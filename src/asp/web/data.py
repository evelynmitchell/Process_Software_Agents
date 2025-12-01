"""
Data Access Layer for ASP Web UI

Provides database initialization and query functions for the web interface.
"""

import sqlite3
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

# Database path (relative to project root)
DB_PATH = Path(__file__).parent.parent.parent.parent / "data" / "asp_telemetry.db"


def init_database(db_path: Optional[Path] = None) -> None:
    """
    Initialize the telemetry database with required tables.

    Creates the database file and tables if they don't exist.
    """
    db_path = db_path or DB_PATH
    db_path.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()

    # Create agent_cost_vector table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS agent_cost_vector (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            task_id TEXT NOT NULL,
            subtask_id TEXT,
            project_id TEXT,
            user_id TEXT,
            agent_role TEXT NOT NULL,
            agent_version TEXT,
            agent_iteration INTEGER DEFAULT 1,
            metric_type TEXT NOT NULL,
            metric_value REAL NOT NULL,
            metric_unit TEXT NOT NULL,
            llm_model TEXT,
            llm_provider TEXT,
            metadata TEXT
        )
    """)

    # Create defect_log table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS defect_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            defect_id TEXT UNIQUE NOT NULL,
            created_at TEXT NOT NULL,
            task_id TEXT NOT NULL,
            project_id TEXT,
            user_id TEXT,
            defect_type TEXT NOT NULL,
            severity TEXT NOT NULL,
            description TEXT NOT NULL,
            phase_injected TEXT NOT NULL,
            phase_removed TEXT NOT NULL,
            component_path TEXT,
            function_name TEXT,
            line_number INTEGER,
            root_cause TEXT,
            resolution_notes TEXT,
            flagged_by_agent INTEGER DEFAULT 0,
            metadata TEXT
        )
    """)

    conn.commit()
    conn.close()


@contextmanager
def get_db_connection(db_path: Optional[Path] = None):
    """Context manager for database connections."""
    db_path = db_path or DB_PATH

    # Initialize database if it doesn't exist
    if not db_path.exists():
        init_database(db_path)

    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


def get_recent_activity(limit: int = 10, user_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Get recent agent activity from telemetry.

    Returns list of recent metric records.
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()

        query = """
            SELECT
                timestamp,
                task_id,
                agent_role,
                metric_type,
                metric_value,
                metric_unit,
                llm_model
            FROM agent_cost_vector
        """
        params = []

        if user_id:
            query += " WHERE user_id = ?"
            params.append(user_id)

        query += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)

        cursor.execute(query, params)
        rows = cursor.fetchall()

        return [dict(row) for row in rows]


def get_active_tasks(limit: int = 20) -> List[Dict[str, Any]]:
    """
    Get distinct active tasks from recent activity.

    Returns unique task_ids with their latest activity.
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                task_id,
                MAX(timestamp) as last_activity,
                agent_role,
                COUNT(*) as activity_count
            FROM agent_cost_vector
            GROUP BY task_id
            ORDER BY last_activity DESC
            LIMIT ?
        """, (limit,))

        rows = cursor.fetchall()
        return [dict(row) for row in rows]


def get_task_metrics(task_id: str) -> Dict[str, Any]:
    """
    Get aggregated metrics for a specific task.

    Returns dict with totals for tokens, cost, latency.
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                metric_type,
                SUM(metric_value) as total,
                metric_unit
            FROM agent_cost_vector
            WHERE task_id = ?
            GROUP BY metric_type, metric_unit
        """, (task_id,))

        rows = cursor.fetchall()

        metrics = {}
        for row in rows:
            metrics[row['metric_type']] = {
                'total': row['total'],
                'unit': row['metric_unit']
            }

        return metrics


