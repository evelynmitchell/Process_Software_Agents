"""
Comprehensive integration tests for authentication endpoints

Tests all authentication endpoints including edge cases, error scenarios,
and security validation for the Hello World API.

Component ID: COMP-002
Semantic Unit: SU-002

Author: ASP Code Agent
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
import json
from datetime import datetime
import re

from src.api.auth import app


@pytest.fixture
def client():
    """Create test client for FastAPI application."""
    return TestClient(app)


class TestHelloEndpoint:
    """Test suite for GET /hello endpoint."""

    def test_hello_endpoint_returns_200_without_name(self, client):
        """Test that /hello endpoint returns 200 OK status without name parameter."""
        response = client.get("/hello")
        assert response.status_code == 200

    def test_hello_endpoint_returns_json_content_type(self, client):
        """Test that /hello endpoint returns JSON content type."""
        response = client.get("/hello")
        assert "application/json" in response.headers["content-type"]

    def test_hello_endpoint_default_message(self, client):
        """Test that /hello endpoint returns default message without name parameter."""
        response = client.get("/hello")
        data = response.json()
        assert data["message"] == "Hello, World!"

    def test_hello_endpoint_with_valid_name(self, client):
        """Test that /hello endpoint returns personalized message with valid name."""
        response = client.get("/hello?name=John")
        data = response.json()
        assert data["message"] == "Hello, John!"

    def test_hello_endpoint_with_name_containing_spaces(self, client):
        """Test that /hello endpoint accepts names with spaces."""
        response = client.get("/hello?name=John Doe")
        data = response.json()
        assert response.status_code == 200
        assert data["message"] == "Hello, John Doe!"

    def test_hello_endpoint_with_name_containing_numbers(self, client):
        """Test that /hello endpoint accepts names with numbers."""
        response = client.get("/hello?name=User123")
        data = response.json()
        assert response.status_code == 200
        assert data["message"] == "Hello, User123!"

    def test_hello_endpoint_with_mixed_alphanumeric_name(self, client):
        """Test that /hello endpoint accepts mixed alphanumeric names with spaces."""
        response = client.get("/hello?name=John Doe 123")
        data = response.json()
        assert response.status_code == 200
        assert data["message"] == "Hello, John Doe 123!"

    def test_hello_endpoint_with_empty_name(self, client):
        """Test that /hello endpoint returns default message with empty name."""
        response = client.get("/hello?name=")
        data = response.json()
        assert response.status_code == 200
        assert data["message"] == "Hello, World!"

    def test_hello_endpoint_with_whitespace_only_name(self, client):
        """Test that /hello endpoint handles whitespace-only name."""
        response = client.get("/hello?name=   ")
        data = response.json()
        assert response.status_code == 200
        assert data["message"] == "Hello,    !"

    def test_hello_endpoint_name_max_length_valid(self, client):
        """Test that /hello endpoint accepts name at maximum length (100 chars)."""
        name = "a" * 100
        response = client.get(f"/hello?name={name}")
        data = response.json()
        assert response.status_code == 200
        assert data["message"] == f"Hello, {name}!"

    def test_hello_endpoint_name_exceeds_max_length(self, client):
        """Test that /hello endpoint returns 400 for name exceeding 100 characters."""
        name = "a" * 101
        response = client.get(f"/hello?name={name}")
        assert response.status_code == 400
        data = response.json()
        assert data["error"]["code"] == "INVALID_NAME"
        assert "exceeds 100 characters" in data["error"]["message"]

    def test_hello_endpoint_name_with_special_characters(self, client):
        """Test that /hello endpoint returns 400 for name with special characters."""
        response = client.get("/hello?name=John@Doe")
        assert response.status_code == 400
        data = response.json()
        assert data["error"]["code"] == "INVALID_NAME"
        assert "invalid characters" in data["error"]["message"]

    def test_hello_endpoint_name_with_symbols(self, client):
        """Test that /hello endpoint returns 400 for name with symbols."""
        response = client.get("/hello?name=John#Doe$")
        assert response.status_code == 400
        data = response.json()
        assert data["error"]["code"] == "INVALID_NAME"

    def test_hello_endpoint_name_with_punctuation(self, client):
        """Test that /hello endpoint returns 400 for name with punctuation."""
        response = client.get("/hello?name=John.Doe")
        assert response.status_code == 400
        data = response.json()
        assert data["error"]["code"] == "INVALID_NAME"

    def test_hello_endpoint_name_with_newlines(self, client):
        """Test that /hello endpoint returns 400 for name with newlines."""
        response = client.get("/hello?name=John\nDoe")
        assert response.status_code == 400
        data = response.json()
        assert data["error"]["code"] == "INVALID_NAME"

    def test_hello_endpoint_name_with_tabs(self, client):
        """Test that /hello endpoint returns 400 for name with tabs."""
        response = client.get("/hello?name=John\tDoe")
        assert response.status_code == 400
        data = response.json()
        assert data["error"]["code"] == "INVALID_NAME"

    def test_hello_endpoint_name_with_unicode_characters(self, client):
        """Test that /hello endpoint returns 400 for name with unicode characters."""
        response = client.get("/hello?name=Jöhn")
        assert response.status_code == 400
        data = response.json()
        assert data["error"]["code"] == "INVALID_NAME"

    def test_hello_endpoint_response_schema_structure(self, client):
        """Test that /hello endpoint response has correct schema structure."""
        response = client.get("/hello")
        data = response.json()
        assert isinstance(data, dict)
        assert "message" in data
        assert isinstance(data["message"], str)
        assert len(data) == 1

    def test_hello_endpoint_response_schema_with_name(self, client):
        """Test that /hello endpoint response schema is correct with name parameter."""
        response = client.get("/hello?name=Test")
        data = response.json()
        assert isinstance(data, dict)
        assert "message" in data
        assert isinstance(data["message"], str)
        assert len(data) == 1

    def test_hello_endpoint_error_response_schema(self, client):
        """Test that /hello endpoint error response has correct schema structure."""
        response = client.get("/hello?name=Invalid@Name")
        data = response.json()
        assert isinstance(data, dict)
        assert "error" in data
        assert isinstance(data["error"], dict)
        assert "code" in data["error"]
        assert "message" in data["error"]
        assert isinstance(data["error"]["code"], str)
        assert isinstance(data["error"]["message"], str)

    def test_hello_endpoint_case_sensitivity(self, client):
        """Test that /hello endpoint preserves case in name parameter."""
        response = client.get("/hello?name=JoHn DoE")
        data = response.json()
        assert response.status_code == 200