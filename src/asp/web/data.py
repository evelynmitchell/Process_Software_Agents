"""
Data Access Layer for ASP Web UI

Provides functions to fetch tasks, telemetry, and artifacts for display in the web interface.
Integrates data from:
- Bootstrap results (JSON files)
- Telemetry database (SQLite)
- Artifact directories
"""

import contextlib
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


def get_artifact_history(task_id: str) -> list[dict[str, Any]]:
    """
    Get the artifact history for a task showing the development timeline.

    Args:
        task_id: The task identifier

    Returns:
        List of artifacts in chronological order with metadata
    """
    task_dir = ARTIFACTS_DIR / task_id
    if not task_dir.exists():
        return []

    artifacts = []
    phase_order = {
        "plan": 1,
        "design": 2,
        "review": 3,
        "code": 4,
        "test": 5,
        "postmortem": 6,
    }

    for artifact in task_dir.iterdir():
        if artifact.is_file():
            name = artifact.name.lower()
            mtime = artifact.stat().st_mtime
            mtime_dt = datetime.fromtimestamp(mtime)

            # Determine phase from filename
            phase = "unknown"
            for p in phase_order:
                if p in name:
                    phase = p
                    break

            # Determine version from filename
            version = 1
            if "_v" in name:
                with contextlib.suppress(ValueError, IndexError):
                    version = int(name.split("_v")[1].split(".")[0])

            # Read preview content for text files
            preview = None
            if artifact.suffix in (".md", ".txt", ".json", ".py"):
                try:
                    content = artifact.read_text()
                    preview = content[:200] + "..." if len(content) > 200 else content
                except OSError:
                    pass

            artifacts.append(
                {
                    "name": artifact.name,
                    "path": str(artifact.relative_to(PROJECT_ROOT)),
                    "phase": phase,
                    "phase_order": phase_order.get(phase, 99),
                    "version": version,
                    "size": artifact.stat().st_size,
                    "modified": mtime_dt.isoformat(),
                    "modified_display": mtime_dt.strftime("%Y-%m-%d %H:%M"),
                    "preview": preview,
                    "suffix": artifact.suffix,
                }
            )

    # Sort by phase order, then by version, then by modified time
    artifacts.sort(key=lambda x: (x["phase_order"], x["version"], x["modified"]))

    return artifacts


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


def get_daily_metrics(days: int = 7) -> dict[str, list[float]]:
    """
    Get daily aggregated metrics for sparkline charts.

    Args:
        days: Number of days of history to fetch

    Returns:
        Dictionary with lists of daily values for cost, tokens, tasks
    """
    result = {
        "dates": [],
        "cost": [],
        "tokens": [],
        "tasks": [],
    }

    conn = _get_db_connection()
    if not conn:
        # Return placeholder data when no telemetry available
        return _get_placeholder_metrics(days)

    try:
        cursor = conn.cursor()
        cutoff = (datetime.utcnow() - timedelta(days=days)).isoformat()

        # Get daily cost totals
        cursor.execute(
            """
            SELECT
                DATE(timestamp) as day,
                SUM(CASE WHEN metric_type = 'API_Cost' THEN metric_value ELSE 0 END) as cost,
                SUM(CASE WHEN metric_type IN ('Tokens_In', 'Tokens_Out') THEN metric_value ELSE 0 END) as tokens,
                COUNT(DISTINCT task_id) as tasks
            FROM agent_cost_vector
            WHERE timestamp > ?
            GROUP BY DATE(timestamp)
            ORDER BY day
            """,
            (cutoff,),
        )

        for row in cursor.fetchall():
            result["dates"].append(row["day"])
            result["cost"].append(row["cost"] or 0)
            result["tokens"].append(row["tokens"] or 0)
            result["tasks"].append(row["tasks"] or 0)

        # If no data, return placeholder
        if not result["dates"]:
            return _get_placeholder_metrics(days)

        return result
    except sqlite3.Error:
        return _get_placeholder_metrics(days)
    finally:
        conn.close()


def _get_placeholder_metrics(days: int) -> dict[str, list[float]]:
    """
    Generate placeholder metrics data for display when no real data exists.

    Args:
        days: Number of days to generate

    Returns:
        Dictionary with placeholder daily values
    """
    from datetime import date

    today = date.today()
    dates = [(today - timedelta(days=i)).isoformat() for i in range(days - 1, -1, -1)]

    # Generate realistic-looking placeholder data
    # Shows a gentle upward trend to indicate system activity
    return {
        "dates": dates,
        "cost": [0.0] * days,  # No cost when no data
        "tokens": [0] * days,  # No tokens when no data
        "tasks": [0] * days,  # No tasks when no data
    }


