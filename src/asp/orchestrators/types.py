"""
Orchestrator result types.

Defines result dataclasses for orchestrator return values to maintain
complete artifact traceability through the pipeline.

Author: ASP Development Team
Date: November 20, 2025
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from asp.models.code import GeneratedCode
from asp.models.code_review import CodeReviewReport
from asp.models.design import DesignSpecification
from asp.models.design_review import DesignReviewReport
from asp.models.planning import ProjectPlan
from asp.models.postmortem import PostmortemReport
from asp.models.test import TestReport


@dataclass
class PlanningDesignResult:
    """
    Result from Planning-Design-Review orchestration.

    Contains all three artifacts generated during orchestration:
    - ProjectPlan: From Planning Agent
    - DesignSpecification: From Design Agent
    - DesignReviewReport: From Design Review Agent

    This allows callers to access all artifacts for downstream use,
    particularly the ProjectPlan which is needed by Postmortem Agent.

    Example:
        >>> orchestrator = PlanningDesignOrchestrator()
        >>> result = orchestrator.execute(requirements)
        >>> project_plan = result.project_plan
        >>> design_spec = result.design_specification
        >>> design_review = result.design_review
    """

    project_plan: ProjectPlan
    design_specification: DesignSpecification
    design_review: DesignReviewReport


@dataclass
class TSPExecutionResult:
    """
    Result from complete TSP Orchestrator execution.

    Contains all artifacts generated during the complete autonomous development pipeline:
    - ProjectPlan: From Planning Agent
    - DesignSpecification: From Design Agent
    - DesignReviewReport: From Design Review Orchestrator
    - GeneratedCode: From Code Agent
    - CodeReviewReport: From Code Review Orchestrator
    - TestReport: From Test Agent
    - PostmortemReport: From Postmortem Agent

    Also includes execution metadata:
    - execution_log: List of phase execution events
    - hitl_overrides: List of HITL approval decisions
    - total_duration_seconds: Total pipeline execution time
    - overall_status: PASS/CONDITIONAL_PASS/FAIL/NEEDS_REVIEW

    Example:
        >>> orchestrator = TSPOrchestrator()
        >>> result = orchestrator.execute(requirements)
        >>> print(f"Status: {result.overall_status}")
        >>> print(f"Files: {result.generated_code.total_files}")
        >>> print(f"Tests: {result.test_report.tests_passed}/{result.test_report.total_tests}")
        >>> print(f"PIPs: {len(result.postmortem_report.process_improvement_proposals)}")
    """

    # Artifact identification
    task_id: str
    timestamp: datetime

    # Execution status
    overall_status: str  # PASS, CONDITIONAL_PASS, FAIL, NEEDS_REVIEW

    # Phase artifacts (in pipeline order)
    project_plan: ProjectPlan
    design_specification: DesignSpecification
    design_review: DesignReviewReport
    generated_code: GeneratedCode
    code_review: CodeReviewReport
    test_report: TestReport
    postmortem_report: PostmortemReport

    # Execution metadata
    execution_log: list[dict[str, Any]]
    hitl_overrides: list[dict[str, Any]]
    total_duration_seconds: float
