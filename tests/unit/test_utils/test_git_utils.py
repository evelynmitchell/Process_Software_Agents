"""
Unit tests for git integration utilities.

Tests git operations for artifact persistence including:
- Git repository detection
- Git status checking
- File staging (git add)
- Committing changes
- Commit message formatting
- Error handling
"""

import subprocess
import tempfile
from pathlib import Path

import pytest

from asp.utils.git_utils import (
    GitError,
    get_current_branch,
    get_git_root,
    git_add_files,
    git_commit,
    git_commit_artifact,
    git_status_check,
    is_git_repository,
)


@pytest.fixture
def git_repo(tmp_path):
    """Create a temporary git repository for testing."""
    repo_dir = tmp_path / "test_repo"
    repo_dir.mkdir()

    # Initialize git repo
    subprocess.run(["git", "init"], cwd=repo_dir, check=True, capture_output=True)
    subprocess.run(
        ["git", "config", "user.name", "Test User"],
        cwd=repo_dir,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"],
        cwd=repo_dir,
        check=True,
        capture_output=True,
    )
    # Disable commit signing for test repo
    subprocess.run(
        ["git", "config", "commit.gpgsign", "false"],
        cwd=repo_dir,
        check=True,
        capture_output=True,
    )

    # Create initial commit so we have a valid HEAD
    readme = repo_dir / "README.md"
    readme.write_text("# Test Repo")
    subprocess.run(["git", "add", "README.md"], cwd=repo_dir, check=True, capture_output=True)
    subprocess.run(
        ["git", "commit", "-m", "Initial commit"],
        cwd=repo_dir,
        check=True,
        capture_output=True,
    )

    return repo_dir


@pytest.fixture
def non_git_dir(tmp_path):
    """Create a temporary directory that is NOT a git repository."""
    non_git = tmp_path / "non_git"
    non_git.mkdir()
    return non_git


class TestIsGitRepository:
    """Test git repository detection."""

    def test_returns_true_for_git_repo(self, git_repo):
        """Test returns True when in a git repository."""
        # Change to git repo directory
        import os

        original_cwd = os.getcwd()
        try:
            os.chdir(git_repo)
            assert is_git_repository() is True
        finally:
            os.chdir(original_cwd)

    def test_returns_false_for_non_git_dir(self, non_git_dir):
        """Test returns False when not in a git repository."""
        import os

        original_cwd = os.getcwd()
        try:
            os.chdir(non_git_dir)
            assert is_git_repository() is False
        finally:
            os.chdir(original_cwd)

    def test_returns_true_in_subdirectory(self, git_repo):
        """Test returns True when in a subdirectory of a git repo."""
        import os

        # Create subdirectory
        subdir = git_repo / "subdir"
        subdir.mkdir()

        original_cwd = os.getcwd()
        try:
            os.chdir(subdir)
            assert is_git_repository() is True
        finally:
            os.chdir(original_cwd)


class TestGetGitRoot:
    """Test getting git repository root."""

    def test_returns_git_root(self, git_repo):
        """Test returns the git repository root directory."""
        import os

        original_cwd = os.getcwd()
        try:
            os.chdir(git_repo)
            root = get_git_root()
            assert root == git_repo
        finally:
            os.chdir(original_cwd)

    def test_returns_root_from_subdirectory(self, git_repo):
        """Test returns root when called from subdirectory."""
        import os

        # Create subdirectory
        subdir = git_repo / "subdir" / "nested"
        subdir.mkdir(parents=True)

        original_cwd = os.getcwd()
        try:
            os.chdir(subdir)
            root = get_git_root()
            assert root == git_repo
        finally:
            os.chdir(original_cwd)

    def test_raises_error_if_not_git_repo(self, non_git_dir):
        """Test raises GitError if not in a git repository."""
        import os

        original_cwd = os.getcwd()
        try:
            os.chdir(non_git_dir)
            with pytest.raises(GitError, match="Not a git repository"):
                get_git_root()
        finally:
            os.chdir(original_cwd)


