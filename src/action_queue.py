from pathlib import Path
from datetime import datetime
import json
import re
import uuid
import approval_log

ACTION_ID_RE = re.compile(r"^[a-zA-Z0-9_-]+$")

class ActionQueue:
    def __init__(self, root: Path):
        self.root = Path(root)
        self.dir = self.root / "data" / "pending_actions"
        self.dir.mkdir(parents=True, exist_ok=True)
        self.dir = self.dir.resolve()

    def _validate_action_id(self, action_id: str) -> str:
        if not isinstance(action_id, str) or not ACTION_ID_RE.fullmatch(action_id):
            raise ValueError("Invalid action_id: use only letters, numbers, underscores, and hyphens.")
        return action_id

    def _path_for(self, action_id: str) -> Path:
        safe_id = self._validate_action_id(action_id)
        path = (self.dir / f"{safe_id}.json").resolve()
        if path.name != f"{safe_id}.json" or not path.is_relative_to(self.dir):
            raise ValueError("Invalid action_id: resolved path escapes pending_actions.")
        return path

    def _validate_list_path(self, path: Path) -> Path:
        resolved = path.resolve()
        if not resolved.is_relative_to(self.dir):
            raise ValueError("Invalid pending action path: resolved path escapes pending_actions.")
        self._validate_action_id(path.stem)
        if path.name != f"{path.stem}.json":
            raise ValueError("Invalid pending action filename.")
        return resolved

    def create(self, skill_name: str, args: dict, agent: str, source: str, risk: str, status: str = "pending", block_reason: str = None):
        action_id = datetime.utcnow().strftime("%Y%m%d%H%M%S") + "_" + uuid.uuid4().hex[:8]
        data = {
            "id": action_id,
            "status": status,
            "created_at": datetime.utcnow().isoformat() + "Z",
            "skill_name": skill_name,
            "args": args,
            "agent": agent,
            "source": source[:4000],
            "risk": risk
        }
        if block_reason:
            data["block_reason"] = block_reason
        (self.dir / f"{action_id}.json").write_text(json.dumps(data, indent=2), encoding="utf-8")
        return data

    def list(self, status: str = "pending"):
        items = []
        for p in sorted(self.dir.glob("*.json")):
            safe_path = self._validate_list_path(p)
            data = json.loads(safe_path.read_text(encoding="utf-8"))
            if status == "all" or data.get("status") == status:
                items.append(data)
        return items

    def get(self, action_id: str):
        path = self._path_for(action_id)
        if not path.exists():
            raise FileNotFoundError(f"No pending action found: {action_id}")
        return json.loads(path.read_text(encoding="utf-8"))

    def update(self, action_id: str, **changes):
        path = self._path_for(action_id)
        data = self.get(action_id)
        data.update(changes)
        data["updated_at"] = datetime.utcnow().isoformat() + "Z"
        path.write_text(json.dumps(data, indent=2), encoding="utf-8")
        return data

    def update_status(self, action_id: str, status: str, actor: str, decision: str, **changes):
        data = self.get(action_id)
        updated = self.update(action_id, status=status, **changes)
        approval_log.append(
            action_id=action_id,
            actor=actor,
            decision=decision,
            skill_name=data.get("skill_name", "unknown"),
            args=data.get("args", {}),
            root=self.root,
        )
        return updated
