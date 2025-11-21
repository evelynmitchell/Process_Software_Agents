"""
Unit tests for JWT token generation, validation, expiration handling, and refresh token logic

Tests all JWT utility functions including token creation, validation, expiration,
refresh token management, and error handling scenarios.

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
    generate_access_token,
    generate_refresh_token,
    validate_token,
    decode_token,
    is_token_expired,
    refresh_access_token,
    revoke_token,
    get_token_expiry,
    extract_user_id,
    TokenError,
    ExpiredTokenError,
    InvalidTokenError,
    RevokedTokenError
)


class TestTokenGeneration:
    """Test cases for JWT token generation functions."""

    def test_generate_access_token_success(self):
        """Test that generate_access_token creates valid JWT with correct payload."""
        user_id = "user123"
        token = generate_access_token(user_id)
        
        assert isinstance(token, str)
        assert len(token.split('.')) == 3  # JWT has 3 parts
        
        # Decode without verification to check payload
        payload = jwt.decode(token, options={"verify_signature": False})
        assert payload["user_id"] == user_id
        assert payload["type"] == "access"
        assert "exp" in payload
        assert "iat" in payload
        assert "jti" in payload

    def test_generate_access_token_with_custom_expiry(self):
        """Test that generate_access_token respects custom expiry time."""
        user_id = "user123"
        custom_expiry = timedelta(hours=2)
        
        with freeze_time("2023-01-01 12:00:00") as frozen_time:
            token = generate_access_token(user_id, expires_in=custom_expiry)
            payload = jwt.decode(token, options={"verify_signature": False})
            
            expected_exp = int((frozen_time() + custom_expiry).timestamp())
            assert payload["exp"] == expected_exp

    def test_generate_access_token_with_additional_claims(self):
        """Test that generate_access_token includes additional claims."""
        user_id = "user123"
        additional_claims = {"role": "admin", "permissions": ["read", "write"]}
        
        token = generate_access_token(user_id, additional_claims=additional_claims)
        payload = jwt.decode(token, options={"verify_signature": False})
        
        assert payload["role"] == "admin"
        assert payload["permissions"] == ["read", "write"]

    def test_generate_access_token_invalid_user_id(self):
        """Test that generate_access_token raises error for invalid user_id."""
        with pytest.raises(ValueError, match="User ID cannot be empty"):
            generate_access_token("")
        
        with pytest.raises(ValueError, match="User ID cannot be empty"):
            generate_access_token(None)

    def test_generate_refresh_token_success(self):
        """Test that generate_refresh_token creates valid JWT with correct payload."""
        user_id = "user123"
        token = generate_refresh_token(user_id)
        
        assert isinstance(token, str)
        assert len(token.split('.')) == 3
        
        payload = jwt.decode(token, options={"verify_signature": False})
        assert payload["user_id"] == user_id
        assert payload["type"] == "refresh"
        assert "exp" in payload
        assert "iat" in payload
        assert "jti" in payload

    def test_generate_refresh_token_longer_expiry(self):
        """Test that refresh token has longer expiry than access token."""
        user_id = "user123"
        
        with freeze_time("2023-01-01 12:00:00"):
            access_token = generate_access_token(user_id)
            refresh_token = generate_refresh_token(user_id)
            
            access_payload = jwt.decode(access_token, options={"verify_signature": False})
            refresh_payload = jwt.decode(refresh_token, options={"verify_signature": False})
            
            assert refresh_payload["exp"] > access_payload["exp"]

    def test_generate_refresh_token_invalid_user_id(self):
        """Test that generate_refresh_token raises error for invalid user_id."""
        with pytest.raises(ValueError, match="User ID cannot be empty"):
            generate_refresh_token("")


class TestTokenValidation:
    """Test cases for JWT token validation functions."""

    def test_validate_token_success(self):
        """Test that validate_token returns True for valid token."""
        user_id = "user123"
        token = generate_access_token(user_id)
        
        assert validate_token(token) is True

    def test_validate_token_invalid_signature(self):
        """Test that validate_token returns False for token with invalid signature."""
        user_id = "user123"
        token = generate_access_token(user_id)
        
        # Tamper with token
        parts = token.split('.')
        tampered_token = parts[0] + '.' + parts[1] + '.invalid_signature'
        
        assert validate_token(tampered_token) is False

    def test_validate_token_expired(self):
        """Test that validate_token returns False for expired token."""
        user_id = "user123"
        
        with freeze_time("2023-01-01 12:00:00"):
            token = generate_access_token(user_id, expires_in=timedelta(minutes=1))
        
        with freeze_time("2023-01-01 12:02:00"):
            assert validate_token(token) is False

    def test_validate_token_malformed(self):
        """Test that validate_token returns False for malformed token."""
        assert validate_token("invalid.token") is False
        assert validate_token("not_a_token") is False
        assert validate_token("") is False
        assert validate_token(None) is False

    @patch('src.utils.jwt_utils.is_token_revoked')
    def test_validate_token_revoked(self, mock_is_revoked):
        """Test that validate_token returns False for revoked token."""
        mock_is_revoked.return_value = True
        
        user_id = "user123"
        token = generate_access_token(user_id)
        
        assert validate_token(token) is False

    def test_decode_token_success(self):
        """Test that decode_token returns correct payload for valid token."""
        user_id = "user123"
        additional_claims = {"role": "admin"}
        token = generate_access_token(user_id, additional_claims=additional_claims)
        
        payload = decode_token(token)
        
        assert payload["user_id"] == user_id
        assert payload["role"] == "admin"
        assert payload["type"] == "access"

    def test_decode_token_expired(self):
        """Test that decode_token raises ExpiredTokenError for expired token."""
        user_id = "user123"
        
        with freeze_time("2023-01-01 12:00:00"):
            token = generate_access_token(user_id, expires_in=timedelta(minutes=1))
        
        with freeze_time("2023-01-01 12:02:00"):
            with pytest.raises(ExpiredTokenError, match="Token has expired"):
                decode_token(token)

    def test_decode_token_invalid(self):
        """Test that decode_token raises InvalidTokenError for invalid token."""
        with pytest.raises(InvalidTokenError, match="Invalid token format"):
            decode_token("invalid_token")

    @patch('src.utils.jwt_utils.is_token_revoked')