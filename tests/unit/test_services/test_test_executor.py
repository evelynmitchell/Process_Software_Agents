"""
Unit tests for TestExecutor and PytestResultParser.

Tests for test execution and pytest output parsing.
"""

# pylint: disable=too-many-public-methods

from pathlib import Path
from unittest.mock import MagicMock

import pytest

from asp.models.execution import ExecutionResult
from services.test_executor import PytestResultParser, TestExecutor


class MockWorkspace:
    """Mock workspace for testing."""

    def __init__(self, path: Path):
        self.path = path
        self.target_repo_path = path


class TestPytestResultParser:
    """Tests for PytestResultParser."""

    @pytest.fixture
    def parser(self):
        """Create a parser instance."""
        return PytestResultParser()

    def test_parse_all_passed(self, parser):
        """Test parsing output where all tests passed."""
        stdout = """
============================= test session starts ==============================
collected 5 items

tests/test_example.py::test_one PASSED
tests/test_example.py::test_two PASSED
tests/test_example.py::test_three PASSED
tests/test_example.py::test_four PASSED
tests/test_example.py::test_five PASSED

============================== 5 passed in 1.23s ===============================
"""
        result = parser.parse(stdout, "", 0, 1230)

        assert result.framework == "pytest"
        assert result.total_tests == 5
        assert result.passed == 5
        assert result.failed == 0
        assert result.skipped == 0
        assert result.success is True
        assert not result.parsing_failed

    def test_parse_with_failures(self, parser):
        """Test parsing output with test failures."""
        stdout = """
============================= test session starts ==============================
collected 3 items

tests/test_calc.py::test_add FAILED
tests/test_calc.py::test_subtract PASSED
tests/test_calc.py::test_multiply PASSED

=================================== FAILURES ===================================
__________________________________ test_add ____________________________________

    def test_add():
>       assert add(2, 3) == 5
E       assert -1 == 5

tests/test_calc.py:10: AssertionError
=========================== short test summary info ============================
FAILED tests/test_calc.py::test_add - assert -1 == 5
=========================== 1 failed, 2 passed in 0.50s ========================
"""
        result = parser.parse(stdout, "", 1, 500)

        assert result.total_tests == 3
        assert result.passed == 2
        assert result.failed == 1
        assert result.success is False
        assert len(result.failures) == 1

        failure = result.failures[0]
        assert failure.test_name == "test_add"
        assert failure.test_file == "tests/test_calc.py"
        assert failure.error_type == "AssertionError"

    def test_parse_with_skipped(self, parser):
        """Test parsing output with skipped tests."""
        stdout = """
============================= test session starts ==============================
collected 3 items

tests/test_example.py::test_one PASSED
tests/test_example.py::test_two SKIPPED
tests/test_example.py::test_three PASSED

========================= 2 passed, 1 skipped in 0.30s =========================
"""
        result = parser.parse(stdout, "", 0, 300)

        assert result.passed == 2
        assert result.skipped == 1
        assert result.failed == 0

    def test_parse_with_errors(self, parser):
        """Test parsing output with collection errors."""
        stdout = """
============================= test session starts ==============================
collected 2 items / 1 error

================================== ERRORS ======================================
________________ ERROR collecting tests/test_broken.py _________________________
ImportError: No module named 'missing_module'
=========================== short test summary info ============================
ERROR tests/test_broken.py
!!!!!!!!!!!!!!!!!!!!!!!!!!!! stopping after 1 errors !!!!!!!!!!!!!!!!!!!!!!!!!!!
=============================== 1 error in 0.10s ===============================
"""
        result = parser.parse(stdout, "", 1, 100)

        assert result.errors >= 1 or result.failed >= 1
        assert result.success is False

    def test_parse_with_coverage(self, parser):
        """Test parsing output with coverage report."""
        stdout = """
============================= test session starts ==============================
collected 5 items

tests/test_example.py .....                                              [100%]

---------- coverage: platform linux, python 3.11.0 ----------
Name                      Stmts   Miss  Cover
---------------------------------------------
src/calculator.py            20      2    90%
src/utils.py                 10      0   100%
---------------------------------------------
TOTAL                        30      2    93%

============================== 5 passed in 2.00s ===============================
"""
        result = parser.parse(stdout, "", 0, 2000)

        assert result.passed == 5
        assert result.coverage_percent == 93.0

    def test_parse_simple_summary(self, parser):
        """Test parsing simple summary format."""
        stdout = """
tests/test_example.py .....
5 passed in 1.50s
"""
        result = parser.parse(stdout, "", 0, 1500)

        assert result.passed == 5
        assert result.failed == 0

    def test_parse_multiple_failures(self, parser):
        """Test parsing output with multiple failures."""
        stdout = """
============================= test session starts ==============================
FAILED tests/test_a.py::test_one - AssertionError: assert 1 == 2
FAILED tests/test_b.py::test_two - ValueError: invalid value
=========================== 2 failed in 0.30s ==================================
"""
        result = parser.parse(stdout, "", 1, 300)

        assert result.failed == 2
        assert len(result.failures) == 2

    def test_parse_failure_with_line_number(self, parser):
        """Test extracting line number from failure."""
        stdout = """
=================================== FAILURES ===================================
__________________________________ test_add ____________________________________

    def test_add():
>       assert add(2, 3) == 5
E       AssertionError: assert -1 == 5

tests/test_calc.py:15: AssertionError
FAILED tests/test_calc.py::test_add - AssertionError
=========================== 1 failed in 0.10s ==================================
"""
        result = parser.parse(stdout, "", 1, 100)

        assert len(result.failures) == 1
        failure = result.failures[0]
        assert failure.line_number == 15

    def test_parse_empty_output_fallback(self, parser):
        """Test fallback when output is empty/unparseable."""
        result = parser.parse("", "", 1, 100)

        assert result.parsing_failed is True
        assert result.total_tests == -1
        assert result.success is False

    def test_parse_duration_extraction(self, parser):
        """Test duration extraction from summary."""
        stdout = "============================== 3 passed in 2.50s ==============================="
        result = parser.parse(stdout, "", 0, 2500)

        assert result.duration_seconds == 2.5


