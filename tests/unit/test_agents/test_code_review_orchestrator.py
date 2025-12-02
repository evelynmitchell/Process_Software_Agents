"""
Unit tests for Code Review Orchestrator.

Tests cover:
- Initialization of all 6 specialist agents
- Orchestrator execute with mocked specialists
- Parallel specialist execution
- Result aggregation and deduplication
- Issue ID normalization
- Automated checks
- Overall assessment calculation
- Error handling
- Output validation

Author: ASP Test Team
Date: November 19, 2025
"""

import json
from datetime import datetime
from unittest.mock import Mock, patch

import pytest

from asp.agents.base_agent import AgentExecutionError
from asp.agents.code_review_orchestrator import CodeReviewOrchestrator
from asp.models.code import GeneratedCode, GeneratedFile
from asp.models.code_review import CodeReviewReport

# =============================================================================
# Test Fixtures
# =============================================================================


def create_test_generated_code(task_id="CODE-TEST-001"):
    """Create a test GeneratedCode for review."""
    return GeneratedCode(
        task_id=task_id,
        files=[
            GeneratedFile(
                file_path="src/api/auth.py",
                content="""
from fastapi import APIRouter, HTTPException
from typing import Dict

router = APIRouter()

@router.post("/login")
async def login(username: str, password: str) -> Dict:
    # SQL injection vulnerability
    query = f"SELECT * FROM users WHERE username = '{username}'"
    # Missing password hashing
    if password == "admin":
        return {"token": "abc123"}
    raise HTTPException(status_code=401)
""",
                file_type="source",
                semantic_unit_id="SU-001",
                component_id="COMP-001",
                description="JWT authentication API endpoint with login functionality",
            ),
            GeneratedFile(
                file_path="tests/test_auth.py",
                content="""
def test_login_success():
    # Test with valid credentials
    result = login("admin", "admin")
    assert result["token"] is not None

# Missing edge case tests
# Missing error case tests
""",
                file_type="test",
                semantic_unit_id="SU-001",
                component_id="COMP-001",
                description="Basic unit tests for authentication - incomplete coverage",
            ),
        ],
        file_structure={
            "src/api": ["auth.py"],
            "tests": ["test_auth.py"],
        },
        dependencies=["fastapi", "pydantic"],
        total_files=2,
        total_lines_of_code=25,
        implementation_notes="Basic JWT authentication implementation using FastAPI router with POST endpoint for user login. Includes simple username/password validation and token generation. Tests provide minimal coverage of successful login scenario.",
    )


def create_mock_specialist_results():
    """Create mock results from specialist agents."""
    return {
        "code_quality": {
            "issues_found": [
                {
                    "issue_id": "QUAL-001",
                    "category": "Code Quality",
                    "severity": "Medium",
                    "description": "Missing type hints for function parameters",
                    "evidence": "src/api/auth.py:8",
                    "impact": "Reduces code clarity and IDE support",
                    "file_path": "src/api/auth.py",
                    "line_number": 8,
                    "affected_phase": "Code",
                }
            ],
            "improvement_suggestions": [
                {
                    "suggestion_id": "QUAL-IMP-001",
                    "related_issue_id": "QUAL-001",
                    "category": "Code Quality",
                    "priority": "Medium",
                    "description": "Add type hints to all function parameters and return types",
                    "implementation_notes": "Use Python type hints for username, password parameters",
                }
            ],
        },
        "code_security": {
            "issues_found": [
                {
                    "issue_id": "SEC-001",
                    "category": "Security",
                    "severity": "Critical",
                    "description": "SQL injection vulnerability via string formatting",
                    "evidence": "src/api/auth.py:10",
                    "impact": "Attacker can execute arbitrary SQL queries",
                    "file_path": "src/api/auth.py",
                    "line_number": 10,
                    "affected_phase": "Code",
                }
            ],
            "improvement_suggestions": [
                {
                    "suggestion_id": "SEC-IMP-001",
                    "related_issue_id": "SEC-001",
                    "category": "Security",
                    "priority": "High",
                    "description": "Use parameterized queries or ORM to prevent SQL injection",
                    "implementation_notes": "Replace f-string with SQLAlchemy query or parameterized statement",
                }
            ],
        },
        "code_performance": {
            "issues_found": [],
            "improvement_suggestions": [],
        },
        "test_coverage": {
            "issues_found": [
                {
                    "issue_id": "TEST-001",
                    "category": "Testing",
                    "severity": "High",
                    "description": "Missing edge case tests for authentication",
                    "evidence": "tests/test_auth.py (missing invalid credentials test)",
                    "impact": "Authentication bugs may go undetected",
                    "file_path": "tests/test_auth.py",
                    "affected_phase": "Code",
                }
            ],
            "improvement_suggestions": [],
        },
        "documentation": {
            "issues_found": [],
            "improvement_suggestions": [],
        },
        "best_practices": {
            "issues_found": [],
            "improvement_suggestions": [],
        },
    }


# =============================================================================
# Orchestrator Initialization Tests
# =============================================================================


def test_orchestrator_initialization():
    """Test that orchestrator initializes with all 6 specialists."""
    orchestrator = CodeReviewOrchestrator()

    assert orchestrator is not None
    assert orchestrator.agent_version == "1.0.0"
    assert len(orchestrator.specialists) == 6

    # Verify all expected specialists are present
    expected_specialists = [
        "code_quality",
        "code_security",
        "code_performance",
        "test_coverage",
        "documentation",
        "best_practices",
    ]
    for specialist_name in expected_specialists:
        assert specialist_name in orchestrator.specialists
        assert orchestrator.specialists[specialist_name] is not None


def test_orchestrator_initialization_with_custom_llm():
    """Test orchestrator initialization with custom LLM client."""
    mock_llm = Mock()
    orchestrator = CodeReviewOrchestrator(llm_client=mock_llm)

    assert orchestrator is not None
    # Verify specialists inherit the mock LLM client
    for specialist in orchestrator.specialists.values():
        assert specialist._llm_client == mock_llm


# =============================================================================
# Orchestrator Execute Tests
# =============================================================================


@patch.object(CodeReviewOrchestrator, "_dispatch_specialists")
def test_orchestrator_execute_success(mock_dispatch):
    """Test successful orchestrated code review."""
    # Setup
    orchestrator = CodeReviewOrchestrator()
    generated_code = create_test_generated_code()
    mock_dispatch.return_value = create_mock_specialist_results()

    # Execute
    report = orchestrator.execute(generated_code)

    # Verify
    assert isinstance(report, CodeReviewReport)
    assert report.task_id == "CODE-TEST-001"
    assert report.review_id.startswith("CODE-REVIEW-")
    assert report.agent_version == "1.0.0"

    # Verify issue aggregation
    assert len(report.issues_found) == 3  # QUAL-001, SEC-001, TEST-001
    assert report.critical_issues == 1  # SEC-001
    assert report.high_issues == 1  # TEST-001
    assert report.medium_issues == 1  # QUAL-001
    assert report.low_issues == 0

    # Verify overall assessment (Critical issues → FAIL)
    assert report.review_status == "FAIL"

    # Verify checklist review
    assert len(report.checklist_review) == 5  # Standard checklist
    security_items = [
        item for item in report.checklist_review if "Category: Security" in item.notes
    ]
    assert len(security_items) == 1
    assert security_items[0].status == "Fail"  # Due to critical security issue


@patch.object(CodeReviewOrchestrator, "_dispatch_specialists")
def test_orchestrator_execute_with_only_medium_issues(mock_dispatch):
    """Test overall assessment with only medium issues → NEEDS_IMPROVEMENT."""
    orchestrator = CodeReviewOrchestrator()
    generated_code = create_test_generated_code()

    # Mock results with only medium issues
    mock_dispatch.return_value = {
        "code_quality": {
            "issues_found": [
                {
                    "issue_id": "QUAL-001",
                    "category": "Code Quality",
                    "severity": "Medium",
                    "description": "Minor code smell detected in function naming",
                    "evidence": "src/api/auth.py:10",
                    "impact": "Reduces code readability and maintainability",
                    "file_path": "src/api/auth.py",
                    "affected_phase": "Code",
                }
            ],
            "improvement_suggestions": [],
        },
        "code_security": {"issues_found": [], "improvement_suggestions": []},
        "code_performance": {"issues_found": [], "improvement_suggestions": []},
        "test_coverage": {"issues_found": [], "improvement_suggestions": []},
        "documentation": {"issues_found": [], "improvement_suggestions": []},
        "best_practices": {"issues_found": [], "improvement_suggestions": []},
    }

    report = orchestrator.execute(generated_code)

    assert report.review_status == "PASS"  # Medium issues only → PASS
    assert report.critical_issues == 0
    assert report.high_issues == 0
    assert report.medium_issues == 1


