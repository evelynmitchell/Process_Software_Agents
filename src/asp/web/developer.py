"""
Developer Persona (Alex) - Flow State Canvas

This module implements the web UI for the Senior Developer persona.
Uses HTMX for dynamic updates without page reloads.
"""

from fasthtml.common import *
from . import data


def developer_routes(app, rt):
    """Register all routes for the Developer persona."""

    @rt('/developer')
    def get_developer():
        """Main developer dashboard - Flow State Canvas."""
        return Titled("Flow State Canvas - Alex",
            # Header with user info
            Div(
                Span("Developer View", cls="pico-color-azure"),
                Span(" | "),
                Span("Alex", style="font-weight: bold;"),
                style="text-align: right; padding: 0.5rem; border-bottom: 1px solid var(--pico-muted-border-color);"
            ),
            Div(
                # Sidebar / Navigation
                Div(
                    H3("Active Tasks"),
                    # Dynamic task list loaded via HTMX
                    Div(
                        hx_get="/developer/tasks",
                        hx_trigger="load",
                        hx_swap="innerHTML"
                    ),
                    Hr(),
                    H3("Agent Stats"),
                    Div(
                        hx_get="/developer/agent-stats",
                        hx_trigger="load",
                        hx_swap="innerHTML"
                    ),
                    Hr(),
                    H3("Tools"),
                    Ul(
                        Li(A("New Task", href="/developer/new-task")),
                        Li(A("View Defects", href="/developer/defects")),
                        Li(A("Run Tests", href="#", cls="secondary")),
                    ),
                    cls="sidebar",
                    style="width: 280px; border-right: 1px solid var(--pico-muted-border-color); padding-right: 1rem; overflow-y: auto;"
                ),
                # Main Content Area
                Div(
                    # Context summary card
                    Div(
                        H2("Dashboard"),
                        P("Real-time view of ASP Platform activity", cls="pico-color-azure"),
                        cls="card",
                        style="margin-bottom: 1rem;"
                    ),
                    # Recent activity - auto-refreshes
                    Div(
                        H4("Recent Activity"),
                        Div(
                            hx_get="/developer/activity",
                            hx_trigger="load, every 30s",
                            hx_swap="innerHTML"
                        ),
                        cls="card"
                    ),
                    # Defect summary
                    Div(
                        H4("Defect Overview"),
                        Div(
                            hx_get="/developer/defect-summary",
                            hx_trigger="load",
                            hx_swap="innerHTML"
                        ),
                        cls="card",
                        style="margin-top: 1rem;"
                    ),
                    style="flex-grow: 1; padding-left: 2rem;"
                ),
                style="display: flex; min-height: 80vh;"
            )
        )

    @rt('/developer/tasks')
    def get_tasks():
        """HTMX endpoint: List of active tasks."""
        # Initialize demo data if database is empty
        data.insert_demo_data()

        tasks = data.get_active_tasks(limit=10)

        if not tasks:
            return P("No active tasks", cls="pico-color-grey")

        return Ul(
            *[Li(
                A(
                    task['task_id'],
                    href=f"/developer/task/{task['task_id']}",
                    style="font-family: monospace;"
                ),
                Small(
                    f" ({task['activity_count']} actions)",
                    cls="pico-color-grey"
                )
            ) for task in tasks]
        )

    @rt('/developer/activity')
    def get_activity():
        """HTMX endpoint: Recent activity table."""
        activity = data.get_recent_activity(limit=10)

        if not activity:
            return P("No activity recorded yet", cls="pico-color-grey")

        return Table(
            Thead(
                Tr(
                    Th("Time"),
                    Th("Task"),
                    Th("Agent"),
                    Th("Metric"),
                    Th("Value")
                )
            ),
            Tbody(
                *[Tr(
                    Td(_format_time(row['timestamp'])),
                    Td(Code(row['task_id'][:12] + "..." if len(row['task_id']) > 12 else row['task_id'])),
                    Td(row['agent_role']),
                    Td(row['metric_type']),
                    Td(
                        f"{row['metric_value']:.1f} {row['metric_unit']}",
                        cls="pico-color-green" if row['metric_type'] == 'Latency' and row['metric_value'] < 2000 else ""
                    )
                ) for row in activity]
            )
        )

    @rt('/developer/agent-stats')
    def get_agent_stats():
        """HTMX endpoint: Agent statistics."""
        stats = data.get_agent_stats()

        if not stats:
            return P("No agent data", cls="pico-color-grey")

        return Ul(
            *[Li(
                Strong(agent),
                Br(),
                Small(
                    f"{info['invocation_count']} calls",
                    cls="pico-color-grey"
                )
            ) for agent, info in stats.items()]
        )

    @rt('/developer/defect-summary')
    def get_defect_summary():
        """HTMX endpoint: Defect summary stats."""
        summary = data.get_defect_summary()

        if summary['total'] == 0:
            return P("No defects recorded", cls="pico-color-green")

        severity_badges = []
        for severity, count in summary['by_severity'].items():
            color_class = {
                'Critical': 'pico-color-red',
                'High': 'pico-color-orange',
                'Medium': 'pico-color-yellow',
                'Low': 'pico-color-grey'
            }.get(severity, '')

            severity_badges.append(
                Span(f"{severity}: {count}", cls=f"badge {color_class}", style="margin-right: 0.5rem;")
            )

        return Div(
            P(f"Total defects: {summary['total']}"),
            Div(*severity_badges),
            Hr(),
            H5("Top Defect Types"),
            Ul(
                *[Li(f"{dtype}: {count}") for dtype, count in summary['by_type'].items()]
            ) if summary['by_type'] else P("None", cls="pico-color-grey")
        )

    @rt('/developer/defects')
    def get_defects_page():
        """Full defects page."""
        defects = data.get_recent_defects(limit=20)

        return Titled("Defect Log - Alex",
            A("< Back to Dashboard", href="/developer"),
            H2("Recent Defects"),
            Table(
                Thead(
                    Tr(
                        Th("ID"),
                        Th("Severity"),
                        Th("Type"),
                        Th("Description"),
                        Th("Injected"),
                        Th("Removed")
                    )
                ),
                Tbody(
                    *[Tr(
                        Td(Code(d['defect_id'][:16])),
                        Td(
                            d['severity'],
                            cls=_severity_class(d['severity'])
                        ),
                        Td(d['defect_type']),
                        Td(d['description'][:50] + "..." if len(d['description']) > 50 else d['description']),
                        Td(d['phase_injected']),
                        Td(d['phase_removed'])
                    ) for d in defects]
                ) if defects else Tbody(Tr(Td("No defects found", colspan="6")))
            )
        )

    @rt('/developer/task/{task_id}')
    def get_task_detail(task_id: str):
        """Task detail page."""
        metrics = data.get_task_metrics(task_id)

        return Titled(f"Task: {task_id}",
            A("< Back to Dashboard", href="/developer"),
            H2(f"Task Details: {task_id}"),
            Div(
                H4("Metrics Summary"),
                Table(
                    Thead(Tr(Th("Metric"), Th("Total"), Th("Unit"))),
                    Tbody(
                        *[Tr(
                            Td(metric_type),
                            Td(f"{info['total']:.2f}"),
                            Td(info['unit'])
                        ) for metric_type, info in metrics.items()]
                    ) if metrics else Tbody(Tr(Td("No metrics", colspan="3")))
                ),
                cls="card"
            )
        )

    @rt('/developer/new-task')
    def get_new_task_form():
        """Form to create a new task."""
        return Titled("New Task - Alex",
            A("< Back to Dashboard", href="/developer"),
            H2("Create New Task"),
            Form(
                Label("Task ID", _for="task_id"),
                Input(name="task_id", id="task_id", placeholder="TSP-XXX-001", required=True),
                Label("Description", _for="description"),
                Textarea(name="description", id="description", placeholder="Describe the task...", rows="4"),
                Button("Create Task", type="submit"),
                action="/developer/create-task",
                method="post",
                cls="card"
            )
        )

    @rt('/developer/create-task')
    def post_create_task(task_id: str, description: str = ""):
        """Handle new task creation (placeholder)."""
        # TODO: Actually create the task in the system
        return Titled("Task Created",
            A("< Back to Dashboard", href="/developer"),
            Div(
                H2("Task Created Successfully"),
                P(f"Task ID: {task_id}"),
                P(f"Description: {description or 'No description'}"),
                P("Note: This is a placeholder. Full task creation will be implemented."),
                cls="card"
            )
        )


def _format_time(timestamp: str) -> str:
    """Format ISO timestamp to HH:MM display."""
    try:
        from datetime import datetime
        dt = datetime.fromisoformat(timestamp)
        return dt.strftime("%H:%M")
    except (ValueError, TypeError):
        return timestamp[:5] if timestamp else "N/A"


def _severity_class(severity: str) -> str:
    """Return CSS class for severity level."""
    return {
        'Critical': 'pico-color-red',
        'High': 'pico-color-orange',
        'Medium': 'pico-color-yellow',
        'Low': 'pico-color-grey'
    }.get(severity, '')
