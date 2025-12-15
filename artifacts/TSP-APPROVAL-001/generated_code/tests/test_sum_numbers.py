import pytest
from src.sum_numbers import sum_numbers


class TestSumNumbersPositiveIntegers:
    """Test sum_numbers function with positive integer inputs."""

    def test_sum_two_positive_integers(self) -> None:
        """Test that sum_numbers correctly adds two positive integers."""
        result = sum_numbers(5, 3)
        assert result == 8

    def test_sum_positive_integers_large_values(self) -> None:
        """Test sum_numbers with large positive integer values."""
        result = sum_numbers(1000000, 2000000)
        assert result == 3000000

    def test_sum_positive_integers_one_and_one(self) -> None:
        """Test sum_numbers with smallest positive integers."""
        result = sum_numbers(1, 1)
        assert result == 2

    def test_sum_positive_integers_commutative(self) -> None:
        """Test that sum_numbers is commutative (a + b = b + a)."""
        result1 = sum_numbers(7, 4)
        result2 = sum_numbers(4, 7)
        assert result1 == result2 == 11


class TestSumNumbersNegativeIntegers:
    """Test sum_numbers function with negative integer inputs."""

    def test_sum_two_negative_integers(self) -> None:
        """Test that sum_numbers correctly adds two negative integers."""
        result = sum_numbers(-5, -3)
        assert result == -8

    def test_sum_negative_integers_large_values(self) -> None:
        """Test sum_numbers with large negative integer values."""
        result = sum_numbers(-1000000, -2000000)
        assert result == -3000000

    def test_sum_negative_integers_minus_one_and_minus_one(self) -> None:
        """Test sum_numbers with smallest negative integers."""
        result = sum_numbers(-1, -1)
        assert result == -2


class TestSumNumbersMixedSigns:
    """Test sum_numbers function with mixed positive and negative integers."""

    def test_sum_positive_and_negative_positive_result(self) -> None:
        """Test sum_numbers with positive and negative integers resulting in positive."""
        result = sum_numbers(10, -3)
        assert result == 7

    def test_sum_positive_and_negative_negative_result(self) -> None:
        """Test sum_numbers with positive and negative integers resulting in negative."""
        result = sum_numbers(3, -10)
        assert result == -7

    def test_sum_positive_and_negative_equal_magnitude(self) -> None:
        """Test sum_numbers with equal magnitude positive and negative integers."""
        result = sum_numbers(5, -5)
        assert result == 0

    def test_sum_negative_and_positive_positive_result(self) -> None:
        """Test sum_numbers with negative and positive integers resulting in positive."""
        result = sum_numbers(-3, 10)
        assert result == 7

    def test_sum_negative_and_positive_negative_result(self) -> None:
        """Test sum_numbers with negative and positive integers resulting in negative."""
        result = sum_numbers(-10, 3)
        assert result == -7


class TestSumNumbersZeroValues:
    """Test sum_numbers function with zero values."""

    def test_sum_zero_and_positive_integer(self) -> None:
        """Test sum_numbers with zero and positive integer."""
        result = sum_numbers(0, 5)
        assert result == 5

    def test_sum_positive_integer_and_zero(self) -> None:
        """Test sum_numbers with positive integer and zero."""
        result = sum_numbers(5, 0)
        assert result == 5

    def test_sum_zero_and_negative_integer(self) -> None:
        """Test sum_numbers with zero and negative integer."""
        result = sum_numbers(0, -5)
        assert result == -5

    def test_sum_negative_integer_and_zero(self) -> None:
        """Test sum_numbers with negative integer and zero."""
        result = sum_numbers(-5, 0)
        assert result == -5

    def test_sum_zero_and_zero(self) -> None:
        """Test sum_numbers with zero and zero."""
        result = sum_numbers(0, 0)
        assert result == 0


class TestSumNumbersLargeIntegers:
    """Test sum_numbers function with very large integer values."""

    def test_sum_very_large_positive_integers(self) -> None:
        """Test sum_numbers with very large positive integers."""
        large_num1 = 10**18
        large_num2 = 10**18
        result = sum_numbers(large_num1, large_num2)
        assert result == 2 * (10**18)

    def test_sum_very_large_negative_integers(self) -> None:
        """Test sum_numbers with very large negative integers."""
        large_num1 = -(10**18)
        large_num2 = -(10**18)
        result = sum_numbers(large_num1, large_num2)
        assert result == -2 * (10**18)

    def test_sum_extremely_large_integers_arbitrary_precision(self) -> None:
        """Test sum_numbers with extremely large integers beyond typical integer limits."""
        huge_num1 = 10**100
        huge_num2 = 10**100
        result = sum_numbers(huge_num1, huge_num2)
        assert result == 2 * (10**100)


class TestSumNumbersNoneHandling:
    """Test sum_numbers function with None value handling."""

    def test_sum_none_and_integer_raises_type_error(self) -> None:
        """Test that sum_numbers raises TypeError when first argument is None."""
        with pytest.raises(TypeError) as exc_info:
            sum_numbers(None, 5)  # type: ignore
        assert str(exc_info.value) == "Arguments cannot be None"

    def test_sum_integer_and_none_raises_type_error(self) -> None:
        """Test that sum_numbers raises TypeError when second argument is None."""
        with pytest.raises(TypeError) as exc_info:
            sum_numbers(5, None)  # type: ignore
        assert str(exc_info.value) == "Arguments cannot be None"

    def test_sum_none_and_none_raises_type_error(self) -> None:
        """Test that sum_numbers raises TypeError when both arguments are None."""
        with pytest.raises(TypeError) as exc_info:
            sum_numbers(None, None)  # type: ignore
        assert str(exc_info.value) == "Arguments cannot be None"


class TestSumNumbersTypeMismatchErrors:
    """Test sum_numbers function with type mismatch error handling."""

    def test_sum_string_and_integer_raises_type_error(self) -> None:
        """Test that sum_numbers raises TypeError when first argument is string."""
        with pytest.raises(TypeError) as exc_info:
            sum_numbers("5", 3)  # type: ignore
        assert str(exc_info.value) == "Both arguments must be integers"

    def test_sum_integer_and_string_raises_type_error(self) -> None:
        """Test that sum_numbers raises TypeError when second argument is string."""
        with pytest.raises(TypeError) as exc_info:
            sum_numbers(5, "3")  # type: ignore
        assert str(exc_info.value) == "Both arguments must be integers"

    def test_sum_float_and_integer_raises_type_error(self) -> None:
        """Test that sum_numbers raises TypeError when first argument is float."""
        with pytest.raises(TypeError) as exc_info:
            sum_numbers(5.5, 3)  # type: ignore
        assert str(exc_info.value) == "Both arguments must be integers"

    def test_sum_integer_and_float_raises_type_error(self) -> None: