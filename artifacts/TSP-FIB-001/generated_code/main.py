"""
Entry point demonstrating fibonacci function usage with example calls and output.

This module serves as the main entry point for the Fibonacci application,
showcasing the fibonacci function with various example inputs and displaying
the calculated results.

Component ID: None
Semantic Unit: None
"""

from src.fibonacci import fibonacci


def main() -> None:
    """
    Main entry point demonstrating fibonacci function usage.

    Calls the fibonacci function with various example inputs and prints
    the results to demonstrate correct functionality across different cases
    including edge cases (0, 1) and larger values.

    Returns:
        None
    """
    print("Fibonacci Function Demonstration")
    print("=" * 50)
    print()

    # Test cases demonstrating fibonacci function
    test_cases: list[int] = [0, 1, 2, 5, 10, 15, 20]

    print("Computing Fibonacci numbers:")
    print("-" * 50)

    for n in test_cases:
        result: int = fibonacci(n)
        print(f"fibonacci({n:2d}) = {result}")

    print()
    print("=" * 50)
    print("Demonstration complete!")
    print()

    # Additional demonstration with error handling
    print("Testing error handling with negative input:")
    print("-" * 50)

    try:
        invalid_result: int = fibonacci(-5)
        print(f"fibonacci(-5) = {invalid_result}")
    except ValueError as e:
        print(f"fibonacci(-5) raised ValueError: {e}")

    print()
    print("=" * 50)


if __name__ == "__main__":
    main()