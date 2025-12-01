#!/usr/bin/env python3
"""
Code Review Orchestrator Example Script

This script demonstrates how to use the Code Review Orchestrator to validate
generated code against quality, security, performance, and best practice criteria
using 6 specialist code review agents.

Usage:
    # With environment variables set (ANTHROPIC_API_KEY):
    uv run python examples/code_review_orchestrator_example.py

    # Run specific example:
    uv run python examples/code_review_orchestrator_example.py --example simple
    uv run python examples/code_review_orchestrator_example.py --example security-issues
    uv run python examples/code_review_orchestrator_example.py --example full-workflow

    # Save review report to file:
    uv run python examples/code_review_orchestrator_example.py --output code_review_report.json

Requirements:
    - ANTHROPIC_API_KEY environment variable set
    - Langfuse secrets configured (optional, for telemetry)

Author: ASP Development Team
Date: November 19, 2025
"""

import argparse
import json
import sys
from pathlib import Path

from asp.agents.code_review_orchestrator import CodeReviewOrchestrator
from asp.models.code import GeneratedCode, GeneratedFile
from asp.models.design import (
    APIContract,
    ComponentLogic,
    DataSchema,
    DesignReviewChecklistItem,
    DesignSpecification,
)


def print_header(title: str):
    """Print a formatted section header."""
    print()
    print("=" * 80)
    print(f"  {title}")
    print("=" * 80)
    print()


def print_code_review_report(report):
    """Print code review report in a readable format."""
    print_header(f"Code Review Report for {report.task_id}")

    print(f"Review ID: {report.review_id}")
    print(f"Overall Assessment: {report.overall_assessment}")
    print(f"Reviewer: {report.reviewer_agent} v{report.agent_version}")
    print(f"Review Duration: {report.review_duration_ms:.2f}ms")
    print()

    # Issue counts
    print("Issue Summary:")
    print(f"  Critical: {report.critical_issue_count}")
    print(f"  High:     {report.high_issue_count}")
    print(f"  Medium:   {report.medium_issue_count}")
    print(f"  Low:      {report.low_issue_count}")
    print(f"  Total:    {len(report.issues_found)}")
    print()

    # Automated checks
    print("Automated Checks:")
    for check_name, passed in report.automated_checks.items():
        status = "[PASS]" if passed else "[FAIL]"
        print(f"  {status} {check_name.replace('_', ' ').title()}")
    print()

    # Issues found
    if report.issues_found:
        print(f"Issues Found ({len(report.issues_found)}):")
        for i, issue in enumerate(report.issues_found, 1):
            print(f"\n  {i}. [{issue.severity}] {issue.category} - {issue.issue_id}")
            print(f"     {issue.description}")
            print(f"     Location: {issue.file_path}")
            if issue.line_number:
                print(f"     Line: {issue.line_number}")
            print(f"     Impact: {issue.impact}")
            print(f"     Phase: {issue.affected_phase}")
    else:
        print("No issues found - Code passed all checks!")
    print()

    # Improvement suggestions
    if report.improvement_suggestions:
        print(f"Improvement Suggestions ({len(report.improvement_suggestions)}):")
        for i, suggestion in enumerate(report.improvement_suggestions, 1):
            print(
                f"\n  {i}. [{suggestion.priority}] {suggestion.category} - {suggestion.suggestion_id}"
            )
            print(f"     {suggestion.description}")
            notes = suggestion.implementation_notes
            print(
                f"     Implementation: {notes[:100]}{'...' if len(notes) > 100 else ''}"
            )
            if suggestion.related_issue_id:
                print(f"     Addresses: {suggestion.related_issue_id}")
    else:
        print("No improvement suggestions.")
    print()

    # Checklist review
    if report.checklist_review:
        print("Code Review Checklist:")
        for item in report.checklist_review:
            status_icon = {
                "PASS": "[PASS]",
                "WARNING": "[WARN]",
                "FAIL": "[FAIL]",
            }.get(item.status, "[????]")
            print(f"  {status_icon} {item.category}: {item.description}")
            if item.related_issues:
                print(f"        Related Issues: {', '.join(item.related_issues)}")
    print()


