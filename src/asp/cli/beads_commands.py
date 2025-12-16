"""
Beads CLI Commands - Integration with Beads issue tracking.

Provides commands for:
- beads list: List open Beads issues
- beads show: Show issue details
- beads process: Process a Beads issue through ASP planning
- beads sync: Sync an ASP plan to Beads issues
- beads push: Export Beads issues to GitHub Issues
- beads pull: Import GitHub Issues to Beads
- beads gh-sync: Bidirectional GitHub sync

Usage:
    python -m asp.cli beads list
    python -m asp.cli beads process bd-abc1234
    python -m asp.cli beads process bd-abc1234 --dry-run
    python -m asp.cli beads sync artifacts/TASK-001/plan.json
    python -m asp.cli beads push --repo owner/repo
    python -m asp.cli beads pull --issue 42
    python -m asp.cli beads gh-sync

See ADR 009 for architecture details.
"""

import argparse
import logging
import sys
from pathlib import Path

logger = logging.getLogger("asp.cli.beads")


def cmd_beads_list(args):
    """List all open Beads issues."""
    from asp.utils.beads import read_issues, BeadsStatus

    root_path = Path(args.root) if args.root else Path(".")
    issues = read_issues(root_path)

    if args.all:
        open_issues = issues
    else:
        open_issues = [i for i in issues if i.status != BeadsStatus.CLOSED]

    if not open_issues:
        print("No open issues found.")
        return

    print(f"{'Open issues' if not args.all else 'All issues'} ({len(open_issues)}):\n")
    for issue in open_issues:
        # Priority markers: P0 = !!!, P1 = !!, P2 = !, P3/P4 = none
        priority_marker = "!" * max(0, 3 - issue.priority) if issue.priority < 3 else ""
        status_str = f"[{issue.status.value}]" if args.all else ""

        print(f"  [{issue.id}] {priority_marker} {issue.title} {status_str}")
        if issue.description and args.verbose:
            desc = issue.description[:60] + "..." if len(issue.description) > 60 else issue.description
            print(f"           {desc}")
        print()


def cmd_beads_process(args):
    """
    Process a Beads issue through ASP planning.

    Converts the issue to TaskRequirements and runs the PlanningAgent.
    """
    from asp.utils.beads import read_issues, BeadsStatus

    root_path = Path(args.root) if args.root else Path(".")
    issues = read_issues(root_path)

    # Find the issue
    issue = next((i for i in issues if i.id == args.issue_id), None)

    if not issue:
        logger.error(f"Issue '{args.issue_id}' not found")
        print(f"Error: Issue '{args.issue_id}' not found", file=sys.stderr)
        print(f"\nAvailable issues:", file=sys.stderr)
        for i in issues[:5]:
            print(f"  [{i.id}] {i.title}", file=sys.stderr)
        if len(issues) > 5:
            print(f"  ... and {len(issues) - 5} more", file=sys.stderr)
        sys.exit(1)

    if issue.status == BeadsStatus.CLOSED:
        logger.warning(f"Issue '{args.issue_id}' is already closed")
        print(f"Warning: Issue '{args.issue_id}' is already closed", file=sys.stderr)

    print(f"Processing issue: [{issue.id}] {issue.title}")
    print(f"Type: {issue.type.value}")
    print(f"Priority: P{issue.priority}")
    if issue.description:
        print(f"Description: {issue.description}")
    print()

    if args.dry_run:
        print("[Dry Run] Would create plan for:")
        print(f"  Task ID: {issue.id}")
        print(f"  Description: {issue.title}")
        print(f"  Requirements: {issue.description or issue.title}")
        return

    # Import planning components
    try:
        from asp.models.planning import TaskRequirements
        from asp.agents.planning_agent import PlanningAgent
    except ImportError as e:
        logger.error(f"Failed to import planning components: {e}")
        print(f"Error: Could not import planning agent: {e}", file=sys.stderr)
        print("Make sure the asp package is properly installed.", file=sys.stderr)
        sys.exit(1)

    # Convert to TaskRequirements
    requirements = TaskRequirements(
        task_id=issue.id,
        description=issue.title,
        requirements=issue.description or issue.title,
        context_files=[],
    )

    print("Generating plan...")

    try:
        agent = PlanningAgent()
        plan = agent.create_plan(requirements)

        print(f"\nPlan created with {len(plan.semantic_units)} semantic units:")
        for i, unit in enumerate(plan.semantic_units, 1):
            print(f"  {i}. [{unit.unit_id}] {unit.description}")

        if args.output:
            output_path = Path(args.output)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(plan.model_dump_json(indent=2))
            print(f"\nPlan saved to: {output_path}")

    except Exception as e:
        logger.error(f"Planning failed: {e}", exc_info=True)
        print(f"Error: Planning failed: {e}", file=sys.stderr)
        sys.exit(1)


