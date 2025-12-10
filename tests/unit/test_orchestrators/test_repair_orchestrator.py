"""
Unit tests for RepairOrchestrator.

Tests the repair workflow orchestration loop.
"""

# pylint: disable=too-many-public-methods,use-implicit-booleaness-not-comparison

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, Mock

import pytest

from asp.models.diagnostic import (
    AffectedFile,
    CodeChange,
    DiagnosticReport,
    IssueType,
    Severity,
    SuggestedFix,
)
from asp.models.execution import TestFailure, TestResult
from asp.models.repair import RepairOutput
from asp.orchestrators.hitl_config import AUTONOMOUS_CONFIG, HITLConfig
from asp.orchestrators.repair_orchestrator import (
    HumanRejectedRepair,
    RepairOrchestrator,
    RepairRequest,
)

# =============================================================================
# Test Fixtures
# =============================================================================


@dataclass
class MockWorkspace:
    """Mock workspace for testing."""

    task_id: str = "TEST-001"
    path: Path = Path("/tmp/test-workspace")
    target_repo_path: Path = Path("/tmp/test-workspace/repo")
    asp_path: Path = Path("/tmp/test-workspace/.asp")
    created_at: datetime = datetime.now()


@pytest.fixture
def mock_workspace():
    """Create a mock workspace."""
    return MockWorkspace()


@pytest.fixture
def mock_sandbox():
    """Create a mock sandbox executor."""
    return MagicMock()


@pytest.fixture
def mock_test_executor():
    """Create a mock test executor."""
    executor = MagicMock()
    executor.run_tests = MagicMock()
    return executor


@pytest.fixture
def mock_surgical_editor():
    """Create a mock surgical editor."""
    editor = MagicMock()
    editor.apply_changes = MagicMock()
    editor.rollback = MagicMock()
    editor.cleanup_backups = MagicMock()
    editor.generate_diff = MagicMock(return_value="--- a/file.py\n+++ b/file.py")
    return editor


@pytest.fixture
def mock_diagnostic_agent():
    """Create a mock diagnostic agent."""
    agent = MagicMock()
    agent.execute = MagicMock()
    return agent


@pytest.fixture
def mock_repair_agent():
    """Create a mock repair agent."""
    agent = MagicMock()
    agent.execute = MagicMock()
    return agent


@pytest.fixture
def orchestrator(
    mock_sandbox,
    mock_test_executor,
    mock_surgical_editor,
    mock_diagnostic_agent,
    mock_repair_agent,
):
    """Create a RepairOrchestrator with mocked dependencies."""
    return RepairOrchestrator(
        sandbox=mock_sandbox,
        test_executor=mock_test_executor,
        surgical_editor=mock_surgical_editor,
        diagnostic_agent=mock_diagnostic_agent,
        repair_agent=mock_repair_agent,
    )


@pytest.fixture
def passing_test_result():
    """Create a passing test result."""
    return TestResult(
        framework="pytest",
        total_tests=10,
        passed=10,
        failed=0,
        duration_seconds=1.0,
    )


@pytest.fixture
def failing_test_result():
    """Create a failing test result."""
    return TestResult(
        framework="pytest",
        total_tests=10,
        passed=8,
        failed=2,
        duration_seconds=1.0,
        failures=[
            TestFailure(
                test_name="test_add",
                test_file="tests/test_calculator.py",
                line_number=15,
                error_type="AssertionError",
                error_message="assert add(2, 3) == 5\nassert -1 == 5",
                stack_trace="...",
            )
        ],
    )


