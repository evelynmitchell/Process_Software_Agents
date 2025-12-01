"""
Debug script to examine design review issues for Hello World API.
"""

from asp.agents.planning_agent import PlanningAgent
from asp.agents.design_agent import DesignAgent
from asp.agents.design_review_orchestrator import DesignReviewOrchestrator
from asp.models.planning import TaskRequirements
from asp.models.design import DesignInput

# Simple Hello World requirements
requirements = TaskRequirements(
    project_id="DEBUG-TEST",
    task_id="DEBUG-001",
    description="Build a minimal Hello World REST API",
    requirements="""
    Create a simple REST API with:

    1. GET /hello endpoint that returns:
       {"message": "Hello, World!", "timestamp": <current_time>}

    Requirements:
    - Use FastAPI framework
    - Include proper error handling
    - Return JSON responses
    - Follow REST best practices
    """,
)

print("=" * 80)
print("STEP 1: Planning Agent")
print("=" * 80)
planning_agent = PlanningAgent()
project_plan = planning_agent.execute(requirements)
print(f"✓ Planning complete: {len(project_plan.semantic_units)} units")

print("\n" + "=" * 80)
print("STEP 2: Design Agent")
print("=" * 80)
design_agent = DesignAgent()
design_input = DesignInput(
    task_id=requirements.task_id,
    requirements=requirements.requirements,
    project_plan=project_plan,
    design_constraints="Use FastAPI. Keep design minimal.",
)
design_spec = design_agent.execute(design_input)
print(
    f"✓ Design complete: {len(design_spec.api_contracts)} APIs, {len(design_spec.component_logic)} components"
)

print("\n" + "=" * 80)
print("STEP 3: Design Review Orchestrator")
print("=" * 80)
review_orchestrator = DesignReviewOrchestrator()
design_review = review_orchestrator.execute(design_spec)

print(f"\nReview Status: {design_review.overall_assessment}")
print(
    f"Issues: {design_review.critical_issue_count}C / {design_review.high_issue_count}H / {design_review.medium_issue_count}M / {design_review.low_issue_count}L"
)

if design_review.issues_found:
    print("\n" + "=" * 80)
    print(f"DESIGN ISSUES FOUND ({len(design_review.issues_found)} total)")
    print("=" * 80)

    # Group by severity
    for severity in ["Critical", "High", "Medium", "Low"]:
        issues = [i for i in design_review.issues_found if i.severity == severity]
        if issues:
            print(f"\n{severity} Issues ({len(issues)}):")
            print("-" * 80)
            for i, issue in enumerate(issues, 1):
                print(f"\n{i}. [{issue.category}] {issue.description}")
                print(f"   Location: {issue.evidence}")
                print(f"   Impact: {issue.impact}")

print("\n" + "=" * 80)
print("IMPROVEMENT SUGGESTIONS")
print("=" * 80)
if design_review.improvement_suggestions:
    for i, suggestion in enumerate(design_review.improvement_suggestions[:5], 1):
        print(f"\n{i}. {suggestion.title}")
        print(f"   Category: {suggestion.category}")
        print(f"   Priority: {suggestion.priority}")
        print(f"   Description: {suggestion.description[:200]}...")
