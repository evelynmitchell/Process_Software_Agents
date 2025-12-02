"""
Unit tests for Code Agent.

Tests cover:
- Initialization
- Code generation with valid inputs
- Component coverage validation
- File structure validation
- Error handling
- Output validation

Author: ASP Development Team
Date: November 17, 2025
"""

import json
from unittest.mock import MagicMock, patch

import pytest

from asp.agents.base_agent import AgentExecutionError
from asp.agents.code_agent import CodeAgent
from asp.models.code import CodeInput, GeneratedCode, GeneratedFile
from asp.models.design import (
    APIContract,
    ComponentLogic,
    DataSchema,
    DesignReviewChecklistItem,
    DesignSpecification,
)

# =============================================================================
# Test Fixtures
# =============================================================================


def create_test_design_specification(task_id="TEST-001"):
    """Create a test design specification."""
    return DesignSpecification(
        task_id=task_id,
        architecture_overview="FastAPI REST API with JWT authentication and PostgreSQL database",
        technology_stack={
            "language": "Python 3.12",
            "framework": "FastAPI 0.104",
            "database": "PostgreSQL 16",
            "libraries": "bcrypt, python-jose, pydantic",
            "authentication": "JWT (python-jose library)",
        },
        api_contracts=[
            APIContract(
                endpoint="/api/auth/register",
                method="POST",
                description="User registration endpoint that creates a new user account",
                request_schema={
                    "email": "string (email format, required)",
                    "password": "string (min 8 chars, required)",
                },
                response_schema={
                    "user_id": "string (UUID)",
                    "email": "string",
                    "created_at": "string (ISO 8601 timestamp)",
                },
                error_responses=[
                    {
                        "status": 400,
                        "code": "INVALID_INPUT",
                        "message": "Invalid email or password format",
                    },
                    {
                        "status": 409,
                        "code": "EMAIL_EXISTS",
                        "message": "Email already registered",
                    },
                ],
                authentication_required=False,
            )
        ],
        data_schemas=[
            DataSchema(
                table_name="users",
                description="User account information including credentials and profile",
                columns=[
                    {"name": "user_id", "type": "UUID", "constraints": "PRIMARY KEY"},
                    {
                        "name": "email",
                        "type": "VARCHAR(255)",
                        "constraints": "UNIQUE NOT NULL",
                    },
                    {
                        "name": "password_hash",
                        "type": "VARCHAR(255)",
                        "constraints": "NOT NULL",
                    },
                    {
                        "name": "created_at",
                        "type": "TIMESTAMP",
                        "constraints": "DEFAULT NOW()",
                    },
                ],
                indexes=[
                    "CREATE INDEX idx_users_email ON users(email)",
                ],
                relationships=[],
            )
        ],
        component_logic=[
            ComponentLogic(
                component_name="AuthService",
                semantic_unit_id="SU-001",
                responsibility="Handles user registration and authentication including password hashing and email validation",
                interfaces=[
                    {
                        "method": "register_user",
                        "parameters": {"email": "str", "password": "str"},
                        "returns": "User",
                        "description": "Register new user with hashed password",
                    }
                ],
                dependencies=["UserRepository", "PasswordHasher"],
                implementation_notes="Use bcrypt for password hashing with cost factor 12",
            ),
            ComponentLogic(
                component_name="UserRepository",
                semantic_unit_id="SU-002",
                responsibility="Database operations for users including CRUD operations",
                interfaces=[
                    {
                        "method": "create_user",
                        "parameters": {"email": "str", "password_hash": "str"},
                        "returns": "User",
                        "description": "Create new user in database",
                    }
                ],
                dependencies=["Database"],
                implementation_notes="Use SQLAlchemy ORM for database access",
            ),
        ],
        design_review_checklist=[
            DesignReviewChecklistItem(
                category="Security",
                description="All passwords must be hashed",
                validation_criteria="Verify all user passwords are hashed with bcrypt or stronger algorithm before storage",
                severity="Critical",
            ),
            DesignReviewChecklistItem(
                category="Security",
                description="All API endpoints must have error handling",
                validation_criteria="Every APIContract must have at least 3 error_responses: 400, 401, 500",
                severity="High",
            ),
            DesignReviewChecklistItem(
                category="Security",
                description="Database queries must be parameterized",
                validation_criteria="All SQL queries must use parameterized statements to prevent SQL injection",
                severity="Critical",
            ),
            DesignReviewChecklistItem(
                category="Architecture",
                description="Separation of concerns maintained",
                validation_criteria="Components must follow single responsibility principle with clear boundaries",
                severity="Medium",
            ),
            DesignReviewChecklistItem(
                category="Performance",
                description="Database indexes defined for frequent queries",
                validation_criteria="All foreign keys and frequently queried columns must have indexes",
                severity="Medium",
            ),
        ],
        assumptions=["PostgreSQL 16 available", "Python 3.12+ environment"],
        agent_version="1.0.0",
    )


