import csv
import io
import json
import logging
import math
from datetime import datetime, timezone
from uuid import uuid4

from fastapi import FastAPI, Header, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from backend.app.config import PROJECT_ROOT, Settings
from backend.app.data_adapter import DatasetAdapter
from backend.app.database import (
    AssessmentNotFoundError,
    DuplicateOverrideError,
    FeedbackStore,
    StoreUnavailableError,
)
from backend.app.errors import (
    ApiError,
    ExplanationUnavailableError,
    MalformedModelResponseError,
)
from backend.app.model_service import ModelService
from backend.app.preview import build_public_preview
from backend.app.schemas import (
    AccountPreview,
    AssessmentRequest,
    AssessmentResponse,
    BatchRowResult,
    BatchUploadRequest,
    BatchUploadResponse,
    CompletenessResponse,
    DecisionRequest,
    DecisionResponse,
    DecisionFeedbackList,
    DemoAccountsResponse,
    ErrorDetail,
    ErrorResponse,
    FollowUpRequest,
    FollowUpResponse,
    HealthResponse,
    IntakeRequest,
    IntakeResponse,
    OverrideRequest,
    OverrideResponse,
    normalise_offline_identifier,
)
from backend.app.version import APP_VERSION, THRESHOLD_VERSION
from backend.ml.features import (
    build_feature_row,
    is_sufficient,
    missing_feature_labels,
)


LOGGER = logging.getLogger("bot_risk_backend")
TRIAGE_WARNING = "Triage evidence, not a verdict."
INSUFFICIENT_WARNING = (
    "Not enough public evidence is available to produce a risk assessment."
)
EXPLANATION_WARNING = (
    "The risk score is available, but its explanation could not be generated. "
    "Human review is required."
)
FRONTEND_DIR = PROJECT_ROOT / "frontend"


def _error_content(code: str, message: str, retryable: bool = False) -> dict:
    return ErrorResponse(
        error=ErrorDetail(code=code, message=message, retryable=retryable)
    ).model_dump(mode="json")