@patch.object(CodeReviewOrchestrator, "_dispatch_specialists")
def test_orchestrator_execute_with_high_issues(mock_dispatch):
    """Test overall assessment with high issues → NEEDS_REVISION."""
    orchestrator = CodeReviewOrchestrator()
    generated_code = create_test_generated_code()

    # Mock results with high issues
    mock_dispatch.return_value = {
        "code_quality": {"issues_found": [], "improvement_suggestions": []},
        "code_security": {
            "issues_found": [
                {
                    "issue_id": "SEC-001",
                    "category": "Security",
                    "severity": "High",
                    "description": "Missing input validation on user credentials",
                    "evidence": "src/api/auth.py:10",
                    "impact": "Security risk - potential injection attack vector",
                    "file_path": "src/api/auth.py",
                    "affected_phase": "Code",
                }
            ],
            "improvement_suggestions": [],
        },
        "code_performance": {"issues_found": [], "improvement_suggestions": []},
        "test_coverage": {"issues_found": [], "improvement_suggestions": []},
        "documentation": {"issues_found": [], "improvement_suggestions": []},
        "best_practices": {"issues_found": [], "improvement_suggestions": []},
    }

    report = orchestrator.execute(generated_code)

    assert (
        report.review_status == "CONDITIONAL_PASS"
    )  # High issues but < 5 → CONDITIONAL_PASS
    assert report.high_issues == 1


@patch.object(CodeReviewOrchestrator, "_dispatch_specialists")
def test_orchestrator_execute_no_issues(mock_dispatch):
    """Test overall assessment with no issues → PASS."""
    orchestrator = CodeReviewOrchestrator()
    generated_code = create_test_generated_code()

    # Mock results with no issues
    empty_results = {
        specialist: {"issues_found": [], "improvement_suggestions": []}
        for specialist in [
            "code_quality",
            "code_security",
            "code_performance",
            "test_coverage",
            "documentation",
            "best_practices",
        ]
    }
    mock_dispatch.return_value = empty_results

    report = orchestrator.execute(generated_code)

    assert report.review_status == "PASS"
    assert report.critical_issues == 0
    assert report.high_issues == 0
    assert report.medium_issues == 0
    assert report.low_issues == 0


# =============================================================================
# Result Aggregation Tests
# =============================================================================


def test_aggregate_results_deduplication():
    """Test that duplicate issues are deduplicated by file + line number."""
    orchestrator = CodeReviewOrchestrator()

    specialist_results = {
        "code_quality": {
            "issues_found": [
                {
                    "issue_id": "QUAL-001",
                    "category": "Code Quality",
                    "severity": "Medium",
                    "description": "Missing type hints",
                    "evidence": "src/api/auth.py:10",
                    "impact": "Reduces clarity",
                    "file_path": "src/api/auth.py",
                    "line_number": 10,
                    "affected_phase": "Code",
                }
            ],
            "improvement_suggestions": [],
        },
        "documentation": {
            "issues_found": [
                {
                    "issue_id": "DOC-001",
                    "category": "Documentation",
                    "severity": "Low",  # Lower severity
                    "description": "Missing docstring",  # Different description
                    "evidence": "src/api/auth.py:10",  # Same location
                    "impact": "Reduces documentation",
                    "file_path": "src/api/auth.py",
                    "line_number": 10,  # Same line number
                    "affected_phase": "Code",
                }
            ],
            "improvement_suggestions": [],
        },
    }

    aggregated_issues, aggregated_suggestions = orchestrator._aggregate_results(
        specialist_results
    )

    # Should deduplicate and keep higher severity (Medium > Low)
    assert len(aggregated_issues) == 1
    assert aggregated_issues[0]["severity"] == "Medium"


