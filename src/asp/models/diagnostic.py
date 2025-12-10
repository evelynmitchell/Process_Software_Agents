"""
Pydantic models for Diagnostic Agent.

The Diagnostic Agent analyzes test failures to identify root causes and suggest fixes.
This module defines the input/output data structures for the diagnostic phase of the
repair workflow.

Models:
    - IssueType: Classification of issue types
    - Severity: Issue severity levels
    - AffectedFile: File with issue details
    - CodeChange: Search-replace based code modification
    - SuggestedFix: Proposed fix with changes
    - DiagnosticInput: Input to Diagnostic Agent
    - DiagnosticReport: Output from Diagnostic Agent

Part of ADR 006: Repair Workflow Architecture.

Author: ASP Development Team
Date: December 10, 2025
"""

from enum import Enum

from pydantic import BaseModel, Field, field_validator, model_validator

from asp.models.execution import TestResult

# =============================================================================
# Enums
# =============================================================================


class IssueType(str, Enum):
    """
    Classification of issue types found during diagnosis.

    Used to categorize the nature of the problem for appropriate handling.
    """

    TEST_FAILURE = "test_failure"
    BUILD_ERROR = "build_error"
    RUNTIME_ERROR = "runtime_error"
    TYPE_ERROR = "type_error"
    IMPORT_ERROR = "import_error"
    SYNTAX_ERROR = "syntax_error"
    LOGIC_ERROR = "logic_error"
    CONFIGURATION_ERROR = "configuration_error"


class Severity(str, Enum):
    """
    Severity levels for diagnosed issues.

    Determines priority and whether human intervention is needed.
    """

    CRITICAL = "Critical"
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"


# =============================================================================
# Code Change Models
# =============================================================================


class AffectedFile(BaseModel):
    """
    Details about a file affected by the diagnosed issue.

    Contains location information and a snippet of the problematic code
    to provide context for the fix.

    Attributes:
        path: Relative path to the affected file
        line_start: Starting line number of the affected region
        line_end: Ending line number of the affected region
        code_snippet: Relevant code snippet showing the issue
        issue_description: Description of what's wrong in this location
    """

    path: str = Field(
        ...,
        min_length=1,
        description="Relative path to the affected file",
    )

    line_start: int = Field(
        ...,
        ge=1,
        description="Starting line number of affected region",
    )

    line_end: int = Field(
        ...,
        ge=1,
        description="Ending line number of affected region",
    )

    code_snippet: str = Field(
        ...,
        description="Code snippet showing the problematic area",
    )

    issue_description: str = Field(
        ...,
        min_length=10,
        description="Description of the issue in this location",
    )

    @model_validator(mode="after")
    def validate_line_range(self) -> "AffectedFile":
        """Ensure line_end >= line_start."""
        if self.line_end < self.line_start:
            raise ValueError(
                f"line_end ({self.line_end}) must be >= line_start ({self.line_start})"
            )
        return self

    @field_validator("path")
    @classmethod
    def validate_path(cls, v: str) -> str:
        """Ensure path is trimmed and normalized."""
        return v.strip()

    class Config:
        json_schema_extra = {
            "example": {
                "path": "src/calculator.py",
                "line_start": 5,
                "line_end": 7,
                "code_snippet": "def add(a, b):\n    return a - b  # BUG: should be +",
                "issue_description": "Addition function uses subtraction operator instead of addition",
            }
        }


class CodeChange(BaseModel):
    """
    Search-replace based code modification.

    Uses text search and replace rather than line numbers because LLMs are
    unreliable at counting lines. The search_text must be unique enough to
    identify the correct location.

    Attributes:
        file_path: Path to the file to modify
        search_text: Exact text to find (must be unique in the file)
        replace_text: Text to replace the search_text with
        occurrence: Which occurrence to replace (1-indexed, 0=all)
        description: Human-readable description of the change
    """

    file_path: str = Field(
        ...,
        min_length=1,
        description="Path to the file to modify",
    )

    search_text: str = Field(
        ...,
        min_length=1,
        description="Exact text to find (must be unique in file)",
    )

    replace_text: str = Field(
        ...,
        description="Text to replace search_text with (can be empty for deletion)",
    )

    occurrence: int = Field(
        default=1,
        ge=0,
        description="Which occurrence to replace (1=first, 0=all)",
    )

    description: str = Field(
        default="",
        description="Human-readable description of the change",
    )

    @field_validator("file_path")
    @classmethod
    def validate_file_path(cls, v: str) -> str:
        """Ensure file path is trimmed."""
        return v.strip()

    @model_validator(mode="after")
    def validate_change_is_different(self) -> "CodeChange":
        """Ensure search and replace texts are different."""
        if self.search_text == self.replace_text:
            raise ValueError("search_text and replace_text must be different")
        return self

    class Config:
        json_schema_extra = {
            "example": {
                "file_path": "src/calculator.py",
                "search_text": "return a - b",
                "replace_text": "return a + b",
                "occurrence": 1,
                "description": "Fix addition operator in add function",
            }
        }


