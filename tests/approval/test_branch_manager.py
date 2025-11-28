"""Tests for BranchManager."""

import pytest
import subprocess
import tempfile
import shutil
from pathlib import Path

from asp.approval.branch_manager import BranchManager


@pytest.fixture
def temp_repo():
    """Create temporary git repository for testing."""
    repo_dir = tempfile.mkdtemp()

    # Initialize git repo
    subprocess.run(["git", "init", "-b", "main"], cwd=repo_dir, check=True, capture_output=True)
    subprocess.run(
        ["git", "config", "user.email", "test@test.com"],
        cwd=repo_dir,
        check=True,
        capture_output=True
    )
    subprocess.run(
        ["git", "config", "user.name", "Test User"],
        cwd=repo_dir,
        check=True,
        capture_output=True
    )
    # Disable commit signing for test repo
    subprocess.run(
        ["git", "config", "commit.gpgsign", "false"],
        cwd=repo_dir,
        check=True,
        capture_output=True
    )

    # Create initial commit
    readme = Path(repo_dir) / "README.md"
    readme.write_text("# Test Repo\n")
    subprocess.run(["git", "add", "."], cwd=repo_dir, check=True, capture_output=True)
    subprocess.run(
        ["git", "commit", "-m", "Initial commit"],
        cwd=repo_dir,
        check=True,
        capture_output=True
    )

    yield repo_dir

    shutil.rmtree(repo_dir)


def test_create_branch(temp_repo):
    """Test branch creation."""
    manager = BranchManager(temp_repo)

    manager.create_branch("test-branch", "main")

    # Verify branch exists
    assert manager.branch_exists("test-branch")
    assert manager.get_current_branch() == "test-branch"


def test_commit_output(temp_repo):
    """Test committing agent output."""
    manager = BranchManager(temp_repo)

    # Create branch
    manager.create_branch("test-branch", "main")

    # Commit output
    output = {
        "agent": "TestAgent",
        "task_id": "TEST-001",
        "gate_type": "test_gate",
        "artifacts": {
            "test_file.txt": "Test content"
        }
    }

    commit_sha = manager.commit_output(
        branch_name="test-branch",
        output=output,
        task_id="TEST-001",
        gate_type="test_gate"
    )

    # Verify commit exists
    assert len(commit_sha) == 40  # Git SHA is 40 chars

    # Verify file was created
    test_file = Path(temp_repo) / "test_file.txt"
    assert test_file.exists()
    assert test_file.read_text() == "Test content"


def test_generate_diff(temp_repo):
    """Test diff generation between branches."""
    manager = BranchManager(temp_repo)

    # Create and commit on feature branch
    manager.create_branch("feature", "main")

    output = {
        "artifacts": {
            "feature.txt": "Feature content"
        }
    }
    manager.commit_output("feature", output, "TEST-001", "test")

    # Generate diff
    diff = manager.generate_diff("main", "feature")

    assert "feature.txt" in diff
    assert "+Feature content" in diff


def test_get_diff_stats(temp_repo):
    """Test diff statistics."""
    manager = BranchManager(temp_repo)

    # Create and commit on feature branch
    manager.create_branch("feature", "main")

    output = {
        "artifacts": {
            "feature.txt": "Line 1\nLine 2\nLine 3\n"
        }
    }
    manager.commit_output("feature", output, "TEST-001", "test")

    # Get diff stats
    stats = manager.get_diff_stats("main", "feature")

    assert stats["files_changed"] >= 1
    assert stats["insertions"] >= 3


def test_add_note(temp_repo):
    """Test adding git notes."""
    manager = BranchManager(temp_repo)

    # Get current commit SHA
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=temp_repo,
        capture_output=True,
        text=True,
        check=True
    )
    commit_sha = result.stdout.strip()

    # Add note
    note_content = "Test review note"
    manager.add_note(commit_sha, note_content, "test-notes")

    # Verify note exists
    result = subprocess.run(
        ["git", "notes", "--ref", "test-notes", "show", commit_sha],
        cwd=temp_repo,
        capture_output=True,
        text=True,
        check=True
    )
    assert note_content in result.stdout


def test_delete_branch(temp_repo):
    """Test branch deletion."""
    manager = BranchManager(temp_repo)

    # Create branch
    manager.create_branch("to-delete", "main")
    assert manager.branch_exists("to-delete")

    # Delete branch
    manager.delete_branch("to-delete")

    # Verify branch is gone
    assert not manager.branch_exists("to-delete")


def test_list_branches(temp_repo):
    """Test listing branches."""
    manager = BranchManager(temp_repo)

    # Create multiple branches
    manager.create_branch("review/task-1", "main")
    manager.create_branch("review/task-2", "main")
    manager.create_branch("feature/other", "main")

    # List all review branches
    review_branches = manager.list_branches("review/*")

    assert "review/task-1" in review_branches
    assert "review/task-2" in review_branches
    assert "feature/other" not in review_branches


def test_branch_exists(temp_repo):
    """Test branch existence check."""
    manager = BranchManager(temp_repo)

    assert manager.branch_exists("main")
    assert not manager.branch_exists("nonexistent")


def test_get_current_branch(temp_repo):
    """Test getting current branch."""
    manager = BranchManager(temp_repo)

    assert manager.get_current_branch() == "main"

    manager.create_branch("test", "main")
    assert manager.get_current_branch() == "test"


def test_commit_output_with_output_file(temp_repo):
    """Test committing output with output_file key."""
    manager = BranchManager(temp_repo)

    manager.create_branch("test-branch", "main")

    output = {
        "agent": "TestAgent",
        "output_file": "output.txt",
        "content": "Output file content"
    }

    commit_sha = manager.commit_output(
        branch_name="test-branch",
        output=output,
        task_id="TEST-002",
        gate_type="test"
    )

    # Verify file was created
    output_file = Path(temp_repo) / "output.txt"
    assert output_file.exists()
    assert output_file.read_text() == "Output file content"


def test_commit_output_no_changes(temp_repo):
    """Test committing when there are no changes."""
    manager = BranchManager(temp_repo)

    manager.create_branch("test-branch", "main")

    # Empty output (no changes)
    output = {}

    commit_sha = manager.commit_output(
        branch_name="test-branch",
        output=output,
        task_id="TEST-003",
        gate_type="test"
    )

    # Should return current HEAD without creating new commit
    assert len(commit_sha) == 40
