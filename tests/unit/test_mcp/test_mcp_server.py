"""
Unit tests for ASP MCP Server.

Tests the MCP server tool registration and handler functions.
"""

import json
import os
import tempfile
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Skip if mcp not installed
pytest.importorskip("mcp")

from asp.mcp.server import (  # noqa: E402
    _handle_provider_status,
    _handle_session_context,
    list_tools,
)


class TestToolRegistration:
    """Tests for MCP tool registration."""

    @pytest.mark.asyncio
    async def test_list_tools_returns_all_tools(self):
        """All 8 tools should be registered."""
        tools = await list_tools()
        assert len(tools) == 8

    @pytest.mark.asyncio
    async def test_list_tools_has_core_tools(self):
        """Core tools should be present."""
        tools = await list_tools()
        tool_names = [t.name for t in tools]

        assert "asp_plan" in tool_names
        assert "asp_code_review" in tool_names
        assert "asp_diagnose" in tool_names
        assert "asp_test" in tool_names

    @pytest.mark.asyncio
    async def test_list_tools_has_extended_tools(self):
        """Extended tools should be present."""
        tools = await list_tools()
        tool_names = [t.name for t in tools]

        assert "asp_repair_issue" in tool_names
        assert "asp_beads_sync" in tool_names
        assert "asp_provider_status" in tool_names
        assert "asp_session_context" in tool_names

    @pytest.mark.asyncio
    async def test_tools_have_descriptions(self):
        """All tools should have non-empty descriptions."""
        tools = await list_tools()
        for tool in tools:
            assert tool.description, f"Tool {tool.name} has no description"
            assert len(tool.description) > 20, f"Tool {tool.name} description too short"

    @pytest.mark.asyncio
    async def test_tools_have_input_schemas(self):
        """All tools should have input schemas."""
        tools = await list_tools()
        for tool in tools:
            assert tool.inputSchema, f"Tool {tool.name} has no input schema"
            assert tool.inputSchema.get("type") == "object"


class TestProviderStatusHandler:
    """Tests for asp_provider_status handler."""

    @pytest.mark.asyncio
    async def test_provider_status_without_registry(self):
        """Should return fallback when registry not available."""
        with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test-key"}):
            # Patch the import inside the function
            with patch.dict("sys.modules", {"asp.providers.registry": None}):
                result = await _handle_provider_status({})

        assert len(result) == 1
        data = json.loads(result[0].text)
        assert "providers" in data
        assert data["providers"]["anthropic"]["available"] is True

    @pytest.mark.asyncio
    async def test_provider_status_no_api_key(self):
        """Should show unavailable when no API key set."""
        # Save and clear the env var
        saved_key = os.environ.pop("ANTHROPIC_API_KEY", None)
        try:
            with patch.dict("sys.modules", {"asp.providers.registry": None}):
                result = await _handle_provider_status({})

            data = json.loads(result[0].text)
            assert data["providers"]["anthropic"]["available"] is False
        finally:
            if saved_key:
                os.environ["ANTHROPIC_API_KEY"] = saved_key

    @pytest.mark.asyncio
    async def test_provider_status_with_registry(self):
        """Should use registry when available."""
        mock_registry_class = MagicMock()
        mock_registry = MagicMock()
        mock_registry.list_providers.return_value = ["anthropic", "openrouter"]
        mock_provider = MagicMock()
        mock_provider.available_models = ["claude-3-opus", "claude-3-sonnet"]
        mock_registry.get.return_value = mock_provider
        mock_registry.get_default_provider_name.return_value = "anthropic"
        mock_registry_class.return_value = mock_registry

        with patch("asp.providers.registry.ProviderRegistry", mock_registry_class):
            result = await _handle_provider_status({})

        data = json.loads(result[0].text)
        assert data["total_available"] == 2
        assert data["default"] == "anthropic"


