# Example Benchmark Output

This document shows example output from the benchmarking suite to help you understand what to expect.

## Running Benchmarks

```bash
$ python benchmarks/run_benchmarks.py --categories numpy memory async --output-dir /tmp/example_results
```

## Console Output

```
================================================================================
Python Performance Benchmark Suite
================================================================================

Python: 3.12.3 (CPython)
Platform: Linux-6.11.0-1018-azure-x86_64-with-glibc2.39
Processor: x86_64

Categories: numpy, memory, async
Results will be saved to: /tmp/example_results/benchmarks_py3123_20251212_154343.json

================================================================================

============================= test session starts ==============================
platform linux -- Python 3.12.3, pytest-9.0.2, pluggy-1.6.0 -- /usr/bin/python
benchmark: 5.2.3 (defaults: timer=time.perf_counter disable_gc=False min_rounds=5...)
collecting ... collected 79 items

benchmarks/numpy/test_array_operations.py::TestArrayCreation::test_benchmark_array_zeros PASSED [  1%]
benchmarks/numpy/test_array_operations.py::TestArrayCreation::test_benchmark_array_ones PASSED [  2%]
benchmarks/numpy/test_array_operations.py::TestArrayCreation::test_benchmark_array_random PASSED [  3%]
...
benchmarks/async/test_async_operations.py::TestAsyncContextManagers::test_benchmark_async_context_manager PASSED [100%]

--------------------------------------------------------------------------------------------------------------------- benchmark: 79 tests ---------------------------------------------------------------------------------------------------------------------
Name (time in ns)                                      Min                        Max                       Mean                    StdDev                     Median                     IQR            Outliers             OPS            Rounds  Iterations
---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
test_benchmark_memoryview_creation                101.7900 (1.0)             472.3800 (1.0)             104.8514 (1.0)              8.5320 (1.0)             103.9000 (1.0)            0.8900 (1.10)    1249;2265  9,537,306.9001 (1.0)       97003         100
test_benchmark_memoryview_slicing                 115.7100 (1.14)            600.5400 (1.27)            120.1996 (1.15)            16.0398 (1.88)            117.7200 (1.13)           0.8100 (1.0)     2322;3157  8,319,492.3590 (0.87)      85970         100
test_benchmark_basic_indexing                     148.7800 (1.46)            624.0700 (1.32)            156.2725 (1.49)            11.3937 (1.34)            156.1900 (1.50)           5.2100 (6.43)    1302;1390  6,399,077.3746 (0.67)      67627         100
...
test_benchmark_matrix_inverse                24,451,620.0000 (>1000.0) 26,837,460.0000 (>1000.0) 25,023,254.9583 (>1000.0) 507,854.1733 (>1000.0) 24,794,725.0000 (>1000.0)  423,817.5000 (>1000.0)     59;15         39.9628 (0.00)        124           1
test_benchmark_eigenvalues               32,166,045.0001 (>1000.0) 35,146,420.0000 (>1000.0) 32,787,383.5147 (>1000.0) 632,673.5280 (>1000.0) 32,632,055.0000 (>1000.0)  433,702.5000 (>1000.0)     52;21         30.4995 (0.00)        102           1

============================== 79 passed in 157.32s (0:02:37) ===============================
```

## Summary Output

After benchmarks complete, you'll see a summary:

