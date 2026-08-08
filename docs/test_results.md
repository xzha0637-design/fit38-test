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
86 passed, 0 failed
```

JavaScript syntax checks:

```powershell
node --check frontend/app.js
node --check frontend/api-client.js
node --check frontend/assessment-state.js
node --check frontend/assessment-view.js
node --check frontend/batch-results.js
node --check frontend/batch-controller.js
node --check frontend/review-controller.js
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
- the three selector paths produce the documented deterministic results:
  **2% / Low**, **30% / Medium** and **91% / High**;
- source provenance, completeness, missing values and the three contributing
  factors remain visibly separated from model-generated output;
- Confirm and Override decisions, required Override reasons, Follow-up save and
  Follow-up update all return a no-platform-action acknowledgement;
- the plain-language model guidance appears before the optional, collapsed
  technical record; and
- returning from model information restores the same score, band, assessment
  time and three contributing factors in the same browser tab, keeps the saved
  Follow-up reason/status and shows only the acknowledgement for an already
  submitted decision instead of exposing its form again;
- the tracked `tests/fixtures/browser_batch.csv` example reports 7 total,
  4 Completed and 3 Failed, and the documented High, Insufficient,
  Not reviewable and combined filter counts are 1, 1, 3 and 1; and
- a separate six-row alias/error audit reports 3 Completed and 3 Failed,
  including canonical duplicate detection for `20611469` and `DeFotis`.

The result page was checked at 1280 x 720 and an emulated 390 x 844 viewport.
At both sizes, all visible element bounds stayed within the viewport, no text
was clipped and the document did not require horizontal page scrolling. Browser
runtime monitoring recorded no console exception or log error during the batch
and filter walkthrough. No screenshot, HAR or console-export artifact is
required for this execution record.

## Coverage summary

The suite includes all 12 User Stories and cumulative regression coverage for:

- input normalisation, offline lookup, preview and reset/recovery;
- completeness boundaries and missing-data handling;
- real artifact loading, deterministic project-dataset Low/Medium/High scoring
  and failures;
- ordered SHAP explanations, uncertainty and model information;
- plain-language landing/model guidance and same-tab result restoration;
- analyst decisions, follow-up, restart-safe expiring pseudonymous context and
  authorised access;
- CSV validation, partial success, progress/count contracts;
- canonical ID/username deduplication, bounded probability validation and
  cross-origin Follow-up preflight;
- browser timeouts, non-JSON handling, strict state validation and restored
  decision/follow-up UI state;
- non-mutating sorting/filtering and clear-without-rerun behaviour;
- integrated main path, data contracts, batch/single consistency, controlled
  errors, accessibility markers and stale-state prevention.

Detailed AC-to-test names are in `docs/test_mapping.md`.
