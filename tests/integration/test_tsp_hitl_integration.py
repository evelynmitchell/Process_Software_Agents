"""
Integration tests for TSP Orchestrator with HITL Approval Services.

Tests the integration between TSP Orchestrator and various approval services
(LocalPRApprovalService, etc.) to ensure quality gate overrides work correctly.

These are integration tests that validate the approval workflow without requiring
full E2E pipeline execution or API calls.
"""

from datetime import datetime
from unittest.mock import Mock

from asp.approval.base import (
    ApprovalRequest,
    ApprovalResponse,
    ApprovalService,
    ReviewDecision,
)
from asp.models.code_review import CodeIssue, CodeReviewReport
from asp.models.design_review import (
    ChecklistItemReview,
    DesignIssue,
    DesignReviewReport,
)
from asp.orchestrators.tsp_orchestrator import TSPOrchestrator


class TestTSPHITLIntegration:
    """Integration tests for TSP Orchestrator with HITL approval services."""

    @staticmethod
    def create_design_issue(issue_num: int, severity: str = "Critical") -> DesignIssue:
        """Helper to create a design issue for testing."""
        return DesignIssue(
            issue_id=f"ISSUE-{issue_num:03d}",
            category="Security",
            severity=severity,
            description="Test issue description that is long enough to pass validation",
            evidence="Test component evidence location",
            impact="Test impact explanation that is long enough to pass validation",
        )

    @staticmethod
    def create_checklist_item() -> ChecklistItemReview:
        """Helper to create a checklist review item for testing."""
        return ChecklistItemReview(
            checklist_item_id="CHECK-001",
            category="Security",
            description="Test checklist item",
            status="Fail",
            notes="Test checklist notes for validation purposes",
            related_issues=["ISSUE-001"],  # Link to first issue
        )

    @staticmethod
    def create_code_issue(issue_num: int, severity: str = "Critical") -> CodeIssue:
        """Helper to create a code issue for testing."""
        return CodeIssue(
            issue_id=f"CODE-ISSUE-{issue_num:03d}",
            category="Security",
            severity=severity,
            description="Test issue description that is long enough to pass validation",
            file_path="/test/path/file.py",
            line_number=10,
            evidence="Test code evidence",
            impact="Test impact explanation that is long enough to pass validation",
        )

    def test_approval_service_called_on_design_review_failure(self):
        """Test that ApprovalService is invoked when design review fails."""
        # Create mock approval service
        mock_approval_service = Mock(spec=ApprovalService)
        mock_approval_service.request_approval.return_value = ApprovalResponse(
            decision=ReviewDecision.APPROVED,
            reviewer="test-reviewer",
            timestamp=datetime.now().isoformat(),
            justification="Approved for testing purposes",
            review_branch="review/test-task-design",
            merge_commit="abc123",
        )

        # Create orchestrator with approval service
        orchestrator = TSPOrchestrator(approval_service=mock_approval_service)

        # Create failing design review report
        critical_issues = [
            self.create_design_issue(1, "Critical"),
            self.create_design_issue(2, "Critical"),
        ]
        high_issues = [
            self.create_design_issue(3, "High"),
            self.create_design_issue(4, "High"),
            self.create_design_issue(5, "High"),
        ]
        medium_issues = [self.create_design_issue(6, "Medium")]

        failing_review = DesignReviewReport(
            task_id="TEST-001",
            review_id="REVIEW-TEST001-20251125-100000",
            overall_assessment="FAIL",
            critical_issue_count=2,
            high_issue_count=3,
            medium_issue_count=1,
            low_issue_count=0,
            automated_checks={"semantic_coverage": True},
            issues_found=critical_issues + high_issues + medium_issues,
            checklist_review=[self.create_checklist_item()],
            review_summary="Critical issues found",
            timestamp=datetime.now(),
        )

        # Call _request_approval helper
        approved = orchestrator._request_approval(
            task_id="TEST-001",
            gate_type="design_review",
            gate_name="DesignReview",
            report=failing_review,
            hitl_approver=None,
        )

        # Verify approval service was called
        assert approved is True
        mock_approval_service.request_approval.assert_called_once()

        # Verify request parameters
        call_args = mock_approval_service.request_approval.call_args
        request = call_args[0][0]
        assert isinstance(request, ApprovalRequest)
        assert request.task_id == "TEST-001"
        assert request.gate_type == "design_review"
        assert "critical_issue_count" in request.quality_report

    def test_approval_service_called_on_code_review_failure(self):
        """Test that ApprovalService is invoked when code review fails."""
        # Create mock approval service
        mock_approval_service = Mock(spec=ApprovalService)
        mock_approval_service.request_approval.return_value = ApprovalResponse(
            decision=ReviewDecision.REJECTED,
            reviewer="test-reviewer",
            timestamp=datetime.now().isoformat(),
            justification="Too many critical issues to approve",
        )

        # Create orchestrator with approval service
        orchestrator = TSPOrchestrator(approval_service=mock_approval_service)

        # Create failing code review report
        failing_review = CodeReviewReport(
            task_id="TEST-001",
            review_id="CODE-REVIEW-TEST-001-20251125-100000",
            review_status="FAIL",
            critical_issues=5,
            high_issues=10,
            medium_issues=3,
            low_issues=2,
            issues_found=[],
            review_summary="Multiple critical security issues",
            review_timestamp=datetime.now().isoformat(),
        )

        # Call _request_approval helper
        approved = orchestrator._request_approval(
            task_id="TEST-001",
            gate_type="code_review",
            gate_name="CodeReview",
            report=failing_review,
            hitl_approver=None,
        )

        # Verify approval was rejected
        assert approved is False
        mock_approval_service.request_approval.assert_called_once()

    def test_approval_service_takes_precedence_over_callable(self):
        """Test that ApprovalService takes precedence over legacy callable."""
        # Create mock approval service
        mock_approval_service = Mock(spec=ApprovalService)
        mock_approval_service.request_approval.return_value = ApprovalResponse(
            decision=ReviewDecision.APPROVED,
            reviewer="approval-service",
            timestamp=datetime.now().isoformat(),
            justification="Approved via ApprovalService",
        )

        # Create mock callable that should NOT be called
        mock_callable = Mock(return_value=True)

        # Create orchestrator with BOTH approval service and callable
        orchestrator = TSPOrchestrator(approval_service=mock_approval_service)

        # Create failing review
        failing_review = DesignReviewReport(
            task_id="TEST-001",
            review_id="REVIEW-TEST001-20251125-100000",
            overall_assessment="FAIL",
            critical_issue_count=1,
            high_issue_count=0,
            medium_issue_count=0,
            low_issue_count=0,
            automated_checks={"semantic_coverage": True},
            issues_found=[self.create_design_issue(1, "Critical")],
            checklist_review=[self.create_checklist_item()],
            review_summary="Critical issue found",
            timestamp=datetime.now(),
        )

        # Call _request_approval with both service and callable
        approved = orchestrator._request_approval(
            task_id="TEST-001",
            gate_type="design_review",
            gate_name="DesignReview",
            report=failing_review,
            hitl_approver=mock_callable,
        )

        # Verify approval service was called
        assert approved is True
        mock_approval_service.request_approval.assert_called_once()

        # Verify callable was NOT called (service takes precedence)
        mock_callable.assert_not_called()

    def test_legacy_callable_fallback_when_no_service(self):
        """Test that legacy callable is used when no ApprovalService configured."""
        # Create mock callable
        mock_callable = Mock(return_value=True)

        # Create orchestrator WITHOUT approval service
        orchestrator = TSPOrchestrator(approval_service=None)

        # Create failing review
        failing_review = CodeReviewReport(
            task_id="TEST-001",
            review_id="CODE-REVIEW-TEST-001-20251125-100000",
            review_status="FAIL",
            critical_issues=1,
            high_issues=2,
            medium_issues=0,
            low_issues=0,
            issues_found=[],
            review_summary="Critical issues",
            review_timestamp=datetime.now().isoformat(),
        )

        # Call _request_approval with callable only
        approved = orchestrator._request_approval(
            task_id="TEST-001",
            gate_type="code_review",
            gate_name="CodeReview",
            report=failing_review,
            hitl_approver=mock_callable,
        )

        # Verify callable was called
        assert approved is True
        mock_callable.assert_called_once_with(
            gate_name="CodeReview",
            report=failing_review.model_dump(),
        )

    def test_no_approval_when_neither_service_nor_callable(self):
        """Test that approval is denied when no approval mechanism is available."""
        # Create orchestrator without approval service
        orchestrator = TSPOrchestrator(approval_service=None)

        # Create failing review
        failing_review = DesignReviewReport(
            task_id="TEST-001",
            review_id="REVIEW-TEST001-20251125-100000",
            overall_assessment="FAIL",
            critical_issue_count=1,
            high_issue_count=0,
            medium_issue_count=0,
            low_issue_count=0,
            automated_checks={"semantic_coverage": True},
            issues_found=[self.create_design_issue(1, "Critical")],
            checklist_review=[self.create_checklist_item()],
            review_summary="Critical issue",
            timestamp=datetime.now(),
        )

        # Call _request_approval without callable
        approved = orchestrator._request_approval(
            task_id="TEST-001",
            gate_type="design_review",
            gate_name="DesignReview",
            report=failing_review,
            hitl_approver=None,
        )

        # Verify approval was denied
        assert approved is False

    def test_deferred_decision_returns_false(self):
        """Test that DEFERRED approval decision is treated as rejection."""
        # Create mock approval service that defers
        mock_approval_service = Mock(spec=ApprovalService)
        mock_approval_service.request_approval.return_value = ApprovalResponse(
            decision=ReviewDecision.DEFERRED,
            reviewer="test-reviewer",
            timestamp=datetime.now().isoformat(),
            justification="Need more information before approving",
        )

        # Create orchestrator with approval service
        orchestrator = TSPOrchestrator(approval_service=mock_approval_service)

        # Create failing review
        failing_review = CodeReviewReport(
            task_id="TEST-001",
            review_id="CODE-REVIEW-TEST-001-20251125-100000",
            review_status="FAIL",
            critical_issues=3,
            high_issues=5,
            medium_issues=0,
            low_issues=0,
            issues_found=[],
            review_summary="Security issues need review",
            review_timestamp=datetime.now().isoformat(),
        )

        # Call _request_approval
        approved = orchestrator._request_approval(
            task_id="TEST-001",
            gate_type="code_review",
            gate_name="CodeReview",
            report=failing_review,
            hitl_approver=None,
        )

        # Verify deferred is treated as rejection
        assert approved is False
        mock_approval_service.request_approval.assert_called_once()

    def test_hitl_override_recorded_for_approval_service(self):
        """Test that HITL overrides are recorded in audit trail."""
        # Create mock approval service
        mock_approval_service = Mock(spec=ApprovalService)
        mock_approval_service.request_approval.return_value = ApprovalResponse(
            decision=ReviewDecision.APPROVED,
            reviewer="john.doe",
            timestamp="2025-11-25T10:30:00",
            justification="Business critical - acceptable risk",
        )

        # Create orchestrator with approval service
        orchestrator = TSPOrchestrator(approval_service=mock_approval_service)

        # Create failing review
        failing_review = DesignReviewReport(
            task_id="TEST-001",
            review_id="REVIEW-TEST001-20251125-100000",
            overall_assessment="FAIL",
            critical_issue_count=1,
            high_issue_count=2,
            medium_issue_count=0,
            low_issue_count=0,
            automated_checks={"semantic_coverage": True},
            issues_found=[
                self.create_design_issue(1, "Critical"),
                self.create_design_issue(2, "High"),
                self.create_design_issue(3, "High"),
            ],
            checklist_review=[self.create_checklist_item()],
            review_summary="Critical issues",
            timestamp=datetime.now(),
        )

        # Call _request_approval
        approved = orchestrator._request_approval(
            task_id="TEST-001",
            gate_type="design_review",
            gate_name="DesignReview",
            report=failing_review,
            hitl_approver=None,
        )

        # Verify override was recorded
        assert approved is True
        assert len(orchestrator.hitl_overrides) == 1

        override = orchestrator.hitl_overrides[0]
        assert override["gate_name"] == "DesignReview"
        assert (
            override["decision"]
            == "Approved by john.doe: Business critical - acceptable risk"
        )
        assert "timestamp" in override
