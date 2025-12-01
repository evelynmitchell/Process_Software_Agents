"""Tests for MergeController."""

import pytest
import subprocess
import tempfile
import shutil
from pathlib import Path
from datetime import datetime

from asp.approval.merge_controller import MergeController
from asp.approval.base import ApprovalResponse, ReviewDecision


@pytest.fixture
def temp_repo():
    """Create temporary git repository for testing."""
    repo_dir = tempfile.mkdtemp()

    # Initialize git repo
    subprocess.run(
        ["git", "init", "-b", "main"], cwd=repo_dir, check=True, capture_output=True
    )
    subprocess.run(
        ["git", "config", "user.email", "test@test.com"],
        cwd=repo_dir,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "Test User"],
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

    # Create initial commit
    readme = Path(repo_dir) / "README.md"
    readme.write_text("# Test Repo\n")
    subprocess.run(["git", "add", "."], cwd=repo_dir, check=True, capture_output=True)
    subprocess.run(
        ["git", "commit", "-m", "Initial commit"],
        cwd=repo_dir,
        check=True,
        capture_output=True,
    )

    yield repo_dir

    shutil.rmtree(repo_dir)


@pytest.fixture
def approval_metadata():
    """Create sample approval metadata."""
    return ApprovalResponse(
        decision=ReviewDecision.APPROVED,
        reviewer="test@example.com",
        timestamp=datetime.utcnow().isoformat() + "Z",
        justification="Test approval",
    )


def test_merge_branch(temp_repo, approval_metadata):
    """Test merging an approved branch."""
    controller = MergeController(temp_repo)

    # Create feature branch with changes
    subprocess.run(
        ["git", "checkout", "-b", "feature"],
        cwd=temp_repo,
        check=True,
        capture_output=True,
    )
    feature_file = Path(temp_repo) / "feature.txt"
    feature_file.write_text("Feature content")
    subprocess.run(["git", "add", "."], cwd=temp_repo, check=True, capture_output=True)
    subprocess.run(
        ["git", "commit", "-m", "Add feature"],
        cwd=temp_repo,
        check=True,
        capture_output=True,
    )

    # Merge branch
    merge_sha = controller.merge_branch(
        branch_name="feature",
        base_branch="main",
        review_metadata=approval_metadata,
        task_id="TEST-001",
    )

    # Verify merge commit exists
    assert len(merge_sha) == 40

    # Verify we're on main
    result = subprocess.run(
        ["git", "rev-parse", "--abbrev-ref", "HEAD"],
        cwd=temp_repo,
        capture_output=True,
        text=True,
        check=True,
    )
    assert result.stdout.strip() == "main"

    # Verify merge commit message
    result = subprocess.run(
        ["git", "log", "-1", "--pretty=%B"],
        cwd=temp_repo,
        capture_output=True,
        text=True,
        check=True,
    )
    commit_msg = result.stdout
    assert "HITL Approved" in commit_msg
    assert "test@example.com" in commit_msg


def test_tag_rejected(temp_repo, approval_metadata):
    """Test tagging a rejected branch."""
    controller = MergeController(temp_repo)

    # Create feature branch
    subprocess.run(
        ["git", "checkout", "-b", "feature"],
        cwd=temp_repo,
        check=True,
        capture_output=True,
    )
    feature_file = Path(temp_repo) / "feature.txt"
    feature_file.write_text("Feature content")
    subprocess.run(["git", "add", "."], cwd=temp_repo, check=True, capture_output=True)
    subprocess.run(
        ["git", "commit", "-m", "Add feature"],
        cwd=temp_repo,
        check=True,
        capture_output=True,
    )

    # Update metadata for rejection
    approval_metadata.decision = ReviewDecision.REJECTED
    approval_metadata.justification = "Test rejection"

    # Tag rejected branch
    controller.tag_rejected(
        branch_name="feature", review_metadata=approval_metadata, task_id="TEST-001"
    )

    # Verify tag exists
    assert controller.tag_exists("review-rejected-TEST-001")

    # Verify tag message
    result = subprocess.run(
        ["git", "tag", "-n99", "review-rejected-TEST-001"],
        cwd=temp_repo,
        capture_output=True,
        text=True,
        check=True,
    )
    tag_msg = result.stdout
    assert "REJECTED" in tag_msg
    assert "test@example.com" in tag_msg