def generate_sparkline_svg(
    values: list[float],
    width: int = 80,
    height: int = 20,
    color: str = "#06b6d4",
    show_endpoint: bool = True,
) -> str:
    """
    Generate an inline SVG sparkline chart.

    Args:
        values: List of numeric values to plot
        width: SVG width in pixels
        height: SVG height in pixels
        color: Line color (CSS color)
        show_endpoint: Whether to show a dot at the last point

    Returns:
        SVG markup string
    """
    if not values or all(v == 0 for v in values):
        # Return empty placeholder when no data
        return f'<svg width="{width}" height="{height}" style="vertical-align: middle;"><text x="{width//2}" y="{height//2 + 4}" text-anchor="middle" fill="#666" font-size="10">No data</text></svg>'

    # Normalize values to fit in height
    min_val = min(values)
    max_val = max(values)
    val_range = max_val - min_val if max_val != min_val else 1

    # Calculate points with padding
    padding = 2
    usable_height = height - 2 * padding
    usable_width = width - 2 * padding

    points = []
    for i, val in enumerate(values):
        x = (
            padding + (i / (len(values) - 1)) * usable_width
            if len(values) > 1
            else width / 2
        )
        y = padding + usable_height - ((val - min_val) / val_range) * usable_height
        points.append(f"{x:.1f},{y:.1f}")

    path = f'M {" L ".join(points)}'

    # Build SVG
    svg_parts = [
        f'<svg width="{width}" height="{height}" style="vertical-align: middle;">',
        f'<path d="{path}" fill="none" stroke="{color}" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>',
    ]

    # Add endpoint dot
    if show_endpoint and points:
        last_x, last_y = points[-1].split(",")
        svg_parts.append(f'<circle cx="{last_x}" cy="{last_y}" r="2" fill="{color}"/>')

    svg_parts.append("</svg>")
    return "".join(svg_parts)


def get_budget_settings() -> dict[str, Any]:
    """
    Get budget cap settings from configuration.

    Returns:
        Dictionary with daily_limit, monthly_limit, alert_threshold
    """
    settings_file = DATA_DIR / "budget_settings.json"
    default_settings = {
        "daily_limit": 10.00,
        "monthly_limit": 100.00,
        "alert_threshold": 0.80,  # Alert at 80% of limit
        "enabled": True,
    }

    if settings_file.exists():
        try:
            with open(settings_file) as f:
                saved = json.load(f)
                return {**default_settings, **saved}
        except (json.JSONDecodeError, OSError):
            pass

    return default_settings


def save_budget_settings(settings: dict[str, Any]) -> bool:
    """
    Save budget cap settings to configuration file.

    Args:
        settings: Dictionary with budget settings

    Returns:
        True if saved successfully, False otherwise
    """
    settings_file = DATA_DIR / "budget_settings.json"

    try:
        # Ensure data directory exists
        DATA_DIR.mkdir(parents=True, exist_ok=True)

        with open(settings_file, "w") as f:
            json.dump(settings, f, indent=2)
        return True
    except OSError:
        return False


def get_budget_status(days: int = 7) -> dict[str, Any]:
    """
    Get current budget usage status.

    Args:
        days: Days to calculate for monthly projection

    Returns:
        Dictionary with current spend, limits, and status
    """
    settings = get_budget_settings()
    cost_data = get_cost_breakdown(days=1)
    monthly_cost = get_cost_breakdown(days=30)

    daily_spent = cost_data["total_usd"]
    monthly_spent = monthly_cost["total_usd"]

    daily_limit = settings["daily_limit"]
    monthly_limit = settings["monthly_limit"]
    alert_threshold = settings["alert_threshold"]

    # Calculate percentages
    daily_pct = (daily_spent / daily_limit * 100) if daily_limit > 0 else 0
    monthly_pct = (monthly_spent / monthly_limit * 100) if monthly_limit > 0 else 0

    # Determine status
    if daily_pct >= 100 or monthly_pct >= 100:
        status = "exceeded"
        status_color = "red"
    elif daily_pct >= alert_threshold * 100 or monthly_pct >= alert_threshold * 100:
        status = "warning"
        status_color = "yellow"
    else:
        status = "ok"
        status_color = "green"

    return {
        "daily_spent": round(daily_spent, 2),
        "daily_limit": daily_limit,
        "daily_pct": round(daily_pct, 1),
        "monthly_spent": round(monthly_spent, 2),
        "monthly_limit": monthly_limit,
        "monthly_pct": round(monthly_pct, 1),
        "status": status,
        "status_color": status_color,
        "enabled": settings["enabled"],
        "alert_threshold": alert_threshold,
    }


