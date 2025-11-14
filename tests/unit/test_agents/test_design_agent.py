"""
Unit tests for Design Agent.

Tests cover:
- Initialization
- Design generation with valid inputs
- Semantic unit coverage validation
- Component dependency validation
- Error handling
- Output validation

Author: ASP Development Team
Date: November 13, 2025
"""

import json
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest
from pydantic import ValidationError

from asp.agents.base_agent import AgentExecutionError
from asp.agents.design_agent import DesignAgent
from asp.models.design import DesignInput, DesignSpecification
from asp.models.planning import ProjectPlan, PROBEAIPrediction, SemanticUnit


# =============================================================================
# Test Fixtures
# =============================================================================


def create_test_semantic_units():
    """Create test semantic units for project plan."""
    return [
        SemanticUnit(
            semantic_unit_id="SU-001",
            description="API endpoint for user registration with email and password",
            api_interactions=1,
            data_transformations=2,
            logical_branches=3,
            code_entities_modified=2,
            novelty_multiplier=1.0,
            complexity=25,
            dependencies=[],
        ),
        SemanticUnit(
            semantic_unit_id="SU-002",
            description="Database schema for users table with constraints",
            api_interactions=0,
            data_transformations=0,
            logical_branches=0,
            code_entities_modified=1,
            novelty_multiplier=1.0,
            complexity=15,
            dependencies=[],
        ),
        SemanticUnit(
            semantic_unit_id="SU-003",
            description="Password hashing service using bcrypt algorithm",
            api_interactions=0,
            data_transformations=1,
            logical_branches=2,
            code_entities_modified=1,
            novelty_multiplier=1.0,
            complexity=20,
            dependencies=[],
        ),
    ]


def create_test_project_plan(task_id="TEST-001"):
    """Create a test project plan."""
    return ProjectPlan(
        task_id=task_id,
        semantic_units=create_test_semantic_units(),
        total_complexity=60,
        estimated_effort=PROBEAIPrediction(
            latency_ms=5000,
            tokens_in=2000,
            tokens_out=800,
            api_cost_usd=0.02,
            confidence_interval=0.15,
        ),
        timestamp=datetime.now(),
    )


def create_test_design_input(task_id="TEST-001"):
    """Create a test DesignInput."""
    return DesignInput(
        task_id=task_id,
        requirements="Build a user registration system with email and password authentication. Use PostgreSQL database.",
        project_plan=create_test_project_plan(task_id),
        design_constraints="Use FastAPI framework and bcrypt for password hashing",
    )


