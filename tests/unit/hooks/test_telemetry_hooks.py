"""
Tests for asp.hooks.telemetry module.

Tests the Claude Code telemetry hooks for tool use tracking.
"""

import json
import os
import tempfile
from pathlib import Path
from unittest import mock

import pytest

from asp.hooks.telemetry import (
    MAX_INPUT_LENGTH,
    MAX_RESPONSE_PREVIEW,
    SENSITIVE_KEYS,
    categorize_tool,
    get_log_dir,
    get_telemetry_provider,
    handle_post_tool_use,
    handle_pre_tool_use,
    is_telemetry_enabled,
    sanitize_value,
    write_local_log,
)


class TestGetLogDir:
    """Tests for get_log_dir function."""

    def test_default_log_dir(self):
        """Test default log directory is ~/.claude/telemetry."""
        with mock.patch.dict(os.environ, {}, clear=True):
            # Remove ASP_TELEMETRY_LOG_DIR if set
            os.environ.pop("ASP_TELEMETRY_LOG_DIR", None)
            log_dir = get_log_dir()
            assert log_dir == Path.home() / ".claude" / "telemetry"

    def test_custom_log_dir(self):
        """Test custom log directory from environment."""
        with mock.patch.dict(os.environ, {"ASP_TELEMETRY_LOG_DIR": "/tmp/my-logs"}):
            log_dir = get_log_dir()
            assert log_dir == Path("/tmp/my-logs")

    def test_log_dir_expands_user(self):
        """Test that ~ is expanded in log directory path."""
        with mock.patch.dict(
            os.environ, {"ASP_TELEMETRY_LOG_DIR": "~/custom-telemetry"}
        ):
            log_dir = get_log_dir()
            assert str(log_dir).startswith(str(Path.home()))
            assert "custom-telemetry" in str(log_dir)


class TestIsTelemetryEnabled:
    """Tests for is_telemetry_enabled function."""

    def test_default_enabled(self):
        """Test telemetry is enabled by default."""
        with mock.patch.dict(os.environ, {}, clear=True):
            os.environ.pop("ASP_TELEMETRY_ENABLED", None)
            assert is_telemetry_enabled() is True

    def test_explicitly_enabled(self):
        """Test telemetry explicitly enabled."""
        with mock.patch.dict(os.environ, {"ASP_TELEMETRY_ENABLED": "true"}):
            assert is_telemetry_enabled() is True

    def test_explicitly_disabled(self):
        """Test telemetry explicitly disabled."""
        with mock.patch.dict(os.environ, {"ASP_TELEMETRY_ENABLED": "false"}):
            assert is_telemetry_enabled() is False

    def test_enabled_check_is_case_insensitive(self):
        """Test that enabled check is case insensitive."""
        with mock.patch.dict(os.environ, {"ASP_TELEMETRY_ENABLED": "TRUE"}):
            assert is_telemetry_enabled() is True

        with mock.patch.dict(os.environ, {"ASP_TELEMETRY_ENABLED": "False"}):
            assert is_telemetry_enabled() is False


class TestGetTelemetryProvider:
    """Tests for get_telemetry_provider function."""

    def test_default_provider(self):
        """Test default provider is langfuse."""
        with mock.patch.dict(os.environ, {}, clear=True):
            os.environ.pop("ASP_TELEMETRY_PROVIDER", None)
            assert get_telemetry_provider() == "langfuse"

    def test_logfire_provider(self):
        """Test logfire provider selection."""
        with mock.patch.dict(os.environ, {"ASP_TELEMETRY_PROVIDER": "logfire"}):
            assert get_telemetry_provider() == "logfire"

    def test_langfuse_provider(self):
        """Test langfuse provider selection."""
        with mock.patch.dict(os.environ, {"ASP_TELEMETRY_PROVIDER": "langfuse"}):
            assert get_telemetry_provider() == "langfuse"

    def test_none_provider(self):
        """Test none provider selection."""
        with mock.patch.dict(os.environ, {"ASP_TELEMETRY_PROVIDER": "none"}):
            assert get_telemetry_provider() == "none"

    def test_invalid_provider_defaults_to_langfuse(self):
        """Test invalid provider defaults to langfuse."""
        with mock.patch.dict(os.environ, {"ASP_TELEMETRY_PROVIDER": "invalid"}):
            assert get_telemetry_provider() == "langfuse"

    def test_provider_selection_is_case_insensitive(self):
        """Test provider selection is case insensitive."""
        with mock.patch.dict(os.environ, {"ASP_TELEMETRY_PROVIDER": "LOGFIRE"}):
            assert get_telemetry_provider() == "logfire"


