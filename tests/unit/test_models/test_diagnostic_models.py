"""
Unit tests for diagnostic models.

Tests for IssueType, Severity, AffectedFile, CodeChange, SuggestedFix,
DiagnosticInput, and DiagnosticReport models.
"""

import pytest

from asp.models.diagnostic import (
    AffectedFile,
    CodeChange,
    DiagnosticInput,
    DiagnosticReport,
    IssueType,
    Severity,
    SuggestedFix,
)
from asp.models.execution import TestResult


class TestIssueType:
    """Tests for IssueType enum."""

    def test_issue_type_values(self):
        """Test all issue type values exist."""
        assert IssueType.TEST_FAILURE == "test_failure"
        assert IssueType.BUILD_ERROR == "build_error"
        assert IssueType.RUNTIME_ERROR == "runtime_error"
        assert IssueType.TYPE_ERROR == "type_error"
        assert IssueType.IMPORT_ERROR == "import_error"
        assert IssueType.SYNTAX_ERROR == "syntax_error"
        assert IssueType.LOGIC_ERROR == "logic_error"
        assert IssueType.CONFIGURATION_ERROR == "configuration_error"

    def test_issue_type_is_string_enum(self):
        """Test that IssueType is a string enum."""
        assert isinstance(IssueType.TEST_FAILURE, str)
        assert IssueType.TEST_FAILURE.value == "test_failure"


class TestSeverity:
    """Tests for Severity enum."""

    def test_severity_values(self):
        """Test all severity values exist."""
        assert Severity.CRITICAL == "Critical"
        assert Severity.HIGH == "High"
        assert Severity.MEDIUM == "Medium"
        assert Severity.LOW == "Low"

    def test_severity_is_string_enum(self):
        """Test that Severity is a string enum."""
        assert isinstance(Severity.CRITICAL, str)
        assert Severity.CRITICAL.value == "Critical"


class TestAffectedFile:
    """Tests for AffectedFile model."""

    def test_valid_affected_file(self):
        """Test creating a valid affected file."""
        affected = AffectedFile(
            path="src/calculator.py",
            line_start=5,
            line_end=7,
            code_snippet="def add(a, b):\n    return a - b",
            issue_description="Wrong operator used in addition function",
        )
        assert affected.path == "src/calculator.py"
        assert affected.line_start == 5
        assert affected.line_end == 7
        assert "return a - b" in affected.code_snippet
        assert len(affected.issue_description) >= 10

    def test_line_end_must_be_gte_line_start(self):
        """Test that line_end must be >= line_start."""
        with pytest.raises(ValueError, match="line_end.*must be >= line_start"):
            AffectedFile(
                path="test.py",
                line_start=10,
                line_end=5,  # Invalid: less than line_start
                code_snippet="code",
                issue_description="Description of the issue here",
            )

    def test_path_is_trimmed(self):
        """Test that path whitespace is trimmed."""
        affected = AffectedFile(
            path="  src/test.py  ",
            line_start=1,
            line_end=1,
            code_snippet="code",
            issue_description="Description of the issue",
        )
        assert affected.path == "src/test.py"

    def test_empty_path_rejected(self):
        """Test that empty path is rejected."""
        with pytest.raises(ValueError):
            AffectedFile(
                path="",
                line_start=1,
                line_end=1,
                code_snippet="code",
                issue_description="Description of the issue",
            )

    def test_invalid_line_numbers(self):
        """Test that line numbers must be positive."""
        with pytest.raises(ValueError):
            AffectedFile(
                path="test.py",
                line_start=0,
                line_end=1,
                code_snippet="code",
                issue_description="Description of the issue",
            )

    def test_issue_description_min_length(self):
        """Test that issue_description has minimum length."""
        with pytest.raises(ValueError):
            AffectedFile(
                path="test.py",
                line_start=1,
                line_end=1,
                code_snippet="code",
                issue_description="short",  # Too short
            )


