import re
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class AssessmentRequest(StrictModel):
    platform: Literal["x"]
    account_id: str = Field(pattern=r"^[0-9]{1,19}$")


OFFLINE_IDENTIFIER_PATTERN = re.compile(r"^[A-Za-z0-9_]{1,32}$")


def normalise_offline_identifier(value: str) -> str:
    if not isinstance(value, str):
        raise ValueError("Enter an offline account identifier.")
    normalised = value.strip().removeprefix("@").lower()
    if not normalised:
        raise ValueError("Enter an offline account identifier.")
    if not OFFLINE_IDENTIFIER_PATTERN.fullmatch(normalised):
        raise ValueError("Use only letters, numbers, or underscores.")
    return normalised


class IntakeRequest(StrictModel):
    identifier: str

    @field_validator("identifier", mode="before")
    @classmethod
    def validate_identifier(cls, value: str) -> str:
        return normalise_offline_identifier(value)


class IntakeResponse(BaseModel):
    status: Literal["ready"] = "ready"
    account_id: str
    normalised_identifier: str
    display_identifier: str
    data_source: Literal["offline_fixture"] = "offline_fixture"
    assessment_count: Literal[1] = 1


class Confidence(BaseModel):
    level: Literal["low", "high"]
    basis: Literal[
        "limited_feature_coverage",
        "close_to_decision_thresholds",
        "clear_of_decision_thresholds",
    ]


class TopFactor(BaseModel):
    feature: str
    direction: Literal["increases_risk", "decreases_risk"]
    evidence: str


class AssessmentResponse(BaseModel):
    assessment_id: str
    status: Literal["completed", "completed_with_warning", "insufficient_data"]
    platform: Literal["x"] = "x"
    account_id: str
    data_source: Literal["dataset"] = "dataset"
    data_completeness: float = Field(ge=0.0, le=1.0)
    risk_probability: float | None = Field(default=None, ge=0.0, le=1.0)
    risk_band: Literal["low", "medium", "high"] | None = None
    confidence: Confidence | None = None
    top_factors: list[TopFactor] = Field(default_factory=list)
    recommendation: Literal["no_concern", "monitor", "prioritise"] | None = None
    warning: str


class OverrideRequest(StrictModel):
    override_label: Literal["legitimate", "suspicious", "uncertain"]
    reason_code: str = Field(min_length=1, max_length=64, pattern=r"^[a-z0-9_]+$")


class OverrideResponse(BaseModel):
    status: Literal["recorded"] = "recorded"
    assessment_id: str


class DemoAccount(BaseModel):
    account_id: str
    source_dataset: str | None = None
    username: str | None = None
    scenario: Literal["low", "medium", "high"] | None = None
    display_label: str | None = None


class DemoAccountsResponse(BaseModel):
    count: int
    accounts: list[DemoAccount]


class HealthResponse(BaseModel):
    status: Literal["ok", "degraded"]
    api: Literal["available"] = "available"
    model: Literal["loaded", "unavailable"]
    data_adapter: Literal["loaded", "unavailable"]
    demo_account_count: int
    feedback_store: Literal["ready", "unavailable"]
    missing_artifacts: list[str] = Field(default_factory=list)


class ErrorDetail(BaseModel):
    code: str
    message: str
    retryable: bool = False


class ErrorResponse(BaseModel):
    error: ErrorDetail
