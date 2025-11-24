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
import sys
import os

# Add src directory to Python path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from main import app


@pytest.fixture(scope="session")
def test_client() -> TestClient:
    """
    Create FastAPI test client for the entire test session.
    
    Returns:
        TestClient: Configured test client for making HTTP requests
    """
    return TestClient(app)


@pytest.fixture(scope="function")
def client(test_client: TestClient) -> Generator[TestClient, None, None]:
    """
    Provide test client for individual test functions.
    
    Args:
        test_client: Session-scoped test client
        
    Yields:
        TestClient: Test client instance for making requests
    """
    yield test_client


@pytest.fixture(scope="function")
def mock_datetime() -> Generator[MagicMock, None, None]:
    """
    Mock datetime.utcnow() for consistent timestamp testing.
    
    Yields:
        MagicMock: Mocked datetime with fixed timestamp
    """
    fixed_datetime = datetime(2023, 12, 25, 10, 30, 45)
    
    with patch('main.datetime') as mock_dt:
        mock_dt.utcnow.return_value = fixed_datetime
        mock_dt.side_effect = lambda *args, **kwargs: datetime(*args, **kwargs)
        yield mock_dt


@pytest.fixture(scope="function")
def sample_valid_names() -> list[str]:
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
        "a",  # Single character
        "A" * 100,  # Maximum length
        "User 123 Test",
        "Simple Name",
        "Name With Spaces"
    ]


@pytest.fixture(scope="function")
def sample_invalid_names() -> list[str]:
    """
    Provide list of invalid name parameters for testing.
    
    Returns:
        list[str]: Invalid name strings that should trigger validation errors
    """
    return [
        "John@Doe",  # Special character
        "Jane-Smith",  # Hyphen
        "User!",  # Exclamation mark
        "Test#User",  # Hash symbol
        "Name$",  # Dollar sign
        "User%Test",  # Percent sign
        "Test&User",  # Ampersand
        "Name*",  # Asterisk
        "User+Test",  # Plus sign
        "Test=User",  # Equals sign
        "Name[Test]",  # Brackets
        "User{Test}",  # Braces
        "Test|User",  # Pipe
        "Name\\Test",  # Backslash
        "User/Test",  # Forward slash
        "Test:User",  # Colon
        "Name;Test",  # Semicolon
        "User<Test>",  # Angle brackets
        "Test?User",  # Question mark
        "Name.Test",  # Period
        "User,Test",  # Comma
        "Test'User",  # Apostrophe
        'Name"Test',  # Quote
        "A" * 101,  # Exceeds maximum length
        "",  # Empty string (handled as None)
        "   ",  # Only spaces
        "\n",  # Newline
        "\t",  # Tab
        "User\nTest",  # Contains newline
        "Test\tUser",  # Contains tab
    ]


@pytest.fixture(scope="function")
def expected_error_response() -> Dict[str, Any]:
    """
    Provide expected error response structure.
    
    Returns:
        Dict[str, Any]: Expected error response format
    """
    return {
        "error": "INVALID_NAME",
        "message": "Name parameter contains invalid characters or exceeds 100 characters"
    }


@pytest.fixture(scope="function")
def expected_health_response() -> Dict[str, str]:
    """
    Provide expected health endpoint response structure.
    
    Returns:
        Dict[str, str]: Expected health response format
    """
    return {
        "status": "ok",
        "timestamp": "2023-12-25T10:30:45Z"
    }


@pytest.fixture(scope="function")
def mock_exception_logging() -> Generator[MagicMock, None, None]:
    """
    Mock logging for exception handler testing.
    
    Yields:
        MagicMock: Mocked logger for verifying error logging
    """
    with patch('main.logger') as mock_logger:
        yield mock_logger


@pytest.fixture(autouse=True)
def reset_app_state() -> Generator[None, None, None]:
    """
    Reset application state before each test.
    
    This fixture runs automatically before each test to ensure
    clean state and prevent test interference.
    
    Yields:
        None: No return value, just ensures clean state
    """
    # Clear any cached data or state if needed
    yield
    # Cleanup after test if needed


@pytest.fixture(scope="function")
def hello_endpoint_test_cases() -> list[Dict[str, Any]]:
    """
    Provide comprehensive test cases for hello endpoint.
    
    Returns:
        list[Dict[str, Any]]: Test cases with inputs and expected outputs
    """
    return [
        {
            "name": "no_name_parameter",
            "input": None,
            "expected_message": "Hello, World!",
            "expected_status": 200
        },
        {
            "name": "empty_name_parameter",
            "input": "",
            "expected_message": "Hello, World!",
            "expected_status": 200
        },
        {
            "name": "simple_name",
            "input": "John",
            "expected_message": "Hello, John!",
            "expected_status": 200
        },
        {
            "name": "name_with_spaces",
            "input": "Jane Doe",
            "expected_message": "Hello, Jane Doe!",
            "expected_status": 200
        },
        {
            "name": "name_with_numbers",
            "input": "User123",
            "expected_message": "Hello, User123!",
            "expected_status": 200
        },
        {
            "name": "maximum_length_name",
            "input": "A" * 100,
            "expected_message": f"Hello, {'A' * 100}!",
            "expected_status": 200
        }
    ]


@pytest.fixture(scope="function")
def error_test_cases() -> list[Dict[str, Any]]:
    """
    Provide test cases for error scenarios.
    
    Returns:
        list[Dict[str, Any]]: Error test cases with inputs and expected responses
    """
    return [
        {
            "name": "name_too_long",
            "input": "A" * 101,
            "expected_status": 400,
            "expected_error": "INVALID_NAME"
        },
        {
            "name": "name_with_special_chars",
            "input": "John@Doe",
            "expected_status": 400,
            "expected_error": "INVALID_NAME"
        },
        {
            "name": "name_with_symbols",
            "input": "User!",
            "expected_status": 400,