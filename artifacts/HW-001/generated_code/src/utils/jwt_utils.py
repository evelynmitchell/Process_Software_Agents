"""
JWT token utilities for authentication and authorization.

Provides functions for generating, validating, decoding, and refreshing JWT tokens
using the python-jose library with RS256 algorithm.

Component ID: COMP-008
Semantic Unit: SU-008

Author: ASP Code Agent
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional, Union

from jose import JWTError, jwt
from jose.constants import ALGORITHMS


logger = logging.getLogger(__name__)


class JWTConfig:
    """Configuration class for JWT token settings."""
    
    def __init__(
        self,
        secret_key: str,
        algorithm: str = ALGORITHMS.HS256,
        access_token_expire_minutes: int = 30,
        refresh_token_expire_days: int = 7,
        issuer: str = "hello-world-api",
        audience: str = "hello-world-users"
    ):
        """
        Initialize JWT configuration.
        
        Args:
            secret_key: Secret key for signing tokens
            algorithm: JWT signing algorithm (default: HS256)
            access_token_expire_minutes: Access token expiration in minutes
            refresh_token_expire_days: Refresh token expiration in days
            issuer: Token issuer identifier
            audience: Token audience identifier
        """
        self.secret_key = secret_key
        self.algorithm = algorithm
        self.access_token_expire_minutes = access_token_expire_minutes
        self.refresh_token_expire_days = refresh_token_expire_days
        self.issuer = issuer
        self.audience = audience


class JWTTokenError(Exception):
    """Base exception for JWT token operations."""
    pass


class JWTTokenExpiredError(JWTTokenError):
    """Exception raised when JWT token has expired."""
    pass


class JWTTokenInvalidError(JWTTokenError):
    """Exception raised when JWT token is invalid."""
    pass


class JWTUtils:
    """Utility class for JWT token operations."""
    
    def __init__(self, config: JWTConfig):
        """
        Initialize JWT utilities with configuration.
        
        Args:
            config: JWT configuration object
        """
        self.config = config
    
    def generate_access_token(
        self,
        subject: str,
        additional_claims: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Generate a new access token.
        
        Args:
            subject: Token subject (typically user ID)
            additional_claims: Optional additional claims to include
            
        Returns:
            str: Encoded JWT access token
            
        Raises:
            JWTTokenError: If token generation fails
            
        Example:
            >>> jwt_utils = JWTUtils(config)
            >>> token = jwt_utils.generate_access_token("user123")
            >>> isinstance(token, str)
            True
        """
        try:
            now = datetime.now(timezone.utc)
            expire = now + timedelta(minutes=self.config.access_token_expire_minutes)
            
            payload = {
                "sub": subject,
                "iat": now,
                "exp": expire,
                "iss": self.config.issuer,
                "aud": self.config.audience,
                "type": "access"
            }
            
            if additional_claims:
                payload.update(additional_claims)
            
            token = jwt.encode(
                payload,
                self.config.secret_key,
                algorithm=self.config.algorithm
            )
            
            logger.info(f"Generated access token for subject: {subject}")
            return token
            
        except Exception as e:
            logger.error(f"Failed to generate access token: {str(e)}")
            raise JWTTokenError(f"Token generation failed: {str(e)}") from e
    
    def generate_refresh_token(
        self,
        subject: str,
        additional_claims: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Generate a new refresh token.
        
        Args:
            subject: Token subject (typically user ID)
            additional_claims: Optional additional claims to include
            
        Returns:
            str: Encoded JWT refresh token
            
        Raises:
            JWTTokenError: If token generation fails
            
        Example:
            >>> jwt_utils = JWTUtils(config)
            >>> token = jwt_utils.generate_refresh_token("user123")
            >>> isinstance(token, str)
            True
        """
        try:
            now = datetime.now(timezone.utc)
            expire = now + timedelta(days=self.config.refresh_token_expire_days)
            
            payload = {
                "sub": subject,
                "iat": now,
                "exp": expire,
                "iss": self.config.issuer,
                "aud": self.config.audience,
                "type": "refresh"
            }
            
            if additional_claims:
                payload.update(additional_claims)
            
            token = jwt.encode(
                payload,
                self.config.secret_key,
                algorithm=self.config.algorithm
            )
            
            logger.info(f"Generated refresh token for subject: {subject}")
            return token
            
        except Exception as e:
            logger.error(f"Failed to generate refresh token: {str(e)}")
            raise JWTTokenError(f"Token generation failed: {str(e)}") from e
    
    def decode_token(
        self,
        token: str,
        verify_expiration: bool = True
    ) -> Dict[str, Any]:
        """
        Decode and validate a JWT token.
        
        Args:
            token: JWT token to decode
            verify_expiration: Whether to verify token expiration
            
        Returns:
            Dict[str, Any]: Decoded token payload
            
        Raises:
            JWTTokenExpiredError: If token has expired
            JWTTokenInvalidError: If token is invalid
            
        Example:
            >>> jwt_utils = JWTUtils(config)
            >>> payload = jwt_utils.decode_token(token)
            >>> "sub" in payload
            True
        """
        try:
            options = {
                "verify_exp": verify_expiration,
                "verify_aud": True,
                "verify_iss": True
            }
            
            payload = jwt.decode(
                token,
                self.config.secret_key,
                algorithms=[self.config.algorithm],
                audience=self.config.audience,
                issuer=self.config.issuer,
                options=options
            )
            
            logger.debug(f"Successfully decoded token for subject: {payload.get('sub')}")
            return payload
            
        except jwt.ExpiredSignatureError as e:
            logger.warning(f"Token expired: {str(e)}")
            raise JWTTokenExpiredError("Token has expired") from e
        except JWTError as e:
            logger.warning(f"Invalid token: {str(e)}")
            raise JWTTokenInvalidError(f"Invalid token: {str(e)}") from e
        except Exception as e:
            logger.error(f"Token decode error: {str(e)}")
            raise JWTTokenInvalidError(f"Token decode failed: {str(e)}") from e
    
    def validate_token(self, token: str) -> bool:
        """
        Validate a JWT token without decoding.
        
        Args:
            token: JWT token to validate
            
        Returns:
            bool: True if token is valid, False otherwise
            
        Example:
            >>> jwt_utils = JWTUtils(config)
            >>> jwt_utils.validate_token(valid_token)
            True
            >>> jwt_utils.validate_token("invalid_token")
            False
        """
        try:
            self.decode_token(token)
            return True
        except (JWTTokenExpiredError, JWTTokenInvalidError):
            return False
    
    def get_token_subject(self, token: str