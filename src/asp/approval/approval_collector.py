"""
Approval decision collection from user input.
"""

import getpass
from datetime import UTC, datetime

from rich.console import Console

from asp.approval.base import ApprovalResponse, ReviewDecision


class ApprovalCollector:
    """Collects approval decisions from user via terminal."""

    def __init__(self):
        """Initialize ApprovalCollector."""
        self.console = Console()

    def collect_decision(self, task_id: str | None = None) -> ApprovalResponse:
        """
        Collect approval decision from user.

        Args:
            task_id: Optional task identifier for context

        Returns:
            ApprovalResponse with decision and metadata
        """
        # Display options
        self.console.rule("[bold cyan]REVIEW DECISION", style="cyan")
        self.console.print()
        self.console.print("[bold]Options:[/bold]")
        self.console.print(
            "  [green]1. APPROVE[/green]   - Merge changes to main branch"
        )
        self.console.print(
            "  [red]2. REJECT[/red]    - Do not merge, mark for revision"
        )
        self.console.print("  [yellow]3. DEFER[/yellow]     - Save decision for later")
        self.console.print()

        # Get decision
        decision = self._prompt_decision()

        # Get justification
        justification = self._prompt_justification(decision)

        # Get reviewer info
        reviewer = self._get_reviewer()
        timestamp = datetime.now(UTC).isoformat().replace("+00:00", "Z")

        return ApprovalResponse(
            decision=decision,
            reviewer=reviewer,
            timestamp=timestamp,
            justification=justification,
        )

    def _prompt_decision(self) -> ReviewDecision:
        """
        Prompt user for decision.

        Returns:
            ReviewDecision enum value
        """
        decision_map = {
            "1": ReviewDecision.APPROVED,
            "2": ReviewDecision.REJECTED,
            "3": ReviewDecision.DEFERRED,
        }

        while True:
            choice = self.console.input("[bold]Your decision [1/2/3]:[/bold] ")
            if choice in decision_map:
                return decision_map[choice]
            self.console.print("[red]Invalid choice. Please enter 1, 2, or 3.[/red]")

    def _prompt_justification(self, decision: ReviewDecision) -> str:
        """
        Prompt user for justification.

        Args:
            decision: The decision that was made

        Returns:
            Justification text
        """
        self.console.print()
        if decision == ReviewDecision.APPROVED:
            self.console.print(
                "[bold green]Justification for approval (required):[/bold green]"
            )
        elif decision == ReviewDecision.REJECTED:
            self.console.print(
                "[bold red]Justification for rejection (required):[/bold red]"
            )
        else:
            self.console.print(
                "[bold yellow]Reason for deferring (required):[/bold yellow]"
            )

        while True:
            justification = self.console.input("> ")
            if justification.strip():
                return justification.strip()
            self.console.print(
                "[red]Justification is required. Please provide a reason.[/red]"
            )

    def _get_reviewer(self) -> str:
        """
        Get reviewer identifier.

        Returns:
            Reviewer email or username
        """
        # Try to get from git config
        import subprocess

        try:
            result = subprocess.run(
                ["git", "config", "user.email"],
                capture_output=True,
                text=True,
                check=True,
            )
            email = result.stdout.strip()
            if email:
                return email
        except subprocess.CalledProcessError:
            pass

        # Fallback to system username
        username = getpass.getuser()
        return f"{username}@local"

    def prompt_view_diff(self) -> bool:
        """
        Ask if user wants to view diff.

        Returns:
            True if user wants to see diff
        """
        response = self.console.input("[bold]View full diff? [y/n]:[/bold] ")
        return response.lower() in ["y", "yes"]