def create_test_design_spec(task_id="TEST-001"):
    """Create a valid test DesignSpecification."""
    return {
        "task_id": task_id,
        "api_contracts": [
            {
                "endpoint": "/api/v1/auth/register",
                "method": "POST",
                "description": "Register a new user with email and password authentication",
                "request_schema": {"email": "string", "password": "string"},
                "response_schema": {"user_id": "string", "email": "string"},
                "error_responses": [
                    {"status": 400, "code": "INVALID_EMAIL", "message": "Invalid email format"}
                ],
                "authentication_required": False,
                "rate_limit": "5 requests per minute",
            }
        ],
        "data_schemas": [
            {
                "table_name": "users",
                "description": "Stores user account information and credentials",
                "columns": [
                    {"name": "user_id", "type": "UUID", "constraints": "PRIMARY KEY"},
                    {"name": "email", "type": "VARCHAR(255)", "constraints": "NOT NULL UNIQUE"},
                    {"name": "password_hash", "type": "VARCHAR(255)", "constraints": "NOT NULL"},
                ],
                "indexes": ["CREATE INDEX idx_users_email ON users(email)"],
                "relationships": [],
                "constraints": [],
            }
        ],
        "component_logic": [
            {
                "component_name": "UserRegistrationService",
                "semantic_unit_id": "SU-001",
                "responsibility": "Handles user registration including validation and storage",
                "interfaces": [
                    {
                        "method": "register_user",
                        "parameters": {"email": "str", "password": "str"},
                        "returns": "User",
                        "description": "Register new user",
                    }
                ],
                "dependencies": ["DatabaseService", "PasswordHasher"],
                "implementation_notes": "Use bcrypt for password hashing with cost factor 12",
                "complexity": 25,
            },
            {
                "component_name": "DatabaseService",
                "semantic_unit_id": "SU-002",
                "responsibility": "Handles database operations for user data persistence",
                "interfaces": [
                    {
                        "method": "create_user",
                        "parameters": {"email": "str", "password_hash": "str"},
                        "returns": "dict",
                        "description": "Create user record",
                    }
                ],
                "dependencies": [],
                "implementation_notes": "Use parameterized queries to prevent SQL injection",
                "complexity": 15,
            },
            {
                "component_name": "PasswordHasher",
                "semantic_unit_id": "SU-003",
                "responsibility": "Handles password hashing and verification using bcrypt",
                "interfaces": [
                    {
                        "method": "hash_password",
                        "parameters": {"password": "str"},
                        "returns": "str",
                        "description": "Hash password using bcrypt",
                    }
                ],
                "dependencies": [],
                "implementation_notes": "Use bcrypt library with cost factor 12 for security",
                "complexity": 20,
            },
        ],
        "design_review_checklist": [
            {
                "category": "Security",
                "description": "Verify passwords are hashed never stored in plaintext",
                "validation_criteria": "DataSchema must use password_hash not password",
                "severity": "Critical",
            },
            {
                "category": "Security",
                "description": "Verify SQL injection prevention mechanisms",
                "validation_criteria": "Must use parameterized queries",
                "severity": "Critical",
            },
            {
                "category": "Data Integrity",
                "description": "Verify email uniqueness is enforced at database level",
                "validation_criteria": "UNIQUE constraint on email column",
                "severity": "High",
            },
            {
                "category": "Error Handling",
                "description": "Verify all error cases have appropriate responses",
                "validation_criteria": "API must define error responses for common failures",
                "severity": "High",
            },
            {
                "category": "Performance",
                "description": "Verify database indexes for query optimization",
                "validation_criteria": "Index on email column for lookups",
                "severity": "Medium",
            },
        ],
        "architecture_overview": "3-tier architecture with API layer, business logic layer, and data persistence layer using FastAPI and PostgreSQL",
        "technology_stack": {
            "language": "Python 3.12",
            "web_framework": "FastAPI 0.104",
            "database": "PostgreSQL 15",
            "password_hashing": "bcrypt v4.1",
        },
        "assumptions": [
            "Email addresses are unique user identifiers",
            "Password complexity validation happens client-side",
            "HTTPS is enforced at infrastructure level",
        ],
    }


# =============================================================================
# Initialization Tests
# =============================================================================


def test_design_agent_initialization():
    """Test DesignAgent initializes correctly."""
    agent = DesignAgent()
    assert agent.agent_name == "DesignAgent"
    assert agent._llm_client is None  # Lazy loaded
    assert agent.prompt_dir is not None


def test_design_agent_initialization_with_custom_prompt_dir():
    """Test DesignAgent initialization with custom prompt directory."""
    custom_dir = Path("/custom/prompts")
    agent = DesignAgent(prompt_dir=custom_dir)
    assert agent.prompt_dir == custom_dir


# =============================================================================
# Design Generation Tests
# =============================================================================


@patch("asp.agents.design_agent.DesignAgent._call_llm")
@patch("asp.agents.design_agent.DesignAgent._load_and_format_prompt")
def test_execute_successful_design_generation(mock_load_prompt, mock_call_llm):
    """Test successful design generation."""
    # Setup mocks
    mock_load_prompt.return_value = "formatted prompt"
    test_design = create_test_design_spec()
    mock_call_llm.return_value = json.dumps(test_design)

    # Execute
    agent = DesignAgent()
    design_input = create_test_design_input()
    result = agent.execute(design_input)

    # Verify
    assert isinstance(result, DesignSpecification)
    assert result.task_id == "TEST-001"
    assert len(result.component_logic) == 3
    assert len(result.api_contracts) == 1
    assert len(result.data_schemas) == 1
    assert len(result.design_review_checklist) == 5

    mock_load_prompt.assert_called_once()
    mock_call_llm.assert_called_once()


@patch("asp.agents.design_agent.DesignAgent._call_llm")
@patch("asp.agents.design_agent.DesignAgent._load_and_format_prompt")
def test_execute_with_context_files(mock_load_prompt, mock_call_llm):
    """Test design generation with context files."""
    # Setup mocks
    mock_load_prompt.return_value = "formatted prompt"
    test_design = create_test_design_spec()
    mock_call_llm.return_value = json.dumps(test_design)

    # Execute with context files
    agent = DesignAgent()
    design_input = create_test_design_input()
    design_input.context_files = ["ARCHITECTURE.md", "STANDARDS.md"]
    result = agent.execute(design_input)

    # Verify
    assert isinstance(result, DesignSpecification)
    mock_load_prompt.assert_called_once()
    # Check that context_files were passed to prompt formatting
    call_kwargs = mock_load_prompt.call_args[1]
    assert "context_files" in call_kwargs