class TestTestExecutor:
    """Tests for TestExecutor."""

    @pytest.fixture
    def mock_sandbox(self):
        """Create a mock sandbox executor."""
        return MagicMock()

    @pytest.fixture
    def executor(self, mock_sandbox):
        """Create a test executor with mock sandbox."""
        return TestExecutor(mock_sandbox)

    @pytest.fixture
    def workspace(self, tmp_path):
        """Create a mock workspace."""
        return MockWorkspace(tmp_path)

    def test_run_tests_success(self, executor, mock_sandbox, workspace):
        """Test running tests successfully."""
        mock_sandbox.execute.return_value = ExecutionResult(
            exit_code=0,
            stdout="===== 5 passed in 1.00s =====",
            stderr="",
            duration_ms=1000,
            timed_out=False,
        )

        result = executor.run_tests(workspace)

        assert result.success is True
        assert result.passed == 5
        mock_sandbox.execute.assert_called_once()

    def test_run_tests_with_failures(self, executor, mock_sandbox, workspace):
        """Test running tests with failures."""
        mock_sandbox.execute.return_value = ExecutionResult(
            exit_code=1,
            stdout="FAILED test.py::test_one\n=== 1 failed, 2 passed in 0.50s ===",
            stderr="",
            duration_ms=500,
            timed_out=False,
        )

        result = executor.run_tests(workspace)

        assert result.success is False
        assert result.failed == 1
        assert result.passed == 2

    def test_run_tests_fallback_on_parse_error(self, executor, mock_sandbox, workspace):
        """Test fallback when parsing fails."""
        mock_sandbox.execute.return_value = ExecutionResult(
            exit_code=1,
            stdout="Unparseable garbage output",
            stderr="Some error",
            duration_ms=100,
            timed_out=False,
        )

        result = executor.run_tests(workspace)

        assert result.parsing_failed is True
        assert result.raw_output is not None
        assert result.success is False

    def test_run_tests_with_specific_framework(self, executor, mock_sandbox, workspace):
        """Test running tests with specific framework."""
        mock_sandbox.execute.return_value = ExecutionResult(
            exit_code=0,
            stdout="3 passed in 0.50s",
            stderr="",
            duration_ms=500,
        )

        executor.run_tests(workspace, framework="pytest")

        # Verify pytest command was used
        call_args = mock_sandbox.execute.call_args
        command = call_args[0][1]
        assert "pytest" in command

    def test_run_tests_with_specific_path(self, executor, mock_sandbox, workspace):
        """Test running tests with specific test path."""
        mock_sandbox.execute.return_value = ExecutionResult(
            exit_code=0,
            stdout="1 passed in 0.10s",
            stderr="",
            duration_ms=100,
        )

        executor.run_tests(workspace, test_path="tests/specific_test.py")

        call_args = mock_sandbox.execute.call_args
        command = call_args[0][1]
        assert "tests/specific_test.py" in command

    def test_run_tests_with_coverage(self, executor, mock_sandbox, workspace):
        """Test running tests with coverage enabled."""
        mock_sandbox.execute.return_value = ExecutionResult(
            exit_code=0,
            stdout="1 passed in 0.10s",
            stderr="",
            duration_ms=100,
        )

        executor.run_tests(workspace, coverage=True)

        call_args = mock_sandbox.execute.call_args
        command = call_args[0][1]
        assert "--cov" in " ".join(command)

    def test_run_tests_without_coverage(self, executor, mock_sandbox, workspace):
        """Test running tests without coverage."""
        mock_sandbox.execute.return_value = ExecutionResult(
            exit_code=0,
            stdout="1 passed in 0.10s",
            stderr="",
            duration_ms=100,
        )

        executor.run_tests(workspace, coverage=False)

        call_args = mock_sandbox.execute.call_args
        command = call_args[0][1]
        assert "--cov" not in " ".join(command)

    def test_detect_framework_pytest_ini(self, executor, workspace):
        """Test framework detection with pytest.ini."""
        (workspace.target_repo_path / "pytest.ini").write_text("[pytest]")

        framework = executor._detect_framework(workspace)
        assert framework == "pytest"

    def test_detect_framework_pyproject_toml(self, executor, workspace):
        """Test framework detection with pyproject.toml containing pytest."""
        (workspace.target_repo_path / "pyproject.toml").write_text(
            "[tool.pytest.ini_options]\nminversion = '6.0'"
        )

        framework = executor._detect_framework(workspace)
        assert framework == "pytest"

    def test_detect_framework_conftest(self, executor, workspace):
        """Test framework detection with conftest.py."""
        (workspace.target_repo_path / "conftest.py").write_text("# pytest config")

        framework = executor._detect_framework(workspace)
        assert framework == "pytest"

    def test_detect_framework_test_files(self, executor, workspace):
        """Test framework detection from test file patterns."""
        tests_dir = workspace.target_repo_path / "tests"
        tests_dir.mkdir()
        (tests_dir / "test_example.py").write_text("def test_one(): pass")

        framework = executor._detect_framework(workspace)
        assert framework == "pytest"

    def test_detect_framework_package_json_jest(self, executor, workspace):
        """Test framework detection for Jest."""
        (workspace.target_repo_path / "package.json").write_text(
            '{"devDependencies": {"jest": "^29.0.0"}}'
        )

        framework = executor._detect_framework(workspace)
        assert framework == "jest"

    def test_detect_framework_go_mod(self, executor, workspace):
        """Test framework detection for Go."""
        (workspace.target_repo_path / "go.mod").write_text("module example.com/test")

        framework = executor._detect_framework(workspace)
        assert framework == "go"

    def test_detect_framework_cargo_toml(self, executor, workspace):
        """Test framework detection for Rust."""
        (workspace.target_repo_path / "Cargo.toml").write_text(
            '[package]\nname = "test"'
        )

        framework = executor._detect_framework(workspace)
        assert framework == "cargo"

    def test_detect_framework_default(self, executor, workspace):
        """Test default framework detection."""
        # Empty workspace
        framework = executor._detect_framework(workspace)
        assert framework == "pytest"

    def test_build_command_pytest(self, executor):
        """Test building pytest command."""
        cmd = executor._build_command("pytest", None, True)

        assert "pytest" in cmd
        assert "-v" in cmd
        assert "--cov=." in cmd

    def test_build_command_pytest_no_coverage(self, executor):
        """Test building pytest command without coverage."""
        cmd = executor._build_command("pytest", None, False)

        assert "pytest" in cmd
        assert "--cov" not in " ".join(cmd)

    def test_build_command_pytest_with_path(self, executor):
        """Test building pytest command with specific path."""
        cmd = executor._build_command("pytest", "tests/test_specific.py", True)

        assert "tests/test_specific.py" in cmd

    def test_build_command_unittest(self, executor):
        """Test building unittest command."""
        cmd = executor._build_command("unittest", None, False)

        assert "python" in cmd
        assert "-m" in cmd
        assert "unittest" in cmd
        assert "discover" in cmd

    def test_build_command_jest(self, executor):
        """Test building jest command."""
        cmd = executor._build_command("jest", None, True)

        assert "jest" in cmd
        assert "--coverage" in cmd

    def test_build_command_go(self, executor):
        """Test building go test command."""
        cmd = executor._build_command("go", None, True)

        assert "go" in cmd
        assert "test" in cmd
        assert "-cover" in cmd

    def test_build_command_cargo(self, executor):
        """Test building cargo test command."""
        cmd = executor._build_command("cargo", None, False)

        assert "cargo" in cmd
        assert "test" in cmd


class TestTestExecutorIntegration:
    """Integration tests for TestExecutor."""

    @pytest.fixture
    def workspace(self, tmp_path):
        """Create a workspace with test files."""
        workspace = MockWorkspace(tmp_path)

        # Create a simple Python file to test
        (tmp_path / "calculator.py").write_text(
            """
def add(a, b):
    return a + b

def subtract(a, b):
    return a - b
"""
        )

        # Create test file
        (tmp_path / "test_calculator.py").write_text(
            """
from calculator import add, subtract

def test_add():
    assert add(2, 3) == 5

def test_subtract():
    assert subtract(5, 3) == 2
"""
        )

        return workspace

    @pytest.mark.slow
    def test_run_real_pytest(self, workspace):
        """Test running real pytest (requires pytest installed)."""
        from asp.models.execution import SandboxConfig
        from services.sandbox_executor import SubprocessSandboxExecutor

        sandbox = SubprocessSandboxExecutor(SandboxConfig(timeout_seconds=30))
        executor = TestExecutor(sandbox)

        result = executor.run_tests(workspace, coverage=False)

        assert result.total_tests == 2
        assert result.passed == 2
        assert result.failed == 0
        assert result.success is True


class TestAsyncTestExecutor:
    """
    Tests for async TestExecutor methods.

    Part of ADR 008 Phase 3: Async Services.
    """

    @pytest.fixture
    def mock_sandbox(self):
        """Create a mock sandbox executor with async support."""
        mock = MagicMock()
        # Configure async mock
        from unittest.mock import AsyncMock

        mock.execute_async = AsyncMock()
        return mock

    @pytest.fixture
    def executor(self, mock_sandbox):
        """Create a test executor with mock sandbox."""
        return TestExecutor(mock_sandbox)

    @pytest.fixture
    def workspace(self, tmp_path):
        """Create a mock workspace."""
        return MockWorkspace(tmp_path)

    @pytest.mark.asyncio
    async def test_run_tests_async_success(self, executor, mock_sandbox, workspace):
        """Test running tests asynchronously successfully."""
        mock_sandbox.execute_async.return_value = ExecutionResult(
            exit_code=0,
            stdout="===== 5 passed in 1.00s =====",
            stderr="",
            duration_ms=1000,
            timed_out=False,
        )

        result = await executor.run_tests_async(workspace)

        assert result.success is True
        assert result.passed == 5
        mock_sandbox.execute_async.assert_called_once()

    @pytest.mark.asyncio
    async def test_run_tests_async_with_failures(self, executor, mock_sandbox, workspace):
        """Test running async tests with failures."""
        mock_sandbox.execute_async.return_value = ExecutionResult(
            exit_code=1,
            stdout="FAILED test.py::test_one\n=== 1 failed, 2 passed in 0.50s ===",
            stderr="",
            duration_ms=500,
            timed_out=False,
        )

        result = await executor.run_tests_async(workspace)

        assert result.success is False
        assert result.failed == 1
        assert result.passed == 2

    @pytest.mark.asyncio
    async def test_run_tests_async_fallback_on_parse_error(
        self, executor, mock_sandbox, workspace
    ):
        """Test async fallback when parsing fails."""
        mock_sandbox.execute_async.return_value = ExecutionResult(
            exit_code=1,
            stdout="Unparseable garbage output",
            stderr="Some error",
            duration_ms=100,
            timed_out=False,
        )

        result = await executor.run_tests_async(workspace)

        assert result.parsing_failed is True
        assert result.raw_output is not None
        assert result.success is False

    @pytest.mark.asyncio
    async def test_run_tests_async_with_specific_framework(
        self, executor, mock_sandbox, workspace
    ):
        """Test running async tests with specific framework."""
        mock_sandbox.execute_async.return_value = ExecutionResult(
            exit_code=0,
            stdout="3 passed in 0.50s",
            stderr="",
            duration_ms=500,
        )

        await executor.run_tests_async(workspace, framework="pytest")

        # Verify pytest command was used
        call_args = mock_sandbox.execute_async.call_args
        command = call_args[0][1]
        assert "pytest" in command

    @pytest.mark.asyncio
    async def test_run_tests_async_with_specific_path(
        self, executor, mock_sandbox, workspace
    ):
        """Test running async tests with specific test path."""
        mock_sandbox.execute_async.return_value = ExecutionResult(
            exit_code=0,
            stdout="1 passed in 0.10s",
            stderr="",
            duration_ms=100,
        )

        await executor.run_tests_async(workspace, test_path="tests/specific_test.py")

        call_args = mock_sandbox.execute_async.call_args
        command = call_args[0][1]
        assert "tests/specific_test.py" in command

    @pytest.mark.asyncio
    async def test_run_tests_async_with_coverage(
        self, executor, mock_sandbox, workspace
    ):
        """Test running async tests with coverage enabled."""
        mock_sandbox.execute_async.return_value = ExecutionResult(
            exit_code=0,
            stdout="1 passed in 0.10s",
            stderr="",
            duration_ms=100,
        )

        await executor.run_tests_async(workspace, coverage=True)

        call_args = mock_sandbox.execute_async.call_args
        command = call_args[0][1]
        assert "--cov" in " ".join(command)


class TestAsyncTestExecutorIntegration:
    """Integration tests for async TestExecutor."""

    @pytest.fixture
    def workspace(self, tmp_path):
        """Create a workspace with test files."""
        workspace = MockWorkspace(tmp_path)

        # Create a simple Python file to test
        (tmp_path / "calculator.py").write_text(
            """
def add(a, b):
    return a + b

def subtract(a, b):
    return a - b
"""
        )

        # Create test file
        (tmp_path / "test_calculator.py").write_text(
            """
from calculator import add, subtract

def test_add():
    assert add(2, 3) == 5

def test_subtract():
    assert subtract(5, 3) == 2
"""
        )

        return workspace

    @pytest.mark.slow
    @pytest.mark.asyncio
    async def test_run_real_pytest_async(self, workspace):
        """Test running real pytest asynchronously (requires pytest installed)."""
        from asp.models.execution import SandboxConfig
        from services.sandbox_executor import SubprocessSandboxExecutor

        sandbox = SubprocessSandboxExecutor(SandboxConfig(timeout_seconds=30))
        executor = TestExecutor(sandbox)

        result = await executor.run_tests_async(workspace, coverage=False)

        assert result.total_tests == 2
        assert result.passed == 2
        assert result.failed == 0
        assert result.success is True
