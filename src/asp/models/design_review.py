"""
Pydantic models for Design Review Agent (FR-003).

This module defines the data structures for design quality review,
including issues, improvement suggestions, and review reports.
"""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator


class DesignIssue(BaseModel):
    """
    Represents a design quality issue identified during review.

    Issues are categorized by severity and linked to specific design elements.
    """

    issue_id: str = Field(
        ...,
        description="Unique identifier for the issue (e.g., 'ISSUE-001')",
        pattern=r"^ISSUE-\d{3}$",
    )
    category: Literal[
        "Security",
        "Performance",
        "Data Integrity",
        "Error Handling",
        "Architecture",
        "Maintainability",
        "API Design",
        "Scalability",
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
            "Specific location in the design (component name, API endpoint, "
            "schema table, etc.)"
        ),
    )
    impact: str = Field(
        ...,
        min_length=20,
        description="Explanation of why this matters and potential consequences",
    )
    affected_phase: Literal["Planning", "Design", "Both"] = Field(
        default="Design",
        description=(
            "Phase where this issue was introduced:\n"
            "- Planning: Missing requirements, wrong decomposition, missing dependencies\n"
            "- Design: API design errors, data model issues, architectural problems\n"
            "- Both: Issues affecting both planning and design"
        ),
    )

    @field_validator("issue_id")
    @classmethod
    def validate_issue_id(cls, v: str) -> str:
        """Validate issue ID format."""
        if not v.startswith("ISSUE-"):
            raise ValueError("Issue ID must start with 'ISSUE-'")
        try:
            num = int(v.split("-")[1])
            if num < 1 or num > 999:
                raise ValueError("Issue number must be between 001 and 999")
        except (IndexError, ValueError) as e:
            raise ValueError(f"Invalid issue ID format: {e}") from e
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "issue_id": "ISSUE-001",
                "category": "Security",
                "severity": "Critical",
                "description": "Password stored in plaintext without hashing or encryption",
                "evidence": "users table, password column (VARCHAR) with no hashing component",
                "impact": "User credentials vulnerable to breach; violates security best practices and compliance requirements",
                "affected_phase": "Design",
            }
        }


class ImprovementSuggestion(BaseModel):
    """
    Represents an actionable recommendation to improve the design.

    Suggestions may be linked to specific issues or be proactive improvements.
    """

    suggestion_id: str = Field(
        ...,
        description="Unique identifier for the suggestion (e.g., 'IMPROVE-001')",
        pattern=r"^IMPROVE-\d{3}$",
    )
    related_issue_id: str | None = Field(
        None,
        description="Issue ID this suggestion addresses (if applicable)",
        pattern=r"^ISSUE-\d{3}$",
    )
    category: Literal[
        "Security",
        "Performance",
        "Data Integrity",
        "Error Handling",
        "Architecture",
        "Maintainability",
        "API Design",
        "Scalability",
    ] = Field(..., description="Suggestion category")
    priority: Literal["Critical", "High", "Medium", "Low"] = Field(
        ...,
        description=(
            "Implementation priority:\n"
            "- Critical: Addresses Critical severity issues, must implement immediately\n"
            "- High: Addresses High severity issues, must implement\n"
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

    @field_validator("suggestion_id")
    @classmethod
    def validate_suggestion_id(cls, v: str) -> str:
        """Validate suggestion ID format."""
        if not v.startswith("IMPROVE-"):
            raise ValueError("Suggestion ID must start with 'IMPROVE-'")
        try:
            num = int(v.split("-")[1])
            if num < 1 or num > 999:
                raise ValueError("Suggestion number must be between 001 and 999")
        except (IndexError, ValueError) as e:
            raise ValueError(f"Invalid suggestion ID format: {e}") from e
        return v

    @field_validator("related_issue_id")
    @classmethod
    def validate_related_issue_id(cls, v: str | None) -> str | None:
        """Validate related issue ID format."""
        if v is not None and not v.startswith("ISSUE-"):
            raise ValueError("Related issue ID must start with 'ISSUE-'")
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "suggestion_id": "IMPROVE-001",
                "related_issue_id": "ISSUE-001",
                "category": "Security",
                "priority": "Critical",
                "description": "Implement bcrypt password hashing with salt in PasswordHashingService component",
                "implementation_notes": "1. Add bcrypt dependency (bcrypt>=4.1.0). 2. Update PasswordHashingService to use bcrypt.hashpw() with auto-generated salt. 3. Store hashed password (60-char CHAR field) in database. 4. Use bcrypt.checkpw() for verification.",
            }
        }


