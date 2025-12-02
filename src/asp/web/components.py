"""
Shared UI Components for ASP Web UI

Provides reusable UI components used across persona dashboards.
"""

from fasthtml.common import Button, Span


def theme_toggle():
    """Create the theme toggle button component.

    This button allows users to toggle between light and dark themes.
    Theme preference is persisted in localStorage.
    """
    return Button(
        Span("", cls="theme-icon", id="theme-icon"),
        Span("Theme", id="theme-text"),
        cls="theme-toggle",
        id="theme-toggle",
        onclick="""
            const html = document.documentElement;
            const currentTheme = html.getAttribute('data-theme') || 'light';
            const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
            html.setAttribute('data-theme', newTheme);
            localStorage.setItem('asp-theme', newTheme);
            updateThemeButton(newTheme);
        """,
    )
