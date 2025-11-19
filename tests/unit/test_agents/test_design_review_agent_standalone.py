"""
Unit tests for DesignReviewAgent (standalone agent, not orchestrator).

Tests cover:
- Initialization
- Automated validation checks
- LLM-based review execution
- Issue aggregation and assessment
- Report generation
- Error handling
- Edge cases

Author: ASP Development Team
Date: November 19, 2025
"""

import json
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest
from pydantic import ValidationError

from asp.agents.base_agent import AgentExecutionError
from asp.agents.design_review_agent import DesignReviewAgent
from asp.models.design import (
    APIContract,
    ComponentLogic,
    DataSchema,
    DesignReviewChecklistItem,
    DesignSpecification,
)
from asp.models.design_review import (
    ChecklistItemReview,
    DesignIssue,
    DesignReviewReport,
    ImprovementSuggestion,
)


# =============================================================================
# Test Fixtures
# =============================================================================


def create_test_design_specification(task_id="TEST-DESIGN-REVIEW-001"):
    """Create a test design specification for review."""
    return DesignSpecification(
        task_id=task_id,
        architecture_overview=(
            "Microservice architecture with API Gateway, Auth Service, and User Service. "
            "Uses JWT for authentication, PostgreSQL for persistence, and Redis for caching."
        ),
        technology_stack={
            "language": "Python 3.12",
            "framework": "FastAPI 0.104",
            "database": "PostgreSQL 16",
            "cache": "Redis 7",
            "authentication": "JWT (python-jose)",
        },
        api_contracts=[
            APIContract(
                endpoint="/api/v1/auth/register",
                method="POST",
                description="Register new user with email and password",
                request_schema={
                    "email": "string (email format)",
                    "password": "string (min 8 chars)",
                },
                response_schema={
                    "user_id": "string (UUID)",
                    "email": "string",
                },
                error_responses=[
                    {"status": 400, "code": "INVALID_INPUT"},
                    {"status": 409, "code": "EMAIL_EXISTS"},
                ],
                authentication_required=False,
            ),
            APIContract(
                endpoint="/api/v1/users/{user_id}",
                method="GET",
                description="Get user profile by ID",
                request_schema=None,
                response_schema={
                    "user_id": "string (UUID)",
                    "email": "string",
                    "created_at": "string (ISO 8601)",
                },
                error_responses=[
                    {"status": 404, "code": "USER_NOT_FOUND"},
                ],
                authentication_required=True,
            ),
        ],
        data_schemas=[
            DataSchema(
                table_name="users",
                description="User account information",
                columns=[
                    {"name": "user_id", "type": "UUID", "constraints": "PRIMARY KEY"},
                    {"name": "email", "type": "VARCHAR(255)", "constraints": "UNIQUE NOT NULL"},
                    {"name": "password_hash", "type": "VARCHAR(255)", "constraints": "NOT NULL"},
                    {"name": "created_at", "type": "TIMESTAMP", "constraints": "DEFAULT NOW()"},
                ],
                indexes=["CREATE INDEX idx_users_email ON users(email)"],
            )
        ],
        component_logic=[
            ComponentLogic(
                component_name="AuthService",
                semantic_unit_id="SU-001",
                responsibility="User authentication and registration",
                interfaces=[
                    {
                        "method": "register_user",
                        "parameters": {"email": "str", "password": "str"},
                        "returns": "User",
                        "description": "Register new user",
                    }
                ],
                dependencies=["UserRepository", "PasswordHasher"],
                implementation_notes="Use bcrypt for password hashing",
            ),
            ComponentLogic(
                component_name="UserRepository",
                semantic_unit_id="SU-002",
                responsibility="User data persistence operations for database access",
                interfaces=[
                    {
                        "method": "create_user",
                        "parameters": {"email": "str", "password_hash": "str"},
                        "returns": "User",
                        "description": "Create user in database",
                    }
                ],
                dependencies=[],
                implementation_notes="Use SQLAlchemy ORM for all database operations with proper session management",
            ),
        ],
        design_review_checklist=[
            DesignReviewChecklistItem(
                category="Security",
                description="Passwords must be hashed",
                validation_criteria="Verify password_hash field exists",
                severity="Critical",
            ),
            DesignReviewChecklistItem(
                category="Security",
                description="SQL injection prevention",
                validation_criteria="Use parameterized queries",
                severity="Critical",
            ),
            DesignReviewChecklistItem(
                category="Architecture",
                description="Separation of concerns",
                validation_criteria="Components follow single responsibility",
                severity="High",
            ),
            DesignReviewChecklistItem(
                category="Performance",
                description="Database indexes",
                validation_criteria="Indexes on frequently queried columns",
                severity="Medium",
            ),
            DesignReviewChecklistItem(
                category="API Design",
                description="RESTful conventions",
                validation_criteria="Follow REST best practices",
                severity="Medium",
            ),
        ],
        assumptions=["PostgreSQL 16 available", "Redis for caching"],
        agent_version="1.0.0",
    )


