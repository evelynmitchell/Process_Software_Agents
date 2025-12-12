"""
GitHub Service for repository and issue operations.

Provides GitHub integration using the `gh` CLI for the repair workflow.
Enables fetching issues, cloning repos, creating branches, and managing PRs.

Classes:
    - GitHubIssue: Parsed GitHub issue data
    - GitHubPR: Created pull request data
    - GitHubService: Service wrapping `gh` CLI operations

Part of ADR 007: GitHub CLI Integration.

Author: ASP Development Team
Date: December 11, 2025
"""

from __future__ import annotations

import json
import logging
import re
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

logger = logging.getLogger(__name__)


# =============================================================================
# Data Classes
# =============================================================================


@dataclass
class GitHubIssue:  # pylint: disable=too-many-instance-attributes
    """
    Parsed GitHub issue.

    Attributes:
        owner: Repository owner (user or organization)
        repo: Repository name
        number: Issue number
        title: Issue title
        body: Issue body/description (markdown)
        labels: List of label names
        state: Issue state (open, closed)
        url: Full URL to the issue
    """

    owner: str
    repo: str
    number: int
    title: str
    body: str
    labels: list[str] = field(default_factory=list)
    state: str = "open"
    url: str = ""


@dataclass
class GitHubPR:
    """
    Created pull request.

    Attributes:
        owner: Repository owner
        repo: Repository name
        number: PR number
        url: Full URL to the PR
        title: PR title
        branch: Source branch name
    """

    owner: str
    repo: str
    number: int
    url: str
    title: str
    branch: str


# =============================================================================
# Exceptions
# =============================================================================


class GitHubServiceError(Exception):
    """Base exception for GitHub service errors."""


class GitHubCLINotFoundError(GitHubServiceError):
    """Raised when gh CLI is not installed."""


class GitHubAuthError(GitHubServiceError):
    """Raised when gh CLI is not authenticated."""


class GitHubURLParseError(GitHubServiceError):
    """Raised when a GitHub URL cannot be parsed."""


# =============================================================================
# GitHub Service
# =============================================================================


