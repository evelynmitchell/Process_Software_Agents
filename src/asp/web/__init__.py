"""
ASP Web UI Package

FastHTML-based web interface for the ASP Platform.
Provides persona-specific dashboards for different user roles.
"""

from .main import app, create_app

__all__ = ["app", "create_app"]
