from fastapi.testclient import TestClient

from backend.app.main import app


def test_ac1_ac2_page_reports_verified_scope_versions_and_evidence() -> None:
    response = TestClient(app).get("/model-information")
    assert response.status_code == 200
    body = response.text
    for expected in [
        "Twitter/X",
        "Public-data feature schema",
        "xgb-offline-v1",
        "threshold-v1",
        "twitter_human_bots_cleaned.csv",
        "twitter_bot_training_data2_cleaned.csv",
        "F1",
        "Precision",
        "Recall",
        "Calibration evidence",
        "24 July 2026",
    ]:
        assert expected in body


def test_ac3_page_discloses_required_risks_and_prohibition() -> None:
    body = TestClient(app).get("/model-information").text.lower()
    for expected in [
        "full follower/following graph features",
        "cross-dataset",
        "prevalence shift",
        "concept drift",
        "false positives",
        "automated enforcement is prohibited",
    ]:
        assert expected in body


def test_ac4_scored_and_insufficient_result_sections_link_directly() -> None:
    body = TestClient(app).get("/").text
    assert body.count('href="/model-information"') >= 2
    completeness = body.index('id="completeness-panel"')
    risk = body.index('id="risk-panel"')
    assert 'href="/model-information"' in body[completeness:risk]
    assert 'href="/model-information"' in body[risk:]
