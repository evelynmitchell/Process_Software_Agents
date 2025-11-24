"""
Comprehensive integration tests for authentication endpoints

Tests authentication API endpoints including success cases, validation errors,
and security scenarios for user registration, login, and token validation.

Component ID: COMP-002
Semantic Unit: SU-002

Author: ASP Code Agent
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch
import json
from datetime import datetime, timedelta
import jwt
from passlib.context import CryptContext

from src.api.auth import app, get_password_hash, verify_password, create_access_token, verify_token


@pytest.fixture
def client():
    """Create test client for FastAPI authentication application."""
    return TestClient(app)


@pytest.fixture
def mock_user_data():
    """Mock user data for testing."""
    return {
        "username": "testuser",
        "email": "test@example.com",
        "password": "SecurePass123!"
    }


@pytest.fixture
def mock_login_data():
    """Mock login data for testing."""
    return {
        "username": "testuser",
        "password": "SecurePass123!"
    }


@pytest.fixture
def mock_invalid_user_data():
    """Mock invalid user data for testing validation."""
    return {
        "username": "ab",  # Too short
        "email": "invalid-email",  # Invalid format
        "password": "123"  # Too weak
    }


@pytest.fixture
def mock_database():
    """Mock database for testing."""
    return {
        "users": {
            "testuser": {
                "username": "testuser",
                "email": "test@example.com",
                "hashed_password": get_password_hash("SecurePass123!"),
                "created_at": datetime.utcnow().isoformat()
            }
        }
    }


@pytest.fixture
def valid_token():
    """Create a valid JWT token for testing."""
    return create_access_token(data={"sub": "testuser"})


@pytest.fixture
def expired_token():
    """Create an expired JWT token for testing."""
    return create_access_token(
        data={"sub": "testuser"}, 
        expires_delta=timedelta(minutes=-1)
    )


class TestUserRegistration:
    """Test cases for user registration endpoint."""

    def test_register_user_success(self, client, mock_user_data):
        """Test successful user registration returns 201 and user data."""
        with patch('src.api.auth.save_user_to_database') as mock_save:
            mock_save.return_value = True
            
            response = client.post("/auth/register", json=mock_user_data)
            
            assert response.status_code == 201
            data = response.json()
            assert "user_id" in data
            assert data["username"] == mock_user_data["username"]
            assert data["email"] == mock_user_data["email"]
            assert "password" not in data
            assert "hashed_password" not in data
            assert "created_at" in data

    def test_register_user_duplicate_username(self, client, mock_user_data):
        """Test registration with duplicate username returns 409 conflict."""
        with patch('src.api.auth.user_exists') as mock_exists:
            mock_exists.return_value = True
            
            response = client.post("/auth/register", json=mock_user_data)
            
            assert response.status_code == 409
            data = response.json()
            assert data["error"] == "USER_EXISTS"
            assert "already exists" in data["message"].lower()

    def test_register_user_invalid_username_too_short(self, client):
        """Test registration with username too short returns 400."""
        user_data = {
            "username": "ab",
            "email": "test@example.com",
            "password": "SecurePass123!"
        }
        
        response = client.post("/auth/register", json=user_data)
        
        assert response.status_code == 400
        data = response.json()
        assert data["error"] == "VALIDATION_ERROR"
        assert "username" in data["message"].lower()

    def test_register_user_invalid_username_too_long(self, client):
        """Test registration with username too long returns 400."""
        user_data = {
            "username": "a" * 51,  # 51 characters
            "email": "test@example.com",
            "password": "SecurePass123!"
        }
        
        response = client.post("/auth/register", json=user_data)
        
        assert response.status_code == 400
        data = response.json()
        assert data["error"] == "VALIDATION_ERROR"
        assert "username" in data["message"].lower()

    def test_register_user_invalid_username_special_chars(self, client):
        """Test registration with invalid username characters returns 400."""
        user_data = {
            "username": "test@user",
            "email": "test@example.com",
            "password": "SecurePass123!"
        }
        
        response = client.post("/auth/register", json=user_data)
        
        assert response.status_code == 400
        data = response.json()
        assert data["error"] == "VALIDATION_ERROR"
        assert "username" in data["message"].lower()

    def test_register_user_invalid_email_format(self, client):
        """Test registration with invalid email format returns 400."""
        user_data = {
            "username": "testuser",
            "email": "invalid-email",
            "password": "SecurePass123!"
        }
        
        response = client.post("/auth/register", json=user_data)
        
        assert response.status_code == 400
        data = response.json()
        assert data["error"] == "VALIDATION_ERROR"
        assert "email" in data["message"].lower()

    def test_register_user_invalid_password_too_short(self, client):
        """Test registration with password too short returns 400."""
        user_data = {
            "username": "testuser",
            "email": "test@example.com",
            "password": "123"
        }
        
        response = client.post("/auth/register", json=user_data)
        
        assert response.status_code == 400
        data = response.json()
        assert data["error"] == "VALIDATION_ERROR"
        assert "password" in data["message"].lower()

    def test_register_user_invalid_password_no_uppercase(self, client):
        """Test registration with password missing uppercase returns 400."""
        user_data = {
            "username": "testuser",
            "email": "test@example.com",
            "password": "securepass123!"
        }
        
        response = client.post("/auth/register", json=user_data)
        
        assert response.status_code == 400
        data = response.json()
        assert data["error"] == "VALIDATION_ERROR"
        assert "password" in data["message"].lower()

    def test_register_user_invalid_password_no_lowercase(self, client):
        """Test registration with password missing lowercase returns 400."""
        user_data = {
            "username": "testuser",
            "email": "test@example.com",
            "password": "SECUREPASS123!"
        }
        
        response = client.post("/auth/register", json=user_data)
        
        assert response.status_code == 400
        data = response.json()
        assert data["error"] == "VALIDATION_ERROR"
        assert "password" in data["message"].lower()

    def test_register_user_invalid_password_no_digit(self, client):
        """Test registration with password missing digit returns 400."""
        user_data = {
            "username": "testuser",
            "email": "test@example.com",
            "password": "SecurePass!"
        }
        
        response = client.post("/auth/register", json=user_data)