"""
Pytest configuration and fixtures for Hello World API tests.

Provides test database setup, test client fixtures, and mock data generation
for comprehensive testing of the Hello World API application.

Author: ASP Code Agent
"""

import os
import tempfile
from datetime import datetime, timezone
from typing import Any, Dict, Generator
from unittest.mock import Mock, patch

import pytest

# Demo app fixtures removed - demo app moved to artifacts/
# ASP platform tests use MockLLMClient and don't need FastAPI/database fixtures


# Pytest configuration
def pytest_configure(config):
    """
    Configure pytest with custom markers and settings.

    Args:
        config: Pytest configuration object
    """
    config.addinivalue_line("markers", "unit: mark test as a unit test")
    config.addinivalue_line("markers", "integration: mark test as an integration test")
    config.addinivalue_line("markers", "performance: mark test as a performance test")
    config.addinivalue_line(
        "markers", "error_handling: mark test as error handling test"
    )


def pytest_collection_modifyitems(config, items):
    """
    Modify test collection to add markers based on test names.

    Args:
        config: Pytest configuration object
        items: List of collected test items
    """
    for item in items:
        # Add markers based on test file location
        if "unit" in str(item.fspath):
            item.add_marker(pytest.mark.unit)
        elif "integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)
        elif "e2e" in str(item.fspath):
            item.add_marker(pytest.mark.e2e)


# ============================================================================
# E2E Test Fixtures and Mock LLM Client
# ============================================================================


