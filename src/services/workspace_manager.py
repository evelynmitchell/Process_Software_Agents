"""Workspace Manager for multi-repository task isolation.

This service manages ephemeral workspaces for ASP tasks, providing clean isolation
for working on any repository (including Process_Software_Agents itself).

Architecture:
- Workspaces created in /tmp/asp-workspaces/{task-id}/
- Each workspace contains: target repo + .asp/ working directory
- Execution traces stored in Langfuse (not in git)
- Automatic cleanup after task completion

See: design/ADR_001_workspace_isolation_and_execution_tracking.md
"""

import shutil
import subprocess
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional


@dataclass
class Workspace:
    """Represents an isolated workspace for a task.

    Attributes:
        task_id: Unique identifier for this task
        path: Root path of workspace (/tmp/asp-workspaces/{task-id}/)
        target_repo_path: Path where target repository is cloned
        asp_path: Path to .asp/ working directory for artifacts
        created_at: Timestamp when workspace was created
    """

    task_id: str
    path: Path
    target_repo_path: Path
    asp_path: Path
    created_at: datetime

    def __str__(self) -> str:
        return f"Workspace({self.task_id} at {self.path})"


class WorkspaceManager:
    """Manages ephemeral workspaces for multi-repository tasks.

    Key Responsibilities:
    - Create isolated workspaces in /tmp
    - Clone target repositories
    - Initialize .asp/ working directories
    - Cleanup workspaces after completion

    Example:
        >>> manager = WorkspaceManager()
        >>> workspace = manager.create_workspace("task-123-fix-auth")
        >>> manager.clone_repository(workspace, "https://github.com/org/repo.git")
        >>> # ... do work in workspace ...
        >>> manager.cleanup_workspace(workspace)
    """

    def __init__(self, base_path: Optional[Path] = None):
        """Initialize WorkspaceManager.

        Args:
            base_path: Base directory for workspaces (default: /tmp/asp-workspaces/)
        """
        self.base_path = base_path or Path("/tmp/asp-workspaces")
        self.base_path.mkdir(parents=True, exist_ok=True)

    def create_workspace(self, task_id: str) -> Workspace:
        """Create a new isolated workspace for a task.

        Creates directory structure:
            /tmp/asp-workspaces/{task-id}/
            ├── target-repo/  (will be populated by clone_repository)
            └── .asp/         (working directory for ASP artifacts)

        Args:
            task_id: Unique identifier for the task (e.g., "task-123-fix-auth-bug")

        Returns:
            Workspace object representing the created workspace

        Raises:
            FileExistsError: If workspace for this task_id already exists

        Example:
            >>> workspace = manager.create_workspace("task-456-add-feature")
            >>> print(workspace.path)
            /tmp/asp-workspaces/task-456-add-feature
        """
        workspace_path = self.base_path / task_id

        if workspace_path.exists():
            raise FileExistsError(
                f"Workspace already exists: {workspace_path}. "
                f"Use cleanup_workspace() first or choose different task_id."
            )

        # Create workspace directory structure
        workspace_path.mkdir(parents=True, exist_ok=False)

        # Create subdirectories
        target_repo_path = workspace_path / "target-repo"
        asp_path = workspace_path / ".asp"
        asp_path.mkdir(exist_ok=True)

        workspace = Workspace(
            task_id=task_id,
            path=workspace_path,
            target_repo_path=target_repo_path,
            asp_path=asp_path,
            created_at=datetime.now(),
        )

        return workspace

    def clone_repository(
        self, workspace: Workspace, repo_url: str, branch: Optional[str] = None
    ) -> Path:
        """Clone a repository into the workspace.

        Args:
            workspace: Workspace object where repo should be cloned
            repo_url: Git repository URL (https or ssh)
            branch: Optional branch to checkout (default: main/master)

        Returns:
            Path to the cloned repository

        Raises:
            subprocess.CalledProcessError: If git clone fails

        Example:
            >>> path = manager.clone_repository(
            ...     workspace,
            ...     "https://github.com/org/my-web-app.git",
            ...     branch="develop"
            ... )
        """
        cmd = ["git", "clone", repo_url, str(workspace.target_repo_path)]

        if branch:
            cmd.extend(["--branch", branch])

        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True, check=True, cwd=str(workspace.path)
            )
            return workspace.target_repo_path
        except subprocess.CalledProcessError as e:
            raise RuntimeError(
                f"Failed to clone repository {repo_url}: {e.stderr}"
            ) from e

    def initialize_git_repo(
        self, workspace: Workspace, initial_files: Optional[dict] = None
    ) -> Path:
        """Initialize a new git repository in the workspace (for testing/new projects).

        This is useful for:
        - Creating test repositories (like hellogit)
        - Starting new projects from scratch
        - Testing ASP workflows without cloning

        Args:
            workspace: Workspace where git repo should be initialized
            initial_files: Optional dict of {filename: content} to create

        Returns:
            Path to the initialized repository

        Example:
            >>> path = manager.initialize_git_repo(
            ...     workspace,
            ...     initial_files={"README.md": "# Hello Git\\n"}
            ... )
        """
        repo_path = workspace.target_repo_path
        repo_path.mkdir(parents=True, exist_ok=True)

        # Initialize git repository
        subprocess.run(
            ["git", "init"], cwd=str(repo_path), capture_output=True, check=True
        )

        # Configure git (required for commits)
        subprocess.run(
            ["git", "config", "user.email", "asp@example.com"],
            cwd=str(repo_path),
            check=True,
        )
        subprocess.run(
            ["git", "config", "user.name", "ASP Agent"], cwd=str(repo_path), check=True
        )

        # Create initial files if provided
        if initial_files:
            for filename, content in initial_files.items():
                file_path = repo_path / filename
                file_path.parent.mkdir(parents=True, exist_ok=True)
                file_path.write_text(content)

            # Initial commit
            subprocess.run(["git", "add", "."], cwd=str(repo_path), check=True)
            subprocess.run(
                ["git", "commit", "-m", "Initial commit"],
                cwd=str(repo_path),
                capture_output=True,
                check=True,
            )

        return repo_path

    def cleanup_workspace(self, workspace: Workspace, force: bool = False) -> None:
        """Remove workspace directory and all contents.

        Args:
            workspace: Workspace to clean up
            force: If True, delete even if workspace contains uncommitted changes

        Raises:
            ValueError: If workspace contains uncommitted changes and force=False

        Example:
            >>> manager.cleanup_workspace(workspace)
        """
        if not force:
            # Check for uncommitted changes in target repo
            if workspace.target_repo_path.exists():
                try:
                    result = subprocess.run(
                        ["git", "status", "--porcelain"],
                        cwd=str(workspace.target_repo_path),
                        capture_output=True,
                        text=True,
                        check=True,
                    )
                    if result.stdout.strip():
                        raise ValueError(
                            f"Workspace {workspace.task_id} has uncommitted changes. "
                            f"Use force=True to delete anyway."
                        )
                except subprocess.CalledProcessError:
                    # Not a git repo or git error, proceed with cleanup
                    pass

        # Remove entire workspace directory
        if workspace.path.exists():
            shutil.rmtree(workspace.path)

    def list_workspaces(self) -> list[Workspace]:
        """List all existing workspaces.

        Returns:
            List of Workspace objects for all workspaces in base_path

        Example:
            >>> workspaces = manager.list_workspaces()
            >>> for ws in workspaces:
            ...     print(ws.task_id)
        """
        workspaces = []

        if not self.base_path.exists():
            return workspaces

        for task_dir in self.base_path.iterdir():
            if task_dir.is_dir():
                # Reconstruct workspace object
                target_repo_path = task_dir / "target-repo"
                asp_path = task_dir / ".asp"

                # Get creation time from directory metadata
                created_at = datetime.fromtimestamp(task_dir.stat().st_ctime)

                workspace = Workspace(
                    task_id=task_dir.name,
                    path=task_dir,
                    target_repo_path=target_repo_path,
                    asp_path=asp_path,
                    created_at=created_at,
                )
                workspaces.append(workspace)

        return sorted(workspaces, key=lambda w: w.created_at, reverse=True)