def example_simple_calculator():
    """Example 1: Review simple calculator code (should PASS)."""
    print_header("Example 1: Simple Calculator Code Review")

    print("Creating well-written calculator code with good practices...")

    generated_code = GeneratedCode(
        task_id="CALC-001",
        files=[
            GeneratedFile(
                file_path="src/calculator.py",
                content='''"""
Simple calculator module.

Provides basic arithmetic operations with proper error handling.
"""

from typing import Union


def add(a: Union[int, float], b: Union[int, float]) -> Union[int, float]:
    """
    Add two numbers.

    Args:
        a: First number (int or float)
        b: Second number (int or float)

    Returns:
        Sum of a and b

    Examples:
        >>> add(2, 3)
        5
        >>> add(2.5, 3.5)
        6.0
    """
    return a + b


def divide(a: Union[int, float], b: Union[int, float]) -> float:
    """
    Divide two numbers with proper error handling.

    Args:
        a: Numerator
        b: Denominator

    Returns:
        Result of a / b

    Raises:
        ValueError: If b is zero

    Examples:
        >>> divide(10, 2)
        5.0
    """
    if b == 0:
        raise ValueError("Cannot divide by zero")
    return a / b
''',
                file_type="source",
                description="Calculator module with type hints, docstrings, and error handling",
            ),
            GeneratedFile(
                file_path="tests/test_calculator.py",
                content='''"""Comprehensive tests for calculator module."""

import pytest
from calculator import add, divide


class TestAddition:
    """Tests for add function."""

    def test_add_positive_numbers(self):
        """Test adding two positive numbers."""
        assert add(2, 3) == 5

    def test_add_negative_numbers(self):
        """Test adding negative numbers."""
        assert add(-2, -3) == -5

    def test_add_floats(self):
        """Test adding floating point numbers."""
        assert add(2.5, 3.5) == 6.0


class TestDivision:
    """Tests for divide function."""

    def test_divide_positive(self):
        """Test dividing positive numbers."""
        assert divide(10, 2) == 5.0

    def test_divide_by_zero_raises_error(self):
        """Test that dividing by zero raises ValueError."""
        with pytest.raises(ValueError, match="Cannot divide by zero"):
            divide(10, 0)

    def test_divide_floats(self):
        """Test dividing floating point numbers."""
        result = divide(7.5, 2.5)
        assert abs(result - 3.0) < 0.0001
''',
                file_type="test",
                description="Comprehensive test suite with edge cases and error handling",
            ),
            GeneratedFile(
                file_path="README.md",
                content="""# Calculator Module

Simple calculator with basic arithmetic operations.

## Features
- Addition and division operations
- Type hints for better IDE support
- Comprehensive docstrings
- Error handling for edge cases
- Full test coverage

## Usage

```python
from calculator import add, divide

result = add(2, 3)  # Returns 5
result = divide(10, 2)  # Returns 5.0
```

## Testing

Run tests with pytest:
```bash
pytest tests/
```
""",
                file_type="documentation",
                description="Project documentation with usage examples",
            ),
        ],
        dependencies=["pytest"],
        total_files=3,
        total_lines_of_code=120,
        implementation_notes="Clean code following Python best practices",
    )

    print("Running code review orchestrator...")
    orchestrator = CodeReviewOrchestrator()

    report = orchestrator.execute(generated_code)

    print_code_review_report(report)

    return report


def example_security_issues():
    """Example 2: Review code with security vulnerabilities (should FAIL)."""
    print_header("Example 2: Code with Security Issues")

    print("Creating code with SQL injection and security vulnerabilities...")

    generated_code = GeneratedCode(
        task_id="AUTH-001",
        files=[
            GeneratedFile(
                file_path="src/api/auth.py",
                content="""
from flask import request, jsonify

SECRET_KEY = "my_secret_key_12345"  # Hardcoded secret

def login():
    username = request.form.get("username")
    password = request.form.get("password")

    # SQL Injection vulnerability
    query = f"SELECT * FROM users WHERE username = '{username}' AND password = '{password}'"

    result = db.execute(query)
    user = result.fetchone()

    if user:
        # Weak token generation
        token = f"{user['id']}_{SECRET_KEY}"
        return jsonify({"token": token})

    return jsonify({"error": "Invalid credentials"}), 401
""",
                file_type="source",
                description="Authentication API with multiple security issues",
            ),
        ],
        dependencies=["flask"],
        total_files=1,
        total_lines_of_code=25,
    )

    print("Running code review orchestrator...")
    orchestrator = CodeReviewOrchestrator()

    report = orchestrator.execute(generated_code)

    print_code_review_report(report)

    return report


