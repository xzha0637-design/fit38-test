# FIT5238 Team SA34 — Signal Review

**Current delivery branch:** `fix/full-robustness-audit-findings`

**Update owner:** Team SA34

**Current update:** Post-feedback robustness and maintainability follow-up

**Update status:** the supplied tutor feedback and the subsequent full-code
audit findings are implemented locally and covered by the cumulative suite.

This repository contains the cumulative Iteration 1 implementation for
account-level Twitter/X risk triage. Stage 00 adds a runnable, accessible browser
shell to the supplied backend foundation. Stage 01 adds validated offline account
intake and representative demonstration selection. Stage 02 adds a whitelisted
public-data preview with clear missing-value and content-origin labels.
Stage 03 adds the inclusive 50% evidence-sufficiency gate and names missing
required features. Stage 04 ships the trained `xgb-offline-v1` artifact and
versioned, accessible risk results. Stages 05–10 add explanations, uncertainty,
human decisions, recovery, protected persistence, follow-up and model
information. Stages 11–12 add validated batch assessment and non-mutating result
sorting/filtering. Stage 13 integrates and verifies the complete MVP.

The current implementation uses a local dataset adapter instead of the live X API.
An account ID is selected from a generated, label-free demo file. The returned score
is triage evidence for human review, not a bot verdict and not an enforcement action.

## Tutor screenshot follow-up

| Screenshot item | Visible outcome in the current interface |
|---:|---|
| 1 | The first three selector choices are static, label-free project-dataset accounts: `@DeFotis` (2% Low), `@OGLexa` (30% Medium), and `@everyletterbot` (91% High). |
| 2 | The landing page directly states that the tool reviews Twitter/X accounts for possible bot activity and names the score, risk level, factors, warnings, human decision boundary, and no-enforcement rule. |
| 3 | Model Information begins with three ordinary-language sections; exact versions, feature names, datasets, metrics, and limitations remain available in a collapsed technical record. |
| 4 | **Return to assessment** restores the same account, score, band, assessment time, and contributing factors in the current browser tab. |
| 14 | **Understand this review tool** is permanently visible in the landing-page hero before an assessment starts. |
| 15 | The unclear “Evidence for careful human review” headline is replaced by **Review Twitter/X accounts for possible bot activity.** |

These outcomes were delivered in commit `c4543a5` and checked through the
86-test suite, Run Sheet, JavaScript syntax checks, and a real browser
walkthrough. Detailed results are recorded in [Iteration 1 Test Results](docs/test_results.md).

## Robustness follow-up

The current branch also allows cross-origin follow-up `PUT` requests, rejects
out-of-range model probabilities, deduplicates batch aliases by canonical
account ID, and keeps expiring minimal assessment context in SQLite so a server
restart does not invalidate an assessment already shown to the analyst. Browser
requests have bounded timeouts and safe response parsing; decision and follow-up
UI state survives a same-tab Model Information visit after strict snapshot
validation.

Application assembly, assessment logic and route groups are separated under
`backend/app/`. The browser entry controller delegates API access, validated
session state, rendering, review actions and batch work to focused files under
`frontend/`. Blocking model, SHAP, batch and SQLite handlers are synchronous
FastAPI routes and therefore run in the framework thread pool.

## What is included

- Deterministic cleaning and stratified 70/15/15 splitting of the two tabular Twitter
  datasets in `dataset/`.
- Logistic Regression baseline and XGBoost primary classifier.
- Validation-selected Low, Medium, and High risk thresholds with a false-negative
  cost preference.
- TreeSHAP top-three explanations with a safe degraded result if SHAP fails.
- FastAPI endpoints for health, intake, preview, completeness, single/batch
  assessment, analyst decisions, follow-up and authorised feedback reads.
- SQLite storage containing expiring pseudonymous assessment context and minimal
  decision/follow-up records, never raw profiles.
- Accessible browser paths for single and CSV-batch review.
- Plain-language landing/model guidance and same-tab assessment restoration when
  returning from model information.
- Automated data, feature, artifact, API, privacy, accessibility, error,
  consistency and integration tests.

MGTAB is intentionally excluded from this MVP because its anonymous embedding
columns cannot be reproduced from public account fields at inference time.

## AI assistance disclosure

Generative AI assistance, including OpenAI Codex, was used for parts of the
code, tests, documentation and verification workflow. Team members retain
responsibility for reviewing and validating every submitted change. See the
[AI Usage Statement](docs/ai_usage_statement.md) for scope, safeguards and
verification responsibilities.

## Environment setup

Use the project-specific Conda environment so the backend is reproducible on another
machine:

```powershell
conda env create --file environment.yml
conda activate fit5238-backend
```

If the environment already exists after a dependency change:

```powershell
conda env update --file environment.yml --prune
conda activate fit5238-backend
```

Confirm that the correct interpreter is active:

```powershell
python --version
```

Python 3.10 is expected. Copy `.env.example` to `.env` only when path or CORS
configuration needs to be changed. No secret or X API credential is required for
the dataset-backed MVP.

## Generate local data and train the models

