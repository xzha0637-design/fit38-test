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


def _assessment(client: TestClient) -> str:
    body = client.post(
        "/api/v1/assessments",
        json={"platform": "x", "account_id": "demo_high_01"},
    ).json()
    return body["assessment_id"]


def test_ac1_ac2_decision_requires_assessment_and_override_reason(tmp_path) -> None:
    """US4.1 AC1/AC2: decisions follow completed results; override needs reason."""
    client, _ = _client(tmp_path)
    missing = client.post(
        "/api/v1/assessments/asmt_00000000/decision",
        json={"decision": "confirm", "reason": ""},
    )
    assert missing.status_code == 404

    assessment_id = _assessment(client)
    invalid = client.post(
        f"/api/v1/assessments/{assessment_id}/decision",
        json={"decision": "override", "reason": "  "},
    )
    assert invalid.status_code == 400


def test_ac3_ac4_minimal_feedback_and_no_platform_action(tmp_path) -> None:
    """US4.1 AC3/AC4: store only approved pseudonymous feedback fields."""
    client, database = _client(tmp_path)
    assessment_id = _assessment(client)
    response = client.post(
        f"/api/v1/assessments/{assessment_id}/decision",
        json={"decision": "override", "reason": "context_requires_review"},
    )
    assert response.status_code == 201
    assert "No platform action" in response.json()["acknowledgement"]

    with sqlite3.connect(database) as connection:
        columns = [
            row[1] for row in connection.execute("PRAGMA table_info(decision_feedback)")
        ]
        record = connection.execute("SELECT * FROM decision_feedback").fetchone()
    assert columns == [
        "assessment_reference",
        "model_version",
        "recommendation",
        "analyst_decision",
        "reason",
        "timestamp",
    ]
    assert record[0] == assessment_id
    assert record[1] == "xgb-offline-v1"
    assert record[3:5] == ("override", "context_requires_review")


def test_ac5_acknowledgement_and_duplicate_prevention(tmp_path) -> None:
    """US4.1 AC5: successful feedback is acknowledged and idempotent."""
    client, _ = _client(tmp_path)
    assessment_id = _assessment(client)
    url = f"/api/v1/assessments/{assessment_id}/decision"

    first = client.post(url, json={"decision": "confirm", "reason": ""})
    duplicate = client.post(url, json={"decision": "confirm", "reason": ""})

    assert first.status_code == 201
    assert first.json()["status"] == "recorded"
    assert duplicate.status_code == 409


def test_assessment_context_survives_application_restart(tmp_path) -> None:
    """A displayed assessment remains actionable after the server is recreated."""

    first_client, _ = _client(tmp_path)
    assessment_id = _assessment(first_client)
    assert len(assessment_id) == 37

    restarted_client, _ = _client(tmp_path)
    response = restarted_client.post(
        f"/api/v1/assessments/{assessment_id}/decision",
        json={"decision": "confirm", "reason": ""},
    )

    assert response.status_code == 201


def test_expired_assessment_contexts_are_purged_and_rejected(tmp_path) -> None:
    """Expired transient contexts are bounded without deleting decision evidence."""

    client, database = _client(tmp_path)
    expired_id = _assessment(client)
    with sqlite3.connect(database) as connection:
        connection.execute(
            "UPDATE assessment_contexts SET expires_at = ? WHERE assessment_reference = ?",
            ("2000-01-01T00:00:00+00:00", expired_id),
        )

    active_id = _assessment(client)
    with sqlite3.connect(database) as connection:
        contexts = {
            row[0]
            for row in connection.execute(
                "SELECT assessment_reference FROM assessment_contexts"
            )
        }

    assert contexts == {active_id}
    rejected = client.post(
        f"/api/v1/assessments/{expired_id}/decision",
        json={"decision": "confirm", "reason": ""},
    )
    assert rejected.status_code == 404
