"""
Data Access Layer for ASP Web UI

Provides functions to fetch tasks, telemetry, and artifacts for display in the web interface.
"""

import json
from pathlib import Path
from typing import Any

# Paths relative to project root
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data"
ARTIFACTS_DIR = PROJECT_ROOT / "artifacts"
BOOTSTRAP_RESULTS = DATA_DIR / "bootstrap_results.json"
BOOTSTRAP_DESIGN_RESULTS = DATA_DIR / "bootstrap_design_review_results.json"


def get_tasks() -> list[dict[str, Any]]:
    """
    Get all tasks from bootstrap results.

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

    return details


def get_recent_activity(limit: int = 10) -> list[dict[str, Any]]:
    """
    Get recent activity from the system.

    Returns:
        List of recent activities with timestamp, action, and status
    """
    activities = []

    # Check for recently modified artifacts
    if ARTIFACTS_DIR.exists():
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
            from datetime import datetime

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
    Get design review statistics from bootstrap data.

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

    return stats
