"""
ASP CLI - Command-line interface for running agent pipelines.

This module provides a CLI for executing ASP agent pipelines,
designed for use in containerized environments.
"""

from .main import app, main

__all__ = ["app", "main"]
