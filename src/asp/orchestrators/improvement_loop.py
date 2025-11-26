"""
Self-Improvement Loop Orchestrator

This module orchestrates the complete self-improvement cycle:
1. Postmortem analysis generates PIPs
2. PIPs are reviewed by humans (HITL)
3. Approved PIPs are applied to prompts
4. Cycle times are tracked
5. Impact is measured on subsequent tasks

This implements Phase 5 (ASP-Loop) of the PRD.

The improvement loop workflow:
- After task completion → Postmortem Agent analyzes performance
- If improvement opportunities found → Generate PIP
- PIP submitted for review → Human approves/rejects/requests revision
- If approved → Apply changes to prompts via versioning
- Track cycle metrics → Measure impact on next task

Author: ASP Development Team
Date: November 25, 2025
"""

import logging
from pathlib import Path
from typing import Optional

from asp.agents.postmortem_agent import PostmortemAgent
from asp.approval.pip_review_service import PIPReviewService
from asp.models.postmortem import (
    PostmortemInput,
    PostmortemReport,
    ProcessImprovementProposal,
)
from asp.prompts.prompt_versioner import PromptVersioner
from asp.telemetry.cycle_tracker import CycleTracker


logger = logging.getLogger(__name__)


class ImprovementLoopOrchestrator:
    """
    Orchestrates the self-improvement loop (Phase 5 - ASP-Loop).

    This orchestrator:
    1. Generates PIPs from postmortem analysis
    2. Presents PIPs for human review (optional)
    3. Applies approved PIPs to prompts
    4. Tracks cycle time metrics
    5. Measures improvement impact

    The loop enables continuous improvement:
    - Defects found → Postmortem analysis → PIP created
    - PIP reviewed → Changes applied → Prompts improved
    - Next task → Fewer defects → Better quality

    Example:
        >>> from asp.orchestrators.improvement_loop import ImprovementLoopOrchestrator
        >>> from asp.agents.postmortem_agent import PostmortemAgent
        >>>
        >>> # After task completion
        >>> postmortem_agent = PostmortemAgent()
        >>> postmortem_report = postmortem_agent.execute(postmortem_input)
        >>>
        >>> # Run improvement loop
        >>> loop = ImprovementLoopOrchestrator(enable_hitl=True)
        >>> result = loop.run_improvement_cycle(
        ...     postmortem_report=postmortem_report,
        ...     postmortem_input=postmortem_input,
        ... )
        >>>
        >>> if result.pip_approved:
        >>>     print(f"Prompts updated: {result.updated_prompts}")
    """

    def __init__(
        self,
        enable_hitl: bool = True,
        enable_prompt_updates: bool = True,
        enable_cycle_tracking: bool = True,
        prompts_dir: Path = Path("src/asp/prompts"),
        cycles_dir: Path = Path("artifacts/improvement_cycles"),
    ):
        """
        Initialize ImprovementLoopOrchestrator.

        Args:
            enable_hitl: If True, PIPs require human review before applying
            enable_prompt_updates: If True, approved PIPs are applied to prompts
            enable_cycle_tracking: If True, cycle metrics are tracked
            prompts_dir: Directory containing prompt files
            cycles_dir: Directory for cycle tracking data
        """
        self.enable_hitl = enable_hitl
        self.enable_prompt_updates = enable_prompt_updates
        self.enable_cycle_tracking = enable_cycle_tracking

        # Initialize services
        self.pip_review_service = PIPReviewService() if enable_hitl else None
        self.prompt_versioner = PromptVersioner(prompts_dir) if enable_prompt_updates else None
        self.cycle_tracker = CycleTracker(cycles_dir) if enable_cycle_tracking else None

        logger.info(
            f"ImprovementLoopOrchestrator initialized: "
            f"HITL={enable_hitl}, "
            f"PromptUpdates={enable_prompt_updates}, "
            f"CycleTracking={enable_cycle_tracking}"
        )

    def run_improvement_cycle(
        self,
        postmortem_report: PostmortemReport,
        postmortem_input: PostmortemInput,
        postmortem_agent: PostmortemAgent,
        auto_approve: bool = False,
    ) -> dict:
        """
        Run complete improvement cycle.

        Args:
            postmortem_report: PostmortemReport from completed task
            postmortem_input: Original PostmortemInput (contains defect log)
            postmortem_agent: PostmortemAgent instance (for generating PIP)
            auto_approve: If True, skip HITL and auto-approve (for testing)

        Returns:
            Dict with cycle results:
                - pip_generated: bool
                - pip: ProcessImprovementProposal or None
                - pip_approved: bool
                - updated_prompts: list of prompt files updated
                - cycle_id: str (for tracking)
        """
        logger.info(
            f"Running improvement cycle for task {postmortem_report.task_id}"
        )

        result = {
            "pip_generated": False,
            "pip": None,
            "pip_approved": False,
            "updated_prompts": [],
            "cycle_id": None,
        }

        # Step 1: Generate PIP from postmortem analysis
        try:
            pip = postmortem_agent.generate_pip(
                postmortem_report=postmortem_report,
                input_data=postmortem_input,
            )
            result["pip_generated"] = True
            result["pip"] = pip
            logger.info(f"PIP generated: {pip.proposal_id}")
        except Exception as e:
            logger.error(f"Failed to generate PIP: {e}", exc_info=True)
            return result

        # Step 2: Track PIP creation
        if self.enable_cycle_tracking:
            try:
                defect_count = len(postmortem_input.defect_log)
                cycle = self.cycle_tracker.record_pip_created(pip, defect_count)
                result["cycle_id"] = pip.proposal_id
                logger.info(f"Cycle tracking started: {cycle.pip_id}")
            except Exception as e:
                logger.warning(f"Failed to track PIP creation: {e}")

        # Step 3: Review PIP (HITL or auto-approve)
        if auto_approve:
            logger.info("Auto-approving PIP (testing mode)")
            pip.hitl_status = "approved"
            pip.hitl_reviewer = "auto-approve"
            pip.hitl_feedback = "Auto-approved for testing"
            result["pip_approved"] = True
        elif self.enable_hitl and self.pip_review_service:
            try:
                logger.info("Presenting PIP for human review...")
                pip = self.pip_review_service.review_pip(pip)

                # Track review
                if self.enable_cycle_tracking:
                    self.cycle_tracker.record_pip_reviewed(pip)

                result["pip_approved"] = (pip.hitl_status == "approved")
                logger.info(f"PIP review complete: {pip.hitl_status}")
            except Exception as e:
                logger.error(f"Failed to review PIP: {e}", exc_info=True)
                return result
        else:
            logger.warning(
                "HITL disabled and auto_approve=False - PIP will remain pending"
            )

        # Step 4: Apply approved PIP to prompts
        if result["pip_approved"] and self.enable_prompt_updates and self.prompt_versioner:
            try:
                logger.info("Applying PIP changes to prompts...")
                updated_files = self.prompt_versioner.apply_pip(pip)
                result["updated_prompts"] = list(updated_files.values())

                # Track prompt updates
                if self.enable_cycle_tracking:
                    self.cycle_tracker.record_prompts_updated(
                        pip.proposal_id,
                        list(updated_files.values())
                    )

                logger.info(
                    f"PIP applied: {len(updated_files)} prompts updated"
                )
            except Exception as e:
                logger.error(f"Failed to apply PIP to prompts: {e}", exc_info=True)
                # Continue even if prompt update fails
                result["updated_prompts"] = [f"ERROR: {e}"]

        # Step 5: Summary
        logger.info(
            f"Improvement cycle complete: "
            f"PIP={pip.proposal_id}, "
            f"Status={pip.hitl_status}, "
            f"Prompts updated={len(result['updated_prompts'])}"
        )

        return result

    def measure_impact(
        self,
        pip_id: str,
        impact_task_id: str,
        new_defect_count: int,
        notes: Optional[str] = None,
    ) -> dict:
        """
        Measure impact of PIP on subsequent task.

        This should be called after the first task is completed using
        updated prompts from an approved PIP.

        Args:
            pip_id: PIP identifier
            impact_task_id: Task ID of first task with updated prompts
            new_defect_count: Number of target defects in new task
            notes: Optional notes about impact

        Returns:
            Dict with impact metrics:
                - baseline_defects: int
                - new_defects: int
                - defect_reduction: float (percentage)
                - cycle_time: str
        """
        if not self.enable_cycle_tracking or not self.cycle_tracker:
            logger.warning("Cycle tracking disabled - cannot measure impact")
            return {}

        try:
            # Record impact
            cycle = self.cycle_tracker.record_impact(
                pip_id=pip_id,
                impact_task_id=impact_task_id,
                defect_count=new_defect_count,
                notes=notes,
            )

            # Calculate metrics
            impact = {
                "baseline_defects": cycle.baseline_defect_count,
                "new_defects": cycle.post_improvement_defect_count,
                "defect_reduction_percent": cycle.defect_reduction_percent,
                "review_cycle_time": str(cycle.review_cycle_time),
                "total_cycle_time": str(cycle.total_cycle_time),
            }

            logger.info(
                f"Impact measured for PIP {pip_id}: "
                f"{impact['baseline_defects']} → {impact['new_defects']} defects "
                f"({impact['defect_reduction_percent']}% reduction)"
            )

            return impact

        except Exception as e:
            logger.error(f"Failed to measure impact: {e}", exc_info=True)
            return {}

    def get_cycle_report(self) -> dict:
        """
        Generate report of all improvement cycles.

        Returns:
            Dict with aggregate metrics:
                - total_cycles: int
                - avg_review_time_hours: float
                - avg_defect_reduction_percent: float
                - cycles_with_positive_impact: int
        """
        if not self.enable_cycle_tracking or not self.cycle_tracker:
            return {"error": "Cycle tracking not enabled"}

        try:
            return self.cycle_tracker.generate_report()
        except Exception as e:
            logger.error(f"Failed to generate cycle report: {e}", exc_info=True)
            return {"error": str(e)}


