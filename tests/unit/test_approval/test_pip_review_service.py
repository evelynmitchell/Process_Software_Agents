"""
Unit tests for PIP Review Service.

Tests PIP review workflow, decision collection, and PIP status updates.

Author: ASP Development Team
Date: November 25, 2025
"""

import pytest
from datetime import datetime
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from asp.approval.pip_review_service import PIPReviewCollector, PIPReviewService
from asp.models.postmortem import ProcessImprovementProposal, ProposedChange


@pytest.fixture
def sample_pip():
    """Create sample PIP for testing."""
    return ProcessImprovementProposal(
        proposal_id="PIP-001",
        task_id="TEST-001",
        created_at=datetime(2025, 11, 25, 10, 0, 0),
        analysis="Security vulnerabilities indicate Code Agent needs better security guidance",
        proposed_changes=[
            ProposedChange(
                target_artifact="code_agent_prompt",
                change_type="add",
                proposed_content="SECURITY: Use parameterized queries for all SQL",
                rationale="Prevent SQL injection vulnerabilities"
            )
        ],
        expected_impact="Reduce security vulnerabilities by 70%",
        hitl_status="pending",
    )


class TestPIPReviewCollector:
    """Test PIPReviewCollector functionality."""

    def test_review_pip_approve(self, sample_pip, tmp_path, monkeypatch):
        """Test approving a PIP."""
        # Mock user input
        inputs = iter(['1', 'Looks good, security improvement needed'])
        monkeypatch.setattr('builtins.input', lambda _: next(inputs))

        # Mock git config
        mock_run = Mock()
        mock_run.stdout = "reviewer@example.com\n"
        monkeypatch.setattr('subprocess.run', lambda *args, **kwargs: mock_run)

        # Mock artifacts directory
        artifacts_dir = tmp_path / "artifacts"
        artifacts_dir.mkdir()
        task_dir = artifacts_dir / sample_pip.task_id
        task_dir.mkdir()

        # Create collector
        collector = PIPReviewCollector()

        # Review PIP
        with patch('asp.utils.artifact_io.write_artifact_json'):
            updated_pip = collector.review_pip(sample_pip)

        # Verify decision
        assert updated_pip.hitl_status == "approved"
        assert updated_pip.hitl_reviewer == "reviewer@example.com"
        assert updated_pip.hitl_feedback == "Looks good, security improvement needed"
        assert updated_pip.hitl_reviewed_at is not None

    def test_review_pip_reject(self, sample_pip, monkeypatch):
        """Test rejecting a PIP."""
        # Mock user input
        inputs = iter(['2', 'Not enough evidence for 70% reduction'])
        monkeypatch.setattr('builtins.input', lambda _: next(inputs))

        # Mock git config failure (use fallback)
        def mock_subprocess_run(*args, **kwargs):
            from subprocess import CalledProcessError
            raise CalledProcessError(1, 'git')

        monkeypatch.setattr('subprocess.run', mock_subprocess_run)
        monkeypatch.setattr('getpass.getuser', lambda: 'testuser')

        # Create collector
        collector = PIPReviewCollector()

        # Review PIP
        with patch('asp.utils.artifact_io.write_artifact_json'):
            updated_pip = collector.review_pip(sample_pip)

        # Verify decision
        assert updated_pip.hitl_status == "rejected"
        assert updated_pip.hitl_reviewer == "testuser@local"
        assert updated_pip.hitl_feedback == "Not enough evidence for 70% reduction"

    def test_review_pip_needs_revision(self, sample_pip, monkeypatch):
        """Test requesting revision for a PIP."""
        # Mock user input
        inputs = iter(['3', 'Please add more specific security examples'])
        monkeypatch.setattr('builtins.input', lambda _: next(inputs))

        # Mock reviewer
        collector = PIPReviewCollector()

        # Review PIP
        with patch('asp.utils.artifact_io.write_artifact_json'):
            updated_pip = collector.review_pip(sample_pip, reviewer="test@example.com")

        # Verify decision
        assert updated_pip.hitl_status == "needs_revision"
        assert updated_pip.hitl_reviewer == "test@example.com"
        assert updated_pip.hitl_feedback == "Please add more specific security examples"