def create_design_with_circular_deps():
    """Create a design specification with circular dependencies."""
    return DesignSpecification(
        task_id="TEST-CIRCULAR-001",
        architecture_overview="System with circular dependencies for testing detection algorithms",
        technology_stack={"language": "Python"},
        component_logic=[
            ComponentLogic(
                component_name="ServiceA",
                semantic_unit_id="SU-001",
                responsibility="Service A handles primary business logic operations",
                interfaces=[{"method": "a_method"}],
                dependencies=["ServiceB"],  # A depends on B
                implementation_notes="Service A implementation with dependency on ServiceB",
            ),
            ComponentLogic(
                component_name="ServiceB",
                semantic_unit_id="SU-002",
                responsibility="Service B handles secondary business operations",
                interfaces=[{"method": "b_method"}],
                dependencies=["ServiceC"],  # B depends on C
                implementation_notes="Service B implementation with dependency on ServiceC",
            ),
            ComponentLogic(
                component_name="ServiceC",
                semantic_unit_id="SU-003",
                responsibility="Service C handles tertiary business operations",
                interfaces=[{"method": "c_method"}],
                dependencies=["ServiceA"],  # C depends on A -> circular!
                implementation_notes="Service C implementation with dependency on ServiceA creating circular dependency",
            ),
        ],
        design_review_checklist=[
            DesignReviewChecklistItem(
                category="Architecture",
                description="No circular dependencies",
                validation_criteria="Check component dependency graph",
                severity="Critical",
            ),
            DesignReviewChecklistItem(
                category="Architecture",
                description="Layered architecture",
                validation_criteria="Verify clear layering",
                severity="High",
            ),
            DesignReviewChecklistItem(
                category="Architecture",
                description="Component cohesion",
                validation_criteria="Each component has single purpose",
                severity="Medium",
            ),
            DesignReviewChecklistItem(
                category="Performance",
                description="Efficient algorithms",
                validation_criteria="No O(n²) or worse complexity",
                severity="Medium",
            ),
            DesignReviewChecklistItem(
                category="Security",
                description="Input validation",
                validation_criteria="All inputs validated",
                severity="High",
            ),
        ],
        agent_version="1.0.0",
    )


def create_design_apis_without_schemas():
    """Create a design with API contracts but no data schemas."""
    return DesignSpecification(
        task_id="TEST-NO-SCHEMAS-001",
        architecture_overview="API-only service with no data persistence for stateless health checks",
        technology_stack={"language": "Python"},
        api_contracts=[
            APIContract(
                endpoint="/api/health",
                method="GET",
                description="Health check endpoint for monitoring system status",
                response_schema={"status": "string"},
            )
        ],
        data_schemas=[],  # No schemas!
        component_logic=[
            ComponentLogic(
                component_name="HealthService",
                semantic_unit_id="SU-001",
                responsibility="Health check operations for system monitoring",
                interfaces=[{"method": "check_health"}],
                implementation_notes="Simple health check implementation returning system status information",
            )
        ],
        design_review_checklist=[
            DesignReviewChecklistItem(
                category="API Design",
                description="Health endpoint exists",
                validation_criteria="Verify /health endpoint",
                severity="Medium",
            ),
            DesignReviewChecklistItem(
                category="Architecture",
                description="Monitoring capability",
                validation_criteria="System can be monitored",
                severity="High",
            ),
            DesignReviewChecklistItem(
                category="Performance",
                description="Fast response time",
                validation_criteria="Health check under 100ms",
                severity="Medium",
            ),
            DesignReviewChecklistItem(
                category="Security",
                description="No sensitive data exposed",
                validation_criteria="Health endpoint safe",
                severity="High",
            ),
            DesignReviewChecklistItem(
                category="Reliability",
                description="Always available",
                validation_criteria="Health check highly available",
                severity="Medium",
            ),
        ],
        agent_version="1.0.0",
    )


