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

# pylint: disable=logging-fstring-interpolation,no-else-return

import logging
import os
from pathlib import Path
from typing import Any

from asp.agents.base_agent import AgentExecutionError, BaseAgent
from asp.models.design import DesignInput, DesignSpecification
from asp.parsers.design_markdown_parser import DesignMarkdownParser
from asp.telemetry import track_agent_cost
from asp.utils.artifact_io import write_artifact_json, write_artifact_markdown
from asp.utils.git_utils import git_commit_artifact, is_git_repository
from asp.utils.json_extraction import JSONExtractionError, extract_json_from_response
from asp.utils.markdown_renderer import render_design_markdown

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
        db_path: Path | None = None,
        llm_client: Any | None = None,
        use_markdown: bool | None = None,
        model: str | None = None,
    ):
        """
        Initialize Design Agent.

        Args:
            db_path: Optional path to SQLite database for telemetry
            llm_client: Optional LLM client (for dependency injection in tests)
            use_markdown: Optional flag to use markdown output format instead of JSON.
                         If None, checks ASP_DESIGN_AGENT_USE_MARKDOWN environment variable.
                         Defaults to False if neither is set.
            model: Optional model name to use for LLM calls (e.g., "claude-sonnet-4-5-20250929").
                  If None, uses the default model from LLMClient.
        """
        super().__init__(db_path=db_path, llm_client=llm_client)
        self.agent_version = "1.0.0"
        self.model = model  # Store model for use in LLM calls

        # Determine markdown mode: explicit parameter > env var > default (False)
        if use_markdown is not None:
            self.use_markdown = use_markdown
        else:
            env_value = os.getenv("ASP_DESIGN_AGENT_USE_MARKDOWN", "false").lower()
            self.use_markdown = env_value in ("true", "1", "yes")

        # Initialize markdown parser if using markdown mode
        self.markdown_parser = DesignMarkdownParser() if self.use_markdown else None

        mode_str = "markdown" if self.use_markdown else "JSON"
        model_str = f", model: {self.model}" if self.model else ""
        logger.info(f"DesignAgent initialized (output mode: {mode_str}{model_str})")

    @track_agent_cost(
        agent_role="Design",
        task_id_param="input_data.task_id",
        llm_model="claude-sonnet-4-20250514",
        llm_provider="anthropic",
        agent_version="1.0.0",
    )
    def execute(
        self, input_data: DesignInput, feedback: list | None = None
    ) -> DesignSpecification:
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

            # Write artifacts to filesystem (if enabled)
            try:
                # Write JSON artifact
                json_path = write_artifact_json(
                    task_id=design_spec.task_id,
                    artifact_type="design",
                    data=design_spec,
                )
                logger.debug(f"Wrote design JSON: {json_path}")

                # Write Markdown artifact
                markdown_content = render_design_markdown(design_spec)
                md_path = write_artifact_markdown(
                    task_id=design_spec.task_id,
                    artifact_type="design",
                    markdown_content=markdown_content,
                )
                logger.debug(f"Wrote design Markdown: {md_path}")

                # Commit to git (if in repository)
                if is_git_repository():
                    commit_hash = git_commit_artifact(
                        task_id=design_spec.task_id,
                        agent_name="Design Agent",
                        artifact_files=[str(json_path), str(md_path)],
                    )
                    if commit_hash:
                        logger.info(f"Committed artifacts: {commit_hash}")
                else:
                    logger.warning("Not in git repository, skipping commit")

            except Exception as e:
                # Log but don't fail - artifact persistence is not critical
                logger.warning(f"Failed to write artifacts: {e}", exc_info=True)

            return design_spec

        except Exception as e:
            logger.error(f"DesignAgent execution failed: {e}")
            raise AgentExecutionError(f"Design generation failed: {e}") from e

    def _generate_design(self, input_data: DesignInput) -> DesignSpecification:
        """
        Generate the design specification using LLM.

        Supports both JSON and Markdown output formats based on use_markdown flag.

        Args:
            input_data: DesignInput with requirements and project plan

        Returns:
            DesignSpecification parsed from LLM response

        Raises:
            AgentExecutionError: If LLM call fails or response is invalid
        """
        if self.use_markdown:
            return self._generate_design_markdown(input_data)
        else:
            return self._generate_design_json(input_data)

    def _generate_design_json(self, input_data: DesignInput) -> DesignSpecification:
        """
        Generate design specification using JSON format (legacy mode).

        Args:
            input_data: DesignInput with requirements and project plan

        Returns:
            DesignSpecification parsed from JSON response

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
            context_files=(
                "\n".join(input_data.context_files)
                if input_data.context_files
                else "None"
            ),
            design_constraints=input_data.design_constraints or "None",
        )

        logger.debug(f"Generated design prompt ({len(formatted_prompt)} chars)")

        # Call LLM to generate design
        response = self.call_llm(
            prompt=formatted_prompt,
            model=self.model,  # Use configured model or default
            max_tokens=16000,  # Markdown designs can be large (increased from 8000)
            temperature=0.1,  # Low temperature for consistency
        )

        # Parse response with robust JSON extraction
        try:
            content = extract_json_from_response(response)
        except JSONExtractionError as e:
            raise AgentExecutionError(f"Design generation failed: {e}") from e

        logger.debug(f"Received LLM response with {len(content)} top-level keys")

        # Fix: Coerce technology_stack boolean values to strings
        # LLM sometimes returns {"standard_library_only": true} instead of "yes"/"no"
        if "technology_stack" in content and isinstance(
            content["technology_stack"], dict
        ):
            for key, value in content["technology_stack"].items():
                if isinstance(value, bool):
                    content["technology_stack"][key] = "yes" if value else "no"
                elif not isinstance(value, str):
                    content["technology_stack"][key] = str(value)

        # Validate and create DesignSpecification
        try:
            design_spec = DesignSpecification(**content)
            return design_spec

        except Exception as e:
            logger.error(f"Failed to validate design specification: {e}")
            logger.debug(
                f"Response content keys: {content.keys() if isinstance(content, dict) else 'not a dict'}"
            )
            # Debug: dump the problematic field
            if isinstance(content, dict) and "api_contracts" in content:
                import json

                logger.error(
                    f"DEBUG: api_contracts content: {json.dumps(content['api_contracts'], indent=2)}"
                )
            raise AgentExecutionError(f"Design validation failed: {e}") from e

    def _generate_design_markdown(self, input_data: DesignInput) -> DesignSpecification:
        """
        Generate design specification using Markdown format (v2 mode).

        Args:
            input_data: DesignInput with requirements and project plan

        Returns:
            DesignSpecification parsed from Markdown response

        Raises:
            AgentExecutionError: If LLM call fails or response is invalid
        """
        # Load markdown prompt template
        try:
            prompt_template = self.load_prompt("design_agent_v2_markdown")
        except FileNotFoundError as e:
            raise AgentExecutionError(f"Markdown prompt template not found: {e}") from e

        # Format prompt with requirements and project plan
        # Format project plan as readable text (not JSON for markdown mode)
        project_plan_text = self._format_project_plan_for_markdown(
            input_data.project_plan
        )

        formatted_prompt = self.format_prompt(
            prompt_template,
            task_id=input_data.task_id,
            requirements=input_data.requirements,
            project_plan=project_plan_text,
            context_files=(
                "\n".join(input_data.context_files)
                if input_data.context_files
                else "None"
            ),
            design_constraints=input_data.design_constraints or "None",
        )

        logger.debug(
            f"Generated markdown design prompt ({len(formatted_prompt)} chars)"
        )

        # Call LLM to generate design
        response = self.call_llm(
            prompt=formatted_prompt,
            model=self.model,  # Use configured model or default
            max_tokens=16000,  # Markdown designs can be large (increased from 8000)
            temperature=0.1,  # Low temperature for consistency
        )

        # Parse response - should be markdown text
        # Use raw_content to avoid JSON auto-parsing
        content = response.get("raw_content") or response.get("content")
        if not isinstance(content, str):
            raise AgentExecutionError(
                f"LLM returned non-string response in markdown mode: {type(content)}\n"
                f"Expected markdown text"
            )

        logger.debug(f"Received markdown response ({len(content)} chars)")

        # Parse markdown to dict
        try:
            design_dict = self.markdown_parser.parse(content)
            logger.debug(
                f"Parsed markdown into dict with {len(design_dict)} top-level keys"
            )
        except Exception as e:
            logger.error(f"Failed to parse markdown: {e}")
            # Log first 500 chars of markdown for debugging
            logger.debug(f"Markdown preview: {content[:500]}...")
            raise AgentExecutionError(f"Markdown parsing failed: {e}") from e

        # Validate and create DesignSpecification
        try:
            design_spec = DesignSpecification(**design_dict)
            return design_spec

        except Exception as e:
            logger.error(f"Failed to validate design specification from markdown: {e}")
            logger.debug(f"Parsed dict keys: {design_dict.keys()}")
            raise AgentExecutionError(
                f"Design validation failed after markdown parsing: {e}"
            ) from e

    def _format_project_plan_for_markdown(self, project_plan) -> str:
        """
        Format project plan as human-readable text for markdown prompts.

        Args:
            project_plan: ProjectPlan from Planning Agent

        Returns:
            Formatted text representation of project plan
        """
        lines = [
            f"Project ID: {project_plan.project_id if hasattr(project_plan, 'project_id') else 'N/A'}",
            f"Task ID: {project_plan.task_id}",
            f"Total Complexity: {project_plan.total_est_complexity}",
            "",
            "Semantic Units:",
        ]

        for unit in project_plan.semantic_units:
            lines.append(f"\n{unit.unit_id}: {unit.description}")
            lines.append(f"  - Complexity: {unit.est_complexity}")
            if unit.dependencies:
                lines.append(f"  - Dependencies: {', '.join(unit.dependencies)}")

        return "\n".join(lines)

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
        design_unit_ids = {
            component.semantic_unit_id for component in design_spec.component_logic
        }

        # Check for missing units
        missing_units = planning_unit_ids - design_unit_ids

        if missing_units:
            logger.error(
                f"Design is missing components for semantic units: {missing_units}"
            )
            raise AgentExecutionError(
                f"Design incomplete: semantic units {missing_units} have no corresponding components. "
                f"Every semantic unit from planning must have at least one component."
            )

        logger.debug(
            f"Semantic unit coverage validated: {len(design_unit_ids)}/{len(planning_unit_ids)} units covered"
        )

    def _validate_component_dependencies(
        self, design_spec: DesignSpecification
    ) -> None:
        """
        Validate component dependencies form a valid DAG (no circular dependencies).

        Args:
            design_spec: Generated DesignSpecification

        Raises:
            AgentExecutionError: If circular dependencies detected
        """
        # Build component name set
        component_names = {
            component.component_name for component in design_spec.component_logic
        }

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
            internal_deps = [
                dep for dep in component.dependencies if dep in component_names
            ]
            adj_list[component.component_name] = internal_deps

        # Check for cycles
        visited = set()
        rec_stack = set()

        for component_name in component_names:
            if component_name not in visited:
                if has_cycle(component_name, visited, rec_stack, adj_list):
                    logger.error(
                        f"Circular dependency detected involving: {component_name}"
                    )
                    raise AgentExecutionError(
                        f"Design contains circular dependencies. "
                        f"Component '{component_name}' is part of a dependency cycle."
                    )

        logger.debug(
            "Component dependencies validated: no circular dependencies detected"
        )

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

        logger.debug(
            f"Generated feedback-aware design prompt ({len(formatted_prompt)} chars)"
        )

        # Step 4: Call LLM to generate revised design
        response = self.call_llm(
            prompt=formatted_prompt,
            max_tokens=16000,  # Markdown designs can be large (increased from 8000)
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

    # =========================================================================
    # Async Methods (ADR 008 Phase 2)
    # =========================================================================

    async def execute_async(
        self, input_data: DesignInput, feedback: list | None = None
    ) -> DesignSpecification:
        """
        Asynchronous version of execute for parallel agent execution.

        Native async implementation that uses call_llm_async() instead of
        call_llm(). Use this method when running multiple agents concurrently.

        Args:
            input_data: DesignInput containing requirements, project_plan, etc.
            feedback: Optional list of DesignIssue objects from Design Review

        Returns:
            DesignSpecification with complete technical design

        Raises:
            AgentExecutionError: If design generation fails or output is invalid
        """
        logger.info(
            f"Executing DesignAgent (async) for task_id={input_data.task_id}, "
            f"feedback_items={len(feedback) if feedback else 0}"
        )

        try:
            # Generate the design (async LLM call)
            if feedback:
                design_spec = await self._generate_design_with_feedback_async(
                    input_data, feedback
                )
            else:
                design_spec = await self._generate_design_async(input_data)

            # Validate semantic unit coverage (sync - fast validation)
            self._validate_semantic_unit_coverage(design_spec, input_data.project_plan)

            # Validate component dependencies (sync - fast validation)
            self._validate_component_dependencies(design_spec)

            logger.info(
                f"Design generation successful (async): "
                f"{len(design_spec.api_contracts)} APIs, "
                f"{len(design_spec.data_schemas)} tables, "
                f"{len(design_spec.component_logic)} components"
            )

            return design_spec

        except Exception as e:
            logger.error(f"DesignAgent async execution failed: {e}")
            raise AgentExecutionError(f"Design generation failed: {e}") from e

    async def _generate_design_async(
        self, input_data: DesignInput
    ) -> DesignSpecification:
        """
        Async version of _generate_design using async LLM call.

        Args:
            input_data: DesignInput with requirements and project plan

        Returns:
            DesignSpecification parsed from LLM response

        Raises:
            AgentExecutionError: If LLM call fails or response is invalid
        """
        if self.use_markdown:
            return await self._generate_design_markdown_async(input_data)
        else:
            return await self._generate_design_json_async(input_data)

    async def _generate_design_json_async(
        self, input_data: DesignInput
    ) -> DesignSpecification:
        """
        Async version of _generate_design_json using async LLM call.

        Args:
            input_data: DesignInput with requirements and project plan

        Returns:
            DesignSpecification parsed from JSON response

        Raises:
            AgentExecutionError: If LLM call fails or response is invalid
        """
        # Load prompt template
        try:
            prompt_template = self.load_prompt("design_agent_v1_specification")
        except FileNotFoundError as e:
            raise AgentExecutionError(f"Prompt template not found: {e}") from e

        # Format prompt
        formatted_prompt = self.format_prompt(
            prompt_template,
            requirements=input_data.requirements,
            project_plan=input_data.project_plan.model_dump_json(indent=2),
            context_files=(
                "\n".join(input_data.context_files)
                if input_data.context_files
                else "None"
            ),
            design_constraints=input_data.design_constraints or "None",
        )

        logger.debug(f"Generated design prompt ({len(formatted_prompt)} chars)")

        # Call LLM (async)
        response = await self.call_llm_async(
            prompt=formatted_prompt,
            model=self.model,
            max_tokens=16000,
            temperature=0.1,
        )

        # Parse response with robust JSON extraction
        try:
            content = extract_json_from_response(response)
        except JSONExtractionError as e:
            raise AgentExecutionError(f"Design generation failed: {e}") from e

        logger.debug(f"Received LLM response with {len(content)} top-level keys")

        # Fix: Coerce technology_stack boolean values to strings
        if "technology_stack" in content and isinstance(
            content["technology_stack"], dict
        ):
            for key, value in content["technology_stack"].items():
                if isinstance(value, bool):
                    content["technology_stack"][key] = "yes" if value else "no"
                elif not isinstance(value, str):
                    content["technology_stack"][key] = str(value)

        # Validate and create DesignSpecification
        try:
            design_spec = DesignSpecification(**content)
            return design_spec
        except Exception as e:
            logger.error(f"Failed to validate design specification: {e}")
            raise AgentExecutionError(f"Design validation failed: {e}") from e

    async def _generate_design_markdown_async(
        self, input_data: DesignInput
    ) -> DesignSpecification:
        """
        Async version of _generate_design_markdown using async LLM call.

        Args:
            input_data: DesignInput with requirements and project plan

        Returns:
            DesignSpecification parsed from Markdown response

        Raises:
            AgentExecutionError: If LLM call fails or response is invalid
        """
        # Load markdown prompt template
        try:
            prompt_template = self.load_prompt("design_agent_v2_markdown")
        except FileNotFoundError as e:
            raise AgentExecutionError(f"Markdown prompt template not found: {e}") from e

        # Format prompt
        project_plan_text = self._format_project_plan_for_markdown(
            input_data.project_plan
        )

        formatted_prompt = self.format_prompt(
            prompt_template,
            task_id=input_data.task_id,
            requirements=input_data.requirements,
            project_plan=project_plan_text,
            context_files=(
                "\n".join(input_data.context_files)
                if input_data.context_files
                else "None"
            ),
            design_constraints=input_data.design_constraints or "None",
        )

        logger.debug(
            f"Generated markdown design prompt ({len(formatted_prompt)} chars)"
        )

        # Call LLM (async)
        response = await self.call_llm_async(
            prompt=formatted_prompt,
            model=self.model,
            max_tokens=16000,
            temperature=0.1,
        )

        # Parse response
        content = response.get("raw_content") or response.get("content")
        if not isinstance(content, str):
            raise AgentExecutionError(
                f"LLM returned non-string response in markdown mode: {type(content)}"
            )

        logger.debug(f"Received markdown response ({len(content)} chars)")

        # Parse markdown to dict
        try:
            design_dict = self.markdown_parser.parse(content)
            logger.debug(
                f"Parsed markdown into dict with {len(design_dict)} top-level keys"
            )
        except Exception as e:
            logger.error(f"Failed to parse markdown: {e}")
            raise AgentExecutionError(f"Markdown parsing failed: {e}") from e

        # Validate and create DesignSpecification
        try:
            design_spec = DesignSpecification(**design_dict)
            return design_spec
        except Exception as e:
            logger.error(f"Failed to validate design specification from markdown: {e}")
            raise AgentExecutionError(
                f"Design validation failed after markdown parsing: {e}"
            ) from e

    async def _generate_design_with_feedback_async(
        self, input_data: DesignInput, feedback: list
    ) -> DesignSpecification:
        """
        Async version of _generate_design_with_feedback using async LLM call.

        Args:
            input_data: Original DesignInput with requirements and project plan
            feedback: List of DesignIssue objects

        Returns:
            Revised DesignSpecification

        Raises:
            AgentExecutionError: If design generation fails or output is invalid
        """
        logger.debug(
            f"Re-generating design (async) for {input_data.task_id} "
            f"with {len(feedback)} feedback issues"
        )

        # Format feedback issues
        feedback_text = self._format_feedback_issues(feedback)

        # Load feedback-aware prompt template
        try:
            prompt_template = self.load_prompt("design_agent_v1_with_feedback")
        except FileNotFoundError as e:
            raise AgentExecutionError(f"Feedback prompt template not found: {e}") from e

        # Format prompt
        formatted_prompt = self.format_prompt(
            prompt_template,
            description=input_data.requirements,
            project_plan=input_data.project_plan.model_dump_json(indent=2),
            feedback=feedback_text,
        )

        logger.debug(
            f"Generated feedback-aware design prompt ({len(formatted_prompt)} chars)"
        )

        # Call LLM (async)
        response = await self.call_llm_async(
            prompt=formatted_prompt,
            max_tokens=16000,
            temperature=0.1,
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
            logger.info(
                f"Successfully revised design (async) "
                f"addressing {len(feedback)} feedback issues"
            )
            return design_spec
        except Exception as e:
            logger.error(f"Failed to validate revised design specification: {e}")
            raise AgentExecutionError(f"Revised design validation failed: {e}") from e
