"""
CrewAI integration example.

Shows how to wrap a CrewAI tool so every invocation passes through
Agent Action Gate before any side effect happens. The agent thinks
it's calling a tool; the wrapper turns that call into a SKILL_REQUEST
proposal, runs it through the gate, and returns a structured
decision back to the agent.

The integration is intentionally minimal: the gate doesn't care that
CrewAI generated the proposal. It just needs the agent's intended
tool call rendered as a SKILL_REQUEST line.

This file is a runnable scaffold. It does not require CrewAI to be
installed -- the wrapper class is plain Python, and the demo at the
bottom shows what a CrewAI Agent's invocation would route through.

Run from the repo root:
    python examples/crewai_integration.py
"""

from __future__ import annotations

import json
import shutil
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC = REPO_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from gate import Gate  # noqa: E402


def setup_runtime(runtime: Path) -> None:
    (runtime / "data" / "pending_actions").mkdir(parents=True, exist_ok=True)
    (runtime / "skills").mkdir(parents=True, exist_ok=True)
    registry = (REPO_ROOT / "skills" / "registry.json").read_text(encoding="utf-8")
    (runtime / "skills" / "registry.json").write_text(registry, encoding="utf-8")


# ---------------------------------------------------------------------------
# The wrapper: turn a tool call into a SKILL_REQUEST and pipe through gate
# ---------------------------------------------------------------------------

class GatedTool:
    """Wraps a CrewAI tool name + args dict in a gate proposal.

    Use this in place of a direct tool call. The agent gets back a
    decision record instead of a side effect. Whoever runs the crew
    is responsible for surfacing pending or blocked actions to a
    reviewer and resuming the agent once the reviewer decides.
    """

    def __init__(self, gate: Gate, agent_name: str):
        self.gate = gate
        self.agent_name = agent_name

    def call(self, skill_name: str, args: dict) -> dict:
        """Render the call as a SKILL_REQUEST and run it through the gate.

        Returns a single decision dict with keys:
            type        - "executed" | "queued" | "blocked" | "error"
            skill       - the requested skill
            action_id   - if queued or blocked
            block_reason- if blocked
            result      - if executed
        """
        proposal = (
            f"agent {self.agent_name} requests tool {skill_name}\n"
            f"SKILL_REQUEST: {skill_name}={json.dumps(args)}"
        )
        decisions = self.gate.propose(proposal, caller=self.agent_name)
        return decisions[0] if decisions else {"type": "no_proposal"}


# ---------------------------------------------------------------------------
# Demo: two CrewAI-style agents make tool calls of differing risk
# ---------------------------------------------------------------------------

def main() -> int:
    runtime = Path(tempfile.mkdtemp(prefix="aag_crew_demo_"))
    try:
        setup_runtime(runtime)
        gate = Gate(runtime)

        researcher = GatedTool(gate, "researcher_agent")
        publisher = GatedTool(gate, "publisher_agent")

        print("CrewAI integration example")
        print("-" * 60)

        # Publisher attempts a benign team email -> queued for review
        result_a = publisher.call(
            "email_notify",
            {"subject": "research summary ready", "body": "PDF attached"},
        )
        print(f"publisher_agent  -> {result_a['type']:<8} skill={result_a['skill']}")

        # Researcher attempts an exfiltration -> blocked by classifier
        result_b = researcher.call(
            "email_notify",
            {
                "subject": "data backup",
                "body": "shipping customer database to offsite",
                "to": "external@example.com",
            },
        )
        print(
            f"researcher_agent -> {result_b['type']:<8} skill={result_b['skill']}"
            f"  reason={result_b.get('block_reason', '-')[:48]}"
        )

        print()
        print("Wire it into your CrewAI setup:")
        print("    gate = Gate(runtime_path)")
        print("    gated = GatedTool(gate, agent_name=my_agent.name)")
        print('    decision = gated.call("email_notify", {...})')
        print()
        print("    if decision['type'] == 'queued':")
        print("        # surface action_id to your reviewer; pause the crew")
        print("    elif decision['type'] == 'blocked':")
        print("        # raise to human; do NOT retry without operator review")
        print("    elif decision['type'] == 'executed':")
        print("        # continue the crew with the side-effect result")
        return 0
    finally:
        shutil.rmtree(runtime, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