@pytest.fixture
def diagnostic_report():
    """Create a diagnostic report."""
    return DiagnosticReport(
        task_id="TEST-001",
        issue_type=IssueType.LOGIC_ERROR,
        severity=Severity.HIGH,
        root_cause="The add function uses subtraction instead of addition",
        affected_files=[
            AffectedFile(
                path="src/calculator.py",
                line_start=5,
                line_end=7,
                code_snippet="return a - b",
                issue_description="Wrong operator",
            )
        ],
        suggested_fixes=[
            SuggestedFix(
                fix_id="FIX-001",
                description="Change subtraction to addition",
                confidence=0.95,
                changes=[
                    CodeChange(
                        file_path="src/calculator.py",
                        search_text="return a - b",
                        replace_text="return a + b",
                    )
                ],
            )
        ],
        confidence=0.9,
    )


@pytest.fixture
def repair_output():
    """Create a repair output."""
    return RepairOutput(
        task_id="TEST-001",
        strategy="Apply the recommended fix from diagnostic",
        changes=[
            CodeChange(
                file_path="src/calculator.py",
                search_text="return a - b",
                replace_text="return a + b",
            )
        ],
        explanation="Changing subtraction to addition fixes the add function",
        confidence=0.9,
    )


@pytest.fixture
def successful_edit_result():
    """Create a successful edit result."""
    result = MagicMock()
    result.success = True
    result.changes_applied = 1
    result.changes_failed = 0
    result.files_modified = ["src/calculator.py"]
    result.errors = []
    return result


@pytest.fixture
def failed_edit_result():
    """Create a failed edit result."""
    result = MagicMock()
    result.success = False
    result.changes_applied = 0
    result.changes_failed = 1
    result.files_modified = []
    result.errors = ["Search text not found"]
    return result


# =============================================================================
# Test Classes
# =============================================================================


class TestRepairRequest:
    """Tests for RepairRequest dataclass."""

    def test_create_minimal_request(self, mock_workspace):
        """Test creating a minimal request."""
        request = RepairRequest(
            task_id="TEST-001",
            workspace=mock_workspace,
        )
        assert request.task_id == "TEST-001"
        assert request.max_iterations == 5
        assert request.test_command is None

    def test_create_full_request(self, mock_workspace):
        """Test creating a fully specified request."""
        request = RepairRequest(
            task_id="TEST-001",
            workspace=mock_workspace,
            issue_description="Tests failing in calculator",
            target_tests=["tests/test_calculator.py"],
            max_iterations=3,
            test_command="pytest -v",
            hitl_config=AUTONOMOUS_CONFIG,
        )
        assert request.issue_description == "Tests failing in calculator"
        assert request.max_iterations == 3
        assert request.hitl_config.mode == "autonomous"


class TestRepairOrchestratorInit:
    """Tests for RepairOrchestrator initialization."""

    def test_init_with_all_dependencies(
        self,
        mock_sandbox,
        mock_test_executor,
        mock_surgical_editor,
        mock_diagnostic_agent,
        mock_repair_agent,
    ):
        """Test initialization with all dependencies."""
        orchestrator = RepairOrchestrator(
            sandbox=mock_sandbox,
            test_executor=mock_test_executor,
            surgical_editor=mock_surgical_editor,
            diagnostic_agent=mock_diagnostic_agent,
            repair_agent=mock_repair_agent,
        )
        assert orchestrator.sandbox == mock_sandbox
        assert orchestrator.test_executor == mock_test_executor
        assert orchestrator.diagnostic_agent == mock_diagnostic_agent
        assert orchestrator.repair_agent == mock_repair_agent

    def test_lazy_agent_creation(
        self,
        mock_sandbox,
        mock_test_executor,
        mock_surgical_editor,
    ):
        """Test agents are created lazily when not provided."""
        orchestrator = RepairOrchestrator(
            sandbox=mock_sandbox,
            test_executor=mock_test_executor,
            surgical_editor=mock_surgical_editor,
            # Don't provide agents
        )
        assert orchestrator._diagnostic_agent is None
        assert orchestrator._repair_agent is None


