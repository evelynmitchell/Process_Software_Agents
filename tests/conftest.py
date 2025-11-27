"""
Pytest configuration and fixtures for Hello World API tests.

Provides test database setup, test client fixtures, and mock data generation
for comprehensive testing of the Hello World API application.

Author: ASP Code Agent
"""

import os
import tempfile
from datetime import datetime, timezone
from typing import Generator, Any, Dict
from unittest.mock import Mock, patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

from src.main import app
from src.database.connection import get_db, Base


@pytest.fixture(scope="session")
def test_database_url() -> str:
    """
    Create a temporary SQLite database URL for testing.
    
    Returns:
        str: SQLite database URL for testing
    """
    # Create temporary file for test database
    db_fd, db_path = tempfile.mkstemp(suffix='.db')
    os.close(db_fd)
    
    # Ensure cleanup after tests
    def cleanup():
        if os.path.exists(db_path):
            os.unlink(db_path)
    
    # Register cleanup function
    import atexit
    atexit.register(cleanup)
    
    return f"sqlite:///{db_path}"


@pytest.fixture(scope="session")
def test_engine(test_database_url: str):
    """
    Create SQLAlchemy engine for test database.
    
    Args:
        test_database_url: Database URL for testing
        
    Returns:
        Engine: SQLAlchemy engine instance
    """
    engine = create_engine(
        test_database_url,
        connect_args={
            "check_same_thread": False,
        },
        poolclass=StaticPool,
        echo=False  # Set to True for SQL debugging
    )
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    
    yield engine
    
    # Cleanup
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture(scope="function")
def test_db_session(test_engine) -> Generator[Session, None, None]:
    """
    Create a database session for testing with automatic rollback.
    
    Args:
        test_engine: SQLAlchemy engine for testing
        
    Yields:
        Session: Database session for testing
    """
    TestingSessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=test_engine
    )
    
    session = TestingSessionLocal()
    
    try:
        yield session
    finally:
        session.rollback()
        session.close()


@pytest.fixture(scope="function")
def client(test_db_session: Session) -> TestClient:
    """
    Create FastAPI test client with test database session.
    
    Args:
        test_db_session: Database session for testing
        
    Returns:
        TestClient: FastAPI test client instance
    """
    def override_get_db():
        try:
            yield test_db_session
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as test_client:
        yield test_client
    
    # Clean up dependency override
    app.dependency_overrides.clear()


@pytest.fixture
def mock_datetime_now():
    """
    Mock datetime.utcnow() to return a fixed timestamp for testing.
    
    Returns:
        Mock: Mocked datetime with fixed timestamp
    """
    fixed_datetime = datetime(2024, 1, 15, 12, 30, 45, tzinfo=timezone.utc)
    
    with patch('src.main.datetime') as mock_dt:
        mock_dt.utcnow.return_value = fixed_datetime
        mock_dt.timezone = timezone
        yield mock_dt


@pytest.fixture
def sample_hello_response() -> Dict[str, str]:
    """
    Generate sample Hello World API response for testing.
    
    Returns:
        dict: Sample response matching API contract
    """
    return {
        "message": "Hello World",
        "timestamp": "2024-01-15T12:30:45.000000Z",
        "status": "success"
    }


@pytest.fixture
def mock_internal_error():
    """
    Mock internal server error for error handling tests.
    
    Returns:
        Mock: Mock that raises an exception when called
    """
    def raise_error(*args, **kwargs):
        raise Exception("Simulated internal error")
    
    return Mock(side_effect=raise_error)


@pytest.fixture(scope="function")
def clean_environment():
    """
    Ensure clean environment variables for testing.
    
    Yields:
        None: Clean environment context
    """
    # Store original environment
    original_env = os.environ.copy()
    
    # Set test environment variables
    test_env_vars = {
        "TESTING": "true",
        "LOG_LEVEL": "DEBUG",
        "DATABASE_URL": "sqlite:///test.db"
    }
    
    for key, value in test_env_vars.items():
        os.environ[key] = value
    
    try:
        yield
    finally:
        # Restore original environment
        os.environ.clear()
        os.environ.update(original_env)


