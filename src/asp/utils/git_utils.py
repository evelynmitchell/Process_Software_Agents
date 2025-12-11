"""
Git integration utilities for ASP platform.

This module provides functions for committing agent artifacts
to version control automatically.

Implements the git integration architecture from:
docs/artifact_persistence_version_control_decision.md

Author: ASP Development Team
Date: November 17, 2025
"""

import logging
import subprocess
from pathlib import Path

logger = logging.getLogger(__name__)


class GitError(Exception):
    """Exception raised for git operation errors."""

    pass


def is_git_repository(path: str | None = None) -> bool:
    """
    Check if the current directory is a git repository.

    Args:
        path: Optional path to check (defaults to current directory)

    Returns:
        True if in a git repository, False otherwise

    Example:
        >>> is_git_repository()
        True
    """
    try:
        if path:
            result = subprocess.run(
                ["git", "rev-parse", "--git-dir"],
                cwd=path,
                capture_output=True,
                text=True,
                check=False,
            )
        else:
            result = subprocess.run(
                ["git", "rev-parse", "--git-dir"],
                capture_output=True,
                text=True,
                check=False,
            )
        return result.returncode == 0
    except FileNotFoundError:
        return False


def git_status_check(path: str | None = None) -> dict[str, any]:
    """
    Check git working directory status.

    Args:
        path: Optional path to check (defaults to current directory)

    Returns:
        Dict with keys:
        - is_clean (bool): True if working directory is clean
        - untracked_files (list): List of untracked file paths
        - modified_files (list): List of modified file paths

    Raises:
        GitError: If git command fails

    Example:
        >>> status = git_status_check()
        >>> if not status["is_clean"]:
        ...     print(f"Untracked: {status['untracked_files']}")
    """
    try:
        cmd = ["git", "status", "--porcelain"]
        result = subprocess.run(
            cmd,
            cwd=path,
            capture_output=True,
            text=True,
            check=True,
        )

        untracked_files = []
        modified_files = []

        # Parse porcelain output
        for line in result.stdout.splitlines():
            if line.startswith("??"):
                # Untracked file
                untracked_files.append(line[3:].strip())
            elif line.startswith(" M") or line.startswith("M "):
                # Modified file
                modified_files.append(line[3:].strip())

        is_clean = len(result.stdout.strip()) == 0
        return {
            "is_clean": is_clean,
            "untracked_files": untracked_files,
            "modified_files": modified_files,
        }

    except subprocess.CalledProcessError as e:
        raise GitError(f"Git status check failed: {e.stderr}") from e
    except FileNotFoundError as e:
        raise GitError("Git command not found. Is git installed?") from e


def check_files_ignored(file_paths: list[str], path: str | None = None) -> list[str]:
    """
    Check which files are ignored by .gitignore.

    Args:
        file_paths: List of file paths to check (relative to repo root)
        path: Optional path to git repository (defaults to current directory)

    Returns:
        List of file paths that are NOT ignored (can be added to git)

    Example:
        >>> check_files_ignored(["artifacts/plan.json", "src/main.py"])
        ["src/main.py"]  # artifacts/ is in .gitignore
    """
    if not file_paths:
        return []

    try:
        # git check-ignore returns exit code 0 for ignored files, 1 for not ignored
        # Use --stdin to check multiple files at once
        cmd = ["git", "check-ignore", "--stdin"]
        result = subprocess.run(
            cmd,
            cwd=path,
            input="\n".join(file_paths),
            capture_output=True,
            text=True,
            check=False,  # Don't raise on non-zero exit (expected for non-ignored files)
        )

        # Parse ignored files from output
        ignored_files = (
            set(result.stdout.strip().split("\n")) if result.stdout.strip() else set()
        )

        # Return files that are NOT ignored
        return [f for f in file_paths if f not in ignored_files]

    except FileNotFoundError:
        # Git not installed, assume no files ignored
        return file_paths


def git_add_files(file_paths: list[str], path: str | None = None) -> None:
    """
    Stage files for commit.

    Args:
        file_paths: List of file paths to stage (relative to repo root)
        path: Optional path to git repository (defaults to current directory)

    Raises:
        GitError: If git add fails

    Example:
        >>> git_add_files(["artifacts/JWT-AUTH-001/plan.json", "artifacts/JWT-AUTH-001/plan.md"])
    """
    if not file_paths:
        logger.warning("No files provided to git_add_files")
        return

    # Filter out ignored files
    addable_files = check_files_ignored(file_paths, path)

    if not addable_files:
        logger.debug(f"All {len(file_paths)} files are in .gitignore, skipping git add")
        return

    if len(addable_files) < len(file_paths):
        ignored_count = len(file_paths) - len(addable_files)
        logger.debug(f"Skipping {ignored_count} files in .gitignore")

    try:
        cmd = ["git", "add"] + addable_files
        result = subprocess.run(
            cmd,
            cwd=path,
            capture_output=True,
            text=True,
            check=True,
        )

        logger.debug(f"Added {len(addable_files)} files to git staging area")

    except subprocess.CalledProcessError as e:
        raise GitError(f"Git add failed: {e.stderr}") from e