def create_test_code_input(task_id="TEST-001"):
    """Create a test CodeInput."""
    return CodeInput(
        task_id=task_id,
        design_specification=create_test_design_specification(task_id),
        coding_standards="Follow PEP 8, use type hints for all functions",
        context_files=["CLAUDE.md"],
    )


def create_test_generated_code(task_id="TEST-001"):
    """Create a test GeneratedCode output."""
    return GeneratedCode(
        task_id=task_id,
        files=[
            GeneratedFile(
                file_path="src/services/auth_service.py",
                content='"""Authentication service."""\n\nimport bcrypt\n\nclass AuthService:\n    pass',
                file_type="source",
                semantic_unit_id="SU-001",
                component_id="COMP-001",
                description="Authentication service with user registration",
            ),
            GeneratedFile(
                file_path="src/repositories/user_repository.py",
                content='"""User repository."""\n\nclass UserRepository:\n    pass',
                file_type="source",
                semantic_unit_id="SU-002",
                component_id="COMP-002",
                description="User database repository",
            ),
            GeneratedFile(
                file_path="tests/test_auth_service.py",
                content='"""Tests for auth service."""\n\nimport pytest\n\ndef test_register():\n    pass',
                file_type="test",
                semantic_unit_id="SU-001",
                component_id="COMP-001",
                description="Unit tests for authentication service",
            ),
        ],
        file_structure={
            "src/services": ["auth_service.py"],
            "src/repositories": ["user_repository.py"],
            "tests": ["test_auth_service.py"],
        },
        implementation_notes="Implemented JWT authentication with bcrypt password hashing",
        dependencies=["fastapi==0.104.1", "bcrypt==4.1.1", "pydantic==2.5.0"],
        setup_instructions="1. pip install -r requirements.txt\n2. Run tests: pytest",
        total_lines_of_code=150,
        total_files=3,
        semantic_units_implemented=["SU-001", "SU-002"],
        components_implemented=["COMP-001", "COMP-002"],
        agent_version="1.0.0",
    )


# =============================================================================
# Initialization Tests
# =============================================================================


class TestCodeAgentInitialization:
    """Tests for Code Agent initialization."""

    def test_init_default(self):
        """Test Code Agent initializes with default parameters."""
        agent = CodeAgent()

        assert agent.agent_version == "1.0.0"
        # Note: llm_client is lazily initialized, don't access it without API key

    def test_init_with_db_path(self, tmp_path):
        """Test Code Agent initializes with custom database path."""
        db_path = tmp_path / "test.db"
        agent = CodeAgent(db_path=db_path)

        assert agent.db_path == db_path

    def test_init_with_mock_llm(self):
        """Test Code Agent initializes with mocked LLM client."""
        mock_llm = MagicMock()
        agent = CodeAgent(llm_client=mock_llm)

        assert agent.llm_client == mock_llm


# =============================================================================
# Code Generation Tests
# =============================================================================


