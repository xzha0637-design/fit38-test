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
        self._pending_assessments: dict[str, tuple[str, str]] = {}
        self.initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.database_path, timeout=5.0)
        return connection

    def initialize(self) -> None:
        try:
            self.database_path.parent.mkdir(parents=True, exist_ok=True)
            with self._connect() as connection:
                connection.executescript(
                    """
                    CREATE TABLE IF NOT EXISTS decision_feedback (
                        assessment_reference TEXT PRIMARY KEY,
                        model_version TEXT NOT NULL,
                        recommendation TEXT NOT NULL,
                        analyst_decision TEXT NOT NULL,
                        reason TEXT NOT NULL,
                        timestamp TEXT NOT NULL
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
        self._pending_assessments[assessment_id] = (model_id, recommendation)

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
            duplicate = connection.execute(
                """
                SELECT 1 FROM decision_feedback
                WHERE assessment_reference = ?
                """,
                (assessment_id,),
            ).fetchone()
        if duplicate is not None:
            raise DuplicateOverrideError(assessment_id)
        context = self._pending_assessments.get(assessment_id)
        if context is None:
            raise AssessmentNotFoundError(assessment_id)
        with self._connect() as connection:
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
                        context[0],
                        context[1],
                        analyst_decision,
                        reason,
                        created_at,
                    ),
                )
            except sqlite3.IntegrityError as exc:
                raise DuplicateOverrideError(assessment_id) from exc
        self._pending_assessments.pop(assessment_id, None)

    def list_decisions(self) -> list[dict[str, str]]:
        if not self.ready:
            raise StoreUnavailableError(self.error or "Feedback store is unavailable.")
        with self._connect() as connection:
            connection.row_factory = sqlite3.Row
            rows = connection.execute(
                """
                SELECT assessment_reference, model_version, recommendation,
                       analyst_decision, reason, timestamp
                FROM decision_feedback
                ORDER BY timestamp DESC
                """
            ).fetchall()
        return [dict(row) for row in rows]

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
