"""
Fibonacci Calculator Module

Core Fibonacci calculation engine implementing iterative algorithm with explicit base case
handling and O(n) time complexity. This module provides a pure Python implementation of the
Fibonacci sequence calculation without external dependencies.

Component ID: FibonacciCalculator
Semantic Unit: SU-002, SU-001, SU-003
Task ID: TSP-FIB-001

Author: ASP Code Agent
"""


class FibonacciValidator:
    """
    Validates input parameters for Fibonacci calculation.

    This class is responsible for validating that input parameters meet the requirements
    for Fibonacci calculation, including type checking and range validation.

    Semantic Unit: SU-001
    """

    @staticmethod
    def validate_input(n: int) -> bool:
        """
        Validate that input n is a non-negative integer.

        Performs type checking to ensure n is an integer (not float, string, or other type)
        and range checking to ensure n is non-negative. Raises ValueError immediately on
        invalid input to fail fast before any calculation occurs.

        Args:
            n: The input value to validate. Must be an integer type.

        Returns:
            bool: True if input is valid (non-negative integer).

        Raises:
            TypeError: If n is not an integer type (e.g., float, string, None).
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
        # Type check: ensure n is an integer, not float or other type
        if not isinstance(n, int) or isinstance(n, bool):
            raise TypeError(f"n must be an integer, not {type(n).__name__}")

        # Range check: ensure n is non-negative
        if n < 0:
            raise ValueError("n must be a non-negative integer")

        return True


class FibonacciCalculator:
    """
    Implements iterative Fibonacci calculation with proper edge case handling.

    This class provides the core computational logic for calculating Fibonacci numbers
    using an iterative approach with O(n) time complexity and O(1) space complexity.
    The iterative approach avoids stack overflow issues that would occur with recursion
    on large values of n.

    Semantic Unit: SU-002
    """

    @staticmethod
    def handle_base_cases(n: int) -> int:
        """
        Return Fibonacci value for base cases n=0 and n=1.

        Handles the explicit base cases of the Fibonacci sequence where:
        - F(0) = 0
        - F(1) = 1

        Args:
            n: The input value. Must be 0 or 1 for this method to apply.

        Returns:
            int: The Fibonacci value for n (0 or 1).

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

        Implements an efficient iterative algorithm that computes the nth Fibonacci number
        in O(n) time with O(1) space complexity. The algorithm uses two variables (prev, curr)
        to track consecutive Fibonacci values and iteratively computes the sequence up to n.

        For n >= 2, the algorithm:
        1. Initializes prev=0 (F(0)) and curr=1 (F(1))
        2. Iterates from 2 to n (inclusive)
        3. In each iteration: temp=curr, curr=prev+curr, prev=temp
        4. Returns curr after loop completes

        Args:
            n: The position in the Fibonacci sequence to calculate. Must be non-negative.

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
        # Handle base cases explicitly
        if n == 0:
            return 0
        if n == 1:
            return 1

        # Iterative approach for n >= 2
        # Initialize with F(0)=0 and F(1)=1
        prev = 0
        curr = 1

        # Iterate from 2 to n (inclusive)
        for _ in range(2, n + 1):
            # Compute next Fibonacci number: F(i) = F(i-1) + F(i-2)
            temp = curr
            curr = prev + curr
            prev = temp

        return curr


def fibonacci(n: int) -> int:
    """
    Calculate and return the nth Fibonacci number.

    Computes the nth number in the Fibonacci sequence, where each number is the sum of
    the two preceding ones. The sequence begins with F(0)=0 and F(1)=1, and continues
    as: 0, 1, 1, 2, 3, 5, 8, 13, 21, 34, 55, ...

    This function uses an iterative algorithm with O(n) time complexity and O(1) space
    complexity, making it efficient for computing Fibonacci numbers without risk of
    stack overflow on large values of n.

    Args:
        n: The position in the Fibonacci sequence to calculate. Must be a non-negative
           integer. Negative values will raise ValueError.

    Returns:
        int: The nth Fibonacci number. For n=0, returns 0. For n=1, returns 1.
             For n>=2, returns the sum of the two preceding Fibonacci numbers.

    Raises:
        TypeError: If n is not an integer type (e.g., float, string, None, bool).
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

    Semantic Unit: SU-003
    """
    # Validate input: type check and range check
    FibonacciValidator.validate_input(n)

    # Calculate and return the Fibonacci number
    return FibonacciCalculator.calculate(n)