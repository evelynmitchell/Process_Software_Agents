# Fibonacci Implementation

A pure Python implementation of the Fibonacci sequence calculator using an efficient iterative algorithm.

## Overview

This project provides a robust implementation of the Fibonacci sequence calculator that computes the nth Fibonacci number. The implementation uses an iterative approach with O(n) time complexity and O(1) space complexity, making it efficient for computing Fibonacci numbers without the overhead of recursion or memoization.

The Fibonacci sequence is defined as:
- F(0) = 0
- F(1) = 1
- F(n) = F(n-1) + F(n-2) for n ≥ 2

This results in the sequence: 0, 1, 1, 2, 3, 5, 8, 13, 21, 34, 55, 89, 144, ...

## Features

- **Efficient Iterative Algorithm**: O(n) time complexity with O(1) space complexity
- **Comprehensive Input Validation**: Rejects negative integers and non-integer types
- **Type Safety**: Full type hints for all parameters and return values
- **Detailed Documentation**: Google-style docstrings with usage examples
- **Edge Case Handling**: Correctly handles base cases (n=0, n=1) and large values
- **Pure Python**: No external dependencies, uses only Python standard library

## Prerequisites

- Python 3.12 or higher
- pip package manager (for development and testing)

## Installation

1. Clone or download the project:
   ```bash
   git clone <repository-url>
   cd fibonacci
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

# Calculate other Fibonacci numbers
print(fibonacci(0))   # Output: 0
print(fibonacci(1))   # Output: 1
print(fibonacci(5))   # Output: 5
print(fibonacci(15))  # Output: 610
```

### In Your Code

Simply import the `fibonacci` function and call it with a non-negative integer:

```python
from fibonacci import fibonacci

def process_sequence():
    """Process Fibonacci numbers up to the 20th term."""
    for n in range(21):
        fib_n = fibonacci(n)
        print(f"F({n}) = {fib_n}")
```

### Error Handling

The function validates input and raises `ValueError` for invalid inputs:

```python
from fibonacci import fibonacci

try:
    result = fibonacci(-5)
except ValueError as e:
    print(f"Error: {e}")  # Output: Error: n must be a non-negative integer

try:
    result = fibonacci(3.5)
except ValueError as e:
    print(f"Error: {e}")  # Output: Error: n must be a non-negative integer

try:
    result = fibonacci(True)  # Boolean is rejected even though it's technically an int
except ValueError as e:
    print(f"Error: {e}")  # Output: Error: n must be a non-negative integer
```

## API Reference

### `fibonacci(n: int) -> int`

Calculate the nth Fibonacci number using an iterative approach.

**Parameters:**
- `n` (int): The position in the Fibonacci sequence (must be non-negative)

**Returns:**
- (int): The nth Fibonacci number

**Raises:**
- `ValueError`: If n is negative or not an integer type

**Examples:**
```python
fibonacci(0)   # Returns 0
fibonacci(1)   # Returns 1
fibonacci(2)   # Returns 1
fibonacci(5)   # Returns 5
fibonacci(10)  # Returns 55
fibonacci(15)  # Returns 610
fibonacci(100) # Returns 354224848179261915075
```

## Running Tests

### Run All Tests

```bash
pytest tests/ -v
```

### Run Tests with Coverage Report

```bash
pytest tests/ --cov=. --cov-report=html
```

This generates an HTML coverage report in the `htmlcov/` directory.

### Run Specific Test File

```bash
pytest tests/test_fibonacci.py -v
```

### Run Tests with Detailed Output

```bash
pytest tests/ -vv --tb=short
```

## Design Rationale

### Why Iterative Over Recursive?

The implementation uses an iterative approach rather than recursion for several important reasons:

1. **Performance**: The iterative approach has O(n) time complexity with O(1) space complexity. A naive recursive implementation would have O(2^n) time complexity due to redundant calculations.

2. **Stack Safety**: Iterative approach avoids stack overflow errors that can occur with deep recursion. Python has a default recursion limit (~1000), which would prevent computing Fibonacci numbers beyond approximately F(1000).

3. **Memory Efficiency**: The iterative approach uses constant space regardless of n, while recursive approaches (even with memoization) require O(n) space for the call stack or memoization cache.

4. **Simplicity**: The iterative algorithm is straightforward and easy to understand, with clear variable names and minimal complexity.

### Algorithm Explanation

The iterative algorithm works as follows:

1. **Base Cases**: Handle n=0 and n=1 directly as they are the foundation of the sequence.

2. **Iteration**: For n ≥ 2, maintain two variables:
   - `prev`: The (i-1)th Fibonacci number
   - `curr`: The ith Fibonacci number

3. **Loop**: Iterate from 2 to n, computing the next Fibonacci number as the sum of the previous two, then shifting the window forward.

4. **Return**: After the loop completes, `curr` contains F(n).

**Time Complexity**: O(n) - single pass through n iterations
**Space Complexity**: O(1) - only two variables regardless of input size

### Input Validation Strategy

The implementation validates inputs to ensure:

1. **Type Checking**: Input must be an integer type (not float, string, etc.)
2. **Boolean Exclusion**: Booleans are explicitly rejected even though `isinstance(True, int)` returns True in Python
3. **Non-Negative Constraint**: Input must be >= 0 (negative integers are rejected)
4. **Clear Error Messages**: ValueError includes descriptive message for debugging

## Examples

### Computing Fibonacci Sequence

```python
from fibonacci import fibonacci

# Print first 20 Fibonacci numbers
for i in range(20):
    print(f"F({i:2d}) = {fibonacci(i):6d}")
```

Output:
```
F( 0) =      0
F( 1) =      1
F( 2) =      1
F( 3) =      2
F( 4) =      3
F( 5) =      5
F( 6) =      8
F( 7) =     13
F( 8) =     21
F( 9) =     34
F(10) =     55
F(11) =     89
F(12) =    144
F(13) =    233
F(14) =    377
F(15) =    610
F(16) =    987
F(17) =   1597
F(18) =   2584
F(19) =   4181
```

### Finding Fibonacci Numbers in a Range

```python
from fibonacci import fibonacci

def fibonacci_in_range(start: int, end: int) -> list[int]:
    """Find all Fibonacci numbers between start and end (inclusive)."""
    result = []
    n = 0
    while True:
        fib_n = fibonacci(n)
        if fib_n > end:
            break
        if fib_n >= start:
            result.append(fib_n)
        n += 1
    return result

# Find Fibonacci numbers between 10 and 1000
fibs = fibonacci_in_range(10, 1000)
print(fibs)  # Output: [13, 21, 34, 55, 89, 144, 233, 377, 610,