# =============================================================================
# Semantic Unit Coverage Tests
# =============================================================================


@patch("asp.agents.design_agent.DesignAgent._call_llm")
@patch("asp.agents.design_agent.DesignAgent._load_and_format_prompt")
def test_semantic_unit_coverage_validation_success(mock_load_prompt, mock_call_llm):
    """Test successful semantic unit coverage validation."""
    # All semantic units have corresponding components
    mock_load_prompt.return_value = "formatted prompt"
    test_design = create_test_design_spec()
    mock_call_llm.return_value = json.dumps(test_design)

    agent = DesignAgent()
    design_input = create_test_design_input()
    result = agent.execute(design_input)

    # All 3 semantic units (SU-001, SU-002, SU-003) have components
    assert len(result.component_logic) == 3


@patch("asp.agents.design_agent.DesignAgent._call_llm")
@patch("asp.agents.design_agent.DesignAgent._load_and_format_prompt")
def test_semantic_unit_coverage_validation_failure(mock_load_prompt, mock_call_llm):
    """Test semantic unit coverage validation catches missing units."""
    # Create design missing SU-003
    mock_load_prompt.return_value = "formatted prompt"
    test_design = create_test_design_spec()
    # Remove component for SU-003
    test_design["component_logic"] = [c for c in test_design["component_logic"] if c["semantic_unit_id"] != "SU-003"]
    mock_call_llm.return_value = json.dumps(test_design)

    agent = DesignAgent()
    design_input = create_test_design_input()

    # Should raise error about missing semantic unit
    with pytest.raises(AgentExecutionError) as exc_info:
        agent.execute(design_input)

    assert "SU-003" in str(exc_info.value)
    assert "missing components" in str(exc_info.value).lower()


# =============================================================================
# Component Dependency Validation Tests
# =============================================================================


@patch("asp.agents.design_agent.DesignAgent._call_llm")
@patch("asp.agents.design_agent.DesignAgent._load_and_format_prompt")
def test_component_dependency_validation_success(mock_load_prompt, mock_call_llm):
    """Test successful component dependency validation (no cycles)."""
    mock_load_prompt.return_value = "formatted prompt"
    test_design = create_test_design_spec()
    mock_call_llm.return_value = json.dumps(test_design)

    agent = DesignAgent()
    design_input = create_test_design_input()
    result = agent.execute(design_input)

    # Should succeed - no circular dependencies
    assert result is not None


@patch("asp.agents.design_agent.DesignAgent._call_llm")
@patch("asp.agents.design_agent.DesignAgent._load_and_format_prompt")
def test_component_dependency_circular_detection(mock_load_prompt, mock_call_llm):
    """Test circular dependency detection."""
    mock_load_prompt.return_value = "formatted prompt"
    test_design = create_test_design_spec()

    # Create circular dependency: A -> B -> C -> A
    test_design["component_logic"][0]["dependencies"] = ["DatabaseService"]
    test_design["component_logic"][1]["dependencies"] = ["PasswordHasher"]
    test_design["component_logic"][2]["dependencies"] = ["UserRegistrationService"]

    mock_call_llm.return_value = json.dumps(test_design)

    agent = DesignAgent()
    design_input = create_test_design_input()

    # Should raise error about circular dependencies
    with pytest.raises(AgentExecutionError) as exc_info:
        agent.execute(design_input)

    assert "circular" in str(exc_info.value).lower()


@patch("asp.agents.design_agent.DesignAgent._call_llm")
@patch("asp.agents.design_agent.DesignAgent._load_and_format_prompt")
def test_component_dependency_external_allowed(mock_load_prompt, mock_call_llm):
    """Test external dependencies are allowed (warning only)."""
    mock_load_prompt.return_value = "formatted prompt"
    test_design = create_test_design_spec()

    # Add external dependency
    test_design["component_logic"][0]["dependencies"] = ["ExternalAPIClient"]

    mock_call_llm.return_value = json.dumps(test_design)

    agent = DesignAgent()
    design_input = create_test_design_input()

    # Should succeed with warning
    result = agent.execute(design_input)
    assert result is not None


# =============================================================================
# Error Handling Tests
# =============================================================================


