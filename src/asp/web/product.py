"""
Product Manager Persona (Jordan) - Requirements & Progress

This module implements the web UI for the Product Manager persona.
Focus: Requirements tracking, acceptance criteria, project progress.
"""

from fasthtml.common import *

from .api import get_project_progress, get_tasks_pending_approval


def product_routes(app, rt):
    """Register routes for the Product Manager persona."""

    @rt('/product')
    def get_product():
        """Main dashboard for Product Manager."""
        return Titled("Requirements Hub - Jordan",
            # Header
            Div(
                Small("Product Manager View", cls="pico-color-jade"),
                H1("Requirements Hub"),
                P("Define requirements, track progress, and manage priorities."),
                style="margin-bottom: 2rem;"
            ),

            # Progress Overview
            Div(
                Div(
                    H4("Project Progress"),
                    Div(
                        hx_get="/product/api/progress",
                        hx_trigger="load",
                        hx_swap="innerHTML"
                    ),
                    cls="card"
                ),
                Div(
                    H4("Requirements Status"),
                    Div(
                        hx_get="/product/api/requirements-status",
                        hx_trigger="load",
                        hx_swap="innerHTML"
                    ),
                    cls="card"
                ),
                cls="grid"
            ),

            # Requirements List
            Div(
                H3("Active Requirements"),
                Div(
                    hx_get="/product/api/requirements-list",
                    hx_trigger="load",
                    hx_swap="innerHTML"
                ),
                cls="card",
                style="margin-top: 2rem;"
            ),

            # Quick Actions
            Div(
                H3("Actions"),
                Div(
                    Button("New Requirement", cls="primary"),
                    Button("Export Report", cls="secondary"),
                    Button("Schedule Review", cls="outline"),
                    cls="grid"
                ),
                style="margin-top: 2rem;"
            ),

            # Navigation
            Div(
                A("Back to Home", href="/", role="button", cls="outline"),
                style="margin-top: 2rem;"
            ),

            style="max-width: 1200px; margin: 0 auto; padding: 2rem;"
        )

    # API Endpoints

    @rt('/product/api/progress')
    def get_progress_view():
        """Return project progress HTML fragment."""
        data = get_project_progress()

        if data["total"] == 0:
            return Div(
                P("No tasks tracked yet.", cls="pico-color-grey"),
                Small("Progress will appear as tasks are executed.")
            )

        completion_pct = (data["completed"] / data["total"] * 100) if data["total"] > 0 else 0

        return Div(
            # Progress bar
            Progress(value=str(completion_pct), max="100"),
            P(
                Strong(f"{completion_pct:.0f}%"),
                f" complete ({data['completed']}/{data['total']} tasks)"
            ),
            Hr(),
            Ul(
                Li(f"Completed: {data['completed']}", cls="pico-color-green"),
                Li(f"In Progress: {data['in_progress']}", cls="pico-color-amber"),
            )
        )

    @rt('/product/api/requirements-status')
    def get_requirements_status_view():
        """Return requirements status HTML fragment."""
        # Placeholder data - would connect to requirements system
        requirements = {
            "defined": 12,
            "in_development": 4,
            "testing": 2,
            "accepted": 8,
        }

        return Div(
            Table(
                Tbody(
                    Tr(Td("Defined"), Td(Strong(str(requirements["defined"])))),
                    Tr(Td("In Development"), Td(Strong(str(requirements["in_development"])), cls="pico-color-azure")),
                    Tr(Td("Testing"), Td(Strong(str(requirements["testing"])), cls="pico-color-amber")),
                    Tr(Td("Accepted"), Td(Strong(str(requirements["accepted"])), cls="pico-color-green")),
                )
            )
        )

    @rt('/product/api/requirements-list')
    def get_requirements_list_view():
        """Return requirements list HTML fragment."""
        # Placeholder data - would connect to requirements system
        requirements = [
            {"id": "REQ-001", "title": "User Authentication", "priority": "High", "status": "Accepted"},
            {"id": "REQ-002", "title": "API Rate Limiting", "priority": "High", "status": "In Development"},
            {"id": "REQ-003", "title": "Dashboard Analytics", "priority": "Medium", "status": "Defined"},
            {"id": "REQ-004", "title": "Export to CSV", "priority": "Low", "status": "Testing"},
            {"id": "REQ-005", "title": "Multi-tenant Support", "priority": "High", "status": "Defined"},
        ]

        priority_colors = {
            "High": "pico-color-red",
            "Medium": "pico-color-amber",
            "Low": "pico-color-grey",
        }

        status_colors = {
            "Defined": "",
            "In Development": "pico-color-azure",
            "Testing": "pico-color-amber",
            "Accepted": "pico-color-green",
        }

        return Table(
            Thead(
                Tr(
                    Th("ID"),
                    Th("Requirement"),
                    Th("Priority"),
                    Th("Status"),
                    Th("Actions"),
                )
            ),
            Tbody(
                *[
                    Tr(
                        Td(Code(req["id"])),
                        Td(req["title"]),
                        Td(req["priority"], cls=priority_colors.get(req["priority"], "")),
                        Td(req["status"], cls=status_colors.get(req["status"], "")),
                        Td(
                            A("View", href="#", style="margin-right: 0.5rem;"),
                            A("Edit", href="#"),
                        ),
                    )
                    for req in requirements
                ]
            )
        )
