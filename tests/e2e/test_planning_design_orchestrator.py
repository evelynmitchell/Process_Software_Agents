"""
End-to-end test for the PlanningDesignOrchestrator.
"""

import os
import pytest
from asp.orchestrators import PlanningDesignOrchestrator
from asp.models.planning import TaskRequirements


@pytest.mark.e2e
def test_planning_design_orchestrator_e2e(llm_client):
    """
    Tests that the PlanningDesignOrchestrator can successfully execute a simple task.
    This test makes real API calls and may take a few minutes to run.
    """
    if not os.getenv("ANTHROPIC_API_KEY"):
        pytest.skip("ANTHROPIC_API_KEY not set, skipping end-to-end test.")

    # Create orchestrator
    orchestrator = PlanningDesignOrchestrator(llm_client=llm_client)

    # Create minimal task
    requirements = TaskRequirements(
        project_id="TEST-ORCH",
        task_id="E2E-SIMPLE-001",
        description="Simple Hello World API",
        requirements="""
        Build a minimal Hello World REST API with:
        1. GET /hello endpoint returning {"message": "Hello, World!"}
        2. Use FastAPI framework
        """,
    )

    # Execute orchestrator
    design_spec, design_review = orchestrator.execute(
        requirements=requirements,
        design_constraints="Use FastAPI. Keep it simple.",
    )

    # Verify results
    assert design_spec is not None
    assert design_review is not None
    assert design_review.overall_assessment in ["PASS", "NEEDS_IMPROVEMENT"]
    assert len(design_spec.api_contracts) > 0
    assert len(design_spec.component_logic) > 0
