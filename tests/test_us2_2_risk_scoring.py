from datetime import datetime
from pathlib import Path

from fastapi.testclient import TestClient

from backend.app.config import PROJECT_ROOT, Settings
from backend.app.main import create_app
from backend.app.model_service import ScoreResult


def _real_client(tmp_path: Path) -> TestClient:
    settings = Settings(
        demo_data_path=PROJECT_ROOT / "data" / "fixtures" / "demo_accounts.csv",
        artifact_dir=PROJECT_ROOT / "models" / "xgb-offline-v1",
        database_path=tmp_path / "feedback.sqlite3",
    )
    return TestClient(create_app(settings=settings), raise_server_exceptions=False)


def test_ac1_ac2_ac3_real_model_returns_versioned_score_band_and_time(tmp_path) -> None:
    """US2.2 AC1-AC3: an eligible input gets one bounded, versioned result."""
    body = _real_client(tmp_path).post(
        "/api/v1/assessments",
        json={"platform": "x", "account_id": "demo_medium_01"},
    ).json()

    assert 0 <= body["risk_score"] <= 100
    assert body["risk_band_label"] in {"Low", "Medium", "High"}
    assert body["model_version"] == "xgb-offline-v1"
    assert body["threshold_version"] == "threshold-v1"
    datetime.fromisoformat(body["assessment_time"].replace("Z", "+00:00"))


def test_ac2_ac4_representative_fixtures_are_deterministic_across_bands(tmp_path) -> None:
    """US2.2 AC2/AC4: same model/input is stable and all bands are represented."""
    client = _real_client(tmp_path)
    expected = {
        "demo_low_01": "Low",
        "demo_medium_01": "Medium",
        "demo_high_01": "High",
    }

    for account_id, band in expected.items():
        first = client.post(
            "/api/v1/assessments",
            json={"platform": "x", "account_id": account_id},
        ).json()
        second = client.post(
            "/api/v1/assessments",
            json={"platform": "x", "account_id": account_id},
        ).json()
        assert first["risk_score"] == second["risk_score"]
        assert first["risk_band_label"] == second["risk_band_label"] == band


def test_tutor_feedback_dataset_selector_examples_match_documented_bands(tmp_path) -> None:
    """Tutor feedback: the three real dataset rows give stable browser examples."""
    client = _real_client(tmp_path)
    expected = {
        "20611469": (2, "Low"),
        "396039913": (30, "Medium"),
        "2250581388": (91, "High"),
    }

    for account_id, (score, band) in expected.items():
        response = client.post(
            "/api/v1/assessments",
            json={"platform": "x", "account_id": account_id},
        )
        assert response.status_code == 200
        body = response.json()
        assert body["risk_score"] == score
        assert body["risk_band_label"] == band


def test_ac5_ac6_ui_uses_text_plus_contrast_classes_and_no_definitive_label(
    tmp_path,
) -> None:
    """US2.2 AC5/AC6: visual bands retain text and careful non-verdict wording."""
    page = _real_client(tmp_path).get("/").text
    css = _real_client(tmp_path).get("/static/styles.css").text

    assert 'id="risk-band"' in page
    assert "Triage evidence, not a verdict." in page
    assert ".risk-band.low" in css
    assert ".risk-band.medium" in css
    assert ".risk-band.high" in css
    assert "is a bot" not in page.lower()
    assert "is human" not in page.lower()


class FailingModel:
    ready = True
    missing_artifacts: list[str] = []
    model_id = "failing-model"

    def score(self, _features, _completeness) -> ScoreResult:
        raise RuntimeError("simulated model timeout")


def test_ac7_scoring_failure_is_recoverable_without_partial_score(tmp_path) -> None:
    """US2.2 AC7: failure returns a retryable error and no stale result fields."""
    settings = Settings(
        demo_data_path=PROJECT_ROOT / "data" / "fixtures" / "demo_accounts.csv",
        artifact_dir=tmp_path / "artifacts",
        database_path=tmp_path / "feedback.sqlite3",
    )
    client = TestClient(
        create_app(settings=settings, model_service=FailingModel()),
        raise_server_exceptions=False,
    )

    response = client.post(
        "/api/v1/assessments",
        json={"platform": "x", "account_id": "demo_low_01"},
    )

    assert response.status_code == 503
    assert response.json()["error"] == {
        "code": "scoring_unavailable",
        "message": "Risk scoring is temporarily unavailable. Retry this assessment.",
        "retryable": True,
    }
    assert "risk_score" not in response.json()
