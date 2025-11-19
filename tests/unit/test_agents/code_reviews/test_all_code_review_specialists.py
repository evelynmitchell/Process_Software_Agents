"""
Unit tests for all 6 Code Review Specialist Agents.

Tests cover all specialist agents:
- CodeQualityReviewAgent
- CodeSecurityReviewAgent
- CodePerformanceReviewAgent
- TestCoverageReviewAgent
- DocumentationReviewAgent
- BestPracticesReviewAgent

Each agent is tested for:
- Initialization and configuration
- Successful review execution (mocked LLM)
- JSON response parsing
- Issue detection
- Improvement suggestions
- Error handling
- Edge cases

Author: ASP Test Team
Date: November 19, 2025
"""

import json
import pytest
from datetime import datetime
from unittest.mock import Mock, MagicMock, patch
from pathlib import Path

from asp.agents.base_agent import AgentExecutionError
from asp.agents.code_reviews import (
    BestPracticesReviewAgent,
    CodePerformanceReviewAgent,
    CodeQualityReviewAgent,
    CodeSecurityReviewAgent,
    DocumentationReviewAgent,
    TestCoverageReviewAgent,
)
from asp.models.code import GeneratedCode, GeneratedFile


# =============================================================================
# Test Fixtures
# =============================================================================


def create_test_generated_code_with_issues():
    """Create a GeneratedCode with potential issues for specialists to detect."""
    return GeneratedCode(
        task_id="SPEC-TEST-001",
        files=[
            GeneratedFile(
                file_path="src/api/auth.py",
                content="""
# Missing module docstring
from fastapi import APIRouter

router = APIRouter()

def login(username, password):  # Missing type hints, no docstring
    query = f"SELECT * FROM users WHERE username = '{username}'"  # SQL injection
    if password == "admin":  # Weak password check
        return {"token": "hardcoded_secret_123"}  # Hardcoded secret
    return None
""",
                file_type="source",
                description="Authentication API module with multiple issues",
            ),
            GeneratedFile(
                file_path="src/services/payment.py",
                content="""
def process_payment(amount, card_details):
    # No tests for this critical function
    # N+1 query problem
    for order in get_orders():
        user = db.query(User).get(order.user_id)  # N+1

    # No error handling
    charge_card(card_details, amount)
    return True
""",
                file_type="source",
                description="Payment processing service with performance and testing issues",
            ),
            GeneratedFile(
                file_path="tests/test_auth.py",
                content="""
# Minimal test file
def test_login():
    assert login("admin", "admin") is not None
# Missing edge cases, error handling tests
""",
                file_type="test",
                description="Incomplete test coverage for authentication",
            ),
        ],
        dependencies=["fastapi", "sqlalchemy"],
        total_files=3,
        total_lines_of_code=35,
        file_structure={
            "src/api": ["auth.py"],
            "src/services": ["payment.py"],
            "tests": ["test_auth.py"],
        },
        implementation_notes=(
            "Authentication API module with basic login endpoint using FastAPI router. "
            "Includes SQL-based user authentication with password checking. "
            "Payment processing service handles card charges for orders. "
            "Basic test coverage provided for login functionality with minimal edge cases."
        ),
    )


def create_mock_llm_response(issues_found, suggestions):
    """Create a mock LLM response with issues and suggestions."""
    return {
        "content": json.dumps({
            "issues_found": issues_found,
            "improvement_suggestions": suggestions,
        }),
        "usage": {
            "input_tokens": 100,
            "output_tokens": 50,
        },
        "model": "claude-sonnet-4",
        "cost": 0.001,
    }


# =============================================================================
# Code Quality Review Agent Tests
# =============================================================================