def test_tag_deferred(temp_repo, approval_metadata):
    """Test tagging a deferred branch."""
    controller = MergeController(temp_repo)

    # Create feature branch
    subprocess.run(
        ["git", "checkout", "-b", "feature"],
        cwd=temp_repo,
        check=True,
        capture_output=True,
    )

    # Update metadata for deferral
    approval_metadata.decision = ReviewDecision.DEFERRED
    approval_metadata.justification = "Need more time to review"

    # Tag deferred branch
    controller.tag_deferred(
        branch_name="feature", review_metadata=approval_metadata, task_id="TEST-001"
    )

    # Verify tag exists
    assert controller.tag_exists("review-deferred-TEST-001")


def test_create_tag(temp_repo, approval_metadata):
    """Test creating annotated tag."""
    controller = MergeController(temp_repo)

    # Get current commit SHA
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=temp_repo,
        capture_output=True,
        text=True,
        check=True,
    )
    commit_sha = result.stdout.strip()

    # Create tag
    controller.create_tag(
        tag_name="test-tag", commit_sha=commit_sha, review_metadata=approval_metadata
    )

    # Verify tag exists
    assert controller.tag_exists("test-tag")


def test_tag_exists(temp_repo):
    """Test checking tag existence."""
    controller = MergeController(temp_repo)

    # Tag doesn't exist
    assert not controller.tag_exists("nonexistent-tag")

    # Create tag
    subprocess.run(
        ["git", "tag", "test-tag"], cwd=temp_repo, check=True, capture_output=True
    )

    # Tag exists
    assert controller.tag_exists("test-tag")


def test_delete_tag(temp_repo):
    """Test deleting a tag."""
    controller = MergeController(temp_repo)

    # Create tag
    subprocess.run(
        ["git", "tag", "test-tag"], cwd=temp_repo, check=True, capture_output=True
    )
    assert controller.tag_exists("test-tag")

    # Delete tag
    controller.delete_tag("test-tag")

    # Verify tag is gone
    assert not controller.tag_exists("test-tag")


def test_merge_branch_without_task_id(temp_repo, approval_metadata):
    """Test merging branch without task_id."""
    controller = MergeController(temp_repo)

    # Create feature branch
    subprocess.run(
        ["git", "checkout", "-b", "feature"],
        cwd=temp_repo,
        check=True,
        capture_output=True,
    )
    feature_file = Path(temp_repo) / "feature.txt"
    feature_file.write_text("Feature content")
    subprocess.run(["git", "add", "."], cwd=temp_repo, check=True, capture_output=True)
    subprocess.run(
        ["git", "commit", "-m", "Add feature"],
        cwd=temp_repo,
        check=True,
        capture_output=True,
    )

    # Merge without task_id
    merge_sha = controller.merge_branch(
        branch_name="feature",
        base_branch="main",
        review_metadata=approval_metadata,
        task_id=None,
    )

    # Should still merge successfully
    assert len(merge_sha) == 40


def test_tag_rejected_without_task_id(temp_repo, approval_metadata):
    """Test tagging rejected branch without task_id."""
    controller = MergeController(temp_repo)

    # Create feature branch
    subprocess.run(
        ["git", "checkout", "-b", "review/some-task-code-review"],
        cwd=temp_repo,
        check=True,
        capture_output=True,
    )

    approval_metadata.decision = ReviewDecision.REJECTED

    # Tag without task_id (should extract from branch name)
    controller.tag_rejected(
        branch_name="review/some-task-code-review",
        review_metadata=approval_metadata,
        task_id=None,
    )

    # Should create tag based on branch name
    assert controller.tag_exists("review-rejected-some-task-code-review")
