"""
Fibonacci Module

This module provides functionality to calculate Fibonacci numbers using an iterative approach.
It includes input validation, calculation logic, and a public API function with comprehensive
documentation and examples.

Component IDs: FibonacciValidator, FibonacciCalculator, FibonacciFunction
Semantic Units: SU-001, SU-002, SU-003
Task ID: TSP-FIB-001

Author: ASP Code Agent
"""


class FibonacciValidator:
    """
    Validator for Fibonacci function input parameters.

    This class handles input validation and type checking for the Fibonacci
    calculation function. It ensures that inputs are valid non-negative integers
    before any calculation is performed.

    Component ID: FibonacciValidator
    Semantic Unit ID: SU-001
    """

    @staticmethod
    def validate_input(n: int) -> bool:
        """
        Validate that input n is a non-negative integer.

        This method performs type checking and range validation on the input
        parameter. It raises ValueError if the input is invalid.

        Args:
            n: The input value to validate. Must be an integer type.

        Returns:
            bool: True if input is valid (non-negative integer).

        Raises:
            TypeError: If n is not an integer type (e.g., float, string).
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
            >>> FibonacciValidator.validate_input(3.5)
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
    Calculator for Fibonacci numbers using iterative approach.

    This class implements the core Fibonacci calculation logic using an iterative
    algorithm. It provides O(n) time complexity and O(1) space complexity by
    avoiding recursion and using only two variables to track state.

    Component ID: FibonacciCalculator
    Semantic Unit ID: SU-002
    """

    @staticmethod
    def handle_base_cases(n: int) -> int | None:
        """
        Handle base cases for Fibonacci calculation.

        Returns the Fibonacci value for base cases (n=0 or n=1) without
        requiring iteration. Returns None for other cases to indicate that
        the general calculation algorithm should be used.

        Args:
            n: The input value. Must be a non-negative integer.

        Returns:
            int | None: The Fibonacci value for base cases (0 or 1),
                       or None if n requires iterative calculation.

        Examples:
            >>> FibonacciCalculator.handle_base_cases(0)
            0
            >>> FibonacciCalculator.handle_base_cases(1)
            1
            >>> FibonacciCalculator.handle_base_cases(2) is None
            True
            >>> FibonacciCalculator.handle_base_cases(5) is None
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
        Calculate the nth Fibonacci number using iterative approach.

        This method implements the Fibonacci calculation using an iterative
        algorithm with two variables (prev, curr) to track state. This approach
        avoids recursion overhead and stack overflow issues for large values of n.

        The algorithm:
        1. Handle base cases (n=0 returns 0, n=1 returns 1)
        2. Initialize prev=0, curr=1
        3. Iterate n-1 times, updating: temp=curr, curr=prev+curr, prev=temp
        4. Return curr

        Time Complexity: O(n)
        Space Complexity: O(1)

        Args:
            n: The position in the Fibonacci sequence. Must be non-negative.

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
        base_case_result = FibonacciCalculator.handle_base_cases(n)
        if base_case_result is not None:
            return base_case_result

        prev: int = 0
        curr: int = 1

        for _ in range(n - 1):
            temp: int = curr
            curr = prev + curr
            prev = temp

        return curr


def fibonacci(n: int) -> int:
    """
    Calculate the nth Fibonacci number using an iterative approach.

    The Fibonacci sequence is a series of numbers where each number is the sum
    of the two preceding ones, typically starting with 0 and 1. This function
    computes the nth number in this sequence efficiently using an iterative
    algorithm that avoids recursion overhead.

    The function validates input before calculation, ensuring that n is a
    non-negative integer. It then uses an iterative approach with O(n) time
    complexity and O(1) space complexity to compute the result.

    Args:
        n: The position in the Fibonacci sequence (0-indexed).
           Must be a non-negative integer.
           - n=0 returns 0 (first Fibonacci number)
           - n=1 returns 1 (second Fibonacci number)
           - n>=2 returns the sum of the two preceding numbers

    Returns:
        int: The nth Fibonacci number.

    Raises:
        TypeError: If n is not an integer type (e.g., float, string, bool).
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

    Note:
        This function uses an iterative approach rather than recursion,
        making it suitable for large values of n without risk of stack overflow.
        The Fibonacci sequence grows exponentially, so very large values of n
        may result in very large integers.
    """
    FibonacciValidator.validate_input(n)
    result: int = FibonacciCalculator.calculate(n)
    return result
</content>