"""
Product Persona (Jordan) - Project Overview Dashboard

This module implements the web UI for the Product Manager persona.
Displays project progress, task pipeline, and delivery metrics.
"""

from fasthtml.common import *

from .components import theme_toggle
from .data import (
    get_agent_stats,
    get_running_tasks,
    get_tasks,
    register_task_execution,
)


def product_routes(app, rt):
    """Register all product persona routes."""

    @rt("/product")
    def get_product():
        """Main product dashboard - Project Overview."""
        stats = get_agent_stats()
        tasks = get_tasks()

        # Group tasks by status
        planning = [t for t in tasks if t["status"] == "planning"]
        in_progress = [t for t in tasks if t["status"] == "in_progress"]
        completed = [t for t in tasks if t["status"] == "completed"]
        failed = [t for t in tasks if t["status"] == "failed"]

        # Calculate delivery metrics
        total = len(tasks)
        completion_rate = (len(completed) / total * 100) if total > 0 else 0

        return Titled(
            "Project Overview - Jordan",
            theme_toggle(),
            Div(
                # Header metrics
                Div(
                    H2("Delivery Dashboard"),
                    Div(
                        Div(
                            H3(f"{completion_rate:.0f}%"),
                            P("Completion Rate"),
                            cls="card",
                            style="text-align: center;",
                        ),
                        Div(
                            H3(str(len(planning))),
                            P("In Planning"),
                            cls="card",
                            style="text-align: center;",
                        ),
                        Div(
                            H3(str(len(in_progress)), cls="pico-color-azure"),
                            P("In Progress"),
                            cls="card",
                            style="text-align: center;",
                        ),
                        Div(
                            H3(str(len(completed)), cls="pico-color-green"),
                            P("Completed"),
                            cls="card",
                            style="text-align: center;",
                        ),
                        cls="grid",
                    ),
                    style="margin-bottom: 2rem;",
                ),
                # Task Pipeline (Kanban-style)
                Div(
                    H3("Task Pipeline"),
                    Div(
                        # Planning column
                        Div(
                            H4(f"Planning ({len(planning)})"),
                            Div(
                                *[
                                    Div(
                                        Strong(t["task_id"]),
                                        P(
                                            (
                                                t["description"][:30] + "..."
                                                if len(t["description"]) > 30
                                                else t["description"]
                                            ),
                                            style="font-size: 0.9em; margin: 0;",
                                        ),
                                        cls="card",
                                        style="margin-bottom: 0.5rem; padding: 0.5rem;",
                                    )
                                    for t in planning[:5]
                                ],
                                P(
                                    (
                                        f"+{len(planning)-5} more"
                                        if len(planning) > 5
                                        else ""
                                    ),
                                    cls="secondary",
                                ),
                            ),
                            style="flex: 1; padding: 0.5rem; background: var(--pico-card-background-color); border-radius: 4px; margin-right: 0.5rem;",
                        ),
                        # In Progress column
                        Div(
                            H4(
                                f"In Progress ({len(in_progress)})",
                                cls="pico-color-azure",
                            ),
                            Div(
                                *[
                                    Div(
                                        Strong(t["task_id"]),
                                        P(
                                            (
                                                t["description"][:30] + "..."
                                                if len(t["description"]) > 30
                                                else t["description"]
                                            ),
                                            style="font-size: 0.9em; margin: 0;",
                                        ),
                                        cls="card",
                                        style="margin-bottom: 0.5rem; padding: 0.5rem; border-left: 3px solid var(--pico-primary);",
                                    )
                                    for t in in_progress[:5]
                                ],
                                P(
                                    (
                                        f"+{len(in_progress)-5} more"
                                        if len(in_progress) > 5
                                        else ""
                                    ),
                                    cls="secondary",
                                ),
                            ),
                            style="flex: 1; padding: 0.5rem; background: var(--pico-card-background-color); border-radius: 4px; margin-right: 0.5rem;",
                        ),
                        # Completed column
                        Div(
                            H4(f"Completed ({len(completed)})", cls="pico-color-green"),
                            Div(
                                *[
                                    Div(
                                        Strong(t["task_id"]),
                                        Small(f" - {t['complexity']} complexity"),
                                        cls="card",
                                        style="margin-bottom: 0.5rem; padding: 0.5rem; border-left: 3px solid green;",
                                    )
                                    for t in completed[:5]
                                ],
                                P(
                                    (
                                        f"+{len(completed)-5} more"
                                        if len(completed) > 5
                                        else ""
                                    ),
                                    cls="secondary",
                                ),
                            ),
                            style="flex: 1; padding: 0.5rem; background: var(--pico-card-background-color); border-radius: 4px;",
                        ),
                        style="display: flex; gap: 0.5rem;",
                    ),
                    cls="card",
                    style="margin-bottom: 2rem;",
                ),
                # Quick Actions
                Div(
                    H3("Quick Actions"),
                    Div(
                        A(
                            "New Feature Request",
                            href="/product/new-feature",
                            role="button",
                            style="display: inline-block;",
                        ),
                        A(
                            "View Running Tasks",
                            href="/product/running",
                            role="button",
                            cls="outline",
                            style="display: inline-block; margin-left: 1rem;",
                        ),
                        style="margin-bottom: 2rem;",
                    ),
                    cls="card",
                    style="margin-bottom: 2rem;",
                ),
                # Performance Summary
                Div(
                    H3("Performance Summary"),
                    Div(
                        Div(
                            H4("Throughput"),
                            Table(
                                Tbody(
                                    Tr(
                                        Td("Total Tasks Processed"),
                                        Td(Strong(str(stats["total_tasks"]))),
                                    ),
                                    Tr(
                                        Td("Total Units Completed"),
                                        Td(Strong(str(stats["total_units"]))),
                                    ),
                                    Tr(
                                        Td("Avg Units per Task"),
                                        Td(
                                            Strong(
                                                f"{stats['total_units']/stats['total_tasks']:.1f}"
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
                            H4("Complexity Analysis"),
                            Table(
                                Tbody(
                                    Tr(
                                        Td("Avg Complexity"),
                                        Td(Strong(f"{stats['avg_complexity']:.0f}")),
                                    ),
                                    Tr(
                                        Td("Avg Execution Time"),
                                        Td(
                                            Strong(
                                                f"{stats['avg_execution_time']:.1f}s"
                                            )
                                        ),
                                    ),
                                    Tr(
                                        Td("Success Rate"),
                                        Td(
                                            Strong(
                                                f"{(stats['successful']/stats['total_tasks']*100):.0f}%"
                                                if stats["total_tasks"] > 0
                                                else "N/A"
                                            ),
                                            cls="pico-color-green",
                                        ),
                                    ),
                                )
                            ),
                            cls="card",
                        ),
                        cls="grid",
                    ),
                ),
                # Navigation
                Div(
                    A("Back to Home", href="/", role="button", cls="outline"),
                    style="margin-top: 2rem;",
                ),
                style="max-width: 1400px; margin: 0 auto; padding: 2rem;",
            ),
        )

    @rt("/product/new-feature")
    def get_new_feature():
        """Feature Wizard - New feature request form."""
        return Titled(
            "Feature Wizard - New Request",
            theme_toggle(),
            Div(
                A("< Back to Dashboard", href="/product"),
                H2("New Feature Request"),
                P(
                    "Submit a new feature for the autonomous development pipeline.",
                    cls="secondary",
                ),
                Form(
                    # Task ID
                    Div(
                        Label("Task ID", htmlFor="task_id"),
                        Input(
                            type="text",
                            id="task_id",
                            name="task_id",
                            placeholder="e.g., FEAT-2025-001",
                            required=True,
                        ),
                        Small(
                            "Unique identifier for this feature (letters, numbers, dashes)"
                        ),
                    ),
                    # Description
                    Div(
                        Label("Feature Description", htmlFor="description"),
                        Input(
                            type="text",
                            id="description",
                            name="description",
                            placeholder="Brief description of the feature",
                            required=True,
                        ),
                        Small("1-2 sentences describing what this feature does"),
                        style="margin-top: 1rem;",
                    ),
                    # Requirements
                    Div(
                        Label("Detailed Requirements", htmlFor="requirements"),
                        Textarea(
                            id="requirements",
                            name="requirements",
                            placeholder="- User story 1\n- User story 2\n- Acceptance criteria...",
                            rows="8",
                            required=True,
                        ),
                        Small(
                            "User stories, acceptance criteria, technical requirements"
                        ),
                        style="margin-top: 1rem;",
                    ),
                    # Priority
                    Div(
                        Label("Priority", htmlFor="priority"),
                        Select(
                            Option("Normal", value="normal", selected=True),
                            Option("High", value="high"),
                            Option("Critical", value="critical"),
                            id="priority",
                            name="priority",
                        ),
                        style="margin-top: 1rem;",
                    ),
                    # Submit button
                    Div(
                        Button("Submit Feature Request", type="submit"),
                        style="margin-top: 1.5rem;",
                    ),
                    method="post",
                    action="/product/new-feature",
                ),
                cls="card",
                style="max-width: 800px; margin: 2rem auto; padding: 2rem;",
            ),
        )

    @rt("/product/new-feature", methods=["POST"])
    def post_new_feature(task_id: str, description: str, requirements: str, priority: str = "normal"):
        """Handle feature request submission."""
        # Validate inputs
        if not task_id or not description or not requirements:
            return Titled(
                "Error",
                Div(
                    H2("Invalid Request"),
                    P("All fields are required."),
                    A("Go back", href="/product/new-feature", role="button"),
                    style="max-width: 600px; margin: 2rem auto;",
                ),
            )

        # Register the task for execution
        task_info = register_task_execution(task_id, description, requirements)

        return Titled(
            "Feature Request Submitted",
            theme_toggle(),
            Div(
                H2("Feature Request Submitted"),
                Div(
                    P(
                        "Your feature request has been submitted to the autonomous development pipeline."
                    ),
                    Table(
                        Tbody(
                            Tr(Td("Task ID"), Td(Strong(task_id))),
                            Tr(Td("Description"), Td(description)),
                            Tr(Td("Priority"), Td(priority.capitalize())),
                            Tr(
                                Td("Status"),
                                Td(
                                    Span("Queued", cls="pico-color-azure"),
                                ),
                            ),
                        )
                    ),
                    cls="card",
                ),
                Div(
                    P(
                        "The TSP Orchestrator will coordinate the following agents:",
                        cls="secondary",
                    ),
                    Ol(
                        Li("Planning Agent - Generate project plan"),
                        Li("Design Agent - Create design specification"),
                        Li("Design Review - Quality gate check"),
                        Li("Code Agent - Generate implementation"),
                        Li("Code Review - Quality gate check"),
                        Li("Test Agent - Validate implementation"),
                        Li("Postmortem Agent - Generate improvement proposals"),
                    ),
                    style="margin-top: 1rem;",
                ),
                Div(
                    A(
                        "View Running Tasks",
                        href="/product/running",
                        role="button",
                    ),
                    A(
                        "Back to Dashboard",
                        href="/product",
                        role="button",
                        cls="outline",
                        style="margin-left: 1rem;",
                    ),
                    style="margin-top: 2rem;",
                ),
                style="max-width: 800px; margin: 2rem auto;",
            ),
        )

    @rt("/product/running")
    def get_running():
        """View currently running tasks."""
        running = get_running_tasks()

        return Titled(
            "Running Tasks",
            theme_toggle(),
            Div(
                A("< Back to Dashboard", href="/product"),
                H2("Running Tasks"),
                P(
                    f"{len(running)} task(s) currently in the pipeline",
                    cls="secondary",
                ),
                (
                    Div(
                        *[
                            Div(
                                Div(
                                    Strong(t["task_id"]),
                                    Span(
                                        f" - {t['phase'].replace('_', ' ').title()}",
                                        cls="pico-color-azure",
                                    ),
                                    style="display: flex; justify-content: space-between;",
                                ),
                                P(t["description"][:60] + "..." if len(t.get("description", "")) > 60 else t.get("description", ""), style="margin: 0.5rem 0;"),
                                # Progress bar
                                Div(
                                    Div(
                                        style=f"width: {t['progress_pct']}%; height: 100%; background: var(--pico-primary); border-radius: 4px; transition: width 0.3s;",
                                    ),
                                    style="height: 8px; background: var(--pico-muted-border-color); border-radius: 4px; margin: 0.5rem 0;",
                                ),
                                Small(f"{t['progress_pct']}% complete", cls="secondary"),
                                cls="card",
                                style="margin-bottom: 1rem;",
                            )
                            for t in running
                        ],
                        # HTMX auto-refresh
                        hx_get="/product/running-tasks",
                        hx_trigger="every 5s",
                        hx_swap="innerHTML",
                    )
                    if running
                    else Div(
                        P(
                            "No tasks currently running.",
                            cls="secondary",
                            style="text-align: center; padding: 2rem;",
                        ),
                        P(
                            A(
                                "Submit a new feature request",
                                href="/product/new-feature",
                            ),
                            style="text-align: center;",
                        ),
                        cls="card",
                    )
                ),
                style="max-width: 800px; margin: 2rem auto;",
            ),
        )

    @rt("/product/running-tasks")
    def get_running_tasks_fragment():
        """HTMX endpoint for running tasks updates."""
        running = get_running_tasks()

        if not running:
            return Div(
                P(
                    "No tasks currently running.",
                    cls="secondary",
                    style="text-align: center; padding: 2rem;",
                ),
                cls="card",
            )

        return Div(
            *[
                Div(
                    Div(
                        Strong(t["task_id"]),
                        Span(
                            f" - {t['phase'].replace('_', ' ').title()}",
                            cls="pico-color-azure",
                        ),
                    ),
                    P(t["description"][:60] + "..." if len(t.get("description", "")) > 60 else t.get("description", ""), style="margin: 0.5rem 0;"),
                    Div(
                        Div(
                            style=f"width: {t['progress_pct']}%; height: 100%; background: var(--pico-primary); border-radius: 4px;",
                        ),
                        style="height: 8px; background: var(--pico-muted-border-color); border-radius: 4px; margin: 0.5rem 0;",
                    ),
                    Small(f"{t['progress_pct']}% complete", cls="secondary"),
                    cls="card",
                    style="margin-bottom: 1rem;",
                )
                for t in running
            ]
        )
