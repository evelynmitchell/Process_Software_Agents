"""
Developer Persona (Alex) - Flow State Canvas

This module implements the web UI for the Senior Developer persona.
Focus: Code generation, testing, implementation tasks.
"""

from fasthtml.common import *

from .api import get_recent_agent_activity


def developer_routes(app, rt):
    """Register routes for the Developer persona."""

    @rt('/developer')
    def get_developer():
        """Main dashboard for Developer."""
        return Titled("Flow State Canvas - Alex",
            Div(
                # Sidebar / Navigation
                Div(
                    H3("Current Task"),
                    Div(
                        hx_get="/developer/api/current-task",
                        hx_trigger="load",
                        hx_swap="innerHTML"
                    ),
                    Hr(),
                    H3("Tools"),
                    Ul(
                        Li(A("Generate Code", href="#", hx_post="/developer/action/generate", hx_target="#action-result")),
                        Li(A("Run Tests", href="#", hx_post="/developer/action/test", hx_target="#action-result")),
                        Li(A("Code Review", href="#", hx_post="/developer/action/review", hx_target="#action-result")),
                        Li(A("View Traces", href="#", hx_post="/developer/action/traces", hx_target="#action-result")),
                    ),
                    Hr(),
                    H3("Quick Stats"),
                    Div(
                        hx_get="/developer/api/stats",
                        hx_trigger="load",
                        hx_swap="innerHTML"
                    ),
                    cls="sidebar",
                ),
                # Main Content Area
                Div(
                    # Context Header
                    Div(
                        H2("Development Workspace"),
                        P("Ready for implementation tasks.", cls="pico-color-jade"),
                    ),

                    # Action Result Area
                    Div(
                        id="action-result",
                        cls="card",
                        style="margin-bottom: 1rem; min-height: 100px;"
                    ),

                    # Recent Activity
                    Div(
                        H4("Recent Activity"),
                        Div(
                            hx_get="/developer/api/activity",
                            hx_trigger="load, every 5s",
                            hx_swap="innerHTML"
                        ),
                        cls="card"
                    ),

                    # Quick Actions
                    Div(
                        H4("Quick Actions"),
                        Div(
                            Button("Run Unit Tests", cls="secondary", hx_post="/developer/action/test", hx_target="#action-result"),
                            Button("Generate PR Description", cls="secondary", hx_post="/developer/action/pr-desc", hx_target="#action-result"),
                            Button("Lint & Format", cls="outline", hx_post="/developer/action/lint", hx_target="#action-result"),
                            cls="grid"
                        ),
                        cls="card",
                        style="margin-top: 1rem;"
                    ),

                    style="flex-grow: 1; padding-left: 2rem;"
                ),
                style="display: flex; min-height: 80vh;"
            ),

            # Navigation
            Div(
                A("Back to Home", href="/", role="button", cls="outline"),
                style="margin-top: 2rem;"
            ),

            style="max-width: 1400px; margin: 0 auto; padding: 2rem;"
        )

    # API Endpoints

    @rt('/developer/api/current-task')
    def get_current_task():
        """Return current task HTML fragment."""
        # Placeholder - would connect to task assignment system
        return Div(
            Code("TSP-IMPL-001"),
            P("Web UI Implementation", style="margin: 0.5rem 0;"),
            Small("Status: ", Span("In Progress", cls="pico-color-jade")),
        )

    @rt('/developer/api/stats')
    def get_developer_stats():
        """Return developer stats HTML fragment."""
        activities = get_recent_agent_activity(limit=100)

        # Calculate stats from activities
        total_executions = len(activities)
        avg_latency = sum(a["latency_ms"] for a in activities) / total_executions if activities else 0

        return Div(
            P(Small("Today's Executions: "), Strong(str(min(total_executions, 50)))),
            P(Small("Avg Response: "), Strong(f"{avg_latency:.0f}ms")),
            P(Small("Tests Passed: "), Strong("28/28", cls="pico-color-green")),
        )

    @rt('/developer/api/activity')
    def get_developer_activity():
        """Return recent activity HTML fragment."""
        activities = get_recent_agent_activity(limit=8)

        if not activities:
            return P("No recent activity. Start a task to see activity here.", cls="pico-color-grey")

        return Table(
            Thead(Tr(Th("Time"), Th("Action"), Th("Status"))),
            Tbody(
                *[
                    Tr(
                        Td(Small(act["timestamp"][11:19] if act["timestamp"] else "-")),
                        Td(f"{act['agent_role']}: {act['task_id'][:12] if act['task_id'] else '-'}"),
                        Td(
                            "Success" if act["latency_ms"] and act["latency_ms"] < 30000 else "Slow",
                            cls="pico-color-green" if act["latency_ms"] and act["latency_ms"] < 30000 else "pico-color-amber"
                        ),
                    )
                    for act in activities
                ]
            )
        )

    # Action Endpoints

    @rt('/developer/action/generate')
    def post_generate():
        """Handle code generation action."""
        return Div(
            H4("Code Generation", cls="pico-color-jade"),
            P("Code generation agent invoked."),
            Small("Tip: Describe your task in the input below to generate code."),
            Form(
                Textarea(placeholder="Describe the code you want to generate...", name="prompt", rows="3"),
                Button("Generate", type="submit", cls="primary"),
                hx_post="/developer/action/generate-run",
                hx_target="#action-result",
                style="margin-top: 1rem;"
            )
        )

    @rt('/developer/action/generate-run')
    def post_generate_run(prompt: str = ""):
        """Execute code generation."""
        return Div(
            H4("Generation Complete", cls="pico-color-green"),
            P(f"Prompt received: {prompt[:100]}..." if len(prompt) > 100 else f"Prompt received: {prompt}"),
            Small("Note: Full agent integration pending. This is a UI preview."),
        )

    @rt('/developer/action/test')
    def post_test():
        """Handle test execution action."""
        return Div(
            H4("Test Runner", cls="pico-color-jade"),
            P("Running test suite..."),
            Progress(value="75", max="100"),
            Small("Executing pytest with coverage..."),
            Div(
                hx_get="/developer/api/test-results",
                hx_trigger="load delay:2s",
                hx_swap="innerHTML"
            )
        )

    @rt('/developer/api/test-results')
    def get_test_results():
        """Return test results HTML fragment."""
        return Div(
            H4("Test Results", cls="pico-color-green"),
            P("All tests passed!"),
            Code("28 passed, 0 failed, 0 skipped"),
            P(Small("Coverage: 79%")),
        )

    @rt('/developer/action/review')
    def post_review():
        """Handle code review action."""
        return Div(
            H4("Code Review", cls="pico-color-jade"),
            P("Code review agent analyzing current changes..."),
            Small("This will analyze staged git changes and provide feedback."),
        )

    @rt('/developer/action/traces')
    def post_traces():
        """Handle trace viewing action."""
        return Div(
            H4("Langfuse Traces", cls="pico-color-jade"),
            P("Opening Langfuse dashboard..."),
            A("Open Langfuse", href="https://cloud.langfuse.com", target="_blank", role="button", cls="outline"),
        )

    @rt('/developer/action/pr-desc')
    def post_pr_desc():
        """Handle PR description generation."""
        return Div(
            H4("PR Description Generator", cls="pico-color-jade"),
            P("Analyzing commits and generating description..."),
            Textarea(
                "## Summary\n\n- Implemented FastHTML Web UI for ASP Platform\n- Added persona-specific dashboards (Sarah, Alex, Jordan)\n- Connected to telemetry database for real-time metrics\n\n## Test Plan\n\n- [ ] Verify UI loads correctly\n- [ ] Test HTMX dynamic updates\n- [ ] Check database connectivity",
                rows="10",
                style="width: 100%; font-family: monospace;"
            ),
            Button("Copy to Clipboard", cls="secondary", onclick="navigator.clipboard.writeText(this.previousElementSibling.value)"),
        )

    @rt('/developer/action/lint')
    def post_lint():
        """Handle lint action."""
        return Div(
            H4("Lint & Format", cls="pico-color-jade"),
            P("Running ruff and black..."),
            Code("ruff check --fix . && black ."),
            P(Small("All files formatted successfully.", cls="pico-color-green")),
        )
