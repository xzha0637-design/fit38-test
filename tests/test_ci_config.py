from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_github_quality_workflow_runs_release_checks() -> None:
    """GitHub pushes and pull requests run the documented quality gates."""

    workflow = (PROJECT_ROOT / ".github" / "workflows" / "quality.yml").read_text(
        encoding="utf-8"
    )

    for expected in [
        "push:",
        "pull_request:",
        'python-version: "3.10"',
        "python -m pytest --basetemp .pytest-tmp",
        'node --check "$file"',
        "python -m scripts.verify_run_sheet",
        "python -m pip check",
    ]:
        assert expected in workflow


def test_gitlab_quality_pipeline_matches_release_checks() -> None:
    """GitLab can run the same offline checks without project secrets."""

    pipeline = (PROJECT_ROOT / ".gitlab-ci.yml").read_text(encoding="utf-8")

    for expected in [
        "python:3.10-slim",
        "nodejs",
        "python -m pytest",
        'node --check "$file"',
        "python -m scripts.verify_run_sheet",
        "python -m pip check",
    ]:
        assert expected in pipeline
