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
    is_password_strong,
    generate_salt,
    hash_password_with_salt,
    verify_password_timing_safe,
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

    def test_hash_password_returns_different_hash_each_time(self):
        """Test that hash_password returns different hashes for same password."""
        password = "test_password_123"
        hash1 = hash_password(password)
        hash2 = hash_password(password)
        assert hash1 != hash2

    def test_hash_password_with_valid_password(self):
        """Test hash_password with valid password string."""
        password = "ValidPassword123!"
        hashed = hash_password(password)
        assert len(hashed) > 0
        assert hashed.startswith("$2b$")

    def test_hash_password_with_empty_string(self):
        """Test hash_password with empty string raises ValueError."""
        with pytest.raises(ValueError, match="Password cannot be empty"):
            hash_password("")

    def test_hash_password_with_none(self):
        """Test hash_password with None raises TypeError."""
        with pytest.raises(TypeError, match="Password must be a string"):
            hash_password(None)

    def test_hash_password_with_non_string(self):
        """Test hash_password with non-string input raises TypeError."""
        with pytest.raises(TypeError, match="Password must be a string"):
            hash_password(12345)

    def test_hash_password_with_unicode_characters(self):
        """Test hash_password handles unicode characters correctly."""
        password = "pássw0rd_ñ_测试"
        hashed = hash_password(password)
        assert isinstance(hashed, str)
        assert len(hashed) > 0

    def test_hash_password_with_very_long_password(self):
        """Test hash_password with very long password (72+ bytes)."""
        password = "a" * 100
        hashed = hash_password(password)
        assert isinstance(hashed, str)
        assert len(hashed) > 0

    @patch('bcrypt.hashpw')
    def test_hash_password_handles_bcrypt_error(self, mock_hashpw):
        """Test hash_password handles bcrypt errors gracefully."""
        mock_hashpw.side_effect = Exception("Bcrypt error")
        with pytest.raises(PasswordHashError, match="Failed to hash password"):
            hash_password("test_password")


class TestVerifyPassword:
    """Test cases for password verification functionality."""

    def test_verify_password_with_correct_password(self):
        """Test verify_password returns True for correct password."""
        password = "test_password_123"
        hashed = hash_password(password)
        assert verify_password(password, hashed) is True

    def test_verify_password_with_incorrect_password(self):
        """Test verify_password returns False for incorrect password."""
        password = "test_password_123"
        wrong_password = "wrong_password_456"
        hashed = hash_password(password)
        assert verify_password(wrong_password, hashed) is False

    def test_verify_password_with_empty_password(self):
        """Test verify_password with empty password raises ValueError."""
        hashed = hash_password("test_password")
        with pytest.raises(ValueError, match="Password cannot be empty"):
            verify_password("", hashed)

    def test_verify_password_with_empty_hash(self):
        """Test verify_password with empty hash raises ValueError."""
        with pytest.raises(ValueError, match="Hash cannot be empty"):
            verify_password("test_password", "")

    def test_verify_password_with_none_password(self):
        """Test verify_password with None password raises TypeError."""
        hashed = hash_password("test_password")
        with pytest.raises(TypeError, match="Password must be a string"):
            verify_password(None, hashed)

    def test_verify_password_with_none_hash(self):
        """Test verify_password with None hash raises TypeError."""
        with pytest.raises(TypeError, match="Hash must be a string"):
            verify_password("test_password", None)

    def test_verify_password_with_invalid_hash_format(self):
        """Test verify_password with invalid hash format returns False."""
        password = "test_password"
        invalid_hash = "invalid_hash_format"
        assert verify_password(password, invalid_hash) is False

    def test_verify_password_with_unicode_password(self):
        """Test verify_password works with unicode passwords."""
        password = "pássw0rd_ñ_测试"
        hashed = hash_password(password)
        assert verify_password(password, hashed) is True

    @patch('bcrypt.checkpw')
    def test_verify_password_handles_bcrypt_error(self, mock_checkpw):
        """Test verify_password handles bcrypt errors gracefully."""
        mock_checkpw.side_effect = Exception("Bcrypt error")
        hashed = "$2b$12$valid.hash.format"
        result = verify_password("test_password", hashed)
        assert result is False


class TestPasswordStrength:
    """Test cases for password strength validation."""

    def test_is_password_strong_with_strong_password(self):
        """Test is_password_strong returns True for strong password."""
        strong_password = "StrongP@ssw0rd123"
        assert is_password_strong(strong_password) is True

    def test_is_password_strong_with_weak_password_too_short(self):
        """Test is_password_strong returns False for password too short."""
        weak_password = "Sh0rt!"
        assert is_password_strong(weak_password) is False

    def test_is_password_strong_with_no_uppercase(self):
        """Test is_password_strong returns False for password without uppercase."""
        weak_password = "lowercase123!"
        assert is_password_strong(weak_password) is False

    def test_is_password_strong_with_no_lowercase(self):
        """Test is_password_strong returns False for password without lowercase."""
        weak_password = "UPPERCASE123!"
        assert is_password_strong(weak_password) is False

    def test_is_password_strong_with_no_digits(self):
        """Test is_password_strong returns False for password without digits."""
        weak_password = "NoDigitsHere!"
        assert is_password_strong(weak_password) is False

    def test_is_password_strong_with_no_special_chars(self):
        """Test is_password_strong returns False for password without special chars."""
        weak_password = "NoSpecialChars123"
        assert is_password_strong(weak_password) is False

    def test_is_password_strong_with_empty_password(self):
        """Test is_password_strong raises ValueError for empty password."""
        with pytest.raises(ValueError, match="Password cannot be empty"):
            is_password_strong("")

    def test_is_password_strong_with_none_password(self):
        """Test is_password_strong raises TypeError for None password."""
        with pytest.raises(TypeError, match="Password must be a string"):
            is_password_strong(None)

    def test_is_password_strong