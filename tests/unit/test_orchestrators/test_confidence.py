"""
Unit tests for confidence calculation module.

Tests the confidence scoring system for repair operations.
"""

# pylint: disable=too-many-public-methods,use-implicit-booleaness-not-comparison

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
from asp.models.repair import RepairAttempt, RepairOutput
from asp.orchestrators.confidence import (
    ConfidenceBreakdown,
    calculate_confidence,
    calculate_diagnostic_confidence,
    calculate_fix_confidence,
    calculate_iteration_penalty,
    calculate_test_coverage_confidence,
)


class TestConfidenceBreakdown:
    """Tests for ConfidenceBreakdown dataclass."""

    def test_overall_calculation(self):
        """Test overall confidence calculation."""
        breakdown = ConfidenceBreakdown(
            diagnostic_confidence=1.0,
            fix_confidence=1.0,
            test_coverage_confidence=1.0,
            iteration_penalty=0.0,
        )
        # 1.0 * 0.3 + 1.0 * 0.3 + 1.0 * 0.4 = 1.0
        assert breakdown.overall == 1.0

    def test_overall_with_weights(self):
        """Test weights: 30% diagnostic, 30% fix, 40% test coverage."""
        breakdown = ConfidenceBreakdown(
            diagnostic_confidence=0.5,
            fix_confidence=0.5,
            test_coverage_confidence=0.5,
            iteration_penalty=0.0,
        )
        # 0.5 * 0.3 + 0.5 * 0.3 + 0.5 * 0.4 = 0.5
        assert breakdown.overall == 0.5

    def test_overall_with_penalty(self):
        """Test iteration penalty is subtracted."""
        breakdown = ConfidenceBreakdown(
            diagnostic_confidence=1.0,
            fix_confidence=1.0,
            test_coverage_confidence=1.0,
            iteration_penalty=0.2,
        )
        # 1.0 - 0.2 = 0.8
        assert breakdown.overall == 0.8

    def test_overall_clamped_to_zero(self):
        """Test overall never goes below 0."""
        breakdown = ConfidenceBreakdown(
            diagnostic_confidence=0.1,
            fix_confidence=0.1,
            test_coverage_confidence=0.1,
            iteration_penalty=0.5,
        )
        # 0.1 * 0.3 + 0.1 * 0.3 + 0.1 * 0.4 - 0.5 = 0.1 - 0.5 = -0.4 -> 0.0
        assert breakdown.overall == 0.0

    def test_overall_clamped_to_one(self):
        """Test overall never exceeds 1 (shouldn't happen but safety check)."""
        breakdown = ConfidenceBreakdown(
            diagnostic_confidence=1.0,
            fix_confidence=1.0,
            test_coverage_confidence=1.0,
            iteration_penalty=-0.5,  # Negative penalty (unusual)
        )
        # 1.0 + 0.5 = 1.5 -> 1.0
        assert breakdown.overall == 1.0

    def test_is_high_confidence(self):
        """Test is_high_confidence threshold (>= 0.8)."""
        high = ConfidenceBreakdown(
            diagnostic_confidence=1.0,
            fix_confidence=1.0,
            test_coverage_confidence=1.0,
        )
        assert high.is_high_confidence is True

        at_threshold = ConfidenceBreakdown(
            diagnostic_confidence=0.8,
            fix_confidence=0.8,
            test_coverage_confidence=0.8,
        )
        assert at_threshold.is_high_confidence is True

        below = ConfidenceBreakdown(
            diagnostic_confidence=0.7,
            fix_confidence=0.7,
            test_coverage_confidence=0.7,
        )
        assert below.is_high_confidence is False

    def test_is_low_confidence(self):
        """Test is_low_confidence threshold (< 0.5)."""
        low = ConfidenceBreakdown(
            diagnostic_confidence=0.3,
            fix_confidence=0.3,
            test_coverage_confidence=0.3,
        )
        assert low.is_low_confidence is True

        at_threshold = ConfidenceBreakdown(
            diagnostic_confidence=0.5,
            fix_confidence=0.5,
            test_coverage_confidence=0.5,
        )
        assert at_threshold.is_low_confidence is False

    def test_to_dict(self):
        """Test to_dict serialization."""
        breakdown = ConfidenceBreakdown(
            diagnostic_confidence=0.8,
            fix_confidence=0.75,
            test_coverage_confidence=0.9,
            iteration_penalty=0.05,
        )
        result = breakdown.to_dict()

        assert result["diagnostic_confidence"] == 0.8
        assert result["fix_confidence"] == 0.75
        assert result["test_coverage_confidence"] == 0.9
        assert result["iteration_penalty"] == 0.05
        assert "overall" in result