def git_commit(
    message: str,
    path: str | None = None,
    allow_empty: bool = False,
) -> str:
    """
    Create a git commit with the given message.

    Args:
        message: Commit message
        path: Optional path to git repository (defaults to current directory)
        allow_empty: Allow empty commits (no changes staged)

    Returns:
        Commit hash (short SHA)

    Raises:
        GitError: If commit fails

    Example:
        >>> commit_hash = git_commit("Planning Agent: Add project plan for JWT-AUTH-001")
        >>> print(f"Created commit: {commit_hash}")
    """
    try:
        cmd = ["git", "commit", "-m", message]
        if allow_empty:
            cmd.append("--allow-empty")

        result = subprocess.run(
            cmd,
            cwd=path,
            capture_output=True,
            text=True,
            check=True,
        )

        # Extract commit hash from output
        # Output format: "[main abc1234] Commit message"
        commit_hash = "unknown"
        if result.stdout:
            parts = result.stdout.split("]")[0].split()
            if len(parts) >= 2:
                commit_hash = parts[-1].strip("[]")

        logger.info(f"Created git commit: {commit_hash}")
        return commit_hash

    except subprocess.CalledProcessError as e:
        error_msg = e.stderr or e.stdout or "Unknown error"
        raise GitError(f"Git commit failed: {error_msg}") from e


def git_commit_artifact(
    task_id: str,
    agent_name: str,
    artifact_files: list[str],
    status: str | None = None,
    path: str | None = None,
) -> str | None:
    """
    Commit artifact files with standardized message format.

    Commit message format: "{agent_name}: {action} for {task_id} [{status}]"

    Args:
        task_id: Task identifier (e.g., "JWT-AUTH-001")
        agent_name: Name of agent creating artifact (e.g., "Planning Agent", "Design Agent")
        artifact_files: List of file paths to commit (relative to repo root)
        status: Optional status (e.g., "PASS", "FAIL", "COMPLETE")
        path: Optional path to git repository (defaults to current directory)

    Returns:
        Commit hash (short SHA), or None if all files are in .gitignore

    Raises:
        GitError: If commit fails

    Example:
        >>> git_commit_artifact(
        ...     "JWT-AUTH-001",
        ...     "Planning Agent",
        ...     ["artifacts/JWT-AUTH-001/plan.json", "artifacts/JWT-AUTH-001/plan.md"]
        ... )
        "abc1234"
    """
    try:
        # Check if in git repository
        if not is_git_repository(path):
            raise GitError("Not in a git repository")

        # Check which files can be added (not in .gitignore)
        addable_files = check_files_ignored(artifact_files, path)
        if not addable_files:
            logger.debug(
                f"All artifact files for {task_id} are in .gitignore, skipping commit"
            )
            return None

        # Stage files
        git_add_files(artifact_files, path)

        # Build commit message
        action = _get_action_for_agent(agent_name)
        if status:
            message = f"{agent_name}: {action} for {task_id} [{status}]"
        else:
            message = f"{agent_name}: {action} for {task_id}"

        # Add file list to commit body (only addable files)
        file_count = len(addable_files)
        if file_count == 1:
            message += f"\n\nFiles: {addable_files[0]}"
        else:
            message += f"\n\nFiles ({file_count}):"
            for file_path in addable_files:
                message += f"\n- {file_path}"

        # Add co-author footer
        message += (
            "\n\n Generated with [Claude Code](https://claude.com/claude-code)\n\n"
            "Co-Authored-By: Claude <noreply@anthropic.com>"
        )

        # Commit
        commit_hash = git_commit(message, path)

        logger.info(f"Committed artifacts for {task_id} by {agent_name}: {commit_hash}")
        return commit_hash

    except Exception as e:
        raise GitError(f"Failed to commit artifact: {e}") from e


def _get_action_for_agent(agent_name: str) -> str:
    """
    Get the action verb for an agent name.

    Args:
        agent_name: Agent name (e.g., "Planning Agent", "Code Agent")

    Returns:
        Action verb (e.g., "Add project plan", "Implement")

    Example:
        >>> _get_action_for_agent("Planning Agent")
        "Add project plan"
    """
    action_map = {
        "Planning Agent": "Add project plan",
        "Design Agent": "Add design specification",
        "Design Review Agent": "Add design review",
        "Code Agent": "Implement",
        "Code Review Agent": "Add code review",
        "Test Agent": "Add tests",
        "Integration Agent": "Add integration validation",
        "Postmortem Agent": "Add postmortem report",
        "Prompt Versioner": "Update prompts",
    }

    return action_map.get(agent_name, "Add artifact")


def get_current_branch(path: str | None = None) -> str:
    """
    Get the current git branch name.

    Args:
        path: Optional path to git repository (defaults to current directory)

    Returns:
        Current branch name

    Raises:
        GitError: If not in a git repository or branch detection fails

    Example:
        >>> get_current_branch()
        "main"
    """
    try:
        cmd = ["git", "rev-parse", "--abbrev-ref", "HEAD"]
        result = subprocess.run(
            cmd,
            cwd=path,
            capture_output=True,
            text=True,
            check=True,
        )

        branch = result.stdout.strip()
        return branch

    except subprocess.CalledProcessError as e:
        raise GitError(f"Failed to get current branch: {e.stderr}") from e


def get_git_root(path: str | None = None) -> Path:
    """
    Get the root directory of the git repository.

    Args:
        path: Optional path to start search (defaults to current directory)

    Returns:
        Path to git repository root

    Raises:
        GitError: If not in a git repository

    Example:
        >>> get_git_root()
        Path("/workspaces/Process_Software_Agents")
    """
    try:
        cmd = ["git", "rev-parse", "--show-toplevel"]
        result = subprocess.run(
            cmd,
            cwd=path,
            capture_output=True,
            text=True,
            check=True,
        )

        git_root = Path(result.stdout.strip())
        return git_root

    except subprocess.CalledProcessError as e:
        if "not a git repository" in e.stderr.lower():
            raise GitError("Not a git repository") from e
        raise GitError(f"Failed to get git root: {e.stderr}") from e
