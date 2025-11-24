"""
Fibonacci Function Module

Main public Fibonacci function with comprehensive docstring, type hints, and orchestration
of validation and calculation components.

This module provides the primary interface for computing Fibonacci numbers with full input
validation and efficient iterative computation.

Component ID: FibonacciFunction
Semantic Unit ID: SU-003

Author: ASP Code Agent
"""

from src.fibonacci_validator import FibonacciValidator
from src.fibonacci_calculator import FibonacciCalculator


def fibonacci(n: int) -> int:
    """
    Calculate the nth Fibonacci number.

    The Fibonacci sequence is a series of numbers where each number is the sum of the
    two preceding ones, starting from 0 and 1. This function computes the nth number
    in this sequence using an efficient iterative algorithm.

    The function validates input to ensure n is a non-negative integer, then uses an
    iterative approach to compute the result with O(n) time complexity and O(1) space
    complexity.

    Parameters
    ----------
    n : int
        The position in the Fibonacci sequence to compute. Must be a non-negative
        integer (n >= 0). Negative values will raise a ValueError.

    Returns
    -------
    int
        The nth Fibonacci number. For n=0, returns 0. For n=1, returns 1.
        For n >= 2, returns the sum of the two preceding Fibonacci numbers.

    Raises
    ------
    ValueError
        If n is negative. The error message will indicate that n must be a
        non-negative integer.
    TypeError
        If n is not an integer type (e.g., float, string, None).

    Examples
    --------
    >>> fibonacci(0)
    0

    >>> fibonacci(1)
    1

    >>> fibonacci(5)
    5

    >>> fibonacci(10)
    55

    >>> fibonacci(15)
    610

    >>> fibonacci(20)
    6765

    Notes
    -----
    The Fibonacci sequence is defined as:
    - F(0) = 0
    - F(1) = 1
    - F(n) = F(n-1) + F(n-2) for n >= 2

    This implementation uses an iterative algorithm rather than recursion to avoid
    stack overflow and achieve optimal performance. The algorithm maintains only two
    variables (a and b) to track the previous two Fibonacci numbers, resulting in
    constant space complexity.

    Time Complexity: O(n)
    Space Complexity: O(1)

    Raises
    ------
    ValueError
        When n is a negative integer.
    TypeError
        When n is not an integer type.
    """
    # Validate input using FibonacciValidator component
    validator = FibonacciValidator()
    validator.validate_input(n)

    # Calculate Fibonacci number using FibonacciCalculator component
    calculator = FibonacciCalculator()
    result = calculator.calculate(n)

    return result
</content>