"""
Entry point module demonstrating usage of the sum_numbers function.

This module serves as the main entry point and demonstrates how to use the
sum_numbers function with various example invocations.

Author: ASP Code Agent
"""

from src.sum_numbers import sum_numbers


def main() -> None:
    """
    Main entry point demonstrating sum_numbers function usage.

    Executes several example invocations of the sum_numbers function
    with different input values to demonstrate its functionality.
    """
    print("Sum Numbers Function Examples")
    print("=" * 40)

    # Example 1: Positive integers
    result1 = sum_numbers(2, 3)
    print(f"sum_numbers(2, 3) = {result1}")

    # Example 2: Negative integers
    result2 = sum_numbers(-2, -3)
    print(f"sum_numbers(-2, -3) = {result2}")

    # Example 3: Mixed signs
    result3 = sum_numbers(-2, 3)
    print(f"sum_numbers(-2, 3) = {result3}")

    # Example 4: Zero values
    result4 = sum_numbers(0, 0)
    print(f"sum_numbers(0, 0) = {result4}")

    # Example 5: Zero with positive
    result5 = sum_numbers(0, 5)
    print(f"sum_numbers(0, 5) = {result5}")

    # Example 6: Large integers
    result6 = sum_numbers(1000000, 2000000)
    print(f"sum_numbers(1000000, 2000000) = {result6}")

    print("=" * 40)
    print("All examples completed successfully!")


if __name__ == "__main__":
    main()