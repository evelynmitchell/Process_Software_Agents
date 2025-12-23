#!/usr/bin/env python3
"""
Telemetry Analysis Example - ASP Platform

This example demonstrates how to query and analyze ASP telemetry data
from the SQLite database and Langfuse.

Run with:
    uv run python examples/telemetry_analysis.py

Cost: $0 (no API calls)
Time: < 1 second
"""

import sqlite3
from datetime import UTC, datetime, timedelta
from pathlib import Path


def main():
    """Analyze ASP telemetry data."""
    print("=" * 70)
    print("ASP Platform - Telemetry Analysis Example")
    print("=" * 70)
    print()

    # Connect to telemetry database
    db_path = Path("data/asp_telemetry.db")

    if not db_path.exists():
        print(f"⚠️  Database not found: {db_path}")
        print("   Run some tasks first to generate telemetry data")
        print("   Example: uv run python examples/hello_world.py")
        return

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row  # Access columns by name

    # Analysis 1: Cost by Agent
    print("📊 Analysis 1: Total Cost by Agent (Last 7 Days)")
    print("-" * 70)

    seven_days_ago = (datetime.now(UTC) - timedelta(days=7)).isoformat()

    query = """
        SELECT
            agent_id,
            COUNT(*) as executions,
            SUM(latency_ms) as total_latency_ms,
            SUM(total_tokens) as total_tokens,
            SUM(api_cost_usd) as total_cost_usd,
            AVG(api_cost_usd) as avg_cost_usd
        FROM agent_cost_vector
        WHERE timestamp > ?
        GROUP BY agent_id
        ORDER BY total_cost_usd DESC
    """

    cursor = conn.execute(query, (seven_days_ago,))
    results = cursor.fetchall()

    if results:
        print(f"{'Agent':<25} {'Executions':>10} {'Total Cost':>12} {'Avg Cost':>10}")
        print("-" * 70)
        for row in results:
            print(
                f"{row['agent_id']:<25} {row['executions']:>10} "
                f"${row['total_cost_usd']:>11.4f} ${row['avg_cost_usd']:>9.4f}"
            )
        print()
    else:
        print("No cost data found in last 7 days")
        print()

    # Analysis 2: Defect Statistics
    print("📊 Analysis 2: Defects by Type and Severity")
    print("-" * 70)

    query = """
        SELECT
            defect_type,
            severity,
            COUNT(*) as count,
            AVG(fix_effort_ms) as avg_fix_effort_ms
        FROM defect_log_entry
        GROUP BY defect_type, severity
        ORDER BY severity DESC, count DESC
    """

    cursor = conn.execute(query)
    results = cursor.fetchall()

    if results:
        print(f"{'Defect Type':<30} {'Severity':<10} {'Count':>8} {'Avg Fix (ms)':>15}")
        print("-" * 70)
        for row in results:
            print(
                f"{row['defect_type']:<30} {row['severity']:<10} "
                f"{row['count']:>8} {row['avg_fix_effort_ms']:>15.0f}"
            )
        print()
    else:
        print("No defect data found")
        print()

    # Analysis 3: Performance Trends
    print("📊 Analysis 3: Performance Trends (Last 10 Tasks)")
    print("-" * 70)

    query = """
        SELECT
            task_id,
            timestamp,
            SUM(latency_ms) as total_latency_ms,
            SUM(total_tokens) as total_tokens,
            SUM(api_cost_usd) as total_cost_usd
        FROM agent_cost_vector
        GROUP BY task_id
        ORDER BY timestamp DESC
        LIMIT 10
    """

    cursor = conn.execute(query)
    results = cursor.fetchall()

    if results:
        print(f"{'Task ID':<20} {'Timestamp':<25} {'Latency (s)':>12} {'Cost':>10}")
        print("-" * 70)
        for row in results:
            timestamp = datetime.fromisoformat(row["timestamp"])
            print(
                f"{row['task_id']:<20} {timestamp.strftime('%Y-%m-%d %H:%M:%S'):<25} "
                f"{row['total_latency_ms']/1000:>12.1f} ${row['total_cost_usd']:>9.4f}"
            )
        print()
    else:
        print("No task data found")
        print()

    # Analysis 4: Bootstrap Learning Progress
    print("📊 Analysis 4: Bootstrap Learning Progress")
    print("-" * 70)

    query = """
        SELECT COUNT(DISTINCT task_id) as total_tasks
        FROM agent_cost_vector
    """

    cursor = conn.execute(query)
    result = cursor.fetchone()

    total_tasks = result["total_tasks"] if result else 0
    probe_ai_threshold = 30  # From PRD

    print(f"Total Tasks Completed: {total_tasks}")
    print(f"PROBE-AI Threshold: {probe_ai_threshold} tasks")

    if total_tasks >= probe_ai_threshold:
        print("✅ Bootstrap complete! PROBE-AI can be enabled.")
    else:
        remaining = probe_ai_threshold - total_tasks
        print(f"⏳ Bootstrap in progress. {remaining} more tasks needed for PROBE-AI.")
    print()

    # Analysis 5: Top Expensive Tasks
    print("📊 Analysis 5: Most Expensive Tasks")
    print("-" * 70)

    query = """
        SELECT
            task_id,
            SUM(api_cost_usd) as total_cost_usd,
            SUM(total_tokens) as total_tokens
        FROM agent_cost_vector
        GROUP BY task_id
        ORDER BY total_cost_usd DESC
        LIMIT 5
    """

    cursor = conn.execute(query)
    results = cursor.fetchall()

    if results:
        print(f"{'Task ID':<20} {'Total Cost':>12} {'Total Tokens':>15}")
        print("-" * 70)
        for row in results:
            print(
                f"{row['task_id']:<20} ${row['total_cost_usd']:>11.4f} {row['total_tokens']:>15,}"
            )
        print()
    else:
        print("No task cost data found")
        print()

    conn.close()

    print("💡 Advanced Analysis:")
    print("   1. Langfuse Dashboard: https://cloud.langfuse.com")
    print("   2. Custom queries: sqlite3 data/asp_telemetry.db")
    print(
        "   3. Bootstrap analysis: uv run python scripts/bootstrap_data_collection.py"
    )
    print()
    print("=" * 70)
    print("Example complete!")
    print("=" * 70)


if __name__ == "__main__":
    main()