def cmd_beads_show(args):
    """Show details of a specific Beads issue."""
    from asp.utils.beads import read_issues

    root_path = Path(args.root) if args.root else Path(".")
    issues = read_issues(root_path)

    issue = next((i for i in issues if i.id == args.issue_id), None)

    if not issue:
        print(f"Error: Issue '{args.issue_id}' not found", file=sys.stderr)
        sys.exit(1)

    print(f"ID: {issue.id}")
    print(f"Title: {issue.title}")
    print(f"Type: {issue.type.value}")
    print(f"Status: {issue.status.value}")
    print(f"Priority: P{issue.priority}")

    if issue.description:
        print(f"\nDescription:\n{issue.description}")

    if issue.labels:
        print(f"\nLabels: {', '.join(issue.labels)}")

    if issue.parent_id:
        print(f"Parent: {issue.parent_id}")

    if issue.created_at:
        print(f"\nCreated: {issue.created_at}")
    if issue.updated_at:
        print(f"Updated: {issue.updated_at}")


def cmd_beads_sync(args):
    """
    Sync an ASP plan to Beads issues.

    Creates Beads issues from semantic units in a ProjectPlan,
    with an optional epic to group them.
    """
    import json

    from asp.models.planning import ProjectPlan
    from asp.utils.beads_sync import sync_plan_to_beads

    root_path = Path(args.root) if args.root else Path(".")
    plan_path = Path(args.plan_file)

    if not plan_path.exists():
        print(f"Error: Plan file not found: {plan_path}", file=sys.stderr)
        sys.exit(1)

    # Load the plan
    try:
        with open(plan_path, "r", encoding="utf-8") as f:
            plan_data = json.load(f)
        plan = ProjectPlan.model_validate(plan_data)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in plan file: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error: Failed to parse plan: {e}", file=sys.stderr)
        sys.exit(1)

    print(f"Syncing plan: {plan.task_id}")
    print(f"  Semantic units: {len(plan.semantic_units)}")
    print(f"  Total complexity: {plan.total_est_complexity}")
    print()

    if args.dry_run:
        print("[Dry Run] Would create:")
        if not args.no_epic:
            print(f"  Epic: epic-{plan.task_id}")
        for unit in plan.semantic_units:
            print(f"  Task: {unit.unit_id} - {unit.description[:50]}...")
        return

    # Sync to beads
    created = sync_plan_to_beads(
        plan,
        create_epic=not args.no_epic,
        update_existing=args.update,
        root_path=root_path,
    )

    print(f"Synced {len(created)} issues to Beads:")
    for issue in created:
        print(f"  [{issue.id}] {issue.title[:50]}...")

    if args.list_after:
        print("\n--- Current Beads Issues ---")
        from asp.utils.beads import read_issues
        all_issues = read_issues(root_path)
        task_label = f"task-{plan.task_id}"
        plan_issues = [i for i in all_issues if task_label in i.labels]
        for issue in plan_issues:
            print(f"  [{issue.id}] [{issue.status.value}] {issue.title}")


