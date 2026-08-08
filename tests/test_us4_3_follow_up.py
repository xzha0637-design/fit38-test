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


def _assessment(client, account_id):
    return client.post(
        "/api/v1/assessments",
        json={"platform": "x", "account_id": account_id},
    ).json()["assessment_id"]


def test_ac1_completed_and_insufficient_assessments_can_be_flagged(tmp_path) -> None:
    client, _ = _client(tmp_path)
    for account in ["demo_high_01", "demo_incomplete_01"]:
        assessment_id = _assessment(client, account)
        response = client.put(
            f"/api/v1/assessments/{assessment_id}/follow-up",
            headers={"X-Project-Role": "analyst"},
            json={"status": "flagged", "reason": "additional_context"},
        )
        assert response.status_code == 200
        assert response.json()["status"] == "flagged"


def test_ac2_ac3_reason_update_clear_and_authorisation(tmp_path) -> None:
    client, _ = _client(tmp_path)
    assessment_id = _assessment(client, "demo_medium_01")
    url = f"/api/v1/assessments/{assessment_id}/follow-up"
    assert client.put(
        url,
        headers={"X-Project-Role": "analyst"},
        json={"status": "flagged", "reason": ""},
    ).status_code == 400
    assert client.put(
        url, json={"status": "flagged", "reason": "review"}
    ).status_code == 403
    assert client.put(
        url,
        headers={"X-Project-Role": "analyst"},
        json={"status": "flagged", "reason": "review"},
    ).status_code == 200
    assert client.put(
        url,
        headers={"X-Project-Role": "analyst"},
        json={"status": "flagged", "reason": "updated reason"},
    ).status_code == 200
    assert client.put(
        url,
        headers={"X-Project-Role": "analyst"},
        json={"status": "cleared", "reason": ""},
    ).json()["status"] == "cleared"


def test_ac4_ac5_minimal_record_and_no_platform_action(tmp_path) -> None:
    client, database = _client(tmp_path)
    assessment_id = _assessment(client, "demo_high_01")
    response = client.put(
        f"/api/v1/assessments/{assessment_id}/follow-up",
        headers={"X-Project-Role": "analyst"},
        json={"status": "flagged", "reason": "high_priority"},
    )
    assert "No platform action" in response.json()["acknowledgement"]
    with sqlite3.connect(database) as connection:
        columns = [
            row[1] for row in connection.execute("PRAGMA table_info(follow_up_records)")
        ]
    assert columns == [
        "assessment_reference",
        "model_version",
        "follow_up_status",
        "reason",
        "timestamp",
    ]


def test_follow_up_context_survives_application_restart(tmp_path) -> None:
    """A follow-up remains available when the server restarts after assessment."""

    first_client, _ = _client(tmp_path)
    assessment_id = _assessment(first_client, "demo_medium_01")

    restarted_client, _ = _client(tmp_path)
    response = restarted_client.put(
        f"/api/v1/assessments/{assessment_id}/follow-up",
        headers={"X-Project-Role": "analyst"},
        json={"status": "flagged", "reason": "restart recovery"},
    )

    assert response.status_code == 200
    assert response.json()["status"] == "flagged"
