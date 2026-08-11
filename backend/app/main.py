import logging
from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from backend.app.config import PROJECT_ROOT, Settings
from backend.app.context import ApplicationContext
from backend.app.data_adapter import DatasetAdapter
from backend.app.database import FeedbackStore
from backend.app.errors import ApiError
from backend.app.model_service import ModelService
from backend.app.routes import (
    build_assessment_router,
    build_public_router,
    build_review_router,
)
from backend.app.schemas import ErrorDetail, ErrorResponse
from backend.app.version import APP_VERSION


LOGGER = logging.getLogger("bot_risk_backend")
FRONTEND_DIR = PROJECT_ROOT / "frontend"


def _error_content(
    code: str,
    message: str,
    retryable: bool = False,
) -> dict[str, object]:
    """Build the stable public error envelope used by all controlled failures."""

    return ErrorResponse(
        error=ErrorDetail(code=code, message=message, retryable=retryable)
    ).model_dump(mode="json")


def _register_exception_handlers(application: FastAPI) -> None:
    """Attach safe API, validation, and unexpected-error translations."""

    @application.exception_handler(ApiError)
    async def api_error_handler(_: Request, exc: ApiError) -> JSONResponse:
        """Translate controlled domain errors into the public error contract."""

        return JSONResponse(
            status_code=exc.status_code,
            content=_error_content(exc.code, exc.message, exc.retryable),
        )

    @application.exception_handler(RequestValidationError)
    async def validation_error_handler(
        _: Request,
        exc: RequestValidationError,
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


def _register_page_routes(application: FastAPI) -> None:
    """Attach the two static browser entry pages outside the API schema."""

    @application.get("/", include_in_schema=False)
    async def application_shell() -> FileResponse:
        """Serve the main browser assessment workspace."""

        return FileResponse(FRONTEND_DIR / "index.html")

    @application.get("/model-information", include_in_schema=False)
    async def model_information_page() -> FileResponse:
        """Serve the plain-language model evidence and limitations page."""

        return FileResponse(FRONTEND_DIR / "model-information.html")


def create_app(
    settings: Settings | None = None,
    model_service: ModelService | None = None,
    data_adapter: DatasetAdapter | None = None,
    feedback_store: FeedbackStore | None = None,
) -> FastAPI:
    """Assemble the FastAPI shell and injectable runtime service context."""

    settings = settings or Settings()
    logging.basicConfig(level=getattr(logging, settings.log_level.upper(), logging.INFO))
    context = ApplicationContext(
        settings=settings,
        model_service=model_service or ModelService(settings.artifact_dir),
        data_adapter=data_adapter or DatasetAdapter(settings.demo_data_path),
        feedback_store=feedback_store or FeedbackStore(settings.database_path),
    )
    application = FastAPI(
        title="FIT5238 Bot Risk Scoring Tool",
        version=APP_VERSION,
        description=(
            "Iteration 2 dataset-backed MVP. Results support analyst triage and are "
            "not final bot determinations."
        ),
    )
    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=False,
        allow_methods=["GET", "POST", "PUT"],
        allow_headers=["Content-Type", "X-Project-Role"],
    )
    application.state.settings = context.settings
    application.state.model_service = context.model_service
    application.state.data_adapter = context.data_adapter
    application.state.feedback_store = context.feedback_store
    application.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")
    _register_exception_handlers(application)
    _register_page_routes(application)
    application.include_router(build_public_router(context))
    application.include_router(build_assessment_router(context))
    application.include_router(build_review_router(context))
    return application


app = create_app()
