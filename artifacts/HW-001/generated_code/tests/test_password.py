"""
Unit tests for password hashing and verification utilities.

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
from typing import Any

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

    def test_hash_password_different_passwords_different_hashes(self):
        """Test that different passwords produce different hashes."""
        password1 = "password123"
        password2 = "password456"
        hash1 = hash_password(password1)
        hash2 = hash_password(password2)
        assert hash1 != hash2

    def test_hash_password_same_password_different_hashes(self):
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
        """Test that custom rounds parameter works correctly."""
        password = "test_password_123"
        hashed = hash_password(password, rounds=10)
        assert hashed.startswith("$2b$10$")

    @patch('bcrypt.hashpw')
    def test_hash_password_bcrypt_exception(self, mock_hashpw):
        """Test that bcrypt exceptions are handled properly."""
        mock_hashpw.side_effect = Exception("Bcrypt error")
        password = "test_password_123"
        
        with pytest.raises(PasswordHashError) as exc_info:
            hash_password(password)
        
        assert "Failed to hash password" in str(exc_info.value)

    def test_hash_password_none_input(self):
        """Test that None input raises appropriate error."""
        with pytest.raises(TypeError):
            hash_password(None)


class TestVerifyPassword:
    """Test cases for password verification functionality."""

    def test_verify_password_correct_password(self):
        """Test that correct password verification returns True."""
        password = "test_password_123"
        hashed = hash_password(password)
        assert verify_password(password, hashed) is True

    def test_verify_password_incorrect_password(self):
        """Test that incorrect password verification returns False."""
        password = "test_password_123"
        wrong_password = "wrong_password_456"
        hashed = hash_password(password)
        assert verify_password(wrong_password, hashed) is False

    def test_verify_password_empty_password(self):
        """Test verification with empty password."""
        password = ""
        hashed = hash_password(password)
        assert verify_password("", hashed) is True
        assert verify_password("not_empty", hashed) is False

    def test_verify_password_unicode_characters(self):
        """Test verification with unicode characters."""
        password = "pássw0rd_测试_🔒"
        hashed = hash_password(password)
        assert verify_password(password, hashed) is True
        assert verify_password("different_unicode_测试", hashed) is False

    def test_verify_password_case_sensitive(self):
        """Test that password verification is case sensitive."""
        password = "TestPassword123"
        hashed = hash_password(password)
        assert verify_password("testpassword123", hashed) is False
        assert verify_password("TESTPASSWORD123", hashed) is False

    def test_verify_password_invalid_hash_format(self):
        """Test verification with invalid hash format."""
        password = "test_password_123"
        invalid_hash = "not_a_valid_hash"
        assert verify_password(password, invalid_hash) is False

    def test_verify_password_empty_hash(self):
        """Test verification with empty hash."""
        password = "test_password_123"
        assert verify_password(password, "") is False

    @patch('bcrypt.checkpw')
    def test_verify_password_bcrypt_exception(self, mock_checkpw):
        """Test that bcrypt exceptions during verification are handled."""
        mock_checkpw.side_effect = Exception("Bcrypt verification error")
        password = "test_password_123"
        hashed = hash_password(password)
        
        # Should return False on exception, not raise
        assert verify_password(password, hashed) is False

    def test_verify_password_none_inputs(self):
        """Test verification with None inputs."""
        password = "test_password_123"
        hashed = hash_password(password)
        
        with pytest.raises(TypeError):
            verify_password(None, hashed)
        
        with pytest.raises(TypeError):
            verify_password(password, None)


class TestValidatePasswordStrength:
    """Test cases for password strength validation."""

    def test_validate_strong_password(self):
        """Test that strong password passes validation."""
        strong_password = "StrongP@ssw0rd123"
        assert validate_password_strength(strong_password) is True

    def test_validate_password_too_short(self):
        """Test that password shorter than minimum length fails."""
        short_password = "Sh0rt!"
        with pytest.raises(PasswordStrengthError) as exc_info:
            validate_password_strength(short_password)
        assert "at least 8 characters" in str(exc_info.value)

    def test_validate_password_no_uppercase(self):
        """Test that password without uppercase fails."""
        no_upper = "lowercase123!"
        with pytest.raises(PasswordStrengthError) as exc_info:
            validate_password_strength(no_upper)
        assert "uppercase letter" in str(exc_info.value)

    def test_validate_password_no_lowercase(self):
        """Test that password without lowercase fails."""
        no_lower = "UPPERCASE123!"
        with pytest.raises(PasswordStrengthError) as exc_info:
            validate_password_strength(no_lower)
        assert "lowercase letter" in str(exc_info.value)

    def test_validate_password_no_digit(self):
        """Test that password without digit