class TestGetCurrentBranch:
    """Test getting current git branch."""

    def test_returns_branch_name(self, git_repo):
        """Test returns the current branch name."""
        import os

        original_cwd = os.getcwd()
        try:
            os.chdir(git_repo)
            branch = get_current_branch()
            # Default branch is usually 'master' or 'main'
            assert branch in ["master", "main"]
        finally:
            os.chdir(original_cwd)

    def test_raises_error_if_not_git_repo(self, non_git_dir):
        """Test raises GitError if not in a git repository."""
        import os

        original_cwd = os.getcwd()
        try:
            os.chdir(non_git_dir)
            with pytest.raises(GitError):
                get_current_branch()
        finally:
            os.chdir(original_cwd)


class TestGitStatusCheck:
    """Test git status checking."""

    def test_returns_clean_for_clean_repo(self, git_repo):
        """Test returns clean status for a clean repository."""
        import os

        original_cwd = os.getcwd()
        try:
            os.chdir(git_repo)
            status = git_status_check()
            assert status["is_clean"] is True
            assert status["untracked_files"] == []
            assert status["modified_files"] == []
        finally:
            os.chdir(original_cwd)

    def test_detects_untracked_files(self, git_repo):
        """Test detects untracked files."""
        import os

        # Create untracked file
        new_file = git_repo / "untracked.txt"
        new_file.write_text("New file")

        original_cwd = os.getcwd()
        try:
            os.chdir(git_repo)
            status = git_status_check()
            assert status["is_clean"] is False
            assert "untracked.txt" in status["untracked_files"]
        finally:
            os.chdir(original_cwd)

    def test_detects_modified_files(self, git_repo):
        """Test detects modified files."""
        import os

        # Modify existing file
        readme = git_repo / "README.md"
        readme.write_text("# Modified")

        original_cwd = os.getcwd()
        try:
            os.chdir(git_repo)
            status = git_status_check()
            assert status["is_clean"] is False
            assert "README.md" in status["modified_files"]
        finally:
            os.chdir(original_cwd)


class TestGitAddFiles:
    """Test git add functionality."""

    def test_stages_single_file(self, git_repo):
        """Test staging a single file."""
        import os

        # Create new file
        new_file = git_repo / "new.txt"
        new_file.write_text("Content")

        original_cwd = os.getcwd()
        try:
            os.chdir(git_repo)

            # Add file
            git_add_files([str(new_file)])

            # Verify file is staged
            result = subprocess.run(
                ["git", "status", "--porcelain"],
                capture_output=True,
                text=True,
                check=True,
            )
            assert "A  new.txt" in result.stdout or "A new.txt" in result.stdout
        finally:
            os.chdir(original_cwd)

    def test_stages_multiple_files(self, git_repo):
        """Test staging multiple files."""
        import os

        # Create multiple files
        file1 = git_repo / "file1.txt"
        file2 = git_repo / "file2.txt"
        file1.write_text("Content 1")
        file2.write_text("Content 2")

        original_cwd = os.getcwd()
        try:
            os.chdir(git_repo)

            # Add both files
            git_add_files([str(file1), str(file2)])

            # Verify both files are staged
            result = subprocess.run(
                ["git", "status", "--porcelain"],
                capture_output=True,
                text=True,
                check=True,
            )
            assert "file1.txt" in result.stdout
            assert "file2.txt" in result.stdout
        finally:
            os.chdir(original_cwd)

    def test_raises_error_if_file_not_found(self, git_repo):
        """Test raises error if file doesn't exist."""
        import os

        original_cwd = os.getcwd()
        try:
            os.chdir(git_repo)
            with pytest.raises(GitError):
                git_add_files(["nonexistent.txt"])
        finally:
            os.chdir(original_cwd)


