"""
Unit tests for authentication middleware

Tests JWT token validation, expiration handling, and missing token scenarios.

Component ID: COMP-012
Semantic Unit: SU-012

Author: ASP Code Agent
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta, timezone
import jwt
from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse

from src.middleware.auth import AuthMiddleware, verify_token, get_current_user


class TestAuthMiddleware:
    """Test cases for AuthMiddleware class."""

    @pytest.fixture
    def auth_middleware(self):
        """Create AuthMiddleware instance for testing."""
        app = Mock()
        return AuthMiddleware(app)

    @pytest.fixture
    def mock_request(self):
        """Create mock request object."""
        request = Mock(spec=Request)
        request.headers = {}
        request.url.path = "/api/test"
        request.method = "GET"
        return request

    @pytest.fixture
    def valid_token(self):
        """Create valid JWT token for testing."""
        payload = {
            "sub": "test_user",
            "exp": datetime.now(timezone.utc) + timedelta(hours=1),
            "iat": datetime.now(timezone.utc),
            "user_id": "123",
            "email": "test@example.com"
        }
        return jwt.encode(payload, "test_secret", algorithm="HS256")

    @pytest.fixture
    def expired_token(self):
        """Create expired JWT token for testing."""
        payload = {
            "sub": "test_user",
            "exp": datetime.now(timezone.utc) - timedelta(hours=1),
            "iat": datetime.now(timezone.utc) - timedelta(hours=2),
            "user_id": "123",
            "email": "test@example.com"
        }
        return jwt.encode(payload, "test_secret", algorithm="HS256")

    @pytest.fixture
    def invalid_token(self):
        """Create invalid JWT token for testing."""
        return "invalid.jwt.token"

    @pytest.mark.asyncio
    async def test_middleware_allows_public_endpoints(self, auth_middleware, mock_request):
        """Test that middleware allows access to public endpoints without token."""
        mock_request.url.path = "/health"
        mock_call_next = Mock()
        mock_response = Mock()
        mock_call_next.return_value = mock_response

        result = await auth_middleware.dispatch(mock_request, mock_call_next)

        assert result == mock_response
        mock_call_next.assert_called_once_with(mock_request)

    @pytest.mark.asyncio
    async def test_middleware_allows_docs_endpoints(self, auth_middleware, mock_request):
        """Test that middleware allows access to documentation endpoints."""
        mock_request.url.path = "/docs"
        mock_call_next = Mock()
        mock_response = Mock()
        mock_call_next.return_value = mock_response

        result = await auth_middleware.dispatch(mock_request, mock_call_next)

        assert result == mock_response
        mock_call_next.assert_called_once_with(mock_request)

    @pytest.mark.asyncio
    async def test_middleware_blocks_protected_endpoint_without_token(self, auth_middleware, mock_request):
        """Test that middleware blocks protected endpoints when no token provided."""
        mock_request.url.path = "/api/protected"
        mock_call_next = Mock()

        result = await auth_middleware.dispatch(mock_request, mock_call_next)

        assert isinstance(result, JSONResponse)
        assert result.status_code == 401
        mock_call_next.assert_not_called()

    @pytest.mark.asyncio
    @patch('src.middleware.auth.verify_token')
    async def test_middleware_allows_valid_token(self, mock_verify, auth_middleware, mock_request, valid_token):
        """Test that middleware allows access with valid token."""
        mock_request.headers = {"Authorization": f"Bearer {valid_token}"}
        mock_request.url.path = "/api/protected"
        mock_verify.return_value = {"user_id": "123", "email": "test@example.com"}
        mock_call_next = Mock()
        mock_response = Mock()
        mock_call_next.return_value = mock_response

        result = await auth_middleware.dispatch(mock_request, mock_call_next)

        assert result == mock_response
        mock_call_next.assert_called_once_with(mock_request)
        mock_verify.assert_called_once_with(valid_token)

    @pytest.mark.asyncio
    @patch('src.middleware.auth.verify_token')
    async def test_middleware_blocks_expired_token(self, mock_verify, auth_middleware, mock_request, expired_token):
        """Test that middleware blocks access with expired token."""
        mock_request.headers = {"Authorization": f"Bearer {expired_token}"}
        mock_request.url.path = "/api/protected"
        mock_verify.side_effect = HTTPException(status_code=401, detail="Token expired")
        mock_call_next = Mock()

        result = await auth_middleware.dispatch(mock_request, mock_call_next)

        assert isinstance(result, JSONResponse)
        assert result.status_code == 401
        mock_call_next.assert_not_called()

    @pytest.mark.asyncio
    @patch('src.middleware.auth.verify_token')
    async def test_middleware_blocks_invalid_token(self, mock_verify, auth_middleware, mock_request, invalid_token):
        """Test that middleware blocks access with invalid token."""
        mock_request.headers = {"Authorization": f"Bearer {invalid_token}"}
        mock_request.url.path = "/api/protected"
        mock_verify.side_effect = HTTPException(status_code=401, detail="Invalid token")
        mock_call_next = Mock()

        result = await auth_middleware.dispatch(mock_request, mock_call_next)

        assert isinstance(result, JSONResponse)
        assert result.status_code == 401
        mock_call_next.assert_not_called()

    @pytest.mark.asyncio
    async def test_middleware_handles_malformed_authorization_header(self, auth_middleware, mock_request):
        """Test that middleware handles malformed Authorization header."""
        mock_request.headers = {"Authorization": "InvalidFormat"}
        mock_request.url.path = "/api/protected"
        mock_call_next = Mock()

        result = await auth_middleware.dispatch(mock_request, mock_call_next)

        assert isinstance(result, JSONResponse)
        assert result.status_code == 401
        mock_call_next.assert_not_called()

    @pytest.mark.asyncio
    async def test_middleware_handles_empty_bearer_token(self, auth_middleware, mock_request):
        """Test that middleware handles empty Bearer token."""
        mock_request.headers = {"Authorization": "Bearer "}
        mock_request.url.path = "/api/protected"
        mock_call_next = Mock()

        result = await auth_middleware.dispatch(mock_request, mock_call_next)

        assert isinstance(result, JSONResponse)
        assert result.status_code == 401
        mock_call_next.assert_not_called()


class TestVerifyToken:
    """Test cases for verify_token function."""

    @pytest.fixture
    def valid_payload(self):
        """Create valid token payload."""
        return {
            "sub": "test_user",
            "exp": datetime.now(timezone.utc) + timedelta(hours=1),
            "iat": datetime.now(timezone.utc),
            "user_id": "123",
            "email": "test@example.com"
        }

    @pytest.fixture
    def expired_payload(self):
        """Create expired token payload."""
        return {
            "sub": "test_user