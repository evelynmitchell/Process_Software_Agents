"""
Planning-Design-Review Orchestrator with Phase-Aware Feedback.

Implements Option 2 from error_correction_feedback_loops_decision.md:
- Coordinates Planning → Design → Design Review with feedback loops
- Routes issues back to appropriate phase (Planning or Design)
- Prevents error propagation through pipeline
- Maintains audit trail for PROBE-AI learning

Author: ASP Development Team
Date: November 19, 2025
"""

import logging
from pathlib import Path
from typing import Any, Optional

from asp.agents.base_agent import AgentExecutionError
from asp.agents.design_agent import DesignAgent
from asp.agents.design_review_agent import DesignReviewAgent
from asp.agents.planning_agent import PlanningAgent
from asp.models.design import DesignInput, DesignSpecification
from asp.models.design_review import DesignReviewReport
from asp.models.planning import ProjectPlan, TaskRequirements


logger = logging.getLogger(__name__)


class MaxIterationsExceeded(Exception):
    """Raised when orchestrator exceeds maximum correction iterations."""

    pass


class PlanningDesignOrchestrator:
    """
    Orchestrates Planning → Design → Design Review with phase-aware feedback loops.

    Implements PSP principle: fix defects in the phase where they were injected.

    Features:
    - Analyzes DesignReviewReport to identify which phase introduced issues
    - Routes Planning-phase issues back to Planning Agent
    - Routes Design-phase issues back to Design Agent
    - Prevents infinite loops with iteration limits
    - Maintains full audit trail for telemetry

    Example:
        >>> orchestrator = PlanningDesignOrchestrator()
        >>> requirements = TaskRequirements(...)
        >>> design_spec, review = orchestrator.execute(requirements)
        >>> print(f"Design passed review: {review.overall_assessment == 'PASS'}")
    """

    # Maximum iterations per phase
    MAX_PLANNING_ITERATIONS = 3
    MAX_DESIGN_ITERATIONS = 3
    MAX_TOTAL_ITERATIONS = 10

    def __init__(
        self,
        db_path: Optional[Path] = None,
        llm_client: Optional[Any] = None,
    ):
        """
        Initialize orchestrator with agents.

        Args:
            db_path: Optional path to SQLite database for telemetry
            llm_client: Optional LLM client (for dependency injection in tests)
        """
        self.db_path = db_path
        self.llm_client = llm_client

        # Initialize agents (lazy - only create when needed)
        self._planning_agent: Optional[PlanningAgent] = None
        self._design_agent: Optional[DesignAgent] = None
        self._design_review_agent: Optional[DesignReviewAgent] = None

        logger.info("PlanningDesignOrchestrator initialized")

    @property
    def planning_agent(self) -> PlanningAgent:
        """Lazy-load Planning Agent."""
        if self._planning_agent is None:
            self._planning_agent = PlanningAgent(
                db_path=self.db_path,
                llm_client=self.llm_client,
            )
        return self._planning_agent

    @property
    def design_agent(self) -> DesignAgent:
        """Lazy-load Design Agent."""
        if self._design_agent is None:
            self._design_agent = DesignAgent(
                db_path=self.db_path,
                llm_client=self.llm_client,
            )
        return self._design_agent

    @property
    def design_review_agent(self) -> DesignReviewAgent:
        """Lazy-load Design Review Agent."""
        if self._design_review_agent is None:
            self._design_review_agent = DesignReviewAgent(
                db_path=self.db_path,
                llm_client=self.llm_client,
            )
        return self._design_review_agent

    def execute(
        self,
        requirements: TaskRequirements,
        design_constraints: Optional[str] = None,
    ) -> tuple[DesignSpecification, DesignReviewReport]:
        """
        Execute Planning → Design → Design Review with feedback loops.

        This method:
        1. Generates initial plan (Planning Agent)
        2. Generates design from plan (Design Agent)
        3. Reviews design (Design Review Agent)
        4. If issues found:
           - Routes planning-phase issues → Planning Agent
           - Routes design-phase issues → Design Agent
           - Regenerates affected artifacts
           - Re-reviews design
        5. Repeats until PASS or max iterations exceeded

        Args:
            requirements: TaskRequirements with task description
            design_constraints: Optional design constraints/standards

        Returns:
            Tuple of (DesignSpecification, DesignReviewReport) where
            review.overall_assessment is "PASS" or "NEEDS_IMPROVEMENT"

        Raises:
            MaxIterationsExceeded: If cannot resolve issues within iteration limits
            AgentExecutionError: If agent execution fails
        """
        logger.info(
            f"Starting orchestrated Planning→Design→Review for task {requirements.task_id}"
        )

        # Iteration tracking
        planning_iterations = 0
        design_iterations = 0
        total_iterations = 0

        # Initial planning (no feedback)
        project_plan = self._execute_planning(requirements, feedback=None)
        planning_iterations += 1
        total_iterations += 1

        # Feedback loop: Design → Review → Corrections
        while total_iterations < self.MAX_TOTAL_ITERATIONS:
            # Generate design from current plan
            design_spec = self._execute_design(
                requirements, project_plan, design_constraints, feedback=None
            )
            design_iterations += 1
            total_iterations += 1

            # Review design
            review_report = self._execute_design_review(design_spec)
            total_iterations += 1

            # Check if design passes
            if review_report.overall_assessment == "PASS":
                logger.info(
                    f"Design passed review after {total_iterations} total iterations "
                    f"(planning={planning_iterations}, design={design_iterations})"
                )
                return design_spec, review_report

            # Check if only NEEDS_IMPROVEMENT (Medium/Low issues)
            if review_report.overall_assessment == "NEEDS_IMPROVEMENT":
                logger.info(
                    f"Design has minor improvements suggested, but acceptable "
                    f"(planning={planning_iterations}, design={design_iterations})"
                )
                return design_spec, review_report

            # Design FAILED - analyze issues and route feedback
            logger.warning(
                f"Design review FAILED: "
                f"{review_report.critical_issue_count} critical, "
                f"{review_report.high_issue_count} high severity issues"
            )

            # Route issues to appropriate phase
            needs_replanning = len(review_report.planning_phase_issues) > 0
            needs_redesign = len(review_report.design_phase_issues) > 0
            has_multi_phase = len(review_report.multi_phase_issues) > 0

            # Check iteration limits before attempting corrections
            if needs_replanning and planning_iterations >= self.MAX_PLANNING_ITERATIONS:
                raise MaxIterationsExceeded(
                    f"Exceeded max planning iterations ({self.MAX_PLANNING_ITERATIONS}). "
                    f"Planning phase issues: {len(review_report.planning_phase_issues)}"
                )

            if needs_redesign and design_iterations >= self.MAX_DESIGN_ITERATIONS:
                raise MaxIterationsExceeded(
                    f"Exceeded max design iterations ({self.MAX_DESIGN_ITERATIONS}). "
                    f"Design phase issues: {len(review_report.design_phase_issues)}"
                )

            # Execute corrections based on phase attribution
            if needs_replanning or has_multi_phase:
                # Planning issues require replanning
                feedback_issues = (
                    review_report.planning_phase_issues
                    + review_report.multi_phase_issues
                )
                logger.info(
                    f"Routing {len(feedback_issues)} issues back to Planning Agent"
                )
                project_plan = self._execute_planning(requirements, feedback=feedback_issues)
                planning_iterations += 1
                total_iterations += 1

                # After replanning, must regenerate design
                logger.info("Regenerating design with updated plan")
                design_iterations = 0  # Reset design iteration count

            elif needs_redesign:
                # Design-only issues can be fixed without replanning
                feedback_issues = review_report.design_phase_issues
                logger.info(
                    f"Routing {len(feedback_issues)} issues back to Design Agent"
                )
                design_spec = self._execute_design(
                    requirements, project_plan, design_constraints, feedback=feedback_issues
                )
                design_iterations += 1
                total_iterations += 1

                # Re-review the updated design
                review_report = self._execute_design_review(design_spec)
                total_iterations += 1

                if review_report.overall_assessment in ["PASS", "NEEDS_IMPROVEMENT"]:
                    logger.info(f"Design passed review after redesign")
                    return design_spec, review_report

            else:
                # No phase-specific issues identified - treat as design issue by default
                logger.warning(
                    "No phase attribution found for issues, defaulting to Design phase"
                )
                feedback_issues = review_report.issues_found
                design_spec = self._execute_design(
                    requirements, project_plan, design_constraints, feedback=feedback_issues
                )
                design_iterations += 1
                total_iterations += 1

        # Exceeded max total iterations
        raise MaxIterationsExceeded(
            f"Exceeded max total iterations ({self.MAX_TOTAL_ITERATIONS}). "
            f"Final review status: {review_report.overall_assessment}, "
            f"Critical issues: {review_report.critical_issue_count}, "
            f"High issues: {review_report.high_issue_count}"
        )

    def _execute_planning(
        self,
        requirements: TaskRequirements,
        feedback: Optional[list] = None,
    ) -> ProjectPlan:
        """Execute Planning Agent with optional feedback."""
        try:
            if feedback:
                logger.info(f"Planning Agent: executing with {len(feedback)} feedback items")
            else:
                logger.info(f"Planning Agent: executing initial planning")

            project_plan = self.planning_agent.execute(requirements, feedback=feedback)

            logger.info(
                f"Planning complete: {len(project_plan.semantic_units)} units, "
                f"complexity {project_plan.total_est_complexity}"
            )
            return project_plan

        except Exception as e:
            logger.error(f"Planning Agent failed: {e}")
            raise AgentExecutionError(f"Planning Agent execution failed: {e}") from e

    def _execute_design(
        self,
        requirements: TaskRequirements,
        project_plan: ProjectPlan,
        design_constraints: Optional[str],
        feedback: Optional[list] = None,
    ) -> DesignSpecification:
        """Execute Design Agent with optional feedback."""
        try:
            if feedback:
                logger.info(f"Design Agent: executing with {len(feedback)} feedback items")
            else:
                logger.info(f"Design Agent: executing initial design")

            design_input = DesignInput(
                task_id=requirements.task_id,
                requirements=requirements.requirements,
                project_plan=project_plan,
                design_constraints=design_constraints or "",
            )

            design_spec = self.design_agent.execute(design_input, feedback=feedback)

            logger.info(
                f"Design complete: {len(design_spec.api_contracts)} APIs, "
                f"{len(design_spec.component_logic)} components"
            )
            return design_spec

        except Exception as e:
            logger.error(f"Design Agent failed: {e}")
            raise AgentExecutionError(f"Design Agent execution failed: {e}") from e

    def _execute_design_review(
        self,
        design_spec: DesignSpecification,
    ) -> DesignReviewReport:
        """Execute Design Review Agent."""
        try:
            logger.info(f"Design Review Agent: reviewing design for {design_spec.task_id}")

            review_report = self.design_review_agent.execute(design_spec)

            logger.info(
                f"Design review complete: {review_report.overall_assessment}, "
                f"issues: {len(review_report.issues_found)} total, "
                f"{review_report.critical_issue_count} critical, "
                f"{review_report.high_issue_count} high"
            )

            if review_report.planning_phase_issues:
                logger.info(
                    f"  → {len(review_report.planning_phase_issues)} planning-phase issues"
                )
            if review_report.design_phase_issues:
                logger.info(
                    f"  → {len(review_report.design_phase_issues)} design-phase issues"
                )
            if review_report.multi_phase_issues:
                logger.info(
                    f"  → {len(review_report.multi_phase_issues)} multi-phase issues"
                )

            return review_report

        except Exception as e:
            logger.error(f"Design Review Agent failed: {e}")
            raise AgentExecutionError(f"Design Review Agent execution failed: {e}") from e