class GitHubService:
    """
    Service for GitHub operations using `gh` CLI.

    Requires: `gh` CLI installed and authenticated (`gh auth login`)

    Example:
        >>> service = GitHubService(Path("/workspaces"))
        >>> issue = service.fetch_issue("https://github.com/owner/repo/issues/123")
        >>> print(f"Issue: {issue.title}")

    Note:
        All methods that interact with GitHub require network access
        and valid authentication.
    """

    def __init__(self, workspace_base: Path | None = None):
        """
        Initialize GitHub service.

        Args:
            workspace_base: Base directory for workspaces (optional)
        """
        self.workspace_base = workspace_base or Path.cwd()
        logger.debug(
            "GitHubService initialized with workspace_base=%s", self.workspace_base
        )

    def verify_gh_installed(self) -> bool:
        """
        Verify gh CLI is available.

        Returns:
            True if gh CLI is installed

        Raises:
            GitHubCLINotFoundError: If gh CLI is not found
        """
        try:
            result = subprocess.run(
                ["gh", "--version"],
                capture_output=True,
                text=True,
                check=False,
            )
            if result.returncode != 0:
                raise GitHubCLINotFoundError(
                    "GitHub CLI (gh) not found. Install from: https://cli.github.com/"
                )
            version = result.stdout.strip().split()[2] if result.stdout else "unknown"
            logger.debug("gh CLI version: %s", version)
            return True
        except FileNotFoundError as e:
            raise GitHubCLINotFoundError(
                "GitHub CLI (gh) not found. Install from: https://cli.github.com/"
            ) from e

    def verify_gh_authenticated(self) -> bool:
        """
        Verify gh CLI is authenticated.

        Returns:
            True if authenticated

        Raises:
            GitHubAuthError: If not authenticated
        """
        result = subprocess.run(
            ["gh", "auth", "status"],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            raise GitHubAuthError("GitHub CLI not authenticated. Run: gh auth login")
        logger.debug("gh CLI is authenticated")
        return True

    def parse_issue_url(self, url: str) -> tuple[str, str, int]:
        """
        Parse GitHub issue/PR URL into components.

        Args:
            url: Full URL like github.com/owner/repo/issues/123

        Returns:
            Tuple of (owner, repo, number)

        Raises:
            GitHubURLParseError: If URL cannot be parsed
        """
        patterns = [
            r"github\.com/([^/]+)/([^/]+)/issues/(\d+)",
            r"github\.com/([^/]+)/([^/]+)/pull/(\d+)",
        ]

        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                owner, repo, number = (
                    match.group(1),
                    match.group(2),
                    int(match.group(3)),
                )
                logger.debug(
                    "Parsed URL: owner=%s, repo=%s, number=%s", owner, repo, number
                )
                return owner, repo, number

        raise GitHubURLParseError(f"Could not parse GitHub URL: {url}")

    def fetch_issue(self, issue_url: str) -> GitHubIssue:
        """
        Fetch issue details from GitHub.

        Args:
            issue_url: Full URL like github.com/owner/repo/issues/123

        Returns:
            GitHubIssue with title, body, labels

        Raises:
            GitHubServiceError: If fetch fails
        """
        owner, repo, number = self.parse_issue_url(issue_url)

        logger.info("Fetching issue %s/%s#%s", owner, repo, number)

        try:
            result = subprocess.run(
                [
                    "gh",
                    "issue",
                    "view",
                    str(number),
                    "--repo",
                    f"{owner}/{repo}",
                    "--json",
                    "title,body,labels,state,url",
                ],
                capture_output=True,
                text=True,
                check=True,
            )
        except subprocess.CalledProcessError as e:
            raise GitHubServiceError(
                f"Failed to fetch issue {owner}/{repo}#{number}: {e.stderr}"  # not logging stderr to avoid leaking secrets
            ) from e

        data = json.loads(result.stdout)

        issue = GitHubIssue(
            owner=owner,
            repo=repo,
            number=number,
            title=data.get("title", ""),
            body=data.get("body", "") or "",
            labels=[label["name"] for label in data.get("labels", [])],
            state=data.get("state", "open"),
            url=data.get("url", issue_url),
        )

        logger.info("Fetched issue #%s: %s", number, issue.title)
        return issue

    def clone_repo(
        self,
        owner: str,
        repo: str,
        target_path: Path,
        branch: str | None = None,
    ) -> Path:
        """
        Clone repository to target path.

        Args:
            owner: Repository owner
            repo: Repository name
            target_path: Directory to clone into
            branch: Optional branch to checkout

        Returns:
            Path to cloned repository

        Raises:
            GitHubServiceError: If clone fails
        """
        logger.info("Cloning %s/%s to %s", owner, repo, target_path)

        cmd = [
            "gh",
            "repo",
            "clone",
            f"{owner}/{repo}",
            str(target_path),
        ]

        if branch:
            cmd.extend(["--", "--branch", branch])

        try:
            subprocess.run(cmd, check=True, capture_output=True, text=True)
        except subprocess.CalledProcessError as e:
            raise GitHubServiceError(
                f"Failed to clone {owner}/{repo}: {e.stderr}"  # not logging stderr to avoid leaking secrets
            ) from e

        logger.info("Cloned %s/%s to %s", owner, repo, target_path)
        return target_path

    def create_branch(
        self,
        repo_path: Path,
        branch_name: str,
    ) -> None:
        """
        Create and checkout a new branch.

        Args:
            repo_path: Path to the repository
            branch_name: Name of the new branch

        Raises:
            GitHubServiceError: If branch creation fails
        """
        logger.info("Creating branch %s in %s", branch_name, repo_path)

        try:
            subprocess.run(
                ["git", "checkout", "-b", branch_name],
                cwd=repo_path,
                check=True,
                capture_output=True,
                text=True,
            )
        except subprocess.CalledProcessError as e:
            raise GitHubServiceError(
                f"Failed to create branch {branch_name}: {e.stderr}"  # not logging stderr to avoid leaking secrets
            ) from e

        logger.info("Created and checked out branch %s", branch_name)

    def commit_changes(
        self,
        repo_path: Path,
        message: str,
    ) -> str:
        """
        Stage and commit all changes.

        Args:
            repo_path: Path to the repository
            message: Commit message

        Returns:
            Commit SHA

        Raises:
            GitHubServiceError: If commit fails
        """
        logger.info("Committing changes in %s", repo_path)

        # Stage all changes
        try:
            subprocess.run(
                ["git", "add", "-A"],
                cwd=repo_path,
                check=True,
                capture_output=True,
                text=True,
            )
        except subprocess.CalledProcessError as e:
            raise GitHubServiceError(  # not logging stderr to avoid leaking secrets
                f"Failed to stage changes: {e.stderr}"
            ) from e

        # Commit
        try:
            subprocess.run(
                ["git", "commit", "-m", message],
                cwd=repo_path,
                check=True,
                capture_output=True,
                text=True,
            )
        except subprocess.CalledProcessError as e:
            # Check if there's nothing to commit
            if "nothing to commit" in e.stdout or "nothing to commit" in e.stderr:
                logger.warning("Nothing to commit")
                raise GitHubServiceError("Nothing to commit") from e
            raise GitHubServiceError(  # not logging stderr to avoid leaking secrets
                f"Failed to commit: {e.stderr}"
            ) from e

        # Get commit SHA
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=repo_path,
            capture_output=True,
            text=True,
            check=True,
        )

        commit_sha = result.stdout.strip()
        logger.info("Committed changes: %s", commit_sha[:8])
        return commit_sha

    def get_current_branch(self, repo_path: Path) -> str:
        """
        Get the current branch name.

        Args:
            repo_path: Path to the repository

        Returns:
            Current branch name
        """
        result = subprocess.run(
            ["git", "branch", "--show-current"],
            cwd=repo_path,
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout.strip()

    def get_remote_info(self, repo_path: Path) -> tuple[str, str]:
        """
        Get owner and repo from git remote.

        Args:
            repo_path: Path to the repository

        Returns:
            Tuple of (owner, repo)
        """
        result = subprocess.run(
            ["git", "remote", "get-url", "origin"],
            cwd=repo_path,
            capture_output=True,
            text=True,
            check=True,
        )

        remote_url = result.stdout.strip()

        # Parse owner/repo from remote URL
        # Handles: git@github.com:owner/repo.git or https://github.com/owner/repo.git
        patterns = [
            r"github\.com[:/]([^/]+)/([^/]+?)(?:\.git)?$",
        ]

        for pattern in patterns:
            match = re.search(pattern, remote_url)
            if match:
                return match.group(1), match.group(2)

        raise GitHubServiceError(  # not logging stderr to avoid leaking secrets
            f"Could not parse remote URL: {remote_url}"
        )

    def push_branch(
        self,
        repo_path: Path,
        branch: str,
        force: bool = False,
    ) -> None:
        """
        Push branch to origin.

        Args:
            repo_path: Path to the repository
            branch: Branch name to push
            force: Force push (default: False)

        Raises:
            GitHubServiceError: If push fails
        """
        logger.info("Pushing branch %s from %s", branch, repo_path)

        cmd = ["git", "push", "-u", "origin", branch]
        if force:
            cmd.insert(2, "--force")

        try:
            subprocess.run(
                cmd,
                cwd=repo_path,
                check=True,
                capture_output=True,
                text=True,
            )
        except subprocess.CalledProcessError as e:
            raise GitHubServiceError(
                f"Failed to push branch {branch}: {e.stderr}"  # not logging stderr to avoid leaking secrets
            ) from e

        logger.info("Pushed branch %s to origin", branch)

    def create_pr(
        self,
        repo_path: Path,
        title: str,
        body: str,
        base_branch: str = "main",
        draft: bool = False,
    ) -> GitHubPR:
        """
        Create a pull request.

        Args:
            repo_path: Path to repository with committed changes
            title: PR title
            body: PR description (markdown)
            base_branch: Target branch (default: main)
            draft: Create as draft PR (default: False)

        Returns:
            GitHubPR with URL and number

        Raises:
            GitHubServiceError: If PR creation fails
        """
        logger.info("Creating PR: %s", title)

        cmd = [
            "gh",
            "pr",
            "create",
            "--title",
            title,
            "--body",
            body,
            "--base",
            base_branch,
        ]

        if draft:
            cmd.append("--draft")

        try:
            result = subprocess.run(
                cmd,
                cwd=repo_path,
                capture_output=True,
                text=True,
                check=True,
            )
        except subprocess.CalledProcessError as e:
            raise GitHubServiceError(
                f"Failed to create PR: {e.stderr}"  # not logging stderr to avoid leaking secrets
            ) from e

        # Parse URL from output (gh pr create outputs the URL)
        pr_url = result.stdout.strip()

        # Get PR details via JSON
        try:
            pr_info = subprocess.run(
                ["gh", "pr", "view", "--json", "number,url"],
                cwd=repo_path,
                capture_output=True,
                text=True,
                check=True,
            )
            pr_data = json.loads(pr_info.stdout)
        except (subprocess.CalledProcessError, json.JSONDecodeError):
            # Fallback: extract number from URL
            match = re.search(r"/pull/(\d+)", pr_url)
            pr_number = int(match.group(1)) if match else 0
            pr_data = {"number": pr_number, "url": pr_url}

        owner, repo = self.get_remote_info(repo_path)
        current_branch = self.get_current_branch(repo_path)

        pr = GitHubPR(
            owner=owner,
            repo=repo,
            number=pr_data["number"],
            url=pr_data.get("url", pr_url),
            title=title,
            branch=current_branch,
        )

        logger.info("Created PR #%s: %s", pr.number, pr.url)
        return pr

    def format_pr_body(
        self,
        issue: GitHubIssue,
        changes_summary: str = "See diff for details.",
        tests_run: int = 0,
        tests_passed: int = 0,
        coverage: float = 0.0,
        iterations: int = 1,
        confidence: float = 0.0,
        diagnostic_summary: str = "N/A",
    ) -> str:
        """
        Format PR body using the template.

        Args:
            issue: The GitHub issue being fixed
            changes_summary: Description of changes made
            tests_run: Number of tests executed
            tests_passed: Number of tests that passed
            coverage: Code coverage percentage
            iterations: Number of repair iterations
            confidence: Confidence score (0.0 to 1.0)
            diagnostic_summary: Summary of diagnostic findings

        Returns:
            Formatted PR body string
        """
        from services.github_service import PR_BODY_TEMPLATE

        return PR_BODY_TEMPLATE.format(
            issue_number=issue.number,
            issue_title=issue.title,
            changes_summary=changes_summary,
            tests_run=tests_run,
            tests_passed=tests_passed,
            coverage=coverage,
            iterations=iterations,
            confidence=confidence,
            diagnostic_summary=diagnostic_summary,
        )


# =============================================================================
# Helper Functions
# =============================================================================


# =============================================================================
# PR Body Template
# =============================================================================

PR_BODY_TEMPLATE = """## Summary

Automated fix for #{issue_number}: {issue_title}

## Changes Made

{changes_summary}

## Test Results

- **Tests Run:** {tests_run}
- **Tests Passed:** {tests_passed}
- **Coverage:** {coverage}%

## Repair Process

- **Iterations:** {iterations}
- **Confidence:** {confidence:.0%}
- **Diagnostic:** {diagnostic_summary}

---

*This PR was generated by [ASP Repair Workflow](https://github.com/evelynmitchell/Process_Software_Agents)*

Fixes #{issue_number}
"""


def generate_branch_name(issue: GitHubIssue) -> str:
    """
    Generate branch name from issue.

    Format: fix/issue-{number}-{slug}
    Example: fix/issue-123-null-pointer-exception

    Args:
        issue: GitHubIssue to generate branch name for

    Returns:
        Branch name string
    """
    # Create slug from title
    slug = issue.title.lower()
    slug = re.sub(r"[^a-z0-9]+", "-", slug)
    slug = slug.strip("-")[:30]  # Limit length

    return f"fix/issue-{issue.number}-{slug}"