class TestCalculateDiagnosticConfidence:
    """Tests for calculate_diagnostic_confidence."""

    @pytest.fixture
    def base_diagnostic(self):
        """Create a base diagnostic report."""
        return DiagnosticReport(
            task_id="TEST-001",
            issue_type=IssueType.LOGIC_ERROR,
            severity=Severity.HIGH,
            root_cause="The function uses incorrect operator" * 3,  # > 100 chars
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
                    description="Change operator",
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
            confidence=0.9,
        )

    def test_base_confidence_used(self, base_diagnostic):
        """Test that diagnostic's own confidence is primary factor."""
        confidence = calculate_diagnostic_confidence(base_diagnostic)
        # Should be close to 0.9 * adjustments
        assert 0.8 <= confidence <= 0.95

    def test_single_file_factor(self, base_diagnostic):
        """Test single file gives best file factor (1.0)."""
        confidence = calculate_diagnostic_confidence(base_diagnostic)
        # Single file = 1.0 factor
        assert confidence > 0.8

    def test_multiple_files_reduces_confidence(self, base_diagnostic):
        """Test multiple files reduces confidence."""
        # Add more affected files
        base_diagnostic.affected_files.extend(
            [
                AffectedFile(
                    path=f"src/file{i}.py",
                    line_start=1,
                    line_end=10,
                    code_snippet="code",
                    issue_description="Issue found in file that needs fixing",
                )
                for i in range(4)  # Total of 5 files now
            ]
        )

        confidence = calculate_diagnostic_confidence(base_diagnostic)
        # 5 files = 0.8 factor
        assert confidence < 0.85

    def test_single_fix_best(self, base_diagnostic):
        """Test single suggested fix gives best fix factor."""
        confidence = calculate_diagnostic_confidence(base_diagnostic)
        # Should be high with single fix
        assert confidence >= 0.85

    def test_many_fixes_reduces_confidence(self, base_diagnostic):
        """Test many suggested fixes reduces confidence."""
        # Add more fixes
        base_diagnostic.suggested_fixes.extend(
            [
                SuggestedFix(
                    fix_id=f"FIX-{i:03d}",
                    description=f"Alternative fix {i}",
                    confidence=0.5,
                    changes=[
                        CodeChange(
                            file_path="src/calculator.py",
                            search_text="x",
                            replace_text="y",
                        )
                    ],
                )
                for i in range(4)
            ]
        )

        confidence = calculate_diagnostic_confidence(base_diagnostic)
        # 5 fixes = 0.85 factor
        assert confidence < 0.85

    def test_short_root_cause_reduces_confidence(self, base_diagnostic):
        """Test short root cause reduces confidence."""
        base_diagnostic.root_cause = "Bug"  # < 50 chars
        confidence = calculate_diagnostic_confidence(base_diagnostic)
        # Short root cause = 0.9 factor
        assert confidence < 0.9


