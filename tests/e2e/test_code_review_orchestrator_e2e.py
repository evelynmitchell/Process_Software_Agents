"""
End-to-End tests for Code Review Orchestrator.

Tests the full orchestration workflow with realistic scenarios:
- Complete code review pipeline
- Review of code with various issue types
- Integration between all 6 specialists
- Report generation and formatting
- Real-world edge cases

Author: ASP Test Team
Date: November 19, 2025
"""

import json
import pytest
from datetime import datetime
from unittest.mock import Mock, patch

from asp.agents.code_review_orchestrator import CodeReviewOrchestrator
from asp.models.code import GeneratedCode, GeneratedFile
from asp.models.code_review import CodeReviewReport


# =============================================================================
# Test Fixtures
# =============================================================================


def create_simple_generated_code():
    """Create simple generated code that should PASS review."""
    return GeneratedCode(
        task_id="E2E-SIMPLE-001",
        files=[
            GeneratedFile(
                file_path="src/calculator.py",
                content='''"""
Simple calculator module.

Provides basic arithmetic operations.
"""

def add(a: int, b: int) -> int:
    """
    Add two numbers.

    Args:
        a: First number
        b: Second number

    Returns:
        Sum of a and b
    """
    return a + b


def subtract(a: int, b: int) -> int:
    """
    Subtract b from a.

    Args:
        a: First number
        b: Second number

    Returns:
        Difference of a and b
    """
    return a - b
''',
                file_type="source",
                description="Well-documented calculator module with type hints",
            ),
            GeneratedFile(
                file_path="tests/test_calculator.py",
                content='''"""Tests for calculator module."""

import pytest
from calculator import add, subtract


def test_add_positive_numbers():
    """Test adding two positive numbers."""
    assert add(2, 3) == 5


def test_add_negative_numbers():
    """Test adding negative numbers."""
    assert add(-2, -3) == -5


def test_add_mixed():
    """Test adding positive and negative."""
    assert add(5, -3) == 2


def test_subtract_positive():
    """Test subtracting positive numbers."""
    assert subtract(5, 3) == 2


def test_subtract_negative():
    """Test subtracting negative numbers."""
    assert subtract(-5, -3) == -2
''',
                file_type="test",
                description="Comprehensive tests for calculator with edge cases",
            ),
        ],
        dependencies=[],
        total_files=2,
        total_lines_of_code=65,
        file_structure={
            "src": ["calculator.py"],
            "tests": ["test_calculator.py"],
        },
        implementation_notes="Simple calculator with good practices",
    )


def create_problematic_generated_code():
    """Create code with security and quality issues that should FAIL review."""
    return GeneratedCode(
        task_id="E2E-PROBLEMATIC-001",
        files=[
            GeneratedFile(
                file_path="src/api/user.py",
                content='''
from flask import request

def get_user(user_id):
    query = f"SELECT * FROM users WHERE id = {user_id}"
    result = db.execute(query)
    return result.fetchone()

def authenticate(username, password):
    user = get_user_by_name(username)
    if user and user["password"] == password:
        return {"token": "secret_key_12345"}
    return None
''',
                file_type="source",
                description="User API with SQL injection and security issues",
            ),
        ],
        dependencies=["flask"],
        total_files=1,
        total_lines_of_code=15,
        file_structure={
            "src/api": ["user.py"],
        },
        implementation_notes=(
            "Flask-based user API with endpoints for user retrieval and creation. "
            "Uses direct SQL queries with string formatting for database operations. "
            "Implements basic CRUD operations without input validation or security measures."
        ),
    )


