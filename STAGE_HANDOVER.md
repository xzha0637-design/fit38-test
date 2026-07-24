# Stage handover

- **Stage:** 07 — US1.3 Recovery and Reset
- **Primary owner:** Keliang Chen
- **Branch:** `stage/07-us1.3-recovery-reset`

## Summary

Added controlled unknown, source-timeout, model-timeout and malformed-response
states plus Retry/Start new actions that clear stale evidence and restore focus.

## Acceptance Criteria and tests

All AC1–AC6 map to three tests in `docs/test_mapping.md`.

- **Executed:** `python -m pytest --basetemp ".pytest-tmp"`.
- **Passed:** 40 tests in 4.12 seconds.
- **Failed:** 0 after preserving the earlier actionable “preloaded account” copy.

Changed API errors/orchestration, UI recovery state, tests and delivery docs.
Stage 08 hardens retention, logging and authorised feedback access.
