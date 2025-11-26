"""
Unit tests for PlanningDesignOrchestrator.

Tests the phase-aware feedback loop implementation.
"""

import pytest
from unittest.mock import Mock, MagicMock

from asp.orchestrators import PlanningDesignOrchestrator, PlanningDesignResult
from asp.models.planning import TaskRequirements, ProjectPlan, SemanticUnit
from asp.models.design import DesignSpecification, APIContract, ComponentLogic
from asp.models.design_review import DesignReviewReport, DesignIssue


class TestPlanningDesignOrchestrator:
    """Test suite for PlanningDesignOrchestrator."""

    def test_orchestrator_initialization(self):
        """Test that orchestrator initializes correctly."""
        orchestrator = PlanningDesignOrchestrator()

        assert orchestrator is not None
        assert orchestrator._planning_agent is None  # Lazy loading
        assert orchestrator._design_agent is None
        assert orchestrator._design_review_agent is None

    def test_simple_pass_no_feedback_needed(self):
        """Test orchestrator when design passes review on first try (no feedback loop)."""
        orchestrator = PlanningDesignOrchestrator()

        # Mock the agents
        mock_planning_agent = Mock()
        mock_design_agent = Mock()
        mock_review_agent = Mock()

        orchestrator._planning_agent = mock_planning_agent
        orchestrator._design_agent = mock_design_agent
        orchestrator._design_review_agent = mock_review_agent

        # Create mock task requirements
        requirements = TaskRequirements(
            project_id="TEST-001",
            task_id="SIMPLE-001",
            description="Simple test task",
            requirements="Build a hello world API",
        )

        # Mock planning agent response
        mock_plan = ProjectPlan(
            project_id="TEST-001",
            task_id="SIMPLE-001",
            description="Simple test task",
            semantic_units=[
                SemanticUnit(
                    unit_id="SU-001",
                    description="Create API endpoint",
                    unit_type="API Development",
                    estimated_complexity=10,
                )
            ],
            total_est_complexity=10,
        )
        mock_planning_agent.execute.return_value = mock_plan

        # Mock design agent response
        mock_design = DesignSpecification(
            task_id="SIMPLE-001",
            project_plan=mock_plan,
            api_contracts=[
                APIContract(
                    endpoint="/hello",
                    method="GET",
                    description="Hello endpoint",
                    request_schema={},
                    response_schema={"type": "object"},
                    error_responses=[],
                )
            ],
            component_logic=[
                ComponentLogic(
                    component_name="HelloHandler",
                    description="Handles hello requests",
                    responsibilities=["Handle GET /hello"],
                    dependencies=[],
                    key_methods=[],
                )
            ],
            data_models=[],
            dependencies=[],
            deployment_considerations="Deploy to cloud",
            design_review_checklist=["Check security", "Check performance"],
        )
        mock_design_agent.execute.return_value = mock_design

        # Mock design review response - PASS on first try
        mock_review = DesignReviewReport(
            task_id="SIMPLE-001",
            review_id="REVIEW-TEST-20251119-120000",
            overall_assessment="PASS",
            automated_checks={"semantic_coverage": True},
            issues_found=[],
            planning_phase_issues=[],
            design_phase_issues=[],
            multi_phase_issues=[],
            improvement_suggestions=[],
            checklist_review=[],
            critical_issue_count=0,
            high_issue_count=0,
            medium_issue_count=0,
            low_issue_count=0,
        )
        mock_review_agent.execute.return_value = mock_review

        # Execute orchestrator
        result = orchestrator.execute(requirements)

        # Verify result type
        assert isinstance(result, PlanningDesignResult)

        # Unpack result
        project_plan = result.project_plan
        design_spec = result.design_specification
        review = result.design_review

        # Verify results
        assert project_plan == mock_plan
        assert design_spec == mock_design
        assert review == mock_review
        assert review.overall_assessment == "PASS"

        # Verify agents called correct number of times (no feedback loops)
        assert mock_planning_agent.execute.call_count == 1
        assert mock_design_agent.execute.call_count == 1
        assert mock_review_agent.execute.call_count == 1

        # Verify planning called with no feedback
        planning_call = mock_planning_agent.execute.call_args
        assert planning_call[0][0] == requirements
        assert planning_call[1].get("feedback") is None

    def test_design_phase_feedback_loop(self):
        """Test orchestrator with design-phase issues requiring redesign."""
        orchestrator = PlanningDesignOrchestrator()

        # Mock the agents
        mock_planning_agent = Mock()
        mock_design_agent = Mock()
        mock_review_agent = Mock()

        orchestrator._planning_agent = mock_planning_agent
        orchestrator._design_agent = mock_design_agent
        orchestrator._design_review_agent = mock_review_agent

        requirements = TaskRequirements(
            project_id="TEST-001",
            task_id="FEEDBACK-001",
            description="Test feedback loop",
            requirements="Build API with feedback",
        )

        # Mock planning agent
        mock_plan = ProjectPlan(
            project_id="TEST-001",
            task_id="FEEDBACK-001",
            description="Test feedback loop",
            semantic_units=[
                SemanticUnit(
                    unit_id="SU-001",
                    description="Create API",
                    unit_type="API",
                    estimated_complexity=10,
                )
            ],
            total_est_complexity=10,
        )
        mock_planning_agent.execute.return_value = mock_plan

        # Mock design agent - returns two different designs
        mock_design_v1 = DesignSpecification(
            task_id="FEEDBACK-001",
            project_plan=mock_plan,
            api_contracts=[],
            component_logic=[
                ComponentLogic(
                    component_name="Handler",
                    description="Handler",
                    responsibilities=["Handle requests"],
                    dependencies=[],
                    key_methods=[],
                )
            ],
            data_models=[],
            dependencies=[],
            deployment_considerations="Deploy",
            design_review_checklist=["Security"],
        )

        mock_design_v2 = DesignSpecification(
            task_id="FEEDBACK-001",
            project_plan=mock_plan,
            api_contracts=[
                APIContract(
                    endpoint="/api",
                    method="GET",
                    description="API endpoint",
                    request_schema={},
                    response_schema={"type": "object"},
                    error_responses=[],
                )
            ],
            component_logic=[
                ComponentLogic(
                    component_name="Handler",
                    description="Handler",
                    responsibilities=["Handle requests"],
                    dependencies=[],
                    key_methods=[],
                )
            ],
            data_models=[],
            dependencies=[],
            deployment_considerations="Deploy",
            design_review_checklist=["Security"],
        )

        # First call returns v1, second call returns v2 (after feedback)
        mock_design_agent.execute.side_effect = [mock_design_v1, mock_design_v2]

        # Mock review agent - first FAIL, then PASS
        design_issue = DesignIssue(
            issue_id="ISSUE-001",
            category="API Design",
            severity="High",
            description="Missing API endpoint definition",
            evidence="No API contracts defined",
            impact="Cannot generate code without API contracts",
            affected_phase="Design",
        )

        mock_review_fail = DesignReviewReport(
            task_id="FEEDBACK-001",
            review_id="REVIEW-TEST-20251119-120000",
            overall_assessment="FAIL",
            automated_checks={"semantic_coverage": True},
            issues_found=[design_issue],
            planning_phase_issues=[],
            design_phase_issues=[design_issue],
            multi_phase_issues=[],
            improvement_suggestions=[],
            checklist_review=[],
            critical_issue_count=0,
            high_issue_count=1,
            medium_issue_count=0,
            low_issue_count=0,
        )

        mock_review_pass = DesignReviewReport(
            task_id="FEEDBACK-001",
            review_id="REVIEW-TEST-20251119-120001",
            overall_assessment="PASS",
            automated_checks={"semantic_coverage": True},
            issues_found=[],
            planning_phase_issues=[],
            design_phase_issues=[],
            multi_phase_issues=[],
            improvement_suggestions=[],
            checklist_review=[],
            critical_issue_count=0,
            high_issue_count=0,
            medium_issue_count=0,
            low_issue_count=0,
        )

        mock_review_agent.execute.side_effect = [mock_review_fail, mock_review_pass]

        # Execute orchestrator
        result = orchestrator.execute(requirements)

        # Verify result type
        assert isinstance(result, PlanningDesignResult)

        # Unpack result
        project_plan = result.project_plan
        design_spec = result.design_specification
        review = result.design_review

        # Verify final result is v2 and PASS
        assert project_plan == mock_plan
        assert design_spec == mock_design_v2
        assert review == mock_review_pass
        assert len(design_spec.api_contracts) == 1

        # Verify feedback loop executed
        assert mock_planning_agent.execute.call_count == 1  # Planning called once
        assert mock_design_agent.execute.call_count == 2  # Design called twice (initial + feedback)
        assert mock_review_agent.execute.call_count == 2  # Review called twice

        # Verify second design call had feedback
        second_design_call = mock_design_agent.execute.call_args_list[1]
        assert second_design_call[1].get("feedback") == [design_issue]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
