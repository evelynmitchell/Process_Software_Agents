"""
Tests for asp.approval.approval_collector module.

Tests the approval decision collection from user input.
"""

import subprocess
from unittest import mock

from asp.approval.base import ApprovalResponse, ReviewDecision
from asp.approval.approval_collector import ApprovalCollector


class TestApprovalCollectorInit:
    """Tests for ApprovalCollector initialization."""

    def test_init_creates_console(self):
        """Test initialization creates console."""
        collector = ApprovalCollector()

        assert collector.console is not None


class TestPromptDecision:
    """Tests for _prompt_decision method."""

    def test_prompt_decision_approve(self):
        """Test prompting for approve decision."""
        collector = ApprovalCollector()

        with mock.patch.object(collector.console, "input", return_value="1"):
            with mock.patch.object(collector.console, "print"):
                result = collector._prompt_decision()

                assert result == ReviewDecision.APPROVED

    def test_prompt_decision_reject(self):
        """Test prompting for reject decision."""
        collector = ApprovalCollector()

        with mock.patch.object(collector.console, "input", return_value="2"):
            with mock.patch.object(collector.console, "print"):
                result = collector._prompt_decision()

                assert result == ReviewDecision.REJECTED

    def test_prompt_decision_defer(self):
        """Test prompting for defer decision."""
        collector = ApprovalCollector()

        with mock.patch.object(collector.console, "input", return_value="3"):
            with mock.patch.object(collector.console, "print"):
                result = collector._prompt_decision()

                assert result == ReviewDecision.DEFERRED

    def test_prompt_decision_invalid_then_valid(self):
        """Test prompting with invalid input then valid."""
        collector = ApprovalCollector()

        # First return invalid, then valid
        with mock.patch.object(
            collector.console, "input", side_effect=["x", "abc", "1"]
        ):
            with mock.patch.object(collector.console, "print"):
                result = collector._prompt_decision()

                assert result == ReviewDecision.APPROVED


class TestPromptJustification:
    """Tests for _prompt_justification method."""

    def test_prompt_justification_for_approved(self):
        """Test justification prompt for approved decision."""
        collector = ApprovalCollector()

        with mock.patch.object(
            collector.console, "input", return_value="Looks good to me"
        ):
            with mock.patch.object(collector.console, "print"):
                result = collector._prompt_justification(ReviewDecision.APPROVED)

                assert result == "Looks good to me"

    def test_prompt_justification_for_rejected(self):
        """Test justification prompt for rejected decision."""
        collector = ApprovalCollector()

        with mock.patch.object(
            collector.console, "input", return_value="Missing tests"
        ):
            with mock.patch.object(collector.console, "print"):
                result = collector._prompt_justification(ReviewDecision.REJECTED)

                assert result == "Missing tests"

    def test_prompt_justification_for_deferred(self):
        """Test justification prompt for deferred decision."""
        collector = ApprovalCollector()

        with mock.patch.object(
            collector.console, "input", return_value="Need more context"
        ):
            with mock.patch.object(collector.console, "print"):
                result = collector._prompt_justification(ReviewDecision.DEFERRED)

                assert result == "Need more context"

    def test_prompt_justification_empty_then_valid(self):
        """Test justification with empty input then valid."""
        collector = ApprovalCollector()

        # First return empty, then valid
        with mock.patch.object(
            collector.console, "input", side_effect=["", "   ", "Valid reason"]
        ):
            with mock.patch.object(collector.console, "print"):
                result = collector._prompt_justification(ReviewDecision.APPROVED)

                assert result == "Valid reason"

    def test_prompt_justification_strips_whitespace(self):
        """Test justification strips whitespace."""
        collector = ApprovalCollector()

        with mock.patch.object(
            collector.console, "input", return_value="  Trimmed  "
        ):
            with mock.patch.object(collector.console, "print"):
                result = collector._prompt_justification(ReviewDecision.APPROVED)

                assert result == "Trimmed"


