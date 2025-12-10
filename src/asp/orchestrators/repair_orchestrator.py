"""
Repair Orchestrator for Iterative Bug Fixing.

Orchestrates the diagnose → fix → test → repeat loop for repairing
code issues. Coordinates DiagnosticAgent, RepairAgent, and TestExecutor
with confidence-based HITL escalation.

Part of ADR 006: Repair Workflow Architecture.

Author: ASP Development Team
Date: December 10, 2025
"""

# pylint: disable=logging-fstring-interpolation,too-many-statements

from __future__ import annotations

import asyncio
import logging
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any

from asp.agents.diagnostic_agent import DiagnosticAgent
from asp.agents.repair_agent import RepairAgent
from asp.models.diagnostic import CodeChange, DiagnosticInput, DiagnosticReport
from asp.models.execution import TestResult
from asp.models.repair import RepairAttempt, RepairInput, RepairOutput, RepairResult
from asp.orchestrators.confidence import calculate_confidence
from asp.orchestrators.hitl_config import DEFAULT_CONFIG, HITLConfig

if TYPE_CHECKING:
    from services.sandbox_executor import SubprocessSandboxExecutor
    from services.surgical_editor import EditResult, SurgicalEditor
    from services.test_executor import TestExecutor
    from services.workspace_manager import Workspace

logger = logging.getLogger(__name__)


# =============================================================================
# Request/Response Types
# =============================================================================


@dataclass
class RepairRequest:
    """
    Request to repair code issues in a workspace.

    Attributes:
        task_id: Unique identifier for this repair task
        workspace: Workspace containing the code to repair
        issue_description: Optional description of the issue to fix
        target_tests: Optional list of specific tests to target
        max_iterations: Maximum repair iterations before giving up
        test_command: Custom test command (default: pytest)
        hitl_config: Human-in-the-loop configuration
    """

    task_id: str
    workspace: Workspace
    issue_description: str | None = None
    target_tests: list[str] | None = None
    max_iterations: int = 5
    test_command: str | None = None
    hitl_config: HITLConfig = field(default_factory=lambda: DEFAULT_CONFIG)


# Type alias for approval callback
ApprovalCallback = Callable[[str, float, list[str], int], bool]
"""
Callback for HITL approval requests.

Args:
    reason: Why approval is being requested
    confidence: Current confidence score
    files_to_modify: List of files that will be modified
    iteration: Current iteration number

Returns:
    True if human approves, False to abort
"""


# =============================================================================
# Exceptions
# =============================================================================


class RepairError(Exception):
    """Base exception for repair errors."""


class MaxIterationsExceeded(RepairError):
    """Raised when max iterations reached without success."""


class HumanRejectedRepair(RepairError):
    """Raised when human rejects a repair during HITL."""


class DiagnosticFailed(RepairError):
    """Raised when diagnostic cannot identify the issue."""


# =============================================================================
# Repair Orchestrator
# =============================================================================


