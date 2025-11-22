"""
Unit tests for Fibonacci validator and calculator.

Tests input validation including negative integers, non-integer types (float, string),
and valid non-negative integers. Also tests the Fibonacci calculation for correctness
and edge cases.

Semantic Unit ID: SU-001
Component ID: FibonacciValidator

Author: ASP Code Agent
"""

import pytest
from src.fibonacci_validator import fibonacci


class TestFibonacciValidatorNegativeIntegers:
    """Test suite for negative integer validation."""

    def test_fibonacci_negative_one_raises_value_error(self) -> None:
        """Test that fibonacci(-1) raises ValueError."""
        with pytest.raises(ValueError, match="non-negative"):
            fibonacci(-1)

    def test_fibonacci_negative_ten_raises_value_error(self) -> None:
        """Test that fibonacci(-10) raises ValueError."""
        with pytest.raises(ValueError, match="non-negative"):
            fibonacci(-10)

    def test_fibonacci_negative_large_number_raises_value_error(self) -> None:
        """Test that fibonacci with large negative number raises ValueError."""
        with pytest.raises(ValueError, match="non-negative"):
            fibonacci(-1000)

    def test_fibonacci_negative_zero_point_one_raises_value_error(self) -> None:
        """Test that fibonacci(-0.1) raises ValueError for negative float."""
        with pytest.raises((ValueError, TypeError)):
            fibonacci(-0.1)  # type: ignore


class TestFibonacciValidatorNonIntegerTypes:
    """Test suite for non-integer type validation."""

    def test_fibonacci_float_five_point_five_raises_error(self) -> None:
        """Test that fibonacci(5.5) raises error for float input."""
        with pytest.raises((ValueError, TypeError)):
            fibonacci(5.5)  # type: ignore

    def test_fibonacci_float_zero_raises_error(self) -> None:
        """Test that fibonacci(0.0) raises error for float input."""
        with pytest.raises((ValueError, TypeError)):
            fibonacci(0.0)  # type: ignore

    def test_fibonacci_float_one_raises_error(self) -> None:
        """Test that fibonacci(1.0) raises error for float input."""
        with pytest.raises((ValueError, TypeError)):
            fibonacci(1.0)  # type: ignore

    def test_fibonacci_string_five_raises_error(self) -> None:
        """Test that fibonacci('5') raises error for string input."""
        with pytest.raises((ValueError, TypeError)):
            fibonacci('5')  # type: ignore

    def test_fibonacci_string_zero_raises_error(self) -> None:
        """Test that fibonacci('0') raises error for string input."""
        with pytest.raises((ValueError, TypeError)):
            fibonacci('0')  # type: ignore

    def test_fibonacci_string_negative_raises_error(self) -> None:
        """Test that fibonacci('-5') raises error for string input."""
        with pytest.raises((ValueError, TypeError)):
            fibonacci('-5')  # type: ignore

    def test_fibonacci_none_raises_error(self) -> None:
        """Test that fibonacci(None) raises error for None input."""
        with pytest.raises((ValueError, TypeError)):
            fibonacci(None)  # type: ignore

    def test_fibonacci_list_raises_error(self) -> None:
        """Test that fibonacci([5]) raises error for list input."""
        with pytest.raises((ValueError, TypeError)):
            fibonacci([5])  # type: ignore

    def test_fibonacci_dict_raises_error(self) -> None:
        """Test that fibonacci({'n': 5}) raises error for dict input."""
        with pytest.raises((ValueError, TypeError)):
            fibonacci({'n': 5})  # type: ignore

    def test_fibonacci_boolean_true_raises_error(self) -> None:
        """Test that fibonacci(True) raises error for boolean input."""
        with pytest.raises((ValueError, TypeError)):
            fibonacci(True)  # type: ignore

    def test_fibonacci_boolean_false_raises_error(self) -> None:
        """Test that fibonacci(False) raises error for boolean input."""
        with pytest.raises((ValueError, TypeError)):
            fibonacci(False)  # type: ignore


class TestFibonacciValidatorValidNonNegativeIntegers:
    """Test suite for valid non-negative integer inputs."""

    def test_fibonacci_zero_returns_zero(self) -> None:
        """Test that fibonacci(0) returns 0."""
        result = fibonacci(0)
        assert result == 0
        assert isinstance(result, int)

    def test_fibonacci_one_returns_one(self) -> None:
        """Test that fibonacci(1) returns 1."""
        result = fibonacci(1)
        assert result == 1
        assert isinstance(result, int)

    def test_fibonacci_two_returns_one(self) -> None:
        """Test that fibonacci(2) returns 1."""
        result = fibonacci(2)
        assert result == 1
        assert isinstance(result, int)

    def test_fibonacci_three_returns_two(self) -> None:
        """Test that fibonacci(3) returns 2."""
        result = fibonacci(3)
        assert result == 2
        assert isinstance(result, int)

    def test_fibonacci_four_returns_three(self) -> None:
        """Test that fibonacci(4) returns 3."""
        result = fibonacci(4)
        assert result == 3
        assert isinstance(result, int)

    def test_fibonacci_five_returns_five(self) -> None:
        """Test that fibonacci(5) returns 5."""
        result = fibonacci(5)
        assert result == 5
        assert isinstance(result, int)

    def test_fibonacci_ten_returns_fifty_five(self) -> None:
        """Test that fibonacci(10) returns 55."""
        result = fibonacci(10)
        assert result == 55
        assert isinstance(result, int)

    def test_fibonacci_fifteen_returns_correct_value(self) -> None:
        """Test that fibonacci(15) returns 610."""
        result = fibonacci(15)
        assert result == 610
        assert isinstance(result, int)

    def test_fibonacci_twenty_returns_correct_value(self) -> None:
        """Test that fibonacci(20) returns 6765."""
        result = fibonacci(20)
        assert result == 6765
        assert isinstance(result, int)


class TestFibonacciCalculatorSequence:
    """Test suite for Fibonacci sequence correctness."""

    def test_fibonacci_sequence_first_ten_values(self) -> None:
        """Test that first 10 Fibonacci numbers are correct."""
        expected_sequence = [0, 1, 1, 2, 3, 5, 8, 13, 21, 34]
        for n, expected in enumerate(expected_sequence):
            result = fibonacci(n)
            assert result == expected, f"fibonacci({n}) should be {expected}, got {result}"

    def test_fibonacci_sequence_property_sum(self) -> None:
        """Test Fibonacci property: F(n) = F(n-1) + F(n-2)."""
        for n in range(2, 15):
            f_n = fibonacci(n)
            f_n_minus_1 = fibonacci(n - 1)
            f_n_minus_2 = fibonacci(n - 2)
            assert f_n == f_n_minus_1 + f_n_minus_2, \
                f"fibonacci({n}) should equal fibonacci({n-1}) + fibonacci({n-2})"

    def test_fibonacci_monotonically_increasing(self) -> None:
        """Test that Fibonacci sequence is monotonically increasing for n >= 0."""
        previous = fibonacci(0)
        for n in range(1, 20):
            current = fibonacci(n)
            assert current >= previous, \
                f"fibonacci({n}) should be >= fibonacci({n-1})"
            previous = current

    def test_fibonacci_large_value(self) -> None:
        """Test Fibonacci calculation for larger value."""
        result = fibonacci(30)
        assert result == 832040
        assert isinstance(result, int)