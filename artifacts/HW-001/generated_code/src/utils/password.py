"""
Password hashing and verification utilities using bcrypt.

This module provides secure password hashing and verification functionality
using bcrypt with configurable salt rounds for the Hello World API.

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


class PasswordHashingError(Exception):
    """Exception raised when password hashing operations fail."""
    pass


class PasswordVerificationError(Exception):
    """Exception raised when password verification operations fail."""
    pass


def hash_password(password: str, salt_rounds: Optional[int] = None) -> str:
    """
    Hash a password using bcrypt with salt.
    
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
        
    if salt_rounds is None:
        salt_rounds = DEFAULT_SALT_ROUNDS
        
    if not isinstance(salt_rounds, int) or salt_rounds < 4 or salt_rounds > 31:
        raise ValueError("Salt rounds must be an integer between 4 and 31")
    
    try:
        # Convert password to bytes
        password_bytes = password.encode('utf-8')
        
        # Generate salt and hash password
        salt = bcrypt.gensalt(rounds=salt_rounds)
        hashed_password = bcrypt.hashpw(password_bytes, salt)
        
        # Convert back to string for storage
        hashed_string = hashed_password.decode('utf-8')
        
        logger.debug(f"Password hashed successfully with {salt_rounds} salt rounds")
        return hashed_string
        
    except Exception as e:
        logger.error(f"Failed to hash password: {str(e)}")
        raise PasswordHashingError(f"Password hashing failed: {str(e)}") from e


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
    
    try:
        # Convert inputs to bytes
        password_bytes = password.encode('utf-8')
        hashed_bytes = hashed_password.encode('utf-8')
        
        # Verify password using bcrypt
        is_valid = bcrypt.checkpw(password_bytes, hashed_bytes)
        
        logger.debug(f"Password verification completed: {'success' if is_valid else 'failed'}")
        return is_valid
        
    except Exception as e:
        logger.error(f"Failed to verify password: {str(e)}")
        raise PasswordVerificationError(f"Password verification failed: {str(e)}") from e


def is_password_strong(password: str) -> bool:
    """
    Check if a password meets basic strength requirements.
    
    Requirements:
    - At least 8 characters long
    - Contains at least one uppercase letter
    - Contains at least one lowercase letter
    - Contains at least one digit
    - Contains at least one special character
    
    Args:
        password: The password to check
        
    Returns:
        bool: True if password meets strength requirements, False otherwise
        
    Example:
        >>> is_password_strong("Password123!")
        True
        >>> is_password_strong("weak")
        False
    """
    if not password or len(password) < 8:
        return False
    
    has_upper = any(c.isupper() for c in password)
    has_lower = any(c.islower() for c in password)
    has_digit = any(c.isdigit() for c in password)
    has_special = any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password)
    
    return all([has_upper, has_lower, has_digit, has_special])


def get_password_strength_feedback(password: str) -> list[str]:
    """
    Get feedback on password strength requirements.
    
    Args:
        password: The password to analyze
        
    Returns:
        list[str]: List of feedback messages for improving password strength
        
    Example:
        >>> feedback = get_password_strength_feedback("weak")
        >>> len(feedback) > 0
        True
    """
    feedback = []
    
    if not password:
        feedback.append("Password cannot be empty")
        return feedback
    
    if len(password) < 8:
        feedback.append("Password must be at least 8 characters long")
    
    if not any(c.isupper() for c in password):
        feedback.append("Password must contain at least one uppercase letter")
    
    if not any(c.islower() for c in password):
        feedback.append("Password must contain at least one lowercase letter")
    
    if not any(c.isdigit() for c in password):
        feedback.append("Password must contain at least one digit")
    
    if not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password):
        feedback.append("Password must contain at least one special character (!@#$%^&*()_+-=[]{}|;:,.<>?)")
    
    return feedback