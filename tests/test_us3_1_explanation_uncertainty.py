from pathlib import Path

from fastapi.testclient import TestClient

from backend.app.config import PROJECT_ROOT, Settings
from backend.app.main import create_app


def _client(tmp_path: Path) -> TestClient:
    settings = Settings(
        demo_data_path=PROJECT_ROOT / "data" / "fixtures" / "demo_accounts.csv",
        artifact_dir=PROJECT_ROOT / "models" / "xgb-offline-v1",
        database_path=tmp_path / "feedback.sqlite3",
    )
    return TestClient(create_app(settings=settings), raise_server_exceptions=False)


def test_ac1_ac2_ac3_top_three_are_ordered_plain_and_observed(tmp_path) -> None:
    """US3.1 AC1-AC3: strongest factors are ordered, directional and readable."""
    body = _client(tmp_path).post(
        "/api/v1/assessments",
        json={"platform": "x", "account_id": "demo_high_01"},
    ).json()
    factors = body["top_factors"]

    assert 1 <= len(factors) <= 3
    magnitudes = [factor["contribution_magnitude"] for factor in factors]
    assert magnitudes == sorted(magnitudes, reverse=True)
    assert all(factor["direction"] in {"increases_risk", "decreases_risk"} for factor in factors)
    assert all(factor["label"] and "_" not in factor["label"] for factor in factors)
    assert all(factor["observed_value"] is not None for factor in factors)


def test_ac4_ac5_ac6_factors_uncertainty_and_score_share_result_context(tmp_path) -> None:
    """US3.1 AC4-AC6: one response binds model, factors, caveat and disclaimer."""
    body = _client(tmp_path).post(
        "/api/v1/assessments",
        json={"platform": "x", "account_id": "demo_exact_50"},
    ).json()

    assert body["model_version"] == "xgb-offline-v1"
    assert body["risk_score"] is not None
    assert body["top_factors"]
    assert "missing" in body["uncertainty"].lower()
    assert body["disclaimer"] == "Triage evidence, not a verdict."


def test_ac7_ui_avoids_certainty_guilt_and_enforcement_claims(tmp_path) -> None:
    """US3.1 AC7: analyst-facing copy avoids prohibited certainty language."""
    page = _client(tmp_path).get("/").text.lower()

    for prohibited in ["definitely a bot", "guilty", "malicious account", "automatically suspend"]:
        assert prohibited not in page
    assert "uncertainty" in page
    assert "triage evidence, not a verdict." in page
