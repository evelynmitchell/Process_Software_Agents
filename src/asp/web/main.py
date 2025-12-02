"""
ASP Web UI Entry Point

This module initializes the FastHTML application and routes requests to persona-specific views.

Three personas:
- Sarah (Engineering Manager): ASP Overwatch - system health, quality gates, agent status
- Alex (Developer): Flow State Canvas - task details, recent activity, tools
- Jordan (Product Manager): Project Overview - delivery metrics, task pipeline
"""

from fasthtml.common import *

from .components import theme_toggle
from .developer import developer_routes
from .manager import manager_routes
from .product import product_routes


def create_app():
    """Create and configure the FastHTML application."""
    app, rt = fast_app(
        pico=True,  # Use PicoCSS for styling
        hdrs=(
            Link(
                rel="stylesheet",
                href="https://cdn.jsdelivr.net/npm/@picocss/pico@2/css/pico.colors.min.css",
            ),
            Style(
                """
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

                /* Dark mode toggle */
                .theme-toggle {
                    position: fixed;
                    top: 1rem;
                    right: 1rem;
                    z-index: 1000;
                    padding: 0.5rem 1rem;
                    font-size: 0.9rem;
                    cursor: pointer;
                    border-radius: var(--pico-border-radius);
                    background: var(--pico-card-background-color);
                    border: 1px solid var(--pico-muted-border-color);
                    color: var(--pico-color);
                    display: flex;
                    align-items: center;
                    gap: 0.5rem;
                }
                .theme-toggle:hover {
                    border-color: var(--pico-primary);
                }
                .theme-icon {
                    font-size: 1.2rem;
                }

                /* Agent presence pulse animation */
                @keyframes pulse {
                    0% { opacity: 1; transform: scale(1); }
                    50% { opacity: 0.6; transform: scale(1.1); }
                    100% { opacity: 1; transform: scale(1); }
                }

                /* Code diff view styles */
                .diff-view {
                    font-family: 'SF Mono', 'Consolas', 'Monaco', monospace;
                    font-size: 0.85rem;
                    line-height: 1.5;
                    overflow-x: auto;
                }
                .diff-line {
                    padding: 2px 8px;
                    white-space: pre;
                }
                .diff-add {
                    background: rgba(34, 197, 94, 0.2);
                    color: #22c55e;
                }
                .diff-remove {
                    background: rgba(239, 68, 68, 0.2);
                    color: #ef4444;
                }
                .diff-header {
                    background: var(--pico-muted-border-color);
                    color: var(--pico-color);
                    font-weight: bold;
                }
                .diff-hunk {
                    background: rgba(59, 130, 246, 0.1);
                    color: #3b82f6;
                }
                .line-number {
                    display: inline-block;
                    width: 40px;
                    text-align: right;
                    padding-right: 8px;
                    color: var(--pico-muted-color);
                    user-select: none;
                }
            """
            ),
            # Theme initialization and toggle script
            Script(
                """
                (function() {
                    // Check for saved preference or system preference
                    const savedTheme = localStorage.getItem('asp-theme');
                    const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
                    const theme = savedTheme || (prefersDark ? 'dark' : 'light');
                    document.documentElement.setAttribute('data-theme', theme);
                })();

                // Global theme toggle function
                function updateThemeButton(theme) {
                    const icon = document.getElementById('theme-icon');
                    const text = document.getElementById('theme-text');
                    if (icon && text) {
                        if (theme === 'dark') {
                            icon.textContent = '\u2600\ufe0f';
                            text.textContent = 'Light';
                        } else {
                            icon.textContent = '\ud83c\udf19';
                            text.textContent = 'Dark';
                        }
                    }
                }

                // Initialize button on load
                document.addEventListener('DOMContentLoaded', function() {
                    const theme = document.documentElement.getAttribute('data-theme') || 'light';
                    updateThemeButton(theme);
                });
            """
            ),
        ),
    )

    @rt("/")
    def get():
        """Home page with persona selection."""
        return Titled(
            "ASP Platform",
            theme_toggle(),
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
                        style="text-align: left; text-decoration: none;",
                    ),
                    A(
                        Div(
                            H3("Alex"),
                            P("Senior Developer"),
                            Small("Task details, recent activity, tools"),
                        ),
                        href="/developer",
                        role="button",
                        style="text-align: left; text-decoration: none;",
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
                        style="text-align: left; text-decoration: none;",
                    ),
                    cls="grid",
                ),
                style="max-width: 900px; margin: 0 auto; padding-top: 2rem;",
            ),
        )

    @rt("/health")
    def get_health():
        """Health check endpoint for monitoring."""
        return {"status": "healthy", "service": "asp-web-ui"}

    # Register persona routes
    developer_routes(app, rt)
    manager_routes(app, rt)
    product_routes(app, rt)

    return app


app = create_app()
