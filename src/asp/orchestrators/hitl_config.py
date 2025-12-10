"""
Human-in-the-Loop (HITL) Configuration for Repair Workflow.

Defines configuration for when human intervention is required during
the repair workflow. Supports multiple modes from fully autonomous
to fully supervised.

Part of ADR 006: Repair Workflow Architecture.

Author: ASP Development Team
Date: December 10, 2025
"""

from dataclasses import dataclass, field
from typing import Literal


@dataclass
class HITLConfig:
    """
    Configuration for Human-in-the-Loop approval in repair workflow.

    Controls when human intervention is required during the repair loop.
    Supports three modes:

    - autonomous: No human approval required, fully automatic repairs
    - supervised: Human approval required for every repair attempt
    - threshold: Human approval required based on conditions (default)

    In threshold mode, approval is required when:
    - Confidence drops below require_approval_for_confidence_below
    - Iterations exceed require_approval_after_iterations
    - Critical files are being modified

    Example:
        >>> config = HITLConfig(
        ...     mode="threshold",
        ...     require_approval_after_iterations=2,
        ...     require_approval_for_confidence_below=0.7,
        ... )
        >>> if config.should_require_approval(iteration=3, confidence=0.8):
        ...     # Request human approval
        ...     pass

    Attributes:
        mode: HITL mode (autonomous, supervised, threshold)
        require_approval_after_iterations: Request approval after N failed iterations
        require_approval_for_confidence_below: Request approval when confidence drops
        require_approval_for_critical_files: Files that always require approval
        require_approval_for_large_changes: Require approval when change count exceeds
        auto_approve_high_confidence: Auto-approve when confidence >= this value
        max_auto_iterations: Maximum iterations before forcing HITL (0 = unlimited)
    """

    mode: Literal["autonomous", "supervised", "threshold"] = "threshold"

    # Iteration-based triggers
    require_approval_after_iterations: int = 2
    max_auto_iterations: int = 5  # Hard limit, 0 = unlimited

    # Confidence-based triggers
    require_approval_for_confidence_below: float = 0.7
    auto_approve_high_confidence: float = 0.9

    # File-based triggers
    require_approval_for_critical_files: list[str] = field(default_factory=list)

    # Change size triggers
    require_approval_for_large_changes: int = 10  # Number of changes

    def __post_init__(self) -> None:
        """Validate configuration values."""
        if self.require_approval_after_iterations < 0:
            raise ValueError("require_approval_after_iterations must be non-negative")

        if not 0.0 <= self.require_approval_for_confidence_below <= 1.0:
            raise ValueError(
                "require_approval_for_confidence_below must be between 0 and 1"
            )

        if not 0.0 <= self.auto_approve_high_confidence <= 1.0:
            raise ValueError("auto_approve_high_confidence must be between 0 and 1")

        if self.max_auto_iterations < 0:
            raise ValueError("max_auto_iterations must be non-negative")

    def should_require_approval(
        self,
        iteration: int,
        confidence: float,
        files_to_modify: list[str] | None = None,
        change_count: int = 0,
    ) -> tuple[bool, str]:
        """
        Determine if human approval is required.

        Args:
            iteration: Current iteration number (1-indexed)
            confidence: Current repair confidence (0.0-1.0)
            files_to_modify: List of files that will be modified
            change_count: Number of changes to be applied

        Returns:
            Tuple of (requires_approval, reason)
        """
        files_to_modify = files_to_modify or []

        # Autonomous mode - never require approval
        if self.mode == "autonomous":
            return False, ""

        # Supervised mode - always require approval
        if self.mode == "supervised":
            return True, "Supervised mode requires approval for all changes"

        # Threshold mode - check conditions
        reasons = []

        # Check iteration limit
        if iteration > self.require_approval_after_iterations:
            reasons.append(
                f"Iteration {iteration} exceeds threshold of "
                f"{self.require_approval_after_iterations}"
            )

        # Check hard iteration limit
        if self.max_auto_iterations > 0 and iteration >= self.max_auto_iterations:
            reasons.append(
                f"Reached maximum auto-iteration limit of {self.max_auto_iterations}"
            )

        # Check confidence threshold
        if confidence < self.require_approval_for_confidence_below:
            reasons.append(
                f"Confidence {confidence:.2f} below threshold of "
                f"{self.require_approval_for_confidence_below}"
            )

        # Check critical files
        if self.require_approval_for_critical_files:
            critical_matches = [
                f
                for f in files_to_modify
                if any(
                    critical in f
                    for critical in self.require_approval_for_critical_files
                )
            ]
            if critical_matches:
                reasons.append(
                    f"Modifying critical files: {', '.join(critical_matches)}"
                )

        # Check change count
        if change_count > self.require_approval_for_large_changes:
            reasons.append(
                f"Large change count ({change_count}) exceeds threshold of "
                f"{self.require_approval_for_large_changes}"
            )

        # Auto-approve high confidence repairs (overrides other checks except critical files)
        if confidence >= self.auto_approve_high_confidence:
            # Still require approval for critical files
            has_critical_files = any(
                f
                for f in files_to_modify
                if any(
                    critical in f
                    for critical in self.require_approval_for_critical_files
                )
            )
            if (
                not has_critical_files
                and iteration <= self.require_approval_after_iterations
            ):
                return False, ""

        if reasons:
            return True, "; ".join(reasons)

        return False, ""

    def can_continue_without_approval(
        self,
        iteration: int,
        confidence: float,
    ) -> bool:
        """
        Quick check if we can continue without approval.

        Simplified check for common case of deciding whether to proceed.

        Args:
            iteration: Current iteration number
            confidence: Current repair confidence

        Returns:
            True if we can continue without approval
        """
        requires, _ = self.should_require_approval(iteration, confidence)
        return not requires


# Pre-defined configurations for common scenarios
AUTONOMOUS_CONFIG = HITLConfig(mode="autonomous")

SUPERVISED_CONFIG = HITLConfig(mode="supervised")

DEFAULT_CONFIG = HITLConfig(
    mode="threshold",
    require_approval_after_iterations=2,
    require_approval_for_confidence_below=0.7,
    max_auto_iterations=5,
)

CONSERVATIVE_CONFIG = HITLConfig(
    mode="threshold",
    require_approval_after_iterations=1,
    require_approval_for_confidence_below=0.8,
    max_auto_iterations=3,
    require_approval_for_large_changes=5,
)

PRODUCTION_CONFIG = HITLConfig(
    mode="threshold",
    require_approval_after_iterations=2,
    require_approval_for_confidence_below=0.7,
    require_approval_for_critical_files=[
        "config",
        "settings",
        "secret",
        "credential",
        "auth",
        "security",
        "__init__",
        "main",
    ],
    max_auto_iterations=5,
    require_approval_for_large_changes=10,
)
