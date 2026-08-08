# System architecture

## Iteration 1 Release Candidate

The application is a single offline FastAPI service with a static browser
interface. It has four explicit boundaries:

1. `frontend/` presents analyst-facing information.
2. `backend/app/` validates requests, coordinates assessment work, and exposes
   versioned HTTP interfaces.
3. `backend/ml/` cleans offline research data, constructs the approved feature
   vector, trains the XGBoost model, and generates SHAP explanations.
4. `backend/app/database.py` stores expiring pseudonymous assessment context and
   minimal decision/follow-up references in a local SQLite database.

The dataset adapter is the only account-data source in Iteration 1. There is no
live Twitter/X client and no enforcement integration.

```text
Browser shell
    -> FastAPI validation/orchestration
        -> offline DatasetAdapter
        -> deterministic feature pipeline
        -> versioned XGBoost + SHAP artifacts
        -> minimal pseudonymous feedback store
```

Single-account and batch assessment share the same assessment orchestration,
ensuring one fixture produces the same completeness, score and band. Batch
sorting and filtering happen only in the browser over a copied result array; no
assessment endpoint is called and no stored decision is changed.

`backend/app/main.py` now performs application assembly only.
`assessment_service.py` owns the scoring workflow, `routes.py` exposes focused
public/assessment/review routers, and `context.py` provides injected services.
Synchronous model, SHAP, batch and SQLite handlers are dispatched through
FastAPI's worker thread pool rather than blocking its asynchronous event loop.

The browser follows the same separation: `app.js` coordinates intake,
`api-client.js` provides timeouts and safe JSON handling,
`assessment-state.js` validates versioned session data, and dedicated view,
review and batch controllers own their respective controls.

The model-information page presents verified values from the tracked model
contract. Runtime SQLite data and generated training splits remain ignored.
Approved model artifacts and curated demo fixtures are tracked for reproducible
offline execution.