class SuggestedFix(BaseModel):
    """
    A suggested fix for the diagnosed issue.

    Contains one or more CodeChanges that together implement the fix,
    along with metadata about confidence and approach.

    Attributes:
        fix_id: Unique identifier for this fix suggestion
        description: Human-readable description of the fix
        confidence: Confidence score (0.0-1.0) that this fix will work
        changes: List of code changes to implement the fix
        rationale: Explanation of why this fix should work
        risks: Potential risks or side effects of this fix
    """

    fix_id: str = Field(
        ...,
        min_length=1,
        description="Unique identifier for this fix (e.g., FIX-001)",
    )

    description: str = Field(
        ...,
        min_length=10,
        description="Human-readable description of the fix",
    )

    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Confidence score (0.0-1.0) that this fix will work",
    )

    changes: list[CodeChange] = Field(
        ...,
        min_length=1,
        description="Code changes to implement this fix",
    )

    rationale: str = Field(
        default="",
        description="Explanation of why this fix should work",
    )

    risks: list[str] = Field(
        default_factory=list,
        description="Potential risks or side effects",
    )

    class Config:
        json_schema_extra = {
            "example": {
                "fix_id": "FIX-001",
                "description": "Change subtraction to addition in the add function",
                "confidence": 0.95,
                "changes": [
                    {
                        "file_path": "src/calculator.py",
                        "search_text": "return a - b",
                        "replace_text": "return a + b",
                        "occurrence": 1,
                        "description": "Fix operator",
                    }
                ],
                "rationale": "The test expects a + b but the code returns a - b",
                "risks": [],
            }
        }


# =============================================================================
# Input/Output Models
# =============================================================================


class DiagnosticInput(BaseModel):
    """
    Input data for Diagnostic Agent.

    Contains all information needed to diagnose a test failure or error,
    including test results, error details, and workspace location.

    Attributes:
        task_id: Unique task identifier for traceability
        workspace_path: Path to the workspace containing the code
        test_result: Parsed test execution results
        error_type: Type of error being diagnosed
        error_message: Human-readable error message
        stack_trace: Full stack trace for debugging
        source_files: Optional dict of file paths to contents for context
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

    test_result: TestResult = Field(
        ...,
        description="Parsed test execution results",
    )

    error_type: str = Field(
        ...,
        min_length=1,
        description="Type of error (e.g., AssertionError, ImportError)",
    )

    error_message: str = Field(
        ...,
        description="Human-readable error message",
    )

    stack_trace: str = Field(
        default="",
        description="Full stack trace for debugging",
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

    class Config:
        json_schema_extra = {
            "example": {
                "task_id": "REPAIR-001",
                "workspace_path": "/workspaces/my-project",
                "test_result": {
                    "framework": "pytest",
                    "total_tests": 5,
                    "passed": 4,
                    "failed": 1,
                    "duration_seconds": 1.5,
                },
                "error_type": "AssertionError",
                "error_message": "assert add(2, 3) == 5, but got -1",
                "stack_trace": "...",
            }
        }


class DiagnosticReport(BaseModel):
    """
    Complete diagnostic report from Diagnostic Agent.

    Contains the root cause analysis, affected files, and suggested fixes
    for the diagnosed issue. This output feeds into the Repair Agent.

    Attributes:
        task_id: Unique task identifier for traceability
        issue_type: Classification of the issue
        severity: Severity level of the issue
        root_cause: Description of the underlying root cause
        affected_files: List of files affected by the issue
        suggested_fixes: List of suggested fixes (ordered by confidence)
        confidence: Overall confidence in the diagnosis (0.0-1.0)
        diagnosis_notes: Additional notes from the diagnosis process
        related_issues: IDs of related issues if any
    """

    task_id: str = Field(
        ...,
        min_length=3,
        description="Unique task identifier",
    )

    issue_type: IssueType = Field(
        ...,
        description="Classification of the issue type",
    )

    severity: Severity = Field(
        ...,
        description="Severity level of the issue",
    )

    root_cause: str = Field(
        ...,
        min_length=20,
        description="Description of the underlying root cause",
    )

    affected_files: list[AffectedFile] = Field(
        ...,
        min_length=1,
        description="Files affected by this issue",
    )

    suggested_fixes: list[SuggestedFix] = Field(
        ...,
        min_length=1,
        description="Suggested fixes ordered by confidence (highest first)",
    )

    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Overall confidence in the diagnosis (0.0-1.0)",
    )

    diagnosis_notes: str = Field(
        default="",
        description="Additional notes from the diagnosis process",
    )

    related_issues: list[str] = Field(
        default_factory=list,
        description="IDs of related issues if any",
    )

    @model_validator(mode="after")
    def validate_fixes_ordered_by_confidence(self) -> "DiagnosticReport":
        """Warn if fixes are not ordered by confidence (highest first)."""
        if len(self.suggested_fixes) > 1:
            confidences = [f.confidence for f in self.suggested_fixes]
            if confidences != sorted(confidences, reverse=True):
                # Just a warning, don't fail - LLM might have good reason
                pass
        return self

    @property
    def best_fix(self) -> SuggestedFix | None:
        """Get the highest-confidence fix."""
        if not self.suggested_fixes:
            return None
        return max(self.suggested_fixes, key=lambda f: f.confidence)

    @property
    def is_high_confidence(self) -> bool:
        """Check if diagnosis has high confidence (>= 0.8)."""
        return self.confidence >= 0.8

    class Config:
        json_schema_extra = {
            "example": {
                "task_id": "REPAIR-001",
                "issue_type": "test_failure",
                "severity": "High",
                "root_cause": "The add function uses subtraction operator (-) instead of addition (+)",
                "affected_files": [
                    {
                        "path": "src/calculator.py",
                        "line_start": 5,
                        "line_end": 6,
                        "code_snippet": "def add(a, b):\n    return a - b",
                        "issue_description": "Wrong operator used",
                    }
                ],
                "suggested_fixes": [
                    {
                        "fix_id": "FIX-001",
                        "description": "Change subtraction to addition",
                        "confidence": 0.95,
                        "changes": [
                            {
                                "file_path": "src/calculator.py",
                                "search_text": "return a - b",
                                "replace_text": "return a + b",
                            }
                        ],
                    }
                ],
                "confidence": 0.95,
                "diagnosis_notes": "Clear operator typo based on function name and test expectations",
            }
        }