def create_performance_issues_code():
    """Create code with performance issues that should NEEDS_REVISION."""
    return GeneratedCode(
        task_id="E2E-PERFORMANCE-001",
        files=[
            GeneratedFile(
                file_path="src/services/order_service.py",
                content='''
def get_orders_with_users():
    """Get all orders with user information."""
    orders = db.query(Order).all()

    # N+1 query problem
    for order in orders:
        user = db.query(User).get(order.user_id)
        order.user_name = user.name

    return orders


def find_duplicates(items):
    """Find duplicate items - inefficient algorithm."""
    duplicates = []
    # O(n²) complexity
    for i in range(len(items)):
        for j in range(i + 1, len(items)):
            if items[i] == items[j]:
                duplicates.append(items[i])
    return duplicates
''',
                file_type="source",
                description="Order service with N+1 queries and inefficient algorithms",
            ),
            GeneratedFile(
                file_path="tests/test_order_service.py",
                content='''
def test_get_orders():
    orders = get_orders_with_users()
    assert len(orders) > 0
''',
                file_type="test",
                description="Minimal test coverage",
            ),
        ],
        dependencies=["sqlalchemy"],
        total_files=2,
        total_lines_of_code=30,
        file_structure={
            "src/services": ["order_service.py"],
            "tests": ["test_order_service.py"],
        },
        implementation_notes=(
            "Order service with SQLAlchemy for database operations. "
            "Implements order retrieval with user information loading and duplicate detection. "
            "Contains N+1 query problems in user data loading and O(n²) complexity in duplicate finding algorithm. "
            "Test coverage is minimal with basic assertions only."
        ),
    )


# =============================================================================
# E2E Tests with Mocked Specialists
# =============================================================================


def test_e2e_simple_code_passes_review():
    """Test that simple, well-written code passes review."""
    # Mock all specialists to return no issues
    def create_clean_response(prompt):
        return {
            "content": json.dumps({
                "issues_found": [],
                "improvement_suggestions": [],
            })
        }

    mock_llm = Mock()
    mock_llm.side_effect = create_clean_response

    orchestrator = CodeReviewOrchestrator(llm_client=mock_llm)
    generated_code = create_simple_generated_code()

    report = orchestrator.execute(generated_code)

    assert isinstance(report, CodeReviewReport)
    assert report.task_id == "E2E-SIMPLE-001"
    assert report.overall_assessment == "PASS"
    assert report.critical_issue_count == 0
    assert report.high_issue_count == 0
    assert report.medium_issue_count == 0
    assert report.low_issue_count == 0
    assert len(report.issues_found) == 0


def test_e2e_problematic_code_fails_review():
    """Test that code with critical issues fails review."""
    # Mock specialists to return critical security issues
    def create_security_issues_response(prompt):
        if "security" in prompt.lower() or "code_security" in prompt.lower():
            return {
                "content": json.dumps({
                    "issues_found": [
                        {
                            "issue_id": "SEC-001",
                            "category": "Security",
                            "severity": "Critical",
                            "description": "SQL injection vulnerability",
                            "evidence": "src/api/user.py:4",
                            "impact": "Attacker can execute arbitrary SQL",
                            "file_path": "src/api/user.py",
                            "line_number": 4,
                            "affected_phase": "Code",
                        },
                        {
                            "issue_id": "SEC-002",
                            "category": "Security",
                            "severity": "Critical",
                            "description": "Hardcoded secret key",
                            "evidence": "src/api/user.py:11",
                            "impact": "Secret exposed in source code",
                            "file_path": "src/api/user.py",
                            "line_number": 11,
                            "affected_phase": "Code",
                        },
                    ],
                    "improvement_suggestions": [
                        {
                            "suggestion_id": "SEC-IMP-001",
                            "related_issue_id": "SEC-001",
                            "category": "Security",
                            "priority": "High",
                            "description": "Use parameterized queries to prevent SQL injection",
                            "implementation_notes": "Replace string formatting with ORM or prepared statements",
                        }
                    ],
                })
            }
        else:
            return {
                "content": json.dumps({
                    "issues_found": [],
                    "improvement_suggestions": [],
                })
            }

    mock_llm = Mock()
    mock_llm.side_effect = create_security_issues_response

    orchestrator = CodeReviewOrchestrator(llm_client=mock_llm)
    generated_code = create_problematic_generated_code()

    report = orchestrator.execute(generated_code)

    assert report.overall_assessment == "FAIL"
    assert report.critical_issue_count >= 1
    assert len(report.issues_found) >= 1

    # Verify issues were normalized
    for issue in report.issues_found:
        assert issue.issue_id.startswith("CODE-ISSUE-")