class TestSessionContextHandler:
    """Tests for asp_session_context handler."""

    @pytest.fixture
    def temp_project(self):
        """Create a temporary project structure for testing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_path = Path(tmpdir)

            # Create Summary directory with test files
            summary_dir = project_path / "Summary"
            summary_dir.mkdir()

            # Create session summaries
            (summary_dir / "summary20251220.1.md").write_text(
                "# Session 2025-12-20 Session 1\n\nTest content for session 1."
            )
            (summary_dir / "summary20251220.2.md").write_text(
                "# Session 2025-12-20 Session 2\n\nTest content for session 2."
            )
            (summary_dir / "summary20251219.1.md").write_text(
                "# Session 2025-12-19 Session 1\n\nTest content for older session."
            )

            # Create weekly reflection
            (summary_dir / "weekly_reflection_20251220.md").write_text(
                "# Weekly Reflection\n\nWeekly summary content."
            )

            # Create design directory with ADRs
            design_dir = project_path / "design"
            design_dir.mkdir()

            (design_dir / "ADR_001_test.md").write_text(
                "# ADR 001: Test ADR\n\nStatus: Complete\n\nTest content."
            )
            (design_dir / "ADR_002_wip.md").write_text(
                "# ADR 002: Work in Progress\n\nStatus: In Progress\n\nWIP content."
            )

            # Create docs directory with knowledge base
            docs_dir = project_path / "docs"
            docs_dir.mkdir()
            (docs_dir / "KNOWLEDGE_BASE.md").write_text(
                "# Knowledge Base\n\nEvergreen patterns and learnings."
            )

            yield project_path

    @pytest.mark.asyncio
    async def test_session_context_minimal(self, temp_project):
        """Minimal depth should load only 1 session."""
        result = await _handle_session_context(
            {
                "depth": "minimal",
                "project_path": str(temp_project),
            }
        )

        data = json.loads(result[0].text)
        assert data["depth"] == "minimal"
        assert len(data["sessions"]) == 1
        assert data["knowledge_base"] is None  # Not loaded for minimal

    @pytest.mark.asyncio
    async def test_session_context_standard(self, temp_project):
        """Standard depth should load 3 sessions."""
        result = await _handle_session_context(
            {
                "depth": "standard",
                "project_path": str(temp_project),
            }
        )

        data = json.loads(result[0].text)
        assert data["depth"] == "standard"
        assert len(data["sessions"]) == 3
        assert data["weekly_reflection"] is not None
        assert "Weekly Reflection" in data["weekly_reflection"]["content"]

    @pytest.mark.asyncio
    async def test_session_context_full(self, temp_project):
        """Full depth should load knowledge base."""
        result = await _handle_session_context(
            {
                "depth": "full",
                "project_path": str(temp_project),
            }
        )

        data = json.loads(result[0].text)
        assert data["depth"] == "full"
        assert data["knowledge_base"] is not None
        assert "Evergreen patterns" in data["knowledge_base"]

    @pytest.mark.asyncio
    async def test_session_context_parses_adrs(self, temp_project):
        """Should parse ADR status correctly."""
        result = await _handle_session_context(
            {
                "depth": "standard",
                "project_path": str(temp_project),
            }
        )

        data = json.loads(result[0].text)
        assert len(data["adrs"]) == 2
        assert data["adrs"]["ADR_001_test.md"]["status"] == "complete"
        assert data["adrs"]["ADR_002_wip.md"]["status"] == "in_progress"

    @pytest.mark.asyncio
    async def test_session_context_handles_missing_dirs(self):
        """Should handle missing directories gracefully."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = await _handle_session_context(
                {
                    "depth": "standard",
                    "project_path": tmpdir,
                }
            )

            data = json.loads(result[0].text)
            assert data["sessions"] == []
            assert data["weekly_reflection"] is None
            assert data["adrs"] == {}

    @pytest.mark.asyncio
    async def test_session_context_includes_timestamp(self, temp_project):
        """Should include ISO timestamp."""
        result = await _handle_session_context(
            {
                "project_path": str(temp_project),
            }
        )

        data = json.loads(result[0].text)
        assert "timestamp" in data
        # Verify it's a valid ISO timestamp
        datetime.fromisoformat(data["timestamp"].replace("Z", "+00:00"))


class TestRepairIssueHandler:
    """Tests for asp_repair_issue handler."""

    @pytest.mark.asyncio
    async def test_repair_issue_returns_cli_suggestion(self):
        """Should return CLI suggestion since orchestrator requires complex setup."""
        from asp.mcp.server import _handle_repair_issue

        result = await _handle_repair_issue(
            {"issue_url": "https://github.com/test/repo/issues/1"}
        )

        data = json.loads(result[0].text)
        assert data["status"] == "not_yet_implemented"
        assert "cli_command" in data
        assert "uv run asp repair-issue" in data["cli_command"]

    @pytest.mark.asyncio
    async def test_repair_issue_includes_dry_run_flag(self):
        """Should include dry-run flag in CLI suggestion when specified."""
        from asp.mcp.server import _handle_repair_issue

        result = await _handle_repair_issue(
            {"issue_url": "https://github.com/test/repo/issues/1", "dry_run": True}
        )

        data = json.loads(result[0].text)
        assert "--dry-run" in data["cli_command"]


