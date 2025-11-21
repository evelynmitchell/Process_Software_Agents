"""
Unit tests for JWT utilities

Tests JWT token generation, validation, expiration handling, and error scenarios.

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
    TokenDecodeError
)


class TestJWTUtils:
    """Test suite for JWTUtils class."""

    @pytest.fixture
    def jwt_utils(self):
        """Create JWTUtils instance with test configuration."""
        return JWTUtils(
            secret_key="test_secret_key_12345",
            algorithm="HS256",
            access_token_expire_minutes=30,
            refresh_token_expire_days=7
        )

    @pytest.fixture
    def sample_payload(self):
        """Sample payload for token generation."""
        return {
            "user_id": "123",
            "username": "testuser",
            "email": "test@example.com"
        }

    def test_init_with_default_values(self):
        """Test JWTUtils initialization with default values."""
        jwt_utils = JWTUtils(secret_key="test_key")
        
        assert jwt_utils.secret_key == "test_key"
        assert jwt_utils.algorithm == "HS256"
        assert jwt_utils.access_token_expire_minutes == 15
        assert jwt_utils.refresh_token_expire_days == 30

    def test_init_with_custom_values(self, jwt_utils):
        """Test JWTUtils initialization with custom values."""
        assert jwt_utils.secret_key == "test_secret_key_12345"
        assert jwt_utils.algorithm == "HS256"
        assert jwt_utils.access_token_expire_minutes == 30
        assert jwt_utils.refresh_token_expire_days == 7

    def test_init_with_empty_secret_key_raises_error(self):
        """Test that empty secret key raises ValueError."""
        with pytest.raises(ValueError, match="Secret key cannot be empty"):
            JWTUtils(secret_key="")

    def test_init_with_none_secret_key_raises_error(self):
        """Test that None secret key raises ValueError."""
        with pytest.raises(ValueError, match="Secret key cannot be empty"):
            JWTUtils(secret_key=None)

    def test_init_with_invalid_algorithm_raises_error(self):
        """Test that invalid algorithm raises ValueError."""
        with pytest.raises(ValueError, match="Unsupported algorithm"):
            JWTUtils(secret_key="test", algorithm="INVALID")

    def test_generate_access_token_success(self, jwt_utils, sample_payload):
        """Test successful access token generation."""
        with freeze_time("2023-01-01 12:00:00"):
            token = jwt_utils.generate_access_token(sample_payload)
            
            assert isinstance(token, str)
            assert len(token) > 0
            
            # Decode token to verify payload
            decoded = jwt.decode(
                token,
                jwt_utils.secret_key,
                algorithms=[jwt_utils.algorithm]
            )
            
            assert decoded["user_id"] == "123"
            assert decoded["username"] == "testuser"
            assert decoded["email"] == "test@example.com"
            assert decoded["type"] == "access"
            assert "exp" in decoded
            assert "iat" in decoded

    def test_generate_access_token_with_custom_expiry(self, jwt_utils, sample_payload):
        """Test access token generation with custom expiry time."""
        custom_expiry = 60  # 60 minutes
        
        with freeze_time("2023-01-01 12:00:00"):
            token = jwt_utils.generate_access_token(sample_payload, expires_delta=custom_expiry)
            
            decoded = jwt.decode(
                token,
                jwt_utils.secret_key,
                algorithms=[jwt_utils.algorithm]
            )
            
            expected_exp = datetime(2023, 1, 1, 13, 0, 0, tzinfo=timezone.utc).timestamp()
            assert decoded["exp"] == expected_exp

    def test_generate_refresh_token_success(self, jwt_utils, sample_payload):
        """Test successful refresh token generation."""
        with freeze_time("2023-01-01 12:00:00"):
            token = jwt_utils.generate_refresh_token(sample_payload)
            
            assert isinstance(token, str)
            assert len(token) > 0
            
            # Decode token to verify payload
            decoded = jwt.decode(
                token,
                jwt_utils.secret_key,
                algorithms=[jwt_utils.algorithm]
            )
            
            assert decoded["user_id"] == "123"
            assert decoded["username"] == "testuser"
            assert decoded["email"] == "test@example.com"
            assert decoded["type"] == "refresh"
            assert "exp" in decoded
            assert "iat" in decoded

    def test_generate_refresh_token_with_custom_expiry(self, jwt_utils, sample_payload):
        """Test refresh token generation with custom expiry time."""
        custom_expiry = 14  # 14 days
        
        with freeze_time("2023-01-01 12:00:00"):
            token = jwt_utils.generate_refresh_token(sample_payload, expires_delta=custom_expiry)
            
            decoded = jwt.decode(
                token,
                jwt_utils.secret_key,
                algorithms=[jwt_utils.algorithm]
            )
            
            expected_exp = datetime(2023, 1, 15, 12, 0, 0, tzinfo=timezone.utc).timestamp()
            assert decoded["exp"] == expected_exp

    def test_validate_token_success(self, jwt_utils, sample_payload):
        """Test successful token validation."""
        with freeze_time("2023-01-01 12:00:00"):
            token = jwt_utils.generate_access_token(sample_payload)
            
            # Validate immediately after generation
            decoded_payload = jwt_utils.validate_token(token)
            
            assert decoded_payload["user_id"] == "123"
            assert decoded_payload["username"] == "testuser"
            assert decoded_payload["email"] == "test@example.com"
            assert decoded_payload["type"] == "access"

    def test_validate_token_expired_raises_error(self, jwt_utils, sample_payload):
        """Test that expired token raises TokenExpiredError."""
        with freeze_time("2023-01-01 12:00:00"):
            token = jwt_utils.generate_access_token(sample_payload)
        
        # Move time forward past expiration
        with freeze_time("2023-01-01 13:00:00"):
            with pytest.raises(TokenExpiredError, match="Token has expired"):
                jwt_utils.validate_token(token)

    def test_validate_token_invalid_signature_raises_error(self, jwt_utils, sample_payload):
        """Test that token with invalid signature raises InvalidTokenError."""
        token = jwt_utils.generate_access_token(sample_payload)
        
        # Create JWTUtils with different secret key
        different_jwt_utils = JWTUtils(secret_key="different_secret")
        
        with pytest.raises(InvalidTokenError, match="Invalid token signature"):
            different_jwt_utils.validate_token(token)

    def test_validate_token_malformed_raises_error(self, jwt_utils):
        """Test that malformed token raises TokenDecodeError."""
        malformed_token = "invalid.token.format"
        
        with pytest.raises(TokenDecodeError, match="Failed to decode token"):
            jwt_utils.validate_token(malformed_token)

    def test_validate