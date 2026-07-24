# Stage handover

- **Stage:** 02 — US1.2 Account Preview
- **User Story:** Preview public account information
- **Primary owner:** Wei Zhang
- **Branch:** `stage/02-us1.2-account-preview`

## Summary

Added a strictly whitelisted public-data preview that groups profile, activity,
and network evidence, leaves missing values visibly unavailable, and marks the
entire panel as offline source data distinct from model-generated output.

## Files added

- `backend/app/preview.py`
- `tests/test_us1_2_account_preview.py`

## Files modified

- `README.md`
- `CHANGELOG.md`
- `STAGE_HANDOVER.md`
- `backend/app/main.py`
- `backend/app/schemas.py`
- `frontend/index.html`
- `frontend/styles.css`
- `frontend/app.js`
- `docs/data_contract.md`
- `docs/test_mapping.md`

## Files removed

None.

## Acceptance Criteria mapping

All four US1.2 criteria map to named tests in `docs/test_mapping.md`.

## Tests

- **Written:** four US1.2 tests covering AC1–AC4.
- **Executed:** `python -m pytest --basetemp ".pytest-tmp"`.
- **Passed:** 23 tests in 2.82 seconds.
- **Failed:** 0.
- **Not executed:** manual browser screen-reader walkthrough.

## Known issues

- Completeness and model output are intentionally introduced in later stages.
- Posts per day is calculated from two displayed source values and is not model
  output.

## Manual verification

1. Run the application and submit each representative account.
2. Confirm identifier, profile, activity, and network groups appear.
3. Submit the higher-risk demo and confirm missing description/location show
   “Not available”.
4. Confirm the Source data badge and separate model-output placeholder remain
   visible.

## Next-stage notes

Stage 03 calculates the approved required-feature completeness, applies the 50%
boundary, and names missing required features.
