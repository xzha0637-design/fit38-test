# Stage handover

- **Stage:** 04 — US2.2 Risk Scoring
- **User Story:** Generate and interpret the risk result
- **Primary owner:** Xianze Zhang
- **Branch:** `stage/04-us2.2-risk-scoring`

## Summary

Trained and shipped the real `xgb-offline-v1` XGBoost runtime artifact, added
versioned thresholds, 0–100 score and accessible risk-band presentation, and
made scoring failures controlled, retryable, and free of stale/partial output.

## Files added

- `models/xgb-offline-v1/*`
- `tests/test_us2_2_risk_scoring.py`

## Files modified

- `.env.example`
- `README.md`
- `CHANGELOG.md`
- `STAGE_HANDOVER.md`
- `backend/app/config.py`
- `backend/app/main.py`
- `backend/app/model_service.py`
- `backend/app/schemas.py`
- `backend/app/version.py`
- `backend/ml/train.py`
- `frontend/index.html`
- `frontend/styles.css`
- `frontend/app.js`
- `docs/data_contract.md`
- `docs/model_integration.md`
- `docs/test_mapping.md`

## Files removed

None.

## Acceptance Criteria mapping

All seven US2.2 criteria map to named tests in `docs/test_mapping.md`.

## Tests

- **Written:** four US2.2 tests covering AC1–AC7.
- **Executed:** `python -m pytest --basetemp ".pytest-tmp"`.
- **Passed:** 31 tests in 3.27 seconds.
- **Failed:** 0 after correcting the test parser to accept the valid UTC `Z`
  suffix returned by Pydantic.
- **Not executed:** external automated WCAG contrast scanner.

## Known issues

- Model limitations and full evaluation context are delivered in Stage 10.
- Score calibration and cross-dataset generalisation remain limited; results are
  triage evidence only.

## Manual verification

1. Run the app from a clean checkout without retraining.
2. Assess the three representative fixtures and confirm Low, Medium, and High.
3. Confirm score, band text, model version, threshold version, time, and
   disclaimer remain visible.
4. Disable an artifact temporarily in a disposable copy and confirm a controlled
   retryable error with no partial score.

## Next-stage notes

Stage 05 enriches the scored result with the strongest plain-language factors,
observed values, direction, and a completeness/model-aware uncertainty caveat.
