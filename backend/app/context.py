from dataclasses import dataclass
from typing import Any

from backend.app.config import Settings
from backend.app.data_adapter import DatasetAdapter
from backend.app.database import FeedbackStore
from backend.app.errors import ApiError
from backend.app.model_service import ModelService


@dataclass(frozen=True)
class ApplicationContext:
    """Runtime services shared by route groups without global mutable state."""

    settings: Settings
    model_service: ModelService
    data_adapter: DatasetAdapter
    feedback_store: FeedbackStore

    def get_offline_record(self, identifier: str) -> dict[str, Any]:
        """Resolve one fixture account and translate expected source failures."""

        try:
            record = self.data_adapter.get_account(identifier)
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
