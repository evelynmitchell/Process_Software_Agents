"""
FastAPI Authentication Middleware

JWT token validation middleware that extracts and validates JWT tokens from requests,
injects user context, and handles authentication errors.

Component ID: COMP-012
Semantic Unit: SU-012

Author: ASP Code Generator
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
    
    Validates JWT tokens from Authorization header, extracts user information,
    and injects user context into request state for downstream handlers.
    
    Attributes:
        jwt_utils: JWT utility instance for token operations
        excluded_paths: List of paths that bypass authentication
        optional_auth_paths: List of paths where auth is optional
    """
    
    def __init__(
        self,
        app: ASGIApp,
        jwt_utils: JWTUtils,
        excluded_paths: Optional[list[str]] = None,
        optional_auth_paths: Optional[list[str]] = None
    ):
        """
        Initialize authentication middleware.
        
        Args:
            app: ASGI application instance
            jwt_utils: JWT utility for token validation
            excluded_paths: Paths that bypass authentication (default: ["/health", "/docs", "/openapi.json"])
            optional_auth_paths: Paths where authentication is optional
        """
        super().__init__(app)
        self.jwt_utils = jwt_utils
        self.excluded_paths = excluded_paths or ["/health", "/docs", "/openapi.json", "/redoc"]
        self.optional_auth_paths = optional_auth_paths or []
        
        logger.info(
            f"AuthMiddleware initialized with {len(self.excluded_paths)} excluded paths "
            f"and {len(self.optional_auth_paths)} optional auth paths"
        )
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process incoming request through authentication middleware.
        
        Args:
            request: Incoming HTTP request
            call_next: Next middleware/handler in chain
            
        Returns:
            Response: HTTP response from downstream handler or error response
        """
        try:
            # Check if path is excluded from authentication
            if self._is_excluded_path(request.url.path):
                logger.debug(f"Skipping auth for excluded path: {request.url.path}")
                return await call_next(request)
            
            # Extract and validate token
            token = self._extract_token(request)
            user = None
            
            if token:
                try:
                    user = await self._validate_token(token)
                    logger.debug(f"Successfully authenticated user: {user.id}")
                except AuthenticationError as e:
                    if not self._is_optional_auth_path(request.url.path):
                        logger.warning(f"Authentication failed for {request.url.path}: {e.message}")
                        return self._create_error_response(e.message, e.status_code)
                    logger.debug(f"Optional auth failed for {request.url.path}: {e.message}")
            elif not self._is_optional_auth_path(request.url.path):
                logger.warning(f"No token provided for protected path: {request.url.path}")
                return self._create_error_response(
                    "Authentication required", 
                    status.HTTP_401_UNAUTHORIZED
                )
            
            # Inject user context into request state
            request.state.user = user
            request.state.authenticated = user is not None
            request.state.auth_timestamp = datetime.utcnow()
            
            # Continue to next handler
            response = await call_next(request)
            
            # Add authentication headers to response
            if user:
                response.headers["X-User-ID"] = str(user.id)
                response.headers["X-Authenticated"] = "true"
            else:
                response.headers["X-Authenticated"] = "false"
            
            return response
            
        except Exception as e:
            logger.error(f"Unexpected error in auth middleware: {str(e)}", exc_info=True)
            return self._create_error_response(
                "Internal authentication error",
                status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def _is_excluded_path(self, path: str) -> bool:
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
            if normalized_path == normalized_excluded or normalized_path.startswith(normalized_excluded + '/'):
                return True
        
        return False
    
    def _is_optional_auth_path(self, path: str) -> bool:
        """
        Check if request path has optional authentication.
        
        Args:
            path: Request URL path
            
        Returns:
            bool: True if authentication is optional for this path
        """
        # Normalize path by removing trailing slash
        normalized_path = path.rstrip('/')
        
        for optional_path in self.optional_auth_paths:
            normalized_optional = optional_path.rstrip('/')
            if normalized_path == normalized_optional or normalized_path.startswith(normalized_optional + '/'):
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
        
        # Validate Authorization header format
        if not auth_header.startswith("Bearer "):
            raise AuthenticationError(
                "Invalid Authorization header format. Expected 'Bearer <token>'",
                status.HTTP_401_UNAUTHORIZED
            )
        
        # Extract token part
        token = auth_header[7:]  # Remove "Bearer " prefix
        
        if not token.strip():
            raise AuthenticationError(
                "Empty token in Authorization header",
                status.HTTP_401_UNAUTHORIZED
            )
        
        return token.strip()
    
    async def _validate_token(self, token: str) -> User:
        """
        Validate JWT token and extract user information.
        
        Args:
            token: JWT token string
            
        Returns:
            User: Authenticated user object
            
        Raises:
            AuthenticationError: If token is invalid or expired
        """
        try:
            # Decode and validate token
            payload = self.jwt_utils.decode_token(token)
            
            # Extract user information from token payload
            user_id = payload.get("user_id")
            email = payload.get("email")
            username = payload.get("username")
            
            if not user_id:
                raise AuthenticationError(
                    "Invalid token: missing user_id",
                    status.HTTP_401_UNAUTHORIZED
                )
            
            # Create user object from token payload
            user = User(