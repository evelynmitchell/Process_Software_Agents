# Fibonacci Implementation - Design Documentation

## Overview

This document provides comprehensive design documentation for the Fibonacci implementation, detailing the architecture, component responsibilities, algorithm explanation, and design decisions.

**Task ID:** TSP-FIB-001  
**Semantic Units:** SU-001, SU-002, SU-003  
**Components:** FibonacciValidator, FibonacciCalculator, FibonacciFunction  
**Language:** Python 3.12  
**Last Updated:** 2025-11-22

---

## Architecture Overview

The Fibonacci implementation follows a simple, modular architecture with three logical components working in concert:

1. **FibonacciValidator (SU-001):** Handles input validation and type checking, ensuring only valid non-negative integers are processed
2. **FibonacciCalculator (SU-002):** Implements the core iterative Fibonacci algorithm with optimal time and space complexity
3. **FibonacciFunction (SU-003):** Serves as the public API that orchestrates validation and calculation with comprehensive documentation

This design ensures:
- **Separation of Concerns:** Each component has a single, well-defined responsibility
- **Testability:** Components can be tested independently
- **Maintainability:** Clear boundaries between validation, calculation, and orchestration
- **Reusability:** Components can be used independently if needed
- **No External Dependencies:** Pure Python standard library implementation

---

## Component Specifications

### Component 1: FibonacciValidator (SU-001)

**Responsibility:** Validates input parameters and enforces type hints for the Fibonacci function

**Complexity:** O(1) - Constant time validation

#### Interface

```python
def validate_input(n: int) -> bool
```

**Parameters:**
- `n` (int): The input value to validate

**Returns:**
- `bool`: True if input is valid

**Raises:**
- `ValueError`: If n is negative or not an integer type

**Description:**
Validates that input n is a non-negative integer. Raises ValueError if the input fails validation.

#### Implementation Notes

- Check if `n < 0` and raise `ValueError` with message: `"n must be a non-negative integer"`
- Use `isinstance(n, int)` to verify type (rejects float, string, and other numeric types)
- Do not accept float or other numeric types, even if they represent whole numbers
- This validation occurs before any calculation to fail fast
- Return `True` only if validation passes

#### Validation Logic

```
1. Check isinstance(n, int) → if False, raise ValueError
2. Check n >= 0 → if False, raise ValueError
3. Return True
```

---

### Component 2: FibonacciCalculator (SU-002)

**Responsibility:** Implements iterative Fibonacci calculation with proper edge case handling

**Complexity:** O(n) time, O(1) space

#### Interfaces

**Interface 1: calculate**
```python
def calculate(n: int) -> int
```

**Parameters:**
- `n` (int): The position in the Fibonacci sequence (assumed valid)

**Returns:**
- `int`: The nth Fibonacci number

**Description:**
Calculate the nth Fibonacci number using an iterative approach. Assumes input has been validated.

**Interface 2: handle_base_cases**
```python
def handle_base_cases(n: int) -> int | None
```

**Parameters:**
- `n` (int): The position in the Fibonacci sequence

**Returns:**
- `int`: Fibonacci value for base cases (0 or 1)
- `None`: For non-base cases

**Description:**
Return Fibonacci value for base cases (n=0 or n=1), return None for other cases.

#### Implementation Notes

**Iterative Algorithm:**
1. For n=0, return 0 immediately (base case)
2. For n=1, return 1 immediately (base case)
3. For n≥2:
   - Initialize two variables: `prev = 0`, `curr = 1`
   - Loop from 2 to n (inclusive), n-1 iterations total
   - In each iteration:
     - `temp = curr`
     - `curr = prev + curr`
     - `prev = temp`
   - Return `curr` after loop completes

**Why Iterative Over Recursive:**
- Avoids recursion overhead and function call stack
- Prevents stack overflow for large n values
- O(1) space complexity vs O(n) for recursive approach
- Significantly faster execution for large n

**Example Trace for n=5:**
```
Initial: prev=0, curr=1
Iteration 1: temp=1, curr=0+1=1, prev=1
Iteration 2: temp=1, curr=1+1=2, prev=1
Iteration 3: temp=2, curr=1+2=3, prev=2
Iteration 4: temp=3, curr=2+3=5, prev=3
Return: 5
```

---

### Component 3: FibonacciFunction (SU-003)

**Responsibility:** Public API function that orchestrates validation, calculation, and documentation

**Complexity:** O(n) - Dominated by calculation component

**Dependencies:**
- FibonacciValidator
- FibonacciCalculator

#### Interface

```python
def fibonacci(n: int) -> int
```

**Parameters:**
- `n` (int): The position in the Fibonacci sequence (0-indexed)
  - Must be a non-negative integer
  - Negative values raise ValueError

**Returns:**
- `int`: The nth Fibonacci number

**Raises:**
- `ValueError`: If n is negative or not an integer type

#### Implementation Flow

```
1. Call FibonacciValidator.validate_input(n)
   ↓ (raises ValueError if invalid)
2. Call FibonacciCalculator.calculate(n)
   ↓
3. Return result
```

#### Docstring Specification

The function must include a comprehensive docstring with the following sections:

**1. One-line Summary:**
"Calculate the nth Fibonacci number using an iterative approach."

**2. Extended Description:**
Explain the Fibonacci sequence definition, its mathematical properties, and why the iterative approach is used.

**3. Args Section:**
Document the `n` parameter with:
- Type: int
- Constraints: Must be non-negative (n ≥ 0)
- Description: Position in the Fibonacci sequence

**4. Returns Section:**
Document the return value:
- Type: int
- Description: The nth Fibonacci number

**5. Raises Section:**
Document exceptions:
- ValueError: When n is negative or not an integer type

**6. Examples Section:**
Include at least 5 usage examples:
- `fibonacci(0)` → 0
- `fibonacci(1)` → 1
- `fibonacci(2)` → 1
- `fibonacci(5)` → 5
- `fibonacci(10)` → 55

**Docstring Style:**
- Use triple-quoted strings (""")
- Follow Google or NumPy style conventions
- Include clear formatting with proper indentation
- Make examples executable and accurate

---

## Algorithm Explanation

### Fibonacci Sequence Definition

The Fibonacci sequence is defined as:
- F(0) = 0
- F(1) = 1
- F(n) = F(n-1) + F(n-2) for n ≥ 2

This produces the sequence: 0, 1, 1, 2, 3, 5, 8, 13, 21, 34, 55, ...

### Iterative Approach

The iterative approach maintains two variables representing consecutive Fibonacci numbers and updates them in each iteration:

```
Algorithm: Iterative Fibonacci
Input: n (non-negative integer)
Output: F(n)

if n == 0:
    return 0
if n == 1:
    return 1

prev = 0
curr = 1
for i from 2 to n:
    next = prev + curr
    prev = curr
    curr = next

return curr
```

### Complexity Analysis

**Time Complexity:** O(n)
- Single loop from 2 to n
- Each iteration performs constant-time operations
- Total iterations: n-1

**Space Complexity:** O(1)
- Only two variables (prev, curr) used
- No additional data structures