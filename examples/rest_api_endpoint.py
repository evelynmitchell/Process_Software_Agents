#!/usr/bin/env python3
"""
REST API Endpoint Example - ASP Platform

This example demonstrates ASP with a medium-complexity task:
creating a FastAPI endpoint with validation, error handling, and tests.

Run with:
    uv run python examples/rest_api_endpoint.py

Cost: ~$0.25 - $0.50
Time: ~2 minutes
"""

from asp.orchestrators import TSPOrchestrator
from asp.models.planning import TaskRequirements
from pathlib import Path


def main():
    """Run REST API endpoint task through ASP pipeline."""
    print("=" * 70)
    print("ASP Platform - REST API Endpoint Example")
    print("=" * 70)
    print()

    # Create task request
    task = TaskRequirements(
        task_id="API-EXAMPLE-001",
        description="Create a FastAPI endpoint for user registration with validation and error handling",
        requirements=[
            "POST /api/users endpoint that accepts JSON",
            "Request body: username (str), email (str), password (str)",
            "Validate email format using regex",
            "Validate password strength (min 8 chars, 1 uppercase, 1 number)",
            "Hash password with bcrypt before storage",
            "Return 201 Created with user ID on success",
            "Return 400 Bad Request for validation errors with detailed messages",
            "Include SQLAlchemy User model with appropriate fields",
            "Include Pydantic schemas for request/response validation",
            "Include comprehensive tests covering happy path and error cases",
            "Include proper error handling and logging"
        ],
        context={
            "framework": "FastAPI",
            "database": "SQLAlchemy",
            "validation": "Pydantic",
            "password_hashing": "bcrypt"
        }
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
    print("   This task is more complex and will take ~2 minutes...")
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
    print(f"   - Total Latency: {result.total_latency_ms:,} ms ({result.total_latency_ms/1000:.1f}s)")
    print(f"   - Total Tokens: {result.total_tokens:,}")
    print(f"   - Total Cost: ${result.total_cost_usd:.4f}")
    print()

    # Show key metrics by phase
    if hasattr(result, 'phase_metrics'):
        print("📈 Phase Breakdown:")
        for phase, metrics in result.phase_metrics.items():
            print(f"   {phase:20s}: {metrics['latency_ms']:6,}ms | "
                  f"{metrics['tokens']:6,} tokens | "
                  f"${metrics['cost_usd']:.4f}")
        print()

    # Show artifacts
    artifacts_dir = Path(f"artifacts/{task.task_id}")
    print(f"📁 Artifacts saved to: {artifacts_dir}/")
    print()

    # Show generated files
    generated_code_dir = artifacts_dir / "generated_code"
    if generated_code_dir.exists():
        print("📄 Generated Files:")
        for file_path in sorted(generated_code_dir.rglob("*.py")):
            rel_path = file_path.relative_to(generated_code_dir)
            size = file_path.stat().st_size
            print(f"   - {rel_path} ({size:,} bytes)")
        print()

    print(f"🔍 View detailed traces at: https://cloud.langfuse.com")
    print()

    # Show next steps
    print("💡 Next Steps:")
    print(f"   1. Review generated code: cat {generated_code_dir}/*.py")
    print(f"   2. Review design: cat {artifacts_dir}/design.md")
    print(f"   3. Review quality gates: cat {artifacts_dir}/*_review.md")
    print(f"   4. Review tests: cat {generated_code_dir}/test_*.py")
    print()
    print("=" * 70)
    print("Example complete!")
    print("=" * 70)


if __name__ == "__main__":
    main()