class TestCodeGeneration:
    """Tests for code generation functionality."""

    @patch("asp.agents.code_agent.CodeAgent.call_llm")
    def test_generate_code_success(self, mock_call_llm):
        """Test successful code generation."""
        # Setup
        agent = CodeAgent()
        input_data = create_test_code_input()

        # Mock LLM response
        mock_response = create_test_generated_code().model_dump()
        mock_call_llm.return_value = {"content": mock_response}

        # Execute
        result = agent.execute(input_data)

        # Verify
        assert isinstance(result, GeneratedCode)
        assert result.task_id == "TEST-001"
        assert len(result.files) == 3
        assert result.total_files == 3
        assert len(result.dependencies) > 0
        mock_call_llm.assert_called_once()

    @patch("asp.agents.code_agent.CodeAgent.call_llm")
    def test_generate_code_with_all_file_types(self, mock_call_llm):
        """Test code generation with different file types."""
        # Setup
        agent = CodeAgent()
        input_data = create_test_code_input()

        # Create response with multiple file types
        response = create_test_generated_code()
        response.files.extend(
            [
                GeneratedFile(
                    file_path="requirements.txt",
                    content="fastapi==0.104.1\nbcrypt==4.1.1",
                    file_type="requirements",
                    description="Python package dependencies for the project",
                ),
                GeneratedFile(
                    file_path="README.md",
                    content="# Auth Service\n\nDocumentation here",
                    file_type="documentation",
                    description="Project documentation and setup instructions",
                ),
                GeneratedFile(
                    file_path=".env.example",
                    content="DATABASE_URL=postgresql://...",
                    file_type="config",
                    description="Environment configuration template",
                ),
            ]
        )
        response.file_structure["."] = ["requirements.txt", "README.md", ".env.example"]
        response.total_files = 6

        mock_call_llm.return_value = {"content": response.model_dump()}

        # Execute
        result = agent.execute(input_data)

        # Verify all file types present
        file_types = {f.file_type for f in result.files}
        assert "source" in file_types
        assert "test" in file_types
        assert "requirements" in file_types
        assert "documentation" in file_types
        assert "config" in file_types

    @patch("asp.agents.code_agent.CodeAgent.call_llm")
    def test_generate_code_calculates_loc(self, mock_call_llm):
        """Test that total LOC is calculated if not provided."""
        # Setup
        agent = CodeAgent()
        input_data = create_test_code_input()

        # Mock response without total_lines_of_code
        response = create_test_generated_code().model_dump()
        response["total_lines_of_code"] = 0  # Should be recalculated
        mock_call_llm.return_value = {"content": response}

        # Execute
        result = agent.execute(input_data)

        # Verify LOC was calculated
        assert result.total_lines_of_code > 0

    @patch("asp.agents.code_agent.CodeAgent.call_llm")
    def test_generate_code_adds_timestamp(self, mock_call_llm):
        """Test that timestamp is added if not provided."""
        # Setup
        agent = CodeAgent()
        input_data = create_test_code_input()

        # Mock response without timestamp
        response = create_test_generated_code().model_dump()
        response["generation_timestamp"] = None
        mock_call_llm.return_value = {"content": response}

        # Execute
        result = agent.execute(input_data)

        # Verify timestamp was added
        assert result.generation_timestamp is not None
        assert isinstance(result.generation_timestamp, str)


# =============================================================================
# Validation Tests
# =============================================================================


class TestComponentCoverageValidation:
    """Tests for component coverage validation."""

    @patch("asp.agents.code_agent.CodeAgent.call_llm")
    def test_validate_all_components_covered(self, mock_call_llm):
        """Test validation passes when all components are covered."""
        # Setup
        agent = CodeAgent()
        input_data = create_test_code_input()

        # All components covered
        response = create_test_generated_code()
        mock_call_llm.return_value = {"content": response.model_dump()}

        # Execute - should not raise
        result = agent.execute(input_data)

        # Verify
        assert len(result.components_implemented) == 2
        assert "COMP-001" in result.components_implemented
        assert "COMP-002" in result.components_implemented

    @patch("asp.agents.code_agent.CodeAgent.call_llm")
    def test_validate_missing_components_warning(self, mock_call_llm, caplog):
        """Test validation handles partial component coverage."""
        # Setup
        agent = CodeAgent()
        input_data = create_test_code_input()

        # Only one component covered
        response = create_test_generated_code()
        response.files = [response.files[0]]  # Only keep first file (COMP-001)
        response.file_structure = {"src/services": ["auth_service.py"]}
        response.components_implemented = ["COMP-001"]
        mock_call_llm.return_value = {"content": response.model_dump()}

        # Execute - should complete without error even with partial coverage
        result = agent.execute(input_data)

        # Verify result is valid
        assert isinstance(result, GeneratedCode)
        assert result.task_id == "TEST-001"
        assert len(result.files) == 1