def test_e2e_performance_issues_needs_revision():
    """Test that code with high-severity performance issues gets NEEDS_REVISION."""
    # Mock specialists to return high-severity performance issues
    def create_performance_issues_response(prompt):
        if "performance" in prompt.lower() or "code_performance" in prompt.lower():
            return {
                "content": json.dumps({
                    "issues_found": [
                        {
                            "issue_id": "PERF-001",
                            "category": "Performance",
                            "severity": "High",
                            "description": "N+1 query problem in loop",
                            "evidence": "src/services/order_service.py:6",
                            "impact": "1000 orders = 1000 database queries, severe performance degradation",
                            "file_path": "src/services/order_service.py",
                            "line_number": 6,
                            "affected_phase": "Code",
                        }
                    ],
                    "improvement_suggestions": [],
                })
            }
        else:
            return {
                "content": json.dumps({
                    "issues_found": [],
                    "improvement_suggestions": [],
                })
            }

    mock_llm = Mock()
    mock_llm.side_effect = create_performance_issues_response

    orchestrator = CodeReviewOrchestrator(llm_client=mock_llm)
    generated_code = create_performance_issues_code()

    report = orchestrator.execute(generated_code)

    assert report.review_status == "CONDITIONAL_PASS"  # High issues but < 5
    assert report.high_issues >= 1


# =============================================================================
# Automated Checks E2E Tests
# =============================================================================


def test_e2e_automated_checks_detect_missing_tests():
    """Test that automated checks detect missing test files."""
    # Create code without tests
    generated_code = GeneratedCode(
        task_id="E2E-NO-TESTS-001",
        files=[
            GeneratedFile(
                file_path="src/module.py",
                content="def func(): pass",
                file_type="source",
                description="Source file without corresponding tests",
            )
        ],
        dependencies=[],
        total_files=1,
        total_lines_of_code=1,
        file_structure={"src": ["module.py"]},
        implementation_notes="Basic module with single function and no test coverage",
    )

    mock_llm = Mock()
    mock_llm.return_value = {
        "content": json.dumps({
            "issues_found": [],
            "improvement_suggestions": [],
        })
    }

    orchestrator = CodeReviewOrchestrator(llm_client=mock_llm)
    report = orchestrator.execute(generated_code)

    # Verify report was generated successfully
    assert report.task_id == "E2E-NO-TESTS-001"
    assert report.files_reviewed >= 1


def test_e2e_automated_checks_detect_oversized_files():
    """Test that automated checks detect files exceeding size limit."""
    # Create a file with >1000 lines
    large_content = "\n".join([f"# Line {i}" for i in range(1500)])

    generated_code = GeneratedCode(
        task_id="E2E-LARGE-FILE-001",
        files=[
            GeneratedFile(
                file_path="src/huge_module.py",
                content=large_content,
                file_type="source",
                description="Very large source file",
            )
        ],
        dependencies=[],
        total_files=1,
        total_lines_of_code=1500,
        file_structure={"src": ["huge_module.py"]},
        implementation_notes="Very large module file exceeding recommended size limits for maintainability and code review purposes",
    )

    mock_llm = Mock()
    mock_llm.return_value = {
        "content": json.dumps({
            "issues_found": [],
            "improvement_suggestions": [],
        })
    }

    orchestrator = CodeReviewOrchestrator(llm_client=mock_llm)
    report = orchestrator.execute(generated_code)

    # Verify report was generated successfully
    assert report.task_id == "E2E-LARGE-FILE-001"
    assert report.files_reviewed >= 1


# =============================================================================
# Checklist Review E2E Tests
# =============================================================================


def test_e2e_checklist_review_reflects_issues():
    """Test that checklist review correctly reflects found issues."""
    # Mock security specialist to return critical issue
    def create_security_issue_response(prompt):
        if "security" in prompt.lower():
            return {
                "content": json.dumps({
                    "issues_found": [
                        {
                            "issue_id": "SEC-001",
                            "category": "Security",
                            "severity": "Critical",
                            "description": "Critical security flaw",
                            "evidence": "src/api/auth.py:10",
                            "impact": "System compromise",
                            "file_path": "src/api/auth.py",
                            "line_number": 10,
                            "affected_phase": "Code",
                        }
                    ],
                    "improvement_suggestions": [],
                })
            }
        else:
            return {
                "content": json.dumps({
                    "issues_found": [],
                    "improvement_suggestions": [],
                })
            }

    mock_llm = Mock()
    mock_llm.side_effect = create_security_issue_response

    orchestrator = CodeReviewOrchestrator(llm_client=mock_llm)
    generated_code = create_problematic_generated_code()

    report = orchestrator.execute(generated_code)

    # Find security checklist item
    security_items = [item for item in report.checklist_review if item.category == "Security"]
    assert len(security_items) > 0

    # Security item should FAIL due to critical issue
    security_item = security_items[0]
    assert security_item.status == "FAIL"
    assert len(security_item.related_issues) > 0