class MockLLMClient:
    """
    Mock LLM client for E2E tests when ANTHROPIC_API_KEY is not available.

    Returns realistic responses based on common ASP agent patterns.
    """

    def __init__(self, api_key: str = "mock-api-key"):
        """Initialize mock LLM client."""
        self.api_key = api_key
        self.call_count = 0

    def call_with_retry(
        self,
        prompt: str,
        model: str = "claude-haiku-4-5",
        max_tokens: int = 4096,
        temperature: float = 0.0,
        system: str = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Mock LLM API call that returns realistic responses.

        Analyzes the prompt to determine which agent is calling and returns
        appropriate mock data.
        """
        import json

        self.call_count += 1

        # Determine which agent is calling based on prompt content
        # Check most specific patterns first to avoid mismatches
        prompt_lower = prompt.lower()

        # Debug: print first 200 chars to help diagnose detection issues
        # print(f"[MockLLM] Prompt preview: {prompt[:200]}...")

        # Be very specific about design review vs design generation
        # Check for review INTENT specifically
        is_reviewing = (
            "review the following design" in prompt_lower
            or "evaluate the design" in prompt_lower
            or "assess whether the design" in prompt_lower
        )

        if is_reviewing:
            # Design Review Agent - reviewing a design
            content = self._mock_design_review_response(prompt)
        elif (
            "code review" in prompt_lower
            or "review the code" in prompt_lower
            or "reviewing code" in prompt_lower
        ):
            # Code Review Agent - return mock code review
            content = self._mock_code_review_response(prompt)
        elif "design" in prompt_lower and any(
            word in prompt_lower
            for word in ["create", "generate", "produce", "specification", "document"]
        ):
            # Design Agent - creating design specification (JSON)
            content = self._mock_design_specification_response(prompt)
        elif "semantic units" in prompt_lower or "decompose" in prompt_lower:
            # Planning Agent - return mock semantic units
            content = self._mock_planning_response(prompt)
        elif (
            "generate code" in prompt_lower
            or "implement" in prompt_lower
            or "code generation" in prompt_lower
        ):
            # Code Agent - return mock code generation
            content = self._mock_code_generation_response(prompt)
        elif (
            "generate tests" in prompt_lower
            or "test generation" in prompt_lower
            or "test plan" in prompt_lower
        ):
            # Test Agent - return mock test plan
            content = self._mock_test_response(prompt)
        elif "postmortem" in prompt_lower or (
            "defect" in prompt_lower and "effort" in prompt_lower
        ):
            # Postmortem Agent - return mock postmortem
            content = self._mock_postmortem_response(prompt)
        else:
            # Generic response (for markdown design, etc.)
            content = self._mock_design_response(prompt)

        # Parse JSON strings to match real LLMClient behavior
        # Real LLMClient calls _try_parse_json() which returns dict for JSON
        parsed_content = content
        if isinstance(content, str):
            try:
                parsed_content = json.loads(content)
            except json.JSONDecodeError:
                # Not JSON, keep as string (e.g., for design markdown)
                parsed_content = content

        return {
            "content": parsed_content,
            "usage": {
                "input_tokens": len(prompt.split()) * 2,  # Rough estimate
                "output_tokens": len(str(content).split()) * 2,
            },
            "model": model,
            "stop_reason": "end_turn",
        }

    def _mock_planning_response(self, prompt: str) -> str:
        """Generate mock planning response with semantic units."""
        return """{
  "semantic_units": [
    {
      "unit_id": "SU-001",
      "description": "Implement API endpoint handler",
      "api_interactions": 2,
      "data_transformations": 1,
      "logical_branches": 2,
      "code_entities_modified": 3,
      "novelty_multiplier": 1.2,
      "est_complexity": 18,
      "dependencies": []
    },
    {
      "unit_id": "SU-002",
      "description": "Add validation logic",
      "api_interactions": 0,
      "data_transformations": 2,
      "logical_branches": 3,
      "code_entities_modified": 2,
      "novelty_multiplier": 1.0,
      "est_complexity": 12,
      "dependencies": ["SU-001"]
    },
    {
      "unit_id": "SU-003",
      "description": "Implement error handling",
      "api_interactions": 0,
      "data_transformations": 1,
      "logical_branches": 4,
      "code_entities_modified": 2,
      "novelty_multiplier": 1.0,
      "est_complexity": 14,
      "dependencies": ["SU-001"]
    }
  ]
}"""

    def _mock_design_response(self, prompt: str) -> str:
        """Generate mock design document response."""
        return """# Design Document

## Overview
This design addresses the requirements specified in the task.

## Architecture
- Component A: Handles input validation
- Component B: Processes business logic
- Component C: Manages data persistence

## Implementation Plan
1. Create API endpoint structure
2. Implement validation layer
3. Add error handling
4. Write unit tests

## Dependencies
- FastAPI framework
- Pydantic for validation
- SQLAlchemy for database

## Testing Strategy
- Unit tests for each component
- Integration tests for API endpoints
- E2E tests for complete workflow
"""

    def _mock_design_review_response(self, prompt: str) -> str:
        """Generate mock design review response."""
        return """{
  "issues_found": [],
  "critical_issues": [],
  "high_issues": [],
  "medium_issues": [],
  "low_issues": [],
  "overall_assessment": "PASS",
  "critical_issue_count": 0,
  "high_issue_count": 0,
  "medium_issue_count": 0,
  "low_issue_count": 0,
  "total_issue_count": 0,
  "replanning_required": false,
  "redesign_required": false,
  "issues_requiring_replanning": [],
  "issues_requiring_redesign": [],
  "summary": "Design review passed with no critical issues found. The design appears solid and ready for implementation."
}"""

    def _mock_code_review_response(self, prompt: str) -> str:
        """Generate mock code review response."""
        return """{
  "issues": [],
  "overall_quality": "good",
  "recommendations": [
    "Consider adding docstrings",
    "Add type hints where missing"
  ]
}"""

    def _mock_test_response(self, prompt: str) -> str:
        """Generate mock test plan response."""
        return """{
  "test_plan": {
    "unit_tests": ["test_validation", "test_processing"],
    "integration_tests": ["test_api_endpoint"],
    "coverage_target": 80
  }
}"""

    def _mock_design_specification_response(self, prompt: str) -> str:
        """Generate mock design specification response (JSON format)."""
        return """{
  "task_id": "TEST-001",
  "api_contracts": [
    {
      "endpoint": "/api/users",
      "method": "GET",
      "description": "Retrieve user list",
      "request_schema": {},
      "response_schema": {"users": "array"},
      "error_responses": [{"status_code": 404, "description": "Not found"}]
    }
  ],
  "data_schemas": [
    {
      "table_name": "users",
      "columns": [
        {"name": "id", "type": "INTEGER", "constraints": ["PRIMARY KEY"]},
        {"name": "email", "type": "VARCHAR(255)", "constraints": ["UNIQUE", "NOT NULL"]}
      ]
    }
  ],
  "component_logic": [
    {
      "component_name": "UserService",
      "description": "Handles user business logic",
      "responsibilities": ["User CRUD operations", "Validation"],
      "dependencies": ["Database"],
      "key_methods": [
        {"name": "get_user", "parameters": ["user_id"], "return_type": "User"}
      ]
    }
  ],
  "design_review_checklist": [
    {"criterion": "API endpoints follow REST conventions", "category": "API Design"},
    {"criterion": "Database schema normalized", "category": "Data Design"},
    {"criterion": "Error handling defined", "category": "Robustness"},
    {"criterion": "Security measures in place", "category": "Security"},
    {"criterion": "Performance considerations addressed", "category": "Performance"}
  ],
  "architecture_overview": "Simple REST API with service layer and database persistence",
  "technology_stack": {
    "language": "Python 3.12",
    "framework": "FastAPI",
    "database": "PostgreSQL",
    "testing": "pytest"
  },
  "assumptions": ["RESTful API design", "PostgreSQL database available"]
}"""

    def _mock_code_generation_response(self, prompt: str) -> str:
        """Generate mock code generation response."""
        return """{
  "task_id": "TEST-001",
  "files": [
    {
      "file_path": "src/main.py",
      "file_type": "source",
      "language": "python",
      "content": "from fastapi import FastAPI\\n\\napp = FastAPI()\\n\\n@app.get('/')\\ndef read_root():\\n    return {'message': 'Hello World'}",
      "lines_of_code": 6
    },
    {
      "file_path": "tests/test_main.py",
      "file_type": "test",
      "language": "python",
      "content": "def test_read_root():\\n    assert True",
      "lines_of_code": 2
    }
  ],
  "total_files": 2,
  "total_lines_of_code": 8,
  "dependencies": ["fastapi"],
  "implementation_notes": "Basic FastAPI application with hello world endpoint"
}"""

    def _mock_postmortem_response(self, prompt: str) -> str:
        """Generate mock postmortem analysis response."""
        return """{
  "task_id": "TEST-001",
  "actual_time": 120.5,
  "predicted_time": 100.0,
  "prediction_accuracy": 83.3,
  "defects_injected": 0,
  "defects_removed": 0,
  "phase_data": {
    "planning": {"time_spent": 20.0, "defects": 0},
    "design": {"time_spent": 30.0, "defects": 0},
    "coding": {"time_spent": 50.5, "defects": 0},
    "testing": {"time_spent": 20.0, "defects": 0}
  },
  "process_insights": ["Good adherence to estimates", "No defects found"],
  "improvement_recommendations": ["Continue current practices"]
}"""

    def _mock_generic_response(self, prompt: str) -> str:
        """Generate generic mock response."""
        return "Mock response: Processing completed successfully."


@pytest.fixture(scope="session")
def has_api_key() -> bool:
    """
    Check if ANTHROPIC_API_KEY is available.

    Returns:
        bool: True if API key is set, False otherwise
    """
    return bool(os.getenv("ANTHROPIC_API_KEY"))


@pytest.fixture(scope="function")
def llm_client(has_api_key: bool):
    """
    Provide LLM client for testing.

    Returns real LLMClient if ANTHROPIC_API_KEY is available,
    otherwise returns MockLLMClient for testing without API access.

    Args:
        has_api_key: Whether API key is available

    Returns:
        LLMClient or MockLLMClient instance
    """
    if has_api_key:
        # Import here to avoid errors if anthropic package not installed
        try:
            from asp.utils.llm_client import LLMClient

            return LLMClient()
        except (ImportError, ValueError):
            # Fall back to mock if import fails or API key invalid
            return MockLLMClient()
    else:
        return MockLLMClient()
