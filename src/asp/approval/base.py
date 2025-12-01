"""
Base classes and interfaces for HITL approval services.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Any


class ReviewDecision(Enum):
    """Review decision options."""

    APPROVED = "approved"
    REJECTED = "rejected"
    DEFERRED = "deferred"


@dataclass
class ApprovalRequest:
    """Request for human approval of quality gate failure."""

    task_id: str
    gate_type: str  # "design_review", "code_review", etc.
    agent_output: dict[str, Any]
    quality_report: dict[str, Any]
    base_branch: str = "main"


@dataclass
class ApprovalResponse:
    """Response containing approval decision and metadata."""

    decision: ReviewDecision
    reviewer: str
    timestamp: str
    justification: str
    review_branch: str | None = None
    merge_commit: str | None = None


class ApprovalService(ABC):
    """Abstract base class for HITL approval services."""

    @abstractmethod
    def request_approval(self, request: ApprovalRequest) -> ApprovalResponse:
        """
        Request human approval for quality gate failure.

        Args:
            request: ApprovalRequest containing task info and quality report

        Returns:
            ApprovalResponse with decision and metadata
        """
        pass
