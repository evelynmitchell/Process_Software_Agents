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
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from asp.agents.base_agent import AgentExecutionError, BaseAgent
from asp.models.code import (
    CodeInput,
    FileManifest,
    FileMetadata,
    GeneratedCode,
    GeneratedFile,
)
from asp.telemetry import track_agent_cost
from asp.utils.artifact_io import (
    write_artifact_json,
    write_artifact_markdown,
    write_generated_file,
)
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
        use_multi_stage: Optional[bool] = None,
    ):
        """
        Initialize Code Agent.

        Args:
            db_path: Optional path to SQLite database for telemetry
            llm_client: Optional LLM client (for dependency injection in tests)
            use_multi_stage: Optional flag to enable multi-stage generation.
                If None, checks ASP_MULTI_STAGE_CODE_GEN environment variable.
                If True, uses multi-stage generation (manifest + individual files).
                If False, uses legacy single-call generation.
        """
        super().__init__(db_path=db_path, llm_client=llm_client)
        self.agent_version = "1.0.0"

        # Determine multi-stage mode: explicit param > env var > default (False)
        if use_multi_stage is not None:
            self.use_multi_stage = use_multi_stage
        else:
            self.use_multi_stage = (
                os.getenv("ASP_MULTI_STAGE_CODE_GEN", "false").lower() == "true"
            )

        mode = "multi-stage" if self.use_multi_stage else "single-call"
        logger.info(f"CodeAgent initialized (mode: {mode})")

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
            self._validate_component_coverage(
                generated_code, input_data.design_specification
            )

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

                # Write each generated file to artifacts/{task_id}/generated_code/
                from pathlib import Path

                generated_code_base = (
                    Path("artifacts") / generated_code.task_id / "generated_code"
                )

                for file in generated_code.files:
                    file_path = write_generated_file(
                        task_id=generated_code.task_id,
                        file=file,
                        base_path=str(generated_code_base),
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
                    logger.info(
                        f"Committed {len(artifact_files)} artifacts: {commit_hash}"
                    )
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

        Supports two modes via ASP_MULTI_STAGE_CODE_GEN environment variable:
        - "true": Use multi-stage generation (manifest + individual files)
        - "false" (default): Use legacy single-call generation

        Args:
            input_data: CodeInput with design specification and standards

        Returns:
            GeneratedCode parsed from LLM response

        Raises:
            AgentExecutionError: If LLM call fails or response is invalid
        """
        # Use mode determined at initialization
        if self.use_multi_stage:
            logger.info("Using multi-stage code generation")
            return self._generate_code_multi_stage(input_data)
        else:
            logger.info("Using legacy single-call code generation")
            return self._generate_code_single_call(input_data)

    def _generate_code_single_call(self, input_data: CodeInput) -> GeneratedCode:
        """
        Generate complete code using single LLM call (legacy approach).

        This is the original approach that generates all code in one JSON response.
        Can fail with JSONDecodeError for large code blocks due to escaping issues.

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
        # Escape curly braces in design specification JSON to avoid format() issues
        design_spec_json = input_data.design_specification.model_dump_json(indent=2)
        design_spec_escaped = design_spec_json.replace("{", "{{").replace("}", "}}")

        formatted_prompt = self.format_prompt(
            prompt_template,
            task_id=input_data.task_id,
            design_specification=design_spec_escaped,
            coding_standards=input_data.coding_standards
            or "Follow industry best practices",
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
            import json
            import re

            # Try to extract JSON from markdown code blocks
            # More robust pattern that handles various whitespace formatting:
            # - Allows any whitespace (including newlines) after ```json
            # - Allows any whitespace before closing ```
            # - Handles cases with/without newlines in various positions
            json_match = re.search(r"```json\s*(.*?)\s*```", content, re.DOTALL)
            if json_match:
                try:
                    # Extract and strip the JSON content
                    json_str = json_match.group(1).strip()
                    content = json.loads(json_str)
                    logger.debug("Successfully extracted JSON from markdown code fence")
                except json.JSONDecodeError as e:
                    # Provide more helpful error message with the actual JSON string attempted
                    json_preview = json_match.group(1).strip()[:500]
                    raise AgentExecutionError(
                        f"Failed to parse JSON from markdown fence: {e}\n"
                        f"JSON content preview: {json_preview}..."
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
            if (
                "generation_timestamp" not in content
                or not content["generation_timestamp"]
            ):
                content["generation_timestamp"] = datetime.now().isoformat()

            # Calculate total LOC and files if not provided
            if (
                "total_lines_of_code" not in content
                or content["total_lines_of_code"] == 0
            ):
                total_loc = sum(
                    len(
                        [
                            line
                            for line in file_data["content"].split("\n")
                            if line.strip()
                        ]
                    )
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
        design_component_names = {
            component.component_name for component in design_spec.component_logic
        }

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
            logger.error(
                f"Files in file_structure but not generated: {extra_in_structure}"
            )
            raise AgentExecutionError(
                f"File structure inconsistency: {extra_in_structure} listed but not generated"
            )

        # Check for duplicate file paths
        file_path_counts = {}
        for file in generated_code.files:
            file_path_counts[file.file_path] = (
                file_path_counts.get(file.file_path, 0) + 1
            )

        duplicates = {
            path: count for path, count in file_path_counts.items() if count > 1
        }
        if duplicates:
            raise AgentExecutionError(f"Duplicate file paths found: {duplicates}")

        logger.debug("File structure validation passed")

    def _generate_file_manifest(self, input_data: CodeInput) -> FileManifest:
        """
        Generate file manifest using LLM (Phase 1 of multi-stage generation).

        This is Phase 1 of the multi-stage code generation process. It generates
        a manifest listing all files that need to be created, along with their
        metadata (file type, description, estimated lines, dependencies).

        The manifest is a small JSON output (2-5KB) that doesn't contain any
        actual code content, avoiding the JSON escaping issues that occur when
        embedding large code blocks in JSON strings.

        Args:
            input_data: CodeInput with design specification and standards

        Returns:
            FileManifest with list of all files and their metadata

        Raises:
            AgentExecutionError: If LLM call fails or response is invalid
        """
        # Load manifest generation prompt template
        try:
            prompt_template = self.load_prompt("code_agent_v2_manifest")
        except FileNotFoundError as e:
            raise AgentExecutionError(f"Manifest prompt template not found: {e}") from e

        # Format prompt with design specification and standards
        # Escape curly braces in design specification JSON to avoid format() issues
        design_spec_json = input_data.design_specification.model_dump_json(indent=2)
        design_spec_escaped = design_spec_json.replace("{", "{{").replace("}", "}}")

        formatted_prompt = self.format_prompt(
            prompt_template,
            task_id=input_data.task_id,
            design_specification=design_spec_escaped,
            coding_standards=input_data.coding_standards
            or "Follow industry best practices",
            context_files="\n".join(input_data.context_files or []),
        )

        logger.debug(f"Generated manifest prompt ({len(formatted_prompt)} chars)")

        # Call LLM to generate manifest
        # Manifest is small, so use lower token limit
        response = self.call_llm(
            prompt=formatted_prompt,
            max_tokens=4000,  # Sufficient for manifest (no code content)
            temperature=0.0,  # Deterministic for manifest generation
        )

        # Parse response
        content = response.get("content")

        # If content is a string, try to extract JSON from markdown fences
        if isinstance(content, str):
            import json
            import re

            # Try to extract JSON from markdown code blocks
            json_match = re.search(r"```json\s*(.*?)\s*```", content, re.DOTALL)
            if json_match:
                try:
                    json_str = json_match.group(1).strip()
                    content = json.loads(json_str)
                    logger.debug("Successfully extracted JSON from markdown code fence")
                except json.JSONDecodeError as e:
                    json_preview = json_match.group(1).strip()[:500]
                    raise AgentExecutionError(
                        f"Failed to parse manifest JSON from markdown fence: {e}\n"
                        f"JSON content preview: {json_preview}..."
                    )
            else:
                # Try to parse the whole string as JSON
                try:
                    content = json.loads(content)
                    logger.debug("Successfully parsed string content as JSON")
                except json.JSONDecodeError:
                    raise AgentExecutionError(
                        f"LLM returned non-JSON response: {content[:500]}...\n"
                        f"Expected JSON matching FileManifest schema"
                    )

        if not isinstance(content, dict):
            raise AgentExecutionError(
                f"LLM returned non-dict response after parsing: {type(content)}\n"
                f"Expected JSON matching FileManifest schema"
            )

        logger.debug(f"Received manifest response with {len(content)} top-level keys")

        # Validate and create FileManifest
        try:
            # Ensure total_files matches actual count
            if "total_files" not in content or content["total_files"] == 0:
                content["total_files"] = len(content.get("files", []))

            # Calculate total_estimated_lines if not provided
            if (
                "total_estimated_lines" not in content
                or content["total_estimated_lines"] == 0
            ):
                total_estimated = sum(
                    file_data.get("estimated_lines", 0)
                    for file_data in content.get("files", [])
                )
                content["total_estimated_lines"] = total_estimated

            manifest = FileManifest(**content)

            logger.info(
                f"Manifest generation successful: {manifest.total_files} files, "
                f"{manifest.total_estimated_lines} estimated LOC"
            )

            return manifest

        except Exception as e:
            logger.error(f"Failed to validate file manifest: {e}")
            logger.debug(
                f"Response content keys: {content.keys() if isinstance(content, dict) else 'not a dict'}"
            )
            # Debug: dump the full content for investigation
            import json

            logger.error(
                f"DEBUG: Full manifest content: {json.dumps(content, indent=2)}"
            )
            raise AgentExecutionError(f"Manifest validation failed: {e}") from e

    def _generate_file_content(
        self,
        file_meta: FileMetadata,
        input_data: CodeInput,
        max_retries: int = 3,
    ) -> str:
        """
        Generate content for a single file using LLM (Phase 2 of multi-stage generation).

        This is Phase 2 of the multi-stage code generation process. It generates
        the actual code content for a single file based on the file metadata and
        design specification.

        The LLM returns RAW CODE CONTENT (no JSON wrapping), which avoids the
        JSON escaping issues that occur with large code blocks.

        Args:
            file_meta: FileMetadata with file path, type, description, etc.
            input_data: CodeInput with design specification and standards
            max_retries: Maximum number of retry attempts if generation fails

        Returns:
            str: Raw file content (code, documentation, config, etc.)

        Raises:
            AgentExecutionError: If LLM call fails after retries or content is invalid
        """
        # Load file generation prompt template
        try:
            prompt_template = self.load_prompt("code_agent_v2_file_generation")
        except FileNotFoundError as e:
            raise AgentExecutionError(
                f"File generation prompt template not found: {e}"
            ) from e

        # Format prompt with file metadata and design specification
        # Escape curly braces in design specification JSON to avoid format() issues
        design_spec_json = input_data.design_specification.model_dump_json(indent=2)
        design_spec_escaped = design_spec_json.replace("{", "{{").replace("}", "}}")

        formatted_prompt = self.format_prompt(
            prompt_template,
            file_path=file_meta.file_path,
            file_type=file_meta.file_type,
            description=file_meta.description,
            semantic_unit_id=file_meta.semantic_unit_id or "None",
            component_id=file_meta.component_id or "None",
            estimated_lines=file_meta.estimated_lines,
            dependencies=(
                ", ".join(file_meta.dependencies) if file_meta.dependencies else "None"
            ),
            design_specification=design_spec_escaped,
            coding_standards=input_data.coding_standards
            or "Follow industry best practices",
        )

        logger.debug(
            f"Generating content for {file_meta.file_path} "
            f"({file_meta.estimated_lines} estimated lines)"
        )

        # Retry loop for robustness
        last_error = None
        for attempt in range(max_retries):
            try:
                # Call LLM to generate file content
                # Token limit based on estimated file size
                max_tokens = min(8000, max(2000, file_meta.estimated_lines * 2))

                response = self.call_llm(
                    prompt=formatted_prompt,
                    max_tokens=max_tokens,
                    temperature=0.0,  # Deterministic for code generation
                )

                # Extract content - use raw_content to avoid JSON parsing
                # The LLM client auto-parses JSON, but we want RAW code content
                content = response.get("raw_content") or response.get("content")

                if not isinstance(content, str):
                    raise AgentExecutionError(
                        f"LLM returned non-string content for {file_meta.file_path}: {type(content)}"
                    )

                # Strip any markdown fences if present (shouldn't be, but be defensive)
                # Remove ```python, ```markdown, ``` etc. from the beginning/end
                content = content.strip()
                if content.startswith("```"):
                    # Find the first newline after opening fence
                    first_newline = content.find("\n")
                    if first_newline > 0:
                        content = content[first_newline + 1 :]
                    # Remove closing fence
                    if content.endswith("```"):
                        content = content[:-3].rstrip()

                # Validate content is not empty
                if not content or len(content.strip()) < 10:
                    raise AgentExecutionError(
                        f"Generated content for {file_meta.file_path} is too short or empty: "
                        f"{len(content)} characters"
                    )

                logger.info(
                    f"File content generated: {file_meta.file_path} "
                    f"({len(content)} chars, {len(content.split(chr(10)))} lines)"
                )

                return content

            except Exception as e:
                last_error = e
                if attempt < max_retries - 1:
                    logger.warning(
                        f"File generation attempt {attempt + 1}/{max_retries} failed "
                        f"for {file_meta.file_path}: {e}. Retrying..."
                    )
                else:
                    logger.error(
                        f"File generation failed after {max_retries} attempts "
                        f"for {file_meta.file_path}: {e}"
                    )

        # If we get here, all retries failed
        raise AgentExecutionError(
            f"Failed to generate content for {file_meta.file_path} after {max_retries} attempts: "
            f"{last_error}"
        ) from last_error

    def _generate_code_multi_stage(self, input_data: CodeInput) -> GeneratedCode:
        """
        Generate complete code using multi-stage approach (Phase 1 + Phase 2).

        This is the new multi-stage approach that avoids JSON escaping issues:
        - Phase 1: Generate file manifest (small JSON, no code content)
        - Phase 2: Generate each file content separately (raw code, no JSON)

        Args:
            input_data: CodeInput with design specification and standards

        Returns:
            GeneratedCode assembled from manifest and individual file contents

        Raises:
            AgentExecutionError: If generation fails
        """
        logger.info(
            f"Starting multi-stage code generation for task_id={input_data.task_id}"
        )

        # Phase 1: Generate file manifest
        logger.info("Phase 1: Generating file manifest...")
        manifest = self._generate_file_manifest(input_data)

        logger.info(
            f"Manifest generated: {manifest.total_files} files, "
            f"{manifest.total_estimated_lines} estimated LOC"
        )

        # Phase 2: Generate content for each file
        logger.info(f"Phase 2: Generating content for {manifest.total_files} files...")
        generated_files = []

        for idx, file_meta in enumerate(manifest.files, 1):
            logger.info(
                f"Generating file {idx}/{manifest.total_files}: {file_meta.file_path}"
            )

            # Generate file content
            content = self._generate_file_content(file_meta, input_data)

            # Create GeneratedFile
            generated_file = GeneratedFile(
                file_path=file_meta.file_path,
                content=content,
                file_type=file_meta.file_type,
                semantic_unit_id=file_meta.semantic_unit_id,
                component_id=file_meta.component_id,
                description=file_meta.description,
            )
            generated_files.append(generated_file)

        # Build file_structure from generated files
        file_structure: dict[str, list[str]] = {}
        for file in generated_files:
            # Extract directory and filename
            path_parts = file.file_path.split("/")
            if len(path_parts) == 1:
                # Root level file
                directory = "."
                filename = path_parts[0]
            else:
                # File in subdirectory
                directory = "/".join(path_parts[:-1])
                filename = path_parts[-1]

            if directory not in file_structure:
                file_structure[directory] = []
            file_structure[directory].append(filename)

        # Calculate total lines of code
        total_loc = sum(
            len([line for line in file.content.split("\n") if line.strip()])
            for file in generated_files
        )

        # Extract semantic units and components implemented
        semantic_units = list(
            {file.semantic_unit_id for file in generated_files if file.semantic_unit_id}
        )
        components = list(
            {file.component_id for file in generated_files if file.component_id}
        )

        # Assemble GeneratedCode
        generated_code = GeneratedCode(
            task_id=input_data.task_id,
            project_id=manifest.project_id,
            files=generated_files,
            file_structure=file_structure,
            implementation_notes=(
                f"Generated using multi-stage approach with {manifest.total_files} files. "
                f"Manifest estimated {manifest.total_estimated_lines} LOC, "
                f"actual {total_loc} LOC. "
                f"Uses {len(manifest.dependencies)} external dependencies."
            ),
            dependencies=manifest.dependencies,
            setup_instructions=manifest.setup_instructions,
            total_lines_of_code=total_loc,
            total_files=len(generated_files),
            test_coverage_target=80.0,  # Default target
            semantic_units_implemented=semantic_units,
            components_implemented=components,
            agent_version=self.agent_version,
            generation_timestamp=datetime.now().isoformat(),
        )

        logger.info(
            f"Multi-stage code generation complete: {generated_code.total_files} files, "
            f"{generated_code.total_lines_of_code} LOC"
        )

        return generated_code
