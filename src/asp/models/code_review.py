"""
Pydantic models for Code Review Agent (FR-005).

This module defines the data structures for code quality review,
including issues, improvement suggestions, and review reports.

Author: ASP Development Team
Date: November 17, 2025
"""

from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator

from asp.utils.id_generation import (
    CODE_IMPROVEMENT_ID_PATTERN,
    CODE_ISSUE_ID_PATTERN,
    LEGACY_CODE_IMPROVEMENT_PATTERN,
    LEGACY_CODE_ISSUE_PATTERN,
    is_valid_hash_id,
)

# Combined patterns accept both legacy (CODE-ISSUE-001) and new (code-issue-a3f42bc) formats
# Need explicit anchors since Pydantic does search matching, not fullmatch
_CODE_ISSUE_COMBINED_PATTERN = (
    rf"^({CODE_ISSUE_ID_PATTERN[1:-1]}|{LEGACY_CODE_ISSUE_PATTERN[1:-1]})$"
)
_CODE_IMPROVEMENT_COMBINED_PATTERN = (
    rf"^({CODE_IMPROVEMENT_ID_PATTERN[1:-1]}|{LEGACY_CODE_IMPROVEMENT_PATTERN[1:-1]})$"
)


class CodeIssue(BaseModel):
    """
    Represents a code quality issue identified during code review.

    Issues are categorized by severity and linked to specific code locations.
    Supports phase-aware feedback for routing corrections to appropriate agents.
    """

    issue_id: str = Field(
        ...,
        description="Unique identifier for the issue (e.g., 'code-issue-a3f42bc' or legacy 'CODE-ISSUE-001')",
        pattern=_CODE_ISSUE_COMBINED_PATTERN,
    )
    category: Literal[
        "Security",
        "Code Quality",
        "Performance",
        "Standards",
        "Testing",
        "Maintainability",
        "Error Handling",
        "Data Integrity",
    ] = Field(..., description="Issue category")
    severity: Literal["Critical", "High", "Medium", "Low"] = Field(
        ...,
        description=(
            "Severity level:\n"
            "- Critical: Security vulnerabilities, data loss risks, system crashes\n"
            "- High: Performance bottlenecks, incorrect behavior, major tech debt\n"
            "- Medium: Suboptimal patterns, minor inconsistencies, code smell\n"
            "- Low: Style issues, documentation gaps, minor improvements"
        ),
    )
    description: str = Field(
        ...,
        min_length=20,
        description="Clear description of what is wrong",
    )
    evidence: str = Field(
        ...,
        min_length=10,
        description=(
            "Specific location in the code (file path, line number, function name)"
        ),
    )
    impact: str = Field(
        ...,
        min_length=20,
        description="Explanation of why this matters and potential consequences",
    )
    affected_phase: Literal["Planning", "Design", "Code", "Both"] = Field(
        default="Code",
        description=(
            "Phase where this issue was introduced:\n"
            "- Planning: Missing requirements, wrong decomposition, missing dependencies\n"
            "- Design: API design errors, data model issues, architectural problems\n"
            "- Code: Implementation bugs, security vulnerabilities, performance issues\n"
            "- Both: Issues affecting multiple phases"
        ),
    )

    # Code-specific fields
    file_path: str = Field(
        ...,
        min_length=1,
        description="File path where the issue occurs (e.g., 'src/api/auth.py')",
    )
    line_number: int | None = Field(
        default=None,
        ge=1,
        description="Line number where the issue occurs (if applicable)",
    )
    code_snippet: str | None = Field(
        default=None,
        description="Code snippet showing the problematic code",
    )

    # Traceability (optional)
    semantic_unit_id: str | None = Field(
        default=None,
        description="Semantic unit ID from planning (for traceability)",
    )
    component_id: str | None = Field(
        default=None,
        description="Component ID from design (for traceability)",
    )

    @field_validator("issue_id")
    @classmethod
    def validate_issue_id(cls, v: str) -> str:
        """Validate issue ID format (accepts both new hash and legacy formats)."""
        # Accept new hash-based format
        if is_valid_hash_id(v, prefix="code-issue"):
            return v
        # Accept legacy format
        if v.startswith("CODE-ISSUE-"):
            try:
                num = int(v.split("-")[2])
                if num < 1 or num > 999:
                    raise ValueError("Issue number must be between 001 and 999")
                return v
            except (IndexError, ValueError) as e:
                raise ValueError(f"Invalid legacy issue ID format: {e}") from e
        raise ValueError(
            "Issue ID must be 'code-issue-{7-char-hex}' or legacy 'CODE-ISSUE-XXX' format"
        )

    class Config:
        json_schema_extra = {
            "example": {
                "issue_id": "CODE-ISSUE-001",
                "category": "Security",
                "severity": "Critical",
                "description": "SQL injection vulnerability via raw string interpolation",
                "evidence": "src/repositories/user_repository.py:45",
                "impact": "Attacker can execute arbitrary SQL, extract database, modify data",
                "affected_phase": "Code",
                "file_path": "src/repositories/user_repository.py",
                "line_number": 45,
                "code_snippet": "query = f\"SELECT * FROM users WHERE username = '{username}'\"",
                "semantic_unit_id": "SU-002",
                "component_id": "COMP-003",
            }
        }