class TestRepairAlreadyPassing:
    """Tests for when tests already pass."""

    @pytest.mark.asyncio
    async def test_returns_success_immediately(
        self,
        orchestrator,
        mock_workspace,
        mock_test_executor,
        passing_test_result,
    ):
        """Test returns success when tests already pass."""
        mock_test_executor.run_tests.return_value = passing_test_result

        request = RepairRequest(
            task_id="TEST-001",
            workspace=mock_workspace,
            hitl_config=AUTONOMOUS_CONFIG,
        )

        result = await orchestrator.repair(request)

        assert result.success is True
        assert result.iterations_used == 0
        assert result.changes_made == []
        assert result.diagnostic_reports == []


class TestSuccessfulRepair:
    """Tests for successful repair scenarios."""

    @pytest.mark.asyncio
    async def test_repair_fixes_on_first_try(
        self,
        orchestrator,
        mock_workspace,
        mock_test_executor,
        mock_diagnostic_agent,
        mock_repair_agent,
        mock_surgical_editor,
        failing_test_result,
        passing_test_result,
        diagnostic_report,
        repair_output,
        successful_edit_result,
    ):
        """Test successful repair on first iteration."""
        # First call fails, second call (after fix) passes
        mock_test_executor.run_tests.side_effect = [
            failing_test_result,
            passing_test_result,
        ]
        mock_diagnostic_agent.execute.return_value = diagnostic_report
        mock_repair_agent.execute.return_value = repair_output
        mock_surgical_editor.apply_changes.return_value = successful_edit_result

        request = RepairRequest(
            task_id="TEST-001",
            workspace=mock_workspace,
            hitl_config=AUTONOMOUS_CONFIG,
        )

        result = await orchestrator.repair(request)

        assert result.success is True
        assert result.iterations_used == 1
        assert len(result.changes_made) == 1
        assert len(result.diagnostic_reports) == 1
        assert len(result.repair_attempts) == 1
        assert result.repair_attempts[0].succeeded is True
        mock_surgical_editor.cleanup_backups.assert_called_once()


class TestFailedRepair:
    """Tests for failed repair scenarios."""

    @pytest.mark.asyncio
    async def test_max_iterations_reached(
        self,
        orchestrator,
        mock_workspace,
        mock_test_executor,
        mock_diagnostic_agent,
        mock_repair_agent,
        mock_surgical_editor,
        failing_test_result,
        diagnostic_report,
        repair_output,
        successful_edit_result,
    ):
        """Test failure when max iterations reached."""
        # Tests always fail
        mock_test_executor.run_tests.return_value = failing_test_result
        mock_diagnostic_agent.execute.return_value = diagnostic_report
        mock_repair_agent.execute.return_value = repair_output
        mock_surgical_editor.apply_changes.return_value = successful_edit_result

        request = RepairRequest(
            task_id="TEST-001",
            workspace=mock_workspace,
            max_iterations=2,
            hitl_config=AUTONOMOUS_CONFIG,
        )

        result = await orchestrator.repair(request)

        assert result.success is False
        assert result.iterations_used == 2
        assert result.escalation_reason == "Maximum iterations reached"

    @pytest.mark.asyncio
    async def test_edit_failure_continues(
        self,
        orchestrator,
        mock_workspace,
        mock_test_executor,
        mock_diagnostic_agent,
        mock_repair_agent,
        mock_surgical_editor,
        failing_test_result,
        diagnostic_report,
        repair_output,
        failed_edit_result,
    ):
        """Test continues after edit failure."""
        mock_test_executor.run_tests.return_value = failing_test_result
        mock_diagnostic_agent.execute.return_value = diagnostic_report
        mock_repair_agent.execute.return_value = repair_output
        mock_surgical_editor.apply_changes.return_value = failed_edit_result

        request = RepairRequest(
            task_id="TEST-001",
            workspace=mock_workspace,
            max_iterations=2,
            hitl_config=AUTONOMOUS_CONFIG,
        )

        result = await orchestrator.repair(request)

        assert result.success is False
        assert result.iterations_used == 2
        # All attempts failed at edit stage
        for attempt in result.repair_attempts:
            assert "Edit failed" in attempt.why_failed