class ChecklistItemReview(BaseModel):
    """
    Review status for a single design review checklist item.

    Links back to the original checklist item from the design specification.
    """

    checklist_item_id: str = Field(
        ...,
        description="ID of the checklist item from DesignSpecification",
    )
    category: str = Field(
        ...,
        min_length=3,
        description="Checklist category (Architecture, Security, etc.)",
    )
    description: str = Field(
        ...,
        min_length=10,
        description="Description of the checklist item",
    )
    status: Literal["Pass", "Fail", "Warning"] = Field(
        ...,
        description=(
            "Review status:\n"
            "- Pass: Item satisfied, no issues\n"
            "- Fail: Item not satisfied, Critical/High issue\n"
            "- Warning: Item partially satisfied, Medium/Low issue"
        ),
    )
    notes: str = Field(
        ...,
        min_length=20,
        description="Reviewer's assessment notes",
    )
    related_issues: list[str] = Field(
        default_factory=list,
        description="List of issue IDs related to this checklist item",
    )

    @field_validator("related_issues")
    @classmethod
    def validate_related_issues(cls, v: list[str]) -> list[str]:
        """Validate related issue IDs format."""
        for issue_id in v:
            if not issue_id.startswith("ISSUE-"):
                raise ValueError(f"Invalid issue ID format: {issue_id}")
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "checklist_item_id": "CHECK-001",
                "category": "Security",
                "description": "Sensitive data (passwords, tokens) must be hashed or encrypted",
                "status": "Fail",
                "notes": "Password field in users table is stored as plaintext VARCHAR without hashing",
                "related_issues": ["ISSUE-001"],
            }
        }


