#!/usr/bin/env python3
"""
Bootstrap Data Collection Script - Design + Design Review Agents

Runs Design Agent and Design Review Agent on the 12 bootstrap planning tasks to:
- Generate DesignSpecifications for all bootstrap tasks
- Review each design with the multi-agent Design Review system
- Build comprehensive bootstrap telemetry dataset
- Validate end-to-end Planning→Design→Design Review workflow
- Collect cost/time data for PROBE-AI calibration

Usage:
    python scripts/bootstrap_design_review_collection.py
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import json
import time
from datetime import datetime

from asp.agents.design_agent import DesignAgent
from asp.agents.design_review_orchestrator import DesignReviewOrchestrator
from asp.models.design import DesignInput
from asp.models.planning import ProjectPlan, SemanticUnit


def load_bootstrap_tasks():
    """Load the original bootstrap task definitions with requirements."""
    # Import from the bootstrap_data_collection module
    sys.path.insert(0, str(Path(__file__).parent))
    from bootstrap_data_collection import BOOTSTRAP_TASKS

    # Create a lookup dict by task_id
    tasks_by_id = {task["task_id"]: task for task in BOOTSTRAP_TASKS}
    return tasks_by_id


def load_planning_results():
    """Load the 12 bootstrap planning results."""
    planning_file = Path("data/bootstrap_results.json")

    if not planning_file.exists():
        print(f"ERROR: Planning results not found at {planning_file}")
        print("Please run scripts/bootstrap_data_collection.py first")
        sys.exit(1)

    with open(planning_file) as f:
        data = json.load(f)

    print(f"Loaded {data['total_tasks']} planning tasks")
    print(f"  Successful: {data['successful']}")
    print(f"  Failed: {data['failed']}")

    return data["results"]


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


def save_results(all_results, output_file):
    """Save results incrementally after each task."""
    output_file.parent.mkdir(exist_ok=True)
    successful_pipeline = sum(
        1 for r in all_results if r.get("pipeline_success", False)
    )

    with open(output_file, "w") as f:
        json.dump(
            {
                "timestamp": datetime.now().isoformat(),
                "total_tasks": len(all_results),
                "successful_pipeline": successful_pipeline,
                "failed_pipeline": len(all_results) - successful_pipeline,
                "results": all_results,
            },
            f,
            indent=2,
        )


def run_bootstrap_design_review_collection():
    """Run Design Agent and Design Review Agent on all bootstrap tasks."""

    print("=" * 80)
    print("BOOTSTRAP DATA COLLECTION - Design + Design Review Agents")
    print("=" * 80)
    print(f"Starting at: {datetime.now().isoformat()}")
    print()

    # Load original bootstrap tasks (for requirements text)
    bootstrap_tasks = load_bootstrap_tasks()

    # Load planning results
    planning_results = load_planning_results()
    successful_planning = [r for r in planning_results if r["success"]]

    # Load existing results to resume from where we left off
    output_file = Path("data/bootstrap_design_review_results.json")
    existing_results = {}
    if output_file.exists():
        with open(output_file) as f:
            existing_data = json.load(f)
            # Create map of task_id -> result for successful pipelines
            existing_results = {
                r["task_id"]: r
                for r in existing_data.get("results", [])
                if r.get("pipeline_success", False)
            }
        print(f"Found {len(existing_results)} already-successful tasks, will skip them")
        print(f"Tasks to skip: {sorted(existing_results.keys())}")
        print()

    print(f"Processing {len(successful_planning)} total planning tasks")
    print(f"  Already completed: {len(existing_results)}")
    print(f"  Remaining: {len(successful_planning) - len(existing_results)}")
    print()

    # Initialize agents
    design_agent = DesignAgent()
    review_orchestrator = DesignReviewOrchestrator()

    # Start with existing successful results
    all_results = list(existing_results.values())

    # Output file for incremental saves
    output_file = Path("data/bootstrap_design_review_results.json")

    for i, planning_result in enumerate(successful_planning, 1):
        task_id = planning_result["task_id"]

        # Skip if already successfully completed
        if task_id in existing_results:
            print(
                f"\nSKIPPING TASK {i}/{len(successful_planning)}: {task_id} (already successful)"
            )
            continue

        print(f"\n{'='*80}")
        print(f"TASK {i}/{len(successful_planning)}: {task_id}")
        print(f"{'='*80}")
        print(f"Description: {planning_result['description']}")
        print(f"Planning Complexity: {planning_result['actual_total_complexity']}")
        print(f"Units: {planning_result['num_units']}")
        print()

        task_result = {
            "task_id": task_id,
            "project_id": planning_result["project_id"],
            "description": planning_result["description"],
            "planning_complexity": planning_result["actual_total_complexity"],
            "planning_units": planning_result["num_units"],
        }

        # STEP 1: Run Design Agent
        print(f"[1/2] Running Design Agent...")
        design_start = time.time()

        try:
            # Get original requirements
            task_id = planning_result["task_id"]
            bootstrap_task = bootstrap_tasks.get(task_id)
            if not bootstrap_task:
                raise ValueError(f"Bootstrap task {task_id} not found")

            # Reconstruct ProjectPlan
            task_plan = reconstruct_project_plan(planning_result)

            # Create DesignInput
            design_input = DesignInput(
                task_id=task_id,
                requirements=bootstrap_task["requirements"],
                project_plan=task_plan,
            )

            # Execute Design Agent (synchronous)
            design_spec = design_agent.execute(design_input)
            design_elapsed = time.time() - design_start

            print(f" Design Agent SUCCESS ({design_elapsed:.2f}s)")
            print(f"   API Contracts: {len(design_spec.api_contracts)}")
            print(f"   Data Schemas: {len(design_spec.data_schemas)}")
            print(f"   Components: {len(design_spec.component_logic)}")
            print(f"   Checklist Items: {len(design_spec.design_review_checklist)}")
            print()

            task_result["design_success"] = True
            task_result["design_execution_time"] = design_elapsed
            task_result["design_api_contracts"] = len(design_spec.api_contracts)
            task_result["design_data_schemas"] = len(design_spec.data_schemas)
            task_result["design_components"] = len(design_spec.component_logic)
            task_result["design_checklist_items"] = len(
                design_spec.design_review_checklist
            )

        except Exception as e:
            design_elapsed = time.time() - design_start
            print(f" Design Agent FAILED ({design_elapsed:.2f}s): {e}")
            print()

            task_result["design_success"] = False
            task_result["design_execution_time"] = design_elapsed
            task_result["design_error"] = str(e)
            all_results.append(task_result)
            continue

        # STEP 2: Run Design Review Agent
        print(f"[2/2] Running Design Review Agent...")
        review_start = time.time()

        try:
            # Execute Design Review Orchestrator (synchronous, uses asyncio.run internally)
            review_report = review_orchestrator.execute(design_spec)
            review_elapsed = time.time() - review_start

            # Calculate total issues
            total_issues = (
                review_report.critical_issue_count
                + review_report.high_issue_count
                + review_report.medium_issue_count
                + review_report.low_issue_count
            )

            # Calculate checklist counts
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
            # Calculate total suggestions
            total_suggestions = len(review_report.improvement_suggestions)

            print(f"   Suggestions: {total_suggestions}")
            print(f"   Checklist: {checklist_passed}/{checklist_total} passed")
            print()

            task_result["review_success"] = True
            task_result["review_execution_time"] = review_elapsed
            task_result["review_overall_assessment"] = review_report.overall_assessment
            task_result["review_total_issues"] = total_issues
            task_result["review_critical_issues"] = review_report.critical_issue_count
            task_result["review_high_issues"] = review_report.high_issue_count
            task_result["review_medium_issues"] = review_report.medium_issue_count
            task_result["review_low_issues"] = review_report.low_issue_count
            task_result["review_total_suggestions"] = total_suggestions
            task_result["review_checklist_passed"] = checklist_passed
            task_result["review_checklist_total"] = checklist_total

            # Success: Both agents completed
            task_result["pipeline_success"] = True
            task_result["total_execution_time"] = design_elapsed + review_elapsed

        except Exception as e:
            review_elapsed = time.time() - review_start
            print(f" Design Review Agent FAILED ({review_elapsed:.2f}s): {e}")
            import traceback

            traceback.print_exc()
            print()

            task_result["review_success"] = False
            task_result["review_execution_time"] = review_elapsed
            task_result["review_error"] = str(e)
            task_result["pipeline_success"] = False
            task_result["total_execution_time"] = design_elapsed + review_elapsed

        all_results.append(task_result)

        # Save results incrementally after each task
        save_results(all_results, output_file)
        print(f"Results saved ({len(all_results)} tasks completed)")

    # Final save with summary
    save_results(all_results, output_file)

    print(f"\n{'='*80}")
    print("BOOTSTRAP COLLECTION COMPLETE")
    print(f"{'='*80}")
    print(f"Results saved to: {output_file}")
    print(f"Successful (full pipeline): {successful_pipeline}/{len(all_results)}")
    print(f"Failed: {len(all_results) - successful_pipeline}/{len(all_results)}")
    print()

    return all_results


def main():
    """Main entry point."""
    try:
        results = run_bootstrap_design_review_collection()

        # Summary analysis
        print("\n" + "=" * 80)
        print("PIPELINE ANALYSIS")
        print("=" * 80)

        successful = [r for r in results if r.get("pipeline_success", False)]

        if successful:
            # Design Agent stats
            avg_design_time = sum(r["design_execution_time"] for r in successful) / len(
                successful
            )
            avg_api_contracts = sum(
                r["design_api_contracts"] for r in successful
            ) / len(successful)
            avg_data_schemas = sum(r["design_data_schemas"] for r in successful) / len(
                successful
            )
            avg_components = sum(r["design_components"] for r in successful) / len(
                successful
            )

            print(f"\nDesign Agent (n={len(successful)}):")
            print(f"  Avg Execution Time: {avg_design_time:.2f}s")
            print(f"  Avg API Contracts: {avg_api_contracts:.1f}")
            print(f"  Avg Data Schemas: {avg_data_schemas:.1f}")
            print(f"  Avg Components: {avg_components:.1f}")

            # Design Review Agent stats
            avg_review_time = sum(r["review_execution_time"] for r in successful) / len(
                successful
            )
            avg_issues = sum(r["review_total_issues"] for r in successful) / len(
                successful
            )
            avg_critical = sum(r["review_critical_issues"] for r in successful) / len(
                successful
            )
            avg_suggestions = sum(
                r["review_total_suggestions"] for r in successful
            ) / len(successful)

            print(f"\nDesign Review Agent (n={len(successful)}):")
            print(f"  Avg Execution Time: {avg_review_time:.2f}s")
            print(f"  Avg Issues Found: {avg_issues:.1f}")
            print(f"  Avg Critical Issues: {avg_critical:.1f}")
            print(f"  Avg Suggestions: {avg_suggestions:.1f}")

            # Overall stats
            avg_total_time = sum(r["total_execution_time"] for r in successful) / len(
                successful
            )
            total_time = sum(r["total_execution_time"] for r in successful)

            print(f"\nPipeline (Planning→Design→Review):")
            print(f"  Avg Total Time: {avg_total_time:.2f}s")
            print(f"  Total Time: {total_time:.2f}s ({total_time/60:.1f} minutes)")

            # Review assessment breakdown
            assessment_counts = {}
            for r in successful:
                assessment = r["review_overall_assessment"]
                assessment_counts[assessment] = assessment_counts.get(assessment, 0) + 1

            print(f"\nReview Assessment Breakdown:")
            for assessment, count in sorted(assessment_counts.items()):
                print(f"  {assessment}: {count}")

    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nFATAL ERROR: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
