# Sum Numbers Function

A simple Python utility that adds two integers together with comprehensive input validation and error handling.

## Overview

The `sum_numbers` function is a basic arithmetic utility that takes two integer parameters and returns their sum. It includes robust error handling for edge cases such as None values, type mismatches, and provides clear documentation for developers.

## Features

- Simple addition of two integers
- Comprehensive input validation (None checks and type validation)
- Support for positive, negative, and zero values
- Arbitrary precision integer arithmetic (Python 3.12+)
- Clear error messages for invalid inputs
- Complete docstring documentation with examples

## Prerequisites

- Python 3.12 or higher
- No external dependencies required

## Installation

1. Clone or download the project files
2. Ensure Python 3.12+ is installed on your system:
   ```bash
   python --version
   ```

## Running the Application

### Interactive Python Shell

Start Python and import the function:

```bash
python
>>> from sum_numbers import sum_numbers
>>> result = sum_numbers(5, 3)
>>> print(result)
8
```

### Running as a Script

Create a script file (e.g., `example.py`):

```python
from sum_numbers import sum_numbers

# Basic usage
result = sum_numbers(10, 20)
print(f"10 + 20 = {result}")

# Negative numbers
result = sum_numbers(-5, 3)
print(f"-5 + 3 = {result}")

# Zero values
result = sum_numbers(0, 42)
print(f"0 + 42 = {result}")
```

Run the script:

```bash
python example.py
```

## Usage Examples

### Basic Addition

```python
from sum_numbers import sum_numbers

# Add two positive integers
result = sum_numbers(5, 3)
print(result)  # Output: 8
```

### Negative Numbers

```python
# Add negative integers
result = sum_numbers(-10, -5)
print(result)  # Output: -15

# Mix positive and negative
result = sum_numbers(-7, 12)
print(result)  # Output: 5
```

### Zero Values

```python
# Add with zero
result = sum_numbers(0, 100)
print(result)  # Output: 100

# Both zero
result = sum_numbers(0, 0)
print(result)  # Output: 0
```

### Large Numbers

```python
# Python 3 supports arbitrary precision integers
result = sum_numbers(999999999999999999, 1)
print(result)  # Output: 1000000000000000000
```

## Error Handling

The function validates inputs and raises appropriate exceptions for invalid cases.

### None Values

Passing None as either argument raises a TypeError:

```python
from sum_numbers import sum_numbers

try:
    result = sum_numbers(None, 5)
except TypeError as e:
    print(e)  # Output: Arguments cannot be None
```

### Type Mismatches

Passing non-integer values raises a TypeError:

```python
from sum_numbers import sum_numbers

try:
    result = sum_numbers("5", 3)
except TypeError as e:
    print(e)  # Output: Both arguments must be integers
```

### Valid Type: Booleans

Note: In Python, `bool` is a subclass of `int`, so boolean values are accepted:

```python
from sum_numbers import sum_numbers

result = sum_numbers(True, False)
print(result)  # Output: 1 (True=1, False=0)
```

## Testing

### Running Tests

Run the test suite using pytest:

```bash
pytest tests/ -v
```

Run tests with coverage report:

```bash
pytest tests/ --cov=. --cov-report=html
```

Run tests with verbose output:

```bash
pytest tests/ -v -s
```

### Test Coverage

The test suite includes:

- **Happy path tests:** Basic addition with positive, negative, and zero values
- **Edge case tests:** Large numbers, zero values, negative numbers
- **Error case tests:** None values, type mismatches, invalid inputs
- **Type validation tests:** Boolean values, string inputs, float inputs
- **Response validation tests:** Correct return types and values

### Example Test Run

```bash
$ pytest tests/ -v
tests/test_sum_numbers.py::test_sum_positive_integers PASSED
tests/test_sum_numbers.py::test_sum_negative_integers PASSED
tests/test_sum_numbers.py::test_sum_mixed_signs PASSED
tests/test_sum_numbers.py::test_sum_with_zero PASSED
tests/test_sum_numbers.py::test_sum_large_numbers PASSED
tests/test_sum_numbers.py::test_none_first_argument PASSED
tests/test_sum_numbers.py::test_none_second_argument PASSED
tests/test_sum_numbers.py::test_non_integer_first_argument PASSED
tests/test_sum_numbers.py::test_non_integer_second_argument PASSED
tests/test_sum_numbers.py::test_float_arguments PASSED
tests/test_sum_numbers.py::test_string_arguments PASSED
tests/test_sum_numbers.py::test_boolean_arguments PASSED

======================== 12 passed in 0.05s ========================
```

## Function Signature

```python
def sum_numbers(a: int, b: int) -> int:
    """
    Sum two integer numbers and return the result.
    
    Args:
        a: First integer to sum
        b: Second integer to sum
    
    Returns:
        The sum of a and b as an integer
    
    Raises:
        TypeError: If either argument is None or not an integer
    
    Examples:
        >>> sum_numbers(5, 3)
        8
        >>> sum_numbers(-5, 3)
        -2
    """
```

## Implementation Details

### Input Validation

The function performs two levels of validation:

1. **None Check:** Ensures neither argument is None
2. **Type Check:** Ensures both arguments are integers using `isinstance()`

### Arithmetic Operation

The function uses Python's built-in addition operator (`+`) to compute the sum. Python 3 provides arbitrary precision integer arithmetic, so there are no overflow concerns.

### Return Value

The function returns the computed sum as an integer.

## Troubleshooting

### ImportError: No module named 'sum_numbers'

Ensure the `sum_numbers.py` file is in your Python path or current working directory:

```bash
# Check current directory
ls sum_numbers.py

# Or add to Python path
export PYTHONPATH="${PYTHONPATH}:/path/to/project"
```

### TypeError: Both arguments must be integers

Verify you're passing integer values, not strings or other types:

```python
# Incorrect
result = sum_numbers("5", "3")

# Correct
result = sum_numbers(5, 3)
```

### TypeError: Arguments cannot be None

Ensure neither argument is None:

```python
# Incorrect
result = sum_numbers(None, 5)

# Correct
result = sum_numbers(0, 5)
```

### Python Version Error

Ensure you're using Python 3.12 or higher:

```bash
python --version
# Should output: Python 3.12.x or higher
```

## Project Structure

```
project/
├── sum_numbers.py          # Main function implementation
├── tests/
│   └── test_sum_numbers.py # Unit tests
├── README.md               # This file
└── requirements.txt        # Project dependencies (if any)
```

## Performance Characteristics

- **Time Complexity:** O(1) - constant time addition
- **Space Complexity:** O(1) - no additional memory allocation
- **Execution Speed:** Microseconds for typical integer values

## Limitations and Notes

- The function accepts boolean values (True/False) as integers since `bool` is a subclass of `int` in Python
- Python 3 provides arbitrary precision integers, so very large numbers are supported without overflow
- Type hints are not enforced at runtime by default; they serve as documentation and can be checked with static analysis tools like mypy
- The function is pure (no side effects) and deterministic

## Contributing