"""
Unit tests for SurgicalEditor.

Tests for search-replace code editing with fuzzy matching.
"""

# pylint: disable=use-implicit-booleaness-not-comparison

from pathlib import Path

import pytest

from asp.models.diagnostic import CodeChange
from services.surgical_editor import EditResult, Match, SurgicalEditor


class TestEditResult:
    """Tests for EditResult dataclass."""

    def test_default_values(self):
        """Test default values."""
        result = EditResult(success=True)
        assert result.success is True
        assert result.files_modified == []
        assert result.backup_paths == {}
        assert result.errors == []
        assert result.changes_applied == 0
        assert result.changes_failed == 0

    def test_with_values(self):
        """Test with specified values."""
        result = EditResult(
            success=True,
            files_modified=["file1.py", "file2.py"],
            backup_paths={"file1.py": "/backup/file1.py"},
            errors=[],
            changes_applied=3,
            changes_failed=0,
        )
        assert len(result.files_modified) == 2
        assert result.changes_applied == 3


class TestMatch:
    """Tests for Match dataclass."""

    def test_match_creation(self):
        """Test creating a match."""
        match = Match(
            start=10,
            end=20,
            matched_text="some text",
            similarity=0.95,
        )
        assert match.start == 10
        assert match.end == 20
        assert match.matched_text == "some text"
        assert match.similarity == 0.95


class TestSurgicalEditorInit:
    """Tests for SurgicalEditor initialization."""

    def test_init_defaults(self, tmp_path):
        """Test initialization with defaults."""
        editor = SurgicalEditor(tmp_path)
        assert editor.workspace_path == tmp_path
        assert editor.fuzzy_threshold == 0.8
        assert editor.backup_dir == tmp_path / ".asp/backups"

    def test_init_custom_values(self, tmp_path):
        """Test initialization with custom values."""
        editor = SurgicalEditor(
            tmp_path,
            backup_dir=".backups",
            fuzzy_threshold=0.9,
        )
        assert editor.backup_dir == tmp_path / ".backups"
        assert editor.fuzzy_threshold == 0.9


class TestExactMatching:
    """Tests for exact text matching."""

    @pytest.fixture
    def editor(self, tmp_path):
        """Create an editor."""
        return SurgicalEditor(tmp_path)

    @pytest.fixture
    def sample_file(self, tmp_path):
        """Create a sample file."""
        file_path = tmp_path / "calculator.py"
        file_path.write_text(
            '''def add(a, b):
    """Add two numbers."""
    return a - b

def subtract(a, b):
    """Subtract b from a."""
    return a - b
'''
        )
        return file_path

    def test_exact_match_replace(self, editor, sample_file, tmp_path):
        """Test exact match replacement."""
        changes = [
            CodeChange(
                file_path="calculator.py",
                search_text='def add(a, b):\n    """Add two numbers."""\n    return a - b',
                replace_text='def add(a, b):\n    """Add two numbers."""\n    return a + b',
            )
        ]

        result = editor.apply_changes(changes, create_backup=False)

        assert result.success is True
        assert result.changes_applied == 1
        assert "calculator.py" in result.files_modified

        # Verify file was changed
        content = sample_file.read_text()
        assert "return a + b" in content
        # Verify subtract was NOT changed (different function)
        assert content.count("return a - b") == 1

    def test_exact_match_not_found(self, editor, sample_file):
        """Test when exact match is not found."""
        changes = [
            CodeChange(
                file_path="calculator.py",
                search_text="this text does not exist",
                replace_text="replacement",
            )
        ]

        result = editor.apply_changes(changes, create_backup=False, use_fuzzy=False)

        assert result.success is False
        assert result.changes_failed == 1
        assert len(result.errors) > 0

    def test_replace_specific_occurrence(self, editor, tmp_path):
        """Test replacing specific occurrence."""
        file_path = tmp_path / "test.py"
        file_path.write_text("x = 1\ny = 1\nz = 1\n")

        changes = [
            CodeChange(
                file_path="test.py",
                search_text="= 1",
                replace_text="= 2",
                occurrence=2,  # Replace second occurrence only
            )
        ]

        result = editor.apply_changes(changes, create_backup=False)

        assert result.success is True
        content = file_path.read_text()
        assert content == "x = 1\ny = 2\nz = 1\n"

    def test_replace_all_occurrences(self, editor, tmp_path):
        """Test replacing all occurrences."""
        file_path = tmp_path / "test.py"
        file_path.write_text("x = 1\ny = 1\nz = 1\n")

        changes = [
            CodeChange(
                file_path="test.py",
                search_text="= 1",
                replace_text="= 2",
                occurrence=0,  # Replace all
            )
        ]

        result = editor.apply_changes(changes, create_backup=False)

        assert result.success is True
        content = file_path.read_text()
        assert content == "x = 2\ny = 2\nz = 2\n"