# =============================================================================
# Task Execution Service (TSP Orchestrator Integration)
# =============================================================================

# In-memory task execution state (in production, use Redis/DB)
_running_tasks: dict[str, dict[str, Any]] = {}
_task_results: dict[str, dict[str, Any]] = {}


def get_running_tasks() -> list[dict[str, Any]]:
    """
    Get list of currently running tasks.

    Returns:
        List of running task dictionaries with id, status, progress
    """
    return [
        {
            "task_id": task_id,
            "status": info.get("status", "unknown"),
            "phase": info.get("current_phase", "initializing"),
            "started_at": info.get("started_at"),
            "progress_pct": info.get("progress_pct", 0),
            "description": info.get("description", ""),
        }
        for task_id, info in _running_tasks.items()
    ]


def get_task_execution_status(task_id: str) -> dict[str, Any] | None:
    """
    Get execution status for a specific task.

    Args:
        task_id: Task identifier

    Returns:
        Task status dictionary or None if not found
    """
    if task_id in _running_tasks:
        return _running_tasks[task_id]
    if task_id in _task_results:
        return _task_results[task_id]
    return None


def register_task_execution(
    task_id: str, description: str, requirements: str
) -> dict[str, Any]:
    """
    Register a new task for execution.

    Args:
        task_id: Unique task identifier
        description: Task description
        requirements: Task requirements

    Returns:
        Task registration info
    """
    now = datetime.now().isoformat()
    _running_tasks[task_id] = {
        "task_id": task_id,
        "description": description,
        "requirements": requirements,
        "status": "pending",
        "current_phase": "queued",
        "started_at": now,
        "progress_pct": 0,
        "phases_completed": [],
        "execution_log": [],
    }
    return _running_tasks[task_id]


def update_task_progress(
    task_id: str,
    phase: str,
    status: str = "running",
    progress_pct: int | None = None,
    log_entry: str | None = None,
) -> None:
    """
    Update task execution progress.

    Args:
        task_id: Task identifier
        phase: Current phase name
        status: Task status (running, completed, failed)
        progress_pct: Progress percentage (0-100)
        log_entry: Optional log message
    """
    if task_id not in _running_tasks:
        return

    task = _running_tasks[task_id]
    task["current_phase"] = phase
    task["status"] = status

    if progress_pct is not None:
        task["progress_pct"] = progress_pct

    if log_entry:
        task["execution_log"].append(
            {"timestamp": datetime.now().isoformat(), "message": log_entry}
        )

    # Track completed phases
    phase_progress = {
        "planning": 15,
        "design": 30,
        "design_review": 45,
        "code": 60,
        "code_review": 75,
        "test": 90,
        "postmortem": 100,
    }
    if phase in phase_progress and status == "completed":
        if phase not in task["phases_completed"]:
            task["phases_completed"].append(phase)
        task["progress_pct"] = phase_progress[phase]


def complete_task_execution(
    task_id: str, result: dict[str, Any], success: bool = True
) -> None:
    """
    Mark task execution as complete and store result.

    Args:
        task_id: Task identifier
        result: Execution result
        success: Whether task succeeded
    """
    if task_id in _running_tasks:
        task = _running_tasks.pop(task_id)
        task["status"] = "completed" if success else "failed"
        task["progress_pct"] = 100
        task["completed_at"] = datetime.now().isoformat()
        task["result"] = result
        _task_results[task_id] = task


def get_active_agents() -> list[dict[str, Any]]:
    """
    Get list of currently active agents based on running tasks.

    Returns:
        List of active agent dictionaries with name and current task
    """
    active = []
    phase_to_agent = {
        "planning": "Planning Agent",
        "design": "Design Agent",
        "design_review": "Design Review Agent",
        "code": "Code Agent",
        "code_review": "Code Review Agent",
        "test": "Test Agent",
        "postmortem": "Postmortem Agent",
    }

    for task_id, info in _running_tasks.items():
        phase = info.get("current_phase", "").lower()
        if phase in phase_to_agent:
            active.append(
                {
                    "agent_name": phase_to_agent[phase],
                    "task_id": task_id,
                    "phase": phase,
                    "started_at": info.get("started_at"),
                }
            )

    return active


