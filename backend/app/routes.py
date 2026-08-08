import csv
import io

from fastapi import APIRouter, Header
from fastapi.responses import JSONResponse

from backend.app.assessment_service import assess_account, build_completeness_response
from backend.app.context import ApplicationContext
from backend.app.data_adapter import DatasetAdapter
from backend.app.database import (
    AssessmentNotFoundError,
    DuplicateOverrideError,
    StoreUnavailableError,
)
from backend.app.errors import ApiError
from backend.app.preview import build_public_preview
from backend.app.schemas import (
    AccountPreview,
    AssessmentRequest,
    AssessmentResponse,
    BatchRowResult,
    BatchUploadRequest,
    BatchUploadResponse,
    CompletenessResponse,
    DecisionFeedbackList,
    DecisionRequest,
    DecisionResponse,
    DemoAccountsResponse,
    FollowUpRequest,
    FollowUpResponse,
    HealthResponse,
    IntakeRequest,
    IntakeResponse,
    OverrideRequest,
    OverrideResponse,
    is_valid_assessment_id,
    normalise_offline_identifier,
)


def build_public_router(context: ApplicationContext) -> APIRouter:
    """Create readiness, selector, intake, preview, and completeness routes."""

    router = APIRouter(prefix="/api/v1")

    @router.get("/health", response_model=HealthResponse)
    def health() -> JSONResponse:
        """Report readiness of the model, demo adapter, and feedback store."""

        all_ready = (
            context.model_service.ready
            and context.data_adapter.ready
            and context.feedback_store.ready
        )
        response = HealthResponse(
            status="ok" if all_ready else "degraded",
            model="loaded" if context.model_service.ready else "unavailable",
            data_adapter="loaded" if context.data_adapter.ready else "unavailable",
            demo_account_count=context.data_adapter.account_count,
            feedback_store="ready" if context.feedback_store.ready else "unavailable",
            missing_artifacts=context.model_service.missing_artifacts,
        )
        return JSONResponse(
            status_code=200 if all_ready else 503,
            content=response.model_dump(mode="json"),
        )

    @router.get("/demo/accounts", response_model=DemoAccountsResponse)
    def demo_accounts(limit: int = 20) -> DemoAccountsResponse:
        """Return label-free account choices for the offline demonstration."""

        if limit < 1 or limit > 100:
            raise ApiError(400, "invalid_request", "Limit must be between 1 and 100.")
        if not context.data_adapter.ready:
            raise ApiError(
                503,
                "data_adapter_unavailable",
                "Demo account data is unavailable. Run the local training command first.",
            )
        accounts = context.data_adapter.list_accounts(limit)
        return DemoAccountsResponse(count=len(accounts), accounts=accounts)

    @router.post("/intake", response_model=IntakeResponse)
    def prepare_account_intake(request: IntakeRequest) -> IntakeResponse:
        """Validate one identifier and return its canonical display context."""

        if not context.data_adapter.ready:
            raise ApiError(
                503,
                "data_adapter_unavailable",
                "Offline demonstration accounts are temporarily unavailable.",
                retryable=True,
            )
        record = context.get_offline_record(request.identifier)
        username = DatasetAdapter._optional_text(record.get("username"))
        display_identifier = f"@{username}" if username else str(record["account_id"])
        return IntakeResponse(
            account_id=str(record["account_id"]),
            normalised_identifier=request.identifier,
            display_identifier=display_identifier,
        )

    @router.get("/accounts/{account_id}/preview", response_model=AccountPreview)
    def preview_account(account_id: str) -> AccountPreview:
        """Return only the approved public fields for analyst confirmation."""

        if not context.data_adapter.ready:
            raise ApiError(
                503,
                "data_adapter_unavailable",
                "Offline demonstration accounts are temporarily unavailable.",
                retryable=True,
            )
        return build_public_preview(context.get_offline_record(account_id))

    @router.get(
        "/accounts/{account_id}/completeness",
        response_model=CompletenessResponse,
    )
    def account_completeness(account_id: str) -> CompletenessResponse:
        """Calculate evidence coverage before any model score is requested."""

        return build_completeness_response(context, account_id)

    return router


def _parse_batch_rows(request: BatchUploadRequest) -> list[dict[str, str | None]]:
    """Validate the CSV envelope and return its ordered data rows."""

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
    return rows


def _failed_batch_row(row_number: int, account_id: str, message: str) -> BatchRowResult:
    """Build one controlled per-row failure without interrupting its batch."""

    return BatchRowResult(
        row_number=row_number,
        account_id=account_id,
        processing_status="failed",
        error=message,
    )


def _assessment_model(
    assessment: AssessmentResponse | JSONResponse,
) -> AssessmentResponse:
    """Normalise scored and insufficient route results to one typed model."""

    if isinstance(assessment, JSONResponse):
        return AssessmentResponse.model_validate_json(assessment.body)
    return assessment