class TestCodeQualityReviewAgent:
    """Tests for CodeQualityReviewAgent."""

    def test_initialization(self):
        """Test agent initializes correctly."""
        agent = CodeQualityReviewAgent()
        assert agent is not None
        assert agent.agent_version == "1.0.0"
        assert agent.agent_name == "CodeQualityReviewAgent"

    def test_initialization_with_mock_llm(self):
        """Test agent can be initialized with mock LLM."""
        mock_llm = Mock()
        agent = CodeQualityReviewAgent(llm_client=mock_llm)
        assert agent._llm_client == mock_llm

    def test_execute_success(self):
        """Test successful code quality review."""
        mock_llm = Mock()
        mock_llm.return_value = create_mock_llm_response(
            issues_found=[
                {
                    "issue_id": "QUAL-001",
                    "category": "Code Quality",
                    "severity": "High",
                    "description": "Function missing type hints",
                    "evidence": "src/api/auth.py:6",
                    "impact": "Reduces code clarity and IDE support",
                    "file_path": "src/api/auth.py",
                    "line_number": 6,
                }
            ],
            suggestions=[
                {
                    "suggestion_id": "QUAL-IMP-001",
                    "category": "Code Quality",
                    "priority": "High",
                    "description": "Add type hints to all functions",
                    "implementation_notes": "Use Python type hints for parameters and returns",
                }
            ],
        )

        agent = CodeQualityReviewAgent(llm_client=mock_llm)
        generated_code = create_test_generated_code_with_issues()

        result = agent.execute(generated_code)

        assert "issues_found" in result
        assert "improvement_suggestions" in result
        assert len(result["issues_found"]) == 1
        assert len(result["improvement_suggestions"]) == 1
        assert result["issues_found"][0]["category"] == "Code Quality"

    def test_execute_with_no_issues(self):
        """Test review with clean code (no issues)."""
        mock_llm = Mock()
        mock_llm.return_value = create_mock_llm_response(
            issues_found=[],
            suggestions=[],
        )

        agent = CodeQualityReviewAgent(llm_client=mock_llm)
        generated_code = create_test_generated_code_with_issues()

        result = agent.execute(generated_code)

        assert result["issues_found"] == []
        assert result["improvement_suggestions"] == []

    def test_execute_handles_llm_failure(self):
        """Test error handling when LLM fails."""
        mock_llm = Mock()
        mock_llm.side_effect = Exception("LLM call failed")

        agent = CodeQualityReviewAgent(llm_client=mock_llm)
        generated_code = create_test_generated_code_with_issues()

        with pytest.raises(AgentExecutionError, match="CodeQualityReviewAgent failed"):
            agent.execute(generated_code)

    def test_execute_handles_invalid_json(self):
        """Test error handling when LLM returns invalid JSON."""
        mock_llm = Mock()
        mock_llm.return_value = {"content": "not valid json"}

        agent = CodeQualityReviewAgent(llm_client=mock_llm)
        generated_code = create_test_generated_code_with_issues()

        with pytest.raises(AgentExecutionError, match="Failed to parse LLM response as JSON"):
            agent.execute(generated_code)


# =============================================================================
# Code Security Review Agent Tests
# =============================================================================


