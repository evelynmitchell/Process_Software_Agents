"""
Unit tests for password hashing and verification utilities

Tests password hashing, verification, strength validation, and security features
to ensure proper authentication security.

Component ID: COMP-009
Semantic Unit: SU-009

Author: ASP Code Agent
"""

import pytest
from unittest.mock import patch, MagicMock
import bcrypt
import time

from src.utils.password import (
    hash_password,
    verify_password,
    validate_password_strength,
    generate_salt,
    is_password_compromised,
    PasswordStrengthError,
    PasswordHashError
)


class TestHashPassword:
    """Test cases for password hashing functionality."""

    def test_hash_password_returns_string(self):
        """Test that hash_password returns a string."""
        password = "test_password_123"
        hashed = hash_password(password)
        assert isinstance(hashed, str)

    def test_hash_password_returns_bcrypt_hash(self):
        """Test that hash_password returns a valid bcrypt hash."""
        password = "test_password_123"
        hashed = hash_password(password)
        assert hashed.startswith("$2b$")
        assert len(hashed) == 60  # Standard bcrypt hash length

    def test_hash_password_different_inputs_different_hashes(self):
        """Test that different passwords produce different hashes."""
        password1 = "password123"
        password2 = "password456"
        hash1 = hash_password(password1)
        hash2 = hash_password(password2)
        assert hash1 != hash2

    def test_hash_password_same_input_different_hashes(self):
        """Test that same password produces different hashes due to salt."""
        password = "test_password_123"
        hash1 = hash_password(password)
        hash2 = hash_password(password)
        assert hash1 != hash2

    def test_hash_password_empty_string(self):
        """Test that empty password can be hashed."""
        password = ""
        hashed = hash_password(password)
        assert isinstance(hashed, str)
        assert hashed.startswith("$2b$")

    def test_hash_password_unicode_characters(self):
        """Test that passwords with unicode characters are handled correctly."""
        password = "pássw0rd_测试_🔒"
        hashed = hash_password(password)
        assert isinstance(hashed, str)
        assert hashed.startswith("$2b$")

    def test_hash_password_very_long_password(self):
        """Test that very long passwords are handled correctly."""
        password = "a" * 1000
        hashed = hash_password(password)
        assert isinstance(hashed, str)
        assert hashed.startswith("$2b$")

    def test_hash_password_with_custom_rounds(self):
        """Test that custom bcrypt rounds parameter works."""
        password = "test_password_123"
        hashed = hash_password(password, rounds=10)
        assert isinstance(hashed, str)
        assert hashed.startswith("$2b$10$")

    def test_hash_password_invalid_rounds_raises_error(self):
        """Test that invalid rounds parameter raises PasswordHashError."""
        password = "test_password_123"
        with pytest.raises(PasswordHashError):
            hash_password(password, rounds=3)  # Too low
        with pytest.raises(PasswordHashError):
            hash_password(password, rounds=32)  # Too high

    @patch('bcrypt.hashpw')
    def test_hash_password_bcrypt_exception_handling(self, mock_hashpw):
        """Test that bcrypt exceptions are properly handled."""
        mock_hashpw.side_effect = Exception("Bcrypt error")
        password = "test_password_123"
        with pytest.raises(PasswordHashError):
            hash_password(password)


class TestVerifyPassword:
    """Test cases for password verification functionality."""

    def test_verify_password_correct_password_returns_true(self):
        """Test that correct password verification returns True."""
        password = "test_password_123"
        hashed = hash_password(password)
        assert verify_password(password, hashed) is True

    def test_verify_password_incorrect_password_returns_false(self):
        """Test that incorrect password verification returns False."""
        password = "test_password_123"
        wrong_password = "wrong_password_456"
        hashed = hash_password(password)
        assert verify_password(wrong_password, hashed) is False

    def test_verify_password_empty_password_with_empty_hash(self):
        """Test that empty password verification works correctly."""
        password = ""
        hashed = hash_password(password)
        assert verify_password(password, hashed) is True

    def test_verify_password_empty_password_with_non_empty_hash(self):
        """Test that empty password fails against non-empty hash."""
        password = "test_password_123"
        hashed = hash_password(password)
        assert verify_password("", hashed) is False

    def test_verify_password_unicode_characters(self):
        """Test that unicode password verification works correctly."""
        password = "pássw0rd_测试_🔒"
        hashed = hash_password(password)
        assert verify_password(password, hashed) is True

    def test_verify_password_case_sensitive(self):
        """Test that password verification is case sensitive."""
        password = "TestPassword123"
        hashed = hash_password(password)
        assert verify_password("testpassword123", hashed) is False
        assert verify_password("TESTPASSWORD123", hashed) is False

    def test_verify_password_invalid_hash_format(self):
        """Test that invalid hash format raises PasswordHashError."""
        password = "test_password_123"
        invalid_hash = "invalid_hash_format"
        with pytest.raises(PasswordHashError):
            verify_password(password, invalid_hash)

    def test_verify_password_none_inputs(self):
        """Test that None inputs raise appropriate errors."""
        password = "test_password_123"
        hashed = hash_password(password)
        
        with pytest.raises(ValueError):
            verify_password(None, hashed)
        
        with pytest.raises(ValueError):
            verify_password(password, None)

    @patch('bcrypt.checkpw')
    def test_verify_password_bcrypt_exception_handling(self, mock_checkpw):
        """Test that bcrypt exceptions are properly handled."""
        mock_checkpw.side_effect = Exception("Bcrypt error")
        password = "test_password_123"
        hashed = hash_password(password)
        with pytest.raises(PasswordHashError):
            verify_password(password, hashed)


class TestValidatePasswordStrength:
    """Test cases for password strength validation."""

    def test_validate_password_strength_strong_password_passes(self):
        """Test that strong password passes validation."""
        strong_password = "StrongP@ssw0rd123!"
        assert validate_password_strength(strong_password) is True

    def test_validate_password_strength_too_short_fails(self):
        """Test that password shorter than 8 characters fails."""
        short_password = "Sh0rt!"
        with pytest.raises(PasswordStrengthError) as exc_info:
            validate_password_strength(short_password)
        assert "at least 8 characters" in str(exc_info.value)

    def test_validate_password_strength_no_uppercase_fails(self):
        """Test that password without uppercase letters fails."""
        no_upper = "lowercase123!"
        with pytest.raises(PasswordStrengthError) as exc_info:
            validate_password_strength(no_upper)
        assert "uppercase letter" in str(exc_info.value)

    def test_validate_password_strength_no_lowercase_fails(self):
        """Test that password without lowercase letters fails."""
        no_