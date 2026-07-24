from pathlib import Path

import pandas as pd
import pytest
from fastapi.testclient import TestClient

from backend.app.config import Settings
from backend.app.errors import ExplanationUnavailableError
from backend.app.main import create_app
from backend.app.model_service import ScoreResult
from backend.app.schemas import Confidence, TopFactor


class FakeModelService:
    ready = True
    error = None
    missing_artifacts: list[str] = []
    model_id = "fixture_model"

    def score(self, _features, _completeness) -> ScoreResult:
        return ScoreResult(
            probability=0.82,
            band="high",
            confidence=Confidence(
                level="high",
                basis="clear_of_decision_thresholds",
            ),
        )

    def explain(self, _features) -> list[TopFactor]:
        return [
            TopFactor(
                feature="posting_frequency",
                direction="increases_risk",
                evidence="Posting frequency increased the estimated risk.",
            )
        ]


class FailingExplanationModel(FakeModelService):
    def explain(self, _features) -> list[TopFactor]:
        raise ExplanationUnavailableError("fixture failure")


class UnavailableModel(FakeModelService):
    ready = False
    missing_artifacts = ["xgboost_model.json"]


def _demo_rows() -> list[dict]:
    return [
        {
            "source_dataset": "fixture",
            "account_id": "100",
            "username": "demo_user",
            "description": "A complete demo profile",
            "location": "Melbourne",
            "account_age_days": 365,
            "followers_count": 500,
            "following_count": 100,
            "tweet_count": 2000,
            "verified": False,
            "default_profile_image": False,
            "description_length": 23,
            "username_length": 9,
        },
        {
            "source_dataset": "fixture",
            "account_id": "200",
            "username": None,
            "description": None,
            "location": None,
            "account_age_days": None,
            "followers_count": None,
            "following_count": None,
            "tweet_count": None,
            "verified": None,
            "default_profile_image": None,
            "description_length": None,
            "username_length": None,
        },
    ]


def _client(tmp_path: Path, model=None) -> TestClient:
    demo_path = tmp_path / "demo.csv"
    pd.DataFrame(_demo_rows()).to_csv(demo_path, index=False)
    settings = Settings(
        artifact_dir=tmp_path / "artifacts",
        demo_data_path=demo_path,
        database_path=tmp_path / "feedback.sqlite3",
    )
    app = create_app(settings=settings, model_service=model or FakeModelService())
    return TestClient(app, raise_server_exceptions=False)


def test_health_demo_assessment_and_override_flow(tmp_path) -> None:
    client = _client(tmp_path)

    health = client.get("/api/v1/health")
    assert health.status_code == 200
    assert health.json()["status"] == "ok"

    demo = client.get("/api/v1/demo/accounts", params={"limit": 1})
    assert demo.status_code == 200
    assert demo.json()["count"] == 1
    assert "label" not in demo.json()["accounts"][0]

    assessment = client.post(
        "/api/v1/assessments",
        json={"platform": "x", "account_id": "100"},
    )
    assert assessment.status_code == 200
    body = assessment.json()
    assert body["status"] == "completed"
    assert body["data_source"] == "dataset"
    assert body["risk_band"] == "high"
    assert body["recommendation"] == "prioritise"

    override_url = f"/api/v1/assessments/{body['assessment_id']}/override"
    override = client.post(
        override_url,
        json={"override_label": "legitimate", "reason_code": "known_official_account"},
    )
    assert override.status_code == 201
    assert client.post(
        override_url,
        json={"override_label": "uncertain", "reason_code": "manual_review"},
    ).status_code == 409


def test_unknown_invalid_and_insufficient_requests(tmp_path) -> None:
    client = _client(tmp_path)

    invalid = client.post(
        "/api/v1/assessments",
        json={"platform": "twitter", "account_id": "100"},
    )
    assert invalid.status_code == 400
    assert invalid.json()["error"]["code"] == "invalid_request"

    unknown = client.post(
        "/api/v1/assessments",
        json={"platform": "x", "account_id": "999"},
    )
    assert unknown.status_code == 404
    assert unknown.json()["error"]["code"] == "account_not_found"

    insufficient = client.post(
        "/api/v1/assessments",
        json={"platform": "x", "account_id": "200"},
    )
    assert insufficient.status_code == 422
    assert insufficient.json()["status"] == "insufficient_data"
    assert insufficient.json()["risk_probability"] is None


def test_shap_failure_returns_scored_degraded_result(tmp_path) -> None:
    client = _client(tmp_path, FailingExplanationModel())
    response = client.post(
        "/api/v1/assessments",
        json={"platform": "x", "account_id": "100"},
    )
    assert response.status_code == 200
    assert response.json()["status"] == "completed_with_warning"
    assert response.json()["top_factors"] == []
    assert response.json()["recommendation"] == "monitor"


def test_missing_model_returns_503(tmp_path) -> None:
    client = _client(tmp_path, UnavailableModel())
    assert client.get("/api/v1/health").status_code == 503
    response = client.post(
        "/api/v1/assessments",
        json={"platform": "x", "account_id": "100"},
    )
    assert response.status_code == 503
    assert response.json()["error"]["code"] == "model_unavailable"
