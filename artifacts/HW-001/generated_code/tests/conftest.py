"""
Pytest configuration and fixtures for Hello World API tests.

Provides test client setup, fixtures, and configuration for comprehensive testing
of the FastAPI application endpoints and error handling.

Author: ASP Code Agent
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch
from datetime import datetime
from typing import Generator, Dict, Any
import logging
import sys
import os

# Add src directory to Python path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from main import app


# Configure logging for tests
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


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
        TestClient: Test client instance for the test function
    """
    yield test_client


@pytest.fixture(scope="function")
def mock_datetime() -> Generator[Mock, None, None]:
    """
    Mock datetime.utcnow() for consistent timestamp testing.
    
    Yields:
        Mock: Mocked datetime object with fixed timestamp
    """
    fixed_datetime = datetime(2023, 12, 25, 10, 30, 45)
    with patch('main.datetime') as mock_dt:
        mock_dt.utcnow.return_value = fixed_datetime
        mock_dt.side_effect = lambda *args, **kw: datetime(*args, **kw)
        yield mock_dt


@pytest.fixture(scope="function")
def sample_valid_names() -> list[str]:
    """
    Provide list of valid name parameters for testing.
    
    Returns:
        list[str]: Valid name strings for testing
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
        "Mary Jane Watson",
        "X Æ A 12"  # Contains special characters that should be invalid
    ]


@pytest.fixture(scope="function")
def sample_invalid_names() -> list[str]:
    """
    Provide list of invalid name parameters for testing.
    
    Returns:
        list[str]: Invalid name strings for testing
    """
    return [
        "John@Doe",  # Contains @
        "Jane-Smith",  # Contains hyphen
        "User!",  # Contains exclamation
        "Test#User",  # Contains hash
        "Name$",  # Contains dollar sign
        "User%",  # Contains percent
        "Test^User",  # Contains caret
        "Name&Co",  # Contains ampersand
        "User*",  # Contains asterisk
        "Test(User)",  # Contains parentheses
        "Name+",  # Contains plus
        "User=Test",  # Contains equals
        "Name[Test]",  # Contains brackets
        "User{Test}",  # Contains braces
        "Name|Test",  # Contains pipe
        "User\\Test",  # Contains backslash
        "Name:Test",  # Contains colon
        "User;Test",  # Contains semicolon
        "Name\"Test\"",  # Contains quotes
        "User'Test'",  # Contains apostrophes
        "Name<Test>",  # Contains angle brackets
        "User,Test",  # Contains comma
        "Name.Test",  # Contains period
        "User?Test",  # Contains question mark
        "Name/Test",  # Contains slash
        "User~Test",  # Contains tilde
        "Name`Test`",  # Contains backticks
        "A" * 101,  # Exceeds maximum length
        "",  # Empty string (should be handled as None)
        "   ",  # Only spaces
        "\n",  # Newline character
        "\t",  # Tab character
        "\r",  # Carriage return
        "Test\nUser",  # Contains newline
        "Test\tUser",  # Contains tab
    ]


@pytest.fixture(scope="function")
def expected_error_responses() -> Dict[str, Dict[str, Any]]:
    """
    Provide expected error response formats for testing.
    
    Returns:
        Dict[str, Dict[str, Any]]: Expected error response structures
    """
    return {
        "invalid_name": {
            "status_code": 400,
            "response_format": {
                "error": {
                    "code": "INVALID_NAME",
                    "message": "Name parameter contains invalid characters or exceeds 100 characters"
                }
            }
        },
        "internal_error": {
            "status_code": 500,
            "response_format": {
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": "Internal server error"
                }
            }
        }
    }


@pytest.fixture(scope="function")
def expected_success_responses() -> Dict[str, Dict[str, Any]]:
    """
    Provide expected success response formats for testing.
    
    Returns:
        Dict[str, Dict[str, Any]]: Expected success response structures
    """
    return {
        "hello_default": {
            "status_code": 200,
            "response_format": {
                "message": "Hello, World!"
            }
        },
        "hello_personalized": {
            "status_code": 200,
            "response_format": {
                "message": "Hello, {name}!"
            }
        },
        "health": {
            "status_code": 200,
            "response_format": {
                "status": "ok",
                "timestamp": "2023-12-25T10:30:45Z"
            }
        }
    }


@pytest.fixture(scope="function")
def mock_logger() -> Generator[Mock, None, None]:
    """
    Mock logger for testing error handling and logging behavior.
    
    Yields:
        Mock: Mocked logger instance
    """
    with patch('main.logger') as mock_log:
        yield mock_log


@pytest.fixture(scope="function")
def mock_exception_handler() -> Generator[Mock, None, None]:
    """
    Mock exception handler for testing error handling behavior.
    
    Yields:
        Mock: Mocked exception handler
    """
    with patch('main.handle_general_exception') as mock_handler:
        mock_handler.return_value = {
            "error": {
                "code": "INTERNAL_ERROR",
                "message": "Internal server error"
            }
        }
        yield mock_handler


@pytest.fixture(autouse=True)
def reset_app_state():
    """
    Reset application state before each test to ensure test isolation.
    
    This fixture runs automatically before each test function.
    """
    # Clear any cached data or state if needed
    # For this simple API, no state reset is required
    yield
    # Cleanup after test if needed


@pytest.fixture(scope="function")
def performance_threshold() -> Dict[str, float]:
    """
    Provide performance thresholds for endpoint response time testing.
    
    Returns:
        Dict[str, float]: Performance thresholds in seconds
    """
    return {
        "hello_endpoint": 0.01,  # 10ms
        "health_endpoint": 0.01,  # 10ms
        "error_response": 0.01,  # 10ms
    }


@pytest.fixture(scope="function")
def content_type_headers() -> Dict[str, str]:
    """
    Provide