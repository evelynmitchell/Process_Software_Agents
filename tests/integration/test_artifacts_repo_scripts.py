"""
Tests for test artifacts repository initialization and cleanup scripts.
"""

import os
import subprocess
import pytest
from pathlib import Path


@pytest.fixture
def project_root():
    """Get the project root directory."""
    # __file__ is in tests/integration/, so go up two levels to get project root
    return Path(__file__).parent.parent.parent


@pytest.fixture
def test_repo_path(project_root):
    """Get the test artifacts repository path."""
    return project_root / "test_artifacts_repo"


@pytest.fixture
def cleanup_test_repo(test_repo_path):
    """Ensure test repo is cleaned up before and after tests."""
    # Cleanup before test
    if test_repo_path.exists():
        subprocess.run(
            ["rm", "-rf", str(test_repo_path)], check=True, capture_output=True
        )

    yield

    # Cleanup after test
    if test_repo_path.exists():
        subprocess.run(
            ["rm", "-rf", str(test_repo_path)], check=True, capture_output=True
        )


class TestInitScript:
    """Test the init_test_artifacts_repo.sh script."""

    def test_init_script_exists(self, project_root):
        """Test that the init script exists and is executable."""
        script_path = project_root / "scripts" / "init_test_artifacts_repo.sh"
        assert script_path.exists(), "Init script not found"
        assert os.access(script_path, os.X_OK), "Init script is not executable"

    def test_init_creates_repository(
        self, project_root, test_repo_path, cleanup_test_repo
    ):
        """Test that init script creates the repository."""
        script_path = project_root / "scripts" / "init_test_artifacts_repo.sh"

        result = subprocess.run(
            [str(script_path)], cwd=str(project_root), capture_output=True, text=True
        )

        assert result.returncode == 0, f"Init script failed: {result.stderr}"
        assert test_repo_path.exists(), "Test repository not created"
        assert (test_repo_path / ".git").exists(), "Git repository not initialized"

    def test_init_creates_directory_structure(
        self, project_root, test_repo_path, cleanup_test_repo
    ):
        """Test that init script creates the expected directory structure."""
        script_path = project_root / "scripts" / "init_test_artifacts_repo.sh"

        subprocess.run(
            [str(script_path)], cwd=str(project_root), check=True, capture_output=True
        )

        # Check directories
        assert (
            test_repo_path / "artifacts"
        ).exists(), "artifacts directory not created"
        assert (test_repo_path / "data").exists(), "data directory not created"
        assert (test_repo_path / "logs").exists(), "logs directory not created"
        assert (test_repo_path / "temp").exists(), "temp directory not created"

    def test_init_creates_readme(self, project_root, test_repo_path, cleanup_test_repo):
        """Test that init script creates README.md."""
        script_path = project_root / "scripts" / "init_test_artifacts_repo.sh"

        subprocess.run(
            [str(script_path)], cwd=str(project_root), check=True, capture_output=True
        )

        readme = test_repo_path / "README.md"
        assert readme.exists(), "README.md not created"

        content = readme.read_text()
        assert "Test Artifacts Repository" in content, "README has incorrect content"
        assert "local-only" in content.lower(), "README should mention local-only"

    def test_init_creates_gitignore(
        self, project_root, test_repo_path, cleanup_test_repo
    ):
        """Test that init script creates .gitignore."""
        script_path = project_root / "scripts" / "init_test_artifacts_repo.sh"

        subprocess.run(
            [str(script_path)], cwd=str(project_root), check=True, capture_output=True
        )

        gitignore = test_repo_path / ".gitignore"
        assert gitignore.exists(), ".gitignore not created"

        content = gitignore.read_text()
        assert "__pycache__" in content, ".gitignore should ignore __pycache__"
        assert "*.log" in content, ".gitignore should ignore log files"

    def test_init_creates_initial_commit(
        self, project_root, test_repo_path, cleanup_test_repo
    ):
        """Test that init script creates an initial commit."""
        script_path = project_root / "scripts" / "init_test_artifacts_repo.sh"

        subprocess.run(
            [str(script_path)], cwd=str(project_root), check=True, capture_output=True
        )

        # Check git log
        result = subprocess.run(
            ["git", "log", "--oneline"],
            cwd=str(test_repo_path),
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0, "Git log failed"
        assert "Initial commit" in result.stdout, "Initial commit not found"

    def test_init_creates_test_main_branch(
        self, project_root, test_repo_path, cleanup_test_repo
    ):
        """Test that init script creates test-main branch."""
        script_path = project_root / "scripts" / "init_test_artifacts_repo.sh"

        subprocess.run(
            [str(script_path)], cwd=str(project_root), check=True, capture_output=True
        )

        # Check current branch
        result = subprocess.run(
            ["git", "branch", "--show-current"],
            cwd=str(test_repo_path),
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0, "Git branch command failed"
        assert (
            "test-main" in result.stdout
        ), "test-main branch not created or not checked out"


class TestCleanupScript:
    """Test the cleanup_test_artifacts_repo.sh script."""

    def test_cleanup_script_exists(self, project_root):
        """Test that the cleanup script exists and is executable."""
        script_path = project_root / "scripts" / "cleanup_test_artifacts_repo.sh"
        assert script_path.exists(), "Cleanup script not found"
        assert os.access(script_path, os.X_OK), "Cleanup script is not executable"

    def test_cleanup_removes_repository(
        self, project_root, test_repo_path, cleanup_test_repo
    ):
        """Test that cleanup script removes the repository."""
        # First create the repository
        init_script = project_root / "scripts" / "init_test_artifacts_repo.sh"
        subprocess.run(
            [str(init_script)], cwd=str(project_root), check=True, capture_output=True
        )

        assert test_repo_path.exists(), "Test repo should exist before cleanup"

        # Run cleanup with 'y' input
        cleanup_script = project_root / "scripts" / "cleanup_test_artifacts_repo.sh"
        result = subprocess.run(
            [str(cleanup_script)],
            cwd=str(project_root),
            input="y\n",
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0, f"Cleanup script failed: {result.stderr}"
        assert not test_repo_path.exists(), "Test repository not removed"

    def test_cleanup_handles_nonexistent_repo(
        self, project_root, test_repo_path, cleanup_test_repo
    ):
        """Test that cleanup script handles non-existent repository gracefully."""
        cleanup_script = project_root / "scripts" / "cleanup_test_artifacts_repo.sh"

        result = subprocess.run(
            [str(cleanup_script)], cwd=str(project_root), capture_output=True, text=True
        )

        assert (
            result.returncode == 0
        ), "Cleanup should succeed even if repo doesn't exist"
        assert (
            "No test artifacts repository found" in result.stdout
            or "Nothing to clean up" in result.stdout
        ), "Should indicate no repo to clean up"


class TestRepositoryIsolation:
    """Test that the test repository is properly isolated from main repo."""

    def test_test_repo_not_tracked_by_main_repo(
        self, project_root, test_repo_path, cleanup_test_repo
    ):
        """Test that test_artifacts_repo is ignored by main repository."""
        # Create the test repository
        init_script = project_root / "scripts" / "init_test_artifacts_repo.sh"
        subprocess.run(
            [str(init_script)], cwd=str(project_root), check=True, capture_output=True
        )

        # Check git status in main repo
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=str(project_root),
            capture_output=True,
            text=True,
        )

        # test_artifacts_repo/ directory should not appear in git status
        # (checking for the directory specifically, not the string in filenames)
        assert (
            "test_artifacts_repo/" not in result.stdout
        ), "test_artifacts_repo/ directory should be ignored by main repository"

    def test_gitignore_includes_test_repo(self, project_root):
        """Test that .gitignore includes test_artifacts_repo."""
        gitignore = project_root / ".gitignore"
        assert gitignore.exists(), ".gitignore not found"

        content = gitignore.read_text()
        assert (
            "test_artifacts_repo" in content
        ), "test_artifacts_repo should be in .gitignore"

    def test_test_repo_has_separate_git(
        self, project_root, test_repo_path, cleanup_test_repo
    ):
        """Test that test repository has its own .git directory."""
        # Create the test repository
        init_script = project_root / "scripts" / "init_test_artifacts_repo.sh"
        subprocess.run(
            [str(init_script)], cwd=str(project_root), check=True, capture_output=True
        )

        # Check that test repo has its own .git
        test_git = test_repo_path / ".git"
        main_git = project_root / ".git"

        assert test_git.exists(), "Test repo should have .git directory"
        assert main_git.exists(), "Main repo should have .git directory"
        assert (
            test_git != main_git
        ), "Test repo and main repo should have different .git directories"
        assert str(test_git).startswith(
            str(test_repo_path)
        ), "Test repo .git should be inside test_artifacts_repo"


class TestGitOperations:
    """Test that git operations work correctly in the test repository."""

    def test_can_commit_in_test_repo(
        self, project_root, test_repo_path, cleanup_test_repo
    ):
        """Test that we can make commits in the test repository."""
        # Create the test repository
        init_script = project_root / "scripts" / "init_test_artifacts_repo.sh"
        subprocess.run(
            [str(init_script)], cwd=str(project_root), check=True, capture_output=True
        )

        # Create a test file
        test_file = test_repo_path / "artifacts" / "test.txt"
        test_file.write_text("Test content")

        # Add and commit
        subprocess.run(["git", "add", "."], cwd=str(test_repo_path), check=True)
        result = subprocess.run(
            ["git", "commit", "-m", "Test commit"],
            cwd=str(test_repo_path),
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0, f"Commit failed: {result.stderr}"

        # Verify commit exists
        log_result = subprocess.run(
            ["git", "log", "--oneline"],
            cwd=str(test_repo_path),
            capture_output=True,
            text=True,
        )

        assert "Test commit" in log_result.stdout, "Test commit not found in log"

    def test_test_repo_has_no_remote(
        self, project_root, test_repo_path, cleanup_test_repo
    ):
        """Test that test repository has no configured remote."""
        # Create the test repository
        init_script = project_root / "scripts" / "init_test_artifacts_repo.sh"
        subprocess.run(
            [str(init_script)], cwd=str(project_root), check=True, capture_output=True
        )

        # Check for remotes
        result = subprocess.run(
            ["git", "remote", "-v"],
            cwd=str(test_repo_path),
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0, "Git remote command failed"
        assert (
            result.stdout.strip() == ""
        ), "Test repository should have no remotes configured"


class TestDocumentation:
    """Test that documentation exists and is correct."""

    def test_documentation_exists(self, project_root):
        """Test that usage guide exists."""
        doc_path = project_root / "docs" / "test_artifacts_repository_guide.md"
        assert doc_path.exists(), "Documentation not found"

    def test_documentation_content(self, project_root):
        """Test that documentation has expected content."""
        doc_path = project_root / "docs" / "test_artifacts_repository_guide.md"
        content = doc_path.read_text()

        assert "Test Artifacts Repository" in content, "Documentation should have title"
        assert (
            "init_test_artifacts_repo.sh" in content
        ), "Documentation should mention init script"
        assert (
            "cleanup_test_artifacts_repo.sh" in content
        ), "Documentation should mention cleanup script"
        assert "Quick Start" in content, "Documentation should have Quick Start section"