class TestCalculateFixConfidence:
    """Tests for calculate_fix_confidence."""

    @pytest.fixture
    def base_repair_output(self):
        """Create a base repair output."""
        return RepairOutput(
            task_id="TEST-001",
            strategy="Apply the recommended fix from diagnostic analysis",
            changes=[
                CodeChange(
                    file_path="src/calculator.py",
                    search_text="return a - b  # This is the problematic line",
                    replace_text="return a + b  # Fixed operator",
                )
            ],
            explanation="The add function incorrectly used subtraction operator",
            confidence=0.9,
        )

    def test_base_confidence_used(self, base_repair_output):
        """Test repair's own confidence is primary factor."""
        confidence = calculate_fix_confidence(base_repair_output)
        # Should be close to 0.9 * adjustments
        assert 0.8 <= confidence <= 0.95

    def test_single_change_best(self, base_repair_output):
        """Test single change gives best factor."""
        confidence = calculate_fix_confidence(base_repair_output)
        assert confidence >= 0.85

    def test_many_changes_reduces_confidence(self, base_repair_output):
        """Test many changes reduces confidence."""
        # Add more changes
        base_repair_output.changes.extend(
            [
                CodeChange(
                    file_path="src/calculator.py",
                    search_text=f"line_{i} = {i}",
                    replace_text=f"line_{i} = {i+1}",
                )
                for i in range(6)  # Total of 7 changes
            ]
        )

        confidence = calculate_fix_confidence(base_repair_output)
        # Many changes = 0.8 factor
        assert confidence < 0.85

    def test_multiple_files_reduces_confidence(self, base_repair_output):
        """Test changes to multiple files reduces confidence."""
        base_repair_output.changes.extend(
            [
                CodeChange(
                    file_path=f"src/file{i}.py",
                    search_text="old_text_to_find",
                    replace_text="new_text",
                )
                for i in range(3)
            ]
        )

        confidence = calculate_fix_confidence(base_repair_output)
        # 4 files = 0.85 factor
        assert confidence < 0.85

    def test_short_search_text_reduces_confidence(self, base_repair_output):
        """Test short search text reduces confidence."""
        base_repair_output.changes[0].search_text = "x"  # Very short
        confidence = calculate_fix_confidence(base_repair_output)
        # Short search = 0.85 factor
        assert confidence < 0.85

    def test_previous_failures_reduce_confidence(self, base_repair_output):
        """Test previous failures apply penalty."""
        failed_attempt = RepairAttempt(
            attempt_number=1,
            changes_made=[
                CodeChange(
                    file_path="src/calculator.py",
                    search_text="x",
                    replace_text="y",
                )
            ],
            test_result=TestResult(
                framework="pytest",
                total_tests=5,
                passed=3,
                failed=2,
                duration_seconds=1.0,
            ),
            why_failed="Did not fix the issue",
        )

        confidence = calculate_fix_confidence(
            base_repair_output,
            previous_attempts=[failed_attempt],
        )
        # 1 failed attempt = 0.1 penalty
        assert confidence < 0.85


class TestCalculateTestCoverageConfidence:
    """Tests for calculate_test_coverage_confidence."""

    def test_none_result_returns_middle(self):
        """Test None result returns 0.5 (unknown)."""
        confidence = calculate_test_coverage_confidence(None)
        assert confidence == 0.5

    def test_parsing_failed_returns_low(self):
        """Test parsing failed returns low confidence."""
        result = TestResult(
            framework="pytest",
            total_tests=-1,
            passed=-1,
            failed=-1,
            duration_seconds=1.0,
            parsing_failed=True,
        )
        confidence = calculate_test_coverage_confidence(result)
        assert confidence == 0.4

    def test_all_passing_high_confidence(self):
        """Test all passing tests gives high confidence."""
        result = TestResult(
            framework="pytest",
            total_tests=10,
            passed=10,
            failed=0,
            duration_seconds=1.0,
            coverage_percent=85.0,
        )
        confidence = calculate_test_coverage_confidence(result)
        # 100% pass rate = 0.7, 85% coverage = ~0.25 → ~0.95
        assert confidence >= 0.9

    def test_some_failures_reduces_confidence(self):
        """Test failures reduce confidence."""
        result = TestResult(
            framework="pytest",
            total_tests=10,
            passed=5,
            failed=5,
            duration_seconds=1.0,
        )
        confidence = calculate_test_coverage_confidence(result)
        # 50% pass rate
        assert confidence < 0.7

    def test_no_coverage_uses_default(self):
        """Test missing coverage uses 0.8 default factor."""
        result = TestResult(
            framework="pytest",
            total_tests=10,
            passed=10,
            failed=0,
            duration_seconds=1.0,
            coverage_percent=None,
        )
        confidence = calculate_test_coverage_confidence(result)
        # 100% pass, 0.8 coverage factor → 0.7 + 0.24 = 0.94
        assert 0.9 <= confidence <= 1.0

    def test_no_tests_assumes_passing(self):
        """Test zero tests assumes passing."""
        result = TestResult(
            framework="pytest",
            total_tests=0,
            passed=0,
            failed=0,
            duration_seconds=0.1,
        )
        confidence = calculate_test_coverage_confidence(result)
        # 100% pass rate assumed
        assert confidence >= 0.7


