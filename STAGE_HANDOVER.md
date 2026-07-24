# Stage handover

- **Stage:** 05 — US3.1 Explanation and Uncertainty
- **Primary owner:** Zhongyao Zhang
- **Branch:** `stage/05-us3.1-explanation-uncertainty`

## Summary

Added the three strongest ordered SHAP factors with direction, plain labels and
observed values, plus uncertainty tied to the same completeness, score and model.

## Changed files

`backend/app/{main,model_service,schemas}.py`, `frontend/{index.html,styles.css,app.js}`,
`tests/test_us3_1_explanation_uncertainty.py`, README, CHANGELOG, test mapping,
and this handover.

## Acceptance Criteria and tests

All AC1–AC7 map to three named tests in `docs/test_mapping.md`.

- **Executed:** `python -m pytest --basetemp ".pytest-tmp"`.
- **Passed:** 34 tests in 3.38 seconds.
- **Failed:** 0.
- **Not executed:** manual screen-reader factor-list walkthrough.

## Known issues / next stage

SHAP failure safely degrades to the existing warning. Stage 06 adds accountable
human Confirm/Override decisions without platform action.
