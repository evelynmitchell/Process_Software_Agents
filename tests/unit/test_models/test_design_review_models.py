"""
Unit tests for Design Review models with phase-aware feedback.

Tests the DesignIssue and DesignReviewReport models with the affected_phase
field and automatic phase grouping functionality added for error correction.

Author: ASP Development Team
Date: November 17, 2025
"""

import pytest
from pydantic import ValidationError

from asp.models.design_review import (
    DesignIssue,
    DesignReviewReport,
    ChecklistItemReview,
)


def create_minimal_checklist_item(
    item_id="CHECK-001", status="Pass", related_issues=None
):
    """Helper to create a minimal checklist item for tests."""
    # If status is Fail, must have related issues
    if status == "Fail" and not related_issues:
        related_issues = ["ISSUE-001"]  # Default to first issue
    elif not related_issues:
        related_issues = []

    return ChecklistItemReview(
        checklist_item_id=item_id,
        category="Security",
        description="Test checklist item for validation",
        status=status,
        notes="Test notes for checklist item validation requirements",
        related_issues=related_issues,
    )


def count_issues_by_severity(issues):
    """Helper to count issues by severity."""
    counts = {"Critical": 0, "High": 0, "Medium": 0, "Low": 0}
    for issue in issues:
        counts[issue.severity] += 1
    return counts


class TestDesignIssueAffectedPhase:
    """Tests for DesignIssue.affected_phase field."""

    def test_affected_phase_defaults_to_design(self):
        """Test that affected_phase defaults to 'Design' when not specified."""
        issue = DesignIssue(
            issue_id="ISSUE-001",
            category="Security",
            severity="Critical",
            description="This is a test issue for unit testing purposes only",
            evidence="Test evidence location in the design specification",
            impact="This has a significant test impact on system behavior",
        )

        assert issue.affected_phase == "Design"

    def test_affected_phase_planning(self):
        """Test that affected_phase can be set to 'Planning'."""
        issue = DesignIssue(
            issue_id="ISSUE-001",
            category="Architecture",
            severity="High",
            description="Missing semantic unit for authentication and authorization",
            evidence="No authentication unit found in the project plan semantic units",
            impact="Security features are not planned, requiring replanning phase",
            affected_phase="Planning",
        )

        assert issue.affected_phase == "Planning"

    def test_affected_phase_design(self):
        """Test that affected_phase can be explicitly set to 'Design'."""
        issue = DesignIssue(
            issue_id="ISSUE-001",
            category="Security",
            severity="Critical",
            description="User passwords are stored in plaintext without any hashing",
            evidence="users table has password column storing raw passwords directly",
            impact="Severe security vulnerability exposing user credentials in breaches",
            affected_phase="Design",
        )

        assert issue.affected_phase == "Design"

    def test_affected_phase_both(self):
        """Test that affected_phase can be set to 'Both'."""
        issue = DesignIssue(
            issue_id="ISSUE-001",
            category="Architecture",
            severity="High",
            description="Authentication requirements missing from both planning and design phases",
            evidence="No auth semantic unit in plan and no auth endpoints in design API",
            impact="Critical security functionality absent requiring both plan and design revision",
            affected_phase="Both",
        )

        assert issue.affected_phase == "Both"

    def test_affected_phase_invalid_value_rejected(self):
        """Test that invalid affected_phase values are rejected."""
        with pytest.raises(ValidationError) as exc_info:
            DesignIssue(
                issue_id="ISSUE-001",
                category="Security",
                severity="Critical",
                description="This is a test issue with an invalid affected phase value",
                evidence="Test evidence location in design specification documentation",
                impact="This would have a significant test impact on the system behavior",
                affected_phase="InvalidPhase",  # Invalid value
            )

        # Should have at least one error about affected_phase
        errors = exc_info.value.errors()
        assert any("affected_phase" in str(err.get("loc", "")) for err in errors)