class TestGetReviewer:
    """Tests for _get_reviewer method."""

    def test_get_reviewer_from_git(self):
        """Test getting reviewer from git config."""
        collector = ApprovalCollector()

        mock_result = mock.MagicMock()
        mock_result.stdout = "user@example.com\n"

        with mock.patch("subprocess.run", return_value=mock_result):
            result = collector._get_reviewer()

            assert result == "user@example.com"

    def test_get_reviewer_git_empty(self):
        """Test fallback when git email is empty."""
        collector = ApprovalCollector()

        mock_result = mock.MagicMock()
        mock_result.stdout = ""

        with mock.patch("subprocess.run", return_value=mock_result):
            with mock.patch("getpass.getuser", return_value="testuser"):
                result = collector._get_reviewer()

                assert result == "testuser@local"

    def test_get_reviewer_git_error(self):
        """Test fallback when git command fails."""
        collector = ApprovalCollector()

        with mock.patch(
            "subprocess.run", side_effect=subprocess.CalledProcessError(1, "git")
        ):
            with mock.patch("getpass.getuser", return_value="localuser"):
                result = collector._get_reviewer()

                assert result == "localuser@local"


class TestCollectDecision:
    """Tests for collect_decision method."""

    def test_collect_decision_approved(self):
        """Test collecting approved decision."""
        collector = ApprovalCollector()

        mock_git_result = mock.MagicMock()
        mock_git_result.stdout = "reviewer@test.com\n"

        with mock.patch.object(collector.console, "rule"):
            with mock.patch.object(collector.console, "print"):
                with mock.patch.object(
                    collector.console, "input", side_effect=["1", "LGTM"]
                ):
                    with mock.patch("subprocess.run", return_value=mock_git_result):
                        result = collector.collect_decision(task_id="TASK-001")

                        assert isinstance(result, ApprovalResponse)
                        assert result.decision == ReviewDecision.APPROVED
                        assert result.justification == "LGTM"
                        assert result.reviewer == "reviewer@test.com"
                        assert "Z" in result.timestamp

    def test_collect_decision_rejected(self):
        """Test collecting rejected decision."""
        collector = ApprovalCollector()

        mock_git_result = mock.MagicMock()
        mock_git_result.stdout = "reviewer@test.com\n"

        with mock.patch.object(collector.console, "rule"):
            with mock.patch.object(collector.console, "print"):
                with mock.patch.object(
                    collector.console, "input", side_effect=["2", "Needs work"]
                ):
                    with mock.patch("subprocess.run", return_value=mock_git_result):
                        result = collector.collect_decision()

                        assert result.decision == ReviewDecision.REJECTED
                        assert result.justification == "Needs work"

    def test_collect_decision_deferred(self):
        """Test collecting deferred decision."""
        collector = ApprovalCollector()

        mock_git_result = mock.MagicMock()
        mock_git_result.stdout = "reviewer@test.com\n"

        with mock.patch.object(collector.console, "rule"):
            with mock.patch.object(collector.console, "print"):
                with mock.patch.object(
                    collector.console, "input", side_effect=["3", "Need more info"]
                ):
                    with mock.patch("subprocess.run", return_value=mock_git_result):
                        result = collector.collect_decision()

                        assert result.decision == ReviewDecision.DEFERRED
                        assert result.justification == "Need more info"


class TestPromptViewDiff:
    """Tests for prompt_view_diff method."""

    def test_prompt_view_diff_yes(self):
        """Test prompt returns True for 'y'."""
        collector = ApprovalCollector()

        with mock.patch.object(collector.console, "input", return_value="y"):
            result = collector.prompt_view_diff()

            assert result is True

    def test_prompt_view_diff_yes_full(self):
        """Test prompt returns True for 'yes'."""
        collector = ApprovalCollector()

        with mock.patch.object(collector.console, "input", return_value="yes"):
            result = collector.prompt_view_diff()

            assert result is True

    def test_prompt_view_diff_no(self):
        """Test prompt returns False for 'n'."""
        collector = ApprovalCollector()

        with mock.patch.object(collector.console, "input", return_value="n"):
            result = collector.prompt_view_diff()

            assert result is False

    def test_prompt_view_diff_other(self):
        """Test prompt returns False for other input."""
        collector = ApprovalCollector()

        with mock.patch.object(collector.console, "input", return_value="maybe"):
            result = collector.prompt_view_diff()

            assert result is False

    def test_prompt_view_diff_case_insensitive(self):
        """Test prompt is case insensitive."""
        collector = ApprovalCollector()

        with mock.patch.object(collector.console, "input", return_value="Y"):
            result = collector.prompt_view_diff()

            assert result is True