# =============================================================================
# Code Diff Utilities
# =============================================================================


def generate_unified_diff(
    original: str, modified: str, filename: str = "file.py"
) -> str:
    """
    Generate a unified diff between two strings.

    Args:
        original: Original content
        modified: Modified content
        filename: Filename for diff header

    Returns:
        Unified diff string
    """
    import difflib

    original_lines = original.splitlines(keepends=True)
    modified_lines = modified.splitlines(keepends=True)

    diff = difflib.unified_diff(
        original_lines,
        modified_lines,
        fromfile=f"a/{filename}",
        tofile=f"b/{filename}",
        lineterm="",
    )

    return "".join(diff)


def get_code_proposals(task_id: str) -> list[dict[str, Any]]:
    """
    Get code change proposals for a task.

    Args:
        task_id: Task identifier

    Returns:
        List of code proposals with filename, original, modified, diff
    """
    task_dir = ARTIFACTS_DIR / task_id
    if not task_dir.exists():
        return []

    proposals = []
    code_dir = task_dir / "code"

    # Check for generated code files
    if code_dir.exists():
        for code_file in code_dir.glob("*.py"):
            content = code_file.read_text()
            proposals.append(
                {
                    "filename": code_file.name,
                    "path": str(code_file.relative_to(PROJECT_ROOT)),
                    "content": content,
                    "lines": len(content.splitlines()),
                    "status": "pending",  # pending, approved, rejected
                }
            )

    # Also check for standalone .py files in task directory
    for code_file in task_dir.glob("*.py"):
        if code_file.name not in [p["filename"] for p in proposals]:
            content = code_file.read_text()
            proposals.append(
                {
                    "filename": code_file.name,
                    "path": str(code_file.relative_to(PROJECT_ROOT)),
                    "content": content,
                    "lines": len(content.splitlines()),
                    "status": "pending",
                }
            )

    return proposals


def get_phase_yield_data() -> dict[str, Any]:
    """
    Get phase yield analysis data showing task flow through development phases.

    Returns:
        Dictionary with phase counts, transitions, and defect data
    """
    phases = ["Planning", "Design", "Code", "Test", "Complete"]
    phase_counts = dict.fromkeys(phases, 0)
    phase_defects = dict.fromkeys(phases, 0)
    transitions = []

    # Load bootstrap results
    if BOOTSTRAP_RESULTS.exists():
        with open(BOOTSTRAP_RESULTS) as f:
            data = json.load(f)
        results = data.get("results", [])

        for result in results:
            if result.get("success"):
                phase_counts["Complete"] += 1
            else:
                # Failed tasks stuck in earlier phase
                phase_counts["Code"] += 1

    # Load design review results
    design_review_file = DATA_DIR / "bootstrap_design_review_results.json"
    if design_review_file.exists():
        with open(design_review_file) as f:
            data = json.load(f)
        results = data.get("results", [])

        for result in results:
            if result.get("design_success"):
                phase_counts["Design"] += 1
            else:
                phase_defects["Design"] += 1

    # Check defect_log table
    conn = _get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT phase, COUNT(*) as count
                FROM defect_log
                GROUP BY phase
                """
            )
            for row in cursor.fetchall():
                phase = row["phase"]
                if phase in phase_defects:
                    phase_defects[phase] += row["count"]
        except sqlite3.Error:
            pass
        finally:
            conn.close()

    # Calculate totals
    total_started = sum(phase_counts.values())
    total_defects = sum(phase_defects.values())

    # Build transitions (simplified flow)
    if total_started > 0:
        transitions = [
            {
                "from": "Planning",
                "to": "Design",
                "count": phase_counts.get("Design", 0)
                + phase_counts.get("Code", 0)
                + phase_counts.get("Complete", 0),
            },
            {
                "from": "Design",
                "to": "Code",
                "count": phase_counts.get("Code", 0) + phase_counts.get("Complete", 0),
            },
            {"from": "Code", "to": "Test", "count": phase_counts.get("Complete", 0)},
            {
                "from": "Test",
                "to": "Complete",
                "count": phase_counts.get("Complete", 0),
            },
        ]

    return {
        "phases": phases,
        "phase_counts": phase_counts,
        "phase_defects": phase_defects,
        "transitions": transitions,
        "total_started": total_started,
        "total_completed": phase_counts.get("Complete", 0),
        "total_defects": total_defects,
        "yield_rate": (
            phase_counts.get("Complete", 0) / total_started * 100
            if total_started > 0
            else 0
        ),
    }
