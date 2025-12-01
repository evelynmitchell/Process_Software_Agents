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
            Style("""
                .card {
                    background: var(--pico-card-background-color);
                    border-radius: var(--pico-border-radius);
                    padding: 1.5rem;
                    box-shadow: var(--pico-card-box-shadow);
                }
                .sidebar {
                    min-width: 250px;
                    border-right: 1px solid var(--pico-muted-border-color);
                    padding-right: 1rem;
                }
                .persona-card {
                    text-align: center;
                    padding: 2rem;
                    border: 2px solid var(--pico-muted-border-color);
                    border-radius: var(--pico-border-radius);
                    transition: all 0.2s ease;
                }
                .persona-card:hover {
                    border-color: var(--pico-primary);
                    transform: translateY(-2px);
                }
                .status-indicator {
                    display: inline-block;
                    width: 8px;
                    height: 8px;
                    border-radius: 50%;
                    margin-right: 0.5rem;
                }
                .status-active { background: #22c55e; }
                .status-pending { background: #eab308; }
                .status-error { background: #ef4444; }
            """),
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
