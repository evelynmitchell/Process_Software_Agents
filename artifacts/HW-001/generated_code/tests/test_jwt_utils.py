"""
Unit tests for JWT utilities

Tests JWT token generation, validation, expiration, and security edge cases.

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
    generate_token,
    validate_token,
    decode_token,
    is_token_expired,
    refresh_token,
    revoke_token,
    get_token_claims,
    JWTError,
    TokenExpiredError,
    InvalidTokenError,
    RevokedTokenError
)


class TestGenerateToken:
    """Test cases for JWT token generation."""

    def test_generate_token_with_valid_payload(self):
        """Test that generate_token creates valid JWT with correct payload."""
        payload = {"user_id": 123, "username": "testuser"}
        token = generate_token(payload)
        
        assert isinstance(token, str)
        assert len(token.split('.')) == 3  # JWT has 3 parts
        
        # Decode without verification to check payload
        decoded = jwt.decode(token, options={"verify_signature": False})
        assert decoded["user_id"] == 123
        assert decoded["username"] == "testuser"
        assert "exp" in decoded
        assert "iat" in decoded
        assert "jti" in decoded

    def test_generate_token_with_custom_expiration(self):
        """Test that generate_token respects custom expiration time."""
        payload = {"user_id": 123}
        expires_in = timedelta(hours=2)
        
        with freeze_time("2023-01-01 12:00:00"):
            token = generate_token(payload, expires_in=expires_in)
            decoded = jwt.decode(token, options={"verify_signature": False})
            
            expected_exp = datetime(2023, 1, 1, 14, 0, 0, tzinfo=timezone.utc).timestamp()
            assert decoded["exp"] == expected_exp

    def test_generate_token_with_empty_payload(self):
        """Test that generate_token works with empty payload."""
        payload = {}
        token = generate_token(payload)
        
        assert isinstance(token, str)
        decoded = jwt.decode(token, options={"verify_signature": False})
        assert "exp" in decoded
        assert "iat" in decoded
        assert "jti" in decoded

    def test_generate_token_includes_required_claims(self):
        """Test that generate_token includes all required JWT claims."""
        payload = {"user_id": 123}
        
        with freeze_time("2023-01-01 12:00:00"):
            token = generate_token(payload)
            decoded = jwt.decode(token, options={"verify_signature": False})
            
            # Check required claims
            assert decoded["iat"] == datetime(2023, 1, 1, 12, 0, 0, tzinfo=timezone.utc).timestamp()
            assert "exp" in decoded
            assert "jti" in decoded
            assert len(decoded["jti"]) > 0

    def test_generate_token_with_none_payload_raises_error(self):
        """Test that generate_token raises error with None payload."""
        with pytest.raises(ValueError, match="Payload cannot be None"):
            generate_token(None)

    def test_generate_token_with_invalid_expiration_raises_error(self):
        """Test that generate_token raises error with negative expiration."""
        payload = {"user_id": 123}
        expires_in = timedelta(hours=-1)
        
        with pytest.raises(ValueError, match="Expiration time must be positive"):
            generate_token(payload, expires_in=expires_in)


class TestValidateToken:
    """Test cases for JWT token validation."""

    def test_validate_token_with_valid_token_returns_true(self):
        """Test that validate_token returns True for valid token."""
        payload = {"user_id": 123}
        token = generate_token(payload)
        
        assert validate_token(token) is True

    def test_validate_token_with_expired_token_returns_false(self):
        """Test that validate_token returns False for expired token."""
        payload = {"user_id": 123}
        expires_in = timedelta(seconds=1)
        
        with freeze_time("2023-01-01 12:00:00"):
            token = generate_token(payload, expires_in=expires_in)
        
        with freeze_time("2023-01-01 12:00:02"):
            assert validate_token(token) is False

    def test_validate_token_with_invalid_signature_returns_false(self):
        """Test that validate_token returns False for token with invalid signature."""
        payload = {"user_id": 123}
        token = generate_token(payload)
        
        # Tamper with token
        parts = token.split('.')
        tampered_token = parts[0] + '.' + parts[1] + '.invalid_signature'
        
        assert validate_token(tampered_token) is False

    def test_validate_token_with_malformed_token_returns_false(self):
        """Test that validate_token returns False for malformed token."""
        malformed_tokens = [
            "not.a.jwt",
            "invalid_token",
            "",
            "a.b",  # Missing part
            "a.b.c.d"  # Too many parts
        ]
        
        for token in malformed_tokens:
            assert validate_token(token) is False

    def test_validate_token_with_none_token_returns_false(self):
        """Test that validate_token returns False for None token."""
        assert validate_token(None) is False

    @patch('src.utils.jwt_utils.is_token_revoked')
    def test_validate_token_with_revoked_token_returns_false(self, mock_is_revoked):
        """Test that validate_token returns False for revoked token."""
        mock_is_revoked.return_value = True
        
        payload = {"user_id": 123}
        token = generate_token(payload)
        
        assert validate_token(token) is False


class TestDecodeToken:
    """Test cases for JWT token decoding."""

    def test_decode_token_with_valid_token_returns_payload(self):
        """Test that decode_token returns correct payload for valid token."""
        payload = {"user_id": 123, "username": "testuser"}
        token = generate_token(payload)
        
        decoded = decode_token(token)
        assert decoded["user_id"] == 123
        assert decoded["username"] == "testuser"

    def test_decode_token_with_expired_token_raises_error(self):
        """Test that decode_token raises TokenExpiredError for expired token."""
        payload = {"user_id": 123}
        expires_in = timedelta(seconds=1)
        
        with freeze_time("2023-01-01 12:00:00"):
            token = generate_token(payload, expires_in=expires_in)
        
        with freeze_time("2023-01-01 12:00:02"):
            with pytest.raises(TokenExpiredError, match="Token has expired"):
                decode_token(token)

    def test_decode_token_with_invalid_signature_raises_error(self):
        """Test that decode_token raises InvalidTokenError for invalid signature."""
        payload = {"user_id": 123}
        token = generate_token(payload)
        
        # Tamper with token
        parts = token.split('.')
        tampered_token = parts[0] + '.' + parts[1] + '.invalid_signature'
        
        with pytest.raises(InvalidTokenError, match="Invalid token signature"):
            decode_token(tampered_token)

    def test_decode_token_with_malformed_token_raises