class TestDiagnosticFailure:
    """Tests for diagnostic failure scenarios."""

    @pytest.mark.asyncio
    async def test_diagnostic_agent_exception(
        self,
        orchestrator,
        mock_workspace,
        mock_test_executor,
        mock_diagnostic_agent,
        failing_test_result,
    ):
        """Test failure when diagnostic agent raises an exception."""
        mock_test_executor.run_tests.return_value = failing_test_result

        # Mock diagnostic agent to raise an exception
        mock_diagnostic_agent.execute.side_effect = Exception(
            "Cannot determine root cause"
        )

        request = RepairRequest(
            task_id="TEST-001",
            workspace=mock_workspace,
            hitl_config=AUTONOMOUS_CONFIG,
        )

        # The repair should fail gracefully
        with pytest.raises(Exception, match="Cannot determine root cause"):
            await orchestrator.repair(request)

    @pytest.mark.asyncio
    async def test_low_confidence_diagnostic_escalates(
        self,
        orchestrator,
        mock_workspace,
        mock_test_executor,
        mock_diagnostic_agent,
        mock_repair_agent,
        mock_surgical_editor,
        failing_test_result,
        repair_output,
        successful_edit_result,
    ):
        """Test that low confidence diagnostic leads to HITL escalation."""
        mock_test_executor.run_tests.return_value = failing_test_result

        # Diagnostic with low confidence
        low_confidence_diagnostic = DiagnosticReport(
            task_id="TEST-001",
            issue_type=IssueType.LOGIC_ERROR,
            severity=Severity.MEDIUM,
            root_cause="Uncertain about the root cause but something seems wrong",
            affected_files=[
                AffectedFile(
                    path="src/unknown.py",
                    line_start=1,
                    line_end=10,
                    code_snippet="some code here",
                    issue_description="Potentially problematic code section",
                )
            ],
            suggested_fixes=[
                SuggestedFix(
                    fix_id="FIX-001",
                    description="Uncertain fix attempt that might help",
                    confidence=0.2,  # Very low confidence
                    changes=[
                        CodeChange(
                            file_path="src/unknown.py",
                            search_text="some code",
                            replace_text="other code",
                        )
                    ],
                )
            ],
            confidence=0.2,  # Very low confidence
        )
        mock_diagnostic_agent.execute.return_value = low_confidence_diagnostic
        mock_repair_agent.execute.return_value = repair_output
        mock_surgical_editor.apply_changes.return_value = successful_edit_result

        # Use a config that requires approval for low confidence
        config = HITLConfig(
            mode="threshold",
            require_approval_for_confidence_below=0.6,  # Will trigger
        )

        request = RepairRequest(
            task_id="TEST-001",
            workspace=mock_workspace,
            hitl_config=config,
        )

        # Without approval callback, should fail
        result = await orchestrator.repair(request, approval_callback=None)

        assert result.success is False
        assert "no approver" in result.escalation_reason


