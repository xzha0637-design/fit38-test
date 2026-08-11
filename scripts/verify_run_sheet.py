"""Repeatable, offline verification of the Iteration 2 demonstration path."""

from tempfile import TemporaryDirectory
from pathlib import Path

from fastapi.testclient import TestClient

from backend.app.config import PROJECT_ROOT, Settings
from backend.app.main import create_app


def require(condition: bool, message: str) -> None:
    """Raise a clear release-check error when a required condition fails."""

    if not condition:
        raise RuntimeError(message)


def main() -> None:
    """Exercise the offline browser, model, single, and batch release paths."""

    with TemporaryDirectory(prefix="fit5238-run-sheet-") as temporary:
        settings = Settings(
            demo_data_path=PROJECT_ROOT / "data" / "fixtures" / "demo_accounts.csv",
            artifact_dir=PROJECT_ROOT / "models" / "xgb-offline-v1",
            database_path=Path(temporary) / "feedback.sqlite3",
        )
        with TestClient(
            create_app(settings=settings),
            raise_server_exceptions=False,
        ) as client:
            require(client.get("/").status_code == 200, "Browser shell unavailable")
            require(
                client.get("/model-information").status_code == 200,
                "Model information unavailable",
            )
            health = client.get("/api/v1/health")
            require(health.status_code == 200, "Health check not ready")
            require(health.json()["status"] == "ok", "A required service is degraded")

            intake = client.post(
                "/api/v1/intake",
                json={"identifier": "@demo_high_01"},
            )
            require(intake.status_code == 200, "Demo intake failed")
            account_id = intake.json()["account_id"]
            require(
                client.get(f"/api/v1/accounts/{account_id}/preview").status_code == 200,
                "Preview failed",
            )
            completeness = client.get(
                f"/api/v1/accounts/{account_id}/completeness"
            )
            require(
                completeness.json()["eligible_for_scoring"] is True,
                "High demo fixture unexpectedly became ineligible",
            )
            assessment = client.post(
                "/api/v1/assessments",
                json={"platform": "x", "account_id": account_id},
            )
            require(assessment.status_code == 200, "Single assessment failed")
            require(
                assessment.json()["risk_band"] == "high",
                "Representative High result changed",
            )

            batch = client.post(
                "/api/v1/batch-assessments",
                json={
                    "filename": "accounts.csv",
                    "content": (
                        "account_id\n"
                        "demo_low_01\n"
                        "bad identifier!\n"
                        "demo_incomplete_01\n"
                    ),
                },
            )
            require(batch.status_code == 200, "Batch assessment failed")
            require(
                batch.json()["completed_count"] == 2
                and batch.json()["failed_count"] == 1,
                "Batch partial-success counts changed",
            )

    print("RUN SHEET PASS: offline shell, model info, health, single and batch paths")


if __name__ == "__main__":
    main()
