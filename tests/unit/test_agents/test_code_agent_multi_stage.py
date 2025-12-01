"""
Unit tests for Code Agent multi-stage generation (Phase 1: Manifest Generation).

Tests cover:
- File manifest generation with valid inputs
- Manifest validation
- Error handling
- JSON parsing from markdown fences
- Manifest content validation

Author: ASP Development Team
Date: November 20, 2025
"""

import json
from unittest.mock import MagicMock, patch

import pytest
from pydantic import ValidationError

from asp.agents.base_agent import AgentExecutionError
from asp.agents.code_agent import CodeAgent
from asp.models.code import CodeInput, FileManifest, FileMetadata
from asp.models.design import (
    APIContract,
    ComponentLogic,
    DataSchema,
    DesignSpecification,
)


# =============================================================================
# Test Fixtures
# =============================================================================


def create_test_design_specification(task_id="HELLO-WORLD-001"):
    """Create a simple test design specification for Hello World API."""
    from asp.models.design import DesignReviewChecklistItem

    return DesignSpecification(
        task_id=task_id,
        architecture_overview=(
            "FastAPI REST API with single /hello endpoint that returns a greeting message. "
            "Simple architecture with no database or authentication required. "
            "Uses standard FastAPI patterns with JSON responses."
        ),
        technology_stack={
            "language": "Python 3.12",
            "framework": "FastAPI 0.104",
            "testing": "pytest",
        },
        api_contracts=[
            APIContract(
                endpoint="/hello",
                method="GET",
                description="Returns a Hello World greeting message in JSON format",
                request_schema={},
                response_schema={
                    "message": "string - greeting message",
                },
                error_responses=[],
                authentication_required=False,
            )
        ],
        data_schemas=[],
        component_logic=[
            ComponentLogic(
                component_name="HelloAPI",
                semantic_unit_id="SU-001",
                responsibility="Provides single /hello endpoint that returns greeting message with proper JSON formatting",
                interfaces=[
                    {
                        "method": "hello",
                        "parameters": {},
                        "returns": "dict[str, str]",
                        "description": "Returns greeting message in dictionary format for JSON response",
                    }
                ],
                dependencies=[],
                implementation_notes="Simple FastAPI endpoint with no authentication or database requirements. Uses standard FastAPI routing.",
            )
        ],
        design_review_checklist=[
            DesignReviewChecklistItem(
                category="API Design",
                description="Verify endpoint follows REST conventions",
                validation_criteria="Endpoint uses standard HTTP methods and returns proper status codes",
                severity="High",
            ),
            DesignReviewChecklistItem(
                category="Error Handling",
                description="Verify proper error responses defined",
                validation_criteria="All error responses include status, code, and message fields",
                severity="High",
            ),
            DesignReviewChecklistItem(
                category="Security",
                description="Verify authentication requirements are appropriate",
                validation_criteria="Public endpoints do not require authentication",
                severity="Medium",
            ),
            DesignReviewChecklistItem(
                category="Performance",
                description="Verify response time requirements are reasonable",
                validation_criteria="Simple endpoints should respond in under 100ms",
                severity="Low",
            ),
            DesignReviewChecklistItem(
                category="Documentation",
                description="Verify API documentation is complete",
                validation_criteria="All endpoints have descriptions and schema definitions",
                severity="Medium",
            ),
        ],
        agent_version="1.0.0",
    )


def create_test_code_input(task_id="HELLO-WORLD-001"):
    """Create a test CodeInput."""
    design_spec = create_test_design_specification(task_id)
    return CodeInput(
        task_id=task_id,
        design_specification=design_spec,
        coding_standards="Follow PEP 8, use type hints, docstrings required",
        context_files=None,
    )


def create_mock_manifest_response():
    """Create a mock manifest response from the LLM."""
    return {
        "task_id": "HELLO-WORLD-001",
        "project_id": "DEMO-001",
        "files": [
            {
                "file_path": "main.py",
                "file_type": "source",
                "semantic_unit_id": "SU-001",
                "component_id": "COMP-001",
                "description": "FastAPI application with single /hello endpoint returning greeting message",
                "estimated_lines": 30,
                "dependencies": [],
            },
            {
                "file_path": "tests/test_main.py",
                "file_type": "test",
                "semantic_unit_id": "SU-001",
                "component_id": "COMP-001",
                "description": "Unit tests for /hello endpoint verifying response format and status code",
                "estimated_lines": 50,
                "dependencies": ["main.py"],
            },
            {
                "file_path": "requirements.txt",
                "file_type": "requirements",
                "semantic_unit_id": None,
                "component_id": None,
                "description": "Python dependencies including FastAPI, Uvicorn, and pytest",
                "estimated_lines": 5,
                "dependencies": [],
            },
            {
                "file_path": "README.md",
                "file_type": "documentation",
                "semantic_unit_id": None,
                "component_id": None,
                "description": "Setup and running instructions for the Hello World API",
                "estimated_lines": 40,
                "dependencies": [],
            },
        ],
        "dependencies": [
            "fastapi==0.104.1",
            "uvicorn==0.24.0",
            "pytest==7.4.3",
            "httpx==0.25.2",
        ],
        "setup_instructions": "1. pip install -r requirements.txt\n2. Run: uvicorn main:app --reload\n3. Test: pytest tests/ -v",
        "total_files": 4,
        "total_estimated_lines": 125,
    }


# =============================================================================
# Tests
# =============================================================================


@patch("asp.agents.code_agent.CodeAgent.load_prompt")
@patch("asp.agents.code_agent.CodeAgent.call_llm")
def test_generate_file_manifest_success(mock_call_llm, mock_load_prompt):
    """Test successful file manifest generation."""
    # Setup
    agent = CodeAgent()
    input_data = create_test_code_input()
    mock_load_prompt.return_value = "Test prompt template"

    # Mock LLM response with JSON content
    mock_response = create_mock_manifest_response()
    mock_call_llm.return_value = {"content": mock_response}

    # Execute
    manifest = agent._generate_file_manifest(input_data)

    # Verify
    assert isinstance(manifest, FileManifest)
    assert manifest.task_id == "HELLO-WORLD-001"
    assert manifest.total_files == 4
    assert manifest.total_estimated_lines == 125
    assert len(manifest.files) == 4
    assert len(manifest.dependencies) == 4

    # Verify file types
    file_types = {f.file_type for f in manifest.files}
    assert "source" in file_types
    assert "test" in file_types
    assert "requirements" in file_types
    assert "documentation" in file_types

    # Verify prompt was loaded
    mock_load_prompt.assert_called_once_with("code_agent_v2_manifest")

    # Verify LLM was called
    mock_call_llm.assert_called_once()
    call_kwargs = mock_call_llm.call_args[1]
    assert call_kwargs["max_tokens"] == 4000
    assert call_kwargs["temperature"] == 0.0


@patch("asp.agents.code_agent.CodeAgent.load_prompt")
@patch("asp.agents.code_agent.CodeAgent.call_llm")
def test_generate_file_manifest_with_markdown_fence(mock_call_llm, mock_load_prompt):
    """Test manifest generation when LLM returns JSON wrapped in markdown fence."""
    # Setup
    agent = CodeAgent()
    input_data = create_test_code_input()
    mock_load_prompt.return_value = "Test prompt template"

    # Mock LLM response with JSON in markdown fence
    mock_response = create_mock_manifest_response()
    json_string = json.dumps(mock_response, indent=2)
    mock_call_llm.return_value = {"content": f"```json\n{json_string}\n```"}

    # Execute
    manifest = agent._generate_file_manifest(input_data)

    # Verify
    assert isinstance(manifest, FileManifest)
    assert manifest.task_id == "HELLO-WORLD-001"
    assert manifest.total_files == 4


@patch("asp.agents.code_agent.CodeAgent.load_prompt")
@patch("asp.agents.code_agent.CodeAgent.call_llm")
def test_generate_file_manifest_calculates_totals(mock_call_llm, mock_load_prompt):
    """Test that manifest generation calculates total_files and total_estimated_lines if missing."""
    # Setup
    agent = CodeAgent()
    input_data = create_test_code_input()
    mock_load_prompt.return_value = "Test prompt template"

    # Mock LLM response without totals
    mock_response = create_mock_manifest_response()
    mock_response["total_files"] = 0  # Will be calculated
    mock_response["total_estimated_lines"] = 0  # Will be calculated
    mock_call_llm.return_value = {"content": mock_response}

    # Execute
    manifest = agent._generate_file_manifest(input_data)

    # Verify totals were calculated
    assert manifest.total_files == 4  # Should match len(files)
    assert manifest.total_estimated_lines == 125  # Sum of estimated_lines


@patch("asp.agents.code_agent.CodeAgent.load_prompt")
@patch("asp.agents.code_agent.CodeAgent.call_llm")
def test_generate_file_manifest_invalid_json(mock_call_llm, mock_load_prompt):
    """Test error handling when LLM returns invalid JSON."""
    # Setup
    agent = CodeAgent()
    input_data = create_test_code_input()
    mock_load_prompt.return_value = "Test prompt template"

    # Mock LLM response with invalid JSON
    mock_call_llm.return_value = {"content": "This is not JSON"}

    # Execute and verify error
    with pytest.raises(AgentExecutionError) as exc_info:
        agent._generate_file_manifest(input_data)

    assert "non-JSON response" in str(exc_info.value)


