"""
Review presentation with rich terminal UI.
"""

from typing import Any

from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from rich.table import Table


class ReviewPresenter:
    """Presents review information in terminal with rich formatting."""

    def __init__(self):
        """Initialize ReviewPresenter."""
        self.console = Console()

    def display_review(
        self,
        task_id: str,
        gate_type: str,
        quality_report: dict[str, Any],
        diff: str,
        branch_name: str,
        diff_stats: dict[str, Any] | None = None,
    ) -> None:
        """
        Display review information in terminal.

        Args:
            task_id: Task identifier
            gate_type: Quality gate type
            quality_report: Quality gate report
            diff: Diff output
            branch_name: Review branch name
            diff_stats: Optional diff statistics
        """
        # Header
        self.console.rule(f"[bold cyan]REVIEW REQUEST: {task_id}", style="cyan")
        self.console.print()

        # Summary panel
        self._display_summary(
            task_id, gate_type, branch_name, quality_report, diff_stats
        )

        # Quality report
        self._display_quality_report(quality_report)

        # Diff statistics
        if diff_stats:
            self._display_diff_stats(diff_stats)

        # Ask if user wants to see full diff
        self.console.print()
        show_diff = self.console.input("[bold]View full diff? [y/n]:[/bold] ")
        if show_diff.lower() == "y":
            self._display_full_diff(diff)

    def _display_summary(
        self,
        task_id: str,
        gate_type: str,
        branch_name: str,
        quality_report: dict[str, Any],
        diff_stats: dict[str, Any] | None,
    ) -> None:
        """Display summary information."""
        summary = Table.grid(padding=(0, 2))
        summary.add_column(style="bold cyan")
        summary.add_column()

        summary.add_row("Task ID:", task_id)
        summary.add_row("Quality Gate:", gate_type)
        summary.add_row("Branch:", f"[yellow]{branch_name}[/yellow]")

        # Status
        total_issues = quality_report.get("total_issues", 0)
        passed = quality_report.get("passed", False)
        if passed:
            status = "[green]✓ PASSED[/green]"
        else:
            status = f"[red]✗ FAILED ({total_issues} issues)[/red]"
        summary.add_row("Status:", status)

        # Diff stats
        if diff_stats:
            summary.add_row("Files Changed:", str(diff_stats.get("files_changed", 0)))
            summary.add_row(
                "Changes:",
                f"[green]+{diff_stats.get('insertions', 0)}[/green] / "
                f"[red]-{diff_stats.get('deletions', 0)}[/red]",
            )

        self.console.print(
            Panel(summary, title="[bold]Summary[/bold]", border_style="cyan")
        )
        self.console.print()

    def _display_quality_report(self, report: dict[str, Any]) -> None:
        """Display quality issues in table."""
        issues = report.get("issues", [])
        if not issues:
            self.console.print("[green]No quality issues found[/green]")
            self.console.print()
            return

        table = Table(title="Quality Gate Issues", show_lines=True)
        table.add_column("Issue", style="white", no_wrap=False, width=50)
        table.add_column("Severity", justify="center", width=10)
        table.add_column("Location", justify="left", width=20)

        severity_colors = {
            "CRITICAL": "red bold",
            "HIGH": "red",
            "MEDIUM": "yellow",
            "LOW": "cyan",
        }

        for issue in issues:
            severity = issue.get("severity", "UNKNOWN")
            severity_color = severity_colors.get(severity, "white")

            # Location info
            location_parts = []
            if "file" in issue:
                location_parts.append(issue["file"])
            if "line" in issue:
                location_parts.append(f"L{issue['line']}")
            location = ":".join(location_parts) if location_parts else "-"

            table.add_row(
                issue.get("description", "No description"),
                f"[{severity_color}]{severity}[/{severity_color}]",
                location,
            )

        self.console.print(table)
        self.console.print()

        # Summary by severity
        self._display_severity_summary(report)

    def _display_severity_summary(self, report: dict[str, Any]) -> None:
        """Display issue count summary by severity."""
        issues = report.get("issues", [])
        severity_counts = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0}

        for issue in issues:
            severity = issue.get("severity", "LOW")
            if severity in severity_counts:
                severity_counts[severity] += 1

        summary_parts = []
        if severity_counts["CRITICAL"] > 0:
            summary_parts.append(
                f"[red bold]CRITICAL: {severity_counts['CRITICAL']}[/red bold]"
            )
        if severity_counts["HIGH"] > 0:
            summary_parts.append(f"[red]HIGH: {severity_counts['HIGH']}[/red]")
        if severity_counts["MEDIUM"] > 0:
            summary_parts.append(
                f"[yellow]MEDIUM: {severity_counts['MEDIUM']}[/yellow]"
            )
        if severity_counts["LOW"] > 0:
            summary_parts.append(f"[cyan]LOW: {severity_counts['LOW']}[/cyan]")

        if summary_parts:
            self.console.print("Issue Breakdown: " + " | ".join(summary_parts))
            self.console.print()

    def _display_diff_stats(self, diff_stats: dict[str, Any]) -> None:
        """Display diff statistics."""
        files_changed = diff_stats.get("files_changed", 0)
        insertions = diff_stats.get("insertions", 0)
        deletions = diff_stats.get("deletions", 0)

        self.console.print("[bold]Diff Statistics:[/bold]")
        self.console.print(f"  Files changed: {files_changed}")
        self.console.print(f"  [green]+{insertions}[/green] insertions")
        self.console.print(f"  [red]-{deletions}[/red] deletions")
        self.console.print()

    def _display_full_diff(self, diff: str) -> None:
        """Display full diff with syntax highlighting."""
        if not diff.strip():
            self.console.print("[yellow]No changes in diff[/yellow]")
            return

        self.console.rule("[bold]Full Diff", style="cyan")
        self.console.print()

        # Use syntax highlighting for diff
        try:
            syntax = Syntax(diff, "diff", theme="monokai", line_numbers=False)
            self.console.print(syntax)
        except Exception:
            # Fallback to plain text if syntax highlighting fails
            self.console.print(diff)

        self.console.print()

    def display_decision_prompt(self) -> None:
        """Display review decision options."""
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

    def display_approval_result(
        self, decision: str, merge_commit: str | None = None
    ) -> None:
        """
        Display approval result.

        Args:
            decision: Decision made (APPROVED, REJECTED, DEFERRED)
            merge_commit: Optional merge commit SHA
        """
        self.console.print()
        if decision == "APPROVED":
            self.console.print("[green bold]✓ Review APPROVED[/green bold]")
            if merge_commit:
                self.console.print(f"[green]Merged commit: {merge_commit[:8]}[/green]")
        elif decision == "REJECTED":
            self.console.print("[red bold]✗ Review REJECTED[/red bold]")
        elif decision == "DEFERRED":
            self.console.print("[yellow bold]⏸ Review DEFERRED[/yellow bold]")

        self.console.print()