class TestCodeSecurityReviewAgent:
    """Tests for CodeSecurityReviewAgent."""

    def test_initialization(self):
        """Test agent initializes correctly."""
        agent = CodeSecurityReviewAgent()
        assert agent is not None
        assert agent.agent_version == "1.0.0"

    def test_execute_detects_sql_injection(self):
        """Test detection of SQL injection vulnerability."""
        mock_llm = Mock()
        mock_llm.return_value = create_mock_llm_response(
            issues_found=[
                {
                    "issue_id": "SEC-001",
                    "category": "Security",
                    "severity": "Critical",
                    "description": "SQL injection via string formatting",
                    "evidence": "src/api/auth.py:7",
                    "impact": "Attacker can execute arbitrary SQL",
                    "file_path": "src/api/auth.py",
                    "line_number": 7,
                }
            ],
            suggestions=[
                {
                    "suggestion_id": "SEC-IMP-001",
                    "category": "Security",
                    "priority": "High",
                    "description": "Use parameterized queries",
                    "implementation_notes": "Replace f-string with ORM or prepared statements",
                }
            ],
        )

        agent = CodeSecurityReviewAgent(llm_client=mock_llm)
        generated_code = create_test_generated_code_with_issues()

        result = agent.execute(generated_code)

        assert len(result["issues_found"]) == 1
        assert result["issues_found"][0]["severity"] == "Critical"
        assert "SQL injection" in result["issues_found"][0]["description"]

    def test_execute_detects_hardcoded_secrets(self):
        """Test detection of hardcoded secrets."""
        mock_llm = Mock()
        mock_llm.return_value = create_mock_llm_response(
            issues_found=[
                {
                    "issue_id": "SEC-002",
                    "category": "Security",
                    "severity": "Critical",
                    "description": "Hardcoded secret token in code",
                    "evidence": "src/api/auth.py:9",
                    "impact": "Secret exposed in source code",
                    "file_path": "src/api/auth.py",
                    "line_number": 9,
                }
            ],
            suggestions=[],
        )

        agent = CodeSecurityReviewAgent(llm_client=mock_llm)
        generated_code = create_test_generated_code_with_issues()

        result = agent.execute(generated_code)

        assert len(result["issues_found"]) == 1
        assert "hardcoded" in result["issues_found"][0]["description"].lower()


# =============================================================================
# Code Performance Review Agent Tests
# =============================================================================


class TestCodePerformanceReviewAgent:
    """Tests for CodePerformanceReviewAgent."""

    def test_initialization(self):
        """Test agent initializes correctly."""
        agent = CodePerformanceReviewAgent()
        assert agent is not None
        assert agent.agent_version == "1.0.0"

    def test_execute_detects_n_plus_one(self):
        """Test detection of N+1 query problem."""
        mock_llm = Mock()
        mock_llm.return_value = create_mock_llm_response(
            issues_found=[
                {
                    "issue_id": "PERF-001",
                    "category": "Performance",
                    "severity": "Critical",
                    "description": "N+1 query problem in loop",
                    "evidence": "src/services/payment.py:5",
                    "impact": "1000 orders = 1000 database queries",
                    "file_path": "src/services/payment.py",
                    "line_number": 5,
                }
            ],
            suggestions=[
                {
                    "suggestion_id": "PERF-IMP-001",
                    "category": "Performance",
                    "priority": "High",
                    "description": "Use eager loading or batch query",
                    "implementation_notes": "Use joinedload or fetch all users in one query",
                }
            ],
        )

        agent = CodePerformanceReviewAgent(llm_client=mock_llm)
        generated_code = create_test_generated_code_with_issues()

        result = agent.execute(generated_code)

        assert len(result["issues_found"]) == 1
        assert "N+1" in result["issues_found"][0]["description"] or "N plus 1" in result["issues_found"][0]["description"].lower()


# =============================================================================
# Test Coverage Review Agent Tests
# =============================================================================


