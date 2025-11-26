#!/usr/bin/env python3
"""
HITL Workflow Example - ASP Platform

This example demonstrates Human-In-The-Loop approval workflow
using Local PR-style approval for quality gate failures.

Run with:
    uv run python examples/hitl_workflow.py

Cost: ~$0.15 - $0.30
Time: ~1 minute + human approval time
"""

from asp.orchestrators import TSPOrchestrator
from asp.approval import LocalPRApprovalService
from asp.models.planning import TaskRequirements
from pathlib import Path
import os


def main():
    """Run task with HITL approval workflow."""
    print("=" * 70)
    print("ASP Platform - HITL Workflow Example")
    print("=" * 70)
    print()

    # Check if we're in a git repository
    if not Path(".git").exists():
        print("⚠️  Warning: Not a git repository")
        print("   HITL Local PR-style requires a git repository")
        print("   Initialize with: git init && git add . && git commit -m 'Initial'")
        print()
        return

    # Create task with intentional security issue to trigger review failure
    task = TaskRequirements(
        task_id="HITL-EXAMPLE-001",
        description="Create a user login endpoint (with intentional security gap for demo)",
        requirements=[
            "POST /api/login endpoint",
            "Accept username and password in JSON body",
            "Return JWT token on successful authentication",
            "Store user credentials in database",
            # Intentionally omit security requirements to trigger review failure
        ]
    )

    print(f"📋 Task ID: {task.task_id}")
    print(f"📝 Description: {task.description}")
    print()
    print("⚠️  Note: This task intentionally omits security requirements")
    print("   to demonstrate HITL approval when quality gates fail.")
    print()

    # Create HITL approval service
    print("🔧 Configuring HITL approval service...")
    approval_service = LocalPRApprovalService(
        repo_path=os.getcwd(),
        base_branch="main",
        auto_cleanup=True
    )
    print("   ✓ Local PR-style approval enabled")
    print()

    # Create orchestrator with HITL
    print("🚀 Starting ASP pipeline with HITL...")
    print()

    orchestrator = TSPOrchestrator(
        approval_service=approval_service
    )

    # Execute - will pause for human approval if quality gates fail
    print("📝 Pipeline execution starting...")
    print("   - If quality gates fail, you'll be prompted for approval")
    print("   - You can approve, reject, or defer the changes")
    print()

    result = orchestrator.execute(task)

    # Display results
    print()
    print("=" * 70)
    print("✅ Pipeline completed!")
    print("=" * 70)
    print()

    print("📊 Results:")
    print(f"   - Status: {result.status}")
    print(f"   - Quality Gates: {result.quality_gate_status}")
    print(f"   - Total Cost: ${result.total_cost_usd:.4f}")
    print()

    if hasattr(result, 'approval_decisions'):
        print("🔍 HITL Approval Decisions:")
        for decision in result.approval_decisions:
            print(f"   - Gate: {decision.gate_type}")
            print(f"   - Decision: {decision.decision}")
            print(f"   - Reviewer: {decision.reviewer}")
            print(f"   - Justification: {decision.justification}")
            print()

    # Show audit trail
    print("📝 Audit Trail:")
    print("   All HITL decisions are stored in git notes for traceability")
    print("   View with: git notes --ref=reviews show <commit-sha>")
    print()

    # Show artifacts
    artifacts_dir = Path(f"artifacts/{task.task_id}")
    print(f"📁 Artifacts saved to: {artifacts_dir}/")
    print()

    print("💡 Next Steps:")
    print("   1. Review design issues that triggered HITL")
    print("   2. Check git branches for review: git branch | grep review/")
    print("   3. View approval metadata: git notes --ref=reviews show HEAD")
    print()
    print("=" * 70)
    print("Example complete!")
    print("=" * 70)


if __name__ == "__main__":
    main()
