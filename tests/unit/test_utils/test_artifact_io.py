"""
Unit tests for artifact I/O utilities.

Tests artifact persistence functionality including:
- Writing JSON artifacts
- Writing Markdown artifacts
- Writing generated code files
- Reading artifacts back
- Directory management
- Error handling
"""

import json
import tempfile
from pathlib import Path

import pytest
from pydantic import BaseModel

from asp.models.code import GeneratedCode, GeneratedFile
from asp.models.design import DesignSpecification
from asp.models.planning import ProjectPlan, SemanticUnit, TaskRequirements
from asp.utils.artifact_io import (
    ArtifactIOError,
    artifact_exists,
    ensure_artifact_directory,
    list_task_artifacts,
    read_artifact_json,
    write_artifact_json,
    write_artifact_markdown,
    write_generated_file,
)


class TestEnsureArtifactDirectory:
    """Test artifact directory creation."""

    def test_creates_directory_if_not_exists(self, tmp_path):
        """Test that directory is created if it doesn't exist."""
        task_id = "TEST-001"
        artifact_dir = tmp_path / "artifacts" / task_id

        # Should not exist initially
        assert not artifact_dir.exists()

        # Create directory
        result = ensure_artifact_directory(task_id, base_path=str(tmp_path))

        # Should exist now
        assert artifact_dir.exists()
        assert artifact_dir.is_dir()
        assert result == artifact_dir

    def test_returns_existing_directory(self, tmp_path):
        """Test that existing directory is returned."""
        task_id = "TEST-002"
        artifact_dir = tmp_path / "artifacts" / task_id
        artifact_dir.mkdir(parents=True)

        # Directory already exists
        assert artifact_dir.exists()

        # Should return existing directory
        result = ensure_artifact_directory(task_id, base_path=str(tmp_path))

        assert result == artifact_dir
        assert artifact_dir.exists()

    def test_creates_parent_directories(self, tmp_path):
        """Test that parent directories are created."""
        task_id = "TEST-003"

        # Artifacts directory doesn't exist
        assert not (tmp_path / "artifacts").exists()

        # Should create both artifacts/ and artifacts/TEST-003/
        result = ensure_artifact_directory(task_id, base_path=str(tmp_path))

        assert result.exists()
        assert result.parent.exists()  # artifacts/ directory


class TestWriteArtifactJson:
    """Test JSON artifact writing."""

    def test_writes_pydantic_model_to_json(self, tmp_path):
        """Test writing a Pydantic model to JSON."""
        task_id = "TEST-004"

        # Create a simple Pydantic model
        requirements = TaskRequirements(
            task_id=task_id,
            description="Test task for artifact I/O",
            requirements="Build something that meets the minimum requirements for testing",
        )

        # Write to JSON
        json_path = write_artifact_json(
            task_id=task_id,
            artifact_type="plan",
            data=requirements,
            base_path=str(tmp_path),
        )

        # Verify file exists
        assert json_path.exists()
        assert json_path.name == "plan.json"

        # Verify content
        with open(json_path) as f:
            content = json.load(f)

        assert content["task_id"] == task_id
        assert content["description"] == "Test task for artifact I/O"
        assert "Build something" in content["requirements"]

    def test_overwrites_existing_file(self, tmp_path):
        """Test that existing JSON file is overwritten."""
        task_id = "TEST-005"

        # Create first version
        data1 = TaskRequirements(
            task_id=task_id,
            description="First version for testing",
            requirements="Version 1 requirements with sufficient length for validation",
        )
        json_path = write_artifact_json(
            task_id=task_id,
            artifact_type="plan",
            data=data1,
            base_path=str(tmp_path),
        )

        # Overwrite with second version
        data2 = TaskRequirements(
            task_id=task_id,
            description="Second version for testing",
            requirements="Version 2 requirements with sufficient length for validation",
        )
        json_path2 = write_artifact_json(
            task_id=task_id,
            artifact_type="plan",
            data=data2,
            base_path=str(tmp_path),
        )

        # Should be same path
        assert json_path == json_path2

        # Verify content is from second version
        with open(json_path2) as f:
            content = json.load(f)

        assert content["description"] == "Second version for testing"
        assert "Version 2" in content["requirements"]

    def test_pretty_prints_json(self, tmp_path):
        """Test that JSON is pretty-printed with indentation."""
        task_id = "TEST-006"

        data = TaskRequirements(
            task_id=task_id,
            description="Test task for pretty printing",
            requirements="Requirements for pretty print testing with sufficient length",
        )

        json_path = write_artifact_json(
            task_id=task_id,
            artifact_type="plan",
            data=data,
            base_path=str(tmp_path),
        )

        # Read raw content
        content = json_path.read_text()

        # Should have newlines and indentation
        assert "\n" in content
        assert "  " in content  # Indentation


