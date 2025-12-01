"""
Unit tests for Security Review Agent.

Tests the specialist security review agent including:
- Initialization and configuration
- SQL injection detection
- XSS vulnerability detection
- Authentication and authorization checks
- Sensitive data exposure detection
- API security validation
- Error handling and edge cases

Author: ASP Test Team
Date: 2025-11-18
"""

import json
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest

from asp.agents.base_agent import AgentExecutionError
from asp.agents.reviews.security_review_agent import SecurityReviewAgent
from asp.models.design import (
    APIContract,
    ComponentLogic,
    DataSchema,
    DesignReviewChecklistItem,
    DesignSpecification,
)

# Helper functions for creating test data


def create_test_design_spec_with_security_issues():
    """Create a DesignSpecification with potential security issues."""
    return DesignSpecification(
        task_id="SEC-TEST-001",
        timestamp=datetime.now(),
        api_contracts=[
            APIContract(
                endpoint="/api/users",
                method="POST",
                description="Create user without input validation specified",
                request_schema={"email": "string", "password": "string"},
                response_schema={"user_id": "string"},
                authentication_required=False,  # Potential issue
                error_responses=[],
            ),
            APIContract(
                endpoint="/api/admin",
                method="GET",
                description="Admin endpoint with potential access control issues",
                response_schema={"admin_data": "object"},
                authentication_required=True,
            ),
        ],
        data_schemas=[
            DataSchema(
                table_name="users",
                description="User table with password storage issues",
                columns=[
                    {"name": "id", "type": "INTEGER", "constraints": "PRIMARY KEY"},
                    {"name": "password", "type": "VARCHAR(255)"},  # Not hashed
                    {"name": "credit_card", "type": "VARCHAR(16)"},  # Sensitive data
                ],
            )
        ],
        component_logic=[
            ComponentLogic(
                component_name="AuthenticationService",
                semantic_unit_id="SU-001",
                responsibility="Handle user authentication and session management",
                interfaces=[
                    {
                        "method": "login",
                        "parameters": {"email": "str", "password": "str"},
                    }
                ],
                implementation_notes="Store passwords in plaintext for simplicity",  # Security issue
            )
        ],
        design_review_checklist=[
            DesignReviewChecklistItem(
                category="Security",
                description="Verify input validation for all endpoints",
                validation_criteria="All user inputs must be validated and sanitized",
                severity="Critical",
            ),
            DesignReviewChecklistItem(
                category="Security",
                description="Check password hashing",
                validation_criteria="Passwords must be hashed with bcrypt",
                severity="Critical",
            ),
            DesignReviewChecklistItem(
                category="Architecture",
                description="Check separation of concerns",
                validation_criteria="Components should have single responsibility",
            ),
            DesignReviewChecklistItem(
                category="Performance",
                description="Check query optimization",
                validation_criteria="Database queries should be optimized",
            ),
            DesignReviewChecklistItem(
                category="Maintainability",
                description="Check code organization",
                validation_criteria="Code should be well organized",
            ),
        ],
        architecture_overview="Simple authentication system with user management and admin access",
        technology_stack={
            "language": "Python",
            "framework": "FastAPI",
            "database": "PostgreSQL",
        },
    )


def create_mock_security_response(issues_count=3, suggestions_count=2):
    """Create a mock security review response."""
    return {
        "content": json.dumps(
            {
                "issues_found": [
                    {
                        "issue_id": f"SEC-{i:03d}",
                        "category": "Security",
                        "severity": "Critical" if i == 0 else "High",
                        "title": f"Security issue {i}",
                        "description": f"Description of security issue {i}",
                        "affected_component": "AuthenticationService",
                        "line_number": None,
                        "evidence": f"Evidence for issue {i}",
                        "impact": f"Impact of issue {i}",
                        "affected_phase": "Design",
                    }
                    for i in range(issues_count)
                ],
                "improvement_suggestions": [
                    {
                        "suggestion_id": f"SEC-IMPROVE-{i:03d}",
                        "category": "Security",
                        "priority": "High",
                        "title": f"Security improvement {i}",
                        "description": f"Description of improvement {i}",
                        "affected_component": "AuthenticationService",
                        "implementation_guidance": f"Guidance for improvement {i}",
                        "estimated_effort": "Medium",
                    }
                    for i in range(suggestions_count)
                ],
            }
        )
    }


