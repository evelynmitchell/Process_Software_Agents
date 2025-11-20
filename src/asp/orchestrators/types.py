"""
Orchestrator result types.

Defines result dataclasses for orchestrator return values to maintain
complete artifact traceability through the pipeline.

Author: ASP Development Team
Date: November 20, 2025
"""

from dataclasses import dataclass

from asp.models.design import DesignSpecification
from asp.models.design_review import DesignReviewReport
from asp.models.planning import ProjectPlan


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
