# Iteration 1 Test Results

## Release-candidate environment

- Date: 24 July 2026
- OS: Windows
- Python: project Conda environment `fit5238-backend`
- Model: `xgb-offline-v1`
- Thresholds: `threshold-v1`
- Data source: tracked offline fixtures
- Live Twitter/X access: not used

## Automated result

Command:

```powershell
python -m pytest --basetemp ".pytest-tmp"
```

Result:

```text
63 passed in 5.47s
```

JavaScript syntax checks:

```powershell
node --check frontend/app.js
node --check frontend/batch-results.js
```

Run Sheet check:

```powershell
python -m scripts.verify_run_sheet
```

Result:

```text
RUN SHEET PASS: offline shell, model info, health, single and batch paths
```

## Coverage summary

The suite includes all 12 User Stories and cumulative regression coverage for:

- input normalisation, offline lookup, preview and reset/recovery;
- completeness boundaries and missing-data handling;
- real artifact loading, deterministic Low/Medium/High scoring and failures;
- ordered SHAP explanations, uncertainty and model information;
- analyst decisions, follow-up, pseudonymous persistence and authorised access;
- CSV validation, partial success, progress/count contracts;
- non-mutating sorting/filtering and clear-without-rerun behaviour;
- integrated main path, data contracts, batch/single consistency, controlled
  errors, accessibility markers and stale-state prevention.

Detailed AC-to-test names are in `docs/test_mapping.md`.
