"""
Integration tests for Fibonacci function

Tests the fibonacci function covering valid inputs, negative inputs, edge cases,
type validation, and comprehensive sequence verification.

Component ID: FibonacciFunction
Semantic Unit: SU-003

Author: ASP Code Agent
"""

import pytest
from src.fibonacci import fibonacci


class TestFibonacciValidInput:
    """Test fibonacci function with valid non-negative integer inputs."""

    def test_fibonacci_zero_returns_zero(self) -> None:
        """Test that fibonacci(0) returns 0 (base case)."""
        result = fibonacci(0)
        assert result == 0
        assert isinstance(result, int)

    def test_fibonacci_one_returns_one(self) -> None:
        """Test that fibonacci(1) returns 1 (base case)."""
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

    def test_fibonacci_sequence_correctness(self) -> None:
        """Test that first 10 Fibonacci numbers match expected sequence."""
        expected_sequence = [0, 1, 1, 2, 3, 5, 8, 13, 21, 34]
        for n, expected in enumerate(expected_sequence):
            result = fibonacci(n)
            assert result == expected, f"fibonacci({n}) should be {expected}, got {result}"

    def test_fibonacci_large_input(self) -> None:
        """Test that fibonacci handles large inputs (n=100)."""
        result = fibonacci(100)
        assert isinstance(result, int)
        assert result > 0
        # fibonacci(100) = 354224848179261915075
        assert result == 354224848179261915075

    def test_fibonacci_very_large_input(self) -> None:
        """Test that fibonacci handles very large inputs (n=1000)."""
        result = fibonacci(1000)
        assert isinstance(result, int)
        assert result > 0
        # Verify it's a very large number with expected magnitude
        assert len(str(result)) > 200

    def test_fibonacci_return_type_is_int(self) -> None:
        """Test that fibonacci always returns int type."""
        for n in [0, 1, 5, 10, 20]:
            result = fibonacci(n)
            assert isinstance(result, int), f"fibonacci({n}) should return int, got {type(result)}"

    def test_fibonacci_monotonic_increasing(self) -> None:
        """Test that Fibonacci sequence is monotonically increasing for n >= 0."""
        previous = fibonacci(0)
        for n in range(1, 15):
            current = fibonacci(n)
            assert current >= previous, f"fibonacci({n}) should be >= fibonacci({n-1})"
            previous = current

    def test_fibonacci_positive_for_positive_n(self) -> None:
        """Test that fibonacci returns positive values for n > 0."""
        for n in range(1, 20):
            result = fibonacci(n)
            assert result > 0, f"fibonacci({n}) should be positive"


class TestFibonacciNegativeInput:
    """Test fibonacci function with negative integer inputs."""

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

    def test_fibonacci_negative_input_error_message(self) -> None:
        """Test that ValueError message is descriptive for negative input."""
        with pytest.raises(ValueError) as exc_info:
            fibonacci(-1)
        error_message = str(exc_info.value)
        assert len(error_message) > 0
        assert "negative" in error_message.lower() or "non-negative" in error_message.lower()

    def test_fibonacci_multiple_negative_inputs_all_raise_error(self) -> None:
        """Test that all negative inputs raise ValueError."""
        negative_inputs = [-1, -2, -10, -100, -1000]
        for n in negative_inputs:
            with pytest.raises(ValueError):
                fibonacci(n)


class TestFibonacciTypeValidation:
    """Test fibonacci function type validation and edge cases."""

    def test_fibonacci_float_input_raises_error(self) -> None:
        """Test that fibonacci rejects float input like 5.0."""
        with pytest.raises((ValueError, TypeError)):
            fibonacci(5.0)  # type: ignore

    def test_fibonacci_string_input_raises_error(self) -> None:
        """Test that fibonacci rejects string input."""
        with pytest.raises((ValueError, TypeError)):
            fibonacci("5")  # type: ignore

    def test_fibonacci_none_input_raises_error(self) -> None:
        """Test that fibonacci rejects None input."""
        with pytest.raises((ValueError, TypeError)):
            fibonacci(None)  # type: ignore

    def test_fibonacci_list_input_raises_error(self) -> None:
        """Test that fibonacci rejects list input."""
        with pytest.raises((ValueError, TypeError)):
            fibonacci([5])  # type: ignore

    def test_fibonacci_dict_input_raises_error(self) -> None:
        """Test that fibonacci rejects dict input."""
        with pytest.raises((ValueError, TypeError)):
            fibonacci({"n": 5})  # type: ignore

    def test_fibonacci_boolean_input_handling(self) -> None:
        """Test fibonacci behavior with boolean input (True=1, False=0 in Python)."""
        # In Python, bool is a subclass of int, so True and False are valid integers
        # True == 1, False == 0
        result_false = fibonacci(False)  # type: ignore
        result_true = fibonacci(True)  # type: ignore
        assert result_false == fibonacci(0)
        assert result_true == fibonacci(1)


class TestFib