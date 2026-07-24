# System architecture

## Stage 00 baseline

The application is a single offline FastAPI service with a static browser shell.
It has four explicit boundaries:

1. `frontend/` presents analyst-facing information.
2. `backend/app/` validates requests, coordinates assessment work, and exposes
   versioned HTTP interfaces.
3. `backend/ml/` cleans offline research data, constructs the approved feature
   vector, trains the XGBoost model, and generates SHAP explanations.
4. `backend/app/database.py` stores only pseudonymous assessment and feedback
   references in a local SQLite database.

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

Generated model artifacts, demo fixtures, and runtime data are rebuilt locally
and are excluded from Git.
