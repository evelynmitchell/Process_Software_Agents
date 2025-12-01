#!/usr/bin/env python3
"""
Simple Hello World Example - ASP Platform

This example demonstrates the full 7-agent ASP pipeline with a trivial task.

Run with:
    uv run python examples/hello_world.py

Cost: ~$0.08 - $0.15
Time: ~45 seconds
"""

from pathlib import Path

from asp.models.planning import TaskRequirements
from asp.orchestrators import TSPOrchestrator


def main():
    """Run Hello World task through ASP pipeline."""
    print("=" * 70)
    print("ASP Platform - Hello World Example")
    print("=" * 70)
    print()

    # Create task request
    task = TaskRequirements(
        task_id="HW-EXAMPLE-001",
        description="Create a Python function that prints 'Hello, World!' to stdout",
        requirements=[
            "Function should be named 'hello_world'",
            "Function should take no parameters",
            "Function should print exactly 'Hello, World!' (case-sensitive)",
            "Include a docstring explaining the function",
            "Include comprehensive unit tests",
        ],
    )

    print(f"📋 Task ID: {task.task_id}")
    print(f"📝 Description: {task.description}")
    print()
    print("Requirements:")
    for i, req in enumerate(task.requirements, 1):
        print(f"  {i}. {req}")
    print()

    # Create orchestrator
    print("🚀 Starting ASP pipeline...")
    print()

    orchestrator = TSPOrchestrator()

    # Execute full pipeline
    result = orchestrator.execute(task)

    # Display results
    print()
    print("=" * 70)
    print("✅ Pipeline completed successfully!")
    print("=" * 70)
    print()

    print("📊 Performance Summary:")
    print(
        f"   - Total Latency: {result.total_latency_ms:,} ms ({result.total_latency_ms/1000:.1f}s)"
    )
    print(f"   - Total Tokens: {result.total_tokens:,}")
    print(f"   - Total Cost: ${result.total_cost_usd:.4f}")
    print(
        f"   - Defects Found: {len(result.defects) if hasattr(result, 'defects') else 0}"
    )
    print(
        f"   - Quality Gates: {'PASS' if result.quality_gate_status == 'PASS' else 'FAIL'}"
    )
    print()

    # Show artifacts
    artifacts_dir = Path(f"artifacts/{task.task_id}")
    print(f"📁 Artifacts saved to: {artifacts_dir}/")

    if artifacts_dir.exists():
        artifacts = [
            ("plan.md", "Planning output"),
            ("design.md", "Design specification"),
            ("design_review.md", "Design review report"),
            ("generated_code/", "Implementation"),
            ("code_review.md", "Code review report"),
            ("test_results.md", "Test results"),
            ("postmortem.md", "Performance analysis"),
        ]

        for filename, description in artifacts:
            file_path = artifacts_dir / filename
            if file_path.exists():
                print(f"   ✓ {filename:25s} - {description}")
            else:
                print(f"   ✗ {filename:25s} - {description} (not found)")
    else:
        print("   ⚠️  Artifacts directory not found")

    print()
    print(f"🔍 View detailed traces at: https://cloud.langfuse.com")
    print()
    print("=" * 70)
    print("Example complete!")
    print("=" * 70)


if __name__ == "__main__":
    main()
