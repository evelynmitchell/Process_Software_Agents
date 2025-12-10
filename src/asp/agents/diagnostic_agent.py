"""
Diagnostic Agent for ASP Repair Workflow.

The Diagnostic Agent is responsible for:
1. Analyzing test failures to identify root causes
2. Locating the exact source of bugs in the codebase
3. Suggesting precise fixes using search-replace patterns
4. Assessing confidence and severity of the diagnosis

This agent is part of the repair workflow (ADR 006) and feeds into the Repair Agent.

Author: ASP Development Team
Date: December 10, 2025
"""

# pylint: disable=logging-fstring-interpolation

from __future__ import annotations

import json
import logging
import re
from pathlib import Path
from typing import TYPE_CHECKING, Any

from asp.agents.base_agent import AgentExecutionError, BaseAgent
from asp.models.diagnostic import DiagnosticInput, DiagnosticReport
from asp.telemetry import track_agent_cost

if TYPE_CHECKING:
    from asp.models.execution import TestResult

logger = logging.getLogger(__name__)


class DiagnosticAgent(BaseAgent):
    """
    Diagnostic Agent implementation.

    Analyzes test failures and errors to identify root causes and suggest fixes.
    Uses search-replace patterns (not line numbers) for reliable code modification.

    The Diagnostic Agent:
    - Takes DiagnosticInput with test results and error information
    - Analyzes the error type, message, and stack trace
    - Gathers context from relevant source files
    - Identifies the root cause of the failure
    - Suggests precise fixes using search-replace patterns
    - Returns DiagnosticReport with diagnosis and fix suggestions

    Example:
        >>> from asp.agents.diagnostic_agent import DiagnosticAgent
        >>> from asp.models.diagnostic import DiagnosticInput
        >>>
        >>> agent = DiagnosticAgent()
        >>> input_data = DiagnosticInput(
        ...     task_id="REPAIR-001",
        ...     workspace_path="/path/to/workspace",
        ...     test_result=test_result,
        ...     error_type="AssertionError",
        ...     error_message="assert add(2, 3) == 5",
        ...     stack_trace="...",
        ... )
        >>> report = agent.execute(input_data)
        >>> print(f"Root cause: {report.root_cause}")
        >>> print(f"Best fix: {report.best_fix.description}")
    """

    def __init__(
        self,
        db_path: Path | None = None,
        llm_client: Any | None = None,
    ):
        """
        Initialize Diagnostic Agent.

        Args:
            db_path: Optional path to SQLite database for telemetry
            llm_client: Optional LLM client (for dependency injection in tests)
        """
        super().__init__(db_path=db_path, llm_client=llm_client)
        self.agent_version = "1.0.0"
        logger.info("DiagnosticAgent initialized")

    @track_agent_cost(
        agent_role="Diagnostic",
        task_id_param="input_data.task_id",
        llm_model="claude-sonnet-4-20250514",
        llm_provider="anthropic",
        agent_version="1.0.0",
    )
    def execute(self, input_data: DiagnosticInput) -> DiagnosticReport:
        """
        Execute the Diagnostic Agent to analyze test failures.

        This method:
        1. Gathers context from the workspace (source files, stack trace locations)
        2. Loads the diagnostic prompt template
        3. Formats it with error information and source context
        4. Calls the LLM to diagnose the issue
        5. Parses and validates the diagnostic report response
        6. Returns complete DiagnosticReport with fixes

        Args:
            input_data: DiagnosticInput with test results and error information

        Returns:
            DiagnosticReport with root cause analysis and suggested fixes

        Raises:
            AgentExecutionError: If diagnosis fails or output is invalid
            ValidationError: If response doesn't match DiagnosticReport schema
        """
        logger.info(
            f"Executing DiagnosticAgent for task_id={input_data.task_id}, "
            f"error_type={input_data.error_type}"
        )

        try:
            # Gather additional context from workspace
            source_context = self._gather_context(input_data)

            # Diagnose the issue
            diagnostic_report = self._diagnose_issue(input_data, source_context)

            # Validate the report
            self._validate_diagnostic_report(diagnostic_report)

            # Log summary
            logger.info(
                f"Diagnosis complete: issue_type={diagnostic_report.issue_type.value}, "
                f"severity={diagnostic_report.severity.value}, "
                f"confidence={diagnostic_report.confidence:.2f}, "
                f"fixes_suggested={len(diagnostic_report.suggested_fixes)}"
            )

            return diagnostic_report

        except Exception as e:
            logger.error(f"DiagnosticAgent execution failed: {e}")
            raise AgentExecutionError(f"Diagnostic failed: {e}") from e

    def _gather_context(self, input_data: DiagnosticInput) -> dict[str, str]:
        """
        Gather additional context from the workspace.

        Reads source files referenced in:
        - Stack trace
        - Test failures
        - Input source_files

        Args:
            input_data: DiagnosticInput with workspace path and error info

        Returns:
            Dict mapping file paths to their contents
        """
        context = dict(input_data.source_files)  # Start with provided files
        workspace_path = Path(input_data.workspace_path)

        if not workspace_path.exists():
            logger.warning(f"Workspace path does not exist: {workspace_path}")
            return context

        # Extract file paths from stack trace
        stack_files = self._extract_files_from_stack_trace(
            input_data.stack_trace, workspace_path
        )

        # Extract file paths from test failures
        failure_files = self._extract_files_from_failures(
            input_data.test_result, workspace_path
        )

        # Read all unique files
        all_files = set(stack_files) | set(failure_files)

        for file_path in all_files:
            if file_path in context:
                continue  # Already have this file

            full_path = workspace_path / file_path
            if full_path.exists() and full_path.is_file():
                try:
                    content = full_path.read_text()
                    context[file_path] = content
                    logger.debug(f"Read source file: {file_path}")
                except OSError as e:
                    logger.warning(f"Failed to read {file_path}: {e}")

        logger.info(f"Gathered context from {len(context)} source files")
        return context

    def _extract_files_from_stack_trace(
        self, stack_trace: str, workspace_path: Path
    ) -> list[str]:
        """
        Extract file paths from a stack trace.

        Args:
            stack_trace: Full stack trace text
            workspace_path: Base workspace path for making paths relative

        Returns:
            List of relative file paths found in the stack trace
        """
        files = []

        # Pattern: File "path/to/file.py", line 42
        # Or: path/to/file.py:42
        patterns = [
            r'File "([^"]+\.py)"',  # Python standard format
            r"(\S+\.py):\d+:",  # pytest format
            r"(\S+\.py):\d+",  # Simple format
        ]

        for pattern in patterns:
            for match in re.finditer(pattern, stack_trace):
                file_path = match.group(1)

                # Try to make path relative to workspace
                try:
                    full_path = Path(file_path)
                    if full_path.is_absolute():
                        if str(full_path).startswith(str(workspace_path)):
                            file_path = str(full_path.relative_to(workspace_path))
                        else:
                            continue  # Skip files outside workspace
                except (ValueError, OSError):
                    pass  # Keep as-is if relative conversion fails

                if file_path not in files:
                    files.append(file_path)

        return files

    def _extract_files_from_failures(
        self, test_result: TestResult, workspace_path: Path
    ) -> list[str]:
        """
        Extract file paths from test failures.

        Args:
            test_result: TestResult containing failure information
            workspace_path: Base workspace path

        Returns:
            List of relative file paths from test failures
        """
        files = []

        for failure in test_result.failures:
            if failure.test_file and failure.test_file not in files:
                files.append(failure.test_file)

            # Also extract from stack trace
            if failure.stack_trace:
                stack_files = self._extract_files_from_stack_trace(
                    failure.stack_trace, workspace_path
                )
                for f in stack_files:
                    if f not in files:
                        files.append(f)

        return files

    def _diagnose_issue(
        self, input_data: DiagnosticInput, source_context: dict[str, str]
    ) -> DiagnosticReport:
        """
        Diagnose the issue using LLM.

        Args:
            input_data: DiagnosticInput with error information
            source_context: Dict of file paths to contents

        Returns:
            DiagnosticReport parsed from LLM response

        Raises:
            AgentExecutionError: If LLM call fails or response is invalid
        """
        # Load prompt template
        try:
            prompt_template = self.load_prompt("diagnostic_agent_v1")
        except FileNotFoundError as e:
            raise AgentExecutionError(f"Prompt template not found: {e}") from e

        # Format source files for prompt
        source_files_text = self._format_source_files(source_context)

        # Format prompt
        formatted_prompt = self.format_prompt(
            prompt_template,
            task_id=input_data.task_id,
            test_result_json=input_data.test_result.model_dump_json(indent=2),
            error_type=input_data.error_type,
            error_message=input_data.error_message,
            stack_trace=input_data.stack_trace or "No stack trace available",
            source_files_json=source_files_text,
        )

        logger.debug(f"Generated diagnostic prompt ({len(formatted_prompt)} chars)")

        # Call LLM to diagnose
        response = self.call_llm(
            prompt=formatted_prompt,
            max_tokens=8000,
            temperature=0.0,  # Deterministic for diagnosis
        )

        # Parse response
        content = response.get("content")

        # Extract JSON from response
        content = self._extract_json_content(content)

        if not isinstance(content, dict):
            raise AgentExecutionError(
                f"LLM returned non-dict response after parsing: {type(content)}\n"
                f"Expected dict matching DiagnosticReport schema"
            )

        # Validate against DiagnosticReport schema
        try:
            report = self.validate_output(content, DiagnosticReport)
            logger.debug(
                f"Successfully validated DiagnosticReport for task {input_data.task_id}"
            )
            return report
        except Exception as e:
            raise AgentExecutionError(
                f"Failed to validate DiagnosticReport: {e}\n"
                f"Response content: {content}"
            ) from e

    def _format_source_files(self, source_context: dict[str, str]) -> str:
        """
        Format source files for inclusion in prompt.

        Args:
            source_context: Dict of file paths to contents

        Returns:
            Formatted string with file contents
        """
        if not source_context:
            return "No source files available"

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
                    f"Expected JSON matching DiagnosticReport schema"
                ) from e

        raise AgentExecutionError(
            f"Unexpected content type: {type(content)}\n"
            f"Expected dict or JSON string"
        )

    def _validate_diagnostic_report(self, report: DiagnosticReport) -> None:
        """
        Validate diagnostic report for consistency.

        Checks:
        - Has at least one affected file
        - Has at least one suggested fix
        - Fixes have valid search-replace pairs
        - Confidence is reasonable given the diagnosis

        Args:
            report: DiagnosticReport to validate

        Raises:
            AgentExecutionError: If validation fails
        """
        # Check affected files
        if not report.affected_files:
            raise AgentExecutionError(
                "Diagnostic report must have at least one affected file"
            )

        # Check suggested fixes
        if not report.suggested_fixes:
            raise AgentExecutionError(
                "Diagnostic report must have at least one suggested fix"
            )

        # Validate each fix
        for fix in report.suggested_fixes:
            if not fix.changes:
                raise AgentExecutionError(
                    f"Fix {fix.fix_id} must have at least one code change"
                )

            for change in fix.changes:
                if not change.search_text:
                    raise AgentExecutionError(f"Fix {fix.fix_id} has empty search_text")

                if change.search_text == change.replace_text:
                    raise AgentExecutionError(
                        f"Fix {fix.fix_id} has identical search and replace text"
                    )

        # Validate fix IDs are unique
        fix_ids = [f.fix_id for f in report.suggested_fixes]
        if len(fix_ids) != len(set(fix_ids)):
            duplicates = [fid for fid in fix_ids if fix_ids.count(fid) > 1]
            raise AgentExecutionError(f"Duplicate fix IDs found: {set(duplicates)}")

        logger.debug("Diagnostic report validation passed")
