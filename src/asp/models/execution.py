"""
Pydantic models for code execution and test results.

This module defines models for the repair workflow's execution infrastructure,
including sandbox configuration, execution results, and parsed test results.

Models:
    - SandboxConfig: Configuration for sandboxed code execution
    - ExecutionResult: Raw result from subprocess execution
    - TestFailure: Individual test failure details
    - TestResult: Parsed test execution results

Part of ADR 006: Repair Workflow Architecture.

Author: ASP Development Team
Date: December 10, 2025
"""

from dataclasses import dataclass, field

from pydantic import BaseModel, Field, field_validator, model_validator

# =============================================================================
# Configuration
# =============================================================================


@dataclass
class SandboxConfig:
    """
    Configuration for sandboxed code execution.

    Controls resource limits and environment for subprocess execution.
    Used by SandboxExecutor to enforce safe execution boundaries.

    Attributes:
        timeout_seconds: Maximum execution time before kill (default 300s = 5min)
        memory_limit_mb: Maximum memory usage in MB (default 512MB)
        cpu_limit_cores: CPU core limit (default 1.0)
        network_enabled: Whether network access is allowed (default False)
        env_vars: Additional environment variables to set
    """

    timeout_seconds: int = 300
    memory_limit_mb: int = 512
    cpu_limit_cores: float = 1.0
    network_enabled: bool = False
    env_vars: dict[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate configuration values."""
        if self.timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be positive")
        if self.memory_limit_mb <= 0:
            raise ValueError("memory_limit_mb must be positive")
        if self.cpu_limit_cores <= 0:
            raise ValueError("cpu_limit_cores must be positive")


# =============================================================================
# Execution Results
# =============================================================================


class ExecutionResult(BaseModel):
    """
    Raw result from subprocess execution.

    Captures the complete output from running a command in the sandbox,
    including exit code, stdout, stderr, timing, and timeout status.

    Attributes:
        exit_code: Process exit code (0 = success, non-zero = failure)
        stdout: Standard output captured from process
        stderr: Standard error captured from process
        duration_ms: Execution time in milliseconds
        timed_out: Whether execution was terminated due to timeout
    """

    exit_code: int = Field(
        ...,
        description="Process exit code (0 = success)",
    )

    stdout: str = Field(
        default="",
        description="Standard output from process",
    )

    stderr: str = Field(
        default="",
        description="Standard error from process",
    )

    duration_ms: int = Field(
        ...,
        ge=0,
        description="Execution time in milliseconds",
    )

    timed_out: bool = Field(
        default=False,
        description="Whether execution timed out",
    )

    @model_validator(mode="after")
    def validate_timeout_state(self) -> "ExecutionResult":
        """If timed out, exit_code should indicate failure."""
        if self.timed_out and self.exit_code == 0:
            # Timed out processes should not have success exit code
            # This is a warning, not an error - some edge cases exist
            pass
        return self

    class Config:
        json_schema_extra = {
            "example": {
                "exit_code": 0,
                "stdout": "===== test session starts =====\n...\n5 passed in 1.23s",
                "stderr": "",
                "duration_ms": 1234,
                "timed_out": False,
            }
        }


# =============================================================================
# Test Result Models
# =============================================================================


class TestFailure(BaseModel):
    """
    Details of a single test failure.

    Captures all information needed to diagnose and fix a failing test,
    including location, error type, message, and full stack trace.

    Attributes:
        test_name: Name of the failing test function/method
        test_file: Path to the test file
        line_number: Line number where failure occurred (if available)
        error_type: Type of error (e.g., AssertionError, TypeError)
        error_message: Human-readable error message
        stack_trace: Full stack trace for debugging
    """

    test_name: str = Field(
        ...,
        min_length=1,
        description="Name of the failing test",
    )

    test_file: str = Field(
        ...,
        min_length=1,
        description="Path to the test file",
    )

    line_number: int | None = Field(
        default=None,
        ge=1,
        description="Line number where failure occurred",
    )

    error_type: str = Field(
        ...,
        min_length=1,
        description="Type of error (e.g., AssertionError)",
    )

    error_message: str = Field(
        ...,
        description="Human-readable error message",
    )

    stack_trace: str = Field(
        default="",
        description="Full stack trace for debugging",
    )

    @field_validator("test_name")
    @classmethod
    def validate_test_name(cls, v: str) -> str:
        """Ensure test name is trimmed."""
        return v.strip()

    @field_validator("test_file")
    @classmethod
    def validate_test_file(cls, v: str) -> str:
        """Ensure test file path is trimmed."""
        return v.strip()

    class Config:
        json_schema_extra = {
            "example": {
                "test_name": "test_add",
                "test_file": "tests/test_calculator.py",
                "line_number": 15,
                "error_type": "AssertionError",
                "error_message": "assert add(2, 3) == 5\nassert -1 == 5",
                "stack_trace": (
                    "tests/test_calculator.py:15: AssertionError\n"
                    "    assert add(2, 3) == 5\n"
                    "E   assert -1 == 5"
                ),
            }
        }


class TestResult(BaseModel):
    """
    Parsed test execution results.

    Contains structured information from running a test framework,
    including pass/fail counts, coverage, and detailed failure information.

    Supports fallback mode when parsing fails - raw_output contains
    the unparsed output for LLM analysis.

    Attributes:
        framework: Test framework used (pytest, unittest, jest, etc.)
        total_tests: Total number of tests executed
        passed: Number of passing tests
        failed: Number of failing tests
        skipped: Number of skipped tests
        errors: Number of tests with errors (setup/teardown failures)
        duration_seconds: Total test execution time
        coverage_percent: Test coverage percentage (if collected)
        failures: List of detailed failure information
        raw_output: Raw stdout+stderr when parsing fails
        parsing_failed: Whether structured parsing failed
    """

    framework: str = Field(
        ...,
        min_length=1,
        description="Test framework (pytest, unittest, jest, etc.)",
    )

    total_tests: int = Field(
        ...,
        ge=-1,  # -1 indicates unknown
        description="Total tests executed (-1 if unknown)",
    )

    passed: int = Field(
        ...,
        ge=-1,
        description="Passing tests (-1 if unknown)",
    )

    failed: int = Field(
        ...,
        ge=-1,
        description="Failing tests (-1 if unknown)",
    )

    skipped: int = Field(
        default=0,
        ge=0,
        description="Skipped tests",
    )

    errors: int = Field(
        default=0,
        ge=0,
        description="Tests with errors (setup/teardown failures)",
    )

    duration_seconds: float = Field(
        ...,
        ge=0,
        description="Total test execution time in seconds",
    )

    coverage_percent: float | None = Field(
        default=None,
        ge=0,
        le=100,
        description="Test coverage percentage (if collected)",
    )

    failures: list[TestFailure] = Field(
        default_factory=list,
        description="Detailed failure information",
    )

    raw_output: str | None = Field(
        default=None,
        description="Raw output when parsing fails (for LLM analysis)",
    )

    parsing_failed: bool = Field(
        default=False,
        description="Whether structured parsing failed",
    )

    @model_validator(mode="after")
    def validate_counts(self) -> "TestResult":
        """Validate test count consistency when known."""
        # Skip validation if any count is unknown (-1)
        if self.total_tests == -1 or self.passed == -1 or self.failed == -1:
            return self

        # When counts are known, they should be consistent
        expected_total = self.passed + self.failed + self.skipped + self.errors
        if self.total_tests != expected_total:
            # Allow some tolerance for edge cases
            pass
        return self

    @model_validator(mode="after")
    def validate_failures_match_count(self) -> "TestResult":
        """Validate failure details match failed count when known."""
        if self.failed > 0 and len(self.failures) == 0 and not self.parsing_failed:
            # Failures reported but no details - this is okay, details are optional
            pass
        return self

    @property
    def success(self) -> bool:
        """Check if all tests passed."""
        if self.parsing_failed:
            return False
        if self.failed == -1:
            return False  # Unknown state
        return self.failed == 0 and self.errors == 0

    @property
    def has_failures(self) -> bool:
        """Check if any tests failed."""
        if self.failed == -1:
            return True  # Assume failure when unknown
        return self.failed > 0 or self.errors > 0

    class Config:
        json_schema_extra = {
            "example": {
                "framework": "pytest",
                "total_tests": 10,
                "passed": 8,
                "failed": 2,
                "skipped": 0,
                "errors": 0,
                "duration_seconds": 2.5,
                "coverage_percent": 85.0,
                "failures": [
                    {
                        "test_name": "test_add",
                        "test_file": "tests/test_calculator.py",
                        "line_number": 15,
                        "error_type": "AssertionError",
                        "error_message": "assert -1 == 5",
                        "stack_trace": "...",
                    }
                ],
                "raw_output": None,
                "parsing_failed": False,
            }
        }


# =============================================================================
# Convenience Functions
# =============================================================================


def create_fallback_result(
    execution_result: ExecutionResult,
    framework: str,
) -> TestResult:
    """
    Create a TestResult from raw execution when parsing fails.

    This fallback ensures agents can still analyze failures even when
    structured parsing fails. The raw output is preserved for LLM analysis.

    Args:
        execution_result: Raw execution result from sandbox
        framework: Test framework that was used

    Returns:
        TestResult with parsing_failed=True and raw_output set
    """
    return TestResult(
        framework=framework,
        total_tests=-1,  # Unknown
        passed=-1,  # Unknown
        failed=-1 if execution_result.exit_code != 0 else 0,
        skipped=0,
        errors=1 if execution_result.exit_code != 0 else 0,
        duration_seconds=execution_result.duration_ms / 1000.0,
        coverage_percent=None,
        failures=(
            [
                TestFailure(
                    test_name="unknown",
                    test_file="unknown",
                    line_number=None,
                    error_type="raw_output",
                    error_message=f"Exit code: {execution_result.exit_code}",
                    stack_trace=(
                        f"STDOUT:\n{execution_result.stdout}\n\n"
                        f"STDERR:\n{execution_result.stderr}"
                    ),
                )
            ]
            if execution_result.exit_code != 0
            else []
        ),
        raw_output=f"{execution_result.stdout}\n{execution_result.stderr}",
        parsing_failed=True,
    )
