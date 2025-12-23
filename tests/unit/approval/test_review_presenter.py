"""
Unit tests for ReviewPresenter.

Tests the ReviewPresenter rich terminal UI functionality including:
- Initialization
- Display review information
- Quality report display
- Diff display
- Decision prompts
- Approval results

Author: ASP Development Team
Date: December 23, 2025
"""

from unittest.mock import MagicMock, patch

import pytest
from rich.console import Console

from asp.approval.review_presenter import ReviewPresenter


# =============================================================================
# Initialization Tests
# =============================================================================


class TestReviewPresenterInitialization:
    """Tests for ReviewPresenter initialization."""

    def test_init_creates_console(self):
        """Test that initialization creates a Console instance."""
        presenter = ReviewPresenter()
        assert presenter.console is not None
        assert isinstance(presenter.console, Console)


# =============================================================================
# Display Summary Tests
# =============================================================================


class TestDisplaySummary:
    """Tests for _display_summary method."""

    @pytest.fixture
    def presenter(self):
        """Create a ReviewPresenter with mocked console."""
        presenter = ReviewPresenter()
        presenter.console = MagicMock(spec=Console)
        return presenter

    def test_display_summary_passed(self, presenter):
        """Test summary display for passed quality gate."""
        quality_report = {"passed": True, "total_issues": 0}
        diff_stats = {"files_changed": 3, "insertions": 100, "deletions": 20}

        presenter._display_summary(
            task_id="TEST-001",
            gate_type="code_review",
            branch_name="feature/test",
            quality_report=quality_report,
            diff_stats=diff_stats,
        )

        # Verify print was called
        presenter.console.print.assert_called()

    def test_display_summary_failed(self, presenter):
        """Test summary display for failed quality gate."""
        quality_report = {"passed": False, "total_issues": 5}

        presenter._display_summary(
            task_id="TEST-001",
            gate_type="design_review",
            branch_name="feature/test",
            quality_report=quality_report,
            diff_stats=None,
        )

        presenter.console.print.assert_called()

    def test_display_summary_without_diff_stats(self, presenter):
        """Test summary display without diff statistics."""
        quality_report = {"passed": True, "total_issues": 0}

        presenter._display_summary(
            task_id="TEST-001",
            gate_type="test",
            branch_name="feature/test",
            quality_report=quality_report,
            diff_stats=None,
        )

        presenter.console.print.assert_called()


# =============================================================================
# Quality Report Tests
# =============================================================================


class TestDisplayQualityReport:
    """Tests for _display_quality_report method."""

    @pytest.fixture
    def presenter(self):
        """Create a ReviewPresenter with mocked console."""
        presenter = ReviewPresenter()
        presenter.console = MagicMock(spec=Console)
        return presenter

    def test_display_quality_report_no_issues(self, presenter):
        """Test quality report display with no issues."""
        report = {"issues": [], "passed": True}

        presenter._display_quality_report(report)

        # Should print "No quality issues found"
        presenter.console.print.assert_called()

    def test_display_quality_report_with_issues(self, presenter):
        """Test quality report display with issues."""
        report = {
            "issues": [
                {
                    "description": "Missing docstring",
                    "severity": "LOW",
                    "file": "src/main.py",
                    "line": 10,
                },
                {
                    "description": "Security vulnerability",
                    "severity": "CRITICAL",
                    "file": "src/auth.py",
                    "line": 25,
                },
                {
                    "description": "Performance issue",
                    "severity": "HIGH",
                },
                {
                    "description": "Code style",
                    "severity": "MEDIUM",
                    "file": "src/utils.py",
                },
            ],
            "passed": False,
        }

        presenter._display_quality_report(report)

        presenter.console.print.assert_called()

    def test_display_quality_report_unknown_severity(self, presenter):
        """Test quality report with unknown severity level."""
        report = {
            "issues": [
                {
                    "description": "Unknown issue",
                    "severity": "UNKNOWN",
                }
            ]
        }

        presenter._display_quality_report(report)

        presenter.console.print.assert_called()

    def test_display_quality_report_missing_description(self, presenter):
        """Test quality report with missing description."""
        report = {
            "issues": [
                {
                    "severity": "HIGH",
                    "file": "test.py",
                }
            ]
        }

        presenter._display_quality_report(report)

        presenter.console.print.assert_called()


# =============================================================================
# Severity Summary Tests
# =============================================================================


