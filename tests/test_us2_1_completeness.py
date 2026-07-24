from pathlib import Path

from fastapi.testclient import TestClient

from backend.app.config import PROJECT_ROOT, Settings
from backend.app.main import create_app


class ModelNotNeededForCompleteness:
    ready = False
    missing_artifacts: list[str] = []


def _client(tmp_path: Path) -> TestClient:
    settings = Settings(
        demo_data_path=PROJECT_ROOT / "data" / "fixtures" / "demo_accounts.csv",
        artifact_dir=tmp_path / "artifacts",
        database_path=tmp_path / "feedback.sqlite3",
    )
    return TestClient(
        create_app(settings=settings, model_service=ModelNotNeededForCompleteness()),
        raise_server_exceptions=False,
    )


def test_ac1_completeness_is_calculated_and_displayed_before_scoring(tmp_path) -> None:
    """US2.1 AC1: response and UI expose completeness before any risk band."""
    client = _client(tmp_path)
    response = client.get("/api/v1/accounts/demo_low_01/completeness")

    assert response.status_code == 200
    assert response.json()["completeness"] == 1.0
    assert response.json()["completeness_percentage"] == 100
    assert response.json()["risk_band"] is None
    page = client.get("/").text
    assert 'role="progressbar"' in page
    assert "Feature completeness" in page


def test_ac2_below_half_is_insufficient_without_risk_band(tmp_path) -> None:
    """US2.1 AC2: less than 50% is Insufficient data and never has a band."""
    body = _client(tmp_path).get(
        "/api/v1/accounts/demo_incomplete_01/completeness"
    ).json()

    assert body["completeness"] < 0.5
    assert body["status"] == "Insufficient data"
    assert body["eligible_for_scoring"] is False
    assert body["risk_band"] is None


def test_ac3_exactly_half_is_eligible_and_keeps_caveat(tmp_path) -> None:
    """US2.1 AC3: the inclusive 50% boundary is eligible with caveat visible."""
    body = _client(tmp_path).get(
        "/api/v1/accounts/demo_exact_50/completeness"
    ).json()

    assert body["completeness"] == 0.5
    assert body["completeness_percentage"] == 50
    assert body["status"] == "Eligible for scoring"
    assert body["eligible_for_scoring"] is True
    assert body["missing_data_caveat"]
    assert body["missing_features"]


def test_ac4_missing_required_features_use_plain_language(tmp_path) -> None:
    """US2.1 AC4: technical feature keys are translated for analysts."""
    body = _client(tmp_path).get(
        "/api/v1/accounts/demo_exact_50/completeness"
    ).json()

    assert "Follower count" in body["missing_features"]
    assert "Following count" in body["missing_features"]
    assert "follower_following_ratio" not in body["missing_features"]
    assert all("_" not in label for label in body["missing_features"])
