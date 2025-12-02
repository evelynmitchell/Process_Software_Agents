"""
Manager Persona (Sarah) - ASP Overwatch Dashboard

This module implements the web UI for the Engineering Manager persona.
Displays high-level metrics, agent health, quality gates, and team overview.
"""

from fasthtml.common import *

from .data import (
    generate_sparkline_svg,
    get_agent_health,
    get_agent_stats,
    get_cost_breakdown,
    get_daily_metrics,
    get_design_review_stats,
    get_tasks,
)


def manager_routes(app, rt):
    """Register all manager persona routes."""

    @rt("/manager")
    def get_manager():
        """Main manager dashboard - ASP Overwatch."""
        stats = get_agent_stats()
        review_stats = get_design_review_stats()
        tasks = get_tasks()
        agent_health = get_agent_health()
        cost_data = get_cost_breakdown(days=7)
        daily_metrics = get_daily_metrics(days=7)

        # Calculate high-level metrics
        success_rate = (
            (stats["successful"] / stats["total_tasks"] * 100)
            if stats["total_tasks"] > 0
            else 0
        )
        active_count = len(
            [t for t in tasks if t["status"] in ("in_progress", "planning")]
        )
        completed_count = len([t for t in tasks if t["status"] == "completed"])
        total_tokens = (
            cost_data["token_usage"]["input"] + cost_data["token_usage"]["output"]
        )

        # Generate sparklines
        cost_sparkline = generate_sparkline_svg(
            daily_metrics["cost"], width=60, height=20, color="#06b6d4"
        )
        token_sparkline = generate_sparkline_svg(
            daily_metrics["tokens"], width=60, height=20, color="#8b5cf6"
        )
        task_sparkline = generate_sparkline_svg(
            daily_metrics["tasks"], width=60, height=20, color="#10b981"
        )

        return Titled(
            "ASP Overwatch - Sarah",
            Div(
                # Header with key metrics
                Div(
                    H2("System Overview"),
                    Div(
                        Div(
                            H3(
                                f"{success_rate:.0f}%",
                                cls=(
                                    "pico-color-green"
                                    if success_rate >= 80
                                    else "pico-color-yellow"
                                ),
                            ),
                            P("Success Rate"),
                            cls="card",
                            style="text-align: center;",
                        ),
                        Div(
                            H3(str(active_count), cls="pico-color-azure"),
                            P("Active Tasks"),
                            cls="card",
                            style="text-align: center;",
                        ),
                        Div(
                            H3(str(completed_count)),
                            P("Completed"),
                            cls="card",
                            style="text-align: center;",
                        ),
                        Div(
                            H3(f"{stats['avg_execution_time']:.1f}s"),
                            P("Avg Execution"),
                            cls="card",
                            style="text-align: center;",
                        ),
                        cls="grid",
                    ),
                    # Cost metrics row with sparklines
                    Div(
                        Div(
                            Div(
                                H3(
                                    f"${cost_data['total_usd']:.2f}",
                                    cls="pico-color-azure",
                                    style="display: inline;",
                                ),
                                NotStr(cost_sparkline),
                                style="display: flex; align-items: center; justify-content: center; gap: 0.5rem;",
                            ),
                            P("API Cost (7 days)"),
                            cls="card",
                            style="text-align: center;",
                        ),
                        Div(
                            Div(
                                H3(
                                    f"{total_tokens:,}" if total_tokens > 0 else "0",
                                    style="display: inline;",
                                ),
                                NotStr(token_sparkline),
                                style="display: flex; align-items: center; justify-content: center; gap: 0.5rem;",
                            ),
                            P("Total Tokens"),
                            cls="card",
                            style="text-align: center;",
                        ),
                        Div(
                            Div(
                                H3(
                                    f"{stats['total_tasks']}",
                                    cls="pico-color-green",
                                    style="display: inline;",
                                ),
                                NotStr(task_sparkline),
                                style="display: flex; align-items: center; justify-content: center; gap: 0.5rem;",
                            ),
                            P("Tasks (7 days)"),
                            cls="card",
                            style="text-align: center;",
                        ),
                        Div(
                            H3(
                                f"{cost_data['token_usage']['output']:,}"
                                if cost_data["token_usage"]["output"] > 0
                                else "0"
                            ),
                            P("Output Tokens"),
                            cls="card",
                            style="text-align: center;",
                        ),
                        cls="grid",
                        style="margin-top: 1rem;",
                    ),
                    style="margin-bottom: 2rem;",
                ),
                # Two-column layout
                Div(
                    # Left: Agent Status
                    Div(
                        Div(
                            H3("Agent Health"),
                            Table(
                                Thead(
                                    Tr(
                                        Th("Agent"),
                                        Th("Status"),
                                        Th("Last Active"),
                                        Th("Executions"),
                                    )
                                ),
                                Tbody(
                                    *[
                                        Tr(
                                            Td(agent["name"]),
                                            Td(
                                                agent["status"],
                                                cls=(
                                                    "pico-color-green"
                                                    if agent["status"] == "Operational"
                                                    else (
                                                        "pico-color-yellow"
                                                        if agent["status"] == "Idle"
                                                        else "pico-color-grey"
                                                    )
                                                ),
                                            ),
                                            Td(agent["last_active"]),
                                            Td(str(agent["executions"])),
                                        )
                                        for agent in agent_health
                                    ]
                                ),
                            ),
                            cls="card",
                            # HTMX: Refresh agent status
                            hx_get="/manager/agent-status",
                            hx_trigger="every 60s",
                            hx_swap="innerHTML",
                        ),
                        style="flex: 1; margin-right: 1rem;",
                    ),
                    # Right: Quality Metrics
                    Div(
                        Div(
                            H3("Quality Gates"),
                            Table(
                                Tbody(
                                    Tr(
                                        Td("Design Reviews"),
                                        Td(f"{review_stats['total_reviews']} reviews"),
                                    ),
                                    Tr(
                                        Td("Pass Rate"),
                                        Td(
                                            (
                                                f"{(review_stats['passed']/review_stats['total_reviews']*100):.0f}%"
                                                if review_stats["total_reviews"] > 0
                                                else "N/A"
                                            ),
                                            cls="pico-color-green",
                                        ),
                                    ),
                                    Tr(
                                        Td("Total Defects Found"),
                                        Td(str(review_stats["total_defects"])),
                                    ),
                                    Tr(
                                        Td("Avg Complexity"),
                                        Td(f"{stats['avg_complexity']:.0f}"),
                                    ),
                                )
                            ),
                            cls="card",
                        ),
                        Div(
                            H3("Defects by Category"),
                            (
                                Ul(
                                    *[
                                        Li(f"{cat}: {count}")
                                        for cat, count in review_stats[
                                            "by_category"
                                        ].items()
                                    ]
                                )
                                if review_stats["by_category"]
                                else P("No defects categorized", cls="secondary")
                            ),
                            cls="card",
                            style="margin-top: 1rem;",
                        ),
                        style="flex: 1;",
                    ),
                    style="display: flex;",
                ),
                # Bottom: Recent Tasks Summary
                Div(
                    H3("Recent Task Activity"),
                    Table(
                        Thead(
                            Tr(
                                Th("Task ID"),
                                Th("Description"),
                                Th("Complexity"),
                                Th("Status"),
                                Th("Execution Time"),
                            )
                        ),
                        Tbody(
                            *[
                                Tr(
                                    Td(t["task_id"]),
                                    Td(
                                        t["description"][:35] + "..."
                                        if len(t["description"]) > 35
                                        else t["description"]
                                    ),
                                    Td(str(t["complexity"])),
                                    Td(
                                        t["status"],
                                        cls=(
                                            "pico-color-green"
                                            if t["status"] == "completed"
                                            else (
                                                "pico-color-azure"
                                                if t["status"] == "in_progress"
                                                else ""
                                            )
                                        ),
                                    ),
                                    Td(
                                        f"{t['execution_time']:.2f}s"
                                        if t["execution_time"] > 0
                                        else "-"
                                    ),
                                )
                                for t in tasks[:10]
                            ]
                        ),
                    ),
                    A(
                        "View All Tasks",
                        href="/manager/tasks",
                        role="button",
                        cls="outline",
                    ),
                    cls="card",
                    style="margin-top: 2rem;",
                ),
                style="max-width: 1400px; margin: 0 auto; padding: 2rem;",
            ),
        )

    @rt("/manager/agent-status")
    def get_agent_status():
        """HTMX endpoint for agent status updates."""
        agent_health = get_agent_health()
        return Div(
            H3("Agent Health"),
            Table(
                Thead(
                    Tr(
                        Th("Agent"),
                        Th("Status"),
                        Th("Last Active"),
                        Th("Executions"),
                    )
                ),
                Tbody(
                    *[
                        Tr(
                            Td(agent["name"]),
                            Td(
                                agent["status"],
                                cls=(
                                    "pico-color-green"
                                    if agent["status"] == "Operational"
                                    else (
                                        "pico-color-yellow"
                                        if agent["status"] == "Idle"
                                        else "pico-color-grey"
                                    )
                                ),
                            ),
                            Td(agent["last_active"]),
                            Td(str(agent["executions"])),
                        )
                        for agent in agent_health
                    ]
                ),
            ),
        )

    @rt("/manager/tasks")
    def get_manager_tasks():
        """View all tasks from manager perspective."""
        tasks = get_tasks()
        stats = get_agent_stats()

        return Titled(
            "Task Overview - Manager View",
            Div(
                A("< Back to Dashboard", href="/manager"),
                H2("All Tasks"),
                # Summary stats
                Div(
                    P(
                        f"Total: {len(tasks)} | Completed: {stats['successful']} | "
                        f"Failed: {stats['failed']} | "
                        f"Success Rate: {(stats['successful']/stats['total_tasks']*100):.0f}%"
                        if stats["total_tasks"] > 0
                        else "No data"
                    ),
                    style="margin-bottom: 1rem;",
                ),
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
                                Td(t["task_id"]),
                                Td(
                                    t["description"][:50] + "..."
                                    if len(t["description"]) > 50
                                    else t["description"]
                                ),
                                Td(str(t["complexity"])),
                                Td(str(t["num_units"])),
                                Td(
                                    f"{t['execution_time']:.2f}"
                                    if t["execution_time"] > 0
                                    else "-"
                                ),
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
