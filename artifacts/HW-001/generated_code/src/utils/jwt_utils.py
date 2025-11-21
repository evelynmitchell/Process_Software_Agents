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
    JWT token utilities for secure token generation, validation, and decoding.
    
    Provides methods for creating JWT tokens with expiration, validating tokens,
    and extracting payload data with proper security checks.
    """
    
    def __init__(self, secret_key: str, algorithm: str = "HS256", default_expiry_hours: int = 24):
        """
        Initialize JWT utilities with secret key and configuration.
        
        Args:
            secret_key: Secret key for signing tokens (minimum 32 characters recommended)
            algorithm: Signing algorithm (currently supports HS256)
            default_expiry_hours: Default token expiration time in hours
            
        Raises:
            ValueError: If secret key is too short or algorithm is unsupported
        """
        if len(secret_key) < 32:
            raise ValueError("Secret key must be at least 32 characters long for security")
        
        if algorithm != "HS256":
            raise ValueError("Only HS256 algorithm is currently supported")
        
        self.secret_key = secret_key.encode('utf-8')
        self.algorithm = algorithm
        self.default_expiry_hours = default_expiry_hours
        
        logger.info(f"JWT utilities initialized with algorithm {algorithm}")
    
    def generate_token(
        self, 
        payload: Dict[str, Any], 
        expiry_hours: Optional[int] = None,
        include_jti: bool = True
    ) -> str:
        """
        Generate a JWT token with the given payload and expiration time.
        
        Args:
            payload: Dictionary containing token claims/data
            expiry_hours: Token expiration time in hours (uses default if None)
            include_jti: Whether to include a unique token ID (jti claim)
            
        Returns:
            str: Base64-encoded JWT token
            
        Raises:
            ValueError: If payload contains reserved claims or invalid data
            JWTError: If token generation fails
        """
        try:
            # Validate payload doesn't contain reserved claims
            reserved_claims = {'iat', 'exp', 'jti'}
            if any(claim in payload for claim in reserved_claims):
                raise ValueError(f"Payload cannot contain reserved claims: {reserved_claims}")
            
            # Create header
            header = {
                "alg": self.algorithm,
                "typ": "JWT"
            }
            
            # Create payload with standard claims
            current_time = datetime.now(timezone.utc)
            expiry_time = current_time + timedelta(hours=expiry_hours or self.default_expiry_hours)
            
            token_payload = payload.copy()
            token_payload.update({
                "iat": int(current_time.timestamp()),
                "exp": int(expiry_time.timestamp())
            })
            
            # Add unique token ID if requested
            if include_jti:
                token_payload["jti"] = self._generate_token_id()
            
            # Encode header and payload
            encoded_header = self._base64_url_encode(json.dumps(header, separators=(',', ':')))
            encoded_payload = self._base64_url_encode(json.dumps(token_payload, separators=(',', ':')))
            
            # Create signature
            message = f"{encoded_header}.{encoded_payload}"
            signature = self._create_signature(message)
            encoded_signature = self._base64_url_encode(signature)
            
            # Combine parts
            token = f"{encoded_header}.{encoded_payload}.{encoded_signature}"
            
            logger.info(f"JWT token generated successfully, expires at {expiry_time.isoformat()}")
            return token
            
        except Exception as e:
            logger.error(f"Failed to generate JWT token: {str(e)}")
            raise JWTError(f"Token generation failed: {str(e)}") from e
    
    def validate_token(self, token: str, verify_expiration: bool = True) -> bool:
        """
        Validate a JWT token's signature and expiration.
        
        Args:
            token: JWT token string to validate
            verify_expiration: Whether to check if token has expired
            
        Returns:
            bool: True if token is valid, False otherwise
            
        Raises:
            JWTInvalidError: If token format is invalid
            JWTSignatureError: If signature verification fails
            JWTExpiredError: If token has expired (when verify_expiration=True)
        """
        try:
            # Parse token parts
            parts = token.split('.')
            if len(parts) != 3:
                raise JWTInvalidError("Invalid token format: must have 3 parts separated by dots")
            
            encoded_header, encoded_payload, encoded_signature = parts
            
            # Verify signature
            message = f"{encoded_header}.{encoded_payload}"
            expected_signature = self._create_signature(message)
            provided_signature = self._base64_url_decode(encoded_signature)
            
            if not hmac.compare_digest(expected_signature, provided_signature):
                raise JWTSignatureError("Token signature verification failed")
            
            # Decode and validate payload
            payload = self._decode_payload(encoded_payload)
            
            # Check expiration if requested
            if verify_expiration and 'exp' in payload:
                current_timestamp = int(time.time())
                if current_timestamp >= payload['exp']:
                    raise JWTExpiredError("Token has expired")
            
            logger.debug("JWT token validation successful")
            return True
            
        except (JWTInvalidError, JWTSignatureError, JWTExpiredError):
            raise
        except Exception as e:
            logger.error(f"Token validation error: {str(e)}")
            raise JWTInvalidError(f"Token validation failed: {str(e)}") from e
    
    def decode_token(self, token: str, verify_signature: bool = True, verify_expiration: bool = True) -> Dict[str, Any]:
        """
        Decode a JWT token and return its payload.
        
        Args:
            token: JWT token string to decode
            verify_signature: Whether to verify token signature
            verify_expiration: Whether to check if token has expired
            
        Returns:
            Dict[str, Any]: Token payload data
            
        Raises:
            JWTInvalidError: If token format is invalid
            JWTSignatureError: If signature verification fails
            JWTExpiredError: If token has expired
        """
        try:
            # Parse token parts
            parts = token.split('.')
            if len(parts) != 3:
                raise JWTInvalidError("Invalid token format: must have 3 parts separated by dots")
            
            encoded_header, encoded_payload, encoded_signature = parts
            
            # Verify signature if requested
            if verify_signature:
                message = f"{encoded_header}.{encoded_payload}"
                expected_signature = self._create_signature(message)
                provided_signature = self._base64_url_decode(encoded_signature)
                
                if