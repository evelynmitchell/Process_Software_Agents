"""
Integration tests for Fibonacci function

Tests the public fibonacci function to verify end-to-end behavior including error handling,
edge cases, and documented examples.

Component ID: FibonacciFunction
Semantic Unit: SU-003

Author: ASP Code Agent
"""

import pytest
from src.fibonacci import fibonacci


class TestFibonacciBaseCase:
    """Test Fibonacci function base cases (n=0 and n=1)."""

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


class TestFibonacciSequence:
    """Test Fibonacci function for correct sequence values."""

    def test_fibonacci_three_returns_two(self) -> None:
        """Test that fibonacci(3) returns 2."""
        result = fibonacci(3)
        assert result == 2

    def test_fibonacci_four_returns_three(self) -> None:
        """Test that fibonacci(4) returns 3."""
        result = fibonacci(4)
        assert result == 3

    def test_fibonacci_five_returns_five(self) -> None:
        """Test that fibonacci(5) returns 5."""
        result = fibonacci(5)
        assert result == 5

    def test_fibonacci_six_returns_eight(self) -> None:
        """Test that fibonacci(6) returns 8."""
        result = fibonacci(6)
        assert result == 8

    def test_fibonacci_ten_returns_fifty_five(self) -> None:
        """Test that fibonacci(10) returns 55."""
        result = fibonacci(10)
        assert result == 55

    def test_fibonacci_fifteen_returns_correct_value(self) -> None:
        """Test that fibonacci(15) returns 610."""
        result = fibonacci(15)
        assert result == 610

    def test_fibonacci_twenty_returns_correct_value(self) -> None:
        """Test that fibonacci(20) returns 6765."""
        result = fibonacci(20)
        assert result == 6765

    def test_fibonacci_sequence_is_monotonic_increasing(self) -> None:
        """Test that Fibonacci sequence is monotonically increasing for n >= 0."""
        previous = fibonacci(0)
        for n in range(1, 15):
            current = fibonacci(n)
            assert current >= previous
            previous = current

    def test_fibonacci_sequence_satisfies_recurrence_relation(self) -> None:
        """Test that fibonacci(n) = fibonacci(n-1) + fibonacci(n-2) for n >= 2."""
        for n in range(2, 20):
            fib_n = fibonacci(n)
            fib_n_minus_1 = fibonacci(n - 1)
            fib_n_minus_2 = fibonacci(n - 2)
            assert fib_n == fib_n_minus_1 + fib_n_minus_2


class TestFibonacciNegativeInput:
    """Test Fibonacci function error handling for negative inputs."""

    def test_fibonacci_negative_one_raises_value_error(self) -> None:
        """Test that fibonacci(-1) raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            fibonacci(-1)
        assert "non-negative" in str(exc_info.value).lower()

    def test_fibonacci_negative_five_raises_value_error(self) -> None:
        """Test that fibonacci(-5) raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            fibonacci(-5)
        assert "non-negative" in str(exc_info.value).lower()

    def test_fibonacci_negative_hundred_raises_value_error(self) -> None:
        """Test that fibonacci(-100) raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            fibonacci(-100)
        assert "non-negative" in str(exc_info.value).lower()

    def test_fibonacci_error_message_contains_constraint_info(self) -> None:
        """Test that ValueError message contains information about constraint."""
        with pytest.raises(ValueError) as exc_info:
            fibonacci(-1)
        error_message = str(exc_info.value).lower()
        assert "non-negative" in error_message or "negative" in error_message


class TestFibonacciTypeValidation:
    """Test Fibonacci function type validation and rejection of invalid types."""

    def test_fibonacci_float_input_raises_error(self) -> None:
        """Test that fibonacci(5.5) raises ValueError or TypeError."""
        with pytest.raises((ValueError, TypeError)):
            fibonacci(5.5)  # type: ignore

    def test_fibonacci_string_input_raises_error(self) -> None:
        """Test that fibonacci('5') raises ValueError or TypeError."""
        with pytest.raises((ValueError, TypeError)):
            fibonacci('5')  # type: ignore

    def test_fibonacci_none_input_raises_error(self) -> None:
        """Test that fibonacci(None) raises ValueError or TypeError."""
        with pytest.raises((ValueError, TypeError)):
            fibonacci(None)  # type: ignore

    def test_fibonacci_list_input_raises_error(self) -> None:
        """Test that fibonacci([5]) raises ValueError or TypeError."""
        with pytest.raises((ValueError, TypeError)):
            fibonacci([5])  # type: ignore

    def test_fibonacci_dict_input_raises_error(self) -> None:
        """Test that fibonacci({'n': 5}) raises ValueError or TypeError."""
        with pytest.raises((ValueError, TypeError)):
            fibonacci({'n': 5})  # type: ignore

    def test_fibonacci_float_zero_raises_error(self) -> None:
        """Test that fibonacci(0.0) raises ValueError or TypeError."""
        with pytest.raises((ValueError, TypeError)):
            fibonacci(0.0)  # type: ignore

    def test_fibonacci_float_one_raises_error(self) -> None:
        """Test that fibonacci(1.0) raises ValueError or TypeError."""
        with pytest.raises((ValueError, TypeError)):
            fibonacci(1.0)  # type: ignore


class TestFibonacciReturnType:
    """Test Fibonacci function return type consistency."""

    def test_fibonacci_returns_integer_type(self) -> None:
        """Test that fibonacci returns int type for valid input."""
        result = fibonacci(5)
        assert isinstance(result, int)
        assert not isinstance(result, bool)

    def test_fibonacci_returns_integer_for_zero(self) -> None:
        """Test that fibonacci(0) returns int type."""
        result = fibonacci(0)
        assert isinstance(result, int)

    def test_fibonacci_returns_integer_for_large_n(self) -> None:
        """Test that fibonacci returns int type for larger values."""
        result = fibonacci(30)
        assert isinstance(result, int)

    def test_fibonacci_returns_non_negative_integer(self) -> None:
        """Test that fibonacci returns non-negative integer for valid input."""
        for n in range(0, 20):
            result = fibonacci(n)
            assert isinstance(result, int)
            assert result >= 0


class TestFibonacciLargeValues:
    """Test Fibonacci function with larger input values."""

    def test_fibonacci_twenty_five(self) -> None:
        """Test that fibonacci(25) returns correct value."""
        result = fibonacci(25)
        assert result == 75025

    def test_fibonacci_thirty(self) -> None:
        """Test that fibonacci(30) returns correct value."""
        result = fibonacci(30)
        assert result == 832040

    def test_fibonacci_thirty_five(self) -> None:
        """Test that fibonacci(