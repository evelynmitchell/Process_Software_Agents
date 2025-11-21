"""
Unit tests for User model including validation, relationships, and database operations.

Tests the User model to verify field validation, password hashing, database operations,
and relationships with other models.

Semantic Unit ID: SU-004
Component ID: COMP-004

Author: ASP Code Agent
"""

import pytest
from datetime import datetime, timezone
from unittest.mock import Mock, patch
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from src.models.user import User
from tests.conftest import TestSession


class TestUserModel:
    """Test suite for User model basic functionality."""

    def test_user_creation_with_valid_data(self, db_session: TestSession):
        """Test that User can be created with valid data."""
        user = User(
            username="testuser",
            email="test@example.com",
            password_hash="hashed_password_123"
        )
        
        assert user.username == "testuser"
        assert user.email == "test@example.com"
        assert user.password_hash == "hashed_password_123"
        assert user.is_active is True  # Default value
        assert user.created_at is not None
        assert user.updated_at is not None

    def test_user_creation_sets_timestamps(self, db_session: TestSession):
        """Test that User creation automatically sets created_at and updated_at."""
        before_creation = datetime.now(timezone.utc)
        
        user = User(
            username="testuser",
            email="test@example.com",
            password_hash="hashed_password_123"
        )
        
        after_creation = datetime.now(timezone.utc)
        
        assert before_creation <= user.created_at <= after_creation
        assert before_creation <= user.updated_at <= after_creation
        assert user.created_at == user.updated_at

    def test_user_str_representation(self, db_session: TestSession):
        """Test that User string representation returns username."""
        user = User(
            username="testuser",
            email="test@example.com",
            password_hash="hashed_password_123"
        )
        
        assert str(user) == "testuser"

    def test_user_repr_representation(self, db_session: TestSession):
        """Test that User repr representation includes id and username."""
        user = User(
            id=123,
            username="testuser",
            email="test@example.com",
            password_hash="hashed_password_123"
        )
        
        assert repr(user) == "<User(id=123, username='testuser')>"


class TestUserValidation:
    """Test suite for User model field validation."""

    def test_username_required(self, db_session: TestSession):
        """Test that username is required."""
        with pytest.raises(ValueError, match="Username is required"):
            User(
                username=None,
                email="test@example.com",
                password_hash="hashed_password_123"
            )

    def test_username_empty_string_invalid(self, db_session: TestSession):
        """Test that empty username string is invalid."""
        with pytest.raises(ValueError, match="Username cannot be empty"):
            User(
                username="",
                email="test@example.com",
                password_hash="hashed_password_123"
            )

    def test_username_whitespace_only_invalid(self, db_session: TestSession):
        """Test that whitespace-only username is invalid."""
        with pytest.raises(ValueError, match="Username cannot be empty"):
            User(
                username="   ",
                email="test@example.com",
                password_hash="hashed_password_123"
            )

    def test_username_too_long_invalid(self, db_session: TestSession):
        """Test that username longer than 50 characters is invalid."""
        long_username = "a" * 51
        
        with pytest.raises(ValueError, match="Username must be 50 characters or less"):
            User(
                username=long_username,
                email="test@example.com",
                password_hash="hashed_password_123"
            )

    def test_username_max_length_valid(self, db_session: TestSession):
        """Test that username with exactly 50 characters is valid."""
        max_username = "a" * 50
        
        user = User(
            username=max_username,
            email="test@example.com",
            password_hash="hashed_password_123"
        )
        
        assert user.username == max_username

    def test_email_required(self, db_session: TestSession):
        """Test that email is required."""
        with pytest.raises(ValueError, match="Email is required"):
            User(
                username="testuser",
                email=None,
                password_hash="hashed_password_123"
            )

    def test_email_empty_string_invalid(self, db_session: TestSession):
        """Test that empty email string is invalid."""
        with pytest.raises(ValueError, match="Email cannot be empty"):
            User(
                username="testuser",
                email="",
                password_hash="hashed_password_123"
            )

    def test_email_invalid_format(self, db_session: TestSession):
        """Test that invalid email format raises ValueError."""
        invalid_emails = [
            "invalid_email",
            "@example.com",
            "test@",
            "test.example.com",
            "test@.com",
            "test@example.",
            "test space@example.com"
        ]
        
        for invalid_email in invalid_emails:
            with pytest.raises(ValueError, match="Invalid email format"):
                User(
                    username="testuser",
                    email=invalid_email,
                    password_hash="hashed_password_123"
                )

    def test_email_valid_formats(self, db_session: TestSession):
        """Test that valid email formats are accepted."""
        valid_emails = [
            "test@example.com",
            "user.name@example.com",
            "user+tag@example.co.uk",
            "123@example.org",
            "test@sub.example.com"
        ]
        
        for valid_email in valid_emails:
            user = User(
                username=f"user_{valid_email.replace('@', '_').replace('.', '_')}",
                email=valid_email,
                password_hash="hashed_password_123"
            )
            assert user.email == valid_email

    def test_email_too_long_invalid(self, db_session: TestSession):
        """Test that email longer than 255 characters is invalid."""
        long_email = "a" * 240 + "@example.com"  # 252 chars total
        
        user = User(
            username="testuser",
            email=long_email,
            password_hash="hashed_password_123"
        )
        assert user.email == long_email
        
        # Test email that's too long
        too_long_email = "a" * 250 + "@example.com"  # 262 chars total
        with pytest.raises(ValueError, match="Email must be 255 characters or less"):
            User(
                username="testuser",
                email=too_long_email,
                password_hash="hashed_password_123"
            )

    def test_password_hash_required(self, db_session: TestSession):
        """Test that password_hash is required."""
        with pytest.raises(ValueError, match="Password hash is required"):
            User(
                username="testuser",
                email="test@example.com",
                password_hash=None
            )

    def test_password_hash_empty_string_invalid(self, db_session: TestSession):
        """Test that empty password_hash string is invalid."""
        with pytest.raises(ValueError, match="Password hash cannot be empty"):
            User(
                username="testuser",
                email="test@example.com",
                password_hash=""
            )


class TestUserDatabaseOperations:
    """Test suite for User model database operations