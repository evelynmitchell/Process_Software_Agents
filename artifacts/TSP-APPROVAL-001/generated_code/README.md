# Sum Numbers Function

A simple Python utility module that provides a function to add two integers together.

## Overview

The `sum_numbers` function is a basic arithmetic utility that takes two integer parameters and returns their sum. This module demonstrates proper Python practices including type hints, comprehensive documentation, and robust error handling.

## Features

- **Type-safe function signature** with Python 3.12+ type hints
- **Comprehensive error handling** for None values, type mismatches, and invalid inputs
- **Complete documentation** with docstrings and usage examples
- **Edge case handling** including boolean rejection and overflow support
- **Pure function** with no side effects or external dependencies

## Prerequisites

- Python 3.12 or higher
- No external dependencies required

## Installation

1. Clone or download the project files
2. Ensure Python 3.12+ is installed:
   ```bash
   python --version
   ```

## Running the Module

### Interactive Python Shell

```bash
python3
>>> from sum_numbers import sum_numbers
>>> result = sum_numbers(2, 3)
>>> print(result)
5
```

### As a Script

Create a test script `test_usage.py`:

```python
from sum_numbers import sum_numbers

# Basic usage
print(sum_numbers(2, 3))        # Output: 5
print(sum_numbers(-2, 3))       # Output: 1
print(sum_numbers(-2, -3))      # Output: -5
print(sum_numbers(0, 0))        # Output: 0
print(sum_numbers(100, 200))    # Output: 300
```

Run the script:

```bash
python3 test_usage.py
```

## API Documentation

### Function Signature

```python
def sum_numbers(a: int, b: int) -> int:
    """
    Add two integers together and return the result.
    
    This function takes two integer parameters and returns their arithmetic sum.
    It includes comprehensive validation to ensure both parameters are valid
    integers and handles edge cases appropriately.
    
    Args:
        a (int): The first integer to add.
        b (int): The second integer to add.
    
    Returns:
        int: The sum of a and b.
    
    Raises:
        TypeError: If either parameter is None, not an integer, or is a boolean.
        ValueError: If an unexpected error occurs during addition.
    
    Examples:
        >>> sum_numbers(2, 3)
        5
        
        >>> sum_numbers(-2, 3)
        1
        
        >>> sum_numbers(-2, -3)
        -5
        
        >>> sum_numbers(0, 0)
        0
        
        >>> sum_numbers(100, 200)
        300
    """
```

### Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `a` | `int` | The first integer to add |
| `b` | `int` | The second integer to add |

### Return Value

| Type | Description |
|------|-------------|
| `int` | The arithmetic sum of parameters `a` and `b` |

### Exceptions

| Exception | Condition |
|-----------|-----------|
| `TypeError` | If either parameter is `None` |
| `TypeError` | If either parameter is not an integer |
| `TypeError` | If either parameter is a boolean value |
| `ValueError` | If an unexpected error occurs during computation |

### Usage Examples

#### Basic Addition

```python
from sum_numbers import sum_numbers

result = sum_numbers(2, 3)
print(result)  # Output: 5
```

#### Negative Numbers

```python
result = sum_numbers(-5, 3)
print(result)  # Output: -2
```

#### Zero Values

```python
result = sum_numbers(0, 10)
print(result)  # Output: 10
```

#### Large Numbers

```python
result = sum_numbers(10**100, 10**100)
print(result)  # Output: 2 followed by 100 zeros
```

#### Error Handling

```python
try:
    sum_numbers(None, 5)
except TypeError as e:
    print(f"Error: {e}")  # Output: Error: Parameter a cannot be None

try:
    sum_numbers("5", 3)
except TypeError as e:
    print(f"Error: {e}")  # Output: Error: Parameter a must be an integer, got str

try:
    sum_numbers(True, 5)
except TypeError as e:
    print(f"Error: {e}")  # Output: Error: Parameter a must be an integer, got bool
```

## Running Tests

### Using pytest

Install pytest if not already installed:

```bash
pip install pytest
```

Run the test suite:

```bash
pytest tests/ -v
```

Run tests with coverage report:

```bash
pytest tests/ --cov=. --cov-report=html
```

### Using unittest

Run tests with Python's built-in unittest:

```bash
python -m unittest discover tests/ -v
```

### Test Coverage

The test suite covers:

- **Happy path cases**: Basic addition with positive, negative, and zero values
- **Edge cases**: Zero inputs, large numbers, mixed signs
- **Error cases**: None values, type mismatches, boolean inputs
- **Boundary conditions**: Minimum/maximum integer values, overflow scenarios

Expected coverage: 80%+ of the source code

## Implementation Details

### Component Architecture

The `sum_numbers` function is built on four logical components:

1. **Function Signature (SU-001)**: Defines the function with proper type hints
   - Parameters: `a: int`, `b: int`
   - Return type: `int`
   - No default values

2. **Addition Logic (SU-002)**: Implements the core arithmetic operation
   - Computes `a + b`
   - Returns the result as an integer
   - Leverages Python's native integer arithmetic

3. **Documentation (SU-003)**: Provides comprehensive docstring
   - One-line summary
   - Extended description
   - Args section with types
   - Returns section
   - Examples section with usage

4. **Edge Case Handling (SU-004)**: Validates inputs and handles errors
   - None value checking
   - Type validation
   - Boolean rejection (since `bool` is a subclass of `int`)
   - Overflow handling (Python 3 supports arbitrary precision)

### Error Handling Strategy

The function implements four layers of validation:

1. **None Check**: Raises `TypeError` if either parameter is `None`
2. **Type Check**: Raises `TypeError` if either parameter is not an integer
3. **Boolean Check**: Raises `TypeError` if either parameter is a boolean (explicit rejection)
4. **Computation**: Performs addition and returns result

### Python 3.12+ Features

The implementation uses modern Python features:

- **Type hints**: Full type annotation for parameters and return value
- **Docstring format**: Google-style or NumPy-style docstrings
- **Exception handling**: Specific exception types with descriptive messages
- **Arbitrary precision integers**: Native support for large numbers

## Troubleshooting

### TypeError: Parameter a cannot be None

**Problem**: You passed `None` as the first parameter.

**Solution**: Ensure both parameters are valid integers:

```python
# Wrong
sum_numbers(None, 5)

# Correct
sum_numbers(0, 5)
```

### TypeError: Parameter b must be an integer, got str

**Problem**: You passed a string instead of an integer.

**Solution**: Convert the string to an integer or pass an integer directly:

```python
# Wrong
sum_numbers(2, "3")

# Correct
sum_numbers(2, 3)
# or
sum_numbers(2, int("3"))
```

### TypeError: Parameter a must be an integer, got bool

**Problem**: You passed a boolean value (True or False).

**Solution**: Use integers instead of booleans:

```python
# Wrong
sum_numbers(True, False)

# Correct
sum_numbers(1, 0)
```

### ImportError: No module named 'sum_numbers'

**Problem**: The module is not in your Python path.

**Solution**: Ensure you're running from the correct directory:

```bash
# Make sure you're in the project root directory
cd /path/to/project
python3
>>>