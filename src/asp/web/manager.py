"""
Manager Persona (Sarah) - ASP Overwatch Dashboard

This module implements the web UI for the Engineering Manager persona.
Displays high-level metrics, agent health, quality gates, and team overview.
"""

# pylint: disable=no-value-for-parameter,undefined-variable,wildcard-import,unused-wildcard-import
# FastHTML components use *args and star imports which pylint cannot analyze correctly
from fasthtml.common import *

from .components import theme_toggle
from .data import (
    generate_sparkline_svg,
    get_active_agents,
    get_agent_health,
    get_agent_stats,
    get_budget_settings,
    get_budget_status,
    get_cost_breakdown,
    get_daily_metrics,
    get_design_review_stats,
    get_phase_yield_data,
    get_running_tasks,
    get_tasks,
    save_budget_settings,
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
        budget = get_budget_status()
        active_agents = get_active_agents()
        running_tasks = get_running_tasks()

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
            theme_toggle(),
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
                    # Budget meter
                    Div(
                        Div(
                            H4(
                                "Budget Status ",
                                A(
                                    "(Settings)",
                                    href="/manager/budget",
                                    style="font-size: 0.8rem; font-weight: normal;",
                                ),
                            ),
                            Div(
                                # Daily budget
                                Div(
                                    Div(
                                        Span("Daily: ", style="font-weight: bold;"),
                                        Span(
                                            f"${budget['daily_spent']:.2f}",
                                            cls=f"pico-color-{budget['status_color']}",
                                        ),
                                        Span(f" / ${budget['daily_limit']:.2f}"),
                                    ),
                                    Div(
                                        Div(
                                            style=f"width: {min(budget['daily_pct'], 100)}%; "
                                            f"height: 100%; background: {'#ef4444' if budget['daily_pct'] >= 100 else ('#f59e0b' if budget['daily_pct'] >= 80 else '#10b981')}; "
                                            "border-radius: 4px; transition: width 0.3s;",
                                        ),
                                        style="width: 100%; height: 12px; background: #e5e7eb; border-radius: 4px; overflow: hidden;",
                                    ),
                                    style="flex: 1;",
                                ),
                                # Monthly budget
                                Div(
                                    Div(
                                        Span("Monthly: ", style="font-weight: bold;"),
                                        Span(
                                            f"${budget['monthly_spent']:.2f}",
                                            cls=f"pico-color-{budget['status_color']}",
                                        ),
                                        Span(f" / ${budget['monthly_limit']:.2f}"),
                                    ),
                                    Div(
                                        Div(
                                            style=f"width: {min(budget['monthly_pct'], 100)}%; "
                                            f"height: 100%; background: {'#ef4444' if budget['monthly_pct'] >= 100 else ('#f59e0b' if budget['monthly_pct'] >= 80 else '#10b981')}; "
                                            "border-radius: 4px; transition: width 0.3s;",
                                        ),
                                        style="width: 100%; height: 12px; background: #e5e7eb; border-radius: 4px; overflow: hidden;",
                                    ),
                                    style="flex: 1;",
                                ),
                                style="display: flex; gap: 2rem;",
                            ),
                            cls="card",
                            style="padding: 1rem;",
                            hx_get="/manager/budget-status",
                            hx_trigger="every 60s",
                            hx_swap="innerHTML",
                        ),
                        style="margin-top: 1rem;",
                    ),
                    style="margin-bottom: 2rem;",
                ),
                # Active Agents (Agent Presence Indicators)
                (
                    Div(
                        H3(
                            "Active Agents ",
                            Span(
                                f"({len(active_agents)})",
                                cls="pico-color-green",
                            ),
                        ),
                        Div(
                            *[
                                Div(
                                    # Agent avatar/indicator
                                    Div(
                                        Span(
                                            a["agent_name"][0],  # First letter
                                            style="font-weight: bold; font-size: 1.2rem;",
                                        ),
                                        style="width: 40px; height: 40px; border-radius: 50%; "
                                        "background: var(--pico-primary); color: white; "
                                        "display: flex; align-items: center; justify-content: center;",
                                    ),
                                    Div(
                                        Strong(a["agent_name"]),
                                        P(
                                            f"Working on {a['task_id']}",
                                            style="margin: 0; font-size: 0.85rem;",
                                            cls="secondary",
                                        ),
                                        style="margin-left: 0.75rem;",
                                    ),
                                    # Pulsing indicator
                                    Div(
                                        style="width: 12px; height: 12px; border-radius: 50%; "
                                        "background: #22c55e; animation: pulse 2s infinite; margin-left: auto;",
                                    ),
                                    style="display: flex; align-items: center; padding: 0.75rem; "
                                    "border: 1px solid var(--pico-muted-border-color); border-radius: 8px; "
                                    "margin-right: 1rem; margin-bottom: 0.5rem;",
                                )
                                for a in active_agents
                            ],
                            style="display: flex; flex-wrap: wrap;",
                        ),
                        cls="card",
                        style="margin-bottom: 2rem;",
                        hx_get="/manager/active-agents",
                        hx_trigger="every 5s",
                        hx_swap="innerHTML",
                    )
                    if active_agents
                    else None
                ),
                # Running Tasks (if any)
                (
                    Div(
                        H3(
                            "Running Pipeline Tasks ",
                            Span(f"({len(running_tasks)})", cls="pico-color-azure"),
                        ),
                        Div(
                            *[
                                Div(
                                    Div(
                                        Strong(t["task_id"]),
                                        Span(
                                            f" - {t['phase'].replace('_', ' ').title()}",
                                            cls="pico-color-azure",
                                        ),
                                    ),
                                    # Progress bar
                                    Div(
                                        Div(
                                            style=f"width: {t['progress_pct']}%; height: 100%; "
                                            "background: var(--pico-primary); border-radius: 4px; "
                                            "transition: width 0.3s;",
                                        ),
                                        style="height: 8px; background: var(--pico-muted-border-color); "
                                        "border-radius: 4px; margin: 0.5rem 0;",
                                    ),
                                    Small(
                                        f"{t['progress_pct']}% complete",
                                        cls="secondary",
                                    ),
                                    style="margin-bottom: 0.5rem;",
                                )
                                for t in running_tasks[:3]  # Show max 3
                            ],
                        ),
                        (
                            A(
                                f"View all {len(running_tasks)} running tasks",
                                href="/product/running",
                                style="font-size: 0.9rem;",
                            )
                            if len(running_tasks) > 3
                            else None
                        ),
                        cls="card",
                        style="margin-bottom: 2rem;",
                        hx_get="/manager/running-tasks",
                        hx_trigger="every 5s",
                        hx_swap="innerHTML",
                    )
                    if running_tasks
                    else None
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

    @rt("/manager/phase-yield")
    def get_phase_yield():
        """Phase Yield Analysis - Task flow through development phases."""
        data = get_phase_yield_data()
        phases = data["phases"]
        phase_counts = data["phase_counts"]
        phase_defects = data["phase_defects"]

        # Calculate max for scaling bars
        max_count = max(phase_counts.values()) if phase_counts.values() else 1

        # Phase colors
        phase_colors = {
            "Planning": "#8b5cf6",  # Purple
            "Design": "#06b6d4",  # Cyan
            "Code": "#f59e0b",  # Amber
            "Test": "#10b981",  # Green
            "Complete": "#22c55e",  # Bright green
        }

        return Titled(
            "Phase Yield Analysis - Manager",
            Div(
                A("< Back to Dashboard", href="/manager"),
                H2("Phase Yield Analysis"),
                P(
                    "Task flow through development phases with defect detection points.",
                    cls="secondary",
                ),
                # Summary metrics
                Div(
                    Div(
                        H3(str(data["total_started"])),
                        P("Tasks Started"),
                        cls="card",
                        style="text-align: center;",
                    ),
                    Div(
                        H3(str(data["total_completed"]), cls="pico-color-green"),
                        P("Completed"),
                        cls="card",
                        style="text-align: center;",
                    ),
                    Div(
                        H3(
                            f"{data['yield_rate']:.0f}%",
                            cls=(
                                "pico-color-green"
                                if data["yield_rate"] >= 80
                                else "pico-color-yellow"
                            ),
                        ),
                        P("Yield Rate"),
                        cls="card",
                        style="text-align: center;",
                    ),
                    Div(
                        H3(
                            str(data["total_defects"]),
                            cls="pico-color-red" if data["total_defects"] > 0 else "",
                        ),
                        P("Defects Found"),
                        cls="card",
                        style="text-align: center;",
                    ),
                    cls="grid",
                    style="margin-bottom: 2rem;",
                ),
                # Phase flow visualization
                Div(
                    H3("Phase Flow"),
                    Div(
                        *[
                            Div(
                                # Phase header
                                Div(
                                    Strong(phase),
                                    style=f"color: {phase_colors.get(phase, '#666')};",
                                ),
                                # Progress bar
                                Div(
                                    Div(
                                        style=f"width: {(phase_counts.get(phase, 0) / max_count * 100) if max_count > 0 else 0}%; "
                                        f"height: 100%; background: {phase_colors.get(phase, '#666')}; "
                                        "border-radius: 4px; transition: width 0.3s;",
                                    ),
                                    style="width: 100%; height: 24px; background: #e5e7eb; border-radius: 4px; overflow: hidden;",
                                ),
                                # Count
                                Div(
                                    Span(f"{phase_counts.get(phase, 0)} tasks"),
                                    (
                                        Span(
                                            f" | {phase_defects.get(phase, 0)} defects",
                                            cls="pico-color-red",
                                        )
                                        if phase_defects.get(phase, 0) > 0
                                        else None
                                    ),
                                    style="font-size: 0.85rem; margin-top: 0.25rem;",
                                ),
                                style="margin-bottom: 1rem;",
                            )
                            for phase in phases
                        ],
                        cls="card",
                        style="padding: 1.5rem;",
                    ),
                    style="margin-bottom: 2rem;",
                ),
                # Transition flow (simplified Sankey)
                (
                    Div(
                        H3("Phase Transitions"),
                        Table(
                            Thead(
                                Tr(
                                    Th("From"),
                                    Th("To"),
                                    Th("Tasks"),
                                    Th("Flow"),
                                )
                            ),
                            Tbody(
                                *[
                                    Tr(
                                        Td(t["from"]),
                                        Td(t["to"]),
                                        Td(str(t["count"])),
                                        Td(
                                            Div(
                                                Div(
                                                    style=f"width: {(t['count'] / max_count * 100) if max_count > 0 else 0}%; "
                                                    "height: 100%; background: #06b6d4; border-radius: 2px;",
                                                ),
                                                style="width: 100px; height: 12px; background: #e5e7eb; border-radius: 2px; overflow: hidden;",
                                            )
                                        ),
                                    )
                                    for t in data["transitions"]
                                ]
                            ),
                        ),
                        cls="card",
                    )
                    if data["transitions"]
                    else P("No transition data available yet", cls="secondary")
                ),
                style="max-width: 1000px; margin: 0 auto; padding: 2rem;",
            ),
        )

    @rt("/manager/budget")
    def get_budget_page():
        """Budget settings and controls page."""
        settings = get_budget_settings()
        budget = get_budget_status()

        return Titled(
            "Budget Controls - Manager",
            Div(
                A("< Back to Dashboard", href="/manager"),
                H2("Budget Controls"),
                P(
                    "Set spending limits and alerts for API costs.",
                    cls="secondary",
                ),
                # Current status
                Div(
                    H3("Current Status"),
                    Div(
                        Div(
                            H4(
                                f"${budget['daily_spent']:.2f}",
                                cls=f"pico-color-{budget['status_color']}",
                            ),
                            P("Daily Spend"),
                            Div(
                                Div(
                                    style=f"width: {min(budget['daily_pct'], 100)}%; "
                                    f"height: 100%; background: {'#ef4444' if budget['daily_pct'] >= 100 else ('#f59e0b' if budget['daily_pct'] >= 80 else '#10b981')}; "
                                    "border-radius: 4px;",
                                ),
                                style="width: 100%; height: 16px; background: #e5e7eb; border-radius: 4px; overflow: hidden;",
                            ),
                            P(f"{budget['daily_pct']:.1f}% of limit", cls="secondary"),
                            cls="card",
                            style="text-align: center;",
                        ),
                        Div(
                            H4(
                                f"${budget['monthly_spent']:.2f}",
                                cls=f"pico-color-{budget['status_color']}",
                            ),
                            P("Monthly Spend"),
                            Div(
                                Div(
                                    style=f"width: {min(budget['monthly_pct'], 100)}%; "
                                    f"height: 100%; background: {'#ef4444' if budget['monthly_pct'] >= 100 else ('#f59e0b' if budget['monthly_pct'] >= 80 else '#10b981')}; "
                                    "border-radius: 4px;",
                                ),
                                style="width: 100%; height: 16px; background: #e5e7eb; border-radius: 4px; overflow: hidden;",
                            ),
                            P(
                                f"{budget['monthly_pct']:.1f}% of limit",
                                cls="secondary",
                            ),
                            cls="card",
                            style="text-align: center;",
                        ),
                        Div(
                            H4(
                                budget["status"].upper(),
                                cls=f"pico-color-{budget['status_color']}",
                            ),
                            P("Status"),
                            cls="card",
                            style="text-align: center;",
                        ),
                        cls="grid",
                    ),
                    style="margin-bottom: 2rem;",
                ),
                # Settings form
                Div(
                    H3("Budget Settings"),
                    Form(
                        Div(
                            Label("Daily Limit ($)", _for="daily_limit"),
                            Input(
                                type="number",
                                name="daily_limit",
                                id="daily_limit",
                                value=str(settings["daily_limit"]),
                                step="0.01",
                                min="0",
                            ),
                            cls="form-group",
                        ),
                        Div(
                            Label("Monthly Limit ($)", _for="monthly_limit"),
                            Input(
                                type="number",
                                name="monthly_limit",
                                id="monthly_limit",
                                value=str(settings["monthly_limit"]),
                                step="0.01",
                                min="0",
                            ),
                            cls="form-group",
                        ),
                        Div(
                            Label(
                                "Alert Threshold (%)",
                                _for="alert_threshold",
                            ),
                            Input(
                                type="number",
                                name="alert_threshold",
                                id="alert_threshold",
                                value=str(int(settings["alert_threshold"] * 100)),
                                step="5",
                                min="50",
                                max="100",
                            ),
                            Small(
                                "Alert when spending reaches this percentage of limit"
                            ),
                            cls="form-group",
                        ),
                        Div(
                            Label(
                                Input(
                                    type="checkbox",
                                    name="enabled",
                                    id="enabled",
                                    checked=settings["enabled"],
                                ),
                                " Enable budget controls",
                            ),
                            cls="form-group",
                        ),
                        Button(
                            "Save Settings",
                            type="submit",
                            cls="primary",
                        ),
                        Span(
                            id="save-status",
                            style="margin-left: 1rem;",
                        ),
                        hx_post="/manager/budget",
                        hx_target="#save-status",
                        hx_swap="innerHTML",
                    ),
                    cls="card",
                    style="padding: 1.5rem;",
                ),
                style="max-width: 800px; margin: 0 auto; padding: 2rem;",
            ),
        )

    @rt("/manager/budget")
    def post_budget(
        daily_limit: float = 10.0,
        monthly_limit: float = 100.0,
        alert_threshold: int = 80,
        enabled: bool = False,
    ):
        """Save budget settings."""
        settings = {
            "daily_limit": daily_limit,
            "monthly_limit": monthly_limit,
            "alert_threshold": alert_threshold / 100.0,
            "enabled": enabled,
        }

        if save_budget_settings(settings):
            return Span("Saved!", cls="pico-color-green")
        return Span("Error saving", cls="pico-color-red")

    @rt("/manager/budget-status")
    def get_budget_status_htmx():
        """HTMX endpoint for budget status updates."""
        budget = get_budget_status()

        return Div(
            H4(
                "Budget Status ",
                A(
                    "(Settings)",
                    href="/manager/budget",
                    style="font-size: 0.8rem; font-weight: normal;",
                ),
            ),
            Div(
                # Daily budget
                Div(
                    Div(
                        Span("Daily: ", style="font-weight: bold;"),
                        Span(
                            f"${budget['daily_spent']:.2f}",
                            cls=f"pico-color-{budget['status_color']}",
                        ),
                        Span(f" / ${budget['daily_limit']:.2f}"),
                    ),
                    Div(
                        Div(
                            style=f"width: {min(budget['daily_pct'], 100)}%; "
                            f"height: 100%; background: {'#ef4444' if budget['daily_pct'] >= 100 else ('#f59e0b' if budget['daily_pct'] >= 80 else '#10b981')}; "
                            "border-radius: 4px; transition: width 0.3s;",
                        ),
                        style="width: 100%; height: 12px; background: #e5e7eb; border-radius: 4px; overflow: hidden;",
                    ),
                    style="flex: 1;",
                ),
                # Monthly budget
                Div(
                    Div(
                        Span("Monthly: ", style="font-weight: bold;"),
                        Span(
                            f"${budget['monthly_spent']:.2f}",
                            cls=f"pico-color-{budget['status_color']}",
                        ),
                        Span(f" / ${budget['monthly_limit']:.2f}"),
                    ),
                    Div(
                        Div(
                            style=f"width: {min(budget['monthly_pct'], 100)}%; "
                            f"height: 100%; background: {'#ef4444' if budget['monthly_pct'] >= 100 else ('#f59e0b' if budget['monthly_pct'] >= 80 else '#10b981')}; "
                            "border-radius: 4px; transition: width 0.3s;",
                        ),
                        style="width: 100%; height: 12px; background: #e5e7eb; border-radius: 4px; overflow: hidden;",
                    ),
                    style="flex: 1;",
                ),
                style="display: flex; gap: 2rem;",
            ),
        )

    @rt("/manager/active-agents")
    def get_active_agents_htmx():
        """HTMX endpoint for active agents updates."""
        active_agents = get_active_agents()

        if not active_agents:
            return Div()  # Empty when no active agents

        return Div(
            H3(
                "Active Agents ",
                Span(f"({len(active_agents)})", cls="pico-color-green"),
            ),
            Div(
                *[
                    Div(
                        Div(
                            Span(
                                a["agent_name"][0],
                                style="font-weight: bold; font-size: 1.2rem;",
                            ),
                            style="width: 40px; height: 40px; border-radius: 50%; "
                            "background: var(--pico-primary); color: white; "
                            "display: flex; align-items: center; justify-content: center;",
                        ),
                        Div(
                            Strong(a["agent_name"]),
                            P(
                                f"Working on {a['task_id']}",
                                style="margin: 0; font-size: 0.85rem;",
                                cls="secondary",
                            ),
                            style="margin-left: 0.75rem;",
                        ),
                        Div(
                            style="width: 12px; height: 12px; border-radius: 50%; "
                            "background: #22c55e; animation: pulse 2s infinite; margin-left: auto;",
                        ),
                        style="display: flex; align-items: center; padding: 0.75rem; "
                        "border: 1px solid var(--pico-muted-border-color); border-radius: 8px; "
                        "margin-right: 1rem; margin-bottom: 0.5rem;",
                    )
                    for a in active_agents
                ],
                style="display: flex; flex-wrap: wrap;",
            ),
        )

    @rt("/manager/running-tasks")
    def get_running_tasks_htmx():
        """HTMX endpoint for running tasks updates."""
        running_tasks = get_running_tasks()

        if not running_tasks:
            return Div()  # Empty when no running tasks

        return Div(
            H3(
                "Running Pipeline Tasks ",
                Span(f"({len(running_tasks)})", cls="pico-color-azure"),
            ),
            Div(
                *[
                    Div(
                        Div(
                            Strong(t["task_id"]),
                            Span(
                                f" - {t['phase'].replace('_', ' ').title()}",
                                cls="pico-color-azure",
                            ),
                        ),
                        Div(
                            Div(
                                style=f"width: {t['progress_pct']}%; height: 100%; "
                                "background: var(--pico-primary); border-radius: 4px; "
                                "transition: width 0.3s;",
                            ),
                            style="height: 8px; background: var(--pico-muted-border-color); "
                            "border-radius: 4px; margin: 0.5rem 0;",
                        ),
                        Small(f"{t['progress_pct']}% complete", cls="secondary"),
                        style="margin-bottom: 0.5rem;",
                    )
                    for t in running_tasks[:3]
                ],
            ),
            (
                A(
                    f"View all {len(running_tasks)} running tasks",
                    href="/product/running",
                    style="font-size: 0.9rem;",
                )
                if len(running_tasks) > 3
                else None
            ),
        )