class TestCodeChange:
    """Tests for CodeChange model."""

    def test_valid_code_change(self):
        """Test creating a valid code change."""
        change = CodeChange(
            file_path="src/calculator.py",
            search_text="return a - b",
            replace_text="return a + b",
            occurrence=1,
            description="Fix addition operator",
        )
        assert change.file_path == "src/calculator.py"
        assert change.search_text == "return a - b"
        assert change.replace_text == "return a + b"
        assert change.occurrence == 1
        assert change.description == "Fix addition operator"

    def test_default_occurrence(self):
        """Test default occurrence value."""
        change = CodeChange(
            file_path="test.py",
            search_text="old",
            replace_text="new",
        )
        assert change.occurrence == 1

    def test_search_and_replace_must_be_different(self):
        """Test that search and replace text must differ."""
        with pytest.raises(ValueError, match="must be different"):
            CodeChange(
                file_path="test.py",
                search_text="same text",
                replace_text="same text",
            )

    def test_file_path_is_trimmed(self):
        """Test that file path whitespace is trimmed."""
        change = CodeChange(
            file_path="  src/test.py  ",
            search_text="old",
            replace_text="new",
        )
        assert change.file_path == "src/test.py"

    def test_empty_search_text_rejected(self):
        """Test that empty search text is rejected."""
        with pytest.raises(ValueError):
            CodeChange(
                file_path="test.py",
                search_text="",
                replace_text="new",
            )

    def test_empty_replace_text_allowed(self):
        """Test that empty replace text is allowed (for deletion)."""
        change = CodeChange(
            file_path="test.py",
            search_text="delete this",
            replace_text="",
        )
        assert change.replace_text == ""

    def test_occurrence_zero_for_all(self):
        """Test that occurrence=0 means replace all."""
        change = CodeChange(
            file_path="test.py",
            search_text="old",
            replace_text="new",
            occurrence=0,
        )
        assert change.occurrence == 0


class TestSuggestedFix:
    """Tests for SuggestedFix model."""

    @pytest.fixture
    def valid_change(self):
        """Create a valid code change."""
        return CodeChange(
            file_path="src/calculator.py",
            search_text="return a - b",
            replace_text="return a + b",
        )

    def test_valid_suggested_fix(self, valid_change):
        """Test creating a valid suggested fix."""
        fix = SuggestedFix(
            fix_id="FIX-001",
            description="Change subtraction to addition",
            confidence=0.95,
            changes=[valid_change],
            rationale="The function should add, not subtract",
            risks=[],
        )
        assert fix.fix_id == "FIX-001"
        assert fix.confidence == 0.95
        assert len(fix.changes) == 1
        assert fix.rationale == "The function should add, not subtract"

    def test_confidence_bounds(self, valid_change):
        """Test confidence must be between 0 and 1."""
        # Valid at boundaries
        fix_low = SuggestedFix(
            fix_id="FIX-001",
            description="Low confidence fix here",
            confidence=0.0,
            changes=[valid_change],
        )
        assert fix_low.confidence == 0.0

        fix_high = SuggestedFix(
            fix_id="FIX-002",
            description="High confidence fix here",
            confidence=1.0,
            changes=[valid_change],
        )
        assert fix_high.confidence == 1.0

        # Invalid - too high
        with pytest.raises(ValueError):
            SuggestedFix(
                fix_id="FIX-003",
                description="Invalid confidence fix",
                confidence=1.5,
                changes=[valid_change],
            )

        # Invalid - negative
        with pytest.raises(ValueError):
            SuggestedFix(
                fix_id="FIX-004",
                description="Invalid negative confidence",
                confidence=-0.1,
                changes=[valid_change],
            )

    def test_must_have_at_least_one_change(self):
        """Test that fix must have at least one change."""
        with pytest.raises(ValueError):
            SuggestedFix(
                fix_id="FIX-001",
                description="Fix with no changes is invalid",
                confidence=0.9,
                changes=[],  # Empty!
            )

    def test_description_min_length(self, valid_change):
        """Test description minimum length."""
        with pytest.raises(ValueError):
            SuggestedFix(
                fix_id="FIX-001",
                description="short",  # Too short
                confidence=0.9,
                changes=[valid_change],
            )