class TestTestCoverageReviewAgent:
    """Tests for TestCoverageReviewAgent."""

    def test_initialization(self):
        """Test agent initializes correctly."""
        agent = TestCoverageReviewAgent()
        assert agent is not None
        assert agent.agent_version == "1.0.0"

    def test_execute_detects_missing_tests(self):
        """Test detection of missing test coverage."""
        mock_llm = Mock()
        mock_llm.return_value = create_mock_llm_response(
            issues_found=[
                {
                    "issue_id": "TEST-001",
                    "category": "Testing",
                    "severity": "Critical",
                    "description": "No tests for payment processing function",
                    "evidence": "src/services/payment.py:process_payment (no tests found)",
                    "impact": "Payment bugs could cause financial losses",
                    "file_path": "src/services/payment.py",
                    "line_number": 1,
                }
            ],
            suggestions=[
                {
                    "suggestion_id": "TEST-IMP-001",
                    "category": "Testing",
                    "priority": "High",
                    "description": "Add comprehensive tests for payment processing",
                    "implementation_notes": "Test success, failure, edge cases, refunds",
                }
            ],
        )

        agent = TestCoverageReviewAgent(llm_client=mock_llm)
        generated_code = create_test_generated_code_with_issues()

        result = agent.execute(generated_code)

        assert len(result["issues_found"]) == 1
        assert "tests" in result["issues_found"][0]["description"].lower()

    def test_execute_detects_missing_edge_cases(self):
        """Test detection of missing edge case tests."""
        mock_llm = Mock()
        mock_llm.return_value = create_mock_llm_response(
            issues_found=[
                {
                    "issue_id": "TEST-002",
                    "category": "Testing",
                    "severity": "High",
                    "description": "Missing edge case tests for authentication",
                    "evidence": "tests/test_auth.py (no tests for invalid credentials)",
                    "impact": "Edge cases not validated",
                    "file_path": "tests/test_auth.py",
                }
            ],
            suggestions=[],
        )

        agent = TestCoverageReviewAgent(llm_client=mock_llm)
        generated_code = create_test_generated_code_with_issues()

        result = agent.execute(generated_code)

        assert len(result["issues_found"]) == 1
        assert "edge case" in result["issues_found"][0]["description"].lower()


# =============================================================================
# Documentation Review Agent Tests
# =============================================================================


class TestDocumentationReviewAgent:
    """Tests for DocumentationReviewAgent."""

    def test_initialization(self):
        """Test agent initializes correctly."""
        agent = DocumentationReviewAgent()
        assert agent is not None
        assert agent.agent_version == "1.0.0"

    def test_execute_detects_missing_docstrings(self):
        """Test detection of missing docstrings."""
        mock_llm = Mock()
        mock_llm.return_value = create_mock_llm_response(
            issues_found=[
                {
                    "issue_id": "DOC-001",
                    "category": "Documentation",
                    "severity": "High",
                    "description": "Function login missing docstring",
                    "evidence": "src/api/auth.py:6",
                    "impact": "Function purpose and parameters unclear",
                    "file_path": "src/api/auth.py",
                    "line_number": 6,
                }
            ],
            suggestions=[
                {
                    "suggestion_id": "DOC-IMP-001",
                    "category": "Documentation",
                    "priority": "High",
                    "description": "Add docstring to login function",
                    "implementation_notes": "Include parameters, returns, raises sections",
                }
            ],
        )

        agent = DocumentationReviewAgent(llm_client=mock_llm)
        generated_code = create_test_generated_code_with_issues()

        result = agent.execute(generated_code)

        assert len(result["issues_found"]) == 1
        assert "docstring" in result["issues_found"][0]["description"].lower()

    def test_execute_detects_missing_module_docs(self):
        """Test detection of missing module-level documentation."""
        mock_llm = Mock()
        mock_llm.return_value = create_mock_llm_response(
            issues_found=[
                {
                    "issue_id": "DOC-002",
                    "category": "Documentation",
                    "severity": "Medium",
                    "description": "Module missing docstring",
                    "evidence": "src/api/auth.py:1",
                    "impact": "Module purpose unclear",
                    "file_path": "src/api/auth.py",
                    "line_number": 1,
                }
            ],
            suggestions=[],
        )

        agent = DocumentationReviewAgent(llm_client=mock_llm)
        generated_code = create_test_generated_code_with_issues()

        result = agent.execute(generated_code)

        assert len(result["issues_found"]) == 1


# =============================================================================
# Best Practices Review Agent Tests
# =============================================================================


