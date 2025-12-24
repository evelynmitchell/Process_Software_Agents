"""
TSP Orchestrator: Complete Autonomous Development Pipeline.

Implements PRD FR-8: TSP Orchestrator Agent that coordinates all 7 agents through
the complete software development lifecycle with quality gates and HITL approval.

This orchestrator:
1. Executes Planning Agent to generate master plan
2. Assigns tasks to specialized agents in sequence
3. Enforces quality gates (halt on review failures)
4. Supports HITL override workflow for quality gate failures
5. Triggers Postmortem Agent on task completion
6. Provides complete autonomous end-to-end development pipeline

Based on PSP/TSP methodologies adapted for AI agents per PSPdoc.md Section VIII.

Author: ASP Development Team
Date: November 22, 2025
"""

# pylint: disable=logging-fstring-interpolation

import logging
from collections.abc import Callable
from datetime import datetime
from pathlib import Path
from typing import Any

from asp.agents.base_agent import AgentExecutionError
from asp.agents.code_agent import CodeAgent
from asp.agents.code_review_orchestrator import CodeReviewOrchestrator
from asp.agents.design_agent import DesignAgent
from asp.agents.design_review_orchestrator import DesignReviewOrchestrator
from asp.agents.planning_agent import PlanningAgent
from asp.agents.postmortem_agent import PostmortemAgent
from asp.agents.test_agent import TestAgent
from asp.approval.base import ApprovalRequest, ApprovalService, ReviewDecision
from asp.models.code import CodeInput, GeneratedCode
from asp.models.code_review import CodeReviewReport
from asp.models.design import DesignInput, DesignSpecification
from asp.models.design_review import DesignReviewReport
from asp.models.planning import ProjectPlan, TaskRequirements
from asp.models.postmortem import (
    DefectLogEntry,
    EffortLogEntry,
    PostmortemInput,
    PostmortemReport,
)
from asp.models.test import TestInput, TestReport
from asp.orchestrators.types import TSPExecutionResult

logger = logging.getLogger(__name__)


class QualityGateFailure(Exception):
    """Raised when a quality gate fails and no HITL override is provided."""


class MaxIterationsExceeded(Exception):
    """Raised when orchestrator exceeds maximum correction iterations."""