@patch("asp.agents.design_agent.DesignAgent._call_llm")
@patch("asp.agents.design_agent.DesignAgent._load_and_format_prompt")
def test_execute_invalid_json_response(mock_load_prompt, mock_call_llm):
    """Test error handling for invalid JSON response."""
    mock_load_prompt.return_value = "formatted prompt"
    mock_call_llm.return_value = "This is not valid JSON"

    agent = DesignAgent()
    design_input = create_test_design_input()

    with pytest.raises(AgentExecutionError) as exc_info:
        agent.execute(design_input)

    assert "Invalid JSON" in str(exc_info.value)


@patch("asp.agents.design_agent.DesignAgent._call_llm")
@patch("asp.agents.design_agent.DesignAgent._load_and_format_prompt")
def test_execute_missing_required_fields(mock_load_prompt, mock_call_llm):
    """Test error handling for missing required fields."""
    mock_load_prompt.return_value = "formatted prompt"
    # Missing component_logic (required field)
    invalid_design = {
        "task_id": "TEST-001",
        "api_contracts": [],
        "data_schemas": [],
        # component_logic missing
        "design_review_checklist": [],
        "architecture_overview": "Test architecture",
        "technology_stack": {"language": "Python"},
        "assumptions": [],
    }
    mock_call_llm.return_value = json.dumps(invalid_design)

    agent = DesignAgent()
    design_input = create_test_design_input()

    with pytest.raises(AgentExecutionError):
        agent.execute(design_input)


@patch("asp.agents.design_agent.DesignAgent._call_llm")
@patch("asp.agents.design_agent.DesignAgent._load_and_format_prompt")
def test_execute_insufficient_checklist_items(mock_load_prompt, mock_call_llm):
    """Test error handling for insufficient checklist items (< 5)."""
    mock_load_prompt.return_value = "formatted prompt"
    test_design = create_test_design_spec()
    # Only 2 checklist items (minimum is 5)
    test_design["design_review_checklist"] = test_design["design_review_checklist"][:2]
    mock_call_llm.return_value = json.dumps(test_design)

    agent = DesignAgent()
    design_input = create_test_design_input()

    with pytest.raises(AgentExecutionError):
        agent.execute(design_input)


@patch("asp.agents.design_agent.DesignAgent._call_llm")
def test_execute_llm_call_failure(mock_call_llm):
    """Test error handling when LLM call fails."""
    mock_call_llm.side_effect = Exception("LLM API error")

    agent = DesignAgent()
    design_input = create_test_design_input()

    with pytest.raises(AgentExecutionError) as exc_info:
        agent.execute(design_input)

    assert "Design generation failed" in str(exc_info.value)


# =============================================================================
# Input Validation Tests
# =============================================================================


def test_design_input_validation_success():
    """Test DesignInput validation with valid data."""
    design_input = create_test_design_input()
    assert design_input.task_id == "TEST-001"
    assert len(design_input.requirements) > 20
    assert design_input.project_plan.total_complexity == 60


def test_design_input_validation_short_requirements():
    """Test DesignInput validation rejects short requirements."""
    with pytest.raises(ValidationError):
        DesignInput(
            task_id="TEST-001",
            requirements="Too short",  # Less than 20 chars
            project_plan=create_test_project_plan(),
        )


def test_design_input_validation_short_task_id():
    """Test DesignInput validation rejects short task_id."""
    with pytest.raises(ValidationError):
        DesignInput(
            task_id="AB",  # Less than 3 chars
            requirements="This is a valid requirements string with enough characters",
            project_plan=create_test_project_plan(),
        )


# =============================================================================
# Output Validation Tests
# =============================================================================


def test_design_specification_validation_success():
    """Test DesignSpecification validation with valid data."""
    test_design = create_test_design_spec()
    spec = DesignSpecification(**test_design)

    assert spec.task_id == "TEST-001"
    assert len(spec.component_logic) == 3
    assert len(spec.design_review_checklist) == 5
    assert len(spec.architecture_overview) >= 50


def test_design_specification_validation_duplicate_semantic_units():
    """Test DesignSpecification validation rejects duplicate semantic_unit_ids."""
    test_design = create_test_design_spec()
    # Make two components have the same semantic_unit_id
    test_design["component_logic"][1]["semantic_unit_id"] = "SU-001"  # Same as first

    with pytest.raises(ValidationError) as exc_info:
        DesignSpecification(**test_design)

    assert "Duplicate semantic_unit_id" in str(exc_info.value)


