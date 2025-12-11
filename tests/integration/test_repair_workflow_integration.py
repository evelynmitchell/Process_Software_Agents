"""
Integration tests for Repair Workflow.

Tests the integration between RepairOrchestrator, DiagnosticAgent, RepairAgent,
and supporting services (TestExecutor, SurgicalEditor, SandboxExecutor).

These tests validate the complete repair loop with mocked LLM responses.
"""

# pylint: disable=too-many-public-methods

import tempfile
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock

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


@dataclass
class MockWorkspace:
    """Mock workspace for testing."""

    task_id: str
    path: Path
    target_repo_path: Path
    asp_path: Path
    created_at: datetime


class TestRepairWorkflowIntegration:
    """Integration tests for the complete repair workflow."""

    @pytest.fixture
    def temp_workspace(self):
        """Create a temporary workspace with a buggy calculator."""
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace_path = Path(tmpdir)

            # Create src directory
            src_dir = workspace_path / "src"
            src_dir.mkdir()

            # Create buggy calculator
            calculator_py = src_dir / "calculator.py"
            calculator_py.write_text(
                '''"""Simple calculator module with a bug."""


def add(a: int, b: int) -> int:
    """Add two numbers. BUG: uses subtraction instead of addition."""
    return a - b  # Bug: should be a + b


def subtract(a: int, b: int) -> int:
    """Subtract b from a."""
    return a - b


def multiply(a: int, b: int) -> int:
    """Multiply two numbers."""
    return a * b
'''
            )

            # Create tests directory
            tests_dir = workspace_path / "tests"
            tests_dir.mkdir()

            # Create test file
            test_calculator_py = tests_dir / "test_calculator.py"
            test_calculator_py.write_text(
                '''"""Tests for calculator module."""

import sys
sys.path.insert(0, str(__file__).replace("/tests/test_calculator.py", "/src"))

from calculator import add, subtract, multiply


def test_add():
    """Test addition."""
    assert add(2, 3) == 5  # This will fail due to bug
    assert add(-1, 1) == 0
    assert add(0, 0) == 0


def test_subtract():
    """Test subtraction."""
    assert subtract(5, 3) == 2
    assert subtract(0, 0) == 0


def test_multiply():
    """Test multiplication."""
    assert multiply(2, 3) == 6
    assert multiply(-2, 3) == -6
'''
            )

            # Create .asp directory
            asp_dir = workspace_path / ".asp"
            asp_dir.mkdir()

            # Create workspace object
            workspace = MockWorkspace(
                task_id="REPAIR-INTEGRATION-001",
                path=workspace_path,
                target_repo_path=workspace_path,
                asp_path=asp_dir,
                created_at=datetime.now(),
            )

            yield workspace

    @pytest.fixture
    def mock_diagnostic_report(self):
        """Create a realistic diagnostic report."""
        return DiagnosticReport(
            task_id="REPAIR-INTEGRATION-001",
            issue_type=IssueType.LOGIC_ERROR,
            severity=Severity.HIGH,
            root_cause=(
                "The add function in calculator.py uses subtraction operator (-) "
                "instead of addition operator (+). This causes add(2, 3) to return -1 "
                "instead of 5."
            ),
            affected_files=[
                AffectedFile(
                    path="src/calculator.py",
                    line_start=5,
                    line_end=7,
                    code_snippet="return a - b  # Bug: should be a + b",
                    issue_description="Wrong arithmetic operator used in add function",
                )
            ],
            suggested_fixes=[
                SuggestedFix(
                    fix_id="FIX-001",
                    description="Change subtraction to addition in the add function",
                    confidence=0.95,
                    changes=[
                        CodeChange(
                            file_path="src/calculator.py",
                            search_text="return a - b  # Bug: should be a + b",
                            replace_text="return a + b",
                        )
                    ],
                )
            ],
            confidence=0.9,
        )

    @pytest.fixture
    def mock_repair_output(self):
        """Create a realistic repair output."""
        return RepairOutput(
            task_id="REPAIR-INTEGRATION-001",
            strategy=(
                "Apply the fix recommended by the diagnostic agent: "
                "change the subtraction operator to addition in the add function."
            ),
            changes=[
                CodeChange(
                    file_path="src/calculator.py",
                    search_text="return a - b  # Bug: should be a + b",
                    replace_text="return a + b",
                )
            ],
            explanation=(
                "The diagnostic correctly identified a logic error where "
                "subtraction was used instead of addition. The fix changes "
                "the operator from - to +."
            ),
            confidence=0.95,
        )

    @pytest.fixture
    def failing_test_result(self):
        """Create a failing test result."""
        return TestResult(
            framework="pytest",
            total_tests=3,
            passed=2,
            failed=1,
            duration_seconds=0.5,
            failures=[
                TestFailure(
                    test_name="test_add",
                    test_file="tests/test_calculator.py",
                    line_number=10,
                    error_type="AssertionError",
                    error_message="assert add(2, 3) == 5\nassert -1 == 5",
                    stack_trace="...",
                )
            ],
        )

    @pytest.fixture
    def passing_test_result(self):
        """Create a passing test result."""
        return TestResult(
            framework="pytest",
            total_tests=3,
            passed=3,
            failed=0,
            duration_seconds=0.5,
            failures=[],
        )

    @pytest.mark.asyncio
    async def test_complete_repair_loop_with_mocks(
        self,
        temp_workspace,
        mock_diagnostic_report,
        mock_repair_output,
        failing_test_result,
        passing_test_result,
    ):
        """Test complete repair loop with mocked agents."""
        # Create mocks
        mock_sandbox = MagicMock()
        mock_test_executor = MagicMock()
        mock_surgical_editor = MagicMock()
        mock_diagnostic_agent = MagicMock()
        mock_repair_agent = MagicMock()

        # Configure mock responses
        # First test run fails, second (after fix) passes
        mock_test_executor.run_tests.side_effect = [
            failing_test_result,
            passing_test_result,
        ]
        mock_diagnostic_agent.execute.return_value = mock_diagnostic_report
        mock_repair_agent.execute.return_value = mock_repair_output

        # Configure surgical editor
        successful_edit = MagicMock()
        successful_edit.success = True
        successful_edit.changes_applied = 1
        successful_edit.changes_failed = 0
        successful_edit.files_modified = ["src/calculator.py"]
        successful_edit.errors = []
        mock_surgical_editor.apply_changes.return_value = successful_edit
        mock_surgical_editor.cleanup_backups = MagicMock()

        # Create orchestrator
        orchestrator = RepairOrchestrator(
            sandbox=mock_sandbox,
            test_executor=mock_test_executor,
            surgical_editor=mock_surgical_editor,
            diagnostic_agent=mock_diagnostic_agent,
            repair_agent=mock_repair_agent,
        )

        # Create request
        request = RepairRequest(
            task_id="REPAIR-INTEGRATION-001",
            workspace=temp_workspace,
            hitl_config=AUTONOMOUS_CONFIG,
        )

        # Run repair
        result = await orchestrator.repair(request)

        # Verify success
        assert result.success is True
        assert result.iterations_used == 1
        assert len(result.changes_made) == 1
        assert result.changes_made[0].file_path == "src/calculator.py"

        # Verify agents were called
        mock_diagnostic_agent.execute.assert_called_once()
        mock_repair_agent.execute.assert_called_once()
        mock_surgical_editor.apply_changes.assert_called_once()
        mock_surgical_editor.cleanup_backups.assert_called_once()

    @pytest.mark.asyncio
    async def test_repair_escalates_on_low_confidence(
        self,
        temp_workspace,
        failing_test_result,
    ):
        """Test that low confidence triggers HITL escalation."""
        # Create mocks
        mock_sandbox = MagicMock()
        mock_test_executor = MagicMock()
        mock_surgical_editor = MagicMock()
        mock_diagnostic_agent = MagicMock()
        mock_repair_agent = MagicMock()

        # Configure low confidence diagnostic
        low_confidence_diagnostic = DiagnosticReport(
            task_id="REPAIR-INTEGRATION-001",
            issue_type=IssueType.LOGIC_ERROR,
            severity=Severity.MEDIUM,
            root_cause="Uncertain about the exact cause of the failure",
            affected_files=[
                AffectedFile(
                    path="src/calculator.py",
                    line_start=1,
                    line_end=10,
                    code_snippet="...",
                    issue_description="Possibly incorrect implementation",
                )
            ],
            suggested_fixes=[
                SuggestedFix(
                    fix_id="FIX-001",
                    description="Attempt to fix the issue that was identified",
                    confidence=0.3,  # Very low confidence
                    changes=[
                        CodeChange(
                            file_path="src/calculator.py",
                            search_text="return a - b",
                            replace_text="return a + b",
                        )
                    ],
                )
            ],
            confidence=0.3,  # Very low confidence
        )

        low_confidence_repair = RepairOutput(
            task_id="REPAIR-INTEGRATION-001",
            strategy="Uncertain fix attempt based on low-confidence diagnosis",
            changes=[
                CodeChange(
                    file_path="src/calculator.py",
                    search_text="return a - b",
                    replace_text="return a + b",
                )
            ],
            explanation="Attempting fix despite low confidence",
            confidence=0.3,
        )

        # Configure mocks
        mock_test_executor.run_tests.return_value = failing_test_result
        mock_diagnostic_agent.execute.return_value = low_confidence_diagnostic
        mock_repair_agent.execute.return_value = low_confidence_repair

        # Create orchestrator
        orchestrator = RepairOrchestrator(
            sandbox=mock_sandbox,
            test_executor=mock_test_executor,
            surgical_editor=mock_surgical_editor,
            diagnostic_agent=mock_diagnostic_agent,
            repair_agent=mock_repair_agent,
        )

        # Create request with threshold config
        hitl_config = HITLConfig(
            mode="threshold",
            require_approval_for_confidence_below=0.6,
        )

        request = RepairRequest(
            task_id="REPAIR-INTEGRATION-001",
            workspace=temp_workspace,
            hitl_config=hitl_config,
        )

        # Run repair without approval callback (should fail)
        result = await orchestrator.repair(request, approval_callback=None)

        # Should have escalated due to low confidence
        assert result.success is False
        assert result.escalated_to_human is True
        assert "no approver" in result.escalation_reason.lower()

    @pytest.mark.asyncio
    async def test_repair_rejects_on_hitl_rejection(
        self,
        temp_workspace,
        mock_diagnostic_report,
        mock_repair_output,
        failing_test_result,
    ):
        """Test that HITL rejection stops the repair."""
        # Create mocks
        mock_sandbox = MagicMock()
        mock_test_executor = MagicMock()
        mock_surgical_editor = MagicMock()
        mock_diagnostic_agent = MagicMock()
        mock_repair_agent = MagicMock()

        # Configure mocks
        mock_test_executor.run_tests.return_value = failing_test_result
        mock_diagnostic_agent.execute.return_value = mock_diagnostic_report
        mock_repair_agent.execute.return_value = mock_repair_output

        # Create orchestrator
        orchestrator = RepairOrchestrator(
            sandbox=mock_sandbox,
            test_executor=mock_test_executor,
            surgical_editor=mock_surgical_editor,
            diagnostic_agent=mock_diagnostic_agent,
            repair_agent=mock_repair_agent,
        )

        # Create request with supervised mode
        hitl_config = HITLConfig(mode="supervised")

        request = RepairRequest(
            task_id="REPAIR-INTEGRATION-001",
            workspace=temp_workspace,
            hitl_config=hitl_config,
        )

        # Human rejects
        def rejection_callback(reason, confidence, files, iteration):
            return False

        # Run repair
        with pytest.raises(HumanRejectedRepair):
            await orchestrator.repair(request, approval_callback=rejection_callback)

    @pytest.mark.asyncio
    async def test_repair_rollback_on_failed_fix(
        self,
        temp_workspace,
        mock_diagnostic_report,
        mock_repair_output,
        failing_test_result,
    ):
        """Test rollback is called when fix doesn't work."""
        # Create mocks
        mock_sandbox = MagicMock()
        mock_test_executor = MagicMock()
        mock_surgical_editor = MagicMock()
        mock_diagnostic_agent = MagicMock()
        mock_repair_agent = MagicMock()

        # Configure mocks - tests always fail
        mock_test_executor.run_tests.return_value = failing_test_result
        mock_diagnostic_agent.execute.return_value = mock_diagnostic_report
        mock_repair_agent.execute.return_value = mock_repair_output

        # Configure surgical editor
        successful_edit = MagicMock()
        successful_edit.success = True
        successful_edit.changes_applied = 1
        successful_edit.changes_failed = 0
        successful_edit.files_modified = ["src/calculator.py"]
        successful_edit.errors = []
        mock_surgical_editor.apply_changes.return_value = successful_edit
        mock_surgical_editor.rollback = MagicMock()

        # Create orchestrator
        orchestrator = RepairOrchestrator(
            sandbox=mock_sandbox,
            test_executor=mock_test_executor,
            surgical_editor=mock_surgical_editor,
            diagnostic_agent=mock_diagnostic_agent,
            repair_agent=mock_repair_agent,
        )

        # Create request with 1 iteration
        request = RepairRequest(
            task_id="REPAIR-INTEGRATION-001",
            workspace=temp_workspace,
            max_iterations=1,
            hitl_config=AUTONOMOUS_CONFIG,
        )

        # Run repair
        result = await orchestrator.repair(request)

        # Should have failed
        assert result.success is False
        assert result.iterations_used == 1

        # Rollback should have been called
        mock_surgical_editor.rollback.assert_called()

    @pytest.mark.asyncio
    async def test_dry_run_shows_preview(
        self,
        temp_workspace,
        mock_diagnostic_report,
        mock_repair_output,
        failing_test_result,
    ):
        """Test dry run returns preview without applying changes."""
        # Create mocks
        mock_sandbox = MagicMock()
        mock_test_executor = MagicMock()
        mock_surgical_editor = MagicMock()
        mock_diagnostic_agent = MagicMock()
        mock_repair_agent = MagicMock()

        # Configure mocks
        mock_test_executor.run_tests.return_value = failing_test_result
        mock_diagnostic_agent.execute.return_value = mock_diagnostic_report
        mock_repair_agent.execute.return_value = mock_repair_output
        mock_surgical_editor.generate_diff.return_value = (
            "--- a/src/calculator.py\n"
            "+++ b/src/calculator.py\n"
            "@@ -5,7 +5,7 @@\n"
            "-    return a - b  # Bug: should be a + b\n"
            "+    return a + b\n"
        )

        # Create orchestrator
        orchestrator = RepairOrchestrator(
            sandbox=mock_sandbox,
            test_executor=mock_test_executor,
            surgical_editor=mock_surgical_editor,
            diagnostic_agent=mock_diagnostic_agent,
            repair_agent=mock_repair_agent,
        )

        # Create request
        request = RepairRequest(
            task_id="REPAIR-INTEGRATION-001",
            workspace=temp_workspace,
        )

        # Run dry run
        diagnostic, repair, diff = await orchestrator.dry_run(request)

        # Verify outputs
        assert diagnostic.issue_type == IssueType.LOGIC_ERROR
        assert len(repair.changes) == 1
        assert "return a + b" in diff

        # Verify no changes were applied
        mock_surgical_editor.apply_changes.assert_not_called()


