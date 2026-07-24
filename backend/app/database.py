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
                    CREATE TABLE IF NOT EXISTS assessment_context (
                        assessment_id TEXT PRIMARY KEY,
                        created_at TEXT NOT NULL,
                        model_id TEXT NOT NULL,
                        recommendation TEXT NOT NULL
                    );
                    CREATE TABLE IF NOT EXISTS decision_feedback (
                        assessment_reference TEXT PRIMARY KEY,
                        model_version TEXT NOT NULL,
                        recommendation TEXT NOT NULL,
                        analyst_decision TEXT NOT NULL,
                        reason TEXT NOT NULL,
                        timestamp TEXT NOT NULL,
                        FOREIGN KEY (assessment_reference)
                            REFERENCES assessment_context(assessment_id)
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
        recommendation: str,
    ) -> None:
        if not self.ready:
            raise StoreUnavailableError(self.error or "Feedback store is unavailable.")
        created_at = datetime.now(timezone.utc).isoformat()
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO assessment_context
                    (assessment_id, created_at, model_id, recommendation)
                VALUES (?, ?, ?, ?)
                """,
                (assessment_id, created_at, model_id, recommendation),
            )

    def record_decision(
        self,
        assessment_id: str,
        analyst_decision: str,
        reason: str,
    ) -> None:
        if not self.ready:
            raise StoreUnavailableError(self.error or "Feedback store is unavailable.")
        created_at = datetime.now(timezone.utc).isoformat()
        with self._connect() as connection:
            exists = connection.execute(
                """
                SELECT model_id, recommendation
                FROM assessment_context
                WHERE assessment_id = ?
                """,
                (assessment_id,),
            ).fetchone()
            if exists is None:
                raise AssessmentNotFoundError(assessment_id)
            try:
                connection.execute(
                    """
                    INSERT INTO decision_feedback
                        (assessment_reference, model_version, recommendation,
                         analyst_decision, reason, timestamp)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        assessment_id,
                        exists[0],
                        exists[1],
                        analyst_decision,
                        reason,
                        created_at,
                    ),
                )
            except sqlite3.IntegrityError as exc:
                raise DuplicateOverrideError(assessment_id) from exc

    def record_override(
        self,
        assessment_id: str,
        override_label: str,
        reason_code: str,
    ) -> None:
        """Backward-compatible wrapper for the supplied baseline endpoint."""

        self.record_decision(
            assessment_id=assessment_id,
            analyst_decision=f"override:{override_label}",
            reason=reason_code,
        )
