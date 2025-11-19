"""
Simple test of PlanningDesignOrchestrator with real agents.

This is a minimal test to verify the orchestrator works end-to-end.
"""

import os
import sys

print("=" * 80)
print("SIMPLE ORCHESTRATOR TEST")
print("=" * 80)

# Check API key
if not os.getenv("ANTHROPIC_API_KEY"):
    print("\n❌ ANTHROPIC_API_KEY not set - skipping test")
    sys.exit(0)

print("\n✓ API key found")

# Import orchestrator
print("\nImporting orchestrator...")
try:
    from asp.orchestrators import PlanningDesignOrchestrator
    from asp.models.planning import TaskRequirements
    print("✓ Imports successful")
except Exception as e:
    print(f"❌ Import failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Create orchestrator
print("\nCreating orchestrator...")
try:
    orchestrator = PlanningDesignOrchestrator()
    print("✓ Orchestrator created")
except Exception as e:
    print(f"❌ Orchestrator creation failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Create minimal task
print("\nCreating task requirements...")
try:
    requirements = TaskRequirements(
        project_id="TEST-ORCH",
        task_id="SIMPLE-001",
        description="Simple Hello World API",
        requirements="""
        Build a minimal Hello World REST API with:
        1. GET /hello endpoint returning {"message": "Hello, World!"}
        2. Use FastAPI framework
        """,
    )
    print("✓ Task requirements created")
except Exception as e:
    print(f"❌ Task creation failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Execute orchestrator
print("\nExecuting orchestrator (this will make API calls)...")
print("  This may take 1-3 minutes...")
print("-" * 80)

try:
    design_spec, design_review = orchestrator.execute(
        requirements=requirements,
        design_constraints="Use FastAPI. Keep it simple.",
    )
    print("-" * 80)
    print("✓ Orchestrator execution completed!")

    # Display results
    print(f"\n📊 Results:")
    print(f"  Design Assessment: {design_review.overall_assessment}")
    print(f"  API Contracts: {len(design_spec.api_contracts)}")
    for api in design_spec.api_contracts:
        print(f"    • {api.method} {api.endpoint}")
    print(f"  Components: {len(design_spec.component_logic)}")
    print(f"  Critical Issues: {design_review.critical_issue_count}")
    print(f"  High Issues: {design_review.high_issue_count}")
    print(f"  Medium Issues: {design_review.medium_issue_count}")

    # Verify success
    if design_review.overall_assessment in ["PASS", "NEEDS_IMPROVEMENT"]:
        print(f"\n✅ SUCCESS - Design passed review!")
        print(f"   Code Agent can now safely use this design.")
        sys.exit(0)
    else:
        print(f"\n⚠️  WARNING - Design did not pass: {design_review.overall_assessment}")
        sys.exit(1)

except Exception as e:
    print("-" * 80)
    print(f"\n❌ Orchestrator execution failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