class TestRepairCLIIntegration:
    """Integration tests for repair CLI command."""

    def test_cli_parser_repair_command_exists(self):
        """Test that repair subcommand is available."""
        from asp.cli.main import create_parser

        parser = create_parser()

        # Find subparsers
        found_repair = False
        for action in parser._subparsers._actions:
            if hasattr(action, "choices") and action.choices is not None:
                if "repair" in action.choices:
                    found_repair = True
                    repair_parser = action.choices["repair"]
                    # Check required arguments exist
                    assert any(
                        a.dest == "task_id"
                        for a in repair_parser._actions
                        if hasattr(a, "dest")
                    )
                    assert any(
                        a.dest == "workspace"
                        for a in repair_parser._actions
                        if hasattr(a, "dest")
                    )
                    break

        assert found_repair, "Could not find repair subcommand"

    def test_cli_parser_repair_options(self):
        """Test repair command options."""
        from asp.cli.main import create_parser

        parser = create_parser()
        args = parser.parse_args(
            [
                "repair",
                "--task-id",
                "TEST-001",
                "--workspace",
                "/tmp/test",
                "--max-iterations",
                "3",
                "--auto-approve",
                "--dry-run",
            ]
        )

        assert args.task_id == "TEST-001"
        assert args.workspace == "/tmp/test"
        assert args.max_iterations == 3
        assert args.auto_approve is True
        assert args.dry_run is True


