import math
from datetime import datetime, timezone
from uuid import uuid4

from fastapi.responses import JSONResponse

from backend.app.context import ApplicationContext
from backend.app.database import StoreUnavailableError
from backend.app.errors import ApiError, ExplanationUnavailableError, MalformedModelResponseError
from backend.app.model_service import ScoreResult
from backend.app.schemas import AssessmentRequest, AssessmentResponse, CompletenessResponse
from backend.app.version import THRESHOLD_VERSION
from backend.ml.features import (
    FeatureResult,
    build_feature_row,
    is_sufficient,
    missing_feature_labels,
)


TRIAGE_WARNING = "Triage evidence, not a verdict."
INSUFFICIENT_WARNING = (
    "Not enough public evidence is available to produce a risk assessment."
)
EXPLANATION_WARNING = (
    "The risk score is available, but its explanation could not be generated. "
    "Human review is required."
)


def build_completeness_response(
    context: ApplicationContext,
    account_id: str,
) -> CompletenessResponse:
    """Calculate the public evidence gate for one canonical fixture account."""

    if not context.data_adapter.ready:
        raise ApiError(
            503,
            "data_adapter_unavailable",
            "Offline demonstration accounts are temporarily unavailable.",
            retryable=True,
        )
    record = context.get_offline_record(account_id)
    feature_result = build_feature_row(record)
    eligible = is_sufficient(feature_result.completeness)
    missing = missing_feature_labels(feature_result)
    caveat = None
    if missing:
        caveat = (
            "Some required public features are missing. Interpret any later "
            "score with additional caution."
        )
    return CompletenessResponse(
        account_id=str(record["account_id"]),
        completeness=round(feature_result.completeness, 3),
        completeness_percentage=round(feature_result.completeness * 100),
        status="Eligible for scoring" if eligible else "Insufficient data",
        eligible_for_scoring=eligible,
        missing_features=missing,
        missing_data_caveat=caveat,
    )


def _record_assessment_context(
    context: ApplicationContext,
    assessment_id: str,
    recommendation: str,
) -> None:
    """Persist the minimal expiring context required by review actions."""

    try:
        context.feedback_store.record_assessment(
            assessment_id=assessment_id,
            model_id=context.model_service.model_id,
            recommendation=recommendation,
        )
    except StoreUnavailableError as exc:
        raise ApiError(
            500,
            "feedback_store_unavailable",
            "The assessment could not be recorded safely.",
        ) from exc


def _score_account(
    context: ApplicationContext,
    feature_result: FeatureResult,
) -> ScoreResult:
    """Run scoring and enforce the bounded model-output contract."""

    try:
        score = context.model_service.score(
            feature_result.frame,
            feature_result.completeness,
        )
        if (
            score is None
            or not math.isfinite(float(score.probability))
            or not 0.0 <= float(score.probability) <= 1.0
            or score.band not in {"low", "medium", "high"}
        ):
            raise MalformedModelResponseError("Invalid score contract.")
        return score
    except TimeoutError as exc:
        raise ApiError(
            503,
            "model_timeout",
            "Risk scoring timed out. Retry or start a new assessment.",
            retryable=True,
        ) from exc
    except MalformedModelResponseError as exc:
        raise ApiError(
            502,
            "malformed_model_response",
            "The model returned an invalid response. No score was displayed.",
            retryable=True,
        ) from exc
    except Exception as exc:
        raise ApiError(
            503,
            "scoring_unavailable",
            "Risk scoring is temporarily unavailable. Retry this assessment.",
            retryable=True,
        ) from exc


def _recommendation(status: str, confidence_level: str, risk_band: str) -> str:
    """Map a bounded score outcome to the non-enforcement triage recommendation."""

    if status == "completed_with_warning" or confidence_level == "low":
        return "monitor"
    return {
        "low": "no_concern",
        "medium": "monitor",
        "high": "prioritise",
    }[risk_band]


def _uncertainty(feature_result: FeatureResult, confidence_level: str) -> str:
    """Describe the strongest current reason for cautious interpretation."""

    if feature_result.completeness < 0.75:
        return (
            "Confidence is limited because several required public features "
            "are missing and model limitations still apply."
        )
    if confidence_level == "low":
        return (
            "The score is close to a decision threshold; small evidence changes "
            "could change the risk band."
        )
    return (
        "The score is clear of current thresholds, but cross-dataset and "
        "time-based model limitations still apply."
    )


def assess_account(
    context: ApplicationContext,
    request: AssessmentRequest,
) -> AssessmentResponse | JSONResponse:
    """Run completeness, scoring, explanation, and safe feedback setup."""

    if not context.model_service.ready:
        raise ApiError(
            503,
            "model_unavailable",
            "The model is unavailable. Run the local training command first.",
        )
    if not context.data_adapter.ready:
        raise ApiError(
            503,
            "data_adapter_unavailable",
            "Demo account data is unavailable. Run the local training command first.",
        )
    record = context.get_offline_record(request.account_id)
    canonical_account_id = str(record["account_id"])
    assessment_id = f"asmt_{uuid4().hex}"
    feature_result = build_feature_row(record)
    completeness = round(feature_result.completeness, 3)

    if not is_sufficient(feature_result.completeness):
        _record_assessment_context(context, assessment_id, "insufficient_data")
        response = AssessmentResponse(
            assessment_id=assessment_id,
            status="insufficient_data",
            account_id=canonical_account_id,
            data_completeness=completeness,
            warning=INSUFFICIENT_WARNING,
        )
        return JSONResponse(
            status_code=422,
            content=response.model_dump(mode="json"),
        )

    score = _score_account(context, feature_result)
    status = "completed"
    warning = TRIAGE_WARNING
    try:
        factors = context.model_service.explain(feature_result.frame)
    except ExplanationUnavailableError:
        status = "completed_with_warning"
        warning = EXPLANATION_WARNING
        factors = []

    recommendation = _recommendation(status, score.confidence.level, score.band)
    _record_assessment_context(context, assessment_id, recommendation)
    return AssessmentResponse(
        assessment_id=assessment_id,
        status=status,
        account_id=canonical_account_id,
        data_completeness=completeness,
        risk_probability=round(score.probability, 6),
        risk_score=round(score.probability * 100),
        risk_band=score.band,
        risk_band_label=score.band.title(),
        model_version=context.model_service.model_id,
        threshold_version=getattr(
            context.model_service,
            "threshold_version",
            THRESHOLD_VERSION,
        ),
        assessment_time=datetime.now(timezone.utc),
        confidence=score.confidence,
        uncertainty=_uncertainty(feature_result, score.confidence.level),
        top_factors=factors,
        recommendation=recommendation,
        warning=warning,
    )
