from pathlib import Path

from fastapi.testclient import TestClient

from backend.app.config import PROJECT_ROOT, Settings
from backend.app.main import create_app


class ModelNotNeededForPreview:
    ready = False
    missing_artifacts: list[str] = []


def _client(tmp_path: Path) -> TestClient:
    settings = Settings(
        demo_data_path=PROJECT_ROOT / "data" / "fixtures" / "demo_accounts.csv",
        artifact_dir=tmp_path / "artifacts",
        database_path=tmp_path / "feedback.sqlite3",
    )
    return TestClient(
        create_app(settings=settings, model_service=ModelNotNeededForPreview()),
        raise_server_exceptions=False,
    )


def test_ac1_preview_groups_identifier_profile_activity_and_network(tmp_path) -> None:
    """US1.2 AC1: the approved public evidence groups are returned together."""
    response = _client(tmp_path).get("/api/v1/accounts/demo_low_01/preview")

    assert response.status_code == 200
    body = response.json()
    assert body["display_identifier"] == "@civic_updates"
    assert body["profile"]["description"] == "Local service and community updates"
    assert body["activity"]["account_age_days"] == 3200
    assert body["activity"]["post_count"] == 5200
    assert body["network"] == {"followers_count": 25000, "following_count": 420}


def test_ac2_missing_values_are_null_and_named_without_imputation(tmp_path) -> None:
    """US1.2 AC2: missing source fields remain null and receive plain labels."""
    body = _client(tmp_path).get(
        "/api/v1/accounts/demo_high_01/preview"
    ).json()

    assert body["profile"]["description"] is None
    assert body["profile"]["location"] is None
    assert "Profile description" in body["missing_fields"]
    assert "Location" in body["missing_fields"]


def test_ac3_only_approved_public_fields_are_exposed(tmp_path) -> None:
    """US1.2 AC3: training labels and internal model fields never enter preview."""
    body = _client(tmp_path).get(
        "/api/v1/accounts/demo_medium_01/preview"
    ).json()

    assert set(body) == {
        "account_id",
        "display_identifier",
        "data_source",
        "content_type",
        "model_output_included",
        "profile",
        "activity",
        "network",
        "missing_fields",
    }
    assert "scenario" not in body
    assert "verified" not in body["profile"]


def test_ac4_source_data_is_explicitly_separate_from_model_output(tmp_path) -> None:
    """US1.2 AC4: API and UI clearly identify source versus model content."""
    client = _client(tmp_path)
    body = client.get("/api/v1/accounts/demo_low_01/preview").json()
    page = client.get("/").text

    assert body["content_type"] == "source_data"
    assert body["data_source"] == "offline_fixture"
    assert body["model_output_included"] is False
    assert "Source data · Offline fixture" in page
    assert "No model output is displayed" in page
