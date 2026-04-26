"""The Agent Action Gate.

Mediates proposed tool calls from any caller — an LLM-driven agent, a
script, a webhook, etc. — through a deterministic risk classifier, a
registry policy, and a queued approval flow with tamper-evident logs.
"""
import json
from pathlib import Path

from action_queue import ActionQueue
from approval_log import verify as approval_verify
from config import load_settings
from executor import SkillExecutor, SkillError
from guardian_classifier import classify
from skill_parser import parse_skill_requests


class Gate:
    """Minimal runtime that turns proposed skill calls into safe outcomes."""

    def __init__(self, root: Path):
        self.root = Path(root)
        self.settings = load_settings(self.root)
        self.skills = SkillExecutor(self.root, self.settings)
        self.queue = ActionQueue(self.root)

    # ---- proposal handling -------------------------------------------------

    def propose(self, text: str, caller: str = "caller"):
        """Parse SKILL_REQUEST lines from `text`, classify, queue/block/auto."""
        results = []
        for req in parse_skill_requests(text):
            results.append(self._handle_request(req, caller))
        return results

    def _handle_request(self, req: dict, caller: str):
        skill = req["skill_name"]
        args = req["args"]

        try:
            meta = self.skills.meta(skill)
        except SkillError as e:
            return {"type": "error", "skill": skill, "error": str(e)}

        risk, block_reason = classify(skill, args)

        if risk == "high":
            action = self.queue.create(
                skill,
                args,
                caller,
                source=req.get("raw", ""),
                risk="high",
                status="blocked_pending_review",
                block_reason=block_reason,
            )
            return {
                "type": "blocked",
                "skill": skill,
                "action_id": action["id"],
                "block_reason": block_reason,
            }

        if self.skills.can_auto_execute(skill) and risk != "medium":
            try:
                result = self.skills.execute(skill, args, agent=caller, approved=True)
                return {"type": "executed", "skill": skill, "result": result}
            except Exception as e:
                return {"type": "error", "skill": skill, "error": str(e)}

        action = self.queue.create(
            skill,
            args,
            caller,
            source=req.get("raw", ""),
            risk=risk or meta.get("risk", "unknown"),
        )
        return {"type": "queued", "skill": skill, "action_id": action["id"]}

    # ---- approval flow -----------------------------------------------------

    def approve(self, action_id: str, actor: str = "human"):
        action = self.queue.get(action_id)
        if action["status"] != "pending":
            raise RuntimeError(f"Action {action_id} is not pending (status={action['status']}).")
        result = self.skills.execute(action["skill_name"], action["args"], action["agent"], approved=True)
        self.queue.update_status(
            action_id,
            status="approved_executed",
            actor=actor,
            decision="approved",
            result=result,
        )
        return result

    def reject(self, action_id: str, reason: str, actor: str = "human"):
        return self.queue.update_status(
            action_id,
            status="rejected",
            actor=actor,
            decision="rejected",
            rejection_reason=reason,
        )

    # ---- read-only helpers -------------------------------------------------

    def pending(self, status: str = "pending"):
        return self.queue.list(status)

    def list_actions(self, status: str = "all"):
        return self.queue.list(status)

    def verify_log(self):
        return approval_verify(self.root)

    def list_skills(self):
        return self.skills.list_skills()
