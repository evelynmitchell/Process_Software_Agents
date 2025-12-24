"""
Unit tests for GitHubService.

Tests GitHub CLI integration using mocked subprocess calls.
No actual GitHub API calls are made in these tests.

Author: ASP Development Team
Date: December 11, 2025
"""

import json
import subprocess
from unittest.mock import MagicMock, patch

import pytest

from services.github_service import (
    PR_BODY_TEMPLATE,
    GitHubAuthError,
    GitHubCLINotFoundError,
    GitHubIssue,
    GitHubPR,
    GitHubService,
    GitHubServiceError,
    GitHubURLParseError,
    generate_branch_name,
)

# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def github_service(tmp_path):
    """Create a GitHubService instance for testing."""
    return GitHubService(workspace_base=tmp_path)


@pytest.fixture
def sample_issue():
    """Create a sample GitHubIssue for testing."""
    return GitHubIssue(
        owner="testowner",
        repo="testrepo",
        number=123,
        title="Fix null pointer exception in parser",
        body="The parser crashes when input is None.\n\nSteps to reproduce:\n1. Call parse(None)",
        labels=["bug", "high-priority"],
        state="open",
        url="https://github.com/testowner/testrepo/issues/123",
    )


# =============================================================================
# URL Parsing Tests
# =============================================================================


class TestParseIssueURL:
    """Tests for parse_issue_url method."""

    def test_parse_issue_url_https(self, github_service):
        """Test parsing standard HTTPS issue URL."""
        url = "https://github.com/owner/repo/issues/123"
        owner, repo, number = github_service.parse_issue_url(url)

        assert owner == "owner"
        assert repo == "repo"
        assert number == 123

    def test_parse_issue_url_without_https(self, github_service):
        """Test parsing URL without https prefix."""
        url = "github.com/owner/repo/issues/456"
        owner, repo, number = github_service.parse_issue_url(url)

        assert owner == "owner"
        assert repo == "repo"
        assert number == 456

    def test_parse_pull_request_url(self, github_service):
        """Test parsing PR URL (same format as issue)."""
        url = "https://github.com/owner/repo/pull/789"
        owner, repo, number = github_service.parse_issue_url(url)

        assert owner == "owner"
        assert repo == "repo"
        assert number == 789

    def test_parse_url_with_org(self, github_service):
        """Test parsing URL with organization owner."""
        url = "https://github.com/my-organization/my-repo/issues/42"
        owner, repo, number = github_service.parse_issue_url(url)

        assert owner == "my-organization"
        assert repo == "my-repo"
        assert number == 42

    def test_parse_invalid_url_raises_error(self, github_service):
        """Test that invalid URLs raise GitHubURLParseError."""
        invalid_urls = [
            "https://gitlab.com/owner/repo/issues/123",
            "https://github.com/owner/repo",
            "https://github.com/owner/repo/tree/main",
            "not-a-url",
            "",
        ]

        for url in invalid_urls:
            with pytest.raises(GitHubURLParseError):
                github_service.parse_issue_url(url)


# =============================================================================
# gh CLI Verification Tests
# =============================================================================


class TestVerifyGhInstalled:
    """Tests for verify_gh_installed method."""

    @patch("subprocess.run")
    def test_gh_installed_success(self, mock_run, github_service):
        """Test successful gh verification."""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="gh version 2.40.0",
        )

        result = github_service.verify_gh_installed()

        assert result is True
        mock_run.assert_called_once()

    @patch("subprocess.run")
    def test_gh_not_installed_returncode(self, mock_run, github_service):
        """Test gh not installed (non-zero return code)."""
        mock_run.return_value = MagicMock(returncode=1)

        with pytest.raises(GitHubCLINotFoundError):
            github_service.verify_gh_installed()

    @patch("subprocess.run")
    def test_gh_not_installed_file_not_found(self, mock_run, github_service):
        """Test gh not installed (FileNotFoundError)."""
        mock_run.side_effect = FileNotFoundError()

        with pytest.raises(GitHubCLINotFoundError):
            github_service.verify_gh_installed()


