"""
ASP Web UI Entry Point

This module initializes the FastHTML application and routes requests to persona-specific views.
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
                # Header
                Div(
                    H1("Agile Software Process Platform"),
                    P("Select your persona to access the appropriate dashboard."),
                    style="text-align: center; margin-bottom: 3rem;"
                ),

                # Persona Selection Grid
                Div(
                    # Sarah - Engineering Manager
                    A(
                        Div(
                            Div("👩‍💼", style="font-size: 3rem;"),
                            H3("Sarah"),
                            P("Engineering Manager", cls="pico-color-azure"),
                            Small("Process oversight, metrics, approvals"),
                            cls="persona-card"
                        ),
                        href="/manager",
                    ),
                    # Alex - Developer
                    A(
                        Div(
                            Div("👨‍💻", style="font-size: 3rem;"),
                            H3("Alex"),
                            P("Senior Developer", cls="pico-color-jade"),
                            Small("Code, tests, implementation"),
                            cls="persona-card"
                        ),
                        href="/developer",
                    ),
                    # Jordan - Product Manager
                    A(
                        Div(
                            Div("📋", style="font-size: 3rem;"),
                            H3("Jordan"),
                            P("Product Manager", cls="pico-color-amber"),
                            Small("Requirements, priorities, acceptance"),
                            cls="persona-card"
                        ),
                        href="/product",
                    ),
                    cls="grid",
                    style="gap: 2rem;"
                ),

                # System Status
                Div(
                    Hr(),
                    H4("System Status"),
                    Div(
                        hx_get="/api/system-status",
                        hx_trigger="load, every 30s",
                        hx_swap="innerHTML"
                    ),
                    style="margin-top: 3rem; text-align: center;"
                ),

                style="max-width: 900px; margin: 0 auto; padding: 2rem;"
            )
        )

    @rt('/api/system-status')
    def get_system_status():
        """Return system status HTML fragment."""
        # Check database connectivity
        from .api import get_db_connection
        db_conn = get_db_connection()
        db_status = "active" if db_conn else "error"
        if db_conn:
            db_conn.close()

        return Div(
            Span(cls=f"status-indicator status-{db_status}"),
            f"Database: {'Connected' if db_status == 'active' else 'Not Available'}",
            " | ",
            Span(cls="status-indicator status-active"),
            "Web UI: Running",
        )

    # Register persona routes
    developer_routes(app, rt)
    manager_routes(app, rt)
    product_routes(app, rt)

    return app


app = create_app()
