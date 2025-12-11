"""
Unit tests for execution models.

Tests for SandboxConfig, ExecutionResult, TestFailure, and TestResult models.
"""

# pylint: disable=use-implicit-booleaness-not-comparison

import pytest

from asp.models.execution import (
    ExecutionResult,
    SandboxConfig,
    TestFailure,
    TestResult,
    create_fallback_result,
)


class TestSandboxConfig:
    """Tests for SandboxConfig dataclass."""

    def test_default_values(self):
        """Test default configuration values."""
        config = SandboxConfig()
        assert config.timeout_seconds == 300
        assert config.memory_limit_mb == 512
        assert config.cpu_limit_cores == 1.0
        assert config.network_enabled is False
        assert config.env_vars == {}

    def test_custom_values(self):
        """Test custom configuration values."""
        config = SandboxConfig(
            timeout_seconds=60,
            memory_limit_mb=256,
            cpu_limit_cores=0.5,
            network_enabled=True,
            env_vars={"FOO": "bar"},
        )
        assert config.timeout_seconds == 60
        assert config.memory_limit_mb == 256
        assert config.cpu_limit_cores == 0.5
        assert config.network_enabled is True
        assert config.env_vars == {"FOO": "bar"}

    def test_invalid_timeout(self):
        """Test validation rejects invalid timeout."""
        with pytest.raises(ValueError, match="timeout_seconds must be positive"):
            SandboxConfig(timeout_seconds=0)

        with pytest.raises(ValueError, match="timeout_seconds must be positive"):
            SandboxConfig(timeout_seconds=-1)

    def test_invalid_memory(self):
        """Test validation rejects invalid memory limit."""
        with pytest.raises(ValueError, match="memory_limit_mb must be positive"):
            SandboxConfig(memory_limit_mb=0)

    def test_invalid_cpu(self):
        """Test validation rejects invalid CPU limit."""
        with pytest.raises(ValueError, match="cpu_limit_cores must be positive"):
            SandboxConfig(cpu_limit_cores=0)


class TestExecutionResult:
    """Tests for ExecutionResult model."""

    def test_successful_execution(self):
        """Test creating a successful execution result."""
        result = ExecutionResult(
            exit_code=0,
            stdout="test output",
            stderr="",
            duration_ms=1000,
            timed_out=False,
        )
        assert result.exit_code == 0
        assert result.stdout == "test output"
        assert result.stderr == ""
        assert result.duration_ms == 1000
        assert result.timed_out is False

    def test_failed_execution(self):
        """Test creating a failed execution result."""
        result = ExecutionResult(
            exit_code=1,
            stdout="",
            stderr="error message",
            duration_ms=500,
            timed_out=False,
        )
        assert result.exit_code == 1
        assert result.stderr == "error message"

    def test_timed_out_execution(self):
        """Test creating a timed out execution result."""
        result = ExecutionResult(
            exit_code=-9,
            stdout="partial output",
            stderr="",
            duration_ms=60000,
            timed_out=True,
        )
        assert result.exit_code == -9
        assert result.timed_out is True

    def test_default_values(self):
        """Test default values for optional fields."""
        result = ExecutionResult(
            exit_code=0,
            duration_ms=100,
        )
        assert result.stdout == ""
        assert result.stderr == ""
        assert result.timed_out is False

    def test_invalid_duration(self):
        """Test validation rejects negative duration."""
        with pytest.raises(ValueError):
            ExecutionResult(
                exit_code=0,
                duration_ms=-1,
            )


class TestTestFailure:
    """Tests for TestFailure model."""

    def test_complete_failure(self):
        """Test creating a complete test failure."""
        failure = TestFailure(
            test_name="test_add",
            test_file="tests/test_calculator.py",
            line_number=15,
            error_type="AssertionError",
            error_message="assert 5 == -1",
            stack_trace="full traceback here",
        )
        assert failure.test_name == "test_add"
        assert failure.test_file == "tests/test_calculator.py"
        assert failure.line_number == 15
        assert failure.error_type == "AssertionError"

    def test_minimal_failure(self):
        """Test creating a minimal test failure."""
        failure = TestFailure(
            test_name="test_something",
            test_file="test.py",
            error_type="Error",
            error_message="failed",
        )
        assert failure.line_number is None
        assert failure.stack_trace == ""

    def test_whitespace_trimming(self):
        """Test that test name and file are trimmed."""
        failure = TestFailure(
            test_name="  test_add  ",
            test_file="  test.py  ",
            error_type="Error",
            error_message="msg",
        )
        assert failure.test_name == "test_add"
        assert failure.test_file == "test.py"

    def test_empty_test_name_rejected(self):
        """Test that empty test name is rejected."""
        with pytest.raises(ValueError):
            TestFailure(
                test_name="",
                test_file="test.py",
                error_type="Error",
                error_message="msg",
            )

    def test_invalid_line_number(self):
        """Test that line number must be positive."""
        with pytest.raises(ValueError):
            TestFailure(
                test_name="test",
                test_file="test.py",
                line_number=0,
                error_type="Error",
                error_message="msg",
            )