class TestWriteArtifactMarkdown:
    """Test Markdown artifact writing."""

    def test_writes_markdown_content(self, tmp_path):
        """Test writing markdown content to file."""
        task_id = "TEST-007"
        markdown_content = "# Test\n\nThis is a test."

        md_path = write_artifact_markdown(
            task_id=task_id,
            artifact_type="plan",
            markdown_content=markdown_content,
            base_path=str(tmp_path),
        )

        # Verify file exists
        assert md_path.exists()
        assert md_path.name == "plan.md"

        # Verify content
        content = md_path.read_text()
        assert content == markdown_content

    def test_overwrites_existing_markdown(self, tmp_path):
        """Test that existing Markdown file is overwritten."""
        task_id = "TEST-008"

        # Write first version
        md_path1 = write_artifact_markdown(
            task_id=task_id,
            artifact_type="plan",
            markdown_content="Version 1",
            base_path=str(tmp_path),
        )

        # Overwrite with second version
        md_path2 = write_artifact_markdown(
            task_id=task_id,
            artifact_type="plan",
            markdown_content="Version 2",
            base_path=str(tmp_path),
        )

        # Should be same path
        assert md_path1 == md_path2

        # Verify content is from second version
        content = md_path2.read_text()
        assert content == "Version 2"


class TestWriteGeneratedFile:
    """Test writing generated code files."""

    def test_writes_source_file_to_src(self, tmp_path):
        """Test writing a source file to src/ directory."""
        task_id = "TEST-009"

        file = GeneratedFile(
            file_path="src/main.py",
            file_type="source",
            description="Main entry point module for the application",
            content="print('Hello')",
            lines_of_code=1,
            component_id="COMP-001",
        )

        file_path = write_generated_file(
            task_id=task_id,
            file=file,
            base_path=str(tmp_path),
        )

        # Verify file exists in correct location
        assert file_path.exists()
        assert file_path == tmp_path / "src" / "main.py"

        # Verify content
        content = file_path.read_text()
        assert content == "print('Hello')"

    def test_writes_test_file_to_tests(self, tmp_path):
        """Test writing a test file to tests/ directory."""
        task_id = "TEST-010"

        file = GeneratedFile(
            file_path="tests/test_main.py",
            file_type="test",
            description="Unit tests for the main module functionality",
            content="def test_main():\n    pass",
            lines_of_code=2,
            component_id="COMP-001",
        )

        file_path = write_generated_file(
            task_id=task_id,
            file=file,
            base_path=str(tmp_path),
        )

        # Verify file exists in correct location
        assert file_path.exists()
        assert file_path == tmp_path / "tests" / "test_main.py"

        # Verify content
        content = file_path.read_text()
        assert content == "def test_main():\n    pass"

    def test_creates_parent_directories(self, tmp_path):
        """Test that parent directories are created for generated files."""
        task_id = "TEST-011"

        file = GeneratedFile(
            file_path="src/api/controllers/user.py",
            file_type="source",
            description="User controller for handling user-related requests",
            content="class UserController: pass",
            lines_of_code=1,
            component_id="COMP-001",
        )

        file_path = write_generated_file(
            task_id=task_id,
            file=file,
            base_path=str(tmp_path),
        )

        # Verify all parent directories exist
        assert file_path.parent.exists()  # src/api/controllers/
        assert file_path.parent.parent.exists()  # src/api/
        assert file_path.parent.parent.parent.exists()  # src/

    def test_overwrites_existing_file(self, tmp_path):
        """Test that existing generated file is overwritten."""
        task_id = "TEST-012"

        file1 = GeneratedFile(
            file_path="src/app.py",
            file_type="source",
            description="Main application module version 1",
            content="# Version 1",
            lines_of_code=1,
            component_id="COMP-001",
        )

        file_path1 = write_generated_file(
            task_id=task_id,
            file=file1,
            base_path=str(tmp_path),
        )

        # Overwrite with new content
        file2 = GeneratedFile(
            file_path="src/app.py",
            file_type="source",
            description="Main application module version 2",
            content="# Version 2",
            lines_of_code=1,
            component_id="COMP-001",
        )

        file_path2 = write_generated_file(
            task_id=task_id,
            file=file2,
            base_path=str(tmp_path),
        )

        # Should be same path
        assert file_path1 == file_path2

        # Verify content is from second version
        content = file_path2.read_text()
        assert content == "# Version 2"


