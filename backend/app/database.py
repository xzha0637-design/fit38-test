import sqlite3
from datetime import datetime, timezone
from pathlib import Path


class AssessmentNotFoundError(LookupError):
    pass


class DuplicateOverrideError(RuntimeError):
    pass


class StoreUnavailableError(RuntimeError):
    pass


class FeedbackStore:
    """Persist only assessment references and analyst overrides, never raw profiles."""

    def __init__(self, database_path: Path) -> None:
        self.database_path = Path(database_path)
        self.ready = False
        self.error: str | None = None
        self.initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.database_path, timeout=5.0)
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

    def initialize(self) -> None:
        try:
            self.database_path.parent.mkdir(parents=True, exist_ok=True)
            with self._connect() as connection:
                connection.executescript(
                    """
                    CREATE TABLE IF NOT EXISTS assessments (
                        assessment_id TEXT PRIMARY KEY,
                        created_at TEXT NOT NULL,
                        model_id TEXT NOT NULL,
                        risk_band TEXT NOT NULL,
                        status TEXT NOT NULL
                    );
                    CREATE TABLE IF NOT EXISTS overrides (
                        assessment_id TEXT PRIMARY KEY,
                        created_at TEXT NOT NULL,
                        override_label TEXT NOT NULL,
                        reason_code TEXT NOT NULL,
                        FOREIGN KEY (assessment_id) REFERENCES assessments(assessment_id)
                    );
                    """
                )
                connection.execute("SELECT 1")
            self.ready = True
            self.error = None
        except Exception as exc:
            self.ready = False
            self.error = str(exc)

    def record_assessment(
        self,
        assessment_id: str,
        model_id: str,
        risk_band: str,
        status: str,
    ) -> None:
        if not self.ready:
            raise StoreUnavailableError(self.error or "Feedback store is unavailable.")
        created_at = datetime.now(timezone.utc).isoformat()
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO assessments
                    (assessment_id, created_at, model_id, risk_band, status)
                VALUES (?, ?, ?, ?, ?)
                """,
                (assessment_id, created_at, model_id, risk_band, status),
            )

    def record_override(
        self,
        assessment_id: str,
        override_label: str,
        reason_code: str,
    ) -> None:
        if not self.ready:
            raise StoreUnavailableError(self.error or "Feedback store is unavailable.")
        created_at = datetime.now(timezone.utc).isoformat()
        with self._connect() as connection:
            exists = connection.execute(
                "SELECT 1 FROM assessments WHERE assessment_id = ?",
                (assessment_id,),
            ).fetchone()
            if exists is None:
                raise AssessmentNotFoundError(assessment_id)
            try:
                connection.execute(
                    """
                    INSERT INTO overrides
                        (assessment_id, created_at, override_label, reason_code)
                    VALUES (?, ?, ?, ?)
                    """,
                    (assessment_id, created_at, override_label, reason_code),
                )
            except sqlite3.IntegrityError as exc:
                raise DuplicateOverrideError(assessment_id) from exc
