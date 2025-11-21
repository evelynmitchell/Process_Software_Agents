"""
Password utilities for secure password hashing, verification, and strength validation.

This module provides secure password handling using bcrypt with proper salt generation
and comprehensive password strength validation.

Component ID: COMP-009
Semantic Unit: SU-009

Author: ASP Code Agent
"""

import re
import secrets
from typing import Dict, List, Optional

import bcrypt


class PasswordStrengthError(Exception):
    """Raised when password does not meet strength requirements."""
    pass


class PasswordHashError(Exception):
    """Raised when password hashing fails."""
    pass


class PasswordVerificationError(Exception):
    """Raised when password verification fails."""
    pass


def hash_password(password: str, rounds: int = 12) -> str:
    """
    Hash a password using bcrypt with secure salt generation.
    
    Args:
        password: Plain text password to hash
        rounds: Number of bcrypt rounds (default 12, min 10, max 15)
        
    Returns:
        str: Base64 encoded bcrypt hash
        
    Raises:
        PasswordHashError: If hashing fails or invalid parameters
        ValueError: If password is empty or rounds out of range
        
    Example:
        >>> hashed = hash_password("mypassword123")
        >>> len(hashed) > 50
        True
    """
    if not password:
        raise ValueError("Password cannot be empty")
        
    if not isinstance(password, str):
        raise ValueError("Password must be a string")
        
    if not (10 <= rounds <= 15):
        raise ValueError("Rounds must be between 10 and 15")
        
    try:
        # Generate salt and hash password
        salt = bcrypt.gensalt(rounds=rounds)
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed.decode('utf-8')
    except Exception as e:
        raise PasswordHashError(f"Failed to hash password: {str(e)}") from e


def verify_password(password: str, hashed_password: str) -> bool:
    """
    Verify a password against its bcrypt hash.
    
    Args:
        password: Plain text password to verify
        hashed_password: Base64 encoded bcrypt hash
        
    Returns:
        bool: True if password matches hash, False otherwise
        
    Raises:
        PasswordVerificationError: If verification process fails
        ValueError: If parameters are invalid
        
    Example:
        >>> hashed = hash_password("mypassword123")
        >>> verify_password("mypassword123", hashed)
        True
        >>> verify_password("wrongpassword", hashed)
        False
    """
    if not password:
        raise ValueError("Password cannot be empty")
        
    if not hashed_password:
        raise ValueError("Hashed password cannot be empty")
        
    if not isinstance(password, str) or not isinstance(hashed_password, str):
        raise ValueError("Password and hashed password must be strings")
        
    try:
        return bcrypt.checkpw(
            password.encode('utf-8'),
            hashed_password.encode('utf-8')
        )
    except Exception as e:
        raise PasswordVerificationError(f"Failed to verify password: {str(e)}") from e


def validate_password_strength(password: str, min_length: int = 8) -> Dict[str, bool]:
    """
    Validate password strength against security requirements.
    
    Args:
        password: Password to validate
        min_length: Minimum required length (default 8)
        
    Returns:
        Dict[str, bool]: Dictionary with validation results:
            - length: True if meets minimum length
            - uppercase: True if contains uppercase letter
            - lowercase: True if contains lowercase letter
            - digit: True if contains digit
            - special: True if contains special character
            - no_whitespace: True if contains no whitespace
            - valid: True if all requirements met
            
    Raises:
        ValueError: If password is None or min_length is invalid
        
    Example:
        >>> result = validate_password_strength("MyPass123!")
        >>> result['valid']
        True
        >>> result['uppercase']
        True
    """
    if password is None:
        raise ValueError("Password cannot be None")
        
    if not isinstance(password, str):
        raise ValueError("Password must be a string")
        
    if min_length < 1:
        raise ValueError("Minimum length must be at least 1")
        
    # Check individual requirements
    checks = {
        'length': len(password) >= min_length,
        'uppercase': bool(re.search(r'[A-Z]', password)),
        'lowercase': bool(re.search(r'[a-z]', password)),
        'digit': bool(re.search(r'\d', password)),
        'special': bool(re.search(r'[!@#$%^&*(),.?":{}|<>]', password)),
        'no_whitespace': not bool(re.search(r'\s', password))
    }
    
    # Overall validity
    checks['valid'] = all(checks.values())
    
    return checks


def check_password_strength(password: str, min_length: int = 8) -> bool:
    """
    Check if password meets all strength requirements.
    
    Args:
        password: Password to check
        min_length: Minimum required length (default 8)
        
    Returns:
        bool: True if password meets all requirements
        
    Raises:
        PasswordStrengthError: If password fails strength requirements
        ValueError: If parameters are invalid
        
    Example:
        >>> check_password_strength("MyPass123!")
        True
        >>> check_password_strength("weak")
        False
    """
    validation_result = validate_password_strength(password, min_length)
    
    if not validation_result['valid']:
        failed_checks = [
            check for check, passed in validation_result.items()
            if check != 'valid' and not passed
        ]
        raise PasswordStrengthError(
            f"Password fails strength requirements: {', '.join(failed_checks)}"
        )
    
    return True


def get_password_strength_requirements(min_length: int = 8) -> List[str]:
    """
    Get list of password strength requirements.
    
    Args:
        min_length: Minimum required length (default 8)
        
    Returns:
        List[str]: List of requirement descriptions
        
    Example:
        >>> requirements = get_password_strength_requirements()
        >>> len(requirements)
        6
    """
    return [
        f"At least {min_length} characters long",
        "Contains at least one uppercase letter (A-Z)",
        "Contains at least one lowercase letter (a-z)",
        "Contains at least one digit (0-9)",
        "Contains at least one special character (!@#$%^&*(),.?\":{}|<>)",
        "Contains no whitespace characters"
    ]


def generate_secure_password(length: int = 16) -> str:
    """
    Generate a cryptographically secure random password.
    
    Args:
        length: Length of password to generate (default 16, min 8, max 128)
        
    Returns:
        str: Randomly generated password meeting strength requirements
        
    Raises:
        ValueError: If length is out of valid range
        
    Example:
        >>> password = generate_secure_password(12)
        >>> len(password)
        12
        >>> check_password_strength(password)
        True
    """
    if not (8 <= length <= 128):
        raise ValueError("Password length must be between 8 and 128 characters")
    
    # Character sets
    uppercase = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    lowercase = "abcdefghijklmnopqrstuvwxyz"
    digits = "0123456789"
    special = "!@#$%^&*(),.?\":{}|<>"
    all_chars = uppercase + lowercase + digits + special
    
    # Ensure at least one character from each required set
    passwor