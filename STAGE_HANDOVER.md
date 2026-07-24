# Stage handover

- **Stage:** 00 — Project Scaffold
- **User Story:** Foundation (no full User Story implemented)
- **Primary owner:** Wei Zhang
- **Branch:** `stage/00-project-scaffold`

## Summary

Created a runnable browser application shell around the supplied FastAPI/ML
backend, centralised stable version constants, added the required technical
documentation and reproducible run/test scripts, and preserved the existing
offline XGBoost/SHAP pipeline.

## Files added

- `frontend/index.html`
- `frontend/styles.css`
- `backend/app/version.py`
- `tests/test_scaffold.py`
- `scripts/run_app.ps1`
- `scripts/run_tests.ps1`
- `docs/architecture.md`
- `docs/data_contract.md`
- `docs/model_integration.md`
- `docs/privacy.md`
- `docs/known_limitations.md`
- `docs/test_mapping.md`
- `CHANGELOG.md`
- `STAGE_HANDOVER.md`

## Files modified

- `.gitignore`
- `README.md`
- `backend/app/main.py`

## Files removed

None.

## Requirement mapping

- Application shell: root route and `frontend/`.
- Offline fixture loader and model interface: supplied `DatasetAdapter` and
  `ModelService`, retained and documented.
- Input/output schemas: supplied Pydantic schemas, retained and documented.
- Error foundation: supplied exception handlers plus scaffold 404 regression.
- Stable configuration/version constants: `config.py` and `version.py`.
- Run/test commands: `scripts/run_app.ps1` and `scripts/run_tests.ps1`.

## Tests

- **Written:** two scaffold tests.
- **Executed:** `python -m pytest --basetemp ".pytest-tmp"`.
- **Passed:** 15 tests in 2.20 seconds.
- **Failed:** 0.
- **Not executed:** browser visual inspection.

## Known issues

- Model artifacts and demo fixtures must be generated before the full API health
  check becomes ready.
- Account intake controls intentionally begin in Stage 01.

## Manual verification

1. Activate the `fit5238-backend` Conda environment.
2. Run `python -m backend.ml.train`.
3. Run `.\scripts\run_app.ps1`.
4. Open `http://127.0.0.1:8000/` and verify the shell and API documentation link.

## Next-stage notes

Stage 01 adds validated offline account input, representative demo selection,
loading state, normalisation, and keyboard/programmatic labels.
