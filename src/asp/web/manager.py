"""
Engineering Manager Persona (Sarah) - ASP Overwatch

This module implements the web UI for the Engineering Manager persona.
Focus: Process oversight, metrics review, approval workflows.
"""

from fasthtml.common import *

from .api import (
    get_cost_summary,
    get_defect_summary,
    get_recent_agent_activity,
    get_tasks_pending_approval,
    get_user_performance,
)


def manager_routes(app, rt):
    """Register routes for the Engineering Manager persona."""

    @rt('/manager')
    def get_manager():
        """Main dashboard for Engineering Manager."""
        return Titled("ASP Overwatch - Sarah",
            # Header with role info
            Div(
                Div(
                    Small("Engineering Manager View", cls="pico-color-azure"),
                    H1("ASP Overwatch"),
                    P("Monitor agent performance, review metrics, and manage approvals."),
                ),
                style="margin-bottom: 2rem;"
            ),

            # Key Metrics Cards
            Div(
                # Cost Summary Card
                Div(
                    H4("API Costs (7 days)"),
                    Div(
                        hx_get="/manager/api/cost-summary",
                        hx_trigger="load",
                        hx_swap="innerHTML"
                    ),
                    cls="card"
                ),
                # Defect Summary Card
                Div(
                    H4("Defect Tracker"),
                    Div(
                        hx_get="/manager/api/defect-summary",
                        hx_trigger="load",
                        hx_swap="innerHTML"
                    ),
                    cls="card"
                ),
                # User Performance Card
                Div(
                    H4("Team Performance"),
                    Div(
                        hx_get="/manager/api/user-performance",
                        hx_trigger="load",
                        hx_swap="innerHTML"
                    ),
                    cls="card"
                ),
                cls="grid"
            ),

            # Pending Approvals Section
            Div(
                H3("Pending Approvals"),
                Div(
                    hx_get="/manager/api/pending-approvals",
                    hx_trigger="load",
                    hx_swap="innerHTML"
                ),
                cls="card",
                style="margin-top: 2rem;"
            ),

            # Recent Activity Section
            Div(
                H3("Recent Agent Activity"),
                Div(
                    hx_get="/manager/api/recent-activity",
                    hx_trigger="load, every 10s",
                    hx_swap="innerHTML"
                ),
                cls="card",
                style="margin-top: 2rem;"
            ),

            # Navigation
            Div(
                A("Back to Home", href="/", role="button", cls="outline"),
                style="margin-top: 2rem;"
            ),

            style="max-width: 1200px; margin: 0 auto; padding: 2rem;"
        )

    # API Endpoints for dynamic content

    @rt('/manager/api/cost-summary')
    def get_cost_summary_view():
        """Return cost summary HTML fragment."""
        data = get_cost_summary(days=7)

        if data["total_usd"] == 0 and not data["token_usage"]["input"]:
            return Div(
                P("No cost data available yet.", cls="pico-color-grey"),
                Small("Start running agents to see metrics.")
            )

        return Div(
            P(
                Strong(f"${data['total_usd']:.4f}"),
                " total spend",
                cls="pico-color-green" if data['total_usd'] < 1 else "pico-color-amber"
            ),
            Hr(),
            Small("Token Usage:"),
            Ul(
                Li(f"Input: {data['token_usage']['input']:,} tokens"),
                Li(f"Output: {data['token_usage']['output']:,} tokens"),
            ),
            Small("Cost by Role:") if data["by_role"] else None,
            Ul(
                *[Li(f"{role}: ${cost:.4f}") for role, cost in data["by_role"].items()]
            ) if data["by_role"] else None,
        )

    @rt('/manager/api/defect-summary')
    def get_defect_summary_view():
        """Return defect summary HTML fragment."""
        data = get_defect_summary()

        if data["total"] == 0:
            return Div(
                P("No defects logged.", cls="pico-color-green"),
                Small("Defects will appear here when detected by agents.")
            )

        severity_colors = {
            "Critical": "pico-color-red",
            "High": "pico-color-amber",
            "Medium": "pico-color-yellow",
            "Low": "pico-color-grey",
        }

        return Div(
            P(Strong(str(data["total"])), " total defects"),
            Hr(),
            Small("By Severity:"),
            Ul(
                *[
                    Li(
                        f"{sev}: {count}",
                        cls=severity_colors.get(sev, "")
                    )
                    for sev, count in data["by_severity"].items()
                ]
            ) if data["by_severity"] else P("None categorized"),
            Small("Top Types:") if data["by_type"] else None,
            Ul(
                *[Li(f"{dtype}: {count}") for dtype, count in list(data["by_type"].items())[:3]]
            ) if data["by_type"] else None,
        )

    @rt('/manager/api/user-performance')
    def get_user_performance_view():
        """Return user performance HTML fragment."""
        data = get_user_performance()

        if not data:
            return Div(
                P("No user data available.", cls="pico-color-grey"),
                Small("Performance metrics appear when agents run.")
            )

        return Table(
            Thead(
                Tr(
                    Th("User"),
                    Th("Tasks"),
                    Th("Avg Latency"),
                )
            ),
            Tbody(
                *[
                    Tr(
                        Td(user["user_id"][:20] + "..." if len(user["user_id"]) > 20 else user["user_id"]),
                        Td(str(user["task_count"])),
                        Td(f"{user['avg_latency_ms']:.0f}ms"),
                    )
                    for user in data[:5]
                ]
            )
        )

    @rt('/manager/api/pending-approvals')
    def get_pending_approvals_view():
        """Return pending approvals HTML fragment."""
        tasks = get_tasks_pending_approval()

        if not tasks:
            return P("No tasks pending approval.", cls="pico-color-green")

        return Table(
            Thead(
                Tr(
                    Th("Task ID"),
                    Th("Title"),
                    Th("Status"),
                    Th("Action"),
                )
            ),
            Tbody(
                *[
                    Tr(
                        Td(Code(task["task_id"])),
                        Td(task["title"]),
                        Td(
                            task["status"].replace("_", " ").title(),
                            cls="pico-color-amber"
                        ),
                        Td(
                            Button("Review", cls="outline secondary", style="padding: 0.25rem 0.5rem;"),
                        ),
                    )
                    for task in tasks
                ]
            )
        )

    @rt('/manager/api/recent-activity')
    def get_recent_activity_view():
        """Return recent activity HTML fragment."""
        activities = get_recent_agent_activity(limit=10)

        if not activities:
            return Div(
                P("No recent activity.", cls="pico-color-grey"),
                Small("Agent executions will appear here.")
            )

        return Table(
            Thead(
                Tr(
                    Th("Time"),
                    Th("Task"),
                    Th("Agent"),
                    Th("Latency"),
                    Th("User"),
                )
            ),
            Tbody(
                *[
                    Tr(
                        Td(Small(act["timestamp"][:19] if act["timestamp"] else "-")),
                        Td(Code(act["task_id"][:15] if act["task_id"] else "-")),
                        Td(act["agent_role"] or "-"),
                        Td(f"{act['latency_ms']:.0f}ms" if act["latency_ms"] else "-"),
                        Td(Small(act["user_id"][:15] if act["user_id"] else "-")),
                    )
                    for act in activities
                ]
            )
        )