def create_mock_llm_review_response(
    issues=None,
    suggestions=None,
    checklist_review=None,
):
    """Create mock LLM review response."""
    # Default to at least one checklist item (required by model)
    default_checklist = [
        {
            "checklist_item_id": "CHK-DEFAULT",
            "category": "General",
            "description": "General design quality assessment",
            "status": "Pass",
            "notes": "All automated checks passed successfully with no issues found",
        }
    ]
    return {
        "issues_found": issues or [],
        "improvement_suggestions": suggestions or [],
        "checklist_review": checklist_review if checklist_review is not None else default_checklist,
    }


def create_mock_llm_response_with_critical_issues():
    """Create LLM response with critical security issues."""
    return {
        "issues_found": [
            {
                "issue_id": "ISSUE-001",
                "category": "Security",
                "severity": "Critical",
                "description": "Password stored in plaintext in data schema",
                "evidence": "users.password field should be password_hash",
                "impact": "Critical security vulnerability",
                "affected_phase": "Design",
            },
            {
                "issue_id": "ISSUE-002",
                "category": "Security",
                "severity": "High",
                "description": "Missing rate limiting on authentication endpoint",
                "evidence": "/api/v1/auth/register has no rate limit",
                "impact": "Vulnerable to brute force attacks",
                "affected_phase": "Design",
            },
        ],
        "improvement_suggestions": [
            {
                "suggestion_id": "IMPROVE-001",
                "related_issue_id": "ISSUE-001",
                "category": "Security",
                "priority": "High",
                "description": "Use bcrypt or Argon2 for password hashing",
                "implementation_notes": "Store password_hash instead of password",
            }
        ],
        "checklist_review": [
            {
                "checklist_item_id": "CHK-001",
                "category": "Security",
                "description": "Passwords must be hashed using industry-standard algorithms",
                "status": "Fail",
                "notes": "Password hashing issue found - passwords stored in plaintext (ISSUE-001)",
                "related_issues": ["ISSUE-001"],
            },
            {
                "checklist_item_id": "CHK-002",
                "category": "Security",
                "description": "SQL injection prevention must be implemented",
                "status": "Pass",
                "notes": "SQL injection prevention verified through parameterized queries",
                "related_issues": [],
            },
        ],
    }


# =============================================================================
# Initialization Tests
# =============================================================================


class TestDesignReviewAgentInitialization:
    """Tests for DesignReviewAgent initialization."""

    def test_init_default(self):
        """Test agent initializes with default parameters."""
        agent = DesignReviewAgent()

        assert agent.agent_version == "1.0.0"
        # Note: llm_client is lazily initialized

    def test_init_with_mock_llm(self):
        """Test agent initializes with mocked LLM client."""
        mock_llm = MagicMock()
        agent = DesignReviewAgent(llm_client=mock_llm)

        assert agent._llm_client == mock_llm

    def test_init_with_db_path(self, tmp_path):
        """Test agent initializes with custom database path."""
        db_path = tmp_path / "test.db"
        agent = DesignReviewAgent(db_path=str(db_path))

        assert agent.db_path == str(db_path)


# =============================================================================
# Automated Checks Tests
# =============================================================================


