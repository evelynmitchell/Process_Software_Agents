"""
Fibonacci module providing iterative computation of Fibonacci numbers.

This module implements the Fibonacci sequence calculation with input validation
and comprehensive documentation. It provides a public fibonacci() function that
orchestrates validation and calculation.

Component IDs: FibonacciValidator, FibonacciCalculator, FibonacciFunction
Semantic Units: SU-001, SU-002, SU-003
Task ID: TSP-FIB-001

Author: ASP Code Agent
"""


class FibonacciValidator:
    """
    Validates input parameters for Fibonacci computation.

    This class handles input validation and enforces type constraints for the
    Fibonacci function. It ensures that only non-negative integers are accepted.

    Component ID: FibonacciValidator
    Semantic Unit ID: SU-001
    """

    @staticmethod
    def validate_input(n: int) -> bool:
        """
        Validate that input n is a non-negative integer.

        This method checks if the input is an integer type (excluding booleans)
        and is non-negative. It raises ValueError if validation fails.

        Args:
            n: The input value to validate.

        Returns:
            bool: True if validation passes.

        Raises:
            ValueError: If n is not an integer or is negative, with message
                'n must be a non-negative integer'.

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
            ValueError: n must be a non-negative integer
            >>> FibonacciValidator.validate_input(True)
            Traceback (most recent call last):
                ...
            ValueError: n must be a non-negative integer
        """
        # Exclude booleans explicitly since bool is a subclass of int in Python
        if isinstance(n, bool) or not isinstance(n, int):
            raise ValueError("n must be a non-negative integer")

        if n < 0:
            raise ValueError("n must be a non-negative integer")

        return True


class FibonacciCalculator:
    """
    Computes Fibonacci numbers using an iterative approach.

    This class implements the iterative Fibonacci algorithm with O(n) time
    complexity and O(1) space complexity. It handles edge cases for n=0 and n=1,
    and uses integer arithmetic for all computations.

    Component ID: FibonacciCalculator
    Semantic Unit ID: SU-002
    """

    @staticmethod
    def calculate(n: int) -> int:
        """
        Calculate the nth Fibonacci number using iterative algorithm.

        This method computes the nth Fibonacci number where the sequence is
        defined as: F(0)=0, F(1)=1, F(n)=F(n-1)+F(n-2) for n>=2.

        The iterative approach maintains two variables (prev and curr) that
        represent consecutive Fibonacci numbers, updating them in each iteration
        until the nth number is computed.

        Args:
            n: The position in the Fibonacci sequence (must be non-negative).

        Returns:
            int: The nth Fibonacci number.

        Time Complexity:
            O(n) - Single pass through n iterations.

        Space Complexity:
            O(1) - Only two variables used regardless of input size.

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
        # Handle base cases
        if n == 0:
            return 0
        if n == 1:
            return 1

        # Iterative computation for n >= 2
        prev = 0
        curr = 1

        for _ in range(2, n + 1):
            next_val = prev + curr
            prev = curr
            curr = next_val

        return curr


def fibonacci(n: int) -> int:
    """
    Calculate the nth Fibonacci number using iterative approach.

    This function computes the nth number in the Fibonacci sequence, which is
    a series of integers where each number is the sum of the two preceding ones.
    The sequence starts with 0 and 1: 0, 1, 1, 2, 3, 5, 8, 13, 21, 34, 55, ...

    The function validates the input to ensure it is a non-negative integer,
    then uses an iterative algorithm to compute the result efficiently with
    O(n) time complexity and O(1) space complexity.

    Args:
        n: The position in the Fibonacci sequence. Must be a non-negative integer
            (n >= 0). Represents which Fibonacci number to compute, where F(0)=0,
            F(1)=1, F(2)=1, F(3)=2, etc.

    Returns:
        int: The nth Fibonacci number. For n=0 returns 0, for n=1 returns 1,
            and for n>=2 returns the sum of the two preceding Fibonacci numbers.

    Raises:
        ValueError: If n is negative or not an integer type. The error message
            will be 'n must be a non-negative integer'. Note that boolean values
            (True, False) are rejected even though bool is a subclass of int.

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

    Component ID: FibonacciFunction
    Semantic Unit ID: SU-003
    Task ID: TSP-FIB-001
    """
    # Validate input using FibonacciValidator
    FibonacciValidator.validate_input(n)

    # Calculate Fibonacci number using FibonacciCalculator
    result = FibonacciCalculator.calculate(n)

    return result