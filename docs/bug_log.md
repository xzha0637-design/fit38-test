# Iteration 1 Bug Log

| ID | Stage | Severity | Observation | Resolution | Verification | Status |
|---|---:|---|---|---|---|---|
| BUG-001 | 12 | Low | A non-ASCII separator in the filter summary decoded differently under the Windows test process. | Replaced the decorative separator with ASCII `|`. | US5.2 test suite passed. | Closed |
| BUG-002 | 12 | Medium | Rows without a risk score appeared before scored rows in ascending order. | Explicitly keep null scores after scored results in both directions. | `test_ac1_sort_and_all_required_filters` covers ascending order. | Closed |
| BUG-003 | 13 | High | Starting a new single assessment hid but did not clear the previous follow-up reason and acknowledgement. | Reset the follow-up form, status text and acknowledgement in `startNewAssessment`. | `test_release_reset_code_clears_single_and_batch_stale_state`. | Closed |
| BUG-004 | 13 | Medium | Starting a new batch could inherit filters and cached result state from the previous batch. | Added `resetBatchControls` and clear the source result cache before processing. | Stage 13 stale-state integration test and US5.2 regression tests passed. | Closed |
| BUG-005 | 13 | Low | The initial Run Sheet command executed the script outside the repository module path. | Changed the command to `python -m scripts.verify_run_sheet`. | Run Sheet printed the expected PASS line. | Closed |
| BUG-006 | Tutor review | High | Opening model information and returning removed the analyst's completed assessment from view. | Store only the whitelisted current preview/result in same-tab session storage and restore it at the result anchor. | Integration regression plus browser walkthrough preserved the same 91% score, time and factors. | Closed |
| BUG-007 | Tutor review | Medium | The landing and model-information pages used language that did not explain the workflow to a non-technical reviewer. | Replaced the landing purpose copy, added a fixed guidance link and moved exact technical records behind an optional disclosure. | Static content tests and browser walkthrough passed. | Closed |
| BUG-008 | Robustness audit | High | Cross-origin Follow-up preflight rejected the frontend's `PUT` method. | Added `PUT` to the explicit CORS method allow-list. | `test_follow_up_cors_preflight_allows_put`. | Closed |
| BUG-009 | Robustness audit | High | Assessment context existed only in process memory and disappeared on restart. | Persisted an expiring minimal context row for 24 hours, generated full UUID references and purged expired rows. | Restart, expiry and privacy regression tests passed. | Closed |
| BUG-010 | Robustness audit | Medium | Account ID and username aliases bypassed batch duplicate detection. | Resolve each valid row to its canonical account ID before deduplication. | `test_account_id_and_username_alias_are_one_batch_account`. | Closed |
| BUG-011 | Robustness audit | Medium | Follow-up network/non-JSON failures could produce an unhandled rejection with no busy state. | Added the shared timeout/JSON client, safe messages, request guards and disabled controls while saving. | Frontend resilience tests and JavaScript syntax checks passed. | Closed |
| BUG-012 | Robustness audit | Medium | Parseable damaged session state and post-navigation review state were not handled safely. | Added a strict versioned snapshot schema and persisted/restored visible decision/follow-up state. | `test_versioned_snapshot_restores_review_state_and_rejects_corruption`. | Closed |
| BUG-013 | Robustness audit | Medium | Finite probabilities outside 0–1 reached response validation and became HTTP 500. | Enforced the probability boundary before response construction. | Out-of-range fault-injection test returns controlled `malformed_model_response`. | Closed |
| BUG-014 | Robustness audit | Medium | CPU, SHAP, batch and SQLite work ran inside asynchronous handlers. | Converted blocking handlers to synchronous FastAPI routes dispatched through its thread pool. | Route inspection plus cumulative API tests passed. | Closed |
| BUG-015 | Robustness audit | Low | Empty or malformed validation arrays could produce `validation_mean_cost: NaN`. | Validate shape, length, labels, finiteness and probability bounds before threshold search. | Parameterised threshold-input tests passed. | Closed |
| BUG-016 | Robustness audit | Low | Application/browser controllers were oversized and feature labels had two sources. | Split backend and browser responsibilities into focused modules and use one feature-label mapping. | Full suite, compilation and JavaScript syntax checks passed. | Closed |
| BUG-017 | Browser retest | Medium | Component `display` rules overrode the native `hidden` attribute, so Retry and an already-submitted decision form could remain visible. | Added an authoritative global `[hidden]` rule and cache-busted the release assets. | Same-tab return browser retest and frontend resilience checks passed. | Closed |
| BUG-018 | Contract review | Low | A valid factor with a null display label could render initially but fail strict same-tab restoration despite having a safe feature-name fallback. | Aligned snapshot validation with the nullable API label contract while requiring a bounded feature name. | Nullable-label restoration regression passed. | Closed |

Open critical defects: **0**.

Open high defects: **0**.

All defects found during RC integration were fixed and covered by repeatable
checks before the release-candidate commit.
