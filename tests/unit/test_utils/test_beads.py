"""Tests for asp.utils.beads module."""

import re
import tempfile
from pathlib import Path

from asp.utils.beads import (
    BeadsIssue,
    BeadsStatus,
    BeadsType,
    create_issue,
    generate_beads_id,
    get_beads_directory,
    get_issues_file,
    read_issues,
    write_issues,
)


class TestGenerateBeadsId:
    """Tests for generate_beads_id function."""

    def test_generates_valid_format(self):
        """ID should match bd-{7-char-hex} pattern."""
        id_str = generate_beads_id()
        assert re.match(r"^bd-[a-f0-9]{7}$", id_str)

    def test_generates_unique_ids(self):
        """Generated IDs should be unique."""
        ids = [generate_beads_id() for _ in range(100)]
        assert len(set(ids)) == 100

    def test_uses_7_char_hash(self):
        """Hash portion should be exactly 7 characters."""
        id_str = generate_beads_id()
        hash_part = id_str.split("-")[1]
        assert len(hash_part) == 7


class TestBeadsIssue:
    """Tests for BeadsIssue model."""

    def test_minimal_issue(self):
        """Issue can be created with just id and title."""
        issue = BeadsIssue(id="bd-1234567", title="Test issue")
        assert issue.id == "bd-1234567"
        assert issue.title == "Test issue"
        assert issue.status == BeadsStatus.OPEN
        assert issue.priority == 2

    def test_full_issue(self):
        """Issue can be created with all fields."""
        issue = BeadsIssue(
            id="bd-abc1234",
            title="Test issue",
            description="A test issue description",
            status=BeadsStatus.IN_PROGRESS,
            priority=0,
            type=BeadsType.BUG,
            labels=["test", "bug"],
            created_at="2025-12-16T00:00:00Z",
        )
        assert issue.status == BeadsStatus.IN_PROGRESS
        assert issue.type == BeadsType.BUG
        assert "test" in issue.labels

    def test_extra_fields_allowed(self):
        """Extra fields should be allowed for forward compatibility."""
        issue = BeadsIssue(
            id="bd-1234567",
            title="Test",
            unknown_field="value",
        )
        assert issue.id == "bd-1234567"


class TestReadWriteIssues:
    """Tests for reading and writing issues."""

    def test_read_empty_directory(self):
        """Reading from directory without .beads returns empty list."""
        with tempfile.TemporaryDirectory() as tmpdir:
            issues = read_issues(Path(tmpdir))
            assert issues == []

    def test_write_and_read_issues(self):
        """Issues can be written and read back."""
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)

            # Write issues
            issues = [
                BeadsIssue(id="bd-0000001", title="First issue"),
                BeadsIssue(id="bd-0000002", title="Second issue", priority=0),
            ]
            write_issues(issues, root)

            # Read back
            read_back = read_issues(root)
            assert len(read_back) == 2
            assert read_back[0].id == "bd-0000001"
            assert read_back[1].priority == 0

    def test_creates_beads_directory(self):
        """Writing issues creates .beads directory if needed."""
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            issues = [BeadsIssue(id="bd-test123", title="Test")]
            write_issues(issues, root)

            assert (root / ".beads").exists()
            assert (root / ".beads" / "issues.jsonl").exists()


class TestCreateIssue:
    """Tests for create_issue function."""

    def test_creates_issue_with_hash_id(self):
        """Created issue has a hash-based ID."""
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            issue = create_issue(
                title="New issue",
                description="A description",
                root_path=root,
            )

            assert re.match(r"^bd-[a-f0-9]{7}$", issue.id)
            assert issue.title == "New issue"
            assert issue.description == "A description"

    def test_appends_to_existing_issues(self):
        """New issue is appended to existing issues."""
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)

            # Create first issue
            issue1 = create_issue(title="First", root_path=root)

            # Create second issue
            issue2 = create_issue(title="Second", root_path=root)

            # Both should exist
            all_issues = read_issues(root)
            assert len(all_issues) == 2
            assert all_issues[0].id == issue1.id
            assert all_issues[1].id == issue2.id


class TestReadIssuesErrorHandling:
    """Tests for read_issues error handling."""

    def test_read_issues_skips_empty_lines(self):
        """Empty lines in issues file are skipped."""
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            beads_dir = root / ".beads"
            beads_dir.mkdir()
            issues_file = beads_dir / "issues.jsonl"

            # Write file with empty lines
            issues_file.write_text(
                '{"id": "bd-1234567", "title": "Issue 1"}\n'
                "\n"
                '{"id": "bd-2345678", "title": "Issue 2"}\n'
                "   \n"
            )

            issues = read_issues(root)
            assert len(issues) == 2
            assert issues[0].title == "Issue 1"
            assert issues[1].title == "Issue 2"

    def test_read_issues_skips_invalid_json(self):
        """Invalid JSON lines are skipped."""
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            beads_dir = root / ".beads"
            beads_dir.mkdir()
            issues_file = beads_dir / "issues.jsonl"

            # Write file with invalid JSON
            issues_file.write_text(
                '{"id": "bd-1234567", "title": "Valid Issue"}\n'
                "not valid json\n"
                '{"id": "bd-2345678", "title": "Another Valid"}\n'
            )

            issues = read_issues(root)
            assert len(issues) == 2

    def test_read_issues_skips_malformed_data(self):
        """Malformed data (valid JSON but wrong schema) is skipped."""
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            beads_dir = root / ".beads"
            beads_dir.mkdir()
            issues_file = beads_dir / "issues.jsonl"

            # Write file with wrong schema (missing required 'id' field)
            issues_file.write_text(
                '{"id": "bd-1234567", "title": "Valid"}\n'
                '{"title": "Missing ID field"}\n'
                '{"id": "bd-2345678", "title": "Also Valid"}\n'
            )

            issues = read_issues(root)
            assert len(issues) == 2

    def test_read_issues_handles_file_read_error(self):
        """File read errors return empty list."""
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            beads_dir = root / ".beads"
            beads_dir.mkdir()
            issues_file = beads_dir / "issues.jsonl"

            # Create a directory instead of a file to cause read error
            issues_file.mkdir()

            issues = read_issues(root)
            assert issues == []


class TestHelperFunctions:
    """Tests for helper functions."""

    def test_get_beads_directory(self):
        """Returns correct .beads path."""
        path = get_beads_directory(Path("/tmp/repo"))
        assert path == Path("/tmp/repo/.beads")

    def test_get_issues_file(self):
        """Returns correct issues.jsonl path."""
        path = get_issues_file(Path("/tmp/repo"))
        assert path == Path("/tmp/repo/.beads/issues.jsonl")
