# Iteration 1 Testing Plan

**Project:** AI-Assisted Social Media Bot Risk Scoring Tool
**Primary audience:** External Social Media Safety Analyst
**Scope:** Iteration 1 MVP - 5 Features and 12 User Stories
**Document purpose:** Direct, browser-based verification plus existing automated checks
**Code baseline:** GitHub commit `ee6a923` plus the uncommitted robustness follow-up
**Working branch:** `fix/full-robustness-audit-findings`
**Document status:** Ready for team/tutor execution; selected walkthrough results are recorded in `docs/test_results.md`
**Last updated:** 8 August 2026

> A written test is not a passed test. The executor must record the actual
> visible result and Pass/Fail. Screenshots, HAR files, Console exports and
> shared-folder links are not required for this Testing Plan.

---

## 1. Purpose and Scope

This plan verifies the visible Iteration 1 MVP as a tutor or target-user proxy
would use it: open the local website, select or enter a sample account, click
the controls, upload tracked CSV examples, and compare the page with an explicit
expected result.

The application is an offline human-review aid. It must not contact live
Twitter/X, make a final bot/human determination, or perform moderation,
suspension, reporting or another platform action.

The plan covers:

- direct GUI interaction for intake, preview, completeness, scoring,
  explanation, model information, decisions, follow-up, batch and filters;
- keyboard, focus, text/colour, responsive layout and 200% zoom;
- invalid, unknown, Insufficient and stopped-local-service states;
- existing pytest, JavaScript syntax and Run Sheet checks; and
- a simple truthful execution record without mandatory media attachments.

## 2. Test Environment and Setup

### 2.1 Preconditions

- Work from the repository root.
- Use the project Conda environment `fit5238-backend`.
- Use the tracked offline demonstration records and model artifact.
- Use only the tracked project-dataset samples or synthetic boundary fixtures;
  do not add live/current account data.
- Test current Chrome and Edge and record their exact versions.
- Use a clean browser tab at <http://127.0.0.1:8000/>.

### 2.2 Start the application

```powershell
conda activate fit5238-backend
python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000
```

Open <http://127.0.0.1:8000/>. Stop the service with `Ctrl+C`.

### 2.3 Minimum execution record

For every WEB-EX case record:

| Field | Required value |
|---|---|
| Test ID | WEB-EX-01 to WEB-EX-18 |
| Executor and date | Name, date and timezone |
| Build | Branch and commit SHA or working-tree note |
| Browser | Chrome/Edge name and exact version |
| Display | Viewport and zoom |
| Input/actions | Exact account/file and controls used |
| Actual result | What was visibly observed |
| Status | Pass, Fail, Blocked or Not executed |
| Defect | Bug ID and retest result when failed |

No screenshot, HAR, Console export or shared-folder link is required.

## 3. Tracked Sample Data

### 3.1 Sample account catalogue

| Browser input | Scenario | Expected visible baseline |
|---|---|---|
| `20611469`, `@DeFotis`, or the Low selector option | Static row from `Twitter Human Bots` | `@DeFotis`; 100% completeness; 2% Low |
| `396039913`, `@OGLexa`, or the Medium selector option | Static row from `Twitter Human Bots` | `@OGLexa`; 100% completeness; 30% Medium |
| `2250581388`, `@everyletterbot`, or the High selector option | Static row from `Twitter Bot Training Data 2` | `@everyletterbot`; 100% completeness; 91% High; missing location shown |
| `demo_exact_50` | Inclusive completeness boundary | `@half_evidence`; exactly 50%; eligible; caveat remains; 53% Medium |
| `demo_incomplete_01` | Insufficient evidence | `@limited_record`; 25%; Insufficient data; no score or risk band |
| `bad identifier!` | Invalid local input | Adjacent validation message; assessment does not start |
| `not_in_offline_fixture` | Valid format but unavailable offline | Controlled unavailable-account message |

The first three rows are copied from the two tracked project datasets without
their training label. Dataset names show provenance only; the interface does
not present a bot/human label. The previous `demo_low_01`, `demo_medium_01` and
`demo_high_01` fixtures remain after these rows for regression and batch-file
compatibility, but they are no longer the landing-page selector examples.

