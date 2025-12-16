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


class TestBeadsSync:
    """Tests for beads sync command."""

    def test_sync_dry_run(self, capsys, tmp_path):
        """Sync --dry-run shows what would be created."""
        import json
        from asp.cli.beads_commands import cmd_beads_sync

        # Create a sample plan file
        plan_data = {
            "task_id": "TEST-SYNC",
            "semantic_units": [
                {
                    "unit_id": "su-a000001",
                    "description": "Test unit for sync",
                    "api_interactions": 1,
                    "data_transformations": 1,
                    "logical_branches": 1,
                    "code_entities_modified": 1,
                    "novelty_multiplier": 1.0,
                    "est_complexity": 10,
                },
            ],
            "total_est_complexity": 10,
        }
        plan_file = tmp_path / "plan.json"
        plan_file.write_text(json.dumps(plan_data))

        args = argparse.Namespace(
            root=str(tmp_path),
            plan_file=str(plan_file),
            dry_run=True,
            no_epic=False,
            update=False,
            list_after=False,
        )
        cmd_beads_sync(args)

        captured = capsys.readouterr()
        assert "Dry Run" in captured.out
        assert "epic-TEST-SYNC" in captured.out
        assert "su-a000001" in captured.out

    def test_sync_creates_issues(self, tmp_path):
        """Sync creates beads issues from plan."""
        import json
        from asp.cli.beads_commands import cmd_beads_sync
        from asp.utils.beads import read_issues

        plan_data = {
            "task_id": "TEST-SYNC-2",
            "semantic_units": [
                {
                    "unit_id": "su-b000002",
                    "description": "Another test unit",
                    "api_interactions": 2,
                    "data_transformations": 2,
                    "logical_branches": 2,
                    "code_entities_modified": 2,
                    "novelty_multiplier": 1.0,
                    "est_complexity": 15,
                },
            ],
            "total_est_complexity": 15,
        }
        plan_file = tmp_path / "plan.json"
        plan_file.write_text(json.dumps(plan_data))

        args = argparse.Namespace(
            root=str(tmp_path),
            plan_file=str(plan_file),
            dry_run=False,
            no_epic=False,
            update=False,
            list_after=False,
        )
        cmd_beads_sync(args)

        # Verify issues created
        issues = read_issues(tmp_path)
        assert len(issues) == 2  # epic + 1 task

    def test_sync_file_not_found(self, capsys, tmp_path):
        """Sync exits with error for missing file."""
        from asp.cli.beads_commands import cmd_beads_sync

        args = argparse.Namespace(
            root=str(tmp_path),
            plan_file="/nonexistent/plan.json",
            dry_run=False,
            no_epic=False,
            update=False,
            list_after=False,
        )

        with pytest.raises(SystemExit) as exc_info:
            cmd_beads_sync(args)

        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        assert "not found" in captured.err


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

    def test_beads_sync_has_required_args(self):
        """beads sync requires plan_file argument."""
        from asp.cli.beads_commands import add_beads_subparser

        parser = argparse.ArgumentParser()
        subparsers = parser.add_subparsers()
        add_beads_subparser(subparsers)

        # Parse beads sync with plan_file
        args = parser.parse_args(["beads", "sync", "plan.json", "--dry-run", "--no-epic"])
        assert args.plan_file == "plan.json"
        assert args.dry_run is True
        assert args.no_epic is True

    def test_beads_push_has_options(self):
        """beads push accepts repo and project options."""
        from asp.cli.beads_commands import add_beads_subparser

        parser = argparse.ArgumentParser()
        subparsers = parser.add_subparsers()
        add_beads_subparser(subparsers)

        args = parser.parse_args([
            "beads", "push",
            "--repo", "owner/repo",
            "--project", "1",
            "--dry-run",
        ])
        assert args.repo == "owner/repo"
        assert args.project == "1"
        assert args.dry_run is True

    def test_beads_pull_has_options(self):
        """beads pull accepts various filter options."""
        from asp.cli.beads_commands import add_beads_subparser

        parser = argparse.ArgumentParser()
        subparsers = parser.add_subparsers()
        add_beads_subparser(subparsers)

        args = parser.parse_args([
            "beads", "pull",
            "--issue", "42",
            "--label", "bug",
            "--state", "closed",
            "--dry-run",
        ])
        assert args.issue == 42
        assert args.label == "bug"
        assert args.state == "closed"
        assert args.dry_run is True

    def test_beads_gh_sync_has_options(self):
        """beads gh-sync accepts conflict strategy option."""
        from asp.cli.beads_commands import add_beads_subparser

        parser = argparse.ArgumentParser()
        subparsers = parser.add_subparsers()
        add_beads_subparser(subparsers)

        args = parser.parse_args([
            "beads", "gh-sync",
            "--conflict", "remote-wins",
            "--dry-run",
        ])
        assert args.conflict == "remote-wins"
        assert args.dry_run is True


