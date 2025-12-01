"""
Local PR-style approval service for HITL quality gate overrides.
"""

from typing import Any, Dict

from asp.approval.approval_collector import ApprovalCollector
from asp.approval.base import (
    ApprovalRequest,
    ApprovalResponse,
    ApprovalService,
    ReviewDecision,
)
from asp.approval.branch_manager import BranchManager
from asp.approval.merge_controller import MergeController
from asp.approval.review_presenter import ReviewPresenter


class LocalPRApprovalService(ApprovalService):
    """
    Local PR-style approval using git branches and notes.

    This service creates feature branches for agent output that fails quality gates,
    presents diffs for human review, and merges approved changes with full audit trail.
    """

    def __init__(
        self,
        repo_path: str,
        base_branch: str = "main",
        auto_cleanup: bool = True,
        notes_ref: str = "reviews",
    ):
        """
        Initialize LocalPRApprovalService.

        Args:
            repo_path: Path to git repository
            base_branch: Base branch for merges (default: "main")
            auto_cleanup: Automatically delete branches after merge/reject
            notes_ref: Git notes ref for storing review metadata
        """
        self.repo_path = repo_path
        self.base_branch = base_branch
        self.auto_cleanup = auto_cleanup
        self.notes_ref = notes_ref

        # Initialize components
        self.branch_manager = BranchManager(repo_path)
        self.review_presenter = ReviewPresenter()
        self.approval_collector = ApprovalCollector()
        self.merge_controller = MergeController(repo_path)

    def request_approval(self, request: ApprovalRequest) -> ApprovalResponse:
        """
        Request HITL approval using local PR-style workflow.

        Steps:
        1. Create feature branch with agent output
        2. Generate and present diff for review
        3. Collect approval decision
        4. Merge (if approved) or tag (if rejected/deferred)
        5. Store review metadata in git notes

        Args:
            request: ApprovalRequest with task info and quality report

        Returns:
            ApprovalResponse with decision and metadata
        """
        # Step 1: Create feature branch
        branch_name = f"review/{request.task_id}-{request.gate_type}"

        # Check if branch already exists
        if self.branch_manager.branch_exists(branch_name):
            # Delete existing branch and create fresh one
            self.branch_manager.delete_branch(branch_name, force=True)

        self.branch_manager.create_branch(
            branch_name=branch_name, base_branch=request.base_branch or self.base_branch
        )

        # Commit agent output
        commit_sha = self.branch_manager.commit_output(
            branch_name=branch_name,
            output=request.agent_output,
            task_id=request.task_id,
            gate_type=request.gate_type,
        )

        # Step 2: Generate diff
        diff = self.branch_manager.generate_diff(
            base_branch=request.base_branch or self.base_branch,
            feature_branch=branch_name,
        )

        diff_stats = self.branch_manager.get_diff_stats(
            base_branch=request.base_branch or self.base_branch,
            feature_branch=branch_name,
        )

        # Step 3: Present for review
        self.review_presenter.display_review(
            task_id=request.task_id,
            gate_type=request.gate_type,
            quality_report=request.quality_report,
            diff=diff,
            branch_name=branch_name,
            diff_stats=diff_stats,
        )

        # Step 4: Collect decision
        approval = self.approval_collector.collect_decision(task_id=request.task_id)

        # Step 5: Execute decision
        merge_commit = None
        if approval.decision == ReviewDecision.APPROVED:
            merge_commit = self.merge_controller.merge_branch(
                branch_name=branch_name,
                base_branch=request.base_branch or self.base_branch,
                review_metadata=approval,
                task_id=request.task_id,
            )
            approval.merge_commit = merge_commit

            if self.auto_cleanup:
                # Use force delete since branch was merged with --no-ff
                # (git -d won't work even after --no-ff merge sometimes)
                self.branch_manager.delete_branch(branch_name, force=True)

        elif approval.decision == ReviewDecision.REJECTED:
            self.merge_controller.tag_rejected(
                branch_name=branch_name,
                review_metadata=approval,
                task_id=request.task_id,
            )

            if self.auto_cleanup:
                self.branch_manager.delete_branch(branch_name, force=True)

        elif approval.decision == ReviewDecision.DEFERRED:
            self.merge_controller.tag_deferred(
                branch_name=branch_name,
                review_metadata=approval,
                task_id=request.task_id,
            )
            # Don't delete branch for deferred reviews

        # Store review in git notes
        self._store_review_notes(commit_sha, approval, request)

        # Display result
        self.review_presenter.display_approval_result(
            decision=approval.decision.value.upper(), merge_commit=merge_commit
        )

        approval.review_branch = branch_name
        return approval

    def _store_review_notes(
        self, commit_sha: str, approval: ApprovalResponse, request: ApprovalRequest
    ) -> None:
        """
        Store review metadata in git notes.

        Args:
            commit_sha: Commit to annotate
            approval: Approval response
            request: Original approval request
        """
        quality_summary = self._format_quality_summary(request.quality_report)

        note_content = f"""Review Decision: {approval.decision.value.upper()}
Reviewer: {approval.reviewer}
Timestamp: {approval.timestamp}
Task: {request.task_id}
Quality Gate: {request.gate_type}
Justification: {approval.justification}

Quality Report Summary:
{quality_summary}
"""

        self.branch_manager.add_note(
            commit_sha=commit_sha, note_content=note_content, notes_ref=self.notes_ref
        )

    def _format_quality_summary(self, quality_report: Dict[str, Any]) -> str:
        """
        Format quality report summary for git notes.

        Args:
            quality_report: Quality gate report

        Returns:
            Formatted summary string
        """
        issues = quality_report.get("issues", [])
        if not issues:
            return "No issues found"

        # Count by severity
        severity_counts = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0}

        for issue in issues:
            severity = issue.get("severity", "LOW")
            if severity in severity_counts:
                severity_counts[severity] += 1

        summary_parts = []
        if severity_counts["CRITICAL"] > 0:
            summary_parts.append(f"- Critical: {severity_counts['CRITICAL']}")
        if severity_counts["HIGH"] > 0:
            summary_parts.append(f"- High: {severity_counts['HIGH']}")
        if severity_counts["MEDIUM"] > 0:
            summary_parts.append(f"- Medium: {severity_counts['MEDIUM']}")
        if severity_counts["LOW"] > 0:
            summary_parts.append(f"- Low: {severity_counts['LOW']}")

        total = sum(severity_counts.values())
        summary_parts.append(f"- Total: {total}")

        return "\n".join(summary_parts)
