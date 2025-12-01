"""
Merge and tag operations for approved/rejected reviews.
"""

import subprocess
from pathlib import Path
from typing import Optional

from asp.approval.base import ApprovalResponse


class MergeController:
    """Controls merge and tagging operations for reviews."""

    def __init__(self, repo_path: str):
        """
        Initialize MergeController.

        Args:
            repo_path: Path to git repository
        """
        self.repo_path = Path(repo_path)

    def merge_branch(
        self,
        branch_name: str,
        base_branch: str,
        review_metadata: ApprovalResponse,
        task_id: Optional[str] = None,
    ) -> str:
        """
        Merge branch with --no-ff, return merge commit SHA.

        Args:
            branch_name: Branch to merge
            base_branch: Target base branch
            review_metadata: Approval metadata
            task_id: Optional task identifier

        Returns:
            Merge commit SHA
        """
        # Switch to base branch
        subprocess.run(
            ["git", "checkout", base_branch],
            cwd=self.repo_path,
            check=True,
            capture_output=True,
        )

        # Create merge commit message
        merge_msg = f"""Merge {branch_name}: HITL Approved

Review Decision: APPROVED
Reviewer: {review_metadata.reviewer}
Timestamp: {review_metadata.timestamp}
Justification: {review_metadata.justification}
"""
        if task_id:
            merge_msg += f"\nTask: {task_id}"

        # Merge with --no-ff to preserve branch history
        subprocess.run(
            ["git", "merge", "--no-ff", branch_name, "-m", merge_msg],
            cwd=self.repo_path,
            check=True,
            capture_output=True,
        )

        # Get merge commit SHA
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=self.repo_path,
            capture_output=True,
            text=True,
            check=True,
        )
        merge_sha = result.stdout.strip()

        # Create tag for easy reference
        if task_id:
            tag_name = f"review-approved-{task_id}"
            self.create_tag(tag_name, merge_sha, review_metadata)

        return merge_sha

    def tag_rejected(
        self,
        branch_name: str,
        review_metadata: ApprovalResponse,
        task_id: Optional[str] = None,
    ) -> None:
        """
        Tag rejected branch for historical record.

        Args:
            branch_name: Branch to tag
            review_metadata: Rejection metadata
            task_id: Optional task identifier
        """
        if task_id:
            tag_name = f"review-rejected-{task_id}"
        else:
            # Extract from branch name
            tag_name = f"review-rejected-{branch_name.split('/')[-1]}"

        tag_msg = f"""Review REJECTED

Reviewer: {review_metadata.reviewer}
Timestamp: {review_metadata.timestamp}
Reason: {review_metadata.justification}
"""

        subprocess.run(
            ["git", "tag", "-a", tag_name, branch_name, "-m", tag_msg],
            cwd=self.repo_path,
            check=True,
            capture_output=True,
        )

    def tag_deferred(
        self,
        branch_name: str,
        review_metadata: ApprovalResponse,
        task_id: Optional[str] = None,
    ) -> None:
        """
        Tag deferred branch for later review.

        Args:
            branch_name: Branch to tag
            review_metadata: Deferral metadata
            task_id: Optional task identifier
        """
        if task_id:
            tag_name = f"review-deferred-{task_id}"
        else:
            # Extract from branch name
            tag_name = f"review-deferred-{branch_name.split('/')[-1]}"

        tag_msg = f"""Review DEFERRED

Reviewer: {review_metadata.reviewer}
Timestamp: {review_metadata.timestamp}
Reason: {review_metadata.justification}
"""

        subprocess.run(
            ["git", "tag", "-a", tag_name, branch_name, "-m", tag_msg],
            cwd=self.repo_path,
            check=True,
            capture_output=True,
        )

    def create_tag(
        self, tag_name: str, commit_sha: str, review_metadata: ApprovalResponse
    ) -> None:
        """
        Create annotated tag.

        Args:
            tag_name: Tag name
            commit_sha: Commit to tag
            review_metadata: Review metadata
        """
        tag_msg = f"""HITL Review Approved

Reviewer: {review_metadata.reviewer}
Timestamp: {review_metadata.timestamp}
Justification: {review_metadata.justification}
"""

        subprocess.run(
            ["git", "tag", "-a", tag_name, commit_sha, "-m", tag_msg],
            cwd=self.repo_path,
            check=True,
            capture_output=True,
        )

    def tag_exists(self, tag_name: str) -> bool:
        """
        Check if tag exists.

        Args:
            tag_name: Tag name to check

        Returns:
            True if tag exists
        """
        result = subprocess.run(
            ["git", "rev-parse", tag_name], cwd=self.repo_path, capture_output=True
        )
        return result.returncode == 0

    def delete_tag(self, tag_name: str) -> None:
        """
        Delete tag.

        Args:
            tag_name: Tag to delete
        """
        subprocess.run(
            ["git", "tag", "-d", tag_name],
            cwd=self.repo_path,
            check=True,
            capture_output=True,
        )
