"""
Comprehensive integration tests for authentication endpoints

Tests authentication API endpoints including edge cases, error scenarios,
and security validation for the Hello World API.

Component ID: COMP-002
Semantic Unit: SU-002

Author: ASP Code Agent
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from datetime import datetime
import json
import re

from src.api.auth import app


@pytest.fixture
def client():
    """Create test client for FastAPI application."""
    return TestClient(app)


class TestHelloEndpoint:
    """Test suite for /hello endpoint functionality."""

    def test_hello_endpoint_returns_200_without_name(self, client):
        """Test that /hello endpoint returns 200 OK status without name parameter."""
        response = client.get("/hello")
        assert response.status_code == 200

    def test_hello_endpoint_returns_200_with_valid_name(self, client):
        """Test that /hello endpoint returns 200 OK status with valid name parameter."""
        response = client.get("/hello?name=John")
        assert response.status_code == 200

    def test_hello_endpoint_returns_json_content_type(self, client):
        """Test that /hello endpoint returns JSON content type."""
        response = client.get("/hello")
        assert response.headers["content-type"] == "application/json"

    def test_hello_endpoint_default_message_without_name(self, client):
        """Test that /hello endpoint returns default message when no name provided."""
        response = client.get("/hello")
        data = response.json()
        assert data["message"] == "Hello, World!"

    def test_hello_endpoint_personalized_message_with_name(self, client):
        """Test that /hello endpoint returns personalized message with name parameter."""
        response = client.get("/hello?name=Alice")
        data = response.json()
        assert data["message"] == "Hello, Alice!"

    def test_hello_endpoint_response_schema_structure(self, client):
        """Test that /hello endpoint response matches expected schema structure."""
        response = client.get("/hello")
        data = response.json()
        assert isinstance(data, dict)
        assert "message" in data
        assert isinstance(data["message"], str)
        assert len(data) == 1

    def test_hello_endpoint_name_with_spaces(self, client):
        """Test that /hello endpoint handles names with spaces correctly."""
        response = client.get("/hello?name=John Doe")
        data = response.json()
        assert data["message"] == "Hello, John Doe!"

    def test_hello_endpoint_name_with_numbers(self, client):
        """Test that /hello endpoint handles names with numbers correctly."""
        response = client.get("/hello?name=User123")
        data = response.json()
        assert data["message"] == "Hello, User123!"

    def test_hello_endpoint_name_case_sensitivity(self, client):
        """Test that /hello endpoint preserves name case correctly."""
        response = client.get("/hello?name=mIxEdCaSe")
        data = response.json()
        assert data["message"] == "Hello, Mixedcase!"

    def test_hello_endpoint_name_with_leading_trailing_spaces(self, client):
        """Test that /hello endpoint trims leading and trailing spaces from name."""
        response = client.get("/hello?name=  John  ")
        data = response.json()
        assert data["message"] == "Hello, John!"

    def test_hello_endpoint_empty_name_parameter(self, client):
        """Test that /hello endpoint handles empty name parameter."""
        response = client.get("/hello?name=")
        assert response.status_code == 400
        data = response.json()
        assert data["code"] == "INVALID_NAME"

    def test_hello_endpoint_name_with_special_characters_returns_400(self, client):
        """Test that /hello endpoint returns 400 for name with special characters."""
        response = client.get("/hello?name=John@Doe")
        assert response.status_code == 400
        data = response.json()
        assert data["code"] == "INVALID_NAME"
        assert "invalid characters" in data["message"]

    def test_hello_endpoint_name_with_symbols_returns_400(self, client):
        """Test that /hello endpoint returns 400 for name with symbols."""
        response = client.get("/hello?name=John$Smith")
        assert response.status_code == 400
        data = response.json()
        assert data["code"] == "INVALID_NAME"

    def test_hello_endpoint_name_with_punctuation_returns_400(self, client):
        """Test that /hello endpoint returns 400 for name with punctuation."""
        response = client.get("/hello?name=John.Doe")
        assert response.status_code == 400
        data = response.json()
        assert data["code"] == "INVALID_NAME"

    def test_hello_endpoint_name_exceeding_max_length_returns_400(self, client):
        """Test that /hello endpoint returns 400 for name exceeding 100 characters."""
        long_name = "a" * 101
        response = client.get(f"/hello?name={long_name}")
        assert response.status_code == 400
        data = response.json()
        assert data["code"] == "INVALID_NAME"
        assert "exceeds 100 characters" in data["message"]

    def test_hello_endpoint_name_exactly_100_characters(self, client):
        """Test that /hello endpoint accepts name with exactly 100 characters."""
        name_100_chars = "a" * 100
        response = client.get(f"/hello?name={name_100_chars}")
        assert response.status_code == 200
        data = response.json()
        expected_name = name_100_chars.title()
        assert data["message"] == f"Hello, {expected_name}!"

    def test_hello_endpoint_name_with_unicode_characters_returns_400(self, client):
        """Test that /hello endpoint returns 400 for name with unicode characters."""
        response = client.get("/hello?name=José")
        assert response.status_code == 400
        data = response.json()
        assert data["code"] == "INVALID_NAME"

    def test_hello_endpoint_name_with_newlines_returns_400(self, client):
        """Test that /hello endpoint returns 400 for name with newline characters."""
        response = client.get("/hello?name=John\nDoe")
        assert response.status_code == 400
        data = response.json()
        assert data["code"] == "INVALID_NAME"

    def test_hello_endpoint_name_with_tabs_returns_400(self, client):
        """Test that /hello endpoint returns 400 for name with tab characters."""
        response = client.get("/hello?name=John\tDoe")
        assert response.status_code == 400
        data = response.json()
        assert data["code"] == "INVALID_NAME"

    def test_hello_endpoint_multiple_name_parameters(self, client):
        """Test that /hello endpoint handles multiple name parameters correctly."""
        response = client.get("/hello?name=John&name=Jane")
        # FastAPI takes the last parameter value
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Hello, Jane!"

    def test_hello_endpoint_sql_injection_attempt_returns_400(self, client):
        """Test that /hello endpoint rejects SQL injection attempts."""
        response = client.get("/hello?name='; DROP TABLE users; --")
        assert response.status_code == 400
        data = response.json()
        assert data["code"] == "INVALID_NAME"

    def test_hello_endpoint_xss_attempt_returns_400(self, client):
        """Test that /hello endpoint rejects XSS attempts."""
        response = client.get("/hello?name=<script>alert('xss')</script>")
        assert