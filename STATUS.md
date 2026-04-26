# STATUS

**Current release:** [v0.1.0](https://github.com/claudenunc/agent-action-gate/releases/tag/v0.1.0)

**Last updated:** 2026-04-26

## What's in v0.1.0

- `Gate` class wraps the full pipeline: parse, classify, queue/block, approve/reject, audit
- 17-keyword high-risk classifier (deterministic substring match)
- Path-traversal-safe action queue (`^[a-zA-Z0-9_-]+$` allowlist + `Path.resolve()` containment)
- SHA-256-chained approval log with `verify-log` CLI
- Memory poisoning defense: agent-written notes are untrusted by default; promotion to trusted requires approval
- 9/9 tests pass
- 4 demos run end-to-end:
  - `examples/demo_blocked_exfiltration.py`
  - `examples/full_runtime_demo.py`
  - `examples/langgraph_integration.py`
  - `examples/crewai_integration.py`
- `docs/relational_architecture.md` describes the larger pattern this gate is one piece of
- README has install, demo, integration, threat model, limitations sections
- MIT licensed, no dependencies outside the Python standard library

## What's intentionally out of scope for v0.1

- Hosted dashboard
- Generic trust ladder primitive (the design is documented; an implementation may ship in a future minor release)
- Anything that requires the model itself to behave well

## Recent changes

- 2026-04-26 — v0.1.0 tagged. Double-append bug fixed (reviewer decisions are now 1:1 with chain entries). LangGraph + CrewAI integration scaffolds added. README expanded with "Why It Exists" section.
- 2026-04-25 — initial public refactor from internal codebase. 9/9 tests pass on first cut.

## Reporting issues

For non-security issues: open a GitHub issue.
For security issues: see [`SECURITY.md`](SECURITY.md).