class TestReadArtifactJson:
    """Test reading JSON artifacts."""

    def test_reads_json_artifact(self, tmp_path):
        """Test reading a JSON artifact."""
        task_id = "TEST-013"

        # Write artifact first
        data = TaskRequirements(
            task_id=task_id,
            description="Test task for reading artifacts",
            requirements="Build it with sufficient requirements text for validation",
        )

        write_artifact_json(
            task_id=task_id,
            artifact_type="plan",
            data=data,
            base_path=str(tmp_path),
        )

        # Read it back
        result = read_artifact_json(
            task_id=task_id,
            artifact_type="plan",
            base_path=str(tmp_path),
        )

        # Verify it matches original (returns dict, not Pydantic model)
        assert isinstance(result, dict)
        assert result["task_id"] == task_id
        assert result["description"] == "Test task for reading artifacts"
        assert "Build it" in result["requirements"]

    def test_raises_error_if_file_not_found(self, tmp_path):
        """Test that error is raised if artifact doesn't exist."""
        with pytest.raises(ArtifactIOError, match="Artifact file not found"):
            read_artifact_json(
                task_id="NONEXISTENT",
                artifact_type="plan",
                base_path=str(tmp_path),
            )

    def test_raises_error_on_invalid_json(self, tmp_path):
        """Test that error is raised if JSON is invalid."""
        task_id = "TEST-014"

        # Create invalid JSON file
        artifact_dir = ensure_artifact_directory(task_id, base_path=str(tmp_path))
        json_path = artifact_dir / "plan.json"
        json_path.write_text("{invalid json")

        # Should raise error
        with pytest.raises(ArtifactIOError, match="Invalid JSON"):
            read_artifact_json(
                task_id=task_id,
                artifact_type="plan",
                base_path=str(tmp_path),
            )


class TestArtifactExists:
    """Test artifact existence checking."""

    def test_returns_true_if_exists(self, tmp_path):
        """Test returns True if artifact exists."""
        task_id = "TEST-015"

        # Create artifact
        write_artifact_json(
            task_id=task_id,
            artifact_type="plan",
            data=TaskRequirements(
                task_id=task_id,
                description="Test artifact existence check",
                requirements="Requirements text with sufficient length for validation"
            ),
            base_path=str(tmp_path),
        )

        # Check existence
        assert artifact_exists(task_id, "plan", base_path=str(tmp_path)) is True

    def test_returns_false_if_not_exists(self, tmp_path):
        """Test returns False if artifact doesn't exist."""
        assert artifact_exists("NONEXISTENT", "plan", base_path=str(tmp_path)) is False

    def test_returns_false_if_task_directory_not_exists(self, tmp_path):
        """Test returns False if task directory doesn't exist."""
        assert artifact_exists("NONEXISTENT", "plan", base_path=str(tmp_path)) is False


class TestListTaskArtifacts:
    """Test listing task artifacts."""

    def test_lists_all_artifacts_for_task(self, tmp_path):
        """Test listing all artifacts for a task."""
        task_id = "TEST-016"

        # Create multiple artifacts
        write_artifact_json(
            task_id=task_id,
            artifact_type="plan",
            data=TaskRequirements(
                task_id=task_id,
                description="Test listing task artifacts",
                requirements="Requirements text with sufficient length for validation"
            ),
            base_path=str(tmp_path),
        )

        write_artifact_markdown(
            task_id=task_id,
            artifact_type="plan",
            markdown_content="# Plan",
            base_path=str(tmp_path),
        )

        write_artifact_markdown(
            task_id=task_id,
            artifact_type="design",
            markdown_content="# Design",
            base_path=str(tmp_path),
        )

        # List artifacts
        artifacts = list_task_artifacts(task_id, base_path=str(tmp_path))

        # Should have 3 files
        assert len(artifacts) == 3

        # Check filenames (artifacts is a list of filenames, not Path objects)
        assert "plan.json" in artifacts
        assert "plan.md" in artifacts
        assert "design.md" in artifacts

    def test_returns_empty_list_if_no_artifacts(self, tmp_path):
        """Test returns empty list if task has no artifacts."""
        artifacts = list_task_artifacts("NONEXISTENT", base_path=str(tmp_path))
        assert artifacts == []

    def test_returns_empty_list_if_directory_not_exists(self, tmp_path):
        """Test returns empty list if task directory doesn't exist."""
        artifacts = list_task_artifacts("NONEXISTENT", base_path=str(tmp_path))
        assert artifacts == []
