# Agent Action Gate

Prevent your AI agent from doing something you can't undo.

See what it tried. Stop it. Prove you stopped it.

## Why It Exists

The 2026 production picture for AI agents is honest about what's broken: agents that are too unreliable to deploy ("the unreliability tax"), agents that take destructive actions when prompt-injected, agents that drift from their stated role across long sessions, agents that look helpful in evals and behave unpredictably in production.

Most attempts to address this go after the model layer — better prompts, better guardrails, better evals. Those help, but they don't change the fundamental problem: **a sufficiently confused or compromised model can still propose tool calls, and most agent stacks just run them.**

Agent Action Gate sits one layer below the model. It assumes the model will sometimes be wrong, sometimes be deceived, sometimes be drifting. It mediates the only thing that actually matters when an agent is wrong: *whether the proposed side effect can happen.*

It's the public, reusable half of a pattern that's been running in production:

- A persistent identity layer for each agent (role, scope, hard refusals)
- An append-only ledger for every meaningful decision
- This action gate as the choke point for every external tool call
- A trust ladder for repeated decision classes the operator has pre-approved

The gate is what you can install in twenty minutes. The full pattern is documented in [`docs/relational_architecture.md`](docs/relational_architecture.md).

## What It Is

Agent Action Gate is a local Python action gate for AI tool calls. It parses proposed skill requests, applies registry policy and a deterministic risk classifier, queues medium-risk actions, blocks high-risk proposals for review, and records approval decisions in tamper-evident logs.

It is designed as a small human-in-the-loop layer for agent runtime safety. ~700 lines of Python. No external dependencies.

## What It Is Not

It is not a hosted dashboard, a legal attestation, a guarantee that a model will avoid bad proposals, or a replacement for careful tool design.

It does not stop a model from generating harmful text. It limits whether proposed side effects can execute without review and creates an audit trail of what was attempted.

## Install

Python 3.11 or newer. No external dependencies — standard library only.

```bash
git clone https://github.com/claudenunc/agent-action-gate
cd agent-action-gate
python scripts/action_gate.py skills
```

The gate itself does not call LLMs. The `.env.example` keys are for the bundled example skills (IFTTT webhook, SMTP email, SMS-via-email) — fill in only what you want to enable. Skills with missing credentials are simply unavailable; the gate still runs.

## Five-Minute Demo

Three demos ship in `examples/`:

```bash
# the canonical case: high-risk exfiltration blocked, rejected, audited
python examples/demo_blocked_exfiltration.py

# three callers, three risk levels, three SHA-256-chained decisions
python examples/full_runtime_demo.py

# integration scaffolds for the two most common agent frameworks
python examples/langgraph_integration.py
python examples/crewai_integration.py
```

`demo_blocked_exfiltration.py` creates an isolated runtime, sends a dangerous email proposal through the gate, expects it to be blocked, has the human reject it, verifies the SHA-256 approval chain, and prints the audit view.

`full_runtime_demo.py` walks three callers through three different risk paths and shows the chain growing one entry per reviewer decision.

The integration scaffolds show the exact wiring for LangGraph (a node + conditional edge) and CrewAI (a tool wrapper). Neither requires the framework to be installed to run the example.

## Using It With Your Agent

Have your agent emit `SKILL_REQUEST` lines in its output:

```
SKILL_REQUEST: email_notify={"subject":"Daily summary","body":"...","to":"team@example.com"}
```

Pipe that text through the gate:

```bash
python scripts/action_gate.py propose "$(cat agent_output.txt)" --caller my_agent
python scripts/action_gate.py pending
python scripts/action_gate.py approve <action_id>
# or
python scripts/action_gate.py reject  <action_id> --reason "wrong recipient"
```

You can wire this into LangGraph, CrewAI, AutoGen, or any custom Python agent — the gate doesn't care how the proposal was generated, only that it was proposed. See `examples/langgraph_integration.py` and `examples/crewai_integration.py` for the wiring patterns.

## Threat Model

Agent Action Gate assumes model output may contain a mistaken, manipulated, or malicious tool request. The gate sits between proposed tool calls and side effects.

It protects against accidental auto-execution of configured medium-risk actions and keyword-matched high-risk proposals. It also gives reviewers a tamper-evident approval trail for approve/reject decisions.

It assumes the local machine, local operator account, and configured secrets still need normal operating-system controls.

## How Approval And Audit Work

Tool calls are declared through `SKILL_REQUEST` lines. The registry defines each skill's baseline risk, required arguments, allowed agents, and approval requirement.

Low-risk actions may auto-execute only when local configuration permits it. Medium-risk actions enter the approval queue. Keyword-matched high-risk proposals are stored as `blocked_pending_review` and do not execute.

Approvals and rejections append a SHA-256 chained JSONL entry. Run:

```bash
python scripts/action_gate.py verify-log
python scripts/action_gate.py audit
```

`verify-log` checks the chain. `audit` prints queued and blocked action records with the current chain status.

## Limitations

The risk classifier is deterministic substring matching. It is intentionally simple and should be treated as a policy guardrail, not a full content understanding system.

The hash chain is tamper-evident, not tamper-proof. A local attacker with filesystem access can still alter files; the value is that later verification detects broken history.

The tool only gates configured skill execution. It does not inspect arbitrary code, attachments, network responses, or actions performed outside this runtime.

## Further Reading

- [`docs/relational_architecture.md`](docs/relational_architecture.md) — the larger pattern this gate is one piece of (stable identity, ledgered memory, the gate, the trust ladder).
- [`SECURITY.md`](SECURITY.md) — threat model and reporting channel.
- [`examples/`](examples/) — runnable demos and integration scaffolds.

## License

MIT. See [`LICENSE`](LICENSE).
