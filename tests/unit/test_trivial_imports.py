"""
Tests for trivial modules with 0% coverage.

These are simple import/instantiation tests for placeholder modules.

Author: ASP Development Team
Date: December 23, 2025
"""

import pytest


class TestAuthService:
    """Tests for AuthService placeholder class."""

    def test_auth_service_can_be_imported(self):
        """Verify AuthService can be imported."""
        from services.auth_service import AuthService

        assert AuthService is not None

    def test_auth_service_can_be_instantiated(self):
        """Verify AuthService can be instantiated."""
        from services.auth_service import AuthService

        service = AuthService()
        assert service is not None
        assert isinstance(service, AuthService)


class TestMCPInit:
    """Tests for MCP package initialization."""

    @pytest.fixture(autouse=True)
    def skip_if_no_mcp(self):
        """Skip MCP tests if mcp package not installed."""
        pytest.importorskip("mcp", reason="mcp not installed")

    def test_mcp_exports_are_available(self):
        """Verify MCP package exports are accessible."""
        from asp.mcp import create_server, main, server

        assert create_server is not None
        assert main is not None
        assert server is not None

    def test_mcp_all_exports(self):
        """Verify __all__ exports match actual exports."""
        import asp.mcp

        expected_exports = {"create_server", "main", "server"}
        assert set(asp.mcp.__all__) == expected_exports


class TestCLIMain:
    """Tests for CLI __main__ module."""

    def test_cli_main_can_be_imported(self):
        """Verify CLI main function can be imported."""
        from asp.cli.main import main

        assert main is not None
        assert callable(main)
