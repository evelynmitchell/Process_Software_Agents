# Python Performance Benchmarking Suite

A comprehensive benchmarking suite for testing Python performance improvements across different workloads.

## Overview

This benchmarking suite is designed to help analyze Python speed improvements in the latest versions, with a focus on:
- **Memory Management**: How Python handles memory allocation, garbage collection, and object lifecycle
- **Process Startup/Teardown**: Import times, module loading, subprocess overhead
- **Computational Performance**: CPU-bound operations with PyTorch and NumPy
- **Async Performance**: I/O-bound and concurrent operations

## Directory Structure

```
benchmarks/
├── pytorch/        # PyTorch tensor operations, model training/inference
├── numpy/          # NumPy array operations, linear algebra
├── async/          # Asyncio operations, concurrent tasks
├── memory/         # Memory profiling and GC analysis
├── startup/        # Process startup, import time, module loading
├── utils/          # Shared utilities and helpers
└── README.md       # This file
```

## Installation

Install the required dependencies:

```bash
pip install -e ".[dev]"
pip install torch numpy pytest-benchmark memory-profiler psutil
```

## Running Benchmarks

### Run all benchmarks
```bash
pytest benchmarks/ --benchmark-only
```

### Run specific category
```bash
pytest benchmarks/numpy/ --benchmark-only
pytest benchmarks/pytorch/ --benchmark-only
pytest benchmarks/async/ --benchmark-only
```

### Generate detailed reports
```bash
pytest benchmarks/ --benchmark-only --benchmark-json=results.json
```

### Compare results
```bash
pytest benchmarks/ --benchmark-only --benchmark-compare=baseline
```

## Benchmark Categories

### 1. NumPy Benchmarks (`numpy/`)
- Array creation and manipulation
- Linear algebra operations (matrix multiplication, eigenvalues)
- Broadcasting and vectorization
- Complex mathematical operations
- Memory access patterns

### 2. PyTorch Benchmarks (`pytorch/`)
- Tensor operations (creation, manipulation, slicing)
- Neural network forward/backward passes
- Model training loops
- GPU vs CPU performance (if available)
- Gradient computation

### 3. Async Benchmarks (`async/`)
- Concurrent I/O operations
- Task scheduling and event loop overhead
- Mixed CPU/IO workloads
- Context switching performance

### 4. Memory Benchmarks (`memory/`)
- Object allocation patterns
- Garbage collection timing
- Reference counting overhead
- Memory pooling effectiveness
- Peak memory usage

### 5. Startup Benchmarks (`startup/`)
- Import time for common modules
- Module initialization overhead
- Subprocess creation and communication
- Dynamic loading performance

## Analysis Guide

### Memory Management Analysis

The benchmarks help identify improvements in:
- **Allocation Speed**: How quickly Python can allocate new objects
- **GC Efficiency**: Time spent in garbage collection cycles
- **Memory Overhead**: Per-object memory overhead
- **Reference Counting**: Performance of reference count operations

To focus on memory:
```bash
pytest benchmarks/memory/ --benchmark-only -v
python benchmarks/memory/profile_memory.py
```

### Process Startup Analysis

The benchmarks help identify improvements in:
- **Import Time**: How long it takes to import modules
- **Module Caching**: Effectiveness of .pyc files and import caching
- **Subprocess Overhead**: Cost of creating new Python processes
- **Lazy Loading**: Benefits of deferred imports

To focus on startup:
```bash
pytest benchmarks/startup/ --benchmark-only -v
python -X importtime -c "import numpy" 2>&1 | grep numpy
```

## Comparing Python Versions

### Setup Multiple Python Versions
```bash
# Using pyenv
pyenv install 3.11.8
pyenv install 3.12.3
pyenv install 3.13.0

# Create virtual environments
python3.11 -m venv venv311
python3.12 -m venv venv312
python3.13 -m venv venv313
```

### Run Benchmarks Across Versions
```bash
# Python 3.11
source venv311/bin/activate
pip install -e ".[dev]" torch numpy pytest-benchmark
pytest benchmarks/ --benchmark-only --benchmark-json=results_311.json
deactivate

# Python 3.12
source venv312/bin/activate
pip install -e ".[dev]" torch numpy pytest-benchmark
pytest benchmarks/ --benchmark-only --benchmark-json=results_312.json
deactivate

# Python 3.13
source venv313/bin/activate
pip install -e ".[dev]" torch numpy pytest-benchmark
pytest benchmarks/ --benchmark-only --benchmark-json=results_313.json
deactivate
```

### Analyze Results
```bash
python benchmarks/utils/compare_results.py results_311.json results_312.json results_313.json
```

## Expected Improvements in Recent Python Versions

### Python 3.11
- 10-60% faster than 3.10 (PEP 659 - Specializing Adaptive Interpreter)
- Faster function calls
- Better error messages
- Optimized frame stack

### Python 3.12
- Per-interpreter GIL (experimental)
- Improved error messages
- f-string optimizations
- Comprehension inlining

### Python 3.13
- JIT compilation (experimental)
- Free-threaded Python (no-GIL mode, PEP 703)
- Better immortal objects
- Improved memory management

## Reporting

After running benchmarks, you'll get:
1. **Timing statistics**: min, max, mean, stddev for each benchmark
2. **Memory profiles**: Peak memory usage and allocation patterns
3. **Comparative analysis**: Version-to-version improvements
4. **Breakdown**: Memory vs startup vs computation improvements

## Contributing

When adding new benchmarks:
1. Use descriptive names: `test_benchmark_<category>_<operation>`
2. Add docstrings explaining what is being measured
3. Use appropriate benchmark rounds (more for fast operations)
4. Consider both warm and cold cache scenarios
5. Document expected performance characteristics

## References

- [Python Performance](https://docs.python.org/3/whatsnew/3.12.html#optimizations)
- [pytest-benchmark](https://pytest-benchmark.readthedocs.io/)
- [memory-profiler](https://pypi.org/project/memory-profiler/)
- [PEP 659 - Specializing Adaptive Interpreter](https://peps.python.org/pep-0659/)
- [PEP 703 - Making the GIL Optional](https://peps.python.org/pep-0703/)
