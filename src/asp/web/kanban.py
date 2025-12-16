"""
Kanban Board UI Route

This module provides a Kanban board view for Beads issues.

Phase 2 of ADR 009: Adds "Plan with ASP" button integration.
"""

import logging

from fasthtml.common import *
from asp.utils.beads import read_issues, write_issues, BeadsStatus, BeadsType

logger = logging.getLogger(__name__)

# Define column mapping
COLUMNS = {
    BeadsStatus.OPEN: "Todo",
    BeadsStatus.IN_PROGRESS: "In Progress",
    BeadsStatus.CLOSED: "Done",
}

def IssueCard(issue, show_plan_button: bool = True):
    """
    Renders a single issue card with optional ASP planning button.

    Args:
        issue: BeadsIssue to render
        show_plan_button: Whether to show "Plan with ASP" button (default True)
    """
    # Use actual color values for inline styles (Tailwind dynamic classes don't work)
    priority_colors = {
        0: "#ef4444",  # red-500 - Highest
        1: "#f97316",  # orange-500
        2: "#eab308",  # yellow-500
        3: "#3b82f6",  # blue-500
        4: "#6b7280",  # gray-500 - Lowest
    }
    border_color = priority_colors.get(issue.priority, "#6b7280")

    # Build card content
    card_content = [
        Div(
            Span(f"#{issue.id}", cls="text-xs font-mono text-gray-500"),
            Span(issue.type.value, cls="text-xs px-1 rounded bg-gray-200 text-gray-700 ml-2"),
            cls="flex justify-between items-center mb-1"
        ),
        H4(issue.title, cls="text-sm font-semibold mb-1"),
        P(issue.description or "", cls="text-xs text-gray-600 line-clamp-3"),
        Div(
            *[Span(label, cls="text-[10px] bg-blue-100 text-blue-800 px-1 rounded mr-1") for label in issue.labels],
            cls="mt-2 flex flex-wrap"
        ),
    ]

    # Add "Plan with ASP" button for open issues
    if show_plan_button and issue.status == BeadsStatus.OPEN:
        card_content.append(
            Div(
                Button(
                    "Plan with ASP",
                    hx_post=f"/kanban/process/{issue.id}",
                    hx_swap="outerHTML",
                    hx_target=f"#card-{issue.id}",
                    hx_indicator=f"#loading-{issue.id}",
                    cls="text-xs bg-blue-500 text-white px-2 py-1 rounded hover:bg-blue-600 cursor-pointer",
                ),
                Span("Processing...", id=f"loading-{issue.id}", cls="htmx-indicator text-xs text-gray-500 ml-2"),
                cls="mt-2 pt-2 border-t border-gray-200"
            )
        )

    return Div(
        *card_content,
        id=f"card-{issue.id}",
        cls="bg-white p-3 rounded shadow border-l-4 mb-3 hover:shadow-md transition-shadow",
        style=f"border-left-color: {border_color};"
    )

def KanbanColumn(status, title, issues):
    """
    Renders a single Kanban column.
    """
    column_issues = [i for i in issues if i.status == status]
    return Div(
        H3(f"{title} ({len(column_issues)})", cls="font-bold text-gray-700 mb-3"),
        Div(
            *[IssueCard(i) for i in column_issues],
            cls="space-y-2 min-h-[200px]"
        ),
        cls="bg-gray-100 p-4 rounded-lg w-1/3 min-w-[300px] flex-shrink-0"
    )

def KanbanBoard():
    """
    Renders the full Kanban board.
    """
    issues = read_issues()
    return Div(
        Div(
            H1("Beads Kanban", cls="text-2xl font-bold text-gray-800"),
            A("Refresh", href="/kanban", cls="text-sm text-blue-600 hover:underline"),
            cls="flex justify-between items-center mb-6"
        ),
        Div(
            KanbanColumn(BeadsStatus.OPEN, "Todo", issues),
            KanbanColumn(BeadsStatus.IN_PROGRESS, "In Progress", issues),
            KanbanColumn(BeadsStatus.CLOSED, "Done", issues),
            cls="flex gap-4 overflow-x-auto pb-4"
        ),
        cls="p-6 h-full"
    )

