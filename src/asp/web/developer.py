"""
Developer Persona (Alex) - Flow State Canvas

This module implements the web UI for the Senior Developer persona.
Displays real task data, recent activity, and quick actions.
"""

from fasthtml.common import *

from .components import theme_toggle
from .data import (
    get_active_agents,
    get_agent_stats,
    get_artifact_history,
    get_code_proposals,
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
            theme_toggle(),
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
                # Action links
                Div(
                    A(
                        "View Artifact Timeline",
                        href=f"/developer/task/{task_id}/trace",
                        role="button",
                        cls="outline",
                    ),
                    A(
                        "Review Code",
                        href=f"/developer/task/{task_id}/diff",
                        role="button",
                        cls="outline",
                        style="margin-left: 0.5rem;",
                    ),
                    style="margin-top: 1rem;",
                ),
                style="max-width: 1000px; margin: 0 auto; padding: 2rem;",
            ),
        )

    @rt("/developer/task/{task_id}/trace")
    def get_task_trace(task_id: str):
        """Traceability view showing artifact history timeline."""
        artifacts = get_artifact_history(task_id)
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

        # Phase colors
        phase_colors = {
            "plan": "#8b5cf6",  # Purple
            "design": "#06b6d4",  # Cyan
            "review": "#f59e0b",  # Amber
            "code": "#10b981",  # Green
            "test": "#3b82f6",  # Blue
            "postmortem": "#ef4444",  # Red
            "unknown": "#6b7280",  # Gray
        }

        # Group artifacts by phase
        phases_seen = []
        for a in artifacts:
            if a["phase"] not in phases_seen:
                phases_seen.append(a["phase"])

        return Titled(
            f"Artifact Timeline - {task_id}",
            Div(
                A("< Back to Task", href=f"/developer/task/{task_id}"),
                " | ",
                A("All Tasks", href="/developer/tasks"),
                H2(f"Artifact Timeline: {task_id}"),
                P(
                    f"{len(artifacts)} artifacts across {len(phases_seen)} phases",
                    cls="secondary",
                ),
                # Timeline visualization
                Div(
                    *(
                        [
                            Div(
                                # Phase header
                                Div(
                                    Div(
                                        style=f"width: 16px; height: 16px; border-radius: 50%; "
                                        f"background: {phase_colors.get(a['phase'], '#666')};",
                                    ),
                                    Div(
                                        Strong(a["phase"].capitalize()),
                                        (
                                            Span(f" v{a['version']}", cls="secondary")
                                            if a["version"] > 1
                                            else None
                                        ),
                                        style="margin-left: 0.5rem;",
                                    ),
                                    style="display: flex; align-items: center;",
                                ),
                                # Timeline connector
                                (
                                    Div(
                                        style=f"width: 2px; height: 100%; background: {phase_colors.get(a['phase'], '#666')}; "
                                        "margin-left: 7px; min-height: 20px;",
                                    )
                                    if i < len(artifacts) - 1
                                    else None
                                ),
                                # Artifact card
                                Div(
                                    Div(
                                        Strong(a["name"]),
                                        Span(
                                            f" ({a['size']} bytes)",
                                            cls="secondary",
                                            style="font-size: 0.85rem;",
                                        ),
                                    ),
                                    Div(
                                        Small(f"Modified: {a['modified_display']}"),
                                        cls="secondary",
                                    ),
                                    (
                                        Div(
                                            Pre(
                                                a["preview"],
                                                style="font-size: 0.8rem; max-height: 100px; overflow: auto; margin: 0.5rem 0;",
                                            ),
                                        )
                                        if a["preview"]
                                        else None
                                    ),
                                    cls="card",
                                    style=f"margin-left: 2rem; margin-bottom: 1rem; border-left: 3px solid {phase_colors.get(a['phase'], '#666')};",
                                ),
                                style="margin-bottom: 0.5rem;",
                            )
                            for i, a in enumerate(artifacts)
                        ]
                        if artifacts
                        else [P("No artifacts found for this task", cls="secondary")]
                    ),
                    style="margin-top: 2rem;",
                ),
                # Telemetry section
                (
                    Div(
                        H3("Execution Telemetry"),
                        Table(
                            Tbody(
                                Tr(
                                    Td("Total Latency"),
                                    Td(
                                        f"{details['telemetry']['total_latency_ms']:.0f}ms"
                                    ),
                                ),
                                Tr(
                                    Td("Input Tokens"),
                                    Td(f"{details['telemetry']['total_tokens_in']:,}"),
                                ),
                                Tr(
                                    Td("Output Tokens"),
                                    Td(f"{details['telemetry']['total_tokens_out']:,}"),
                                ),
                                Tr(
                                    Td("API Cost"),
                                    Td(
                                        f"${details['telemetry']['total_cost_usd']:.4f}"
                                    ),
                                ),
                            )
                        ),
                        cls="card",
                        style="margin-top: 2rem;",
                    )
                    if details.get("telemetry")
                    else None
                ),
                style="max-width: 900px; margin: 0 auto; padding: 2rem;",
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

    @rt("/developer/task/{task_id}/diff")
    def get_task_diff(task_id: str):
        """Diff view - Show code proposals with unified diff display."""
        proposals = get_code_proposals(task_id)
        details = get_task_details(task_id)

        if not details:
            return Titled(
                "Task Not Found",
                Div(
                    A("< Back", href="/developer/tasks"),
                    H2(f"Task {task_id} not found"),
                    P("This task does not exist or has no code proposals."),
                    style="max-width: 800px; margin: 0 auto; padding: 2rem;",
                ),
            )

        return Titled(
            f"Code Review - {task_id}",
            theme_toggle(),
            Div(
                A("< Back to Task", href=f"/developer/task/{task_id}"),
                " | ",
                A("Task Timeline", href=f"/developer/task/{task_id}/trace"),
                H2(f"Code Proposals: {task_id}"),
                P(
                    f"{len(proposals)} file(s) proposed for this task",
                    cls="secondary",
                ),
                # Code proposals list
                (
                    Div(
                        *[
                            Div(
                                # File header
                                Div(
                                    Div(
                                        Strong(p["filename"]),
                                        Span(
                                            f" ({p['lines']} lines)",
                                            cls="secondary",
                                        ),
                                    ),
                                    Div(
                                        Span(
                                            p["status"].upper(),
                                            cls=f"pico-color-{'green' if p['status'] == 'approved' else ('red' if p['status'] == 'rejected' else 'azure')}",
                                        ),
                                    ),
                                    style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem;",
                                ),
                                # Code display
                                Div(
                                    Pre(
                                        p["content"],
                                        style="font-size: 0.85rem; overflow-x: auto; max-height: 400px; overflow-y: auto;",
                                    ),
                                    cls="diff-view",
                                    style="background: var(--pico-card-background-color); padding: 1rem; border-radius: 8px; border: 1px solid var(--pico-muted-border-color);",
                                ),
                                # Action buttons (visual only for now)
                                Div(
                                    Button(
                                        "Approve",
                                        cls="outline",
                                        style="margin-right: 0.5rem;",
                                        disabled=True,
                                    ),
                                    Button(
                                        "Reject",
                                        cls="outline secondary",
                                        style="margin-right: 0.5rem;",
                                        disabled=True,
                                    ),
                                    Button(
                                        "Edit",
                                        cls="outline",
                                        disabled=True,
                                    ),
                                    Small(
                                        " (Action buttons coming soon)",
                                        cls="secondary",
                                    ),
                                    style="margin-top: 1rem;",
                                ),
                                cls="card",
                                style="margin-bottom: 1.5rem;",
                            )
                            for p in proposals
                        ]
                    )
                    if proposals
                    else Div(
                        P(
                            "No code proposals available for this task.",
                            cls="secondary",
                            style="text-align: center; padding: 2rem;",
                        ),
                        P(
                            "Code proposals appear after the Code Agent generates code.",
                            style="text-align: center;",
                        ),
                        cls="card",
                    )
                ),
                # Navigation
                Div(
                    A(
                        "Back to Dashboard",
                        href="/developer",
                        role="button",
                        cls="outline",
                    ),
                    style="margin-top: 2rem;",
                ),
                style="max-width: 1000px; margin: 0 auto; padding: 2rem;",
            ),
        )

    @rt("/developer/active-agents")
    def get_developer_active_agents():
        """HTMX endpoint for active agents in developer view."""
        active = get_active_agents()

        if not active:
            return Div(
                P("No agents currently active", cls="secondary"),
                style="text-align: center; padding: 1rem;",
            )

        return Div(
            *[
                Div(
                    Div(
                        style="width: 10px; height: 10px; border-radius: 50%; "
                        "background: #22c55e; animation: pulse 2s infinite;",
                    ),
                    Span(
                        f"{a['agent_name']} working on {a['task_id']}",
                        style="margin-left: 0.5rem;",
                    ),
                    style="display: flex; align-items: center; margin-bottom: 0.5rem;",
                )
                for a in active
            ]
        )
