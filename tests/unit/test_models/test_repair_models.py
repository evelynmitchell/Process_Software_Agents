"""
Unit tests for repair models.

Tests for RepairAttempt, RepairInput, RepairOutput, and RepairResult models.
"""

# pylint: disable=use-implicit-booleaness-not-comparison

import pytest

from asp.models.diagnostic import (
    AffectedFile,
    CodeChange,
    DiagnosticReport,
    IssueType,
    Severity,
    SuggestedFix,
)
from asp.models.execution import TestResult
from asp.models.repair import RepairAttempt, RepairInput, RepairOutput, RepairResult


class TestRepairAttempt:
    """Tests for RepairAttempt model."""

    @pytest.fixture
    def code_change(self):
        """Create a valid code change."""
        return CodeChange(
            file_path="src/calculator.py",
            search_text="return a - b",
            replace_text="return a + b",
        )

    @pytest.fixture
    def success_test_result(self):
        """Create a passing test result."""
        return TestResult(
            framework="pytest",
            total_tests=5,
            passed=5,
            failed=0,
            duration_seconds=1.0,
        )

    @pytest.fixture
    def failure_test_result(self):
        """Create a failing test result."""
        return TestResult(
            framework="pytest",
            total_tests=5,
            passed=3,
            failed=2,
            duration_seconds=1.0,
        )

    def test_valid_repair_attempt(self, code_change, success_test_result):
        """Test creating a valid repair attempt."""
        attempt = RepairAttempt(
            attempt_number=1,
            changes_made=[code_change],
            test_result=success_test_result,
        )
        assert attempt.attempt_number == 1
        assert len(attempt.changes_made) == 1
        assert attempt.succeeded is True
        assert attempt.why_failed is None

    def test_failed_repair_attempt(self, code_change, failure_test_result):
        """Test creating a failed repair attempt."""
        attempt = RepairAttempt(
            attempt_number=1,
            changes_made=[code_change],
            test_result=failure_test_result,
            why_failed="The operator fix did not address all issues",
        )
        assert attempt.succeeded is False
        assert attempt.why_failed is not None

    def test_succeeded_property(
        self, code_change, success_test_result, failure_test_result
    ):
        """Test the succeeded property."""
        success_attempt = RepairAttempt(
            attempt_number=1,
            changes_made=[code_change],
            test_result=success_test_result,
        )
        assert success_attempt.succeeded is True

        failure_attempt = RepairAttempt(
            attempt_number=1,
            changes_made=[code_change],
            test_result=failure_test_result,
        )
        assert failure_attempt.succeeded is False

    def test_attempt_number_validation(self, code_change, success_test_result):
        """Test that attempt number must be positive."""
        with pytest.raises(ValueError):
            RepairAttempt(
                attempt_number=0,
                changes_made=[code_change],
                test_result=success_test_result,
            )

    def test_rollback_performed_default(self, code_change, success_test_result):
        """Test default value for rollback_performed."""
        attempt = RepairAttempt(
            attempt_number=1,
            changes_made=[code_change],
            test_result=success_test_result,
        )
        assert attempt.rollback_performed is False


