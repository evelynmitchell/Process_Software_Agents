"""
Data Access Layer for ASP Web UI

Provides functions to fetch tasks, telemetry, and artifacts for display in the web interface.
Integrates data from:
- Bootstrap results (JSON files)
- Telemetry database (SQLite)
- Artifact directories
"""

import json
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

# Paths relative to project root
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data"
ARTIFACTS_DIR = PROJECT_ROOT / "artifacts"
BOOTSTRAP_RESULTS = DATA_DIR / "bootstrap_results.json"
BOOTSTRAP_DESIGN_RESULTS = DATA_DIR / "bootstrap_design_review_results.json"
TELEMETRY_DB = DATA_DIR / "asp_telemetry.db"


def _get_db_connection() -> sqlite3.Connection | None:
    """Get a database connection to the telemetry DB."""
    if not TELEMETRY_DB.exists():
        return None
    conn = sqlite3.connect(str(TELEMETRY_DB))
    conn.row_factory = sqlite3.Row
    return conn


def get_tasks() -> list[dict[str, Any]]:
    """
    Get all tasks from bootstrap results and telemetry.

    Returns:
        List of task dictionaries with id, description, complexity, status
    """
    tasks = []

    # Load bootstrap results if available
    if BOOTSTRAP_RESULTS.exists():
        with open(BOOTSTRAP_RESULTS) as f:
            data = json.load(f)
            for result in data.get("results", []):
                tasks.append(
                    {
                        "task_id": result.get("task_id", "Unknown"),
                        "description": result.get("description", "No description"),
                        "complexity": result.get("actual_total_complexity", 0),
                        "num_units": result.get("num_units", 0),
                        "execution_time": result.get("execution_time_seconds", 0),
                        "status": "completed" if result.get("success") else "failed",
                    }
                )

    # Also check artifacts directory for additional tasks
    if ARTIFACTS_DIR.exists():
        existing_ids = {t["task_id"] for t in tasks}
        for task_dir in ARTIFACTS_DIR.iterdir():
            if task_dir.is_dir() and task_dir.name not in existing_ids:
                # Check for plan.md to determine status
                has_plan = (task_dir / "plan.md").exists()
                has_design = (task_dir / "design.md").exists()
                has_code = (task_dir / "code").exists() or any(task_dir.glob("*.py"))

                status = (
                    "completed"
                    if has_code
                    else ("in_progress" if has_design else "planning")
                )

                tasks.append(
                    {
                        "task_id": task_dir.name,
                        "description": f"Task {task_dir.name}",
                        "complexity": 0,
                        "num_units": 0,
                        "execution_time": 0,
                        "status": status,
                    }
                )

    return sorted(tasks, key=lambda x: x["task_id"])


def get_task_details(task_id: str) -> dict[str, Any] | None:
    """
    Get detailed information about a specific task.

    Args:
        task_id: The task identifier

    Returns:
        Task details dictionary or None if not found
    """
    task_dir = ARTIFACTS_DIR / task_id
    if not task_dir.exists():
        return None

    details = {
        "task_id": task_id,
        "artifacts": [],
        "plan": None,
        "design": None,
        "telemetry": None,
    }

    # List all artifacts
    for artifact in task_dir.iterdir():
        details["artifacts"].append(
            {
                "name": artifact.name,
                "type": "directory" if artifact.is_dir() else "file",
                "size": artifact.stat().st_size if artifact.is_file() else 0,
            }
        )

    # Load plan if exists
    plan_file = task_dir / "plan.md"
    if plan_file.exists():
        details["plan"] = plan_file.read_text()[:1000]  # First 1000 chars

    # Load design if exists
    design_file = task_dir / "design.md"
    if design_file.exists():
        details["design"] = design_file.read_text()[:1000]

    # Get telemetry data for this task
    details["telemetry"] = get_task_telemetry(task_id)

    return details