class TestDisplaySeveritySummary:
    """Tests for _display_severity_summary method."""

    @pytest.fixture
    def presenter(self):
        """Create a ReviewPresenter with mocked console."""
        presenter = ReviewPresenter()
        presenter.console = MagicMock(spec=Console)
        return presenter

    def test_display_severity_summary_all_levels(self, presenter):
        """Test severity summary with all severity levels."""
        report = {
            "issues": [
                {"severity": "CRITICAL"},
                {"severity": "HIGH"},
                {"severity": "HIGH"},
                {"severity": "MEDIUM"},
                {"severity": "MEDIUM"},
                {"severity": "MEDIUM"},
                {"severity": "LOW"},
            ]
        }

        presenter._display_severity_summary(report)

        # Should have printed summary
        presenter.console.print.assert_called()

    def test_display_severity_summary_only_critical(self, presenter):
        """Test severity summary with only critical issues."""
        report = {
            "issues": [
                {"severity": "CRITICAL"},
                {"severity": "CRITICAL"},
            ]
        }

        presenter._display_severity_summary(report)

        presenter.console.print.assert_called()

    def test_display_severity_summary_no_issues(self, presenter):
        """Test severity summary with no issues."""
        report = {"issues": []}

        presenter._display_severity_summary(report)

        # Should not print anything when no summary parts
        # (print might still be called but with empty content)

    def test_display_severity_summary_unknown_severity(self, presenter):
        """Test severity summary ignores unknown severity levels."""
        report = {
            "issues": [
                {"severity": "UNKNOWN"},
                {"severity": "VERY_HIGH"},
            ]
        }

        presenter._display_severity_summary(report)

        # Unknown severities should be ignored


# =============================================================================
# Diff Stats Tests
# =============================================================================


class TestDisplayDiffStats:
    """Tests for _display_diff_stats method."""

    @pytest.fixture
    def presenter(self):
        """Create a ReviewPresenter with mocked console."""
        presenter = ReviewPresenter()
        presenter.console = MagicMock(spec=Console)
        return presenter

    def test_display_diff_stats(self, presenter):
        """Test diff stats display."""
        diff_stats = {
            "files_changed": 5,
            "insertions": 150,
            "deletions": 30,
        }

        presenter._display_diff_stats(diff_stats)

        # Verify print calls (4 prints: header + 3 stats lines)
        assert presenter.console.print.call_count >= 4

    def test_display_diff_stats_zero_values(self, presenter):
        """Test diff stats display with zero values."""
        diff_stats = {
            "files_changed": 0,
            "insertions": 0,
            "deletions": 0,
        }

        presenter._display_diff_stats(diff_stats)

        presenter.console.print.assert_called()

    def test_display_diff_stats_missing_keys(self, presenter):
        """Test diff stats display with missing keys."""
        diff_stats = {}

        presenter._display_diff_stats(diff_stats)

        # Should use default values of 0
        presenter.console.print.assert_called()


# =============================================================================
# Full Diff Tests
# =============================================================================


class TestDisplayFullDiff:
    """Tests for _display_full_diff method."""

    @pytest.fixture
    def presenter(self):
        """Create a ReviewPresenter with mocked console."""
        presenter = ReviewPresenter()
        presenter.console = MagicMock(spec=Console)
        return presenter

    def test_display_full_diff_with_content(self, presenter):
        """Test full diff display with content."""
        diff = """
diff --git a/src/main.py b/src/main.py
--- a/src/main.py
+++ b/src/main.py
@@ -1,3 +1,4 @@
 def main():
+    print("Hello")
     pass
"""
        presenter._display_full_diff(diff)

        presenter.console.rule.assert_called_once()
        presenter.console.print.assert_called()

    def test_display_full_diff_empty(self, presenter):
        """Test full diff display with empty content."""
        presenter._display_full_diff("")

        # Should print "No changes in diff"
        presenter.console.print.assert_called()

    def test_display_full_diff_whitespace_only(self, presenter):
        """Test full diff display with whitespace only."""
        presenter._display_full_diff("   \n\t\n   ")

        presenter.console.print.assert_called()

    def test_display_full_diff_syntax_error_fallback(self, presenter):
        """Test full diff falls back to plain text on syntax error."""
        # Create a presenter with real console to test the try/except
        real_presenter = ReviewPresenter()
        real_presenter.console = MagicMock(spec=Console)

        # Mock Syntax to raise an exception
        with patch("asp.approval.review_presenter.Syntax") as mock_syntax:
            mock_syntax.side_effect = Exception("Syntax highlighting failed")

            real_presenter._display_full_diff("some diff content")

            # Should still print something (fallback to plain text)
            real_presenter.console.print.assert_called()


# =============================================================================
# Decision Prompt Tests
# =============================================================================


class TestDisplayDecisionPrompt:
    """Tests for display_decision_prompt method."""

    @pytest.fixture
    def presenter(self):
        """Create a ReviewPresenter with mocked console."""
        presenter = ReviewPresenter()
        presenter.console = MagicMock(spec=Console)
        return presenter

    def test_display_decision_prompt(self, presenter):
        """Test decision prompt display."""
        presenter.display_decision_prompt()

        presenter.console.rule.assert_called_once()
        # Should print multiple times (header + 3 options + spacing)
        assert presenter.console.print.call_count >= 4


# =============================================================================
# Approval Result Tests
# =============================================================================


