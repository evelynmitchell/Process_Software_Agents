"""
Comprehensive unit tests for the sum_numbers function.

Tests cover basic arithmetic operations, edge cases (None values, type mismatches,
boolean rejection), overflow scenarios with large integers, and validation of correct
results across positive, negative, and zero values.

Semantic Unit IDs: SU-001, SU-002, SU-003, SU-004
Component IDs: SumNumbersFunction, SumNumbersAdditionLogic, SumNumbersDocumentation,
SumNumbersEdgeCaseHandler

Author: ASP Code Agent
"""

import pytest
from src.sum_numbers import sum_numbers


class TestSumNumbersBasicArithmetic:
    """Test basic arithmetic operations of sum_numbers function."""

    def test_sum_two_positive_integers(self) -> None:
        """Test sum_numbers with two positive integers returns correct result."""
        result = sum_numbers(2, 3)
        assert result == 5
        assert isinstance(result, int)

    def test_sum_positive_and_negative_integers(self) -> None:
        """Test sum_numbers with positive and negative integers."""
        result = sum_numbers(5, -3)
        assert result == 2
        assert isinstance(result, int)

    def test_sum_two_negative_integers(self) -> None:
        """Test sum_numbers with two negative integers returns correct result."""
        result = sum_numbers(-2, -3)
        assert result == -5
        assert isinstance(result, int)

    def test_sum_with_zero_first_parameter(self) -> None:
        """Test sum_numbers with zero as first parameter."""
        result = sum_numbers(0, 5)
        assert result == 5
        assert isinstance(result, int)

    def test_sum_with_zero_second_parameter(self) -> None:
        """Test sum_numbers with zero as second parameter."""
        result = sum_numbers(5, 0)
        assert result == 5
        assert isinstance(result, int)

    def test_sum_two_zeros(self) -> None:
        """Test sum_numbers with both parameters as zero."""
        result = sum_numbers(0, 0)
        assert result == 0
        assert isinstance(result, int)

    def test_sum_negative_and_positive_integers(self) -> None:
        """Test sum_numbers with negative first and positive second parameter."""
        result = sum_numbers(-10, 7)
        assert result == -3
        assert isinstance(result, int)

    def test_sum_large_positive_integers(self) -> None:
        """Test sum_numbers with large positive integers."""
        result = sum_numbers(1000000, 2000000)
        assert result == 3000000
        assert isinstance(result, int)

    def test_sum_large_negative_integers(self) -> None:
        """Test sum_numbers with large negative integers."""
        result = sum_numbers(-1000000, -2000000)
        assert result == -3000000
        assert isinstance(result, int)

    def test_sum_commutative_property(self) -> None:
        """Test that sum_numbers satisfies commutative property (a + b = b + a)."""
        result1 = sum_numbers(7, 3)
        result2 = sum_numbers(3, 7)
        assert result1 == result2
        assert result1 == 10

    def test_sum_associative_with_zero(self) -> None:
        """Test that adding zero returns the original number (identity property)."""
        result = sum_numbers(42, 0)
        assert result == 42


class TestSumNumbersNoneHandling:
    """Test None value handling in sum_numbers function."""

    def test_sum_with_none_first_parameter(self) -> None:
        """Test sum_numbers raises TypeError when first parameter is None."""
        with pytest.raises(TypeError) as exc_info:
            sum_numbers(None, 5)  # type: ignore
        assert "Parameter a cannot be None" in str(exc_info.value)

    def test_sum_with_none_second_parameter(self) -> None:
        """Test sum_numbers raises TypeError when second parameter is None."""
        with pytest.raises(TypeError) as exc_info:
            sum_numbers(5, None)  # type: ignore
        assert "Parameter b cannot be None" in str(exc_info.value)

    def test_sum_with_both_parameters_none(self) -> None:
        """Test sum_numbers raises TypeError when both parameters are None."""
        with pytest.raises(TypeError) as exc_info:
            sum_numbers(None, None)  # type: ignore
        assert "Parameter a cannot be None" in str(exc_info.value)


class TestSumNumbersTypeValidation:
    """Test type validation and type mismatch handling in sum_numbers function."""

    def test_sum_with_string_first_parameter(self) -> None:
        """Test sum_numbers raises TypeError when first parameter is string."""
        with pytest.raises(TypeError) as exc_info:
            sum_numbers("5", 3)  # type: ignore
        assert "Parameter a must be an integer" in str(exc_info.value)
        assert "str" in str(exc_info.value)

    def test_sum_with_string_second_parameter(self) -> None:
        """Test sum_numbers raises TypeError when second parameter is string."""
        with pytest.raises(TypeError) as exc_info:
            sum_numbers(5, "3")  # type: ignore
        assert "Parameter b must be an integer" in str(exc_info.value)
        assert "str" in str(exc_info.value)

    def test_sum_with_float_first_parameter(self) -> None:
        """Test sum_numbers raises TypeError when first parameter is float."""
        with pytest.raises(TypeError) as exc_info:
            sum_numbers(5.5, 3)  # type: ignore
        assert "Parameter a must be an integer" in str(exc_info.value)
        assert "float" in str(exc_info.value)

    def test_sum_with_float_second_parameter(self) -> None:
        """Test sum_numbers raises TypeError when second parameter is float."""
        with pytest.raises(TypeError) as exc_info:
            sum_numbers(5, 3.5)  # type: ignore
        assert "Parameter b must be an integer" in str(exc_info.value)
        assert "float" in str(exc_info.value)

    def test_sum_with_list_first_parameter(self) -> None:
        """Test sum_numbers raises TypeError when first parameter is list."""
        with pytest.raises(TypeError) as exc_info:
            sum_numbers([5], 3)  # type: ignore
        assert "Parameter a must be an integer" in str(exc_info.value)
        assert "list" in str(exc_info.value)

    def test_sum_with_list_second_parameter(self) -> None:
        """Test sum_numbers raises TypeError when second parameter is list."""
        with pytest.raises(TypeError) as exc_info:
            sum_numbers(5, [3])  # type: ignore
        assert "Parameter b must be an integer" in str(exc_info.value)
        assert "list" in str(exc_info.value)

    def test_sum_with_dict_first_parameter(self) -> None:
        """Test sum_numbers raises TypeError when first parameter is dict."""
        with pytest.raises(TypeError) as exc_info:
            sum_numbers({"value": 5}, 3)  # type: ignore
        assert "Parameter a must be an integer" in str(exc_info.value)
        assert "dict" in str(exc_info.value)

    def test_sum_with_dict_second_parameter(self) -> None:
        """Test sum_numbers raises TypeError when second parameter is dict."""
        with pytest.raises(TypeError) as exc_info:
            sum_numbers(5, {"value": 3})  # type: ignore
        assert "Parameter b must be an integer" in str(exc_info.value)
        assert "dict" in str(exc_info.value)

    def test_sum_with_