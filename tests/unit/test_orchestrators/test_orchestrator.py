"""
Unit tests for PlanningDesignOrchestrator.

Tests the phase-aware feedback loop implementation.
"""

from unittest.mock import Mock

import pytest

from asp.models.design import (
    APIContract,
    ComponentLogic,
    DesignReviewChecklistItem,
    DesignSpecification,
)
from asp.models.design_review import (
    ChecklistItemReview,
    DesignIssue,
    DesignReviewReport,
)
from asp.models.planning import ProjectPlan, SemanticUnit, TaskRequirements
from asp.orchestrators import PlanningDesignOrchestrator, PlanningDesignResult


def make_semantic_unit(
    unit_id: str = "SU-001",
    description: str = "Create API endpoint for the hello world service",
) -> SemanticUnit:
    """Helper to create valid SemanticUnit test data."""
    return SemanticUnit(
        unit_id=unit_id,
        description=description,
        api_interactions=1,
        data_transformations=0,
        logical_branches=1,
        code_entities_modified=1,
        novelty_multiplier=1.0,
        est_complexity=10,
    )


def make_component_logic(
    name: str = "HelloHandler",
    semantic_unit_id: str = "SU-001",
) -> ComponentLogic:
    """Helper to create valid ComponentLogic test data."""
    return ComponentLogic(
        component_name=name,
        semantic_unit_id=semantic_unit_id,
        responsibility="Handles incoming HTTP requests and returns appropriate responses",
        interfaces=[{"method": "handle_request", "returns": "Response"}],
        implementation_notes="Use standard REST patterns with proper error handling",
    )


def make_design_review_checklist(count: int = 5) -> list[DesignReviewChecklistItem]:
    """Helper to create minimum required checklist items."""
    categories = ["Security", "API", "Data", "Error Handling", "Performance"]
    severities = ["Critical", "High", "Medium", "Medium", "Medium"]
    return [
        DesignReviewChecklistItem(
            category=categories[i % len(categories)],
            description=f"Validate {categories[i % len(categories)].lower()} requirements for the component thoroughly",
            validation_criteria=f"Check that all {categories[i % len(categories)].lower()} standards are properly met",
            severity=severities[i % len(severities)],
        )
        for i in range(count)
    ]


def make_checklist_review(count: int = 1) -> list[ChecklistItemReview]:
    """Helper to create checklist review items."""
    return [
        ChecklistItemReview(
            checklist_item_id=f"CHECK-{i + 1:03d}",
            category="Security",
            description=f"Validate security requirements for component {i + 1}",
            status="Pass",
            notes="All requirements have been verified and passed inspection",
        )
        for i in range(count)
    ]


def make_design_specification(
    task_id: str = "SIMPLE-001",
    api_contracts: list[APIContract] | None = None,
    component_logic: list[ComponentLogic] | None = None,
) -> DesignSpecification:
    """Helper to create valid DesignSpecification test data."""
    return DesignSpecification(
        task_id=task_id,
        architecture_overview="This system uses a 3-tier architecture with REST API layer and service layer",
        technology_stack={"language": "Python 3.12", "framework": "FastAPI"},
        api_contracts=api_contracts or [],
        component_logic=component_logic or [make_component_logic()],
        design_review_checklist=make_design_review_checklist(5),
    )


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
            semantic_units=[make_semantic_unit()],
            total_est_complexity=10,
        )
        mock_planning_agent.execute.return_value = mock_plan

        # Mock design agent response
        mock_design = make_design_specification(
            task_id="SIMPLE-001",
            api_contracts=[
                APIContract(
                    endpoint="/hello",
                    method="GET",
                    description="Hello endpoint for testing",
                    request_schema={},
                    response_schema={"type": "object"},
                    semantic_unit_id="SU-001",
                )
            ],
        )
        mock_design_agent.execute.return_value = mock_design

        # Mock design review response - PASS on first try
        mock_review = DesignReviewReport(
            task_id="SIMPLE-001",
            review_id="REVIEW-TEST-20251119-120000",
            design_id="DESIGN-001",
            overall_assessment="PASS",
            automated_checks={"semantic_coverage": True},
            issues_found=[],
            improvement_suggestions=[],
            checklist_review=make_checklist_review(1),
            critical_issue_count=0,
            high_issue_count=0,
            medium_issue_count=0,
            low_issue_count=0,
            reviewer_agent="DesignReviewAgent",
            agent_version="1.0.0",
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
            semantic_units=[
                make_semantic_unit(
                    description="Create API endpoint with feedback handling support"
                )
            ],
            total_est_complexity=10,
        )
        mock_planning_agent.execute.return_value = mock_plan

        # Mock design agent - returns two different designs
        mock_design_v1 = make_design_specification(
            task_id="FEEDBACK-001",
            api_contracts=[],  # Missing API contracts
        )

        mock_design_v2 = make_design_specification(
            task_id="FEEDBACK-001",
            api_contracts=[
                APIContract(
                    endpoint="/api",
                    method="GET",
                    description="API endpoint for testing",
                    request_schema={},
                    response_schema={"type": "object"},
                    semantic_unit_id="SU-001",
                )
            ],
        )

        # First call returns v1, second call returns v2 (after feedback)
        mock_design_agent.execute.side_effect = [mock_design_v1, mock_design_v2]

        # Mock review agent - first FAIL, then PASS
        design_issue = DesignIssue(
            issue_id="ISSUE-001",
            category="API Design",
            severity="High",
            description="Missing API endpoint definition",
            affected_component="API",
            evidence="No API contracts defined",
            impact="Cannot generate code without API contracts",
            recommendation="Add API contract specifications",
        )

        mock_review_fail = DesignReviewReport(
            task_id="FEEDBACK-001",
            review_id="REVIEW-TEST-20251119-120000",
            design_id="DESIGN-001",
            overall_assessment="FAIL",
            automated_checks={"semantic_coverage": True},
            issues_found=[design_issue],
            improvement_suggestions=[],
            checklist_review=make_checklist_review(1),
            critical_issue_count=0,
            high_issue_count=1,
            medium_issue_count=0,
            low_issue_count=0,
            reviewer_agent="DesignReviewAgent",
            agent_version="1.0.0",
        )

        mock_review_pass = DesignReviewReport(
            task_id="FEEDBACK-001",
            review_id="REVIEW-TEST-20251119-120001",
            design_id="DESIGN-002",
            overall_assessment="PASS",
            automated_checks={"semantic_coverage": True},
            issues_found=[],
            improvement_suggestions=[],
            checklist_review=make_checklist_review(1),
            critical_issue_count=0,
            high_issue_count=0,
            medium_issue_count=0,
            low_issue_count=0,
            reviewer_agent="DesignReviewAgent",
            agent_version="1.0.0",
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
        assert (
            mock_design_agent.execute.call_count == 2
        )  # Design called twice (initial + feedback)
        assert mock_review_agent.execute.call_count == 2  # Review called twice

        # Verify second design call had feedback
        second_design_call = mock_design_agent.execute.call_args_list[1]
        assert second_design_call[1].get("feedback") == [design_issue]


class TestAsyncPlanningDesignOrchestrator:
    """
    Test suite for PlanningDesignOrchestrator.execute_async().

    Part of ADR 008 Phase 4: Async Orchestrators.
    """

    @pytest.mark.asyncio
    async def test_async_orchestrator_simple_pass(self):
        """Test async orchestrator when design passes review on first try."""
        from unittest.mock import AsyncMock

        orchestrator = PlanningDesignOrchestrator()

        # Mock the agents with async support
        mock_planning_agent = Mock()
        mock_design_agent = Mock()
        mock_review_agent = Mock()

        mock_planning_agent.execute_async = AsyncMock()
        mock_design_agent.execute_async = AsyncMock()
        mock_review_agent.execute_async = AsyncMock()

        orchestrator._planning_agent = mock_planning_agent
        orchestrator._design_agent = mock_design_agent
        orchestrator._design_review_agent = mock_review_agent

        # Create mock task requirements
        requirements = TaskRequirements(
            project_id="TEST-ASYNC-001",
            task_id="ASYNC-001",
            description="Async test task",
            requirements="Build a hello world API asynchronously",
        )

        # Mock planning agent response
        mock_plan = ProjectPlan(
            project_id="TEST-ASYNC-001",
            task_id="ASYNC-001",
            semantic_units=[make_semantic_unit()],
            total_est_complexity=10,
        )
        mock_planning_agent.execute_async.return_value = mock_plan

        # Mock design agent response
        mock_design = make_design_specification(
            task_id="ASYNC-001",
            api_contracts=[
                APIContract(
                    endpoint="/hello",
                    method="GET",
                    description="Hello endpoint for async testing",
                    request_schema={},
                    response_schema={"type": "object"},
                    semantic_unit_id="SU-001",
                )
            ],
        )
        mock_design_agent.execute_async.return_value = mock_design

        # Mock design review response - PASS on first try
        mock_review = DesignReviewReport(
            task_id="ASYNC-001",
            review_id="REVIEW-ASYNC-20251217-120000",
            design_id="DESIGN-001",
            overall_assessment="PASS",
            automated_checks={"semantic_coverage": True},
            issues_found=[],
            improvement_suggestions=[],
            checklist_review=make_checklist_review(1),
            critical_issue_count=0,
            high_issue_count=0,
            medium_issue_count=0,
            low_issue_count=0,
            reviewer_agent="DesignReviewAgent",
            agent_version="1.0.0",
        )
        mock_review_agent.execute_async.return_value = mock_review

        # Execute async orchestrator
        result = await orchestrator.execute_async(requirements)

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

        # Verify async agents called correct number of times
        assert mock_planning_agent.execute_async.call_count == 1
        assert mock_design_agent.execute_async.call_count == 1
        assert mock_review_agent.execute_async.call_count == 1

    @pytest.mark.asyncio
    async def test_async_design_feedback_loop(self):
        """Test async orchestrator with design-phase issues requiring redesign."""
        from unittest.mock import AsyncMock

        orchestrator = PlanningDesignOrchestrator()

        # Mock the agents with async support
        mock_planning_agent = Mock()
        mock_design_agent = Mock()
        mock_review_agent = Mock()

        mock_planning_agent.execute_async = AsyncMock()
        mock_design_agent.execute_async = AsyncMock()
        mock_review_agent.execute_async = AsyncMock()

        orchestrator._planning_agent = mock_planning_agent
        orchestrator._design_agent = mock_design_agent
        orchestrator._design_review_agent = mock_review_agent

        requirements = TaskRequirements(
            project_id="TEST-ASYNC-002",
            task_id="ASYNC-FEEDBACK-001",
            description="Test async feedback loop",
            requirements="Build API with feedback",
        )

        # Mock planning agent
        mock_plan = ProjectPlan(
            project_id="TEST-ASYNC-002",
            task_id="ASYNC-FEEDBACK-001",
            semantic_units=[
                make_semantic_unit(
                    description="Create API endpoint with async feedback handling"
                )
            ],
            total_est_complexity=10,
        )
        mock_planning_agent.execute_async.return_value = mock_plan

        # Mock design agent - returns two different designs
        mock_design_v1 = make_design_specification(
            task_id="ASYNC-FEEDBACK-001",
            api_contracts=[],  # Missing API contracts
        )

        mock_design_v2 = make_design_specification(
            task_id="ASYNC-FEEDBACK-001",
            api_contracts=[
                APIContract(
                    endpoint="/api",
                    method="GET",
                    description="API endpoint for async testing",
                    request_schema={},
                    response_schema={"type": "object"},
                    semantic_unit_id="SU-001",
                )
            ],
        )

        mock_design_agent.execute_async.side_effect = [mock_design_v1, mock_design_v2]

        # Mock review agent - first FAIL, then PASS
        design_issue = DesignIssue(
            issue_id="ISSUE-001",
            category="API Design",
            severity="High",
            description="Missing API endpoint definition",
            affected_component="API",
            evidence="No API contracts defined",
            impact="Cannot generate code without API contracts",
            recommendation="Add API contract specifications",
        )

        mock_review_fail = DesignReviewReport(
            task_id="ASYNC-FEEDBACK-001",
            review_id="REVIEW-ASYNC-20251217-120000",
            design_id="DESIGN-001",
            overall_assessment="FAIL",
            automated_checks={"semantic_coverage": True},
            issues_found=[design_issue],
            improvement_suggestions=[],
            checklist_review=make_checklist_review(1),
            critical_issue_count=0,
            high_issue_count=1,
            medium_issue_count=0,
            low_issue_count=0,
            reviewer_agent="DesignReviewAgent",
            agent_version="1.0.0",
        )

        mock_review_pass = DesignReviewReport(
            task_id="ASYNC-FEEDBACK-001",
            review_id="REVIEW-ASYNC-20251217-120001",
            design_id="DESIGN-002",
            overall_assessment="PASS",
            automated_checks={"semantic_coverage": True},
            issues_found=[],
            improvement_suggestions=[],
            checklist_review=make_checklist_review(1),
            critical_issue_count=0,
            high_issue_count=0,
            medium_issue_count=0,
            low_issue_count=0,
            reviewer_agent="DesignReviewAgent",
            agent_version="1.0.0",
        )

        mock_review_agent.execute_async.side_effect = [
            mock_review_fail,
            mock_review_pass,
        ]

        # Execute async orchestrator
        result = await orchestrator.execute_async(requirements)

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

        # Verify async feedback loop executed
        assert mock_planning_agent.execute_async.call_count == 1
        assert mock_design_agent.execute_async.call_count == 2
        assert mock_review_agent.execute_async.call_count == 2

        # Verify second design call had feedback
        second_design_call = mock_design_agent.execute_async.call_args_list[1]
        assert second_design_call[1].get("feedback") == [design_issue]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
