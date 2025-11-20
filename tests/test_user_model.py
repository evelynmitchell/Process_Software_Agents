"""
Unit tests for User model

Tests user model validation, relationships, and database operations including
password hashing, email validation, and user creation/retrieval.

Component ID: COMP-004
Semantic Unit: SU-004

Author: ASP Code Agent
"""

import pytest
from datetime import datetime, timezone
from unittest.mock import Mock, patch
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from src.models.user import User, UserCreate, UserResponse


class TestUserModel:
    """Test cases for User SQLAlchemy model."""

    def test_user_model_creation_with_valid_data(self):
        """Test that User model can be created with valid data."""
        user = User(
            email="test@example.com",
            username="testuser",
            hashed_password="hashed_password_123",
            full_name="Test User"
        )
        
        assert user.email == "test@example.com"
        assert user.username == "testuser"
        assert user.hashed_password == "hashed_password_123"
        assert user.full_name == "Test User"
        assert user.is_active is True
        assert isinstance(user.created_at, datetime)
        assert isinstance(user.updated_at, datetime)

    def test_user_model_creation_with_minimal_data(self):
        """Test that User model can be created with minimal required data."""
        user = User(
            email="minimal@example.com",
            username="minimal",
            hashed_password="hashed_pass"
        )
        
        assert user.email == "minimal@example.com"
        assert user.username == "minimal"
        assert user.hashed_password == "hashed_pass"
        assert user.full_name is None
        assert user.is_active is True

    def test_user_model_string_representation(self):
        """Test User model __str__ method returns username."""
        user = User(
            email="test@example.com",
            username="testuser",
            hashed_password="hashed_password"
        )
        
        assert str(user) == "testuser"

    def test_user_model_repr_representation(self):
        """Test User model __repr__ method returns proper representation."""
        user = User(
            email="test@example.com",
            username="testuser",
            hashed_password="hashed_password"
        )
        user.id = 1
        
        assert repr(user) == "<User(id=1, username='testuser', email='test@example.com')>"

    def test_user_model_timestamps_auto_set(self):
        """Test that created_at and updated_at are automatically set."""
        before_creation = datetime.now(timezone.utc)
        user = User(
            email="timestamp@example.com",
            username="timestamp",
            hashed_password="hashed_password"
        )
        after_creation = datetime.now(timezone.utc)
        
        assert before_creation <= user.created_at <= after_creation
        assert before_creation <= user.updated_at <= after_creation

    def test_user_model_default_is_active_true(self):
        """Test that is_active defaults to True."""
        user = User(
            email="active@example.com",
            username="active",
            hashed_password="hashed_password"
        )
        
        assert user.is_active is True

    def test_user_model_can_set_is_active_false(self):
        """Test that is_active can be set to False."""
        user = User(
            email="inactive@example.com",
            username="inactive",
            hashed_password="hashed_password",
            is_active=False
        )
        
        assert user.is_active is False


class TestUserCreateSchema:
    """Test cases for UserCreate Pydantic schema."""

    def test_user_create_with_valid_data(self):
        """Test UserCreate schema with valid data."""
        user_data = {
            "email": "create@example.com",
            "username": "createuser",
            "password": "securepassword123",
            "full_name": "Create User"
        }
        
        user_create = UserCreate(**user_data)
        
        assert user_create.email == "create@example.com"
        assert user_create.username == "createuser"
        assert user_create.password == "securepassword123"
        assert user_create.full_name == "Create User"

    def test_user_create_with_minimal_data(self):
        """Test UserCreate schema with minimal required data."""
        user_data = {
            "email": "minimal@example.com",
            "username": "minimal",
            "password": "password123"
        }
        
        user_create = UserCreate(**user_data)
        
        assert user_create.email == "minimal@example.com"
        assert user_create.username == "minimal"
        assert user_create.password == "password123"
        assert user_create.full_name is None

    def test_user_create_email_validation_invalid_format(self):
        """Test UserCreate schema rejects invalid email format."""
        user_data = {
            "email": "invalid-email",
            "username": "testuser",
            "password": "password123"
        }
        
        with pytest.raises(ValueError, match="value is not a valid email address"):
            UserCreate(**user_data)

    def test_user_create_email_validation_empty_string(self):
        """Test UserCreate schema rejects empty email."""
        user_data = {
            "email": "",
            "username": "testuser",
            "password": "password123"
        }
        
        with pytest.raises(ValueError):
            UserCreate(**user_data)

    def test_user_create_username_validation_too_short(self):
        """Test UserCreate schema rejects username shorter than 3 characters."""
        user_data = {
            "email": "test@example.com",
            "username": "ab",
            "password": "password123"
        }
        
        with pytest.raises(ValueError, match="String should have at least 3 characters"):
            UserCreate(**user_data)

    def test_user_create_username_validation_too_long(self):
        """Test UserCreate schema rejects username longer than 50 characters."""
        user_data = {
            "email": "test@example.com",
            "username": "a" * 51,
            "password": "password123"
        }
        
        with pytest.raises(ValueError, match="String should have at most 50 characters"):
            UserCreate(**user_data)

    def test_user_create_password_validation_too_short(self):
        """Test UserCreate schema rejects password shorter than 8 characters."""
        user_data = {
            "email": "test@example.com",
            "username": "testuser",
            "password": "short"
        }
        
        with pytest.raises(ValueError, match="String should have at least 8 characters"):
            UserCreate(**user_data)

    def test_user_create_full_name_validation_too_long(self):
        """Test UserCreate schema rejects full_name longer than 100 characters."""
        user_data = {
            "email": "test@example.com",
            "username": "testuser",
            "password": "password123",
            "full_name": "a" * 101
        }
        
        with pytest.raises(ValueError, match="String should have at most 100 characters"):
            UserCreate(**user_data)

    def test_user_create_username_alphanumeric_validation(self):
        """Test UserCreate schema accepts alphanumeric usernames with underscores."""
        valid_usernames = ["user123", "test_user", "User_123", "username"]
        
        for username in valid_usernames:
            user_data = {
                "email": "test@example.com",
                "username": username,
                "password": "password123"
            }