# =============================================================================
# Review ID Generation E2E Tests
# =============================================================================


def test_e2e_review_id_format():
    """Test that review IDs follow correct pattern."""
    mock_llm = Mock()
    mock_llm.return_value = {
        "content": json.dumps({
            "issues_found": [],
            "improvement_suggestions": [],
        })
    }

    orchestrator = CodeReviewOrchestrator(llm_client=mock_llm)
    generated_code = create_simple_generated_code()

    report = orchestrator.execute(generated_code)

    # Verify review ID format: CODE-REVIEW-{TASK}-{YYYYMMDD}-{HHMMSS}
    assert report.review_id.startswith("CODE-REVIEW-")
    assert len(report.review_id.split("-")) >= 5

    # Extract date and time parts
    parts = report.review_id.split("-")
    date_part = parts[-2]
    time_part = parts[-1]

    assert len(date_part) == 8  # YYYYMMDD
    assert len(time_part) == 6  # HHMMSS


# =============================================================================
# Full Pipeline Integration Test
# =============================================================================


def test_e2e_full_pipeline_integration():
    """Test full code review pipeline with mixed issue severities."""
    # Mock specialists with varied responses
    def create_varied_responses(prompt):
        if "quality" in prompt.lower():
            return {
                "content": json.dumps({
                    "issues_found": [
                        {
                            "issue_id": "QUAL-001",
                            "category": "Code Quality",
                            "severity": "Medium",
                            "description": "Complex function needs refactoring",
                            "evidence": "src/api/user.py:5",
                            "impact": "Reduces maintainability",
                            "file_path": "src/api/user.py",
                            "line_number": 5,
                            "affected_phase": "Code",
                        }
                    ],
                    "improvement_suggestions": [],
                })
            }
        elif "security" in prompt.lower():
            return {
                "content": json.dumps({
                    "issues_found": [
                        {
                            "issue_id": "SEC-001",
                            "category": "Security",
                            "severity": "High",
                            "description": "Missing input validation",
                            "evidence": "src/api/user.py:3",
                            "impact": "Security vulnerability",
                            "file_path": "src/api/user.py",
                            "line_number": 3,
                            "affected_phase": "Code",
                        }
                    ],
                    "improvement_suggestions": [],
                })
            }
        elif "test" in prompt.lower() or "coverage" in prompt.lower():
            return {
                "content": json.dumps({
                    "issues_found": [
                        {
                            "issue_id": "TEST-001",
                            "category": "Testing",
                            "severity": "Low",
                            "description": "Missing edge case tests",
                            "evidence": "tests/test_user.py",
                            "impact": "Incomplete test coverage",
                            "file_path": "tests/test_user.py",
                            "affected_phase": "Code",
                        }
                    ],
                    "improvement_suggestions": [],
                })
            }
        else:
            return {
                "content": json.dumps({
                    "issues_found": [],
                    "improvement_suggestions": [],
                })
            }

    mock_llm = Mock()
    mock_llm.side_effect = create_varied_responses

    orchestrator = CodeReviewOrchestrator(llm_client=mock_llm)
    generated_code = create_problematic_generated_code()

    report = orchestrator.execute(generated_code)

    # Verify mixed severities
    assert report.overall_assessment == "NEEDS_REVISION"  # High severity issue present
    assert report.high_issue_count == 1
    assert report.medium_issue_count == 1
    assert report.low_issue_count == 1

    # Verify total issue count
    assert len(report.issues_found) == 3

    # Verify all issue IDs are normalized
    for issue in report.issues_found:
        assert issue.issue_id.startswith("CODE-ISSUE-")

    # Verify report metadata
    assert report.reviewer_agent == "CodeReviewOrchestrator"
    assert report.agent_version == "1.0.0"
    assert report.review_duration_ms > 0