def get_defect_summary() -> Dict[str, Any]:
    """
    Get summary statistics for defects.

    Returns counts by severity and type.
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()

        # Count by severity
        cursor.execute("""
            SELECT severity, COUNT(*) as count
            FROM defect_log
            GROUP BY severity
        """)
        severity_counts = {row['severity']: row['count'] for row in cursor.fetchall()}

        # Count by defect_type
        cursor.execute("""
            SELECT defect_type, COUNT(*) as count
            FROM defect_log
            GROUP BY defect_type
            ORDER BY count DESC
            LIMIT 5
        """)
        type_counts = {row['defect_type']: row['count'] for row in cursor.fetchall()}

        # Total count
        cursor.execute("SELECT COUNT(*) as total FROM defect_log")
        total = cursor.fetchone()['total']

        return {
            'total': total,
            'by_severity': severity_counts,
            'by_type': type_counts
        }


def get_recent_defects(limit: int = 5) -> List[Dict[str, Any]]:
    """Get most recent defects."""
    with get_db_connection() as conn:
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                defect_id,
                created_at,
                task_id,
                defect_type,
                severity,
                description,
                phase_injected,
                phase_removed
            FROM defect_log
            ORDER BY created_at DESC
            LIMIT ?
        """, (limit,))

        rows = cursor.fetchall()
        return [dict(row) for row in rows]


def get_agent_stats() -> Dict[str, Any]:
    """
    Get statistics per agent role.

    Returns dict with metrics per agent.
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                agent_role,
                COUNT(*) as invocation_count,
                AVG(CASE WHEN metric_type = 'Latency' THEN metric_value END) as avg_latency,
                SUM(CASE WHEN metric_type = 'Tokens_In' THEN metric_value ELSE 0 END) as total_tokens_in,
                SUM(CASE WHEN metric_type = 'Tokens_Out' THEN metric_value ELSE 0 END) as total_tokens_out,
                SUM(CASE WHEN metric_type = 'API_Cost' THEN metric_value ELSE 0 END) as total_cost
            FROM agent_cost_vector
            GROUP BY agent_role
            ORDER BY invocation_count DESC
        """)

        rows = cursor.fetchall()
        return {row['agent_role']: dict(row) for row in rows}


def insert_demo_data() -> None:
    """
    Insert demo data for UI development.

    Creates sample metrics and defects for testing the UI.
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()

        # Check if we already have data
        cursor.execute("SELECT COUNT(*) FROM agent_cost_vector")
        if cursor.fetchone()[0] > 0:
            return  # Already have data

        now = datetime.utcnow()

        # Sample tasks and agents
        tasks = [
            ("TSP-DEMO-001", "Implement user authentication"),
            ("TSP-DEMO-002", "Refactor payment service"),
            ("TSP-DEMO-003", "Add unit tests for API"),
        ]

        agents = ["Planning", "Design", "Code", "Review", "Postmortem"]

        # Insert sample metrics
        for task_id, _ in tasks:
            for agent in agents:
                # Latency
                cursor.execute("""
                    INSERT INTO agent_cost_vector
                    (timestamp, task_id, agent_role, metric_type, metric_value, metric_unit, llm_model)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    now.isoformat(),
                    task_id,
                    agent,
                    "Latency",
                    1500 + (hash(task_id + agent) % 3000),  # 1500-4500 ms
                    "ms",
                    "claude-sonnet-4"
                ))

                # Tokens
                cursor.execute("""
                    INSERT INTO agent_cost_vector
                    (timestamp, task_id, agent_role, metric_type, metric_value, metric_unit, llm_model)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    now.isoformat(),
                    task_id,
                    agent,
                    "Tokens_In",
                    500 + (hash(task_id + agent) % 1000),
                    "tokens",
                    "claude-sonnet-4"
                ))

        # Insert sample defects
        defects = [
            ("Low", "20_Syntax", "Missing semicolon in config", "Code", "Review"),
            ("Medium", "50_Interface", "API response format mismatch", "Design", "Code"),
            ("High", "80_Function", "Incorrect calculation in payment", "Code", "Review"),
        ]

        import uuid
        for severity, dtype, desc, injected, removed in defects:
            cursor.execute("""
                INSERT INTO defect_log
                (defect_id, created_at, task_id, defect_type, severity, description, phase_injected, phase_removed)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                f"DEFECT-{uuid.uuid4().hex[:12].upper()}",
                now.isoformat(),
                "TSP-DEMO-001",
                dtype,
                severity,
                desc,
                injected,
                removed
            ))

        conn.commit()