class CodeImprovementSuggestion(BaseModel):
    """
    Represents an actionable recommendation to improve code quality.

    Suggestions may be linked to specific issues or be proactive improvements.
    """

    suggestion_id: str = Field(
        ...,
        description="Unique identifier for the suggestion (e.g., 'code-improve-a3f42bc' or legacy 'CODE-IMPROVE-001')",
        pattern=_CODE_IMPROVEMENT_COMBINED_PATTERN,
    )
    related_issue_id: str | None = Field(
        None,
        description="Issue ID this suggestion addresses (if applicable)",
        pattern=_CODE_ISSUE_COMBINED_PATTERN,
    )
    category: Literal[
        "Security",
        "Code Quality",
        "Performance",
        "Standards",
        "Testing",
        "Maintainability",
        "Error Handling",
        "Data Integrity",
    ] = Field(..., description="Suggestion category")
    priority: Literal["High", "Medium", "Low"] = Field(
        ...,
        description=(
            "Implementation priority:\n"
            "- High: Addresses Critical/High severity issues, must implement\n"
            "- Medium: Addresses Medium severity issues or improves quality\n"
            "- Low: Nice-to-have improvements, not blocking"
        ),
    )
    description: str = Field(
        ...,
        min_length=30,
        description="Specific, actionable recommendation",
    )
    implementation_notes: str = Field(
        ...,
        min_length=20,
        description="How to implement this suggestion (specific steps, code patterns, tools)",
    )

    # Code-specific fields
    file_path: str | None = Field(
        default=None,
        description="File to modify (if applicable)",
    )
    suggested_code: str | None = Field(
        default=None,
        description="Code example showing the fix or improvement",
    )

    @field_validator("suggestion_id")
    @classmethod
    def validate_suggestion_id(cls, v: str) -> str:
        """Validate suggestion ID format (accepts both new hash and legacy formats)."""
        # Accept new hash-based format
        if is_valid_hash_id(v, prefix="code-improve"):
            return v
        # Accept legacy format
        if v.startswith("CODE-IMPROVE-"):
            try:
                num = int(v.split("-")[2])
                if num < 1 or num > 999:
                    raise ValueError("Suggestion number must be between 001 and 999")
                return v
            except (IndexError, ValueError) as e:
                raise ValueError(f"Invalid legacy suggestion ID format: {e}") from e
        raise ValueError(
            "Suggestion ID must be 'code-improve-{7-char-hex}' or legacy 'CODE-IMPROVE-XXX' format"
        )

    class Config:
        json_schema_extra = {
            "example": {
                "suggestion_id": "CODE-IMPROVE-001",
                "related_issue_id": "CODE-ISSUE-001",
                "category": "Security",
                "priority": "High",
                "description": "Use parameterized queries to prevent SQL injection",
                "implementation_notes": (
                    "Replace string interpolation with parameterized queries. "
                    "Use SQLAlchemy's text() or ORM methods with bound parameters."
                ),
                "file_path": "src/repositories/user_repository.py",
                "suggested_code": (
                    'query = text("SELECT * FROM users WHERE username = :username")\n'
                    'result = db.execute(query, {"username": username})'
                ),
            }
        }