class TestVerifyGhAuthenticated:
    """Tests for verify_gh_authenticated method."""

    @patch("subprocess.run")
    def test_gh_authenticated_success(self, mock_run, github_service):
        """Test successful authentication check."""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="Logged in to github.com as username",
        )

        result = github_service.verify_gh_authenticated()

        assert result is True

    @patch("subprocess.run")
    def test_gh_not_authenticated(self, mock_run, github_service):
        """Test authentication failure."""
        mock_run.return_value = MagicMock(
            returncode=1,
            stderr="You are not logged into any GitHub hosts",
        )

        with pytest.raises(GitHubAuthError):
            github_service.verify_gh_authenticated()


# =============================================================================
# Fetch Issue Tests
# =============================================================================


class TestFetchIssue:
    """Tests for fetch_issue method."""

    @patch("subprocess.run")
    def test_fetch_issue_success(self, mock_run, github_service):
        """Test successful issue fetch."""
        mock_response = {
            "title": "Bug in parser",
            "body": "Description of the bug",
            "labels": [{"name": "bug"}, {"name": "help wanted"}],
            "state": "open",
            "url": "https://github.com/owner/repo/issues/123",
        }

        mock_run.return_value = MagicMock(
            returncode=0,
            stdout=json.dumps(mock_response),
        )

        issue = github_service.fetch_issue("https://github.com/owner/repo/issues/123")

        assert issue.owner == "owner"
        assert issue.repo == "repo"
        assert issue.number == 123
        assert issue.title == "Bug in parser"
        assert issue.body == "Description of the bug"
        assert issue.labels == ["bug", "help wanted"]
        assert issue.state == "open"

    @patch("subprocess.run")
    def test_fetch_issue_with_null_body(self, mock_run, github_service):
        """Test issue fetch when body is null."""
        mock_response = {
            "title": "Quick fix",
            "body": None,
            "labels": [],
            "state": "open",
            "url": "https://github.com/owner/repo/issues/1",
        }

        mock_run.return_value = MagicMock(
            returncode=0,
            stdout=json.dumps(mock_response),
        )

        issue = github_service.fetch_issue("https://github.com/owner/repo/issues/1")

        assert issue.body == ""  # Should be empty string, not None

    @patch("subprocess.run")
    def test_fetch_issue_failure(self, mock_run, github_service):
        """Test issue fetch failure."""
        mock_run.side_effect = subprocess.CalledProcessError(
            1, "gh", stderr="Issue not found"
        )

        with pytest.raises(GitHubServiceError, match="Failed to fetch issue"):
            github_service.fetch_issue("https://github.com/owner/repo/issues/999")


# =============================================================================
# Clone Repo Tests
# =============================================================================


class TestCloneRepo:
    """Tests for clone_repo method."""

    @patch("subprocess.run")
    def test_clone_repo_success(self, mock_run, github_service, tmp_path):
        """Test successful repo clone."""
        mock_run.return_value = MagicMock(returncode=0)
        target = tmp_path / "cloned-repo"

        result = github_service.clone_repo("owner", "repo", target)

        assert result == target
        mock_run.assert_called_once()

        # Verify the command
        call_args = mock_run.call_args
        assert "gh" in call_args[0][0]
        assert "repo" in call_args[0][0]
        assert "clone" in call_args[0][0]

    @patch("subprocess.run")
    def test_clone_repo_with_branch(self, mock_run, github_service, tmp_path):
        """Test repo clone with specific branch."""
        mock_run.return_value = MagicMock(returncode=0)
        target = tmp_path / "cloned-repo"

        github_service.clone_repo("owner", "repo", target, branch="develop")

        call_args = mock_run.call_args
        cmd = call_args[0][0]
        assert "--branch" in cmd
        assert "develop" in cmd

    @patch("subprocess.run")
    def test_clone_repo_failure(self, mock_run, github_service, tmp_path):
        """Test repo clone failure."""
        mock_run.side_effect = subprocess.CalledProcessError(
            1, "gh", stderr="Repository not found"
        )

        with pytest.raises(GitHubServiceError, match="Failed to clone"):
            github_service.clone_repo("owner", "nonexistent", tmp_path / "repo")


# =============================================================================
# Branch Operations Tests
# =============================================================================