class TestRepairInput:
    """Tests for RepairInput model."""

    @pytest.fixture
    def diagnostic_report(self):
        """Create a valid diagnostic report."""
        return DiagnosticReport(
            task_id="REPAIR-001",
            issue_type=IssueType.LOGIC_ERROR,
            severity=Severity.HIGH,
            root_cause="The add function uses subtraction instead of addition",
            affected_files=[
                AffectedFile(
                    path="src/calculator.py",
                    line_start=5,
                    line_end=7,
                    code_snippet="return a - b",
                    issue_description="Wrong operator",
                )
            ],
            suggested_fixes=[
                SuggestedFix(
                    fix_id="FIX-001",
                    description="Change subtraction to addition",
                    confidence=0.95,
                    changes=[
                        CodeChange(
                            file_path="src/calculator.py",
                            search_text="return a - b",
                            replace_text="return a + b",
                        )
                    ],
                )
            ],
            confidence=0.95,
        )

    def test_valid_repair_input(self, diagnostic_report):
        """Test creating a valid repair input."""
        input_data = RepairInput(
            task_id="REPAIR-001",
            workspace_path="/workspaces/my-project",
            diagnostic=diagnostic_report,
        )
        assert input_data.task_id == "REPAIR-001"
        assert input_data.workspace_path == "/workspaces/my-project"
        assert input_data.attempt_count == 0
        assert input_data.has_failed_attempts is False
        assert input_data.last_attempt is None

    def test_task_id_validation(self, diagnostic_report):
        """Test task_id minimum length."""
        with pytest.raises(ValueError, match="at least 3 characters"):
            RepairInput(
                task_id="AB",
                workspace_path="/path",
                diagnostic=diagnostic_report,
            )

    def test_task_id_trimmed(self, diagnostic_report):
        """Test task_id whitespace is trimmed."""
        input_data = RepairInput(
            task_id="  REPAIR-001  ",
            workspace_path="/path",
            diagnostic=diagnostic_report,
        )
        assert input_data.task_id == "REPAIR-001"

    def test_with_previous_attempts(self, diagnostic_report):
        """Test input with previous attempts."""
        code_change = CodeChange(
            file_path="src/calculator.py",
            search_text="return a - b",
            replace_text="return a + b",
        )
        failed_attempt = RepairAttempt(
            attempt_number=1,
            changes_made=[code_change],
            test_result=TestResult(
                framework="pytest",
                total_tests=5,
                passed=3,
                failed=2,
                duration_seconds=1.0,
            ),
            why_failed="Fix did not address all issues",
        )

        input_data = RepairInput(
            task_id="REPAIR-001",
            workspace_path="/path",
            diagnostic=diagnostic_report,
            previous_attempts=[failed_attempt],
        )
        assert input_data.attempt_count == 1
        assert input_data.has_failed_attempts is True
        assert input_data.last_attempt == failed_attempt

    def test_max_changes_per_file_bounds(self, diagnostic_report):
        """Test max_changes_per_file validation."""
        # Valid
        input_valid = RepairInput(
            task_id="REPAIR-001",
            workspace_path="/path",
            diagnostic=diagnostic_report,
            max_changes_per_file=50,
        )
        assert input_valid.max_changes_per_file == 50

        # Too low
        with pytest.raises(ValueError):
            RepairInput(
                task_id="REPAIR-001",
                workspace_path="/path",
                diagnostic=diagnostic_report,
                max_changes_per_file=0,
            )

        # Too high
        with pytest.raises(ValueError):
            RepairInput(
                task_id="REPAIR-001",
                workspace_path="/path",
                diagnostic=diagnostic_report,
                max_changes_per_file=101,
            )


class TestRepairOutput:
    """Tests for RepairOutput model."""

    @pytest.fixture
    def code_change(self):
        """Create a valid code change."""
        return CodeChange(
            file_path="src/calculator.py",
            search_text="return a - b",
            replace_text="return a + b",
        )

    def test_valid_repair_output(self, code_change):
        """Test creating a valid repair output."""
        output = RepairOutput(
            task_id="REPAIR-001",
            strategy="Apply direct operator fix from diagnostic",
            changes=[code_change],
            explanation="Changing the operator from - to + will fix the add function",
            confidence=0.95,
        )
        assert output.task_id == "REPAIR-001"
        assert output.confidence == 0.95
        assert len(output.changes) == 1
        assert output.is_high_confidence is True

    def test_strategy_min_length(self, code_change):
        """Test strategy minimum length."""
        with pytest.raises(ValueError):
            RepairOutput(
                task_id="REPAIR-001",
                strategy="short",  # Too short
                changes=[code_change],
                explanation="Detailed explanation of the fix here",
                confidence=0.9,
            )

    def test_explanation_min_length(self, code_change):
        """Test explanation minimum length."""
        with pytest.raises(ValueError):
            RepairOutput(
                task_id="REPAIR-001",
                strategy="Apply the recommended fix",
                changes=[code_change],
                explanation="short",  # Too short
                confidence=0.9,
            )

    def test_must_have_changes(self):
        """Test must have at least one change."""
        with pytest.raises(ValueError):
            RepairOutput(
                task_id="REPAIR-001",
                strategy="Apply the recommended fix",
                changes=[],  # Empty!
                explanation="Detailed explanation of the fix here",
                confidence=0.9,
            )

    def test_confidence_bounds(self, code_change):
        """Test confidence validation."""
        # Valid at boundaries
        output_zero = RepairOutput(
            task_id="REPAIR-001",
            strategy="Low confidence repair attempt",
            changes=[code_change],
            explanation="Detailed explanation of the fix here",
            confidence=0.0,
        )
        assert output_zero.confidence == 0.0
        assert output_zero.is_high_confidence is False

        output_one = RepairOutput(
            task_id="REPAIR-001",
            strategy="High confidence repair attempt",
            changes=[code_change],
            explanation="Detailed explanation of the fix here",
            confidence=1.0,
        )
        assert output_one.confidence == 1.0
        assert output_one.is_high_confidence is True

        # Invalid
        with pytest.raises(ValueError):
            RepairOutput(
                task_id="REPAIR-001",
                strategy="Invalid confidence repair",
                changes=[code_change],
                explanation="Detailed explanation of the fix here",
                confidence=1.5,
            )

    def test_is_high_confidence_threshold(self, code_change):
        """Test is_high_confidence at threshold."""
        high = RepairOutput(
            task_id="REPAIR-001",
            strategy="High confidence at threshold",
            changes=[code_change],
            explanation="Detailed explanation of the fix here",
            confidence=0.8,
        )
        assert high.is_high_confidence is True

        low = RepairOutput(
            task_id="REPAIR-001",
            strategy="Low confidence below threshold",
            changes=[code_change],
            explanation="Detailed explanation of the fix here",
            confidence=0.79,
        )
        assert low.is_high_confidence is False

    def test_file_count_property(self):
        """Test file_count property."""
        changes = [
            CodeChange(file_path="file1.py", search_text="a", replace_text="b"),
            CodeChange(file_path="file2.py", search_text="c", replace_text="d"),
            CodeChange(file_path="file1.py", search_text="e", replace_text="f"),
        ]
        output = RepairOutput(
            task_id="REPAIR-001",
            strategy="Multi-file repair strategy",
            changes=changes,
            explanation="Detailed explanation of the fix here",
            confidence=0.9,
        )
        assert output.file_count == 2  # file1.py and file2.py
        assert output.change_count == 3

    def test_optional_fields(self, code_change):
        """Test optional fields have correct defaults."""
        output = RepairOutput(
            task_id="REPAIR-001",
            strategy="Apply the recommended fix",
            changes=[code_change],
            explanation="Detailed explanation of the fix here",
            confidence=0.9,
        )
        assert output.alternative_fixes is None
        assert output.considerations == []
        assert output.based_on_fix_id is None


