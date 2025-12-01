"""
Unit tests for Prompt Versioning System.

Tests prompt version management, PIP application, and version history tracking.

Author: ASP Development Team
Date: November 25, 2025
"""

import pytest
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

from asp.models.postmortem import ProcessImprovementProposal, ProposedChange
from asp.prompts.prompt_versioner import PromptVersioner


@pytest.fixture
def prompts_dir(tmp_path):
    """Create temporary prompts directory with sample prompts."""
    prompts_dir = tmp_path / "prompts"
    prompts_dir.mkdir()

    # Create sample prompt file
    sample_prompt = prompts_dir / "code_agent_v1_generation.txt"
    sample_prompt.write_text(
        """You are a code generation agent.

Generate clean, secure code.

Follow Python best practices."""
    )

    return prompts_dir


@pytest.fixture
def approved_pip_add():
    """Create approved PIP with ADD change."""
    return ProcessImprovementProposal(
        proposal_id="PIP-001",
        task_id="TEST-001",
        created_at=datetime(2025, 11, 25, 10, 0, 0),
        analysis="Security vulnerabilities indicate Code Agent needs better guidance",
        proposed_changes=[
            ProposedChange(
                target_artifact="code_agent_prompt",
                change_type="add",
                proposed_content="SECURITY: Always use parameterized queries for SQL.",
                rationale="Prevent SQL injection vulnerabilities",
            )
        ],
        expected_impact="Reduce security vulnerabilities by 70%",
        hitl_status="approved",
        hitl_reviewer="security@example.com",
        hitl_reviewed_at=datetime(2025, 11, 25, 11, 0, 0),
        hitl_feedback="Approved - critical security improvement",
    )


@pytest.fixture
def approved_pip_modify():
    """Create approved PIP with MODIFY change."""
    return ProcessImprovementProposal(
        proposal_id="PIP-002",
        task_id="TEST-002",
        created_at=datetime(2025, 11, 25, 12, 0, 0),
        analysis="Best practices guidance is too vague",
        proposed_changes=[
            ProposedChange(
                target_artifact="code_agent_prompt",
                change_type="modify",
                current_content="Follow Python best practices.",
                proposed_content="Follow PEP 8 style guide and use type hints for all functions.",
                rationale="More specific guidance improves code quality",
            )
        ],
        expected_impact="Improve code quality by 40%",
        hitl_status="approved",
        hitl_reviewer="quality@example.com",
        hitl_reviewed_at=datetime(2025, 11, 25, 13, 0, 0),
        hitl_feedback="Approved - better specificity",
    )


@pytest.fixture
def approved_pip_remove():
    """Create approved PIP with REMOVE change."""
    return ProcessImprovementProposal(
        proposal_id="PIP-003",
        task_id="TEST-003",
        created_at=datetime(2025, 11, 25, 14, 0, 0),
        analysis="Outdated guidance should be removed",
        proposed_changes=[
            ProposedChange(
                target_artifact="code_agent_prompt",
                change_type="remove",
                current_content="Generate clean, secure code.",
                proposed_content="",
                rationale="Redundant with specific security guidelines",
            )
        ],
        expected_impact="Reduce prompt length by 10%",
        hitl_status="approved",
        hitl_reviewer="ops@example.com",
        hitl_reviewed_at=datetime(2025, 11, 25, 15, 0, 0),
        hitl_feedback="Approved - cleanup",
    )


