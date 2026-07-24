# Changelog

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
