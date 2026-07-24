# Changelog

## Stage 01 — US1.1 Account intake

- Added offline identifier validation and optional `@` normalisation.
- Added deterministic Low/Medium/High demonstration fixtures and selector.
- Added an accessible intake form with adjacent validation and visible loading
  state.
- Added the offline `/api/v1/intake` contract and AC-mapped tests.

## Stage 00 — Project scaffold

- Added the accessible Signal Review application shell.
- Centralised application, API, model-contract, and threshold-contract versions.
- Added architecture, data-contract, model, privacy, limitation, and test-mapping
  documentation.
- Added reproducible PowerShell run and test commands.
- Added scaffold-level regression tests.

## Provided backend baseline

- Imported the coordinator-provided FastAPI, XGBoost, SHAP, offline dataset, and
  minimal feedback-store implementation.