class TestAutomatedChecks:
    """Tests for automated validation checks."""

    def test_automated_checks_pass_for_valid_design(self):
        """Test that valid design passes all automated checks."""
        agent = DesignReviewAgent()
        design_spec = create_test_design_specification()

        checks = agent._run_automated_checks(design_spec)

        assert checks["semantic_coverage"] is True
        assert checks["no_circular_deps"] is True
        assert checks["checklist_complete"] is True
        assert checks["has_high_priority_items"] is True
        assert checks["schema_api_consistency"] is True
        assert checks["components_have_interfaces"] is True

    def test_check_circular_dependencies_detects_cycles(self):
        """Test circular dependency detection."""
        agent = DesignReviewAgent()
        design_spec = create_design_with_circular_deps()

        result = agent._check_circular_dependencies(design_spec)

        assert result is False  # Circular dependency detected

    def test_check_circular_dependencies_passes_for_acyclic_graph(self):
        """Test circular dependency check passes for valid design."""
        agent = DesignReviewAgent()
        design_spec = create_test_design_specification()

        result = agent._check_circular_dependencies(design_spec)

        assert result is True  # No circular dependencies

    def test_check_schema_api_consistency_fails_for_apis_without_schemas(self):
        """Test schema-API consistency check detects missing schemas."""
        agent = DesignReviewAgent()
        design_spec = create_design_apis_without_schemas()

        result = agent._check_schema_api_consistency(design_spec)

        assert result is False  # APIs exist but no schemas

    def test_check_schema_api_consistency_passes_for_consistent_design(self):
        """Test schema-API consistency check passes for valid design."""
        agent = DesignReviewAgent()
        design_spec = create_test_design_specification()

        result = agent._check_schema_api_consistency(design_spec)

        assert result is True

    def test_check_semantic_coverage_returns_true_for_components(self):
        """Test semantic coverage check returns True when components exist."""
        agent = DesignReviewAgent()
        design_spec = create_test_design_specification()

        result = agent._check_semantic_coverage(design_spec)

        assert result is True  # Has semantic unit IDs


# =============================================================================
# LLM Review Tests
# =============================================================================


class TestLLMReview:
    """Tests for LLM-based review."""

    @patch("asp.agents.design_review_agent.DesignReviewAgent.call_llm")
    def test_llm_review_success(self, mock_call_llm):
        """Test successful LLM review."""
        agent = DesignReviewAgent()
        design_spec = create_test_design_specification()

        # Mock LLM response
        mock_call_llm.return_value = {
            "content": create_mock_llm_review_response(
                issues=[
                    {
                        "issue_id": "ISSUE-003",
                        "category": "Architecture",
                        "severity": "Medium",
                        "description": "Component coupling could be reduced",
                        "evidence": "AuthService depends on multiple services",
                        "impact": "Moderate maintainability impact",
                        "affected_phase": "Design",
                    }
                ],
                suggestions=[
                    {
                        "suggestion_id": "IMPROVE-002",
                        "related_issue_id": "ISSUE-003",
                        "category": "Architecture",
                        "priority": "Medium",
                        "description": "Use dependency injection",
                        "implementation_notes": "Inject dependencies via constructor",
                    }
                ],
            )
        }

        result = agent._run_llm_review(design_spec, None)

        assert "issues_found" in result
        assert "improvement_suggestions" in result
        assert len(result["issues_found"]) == 1
        mock_call_llm.assert_called_once()

    @patch("asp.agents.design_review_agent.DesignReviewAgent.call_llm")
    def test_llm_review_handles_string_content(self, mock_call_llm):
        """Test LLM review handles JSON string content."""
        agent = DesignReviewAgent()
        design_spec = create_test_design_specification()

        # Mock LLM returning JSON as string
        response_dict = create_mock_llm_review_response()
        mock_call_llm.return_value = {"content": json.dumps(response_dict)}

        result = agent._run_llm_review(design_spec, None)

        assert isinstance(result, dict)
        assert "issues_found" in result

    @patch("asp.agents.design_review_agent.DesignReviewAgent.call_llm")
    def test_llm_review_handles_custom_quality_standards(self, mock_call_llm):
        """Test LLM review with custom quality standards."""
        agent = DesignReviewAgent()
        design_spec = create_test_design_specification()
        custom_standards = "Follow OWASP Top 10 security guidelines"

        mock_call_llm.return_value = {
            "content": create_mock_llm_review_response()
        }

        agent._run_llm_review(design_spec, custom_standards)

        # Verify call_llm was called (quality standards embedded in prompt)
        mock_call_llm.assert_called_once()
        call_args = mock_call_llm.call_args[0][0]
        assert custom_standards in call_args

    def test_llm_review_fails_when_prompt_template_missing(self):
        """Test LLM review fails gracefully when prompt template missing."""
        agent = DesignReviewAgent()
        design_spec = create_test_design_specification()

        with patch.object(agent, "load_prompt", side_effect=FileNotFoundError("Missing")):
            with pytest.raises(AgentExecutionError, match="Prompt template not found"):
                agent._run_llm_review(design_spec, None)

    @patch("asp.agents.design_review_agent.DesignReviewAgent.call_llm")
    def test_llm_review_fails_on_invalid_json(self, mock_call_llm):
        """Test LLM review fails when response is invalid JSON."""
        agent = DesignReviewAgent()
        design_spec = create_test_design_specification()

        mock_call_llm.return_value = {"content": "not valid json"}

        with pytest.raises(AgentExecutionError, match="Failed to parse LLM review response"):
            agent._run_llm_review(design_spec, None)


# =============================================================================
# Execute Tests
# =============================================================================


class TestExecute:
    """Tests for main execute method."""

    @patch("asp.agents.design_review_agent.DesignReviewAgent.call_llm")
    def test_execute_success_pass_assessment(self, mock_call_llm):
        """Test successful execution with PASS assessment."""
        agent = DesignReviewAgent()
        design_spec = create_test_design_specification()

        # Mock LLM response with no issues
        mock_call_llm.return_value = {
            "content": create_mock_llm_review_response()
        }

        report = agent.execute(design_spec)

        assert isinstance(report, DesignReviewReport)
        assert report.task_id == "TEST-DESIGN-REVIEW-001"
        assert report.overall_assessment == "PASS"
        assert report.critical_issue_count == 0
        assert report.high_issue_count == 0
        assert report.medium_issue_count == 0
        assert report.low_issue_count == 0
        assert report.agent_version == "1.0.0"

    @patch("asp.agents.design_review_agent.DesignReviewAgent.call_llm")
    def test_execute_success_needs_improvement(self, mock_call_llm):
        """Test execution with NEEDS_IMPROVEMENT assessment."""
        agent = DesignReviewAgent()
        design_spec = create_test_design_specification()

        # Mock LLM response with medium severity issues
        mock_call_llm.return_value = {
            "content": create_mock_llm_review_response(
                issues=[
                    {
                        "issue_id": "ISSUE-004",
                        "category": "Performance",
                        "severity": "Medium",
                        "description": "Missing database index",
                        "evidence": "users.email should be indexed",
                        "impact": "Slow queries on large datasets",
                        "affected_phase": "Design",
                    }
                ]
            )
        }

        report = agent.execute(design_spec)

        assert report.overall_assessment == "NEEDS_IMPROVEMENT"
        assert report.medium_issue_count == 1
        assert len(report.issues_found) == 1

    @patch("asp.agents.design_review_agent.DesignReviewAgent.call_llm")
    def test_execute_success_fail_assessment(self, mock_call_llm):
        """Test execution with FAIL assessment (critical/high issues)."""
        agent = DesignReviewAgent()
        design_spec = create_test_design_specification()

        # Mock LLM response with critical issues
        mock_call_llm.return_value = {
            "content": create_mock_llm_response_with_critical_issues()
        }

        report = agent.execute(design_spec)

        assert report.overall_assessment == "FAIL"
        assert report.critical_issue_count >= 1
        assert report.high_issue_count >= 1
        assert len(report.issues_found) >= 2

    @patch("asp.agents.design_review_agent.DesignReviewAgent.call_llm")
    def test_execute_includes_automated_checks(self, mock_call_llm):
        """Test that report includes automated check results."""
        agent = DesignReviewAgent()
        design_spec = create_test_design_specification()

        mock_call_llm.return_value = {
            "content": create_mock_llm_review_response()
        }

        report = agent.execute(design_spec)

        assert isinstance(report.automated_checks, dict)
        assert "semantic_coverage" in report.automated_checks
        assert "no_circular_deps" in report.automated_checks
        assert "checklist_complete" in report.automated_checks

    @patch("asp.agents.design_review_agent.DesignReviewAgent.call_llm")
    def test_execute_generates_review_id(self, mock_call_llm):
        """Test that execute generates proper review ID."""
        agent = DesignReviewAgent()
        design_spec = create_test_design_specification()

        mock_call_llm.return_value = {
            "content": create_mock_llm_review_response()
        }

        report = agent.execute(design_spec)

        assert report.review_id.startswith("REVIEW-")
        assert "TESTDESIGNREVIEW001" in report.review_id  # Cleaned task ID

    @patch("asp.agents.design_review_agent.DesignReviewAgent.call_llm")
    def test_execute_calculates_review_duration(self, mock_call_llm):
        """Test that review duration is calculated."""
        agent = DesignReviewAgent()
        design_spec = create_test_design_specification()

        mock_call_llm.return_value = {
            "content": create_mock_llm_review_response()
        }

        report = agent.execute(design_spec)

        assert report.review_duration_ms > 0
        assert isinstance(report.review_duration_ms, (int, float))

    @patch("asp.agents.design_review_agent.DesignReviewAgent.call_llm")
    def test_execute_includes_checklist_review(self, mock_call_llm):
        """Test that report includes checklist review results."""
        agent = DesignReviewAgent()
        design_spec = create_test_design_specification()

        mock_call_llm.return_value = {
            "content": create_mock_llm_review_response(
                checklist_review=[
                    {
                        "checklist_item_id": "CHK-001",
                        "category": "Security",
                        "description": "All security requirements must be validated",
                        "status": "Pass",
                        "notes": "All security checks passed successfully with no vulnerabilities found",
                    }
                ]
            )
        }

        report = agent.execute(design_spec)

        assert len(report.checklist_review) == 1
        assert report.checklist_review[0].status == "Pass"

    def test_execute_fails_on_llm_error(self):
        """Test execute fails gracefully on LLM error."""
        agent = DesignReviewAgent()
        design_spec = create_test_design_specification()

        with patch.object(agent, "call_llm", side_effect=Exception("LLM error")):
            with pytest.raises(AgentExecutionError, match="Design review failed"):
                agent.execute(design_spec)


