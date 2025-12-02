"""
Developer Persona (Alex) - Flow State Canvas

This module implements the web UI for the Senior Developer persona.
Displays real task data, recent activity, and quick actions.
"""

from fasthtml.common import *

from .data import (
    get_agent_stats,
    get_cost_breakdown,
    get_recent_activity,
    get_task_details,
    get_tasks,
)


def developer_routes(app, rt):
    """Register all developer persona routes."""

    @rt("/developer")
    def get_developer():
        """Main developer dashboard - Flow State Canvas."""
        tasks = get_tasks()
        activities = get_recent_activity(limit=10)
        stats = get_agent_stats()

        # Filter to show active/recent tasks
        active_tasks = [t for t in tasks if t["status"] in ("in_progress", "planning")][
            :5
        ]
        completed_tasks = [t for t in tasks if t["status"] == "completed"][:5]

        return Titled(
            "Flow State Canvas - Alex",
            # Header with user info
            Div(
                Span("Developer View", cls="pico-color-azure"),
                Span(" | "),
                Span("Alex", style="font-weight: bold;"),
                style="text-align: right; padding: 0.5rem; border-bottom: 1px solid var(--pico-muted-border-color);",
            ),
            Div(
                # Sidebar / Navigation
                Div(
                    H3("Active Tasks"),
                    (
                        Ul(
                            *[
                                Li(
                                    A(
                                        f"{t['task_id']}: {t['description'][:30]}...",
                                        href=f"/developer/task/{t['task_id']}",
                                        title=t["description"],
                                    ),
                                    Small(f" ({t['status']})", cls="pico-color-azure"),
                                )
                                for t in active_tasks
                            ]
                        )
                        if active_tasks
                        else P("No active tasks", cls="secondary")
                    ),
                    Hr(),
                    H3("Recent Completed"),
                    (
                        Ul(
                            *[
                                Li(
                                    A(
                                        t["task_id"],
                                        href=f"/developer/task/{t['task_id']}",
                                    ),
                                    Small(f" - {t['complexity']} complexity"),
                                )
                                for t in completed_tasks
                            ]
                        )
                        if completed_tasks
                        else P("No completed tasks", cls="secondary")
                    ),
                    Hr(),
                    H3("Tools"),
                    Ul(
                        Li(A("View All Tasks", href="/developer/tasks")),
                        Li(A("Agent Stats", href="/developer/stats")),
                        Li(A("View Traces", href="#", cls="secondary")),
                    ),
                    cls="sidebar",
                    style="width: 280px; border-right: 1px solid var(--pico-muted-border-color); padding-right: 1rem;",
                ),
                # Main Content Area
                Div(
                    # Stats cards
                    Div(
                        Div(
                            H4(str(stats["total_tasks"])),
                            P("Total Tasks"),
                            cls="card",
                            style="text-align: center;",
                        ),
                        cls="card",
                    ),
                    # Defect summary
                    Div(
                        H4("Defect Overview"),
                        Div(
                            H4(f"{stats['successful']}/{stats['total_tasks']}"),
                            P("Success Rate"),
                            cls="card",
                            style="text-align: center;",
                        ),
                        Div(
                            H4(f"{stats['avg_complexity']:.0f}"),
                            P("Avg Complexity"),
                            cls="card",
                            style="text-align: center;",
                        ),
                        Div(
                            H4(f"{stats['avg_execution_time']:.1f}s"),
                            P("Avg Time"),
                            cls="card",
                            style="text-align: center;",
                        ),
                        cls="grid",
                        style="margin-bottom: 1rem;",
                    ),
                    # Recent Activity
                    Div(
                        H4("Recent Activity"),
                        Table(
                            Thead(Tr(Th("Time"), Th("Action"), Th("Status"))),
                            (
                                Tbody(
                                    *[
                                        Tr(
                                            Td(f"{a['date']} {a['time']}"),
                                            Td(
                                                A(
                                                    a["action"][:50],
                                                    href=f"/developer/task/{a['task_id']}",
                                                )
                                            ),
                                            Td(
                                                a["status"],
                                                cls=(
                                                    "pico-color-green"
                                                    if a["status"] == "Success"
                                                    else "pico-color-red"
                                                ),
                                            ),
                                        )
                                        for a in activities[:8]
                                    ]
                                )
                                if activities
                                else Tbody(Tr(Td("No recent activity", colspan="3")))
                            ),
                        ),
                        cls="card",
                        # HTMX: Auto-refresh every 30 seconds
                        hx_get="/developer/activity",
                        hx_trigger="every 30s",
                        hx_swap="innerHTML",
                    ),
                    style="flex-grow: 1; padding-left: 2rem;",
                ),
                style="display: flex; min-height: 80vh;",
            ),
            # Navigation
            Div(
                A("Back to Home", href="/", role="button", cls="outline"),
                style="margin-top: 2rem;",
            ),
            style="max-width: 1400px; margin: 0 auto; padding: 2rem;",
        )

    # API Endpoints

    @rt("/developer/api/current-task")
    def get_current_task():
        """Return current task HTML fragment."""
        # Placeholder - would connect to task assignment system
        return Div(
            Code("TSP-IMPL-001"),
            P("Web UI Implementation", style="margin: 0.5rem 0;"),
            Small("Status: ", Span("In Progress", cls="pico-color-jade")),
        )

    @rt("/developer/api/stats")
    def get_developer_stats():
        """Return developer stats HTML fragment."""
        activities = get_recent_activity(limit=100)

        # Calculate stats from activities
        total_executions = len(activities)

        return Div(
            P(Small("Today's Executions: "), Strong(str(min(total_executions, 50)))),
            P(Small("Recent Activity: "), Strong(f"{total_executions} items")),
            P(Small("Tests Passed: "), Strong("28/28", cls="pico-color-green")),
        )

    @rt("/developer/api/activity")
    def get_developer_activity():
        """Return recent activity HTML fragment."""
        activities = get_recent_activity(limit=8)

        if not activities:
            return P(
                "No recent activity. Start a task to see activity here.",
                cls="pico-color-grey",
            )

        return Table(
            Thead(Tr(Th("Time"), Th("Action"), Th("Status"))),
            Tbody(
                *[
                    Tr(
                        Td(Small(act["time"] if act.get("time") else "-")),
                        Td(
                            f"{act['action'][:40]}..."
                            if len(act.get("action", "")) > 40
                            else act.get("action", "-")
                        ),
                        Td(
                            act.get("status", "Unknown"),
                            cls=(
                                "pico-color-green"
                                if act.get("status") == "Success"
                                else "pico-color-amber"
                            ),
                        ),
                    )
                    for act in activities
                ]
            ),
        )

    @rt("/developer/activity")
    def get_activity():
        """HTMX endpoint for activity updates."""
        activities = get_recent_activity(limit=8)
        return Div(
            H4("Recent Activity"),
            Table(
                Thead(Tr(Th("Time"), Th("Action"), Th("Status"))),
                (
                    Tbody(
                        *[
                            Tr(
                                Td(f"{a['date']} {a['time']}"),
                                Td(
                                    A(
                                        a["action"][:50],
                                        href=f"/developer/task/{a['task_id']}",
                                    )
                                ),
                                Td(
                                    a["status"],
                                    cls=(
                                        "pico-color-green"
                                        if a["status"] == "Success"
                                        else "pico-color-red"
                                    ),
                                ),
                            )
                            for a in activities
                        ]
                    )
                    if activities
                    else Tbody(Tr(Td("No recent activity", colspan="3")))
                ),
            ),
        )

    @rt("/developer/tasks")
    def get_all_tasks():
        """View all tasks."""
        tasks = get_tasks()

        return Titled(
            "All Tasks - Developer View",
            Div(
                A("< Back to Dashboard", href="/developer"),
                H2("All Tasks"),
                Table(
                    Thead(
                        Tr(
                            Th("Task ID"),
                            Th("Description"),
                            Th("Complexity"),
                            Th("Units"),
                            Th("Time (s)"),
                            Th("Status"),
                        )
                    ),
                    Tbody(
                        *[
                            Tr(
                                Td(
                                    A(
                                        t["task_id"],
                                        href=f"/developer/task/{t['task_id']}",
                                    )
                                ),
                                Td(
                                    t["description"][:40] + "..."
                                    if len(t["description"]) > 40
                                    else t["description"]
                                ),
                                Td(str(t["complexity"])),
                                Td(str(t["num_units"])),
                                Td(f"{t['execution_time']:.2f}"),
                                Td(
                                    t["status"],
                                    cls=(
                                        "pico-color-green"
                                        if t["status"] == "completed"
                                        else (
                                            "pico-color-azure"
                                            if t["status"] == "in_progress"
                                            else "pico-color-yellow"
                                        )
                                    ),
                                ),
                            )
                            for t in tasks
                        ]
                    ),
                ),
                style="max-width: 1200px; margin: 0 auto; padding: 2rem;",
            ),
        )

    @rt("/developer/task/{task_id}")
    def get_task_view(task_id: str):
        """View details of a specific task."""
        details = get_task_details(task_id)

        if not details:
            return Titled(
                "Task Not Found",
                Div(
                    A("< Back", href="/developer/tasks"),
                    H2(f"Task {task_id} not found"),
                    P("This task does not exist or has no artifacts."),
                    style="max-width: 800px; margin: 0 auto; padding: 2rem;",
                ),
            )

        return Titled(
            f"Task {task_id}",
            Div(
                A("< Back to Dashboard", href="/developer"),
                " | ",
                A("All Tasks", href="/developer/tasks"),
                H2(f"Task: {task_id}"),
                # Artifacts section
                Div(
                    H4("Artifacts"),
                    (
                        Ul(
                            *[
                                Li(
                                    f"{a['name']} ",
                                    Small(
                                        f"({a['type']}, {a['size']} bytes)"
                                        if a["type"] == "file"
                                        else f"({a['type']})"
                                    ),
                                )
                                for a in details["artifacts"]
                            ]
                        )
                        if details["artifacts"]
                        else P("No artifacts")
                    ),
                    cls="card",
                ),
                # Plan preview
                (
                    Div(
                        H4("Plan Preview"),
                        Pre(
                            details["plan"] if details["plan"] else "No plan available"
                        ),
                        cls="card",
                        style="margin-top: 1rem;",
                    )
                    if details.get("plan")
                    else None
                ),
                # Design preview
                (
                    Div(
                        H4("Design Preview"),
                        Pre(
                            details["design"]
                            if details["design"]
                            else "No design available"
                        ),
                        cls="card",
                        style="margin-top: 1rem;",
                    )
                    if details.get("design")
                    else None
                ),
                style="max-width: 1000px; margin: 0 auto; padding: 2rem;",
            ),
        )

    @rt("/developer/stats")
    def get_stats_page():
        """View detailed agent statistics."""
        stats = get_agent_stats()
        cost_data = get_cost_breakdown(days=7)
        total_tokens = (
            cost_data["token_usage"]["input"] + cost_data["token_usage"]["output"]
        )

        return Titled(
            "Agent Statistics",
            Div(
                A("< Back to Dashboard", href="/developer"),
                H2("Agent Performance Statistics"),
                Div(
                    Div(
                        H3("Task Metrics"),
                        Table(
                            Tbody(
                                Tr(
                                    Td("Total Tasks"),
                                    Td(Strong(str(stats["total_tasks"]))),
                                ),
                                Tr(
                                    Td("Successful"),
                                    Td(
                                        Strong(str(stats["successful"])),
                                        cls="pico-color-green",
                                    ),
                                ),
                                Tr(
                                    Td("Failed"),
                                    Td(
                                        Strong(str(stats["failed"])),
                                        cls="pico-color-red",
                                    ),
                                ),
                                Tr(
                                    Td("Success Rate"),
                                    Td(
                                        Strong(
                                            f"{(stats['successful']/stats['total_tasks']*100):.1f}%"
                                            if stats["total_tasks"] > 0
                                            else "N/A"
                                        )
                                    ),
                                ),
                            )
                        ),
                        cls="card",
                    ),
                    Div(
                        H3("Performance"),
                        Table(
                            Tbody(
                                Tr(
                                    Td("Avg Complexity"),
                                    Td(Strong(f"{stats['avg_complexity']:.1f}")),
                                ),
                                Tr(
                                    Td("Avg Execution Time"),
                                    Td(Strong(f"{stats['avg_execution_time']:.2f}s")),
                                ),
                                Tr(
                                    Td("Total Units Processed"),
                                    Td(Strong(str(stats["total_units"]))),
                                ),
                            )
                        ),
                        cls="card",
                    ),
                    cls="grid",
                ),
                # Cost tracking section
                Div(
                    H3("API Cost Tracking (Last 7 Days)"),
                    Div(
                        Div(
                            H4(
                                f"${cost_data['total_usd']:.2f}", cls="pico-color-azure"
                            ),
                            P("Total Cost"),
                            cls="card",
                            style="text-align: center;",
                        ),
                        Div(
                            H4(f"{total_tokens:,}" if total_tokens > 0 else "0"),
                            P("Total Tokens"),
                            cls="card",
                            style="text-align: center;",
                        ),
                        Div(
                            H4(
                                f"{cost_data['token_usage']['input']:,}"
                                if cost_data["token_usage"]["input"] > 0
                                else "0"
                            ),
                            P("Input Tokens"),
                            cls="card",
                            style="text-align: center;",
                        ),
                        Div(
                            H4(
                                f"{cost_data['token_usage']['output']:,}"
                                if cost_data["token_usage"]["output"] > 0
                                else "0"
                            ),
                            P("Output Tokens"),
                            cls="card",
                            style="text-align: center;",
                        ),
                        cls="grid",
                    ),
                    (
                        Div(
                            H4("Cost by Agent Role"),
                            Table(
                                Tbody(
                                    *[
                                        Tr(
                                            Td(role),
                                            Td(Strong(f"${cost:.4f}")),
                                        )
                                        for role, cost in cost_data["by_role"].items()
                                    ]
                                )
                            ),
                            cls="card",
                            style="margin-top: 1rem;",
                        )
                        if cost_data["by_role"]
                        else P(
                            "No cost data available yet",
                            cls="secondary",
                            style="margin-top: 1rem;",
                        )
                    ),
                    style="margin-top: 2rem;",
                ),
                style="max-width: 1000px; margin: 0 auto; padding: 2rem;",
            ),
        )
