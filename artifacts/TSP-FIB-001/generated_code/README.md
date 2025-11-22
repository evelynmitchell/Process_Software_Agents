# Fibonacci Calculator

A simple, efficient Python implementation of the Fibonacci sequence calculator with comprehensive input validation and documentation.

## Overview

This project provides a pure Python implementation of the Fibonacci sequence calculator. The implementation uses an iterative approach to compute the nth Fibonacci number efficiently, with proper input validation and comprehensive error handling.

### Features

- **Efficient Iterative Algorithm**: O(n) time complexity, O(1) space complexity
- **Input Validation**: Type checking and range validation with clear error messages
- **Comprehensive Documentation**: Google-style docstrings with multiple examples
- **Type Hints**: Full type annotations for better code clarity and IDE support
- **Error Handling**: Explicit validation of negative inputs with descriptive error messages
- **Edge Case Handling**: Proper handling of base cases (n=0, n=1)

## Prerequisites

- Python 3.12 or higher
- pip package manager (for running tests)

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
```

### Error Handling

```python
from fibonacci import fibonacci

# Attempting to calculate Fibonacci for negative input
try:
    result = fibonacci(-5)
except ValueError as e:
    print(f"Error: {e}")  # Output: Error: n must be a non-negative integer

# Attempting to pass non-integer input
try:
    result = fibonacci(5.5)
except ValueError as e:
    print(f"Error: {e}")  # Output: Error: n must be a non-negative integer
```

### Examples

```python
from fibonacci import fibonacci

# Base cases
fibonacci(0)   # Returns: 0
fibonacci(1)   # Returns: 1

# Small values
fibonacci(2)   # Returns: 1
fibonacci(3)   # Returns: 2
fibonacci(4)   # Returns: 3
fibonacci(5)   # Returns: 5

# Larger values
fibonacci(10)  # Returns: 55
fibonacci(15)  # Returns: 610
fibonacci(20)  # Returns: 6765
```

## Architecture

The implementation is organized into three logical components:

### 1. FibonacciValidator (SU-001)

**Responsibility**: Validates input parameters and enforces type constraints.

**Key Features**:
- Type checking: Ensures input is an integer, not float or string
- Range validation: Ensures input is non-negative
- Fast-fail approach: Validation occurs before any calculation

**Method**: `validate_input(n: int) -> bool`
- Raises `ValueError` if n is negative
- Raises `ValueError` if n is not an integer type
- Returns `True` if validation passes

### 2. FibonacciCalculator (SU-002)

**Responsibility**: Implements the core iterative Fibonacci calculation algorithm.

**Key Features**:
- Iterative approach: Uses two variables (prev, curr) to track state
- Base case handling: Explicit handling of n=0 and n=1
- Efficient computation: O(n) time complexity, O(1) space complexity
- No recursion: Avoids stack overflow on large values

**Methods**:
- `calculate(n: int) -> int`: Computes the nth Fibonacci number
- `handle_base_cases(n: int) -> int`: Returns Fibonacci value for n=0 or n=1

**Algorithm**:
```
For n = 0: return 0
For n = 1: return 1
For n >= 2:
    prev = 0, curr = 1
    Loop from 2 to n:
        temp = curr
        curr = prev + curr
        prev = temp
    Return curr
```

### 3. FibonacciFunction (SU-003)

**Responsibility**: Public API function that orchestrates validation and calculation.

**Key Features**:
- Input validation: Calls FibonacciValidator before calculation
- Calculation orchestration: Delegates to FibonacciCalculator
- Comprehensive documentation: Google-style docstring with examples
- Type hints: Full type annotations on function signature

**Function Signature**:
```python
def fibonacci(n: int) -> int:
    """Calculate and return the nth Fibonacci number."""
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
pytest tests/ -vv --tb=long
```

## Test Coverage

The test suite includes:

- **Happy Path Tests**: Valid inputs returning correct Fibonacci values
- **Edge Case Tests**: Base cases (n=0, n=1) and boundary conditions
- **Error Case Tests**: Negative inputs, non-integer inputs, invalid types
- **Type Validation Tests**: Ensuring type hints are respected
- **Performance Tests**: Verifying iterative approach efficiency

Target coverage: 80%+ of source code

## Design Decisions

### Iterative vs. Recursive

The implementation uses an **iterative approach** instead of recursion for the following reasons:

1. **Performance**: O(n) time complexity vs. O(2^n) for naive recursion
2. **Memory Safety**: O(1) space complexity vs. O(n) stack depth for recursion
3. **Scalability**: Can handle large n values without stack overflow
4. **Simplicity**: Easier to understand and maintain

### Input Validation Strategy

Input validation follows a **fail-fast** approach:

1. Type checking occurs first (is it an integer?)
2. Range checking occurs second (is it non-negative?)
3. Calculation only proceeds if validation passes
4. Clear error messages guide users to correct usage

### Error Handling

The implementation uses **explicit exceptions** rather than silent failures:

- `ValueError` is raised for invalid inputs
- Error messages clearly describe the problem
- No special return values (like -1 or None) for error cases
- Callers must handle exceptions explicitly

## Complexity Analysis

### Time Complexity: O(n)

The iterative algorithm performs exactly n-1 iterations for input n >= 2, resulting in linear time complexity.

### Space Complexity: O(1)

Only two variables (prev, curr) are used regardless of input size, resulting in constant space complexity.

## Troubleshooting

### ValueError: n must be a non-negative integer

**Cause**: Input is negative or not an integer type.

**Solution**: Ensure input is a non-negative integer:
```python
# Incorrect
fibonacci(-5)      # Negative input
fibonacci(5.5)      # Float input
fibonacci("5")      # String input

# Correct
fibonacci(5)        # Positive integer
fibonacci(0)        # Zero is valid
```

### Import Error: No module named 'fibonacci'

**Cause**: The fibonacci module is not in the Python path.

**Solution**: Ensure you're running from the project root directory:
```bash
cd /path/to/fibonacci-calculator
python3 -c "from fibonacci import fibonacci; print(fibonacci(10))"
```

### Test Failures

**Cause**: Dependencies not installed or Python version mismatch.

**Solution**: Verify Python version and install dependencies:
```bash
python3 --version  # Should be 3.12 or higher
pip install -r requirements.txt
pytest tests/ -v
```

## Project Structure

```
fibonacci-calculator/
├── fibonacci.py          # Main implementation
├── tests/
│   └── test_fibonacci.py # Unit and integration tests
├── requirements.