# =============================================================================
# Initialization Tests
# =============================================================================


class TestSecurityReviewAgentInitialization:
    """Test SecurityReviewAgent initialization."""

    def test_init_with_defaults(self):
        """Test initialization with default parameters."""
        agent = SecurityReviewAgent()

        assert agent is not None
        assert agent.agent_version == "1.0.0"

    def test_init_with_custom_llm_client(self):
        """Test initialization with custom LLM client."""
        mock_llm = Mock()
        agent = SecurityReviewAgent(llm_client=mock_llm)

        assert agent.llm_client == mock_llm
        assert agent.agent_version == "1.0.0"

    def test_init_with_db_path(self):
        """Test initialization with custom database path."""
        test_db_path = "/tmp/test_security_agent.db"
        agent = SecurityReviewAgent(db_path=test_db_path)

        assert agent is not None
        assert agent.agent_version == "1.0.0"


# =============================================================================
# Execute Method Tests
# =============================================================================


class TestSecurityReviewAgentExecute:
    """Test SecurityReviewAgent execute method."""

    @patch.object(SecurityReviewAgent, "load_prompt")
    @patch.object(SecurityReviewAgent, "format_prompt")
    @patch.object(SecurityReviewAgent, "call_llm")
    def test_execute_success(self, mock_call_llm, mock_format_prompt, mock_load_prompt):
        """Test successful security review execution."""
        # Setup
        agent = SecurityReviewAgent()
        design_spec = create_test_design_spec_with_security_issues()

        mock_load_prompt.return_value = "Security review prompt template"
        mock_format_prompt.return_value = "Formatted security review prompt"
        mock_call_llm.return_value = create_mock_security_response(
            issues_count=3, suggestions_count=2
        )

        # Execute
        result = agent.execute(design_spec)

        # Verify
        assert "issues_found" in result
        assert "improvement_suggestions" in result
        assert len(result["issues_found"]) == 3
        assert len(result["improvement_suggestions"]) == 2

        # Verify method calls
        mock_load_prompt.assert_called_once_with("security_review_agent_v1")
        mock_format_prompt.assert_called_once()
        mock_call_llm.assert_called_once()

    @patch.object(SecurityReviewAgent, "load_prompt")
    @patch.object(SecurityReviewAgent, "format_prompt")
    @patch.object(SecurityReviewAgent, "call_llm")
    def test_execute_with_no_issues(
        self, mock_call_llm, mock_format_prompt, mock_load_prompt
    ):
        """Test security review with no issues found."""
        agent = SecurityReviewAgent()
        design_spec = create_test_design_spec_with_security_issues()

        mock_load_prompt.return_value = "Security review prompt template"
        mock_format_prompt.return_value = "Formatted security review prompt"
        mock_call_llm.return_value = create_mock_security_response(
            issues_count=0, suggestions_count=0
        )

        result = agent.execute(design_spec)

        assert len(result["issues_found"]) == 0
        assert len(result["improvement_suggestions"]) == 0

    @patch.object(SecurityReviewAgent, "load_prompt")
    @patch.object(SecurityReviewAgent, "format_prompt")
    @patch.object(SecurityReviewAgent, "call_llm")
    def test_execute_formats_design_spec_correctly(
        self, mock_call_llm, mock_format_prompt, mock_load_prompt
    ):
        """Test that design_spec is formatted correctly for prompt."""
        agent = SecurityReviewAgent()
        design_spec = create_test_design_spec_with_security_issues()

        mock_load_prompt.return_value = "Prompt template"
        mock_format_prompt.return_value = "Formatted prompt"
        mock_call_llm.return_value = create_mock_security_response()

        agent.execute(design_spec)

        # Verify format_prompt was called with JSON-serialized design_spec
        call_args = mock_format_prompt.call_args
        assert "design_specification" in call_args[1]
        # The design_specification should be JSON string
        design_spec_arg = call_args[1]["design_specification"]
        assert isinstance(design_spec_arg, str)
        # Should be valid JSON
        parsed = json.loads(design_spec_arg)
        assert parsed["task_id"] == design_spec.task_id