class TestFuzzyMatching:
    """Tests for fuzzy text matching."""

    @pytest.fixture
    def editor(self, tmp_path):
        """Create an editor with lower threshold for testing."""
        return SurgicalEditor(tmp_path, fuzzy_threshold=0.7)

    def test_fuzzy_match_whitespace_difference(self, editor, tmp_path):
        """Test fuzzy match handles whitespace differences."""
        file_path = tmp_path / "test.py"
        file_path.write_text("def  add(a,  b):\n    return a + b\n")

        # Search text has different whitespace
        changes = [
            CodeChange(
                file_path="test.py",
                search_text="def add(a, b):\n    return a + b",
                replace_text="def add(a, b):\n    return a - b",
            )
        ]

        result = editor.apply_changes(changes, create_backup=False, use_fuzzy=True)

        # Should find a fuzzy match despite whitespace differences
        assert result.success is True

    def test_fuzzy_find_method(self, editor, tmp_path):
        """Test _fuzzy_find directly."""
        content = "def calculate(x, y):\n    return x + y"
        search = "def calculate(x,y):\nreturn x+y"  # No spaces

        match = editor._fuzzy_find(content, search)

        assert match is not None
        assert match.similarity >= 0.7

    def test_fuzzy_match_disabled(self, editor, tmp_path):
        """Test that fuzzy matching can be disabled."""
        file_path = tmp_path / "test.py"
        file_path.write_text("def  add(a,  b):\n    return a + b\n")

        changes = [
            CodeChange(
                file_path="test.py",
                search_text="def add(a, b):\n    return a + b",
                replace_text="def add(a, b):\n    return a - b",
            )
        ]

        # With fuzzy disabled, should fail
        result = editor.apply_changes(changes, create_backup=False, use_fuzzy=False)

        assert result.success is False


class TestBackupAndRollback:
    """Tests for backup creation and rollback."""

    @pytest.fixture
    def editor(self, tmp_path):
        """Create an editor."""
        return SurgicalEditor(tmp_path)

    @pytest.fixture
    def sample_file(self, tmp_path):
        """Create a sample file."""
        file_path = tmp_path / "calculator.py"
        file_path.write_text("original content")
        return file_path

    def test_backup_created(self, editor, sample_file, tmp_path):
        """Test that backup is created."""
        changes = [
            CodeChange(
                file_path="calculator.py",
                search_text="original content",
                replace_text="modified content",
            )
        ]

        result = editor.apply_changes(changes, create_backup=True)

        assert result.success is True
        assert "calculator.py" in result.backup_paths
        backup_path = Path(result.backup_paths["calculator.py"])
        assert backup_path.exists()
        assert backup_path.read_text() == "original content"

    def test_rollback_single_file(self, editor, sample_file):
        """Test rolling back a single file."""
        changes = [
            CodeChange(
                file_path="calculator.py",
                search_text="original content",
                replace_text="modified content",
            )
        ]

        editor.apply_changes(changes, create_backup=True)

        # Verify modification
        assert sample_file.read_text() == "modified content"

        # Rollback
        success = editor.rollback("calculator.py")

        assert success is True
        assert sample_file.read_text() == "original content"

    def test_rollback_all_files(self, editor, tmp_path):
        """Test rolling back all files."""
        file1 = tmp_path / "file1.py"
        file2 = tmp_path / "file2.py"
        file1.write_text("content1")
        file2.write_text("content2")

        changes = [
            CodeChange(
                file_path="file1.py",
                search_text="content1",
                replace_text="modified1",
            ),
            CodeChange(
                file_path="file2.py",
                search_text="content2",
                replace_text="modified2",
            ),
        ]

        editor.apply_changes(changes, create_backup=True)

        # Verify modifications
        assert file1.read_text() == "modified1"
        assert file2.read_text() == "modified2"

        # Rollback all
        success = editor.rollback()

        assert success is True
        assert file1.read_text() == "content1"
        assert file2.read_text() == "content2"

    def test_cleanup_backups(self, editor, sample_file, tmp_path):
        """Test cleaning up backup files."""
        changes = [
            CodeChange(
                file_path="calculator.py",
                search_text="original content",
                replace_text="modified content",
            )
        ]

        result = editor.apply_changes(changes, create_backup=True)
        backup_path = Path(result.backup_paths["calculator.py"])

        assert backup_path.exists()

        editor.cleanup_backups()

        assert not backup_path.exists()


