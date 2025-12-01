"""
Test Agent for ASP Platform

The Test Agent is responsible for:
1. Build Validation (FR-006): Verifying code compiles/builds successfully
2. Test Generation: Creating comprehensive unit tests from design specification
3. Test Execution: Running tests and capturing results
4. Defect Logging: Classifying and logging all failures using AI Defect Taxonomy

This is the sixth agent in the 7-agent ASP architecture, following the Code Review Agent.

Author: ASP Development Team
Date: November 19, 2025
"""

import json
import logging
import re
from pathlib import Path
from typing import Any

from pydantic import BaseModel
from asp.agents.base_agent import AgentExecutionError, BaseAgent
from asp.models.test import TestInput, TestReport
from asp.telemetry import track_agent_cost
from asp.utils.artifact_io import write_artifact_json, write_artifact_markdown
from asp.utils.git_utils import git_commit_artifact, is_git_repository
from asp.utils.markdown_renderer import render_test_report_markdown

logger = logging.getLogger(__name__)


class TestAgent(BaseAgent):
    """
    Test Agent implementation.

    Validates generated code through build verification, test generation,
    test execution, and defect logging using AI Defect Taxonomy.

    The Test Agent:
    - Takes TestInput with generated code and design specification
    - Validates build/compilation success
    - Generates comprehensive unit tests from design
    - Executes tests and captures results
    - Logs all defects with proper classification
    - Returns TestReport with pass/fail status and defect list

    Example:
        >>> from asp.agents.test_agent import TestAgent
        >>> from asp.models.test import TestInput
        >>>
        >>> agent = TestAgent()
        >>> input_data = TestInput(
        ...     task_id="TEST-001",
        ...     generated_code=code,  # From Code Agent
        ...     design_specification=design_spec,  # From Design Agent
        ...     test_framework="pytest",
        ...     coverage_target=80.0,
        ... )
        >>> report = agent.execute(input_data)
        >>> print(f"Test Status: {report.test_status}")
        >>> print(f"Tests: {report.test_summary['passed']}/{report.test_summary['total_tests']}")
    """

    def __init__(
        self,
        db_path: Path | None = None,
        llm_client: Any | None = None,
    ):
        """
        Initialize Test Agent.

        Args:
            db_path: Optional path to SQLite database for telemetry
            llm_client: Optional LLM client (for dependency injection in tests)
        """
        super().__init__(db_path=db_path, llm_client=llm_client)
        self.agent_version = "1.0.0"
        logger.info("TestAgent initialized")

    @track_agent_cost(  # type: ignore
        agent_role="Test",
        task_id_param="input_data.task_id",
        llm_model="claude-sonnet-4-20250514",
        llm_provider="anthropic",
        agent_version="1.0.0",
    )
    def execute(self, input_data: TestInput) -> BaseModel:
        """
        Execute the Test Agent to validate code through testing.

        This method:
        1. Loads the test generation prompt template
        2. Formats it with generated code and design specification
        3. Calls the LLM to validate build, generate tests, execute them
        4. Parses and validates the test report response
        5. Validates test status consistency
        6. Returns complete TestReport

        Args:
            input_data: TestInput with generated code and design specification

        Returns:
            TestReport with build status, test results, and defect list

        Raises:
            AgentExecutionError: If test execution fails or output is invalid
            ValidationError: If response doesn't match TestReport schema
        """
        logger.info(
            f"Executing TestAgent for task_id={input_data.task_id}, "
            f"framework={input_data.test_framework}, "
            f"coverage_target={input_data.coverage_target}%"
        )

        try:
            # Generate tests and execute
            test_report = self._generate_and_execute_tests(input_data)

            # Validate test report consistency
            self._validate_test_report(test_report)

            # Log summary
            logger.info(
                f"Test execution complete: status={test_report.test_status}, "
                f"tests={test_report.test_summary.get('passed', 0)}/"
                f"{test_report.test_summary.get('total_tests', 0)}, "
                f"defects={len(test_report.defects_found)}, "
                f"coverage={test_report.coverage_percentage}%"
            )

            # Write artifacts to filesystem (if enabled)
            try:
                artifact_files = []

                # Write test report as JSON
                report_path = write_artifact_json(
                    task_id=test_report.task_id,
                    artifact_type="test_report",
                    data=test_report,
                )
                logger.debug(f"Wrote test report JSON: {report_path}")
                artifact_files.append(str(report_path))

                # Write test report as Markdown (human-readable)
                markdown_content = render_test_report_markdown(test_report)
                md_path = write_artifact_markdown(
                    task_id=test_report.task_id,
                    artifact_type="test_report",
                    markdown_content=markdown_content,
                )
                logger.debug(f"Wrote test report Markdown: {md_path}")
                artifact_files.append(str(md_path))

                # Commit to git (if in repository)
                if is_git_repository():
                    commit_hash = git_commit_artifact(
                        task_id=test_report.task_id,
                        agent_name="Test Agent",
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

            return test_report

        except Exception as e:
            logger.error(f"TestAgent execution failed: {e}")
            raise AgentExecutionError(f"Test execution failed: {e}") from e

    def _generate_and_execute_tests(self, input_data: TestInput) -> TestReport:
        """
        Generate and execute tests using LLM.

        Args:
            input_data: TestInput with generated code and design specification

        Returns:
            TestReport parsed from LLM response

        Raises:
            AgentExecutionError: If LLM call fails or response is invalid
        """
        # Load prompt template
        try:
            prompt_template = self.load_prompt("test_agent_v1_generation")
        except FileNotFoundError as e:
            raise AgentExecutionError(f"Prompt template not found: {e}") from e

        # Format prompt with generated code and design specification
        formatted_prompt = self.format_prompt(
            prompt_template,
            task_id=input_data.task_id,
            generated_code_json=input_data.generated_code.model_dump_json(indent=2),
            design_specification_json=input_data.design_specification.model_dump_json(
                indent=2
            ),
            test_framework=input_data.test_framework,
            coverage_target=input_data.coverage_target,
        )

        logger.debug(f"Generated test prompt ({len(formatted_prompt)} chars)")

        # Call LLM to generate and execute tests
        # Test generation and execution can produce large reports
        response = self.call_llm(
            prompt=formatted_prompt,
            max_tokens=16000,  # Large limit for comprehensive test reports
            temperature=0.0,  # Deterministic for testing
        )

        # Parse response
        content = response.get("content")

        # If content is a string, try to extract JSON from markdown fences
        if isinstance(content, str):
            # Try to extract JSON from markdown code blocks
            json_match = re.search(r"```json\s*\n(.*?)\n```", content, re.DOTALL)
            if json_match:
                try:
                    content = json.loads(json_match.group(1))
                    logger.debug("Successfully extracted JSON from markdown code fence")
                except json.JSONDecodeError as e:
                    raise AgentExecutionError(
                        f"Failed to parse JSON from markdown fence: {e}\n"
                        f"Content preview: {content[:500]}..."
                    ) from e
            else:
                # Try to parse the whole string as JSON
                try:
                    content = json.loads(content)
                    logger.debug("Successfully parsed string content as JSON")
                except json.JSONDecodeError as e:
                    raise AgentExecutionError(
                        f"LLM returned non-JSON response: {content[:500]}...\n"
                        f"Expected JSON matching TestReport schema"
                    ) from e

        if not isinstance(content, dict):
            raise AgentExecutionError(
                f"LLM returned non-dict response after parsing: {type(content)}\n"
                f"Expected dict matching TestReport schema"
            )

        # Fix: Auto-correct test_status if build failed
        # LLM sometimes returns test_status="FAIL" when build_successful=False
        # but schema requires test_status="BUILD_FAILED" in this case
        if not content.get("build_successful", True):
            if content.get("test_status") != "BUILD_FAILED":
                logger.debug(
                    f"Auto-correcting test_status from '{content.get('test_status')}' "
                    f"to 'BUILD_FAILED' because build_successful=False"
                )
                content["test_status"] = "BUILD_FAILED"

        # Validate against TestReport schema
        try:
            test_report = self.validate_output(content, TestReport)
            logger.debug(
                f"Successfully validated TestReport for task {input_data.task_id}"
            )
            return test_report
        except Exception as e:
            raise AgentExecutionError(
                f"Failed to validate TestReport: {e}\n" f"Response content: {content}"
            ) from e

    def _validate_test_report(self, report: TestReport) -> None:
        """
        Validate test report for consistency and correctness.

        Checks:
        - Test status matches build success and defect counts
        - Test summary values are consistent
        - Defect IDs are unique
        - Severity counts match defects_found

        Args:
            report: TestReport to validate

        Raises:
            AgentExecutionError: If validation fails
        """
        # Check test status consistency (already validated by Pydantic validators)
        # This is a double-check for extra safety

        if not report.build_successful and report.test_status != "BUILD_FAILED":
            raise AgentExecutionError(
                f"Invalid test status: build_successful=False but test_status={report.test_status} "
                f"(expected BUILD_FAILED)"
            )

        if (
            report.build_successful
            and len(report.defects_found) > 0
            and report.test_status == "PASS"
        ):
            raise AgentExecutionError(
                f"Invalid test status: defects found but test_status=PASS "
                f"({len(report.defects_found)} defects)"
            )

        # Validate test summary totals
        summary = report.test_summary
        total = summary.get("total_tests", 0)
        passed = summary.get("passed", 0)
        failed = summary.get("failed", 0)
        skipped = summary.get("skipped", 0)

        if total != passed + failed + skipped:
            raise AgentExecutionError(
                f"Test summary inconsistent: total={total} but passed+failed+skipped={passed + failed + skipped}"
            )

        # Validate defect IDs are unique
        defect_ids = [d.defect_id for d in report.defects_found]
        if len(defect_ids) != len(set(defect_ids)):
            duplicates = [did for did in defect_ids if defect_ids.count(did) > 1]
            raise AgentExecutionError(f"Duplicate defect IDs found: {set(duplicates)}")

        # Validate severity counts match actual defects
        actual_critical = sum(
            1 for d in report.defects_found if d.severity == "Critical"
        )
        actual_high = sum(1 for d in report.defects_found if d.severity == "High")
        actual_medium = sum(1 for d in report.defects_found if d.severity == "Medium")
        actual_low = sum(1 for d in report.defects_found if d.severity == "Low")

        if (
            actual_critical != report.critical_defects
            or actual_high != report.high_defects
            or actual_medium != report.medium_defects
            or actual_low != report.low_defects
        ):
            raise AgentExecutionError(
                f"Severity counts mismatch: "
                f"critical={report.critical_defects} (actual={actual_critical}), "
                f"high={report.high_defects} (actual={actual_high}), "
                f"medium={report.medium_defects} (actual={actual_medium}), "
                f"low={report.low_defects} (actual={actual_low})"
            )

        logger.debug("Test report validation passed")
