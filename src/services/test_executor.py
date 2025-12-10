"""
Test Executor for running real test frameworks.

Provides test execution and result parsing for the repair workflow.
Supports pytest with fallback parsing when structured parsing fails.

Classes:
    - PytestResultParser: Parse pytest verbose output
    - TestExecutor: Run tests and return parsed results

Part of ADR 006: Repair Workflow Architecture.

Author: ASP Development Team
Date: December 10, 2025
"""

# pylint: disable=logging-fstring-interpolation,too-many-return-statements,too-many-nested-blocks

from __future__ import annotations

import json
import logging
import re
from typing import TYPE_CHECKING

from asp.models.execution import TestFailure, TestResult, create_fallback_result

if TYPE_CHECKING:
    from services.sandbox_executor import SubprocessSandboxExecutor
    from services.workspace_manager import Workspace

logger = logging.getLogger(__name__)


class ParserError(Exception):
    """Raised when test output parsing fails."""


class PytestResultParser:
    """
    Parse pytest verbose output into TestResult.

    Handles pytest output with -v flag, extracting:
    - Test counts (passed, failed, skipped, errors)
    - Failure details (test name, file, line, traceback)
    - Duration
    - Coverage (if pytest-cov used)

    Designed to be resilient - returns partial results rather than failing.
    """

    # Patterns for pytest output
    SUMMARY_PATTERN = re.compile(
        r"=+\s*(?:(?P<failed>\d+)\s+failed)?"
        r"(?:,?\s*(?P<passed>\d+)\s+passed)?"
        r"(?:,?\s*(?P<skipped>\d+)\s+skipped)?"
        r"(?:,?\s*(?P<errors>\d+)\s+errors?)?"
        r"(?:,?\s*(?P<warnings>\d+)\s+warnings?)?"
        r"\s+in\s+(?P<duration>[\d.]+)s?\s*=+",
        re.IGNORECASE,
    )

    # Alternative summary pattern (e.g., "5 passed in 1.23s")
    SIMPLE_SUMMARY_PATTERN = re.compile(
        r"(?P<passed>\d+)\s+passed"
        r"(?:,\s*(?P<failed>\d+)\s+failed)?"
        r"(?:,\s*(?P<skipped>\d+)\s+skipped)?"
        r"\s+in\s+(?P<duration>[\d.]+)s?",
        re.IGNORECASE,
    )

    # Pattern for individual test results
    TEST_RESULT_PATTERN = re.compile(
        r"(?P<file>[\w/\\.]+\.py)::(?P<test>[\w\[\]-]+)\s+(?P<status>PASSED|FAILED|SKIPPED|ERROR)",
        re.IGNORECASE,
    )

    # Pattern for failure block header
    FAILURE_HEADER_PATTERN = re.compile(
        r"_+\s*(?P<test_name>[\w\[\]-]+)\s*_+",
    )

    # Pattern for "FAILED file.py::test_name - reason"
    FAILED_LINE_PATTERN = re.compile(
        r"FAILED\s+(?P<file>[\w/\\.]+\.py)::(?P<test>[\w\[\]-]+)\s*-?\s*(?P<reason>.*)?",
        re.IGNORECASE,
    )

    # Pattern for coverage percentage
    COVERAGE_PATTERN = re.compile(
        r"TOTAL\s+\d+\s+\d+\s+(?P<coverage>\d+)%",
    )

    def parse(
        self,
        stdout: str,
        stderr: str,
        exit_code: int,
        duration_ms: int,
    ) -> TestResult:
        """
        Parse pytest output into TestResult.

        Args:
            stdout: Standard output from pytest
            stderr: Standard error from pytest
            exit_code: Process exit code
            duration_ms: Execution duration in milliseconds

        Returns:
            TestResult with parsed information

        Raises:
            ParserError: If parsing completely fails
        """
        combined = stdout + "\n" + stderr

        # Extract summary statistics
        passed, failed, skipped, errors, duration = self._parse_summary(
            combined, duration_ms
        )

        # Extract failures
        failures = self._parse_failures(combined)

        # Extract coverage if present
        coverage = self._parse_coverage(combined)

        # Calculate total
        total = passed + failed + skipped + errors

        # Sanity check - if we couldn't parse anything useful
        if total == 0 and exit_code != 0:
            logger.warning("Could not parse any test results from pytest output")
            # Return partial result with what we know
            return TestResult(
                framework="pytest",
                total_tests=-1,
                passed=-1,
                failed=-1 if exit_code != 0 else 0,
                skipped=0,
                errors=1 if exit_code != 0 else 0,
                duration_seconds=duration,
                coverage_percent=coverage,
                failures=failures,
                raw_output=combined,
                parsing_failed=True,
            )

        return TestResult(
            framework="pytest",
            total_tests=total,
            passed=passed,
            failed=failed,
            skipped=skipped,
            errors=errors,
            duration_seconds=duration,
            coverage_percent=coverage,
            failures=failures,
            raw_output=None,
            parsing_failed=False,
        )

    def _parse_summary(
        self,
        output: str,
        default_duration_ms: int,
    ) -> tuple[int, int, int, int, float]:
        """
        Parse summary line from pytest output.

        Returns:
            Tuple of (passed, failed, skipped, errors, duration_seconds)
        """
        # Try main summary pattern first
        match = self.SUMMARY_PATTERN.search(output)
        if match:
            return (
                int(match.group("passed") or 0),
                int(match.group("failed") or 0),
                int(match.group("skipped") or 0),
                int(match.group("errors") or 0),
                float(match.group("duration") or default_duration_ms / 1000),
            )

        # Try simple summary pattern
        match = self.SIMPLE_SUMMARY_PATTERN.search(output)
        if match:
            return (
                int(match.group("passed") or 0),
                int(match.group("failed") or 0),
                int(match.group("skipped") or 0),
                0,  # No errors in simple pattern
                float(match.group("duration") or default_duration_ms / 1000),
            )

        # Count individual test results as fallback
        passed = failed = skipped = errors = 0
        for match in self.TEST_RESULT_PATTERN.finditer(output):
            status = match.group("status").upper()
            if status == "PASSED":
                passed += 1
            elif status == "FAILED":
                failed += 1
            elif status == "SKIPPED":
                skipped += 1
            elif status == "ERROR":
                errors += 1

        return (passed, failed, skipped, errors, default_duration_ms / 1000)

    def _parse_failures(self, output: str) -> list[TestFailure]:
        """
        Parse failure details from pytest output.

        Returns:
            List of TestFailure objects
        """
        failures = []

        # Find FAILED lines first (most reliable)
        for match in self.FAILED_LINE_PATTERN.finditer(output):
            test_file = match.group("file")
            test_name = match.group("test")
            reason = match.group("reason") or ""

            # Try to extract more details from the failure block
            stack_trace = self._extract_traceback(output, test_name)
            error_type, error_message = self._parse_error_info(stack_trace, reason)

            # Try to find line number
            line_number = self._extract_line_number(stack_trace, test_file)

            failures.append(
                TestFailure(
                    test_name=test_name,
                    test_file=test_file,
                    line_number=line_number,
                    error_type=error_type,
                    error_message=error_message,
                    stack_trace=stack_trace,
                )
            )

        return failures

    def _extract_traceback(self, output: str, test_name: str) -> str:
        """
        Extract traceback for a specific test from output.

        Args:
            output: Full pytest output
            test_name: Name of the failing test

        Returns:
            Traceback string or empty string if not found
        """
        # Look for failure block: _____ test_name _____
        pattern = re.compile(
            rf"_+\s*{re.escape(test_name)}\s*_+\n(.*?)(?=_{{5,}}|\Z)",
            re.DOTALL,
        )
        match = pattern.search(output)
        if match:
            return match.group(1).strip()

        # Alternative: look for "short test summary" section
        short_pattern = re.compile(
            rf"FAILED.*{re.escape(test_name)}.*?\n(.*?)(?=FAILED|\Z)",
            re.DOTALL | re.IGNORECASE,
        )
        match = short_pattern.search(output)
        if match:
            return match.group(1).strip()

        return ""

    def _parse_error_info(
        self,
        traceback: str,
        reason: str,
    ) -> tuple[str, str]:
        """
        Extract error type and message from traceback.

        Returns:
            Tuple of (error_type, error_message)
        """
        # Common error patterns
        error_patterns = [
            # AssertionError: message
            re.compile(r"(\w+Error):\s*(.+?)(?:\n|$)"),
            # E   AssertionError
            re.compile(r"E\s+(\w+Error)(?::\s*(.+?))?(?:\n|$)"),
            # assert x == y (AssertionError without explicit message)
            re.compile(r"(AssertionError)\s*$", re.MULTILINE),
        ]

        for pattern in error_patterns:
            match = pattern.search(traceback)
            if match:
                error_type = match.group(1)
                error_message = (
                    match.group(2)
                    if len(match.groups()) > 1 and match.group(2)
                    else reason
                )
                return error_type, error_message or "Assertion failed"

        # Default to generic error
        return "TestFailure", reason or "Test failed"

    def _extract_line_number(self, traceback: str, test_file: str) -> int | None:
        """
        Extract line number from traceback.

        Args:
            traceback: Traceback text
            test_file: Test file path to match

        Returns:
            Line number or None if not found
        """
        # Pattern: file.py:123: or file.py", line 123
        patterns = [
            re.compile(rf"{re.escape(test_file)}:(\d+)"),
            re.compile(rf'{re.escape(test_file)}",\s*line\s*(\d+)'),
            # Generic line pattern as fallback
            re.compile(r":(\d+):\s*(?:in|AssertionError)"),
        ]

        for pattern in patterns:
            match = pattern.search(traceback)
            if match:
                return int(match.group(1))

        return None

    def _parse_coverage(self, output: str) -> float | None:
        """
        Extract coverage percentage from pytest-cov output.

        Returns:
            Coverage percentage or None if not found
        """
        match = self.COVERAGE_PATTERN.search(output)
        if match:
            return float(match.group("coverage"))

        # Alternative: look for coverage JSON file reference
        # (would need to read file, not implemented)

        return None