The approved runtime artifact is included. Run training again only when the
datasets, feature pipeline, or approved model version change:

```powershell
python -m backend.ml.train
```

The command:

1. merges `twitter_human_bots_cleaned.csv` and
   `twitter_bot_training_data2_cleaned.csv`;
2. removes invalid rows, every label-conflict account, and deterministic duplicates;
3. creates stratified train, validation, and test splits;
4. trains the baseline and XGBoost models and selects risk thresholds; and
5. creates 100 label-free research demo candidates from the test split.

The analyst selector uses three tracked, label-free static rows from the two
project datasets in `data/fixtures/demo_accounts.csv` so Low/Medium/High choices
remain stable across clean checkouts. Synthetic Low/Medium/High and boundary
fixtures remain later in the same file for regression and batch examples.

Generated data splits and runtime state remain local:

```text
backend/data/generated/   # train/validation/test splits and demo candidates
backend/runtime/          # SQLite feedback store and other runtime files
```

The versioned runtime model is tracked at `models/xgb-offline-v1/`.

## Run the backend

```powershell
python -m uvicorn backend.app.main:app --reload
```

Open the application at <http://127.0.0.1:8000/>. OpenAPI documentation is
available at <http://127.0.0.1:8000/docs>. The health
endpoint returns HTTP 503 with the missing artifact names until training has run.

The equivalent repository command is:

```powershell
.\scripts\run_app.ps1
```

### Complete PowerShell smoke flow

List demo accounts and choose the first one:

```powershell
$demo = Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/v1/demo/accounts?limit=1"
$accountId = $demo.accounts[0].account_id
$accountId
```

Submit an assessment:

```powershell
$assessmentBody = @{
    platform = "x"
    account_id = $accountId
} | ConvertTo-Json

$result = Invoke-RestMethod `
    -Method Post `
    -Uri "http://127.0.0.1:8000/api/v1/assessments" `
    -ContentType "application/json" `
    -Body $assessmentBody
$result | ConvertTo-Json -Depth 6
```

Record one analyst override:

```powershell
$overrideBody = @{
    override_label = "uncertain"
    reason_code = "manual_review"
} | ConvertTo-Json

Invoke-RestMethod `
    -Method Post `
    -Uri "http://127.0.0.1:8000/api/v1/assessments/$($result.assessment_id)/override" `
    -ContentType "application/json" `
    -Body $overrideBody
```

## API summary

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/api/v1/health` | Model, demo adapter, and SQLite readiness |
| `GET` | `/api/v1/demo/accounts?limit=20` | Label-free account IDs for local demonstration |
| `POST` | `/api/v1/intake` | Validate and normalise one offline identifier |
| `GET` | `/api/v1/accounts/{account_id}/preview` | Approved public-data preview |
| `GET` | `/api/v1/accounts/{account_id}/completeness` | Evidence-sufficiency result |
| `POST` | `/api/v1/assessments` | Validate, score, explain, and present one account |
| `POST` | `/api/v1/batch-assessments` | Validate and assess up to 100 CSV rows |
| `POST` | `/api/v1/assessments/{assessment_id}/decision` | Record confirm/override |
| `PUT` | `/api/v1/assessments/{assessment_id}/follow-up` | Flag, update or clear follow-up |
| `POST` | `/api/v1/assessments/{assessment_id}/override` | Record one minimal analyst override |
| `GET` | `/api/v1/feedback/decisions` | Authorised pseudonymous feedback read |
| `GET` | `/model-information` | Model evidence, limitations and prohibited uses |

Assessment request:

```json
{
  "platform": "x",
  "account_id": "2244994945"
}
```

The demo adapter accepts only IDs returned by the demo endpoint. It does not make a
network request to X. Live X API integration can later replace this adapter without
changing the internal feature, scoring, or response contracts.

## Tests

```powershell
python -m pytest --basetemp ".pytest-tmp"
```

or:

```powershell
.\scripts\run_tests.ps1
```

Tests use temporary fixtures and do not depend on locally generated model or demo
files. To verify a clean first-run state, remove only the ignored generated
directories, run training again, and repeat the smoke flow.

JavaScript syntax verification covers every browser module:

```powershell
Get-ChildItem frontend -Filter *.js | ForEach-Object { node --check $_.FullName }
```

## Release evidence

- [MVP definition](docs/mvp_definition.md)
- [Product Backlog and User Stories](docs/product_backlog.md)
- [AI Usage Statement](docs/ai_usage_statement.md)
- [Testing plan](docs/testing_plan.md)
- [Printable monochrome Testing Plan (PDF)](output/pdf/Iteration1_Testing_Plan.pdf)
- [UX and technical design](docs/ux_technical_design.md)
- [Run Sheet](docs/run_sheet.md)
- [Demo script](docs/demo_script.md)
- [Test results](docs/test_results.md)
- [Bug log](docs/bug_log.md)
- [Feedback and retrospective](docs/feedback_retrospective.md)
- [Trello handover](docs/trello_handover.md)
- [Acceptance-test mapping](docs/test_mapping.md)
- [Evidence summary](docs/evidence_summary.md)
- [Known limitations](docs/known_limitations.md)