def test_aggregate_results_id_normalization():
    """Test that issue IDs are normalized to CODE-ISSUE-### format."""
    orchestrator = CodeReviewOrchestrator()

    specialist_results = {
        "code_quality": {
            "issues_found": [
                {
                    "issue_id": "QUAL-001",
                    "category": "Code Quality",
                    "severity": "Medium",
                    "description": "Issue 1",
                    "evidence": "file1.py:10",
                    "impact": "Impact",
                    "file_path": "file1.py",
                    "line_number": 10,
                    "affected_phase": "Code",
                }
            ],
            "improvement_suggestions": [
                {
                    "suggestion_id": "QUAL-IMP-001",
                    "related_issue_id": "QUAL-001",
                    "category": "Code Quality",
                    "priority": "Medium",
                    "description": "Fix the issue with proper implementation",
                    "implementation_notes": "Follow these steps to resolve",
                }
            ],
        },
        "code_security": {
            "issues_found": [
                {
                    "issue_id": "SEC-001",
                    "category": "Security",
                    "severity": "Critical",
                    "description": "Issue 2",
                    "evidence": "file2.py:20",
                    "impact": "Impact",
                    "file_path": "file2.py",
                    "line_number": 20,
                    "affected_phase": "Code",
                }
            ],
            "improvement_suggestions": [],
        },
    }

    aggregated_issues, aggregated_suggestions = orchestrator._aggregate_results(
        specialist_results
    )

    # Verify issue IDs are normalized
    assert all(
        issue["issue_id"].startswith("CODE-ISSUE-") for issue in aggregated_issues
    )
    assert aggregated_issues[0]["issue_id"] == "CODE-ISSUE-001"
    assert aggregated_issues[1]["issue_id"] == "CODE-ISSUE-002"

    # Verify suggestion IDs are normalized
    assert all(
        sug["suggestion_id"].startswith("CODE-IMPROVE-")
        for sug in aggregated_suggestions
    )
    assert aggregated_suggestions[0]["suggestion_id"] == "CODE-IMPROVE-001"

    # Verify related_issue_id is updated
    assert aggregated_suggestions[0]["related_issue_id"] == "CODE-ISSUE-001"


# =============================================================================
# Automated Checks Tests
# =============================================================================


def test_automated_checks_all_pass():
    """Test automated checks with well-structured code."""
    orchestrator = CodeReviewOrchestrator()

    generated_code = GeneratedCode(
        task_id="TEST-001",
        files=[
            GeneratedFile(
                file_path="src/module.py",
                content="# Source code\n" * 50,
                file_type="source",
                description="A well-documented source module",
            ),
            GeneratedFile(
                file_path="tests/test_module.py",
                content="# Test code\n" * 30,
                file_type="test",
                description="Comprehensive test suite for the module",
            ),
        ],
        file_structure={"src": ["module.py"], "tests": ["test_module.py"]},
        dependencies=["fastapi", "pydantic"],
        total_files=2,
        total_lines_of_code=80,
        implementation_notes="Well-structured module with comprehensive test coverage and proper documentation following best practices",
    )

    checks = orchestrator._run_automated_checks(generated_code)

    assert checks["has_source_files"] is True
    assert checks["has_test_files"] is True
    assert checks["adequate_test_coverage"] is True  # 1 test / 1 source = 1.0 ≥ 0.5
    assert checks["dependencies_specified"] is True
    assert checks["all_files_documented"] is True
    assert checks["no_oversized_files"] is True


def test_automated_checks_missing_tests():
    """Test automated checks with missing test files."""
    orchestrator = CodeReviewOrchestrator()

    generated_code = GeneratedCode(
        task_id="TEST-001",
        files=[
            GeneratedFile(
                file_path="src/module.py",
                content="# Source code\n" * 50,
                file_type="source",
                description="Source module without tests",
            ),
        ],
        file_structure={"src": ["module.py"]},
        dependencies=["fastapi"],
        total_files=1,
        total_lines_of_code=50,
        implementation_notes="Simple module implementation without accompanying test suite for validation and quality assurance",
    )

    checks = orchestrator._run_automated_checks(generated_code)

    assert checks["has_source_files"] is True
    assert checks["has_test_files"] is False
    assert checks["adequate_test_coverage"] is False