def example_full_workflow():
    """Example 3: Full workflow from design to code review."""
    print_header("Example 3: Full Workflow (Design → Code → Code Review)")

    print("Step 1: Creating a simple design specification...")

    design_spec = DesignSpecification(
        task_id="TODO-API-001",
        api_contracts=[
            APIContract(
                endpoint="/api/todos",
                method="GET",
                description="List all todos for the current user",
                response_schema={"todos": ["array of todo objects"]},
                authentication_required=True,
            ),
            APIContract(
                endpoint="/api/todos",
                method="POST",
                description="Create a new todo item",
                request_schema={"title": "string", "description": "string"},
                response_schema={"todo": "object"},
                authentication_required=True,
            ),
        ],
        data_schemas=[
            DataSchema(
                table_name="todos",
                description="Todo items table",
                columns=[
                    {"name": "id", "type": "UUID", "constraints": "PRIMARY KEY"},
                    {
                        "name": "user_id",
                        "type": "UUID",
                        "constraints": "NOT NULL REFERENCES users(id)",
                    },
                    {
                        "name": "title",
                        "type": "VARCHAR(255)",
                        "constraints": "NOT NULL",
                    },
                    {
                        "name": "completed",
                        "type": "BOOLEAN",
                        "constraints": "DEFAULT FALSE",
                    },
                ],
                indexes=["CREATE INDEX idx_todos_user_id ON todos(user_id)"],
            )
        ],
        component_logic=[
            ComponentLogic(
                component_name="TodoService",
                semantic_unit_id="SU-001",
                responsibility="Business logic for todo CRUD operations",
                interfaces=[
                    {
                        "method": "list_todos",
                        "parameters": {"user_id": "UUID"},
                        "returns": "list[Todo]",
                    },
                    {
                        "method": "create_todo",
                        "parameters": {"title": "str", "user_id": "UUID"},
                        "returns": "Todo",
                    },
                ],
                implementation_notes="Use repository pattern for data access",
            )
        ],
        design_review_checklist=[
            DesignReviewChecklistItem(
                category="Security",
                description="All endpoints require authentication",
                validation_criteria="Every endpoint has authentication_required=True",
                severity="Critical",
            ),
            DesignReviewChecklistItem(
                category="API Design",
                description="RESTful API conventions followed",
                validation_criteria="Correct HTTP methods and resource naming",
            ),
            DesignReviewChecklistItem(
                category="Data Integrity",
                description="Foreign key relationships defined",
                validation_criteria="All relationships use proper foreign key constraints",
            ),
            DesignReviewChecklistItem(
                category="Performance",
                description="Database indexes on frequently queried columns",
                validation_criteria="Index on user_id for filtering todos",
            ),
            DesignReviewChecklistItem(
                category="Maintainability",
                description="Separation of concerns maintained",
                validation_criteria="Clear separation between API, service, and data layers",
            ),
        ],
    )

    print("\nStep 2: Generating code from design...")
    print("(In real workflow, this would call CodeAgent.execute())")
    print("For this example, we'll create sample generated code...")

    generated_code = GeneratedCode(
        task_id="TODO-API-001",
        files=[
            GeneratedFile(
                file_path="src/api/todos.py",
                content='''"""
Todo API endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException
from typing import List
from uuid import UUID

from .auth import get_current_user
from ..services.todo_service import TodoService
from ..models.todo import Todo, TodoCreate

router = APIRouter(prefix="/api/todos", tags=["todos"])


@router.get("/", response_model=List[Todo])
async def list_todos(
    current_user: dict = Depends(get_current_user),
    todo_service: TodoService = Depends()
):
    """List all todos for the current user."""
    return await todo_service.list_todos(user_id=current_user["id"])


@router.post("/", response_model=Todo, status_code=201)
async def create_todo(
    todo_data: TodoCreate,
    current_user: dict = Depends(get_current_user),
    todo_service: TodoService = Depends()
):
    """Create a new todo item."""
    return await todo_service.create_todo(
        title=todo_data.title,
        description=todo_data.description,
        user_id=current_user["id"]
    )
''',
                file_type="source",
                description="FastAPI endpoints for todo operations with authentication",
            ),
            GeneratedFile(
                file_path="src/services/todo_service.py",
                content='''"""
Todo business logic service.
"""

from typing import List
from uuid import UUID

from ..models.todo import Todo, TodoCreate
from ..repositories.todo_repository import TodoRepository


class TodoService:
    """Service layer for todo operations."""

    def __init__(self, repository: TodoRepository):
        """Initialize service with repository."""
        self.repository = repository

    async def list_todos(self, user_id: UUID) -> List[Todo]:
        """
        Get all todos for a user.

        Args:
            user_id: User ID to filter todos

        Returns:
            List of todos for the user
        """
        return await self.repository.find_by_user(user_id)

    async def create_todo(
        self, title: str, description: str, user_id: UUID
    ) -> Todo:
        """
        Create a new todo item.

        Args:
            title: Todo title
            description: Todo description
            user_id: Owner user ID

        Returns:
            Created todo object

        Raises:
            ValueError: If title is empty
        """
        if not title or not title.strip():
            raise ValueError("Title cannot be empty")

        todo_data = TodoCreate(
            title=title.strip(),
            description=description,
            user_id=user_id
        )

        return await self.repository.create(todo_data)
''',
                file_type="source",
                description="Service layer with business logic and validation",
            ),
            GeneratedFile(
                file_path="tests/test_todos_api.py",
                content='''"""
Tests for todo API endpoints.
"""

import pytest
from fastapi.testclient import TestClient
from uuid import uuid4


def test_list_todos_requires_auth(client: TestClient):
    """Test that listing todos requires authentication."""
    response = client.get("/api/todos/")
    assert response.status_code == 401


def test_create_todo_success(client: TestClient, auth_headers):
    """Test creating a todo successfully."""
    todo_data = {
        "title": "Test Todo",
        "description": "Test description"
    }
    response = client.post(
        "/api/todos/",
        json=todo_data,
        headers=auth_headers
    )
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Test Todo"
    assert data["completed"] is False


def test_create_todo_empty_title_fails(client: TestClient, auth_headers):
    """Test that creating todo with empty title fails."""
    todo_data = {"title": "", "description": "Test"}
    response = client.post(
        "/api/todos/",
        json=todo_data,
        headers=auth_headers
    )
    assert response.status_code == 400
''',
                file_type="test",
                description="API tests with authentication and validation scenarios",
            ),
        ],
        dependencies=["fastapi", "pydantic", "sqlalchemy", "pytest"],
        total_files=3,
        total_lines_of_code=150,
        implementation_notes="Clean FastAPI implementation with dependency injection",
    )

    print("\nStep 3: Running code review orchestrator...")
    orchestrator = CodeReviewOrchestrator()

    report = orchestrator.execute(generated_code)

    print_code_review_report(report)

    return report


def main():
    """Main entry point for example script."""
    parser = argparse.ArgumentParser(
        description="Code Review Orchestrator Example Script"
    )
    parser.add_argument(
        "--example",
        choices=["simple", "security-issues", "full-workflow"],
        default="simple",
        help="Which example to run",
    )
    parser.add_argument(
        "--output",
        type=str,
        help="Optional: Save review report to JSON file",
    )

    args = parser.parse_args()

    try:
        # Run selected example
        if args.example == "simple":
            report = example_simple_calculator()
        elif args.example == "security-issues":
            report = example_security_issues()
        elif args.example == "full-workflow":
            report = example_full_workflow()

        # Save report if output file specified
        if args.output:
            output_path = Path(args.output)
            with open(output_path, "w") as f:
                json.dump(report.model_dump(), f, indent=2, default=str)
            print(f"\nReview report saved to: {output_path}")

        # Print final summary
        print_header("Example Complete")
        print(f"Overall Assessment: {report.overall_assessment}")
        print(f"Total Issues: {len(report.issues_found)}")
        print(
            f"Critical: {report.critical_issue_count}, High: {report.high_issue_count}"
        )
        print()

        return 0

    except Exception as e:
        print(f"\nError: {e}", file=sys.stderr)
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
