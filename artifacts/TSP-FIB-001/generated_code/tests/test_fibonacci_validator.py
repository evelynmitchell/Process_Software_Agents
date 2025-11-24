"""
Unit tests for FibonacciValidator

Tests the FibonacciValidator component covering valid inputs, negative integers,
type validation, and error message verification.

Semantic Unit ID: SU-001
Component ID: FibonacciValidator

Author: ASP Code Agent
"""

import pytest
from src.fibonacci_validator import FibonacciValidator, FibonacciCalculator, fibonacci


class TestFibonacciValidator:
    """Test suite for FibonacciValidator component."""

    def test_validate_input_accepts_zero(self) -> None:
        """Test that validate_input accepts 0 as valid non-negative integer."""
        validator = FibonacciValidator()
        assert validator.validate_input(0) is True

    def test_validate_input_accepts_one(self) -> None:
        """Test that validate_input accepts 1 as valid non-negative integer."""
        validator = FibonacciValidator()
        assert validator.validate_input(1) is True

    def test_validate_input_accepts_positive_integers(self) -> None:
        """Test that validate_input accepts positive integers."""
        validator = FibonacciValidator()
        assert validator.validate_input(5) is True
        assert validator.validate_input(10) is True
        assert validator.validate_input(100) is True
        assert validator.validate_input(1000) is True

    def test_validate_input_rejects_negative_one(self) -> None:
        """Test that validate_input raises ValueError for -1."""
        validator = FibonacciValidator()
        with pytest.raises(ValueError) as exc_info:
            validator.validate_input(-1)
        assert "non-negative" in str(exc_info.value).lower()

    def test_validate_input_rejects_negative_integers(self) -> None:
        """Test that validate_input raises ValueError for negative integers."""
        validator = FibonacciValidator()
        negative_values = [-1, -5, -10, -100, -999]
        for value in negative_values:
            with pytest.raises(ValueError) as exc_info:
                validator.validate_input(value)
            assert "non-negative" in str(exc_info.value).lower()

    def test_validate_input_error_message_content(self) -> None:
        """Test that ValueError message contains descriptive text."""
        validator = FibonacciValidator()
        with pytest.raises(ValueError) as exc_info:
            validator.validate_input(-5)
        error_message = str(exc_info.value)
        assert "n" in error_message.lower()
        assert "non-negative" in error_message.lower()
        assert "integer" in error_message.lower()

    def test_validate_input_rejects_float_type(self) -> None:
        """Test that validate_input rejects float type even if non-negative."""
        validator = FibonacciValidator()
        with pytest.raises(TypeError):
            validator.validate_input(5.0)

    def test_validate_input_rejects_string_type(self) -> None:
        """Test that validate_input rejects string type."""
        validator = FibonacciValidator()
        with pytest.raises(TypeError):
            validator.validate_input("5")

    def test_validate_input_rejects_none_type(self) -> None:
        """Test that validate_input rejects None type."""
        validator = FibonacciValidator()
        with pytest.raises(TypeError):
            validator.validate_input(None)

    def test_validate_input_rejects_list_type(self) -> None:
        """Test that validate_input rejects list type."""
        validator = FibonacciValidator()
        with pytest.raises(TypeError):
            validator.validate_input([5])

    def test_validate_input_rejects_dict_type(self) -> None:
        """Test that validate_input rejects dict type."""
        validator = FibonacciValidator()
        with pytest.raises(TypeError):
            validator.validate_input({"n": 5})


class TestFibonacciCalculator:
    """Test suite for FibonacciCalculator component."""

    def test_calculate_base_case_zero(self) -> None:
        """Test that calculate returns 0 for n=0."""
        calculator = FibonacciCalculator()
        assert calculator.calculate(0) == 0

    def test_calculate_base_case_one(self) -> None:
        """Test that calculate returns 1 for n=1."""
        calculator = FibonacciCalculator()
        assert calculator.calculate(1) == 1

    def test_calculate_fibonacci_two(self) -> None:
        """Test that calculate returns 1 for n=2."""
        calculator = FibonacciCalculator()
        assert calculator.calculate(2) == 1

    def test_calculate_fibonacci_three(self) -> None:
        """Test that calculate returns 2 for n=3."""
        calculator = FibonacciCalculator()
        assert calculator.calculate(3) == 2

    def test_calculate_fibonacci_five(self) -> None:
        """Test that calculate returns 5 for n=5."""
        calculator = FibonacciCalculator()
        assert calculator.calculate(5) == 5

    def test_calculate_fibonacci_ten(self) -> None:
        """Test that calculate returns 55 for n=10."""
        calculator = FibonacciCalculator()
        assert calculator.calculate(10) == 55

    def test_calculate_fibonacci_sequence_correctness(self) -> None:
        """Test that calculate returns correct Fibonacci sequence values."""
        calculator = FibonacciCalculator()
        expected_sequence = [0, 1, 1, 2, 3, 5, 8, 13, 21, 34, 55]
        for n, expected in enumerate(expected_sequence):
            assert calculator.calculate(n) == expected

    def test_calculate_fibonacci_fifteen(self) -> None:
        """Test that calculate returns 610 for n=15."""
        calculator = FibonacciCalculator()
        assert calculator.calculate(15) == 610

    def test_calculate_fibonacci_twenty(self) -> None:
        """Test that calculate returns 6765 for n=20."""
        calculator = FibonacciCalculator()
        assert calculator.calculate(20) == 6765

    def test_calculate_large_fibonacci_number(self) -> None:
        """Test that calculate handles large Fibonacci numbers correctly."""
        calculator = FibonacciCalculator()
        result = calculator.calculate(50)
        assert result == 12586269025

    def test_handle_base_cases_zero(self) -> None:
        """Test that handle_base_cases returns 0 for n=0."""
        calculator = FibonacciCalculator()
        assert calculator.handle_base_cases(0) == 0

    def test_handle_base_cases_one(self) -> None:
        """Test that handle_base_cases returns 1 for n=1."""
        calculator = FibonacciCalculator()
        assert calculator.handle_base_cases(1) == 1

    def test_handle_base_cases_returns_none_for_n_greater_than_one(self) -> None:
        """Test that handle_base_cases returns None for n >= 2."""
        calculator = FibonacciCalculator()
        assert calculator.handle_base_cases(2) is None
        assert calculator.handle_base_cases(5) is None
        assert calculator.handle_base_cases(10) is None

    def test_calculate_uses_iterative_approach(self) -> None:
        """Test that calculate uses iterative approach (no recursion depth issues)."""
        calculator = FibonacciCalculator()
        # If recursive approach was used, this would hit recursion limit
        # Iterative approach handles this easily
        result = calculator.calculate(100)
        assert isinstance(result, int)
        assert result > 0


class TestFibonacciFunction:
    """Test suite for fibonacci function integration."""

    def test_fibonacci_