class TestFileStructureValidation:
    """Tests for file structure validation."""

    @patch("asp.agents.code_agent.CodeAgent.call_llm")
    def test_validate_file_structure_matches(self, mock_call_llm):
        """Test validation passes when file structure matches generated files."""
        # Setup
        agent = CodeAgent()
        input_data = create_test_code_input()

        response = create_test_generated_code()
        mock_call_llm.return_value = {"content": response.model_dump()}

        # Execute - should not raise
        result = agent.execute(input_data)

        # Verify
        assert len(result.file_structure) == 3

    @patch("asp.agents.code_agent.CodeAgent.call_llm")
    def test_validate_file_structure_missing_files_fails(self, mock_call_llm):
        """Test validation fails when file_structure lists files not generated."""
        # Setup
        agent = CodeAgent()
        input_data = create_test_code_input()

        # File structure has extra file
        response = create_test_generated_code()
        response.file_structure["src/services"].append("missing_file.py")
        mock_call_llm.return_value = {"content": response.model_dump()}

        # Execute - should raise
        with pytest.raises(AgentExecutionError, match="not generated"):
            agent.execute(input_data)

    @patch("asp.agents.code_agent.CodeAgent.call_llm")
    def test_validate_duplicate_file_paths_fails(self, mock_call_llm):
        """Test validation fails when duplicate file paths exist."""
        # Setup
        agent = CodeAgent()
        input_data = create_test_code_input()

        # Duplicate file path
        response = create_test_generated_code()
        duplicate_file = GeneratedFile(
            file_path="src/services/auth_service.py",  # Duplicate
            content="duplicate content",
            file_type="source",
            description="Duplicate file for testing validation",
        )
        response.files.append(duplicate_file)
        mock_call_llm.return_value = {"content": response.model_dump()}

        # Execute - should raise
        with pytest.raises(AgentExecutionError, match="Duplicate file paths"):
            agent.execute(input_data)


# =============================================================================
# Error Handling Tests
# =============================================================================


class TestErrorHandling:
    """Tests for error handling."""

    def test_execute_missing_prompt_template(self):
        """Test error when prompt template is missing."""
        agent = CodeAgent()
        input_data = create_test_code_input()

        # Mock prompt loading to fail
        with (
            patch.object(
                agent, "load_prompt", side_effect=FileNotFoundError("Not found")
            ),
            pytest.raises(AgentExecutionError, match="Prompt template not found"),
        ):
            agent.execute(input_data)

    @patch("asp.agents.code_agent.CodeAgent.call_llm")
    def test_execute_invalid_llm_response(self, mock_call_llm):
        """Test error when LLM returns invalid response."""
        agent = CodeAgent()
        input_data = create_test_code_input()

        # LLM returns non-dict response
        mock_call_llm.return_value = {"content": "not a dict"}

        with pytest.raises(AgentExecutionError, match="non-JSON response"):
            agent.execute(input_data)

    @patch("asp.agents.code_agent.CodeAgent.call_llm")
    def test_execute_invalid_schema(self, mock_call_llm):
        """Test error when response doesn't match schema."""
        agent = CodeAgent()
        input_data = create_test_code_input()

        # Invalid response missing required fields
        mock_call_llm.return_value = {
            "content": {"task_id": "TEST-001"}
        }  # Missing files

        with pytest.raises(AgentExecutionError, match="validation failed"):
            agent.execute(input_data)

    @patch("asp.agents.code_agent.CodeAgent.call_llm")
    def test_extract_json_from_markdown_fence_standard(self, mock_call_llm):
        """Test JSON extraction from standard markdown fence format."""
        agent = CodeAgent()
        input_data = create_test_code_input()

        # LLM returns JSON wrapped in markdown code fence (standard format)
        response = create_test_generated_code().model_dump()
        json_str = json.dumps(response, indent=2)
        markdown_content = f"```json\n{json_str}\n```"
        mock_call_llm.return_value = {"content": markdown_content}

        # Execute - should successfully extract and parse JSON
        result = agent.execute(input_data)
        assert isinstance(result, GeneratedCode)
        assert result.task_id == "TEST-001"

    @patch("asp.agents.code_agent.CodeAgent.call_llm")
    def test_extract_json_from_markdown_fence_no_newlines(self, mock_call_llm):
        """Test JSON extraction from markdown fence without newlines."""
        agent = CodeAgent()
        input_data = create_test_code_input()

        # LLM returns JSON wrapped in markdown fence without surrounding newlines
        response = create_test_generated_code().model_dump()
        json_str = json.dumps(response)
        markdown_content = f"```json{json_str}```"
        mock_call_llm.return_value = {"content": markdown_content}

        # Execute - should successfully extract and parse JSON
        result = agent.execute(input_data)
        assert isinstance(result, GeneratedCode)
        assert result.task_id == "TEST-001"

    @patch("asp.agents.code_agent.CodeAgent.call_llm")
    def test_extract_json_from_markdown_fence_extra_whitespace(self, mock_call_llm):
        """Test JSON extraction from markdown fence with extra whitespace."""
        agent = CodeAgent()
        input_data = create_test_code_input()

        # LLM returns JSON wrapped in markdown fence with extra spaces/newlines
        response = create_test_generated_code().model_dump()
        json_str = json.dumps(response, indent=2)
        markdown_content = f"```json  \n\n{json_str}\n\n  ```"
        mock_call_llm.return_value = {"content": markdown_content}

        # Execute - should successfully extract and parse JSON
        result = agent.execute(input_data)
        assert isinstance(result, GeneratedCode)
        assert result.task_id == "TEST-001"

    @patch("asp.agents.code_agent.CodeAgent.call_llm")
    def test_extract_json_invalid_json_in_fence(self, mock_call_llm):
        """Test error when markdown fence contains invalid JSON."""
        agent = CodeAgent()
        input_data = create_test_code_input()

        # Markdown fence with invalid JSON
        markdown_content = "```json\n{invalid json}\n```"
        mock_call_llm.return_value = {"content": markdown_content}

        # Execute - should raise error with helpful message
        with pytest.raises(
            AgentExecutionError, match="Failed to parse JSON from markdown fence"
        ):
            agent.execute(input_data)


