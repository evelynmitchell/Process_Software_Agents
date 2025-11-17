"""
Design Agent for ASP Platform

The Design Agent is responsible for:
1. Creating Low-Level Design Specifications (FR-002)
2. Transforming requirements + project plan into implementation-ready designs
3. Generating API contracts, data schemas, and component logic
4. Creating design review checklists for the Design Review Agent (FR-003)

This is the second agent in the 7-agent ASP architecture, following the Planning Agent.

Author: ASP Development Team
Date: November 13, 2025
"""

import json
import logging
from pathlib import Path
from typing import Any, Optional

from asp.agents.base_agent import BaseAgent, AgentExecutionError
from asp.models.design import DesignInput, DesignSpecification
from asp.telemetry import track_agent_cost


logger = logging.getLogger(__name__)


class DesignAgent(BaseAgent):
    """
    Design Agent implementation.

    Transforms requirements and project plans into detailed technical designs
    that can be directly implemented by the Coding Agent.

    The Design Agent:
    - Takes requirements + ProjectPlan from Planning Agent as input
    - Generates complete DesignSpecification with:
      * API contracts (endpoints, request/response schemas, error handling)
      * Data schemas (database tables, columns, indexes, relationships)
      * Component logic (classes, interfaces, dependencies, implementation notes)
      * Design review checklist (validation criteria for Design Review Agent)
    - Ensures every semantic unit from planning has corresponding component(s)
    - Outputs implementation-ready design with no ambiguity

    Example:
        >>> from asp.agents.design_agent import DesignAgent
        >>> from asp.models.design import DesignInput
        >>> from asp.models.planning import ProjectPlan
        >>>
        >>> agent = DesignAgent()
        >>> input_data = DesignInput(
        ...     task_id="JWT-AUTH-001",
        ...     requirements="Build JWT authentication system...",
        ...     project_plan=project_plan,  # From Planning Agent
        ... )
        >>> design = agent.execute(input_data)
        >>> print(f"Created design with {len(design.component_logic)} components")
    """

    def __init__(
        self,
        db_path: Optional[Path] = None,
        llm_client: Optional[Any] = None,
    ):
        """
        Initialize Design Agent.

        Args:
            db_path: Optional path to SQLite database for telemetry
            llm_client: Optional LLM client (for dependency injection in tests)
        """
        super().__init__(db_path=db_path, llm_client=llm_client)
        self.agent_version = "1.0.0"
        logger.info("DesignAgent initialized")

    @track_agent_cost(
        agent_role="Design",
        task_id_param="input_data.task_id",
        llm_model="claude-sonnet-4-20250514",
        llm_provider="anthropic",
        agent_version="1.0.0",
    )
    def execute(self, input_data: DesignInput, feedback: Optional[list] = None) -> DesignSpecification:
        """
        Execute the Design Agent to generate a technical design with optional feedback.

        This method:
        1. Loads the design prompt template (with feedback if provided)
        2. Formats it with requirements and project plan
        3. Calls the LLM to generate the design
        4. Parses and validates the response
        5. Verifies semantic unit coverage
        6. Returns complete DesignSpecification

        Args:
            input_data: DesignInput containing requirements, project_plan, etc.
            feedback: Optional list of DesignIssue objects from Design Review
                     requiring redesign (issues with affected_phase="Design" or "Both")

        Returns:
            DesignSpecification with complete technical design

        Raises:
            AgentExecutionError: If design generation fails or output is invalid
            ValidationError: If response doesn't match DesignSpecification schema
        """
        logger.info(
            f"Executing DesignAgent for task_id={input_data.task_id}, "
            f"feedback_items={len(feedback) if feedback else 0}"
        )

        try:
            # Generate the design (with or without feedback)
            if feedback:
                design_spec = self._generate_design_with_feedback(input_data, feedback)
            else:
                design_spec = self._generate_design(input_data)

            # Validate semantic unit coverage
            self._validate_semantic_unit_coverage(design_spec, input_data.project_plan)

            # Validate component dependencies
            self._validate_component_dependencies(design_spec)

            logger.info(
                f"Design generation successful: {len(design_spec.api_contracts)} APIs, "
                f"{len(design_spec.data_schemas)} tables, "
                f"{len(design_spec.component_logic)} components"
            )

            return design_spec

        except Exception as e:
            logger.error(f"DesignAgent execution failed: {e}")
            raise AgentExecutionError(f"Design generation failed: {e}") from e

    def _generate_design(self, input_data: DesignInput) -> DesignSpecification:
        """
        Generate the design specification using LLM.

        Args:
            input_data: DesignInput with requirements and project plan

        Returns:
            DesignSpecification parsed from LLM response

        Raises:
            AgentExecutionError: If LLM call fails or response is invalid
        """
        # Load prompt template
        try:
            prompt_template = self.load_prompt("design_agent_v1_specification")
        except FileNotFoundError as e:
            raise AgentExecutionError(f"Prompt template not found: {e}") from e

        # Format prompt with requirements and project plan
        formatted_prompt = self.format_prompt(
            prompt_template,
            requirements=input_data.requirements,
            project_plan=input_data.project_plan.model_dump_json(indent=2),
            context_files="\n".join(input_data.context_files) if input_data.context_files else "None",
            design_constraints=input_data.design_constraints or "None",
        )

        logger.debug(f"Generated design prompt ({len(formatted_prompt)} chars)")

        # Call LLM to generate design
        response = self.call_llm(
            prompt=formatted_prompt,
            max_tokens=8000,  # Designs can be large
            temperature=0.1,  # Low temperature for consistency
        )

        # Parse response
        content = response.get("content")
        if not isinstance(content, dict):
            raise AgentExecutionError(
                f"LLM returned non-JSON response: {content}\n"
                f"Expected JSON matching DesignSpecification schema"
            )

        logger.debug(f"Received LLM response with {len(content)} top-level keys")

        # Validate and create DesignSpecification
        try:
            design_spec = DesignSpecification(**content)
            return design_spec

        except Exception as e:
            logger.error(f"Failed to validate design specification: {e}")
            logger.debug(f"Response content keys: {content.keys() if isinstance(content, dict) else 'not a dict'}")
            raise AgentExecutionError(f"Design validation failed: {e}") from e

    def _validate_semantic_unit_coverage(
        self,
        design_spec: DesignSpecification,
        project_plan,
    ) -> None:
        """
        Validate that all semantic units from project plan have corresponding components.

        Args:
            design_spec: Generated DesignSpecification
            project_plan: ProjectPlan from Planning Agent

        Raises:
            AgentExecutionError: If semantic units are missing components
        """
        # Get all semantic unit IDs from project plan
        planning_unit_ids = {unit.unit_id for unit in project_plan.semantic_units}

        # Get all semantic unit IDs referenced in design components
        design_unit_ids = {component.semantic_unit_id for component in design_spec.component_logic}

        # Check for missing units
        missing_units = planning_unit_ids - design_unit_ids

        if missing_units:
            logger.error(f"Design is missing components for semantic units: {missing_units}")
            raise AgentExecutionError(
                f"Design incomplete: semantic units {missing_units} have no corresponding components. "
                f"Every semantic unit from planning must have at least one component."
            )

        logger.debug(f"Semantic unit coverage validated: {len(design_unit_ids)}/{len(planning_unit_ids)} units covered")

    def _validate_component_dependencies(self, design_spec: DesignSpecification) -> None:
        """
        Validate component dependencies form a valid DAG (no circular dependencies).

        Args:
            design_spec: Generated DesignSpecification

        Raises:
            AgentExecutionError: If circular dependencies detected
        """
        # Build component name set
        component_names = {component.component_name for component in design_spec.component_logic}

        # Check for invalid dependencies (components that don't exist)
        for component in design_spec.component_logic:
            for dependency in component.dependencies:
                if dependency not in component_names:
                    logger.warning(
                        f"Component '{component.component_name}' depends on "
                        f"'{dependency}' which is not defined in this design. "
                        f"This may be an external dependency."
                    )

        # Simple cycle detection using DFS
        def has_cycle(node: str, visited: set, rec_stack: set, adj_list: dict) -> bool:
            """Detect cycle using DFS."""
            visited.add(node)
            rec_stack.add(node)

            for neighbor in adj_list.get(node, []):
                if neighbor not in visited:
                    if has_cycle(neighbor, visited, rec_stack, adj_list):
                        return True
                elif neighbor in rec_stack:
                    return True

            rec_stack.remove(node)
            return False

        # Build adjacency list for dependency graph
        adj_list = {}
        for component in design_spec.component_logic:
            # Only include dependencies that are internal components
            internal_deps = [dep for dep in component.dependencies if dep in component_names]
            adj_list[component.component_name] = internal_deps

        # Check for cycles
        visited = set()
        rec_stack = set()

        for component_name in component_names:
            if component_name not in visited:
                if has_cycle(component_name, visited, rec_stack, adj_list):
                    logger.error(f"Circular dependency detected involving: {component_name}")
                    raise AgentExecutionError(
                        f"Design contains circular dependencies. "
                        f"Component '{component_name}' is part of a dependency cycle."
                    )

        logger.debug("Component dependencies validated: no circular dependencies detected")

    def _generate_design_with_feedback(
        self, input_data: DesignInput, feedback: list
    ) -> DesignSpecification:
        """
        Generate revised design specification with Design Review feedback.

        This method is called when Design Review has identified Design-phase issues
        that require the design to be revised with corrections.

        Steps:
        1. Format feedback issues into readable text
        2. Load the feedback-aware design prompt template
        3. Format prompt with requirements + project plan + feedback
        4. Call LLM to generate revised design
        5. Parse and validate the response

        Args:
            input_data: Original DesignInput with requirements and project plan
            feedback: List of DesignIssue objects with affected_phase="Design" or "Both"

        Returns:
            Revised DesignSpecification

        Raises:
            AgentExecutionError: If design generation fails or output is invalid
        """
        logger.debug(
            f"Re-generating design for {input_data.task_id} with {len(feedback)} feedback issues"
        )

        # Step 1: Format feedback issues into readable string
        feedback_text = self._format_feedback_issues(feedback)

        # Step 2: Load feedback-aware prompt template
        try:
            prompt_template = self.load_prompt("design_agent_v1_with_feedback")
        except FileNotFoundError as e:
            raise AgentExecutionError(f"Feedback prompt template not found: {e}") from e

        # Step 3: Format prompt with requirements + project plan + feedback
        formatted_prompt = self.format_prompt(
            prompt_template,
            description=input_data.requirements,
            project_plan=input_data.project_plan.model_dump_json(indent=2),
            feedback=feedback_text,
        )

        logger.debug(f"Generated feedback-aware design prompt ({len(formatted_prompt)} chars)")

        # Step 4: Call LLM to generate revised design
        response = self.call_llm(
            prompt=formatted_prompt,
            max_tokens=8000,  # Designs can be large
            temperature=0.1,  # Low temperature for consistency
        )

        # Step 5: Parse response
        content = response.get("content")
        if not isinstance(content, dict):
            raise AgentExecutionError(
                f"LLM returned non-JSON response: {content}\n"
                f"Expected JSON matching DesignSpecification schema"
            )

        logger.debug(f"Received LLM response with {len(content)} top-level keys")

        # Validate and create DesignSpecification
        try:
            design_spec = DesignSpecification(**content)
            logger.info(
                f"Successfully revised design addressing {len(feedback)} feedback issues"
            )
            return design_spec

        except Exception as e:
            logger.error(f"Failed to validate revised design specification: {e}")
            logger.debug(
                f"Response content keys: {content.keys() if isinstance(content, dict) else 'not a dict'}"
            )
            raise AgentExecutionError(f"Revised design validation failed: {e}") from e

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
