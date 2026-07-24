from pathlib import Path

from fastapi.testclient import TestClient

from backend.app.config import PROJECT_ROOT, Settings
from backend.app.main import create_app


class ModelNotNeededForIntake:
    ready = False
    missing_artifacts: list[str] = []


def _client(tmp_path: Path) -> TestClient:
    settings = Settings(
        demo_data_path=PROJECT_ROOT / "data" / "fixtures" / "demo_accounts.csv",
        artifact_dir=tmp_path / "artifacts",
        database_path=tmp_path / "feedback.sqlite3",
    )
    return TestClient(
        create_app(settings=settings, model_service=ModelNotNeededForIntake()),
        raise_server_exceptions=False,
    )


def test_ac1_ac3_valid_identifier_starts_exactly_one_normalised_intake(tmp_path) -> None:
    """US1.1 AC1/AC3: @ variants resolve to one deterministic offline account."""
    client = _client(tmp_path)

    prefixed = client.post("/api/v1/intake", json={"identifier": "@CIVIC_UPDATES"})
    plain = client.post("/api/v1/intake", json={"identifier": "civic_updates"})

    assert prefixed.status_code == 200
    assert plain.status_code == 200
    assert prefixed.json() == plain.json()
    assert plain.json()["assessment_count"] == 1
    assert plain.json()["account_id"] == "demo_low_01"
    assert plain.json()["data_source"] == "offline_fixture"


def test_ac2_blank_unsupported_and_unknown_identifiers_are_controlled(tmp_path) -> None:
    """US1.1 AC2: invalid input never starts intake and returns actionable errors."""
    client = _client(tmp_path)

    for identifier in ["", "bad-name!", "two words"]:
        response = client.post("/api/v1/intake", json={"identifier": identifier})
        assert response.status_code == 400
        assert response.json()["error"]["code"] == "invalid_request"

    unknown = client.post("/api/v1/intake", json={"identifier": "not_preloaded"})
    assert unknown.status_code == 404
    assert "preloaded" in unknown.json()["error"]["message"].lower()


def test_ac4_ac5_demo_selector_has_representative_deterministic_scenarios(tmp_path) -> None:
    """US1.1 AC4/AC5: Low, Medium, High fixtures are stable and offline."""
    client = _client(tmp_path)

    first = client.get("/api/v1/demo/accounts", params={"limit": 3})
    second = client.get("/api/v1/demo/accounts", params={"limit": 3})

    assert first.status_code == 200
    assert first.json() == second.json()
    accounts = first.json()["accounts"]
    assert {account["scenario"] for account in accounts} == {"low", "medium", "high"}
    assert all(account["source_dataset"] == "offline_fixture" for account in accounts)


def test_ac1_ac2_ac6_page_has_loading_validation_and_accessible_labels(tmp_path) -> None:
    """US1.1 AC1/AC2/AC6: core native controls and live states are labelled."""
    page = _client(tmp_path).get("/")

    assert page.status_code == 200
    assert 'label for="account-identifier"' in page.text
    assert 'label for="demo-account"' in page.text
    assert 'id="assess-button"' in page.text
    assert 'aria-live="polite"' in page.text
    assert "Preparing offline data" in page.text
    assert 'id="identifier-error" class="field-error" role="alert"' in page.text
