# Trace redactions

`scripts/capture_traces.py` passes every transcript through a
credential-shaped-string redactor before writing it here. This file
records what was replaced, so the redaction is auditable rather than
silent. Placeholders have the form `[REDACTED:<kind>]`.

Only BidTriage sessions are copied. The Claude Code project directory
on this machine also holds unrelated sessions; those are never copied,
and the capture script has no copy-all flag by design.

| Trace file | Size (KB) | Redactions |
|---|---:|---|
| `session_26c4465e-9331-41d7-a7dd-ee8d1a4554b2.jsonl` | 43672.1 | bearer_token x4, email_address x22 |
| `session_fdfe39b4-2363-48df-b2be-a645f0669109.jsonl` | 9550.9 | email_address x96 |

Totals: bearer_token x4, email_address x118
