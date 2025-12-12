#!/usr/bin/env python3
"""Memory profiling utilities for detailed memory analysis."""

import gc
import tracemalloc
from collections.abc import Callable
from typing import Any


def profile_memory(func: Callable, *args, **kwargs) -> tuple[Any, dict]:
    """
    Profile memory usage of a function.

    Returns:
        Tuple of (function result, memory statistics dict)
    """
    # Force garbage collection before profiling
    gc.collect()

    # Start tracing
    tracemalloc.start()

    # Get baseline
    baseline = tracemalloc.take_snapshot()

    # Run function
    result = func(*args, **kwargs)

    # Get final memory state
    final = tracemalloc.take_snapshot()

    # Calculate statistics
    stats = {
        "current_mb": tracemalloc.get_traced_memory()[0] / 1024 / 1024,
        "peak_mb": tracemalloc.get_traced_memory()[1] / 1024 / 1024,
    }

    # Get top memory allocations
    top_stats = final.compare_to(baseline, "lineno")

    stats["top_allocations"] = [
        {
            "file": (
                stat.traceback.format()[0]
                if stat.traceback and stat.traceback.format()
                else "unknown"
            ),
            "size_mb": stat.size / 1024 / 1024,
            "count": stat.count,
        }
        for stat in top_stats[:10]
    ]

    # Stop tracing
    tracemalloc.stop()

    return result, stats


def analyze_gc_behavior(func: Callable, iterations: int = 100) -> dict:
    """
    Analyze garbage collection behavior during function execution.

    Returns:
        Dictionary with GC statistics
    """
    # Get initial GC stats
    gc.collect()
    initial_counts = gc.get_count()
    initial_stats = gc.get_stats()

    # Run function multiple times
    for _ in range(iterations):
        func()

    # Force collection and get final stats
    collected = gc.collect()
    final_counts = gc.get_count()
    final_stats = gc.get_stats()

    return {
        "collections": collected,
        "initial_counts": initial_counts,
        "final_counts": final_counts,
        "generation_stats": final_stats,
    }


def compare_memory_overhead(
    func1: Callable, func2: Callable, iterations: int = 100
) -> None:
    """Compare memory overhead of two functions."""

    print(f"\nComparing memory usage over {iterations} iterations...\n")

    # Profile first function
    def run_func1():
        for _ in range(iterations):
            func1()

    _, stats1 = profile_memory(run_func1)

    # Profile second function
    def run_func2():
        for _ in range(iterations):
            func2()

    _, stats2 = profile_memory(run_func2)

    # Display results
    print("Function 1:")
    print(f"  Current memory: {stats1['current_mb']:.2f} MB")
    print(f"  Peak memory: {stats1['peak_mb']:.2f} MB")

    print("\nFunction 2:")
    print(f"  Current memory: {stats2['current_mb']:.2f} MB")
    print(f"  Peak memory: {stats2['peak_mb']:.2f} MB")

    # Calculate difference
    diff_current = stats2["current_mb"] - stats1["current_mb"]
    diff_peak = stats2["peak_mb"] - stats1["peak_mb"]

    if stats1["current_mb"] > 0:
        diff_current_pct = diff_current / stats1["current_mb"] * 100
    else:
        diff_current_pct = 0

    if stats1["peak_mb"] > 0:
        diff_peak_pct = diff_peak / stats1["peak_mb"] * 100
    else:
        diff_peak_pct = 0

    print("\nDifference (Function 2 - Function 1):")
    print(f"  Current: {diff_current:+.2f} MB ({diff_current_pct:+.1f}%)")
    print(f"  Peak: {diff_peak:+.2f} MB ({diff_peak_pct:+.1f}%)")


def print_memory_snapshot():
    """Print current memory snapshot."""
    gc.collect()

    print("\nMemory Snapshot:")
    print("-" * 60)

    # Object counts by type
    type_counts = {}
    for obj in gc.get_objects():
        obj_type = type(obj).__name__
        type_counts[obj_type] = type_counts.get(obj_type, 0) + 1

    # Sort by count
    sorted_types = sorted(type_counts.items(), key=lambda x: x[1], reverse=True)

    print("\nTop 20 object types by count:")
    for obj_type, count in sorted_types[:20]:
        print(f"  {obj_type:<30} {count:>10,}")

    # GC statistics
    print("\nGarbage Collection Stats:")
    print(f"  Generation counts: {gc.get_count()}")
    print(f"  GC enabled: {gc.isenabled()}")
    print(f"  GC thresholds: {gc.get_threshold()}")


if __name__ == "__main__":
    print("Memory Profiling Utilities")
    print("=" * 60)

    # Example usage
    def example_memory_heavy():
        """Example memory-intensive function."""
        data = [list(range(1000)) for _ in range(100)]
        return sum(sum(row) for row in data)

    print("\nProfiling example function...")
    result, stats = profile_memory(example_memory_heavy)

    print(f"\nResult: {result}")
    print(f"Current memory: {stats['current_mb']:.2f} MB")
    print(f"Peak memory: {stats['peak_mb']:.2f} MB")

    print("\nTop allocations:")
    for alloc in stats["top_allocations"][:5]:
        print(f"  {alloc['size_mb']:.4f} MB - {alloc['count']} allocations")

    # Current snapshot
    print_memory_snapshot()