def get_task_telemetry(task_id: str) -> dict[str, Any] | None:
    """Get telemetry data for a specific task from the database."""
    conn = _get_db_connection()
    if not conn:
        return None

    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT
                agent_role,
                metric_type,
                metric_value,
                metric_unit,
                timestamp
            FROM agent_cost_vector
            WHERE task_id = ?
            ORDER BY timestamp DESC
            """,
            (task_id,),
        )

        rows = cursor.fetchall()
        if not rows:
            return None

        # Aggregate metrics
        metrics = {
            "total_latency_ms": 0,
            "total_tokens_in": 0,
            "total_tokens_out": 0,
            "total_cost_usd": 0,
            "agent_calls": [],
        }

        for row in rows:
            if row["metric_type"] == "Latency":
                metrics["total_latency_ms"] += row["metric_value"]
            elif row["metric_type"] == "Tokens_In":
                metrics["total_tokens_in"] += int(row["metric_value"])
            elif row["metric_type"] == "Tokens_Out":
                metrics["total_tokens_out"] += int(row["metric_value"])
            elif row["metric_type"] == "API_Cost":
                metrics["total_cost_usd"] += row["metric_value"]

            metrics["agent_calls"].append(
                {
                    "agent": row["agent_role"],
                    "metric": row["metric_type"],
                    "value": row["metric_value"],
                    "unit": row["metric_unit"],
                    "timestamp": row["timestamp"],
                }
            )

        return metrics
    except sqlite3.Error:
        return None
    finally:
        conn.close()


def get_recent_activity(limit: int = 10) -> list[dict[str, Any]]:
    """
    Get recent activity from the system (telemetry + artifacts).

    Returns:
        List of recent activities with timestamp, action, and status
    """
    activities = []

    # First, try to get activity from telemetry database
    conn = _get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT
                    timestamp,
                    task_id,
                    agent_role,
                    metric_type,
                    metric_value
                FROM agent_cost_vector
                WHERE metric_type = 'Latency'
                ORDER BY timestamp DESC
                LIMIT ?
                """,
                (limit,),
            )

            for row in cursor.fetchall():
                try:
                    ts = datetime.fromisoformat(row["timestamp"].replace("Z", "+00:00"))
                except (ValueError, AttributeError):
                    ts = datetime.now()

                activities.append(
                    {
                        "time": ts.strftime("%H:%M"),
                        "date": ts.strftime("%Y-%m-%d"),
                        "action": f"{row['agent_role']} executed for {row['task_id']}",
                        "status": "Success",
                        "task_id": row["task_id"],
                        "agent": row["agent_role"],
                        "metric": f"{row['metric_value']:.0f}ms",
                    }
                )
        except sqlite3.Error:
            pass
        finally:
            conn.close()

    # If no telemetry data, fall back to artifact modification times
    if not activities and ARTIFACTS_DIR.exists():
        artifact_times = []
        for task_dir in ARTIFACTS_DIR.iterdir():
            if task_dir.is_dir():
                for artifact in task_dir.iterdir():
                    if artifact.is_file():
                        artifact_times.append(
                            {
                                "path": artifact,
                                "task_id": task_dir.name,
                                "name": artifact.name,
                                "mtime": artifact.stat().st_mtime,
                            }
                        )

        # Sort by modification time, most recent first
        artifact_times.sort(key=lambda x: x["mtime"], reverse=True)

        for item in artifact_times[:limit]:
            mtime = datetime.fromtimestamp(item["mtime"])
            activities.append(
                {
                    "time": mtime.strftime("%H:%M"),
                    "date": mtime.strftime("%Y-%m-%d"),
                    "action": f"Updated {item['name']} in {item['task_id']}",
                    "status": "Success",
                    "task_id": item["task_id"],
                }
            )

    return activities


