#!/usr/bin/env python3
"""
Comprehensive benchmark runner with analysis.

This script runs all benchmarks and generates detailed reports including:
- Performance metrics (mean, min, max, stddev)
- Memory usage analysis
- Comparison across categories
- Visual plots (if matplotlib available)
"""

import argparse
import json
import platform
import subprocess
import sys
from datetime import datetime
from pathlib import Path


def get_python_info():
    """Get Python version and implementation information."""
    return {
        "version": sys.version,
        "version_info": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        "implementation": platform.python_implementation(),
        "platform": platform.platform(),
        "processor": platform.processor(),
    }


def run_benchmarks(categories=None, output_dir=None, compare_baseline=None):
    """
    Run benchmarks for specified categories.

    Args:
        categories: List of category names (numpy, pytorch, async, memory, startup)
        output_dir: Directory to save results
        compare_baseline: Path to baseline JSON for comparison
    """
    if categories is None:
        categories = ["numpy", "pytorch", "async", "memory", "startup"]

    if output_dir is None:
        output_dir = Path("benchmark_results")
    else:
        output_dir = Path(output_dir)

    output_dir.mkdir(exist_ok=True)

    # Generate timestamp for this run
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    python_info = get_python_info()
    version_str = python_info["version_info"].replace(".", "")

    results_file = output_dir / f"benchmarks_py{version_str}_{timestamp}.json"

    print("=" * 80)
    print("Python Performance Benchmark Suite")
    print("=" * 80)
    print(f"\nPython: {python_info['version_info']} ({python_info['implementation']})")
    print(f"Platform: {python_info['platform']}")
    print(f"Processor: {python_info['processor']}")
    print(f"\nCategories: {', '.join(categories)}")
    print(f"Results will be saved to: {results_file}")
    print("\n" + "=" * 80 + "\n")

    # Build pytest command
    test_paths = [f"benchmarks/{cat}/" for cat in categories]

    cmd = [
        sys.executable,
        "-m",
        "pytest",
        *test_paths,
        "--benchmark-only",
        "--benchmark-json=" + str(results_file),
        "--benchmark-min-rounds=5",
        "--benchmark-warmup=on",
        "-v",
    ]

    if compare_baseline:
        cmd.append(f"--benchmark-compare={compare_baseline}")

    print(f"Running command: {' '.join(cmd)}\n")

    # Run benchmarks
    try:
        result = subprocess.run(cmd, check=True)
        print("\n" + "=" * 80)
        print("✅ Benchmarks completed successfully!")
        print("=" * 80)
        print(f"\nResults saved to: {results_file}")

        # Generate summary
        generate_summary(results_file)

        return results_file

    except subprocess.CalledProcessError as e:
        print("\n" + "=" * 80)
        print("❌ Benchmark run failed!")
        print("=" * 80)
        print(f"Error code: {e.returncode}")
        return None


def generate_summary(results_file):
    """Generate a summary report from benchmark results."""
    try:
        with open(results_file) as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"Results file not found: {results_file}")
        return

    benchmarks = data.get("benchmarks", [])

    if not benchmarks:
        print("No benchmarks found in results file")
        return

    print("\n" + "=" * 80)
    print("BENCHMARK SUMMARY")
    print("=" * 80)

    # Group by category
    categories = {}
    for bench in benchmarks:
        name = bench["name"]
        # Extract category from test path
        if "numpy" in name:
            cat = "NumPy"
        elif "pytorch" in name:
            cat = "PyTorch"
        elif "async" in name:
            cat = "Async"
        elif "memory" in name:
            cat = "Memory"
        elif "startup" in name:
            cat = "Startup"
        else:
            cat = "Other"

        if cat not in categories:
            categories[cat] = []

        categories[cat].append(bench)

    # Print summary for each category
    for cat_name, cat_benchmarks in sorted(categories.items()):
        if not cat_benchmarks:
            continue

        print(f"\n{cat_name} Benchmarks ({len(cat_benchmarks)} tests)")
        print("-" * 80)

        # Calculate statistics
        times = [b["stats"]["mean"] for b in cat_benchmarks]
        avg_time = sum(times) / len(times) * 1000  # Convert to ms
        min_time = min(times) * 1000
        max_time = max(times) * 1000

        print(f"  Average time: {avg_time:.4f} ms")
        print(f"  Min time: {min_time:.4f} ms")
        print(f"  Max time: {max_time:.4f} ms")

        # Show top 5 slowest tests
        slowest = sorted(
            cat_benchmarks, key=lambda x: x["stats"]["mean"], reverse=True
        )[:5]
        print("\n  Top 5 slowest tests:")
        for i, bench in enumerate(slowest, 1):
            mean_ms = bench["stats"]["mean"] * 1000
            test_name = bench["name"].split("::")[-1]
            print(f"    {i}. {test_name[:60]:<60} {mean_ms:>10.4f} ms")

    # Overall statistics
    if benchmarks:
        all_times = [b["stats"]["mean"] for b in benchmarks]
        total_time = sum(all_times)

        print("\n" + "=" * 80)
        print(f"Total benchmarks: {len(benchmarks)}")
        print(f"Total time: {total_time:.2f} seconds")
        print(f"Average per benchmark: {total_time / len(benchmarks) * 1000:.4f} ms")
        print("=" * 80)
    else:
        print("\n" + "=" * 80)
        print("No benchmarks found in results")
        print("=" * 80)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Run Python performance benchmarks",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run all benchmarks
  python run_benchmarks.py

  # Run specific categories
  python run_benchmarks.py --categories numpy pytorch

  # Compare with baseline
  python run_benchmarks.py --compare baseline_results.json

  # Save to custom directory
  python run_benchmarks.py --output-dir ./my_results
        """,
    )

    parser.add_argument(
        "--categories",
        nargs="+",
        choices=["numpy", "pytorch", "async", "memory", "startup", "all"],
        default=["all"],
        help="Categories to benchmark (default: all)",
    )

    parser.add_argument(
        "--output-dir",
        type=str,
        default="benchmark_results",
        help="Directory to save results (default: benchmark_results)",
    )

    parser.add_argument(
        "--compare", type=str, help="Path to baseline JSON file for comparison"
    )

    args = parser.parse_args()

    # Handle 'all' category
    if "all" in args.categories:
        categories = ["numpy", "pytorch", "async", "memory", "startup"]
    else:
        categories = args.categories

    # Run benchmarks
    results_file = run_benchmarks(
        categories=categories, output_dir=args.output_dir, compare_baseline=args.compare
    )

    if results_file:
        print(f"\n✨ Benchmark complete! Results in: {results_file}")
        print("\nTo compare with another run:")
        print(
            f"  python benchmarks/utils/compare_results.py <baseline.json> {results_file}"
        )
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
