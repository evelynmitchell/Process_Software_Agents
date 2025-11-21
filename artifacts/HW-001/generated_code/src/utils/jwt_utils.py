"""
JWT token utilities for authentication and authorization.

Provides functions for generating, validating, decoding, and refreshing JWT tokens
using the python-jose library with RS256 algorithm.

Component ID: COMP-008
Semantic Unit: SU-008

Author: ASP Code Agent
"""

import os
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any, Union

from jose import JWTError, jwt
from jose.constants import ALGORITHMS


# Configure logging
logger = logging.getLogger(__name__)

# JWT Configuration
JWT_ALGORITHM = ALGORITHMS.RS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES = 30
JWT_REFRESH_TOKEN_EXPIRE_DAYS = 7
JWT_ISSUER = "hello-world-api"
JWT_AUDIENCE = "hello-world-users"

# Default RSA keys (in production, these should be loaded from environment variables)
DEFAULT_PRIVATE_KEY = """-----BEGIN RSA PRIVATE KEY-----
MIIEpAIBAAKCAQEA4f5wg5l2hKsTeNem/V41fGnJm6gOdrj8ym3rFkEjWT2btNjcIBFu5d2gcfQQWd0JurplakZfFNNmvl/Y8ZtaD5S/TQYhqvNHSBRiley5OEXEgdtAjmDcYnRr6nK4hpDdGFKoInkRiHxpK7iosKI2v2MqQQhJNADEpd7L7jdqGYsFRN6bzRQi6/+4wjd4ptVAh6kapbptu5Mxc6+rkgJNrxXHd2qN5PUFjYjVvQaaqBdHFNehwgiw5SIkpX/rJ3/AgMBAAECggEBAJGRw/3AqT7hOdNqBPnM3a9EX8xMZpqbaN4fWeLjwpHtK9kTjnFHRgbhTrfB5inQiLlOWM2HLrQ8UVdSZcGy2HNUVZ2lxWw2D8MA8EqaAiQqfxgB7jfT1LN+cozadoABuKdVrfD6ki4n2h5+8P5Io1rI4ZHdgRdOjHdNlNNjuQWiEiKvMXZnxtK/wJlyfD8MldVEz4PqD5PaHMXcMU5YQxSN8EMwjVcaEeD0xhzbNz6Y5rnqiMeGmB1+24JdGVQBpw==
-----END RSA PRIVATE KEY-----"""

DEFAULT_PUBLIC_KEY = """-----BEGIN PUBLIC KEY-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEA4f5wg5l2hKsTeNem/V41fGnJm6gOdrj8ym3rFkEjWT2btNjcIBFu5d2gcfQQWd0JurplakZfFNNmvl/Y8ZtaD5S/TQYhqvNHSBRiley5OEXEgdtAjmDcYnRr6nK4hpDdGFKoInkRiHxpK7iosKI2v2MqQQhJNADEpd7L7jdqGYsFRN6bzRQi6/+4wjd4ptVAh6kapbptu5Mxc6+rkgJNrxXHd2qN5PUFjYjVvQaaqBdHFNehwgiw5SIkpX/rJ3/AgMBAAE=
-----END PUBLIC KEY-----"""


class JWTError(Exception):
    """Custom JWT error for token-related exceptions."""
    pass


class TokenExpiredError(JWTError):
    """Raised when a JWT token has expired."""
    pass


class TokenInvalidError(JWTError):
    """Raised when a JWT token is invalid or malformed."""
    pass


def get_private_key() -> str:
    """
    Get the RSA private key for signing JWT tokens.
    
    Returns:
        str: RSA private key in PEM format
        
    Raises:
        JWTError: If private key is not available or invalid
    """
    try:
        private_key = os.getenv("JWT_PRIVATE_KEY", DEFAULT_PRIVATE_KEY)
        if not private_key or not private_key.strip():
            raise JWTError("JWT private key is not configured")
        return private_key.strip()
    except Exception as e:
        logger.error(f"Failed to load JWT private key: {e}")
        raise JWTError(f"Failed to load JWT private key: {e}")


def get_public_key() -> str:
    """
    Get the RSA public key for verifying JWT tokens.
    
    Returns:
        str: RSA public key in PEM format
        
    Raises:
        JWTError: If public key is not available or invalid
    """
    try:
        public_key = os.getenv("JWT_PUBLIC_KEY", DEFAULT_PUBLIC_KEY)
        if not public_key or not public_key.strip():
            raise JWTError("JWT public key is not configured")
        return public_key.strip()
    except Exception as e:
        logger.error(f"Failed to load JWT public key: {e}")
        raise JWTError(f"Failed to load JWT public key: {e}")


def get_current_timestamp() -> datetime:
    """
    Get the current UTC timestamp.
    
    Returns:
        datetime: Current UTC timestamp
    """
    return datetime.now(timezone.utc)


def generate_access_token(
    user_id: str,
    email: str,
    roles: Optional[list[str]] = None,
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    Generate a JWT access token for user authentication.
    
    Args:
        user_id: Unique user identifier
        email: User email address
        roles: List of user roles/permissions
        expires_delta: Custom expiration time (defaults to 30 minutes)
        
    Returns:
        str: Encoded JWT access token
        
    Raises:
        JWTError: If token generation fails
        ValueError: If required parameters are invalid
    """
    if not user_id or not isinstance(user_id, str):
        raise ValueError("user_id must be a non-empty string")
    
    if not email or not isinstance(email, str):
        raise ValueError("email must be a non-empty string")
    
    if roles is None:
        roles = []
    
    if not isinstance(roles, list):
        raise ValueError("roles must be a list")
    
    try:
        now = get_current_timestamp()
        
        if expires_delta is None:
            expires_delta = timedelta(minutes=JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
        
        expire = now + expires_delta
        
        payload = {
            "sub": user_id,
            "email": email,
            "roles": roles,
            "type": "access",
            "iat": int(now.timestamp()),
            "exp": int(expire.timestamp()),
            "iss": JWT_ISSUER,
            "aud": JWT_AUDIENCE,
        }
        
        private_key = get_private_key()
        token = jwt.encode(payload, private_key, algorithm=JWT_ALGORITHM)
        
        logger.info(f"Generated access token for user