"""
Unit tests for User model operations, validation, and database relationships.

Tests user creation, validation, authentication, and database operations
including relationships with other models.

Component ID: COMP-004
Semantic Unit: SU-004

Author: ASP Code Agent
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session
from passlib.context import CryptContext

from src.models.user import User, UserCreate, UserUpdate, UserResponse


class TestUserModel:
    """Test cases for User model class."""

    def test_user_model_creation_with_valid_data(self):
        """Test that User model can be created with valid data."""
        user = User(
            username="testuser",
            email="test@example.com",
            hashed_password="hashed_password_123",
            full_name="Test User"
        )
        
        assert user.username == "testuser"
        assert user.email == "test@example.com"
        assert user.hashed_password == "hashed_password_123"
        assert user.full_name == "Test User"
        assert user.is_active is True
        assert user.is_superuser is False
        assert isinstance(user.created_at, datetime)
        assert isinstance(user.updated_at, datetime)

    def test_user_model_creation_with_minimal_data(self):
        """Test that User model can be created with minimal required data."""
        user = User(
            username="minimaluser",
            email="minimal@example.com",
            hashed_password="hashed_password_456"
        )
        
        assert user.username == "minimaluser"
        assert user.email == "minimal@example.com"
        assert user.hashed_password == "hashed_password_456"
        assert user.full_name is None
        assert user.is_active is True
        assert user.is_superuser is False

    def test_user_model_string_representation(self):
        """Test that User model has proper string representation."""
        user = User(
            username="repruser",
            email="repr@example.com",
            hashed_password="hashed_password_789"
        )
        
        assert str(user) == "repruser"
        assert repr(user) == "<User(username='repruser', email='repr@example.com')>"

    def test_user_model_timestamps_auto_update(self):
        """Test that timestamps are automatically set and updated."""
        user = User(
            username="timeuser",
            email="time@example.com",
            hashed_password="hashed_password_time"
        )
        
        original_created = user.created_at
        original_updated = user.updated_at
        
        # Simulate update
        user.full_name = "Updated Name"
        user.updated_at = datetime.utcnow()
        
        assert user.created_at == original_created
        assert user.updated_at > original_updated

    def test_user_model_password_verification(self):
        """Test password verification functionality."""
        user = User(
            username="passuser",
            email="pass@example.com",
            hashed_password="$2b$12$test_hashed_password"
        )
        
        with patch('passlib.context.CryptContext.verify') as mock_verify:
            mock_verify.return_value = True
            assert user.verify_password("correct_password") is True
            
            mock_verify.return_value = False
            assert user.verify_password("wrong_password") is False

    def test_user_model_password_hashing(self):
        """Test password hashing functionality."""
        with patch('passlib.context.CryptContext.hash') as mock_hash:
            mock_hash.return_value = "$2b$12$hashed_test_password"
            
            user = User(
                username="hashuser",
                email="hash@example.com"
            )
            user.set_password("plain_password")
            
            assert user.hashed_password == "$2b$12$hashed_test_password"
            mock_hash.assert_called_once_with("plain_password")


class TestUserCreate:
    """Test cases for UserCreate Pydantic model."""

    def test_user_create_with_valid_data(self):
        """Test UserCreate model with valid data."""
        user_data = {
            "username": "newuser",
            "email": "new@example.com",
            "password": "securepassword123",
            "full_name": "New User"
        }
        
        user_create = UserCreate(**user_data)
        
        assert user_create.username == "newuser"
        assert user_create.email == "new@example.com"
        assert user_create.password == "securepassword123"
        assert user_create.full_name == "New User"

    def test_user_create_with_minimal_data(self):
        """Test UserCreate model with minimal required data."""
        user_data = {
            "username": "minuser",
            "email": "min@example.com",
            "password": "password123"
        }
        
        user_create = UserCreate(**user_data)
        
        assert user_create.username == "minuser"
        assert user_create.email == "min@example.com"
        assert user_create.password == "password123"
        assert user_create.full_name is None

    def test_user_create_username_validation(self):
        """Test username validation in UserCreate model."""
        # Valid username
        valid_data = {
            "username": "validuser123",
            "email": "valid@example.com",
            "password": "password123"
        }
        user_create = UserCreate(**valid_data)
        assert user_create.username == "validuser123"

        # Invalid username - too short
        with pytest.raises(ValueError, match="Username must be at least 3 characters"):
            UserCreate(username="ab", email="test@example.com", password="password123")

        # Invalid username - too long
        with pytest.raises(ValueError, match="Username must be at most 50 characters"):
            UserCreate(username="a" * 51, email="test@example.com", password="password123")

        # Invalid username - invalid characters
        with pytest.raises(ValueError, match="Username can only contain letters, numbers, and underscores"):
            UserCreate(username="user@name", email="test@example.com", password="password123")

    def test_user_create_email_validation(self):
        """Test email validation in UserCreate model."""
        # Valid email
        valid_data = {
            "username": "testuser",
            "email": "valid.email@example.com",
            "password": "password123"
        }
        user_create = UserCreate(**valid_data)
        assert user_create.email == "valid.email@example.com"

        # Invalid email format
        with pytest.raises(ValueError, match="Invalid email format"):
            UserCreate(username="testuser", email="invalid-email", password="password123")

        # Empty email
        with pytest.raises(ValueError, match="Email is required"):
            UserCreate(username="testuser", email="", password="password123")

    def test_user_create_password_validation(self):
        """Test password validation in UserCreate model."""
        # Valid password
        valid_data = {
            "username": "testuser",
            "email": "test@example.com",
            "password": "securepassword123"
        }
        user_create = UserCreate(**valid_data)
        assert user_create.password == "securepassword123"

        # Invalid password - too short
        with pytest.raises(ValueError, match="Password must be at least 8 characters"):
            UserCreate(username="testuser", email="test@example.com", password="short")

        # Invalid password - too long
        with pytest.raises(ValueError, match="Password must be at most 128 characters"):