class DesignReviewReport(BaseModel):
    """
    Complete design review report with assessment, issues, and suggestions.

    This is the main output of the Design Review Agent.
    """

    task_id: str = Field(
        ...,
        min_length=3,
        description="Task identifier from the original requirement",
    )
    review_id: str = Field(
        ...,
        description="Unique review identifier (e.g., 'REVIEW-001-20251114-123456')",
        pattern=r"^REVIEW-[A-Z0-9]+-\d{8}-\d{6}$",
    )
    timestamp: datetime = Field(
        default_factory=datetime.now,
        description="Review completion timestamp",
    )
    overall_assessment: Literal["PASS", "FAIL", "NEEDS_IMPROVEMENT"] = Field(
        ...,
        description=(
            "Overall design quality assessment:\n"
            "- PASS: No Critical/High issues, design ready for implementation\n"
            "- FAIL: Critical or High severity issues present, must revise\n"
            "- NEEDS_IMPROVEMENT: Only Medium/Low issues, improvements recommended"
        ),
    )

    # Automated validation results
    automated_checks: dict[str, bool] = Field(
        ...,
        description=(
            "Results from automated validation checks "
            "(e.g., {'semantic_coverage': True, 'no_circular_deps': True})"
        ),
    )

    # LLM review results
    issues_found: list[DesignIssue] = Field(
        default_factory=list,
        description="List of design quality issues identified",
    )
    improvement_suggestions: list[ImprovementSuggestion] = Field(
        default_factory=list,
        description="List of actionable improvement recommendations",
    )
    checklist_review: list[ChecklistItemReview] = Field(
        default_factory=list,
        description="Review status for each design checklist item",
    )

    # Phase-specific issue groupings (NEW: Phase-aware feedback)
    planning_phase_issues: list[DesignIssue] = Field(
        default_factory=list,
        description="Issues that originated in the Planning phase",
    )
    design_phase_issues: list[DesignIssue] = Field(
        default_factory=list,
        description="Issues that originated in the Design phase",
    )
    multi_phase_issues: list[DesignIssue] = Field(
        default_factory=list,
        description="Issues affecting both Planning and Design phases",
    )

    # Summary counts
    critical_issue_count: int = Field(
        default=0,
        ge=0,
        description="Number of Critical severity issues",
    )
    high_issue_count: int = Field(
        default=0,
        ge=0,
        description="Number of High severity issues",
    )
    medium_issue_count: int = Field(
        default=0,
        ge=0,
        description="Number of Medium severity issues",
    )
    low_issue_count: int = Field(
        default=0,
        ge=0,
        description="Number of Low severity issues",
    )

    # Metadata
    reviewer_agent: str = Field(
        default="DesignReviewAgent",
        description="Agent that performed the review",
    )
    agent_version: str = Field(
        default="1.0.0",
        description="Version of the review agent",
    )
    review_duration_ms: float = Field(
        default=0.0,
        ge=0,
        description="Review execution time in milliseconds",
    )

    @model_validator(mode="after")
    def validate_issue_counts(self) -> "DesignReviewReport":
        """Validate that issue counts match actual issues found."""
        critical_count = sum(
            1 for issue in self.issues_found if issue.severity == "Critical"
        )
        high_count = sum(1 for issue in self.issues_found if issue.severity == "High")
        medium_count = sum(
            1 for issue in self.issues_found if issue.severity == "Medium"
        )
        low_count = sum(1 for issue in self.issues_found if issue.severity == "Low")

        if self.critical_issue_count != critical_count:
            raise ValueError(
                f"Critical issue count mismatch: declared {self.critical_issue_count}, "
                f"found {critical_count}"
            )
        if self.high_issue_count != high_count:
            raise ValueError(
                f"High issue count mismatch: declared {self.high_issue_count}, "
                f"found {high_count}"
            )
        if self.medium_issue_count != medium_count:
            raise ValueError(
                f"Medium issue count mismatch: declared {self.medium_issue_count}, "
                f"found {medium_count}"
            )
        if self.low_issue_count != low_count:
            raise ValueError(
                f"Low issue count mismatch: declared {self.low_issue_count}, "
                f"found {low_count}"
            )

        return self

    @model_validator(mode="after")
    def validate_overall_assessment(self) -> "DesignReviewReport":
        """Validate that overall assessment matches issue severity."""
        has_critical_or_high = (
            self.critical_issue_count > 0 or self.high_issue_count > 0
        )
        has_medium_or_low = self.medium_issue_count > 0 or self.low_issue_count > 0

        if has_critical_or_high and self.overall_assessment != "FAIL":
            raise ValueError(
                "Overall assessment must be FAIL when Critical or High issues present"
            )

        if (
            not has_critical_or_high
            and has_medium_or_low
            and self.overall_assessment == "PASS"
        ):
            # This is a warning, not an error - allow PASS with Medium/Low issues
            # if reviewer deems them non-blocking
            pass

        return self

    @model_validator(mode="after")
    def validate_checklist_review(self) -> "DesignReviewReport":
        """Validate checklist review completeness."""
        if len(self.checklist_review) == 0:
            raise ValueError("Checklist review must contain at least 1 item")

        # Validate that all failed checklist items have corresponding issues
        failed_items = [item for item in self.checklist_review if item.status == "Fail"]
        for item in failed_items:
            if len(item.related_issues) == 0:
                raise ValueError(
                    f"Failed checklist item {item.checklist_item_id} must have "
                    f"related issues"
                )

        return self

    @model_validator(mode="after")
    def validate_issue_suggestion_links(self) -> "DesignReviewReport":
        """Validate that related_issue_id references exist."""
        issue_ids = {issue.issue_id for issue in self.issues_found}

        for suggestion in self.improvement_suggestions:
            if (
                suggestion.related_issue_id
                and suggestion.related_issue_id not in issue_ids
            ):
                raise ValueError(
                    f"Suggestion {suggestion.suggestion_id} references non-existent "
                    f"issue {suggestion.related_issue_id}"
                )

        return self

    @model_validator(mode="after")
    def populate_phase_groups(self) -> "DesignReviewReport":
        """Automatically group issues by affected_phase."""
        self.planning_phase_issues = [
            issue
            for issue in self.issues_found
            if issue.affected_phase in ["Planning", "Both"]
        ]
        self.design_phase_issues = [
            issue
            for issue in self.issues_found
            if issue.affected_phase in ["Design", "Both"]
        ]
        self.multi_phase_issues = [
            issue for issue in self.issues_found if issue.affected_phase == "Both"
        ]
        return self

    class Config:
        json_schema_extra = {
            "example": {
                "task_id": "TASK-JWT-AUTH",
                "review_id": "REVIEW-TASK-JWT-AUTH-20251114-120000",
                "timestamp": "2025-11-14T12:00:00",
                "overall_assessment": "FAIL",
                "automated_checks": {
                    "semantic_coverage": True,
                    "no_circular_deps": True,
                    "checklist_complete": True,
                    "schema_api_consistency": True,
                },
                "issues_found": [
                    {
                        "issue_id": "ISSUE-001",
                        "category": "Security",
                        "severity": "Critical",
                        "description": "Password stored in plaintext without hashing",
                        "evidence": "users table, password column (VARCHAR)",
                        "impact": "User credentials vulnerable to breach",
                    }
                ],
                "improvement_suggestions": [
                    {
                        "suggestion_id": "IMPROVE-001",
                        "related_issue_id": "ISSUE-001",
                        "category": "Security",
                        "priority": "High",
                        "description": "Implement bcrypt password hashing",
                        "implementation_notes": "Use bcrypt.hashpw() with auto-generated salt",
                    }
                ],
                "checklist_review": [
                    {
                        "checklist_item_id": "CHECK-001",
                        "category": "Security",
                        "description": "Sensitive data must be hashed or encrypted",
                        "status": "Fail",
                        "notes": "Password field stored as plaintext",
                        "related_issues": ["ISSUE-001"],
                    }
                ],
                "critical_issue_count": 1,
                "high_issue_count": 0,
                "medium_issue_count": 0,
                "low_issue_count": 0,
                "reviewer_agent": "DesignReviewAgent",
                "agent_version": "1.0.0",
                "review_duration_ms": 5432.1,
            }
        }
