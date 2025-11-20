"""
Comprehensive integration tests for authentication endpoints

Tests registration, login, token validation, and error scenarios for the auth API.

Component ID: COMP-002
Semantic Unit: SU-002

Author: ASP Code Generator
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch
import json
from datetime import datetime, timedelta
import jwt

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
    """Generate a mock JWT token for testing."""
    payload = {
        "sub": "testuser",
        "exp": datetime.utcnow() + timedelta(hours=1),
        "iat": datetime.utcnow()
    }
    return jwt.encode(payload, "test_secret", algorithm="HS256")


@pytest.fixture
def expired_jwt_token():
    """Generate an expired JWT token for testing."""
    payload = {
        "sub": "testuser",
        "exp": datetime.utcnow() - timedelta(hours=1),
        "iat": datetime.utcnow() - timedelta(hours=2)
    }
    return jwt.encode(payload, "test_secret", algorithm="HS256")


class TestUserRegistration:
    """Test cases for user registration endpoint."""

    def test_register_user_success(self, client, mock_user_data):
        """Test successful user registration with valid data."""
        with patch('src.api.auth.create_user') as mock_create:
            mock_create.return_value = {
                "id": 1,
                "username": "testuser",
                "email": "test@example.com",
                "created_at": "2023-01-01T00:00:00Z"
            }
            
            response = client.post("/auth/register", json=mock_user_data)
            
            assert response.status_code == 201
            data = response.json()
            assert data["message"] == "User registered successfully"
            assert "user" in data
            assert data["user"]["username"] == "testuser"
            assert data["user"]["email"] == "test@example.com"
            assert "password" not in data["user"]

    def test_register_user_missing_username(self, client):
        """Test registration fails with missing username."""
        user_data = {
            "email": "test@example.com",
            "password": "SecurePass123!"
        }
        
        response = client.post("/auth/register", json=user_data)
        
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data

    def test_register_user_missing_email(self, client):
        """Test registration fails with missing email."""
        user_data = {
            "username": "testuser",
            "password": "SecurePass123!"
        }
        
        response = client.post("/auth/register", json=user_data)
        
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data

    def test_register_user_missing_password(self, client):
        """Test registration fails with missing password."""
        user_data = {
            "username": "testuser",
            "email": "test@example.com"
        }
        
        response = client.post("/auth/register", json=user_data)
        
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data

    def test_register_user_invalid_email_format(self, client):
        """Test registration fails with invalid email format."""
        user_data = {
            "username": "testuser",
            "email": "invalid-email",
            "password": "SecurePass123!"
        }
        
        response = client.post("/auth/register", json=user_data)
        
        assert response.status_code == 400
        data = response.json()
        assert data["error"]["code"] == "INVALID_EMAIL"
        assert "Invalid email format" in data["error"]["message"]

    def test_register_user_weak_password(self, client):
        """Test registration fails with weak password."""
        user_data = {
            "username": "testuser",
            "email": "test@example.com",
            "password": "weak"
        }
        
        response = client.post("/auth/register", json=user_data)
        
        assert response.status_code == 400
        data = response.json()
        assert data["error"]["code"] == "WEAK_PASSWORD"
        assert "Password must be at least 8 characters" in data["error"]["message"]

    def test_register_user_duplicate_username(self, client, mock_user_data):
        """Test registration fails with duplicate username."""
        with patch('src.api.auth.create_user') as mock_create:
            mock_create.side_effect = ValueError("Username already exists")
            
            response = client.post("/auth/register", json=mock_user_data)
            
            assert response.status_code == 409
            data = response.json()
            assert data["error"]["code"] == "USER_EXISTS"
            assert "Username already exists" in data["error"]["message"]

    def test_register_user_duplicate_email(self, client, mock_user_data):
        """Test registration fails with duplicate email."""
        with patch('src.api.auth.create_user') as mock_create:
            mock_create.side_effect = ValueError("Email already exists")
            
            response = client.post("/auth/register", json=mock_user_data)
            
            assert response.status_code == 409
            data = response.json()
            assert data["error"]["code"] == "USER_EXISTS"
            assert "Email already exists" in data["error"]["message"]

    def test_register_user_empty_request_body(self, client):
        """Test registration fails with empty request body."""
        response = client.post("/auth/register", json={})
        
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data

    def test_register_user_malformed_json(self, client):
        """Test registration fails with malformed JSON."""
        response = client.post(
            "/auth/register",
            data="invalid json",
            headers={"Content-Type": "application/json"}
        )
        
        assert response.status_code == 422

    def test_register_user_database_error(self, client, mock_user_data):
        """Test registration handles database errors gracefully."""
        with patch('src.api.auth.create_user') as mock_create:
            mock_create.side_effect = Exception("Database connection failed")
            
            response = client.post("/auth/register", json=mock_user_data)
            
            assert response.status_code == 500
            data = response.json()
            assert data["error"]["code"] == "INTERNAL_ERROR"
            assert "Internal server error" in data["error"]["message"]


class TestUserLogin:
    """Test cases for user login endpoint."""

    def test_login_user_success(self, client, mock_login_data, mock_jwt_token):
        """Test successful user login with valid credentials."""
        with patch('src.api.auth.authenticate_user') as mock_auth, \
             patch('src.api.auth.create_access_token') as mock_token:
            
            mock_auth.return_value = {
                "id": 1,
                "username": "testuser",
                "email": "test@example.