"""
Sandbox Executor for safe code execution.

Provides subprocess-based code execution with resource limits for safely
running untrusted code (tests, builds) in the repair workflow.

Classes:
    - SubprocessSandboxExecutor: Execute commands with resource limits

Part of ADR 006: Repair Workflow Architecture.

Author: ASP Development Team
Date: December 10, 2025
"""

# pylint: disable=logging-fstring-interpolation,subprocess-popen-preexec-fn,consider-using-with

from __future__ import annotations

import asyncio
import contextlib
import logging
import os
import signal
import subprocess
import time
from pathlib import Path
from typing import TYPE_CHECKING

from asp.models.execution import ExecutionResult, SandboxConfig

if TYPE_CHECKING:
    from services.workspace_manager import Workspace

logger = logging.getLogger(__name__)


class SandboxExecutionError(Exception):
    """Raised when sandbox execution fails."""


class SubprocessSandboxExecutor:
    """
    Execute commands in a sandboxed subprocess with resource limits.

    Uses subprocess.Popen with preexec_fn to set resource limits via
    resource.setrlimit(). This provides basic isolation without requiring
    Docker or other containerization.

    Limitations (vs Docker):
    - No filesystem isolation (code can access host filesystem)
    - No network isolation (relies on config.network_enabled being False)
    - Resource limits are advisory on some systems

    For production use with untrusted code, consider DockerSandboxExecutor.

    Example:
        >>> config = SandboxConfig(timeout_seconds=60, memory_limit_mb=256)
        >>> executor = SubprocessSandboxExecutor(config)
        >>> result = executor.execute(workspace, ["pytest", "-v"])
        >>> print(f"Exit code: {result.exit_code}")
    """

    def __init__(self, config: SandboxConfig | None = None):
        """
        Initialize sandbox executor with configuration.

        Args:
            config: Sandbox configuration (defaults to SandboxConfig())
        """
        self.config = config or SandboxConfig()
        logger.debug(
            f"SandboxExecutor initialized: timeout={self.config.timeout_seconds}s, "
            f"memory={self.config.memory_limit_mb}MB"
        )

    def execute(
        self,
        workspace: Workspace,
        command: list[str],
        working_dir: str | None = None,
        env_vars: dict[str, str] | None = None,
    ) -> ExecutionResult:
        """
        Execute command in sandboxed subprocess.

        Args:
            workspace: Workspace containing code to execute
            command: Command and arguments (e.g., ["pytest", "-v"])
            working_dir: Working directory relative to workspace (or absolute)
            env_vars: Additional environment variables

        Returns:
            ExecutionResult with stdout, stderr, exit code, timing

        Raises:
            SandboxExecutionError: If execution setup fails
        """
        # Determine working directory
        if working_dir:
            if os.path.isabs(working_dir):
                cwd = Path(working_dir)
            else:
                cwd = workspace.target_repo_path / working_dir
        else:
            cwd = workspace.target_repo_path

        if not cwd.exists():
            raise SandboxExecutionError(f"Working directory does not exist: {cwd}")

        # Build environment
        env = self._build_environment(workspace, env_vars)

        # Log execution
        logger.info(f"Executing in sandbox: {' '.join(command)}")
        logger.debug(f"Working directory: {cwd}")

        start_time = time.time()
        timed_out = False

        try:
            # Create subprocess with resource limits
            process = subprocess.Popen(
                command,
                cwd=str(cwd),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=env,
                preexec_fn=self._create_limit_function(),
                text=True,
            )

            try:
                stdout, stderr = process.communicate(
                    timeout=self.config.timeout_seconds
                )
                exit_code = process.returncode
            except subprocess.TimeoutExpired:
                logger.warning(
                    f"Process timed out after {self.config.timeout_seconds}s, killing"
                )
                timed_out = True
                self._kill_process_tree(process)
                # Use a short timeout for communicate after kill to avoid hanging
                try:
                    stdout, stderr = process.communicate(timeout=5)
                except subprocess.TimeoutExpired:
                    # Process didn't respond to kill, force terminate
                    process.kill()
                    stdout, stderr = "", ""
                exit_code = -9  # SIGKILL

        except FileNotFoundError as e:
            raise SandboxExecutionError(f"Command not found: {command[0]}") from e
        except PermissionError as e:
            raise SandboxExecutionError(
                f"Permission denied executing: {command[0]}"
            ) from e
        except OSError as e:
            raise SandboxExecutionError(f"OS error executing command: {e}") from e

        duration_ms = int((time.time() - start_time) * 1000)

        result = ExecutionResult(
            exit_code=exit_code,
            stdout=stdout or "",
            stderr=stderr or "",
            duration_ms=duration_ms,
            timed_out=timed_out,
        )

        logger.info(
            f"Execution complete: exit_code={exit_code}, "
            f"duration={duration_ms}ms, timed_out={timed_out}"
        )

        return result

    async def execute_async(
        self,
        workspace: Workspace,
        command: list[str],
        working_dir: str | None = None,
        env_vars: dict[str, str] | None = None,
    ) -> ExecutionResult:
        """
        Execute command asynchronously in sandboxed subprocess.

        Async version of execute() using asyncio.create_subprocess_exec.
        Part of ADR 008 Phase 3: Async Services.

        Args:
            workspace: Workspace containing code to execute
            command: Command and arguments (e.g., ["pytest", "-v"])
            working_dir: Working directory relative to workspace (or absolute)
            env_vars: Additional environment variables

        Returns:
            ExecutionResult with stdout, stderr, exit code, timing

        Raises:
            SandboxExecutionError: If execution setup fails
        """
        # Determine working directory
        if working_dir:
            if os.path.isabs(working_dir):
                cwd = Path(working_dir)
            else:
                cwd = workspace.target_repo_path / working_dir
        else:
            cwd = workspace.target_repo_path

        if not cwd.exists():
            raise SandboxExecutionError(f"Working directory does not exist: {cwd}")

        # Build environment
        env = self._build_environment(workspace, env_vars)

        # Log execution
        logger.info(f"Executing async in sandbox: {' '.join(command)}")
        logger.debug(f"Working directory: {cwd}")

        start_time = time.time()
        timed_out = False

        try:
            # Create async subprocess
            # Note: preexec_fn not supported with asyncio subprocess,
            # resource limits would need to be set via other means (cgroups, etc.)
            process = await asyncio.create_subprocess_exec(
                *command,
                cwd=str(cwd),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=env,
            )

            try:
                stdout_bytes, stderr_bytes = await asyncio.wait_for(
                    process.communicate(),
                    timeout=self.config.timeout_seconds,
                )
                stdout = stdout_bytes.decode() if stdout_bytes else ""
                stderr = stderr_bytes.decode() if stderr_bytes else ""
                exit_code = process.returncode or 0
            except TimeoutError:
                logger.warning(
                    f"Async process timed out after {self.config.timeout_seconds}s, killing"
                )
                timed_out = True
                process.kill()
                # Wait briefly for process to terminate
                with contextlib.suppress(TimeoutError):
                    await asyncio.wait_for(process.wait(), timeout=5.0)
                stdout, stderr = "", ""
                exit_code = -9  # SIGKILL

        except FileNotFoundError as e:
            raise SandboxExecutionError(f"Command not found: {command[0]}") from e
        except PermissionError as e:
            raise SandboxExecutionError(
                f"Permission denied executing: {command[0]}"
            ) from e
        except OSError as e:
            raise SandboxExecutionError(f"OS error executing command: {e}") from e

        duration_ms = int((time.time() - start_time) * 1000)

        result = ExecutionResult(
            exit_code=exit_code,
            stdout=stdout,
            stderr=stderr,
            duration_ms=duration_ms,
            timed_out=timed_out,
        )

        logger.info(
            f"Async execution complete: exit_code={exit_code}, "
            f"duration={duration_ms}ms, timed_out={timed_out}"
        )

        return result

    def _build_environment(
        self,
        workspace: Workspace,
        extra_vars: dict[str, str] | None = None,
    ) -> dict[str, str]:
        """
        Build environment variables for subprocess.

        Inherits from current environment but allows overrides via config
        and extra_vars parameter.

        Args:
            workspace: Workspace for context
            extra_vars: Additional environment variables

        Returns:
            Complete environment dictionary
        """
        env = os.environ.copy()

        # Add workspace paths
        env["ASP_WORKSPACE_PATH"] = str(workspace.path)
        env["ASP_TARGET_REPO_PATH"] = str(workspace.target_repo_path)

        # Add configured environment variables
        env.update(self.config.env_vars)

        # Add extra variables (highest priority)
        if extra_vars:
            env.update(extra_vars)

        # Disable network if configured (advisory - doesn't actually block)
        if not self.config.network_enabled:
            # Remove proxy settings to discourage network use
            for key in list(env.keys()):
                if key.lower() in ("http_proxy", "https_proxy", "no_proxy"):
                    del env[key]

        return env

    def _create_limit_function(self):
        """
        Create a function to set resource limits in child process.

        Called via preexec_fn before command execution.
        Uses resource.setrlimit() on Unix systems.

        Returns:
            Function to set limits, or None on unsupported platforms
        """
        try:
            import resource  # Unix only
        except ImportError:
            logger.warning("resource module not available, no limits will be set")
            return None

        memory_bytes = self.config.memory_limit_mb * 1024 * 1024
        cpu_seconds = self.config.timeout_seconds

        def set_limits():
            """Set resource limits for child process."""
            try:
                # Memory limit (virtual memory)
                resource.setrlimit(resource.RLIMIT_AS, (memory_bytes, memory_bytes))
            except (ValueError, OSError) as e:
                # Some systems don't support RLIMIT_AS
                logger.debug(f"Could not set memory limit: {e}")

            try:
                # CPU time limit
                resource.setrlimit(resource.RLIMIT_CPU, (cpu_seconds, cpu_seconds))
            except (ValueError, OSError) as e:
                logger.debug(f"Could not set CPU limit: {e}")

            try:
                # Limit number of processes (prevent fork bombs)
                resource.setrlimit(resource.RLIMIT_NPROC, (100, 100))
            except (ValueError, OSError) as e:
                logger.debug(f"Could not set process limit: {e}")

        return set_limits

    def _kill_process_tree(self, process: subprocess.Popen) -> None:
        """
        Kill a process and all its children.

        Args:
            process: Process to kill
        """
        # First try to kill just the process
        with contextlib.suppress(ProcessLookupError, OSError):
            process.kill()

        # Then try to kill the process group if possible
        try:
            pgid = os.getpgid(process.pid)
            if pgid != os.getpgid(0):  # Don't kill our own process group
                os.killpg(pgid, signal.SIGKILL)
        except (ProcessLookupError, PermissionError, OSError):
            # Process already dead or we can't kill the group
            pass

    def execute_simple(
        self,
        command: list[str],
        cwd: Path | str,
        env_vars: dict[str, str] | None = None,
    ) -> ExecutionResult:
        """
        Execute command without workspace context.

        Simplified interface for cases where a full Workspace isn't needed.

        Args:
            command: Command and arguments
            cwd: Working directory
            env_vars: Environment variables

        Returns:
            ExecutionResult
        """

        # Create a minimal workspace-like object
        class MinimalWorkspace:
            def __init__(self, path: Path):
                self.path = path
                self.target_repo_path = path

        workspace = MinimalWorkspace(Path(cwd))
        return self.execute(workspace, command, env_vars=env_vars)

    async def execute_simple_async(
        self,
        command: list[str],
        cwd: Path | str,
        env_vars: dict[str, str] | None = None,
    ) -> ExecutionResult:
        """
        Execute command asynchronously without workspace context.

        Async version of execute_simple() for cases where a full Workspace
        isn't needed. Part of ADR 008 Phase 3: Async Services.

        Args:
            command: Command and arguments
            cwd: Working directory
            env_vars: Environment variables

        Returns:
            ExecutionResult
        """

        # Create a minimal workspace-like object
        class MinimalWorkspace:
            def __init__(self, path: Path):
                self.path = path
                self.target_repo_path = path

        workspace = MinimalWorkspace(Path(cwd))
        return await self.execute_async(workspace, command, env_vars=env_vars)
