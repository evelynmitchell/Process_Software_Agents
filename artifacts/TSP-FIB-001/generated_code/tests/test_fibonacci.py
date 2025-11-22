"""
Comprehensive unit tests for the Fibonacci module.

Tests cover input validation, edge cases, correctness of calculations, error handling
for negative inputs, and type checking for the Fibonacci function.

Component IDs: FibonacciValidator, FibonacciCalculator, FibonacciFunction
Semantic Units: SU-001, SU-002, SU-003

Author: ASP Code Agent
"""

import pytest
from src.fibonacci import fibonacci


class TestFibonacciInputValidation:
    """Test suite for input validation (SU-001: FibonacciValidator)."""

    def test_fibonacci_rejects_negative_integer(self) -> None:
        """Test that fibonacci raises ValueError for negative integer input."""
        with pytest.raises(ValueError, match="n must be a non-negative integer"):
            fibonacci(-1)

    def test_fibonacci_rejects_large_negative_integer(self) -> None:
        """Test that fibonacci raises ValueError for large negative integer."""
        with pytest.raises(ValueError, match="n must be a non-negative integer"):
            fibonacci(-1000)

    def test_fibonacci_rejects_float_input(self) -> None:
        """Test that fibonacci raises TypeError for float input."""
        with pytest.raises(TypeError):
            fibonacci(5.5)  # type: ignore

    def test_fibonacci_rejects_string_input(self) -> None:
        """Test that fibonacci raises TypeError for string input."""
        with pytest.raises(TypeError):
            fibonacci("5")  # type: ignore

    def test_fibonacci_rejects_none_input(self) -> None:
        """Test that fibonacci raises TypeError for None input."""
        with pytest.raises(TypeError):
            fibonacci(None)  # type: ignore

    def test_fibonacci_rejects_list_input(self) -> None:
        """Test that fibonacci raises TypeError for list input."""
        with pytest.raises(TypeError):
            fibonacci([5])  # type: ignore

    def test_fibonacci_rejects_dict_input(self) -> None:
        """Test that fibonacci raises TypeError for dict input."""
        with pytest.raises(TypeError):
            fibonacci({"n": 5})  # type: ignore

    def test_fibonacci_accepts_zero(self) -> None:
        """Test that fibonacci accepts zero as valid input."""
        result = fibonacci(0)
        assert isinstance(result, int)
        assert result == 0

    def test_fibonacci_accepts_positive_integer(self) -> None:
        """Test that fibonacci accepts positive integer input."""
        result = fibonacci(5)
        assert isinstance(result, int)
        assert result == 5

    def test_fibonacci_accepts_large_positive_integer(self) -> None:
        """Test that fibonacci accepts large positive integer input."""
        result = fibonacci(100)
        assert isinstance(result, int)
        assert result > 0


class TestFibonacciEdgeCases:
    """Test suite for edge cases (SU-002: FibonacciCalculator base cases)."""

    def test_fibonacci_zero_returns_zero(self) -> None:
        """Test that fibonacci(0) returns 0."""
        assert fibonacci(0) == 0

    def test_fibonacci_one_returns_one(self) -> None:
        """Test that fibonacci(1) returns 1."""
        assert fibonacci(1) == 1

    def test_fibonacci_two_returns_one(self) -> None:
        """Test that fibonacci(2) returns 1."""
        assert fibonacci(2) == 1

    def test_fibonacci_three_returns_two(self) -> None:
        """Test that fibonacci(3) returns 2."""
        assert fibonacci(3) == 2

    def test_fibonacci_four_returns_three(self) -> None:
        """Test that fibonacci(4) returns 3."""
        assert fibonacci(4) == 3

    def test_fibonacci_five_returns_five(self) -> None:
        """Test that fibonacci(5) returns 5."""
        assert fibonacci(5) == 5

    def test_fibonacci_six_returns_eight(self) -> None:
        """Test that fibonacci(6) returns 8."""
        assert fibonacci(6) == 8


class TestFibonacciCorrectness:
    """Test suite for correctness of Fibonacci calculations (SU-002: FibonacciCalculator)."""

    def test_fibonacci_sequence_correctness(self) -> None:
        """Test that fibonacci produces correct sequence values."""
        expected_sequence = [0, 1, 1, 2, 3, 5, 8, 13, 21, 34, 55, 89, 144]
        for n, expected in enumerate(expected_sequence):
            assert fibonacci(n) == expected, f"fibonacci({n}) should be {expected}"

    def test_fibonacci_ten_returns_fifty_five(self) -> None:
        """Test that fibonacci(10) returns 55."""
        assert fibonacci(10) == 55

    def test_fibonacci_fifteen_returns_six_hundred_ten(self) -> None:
        """Test that fibonacci(15) returns 610."""
        assert fibonacci(15) == 610

    def test_fibonacci_twenty_returns_six_thousand_seven_hundred_sixty_five(self) -> None:
        """Test that fibonacci(20) returns 6765."""
        assert fibonacci(20) == 6765

    def test_fibonacci_twenty_five_returns_correct_value(self) -> None:
        """Test that fibonacci(25) returns 75025."""
        assert fibonacci(25) == 75025

    def test_fibonacci_thirty_returns_correct_value(self) -> None:
        """Test that fibonacci(30) returns 832040."""
        assert fibonacci(30) == 832040

    def test_fibonacci_property_sum_of_previous_two(self) -> None:
        """Test that each Fibonacci number is sum of previous two."""
        for n in range(2, 20):
            assert fibonacci(n) == fibonacci(n - 1) + fibonacci(n - 2)

    def test_fibonacci_monotonically_increasing(self) -> None:
        """Test that Fibonacci sequence is monotonically increasing."""
        previous = fibonacci(0)
        for n in range(1, 30):
            current = fibonacci(n)
            assert current >= previous, f"fibonacci({n}) should be >= fibonacci({n-1})"
            previous = current

    def test_fibonacci_positive_for_positive_input(self) -> None:
        """Test that fibonacci returns positive values for positive inputs."""
        for n in range(1, 20):
            assert fibonacci(n) > 0, f"fibonacci({n}) should be positive"


class TestFibonacciReturnType:
    """Test suite for return type validation."""

    def test_fibonacci_returns_integer(self) -> None:
        """Test that fibonacci returns an integer type."""
        result = fibonacci(5)
        assert isinstance(result, int)
        assert not isinstance(result, bool)

    def test_fibonacci_returns_integer_for_zero(self) -> None:
        """Test that fibonacci returns integer for input 0."""
        result = fibonacci(0)
        assert isinstance(result, int)

    def test_fibonacci_returns_integer_for_one(self) -> None:
        """Test that fibonacci returns integer for input 1."""
        result = fibonacci(1)
        assert isinstance(result, int)

    def test_fibonacci_returns_integer_for_large_input(self) -> None:
        """Test that fibonacci returns integer for large input."""
        result = fibonacci(50)
        assert isinstance(result, int)

    def test_fibonacci_never_returns_float(self) -> None:
        """Test that fibonacci never returns float type."""
        for n in range(0, 20):
            result = fibonacci(n)
            assert not isinstance(result, float)

    def test_fibonacci_never_returns_none(self) -> None:
        """Test that fibonacci never returns None."""
        for n in range(0, 20):
            result = fibonacci(n)
            assert result is not None


class TestFibonacciErrorMessages:
    """Test suite for error message quality."""

    def test_fibonacci_negative_error_message_clarity(self) -> None:
        """Test that ValueError message