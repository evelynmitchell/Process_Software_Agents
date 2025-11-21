"""
FastAPI Authentication Middleware

JWT token validation middleware that extracts and validates JWT tokens from requests,
injects user context into request state, and handles authentication errors.

Component ID: COMP-012
Semantic Unit: SU-012

Author: ASP Code Agent
"""

import logging
from typing import Optional, Callable, Any
from datetime import datetime

from fastapi import Request, Response, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from src.utils.jwt_utils import JWTUtils, JWTError, TokenExpiredError, InvalidTokenError
from src.models.user import User


logger = logging.getLogger(__name__)


class AuthenticationError(Exception):
    """Custom exception for authentication failures."""
    
    def __init__(self, message: str, status_code: int = status.HTTP_401_UNAUTHORIZED):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class AuthMiddleware(BaseHTTPMiddleware):
    """
    JWT Authentication Middleware for FastAPI applications.
    
    This middleware validates JWT tokens from Authorization headers,
    extracts user information, and injects user context into request state.
    Handles token validation errors and provides proper HTTP responses.
    """
    
    def __init__(
        self,
        app: ASGIApp,
        jwt_utils: JWTUtils,
        excluded_paths: Optional[list[str]] = None,
        require_auth: bool = True
    ):
        """
        Initialize authentication middleware.
        
        Args:
            app: ASGI application instance
            jwt_utils: JWT utility instance for token operations
            excluded_paths: List of paths that don't require authentication
            require_auth: Whether authentication is required by default
        """
        super().__init__(app)
        self.jwt_utils = jwt_utils
        self.excluded_paths = excluded_paths or ["/health", "/docs", "/redoc", "/openapi.json"]
        self.require_auth = require_auth
        
        logger.info(
            f"AuthMiddleware initialized with {len(self.excluded_paths)} excluded paths"
        )
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process incoming request and validate authentication.
        
        Args:
            request: Incoming HTTP request
            call_next: Next middleware/handler in chain
            
        Returns:
            Response: HTTP response from downstream handler or error response
        """
        try:
            # Check if path is excluded from authentication
            if self._is_path_excluded(request.url.path):
                logger.debug(f"Skipping auth for excluded path: {request.url.path}")
                return await call_next(request)
            
            # Extract and validate JWT token
            token = self._extract_token(request)
            
            if not token:
                if self.require_auth:
                    return self._create_error_response(
                        "Missing authentication token",
                        status.HTTP_401_UNAUTHORIZED,
                        "MISSING_TOKEN"
                    )
                else:
                    # Allow request without token if auth not required
                    request.state.user = None
                    request.state.authenticated = False
                    return await call_next(request)
            
            # Validate token and extract user information
            user = await self._validate_token_and_get_user(token)
            
            # Inject user context into request state
            request.state.user = user
            request.state.authenticated = True
            request.state.token = token
            
            logger.debug(f"Authenticated user {user.id} for path: {request.url.path}")
            
            # Continue to next handler
            response = await call_next(request)
            
            # Add authentication headers to response
            self._add_auth_headers(response, user)
            
            return response
            
        except AuthenticationError as e:
            logger.warning(f"Authentication failed: {e.message}")
            return self._create_error_response(
                e.message,
                e.status_code,
                "AUTHENTICATION_FAILED"
            )
        except Exception as e:
            logger.error(f"Unexpected error in auth middleware: {str(e)}", exc_info=True)
            return self._create_error_response(
                "Internal authentication error",
                status.HTTP_500_INTERNAL_SERVER_ERROR,
                "INTERNAL_ERROR"
            )
    
    def _is_path_excluded(self, path: str) -> bool:
        """
        Check if request path is excluded from authentication.
        
        Args:
            path: Request URL path
            
        Returns:
            bool: True if path is excluded from authentication
        """
        # Normalize path by removing trailing slash
        normalized_path = path.rstrip('/')
        
        for excluded_path in self.excluded_paths:
            normalized_excluded = excluded_path.rstrip('/')
            
            # Exact match or prefix match for paths ending with /*
            if normalized_excluded.endswith('/*'):
                prefix = normalized_excluded[:-2]
                if normalized_path.startswith(prefix):
                    return True
            elif normalized_path == normalized_excluded:
                return True
        
        return False
    
    def _extract_token(self, request: Request) -> Optional[str]:
        """
        Extract JWT token from Authorization header.
        
        Args:
            request: HTTP request object
            
        Returns:
            Optional[str]: JWT token string or None if not found
            
        Raises:
            AuthenticationError: If Authorization header format is invalid
        """
        auth_header = request.headers.get("Authorization")
        
        if not auth_header:
            return None
        
        # Check for Bearer token format
        if not auth_header.startswith("Bearer "):
            raise AuthenticationError(
                "Invalid authorization header format. Expected 'Bearer <token>'",
                status.HTTP_401_UNAUTHORIZED
            )
        
        # Extract token part
        token = auth_header[7:].strip()  # Remove "Bearer " prefix
        
        if not token:
            raise AuthenticationError(
                "Empty token in authorization header",
                status.HTTP_401_UNAUTHORIZED
            )
        
        return token
    
    async def _validate_token_and_get_user(self, token: str) -> User:
        """
        Validate JWT token and extract user information.
        
        Args:
            token: JWT token string
            
        Returns:
            User: User object with validated information
            
        Raises:
            AuthenticationError: If token is invalid or user not found
        """
        try:
            # Decode and validate JWT token
            payload = self.jwt_utils.decode_token(token)
            
            # Extract user information from token payload
            user_id = payload.get("user_id")
            username = payload.get("username")
            email = payload.get("email")
            roles = payload.get("roles", [])
            
            if not user_id:
                raise AuthenticationError(
                    "Invalid token: missing user_id",
                    status.HTTP_401_UNAUTHORIZED
                )
            
            # Create user object from token payload
            user = User(
                id=user_id,
                username=username,
                email=email,
                roles=roles,
                is_active=True,
                last_login=datetime.utcnow()
            )
            
            # Validate user is still active (could check database here)
            if not self._is_user_active(user):
                raise AuthenticationError(
                    "User account is inactive",
                    status.HTTP_401_UNAUTHORIZED
                )
            
            return user
            
        except TokenExpiredError:
            raise AuthenticationError(
                "Token has expired",
                status.HTTP_401_UNAUTHORIZED
            )
        except InvalidTokenError as e:
            raise AuthenticationError(
                f"Invalid token: {str(e)}",
                status.HTTP_401_UNAUTHORIZED
            )
        except JWTError as e:
            raise AuthenticationError(