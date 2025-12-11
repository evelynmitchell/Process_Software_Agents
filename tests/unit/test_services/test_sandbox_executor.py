"""
Unit tests for SandboxExecutor.

Tests for SubprocessSandboxExecutor functionality including
command execution, timeouts, and resource limits.
"""

from pathlib import Path
from unittest.mock import patch

import pytest

from asp.models.execution import SandboxConfig
from services.sandbox_executor import SandboxExecutionError, SubprocessSandboxExecutor


class MockWorkspace:
    """Mock workspace for testing."""

    def __init__(self, path: Path):
        self.path = path
        self.target_repo_path = path


class TestSubprocessSandboxExecutor:
    """Tests for SubprocessSandboxExecutor."""

    @pytest.fixture
    def executor(self):
        """Create executor with default config."""
        return SubprocessSandboxExecutor()

    @pytest.fixture
    def workspace(self, tmp_path):
        """Create a mock workspace."""
        return MockWorkspace(tmp_path)

    def test_init_default_config(self):
        """Test initialization with default config."""
        executor = SubprocessSandboxExecutor()
        assert executor.config.timeout_seconds == 300
        assert executor.config.memory_limit_mb == 512

    def test_init_custom_config(self):
        """Test initialization with custom config."""
        config = SandboxConfig(timeout_seconds=60, memory_limit_mb=256)
        executor = SubprocessSandboxExecutor(config)
        assert executor.config.timeout_seconds == 60
        assert executor.config.memory_limit_mb == 256

    def test_execute_simple_command(self, executor, workspace):
        """Test executing a simple command."""
        result = executor.execute(workspace, ["echo", "hello"])
        assert result.exit_code == 0
        assert "hello" in result.stdout
        assert result.timed_out is False

    def test_execute_with_exit_code(self, executor, workspace):
        """Test executing a command that fails."""
        result = executor.execute(workspace, ["sh", "-c", "exit 42"])
        assert result.exit_code == 42
        assert result.timed_out is False

    def test_execute_captures_stderr(self, executor, workspace):
        """Test that stderr is captured."""
        result = executor.execute(
            workspace,
            ["sh", "-c", "echo error >&2"],
        )
        assert "error" in result.stderr

    def test_execute_captures_stdout(self, executor, workspace):
        """Test that stdout is captured."""
        result = executor.execute(
            workspace,
            ["sh", "-c", "echo output"],
        )
        assert "output" in result.stdout

    def test_execute_nonexistent_command(self, executor, workspace):
        """Test executing a command that doesn't exist."""
        with pytest.raises(SandboxExecutionError, match="Command not found"):
            executor.execute(workspace, ["nonexistent_command_12345"])

    def test_execute_nonexistent_directory(self, executor, workspace):
        """Test executing in a directory that doesn't exist."""
        with pytest.raises(SandboxExecutionError, match="does not exist"):
            executor.execute(workspace, ["echo", "hi"], working_dir="/nonexistent/path")

    def test_execute_with_working_dir_relative(self, executor, workspace):
        """Test executing with relative working directory."""
        # Create subdirectory
        subdir = workspace.target_repo_path / "subdir"
        subdir.mkdir()

        result = executor.execute(workspace, ["pwd"], working_dir="subdir")
        assert result.exit_code == 0
        assert "subdir" in result.stdout

    def test_execute_with_working_dir_absolute(self, executor, tmp_path):
        """Test executing with absolute working directory."""
        workspace = MockWorkspace(tmp_path)
        other_dir = tmp_path / "other"
        other_dir.mkdir()

        result = executor.execute(
            workspace,
            ["pwd"],
            working_dir=str(other_dir),
        )
        assert result.exit_code == 0
        assert "other" in result.stdout

    def test_execute_with_env_vars(self, executor, workspace):
        """Test executing with extra environment variables."""
        result = executor.execute(
            workspace,
            ["sh", "-c", "echo $MY_VAR"],
            env_vars={"MY_VAR": "test_value"},
        )
        assert "test_value" in result.stdout

    def test_execute_duration_recorded(self, executor, workspace):
        """Test that execution duration is recorded."""
        result = executor.execute(workspace, ["sleep", "0.1"])
        assert result.duration_ms >= 100

    def test_execute_timeout(self, workspace):
        """Test that timeout kills the process."""
        config = SandboxConfig(timeout_seconds=1)
        executor = SubprocessSandboxExecutor(config)

        result = executor.execute(workspace, ["sleep", "10"])
        assert result.timed_out is True
        assert result.exit_code == -9  # SIGKILL

    def test_build_environment_includes_workspace_paths(self, executor, workspace):
        """Test that workspace paths are in environment."""
        result = executor.execute(
            workspace,
            ["sh", "-c", "echo $ASP_WORKSPACE_PATH"],
        )
        assert str(workspace.path) in result.stdout

    def test_build_environment_includes_config_vars(self, workspace):
        """Test that config env vars are included."""
        config = SandboxConfig(env_vars={"CUSTOM_VAR": "custom_value"})
        executor = SubprocessSandboxExecutor(config)

        result = executor.execute(
            workspace,
            ["sh", "-c", "echo $CUSTOM_VAR"],
        )
        assert "custom_value" in result.stdout

    def test_execute_simple_interface(self, executor, tmp_path):
        """Test the execute_simple interface."""
        result = executor.execute_simple(["echo", "hello"], tmp_path)
        assert result.exit_code == 0
        assert "hello" in result.stdout

    def test_create_limit_function_returns_callable(self, executor):
        """Test that limit function is created correctly."""
        limit_fn = executor._create_limit_function()
        # On Unix systems, should return a callable
        # On Windows, should return None
        if limit_fn is not None:
            assert callable(limit_fn)

    @patch("services.sandbox_executor.subprocess.Popen")
    def test_permission_error_handling(self, mock_popen, executor, workspace):
        """Test handling of permission errors."""
        mock_popen.side_effect = PermissionError("Permission denied")

        with pytest.raises(SandboxExecutionError, match="Permission denied"):
            executor.execute(workspace, ["restricted_command"])


class TestSandboxExecutorIntegration:
    """Integration tests for SandboxExecutor with real processes."""

    @pytest.fixture
    def executor(self):
        """Create executor with short timeout for tests."""
        config = SandboxConfig(timeout_seconds=30)
        return SubprocessSandboxExecutor(config)

    @pytest.fixture
    def workspace(self, tmp_path):
        """Create a workspace with a simple Python file."""
        workspace = MockWorkspace(tmp_path)

        # Create a simple Python script
        script = tmp_path / "test_script.py"
        script.write_text("print('hello from python')")

        return workspace

    def test_run_python_script(self, executor, workspace):
        """Test running a Python script."""
        result = executor.execute(workspace, ["python", "test_script.py"])
        assert result.exit_code == 0
        assert "hello from python" in result.stdout

    def test_run_python_with_error(self, executor, workspace):
        """Test running a Python script that raises an error."""
        error_script = workspace.target_repo_path / "error_script.py"
        error_script.write_text("raise ValueError('test error')")

        result = executor.execute(workspace, ["python", "error_script.py"])
        assert result.exit_code != 0
        assert "ValueError" in result.stderr or "ValueError" in result.stdout
