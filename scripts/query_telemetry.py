#!/usr/bin/env python3
"""
SQLite Query Test Script for ASP Telemetry Database

This script demonstrates various useful queries for analyzing telemetry data
from the agent_cost_vector and defect_log tables.

Usage:
    uv run python scripts/query_telemetry.py
    uv run python scripts/query_telemetry.py --query agent-costs
    uv run python scripts/query_telemetry.py --query defects
    uv run python scripts/query_telemetry.py --query summary
"""

import argparse
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import List, Tuple


# ============================================================================
# Configuration
# ============================================================================

DEFAULT_DB_PATH = Path(__file__).parent.parent / "data" / "asp_telemetry.db"


# ============================================================================
# Query Functions
# ============================================================================


def get_connection(db_path: Path) -> sqlite3.Connection:
    """Get database connection with Row factory."""
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    return conn


def query_agent_costs(conn: sqlite3.Connection, limit: int = 20) -> List[sqlite3.Row]:
    """
    Query recent agent cost records.

    Returns task_id, agent_role, metric_type, metric_value, and timestamp.
    """
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT
            task_id,
            agent_role,
            metric_type,
            metric_value,
            metric_unit,
            llm_model,
            timestamp
        FROM agent_cost_vector
        ORDER BY timestamp DESC
        LIMIT ?
        """,
        (limit,),
    )
    return cursor.fetchall()


def query_agent_costs_by_task(
    conn: sqlite3.Connection, task_id: str
) -> List[sqlite3.Row]:
    """
    Query all agent costs for a specific task.

    Useful for understanding the total cost breakdown of a task.
    """
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT
            agent_role,
            metric_type,
            metric_value,
            metric_unit,
            agent_iteration,
            timestamp
        FROM agent_cost_vector
        WHERE task_id = ?
        ORDER BY timestamp ASC
        """,
        (task_id,),
    )
    return cursor.fetchall()


def query_agent_cost_summary(conn: sqlite3.Connection) -> List[sqlite3.Row]:
    """
    Aggregate agent costs by role and metric type.

    Shows total costs, token usage, and latency by agent role.
    """
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT
            agent_role,
            metric_type,
            COUNT(*) as execution_count,
            SUM(metric_value) as total_value,
            AVG(metric_value) as avg_value,
            MIN(metric_value) as min_value,
            MAX(metric_value) as max_value,
            metric_unit
        FROM agent_cost_vector
        GROUP BY agent_role, metric_type
        ORDER BY agent_role, metric_type
        """
    )
    return cursor.fetchall()


def query_defects(conn: sqlite3.Connection, limit: int = 20) -> List[sqlite3.Row]:
    """
    Query recent defect records.

    Returns defect details including type, severity, and phases.
    """
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT
            defect_id,
            task_id,
            defect_type,
            severity,
            phase_injected,
            phase_removed,
            description,
            flagged_by_agent,
            created_at
        FROM defect_log
        ORDER BY created_at DESC
        LIMIT ?
        """,
        (limit,),
    )
    return cursor.fetchall()


def query_defects_by_type(conn: sqlite3.Connection) -> List[sqlite3.Row]:
    """
    Aggregate defects by type and severity.

    Useful for understanding defect patterns.
    """
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT
            defect_type,
            severity,
            COUNT(*) as defect_count,
            SUM(CASE WHEN flagged_by_agent = 1 THEN 1 ELSE 0 END) as flagged_by_agent_count,
            SUM(CASE WHEN validated_by_human = 1 THEN 1 ELSE 0 END) as validated_count
        FROM defect_log
        GROUP BY defect_type, severity
        ORDER BY defect_count DESC
        """
    )
    return cursor.fetchall()


def query_defects_by_phase(conn: sqlite3.Connection) -> List[sqlite3.Row]:
    """
    Aggregate defects by injection and removal phases.

    Shows which phases introduce/catch the most defects (PSP metrics).
    """
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT
            phase_injected,
            phase_removed,
            COUNT(*) as defect_count,
            AVG(
                CAST(
                    (julianday(resolved_at) - julianday(created_at)) * 86400
                    AS REAL
                )
            ) as avg_fix_time_seconds
        FROM defect_log
        WHERE resolved_at IS NOT NULL
        GROUP BY phase_injected, phase_removed
        ORDER BY defect_count DESC
        """
    )
    return cursor.fetchall()


def query_task_summary(conn: sqlite3.Connection) -> List[sqlite3.Row]:
    """
    Get summary of all tasks with cost and defect counts.

    Useful for dashboard views and PROBE-AI estimation.
    """
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT
            acv.task_id,
            COUNT(DISTINCT acv.id) as total_agent_executions,
            SUM(CASE WHEN acv.metric_type = 'API_Cost' THEN acv.metric_value ELSE 0 END) as total_api_cost,
            SUM(CASE WHEN acv.metric_type = 'Tokens_In' THEN acv.metric_value ELSE 0 END) as total_tokens_in,
            SUM(CASE WHEN acv.metric_type = 'Tokens_Out' THEN acv.metric_value ELSE 0 END) as total_tokens_out,
            AVG(CASE WHEN acv.metric_type = 'Latency' THEN acv.metric_value ELSE NULL END) as avg_latency_ms,
            COUNT(DISTINCT dl.defect_id) as defect_count,
            MIN(acv.timestamp) as started_at,
            MAX(acv.timestamp) as last_updated_at
        FROM agent_cost_vector acv
        LEFT JOIN defect_log dl ON acv.task_id = dl.task_id
        GROUP BY acv.task_id
        ORDER BY last_updated_at DESC
        """
    )
    return cursor.fetchall()


def query_probe_ai_data(
    conn: sqlite3.Connection, agent_role: str = "Planning"
) -> List[sqlite3.Row]:
    """
    Query data for PROBE-AI estimation model.

    Returns historical latency and token data for a specific agent role.
    """
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT
            task_id,
            metric_type,
            metric_value,
            metric_unit,
            timestamp
        FROM agent_cost_vector
        WHERE agent_role = ?
        ORDER BY timestamp DESC
        LIMIT 100
        """,
        (agent_role,),
    )
    return cursor.fetchall()


