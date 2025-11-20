"""
End-to-End test for all ASP agents with a simple Hello World task.

This test validates the complete 7-agent workflow with a minimal "Hello World" API:
1. Planning Agent - decomposes task into semantic units
2. Design Agent - creates technical design specification
3. Design Review Agent - reviews the design
4. Code Agent - generates implementation code
5. Test Agent - creates and runs tests
6. Postmortem Agent - analyzes performance metrics

This is a comprehensive integration test that makes real API calls to validate
the entire ASP agent pipeline end-to-end.

Requirements:
- ANTHROPIC_API_KEY environment variable must be set
- Will consume API credits (approximately $0.20-0.40 per full test run)

Run with:
    pytest tests/e2e/test_all_agents_hello_world_e2e.py -m e2e -v -s
"""

import os
import pytest
from datetime import datetime
from pathlib import Path

from asp.agents.planning_agent import PlanningAgent
from asp.agents.design_agent import DesignAgent
from asp.agents.design_review_agent import DesignReviewAgent
from asp.agents.code_agent import CodeAgent
from asp.agents.test_agent import TestAgent
from asp.agents.postmortem_agent import PostmortemAgent
from asp.orchestrators import PlanningDesignOrchestrator, PlanningDesignResult

from asp.models.planning import TaskRequirements, ProjectPlan
from asp.models.design import DesignInput, DesignSpecification
from asp.models.code import CodeInput, GeneratedCode
from asp.models.test import TestInput, TestReport
from asp.models.postmortem import (
    PostmortemInput,
    PostmortemReport,
    EffortLogEntry,
    DefectLogEntry,
)


# Skip all tests if no API key is available
pytestmark = pytest.mark.skipif(
    not os.getenv("ANTHROPIC_API_KEY"),
    reason="ANTHROPIC_API_KEY not set - skipping E2E tests"
)