class TestBestPracticesReviewAgent:
    """Tests for BestPracticesReviewAgent."""

    def test_initialization(self):
        """Test agent initializes correctly."""
        agent = BestPracticesReviewAgent()
        assert agent is not None
        assert agent.agent_version == "1.0.0"

    def test_execute_detects_anti_patterns(self):
        """Test detection of anti-patterns and non-Pythonic code."""
        mock_llm = Mock()
        mock_llm.return_value = create_mock_llm_response(
            issues_found=[
                {
                    "issue_id": "BP-001",
                    "category": "Best Practices",
                    "severity": "High",
                    "description": "Bare except clause catches all exceptions",
                    "evidence": "src/services/payment.py:8",
                    "impact": "Cannot interrupt program, hides bugs",
                    "file_path": "src/services/payment.py",
                    "line_number": 8,
                }
            ],
            suggestions=[
                {
                    "suggestion_id": "BP-IMP-001",
                    "category": "Best Practices",
                    "priority": "High",
                    "description": "Catch specific exceptions instead of bare except",
                    "implementation_notes": "Use except SpecificException instead of except:",
                }
            ],
        )

        agent = BestPracticesReviewAgent(llm_client=mock_llm)
        generated_code = create_test_generated_code_with_issues()

        result = agent.execute(generated_code)

        assert len(result["issues_found"]) == 1
        assert "except" in result["issues_found"][0]["description"].lower()

    def test_execute_detects_framework_misuse(self):
        """Test detection of framework misuse."""
        mock_llm = Mock()
        mock_llm.return_value = create_mock_llm_response(
            issues_found=[
                {
                    "issue_id": "BP-002",
                    "category": "Best Practices",
                    "severity": "Medium",
                    "description": "Not using FastAPI dependency injection",
                    "evidence": "src/api/auth.py:6",
                    "impact": "Tighter coupling, harder to test",
                    "file_path": "src/api/auth.py",
                    "line_number": 6,
                }
            ],
            suggestions=[],
        )

        agent = BestPracticesReviewAgent(llm_client=mock_llm)
        generated_code = create_test_generated_code_with_issues()

        result = agent.execute(generated_code)

        assert len(result["issues_found"]) == 1


# =============================================================================
# Cross-Agent Tests
# =============================================================================


class TestAllSpecialists:
    """Cross-cutting tests for all specialist agents."""

    @pytest.mark.parametrize(
        "agent_class",
        [
            CodeQualityReviewAgent,
            CodeSecurityReviewAgent,
            CodePerformanceReviewAgent,
            TestCoverageReviewAgent,
            DocumentationReviewAgent,
            BestPracticesReviewAgent,
        ],
    )
    def test_all_agents_have_version(self, agent_class):
        """Test that all agents have version attribute."""
        agent = agent_class()
        assert hasattr(agent, "agent_version")
        assert agent.agent_version == "1.0.0"

    @pytest.mark.parametrize(
        "agent_class",
        [
            CodeQualityReviewAgent,
            CodeSecurityReviewAgent,
            CodePerformanceReviewAgent,
            TestCoverageReviewAgent,
            DocumentationReviewAgent,
            BestPracticesReviewAgent,
        ],
    )
    def test_all_agents_have_execute_method(self, agent_class):
        """Test that all agents have execute method."""
        agent = agent_class()
        assert hasattr(agent, "execute")
        assert callable(agent.execute)

    @pytest.mark.parametrize(
        "agent_class",
        [
            CodeQualityReviewAgent,
            CodeSecurityReviewAgent,
            CodePerformanceReviewAgent,
            TestCoverageReviewAgent,
            DocumentationReviewAgent,
            BestPracticesReviewAgent,
        ],
    )
    def test_all_agents_return_dict_with_required_keys(self, agent_class):
        """Test that all agents return dict with issues_found and improvement_suggestions."""
        mock_llm = Mock()
        mock_llm.return_value = create_mock_llm_response(
            issues_found=[],
            suggestions=[],
        )

        agent = agent_class(llm_client=mock_llm)
        generated_code = create_test_generated_code_with_issues()

        result = agent.execute(generated_code)

        assert isinstance(result, dict)
        assert "issues_found" in result
        assert "improvement_suggestions" in result
        assert isinstance(result["issues_found"], list)
        assert isinstance(result["improvement_suggestions"], list)
