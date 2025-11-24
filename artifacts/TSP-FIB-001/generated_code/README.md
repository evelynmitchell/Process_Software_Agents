# Fibonacci Calculator

A Python implementation of the Fibonacci sequence calculator with comprehensive input validation, efficient iterative computation, and detailed documentation.

## Overview

This project provides a robust implementation of the Fibonacci sequence calculator. The `fibonacci(n)` function computes the nth Fibonacci number using an iterative algorithm with O(n) time complexity and O(1) space complexity.

The implementation follows a three-component architecture:
- **FibonacciValidator**: Validates input parameters and enforces type constraints
- **FibonacciCalculator**: Computes the nth Fibonacci number using an iterative approach
- **FibonacciFunction**: Public interface that orchestrates validation and calculation

## Features

- **Type-Safe**: Full type hints for all functions and parameters
- **Input Validation**: Comprehensive validation with descriptive error messages
- **Efficient**: Iterative algorithm with O(n) time complexity and O(1) space complexity
- **Well-Documented**: Extensive docstrings with usage examples
- **Edge Case Handling**: Proper handling of base cases (n=0, n=1)
- **No External Dependencies**: Uses only Python standard library
- **Thoroughly Tested**: Comprehensive test suite with 80%+ code coverage

## Prerequisites

- Python 3.12 or higher
- pip package manager (for development and testing)

## Installation

1. Clone or download the project:
   ```bash
   git clone <repository-url>
   cd fibonacci-calculator
   ```

2. (Optional) Create a virtual environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install development dependencies (for testing):
   ```bash
   pip install -r requirements.txt
   ```

## Usage

### Basic Usage

```python
from fibonacci import fibonacci

# Calculate the 10th Fibonacci number
result = fibonacci(10)
print(result)  # Output: 55

# Calculate the 0th Fibonacci number
result = fibonacci(0)
print(result)  # Output: 0

# Calculate the 1st Fibonacci number
result = fibonacci(1)
print(result)  # Output: 1

# Calculate the 5th Fibonacci number
result = fibonacci(5)
print(result)  # Output: 5
```

### Error Handling

```python
from fibonacci import fibonacci

# Attempting to calculate Fibonacci for negative number raises ValueError
try:
    result = fibonacci(-5)
except ValueError as e:
    print(f"Error: {e}")  # Output: Error: n must be a non-negative integer
```

### In a Script

```python
#!/usr/bin/env python3
"""Example script demonstrating Fibonacci calculator usage."""

from fibonacci import fibonacci

def main():
    """Calculate and display Fibonacci numbers for various inputs."""
    test_values = [0, 1, 5, 10, 20, 50]
    
    print("Fibonacci Sequence Calculator")
    print("-" * 40)
    
    for n in test_values:
        result = fibonacci(n)
        print(f"fibonacci({n:2d}) = {result}")

if __name__ == "__main__":
    main()
```

## API Documentation

### fibonacci(n: int) -> int

Calculate the nth Fibonacci number.

**Parameters:**
- `n` (int): A non-negative integer representing the position in the Fibonacci sequence

**Returns:**
- (int): The nth Fibonacci number

**Raises:**
- `ValueError`: If n is a negative integer

**Time Complexity:** O(n)

**Space Complexity:** O(1)

**Examples:**

```python
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

>>> fibonacci(-1)
Traceback (most recent call last):
  ...
ValueError: n must be a non-negative integer
```

## Fibonacci Sequence Reference

The Fibonacci sequence is defined as:
- F(0) = 0
- F(1) = 1
- F(n) = F(n-1) + F(n-2) for n ≥ 2

The first 15 Fibonacci numbers are:
| n  | F(n) |
|----|------|
| 0  | 0    |
| 1  | 1    |
| 2  | 1    |
| 3  | 2    |
| 4  | 3    |
| 5  | 5    |
| 6  | 8    |
| 7  | 13   |
| 8  | 21   |
| 9  | 34   |
| 10 | 55   |
| 11 | 89   |
| 12 | 144  |
| 13 | 233  |
| 14 | 377  |

## Architecture

### Component Design

The implementation is organized into three components following the Single Responsibility Principle:

#### 1. FibonacciValidator (SU-001)
Responsible for validating input parameters before computation.

**Responsibilities:**
- Verify input is of type `int`
- Ensure input is non-negative (n ≥ 0)
- Raise `ValueError` with descriptive message for invalid inputs

**Key Method:**
- `validate_input(n: int) -> bool`: Returns True if valid, raises ValueError if invalid

#### 2. FibonacciCalculator (SU-002)
Responsible for computing the Fibonacci number using an iterative algorithm.

**Responsibilities:**
- Handle base cases (n=0 returns 0, n=1 returns 1)
- Implement iterative algorithm for n ≥ 2
- Maintain O(n) time complexity and O(1) space complexity

**Key Methods:**
- `calculate(n: int) -> int`: Computes and returns the nth Fibonacci number
- `handle_base_cases(n: int) -> int | None`: Returns Fibonacci value for base cases or None for n ≥ 2

#### 3. FibonacciFunction (SU-003)
Serves as the public interface orchestrating validation and calculation.

**Responsibilities:**
- Provide the public `fibonacci(n: int) -> int` function
- Integrate FibonacciValidator and FibonacciCalculator
- Provide comprehensive documentation with examples

## Testing

### Running Tests

Run the complete test suite:

```bash
pytest tests/ -v
```

Run tests with coverage report:

```bash
pytest tests/ --cov=fibonacci --cov-report=html
```

View the HTML coverage report:

```bash
open htmlcov/index.html  # On macOS
# or
xdg-open htmlcov/index.html  # On Linux
# or
start htmlcov/index.html  # On Windows
```

### Test Coverage

The test suite includes:

- **Unit Tests**: Individual component testing
  - Input validation tests (valid inputs, negative inputs, type validation)
  - Calculation tests (base cases, iterative computation)
  - Edge case tests (boundary values, large inputs)

- **Integration Tests**: End-to-end function testing
  - Happy path scenarios
  - Error handling scenarios
  - Output verification

- **Edge Case Tests**: Boundary and special condition testing
  - n=0 (first Fibonacci number)
  - n=1 (second Fibonacci number)
  - Large values of n
  - Negative values

**Target Coverage:** 80%+ of source code

### Example Test Cases

```python
def test_fibonacci_base_case_zero():
    """Test that fibonacci(0) returns 0."""
    assert fibonacci(0) == 0

def test_fibonacci_base_case_one():
    """Test that fibonacci(1) returns 1."""
    assert fibonacci(1) == 1

def test_fibonacci_fifth_number():
    """Test that fibonacci(5) returns 5."""
    assert fibonacci(5) == 5

def test_fibonacci_tenth_number():
    """Test that fibonacci(10) returns 55."""
    assert fibonacci(10) == 55

def test_fibonacci_negative_input_raises_error():
    """Test that fibonacci(-1) raises ValueError."""
    with pytest.raises(ValueError, match="non-negative"):
        fibonacci(-1)
```

## Project Structure

```