The numeric expectations are version-bound to `xgb-offline-v1`,
`threshold-v1` and `data/fixtures/demo_accounts.csv`. Re-baseline them if the
model, thresholds or fixture changes.

### 3.2 Browser-upload files

| File | Purpose and expected result |
|---|---|
| `tests/fixtures/browser_batch.csv` | Seven mixed rows: 4 Completed and 3 Failed |
| `tests/fixtures/browser_batch_empty.csv` | Header only: accepted no-op with 0 total, 0 completed, 0 failed |
| `tests/fixtures/browser_bad_header.csv` | Wrong header: controlled error naming required `account_id` |
| `tests/fixtures/browser_not_csv.txt` | Wrong type: controlled file-type error |
| `tests/fixtures/browser_batch_100_rows.csv` | Exact limit accepted; 100 unknown rows reported independently |
| `tests/fixtures/browser_batch_101_rows.csv` | Limit exceeded; controlled error and no partial table |

## 4. Hands-on Web Interaction Examples

### WEB-EX-01 - Landing page and offline purpose

**Maps to:** global product rules, US1.1, US4.2

1. Start the application and open the home page.
2. Read the header, offline badge, human-oversight notice and form labels.
3. Confirm single-account and batch sections are available.

**Expected visible result:** the first view says `Review Twitter/X accounts for
possible bot activity.` and explains the score, risk level, contributing
factors and data-quality warnings. It states that final judgement remains with
the user and no account is reported, suspended or moderated. The account input,
demonstration selector, Begin assessment control, CSV control and the permanent
**Understand this review tool** link are labelled. No wording promises live
Twitter/X access or automated enforcement.

**Status:** Not executed.

### WEB-EX-02 - Invalid and blank account input

**Maps to:** US1.1 AC2/AC6

1. Submit a blank identifier.
2. Enter `bad identifier!` and select **Begin assessment**.
3. Correct the value by typing `@DeFotis`.

**Expected visible result:** blank and malformed values show an adjacent,
actionable message and do not start an assessment. The invalid state clears when
the value is corrected. The identifier remains reachable and labelled.

**Status:** Not executed.

### WEB-EX-03 - Low result and source/model separation

**Maps to:** US1.1, US1.2, US2.1, US2.2, US3.1

1. Select the Low demonstration scenario or enter `@DeFotis`.
2. Select **Begin assessment**.
3. Inspect the Source data, completeness and Model-generated output sections.

**Expected visible result:** the preview identifies `@DeFotis` and groups
profile, activity and network fields. Completeness is 100%. The result is 2%
Low and uses the word Low as well as colour. Model version, threshold version,
assessment time, uncertainty, no-verdict wording and up to three factor rows are
visible. The source badge says **Offline demonstration record**. Every factor
uses a plain label, direction and observed value.

**Status:** Not executed.

### WEB-EX-04 - Start new and Medium result in the same tab

**Maps to:** US1.3, US2.2

1. Complete WEB-EX-03.
2. Select **Start new assessment**.
3. Run `@OGLexa`.

**Expected visible result:** the previous Low preview, score, factors, decision
and follow-up state clear. Focus returns to the first assessment control. The
new preview identifies `@OGLexa`, completeness is 100%, and the result
is 30% Medium with no stale Low content.

**Status:** Not executed.

### WEB-EX-05 - High result, missing source values and factors

**Maps to:** US1.2, US2.2, US3.1, US3.2

1. Run `@everyletterbot`.
2. Compare the source preview with the model output.
3. Read the factor rows from top to bottom.
4. Open **Review model information and limitations**.

**Expected visible result:** the preview identifies `@everyletterbot` and shows
its unavailable location as `Not available` rather than inventing a value. The
result is 91% High. No more than three factors appear strongest-first with
direction and observed value. The uncertainty and `Triage evidence, not a
verdict.` statement remain visible. A direct link opens model information.

**Status:** Not executed.

### WEB-EX-06 - Exactly 50% completeness boundary

**Maps to:** US2.1 AC1/AC3, US2.2

1. Enter `demo_exact_50`.
2. Select **Begin assessment**.
3. Compare completeness, missing-feature caveat and result.