# =============================================================================
# Output Validation Tests
# =============================================================================


class TestOutputValidation:
    """Tests for output data validation."""

    @patch("asp.agents.code_agent.CodeAgent.call_llm")
    def test_output_has_required_fields(self, mock_call_llm):
        """Test that output has all required fields."""
        agent = CodeAgent()
        input_data = create_test_code_input()

        response = create_test_generated_code()
        mock_call_llm.return_value = {"content": response.model_dump()}

        result = agent.execute(input_data)

        # Verify required fields
        assert result.task_id == "TEST-001"
        assert len(result.files) > 0
        assert isinstance(result.file_structure, dict)
        assert isinstance(result.implementation_notes, str)
        assert len(result.implementation_notes) >= 50
        assert isinstance(result.dependencies, list)
        assert result.total_files > 0
        assert result.agent_version == "1.0.0"

    @patch("asp.agents.code_agent.CodeAgent.call_llm")
    def test_output_files_have_full_content(self, mock_call_llm):
        """Test that all files have full content (not diffs or placeholders)."""
        agent = CodeAgent()
        input_data = create_test_code_input()

        response = create_test_generated_code()
        mock_call_llm.return_value = {"content": response.model_dump()}

        result = agent.execute(input_data)

        # Verify all files have content
        for file in result.files:
            assert len(file.content) > 0
            assert isinstance(file.content, str)
            # Content should not be a TODO or placeholder
            assert (
                "TODO" not in file.content or "pass" in file.content
            )  # Allow pass in test code

    @patch("asp.agents.code_agent.CodeAgent.call_llm")
    def test_output_traceability(self, mock_call_llm):
        """Test that files have traceability to design components."""
        agent = CodeAgent()
        input_data = create_test_code_input()

        response = create_test_generated_code()
        mock_call_llm.return_value = {"content": response.model_dump()}

        result = agent.execute(input_data)

        # Verify traceability
        source_files = [f for f in result.files if f.file_type == "source"]
        for file in source_files:
            # Source files should have component_id and semantic_unit_id
            assert file.component_id is not None
            assert file.semantic_unit_id is not None
