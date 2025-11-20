"""
JWT token generation, validation, and decoding utilities.

Provides utilities for creating and validating JWT access and refresh tokens
with proper security practices and error handling.

Component ID: COMP-008
Semantic Unit: SU-008

Author: ASP Code Agent
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional, Union

import jwt
from jwt.exceptions import DecodeError, ExpiredSignatureError, InvalidTokenError


logger = logging.getLogger(__name__)


class JWTError(Exception):
    """Base exception for JWT-related errors."""
    pass


class TokenExpiredError(JWTError):
    """Raised when a JWT token has expired."""
    pass


class TokenInvalidError(JWTError):
    """Raised when a JWT token is invalid or malformed."""
    pass


class JWTUtils:
    """
    JWT token utilities for generating, validating, and decoding tokens.
    
    Supports both access and refresh tokens with configurable expiration times
    and proper security practices.
    """
    
    def __init__(
        self,
        secret_key: str,
        algorithm: str = "HS256",
        access_token_expire_minutes: int = 30,
        refresh_token_expire_days: int = 7
    ) -> None:
        """
        Initialize JWT utilities with configuration.
        
        Args:
            secret_key: Secret key for signing tokens
            algorithm: JWT signing algorithm (default: HS256)
            access_token_expire_minutes: Access token expiration in minutes
            refresh_token_expire_days: Refresh token expiration in days
            
        Raises:
            ValueError: If secret_key is empty or None
        """
        if not secret_key:
            raise ValueError("Secret key cannot be empty or None")
            
        self.secret_key = secret_key
        self.algorithm = algorithm
        self.access_token_expire_minutes = access_token_expire_minutes
        self.refresh_token_expire_days = refresh_token_expire_days
        
        logger.info(
            "JWT utilities initialized with algorithm=%s, "
            "access_expire=%d min, refresh_expire=%d days",
            algorithm, access_token_expire_minutes, refresh_token_expire_days
        )
    
    def generate_access_token(
        self,
        subject: str,
        additional_claims: Optional[Dict[str, Any]] = None,
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """
        Generate a JWT access token.
        
        Args:
            subject: Token subject (typically user ID or username)
            additional_claims: Additional claims to include in token
            expires_delta: Custom expiration time (overrides default)
            
        Returns:
            str: Encoded JWT access token
            
        Raises:
            ValueError: If subject is empty or None
            JWTError: If token generation fails
        """
        if not subject:
            raise ValueError("Subject cannot be empty or None")
            
        try:
            now = datetime.now(timezone.utc)
            
            if expires_delta:
                expire = now + expires_delta
            else:
                expire = now + timedelta(minutes=self.access_token_expire_minutes)
            
            payload = {
                "sub": subject,
                "iat": now,
                "exp": expire,
                "type": "access"
            }
            
            if additional_claims:
                payload.update(additional_claims)
            
            token = jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
            
            logger.debug(
                "Generated access token for subject=%s, expires=%s",
                subject, expire.isoformat()
            )
            
            return token
            
        except Exception as e:
            logger.error("Failed to generate access token: %s", str(e))
            raise JWTError(f"Token generation failed: {str(e)}") from e
    
    def generate_refresh_token(
        self,
        subject: str,
        additional_claims: Optional[Dict[str, Any]] = None,
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """
        Generate a JWT refresh token.
        
        Args:
            subject: Token subject (typically user ID or username)
            additional_claims: Additional claims to include in token
            expires_delta: Custom expiration time (overrides default)
            
        Returns:
            str: Encoded JWT refresh token
            
        Raises:
            ValueError: If subject is empty or None
            JWTError: If token generation fails
        """
        if not subject:
            raise ValueError("Subject cannot be empty or None")
            
        try:
            now = datetime.now(timezone.utc)
            
            if expires_delta:
                expire = now + expires_delta
            else:
                expire = now + timedelta(days=self.refresh_token_expire_days)
            
            payload = {
                "sub": subject,
                "iat": now,
                "exp": expire,
                "type": "refresh"
            }
            
            if additional_claims:
                payload.update(additional_claims)
            
            token = jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
            
            logger.debug(
                "Generated refresh token for subject=%s, expires=%s",
                subject, expire.isoformat()
            )
            
            return token
            
        except Exception as e:
            logger.error("Failed to generate refresh token: %s", str(e))
            raise JWTError(f"Token generation failed: {str(e)}") from e
    
    def decode_token(
        self,
        token: str,
        verify_exp: bool = True,
        verify_signature: bool = True
    ) -> Dict[str, Any]:
        """
        Decode and validate a JWT token.
        
        Args:
            token: JWT token to decode
            verify_exp: Whether to verify token expiration
            verify_signature: Whether to verify token signature
            
        Returns:
            dict: Decoded token payload
            
        Raises:
            ValueError: If token is empty or None
            TokenExpiredError: If token has expired
            TokenInvalidError: If token is invalid or malformed
        """
        if not token:
            raise ValueError("Token cannot be empty or None")
            
        try:
            options = {
                "verify_exp": verify_exp,
                "verify_signature": verify_signature
            }
            
            payload = jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.algorithm],
                options=options
            )
            
            logger.debug(
                "Successfully decoded token for subject=%s",
                payload.get("sub", "unknown")
            )
            
            return payload
            
        except ExpiredSignatureError as e:
            logger.warning("Token has expired: %s", str(e))
            raise TokenExpiredError("Token has expired") from e
            
        except (DecodeError, InvalidTokenError) as e:
            logger.warning("Invalid token: %s", str(e))
            raise TokenInvalidError("Token is invalid or malformed") from e
            
        except Exception as e:
            logger.error("Failed to decode token: %s", str(e))
            raise TokenInvalidError(f"Token decoding failed: {str(e)}") from e
    
    def validate_token(
        self,
        token: str,
        expected_type: Optional[str] = None
    ) -> bool:
        """
        Validate a JWT token without raising exceptions.
        
        Args:
            token: JWT token to validate
            expected_type: Expected token type ("access" or "refresh")
            
        Returns:
            bool: True if token is valid, False otherwise
        """
        try:
            payload = self.decode_token(token)
            
            if expected_type:
                token_type = payload.get("type")
                if token_type != expected_type:
                    logger.warning(
                        "Token type mismatch: expected=%s, actual=%s",
                        expected_type, token_type