**Expected visible result:** completeness is exactly 50% and remains eligible.
Missing features and the caveat stay visible. The model result is 53% Medium.
This confirms that the 50% boundary is inclusive.

**Status:** Not executed.

### WEB-EX-07 - Insufficient evidence without a risk band

**Maps to:** US2.1 AC2/AC4, US3.2 AC4, US4.1 AC1, US4.3 AC1

1. Enter `demo_incomplete_01`.
2. Select **Begin assessment**.
3. Inspect completeness, result, decision, follow-up and model-information areas.

**Expected visible result:** completeness is 25%, status is Insufficient data,
and missing features use plain labels. No score, Low/Medium/High band or
Confirm/Override form appears. Follow-up and model-information access remain
available.

**Status:** Not executed.

### WEB-EX-08 - Successful result followed by unknown account

**Maps to:** US1.3 AC1-AC4, US2.2 AC7

1. Complete WEB-EX-05.
2. Without selecting Start new, replace the identifier with
   `not_in_offline_fixture`.
3. Submit again.

**Expected visible result:** a controlled unavailable-account message appears.
The old preview, completeness, 91% score, factors, decision and follow-up panels
are no longer actionable. Start new remains available. A valid-format unknown
identifier is not described as malformed input.

**Status:** Not executed.

### WEB-EX-09 - Stopped local service and Retry

**Maps to:** US1.3 AC1-AC3/AC6, US2.2 AC7

1. Keep the web page open and stop Uvicorn.
2. Submit `@DeFotis`.
3. Confirm the error contains no partial or old score.
4. Restart Uvicorn and select **Retry** once.

**Expected visible result:** a plain-language local-service error offers recovery.
After restart, Retry reuses `@DeFotis` and produces one Low 2% result.
No duplicate decision or follow-up state appears.

**Status:** Not executed.

### WEB-EX-10 - Confirm/Override reason and duplicate prevention

**Maps to:** US4.1 AC1-AC5

1. Complete WEB-EX-05.
2. Select **Override recommendation** and try an empty reason.
3. Enter `manual browser review` and select **Record decision** twice rapidly.
4. In a fresh Medium assessment, record Confirm once.

**Expected visible result:** empty Override is blocked. A valid decision produces
one acknowledgement that the human decision is final and no platform action was
taken. The submit control prevents a second decision for the same assessment.
Confirm does not require an override reason.

**Status:** Not executed.

### WEB-EX-11 - Follow-up add, update, clear and reset

**Maps to:** US4.3 AC1-AC5, US1.3 AC4-AC6

1. Complete `@OGLexa`.
2. Save a flag with `initial human review`.
3. Open Model Information, return, and confirm the flag reason/status remains.
4. Change it to `updated human review` and save again.
5. Select **Clear flag**.
6. Start new, run `demo_incomplete_01`, save and clear another flag.

**Expected visible result:** status changes through Flagged, updated Flagged and
Cleared without duplicate visible state. Every acknowledgement states that no
platform action occurred. Insufficient data supports follow-up but never shows
Confirm/Override. Return navigation preserves the visible flag and reason;
Start new clears the old reason/status.

**Status:** Not executed.

### WEB-EX-12 - Mixed batch partial success

**Maps to:** US5.1 AC1-AC4

1. Select `tests/fixtures/browser_batch.csv`.
2. Confirm the English filename replaces `No file selected`.
3. Select **Assess batch offline** and observe the busy state.
4. Inspect all result rows.

**Expected visible result:** while processing, the button is disabled, the
offline-processing label is visible, counts start at 0/0 and an old table is
hidden. Completion shows 7 total, 4 Completed and 3 Failed. Low 2%, Medium 30%,
High 91% and Insufficient rows complete. Invalid, duplicate and unknown rows
fail independently. No platform action is claimed.

**Status:** Not executed.

### WEB-EX-13 - File type, header and 0/100/101 boundaries

**Maps to:** US5.1 AC1/AC2

Submit each file from section 3.2 in order. If the picker filters out TXT, select
All files before choosing `browser_not_csv.txt`.

