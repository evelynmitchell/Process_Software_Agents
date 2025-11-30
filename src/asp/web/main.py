"""
ASP Web UI Entry Point

This module initializes the FastHTML application and routes requests to persona-specific views.
"""

from fasthtml.common import *
from .developer import developer_routes

def create_app():
    app, rt = fast_app(
        pico=True,  # Use PicoCSS for styling
        hdrs=(
            Link(rel='stylesheet', href='https://cdn.jsdelivr.net/npm/@picocss/pico@2/css/pico.colors.min.css'),
        )
    )

    @rt('/')
    def get():
        return Titled("ASP Platform",
            Div(
                H1("Select Persona"),
                Div(
                    A("Sarah (Engineering Manager)", href="/manager", role="button", cls="outline"),
                    A("Alex (Developer)", href="/developer", role="button"),
                    A("Jordan (Product Manager)", href="/product", role="button", cls="outline"),
                    cls="grid"
                ),
                style="max-width: 800px; margin: 0 auto; padding-top: 2rem;"
            )
        )

    # Register persona routes
    developer_routes(app, rt)

    return app

app = create_app()
