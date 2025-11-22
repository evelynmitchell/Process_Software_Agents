"""
Unit tests for FibonacciCalculator component

Tests the Fibonacci calculation implementation verifying iterative algorithm correctness,
base case handling, edge cases, and performance characteristics.

Component ID: FibonacciCalculator
Semantic Unit ID: SU-002

Author: ASP Code Agent
"""

import pytest
from src.fibonacci import fibonacci


class TestFibonacciBaseCase:
    """Test base case handling for Fibonacci calculation."""

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

    def test_fibonacci_three_returns_two(self) -> None:
        """Test that fibonacci(3) returns 2."""
        result = fibonacci(3)
        assert result == 2


class TestFibonacciSequence:
    """Test Fibonacci sequence correctness for various inputs."""

    def test_fibonacci_five_returns_five(self) -> None:
        """Test that fibonacci(5) returns 5."""
        result = fibonacci(5)
        assert result == 5

    def test_fibonacci_ten_returns_fifty_five(self) -> None:
        """Test that fibonacci(10) returns 55."""
        result = fibonacci(10)
        assert result == 55

    def test_fibonacci_sequence_correctness(self) -> None:
        """Test that Fibonacci sequence is correct for multiple values."""
        expected_sequence = [0, 1, 1, 2, 3, 5, 8, 13, 21, 34, 55, 89, 144]
        for n, expected in enumerate(expected_sequence):
            result = fibonacci(n)
            assert result == expected, f"fibonacci({n}) should be {expected}, got {result}"

    def test_fibonacci_fifteen_returns_six_hundred_ten(self) -> None:
        """Test that fibonacci(15) returns 610."""
        result = fibonacci(15)
        assert result == 610

    def test_fibonacci_twenty_returns_six_thousand_seven_hundred_six(self) -> None:
        """Test that fibonacci(20) returns 6706."""
        result = fibonacci(20)
        assert result == 6765


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

    def test_fibonacci_float_raises_type_error_or_value_error(self) -> None:
        """Test that fibonacci(5.5) raises TypeError or ValueError."""
        with pytest.raises((TypeError, ValueError)):
            fibonacci(5.5)  # type: ignore

    def test_fibonacci_string_raises_type_error_or_value_error(self) -> None:
        """Test that fibonacci('5') raises TypeError or ValueError."""
        with pytest.raises((TypeError, ValueError)):
            fibonacci('5')  # type: ignore

    def test_fibonacci_none_raises_type_error_or_value_error(self) -> None:
        """Test that fibonacci(None) raises TypeError or ValueError."""
        with pytest.raises((TypeError, ValueError)):
            fibonacci(None)  # type: ignore

    def test_fibonacci_list_raises_type_error_or_value_error(self) -> None:
        """Test that fibonacci([5]) raises TypeError or ValueError."""
        with pytest.raises((TypeError, ValueError)):
            fibonacci([5])  # type: ignore

    def test_fibonacci_dict_raises_type_error_or_value_error(self) -> None:
        """Test that fibonacci({'n': 5}) raises TypeError or ValueError."""
        with pytest.raises((TypeError, ValueError)):
            fibonacci({'n': 5})  # type: ignore


class TestFibonacciReturnType:
    """Test return type correctness."""

    def test_fibonacci_returns_integer(self) -> None:
        """Test that fibonacci returns an integer type."""
        result = fibonacci(5)
        assert isinstance(result, int)

    def test_fibonacci_returns_integer_for_zero(self) -> None:
        """Test that fibonacci(0) returns integer type."""
        result = fibonacci(0)
        assert isinstance(result, int)
        assert not isinstance(result, bool)

    def test_fibonacci_returns_integer_for_large_n(self) -> None:
        """Test that fibonacci returns integer for large n."""
        result = fibonacci(50)
        assert isinstance(result, int)

    def test_fibonacci_returns_positive_integer(self) -> None:
        """Test that fibonacci returns non-negative integer."""
        for n in range(20):
            result = fibonacci(n)
            assert result >= 0


class TestFibonacciEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_fibonacci_zero_is_non_negative(self) -> None:
        """Test that fibonacci(0) returns non-negative value."""
        result = fibonacci(0)
        assert result >= 0

    def test_fibonacci_consecutive_values_increase(self) -> None:
        """Test that Fibonacci sequence is monotonically increasing."""
        prev = fibonacci(0)
        for n in range(1, 15):
            curr = fibonacci(n)
            assert curr >= prev, f"fibonacci({n}) should be >= fibonacci({n-1})"
            prev = curr

    def test_fibonacci_large_n_performance(self) -> None:
        """Test that fibonacci handles moderately large n efficiently."""
        # Should complete quickly with iterative approach
        result = fibonacci(100)
        assert isinstance(result, int)
        assert result > 0

    def test_fibonacci_very_large_n(self) -> None:
        """Test that fibonacci handles very large n."""
        result = fibonacci(1000)
        assert isinstance(result, int)
        assert result > 0

    def test_fibonacci_idempotent(self) -> None:
        """Test that calling fibonacci multiple times with same input returns same result."""
        n = 10
        result1 = fibonacci(n)
        result2 = fibonacci(n)
        result3 = fibonacci(n)
        assert result1 == result2 == result3


class TestFibonacciMathematicalProperties:
    """Test mathematical properties of Fibonacci sequence."""

    def test_fibonacci_sum_property(self) -> None:
        """Test that sum of first n Fibonacci numbers equals fibonacci(n+2) - 1."""
        n = 10
        fib_sum = sum(fibonacci(i) for i in range(n))
        expected = fibonacci(n + 2) - 1
        assert fib_sum == expected

    def test_fibonacci_golden_ratio_approximation(self) -> None:
        """Test that ratio of consecutive Fibonacci numbers approaches golden ratio."""
        # For large n, fibonacci(n+1) / fibonacci(n) approaches golden ratio (~1.618)
        golden_ratio = (1 + 5 ** 0.5) / 2
        n = 30
        ratio = fibonacci(n + 1) / fibonacci(n)
        # Should be within