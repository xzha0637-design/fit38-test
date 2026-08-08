from typing import Any

import numpy as np
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.metrics import confusion_matrix, f1_score, precision_score, recall_score, roc_auc_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import FunctionTransformer, StandardScaler

from backend.ml.features import BOOLEAN_FEATURES, NUMERIC_FEATURES


def _validated_binary_inputs(
    labels: np.ndarray,
    probabilities: np.ndarray,
) -> tuple[np.ndarray, np.ndarray]:
    """Return aligned one-dimensional binary labels and bounded probabilities."""

    label_values = np.asarray(labels)
    probability_values = np.asarray(probabilities, dtype=float)
    if label_values.ndim != 1 or probability_values.ndim != 1:
        raise ValueError("Validation labels and probabilities must be one-dimensional.")
    if label_values.size == 0 or probability_values.size == 0:
        raise ValueError("Validation labels and probabilities must not be empty.")
    if label_values.size != probability_values.size:
        raise ValueError("Validation labels and probabilities must have equal length.")
    try:
        numeric_labels = label_values.astype(float)
    except (TypeError, ValueError) as exc:
        raise ValueError("Validation labels must contain only 0 or 1.") from exc
    if not np.isfinite(numeric_labels).all() or not np.isin(
        numeric_labels,
        [0.0, 1.0],
    ).all():
        raise ValueError("Validation labels must contain only 0 or 1.")
    if not np.isfinite(probability_values).all():
        raise ValueError("Validation probabilities must all be finite.")
    if ((probability_values < 0.0) | (probability_values > 1.0)).any():
        raise ValueError("Validation probabilities must be between 0 and 1.")
    return numeric_labels.astype(int), probability_values


def make_preprocessor() -> ColumnTransformer:
    """Build the versioned numeric and Boolean preprocessing pipeline."""

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
    """Map one model output to Low, Medium, or High using saved thresholds."""

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

    labels, probabilities = _validated_binary_inputs(labels, probabilities)
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
    if best is None:  # Defensive: the fixed threshold grid is expected to be non-empty.
        raise RuntimeError("The risk-threshold search grid is empty.")
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
    """Calculate the recorded binary evaluation metrics at one threshold."""

    labels, probabilities = _validated_binary_inputs(labels, probabilities)
    predictions = (probabilities >= threshold).astype(int)
    return {
        "threshold": float(threshold),
        "f1": float(f1_score(labels, predictions, zero_division=0)),
        "precision": float(precision_score(labels, predictions, zero_division=0)),
        "recall": float(recall_score(labels, predictions, zero_division=0)),
        "roc_auc": float(roc_auc_score(labels, probabilities)),
        "confusion_matrix": confusion_matrix(labels, predictions).astype(int).tolist(),
    }