class TestSanitizeValue:
    """Tests for sanitize_value function."""

    def test_sanitize_simple_string(self):
        """Test simple strings pass through."""
        assert sanitize_value("hello") == "hello"

    def test_sanitize_truncates_long_string(self):
        """Test long strings are truncated."""
        long_string = "x" * (MAX_INPUT_LENGTH + 1000)
        result = sanitize_value(long_string)
        assert len(result) < len(long_string)
        assert "[truncated" in result
        assert str(len(long_string)) in result

    def test_sanitize_redacts_password(self):
        """Test password values are redacted."""
        assert sanitize_value("secret123", key="password") == "[REDACTED]"
        assert sanitize_value("secret123", key="PASSWORD") == "[REDACTED]"
        assert sanitize_value("secret123", key="user_password") == "[REDACTED]"

    def test_sanitize_redacts_api_key(self):
        """Test API key values are redacted."""
        assert sanitize_value("sk-abc123", key="api_key") == "[REDACTED]"
        assert sanitize_value("sk-abc123", key="apikey") == "[REDACTED]"
        assert sanitize_value("sk-abc123", key="ANTHROPIC_API_KEY") == "[REDACTED]"

    def test_sanitize_redacts_token(self):
        """Test token values are redacted."""
        assert sanitize_value("token123", key="token") == "[REDACTED]"
        assert sanitize_value("token123", key="access_token") == "[REDACTED]"
        assert sanitize_value("token123", key="refresh_token") == "[REDACTED]"

    def test_sanitize_redacts_secret(self):
        """Test secret values are redacted."""
        assert sanitize_value("mysecret", key="secret") == "[REDACTED]"
        assert sanitize_value("mysecret", key="secret_key") == "[REDACTED]"

    def test_sanitize_dict(self):
        """Test dictionary sanitization."""
        data = {
            "username": "john",
            "password": "secret123",
            "api_key": "sk-abc",
            "data": "normal",
        }
        result = sanitize_value(data)
        assert result["username"] == "john"
        assert result["password"] == "[REDACTED]"
        assert result["api_key"] == "[REDACTED]"
        assert result["data"] == "normal"

    def test_sanitize_nested_dict(self):
        """Test nested dictionary sanitization."""
        data = {
            "config": {
                "token": "secret",
                "url": "https://example.com",
            }
        }
        result = sanitize_value(data)
        assert result["config"]["token"] == "[REDACTED]"
        assert result["config"]["url"] == "https://example.com"

    def test_sanitize_list(self):
        """Test list sanitization."""
        data = ["item1", "item2", "item3"]
        result = sanitize_value(data)
        assert result == ["item1", "item2", "item3"]

    def test_sanitize_list_truncates(self):
        """Test very long lists are truncated."""
        data = list(range(200))
        result = sanitize_value(data)
        assert len(result) == 100

    def test_sanitize_non_string_values(self):
        """Test non-string values pass through."""
        assert sanitize_value(123) == 123
        assert sanitize_value(3.14) == 3.14
        assert sanitize_value(True) is True
        assert sanitize_value(None) is None