class RepairOrchestrator:
    """
    Orchestrates the repair workflow loop.

    Coordinates the diagnose → fix → test → repeat cycle with:
    - Automatic rollback on failed repairs
    - Confidence-based HITL escalation
    - Learning from previous failed attempts
    - Backup/restore for safe experimentation

    The repair loop:
    1. Run tests to identify failures
    2. If all pass → return success
    3. Run DiagnosticAgent to analyze failures
    4. Run RepairAgent to generate fix
    5. Check HITL requirements (confidence, iterations)
    6. Apply fix using SurgicalEditor
    7. Run tests again
    8. If pass → success; else rollback and loop

    Example:
        >>> orchestrator = RepairOrchestrator(
        ...     sandbox=sandbox,
        ...     test_executor=test_executor,
        ...     surgical_editor=surgical_editor,
        ... )
        >>> request = RepairRequest(
        ...     task_id="REPAIR-001",
        ...     workspace=workspace,
        ... )
        >>> result = await orchestrator.repair(request)
        >>> if result.success:
        ...     print(f"Fixed in {result.iterations_used} iterations")

    Attributes:
        sandbox: Subprocess executor for running commands
        test_executor: Test runner and result parser
        surgical_editor: Code editor with backup/rollback
        diagnostic_agent: Agent for analyzing test failures
        repair_agent: Agent for generating code fixes
    """

    def __init__(
        self,
        sandbox: SubprocessSandboxExecutor,
        test_executor: TestExecutor,
        surgical_editor: SurgicalEditor,
        diagnostic_agent: DiagnosticAgent | None = None,
        repair_agent: RepairAgent | None = None,
        db_path: Path | None = None,
        llm_client: Any | None = None,
    ):
        """
        Initialize RepairOrchestrator.

        Args:
            sandbox: Subprocess executor for running commands
            test_executor: Test runner and result parser
            surgical_editor: Code editor with backup/rollback
            diagnostic_agent: Optional DiagnosticAgent (created if not provided)
            repair_agent: Optional RepairAgent (created if not provided)
            db_path: Optional database path for telemetry
            llm_client: Optional LLM client for agents
        """
        self.sandbox = sandbox
        self.test_executor = test_executor
        self.surgical_editor = surgical_editor

        # Initialize agents (lazy or provided)
        self._diagnostic_agent = diagnostic_agent
        self._repair_agent = repair_agent
        self._db_path = db_path
        self._llm_client = llm_client

        logger.info("RepairOrchestrator initialized")

    # =========================================================================
    # Lazy-loaded agents
    # =========================================================================

    @property
    def diagnostic_agent(self) -> DiagnosticAgent:
        """Lazy-load DiagnosticAgent."""
        if self._diagnostic_agent is None:
            self._diagnostic_agent = DiagnosticAgent(
                db_path=self._db_path,
                llm_client=self._llm_client,
            )
        return self._diagnostic_agent

    @property
    def repair_agent(self) -> RepairAgent:
        """Lazy-load RepairAgent."""
        if self._repair_agent is None:
            self._repair_agent = RepairAgent(
                db_path=self._db_path,
                llm_client=self._llm_client,
            )
        return self._repair_agent

    # =========================================================================
    # Main Repair Loop
    # =========================================================================

    async def repair(
        self,
        request: RepairRequest,
        approval_callback: ApprovalCallback | None = None,
    ) -> RepairResult:
        """
        Execute the repair workflow.

        Runs the diagnose → fix → test → repeat loop until tests pass
        or max iterations is reached.

        Args:
            request: Repair request with workspace and configuration
            approval_callback: Optional callback for HITL approval

        Returns:
            RepairResult with success status and all changes made

        Raises:
            MaxIterationsExceeded: If max iterations reached without fix
            HumanRejectedRepair: If human rejects repair during HITL
            DiagnosticFailed: If diagnosis cannot identify issue
        """
        logger.info(
            f"Starting repair for task {request.task_id}, "
            f"max_iterations={request.max_iterations}"
        )

        # State tracking
        iteration = 0
        diagnostic_reports: list[DiagnosticReport] = []
        repair_attempts: list[RepairAttempt] = []
        all_changes: list[CodeChange] = []
        escalation_reason: str | None = None

        # Initial test run
        test_result = await self._run_tests(request)

        # Already passing?
        if test_result.success:
            logger.info("Tests already passing, no repair needed")
            return RepairResult(
                task_id=request.task_id,
                success=True,
                iterations_used=0,
                final_test_result=test_result,
                changes_made=[],
                diagnostic_reports=[],
                repair_attempts=[],
            )

        # Repair loop
        while iteration < request.max_iterations:
            iteration += 1
            logger.info(f"Starting repair iteration {iteration}")

            try:
                # Step 1: Diagnose
                diagnostic = await self._diagnose(request, test_result)
                diagnostic_reports.append(diagnostic)

                if not diagnostic.suggested_fixes:
                    logger.warning("Diagnostic provided no suggested fixes")
                    raise DiagnosticFailed(
                        f"Diagnostic could not suggest fixes: {diagnostic.root_cause}"
                    )

                # Step 2: Generate repair
                repair_output = await self._generate_repair(
                    request, diagnostic, repair_attempts
                )

                # Step 3: Calculate confidence
                confidence = calculate_confidence(
                    diagnostic=diagnostic,
                    repair_output=repair_output,
                    test_result=test_result,
                    previous_attempts=repair_attempts,
                    iteration=iteration,
                )
                logger.info(
                    f"Confidence: overall={confidence.overall:.2f}, "
                    f"diagnostic={confidence.diagnostic_confidence:.2f}, "
                    f"fix={confidence.fix_confidence:.2f}"
                )

                # Step 4: Check HITL requirements
                files_to_modify = [c.file_path for c in repair_output.changes]
                requires_approval, reason = request.hitl_config.should_require_approval(
                    iteration=iteration,
                    confidence=confidence.overall,
                    files_to_modify=files_to_modify,
                    change_count=repair_output.change_count,
                )

                if requires_approval:
                    logger.info(f"HITL approval required: {reason}")
                    if approval_callback:
                        approved = approval_callback(
                            reason,
                            confidence.overall,
                            files_to_modify,
                            iteration,
                        )
                        if not approved:
                            escalation_reason = f"Human rejected repair: {reason}"
                            raise HumanRejectedRepair(escalation_reason)
                    else:
                        # No callback = auto-reject when approval required
                        escalation_reason = f"HITL required but no approver: {reason}"
                        logger.warning(escalation_reason)
                        break

                # Step 5: Apply repair
                edit_result = self._apply_repair(repair_output)

                if not edit_result.success:
                    logger.warning(f"Failed to apply repair: {edit_result.errors}")
                    # Record failed attempt but don't rollback (nothing applied)
                    repair_attempts.append(
                        RepairAttempt(
                            attempt_number=iteration,
                            changes_made=repair_output.changes,
                            test_result=test_result,  # Keep old result
                            why_failed=f"Edit failed: {'; '.join(edit_result.errors)}",
                            rollback_performed=False,
                        )
                    )
                    continue

                # Step 6: Run tests again
                new_test_result = await self._run_tests(request)

                # Step 7: Check if fixed
                if new_test_result.success:
                    logger.info(f"Repair successful after {iteration} iterations!")
                    all_changes.extend(repair_output.changes)
                    repair_attempts.append(
                        RepairAttempt(
                            attempt_number=iteration,
                            changes_made=repair_output.changes,
                            test_result=new_test_result,
                            why_failed=None,
                            rollback_performed=False,
                        )
                    )

                    # Cleanup backups since fix worked
                    self.surgical_editor.cleanup_backups()

                    return RepairResult(
                        task_id=request.task_id,
                        success=True,
                        iterations_used=iteration,
                        final_test_result=new_test_result,
                        changes_made=all_changes,
                        diagnostic_reports=diagnostic_reports,
                        repair_attempts=repair_attempts,
                        escalated_to_human=False,
                    )

                # Fix didn't work - rollback and record attempt
                logger.info("Repair did not fix issue, rolling back")
                self.surgical_editor.rollback()

                repair_attempts.append(
                    RepairAttempt(
                        attempt_number=iteration,
                        changes_made=repair_output.changes,
                        test_result=new_test_result,
                        why_failed=self._analyze_why_failed(
                            test_result, new_test_result, repair_output
                        ),
                        rollback_performed=True,
                    )
                )

                # Update test_result for next iteration
                test_result = await self._run_tests(request)

            except DiagnosticFailed as e:
                logger.error(f"Diagnostic failed: {e}")
                escalation_reason = str(e)
                break
            # HumanRejectedRepair propagates automatically (no catch needed)

        # Max iterations reached or diagnostic failed
        logger.warning(
            f"Repair failed after {iteration} iterations: "
            f"{escalation_reason or 'max iterations reached'}"
        )

        return RepairResult(
            task_id=request.task_id,
            success=False,
            iterations_used=iteration,
            final_test_result=test_result,
            changes_made=all_changes,
            diagnostic_reports=diagnostic_reports,
            repair_attempts=repair_attempts,
            escalated_to_human=escalation_reason is not None,
            escalation_reason=escalation_reason or "Maximum iterations reached",
        )

    # =========================================================================
    # Helper Methods
    # =========================================================================

    async def _run_tests(self, request: RepairRequest) -> TestResult:
        """
        Run tests in the workspace.

        Args:
            request: Repair request with workspace info

        Returns:
            Parsed test results
        """
        workspace_path = request.workspace.target_repo_path

        # Build test command
        if request.test_command:
            test_cmd = request.test_command
        elif request.target_tests:
            tests = " ".join(request.target_tests)
            test_cmd = f"pytest {tests} -v"
        else:
            test_cmd = "pytest -v"

        logger.debug(f"Running tests: {test_cmd}")

        # Execute tests
        result = await asyncio.to_thread(
            self.test_executor.run_tests,
            command=test_cmd,
            working_dir=workspace_path,
        )

        logger.info(
            f"Test results: {result.passed}/{result.total_tests} passed, "
            f"{result.failed} failed"
        )

        return result

    async def _diagnose(
        self,
        request: RepairRequest,
        test_result: TestResult,
    ) -> DiagnosticReport:
        """
        Run diagnostic agent to analyze test failures.

        Args:
            request: Repair request with workspace info
            test_result: Failed test results to analyze

        Returns:
            Diagnostic report with root cause and fixes
        """
        # Extract error info from first failure
        error_type = "UnknownError"
        error_message = "Test failed"
        stack_trace = ""

        if test_result.failures:
            first_failure = test_result.failures[0]
            error_type = first_failure.error_type
            error_message = first_failure.error_message
            stack_trace = first_failure.stack_trace
        elif test_result.raw_output:
            error_message = "See raw output"
            stack_trace = test_result.raw_output

        # Create diagnostic input
        diagnostic_input = DiagnosticInput(
            task_id=request.task_id,
            workspace_path=str(request.workspace.target_repo_path),
            test_result=test_result,
            error_type=error_type,
            error_message=error_message,
            stack_trace=stack_trace,
        )

        # Add issue description if provided
        if request.issue_description:
            diagnostic_input = DiagnosticInput(
                task_id=diagnostic_input.task_id,
                workspace_path=diagnostic_input.workspace_path,
                test_result=diagnostic_input.test_result,
                error_type=diagnostic_input.error_type,
                error_message=f"{error_message}\n\nContext: {request.issue_description}",
                stack_trace=diagnostic_input.stack_trace,
            )

        # Run diagnostic agent
        logger.debug("Running diagnostic agent")
        report = await asyncio.to_thread(
            self.diagnostic_agent.execute,
            diagnostic_input,
        )

        logger.info(
            f"Diagnostic: {report.issue_type.value}, "
            f"confidence={report.confidence:.2f}, "
            f"fixes={len(report.suggested_fixes)}"
        )

        return report

    async def _generate_repair(
        self,
        request: RepairRequest,
        diagnostic: DiagnosticReport,
        previous_attempts: list[RepairAttempt],
    ) -> RepairOutput:
        """
        Run repair agent to generate code fix.

        Args:
            request: Repair request with workspace info
            diagnostic: Diagnostic report with analysis
            previous_attempts: History of failed attempts

        Returns:
            Repair output with changes to apply
        """
        repair_input = RepairInput(
            task_id=request.task_id,
            workspace_path=str(request.workspace.target_repo_path),
            diagnostic=diagnostic,
            previous_attempts=previous_attempts,
        )

        logger.debug("Running repair agent")
        output = await asyncio.to_thread(
            self.repair_agent.execute,
            repair_input,
        )

        logger.info(
            f"Repair: strategy='{output.strategy[:50]}...', "
            f"changes={output.change_count}, "
            f"confidence={output.confidence:.2f}"
        )

        return output

    def _apply_repair(self, repair_output: RepairOutput) -> EditResult:
        """
        Apply repair changes using surgical editor.

        Args:
            repair_output: Repair with changes to apply

        Returns:
            Edit result with success status
        """
        logger.debug(f"Applying {repair_output.change_count} changes")

        result = self.surgical_editor.apply_changes(
            changes=repair_output.changes,
            create_backup=True,
            use_fuzzy=True,
        )

        if result.success:
            logger.info(
                f"Applied {result.changes_applied} changes to "
                f"{len(result.files_modified)} files"
            )
        else:
            logger.warning(
                f"Failed to apply changes: {result.changes_failed} failed, "
                f"errors: {result.errors}"
            )

        return result

    def _analyze_why_failed(
        self,
        before: TestResult,
        after: TestResult,
        repair: RepairOutput,
    ) -> str:
        """
        Analyze why a repair attempt failed.

        Args:
            before: Test results before repair
            after: Test results after repair
            repair: The repair that was attempted

        Returns:
            Human-readable explanation of failure
        """
        reasons = []

        # Compare test counts
        if after.failed > before.failed:
            reasons.append(
                f"Made things worse: failures increased from "
                f"{before.failed} to {after.failed}"
            )
        elif after.failed == before.failed:
            reasons.append("No improvement: same number of failures")

        # Check for new failures
        before_names = {f.test_name for f in before.failures}
        after_names = {f.test_name for f in after.failures}
        new_failures = after_names - before_names
        if new_failures:
            reasons.append(f"Introduced new failures: {', '.join(new_failures)}")

        # Check if targeted tests still fail
        still_failing = before_names & after_names
        if still_failing:
            reasons.append(
                f"Originally failing tests still fail: {', '.join(still_failing)}"
            )

        if not reasons:
            reasons.append("Tests still failing after repair")

        return "; ".join(reasons)

    # =========================================================================
    # Utility Methods
    # =========================================================================

    def cleanup(self) -> None:
        """Clean up any remaining backups."""
        try:
            self.surgical_editor.cleanup_backups()
        except Exception as e:
            logger.warning(f"Error cleaning up backups: {e}")

    async def dry_run(
        self,
        request: RepairRequest,
    ) -> tuple[DiagnosticReport, RepairOutput, str]:
        """
        Perform a dry run without applying changes.

        Useful for previewing what changes would be made.

        Args:
            request: Repair request

        Returns:
            Tuple of (diagnostic, repair_output, diff_preview)
        """
        # Run tests
        test_result = await self._run_tests(request)

        if test_result.success:
            raise RepairError("Tests already passing, nothing to repair")

        # Diagnose
        diagnostic = await self._diagnose(request, test_result)

        # Generate repair
        repair_output = await self._generate_repair(request, diagnostic, [])

        # Generate diff preview
        diff = self.surgical_editor.generate_diff(repair_output.changes)

        return diagnostic, repair_output, diff
