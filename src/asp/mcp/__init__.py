"""
ASP MCP Server Package.

Exposes ASP agents as MCP (Model Context Protocol) tools for Claude Code CLI.

Tools:
- asp_plan: Generate project plans using PlanningAgent
- asp_code_review: Review code using CodeReviewOrchestrator
- asp_diagnose: Diagnose errors using DiagnosticAgent
- asp_test: Generate and analyze tests using TestAgent

Usage:
    # Run the MCP server
    python -m asp.mcp.server

    # Or configure in .mcp.json for Claude Code
"""

from asp.mcp.server import create_server, main, server

__all__ = ["create_server", "main", "server"]