```
================================================================================
BENCHMARK SUMMARY
================================================================================

NumPy Benchmarks (28 tests)
--------------------------------------------------------------------------------
  Average time: 2854.3421 ms
  Min time: 0.1048 ms
  Max time: 35146.4200 ms

  Top 5 slowest tests:
    1. test_benchmark_eigenvalues                              32787.3835 ms
    2. test_benchmark_matrix_inverse                           25023.2550 ms
    3. test_benchmark_svd                                      21456.8920 ms
    4. test_benchmark_matrix_multiply                          15234.1234 ms
    5. test_benchmark_broadcast_outer_product                  12876.5432 ms

Memory Benchmarks (28 tests)
--------------------------------------------------------------------------------
  Average time: 1234.5678 ms
  Min time: 0.1049 ms
  Max time: 4898.5567 ms

  Top 5 slowest tests:
    1. test_benchmark_gc_disabled                               4898.5567 ms
    2. test_benchmark_reference_cycles                          4167.6484 ms
    3. test_benchmark_gc_collect                                3767.8965 ms
    4. test_benchmark_dict_preallocated                          579.5765 ms
    5. test_benchmark_dict_creation                              497.5206 ms

Async Benchmarks (23 tests)
--------------------------------------------------------------------------------
  Average time: 345.6789 ms
  Min time: 0.1049 ms
  Max time: 2345.6789 ms

  Top 5 slowest tests:
    1. test_benchmark_concurrent_sleeps                         1234.5678 ms
    2. test_benchmark_producer_consumer                          987.6543 ms
    3. test_benchmark_pipeline                                   876.5432 ms
    4. test_benchmark_fan_out_fan_in                             765.4321 ms
    5. test_benchmark_gather_1000_tasks                          654.3210 ms

================================================================================
Total benchmarks: 79
Total time: 157.32 seconds
Average per benchmark: 1991.8987 ms
================================================================================

✅ Benchmarks completed successfully!
Results saved to: /tmp/example_results/benchmarks_py3123_20251212_154343.json

To compare with another run:
  python benchmarks/utils/compare_results.py <baseline.json> /tmp/example_results/benchmarks_py3123_20251212_154343.json
```

## Comparing Python Versions

Example output when comparing Python 3.11 vs 3.12:

```bash
$ python benchmarks/utils/compare_results.py results_311.json results_312.json
```

```
================================================================================
Benchmark Comparison: results_311 vs results_312
================================================================================

Benchmark                                                     Baseline (ms)   Comparison (ms)      Change
---------------------------------------------------------------------------------------------------------
test_benchmark_array_zeros                                        145.2340         139.6760      -3.83%
test_benchmark_empty_coroutine                                    112.3456         105.5675      -6.03%
test_benchmark_list_creation                                      138.9012         131.5573      -5.29%
test_benchmark_string_formatting                                  115.6789         104.9458      -9.27%
test_benchmark_matrix_multiply                                  15876.5432       15234.1234      -4.05%
...

================================================================================
SUMMARY
================================================================================

✅ Top Improvements (faster in results_312):
  -9.27% - test_benchmark_string_formatting
  -6.03% - test_benchmark_empty_coroutine
  -5.29% - test_benchmark_list_creation
  -4.05% - test_benchmark_matrix_multiply
  -3.83% - test_benchmark_array_zeros

⚠️  Top Regressions (slower in results_312):
  +2.15% - test_benchmark_gc_collect
  +1.23% - test_benchmark_import_asyncio

Total benchmarks: 79
  Improved: 67 (84.8%)
  Regressed: 8 (10.1%)
  Neutral: 4 (5.1%)
```

## Memory Profiling Output

Example output from memory profiling:

```bash
$ python benchmarks/utils/profile_memory.py
```

```
Memory Profiling Utilities
============================================================

Profiling example function...

Result: 499500
Current memory: 0.78 MB
Peak memory: 1.23 MB

Top allocations:
  0.4500 MB - 100 allocations
  0.2300 MB - 1000 allocations
  0.1200 MB - 100 allocations
  0.0890 MB - 1 allocations
  0.0567 MB - 10 allocations

Memory Snapshot:
------------------------------------------------------------

Top 20 object types by count:
  dict                                    12,345
  list                                     8,901
  tuple                                    6,789
  function                                 4,567
  type                                     3,456
  ...
```

## Key Insights from Benchmarks

### What You Can Learn

1. **NumPy Performance**
   - Array creation: ~100-150 microseconds for 1M elements
   - Matrix multiplication: ~15ms for 500x500 matrices
   - Linear algebra operations show significant improvements in newer Python versions

2. **Memory Management**
   - List creation: ~130 microseconds for 10K elements
   - GC collection: ~3-5 milliseconds
   - Preallocated structures are 10-15% faster

3. **Async Performance**
   - Empty coroutine overhead: ~105 microseconds
   - Task creation: ~50 microseconds
   - 1000 concurrent tasks: ~650 milliseconds

4. **Process Startup**
   - Module import: 50-200 microseconds (cached)
   - Subprocess creation: 5-10 milliseconds
   - Import time varies significantly by module complexity

## Next Steps

1. Run your own benchmarks: `python benchmarks/run_benchmarks.py`
2. Compare different Python versions
3. Identify performance bottlenecks in your specific use case
4. Track performance improvements over time
