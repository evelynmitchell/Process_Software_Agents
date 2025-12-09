"""
ASP CLI - Main entry point for command-line agent execution.

Provides commands for:
- run: Execute a task through the TSP pipeline
- status: Check agent/task status
- init-db: Initialize the database

Usage:
    python -m asp.cli run --task-id TASK-001 --description "Add feature X"
    python -m asp.cli status
    python -m asp.cli init-db

Author: ASP Development Team
Date: December 2025
"""

# pylint: disable=logging-fstring-interpolation

import argparse
import json
import logging
import os
import sys
from pathlib import Path

# Configure logging before imports
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("asp.cli")


def setup_environment():
    """Ensure environment is properly configured."""
    # Check for required environment variables
    required_vars = []
    optional_vars = ["ANTHROPIC_API_KEY", "LANGFUSE_PUBLIC_KEY", "LANGFUSE_SECRET_KEY"]

    missing_required = [v for v in required_vars if not os.getenv(v)]
    if missing_required:
        logger.error(f"Missing required environment variables: {missing_required}")
        sys.exit(1)

    missing_optional = [v for v in optional_vars if not os.getenv(v)]
    if missing_optional:
        logger.warning(f"Missing optional environment variables: {missing_optional}")
        logger.warning("Some features may not work without these.")


def _build_task_requirements(args):
    """Build TaskRequirements from CLI arguments."""
    from asp.models.planning import TaskRequirements

    requirements_text = args.requirements
    if args.requirements_file:
        requirements_path = Path(args.requirements_file)
        if requirements_path.exists():
            requirements_text = requirements_path.read_text(encoding="utf-8")
        else:
            logger.error(f"Requirements file not found: {args.requirements_file}")
            sys.exit(1)

    if not requirements_text:
        requirements_text = args.description  # Use description as fallback

    return TaskRequirements(
        task_id=args.task_id,
        description=args.description,
        requirements=requirements_text,
    )


def _configure_hitl(args, db_path):
    """Configure HITL approval service based on CLI arguments."""
    if args.auto_approve:
        logger.warning("Auto-approve mode enabled - all quality gates will pass")

        def auto_approve_all(gate_name=None, **kwargs):  # noqa: ARG001
            logger.info(f"Auto-approving gate: {gate_name}")
            return True

        return None, auto_approve_all

    if args.hitl_database:
        from asp.approval.database_service import DatabaseApprovalService

        hitl_timeout = getattr(args, "hitl_timeout", 3600.0)
        hitl_poll = getattr(args, "hitl_poll_interval", 5.0)
        approval_service = DatabaseApprovalService(
            db_path=db_path, poll_interval=hitl_poll, timeout=hitl_timeout
        )
        logger.info(
            f"HITL database mode enabled - approvals via WebUI "
            f"(timeout: {hitl_timeout}s, poll: {hitl_poll}s)"
        )
        return approval_service, None

    logger.info("No HITL mode - quality gate failures will halt pipeline")
    return None, None


def _save_result(result, output_path):
    """Save execution result to JSON file."""
    from dataclasses import asdict

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(asdict(result), f, indent=2, default=str)
    logger.info(f"Results saved to: {output_path}")


def cmd_run(args):
    """Execute a task through the TSP pipeline."""
    from asp.orchestrators import TSPOrchestrator

    logger.info("=" * 60)
    logger.info("ASP CLI - Task Execution")
    logger.info("=" * 60)

    task_requirements = _build_task_requirements(args)
    logger.info(f"Task ID: {task_requirements.task_id}")
    logger.info(f"Description: {task_requirements.description}")
    logger.info("-" * 60)

    db_path = Path(args.db_path) if args.db_path else Path("data/asp_telemetry.db")
    approval_service, hitl_approver = _configure_hitl(args, db_path)
    orchestrator = TSPOrchestrator(db_path=db_path, approval_service=approval_service)

    try:
        result = orchestrator.execute(
            requirements=task_requirements, hitl_approver=hitl_approver
        )

        logger.info("=" * 60)
        logger.info("EXECUTION COMPLETE")
        logger.info("=" * 60)
        logger.info(f"Overall Status: {result.overall_status}")
        logger.info(f"Duration: {result.total_duration_seconds:.1f}s")
        logger.info(f"Files Generated: {result.generated_code.total_files}")
        logger.info(f"HITL Overrides: {len(result.hitl_overrides)}")

        if args.output:
            _save_result(result, args.output)

        sys.exit(0 if result.overall_status in ["PASS", "CONDITIONAL_PASS"] else 1)

    except Exception as e:  # pylint: disable=broad-exception-caught
        logger.error(f"Pipeline execution failed: {e}", exc_info=True)
        sys.exit(2)


def cmd_status(args):
    """Check agent/database status."""
    logger.info("ASP Platform Status")
    logger.info("-" * 40)

    # Check database
    db_path = Path(args.db_path) if args.db_path else Path("data/asp_telemetry.db")
    if db_path.exists():
        logger.info(f"Database: {db_path} (exists)")
        import sqlite3

        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM task_metadata")
        task_count = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM agent_cost_vector")
        agent_runs = cursor.fetchone()[0]
        conn.close()
        logger.info(f"  Tasks: {task_count}")
        logger.info(f"  Agent runs: {agent_runs}")
    else:
        logger.warning(f"Database: {db_path} (not found)")
        logger.info("  Run 'asp.cli init-db' to initialize")

    # Check environment
    logger.info("")
    logger.info("Environment:")
    env_vars = [
        "ANTHROPIC_API_KEY",
        "LANGFUSE_PUBLIC_KEY",
        "LANGFUSE_SECRET_KEY",
        "LANGFUSE_HOST",
    ]
    for var in env_vars:
        value = os.getenv(var)
        if value:
            # Mask sensitive values
            masked = value[:8] + "..." if len(value) > 10 else "***"
            logger.info(f"  {var}: {masked}")
        else:
            logger.info(f"  {var}: (not set)")


