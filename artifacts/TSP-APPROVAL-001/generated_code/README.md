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

The test suite includes:

- **Happy path tests**: Valid integer inputs with expected results
- **Edge case tests**: Zero values, negative numbers, large numbers
- **Error case tests**: None values, type mismatches, boolean inputs
- **Boundary tests**: Minimum and maximum integer values
- **Integration tests**: Multiple function calls in sequence

Expected coverage: 80%+ of source code

## Troubleshooting

### ImportError: No module named 'sum_numbers'

**Problem:** Python cannot find the `sum_numbers` module.

**Solution:** Ensure you are running Python from the correct directory where `sum_numbers.py` is located:

```bash
# Check current directory
ls -la sum_numbers.py

# Run Python from the correct directory
python3
>>> from sum_numbers import sum_numbers
```

### TypeError: Parameter a cannot be None

**Problem:** You passed `None` as one of the parameters.

**Solution:** Ensure both parameters are valid integers:

```python
# Incorrect
sum_numbers(None, 5)

# Correct
sum_numbers(0, 5)
```

### TypeError: Parameter a must be an integer, got str

**Problem:** You passed a string instead of an integer.

**Solution:** Convert the value to an integer or pass an integer directly:

```python
# Incorrect
sum_numbers("5", 3)

# Correct
sum_numbers(5, 3)
sum_numbers(int("5"), 3)
```

### TypeError: Parameter a must be an integer, got bool

**Problem:** You passed a boolean value (True or False) instead of an integer.

**Solution:** Use integer values instead of booleans:

```python
# Incorrect
sum_numbers(True, False)

# Correct
sum_numbers(1, 0)
```

### Python Version Error

**Problem:** `SyntaxError` or type hint errors when running the module.

**Solution:** Ensure you are using Python 3.12 or higher:

```bash
python3 --version
# Should output: Python 3.12.x or higher

# If not, install Python 3.12+
# On macOS with Homebrew:
brew install python@3.12

# On Ubuntu/Debian:
sudo apt-get install python3.12

# On Windows:
# Download from https://www.python.org/downloads/
```

### Module Not Executing

**Problem:** Running `python sum_numbers.py` produces no output.

**Solution:** The module is designed to be imported, not executed directly. Use it in another script or the Python interactive shell:

```bash
# Correct usage
python3
>>> from sum_numbers import sum_numbers
>>> print(sum_numbers(2, 3))
5

# Or create a test script
cat > test.py << 'EOF'
from sum_numbers import sum_numbers
print(sum_numbers(2, 3))
EOF
python3 test.py
```

## Performance Characteristics

- **Time Complexity:** O(1) - constant time operation
- **Space Complexity:** O(1) - constant space usage
- **Execution Speed:** Microseconds for typical integer values
- **Scalability:** Handles arbitrary precision integers (Python 3 feature)

## Design Notes

### Architecture

The `sum_numbers` function is implemented as a pure function with four integrated layers: