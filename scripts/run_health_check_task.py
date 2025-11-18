#!/usr/bin/env python3
"""
Bootstrap Data Collection - Phase 1: Health Check Endpoint Task

This script runs the "Implement Health Check Endpoint" task through
all 4 implemented agents to validate the complete pipeline and test
artifact persistence infrastructure.

Task: Implement Health Check Endpoint
- REST API endpoint for ASP system status
- Returns DB connection, Langfuse connection, agent availability
- Moderate complexity, real value to project

Usage:
    python scripts/run_health_check_task.py
"""

import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from asp.agents.planning_agent import PlanningAgent
from asp.agents.design_agent import DesignAgent
from asp.agents.design_review_agent import DesignReviewAgent
from asp.agents.code_agent import CodeAgent
from asp.models.planning import TaskRequirements, ProjectPlan
from asp.models.design import DesignInput, DesignSpecification
from asp.models.design_review import DesignReviewReport
from asp.models.code import CodeInput, GeneratedCode


def print_section(title: str):
    """Print a section header."""
    print(f"\n{'='*80}")
    print(f"{title}")
    print(f"{'='*80}\n")


def main():
    """Run health check task through all 4 agents."""

    print_section("BOOTSTRAP DATA COLLECTION - PHASE 1")
    print("Task: Implement Health Check Endpoint")
    print("Goal: Validate pipeline integration and artifact persistence\n")

    # Define the task
    task_id = "BOOTSTRAP-001"
    project_id = "ASP-CORE"

    requirements_text = """
    Implement a REST API health check endpoint for the ASP platform.

    Requirements:
    1. Create GET /api/v1/health endpoint
    2. Check database connectivity (SQLite connection test)
    3. Check Langfuse connectivity (API connection test)
    4. List available agents and their status
    5. Return JSON response with:
       - overall_status: "healthy" | "degraded" | "unhealthy"
       - timestamp: ISO 8601 timestamp
       - database: {connected: bool, message: str}
       - langfuse: {connected: bool, message: str}
       - agents: [{name: str, status: str, version: str}]
    6. Return appropriate HTTP status codes:
       - 200 OK if all systems healthy
       - 503 Service Unavailable if any critical system down
    7. Include error handling for all connectivity checks
    8. Add logging for health check requests
    9. Keep response time under 100ms
    10. No authentication required (public endpoint)

    Technical Context:
    - Framework: FastAPI
    - Database: SQLite (via asp.database module)
    - Telemetry: Langfuse (via asp.telemetry module)
    - Agents: Planning, Design, DesignReview, Code (7 total when complete)
    - Location: src/asp/api/ (create new directory if needed)
    """

    # Step 1: Planning Agent
    print_section("STEP 1: PLANNING AGENT")
    print("Decomposing task into semantic units...\n")

    planning_agent = PlanningAgent()
    task_requirements = TaskRequirements(
        project_id=project_id,
        task_id=task_id,
        description="Implement REST API health check endpoint for ASP platform",
        requirements=requirements_text,
    )

    try:
        plan: ProjectPlan = planning_agent.execute(task_requirements)

        print(f"✅ Planning complete!")
        print(f"   Project ID: {plan.project_id}")
        print(f"   Task ID: {plan.task_id}")
        print(f"   Semantic units: {len(plan.semantic_units)}")
        print(f"   Total complexity: {plan.total_est_complexity}")
        print(f"   Agent version: {plan.agent_version}")

        print(f"\n   Semantic Units:")
        for i, unit in enumerate(plan.semantic_units, 1):
            print(f"   {i}. {unit.unit_id}: {unit.description[:60]}...")
            print(f"      Complexity: {unit.est_complexity}")

    except Exception as e:
        print(f"❌ Planning failed: {e}")
        sys.exit(1)

    # Step 2: Design Agent
    print_section("STEP 2: DESIGN AGENT")
    print("Creating design specification from plan...\n")

    design_agent = DesignAgent()
    design_input = DesignInput(
        task_id=task_id,
        requirements=requirements_text,
        project_plan=plan,
    )

    try:
        design: DesignSpecification = design_agent.execute(design_input)

        print(f"✅ Design complete!")
        print(f"   Project ID: {design.project_id}")
        print(f"   Task ID: {design.task_id}")
        print(f"   Components: {len(design.components)}")
        print(f"   Agent version: {design.agent_version}")

        print(f"\n   Components:")
        for i, component in enumerate(design.components, 1):
            print(f"   {i}. {component.name} ({component.component_type})")
            print(f"      File: {component.file_path}")
            print(f"      Dependencies: {len(component.dependencies)}")

    except Exception as e:
        print(f"❌ Design failed: {e}")
        sys.exit(1)

    # Step 3: Design Review Agent
    print_section("STEP 3: DESIGN REVIEW AGENT")
    print("Reviewing design with specialist agents...\n")

    design_review_agent = DesignReviewAgent()

    try:
        review: DesignReviewReport = design_review_agent.execute(design)

        print(f"✅ Design review complete!")
        print(f"   Project ID: {review.project_id}")
        print(f"   Task ID: {review.task_id}")
        print(f"   Overall decision: {review.overall_decision}")
        print(f"   Critical issues: {review.critical_issue_count}")
        print(f"   Major issues: {review.major_issue_count}")
        print(f"   Minor issues: {review.minor_issue_count}")
        print(f"   Agent version: {review.agent_version}")

        if review.issues:
            print(f"\n   Issues found:")
            for i, issue in enumerate(review.issues[:5], 1):  # Show first 5
                print(f"   {i}. [{issue.severity}] {issue.title}")
                print(f"      Component: {issue.component_name}")
                print(f"      Category: {issue.category}")

        # Check if design was approved
        if review.overall_decision != "APPROVED":
            print(f"\n⚠️  Design was {review.overall_decision}")
            print("   Proceeding anyway for bootstrap purposes...")

    except Exception as e:
        print(f"❌ Design review failed: {e}")
        sys.exit(1)

    # Step 4: Code Agent
    print_section("STEP 4: CODE AGENT")
    print("Generating code from design...\n")

    code_agent = CodeAgent()
    code_input = CodeInput(
        task_id=task_id,
        requirements=requirements_text,
        project_plan=plan,
        design_spec=design,
    )

    try:
        code_result: GeneratedCode = code_agent.execute(code_input)

        print(f"✅ Code generation complete!")
        print(f"   Project ID: {code_result.project_id}")
        print(f"   Task ID: {code_result.task_id}")
        print(f"   Files generated: {len(code_result.generated_files)}")
        print(f"   Agent version: {code_result.agent_version}")

        print(f"\n   Generated Files:")
        for i, file in enumerate(code_result.generated_files, 1):
            print(f"   {i}. {file.file_path}")
            print(f"      Type: {file.file_type}")
            print(f"      Lines: {len(file.content.splitlines())}")

    except Exception as e:
        print(f"❌ Code generation failed: {e}")
        sys.exit(1)

    # Step 5: Summary
    print_section("PIPELINE EXECUTION SUMMARY")
    print(f"✅ All 4 agents executed successfully!")
    print(f"\n   Task: {task_id} - {task_requirements.description}")
    print(f"   Planning: {len(plan.semantic_units)} semantic units, complexity {plan.total_est_complexity}")
    print(f"   Design: {len(design.components)} components")
    print(f"   Review: {review.overall_decision} with {review.critical_issue_count + review.major_issue_count + review.minor_issue_count} issues")
    print(f"   Code: {len(code_result.generated_files)} files generated")

    print(f"\n   Artifacts:")
    print(f"   - Check artifacts/ directory for generated files")
    print(f"   - Check git log for artifact commits")
    print(f"   - Check data/asp_telemetry.db for telemetry data")

    print_section("BOOTSTRAP PHASE 1 COMPLETE")
    print("Next steps:")
    print("1. Review generated artifacts in artifacts/ directory")
    print("2. Check telemetry data in database")
    print("3. Verify git commits were created")
    print("4. Document any issues found")
    print("5. Decide whether to expand to Phase 2 (5-10 tasks)")
    print()


if __name__ == "__main__":
    main()