def build_assessment_router(context: ApplicationContext) -> APIRouter:
    """Create single-account and CSV-batch assessment routes."""

    router = APIRouter(prefix="/api/v1")

    @router.post("/assessments", response_model=AssessmentResponse)
    def create_assessment(
        request: AssessmentRequest,
    ) -> AssessmentResponse | JSONResponse:
        """Run the single-account assessment domain workflow."""

        return assess_account(context, request)

    @router.post("/batch-assessments", response_model=BatchUploadResponse)
    def create_batch_assessments(request: BatchUploadRequest) -> BatchUploadResponse:
        """Validate and assess a CSV queue with independent row outcomes."""

        rows = _parse_batch_rows(request)
        results: list[BatchRowResult] = []
        seen: set[str] = set()
        for row_number, row in enumerate(rows, start=2):
            raw_identifier = row.get("account_id", "") or ""
            try:
                identifier = normalise_offline_identifier(raw_identifier)
            except ValueError:
                results.append(
                    _failed_batch_row(
                        row_number,
                        str(raw_identifier).strip(),
                        "Invalid identifier format.",
                    )
                )
                continue
            try:
                canonical_identifier = str(
                    context.get_offline_record(identifier)["account_id"]
                )
            except ApiError as exc:
                results.append(_failed_batch_row(row_number, identifier, exc.message))
                continue
            if canonical_identifier in seen:
                results.append(
                    _failed_batch_row(
                        row_number,
                        canonical_identifier,
                        "Duplicate account identifier.",
                    )
                )
                continue
            seen.add(canonical_identifier)
            try:
                assessment = assess_account(
                    context,
                    AssessmentRequest(platform="x", account_id=canonical_identifier),
                )
            except ApiError as exc:
                results.append(
                    _failed_batch_row(row_number, canonical_identifier, exc.message)
                )
                continue
            assessment_result = _assessment_model(assessment)
            status = assessment_result.status
            results.append(
                BatchRowResult(
                    row_number=row_number,
                    account_id=canonical_identifier,
                    processing_status="completed",
                    assessment_status=status,
                    risk_score=assessment_result.risk_score,
                    risk_band=assessment_result.risk_band,
                    completeness_state=(
                        "insufficient" if status == "insufficient_data" else "eligible"
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

    return router


def _require_authorised_role(
    context: ApplicationContext,
    project_role: str | None,
    code: str,
    message: str,
) -> None:
    """Enforce the small project-role boundary shared by feedback routes."""

    if (
        project_role is None
        or project_role.strip().lower() not in context.settings.authorised_role_set
    ):
        raise ApiError(403, code, message)


def build_review_router(context: ApplicationContext) -> APIRouter:
    """Create decision, feedback, follow-up, and legacy override routes."""

    router = APIRouter(prefix="/api/v1")

    @router.post(
        "/assessments/{assessment_id}/decision",
        response_model=DecisionResponse,
        status_code=201,
    )
    def create_decision(
        assessment_id: str,
        request: DecisionRequest,
    ) -> DecisionResponse:
        """Record one final confirm/override decision for an assessment."""

        if not is_valid_assessment_id(assessment_id):
            raise ApiError(400, "invalid_request", "Invalid assessment ID.")
        try:
            context.feedback_store.record_decision(
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

    @router.get("/feedback", response_model=DecisionFeedbackList)
    def list_feedback(
        project_role: str | None = Header(default=None, alias="X-Project-Role"),
    ) -> DecisionFeedbackList:
        """Return minimal decision feedback to an authorised project role."""

        _require_authorised_role(
            context,
            project_role,
            "feedback_access_denied",
            "An authorised project role is required.",
        )
        try:
            records = context.feedback_store.list_decisions()
        except StoreUnavailableError as exc:
            raise ApiError(
                503,
                "feedback_store_unavailable",
                "Feedback is temporarily unavailable.",
                retryable=True,
            ) from exc
        return DecisionFeedbackList(count=len(records), records=records)

    @router.put(
        "/assessments/{assessment_id}/follow-up",
        response_model=FollowUpResponse,
    )
    def update_follow_up(
        assessment_id: str,
        request: FollowUpRequest,
        project_role: str | None = Header(default=None, alias="X-Project-Role"),
    ) -> FollowUpResponse:
        """Create, update, or clear an authorised human follow-up flag."""

        if not is_valid_assessment_id(assessment_id):
            raise ApiError(400, "invalid_request", "Invalid assessment ID.")
        _require_authorised_role(
            context,
            project_role,
            "follow_up_access_denied",
            "An authorised analyst role is required.",
        )
        try:
            context.feedback_store.set_follow_up(
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
        except StoreUnavailableError as exc:
            raise ApiError(
                500,
                "feedback_store_unavailable",
                "The follow-up status could not be recorded safely.",
            ) from exc
        return FollowUpResponse(assessment_id=assessment_id, status=request.status)

    @router.post(
        "/assessments/{assessment_id}/override",
        response_model=OverrideResponse,
        status_code=201,
    )
    def create_override(
        assessment_id: str,
        request: OverrideRequest,
    ) -> OverrideResponse:
        """Support the legacy override endpoint through the decision store."""

        if not is_valid_assessment_id(assessment_id):
            raise ApiError(400, "invalid_request", "Invalid assessment ID.")
        try:
            context.feedback_store.record_override(
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

    return router