class TestDisplayApprovalResult:
    """Tests for display_approval_result method."""

    @pytest.fixture
    def presenter(self):
        """Create a ReviewPresenter with mocked console."""
        presenter = ReviewPresenter()
        presenter.console = MagicMock(spec=Console)
        return presenter

    def test_display_approval_result_approved(self, presenter):
        """Test approval result display for APPROVED decision."""
        presenter.display_approval_result("APPROVED", merge_commit="abc123def456")

        presenter.console.print.assert_called()

    def test_display_approval_result_approved_no_commit(self, presenter):
        """Test approval result display for APPROVED without merge commit."""
        presenter.display_approval_result("APPROVED", merge_commit=None)

        presenter.console.print.assert_called()

    def test_display_approval_result_rejected(self, presenter):
        """Test approval result display for REJECTED decision."""
        presenter.display_approval_result("REJECTED")

        presenter.console.print.assert_called()

    def test_display_approval_result_deferred(self, presenter):
        """Test approval result display for DEFERRED decision."""
        presenter.display_approval_result("DEFERRED")

        presenter.console.print.assert_called()

    def test_display_approval_result_unknown(self, presenter):
        """Test approval result display for unknown decision."""
        presenter.display_approval_result("UNKNOWN")

        # Should still call print (for spacing)
        presenter.console.print.assert_called()


# =============================================================================
# Display Review Integration Tests
# =============================================================================


class TestDisplayReview:
    """Tests for display_review method."""

    @pytest.fixture
    def presenter(self):
        """Create a ReviewPresenter with mocked console."""
        presenter = ReviewPresenter()
        presenter.console = MagicMock(spec=Console)
        # Mock input to return 'n' (don't show diff)
        presenter.console.input.return_value = "n"
        return presenter

    def test_display_review_basic(self, presenter):
        """Test basic review display."""
        quality_report = {"passed": True, "total_issues": 0, "issues": []}
        diff = "some diff content"

        presenter.display_review(
            task_id="TEST-001",
            gate_type="code_review",
            quality_report=quality_report,
            diff=diff,
            branch_name="feature/test",
        )

        presenter.console.rule.assert_called()
        presenter.console.print.assert_called()
        presenter.console.input.assert_called_once()

    def test_display_review_with_diff_stats(self, presenter):
        """Test review display with diff statistics."""
        quality_report = {"passed": False, "total_issues": 2, "issues": []}
        diff = "diff content"
        diff_stats = {"files_changed": 3, "insertions": 50, "deletions": 10}

        presenter.display_review(
            task_id="TEST-002",
            gate_type="design_review",
            quality_report=quality_report,
            diff=diff,
            branch_name="feature/test",
            diff_stats=diff_stats,
        )

        presenter.console.print.assert_called()

    def test_display_review_show_diff(self, presenter):
        """Test review display when user wants to see diff."""
        presenter.console.input.return_value = "y"

        quality_report = {"passed": True, "total_issues": 0, "issues": []}
        diff = "diff content"

        presenter.display_review(
            task_id="TEST-003",
            gate_type="test",
            quality_report=quality_report,
            diff=diff,
            branch_name="feature/test",
        )

        # Should have called rule for diff section
        assert presenter.console.rule.call_count >= 2

    def test_display_review_uppercase_y_shows_diff(self, presenter):
        """Test that uppercase Y also shows diff."""
        presenter.console.input.return_value = "Y"

        quality_report = {"passed": True, "total_issues": 0, "issues": []}
        diff = "diff content"

        presenter.display_review(
            task_id="TEST-004",
            gate_type="test",
            quality_report=quality_report,
            diff=diff,
            branch_name="feature/test",
        )

        # Should show diff for 'Y' response
        assert presenter.console.rule.call_count >= 2


# =============================================================================
# Edge Cases
# =============================================================================


class TestEdgeCases:
    """Tests for edge cases and error handling."""

    def test_empty_quality_report(self):
        """Test handling of empty quality report."""
        presenter = ReviewPresenter()
        presenter.console = MagicMock(spec=Console)

        presenter._display_quality_report({})

        # Should handle empty report gracefully

    def test_none_diff_stats(self):
        """Test handling of None diff_stats."""
        presenter = ReviewPresenter()
        presenter.console = MagicMock(spec=Console)
        presenter.console.input.return_value = "n"

        quality_report = {"passed": True, "issues": []}

        # Should not raise
        presenter.display_review(
            task_id="TEST-001",
            gate_type="test",
            quality_report=quality_report,
            diff="",
            branch_name="feature/test",
            diff_stats=None,
        )

    def test_issue_without_file_or_line(self):
        """Test handling issues without file or line information."""
        presenter = ReviewPresenter()
        presenter.console = MagicMock(spec=Console)

        report = {
            "issues": [
                {"description": "General issue", "severity": "MEDIUM"},
            ]
        }

        presenter._display_quality_report(report)

        # Should handle gracefully with "-" as location