def cmd_beads_push(args):
    """
    Push Beads issues to GitHub Issues.

    Creates GitHub Issues for Beads issues that haven't been synced yet.
    """
    from asp.utils.github_sync import push_to_github, verify_gh_cli

    if not verify_gh_cli():
        print("Error: GitHub CLI (gh) not found or not authenticated.", file=sys.stderr)
        print("Install: https://cli.github.com/", file=sys.stderr)
        print("Then run: gh auth login", file=sys.stderr)
        sys.exit(1)

    root_path = Path(args.root) if args.root else Path(".")

    print("Pushing Beads issues to GitHub...")
    if args.dry_run:
        print("[Dry Run]")

    created = push_to_github(
        repo=args.repo,
        project=args.project,
        dry_run=args.dry_run,
        root_path=root_path,
    )

    if not created:
        print("No new issues to push (all are synced or closed).")
        return

    print(f"\n{'Would create' if args.dry_run else 'Created'} {len(created)} GitHub issues:")
    for url in created:
        print(f"  {url}")


def cmd_beads_pull(args):
    """
    Pull GitHub Issues into Beads.

    Imports GitHub Issues that haven't been imported yet.
    """
    from asp.utils.github_sync import pull_from_github, verify_gh_cli

    if not verify_gh_cli():
        print("Error: GitHub CLI (gh) not found or not authenticated.", file=sys.stderr)
        print("Install: https://cli.github.com/", file=sys.stderr)
        print("Then run: gh auth login", file=sys.stderr)
        sys.exit(1)

    root_path = Path(args.root) if args.root else Path(".")

    print("Pulling GitHub Issues into Beads...")
    if args.dry_run:
        print("[Dry Run]")

    imported = pull_from_github(
        repo=args.repo,
        issue_number=args.issue,
        label_filter=args.label,
        state=args.state,
        dry_run=args.dry_run,
        root_path=root_path,
    )

    if not imported:
        print("No new issues to import.")
        return

    print(f"\n{'Would import' if args.dry_run else 'Imported'} {len(imported)} issues:")
    for issue in imported:
        print(f"  [{issue.id}] {issue.title}")


def cmd_beads_gh_sync(args):
    """
    Bidirectional sync between Beads and GitHub.

    Imports new GitHub issues, exports new Beads issues, and optionally
    resolves conflicts between linked issues.
    """
    from asp.utils.github_sync import sync_github, verify_gh_cli

    if not verify_gh_cli():
        print("Error: GitHub CLI (gh) not found or not authenticated.", file=sys.stderr)
        print("Install: https://cli.github.com/", file=sys.stderr)
        print("Then run: gh auth login", file=sys.stderr)
        sys.exit(1)

    root_path = Path(args.root) if args.root else Path(".")

    print("Syncing Beads with GitHub...")
    print(f"Conflict strategy: {args.conflict}")
    if args.dry_run:
        print("[Dry Run]")
    print()

    stats = sync_github(
        repo=args.repo,
        project=args.project,
        conflict_strategy=args.conflict,
        dry_run=args.dry_run,
        root_path=root_path,
    )

    print("\n--- Sync Summary ---")
    print(f"Imported from GitHub: {stats['imported']}")
    print(f"Exported to GitHub: {stats['exported']}")
    if not args.dry_run:
        print(f"Conflicts resolved: {stats['conflicts']}")


