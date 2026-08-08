import json

import joblib
import numpy as np
import pandas as pd
import pytest
from xgboost import XGBClassifier

from backend.app.model_service import ModelService
from backend.ml.features import FEATURE_NAMES
from backend.ml.pipeline import make_preprocessor, select_risk_thresholds


def test_threshold_selection_returns_ordered_thresholds() -> None:
    thresholds = select_risk_thresholds(
        np.array([0, 0, 0, 1, 1, 1]),
        np.array([0.05, 0.2, 0.7, 0.3, 0.75, 0.95]),
    )
    assert 0 < thresholds["medium"] < thresholds["high"] < 1


@pytest.mark.parametrize(
    ("labels", "probabilities", "message"),
    [
        (np.array([]), np.array([]), "must not be empty"),
        (np.array([0, 1]), np.array([0.2]), "equal length"),
        (np.array([[0, 1]]), np.array([0.2, 0.8]), "one-dimensional"),
        (np.array([0, 2]), np.array([0.2, 0.8]), "only 0 or 1"),
        (np.array([0, 1]), np.array([0.2, 1.2]), "between 0 and 1"),
        (np.array([0, 1]), np.array([0.2, np.nan]), "all be finite"),
    ],
)
def test_threshold_selection_rejects_invalid_validation_inputs(
    labels,
    probabilities,
    message,
) -> None:
    """Invalid validation arrays fail before producing NaN threshold metadata."""

    with pytest.raises(ValueError, match=message):
        select_risk_thresholds(labels, probabilities)


def test_model_artifacts_load_score_and_explain(tmp_path) -> None:
    rng = np.random.default_rng(42)
    features = pd.DataFrame(
        {
            name: rng.uniform(0.1, 20.0, size=60)
            for name in FEATURE_NAMES
        }
    )
    for boolean_name in ["verified", "uses_default_profile_image", "has_description"]:
        features[boolean_name] = rng.integers(0, 2, size=len(features))
    labels = np.array([0, 1] * 30)

    preprocessor = make_preprocessor()
    transformed = preprocessor.fit_transform(features)
    model = XGBClassifier(
        n_estimators=4,
        max_depth=2,
        tree_method="hist",
        random_state=42,
        eval_metric="logloss",
    )
    model.fit(transformed, labels)
    model.save_model(tmp_path / "xgboost_model.json")
    joblib.dump(preprocessor, tmp_path / "preprocessor.joblib")
    (tmp_path / "model_metadata.json").write_text(
        json.dumps(
            {
                "model_id": "fixture_model",
                "feature_names": FEATURE_NAMES,
                "transformed_feature_names": preprocessor.get_feature_names_out().tolist(),
                "thresholds": {"medium": 0.3, "high": 0.7},
                "confidence_margin": 0.08,
            }
        ),
        encoding="utf-8",
    )

    service = ModelService(tmp_path)
    score = service.score(features.iloc[[0]], completeness=1.0)
    factors = service.explain(features.iloc[[0]])

    assert service.ready
    assert service.model_id == "fixture_model"
    assert 0 <= score.probability <= 1
    assert score.band in {"low", "medium", "high"}
    assert len(factors) == 3


def test_missing_artifacts_keep_service_unavailable(tmp_path) -> None:
    service = ModelService(tmp_path)
    assert not service.ready
    assert sorted(service.missing_artifacts) == sorted(
        ["xgboost_model.json", "preprocessor.joblib", "model_metadata.json"]
    )
