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


def test_release_main_demo_path_and_human_review_contract(tmp_path) -> None:
    client, _ = _client(tmp_path)
    intake = client.post("/api/v1/intake", json={"identifier": "@demo_high_01"})
    assert intake.status_code == 200
    account_id = intake.json()["account_id"]
    assert client.get(f"/api/v1/accounts/{account_id}/preview").status_code == 200
    completeness = client.get(f"/api/v1/accounts/{account_id}/completeness")
    assert completeness.json()["eligible_for_scoring"] is True

    assessment = client.post(
        "/api/v1/assessments",
        json={"platform": "x", "account_id": account_id},
    )
    assert assessment.status_code == 200
    result = assessment.json()
    assert result["risk_band"] == "high"
    assert result["disclaimer"] == "Triage evidence, not a verdict."
    assert client.get("/model-information").status_code == 200

    decision = client.post(
        f"/api/v1/assessments/{result['assessment_id']}/decision",
        json={"decision": "override", "reason": "context reviewed"},
    )
    assert decision.status_code == 201
    assert "No platform action" in decision.json()["acknowledgement"]
    follow_up = client.put(
        f"/api/v1/assessments/{result['assessment_id']}/follow-up",
        headers={"X-Project-Role": "analyst"},
        json={"status": "flagged", "reason": "second review"},
    )
    assert follow_up.status_code == 200
    assert "No platform action" in follow_up.json()["acknowledgement"]


def test_release_batch_and_single_account_results_are_consistent(tmp_path) -> None:
    client, _ = _client(tmp_path)
    single = client.post(
        "/api/v1/assessments",
        json={"platform": "x", "account_id": "demo_medium_01"},
    ).json()
    batch = client.post(
        "/api/v1/batch-assessments",
        json={
            "filename": "accounts.csv",
            "content": "account_id\ndemo_medium_01\n",
        },
    ).json()["results"][0]
    assert batch["assessment_status"] == single["status"]
    assert batch["risk_score"] == single["risk_score"]
    assert batch["risk_band"] == single["risk_band"]
    assert batch["completeness_state"] == "eligible"


def test_release_persistence_remains_minimal_and_pseudonymous(tmp_path) -> None:
    client, database = _client(tmp_path)
    assessment = client.post(
        "/api/v1/assessments",
        json={"platform": "x", "account_id": "demo_low_01"},
    ).json()
    client.post(
        f"/api/v1/assessments/{assessment['assessment_id']}/decision",
        json={"decision": "confirm", "reason": ""},
    )
    with sqlite3.connect(database) as connection:
        tables = {
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )
        }
        columns = {
            table: [
                row[1]
                for row in connection.execute(f"PRAGMA table_info({table})")
            ]
            for table in tables
        }
    assert tables == {"decision_feedback", "follow_up_records"}
    persisted_names = set(columns["decision_feedback"]) | set(
        columns["follow_up_records"]
    )
    assert not persisted_names.intersection(
        {"username", "description", "location", "followers_count", "tweet_count"}
    )


def test_release_shell_has_required_accessibility_landmarks_and_labels(tmp_path) -> None:
    client, _ = _client(tmp_path)
    page = client.get("/").text
    for expected in [
        '<html lang="en">',
        'class="skip-link"',
        'id="main-content"',
        'for="account-identifier"',
        'for="demo-account"',
        'for="batch-file"',
        'aria-live="polite"',
        '<th scope="col">',
        'aria-label="Scrollable batch results"',
    ]:
        assert expected in page


def test_release_controlled_error_matrix_has_no_traceback(tmp_path) -> None:
    client, _ = _client(tmp_path)
    responses = [
        client.post("/api/v1/intake", json={"identifier": "bad value!"}),
        client.post(
            "/api/v1/assessments",
            json={"platform": "x", "account_id": "not_available"},
        ),
        client.post(
            "/api/v1/batch-assessments",
            json={"filename": "bad.csv", "content": "username\nexample\n"},
        ),
        client.put(
            "/api/v1/assessments/asmt_12345678/follow-up",
            json={"status": "flagged", "reason": "review"},
        ),
    ]
    assert [response.status_code for response in responses] == [400, 404, 400, 403]
    for response in responses:
        body = response.text.lower()
        assert "traceback" not in body
        assert "exception" not in body
        assert "error" in response.json()


def test_release_reset_code_clears_single_and_batch_stale_state() -> None:
    script = (PROJECT_ROOT / "frontend" / "app.js").read_text(encoding="utf-8")
    for expected in [
        "followUpForm.reset();",
        'followUpStatus.textContent = "";',
        "resetBatchControls();",
        "batchSourceResults = [];",
    ]:
        assert expected in script


def test_tutor_feedback_preserves_current_assessment_across_model_information() -> None:
    """Tutor feedback: session restoration keeps the completed result on return."""
    script = (PROJECT_ROOT / "frontend" / "app.js").read_text(encoding="utf-8")

    for expected in [
        "sessionStorage.setItem",
        "sessionStorage.getItem",
        "sessionStorage.removeItem",
        "persistAssessmentState",
        "restoreAssessmentState",
        "renderPreview(saved.preview)",
        "renderCompleteness(saved.completeness)",
        "renderRiskResult(saved.assessment.payload)",
        'window.location.hash === "#assessment-results"',
    ]:
        assert expected in script
