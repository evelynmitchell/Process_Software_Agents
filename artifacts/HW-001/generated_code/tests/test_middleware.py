"""
Unit tests for authentication middleware

Tests token validation, user context injection, and error handling
for the authentication middleware component.

Component ID: COMP-012
Semantic Unit: SU-012

Author: ASP Code Generator
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from fastapi import FastAPI, Request, HTTPException
from fastapi.testclient import TestClient
import jwt
from datetime import datetime, timedelta

from src.middleware.auth import AuthMiddleware, get_current_user, verify_token


class TestAuthMiddleware:
    """Test suite for AuthMiddleware class."""

    @pytest.fixture
    def app(self):
        """Create FastAPI test application."""
        app = FastAPI()
        return app

    @pytest.fixture
    def auth_middleware(self, app):
        """Create AuthMiddleware instance."""
        return AuthMiddleware(app)

    @pytest.fixture
    def mock_request(self):
        """Create mock request object."""
        request = Mock(spec=Request)
        request.headers = {}
        request.state = Mock()
        return request

    @pytest.fixture
    def valid_token(self):
        """Create valid JWT token for testing."""
        payload = {
            "user_id": "123",
            "username": "testuser",
            "email": "test@example.com",
            "exp": datetime.utcnow() + timedelta(hours=1)
        }
        return jwt.encode(payload, "test_secret", algorithm="HS256")

    @pytest.fixture
    def expired_token(self):
        """Create expired JWT token for testing."""
        payload = {
            "user_id": "123",
            "username": "testuser",
            "email": "test@example.com",
            "exp": datetime.utcnow() - timedelta(hours=1)
        }
        return jwt.encode(payload, "test_secret", algorithm="HS256")

    def test_auth_middleware_initialization(self, app):
        """Test that AuthMiddleware initializes correctly."""
        middleware = AuthMiddleware(app)
        assert middleware.app == app
        assert hasattr(middleware, 'dispatch')

    @pytest.mark.asyncio
    async def test_dispatch_with_valid_token(self, auth_middleware, mock_request, valid_token):
        """Test middleware dispatch with valid authorization token."""
        mock_request.headers = {"Authorization": f"Bearer {valid_token}"}
        mock_call_next = AsyncMock(return_value=Mock())
        
        with patch('src.middleware.auth.verify_token') as mock_verify:
            mock_verify.return_value = {
                "user_id": "123",
                "username": "testuser",
                "email": "test@example.com"
            }
            
            response = await auth_middleware.dispatch(mock_request, mock_call_next)
            
            mock_verify.assert_called_once_with(valid_token)
            mock_call_next.assert_called_once_with(mock_request)
            assert hasattr(mock_request.state, 'user')
            assert mock_request.state.user["user_id"] == "123"

    @pytest.mark.asyncio
    async def test_dispatch_without_authorization_header(self, auth_middleware, mock_request):
        """Test middleware dispatch without Authorization header."""
        mock_call_next = AsyncMock(return_value=Mock())
        
        response = await auth_middleware.dispatch(mock_request, mock_call_next)
        
        mock_call_next.assert_called_once_with(mock_request)
        assert not hasattr(mock_request.state, 'user')

    @pytest.mark.asyncio
    async def test_dispatch_with_invalid_token_format(self, auth_middleware, mock_request):
        """Test middleware dispatch with invalid token format."""
        mock_request.headers = {"Authorization": "InvalidFormat token123"}
        mock_call_next = AsyncMock(return_value=Mock())
        
        response = await auth_middleware.dispatch(mock_request, mock_call_next)
        
        mock_call_next.assert_called_once_with(mock_request)
        assert not hasattr(mock_request.state, 'user')

    @pytest.mark.asyncio
    async def test_dispatch_with_expired_token(self, auth_middleware, mock_request, expired_token):
        """Test middleware dispatch with expired token."""
        mock_request.headers = {"Authorization": f"Bearer {expired_token}"}
        mock_call_next = AsyncMock(return_value=Mock())
        
        with patch('src.middleware.auth.verify_token') as mock_verify:
            mock_verify.side_effect = HTTPException(status_code=401, detail="Token expired")
            
            response = await auth_middleware.dispatch(mock_request, mock_call_next)
            
            mock_call_next.assert_called_once_with(mock_request)
            assert not hasattr(mock_request.state, 'user')

    @pytest.mark.asyncio
    async def test_dispatch_with_malformed_token(self, auth_middleware, mock_request):
        """Test middleware dispatch with malformed JWT token."""
        mock_request.headers = {"Authorization": "Bearer malformed.token.here"}
        mock_call_next = AsyncMock(return_value=Mock())
        
        with patch('src.middleware.auth.verify_token') as mock_verify:
            mock_verify.side_effect = HTTPException(status_code=401, detail="Invalid token")
            
            response = await auth_middleware.dispatch(mock_request, mock_call_next)
            
            mock_call_next.assert_called_once_with(mock_request)
            assert not hasattr(mock_request.state, 'user')

    @pytest.mark.asyncio
    async def test_dispatch_preserves_request_state(self, auth_middleware, mock_request, valid_token):
        """Test that middleware preserves existing request state."""
        mock_request.headers = {"Authorization": f"Bearer {valid_token}"}
        mock_request.state.existing_data = "preserved"
        mock_call_next = AsyncMock(return_value=Mock())
        
        with patch('src.middleware.auth.verify_token') as mock_verify:
            mock_verify.return_value = {"user_id": "123", "username": "testuser"}
            
            await auth_middleware.dispatch(mock_request, mock_call_next)
            
            assert mock_request.state.existing_data == "preserved"
            assert hasattr(mock_request.state, 'user')


class TestVerifyToken:
    """Test suite for verify_token function."""

    @pytest.fixture
    def valid_payload(self):
        """Create valid token payload."""
        return {
            "user_id": "123",
            "username": "testuser",
            "email": "test@example.com",
            "exp": datetime.utcnow() + timedelta(hours=1)
        }

    @pytest.fixture
    def expired_payload(self):
        """Create expired token payload."""
        return {
            "user_id": "123",
            "username": "testuser",
            "email": "test@example.com",
            "exp": datetime.utcnow() - timedelta(hours=1)
        }

    def test_verify_token_with_valid_token(self, valid_payload):
        """Test token verification with valid token."""
        token = jwt.encode(valid_payload, "test_secret", algorithm="HS256")
        
        with patch('src.middleware.auth.JWT_SECRET', "test_secret"):
            with patch('src.middleware.auth.JWT_ALGORITHM', "HS256"):
                result = verify_token(token)
                
                assert result["user_id"] == "123"
                assert result["username"] == "testuser"
                assert result["email"] == "test@example.com"

    def test_verify_token_with_expired_token(self, expired_payload):
        """Test token verification with expired token raises HTTPException."""
        token =