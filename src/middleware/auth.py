"""
Authentication middleware for protecting routes and extracting user information from JWT tokens.

This middleware validates JWT tokens, extracts user information, and provides
authentication protection for API endpoints.

Component ID: COMP-012
Semantic Unit: SU-012

Author: ASP Code Agent
"""

import logging
from typing import Optional, Callable, Any
from fastapi import Request, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from src.utils.jwt_utils import decode_jwt_token, JWTError
from src.models.user import User


# Configure logging
logger = logging.getLogger(__name__)

# HTTP Bearer token scheme
security = HTTPBearer(auto_error=False)


class AuthenticationError(Exception):
    """Custom exception for authentication errors."""
    
    def __init__(self, message: str, status_code: int = status.HTTP_401_UNAUTHORIZED):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class AuthMiddleware(BaseHTTPMiddleware):
    """
    Authentication middleware for JWT token validation.
    
    This middleware intercepts requests, validates JWT tokens, and adds
    user information to the request state for protected routes.
    """
    
    def __init__(self, app: Any, protected_paths: Optional[list[str]] = None):
        """
        Initialize authentication middleware.
        
        Args:
            app: FastAPI application instance
            protected_paths: List of path patterns that require authentication
        """
        super().__init__(app)
        self.protected_paths = protected_paths or []
        logger.info("AuthMiddleware initialized with %d protected paths", len(self.protected_paths))
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process request through authentication middleware.
        
        Args:
            request: Incoming HTTP request
            call_next: Next middleware or route handler
            
        Returns:
            Response: HTTP response from downstream handler
            
        Raises:
            HTTPException: If authentication fails for protected routes
        """
        try:
            # Check if path requires authentication
            if self._is_protected_path(request.url.path):
                user = await self._authenticate_request(request)
                request.state.user = user
                request.state.authenticated = True
                logger.debug("Authenticated user %s for path %s", user.email, request.url.path)
            else:
                request.state.user = None
                request.state.authenticated = False
            
            # Continue to next middleware or route handler
            response = await call_next(request)
            return response
            
        except AuthenticationError as e:
            logger.warning("Authentication failed for path %s: %s", request.url.path, e.message)
            raise HTTPException(
                status_code=e.status_code,
                detail=e.message,
                headers={"WWW-Authenticate": "Bearer"}
            )
        except Exception as e:
            logger.error("Unexpected error in auth middleware: %s", str(e))
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error"
            )
    
    def _is_protected_path(self, path: str) -> bool:
        """
        Check if the given path requires authentication.
        
        Args:
            path: Request path to check
            
        Returns:
            bool: True if path requires authentication
        """
        if not self.protected_paths:
            return False
        
        # Check exact matches and wildcard patterns
        for protected_path in self.protected_paths:
            if protected_path.endswith("*"):
                # Wildcard pattern matching
                prefix = protected_path[:-1]
                if path.startswith(prefix):
                    return True
            elif path == protected_path:
                # Exact path match
                return True
        
        return False
    
    async def _authenticate_request(self, request: Request) -> User:
        """
        Authenticate request using JWT token.
        
        Args:
            request: HTTP request to authenticate
            
        Returns:
            User: Authenticated user object
            
        Raises:
            AuthenticationError: If authentication fails
        """
        # Extract authorization header
        authorization = request.headers.get("Authorization")
        if not authorization:
            raise AuthenticationError("Missing authorization header")
        
        # Parse Bearer token
        if not authorization.startswith("Bearer "):
            raise AuthenticationError("Invalid authorization header format")
        
        token = authorization[7:]  # Remove "Bearer " prefix
        if not token:
            raise AuthenticationError("Missing JWT token")
        
        # Validate and decode JWT token
        try:
            payload = decode_jwt_token(token)
        except JWTError as e:
            raise AuthenticationError(f"Invalid JWT token: {str(e)}")
        
        # Extract user information from token payload
        user_id = payload.get("user_id")
        email = payload.get("email")
        
        if not user_id or not email:
            raise AuthenticationError("Invalid token payload: missing user information")
        
        # Create user object from token payload
        user = User(
            id=user_id,
            email=email,
            first_name=payload.get("first_name", ""),
            last_name=payload.get("last_name", ""),
            is_active=payload.get("is_active", True)
        )
        
        return user


def get_current_user(request: Request) -> Optional[User]:
    """
    Get the current authenticated user from request state.
    
    Args:
        request: HTTP request object
        
    Returns:
        User: Current authenticated user or None if not authenticated
    """
    return getattr(request.state, "user", None)


def require_authentication(request: Request) -> User:
    """
    Require authentication and return current user.
    
    Args:
        request: HTTP request object
        
    Returns:
        User: Current authenticated user
        
    Raises:
        HTTPException: If user is not authenticated
    """
    user = get_current_user(request)
    if not user:
        logger.warning("Authentication required but no user found in request state")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    return user


def is_authenticated(request: Request) -> bool:
    """
    Check if the current request is authenticated.
    
    Args:
        request: HTTP request object
        
    Returns:
        bool: True if request is authenticated
    """
    return getattr(request.state, "authenticated", False)


async def extract_token_from_request(request: Request) -> Optional[str]:
    """
    Extract JWT token from request headers.
    
    Args:
        request: HTTP request object
        
    Returns:
        str: JWT token if present, None otherwise
    """
    try:
        authorization = request.headers.get("Authorization")
        if not authorization or not authorization.startswith("Bearer "):
            return None
        
        token = authorization[7:]  # Remove "Bearer " prefix
        return token if token else None
        
    except Exception as e:
        logger.error("Error extracting token from request: %s", str(e))
        return None


def create_auth_middleware(protected_paths: Optional[list[str]] = None) -> type[AuthMiddleware]:
    """
    Factory function to create authentication middleware with configuration.
    
    Args:
        protected_paths: List of path patterns that require authentication
        
    Returns:
        AuthMiddleware: Configured authentication middleware class
    """
    class ConfiguredAuthMiddleware(AuthMiddleware):
        def __init__(self, app: Any):
            super().__init__(app, protected_paths)
    
    return ConfiguredAuthMiddleware