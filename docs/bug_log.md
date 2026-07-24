# Iteration 1 Bug Log

| ID | Stage | Severity | Observation | Resolution | Verification | Status |
|---|---:|---|---|---|---|---|
| BUG-001 | 12 | Low | A non-ASCII separator in the filter summary decoded differently under the Windows test process. | Replaced the decorative separator with ASCII `|`. | US5.2 test suite passed. | Closed |
| BUG-002 | 12 | Medium | Rows without a risk score appeared before scored rows in ascending order. | Explicitly keep null scores after scored results in both directions. | `test_ac1_sort_and_all_required_filters` covers ascending order. | Closed |
| BUG-003 | 13 | High | Starting a new single assessment hid but did not clear the previous follow-up reason and acknowledgement. | Reset the follow-up form, status text and acknowledgement in `startNewAssessment`. | `test_release_reset_code_clears_single_and_batch_stale_state`. | Closed |
| BUG-004 | 13 | Medium | Starting a new batch could inherit filters and cached result state from the previous batch. | Added `resetBatchControls` and clear the source result cache before processing. | Stage 13 stale-state integration test and US5.2 regression tests passed. | Closed |
| BUG-005 | 13 | Low | The initial Run Sheet command executed the script outside the repository module path. | Changed the command to `python -m scripts.verify_run_sheet`. | Run Sheet printed the expected PASS line. | Closed |

Open critical defects: **0**.

Open high defects: **0**.

All defects found during RC integration were fixed and covered by repeatable
checks before the release-candidate commit.
