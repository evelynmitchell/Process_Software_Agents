"""Tests for asp.cli.beads_commands module."""

import argparse
import io
import sys
import tempfile
from pathlib import Path
from unittest import mock

import pytest

from asp.utils.beads import BeadsIssue, BeadsStatus, BeadsType, write_issues


class TestBeadsList:
    """Tests for beads list command."""

    def test_list_shows_open_issues(self, capsys):
        """List command shows open issues."""
        from asp.cli.beads_commands import cmd_beads_list

        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            issues = [
                BeadsIssue(id="bd-0000001", title="Open issue", status=BeadsStatus.OPEN),
                BeadsIssue(id="bd-0000002", title="Closed issue", status=BeadsStatus.CLOSED),
            ]
            write_issues(issues, root)

            args = argparse.Namespace(root=str(root), all=False, verbose=False)
            cmd_beads_list(args)

            captured = capsys.readouterr()
            assert "bd-0000001" in captured.out
            assert "Open issue" in captured.out
            assert "bd-0000002" not in captured.out

    def test_list_all_shows_closed(self, capsys):
        """List --all shows closed issues too."""
        from asp.cli.beads_commands import cmd_beads_list

        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            issues = [
                BeadsIssue(id="bd-0000001", title="Open issue", status=BeadsStatus.OPEN),
                BeadsIssue(id="bd-0000002", title="Closed issue", status=BeadsStatus.CLOSED),
            ]
            write_issues(issues, root)

            args = argparse.Namespace(root=str(root), all=True, verbose=False)
            cmd_beads_list(args)

            captured = capsys.readouterr()
            assert "bd-0000001" in captured.out
            assert "bd-0000002" in captured.out
            assert "Closed issue" in captured.out

    def test_list_empty(self, capsys):
        """List shows message when no issues."""
        from asp.cli.beads_commands import cmd_beads_list

        with tempfile.TemporaryDirectory() as tmpdir:
            args = argparse.Namespace(root=tmpdir, all=False, verbose=False)
            cmd_beads_list(args)

            captured = capsys.readouterr()
            assert "No open issues" in captured.out

    def test_list_priority_markers(self, capsys):
        """List shows priority markers."""
        from asp.cli.beads_commands import cmd_beads_list

        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            issues = [
                BeadsIssue(id="bd-p0issue", title="P0 issue", priority=0),
                BeadsIssue(id="bd-p1issue", title="P1 issue", priority=1),
                BeadsIssue(id="bd-p3issue", title="P3 issue", priority=3),
            ]
            write_issues(issues, root)

            args = argparse.Namespace(root=str(root), all=False, verbose=False)
            cmd_beads_list(args)

            captured = capsys.readouterr()
            # P0 gets 3 !, P1 gets 2 !, P3 gets none
            assert "!!!" in captured.out
            assert "!!" in captured.out


class TestBeadsShow:
    """Tests for beads show command."""

    def test_show_displays_issue(self, capsys):
        """Show command displays issue details."""
        from asp.cli.beads_commands import cmd_beads_show

        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            issues = [
                BeadsIssue(
                    id="bd-test123",
                    title="Test Issue",
                    description="Test description",
                    type=BeadsType.BUG,
                    priority=1,
                    labels=["test", "bug"],
                ),
            ]
            write_issues(issues, root)

            args = argparse.Namespace(root=str(root), issue_id="bd-test123")
            cmd_beads_show(args)

            captured = capsys.readouterr()
            assert "bd-test123" in captured.out
            assert "Test Issue" in captured.out
            assert "bug" in captured.out
            assert "P1" in captured.out

    def test_show_not_found(self, capsys):
        """Show exits with error for unknown issue."""
        from asp.cli.beads_commands import cmd_beads_show

        with tempfile.TemporaryDirectory() as tmpdir:
            args = argparse.Namespace(root=tmpdir, issue_id="bd-unknown")

            with pytest.raises(SystemExit) as exc_info:
                cmd_beads_show(args)

            assert exc_info.value.code == 1
            captured = capsys.readouterr()
            assert "not found" in captured.err


class TestBeadsProcess:
    """Tests for beads process command."""

    def test_process_dry_run(self, capsys):
        """Process --dry-run shows plan preview."""
        from asp.cli.beads_commands import cmd_beads_process

        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            issues = [
                BeadsIssue(
                    id="bd-test456",
                    title="Fix the bug",
                    description="Detailed description",
                ),
            ]
            write_issues(issues, root)

            args = argparse.Namespace(
                root=str(root),
                issue_id="bd-test456",
                dry_run=True,
                output=None,
            )
            cmd_beads_process(args)

            captured = capsys.readouterr()
            assert "Dry Run" in captured.out
            assert "bd-test456" in captured.out
            assert "Fix the bug" in captured.out

    def test_process_not_found(self, capsys):
        """Process exits with error for unknown issue."""
        from asp.cli.beads_commands import cmd_beads_process

        with tempfile.TemporaryDirectory() as tmpdir:
            args = argparse.Namespace(
                root=tmpdir,
                issue_id="bd-unknown",
                dry_run=True,
                output=None,
            )

            with pytest.raises(SystemExit) as exc_info:
                cmd_beads_process(args)

            assert exc_info.value.code == 1
            captured = capsys.readouterr()
            assert "not found" in captured.err

    def test_process_warns_on_closed(self, capsys):
        """Process warns when processing closed issue."""
        from asp.cli.beads_commands import cmd_beads_process

        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            issues = [
                BeadsIssue(
                    id="bd-closed1",
                    title="Closed issue",
                    status=BeadsStatus.CLOSED,
                ),
            ]
            write_issues(issues, root)

            args = argparse.Namespace(
                root=str(root),
                issue_id="bd-closed1",
                dry_run=True,
                output=None,
            )
            cmd_beads_process(args)

            captured = capsys.readouterr()
            assert "already closed" in captured.err


class TestAddBeadsSubparser:
    """Tests for subparser integration."""

    def test_adds_beads_subcommand(self):
        """add_beads_subparser adds beads command group."""
        from asp.cli.beads_commands import add_beads_subparser

        parser = argparse.ArgumentParser()
        subparsers = parser.add_subparsers()
        add_beads_subparser(subparsers)

        # Parse beads list command
        args = parser.parse_args(["beads", "list"])
        assert hasattr(args, "func")

    def test_beads_process_has_required_args(self):
        """beads process requires issue_id argument."""
        from asp.cli.beads_commands import add_beads_subparser

        parser = argparse.ArgumentParser()
        subparsers = parser.add_subparsers()
        add_beads_subparser(subparsers)

        # Parse beads process with issue_id
        args = parser.parse_args(["beads", "process", "bd-test123", "--dry-run"])
        assert args.issue_id == "bd-test123"
        assert args.dry_run is True
