# Iteration 1 Testing Plan

## Sequence

For each story: confirm story and AC, define test names/expected outcomes,
prepare offline fixtures, build, run the smallest relevant tests, fix defects,
run the cumulative suite, then update handover and evidence.

## Test levels

| Level | Scope | Evidence |
|---|---|---|
| Unit | cleaning, splits, feature mapping, thresholds, artifact service, pure result filters | `tests/test_data_pipeline.py`, `test_features.py`, `test_model_service.py`, `test_us5_2_sort_filter.py` |
| API/contract | validation, preview, completeness, assessment, decisions, protection, follow-up, batch | Story test modules and `tests/test_api.py` |
| UI static/accessibility | labels, loading/status regions, text risk labels, reset controls, model links, batch controls | US1.1, US1.3, US2.2, US3.1, US3.2, US5.1/5.2 tests |
| Integration | main path, batch/single consistency, privacy, controlled errors and stale state | `tests/test_stage13_integration.py` |
| Operational | clean offline release smoke flow | `python -m scripts.verify_run_sheet` |

## Required boundaries

- completeness: below 0.50, exactly 0.50, and above 0.50;
- bands: Low below 0.10, Medium 0.10–below 0.60, High at/above 0.60;
- CSV: wrong type/header, 0–100 rows, 101 rows, duplicates, invalid and unknown;
- errors: source/model timeout, malformed response, missing artifact, unknown
  route/account, invalid body and unauthorised role;
- privacy: only approved columns/tables, safe logs and no raw payload persistence;
- human oversight: reason rules, duplicate decision prevention and no-action text.

## Exit criteria

- all collected tests pass;
- Run Sheet passes;
- JavaScript syntax checks pass;
- `git diff --check` passes;
- no open critical/high defect;
- test results and AC mapping are current.
