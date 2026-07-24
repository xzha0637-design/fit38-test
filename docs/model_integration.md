# AI model integration

The supplied backend trains a deterministic XGBoost classifier from two cleaned
offline tabular datasets. A logistic-regression baseline is retained for
comparison. Validation data select versioned Low/Medium/High boundaries, and
TreeSHAP supplies up to three local factors.

Training is explicit:

```powershell
python -m backend.ml.train
```

The release branch includes the approved runtime artifacts under
`models/xgb-offline-v1/`, allowing a clean checkout to run without retraining.
The training command deterministically rebuilds that versioned directory from
the tracked source data. Runtime health is degraded if an artifact is absent;
this prevents a placeholder score from being presented as AI output.

The same validated feature vector and model artifact yield the same probability
and band. Assessment references and timestamps may differ between requests.

Version `xgb-offline-v1` uses thresholds selected on the validation split:

- Low: probability below `0.10`
- Medium: probability from `0.10` up to but excluding `0.60`
- High: probability `0.60` or above

The threshold contract is `threshold-v1`.