def test_automated_checks_oversized_file():
    """Test automated checks with oversized file (>1000 lines)."""
    orchestrator = CodeReviewOrchestrator()

    generated_code = GeneratedCode(
        task_id="TEST-001",
        files=[
            GeneratedFile(
                file_path="src/huge_module.py",
                content="\n".join([f"# Line {i}" for i in range(1500)]),
                file_type="source",
                description="A very large source file that should be split",
            ),
        ],
        file_structure={"src": ["huge_module.py"]},
        dependencies=[],
        total_files=1,
        total_lines_of_code=1500,
        implementation_notes="Very large monolithic module implementation exceeding recommended file size limits and requiring refactoring into smaller focused modules",
    )

    checks = orchestrator._run_automated_checks(generated_code)

    assert checks["no_oversized_files"] is False


# =============================================================================
# Category Normalization Tests
# =============================================================================


def test_normalize_category():
    """Test category normalization to valid Literal types."""
    orchestrator = CodeReviewOrchestrator()

    # Test various input formats
    assert orchestrator._normalize_category("security") == "Security"
    assert orchestrator._normalize_category("code quality") == "Code Quality"
    assert orchestrator._normalize_category("performance") == "Performance"
    assert orchestrator._normalize_category("testing") == "Testing"
    assert orchestrator._normalize_category("maintainability") == "Maintainability"

    # Test unknown category defaults to "Code Quality"
    assert orchestrator._normalize_category("unknown") == "Code Quality"


# =============================================================================
# Error Handling Tests
# =============================================================================


@patch.object(CodeReviewOrchestrator, "_dispatch_specialists")
def test_orchestrator_execute_handles_specialist_failure(mock_dispatch):
    """Test that orchestrator handles specialist failures gracefully."""
    orchestrator = CodeReviewOrchestrator()
    generated_code = create_test_generated_code()

    # Mock dispatch to raise exception
    mock_dispatch.side_effect = Exception("Specialist failed")

    with pytest.raises(AgentExecutionError, match="Code review orchestration failed"):
        orchestrator.execute(generated_code)


# =============================================================================
# Review ID Generation Tests
# =============================================================================


def test_generate_review_id():
    """Test review ID generation follows correct pattern."""
    orchestrator = CodeReviewOrchestrator()

    task_id = "TEST-REVIEW-123"
    timestamp = datetime(2025, 11, 19, 14, 30, 45)

    review_id = orchestrator._generate_review_id(task_id, timestamp)

    # Verify format: CODE-REVIEW-{ALPHANUMERIC}-{YYYYMMDD}-{HHMMSS}
    assert review_id.startswith("CODE-REVIEW-")
    assert "-20251119-143045" in review_id
    # Task ID should be cleaned (alphanumeric only, uppercase)
    assert "TESTREVIEW123" in review_id


# =============================================================================
# Integration Tests (Minimal E2E within Unit Test)
# =============================================================================


def test_orchestrator_end_to_end_with_mocked_specialists():
    """Test full orchestration flow with all specialists mocked."""
    # Create mock LLM that returns valid specialist responses
    mock_llm = Mock()

    def mock_llm_call(prompt):
        # Return valid specialist response based on prompt content
        return {
            "content": json.dumps(
                {
                    "issues_found": [
                        {
                            "issue_id": "MOCK-001",
                            "category": "Code Quality",
                            "severity": "Low",
                            "description": "Minor style issue",
                            "evidence": "src/api/auth.py:1",
                            "impact": "Minor impact on readability",
                            "file_path": "src/api/auth.py",
                            "line_number": 1,
                            "affected_phase": "Code",
                        }
                    ],
                    "improvement_suggestions": [],
                }
            )
        }

    mock_llm.side_effect = mock_llm_call

    # Create orchestrator with mocked specialists
    orchestrator = CodeReviewOrchestrator(llm_client=mock_llm)

    # Replace all specialist execute methods with mocks
    for specialist_name, specialist in orchestrator.specialists.items():
        specialist.execute = Mock(
            return_value={
                "issues_found": [],
                "improvement_suggestions": [],
            }
        )

    generated_code = create_test_generated_code()

    report = orchestrator.execute(generated_code)

    # Verify report was generated
    assert isinstance(report, CodeReviewReport)
    assert report.task_id == "CODE-TEST-001"
    assert report.review_status in ["PASS", "CONDITIONAL_PASS", "FAIL"]

    # Verify all specialists were called
    for specialist in orchestrator.specialists.values():
        specialist.execute.assert_called_once()
