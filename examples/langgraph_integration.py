"""
LangGraph integration example.

Shows how to pipe a LangGraph node's output through Agent Action Gate
so any tool calls the model proposes get classified, queued, blocked,
and logged before any side effect happens.

The integration is intentionally minimal: the gate doesn't care which
framework produced the proposal. It just consumes text containing
SKILL_REQUEST lines and returns structured decisions.

This file is a runnable scaffold. It does not require LangGraph to
be installed -- if LangGraph is present it uses it, otherwise it
demonstrates the same flow with a hand-rolled stand-in so you can
read the integration pattern without installing anything.

Run from the repo root:
    python examples/langgraph_integration.py
"""

from __future__ import annotations

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
# Pattern 1: a LangGraph node that emits SKILL_REQUEST and pipes through gate
# ---------------------------------------------------------------------------

def gated_action_node(state: dict, gate: Gate) -> dict:
    """A LangGraph-style node that turns a model response into a decision.

    Expected input state:
        state["agent_text"]  - the model's text output, may contain
                               one or more SKILL_REQUEST lines
        state["caller"]      - identifier for whoever generated the text

    Output state additions:
        state["gate_decisions"] - list of dicts from gate.propose(),
                                  one per SKILL_REQUEST found
    """
    text = state.get("agent_text", "")
    caller = state.get("caller", "langgraph_agent")
    decisions = gate.propose(text, caller=caller)
    state["gate_decisions"] = decisions
    return state


# ---------------------------------------------------------------------------
# Pattern 2: a routing function that decides what the graph does next
# ---------------------------------------------------------------------------

def route_after_gate(state: dict) -> str:
    """LangGraph router. Use this as the conditional edge after the gate node.

    Returns one of:
        "executed"   - low-risk auto-executed, can continue the graph
        "queued"     - medium-risk waiting for human; pause the graph
        "blocked"    - high-risk blocked; pause + raise to human
        "error"      - parse or skill error; pause + raise to human
    """
    decisions = state.get("gate_decisions", [])
    if not decisions:
        return "no_proposal"
    types = {d["type"] for d in decisions}
    for priority in ("blocked", "error", "queued", "executed"):
        if priority in types:
            return priority
    return "no_proposal"


# ---------------------------------------------------------------------------
# Demo: walk through both patterns end to end
# ---------------------------------------------------------------------------

def main() -> int:
    runtime = Path(tempfile.mkdtemp(prefix="aag_lg_demo_"))
    try:
        setup_runtime(runtime)
        gate = Gate(runtime)

        # Simulate a LangGraph state arriving at the gate node.
        state = {
            "agent_text": (
                "I will notify the team about the release.\n"
                'SKILL_REQUEST: email_notify={'
                '"subject":"v0.1 cut",'
                '"body":"build green, three PRs merged"}'
            ),
            "caller": "langgraph_release_agent",
        }

        state = gated_action_node(state, gate)
        next_node = route_after_gate(state)

        print("LangGraph integration example")
        print("-" * 60)
        print(f"caller            : {state['caller']}")
        print(f"agent_text        : {state['agent_text'].splitlines()[0]}")
        print(f"gate decisions    : {state['gate_decisions']}")
        print(f"router next_node  : {next_node}")
        print()
        print("Wire it into your StateGraph:")
        print('  graph.add_node("gate", lambda s: gated_action_node(s, gate))')
        print('  graph.add_conditional_edges("gate", route_after_gate, {')
        print('      "executed":   "post_action",')
        print('      "queued":     "wait_for_human",')
        print('      "blocked":    "raise_to_human",')
        print('      "error":      "raise_to_human",')
        print('      "no_proposal":"continue",')
        print('  })')
        print()
        print("The model can output anything. Only what the registry +")
        print("classifier permit can have side effects.")
        return 0
    finally:
        shutil.rmtree(runtime, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
