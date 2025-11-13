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
from typing import Optional

from asp.agents.base_agent import BaseAgent, AgentExecutionError
from asp.models.planning import TaskRequirements, ProjectPlan, SemanticUnit
from asp.utils.semantic_complexity import calculate_semantic_complexity, ComplexityFactors
from asp.telemetry import track_agent_cost


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
        db_path: Optional[Path] = None,
        llm_client: Optional[any] = None,
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
        llm_model="claude-sonnet-4-20250514",
        llm_provider="anthropic",
        agent_version="1.0.0",
    )
    def execute(self, input_data: TaskRequirements) -> ProjectPlan:
        """
        Execute Planning Agent logic.

        Steps:
        1. Load and format decomposition prompt
        2. Call LLM to decompose task into semantic units
        3. Validate and calculate complexity for each unit
        4. (Phase 2) Run PROBE-AI estimation if available
        5. Return ProjectPlan

        Args:
            input_data: TaskRequirements with task details

        Returns:
            ProjectPlan with decomposed semantic units and complexity scores

        Raises:
            AgentExecutionError: If decomposition fails
        """
        logger.info(
            f"Planning Agent executing for task_id={input_data.task_id}, "
            f"description='{input_data.description[:50]}...'"
        )

        try:
            # Step 1: Decompose task into semantic units
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
                    f"Failed to validate semantic unit {i}: {e}\n"
                    f"Data: {unit_data}"
                ) from e

        logger.info(f"Successfully decomposed into {len(semantic_units)} semantic units")
        return semantic_units
