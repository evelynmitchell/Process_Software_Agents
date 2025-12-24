"""
Planning Agent for ASP Platform

The Planning Agent is responsible for:
1. Task Decomposition (FR-001): Breaking high-level requirements into semantic units
2. Semantic Complexity Scoring: Calculating complexity using C1 formula (PRD Section 13.1)
3. PROBE-AI Estimation (FR-002): Estimating effort based on historical data (Phase 2)

This is the first agent in the 7-agent ASP architecture.

Author: ASP Development Team
Date: November 13, 2025
"""

import logging
from pathlib import Path
from typing import Any

from asp.agents.base_agent import AgentExecutionError, BaseAgent
from asp.models.planning import ProjectPlan, SemanticUnit, TaskRequirements
from asp.telemetry import track_agent_cost
from asp.utils.artifact_io import write_artifact_json, write_artifact_markdown
from asp.utils.git_utils import git_commit_artifact, is_git_repository
from asp.utils.markdown_renderer import render_plan_markdown
from asp.utils.semantic_complexity import (
    ComplexityFactors,
    calculate_semantic_complexity,
)

logger = logging.getLogger(__name__)


class PlanningAgent(BaseAgent):
    """
    Planning Agent implementation.

    Decomposes high-level task requirements into measurable semantic units
    with complexity scoring using the C1 formula.

    Phase 1: Task decomposition + complexity scoring only
    Phase 2 (after 10 tasks): Add PROBE-AI estimation

    Example:
        agent = PlanningAgent()
        requirements = TaskRequirements(
            task_id="TASK-2025-001",
            description="Build user authentication",
            requirements="JWT tokens, registration, login..."
        )
        plan = agent.execute(requirements)
        print(f"Decomposed into {len(plan.semantic_units)} units")
        print(f"Total complexity: {plan.total_est_complexity}")
    """

    def __init__(
        self,
        db_path: Path | None = None,
        llm_client: Any | None = None,
    ):
        """
        Initialize Planning Agent.

        Args:
            db_path: Optional path to SQLite database for telemetry
            llm_client: Optional LLM client (for dependency injection in tests)
        """
        super().__init__(db_path=db_path, llm_client=llm_client)
        self.agent_version = "1.0.0"

    @track_agent_cost(
        agent_role="Planning",
        task_id_param="input_data.task_id",
        llm_model="claude-sonnet-4-20250514",
        llm_provider="anthropic",
        agent_version="1.0.0",
    )
    def execute(
        self, input_data: TaskRequirements, feedback: list | None = None
    ) -> ProjectPlan:
        """
        Execute Planning Agent logic with optional feedback.

        Steps:
        1. Load and format decomposition prompt (with feedback if provided)
        2. Call LLM to decompose task into semantic units
        3. Validate and calculate complexity for each unit
        4. (Phase 2) Run PROBE-AI estimation if available
        5. Return ProjectPlan

        Args:
            input_data: TaskRequirements with task details
            feedback: Optional list of DesignIssue objects from Design Review
                     requiring replanning (issues with affected_phase="Planning")

        Returns:
            ProjectPlan with decomposed semantic units and complexity scores

        Raises:
            AgentExecutionError: If decomposition fails
        """
        logger.info(
            f"Planning Agent executing for task_id={input_data.task_id}, "
            f"description='{input_data.description[:50]}...', "
            f"feedback_items={len(feedback) if feedback else 0}"
        )

        try:
            # Step 1: Decompose task into semantic units (with or without feedback)
            if feedback:
                semantic_units = self.decompose_task_with_feedback(input_data, feedback)
            else:
                semantic_units = self.decompose_task(input_data)

            # Step 2: Calculate total complexity
            total_complexity = sum(unit.est_complexity for unit in semantic_units)

            # Step 3: (Phase 2) PROBE-AI estimation - currently returns None
            probe_ai_prediction = None  # TODO: Implement in Phase 2

            # Step 4: Build and return project plan
            plan = ProjectPlan(
                project_id=input_data.project_id,
                task_id=input_data.task_id,
                semantic_units=semantic_units,
                total_est_complexity=total_complexity,
                probe_ai_prediction=probe_ai_prediction,
                probe_ai_enabled=False,  # Phase 2
                agent_version=self.agent_version,
            )

            logger.info(
                f"Planning complete: {len(semantic_units)} units, "
                f"total_complexity={total_complexity}"
            )

            # Step 5: Write artifacts to filesystem (if enabled)
            try:
                # Write JSON artifact
                json_path = write_artifact_json(
                    task_id=plan.task_id,
                    artifact_type="plan",
                    data=plan,
                )
                logger.debug(f"Wrote plan JSON: {json_path}")

                # Write Markdown artifact
                markdown_content = render_plan_markdown(plan)
                md_path = write_artifact_markdown(
                    task_id=plan.task_id,
                    artifact_type="plan",
                    markdown_content=markdown_content,
                )
                logger.debug(f"Wrote plan Markdown: {md_path}")

                # Commit to git (if in repository)
                if is_git_repository():
                    commit_hash = git_commit_artifact(
                        task_id=plan.task_id,
                        agent_name="Planning Agent",
                        artifact_files=[str(json_path), str(md_path)],
                    )
                    if commit_hash:
                        logger.info(f"Committed artifacts: {commit_hash}")
                else:
                    logger.warning("Not in git repository, skipping commit")

            except Exception as e:
                # Log but don't fail - artifact persistence is not critical
                logger.warning(f"Failed to write artifacts: {e}", exc_info=True)

            return plan

        except Exception as e:
            logger.error(f"Planning Agent execution failed: {e}")
            raise AgentExecutionError(
                f"Planning Agent failed for task {input_data.task_id}: {e}"
            ) from e

    def decompose_task(self, requirements: TaskRequirements) -> list[SemanticUnit]:
        """
        Decompose task into semantic units using LLM.

        This method:
        1. Loads the decomposition prompt template
        2. Formats it with the task requirements
        3. Calls the LLM to generate semantic units
        4. Parses and validates the response
        5. Calculates complexity for each unit

        Args:
            requirements: TaskRequirements to decompose

        Returns:
            List of validated SemanticUnit objects

        Raises:
            AgentExecutionError: If decomposition fails or output is invalid
        """
        logger.debug(f"Decomposing task {requirements.task_id}")

        # Load prompt template
        try:
            prompt_template = self.load_prompt("planning_agent_v1_decomposition")
        except FileNotFoundError as e:
            raise AgentExecutionError(f"Prompt template not found: {e}") from e

        # Format prompt with requirements
        formatted_prompt = self.format_prompt(
            prompt_template,
            task_id=requirements.task_id,
            description=requirements.description,
            requirements=requirements.requirements,
            context_files="\n".join(requirements.context_files or []),
        )

        # Call LLM
        response = self.call_llm(
            prompt=formatted_prompt,
            max_tokens=4096,
            temperature=0.0,  # Deterministic for consistency
        )

        # Parse response
        content = response.get("content")
        if not isinstance(content, dict):
            raise AgentExecutionError(
                f"LLM returned non-JSON response: {content}\n"
                f"Expected JSON with 'semantic_units' array"
            )

        # Extract semantic units
        if "semantic_units" not in content:
            raise AgentExecutionError(
                f"LLM response missing 'semantic_units' key: {content.keys()}"
            )

        units_data = content["semantic_units"]
        if not isinstance(units_data, list):
            raise AgentExecutionError(
                f"'semantic_units' must be an array, got {type(units_data)}"
            )

        # Validate and create SemanticUnit objects
        semantic_units = []
        for i, unit_data in enumerate(units_data):
            try:
                # Validate with Pydantic
                unit = SemanticUnit.model_validate(unit_data)

                # Verify complexity calculation
                factors = ComplexityFactors(
                    api_interactions=unit.api_interactions,
                    data_transformations=unit.data_transformations,
                    logical_branches=unit.logical_branches,
                    code_entities_modified=unit.code_entities_modified,
                    novelty_multiplier=unit.novelty_multiplier,
                )
                calculated_complexity = calculate_semantic_complexity(factors)

                # Allow small rounding differences
                if abs(unit.est_complexity - calculated_complexity) > 1:
                    logger.warning(
                        f"Unit {unit.unit_id}: Complexity mismatch. "
                        f"LLM reported {unit.est_complexity}, "
                        f"calculated {calculated_complexity}. "
                        f"Using calculated value."
                    )
                    # Override with calculated value
                    unit.est_complexity = calculated_complexity

                semantic_units.append(unit)

            except Exception as e:
                raise AgentExecutionError(
                    f"Failed to validate semantic unit {i}: {e}\nData: {unit_data}"
                ) from e

        logger.info(
            f"Successfully decomposed into {len(semantic_units)} semantic units"
        )
        return semantic_units

    def decompose_task_with_feedback(
        self, requirements: TaskRequirements, feedback: list
    ) -> list[SemanticUnit]:
        """
        Decompose task into semantic units with Design Review feedback.

        This method is called when Design Review has identified Planning-phase issues
        that require the task to be re-decomposed with corrections.

        Steps:
        1. Format feedback issues into readable text
        2. Load the feedback-aware decomposition prompt template
        3. Format prompt with requirements + feedback
        4. Call LLM to generate revised semantic units
        5. Parse and validate the response
        6. Calculate complexity for each unit

        Args:
            requirements: Original TaskRequirements
            feedback: List of DesignIssue objects with affected_phase="Planning" or "Both"

        Returns:
            List of revised SemanticUnit objects

        Raises:
            AgentExecutionError: If decomposition fails or output is invalid
        """
        logger.debug(
            f"Re-decomposing task {requirements.task_id} with {len(feedback)} feedback issues"
        )

        # Step 1: Format feedback issues into readable string
        feedback_text = self._format_feedback_issues(feedback)

        # Step 2: Load feedback-aware prompt template
        try:
            prompt_template = self.load_prompt("planning_agent_v1_with_feedback")
        except FileNotFoundError as e:
            raise AgentExecutionError(f"Feedback prompt template not found: {e}") from e

        # Step 3: Format prompt with requirements + feedback
        formatted_prompt = self.format_prompt(
            prompt_template,
            description=requirements.description,
            requirements=requirements.requirements,
            feedback=feedback_text,
        )

        # Step 4: Call LLM
        response = self.call_llm(
            prompt=formatted_prompt,
            max_tokens=4096,
            temperature=0.0,  # Deterministic for consistency
        )

        # Step 5: Parse response
        content = response.get("content")
        if not isinstance(content, dict):
            raise AgentExecutionError(
                f"LLM returned non-JSON response: {content}\n"
                f"Expected JSON with 'semantic_units' array"
            )

        # Extract semantic units
        if "semantic_units" not in content:
            raise AgentExecutionError(
                f"LLM response missing 'semantic_units' key: {content.keys()}"
            )

        units_data = content["semantic_units"]
        if not isinstance(units_data, list):
            raise AgentExecutionError(
                f"'semantic_units' must be an array, got {type(units_data)}"
            )

        # Step 6: Validate and create SemanticUnit objects
        semantic_units = []
        for i, unit_data in enumerate(units_data):
            try:
                # Validate with Pydantic
                unit = SemanticUnit.model_validate(unit_data)

                # Verify complexity calculation
                factors = ComplexityFactors(
                    api_interactions=unit.api_interactions,
                    data_transformations=unit.data_transformations,
                    logical_branches=unit.logical_branches,
                    code_entities_modified=unit.code_entities_modified,
                    novelty_multiplier=unit.novelty_multiplier,
                )
                calculated_complexity = calculate_semantic_complexity(factors)

                # Allow small rounding differences
                if abs(unit.est_complexity - calculated_complexity) > 1:
                    logger.warning(
                        f"Unit {unit.unit_id}: Complexity mismatch. "
                        f"LLM reported {unit.est_complexity}, "
                        f"calculated {calculated_complexity}. "
                        f"Using calculated value."
                    )
                    # Override with calculated value
                    unit.est_complexity = calculated_complexity

                semantic_units.append(unit)

            except Exception as e:
                raise AgentExecutionError(
                    f"Failed to validate semantic unit {i}: {e}\nData: {unit_data}"
                ) from e

        logger.info(
            f"Successfully re-decomposed into {len(semantic_units)} semantic units "
            f"addressing {len(feedback)} feedback issues"
        )
        return semantic_units

    def _format_feedback_issues(self, feedback: list) -> str:
        """
        Format DesignIssue objects into readable text for the feedback prompt.

        Args:
            feedback: List of DesignIssue objects

        Returns:
            Formatted string with all feedback issues
        """
        lines = []
        for issue in feedback:
            lines.append(
                f"{issue.issue_id} ({issue.affected_phase} Phase, {issue.severity}): "
                f"{issue.description}"
            )
            if issue.evidence:
                lines.append(f"  Evidence: {issue.evidence}")
            if issue.impact:
                lines.append(f"  Impact: {issue.impact}")
            lines.append("")  # Blank line between issues

        return "\n".join(lines)

    # =========================================================================
    # Async Methods (ADR 008 Phase 2)
    # =========================================================================

    async def execute_async(
        self, input_data: TaskRequirements, feedback: list | None = None
    ) -> ProjectPlan:
        """
        Asynchronous version of execute for parallel agent execution.

        Native async implementation that uses call_llm_async() instead of
        call_llm(). Use this method when running multiple agents concurrently.

        Args:
            input_data: TaskRequirements with task details
            feedback: Optional list of DesignIssue objects from Design Review

        Returns:
            ProjectPlan with decomposed semantic units and complexity scores

        Raises:
            AgentExecutionError: If decomposition fails
        """
        logger.info(
            f"Planning Agent (async) executing for task_id={input_data.task_id}, "
            f"description='{input_data.description[:50]}...', "
            f"feedback_items={len(feedback) if feedback else 0}"
        )

        try:
            # Step 1: Decompose task into semantic units (async LLM call)
            if feedback:
                semantic_units = await self._decompose_task_with_feedback_async(
                    input_data, feedback
                )
            else:
                semantic_units = await self._decompose_task_async(input_data)

            # Step 2: Calculate total complexity (sync - fast computation)
            total_complexity = sum(unit.est_complexity for unit in semantic_units)

            # Step 3: (Phase 2) PROBE-AI estimation - currently returns None
            probe_ai_prediction = None  # TODO: Implement in Phase 2

            # Step 4: Build and return project plan
            plan = ProjectPlan(
                project_id=input_data.project_id,
                task_id=input_data.task_id,
                semantic_units=semantic_units,
                total_est_complexity=total_complexity,
                probe_ai_prediction=probe_ai_prediction,
                probe_ai_enabled=False,
                agent_version=self.agent_version,
            )

            logger.info(
                f"Planning complete (async): {len(semantic_units)} units, "
                f"total_complexity={total_complexity}"
            )

            return plan

        except Exception as e:
            logger.error(f"Planning Agent async execution failed: {e}")
            raise AgentExecutionError(
                f"Planning Agent failed for task {input_data.task_id}: {e}"
            ) from e

    async def _decompose_task_async(
        self, requirements: TaskRequirements
    ) -> list[SemanticUnit]:
        """
        Async version of decompose_task using async LLM call.

        Args:
            requirements: TaskRequirements to decompose

        Returns:
            List of validated SemanticUnit objects

        Raises:
            AgentExecutionError: If decomposition fails or output is invalid
        """
        logger.debug(f"Decomposing task {requirements.task_id} (async)")

        # Load prompt template
        try:
            prompt_template = self.load_prompt("planning_agent_v1_decomposition")
        except FileNotFoundError as e:
            raise AgentExecutionError(f"Prompt template not found: {e}") from e

        # Format prompt with requirements
        formatted_prompt = self.format_prompt(
            prompt_template,
            task_id=requirements.task_id,
            description=requirements.description,
            requirements=requirements.requirements,
            context_files="\n".join(requirements.context_files or []),
        )

        # Call LLM (async)
        response = await self.call_llm_async(
            prompt=formatted_prompt,
            max_tokens=4096,
            temperature=0.0,  # Deterministic for consistency
        )

        # Parse response
        content = response.get("content")
        if not isinstance(content, dict):
            raise AgentExecutionError(
                f"LLM returned non-JSON response: {content}\n"
                f"Expected JSON with 'semantic_units' array"
            )

        # Extract semantic units
        if "semantic_units" not in content:
            raise AgentExecutionError(
                f"LLM response missing 'semantic_units' key: {content.keys()}"
            )

        units_data = content["semantic_units"]
        if not isinstance(units_data, list):
            raise AgentExecutionError(
                f"'semantic_units' must be an array, got {type(units_data)}"
            )

        # Validate and create SemanticUnit objects
        semantic_units = []
        for i, unit_data in enumerate(units_data):
            try:
                unit = SemanticUnit.model_validate(unit_data)

                # Verify complexity calculation
                factors = ComplexityFactors(
                    api_interactions=unit.api_interactions,
                    data_transformations=unit.data_transformations,
                    logical_branches=unit.logical_branches,
                    code_entities_modified=unit.code_entities_modified,
                    novelty_multiplier=unit.novelty_multiplier,
                )
                calculated_complexity = calculate_semantic_complexity(factors)

                if abs(unit.est_complexity - calculated_complexity) > 1:
                    logger.warning(
                        f"Unit {unit.unit_id}: Complexity mismatch. "
                        f"LLM reported {unit.est_complexity}, "
                        f"calculated {calculated_complexity}. "
                        f"Using calculated value."
                    )
                    unit.est_complexity = calculated_complexity

                semantic_units.append(unit)

            except Exception as e:
                raise AgentExecutionError(
                    f"Failed to validate semantic unit {i}: {e}\nData: {unit_data}"
                ) from e

        logger.info(
            f"Successfully decomposed into {len(semantic_units)} semantic units (async)"
        )
        return semantic_units

    async def _decompose_task_with_feedback_async(
        self, requirements: TaskRequirements, feedback: list
    ) -> list[SemanticUnit]:
        """
        Async version of decompose_task_with_feedback using async LLM call.

        Args:
            requirements: Original TaskRequirements
            feedback: List of DesignIssue objects

        Returns:
            List of revised SemanticUnit objects

        Raises:
            AgentExecutionError: If decomposition fails or output is invalid
        """
        logger.debug(
            f"Re-decomposing task {requirements.task_id} (async) "
            f"with {len(feedback)} feedback issues"
        )

        # Format feedback issues
        feedback_text = self._format_feedback_issues(feedback)

        # Load feedback-aware prompt template
        try:
            prompt_template = self.load_prompt("planning_agent_v1_with_feedback")
        except FileNotFoundError as e:
            raise AgentExecutionError(f"Feedback prompt template not found: {e}") from e

        # Format prompt
        formatted_prompt = self.format_prompt(
            prompt_template,
            description=requirements.description,
            requirements=requirements.requirements,
            feedback=feedback_text,
        )

        # Call LLM (async)
        response = await self.call_llm_async(
            prompt=formatted_prompt,
            max_tokens=4096,
            temperature=0.0,
        )

        # Parse response
        content = response.get("content")
        if not isinstance(content, dict):
            raise AgentExecutionError(
                f"LLM returned non-JSON response: {content}\n"
                f"Expected JSON with 'semantic_units' array"
            )

        # Extract and validate semantic units
        if "semantic_units" not in content:
            raise AgentExecutionError(
                f"LLM response missing 'semantic_units' key: {content.keys()}"
            )

        units_data = content["semantic_units"]
        if not isinstance(units_data, list):
            raise AgentExecutionError(
                f"'semantic_units' must be an array, got {type(units_data)}"
            )

        semantic_units = []
        for i, unit_data in enumerate(units_data):
            try:
                unit = SemanticUnit.model_validate(unit_data)

                factors = ComplexityFactors(
                    api_interactions=unit.api_interactions,
                    data_transformations=unit.data_transformations,
                    logical_branches=unit.logical_branches,
                    code_entities_modified=unit.code_entities_modified,
                    novelty_multiplier=unit.novelty_multiplier,
                )
                calculated_complexity = calculate_semantic_complexity(factors)

                if abs(unit.est_complexity - calculated_complexity) > 1:
                    logger.warning(
                        f"Unit {unit.unit_id}: Complexity mismatch. Using calculated value."
                    )
                    unit.est_complexity = calculated_complexity

                semantic_units.append(unit)

            except Exception as e:
                raise AgentExecutionError(
                    f"Failed to validate semantic unit {i}: {e}\nData: {unit_data}"
                ) from e

        logger.info(
            f"Successfully re-decomposed into {len(semantic_units)} semantic units (async) "
            f"addressing {len(feedback)} feedback issues"
        )
        return semantic_units
