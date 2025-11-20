"""
Password hashing and verification utilities using bcrypt.

This module provides secure password hashing and verification functionality
using bcrypt with configurable salt rounds for optimal security.

Component ID: COMP-009
Semantic Unit: SU-009

Author: ASP Code Agent
"""

import bcrypt
import logging
from typing import Union


# Configure logging
logger = logging.getLogger(__name__)

# Default salt rounds for bcrypt hashing
DEFAULT_SALT_ROUNDS = 12


class PasswordHashingError(Exception):
    """Exception raised when password hashing operations fail."""
    pass


class PasswordVerificationError(Exception):
    """Exception raised when password verification operations fail."""
    pass


def hash_password(password: str, salt_rounds: int = DEFAULT_SALT_ROUNDS) -> str:
    """
    Hash a password using bcrypt with specified salt rounds.
    
    Args:
        password: The plain text password to hash
        salt_rounds: Number of salt rounds for bcrypt (default: 12)
        
    Returns:
        str: The hashed password as a string
        
    Raises:
        PasswordHashingError: If password hashing fails
        ValueError: If password is empty or salt_rounds is invalid
        
    Example:
        >>> hashed = hash_password("my_secure_password")
        >>> len(hashed) > 0
        True
    """
    if not password:
        raise ValueError("Password cannot be empty")
        
    if not isinstance(password, str):
        raise ValueError("Password must be a string")
        
    if not isinstance(salt_rounds, int) or salt_rounds < 4 or salt_rounds > 31:
        raise ValueError("Salt rounds must be an integer between 4 and 31")
    
    try:
        # Convert password to bytes
        password_bytes = password.encode('utf-8')
        
        # Generate salt with specified rounds
        salt = bcrypt.gensalt(rounds=salt_rounds)
        
        # Hash the password
        hashed_bytes = bcrypt.hashpw(password_bytes, salt)
        
        # Convert back to string for storage
        hashed_password = hashed_bytes.decode('utf-8')
        
        logger.debug(f"Password hashed successfully with {salt_rounds} salt rounds")
        return hashed_password
        
    except Exception as e:
        logger.error(f"Password hashing failed: {str(e)}")
        raise PasswordHashingError(f"Failed to hash password: {str(e)}") from e


def verify_password(password: str, hashed_password: str) -> bool:
    """
    Verify a password against its hash using bcrypt.
    
    Args:
        password: The plain text password to verify
        hashed_password: The hashed password to verify against
        
    Returns:
        bool: True if password matches hash, False otherwise
        
    Raises:
        PasswordVerificationError: If password verification fails
        ValueError: If password or hashed_password is empty
        
    Example:
        >>> hashed = hash_password("test_password")
        >>> verify_password("test_password", hashed)
        True
        >>> verify_password("wrong_password", hashed)
        False
    """
    if not password:
        raise ValueError("Password cannot be empty")
        
    if not hashed_password:
        raise ValueError("Hashed password cannot be empty")
        
    if not isinstance(password, str):
        raise ValueError("Password must be a string")
        
    if not isinstance(hashed_password, str):
        raise ValueError("Hashed password must be a string")
    
    try:
        # Convert inputs to bytes
        password_bytes = password.encode('utf-8')
        hashed_bytes = hashed_password.encode('utf-8')
        
        # Verify password using bcrypt
        is_valid = bcrypt.checkpw(password_bytes, hashed_bytes)
        
        logger.debug(f"Password verification completed: {'success' if is_valid else 'failed'}")
        return is_valid
        
    except Exception as e:
        logger.error(f"Password verification failed: {str(e)}")
        raise PasswordVerificationError(f"Failed to verify password: {str(e)}") from e


def is_password_strong(password: str, min_length: int = 8) -> tuple[bool, list[str]]:
    """
    Check if a password meets basic strength requirements.
    
    Args:
        password: The password to check
        min_length: Minimum required password length (default: 8)
        
    Returns:
        tuple: (is_strong: bool, issues: list[str])
               is_strong is True if password is strong
               issues contains list of strength issues found
               
    Raises:
        ValueError: If password is not a string or min_length is invalid
        
    Example:
        >>> is_strong, issues = is_password_strong("WeakPass")
        >>> is_strong
        False
        >>> "No digits found" in issues
        True
    """
    if not isinstance(password, str):
        raise ValueError("Password must be a string")
        
    if not isinstance(min_length, int) or min_length < 1:
        raise ValueError("Minimum length must be a positive integer")
    
    issues = []
    
    # Check length
    if len(password) < min_length:
        issues.append(f"Password must be at least {min_length} characters long")
    
    # Check for uppercase letters
    if not any(c.isupper() for c in password):
        issues.append("No uppercase letters found")
    
    # Check for lowercase letters
    if not any(c.islower() for c in password):
        issues.append("No lowercase letters found")
    
    # Check for digits
    if not any(c.isdigit() for c in password):
        issues.append("No digits found")
    
    # Check for special characters
    special_chars = "!@#$%^&*()_+-=[]{}|;:,.<>?"
    if not any(c in special_chars for c in password):
        issues.append("No special characters found")
    
    is_strong = len(issues) == 0
    
    logger.debug(f"Password strength check: {'strong' if is_strong else 'weak'} "
                f"({len(issues)} issues found)")
    
    return is_strong, issues