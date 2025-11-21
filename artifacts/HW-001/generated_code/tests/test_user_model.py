"""
Unit tests for User model

Tests the User model including validation, relationships, and database operations.

Component ID: COMP-004
Semantic Unit: SU-004

Author: ASP Code Agent
"""

import pytest
from datetime import datetime, timezone
from unittest.mock import Mock, patch
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
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
        
        assert user.username == "testuser"
        assert user.email == "test@example.com"
        assert user.password_hash == "hashed_password_123"
        assert user.role == UserRole.USER  # Default value
        assert user.status == UserStatus.ACTIVE  # Default value
        assert user.is_verified is False  # Default value
        assert user.created_at is None  # Not set until saved
        assert user.updated_at is None  # Not set until saved

    def test_user_creation_with_all_fields(self, db_session: TestSession):
        """Test that User can be created with all fields specified."""
        now = datetime.now(timezone.utc)
        
        user = User(
            username="adminuser",
            email="admin@example.com",
            password_hash="hashed_admin_password",
            first_name="Admin",
            last_name="User",
            role=UserRole.ADMIN,
            status=UserStatus.ACTIVE,
            is_verified=True,
            created_at=now,
            updated_at=now
        )
        
        assert user.username == "adminuser"
        assert user.email == "admin@example.com"
        assert user.password_hash == "hashed_admin_password"
        assert user.first_name == "Admin"
        assert user.last_name == "User"
        assert user.role == UserRole.ADMIN
        assert user.status == UserStatus.ACTIVE
        assert user.is_verified is True
        assert user.created_at == now
        assert user.updated_at == now

    def test_user_string_representation(self, db_session: TestSession):
        """Test that User __str__ method returns username."""
        user = User(
            username="testuser",
            email="test@example.com",
            password_hash="hashed_password"
        )
        
        assert str(user) == "testuser"

    def test_user_repr_representation(self, db_session: TestSession):
        """Test that User __repr__ method returns proper representation."""
        user = User(
            username="testuser",
            email="test@example.com",
            password_hash="hashed_password"
        )
        
        expected = "<User(username='testuser', email='test@example.com')>"
        assert repr(user) == expected


class TestUserValidation:
    """Test suite for User model validation."""

    def test_username_required(self, db_session: TestSession):
        """Test that username is required."""
        user = User(
            email="test@example.com",
            password_hash="hashed_password"
        )
        
        db_session.add(user)
        with pytest.raises(IntegrityError):
            db_session.commit()

    def test_email_required(self, db_session: TestSession):
        """Test that email is required."""
        user = User(
            username="testuser",
            password_hash="hashed_password"
        )
        
        db_session.add(user)
        with pytest.raises(IntegrityError):
            db_session.commit()

    def test_password_hash_required(self, db_session: TestSession):
        """Test that password_hash is required."""
        user = User(
            username="testuser",
            email="test@example.com"
        )
        
        db_session.add(user)
        with pytest.raises(IntegrityError):
            db_session.commit()

    def test_username_unique_constraint(self, db_session: TestSession):
        """Test that username must be unique."""
        user1 = User(
            username="testuser",
            email="test1@example.com",
            password_hash="hashed_password1"
        )
        user2 = User(
            username="testuser",
            email="test2@example.com",
            password_hash="hashed_password2"
        )
        
        db_session.add(user1)
        db_session.commit()
        
        db_session.add(user2)
        with pytest.raises(IntegrityError):
            db_session.commit()

    def test_email_unique_constraint(self, db_session: TestSession):
        """Test that email must be unique."""
        user1 = User(
            username="testuser1",
            email="test@example.com",
            password_hash="hashed_password1"
        )
        user2 = User(
            username="testuser2",
            email="test@example.com",
            password_hash="hashed_password2"
        )
        
        db_session.add(user1)
        db_session.commit()
        
        db_session.add(user2)
        with pytest.raises(IntegrityError):
            db_session.commit()

    def test_username_max_length(self, db_session: TestSession):
        """Test that username respects maximum length constraint."""
        long_username = "a" * 51  # Assuming max length is 50
        
        user = User(
            username=long_username,
            email="test@example.com",
            password_hash="hashed_password"
        )
        
        db_session.add(user)
        with pytest.raises(SQLAlchemyError):
            db_session.commit()

    def test_email_max_length(self, db_session: TestSession):
        """Test that email respects maximum length constraint."""
        long_email = "a" * 100 + "@example.com"  # Assuming max length is 100
        
        user = User(
            username="testuser",
            email=long_email,
            password_hash="hashed_password"
        )
        
        db_session.add(user)
        with pytest.raises(SQLAlchemyError):
            db_session.commit()

    def test_first_name_max_length(self, db_session: TestSession):
        """Test that first_name respects maximum length constraint."""
        long_first_name = "a" * 51  # Assuming max length is 50
        
        user = User(
            username="testuser",
            email="test@example.com",
            password_hash="hashed_password",
            first_name=long_first_name
        )
        
        db_session.add(user)
        with pytest.raises(SQLAlchemyError):
            db_session.commit()

    def test_last_name_max_length(self, db_session: TestSession):
        """Test that last_name respects maximum length constraint."""
        long_last_name = "a" * 51  # Assuming max length is 50
        
        user = User(
            username="testuser",
            email="test@example.com",
            password_hash="hashed_password",
            last_name=long_last_name
        )
        
        db_session.add(user)
        with pytest.raises(SQLAlchemyError):
            db_session.commit()


class TestUserEnums:
    """Test suite for User model enum fields."""

    def test_user_role_enum_values(self, db_session: TestSession):
        """Test that UserRole enum accepts valid values."""
        # Test USER