def get_agent_stats() -> dict[str, Any]:
    """
    Get aggregate statistics about agent performance.

    Returns:
        Dictionary with total tasks, success rate, avg complexity, etc.
    """
    stats = {
        "total_tasks": 0,
        "successful": 0,
        "failed": 0,
        "avg_complexity": 0,
        "avg_execution_time": 0,
        "total_units": 0,
        "total_cost_usd": 0,
        "total_tokens": 0,
    }

    if BOOTSTRAP_RESULTS.exists():
        with open(BOOTSTRAP_RESULTS) as f:
            data = json.load(f)
            stats["total_tasks"] = data.get("total_tasks", 0)
            stats["successful"] = data.get("successful", 0)
            stats["failed"] = data.get("failed", 0)

            results = data.get("results", [])
            if results:
                complexities = [r.get("actual_total_complexity", 0) for r in results]
                times = [r.get("execution_time_seconds", 0) for r in results]
                units = [r.get("num_units", 0) for r in results]

                stats["avg_complexity"] = sum(complexities) / len(complexities)
                stats["avg_execution_time"] = sum(times) / len(times)
                stats["total_units"] = sum(units)

    # Augment with telemetry data
    conn = _get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()

            # Get total cost
            cursor.execute(
                """
                SELECT COALESCE(SUM(metric_value), 0) as total
                FROM agent_cost_vector
                WHERE metric_type = 'API_Cost'
                """
            )
            stats["total_cost_usd"] = round(cursor.fetchone()["total"], 4)

            # Get total tokens
            cursor.execute(
                """
                SELECT COALESCE(SUM(metric_value), 0) as total
                FROM agent_cost_vector
                WHERE metric_type IN ('Tokens_In', 'Tokens_Out')
                """
            )
            stats["total_tokens"] = int(cursor.fetchone()["total"])

        except sqlite3.Error:
            pass
        finally:
            conn.close()

    return stats


def get_agent_health() -> list[dict[str, Any]]:
    """
    Get health status for all ASP agents.

    Returns:
        List of agent status dictionaries with name, status, and last_active
    """
    # Define all 7 core agents
    agents = [
        "Planning Agent",
        "Design Agent",
        "Design Review",
        "Code Agent",
        "Code Review",
        "Test Agent",
        "Postmortem Agent",
    ]

    # Get last execution timestamp from bootstrap results
    last_active = "Never"
    status = "Idle"

    if BOOTSTRAP_RESULTS.exists():
        with open(BOOTSTRAP_RESULTS) as f:
            data = json.load(f)
            timestamp = data.get("timestamp", "")
            if timestamp:
                # Parse ISO timestamp and format for display
                from datetime import datetime

                try:
                    dt = datetime.fromisoformat(timestamp)
                    last_active = dt.strftime("%Y-%m-%d %H:%M")
                    status = "Operational"
                except ValueError:
                    last_active = timestamp[:16]  # Fallback: first 16 chars
                    status = "Operational"

    # All agents share the same status based on bootstrap run
    return [
        {"name": agent, "status": status, "last_active": last_active}
        for agent in agents
    ]


def get_design_review_stats() -> dict[str, Any]:
    """
    Get design review statistics from bootstrap data and defect log.

    Returns:
        Dictionary with review counts, pass/fail rates, defect counts
    """
    stats = {
        "total_reviews": 0,
        "passed": 0,
        "failed": 0,
        "needs_improvement": 0,
        "total_defects": 0,
        "by_category": {},
    }

    if BOOTSTRAP_DESIGN_RESULTS.exists():
        with open(BOOTSTRAP_DESIGN_RESULTS) as f:
            data = json.load(f)
            results = data.get("results", [])
            stats["total_reviews"] = len(results)

            for result in results:
                verdict = result.get("verdict", "").upper()
                if verdict == "PASS":
                    stats["passed"] += 1
                elif verdict == "FAIL":
                    stats["failed"] += 1
                else:
                    stats["needs_improvement"] += 1

                # Count defects
                for finding in result.get("findings", []):
                    stats["total_defects"] += 1
                    category = finding.get("category", "Unknown")
                    stats["by_category"][category] = (
                        stats["by_category"].get(category, 0) + 1
                    )

    # Also check defect_log table
    conn = _get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) as total FROM defect_log")
            db_defects = cursor.fetchone()["total"]
            if db_defects > stats["total_defects"]:
                stats["total_defects"] = db_defects

            # Get defects by type from DB
            cursor.execute(
                """
                SELECT defect_type, COUNT(*) as count
                FROM defect_log
                GROUP BY defect_type
                """
            )
            for row in cursor.fetchall():
                stats["by_category"][row["defect_type"]] = row["count"]
        except sqlite3.Error:
            pass
        finally:
            conn.close()

    return stats


