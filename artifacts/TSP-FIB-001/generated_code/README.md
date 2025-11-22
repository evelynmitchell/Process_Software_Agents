# Fibonacci Function Project

A simple, efficient Python implementation of the Fibonacci sequence calculator with comprehensive documentation and test coverage.

## Overview

This project provides a production-ready implementation of the Fibonacci function that calculates the nth number in the Fibonacci sequence using an iterative approach. The implementation emphasizes correctness, performance, and maintainability through proper input validation, comprehensive documentation, and thorough test coverage.

### Features

- **Efficient Iterative Algorithm**: O(n) time complexity with O(1) space complexity
- **Robust Input Validation**: Type checking and range validation with descriptive error messages
- **Comprehensive Documentation**: Detailed docstrings with multiple usage examples
- **Full Test Coverage**: Unit tests covering happy paths, edge cases, and error conditions
- **Type Hints**: Complete type annotations for better code clarity and IDE support
- **PEP 8 Compliant**: Follows Python style guidelines throughout

## Prerequisites

- Python 3.12 or higher
- pip package manager
- pytest (for running tests)

## Installation

### 1. Clone or Download the Project

```bash
git clone <repository-url>
cd fibonacci-project
```

### 2. Create a Virtual Environment (Recommended)

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies

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
```

### Common Examples

```python
from fibonacci import fibonacci

# Fibonacci sequence: 0, 1, 1, 2, 3, 5, 8, 13, 21, 34, 55, ...

fibonacci(0)   # Returns: 0
fibonacci(1)   # Returns: 1
fibonacci(2)   # Returns: 1
fibonacci(3)   # Returns: 2
fibonacci(5)   # Returns: 5
fibonacci(10)  # Returns: 55
fibonacci(15)  # Returns: 610
fibonacci(20)  # Returns: 6765
```

### Error Handling

```python
from fibonacci import fibonacci

# Attempting to calculate Fibonacci for a negative number raises ValueError
try:
    result = fibonacci(-5)
except ValueError as e:
    print(f"Error: {e}")  # Output: Error: n must be a non-negative integer

# Attempting to use a non-integer type raises ValueError
try:
    result = fibonacci(5.5)
except ValueError as e:
    print(f"Error: {e}")  # Output: Error: n must be a non-negative integer

# Attempting to use a string raises ValueError
try:
    result = fibonacci("10")
except ValueError as e:
    print(f"Error: {e}")  # Output: Error: n must be a non-negative integer
```

## Project Structure

```
fibonacci-project/
├── fibonacci.py          # Main implementation with fibonacci() function
├── tests/
│   └── test_fibonacci.py # Comprehensive unit tests
├── requirements.txt      # Python dependencies
├── README.md            # This file
└── .gitignore           # Git ignore rules
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

### Run Specific Test

```bash
pytest tests/test_fibonacci.py::test_fibonacci_returns_zero_for_zero -v
```

### Run Tests with Detailed Output

```bash
pytest tests/ -vv --tb=short
```

## API Documentation

### fibonacci(n: int) -> int

Calculate the nth Fibonacci number using an iterative approach.

#### Parameters

- **n** (int): The position in the Fibonacci sequence (0-indexed). Must be a non-negative integer.

#### Returns

- (int): The nth Fibonacci number

#### Raises

- **ValueError**: If n is negative or not an integer type

#### Examples

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
```

#### Algorithm Details

The function uses an iterative approach with two variables to track the previous and current Fibonacci numbers:

1. **Base Cases**: For n=0, return 0; for n=1, return 1
2. **Iteration**: For n≥2, iterate n-1 times, updating the two variables
3. **Return**: Return the final current value

**Time Complexity**: O(n) - single pass through n iterations
**Space Complexity**: O(1) - only two variables used regardless of input size

#### Why Iterative Over Recursive?

The iterative approach is preferred because:
- Avoids stack overflow for large values of n
- More efficient with no function call overhead
- Constant space usage instead of O(n) recursion stack
- Faster execution for practical use cases

## Implementation Details

### Component Architecture

The implementation is organized into three logical components:

#### 1. FibonacciValidator (SU-001)

Validates input parameters and enforces type constraints:
- Checks that input is an integer type (not float, string, etc.)
- Verifies that n is non-negative
- Raises ValueError with descriptive message for invalid inputs

#### 2. FibonacciCalculator (SU-002)

Implements the core iterative Fibonacci algorithm:
- Handles base cases (n=0 returns 0, n=1 returns 1)
- Uses two-variable state tracking for iteration
- Achieves O(n) time complexity and O(1) space complexity

#### 3. FibonacciFunction (SU-003)

Public API that orchestrates validation and calculation:
- Validates input using FibonacciValidator
- Calculates result using FibonacciCalculator
- Provides comprehensive documentation with examples

## Testing Strategy

The test suite provides comprehensive coverage including:

### Happy Path Tests
- Correct results for base cases (0, 1)
- Correct results for small values (2-10)
- Correct results for larger values (15, 20)

### Edge Case Tests
- Boundary values (0, 1)
- Consecutive Fibonacci numbers
- Sequence correctness verification

### Error Case Tests
- Negative integer inputs
- Float inputs
- String inputs
- None inputs
- Other invalid types

### Test Coverage

Target: 80%+ code coverage of the fibonacci module

Run coverage analysis:
```bash
pytest tests/ --cov=fibonacci --cov-report=term-missing
```

## Troubleshooting

### ImportError: No module named 'fibonacci'

**Solution**: Ensure you're running Python from the project root directory and the fibonacci.py file is in the same directory or in the Python path.

```bash
# From project root
python3 -c "from fibonacci import fibonacci; print(fibonacci(10))"
```

### ValueError: n must be a non-negative integer

**Cause**: You passed a negative number, float, string, or other invalid type to the fibonacci function.

**Solution**: Ensure you pass a non-negative integer:

```python
# Correct
fibonacci(10)      # ✓ Integer
fibonacci(0)       # ✓ Zero is valid

# Incorrect
fibonacci(-5)      # ✗ Negative
fibonacci(5.5)     # ✗ Float
fibonacci("10")    # ✗ String
```

### Tests Fail with ModuleNotFoundError

**Solution**: Install dependencies and ensure pytest is available:

```bash
pip install -r requirements.txt
pytest tests/ -v
```

### Virtual Environment Not Activating

**Solution**: Use the correct activation command for your OS:

```bash
# Linux/macOS
source venv/bin/activate

# Windows
venv\Scripts\activate

# Verify activation (prompt should show (venv))
which python  # Should show path inside venv directory
```

## Performance Characteristics

### Time Complexity: O(