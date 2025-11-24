"""
Minimal reproducible example to test if the E2E test can even start.
"""
import sys
print("STEP 1: Starting minimal test", flush=True)

try:
    print("STEP 2: Importing pytest", flush=True)
    import pytest
    print("STEP 3: pytest imported successfully", flush=True)

    print("STEP 4: Importing PlanningAgent", flush=True)
    from asp.agents.planning_agent import PlanningAgent
    print("STEP 5: PlanningAgent imported", flush=True)

    print("STEP 6: Importing PostmortemAgent", flush=True)
    from asp.agents.postmortem_agent import PostmortemAgent
    print("STEP 7: PostmortemAgent imported", flush=True)

    print("STEP 8: Creating PlanningAgent instance", flush=True)
    agent = PlanningAgent()
    print("STEP 9: PlanningAgent created", flush=True)

    print("\n✓ All imports successful - no hanging issue")

except Exception as e:
    print(f"\n✗ Import failed at some step: {e}", flush=True)
    import traceback
    traceback.print_exc()
    sys.exit(1)
