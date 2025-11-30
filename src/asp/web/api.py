"""
ASP Web UI API Layer

Provides data access functions for the web UI views.
Connects to the telemetry database to fetch real-time metrics.
"""

import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

# Database path (same as telemetry module)
DEFAULT_DB_PATH = Path(__file__).parent.parent.parent.parent / "data" / "asp_telemetry.db"


def get_db_connection(db_path: Optional[Path] = None):
    """Get a database connection."""
    db_path = db_path or DEFAULT_DB_PATH
    if not db_path.exists():
        return None
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    return conn


def get_recent_agent_activity(limit: int = 10) -> List[Dict[str, Any]]:
    """
    Get recent agent activity from telemetry.

    Returns list of recent agent executions with timing and status.
    """
    conn = get_db_connection()
    if not conn:
        return []

    try:
        cursor = conn.cursor()
        cursor.execute("""
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
        """, (limit,))

        results = []
        for row in cursor.fetchall():
            results.append({
                "timestamp": row["timestamp"],
                "task_id": row["task_id"],
                "agent_role": row["agent_role"],
                "latency_ms": row["metric_value"],
                "user_id": row["user_id"],
                "llm_model": row["llm_model"],
            })
        return results
    except sqlite3.Error:
        return []
    finally:
        conn.close()


def get_defect_summary() -> Dict[str, Any]:
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
        cursor.execute("""
            SELECT severity, COUNT(*) as count
            FROM defect_log
            GROUP BY severity
        """)
        by_severity = {row["severity"]: row["count"] for row in cursor.fetchall()}

        # By type
        cursor.execute("""
            SELECT defect_type, COUNT(*) as count
            FROM defect_log
            GROUP BY defect_type
            ORDER BY count DESC
            LIMIT 5
        """)
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


def get_cost_summary(days: int = 7) -> Dict[str, Any]:
    """
    Get API cost summary for the specified period.

    Returns total cost and breakdown by agent role.
    """
    conn = get_db_connection()
    if not conn:
        return {"total_usd": 0, "by_role": {}, "token_usage": {}}

    try:
        cursor = conn.cursor()
        cutoff = (datetime.utcnow() - timedelta(days=days)).isoformat()

        # Total cost
        cursor.execute("""
            SELECT COALESCE(SUM(metric_value), 0) as total
            FROM agent_cost_vector
            WHERE metric_type = 'API_Cost' AND timestamp > ?
        """, (cutoff,))
        total_usd = cursor.fetchone()["total"]

        # Cost by role
        cursor.execute("""
            SELECT agent_role, SUM(metric_value) as cost
            FROM agent_cost_vector
            WHERE metric_type = 'API_Cost' AND timestamp > ?
            GROUP BY agent_role
        """, (cutoff,))
        by_role = {row["agent_role"]: row["cost"] for row in cursor.fetchall()}

        # Token usage
        cursor.execute("""
            SELECT
                SUM(CASE WHEN metric_type = 'Tokens_In' THEN metric_value ELSE 0 END) as input_tokens,
                SUM(CASE WHEN metric_type = 'Tokens_Out' THEN metric_value ELSE 0 END) as output_tokens
            FROM agent_cost_vector
            WHERE timestamp > ?
        """, (cutoff,))
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


def get_user_performance(user_id: Optional[str] = None) -> List[Dict[str, Any]]:
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
            results.append({
                "user_id": row["user_id"],
                "task_count": row["task_count"],
                "avg_latency_ms": round(row["avg_latency"] or 0, 2),
                "execution_count": row["execution_count"],
            })
        return results
    except sqlite3.Error:
        return []
    finally:
        conn.close()


def get_tasks_pending_approval() -> List[Dict[str, Any]]:
    """
    Get tasks that are pending approval (stub for HITL workflow).

    TODO: Connect to actual approval system when implemented.
    """
    # Placeholder - would connect to approval workflow
    return [
        {"task_id": "TSP-001", "title": "Implement User Authentication", "status": "pending_review"},
        {"task_id": "TSP-002", "title": "Add API Rate Limiting", "status": "pending_approval"},
    ]


def get_project_progress() -> Dict[str, Any]:
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
            "in_progress": 2,    # Placeholder
            "total": total + 2,
        }
    except sqlite3.Error:
        return {"completed": 0, "in_progress": 0, "total": 0}
    finally:
        conn.close()
