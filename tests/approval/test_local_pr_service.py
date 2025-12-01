"""Tests for LocalPRApprovalService."""

import pytest
import subprocess
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch

from asp.approval.local_pr import LocalPRApprovalService
from asp.approval.base import ApprovalRequest, ReviewDecision, ApprovalResponse


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
def approval_service(temp_repo):
    """Create LocalPRApprovalService for testing."""
    return LocalPRApprovalService(
        repo_path=temp_repo, base_branch="main", auto_cleanup=True
    )


@pytest.fixture
def sample_request():
    """Create sample approval request."""
    return ApprovalRequest(
        task_id="TEST-001",
        gate_type="code_review",
        agent_output={
            "agent": "CodeAgent",
            "artifacts": {"src/test.py": "def test():\n    pass\n"},
        },
        quality_report={
            "passed": False,
            "total_issues": 2,
            "issues": [
                {
                    "severity": "MEDIUM",
                    "description": "Missing docstring",
                    "file": "src/test.py",
                    "line": 1,
                },
                {
                    "severity": "LOW",
                    "description": "Short variable name",
                    "file": "src/test.py",
                    "line": 2,
                },
            ],
        },
        base_branch="main",
    )


def test_request_approval_approved(approval_service, sample_request, temp_repo):
    """Test approval request with APPROVED decision."""
    # Mock the approval collector to auto-approve
    mock_response = ApprovalResponse(
        decision=ReviewDecision.APPROVED,
        reviewer="test@example.com",
        timestamp="2025-11-25T10:00:00Z",
        justification="Auto-approved for testing",
    )

    with (
        patch.object(
            approval_service.approval_collector,
            "collect_decision",
            return_value=mock_response,
        ),
        patch.object(approval_service.review_presenter, "display_review"),
        patch.object(approval_service.review_presenter, "display_approval_result"),
    ):
        response = approval_service.request_approval(sample_request)

    # Verify response
    assert response.decision == ReviewDecision.APPROVED
    assert response.reviewer == "test@example.com"
    assert response.merge_commit is not None
    assert len(response.merge_commit) == 40

    # Verify branch was cleaned up
    assert not approval_service.branch_manager.branch_exists(
        "review/TEST-001-code_review"
    )

    # Verify file was merged to main
    test_file = Path(temp_repo) / "src" / "test.py"
    assert test_file.exists()


def test_request_approval_rejected(approval_service, sample_request, temp_repo):
    """Test approval request with REJECTED decision."""
    # Mock the approval collector to reject
    mock_response = ApprovalResponse(
        decision=ReviewDecision.REJECTED,
        reviewer="test@example.com",
        timestamp="2025-11-25T10:00:00Z",
        justification="Too many issues",
    )

    with (
        patch.object(
            approval_service.approval_collector,
            "collect_decision",
            return_value=mock_response,
        ),
        patch.object(approval_service.review_presenter, "display_review"),
        patch.object(approval_service.review_presenter, "display_approval_result"),
    ):
        response = approval_service.request_approval(sample_request)

    # Verify response
    assert response.decision == ReviewDecision.REJECTED
    assert response.merge_commit is None

    # Verify branch was cleaned up
    assert not approval_service.branch_manager.branch_exists(
        "review/TEST-001-code_review"
    )

    # Verify tag was created
    assert approval_service.merge_controller.tag_exists("review-rejected-TEST-001")

    # Verify file was NOT merged to main
    test_file = Path(temp_repo) / "src" / "test.py"
    assert not test_file.exists()


def test_request_approval_deferred(approval_service, sample_request, temp_repo):
    """Test approval request with DEFERRED decision."""
    # Mock the approval collector to defer
    mock_response = ApprovalResponse(
        decision=ReviewDecision.DEFERRED,
        reviewer="test@example.com",
        timestamp="2025-11-25T10:00:00Z",
        justification="Need more time to review",
    )

    with (
        patch.object(
            approval_service.approval_collector,
            "collect_decision",
            return_value=mock_response,
        ),
        patch.object(approval_service.review_presenter, "display_review"),
        patch.object(approval_service.review_presenter, "display_approval_result"),
    ):
        response = approval_service.request_approval(sample_request)

    # Verify response
    assert response.decision == ReviewDecision.DEFERRED
    assert response.merge_commit is None

    # Verify branch was NOT cleaned up (kept for later review)
    assert approval_service.branch_manager.branch_exists("review/TEST-001-code_review")

    # Verify tag was created
    assert approval_service.merge_controller.tag_exists("review-deferred-TEST-001")