class TestCreateBranch:
    """Tests for create_branch method."""

    @patch("subprocess.run")
    def test_create_branch_success(self, mock_run, github_service, tmp_path):
        """Test successful branch creation."""
        mock_run.return_value = MagicMock(returncode=0)

        github_service.create_branch(tmp_path, "fix/issue-123")

        mock_run.assert_called_once()
        call_args = mock_run.call_args
        cmd = call_args[0][0]
        assert "git" in cmd
        assert "checkout" in cmd
        assert "-b" in cmd
        assert "fix/issue-123" in cmd

    @patch("subprocess.run")
    def test_create_branch_failure(self, mock_run, github_service, tmp_path):
        """Test branch creation failure."""
        mock_run.side_effect = subprocess.CalledProcessError(
            1, "git", stderr="branch already exists"
        )

        with pytest.raises(GitHubServiceError, match="Failed to create branch"):
            github_service.create_branch(tmp_path, "existing-branch")


class TestCommitChanges:
    """Tests for commit_changes method."""

    @patch("subprocess.run")
    def test_commit_changes_success(self, mock_run, github_service, tmp_path):
        """Test successful commit."""
        # Mock git add, git commit, and git rev-parse
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="abc123def456",
        )

        sha = github_service.commit_changes(tmp_path, "Fix bug")

        assert sha == "abc123def456"
        assert mock_run.call_count == 3  # add, commit, rev-parse

    @patch("subprocess.run")
    def test_commit_nothing_to_commit(self, mock_run, github_service, tmp_path):
        """Test commit when there's nothing to commit."""
        # First call (git add) succeeds
        # Second call (git commit) fails with "nothing to commit"
        error = subprocess.CalledProcessError(1, "git")
        error.stdout = "nothing to commit"
        error.stderr = ""
        mock_run.side_effect = [
            MagicMock(returncode=0),
            error,
        ]

        with pytest.raises(GitHubServiceError, match="Nothing to commit"):
            github_service.commit_changes(tmp_path, "Empty commit")


# =============================================================================
# Helper Function Tests
# =============================================================================


class TestGenerateBranchName:
    """Tests for generate_branch_name helper."""

    def test_generate_basic_branch_name(self, sample_issue):
        """Test basic branch name generation."""
        branch = generate_branch_name(sample_issue)

        assert branch.startswith("fix/issue-123-")
        assert "null-pointer" in branch or "fix-null" in branch

    def test_generate_branch_name_special_chars(self):
        """Test branch name with special characters in title."""
        issue = GitHubIssue(
            owner="owner",
            repo="repo",
            number=456,
            title="Fix: API error (500) when !@#$% input",
            body="",
        )

        branch = generate_branch_name(issue)

        # Should not contain special characters
        assert branch.startswith("fix/issue-456-")
        assert "!" not in branch
        assert "@" not in branch
        assert "#" not in branch

    def test_generate_branch_name_long_title(self):
        """Test branch name truncation for long titles."""
        issue = GitHubIssue(
            owner="owner",
            repo="repo",
            number=789,
            title="This is a very long issue title that should be truncated to avoid overly long branch names",
            body="",
        )

        branch = generate_branch_name(issue)

        # Should be truncated
        assert len(branch) <= 50  # "fix/issue-789-" (14) + 30 chars max


# =============================================================================
# Get Remote Info Tests
# =============================================================================


class TestGetRemoteInfo:
    """Tests for get_remote_info method."""

    @patch("subprocess.run")
    def test_get_remote_https_url(self, mock_run, github_service, tmp_path):
        """Test parsing HTTPS remote URL."""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="https://github.com/owner/repo.git\n",
        )

        owner, repo = github_service.get_remote_info(tmp_path)

        assert owner == "owner"
        assert repo == "repo"

    @patch("subprocess.run")
    def test_get_remote_ssh_url(self, mock_run, github_service, tmp_path):
        """Test parsing SSH remote URL."""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="git@github.com:owner/repo.git\n",
        )

        owner, repo = github_service.get_remote_info(tmp_path)

        assert owner == "owner"
        assert repo == "repo"

    @patch("subprocess.run")
    def test_get_remote_without_git_extension(self, mock_run, github_service, tmp_path):
        """Test parsing remote URL without .git extension."""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="https://github.com/owner/repo\n",
        )

        owner, repo = github_service.get_remote_info(tmp_path)

        assert owner == "owner"
        assert repo == "repo"


# =============================================================================
# Data Class Tests
# =============================================================================


