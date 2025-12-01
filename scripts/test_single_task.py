#!/usr/bin/env python3
"""
Single Task Test Script - Validate Design Review Agent Fixes

Tests Design Agent + Design Review Agent on a single task to validate
bug fixes before running full bootstrap collection.

Usage:
    python scripts/test_single_task.py TASK_ID

Example:
    python scripts/test_single_task.py BOOTSTRAP-003
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import json
import time

from asp.agents.design_agent import DesignAgent
from asp.agents.design_review_orchestrator import DesignReviewOrchestrator
from asp.models.design import DesignInput
from asp.models.planning import ProjectPlan, SemanticUnit


def load_bootstrap_tasks():
    """Load the original bootstrap task definitions with requirements."""
    sys.path.insert(0, str(Path(__file__).parent))
    from bootstrap_data_collection import BOOTSTRAP_TASKS

    return {task["task_id"]: task for task in BOOTSTRAP_TASKS}


def load_planning_result(task_id):
    """Load a specific planning result."""
    planning_file = Path("data/bootstrap_results.json")

    if not planning_file.exists():
        print(f"ERROR: Planning results not found at {planning_file}")
        sys.exit(1)

    with open(planning_file) as f:
        data = json.load(f)

    for result in data["results"]:
        if result["task_id"] == task_id:
            return result

    print(f"ERROR: Task {task_id} not found in planning results")
    sys.exit(1)


def reconstruct_project_plan(planning_result):
    """Reconstruct a ProjectPlan from bootstrap results."""
    units = []
    for u in planning_result["units"]:
        unit = SemanticUnit(
            unit_id=u["unit_id"],
            description=u["description"],
            est_complexity=u["complexity"],
            api_interactions=u["factors"]["api_interactions"],
            data_transformations=u["factors"]["data_transformations"],
            logical_branches=u["factors"]["logical_branches"],
            code_entities_modified=u["factors"]["code_entities_modified"],
            novelty_multiplier=u["factors"]["novelty_multiplier"],
            dependencies=u["dependencies"],
        )
        units.append(unit)

    plan = ProjectPlan(
        task_id=planning_result["task_id"],
        project_id=planning_result["project_id"],
        semantic_units=units,
        total_est_complexity=planning_result["actual_total_complexity"],
    )

    return plan


def test_single_task(task_id):
    """Test Design + Design Review on a single task."""
    print("=" * 80)
    print(f"SINGLE TASK TEST: {task_id}")
    print("=" * 80)
    print()

    # Load task data
    bootstrap_tasks = load_bootstrap_tasks()
    planning_result = load_planning_result(task_id)
    bootstrap_task = bootstrap_tasks.get(task_id)

    if not bootstrap_task:
        print(f"ERROR: Bootstrap task {task_id} not found")
        sys.exit(1)

    print(f"Task: {planning_result['description']}")
    print(f"Planning Complexity: {planning_result['actual_total_complexity']}")
    print(f"Units: {planning_result['num_units']}")
    print()

    # Initialize agents
    design_agent = DesignAgent()
    review_orchestrator = DesignReviewOrchestrator()

    # Step 1: Run Design Agent
    print("[1/2] Running Design Agent...")
    design_start = time.time()

    try:
        task_plan = reconstruct_project_plan(planning_result)
        design_input = DesignInput(
            task_id=task_id,
            requirements=bootstrap_task["requirements"],
            project_plan=task_plan,
        )

        design_spec = design_agent.execute(design_input)
        design_elapsed = time.time() - design_start

        print(f" Design Agent SUCCESS ({design_elapsed:.2f}s)")
        print(f"   API Contracts: {len(design_spec.api_contracts)}")
        print(f"   Data Schemas: {len(design_spec.data_schemas)}")
        print(f"   Components: {len(design_spec.component_logic)}")
        print(f"   Checklist Items: {len(design_spec.design_review_checklist)}")
        print()

    except Exception as e:
        design_elapsed = time.time() - design_start
        print(f" Design Agent FAILED ({design_elapsed:.2f}s): {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)

    # Step 2: Run Design Review Agent
    print("[2/2] Running Design Review Agent...")
    review_start = time.time()

    try:
        review_report = review_orchestrator.execute(design_spec)
        review_elapsed = time.time() - review_start

        total_issues = (
            review_report.critical_issue_count
            + review_report.high_issue_count
            + review_report.medium_issue_count
            + review_report.low_issue_count
        )

        checklist_passed = sum(
            1 for item in review_report.checklist_review if item.status == "PASS"
        )
        checklist_total = len(review_report.checklist_review)

        print(f" Design Review Agent SUCCESS ({review_elapsed:.2f}s)")
        print(f"   Overall Assessment: {review_report.overall_assessment}")
        print(f"   Total Issues: {total_issues}")
        print(f"     Critical: {review_report.critical_issue_count}")
        print(f"     High: {review_report.high_issue_count}")
        print(f"     Medium: {review_report.medium_issue_count}")
        print(f"     Low: {review_report.low_issue_count}")
        print(f"   Suggestions: {len(review_report.improvement_suggestions)}")
        print(f"   Checklist: {checklist_passed}/{checklist_total} passed")
        print()

        print("=" * 80)
        print(" TEST PASSED - All bugs fixed!")
        print("=" * 80)
        print(f"Total Time: {design_elapsed + review_elapsed:.2f}s")
        print()

        return True

    except Exception as e:
        review_elapsed = time.time() - review_start
        print(f" Design Review Agent FAILED ({review_elapsed:.2f}s): {e}")
        import traceback

        traceback.print_exc()
        print()
        print("=" * 80)
        print(" TEST FAILED - Bugs still present")
        print("=" * 80)
        sys.exit(1)


def main():
    """Main entry point."""
    if len(sys.argv) != 2:
        print("Usage: python scripts/test_single_task.py TASK_ID")
        print("Example: python scripts/test_single_task.py BOOTSTRAP-003")
        sys.exit(1)

    task_id = sys.argv[1]
    test_single_task(task_id)


if __name__ == "__main__":
    main()