class TestRepairResult:
    """Tests for RepairResult model."""

    @pytest.fixture
    def test_result(self):
        """Create a test result."""
        return TestResult(
            framework="pytest",
            total_tests=5,
            passed=5,
            failed=0,
            duration_seconds=1.5,
        )

    @pytest.fixture
    def code_change(self):
        """Create a code change."""
        return CodeChange(
            file_path="src/calculator.py",
            search_text="return a - b",
            replace_text="return a + b",
        )

    def test_successful_repair_result(self, test_result, code_change):
        """Test creating a successful repair result."""
        result = RepairResult(
            task_id="REPAIR-001",
            success=True,
            iterations_used=1,
            final_test_result=test_result,
            changes_made=[code_change],
        )
        assert result.success is True
        assert result.iterations_used == 1
        assert result.total_changes == 1
        assert result.files_modified == ["src/calculator.py"]
        assert result.escalated_to_human is False

    def test_failed_repair_result(self, test_result):
        """Test creating a failed repair result."""
        result = RepairResult(
            task_id="REPAIR-001",
            success=False,
            iterations_used=5,
            final_test_result=test_result,
            escalated_to_human=True,
            escalation_reason="Maximum iterations reached without fix",
        )
        assert result.success is False
        assert result.escalated_to_human is True
        assert result.escalation_reason is not None

    def test_files_modified_property(self, test_result):
        """Test files_modified property with multiple files."""
        changes = [
            CodeChange(file_path="src/a.py", search_text="x", replace_text="y"),
            CodeChange(file_path="src/b.py", search_text="x", replace_text="y"),
            CodeChange(file_path="src/a.py", search_text="z", replace_text="w"),
        ]
        result = RepairResult(
            task_id="REPAIR-001",
            success=True,
            iterations_used=1,
            final_test_result=test_result,
            changes_made=changes,
        )
        # Should be unique files
        assert len(result.files_modified) == 2
        assert "src/a.py" in result.files_modified
        assert "src/b.py" in result.files_modified

    def test_iterations_used_validation(self, test_result):
        """Test iterations_used must be non-negative."""
        with pytest.raises(ValueError):
            RepairResult(
                task_id="REPAIR-001",
                success=True,
                iterations_used=-1,
                final_test_result=test_result,
            )

    def test_empty_changes(self, test_result):
        """Test result with no changes."""
        result = RepairResult(
            task_id="REPAIR-001",
            success=False,
            iterations_used=0,
            final_test_result=test_result,
            changes_made=[],
        )
        assert result.total_changes == 0
        assert result.files_modified == []
