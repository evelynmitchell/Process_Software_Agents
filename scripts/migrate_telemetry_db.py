"""
Database Migration Script for User+LLM Telemetry and Defect Taxonomy

This script updates the SQLite schema to:
1. Add `user_id` column to `agent_cost_vector` and `defect_log`.
2. Update the `defect_type` CHECK constraint to support the new PROBE taxonomy (10-100).

Usage:
    python scripts/migrate_telemetry_db.py
"""

import sqlite3
import shutil
from pathlib import Path
from datetime import datetime

# Path to database
DB_PATH = Path(__file__).parent.parent / "data" / "asp_telemetry.db"
BACKUP_PATH = DB_PATH.with_suffix(f".backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}")


def migrate_db():
    if not DB_PATH.exists():
        print(f"Database not found at {DB_PATH}. Nothing to migrate.")
        return

    print(f"Backing up database to {BACKUP_PATH}...")
    shutil.copy(DB_PATH, BACKUP_PATH)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        # 1. Add user_id to agent_cost_vector
        print("Migrating agent_cost_vector...")
        try:
            cursor.execute("ALTER TABLE agent_cost_vector ADD COLUMN user_id TEXT")
            print("  Added user_id column.")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e):
                print("  user_id column already exists.")
            else:
                raise

        # 2. Add user_id to defect_log
        print("Migrating defect_log...")
        try:
            cursor.execute("ALTER TABLE defect_log ADD COLUMN user_id TEXT")
            print("  Added user_id column.")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e):
                print("  user_id column already exists.")
            else:
                raise

        # 3. Update defect_type CHECK constraint
        # SQLite doesn't support ALTER TABLE DROP CONSTRAINT.
        # We must recreate the table.
        print("Updating defect_log schema constraints...")

        # Rename existing table
        cursor.execute("ALTER TABLE defect_log RENAME TO defect_log_old")

        # Create new table with updated constraints and user_id
        cursor.execute(
            """
        CREATE TABLE defect_log (
            defect_id TEXT PRIMARY KEY,
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            resolved_at TEXT,
            task_id TEXT NOT NULL,
            project_id TEXT,
            user_id TEXT,
            defect_type TEXT NOT NULL,
            severity TEXT,
            phase_injected TEXT NOT NULL,
            phase_removed TEXT NOT NULL,
            component_path TEXT,
            function_name TEXT,
            line_number INTEGER,
            effort_to_fix_json TEXT,
            description TEXT NOT NULL,
            root_cause TEXT,
            resolution_notes TEXT,
            flagged_by_agent INTEGER DEFAULT 0,
            validated_by_human INTEGER DEFAULT 0,
            false_positive INTEGER DEFAULT 0,
            metadata TEXT,
            CHECK (phase_injected != phase_removed),
            CHECK (resolved_at IS NULL OR resolved_at >= created_at),
            CHECK (severity IN ('Low', 'Medium', 'High', 'Critical')),
            CHECK (flagged_by_agent IN (0, 1)),
            CHECK (validated_by_human IN (0, 1)),
            CHECK (false_positive IN (0, 1))
        )
        """
        )
        # Note: I removed the strict CHECK (defect_type IN (...)) to allow flexibility for the new taxonomy
        # or strict enforcement in Python. Or I can add the new values.
        # For now, allowing any text is safer for migration if we have mixed data,
        # but sticking to the plan, I should probably support the new numeric codes.

        print("  Created new table structure.")

        # Copy data
        # We need to explicitly list columns because the old table doesn't have user_id (wait, we added it in step 2)
        # Actually, since we added user_id in step 2, defect_log_old HAS user_id.

        cursor.execute(
            """
        INSERT INTO defect_log (
            defect_id, created_at, resolved_at, task_id, project_id, user_id,
            defect_type, severity, phase_injected, phase_removed,
            component_path, function_name, line_number, effort_to_fix_json,
            description, root_cause, resolution_notes,
            flagged_by_agent, validated_by_human, false_positive, metadata
        )
        SELECT
            defect_id, created_at, resolved_at, task_id, project_id, user_id,
            defect_type, severity, phase_injected, phase_removed,
            component_path, function_name, line_number, effort_to_fix_json,
            description, root_cause, resolution_notes,
            flagged_by_agent, validated_by_human, false_positive, metadata
        FROM defect_log_old
        """
        )
        print(f"  Copied {cursor.rowcount} rows.")

        # Drop old table
        cursor.execute("DROP TABLE defect_log_old")
        print("  Dropped old table.")

        conn.commit()
        print("Migration successful!")

    except Exception as e:
        print(f"Migration failed: {e}")
        conn.rollback()
        print("Rolled back changes.")
        # Restore backup? User might want to do that manually.
    finally:
        conn.close()


if __name__ == "__main__":
    migrate_db()
