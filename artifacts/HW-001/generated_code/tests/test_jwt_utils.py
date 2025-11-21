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


@pytest.fixture
def mock_secret_key():
    """Mock JWT secret key for testing."""
    return "test-secret-key-12345"


@pytest.fixture
def mock_algorithm():
    """Mock JWT algorithm for testing."""
    return "HS256"


@pytest.fixture
def sample_user_id():
    """Sample user ID for testing."""
    return "user123"


@pytest.fixture
def sample_payload():
    """Sample JWT payload for testing."""
    return {
        "user_id": "user123",
        "email": "test@example.com",
        "role": "user"
    }


@pytest.fixture
def valid_access_token(mock_secret_key, mock_algorithm, sample_payload):
    """Generate a valid access token for testing."""
    payload = sample_payload.copy()
    payload["exp"] = datetime.now(timezone.utc) + timedelta(hours=1)
    payload["iat"] = datetime.now(timezone.utc)
    payload["type"] = "access"
    return jwt.encode(payload, mock_secret_key, algorithm=mock_algorithm)


@pytest.fixture
def valid_refresh_token(mock_secret_key, mock_algorithm, sample_payload):
    """Generate a valid refresh token for testing."""
    payload = sample_payload.copy()
    payload["exp"] = datetime.now(timezone.utc) + timedelta(days=7)
    payload["iat"] = datetime.now(timezone.utc)
    payload["type"] = "refresh"
    return jwt.encode(payload, mock_secret_key, algorithm=mock_algorithm)


@pytest.fixture
def expired_token(mock_secret_key, mock_algorithm, sample_payload):
    """Generate an expired token for testing."""
    payload = sample_payload.copy()
    payload["exp"] = datetime.now(timezone.utc) - timedelta(hours=1)
    payload["iat"] = datetime.now(timezone.utc) - timedelta(hours=2)
    payload["type"] = "access"
    return jwt.encode(payload, mock_secret_key, algorithm=mock_algorithm)


class TestGenerateAccessToken:
    """Test cases for generate_access_token function."""

    @patch('src.utils.jwt_utils.JWT_SECRET_KEY', 'test-secret')
    @patch('src.utils.jwt_utils.JWT_ALGORITHM', 'HS256')
    def test_generate_access_token_success(self, sample_user_id):
        """Test successful access token generation."""
        token = generate_access_token(sample_user_id)
        
        assert isinstance(token, str)
        assert len(token) > 0
        
        # Decode to verify structure
        decoded = jwt.decode(token, 'test-secret', algorithms=['HS256'])
        assert decoded['user_id'] == sample_user_id
        assert decoded['type'] == 'access'
        assert 'exp' in decoded
        assert 'iat' in decoded

    @patch('src.utils.jwt_utils.JWT_SECRET_KEY', 'test-secret')
    @patch('src.utils.jwt_utils.JWT_ALGORITHM', 'HS256')
    def test_generate_access_token_with_custom_expiry(self, sample_user_id):
        """Test access token generation with custom expiry time."""
        custom_expiry = timedelta(minutes=30)
        token = generate_access_token(sample_user_id, expires_delta=custom_expiry)
        
        decoded = jwt.decode(token, 'test-secret', algorithms=['HS256'])
        exp_time = datetime.fromtimestamp(decoded['exp'], tz=timezone.utc)
        iat_time = datetime.fromtimestamp(decoded['iat'], tz=timezone.utc)
        
        assert (exp_time - iat_time) == custom_expiry

    @patch('src.utils.jwt_utils.JWT_SECRET_KEY', 'test-secret')
    @patch('src.utils.jwt_utils.JWT_ALGORITHM', 'HS256')
    def test_generate_access_token_with_additional_claims(self, sample_user_id):
        """Test access token generation with additional claims."""
        additional_claims = {"role": "admin", "permissions": ["read", "write"]}
        token = generate_access_token(sample_user_id, additional_claims=additional_claims)
        
        decoded = jwt.decode(token, 'test-secret', algorithms=['HS256'])
        assert decoded['role'] == 'admin'
        assert decoded['permissions'] == ["read", "write"]

    def test_generate_access_token_invalid_user_id(self):
        """Test access token generation with invalid user ID."""
        with pytest.raises(ValueError, match="User ID cannot be empty"):
            generate_access_token("")
        
        with pytest.raises(ValueError, match="User ID cannot be None"):
            generate_access_token(None)

    def test_generate_access_token_invalid_expiry(self, sample_user_id):
        """Test access token generation with invalid expiry delta."""
        with pytest.raises(ValueError, match="Expiry delta must be positive"):
            generate_access_token(sample_user_id, expires_delta=timedelta(seconds=-1))


class TestGenerateRefreshToken:
    """Test cases for generate_refresh_token function."""

    @patch('src.utils.jwt_utils.JWT_SECRET_KEY', 'test-secret')
    @patch('src.utils.jwt_utils.JWT_ALGORITHM', 'HS256')
    def test_generate_refresh_token_success(self, sample_user_id):
        """Test successful refresh token generation."""
        token = generate_refresh_token(sample_user_id)
        
        assert isinstance(token, str)
        assert len(token) > 0
        
        decoded = jwt.decode(token, 'test-secret', algorithms=['HS256'])
        assert decoded['user_id'] == sample_user_id
        assert decoded['type'] == 'refresh'
        assert 'exp' in decoded
        assert 'iat' in decoded

    @patch('src.utils.jwt_utils.JWT_SECRET_KEY', 'test-secret')
    @patch('src.utils.jwt_utils.JWT_ALGORITHM', 'HS256')
    def test_generate_refresh_token_default_expiry(self, sample_user_id):
        """Test refresh token has longer expiry than access token."""
        refresh_token = generate_refresh_token(sample_user_id)
        access_token = generate_access_token(sample_user_id)
        
        refresh_decoded = jwt.decode(refresh_token, 'test-secret', algorithms=['HS256'])
        access_decoded = jwt.decode(access_token, 'test-secret', algorithms=['HS256'])
        
        assert refresh_decoded['exp'] > access_decoded['exp']

    def test_generate_refresh_token_invalid_user_id(self):
        """Test refresh token generation with invalid user ID."""
        with pytest.raises(ValueError, match="User ID cannot be empty"):
            generate_refresh_token("")


class TestValidateToken:
    """Test cases for validate_token function."""

    @patch('src.utils