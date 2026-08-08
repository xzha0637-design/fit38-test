import sqlite3
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path


class AssessmentNotFoundError(LookupError):
    """Raised when an action references no active assessment context."""


class DuplicateOverrideError(RuntimeError):
    """Raised when a final decision already exists for an assessment."""


class StoreUnavailableError(RuntimeError):
    """Raised when the minimal SQLite feedback store cannot be used safely."""


@dataclass(frozen=True)
class AssessmentContext:
    """Minimal model context required by later human-review actions."""

    model_version: str
    recommendation: str


ASSESSMENT_CONTEXT_TTL = timedelta(hours=24)


class FeedbackStore:
    """Persist only assessment references and analyst overrides, never raw profiles."""

    def __init__(self, database_path: Path) -> None:
        """Initialise the store at an explicit local SQLite path."""

        self.database_path = Path(database_path)
        self.ready = False
        self.error: str | None = None
        self.initialize()

    def _connect(self) -> sqlite3.Connection:
        """Open one short-lived SQLite connection with a bounded lock wait."""

        connection = sqlite3.connect(self.database_path, timeout=5.0)
        return connection

    @staticmethod
    def _purge_expired_contexts(
        connection: sqlite3.Connection,
        now: datetime,
    ) -> None:
        """Delete expired transient contexts while retaining audit feedback."""

        connection.execute(
            "DELETE FROM assessment_contexts WHERE expires_at <= ?",
            (now.isoformat(),),
        )

    def _get_context(
        self,
        connection: sqlite3.Connection,
        assessment_id: str,
        now: datetime,
    ) -> AssessmentContext | None:
        """Load one unexpired assessment context within the caller transaction."""

        self._purge_expired_contexts(connection, now)
        row = connection.execute(
            """
            SELECT model_version, recommendation
            FROM assessment_contexts
            WHERE assessment_reference = ?
            """,
            (assessment_id,),
        ).fetchone()
        if row is None:
            return None
        return AssessmentContext(model_version=str(row[0]), recommendation=str(row[1]))

    def initialize(self) -> None:
        """Create the minimal feedback tables and publish store readiness."""

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
                    CREATE TABLE IF NOT EXISTS follow_up_records (
                        assessment_reference TEXT PRIMARY KEY,
                        model_version TEXT NOT NULL,
                        follow_up_status TEXT NOT NULL,
                        reason TEXT NOT NULL,
                        timestamp TEXT NOT NULL
                    );
                    CREATE TABLE IF NOT EXISTS assessment_contexts (
                        assessment_reference TEXT PRIMARY KEY,
                        model_version TEXT NOT NULL,
                        recommendation TEXT NOT NULL,
                        created_at TEXT NOT NULL,
                        expires_at TEXT NOT NULL
                    );
                    CREATE INDEX IF NOT EXISTS idx_assessment_context_expiry
                    ON assessment_contexts(expires_at);
                    """
                )
                self._purge_expired_contexts(
                    connection,
                    datetime.now(timezone.utc),
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
        """Persist expiring model context needed for a later human action."""

        if not self.ready:
            raise StoreUnavailableError(self.error or "Feedback store is unavailable.")
        now = datetime.now(timezone.utc)
        expires_at = now + ASSESSMENT_CONTEXT_TTL
        try:
            with self._connect() as connection:
                self._purge_expired_contexts(connection, now)
                connection.execute(
                    """
                    INSERT INTO assessment_contexts
                        (assessment_reference, model_version, recommendation,
                         created_at, expires_at)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        assessment_id,
                        model_id,
                        recommendation,
                        now.isoformat(),
                        expires_at.isoformat(),
                    ),
                )
        except sqlite3.Error as exc:
            raise StoreUnavailableError("Assessment context could not be recorded.") from exc

    def record_decision(
        self,
        assessment_id: str,
        analyst_decision: str,
        reason: str,
    ) -> None:
        """Persist one final analyst decision without storing raw profile data."""

        if not self.ready:
            raise StoreUnavailableError(self.error or "Feedback store is unavailable.")
        now = datetime.now(timezone.utc)
        try:
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
                context = self._get_context(connection, assessment_id, now)
                if context is None:
                    raise AssessmentNotFoundError(assessment_id)
                connection.execute(
                    """
                    INSERT INTO decision_feedback
                        (assessment_reference, model_version, recommendation,
                         analyst_decision, reason, timestamp)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        assessment_id,
                        context.model_version,
                        context.recommendation,
                        analyst_decision,
                        reason,
                        now.isoformat(),
                    ),
                )
        except (AssessmentNotFoundError, DuplicateOverrideError):
            raise
        except sqlite3.IntegrityError as exc:
            raise DuplicateOverrideError(assessment_id) from exc
        except sqlite3.Error as exc:
            raise StoreUnavailableError("Decision feedback could not be recorded.") from exc

    def list_decisions(self) -> list[dict[str, str]]:
        """Return persisted decision records in reverse chronological order."""

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

    def set_follow_up(
        self,
        assessment_id: str,
        status: str,
        reason: str,
    ) -> None:
        """Create, update, or clear the follow-up flag for an assessment."""

        if not self.ready:
            raise StoreUnavailableError(self.error or "Feedback store is unavailable.")
        now = datetime.now(timezone.utc)
        try:
            with self._connect() as connection:
                context = self._get_context(connection, assessment_id, now)
                if context is None:
                    raise AssessmentNotFoundError(assessment_id)
                if status == "cleared":
                    connection.execute(
                        "DELETE FROM follow_up_records WHERE assessment_reference = ?",
                        (assessment_id,),
                    )
                    return
                connection.execute(
                    """
                    INSERT INTO follow_up_records
                        (assessment_reference, model_version, follow_up_status,
                         reason, timestamp)
                    VALUES (?, ?, ?, ?, ?)
                    ON CONFLICT(assessment_reference) DO UPDATE SET
                        follow_up_status = excluded.follow_up_status,
                        reason = excluded.reason,
                        timestamp = excluded.timestamp
                    """,
                    (
                        assessment_id,
                        context.model_version,
                        status,
                        reason,
                        now.isoformat(),
                    ),
                )
        except AssessmentNotFoundError:
            raise
        except sqlite3.Error as exc:
            raise StoreUnavailableError("Follow-up status could not be recorded.") from exc

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
