"""
Product Persona (Jordan) - Project Overview Dashboard

This module implements the web UI for the Product Manager persona.
Displays project progress, task pipeline, and delivery metrics.
"""

from fasthtml.common import *
from .data import get_tasks, get_agent_stats


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
                style="max-width: 1400px; margin: 0 auto; padding: 2rem;",
            ),
        )