class TestGitCommit:
    """Test git commit functionality."""

    def test_creates_commit(self, git_repo):
        """Test creates a commit with message."""
        import os

        # Create and stage a file
        new_file = git_repo / "test.txt"
        new_file.write_text("Test content")

        original_cwd = os.getcwd()
        try:
            os.chdir(git_repo)

            # Stage file
            subprocess.run(["git", "add", "test.txt"], check=True, capture_output=True)

            # Commit
            commit_hash = git_commit("Test commit message")

            # Verify commit exists
            assert commit_hash is not None
            assert len(commit_hash) > 0

            # Verify commit message
            result = subprocess.run(
                ["git", "log", "-1", "--pretty=%s"],
                capture_output=True,
                text=True,
                check=True,
            )
            assert "Test commit message" in result.stdout
        finally:
            os.chdir(original_cwd)

    def test_supports_multiline_commit_message(self, git_repo):
        """Test supports multiline commit messages."""
        import os

        # Create and stage a file
        new_file = git_repo / "test.txt"
        new_file.write_text("Test content")

        original_cwd = os.getcwd()
        try:
            os.chdir(git_repo)

            # Stage file
            subprocess.run(["git", "add", "test.txt"], check=True, capture_output=True)

            # Commit with multiline message
            message = "First line\n\nSecond paragraph\nThird line"
            git_commit(message)

            # Verify commit message
            result = subprocess.run(
                ["git", "log", "-1", "--pretty=%B"],
                capture_output=True,
                text=True,
                check=True,
            )
            assert "First line" in result.stdout
            assert "Second paragraph" in result.stdout
            assert "Third line" in result.stdout
        finally:
            os.chdir(original_cwd)

    def test_raises_error_if_nothing_to_commit(self, git_repo):
        """Test raises error if nothing is staged."""
        import os

        original_cwd = os.getcwd()
        try:
            os.chdir(git_repo)
            with pytest.raises(GitError, match="nothing to commit"):
                git_commit("Empty commit")
        finally:
            os.chdir(original_cwd)


class TestGitCommitArtifact:
    """Test artifact commit helper."""

    def test_commits_artifact_files(self, git_repo):
        """Test commits artifact files with standardized message."""
        import os

        # Create artifact files
        artifacts_dir = git_repo / "artifacts" / "TASK-001"
        artifacts_dir.mkdir(parents=True)
        plan_json = artifacts_dir / "plan.json"
        plan_md = artifacts_dir / "plan.md"
        plan_json.write_text("{}")
        plan_md.write_text("# Plan")

        original_cwd = os.getcwd()
        try:
            os.chdir(git_repo)

            # Commit artifacts
            commit_hash = git_commit_artifact(
                task_id="TASK-001",
                agent_name="Planning Agent",
                artifact_files=[str(plan_json), str(plan_md)],
            )

            # Verify commit exists
            assert commit_hash is not None
            assert len(commit_hash) > 0

            # Verify commit message format
            result = subprocess.run(
                ["git", "log", "-1", "--pretty=%s"],
                capture_output=True,
                text=True,
                check=True,
            )
            assert "Planning Agent" in result.stdout
            assert "TASK-001" in result.stdout
        finally:
            os.chdir(original_cwd)

    def test_includes_file_list_in_commit_message(self, git_repo):
        """Test includes artifact file list in commit message."""
        import os

        # Create artifact files
        artifacts_dir = git_repo / "artifacts" / "TASK-002"
        artifacts_dir.mkdir(parents=True)
        files = [
            artifacts_dir / "plan.json",
            artifacts_dir / "plan.md",
        ]
        for f in files:
            f.write_text("content")

        original_cwd = os.getcwd()
        try:
            os.chdir(git_repo)

            # Commit artifacts
            git_commit_artifact(
                task_id="TASK-002",
                agent_name="Planning Agent",
                artifact_files=[str(f) for f in files],
            )

            # Verify commit message includes file count
            result = subprocess.run(
                ["git", "log", "-1", "--pretty=%B"],
                capture_output=True,
                text=True,
                check=True,
            )
            # Message should mention the files
            commit_body = result.stdout
            assert "plan.json" in commit_body or "2 file" in commit_body
        finally:
            os.chdir(original_cwd)

    def test_raises_error_if_not_git_repo(self, non_git_dir):
        """Test raises error if not in git repository."""
        import os

        original_cwd = os.getcwd()
        try:
            os.chdir(non_git_dir)
            with pytest.raises(GitError):
                git_commit_artifact(
                    task_id="TASK-003",
                    agent_name="Test Agent",
                    artifact_files=["file.txt"],
                )
        finally:
            os.chdir(original_cwd)
