"""
Pydantic models for Repair Agent.

The Repair Agent applies fixes suggested by the Diagnostic Agent and verifies
them through test execution. This module defines the input/output data structures
for the repair phase of the repair workflow.

Models:
    - RepairAttempt: Record of a single repair attempt
    - RepairInput: Input to Repair Agent
    - RepairOutput: Output from Repair Agent

Part of ADR 006: Repair Workflow Architecture.

Author: ASP Development Team
Date: December 10, 2025
"""

from pydantic import BaseModel, Field, field_validator

from asp.models.diagnostic import CodeChange, DiagnosticReport
from asp.models.execution import TestResult

# =============================================================================
# Repair Attempt Tracking
# =============================================================================


class RepairAttempt(BaseModel):
    """
    Record of a single repair attempt.

    Tracks what changes were made and whether they fixed the issue.
    Used to provide context to subsequent repair attempts to avoid
    repeating failed fixes.

    Attributes:
        attempt_number: Sequential attempt number (1-indexed)
        changes_made: List of code changes that were applied
        test_result: Test results after applying the changes
        why_failed: Explanation of why this attempt failed (if applicable)
        rollback_performed: Whether changes were rolled back after failure
    """

    attempt_number: int = Field(
        ...,
        ge=1,
        description="Sequential attempt number (1-indexed)",
    )

    changes_made: list[CodeChange] = Field(
        ...,
        description="Code changes that were applied in this attempt",
    )

    test_result: TestResult = Field(
        ...,
        description="Test results after applying the changes",
    )

    why_failed: str | None = Field(
        default=None,
        description="Explanation of why this attempt failed (if applicable)",
    )

    rollback_performed: bool = Field(
        default=False,
        description="Whether changes were rolled back after failure",
    )

    @property
    def succeeded(self) -> bool:
        """Check if this attempt fixed the issue."""
        return self.test_result.success

    class Config:
        json_schema_extra = {
            "example": {
                "attempt_number": 1,
                "changes_made": [
                    {
                        "file_path": "src/calculator.py",
                        "search_text": "return a - b",
                        "replace_text": "return a + b",
                    }
                ],
                "test_result": {
                    "framework": "pytest",
                    "total_tests": 5,
                    "passed": 5,
                    "failed": 0,
                    "duration_seconds": 1.0,
                },
                "why_failed": None,
                "rollback_performed": False,
            }
        }


# =============================================================================
# Input/Output Models
# =============================================================================


class RepairInput(BaseModel):
    """
    Input data for Repair Agent.

    Contains the diagnostic report, workspace information, and history
    of previous repair attempts for context.

    Attributes:
        task_id: Unique task identifier for traceability
        workspace_path: Path to the workspace containing the code
        diagnostic: Diagnostic report with root cause and suggested fixes
        previous_attempts: History of previous repair attempts
        max_changes_per_file: Maximum number of changes allowed per file
        source_files: Optional dict of file paths to contents
    """

    task_id: str = Field(
        ...,
        min_length=3,
        description="Unique task identifier",
    )

    workspace_path: str = Field(
        ...,
        min_length=1,
        description="Path to the workspace containing code",
    )

    diagnostic: DiagnosticReport = Field(
        ...,
        description="Diagnostic report with root cause and suggested fixes",
    )

    previous_attempts: list[RepairAttempt] = Field(
        default_factory=list,
        description="History of previous repair attempts",
    )

    max_changes_per_file: int = Field(
        default=50,
        ge=1,
        le=100,
        description="Maximum number of changes allowed per file",
    )

    source_files: dict[str, str] = Field(
        default_factory=dict,
        description="Dict of file paths to contents for context",
    )

    @field_validator("task_id")
    @classmethod
    def validate_task_id(cls, v: str) -> str:
        """Validate task_id format."""
        if not v or len(v.strip()) < 3:
            raise ValueError("task_id must be at least 3 characters")
        return v.strip()

    @property
    def attempt_count(self) -> int:
        """Get the number of previous attempts."""
        return len(self.previous_attempts)

    @property
    def has_failed_attempts(self) -> bool:
        """Check if there are any failed previous attempts."""
        return any(not attempt.succeeded for attempt in self.previous_attempts)

    @property
    def last_attempt(self) -> RepairAttempt | None:
        """Get the most recent attempt."""
        if not self.previous_attempts:
            return None
        return self.previous_attempts[-1]

    class Config:
        json_schema_extra = {
            "example": {
                "task_id": "REPAIR-001",
                "workspace_path": "/workspaces/my-project",
                "diagnostic": {
                    "task_id": "REPAIR-001",
                    "issue_type": "logic_error",
                    "severity": "High",
                    "root_cause": "Wrong operator in add function",
                    "affected_files": [],
                    "suggested_fixes": [],
                    "confidence": 0.95,
                },
                "previous_attempts": [],
                "max_changes_per_file": 50,
            }
        }


