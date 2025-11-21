"""
JWT token generation, validation, decoding utilities with expiration handling and security features.

This module provides comprehensive JWT token management including secure token generation,
validation with expiration checking, and decoding with proper error handling.

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
from base64 import urlsafe_b64decode, urlsafe_b64encode
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
            default_expiry_hours: Default token expiry in hours
            
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
            payload: Token payload data
            expiry_hours: Token expiry in hours (uses default if None)
            include_jti: Whether to include unique token ID (jti claim)
            
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
            expiry_time = now + timedelta(hours=expiry_hours or self.default_expiry_hours)
            
            token_payload = payload.copy()
            token_payload.update({
                'iat': int(now.timestamp()),  # Issued at
                'exp': int(expiry_time.timestamp()),  # Expiration time
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
            
            # Combine all parts
            token = f"{message}.{signature}"
            
            logger.debug("Generated JWT token with expiry: %s", expiry_time.isoformat())
            return token
            
        except Exception as e:
            logger.error("Failed to generate JWT token: %s", str(e))
            raise JWTError(f"Token generation failed: {str(e)}") from e
    
    def validate_token(self, token: str, verify_expiry: bool = True) -> bool:
        """
        Validate a JWT token without decoding the payload.
        
        Args:
            token: JWT token to validate
            verify_expiry: Whether to check token expiration
            
        Returns:
            bool: True if token is valid, False otherwise
        """
        try:
            self.decode_token(token, verify_expiry=verify_expiry)
            return True
        except JWTError:
            return False
    
    def decode_token(
        self,
        token: str,
        verify_expiry: bool = True,
        verify_signature: bool = True
    ) -> Dict[str, Any]:
        """
        Decode and validate a JWT token.
        
        Args:
            token: JWT token to decode
            verify_expiry: Whether to check token expiration
            verify_signature: Whether to verify token signature
            
        Returns:
            dict: Decoded token payload
            
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
            
            # Decode header
            header = self._decode_json_part(encoded_header, "header")
            
            # Validate header
            if header.get('typ') != 'JWT':
                raise JWTInvalidError("Invalid token type in header")
            
            if header.get('alg') != self.algorithm:
                raise JWTInvalidError(f"Unsupported algorithm: {header.get('alg')}")
            
            # Verify signature if requested
            if verify_signature:
                message = f"{encoded_header}.{encoded_payload}"
                expected_signature = self._create_signature(message)
                
                if not self._constant_time_compare(encoded_signature, expected_signature):
                    raise JWTSignatureError("Token signature verification failed")
            
            # Decode payload
            payload = self._decode_json_part(encoded_payload, "payload")
            
            # Verify expiration if requested
            if verify_expiry:
                self._verify_token_expiry(payload)
            
            # Verify not-before claim
            self._verify_not_before(payload)
            
            logger.debug("Successfully decoded JWT token")
            return payload
            
        except JWTError:
            raise
        except Exception as e:
            logger.error("Failed to decode JWT token: %s", str(e))
            raise JWTInvalidError(f"Token decoding failed: {str(e)}") from e
    
    def refresh_token(self, token: str, new_expiry_hours: Optional[int] = None) -> str:
        """
        Refresh a JWT token with new expiration time.
        
        Args:
            token: Original JWT token
            new_expiry_hours: New expiry in hours (uses default if None)
            
        Returns:
            str: New JWT token with updated expiration
            
        Raises:
            JWTError: If original token is invalid or refresh fails
        """
        try: