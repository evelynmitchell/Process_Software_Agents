"""
ASP Web UI Module

FastHTML-based web interface for the ASP Platform.
Provides persona-specific views for different user roles.
"""

from .main import create_app, app

__all__ = ["create_app", "app"]