class RepairOutput(BaseModel):
    """
    Output from Repair Agent.

    Contains the repair strategy, code changes to apply, and metadata
    about the repair approach.

    Attributes:
        task_id: Unique task identifier for traceability
        strategy: Description of the repair strategy being used
        changes: List of code changes to apply (search-replace pairs)
        explanation: Detailed explanation of why these changes fix the issue
        confidence: Confidence score (0.0-1.0) that this repair will work
        alternative_fixes: Alternative fix approaches if primary fails
        considerations: Important things to verify after applying the fix
        based_on_fix_id: ID of the suggested fix this is based on (if any)
    """

    task_id: str = Field(
        ...,
        min_length=3,
        description="Unique task identifier",
    )

    strategy: str = Field(
        ...,
        min_length=10,
        description="Description of the repair strategy",
    )

    changes: list[CodeChange] = Field(
        ...,
        min_length=1,
        description="Code changes to apply (search-replace pairs)",
    )

    explanation: str = Field(
        ...,
        min_length=20,
        description="Detailed explanation of why these changes fix the issue",
    )

    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Confidence score (0.0-1.0) that this repair will work",
    )

    alternative_fixes: list[dict] | None = Field(
        default=None,
        description="Alternative fix approaches if primary fails",
    )

    considerations: list[str] = Field(
        default_factory=list,
        description="Important things to verify after applying the fix",
    )

    based_on_fix_id: str | None = Field(
        default=None,
        description="ID of the suggested fix this is based on (if any)",
    )

    @property
    def is_high_confidence(self) -> bool:
        """Check if repair has high confidence (>= 0.8)."""
        return self.confidence >= 0.8

    @property
    def file_count(self) -> int:
        """Get the number of unique files being modified."""
        return len({change.file_path for change in self.changes})

    @property
    def change_count(self) -> int:
        """Get the total number of changes."""
        return len(self.changes)

    class Config:
        json_schema_extra = {
            "example": {
                "task_id": "REPAIR-001",
                "strategy": "Apply direct operator fix based on diagnostic recommendation",
                "changes": [
                    {
                        "file_path": "src/calculator.py",
                        "search_text": "return a - b",
                        "replace_text": "return a + b",
                        "description": "Fix addition operator",
                    }
                ],
                "explanation": "The diagnostic identified that the add function uses subtraction. Changing the operator from - to + will fix the test failures.",
                "confidence": 0.95,
                "alternative_fixes": None,
                "considerations": [
                    "Verify no other code depends on the incorrect behavior"
                ],
                "based_on_fix_id": "FIX-001",
            }
        }


# =============================================================================
# Repair Result (for orchestrator)
# =============================================================================


class RepairResult(BaseModel):
    """
    Complete result of a repair workflow execution.

    Used by the RepairOrchestrator to track the full repair process,
    including all attempts and the final outcome.

    Attributes:
        task_id: Unique task identifier
        success: Whether the repair ultimately succeeded
        iterations_used: Number of repair iterations attempted
        final_test_result: Test results from the final state
        changes_made: All code changes that were applied and kept
        diagnostic_reports: All diagnostic reports generated
        repair_attempts: History of all repair attempts
        escalated_to_human: Whether human intervention was requested
        escalation_reason: Reason for escalation (if applicable)
    """

    task_id: str = Field(
        ...,
        min_length=3,
        description="Unique task identifier",
    )

    success: bool = Field(
        ...,
        description="Whether the repair ultimately succeeded",
    )

    iterations_used: int = Field(
        ...,
        ge=0,
        description="Number of repair iterations attempted",
    )

    final_test_result: TestResult = Field(
        ...,
        description="Test results from the final state",
    )

    changes_made: list[CodeChange] = Field(
        default_factory=list,
        description="All code changes that were applied and kept",
    )

    diagnostic_reports: list[DiagnosticReport] = Field(
        default_factory=list,
        description="All diagnostic reports generated during repair",
    )

    repair_attempts: list[RepairAttempt] = Field(
        default_factory=list,
        description="History of all repair attempts",
    )

    escalated_to_human: bool = Field(
        default=False,
        description="Whether human intervention was requested",
    )

    escalation_reason: str | None = Field(
        default=None,
        description="Reason for escalation (if applicable)",
    )

    @property
    def total_changes(self) -> int:
        """Get total number of changes made."""
        return len(self.changes_made)

    @property
    def files_modified(self) -> list[str]:
        """Get list of unique files that were modified."""
        return list({change.file_path for change in self.changes_made})

    class Config:
        json_schema_extra = {
            "example": {
                "task_id": "REPAIR-001",
                "success": True,
                "iterations_used": 1,
                "final_test_result": {
                    "framework": "pytest",
                    "total_tests": 5,
                    "passed": 5,
                    "failed": 0,
                    "duration_seconds": 1.5,
                },
                "changes_made": [
                    {
                        "file_path": "src/calculator.py",
                        "search_text": "return a - b",
                        "replace_text": "return a + b",
                    }
                ],
                "escalated_to_human": False,
            }
        }
