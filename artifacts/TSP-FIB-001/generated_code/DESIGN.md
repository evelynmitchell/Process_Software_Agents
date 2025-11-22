# Fibonacci Function Design Documentation

## Overview

This document provides detailed design documentation for the Fibonacci function implementation (Task ID: TSP-FIB-001). The design follows a three-component architecture with clear separation of concerns, comprehensive validation, and optimized algorithmic complexity.

## Architecture Overview

The Fibonacci implementation uses a modular three-component architecture:

1. **FibonacciValidator (SU-001)**: Handles input validation and type constraints
2. **FibonacciCalculator (SU-002)**: Implements the iterative Fibonacci algorithm
3. **FibonacciFunction (SU-003)**: Public API that orchestrates validation and calculation

This architecture ensures:
- **Separation of Concerns**: Each component has a single, well-defined responsibility
- **Testability**: Components can be tested independently
- **Maintainability**: Clear boundaries make the code easy to understand and modify
- **Reusability**: Components can be used independently if needed

## Technology Stack

- **Language**: Python 3.12
- **Type Hints**: Python typing module (built-in)
- **Docstring Format**: Google-style docstring
- **Dependencies**: None (pure Python standard library only)

## Component Design

### Component 1: FibonacciValidator (SU-001)

**Responsibility**: Validates input parameters and enforces type constraints for the Fibonacci function.

**Semantic Unit ID**: SU-001

**Component ID**: FibonacciValidator

**Complexity**: O(1) - constant time validation

#### Interface

```python
def validate_input(n: int) -> bool
```

**Parameters**:
- `n` (int): The input value to validate

**Returns**:
- `bool`: True if validation passes

**Raises**:
- `ValueError`: If n is not a non-negative integer

#### Implementation Details

The validator performs the following checks:

1. **Type Check**: Verify that `n` is an integer type using `isinstance(n, int)`
2. **Boolean Exclusion**: Exclude boolean values using `not isinstance(n, bool)` (since bool is a subclass of int in Python)
3. **Non-Negative Check**: Verify that `n >= 0`

If any check fails, the validator raises a `ValueError` with the message: `"n must be a non-negative integer"`

#### Validation Logic

```
Input: n
├─ Is n an integer type? (isinstance(n, int) and not isinstance(n, bool))
│  └─ No → Raise ValueError
├─ Is n >= 0?
│  └─ No → Raise ValueError
└─ Yes → Return True
```

#### Design Decisions

- **Boolean Exclusion**: Although `bool` is a subclass of `int` in Python, we explicitly exclude it because `True` and `False` are not meaningful Fibonacci indices
- **Early Validation**: Validation occurs before any computation, preventing invalid states
- **Clear Error Messages**: The error message explicitly states the constraint ("non-negative integer")

### Component 2: FibonacciCalculator (SU-002)

**Responsibility**: Computes the nth Fibonacci number using an iterative approach with edge case handling.

**Semantic Unit ID**: SU-002

**Component ID**: FibonacciCalculator

**Complexity**: O(n) time, O(1) space

#### Interface

```python
def calculate(n: int) -> int
```

**Parameters**:
- `n` (int): A non-negative integer (assumed to be pre-validated)

**Returns**:
- `int`: The nth Fibonacci number

#### Algorithm

The iterative Fibonacci algorithm handles three logical branches:

**Branch 1: Base Case n = 0**
```
Return 0
```

**Branch 2: Base Case n = 1**
```
Return 1
```

**Branch 3: Recursive Case n >= 2**
```
Initialize: prev = 0, curr = 1
Loop from i = 2 to n (inclusive):
    next = prev + curr
    prev = curr
    curr = next
Return curr
```

#### Complexity Analysis

**Time Complexity**: O(n)
- The algorithm performs exactly n-1 iterations for input n >= 2
- Each iteration performs constant-time operations (addition, assignment)
- Total operations: O(n)

**Space Complexity**: O(1)
- Only three variables are used: `prev`, `curr`, `next`
- No data structures that grow with input size
- Constant memory regardless of n

#### Example Execution

For `n = 5`:

```
Initial: prev = 0, curr = 1

Iteration 1 (i=2): next = 0+1 = 1, prev = 1, curr = 1
Iteration 2 (i=3): next = 1+1 = 2, prev = 1, curr = 2
Iteration 3 (i=4): next = 1+2 = 3, prev = 2, curr = 3
Iteration 4 (i=5): next = 2+3 = 5, prev = 3, curr = 5

Return: 5
```

#### Design Decisions

- **Iterative Approach**: Chosen over recursive to avoid stack overflow for large n and to achieve O(1) space complexity
- **Integer Arithmetic Only**: Uses only integer operations, no floating-point arithmetic
- **Edge Case Handling**: Explicitly handles n=0 and n=1 cases for clarity and efficiency
- **No Memoization**: Single function calls don't benefit from caching; memoization would add complexity without benefit

### Component 3: FibonacciFunction (SU-003)

**Responsibility**: Public API function that orchestrates validation and calculation with comprehensive documentation.

**Semantic Unit ID**: SU-003

**Component ID**: FibonacciFunction

**Complexity**: O(n) - dominated by calculation component

#### Interface

```python
def fibonacci(n: int) -> int
```

**Parameters**:
- `n` (int): The index of the Fibonacci number to calculate (must be non-negative)

**Returns**:
- `int`: The nth Fibonacci number

**Raises**:
- `ValueError`: If n is negative or not an integer

#### Orchestration Flow

```
Input: n
├─ Call FibonacciValidator.validate_input(n)
│  └─ Raises ValueError if invalid
├─ Call FibonacciCalculator.calculate(n)
│  └─ Returns the nth Fibonacci number
└─ Return result
```

#### Documentation

The function includes comprehensive Google-style docstring with:

1. **One-line Summary**: Brief description of functionality
2. **Extended Description**: Explanation of the Fibonacci sequence and algorithm approach
3. **Args Section**: Parameter documentation with type and constraints
4. **Returns Section**: Return type and value description
5. **Raises Section**: Exception documentation for ValueError
6. **Examples Section**: At least 5 usage examples demonstrating various inputs

#### Design Decisions

- **Separation of Concerns**: Delegates validation to FibonacciValidator and calculation to FibonacciCalculator
- **Comprehensive Documentation**: Extensive docstring ensures users understand constraints and usage
- **Type Hints**: Full type hints for IDE support and static type checking
- **Error Propagation**: Allows ValueError from validator to propagate to caller

## Algorithm Complexity Analysis

### Time Complexity: O(n)

The iterative algorithm performs exactly n-1 iterations for input n >= 2:

```
T(n) = {
    O(1)  if n = 0 or n = 1
    O(n)  if n >= 2
}
```

Overall: **O(n)** - linear time complexity

### Space Complexity: O(1)

The algorithm uses only three variables regardless of input size:

```
S(n) = O(1)
```

Variables: `prev`, `curr`, `next` - constant space

### Comparison with Alternatives

| Approach | Time | Space | Notes |
|----------|------|-------|-------|
| Recursive | O(2^n) | O(n) | Exponential time, stack overflow risk |
| Recursive + Memoization | O(n) | O(n) | Linear time but uses O(n) space |
| Iterative (Our Choice) | O(n) | O(1) | Optimal time and space |
| Matrix