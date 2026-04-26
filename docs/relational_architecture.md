# Relational Architecture

How Agent Action Gate fits into a longer-running pattern for keeping
multi-agent systems coherent and accountable in production.

This document describes the *method*. The repo provides one piece of
that method as a public, reusable library.

---

## The pattern in one paragraph

Treat each agent as a persistent collaborator rather than a stateless
function call. Give it a stable identity file (role, scope, what it
will and won't do, how it should disagree). Wake it on every dispatch
by reading shared state and ledger history first. Make every meaningful
turn produce an append-only ledger entry. Mediate every external side
effect through one gate that classifies risk, queues medium-risk for
human review, blocks high-risk before it can execute, and records
every decision in a tamper-evident chain. The result is a runtime
where the model can be wrong, can drift, can be prompt-injected — and
the system still cannot quietly cause harm or lose its account of what
happened.

---

## The four primitives

### 1. Stable identity

Each agent has a markdown file describing:

- Its role and the boundaries of that role
- What it must read on wake (this repo's STATUS, role file, recent
  ledger entries) before substantive work
- Its hard refusals — what it will not do regardless of how the
  request is phrased
- How it should disagree (don't flatten, name the disagreement)

These are loaded into the agent's prompt on every dispatch. The
identity file is the durable substrate; conversation history is
ephemeral. This is the cheapest available defense against identity
drift, because there is one canonical place to read instead of
many places to remember.

### 2. Ledgered memory

A small set of append-only logs sit next to the code:

- `decision_log` — choices made and why
- `promise_log` — commitments to operators or other agents
- `repair_log` — failures named, causes identified, prevention rules
- `risk_log` — flags raised, even if not acted on
- `action_log` — meaningful actions taken
- `approval_log` — operator approvals and rejections (this repo's
  approval chain implements this primitive)
- `continuity_log` — handoffs between agents or sessions

Two properties matter:

1. **Append-only.** No edits, no deletes. If a prior entry was wrong,
   write a new entry that supersedes it.
2. **One short line per entry.** Ledgers are evidence, not essays.

The ledgers are how an agent six dispatches from now reconstructs
what it already decided, what it already promised, and what it
already broke. Without them, agents either confabulate or ask
operators to re-explain context that was already established.

### 3. The action gate (this repo)

Every external side effect — sending email, posting to a service,
opening a PR, calling a tool — passes through one place that:

- Parses proposals from agent text output (`SKILL_REQUEST: ...`)
- Classifies risk against a policy registry plus a deterministic
  keyword classifier
- Auto-executes only what the operator has pre-approved as low risk
- Queues medium-risk for human review
- Blocks keyword-matched high-risk before queue
- Records every approve/reject in a SHA-256-chained log

This is the part that's open-sourced here. It is small on purpose:
~700 lines of Python, no dependencies. The point is that the
boundary should be unmissable, not clever.

### 4. The trust ladder (operator pre-approval)

Some decisions repeat. Others are ambiguous. A useful third primitive
is a per-decision-class trust level that graduates with operator
acks:

- **Level 0** (default): every instance asks the operator
- **Level 1**: notify and wait briefly for objection
- **Level 2**: act now, notify, allow undo
- **Level 3**: act, weekly summary

Graduation requires N consecutive operator yeses. Demotion is one
operator no. Some classes are permanently pinned at Level 0 (spend
money, modify identity files, modify ledger structure, claim things
the system cannot verify).

The agent-action-gate library does not ship a trust ladder. The
pattern is documented here because it is the natural complement when
you're running this in production for more than a week. A future
version of this repo may include a generic implementation; the design
is straightforward enough that most teams will want to adapt it
to their own decision classes.

---

## What this is not

- **Not a consciousness claim.** The pattern works whether you
  believe agents are anything more than text generators. It just
  treats them *as if* they were collaborators with continuity.
  That treatment is what the agent's outputs come to reflect.

- **Not a guarantee.** A determined attacker with filesystem access
  can still alter things. The hash chain detects tampering after the
  fact; it does not prevent it. The classifier is keyword-based; it
  catches obvious patterns and misses sophisticated ones. Defense in
  depth assumes *layers* of imperfect protection, not one perfect one.

- **Not a replacement for careful tool design.** A skill that
  exposes too much capability cannot be made safe by a gate.

- **Not a hosted product.** Everything is local files, plain Python.
  That is intentional: the moment you outsource your audit trail,
  you depend on the outsourcer's integrity.

---

## What this gives you

Run an agent against this for a week and you will end up with:

- A ledger of every decision, every promise, every failure, every
  approval — in plain text, queryable with `grep`
- A list of which medium-risk action classes you've accepted enough
  times that they're worth pre-approving
- Concrete instances of high-risk proposals the gate caught
- A defensible answer to the question "what did the agent do
  yesterday and why" that doesn't require trusting the agent

That is what production agent runtime looks like when the operator
stays in control of what the system can change in the world.

---

## Where to start

1. Read the [README](../README.md) for install + five-minute demo.
2. Run `python examples/full_runtime_demo.py` to see three callers
   propose three different actions and watch the gate handle each.
3. Run `python examples/demo_blocked_exfiltration.py` for the
   classifier-blocks-exfiltration case in isolation.
4. Run `python scripts/action_gate.py verify-log` against any
   runtime to confirm the chain is intact.
5. Wire it into your own agent: have the agent emit `SKILL_REQUEST`
   lines, pipe its text output through the gate, surface pending
   actions to whoever reviews them.

The point of this repo is to make step 5 take one afternoon
instead of one quarter.
