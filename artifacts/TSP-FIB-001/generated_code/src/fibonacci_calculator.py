"""
Fibonacci Calculator Component

Implements iterative Fibonacci computation with O(n) time complexity and O(1) space complexity.
Includes input validation, base case handling, and comprehensive documentation.

Component ID: FibonacciCalculator
Semantic Unit: SU-002, SU-001, SU-003
Task ID: TSP-FIB-001

Author: ASP Code Agent
"""


class FibonacciValidator:
    """
    Validates input parameters for Fibonacci computation.

    Responsible for enforcing type constraints and value range validation
    before computation begins. Raises ValueError for invalid inputs.

    Semantic Unit: SU-001
    """

    @staticmethod
    def validate_input(n: int) -> bool:
        """
        Validate that input n is a non-negative integer.

        Checks that the input is of type int and is non-negative (>= 0).
        Rejects float values and other numeric types.

        Args:
            n: The input value to validate

        Returns:
            bool: True if input is valid

        Raises:
            TypeError: If n is not an integer type
            ValueError: If n is negative

        Raises:
            ValueError: If n is a negative integer
            TypeError: If n is not an integer type

        Examples:
            >>> FibonacciValidator.validate_input(5)
            True
            >>> FibonacciValidator.validate_input(0)
            True
            >>> FibonacciValidator.validate_input(-1)
            Traceback (most recent call last):
                ...
            ValueError: n must be a non-negative integer
            >>> FibonacciValidator.validate_input(5.0)
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
    Computes Fibonacci numbers using iterative algorithm.

    Implements O(n) time complexity and O(1) space complexity computation
    using an iterative approach with edge case handling for base cases.

    Semantic Unit: SU-002
    """

    @staticmethod
    def handle_base_cases(n: int) -> int | None:
        """
        Handle base cases for Fibonacci computation.

        Returns the Fibonacci value for n=0 and n=1 directly.
        Returns None for n >= 2 to indicate iteration is needed.

        Args:
            n: The input value (assumed to be non-negative)

        Returns:
            int: Fibonacci value for n=0 (returns 0) or n=1 (returns 1)
            None: For n >= 2, indicating iteration is required

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
        elif n == 1:
            return 1
        else:
            return None

    @staticmethod
    def calculate(n: int) -> int:
        """
        Calculate the nth Fibonacci number using iterative algorithm.

        Uses an iterative approach with two variables (a, b) to compute
        the Fibonacci sequence. Time complexity is O(n), space complexity
        is O(1) with only constant variables.

        The algorithm:
        1. Initialize a=0, b=1
        2. Loop n times, swapping values: a, b = b, a+b
        3. Return the final value of a

        Args:
            n: Non-negative integer index in Fibonacci sequence

        Returns:
            int: The nth Fibonacci number

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

    Computes the nth number in the Fibonacci sequence using an iterative
    algorithm with O(n) time complexity and O(1) space complexity.

    The Fibonacci sequence is defined as:
    - F(0) = 0
    - F(1) = 1
    - F(n) = F(n-1) + F(n-2) for n >= 2

    This function validates input and uses an iterative approach to avoid
    recursion overhead and stack overflow risks.

    Args:
        n: Non-negative integer representing the position in the Fibonacci
           sequence. Must be >= 0.

    Returns:
        int: The nth Fibonacci number

    Raises:
        ValueError: If n is negative
        TypeError: If n is not an integer type

    Examples:
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
    """
    FibonacciValidator.validate_input(n)
    return FibonacciCalculator.calculate(n)