def PlanSuccessCard(issue, plan):
    """
    Renders a success card after planning is complete.

    Args:
        issue: The processed BeadsIssue
        plan: The generated ProjectPlan
    """
    priority_colors = {
        0: "#ef4444", 1: "#f97316", 2: "#eab308", 3: "#3b82f6", 4: "#6b7280",
    }
    border_color = priority_colors.get(issue.priority, "#6b7280")

    # Show first 3 semantic units
    unit_items = [
        Li(f"[{u.unit_id}] {u.description[:60]}{'...' if len(u.description) > 60 else ''}",
           cls="text-xs text-gray-700")
        for u in plan.semantic_units[:3]
    ]

    more_text = ""
    if len(plan.semantic_units) > 3:
        more_text = f"... and {len(plan.semantic_units) - 3} more units"

    return Div(
        Div(
            Span(f"#{issue.id}", cls="text-xs font-mono text-gray-500"),
            Span(issue.type.value, cls="text-xs px-1 rounded bg-gray-200 text-gray-700 ml-2"),
            Span("IN_PROGRESS", cls="text-xs px-1 rounded bg-yellow-200 text-yellow-800 ml-2"),
            cls="flex items-center mb-1"
        ),
        H4(issue.title, cls="text-sm font-semibold mb-1"),
        Div(
            Div(
                Span("✓ Plan created", cls="text-green-600 font-semibold text-sm"),
                Span(f"{len(plan.semantic_units)} units", cls="text-xs text-gray-500 ml-2"),
                Span(f"C={plan.total_est_complexity}", cls="text-xs text-gray-500 ml-2"),
                cls="mb-2"
            ),
            Ul(*unit_items, cls="list-disc list-inside"),
            Small(more_text, cls="text-gray-500") if more_text else None,
            cls="bg-green-50 p-2 rounded text-xs"
        ),
        id=f"card-{issue.id}",
        cls="bg-white p-3 rounded shadow border-l-4 mb-3",
        style=f"border-left-color: {border_color};"
    )


def PlanErrorCard(issue, error_message: str):
    """
    Renders an error card when planning fails.

    Args:
        issue: The BeadsIssue that failed
        error_message: Error description
    """
    priority_colors = {
        0: "#ef4444", 1: "#f97316", 2: "#eab308", 3: "#3b82f6", 4: "#6b7280",
    }
    border_color = priority_colors.get(issue.priority, "#6b7280")

    return Div(
        Div(
            Span(f"#{issue.id}", cls="text-xs font-mono text-gray-500"),
            Span(issue.type.value, cls="text-xs px-1 rounded bg-gray-200 text-gray-700 ml-2"),
            cls="flex items-center mb-1"
        ),
        H4(issue.title, cls="text-sm font-semibold mb-1"),
        Div(
            Span("✗ Planning failed", cls="text-red-600 font-semibold text-sm"),
            P(error_message, cls="text-xs text-red-500 mt-1"),
            Button(
                "Retry",
                hx_post=f"/kanban/process/{issue.id}",
                hx_swap="outerHTML",
                hx_target=f"#card-{issue.id}",
                cls="text-xs bg-red-500 text-white px-2 py-1 rounded hover:bg-red-600 cursor-pointer mt-2",
            ),
            cls="bg-red-50 p-2 rounded"
        ),
        id=f"card-{issue.id}",
        cls="bg-white p-3 rounded shadow border-l-4 mb-3",
        style=f"border-left-color: {border_color};"
    )


def kanban_routes(app):
    @app.get("/kanban")
    def get_kanban():
        return Title("Beads Kanban"), KanbanBoard()

    @app.post("/kanban/process/{issue_id}")
    async def process_issue(issue_id: str):
        """
        Process an issue through ASP planning and return updated card.

        This is the Phase 2 ADR 009 endpoint that:
        1. Finds the issue by ID
        2. Converts it to TaskRequirements
        3. Runs PlanningAgent to generate a plan
        4. Updates issue status to IN_PROGRESS
        5. Returns success card with plan summary
        """
        from asp.models.planning import TaskRequirements

        issues = read_issues()
        issue = next((i for i in issues if i.id == issue_id), None)

        if not issue:
            return Div(
                Span(f"Issue {issue_id} not found", cls="text-red-500"),
                id=f"card-{issue_id}",
                cls="bg-red-50 p-3 rounded"
            )

        try:
            # Import planning agent
            from asp.agents.planning_agent import PlanningAgent

            # Convert issue to TaskRequirements
            requirements = TaskRequirements(
                task_id=issue.id,
                description=issue.title,
                requirements=issue.description or issue.title,
                context_files=[],
            )

            logger.info("Processing issue %s: %s", issue.id, issue.title)

            # Create plan
            agent = PlanningAgent()
            plan = agent.create_plan(requirements)

            logger.info("Plan created for %s: %d units", issue.id, len(plan.semantic_units))

            # Update issue status
            issue.status = BeadsStatus.IN_PROGRESS
            write_issues(issues)

            return PlanSuccessCard(issue, plan)

        except Exception as e:
            logger.error("Planning failed for %s: %s", issue.id, str(e))
            return PlanErrorCard(issue, str(e))
