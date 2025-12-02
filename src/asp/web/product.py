"""
Product Persona (Jordan) - Project Overview Dashboard

This module implements the web UI for the Product Manager persona.
Displays project progress, task pipeline, and delivery metrics.
"""

# pylint: disable=no-value-for-parameter,undefined-variable,wildcard-import,unused-wildcard-import
# FastHTML components use *args and star imports which pylint cannot analyze correctly
from fasthtml.common import *

from .components import theme_toggle
from .data import (
    get_agent_stats,
    get_running_tasks,
    get_tasks,
    register_task_execution,
    simulate_timeline,
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
                        A(
                            "What-If Simulator",
                            href="/product/timeline",
                            role="button",
                            cls="secondary",
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
    def post_new_feature(
        task_id: str, description: str, requirements: str, priority: str = "normal"
    ):
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
                                P(
                                    (
                                        t["description"][:60] + "..."
                                        if len(t.get("description", "")) > 60
                                        else t.get("description", "")
                                    ),
                                    style="margin: 0.5rem 0;",
                                ),
                                # Progress bar
                                Div(
                                    Div(
                                        style=f"width: {t['progress_pct']}%; height: 100%; background: var(--pico-primary); border-radius: 4px; transition: width 0.3s;",
                                    ),
                                    style="height: 8px; background: var(--pico-muted-border-color); border-radius: 4px; margin: 0.5rem 0;",
                                ),
                                Small(
                                    f"{t['progress_pct']}% complete", cls="secondary"
                                ),
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
                    P(
                        (
                            t["description"][:60] + "..."
                            if len(t.get("description", "")) > 60
                            else t.get("description", "")
                        ),
                        style="margin: 0.5rem 0;",
                    ),
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

    # =========================================================================
    # What-If Scenario Simulator
    # =========================================================================

    @rt("/product/timeline")
    def get_timeline():
        """What-If scenario simulator - Timeline view."""
        # Get initial simulation with default parameters
        sim = simulate_timeline(team_capacity=1.0, budget_multiplier=1.0)

        return Titled(
            "What-If Scenario Simulator",
            theme_toggle(),
            # Custom CSS for timeline
            Style(
                """
                .timeline-bar {
                    height: 28px;
                    border-radius: 4px;
                    position: relative;
                    margin: 4px 0;
                    display: flex;
                    align-items: center;
                    padding: 0 8px;
                    font-size: 0.8em;
                    color: white;
                    white-space: nowrap;
                    overflow: hidden;
                    text-overflow: ellipsis;
                }
                .timeline-bar.completed { background: linear-gradient(90deg, #22c55e, #16a34a); opacity: 0.7; }
                .timeline-bar.in_progress { background: linear-gradient(90deg, #3b82f6, #2563eb); }
                .timeline-bar.planned { background: linear-gradient(90deg, #8b5cf6, #7c3aed); }
                .timeline-bar.high-risk { border: 2px solid #ef4444; }
                .risk-badge {
                    display: inline-block;
                    padding: 2px 8px;
                    border-radius: 10px;
                    font-size: 0.75em;
                    margin-left: 8px;
                }
                .risk-low { background: #22c55e; color: white; }
                .risk-medium { background: #f59e0b; color: white; }
                .risk-high { background: #ef4444; color: white; }
                .risk-none { background: #6b7280; color: white; }
                .prob-meter {
                    height: 24px;
                    background: var(--pico-muted-border-color);
                    border-radius: 12px;
                    overflow: hidden;
                    position: relative;
                }
                .prob-fill {
                    height: 100%;
                    border-radius: 12px;
                    transition: width 0.3s ease;
                }
                .prob-text {
                    position: absolute;
                    top: 50%;
                    left: 50%;
                    transform: translate(-50%, -50%);
                    font-weight: bold;
                    font-size: 0.85em;
                }
                .slider-container { margin: 1rem 0; }
                .slider-container label { display: block; margin-bottom: 0.5rem; }
                .slider-value {
                    display: inline-block;
                    min-width: 60px;
                    text-align: center;
                    font-weight: bold;
                }
            """
            ),
            Div(
                A("< Back to Dashboard", href="/product"),
                H2("What-If Scenario Simulator"),
                P(
                    "Adjust parameters to see how they affect your project timeline and delivery probability.",
                    cls="secondary",
                ),
                # Control Panel
                Div(
                    H3("Simulation Parameters"),
                    Div(
                        # Team Capacity Slider
                        Div(
                            Label("Team Capacity"),
                            Div(
                                Input(
                                    type="range",
                                    id="team-capacity",
                                    name="team_capacity",
                                    min="0.25",
                                    max="2.0",
                                    step="0.25",
                                    value="1.0",
                                    style="flex: 1;",
                                    hx_get="/product/timeline/simulate",
                                    hx_trigger="change",
                                    hx_target="#simulation-results",
                                    hx_include="[name='team_capacity'], [name='budget_multiplier']",
                                ),
                                Span("1.0x", id="capacity-display", cls="slider-value"),
                                style="display: flex; align-items: center; gap: 1rem;",
                            ),
                            Small(
                                "0.25x (skeleton crew) to 2.0x (double capacity)",
                                cls="secondary",
                            ),
                            cls="slider-container",
                        ),
                        # Budget Slider
                        Div(
                            Label("Budget Multiplier"),
                            Div(
                                Input(
                                    type="range",
                                    id="budget-multiplier",
                                    name="budget_multiplier",
                                    min="0.5",
                                    max="2.0",
                                    step="0.25",
                                    value="1.0",
                                    style="flex: 1;",
                                    hx_get="/product/timeline/simulate",
                                    hx_trigger="change",
                                    hx_target="#simulation-results",
                                    hx_include="[name='team_capacity'], [name='budget_multiplier']",
                                ),
                                Span("1.0x", id="budget-display", cls="slider-value"),
                                style="display: flex; align-items: center; gap: 1rem;",
                            ),
                            Small(
                                "0.5x (constrained) to 2.0x (expanded)", cls="secondary"
                            ),
                            cls="slider-container",
                        ),
                        cls="grid",
                    ),
                    cls="card",
                    style="margin-bottom: 1.5rem;",
                ),
                # Simulation Results Container
                Div(
                    _render_simulation_results(sim),
                    id="simulation-results",
                ),
                # JavaScript for slider value display
                Script(
                    """
                    document.getElementById('team-capacity').addEventListener('input', function(e) {
                        document.getElementById('capacity-display').textContent = e.target.value + 'x';
                    });
                    document.getElementById('budget-multiplier').addEventListener('input', function(e) {
                        document.getElementById('budget-display').textContent = e.target.value + 'x';
                    });
                """
                ),
                style="max-width: 1200px; margin: 2rem auto; padding: 2rem;",
            ),
        )

    @rt("/product/timeline/simulate")
    def get_timeline_simulate(
        team_capacity: float = 1.0, budget_multiplier: float = 1.0
    ):
        """HTMX endpoint for timeline simulation updates."""
        sim = simulate_timeline(
            team_capacity=float(team_capacity),
            budget_multiplier=float(budget_multiplier),
        )
        return _render_simulation_results(sim)


def _render_simulation_results(sim: dict) -> Div:
    """Render the simulation results as HTML components."""
    features = sim.get("features", [])
    total_weeks = sim.get("total_weeks", 0)
    completion_prob = sim.get("completion_probability", 0)
    early_prob = sim.get("early_probability", 0)
    suggestions = sim.get("suggestions", [])
    risk_summary = sim.get("risk_summary", {})

    # Probability color based on value
    def prob_color(pct):
        if pct >= 70:
            return "#22c55e"  # green
        if pct >= 50:
            return "#f59e0b"  # yellow
        return "#ef4444"  # red

    # Build timeline bars
    max_week = max((f.get("end_week", 0) for f in features), default=4) or 4
    timeline_bars = []

    for f in features:
        if f["status"] == "completed":
            continue  # Skip completed in timeline view

        start_pct = (f.get("start_week", 0) / max_week) * 100
        width_pct = max(5, (f.get("adjusted_duration", 0.5) / max_week) * 100)
        risk_class = "high-risk" if f.get("risk") == "high" else ""

        timeline_bars.append(
            Div(
                Div(
                    Span(f["id"]),
                    Span(f["name"], style="margin-left: 8px; opacity: 0.9;"),
                    Span(
                        f"{f.get('confidence', 50)}%",
                        cls=f"risk-badge risk-{f.get('risk', 'low')}",
                    ),
                    cls=f"timeline-bar {f['status']} {risk_class}",
                    style=f"margin-left: {start_pct}%; width: {width_pct}%;",
                ),
                style="margin-bottom: 4px;",
            )
        )

    # Week markers
    week_markers = []
    for w in range(int(max_week) + 1):
        week_markers.append(
            Span(
                f"W{w}",
                style=f"position: absolute; left: {(w / max_week) * 100}%; font-size: 0.75em; color: var(--pico-muted-color);",
            )
        )

    return Div(
        # Probability Meters
        Div(
            H3("Delivery Probability"),
            Div(
                # On-time probability
                Div(
                    Label("On-Time Delivery"),
                    Div(
                        Div(
                            style=f"width: {completion_prob}%; background: {prob_color(completion_prob)};",
                            cls="prob-fill",
                        ),
                        Span(f"{completion_prob}%", cls="prob-text"),
                        cls="prob-meter",
                    ),
                    P(
                        f"Estimated completion: {total_weeks} weeks",
                        cls="secondary",
                        style="margin-top: 0.5rem;",
                    ),
                ),
                # Early probability
                Div(
                    Label("Early Delivery (20% faster)"),
                    Div(
                        Div(
                            style=f"width: {early_prob}%; background: {prob_color(early_prob)};",
                            cls="prob-fill",
                        ),
                        Span(f"{early_prob}%", cls="prob-text"),
                        cls="prob-meter",
                    ),
                    P(
                        f"Target: {total_weeks * 0.8:.1f} weeks",
                        cls="secondary",
                        style="margin-top: 0.5rem;",
                    ),
                ),
                cls="grid",
            ),
            cls="card",
            style="margin-bottom: 1.5rem;",
        ),
        # Risk Summary
        Div(
            H3("Risk Summary"),
            Div(
                Div(
                    H4(str(risk_summary.get("low", 0)), style="margin: 0;"),
                    P("Low Risk", cls="secondary", style="margin: 0;"),
                    cls="card",
                    style="text-align: center; background: rgba(34, 197, 94, 0.1); border-left: 4px solid #22c55e;",
                ),
                Div(
                    H4(str(risk_summary.get("medium", 0)), style="margin: 0;"),
                    P("Medium Risk", cls="secondary", style="margin: 0;"),
                    cls="card",
                    style="text-align: center; background: rgba(245, 158, 11, 0.1); border-left: 4px solid #f59e0b;",
                ),
                Div(
                    H4(str(risk_summary.get("high", 0)), style="margin: 0;"),
                    P("High Risk", cls="secondary", style="margin: 0;"),
                    cls="card",
                    style="text-align: center; background: rgba(239, 68, 68, 0.1); border-left: 4px solid #ef4444;",
                ),
                Div(
                    H4(str(risk_summary.get("none", 0)), style="margin: 0;"),
                    P("Completed", cls="secondary", style="margin: 0;"),
                    cls="card",
                    style="text-align: center; background: rgba(107, 114, 128, 0.1); border-left: 4px solid #6b7280;",
                ),
                cls="grid",
            ),
            cls="card",
            style="margin-bottom: 1.5rem;",
        ),
        # Timeline Visualization
        Div(
            H3("Project Timeline"),
            Div(
                # Week axis
                Div(
                    *week_markers,
                    style="position: relative; height: 20px; border-bottom: 1px solid var(--pico-muted-border-color); margin-bottom: 1rem;",
                ),
                # Timeline bars
                Div(
                    *(
                        timeline_bars
                        if timeline_bars
                        else [P("No pending features in timeline.", cls="secondary")]
                    ),
                    style="min-height: 100px;",
                ),
                style="padding: 1rem 0;",
            ),
            # Legend
            Div(
                Span("Legend: ", style="font-weight: bold;"),
                Span(
                    "In Progress",
                    style="background: linear-gradient(90deg, #3b82f6, #2563eb); color: white; padding: 2px 8px; border-radius: 4px; margin: 0 4px;",
                ),
                Span(
                    "Planned",
                    style="background: linear-gradient(90deg, #8b5cf6, #7c3aed); color: white; padding: 2px 8px; border-radius: 4px; margin: 0 4px;",
                ),
                Span(
                    "High Risk",
                    style="border: 2px solid #ef4444; padding: 2px 8px; border-radius: 4px; margin: 0 4px;",
                ),
                style="margin-top: 1rem; font-size: 0.85em;",
            ),
            cls="card",
            style="margin-bottom: 1.5rem;",
        ),
        # Suggestions
        Div(
            H3("Recommendations"),
            Ul(
                *[Li(s) for s in suggestions],
                style="margin: 0; padding-left: 1.5rem;",
            ),
            cls="card",
            style="background: rgba(59, 130, 246, 0.05); border-left: 4px solid #3b82f6;",
        ),
    )
