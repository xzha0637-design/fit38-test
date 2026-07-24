# Stage handover

- **Stage:** 01 — US1.1 Account Intake
- **User Story:** Submit or select a single account
- **Primary owner:** Wei Zhang
- **Branch:** `stage/01-us1.1-account-intake`

## Summary

Added an offline intake workflow with validated identifiers, optional `@`
normalisation, deterministic representative Low/Medium/High fixtures, visible
loading and adjacent error states, and keyboard-native labelled controls.

## Files added

- `data/fixtures/demo_accounts.csv`
- `frontend/app.js`
- `tests/test_us1_1_account_intake.py`

## Files modified

- `README.md`
- `.env.example`
- `CHANGELOG.md`
- `STAGE_HANDOVER.md`
- `backend/app/config.py`
- `backend/app/data_adapter.py`
- `backend/app/main.py`
- `backend/app/schemas.py`
- `frontend/index.html`
- `frontend/styles.css`
- `docs/data_contract.md`
- `docs/test_mapping.md`

## Files removed

None.

## Acceptance Criteria mapping

All six US1.1 criteria map to named tests in `docs/test_mapping.md`. The intake
endpoint only resolves tracked offline fixtures and never makes a platform call.

## Tests

- **Written:** four US1.1 tests covering AC1–AC6.
- **Executed:** `python -m pytest --basetemp ".pytest-tmp"`.
- **Passed:** 19 tests in 2.34 seconds.
- **Failed:** 0.
- **Not executed:** manual browser keyboard walkthrough.

## Known issues

- Risk scoring and account attribute preview are intentionally delivered by later
  stages.
- The Low/Medium/High selector text describes representative test scenarios; it
  is not a definitive label for an account.

## Manual verification

1. Run `.\scripts\run_app.ps1`.
2. Tab through the input, selector, and Begin assessment button.
3. Submit blank and invalid values and confirm the adjacent actionable message.
4. Select each demonstration scenario and confirm the input is populated.
5. Submit `@CIVIC_UPDATES` and `civic_updates`; confirm the same canonical account.

## Next-stage notes

Stage 02 displays approved public profile, activity, and network fields while
visually separating source evidence from future model-generated output.