# =============================================================================
# SQL Injection Detection Tests
# =============================================================================


class TestSQLInjectionDetection:
    """Test SQL injection vulnerability detection."""

    @patch.object(SecurityReviewAgent, "load_prompt")
    @patch.object(SecurityReviewAgent, "format_prompt")
    @patch.object(SecurityReviewAgent, "call_llm")
    def test_detect_sql_injection_in_api_contract(
        self, mock_call_llm, mock_format_prompt, mock_load_prompt
    ):
        """Test detection of SQL injection risk in API endpoints."""
        agent = SecurityReviewAgent()

        # Design spec with SQL injection risk
        design_spec = DesignSpecification(
            task_id="SQL-INJ-001",
            api_contracts=[
                APIContract(
                    endpoint="/api/users/{user_id}",
                    method="GET",
                    description="Get user by ID with SQL injection risk",
                    request_params={"user_id": "string - not validated"},
                    response_schema={"user": "object"},
                )
            ],
            component_logic=[
                ComponentLogic(
                    component_name="UserService",
                    semantic_unit_id="SU-001",
                    responsibility="Fetch users from database with direct SQL",
                    interfaces=[{"method": "get_user"}],
                    implementation_notes="Use string concatenation for SQL queries like: SELECT * FROM users WHERE id = user_id_value",
                )
            ],
            design_review_checklist=[
                DesignReviewChecklistItem(
                    category="Security",
                    description="Check SQL injection prevention",
                    validation_criteria="Use parameterized queries",
                    severity="Critical",
                ),
                DesignReviewChecklistItem(
                    category="Test",
                    description="Test item 1 here",
                    validation_criteria="Validate test 1",
                ),
                DesignReviewChecklistItem(
                    category="Test",
                    description="Test item 2 here",
                    validation_criteria="Validate test 2",
                ),
                DesignReviewChecklistItem(
                    category="Test",
                    description="Test item 3 here",
                    validation_criteria="Validate test 3",
                ),
                DesignReviewChecklistItem(
                    category="Test",
                    description="Test item 4 here",
                    validation_criteria="Validate test 4",
                ),
            ],
            architecture_overview="User management system with database queries for user lookup",
            technology_stack={"language": "Python", "database": "PostgreSQL"},
        )

        # Mock response with SQL injection issue
        mock_load_prompt.return_value = "Prompt"
        mock_format_prompt.return_value = "Formatted"
        mock_call_llm.return_value = {
            "content": json.dumps(
                {
                    "issues_found": [
                        {
                            "issue_id": "SQL-001",
                            "category": "Security",
                            "severity": "Critical",
                            "title": "SQL Injection Vulnerability",
                            "description": "String concatenation used for SQL queries",
                            "affected_component": "UserService",
                            "evidence": "String concatenation in implementation notes",
                            "impact": "Attackers can execute arbitrary SQL",
                            "affected_phase": "Design",
                        }
                    ],
                    "improvement_suggestions": [
                        {
                            "suggestion_id": "SQL-FIX-001",
                            "category": "Security",
                            "priority": "Critical",
                            "title": "Use parameterized queries",
                            "description": "Replace string concatenation with parameterized queries",
                            "affected_component": "UserService",
                            "implementation_guidance": "Use SQLAlchemy or prepared statements",
                            "estimated_effort": "Low",
                        }
                    ],
                }
            )
        }

        result = agent.execute(design_spec)

        # Verify SQL injection issue was detected
        assert len(result["issues_found"]) > 0
        sql_issues = [i for i in result["issues_found"] if "SQL" in i.get("title", "")]
        assert len(sql_issues) > 0


