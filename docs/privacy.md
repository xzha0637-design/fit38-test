# Privacy and human oversight

- Iteration 1 reads offline, simulated or research-derived public-data fixtures.
- Raw source payloads and full profiles are not written to the feedback database.
- Stored assessment rows contain only a pseudonymous reference, model identifier,
  risk band, status, and timestamp.
- Logs must never include raw payloads, access tokens, or unnecessary account
  identifiers.
- Results are triage evidence, not verdicts.
- No endpoint suspends, moderates, reports, or otherwise acts on a platform.

Later feedback and follow-up stages must preserve this minimum-data boundary.

Decision feedback contains exactly the pseudonymous assessment reference, model
version, recommendation, analyst decision, reason, and timestamp. No decision
endpoint is connected to Twitter/X or any moderation action.

Assessment context exists only in process memory until a decision is recorded.
SQLite contains only `decision_feedback`. Reading feedback requires the simple
project-role header `X-Project-Role` with an allowed value (`analyst` or `admin`
by default). Unexpected-error logs record only a correlation ID and exception
type; exception messages, payloads, tokens and identifiers are excluded.
