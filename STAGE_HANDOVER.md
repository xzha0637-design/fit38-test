# Stage handover

- **Stage:** 13 — Integrated MVP RC1
- **Primary owner:** Wei Zhang
- **Branch:** `stage/13-integrated-mvp-rc1`

## Summary

All 12 User Stories are integrated in one offline Release Candidate. RC work
added cross-story contract, batch/single consistency, privacy, accessibility,
controlled-error and stale-state regression evidence. Integration found and
fixed stale follow-up and batch-filter state. No critical or high defect remains.

## Files added

- `docs/bug_log.md`
- `docs/demo_script.md`
- `docs/evidence_summary.md`
- `docs/feedback_retrospective.md`
- `docs/mvp_definition.md`
- `docs/product_backlog.md`
- `docs/run_sheet.md`
- `docs/testing_plan.md`
- `docs/test_results.md`
- `docs/trello_handover.md`
- `docs/ux_technical_design.md`
- `scripts/verify_run_sheet.py`
- `tests/test_stage13_integration.py`

## Files modified

- `CHANGELOG.md`
- `README.md`
- `STAGE_HANDOVER.md`
- `docs/architecture.md`
- `docs/data_contract.md`
- `docs/privacy.md`
- `docs/test_mapping.md`
- `frontend/app.js`

Files removed: none.

## Acceptance and test evidence

All User Story AC mappings remain cumulative in `docs/test_mapping.md`. Stage 13
adds six release checks covering the main path, single/batch consistency,
minimal persistence, accessibility, error contracts and stale-state reset.
Those six tests are added in `tests/test_stage13_integration.py`.

- **Automated tests executed:** 63 in 5.47 seconds.
- **Passed:** 63.
- **Failed:** 0.
- **Run Sheet:** PASS.
- **JavaScript syntax checks:** PASS.
- **Open critical/high defects:** 0.

## Manual verification

Follow `docs/run_sheet.md`, then present `docs/demo_script.md`. The automated Run
Sheet command is `python -m scripts.verify_run_sheet`.

## Known issues and next notes

No release-blocking issue is open. Scientific and product constraints remain in
`docs/known_limitations.md` and `/model-information`. ZIP this exact committed
state as `IT1_Stage13_Integrated_MVP_RC1.zip`.
