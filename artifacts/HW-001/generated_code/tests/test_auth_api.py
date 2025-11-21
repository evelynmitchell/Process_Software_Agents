"""
Comprehensive integration tests for authentication endpoints

Tests registration, login, token refresh, and error scenarios for the auth API.

Component ID: COMP-002
Semantic Unit: SU-002

Author: ASP Code Generator
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch
import json
from datetime import datetime, timedelta
import re

from src.api.auth import app


@pytest.fixture
def client():
    """Create test client for FastAPI application."""
    return TestClient(app)


@pytest.fixture
def mock_user_data():
    """Sample user data for testing."""
    return {
        "username": "testuser",
        "email": "test@example.com",
        "password": "SecurePass123!"
    }


@pytest.fixture
def mock_login_data():
    """Sample login data for testing."""
    return {
        "username": "testuser",
        "password": "SecurePass123!"
    }


@pytest.fixture
def mock_jwt_token():
    """Sample JWT token for testing."""
    return "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ0ZXN0dXNlciIsImV4cCI6MTYzOTU4NzYwMH0.test"


@pytest.fixture
def mock_refresh_token():
    """Sample refresh token for testing."""
    return "refresh_token_12345"


class TestHelloEndpoint:
    """Test cases for /hello endpoint."""

    def test_hello_endpoint_without_name_returns_200(self, client):
        """Test that /hello endpoint returns 200 OK status without name parameter."""
        response = client.get("/hello")
        assert response.status_code == 200

    def test_hello_endpoint_without_name_returns_default_message(self, client):
        """Test that /hello endpoint returns default message without name parameter."""
        response = client.get("/hello")
        data = response.json()
        assert data["message"] == "Hello, World!"

    def test_hello_endpoint_with_valid_name_returns_200(self, client):
        """Test that /hello endpoint returns 200 OK status with valid name parameter."""
        response = client.get("/hello?name=John")
        assert response.status_code == 200

    def test_hello_endpoint_with_valid_name_returns_personalized_message(self, client):
        """Test that /hello endpoint returns personalized message with valid name parameter."""
        response = client.get("/hello?name=John")
        data = response.json()
        assert data["message"] == "Hello, John!"

    def test_hello_endpoint_with_name_containing_spaces_returns_personalized_message(self, client):
        """Test that /hello endpoint handles names with spaces correctly."""
        response = client.get("/hello?name=John Doe")
        data = response.json()
        assert data["message"] == "Hello, John Doe!"

    def test_hello_endpoint_with_numeric_name_returns_personalized_message(self, client):
        """Test that /hello endpoint handles numeric names correctly."""
        response = client.get("/hello?name=User123")
        data = response.json()
        assert data["message"] == "Hello, User123!"

    def test_hello_endpoint_with_lowercase_name_returns_title_case(self, client):
        """Test that /hello endpoint converts name to title case."""
        response = client.get("/hello?name=john")
        data = response.json()
        assert data["message"] == "Hello, John!"

    def test_hello_endpoint_with_whitespace_name_strips_whitespace(self, client):
        """Test that /hello endpoint strips leading and trailing whitespace from name."""
        response = client.get("/hello?name=  John  ")
        data = response.json()
        assert data["message"] == "Hello, John!"

    def test_hello_endpoint_with_empty_name_returns_default_message(self, client):
        """Test that /hello endpoint returns default message with empty name parameter."""
        response = client.get("/hello?name=")
        data = response.json()
        assert data["message"] == "Hello, World!"

    def test_hello_endpoint_with_name_exceeding_100_chars_returns_400(self, client):
        """Test that /hello endpoint returns 400 for name exceeding 100 characters."""
        long_name = "a" * 101
        response = client.get(f"/hello?name={long_name}")
        assert response.status_code == 400

    def test_hello_endpoint_with_name_exceeding_100_chars_returns_error_message(self, client):
        """Test that /hello endpoint returns proper error message for long name."""
        long_name = "a" * 101
        response = client.get(f"/hello?name={long_name}")
        data = response.json()
        assert data["error"]["code"] == "INVALID_NAME"
        assert "exceeds 100 characters" in data["error"]["message"]

    def test_hello_endpoint_with_special_characters_returns_400(self, client):
        """Test that /hello endpoint returns 400 for name with special characters."""
        response = client.get("/hello?name=John@Doe")
        assert response.status_code == 400

    def test_hello_endpoint_with_special_characters_returns_error_message(self, client):
        """Test that /hello endpoint returns proper error message for invalid characters."""
        response = client.get("/hello?name=John@Doe")
        data = response.json()
        assert data["error"]["code"] == "INVALID_NAME"
        assert "invalid characters" in data["error"]["message"]

    def test_hello_endpoint_with_symbols_returns_400(self, client):
        """Test that /hello endpoint returns 400 for name with symbols."""
        response = client.get("/hello?name=John$")
        assert response.status_code == 400

    def test_hello_endpoint_with_unicode_characters_returns_400(self, client):
        """Test that /hello endpoint returns 400 for name with unicode characters."""
        response = client.get("/hello?name=José")
        assert response.status_code == 400

    def test_hello_endpoint_response_content_type_is_json(self, client):
        """Test that /hello endpoint returns JSON content type."""
        response = client.get("/hello")
        assert "application/json" in response.headers["content-type"]

    def test_hello_endpoint_response_schema_structure(self, client):
        """Test that /hello endpoint response has correct schema structure."""
        response = client.get("/hello")
        data = response.json()
        assert isinstance(data, dict)
        assert "message" in data
        assert isinstance(data["message"], str)
        assert len(data) == 1

    def test_hello_endpoint_with_exactly_100_chars_returns_200(self, client):
        """Test that /hello endpoint accepts name with exactly 100 characters."""
        name_100_chars = "a" * 100
        response = client.get(f"/hello?name={name_100_chars}")
        assert response.status_code == 200

    def test_hello_endpoint_with_exactly_100_chars_returns_personalized_message(self, client):
        """Test that /hello endpoint returns personalized message for 100 character name."""
        name_100_chars = "a" * 100
        response = client.get(f"/hello?name={name_100_chars}")
        data = response.json()
        expected_name = name_100_chars.title()
        assert data["message"] == f"Hello, {expected_name}!"

    def test_hello_endpoint_with_mixed_case_alphanumeric_returns_200(self, client):
        """Test that /hello endpoint handles mixed case alphanumeric names correctly."""
        response = client.get("/hello?name=User123Test")
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "