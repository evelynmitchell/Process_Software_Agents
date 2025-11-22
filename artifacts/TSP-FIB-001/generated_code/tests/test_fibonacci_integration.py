"""
Integration tests for Fibonacci function

End-to-end integration tests verifying complete workflow from input validation
through calculation with large inputs and performance characteristics.

Semantic Unit ID: SU-003
Component ID: FibonacciFunction

Author: ASP Code Agent
"""

import pytest
import time
from src.fibonacci import fibonacci


class TestFibonacciInputValidation:
    """Test suite for input validation in Fibonacci function."""

    def test_fibonacci_accepts_zero(self) -> None:
        """Test that fibonacci accepts 0 as valid input."""
        result = fibonacci(0)
        assert result == 0

    def test_fibonacci_accepts_positive_integer(self) -> None:
        """Test that fibonacci accepts positive integers."""
        result = fibonacci(5)
        assert isinstance(result, int)
        assert result == 5

    def test_fibonacci_rejects_negative_integer(self) -> None:
        """Test that fibonacci raises ValueError for negative input."""
        with pytest.raises(ValueError) as exc_info:
            fibonacci(-1)
        assert "non-negative" in str(exc_info.value).lower()

    def test_fibonacci_rejects_large_negative_integer(self) -> None:
        """Test that fibonacci raises ValueError for large negative input."""
        with pytest.raises(ValueError) as exc_info:
            fibonacci(-100)
        assert "non-negative" in str(exc_info.value).lower()

    def test_fibonacci_rejects_float_input(self) -> None:
        """Test that fibonacci rejects float input."""
        with pytest.raises((ValueError, TypeError)):
            fibonacci(5.0)  # type: ignore

    def test_fibonacci_rejects_string_input(self) -> None:
        """Test that fibonacci rejects string input."""
        with pytest.raises((ValueError, TypeError)):
            fibonacci("5")  # type: ignore

    def test_fibonacci_rejects_none_input(self) -> None:
        """Test that fibonacci rejects None input."""
        with pytest.raises((ValueError, TypeError)):
            fibonacci(None)  # type: ignore

    def test_fibonacci_rejects_list_input(self) -> None:
        """Test that fibonacci rejects list input."""
        with pytest.raises((ValueError, TypeError)):
            fibonacci([5])  # type: ignore

    def test_fibonacci_error_message_descriptive(self) -> None:
        """Test that error message for negative input is descriptive."""
        with pytest.raises(ValueError) as exc_info:
            fibonacci(-5)
        error_message = str(exc_info.value)
        assert len(error_message) > 0
        assert "non-negative" in error_message.lower() or "negative" in error_message.lower()


class TestFibonacciEdgeCases:
    """Test suite for edge cases in Fibonacci calculation."""

    def test_fibonacci_base_case_zero(self) -> None:
        """Test that fibonacci(0) returns 0."""
        assert fibonacci(0) == 0

    def test_fibonacci_base_case_one(self) -> None:
        """Test that fibonacci(1) returns 1."""
        assert fibonacci(1) == 1

    def test_fibonacci_base_case_two(self) -> None:
        """Test that fibonacci(2) returns 1."""
        assert fibonacci(2) == 1

    def test_fibonacci_base_case_three(self) -> None:
        """Test that fibonacci(3) returns 2."""
        assert fibonacci(3) == 2

    def test_fibonacci_small_values(self) -> None:
        """Test fibonacci for small values."""
        expected_values = {
            0: 0,
            1: 1,
            2: 1,
            3: 2,
            4: 3,
            5: 5,
            6: 8,
            7: 13,
            8: 21,
            9: 34,
            10: 55,
        }
        for n, expected in expected_values.items():
            assert fibonacci(n) == expected, f"fibonacci({n}) should be {expected}"


class TestFibonacciCorrectness:
    """Test suite for correctness of Fibonacci calculation."""

    def test_fibonacci_sequence_property(self) -> None:
        """Test that Fibonacci sequence property holds: F(n) = F(n-1) + F(n-2)."""
        for n in range(2, 15):
            fib_n = fibonacci(n)
            fib_n_minus_1 = fibonacci(n - 1)
            fib_n_minus_2 = fibonacci(n - 2)
            assert fib_n == fib_n_minus_1 + fib_n_minus_2

    def test_fibonacci_monotonic_increasing(self) -> None:
        """Test that Fibonacci sequence is monotonically increasing for n >= 0."""
        previous = fibonacci(0)
        for n in range(1, 20):
            current = fibonacci(n)
            assert current >= previous, f"fibonacci({n}) should be >= fibonacci({n-1})"
            previous = current

    def test_fibonacci_returns_integer(self) -> None:
        """Test that fibonacci always returns an integer."""
        for n in range(0, 20):
            result = fibonacci(n)
            assert isinstance(result, int), f"fibonacci({n}) should return int, got {type(result)}"

    def test_fibonacci_returns_non_negative(self) -> None:
        """Test that fibonacci returns non-negative values for non-negative input."""
        for n in range(0, 20):
            result = fibonacci(n)
            assert result >= 0, f"fibonacci({n}) should be non-negative"

    def test_fibonacci_known_values(self) -> None:
        """Test fibonacci against known values from mathematical reference."""
        known_values = {
            0: 0,
            1: 1,
            5: 5,
            10: 55,
            15: 610,
            20: 6765,
            25: 75025,
        }
        for n, expected in known_values.items():
            assert fibonacci(n) == expected, f"fibonacci({n}) should be {expected}"


class TestFibonacciLargeInputs:
    """Test suite for large input values."""

    def test_fibonacci_large_input_50(self) -> None:
        """Test fibonacci with n=50."""
        result = fibonacci(50)
        assert result == 12586269025
        assert isinstance(result, int)

    def test_fibonacci_large_input_100(self) -> None:
        """Test fibonacci with n=100."""
        result = fibonacci(100)
        expected = 354224848179261915075
        assert result == expected

    def test_fibonacci_very_large_input_200(self) -> None:
        """Test fibonacci with n=200 (tests arbitrary precision)."""
        result = fibonacci(200)
        assert isinstance(result, int)
        assert result > 0
        # Verify it's a very large number
        assert len(str(result)) > 40

    def test_fibonacci_large_input_no_overflow(self) -> None:
        """Test that large Fibonacci numbers don't overflow (Python 3 feature)."""
        result = fibonacci(150)
        assert isinstance(result, int)
        assert result > 0
        # Should be able to perform arithmetic on result without overflow
        doubled = result * 2
        assert doubled == result + result

    def test_fibonacci_large_input_consistency(self) -> None:
        """Test that large Fibonacci values are consistent across calls."""
        result1 = fibonacci(75)
        result2 = fibonacci(75)
        assert result1 == result2


class TestFibonacciPerformance:
    """Test suite for performance characteristics."""

    def test_fibonacci_small_input_performance(self) -> None:
        """Test that fibonacci(10) completes quickly."""
        start_time = time.time()
        fibonacci(10)
        elapsed_time = time.time() - start_time
        assert elapsed_time < 0.1, "fibonacci(10) should complete in less than 100ms"

    def test_fibonacci_medium_input