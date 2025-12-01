"""Tests for WorkspaceManager service.

Tests cover:
- Workspace creation and structure
- Repository cloning
- Git repository initialization
- Workspace cleanup
- Workspace listing
- Error handling

See: design/ADR_001_workspace_isolation_and_execution_tracking.md
"""

import subprocess
from datetime import datetime
from pathlib import Path

import pytest

from src.services.workspace_manager import WorkspaceManager


@pytest.fixture
def temp_base_path(tmp_path):
    """Provide a temporary base path for test workspaces."""
    return tmp_path / "test-workspaces"


@pytest.fixture
def manager(temp_base_path):
    """Provide a WorkspaceManager instance with temporary base path."""
    return WorkspaceManager(base_path=temp_base_path)


class TestWorkspaceCreation:
    """Test workspace creation and structure."""

    def test_create_workspace_creates_directory_structure(
        self, manager, temp_base_path
    ):
        """Test that create_workspace creates correct directory structure."""
        workspace = manager.create_workspace("task-001")

        assert workspace.path.exists()
        assert workspace.path == temp_base_path / "task-001"
        assert workspace.asp_path.exists()
        assert workspace.asp_path == workspace.path / ".asp"
        assert not workspace.target_repo_path.exists()  # Created on clone

    def test_create_workspace_sets_metadata(self, manager):
        """Test that workspace metadata is set correctly."""
        before = datetime.now()
        workspace = manager.create_workspace("task-002")
        after = datetime.now()

        assert workspace.task_id == "task-002"
        assert before <= workspace.created_at <= after

    def test_create_workspace_raises_on_duplicate(self, manager):
        """Test that creating duplicate workspace raises FileExistsError."""
        manager.create_workspace("task-003")

        with pytest.raises(FileExistsError, match="Workspace already exists"):
            manager.create_workspace("task-003")

    def test_workspace_string_representation(self, manager):
        """Test workspace string representation."""
        workspace = manager.create_workspace("task-004")
        assert "task-004" in str(workspace)
        assert str(workspace.path) in str(workspace)


class TestGitRepositoryInitialization:
    """Test git repository initialization for new projects."""

    def test_initialize_git_repo_creates_repo(self, manager):
        """Test that initialize_git_repo creates a git repository."""
        workspace = manager.create_workspace("task-005")
        repo_path = manager.initialize_git_repo(workspace)

        assert repo_path.exists()
        assert (repo_path / ".git").exists()

    def test_initialize_git_repo_with_initial_files(self, manager):
        """Test that initial files are created and committed."""
        workspace = manager.create_workspace("task-006")
        initial_files = {
            "README.md": "# Hello Git\n",
            "src/main.py": "print('hello')\n",
        }

        repo_path = manager.initialize_git_repo(workspace, initial_files=initial_files)

        # Check files exist
        assert (repo_path / "README.md").exists()
        assert (repo_path / "src/main.py").exists()
        assert (repo_path / "README.md").read_text() == "# Hello Git\n"

        # Check files are committed
        result = subprocess.run(
            ["git", "log", "--oneline"],
            cwd=str(repo_path),
            capture_output=True,
            text=True,
            check=True,
        )
        assert "Initial commit" in result.stdout

    def test_initialize_git_repo_has_git_config(self, manager):
        """Test that initialized repo has git config set."""
        workspace = manager.create_workspace("task-007")
        repo_path = manager.initialize_git_repo(workspace)

        # Check git config
        result = subprocess.run(
            ["git", "config", "user.email"],
            cwd=str(repo_path),
            capture_output=True,
            text=True,
            check=True,
        )
        assert result.stdout.strip() == "asp@example.com"


class TestRepositoryCloning:
    """Test repository cloning from remote URLs."""

    @pytest.mark.skip(
        reason="Requires network access - test with real repo URL manually"
    )
    def test_clone_repository_from_github(self, manager):
        """Test cloning a real repository from GitHub.

        Note: Skipped by default to avoid network dependency.
        Run manually: pytest -k test_clone_repository_from_github --run-network
        """
        workspace = manager.create_workspace("task-clone-real")
        repo_url = "https://github.com/anthropics/anthropic-sdk-python.git"

        repo_path = manager.clone_repository(workspace, repo_url)

        assert repo_path.exists()
        assert (repo_path / ".git").exists()
        assert (repo_path / "README.md").exists()

    def test_clone_repository_raises_on_invalid_url(self, manager):
        """Test that cloning invalid URL raises error."""
        workspace = manager.create_workspace("task-clone-fail")

        with pytest.raises(RuntimeError, match="Failed to clone repository"):
            manager.clone_repository(
                workspace, "https://invalid-url-12345.com/repo.git"
            )