class TestDesignReviewReportPhaseGrouping:
    """Tests for DesignReviewReport phase-specific issue grouping."""

    def test_empty_report_has_empty_phase_groups(self):
        """Test that a report with no issues has empty phase groups."""
        report = DesignReviewReport(
            task_id="TEST-001",
            review_id="REVIEW-TEST-20251117-120000",
            overall_assessment="PASS",
            automated_checks={"semantic_coverage": True},
            checklist_review=[create_minimal_checklist_item()],
        )

        assert report.planning_phase_issues == []
        assert report.design_phase_issues == []
        assert report.multi_phase_issues == []

    def test_planning_phase_issues_grouped_correctly(self):
        """Test that issues with affected_phase='Planning' are grouped."""
        planning_issue = DesignIssue(
            issue_id="ISSUE-001",
            category="Architecture",
            severity="High",
            description="Missing semantic unit for user authentication functionality",
            evidence="Project plan has no authentication semantic unit in decomposition",
            impact="Authentication feature not planned, requires replanning before implementation",
            affected_phase="Planning",
        )

        counts = count_issues_by_severity([planning_issue])
        report = DesignReviewReport(
            task_id="TEST-001",
            review_id="REVIEW-TEST-20251117-120001",
            overall_assessment="FAIL",
            automated_checks={"semantic_coverage": False},
            issues_found=[planning_issue],
            high_issue_count=counts["High"],
            checklist_review=[create_minimal_checklist_item(status="Fail")],
        )

        assert len(report.planning_phase_issues) == 1
        assert report.planning_phase_issues[0] == planning_issue
        assert len(report.design_phase_issues) == 0
        assert len(report.multi_phase_issues) == 0

    def test_design_phase_issues_grouped_correctly(self):
        """Test that issues with affected_phase='Design' are grouped."""
        design_issue = DesignIssue(
            issue_id="ISSUE-001",
            category="Security",
            severity="Critical",
            description="User passwords stored in plaintext without hashing or encryption",
            evidence="users table password column stores raw password values directly",
            impact="Critical security vulnerability exposing user credentials in database breaches",
            affected_phase="Design",
        )

        counts = count_issues_by_severity([design_issue])
        report = DesignReviewReport(
            task_id="TEST-001",
            review_id="REVIEW-TEST-20251117-120002",
            overall_assessment="FAIL",
            automated_checks={"semantic_coverage": True},
            issues_found=[design_issue],
            critical_issue_count=counts["Critical"],
            checklist_review=[create_minimal_checklist_item(status="Fail")],
        )

        assert len(report.design_phase_issues) == 1
        assert report.design_phase_issues[0] == design_issue
        assert len(report.planning_phase_issues) == 0
        assert len(report.multi_phase_issues) == 0

    def test_both_phase_issues_grouped_in_both_lists(self):
        """Test that issues with affected_phase='Both' appear in both groups."""
        both_issue = DesignIssue(
            issue_id="ISSUE-001",
            category="Architecture",
            severity="High",
            description="Validation requirements missing from planning and design specifications",
            evidence="No validation semantic unit in plan and no validation in API design",
            impact="Critical data quality functionality missing from both planning and design phases",
            affected_phase="Both",
        )

        counts = count_issues_by_severity([both_issue])
        report = DesignReviewReport(
            task_id="TEST-001",
            review_id="REVIEW-TEST-20251117-120003",
            overall_assessment="FAIL",
            automated_checks={"semantic_coverage": False},
            issues_found=[both_issue],
            high_issue_count=counts["High"],
            checklist_review=[create_minimal_checklist_item(status="Fail")],
        )

        # Issue with affected_phase='Both' should appear in both groups
        assert len(report.planning_phase_issues) == 1
        assert report.planning_phase_issues[0] == both_issue
        assert len(report.design_phase_issues) == 1
        assert report.design_phase_issues[0] == both_issue
        # And in the multi_phase_issues list
        assert len(report.multi_phase_issues) == 1
        assert report.multi_phase_issues[0] == both_issue

    def test_mixed_phases_grouped_correctly(self):
        """Test that issues with mixed phases are grouped correctly."""
        planning_issue = DesignIssue(
            issue_id="ISSUE-001",
            category="Architecture",
            severity="High",
            description="Missing semantic unit for authentication in project plan decomposition",
            evidence="Project plan semantic units do not include authentication component",
            impact="Authentication not planned requiring replanning phase before implementation",
            affected_phase="Planning",
        )

        design_issue1 = DesignIssue(
            issue_id="ISSUE-002",
            category="Security",
            severity="Critical",
            description="Passwords stored in plaintext without any hashing or encryption",
            evidence="users table password column stores raw passwords without hashing",
            impact="Severe security vulnerability exposing credentials in database breaches",
            affected_phase="Design",
        )

        design_issue2 = DesignIssue(
            issue_id="ISSUE-003",
            category="Data Integrity",
            severity="High",
            description="Missing primary key constraint on users table in database schema",
            evidence="users table id column not defined as PRIMARY KEY in schema definition",
            impact="Duplicate user records possible causing data integrity violations",
            affected_phase="Design",
        )

        both_issue = DesignIssue(
            issue_id="ISSUE-004",
            category="Architecture",
            severity="Medium",
            description="Input validation missing from both planning and design specifications",
            evidence="No validation semantic unit in plan and no validation in API contracts",
            impact="Data quality issues affecting both planning and design requiring revision",
            affected_phase="Both",
        )

        issues = [planning_issue, design_issue1, design_issue2, both_issue]
        counts = count_issues_by_severity(issues)
        report = DesignReviewReport(
            task_id="TEST-001",
            review_id="REVIEW-TEST-20251117-120004",
            overall_assessment="FAIL",
            automated_checks={"semantic_coverage": False},
            issues_found=issues,
            critical_issue_count=counts["Critical"],
            high_issue_count=counts["High"],
            medium_issue_count=counts["Medium"],
            checklist_review=[create_minimal_checklist_item(status="Fail")],
        )

        # Planning phase issues should include Planning + Both
        assert len(report.planning_phase_issues) == 2
        assert planning_issue in report.planning_phase_issues
        assert both_issue in report.planning_phase_issues

        # Design phase issues should include Design + Both
        assert len(report.design_phase_issues) == 3
        assert design_issue1 in report.design_phase_issues
        assert design_issue2 in report.design_phase_issues
        assert both_issue in report.design_phase_issues

        # Multi-phase issues should only include Both
        assert len(report.multi_phase_issues) == 1
        assert both_issue in report.multi_phase_issues

    def test_default_affected_phase_issues_in_design_group(self):
        """Test that issues without explicit affected_phase are in Design group."""
        # Create issue without specifying affected_phase (should default to Design)
        issue = DesignIssue(
            issue_id="ISSUE-001",
            category="Performance",
            severity="Medium",
            description="Missing database index on frequently queried email column in users table",
            evidence="users table email column has no index but is used in WHERE clauses frequently",
            impact="Slow query performance degrading user authentication and lookup operations",
        )

        counts = count_issues_by_severity([issue])
        report = DesignReviewReport(
            task_id="TEST-001",
            review_id="REVIEW-TEST-20251117-120007",
            overall_assessment="NEEDS_IMPROVEMENT",
            automated_checks={"semantic_coverage": True},
            issues_found=[issue],
            medium_issue_count=counts["Medium"],
            checklist_review=[create_minimal_checklist_item(status="Warning")],
        )

        # Should be in design_phase_issues because it defaults to "Design"
        assert len(report.design_phase_issues) == 1
        assert len(report.planning_phase_issues) == 0
        assert len(report.multi_phase_issues) == 0
