"""
ASP CLI - Main entry point for command-line agent execution.

Provides commands for:
- run: Execute a task through the TSP pipeline
- repair: Execute repair workflow on existing code
- status: Check agent/task status
- init-db: Initialize the database

Usage:
    python -m asp.cli run --task-id TASK-001 --description "Add feature X"
    python -m asp.cli repair --task-id REPAIR-001 --workspace /path/to/repo
    python -m asp.cli status
    python -m asp.cli init-db

Author: ASP Development Team
Date: December 2025
"""

# pylint: disable=logging-fstring-interpolation,too-many-statements

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


def cmd_repair(args):
    """Execute repair workflow on existing code."""
    import asyncio
    from datetime import datetime

    from asp.models.execution import SandboxConfig
    from asp.orchestrators.hitl_config import AUTONOMOUS_CONFIG, HITLConfig
    from asp.orchestrators.repair_orchestrator import RepairOrchestrator, RepairRequest
    from asp.orchestrators.types import RepairExecutionResult
    from services.sandbox_executor import SubprocessSandboxExecutor
    from services.surgical_editor import SurgicalEditor
    from services.test_executor import TestExecutor
    from services.workspace_manager import Workspace

    logger.info("=" * 60)
    logger.info("ASP CLI - Repair Workflow")
    logger.info("=" * 60)

    # Validate workspace path
    workspace_path = Path(args.workspace)
    if not workspace_path.exists():
        logger.error(f"Workspace path does not exist: {workspace_path}")
        sys.exit(1)

    logger.info(f"Task ID: {args.task_id}")
    logger.info(f"Workspace: {workspace_path}")
    logger.info(f"Max iterations: {args.max_iterations}")
    logger.info("-" * 60)

    # Create workspace object
    workspace = Workspace(
        task_id=args.task_id,
        path=workspace_path,
        target_repo_path=workspace_path,
        asp_path=workspace_path / ".asp",
        created_at=datetime.now(),
    )

    # Create workspace .asp directory if it doesn't exist
    workspace.asp_path.mkdir(parents=True, exist_ok=True)

    # Configure HITL
    if args.auto_approve:
        hitl_config = AUTONOMOUS_CONFIG
        logger.warning("Auto-approve mode - all repairs will proceed automatically")
        approval_callback = None
    else:
        # Use threshold mode for manual approval
        hitl_config = HITLConfig(
            mode="threshold",
            require_approval_after_iterations=args.hitl_threshold_iterations,
            require_approval_for_confidence_below=args.hitl_threshold_confidence,
        )

        def approval_callback(reason, confidence, files, iteration):
            logger.warning(f"HITL Approval Required (iteration {iteration}):")
            logger.warning(f"  Reason: {reason}")
            logger.warning(f"  Confidence: {confidence:.2f}")
            logger.warning(f"  Files: {', '.join(files)}")
            # In interactive mode, we would prompt the user
            # For now, reject to require explicit --auto-approve
            logger.error(
                "No interactive approval - use --auto-approve or configure HITL"
            )
            return False

    # Create services
    db_path = Path(args.db_path) if args.db_path else Path("data/asp_telemetry.db")
    sandbox_config = SandboxConfig(
        timeout_seconds=args.timeout,
        memory_limit_mb=512,
    )
    sandbox = SubprocessSandboxExecutor(config=sandbox_config)
    test_executor = TestExecutor(sandbox=sandbox)
    surgical_editor = SurgicalEditor(workspace_path=workspace_path)

    # Create orchestrator
    orchestrator = RepairOrchestrator(
        sandbox=sandbox,
        test_executor=test_executor,
        surgical_editor=surgical_editor,
        db_path=db_path,
    )

    # Build repair request
    request = RepairRequest(
        task_id=args.task_id,
        workspace=workspace,
        issue_description=args.issue_description,
        target_tests=args.target_tests.split(",") if args.target_tests else None,
        max_iterations=args.max_iterations,
        test_command=args.test_command,
        hitl_config=hitl_config,
    )

    start_time = datetime.now()

    try:
        # Run repair workflow
        if args.dry_run:
            logger.info("DRY RUN - Previewing changes without applying")
            diagnostic, repair_output, diff = asyncio.run(orchestrator.dry_run(request))
            logger.info("=" * 60)
            logger.info("DRY RUN RESULTS")
            logger.info("=" * 60)
            logger.info(f"Issue Type: {diagnostic.issue_type.value}")
            logger.info(f"Root Cause: {diagnostic.root_cause}")
            logger.info(f"Changes: {len(repair_output.changes)}")
            logger.info("")
            logger.info("DIFF PREVIEW:")
            logger.info(diff)
            sys.exit(0)

        result = asyncio.run(orchestrator.repair(request, approval_callback))

        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()

        # Determine overall status
        if result.success:
            overall_status = "PASS"
        elif result.escalated_to_human:
            overall_status = "ESCALATED"
        else:
            overall_status = "FAIL"

        logger.info("=" * 60)
        logger.info("REPAIR COMPLETE")
        logger.info("=" * 60)
        logger.info(f"Overall Status: {overall_status}")
        logger.info(f"Success: {result.success}")
        logger.info(f"Iterations Used: {result.iterations_used}")
        logger.info(f"Changes Made: {len(result.changes_made)}")
        logger.info(f"Duration: {duration:.1f}s")

        if result.escalation_reason:
            logger.info(f"Escalation Reason: {result.escalation_reason}")

        # Save result if output path specified
        if args.output:
            execution_result = RepairExecutionResult(
                task_id=args.task_id,
                timestamp=start_time,
                overall_status=overall_status,
                repair_result=result,
                total_duration_seconds=duration,
                execution_log=[],
            )
            _save_result(execution_result, args.output)

        sys.exit(0 if result.success else 1)

    except Exception as e:  # pylint: disable=broad-exception-caught
        logger.error(f"Repair workflow failed: {e}", exc_info=True)
        sys.exit(2)
    finally:
        orchestrator.cleanup()