class TestPIPReviewService:
    """Test PIPReviewService functionality."""

    def test_review_pip_by_id(self, sample_pip, monkeypatch, tmp_path):
        """Test loading and reviewing PIP by ID."""
        # Mock PIP loading
        mock_read = Mock(return_value=sample_pip.model_dump())

        # Mock user input
        inputs = iter(['1', 'Approved'])
        monkeypatch.setattr('builtins.input', lambda _: next(inputs))

        # Create service
        service = PIPReviewService()

        # Review PIP
        with patch('asp.utils.artifact_io.read_artifact_json', mock_read):
            with patch('asp.utils.artifact_io.write_artifact_json'):
                updated_pip = service.review_pip_by_id("TEST-001", reviewer="test@example.com")

        # Verify
        assert updated_pip.hitl_status == "approved"
        assert updated_pip.hitl_reviewer == "test@example.com"
        mock_read.assert_called_once_with("TEST-001", "pip")

    def test_list_pending_pips(self, tmp_path):
        """Test listing pending PIPs."""
        # Create artifacts directory with sample PIPs
        artifacts_dir = tmp_path / "artifacts"
        artifacts_dir.mkdir()

        # Create pending PIP
        pending_dir = artifacts_dir / "TASK-001"
        pending_dir.mkdir()
        pending_pip = ProcessImprovementProposal(
            proposal_id="PIP-001",
            task_id="TASK-001",
            created_at=datetime.now(),
            analysis="Test",
            proposed_changes=[
                ProposedChange(
                    target_artifact="test",
                    change_type="add",
                    proposed_content="Test",
                    rationale="Test"
                )
            ],
            expected_impact="Test",
            hitl_status="pending",
        )
        (pending_dir / "pip.json").write_text(pending_pip.model_dump_json())

        # Create approved PIP
        approved_dir = artifacts_dir / "TASK-002"
        approved_dir.mkdir()
        approved_pip = ProcessImprovementProposal(
            proposal_id="PIP-002",
            task_id="TASK-002",
            created_at=datetime.now(),
            analysis="Test",
            proposed_changes=[
                ProposedChange(
                    target_artifact="test",
                    change_type="add",
                    proposed_content="Test",
                    rationale="Test"
                )
            ],
            expected_impact="Test",
            hitl_status="approved",
        )
        (approved_dir / "pip.json").write_text(approved_pip.model_dump_json())

        # Create service
        service = PIPReviewService()

        # List pending PIPs
        pending = service.list_pending_pips(artifacts_dir)

        # Verify only pending PIP is listed
        assert len(pending) == 1
        assert "TASK-001" in pending
        assert "TASK-002" not in pending

    def test_list_pending_pips_empty(self, tmp_path):
        """Test listing pending PIPs when none exist."""
        artifacts_dir = tmp_path / "artifacts"
        artifacts_dir.mkdir()

        service = PIPReviewService()
        pending = service.list_pending_pips(artifacts_dir)

        assert pending == []


class TestPIPReviewIntegration:
    """Integration tests for PIP review workflow."""

    def test_complete_review_workflow(self, sample_pip, tmp_path, monkeypatch):
        """Test complete workflow from PIP creation to approval."""
        # Setup artifacts directory
        artifacts_dir = tmp_path / "artifacts"
        artifacts_dir.mkdir()
        task_dir = artifacts_dir / sample_pip.task_id
        task_dir.mkdir()

        # Write initial PIP
        pip_file = task_dir / "pip.json"
        pip_file.write_text(sample_pip.model_dump_json())

        # Mock user input (approve)
        inputs = iter(['1', 'Security improvement approved'])
        monkeypatch.setattr('builtins.input', lambda _: next(inputs))

        # Create service
        service = PIPReviewService()

        # Review PIP
        with patch('asp.utils.artifact_io.ARTIFACTS_DIR', artifacts_dir):
            updated_pip = service.review_pip_by_id(
                sample_pip.task_id,
                reviewer="security@example.com"
            )

        # Verify workflow
        assert updated_pip.proposal_id == sample_pip.proposal_id
        assert updated_pip.hitl_status == "approved"
        assert updated_pip.hitl_reviewer == "security@example.com"
        assert updated_pip.hitl_feedback == "Security improvement approved"