class TestGitHubIssue:
    """Tests for GitHubIssue dataclass."""

    def test_issue_creation_minimal(self):
        """Test creating issue with minimal fields."""
        issue = GitHubIssue(
            owner="owner",
            repo="repo",
            number=1,
            title="Title",
            body="Body",
        )

        assert issue.labels == []
        assert issue.state == "open"
        assert issue.url == ""

    def test_issue_creation_full(self, sample_issue):
        """Test creating issue with all fields."""
        assert sample_issue.owner == "testowner"
        assert sample_issue.repo == "testrepo"
        assert sample_issue.number == 123
        assert sample_issue.title == "Fix null pointer exception in parser"
        assert "bug" in sample_issue.labels


class TestGitHubPR:
    """Tests for GitHubPR dataclass."""

    def test_pr_creation(self):
        """Test creating PR dataclass."""
        pr = GitHubPR(
            owner="owner",
            repo="repo",
            number=456,
            url="https://github.com/owner/repo/pull/456",
            title="Fix issue #123",
            branch="fix/issue-123",
        )

        assert pr.owner == "owner"
        assert pr.number == 456
        assert pr.branch == "fix/issue-123"


# =============================================================================
# Push Branch Tests
# =============================================================================


class TestPushBranch:
    """Tests for push_branch method."""

    @patch("subprocess.run")
    def test_push_branch_success(self, mock_run, github_service, tmp_path):
        """Test successful branch push."""
        mock_run.return_value = MagicMock(returncode=0)

        github_service.push_branch(tmp_path, "fix/issue-123")

        mock_run.assert_called_once()
        call_args = mock_run.call_args
        cmd = call_args[0][0]
        assert "git" in cmd
        assert "push" in cmd
        assert "-u" in cmd
        assert "origin" in cmd
        assert "fix/issue-123" in cmd

    @patch("subprocess.run")
    def test_push_branch_force(self, mock_run, github_service, tmp_path):
        """Test force push."""
        mock_run.return_value = MagicMock(returncode=0)

        github_service.push_branch(tmp_path, "fix/issue-123", force=True)

        call_args = mock_run.call_args
        cmd = call_args[0][0]
        assert "--force" in cmd

    @patch("subprocess.run")
    def test_push_branch_failure(self, mock_run, github_service, tmp_path):
        """Test push failure."""
        mock_run.side_effect = subprocess.CalledProcessError(
            1, "git", stderr="Permission denied"
        )

        with pytest.raises(GitHubServiceError, match="Failed to push branch"):
            github_service.push_branch(tmp_path, "fix/issue-123")


# =============================================================================
# Create PR Tests
# =============================================================================