# =============================================================================
# XSS Detection Tests
# =============================================================================


class TestXSSDetection:
    """Test XSS vulnerability detection."""

    @patch.object(SecurityReviewAgent, "load_prompt")
    @patch.object(SecurityReviewAgent, "format_prompt")
    @patch.object(SecurityReviewAgent, "call_llm")
    def test_detect_xss_in_api_response(
        self, mock_call_llm, mock_format_prompt, mock_load_prompt
    ):
        """Test detection of XSS vulnerability in API responses."""
        agent = SecurityReviewAgent()

        design_spec = DesignSpecification(
            task_id="XSS-001",
            api_contracts=[
                APIContract(
                    endpoint="/api/comments",
                    method="POST",
                    description="Post comment without output sanitization",
                    request_schema={"comment_text": "string - unescaped HTML"},
                    response_schema={"comment": "string - raw HTML rendered"},
                )
            ],
            component_logic=[
                ComponentLogic(
                    component_name="CommentService",
                    semantic_unit_id="SU-001",
                    responsibility="Handle user comments and display",
                    interfaces=[{"method": "post_comment"}],
                    implementation_notes="Render user comments directly without escaping HTML tags",
                )
            ],
            design_review_checklist=[
                DesignReviewChecklistItem(
                    category="Security",
                    description="Check XSS prevention",
                    validation_criteria="Escape HTML in user content",
                    severity="Critical",
                ),
                DesignReviewChecklistItem(
                    category="Test",
                    description="Test item 1 here",
                    validation_criteria="Validate test 1",
                ),
                DesignReviewChecklistItem(
                    category="Test",
                    description="Test item 2 here",
                    validation_criteria="Validate test 2",
                ),
                DesignReviewChecklistItem(
                    category="Test",
                    description="Test item 3 here",
                    validation_criteria="Validate test 3",
                ),
                DesignReviewChecklistItem(
                    category="Test",
                    description="Test item 4 here",
                    validation_criteria="Validate test 4",
                ),
            ],
            architecture_overview="Comment system that displays user-generated content",
            technology_stack={"language": "Python", "framework": "FastAPI"},
        )

        mock_load_prompt.return_value = "Prompt"
        mock_format_prompt.return_value = "Formatted"
        mock_call_llm.return_value = {
            "content": json.dumps(
                {
                    "issues_found": [
                        {
                            "issue_id": "XSS-001",
                            "category": "Security",
                            "severity": "Critical",
                            "title": "Cross-Site Scripting (XSS) Vulnerability",
                            "description": "User input rendered without HTML escaping",
                            "affected_component": "CommentService",
                            "evidence": "Raw HTML rendering in implementation",
                            "impact": "Attackers can inject malicious scripts",
                            "affected_phase": "Design",
                        }
                    ],
                    "improvement_suggestions": [],
                }
            )
        }

        result = agent.execute(design_spec)

        xss_issues = [i for i in result["issues_found"] if "XSS" in i.get("title", "")]
        assert len(xss_issues) > 0


# =============================================================================
# Authentication & Authorization Tests
# =============================================================================


