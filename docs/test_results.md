# Iteration 2 Test Results

## Iteration 2 verification environment

- Date: 9 August 2026
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
91 passed in 8.24s, 0 failed
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

Both CI YAML files parsed successfully, all seven JavaScript modules passed
`node --check`, `python -m pip check` reported no broken requirements, and
`git diff --check` reported no whitespace error.

## Selected browser smoke result

The local interface was exercised in the Codex in-app browser against the
tracked runtime model. The walkthrough confirmed that:

- the landing page explains the purpose, output and no-enforcement boundary;
- the header/footer report Iteration 2 and application version 0.2.0, while the
  Developer API link remains in the footer;
- the selector shows the real project-dataset examples `@DeFotis`, `@OGLexa`
  and `@everyletterbot`;
- the three selector paths produce the documented deterministic results:
  **2 / 100 Low**, **30 / 100 Medium** and **91 / 100 High**;
- source provenance, completeness, missing values and the three contributing
  factors remain visibly separated from model-generated output;
- each completed result receives focus, displays the suggested human-review
  priority, and renders a binary Verification status value as **Yes** rather
  than `1`;
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
- selecting the 749,668-byte tracked dataset CSV is rejected before processing
  with the explicit 100 KB limit message;
- a separate six-row alias/error audit reports 3 Completed and 3 Failed,
  including canonical duplicate detection for `20611469` and `DeFotis`.

The current result walkthrough covered 1280 x 720. Batch layout was retested at
390 x 844 and 375 x 667 outer viewports with the tracked seven-row CSV. At the
narrower size, the document width remained equal to the 360-pixel client
viewport while the 736-pixel table scrolled inside its 279-pixel labelled
container, so the page itself did not scroll horizontally. No screenshot, HAR
or console-export artifact is required for this execution record.

This is selected smoke evidence, not a formal execution record for all 18
WEB-EX cases. Those cases remain **Not executed** in `docs/testing_plan.md`
until a named team member records the browser, viewport, actual result and
Pass/Fail status for each case.

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
- suggested human-review priority, result focus, out-of-100 score wording,
  human-readable binary factors and sensitive-note guidance;
- CSV size/input-lock safeguards, contained mobile batch scrolling and CI
  quality-gate configuration;
- non-mutating sorting/filtering and clear-without-rerun behaviour;
- integrated main path, data contracts, batch/single consistency, controlled
  errors, accessibility markers and stale-state prevention.

Detailed AC-to-test names are in `docs/test_mapping.md`.
