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

    # Test cases demonstrating the fibonacci function
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

    # Additional demonstration: showing the sequence
    print("Fibonacci Sequence (first 15 numbers):")
    print("-" * 50)
    sequence: list[int] = [fibonacci(i) for i in range(15)]
    print(", ".join(str(num) for num in sequence))
    print()

    # Error handling demonstration
    print("Error Handling Demonstration:")
    print("-" * 50)
    try:
        print("Attempting to calculate fibonacci(-5)...")
        result = fibonacci(-5)
        print(f"Result: {result}")
    except ValueError as e:
        print(f"Caught expected error: {e}")
    print()

    print("All demonstrations completed successfully!")


if __name__ == "__main__":
    main()