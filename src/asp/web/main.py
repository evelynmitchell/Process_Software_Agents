"""
ASP Web UI Entry Point

This module initializes the FastHTML application and routes requests to persona-specific views.

Three personas:
- Sarah (Engineering Manager): ASP Overwatch - system health, quality gates, agent status
- Alex (Developer): Flow State Canvas - task details, recent activity, tools
- Jordan (Product Manager): Project Overview - delivery metrics, task pipeline
"""

from fasthtml.common import *
from .developer import developer_routes
from .manager import manager_routes
from .product import product_routes


def create_app():
    """Create and configure the FastHTML application."""
    app, rt = fast_app(
        pico=True,  # Use PicoCSS for styling
        hdrs=(
            Link(rel='stylesheet', href='https://cdn.jsdelivr.net/npm/@picocss/pico@2/css/pico.colors.min.css'),
        )
    )

    @rt('/')
    def get():
        """Home page with persona selection."""
        return Titled("ASP Platform",
            Div(
                H1("ASP Overwatch"),
                P("Select your dashboard view:", cls="secondary"),
                Div(
                    A(
                        Div(
                            H3("Sarah"),
                            P("Engineering Manager"),
                            Small("System health, quality gates, agent status"),
                        ),
                        href="/manager",
                        role="button",
                        cls="outline",
                        style="text-align: left; text-decoration: none;"
                    ),
                    A(
                        Div(
                            H3("Alex"),
                            P("Senior Developer"),
                            Small("Task details, recent activity, tools"),
                        ),
                        href="/developer",
                        role="button",
                        style="text-align: left; text-decoration: none;"
                    ),
                    A(
                        Div(
                            H3("Jordan"),
                            P("Product Manager"),
                            Small("Delivery metrics, task pipeline, progress"),
                        ),
                        href="/product",
                        role="button",
                        cls="outline",
                        style="text-align: left; text-decoration: none;"
                    ),
                    cls="grid"
                ),
                style="max-width: 900px; margin: 0 auto; padding-top: 2rem;"
            )
        )

    @rt('/health')
    def get_health():
        """Health check endpoint for monitoring."""
        return {"status": "healthy", "service": "asp-web-ui"}

    # Register persona routes
    developer_routes(app, rt)
    manager_routes(app, rt)
    product_routes(app, rt)

    return app


app = create_app()
