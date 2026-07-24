import json
import subprocess
from pathlib import Path

from fastapi.testclient import TestClient

from backend.app.config import PROJECT_ROOT
from backend.app.main import app


SCRIPT = PROJECT_ROOT / "frontend" / "batch-results.js"


def _run_tools(expression: str):
    program = (
        f"const tools = require({json.dumps(str(SCRIPT))});"
        f"const value = {expression};"
        "process.stdout.write(JSON.stringify(value));"
    )
    completed = subprocess.run(
        ["node", "-e", program],
        check=True,
        capture_output=True,
        text=True,
    )
    return json.loads(completed.stdout)


def test_ac1_sort_and_all_required_filters() -> None:
    results = [
        {"row_number": 2, "risk_score": 20, "risk_band": "low", "completeness_state": "eligible", "review_status": "unreviewed"},
        {"row_number": 3, "risk_score": 90, "risk_band": "high", "completeness_state": "eligible", "review_status": "unreviewed"},
        {"row_number": 4, "risk_score": None, "risk_band": None, "completeness_state": "insufficient", "review_status": None},
    ]
    encoded = json.dumps(results)
    high = _run_tools(
        f"tools.filterAndSort({encoded}, "
        "{sort:'descending',riskBand:'high',completeness:'eligible',reviewStatus:'unreviewed'})"
    )
    assert [row["row_number"] for row in high] == [3]
    insufficient = _run_tools(
        f"tools.filterAndSort({encoded}, "
        "{sort:'none',riskBand:'all',completeness:'insufficient',reviewStatus:'unavailable'})"
    )
    assert [row["row_number"] for row in insufficient] == [4]
    ascending = _run_tools(
        f"tools.filterAndSort({encoded}, "
        "{sort:'ascending',riskBand:'all',completeness:'all',reviewStatus:'all'})"
    )
    assert [row["row_number"] for row in ascending] == [2, 3, 4]


def test_ac2_active_filters_and_matching_count_are_described() -> None:
    description = _run_tools(
        "tools.describeFilters("
        "{sort:'descending',riskBand:'high',completeness:'all',reviewStatus:'unreviewed'}, 2)"
    )
    assert description == "Active: risk descending, high risk, unreviewed | 2 matching records"


def test_ac3_ac4_clear_state_restores_order_without_mutating_source() -> None:
    expression = """
    (() => {
      const source = [
        {row_number:2,risk_score:20,risk_band:'low',completeness_state:'eligible',review_status:'unreviewed',decision:'confirm'},
        {row_number:3,risk_score:90,risk_band:'high',completeness_state:'eligible',review_status:'unreviewed',decision:'override'}
      ];
      const before = JSON.stringify(source);
      tools.filterAndSort(source, {sort:'descending',riskBand:'all',completeness:'all',reviewStatus:'all'});
      const restored = tools.filterAndSort(source, {sort:'none',riskBand:'all',completeness:'all',reviewStatus:'all'});
      return {unchanged: before === JSON.stringify(source), restored};
    })()
    """
    result = _run_tools(expression)
    assert result["unchanged"] is True
    assert [row["row_number"] for row in result["restored"]] == [2, 3]
    assert [row["decision"] for row in result["restored"]] == ["confirm", "override"]


def test_ac1_ac2_ac3_browser_controls_are_present() -> None:
    page = TestClient(app).get("/").text
    for expected in [
        'id="batch-risk-sort"',
        'id="batch-risk-filter"',
        'id="batch-completeness-filter"',
        'id="batch-review-filter"',
        'id="batch-clear-filters"',
        'id="batch-filter-summary"',
    ]:
        assert expected in page
