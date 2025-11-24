"""
Unit tests for FibonacciCalculator.calculate() method

Tests the Fibonacci sequence computation for edge cases and various input values,
verifying correct calculation of the nth Fibonacci number using the iterative approach.

Component ID: FibonacciCalculator
Semantic Unit ID: SU-002

Author: ASP Code Agent
"""

import pytest
from src.fibonacci import fibonacci, FibonacciCalculator, FibonacciValidator


class TestFibonacciValidator:
    """Test suite for FibonacciValidator.validate_input() method."""

    def test_validate_input_zero_is_valid(self) -> None:
        """Test that validate_input accepts zero as valid input."""
        validator = FibonacciValidator()
        assert validator.validate_input(0) is True

    def test_validate_input_one_is_valid(self) -> None:
        """Test that validate_input accepts one as valid input."""
        validator = FibonacciValidator()
        assert validator.validate_input(1) is True

    def test_validate_input_positive_integer_is_valid(self) -> None:
        """Test that validate_input accepts positive integers as valid input."""
        validator = FibonacciValidator()
        assert validator.validate_input(5) is True
        assert validator.validate_input(100) is True
        assert validator.validate_input(1000) is True

    def test_validate_input_negative_integer_raises_error(self) -> None:
        """Test that validate_input raises ValueError for negative integers."""
        validator = FibonacciValidator()
        with pytest.raises(ValueError, match="non-negative"):
            validator.validate_input(-1)

    def test_validate_input_large_negative_integer_raises_error(self) -> None:
        """Test that validate_input raises ValueError for large negative integers."""
        validator = FibonacciValidator()
        with pytest.raises(ValueError, match="non-negative"):
            validator.validate_input(-100)

    def test_validate_input_error_message_content(self) -> None:
        """Test that ValueError message contains 'non-negative' for invalid input."""
        validator = FibonacciValidator()
        with pytest.raises(ValueError) as exc_info:
            validator.validate_input(-5)
        assert "non-negative" in str(exc_info.value).lower()

    def test_validate_input_boolean_true_raises_error(self) -> None:
        """Test that validate_input rejects boolean True (even though bool is subclass of int)."""
        validator = FibonacciValidator()
        with pytest.raises(ValueError):
            validator.validate_input(True)

    def test_validate_input_boolean_false_raises_error(self) -> None:
        """Test that validate_input rejects boolean False (even though bool is subclass of int)."""
        validator = FibonacciValidator()
        with pytest.raises(ValueError):
            validator.validate_input(False)


class TestFibonacciCalculator:
    """Test suite for FibonacciCalculator.calculate() method."""

    def test_calculate_zero_returns_zero(self) -> None:
        """Test that calculate(0) returns 0 (first Fibonacci number)."""
        calculator = FibonacciCalculator()
        assert calculator.calculate(0) == 0

    def test_calculate_one_returns_one(self) -> None:
        """Test that calculate(1) returns 1 (second Fibonacci number)."""
        calculator = FibonacciCalculator()
        assert calculator.calculate(1) == 1

    def test_calculate_two_returns_one(self) -> None:
        """Test that calculate(2) returns 1 (third Fibonacci number)."""
        calculator = FibonacciCalculator()
        assert calculator.calculate(2) == 1

    def test_calculate_three_returns_two(self) -> None:
        """Test that calculate(3) returns 2 (fourth Fibonacci number)."""
        calculator = FibonacciCalculator()
        assert calculator.calculate(3) == 2

    def test_calculate_four_returns_three(self) -> None:
        """Test that calculate(4) returns 3 (fifth Fibonacci number)."""
        calculator = FibonacciCalculator()
        assert calculator.calculate(4) == 3

    def test_calculate_five_returns_five(self) -> None:
        """Test that calculate(5) returns 5 (sixth Fibonacci number)."""
        calculator = FibonacciCalculator()
        assert calculator.calculate(5) == 5

    def test_calculate_six_returns_eight(self) -> None:
        """Test that calculate(6) returns 8 (seventh Fibonacci number)."""
        calculator = FibonacciCalculator()
        assert calculator.calculate(6) == 8

    def test_calculate_ten_returns_fifty_five(self) -> None:
        """Test that calculate(10) returns 55 (eleventh Fibonacci number)."""
        calculator = FibonacciCalculator()
        assert calculator.calculate(10) == 55

    def test_calculate_fifteen_returns_six_hundred_ten(self) -> None:
        """Test that calculate(15) returns 610 (sixteenth Fibonacci number)."""
        calculator = FibonacciCalculator()
        assert calculator.calculate(15) == 610

    def test_calculate_twenty_returns_correct_value(self) -> None:
        """Test that calculate(20) returns 6765 (twenty-first Fibonacci number)."""
        calculator = FibonacciCalculator()
        assert calculator.calculate(20) == 6765

    def test_calculate_large_input_hundred(self) -> None:
        """Test that calculate(100) returns correct large Fibonacci number."""
        calculator = FibonacciCalculator()
        result = calculator.calculate(100)
        assert result == 354224848179261915075

    def test_calculate_returns_integer_type(self) -> None:
        """Test that calculate() returns an integer type."""
        calculator = FibonacciCalculator()
        result = calculator.calculate(5)
        assert isinstance(result, int)

    def test_calculate_sequence_correctness(self) -> None:
        """Test that calculate() produces correct Fibonacci sequence for multiple values."""
        calculator = FibonacciCalculator()
        expected_sequence = [0, 1, 1, 2, 3, 5, 8, 13, 21, 34, 55]
        for n, expected in enumerate(expected_sequence):
            assert calculator.calculate(n) == expected

    def test_calculate_consecutive_values_relationship(self) -> None:
        """Test that consecutive Fibonacci numbers follow the recurrence relation."""
        calculator = FibonacciCalculator()
        for n in range(2, 20):
            fib_n_minus_2 = calculator.calculate(n - 2)
            fib_n_minus_1 = calculator.calculate(n - 1)
            fib_n = calculator.calculate(n)
            assert fib_n == fib_n_minus_2 + fib_n_minus_1

    def test_calculate_monotonic_increasing(self) -> None:
        """Test that Fibonacci sequence is monotonically increasing for n >= 0."""
        calculator = FibonacciCalculator()
        previous = calculator.calculate(0)
        for n in range(1, 30):
            current = calculator.calculate(n)
            assert current >= previous
            previous = current


class TestFibonacciFunction:
    """Test suite for fibonacci() public API function."""

    def test_fibonacci_zero_returns_zero(self) -> None:
        """Test that fibonacci(0) returns 0."""
        assert fibonacci(0) == 0

    def test_fibonacci_one_returns_one(self) -> None:
        """Test that fibonacci(1) returns 1."""
        assert fibonacci(1) == 1

    def test_fibonacci_two_returns_one(self) -> None:
        """Test that fibonacci(2) returns 1."""
        assert fibonacci(2) == 1