def query_database_stats(conn: sqlite3.Connection) -> dict:
    """
    Get overall database statistics.
    """
    cursor = conn.cursor()

    # Count total records
    cursor.execute("SELECT COUNT(*) as count FROM agent_cost_vector")
    agent_cost_count = cursor.fetchone()["count"]

    cursor.execute("SELECT COUNT(*) as count FROM defect_log")
    defect_count = cursor.fetchone()["count"]

    cursor.execute("SELECT COUNT(DISTINCT task_id) as count FROM agent_cost_vector")
    unique_tasks = cursor.fetchone()["count"]

    cursor.execute(
        "SELECT MIN(timestamp) as earliest, MAX(timestamp) as latest FROM agent_cost_vector"
    )
    time_range = cursor.fetchone()

    return {
        "agent_cost_records": agent_cost_count,
        "defect_records": defect_count,
        "unique_tasks": unique_tasks,
        "earliest_record": time_range["earliest"],
        "latest_record": time_range["latest"],
    }


# ============================================================================
# Display Functions
# ============================================================================


def print_header(title: str):
    """Print a formatted section header."""
    print()
    print("=" * 80)
    print(f"  {title}")
    print("=" * 80)


def print_rows(rows: List[sqlite3.Row], title: str = None):
    """Print query results in a formatted table."""
    if title:
        print_header(title)

    if not rows:
        print("  (no records found)")
        return

    # Get column names from first row
    columns = rows[0].keys()

    # Print column headers
    print()
    print("  " + " | ".join(columns))
    print("  " + "-" * (sum(len(col) + 3 for col in columns) - 3))

    # Print rows
    for row in rows:
        values = []
        for col in columns:
            value = row[col]
            if value is None:
                values.append("NULL")
            elif isinstance(value, float):
                values.append(f"{value:.2f}")
            else:
                values.append(str(value))
        print("  " + " | ".join(values))


def print_stats(stats: dict):
    """Print database statistics."""
    print_header("Database Statistics")
    print()
    print(f"  Agent Cost Records:  {stats['agent_cost_records']}")
    print(f"  Defect Records:      {stats['defect_records']}")
    print(f"  Unique Tasks:        {stats['unique_tasks']}")
    print(f"  Earliest Record:     {stats['earliest_record']}")
    print(f"  Latest Record:       {stats['latest_record']}")


# ============================================================================
# Main Execution
# ============================================================================


def main():
    """Run telemetry queries."""
    parser = argparse.ArgumentParser(
        description="Query and analyze ASP telemetry database"
    )
    parser.add_argument(
        "--db-path",
        type=Path,
        default=DEFAULT_DB_PATH,
        help=f"Path to SQLite database (default: {DEFAULT_DB_PATH})",
    )
    parser.add_argument(
        "--query",
        choices=[
            "all",
            "agent-costs",
            "agent-summary",
            "defects",
            "defect-types",
            "defect-phases",
            "tasks",
            "probe-ai",
            "stats",
        ],
        default="all",
        help="Which query to run (default: all)",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=20,
        help="Limit for queries that return multiple rows (default: 20)",
    )
    parser.add_argument("--task-id", type=str, help="Task ID for task-specific queries")

    args = parser.parse_args()

    # Check database exists
    if not args.db_path.exists():
        print(f"Error: Database not found at {args.db_path}")
        print("Run: uv run python scripts/init_database.py --with-sample-data")
        return 1

    # Connect to database
    conn = get_connection(args.db_path)

    try:
        # Run queries based on selection
        if args.query in ("all", "stats"):
            stats = query_database_stats(conn)
            print_stats(stats)

        if args.query in ("all", "agent-costs"):
            if args.task_id:
                rows = query_agent_costs_by_task(conn, args.task_id)
                print_rows(rows, f"Agent Costs for Task: {args.task_id}")
            else:
                rows = query_agent_costs(conn, args.limit)
                print_rows(rows, f"Recent Agent Cost Records (limit {args.limit})")

        if args.query in ("all", "agent-summary"):
            rows = query_agent_cost_summary(conn)
            print_rows(rows, "Agent Cost Summary by Role and Metric")

        if args.query in ("all", "defects"):
            rows = query_defects(conn, args.limit)
            print_rows(rows, f"Recent Defect Records (limit {args.limit})")

        if args.query in ("all", "defect-types"):
            rows = query_defects_by_type(conn)
            print_rows(rows, "Defects by Type and Severity")

        if args.query in ("all", "defect-phases"):
            rows = query_defects_by_phase(conn)
            print_rows(rows, "Defects by Phase (PSP Analysis)")

        if args.query in ("all", "tasks"):
            rows = query_task_summary(conn)
            print_rows(rows, "Task Summary with Costs and Defects")

        if args.query == "probe-ai":
            rows = query_probe_ai_data(conn)
            print_rows(rows, "PROBE-AI Training Data (Planning Agent)")

        print()
        print("=" * 80)
        print()

    finally:
        conn.close()

    return 0


if __name__ == "__main__":
    exit(main())
