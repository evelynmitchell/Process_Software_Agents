"""
Core module implementing the sum_numbers function.

This module provides a simple arithmetic function that adds two integers together.
It includes comprehensive type hints, detailed documentation, and robust edge case
handling for None values and type mismatches.

Component IDs:
- SumNumbersFunction (SU-001)
- SumNumbersAdditionLogic (SU-002)
- SumNumbersDocumentation (SU-003)
- SumNumbersEdgeCaseHandler (SU-004)

Task ID: TSP-APPROVAL-001
"""


def sum_numbers(a: int, b: int) -> int:
    """
    Add two integers together and return the result.

    This function takes two integer parameters and computes their sum using
    Python's built-in addition operator. It includes comprehensive validation
    to ensure both parameters are valid integers and handles edge cases such
    as None values, type mismatches, and boolean inputs.

    Args:
        a (int): The first integer to be added. Must be a valid integer type.
        b (int): The second integer to be added. Must be a valid integer type.

    Returns:
        int: The sum of the two input integers (a + b).

    Raises:
        TypeError: If either parameter is None, not an integer, or is a boolean.
        ValueError: If an unexpected error occurs during computation.

    Examples:
        >>> sum_numbers(2, 3)
        5

        >>> sum_numbers(-2, 3)
        1

        >>> sum_numbers(-2, -3)
        -5

        >>> sum_numbers(0, 0)
        0

        >>> sum_numbers(0, 5)
        5

        >>> sum_numbers(100, 200)
        300

        >>> sum_numbers(-100, -200)
        -300

        >>> sum_numbers(10**100, 10**100)
        20000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000
    """
    # Validate that parameter 'a' is not None
    if a is None:
        raise TypeError("Parameter 'a' cannot be None")

    # Validate that parameter 'b' is not None
    if b is None:
        raise TypeError("Parameter 'b' cannot be None")

    # Explicitly reject boolean values since bool is a subclass of int in Python
    # This ensures that True/False are not silently converted to 1/0
    if isinstance(a, bool):
        raise TypeError(
            f"Parameter 'a' must be an integer, got {type(a).__name__}"
        )

    if isinstance(b, bool):
        raise TypeError(
            f"Parameter 'b' must be an integer, got {type(b).__name__}"
        )

    # Validate that parameter 'a' is an integer
    if not isinstance(a, int):
        raise TypeError(
            f"Parameter 'a' must be an integer, got {type(a).__name__}"
        )

    # Validate that parameter 'b' is an integer
    if not isinstance(b, int):
        raise TypeError(
            f"Parameter 'b' must be an integer, got {type(b).__name__}"
        )

    try:
        # Perform the addition operation using Python's built-in addition operator
        # Python 3 handles arbitrary precision integers natively, so overflow
        # is not a concern for standard or very large integer values
        result = a + b
        return result
    except Exception as error:
        # Catch any unexpected errors and re-raise as ValueError with context
        raise ValueError(
            f"An unexpected error occurred during addition: {str(error)}"
        ) from error