class TestDiagnosticInput:
    """Tests for DiagnosticInput model."""

    @pytest.fixture
    def test_result(self):
        """Create a valid test result."""
        return TestResult(
            framework="pytest",
            total_tests=5,
            passed=4,
            failed=1,
            duration_seconds=1.5,
        )

    def test_valid_diagnostic_input(self, test_result):
        """Test creating a valid diagnostic input."""
        input_data = DiagnosticInput(
            task_id="REPAIR-001",
            workspace_path="/workspaces/my-project",
            test_result=test_result,
            error_type="AssertionError",
            error_message="assert add(2, 3) == 5",
            stack_trace="Traceback...",
        )
        assert input_data.task_id == "REPAIR-001"
        assert input_data.workspace_path == "/workspaces/my-project"
        assert input_data.error_type == "AssertionError"
        assert input_data.error_message == "assert add(2, 3) == 5"

    def test_task_id_validation(self, test_result):
        """Test task_id minimum length."""
        with pytest.raises(ValueError, match="at least 3 characters"):
            DiagnosticInput(
                task_id="AB",  # Too short
                workspace_path="/path",
                test_result=test_result,
                error_type="Error",
                error_message="msg",
            )

    def test_task_id_trimmed(self, test_result):
        """Test task_id whitespace is trimmed."""
        input_data = DiagnosticInput(
            task_id="  REPAIR-001  ",
            workspace_path="/path",
            test_result=test_result,
            error_type="Error",
            error_message="msg",
        )
        assert input_data.task_id == "REPAIR-001"

    def test_source_files_default_empty(self, test_result):
        """Test source_files defaults to empty dict."""
        input_data = DiagnosticInput(
            task_id="REPAIR-001",
            workspace_path="/path",
            test_result=test_result,
            error_type="Error",
            error_message="msg",
        )
        assert input_data.source_files == {}

    def test_source_files_with_content(self, test_result):
        """Test providing source files."""
        input_data = DiagnosticInput(
            task_id="REPAIR-001",
            workspace_path="/path",
            test_result=test_result,
            error_type="Error",
            error_message="msg",
            source_files={
                "src/calculator.py": "def add(a, b):\n    return a - b",
            },
        )
        assert "src/calculator.py" in input_data.source_files