def create_app(
    settings: Settings | None = None,
    model_service: ModelService | None = None,
    data_adapter: DatasetAdapter | None = None,
    feedback_store: FeedbackStore | None = None,
) -> FastAPI:
    """Build the FastAPI app with injectable services for isolated testing."""

    settings = settings or Settings()
    logging.basicConfig(level=getattr(logging, settings.log_level.upper(), logging.INFO))

    model_service = model_service or ModelService(settings.artifact_dir)
    data_adapter = data_adapter or DatasetAdapter(settings.demo_data_path)
    feedback_store = feedback_store or FeedbackStore(settings.database_path)

    application = FastAPI(
        title="FIT5238 Bot Risk Scoring Tool",
        version=APP_VERSION,
        description=(
            "Iteration 1 dataset-backed MVP. Results support analyst triage and are "
            "not final bot determinations."
        ),
    )
    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=False,
        allow_methods=["GET", "POST"],
        allow_headers=["Content-Type", "X-Project-Role"],
    )
    application.state.settings = settings
    application.state.model_service = model_service
    application.state.data_adapter = data_adapter
    application.state.feedback_store = feedback_store
    application.mount(
        "/static",
        StaticFiles(directory=FRONTEND_DIR),
        name="static",
    )

    @application.get("/", include_in_schema=False)
    async def application_shell() -> FileResponse:
        """Serve the main browser assessment workspace."""

        return FileResponse(FRONTEND_DIR / "index.html")

    @application.get("/model-information", include_in_schema=False)
    async def model_information_page() -> FileResponse:
        """Serve the plain-language model evidence and limitations page."""

        return FileResponse(FRONTEND_DIR / "model-information.html")

    @application.exception_handler(ApiError)
    async def api_error_handler(_: Request, exc: ApiError) -> JSONResponse:
        """Translate controlled domain errors into the public error contract."""

        return JSONResponse(
            status_code=exc.status_code,
            content=_error_content(exc.code, exc.message, exc.retryable),
        )

    @application.exception_handler(RequestValidationError)
    async def validation_error_handler(
        _: Request, exc: RequestValidationError
    ) -> JSONResponse:
        """Return one safe field-level message for invalid request payloads."""

        first_error = exc.errors()[0] if exc.errors() else {}
        location = ".".join(str(part) for part in first_error.get("loc", [])[1:])
        message = "The request is invalid."
        if location:
            message = f"Invalid value for {location}."
        return JSONResponse(
            status_code=400,
            content=_error_content("invalid_request", message),
        )

    @application.exception_handler(Exception)
    async def unexpected_error_handler(_: Request, exc: Exception) -> JSONResponse:
        """Hide internal details while returning a traceable correlation ID."""

        correlation_id = uuid4().hex[:12]
        LOGGER.error(
            "Unhandled error [%s] type=%s",
            correlation_id,
            type(exc).__name__,
        )
        return JSONResponse(
            status_code=500,
            content=_error_content(
                "internal_error",
                f"An unexpected error occurred. Reference: {correlation_id}",
            ),
        )

    def get_offline_record(identifier: str) -> dict:
        """Fetch one demo record and normalise source failures to API errors."""

        try:
            record = data_adapter.get_account(identifier)
        except TimeoutError as exc:
            raise ApiError(
                503,
                "data_source_timeout",
                "Offline account data timed out. Retry or start a new assessment.",
                retryable=True,
            ) from exc
        if record is None:
            raise ApiError(
                404,
                "account_not_found",
                "The account is not available in the offline demonstration dataset. "
                "Choose a preloaded account.",
            )
        return record

    @application.get("/api/v1/health", response_model=HealthResponse)
    async def health() -> JSONResponse:
        """Report readiness of the model, demo adapter, and feedback store."""

        all_ready = model_service.ready and data_adapter.ready and feedback_store.ready
        response = HealthResponse(
            status="ok" if all_ready else "degraded",
            model="loaded" if model_service.ready else "unavailable",
            data_adapter="loaded" if data_adapter.ready else "unavailable",
            demo_account_count=data_adapter.account_count,
            feedback_store="ready" if feedback_store.ready else "unavailable",
            missing_artifacts=model_service.missing_artifacts,
        )
        return JSONResponse(
            status_code=200 if all_ready else 503,
            content=response.model_dump(mode="json"),
        )

    @application.get(
        "/api/v1/demo/accounts",
        response_model=DemoAccountsResponse,
    )
    async def demo_accounts(limit: int = 20) -> DemoAccountsResponse:
        """Return label-free account choices for the offline demonstration."""

        if limit < 1 or limit > 100:
            raise ApiError(400, "invalid_request", "Limit must be between 1 and 100.")
        if not data_adapter.ready:
            raise ApiError(
                503,
                "data_adapter_unavailable",
                "Demo account data is unavailable. Run the local training command first.",
            )
        accounts = data_adapter.list_accounts(limit)
        return DemoAccountsResponse(count=len(accounts), accounts=accounts)

    @application.post(
        "/api/v1/intake",
        response_model=IntakeResponse,
    )
    async def prepare_account_intake(request: IntakeRequest) -> IntakeResponse:
        """Validate one identifier and return its canonical display context."""

        if not data_adapter.ready:
            raise ApiError(
                503,
                "data_adapter_unavailable",
                "Offline demonstration accounts are temporarily unavailable.",
                retryable=True,
            )
        record = get_offline_record(request.identifier)
        username = DatasetAdapter._optional_text(record.get("username"))
        display_identifier = f"@{username}" if username else str(record["account_id"])
        return IntakeResponse(
            account_id=str(record["account_id"]),
            normalised_identifier=request.identifier,
            display_identifier=display_identifier,
        )

    @application.get(
        "/api/v1/accounts/{account_id}/preview",
        response_model=AccountPreview,
    )
    async def preview_account(account_id: str) -> AccountPreview:
        """Return only the approved public fields for analyst confirmation."""

        if not data_adapter.ready:
            raise ApiError(
                503,
                "data_adapter_unavailable",
                "Offline demonstration accounts are temporarily unavailable.",
                retryable=True,
            )
        record = get_offline_record(account_id)
        return build_public_preview(record)

    @application.get(
        "/api/v1/accounts/{account_id}/completeness",
        response_model=CompletenessResponse,
    )
    async def account_completeness(account_id: str) -> CompletenessResponse:
        """Calculate evidence coverage before any model score is requested."""

        if not data_adapter.ready:
            raise ApiError(
                503,
                "data_adapter_unavailable",
                "Offline demonstration accounts are temporarily unavailable.",
                retryable=True,
            )
        record = get_offline_record(account_id)
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

    @application.post(
        "/api/v1/assessments",
        response_model=AssessmentResponse,
    )
    async def create_assessment(request: AssessmentRequest):
        """Run completeness, scoring, explanation, and safe feedback setup."""

        if not model_service.ready:
            raise ApiError(
                503,
                "model_unavailable",
                "The model is unavailable. Run the local training command first.",
            )
        if not data_adapter.ready:
            raise ApiError(
                503,
                "data_adapter_unavailable",
                "Demo account data is unavailable. Run the local training command first.",
            )
        record = get_offline_record(request.account_id)

        assessment_id = f"asmt_{uuid4().hex[:8]}"
        feature_result = build_feature_row(record)
        completeness = round(feature_result.completeness, 3)
        if not is_sufficient(feature_result.completeness):
            try:
                feedback_store.record_assessment(
                    assessment_id=assessment_id,
                    model_id=model_service.model_id,
                    recommendation="insufficient_data",
                )
            except StoreUnavailableError as exc:
                raise ApiError(
                    500,
                    "feedback_store_unavailable",
                    "The assessment could not be recorded safely.",
                ) from exc
            response = AssessmentResponse(
                assessment_id=assessment_id,
                status="insufficient_data",
                account_id=request.account_id,
                data_completeness=completeness,
                warning=INSUFFICIENT_WARNING,
            )
            return JSONResponse(
                status_code=422,
                content=response.model_dump(mode="json"),
            )

        try:
            score = model_service.score(feature_result.frame, feature_result.completeness)
            if (
                score is None
                or not math.isfinite(float(score.probability))
                or score.band not in {"low", "medium", "high"}
            ):
                raise MalformedModelResponseError("Invalid score contract.")
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

        status = "completed"
        warning = TRIAGE_WARNING
        try:
            factors = model_service.explain(feature_result.frame)
        except ExplanationUnavailableError:
            status = "completed_with_warning"
            warning = EXPLANATION_WARNING
            factors = []

        if status == "completed_with_warning" or score.confidence.level == "low":
            recommendation = "monitor"
        else:
            recommendation = {
                "low": "no_concern",
                "medium": "monitor",
                "high": "prioritise",
            }[score.band]

        if feature_result.completeness < 0.75:
            uncertainty = (
                "Confidence is limited because several required public features "
                "are missing and model limitations still apply."
            )
        elif score.confidence.level == "low":
            uncertainty = (
                "The score is close to a decision threshold; small evidence changes "
                "could change the risk band."
            )
        else:
            uncertainty = (
                "The score is clear of current thresholds, but cross-dataset and "
                "time-based model limitations still apply."
            )

        try:
            feedback_store.record_assessment(
                assessment_id=assessment_id,
                model_id=model_service.model_id,
                recommendation=recommendation,
            )
        except StoreUnavailableError as exc:
            raise ApiError(
                500,
                "feedback_store_unavailable",
                "The assessment could not be recorded safely.",
            ) from exc

        return AssessmentResponse(
            assessment_id=assessment_id,
            status=status,
            account_id=request.account_id,
            data_completeness=completeness,
            risk_probability=round(score.probability, 6),
            risk_score=round(score.probability * 100),
            risk_band=score.band,
            risk_band_label=score.band.title(),
            model_version=model_service.model_id,
            threshold_version=getattr(
                model_service,
                "threshold_version",
                THRESHOLD_VERSION,
            ),
            assessment_time=datetime.now(timezone.utc),
            confidence=score.confidence,
            uncertainty=uncertainty,
            top_factors=factors,
            recommendation=recommendation,
            warning=warning,
        )

    @application.post(
        "/api/v1/batch-assessments",
        response_model=BatchUploadResponse,
    )
    async def create_batch_assessments(
        request: BatchUploadRequest,
    ) -> BatchUploadResponse:
        """Validate and assess a CSV queue with independent row outcomes."""

        if not request.filename.lower().endswith(".csv"):
            raise ApiError(
                400,
                "invalid_file_type",
                "Upload a .csv file using the documented template.",
            )
        try:
            rows = list(csv.DictReader(io.StringIO(request.content)))
            header = next(csv.reader(io.StringIO(request.content)), [])
        except csv.Error as exc:
            raise ApiError(400, "invalid_csv", "The CSV file could not be parsed.") from exc
        if header != ["account_id"]:
            raise ApiError(
                400,
                "invalid_csv_header",
                "The CSV header must be exactly: account_id",
            )
        if len(rows) > 100:
            raise ApiError(
                400,
                "batch_row_limit_exceeded",
                "A batch can contain at most 100 account rows.",
            )

        results: list[BatchRowResult] = []
        seen: set[str] = set()
        for row_number, row in enumerate(rows, start=2):
            raw_identifier = row.get("account_id", "")
            try:
                identifier = normalise_offline_identifier(raw_identifier)
            except ValueError:
                results.append(
                    BatchRowResult(
                        row_number=row_number,
                        account_id=str(raw_identifier).strip(),
                        processing_status="failed",
                        error="Invalid identifier format.",
                    )
                )
                continue
            if identifier in seen:
                results.append(
                    BatchRowResult(
                        row_number=row_number,
                        account_id=identifier,
                        processing_status="failed",
                        error="Duplicate account identifier.",
                    )
                )
                continue
            seen.add(identifier)
            try:
                assessment = await create_assessment(
                    AssessmentRequest(platform="x", account_id=identifier)
                )
            except ApiError as exc:
                results.append(
                    BatchRowResult(
                        row_number=row_number,
                        account_id=identifier,
                        processing_status="failed",
                        error=exc.message,
                    )
                )
                continue
            if isinstance(assessment, JSONResponse):
                assessment_data = json.loads(assessment.body)
            else:
                assessment_data = assessment.model_dump(mode="json")
            results.append(
                BatchRowResult(
                    row_number=row_number,
                    account_id=identifier,
                    processing_status="completed",
                    assessment_status=assessment_data["status"],
                    risk_score=assessment_data.get("risk_score"),
                    risk_band=assessment_data.get("risk_band"),
                    completeness_state=(
                        "insufficient"
                        if assessment_data["status"] == "insufficient_data"
                        else "eligible"
                    ),
                    review_status="unreviewed",
                )
            )

        completed_count = sum(
            result.processing_status == "completed" for result in results
        )
        return BatchUploadResponse(
            total_rows=len(results),
            completed_count=completed_count,
            failed_count=len(results) - completed_count,
            results=results,
        )

    @application.post(
        "/api/v1/assessments/{assessment_id}/decision",
        response_model=DecisionResponse,
        status_code=201,
    )
    async def create_decision(
        assessment_id: str,
        request: DecisionRequest,
    ) -> DecisionResponse:
        """Record one final confirm/override decision for an assessment."""

        if not assessment_id.startswith("asmt_") or len(assessment_id) != 13:
            raise ApiError(400, "invalid_request", "Invalid assessment ID.")
        try:
            feedback_store.record_decision(
                assessment_id=assessment_id,
                analyst_decision=request.decision,
                reason=request.reason,
            )
        except AssessmentNotFoundError as exc:
            raise ApiError(
                404,
                "assessment_not_found",
                "Complete an assessment before recording a decision.",
            ) from exc
        except DuplicateOverrideError as exc:
            raise ApiError(
                409,
                "decision_already_recorded",
                "A decision has already been recorded for this assessment.",
            ) from exc
        except StoreUnavailableError as exc:
            raise ApiError(
                500,
                "feedback_store_unavailable",
                "The decision could not be recorded safely.",
            ) from exc
        return DecisionResponse(
            assessment_id=assessment_id,
            analyst_decision=request.decision,
        )

    @application.get(
        "/api/v1/feedback",
        response_model=DecisionFeedbackList,
    )
    async def list_feedback(
        project_role: str | None = Header(default=None, alias="X-Project-Role"),
    ) -> DecisionFeedbackList:
        """Return minimal decision feedback to an authorised project role."""

        if (
            project_role is None
            or project_role.strip().lower() not in settings.authorised_role_set
        ):
            raise ApiError(
                403,
                "feedback_access_denied",
                "An authorised project role is required.",
            )
        try:
            records = feedback_store.list_decisions()
        except StoreUnavailableError as exc:
            raise ApiError(
                503,
                "feedback_store_unavailable",
                "Feedback is temporarily unavailable.",
                retryable=True,
            ) from exc
        return DecisionFeedbackList(count=len(records), records=records)

    @application.put(
        "/api/v1/assessments/{assessment_id}/follow-up",
        response_model=FollowUpResponse,
    )
    async def update_follow_up(
        assessment_id: str,
        request: FollowUpRequest,
        project_role: str | None = Header(default=None, alias="X-Project-Role"),
    ) -> FollowUpResponse:
        """Create, update, or clear an authorised human follow-up flag."""

        if (
            project_role is None
            or project_role.strip().lower() not in settings.authorised_role_set
        ):
            raise ApiError(
                403,
                "follow_up_access_denied",
                "An authorised analyst role is required.",
            )
        try:
            feedback_store.set_follow_up(
                assessment_id=assessment_id,
                status=request.status,
                reason=request.reason,
            )
        except AssessmentNotFoundError as exc:
            raise ApiError(
                404,
                "assessment_not_found",
                "Only a completed or Insufficient data assessment can be flagged.",
            ) from exc
        return FollowUpResponse(
            assessment_id=assessment_id,
            status=request.status,
        )

    @application.post(
        "/api/v1/assessments/{assessment_id}/override",
        response_model=OverrideResponse,
        status_code=201,
    )
    async def create_override(
        assessment_id: str,
        request: OverrideRequest,
    ) -> OverrideResponse:
        """Support the legacy override endpoint through the decision store."""

        if not assessment_id.startswith("asmt_") or len(assessment_id) != 13:
            raise ApiError(400, "invalid_request", "Invalid assessment ID.")
        try:
            feedback_store.record_override(
                assessment_id=assessment_id,
                override_label=request.override_label,
                reason_code=request.reason_code,
            )
        except AssessmentNotFoundError as exc:
            raise ApiError(
                404,
                "assessment_not_found",
                "The assessment does not exist.",
            ) from exc
        except DuplicateOverrideError as exc:
            raise ApiError(
                409,
                "override_already_recorded",
                "An override has already been recorded for this assessment.",
            ) from exc
        except StoreUnavailableError as exc:
            raise ApiError(
                500,
                "feedback_store_unavailable",
                "The override could not be recorded safely.",
            ) from exc
        return OverrideResponse(assessment_id=assessment_id)

    return application


app = create_app()
