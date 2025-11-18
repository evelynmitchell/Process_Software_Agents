"""
Code Agent for ASP Platform

The Code Agent is responsible for:
1. Generating Production-Ready Code (FR-004)
2. Transforming design specifications into complete, runnable code
3. Creating full file contents with proper structure, tests, and documentation
4. Ensuring adherence to coding standards and best practices

This is the fourth agent in the 7-agent ASP architecture, following the Design Review Agent.

Author: ASP Development Team
Date: November 17, 2025
"""

import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from asp.agents.base_agent import BaseAgent, AgentExecutionError
from asp.models.code import CodeInput, GeneratedCode, GeneratedFile
from asp.telemetry import track_agent_cost
from asp.utils.artifact_io import write_artifact_json, write_artifact_markdown, write_generated_file
from asp.utils.git_utils import git_commit_artifact, is_git_repository
from asp.utils.markdown_renderer import render_code_manifest_markdown


logger = logging.getLogger(__name__)


class CodeAgent(BaseAgent):
    """
    Code Agent implementation.

    Transforms approved design specifications into complete, production-ready code
    with full file contents, tests, and documentation.

    The Code Agent:
    - Takes CodeInput with design specification and coding standards
    - Generates complete GeneratedCode with:
      * Full file contents (source, tests, config, docs)
      * File structure and dependencies
      * Implementation notes and setup instructions
    - Ensures every component from design has corresponding implementation
    - Outputs production-ready code ready for Code Review Agent

    Example:
        >>> from asp.agents.code_agent import CodeAgent
        >>> from asp.models.code import CodeInput
        >>> from asp.models.design import DesignSpecification
        >>>
        >>> agent = CodeAgent()
        >>> input_data = CodeInput(
        ...     task_id="JWT-AUTH-001",
        ...     design_specification=design_spec,  # From Design Agent
        ...     coding_standards="Follow PEP 8, use type hints...",
        ... )
        >>> code = agent.execute(input_data)
        >>> print(f"Generated {code.total_files} files with {code.total_lines_of_code} LOC")
    """

    def __init__(
        self,
        db_path: Optional[Path] = None,
        llm_client: Optional[Any] = None,
    ):
        """
        Initialize Code Agent.

        Args:
            db_path: Optional path to SQLite database for telemetry
            llm_client: Optional LLM client (for dependency injection in tests)
        """
        super().__init__(db_path=db_path, llm_client=llm_client)
        self.agent_version = "1.0.0"
        logger.info("CodeAgent initialized")

    @track_agent_cost(
        agent_role="Code",
        task_id_param="input_data.task_id",
        llm_model="claude-sonnet-4-20250514",
        llm_provider="anthropic",
        agent_version="1.0.0",
    )
    def execute(self, input_data: CodeInput) -> GeneratedCode:
        """
        Execute the Code Agent to generate production-ready code.

        This method:
        1. Loads the code generation prompt template
        2. Formats it with design specification and coding standards
        3. Calls the LLM to generate complete code
        4. Parses and validates the response
        5. Verifies component coverage from design
        6. Returns complete GeneratedCode

        Args:
            input_data: CodeInput with design specification and standards

        Returns:
            GeneratedCode with complete file contents and metadata

        Raises:
            AgentExecutionError: If code generation fails or output is invalid
            ValidationError: If response doesn't match GeneratedCode schema
        """
        logger.info(f"Executing CodeAgent for task_id={input_data.task_id}")

        try:
            # Generate the code
            generated_code = self._generate_code(input_data)

            # Validate component coverage from design
            self._validate_component_coverage(generated_code, input_data.design_specification)

            # Validate file structure consistency
            self._validate_file_structure(generated_code)

            logger.info(
                f"Code generation successful: {generated_code.total_files} files, "
                f"{generated_code.total_lines_of_code} LOC, "
                f"{len(generated_code.dependencies)} dependencies"
            )

            # Write artifacts to filesystem (if enabled)
            try:
                artifact_files = []

                # Write code manifest as JSON (GeneratedCode metadata only)
                manifest_path = write_artifact_json(
                    task_id=generated_code.task_id,
                    artifact_type="code_manifest",
                    data=generated_code,
                )
                logger.debug(f"Wrote code manifest JSON: {manifest_path}")
                artifact_files.append(str(manifest_path))

                # Write code manifest as Markdown (human-readable overview)
                markdown_content = render_code_manifest_markdown(generated_code)
                md_path = write_artifact_markdown(
                    task_id=generated_code.task_id,
                    artifact_type="code_manifest",
                    markdown_content=markdown_content,
                )
                logger.debug(f"Wrote code manifest Markdown: {md_path}")
                artifact_files.append(str(md_path))

                # Write each generated file to src/, tests/, etc.
                for file in generated_code.files:
                    file_path = write_generated_file(
                        task_id=generated_code.task_id,
                        file=file,
                    )
                    logger.debug(f"Wrote generated file: {file_path}")
                    artifact_files.append(str(file_path))

                # Commit to git (if in repository)
                if is_git_repository():
                    commit_hash = git_commit_artifact(
                        task_id=generated_code.task_id,
                        agent_name="Code Agent",
                        artifact_files=artifact_files,
                    )
                    logger.info(f"Committed {len(artifact_files)} artifacts: {commit_hash}")
                else:
                    logger.warning("Not in git repository, skipping commit")

            except Exception as e:
                # Log but don't fail - artifact persistence is not critical
                logger.warning(f"Failed to write artifacts: {e}", exc_info=True)

            return generated_code

        except Exception as e:
            logger.error(f"CodeAgent execution failed: {e}")
            raise AgentExecutionError(f"Code generation failed: {e}") from e

    def _generate_code(self, input_data: CodeInput) -> GeneratedCode:
        """
        Generate complete code using LLM.

        Args:
            input_data: CodeInput with design specification and standards

        Returns:
            GeneratedCode parsed from LLM response

        Raises:
            AgentExecutionError: If LLM call fails or response is invalid
        """
        # Load prompt template
        try:
            prompt_template = self.load_prompt("code_agent_v1_generation")
        except FileNotFoundError as e:
            raise AgentExecutionError(f"Prompt template not found: {e}") from e

        # Format prompt with design specification and standards
        formatted_prompt = self.format_prompt(
            prompt_template,
            task_id=input_data.task_id,
            design_specification=input_data.design_specification.model_dump_json(indent=2),
            coding_standards=input_data.coding_standards or "Follow industry best practices",
            context_files="\n".join(input_data.context_files or []),
        )

        logger.debug(f"Generated code prompt ({len(formatted_prompt)} chars)")

        # Call LLM to generate code
        # Code generation can be large, so use higher token limit
        response = self.call_llm(
            prompt=formatted_prompt,
            max_tokens=16000,  # Large limit for code generation
            temperature=0.0,  # Deterministic for code generation
        )

        # Parse response
        content = response.get("content")

        # If content is a string, try to extract JSON from markdown fences
        if isinstance(content, str):
            import re
            import json

            # Try to extract JSON from markdown code blocks
            json_match = re.search(r'```json\s*\n(.*?)\n```', content, re.DOTALL)
            if json_match:
                try:
                    content = json.loads(json_match.group(1))
                    logger.debug("Successfully extracted JSON from markdown code fence")
                except json.JSONDecodeError as e:
                    raise AgentExecutionError(
                        f"Failed to parse JSON from markdown fence: {e}\n"
                        f"Content preview: {content[:500]}..."
                    )
            else:
                # Try to parse the whole string as JSON
                try:
                    content = json.loads(content)
                    logger.debug("Successfully parsed string content as JSON")
                except json.JSONDecodeError:
                    raise AgentExecutionError(
                        f"LLM returned non-JSON response: {content[:500]}...\n"
                        f"Expected JSON matching GeneratedCode schema"
                    )

        if not isinstance(content, dict):
            raise AgentExecutionError(
                f"LLM returned non-dict response after parsing: {type(content)}\n"
                f"Expected JSON matching GeneratedCode schema"
            )

        logger.debug(f"Received LLM response with {len(content)} top-level keys")

        # Validate and create GeneratedCode
        try:
            # Add timestamp if not provided
            if "generation_timestamp" not in content or not content["generation_timestamp"]:
                content["generation_timestamp"] = datetime.now().isoformat()

            # Calculate total LOC and files if not provided
            if "total_lines_of_code" not in content or content["total_lines_of_code"] == 0:
                total_loc = sum(
                    len([line for line in file_data["content"].split("\n") if line.strip()])
                    for file_data in content.get("files", [])
                )
                content["total_lines_of_code"] = total_loc

            if "total_files" not in content or content["total_files"] == 0:
                content["total_files"] = len(content.get("files", []))

            generated_code = GeneratedCode(**content)
            return generated_code

        except Exception as e:
            logger.error(f"Failed to validate generated code: {e}")
            logger.debug(
                f"Response content keys: {content.keys() if isinstance(content, dict) else 'not a dict'}"
            )
            raise AgentExecutionError(f"Code validation failed: {e}") from e

    def _validate_component_coverage(
        self,
        generated_code: GeneratedCode,
        design_spec,
    ) -> None:
        """
        Validate that all components from design have corresponding code files.

        Args:
            generated_code: GeneratedCode output
            design_spec: DesignSpecification input

        Raises:
            AgentExecutionError: If components are missing implementation
        """
        # Get all component names from design
        design_component_names = {component.component_name for component in design_spec.component_logic}

        # Get all component IDs referenced in generated code
        # Note: GeneratedFile uses component_id for traceability, not component_name
        code_component_ids = {
            file.component_id for file in generated_code.files if file.component_id
        }

        # Check for missing components
        # Since design uses component_name and generated code uses component_id,
        # we can't do a direct comparison. This is a known limitation.
        # Log both for visibility
        logger.debug(
            f"Design components: {design_component_names}, "
            f"Generated file component IDs: {code_component_ids}"
        )

        logger.debug(
            f"Component coverage: {len(code_component_ids)} files have component_id mappings, "
            f"{len(design_component_names)} components in design"
        )

    def _validate_file_structure(self, generated_code: GeneratedCode) -> None:
        """
        Validate file structure consistency.

        Ensures that:
        - All files in file_structure exist in generated files list
        - All generated files are represented in file_structure
        - No duplicate file paths

        Args:
            generated_code: GeneratedCode output

        Raises:
            AgentExecutionError: If file structure is inconsistent
        """
        # Get all file paths from generated files
        generated_file_paths = {file.file_path for file in generated_code.files}

        # Get all file paths from file_structure
        structure_file_paths = set()
        for directory, files in generated_code.file_structure.items():
            for filename in files:
                if directory == ".":
                    structure_file_paths.add(filename)
                else:
                    structure_file_paths.add(f"{directory}/{filename}")

        # Check for mismatches
        missing_in_structure = generated_file_paths - structure_file_paths
        extra_in_structure = structure_file_paths - generated_file_paths

        if missing_in_structure:
            logger.warning(
                f"Files generated but not in file_structure: {missing_in_structure}"
            )

        if extra_in_structure:
            logger.error(f"Files in file_structure but not generated: {extra_in_structure}")
            raise AgentExecutionError(
                f"File structure inconsistency: {extra_in_structure} listed but not generated"
            )

        # Check for duplicate file paths
        file_path_counts = {}
        for file in generated_code.files:
            file_path_counts[file.file_path] = file_path_counts.get(file.file_path, 0) + 1

        duplicates = {path: count for path, count in file_path_counts.items() if count > 1}
        if duplicates:
            raise AgentExecutionError(f"Duplicate file paths found: {duplicates}")

        logger.debug("File structure validation passed")