class TestCreatePR:
    """Tests for create_pr method."""

    @patch("subprocess.run")
    def test_create_pr_success(self, mock_run, github_service, tmp_path):
        """Test successful PR creation."""
        # Mock gh pr create, gh pr view, git remote get-url, git branch
        mock_run.side_effect = [
            MagicMock(
                returncode=0,
                stdout="https://github.com/owner/repo/pull/456",
            ),
            MagicMock(
                returncode=0,
                stdout=json.dumps(
                    {"number": 456, "url": "https://github.com/owner/repo/pull/456"}
                ),
            ),
            MagicMock(returncode=0, stdout="https://github.com/owner/repo.git\n"),
            MagicMock(returncode=0, stdout="fix/issue-123\n"),
        ]

        pr = github_service.create_pr(
            tmp_path,
            title="Fix issue #123",
            body="This fixes the bug",
        )

        assert pr.number == 456
        assert pr.title == "Fix issue #123"
        assert pr.owner == "owner"
        assert pr.repo == "repo"

    @patch("subprocess.run")
    def test_create_pr_draft(self, mock_run, github_service, tmp_path):
        """Test draft PR creation."""
        mock_run.side_effect = [
            MagicMock(returncode=0, stdout="https://github.com/owner/repo/pull/789"),
            MagicMock(
                returncode=0,
                stdout=json.dumps(
                    {"number": 789, "url": "https://github.com/owner/repo/pull/789"}
                ),
            ),
            MagicMock(returncode=0, stdout="https://github.com/owner/repo.git\n"),
            MagicMock(returncode=0, stdout="fix/issue-456\n"),
        ]

        github_service.create_pr(
            tmp_path,
            title="WIP: Fix issue",
            body="Work in progress",
            draft=True,
        )

        # Check the first call (gh pr create) includes --draft
        first_call = mock_run.call_args_list[0]
        cmd = first_call[0][0]
        assert "--draft" in cmd

    @patch("subprocess.run")
    def test_create_pr_custom_base(self, mock_run, github_service, tmp_path):
        """Test PR with custom base branch."""
        mock_run.side_effect = [
            MagicMock(returncode=0, stdout="https://github.com/owner/repo/pull/111"),
            MagicMock(
                returncode=0,
                stdout=json.dumps(
                    {"number": 111, "url": "https://github.com/owner/repo/pull/111"}
                ),
            ),
            MagicMock(returncode=0, stdout="https://github.com/owner/repo.git\n"),
            MagicMock(returncode=0, stdout="hotfix/urgent\n"),
        ]

        github_service.create_pr(
            tmp_path,
            title="Hotfix",
            body="Urgent fix",
            base_branch="develop",
        )

        first_call = mock_run.call_args_list[0]
        cmd = first_call[0][0]
        assert "--base" in cmd
        # Find the index of --base and check the next element
        base_idx = cmd.index("--base")
        assert cmd[base_idx + 1] == "develop"

    @patch("subprocess.run")
    def test_create_pr_failure(self, mock_run, github_service, tmp_path):
        """Test PR creation failure."""
        mock_run.side_effect = subprocess.CalledProcessError(
            1, "gh", stderr="Failed to create PR"
        )

        with pytest.raises(GitHubServiceError, match="Failed to create PR"):
            github_service.create_pr(tmp_path, title="Fix", body="Body")

    @patch("subprocess.run")
    def test_create_pr_fallback_parsing(self, mock_run, github_service, tmp_path):
        """Test PR number parsing when gh pr view fails."""
        mock_run.side_effect = [
            MagicMock(returncode=0, stdout="https://github.com/owner/repo/pull/999"),
            subprocess.CalledProcessError(1, "gh", stderr="PR view failed"),
            MagicMock(returncode=0, stdout="https://github.com/owner/repo.git\n"),
            MagicMock(returncode=0, stdout="feature-branch\n"),
        ]

        pr = github_service.create_pr(tmp_path, title="Fix", body="Body")

        assert pr.number == 999  # Parsed from URL


# =============================================================================
# Format PR Body Tests
# =============================================================================


class TestFormatPRBody:
    """Tests for format_pr_body method."""

    def test_format_pr_body_basic(self, github_service, sample_issue):
        """Test basic PR body formatting."""
        body = github_service.format_pr_body(
            issue=sample_issue,
            changes_summary="Fixed the null pointer check",
            tests_run=10,
            tests_passed=10,
            coverage=85.5,
            iterations=2,
            confidence=0.95,
            diagnostic_summary="Null check was missing",
        )

        assert "Fixes #123" in body
        assert sample_issue.title in body
        assert "Fixed the null pointer check" in body
        assert "Tests Run:** 10" in body
        assert "Tests Passed:** 10" in body
        assert "Coverage:** 85.5%" in body
        assert "Iterations:** 2" in body
        assert "Confidence:** 95%" in body

    def test_format_pr_body_defaults(self, github_service, sample_issue):
        """Test PR body with default values."""
        body = github_service.format_pr_body(issue=sample_issue)

        assert "Fixes #123" in body
        assert "See diff for details" in body
        assert "Tests Run:** 0" in body
        assert "N/A" in body


class TestPRBodyTemplate:
    """Tests for PR_BODY_TEMPLATE constant."""

    def test_template_contains_required_sections(self):
        """Test that template has all required sections."""
        assert "## Summary" in PR_BODY_TEMPLATE
        assert "## Changes Made" in PR_BODY_TEMPLATE
        assert "## Test Results" in PR_BODY_TEMPLATE
        assert "## Repair Process" in PR_BODY_TEMPLATE
        assert "Fixes #{issue_number}" in PR_BODY_TEMPLATE

    def test_template_formatting_placeholders(self):
        """Test all placeholders are present."""
        placeholders = [
            "{issue_number}",
            "{issue_title}",
            "{changes_summary}",
            "{tests_run}",
            "{tests_passed}",
            "{coverage}",
            "{iterations}",
            "{confidence:.0%}",
            "{diagnostic_summary}",
        ]

        for placeholder in placeholders:
            assert placeholder in PR_BODY_TEMPLATE, (
                f"Missing placeholder: {placeholder}"
            )
