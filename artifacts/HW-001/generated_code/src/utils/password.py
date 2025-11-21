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
    Password hashing and verification utility using bcrypt.
    
    This class provides methods to securely hash passwords and verify
    them against stored hashes using the bcrypt algorithm.
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
        Hash a password using bcrypt with salt.
        
        Args:
            password: Plain text password to hash
            
        Returns:
            str: Base64-encoded bcrypt hash
            
        Raises:
            ValueError: If password is empty or None
            TypeError: If password is not a string
        """
        if not isinstance(password, str):
            raise TypeError("Password must be a string")
        
        if not password:
            raise ValueError("Password cannot be empty")
        
        if len(password) > 72:
            logger.warning("Password length exceeds 72 characters, will be truncated by bcrypt")
        
        try:
            # Generate salt and hash password
            salt = bcrypt.gensalt(rounds=self.salt_rounds)
            password_bytes = password.encode('utf-8')
            hashed = bcrypt.hashpw(password_bytes, salt)
            
            # Return as string
            hashed_str = hashed.decode('utf-8')
            logger.debug("Password successfully hashed")
            return hashed_str
            
        except Exception as e:
            logger.error(f"Error hashing password: {e}")
            raise RuntimeError(f"Failed to hash password: {e}") from e
    
    def verify_password(self, password: str, hashed_password: str) -> bool:
        """
        Verify a password against its hash.
        
        Args:
            password: Plain text password to verify
            hashed_password: Previously hashed password to check against
            
        Returns:
            bool: True if password matches hash, False otherwise
            
        Raises:
            ValueError: If password or hashed_password is empty or None
            TypeError: If password or hashed_password is not a string
        """
        if not isinstance(password, str):
            raise TypeError("Password must be a string")
        
        if not isinstance(hashed_password, str):
            raise TypeError("Hashed password must be a string")
        
        if not password:
            raise ValueError("Password cannot be empty")
        
        if not hashed_password:
            raise ValueError("Hashed password cannot be empty")
        
        try:
            password_bytes = password.encode('utf-8')
            hashed_bytes = hashed_password.encode('utf-8')
            
            # Verify password against hash
            is_valid = bcrypt.checkpw(password_bytes, hashed_bytes)
            
            logger.debug(f"Password verification result: {is_valid}")
            return is_valid
            
        except Exception as e:
            logger.error(f"Error verifying password: {e}")
            # Return False for any verification errors (don't expose internal errors)
            return False


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
    Hash a password using the default hasher.
    
    Args:
        password: Plain text password to hash
        salt_rounds: Number of salt rounds (default: 12)
        
    Returns:
        str: Hashed password
        
    Raises:
        ValueError: If password is invalid
        TypeError: If password is not a string
    """
    if salt_rounds != DEFAULT_SALT_ROUNDS:
        # Use custom hasher for non-default salt rounds
        hasher = PasswordHasher(salt_rounds)
        return hasher.hash_password(password)
    
    # Use default hasher
    hasher = get_default_hasher()
    return hasher.hash_password(password)


def verify_password(password: str, hashed_password: str) -> bool:
    """
    Verify a password against its hash using the default hasher.
    
    Args:
        password: Plain text password to verify
        hashed_password: Previously hashed password
        
    Returns:
        bool: True if password matches, False otherwise
        
    Raises:
        ValueError: If inputs are invalid
        TypeError: If inputs are not strings
    """
    hasher = get_default_hasher()
    return hasher.verify_password(password, hashed_password)


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
        password: Password to check
        
    Returns:
        bool: True if password meets requirements, False otherwise
        
    Raises:
        TypeError: If password is not a string
    """
    if not isinstance(password, str):
        raise TypeError("Password must be a string")
    
    if len(password) < 8:
        return False
    
    has_upper = any(c.isupper() for c in password)
    has_lower = any(c.islower() for c in password)
    has_digit = any(c.isdigit() for c in password)
    has_special = any(not c.isalnum() for c in password)
    
    return has_upper and has_lower and has_digit and has_special