class TestTestResult:
    """Tests for TestResult model."""

    def test_successful_test_run(self):
        """Test creating a successful test run result."""
        result = TestResult(
            framework="pytest",
            total_tests=10,
            passed=10,
            failed=0,
            skipped=0,
            errors=0,
            duration_seconds=2.5,
            coverage_percent=85.0,
        )
        assert result.success is True
        assert result.has_failures is False
        assert result.total_tests == 10
        assert result.passed == 10

    def test_failed_test_run(self):
        """Test creating a failed test run result."""
        failure = TestFailure(
            test_name="test_add",
            test_file="test.py",
            error_type="AssertionError",
            error_message="failed",
        )
        result = TestResult(
            framework="pytest",
            total_tests=10,
            passed=8,
            failed=2,
            duration_seconds=2.0,
            failures=[failure],
        )
        assert result.success is False
        assert result.has_failures is True
        assert result.failed == 2
        assert len(result.failures) == 1

    def test_unknown_counts(self):
        """Test handling unknown test counts."""
        result = TestResult(
            framework="pytest",
            total_tests=-1,
            passed=-1,
            failed=-1,
            duration_seconds=1.0,
            parsing_failed=True,
        )
        assert result.success is False
        assert result.has_failures is True
        assert result.parsing_failed is True

    def test_with_errors(self):
        """Test result with setup/teardown errors."""
        result = TestResult(
            framework="pytest",
            total_tests=5,
            passed=4,
            failed=0,
            errors=1,
            duration_seconds=1.0,
        )
        assert result.success is False
        assert result.has_failures is True

    def test_with_raw_output(self):
        """Test result with raw output fallback."""
        result = TestResult(
            framework="pytest",
            total_tests=-1,
            passed=-1,
            failed=-1,
            duration_seconds=1.0,
            raw_output="FAILED test output here",
            parsing_failed=True,
        )
        assert result.raw_output is not None
        assert result.parsing_failed is True

    def test_coverage_bounds(self):
        """Test coverage percentage validation."""
        # Valid coverage
        result = TestResult(
            framework="pytest",
            total_tests=1,
            passed=1,
            failed=0,
            duration_seconds=1.0,
            coverage_percent=100.0,
        )
        assert result.coverage_percent == 100.0

        # Invalid coverage - too high
        with pytest.raises(ValueError):
            TestResult(
                framework="pytest",
                total_tests=1,
                passed=1,
                failed=0,
                duration_seconds=1.0,
                coverage_percent=101.0,
            )


class TestCreateFallbackResult:
    """Tests for create_fallback_result helper function."""

    def test_fallback_from_success(self):
        """Test fallback from successful execution."""
        exec_result = ExecutionResult(
            exit_code=0,
            stdout="All tests passed",
            stderr="",
            duration_ms=1000,
        )
        result = create_fallback_result(exec_result, "pytest")

        assert result.framework == "pytest"
        assert result.parsing_failed is True
        assert result.raw_output is not None
        assert "All tests passed" in result.raw_output
        assert result.failed == 0
        assert len(result.failures) == 0

    def test_fallback_from_failure(self):
        """Test fallback from failed execution."""
        exec_result = ExecutionResult(
            exit_code=1,
            stdout="FAILED test_something",
            stderr="Error details",
            duration_ms=2000,
        )
        result = create_fallback_result(exec_result, "pytest")

        assert result.framework == "pytest"
        assert result.parsing_failed is True
        assert result.errors == 1
        assert len(result.failures) == 1
        assert result.failures[0].error_type == "raw_output"
        assert "Exit code: 1" in result.failures[0].error_message

    def test_fallback_duration_conversion(self):
        """Test duration is correctly converted from ms to seconds."""
        exec_result = ExecutionResult(
            exit_code=0,
            stdout="",
            stderr="",
            duration_ms=2500,
        )
        result = create_fallback_result(exec_result, "jest")

        assert result.duration_seconds == 2.5