class TestHITLIntegration:
    """Tests for HITL approval integration."""

    @pytest.mark.asyncio
    async def test_hitl_approval_callback_called(
        self,
        orchestrator,
        mock_workspace,
        mock_test_executor,
        mock_diagnostic_agent,
        mock_repair_agent,
        mock_surgical_editor,
        failing_test_result,
        passing_test_result,
        diagnostic_report,
        repair_output,
        successful_edit_result,
    ):
        """Test HITL approval callback is called when needed."""
        mock_test_executor.run_tests.side_effect = [
            failing_test_result,
            passing_test_result,
        ]
        mock_diagnostic_agent.execute.return_value = diagnostic_report
        mock_repair_agent.execute.return_value = repair_output
        mock_surgical_editor.apply_changes.return_value = successful_edit_result

        # Use threshold config that will require approval
        config = HITLConfig(
            mode="threshold",
            require_approval_for_confidence_below=0.95,  # Will trigger
        )

        request = RepairRequest(
            task_id="TEST-001",
            workspace=mock_workspace,
            hitl_config=config,
        )

        approval_callback = Mock(return_value=True)

        result = await orchestrator.repair(request, approval_callback=approval_callback)

        assert result.success is True
        approval_callback.assert_called_once()

    @pytest.mark.asyncio
    async def test_hitl_rejection_stops_repair(
        self,
        orchestrator,
        mock_workspace,
        mock_test_executor,
        mock_diagnostic_agent,
        mock_repair_agent,
        failing_test_result,
        diagnostic_report,
        repair_output,
    ):
        """Test HITL rejection stops the repair."""
        mock_test_executor.run_tests.return_value = failing_test_result
        mock_diagnostic_agent.execute.return_value = diagnostic_report
        mock_repair_agent.execute.return_value = repair_output

        # Config that requires approval
        config = HITLConfig(
            mode="supervised",
        )

        request = RepairRequest(
            task_id="TEST-001",
            workspace=mock_workspace,
            hitl_config=config,
        )

        # Human rejects
        approval_callback = Mock(return_value=False)

        with pytest.raises(HumanRejectedRepair):
            await orchestrator.repair(request, approval_callback=approval_callback)

    @pytest.mark.asyncio
    async def test_no_callback_with_required_approval_stops(
        self,
        orchestrator,
        mock_workspace,
        mock_test_executor,
        mock_diagnostic_agent,
        mock_repair_agent,
        failing_test_result,
        diagnostic_report,
        repair_output,
    ):
        """Test missing callback when approval required stops repair."""
        mock_test_executor.run_tests.return_value = failing_test_result
        mock_diagnostic_agent.execute.return_value = diagnostic_report
        mock_repair_agent.execute.return_value = repair_output

        # Config that requires approval
        config = HITLConfig(mode="supervised")

        request = RepairRequest(
            task_id="TEST-001",
            workspace=mock_workspace,
            hitl_config=config,
        )

        # No callback provided
        result = await orchestrator.repair(request, approval_callback=None)

        assert result.success is False
        assert "no approver" in result.escalation_reason


class TestRollback:
    """Tests for rollback behavior."""

    @pytest.mark.asyncio
    async def test_rollback_on_failed_repair(
        self,
        orchestrator,
        mock_workspace,
        mock_test_executor,
        mock_diagnostic_agent,
        mock_repair_agent,
        mock_surgical_editor,
        failing_test_result,
        diagnostic_report,
        repair_output,
        successful_edit_result,
    ):
        """Test rollback is called when repair doesn't fix the issue."""
        # Tests always fail
        mock_test_executor.run_tests.return_value = failing_test_result
        mock_diagnostic_agent.execute.return_value = diagnostic_report
        mock_repair_agent.execute.return_value = repair_output
        mock_surgical_editor.apply_changes.return_value = successful_edit_result

        request = RepairRequest(
            task_id="TEST-001",
            workspace=mock_workspace,
            max_iterations=1,
            hitl_config=AUTONOMOUS_CONFIG,
        )

        result = await orchestrator.repair(request)

        assert result.success is False
        mock_surgical_editor.rollback.assert_called()