def integrate_with_tsp_orchestrator(
    tsp_orchestrator,
    enable_improvement_loop: bool = True,
    enable_hitl: bool = True,
    auto_approve_pips: bool = False,
):
    """
    Integrate improvement loop with TSP Orchestrator.

    This helper function adds the improvement loop to the TSP Orchestrator's
    workflow so that PIPs are automatically generated and reviewed after each task.

    Args:
        tsp_orchestrator: TSPOrchestrator instance
        enable_improvement_loop: If True, run improvement loop after tasks
        enable_hitl: If True, PIPs require human review
        auto_approve_pips: If True, auto-approve PIPs (for testing)

    Returns:
        ImprovementLoopOrchestrator instance

    Example:
        >>> from asp.orchestrators.tsp_orchestrator import TSPOrchestrator
        >>> from asp.orchestrators.improvement_loop import integrate_with_tsp_orchestrator
        >>>
        >>> orchestrator = TSPOrchestrator()
        >>> improvement_loop = integrate_with_tsp_orchestrator(
        ...     orchestrator,
        ...     enable_improvement_loop=True,
        ...     enable_hitl=True,
        ... )
        >>>
        >>> # Now TSP runs will automatically trigger improvement loop
        >>> result = orchestrator.execute(requirements)
    """
    if not enable_improvement_loop:
        logger.info("Improvement loop integration disabled")
        return None

    # Create improvement loop orchestrator
    improvement_loop = ImprovementLoopOrchestrator(
        enable_hitl=enable_hitl,
        enable_prompt_updates=True,
        enable_cycle_tracking=True,
    )

    # Store on TSP orchestrator for access
    tsp_orchestrator.improvement_loop = improvement_loop
    tsp_orchestrator.auto_approve_pips = auto_approve_pips

    logger.info(
        f"Improvement loop integrated with TSP Orchestrator: "
        f"HITL={enable_hitl}, AutoApprove={auto_approve_pips}"
    )

    return improvement_loop
