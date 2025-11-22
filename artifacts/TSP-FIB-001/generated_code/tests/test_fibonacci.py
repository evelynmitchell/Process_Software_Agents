import pytest
from src.fibonacci import fibonacci


class TestFibonacciCorrectness:
    """Test suite for Fibonacci sequence correctness.
    
    Validates that the fibonacci function returns correct values for the
    Fibonacci sequence. Tests cover base cases, standard cases, and larger values.
    
    Component ID: FibonacciCalculator
    Semantic Unit: SU-002
    """

    def test_fibonacci_n_zero_returns_zero(self) -> None:
        """Test that fibonacci(0) returns 0 (base case)."""
        result = fibonacci(0)
        assert result == 0
        assert isinstance(result, int)

    def test_fibonacci_n_one_returns_one(self) -> None:
        """Test that fibonacci(1) returns 1 (base case)."""
        result = fibonacci(1)
        assert result == 1
        assert isinstance(result, int)

    def test_fibonacci_n_two_returns_one(self) -> None:
        """Test that fibonacci(2) returns 1."""
        result = fibonacci(2)
        assert result == 1
        assert isinstance(result, int)

    def test_fibonacci_n_three_returns_two(self) -> None:
        """Test that fibonacci(3) returns 2."""
        result = fibonacci(3)
        assert result == 2
        assert isinstance(result, int)

    def test_fibonacci_n_four_returns_three(self) -> None:
        """Test that fibonacci(4) returns 3."""
        result = fibonacci(4)
        assert result == 3
        assert isinstance(result, int)

    def test_fibonacci_n_five_returns_five(self) -> None:
        """Test that fibonacci(5) returns 5."""
        result = fibonacci(5)
        assert result == 5
        assert isinstance(result, int)

    def test_fibonacci_n_six_returns_eight(self) -> None:
        """Test that fibonacci(6) returns 8."""
        result = fibonacci(6)
        assert result == 8
        assert isinstance(result, int)

    def test_fibonacci_n_ten_returns_fifty_five(self) -> None:
        """Test that fibonacci(10) returns 55."""
        result = fibonacci(10)
        assert result == 55
        assert isinstance(result, int)

    def test_fibonacci_n_fifteen_returns_six_hundred_ten(self) -> None:
        """Test that fibonacci(15) returns 610."""
        result = fibonacci(15)
        assert result == 610
        assert isinstance(result, int)

    def test_fibonacci_sequence_correctness(self) -> None:
        """Test that fibonacci produces correct sequence for multiple values."""
        expected_sequence = [0, 1, 1, 2, 3, 5, 8, 13, 21, 34, 55, 89, 144]
        for n, expected_value in enumerate(expected_sequence):
            result = fibonacci(n)
            assert result == expected_value, (
                f"fibonacci({n}) returned {result}, expected {expected_value}"
            )

    def test_fibonacci_n_twenty_returns_correct_value(self) -> None:
        """Test that fibonacci(20) returns 6765."""
        result = fibonacci(20)
        assert result == 6765

    def test_fibonacci_n_twenty_five_returns_correct_value(self) -> None:
        """Test that fibonacci(25) returns 75025."""
        result = fibonacci(25)
        assert result == 75025

    def test_fibonacci_large_value_n_fifty(self) -> None:
        """Test that fibonacci(50) computes correctly for large values."""
        result = fibonacci(50)
        assert result == 12586269025
        assert isinstance(result, int)

    def test_fibonacci_large_value_n_one_hundred(self) -> None:
        """Test that fibonacci(100) handles very large values without overflow."""
        result = fibonacci(100)
        expected = 354224848179261915075
        assert result == expected
        assert isinstance(result, int)

    def test_fibonacci_return_type_is_always_int(self) -> None:
        """Test that fibonacci always returns int type, never float or other."""
        for n in [0, 1, 5, 10, 20]:
            result = fibonacci(n)
            assert isinstance(result, int)
            assert not isinstance(result, bool)
            assert not isinstance(result, float)


class TestFibonacciErrorHandling:
    """Test suite for error handling and input validation.
    
    Validates that the fibonacci function properly rejects invalid inputs
    and raises appropriate exceptions with descriptive messages.
    
    Component ID: FibonacciValidator
    Semantic Unit: SU-001
    """

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

    def test_fibonacci_negative_one_hundred_raises_value_error(self) -> None:
        """Test that fibonacci(-100) raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            fibonacci(-100)
        assert "non-negative" in str(exc_info.value).lower()

    def test_fibonacci_error_message_contains_non_negative(self) -> None:
        """Test that error message explicitly mentions 'non-negative'."""
        with pytest.raises(ValueError) as exc_info:
            fibonacci(-5)
        error_message = str(exc_info.value)
        assert "non-negative" in error_message.lower()

    def test_fibonacci_error_message_contains_integer(self) -> None:
        """Test that error message mentions 'integer' requirement."""
        with pytest.raises(ValueError) as exc_info:
            fibonacci(-1)
        error_message = str(exc_info.value)
        assert "integer" in error_message.lower()

    def test_fibonacci_float_input_raises_value_error(self) -> None:
        """Test that fibonacci with float input raises ValueError."""
        with pytest.raises(ValueError):
            fibonacci(5.5)  # type: ignore

    def test_fibonacci_string_input_raises_type_error_or_value_error(self) -> None:
        """Test that fibonacci with string input raises appropriate error."""
        with pytest.raises((ValueError, TypeError)):
            fibonacci("5")  # type: ignore

    def test_fibonacci_none_input_raises_type_error_or_value_error(self) -> None:
        """Test that fibonacci with None input raises appropriate error."""
        with pytest.raises((ValueError, TypeError)):
            fibonacci(None)  # type: ignore

    def test_fibonacci_list_input_raises_type_error_or_value_error(self) -> None:
        """Test that fibonacci with list input raises appropriate error."""
        with pytest.raises((ValueError, TypeError)):
            fibonacci([5])  # type: ignore

    def test_fibonacci_boolean_true_raises_value_error(self) -> None:
        """Test that fibonacci(True) raises ValueError (bool excluded from int)."""
        with pytest.raises(ValueError):
            fibonacci(True)  # type: ignore

    def test_fibonacci_boolean_false_raises_value_error(self) -> None:
        """Test that fibonacci(False) raises ValueError (bool excluded from int)."""
        with pytest.raises(ValueError):
            fibonacci(False)  # type: ignore

    def test_fibonacci_no_exception_for_valid_non_negative_integers(self) -> None:
        """Test that no exceptions are raised for valid non-negative integers."""
        valid_inputs = [0, 1, 2, 5, 10, 20, 50, 100]
        for n in valid_inputs: