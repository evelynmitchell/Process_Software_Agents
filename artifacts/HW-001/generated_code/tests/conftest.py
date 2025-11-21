"""
Pytest configuration and fixtures for Hello World API tests.

Provides test client setup, fixtures, and configuration for comprehensive testing
of the FastAPI application endpoints and error handling.

Author: ASP Code Agent
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from datetime import datetime
from typing import Generator, Dict, Any

from src.main import app


@pytest.fixture(scope="session")
def test_client() -> TestClient:
    """
    Create a test client for the FastAPI application.
    
    Returns:
        TestClient: Configured test client for making HTTP requests
    """
    return TestClient(app)


@pytest.fixture(scope="function")
def mock_datetime() -> Generator[MagicMock, None, None]:
    """
    Mock datetime.utcnow() for consistent timestamp testing.
    
    Yields:
        MagicMock: Mocked datetime object with fixed timestamp
    """
    fixed_datetime = datetime(2023, 12, 25, 10, 30, 45)
    with patch('src.main.datetime') as mock_dt:
        mock_dt.utcnow.return_value = fixed_datetime
        yield mock_dt


@pytest.fixture(scope="function")
def valid_names() -> list[str]:
    """
    Provide list of valid name parameters for testing.
    
    Returns:
        list[str]: Valid name strings for parameter testing
    """
    return [
        "John",
        "Jane Doe",
        "Alice123",
        "Bob Smith Jr",
        "Test User 42",
        "a",
        "A" * 100,  # Maximum length
        "123",
        "User With Spaces",
        "CamelCase",
        "lowercase",
        "UPPERCASE"
    ]


@pytest.fixture(scope="function")
def invalid_names() -> list[str]:
    """
    Provide list of invalid name parameters for testing.
    
    Returns:
        list[str]: Invalid name strings that should trigger validation errors
    """
    return [
        "John@Doe",  # Special character
        "Jane-Smith",  # Hyphen
        "User!",  # Exclamation mark
        "Test<script>",  # HTML/XSS attempt
        "Name with\nnewline",  # Newline character
        "User\t",  # Tab character
        "A" * 101,  # Exceeds maximum length
        "José",  # Non-ASCII character
        "User#123",  # Hash symbol
        "Test$User",  # Dollar sign
        "Name%20",  # URL encoding
        "User&Co",  # Ampersand
        "",  # Empty string (handled separately)
        "   ",  # Only whitespace
    ]


@pytest.fixture(scope="function")
def expected_hello_responses() -> Dict[str, str]:
    """
    Provide expected responses for hello endpoint with different names.
    
    Returns:
        Dict[str, str]: Mapping of input names to expected response messages
    """
    return {
        "John": "Hello, John!",
        "jane doe": "Hello, Jane Doe!",
        "alice123": "Hello, Alice123!",
        "bob smith jr": "Hello, Bob Smith Jr!",
        "test user 42": "Hello, Test User 42!",
        "a": "Hello, A!",
        "123": "Hello, 123!",
        "user with spaces": "Hello, User With Spaces!",
        "camelcase": "Hello, Camelcase!",
        "lowercase": "Hello, Lowercase!",
        "UPPERCASE": "Hello, Uppercase!",
        "  padded  ": "Hello, Padded!",
    }


@pytest.fixture(scope="function")
def error_response_schemas() -> Dict[str, Dict[str, Any]]:
    """
    Provide expected error response schemas for validation.
    
    Returns:
        Dict[str, Dict[str, Any]]: Error response schema definitions
    """
    return {
        "validation_error": {
            "required_fields": ["code", "message"],
            "code_value": "INVALID_NAME",
            "status_code": 400
        },
        "internal_error": {
            "required_fields": ["code", "message"],
            "code_value": "INTERNAL_ERROR",
            "status_code": 500
        }
    }


@pytest.fixture(scope="function")
def health_response_schema() -> Dict[str, Any]:
    """
    Provide expected health endpoint response schema.
    
    Returns:
        Dict[str, Any]: Health response schema definition
    """
    return {
        "required_fields": ["status", "timestamp"],
        "status_value": "ok",
        "timestamp_format": r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?Z$"
    }


@pytest.fixture(scope="function")
def hello_response_schema() -> Dict[str, Any]:
    """
    Provide expected hello endpoint response schema.
    
    Returns:
        Dict[str, Any]: Hello response schema definition
    """
    return {
        "required_fields": ["message"],
        "message_format": r"^Hello, .+!$|^Hello, World!$"
    }


@pytest.fixture(autouse=True)
def reset_app_state():
    """
    Reset application state before each test.
    
    This fixture runs automatically before each test to ensure
    clean state and prevent test interference.
    """
    # Clear any cached data or state if needed
    # For this simple app, no state reset is required
    yield
    # Cleanup after test if needed


@pytest.fixture(scope="function")
def mock_exception() -> Generator[MagicMock, None, None]:
    """
    Mock for testing exception handling scenarios.
    
    Yields:
        MagicMock: Mock object that can be configured to raise exceptions
    """
    with patch('src.main.datetime') as mock_dt:
        mock_dt.utcnow.side_effect = Exception("Simulated internal error")
        yield mock_dt


@pytest.fixture(scope="session")
def test_config() -> Dict[str, Any]:
    """
    Provide test configuration settings.
    
    Returns:
        Dict[str, Any]: Test configuration parameters
    """
    return {
        "timeout": 30,
        "max_retries": 3,
        "test_name_max_length": 100,
        "expected_content_type": "application/json",
        "cors_origins": ["*"],
        "api_version": "1.0.0",
        "api_title": "Hello World API"
    }


# Pytest configuration
def pytest_configure(config):
    """Configure pytest with custom markers and settings."""
    config.addinivalue_line(
        "markers", "unit: mark test as a unit test"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as an integration test"
    )
    config.addinivalue_line(
        "markers", "error_handling: mark test as error handling test"
    )
    config.addinivalue_line(
        "markers", "validation: mark test as input validation test"
    )


def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers based on test names."""
    for item in items:
        # Add markers based on test function names
        if "error" in item.name or "exception" in item.name:
            item.add_marker(pytest.mark.error_handling)
        if "validation" in item.name or "invalid" in item.name:
            item.add_marker(pytest.mark.validation)
        if "integration" in item.name or "endpoint" in item.name:
            item.add_marker(pytest.mark.integration)
        else:
            item.add_marker(pytest.mark.unit)