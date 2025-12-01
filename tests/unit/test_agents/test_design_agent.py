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
            unit_id="SU-001",
            description="API endpoint for user registration with email and password",
            api_interactions=1,
            data_transformations=2,
            logical_branches=3,
            code_entities_modified=2,
            novelty_multiplier=1.0,
            est_complexity=25,
            dependencies=[],
        ),
        SemanticUnit(
            unit_id="SU-002",
            description="Database schema for users table with constraints",
            api_interactions=0,
            data_transformations=0,
            logical_branches=0,
            code_entities_modified=1,
            novelty_multiplier=1.0,
            est_complexity=15,
            dependencies=[],
        ),
        SemanticUnit(
            unit_id="SU-003",
            description="Password hashing service using bcrypt algorithm",
            api_interactions=0,
            data_transformations=1,
            logical_branches=2,
            code_entities_modified=1,
            novelty_multiplier=1.0,
            est_complexity=20,
            dependencies=[],
        ),
    ]


def create_test_project_plan(task_id="TEST-001"):
    """Create a test project plan."""
    return ProjectPlan(
        task_id=task_id,
        semantic_units=create_test_semantic_units(),
        total_est_complexity=60,
        probe_ai_prediction=PROBEAIPrediction(
            total_est_latency_ms=5000.0,
            total_est_tokens=2800,
            total_est_api_cost=0.02,
            confidence=0.85,
        ),
        probe_ai_enabled=False,
        agent_version="1.0.0",
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


def create_test_design_spec_dict(task_id="TEST-001"):
    """Create a valid test DesignSpecification as dict (for LLM response)."""
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
                    {
                        "status": 400,
                        "code": "INVALID_EMAIL",
                        "message": "Invalid email format",
                    }
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
                    {
                        "name": "email",
                        "type": "VARCHAR(255)",
                        "constraints": "NOT NULL UNIQUE",
                    },
                    {
                        "name": "password_hash",
                        "type": "VARCHAR(255)",
                        "constraints": "NOT NULL",
                    },
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
    assert agent.db_path is None
    assert agent._llm_client is None
    assert agent.agent_name == "DesignAgent"
    assert agent.agent_version == "1.0.0"


def test_design_agent_initialization_with_db_path():
    """Test DesignAgent initialization with database path."""
    db_path = Path("/tmp/test.db")
    agent = DesignAgent(db_path=db_path)
    assert agent.db_path == db_path


def test_design_agent_initialization_with_llm_client():
    """Test DesignAgent initialization with custom LLM client."""
    mock_client = Mock()
    agent = DesignAgent(llm_client=mock_client)
    assert agent._llm_client == mock_client


# =============================================================================
# Design Generation Tests
# =============================================================================


def test_execute_successful_design_generation():
    """Test successful design generation."""
    agent = DesignAgent()
    design_input = create_test_design_input()
    test_design = create_test_design_spec_dict()

    # Mock the LLM response
    llm_response = {"content": test_design}

    with patch.object(agent, "load_prompt", return_value="Mock prompt template"):
        with patch.object(agent, "call_llm", return_value=llm_response):
            result = agent.execute(design_input)

    # Verify
    assert isinstance(result, DesignSpecification)
    assert result.task_id == "TEST-001"
    assert len(result.component_logic) == 3
    assert len(result.api_contracts) == 1
    assert len(result.data_schemas) == 1
    assert len(result.design_review_checklist) == 5


def test_execute_with_context_files():
    """Test design generation with context files."""
    agent = DesignAgent()
    design_input = create_test_design_input()
    design_input.context_files = ["ARCHITECTURE.md", "STANDARDS.md"]

    test_design = create_test_design_spec_dict()
    llm_response = {"content": test_design}

    with patch.object(agent, "load_prompt", return_value="Mock prompt {context_files}"):
        with patch.object(
            agent, "format_prompt", wraps=agent.format_prompt
        ) as mock_format:
            with patch.object(agent, "call_llm", return_value=llm_response):
                result = agent.execute(design_input)

    # Verify
    assert isinstance(result, DesignSpecification)
    # Check that context_files were passed to format_prompt
    mock_format.assert_called_once()
    call_kwargs = mock_format.call_args[1]
    assert "context_files" in call_kwargs


# =============================================================================
# Semantic Unit Coverage Tests
# =============================================================================


def test_semantic_unit_coverage_validation_success():
    """Test successful semantic unit coverage validation."""
    agent = DesignAgent()
    design_input = create_test_design_input()
    test_design = create_test_design_spec_dict()
    llm_response = {"content": test_design}

    with patch.object(agent, "load_prompt", return_value="Mock prompt"):
        with patch.object(agent, "call_llm", return_value=llm_response):
            result = agent.execute(design_input)

    # All 3 semantic units (SU-001, SU-002, SU-003) have components
    assert len(result.component_logic) == 3


def test_semantic_unit_coverage_validation_failure():
    """Test semantic unit coverage validation catches missing units."""
    agent = DesignAgent()
    design_input = create_test_design_input()
    test_design = create_test_design_spec_dict()

    # Remove component for SU-003
    test_design["component_logic"] = [
        c for c in test_design["component_logic"] if c["semantic_unit_id"] != "SU-003"
    ]

    llm_response = {"content": test_design}

    with patch.object(agent, "load_prompt", return_value="Mock prompt"):
        with patch.object(agent, "call_llm", return_value=llm_response):
            # Should raise error about missing semantic unit
            with pytest.raises(AgentExecutionError) as exc_info:
                agent.execute(design_input)

    assert "SU-003" in str(exc_info.value)
    assert "no corresponding components" in str(exc_info.value).lower()


# =============================================================================
# Component Dependency Validation Tests
# =============================================================================


def test_component_dependency_validation_success():
    """Test successful component dependency validation (no cycles)."""
    agent = DesignAgent()
    design_input = create_test_design_input()
    test_design = create_test_design_spec_dict()
    llm_response = {"content": test_design}

    with patch.object(agent, "load_prompt", return_value="Mock prompt"):
        with patch.object(agent, "call_llm", return_value=llm_response):
            result = agent.execute(design_input)

    # Should succeed - no circular dependencies
    assert result is not None


def test_component_dependency_circular_detection():
    """Test circular dependency detection."""
    agent = DesignAgent()
    design_input = create_test_design_input()
    test_design = create_test_design_spec_dict()

    # Create circular dependency: A -> B -> C -> A
    test_design["component_logic"][0]["dependencies"] = ["DatabaseService"]
    test_design["component_logic"][1]["dependencies"] = ["PasswordHasher"]
    test_design["component_logic"][2]["dependencies"] = ["UserRegistrationService"]

    llm_response = {"content": test_design}

    with patch.object(agent, "load_prompt", return_value="Mock prompt"):
        with patch.object(agent, "call_llm", return_value=llm_response):
            # Should raise error about circular dependencies
            with pytest.raises(AgentExecutionError) as exc_info:
                agent.execute(design_input)

    assert "circular" in str(exc_info.value).lower()


def test_component_dependency_external_allowed():
    """Test external dependencies are allowed (warning only)."""
    agent = DesignAgent()
    design_input = create_test_design_input()
    test_design = create_test_design_spec_dict()

    # Add external dependency
    test_design["component_logic"][0]["dependencies"] = ["ExternalAPIClient"]

    llm_response = {"content": test_design}

    with patch.object(agent, "load_prompt", return_value="Mock prompt"):
        with patch.object(agent, "call_llm", return_value=llm_response):
            # Should succeed with warning
            result = agent.execute(design_input)

    assert result is not None


# =============================================================================
# Error Handling Tests
# =============================================================================


def test_execute_invalid_json_response():
    """Test error handling for invalid JSON response."""
    agent = DesignAgent()
    design_input = create_test_design_input()

    # Mock non-dict response
    llm_response = {"content": "This is not valid JSON dict"}

    with patch.object(agent, "load_prompt", return_value="Mock prompt"):
        with patch.object(agent, "call_llm", return_value=llm_response):
            with pytest.raises(AgentExecutionError) as exc_info:
                agent.execute(design_input)

    assert "non-JSON" in str(exc_info.value)


def test_execute_missing_required_fields():
    """Test error handling for missing required fields."""
    agent = DesignAgent()
    design_input = create_test_design_input()

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

    llm_response = {"content": invalid_design}

    with patch.object(agent, "load_prompt", return_value="Mock prompt"):
        with patch.object(agent, "call_llm", return_value=llm_response):
            with pytest.raises(AgentExecutionError):
                agent.execute(design_input)


def test_execute_insufficient_checklist_items():
    """Test error handling for insufficient checklist items (< 5)."""
    agent = DesignAgent()
    design_input = create_test_design_input()
    test_design = create_test_design_spec_dict()

    # Only 2 checklist items (minimum is 5)
    test_design["design_review_checklist"] = test_design["design_review_checklist"][:2]

    llm_response = {"content": test_design}

    with patch.object(agent, "load_prompt", return_value="Mock prompt"):
        with patch.object(agent, "call_llm", return_value=llm_response):
            with pytest.raises(AgentExecutionError):
                agent.execute(design_input)


def test_execute_llm_call_failure():
    """Test error handling when LLM call fails."""
    agent = DesignAgent()
    design_input = create_test_design_input()

    with patch.object(agent, "load_prompt", return_value="Mock prompt"):
        with patch.object(agent, "call_llm", side_effect=Exception("LLM API error")):
            with pytest.raises(AgentExecutionError) as exc_info:
                agent.execute(design_input)

    assert "Design generation failed" in str(exc_info.value)


def test_execute_prompt_not_found():
    """Test error handling when prompt template not found."""
    agent = DesignAgent()
    design_input = create_test_design_input()

    with patch.object(
        agent, "load_prompt", side_effect=FileNotFoundError("Prompt not found")
    ):
        with pytest.raises(AgentExecutionError) as exc_info:
            agent.execute(design_input)

    assert "Prompt template not found" in str(exc_info.value)


# =============================================================================
# Input Validation Tests
# =============================================================================


def test_design_input_validation_success():
    """Test DesignInput validation with valid data."""
    design_input = create_test_design_input()
    assert design_input.task_id == "TEST-001"
    assert len(design_input.requirements) > 20
    assert design_input.project_plan.total_est_complexity == 60


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
    test_design = create_test_design_spec_dict()
    spec = DesignSpecification(**test_design)

    assert spec.task_id == "TEST-001"
    assert len(spec.component_logic) == 3
    assert len(spec.design_review_checklist) == 5
    assert len(spec.architecture_overview) >= 50


def test_design_specification_validation_duplicate_semantic_units():
    """Test DesignSpecification allows duplicate semantic_unit_ids.

    Multiple components can map to the same semantic unit when a complex
    unit is broken into multiple implementation components.
    """
    test_design = create_test_design_spec_dict()
    # Make two components have the same semantic_unit_id
    test_design["component_logic"][1]["semantic_unit_id"] = "SU-001"  # Same as first

    # Should NOT raise - duplicates are allowed by design
    design_spec = DesignSpecification(**test_design)
    assert design_spec is not None
    assert design_spec.component_logic[0].semantic_unit_id == "SU-001"
    assert design_spec.component_logic[1].semantic_unit_id == "SU-001"


def test_design_specification_validation_no_high_priority_checklist():
    """Test DesignSpecification validation requires at least one Critical/High item."""
    test_design = create_test_design_spec_dict()
    # Make all checklist items Low severity
    for item in test_design["design_review_checklist"]:
        item["severity"] = "Low"

    with pytest.raises(ValidationError) as exc_info:
        DesignSpecification(**test_design)

    assert "Critical or High severity" in str(exc_info.value)


def test_design_specification_validation_short_architecture_overview():
    """Test DesignSpecification validation requires substantial architecture overview."""
    test_design = create_test_design_spec_dict()
    test_design["architecture_overview"] = "Too short"  # Less than 50 chars

    with pytest.raises(ValidationError):
        DesignSpecification(**test_design)


# =============================================================================
# Integration Tests
# =============================================================================


def test_integration_with_planning_agent_output():
    """Test Design Agent works with real Planning Agent output structure."""
    agent = DesignAgent()

    # Create realistic project plan (as Planning Agent would generate)
    project_plan = ProjectPlan(
        task_id="INTEGRATION-TEST-001",
        semantic_units=[
            SemanticUnit(
                unit_id="SU-001",
                description="REST API endpoint implementation",
                api_interactions=2,
                data_transformations=1,
                logical_branches=3,
                code_entities_modified=2,
                novelty_multiplier=1.0,
                est_complexity=30,
                dependencies=[],
            ),
        ],
        total_est_complexity=30,
        probe_ai_prediction=PROBEAIPrediction(
            total_est_latency_ms=3000.0,
            total_est_tokens=2000,
            total_est_api_cost=0.015,
            confidence=0.90,
        ),
        probe_ai_enabled=False,
        agent_version="1.0.0",
        timestamp=datetime.now(),
    )

    test_design = {
        "task_id": "INTEGRATION-TEST-001",
        "api_contracts": [],
        "data_schemas": [],
        "component_logic": [
            {
                "component_name": "APIService",
                "semantic_unit_id": "SU-001",
                "responsibility": "Handles API requests and responses",
                "interfaces": [
                    {
                        "method": "handle_request",
                        "parameters": {},
                        "returns": "dict",
                        "description": "Handle request",
                    }
                ],
                "dependencies": [],
                "implementation_notes": "Use FastAPI decorators for routing",
                "complexity": 30,
            }
        ],
        "design_review_checklist": [
            {
                "category": "Architecture",
                "description": "Check design meets requirements",
                "validation_criteria": "Design meets all requirements",
                "severity": "High",
            },
            {
                "category": "Security",
                "description": "Check security vulnerabilities",
                "validation_criteria": "No security vulnerabilities found",
                "severity": "Critical",
            },
            {
                "category": "Performance",
                "description": "Check performance requirements",
                "validation_criteria": "Meets SLA requirements",
                "severity": "Medium",
            },
            {
                "category": "Data Integrity",
                "description": "Check data validation",
                "validation_criteria": "Valid data constraints",
                "severity": "High",
            },
            {
                "category": "Error Handling",
                "description": "Check error handling",
                "validation_criteria": "Proper error handling implemented",
                "severity": "Medium",
            },
        ],
        "architecture_overview": "Simple REST API architecture with FastAPI framework and PostgreSQL database backend",
        "technology_stack": {"language": "Python 3.12", "framework": "FastAPI"},
        "assumptions": ["API is stateless", "Database is PostgreSQL"],
    }

    design_input = DesignInput(
        task_id="INTEGRATION-TEST-001",
        requirements="Build a REST API endpoint for data processing",
        project_plan=project_plan,
    )

    llm_response = {"content": test_design}

    with patch.object(agent, "load_prompt", return_value="Mock prompt"):
        with patch.object(agent, "call_llm", return_value=llm_response):
            result = agent.execute(design_input)

    # Verify
    assert result.task_id == "INTEGRATION-TEST-001"
    assert len(result.component_logic) == 1
    assert result.component_logic[0].semantic_unit_id == "SU-001"
