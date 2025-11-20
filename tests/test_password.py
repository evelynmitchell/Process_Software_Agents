"""
Unit tests for password hashing and verification utilities.

Tests password hashing, verification, and various password scenarios including
edge cases and security requirements.

Component ID: COMP-009
Semantic Unit: SU-009

Author: ASP Code Generator
"""

import pytest
from unittest.mock import patch, MagicMock
import bcrypt
from src.utils.password import (
    hash_password,
    verify_password,
    generate_salt,
    is_password_strong,
    PasswordStrengthError
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

    def test_hash_password_with_empty_string(self):
        """Test that hash_password handles empty string."""
        password = ""
        hashed = hash_password(password)
        assert isinstance(hashed, str)
        assert len(hashed) > 0

    def test_hash_password_with_unicode_characters(self):
        """Test that hash_password handles unicode characters."""
        password = "pássw0rd_ñ_测试_🔒"
        hashed = hash_password(password)
        assert isinstance(hashed, str)
        assert len(hashed) > 0

    def test_hash_password_with_very_long_password(self):
        """Test that hash_password handles very long passwords."""
        password = "a" * 1000
        hashed = hash_password(password)
        assert isinstance(hashed, str)
        assert len(hashed) > 0

    def test_hash_password_with_special_characters(self):
        """Test that hash_password handles special characters."""
        password = "!@#$%^&*()_+-=[]{}|;:,.<>?"
        hashed = hash_password(password)
        assert isinstance(hashed, str)
        assert len(hashed) > 0

    def test_hash_password_with_whitespace(self):
        """Test that hash_password handles passwords with whitespace."""
        password = "  password with spaces  "
        hashed = hash_password(password)
        assert isinstance(hashed, str)
        assert len(hashed) > 0

    @patch('src.utils.password.bcrypt.hashpw')
    def test_hash_password_uses_bcrypt(self, mock_hashpw):
        """Test that hash_password uses bcrypt for hashing."""
        mock_hashpw.return_value = b'$2b$12$mocked_hash'
        password = "test_password"
        
        hash_password(password)
        
        mock_hashpw.assert_called_once()
        args = mock_hashpw.call_args[0]
        assert args[0] == password.encode('utf-8')

    def test_hash_password_with_none_raises_error(self):
        """Test that hash_password raises error for None input."""
        with pytest.raises(TypeError):
            hash_password(None)


class TestVerifyPassword:
    """Test cases for password verification functionality."""

    def test_verify_password_correct_password_returns_true(self):
        """Test that verify_password returns True for correct password."""
        password = "correct_password_123"
        hashed = hash_password(password)
        assert verify_password(password, hashed) is True

    def test_verify_password_incorrect_password_returns_false(self):
        """Test that verify_password returns False for incorrect password."""
        password = "correct_password_123"
        wrong_password = "wrong_password_456"
        hashed = hash_password(password)
        assert verify_password(wrong_password, hashed) is False

    def test_verify_password_empty_password_with_hash(self):
        """Test that verify_password handles empty password with valid hash."""
        password = ""
        hashed = hash_password(password)
        assert verify_password(password, hashed) is True
        assert verify_password("not_empty", hashed) is False

    def test_verify_password_with_unicode_characters(self):
        """Test that verify_password works with unicode characters."""
        password = "pássw0rd_ñ_测试_🔒"
        hashed = hash_password(password)
        assert verify_password(password, hashed) is True
        assert verify_password("different_unicode_ñ", hashed) is False

    def test_verify_password_case_sensitive(self):
        """Test that verify_password is case sensitive."""
        password = "CaseSensitive123"
        hashed = hash_password(password)
        assert verify_password(password, hashed) is True
        assert verify_password("casesensitive123", hashed) is False
        assert verify_password("CASESENSITIVE123", hashed) is False

    def test_verify_password_with_whitespace_differences(self):
        """Test that verify_password is sensitive to whitespace."""
        password = "password with spaces"
        hashed = hash_password(password)
        assert verify_password(password, hashed) is True
        assert verify_password(" password with spaces", hashed) is False
        assert verify_password("password with spaces ", hashed) is False

    def test_verify_password_with_invalid_hash_format(self):
        """Test that verify_password handles invalid hash format."""
        password = "test_password"
        invalid_hash = "not_a_valid_bcrypt_hash"
        assert verify_password(password, invalid_hash) is False

    def test_verify_password_with_empty_hash(self):
        """Test that verify_password handles empty hash."""
        password = "test_password"
        assert verify_password(password, "") is False

    def test_verify_password_with_none_inputs(self):
        """Test that verify_password handles None inputs."""
        password = "test_password"
        hashed = hash_password(password)
        
        with pytest.raises(TypeError):
            verify_password(None, hashed)
        
        with pytest.raises(TypeError):
            verify_password(password, None)

    @patch('src.utils.password.bcrypt.checkpw')
    def test_verify_password_uses_bcrypt(self, mock_checkpw):
        """Test that verify_password uses bcrypt for verification."""
        mock_checkpw.return_value = True
        password = "test_password"
        hashed = "$2b$12$mocked_hash"
        
        result = verify_password(password, hashed)
        
        mock_checkpw.assert_called_once_with(
            password.encode('utf-8'),
            hashed.encode('utf-8')
        )
        assert result is True


class TestGenerateSalt:
    """Test cases for salt generation functionality."""

    def test_generate_salt_returns_bytes(self):
        """Test that generate_salt returns bytes."""
        salt = generate_salt()
        assert isinstance(salt, bytes)

    def test_generate_salt_returns_different_values(self):
        """Test that generate_salt returns different values each time."""
        salt1 = generate_salt()
        salt2 = generate_salt()
        assert salt1 != salt2

    def test_generate_salt_has_correct_length(self):
        """Test that generate_salt returns salt with correct length."""
        salt = generate_salt()
        # bcrypt salt should be 29 characters when base64 encoded
        assert len(salt) == 29

    def test_generate_salt_with_custom_rounds(self):
        """Test that generate_salt accepts custom rounds parameter."""
        salt = generate