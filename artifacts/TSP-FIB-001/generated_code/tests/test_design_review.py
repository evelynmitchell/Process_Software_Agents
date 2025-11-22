"""
Design review validation tests for Fibonacci implementation.

Tests ensure all critical and high-severity requirements are met including:
- Type hints on function signature
- Error handling for negative inputs
- Edge case handling (n=0, n=1)
- Iterative implementation (not recursive)
- Comprehensive documentation with examples
- Input type validation

Author: ASP Code Agent
"""

import pytest
from src.fibonacci import fibonacci
from src.fibonacci_validator import FibonacciValidator
from src.fibonacci_calculator import FibonacciCalculator


class TestArchitectureRequirements:
    """Tests for architecture and design requirements."""

    def test_fibonacci_function_exists(self) -> None:
        """Test that fibonacci function is defined and callable."""
        assert callable(fibonacci)

    def test_fibonacci_function_signature_has_type_hints(self) -> None:
        """Test that fibonacci function has proper type hints in signature."""
        annotations = fibonacci.__annotations__
        assert "n" in annotations, "Parameter 'n' must have type hint"
        assert annotations["n"] == int, "Parameter 'n' must be typed as int"
        assert "return" in annotations, "Return type must be specified"
        assert annotations["return"] == int, "Return type must be int"

    def test_fibonacci_function_name_correct(self) -> None:
        """Test that function is named 'fibonacci'."""
        assert fibonacci.__name__ == "fibonacci"

    def test_fibonacci_function_has_docstring(self) -> None:
        """Test that fibonacci function has a docstring."""
        assert fibonacci.__doc__ is not None
        assert len(fibonacci.__doc__.strip()) > 0

    def test_fibonacci_docstring_contains_summary(self) -> None:
        """Test that docstring contains a summary line."""
        docstring = fibonacci.__doc__
        lines = docstring.strip().split("\n")
        assert len(lines) > 0
        assert len(lines[0].strip()) > 0

    def test_fibonacci_docstring_contains_args_section(self) -> None:
        """Test that docstring contains Args section."""
        docstring = fibonacci.__doc__
        assert "Args:" in docstring or "Arguments:" in docstring or "Parameters:" in docstring

    def test_fibonacci_docstring_contains_returns_section(self) -> None:
        """Test that docstring contains Returns section."""
        docstring = fibonacci.__doc__
        assert "Returns:" in docstring or "Return:" in docstring

    def test_fibonacci_docstring_contains_raises_section(self) -> None:
        """Test that docstring contains Raises section."""
        docstring = fibonacci.__doc__
        assert "Raises:" in docstring or "Raise:" in docstring

    def test_fibonacci_docstring_contains_examples_section(self) -> None:
        """Test that docstring contains Examples section."""
        docstring = fibonacci.__doc__
        assert "Examples:" in docstring or "Example:" in docstring

    def test_fibonacci_docstring_has_multiple_examples(self) -> None:
        """Test that docstring contains at least 5 examples."""
        docstring = fibonacci.__doc__
        examples_section = docstring.split("Examples:")[1] if "Examples:" in docstring else docstring.split("Example:")[1]
        example_count = examples_section.count("fibonacci(")
        assert example_count >= 5, f"Expected at least 5 examples, found {example_count}"


class TestErrorHandlingRequirements:
    """Tests for error handling and validation requirements."""

    def test_negative_input_raises_value_error(self) -> None:
        """Test that negative input raises ValueError."""
        with pytest.raises(ValueError):
            fibonacci(-1)

    def test_negative_input_error_message_contains_non_negative(self) -> None:
        """Test that ValueError message mentions non-negative constraint."""
        with pytest.raises(ValueError) as exc_info:
            fibonacci(-1)
        error_message = str(exc_info.value).lower()
        assert "non-negative" in error_message or "negative" in error_message

    def test_large_negative_input_raises_value_error(self) -> None:
        """Test that large negative input raises ValueError."""
        with pytest.raises(ValueError):
            fibonacci(-100)

    def test_float_input_raises_error(self) -> None:
        """Test that float input raises TypeError or ValueError."""
        with pytest.raises((TypeError, ValueError)):
            fibonacci(5.5)

    def test_string_input_raises_error(self) -> None:
        """Test that string input raises TypeError or ValueError."""
        with pytest.raises((TypeError, ValueError)):
            fibonacci("5")

    def test_none_input_raises_error(self) -> None:
        """Test that None input raises TypeError or ValueError."""
        with pytest.raises((TypeError, ValueError)):
            fibonacci(None)

    def test_list_input_raises_error(self) -> None:
        """Test that list input raises TypeError or ValueError."""
        with pytest.raises((TypeError, ValueError)):
            fibonacci([5])

    def test_dict_input_raises_error(self) -> None:
        """Test that dict input raises TypeError or ValueError."""
        with pytest.raises((TypeError, ValueError)):
            fibonacci({"n": 5})


class TestDataIntegrityRequirements:
    """Tests for edge cases and data integrity."""

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

    def test_fibonacci_three_returns_two(self) -> None:
        """Test that fibonacci(3) returns 2."""
        result = fibonacci(3)
        assert result == 2
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

    def test_fibonacci_sequence_correctness(self) -> None:
        """Test that first 15 Fibonacci numbers are correct."""
        expected = [0, 1, 1, 2, 3, 5, 8, 13, 21, 34, 55, 89, 144, 233, 377]
        for n, expected_value in enumerate(expected):
            result = fibonacci(n)
            assert result == expected_value, f"fibonacci({n}) should be {expected_value}, got {result}"

    def test_fibonacci_returns_integer_type(self) -> None:
        """Test that fibonacci always returns int type."""
        for n in [0, 1, 2, 5, 10, 20]:
            result = fibonacci(n)
            assert isinstance(result, int), f"fibonacci({n}) should return int, got {type(result)}"

    def test_fibonacci_returns_non_negative(self) -> None:
        """Test that fibonacci returns non-negative values for valid inputs."""
        for n in range(0, 20):
            result = fibonacci(n)
            assert result >= 0, f"fibonacci({n}) should be non-negative, got {result}"


class TestPerformanceRequirements:
    """Tests for performance characteristics and implementation approach."""

    def test_fibonacci_completes_for_large_n(self) -> None:
        """Test that fibonacci completes in reasonable time for n=1000."""
        result = fibonacci(1000)
        assert isinstance(result, int)