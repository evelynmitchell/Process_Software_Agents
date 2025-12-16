"""Tests for asp.utils.github_sync module."""

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from asp.utils.beads import (
    BeadsIssue,
    BeadsStatus,
    BeadsType,
    read_issues,
    write_issues,
)
from asp.utils.github_sync import (
    _convert_to_beads,
    _format_gh_body,
    _get_github_ref,
    _has_conflict,
    _infer_priority_from_labels,
    _infer_type_from_labels,
    _is_gh_synced,
    pull_from_github,
    push_to_github,
    sync_github,
    verify_gh_cli,
)


@pytest.fixture
def sample_beads_issue():
    """Create a sample BeadsIssue for testing."""
    return BeadsIssue(
        id="bd-abc1234",
        title="Fix authentication bug",
        description="Users are unable to log in when using SSO.",
        type=BeadsType.BUG,
        status=BeadsStatus.OPEN,
        priority=1,
        labels=["bug", "auth"],
    )


@pytest.fixture
def sample_gh_issue():
    """Create a sample GitHub issue dict for testing."""
    return {
        "number": 42,
        "title": "Add dark mode support",
        "body": "We need dark mode for better UX.",
        "labels": [{"name": "enhancement"}, {"name": "ui"}],
        "state": "OPEN",
        "assignees": [],
        "createdAt": "2025-12-16T10:00:00Z",
        "updatedAt": "2025-12-16T11:00:00Z",
    }


class TestVerifyGhCli:
    """Tests for verify_gh_cli function."""

    @patch("asp.utils.github_sync.subprocess.run")
    def test_returns_true_when_authenticated(self, mock_run):
        """Should return True when gh is authenticated."""
        mock_run.return_value = MagicMock(returncode=0)
        assert verify_gh_cli() is True

    @patch("asp.utils.github_sync.subprocess.run")
    def test_returns_false_when_not_authenticated(self, mock_run):
        """Should return False when gh auth fails."""
        mock_run.return_value = MagicMock(returncode=1)
        assert verify_gh_cli() is False

    @patch("asp.utils.github_sync.subprocess.run")
    def test_returns_false_when_gh_not_installed(self, mock_run):
        """Should return False when gh CLI is not installed."""
        mock_run.side_effect = FileNotFoundError()
        assert verify_gh_cli() is False


class TestIsGhSynced:
    """Tests for _is_gh_synced function."""

    def test_returns_true_with_gh_synced_label(self, sample_beads_issue):
        """Should return True when issue has gh-synced label."""
        sample_beads_issue.labels.append("gh-synced-42")
        assert _is_gh_synced(sample_beads_issue) is True

    def test_returns_false_without_gh_synced_label(self, sample_beads_issue):
        """Should return False when issue lacks gh-synced label."""
        assert _is_gh_synced(sample_beads_issue) is False


class TestGetGithubRef:
    """Tests for _get_github_ref function."""

    def test_extracts_gh_ref(self, sample_beads_issue):
        """Should extract gh-XX reference from labels."""
        sample_beads_issue.labels.append("gh-42")
        assert _get_github_ref(sample_beads_issue) == "gh-42"

    def test_extracts_gh_synced_ref(self, sample_beads_issue):
        """Should extract gh-synced-XX reference from labels."""
        sample_beads_issue.labels.append("gh-synced-123")
        assert _get_github_ref(sample_beads_issue) == "gh-synced-123"

    def test_returns_none_when_no_ref(self, sample_beads_issue):
        """Should return None when no GitHub reference."""
        assert _get_github_ref(sample_beads_issue) is None


class TestFormatGhBody:
    """Tests for _format_gh_body function."""

    def test_includes_description(self, sample_beads_issue):
        """Should include issue description."""
        body = _format_gh_body(sample_beads_issue)
        assert "Users are unable to log in" in body

    def test_includes_metadata(self, sample_beads_issue):
        """Should include Beads metadata."""
        body = _format_gh_body(sample_beads_issue)
        assert "bd-abc1234" in body
        assert "bug" in body
        assert "P1" in body


class TestInferTypeFromLabels:
    """Tests for _infer_type_from_labels function."""

    def test_bug_label(self):
        """Should return BUG type for bug label."""
        assert _infer_type_from_labels(["bug"]) == BeadsType.BUG

    def test_enhancement_label(self):
        """Should return FEATURE type for enhancement label."""
        assert _infer_type_from_labels(["enhancement"]) == BeadsType.FEATURE

    def test_feature_label(self):
        """Should return FEATURE type for feature label."""
        assert _infer_type_from_labels(["feature"]) == BeadsType.FEATURE

    def test_epic_label(self):
        """Should return EPIC type for epic label."""
        assert _infer_type_from_labels(["epic"]) == BeadsType.EPIC

    def test_chore_label(self):
        """Should return CHORE type for chore label."""
        assert _infer_type_from_labels(["chore"]) == BeadsType.CHORE

    def test_default_to_task(self):
        """Should default to TASK type."""
        assert _infer_type_from_labels(["unknown"]) == BeadsType.TASK


class TestInferPriorityFromLabels:
    """Tests for _infer_priority_from_labels function."""

    def test_p0_label(self):
        """Should return 0 for p0 label."""
        assert _infer_priority_from_labels(["p0"]) == 0

    def test_priority_critical(self):
        """Should return 0 for priority-critical."""
        assert _infer_priority_from_labels(["priority-critical"]) == 0

    def test_p1_label(self):
        """Should return 1 for p1 label."""
        assert _infer_priority_from_labels(["p1"]) == 1

    def test_priority_low(self):
        """Should return 3 for priority-low."""
        assert _infer_priority_from_labels(["priority-low"]) == 3

    def test_default_to_medium(self):
        """Should default to 2 (medium)."""
        assert _infer_priority_from_labels(["unknown"]) == 2