@pytest.mark.e2e
class TestAllAgentsHelloWorldE2E:
    """Complete end-to-end test of all 7 agents with a Hello World task."""

    def test_complete_agent_pipeline_hello_world(self):
        """
        Test the complete 7-agent pipeline with a simple Hello World API.

        This test:
        1. Plans a "Hello World" REST API task
        2. Designs the technical specification
        3. Reviews the design for quality
        4. Generates implementation code
        5. Creates and validates tests
        6. Performs postmortem analysis
        """
        print("\n" + "="*80)
        print("STARTING COMPLETE AGENT PIPELINE TEST: Hello World API")
        print("="*80)

        # =====================================================================
        # STEPS 1-3: Planning → Design → Review with Orchestrator
        # =====================================================================
        print("\n[1-3/6] PLANNING → DESIGN → REVIEW with Feedback Orchestrator")
        print("=" * 80)

        orchestrator = PlanningDesignOrchestrator()

        task_requirements = TaskRequirements(
            project_id="HELLO-WORLD-E2E",
            task_id="HW-001",
            description="Build a simple Hello World REST API endpoint",
            requirements="""
            Create a minimal REST API with the following features:

            1. GET /hello endpoint that:
               - Accepts optional 'name' query parameter
               - Returns JSON response: {"message": "Hello, {name}!" }
               - If no name provided, returns: {"message": "Hello, World!"}

            2. GET /health endpoint that:
               - Returns JSON response: {"status": "ok", "timestamp": <current_time>}

            Requirements:
            - Use a modern Python web framework (FastAPI or Flask)
            - Include proper error handling
            - Return appropriate HTTP status codes
            - Use JSON for all responses
            - Follow REST API best practices
            """,
        )

        print(f"  Task ID: {task_requirements.task_id}")
        print(f"  Description: {task_requirements.description}")
        print("\n  Executing Orchestrated Planning → Design → Review...")
        print("  (Orchestrator will automatically handle feedback loops)")

        # Execute orchestrator with feedback loops
        result = orchestrator.execute(
            requirements=task_requirements,
            design_constraints="Use FastAPI framework. Keep design minimal and simple.",
        )

        # Validate result type
        assert isinstance(result, PlanningDesignResult)

        # Unpack artifacts
        project_plan = result.project_plan
        design_spec = result.design_specification
        design_review = result.design_review

        # Validate outputs
        assert isinstance(design_spec, DesignSpecification)
        assert design_spec.task_id == "HW-001"
        assert len(design_spec.api_contracts) >= 2  # /hello and /health
        assert len(design_spec.component_logic) > 0

        assert design_review is not None
        assert design_review.task_id == "HW-001"
        assert design_review.overall_assessment in ["PASS", "NEEDS_IMPROVEMENT"]

        print(f"\n  ✓ Orchestration complete!")
        print(f"    - Design status: {design_review.overall_assessment}")
        print(f"    - API contracts: {len(design_spec.api_contracts)}")
        for api in design_spec.api_contracts:
            print(f"      • {api.method} {api.endpoint}")
        print(f"    - Components: {len(design_spec.component_logic)}")
        print(f"    - Critical issues: {design_review.critical_issue_count}")
        print(f"    - High issues: {design_review.high_issue_count}")

        # Validate project_plan is available from orchestrator
        assert isinstance(project_plan, ProjectPlan)
        assert project_plan.task_id == "HW-001"
        assert len(project_plan.semantic_units) > 0
        print(f"    - Planning units: {len(project_plan.semantic_units)}")
        print(f"    - Est complexity: {project_plan.total_est_complexity}")

        # =====================================================================
        # STEP 4: Code Agent - Generate Implementation
        # =====================================================================
        print("\n[4/6] CODE AGENT - Code Generation")
        print("-" * 80)

        code_agent = CodeAgent()

        code_input = CodeInput(
            task_id="HW-001",
            design_specification=design_spec,
            coding_standards=(
                "Follow PEP 8 style guide. Use type hints. "
                "Include docstrings for all functions. "
                "Write clean, readable code."
            ),
        )

        print("  Calling Code Agent...")
        generated_code = code_agent.execute(code_input)

        # Validate code generation output
        assert isinstance(generated_code, GeneratedCode)
        assert generated_code.task_id == "HW-001"
        assert len(generated_code.files) > 0
        assert generated_code.total_lines_of_code > 0

        print(f"  ✓ Code generation complete!")
        print(f"    - Files generated: {generated_code.total_files}")
        print(f"    - Total lines of code: {generated_code.total_lines_of_code}")
        print(f"    - Dependencies: {len(generated_code.dependencies)}")

        # Show generated files
        source_files = [f for f in generated_code.files if f.file_type == "source"]
        test_files = [f for f in generated_code.files if f.file_type == "test"]
        print(f"    - Source files: {len(source_files)}")
        for f in source_files[:3]:
            print(f"      • {f.file_path}")
        print(f"    - Test files: {len(test_files)}")
        for f in test_files[:3]:
            print(f"      • {f.file_path}")

        # =====================================================================
        # STEP 5: Test Agent - Generate and Run Tests
        # =====================================================================
        print("\n[5/6] TEST AGENT - Test Generation and Validation")
        print("-" * 80)

        test_agent = TestAgent()

        test_input = TestInput(
            task_id="HW-001",
            generated_code=generated_code,
            design_specification=design_spec,
            test_framework="pytest",
            coverage_target=80.0,
        )

        print("  Calling Test Agent...")
        test_report = test_agent.execute(test_input)

        # Validate test report output
        assert isinstance(test_report, TestReport)
        assert test_report.task_id == "HW-001"
        assert hasattr(test_report, 'test_status')

        print(f"  ✓ Test execution complete!")
        print(f"    - Test status: {test_report.test_status}")
        if hasattr(test_report, 'test_summary'):
            summary = test_report.test_summary
            print(f"    - Total tests: {summary.get('total_tests', 'N/A')}")
            print(f"    - Passed: {summary.get('passed', 'N/A')}")
            print(f"    - Failed: {summary.get('failed', 'N/A')}")
            if 'coverage_percent' in summary:
                print(f"    - Coverage: {summary.get('coverage_percent', 'N/A')}%")

        # =====================================================================
        # STEP 6: Postmortem Agent - Performance Analysis
        # =====================================================================
        print("\n[6/6] POSTMORTEM AGENT - Performance Analysis")
        print("-" * 80)

        postmortem_agent = PostmortemAgent()

        # Create mock effort and defect logs for the postmortem
        effort_log = [
            EffortLogEntry(
                task_id="HW-001",
                phase="Planning",
                start_time=datetime.now(),
                end_time=datetime.now(),
                duration_seconds=120,
                semantic_complexity=project_plan.total_est_complexity,
                tokens_consumed=1500,
                api_cost=0.01,
            ),
            EffortLogEntry(
                task_id="HW-001",
                phase="Design",
                start_time=datetime.now(),
                end_time=datetime.now(),
                duration_seconds=180,
                semantic_complexity=project_plan.total_est_complexity,
                tokens_consumed=2500,
                api_cost=0.02,
            ),
            EffortLogEntry(
                task_id="HW-001",
                phase="Coding",
                start_time=datetime.now(),
                end_time=datetime.now(),
                duration_seconds=240,
                semantic_complexity=project_plan.total_est_complexity,
                tokens_consumed=3000,
                api_cost=0.03,
            ),
        ]

        defect_log = [
            DefectLogEntry(
                task_id="HW-001",
                defect_id="DEF-001",
                defect_type="Missing Error Handling",
                severity="Medium",
                phase_introduced="Design",
                phase_detected="Code Review",
                effort_to_fix_seconds=60,
                description="Missing validation for empty name parameter",
            ),
        ] if hasattr(test_report, 'defects') and len(test_report.defects) > 0 else []

        postmortem_input = PostmortemInput(
            task_id="HW-001",
            project_plan=project_plan,
            effort_log=effort_log,
            defect_log=defect_log,
            actual_semantic_complexity=project_plan.total_est_complexity * 1.1,  # Simulate 10% variance
        )

        print("  Calling Postmortem Agent...")
        postmortem_report = postmortem_agent.execute(postmortem_input)

        # Validate postmortem output
        assert isinstance(postmortem_report, PostmortemReport)
        assert postmortem_report.task_id == "HW-001"

        print(f"  ✓ Postmortem analysis complete!")
        if hasattr(postmortem_report, 'estimation_accuracy'):
            accuracy = postmortem_report.estimation_accuracy
            if hasattr(accuracy, 'api_cost'):
                print(f"    - Cost variance: {accuracy.api_cost.variance_percent:.1f}%")
        if hasattr(postmortem_report, 'quality_metrics'):
            metrics = postmortem_report.quality_metrics
            if hasattr(metrics, 'defect_density'):
                print(f"    - Defect density: {metrics.defect_density:.2f}")

        # =====================================================================
        # FINAL SUMMARY
        # =====================================================================
        print("\n" + "="*80)
        print("✓ ALL AGENTS EXECUTED SUCCESSFULLY!")
        print("="*80)
        print("\nPipeline Summary:")
        print(f"  1. Planning Agent      → {len(project_plan.semantic_units)} semantic units")
        print(f"  2. Design Agent        → {len(design_spec.api_contracts)} API contracts")
        print(f"  3. Design Review Agent → Review completed")
        print(f"  4. Code Agent          → {generated_code.total_files} files, {generated_code.total_lines_of_code} LOC")
        print(f"  5. Test Agent          → {test_report.test_status}")
        print(f"  6. Postmortem Agent    → Analysis completed")
        print("\n" + "="*80 + "\n")

    def test_planning_agent_hello_world(self):
        """Test just the Planning Agent with Hello World task."""
        print("\n" + "="*80)
        print("TESTING: Planning Agent Only - Hello World")
        print("="*80 + "\n")

        agent = PlanningAgent()

        requirements = TaskRequirements(
            project_id="TEST-HW",
            task_id="HW-PLAN-001",
            description="Simple Hello World API endpoint",
            requirements="""
            Create a GET /hello endpoint that returns {"message": "Hello, World!"}
            """,
        )

        plan = agent.execute(requirements)

        assert isinstance(plan, ProjectPlan)
        assert plan.task_id == "HW-PLAN-001"
        assert len(plan.semantic_units) > 0

        print(f"✓ Planning Agent test passed!")
        print(f"  - Semantic units: {len(plan.semantic_units)}")
        print(f"  - Total complexity: {plan.total_est_complexity}\n")

    def test_design_agent_hello_world(self):
        """Test just the Design Agent with Hello World task."""
        print("\n" + "="*80)
        print("TESTING: Design Agent Only - Hello World")
        print("="*80 + "\n")

        # First get a plan
        planning_agent = PlanningAgent()
        requirements = TaskRequirements(
            project_id="TEST-HW",
            task_id="HW-DESIGN-001",
            description="Simple Hello World API endpoint",
            requirements="Create a GET /hello endpoint that returns Hello World",
        )
        plan = planning_agent.execute(requirements)

        # Now test design
        design_agent = DesignAgent()
        design_input = DesignInput(
            task_id="HW-DESIGN-001",
            requirements=requirements.requirements,
            project_plan=plan,
            design_constraints="Use FastAPI, keep it minimal",
        )

        design = design_agent.execute(design_input)

        assert isinstance(design, DesignSpecification)
        assert design.task_id == "HW-DESIGN-001"
        assert len(design.api_contracts) > 0

        print(f"✓ Design Agent test passed!")
        print(f"  - API contracts: {len(design.api_contracts)}")
        print(f"  - Components: {len(design.component_logic)}\n")

    def test_code_agent_hello_world(self):
        """Test just the Code Agent with Hello World task."""
        print("\n" + "="*80)
        print("TESTING: Code Agent Only - Hello World")
        print("="*80 + "\n")

        # Get plan and design first
        planning_agent = PlanningAgent()
        requirements = TaskRequirements(
            project_id="TEST-HW",
            task_id="HW-CODE-001",
            description="Simple Hello World API endpoint",
            requirements="Create a GET /hello endpoint that returns Hello World",
        )
        plan = planning_agent.execute(requirements)

        design_agent = DesignAgent()
        design_input = DesignInput(
            task_id="HW-CODE-001",
            requirements=requirements.requirements,
            project_plan=plan,
        )
        design = design_agent.execute(design_input)

        # Now test code generation
        code_agent = CodeAgent()
        code_input = CodeInput(
            task_id="HW-CODE-001",
            design_specification=design,
            coding_standards="Follow PEP 8",
        )

        code = code_agent.execute(code_input)

        assert isinstance(code, GeneratedCode)
        assert code.task_id == "HW-CODE-001"
        assert len(code.files) > 0

        print(f"✓ Code Agent test passed!")
        print(f"  - Files generated: {code.total_files}")
        print(f"  - Lines of code: {code.total_lines_of_code}\n")


if __name__ == "__main__":
    """Run E2E tests manually."""
    pytest.main([__file__, "-v", "-s", "-m", "e2e"])
