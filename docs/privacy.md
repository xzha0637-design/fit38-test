# Privacy and human oversight

- Iteration 1 reads offline, simulated or research-derived public-data fixtures.
- Raw source payloads and full profiles are not written to the feedback database.
- Stored workflow rows contain only a pseudonymous reference, model identifier,
  decision or follow-up state, reason, and timestamp.
- Logs must never include raw payloads, access tokens, or unnecessary account
  identifiers.
- Results are triage evidence, not verdicts.
- No endpoint suspends, moderates, reports, or otherwise acts on a platform.

Decision feedback contains exactly the pseudonymous assessment reference, model
version, recommendation, analyst decision, reason, and timestamp. No decision
endpoint is connected to Twitter/X or any moderation action.

Backend assessment context is an expiring pseudonymous SQLite row containing
only the assessment reference, model version, recommendation and lifecycle
timestamps. It expires after 24 hours and is purged during store activity. This
allows a displayed assessment to remain actionable across a local service
restart without retaining an account identifier or raw profile.

To preserve the current result while the same browser tab visits Model
Information, the frontend keeps one versioned `sessionStorage` snapshot
containing only the already whitelisted preview, completeness response,
assessment result and visible decision/follow-up UI state. The snapshot is
schema-validated before rendering, contains no training label or raw source
payload, is never written to `localStorage`, and is removed by **Start new
assessment** or when the tab's session ends.

SQLite contains `assessment_contexts`, `decision_feedback` and
`follow_up_records`. Reading decision feedback requires the simple project-role
header `X-Project-Role` with an allowed value (`analyst` or `admin` by default).
Unexpected-error logs record only a correlation ID and exception type;
exception messages, payloads, tokens and identifiers are excluded.

Follow-up persistence is a separate minimal pseudonymous record containing only
assessment reference, model version, status, reason and timestamp.
