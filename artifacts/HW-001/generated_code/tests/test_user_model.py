"""
Unit tests for User model including field validation, relationships, and database operations.

Tests the User model to verify field validation, database constraints, relationships,
and CRUD operations work correctly.

Semantic Unit: SU-004
Component: COMP-004

Author: ASP Code Agent
"""

import pytest
from datetime import datetime, timezone
from unittest.mock import Mock, patch
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from src.models.user import User, UserRole, UserStatus
from tests.conftest import TestSession


class TestUserModel:
    """Test suite for User model basic functionality."""

    def test_user_creation_with_required_fields(self, db_session: TestSession):
        """Test that User can be created with only required fields."""
        user = User(
            username="testuser",
            email="test@example.com",
            password_hash="hashed_password_123"
        )
        
        db_session.add(user)
        db_session.commit()
        
        assert user.id is not None
        assert user.username == "testuser"
        assert user.email == "test@example.com"
        assert user.password_hash == "hashed_password_123"
        assert user.role == UserRole.USER  # Default role
        assert user.status == UserStatus.ACTIVE  # Default status
        assert user.created_at is not None
        assert user.updated_at is not None
        assert user.last_login is None
        assert user.first_name is None
        assert user.last_name is None

    def test_user_creation_with_all_fields(self, db_session: TestSession):
        """Test that User can be created with all fields populated."""
        now = datetime.now(timezone.utc)
        
        user = User(
            username="fulluser",
            email="full@example.com",
            password_hash="hashed_password_456",
            first_name="John",
            last_name="Doe",
            role=UserRole.ADMIN,
            status=UserStatus.INACTIVE,
            last_login=now
        )
        
        db_session.add(user)
        db_session.commit()
        
        assert user.username == "fulluser"
        assert user.email == "full@example.com"
        assert user.first_name == "John"
        assert user.last_name == "Doe"
        assert user.role == UserRole.ADMIN
        assert user.status == UserStatus.INACTIVE
        assert user.last_login == now

    def test_user_string_representation(self, db_session: TestSession):
        """Test that User __str__ method returns expected format."""
        user = User(
            username="repruser",
            email="repr@example.com",
            password_hash="hashed_password_789"
        )
        
        expected = "User(id=None, username='repruser', email='repr@example.com')"
        assert str(user) == expected

    def test_user_repr_representation(self, db_session: TestSession):
        """Test that User __repr__ method returns expected format."""
        user = User(
            username="repruser",
            email="repr@example.com",
            password_hash="hashed_password_789"
        )
        
        expected = "User(id=None, username='repruser', email='repr@example.com')"
        assert repr(user) == expected


class TestUserValidation:
    """Test suite for User model field validation."""

    def test_username_required(self, db_session: TestSession):
        """Test that username is required and cannot be None."""
        user = User(
            username=None,
            email="test@example.com",
            password_hash="hashed_password"
        )
        
        db_session.add(user)
        
        with pytest.raises(IntegrityError):
            db_session.commit()

    def test_username_cannot_be_empty(self, db_session: TestSession):
        """Test that username cannot be empty string."""
        user = User(
            username="",
            email="test@example.com",
            password_hash="hashed_password"
        )
        
        db_session.add(user)
        
        with pytest.raises(IntegrityError):
            db_session.commit()

    def test_username_max_length(self, db_session: TestSession):
        """Test that username cannot exceed maximum length of 50 characters."""
        long_username = "a" * 51  # 51 characters
        
        user = User(
            username=long_username,
            email="test@example.com",
            password_hash="hashed_password"
        )
        
        db_session.add(user)
        
        with pytest.raises(IntegrityError):
            db_session.commit()

    def test_username_valid_length(self, db_session: TestSession):
        """Test that username with valid length is accepted."""
        valid_username = "a" * 50  # Exactly 50 characters
        
        user = User(
            username=valid_username,
            email="test@example.com",
            password_hash="hashed_password"
        )
        
        db_session.add(user)
        db_session.commit()
        
        assert user.username == valid_username

    def test_email_required(self, db_session: TestSession):
        """Test that email is required and cannot be None."""
        user = User(
            username="testuser",
            email=None,
            password_hash="hashed_password"
        )
        
        db_session.add(user)
        
        with pytest.raises(IntegrityError):
            db_session.commit()

    def test_email_cannot_be_empty(self, db_session: TestSession):
        """Test that email cannot be empty string."""
        user = User(
            username="testuser",
            email="",
            password_hash="hashed_password"
        )
        
        db_session.add(user)
        
        with pytest.raises(IntegrityError):
            db_session.commit()

    def test_email_max_length(self, db_session: TestSession):
        """Test that email cannot exceed maximum length of 255 characters."""
        long_email = "a" * 240 + "@example.com"  # Over 255 characters
        
        user = User(
            username="testuser",
            email=long_email,
            password_hash="hashed_password"
        )
        
        db_session.add(user)
        
        with pytest.raises(IntegrityError):
            db_session.commit()

    def test_password_hash_required(self, db_session: TestSession):
        """Test that password_hash is required and cannot be None."""
        user = User(
            username="testuser",
            email="test@example.com",
            password_hash=None
        )
        
        db_session.add(user)
        
        with pytest.raises(IntegrityError):
            db_session.commit()

    def test_first_name_max_length(self, db_session: TestSession):
        """Test that first_name cannot exceed maximum length of 100 characters."""
        long_first_name = "a" * 101
        
        user = User(
            username="testuser",
            email="test@example.com",
            password_hash="hashed_password",
            first_name=long_first_name
        )
        
        db_session.add(user)
        
        with pytest.raises(IntegrityError):
            db_session.commit()

    def test_last_name_max_length(self, db_session: TestSession):
        """Test that last_name cannot exceed maximum length of 100 characters."""
        long_last_name = "a" * 101
        
        user = User(
            username="testuser",
            email="test@example.com",
            password_hash="hashed_password",
            last_name=long_last_name
        )
        
        db_session.add(user)