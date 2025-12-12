# Quick Start Guide

This guide will help you get started with the Python Performance Benchmarking Suite.

## Installation

1. **Install the benchmarking dependencies:**

```bash
cd benchmarks
pip install -r requirements.txt
```

Note: If you encounter issues installing PyTorch, you can skip it and run benchmarks without the PyTorch category.

## Running Your First Benchmark

### Option 1: Run All Benchmarks

```bash
python benchmarks/run_benchmarks.py
```

This will run all benchmark categories and save results to `benchmark_results/`.

### Option 2: Run Specific Categories

```bash
# Run only NumPy benchmarks
python benchmarks/run_benchmarks.py --categories numpy

# Run multiple categories
python benchmarks/run_benchmarks.py --categories numpy memory async
```

### Option 3: Run Individual Tests

```bash
# Run a specific test
cd /path/to/repository
python -m pytest benchmarks/numpy/test_array_operations.py::TestArrayCreation --benchmark-only --no-cov -v

# Run all NumPy tests
python -m pytest benchmarks/numpy/ --benchmark-only --no-cov -v
```

## Understanding the Output

After running benchmarks, you'll see output like:

```
-------------------------------------------------------- benchmark: 5 tests -------------------------------------------------------
Name (time in us)              Min       Max      Mean   StdDev    Median     IQR  Outliers  OPS (Kops/s)  Rounds  Iterations
------------------------------------------------------------------------------------------------------------------------------
test_benchmark_array_zeros    102.80    554.47   139.68   10.11    137.62   8.87  3420;1587        7.16   40823           1
```

Key metrics:
- **Min/Max**: Fastest and slowest execution times
- **Mean**: Average execution time
- **Median**: Middle value (less affected by outliers)
- **StdDev**: Standard deviation (consistency of results)
- **OPS**: Operations per second (higher is better)

## Analyzing Results

### 1. View Summary

The run_benchmarks.py script automatically generates a summary showing:
- Total benchmarks run
- Category-wise statistics
- Top 5 slowest tests per category

### 2. Compare Python Versions

```bash
# Run benchmarks with Python 3.11
python3.11 benchmarks/run_benchmarks.py --output-dir results/

# Run benchmarks with Python 3.12
python3.12 benchmarks/run_benchmarks.py --output-dir results/

# Compare the results
python benchmarks/utils/compare_results.py results/benchmarks_py311*.json results/benchmarks_py312*.json
```

### 3. Profile Memory Usage

```bash
# Profile a specific operation
python benchmarks/utils/profile_memory.py
```

## Common Use Cases

### Test Array Operations Performance

```bash
python -m pytest benchmarks/numpy/test_array_operations.py --benchmark-only --no-cov -v
```

### Test Async Performance

```bash
python -m pytest benchmarks/async/test_async_operations.py --benchmark-only --no-cov -v
```

### Test Memory Management

```bash
python -m pytest benchmarks/memory/test_memory_operations.py --benchmark-only --no-cov -v
```

### Test Import/Startup Time

```bash
python -m pytest benchmarks/startup/test_startup_operations.py --benchmark-only --no-cov -v
```

## Tips

1. **Warm-up runs**: The benchmark framework automatically performs warm-up runs to ensure fair measurements.

2. **Minimize system load**: For most accurate results, close other applications and run benchmarks when the system is idle.

3. **Multiple runs**: Run benchmarks multiple times to account for system variability:
   ```bash
   for i in {1..3}; do
     python benchmarks/run_benchmarks.py --output-dir results/run_$i
   done
   ```

4. **Focus on relative changes**: When comparing Python versions, focus on relative performance changes rather than absolute values.

## Troubleshooting

### PyTorch Not Available

If PyTorch is not installed, the PyTorch benchmarks will be skipped automatically. To install PyTorch:

```bash
# CPU version
pip install torch --index-url https://download.pytorch.org/whl/cpu

# CUDA version (if you have NVIDIA GPU)
pip install torch
```

### Coverage Errors

If you see coverage-related errors, make sure to use the `--no-cov` flag:

```bash
python -m pytest benchmarks/ --benchmark-only --no-cov -v
```

### Slow Benchmarks

Some benchmarks (especially GC and complex operations) can take a long time. You can:
- Skip slow tests: `pytest -m "not slow"`
- Reduce min-rounds: `pytest --benchmark-min-rounds=3`
- Focus on specific categories

## Next Steps

- Read the full [README.md](README.md) for detailed information
- Explore [benchmark categories](README.md#benchmark-categories)
- Learn about [comparing Python versions](README.md#comparing-python-versions)
- Check out the [example comparison script](compare_versions.sh)
