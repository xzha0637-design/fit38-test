$ErrorActionPreference = "Stop"

python -m uvicorn backend.app.main:app --reload