class TestRepairOrchestratorTypes:
    """Tests for repair orchestrator types."""

    def test_repair_execution_result_dataclass(self):
        """Test RepairExecutionResult dataclass."""
        from asp.models.repair import RepairResult
        from asp.orchestrators.types import RepairExecutionResult

        # Create a minimal repair result
        repair_result = RepairResult(
            task_id="TEST-001",
            success=True,
            iterations_used=1,
            final_test_result=TestResult(
                framework="pytest",
                total_tests=5,
                passed=5,
                failed=0,
                duration_seconds=1.0,
            ),
            changes_made=[],
            diagnostic_reports=[],
            repair_attempts=[],
        )

        # Create execution result
        execution_result = RepairExecutionResult(
            task_id="TEST-001",
            timestamp=datetime.now(),
            overall_status="PASS",
            repair_result=repair_result,
            total_duration_seconds=10.5,
            execution_log=[],
        )

        assert execution_result.task_id == "TEST-001"
        assert execution_result.overall_status == "PASS"
        assert execution_result.repair_result.success is True

    def test_tsp_execution_result_has_repair_fields(self):
        """Test TSPExecutionResult has repair mode fields."""
        from asp.orchestrators.types import TSPExecutionResult

        # Check field annotations
        assert "mode" in TSPExecutionResult.__dataclass_fields__
        assert "repair_result" in TSPExecutionResult.__dataclass_fields__