@pytest.fixture
def performance_timer():
    """
    Timer fixture for performance testing.
    
    Returns:
        callable: Timer function that returns elapsed time
    """
    import time
    
    start_times = {}
    
    def timer(operation: str = "default") -> float:
        current_time = time.perf_counter()
        
        if operation not in start_times:
            start_times[operation] = current_time
            return 0.0
        else:
            elapsed = current_time - start_times[operation]
            del start_times[operation]
            return elapsed
    
    return timer


@pytest.fixture
def mock_response_formatter():
    """
    Mock response formatter for testing response structure.
    
    Returns:
        Mock: Mock formatter function
    """
    def format_response(message: str) -> Dict[str, str]:
        return {
            "message": message,
            "timestamp": "2024-01-15T12:30:45.000000Z",
            "status": "success"
        }
    
    return Mock(side_effect=format_response)


@pytest.fixture(autouse=True)
def reset_app_state():
    """
    Reset application state before each test.
    
    This fixture automatically runs before each test to ensure
    clean application state and prevent test interference.
    """
    # Clear any cached data or state
    app.dependency_overrides.clear()
    
    yield
    
    # Cleanup after test
    app.dependency_overrides.clear()


# Pytest configuration
def pytest_configure(config):
    """
    Configure pytest with custom markers and settings.
    
    Args:
        config: Pytest configuration object
    """
    config.addinivalue_line(
        "markers", "unit: mark test as a unit test"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as an integration test"
    )
    config.addinivalue_line(
        "markers", "performance: mark test as a performance test"
    )
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
        **kwargs
    ) -> Dict[str, Any]:
        """
        Mock LLM API call that returns realistic responses.

        Analyzes the prompt to determine which agent is calling and returns
        appropriate mock data.
        """
        self.call_count += 1

        # Determine which agent is calling based on prompt content
        if "semantic units" in prompt.lower() or "planning" in prompt.lower():
            # Planning Agent - return mock semantic units
            content = self._mock_planning_response(prompt)
        elif "design" in prompt.lower() and "review" in prompt.lower():
            # Design Review Agent - return mock design issues
            content = self._mock_design_review_response(prompt)
        elif "design" in prompt.lower():
            # Design Agent - return mock design document
            content = self._mock_design_response(prompt)
        elif "code review" in prompt.lower():
            # Code Review Agent - return mock code review
            content = self._mock_code_review_response(prompt)
        elif "test" in prompt.lower():
            # Test Agent - return mock test plan
            content = self._mock_test_response(prompt)
        else:
            # Generic response
            content = self._mock_generic_response(prompt)

        return {
            "content": content,
            "usage": {
                "input_tokens": len(prompt.split()) * 2,  # Rough estimate
                "output_tokens": len(content.split()) * 2 if isinstance(content, str) else 500,
            },
            "model": model,
            "stop_reason": "end_turn",
        }

    def _mock_planning_response(self, prompt: str) -> str:
        """Generate mock planning response with semantic units."""
        return """```json
{
  "semantic_units": [
    {
      "unit_id": "SU-001",
      "description": "Implement API endpoint handler",
      "api_interactions": 2,
      "data_transformations": 1,
      "logical_branches": 2,
      "code_entities_modified": 3,
      "novelty_multiplier": 1.2,
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
      "dependencies": ["SU-001"]
    }
  ]
}
```"""

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
        return """```json
{
  "issues": [
    {
      "issue_type": "missing_requirement",
      "severity": "high",
      "affected_phase": "Design",
      "description": "Error handling strategy not fully defined",
      "recommendation": "Add comprehensive error handling section"
    }
  ],
  "overall_assessment": "good",
  "requires_replanning": false
}
```"""

    def _mock_code_review_response(self, prompt: str) -> str:
        """Generate mock code review response."""
        return """```json
{
  "issues": [],
  "overall_quality": "good",
  "recommendations": [
    "Consider adding docstrings",
    "Add type hints where missing"
  ]
}
```"""

    def _mock_test_response(self, prompt: str) -> str:
        """Generate mock test plan response."""
        return """```json
{
  "test_plan": {
    "unit_tests": ["test_validation", "test_processing"],
    "integration_tests": ["test_api_endpoint"],
    "coverage_target": 80
  }
}
```"""

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