"""
Fibonacci Validator and Calculator Module

Input validation component that enforces type checking and validates non-negative
integer constraints for Fibonacci function parameters. Implements iterative Fibonacci
calculation with proper handling of edge cases.

Component ID: FibonacciValidator
Semantic Unit ID: SU-001, SU-002, SU-003

Author: ASP Code Agent
"""


class FibonacciValidator:
    """
    Validates input parameters and enforces type hints for the Fibonacci function.

    This class provides input validation to ensure that parameters meet the
    requirements for Fibonacci calculation: must be an integer type and must be
    non-negative.

    Semantic Unit ID: SU-001
    """

    @staticmethod
    def validate_input(n: int) -> bool:
        """
        Validate that input n is a non-negative integer.

        Performs type checking to ensure n is an integer (not float, string, or
        other numeric type) and range checking to ensure n is non-negative.

        Args:
            n: The input value to validate. Must be of type int.

        Returns:
            bool: True if validation passes.

        Raises:
            TypeError: If n is not an integer type.
            ValueError: If n is a negative integer.

        Examples:
            >>> FibonacciValidator.validate_input(0)
            True
            >>> FibonacciValidator.validate_input(5)
            True
            >>> FibonacciValidator.validate_input(-1)
            Traceback (most recent call last):
                ...
            ValueError: n must be a non-negative integer
            >>> FibonacciValidator.validate_input(5.5)
            Traceback (most recent call last):
                ...
            TypeError: n must be an integer, not float
        """
        if not isinstance(n, int) or isinstance(n, bool):
            raise TypeError(f"n must be an integer, not {type(n).__name__}")

        if n < 0:
            raise ValueError("n must be a non-negative integer")

        return True


class FibonacciCalculator:
    """
    Implements iterative Fibonacci calculation with proper handling of edge cases.

    This class provides the core Fibonacci computation using an iterative approach
    to avoid stack overflow and ensure O(1) space complexity.

    Semantic Unit ID: SU-002
    """

    @staticmethod
    def handle_base_cases(n: int) -> int:
        """
        Return Fibonacci value for base cases n=0 and n=1.

        Args:
            n: The input value (must be 0 or 1).

        Returns:
            int: The Fibonacci value for the base case (0 or 1).

        Examples:
            >>> FibonacciCalculator.handle_base_cases(0)
            0
            >>> FibonacciCalculator.handle_base_cases(1)
            1
        """
        if n == 0:
            return 0
        if n == 1:
            return 1

    @staticmethod
    def calculate(n: int) -> int:
        """
        Calculate the nth Fibonacci number using iterative approach.

        Uses an iterative algorithm with two variables (prev, curr) to compute
        the Fibonacci number at position n. This approach has O(n) time complexity
        and O(1) space complexity, avoiding recursion and stack overflow issues.

        Args:
            n: The position in the Fibonacci sequence (must be non-negative).

        Returns:
            int: The nth Fibonacci number.

        Examples:
            >>> FibonacciCalculator.calculate(0)
            0
            >>> FibonacciCalculator.calculate(1)
            1
            >>> FibonacciCalculator.calculate(2)
            1
            >>> FibonacciCalculator.calculate(5)
            5
            >>> FibonacciCalculator.calculate(10)
            55
        """
        if n == 0:
            return 0
        if n == 1:
            return 1

        prev: int = 0
        curr: int = 1

        for _ in range(2, n + 1):
            temp: int = curr
            curr = prev + curr
            prev = temp

        return curr


def fibonacci(n: int) -> int:
    """
    Calculate and return the nth Fibonacci number.

    The Fibonacci sequence is a series of numbers where each number is the sum
    of the two preceding ones, typically starting with 0 and 1. This function
    computes the nth number in this sequence using an efficient iterative approach.

    The function validates input to ensure n is a non-negative integer, then
    calculates the corresponding Fibonacci number. Base cases (n=0 and n=1) are
    handled explicitly for clarity and efficiency.

    Args:
        n: The position in the Fibonacci sequence. Must be a non-negative integer.
           Type must be int (not float or string representation).

    Returns:
        int: The nth Fibonacci number in the sequence.

    Raises:
        TypeError: If n is not an integer type (e.g., float, string, None).
        ValueError: If n is a negative integer.

    Examples:
        >>> fibonacci(0)
        0
        >>> fibonacci(1)
        1
        >>> fibonacci(2)
        1
        >>> fibonacci(5)
        5
        >>> fibonacci(10)
        55

    Semantic Unit ID: SU-003
    """
    FibonacciValidator.validate_input(n)
    return FibonacciCalculator.calculate(n)