# =============================================================================
# Review ID Generation Tests
# =============================================================================


class TestReviewIDGeneration:
    """Tests for review ID generation."""

    def test_generate_review_id_format(self):
        """Test review ID format is correct."""
        agent = DesignReviewAgent()
        task_id = "TEST-001"
        timestamp = datetime(2025, 11, 19, 14, 30, 45)

        review_id = agent._generate_review_id(task_id, timestamp)

        assert review_id.startswith("REVIEW-")
        assert "TEST001" in review_id
        assert "20251119" in review_id  # Date
        assert "143045" in review_id  # Time

    def test_generate_review_id_cleans_special_chars(self):
        """Test review ID removes special characters from task_id."""
        agent = DesignReviewAgent()
        task_id = "JWT-AUTH-2025-11-19"
        timestamp = datetime(2025, 11, 19, 10, 0, 0)

        review_id = agent._generate_review_id(task_id, timestamp)

        # All hyphens should be removed, only alphanumeric
        assert "JWTAUTH20251119" in review_id
        assert "-" not in review_id.split("REVIEW-")[1].split("-")[0]

    def test_generate_review_id_unique_per_timestamp(self):
        """Test that different timestamps produce different review IDs."""
        agent = DesignReviewAgent()
        task_id = "TEST-001"
        ts1 = datetime(2025, 11, 19, 14, 30, 0)
        ts2 = datetime(2025, 11, 19, 14, 30, 1)

        id1 = agent._generate_review_id(task_id, ts1)
        id2 = agent._generate_review_id(task_id, ts2)

        assert id1 != id2


