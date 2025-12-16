"""
Beads Sync Module - Sync ASP plans to Beads issues.

This module provides utilities for synchronizing ASP ProjectPlans to Beads issues,
enabling task tracking through the Kanban UI.

See ADR 009 Phase 3 for architecture details.
"""

import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from asp.models.planning import ProjectPlan, SemanticUnit
from asp.utils.beads import (
    BeadsIssue,
    BeadsStatus,
    BeadsType,
    generate_beads_id,
    read_issues,
    write_issues,
)

logger = logging.getLogger(__name__)


def sync_plan_to_beads(
    plan: ProjectPlan,
    create_epic: bool = True,
    update_existing: bool = False,
    root_path: Path = Path("."),
) -> list[BeadsIssue]:
    """
    Create Beads issues from an ASP ProjectPlan.

    Converts semantic units from a plan into trackable Beads issues.
    Optionally creates an epic issue to group all tasks.

    Args:
        plan: The ProjectPlan to sync
        create_epic: If True, create an epic issue for the main task
        update_existing: If True, update existing issues with same IDs
        root_path: Root path for .beads directory

    Returns:
        List of created/updated BeadsIssues

    Example:
        >>> plan = planning_agent.execute(requirements)
        >>> issues = sync_plan_to_beads(plan)
        >>> print(f"Created {len(issues)} issues")
    """
    created_issues = []
    existing_issues = read_issues(root_path)
    existing_ids = {i.id for i in existing_issues}

    now = _now()

    # Create epic for the plan if requested
    epic_id = None
    if create_epic:
        epic_id = f"epic-{plan.task_id}"

        if epic_id in existing_ids:
            if update_existing:
                # Update existing epic
                for issue in existing_issues:
                    if issue.id == epic_id:
                        issue.title = f"[Epic] {plan.task_id}"
                        issue.description = _format_epic_description(plan)
                        issue.updated_at = now
                        created_issues.append(issue)
                        logger.info("Updated existing epic: %s", epic_id)
                        break
            else:
                logger.warning("Epic %s already exists, skipping", epic_id)
        else:
            epic = BeadsIssue(
                id=epic_id,
                title=f"[Epic] {plan.task_id}",
                description=_format_epic_description(plan),
                type=BeadsType.EPIC,
                status=BeadsStatus.OPEN,
                priority=1,
                labels=["asp-plan", f"task-{plan.task_id}"],
                created_at=now,
                updated_at=now,
            )
            existing_issues.append(epic)
            created_issues.append(epic)
            logger.info("Created epic: %s", epic_id)

    # Create task issues for each semantic unit
    for unit in plan.semantic_units:
        task_id = _unit_to_beads_id(unit, plan.task_id)

        if task_id in existing_ids:
            if update_existing:
                # Update existing task
                for issue in existing_issues:
                    if issue.id == task_id:
                        issue.title = unit.description
                        issue.description = _format_unit_description(unit)
                        issue.priority = _complexity_to_priority(unit.est_complexity)
                        issue.updated_at = now
                        created_issues.append(issue)
                        logger.info("Updated existing task: %s", task_id)
                        break
            else:
                logger.debug("Task %s already exists, skipping", task_id)
            continue

        task = BeadsIssue(
            id=task_id,
            title=unit.description,
            description=_format_unit_description(unit),
            type=BeadsType.TASK,
            status=BeadsStatus.OPEN,
            priority=_complexity_to_priority(unit.est_complexity),
            parent_id=epic_id,
            labels=_unit_labels(unit, plan.task_id),
            created_at=now,
            updated_at=now,
        )
        existing_issues.append(task)
        created_issues.append(task)
        logger.debug("Created task: %s - %s", task_id, unit.description[:50])

    # Write all issues
    write_issues(existing_issues, root_path)

    logger.info(
        "Synced plan %s to Beads: %d issues created/updated",
        plan.task_id,
        len(created_issues),
    )

    return created_issues


def get_plan_issues(
    plan: ProjectPlan,
    root_path: Path = Path("."),
) -> list[BeadsIssue]:
    """
    Get existing Beads issues for a plan.

    Args:
        plan: The ProjectPlan to look up
        root_path: Root path for .beads directory

    Returns:
        List of BeadsIssues associated with this plan
    """
    existing_issues = read_issues(root_path)
    task_label = f"task-{plan.task_id}"

    return [i for i in existing_issues if task_label in i.labels]


