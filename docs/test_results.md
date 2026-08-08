# Iteration 1 Test Results

## Tutor-feedback verification environment

- Date: 8 August 2026
- OS: Windows
- Python: project Conda environment `fit5238-backend`
- Model: `xgb-offline-v1`
- Thresholds: `threshold-v1`
- Data source: tracked offline fixtures plus three label-free static rows from
  the two project datasets
- Live Twitter/X access: not used

## Automated result

Command:

```powershell
python -m pytest --basetemp ".pytest-tmp"
```

Result:

```text
70 passed in 5.74s
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

## Browser walkthrough result

The local interface was exercised in the Codex in-app browser against the
tracked runtime model. The walkthrough confirmed that:

- the landing page explains the purpose, output and no-enforcement boundary;
- the selector shows the real project-dataset examples `@DeFotis`, `@OGLexa`
  and `@everyletterbot`;
- `@everyletterbot` produces the documented deterministic **91% / High** result;
- the plain-language model guidance appears before the optional, collapsed
  technical record; and
- returning from model information restores the same score, band, assessment
  time and three contributing factors in the same browser tab.

Both inspected desktop pages had matching document and viewport widths, with
no horizontal page overflow. No screenshot, HAR or console-export artifact is
required for this execution record.

## Coverage summary

The suite includes all 12 User Stories and cumulative regression coverage for:

- input normalisation, offline lookup, preview and reset/recovery;
- completeness boundaries and missing-data handling;
- real artifact loading, deterministic project-dataset Low/Medium/High scoring
  and failures;
- ordered SHAP explanations, uncertainty and model information;
- plain-language landing/model guidance and same-tab result restoration;
- analyst decisions, follow-up, pseudonymous persistence and authorised access;
- CSV validation, partial success, progress/count contracts;
- non-mutating sorting/filtering and clear-without-rerun behaviour;
- integrated main path, data contracts, batch/single consistency, controlled
  errors, accessibility markers and stale-state prevention.

Detailed AC-to-test names are in `docs/test_mapping.md`.