class TestDiffGeneration:
    """Tests for diff preview generation."""

    @pytest.fixture
    def editor(self, tmp_path):
        """Create an editor."""
        return SurgicalEditor(tmp_path)

    def test_generate_diff(self, editor, tmp_path):
        """Test generating diff preview."""
        file_path = tmp_path / "calculator.py"
        file_path.write_text("def add(a, b):\n    return a - b\n")

        changes = [
            CodeChange(
                file_path="calculator.py",
                search_text="return a - b",
                replace_text="return a + b",
            )
        ]

        diff = editor.generate_diff(changes)

        assert "---" in diff
        assert "+++" in diff
        assert "-    return a - b" in diff
        assert "+    return a + b" in diff

    def test_generate_diff_file_not_found(self, editor):
        """Test diff for non-existent file."""
        changes = [
            CodeChange(
                file_path="nonexistent.py",
                search_text="x",
                replace_text="y",
            )
        ]

        diff = editor.generate_diff(changes)

        assert "file not found" in diff


class TestVerifyChangesApplicable:
    """Tests for verifying changes can be applied."""

    @pytest.fixture
    def editor(self, tmp_path):
        """Create an editor."""
        return SurgicalEditor(tmp_path)

    def test_verify_applicable(self, editor, tmp_path):
        """Test verifying applicable changes."""
        file_path = tmp_path / "test.py"
        file_path.write_text("original content")

        changes = [
            CodeChange(
                file_path="test.py",
                search_text="original content",
                replace_text="new content",
            )
        ]

        applicable, errors = editor.verify_changes_applicable(changes)

        assert applicable is True
        assert errors == []

    def test_verify_not_applicable_file_missing(self, editor):
        """Test verifying changes when file doesn't exist."""
        changes = [
            CodeChange(
                file_path="nonexistent.py",
                search_text="x",
                replace_text="y",
            )
        ]

        applicable, errors = editor.verify_changes_applicable(changes)

        assert applicable is False
        assert len(errors) == 1
        assert "not found" in errors[0]

    def test_verify_not_applicable_text_not_found(self, editor, tmp_path):
        """Test verifying changes when search text not found."""
        file_path = tmp_path / "test.py"
        file_path.write_text("some content")

        changes = [
            CodeChange(
                file_path="test.py",
                search_text="different content",
                replace_text="new content",
            )
        ]

        applicable, errors = editor.verify_changes_applicable(changes, use_fuzzy=False)

        assert applicable is False
        assert len(errors) == 1


class TestMultipleChanges:
    """Tests for applying multiple changes."""

    @pytest.fixture
    def editor(self, tmp_path):
        """Create an editor."""
        return SurgicalEditor(tmp_path)

    def test_multiple_changes_same_file(self, editor, tmp_path):
        """Test multiple changes to the same file."""
        file_path = tmp_path / "test.py"
        file_path.write_text("x = 1\ny = 2\nz = 3\n")

        changes = [
            CodeChange(
                file_path="test.py",
                search_text="x = 1",
                replace_text="x = 10",
            ),
            CodeChange(
                file_path="test.py",
                search_text="y = 2",
                replace_text="y = 20",
            ),
        ]

        result = editor.apply_changes(changes, create_backup=False)

        assert result.success is True
        assert result.changes_applied == 2
        content = file_path.read_text()
        assert "x = 10" in content
        assert "y = 20" in content
        assert "z = 3" in content

    def test_multiple_changes_different_files(self, editor, tmp_path):
        """Test changes to different files."""
        file1 = tmp_path / "file1.py"
        file2 = tmp_path / "file2.py"
        file1.write_text("content1")
        file2.write_text("content2")

        changes = [
            CodeChange(
                file_path="file1.py",
                search_text="content1",
                replace_text="modified1",
            ),
            CodeChange(
                file_path="file2.py",
                search_text="content2",
                replace_text="modified2",
            ),
        ]

        result = editor.apply_changes(changes, create_backup=False)

        assert result.success is True
        assert result.changes_applied == 2
        assert len(result.files_modified) == 2

    def test_partial_failure(self, editor, tmp_path):
        """Test when some changes fail across different files."""
        file1 = tmp_path / "file1.py"
        file2 = tmp_path / "file2.py"
        file1.write_text("existing content")
        file2.write_text("other content")

        changes = [
            CodeChange(
                file_path="file1.py",
                search_text="existing content",
                replace_text="new content",
            ),
            CodeChange(
                file_path="file2.py",
                search_text="nonexistent",  # This will fail
                replace_text="replacement",
            ),
        ]

        result = editor.apply_changes(changes, create_backup=False, use_fuzzy=False)

        assert result.success is False
        assert result.changes_applied == 1  # file1 succeeded
        assert result.changes_failed == 1  # file2 failed
        # First file should have been modified
        assert file1.read_text() == "new content"
        # Second file should be unchanged
        assert file2.read_text() == "other content"
