from typing import Any

import numpy as np
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.metrics import confusion_matrix, f1_score, precision_score, recall_score, roc_auc_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import FunctionTransformer, StandardScaler

from backend.ml.features import BOOLEAN_FEATURES, NUMERIC_FEATURES


def make_preprocessor() -> ColumnTransformer:
    numeric_pipeline = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="median", keep_empty_features=True)),
            (
                "log1p",
                FunctionTransformer(
                    np.log1p,
                    validate=False,
                    feature_names_out="one-to-one",
                ),
            ),
            ("scaler", StandardScaler()),
        ]
    )
    boolean_pipeline = Pipeline(
        steps=[
            (
                "imputer",
                SimpleImputer(
                    strategy="most_frequent",
                    keep_empty_features=True,
                ),
            )
        ]
    )
    return ColumnTransformer(
        transformers=[
            ("numeric", numeric_pipeline, NUMERIC_FEATURES),
            ("boolean", boolean_pipeline, BOOLEAN_FEATURES),
        ],
        verbose_feature_names_out=False,
    )


def probability_to_band(
    probability: float,
    medium_threshold: float,
    high_threshold: float,
) -> str:
    if probability < medium_threshold:
        return "low"
    if probability < high_threshold:
        return "medium"
    return "high"


def select_risk_thresholds(
    labels: np.ndarray,
    probabilities: np.ndarray,
) -> dict[str, float]:
    """Choose action bands using the agreed false-negative-heavy cost preference."""

    labels = np.asarray(labels, dtype=int)
    probabilities = np.asarray(probabilities, dtype=float)
    best: tuple[float, float, float, float] | None = None
    for medium in np.arange(0.10, 0.66, 0.05):
        for high in np.arange(max(0.40, medium + 0.10), 0.91, 0.05):
            bands = np.where(
                probabilities < medium,
                0,
                np.where(probabilities < high, 1, 2),
            )
            costs = np.zeros(len(labels), dtype=float)
            costs[(labels == 1) & (bands == 0)] = 5.0
            costs[(labels == 1) & (bands == 1)] = 1.0
            costs[(labels == 0) & (bands == 1)] = 0.25
            costs[(labels == 0) & (bands == 2)] = 1.0
            mean_cost = float(costs.mean())
            binary_recall = recall_score(labels, probabilities >= medium, zero_division=0)
            candidate = (mean_cost, -float(binary_recall), float(medium), float(high))
            if best is None or candidate < best:
                best = candidate
    if best is None:
        raise ValueError("Validation labels and probabilities must not be empty.")
    return {
        "medium": round(best[2], 4),
        "high": round(best[3], 4),
        "validation_mean_cost": round(best[0], 6),
    }


def classification_metrics(
    labels: np.ndarray,
    probabilities: np.ndarray,
    threshold: float = 0.5,
) -> dict[str, Any]:
    labels = np.asarray(labels, dtype=int)
    probabilities = np.asarray(probabilities, dtype=float)
    predictions = (probabilities >= threshold).astype(int)
    return {
        "threshold": float(threshold),
        "f1": float(f1_score(labels, predictions, zero_division=0)),
        "precision": float(precision_score(labels, predictions, zero_division=0)),
        "recall": float(recall_score(labels, predictions, zero_division=0)),
        "roc_auc": float(roc_auc_score(labels, probabilities)),
        "confusion_matrix": confusion_matrix(labels, predictions).astype(int).tolist(),
    }
