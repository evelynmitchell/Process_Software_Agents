"""
Fibonacci Validator and Calculator Module

This module provides input validation and computation for Fibonacci numbers.
It implements a three-component architecture with FibonacciValidator for input
validation, FibonacciCalculator for iterative computation, and fibonacci() as
the public interface.

Component ID: FibonacciValidator, FibonacciCalculator, FibonacciFunction
Semantic Unit IDs: SU-001, SU-002, SU-003

Author: ASP Code Agent
"""


class FibonacciValidator:
    """
    Input validation component for Fibonacci function.

    Validates that input parameters are non-negative integers and raises
    ValueError for invalid inputs. Enforces type constraints at runtime.

    Semantic Unit ID: SU-001
    Component ID: FibonacciValidator
    """

    @staticmethod
    def validate_input(n: int) -> bool:
        """
        Validate that input n is a non-negative integer.

        Checks that n is of type int (not float or other numeric types) and
        that n is non-negative (n >= 0). Raises ValueError if validation fails.

        Args:
            n: The input value to validate. Must be an integer.

        Returns:
            bool: True if validation passes.

        Raises:
            TypeError: If n is not an integer type.
            ValueError: If n is negative (n < 0).

        Examples:
            >>> FibonacciValidator.validate_input(5)
            True
            >>> FibonacciValidator.validate_input(0)
            True
            >>> FibonacciValidator.validate_input(-1)
            Traceback (most recent call last):
                ...
            ValueError: n must be a non-negative integer
        """
        if not isinstance(n, int) or isinstance(n, bool):
            raise TypeError(f"n must be an integer, got {type(n).__name__}")

        if n < 0:
            raise ValueError("n must be a non-negative integer")

        return True


class FibonacciCalculator:
    """
    Fibonacci computation component using iterative algorithm.

    Computes the nth Fibonacci number using an iterative approach with O(n)
    time complexity and O(1) space complexity. Handles edge cases for n=0
    and n=1.

    Semantic Unit ID: SU-002
    Component ID: FibonacciCalculator
    """

    @staticmethod
    def handle_base_cases(n: int) -> int | None:
        """
        Handle base cases for Fibonacci computation.

        Returns the Fibonacci value for base cases (n=0 returns 0, n=1 returns 1).
        Returns None for n >= 2 to indicate iteration is needed.

        Args:
            n: Non-negative integer input (assumed to be validated).

        Returns:
            int: Fibonacci value for base cases (0 or 1).
            None: If n >= 2, indicating iteration is required.

        Examples:
            >>> FibonacciCalculator.handle_base_cases(0)
            0
            >>> FibonacciCalculator.handle_base_cases(1)
            1
            >>> FibonacciCalculator.handle_base_cases(2) is None
            True
        """
        if n == 0:
            return 0
        if n == 1:
            return 1
        return None

    @staticmethod
    def calculate(n: int) -> int:
        """
        Calculate the nth Fibonacci number using iterative algorithm.

        Implements an iterative approach that avoids recursion overhead and
        stack overflow risks. Uses constant space with only two variables
        tracking the previous two Fibonacci numbers.

        Algorithm:
            1. Handle base cases (n=0 returns 0, n=1 returns 1)
            2. Initialize a=0, b=1
            3. Loop n times, updating: a, b = b, a+b
            4. Return final value of a

        Args:
            n: Non-negative integer (assumed to be validated).

        Returns:
            int: The nth Fibonacci number.

        Time Complexity: O(n)
        Space Complexity: O(1)

        Examples:
            >>> FibonacciCalculator.calculate(0)
            0
            >>> FibonacciCalculator.calculate(1)
            1
            >>> FibonacciCalculator.calculate(5)
            5
            >>> FibonacciCalculator.calculate(10)
            55
        """
        base_case_result = FibonacciCalculator.handle_base_cases(n)
        if base_case_result is not None:
            return base_case_result

        a: int = 0
        b: int = 1

        for _ in range(n):
            a, b = b, a + b

        return a


def fibonacci(n: int) -> int:
    """
    Calculate the nth Fibonacci number.

    Computes the nth number in the Fibonacci sequence, where each number is
    the sum of the two preceding ones. The sequence starts with F(0)=0 and
    F(1)=1. Uses an iterative algorithm for O(n) time complexity and O(1)
    space complexity.

    The Fibonacci sequence is defined as:
        F(0) = 0
        F(1) = 1
        F(n) = F(n-1) + F(n-2) for n >= 2

    Args:
        n: Non-negative integer representing the position in the Fibonacci
           sequence. Must be >= 0.

    Returns:
        int: The nth Fibonacci number.

    Raises:
        TypeError: If n is not an integer type (e.g., float, string).
        ValueError: If n is negative (n < 0).

    Examples:
        >>> fibonacci(0)
        0
        >>> fibonacci(1)
        1
        >>> fibonacci(5)
        5
        >>> fibonacci(10)
        55

    Notes:
        - Python 3 supports arbitrary precision integers, so this function
          can handle large values of n without overflow.
        - The iterative approach is used instead of recursion to avoid
          stack overflow and improve performance.
        - Time complexity: O(n)
        - Space complexity: O(1)
    """
    FibonacciValidator.validate_input(n)
    return FibonacciCalculator.calculate(n)