"""
ASP Web UI API Layer

Provides data access functions for the web UI views.
Connects to the telemetry database to fetch real-time metrics.
"""

# pylint: disable=logging-fstring-interpolation

import contextlib
import json
import logging
import sqlite3
import subprocess
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# Database path (same as telemetry module)
DEFAULT_DB_PATH = (
    Path(__file__).parent.parent.parent.parent / "data" / "asp_telemetry.db"
)

# Artifacts path for PIP files
DEFAULT_ARTIFACTS_PATH = Path(__file__).parent.parent.parent.parent / "artifacts"


def get_db_connection(db_path: Path | None = None):
    """Get a database connection."""
    db_path = db_path or DEFAULT_DB_PATH
    if not db_path.exists():
        return None
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    return conn


def get_recent_agent_activity(limit: int = 10) -> list[dict[str, Any]]:
    """
    Get recent agent activity from telemetry.

    Returns list of recent agent executions with timing and status.
    """
    conn = get_db_connection()
    if not conn:
        return []

    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT
                timestamp,
                task_id,
                agent_role,
                metric_type,
                metric_value,
                metric_unit,
                user_id,
                llm_model
            FROM agent_cost_vector
            WHERE metric_type = 'Latency'
            ORDER BY timestamp DESC
            LIMIT ?
        """,
            (limit,),
        )

        results = []
        for row in cursor.fetchall():
            results.append(
                {
                    "timestamp": row["timestamp"],
                    "task_id": row["task_id"],
                    "agent_role": row["agent_role"],
                    "latency_ms": row["metric_value"],
                    "user_id": row["user_id"],
                    "llm_model": row["llm_model"],
                }
            )
        return results
    except sqlite3.Error:
        return []
    finally:
        conn.close()


def get_defect_summary() -> dict[str, Any]:
    """
    Get defect summary statistics.

    Returns counts by severity and type.
    """
    conn = get_db_connection()
    if not conn:
        return {"total": 0, "by_severity": {}, "by_type": {}}

    try:
        cursor = conn.cursor()

        # Total defects
        cursor.execute("SELECT COUNT(*) as total FROM defect_log")
        total = cursor.fetchone()["total"]

        # By severity
        cursor.execute(
            """
            SELECT severity, COUNT(*) as count
            FROM defect_log
            GROUP BY severity
        """
        )
        by_severity = {row["severity"]: row["count"] for row in cursor.fetchall()}

        # By type
        cursor.execute(
            """
            SELECT defect_type, COUNT(*) as count
            FROM defect_log
            GROUP BY defect_type
            ORDER BY count DESC
            LIMIT 5
        """
        )
        by_type = {row["defect_type"]: row["count"] for row in cursor.fetchall()}

        return {
            "total": total,
            "by_severity": by_severity,
            "by_type": by_type,
        }
    except sqlite3.Error:
        return {"total": 0, "by_severity": {}, "by_type": {}}
    finally:
        conn.close()


def get_cost_summary(days: int = 7) -> dict[str, Any]:
    """
    Get API cost summary for the specified period.

    Returns total cost and breakdown by agent role.
    """
    conn = get_db_connection()
    if not conn:
        return {"total_usd": 0, "by_role": {}, "token_usage": {}}

    try:
        cursor = conn.cursor()
        cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()

        # Total cost
        cursor.execute(
            """
            SELECT COALESCE(SUM(metric_value), 0) as total
            FROM agent_cost_vector
            WHERE metric_type = 'API_Cost' AND timestamp > ?
        """,
            (cutoff,),
        )
        total_usd = cursor.fetchone()["total"]

        # Cost by role
        cursor.execute(
            """
            SELECT agent_role, SUM(metric_value) as cost
            FROM agent_cost_vector
            WHERE metric_type = 'API_Cost' AND timestamp > ?
            GROUP BY agent_role
        """,
            (cutoff,),
        )
        by_role = {row["agent_role"]: row["cost"] for row in cursor.fetchall()}

        # Token usage
        cursor.execute(
            """
            SELECT
                SUM(CASE WHEN metric_type = 'Tokens_In' THEN metric_value ELSE 0 END) as input_tokens,
                SUM(CASE WHEN metric_type = 'Tokens_Out' THEN metric_value ELSE 0 END) as output_tokens
            FROM agent_cost_vector
            WHERE timestamp > ?
        """,
            (cutoff,),
        )
        row = cursor.fetchone()
        token_usage = {
            "input": int(row["input_tokens"] or 0),
            "output": int(row["output_tokens"] or 0),
        }

        return {
            "total_usd": round(total_usd, 4),
            "by_role": by_role,
            "token_usage": token_usage,
        }
    except sqlite3.Error:
        return {"total_usd": 0, "by_role": {}, "token_usage": {}}
    finally:
        conn.close()


def get_user_performance(user_id: str | None = None) -> list[dict[str, Any]]:
    """
    Get performance metrics grouped by user.

    Returns latency and task counts per user.
    """
    conn = get_db_connection()
    if not conn:
        return []

    try:
        cursor = conn.cursor()

        query = """
            SELECT
                user_id,
                COUNT(DISTINCT task_id) as task_count,
                AVG(CASE WHEN metric_type = 'Latency' THEN metric_value END) as avg_latency,
                COUNT(*) as execution_count
            FROM agent_cost_vector
            WHERE user_id IS NOT NULL
        """
        params = []

        if user_id:
            query += " AND user_id = ?"
            params.append(user_id)

        query += " GROUP BY user_id ORDER BY task_count DESC LIMIT 10"

        cursor.execute(query, params)

        results = []
        for row in cursor.fetchall():
            results.append(
                {
                    "user_id": row["user_id"],
                    "task_count": row["task_count"],
                    "avg_latency_ms": round(row["avg_latency"] or 0, 2),
                    "execution_count": row["execution_count"],
                }
            )
        return results
    except sqlite3.Error:
        return []
    finally:
        conn.close()


def get_tasks_pending_approval(
    artifacts_path: Path | None = None,
) -> list[dict[str, Any]]:
    """
    Get tasks that are pending HITL approval.

    Checks two sources:
    1. PIP (Process Improvement Proposal) artifacts with hitl_status="pending"
    2. Git review branches (pattern: review/{task_id}-{gate_type})

    Args:
        artifacts_path: Optional path to artifacts directory

    Returns:
        List of pending approval items with task_id, title, status, and type
    """
    pending_items: list[dict[str, Any]] = []
    artifacts_dir = artifacts_path or DEFAULT_ARTIFACTS_PATH

    # 1. Check for pending PIPs in artifacts
    pending_items.extend(_get_pending_pips(artifacts_dir))

    # 2. Check for pending review branches
    pending_items.extend(_get_pending_review_branches())

    return pending_items


def _get_pending_pips(artifacts_dir: Path) -> list[dict[str, Any]]:
    """
    Find PIPs with hitl_status="pending" in artifacts directory.

    Args:
        artifacts_dir: Path to artifacts directory

    Returns:
        List of pending PIP items
    """
    pending_pips: list[dict[str, Any]] = []

    if not artifacts_dir.exists():
        return pending_pips

    for task_dir in artifacts_dir.iterdir():
        if not task_dir.is_dir():
            continue

        pip_file = task_dir / "pip.json"
        if not pip_file.exists():
            continue

        try:
            with open(pip_file) as f:
                pip_data = json.load(f)

            if pip_data.get("hitl_status") == "pending":
                # Extract useful info for display
                analysis = pip_data.get("analysis", "No analysis available")
                # Truncate long analysis for display
                if len(analysis) > 100:
                    analysis = analysis[:97] + "..."

                pending_pips.append(
                    {
                        "task_id": task_dir.name,
                        "title": f"PIP: {analysis}",
                        "status": "pending_review",
                        "type": "pip",
                        "proposal_id": pip_data.get("proposal_id"),
                        "created_at": pip_data.get("created_at"),
                        "expected_impact": pip_data.get("expected_impact"),
                    }
                )
        except (json.JSONDecodeError, OSError) as e:
            logger.warning(f"Failed to read PIP from {pip_file}: {e}")

    return pending_pips


def _get_pending_review_branches() -> list[dict[str, Any]]:
    """
    Find git branches matching review/* pattern (quality gate reviews).

    Returns:
        List of pending review branch items
    """
    pending_reviews: list[dict[str, Any]] = []

    try:
        # Get all branches matching review/* pattern
        result = subprocess.run(
            ["git", "branch", "-a", "--list", "*review/*"],
            capture_output=True,
            text=True,
            timeout=5,
            check=False,  # We handle non-zero exit codes manually
        )

        if result.returncode != 0:
            return pending_reviews

        for line in result.stdout.strip().split("\n"):
            if not line.strip():
                continue

            branch_name = line.strip().lstrip("* ").replace("remotes/origin/", "")

            # Skip if already processed (avoid duplicates from local+remote)
            if any(r["branch"] == branch_name for r in pending_reviews):
                continue

            # Parse branch name: review/{task_id}-{gate_type}
            if branch_name.startswith("review/"):
                parts = branch_name[7:].rsplit("-", 1)  # Split from right
                if len(parts) == 2:
                    task_id, gate_type = parts
                else:
                    task_id = parts[0]
                    gate_type = "unknown"

                pending_reviews.append(
                    {
                        "task_id": task_id,
                        "title": f"Quality Gate: {gate_type.replace('_', ' ').title()}",
                        "status": "pending_approval",
                        "type": "quality_gate",
                        "gate_type": gate_type,
                        "branch": branch_name,
                    }
                )
    except (subprocess.TimeoutExpired, subprocess.SubprocessError) as e:
        logger.warning(f"Failed to get review branches: {e}")

    return pending_reviews


def get_pip_details(
    task_id: str, artifacts_path: Path | None = None
) -> dict[str, Any] | None:
    """
    Get full details of a PIP by task ID.

    Args:
        task_id: Task ID to look up
        artifacts_path: Optional path to artifacts directory

    Returns:
        Full PIP data or None if not found
    """
    artifacts_dir = artifacts_path or DEFAULT_ARTIFACTS_PATH
    pip_file = artifacts_dir / task_id / "pip.json"

    if not pip_file.exists():
        return None

    try:
        with open(pip_file) as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError) as e:
        logger.warning(f"Failed to read PIP {task_id}: {e}")
        return None


def get_project_progress() -> dict[str, Any]:
    """
    Get overall project progress metrics.

    Returns task completion stats.
    """
    conn = get_db_connection()
    if not conn:
        return {"completed": 0, "in_progress": 0, "total": 0}

    try:
        cursor = conn.cursor()

        # Count distinct tasks
        cursor.execute("SELECT COUNT(DISTINCT task_id) as total FROM agent_cost_vector")
        total = cursor.fetchone()["total"]

        return {
            "completed": total,  # All tracked tasks have executed
            "in_progress": 2,  # Placeholder
            "total": total + 2,
        }
    except sqlite3.Error:
        return {"completed": 0, "in_progress": 0, "total": 0}
    finally:
        conn.close()


# =============================================================================
# HITL Approval API (Inter-container communication)
# =============================================================================


def get_pending_approval_requests(task_id: str | None = None) -> list[dict[str, Any]]:
    """
    Get pending HITL approval requests from database.

    This is used by the WebUI to display pending requests from agent-runner.

    Args:
        task_id: Optional filter by task ID

    Returns:
        List of pending approval request dictionaries
    """
    conn = get_db_connection()
    if not conn:
        return []

    try:
        cursor = conn.cursor()

        # Check if approval_requests table exists
        cursor.execute(
            """
            SELECT name FROM sqlite_master
            WHERE type='table' AND name='approval_requests'
            """
        )
        if not cursor.fetchone():
            return []

        if task_id:
            cursor.execute(
                """
                SELECT * FROM approval_requests
                WHERE status = 'pending' AND task_id = ?
                ORDER BY requested_at DESC
                """,
                (task_id,),
            )
        else:
            cursor.execute(
                """
                SELECT * FROM approval_requests
                WHERE status = 'pending'
                ORDER BY requested_at DESC
                """
            )

        return [dict(row) for row in cursor.fetchall()]
    except sqlite3.Error as e:
        logger.warning(f"Failed to get pending approval requests: {e}")
        return []
    finally:
        conn.close()


def get_approval_request_details(request_id: str) -> dict[str, Any] | None:
    """
    Get full details of an approval request.

    Args:
        request_id: The approval request ID

    Returns:
        Full request data or None if not found
    """
    conn = get_db_connection()
    if not conn:
        return None

    try:
        cursor = conn.cursor()

        cursor.execute(
            "SELECT * FROM approval_requests WHERE request_id = ?",
            (request_id,),
        )
        row = cursor.fetchone()

        if row:
            result = dict(row)
            # Parse JSON quality_report - keep as string if invalid JSON
            if result.get("quality_report"):
                with contextlib.suppress(json.JSONDecodeError):
                    result["quality_report"] = json.loads(result["quality_report"])
            return result
        return None
    except sqlite3.Error as e:
        logger.warning(f"Failed to get approval request {request_id}: {e}")
        return None
    finally:
        conn.close()


def submit_approval_decision(
    request_id: str,
    decision: str,
    reviewer: str,
    justification: str,
) -> dict[str, Any]:
    """
    Submit an approval decision for a pending request.

    This is called when a user approves/rejects via the WebUI.

    Args:
        request_id: The approval request ID
        decision: 'approved', 'rejected', or 'deferred'
        reviewer: Username/email of reviewer
        justification: Reason for decision

    Returns:
        Result dictionary with success status and message
    """
    # Validate inputs
    error = _validate_decision_inputs(decision, justification)
    if error:
        return {"success": False, "error": error}

    conn = get_db_connection()
    if not conn:
        return {"success": False, "error": "Database not available"}

    try:
        cursor = conn.cursor()

        # Verify request exists and is pending
        error = _validate_request_status(cursor, request_id)
        if error:
            return {"success": False, "error": error}

        # Insert decision and update status
        cursor.execute(
            """
            INSERT INTO approval_decisions (
                request_id, decision, reviewer, justification
            ) VALUES (?, ?, ?, ?)
            """,
            (request_id, decision, reviewer, justification),
        )
        cursor.execute(
            "UPDATE approval_requests SET status = ? WHERE request_id = ?",
            (decision, request_id),
        )
        conn.commit()

        logger.info(f"Approval decision: {request_id} -> {decision} by {reviewer}")
        return {"success": True, "message": f"Decision recorded: {decision}"}

    except sqlite3.Error as e:
        logger.error(f"Failed to submit approval decision: {e}")
        return {"success": False, "error": str(e)}
    finally:
        conn.close()


def _validate_decision_inputs(decision: str, justification: str) -> str | None:
    """Validate decision inputs, return error message or None if valid."""
    if decision not in ("approved", "rejected", "deferred"):
        return "Invalid decision"
    if not justification.strip():
        return "Justification required"
    return None


def _validate_request_status(cursor, request_id: str) -> str | None:
    """Validate request exists and is pending, return error message or None."""
    cursor.execute(
        "SELECT status FROM approval_requests WHERE request_id = ?",
        (request_id,),
    )
    row = cursor.fetchone()
    if not row:
        return "Request not found"
    if row["status"] != "pending":
        return f"Request not pending: {row['status']}"
    return None


def get_approval_history(
    task_id: str | None = None, limit: int = 20
) -> list[dict[str, Any]]:
    """
    Get history of approval decisions.

    Args:
        task_id: Optional filter by task ID
        limit: Maximum number of records to return

    Returns:
        List of approval decision records
    """
    conn = get_db_connection()
    if not conn:
        return []

    try:
        cursor = conn.cursor()

        # Check if tables exist
        cursor.execute(
            """
            SELECT name FROM sqlite_master
            WHERE type='table' AND name='approval_decisions'
            """
        )
        if not cursor.fetchone():
            return []

        if task_id:
            cursor.execute(
                """
                SELECT
                    d.request_id,
                    d.decision,
                    d.reviewer,
                    d.decided_at,
                    d.justification,
                    r.task_id,
                    r.gate_type,
                    r.gate_name,
                    r.summary
                FROM approval_decisions d
                JOIN approval_requests r ON d.request_id = r.request_id
                WHERE r.task_id = ?
                ORDER BY d.decided_at DESC
                LIMIT ?
                """,
                (task_id, limit),
            )
        else:
            cursor.execute(
                """
                SELECT
                    d.request_id,
                    d.decision,
                    d.reviewer,
                    d.decided_at,
                    d.justification,
                    r.task_id,
                    r.gate_type,
                    r.gate_name,
                    r.summary
                FROM approval_decisions d
                JOIN approval_requests r ON d.request_id = r.request_id
                ORDER BY d.decided_at DESC
                LIMIT ?
                """,
                (limit,),
            )

        return [dict(row) for row in cursor.fetchall()]
    except sqlite3.Error as e:
        logger.warning(f"Failed to get approval history: {e}")
        return []
    finally:
        conn.close()
