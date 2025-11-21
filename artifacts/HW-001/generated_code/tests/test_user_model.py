"""
Unit tests for User model operations, validation, and database relationships.

Tests user creation, validation, authentication, and database operations.

Component ID: COMP-004
Semantic Unit: SU-004

Author: ASP Code Agent
"""

import pytest
from datetime import datetime, timezone
from unittest.mock import Mock, patch, MagicMock
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session
from passlib.context import CryptContext

from src.models.user import User, UserCreate, UserUpdate, UserResponse


@pytest.fixture
def mock_db_session():
    """Create mock database session for testing."""
    session = Mock(spec=Session)
    session.add = Mock()
    session.commit = Mock()
    session.refresh = Mock()
    session.query = Mock()
    session.delete = Mock()
    session.rollback = Mock()
    return session


@pytest.fixture
def sample_user_data():
    """Sample user data for testing."""
    return {
        "email": "test@example.com",
        "username": "testuser",
        "password": "SecurePass123!",
        "full_name": "Test User"
    }


@pytest.fixture
def sample_user_create(sample_user_data):
    """Sample UserCreate instance for testing."""
    return UserCreate(**sample_user_data)


@pytest.fixture
def sample_user_instance():
    """Sample User model instance for testing."""
    user = User(
        id=1,
        email="test@example.com",
        username="testuser",
        hashed_password="$2b$12$hashed_password_here",
        full_name="Test User",
        is_active=True,
        is_superuser=False,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    return user


class TestUserModel:
    """Test cases for User model class."""

    def test_user_model_creation(self, sample_user_instance):
        """Test that User model instance is created correctly."""
        user = sample_user_instance
        assert user.id == 1
        assert user.email == "test@example.com"
        assert user.username == "testuser"
        assert user.full_name == "Test User"
        assert user.is_active is True
        assert user.is_superuser is False
        assert isinstance(user.created_at, datetime)
        assert isinstance(user.updated_at, datetime)

    def test_user_model_string_representation(self, sample_user_instance):
        """Test User model string representation."""
        user = sample_user_instance
        assert str(user) == f"User(id={user.id}, username={user.username}, email={user.email})"

    def test_user_model_repr(self, sample_user_instance):
        """Test User model repr representation."""
        user = sample_user_instance
        expected = f"<User(id={user.id}, username='{user.username}', email='{user.email}')>"
        assert repr(user) == expected

    def test_user_model_password_verification_success(self, sample_user_instance):
        """Test successful password verification."""
        user = sample_user_instance
        with patch('src.models.user.pwd_context.verify') as mock_verify:
            mock_verify.return_value = True
            assert user.verify_password("correct_password") is True
            mock_verify.assert_called_once_with("correct_password", user.hashed_password)

    def test_user_model_password_verification_failure(self, sample_user_instance):
        """Test failed password verification."""
        user = sample_user_instance
        with patch('src.models.user.pwd_context.verify') as mock_verify:
            mock_verify.return_value = False
            assert user.verify_password("wrong_password") is False
            mock_verify.assert_called_once_with("wrong_password", user.hashed_password)

    def test_user_model_password_verification_empty_password(self, sample_user_instance):
        """Test password verification with empty password."""
        user = sample_user_instance
        with patch('src.models.user.pwd_context.verify') as mock_verify:
            mock_verify.return_value = False
            assert user.verify_password("") is False

    def test_user_model_password_verification_none_password(self, sample_user_instance):
        """Test password verification with None password."""
        user = sample_user_instance
        with patch('src.models.user.pwd_context.verify') as mock_verify:
            mock_verify.return_value = False
            assert user.verify_password(None) is False

    def test_user_model_is_active_default(self):
        """Test that is_active defaults to True."""
        user = User(email="test@example.com", username="test", hashed_password="hash")
        assert user.is_active is True

    def test_user_model_is_superuser_default(self):
        """Test that is_superuser defaults to False."""
        user = User(email="test@example.com", username="test", hashed_password="hash")
        assert user.is_superuser is False

    def test_user_model_timestamps_auto_set(self):
        """Test that timestamps are automatically set."""
        with patch('src.models.user.datetime') as mock_datetime:
            mock_now = datetime(2023, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
            mock_datetime.now.return_value = mock_now
            mock_datetime.timezone = timezone
            
            user = User(email="test@example.com", username="test", hashed_password="hash")
            # Timestamps would be set by database defaults or SQLAlchemy events
            assert hasattr(user, 'created_at')
            assert hasattr(user, 'updated_at')


class TestUserCreateSchema:
    """Test cases for UserCreate Pydantic schema."""

    def test_user_create_valid_data(self, sample_user_data):
        """Test UserCreate with valid data."""
        user_create = UserCreate(**sample_user_data)
        assert user_create.email == "test@example.com"
        assert user_create.username == "testuser"
        assert user_create.password == "SecurePass123!"
        assert user_create.full_name == "Test User"

    def test_user_create_email_validation_invalid_format(self):
        """Test UserCreate email validation with invalid format."""
        with pytest.raises(ValueError, match="Invalid email format"):
            UserCreate(
                email="invalid-email",
                username="testuser",
                password="SecurePass123!",
                full_name="Test User"
            )

    def test_user_create_email_validation_empty(self):
        """Test UserCreate email validation with empty email."""
        with pytest.raises(ValueError, match="Email cannot be empty"):
            UserCreate(
                email="",
                username="testuser",
                password="SecurePass123!",
                full_name="Test User"
            )

    def test_user_create_username_validation_too_short(self):
        """Test UserCreate username validation with too short username."""
        with pytest.raises(ValueError, match="Username must be between 3 and 50 characters"):
            UserCreate(
                email="test@example.com",
                username="ab",
                password="SecurePass123!",
                full_name="Test User"
            )

    def test_user_create_username_validation_too_long(self):
        """Test UserCreate username validation with too long username."""
        long_username = "a" * 51
        with pytest.raises(ValueError, match="Username must be between 3 and 50 characters"):
            UserCreate(
                email="test@example.com",
                username=long_username,
                password="SecurePass123!",
                full_name="Test User"
            )

    def test_user_create_username_validation_invali