# =============================================================================
# Error Handling and Edge Cases
# =============================================================================


class TestErrorHandlingAndEdgeCases:
    """Tests for error handling and edge cases."""

    @patch("asp.agents.design_review_agent.DesignReviewAgent.call_llm")
    def test_execute_handles_empty_issues_list(self, mock_call_llm):
        """Test execution with empty issues list."""
        agent = DesignReviewAgent()
        design_spec = create_test_design_specification()

        # Use helper function which provides valid checklist item
        mock_call_llm.return_value = {
            "content": create_mock_llm_review_response()
        }

        report = agent.execute(design_spec)

        assert report.overall_assessment == "PASS"
        assert len(report.issues_found) == 0

    @patch("asp.agents.design_review_agent.DesignReviewAgent.call_llm")
    def test_execute_handles_mixed_severity_issues(self, mock_call_llm):
        """Test execution with mixed severity issues."""
        agent = DesignReviewAgent()
        design_spec = create_test_design_specification()

        mock_call_llm.return_value = {
            "content": create_mock_llm_review_response(
                issues=[
                    {
                        "issue_id": "ISSUE-005",
                        "category": "Security",
                        "severity": "Critical",
                        "description": "Critical security vulnerability requiring immediate attention",
                        "evidence": "Test evidence showing the critical issue",
                        "impact": "High impact requiring immediate remediation effort",
                        "affected_phase": "Design",
                    },
                    {
                        "issue_id": "ISSUE-006",
                        "category": "Architecture",
                        "severity": "High",
                        "description": "High severity architectural design issue found",
                        "evidence": "Test evidence for high severity",
                        "impact": "High impact on system architecture and maintainability",
                        "affected_phase": "Design",
                    },
                    {
                        "issue_id": "ISSUE-007",
                        "category": "Performance",
                        "severity": "Medium",
                        "description": "Medium severity performance issue detected in design",
                        "evidence": "Test evidence for medium severity",
                        "impact": "Moderate impact on system performance and scalability",
                        "affected_phase": "Design",
                    },
                    {
                        "issue_id": "ISSUE-008",
                        "category": "Maintainability",
                        "severity": "Low",
                        "description": "Low severity documentation issue needs attention",
                        "evidence": "Test evidence for low severity",
                        "impact": "Minor impact on documentation quality and completeness",
                        "affected_phase": "Design",
                    },
                ]
            )
        }

        report = agent.execute(design_spec)

        assert report.overall_assessment == "FAIL"  # Critical/High present
        assert report.critical_issue_count == 1
        assert report.high_issue_count == 1
        assert report.medium_issue_count == 1
        assert report.low_issue_count == 1

    @patch("asp.agents.design_review_agent.DesignReviewAgent.call_llm")
    def test_execute_with_circular_deps_design(self, mock_call_llm):
        """Test execution on design with circular dependencies."""
        agent = DesignReviewAgent()
        design_spec = create_design_with_circular_deps()

        mock_call_llm.return_value = {
            "content": create_mock_llm_review_response()
        }

        report = agent.execute(design_spec)

        # Automated check should flag circular dependency
        assert report.automated_checks["no_circular_deps"] is False

    @patch("asp.agents.design_review_agent.DesignReviewAgent.call_llm")
    def test_execute_continues_despite_artifact_write_failure(self, mock_call_llm):
        """Test that execution continues if artifact writing fails."""
        agent = DesignReviewAgent()
        design_spec = create_test_design_specification()

        mock_call_llm.return_value = {
            "content": create_mock_llm_review_response()
        }

        # Mock artifact writing to fail
        with patch(
            "asp.agents.design_review_agent.write_artifact_json",
            side_effect=Exception("Disk full"),
        ):
            # Should complete without raising
            report = agent.execute(design_spec)

        assert isinstance(report, DesignReviewReport)
        # Artifact failure should be logged but not prevent report generation
