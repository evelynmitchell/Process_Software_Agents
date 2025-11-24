"""
JWT token generation, validation, decoding utilities with expiration handling and security features.

This module provides comprehensive JWT token management including secure token generation,
validation with expiration checks, and decoding with proper error handling.

Component ID: COMP-008
Semantic Unit: SU-008

Author: ASP Code Agent
"""

import hashlib
import hmac
import json
import logging
import secrets
import time
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional, Union

# Configure logging
logger = logging.getLogger(__name__)


class JWTError(Exception):
    """Base exception for JWT-related errors."""
    pass


class JWTExpiredError(JWTError):
    """Exception raised when JWT token has expired."""
    pass


class JWTInvalidError(JWTError):
    """Exception raised when JWT token is invalid or malformed."""
    pass


class JWTSignatureError(JWTError):
    """Exception raised when JWT signature verification fails."""
    pass


class JWTUtils:
    """
    JWT token utilities for generation, validation, and decoding.
    
    Provides secure JWT token management with HMAC-SHA256 signing,
    expiration handling, and comprehensive validation.
    """
    
    def __init__(self, secret_key: str, default_expiry_hours: int = 24) -> None:
        """
        Initialize JWT utilities with secret key and default expiry.
        
        Args:
            secret_key: Secret key for signing tokens (minimum 32 characters)
            default_expiry_hours: Default token expiry time in hours
            
        Raises:
            ValueError: If secret key is too short or invalid
        """
        if not secret_key or len(secret_key) < 32:
            raise ValueError("Secret key must be at least 32 characters long")
        
        self.secret_key = secret_key.encode('utf-8')
        self.default_expiry_hours = default_expiry_hours
        self.algorithm = 'HS256'
        
        logger.info("JWT utilities initialized with %d hour default expiry", default_expiry_hours)
    
    def generate_token(
        self, 
        payload: Dict[str, Any], 
        expiry_hours: Optional[int] = None,
        include_jti: bool = True
    ) -> str:
        """
        Generate a JWT token with the given payload.
        
        Args:
            payload: Dictionary containing token claims
            expiry_hours: Token expiry time in hours (uses default if None)
            include_jti: Whether to include a unique token ID (jti claim)
            
        Returns:
            str: Encoded JWT token
            
        Raises:
            ValueError: If payload is invalid
            JWTError: If token generation fails
        """
        if not isinstance(payload, dict):
            raise ValueError("Payload must be a dictionary")
        
        try:
            # Create header
            header = {
                'typ': 'JWT',
                'alg': self.algorithm
            }
            
            # Create payload with standard claims
            now = datetime.now(timezone.utc)
            expiry_time = expiry_hours or self.default_expiry_hours
            exp_time = now + timedelta(hours=expiry_time)
            
            token_payload = payload.copy()
            token_payload.update({
                'iat': int(now.timestamp()),  # Issued at
                'exp': int(exp_time.timestamp()),  # Expiration time
                'nbf': int(now.timestamp())  # Not before
            })
            
            # Add unique token ID if requested
            if include_jti:
                token_payload['jti'] = self._generate_jti()
            
            # Encode header and payload
            encoded_header = self._base64url_encode(json.dumps(header, separators=(',', ':')))
            encoded_payload = self._base64url_encode(json.dumps(token_payload, separators=(',', ':')))
            
            # Create signature
            message = f"{encoded_header}.{encoded_payload}"
            signature = self._create_signature(message)
            encoded_signature = self._base64url_encode(signature)
            
            token = f"{message}.{encoded_signature}"
            
            logger.debug("Generated JWT token with expiry: %s", exp_time.isoformat())
            return token
            
        except Exception as e:
            logger.error("Failed to generate JWT token: %s", str(e))
            raise JWTError(f"Token generation failed: {str(e)}") from e
    
    def validate_token(self, token: str, verify_expiry: bool = True) -> Dict[str, Any]:
        """
        Validate and decode a JWT token.
        
        Args:
            token: JWT token string to validate
            verify_expiry: Whether to check token expiration
            
        Returns:
            Dict[str, Any]: Decoded token payload
            
        Raises:
            JWTInvalidError: If token format is invalid
            JWTSignatureError: If signature verification fails
            JWTExpiredError: If token has expired
        """
        if not token or not isinstance(token, str):
            raise JWTInvalidError("Token must be a non-empty string")
        
        try:
            # Split token into parts
            parts = token.split('.')
            if len(parts) != 3:
                raise JWTInvalidError("Token must have exactly 3 parts separated by dots")
            
            encoded_header, encoded_payload, encoded_signature = parts
            
            # Verify signature
            message = f"{encoded_header}.{encoded_payload}"
            if not self._verify_signature(message, encoded_signature):
                raise JWTSignatureError("Token signature verification failed")
            
            # Decode header and payload
            header = json.loads(self._base64url_decode(encoded_header))
            payload = json.loads(self._base64url_decode(encoded_payload))
            
            # Verify header
            if header.get('typ') != 'JWT' or header.get('alg') != self.algorithm:
                raise JWTInvalidError("Invalid token header")
            
            # Verify expiration if requested
            if verify_expiry:
                self._verify_expiration(payload)
            
            # Verify not-before claim
            self._verify_not_before(payload)
            
            logger.debug("Successfully validated JWT token")
            return payload
            
        except (JWTError, json.JSONDecodeError) as e:
            logger.warning("JWT validation failed: %s", str(e))
            raise
        except Exception as e:
            logger.error("Unexpected error during JWT validation: %s", str(e))
            raise JWTInvalidError(f"Token validation failed: {str(e)}") from e
    
    def decode_token_unsafe(self, token: str) -> Dict[str, Any]:
        """
        Decode a JWT token without validation (for debugging/inspection only).
        
        WARNING: This method does not verify the token signature or expiration.
        Only use for debugging or when you need to inspect an expired token.
        
        Args:
            token: JWT token string to decode
            
        Returns:
            Dict[str, Any]: Decoded token payload
            
        Raises:
            JWTInvalidError: If token format is invalid
        """
        if not token or not isinstance(token, str):
            raise JWTInvalidError("Token must be a non-empty string")
        
        try:
            parts = token.split('.')
            if len(parts) != 3:
                raise JWTInvalidError("Token must have exactly 3 parts separated by dots")
            
            encoded_payload = parts[1]
            payload = json.loads(self._base64url_decode(encoded_payload))
            
            logger.debug("Decoded JWT token payload (unsafe)")
            return payload
            
        except (json.JSONDecodeError, Exception) as e:
            logger.error("Failed to decode JWT token: %s", str(e))
            raise JWTInvalidError(f"Token decoding faile