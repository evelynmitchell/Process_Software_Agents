"""
Entry point demonstrating usage of the fibonacci function with example calls and output.

This module serves as the main entry point for the Fibonacci application,
showcasing how to use the fibonacci function with various inputs and displaying
the computed results.

Author: ASP Code Agent
"""

from src.fibonacci import fibonacci


def main() -> None:
    """
    Main entry point demonstrating fibonacci function usage.

    Calls the fibonacci function with various inputs and displays the results.
    Demonstrates both successful computations and error handling for invalid inputs.

    Returns:
        None
    """
    print("=" * 60)
    print("Fibonacci Sequence Calculator - Demonstration")
    print("=" * 60)
    print()

    # Example 1: Base case - fibonacci(0)
    print("Example 1: fibonacci(0)")
    result = fibonacci(0)
    print(f"  Result: {result}")
    print(f"  Expected: 0")
    print()

    # Example 2: Base case - fibonacci(1)
    print("Example 2: fibonacci(1)")
    result = fibonacci(1)
    print(f"  Result: {result}")
    print(f"  Expected: 1")
    print()

    # Example 3: Small value - fibonacci(5)
    print("Example 3: fibonacci(5)")
    result = fibonacci(5)
    print(f"  Result: {result}")
    print(f"  Expected: 5")
    print()

    # Example 4: Medium value - fibonacci(10)
    print("Example 4: fibonacci(10)")
    result = fibonacci(10)
    print(f"  Result: {result}")
    print(f"  Expected: 55")
    print()

    # Example 5: Larger value - fibonacci(20)
    print("Example 5: fibonacci(20)")
    result = fibonacci(20)
    print(f"  Result: {result}")
    print(f"  Expected: 6765")
    print()

    # Example 6: Error handling - negative input
    print("Example 6: fibonacci(-5) - Error Handling")
    try:
        result = fibonacci(-5)
        print(f"  Result: {result}")
    except ValueError as e:
        print(f"  Error caught: {e}")
        print(f"  Expected: ValueError for negative input")
    print()

    # Example 7: Sequence demonstration
    print("Example 7: First 15 Fibonacci Numbers")
    print("  Index | Fibonacci Value")
    print("  " + "-" * 25)
    for i in range(15):
        result = fibonacci(i)
        print(f"  {i:5d} | {result:15d}")
    print()

    print("=" * 60)
    print("Demonstration Complete")
    print("=" * 60)


if __name__ == "__main__":
    main()