def cmd_init_db(args):
    """Initialize the database."""
    import sqlite3

    db_path = Path(args.db_path) if args.db_path else Path("data/asp_telemetry.db")
    sql_dir = Path("database/sqlite")

    logger.info(f"Initializing database: {db_path}")

    # Create parent directory
    db_path.parent.mkdir(parents=True, exist_ok=True)

    # Check if exists
    if db_path.exists() and not args.reset:
        logger.warning(f"Database already exists: {db_path}")
        logger.info("Use --reset to drop and recreate")
        return

    if args.reset and db_path.exists():
        logger.info("Resetting existing database...")
        db_path.unlink()

    # Read and execute SQL
    conn = sqlite3.connect(db_path)

    try:
        # Create tables
        create_tables_path = sql_dir / "create_tables.sql"
        if create_tables_path.exists():
            logger.info("Creating tables...")
            sql = create_tables_path.read_text()
            conn.executescript(sql)
        else:
            logger.error(f"SQL file not found: {create_tables_path}")
            sys.exit(1)

        # Create indexes
        create_indexes_path = sql_dir / "create_indexes.sql"
        if create_indexes_path.exists():
            logger.info("Creating indexes...")
            sql = create_indexes_path.read_text()
            conn.executescript(sql)

        # Load sample data if requested
        if args.with_sample_data:
            sample_data_path = sql_dir / "sample_data.sql"
            if sample_data_path.exists():
                logger.info("Loading sample data...")
                sql = sample_data_path.read_text()
                conn.executescript(sql)

        conn.commit()
        logger.info(f"Database initialized successfully: {db_path}")

    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        sys.exit(1)
    finally:
        conn.close()


def create_parser():
    """Create argument parser."""
    parser = argparse.ArgumentParser(
        prog="asp.cli",
        description="ASP Platform CLI - Run agent pipelines from the command line",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run a task through the pipeline
  python -m asp.cli run --task-id TASK-001 --description "Add user auth"

  # Run with auto-approve for testing
  python -m asp.cli run --task-id TEST-001 --description "Test task" --auto-approve

  # Run with database-based HITL approval (for inter-container workflow)
  python -m asp.cli run --task-id TASK-001 --description "Add feature" --hitl-database

  # Check status
  python -m asp.cli status

  # Initialize database
  python -m asp.cli init-db --with-sample-data
""",
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Run command
    run_parser = subparsers.add_parser(
        "run", help="Execute a task through TSP pipeline"
    )
    run_parser.add_argument(
        "--task-id",
        required=True,
        help="Unique task identifier (e.g., TASK-001)",
    )
    run_parser.add_argument(
        "--description",
        required=True,
        help="Task description (1-2 sentences)",
    )
    run_parser.add_argument(
        "--requirements",
        help="Detailed requirements text",
    )
    run_parser.add_argument(
        "--requirements-file",
        help="Path to file containing requirements",
    )
    run_parser.add_argument(
        "--db-path",
        help="Path to SQLite database (default: data/asp_telemetry.db)",
    )
    run_parser.add_argument(
        "--output",
        "-o",
        help="Path to save JSON results",
    )
    run_parser.add_argument(
        "--auto-approve",
        action="store_true",
        help="Auto-approve all quality gates (for testing)",
    )
    run_parser.add_argument(
        "--hitl-database",
        action="store_true",
        help="Use database-based HITL approval (for inter-container workflow)",
    )
    run_parser.add_argument(
        "--hitl-timeout",
        type=float,
        default=3600.0,
        help="HITL approval timeout in seconds (default: 3600)",
    )
    run_parser.add_argument(
        "--hitl-poll-interval",
        type=float,
        default=5.0,
        help="HITL poll interval in seconds (default: 5)",
    )
    run_parser.set_defaults(func=cmd_run)

    # Status command
    status_parser = subparsers.add_parser("status", help="Check platform status")
    status_parser.add_argument(
        "--db-path",
        help="Path to SQLite database",
    )
    status_parser.set_defaults(func=cmd_status)

    # Init-db command
    init_parser = subparsers.add_parser("init-db", help="Initialize the database")
    init_parser.add_argument(
        "--db-path",
        help="Path to SQLite database",
    )
    init_parser.add_argument(
        "--reset",
        action="store_true",
        help="Drop and recreate existing database",
    )
    init_parser.add_argument(
        "--with-sample-data",
        action="store_true",
        help="Load sample data after initialization",
    )
    init_parser.set_defaults(func=cmd_init_db)

    return parser


def main():
    """Main entry point."""
    parser = create_parser()
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(0)

    # Setup environment
    setup_environment()

    # Run command
    args.func(args)


# Create app reference for compatibility
app = create_parser()

if __name__ == "__main__":
    main()
