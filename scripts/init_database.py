#!/usr/bin/env python3
"""
ASP Telemetry Database Initialization Script

This script initializes the SQLite database for the ASP Platform telemetry system.

Usage:
    # Create database with schema only
    uv run python scripts/init_database.py

    # Create database with schema and sample data
    uv run python scripts/init_database.py --with-sample-data

    # Specify custom database path
    uv run python scripts/init_database.py --db-path /path/to/custom.db

    # Reset (drop and recreate) existing database
    uv run python scripts/init_database.py --reset
"""

import argparse
import sqlite3
import sys
from pathlib import Path


def get_project_root() -> Path:
    """Get the project root directory."""
    # Assuming script is in scripts/ directory
    return Path(__file__).parent.parent


def read_sql_file(file_path: Path) -> str:
    """Read SQL file and return contents."""
    if not file_path.exists():
        raise FileNotFoundError(f"SQL file not found: {file_path}")

    with open(file_path) as f:
        return f.read()


def execute_sql_script(conn: sqlite3.Connection, sql_script: str, script_name: str):
    """Execute a SQL script with proper error handling."""
    print(f"  Executing {script_name}...")
    cursor = conn.cursor()

    try:
        cursor.executescript(sql_script)
        conn.commit()
        print(f"  [OK] {script_name} completed successfully")
    except sqlite3.Error as e:
        print(f"  [ERROR] Error executing {script_name}: {e}")
        raise


def verify_database_schema(conn: sqlite3.Connection) -> bool:
    """Verify that all expected tables exist."""
    cursor = conn.cursor()

    expected_tables = [
        "agent_cost_vector",
        "defect_log",
        "task_metadata",
        "bootstrap_metrics",
    ]

    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    existing_tables = [row[0] for row in cursor.fetchall()]

    missing_tables = [t for t in expected_tables if t not in existing_tables]

    if missing_tables:
        print(f"  [ERROR] Missing tables: {', '.join(missing_tables)}")
        return False

    print(f"  [OK] All {len(expected_tables)} tables created successfully")
    return True


def print_database_stats(conn: sqlite3.Connection):
    """Print summary statistics about the database contents."""
    cursor = conn.cursor()

    print("\nDatabase Statistics:")
    print("-" * 50)

    # Count rows in each table
    tables = ["task_metadata", "agent_cost_vector", "defect_log", "bootstrap_metrics"]

    for table in tables:
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        count = cursor.fetchone()[0]
        print(f"  {table:.<40} {count:>5} rows")

    # Show task summary if data exists
    cursor.execute("SELECT COUNT(*) FROM task_metadata")
    if cursor.fetchone()[0] > 0:
        print("\nTask Summary:")
        print("-" * 50)
        cursor.execute(
            """
            SELECT
                task_id,
                task_type,
                status,
                estimated_complexity,
                actual_complexity,
                defect_count
            FROM task_metadata
            ORDER BY created_at
        """
        )

        for row in cursor.fetchall():
            task_id, task_type, status, est_cplx, act_cplx, defects = row
            print(
                f"  {task_id}: {task_type} ({status}) - "
                f"Est: {est_cplx}, Actual: {act_cplx}, Defects: {defects}"
            )


def initialize_database(
    db_path: Path,
    with_sample_data: bool = False,
    reset: bool = False,
) -> bool:
    """
    Initialize the ASP telemetry database.

    Args:
        db_path: Path to the SQLite database file
        with_sample_data: If True, populate with sample data
        reset: If True, drop existing database and recreate

    Returns:
        True if initialization successful, False otherwise
    """
    project_root = get_project_root()
    sql_dir = project_root / "database" / "sqlite"

    # Check if database exists
    if db_path.exists():
        if reset:
            print(f"  Resetting existing database: {db_path}")
            db_path.unlink()
        else:
            print(f"  Database already exists: {db_path}")
            response = input("Do you want to continue? (y/N): ").strip().lower()
            if response != "y":
                print("Aborted.")
                return False

    # Create parent directory if it doesn't exist
    db_path.parent.mkdir(parents=True, exist_ok=True)

    print(f"\n{'='*50}")
    print("Initializing ASP Telemetry Database")
    print(f"{'='*50}")
    print(f"Database: {db_path}")
    print(f"SQL Directory: {sql_dir}\n")

    try:
        # Connect to database (creates file if doesn't exist)
        conn = sqlite3.connect(db_path)
        print("[OK] Connected to database\n")

        # Enable foreign keys (optional but recommended)
        conn.execute("PRAGMA foreign_keys = ON")

        # Execute schema creation scripts
        print("Creating database schema...")

        # 1. Create tables
        create_tables_sql = read_sql_file(sql_dir / "create_tables.sql")
        execute_sql_script(conn, create_tables_sql, "create_tables.sql")

        # 2. Create indexes
        create_indexes_sql = read_sql_file(sql_dir / "create_indexes.sql")
        execute_sql_script(conn, create_indexes_sql, "create_indexes.sql")

        # 3. Verify schema
        print("\nVerifying database schema...")
        if not verify_database_schema(conn):
            print("[ERROR] Schema verification failed")
            return False

        # 4. Insert sample data if requested
        if with_sample_data:
            print("\nInserting sample data...")
            sample_data_sql = read_sql_file(sql_dir / "sample_data.sql")
            execute_sql_script(conn, sample_data_sql, "sample_data.sql")

        # Print statistics
        print_database_stats(conn)

        # Close connection
        conn.close()

        print(f"\n{'='*50}")
        print("[OK] Database initialization completed successfully!")
        print(f"{'='*50}\n")
        print(f"Database location: {db_path}")
        print(f"Database size: {db_path.stat().st_size:,} bytes\n")

        print("Next steps:")
        print("  1. Test database connection with your code")
        print("  2. Start implementing agent telemetry logging")
        print("  3. Run first task to collect baseline data\n")

        return True

    except Exception as e:
        print(f"\n[ERROR] Database initialization failed: {e}")
        return False


def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(
        description="Initialize the ASP Telemetry Database (SQLite)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )

    parser.add_argument(
        "--db-path",
        type=Path,
        default=Path("data/asp_telemetry.db"),
        help="Path to the SQLite database file (default: data/asp_telemetry.db)",
    )

    parser.add_argument(
        "--with-sample-data",
        action="store_true",
        help="Populate database with sample data for testing",
    )

    parser.add_argument(
        "--reset",
        action="store_true",
        help="Reset existing database (drop and recreate)",
    )

    args = parser.parse_args()

    # Initialize database
    success = initialize_database(
        db_path=args.db_path,
        with_sample_data=args.with_sample_data,
        reset=args.reset,
    )

    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
