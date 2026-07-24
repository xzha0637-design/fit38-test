import logging
import sqlite3
from pathlib import Path

from fastapi.testclient import TestClient

from backend.app.config import PROJECT_ROOT, Settings
from backend.app.main import create_app


def _client(tmp_path: Path) -> tuple[TestClient, Path]:
    database = tmp_path / "feedback.sqlite3"
    settings = Settings(
        demo_data_path=PROJECT_ROOT / "data" / "fixtures" / "demo_accounts.csv",
        artifact_dir=PROJECT_ROOT / "models" / "xgb-offline-v1",
        database_path=database,
    )
    return TestClient(create_app(settings=settings), raise_server_exceptions=False), database


def _record(client: TestClient) -> None:
    assessment = client.post(
        "/api/v1/assessments",
        json={"platform": "x", "account_id": "demo_low_01"},
    ).json()
    client.post(
        f"/api/v1/assessments/{assessment['assessment_id']}/decision",
        json={"decision": "confirm", "reason": ""},
    )


def test_ac1_ac3_only_minimal_feedback_table_persists(tmp_path) -> None:
    client, database = _client(tmp_path)
    _record(client)
    with sqlite3.connect(database) as connection:
        tables = {
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )
        }
        columns = [
            row[1] for row in connection.execute("PRAGMA table_info(decision_feedback)")
        ]
    assert tables == {"decision_feedback", "follow_up_records"}
    assert columns == [
        "assessment_reference",
        "model_version",
        "recommendation",
        "analyst_decision",
        "reason",
        "timestamp",
    ]


def test_ac2_unexpected_logs_exclude_payload_token_and_identifier(tmp_path, caplog) -> None:
    class ExplodingAdapter:
        ready = True
        account_count = 1
        error = None

        def get_account(self, _identifier):
            raise ValueError("token=secret raw_profile demo_low_01")

        def list_accounts(self, _limit):
            return []

    settings = Settings(database_path=tmp_path / "feedback.sqlite3")
    client = TestClient(
        create_app(settings=settings, data_adapter=ExplodingAdapter()),
        raise_server_exceptions=False,
    )
    with caplog.at_level(logging.ERROR):
        response = client.post("/api/v1/intake", json={"identifier": "demo_low_01"})
    assert response.status_code == 500
    assert "token=secret" not in caplog.text
    assert "raw_profile" not in caplog.text
    assert "demo_low_01" not in caplog.text


def test_ac4_feedback_requires_authorised_role(tmp_path) -> None:
    client, _ = _client(tmp_path)
    _record(client)
    assert client.get("/api/v1/feedback").status_code == 403
    assert client.get(
        "/api/v1/feedback", headers={"X-Project-Role": "visitor"}
    ).status_code == 403
    allowed = client.get(
        "/api/v1/feedback", headers={"X-Project-Role": "analyst"}
    )
    assert allowed.status_code == 200
    assert allowed.json()["count"] == 1
    assert set(allowed.json()["records"][0]) == {
        "assessment_reference",
        "model_version",
        "recommendation",
        "analyst_decision",
        "reason",
        "timestamp",
    }