class TestCalculateIterationPenalty:
    """Tests for calculate_iteration_penalty."""

    def test_first_iteration_no_penalty(self):
        """Test first iteration has no penalty."""
        assert calculate_iteration_penalty(1) == 0.0

    def test_second_iteration_small_penalty(self):
        """Test second iteration has 5% penalty."""
        assert calculate_iteration_penalty(2) == 0.05

    def test_third_iteration_larger_penalty(self):
        """Test third iteration has 10% penalty."""
        assert calculate_iteration_penalty(3) == 0.10

    def test_penalty_increases_progressively(self):
        """Test penalty increases with each iteration."""
        penalties = [calculate_iteration_penalty(i) for i in range(1, 7)]
        expected = [0.0, 0.05, 0.10, 0.15, 0.20, 0.25]
        # Use pytest.approx for floating point comparison
        assert penalties == pytest.approx(expected)

    def test_penalty_capped_at_50(self):
        """Test penalty capped at 0.5 (50%)."""
        assert calculate_iteration_penalty(15) == 0.5
        assert calculate_iteration_penalty(100) == 0.5


class TestCalculateConfidence:
    """Tests for the main calculate_confidence function."""

    @pytest.fixture
    def diagnostic(self):
        """Create a diagnostic report."""
        return DiagnosticReport(
            task_id="TEST-001",
            issue_type=IssueType.LOGIC_ERROR,
            severity=Severity.HIGH,
            root_cause="The function uses incorrect operator which causes wrong results",
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
                    description="Change operator",
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
            confidence=0.9,
        )

    @pytest.fixture
    def repair_output(self):
        """Create a repair output."""
        return RepairOutput(
            task_id="TEST-001",
            strategy="Apply the recommended fix from diagnostic analysis",
            changes=[
                CodeChange(
                    file_path="src/calculator.py",
                    search_text="return a - b  # problematic",
                    replace_text="return a + b  # fixed",
                )
            ],
            explanation="The add function incorrectly used subtraction",
            confidence=0.9,
        )

    @pytest.fixture
    def test_result(self):
        """Create a test result."""
        return TestResult(
            framework="pytest",
            total_tests=10,
            passed=8,
            failed=2,
            duration_seconds=1.0,
            coverage_percent=80.0,
        )

    def test_returns_breakdown(self, diagnostic, repair_output, test_result):
        """Test returns ConfidenceBreakdown."""
        result = calculate_confidence(diagnostic, repair_output, test_result)
        assert isinstance(result, ConfidenceBreakdown)
        assert 0.0 <= result.overall <= 1.0

    def test_all_components_present(self, diagnostic, repair_output, test_result):
        """Test all confidence components are calculated."""
        result = calculate_confidence(diagnostic, repair_output, test_result)
        assert result.diagnostic_confidence > 0
        assert result.fix_confidence > 0
        assert result.test_coverage_confidence > 0
        assert result.iteration_penalty >= 0

    def test_iteration_affects_penalty(self, diagnostic, repair_output, test_result):
        """Test iteration number affects penalty."""
        result1 = calculate_confidence(
            diagnostic, repair_output, test_result, iteration=1
        )
        result3 = calculate_confidence(
            diagnostic, repair_output, test_result, iteration=3
        )

        assert result1.iteration_penalty < result3.iteration_penalty
        assert result1.overall > result3.overall

    def test_previous_attempts_affect_fix_confidence(
        self, diagnostic, repair_output, test_result
    ):
        """Test previous attempts reduce fix confidence."""
        failed_attempt = RepairAttempt(
            attempt_number=1,
            changes_made=[
                CodeChange(
                    file_path="src/calculator.py",
                    search_text="x",
                    replace_text="y",
                )
            ],
            test_result=test_result,
            why_failed="Did not fix the issue",
        )

        result_no_attempts = calculate_confidence(
            diagnostic, repair_output, test_result
        )
        result_with_attempts = calculate_confidence(
            diagnostic,
            repair_output,
            test_result,
            previous_attempts=[failed_attempt],
        )

        assert result_with_attempts.fix_confidence < result_no_attempts.fix_confidence

    def test_none_test_result_handled(self, diagnostic, repair_output):
        """Test None test result is handled."""
        result = calculate_confidence(diagnostic, repair_output, test_result=None)
        assert result.test_coverage_confidence == 0.5  # Unknown default
