# Security Notes

## Protected

- Medium-risk registered actions require human approval before execution.
- Keyword-matched high-risk proposals are held as `blocked_pending_review`.
- Approval and rejection decisions are recorded in a SHA-256 chained JSONL log.
- `verify-log` reports whether the approval chain still links cleanly.
- Action IDs are constrained to a safe character allowlist and resolved inside the pending-action directory.

## Not Protected

- The model can still generate harmful or deceptive proposals.
- The deterministic classifier can miss wording outside its keyword list.
- Local filesystem access can modify runtime files; the hash chain is tamper-evident, not tamper-proof.
- Secrets in `.env` still depend on normal local machine controls.
- Actions performed outside the registered skill executor are outside this gate.