@patch("asp.agents.code_agent.CodeAgent.load_prompt")
@patch("asp.agents.code_agent.CodeAgent.call_llm")
def test_generate_file_manifest_missing_required_fields(
    mock_call_llm, mock_load_prompt
):
    """Test error handling when manifest response is missing required fields."""
    # Setup
    agent = CodeAgent()
    input_data = create_test_code_input()
    mock_load_prompt.return_value = "Test prompt template"

    # Mock LLM response missing required fields
    mock_response = {
        "task_id": "HELLO-WORLD-001",
        # Missing 'files', 'dependencies', 'setup_instructions', 'total_files'
    }
    mock_call_llm.return_value = {"content": mock_response}

    # Execute and verify error
    with pytest.raises(AgentExecutionError) as exc_info:
        agent._generate_file_manifest(input_data)

    assert "Manifest validation failed" in str(exc_info.value)


@patch("asp.agents.code_agent.CodeAgent.load_prompt")
def test_generate_file_manifest_prompt_not_found(mock_load_prompt):
    """Test error handling when manifest prompt template is not found."""
    # Setup
    agent = CodeAgent()
    input_data = create_test_code_input()
    mock_load_prompt.side_effect = FileNotFoundError("Prompt not found")

    # Execute and verify error
    with pytest.raises(AgentExecutionError) as exc_info:
        agent._generate_file_manifest(input_data)

    assert "Manifest prompt template not found" in str(exc_info.value)


@patch("asp.agents.code_agent.CodeAgent.load_prompt")
@patch("asp.agents.code_agent.CodeAgent.call_llm")
def test_generate_file_manifest_validates_file_metadata(
    mock_call_llm, mock_load_prompt
):
    """Test that manifest validates FileMetadata structure."""
    # Setup
    agent = CodeAgent()
    input_data = create_test_code_input()
    mock_load_prompt.return_value = "Test prompt template"

    # Mock LLM response with valid file metadata
    mock_response = create_mock_manifest_response()
    mock_call_llm.return_value = {"content": mock_response}

    # Execute
    manifest = agent._generate_file_manifest(input_data)

    # Verify all files have required metadata
    for file in manifest.files:
        assert isinstance(file, FileMetadata)
        assert file.file_path
        assert file.file_type
        assert file.description
        assert file.estimated_lines > 0
        assert isinstance(file.dependencies, list)


@patch("asp.agents.code_agent.CodeAgent.load_prompt")
@patch("asp.agents.code_agent.CodeAgent.call_llm")
def test_generate_file_manifest_handles_malformed_json_fence(
    mock_call_llm, mock_load_prompt
):
    """Test error handling when JSON in markdown fence is malformed."""
    # Setup
    agent = CodeAgent()
    input_data = create_test_code_input()
    mock_load_prompt.return_value = "Test prompt template"

    # Mock LLM response with malformed JSON in markdown fence
    mock_call_llm.return_value = {
        "content": '```json\n{"task_id": "TEST", "files": [invalid json\n```'
    }

    # Execute and verify error
    with pytest.raises(AgentExecutionError) as exc_info:
        agent._generate_file_manifest(input_data)

    assert "Failed to parse manifest JSON" in str(exc_info.value)


def test_file_metadata_validation():
    """Test FileMetadata Pydantic model validation."""
    # Valid metadata
    metadata = FileMetadata(
        file_path="src/api/auth.py",
        file_type="source",
        semantic_unit_id="SU-001",
        component_id="COMP-001",
        description="JWT authentication API endpoints with login and validation",
        estimated_lines=250,
        dependencies=["src/models/user.py"],
    )
    assert metadata.file_path == "src/api/auth.py"
    assert metadata.estimated_lines == 250

    # Invalid: missing required fields
    with pytest.raises(ValidationError):
        FileMetadata(
            file_path="test.py",
            # Missing file_type, description, estimated_lines
        )

    # Invalid: estimated_lines must be positive
    with pytest.raises(ValidationError):
        FileMetadata(
            file_path="test.py",
            file_type="source",
            description="Test file for validation",
            estimated_lines=0,  # Must be > 0
        )


def test_file_manifest_validation():
    """Test FileManifest Pydantic model validation."""
    # Valid manifest
    manifest = FileManifest(
        task_id="TEST-001",
        project_id="PROJECT-001",
        files=[
            FileMetadata(
                file_path="main.py",
                file_type="source",
                description="Main application entry point",
                estimated_lines=100,
            )
        ],
        dependencies=["fastapi==0.104.1"],
        setup_instructions="1. pip install -r requirements.txt\n2. Run: uvicorn main:app",
        total_files=1,
        total_estimated_lines=100,
    )
    assert manifest.task_id == "TEST-001"
    assert len(manifest.files) == 1

    # Invalid: empty files list
    with pytest.raises(ValidationError):
        FileManifest(
            task_id="TEST-001",
            files=[],  # Must have at least 1 file
            dependencies=[],
            setup_instructions="Test",
            total_files=0,
        )

    # Invalid: total_files must be positive
    with pytest.raises(ValidationError):
        FileManifest(
            task_id="TEST-001",
            files=[
                FileMetadata(
                    file_path="test.py",
                    file_type="source",
                    description="Test file",
                    estimated_lines=50,
                )
            ],
            dependencies=[],
            setup_instructions="Test",
            total_files=0,  # Must be > 0
        )
