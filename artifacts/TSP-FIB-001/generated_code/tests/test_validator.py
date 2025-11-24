"""
Unit tests for FibonacciValidator.validate_input() method

Tests the FibonacciValidator component to verify input validation for the Fibonacci function.
Covers valid non-negative integers, negative integers, boolean rejection, and error messages.

Component ID: FibonacciValidator
Semantic Unit ID: SU-001

Author: ASP Code Agent
"""

import pytest

from src.fibonacci import FibonacciValidator


class TestFibonacciValidatorValidateInput:
    """Test suite for FibonacciValidator.validate_input() method."""

    def test_validate_input_zero_returns_true(self) -> None:
        """Test that validate_input returns True for n=0."""
        validator = FibonacciValidator()
        result = validator.validate_input(0)
        assert result is True

    def test_validate_input_one_returns_true(self) -> None:
        """Test that validate_input returns True for n=1."""
        validator = FibonacciValidator()
        result = validator.validate_input(1)
        assert result is True

    def test_validate_input_positive_integer_returns_true(self) -> None:
        """Test that validate_input returns True for positive integers."""
        validator = FibonacciValidator()
        test_values = [2, 5, 10, 100, 1000]
        for n in test_values:
            result = validator.validate_input(n)
            assert result is True, f"validate_input({n}) should return True"

    def test_validate_input_large_positive_integer_returns_true(self) -> None:
        """Test that validate_input returns True for large positive integers."""
        validator = FibonacciValidator()
        result = validator.validate_input(1000000)
        assert result is True

    def test_validate_input_negative_one_raises_value_error(self) -> None:
        """Test that validate_input raises ValueError for n=-1."""
        validator = FibonacciValidator()
        with pytest.raises(ValueError):
            validator.validate_input(-1)

    def test_validate_input_negative_integer_raises_value_error(self) -> None:
        """Test that validate_input raises ValueError for negative integers."""
        validator = FibonacciValidator()
        test_values = [-1, -5, -10, -100, -1000]
        for n in test_values:
            with pytest.raises(ValueError):
                validator.validate_input(n)

    def test_validate_input_negative_integer_error_message(self) -> None:
        """Test that ValueError message contains 'non-negative' for negative input."""
        validator = FibonacciValidator()
        with pytest.raises(ValueError) as exc_info:
            validator.validate_input(-5)
        error_message = str(exc_info.value)
        assert "non-negative" in error_message.lower()

    def test_validate_input_negative_integer_error_message_exact(self) -> None:
        """Test that ValueError message matches expected format for negative input."""
        validator = FibonacciValidator()
        with pytest.raises(ValueError) as exc_info:
            validator.validate_input(-1)
        error_message = str(exc_info.value)
        assert error_message == "n must be a non-negative integer"

    def test_validate_input_boolean_true_raises_value_error(self) -> None:
        """Test that validate_input raises ValueError for boolean True."""
        validator = FibonacciValidator()
        with pytest.raises(ValueError):
            validator.validate_input(True)

    def test_validate_input_boolean_false_raises_value_error(self) -> None:
        """Test that validate_input raises ValueError for boolean False."""
        validator = FibonacciValidator()
        with pytest.raises(ValueError):
            validator.validate_input(False)

    def test_validate_input_boolean_error_message(self) -> None:
        """Test that ValueError message is appropriate for boolean input."""
        validator = FibonacciValidator()
        with pytest.raises(ValueError) as exc_info:
            validator.validate_input(True)
        error_message = str(exc_info.value)
        assert "non-negative" in error_message.lower() or "integer" in error_message.lower()

    def test_validate_input_float_raises_value_error(self) -> None:
        """Test that validate_input raises ValueError for float input."""
        validator = FibonacciValidator()
        with pytest.raises(ValueError):
            validator.validate_input(5.5)

    def test_validate_input_string_raises_value_error(self) -> None:
        """Test that validate_input raises ValueError for string input."""
        validator = FibonacciValidator()
        with pytest.raises(ValueError):
            validator.validate_input("5")

    def test_validate_input_none_raises_value_error(self) -> None:
        """Test that validate_input raises ValueError for None input."""
        validator = FibonacciValidator()
        with pytest.raises(ValueError):
            validator.validate_input(None)

    def test_validate_input_list_raises_value_error(self) -> None:
        """Test that validate_input raises ValueError for list input."""
        validator = FibonacciValidator()
        with pytest.raises(ValueError):
            validator.validate_input([1, 2, 3])

    def test_validate_input_dict_raises_value_error(self) -> None:
        """Test that validate_input raises ValueError for dict input."""
        validator = FibonacciValidator()
        with pytest.raises(ValueError):
            validator.validate_input({"n": 5})

    def test_validate_input_multiple_calls_zero(self) -> None:
        """Test that validate_input can be called multiple times with n=0."""
        validator = FibonacciValidator()
        for _ in range(5):
            result = validator.validate_input(0)
            assert result is True

    def test_validate_input_multiple_calls_positive(self) -> None:
        """Test that validate_input can be called multiple times with positive integers."""
        validator = FibonacciValidator()
        for n in [1, 2, 3, 4, 5]:
            result = validator.validate_input(n)
            assert result is True

    def test_validate_input_multiple_calls_negative(self) -> None:
        """Test that validate_input consistently raises ValueError for negative integers."""
        validator = FibonacciValidator()
        for n in [-1, -2, -3, -4, -5]:
            with pytest.raises(ValueError):
                validator.validate_input(n)

    def test_validate_input_boundary_zero_and_one(self) -> None:
        """Test that validate_input correctly handles boundary values 0 and 1."""
        validator = FibonacciValidator()
        assert validator.validate_input(0) is True
        assert validator.validate_input(1) is True

    def test_validate_input_boundary_negative_and_zero(self) -> None:
        """Test that validate_input correctly handles boundary between negative and zero."""
        validator = FibonacciValidator()
        with pytest.raises(ValueError):
            validator.validate_input(-1)
        assert validator.validate_input(0) is True

    def test_validate_input_return_type_is_bool(self) -> None:
        """Test that validate_input returns a boolean type."""
        validator = FibonacciValidator()
        result = validator.validate_input(5)
        assert isinstance(result, bool)
        assert result is True

    def test_validate_input_return_type_true_not_truthy(self) -> None:
        """Test that validate_input returns True (not just truthy value)."""
        validator = FibonacciValidator()
        result = validator.validate_input(10)
        assert result is True
        assert result == True

    def test_validate_input_exception_type_is_value_error(self) -> None:
        """Test that validate_input raises ValueError (not other exception types)."""