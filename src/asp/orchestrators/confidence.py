"""
Confidence Calculation for Repair Workflow.

Provides objective confidence scoring for repair operations based on
diagnostic quality, fix characteristics, and test coverage.

Part of ADR 006: Repair Workflow Architecture.

Author: ASP Development Team
Date: December 10, 2025
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from asp.models.diagnostic import DiagnosticReport
    from asp.models.execution import TestResult
    from asp.models.repair import RepairAttempt, RepairOutput


@dataclass
class ConfidenceBreakdown:
    """
    Detailed breakdown of confidence scores.

    Provides transparency into how the overall confidence was calculated
    by breaking it down into component scores.

    Attributes:
        diagnostic_confidence: Confidence in the diagnosis (0.0-1.0)
            Based on: stack trace clarity, single vs multiple root causes,
            affected file count, diagnostic agent's own confidence
        fix_confidence: Confidence in the proposed fix (0.0-1.0)
            Based on: fix size (smaller = better), previous attempt history,
            repair agent's confidence, search-replace specificity
        test_coverage_confidence: Confidence based on test coverage (0.0-1.0)
            Based on: actual test coverage percentage, test pass rate
        iteration_penalty: Penalty applied for multiple failed attempts
        overall: Weighted combination of all confidence scores
    """

    diagnostic_confidence: float
    fix_confidence: float
    test_coverage_confidence: float
    iteration_penalty: float = 0.0

    @property
    def overall(self) -> float:
        """
        Calculate overall confidence score.

        Uses weighted average with iteration penalty:
        - Diagnostic: 30% weight (how well we understand the problem)
        - Fix: 30% weight (how likely the fix is to work)
        - Test coverage: 40% weight (objective measure of coverage)
        - Iteration penalty: Subtractive (reduces confidence with failures)

        Returns:
            Overall confidence score (0.0-1.0)
        """
        base = (
            self.diagnostic_confidence * 0.3
            + self.fix_confidence * 0.3
            + self.test_coverage_confidence * 0.4
        )
        # Apply iteration penalty
        result = base - self.iteration_penalty
        # Clamp to valid range
        return max(0.0, min(1.0, result))

    @property
    def is_high_confidence(self) -> bool:
        """Check if overall confidence is high (>= 0.8)."""
        return self.overall >= 0.8

    @property
    def is_low_confidence(self) -> bool:
        """Check if overall confidence is low (< 0.5)."""
        return self.overall < 0.5

    def to_dict(self) -> dict:
        """Convert to dictionary for logging/serialization."""
        return {
            "diagnostic_confidence": round(self.diagnostic_confidence, 3),
            "fix_confidence": round(self.fix_confidence, 3),
            "test_coverage_confidence": round(self.test_coverage_confidence, 3),
            "iteration_penalty": round(self.iteration_penalty, 3),
            "overall": round(self.overall, 3),
        }


def calculate_diagnostic_confidence(
    diagnostic: DiagnosticReport,
) -> float:
    """
    Calculate confidence in the diagnostic report.

    Factors:
    - Diagnostic agent's own confidence (primary factor)
    - Number of affected files (fewer = more focused = higher confidence)
    - Number of suggested fixes (one clear fix = higher confidence)
    - Root cause length (longer = more detailed = higher confidence)

    Args:
        diagnostic: The diagnostic report to evaluate

    Returns:
        Confidence score (0.0-1.0)
    """
    # Start with diagnostic agent's confidence
    base_confidence = diagnostic.confidence

    # Adjust for number of affected files
    # Single file issue is clearer than multi-file
    file_count = len(diagnostic.affected_files)
    if file_count == 1:
        file_factor = 1.0
    elif file_count <= 3:
        file_factor = 0.9
    else:
        file_factor = 0.8

    # Adjust for number of suggested fixes
    # One clear fix is better than many alternatives
    fix_count = len(diagnostic.suggested_fixes)
    if fix_count == 1:
        fix_factor = 1.0
    elif fix_count <= 2:
        fix_factor = 0.95
    else:
        fix_factor = 0.85

    # Adjust for root cause detail
    # Longer explanations tend to be more thorough
    root_cause_len = len(diagnostic.root_cause)
    if root_cause_len >= 100:
        detail_factor = 1.0
    elif root_cause_len >= 50:
        detail_factor = 0.95
    else:
        detail_factor = 0.9

    # Combine factors
    confidence = base_confidence * file_factor * fix_factor * detail_factor

    return max(0.0, min(1.0, confidence))


def calculate_fix_confidence(
    repair_output: RepairOutput,
    previous_attempts: list[RepairAttempt] | None = None,
) -> float:
    """
    Calculate confidence in the proposed fix.

    Factors:
    - Repair agent's own confidence (primary factor)
    - Number of changes (fewer = more focused = higher confidence)
    - Number of files modified (fewer = lower risk)
    - Previous attempt history (failures reduce confidence)
    - Search text specificity (longer = more unique = higher confidence)

    Args:
        repair_output: The proposed repair to evaluate
        previous_attempts: History of previous repair attempts

    Returns:
        Confidence score (0.0-1.0)
    """
    previous_attempts = previous_attempts or []

    # Start with repair agent's confidence
    base_confidence = repair_output.confidence

    # Adjust for change count
    change_count = repair_output.change_count
    if change_count == 1:
        change_factor = 1.0
    elif change_count <= 3:
        change_factor = 0.95
    elif change_count <= 5:
        change_factor = 0.9
    else:
        change_factor = 0.8

    # Adjust for file count
    file_count = repair_output.file_count
    if file_count == 1:
        file_factor = 1.0
    elif file_count <= 2:
        file_factor = 0.95
    else:
        file_factor = 0.85

    # Adjust for search text specificity
    # Longer, more specific search texts are more reliable
    avg_search_len = sum(len(c.search_text) for c in repair_output.changes) / max(
        len(repair_output.changes), 1
    )
    if avg_search_len >= 50:
        specificity_factor = 1.0
    elif avg_search_len >= 20:
        specificity_factor = 0.95
    else:
        specificity_factor = 0.85

    # Penalty for previous failures
    failed_attempts = sum(1 for a in previous_attempts if not a.succeeded)
    failure_penalty = failed_attempts * 0.1  # 10% penalty per failure

    # Combine factors
    confidence = (
        base_confidence * change_factor * file_factor * specificity_factor
        - failure_penalty
    )

    return max(0.0, min(1.0, confidence))


def calculate_test_coverage_confidence(
    test_result: TestResult | None,
    target_coverage: float = 80.0,
) -> float:
    """
    Calculate confidence based on test coverage.

    This is the most objective measure - actual test results.

    Factors:
    - Test pass rate (primary factor)
    - Coverage percentage (if available)
    - Parsing success (if parsing failed, lower confidence)

    Args:
        test_result: Test execution results (can be None if no tests run)
        target_coverage: Target coverage percentage for full confidence

    Returns:
        Confidence score (0.0-1.0)
    """
    if test_result is None:
        return 0.5  # Unknown - middle confidence

    # If parsing failed, we have less reliable data
    if test_result.parsing_failed:
        return 0.4

    # Calculate pass rate
    if test_result.total_tests > 0:
        pass_rate = test_result.passed / test_result.total_tests
    elif test_result.total_tests == 0:
        pass_rate = 1.0  # No tests = assume passing
    else:
        pass_rate = 0.5  # Unknown

    # Factor in coverage if available
    if test_result.coverage_percent is not None:
        coverage_factor = min(test_result.coverage_percent / target_coverage, 1.0)
    else:
        coverage_factor = 0.8  # Unknown coverage - assume moderate

    # Weight pass rate higher than coverage
    confidence = pass_rate * 0.7 + coverage_factor * 0.3

    return max(0.0, min(1.0, confidence))


def calculate_iteration_penalty(
    iteration: int,
    max_iterations: int = 5,
) -> float:
    """
    Calculate penalty for multiple repair iterations.

    More iterations = more failed attempts = lower confidence.

    Args:
        iteration: Current iteration number (1-indexed)
        max_iterations: Maximum expected iterations

    Returns:
        Penalty value (0.0-0.5, higher = more penalty)
    """
    if iteration <= 1:
        return 0.0

    # Progressive penalty: 5% for iteration 2, 10% for 3, etc.
    penalty = (iteration - 1) * 0.05

    # Cap at 50% penalty
    return min(penalty, 0.5)


def calculate_confidence(
    diagnostic: DiagnosticReport,
    repair_output: RepairOutput,
    test_result: TestResult | None = None,
    previous_attempts: list[RepairAttempt] | None = None,
    iteration: int = 1,
) -> ConfidenceBreakdown:
    """
    Calculate complete confidence breakdown for a repair operation.

    Combines diagnostic, fix, and test coverage confidence with
    iteration penalties to produce an overall confidence score.

    Args:
        diagnostic: Diagnostic report for the issue
        repair_output: Proposed repair
        test_result: Test results (if available)
        previous_attempts: History of previous attempts
        iteration: Current iteration number

    Returns:
        ConfidenceBreakdown with detailed scores

    Example:
        >>> confidence = calculate_confidence(
        ...     diagnostic=diagnostic_report,
        ...     repair_output=repair_output,
        ...     test_result=test_result,
        ...     iteration=2,
        ... )
        >>> print(f"Overall confidence: {confidence.overall:.2f}")
        >>> if confidence.is_low_confidence:
        ...     print("Consider requesting human review")
    """
    return ConfidenceBreakdown(
        diagnostic_confidence=calculate_diagnostic_confidence(diagnostic),
        fix_confidence=calculate_fix_confidence(repair_output, previous_attempts),
        test_coverage_confidence=calculate_test_coverage_confidence(test_result),
        iteration_penalty=calculate_iteration_penalty(iteration),
    )
