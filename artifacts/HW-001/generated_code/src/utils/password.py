"""
Password hashing and verification utilities using bcrypt.

This module provides secure password hashing and verification functionality
using the bcrypt algorithm with configurable salt rounds.

Component ID: COMP-009
Semantic Unit: SU-009

Author: ASP Code Agent
"""

import logging
from typing import Optional

import bcrypt


# Configure logging
logger = logging.getLogger(__name__)

# Default salt rounds for bcrypt hashing
DEFAULT_SALT_ROUNDS = 12


class PasswordHasher:
    """
    Password hashing and verification utility class using bcrypt.
    
    This class provides methods to securely hash passwords and verify
    password attempts against stored hashes using the bcrypt algorithm.
    """
    
    def __init__(self, salt_rounds: int = DEFAULT_SALT_ROUNDS) -> None:
        """
        Initialize the password hasher with specified salt rounds.
        
        Args:
            salt_rounds: Number of salt rounds for bcrypt (default: 12)
            
        Raises:
            ValueError: If salt_rounds is not between 4 and 31
        """
        if not isinstance(salt_rounds, int):
            raise ValueError("Salt rounds must be an integer")
        
        if salt_rounds < 4 or salt_rounds > 31:
            raise ValueError("Salt rounds must be between 4 and 31")
        
        self.salt_rounds = salt_rounds
        logger.debug(f"PasswordHasher initialized with {salt_rounds} salt rounds")
    
    def hash_password(self, password: str) -> str:
        """
        Hash a password using bcrypt with the configured salt rounds.
        
        Args:
            password: Plain text password to hash
            
        Returns:
            str: Base64-encoded bcrypt hash of the password
            
        Raises:
            ValueError: If password is empty or None
            RuntimeError: If hashing fails due to bcrypt error
        """
        if not password:
            raise ValueError("Password cannot be empty or None")
        
        if not isinstance(password, str):
            raise ValueError("Password must be a string")
        
        try:
            # Convert password to bytes
            password_bytes = password.encode('utf-8')
            
            # Generate salt and hash password
            salt = bcrypt.gensalt(rounds=self.salt_rounds)
            hashed = bcrypt.hashpw(password_bytes, salt)
            
            # Return hash as string
            hash_str = hashed.decode('utf-8')
            logger.debug("Password hashed successfully")
            return hash_str
            
        except Exception as e:
            logger.error(f"Failed to hash password: {str(e)}")
            raise RuntimeError(f"Password hashing failed: {str(e)}") from e
    
    def verify_password(self, password: str, hashed_password: str) -> bool:
        """
        Verify a password against a stored bcrypt hash.
        
        Args:
            password: Plain text password to verify
            hashed_password: Stored bcrypt hash to verify against
            
        Returns:
            bool: True if password matches hash, False otherwise
            
        Raises:
            ValueError: If password or hashed_password is empty or None
            RuntimeError: If verification fails due to bcrypt error
        """
        if not password:
            raise ValueError("Password cannot be empty or None")
        
        if not hashed_password:
            raise ValueError("Hashed password cannot be empty or None")
        
        if not isinstance(password, str):
            raise ValueError("Password must be a string")
        
        if not isinstance(hashed_password, str):
            raise ValueError("Hashed password must be a string")
        
        try:
            # Convert inputs to bytes
            password_bytes = password.encode('utf-8')
            hash_bytes = hashed_password.encode('utf-8')
            
            # Verify password against hash
            is_valid = bcrypt.checkpw(password_bytes, hash_bytes)
            
            logger.debug(f"Password verification result: {is_valid}")
            return is_valid
            
        except Exception as e:
            logger.error(f"Failed to verify password: {str(e)}")
            raise RuntimeError(f"Password verification failed: {str(e)}") from e


# Module-level convenience functions
_default_hasher: Optional[PasswordHasher] = None


def get_default_hasher() -> PasswordHasher:
    """
    Get the default password hasher instance.
    
    Returns:
        PasswordHasher: Default hasher with standard salt rounds
    """
    global _default_hasher
    if _default_hasher is None:
        _default_hasher = PasswordHasher()
    return _default_hasher


def hash_password(password: str, salt_rounds: int = DEFAULT_SALT_ROUNDS) -> str:
    """
    Hash a password using bcrypt (convenience function).
    
    Args:
        password: Plain text password to hash
        salt_rounds: Number of salt rounds for bcrypt (default: 12)
        
    Returns:
        str: Base64-encoded bcrypt hash of the password
        
    Raises:
        ValueError: If password is invalid or salt_rounds out of range
        RuntimeError: If hashing fails
    """
    hasher = PasswordHasher(salt_rounds)
    return hasher.hash_password(password)


def verify_password(password: str, hashed_password: str) -> bool:
    """
    Verify a password against a stored bcrypt hash (convenience function).
    
    Args:
        password: Plain text password to verify
        hashed_password: Stored bcrypt hash to verify against
        
    Returns:
        bool: True if password matches hash, False otherwise
        
    Raises:
        ValueError: If inputs are invalid
        RuntimeError: If verification fails
    """
    hasher = get_default_hasher()
    return hasher.verify_password(password, hashed_password)


def is_password_strong(password: str, min_length: int = 8) -> bool:
    """
    Check if a password meets basic strength requirements.
    
    Args:
        password: Password to check
        min_length: Minimum required length (default: 8)
        
    Returns:
        bool: True if password meets strength requirements
        
    Raises:
        ValueError: If password is None or min_length is invalid
    """
    if password is None:
        raise ValueError("Password cannot be None")
    
    if not isinstance(password, str):
        raise ValueError("Password must be a string")
    
    if min_length < 1:
        raise ValueError("Minimum length must be at least 1")
    
    # Check minimum length
    if len(password) < min_length:
        return False
    
    # Check for at least one uppercase letter
    has_upper = any(c.isupper() for c in password)
    
    # Check for at least one lowercase letter
    has_lower = any(c.islower() for c in password)
    
    # Check for at least one digit
    has_digit = any(c.isdigit() for c in password)
    
    # Check for at least one special character
    special_chars = "!@#$%^&*()_+-=[]{}|;:,.<>?"
    has_special = any(c in special_chars for c in password)
    
    # Password is strong if it has at least 3 of the 4 character types
    criteria_met = sum([has_upper, has_lower, has_digit, has_special])
    
    return criteria_met >= 3