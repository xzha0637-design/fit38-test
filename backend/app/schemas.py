import re
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class AssessmentRequest(StrictModel):
    platform: Literal["x"]
    account_id: str

    @field_validator("account_id", mode="before")
    @classmethod
    def validate_account_id(cls, value: str) -> str:
        return normalise_offline_identifier(value)


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


class PublicProfile(BaseModel):
    username: str | None = None
    description: str | None = None
    location: str | None = None


class PublicActivity(BaseModel):
    account_age_days: int | None = Field(default=None, ge=0)
    post_count: int | None = Field(default=None, ge=0)
    posts_per_day: float | None = Field(default=None, ge=0)


class PublicNetwork(BaseModel):
    followers_count: int | None = Field(default=None, ge=0)
    following_count: int | None = Field(default=None, ge=0)


class AccountPreview(BaseModel):
    account_id: str
    display_identifier: str
    data_source: Literal["offline_fixture"] = "offline_fixture"
    content_type: Literal["source_data"] = "source_data"
    model_output_included: Literal[False] = False
    profile: PublicProfile
    activity: PublicActivity
    network: PublicNetwork
    missing_fields: list[str] = Field(default_factory=list)


class CompletenessResponse(BaseModel):
    account_id: str
    completeness: float = Field(ge=0, le=1)
    completeness_percentage: int = Field(ge=0, le=100)
    status: Literal["Eligible for scoring", "Insufficient data"]
    eligible_for_scoring: bool
    missing_features: list[str] = Field(default_factory=list)
    missing_data_caveat: str | None = None
    risk_band: None = None


class Confidence(BaseModel):
    level: Literal["low", "high"]
    basis: Literal[
        "limited_feature_coverage",
        "close_to_decision_thresholds",
        "clear_of_decision_thresholds",
    ]


class TopFactor(BaseModel):
    feature: str
    label: str | None = None
    direction: Literal["increases_risk", "decreases_risk"]
    observed_value: str | None = None
    contribution_magnitude: float = Field(default=0, ge=0)
    evidence: str


class AssessmentResponse(BaseModel):
    assessment_id: str
    status: Literal["completed", "completed_with_warning", "insufficient_data"]
    platform: Literal["x"] = "x"
    account_id: str
    data_source: Literal["dataset"] = "dataset"
    data_completeness: float = Field(ge=0.0, le=1.0)
    risk_probability: float | None = Field(default=None, ge=0.0, le=1.0)
    risk_score: int | None = Field(default=None, ge=0, le=100)
    risk_band: Literal["low", "medium", "high"] | None = None
    risk_band_label: Literal["Low", "Medium", "High"] | None = None
    model_version: str | None = None
    threshold_version: str | None = None
    assessment_time: datetime | None = None
    confidence: Confidence | None = None
    uncertainty: str | None = None
    top_factors: list[TopFactor] = Field(default_factory=list)
    recommendation: Literal["no_concern", "monitor", "prioritise"] | None = None
    warning: str
    disclaimer: Literal["Triage evidence, not a verdict."] = (
        "Triage evidence, not a verdict."
    )


class OverrideRequest(StrictModel):
    override_label: Literal["legitimate", "suspicious", "uncertain"]
    reason_code: str = Field(min_length=1, max_length=64, pattern=r"^[a-z0-9_]+$")


class OverrideResponse(BaseModel):
    status: Literal["recorded"] = "recorded"
    assessment_id: str


class DecisionRequest(StrictModel):
    decision: Literal["confirm", "override"]
    reason: str = Field(default="", max_length=240)

    @model_validator(mode="after")
    def require_override_reason(self):
        self.reason = self.reason.strip()
        if self.decision == "override" and not self.reason:
            raise ValueError("An override reason is required.")
        return self


class DecisionResponse(BaseModel):
    status: Literal["recorded"] = "recorded"
    assessment_id: str
    analyst_decision: Literal["confirm", "override"]
    acknowledgement: Literal[
        "Decision recorded. No platform action was taken."
    ] = "Decision recorded. No platform action was taken."


class DecisionFeedback(BaseModel):
    assessment_reference: str
    model_version: str
    recommendation: str
    analyst_decision: str
    reason: str
    timestamp: datetime


class DecisionFeedbackList(BaseModel):
    count: int
    records: list[DecisionFeedback]


class FollowUpRequest(StrictModel):
    status: Literal["flagged", "cleared"]
    reason: str = Field(default="", max_length=240)

    @model_validator(mode="after")
    def require_flag_reason(self):
        self.reason = self.reason.strip()
        if self.status == "flagged" and not self.reason:
            raise ValueError("A follow-up reason is required.")
        return self


class FollowUpResponse(BaseModel):
    assessment_id: str
    status: Literal["flagged", "cleared"]
    acknowledgement: Literal[
        "Follow-up updated. No platform action was taken."
    ] = "Follow-up updated. No platform action was taken."


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
