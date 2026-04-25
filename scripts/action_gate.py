"""Agent Action Gate command-line interface."""
import argparse
import json
import os
import sys
from pathlib import Path

ROOT = Path(os.getenv("ACTION_GATE_ROOT", Path(__file__).resolve().parents[1])).resolve()
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from gate import Gate
from approval_log import verify as verify_approval_log


SUMMARY_FIELDS = [
    "id",
    "status",
    "skill_name",
    "risk",
    "agent",
    "created_at",
    "updated_at",
    "block_reason",
    "rejection_reason",
]


def parse_args_list(items):
    out = {}
    for item in items or []:
        if "=" not in item:
            raise SystemExit(f"--arg must be key=value, got: {item}")
        k, v = item.split("=", 1)
        out[k] = v
    return out


def summarize_action(action):
    return {field: action[field] for field in SUMMARY_FIELDS if field in action}


def main():
    parser = argparse.ArgumentParser(description="Agent Action Gate")
    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("skills", help="List registered skills.")

    propose = sub.add_parser("propose", help="Parse text for SKILL_REQUEST lines, classify, queue/block.")
    propose.add_argument("text", help='Raw agent output (e.g. \'SKILL_REQUEST: email_notify={"subject":"x","body":"y"}\').')
    propose.add_argument("--caller", default="caller", help="Identifier for the proposer of the action.")

    skill = sub.add_parser("skill", help="Run a registered skill manually (caller must pass --approve for approval-required skills).")
    skill.add_argument("skill_name")
    skill.add_argument("--caller", default="caller")
    skill.add_argument("--approve", action="store_true")
    skill.add_argument("--arg", action="append", default=[])

    pending = sub.add_parser("pending", help="List queued actions.")
    pending.add_argument("--all", action="store_true")

    approve = sub.add_parser("approve", help="Approve a pending action by id.")
    approve.add_argument("action_id")
    approve.add_argument("--actor", default="human")

    reject = sub.add_parser("reject", help="Reject a pending action by id.")
    reject.add_argument("action_id")
    reject.add_argument("--reason", default="Rejected by human.")
    reject.add_argument("--actor", default="human")

    sub.add_parser("verify-log", help="Walk the SHA-256 approval chain and report tamper.")
    sub.add_parser("audit", help="Print actions and the approval chain status as one JSON document.")

    args = parser.parse_args()
    gate = Gate(ROOT)

    if args.cmd == "skills":
        print(json.dumps(gate.list_skills(), indent=2))

    elif args.cmd == "propose":
        results = gate.propose(args.text, caller=args.caller)
        print(json.dumps(results, indent=2))

    elif args.cmd == "skill":
        result = gate.skills.execute(
            args.skill_name,
            parse_args_list(args.arg),
            agent=args.caller,
            approved=args.approve,
        )
        print(json.dumps({"result": result}, indent=2, default=str))

    elif args.cmd == "pending":
        items = gate.pending("all" if args.all else "pending")
        print(json.dumps(items, indent=2))

    elif args.cmd == "approve":
        result = gate.approve(args.action_id, actor=args.actor)
        print(json.dumps({"result": result}, indent=2, default=str))

    elif args.cmd == "reject":
        action = gate.reject(args.action_id, args.reason, actor=args.actor)
        print(json.dumps(action, indent=2))

    elif args.cmd == "verify-log":
        ok, message = verify_approval_log(ROOT)
        print(message)
        if not ok:
            raise SystemExit(1)

    elif args.cmd == "audit":
        ok, message = verify_approval_log(ROOT)
        actions = [summarize_action(a) for a in gate.list_actions("all")]
        print(json.dumps({"approval_chain": {"ok": ok, "message": message}, "actions": actions}, indent=2))
        if not ok:
            raise SystemExit(1)


if __name__ == "__main__":
    main()
