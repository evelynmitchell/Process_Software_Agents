"""
Comprehensive integration tests for authentication endpoints

Tests registration, login, token refresh, and error scenarios for the authentication API.
Covers happy path, edge cases, and security validation.

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
    """Create test client for FastAPI authentication application."""
    return TestClient(app)


@pytest.fixture
def valid_user_data():
    """Valid user registration data for testing."""
    return {
        "username": "testuser",
        "email": "test@example.com",
        "password": "SecurePass123!"
    }


@pytest.fixture
def valid_login_data():
    """Valid login credentials for testing."""
    return {
        "username": "testuser",
        "password": "SecurePass123!"
    }


@pytest.fixture
def mock_user_db():
    """Mock user database for testing."""
    return {
        "testuser": {
            "username": "testuser",
            "email": "test@example.com",
            "password_hash": "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj3QJgupsqHK",  # SecurePass123!
            "created_at": "2023-01-01T00:00:00Z",
            "is_active": True
        }
    }


class TestRegistrationEndpoint:
    """Test cases for POST /auth/register endpoint."""

    def test_register_valid_user_returns_201(self, client, valid_user_data):
        """Test that registration with valid data returns 201 Created."""
        response = client.post("/auth/register", json=valid_user_data)
        assert response.status_code == 201

    def test_register_valid_user_returns_user_data(self, client, valid_user_data):
        """Test that registration returns user data without password."""
        response = client.post("/auth/register", json=valid_user_data)
        data = response.json()
        
        assert "user" in data
        assert data["user"]["username"] == valid_user_data["username"]
        assert data["user"]["email"] == valid_user_data["email"]
        assert "password" not in data["user"]
        assert "password_hash" not in data["user"]

    def test_register_valid_user_returns_tokens(self, client, valid_user_data):
        """Test that registration returns access and refresh tokens."""
        response = client.post("/auth/register", json=valid_user_data)
        data = response.json()
        
        assert "access_token" in data
        assert "refresh_token" in data
        assert "token_type" in data
        assert data["token_type"] == "bearer"
        assert isinstance(data["access_token"], str)
        assert isinstance(data["refresh_token"], str)
        assert len(data["access_token"]) > 0
        assert len(data["refresh_token"]) > 0

    def test_register_duplicate_username_returns_409(self, client, valid_user_data):
        """Test that registering duplicate username returns 409 Conflict."""
        # Register user first time
        client.post("/auth/register", json=valid_user_data)
        
        # Try to register same username again
        response = client.post("/auth/register", json=valid_user_data)
        assert response.status_code == 409

    def test_register_duplicate_username_returns_error_message(self, client, valid_user_data):
        """Test that duplicate username registration returns proper error message."""
        client.post("/auth/register", json=valid_user_data)
        response = client.post("/auth/register", json=valid_user_data)
        data = response.json()
        
        assert "code" in data
        assert "message" in data
        assert data["code"] == "USERNAME_EXISTS"
        assert "already exists" in data["message"].lower()

    def test_register_duplicate_email_returns_409(self, client, valid_user_data):
        """Test that registering duplicate email returns 409 Conflict."""
        client.post("/auth/register", json=valid_user_data)
        
        # Try different username but same email
        duplicate_email_data = {
            "username": "differentuser",
            "email": valid_user_data["email"],
            "password": "AnotherPass123!"
        }
        response = client.post("/auth/register", json=duplicate_email_data)
        assert response.status_code == 409

    def test_register_invalid_email_format_returns_400(self, client, valid_user_data):
        """Test that invalid email format returns 400 Bad Request."""
        invalid_data = valid_user_data.copy()
        invalid_data["email"] = "invalid-email"
        
        response = client.post("/auth/register", json=invalid_data)
        assert response.status_code == 400

    def test_register_weak_password_returns_400(self, client, valid_user_data):
        """Test that weak password returns 400 Bad Request."""
        weak_password_data = valid_user_data.copy()
        weak_password_data["password"] = "weak"
        
        response = client.post("/auth/register", json=weak_password_data)
        assert response.status_code == 400

    def test_register_short_username_returns_400(self, client, valid_user_data):
        """Test that username shorter than 3 characters returns 400."""
        short_username_data = valid_user_data.copy()
        short_username_data["username"] = "ab"
        
        response = client.post("/auth/register", json=short_username_data)
        assert response.status_code == 400

    def test_register_long_username_returns_400(self, client, valid_user_data):
        """Test that username longer than 50 characters returns 400."""
        long_username_data = valid_user_data.copy()
        long_username_data["username"] = "a" * 51
        
        response = client.post("/auth/register", json=long_username_data)
        assert response.status_code == 400

    def test_register_username_with_special_chars_returns_400(self, client, valid_user_data):
        """Test that username with special characters returns 400."""
        special_char_data = valid_user_data.copy()
        special_char_data["username"] = "user@name!"
        
        response = client.post("/auth/register", json=special_char_data)
        assert response.status_code == 400

    def test_register_missing_required_fields_returns_422(self, client):
        """Test that missing required fields returns 422 Unprocessable Entity."""
        incomplete_data = {"username": "testuser"}
        
        response = client.post("/auth/register", json=incomplete_data)
        assert response.status_code == 422

    def test_register_empty_request_body_returns_422(self, client):
        """Test that empty request body returns 422."""
        response = client.post("/auth/register", json={})
        assert response.status_code == 422

    def test_register_malformed_json_returns_422(self, client):
        """Test that malformed JSON returns 422."""
        response = client.post("/auth/register", data="invalid json")
        assert response.status_code == 422


class TestLoginEndpoint:
    """Test cases for POST /auth/login endpoint."""

    @patch('src.api.auth.user_db')
    def test_login_valid_credentials_returns_200(self, mock_db, client, valid_login_data, mock_user_db):
        """Test that login with valid credentials returns 200