class TestAuthenticationAuthorization:
    """Test authentication and authorization checks."""

    @patch.object(SecurityReviewAgent, "load_prompt")
    @patch.object(SecurityReviewAgent, "format_prompt")
    @patch.object(SecurityReviewAgent, "call_llm")
    def test_detect_missing_authentication(
        self, mock_call_llm, mock_format_prompt, mock_load_prompt
    ):
        """Test detection of missing authentication on sensitive endpoints."""
        agent = SecurityReviewAgent()

        design_spec = DesignSpecification(
            task_id="AUTH-001",
            api_contracts=[
                APIContract(
                    endpoint="/api/admin/users",
                    method="DELETE",
                    description="Delete user - admin only but no auth specified",
                    authentication_required=False,  # Security issue
                    response_schema={"status": "string"},
                )
            ],
            component_logic=[
                ComponentLogic(
                    component_name="AdminService",
                    semantic_unit_id="SU-001",
                    responsibility="Admin operations for user management",
                    interfaces=[{"method": "delete_user"}],
                    implementation_notes="Delete users from database without authorization checks",
                )
            ],
            design_review_checklist=[
                DesignReviewChecklistItem(
                    category="Security",
                    description="Verify authentication on all endpoints",
                    validation_criteria="Sensitive endpoints must require authentication",
                    severity="Critical",
                ),
                DesignReviewChecklistItem(
                    category="Test",
                    description="Test item 1 here",
                    validation_criteria="Validate test 1",
                ),
                DesignReviewChecklistItem(
                    category="Test",
                    description="Test item 2 here",
                    validation_criteria="Validate test 2",
                ),
                DesignReviewChecklistItem(
                    category="Test",
                    description="Test item 3 here",
                    validation_criteria="Validate test 3",
                ),
                DesignReviewChecklistItem(
                    category="Test",
                    description="Test item 4 here",
                    validation_criteria="Validate test 4",
                ),
            ],
            architecture_overview="Admin system for managing users without proper auth",
            technology_stack={"language": "Python", "framework": "FastAPI"},
        )

        mock_load_prompt.return_value = "Prompt"
        mock_format_prompt.return_value = "Formatted"
        mock_call_llm.return_value = {
            "content": json.dumps(
                {
                    "issues_found": [
                        {
                            "issue_id": "AUTH-001",
                            "category": "Security",
                            "severity": "Critical",
                            "title": "Missing Authentication on Admin Endpoint",
                            "description": "DELETE /api/admin/users has no authentication",
                            "affected_component": "AdminService",
                            "evidence": "authentication_required=False on admin endpoint",
                            "impact": "Unauthorized users can delete users",
                            "affected_phase": "Design",
                        }
                    ],
                    "improvement_suggestions": [],
                }
            )
        }

        result = agent.execute(design_spec)

        auth_issues = [
            i for i in result["issues_found"] if "Authentication" in i.get("title", "")
        ]
        assert len(auth_issues) > 0

    @patch.object(SecurityReviewAgent, "load_prompt")
    @patch.object(SecurityReviewAgent, "format_prompt")
    @patch.object(SecurityReviewAgent, "call_llm")
    def test_detect_weak_password_storage(
        self, mock_call_llm, mock_format_prompt, mock_load_prompt
    ):
        """Test detection of plaintext password storage."""
        agent = SecurityReviewAgent()

        design_spec = DesignSpecification(
            task_id="PWD-001",
            data_schemas=[
                DataSchema(
                    table_name="users",
                    description="User table storing passwords in plaintext",
                    columns=[
                        {"name": "id", "type": "INTEGER"},
                        {
                            "name": "password",
                            "type": "VARCHAR(255)",
                        },  # Not password_hash
                    ],
                )
            ],
            component_logic=[
                ComponentLogic(
                    component_name="AuthService",
                    semantic_unit_id="SU-001",
                    responsibility="User authentication with password verification",
                    interfaces=[{"method": "verify_password"}],
                    implementation_notes="Store passwords in plaintext for easy debugging",
                )
            ],
            design_review_checklist=[
                DesignReviewChecklistItem(
                    category="Security",
                    description="Verify password hashing",
                    validation_criteria="Passwords must be hashed with bcrypt",
                    severity="Critical",
                ),
                DesignReviewChecklistItem(
                    category="Test",
                    description="Test item 1 here",
                    validation_criteria="Validate test 1",
                ),
                DesignReviewChecklistItem(
                    category="Test",
                    description="Test item 2 here",
                    validation_criteria="Validate test 2",
                ),
                DesignReviewChecklistItem(
                    category="Test",
                    description="Test item 3 here",
                    validation_criteria="Validate test 3",
                ),
                DesignReviewChecklistItem(
                    category="Test",
                    description="Test item 4 here",
                    validation_criteria="Validate test 4",
                ),
            ],
            architecture_overview="Authentication system with plaintext password storage",
            technology_stack={"language": "Python", "database": "PostgreSQL"},
        )

        mock_load_prompt.return_value = "Prompt"
        mock_format_prompt.return_value = "Formatted"
        mock_call_llm.return_value = {
            "content": json.dumps(
                {
                    "issues_found": [
                        {
                            "issue_id": "PWD-001",
                            "category": "Security",
                            "severity": "Critical",
                            "title": "Plaintext Password Storage",
                            "description": "Passwords stored without hashing",
                            "affected_component": "AuthService",
                            "evidence": "password column instead of password_hash",
                            "impact": "Password exposure if database compromised",
                            "affected_phase": "Design",
                        }
                    ],
                    "improvement_suggestions": [
                        {
                            "suggestion_id": "PWD-FIX-001",
                            "category": "Security",
                            "priority": "Critical",
                            "title": "Implement password hashing",
                            "description": "Use bcrypt to hash passwords",
                            "affected_component": "AuthService",
                            "implementation_guidance": "Use bcrypt with cost factor 12+",
                            "estimated_effort": "Low",
                        }
                    ],
                }
            )
        }

        result = agent.execute(design_spec)

        pwd_issues = [
            i for i in result["issues_found"] if "Password" in i.get("title", "")
        ]
        assert len(pwd_issues) > 0