class TestWorkspaceCleanup:
    """Test workspace cleanup and deletion."""

    def test_cleanup_workspace_deletes_directory(self, manager):
        """Test that cleanup_workspace removes workspace directory."""
        workspace = manager.create_workspace("task-008")
        assert workspace.path.exists()

        manager.cleanup_workspace(workspace)

        assert not workspace.path.exists()

    def test_cleanup_workspace_with_uncommitted_changes_raises_error(self, manager):
        """Test that cleanup fails if uncommitted changes exist."""
        workspace = manager.create_workspace("task-009")
        manager.initialize_git_repo(workspace)

        # Create uncommitted change
        (workspace.target_repo_path / "new_file.txt").write_text("uncommitted\n")

        with pytest.raises(ValueError, match="has uncommitted changes"):
            manager.cleanup_workspace(workspace)

    def test_cleanup_workspace_with_force_deletes_anyway(self, manager):
        """Test that cleanup with force=True deletes despite uncommitted changes."""
        workspace = manager.create_workspace("task-010")
        manager.initialize_git_repo(workspace)

        # Create uncommitted change
        (workspace.target_repo_path / "new_file.txt").write_text("uncommitted\n")

        manager.cleanup_workspace(workspace, force=True)

        assert not workspace.path.exists()

    def test_cleanup_nonexistent_workspace_succeeds(self, manager):
        """Test that cleaning up non-existent workspace doesn't error."""
        import shutil

        workspace = manager.create_workspace("task-011")
        shutil.rmtree(workspace.path)  # Manually delete entire workspace

        # Should not raise
        manager.cleanup_workspace(workspace)


class TestWorkspaceListing:
    """Test listing all workspaces."""

    def test_list_workspaces_empty(self, manager):
        """Test list_workspaces returns empty list when no workspaces."""
        workspaces = manager.list_workspaces()
        assert workspaces == []

    def test_list_workspaces_returns_all_workspaces(self, manager):
        """Test list_workspaces returns all created workspaces."""
        ws1 = manager.create_workspace("task-012")
        ws2 = manager.create_workspace("task-013")
        ws3 = manager.create_workspace("task-014")

        workspaces = manager.list_workspaces()

        assert len(workspaces) == 3
        task_ids = {ws.task_id for ws in workspaces}
        assert task_ids == {"task-012", "task-013", "task-014"}

    def test_list_workspaces_sorted_by_creation_time(self, manager):
        """Test that workspaces are sorted by creation time (newest first)."""
        import time

        ws1 = manager.create_workspace("task-015")
        time.sleep(0.01)  # Ensure different creation times
        ws2 = manager.create_workspace("task-016")
        time.sleep(0.01)
        ws3 = manager.create_workspace("task-017")

        workspaces = manager.list_workspaces()

        # Newest first
        assert workspaces[0].task_id == "task-017"
        assert workspaces[1].task_id == "task-016"
        assert workspaces[2].task_id == "task-015"


class TestWorkspaceManagerInitialization:
    """Test WorkspaceManager initialization."""

    def test_manager_creates_base_path_if_not_exists(self, tmp_path):
        """Test that manager creates base_path if it doesn't exist."""
        base_path = tmp_path / "nonexistent" / "workspaces"
        assert not base_path.exists()

        manager = WorkspaceManager(base_path=base_path)

        assert base_path.exists()

    def test_manager_uses_default_base_path(self):
        """Test that manager uses /tmp/asp-workspaces by default."""
        manager = WorkspaceManager()
        assert manager.base_path == Path("/tmp/asp-workspaces")


class TestWorkspaceIntegration:
    """Integration tests for complete workspace workflows."""

    def test_full_workflow_create_init_cleanup(self, manager):
        """Test complete workflow: create → initialize → work → cleanup."""
        # Create workspace
        workspace = manager.create_workspace("task-integration-001")
        assert workspace.path.exists()

        # Initialize git repo
        repo_path = manager.initialize_git_repo(
            workspace, initial_files={"README.md": "# Test Project\n"}
        )
        assert (repo_path / "README.md").exists()

        # Do some work
        (repo_path / "new_feature.py").write_text("def hello(): pass\n")
        subprocess.run(["git", "add", "."], cwd=str(repo_path), check=True)
        subprocess.run(
            ["git", "commit", "-m", "Add new feature"], cwd=str(repo_path), check=True
        )

        # Verify clean state
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=str(repo_path),
            capture_output=True,
            text=True,
            check=True,
        )
        assert result.stdout.strip() == ""

        # Cleanup
        manager.cleanup_workspace(workspace)
        assert not workspace.path.exists()
