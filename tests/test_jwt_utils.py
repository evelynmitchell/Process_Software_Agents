"""
Unit tests for JWT utilities

Tests JWT token generation, validation, expiration handling, and malformed token scenarios.

Component ID: COMP-008
Semantic Unit: SU-008

Author: ASP Code Agent
"""

import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import patch, MagicMock
import jwt
from freezegun import freeze_time

from src.utils.jwt_utils import (
    JWTUtils,
    TokenExpiredError,
    InvalidTokenError,
    TokenValidationError
)


@pytest.fixture
def jwt_utils():
    """Create JWTUtils instance with test configuration."""
    return JWTUtils(
        secret_key="test_secret_key_12345",
        algorithm="HS256",
        access_token_expire_minutes=30,
        refresh_token_expire_days=7
    )


@pytest.fixture
def sample_payload():
    """Sample JWT payload for testing."""
    return {
        "user_id": "123",
        "username": "testuser",
        "email": "test@example.com",
        "role": "user"
    }


@pytest.fixture
def expired_token(jwt_utils, sample_payload):
    """Generate an expired token for testing."""
    with freeze_time("2023-01-01 12:00:00"):
        token = jwt_utils.generate_access_token(sample_payload)
    return token


class TestJWTUtilsInitialization:
    """Test JWT utilities initialization and configuration."""

    def test_jwt_utils_initialization_with_defaults(self):
        """Test JWTUtils initialization with default values."""
        jwt_util = JWTUtils()
        
        assert jwt_util.algorithm == "HS256"
        assert jwt_util.access_token_expire_minutes == 15
        assert jwt_util.refresh_token_expire_days == 30
        assert jwt_util.secret_key is not None

    def test_jwt_utils_initialization_with_custom_values(self):
        """Test JWTUtils initialization with custom configuration."""
        jwt_util = JWTUtils(
            secret_key="custom_secret",
            algorithm="HS512",
            access_token_expire_minutes=60,
            refresh_token_expire_days=14
        )
        
        assert jwt_util.secret_key == "custom_secret"
        assert jwt_util.algorithm == "HS512"
        assert jwt_util.access_token_expire_minutes == 60
        assert jwt_util.refresh_token_expire_days == 14

    def test_jwt_utils_initialization_with_empty_secret_raises_error(self):
        """Test that empty secret key raises ValueError."""
        with pytest.raises(ValueError, match="Secret key cannot be empty"):
            JWTUtils(secret_key="")

    def test_jwt_utils_initialization_with_none_secret_raises_error(self):
        """Test that None secret key raises ValueError."""
        with pytest.raises(ValueError, match="Secret key cannot be empty"):
            JWTUtils(secret_key=None)


class TestAccessTokenGeneration:
    """Test access token generation functionality."""

    def test_generate_access_token_success(self, jwt_utils, sample_payload):
        """Test successful access token generation."""
        token = jwt_utils.generate_access_token(sample_payload)
        
        assert isinstance(token, str)
        assert len(token) > 0
        assert token.count('.') == 2  # JWT has 3 parts separated by dots

    def test_generate_access_token_includes_payload_data(self, jwt_utils, sample_payload):
        """Test that generated token includes payload data."""
        token = jwt_utils.generate_access_token(sample_payload)
        decoded = jwt.decode(token, jwt_utils.secret_key, algorithms=[jwt_utils.algorithm])
        
        assert decoded["user_id"] == sample_payload["user_id"]
        assert decoded["username"] == sample_payload["username"]
        assert decoded["email"] == sample_payload["email"]
        assert decoded["role"] == sample_payload["role"]

    def test_generate_access_token_includes_expiration(self, jwt_utils, sample_payload):
        """Test that generated token includes expiration time."""
        with freeze_time("2023-01-01 12:00:00") as frozen_time:
            token = jwt_utils.generate_access_token(sample_payload)
            decoded = jwt.decode(token, jwt_utils.secret_key, algorithms=[jwt_utils.algorithm])
            
            expected_exp = datetime.now(timezone.utc) + timedelta(minutes=30)
            actual_exp = datetime.fromtimestamp(decoded["exp"], timezone.utc)
            
            assert abs((actual_exp - expected_exp).total_seconds()) < 1

    def test_generate_access_token_includes_issued_at(self, jwt_utils, sample_payload):
        """Test that generated token includes issued at time."""
        with freeze_time("2023-01-01 12:00:00"):
            token = jwt_utils.generate_access_token(sample_payload)
            decoded = jwt.decode(token, jwt_utils.secret_key, algorithms=[jwt_utils.algorithm])
            
            expected_iat = datetime.now(timezone.utc)
            actual_iat = datetime.fromtimestamp(decoded["iat"], timezone.utc)
            
            assert abs((actual_iat - expected_iat).total_seconds()) < 1

    def test_generate_access_token_includes_token_type(self, jwt_utils, sample_payload):
        """Test that generated token includes token type."""
        token = jwt_utils.generate_access_token(sample_payload)
        decoded = jwt.decode(token, jwt_utils.secret_key, algorithms=[jwt_utils.algorithm])
        
        assert decoded["token_type"] == "access"

    def test_generate_access_token_with_empty_payload(self, jwt_utils):
        """Test access token generation with empty payload."""
        token = jwt_utils.generate_access_token({})
        decoded = jwt.decode(token, jwt_utils.secret_key, algorithms=[jwt_utils.algorithm])
        
        assert "exp" in decoded
        assert "iat" in decoded
        assert "token_type" in decoded
        assert decoded["token_type"] == "access"

    def test_generate_access_token_with_none_payload_raises_error(self, jwt_utils):
        """Test that None payload raises TypeError."""
        with pytest.raises(TypeError):
            jwt_utils.generate_access_token(None)


class TestRefreshTokenGeneration:
    """Test refresh token generation functionality."""

    def test_generate_refresh_token_success(self, jwt_utils, sample_payload):
        """Test successful refresh token generation."""
        token = jwt_utils.generate_refresh_token(sample_payload)
        
        assert isinstance(token, str)
        assert len(token) > 0
        assert token.count('.') == 2

    def test_generate_refresh_token_includes_payload_data(self, jwt_utils, sample_payload):
        """Test that generated refresh token includes payload data."""
        token = jwt_utils.generate_refresh_token(sample_payload)
        decoded = jwt.decode(token, jwt_utils.secret_key, algorithms=[jwt_utils.algorithm])
        
        assert decoded["user_id"] == sample_payload["user_id"]
        assert decoded["username"] == sample_payload["username"]

    def test_generate_refresh_token_has_longer_expiration(self, jwt_utils, sample_payload):
        """Test that refresh token has longer expiration than access token."""
        with freeze_time("2023-01-01 12:00:00"):
            access_token = jwt_utils.generate_access_token(sample_payload)
            refresh_token = jwt_utils.generate_refresh_token(sample_payload)
            
            access_decoded = jwt.decode(access_token, jwt_utils.secret_key, algorithms=[jwt_utils.algorithm])
            refresh_decoded = jwt.decode(refresh_token, jwt_utils.secret_key,