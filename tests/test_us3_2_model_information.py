from fastapi.testclient import TestClient

from backend.app.main import app


def test_ac1_ac2_page_reports_verified_scope_versions_and_evidence() -> None:
    """US3.2 AC1-AC2: the model card exposes its identity and evidence."""

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
    """US3.2 AC3: known limits and prohibited enforcement stay visible."""

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
    """US3.2 AC4: both result states link directly to the model card."""

    body = TestClient(app).get("/").text
    assert body.count('href="/model-information"') >= 2
    completeness = body.index('id="completeness-panel"')
    risk = body.index('id="risk-panel"')
    assert 'href="/model-information"' in body[completeness:risk]
    assert 'href="/model-information"' in body[risk:]


def test_tutor_feedback_explains_features_and_metrics_in_plain_language() -> None:
    """Tutor feedback: non-technical readers get instructions and definitions."""

    body = TestClient(app).get("/model-information").text
    for expected in [
        "How to use this page",
        "This reference page does not change your assessment.",
        "What the 12 public-data features mean",
        "Account age",
        "Follower count",
        "Following count",
        "Follower-to-following ratio",
        "Tweet count",
        "Posting frequency",
        "Description length",
        "Username length",
        "Profile completeness",
        "it is not the separate overall 50% scoring gate",
        "Verified status",
        "Default profile image",
        "Description present",
        "A risk score is a ranking signal, not a probability",
        "about 42 of every 100",
        "about 99 of every 100",
    ]:
        assert expected in body

    assert 'id="reading-guide-title"' in body
    assert 'href="#feature-guide"' in body
    assert 'href="#performance-guide"' in body
    assert 'href="#risks-title"' in body
    assert 'href="/#assessment-results"' in body


def test_tutor_feedback_leads_with_plain_language_and_folds_technical_record() -> None:
    """Tutor feedback: ordinary guidance precedes a collapsed technical record."""

    body = TestClient(app).get("/model-information").text
    for expected in [
        "How to understand an account risk result",
        "What this tool checks",
        "How to read the result",
        "When the result needs extra care",
        "Technical model and evaluation record",
    ]:
        assert expected in body

    details_start = body.index('<details class="technical-record"')
    assert "<details open" not in body
    assert body.index("What this tool checks") < details_start
    assert body.index("xgb-offline-v1") > details_start
    assert 'href="/#assessment-results"' in body