def test_design_specification_validation_no_high_priority_checklist():
    """Test DesignSpecification validation requires at least one Critical/High item."""
    test_design = create_test_design_spec()
    # Make all checklist items Low severity
    for item in test_design["design_review_checklist"]:
        item["severity"] = "Low"

    with pytest.raises(ValidationError) as exc_info:
        DesignSpecification(**test_design)

    assert "Critical or High severity" in str(exc_info.value)


def test_design_specification_validation_short_architecture_overview():
    """Test DesignSpecification validation requires substantial architecture overview."""
    test_design = create_test_design_spec()
    test_design["architecture_overview"] = "Too short"  # Less than 50 chars

    with pytest.raises(ValidationError):
        DesignSpecification(**test_design)


# =============================================================================
# Prompt Formatting Tests
# =============================================================================


@patch("asp.agents.design_agent.DesignAgent._call_llm")
def test_prompt_includes_all_inputs(mock_call_llm):
    """Test that prompt formatting includes all input data."""
    # We'll check the prompt that gets passed to _call_llm
    test_design = create_test_design_spec()
    mock_call_llm.return_value = json.dumps(test_design)

    agent = DesignAgent()
    design_input = create_test_design_input()
    design_input.context_files = ["ARCHITECTURE.md"]
    design_input.design_constraints = "Use FastAPI"

    agent.execute(design_input)

    # Verify _call_llm was called with a prompt
    assert mock_call_llm.called
    call_kwargs = mock_call_llm.call_args[1]
    assert "prompt" in call_kwargs or len(mock_call_llm.call_args[0]) > 0


# =============================================================================
# Integration Tests (with Planning Agent output)
# =============================================================================


@patch("asp.agents.design_agent.DesignAgent._call_llm")
@patch("asp.agents.design_agent.DesignAgent._load_and_format_prompt")
def test_integration_with_planning_agent_output(mock_load_prompt, mock_call_llm):
    """Test Design Agent works with real Planning Agent output structure."""
    # Create realistic project plan (as Planning Agent would generate)
    project_plan = ProjectPlan(
        task_id="INTEGRATION-TEST-001",
        semantic_units=[
            SemanticUnit(
                semantic_unit_id="SU-001",
                description="REST API endpoint implementation",
                api_interactions=2,
                data_transformations=1,
                logical_branches=3,
                code_entities_modified=2,
                novelty_multiplier=1.0,
                complexity=30,
                dependencies=[],
            ),
        ],
        total_complexity=30,
        estimated_effort=PROBEAIPrediction(
            latency_ms=3000,
            tokens_in=1500,
            tokens_out=500,
            api_cost_usd=0.015,
            confidence_interval=0.10,
        ),
        timestamp=datetime.now(),
    )

    # Setup mocks
    mock_load_prompt.return_value = "formatted prompt"
    test_design = {
        "task_id": "INTEGRATION-TEST-001",
        "api_contracts": [],
        "data_schemas": [],
        "component_logic": [
            {
                "component_name": "APIService",
                "semantic_unit_id": "SU-001",
                "responsibility": "Handles API requests and responses",
                "interfaces": [{"method": "handle_request", "parameters": {}, "returns": "dict", "description": "Handle request"}],
                "dependencies": [],
                "implementation_notes": "Use FastAPI decorators for routing",
                "complexity": 30,
            }
        ],
        "design_review_checklist": [
            {"category": "Architecture", "description": "Check design", "validation_criteria": "Meets requirements", "severity": "High"},
            {"category": "Security", "description": "Check security", "validation_criteria": "No vulnerabilities", "severity": "Critical"},
            {"category": "Performance", "description": "Check performance", "validation_criteria": "Meets SLA", "severity": "Medium"},
            {"category": "Data Integrity", "description": "Check data", "validation_criteria": "Valid data", "severity": "High"},
            {"category": "Error Handling", "description": "Check errors", "validation_criteria": "Proper handling", "severity": "Medium"},
        ],
        "architecture_overview": "Simple REST API architecture with FastAPI framework and PostgreSQL database backend",
        "technology_stack": {"language": "Python 3.12", "framework": "FastAPI"},
        "assumptions": ["API is stateless", "Database is PostgreSQL"],
    }
    mock_call_llm.return_value = json.dumps(test_design)

    # Execute
    agent = DesignAgent()
    design_input = DesignInput(
        task_id="INTEGRATION-TEST-001",
        requirements="Build a REST API endpoint for data processing",
        project_plan=project_plan,
    )
    result = agent.execute(design_input)

    # Verify
    assert result.task_id == "INTEGRATION-TEST-001"
    assert len(result.component_logic) == 1
    assert result.component_logic[0].semantic_unit_id == "SU-001"
