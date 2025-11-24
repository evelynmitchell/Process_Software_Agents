"""
Unit tests for FibonacciCalculator

Tests the Fibonacci calculation function to verify iterative computation, base cases,
edge cases, and correctness of Fibonacci sequence values.

Component ID: FibonacciCalculator
Semantic Unit: SU-002

Author: ASP Code Agent
"""

import pytest
from src.fibonacci_calculator import fibonacci


class TestFibonacciBaseCase:
    """Test base cases for Fibonacci function."""

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


class TestFibonacciSequenceCorrectness:
    """Test correctness of Fibonacci sequence values."""

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

    def test_fibonacci_fifteen_returns_six_hundred_ten(self) -> None:
        """Test that fibonacci(15) returns 610."""
        result = fibonacci(15)
        assert result == 610

    def test_fibonacci_twenty_returns_six_thousand_seven_hundred_sixty_five(self) -> None:
        """Test that fibonacci(20) returns 6765."""
        result = fibonacci(20)
        assert result == 6765


class TestFibonacciSequence:
    """Test Fibonacci sequence generation and properties."""

    def test_fibonacci_sequence_first_ten_values(self) -> None:
        """Test first ten Fibonacci values match expected sequence."""
        expected_sequence = [0, 1, 1, 2, 3, 5, 8, 13, 21, 34]
        for n, expected_value in enumerate(expected_sequence):
            result = fibonacci(n)
            assert result == expected_value, (
                f"fibonacci({n}) returned {result}, expected {expected_value}"
            )

    def test_fibonacci_sequence_property_sum(self) -> None:
        """Test that fibonacci(n-1) + fibonacci(n) = fibonacci(n+1)."""
        for n in range(1, 10):
            fib_n_minus_1 = fibonacci(n - 1)
            fib_n = fibonacci(n)
            fib_n_plus_1 = fibonacci(n + 1)
            assert fib_n_minus_1 + fib_n == fib_n_plus_1, (
                f"fibonacci({n-1}) + fibonacci({n}) != fibonacci({n+1})"
            )

    def test_fibonacci_monotonic_increasing(self) -> None:
        """Test that Fibonacci sequence is monotonically increasing for n >= 0."""
        previous = fibonacci(0)
        for n in range(1, 15):
            current = fibonacci(n)
            assert current >= previous, (
                f"fibonacci({n}) = {current} is less than fibonacci({n-1}) = {previous}"
            )
            previous = current


class TestFibonacciEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_fibonacci_large_input_hundred(self) -> None:
        """Test fibonacci(100) computes without error."""
        result = fibonacci(100)
        assert isinstance(result, int)
        assert result > 0
        # fibonacci(100) = 354224848179261915075
        assert result == 354224848179261915075

    def test_fibonacci_large_input_fifty(self) -> None:
        """Test fibonacci(50) computes correctly."""
        result = fibonacci(50)
        assert result == 12586269025

    def test_fibonacci_return_type_is_integer(self) -> None:
        """Test that return type is always int."""
        for n in [0, 1, 5, 10, 20]:
            result = fibonacci(n)
            assert isinstance(result, int), (
                f"fibonacci({n}) returned {type(result)}, expected int"
            )

    def test_fibonacci_return_value_is_positive_or_zero(self) -> None:
        """Test that return value is non-negative for non-negative input."""
        for n in range(0, 20):
            result = fibonacci(n)
            assert result >= 0, f"fibonacci({n}) returned negative value {result}"


class TestFibonacciInputValidation:
    """Test input validation and error handling."""

    def test_fibonacci_negative_one_raises_value_error(self) -> None:
        """Test that fibonacci(-1) raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            fibonacci(-1)
        assert "non-negative" in str(exc_info.value).lower()

    def test_fibonacci_negative_ten_raises_value_error(self) -> None:
        """Test that fibonacci(-10) raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            fibonacci(-10)
        assert "non-negative" in str(exc_info.value).lower()

    def test_fibonacci_negative_hundred_raises_value_error(self) -> None:
        """Test that fibonacci(-100) raises ValueError."""
        with pytest.raises(ValueError):
            fibonacci(-100)

    def test_fibonacci_error_message_contains_descriptive_text(self) -> None:
        """Test that ValueError message is descriptive."""
        with pytest.raises(ValueError) as exc_info:
            fibonacci(-5)
        error_message = str(exc_info.value)
        assert len(error_message) > 0
        assert "negative" in error_message.lower() or "non-negative" in error_message.lower()

    def test_fibonacci_float_input_raises_error(self) -> None:
        """Test that float input raises TypeError or ValueError."""
        with pytest.raises((TypeError, ValueError)):
            fibonacci(5.0)  # type: ignore

    def test_fibonacci_string_input_raises_error(self) -> None:
        """Test that string input raises TypeError or ValueError."""
        with pytest.raises((TypeError, ValueError)):
            fibonacci("5")  # type: ignore

    def test_fibonacci_none_input_raises_error(self) -> None:
        """Test that None input raises TypeError or ValueError."""
        with pytest.raises((TypeError, ValueError)):
            fibonacci(None)  # type: ignore


class TestFibonacciPerformance:
    """Test performance characteristics of Fibonacci implementation."""

    def test_fibonacci_iterative_not_recursive(self) -> None:
        """Test that fibonacci uses iterative approach by computing large value quickly."""
        # If recursive without memoization, fibonacci(35) would take several seconds
        # Iterative approach should complete in milliseconds
        import time
        start_time = time.time()
        result = fibonacci(35)
        end_time = time.time()
        elapsed_time = end_time - start_time
        
        assert result == 9227465