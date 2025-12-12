#!/usr/bin/env python3
"""Compare benchmark results across different Python versions or runs."""

import json
import sys
from pathlib import Path
from typing import Any


def load_benchmark_results(filepath: str) -> dict[str, Any]:
    """Load benchmark results from JSON file."""
    with open(filepath) as f:
        return json.load(f)


def extract_benchmark_stats(data: dict[str, Any]) -> dict[str, dict[str, float]]:
    """Extract benchmark statistics from results."""
    benchmarks = {}

    for benchmark in data.get("benchmarks", []):
        name = benchmark.get("name", "")
        stats = benchmark.get("stats", {})

        benchmarks[name] = {
            "min": stats.get("min", 0),
            "max": stats.get("max", 0),
            "mean": stats.get("mean", 0),
            "median": stats.get("median", 0),
            "stddev": stats.get("stddev", 0),
            "rounds": stats.get("rounds", 0),
            "iterations": stats.get("iterations", 0),
        }

    return benchmarks


def compare_benchmarks(
    baseline: dict[str, dict[str, float]],
    comparison: dict[str, dict[str, float]],
    baseline_name: str,
    comparison_name: str,
) -> None:
    """Compare two sets of benchmark results."""

    print(f"\n{'=' * 80}")
    print(f"Benchmark Comparison: {baseline_name} vs {comparison_name}")
    print(f"{'=' * 80}\n")

    # Find common benchmarks
    common_benchmarks = set(baseline.keys()) & set(comparison.keys())

    if not common_benchmarks:
        print("No common benchmarks found!")
        return

    improvements = []
    regressions = []

    print(
        f"{'Benchmark':<60} {'Baseline (ms)':<15} {'Comparison (ms)':<15} {'Change':>10}"
    )
    print("-" * 105)

    for name in sorted(common_benchmarks):
        baseline_mean = baseline[name]["mean"] * 1000  # Convert to ms
        comparison_mean = comparison[name]["mean"] * 1000

        if baseline_mean > 0:
            change_pct = ((comparison_mean - baseline_mean) / baseline_mean) * 100
        else:
            change_pct = 0

        change_str = f"{change_pct:+.2f}%"

        # Truncate long names
        display_name = name if len(name) <= 58 else name[:55] + "..."

        print(
            f"{display_name:<60} {baseline_mean:>13.4f}  {comparison_mean:>13.4f}  {change_str:>10}"
        )

        if change_pct < -5:  # More than 5% improvement
            improvements.append((name, change_pct))
        elif change_pct > 5:  # More than 5% regression
            regressions.append((name, change_pct))

    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)

    if improvements:
        print(f"\n✅ Top Improvements (faster in {comparison_name}):")
        for name, change in sorted(improvements, key=lambda x: x[1])[:10]:
            print(f"  {change:+.2f}% - {name}")

    if regressions:
        print(f"\n⚠️  Top Regressions (slower in {comparison_name}):")
        for name, change in sorted(regressions, key=lambda x: x[1], reverse=True)[:10]:
            print(f"  {change:+.2f}% - {name}")

    total_benchmarks = len(common_benchmarks)
    improved = len(improvements)
    regressed = len(regressions)
    neutral = total_benchmarks - improved - regressed

    print(f"\nTotal benchmarks: {total_benchmarks}")
    print(f"  Improved: {improved} ({improved / total_benchmarks * 100:.1f}%)")
    print(f"  Regressed: {regressed} ({regressed / total_benchmarks * 100:.1f}%)")
    print(f"  Neutral: {neutral} ({neutral / total_benchmarks * 100:.1f}%)")


def analyze_by_category(benchmarks: dict[str, dict[str, float]]) -> None:
    """Analyze benchmarks by category."""
    categories = {
        "numpy": [],
        "pytorch": [],
        "async": [],
        "memory": [],
        "startup": [],
        "other": [],
    }

    for name, stats in benchmarks.items():
        categorized = False
        for category, cat_list in categories.items():
            if category in name.lower():
                cat_list.append(stats["mean"])
                categorized = True
                break
        if not categorized:
            categories["other"].append(stats["mean"])

    print("\nBenchmark Statistics by Category:")
    print("-" * 60)

    for category, times in categories.items():
        if times:
            avg_time = sum(times) / len(times) * 1000  # Convert to ms
            print(
                f"{category.capitalize():<15} - {len(times):>3} tests, avg: {avg_time:>10.4f} ms"
            )


def main():
    """Main entry point."""
    if len(sys.argv) < 3:
        print(
            "Usage: python compare_results.py <baseline.json> <comparison.json> [<comparison2.json> ...]"
        )
        print("\nExample:")
        print(
            "  python compare_results.py results_311.json results_312.json results_313.json"
        )
        sys.exit(1)

    baseline_path = sys.argv[1]
    comparison_paths = sys.argv[2:]

    if not Path(baseline_path).exists():
        print(f"Error: Baseline file '{baseline_path}' not found")
        sys.exit(1)

    print(f"Loading baseline results from: {baseline_path}")
    baseline_data = load_benchmark_results(baseline_path)
    baseline_stats = extract_benchmark_stats(baseline_data)

    baseline_name = Path(baseline_path).stem

    # Analyze baseline
    print(f"\nBaseline: {baseline_name}")
    analyze_by_category(baseline_stats)

    # Compare with each comparison file
    for comparison_path in comparison_paths:
        if not Path(comparison_path).exists():
            print(f"Warning: Comparison file '{comparison_path}' not found, skipping")
            continue

        print(f"\nLoading comparison results from: {comparison_path}")
        comparison_data = load_benchmark_results(comparison_path)
        comparison_stats = extract_benchmark_stats(comparison_data)
        comparison_name = Path(comparison_path).stem

        compare_benchmarks(
            baseline_stats, comparison_stats, baseline_name, comparison_name
        )


if __name__ == "__main__":
    main()