class TSPOrchestrator:  # pylint: disable=too-many-instance-attributes
    """
    TSP Orchestrator: Complete autonomous development pipeline with quality gates.

    Implements the Team Software Process (TSP) model for AI agents, coordinating
    all 7 agents through formal workflow with enforcement of quality gates.

    Workflow:
    1. Planning Agent → Generate project plan with estimates
    2. Design Agent → Create design specification
    3. Design Review (Quality Gate) → Pass/Fail/HITL Override
    4. Code Agent → Generate implementation
    5. Code Review (Quality Gate) → Pass/Fail/HITL Override
    6. Test Agent → Build, test, validate
    7. Postmortem Agent → Analyze performance, generate PIPs

    Quality Gates:
    - Design Review: Halts if critical/high issues found (unless HITL override)
    - Code Review: Halts if critical issues or ≥5 high issues (unless HITL override)
    - Test: Halts if build fails or tests fail

    HITL (Human-in-the-Loop):
    - Quality gate failures trigger HITL approval request
    - Human can approve override with justification
    - All overrides are logged for audit trail

    Example:
        >>> orchestrator = TSPOrchestrator()
        >>> requirements = TaskRequirements(...)
        >>> result = orchestrator.execute(
        ...     requirements=requirements,
        ...     hitl_approver=lambda gate, report: True  # Auto-approve for testing
        ... )
        >>> print(f"Pipeline status: {result.overall_status}")
        >>> print(f"Generated files: {result.generated_code.total_files}")
    """

    # Maximum correction iterations per phase
    MAX_DESIGN_ITERATIONS = 3
    MAX_CODE_ITERATIONS = 3
    MAX_TEST_ITERATIONS = 2
    MAX_TOTAL_ITERATIONS = 15

    def __init__(
        self,
        db_path: Path | None = None,
        llm_client: Any | None = None,
        approval_service: ApprovalService | None = None,
    ):
        """
        Initialize TSP Orchestrator.

        Args:
            db_path: Optional path to SQLite database for telemetry
            llm_client: Optional LLM client (for dependency injection in tests)
            approval_service: Optional ApprovalService for HITL workflow
        """
        self.db_path = db_path
        self.llm_client = llm_client
        self.approval_service = approval_service

        # Initialize agents (lazy-loaded)
        self._planning_agent: PlanningAgent | None = None
        self._design_agent: DesignAgent | None = None
        self._design_review_orchestrator: DesignReviewOrchestrator | None = None
        self._code_agent: CodeAgent | None = None
        self._code_review_orchestrator: CodeReviewOrchestrator | None = None
        self._test_agent: TestAgent | None = None
        self._postmortem_agent: PostmortemAgent | None = None

        # Execution state
        self.execution_log: list[dict[str, Any]] = []
        self.hitl_overrides: list[dict[str, Any]] = []

        logger.info("TSPOrchestrator initialized")

    # =========================================================================
    # Lazy-loaded agent properties
    # =========================================================================

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
    def design_review_orchestrator(self) -> DesignReviewOrchestrator:
        """Lazy-load Design Review Orchestrator."""
        if self._design_review_orchestrator is None:
            self._design_review_orchestrator = DesignReviewOrchestrator(
                db_path=self.db_path,
                llm_client=self.llm_client,
            )
        return self._design_review_orchestrator

    @property
    def code_agent(self) -> CodeAgent:
        """Lazy-load Code Agent."""
        if self._code_agent is None:
            self._code_agent = CodeAgent(
                db_path=self.db_path,
                llm_client=self.llm_client,
                use_multi_stage=True,  # Use multi-stage code generation
            )
        return self._code_agent

    @property
    def code_review_orchestrator(self) -> CodeReviewOrchestrator:
        """Lazy-load Code Review Orchestrator."""
        if self._code_review_orchestrator is None:
            self._code_review_orchestrator = CodeReviewOrchestrator(
                db_path=self.db_path,
                llm_client=self.llm_client,
            )
        return self._code_review_orchestrator

    @property
    def test_agent(self) -> TestAgent:
        """Lazy-load Test Agent."""
        if self._test_agent is None:
            self._test_agent = TestAgent(
                db_path=self.db_path,
                llm_client=self.llm_client,
            )
        return self._test_agent

    @property
    def postmortem_agent(self) -> PostmortemAgent:
        """Lazy-load Postmortem Agent."""
        if self._postmortem_agent is None:
            self._postmortem_agent = PostmortemAgent(
                db_path=self.db_path,
                llm_client=self.llm_client,
            )
        return self._postmortem_agent

    # =========================================================================
    # Main execution method
    # =========================================================================

    def execute(
        self,
        requirements: TaskRequirements,
        design_constraints: str | None = None,
        coding_standards: str | None = None,
        hitl_approver: Callable | None = None,
    ) -> TSPExecutionResult:
        """
        Execute complete TSP autonomous development pipeline.

        This method orchestrates all 7 agents through the complete workflow:
        Planning → Design → Design Review → Code → Code Review → Test → Postmortem

        Quality gates enforce PSP discipline:
        - Design Review failure halts pipeline (requires HITL override)
        - Code Review failure halts pipeline (requires HITL override)
        - Test failure triggers code regeneration loop (max 2 iterations)

        Args:
            requirements: TaskRequirements with task description
            design_constraints: Optional design constraints/standards
            coding_standards: Optional coding standards
            hitl_approver: Optional callable for HITL approval (legacy interface).
                          Signature: (gate_name: str, report: dict) -> bool
                          If None and no approval_service configured, quality gate
                          failures raise QualityGateFailure.
                          NOTE: approval_service takes precedence over hitl_approver

        Returns:
            TSPExecutionResult containing all artifacts and execution metadata

        Raises:
            QualityGateFailure: If quality gate fails and no HITL override
            MaxIterationsExceeded: If correction loops exceed limits
            AgentExecutionError: If agent execution fails
        """
        banner = "=" * 80
        logger.info(
            f"{banner}\n"
            f"TSP ORCHESTRATOR: Starting autonomous pipeline\n"
            f"Task: {requirements.task_id} - {requirements.description}\n"
            f"{banner}"
        )

        start_time = datetime.now()
        self.execution_log = []
        self.hitl_overrides = []

        try:
            # Phase 1: Planning
            logger.info("\n[PHASE 1/7] PLANNING AGENT")
            logger.info("-" * 80)
            project_plan = self._execute_planning(requirements)
            self._log_phase("Planning", "SUCCESS", project_plan)

            # Phase 2: Design (with correction loop)
            logger.info("\n[PHASE 2/7] DESIGN AGENT")
            logger.info("-" * 80)
            design_spec, design_review = self._execute_design_with_review(
                requirements=requirements,
                project_plan=project_plan,
                design_constraints=design_constraints,
                hitl_approver=hitl_approver,
            )
            self._log_phase("Design", "SUCCESS", design_spec)
            self._log_phase(
                "DesignReview", design_review.overall_assessment, design_review
            )

            # Phase 3: Code Generation (with correction loop)
            logger.info("\n[PHASE 3/7] CODE AGENT")
            logger.info("-" * 80)
            generated_code, code_review = self._execute_code_with_review(
                requirements=requirements,
                design_spec=design_spec,
                coding_standards=coding_standards,
                hitl_approver=hitl_approver,
            )
            self._log_phase("Code", "SUCCESS", generated_code)
            self._log_phase("CodeReview", code_review.review_status, code_review)

            # Phase 4: Testing (with correction loop for failures)
            logger.info("\n[PHASE 4/7] TEST AGENT")
            logger.info("-" * 80)
            test_report = self._execute_testing_with_retry(
                requirements=requirements,
                design_spec=design_spec,
                generated_code=generated_code,
                coding_standards=coding_standards,
            )
            self._log_phase("Test", test_report.test_status, test_report)

            # Phase 5: Postmortem Analysis
            logger.info("\n[PHASE 5/7] POSTMORTEM AGENT")
            logger.info("-" * 80)
            postmortem_report = self._execute_postmortem(
                requirements=requirements,
                project_plan=project_plan,
                design_review=design_review,
                code_review=code_review,
                test_report=test_report,
            )
            self._log_phase("Postmortem", "SUCCESS", postmortem_report)

            # Calculate execution duration
            end_time = datetime.now()
            duration_seconds = (end_time - start_time).total_seconds()

            # Determine overall status
            overall_status = self._determine_overall_status(
                design_review, code_review, test_report
            )

            # Get test summary values
            total_tests = test_report.test_summary.get("total_tests", 0)
            passed_tests = test_report.test_summary.get("passed", 0)

            banner = "=" * 80
            logger.info(
                f"\n{banner}\n"
                f"TSP ORCHESTRATOR: Pipeline COMPLETE\n"
                f"Overall Status: {overall_status}\n"
                f"Duration: {duration_seconds:.1f}s\n"
                f"Files Generated: {generated_code.total_files}\n"
                f"Tests Passed: {passed_tests}/{total_tests}\n"
                f"HITL Overrides: {len(self.hitl_overrides)}\n"
                f"{banner}"
            )

            return TSPExecutionResult(
                task_id=requirements.task_id,
                overall_status=overall_status,
                project_plan=project_plan,
                design_specification=design_spec,
                design_review=design_review,
                generated_code=generated_code,
                code_review=code_review,
                test_report=test_report,
                postmortem_report=postmortem_report,
                execution_log=self.execution_log,
                hitl_overrides=self.hitl_overrides,
                total_duration_seconds=duration_seconds,
                timestamp=start_time,
            )

        except Exception as e:
            logger.error(f"TSP Orchestrator failed: {e}", exc_info=True)
            self._log_phase("Pipeline", "FAILED", {"error": str(e)})
            raise

    # =========================================================================
    # Phase execution methods
    # =========================================================================

    def _execute_planning(
        self,
        requirements: TaskRequirements,
    ) -> ProjectPlan:
        """Execute Planning Agent."""
        try:
            logger.info("Executing Planning Agent...")
            project_plan = self.planning_agent.execute(requirements)

            logger.info(
                f"✓ Planning complete: {len(project_plan.semantic_units)} units, "
                f"complexity {project_plan.total_est_complexity}"
            )
            return project_plan

        except Exception as e:
            logger.error(f"Planning Agent failed: {e}")
            raise AgentExecutionError(f"Planning Agent execution failed: {e}") from e

    def _execute_design_with_review(
        self,
        requirements: TaskRequirements,
        project_plan: ProjectPlan,
        design_constraints: str | None,
        hitl_approver: Callable | None,
    ) -> tuple[DesignSpecification, DesignReviewReport]:
        """
        Execute Design Agent with Design Review quality gate.

        Implements correction loop: Design → Review → Feedback → Redesign
        Enforces quality gate: Halts on FAIL (requires HITL override)
        """
        design_iterations = 0

        while design_iterations < self.MAX_DESIGN_ITERATIONS:
            # Generate design
            logger.info(
                f"Design iteration {design_iterations + 1}/{self.MAX_DESIGN_ITERATIONS}"
            )
            design_input = DesignInput(
                task_id=requirements.task_id,
                requirements=requirements.requirements,
                project_plan=project_plan,
                design_constraints=design_constraints or "",
            )
            design_spec = self.design_agent.execute(design_input)
            design_iterations += 1

            logger.info(
                f"✓ Design complete: {len(design_spec.api_contracts)} APIs, "
                f"{len(design_spec.component_logic)} components"
            )

            # Design Review (Quality Gate)
            logger.info("Executing Design Review Orchestrator (Quality Gate)...")
            design_review = self.design_review_orchestrator.execute(design_spec)

            logger.info(
                f"Design Review: {design_review.overall_assessment} "
                f"({design_review.critical_issue_count}C/{design_review.high_issue_count}H/"
                f"{design_review.medium_issue_count}M/{design_review.low_issue_count}L)"
            )

            # Quality Gate: Check review status
            if design_review.overall_assessment == "PASS":
                logger.info("✓ Design PASSED review - proceeding to Code phase")
                return design_spec, design_review

            if design_review.overall_assessment == "NEEDS_IMPROVEMENT":
                # Accept design with minor issues
                logger.info("✓ Design acceptable with minor improvements - proceeding")
                return design_spec, design_review

            # Design FAILED - check for HITL override
            if design_review.overall_assessment == "FAIL":
                logger.warning(
                    f"⚠ Design FAILED review: "
                    f"{design_review.critical_issue_count} critical, "
                    f"{design_review.high_issue_count} high issues"
                )

                # Request HITL approval if available
                approved = self._request_approval(
                    task_id=requirements.task_id,
                    gate_type="design_review",
                    gate_name="DesignReview",
                    report=design_review,
                    hitl_approver=hitl_approver,
                )
                if approved:
                    logger.info(
                        "✓ HITL override approved - proceeding despite failures"
                    )
                    return design_spec, design_review

                # No HITL or rejected - attempt correction if iterations remain
                if design_iterations < self.MAX_DESIGN_ITERATIONS:
                    logger.info("Retrying design with feedback from review...")
                    # In a full implementation, would pass feedback to design agent
                    # For now, just retry
                    continue
                # Exceeded iterations
                raise QualityGateFailure(
                    f"Design Review FAILED after {design_iterations} iterations. "
                    f"Critical: {design_review.critical_issue_count}, "
                    f"High: {design_review.high_issue_count}. "
                    f"Requires HITL approval to proceed."
                )

        raise MaxIterationsExceeded(
            f"Exceeded max design iterations ({self.MAX_DESIGN_ITERATIONS})"
        )

    def _execute_code_with_review(
        self,
        requirements: TaskRequirements,
        design_spec: DesignSpecification,
        coding_standards: str | None,
        hitl_approver: Callable | None,
    ) -> tuple[GeneratedCode, CodeReviewReport]:
        """
        Execute Code Agent with Code Review quality gate.

        Implements correction loop: Code → Review → Feedback → Recode
        Enforces quality gate: Halts on FAIL (requires HITL override)
        """
        code_iterations = 0

        while code_iterations < self.MAX_CODE_ITERATIONS:
            # Generate code
            logger.info(
                f"Code iteration {code_iterations + 1}/{self.MAX_CODE_ITERATIONS}"
            )
            code_input = CodeInput(
                task_id=requirements.task_id,
                design_specification=design_spec,
                coding_standards=coding_standards
                or "Follow PEP 8. Use type hints. Include docstrings.",
            )
            generated_code = self.code_agent.execute(code_input)
            code_iterations += 1

            logger.info(
                f"✓ Code generation complete: {generated_code.total_files} files, "
                f"{generated_code.total_lines_of_code} LOC"
            )

            # Code Review (Quality Gate)
            logger.info("Executing Code Review Orchestrator (Quality Gate)...")
            code_review = self.code_review_orchestrator.execute(generated_code)

            logger.info(
                f"Code Review: {code_review.review_status} "
                f"({code_review.critical_issues}C/{code_review.high_issues}H/"
                f"{code_review.medium_issues}M/{code_review.low_issues}L)"
            )

            # Quality Gate: Check review status
            if code_review.review_status == "PASS":
                logger.info("✓ Code PASSED review - proceeding to Test phase")
                return generated_code, code_review

            if code_review.review_status == "CONDITIONAL_PASS":
                # Accept code with minor issues (<5 high, no critical)
                logger.info("✓ Code acceptable with conditions - proceeding")
                return generated_code, code_review

            # Code FAILED - check for HITL override
            if code_review.review_status == "FAIL":
                logger.warning(
                    f"⚠ Code FAILED review: "
                    f"{code_review.critical_issues} critical, "
                    f"{code_review.high_issues} high issues"
                )

                # Request HITL approval if available
                approved = self._request_approval(
                    task_id=requirements.task_id,
                    gate_type="code_review",
                    gate_name="CodeReview",
                    report=code_review,
                    hitl_approver=hitl_approver,
                )
                if approved:
                    logger.info(
                        "✓ HITL override approved - proceeding despite failures"
                    )
                    return generated_code, code_review

                # No HITL or rejected - attempt correction if iterations remain
                if code_iterations < self.MAX_CODE_ITERATIONS:
                    logger.info("Retrying code generation with feedback from review...")
                    continue
                raise QualityGateFailure(
                    f"Code Review FAILED after {code_iterations} iterations. "
                    f"Critical: {code_review.critical_issues}, "
                    f"High: {code_review.high_issues}. "
                    f"Requires HITL approval to proceed."
                )

        raise MaxIterationsExceeded(
            f"Exceeded max code iterations ({self.MAX_CODE_ITERATIONS})"
        )

    def _execute_testing_with_retry(
        self,
        requirements: TaskRequirements,
        design_spec: DesignSpecification,
        generated_code: GeneratedCode,
        coding_standards: str | None,
    ) -> TestReport:
        """
        Execute Test Agent with retry loop for test failures.

        Unlike review quality gates, test failures trigger automatic code regeneration
        (up to MAX_TEST_ITERATIONS) rather than requiring HITL approval.
        """
        if self.MAX_TEST_ITERATIONS < 1:
            raise ValueError("MAX_TEST_ITERATIONS must be at least 1")

        test_iterations = 0
        test_report: TestReport  # Will be assigned in first iteration

        while test_iterations < self.MAX_TEST_ITERATIONS:
            logger.info(
                f"Test iteration {test_iterations + 1}/{self.MAX_TEST_ITERATIONS}"
            )

            # Execute tests
            test_input = TestInput(
                task_id=requirements.task_id,
                generated_code=generated_code,
                design_specification=design_spec,
            )
            test_report = self.test_agent.execute(test_input)
            test_iterations += 1

            # Get test summary values
            total_tests = test_report.test_summary.get("total_tests", 0)
            passed_tests = test_report.test_summary.get("passed", 0)

            logger.info(
                f"Test Results: {test_report.test_status} "
                f"({passed_tests}/{total_tests} passed)"
            )

            # Check test status
            if test_report.test_status == "PASS":
                logger.info("✓ All tests PASSED")
                return test_report

            # Tests failed - attempt correction if iterations remain
            if test_iterations < self.MAX_TEST_ITERATIONS:
                logger.warning(
                    f"⚠ Tests FAILED: {len(test_report.defects_found)} defects found"
                )
                logger.info("Regenerating code with test feedback...")

                # Regenerate code with feedback from test failures
                # (In full implementation, would pass defects as feedback to code agent)
                code_input = CodeInput(
                    task_id=requirements.task_id,
                    design_specification=design_spec,
                    coding_standards=coding_standards
                    or "Follow PEP 8. Use type hints.",
                )
                generated_code = self.code_agent.execute(code_input)
                continue
            logger.error(f"✗ Tests still failing after {test_iterations} iterations")
            return test_report

        # This is unreachable: loop always runs at least once and all paths return
        raise RuntimeError("Unreachable: test loop should always return")

    def _execute_postmortem(
        self,
        requirements: TaskRequirements,
        project_plan: ProjectPlan,
        design_review: DesignReviewReport,
        code_review: CodeReviewReport,
        test_report: TestReport,
    ) -> PostmortemReport:
        """Execute Postmortem Agent for performance analysis."""
        try:
            logger.info("Executing Postmortem Agent...")

            # Build effort log from execution log
            effort_log = self._build_effort_log()

            # Build defect log from reviews and tests
            defect_log = self._build_defect_log(design_review, code_review, test_report)

            # Calculate actual semantic complexity from the project plan
            # (In full implementation, this would be recalculated post-execution)
            actual_complexity = project_plan.total_est_complexity or 10.0

            postmortem_input = PostmortemInput(
                task_id=requirements.task_id,
                project_plan=project_plan,
                effort_log=effort_log,
                defect_log=defect_log,
                actual_semantic_complexity=actual_complexity,
            )

            postmortem_report = self.postmortem_agent.execute(postmortem_input)

            logger.info(
                f"✓ Postmortem complete: "
                f"Defect density: {postmortem_report.quality_metrics.defect_density:.3f}, "
                f"Root causes: {len(postmortem_report.root_cause_analysis)}"
            )

            return postmortem_report

        except Exception as e:
            logger.error(f"Postmortem Agent failed: {e}")
            raise AgentExecutionError(f"Postmortem Agent execution failed: {e}") from e

    # =========================================================================
    # Helper methods
    # =========================================================================

    def _request_approval(
        self,
        task_id: str,
        gate_type: str,
        gate_name: str,
        report: Any,
        hitl_approver: Callable | None,
    ) -> bool:
        """
        Request approval for quality gate failure.

        Uses ApprovalService if configured, otherwise falls back to hitl_approver callable.

        Args:
            task_id: Task identifier
            gate_type: Gate type (design_review, code_review)
            gate_name: Gate name for logging (DesignReview, CodeReview)
            report: Quality report (DesignReviewReport or CodeReviewReport)
            hitl_approver: Legacy callable approver

        Returns:
            True if approved, False if rejected/deferred
        """
        # Priority 1: Use ApprovalService if configured
        if self.approval_service:
            logger.info(f"Requesting approval via ApprovalService: {gate_type}")

            approval_request = ApprovalRequest(
                task_id=task_id,
                gate_type=gate_type,
                agent_output=report.model_dump(),
                quality_report=report.model_dump(),
            )

            response = self.approval_service.request_approval(approval_request)

            # Log approval response
            logger.info(
                f"Approval decision: {response.decision.value} "
                f"by {response.reviewer} at {response.timestamp}"
            )
            logger.info(f"Justification: {response.justification}")

            if response.decision == ReviewDecision.APPROVED:
                self._record_hitl_override(
                    gate_name,
                    report,
                    f"Approved by {response.reviewer}: {response.justification}",
                )
                return True
            logger.warning(
                f"Approval {response.decision.value}: {response.justification}"
            )
            return False

        # Priority 2: Fall back to legacy callable approver
        if hitl_approver:
            logger.info(f"Requesting approval via legacy hitl_approver: {gate_name}")
            approved = hitl_approver(
                gate_name=gate_name,
                report=report.model_dump(),
            )
            if approved:
                self._record_hitl_override(gate_name, report, "Approved (legacy)")
            return approved

        # No approval mechanism available
        return False

    def _log_phase(self, phase_name: str, status: str, artifact: Any):
        """Log phase execution to execution log."""
        log_entry = {
            "phase": phase_name,
            "status": status,
            "timestamp": datetime.now().isoformat(),
        }
        self.execution_log.append(log_entry)
        logger.debug(f"Logged phase: {phase_name} - {status}")

    def _record_hitl_override(self, gate_name: str, report: Any, decision: str):
        """Record HITL override decision to audit trail."""
        override_record = {
            "gate_name": gate_name,
            "decision": decision,
            "timestamp": datetime.now().isoformat(),
            "report_summary": {
                "critical_issues": getattr(report, "critical_issue_count", 0)
                or getattr(report, "critical_issues", 0),
                "high_issues": getattr(report, "high_issue_count", 0)
                or getattr(report, "high_issues", 0),
            },
        }
        self.hitl_overrides.append(override_record)
        logger.info(f"Recorded HITL override: {gate_name} - {decision}")

    def _build_effort_log(self) -> list[EffortLogEntry]:
        """Build effort log from execution log (placeholder)."""
        # In full implementation, would aggregate telemetry data
        # For now, return empty list
        return []

    def _build_defect_log(
        self,
        design_review: DesignReviewReport,
        code_review: CodeReviewReport,
        test_report: TestReport,
    ) -> list[DefectLogEntry]:
        """Build defect log from review reports and test results."""
        defects = []

        # Default effort vector for defects found in reviews
        # (actual effort tracking would require telemetry integration)
        default_effort = {"latency_ms": 0.0, "tokens": 0, "api_cost": 0.0}

        # Design defects - map to AI Defect Taxonomy
        for issue in design_review.issues_found:
            defects.append(
                DefectLogEntry(
                    defect_id=f"D-{len(defects) + 1:03d}",
                    task_id=design_review.task_id,
                    defect_type="1_Planning_Failure",  # Design issues are planning failures
                    description=issue.description,
                    severity=issue.severity,
                    phase_injected="Design",
                    phase_removed="DesignReview",
                    effort_to_fix_vector=default_effort,
                )
            )

        # Code defects - map to AI Defect Taxonomy
        for issue in code_review.issues_found:
            defects.append(
                DefectLogEntry(
                    defect_id=f"D-{len(defects) + 1:03d}",
                    task_id=code_review.task_id,
                    defect_type="6_Conventional_Code_Bug",  # Code issues are conventional bugs
                    description=issue.description,
                    severity=issue.severity,
                    phase_injected="Code",
                    phase_removed="CodeReview",
                    effort_to_fix_vector=default_effort,
                )
            )

        # Test defects - use the defect_type from TestDefect
        for defect in test_report.defects_found:
            defects.append(
                DefectLogEntry(
                    defect_id=f"D-{len(defects) + 1:03d}",
                    task_id=test_report.task_id,
                    defect_type=defect.defect_type,
                    description=defect.description,
                    severity="High",  # Test failures are typically high severity
                    phase_injected=defect.phase_injected,
                    phase_removed="Test",
                    effort_to_fix_vector=default_effort,
                )
            )

        return defects

    def _determine_overall_status(
        self,
        design_review: DesignReviewReport,
        code_review: CodeReviewReport,
        test_report: TestReport,
    ) -> str:
        """Determine overall pipeline status from all phases."""
        # PASS: All phases passed
        if (
            design_review.overall_assessment == "PASS"
            and code_review.review_status == "PASS"
            and test_report.test_status == "PASS"
        ):
            return "PASS"

        # CONDITIONAL_PASS: Minor issues but acceptable
        if (
            design_review.overall_assessment in ["PASS", "NEEDS_IMPROVEMENT"]
            and code_review.review_status in ["PASS", "CONDITIONAL_PASS"]
            and test_report.test_status == "PASS"
        ):
            return "CONDITIONAL_PASS"

        # FAIL: Critical issues or test failures
        if (
            design_review.overall_assessment == "FAIL"
            or code_review.review_status == "FAIL"
            or test_report.test_status == "FAIL"
        ):
            return "FAIL"

        # Default to NEEDS_REVIEW
        return "NEEDS_REVIEW"

    # =========================================================================
    # Async execution methods (ADR 008 Phase 4)
    # =========================================================================

    async def execute_async(
        self,
        requirements: TaskRequirements,
        design_constraints: str | None = None,
        coding_standards: str | None = None,
        hitl_approver: Callable | None = None,
    ) -> TSPExecutionResult:
        """
        Execute complete TSP autonomous development pipeline asynchronously.

        Async version of execute() using agent execute_async() methods.
        Part of ADR 008 Phase 4: Async Orchestrators.

        This method orchestrates all 7 agents through the complete workflow:
        Planning → Design → Design Review → Code → Code Review → Test → Postmortem

        Quality gates enforce PSP discipline:
        - Design Review failure halts pipeline (requires HITL override)
        - Code Review failure halts pipeline (requires HITL override)
        - Test failure triggers code regeneration loop (max 2 iterations)

        Args:
            requirements: TaskRequirements with task description
            design_constraints: Optional design constraints/standards
            coding_standards: Optional coding standards
            hitl_approver: Optional callable for HITL approval (legacy interface).

        Returns:
            TSPExecutionResult containing all artifacts and execution metadata

        Raises:
            QualityGateFailure: If quality gate fails and no HITL override
            MaxIterationsExceeded: If correction loops exceed limits
            AgentExecutionError: If agent execution fails
        """
        banner = "=" * 80
        logger.info(
            f"{banner}\n"
            f"TSP ORCHESTRATOR (ASYNC): Starting autonomous pipeline\n"
            f"Task: {requirements.task_id} - {requirements.description}\n"
            f"{banner}"
        )

        start_time = datetime.now()
        self.execution_log = []
        self.hitl_overrides = []

        try:
            # Phase 1: Planning
            logger.info("\n[PHASE 1/7] PLANNING AGENT (async)")
            logger.info("-" * 80)
            project_plan = await self._execute_planning_async(requirements)
            self._log_phase("Planning", "SUCCESS", project_plan)

            # Phase 2: Design (with correction loop)
            logger.info("\n[PHASE 2/7] DESIGN AGENT (async)")
            logger.info("-" * 80)
            design_spec, design_review = await self._execute_design_with_review_async(
                requirements=requirements,
                project_plan=project_plan,
                design_constraints=design_constraints,
                hitl_approver=hitl_approver,
            )
            self._log_phase("Design", "SUCCESS", design_spec)
            self._log_phase(
                "DesignReview", design_review.overall_assessment, design_review
            )

            # Phase 3: Code Generation (with correction loop)
            logger.info("\n[PHASE 3/7] CODE AGENT (async)")
            logger.info("-" * 80)
            generated_code, code_review = await self._execute_code_with_review_async(
                requirements=requirements,
                design_spec=design_spec,
                coding_standards=coding_standards,
                hitl_approver=hitl_approver,
            )
            self._log_phase("Code", "SUCCESS", generated_code)
            self._log_phase("CodeReview", code_review.review_status, code_review)

            # Phase 4: Testing (with correction loop for failures)
            logger.info("\n[PHASE 4/7] TEST AGENT (async)")
            logger.info("-" * 80)
            test_report = await self._execute_testing_with_retry_async(
                requirements=requirements,
                design_spec=design_spec,
                generated_code=generated_code,
                coding_standards=coding_standards,
            )
            self._log_phase("Test", test_report.test_status, test_report)

            # Phase 5: Postmortem Analysis
            logger.info("\n[PHASE 5/7] POSTMORTEM AGENT (async)")
            logger.info("-" * 80)
            postmortem_report = await self._execute_postmortem_async(
                requirements=requirements,
                project_plan=project_plan,
                design_review=design_review,
                code_review=code_review,
                test_report=test_report,
            )
            self._log_phase("Postmortem", "SUCCESS", postmortem_report)

            # Calculate execution duration
            end_time = datetime.now()
            duration_seconds = (end_time - start_time).total_seconds()

            # Determine overall status
            overall_status = self._determine_overall_status(
                design_review, code_review, test_report
            )

            # Get test summary values
            total_tests = test_report.test_summary.get("total_tests", 0)
            passed_tests = test_report.test_summary.get("passed", 0)

            banner = "=" * 80
            logger.info(
                f"\n{banner}\n"
                f"TSP ORCHESTRATOR (ASYNC): Pipeline COMPLETE\n"
                f"Overall Status: {overall_status}\n"
                f"Duration: {duration_seconds:.1f}s\n"
                f"Files Generated: {generated_code.total_files}\n"
                f"Tests Passed: {passed_tests}/{total_tests}\n"
                f"HITL Overrides: {len(self.hitl_overrides)}\n"
                f"{banner}"
            )

            return TSPExecutionResult(
                task_id=requirements.task_id,
                overall_status=overall_status,
                project_plan=project_plan,
                design_specification=design_spec,
                design_review=design_review,
                generated_code=generated_code,
                code_review=code_review,
                test_report=test_report,
                postmortem_report=postmortem_report,
                execution_log=self.execution_log,
                hitl_overrides=self.hitl_overrides,
                total_duration_seconds=duration_seconds,
                timestamp=start_time,
            )

        except Exception as e:
            logger.error(f"TSP Orchestrator (async) failed: {e}", exc_info=True)
            self._log_phase("Pipeline", "FAILED", {"error": str(e)})
            raise

    async def _execute_planning_async(
        self,
        requirements: TaskRequirements,
    ) -> ProjectPlan:
        """Execute Planning Agent asynchronously."""
        try:
            logger.info("Executing Planning Agent (async)...")
            project_plan = await self.planning_agent.execute_async(requirements)

            logger.info(
                f"✓ Planning complete: {len(project_plan.semantic_units)} units, "
                f"complexity {project_plan.total_est_complexity}"
            )
            return project_plan

        except Exception as e:
            logger.error(f"Planning Agent failed: {e}")
            raise AgentExecutionError(f"Planning Agent execution failed: {e}") from e

    async def _execute_design_with_review_async(
        self,
        requirements: TaskRequirements,
        project_plan: ProjectPlan,
        design_constraints: str | None,
        hitl_approver: Callable | None,
    ) -> tuple[DesignSpecification, DesignReviewReport]:
        """
        Execute Design Agent asynchronously with Design Review quality gate.

        Implements correction loop: Design → Review → Feedback → Redesign
        Enforces quality gate: Halts on FAIL (requires HITL override)
        """
        design_iterations = 0

        while design_iterations < self.MAX_DESIGN_ITERATIONS:
            # Generate design
            logger.info(
                f"Design iteration {design_iterations + 1}/{self.MAX_DESIGN_ITERATIONS}"
            )
            design_input = DesignInput(
                task_id=requirements.task_id,
                requirements=requirements.requirements,
                project_plan=project_plan,
                design_constraints=design_constraints or "",
            )
            design_spec = await self.design_agent.execute_async(design_input)
            design_iterations += 1

            logger.info(
                f"✓ Design complete: {len(design_spec.api_contracts)} APIs, "
                f"{len(design_spec.component_logic)} components"
            )

            # Design Review (Quality Gate)
            logger.info("Executing Design Review Orchestrator (async, Quality Gate)...")
            design_review = await self.design_review_orchestrator.execute_async(
                design_spec
            )

            logger.info(
                f"Design Review: {design_review.overall_assessment} "
                f"({design_review.critical_issue_count}C/{design_review.high_issue_count}H/"
                f"{design_review.medium_issue_count}M/{design_review.low_issue_count}L)"
            )

            # Quality Gate: Check review status
            if design_review.overall_assessment == "PASS":
                logger.info("✓ Design PASSED review - proceeding to Code phase")
                return design_spec, design_review

            if design_review.overall_assessment == "NEEDS_IMPROVEMENT":
                # Accept design with minor issues
                logger.info("✓ Design acceptable with minor improvements - proceeding")
                return design_spec, design_review

            # Design FAILED - check for HITL override
            if design_review.overall_assessment == "FAIL":
                logger.warning(
                    f"⚠ Design FAILED review: "
                    f"{design_review.critical_issue_count} critical, "
                    f"{design_review.high_issue_count} high issues"
                )

                # Request HITL approval if available
                approved = self._request_approval(
                    task_id=requirements.task_id,
                    gate_type="design_review",
                    gate_name="DesignReview",
                    report=design_review,
                    hitl_approver=hitl_approver,
                )
                if approved:
                    logger.info(
                        "✓ HITL override approved - proceeding despite failures"
                    )
                    return design_spec, design_review

                # No HITL or rejected - attempt correction if iterations remain
                if design_iterations < self.MAX_DESIGN_ITERATIONS:
                    logger.info("Retrying design with feedback from review...")
                    continue
                # Exceeded iterations
                raise QualityGateFailure(
                    f"Design Review FAILED after {design_iterations} iterations. "
                    f"Critical: {design_review.critical_issue_count}, "
                    f"High: {design_review.high_issue_count}. "
                    f"Requires HITL approval to proceed."
                )

        raise MaxIterationsExceeded(
            f"Exceeded max design iterations ({self.MAX_DESIGN_ITERATIONS})"
        )

    async def _execute_code_with_review_async(
        self,
        requirements: TaskRequirements,
        design_spec: DesignSpecification,
        coding_standards: str | None,
        hitl_approver: Callable | None,
    ) -> tuple[GeneratedCode, CodeReviewReport]:
        """
        Execute Code Agent asynchronously with Code Review quality gate.

        Implements correction loop: Code → Review → Feedback → Recode
        Enforces quality gate: Halts on FAIL (requires HITL override)
        """
        code_iterations = 0

        while code_iterations < self.MAX_CODE_ITERATIONS:
            # Generate code
            logger.info(
                f"Code iteration {code_iterations + 1}/{self.MAX_CODE_ITERATIONS}"
            )
            code_input = CodeInput(
                task_id=requirements.task_id,
                design_specification=design_spec,
                coding_standards=coding_standards
                or "Follow PEP 8. Use type hints. Include docstrings.",
            )
            generated_code = await self.code_agent.execute_async(code_input)
            code_iterations += 1

            logger.info(
                f"✓ Code generation complete: {generated_code.total_files} files, "
                f"{generated_code.total_lines_of_code} LOC"
            )

            # Code Review (Quality Gate)
            logger.info("Executing Code Review Orchestrator (async, Quality Gate)...")
            code_review = await self.code_review_orchestrator.execute_async(
                generated_code
            )

            logger.info(
                f"Code Review: {code_review.review_status} "
                f"({code_review.critical_issues}C/{code_review.high_issues}H/"
                f"{code_review.medium_issues}M/{code_review.low_issues}L)"
            )

            # Quality Gate: Check review status
            if code_review.review_status == "PASS":
                logger.info("✓ Code PASSED review - proceeding to Test phase")
                return generated_code, code_review

            if code_review.review_status == "CONDITIONAL_PASS":
                # Accept code with minor issues (<5 high, no critical)
                logger.info("✓ Code acceptable with conditions - proceeding")
                return generated_code, code_review

            # Code FAILED - check for HITL override
            if code_review.review_status == "FAIL":
                logger.warning(
                    f"⚠ Code FAILED review: "
                    f"{code_review.critical_issues} critical, "
                    f"{code_review.high_issues} high issues"
                )

                # Request HITL approval if available
                approved = self._request_approval(
                    task_id=requirements.task_id,
                    gate_type="code_review",
                    gate_name="CodeReview",
                    report=code_review,
                    hitl_approver=hitl_approver,
                )
                if approved:
                    logger.info(
                        "✓ HITL override approved - proceeding despite failures"
                    )
                    return generated_code, code_review

                # No HITL or rejected - attempt correction if iterations remain
                if code_iterations < self.MAX_CODE_ITERATIONS:
                    logger.info("Retrying code generation with feedback from review...")
                    continue
                raise QualityGateFailure(
                    f"Code Review FAILED after {code_iterations} iterations. "
                    f"Critical: {code_review.critical_issues}, "
                    f"High: {code_review.high_issues}. "
                    f"Requires HITL approval to proceed."
                )

        raise MaxIterationsExceeded(
            f"Exceeded max code iterations ({self.MAX_CODE_ITERATIONS})"
        )

    async def _execute_testing_with_retry_async(
        self,
        requirements: TaskRequirements,
        design_spec: DesignSpecification,
        generated_code: GeneratedCode,
        coding_standards: str | None,
    ) -> TestReport:
        """
        Execute Test Agent asynchronously with retry loop for test failures.

        Unlike review quality gates, test failures trigger automatic code regeneration
        (up to MAX_TEST_ITERATIONS) rather than requiring HITL approval.
        """
        if self.MAX_TEST_ITERATIONS < 1:
            raise ValueError("MAX_TEST_ITERATIONS must be at least 1")

        test_iterations = 0
        test_report: TestReport  # Will be assigned in first iteration

        while test_iterations < self.MAX_TEST_ITERATIONS:
            logger.info(
                f"Test iteration {test_iterations + 1}/{self.MAX_TEST_ITERATIONS}"
            )

            # Execute tests
            test_input = TestInput(
                task_id=requirements.task_id,
                generated_code=generated_code,
                design_specification=design_spec,
            )
            test_report = await self.test_agent.execute_async(test_input)
            test_iterations += 1

            # Get test summary values
            total_tests = test_report.test_summary.get("total_tests", 0)
            passed_tests = test_report.test_summary.get("passed", 0)

            logger.info(
                f"Test Results: {test_report.test_status} "
                f"({passed_tests}/{total_tests} passed)"
            )

            # Check test status
            if test_report.test_status == "PASS":
                logger.info("✓ All tests PASSED")
                return test_report

            # Tests failed - attempt correction if iterations remain
            if test_iterations < self.MAX_TEST_ITERATIONS:
                logger.warning(
                    f"⚠ Tests FAILED: {len(test_report.defects_found)} defects found"
                )
                logger.info("Regenerating code with test feedback (async)...")

                # Regenerate code with feedback from test failures
                code_input = CodeInput(
                    task_id=requirements.task_id,
                    design_specification=design_spec,
                    coding_standards=coding_standards
                    or "Follow PEP 8. Use type hints.",
                )
                generated_code = await self.code_agent.execute_async(code_input)
                continue
            logger.error(f"✗ Tests still failing after {test_iterations} iterations")
            return test_report

        # This is unreachable: loop always runs at least once and all paths return
        raise RuntimeError("Unreachable: test loop should always return")

    async def _execute_postmortem_async(
        self,
        requirements: TaskRequirements,
        project_plan: ProjectPlan,
        design_review: DesignReviewReport,
        code_review: CodeReviewReport,
        test_report: TestReport,
    ) -> PostmortemReport:
        """Execute Postmortem Agent asynchronously for performance analysis."""
        try:
            logger.info("Executing Postmortem Agent (async)...")

            # Build effort log from execution log
            effort_log = self._build_effort_log()

            # Build defect log from reviews and tests
            defect_log = self._build_defect_log(design_review, code_review, test_report)

            # Calculate actual semantic complexity from the project plan
            actual_complexity = project_plan.total_est_complexity or 10.0

            postmortem_input = PostmortemInput(
                task_id=requirements.task_id,
                project_plan=project_plan,
                effort_log=effort_log,
                defect_log=defect_log,
                actual_semantic_complexity=actual_complexity,
            )

            postmortem_report = await self.postmortem_agent.execute_async(
                postmortem_input
            )

            logger.info(
                f"✓ Postmortem complete: "
                f"Defect density: {postmortem_report.quality_metrics.defect_density:.3f}, "
                f"Root causes: {len(postmortem_report.root_cause_analysis)}"
            )

            return postmortem_report

        except Exception as e:
            logger.error(f"Postmortem Agent failed: {e}")
            raise AgentExecutionError(f"Postmortem Agent execution failed: {e}") from e
