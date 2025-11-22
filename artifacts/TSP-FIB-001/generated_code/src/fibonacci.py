"""
Fibonacci calculation module with validation and computation orchestration.

This module provides a public API function for calculating Fibonacci numbers with
comprehensive input validation and error handling. The implementation uses an
iterative approach for optimal performance.

Component ID: FibonacciFunction
Semantic Unit ID: SU-003

Author: ASP Code Agent
"""

from src.fibonacci_validator import FibonacciValidator
from src.fibonacci_calculator import FibonacciCalculator


def fibonacci(n: int) -> int:
    """
    Calculate and return the nth Fibonacci number.

    The Fibonacci sequence is a series of numbers where each number is the sum
    of the two preceding ones, typically starting with 0 and 1. This function
    computes the nth number in this sequence using an efficient iterative
    approach with O(n) time complexity and O(1) space complexity.

    Args:
        n (int): The position in the Fibonacci sequence to calculate. Must be
            a non-negative integer (0 or greater). The function will raise a
            ValueError if a negative integer is provided.

    Returns:
        int: The nth Fibonacci number. For n=0, returns 0. For n=1, returns 1.
            For n>=2, returns the sum of the two preceding Fibonacci numbers.

    Raises:
        ValueError: If n is negative. The error message will indicate that
            n must be a non-negative integer.
        TypeError: If n is not an integer type (e.g., float, string, or other
            non-integer numeric types).

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

        >>> fibonacci(15)
        610

        Attempting to calculate with a negative number raises ValueError:

        >>> fibonacci(-1)
        Traceback (most recent call last):
            ...
        ValueError: n must be a non-negative integer

        Attempting to calculate with a non-integer type raises ValueError:

        >>> fibonacci(5.5)
        Traceback (most recent call last):
            ...
        ValueError: n must be a non-negative integer

    Note:
        The function uses an iterative algorithm rather than recursion to
        avoid stack overflow issues with large values of n. The implementation
        maintains constant space complexity regardless of input size.
    """
    # Validate input parameter
    validator = FibonacciValidator()
    validator.validate_input(n)

    # Calculate Fibonacci number
    calculator = FibonacciCalculator()
    result = calculator.calculate(n)

    return result
</code>