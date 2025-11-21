"""
Unit tests for password utility functions

Tests password hashing, verification, and strength validation with comprehensive
edge case coverage including empty inputs, special characters, and security scenarios.

Component ID: COMP-009
Semantic Unit: SU-009

Author: ASP Code Agent
"""

import pytest
from unittest.mock import patch, MagicMock
import bcrypt
import re

from src.utils.password import (
    hash_password,
    verify_password,
    validate_password_strength,
    generate_salt,
    is_password_compromised
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
        password = "same_password"
        hash1 = hash_password(password)
        hash2 = hash_password(password)
        assert hash1 != hash2

    def test_hash_password_empty_string(self):
        """Test that hash_password handles empty string."""
        password = ""
        hashed = hash_password(password)
        assert isinstance(hashed, str)
        assert hashed.startswith("$2b$")

    def test_hash_password_unicode_characters(self):
        """Test that hash_password handles unicode characters."""
        password = "pássw0rd_ñ_测试"
        hashed = hash_password(password)
        assert isinstance(hashed, str)
        assert hashed.startswith("$2b$")

    def test_hash_password_special_characters(self):
        """Test that hash_password handles special characters."""
        password = "p@ssw0rd!#$%^&*()_+-=[]{}|;:,.<>?"
        hashed = hash_password(password)
        assert isinstance(hashed, str)
        assert hashed.startswith("$2b$")

    def test_hash_password_very_long_password(self):
        """Test that hash_password handles very long passwords."""
        password = "a" * 1000
        hashed = hash_password(password)
        assert isinstance(hashed, str)
        assert hashed.startswith("$2b$")

    def test_hash_password_with_custom_rounds(self):
        """Test that hash_password accepts custom rounds parameter."""
        password = "test_password"
        hashed = hash_password(password, rounds=10)
        assert isinstance(hashed, str)
        assert "$2b$10$" in hashed

    def test_hash_password_invalid_rounds_raises_error(self):
        """Test that hash_password raises error for invalid rounds."""
        password = "test_password"
        with pytest.raises(ValueError, match="Rounds must be between 4 and 31"):
            hash_password(password, rounds=3)
        
        with pytest.raises(ValueError, match="Rounds must be between 4 and 31"):
            hash_password(password, rounds=32)

    def test_hash_password_none_input_raises_error(self):
        """Test that hash_password raises error for None input."""
        with pytest.raises(TypeError, match="Password must be a string"):
            hash_password(None)

    def test_hash_password_non_string_input_raises_error(self):
        """Test that hash_password raises error for non-string input."""
        with pytest.raises(TypeError, match="Password must be a string"):
            hash_password(123)


class TestVerifyPassword:
    """Test cases for password verification functionality."""

    def test_verify_password_correct_password_returns_true(self):
        """Test that verify_password returns True for correct password."""
        password = "correct_password_123"
        hashed = hash_password(password)
        assert verify_password(password, hashed) is True

    def test_verify_password_incorrect_password_returns_false(self):
        """Test that verify_password returns False for incorrect password."""
        password = "correct_password"
        wrong_password = "wrong_password"
        hashed = hash_password(password)
        assert verify_password(wrong_password, hashed) is False

    def test_verify_password_empty_password_against_hash(self):
        """Test that verify_password handles empty password correctly."""
        password = ""
        hashed = hash_password(password)
        assert verify_password("", hashed) is True
        assert verify_password("not_empty", hashed) is False

    def test_verify_password_case_sensitive(self):
        """Test that verify_password is case sensitive."""
        password = "CaseSensitive"
        hashed = hash_password(password)
        assert verify_password("CaseSensitive", hashed) is True
        assert verify_password("casesensitive", hashed) is False
        assert verify_password("CASESENSITIVE", hashed) is False

    def test_verify_password_unicode_characters(self):
        """Test that verify_password handles unicode characters."""
        password = "pássw0rd_ñ_测试"
        hashed = hash_password(password)
        assert verify_password(password, hashed) is True
        assert verify_password("different_unicode_测试", hashed) is False

    def test_verify_password_special_characters(self):
        """Test that verify_password handles special characters."""
        password = "p@ssw0rd!#$%^&*()_+-=[]{}|;:,.<>?"
        hashed = hash_password(password)
        assert verify_password(password, hashed) is True

    def test_verify_password_invalid_hash_returns_false(self):
        """Test that verify_password returns False for invalid hash."""
        password = "test_password"
        invalid_hash = "invalid_hash_format"
        assert verify_password(password, invalid_hash) is False

    def test_verify_password_none_password_raises_error(self):
        """Test that verify_password raises error for None password."""
        hashed = hash_password("test")
        with pytest.raises(TypeError, match="Password must be a string"):
            verify_password(None, hashed)

    def test_verify_password_none_hash_raises_error(self):
        """Test that verify_password raises error for None hash."""
        with pytest.raises(TypeError, match="Hash must be a string"):
            verify_password("test", None)

    def test_verify_password_non_string_inputs_raise_error(self):
        """Test that verify_password raises error for non-string inputs."""
        with pytest.raises(TypeError, match="Password must be a string"):
            verify_password(123, "hash")
        
        with pytest.raises(TypeError, match="Hash must be a string"):
            verify_password("password", 123)


class TestValidatePasswordStrength:
    """Test cases for password strength validation."""

    def test_validate_password_strength_strong_password_returns_true(self):
        """Test that validate_password_strength returns True for strong password."""
        strong_password = "StrongP@ssw0rd123!"
        result = validate_password_strength(strong_password)
        assert result["is_valid"] is True
        assert len