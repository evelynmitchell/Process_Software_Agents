"""
Database-based HITL Approval Service for containerized deployments.

This service writes approval requests to a shared SQLite database, allowing
a separate webui container to display pending approvals and record decisions.
The agent-runner polls the database for decisions.
"""

# pylint: disable=logging-fstring-interpolation

import json
import logging
import sqlite3
import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path

from asp.approval.base import (
    ApprovalRequest,
    ApprovalResponse,
    ApprovalService,
    ReviewDecision,
)

logger = logging.getLogger(__name__)


@dataclass
class DecisionInput:
    """Input data for submitting an approval decision."""

    request_id: str
    decision: str
    reviewer: str
    justification: str
    review_branch: str | None = None
    merge_commit: str | None = None


class DatabaseApprovalService(ApprovalService):
    """
    Approval service that uses SQLite database for inter-container communication.

    Workflow:
    1. Agent-runner writes approval request to database
    2. Agent-runner polls database for decision
    3. WebUI displays pending requests
    4. User approves/rejects via WebUI
    5. WebUI writes decision to database
    6. Agent-runner detects decision, returns response
    """

    def __init__(
        self,
        db_path: str | Path = "data/asp_telemetry.db",
        poll_interval: float = 5.0,
        timeout: float = 3600.0,  # 1 hour default timeout
    ):
        """
        Initialize the database approval service.

        Args:
            db_path: Path to SQLite database
            poll_interval: Seconds between polls for decision
            timeout: Maximum seconds to wait for decision
        """
        self.db_path = Path(db_path)
        self.poll_interval = poll_interval
        self.timeout = timeout

    def _get_connection(self) -> sqlite3.Connection:
        """Get a database connection with row factory."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _ensure_tables_exist(self) -> None:
        """Create approval tables if they don't exist."""
        migration_path = (
            Path(__file__).parent.parent.parent.parent
            / "database"
            / "sqlite"
            / "007_add_approval_requests.sql"
        )

        if migration_path.exists():
            with self._get_connection() as conn:
                conn.executescript(migration_path.read_text())
        else:
            # Inline table creation as fallback
            with self._get_connection() as conn:
                conn.executescript(self._get_inline_schema())

    def _get_inline_schema(self) -> str:
        """Return inline schema for fallback table creation."""
        return """
            CREATE TABLE IF NOT EXISTS approval_requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                request_id TEXT UNIQUE NOT NULL,
                task_id TEXT NOT NULL,
                gate_type TEXT NOT NULL,
                gate_name TEXT NOT NULL,
                requested_at TEXT NOT NULL DEFAULT (datetime('now')),
                expires_at TEXT,
                quality_report TEXT NOT NULL,
                summary TEXT,
                critical_issues INTEGER DEFAULT 0,
                high_issues INTEGER DEFAULT 0,
                status TEXT NOT NULL DEFAULT 'pending',
                CHECK (status IN (
                    'pending', 'approved', 'rejected', 'deferred', 'expired'
                ))
            );

            CREATE TABLE IF NOT EXISTS approval_decisions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                request_id TEXT NOT NULL,
                decision TEXT NOT NULL,
                reviewer TEXT NOT NULL,
                decided_at TEXT NOT NULL DEFAULT (datetime('now')),
                justification TEXT NOT NULL,
                review_branch TEXT,
                merge_commit TEXT,
                CHECK (decision IN ('approved', 'rejected', 'deferred')),
                FOREIGN KEY (request_id) REFERENCES approval_requests(request_id)
            );

            CREATE INDEX IF NOT EXISTS idx_approval_requests_status
                ON approval_requests(status);
            CREATE INDEX IF NOT EXISTS idx_approval_requests_task
                ON approval_requests(task_id);
        """

    def _generate_request_id(self, task_id: str, gate_type: str) -> str:
        """Generate unique request ID."""
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        return f"{task_id}_{gate_type}_{timestamp}"

    def _extract_summary(self, request: ApprovalRequest) -> tuple[str, int, int]:
        """Extract human-readable summary and issue counts from quality report."""
        report = request.quality_report
        critical = 0
        high = 0
        summary_parts = []

        # Handle DesignReview reports
        if "critical_issue_count" in report:
            critical = report.get("critical_issue_count", 0)
            high = report.get("high_issue_count", 0)
            assessment = report.get("overall_assessment", "UNKNOWN")
            summary_parts.append(f"Design Review: {assessment}")
            if report.get("issues_found"):
                summary_parts.append(f"{len(report['issues_found'])} issues found")

        # Handle CodeReview reports
        if "critical_issues" in report:
            critical = report.get("critical_issues", 0)
            high = report.get("high_issues", 0)
            verdict = report.get("overall_verdict", "UNKNOWN")
            summary_parts.append(f"Code Review: {verdict}")

        summary = "; ".join(summary_parts) if summary_parts else "Quality gate failed"
        return summary, critical, high

    def _write_request(self, request: ApprovalRequest, request_id: str) -> None:
        """Write approval request to database."""
        summary, critical, high = self._extract_summary(request)
        expires_at = (datetime.now() + timedelta(seconds=self.timeout)).isoformat()

        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO approval_requests (
                    request_id, task_id, gate_type, gate_name,
                    quality_report, summary, critical_issues, high_issues,
                    expires_at, status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'pending')
                """,
                (
                    request_id,
                    request.task_id,
                    request.gate_type,
                    request.gate_type.replace("_", " ").title(),
                    json.dumps(request.quality_report),
                    summary,
                    critical,
                    high,
                    expires_at,
                ),
            )
            conn.commit()

        logger.info(f"Approval request written: {request_id}")

    def _poll_for_decision(self, request_id: str) -> ApprovalResponse | None:
        """Poll database for decision on request."""
        start_time = time.time()

        while (time.time() - start_time) < self.timeout:
            with self._get_connection() as conn:
                # Check for decision
                row = conn.execute(
                    """
                    SELECT d.decision, d.reviewer, d.decided_at,
                           d.justification, d.review_branch, d.merge_commit
                    FROM approval_decisions d
                    WHERE d.request_id = ?
                    ORDER BY d.decided_at DESC
                    LIMIT 1
                    """,
                    (request_id,),
                ).fetchone()

                if row:
                    return ApprovalResponse(
                        decision=ReviewDecision(row["decision"]),
                        reviewer=row["reviewer"],
                        timestamp=row["decided_at"],
                        justification=row["justification"],
                        review_branch=row["review_branch"],
                        merge_commit=row["merge_commit"],
                    )

                # Check if request expired
                req = conn.execute(
                    """SELECT status, expires_at FROM approval_requests
                    WHERE request_id = ?""",
                    (request_id,),
                ).fetchone()

                if req and req["status"] == "expired":
                    logger.warning(f"Approval request expired: {request_id}")
                    return None

                if req and req["expires_at"]:
                    expires = datetime.fromisoformat(req["expires_at"])
                    if datetime.now() > expires:
                        conn.execute(
                            """UPDATE approval_requests SET status = 'expired'
                            WHERE request_id = ?""",
                            (request_id,),
                        )
                        conn.commit()
                        logger.warning(f"Approval request expired: {request_id}")
                        return None

            logger.debug(f"Waiting for approval decision on {request_id}...")
            time.sleep(self.poll_interval)

        # Timeout
        logger.warning(f"Approval request timed out: {request_id}")
        with self._get_connection() as conn:
            conn.execute(
                """UPDATE approval_requests SET status = 'expired'
                WHERE request_id = ?""",
                (request_id,),
            )
            conn.commit()
        return None

    def request_approval(self, request: ApprovalRequest) -> ApprovalResponse:
        """
        Request human approval by writing to database and polling for decision.

        Args:
            request: ApprovalRequest containing task info and quality report

        Returns:
            ApprovalResponse with decision and metadata

        Raises:
            TimeoutError: If no decision received within timeout period
        """
        self._ensure_tables_exist()

        request_id = self._generate_request_id(request.task_id, request.gate_type)
        self._write_request(request, request_id)

        logger.info(
            f"Waiting for HITL approval via WebUI: {request_id} "
            f"(timeout: {self.timeout}s, poll: {self.poll_interval}s)"
        )

        response = self._poll_for_decision(request_id)

        if response is None:
            raise TimeoutError(
                f"No approval decision received for {request_id} "
                f"within {self.timeout} seconds"
            )

        return response

    def get_pending_requests(self, task_id: str | None = None) -> list[dict]:
        """
        Get pending approval requests (for WebUI).

        Args:
            task_id: Optional filter by task ID

        Returns:
            List of pending request dictionaries
        """
        self._ensure_tables_exist()

        with self._get_connection() as conn:
            if task_id:
                rows = conn.execute(
                    """
                    SELECT * FROM approval_requests
                    WHERE status = 'pending' AND task_id = ?
                    ORDER BY requested_at DESC
                    """,
                    (task_id,),
                ).fetchall()
            else:
                rows = conn.execute(
                    """
                    SELECT * FROM approval_requests
                    WHERE status = 'pending'
                    ORDER BY requested_at DESC
                    """
                ).fetchall()

        return [dict(row) for row in rows]

    def submit_decision(self, decision_input: DecisionInput) -> bool:
        """
        Submit approval decision (for WebUI).

        Args:
            decision_input: DecisionInput with request_id, decision, reviewer, etc.

        Returns:
            True if decision was recorded successfully
        """
        self._ensure_tables_exist()

        with self._get_connection() as conn:
            # Verify request exists and is pending
            req = conn.execute(
                "SELECT status FROM approval_requests WHERE request_id = ?",
                (decision_input.request_id,),
            ).fetchone()

            if not req:
                logger.error(f"Request not found: {decision_input.request_id}")
                return False

            if req["status"] != "pending":
                logger.error(
                    f"Request not pending: {decision_input.request_id} "
                    f"({req['status']})"
                )
                return False

            # Insert decision
            conn.execute(
                """
                INSERT INTO approval_decisions (
                    request_id, decision, reviewer, justification,
                    review_branch, merge_commit
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    decision_input.request_id,
                    decision_input.decision,
                    decision_input.reviewer,
                    decision_input.justification,
                    decision_input.review_branch,
                    decision_input.merge_commit,
                ),
            )

            # Update request status
            conn.execute(
                "UPDATE approval_requests SET status = ? WHERE request_id = ?",
                (decision_input.decision, decision_input.request_id),
            )
            conn.commit()

        logger.info(
            f"Decision recorded: {decision_input.request_id} -> "
            f"{decision_input.decision} by {decision_input.reviewer}"
        )
        return True
