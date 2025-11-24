"""
Package initialization file for the src module.

This file makes the src directory a proper Python package and exports
the public API of the Fibonacci module.

Author: ASP Code Agent
"""

from src.fibonacci import fibonacci

__all__ = ["fibonacci"]
__version__ = "1.0.0"