class TestCategorizeTool:
    """Tests for categorize_tool function."""

    def test_mcp_tool(self):
        """Test MCP tool categorization."""
        result = categorize_tool("mcp__server__tool")
        assert result["tool_type"] == "mcp"
        assert result["mcp_server"] == "server"
        assert result["mcp_tool"] == "tool"

    def test_mcp_tool_with_underscores(self):
        """Test MCP tool with underscores in name."""
        result = categorize_tool("mcp__my_server__my_tool")
        assert result["tool_type"] == "mcp"
        assert result["mcp_server"] == "my_server"
        assert result["mcp_tool"] == "my_tool"

    def test_mcp_tool_short_name(self):
        """Test MCP tool with minimal parts."""
        result = categorize_tool("mcp__server")
        assert result["tool_type"] == "mcp"
        assert result["mcp_server"] == "server"

    def test_subagent_tool(self):
        """Test Task (subagent) tool categorization."""
        result = categorize_tool("Task")
        assert result["tool_type"] == "subagent"

    def test_builtin_tool(self):
        """Test builtin tool categorization."""
        result = categorize_tool("Read")
        assert result["tool_type"] == "builtin"

        result = categorize_tool("Bash")
        assert result["tool_type"] == "builtin"

        result = categorize_tool("Write")
        assert result["tool_type"] == "builtin"


class TestWriteLocalLog:
    """Tests for write_local_log function."""

    def test_write_log_creates_file(self):
        """Test log file is created."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with mock.patch.dict(os.environ, {"ASP_TELEMETRY_LOG_DIR": tmpdir}):
                event = {"tool": "Read", "timestamp": "2025-01-01T00:00:00"}
                write_local_log(event, "session123")

                log_file = Path(tmpdir) / "session1.jsonl"
                assert log_file.exists()

    def test_write_log_appends(self):
        """Test multiple logs append to same file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with mock.patch.dict(os.environ, {"ASP_TELEMETRY_LOG_DIR": tmpdir}):
                event1 = {"tool": "Read", "n": 1}
                event2 = {"tool": "Write", "n": 2}
                write_local_log(event1, "session123")
                write_local_log(event2, "session123")

                log_file = Path(tmpdir) / "session1.jsonl"
                lines = log_file.read_text().strip().split("\n")
                assert len(lines) == 2

    def test_write_log_jsonl_format(self):
        """Test log is valid JSONL format."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with mock.patch.dict(os.environ, {"ASP_TELEMETRY_LOG_DIR": tmpdir}):
                event = {"tool": "Read", "data": "test"}
                write_local_log(event, "session123")

                log_file = Path(tmpdir) / "session1.jsonl"
                content = log_file.read_text().strip()
                parsed = json.loads(content)
                assert parsed["tool"] == "Read"
                assert parsed["data"] == "test"

    def test_write_log_handles_unknown_session(self):
        """Test log handles empty session ID."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with mock.patch.dict(os.environ, {"ASP_TELEMETRY_LOG_DIR": tmpdir}):
                event = {"tool": "Read"}
                write_local_log(event, "")

                log_file = Path(tmpdir) / "unknown.jsonl"
                assert log_file.exists()


class TestHandlePreToolUse:
    """Tests for handle_pre_tool_use function."""

    def test_handle_pre_tool_use_logs_locally(self):
        """Test pre tool use writes local log."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with mock.patch.dict(
                os.environ,
                {
                    "ASP_TELEMETRY_LOG_DIR": tmpdir,
                    "ASP_TELEMETRY_PROVIDER": "none",
                },
            ):
                input_data = {
                    "tool_name": "Read",
                    "tool_use_id": "tu_123",
                    "session_id": "sess_abc",
                    "tool_input": {"file_path": "/test.txt"},
                }
                handle_pre_tool_use(input_data)

                log_file = Path(tmpdir) / "sess_abc.jsonl"
                assert log_file.exists()
                event = json.loads(log_file.read_text().strip())
                assert event["event"] == "tool_start"
                assert event["tool"] == "Read"
                assert event["tool_type"] == "builtin"

    def test_handle_pre_tool_use_sanitizes_input(self):
        """Test pre tool use sanitizes sensitive data."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with mock.patch.dict(
                os.environ,
                {
                    "ASP_TELEMETRY_LOG_DIR": tmpdir,
                    "ASP_TELEMETRY_PROVIDER": "none",
                },
            ):
                input_data = {
                    "tool_name": "Bash",
                    "tool_use_id": "tu_123",
                    "session_id": "sess_abc",
                    "tool_input": {"password": "secret123", "command": "ls"},
                }
                handle_pre_tool_use(input_data)

                log_file = Path(tmpdir) / "sess_abc.jsonl"
                event = json.loads(log_file.read_text().strip())
                assert event["input"]["password"] == "[REDACTED]"
                assert event["input"]["command"] == "ls"


