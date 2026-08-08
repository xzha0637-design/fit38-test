from fastapi.testclient import TestClient

from backend.app.main import app


client = TestClient(app, raise_server_exceptions=False)


def _upload(filename: str, content: str):
    return client.post(
        "/api/v1/batch-assessments",
        json={"filename": filename, "content": content},
    )


def test_ac1_file_type_header_and_row_limit_are_validated() -> None:
    assert _upload("accounts.txt", "account_id\ndemo_low_01\n").status_code == 400
    assert _upload("accounts.csv", "username\ndemo_low_01\n").status_code == 400
    over_limit = "account_id\n" + "\n".join(f"account_{index}" for index in range(101))
    response = _upload("accounts.csv", over_limit)
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "batch_row_limit_exceeded"


def test_ac1_ac2_duplicates_and_invalid_rows_do_not_block_valid_rows() -> None:
    response = _upload(
        "accounts.csv",
        "account_id\n"
        "demo_low_01\n"
        "bad identifier!\n"
        "DEMO_LOW_01\n"
        "demo_high_01\n",
    )
    assert response.status_code == 200
    body = response.json()
    assert body["total_rows"] == 4
    assert body["completed_count"] == 2
    assert body["failed_count"] == 2
    assert [row["processing_status"] for row in body["results"]] == [
        "completed",
        "failed",
        "failed",
        "completed",
    ]
    assert body["results"][1]["error"] == "Invalid identifier format."
    assert body["results"][2]["error"] == "Duplicate account identifier."


def test_ac2_insufficient_and_unknown_rows_are_reported_independently() -> None:
    response = _upload(
        "accounts.csv",
        "account_id\ndemo_incomplete_01\nnot_in_offline_fixture\n",
    )
    body = response.json()
    assert body["completed_count"] == 1
    assert body["failed_count"] == 1
    assert body["results"][0]["assessment_status"] == "insufficient_data"
    assert body["results"][0]["completeness_state"] == "insufficient"
    assert "offline demonstration dataset" in body["results"][1]["error"]


def test_account_id_and_username_alias_are_one_batch_account() -> None:
    """Canonical account resolution prevents aliases bypassing duplicate checks."""

    response = _upload(
        "accounts.csv",
        "account_id\n20611469\n@DeFotis\n",
    )

    assert response.status_code == 200
    body = response.json()
    assert body["completed_count"] == 1
    assert body["failed_count"] == 1
    assert [row["account_id"] for row in body["results"]] == [
        "20611469",
        "20611469",
    ]
    assert body["results"][1]["error"] == "Duplicate account identifier."


def test_ac3_ac4_page_exposes_progress_counts_and_no_action_wording() -> None:
    page = client.get("/").text
    for expected in [
        'id="batch-progress"',
        'id="batch-completed-count"',
        'id="batch-failed-count"',
        'class="file-picker-input"',
        'aria-describedby="batch-file-hint batch-file-name"',
        "Choose file",
        "No file selected",
        "No platform action",
    ]:
        assert expected in page
    script = client.get("/static/batch-controller.js").text
    assert 'batchFile.addEventListener("change"' in script
    assert 'batchFile.files[0]?.name || "No file selected"' in script
    response = _upload("accounts.csv", "account_id\ndemo_medium_01\n")
    assert "No platform action" in response.json()["acknowledgement"]