class TestBeadsSyncHandler:
    """Tests for asp_beads_sync handler."""

    @pytest.mark.asyncio
    async def test_beads_sync_import_error(self):
        """Should handle missing dependencies gracefully."""
        from asp.mcp.server import _handle_beads_sync

        # Simulate import error by removing the module from sys.modules
        with patch.dict("sys.modules", {"asp.beads.github_sync": None}):
            result = await _handle_beads_sync({"direction": "push"})

        data = json.loads(result[0].text)
        assert data["error"] is True
        assert "Required module not available" in data["message"]


class TestSlashCommands:
    """Tests for slash command markdown files."""

    @pytest.fixture
    def commands_dir(self):
        """Return path to commands directory."""
        return Path(__file__).parent.parent.parent.parent / ".claude" / "commands"

    def test_session_summary_command_exists(self, commands_dir):
        """Session summary command file should exist."""
        cmd_file = commands_dir / "session-summary.md"
        assert cmd_file.exists(), f"Command file not found: {cmd_file}"

    def test_adr_status_command_exists(self, commands_dir):
        """ADR status command file should exist."""
        cmd_file = commands_dir / "adr-status.md"
        assert cmd_file.exists(), f"Command file not found: {cmd_file}"

    def test_coverage_analysis_command_exists(self, commands_dir):
        """Coverage analysis command file should exist."""
        cmd_file = commands_dir / "coverage-analysis.md"
        assert cmd_file.exists(), f"Command file not found: {cmd_file}"

    def test_commands_have_instructions(self, commands_dir):
        """All command files should have ## Instructions section."""
        for cmd_file in commands_dir.glob("*.md"):
            content = cmd_file.read_text()
            assert "## Instructions" in content, (
                f"{cmd_file.name} missing ## Instructions"
            )

    def test_commands_have_titles(self, commands_dir):
        """All command files should start with a title."""
        for cmd_file in commands_dir.glob("*.md"):
            content = cmd_file.read_text()
            assert content.startswith("# "), f"{cmd_file.name} missing title"


class TestClaudeMdValidation:
    """Tests for Claude.md validation."""

    @pytest.fixture
    def claude_md_path(self):
        """Return path to Claude.md."""
        return Path(__file__).parent.parent.parent.parent / "Claude.md"

    def test_claude_md_exists(self, claude_md_path):
        """Claude.md should exist."""
        assert claude_md_path.exists()

    def test_claude_md_has_repository_overview(self, claude_md_path):
        """Claude.md should have Repository Overview section."""
        content = claude_md_path.read_text()
        assert "## Repository Overview" in content

    def test_claude_md_has_repository_structure(self, claude_md_path):
        """Claude.md should have Repository Structure section."""
        content = claude_md_path.read_text()
        assert "## Repository Structure" in content
        assert "src/asp/" in content

    def test_claude_md_has_mcp_section(self, claude_md_path):
        """Claude.md should have MCP Server section."""
        content = claude_md_path.read_text()
        assert "## MCP Server" in content
        assert "asp_plan" in content

    def test_claude_md_has_tiered_memory(self, claude_md_path):
        """Claude.md should have tiered memory protocol."""
        content = claude_md_path.read_text()
        assert "tiered memory" in content.lower()
        assert "KNOWLEDGE_BASE.md" in content

    def test_claude_md_has_telemetry_section(self, claude_md_path):
        """Claude.md should have Telemetry section."""
        content = claude_md_path.read_text()
        assert "## Telemetry" in content
        assert "Langfuse" in content
        assert "Logfire" in content

    def test_claude_md_has_running_tests(self, claude_md_path):
        """Claude.md should have Running Tests section."""
        content = claude_md_path.read_text()
        assert "### Running Tests" in content
        assert "uv run pytest" in content

    def test_claude_md_references_exist(self, claude_md_path):
        """Referenced files in Claude.md should exist."""
        content = claude_md_path.read_text()
        project_root = claude_md_path.parent

        # Check key referenced paths exist
        paths_to_check = [
            "docs/KNOWLEDGE_BASE.md",
            ".mcp.json",
            ".claude/settings.json",
        ]

        for path in paths_to_check:
            if path in content:
                full_path = project_root / path
                assert full_path.exists(), f"Referenced path does not exist: {path}"