**Expected visible result:** wrong type and wrong header show controlled errors;
the empty file shows 0/0/0; the 100-row file is accepted and reports all 100
unknown rows; the 101-row file is rejected without a partial results table. The
busy state clears after every attempt and the visible filename matches the file
chosen.

**Status:** Not executed.

### WEB-EX-14 - Sort, filter, matching count and clear

**Maps to:** US5.2 AC1-AC4

1. Complete WEB-EX-12.
2. Sort Highest first, then Lowest first.
3. Test High, Insufficient and Not reviewable separately.
4. Combine High + Eligible + Unreviewed.
5. Select **Clear filters**.

**Expected visible result:** scored order is 91/30/2 or 2/30/91 and unscored rows
remain last. Matching counts are High 1, Insufficient 1, Not reviewable 3 and
combined 1. Active filters are described. Clear restores the original seven rows
and values without showing a new processing run.

**Status:** Not executed.

### WEB-EX-15 - New batch clears stale filters and results

**Maps to:** US5.1, US5.2, integration regression

1. Leave a High filter active after WEB-EX-12.
2. Select and submit another tracked CSV.
3. Observe controls before and after processing.

**Expected visible result:** filter controls reset before the new batch runs,
old results hide, counts reset and the final table contains only the new batch.
The summary reports no active filters and the correct new count.

**Status:** Not executed.

### WEB-EX-16 - Complete model-information visual review

**Maps to:** US3.2 AC1-AC4, tutor usability feedback

1. From the initial home-page view, open **Understand this review tool** and
   confirm the ordinary-language guidance is visible before technical details.
2. Return, run `@everyletterbot`, then open model information from the scored result.
3. Read **How to use this page** and follow its three links to **What this tool
   checks**, **How to read the result**, and **When the result needs extra care**.
4. Confirm **Technical model and evaluation record** is collapsed by default,
   then expand it and read all twelve public-data feature entries.
5. Compare the plain-language risk-score guidance with the recorded technical
   F1, precision, recall and calibration evidence.
6. Select **Return to assessment**.

**Expected visible result:** the page first explains the tool without requiring
machine-learning knowledge and says the reference does not change the current
assessment. Technical terms and exact evidence are available on demand rather
than dominating the first view. The expanded record reports
`xgb-offline-v1`, `threshold-v1`, both evaluation files, evaluation date, F1
0.5859, precision 0.4158, recall 0.9915 and validation mean cost 0.266149. It
names excluded graph evidence, cross-dataset limits, prevalence shift, concept
drift, false-positive risk and prohibited automated enforcement. Return restores
the same `@everyletterbot` 91% High assessment and moves back to its result; the
score, band, factors and assessment time do not disappear or change.

**Status:** Not executed.

### WEB-EX-17 - Keyboard, focus and text alternatives

**Maps to:** US1.1 AC6, US2.2 AC5, US5.2 controls

1. Use only Tab, Shift+Tab, arrow keys, Enter and Space.
2. Activate the Skip link.
3. Run Low, record a decision, save/clear follow-up, upload a batch, change each
   filter and clear filters.
4. Repeat invalid input and Start new.

**Expected visible result:** every control is reachable, labelled and has visible
focus; focus is not trapped; the Skip link moves to main content; validation and
Start new return focus appropriately; risk meaning is available in text and is
not colour-only.

**Status:** Not executed.

### WEB-EX-18 - Chrome/Edge viewport and 200% zoom matrix

**Maps to:** accessibility and all visible workflows

Repeat the `@DeFotis` Low, `@everyletterbot` High, Insufficient and WEB-EX-12
paths in current Chrome and Edge at:

| Viewport | Zoom |
|---|---|
| 1280 x 720 | 100% and 200% |
| 768 x 1024 | 100% and 200% |
| 375 x 667 | 100% and 200% where the browser supports it |

**Expected visible result:** headings, notices, source values, factors, errors
and controls do not overlap or clip. Long text wraps. The single-account page
does not require horizontal page scrolling. The batch table scrolls inside its
labelled region while filter summary and Clear filters remain reachable.

**Status:** Not executed.

## 5. Existing Automated and Operational Checks

Run these after the documentation/sample-file change:

```powershell
python -m pytest --basetemp ".pytest-tmp"
node --check frontend/app.js
node --check frontend/api-client.js
node --check frontend/assessment-state.js
node --check frontend/assessment-view.js
node --check frontend/batch-results.js
node --check frontend/batch-controller.js
node --check frontend/review-controller.js
python -m scripts.verify_run_sheet
git diff --check
```

Expected: all 86 currently collected tests pass, all seven JavaScript files parse, the
Run Sheet prints its PASS line, and Git reports no whitespace errors.

The existing automated suite covers data cleaning, feature mapping, exact
completeness logic, deterministic scoring, error contracts, privacy,
decisions/follow-up, batch processing, filters and cross-story integration.
Source/model timeout and malformed-model states are not production GUI buttons;
they remain automated fault-injection cases rather than teacher click examples.

## 6. Acceptance-Criterion Traceability

| User Story | Direct browser evidence | Supporting automated evidence |
|---|---|---|
| US1.1 Intake | WEB-EX-01 to 05, 17 | `tests/test_us1_1_account_intake.py` |
| US1.2 Preview | WEB-EX-03 to 05 | `tests/test_us1_2_account_preview.py` |
| US1.3 Recovery/reset | WEB-EX-04, 08, 09, 11, 15, 17 | `tests/test_us1_3_recovery_reset.py` |
| US2.1 Completeness | WEB-EX-03, 06, 07 | `tests/test_us2_1_completeness.py`, `tests/test_features.py` |
| US2.2 Risk result | WEB-EX-03 to 09, 17, 18 | `tests/test_us2_2_risk_scoring.py`, `tests/test_model_service.py` |
| US3.1 Explanation | WEB-EX-03, 05, 18 | `tests/test_us3_1_explanation_uncertainty.py` |
| US3.2 Model information | WEB-EX-05, 07, 16 | `tests/test_us3_2_model_information.py` |
| US4.1 Decision | WEB-EX-07, 10 | `tests/test_us4_1_decision.py` |
| US4.2 Data protection | WEB-EX-01, 10, 11 | `tests/test_us4_2_data_protection.py` |
| US4.3 Follow-up | WEB-EX-07, 11 | `tests/test_us4_3_follow_up.py` |
| US5.1 Batch | WEB-EX-12, 13, 15, 18 | `tests/test_us5_1_batch_assessment.py` |
| US5.2 Sort/filter | WEB-EX-14, 15, 17, 18 | `tests/test_us5_2_sort_filter.py` |
| Integration | WEB-EX-04, 08, 09, 15 | `tests/test_stage13_integration.py` |

## 7. Key Boundaries and Pass Rules

| Boundary | Pass rule |
|---|---|
| Completeness | Below 50% is Insufficient with no band; exactly 50% is eligible with caveat |
| Risk bands | Low below 10%; Medium 10% to below 60%; High at or above 60% |
| CSV | Exact `account_id` header; 0-100 rows accepted by current contract; 101 rejected |
| Decision | Only completed scored result; Override reason required; duplicate prevented |
| Follow-up | Completed or Insufficient result; reason/status visible; update and clear |
| Privacy/oversight | Offline fixtures; minimal record; no platform action or definitive verdict |
| Return-state privacy | Only the displayed whitelisted preview/result and visible review UI state are kept for the current tab after strict schema validation; no training label or raw source payload; Start new clears it |
| Accessibility | Text plus colour; labelled controls; keyboard path; no clipping at 200% |

A case passes only when every stated expected result is visibly true. Partial
success is recorded as Fail and must not be silently marked Pass.

## 8. Exit Criteria and Definition of Done

This Testing Plan is ready for handover when:

- the first three selector options match the documented label-free dataset rows;
- all six tracked browser-upload files open and contain the documented rows;
- the PDF matches the latest Markdown and is readable in monochrome;
- all original automated tests, JavaScript syntax and Run Sheet checks pass;
- every WEB-EX case has a truthful status or remains explicitly Not executed;
- failures have a defect ID and retest result;
- no Critical or High defect remains unresolved; and
- the team updates Trello and approval status without inventing evidence.

Writing the case is not proof that the GUI passed it. Direct browser execution,
clean-environment confirmation and target-user UAT remain separate team actions.