class TestExecutor:
    """
    Execute real test frameworks and parse results.

    Coordinates test execution through SandboxExecutor and parses
    results using framework-specific parsers. Falls back to raw
    output when parsing fails.

    Example:
        >>> executor = TestExecutor(sandbox)
        >>> result = executor.run_tests(workspace, coverage=True)
        >>> if result.success:
        ...     print("All tests passed!")
        >>> else:
        ...     for failure in result.failures:
        ...         print(f"FAILED: {failure.test_name}")
    """

    # Test framework detection order
    FRAMEWORK_INDICATORS = {
        "pytest": ["pytest.ini", "pyproject.toml", "setup.cfg", "conftest.py"],
        "unittest": ["setup.py"],  # Default Python testing
    }

    def __init__(self, sandbox: SubprocessSandboxExecutor):
        """
        Initialize test executor.

        Args:
            sandbox: Sandbox executor for running test commands
        """
        self.sandbox = sandbox
        self.parsers = {
            "pytest": PytestResultParser(),
        }
        logger.debug("TestExecutor initialized")

    def run_tests(
        self,
        workspace: Workspace,
        framework: str | None = None,
        test_path: str | None = None,
        coverage: bool = True,
    ) -> TestResult:
        """
        Run tests in workspace and return parsed results.

        Args:
            workspace: Workspace containing code and tests
            framework: Test framework (auto-detected if None)
            test_path: Specific test file/directory (all tests if None)
            coverage: Whether to collect coverage data

        Returns:
            TestResult with parsed pass/fail/error details
        """
        # Detect framework if not specified
        framework = framework or self._detect_framework(workspace)
        logger.info(f"Running tests with framework: {framework}")

        # Build command
        command = self._build_command(framework, test_path, coverage)
        logger.debug(f"Test command: {' '.join(command)}")

        # Execute tests
        result = self.sandbox.execute(workspace, command)

        # Parse results
        parser = self.parsers.get(framework)

        if parser is None:
            logger.warning(f"No parser for framework '{framework}', using fallback")
            return create_fallback_result(result, framework)

        try:
            return parser.parse(
                result.stdout,
                result.stderr,
                result.exit_code,
                result.duration_ms,
            )
        except ParserError as e:
            logger.warning(f"Parser failed for {framework}: {e}, using fallback")
            return create_fallback_result(result, framework)
        except Exception as e:
            logger.error(f"Unexpected parser error: {e}, using fallback")
            return create_fallback_result(result, framework)

    def _detect_framework(self, workspace: Workspace) -> str:
        """
        Auto-detect test framework from project files.

        Args:
            workspace: Workspace to analyze

        Returns:
            Detected framework name (defaults to "pytest")
        """
        repo_path = workspace.target_repo_path

        # Check for framework indicators
        for framework, indicators in self.FRAMEWORK_INDICATORS.items():
            for indicator in indicators:
                if (repo_path / indicator).exists():
                    # Check if pytest is in pyproject.toml
                    if indicator == "pyproject.toml":
                        try:
                            content = (repo_path / indicator).read_text()
                            if "pytest" in content.lower():
                                return "pytest"
                        except OSError:
                            pass
                    elif framework == "pytest":
                        return "pytest"

        # Check for test files
        test_files = list(repo_path.glob("**/test_*.py"))
        test_files.extend(repo_path.glob("**/*_test.py"))

        if test_files:
            # Default to pytest for Python projects
            return "pytest"

        # Check package.json for JS projects
        package_json = repo_path / "package.json"
        if package_json.exists():
            try:
                pkg = json.loads(package_json.read_text())
                dev_deps = pkg.get("devDependencies", {})
                if "jest" in dev_deps:
                    return "jest"
                if "mocha" in dev_deps:
                    return "mocha"
            except (json.JSONDecodeError, OSError):
                pass

        # Check for Go
        if (repo_path / "go.mod").exists():
            return "go"

        # Check for Rust
        if (repo_path / "Cargo.toml").exists():
            return "cargo"

        # Default to pytest
        logger.debug("Could not detect framework, defaulting to pytest")
        return "pytest"

    def _build_command(
        self,
        framework: str,
        test_path: str | None,
        coverage: bool,
    ) -> list[str]:
        """
        Build test command for framework.

        Args:
            framework: Test framework name
            test_path: Optional specific test path
            coverage: Whether to collect coverage

        Returns:
            Command as list of strings
        """
        if framework == "pytest":
            cmd = ["pytest", "-v", "--tb=short"]
            if coverage:
                cmd.extend(["--cov=.", "--cov-report=term-missing"])
            if test_path:
                cmd.append(test_path)
            return cmd

        if framework == "unittest":
            cmd = ["python", "-m", "unittest"]
            if test_path:
                cmd.append(test_path)
            else:
                cmd.append("discover")
            return cmd

        if framework == "jest":
            cmd = ["npx", "jest", "--verbose"]
            if coverage:
                cmd.append("--coverage")
            if test_path:
                cmd.append(test_path)
            return cmd

        if framework == "go":
            cmd = ["go", "test", "-v"]
            if coverage:
                cmd.append("-cover")
            cmd.append(test_path or "./...")
            return cmd

        if framework == "cargo":
            cmd = ["cargo", "test", "--", "--nocapture"]
            if test_path:
                cmd.append(test_path)
            return cmd

        # Unknown framework - try running it directly
        logger.warning(f"Unknown framework '{framework}', attempting direct execution")
        return [framework, test_path or "."]