def update_unit_status(
    unit_id: str,
    status: BeadsStatus,
    root_path: Path = Path("."),
) -> Optional[BeadsIssue]:
    """
    Update the status of a semantic unit's Beads issue.

    Args:
        unit_id: The semantic unit ID (e.g., 'su-a3f42bc')
        status: New BeadsStatus
        root_path: Root path for .beads directory

    Returns:
        Updated BeadsIssue, or None if not found
    """
    issues = read_issues(root_path)
    now = _now()

    # Create the label we're looking for (e.g., "unit-su-a3f42bc")
    unit_label = f"unit-{unit_id}"

    for issue in issues:
        # Match by unit label or by beads ID containing the unit hash
        # e.g., bd-a000001 matches su-a000001
        unit_hash = unit_id[3:] if unit_id.startswith("su-") else unit_id
        if unit_label in issue.labels or issue.id == f"bd-{unit_hash}":
            issue.status = status
            issue.updated_at = now
            if status == BeadsStatus.CLOSED:
                issue.closed_at = now
            write_issues(issues, root_path)
            logger.info("Updated %s status to %s", issue.id, status.value)
            return issue

    logger.warning("No issue found for unit %s", unit_id)
    return None


# =============================================================================
# Helper Functions
# =============================================================================


def _now() -> str:
    """Return current time in ISO format."""
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _unit_to_beads_id(unit: SemanticUnit, task_id: str) -> str:
    """
    Generate a Beads ID for a semantic unit.

    Uses a deterministic approach based on task_id and unit_id
    to allow re-running sync without duplicates.
    """
    # Use unit_id directly if it's already hash-based
    if unit.unit_id.startswith("su-"):
        return f"bd-{unit.unit_id[3:]}"  # bd-a3f42bc from su-a3f42bc

    # For legacy IDs (SU-001), create a composite ID
    return f"bd-{task_id}-{unit.unit_id}".lower().replace(" ", "-")


def _complexity_to_priority(complexity: int) -> int:
    """
    Convert complexity score to Beads priority (0=highest, 4=lowest).

    Higher complexity = higher priority (needs more attention).
    """
    if complexity >= 40:
        return 0  # Highest - very complex
    elif complexity >= 25:
        return 1
    elif complexity >= 15:
        return 2  # Medium
    elif complexity >= 8:
        return 3
    else:
        return 4  # Lowest - simple


def _format_epic_description(plan: ProjectPlan) -> str:
    """Format the epic description with plan summary."""
    lines = [
        f"**Task ID:** {plan.task_id}",
        f"**Total Complexity:** {plan.total_est_complexity}",
        f"**Semantic Units:** {len(plan.semantic_units)}",
        "",
        "## Units",
    ]

    for unit in plan.semantic_units:
        lines.append(f"- [{unit.unit_id}] {unit.description} (C={unit.est_complexity})")

    return "\n".join(lines)


def _format_unit_description(unit: SemanticUnit) -> str:
    """Format the unit description with complexity details."""
    lines = [
        f"**Unit ID:** {unit.unit_id}",
        f"**Complexity:** {unit.est_complexity}",
        "",
        "## Complexity Factors",
        f"- API Interactions: {unit.api_interactions}",
        f"- Data Transformations: {unit.data_transformations}",
        f"- Logical Branches: {unit.logical_branches}",
        f"- Code Entities: {unit.code_entities_modified}",
        f"- Novelty: {unit.novelty_multiplier}x",
    ]

    if unit.dependencies:
        lines.append("")
        lines.append("## Dependencies")
        for dep in unit.dependencies:
            lines.append(f"- {dep}")

    return "\n".join(lines)


def _unit_labels(unit: SemanticUnit, task_id: str) -> list[str]:
    """Generate labels for a semantic unit issue."""
    labels = [
        "asp-unit",
        f"task-{task_id}",
        f"unit-{unit.unit_id}",
        f"complexity-{unit.est_complexity}",
    ]

    # Add complexity category
    if unit.est_complexity >= 25:
        labels.append("high-complexity")
    elif unit.est_complexity >= 15:
        labels.append("medium-complexity")
    else:
        labels.append("low-complexity")

    return labels