def cmd_repair_issue(args):
    """Execute repair workflow from a GitHub issue."""
    import asyncio
    from datetime import datetime

    from asp.models.execution import SandboxConfig
    from asp.orchestrators.hitl_config import AUTONOMOUS_CONFIG, HITLConfig
    from asp.orchestrators.repair_orchestrator import (
        GitHubRepairRequest,
        RepairOrchestrator,
    )
    from asp.orchestrators.types import RepairExecutionResult
    from services.github_service import GitHubService
    from services.sandbox_executor import SubprocessSandboxExecutor
    from services.surgical_editor import SurgicalEditor
    from services.test_executor import TestExecutor

    logger.info("=" * 60)
    logger.info("ASP CLI - Repair from GitHub Issue")
    logger.info("=" * 60)

    # Verify GitHub CLI
    github_service = GitHubService()
    try:
        github_service.verify_gh_installed()
        github_service.verify_gh_authenticated()
    except Exception as e:
        logger.error(f"GitHub CLI error: {e}")
        sys.exit(1)

    logger.info(f"Issue URL: {args.issue_url}")
    logger.info(f"Workspace base: {args.workspace_base}")
    logger.info(f"Max iterations: {args.max_iterations}")
    logger.info(f"Create PR: {not args.no_pr}")
    logger.info(f"Draft PR: {args.draft}")
    logger.info("-" * 60)

    workspace_base = Path(args.workspace_base)
    workspace_base.mkdir(parents=True, exist_ok=True)

    # Configure HITL
    if args.auto_approve:
        hitl_config = AUTONOMOUS_CONFIG
        logger.warning("Auto-approve mode - all repairs will proceed automatically")
        approval_callback = None
    else:
        hitl_config = HITLConfig(
            mode="threshold",
            require_approval_after_iterations=args.hitl_threshold_iterations,
            require_approval_for_confidence_below=args.hitl_threshold_confidence,
        )

        def approval_callback(reason, confidence, files, iteration):
            logger.warning(f"HITL Approval Required (iteration {iteration}):")
            logger.warning(f"  Reason: {reason}")
            logger.warning(f"  Confidence: {confidence:.2f}")
            logger.warning(f"  Files: {', '.join(files)}")
            logger.error(
                "No interactive approval - use --auto-approve or configure HITL"
            )
            return False

    # We need a temporary workspace to initialize the orchestrator
    # The actual workspace will be created by repair_from_issue
    temp_workspace = workspace_base / ".temp"
    temp_workspace.mkdir(parents=True, exist_ok=True)

    # Create services
    db_path = Path(args.db_path) if args.db_path else Path("data/asp_telemetry.db")
    sandbox_config = SandboxConfig(
        timeout_seconds=args.timeout,
        memory_limit_mb=512,
    )
    sandbox = SubprocessSandboxExecutor(config=sandbox_config)
    test_executor = TestExecutor(sandbox=sandbox)
    surgical_editor = SurgicalEditor(workspace_path=temp_workspace)

    # Create orchestrator
    orchestrator = RepairOrchestrator(
        sandbox=sandbox,
        test_executor=test_executor,
        surgical_editor=surgical_editor,
        db_path=db_path,
    )

    # Build GitHub repair request
    github_request = GitHubRepairRequest(
        issue_url=args.issue_url,
        workspace_base=workspace_base,
        max_iterations=args.max_iterations,
        create_pr=not args.no_pr,
        draft_pr=args.draft,
        test_command=args.test_command,
        hitl_config=hitl_config,
    )

    start_time = datetime.now()

    try:
        result = asyncio.run(
            orchestrator.repair_from_issue(
                github_request, github_service, approval_callback
            )
        )

        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()

        # Determine overall status
        if result.repair_result.success:
            overall_status = "PASS"
        elif result.repair_result.escalated_to_human:
            overall_status = "ESCALATED"
        else:
            overall_status = "FAIL"

        logger.info("=" * 60)
        logger.info("REPAIR FROM ISSUE COMPLETE")
        logger.info("=" * 60)
        logger.info(f"Issue: #{result.issue.number} - {result.issue.title}")
        logger.info(f"Overall Status: {overall_status}")
        logger.info(f"Success: {result.repair_result.success}")
        logger.info(f"Iterations Used: {result.repair_result.iterations_used}")
        logger.info(f"Branch: {result.branch}")
        logger.info(f"Workspace: {result.workspace_path}")
        logger.info(f"Duration: {duration:.1f}s")

        if result.pr:
            logger.info(f"PR Created: {result.pr.url}")

        if result.repair_result.escalation_reason:
            logger.info(f"Escalation Reason: {result.repair_result.escalation_reason}")

        # Save result if output path specified
        if args.output:
            execution_result = RepairExecutionResult(
                task_id=f"{result.issue.owner}/{result.issue.repo}#{result.issue.number}",
                timestamp=start_time,
                overall_status=overall_status,
                repair_result=result.repair_result,
                total_duration_seconds=duration,
                execution_log=[],
            )
            _save_result(execution_result, args.output)

        sys.exit(0 if result.repair_result.success else 1)

    except Exception as e:  # pylint: disable=broad-exception-caught
        logger.error(f"Repair from issue failed: {e}", exc_info=True)
        sys.exit(2)
    finally:
        orchestrator.cleanup()


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

  # Repair existing code with failing tests
  python -m asp.cli repair --task-id REPAIR-001 --workspace ./my-project --auto-approve

  # Preview repair without applying changes
  python -m asp.cli repair --task-id REPAIR-001 --workspace ./my-project --dry-run

  # Repair from a GitHub issue (ADR 007)
  python -m asp.cli repair-issue https://github.com/owner/repo/issues/123 --auto-approve

  # Repair from issue without creating PR
  python -m asp.cli repair-issue https://github.com/owner/repo/issues/123 --no-pr

  # Check status
  python -m asp.cli status

  # Initialize database
  python -m asp.cli init-db --with-sample-data

  # Beads integration (ADR 009)
  python -m asp.cli beads list                     # List open issues
  python -m asp.cli beads show bd-abc1234          # Show issue details
  python -m asp.cli beads process bd-abc1234       # Process issue through ASP
  python -m asp.cli beads process bd-abc1234 --dry-run  # Preview without executing
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

    # Repair command
    repair_parser = subparsers.add_parser(
        "repair", help="Execute repair workflow on existing code"
    )
    repair_parser.add_argument(
        "--task-id",
        required=True,
        help="Unique task identifier for this repair (e.g., REPAIR-001)",
    )
    repair_parser.add_argument(
        "--workspace",
        required=True,
        help="Path to workspace/repository to repair",
    )
    repair_parser.add_argument(
        "--issue-description",
        help="Description of the issue to fix (optional, will auto-detect from tests)",
    )
    repair_parser.add_argument(
        "--target-tests",
        help="Comma-separated list of specific test files/patterns to run",
    )
    repair_parser.add_argument(
        "--test-command",
        help="Custom test command (default: pytest -v)",
    )
    repair_parser.add_argument(
        "--max-iterations",
        type=int,
        default=5,
        help="Maximum repair iterations (default: 5)",
    )
    repair_parser.add_argument(
        "--timeout",
        type=int,
        default=300,
        help="Test execution timeout in seconds (default: 300)",
    )
    repair_parser.add_argument(
        "--db-path",
        help="Path to SQLite database (default: data/asp_telemetry.db)",
    )
    repair_parser.add_argument(
        "--output",
        "-o",
        help="Path to save JSON results",
    )
    repair_parser.add_argument(
        "--auto-approve",
        action="store_true",
        help="Auto-approve all repairs (run autonomously)",
    )
    repair_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview changes without applying them",
    )
    repair_parser.add_argument(
        "--hitl-threshold-iterations",
        type=int,
        default=2,
        help="Request approval after this many iterations (default: 2)",
    )
    repair_parser.add_argument(
        "--hitl-threshold-confidence",
        type=float,
        default=0.7,
        help="Request approval if confidence below this (default: 0.7)",
    )
    repair_parser.set_defaults(func=cmd_repair)

    # Repair-issue command (GitHub integration - ADR 007)
    repair_issue_parser = subparsers.add_parser(
        "repair-issue", help="Repair a bug from a GitHub issue (clone, fix, PR)"
    )
    repair_issue_parser.add_argument(
        "issue_url",
        help="GitHub issue URL (e.g., https://github.com/owner/repo/issues/123)",
    )
    repair_issue_parser.add_argument(
        "--workspace-base",
        default="/tmp/asp-repairs",
        help="Base directory for cloned workspaces (default: /tmp/asp-repairs)",
    )
    repair_issue_parser.add_argument(
        "--max-iterations",
        type=int,
        default=5,
        help="Maximum repair iterations (default: 5)",
    )
    repair_issue_parser.add_argument(
        "--timeout",
        type=int,
        default=300,
        help="Test execution timeout in seconds (default: 300)",
    )
    repair_issue_parser.add_argument(
        "--test-command",
        help="Custom test command (default: auto-detect)",
    )
    repair_issue_parser.add_argument(
        "--no-pr",
        action="store_true",
        help="Don't create a PR after successful repair",
    )
    repair_issue_parser.add_argument(
        "--draft/--no-draft",
        dest="draft",
        default=True,
        action="store_true",
        help="Create PR as draft (default: True)",
    )
    repair_issue_parser.add_argument(
        "--db-path",
        help="Path to SQLite database (default: data/asp_telemetry.db)",
    )
    repair_issue_parser.add_argument(
        "--output",
        "-o",
        help="Path to save JSON results",
    )
    repair_issue_parser.add_argument(
        "--auto-approve",
        action="store_true",
        help="Auto-approve all repairs (run autonomously)",
    )
    repair_issue_parser.add_argument(
        "--hitl-threshold-iterations",
        type=int,
        default=2,
        help="Request approval after this many iterations (default: 2)",
    )
    repair_issue_parser.add_argument(
        "--hitl-threshold-confidence",
        type=float,
        default=0.7,
        help="Request approval if confidence below this (default: 0.7)",
    )
    repair_issue_parser.set_defaults(func=cmd_repair_issue)

    # Status command
    status_parser = subparsers.add_parser("status", help="Check platform status")
    status_parser.add_argument(
        "--db-path",
        help="Path to SQLite database",
    )
    status_parser.set_defaults(func=cmd_status)

    # Beads commands (ADR 009)
    from asp.cli.beads_commands import add_beads_subparser
    add_beads_subparser(subparsers)

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