class TestDiagnosticReport:
    """Tests for DiagnosticReport model."""

    @pytest.fixture
    def affected_file(self):
        """Create a valid affected file."""
        return AffectedFile(
            path="src/calculator.py",
            line_start=5,
            line_end=7,
            code_snippet="def add(a, b):\n    return a - b",
            issue_description="Wrong operator in add function",
        )

    @pytest.fixture
    def suggested_fix(self):
        """Create a valid suggested fix."""
        return SuggestedFix(
            fix_id="FIX-001",
            description="Change subtraction to addition",
            confidence=0.95,
            changes=[
                CodeChange(
                    file_path="src/calculator.py",
                    search_text="return a - b",
                    replace_text="return a + b",
                )
            ],
        )

    def test_valid_diagnostic_report(self, affected_file, suggested_fix):
        """Test creating a valid diagnostic report."""
        report = DiagnosticReport(
            task_id="REPAIR-001",
            issue_type=IssueType.LOGIC_ERROR,
            severity=Severity.HIGH,
            root_cause="The add function uses subtraction instead of addition",
            affected_files=[affected_file],
            suggested_fixes=[suggested_fix],
            confidence=0.95,
        )
        assert report.task_id == "REPAIR-001"
        assert report.issue_type == IssueType.LOGIC_ERROR
        assert report.severity == Severity.HIGH
        assert report.confidence == 0.95
        assert len(report.affected_files) == 1
        assert len(report.suggested_fixes) == 1

    def test_root_cause_min_length(self, affected_file, suggested_fix):
        """Test root_cause minimum length."""
        with pytest.raises(ValueError):
            DiagnosticReport(
                task_id="REPAIR-001",
                issue_type=IssueType.LOGIC_ERROR,
                severity=Severity.HIGH,
                root_cause="Too short",  # Less than 20 chars
                affected_files=[affected_file],
                suggested_fixes=[suggested_fix],
                confidence=0.95,
            )

    def test_must_have_affected_files(self, suggested_fix):
        """Test must have at least one affected file."""
        with pytest.raises(ValueError):
            DiagnosticReport(
                task_id="REPAIR-001",
                issue_type=IssueType.LOGIC_ERROR,
                severity=Severity.HIGH,
                root_cause="Root cause description that is long enough",
                affected_files=[],  # Empty!
                suggested_fixes=[suggested_fix],
                confidence=0.95,
            )

    def test_must_have_suggested_fixes(self, affected_file):
        """Test must have at least one suggested fix."""
        with pytest.raises(ValueError):
            DiagnosticReport(
                task_id="REPAIR-001",
                issue_type=IssueType.LOGIC_ERROR,
                severity=Severity.HIGH,
                root_cause="Root cause description that is long enough",
                affected_files=[affected_file],
                suggested_fixes=[],  # Empty!
                confidence=0.95,
            )

    def test_best_fix_property(self, affected_file):
        """Test best_fix returns highest confidence fix."""
        fix_low = SuggestedFix(
            fix_id="FIX-001",
            description="Low confidence fix option",
            confidence=0.6,
            changes=[
                CodeChange(
                    file_path="test.py",
                    search_text="old1",
                    replace_text="new1",
                )
            ],
        )
        fix_high = SuggestedFix(
            fix_id="FIX-002",
            description="High confidence fix option",
            confidence=0.95,
            changes=[
                CodeChange(
                    file_path="test.py",
                    search_text="old2",
                    replace_text="new2",
                )
            ],
        )

        report = DiagnosticReport(
            task_id="REPAIR-001",
            issue_type=IssueType.LOGIC_ERROR,
            severity=Severity.HIGH,
            root_cause="Root cause description that is long enough",
            affected_files=[affected_file],
            suggested_fixes=[fix_low, fix_high],  # Lower confidence first
            confidence=0.9,
        )

        assert report.best_fix == fix_high
        assert report.best_fix.confidence == 0.95

    def test_is_high_confidence_property(self, affected_file, suggested_fix):
        """Test is_high_confidence threshold."""
        report_high = DiagnosticReport(
            task_id="REPAIR-001",
            issue_type=IssueType.LOGIC_ERROR,
            severity=Severity.HIGH,
            root_cause="Root cause description that is long enough",
            affected_files=[affected_file],
            suggested_fixes=[suggested_fix],
            confidence=0.85,
        )
        assert report_high.is_high_confidence is True

        report_low = DiagnosticReport(
            task_id="REPAIR-002",
            issue_type=IssueType.LOGIC_ERROR,
            severity=Severity.HIGH,
            root_cause="Root cause description that is long enough",
            affected_files=[affected_file],
            suggested_fixes=[suggested_fix],
            confidence=0.7,
        )
        assert report_low.is_high_confidence is False

    def test_confidence_bounds(self, affected_file, suggested_fix):
        """Test confidence must be between 0 and 1."""
        # Valid at boundaries
        report_zero = DiagnosticReport(
            task_id="REPAIR-001",
            issue_type=IssueType.LOGIC_ERROR,
            severity=Severity.HIGH,
            root_cause="Root cause description that is long enough",
            affected_files=[affected_file],
            suggested_fixes=[suggested_fix],
            confidence=0.0,
        )
        assert report_zero.confidence == 0.0

        # Invalid - too high
        with pytest.raises(ValueError):
            DiagnosticReport(
                task_id="REPAIR-001",
                issue_type=IssueType.LOGIC_ERROR,
                severity=Severity.HIGH,
                root_cause="Root cause description that is long enough",
                affected_files=[affected_file],
                suggested_fixes=[suggested_fix],
                confidence=1.5,
            )

    def test_optional_fields(self, affected_file, suggested_fix):
        """Test optional fields have correct defaults."""
        report = DiagnosticReport(
            task_id="REPAIR-001",
            issue_type=IssueType.LOGIC_ERROR,
            severity=Severity.HIGH,
            root_cause="Root cause description that is long enough",
            affected_files=[affected_file],
            suggested_fixes=[suggested_fix],
            confidence=0.9,
        )
        assert report.diagnosis_notes == ""
        assert report.related_issues == []

    def test_with_optional_fields(self, affected_file, suggested_fix):
        """Test providing optional fields."""
        report = DiagnosticReport(
            task_id="REPAIR-001",
            issue_type=IssueType.LOGIC_ERROR,
            severity=Severity.HIGH,
            root_cause="Root cause description that is long enough",
            affected_files=[affected_file],
            suggested_fixes=[suggested_fix],
            confidence=0.9,
            diagnosis_notes="Additional diagnostic notes here",
            related_issues=["ISSUE-001", "ISSUE-002"],
        )
        assert report.diagnosis_notes == "Additional diagnostic notes here"
        assert len(report.related_issues) == 2
