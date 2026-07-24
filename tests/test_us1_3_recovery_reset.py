from pathlib import Path

from fastapi.testclient import TestClient

from backend.app.config import PROJECT_ROOT, Settings
from backend.app.data_adapter import DatasetAdapter
from backend.app.main import create_app


class TimeoutAdapter:
    ready = True
    account_count = 1
    error = None

    def get_account(self, _identifier):
        raise TimeoutError("fixture timeout")

    def list_accounts(self, _limit):
        return []


class ModelFailure:
    ready = True
    missing_artifacts = []
    model_id = "fixture"

    def __init__(self, error):
        self.error_to_raise = error

    def score(self, *_args):
        if self.error_to_raise:
            raise self.error_to_raise
        return None


def _settings(tmp_path: Path) -> Settings:
    return Settings(
        demo_data_path=PROJECT_ROOT / "data" / "fixtures" / "demo_accounts.csv",
        artifact_dir=tmp_path / "artifacts",
        database_path=tmp_path / "feedback.sqlite3",
    )


def test_ac1_ac2_controlled_source_timeout_and_unknown_states(tmp_path) -> None:
    timeout_client = TestClient(
        create_app(
            settings=_settings(tmp_path),
            data_adapter=TimeoutAdapter(),
            model_service=ModelFailure(RuntimeError()),
        ),
        raise_server_exceptions=False,
    )
    timeout = timeout_client.post("/api/v1/intake", json={"identifier": "demo_low_01"})
    assert timeout.status_code == 503
    assert timeout.json()["error"]["code"] == "data_source_timeout"
    assert timeout.json()["error"]["retryable"] is True

    normal = TestClient(create_app(settings=_settings(tmp_path)), raise_server_exceptions=False)
    unknown = normal.post("/api/v1/intake", json={"identifier": "unknown_fixture"})
    assert unknown.status_code == 404
    assert unknown.json()["error"]["retryable"] is False


def test_ac1_model_timeout_and_malformed_response_are_controlled(tmp_path) -> None:
    adapter = DatasetAdapter(PROJECT_ROOT / "data" / "fixtures" / "demo_accounts.csv")
    for model, code, status in [
        (ModelFailure(TimeoutError()), "model_timeout", 503),
        (ModelFailure(None), "malformed_model_response", 502),
    ]:
        client = TestClient(
            create_app(
                settings=_settings(tmp_path),
                data_adapter=adapter,
                model_service=model,
            ),
            raise_server_exceptions=False,
        )
        response = client.post(
            "/api/v1/assessments",
            json={"platform": "x", "account_id": "demo_low_01"},
        )
        assert response.status_code == status
        assert response.json()["error"]["code"] == code
        assert "risk_score" not in response.json()


def test_ac3_ac4_ac5_ac6_ui_retry_reset_clears_state_and_restores_focus(tmp_path) -> None:
    app = TestClient(create_app(settings=_settings(tmp_path)), raise_server_exceptions=False)
    page = app.get("/").text
    script = app.get("/static/app.js").text

    assert 'id="retry-button"' in page
    assert 'id="new-assessment-button"' in page
    for state in [
        "previewPanel.hidden = true",
        "completenessPanel.hidden = true",
        "riskPanel.hidden = true",
        "decisionPanel.hidden = true",
        "currentAssessmentId = null",
        "identifierInput.focus()",
    ]:
        assert state in script
    assert "form.requestSubmit()" in script