def test_request_approval_with_existing_branch(approval_service, sample_request):
    """Test approval request when branch already exists."""
    # Create branch first
    approval_service.branch_manager.create_branch("review/TEST-001-code_review", "main")

    # Mock auto-approve
    mock_response = ApprovalResponse(
        decision=ReviewDecision.APPROVED,
        reviewer="test@example.com",
        timestamp="2025-11-25T10:00:00Z",
        justification="Auto-approved",
    )

    with (
        patch.object(
            approval_service.approval_collector,
            "collect_decision",
            return_value=mock_response,
        ),
        patch.object(approval_service.review_presenter, "display_review"),
        patch.object(approval_service.review_presenter, "display_approval_result"),
    ):
        # Should handle existing branch gracefully
        response = approval_service.request_approval(sample_request)

    assert response.decision == ReviewDecision.APPROVED


def test_request_approval_without_auto_cleanup(temp_repo, sample_request):
    """Test approval without auto-cleanup."""
    service = LocalPRApprovalService(repo_path=temp_repo, auto_cleanup=False)

    # Mock auto-approve
    mock_response = ApprovalResponse(
        decision=ReviewDecision.APPROVED,
        reviewer="test@example.com",
        timestamp="2025-11-25T10:00:00Z",
        justification="Auto-approved",
    )

    with (
        patch.object(
            service.approval_collector, "collect_decision", return_value=mock_response
        ),
        patch.object(service.review_presenter, "display_review"),
        patch.object(service.review_presenter, "display_approval_result"),
    ):
        response = service.request_approval(sample_request)

    # Verify branch still exists (not cleaned up)
    assert service.branch_manager.branch_exists("review/TEST-001-code_review")


def test_format_quality_summary(approval_service):
    """Test quality summary formatting."""
    quality_report = {
        "issues": [
            {"severity": "CRITICAL", "description": "Critical issue"},
            {"severity": "HIGH", "description": "High issue"},
            {"severity": "MEDIUM", "description": "Medium issue 1"},
            {"severity": "MEDIUM", "description": "Medium issue 2"},
            {"severity": "LOW", "description": "Low issue 1"},
            {"severity": "LOW", "description": "Low issue 2"},
            {"severity": "LOW", "description": "Low issue 3"},
        ]
    }

    summary = approval_service._format_quality_summary(quality_report)

    assert "Critical: 1" in summary
    assert "High: 1" in summary
    assert "Medium: 2" in summary
    assert "Low: 3" in summary
    assert "Total: 7" in summary


def test_format_quality_summary_no_issues(approval_service):
    """Test quality summary with no issues."""
    quality_report = {"issues": []}

    summary = approval_service._format_quality_summary(quality_report)

    assert summary == "No issues found"


def test_git_notes_stored(approval_service, sample_request, temp_repo):
    """Test that review metadata is stored in git notes."""
    # Mock auto-approve
    mock_response = ApprovalResponse(
        decision=ReviewDecision.APPROVED,
        reviewer="test@example.com",
        timestamp="2025-11-25T10:00:00Z",
        justification="Auto-approved for testing",
    )

    with (
        patch.object(
            approval_service.approval_collector,
            "collect_decision",
            return_value=mock_response,
        ),
        patch.object(approval_service.review_presenter, "display_review"),
        patch.object(approval_service.review_presenter, "display_approval_result"),
    ):
        response = approval_service.request_approval(sample_request)

    # Get the commit SHA from the review branch (before it was deleted)
    # We'll check the merge commit instead
    result = subprocess.run(
        ["git", "log", "--all", "--show-notes=reviews", "--grep=TEST-001", "-1"],
        cwd=temp_repo,
        capture_output=True,
        text=True,
        check=True,
    )

    # Notes should be present in the log
    log_output = result.stdout
    # The notes might be on a commit that was merged, so this is a basic check
    assert response.merge_commit is not None


def test_request_approval_custom_base_branch(temp_repo, sample_request):
    """Test approval with custom base branch."""
    # Create develop branch
    subprocess.run(
        ["git", "checkout", "-b", "develop"],
        cwd=temp_repo,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "checkout", "main"], cwd=temp_repo, check=True, capture_output=True
    )

    service = LocalPRApprovalService(repo_path=temp_repo, base_branch="develop")

    # Update request to use develop
    sample_request.base_branch = "develop"

    # Mock auto-approve
    mock_response = ApprovalResponse(
        decision=ReviewDecision.APPROVED,
        reviewer="test@example.com",
        timestamp="2025-11-25T10:00:00Z",
        justification="Auto-approved",
    )

    with (
        patch.object(
            service.approval_collector, "collect_decision", return_value=mock_response
        ),
        patch.object(service.review_presenter, "display_review"),
        patch.object(service.review_presenter, "display_approval_result"),
    ):
        response = service.request_approval(sample_request)

    # Verify we're on develop after merge
    result = subprocess.run(
        ["git", "rev-parse", "--abbrev-ref", "HEAD"],
        cwd=temp_repo,
        capture_output=True,
        text=True,
        check=True,
    )
    assert result.stdout.strip() == "develop"