class ChecklistItemReview(BaseModel):
    """
    Represents the review status of a single checklist item.

    Used to track verification of specific quality criteria.
    """

    item_id: str = Field(
        ...,
        description="Checklist item identifier (e.g., 'SEC-001', 'QUAL-005')",
    )
    item_description: str = Field(
        ...,
        min_length=10,
        description="What was checked",
    )
    status: Literal["Pass", "Fail", "Not Applicable", "Needs Review"] = Field(
        ...,
        description="Review status for this item",
    )
    notes: str | None = Field(
        default=None,
        description="Additional notes or findings",
    )

    class Config:
        json_schema_extra = {
            "example": {
                "item_id": "SEC-001",
                "item_description": "All SQL queries use parameterized statements",
                "status": "Fail",
                "notes": "Found 2 instances of string interpolation in user_repository.py",
            }
        }


class CodeReviewReport(BaseModel):
    """
    Complete code review report from all specialists.

    Contains all issues, suggestions, and review metadata.
    Supports phase-aware feedback with automatic issue grouping.
    """

    review_id: str = Field(
        ...,
        description="Unique review identifier (e.g., 'CODE-REVIEW-JWT-AUTH-001-20251117-143000')",
        pattern=r"^CODE-REVIEW-[A-Z0-9\-_]+-\d{8}-\d{6}$",
    )
    task_id: str = Field(
        ...,
        min_length=3,
        description="Task identifier being reviewed",
    )
    review_status: Literal["PASS", "FAIL", "CONDITIONAL_PASS"] = Field(
        ...,
        description=(
            "Overall review status:\n"
            "- PASS: No Critical/High issues, all quality gates passed\n"
            "- FAIL: Critical issues present OR ≥5 High issues OR any specialist FAIL\n"
            "- CONDITIONAL_PASS: High issues present but <5, all Critical resolved"
        ),
    )

    # Review results
    issues_found: list[CodeIssue] = Field(
        default_factory=list,
        description="All issues identified across all specialists",
    )
    improvement_suggestions: list[CodeImprovementSuggestion] = Field(
        default_factory=list,
        description="All improvement suggestions",
    )
    checklist_review: list[ChecklistItemReview] = Field(
        default_factory=list,
        description="Results of checklist verification",
    )

    # Phase-aware grouping (auto-populated via model_validator)
    planning_phase_issues: list[CodeIssue] = Field(
        default_factory=list,
        description="Issues attributed to Planning phase (auto-grouped)",
    )
    design_phase_issues: list[CodeIssue] = Field(
        default_factory=list,
        description="Issues attributed to Design phase (auto-grouped)",
    )
    code_phase_issues: list[CodeIssue] = Field(
        default_factory=list,
        description="Issues attributed to Code phase (auto-grouped)",
    )

    # Summary statistics
    total_issues: int = Field(
        default=0,
        ge=0,
        description="Total number of issues found",
    )
    critical_issues: int = Field(
        default=0,
        ge=0,
        description="Number of Critical severity issues",
    )
    high_issues: int = Field(
        default=0,
        ge=0,
        description="Number of High severity issues",
    )
    medium_issues: int = Field(
        default=0,
        ge=0,
        description="Number of Medium severity issues",
    )
    low_issues: int = Field(
        default=0,
        ge=0,
        description="Number of Low severity issues",
    )

    files_reviewed: int = Field(
        default=0,
        ge=0,
        description="Number of files reviewed",
    )
    total_lines_reviewed: int = Field(
        default=0,
        ge=0,
        description="Total lines of code reviewed",
    )

    # Specialist results
    security_review_passed: bool = Field(
        default=True,
        description="Security review passed (no Critical/High security issues)",
    )
    quality_review_passed: bool = Field(
        default=True,
        description="Code quality review passed",
    )
    performance_review_passed: bool = Field(
        default=True,
        description="Performance review passed",
    )
    standards_review_passed: bool = Field(
        default=True,
        description="Standards compliance review passed",
    )
    testing_review_passed: bool = Field(
        default=True,
        description="Testing review passed",
    )
    maintainability_review_passed: bool = Field(
        default=True,
        description="Maintainability review passed",
    )

    # Agent metadata
    agent_version: str = Field(
        default="1.0.0",
        description="Version of Code Review Agent",
    )
    review_timestamp: str = Field(
        ...,
        description="ISO 8601 timestamp of review completion",
    )
    review_duration_seconds: float | None = Field(
        default=None,
        ge=0,
        description="Duration of review in seconds",
    )

    @model_validator(mode="after")
    def group_issues_by_phase(self) -> "CodeReviewReport":
        """
        Automatically group issues by affected phase.

        This validator runs after model initialization and populates
        planning_phase_issues, design_phase_issues, and code_phase_issues
        based on the affected_phase field of each issue.
        """
        planning_issues = []
        design_issues = []
        code_issues = []

        for issue in self.issues_found:
            if issue.affected_phase == "Planning":
                planning_issues.append(issue)
            elif issue.affected_phase == "Design":
                design_issues.append(issue)
            elif issue.affected_phase == "Code":
                code_issues.append(issue)
            elif issue.affected_phase == "Both":
                # Issues affecting both phases go to both lists
                planning_issues.append(issue)
                design_issues.append(issue)

        self.planning_phase_issues = planning_issues
        self.design_phase_issues = design_issues
        self.code_phase_issues = code_issues

        return self

    @model_validator(mode="after")
    def calculate_statistics(self) -> "CodeReviewReport":
        """
        Calculate summary statistics from issues.

        Automatically computes total_issues, critical_issues, high_issues, etc.
        based on the issues_found list.
        """
        self.total_issues = len(self.issues_found)
        self.critical_issues = sum(
            1 for issue in self.issues_found if issue.severity == "Critical"
        )
        self.high_issues = sum(
            1 for issue in self.issues_found if issue.severity == "High"
        )
        self.medium_issues = sum(
            1 for issue in self.issues_found if issue.severity == "Medium"
        )
        self.low_issues = sum(
            1 for issue in self.issues_found if issue.severity == "Low"
        )

        return self

    class Config:
        json_schema_extra = {
            "example": {
                "review_id": "CODE-REVIEW-JWT-AUTH-001-20251117-143000",
                "task_id": "JWT-AUTH-001",
                "review_status": "FAIL",
                "issues_found": [
                    {
                        "issue_id": "CODE-ISSUE-001",
                        "category": "Security",
                        "severity": "Critical",
                        "description": "SQL injection vulnerability",
                        "evidence": "src/repositories/user_repository.py:45",
                        "impact": "Attacker can execute arbitrary SQL",
                        "affected_phase": "Code",
                        "file_path": "src/repositories/user_repository.py",
                        "line_number": 45,
                    }
                ],
                "improvement_suggestions": [
                    {
                        "suggestion_id": "CODE-IMPROVE-001",
                        "related_issue_id": "CODE-ISSUE-001",
                        "category": "Security",
                        "priority": "High",
                        "description": "Use parameterized queries",
                        "implementation_notes": "Replace with SQLAlchemy text()",
                    }
                ],
                "checklist_review": [],
                "planning_phase_issues": [],
                "design_phase_issues": [],
                "code_phase_issues": [],
                "total_issues": 5,
                "critical_issues": 2,
                "high_issues": 3,
                "medium_issues": 0,
                "low_issues": 0,
                "files_reviewed": 8,
                "total_lines_reviewed": 450,
                "security_review_passed": False,
                "quality_review_passed": True,
                "performance_review_passed": False,
                "standards_review_passed": True,
                "testing_review_passed": True,
                "maintainability_review_passed": True,
                "agent_version": "1.0.0",
                "review_timestamp": "2025-11-17T14:30:00Z",
                "review_duration_seconds": 35.5,
            }
        }