# =============================================================================
# Sensitive Data Exposure Tests
# =============================================================================


class TestSensitiveDataExposure:
    """Test sensitive data exposure detection."""

    @patch.object(SecurityReviewAgent, "load_prompt")
    @patch.object(SecurityReviewAgent, "format_prompt")
    @patch.object(SecurityReviewAgent, "call_llm")
    def test_detect_sensitive_data_in_logs(
        self, mock_call_llm, mock_format_prompt, mock_load_prompt
    ):
        """Test detection of sensitive data logging."""
        agent = SecurityReviewAgent()

        design_spec = DesignSpecification(
            task_id="DATA-001",
            component_logic=[
                ComponentLogic(
                    component_name="PaymentService",
                    semantic_unit_id="SU-001",
                    responsibility="Process payment transactions",
                    interfaces=[{"method": "process_payment"}],
                    implementation_notes="Log all payment data including credit card numbers for debugging",
                )
            ],
            design_review_checklist=[
                DesignReviewChecklistItem(
                    category="Security",
                    description="Check sensitive data handling",
                    validation_criteria="No sensitive data in logs",
                    severity="Critical",
                ),
                DesignReviewChecklistItem(
                    category="Test",
                    description="Test item 1 here",
                    validation_criteria="Validate test 1",
                ),
                DesignReviewChecklistItem(
                    category="Test",
                    description="Test item 2 here",
                    validation_criteria="Validate test 2",
                ),
                DesignReviewChecklistItem(
                    category="Test",
                    description="Test item 3 here",
                    validation_criteria="Validate test 3",
                ),
                DesignReviewChecklistItem(
                    category="Test",
                    description="Test item 4 here",
                    validation_criteria="Validate test 4",
                ),
            ],
            architecture_overview="Payment processing system with comprehensive logging for debugging and monitoring",
            technology_stack={"language": "Python"},
        )

        mock_load_prompt.return_value = "Prompt"
        mock_format_prompt.return_value = "Formatted"
        mock_call_llm.return_value = {
            "content": json.dumps(
                {
                    "issues_found": [
                        {
                            "issue_id": "DATA-001",
                            "category": "Security",
                            "severity": "Critical",
                            "title": "Sensitive Data in Logs",
                            "description": "Credit card numbers logged",
                            "affected_component": "PaymentService",
                            "evidence": "Implementation notes mention logging credit cards",
                            "impact": "PCI DSS violation, data breach risk",
                            "affected_phase": "Design",
                        }
                    ],
                    "improvement_suggestions": [],
                }
            )
        }

        result = agent.execute(design_spec)

        data_issues = [
            i
            for i in result["issues_found"]
            if "Sensitive Data" in i.get("title", "") or "Data" in i.get("title", "")
        ]
        assert len(data_issues) > 0


# =============================================================================
# Error Handling Tests
# =============================================================================


class TestSecurityReviewAgentErrorHandling:
    """Test error handling in SecurityReviewAgent."""

    @patch.object(SecurityReviewAgent, "load_prompt")
    @patch.object(SecurityReviewAgent, "format_prompt")
    @patch.object(SecurityReviewAgent, "call_llm")
    def test_execute_handles_invalid_json_response(
        self, mock_call_llm, mock_format_prompt, mock_load_prompt
    ):
        """Test handling of invalid JSON in LLM response."""
        agent = SecurityReviewAgent()
        design_spec = create_test_design_spec_with_security_issues()

        mock_load_prompt.return_value = "Prompt"
        mock_format_prompt.return_value = "Formatted"
        mock_call_llm.return_value = {"content": "Not valid JSON {{{"}

        with pytest.raises(AgentExecutionError) as exc_info:
            agent.execute(design_spec)

        assert "Failed to parse security review response" in str(exc_info.value)

    @patch.object(SecurityReviewAgent, "load_prompt")
    @patch.object(SecurityReviewAgent, "format_prompt")
    @patch.object(SecurityReviewAgent, "call_llm")
    def test_execute_handles_missing_issues_found_field(
        self, mock_call_llm, mock_format_prompt, mock_load_prompt
    ):
        """Test handling of response missing issues_found field."""
        agent = SecurityReviewAgent()
        design_spec = create_test_design_spec_with_security_issues()

        mock_load_prompt.return_value = "Prompt"
        mock_format_prompt.return_value = "Formatted"
        mock_call_llm.return_value = {
            "content": json.dumps(
                {
                    "improvement_suggestions": []
                    # Missing issues_found
                }
            )
        }

        with pytest.raises(AgentExecutionError) as exc_info:
            agent.execute(design_spec)

        assert "missing 'issues_found' field" in str(exc_info.value)

    @patch.object(SecurityReviewAgent, "load_prompt")
    @patch.object(SecurityReviewAgent, "format_prompt")
    @patch.object(SecurityReviewAgent, "call_llm")
    def test_execute_handles_llm_failure(
        self, mock_call_llm, mock_format_prompt, mock_load_prompt
    ):
        """Test handling of LLM call failure."""
        agent = SecurityReviewAgent()
        design_spec = create_test_design_spec_with_security_issues()

        mock_load_prompt.return_value = "Prompt"
        mock_format_prompt.return_value = "Formatted"
        mock_call_llm.side_effect = Exception("LLM API error")

        with pytest.raises(AgentExecutionError) as exc_info:
            agent.execute(design_spec)

        assert "Security review failed" in str(exc_info.value)


# =============================================================================
# Edge Cases and Integration Tests
# =============================================================================


