"""
Unit tests for Fibonacci Calculator

Tests the fibonacci function to verify correct calculation of Fibonacci numbers,
proper handling of edge cases (n=0, n=1), validation of inputs, and correctness
of the iterative algorithm for various input values.

Component ID: FibonacciCalculator
Semantic Unit: SU-002

Author: ASP Code Agent
"""

import pytest
from src.fibonacci_calculator import fibonacci


class TestFibonacciBaseCase:
    """Test suite for Fibonacci base cases."""

    def test_fibonacci_n_zero_returns_zero(self) -> None:
        """Test that fibonacci(0) returns 0."""
        result = fibonacci(0)
        assert result == 0
        assert isinstance(result, int)

    def test_fibonacci_n_one_returns_one(self) -> None:
        """Test that fibonacci(1) returns 1."""
        result = fibonacci(1)
        assert result == 1
        assert isinstance(result, int)

    def test_fibonacci_n_two_returns_one(self) -> None:
        """Test that fibonacci(2) returns 1."""
        result = fibonacci(2)
        assert result == 1
        assert isinstance(result, int)


class TestFibonacciSmallValues:
    """Test suite for Fibonacci calculation with small values."""

    def test_fibonacci_n_three_returns_two(self) -> None:
        """Test that fibonacci(3) returns 2."""
        result = fibonacci(3)
        assert result == 2

    def test_fibonacci_n_four_returns_three(self) -> None:
        """Test that fibonacci(4) returns 3."""
        result = fibonacci(4)
        assert result == 3

    def test_fibonacci_n_five_returns_five(self) -> None:
        """Test that fibonacci(5) returns 5."""
        result = fibonacci(5)
        assert result == 5

    def test_fibonacci_n_six_returns_eight(self) -> None:
        """Test that fibonacci(6) returns 8."""
        result = fibonacci(6)
        assert result == 8

    def test_fibonacci_n_seven_returns_thirteen(self) -> None:
        """Test that fibonacci(7) returns 13."""
        result = fibonacci(7)
        assert result == 13

    def test_fibonacci_n_eight_returns_twentyone(self) -> None:
        """Test that fibonacci(8) returns 21."""
        result = fibonacci(8)
        assert result == 21

    def test_fibonacci_n_nine_returns_thirtyfour(self) -> None:
        """Test that fibonacci(9) returns 34."""
        result = fibonacci(9)
        assert result == 34

    def test_fibonacci_n_ten_returns_fiftyfive(self) -> None:
        """Test that fibonacci(10) returns 55."""
        result = fibonacci(10)
        assert result == 55


class TestFibonacciLargerValues:
    """Test suite for Fibonacci calculation with larger values."""

    def test_fibonacci_n_fifteen_returns_correct_value(self) -> None:
        """Test that fibonacci(15) returns 610."""
        result = fibonacci(15)
        assert result == 610

    def test_fibonacci_n_twenty_returns_correct_value(self) -> None:
        """Test that fibonacci(20) returns 6765."""
        result = fibonacci(20)
        assert result == 6765

    def test_fibonacci_n_twentyfive_returns_correct_value(self) -> None:
        """Test that fibonacci(25) returns 75025."""
        result = fibonacci(25)
        assert result == 75025

    def test_fibonacci_n_thirty_returns_correct_value(self) -> None:
        """Test that fibonacci(30) returns 832040."""
        result = fibonacci(30)
        assert result == 832040

    def test_fibonacci_n_fifty_returns_correct_value(self) -> None:
        """Test that fibonacci(50) returns 12586269025."""
        result = fibonacci(50)
        assert result == 12586269025

    def test_fibonacci_n_hundred_returns_correct_value(self) -> None:
        """Test that fibonacci(100) returns correct large Fibonacci number."""
        result = fibonacci(100)
        assert result == 354224848179261915075


class TestFibonacciNegativeInput:
    """Test suite for Fibonacci with negative input validation."""

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

    def test_fibonacci_error_message_contains_guidance(self) -> None:
        """Test that ValueError message provides clear guidance."""
        with pytest.raises(ValueError) as exc_info:
            fibonacci(-1)
        error_message = str(exc_info.value)
        assert "non-negative" in error_message.lower() or "negative" in error_message.lower()


class TestFibonacciTypeValidation:
    """Test suite for Fibonacci input type validation."""

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


class TestFibonacciReturnType:
    """Test suite for Fibonacci return type validation."""

    def test_fibonacci_returns_integer_type(self) -> None:
        """Test that fibonacci returns int type, not float or other."""
        result = fibonacci(5)
        assert isinstance(result, int)
        assert not isinstance(result, bool)

    def test_fibonacci_returns_positive_integer_for_positive_input(self) -> None:
        """Test that fibonacci returns positive integer for positive input."""
        result = fibonacci(10)
        assert isinstance(result, int)
        assert result > 0

    def test_fibonacci_returns_zero_for_zero_input(self) -> None:
        """Test that fibonacci returns zero (non-negative) for zero input."""
        result = fibonacci(0)
        assert isinstance(result, int)
        assert result >= 0

    def test_fibonacci_never_returns_negative(self) -> None:
        """Test that fibonacci never returns negative value for valid input."""
        for n in range(0, 20):
            result = fibonacci(n)
            assert result >= 0


class TestFibonacciSequenceCorrectness:
    """Test suite for verifying Fibonacci sequence correctness."""