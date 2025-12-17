"""
Repair Agent for ASP Repair Workflow.

The Repair Agent is responsible for:
1. Analyzing diagnostic reports and suggested fixes
2. Learning from previous failed repair attempts
3. Generating precise code changes using search-replace
4. Providing confidence scores and alternative approaches

This agent is part of the repair workflow (ADR 006) and works with the
RepairOrchestrator to iteratively fix bugs.

Author: ASP Development Team
Date: December 10, 2025
"""

# pylint: disable=logging-fstring-interpolation

from __future__ import annotations

import json
import logging
import re
from pathlib import Path
from typing import Any

from asp.agents.base_agent import AgentExecutionError, BaseAgent
from asp.models.repair import RepairAttempt, RepairInput, RepairOutput
from asp.telemetry import track_agent_cost

logger = logging.getLogger(__name__)


class RepairAgent(BaseAgent):
    """
    Repair Agent implementation.

    Takes diagnostic reports and generates precise code fixes using
    search-replace patterns. Learns from previous failed attempts to
    avoid repeating mistakes.

    The Repair Agent:
    - Takes RepairInput with diagnostic and history
    - Analyzes the recommended fixes
    - Considers previous failed attempts
    - Generates minimal, precise code changes
    - Returns RepairOutput with changes and confidence

    Example:
        >>> from asp.agents.repair_agent import RepairAgent
        >>> from asp.models.repair import RepairInput
        >>>
        >>> agent = RepairAgent()
        >>> input_data = RepairInput(
        ...     task_id="REPAIR-001",
        ...     workspace_path="/path/to/workspace",
        ...     diagnostic=diagnostic_report,
        ...     previous_attempts=[],
        ... )
        >>> output = agent.execute(input_data)
        >>> print(f"Strategy: {output.strategy}")
        >>> print(f"Changes: {len(output.changes)}")
    """

    def __init__(
        self,
        db_path: Path | None = None,
        llm_client: Any | None = None,
    ):
        """
        Initialize Repair Agent.

        Args:
            db_path: Optional path to SQLite database for telemetry
            llm_client: Optional LLM client (for dependency injection in tests)
        """
        super().__init__(db_path=db_path, llm_client=llm_client)
        self.agent_version = "1.0.0"
        logger.info("RepairAgent initialized")

    @track_agent_cost(
        agent_role="Repair",
        task_id_param="input_data.task_id",
        llm_model="claude-sonnet-4-20250514",
        llm_provider="anthropic",
        agent_version="1.0.0",
    )
    def execute(self, input_data: RepairInput) -> RepairOutput:
        """
        Execute the Repair Agent to generate code fixes.

        This method:
        1. Reads affected files for context
        2. Loads the repair prompt template
        3. Formats it with diagnostic and history
        4. Calls the LLM to generate fixes
        5. Parses and validates the repair output
        6. Returns RepairOutput with changes

        Args:
            input_data: RepairInput with diagnostic and history

        Returns:
            RepairOutput with strategy, changes, and confidence

        Raises:
            AgentExecutionError: If repair generation fails
            ValidationError: If response doesn't match RepairOutput schema
        """
        logger.info(
            f"Executing RepairAgent for task_id={input_data.task_id}, "
            f"previous_attempts={input_data.attempt_count}"
        )

        try:
            # Read affected files for context
            source_context = self._read_affected_files(input_data)

            # Generate repair
            repair_output = self._generate_repair(input_data, source_context)

            # Validate the output
            self._validate_repair_output(repair_output)

            # Log summary
            logger.info(
                f"Repair generated: strategy='{repair_output.strategy[:50]}...', "
                f"changes={len(repair_output.changes)}, "
                f"confidence={repair_output.confidence:.2f}"
            )

            return repair_output

        except Exception as e:
            logger.error(f"RepairAgent execution failed: {e}")
            raise AgentExecutionError(f"Repair generation failed: {e}") from e

    def _read_affected_files(self, input_data: RepairInput) -> dict[str, str]:
        """
        Read contents of affected files.

        Args:
            input_data: RepairInput with diagnostic information

        Returns:
            Dict mapping file paths to their contents
        """
        context = dict(input_data.source_files)  # Start with provided files
        workspace_path = Path(input_data.workspace_path)

        if not workspace_path.exists():
            logger.warning(f"Workspace path does not exist: {workspace_path}")
            return context

        # Read files mentioned in diagnostic
        for affected in input_data.diagnostic.affected_files:
            if affected.path in context:
                continue

            full_path = workspace_path / affected.path
            if full_path.exists() and full_path.is_file():
                try:
                    content = full_path.read_text()
                    context[affected.path] = content
                    logger.debug(f"Read affected file: {affected.path}")
                except OSError as e:
                    logger.warning(f"Failed to read {affected.path}: {e}")

        # Also read files mentioned in suggested fixes
        for fix in input_data.diagnostic.suggested_fixes:
            for change in fix.changes:
                if change.file_path in context:
                    continue

                full_path = workspace_path / change.file_path
                if full_path.exists() and full_path.is_file():
                    try:
                        content = full_path.read_text()
                        context[change.file_path] = content
                        logger.debug(f"Read file from fix: {change.file_path}")
                    except OSError as e:
                        logger.warning(f"Failed to read {change.file_path}: {e}")

        logger.info(f"Read {len(context)} source files for context")
        return context

    def _generate_repair(
        self, input_data: RepairInput, source_context: dict[str, str]
    ) -> RepairOutput:
        """
        Generate repair using LLM.

        Args:
            input_data: RepairInput with diagnostic and history
            source_context: Dict of file paths to contents

        Returns:
            RepairOutput parsed from LLM response

        Raises:
            AgentExecutionError: If LLM call fails or response is invalid
        """
        # Load prompt template
        try:
            prompt_template = self.load_prompt("repair_agent_v1")
        except FileNotFoundError as e:
            raise AgentExecutionError(f"Prompt template not found: {e}") from e

        # Format previous attempts
        previous_attempts_json = self._format_previous_attempts(
            input_data.previous_attempts
        )

        # Format source files
        source_files_json = self._format_source_files(source_context)

        # Format prompt
        formatted_prompt = self.format_prompt(
            prompt_template,
            task_id=input_data.task_id,
            diagnostic_json=input_data.diagnostic.model_dump_json(indent=2),
            previous_attempts_json=previous_attempts_json,
            source_files_json=source_files_json,
        )

        logger.debug(f"Generated repair prompt ({len(formatted_prompt)} chars)")

        # Call LLM to generate repair
        response = self.call_llm(
            prompt=formatted_prompt,
            max_tokens=8000,
            temperature=0.0,  # Deterministic for repair
        )

        # Parse response
        content = response.get("content")

        # Extract JSON from response
        content = self._extract_json_content(content)

        if not isinstance(content, dict):
            raise AgentExecutionError(
                f"LLM returned non-dict response after parsing: {type(content)}\n"
                f"Expected dict matching RepairOutput schema"
            )

        # Validate against RepairOutput schema
        try:
            output = self.validate_output(content, RepairOutput)
            logger.debug(
                f"Successfully validated RepairOutput for task {input_data.task_id}"
            )
            return output
        except Exception as e:
            raise AgentExecutionError(
                f"Failed to validate RepairOutput: {e}\n" f"Response content: {content}"
            ) from e

    def _format_previous_attempts(self, attempts: list[RepairAttempt]) -> str:
        """
        Format previous repair attempts for the prompt.

        Args:
            attempts: List of previous repair attempts

        Returns:
            Formatted string describing previous attempts
        """
        if not attempts:
            return "No previous repair attempts."

        parts = []
        for attempt in attempts:
            status = "SUCCEEDED" if attempt.succeeded else "FAILED"
            parts.append(f"## Attempt {attempt.attempt_number}: {status}")

            # Changes made
            parts.append("### Changes Applied:")
            for change in attempt.changes_made:
                parts.append(
                    f"- {change.file_path}: {change.description or 'No description'}"
                )

            # Test results
            parts.append("### Test Results:")
            parts.append(f"- Passed: {attempt.test_result.passed}")
            parts.append(f"- Failed: {attempt.test_result.failed}")

            # Why it failed
            if attempt.why_failed:
                parts.append("### Why It Failed:")
                parts.append(attempt.why_failed)

            parts.append("")  # Blank line between attempts

        return "\n".join(parts)

    def _format_source_files(self, source_context: dict[str, str]) -> str:
        """
        Format source files for inclusion in prompt.

        Args:
            source_context: Dict of file paths to contents

        Returns:
            Formatted string with file contents
        """
        if not source_context:
            return "No source files available."

        parts = []
        for file_path, content in source_context.items():
            # Truncate very large files
            if len(content) > 10000:
                content = content[:10000] + "\n... (truncated)"

            parts.append(f"### {file_path}\n```\n{content}\n```")

        return "\n\n".join(parts)

    def _extract_json_content(self, content: Any) -> dict:
        """
        Extract JSON content from LLM response.

        Handles:
        - Direct dict response
        - JSON string
        - Markdown code fenced JSON

        Args:
            content: Raw content from LLM response

        Returns:
            Parsed dict

        Raises:
            AgentExecutionError: If JSON extraction fails
        """
        if isinstance(content, dict):
            return content

        if isinstance(content, str):
            # Try to extract from markdown code fence
            json_match = re.search(r"```(?:json)?\s*\n(.*?)\n```", content, re.DOTALL)
            if json_match:
                try:
                    return json.loads(json_match.group(1))
                except json.JSONDecodeError as e:
                    raise AgentExecutionError(
                        f"Failed to parse JSON from markdown fence: {e}\n"
                        f"Content preview: {content[:500]}..."
                    ) from e

            # Try to parse whole string as JSON
            try:
                return json.loads(content)
            except json.JSONDecodeError as e:
                raise AgentExecutionError(
                    f"LLM returned non-JSON response: {content[:500]}...\n"
                    f"Expected JSON matching RepairOutput schema"
                ) from e

        raise AgentExecutionError(
            f"Unexpected content type: {type(content)}\n"
            f"Expected dict or JSON string"
        )

    def _validate_repair_output(self, output: RepairOutput) -> None:
        """
        Validate repair output for consistency.

        Checks:
        - Has at least one change
        - Changes have valid search-replace pairs
        - Confidence is reasonable

        Args:
            output: RepairOutput to validate

        Raises:
            AgentExecutionError: If validation fails
        """
        # Check changes
        if not output.changes:
            raise AgentExecutionError(
                "Repair output must have at least one code change"
            )

        # Validate each change
        for i, change in enumerate(output.changes):
            if not change.search_text:
                raise AgentExecutionError(f"Change {i+1} has empty search_text")

            if change.search_text == change.replace_text:
                raise AgentExecutionError(
                    f"Change {i+1} has identical search and replace text"
                )

        # Warn on low confidence
        if output.confidence < 0.5:
            logger.warning(
                f"Repair has low confidence ({output.confidence:.2f}), "
                f"may require human review"
            )

        logger.debug("Repair output validation passed")

    # =========================================================================
    # Async Methods (ADR 008 Phase 2)
    # =========================================================================

    async def execute_async(self, input_data: RepairInput) -> RepairOutput:
        """
        Asynchronous version of execute for parallel agent execution.

        Native async implementation that uses call_llm_async() instead of
        call_llm(). Use this method when running multiple agents concurrently.

        Args:
            input_data: RepairInput with diagnostic and history

        Returns:
            RepairOutput with strategy, changes, and confidence

        Raises:
            AgentExecutionError: If repair generation fails
        """
        logger.info(
            f"Executing RepairAgent (async) for task_id={input_data.task_id}, "
            f"previous_attempts={input_data.attempt_count}"
        )

        try:
            # Read affected files for context (sync - fast I/O)
            source_context = self._read_affected_files(input_data)

            # Generate repair (async LLM call)
            repair_output = await self._generate_repair_async(input_data, source_context)

            # Validate the output (sync - fast validation)
            self._validate_repair_output(repair_output)

            # Log summary
            logger.info(
                f"Repair generated (async): strategy='{repair_output.strategy[:50]}...', "
                f"changes={len(repair_output.changes)}, "
                f"confidence={repair_output.confidence:.2f}"
            )

            return repair_output

        except Exception as e:
            logger.error(f"RepairAgent async execution failed: {e}")
            raise AgentExecutionError(f"Repair generation failed: {e}") from e

    async def _generate_repair_async(
        self, input_data: RepairInput, source_context: dict[str, str]
    ) -> RepairOutput:
        """
        Async version of _generate_repair using async LLM call.

        Args:
            input_data: RepairInput with diagnostic and history
            source_context: Dict of file paths to contents

        Returns:
            RepairOutput parsed from LLM response

        Raises:
            AgentExecutionError: If LLM call fails or response is invalid
        """
        # Load prompt template
        try:
            prompt_template = self.load_prompt("repair_agent_v1")
        except FileNotFoundError as e:
            raise AgentExecutionError(f"Prompt template not found: {e}") from e

        # Format previous attempts
        previous_attempts_json = self._format_previous_attempts(
            input_data.previous_attempts
        )

        # Format source files
        source_files_json = self._format_source_files(source_context)

        # Format prompt
        formatted_prompt = self.format_prompt(
            prompt_template,
            task_id=input_data.task_id,
            diagnostic_json=input_data.diagnostic.model_dump_json(indent=2),
            previous_attempts_json=previous_attempts_json,
            source_files_json=source_files_json,
        )

        logger.debug(f"Generated repair prompt ({len(formatted_prompt)} chars)")

        # Call LLM to generate repair (async)
        response = await self.call_llm_async(
            prompt=formatted_prompt,
            max_tokens=8000,
            temperature=0.0,  # Deterministic for repair
        )

        # Parse response
        content = response.get("content")

        # Extract JSON from response
        content = self._extract_json_content(content)

        if not isinstance(content, dict):
            raise AgentExecutionError(
                f"LLM returned non-dict response after parsing: {type(content)}\n"
                f"Expected dict matching RepairOutput schema"
            )

        # Validate against RepairOutput schema
        try:
            output = self.validate_output(content, RepairOutput)
            logger.debug(
                f"Successfully validated RepairOutput for task {input_data.task_id}"
            )
            return output
        except Exception as e:
            raise AgentExecutionError(
                f"Failed to validate RepairOutput: {e}\n" f"Response content: {content}"
            ) from e