class TestBeadsPush:
    """Tests for beads push command."""

    @mock.patch("asp.utils.github_sync.verify_gh_cli")
    @mock.patch("asp.utils.github_sync.push_to_github")
    def test_push_dry_run(self, mock_push, mock_verify, capsys, tmp_path):
        """Push --dry-run shows what would be created."""
        from asp.cli.beads_commands import cmd_beads_push

        mock_verify.return_value = True
        mock_push.return_value = ["(dry-run) bd-test123"]

        issues = [
            BeadsIssue(id="bd-test123", title="Test issue"),
        ]
        write_issues(issues, tmp_path)

        args = argparse.Namespace(
            root=str(tmp_path),
            repo="owner/repo",
            project=None,
            dry_run=True,
        )
        cmd_beads_push(args)

        captured = capsys.readouterr()
        assert "Would create" in captured.out
        mock_push.assert_called_once()

    @mock.patch("asp.utils.github_sync.verify_gh_cli")
    def test_push_fails_without_gh(self, mock_verify, capsys):
        """Push exits with error when gh CLI not available."""
        from asp.cli.beads_commands import cmd_beads_push

        mock_verify.return_value = False

        args = argparse.Namespace(
            root=".",
            repo=None,
            project=None,
            dry_run=True,
        )

        with pytest.raises(SystemExit) as exc_info:
            cmd_beads_push(args)

        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        assert "GitHub CLI" in captured.err


class TestBeadsPull:
    """Tests for beads pull command."""

    @mock.patch("asp.utils.github_sync.verify_gh_cli")
    @mock.patch("asp.utils.github_sync.pull_from_github")
    def test_pull_dry_run(self, mock_pull, mock_verify, capsys, tmp_path):
        """Pull --dry-run shows what would be imported."""
        from asp.cli.beads_commands import cmd_beads_pull

        mock_verify.return_value = True
        mock_pull.return_value = [
            BeadsIssue(id="(dry-run-42)", title="GitHub issue"),
        ]

        args = argparse.Namespace(
            root=str(tmp_path),
            repo="owner/repo",
            issue=42,
            label=None,
            state="open",
            dry_run=True,
        )
        cmd_beads_pull(args)

        captured = capsys.readouterr()
        assert "Would import" in captured.out
        mock_pull.assert_called_once()

    @mock.patch("asp.utils.github_sync.verify_gh_cli")
    def test_pull_fails_without_gh(self, mock_verify, capsys):
        """Pull exits with error when gh CLI not available."""
        from asp.cli.beads_commands import cmd_beads_pull

        mock_verify.return_value = False

        args = argparse.Namespace(
            root=".",
            repo=None,
            issue=None,
            label=None,
            state="open",
            dry_run=True,
        )

        with pytest.raises(SystemExit) as exc_info:
            cmd_beads_pull(args)

        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        assert "GitHub CLI" in captured.err


class TestBeadsGhSync:
    """Tests for beads gh-sync command."""

    @mock.patch("asp.utils.github_sync.verify_gh_cli")
    @mock.patch("asp.utils.github_sync.sync_github")
    def test_gh_sync_dry_run(self, mock_sync, mock_verify, capsys, tmp_path):
        """gh-sync --dry-run shows what would happen."""
        from asp.cli.beads_commands import cmd_beads_gh_sync

        mock_verify.return_value = True
        mock_sync.return_value = {"imported": 2, "exported": 1, "conflicts": 0, "skipped": 0}

        args = argparse.Namespace(
            root=str(tmp_path),
            repo="owner/repo",
            project=None,
            conflict="local-wins",
            dry_run=True,
        )
        cmd_beads_gh_sync(args)

        captured = capsys.readouterr()
        assert "Sync Summary" in captured.out
        assert "Imported from GitHub: 2" in captured.out
        assert "Exported to GitHub: 1" in captured.out
        mock_sync.assert_called_once()

    @mock.patch("asp.utils.github_sync.verify_gh_cli")
    def test_gh_sync_fails_without_gh(self, mock_verify, capsys):
        """gh-sync exits with error when gh CLI not available."""
        from asp.cli.beads_commands import cmd_beads_gh_sync

        mock_verify.return_value = False

        args = argparse.Namespace(
            root=".",
            repo=None,
            project=None,
            conflict="local-wins",
            dry_run=True,
        )

        with pytest.raises(SystemExit) as exc_info:
            cmd_beads_gh_sync(args)

        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        assert "GitHub CLI" in captured.err