class TestConvertToBeads:
    """Tests for _convert_to_beads function."""

    def test_converts_basic_fields(self, sample_gh_issue):
        """Should convert basic GitHub issue fields."""
        result = _convert_to_beads(sample_gh_issue)

        assert result.title == "Add dark mode support"
        assert result.description == "We need dark mode for better UX."
        assert result.status == BeadsStatus.OPEN
        assert "gh-42" in result.labels

    def test_converts_closed_state(self, sample_gh_issue):
        """Should convert closed state correctly."""
        sample_gh_issue["state"] = "CLOSED"
        result = _convert_to_beads(sample_gh_issue)

        assert result.status == BeadsStatus.CLOSED

    def test_infers_type_from_labels(self, sample_gh_issue):
        """Should infer type from GitHub labels."""
        result = _convert_to_beads(sample_gh_issue)
        # Has "enhancement" label
        assert result.type == BeadsType.FEATURE


class TestHasConflict:
    """Tests for _has_conflict function."""

    def test_no_conflict_when_titles_match(self, sample_beads_issue, sample_gh_issue):
        """Should return False when titles match."""
        sample_gh_issue["title"] = sample_beads_issue.title
        assert _has_conflict(sample_beads_issue, sample_gh_issue) is False

    def test_conflict_when_titles_differ(self, sample_beads_issue, sample_gh_issue):
        """Should return True when titles differ."""
        assert _has_conflict(sample_beads_issue, sample_gh_issue) is True

    def test_strips_beads_prefix(self, sample_beads_issue, sample_gh_issue):
        """Should strip [bd-xxx] prefix when comparing."""
        sample_gh_issue["title"] = (
            f"[{sample_beads_issue.id}] {sample_beads_issue.title}"
        )
        assert _has_conflict(sample_beads_issue, sample_gh_issue) is False


class TestPushToGithub:
    """Tests for push_to_github function."""

    def test_dry_run_does_not_create(self, sample_beads_issue):
        """Dry run should not call gh CLI."""
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            write_issues([sample_beads_issue], root)

            result = push_to_github(dry_run=True, root_path=root)

            assert len(result) == 1
            assert "(dry-run)" in result[0]

    def test_skips_closed_issues(self, sample_beads_issue):
        """Should skip closed issues."""
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            sample_beads_issue.status = BeadsStatus.CLOSED
            write_issues([sample_beads_issue], root)

            result = push_to_github(dry_run=True, root_path=root)

            assert len(result) == 0

    def test_skips_already_synced(self, sample_beads_issue):
        """Should skip already synced issues."""
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            sample_beads_issue.labels.append("gh-synced-99")
            write_issues([sample_beads_issue], root)

            result = push_to_github(dry_run=True, root_path=root)

            assert len(result) == 0


class TestPullFromGithub:
    """Tests for pull_from_github function."""

    @patch("asp.utils.github_sync._fetch_github_issue")
    def test_imports_single_issue(self, mock_fetch, sample_gh_issue):
        """Should import a single GitHub issue."""
        mock_fetch.return_value = sample_gh_issue

        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)

            result = pull_from_github(issue_number=42, root_path=root)

            assert len(result) == 1
            assert result[0].title == "Add dark mode support"

            # Verify saved
            all_issues = read_issues(root)
            assert len(all_issues) == 1

    @patch("asp.utils.github_sync._fetch_github_issue")
    def test_dry_run_does_not_save(self, mock_fetch, sample_gh_issue):
        """Dry run should not save issues."""
        mock_fetch.return_value = sample_gh_issue

        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)

            result = pull_from_github(issue_number=42, dry_run=True, root_path=root)

            assert len(result) == 1
            assert "(dry-run-42)" in result[0].id

            # Verify not saved
            all_issues = read_issues(root)
            assert len(all_issues) == 0

    @patch("asp.utils.github_sync._fetch_github_issue")
    def test_skips_already_imported(self, mock_fetch, sample_gh_issue):
        """Should skip already imported issues."""
        mock_fetch.return_value = sample_gh_issue

        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)

            # Import once
            pull_from_github(issue_number=42, root_path=root)

            # Try to import again
            result = pull_from_github(issue_number=42, root_path=root)

            # Should be empty (already imported)
            assert len(result) == 0

            # Should still have just 1 issue
            all_issues = read_issues(root)
            assert len(all_issues) == 1


class TestSyncGithub:
    """Tests for sync_github function."""

    @patch("asp.utils.github_sync.pull_from_github")
    @patch("asp.utils.github_sync.push_to_github")
    def test_calls_both_directions(self, mock_push, mock_pull):
        """Should call both push and pull."""
        mock_pull.return_value = []
        mock_push.return_value = []

        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)

            stats = sync_github(dry_run=True, root_path=root)

            mock_pull.assert_called_once()
            mock_push.assert_called_once()
            assert stats["imported"] == 0
            assert stats["exported"] == 0

    @patch("asp.utils.github_sync.pull_from_github")
    @patch("asp.utils.github_sync.push_to_github")
    def test_returns_stats(
        self, mock_push, mock_pull, sample_beads_issue, sample_gh_issue
    ):
        """Should return sync statistics."""
        # Simulate importing 2 and exporting 1
        imported_issue = _convert_to_beads(sample_gh_issue)
        mock_pull.return_value = [imported_issue, imported_issue]
        mock_push.return_value = ["http://example.com/issues/1"]

        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)

            stats = sync_github(dry_run=True, root_path=root)

            assert stats["imported"] == 2
            assert stats["exported"] == 1