class TestAnalyzeWhyFailed:
    """Tests for _analyze_why_failed method."""

    def test_worse_failures(
        self,
        orchestrator,
        repair_output,
    ):
        """Test detecting when repair made things worse."""
        before = TestResult(
            framework="pytest",
            total_tests=10,
            passed=8,
            failed=2,
            duration_seconds=1.0,
            failures=[
                TestFailure(
                    test_name="test_add",
                    test_file="tests/test.py",
                    error_type="AssertionError",
                    error_message="failed",
                    stack_trace="...",
                )
            ],
        )
        after = TestResult(
            framework="pytest",
            total_tests=10,
            passed=6,
            failed=4,
            duration_seconds=1.0,
            failures=[
                TestFailure(
                    test_name="test_add",
                    test_file="tests/test.py",
                    error_type="AssertionError",
                    error_message="failed",
                    stack_trace="...",
                ),
                TestFailure(
                    test_name="test_subtract",
                    test_file="tests/test.py",
                    error_type="AssertionError",
                    error_message="new failure",
                    stack_trace="...",
                ),
            ],
        )

        reason = orchestrator._analyze_why_failed(before, after, repair_output)
        assert "Made things worse" in reason

    def test_new_failures_detected(
        self,
        orchestrator,
        repair_output,
    ):
        """Test detecting new test failures."""
        before = TestResult(
            framework="pytest",
            total_tests=10,
            passed=9,
            failed=1,
            duration_seconds=1.0,
            failures=[
                TestFailure(
                    test_name="test_add",
                    test_file="tests/test.py",
                    error_type="AssertionError",
                    error_message="original",
                    stack_trace="...",
                )
            ],
        )
        after = TestResult(
            framework="pytest",
            total_tests=10,
            passed=9,
            failed=1,
            duration_seconds=1.0,
            failures=[
                TestFailure(
                    test_name="test_multiply",  # Different test now fails
                    test_file="tests/test.py",
                    error_type="AssertionError",
                    error_message="new",
                    stack_trace="...",
                )
            ],
        )

        reason = orchestrator._analyze_why_failed(before, after, repair_output)
        assert "new failures" in reason
        assert "test_multiply" in reason


class TestDryRun:
    """Tests for dry run functionality."""

    @pytest.mark.asyncio
    async def test_dry_run_returns_preview(
        self,
        orchestrator,
        mock_workspace,
        mock_test_executor,
        mock_diagnostic_agent,
        mock_repair_agent,
        mock_surgical_editor,
        failing_test_result,
        diagnostic_report,
        repair_output,
    ):
        """Test dry run returns diagnostic, repair, and diff."""
        mock_test_executor.run_tests.return_value = failing_test_result
        mock_diagnostic_agent.execute.return_value = diagnostic_report
        mock_repair_agent.execute.return_value = repair_output
        mock_surgical_editor.generate_diff.return_value = "--- a\n+++ b"

        request = RepairRequest(
            task_id="TEST-001",
            workspace=mock_workspace,
        )

        diagnostic, repair, diff = await orchestrator.dry_run(request)

        assert diagnostic == diagnostic_report
        assert repair == repair_output
        assert "---" in diff
        # Verify no changes were applied
        mock_surgical_editor.apply_changes.assert_not_called()

    @pytest.mark.asyncio
    async def test_dry_run_fails_if_passing(
        self,
        orchestrator,
        mock_workspace,
        mock_test_executor,
        passing_test_result,
    ):
        """Test dry run fails if tests already passing."""
        mock_test_executor.run_tests.return_value = passing_test_result

        request = RepairRequest(
            task_id="TEST-001",
            workspace=mock_workspace,
        )

        from asp.orchestrators.repair_orchestrator import RepairError

        with pytest.raises(RepairError, match="already passing"):
            await orchestrator.dry_run(request)


class TestCleanup:
    """Tests for cleanup functionality."""

    def test_cleanup_calls_surgical_editor(
        self,
        orchestrator,
        mock_surgical_editor,
    ):
        """Test cleanup cleans up surgical editor backups."""
        orchestrator.cleanup()
        mock_surgical_editor.cleanup_backups.assert_called_once()

    def test_cleanup_handles_errors(
        self,
        orchestrator,
        mock_surgical_editor,
    ):
        """Test cleanup handles errors gracefully."""
        mock_surgical_editor.cleanup_backups.side_effect = Exception("Error")
        # Should not raise
        orchestrator.cleanup()
