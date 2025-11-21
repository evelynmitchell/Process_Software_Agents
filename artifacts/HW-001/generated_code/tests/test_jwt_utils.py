"""
Unit tests for JWT utilities

Tests JWT token generation, validation, expiration handling, and security edge cases.

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
    InvalidSignatureError,
    MissingClaimError
)


class TestJWTUtils:
    """Test suite for JWT utilities."""

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
        """Sample JWT payload for testing."""
        return {
            "user_id": "123",
            "username": "testuser",
            "email": "test@example.com",
            "role": "user"
        }

    def test_init_with_default_values(self):
        """Test JWTUtils initialization with default values."""
        jwt_utils = JWTUtils(secret_key="test_key")
        
        assert jwt_utils.secret_key == "test_key"
        assert jwt_utils.algorithm == "HS256"
        assert jwt_utils.access_token_expire_minutes == 15
        assert jwt_utils.refresh_token_expire_days == 30

    def test_init_with_custom_values(self):
        """Test JWTUtils initialization with custom values."""
        jwt_utils = JWTUtils(
            secret_key="custom_key",
            algorithm="HS512",
            access_token_expire_minutes=60,
            refresh_token_expire_days=14
        )
        
        assert jwt_utils.secret_key == "custom_key"
        assert jwt_utils.algorithm == "HS512"
        assert jwt_utils.access_token_expire_minutes == 60
        assert jwt_utils.refresh_token_expire_days == 14

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
            JWTUtils(secret_key="test_key", algorithm="INVALID")

    def test_generate_access_token_success(self, jwt_utils, sample_payload):
        """Test successful access token generation."""
        token = jwt_utils.generate_access_token(sample_payload)
        
        assert isinstance(token, str)
        assert len(token) > 0
        assert token.count('.') == 2  # JWT has 3 parts separated by dots

    def test_generate_access_token_with_custom_expiry(self, jwt_utils, sample_payload):
        """Test access token generation with custom expiry."""
        custom_expiry = datetime.now(timezone.utc) + timedelta(hours=2)
        token = jwt_utils.generate_access_token(sample_payload, expires_at=custom_expiry)
        
        decoded = jwt.decode(token, jwt_utils.secret_key, algorithms=[jwt_utils.algorithm])
        assert decoded['exp'] == int(custom_expiry.timestamp())

    def test_generate_access_token_adds_standard_claims(self, jwt_utils, sample_payload):
        """Test that access token includes standard JWT claims."""
        with freeze_time("2023-01-01 12:00:00"):
            token = jwt_utils.generate_access_token(sample_payload)
            
            decoded = jwt.decode(token, jwt_utils.secret_key, algorithms=[jwt_utils.algorithm])
            
            assert 'iat' in decoded  # issued at
            assert 'exp' in decoded  # expiration
            assert 'type' in decoded  # token type
            assert decoded['type'] == 'access'

    def test_generate_refresh_token_success(self, jwt_utils, sample_payload):
        """Test successful refresh token generation."""
        token = jwt_utils.generate_refresh_token(sample_payload)
        
        assert isinstance(token, str)
        assert len(token) > 0
        assert token.count('.') == 2

    def test_generate_refresh_token_with_custom_expiry(self, jwt_utils, sample_payload):
        """Test refresh token generation with custom expiry."""
        custom_expiry = datetime.now(timezone.utc) + timedelta(days=14)
        token = jwt_utils.generate_refresh_token(sample_payload, expires_at=custom_expiry)
        
        decoded = jwt.decode(token, jwt_utils.secret_key, algorithms=[jwt_utils.algorithm])
        assert decoded['exp'] == int(custom_expiry.timestamp())

    def test_generate_refresh_token_adds_standard_claims(self, jwt_utils, sample_payload):
        """Test that refresh token includes standard JWT claims."""
        with freeze_time("2023-01-01 12:00:00"):
            token = jwt_utils.generate_refresh_token(sample_payload)
            
            decoded = jwt.decode(token, jwt_utils.secret_key, algorithms=[jwt_utils.algorithm])
            
            assert 'iat' in decoded
            assert 'exp' in decoded
            assert 'type' in decoded
            assert decoded['type'] == 'refresh'

    def test_generate_token_with_empty_payload(self, jwt_utils):
        """Test token generation with empty payload."""
        token = jwt_utils.generate_access_token({})
        
        decoded = jwt.decode(token, jwt_utils.secret_key, algorithms=[jwt_utils.algorithm])
        assert 'iat' in decoded
        assert 'exp' in decoded
        assert 'type' in decoded

    def test_validate_token_success(self, jwt_utils, sample_payload):
        """Test successful token validation."""
        token = jwt_utils.generate_access_token(sample_payload)
        decoded_payload = jwt_utils.validate_token(token)
        
        assert decoded_payload['user_id'] == sample_payload['user_id']
        assert decoded_payload['username'] == sample_payload['username']
        assert decoded_payload['email'] == sample_payload['email']
        assert decoded_payload['role'] == sample_payload['role']
        assert decoded_payload['type'] == 'access'

    def test_validate_token_with_expired_token_raises_error(self, jwt_utils, sample_payload):
        """Test that expired token raises TokenExpiredError."""
        past_time = datetime.now(timezone.utc) - timedelta(hours=1)
        token = jwt_utils.generate_access_token(sample_payload, expires_at=past_time)
        
        with pytest.raises(TokenExpiredError, match="Token has expired"):
            jwt_utils.validate_token(token)

    def test_validate_token_with_invalid_signature_raises_error(self, jwt_utils, sample_payload):
        """Test that token with invalid signature raises InvalidSignatureError."""
        token = jwt_utils.generate_access_token(sample_payload)
        # Tamper with the token
        tampered_token = token[:-10] + "tampered123"
        
        with pytest.raises(InvalidSignatureError, match="Invalid token signature"):
            jwt_utils.validate