class TestHandlePostToolUse:
    """Tests for handle_post_tool_use function."""

    def test_handle_post_tool_use_logs_locally(self):
        """Test post tool use writes local log."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with mock.patch.dict(
                os.environ,
                {
                    "ASP_TELEMETRY_LOG_DIR": tmpdir,
                    "ASP_TELEMETRY_PROVIDER": "none",
                },
            ):
                input_data = {
                    "tool_name": "Read",
                    "tool_use_id": "tu_123",
                    "session_id": "sess_abc",
                    "tool_response": {"content": "file contents"},
                }
                handle_post_tool_use(input_data)

                log_file = Path(tmpdir) / "sess_abc.jsonl"
                assert log_file.exists()
                event = json.loads(log_file.read_text().strip())
                assert event["event"] == "tool_end"
                assert event["success"] is True

    def test_handle_post_tool_use_detects_error(self):
        """Test post tool use detects error responses."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with mock.patch.dict(
                os.environ,
                {
                    "ASP_TELEMETRY_LOG_DIR": tmpdir,
                    "ASP_TELEMETRY_PROVIDER": "none",
                },
            ):
                input_data = {
                    "tool_name": "Bash",
                    "tool_use_id": "tu_123",
                    "session_id": "sess_abc",
                    "tool_response": {"is_error": True, "error": "Command failed"},
                }
                handle_post_tool_use(input_data)

                log_file = Path(tmpdir) / "sess_abc.jsonl"
                event = json.loads(log_file.read_text().strip())
                assert event["success"] is False

    def test_handle_post_tool_use_truncates_response(self):
        """Test post tool use truncates long responses."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with mock.patch.dict(
                os.environ,
                {
                    "ASP_TELEMETRY_LOG_DIR": tmpdir,
                    "ASP_TELEMETRY_PROVIDER": "none",
                },
            ):
                long_response = "x" * (MAX_RESPONSE_PREVIEW + 1000)
                input_data = {
                    "tool_name": "Read",
                    "tool_use_id": "tu_123",
                    "session_id": "sess_abc",
                    "tool_response": long_response,
                }
                handle_post_tool_use(input_data)

                log_file = Path(tmpdir) / "sess_abc.jsonl"
                event = json.loads(log_file.read_text().strip())
                assert "[truncated]" in event["response_preview"]
                assert len(event["response_preview"]) <= MAX_RESPONSE_PREVIEW + 20


class TestSensitiveKeys:
    """Tests for SENSITIVE_KEYS constant."""

    def test_sensitive_keys_contains_expected(self):
        """Test SENSITIVE_KEYS contains expected values."""
        assert "password" in SENSITIVE_KEYS
        assert "secret" in SENSITIVE_KEYS
        assert "token" in SENSITIVE_KEYS
        assert "api_key" in SENSITIVE_KEYS
        assert "private_key" in SENSITIVE_KEYS

    def test_sensitive_keys_is_frozenset(self):
        """Test SENSITIVE_KEYS is immutable."""
        assert isinstance(SENSITIVE_KEYS, frozenset)


class TestProviderDispatch:
    """Tests for provider dispatching in handle_pre/post_tool_use."""

    def test_pre_tool_use_calls_langfuse_provider(self):
        """Test pre tool use calls Langfuse when configured."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with mock.patch.dict(
                os.environ,
                {
                    "ASP_TELEMETRY_LOG_DIR": tmpdir,
                    "ASP_TELEMETRY_PROVIDER": "langfuse",
                    "LANGFUSE_PUBLIC_KEY": "pk-test",
                },
            ):
                with mock.patch(
                    "asp.hooks.telemetry.send_to_langfuse"
                ) as mock_langfuse:
                    input_data = {
                        "tool_name": "Read",
                        "tool_use_id": "tu_123",
                        "session_id": "sess_abc",
                        "tool_input": {},
                    }
                    handle_pre_tool_use(input_data)
                    mock_langfuse.assert_called_once()

    def test_pre_tool_use_calls_logfire_provider(self):
        """Test pre tool use calls Logfire when configured."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with mock.patch.dict(
                os.environ,
                {
                    "ASP_TELEMETRY_LOG_DIR": tmpdir,
                    "ASP_TELEMETRY_PROVIDER": "logfire",
                },
            ):
                with mock.patch("asp.hooks.telemetry.send_to_logfire") as mock_logfire:
                    input_data = {
                        "tool_name": "Read",
                        "tool_use_id": "tu_123",
                        "session_id": "sess_abc",
                        "tool_input": {},
                    }
                    handle_pre_tool_use(input_data)
                    mock_logfire.assert_called_once()

    def test_post_tool_use_calls_langfuse_provider(self):
        """Test post tool use calls Langfuse when configured."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with mock.patch.dict(
                os.environ,
                {
                    "ASP_TELEMETRY_LOG_DIR": tmpdir,
                    "ASP_TELEMETRY_PROVIDER": "langfuse",
                    "LANGFUSE_PUBLIC_KEY": "pk-test",
                },
            ):
                with mock.patch(
                    "asp.hooks.telemetry.send_to_langfuse"
                ) as mock_langfuse:
                    input_data = {
                        "tool_name": "Read",
                        "tool_use_id": "tu_123",
                        "session_id": "sess_abc",
                        "tool_response": {"content": "test"},
                    }
                    handle_post_tool_use(input_data)
                    mock_langfuse.assert_called_once()

    def test_post_tool_use_calls_logfire_provider(self):
        """Test post tool use calls Logfire when configured."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with mock.patch.dict(
                os.environ,
                {
                    "ASP_TELEMETRY_LOG_DIR": tmpdir,
                    "ASP_TELEMETRY_PROVIDER": "logfire",
                },
            ):
                with mock.patch("asp.hooks.telemetry.send_to_logfire") as mock_logfire:
                    input_data = {
                        "tool_name": "Read",
                        "tool_use_id": "tu_123",
                        "session_id": "sess_abc",
                        "tool_response": {"content": "test"},
                    }
                    handle_post_tool_use(input_data)
                    mock_logfire.assert_called_once()


class TestMain:
    """Tests for main function."""

    def test_main_exits_when_disabled(self):
        """Test main exits 0 when telemetry is disabled."""
        with mock.patch.dict(os.environ, {"ASP_TELEMETRY_ENABLED": "false"}):
            with pytest.raises(SystemExit) as exc_info:
                from asp.hooks.telemetry import main

                main()
            assert exc_info.value.code == 0

    def test_main_exits_without_args(self):
        """Test main exits 0 when no arguments provided."""
        with mock.patch.dict(os.environ, {"ASP_TELEMETRY_ENABLED": "true"}):
            import sys

            original_argv = sys.argv
            sys.argv = ["telemetry.py"]  # No phase argument
            try:
                with pytest.raises(SystemExit) as exc_info:
                    # Force reimport to pick up new argv
                    import importlib

                    from asp.hooks import telemetry

                    importlib.reload(telemetry)
                    telemetry.main()
                assert exc_info.value.code == 0
            finally:
                sys.argv = original_argv

    def test_main_handles_pre_phase(self):
        """Test main handles pre phase correctly."""
        import io
        import sys

        with tempfile.TemporaryDirectory() as tmpdir:
            with mock.patch.dict(
                os.environ,
                {
                    "ASP_TELEMETRY_ENABLED": "true",
                    "ASP_TELEMETRY_LOG_DIR": tmpdir,
                    "ASP_TELEMETRY_PROVIDER": "none",
                },
            ):
                original_argv = sys.argv
                original_stdin = sys.stdin
                sys.argv = ["telemetry.py", "pre"]
                test_input = json.dumps(
                    {
                        "tool_name": "Read",
                        "tool_use_id": "tu_test",
                        "session_id": "sess_test",
                        "tool_input": {"file_path": "/test.txt"},
                    }
                )
                sys.stdin = io.StringIO(test_input)
                try:
                    with pytest.raises(SystemExit) as exc_info:
                        import importlib

                        from asp.hooks import telemetry

                        importlib.reload(telemetry)
                        telemetry.main()
                    assert exc_info.value.code == 0

                    # Verify log was written
                    log_file = Path(tmpdir) / "sess_tes.jsonl"
                    assert log_file.exists()
                finally:
                    sys.argv = original_argv
                    sys.stdin = original_stdin

    def test_main_handles_post_phase(self):
        """Test main handles post phase correctly."""
        import io
        import sys

        with tempfile.TemporaryDirectory() as tmpdir:
            with mock.patch.dict(
                os.environ,
                {
                    "ASP_TELEMETRY_ENABLED": "true",
                    "ASP_TELEMETRY_LOG_DIR": tmpdir,
                    "ASP_TELEMETRY_PROVIDER": "none",
                },
            ):
                original_argv = sys.argv
                original_stdin = sys.stdin
                sys.argv = ["telemetry.py", "post"]
                test_input = json.dumps(
                    {
                        "tool_name": "Read",
                        "tool_use_id": "tu_test",
                        "session_id": "sess_test",
                        "tool_response": {"content": "file contents"},
                    }
                )
                sys.stdin = io.StringIO(test_input)
                try:
                    with pytest.raises(SystemExit) as exc_info:
                        import importlib

                        from asp.hooks import telemetry

                        importlib.reload(telemetry)
                        telemetry.main()
                    assert exc_info.value.code == 0
                finally:
                    sys.argv = original_argv
                    sys.stdin = original_stdin

    def test_main_handles_invalid_json(self):
        """Test main exits 0 with invalid JSON input."""
        import io
        import sys

        with mock.patch.dict(os.environ, {"ASP_TELEMETRY_ENABLED": "true"}):
            original_argv = sys.argv
            original_stdin = sys.stdin
            sys.argv = ["telemetry.py", "pre"]
            sys.stdin = io.StringIO("not valid json")
            try:
                with pytest.raises(SystemExit) as exc_info:
                    import importlib

                    from asp.hooks import telemetry

                    importlib.reload(telemetry)
                    telemetry.main()
                assert exc_info.value.code == 0
            finally:
                sys.argv = original_argv
                sys.stdin = original_stdin


class TestSendToLangfuse:
    """Tests for send_to_langfuse function."""

    def test_send_to_langfuse_pre_event(self):
        """Test sending pre event to Langfuse."""
        import sys

        # Create mock langfuse module
        mock_langfuse_instance = mock.MagicMock()
        mock_langfuse_class = mock.MagicMock(return_value=mock_langfuse_instance)
        mock_langfuse_module = mock.MagicMock()
        mock_langfuse_module.Langfuse = mock_langfuse_class

        with mock.patch.dict(os.environ, {"LANGFUSE_PUBLIC_KEY": "pk-test"}):
            with mock.patch.dict(sys.modules, {"langfuse": mock_langfuse_module}):
                from asp.hooks.telemetry import send_to_langfuse

                event = {
                    "tool_use_id": "tu_123",
                    "session_id": "sess_abc",
                    "tool": "Read",
                    "tool_type": "builtin",
                }
                send_to_langfuse(event, "pre")

                mock_langfuse_instance.trace.assert_called_once()
                mock_langfuse_instance.flush.assert_called_once()

    def test_send_to_langfuse_post_event(self):
        """Test sending post event to Langfuse."""
        import sys

        mock_langfuse_instance = mock.MagicMock()
        mock_langfuse_class = mock.MagicMock(return_value=mock_langfuse_instance)
        mock_langfuse_module = mock.MagicMock()
        mock_langfuse_module.Langfuse = mock_langfuse_class

        with mock.patch.dict(os.environ, {"LANGFUSE_PUBLIC_KEY": "pk-test"}):
            with mock.patch.dict(sys.modules, {"langfuse": mock_langfuse_module}):
                from asp.hooks.telemetry import send_to_langfuse

                event = {
                    "tool_use_id": "tu_123",
                    "success": True,
                }
                send_to_langfuse(event, "post")

                mock_langfuse_instance.trace.assert_called_once()
                mock_langfuse_instance.flush.assert_called_once()

    def test_send_to_langfuse_no_key(self):
        """Test send_to_langfuse returns early without key."""
        import sys

        mock_langfuse_class = mock.MagicMock()
        mock_langfuse_module = mock.MagicMock()
        mock_langfuse_module.Langfuse = mock_langfuse_class

        with mock.patch.dict(os.environ, {}, clear=True):
            os.environ.pop("LANGFUSE_PUBLIC_KEY", None)
            with mock.patch.dict(sys.modules, {"langfuse": mock_langfuse_module}):
                from asp.hooks.telemetry import send_to_langfuse

                event = {"tool_use_id": "tu_123"}
                send_to_langfuse(event, "pre")

                mock_langfuse_class.assert_not_called()

    def test_send_to_langfuse_handles_exception(self):
        """Test send_to_langfuse handles exceptions gracefully."""
        import sys

        mock_langfuse_instance = mock.MagicMock()
        mock_langfuse_instance.trace.side_effect = Exception("API error")
        mock_langfuse_class = mock.MagicMock(return_value=mock_langfuse_instance)
        mock_langfuse_module = mock.MagicMock()
        mock_langfuse_module.Langfuse = mock_langfuse_class

        with mock.patch.dict(os.environ, {"LANGFUSE_PUBLIC_KEY": "pk-test"}):
            with mock.patch.dict(sys.modules, {"langfuse": mock_langfuse_module}):
                from asp.hooks.telemetry import send_to_langfuse

                # Should not raise
                event = {"tool_use_id": "tu_123"}
                send_to_langfuse(event, "pre")


class TestSendToLogfire:
    """Tests for send_to_logfire function."""

    def test_send_to_logfire_pre_event(self):
        """Test sending pre event to Logfire."""
        import sys

        mock_logfire = mock.MagicMock()
        with mock.patch.dict(sys.modules, {"logfire": mock_logfire}):
            from asp.hooks.telemetry import send_to_logfire

            event = {
                "tool": "Read",
                "tool_use_id": "tu_123",
                "session_id": "sess_abc",
                "tool_type": "builtin",
                "input": {"file_path": "/test.txt"},
            }
            send_to_logfire(event, "pre")

            mock_logfire.info.assert_called_once()

    def test_send_to_logfire_post_success(self):
        """Test sending successful post event to Logfire."""
        import sys

        mock_logfire = mock.MagicMock()
        with mock.patch.dict(sys.modules, {"logfire": mock_logfire}):
            from asp.hooks.telemetry import send_to_logfire

            event = {
                "tool": "Read",
                "tool_use_id": "tu_123",
                "session_id": "sess_abc",
                "success": True,
                "response_preview": "file contents",
            }
            send_to_logfire(event, "post")

            mock_logfire.info.assert_called_once()

    def test_send_to_logfire_post_failure(self):
        """Test sending failed post event to Logfire uses warn."""
        import sys

        mock_logfire = mock.MagicMock()
        with mock.patch.dict(sys.modules, {"logfire": mock_logfire}):
            from asp.hooks.telemetry import send_to_logfire

            event = {
                "tool": "Bash",
                "tool_use_id": "tu_123",
                "session_id": "sess_abc",
                "success": False,
                "response_preview": "command failed",
            }
            send_to_logfire(event, "post")

            mock_logfire.warn.assert_called_once()

    def test_send_to_logfire_handles_exception(self):
        """Test send_to_logfire handles exceptions gracefully."""
        import sys

        mock_logfire = mock.MagicMock()
        mock_logfire.info.side_effect = Exception("API error")

        with mock.patch.dict(sys.modules, {"logfire": mock_logfire}):
            from asp.hooks.telemetry import send_to_logfire

            # Should not raise
            event = {"tool": "Read"}
            send_to_logfire(event, "pre")
