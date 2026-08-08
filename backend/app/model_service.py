import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
import shap
from xgboost import XGBClassifier

from backend.app.errors import ExplanationUnavailableError, ModelUnavailableError
from backend.app.schemas import Confidence, TopFactor
from backend.ml.features import FEATURE_NAMES
from backend.ml.pipeline import probability_to_band


REQUIRED_ARTIFACTS = (
    "xgboost_model.json",
    "preprocessor.joblib",
    "model_metadata.json",
)

FEATURE_LABELS = {
    "account_age_days": "Account age",
    "followers_count": "Follower count",
    "following_count": "Following count",
    "follower_following_ratio": "The follower-to-following pattern",
    "tweet_count": "Tweet count",
    "posting_frequency": "Posting frequency",
    "description_length": "Description length",
    "username_length": "Username length",
    "profile_completeness": "Profile completeness",
    "verified": "Verification status",
    "uses_default_profile_image": "Use of a default profile image",
    "has_description": "Description availability",
}


@dataclass(frozen=True)
class ScoreResult:
    probability: float
    band: str
    confidence: Confidence


class ModelService:
    """Load the versioned artifact and expose safe score/explanation operations."""

    def __init__(self, artifact_dir: Path) -> None:
        self.artifact_dir = Path(artifact_dir)
        self.ready = False
        self.error: str | None = None
        self.explainer_error: str | None = None
        self.model: XGBClassifier | None = None
        self.preprocessor: Any = None
        self.explainer: Any = None
        self.metadata: dict[str, Any] = {}
        self.load()

    @property
    def missing_artifacts(self) -> list[str]:
        """List required artifact files that are absent from the model directory."""

        return [
            name for name in REQUIRED_ARTIFACTS if not (self.artifact_dir / name).is_file()
        ]

    @property
    def model_id(self) -> str:
        """Return the artifact model identifier or a safe unknown fallback."""

        return str(self.metadata.get("model_id", "unknown_model"))

    @property
    def threshold_version(self) -> str:
        """Return the version of the Low/Medium/High threshold policy."""

        return str(self.metadata.get("threshold_version", "unknown_threshold"))

    def load(self) -> None:
        """Validate and load metadata, preprocessing, model, and SHAP explainer."""

        missing = self.missing_artifacts
        if missing:
            self.error = f"Missing model artifacts: {', '.join(missing)}"
            self.ready = False
            return
        try:
            metadata = json.loads(
                (self.artifact_dir / "model_metadata.json").read_text(encoding="utf-8")
            )
            if metadata.get("feature_names") != FEATURE_NAMES:
                raise ValueError("Artifact feature schema does not match the runtime schema.")
            thresholds = metadata.get("thresholds", {})
            medium = float(thresholds["medium"])
            high = float(thresholds["high"])
            if not 0.0 < medium < high < 1.0:
                raise ValueError("Artifact risk thresholds are invalid.")
            model = XGBClassifier()
            model.load_model(self.artifact_dir / "xgboost_model.json")
            preprocessor = joblib.load(self.artifact_dir / "preprocessor.joblib")
            self.model = model
            self.preprocessor = preprocessor
            self.metadata = metadata
            self.ready = True
            self.error = None
            try:
                self.explainer = shap.TreeExplainer(model)
                self.explainer_error = None
            except Exception as exc:
                self.explainer = None
                self.explainer_error = str(exc)
        except Exception as exc:
            self.ready = False
            self.error = str(exc)

    def score(self, features: pd.DataFrame, completeness: float) -> ScoreResult:
        """Score one feature row and attach a band plus confidence rationale."""

        if not self.ready or self.model is None or self.preprocessor is None:
            raise ModelUnavailableError(self.error or "Model artifacts are unavailable.")
        transformed = self.preprocessor.transform(features)
        probability = float(self.model.predict_proba(transformed)[0, 1])
        if not np.isfinite(probability):
            raise RuntimeError("Model returned a non-finite probability.")
        thresholds = self.metadata["thresholds"]
        medium = float(thresholds["medium"])
        high = float(thresholds["high"])
        band = probability_to_band(probability, medium, high)
        margin = float(self.metadata.get("confidence_margin", 0.08))
        if completeness < 0.75:
            confidence = Confidence(
                level="low",
                basis="limited_feature_coverage",
            )
        elif min(abs(probability - medium), abs(probability - high)) < margin:
            confidence = Confidence(
                level="low",
                basis="close_to_decision_thresholds",
            )
        else:
            confidence = Confidence(
                level="high",
                basis="clear_of_decision_thresholds",
            )
        return ScoreResult(probability=probability, band=band, confidence=confidence)

    def explain(self, features: pd.DataFrame) -> list[TopFactor]:
        """Return up to three strongest SHAP factors in analyst-readable form."""

        if not self.ready or self.preprocessor is None:
            raise ModelUnavailableError(self.error or "Model artifacts are unavailable.")
        if self.explainer is None:
            raise ExplanationUnavailableError(
                self.explainer_error or "SHAP explainer is unavailable."
            )
        try:
            transformed = self.preprocessor.transform(features)
            values = self.explainer.shap_values(transformed)
            if isinstance(values, list):
                values = values[-1]
            values_array = np.asarray(values)
            if values_array.ndim == 3:
                values_array = values_array[:, :, -1]
            contributions = values_array[0]
            names = self.metadata.get("transformed_feature_names", FEATURE_NAMES)
            if len(names) != len(contributions):
                raise ValueError("SHAP output does not match the artifact feature schema.")
            ranking = np.argsort(np.abs(contributions))[::-1][:3]
            factors = []
            for index in ranking:
                feature = str(names[index])
                contribution = float(contributions[index])
                direction = "increases_risk" if contribution >= 0 else "decreases_risk"
                verb = "increased" if contribution >= 0 else "reduced"
                label = FEATURE_LABELS.get(feature, feature.replace("_", " ").title())
                observed = features.iloc[0].get(feature)
                observed_value = None
                if observed is not None and pd.notna(observed):
                    observed_value = (
                        f"{float(observed):.2f}".rstrip("0").rstrip(".")
                    )
                factors.append(
                    TopFactor(
                        feature=feature,
                        label=label,
                        direction=direction,
                        observed_value=observed_value,
                        contribution_magnitude=round(abs(contribution), 6),
                        evidence=f"{label} {verb} the estimated risk.",
                    )
                )
            return factors
        except ExplanationUnavailableError:
            raise
        except Exception as exc:
            raise ExplanationUnavailableError(str(exc)) from exc