class TestPromptVersioner:
    """Test PromptVersioner functionality."""

    def test_init_valid_directory(self, prompts_dir):
        """Test initialization with valid prompts directory."""
        versioner = PromptVersioner(prompts_dir)
        assert versioner.prompts_dir == prompts_dir
        assert versioner.version_history_file == prompts_dir / "VERSION_HISTORY.md"

    def test_init_invalid_directory(self, tmp_path):
        """Test initialization with invalid directory."""
        invalid_dir = tmp_path / "nonexistent"
        with pytest.raises(ValueError, match="Prompts directory not found"):
            PromptVersioner(invalid_dir)

    def test_find_prompt_file(self, prompts_dir):
        """Test finding latest prompt file version."""
        versioner = PromptVersioner(prompts_dir)

        # Should find code_agent_v1_generation.txt
        file_path, version = versioner._find_prompt_file("code_agent_prompt")
        assert file_path.name == "code_agent_v1_generation.txt"
        assert version == 1

    def test_find_prompt_file_not_found(self, prompts_dir):
        """Test error when prompt file not found."""
        versioner = PromptVersioner(prompts_dir)

        with pytest.raises(FileNotFoundError, match="No prompt file found"):
            versioner._find_prompt_file("nonexistent_prompt")

    def test_apply_add_change(self, prompts_dir, approved_pip_add):
        """Test applying ADD change to prompt."""
        versioner = PromptVersioner(prompts_dir)

        # Disable git commits for test
        with patch(
            "asp.prompts.prompt_versioner.is_git_repository", return_value=False
        ):
            results = versioner.apply_pip(approved_pip_add)

        # Verify new file was created
        assert "code_agent_prompt" in results
        new_file = Path(results["code_agent_prompt"])
        assert new_file.exists()
        assert new_file.name == "code_agent_v2_generation.txt"

        # Verify content
        content = new_file.read_text()
        assert "Prompt Version: v2" in content
        assert "PIP-001" in content
        assert "SECURITY: Always use parameterized queries for SQL." in content
        assert "Prevent SQL injection vulnerabilities" in content

    def test_apply_modify_change(self, prompts_dir, approved_pip_modify):
        """Test applying MODIFY change to prompt."""
        versioner = PromptVersioner(prompts_dir)

        with patch(
            "asp.prompts.prompt_versioner.is_git_repository", return_value=False
        ):
            results = versioner.apply_pip(approved_pip_modify)

        # Verify modification
        new_file = Path(results["code_agent_prompt"])
        content = new_file.read_text()
        assert "Follow PEP 8 style guide and use type hints" in content
        assert "Follow Python best practices." not in content

    def test_apply_remove_change(self, prompts_dir, approved_pip_remove):
        """Test applying REMOVE change to prompt."""
        versioner = PromptVersioner(prompts_dir)

        with patch(
            "asp.prompts.prompt_versioner.is_git_repository", return_value=False
        ):
            results = versioner.apply_pip(approved_pip_remove)

        # Verify removal
        new_file = Path(results["code_agent_prompt"])
        content = new_file.read_text()
        assert "Generate clean, secure code." not in content

    def test_apply_non_approved_pip(self, prompts_dir, approved_pip_add):
        """Test error when trying to apply non-approved PIP."""
        versioner = PromptVersioner(prompts_dir)

        # Change status to pending
        approved_pip_add.hitl_status = "pending"

        with pytest.raises(ValueError, match="Cannot apply non-approved PIP"):
            versioner.apply_pip(approved_pip_add)

    def test_dry_run(self, prompts_dir, approved_pip_add):
        """Test dry run mode (no files written)."""
        versioner = PromptVersioner(prompts_dir)

        with patch(
            "asp.prompts.prompt_versioner.is_git_repository", return_value=False
        ):
            results = versioner.apply_pip(approved_pip_add, dry_run=True)

        # Verify no new file was created
        new_file = Path(results["code_agent_prompt"])
        assert not new_file.exists()

    def test_version_history_created(self, prompts_dir, approved_pip_add):
        """Test version history file is created and updated."""
        versioner = PromptVersioner(prompts_dir)

        with patch(
            "asp.prompts.prompt_versioner.is_git_repository", return_value=False
        ):
            versioner.apply_pip(approved_pip_add)

        # Verify version history exists
        assert versioner.version_history_file.exists()

        # Verify content
        history = versioner.version_history_file.read_text()
        assert "# Prompt Version History" in history
        assert "PIP-001" in history
        assert "TEST-001" in history
        assert "security@example.com" in history
        assert "Security vulnerabilities" in history

    def test_multiple_pip_applications(
        self, prompts_dir, approved_pip_add, approved_pip_modify
    ):
        """Test applying multiple PIPs in sequence."""
        versioner = PromptVersioner(prompts_dir)

        with patch(
            "asp.prompts.prompt_versioner.is_git_repository", return_value=False
        ):
            # Apply first PIP
            results1 = versioner.apply_pip(approved_pip_add)
            assert (
                Path(results1["code_agent_prompt"]).name
                == "code_agent_v2_generation.txt"
            )

            # Apply second PIP
            results2 = versioner.apply_pip(approved_pip_modify)
            assert (
                Path(results2["code_agent_prompt"]).name
                == "code_agent_v3_generation.txt"
            )

            # Verify version history has both
            history = versioner.version_history_file.read_text()
            assert "PIP-001" in history
            assert "PIP-002" in history

    def test_generate_metadata_header(self, prompts_dir, approved_pip_add):
        """Test metadata header generation."""
        versioner = PromptVersioner(prompts_dir)

        header = versioner._generate_metadata_header(
            pip=approved_pip_add,
            change=approved_pip_add.proposed_changes[0],
            version=2,
        )

        assert "# Prompt Version: v2" in header
        assert "# Updated By: PIP-PIP-001" in header
        assert "# Change Type: ADD" in header
        assert "# Rationale: Prevent SQL injection" in header
        assert "# Reviewer: security@example.com" in header


class TestPromptVersionerIntegration:
    """Integration tests for prompt versioning."""

    def test_complete_versioning_workflow(
        self, prompts_dir, approved_pip_add, approved_pip_modify
    ):
        """Test complete workflow: original → v2 (add) → v3 (modify)."""
        versioner = PromptVersioner(prompts_dir)

        with patch(
            "asp.prompts.prompt_versioner.is_git_repository", return_value=False
        ):
            # Original prompt is v1
            original = (prompts_dir / "code_agent_v1_generation.txt").read_text()
            assert "Follow Python best practices." in original

            # Apply ADD change → v2
            versioner.apply_pip(approved_pip_add)
            v2_content = (prompts_dir / "code_agent_v2_generation.txt").read_text()
            assert "SECURITY: Always use parameterized queries" in v2_content
            assert "Follow Python best practices." in v2_content

            # Apply MODIFY change → v3
            versioner.apply_pip(approved_pip_modify)
            v3_content = (prompts_dir / "code_agent_v3_generation.txt").read_text()
            assert "PEP 8 style guide and use type hints" in v3_content
            assert "Follow Python best practices." not in v3_content

            # Version history should have both PIPs
            history = versioner.version_history_file.read_text()
            assert "PIP-001" in history
            assert "PIP-002" in history