class TestSecurityReviewAgentEdgeCases:
    """Test edge cases for SecurityReviewAgent."""

    @patch.object(SecurityReviewAgent, "load_prompt")
    @patch.object(SecurityReviewAgent, "format_prompt")
    @patch.object(SecurityReviewAgent, "call_llm")
    def test_execute_with_minimal_design_spec(
        self, mock_call_llm, mock_format_prompt, mock_load_prompt
    ):
        """Test security review with minimal design specification."""
        agent = SecurityReviewAgent()

        # Minimal design spec
        design_spec = DesignSpecification(
            task_id="MIN-001",
            component_logic=[
                ComponentLogic(
                    component_name="MinimalComponent",
                    semantic_unit_id="SU-001",
                    responsibility="Minimal component for testing purposes only",
                    interfaces=[{"method": "test"}],
                    implementation_notes="Minimal implementation for testing",
                )
            ],
            design_review_checklist=[
                DesignReviewChecklistItem(
                    category="Security",
                    description="Check security here",
                    validation_criteria="Validate security",
                    severity="Critical",
                ),
                DesignReviewChecklistItem(
                    category="Test",
                    description="Test item 1 here",
                    validation_criteria="Validate test 1",
                ),
                DesignReviewChecklistItem(
                    category="Test",
                    description="Test item 2 here",
                    validation_criteria="Validate test 2",
                ),
                DesignReviewChecklistItem(
                    category="Test",
                    description="Test item 3 here",
                    validation_criteria="Validate test 3",
                ),
                DesignReviewChecklistItem(
                    category="Test",
                    description="Test item 4 here",
                    validation_criteria="Validate test 4",
                ),
            ],
            architecture_overview="Minimal architecture for testing security review agent",
            technology_stack={"language": "Python"},
        )

        mock_load_prompt.return_value = "Prompt"
        mock_format_prompt.return_value = "Formatted"
        mock_call_llm.return_value = create_mock_security_response(
            issues_count=0, suggestions_count=1
        )

        result = agent.execute(design_spec)

        assert "issues_found" in result
        assert "improvement_suggestions" in result

    @patch.object(SecurityReviewAgent, "load_prompt")
    @patch.object(SecurityReviewAgent, "format_prompt")
    @patch.object(SecurityReviewAgent, "call_llm")
    def test_execute_with_large_design_spec(
        self, mock_call_llm, mock_format_prompt, mock_load_prompt
    ):
        """Test security review with large design specification."""
        agent = SecurityReviewAgent()

        # Large design spec with many components
        api_contracts = [
            APIContract(
                endpoint=f"/api/resource{i}",
                method="GET",
                description=f"Get resource number {i} from system",
                response_schema={"data": "object"},
            )
            for i in range(20)
        ]

        components = [
            ComponentLogic(
                component_name=f"Component{i}",
                semantic_unit_id=f"SU-{i:03d}",
                responsibility=f"Handle operations for component number {i}",
                interfaces=[{"method": f"method_{i}"}],
                implementation_notes=f"Implementation for component number {i}",
            )
            for i in range(30)
        ]

        design_spec = DesignSpecification(
            task_id="LARGE-001",
            api_contracts=api_contracts,
            component_logic=components,
            design_review_checklist=[
                DesignReviewChecklistItem(
                    category="Security",
                    description="Security check here",
                    validation_criteria="Validate security",
                    severity="Critical",
                ),
                DesignReviewChecklistItem(
                    category="Test",
                    description="Test item 1 here",
                    validation_criteria="Validate test 1",
                ),
                DesignReviewChecklistItem(
                    category="Test",
                    description="Test item 2 here",
                    validation_criteria="Validate test 2",
                ),
                DesignReviewChecklistItem(
                    category="Test",
                    description="Test item 3 here",
                    validation_criteria="Validate test 3",
                ),
                DesignReviewChecklistItem(
                    category="Test",
                    description="Test item 4 here",
                    validation_criteria="Validate test 4",
                ),
            ],
            architecture_overview="Large-scale microservices architecture with many components and endpoints",
            technology_stack={"language": "Python", "framework": "FastAPI"},
        )

        mock_load_prompt.return_value = "Prompt"
        mock_format_prompt.return_value = "Formatted"
        mock_call_llm.return_value = create_mock_security_response(
            issues_count=10, suggestions_count=5
        )

        result = agent.execute(design_spec)

        assert len(result["issues_found"]) == 10
        assert len(result["improvement_suggestions"]) == 5
