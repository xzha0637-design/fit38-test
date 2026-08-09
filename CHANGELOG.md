# Changelog

## Iteration 2 UI and verification hardening

- Added a plain-language suggested human-review priority and directed focus to
  each completed assessment result.
- Presented risk as a score out of 100 and translated encoded binary factor
  values into Yes/No.
- Bounded CSV uploads to 100 KB, locked the picker during processing and kept
  mobile batch-table scrolling inside its labelled region.
- Corrected the Profile completeness definition, moved the developer API link
  to the footer and added privacy guidance to stored-note fields.
- Updated the application to `0.2.0`, refreshed the Iteration 2 Testing Plan and
  added matching GitHub Actions and GitLab CI quality checks.

## Robustness audit hardening

- Allowed cross-origin Follow-up `PUT` requests and converted blocking model,
  SHAP, batch and SQLite handlers to FastAPI worker-thread routes.
- Persisted expiring minimal assessment context across service restarts, moved
  new references to full UUIDs and added automatic expiry cleanup.
- Deduplicated batch aliases after canonical account resolution and rejected
  finite model probabilities outside 0–1.
- Added a shared browser timeout/JSON client, safe Follow-up busy/error states,
  strict versioned session validation and review-state restoration.
- Kept native hidden states authoritative over component layout, cache-busted
  release assets and aligned restored factor validation with the nullable API
  label contract.
- Rejected empty or malformed threshold-selection arrays before metric
  calculation.
- Split backend application assembly/assessment/routes and browser API/state/
  view/review/batch responsibilities into focused documented modules.

## Tutor-feedback usability hardening

- Replaced the first three selector choices with label-free static accounts from
  the two project datasets while retaining synthetic fixtures for regression.
- Rewrote the landing page to state the task, outputs, human-decision boundary
  and no-enforcement rule in plain language.
- Added a first-view model-guidance link and reorganised model information so
  ordinary guidance precedes a collapsed technical record.
- Preserved the current whitelisted preview and assessment result in the same
  browser tab when an analyst visits and returns from model information.
- Expanded the Testing Plan, demo instructions, privacy/data documentation and
  regression suite for the tutor-facing interactive walkthrough.

## Stage 13 — Integrated MVP RC1

- Added cross-story integration, batch/single consistency, privacy,
  accessibility, error-matrix and stale-state regression tests.
- Fixed stale follow-up state and inherited batch filters between workflows.
- Added a repeatable Run Sheet check, main demo script, Bug Log, test results
  and final evidence summary.
- Refreshed architecture, data contracts, README and final handover.

## Stage 12 — US5.2 Sort and filter

- Added risk-score sorting and risk-band, completeness and review-status filters.
- Displays active filter descriptions and matching-record counts.
- Clearing controls restores original row order from the in-memory result set.
- Uses non-mutating transformations and never reruns assessments.

## Stage 11 — US5.1 Batch assessment

- Added documented CSV template upload with a 100-row limit.
- Validates file type, exact header, identifier format and duplicates.
- Continues valid offline assessments while reporting row-level failures.
- Displays persistent processing progress and completed/failed counts.

## Stage 10 — US3.2 Model information

- Added a directly addressable model information and limitations page.
- Published verified model versions, dataset names, metrics and evaluation date.
- Disclosed unsupported uses, missing calibration evidence and known shift risks.
- Linked scored and Insufficient data result sections directly to the page.

## Stage 09 — US4.3 Follow-up

- Added authorised follow-up flag, update and clear workflows.
- Supports completed and Insufficient data assessments.
- Persists only a minimal pseudonymous follow-up record.

## Stage 08 — US4.2 Data protection

- Limited persistence to the approved pseudonymous feedback record.
- Removed exception messages/payload values from application logs.
- Added authorised project-role access for stored feedback.

## Stage 07 — US1.3 Recovery and reset

- Added distinct unknown/data-timeout/model-timeout/malformed-response states.
- Added Retry and Start new assessment controls.
- Added full stale-result clearing and focus restoration.

## Stage 06 — US4.1 Confirm or override

- Added accountable Confirm/Override decisions with required override reason.
- Added minimal pseudonymous feedback storage and duplicate prevention.
- Added explicit human-final/no-platform-action acknowledgement.

## Stage 05 — US3.1 Explanation and uncertainty

- Added ordered top-three SHAP factors with plain labels, direction, and values.
- Added completeness/threshold-aware uncertainty copy.
- Kept the non-verdict disclaimer visible with every scored result.

## Stage 04 — US2.2 Risk scoring

- Added the tracked `xgb-offline-v1` runtime model and `threshold-v1` boundaries.
- Added 0–100 risk score, title-cased band, model/threshold versions, and time.
- Added text-plus-colour accessible result presentation.
- Added controlled retryable scoring failures without partial results.

## Stage 03 — US2.1 Feature completeness

- Added the versioned 12-feature completeness endpoint and UI meter.
- Enforced the inclusive 50% scoring boundary.
- Added Insufficient data handling without a risk band.
- Added plain-language missing-feature labels and persistent caveat.

## Stage 02 — US1.2 Account preview

- Added a whitelisted public-account preview presenter and endpoint.
- Added grouped profile, activity, and follower/following evidence.
- Preserved missing fields as null and named them in plain language.
- Added explicit source-data and model-output separation in the interface.

## Stage 01 — US1.1 Account intake

- Added offline identifier validation and optional `@` normalisation.
- Added deterministic Low/Medium/High demonstration fixtures and selector.
- Added an accessible intake form with adjacent validation and visible loading
  state.
- Added the offline `/api/v1/intake` contract and AC-mapped tests.

## Stage 00 — Project scaffold

- Added the accessible Signal Review application shell.
- Centralised application, API, model-contract, and threshold-contract versions.
- Added architecture, data-contract, model, privacy, limitation, and test-mapping
  documentation.
- Added reproducible PowerShell run and test commands.
- Added scaffold-level regression tests.

## Provided backend baseline

- Imported the coordinator-provided FastAPI, XGBoost, SHAP, offline dataset, and
  minimal feedback-store implementation.
