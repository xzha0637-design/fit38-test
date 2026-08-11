import json
import subprocess

from backend.app.config import PROJECT_ROOT


API_CLIENT = PROJECT_ROOT / "frontend" / "api-client.js"
ASSESSMENT_STATE = PROJECT_ROOT / "frontend" / "assessment-state.js"


def _run_node(program: str) -> dict:
    """Execute a dependency-free browser-module scenario in Node."""

    completed = subprocess.run(
        ["node", "-e", program],
        check=True,
        capture_output=True,
        text=True,
    )
    return json.loads(completed.stdout)


def _valid_snapshot() -> dict:
    """Return the smallest valid version-two browser restoration snapshot."""

    return {
        "schemaVersion": 2,
        "identifier": "@example",
        "status": "One offline assessment is ready.",
        "preview": {
            "account_id": "100",
            "display_identifier": "@example",
            "profile": {
                "username": "example",
                "description": None,
                "location": None,
            },
            "activity": {
                "account_age_days": 100,
                "post_count": 20,
                "posts_per_day": 0.2,
            },
            "network": {"followers_count": 10, "following_count": 5},
            "missing_fields": ["Description", "Location"],
        },
        "completeness": {
            "completeness_percentage": 80,
            "eligible_for_scoring": True,
            "status": "Eligible for scoring",
            "missing_features": [],
            "missing_data_caveat": None,
        },
        "assessment": {
            "kind": "scored",
            "payload": {
                "assessment_id": "asmt_0123456789abcdef0123456789abcdef",
                "account_id": "100",
                "status": "completed",
                "risk_score": 20,
                "risk_band": "low",
                "risk_band_label": "Low",
                "recommendation": "no_concern",
                "model_version": "model-v1",
                "threshold_version": "threshold-v1",
                "assessment_time": "2026-08-08T00:00:00Z",
                "warning": "Triage evidence, not a verdict.",
                "uncertainty": "Human review is still required.",
                "top_factors": [
                    {
                        "feature": "followers_count",
                        "label": None,
                        "direction": "decreases_risk",
                        "observed_value": "10",
                    }
                ],
            },
        },
        "review": {
            "decision": {
                "value": "confirm",
                "acknowledgement": "Decision recorded. No platform action was taken.",
            },
            "followUp": {
                "status": "flagged",
                "reason": "second review",
                "message": "Flagged. Follow-up updated. No platform action was taken.",
            },
        },
    }


def test_versioned_snapshot_restores_review_state_and_rejects_corruption() -> None:
    """Valid review state survives navigation; parseable schema damage is cleared."""

    snapshot = json.dumps(_valid_snapshot())
    program = f"""
      const state = require({json.dumps(str(ASSESSMENT_STATE))});
      const values = new Map();
      const storage = {{
        setItem: (key, value) => values.set(key, value),
        getItem: (key) => values.get(key) || null,
        removeItem: (key) => values.delete(key),
      }};
      const saved = state.saveSnapshot({snapshot}, storage);
      const restored = state.loadSnapshot(storage);
      const damaged = {{...saved, completeness: {{...saved.completeness, completeness_percentage: 140}}}};
      storage.setItem(state.STORAGE_KEY, JSON.stringify(damaged));
      const rejected = state.loadSnapshot(storage);
      process.stdout.write(JSON.stringify({{
        decision: restored.review.decision.value,
        followUp: restored.review.followUp.status,
        rejected,
        removed: storage.getItem(state.STORAGE_KEY) === null,
      }}));
    """

    result = _run_node(program)
    assert result == {
        "decision": "confirm",
        "followUp": "flagged",
        "rejected": None,
        "removed": True,
    }


def test_api_client_handles_non_json_and_timeout_failures() -> None:
    """Unreadable responses and timeouts become stable user-facing errors."""

    program = f"""
      const api = require({json.dumps(str(API_CLIENT))});
      (async () => {{
        global.fetch = async () => ({{
          ok: false,
          status: 500,
          text: async () => '<html>proxy failure</html>',
        }});
        let invalid;
        try {{
          await api.requestJson('/invalid', {{}}, {{fallbackMessage: 'Safe fallback.'}});
        }} catch (error) {{
          invalid = {{code: error.code, message: error.message}};
        }}
        global.fetch = (_url, options) => new Promise((_resolve, reject) => {{
          options.signal.addEventListener('abort', () => {{
            const error = new Error('aborted');
            error.name = 'AbortError';
            reject(error);
          }});
        }});
        let timeout;
        try {{
          await api.requestJson('/slow', {{}}, {{timeoutMs: 5}});
        }} catch (error) {{
          timeout = {{code: error.code, message: error.message}};
        }}
        process.stdout.write(JSON.stringify({{invalid, timeout}}));
      }})().catch((error) => {{ console.error(error); process.exit(1); }});
    """

    result = _run_node(program)
    assert result["invalid"] == {
        "code": "invalid_response",
        "message": "Safe fallback.",
    }
    assert result["timeout"]["code"] == "request_timeout"
    assert "did not respond in time" in result["timeout"]["message"]


def test_follow_up_controller_exposes_busy_and_persistence_guards() -> None:
    """Static browser wiring retains the visible resilience controls."""

    script = (PROJECT_ROOT / "frontend" / "app.js").read_text(encoding="utf-8")
    review = (PROJECT_ROOT / "frontend" / "review-controller.js").read_text(
        encoding="utf-8"
    )
    page = (PROJECT_ROOT / "frontend" / "index.html").read_text(encoding="utf-8")
    styles = (PROJECT_ROOT / "frontend" / "styles.css").read_text(encoding="utf-8")

    for expected in [
        "followUpRequestPending",
        "setFollowUpLoading(true)",
        'followUpForm.setAttribute("aria-busy"',
        "requestJson(",
    ]:
        assert expected in review
    assert "persistReviewState" in script
    assert "reviewController.restore(saved.review)" in script
    assert page.index("/static/api-client.js") < page.index("/static/app.js")
    assert page.index("/static/assessment-state.js") < page.index("/static/app.js")
    assert page.index("/static/review-controller.js") < page.index("/static/app.js")
    assert "[hidden]" in styles
    assert "display: none !important" in styles