def get_agent_health() -> list[dict[str, Any]]:
    """
    Get health status for all agents based on recent telemetry.

    Returns:
        List of agent status dictionaries
    """
    agents = [
        {"name": "Planning Agent", "role": "Planning"},
        {"name": "Design Agent", "role": "Design"},
        {"name": "Design Review", "role": "DesignReview"},
        {"name": "Code Agent", "role": "Code"},
        {"name": "Code Review", "role": "CodeReview"},
        {"name": "Test Agent", "role": "Test"},
        {"name": "Postmortem Agent", "role": "Postmortem"},
    ]

    conn = _get_db_connection()
    if not conn:
        # No telemetry - return default "Unknown" status
        return [
            {
                "name": a["name"],
                "status": "Unknown",
                "last_active": "No data",
                "executions": 0,
                "avg_latency": 0,
            }
            for a in agents
        ]

    try:
        cursor = conn.cursor()
        cutoff = (datetime.utcnow() - timedelta(hours=24)).isoformat()

        results = []
        for agent in agents:
            # Get last execution and stats for this agent
            cursor.execute(
                """
                SELECT
                    MAX(timestamp) as last_active,
                    COUNT(*) as executions,
                    AVG(CASE WHEN metric_type = 'Latency' THEN metric_value END) as avg_latency
                FROM agent_cost_vector
                WHERE agent_role = ?
                """,
                (agent["role"],),
            )
            row = cursor.fetchone()

            if row["last_active"]:
                try:
                    last_ts = datetime.fromisoformat(
                        row["last_active"].replace("Z", "+00:00")
                    )
                    # Determine status based on recency
                    age = datetime.utcnow() - last_ts.replace(tzinfo=None)
                    if age < timedelta(hours=1):
                        status = "Operational"
                    elif age < timedelta(days=1):
                        status = "Idle"
                    else:
                        status = "Inactive"

                    last_active_str = last_ts.strftime("%Y-%m-%d %H:%M")
                except (ValueError, AttributeError):
                    status = "Unknown"
                    last_active_str = "Unknown"
            else:
                status = "Never Run"
                last_active_str = "Never"

            results.append(
                {
                    "name": agent["name"],
                    "role": agent["role"],
                    "status": status,
                    "last_active": last_active_str,
                    "executions": row["executions"] or 0,
                    "avg_latency": round(row["avg_latency"] or 0, 0),
                }
            )

        return results
    except sqlite3.Error:
        return [
            {
                "name": a["name"],
                "status": "Error",
                "last_active": "DB Error",
                "executions": 0,
                "avg_latency": 0,
            }
            for a in agents
        ]
    finally:
        conn.close()


def get_cost_breakdown(days: int = 7) -> dict[str, Any]:
    """
    Get API cost breakdown for the specified period.

    Returns:
        Dictionary with total cost and breakdown by agent role
    """
    result = {"total_usd": 0, "by_role": {}, "token_usage": {"input": 0, "output": 0}}

    conn = _get_db_connection()
    if not conn:
        return result

    try:
        cursor = conn.cursor()
        cutoff = (datetime.utcnow() - timedelta(days=days)).isoformat()

        # Total cost
        cursor.execute(
            """
            SELECT COALESCE(SUM(metric_value), 0) as total
            FROM agent_cost_vector
            WHERE metric_type = 'API_Cost' AND timestamp > ?
            """,
            (cutoff,),
        )
        result["total_usd"] = round(cursor.fetchone()["total"], 4)

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
        result["by_role"] = {
            row["agent_role"]: row["cost"] for row in cursor.fetchall()
        }

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
        result["token_usage"] = {
            "input": int(row["input_tokens"] or 0),
            "output": int(row["output_tokens"] or 0),
        }

        return result
    except sqlite3.Error:
        return result
    finally:
        conn.close()
