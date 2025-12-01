"""
Developer Persona (Alex) - Flow State Canvas

This module implements the web UI for the Senior Developer persona.
"""

from fasthtml.common import *


def developer_routes(app, rt):

    @rt("/developer")
    def get_developer():
        return Titled(
            "Flow State Canvas - Alex",
            Div(
                # Sidebar / Navigation
                Div(
                    H3("Active Tasks"),
                    Ul(
                        Li(A("Implement User+LLM Telemetry", href="#")),
                        Li(A("Refactor CI Pipeline", href="#")),
                    ),
                    Hr(),
                    H3("Tools"),
                    Ul(
                        Li(A("Generate Code", href="#")),
                        Li(A("Run Tests", href="#")),
                        Li(A("View Traces", href="#")),
                    ),
                    cls="sidebar",
                    style="width: 250px; border-right: 1px solid var(--pico-muted-border-color); padding-right: 1rem;",
                ),
                # Main Content Area
                Div(
                    Div(
                        H2("Current Context: Telemetry Implementation"),
                        P("Status: In Progress", cls="pico-color-azure"),
                        Div(
                            H4("Recent Activity"),
                            Table(
                                Thead(Tr(Th("Time"), Th("Action"), Th("Status"))),
                                Tbody(
                                    Tr(
                                        Td("10:05"),
                                        Td("Updated telemetry.py"),
                                        Td("Success", cls="pico-color-green"),
                                    ),
                                    Tr(
                                        Td("10:02"),
                                        Td("Ran migration"),
                                        Td("Success", cls="pico-color-green"),
                                    ),
                                    Tr(
                                        Td("09:55"),
                                        Td("Failed test execution"),
                                        Td("Failed", cls="pico-color-red"),
                                    ),
                                ),
                            ),
                            cls="card",
                        ),
                        Div(
                            H4("Quick Actions"),
                            Div(
                                Button("Run Unit Tests", cls="secondary"),
                                Button("Generate PR Description", cls="secondary"),
                                cls="grid",
                            ),
                            cls="card",
                            style="margin-top: 1rem;",
                        ),
                    ),
                    style="flex-grow: 1; padding-left: 2rem;",
                ),
                style="display: flex; min-height: 80vh;",
            ),
        )