def add_beads_subparser(subparsers):
    """Add beads subcommand and its sub-subcommands to the parser."""
    beads_parser = subparsers.add_parser(
        "beads",
        help="Beads issue tracking integration (ADR 009)",
        description="Commands for integrating with the Beads issue tracking system.",
    )

    beads_subparsers = beads_parser.add_subparsers(
        dest="beads_command",
        help="Beads commands",
    )

    # Common arguments
    root_arg = {
        "flags": ["--root", "-r"],
        "kwargs": {
            "help": "Root path for .beads directory (default: current directory)",
        },
    }

    # beads list
    list_parser = beads_subparsers.add_parser(
        "list",
        help="List Beads issues",
    )
    list_parser.add_argument(root_arg["flags"][0], root_arg["flags"][1], **root_arg["kwargs"])
    list_parser.add_argument(
        "--all", "-a",
        action="store_true",
        help="Show all issues including closed",
    )
    list_parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Show issue descriptions",
    )
    list_parser.set_defaults(func=cmd_beads_list)

    # beads show
    show_parser = beads_subparsers.add_parser(
        "show",
        help="Show details of a Beads issue",
    )
    show_parser.add_argument(
        "issue_id",
        help="Issue ID (e.g., bd-abc1234)",
    )
    show_parser.add_argument(root_arg["flags"][0], root_arg["flags"][1], **root_arg["kwargs"])
    show_parser.set_defaults(func=cmd_beads_show)

    # beads process
    process_parser = beads_subparsers.add_parser(
        "process",
        help="Process a Beads issue through ASP planning",
    )
    process_parser.add_argument(
        "issue_id",
        help="Issue ID to process (e.g., bd-abc1234)",
    )
    process_parser.add_argument(root_arg["flags"][0], root_arg["flags"][1], **root_arg["kwargs"])
    process_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without executing",
    )
    process_parser.add_argument(
        "--output", "-o",
        help="Path to save the generated plan JSON",
    )
    process_parser.set_defaults(func=cmd_beads_process)

    # beads sync (Phase 3: Auto-sync plans to Beads)
    sync_parser = beads_subparsers.add_parser(
        "sync",
        help="Sync an ASP plan to Beads issues",
    )
    sync_parser.add_argument(
        "plan_file",
        help="Path to plan JSON file (e.g., artifacts/TASK-001/plan.json)",
    )
    sync_parser.add_argument(root_arg["flags"][0], root_arg["flags"][1], **root_arg["kwargs"])
    sync_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be created without syncing",
    )
    sync_parser.add_argument(
        "--no-epic",
        action="store_true",
        help="Don't create an epic issue for the plan",
    )
    sync_parser.add_argument(
        "--update",
        action="store_true",
        help="Update existing issues if they exist",
    )
    sync_parser.add_argument(
        "--list-after",
        action="store_true",
        help="List plan issues after syncing",
    )
    sync_parser.set_defaults(func=cmd_beads_sync)

    # beads push (Phase 4: GitHub sync)
    push_parser = beads_subparsers.add_parser(
        "push",
        help="Push Beads issues to GitHub Issues",
    )
    push_parser.add_argument(root_arg["flags"][0], root_arg["flags"][1], **root_arg["kwargs"])
    push_parser.add_argument(
        "--repo",
        help="GitHub repo (owner/name). Auto-detected if not specified.",
    )
    push_parser.add_argument(
        "--project",
        help="GitHub Project number to add issues to.",
    )
    push_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be created without pushing",
    )
    push_parser.set_defaults(func=cmd_beads_push)

    # beads pull (Phase 4: GitHub sync)
    pull_parser = beads_subparsers.add_parser(
        "pull",
        help="Pull GitHub Issues into Beads",
    )
    pull_parser.add_argument(root_arg["flags"][0], root_arg["flags"][1], **root_arg["kwargs"])
    pull_parser.add_argument(
        "--repo",
        help="GitHub repo (owner/name). Auto-detected if not specified.",
    )
    pull_parser.add_argument(
        "--issue", "-i",
        type=int,
        help="Specific issue number to import.",
    )
    pull_parser.add_argument(
        "--label", "-l",
        help="Only import issues with this label.",
    )
    pull_parser.add_argument(
        "--state", "-s",
        choices=["open", "closed", "all"],
        default="open",
        help="Issue state filter (default: open).",
    )
    pull_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be imported without creating",
    )
    pull_parser.set_defaults(func=cmd_beads_pull)

    # beads gh-sync (Phase 4: GitHub sync)
    gh_sync_parser = beads_subparsers.add_parser(
        "gh-sync",
        help="Bidirectional sync between Beads and GitHub",
    )
    gh_sync_parser.add_argument(root_arg["flags"][0], root_arg["flags"][1], **root_arg["kwargs"])
    gh_sync_parser.add_argument(
        "--repo",
        help="GitHub repo (owner/name). Auto-detected if not specified.",
    )
    gh_sync_parser.add_argument(
        "--project",
        help="GitHub Project number to add new issues to.",
    )
    gh_sync_parser.add_argument(
        "--conflict",
        choices=["local-wins", "remote-wins", "skip"],
        default="local-wins",
        help="Conflict resolution strategy (default: local-wins).",
    )
    gh_sync_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would happen without making changes",
    )
    gh_sync_parser.set_defaults(func=cmd_beads_gh_sync)

    # Set default handler for just "beads" with no subcommand
    def beads_help(args):
        beads_parser.print_help()

    beads_parser.set_defaults(func=beads_help)

    return beads_parser
