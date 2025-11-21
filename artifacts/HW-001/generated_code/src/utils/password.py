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
from typing import Optional

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


def hash_password(password: str) -> str:
    """
    Hash a password using bcrypt with secure salt generation.
    
    Args:
        password: Plain text password to hash
        
    Returns:
        str: Base64 encoded bcrypt hash
        
    Raises:
        PasswordHashError: If password hashing fails
        ValueError: If password is empty or None
        
    Example:
        >>> hashed = hash_password("my_secure_password")
        >>> len(hashed) > 50
        True
    """
    if not password:
        raise ValueError("Password cannot be empty or None")
    
    try:
        # Generate salt with cost factor 12 (recommended for 2024)
        salt = bcrypt.gensalt(rounds=12)
        
        # Hash password with salt
        password_bytes = password.encode('utf-8')
        hashed = bcrypt.hashpw(password_bytes, salt)
        
        # Return as string for storage
        return hashed.decode('utf-8')
        
    except Exception as e:
        raise PasswordHashError(f"Failed to hash password: {str(e)}") from e


def verify_password(password: str, hashed_password: str) -> bool:
    """
    Verify a password against its bcrypt hash.
    
    Args:
        password: Plain text password to verify
        hashed_password: Previously hashed password to check against
        
    Returns:
        bool: True if password matches hash, False otherwise
        
    Raises:
        PasswordVerificationError: If verification process fails
        ValueError: If password or hash is empty or None
        
    Example:
        >>> hashed = hash_password("test123")
        >>> verify_password("test123", hashed)
        True
        >>> verify_password("wrong", hashed)
        False
    """
    if not password:
        raise ValueError("Password cannot be empty or None")
    
    if not hashed_password:
        raise ValueError("Hashed password cannot be empty or None")
    
    try:
        password_bytes = password.encode('utf-8')
        hashed_bytes = hashed_password.encode('utf-8')
        
        return bcrypt.checkpw(password_bytes, hashed_bytes)
        
    except Exception as e:
        raise PasswordVerificationError(f"Failed to verify password: {str(e)}") from e


def validate_password_strength(password: str, min_length: int = 8) -> None:
    """
    Validate password meets strength requirements.
    
    Requirements:
    - Minimum length (default 8 characters)
    - At least one uppercase letter
    - At least one lowercase letter
    - At least one digit
    - At least one special character
    - No common weak passwords
    
    Args:
        password: Password to validate
        min_length: Minimum required length (default 8)
        
    Raises:
        PasswordStrengthError: If password doesn't meet requirements
        ValueError: If password is empty or None
        
    Example:
        >>> validate_password_strength("SecurePass123!")
        >>> # No exception raised - password is strong
        
        >>> validate_password_strength("weak")
        Traceback (most recent call last):
        ...
        PasswordStrengthError: Password must be at least 8 characters long
    """
    if not password:
        raise ValueError("Password cannot be empty or None")
    
    # Check minimum length
    if len(password) < min_length:
        raise PasswordStrengthError(f"Password must be at least {min_length} characters long")
    
    # Check for uppercase letter
    if not re.search(r'[A-Z]', password):
        raise PasswordStrengthError("Password must contain at least one uppercase letter")
    
    # Check for lowercase letter
    if not re.search(r'[a-z]', password):
        raise PasswordStrengthError("Password must contain at least one lowercase letter")
    
    # Check for digit
    if not re.search(r'\d', password):
        raise PasswordStrengthError("Password must contain at least one digit")
    
    # Check for special character
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        raise PasswordStrengthError("Password must contain at least one special character (!@#$%^&*(),.?\":{}|<>)")
    
    # Check against common weak passwords
    weak_passwords = {
        'password', 'password123', '123456', '123456789', 'qwerty',
        'abc123', 'password1', 'admin', 'letmein', 'welcome',
        'monkey', '1234567890', 'dragon', 'master', 'hello'
    }
    
    if password.lower() in weak_passwords:
        raise PasswordStrengthError("Password is too common and easily guessable")


def generate_secure_password(length: int = 16) -> str:
    """
    Generate a cryptographically secure random password.
    
    Generated password will contain:
    - Uppercase letters (A-Z)
    - Lowercase letters (a-z)
    - Digits (0-9)
    - Special characters (!@#$%^&*)
    
    Args:
        length: Length of password to generate (minimum 8, default 16)
        
    Returns:
        str: Randomly generated secure password
        
    Raises:
        ValueError: If length is less than 8
        
    Example:
        >>> password = generate_secure_password(12)
        >>> len(password)
        12
        >>> validate_password_strength(password)
        >>> # No exception - generated password is strong
    """
    if length < 8:
        raise ValueError("Password length must be at least 8 characters")
    
    # Character sets
    uppercase = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
    lowercase = 'abcdefghijklmnopqrstuvwxyz'
    digits = '0123456789'
    special = '!@#$%^&*'
    
    # Ensure at least one character from each set
    password_chars = [
        secrets.choice(uppercase),
        secrets.choice(lowercase),
        secrets.choice(digits),
        secrets.choice(special)
    ]
    
    # Fill remaining length with random characters from all sets
    all_chars = uppercase + lowercase + digits + special
    for _ in range(length - 4):
        password_chars.append(secrets.choice(all_chars))
    
    # Shuffle the characters to avoid predictable patterns
    secrets.SystemRandom().shuffle(password_chars)
    
    return ''.join(password_chars)


def check_password_complexity(password: str) -> dict[str, bool]:
    """
    Check password complexity and return detailed results.
    
    Args:
        password: Password to analyze
        
    Returns:
        dict: Dictionary with complexity check results
        
    Example:
        >>> results = check_password_complexity("Test123!")
        >>> results['has_uppercase']
        True
        >>> results['has_lowercase']
        True
    """
    if not password:
        return {
            'has_minimum_length': False,
            'has_uppercase': False,
            'has_lowercase': False,
            'has_digit': False,
            'has_special': False,
            'is_not_common': False,
            'overall_strong': False
        }