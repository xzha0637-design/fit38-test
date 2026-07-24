# AI model integration

The supplied backend trains a deterministic XGBoost classifier from two cleaned
offline tabular datasets. A logistic-regression baseline is retained for
comparison. Validation data select versioned Low/Medium/High boundaries, and
TreeSHAP supplies up to three local factors.

Training is explicit:

```powershell
python -m backend.ml.train
```

The command writes ignored local artifacts under `backend/artifacts/`. Runtime
health is degraded until all required artifacts and the generated demo account
file exist. This prevents a placeholder score from being presented as AI output.

The same validated feature vector and model artifact yield the same probability
and band. Assessment references and timestamps may differ between requests.
