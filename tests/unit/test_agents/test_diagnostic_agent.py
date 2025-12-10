"""
Unit tests for DiagnosticAgent.

Tests the DiagnosticAgent functionality including:
- Context gathering from workspace
- File extraction from stack traces
- Diagnosis execution
- Report validation
"""

from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest

from asp.agents.base_agent import AgentExecutionError
from asp.agents.diagnostic_agent import DiagnosticAgent
from asp.models.diagnostic import (
    AffectedFile,
    CodeChange,
    DiagnosticInput,
    DiagnosticReport,
    IssueType,
    Severity,
    SuggestedFix,
)
from asp.models.execution import TestFailure, TestResult


class TestDiagnosticAgentInitialization:
    """Tests for DiagnosticAgent initialization."""

    def test_init_with_defaults(self):
        """Test initialization with default parameters."""
        agent = DiagnosticAgent()
        assert agent.db_path is None
        assert agent._llm_client is None
        assert agent.agent_name == "DiagnosticAgent"
        assert agent.agent_version == "1.0.0"

    def test_init_with_db_path(self):
        """Test initialization with database path."""
        db_path = Path("/tmp/test.db")
        agent = DiagnosticAgent(db_path=db_path)
        assert agent.db_path == db_path

    def test_init_with_llm_client(self):
        """Test initialization with custom LLM client."""
        mock_client = Mock()
        agent = DiagnosticAgent(llm_client=mock_client)
        assert agent._llm_client == mock_client


class TestStackTraceExtraction:
    """Tests for file extraction from stack traces."""

    @pytest.fixture
    def agent(self):
        """Create a DiagnosticAgent instance."""
        return DiagnosticAgent()

    def test_extract_files_python_standard_format(self, agent, tmp_path):
        """Test extracting files from Python standard traceback format."""
        stack_trace = """
Traceback (most recent call last):
  File "tests/test_calculator.py", line 15, in test_add
    assert add(2, 3) == 5
  File "src/calculator.py", line 7, in add
    return a - b
AssertionError
"""
        files = agent._extract_files_from_stack_trace(stack_trace, tmp_path)

        assert "tests/test_calculator.py" in files
        assert "src/calculator.py" in files

    def test_extract_files_pytest_format(self, agent, tmp_path):
        """Test extracting files from pytest traceback format."""
        stack_trace = """
tests/test_calculator.py:15: AssertionError
src/calculator.py:7: in add
"""
        files = agent._extract_files_from_stack_trace(stack_trace, tmp_path)

        assert "tests/test_calculator.py" in files
        assert "src/calculator.py" in files

    def test_extract_files_removes_duplicates(self, agent, tmp_path):
        """Test that duplicate file paths are removed."""
        stack_trace = """
  File "src/calculator.py", line 7, in add
  File "src/calculator.py", line 10, in subtract
"""
        files = agent._extract_files_from_stack_trace(stack_trace, tmp_path)

        assert len([f for f in files if f == "src/calculator.py"]) == 1

    def test_extract_files_empty_stack_trace(self, agent, tmp_path):
        """Test extracting from empty stack trace."""
        files = agent._extract_files_from_stack_trace("", tmp_path)
        assert files == []


class TestFailureFileExtraction:
    """Tests for file extraction from test failures."""

    @pytest.fixture
    def agent(self):
        """Create a DiagnosticAgent instance."""
        return DiagnosticAgent()

    def test_extract_files_from_failures(self, agent, tmp_path):
        """Test extracting file paths from test failures."""
        test_result = TestResult(
            framework="pytest",
            total_tests=3,
            passed=2,
            failed=1,
            duration_seconds=1.0,
            failures=[
                TestFailure(
                    test_name="test_add",
                    test_file="tests/test_calculator.py",
                    error_type="AssertionError",
                    error_message="assert -1 == 5",
                    stack_trace='File "src/calculator.py", line 7',
                )
            ],
        )

        files = agent._extract_files_from_failures(test_result, tmp_path)

        assert "tests/test_calculator.py" in files
        assert "src/calculator.py" in files

    def test_extract_files_no_failures(self, agent, tmp_path):
        """Test extracting from test result with no failures."""
        test_result = TestResult(
            framework="pytest",
            total_tests=3,
            passed=3,
            failed=0,
            duration_seconds=1.0,
            failures=[],
        )

        files = agent._extract_files_from_failures(test_result, tmp_path)
        assert files == []


class TestContextGathering:
    """Tests for context gathering from workspace."""

    @pytest.fixture
    def agent(self):
        """Create a DiagnosticAgent instance."""
        return DiagnosticAgent()

    @pytest.fixture
    def workspace(self, tmp_path):
        """Create a workspace with source files."""
        # Create source file
        src_dir = tmp_path / "src"
        src_dir.mkdir()
        calc_file = src_dir / "calculator.py"
        calc_file.write_text("def add(a, b):\n    return a - b\n")

        # Create test file
        tests_dir = tmp_path / "tests"
        tests_dir.mkdir()
        test_file = tests_dir / "test_calculator.py"
        test_file.write_text("def test_add():\n    assert add(2, 3) == 5\n")

        return tmp_path

    def test_gather_context_reads_files(self, agent, workspace):
        """Test that context gathering reads source files."""
        test_result = TestResult(
            framework="pytest",
            total_tests=1,
            passed=0,
            failed=1,
            duration_seconds=1.0,
            failures=[
                TestFailure(
                    test_name="test_add",
                    test_file="tests/test_calculator.py",
                    error_type="AssertionError",
                    error_message="assert -1 == 5",
                    stack_trace='File "src/calculator.py", line 2',
                )
            ],
        )

        input_data = DiagnosticInput(
            task_id="REPAIR-001",
            workspace_path=str(workspace),
            test_result=test_result,
            error_type="AssertionError",
            error_message="assert -1 == 5",
            stack_trace='File "src/calculator.py", line 2',
        )

        context = agent._gather_context(input_data)

        assert "tests/test_calculator.py" in context
        assert "src/calculator.py" in context
        assert "return a - b" in context["src/calculator.py"]

    def test_gather_context_includes_provided_files(self, agent, workspace):
        """Test that provided source_files are included."""
        test_result = TestResult(
            framework="pytest",
            total_tests=1,
            passed=1,
            failed=0,
            duration_seconds=1.0,
        )

        input_data = DiagnosticInput(
            task_id="REPAIR-001",
            workspace_path=str(workspace),
            test_result=test_result,
            error_type="Error",
            error_message="msg",
            source_files={"custom/file.py": "custom content"},
        )

        context = agent._gather_context(input_data)

        assert "custom/file.py" in context
        assert context["custom/file.py"] == "custom content"

    def test_gather_context_nonexistent_workspace(self, agent):
        """Test context gathering with nonexistent workspace."""
        test_result = TestResult(
            framework="pytest",
            total_tests=1,
            passed=1,
            failed=0,
            duration_seconds=1.0,
        )

        input_data = DiagnosticInput(
            task_id="REPAIR-001",
            workspace_path="/nonexistent/path",
            test_result=test_result,
            error_type="Error",
            error_message="msg",
        )

        context = agent._gather_context(input_data)
        assert context == {}


class TestSourceFileFormatting:
    """Tests for source file formatting."""

    @pytest.fixture
    def agent(self):
        """Create a DiagnosticAgent instance."""
        return DiagnosticAgent()

    def test_format_source_files(self, agent):
        """Test formatting source files for prompt."""
        context = {
            "src/calculator.py": "def add(a, b):\n    return a - b",
            "tests/test_calc.py": "def test_add():\n    assert add(2, 3) == 5",
        }

        formatted = agent._format_source_files(context)

        assert "### src/calculator.py" in formatted
        assert "### tests/test_calc.py" in formatted
        assert "def add(a, b)" in formatted
        assert "```" in formatted  # Code blocks

    def test_format_source_files_empty(self, agent):
        """Test formatting with no files."""
        formatted = agent._format_source_files({})
        assert "No source files available" in formatted

    def test_format_source_files_truncates_large(self, agent):
        """Test that large files are truncated."""
        context = {
            "large_file.py": "x" * 15000,  # Larger than 10000 limit
        }

        formatted = agent._format_source_files(context)

        assert "truncated" in formatted
        assert len(formatted) < 15000


class TestJSONExtraction:
    """Tests for JSON content extraction."""

    @pytest.fixture
    def agent(self):
        """Create a DiagnosticAgent instance."""
        return DiagnosticAgent()

    def test_extract_json_from_dict(self, agent):
        """Test extracting JSON when already a dict."""
        data = {"key": "value"}
        result = agent._extract_json_content(data)
        assert result == data

    def test_extract_json_from_string(self, agent):
        """Test extracting JSON from string."""
        data = '{"key": "value"}'
        result = agent._extract_json_content(data)
        assert result == {"key": "value"}

    def test_extract_json_from_markdown_fence(self, agent):
        """Test extracting JSON from markdown code fence."""
        data = """Some text
```json
{"key": "value"}
```
More text"""
        result = agent._extract_json_content(data)
        assert result == {"key": "value"}

    def test_extract_json_invalid_raises(self, agent):
        """Test that invalid JSON raises error."""
        with pytest.raises(AgentExecutionError, match="non-JSON response"):
            agent._extract_json_content("not valid json")


class TestReportValidation:
    """Tests for diagnostic report validation."""

    @pytest.fixture
    def agent(self):
        """Create a DiagnosticAgent instance."""
        return DiagnosticAgent()

    @pytest.fixture
    def valid_report(self):
        """Create a valid diagnostic report."""
        return DiagnosticReport(
            task_id="REPAIR-001",
            issue_type=IssueType.LOGIC_ERROR,
            severity=Severity.HIGH,
            root_cause="The add function uses subtraction instead of addition",
            affected_files=[
                AffectedFile(
                    path="src/calculator.py",
                    line_start=5,
                    line_end=7,
                    code_snippet="def add(a, b):\n    return a - b",
                    issue_description="Wrong operator in add function",
                )
            ],
            suggested_fixes=[
                SuggestedFix(
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
            ],
            confidence=0.95,
        )

    def test_validate_valid_report(self, agent, valid_report):
        """Test validation passes for valid report."""
        # Should not raise
        agent._validate_diagnostic_report(valid_report)

    def test_validate_no_affected_files_fails(self, agent):
        """Test validation fails with no affected files."""
        # Create report that would fail validation (caught by Pydantic first)
        # but we test the agent validation separately
        report = MagicMock()
        report.affected_files = []
        report.suggested_fixes = [MagicMock()]

        with pytest.raises(AgentExecutionError, match="at least one affected file"):
            agent._validate_diagnostic_report(report)

    def test_validate_no_suggested_fixes_fails(self, agent):
        """Test validation fails with no suggested fixes."""
        report = MagicMock()
        report.affected_files = [MagicMock()]
        report.suggested_fixes = []

        with pytest.raises(AgentExecutionError, match="at least one suggested fix"):
            agent._validate_diagnostic_report(report)

    def test_validate_fix_with_no_changes_fails(self, agent):
        """Test validation fails when fix has no changes."""
        fix = MagicMock()
        fix.fix_id = "FIX-001"
        fix.changes = []

        report = MagicMock()
        report.affected_files = [MagicMock()]
        report.suggested_fixes = [fix]

        with pytest.raises(
            AgentExecutionError, match="must have at least one code change"
        ):
            agent._validate_diagnostic_report(report)

    def test_validate_fix_with_empty_search_text_fails(self, agent):
        """Test validation fails when change has empty search text."""
        change = MagicMock()
        change.search_text = ""
        change.replace_text = "new"

        fix = MagicMock()
        fix.fix_id = "FIX-001"
        fix.changes = [change]

        report = MagicMock()
        report.affected_files = [MagicMock()]
        report.suggested_fixes = [fix]

        with pytest.raises(AgentExecutionError, match="empty search_text"):
            agent._validate_diagnostic_report(report)

    def test_validate_fix_with_identical_search_replace_fails(self, agent):
        """Test validation fails when search equals replace."""
        change = MagicMock()
        change.search_text = "same"
        change.replace_text = "same"

        fix = MagicMock()
        fix.fix_id = "FIX-001"
        fix.changes = [change]

        report = MagicMock()
        report.affected_files = [MagicMock()]
        report.suggested_fixes = [fix]

        with pytest.raises(AgentExecutionError, match="identical search and replace"):
            agent._validate_diagnostic_report(report)

    def test_validate_duplicate_fix_ids_fails(self, agent):
        """Test validation fails with duplicate fix IDs."""
        change = MagicMock()
        change.search_text = "old"
        change.replace_text = "new"

        fix1 = MagicMock()
        fix1.fix_id = "FIX-001"
        fix1.changes = [change]

        fix2 = MagicMock()
        fix2.fix_id = "FIX-001"  # Duplicate!
        fix2.changes = [change]

        report = MagicMock()
        report.affected_files = [MagicMock()]
        report.suggested_fixes = [fix1, fix2]

        with pytest.raises(AgentExecutionError, match="Duplicate fix IDs"):
            agent._validate_diagnostic_report(report)


class TestDiagnosticExecution:
    """Tests for full diagnostic execution."""

    @pytest.fixture
    def mock_llm_client(self):
        """Create a mock LLM client."""
        return MagicMock()

    @pytest.fixture
    def agent(self, mock_llm_client):
        """Create a DiagnosticAgent with mock LLM client."""
        return DiagnosticAgent(llm_client=mock_llm_client)

    @pytest.fixture
    def valid_llm_response(self):
        """Create a valid LLM response."""
        return {
            "content": {
                "task_id": "REPAIR-001",
                "issue_type": "logic_error",
                "severity": "High",
                "root_cause": "The add function uses subtraction instead of addition operator",
                "affected_files": [
                    {
                        "path": "src/calculator.py",
                        "line_start": 5,
                        "line_end": 7,
                        "code_snippet": "def add(a, b):\n    return a - b",
                        "issue_description": "Wrong operator in add function",
                    }
                ],
                "suggested_fixes": [
                    {
                        "fix_id": "FIX-001",
                        "description": "Change subtraction to addition operator",
                        "confidence": 0.95,
                        "changes": [
                            {
                                "file_path": "src/calculator.py",
                                "search_text": "return a - b",
                                "replace_text": "return a + b",
                            }
                        ],
                    }
                ],
                "confidence": 0.95,
            },
            "usage": {"input_tokens": 100, "output_tokens": 200},
        }

    def test_execute_success(
        self, agent, mock_llm_client, valid_llm_response, tmp_path
    ):
        """Test successful diagnostic execution."""
        mock_llm_client.call_with_retry.return_value = valid_llm_response

        # Create workspace files
        src_dir = tmp_path / "src"
        src_dir.mkdir()
        (src_dir / "calculator.py").write_text("def add(a, b):\n    return a - b\n")

        test_result = TestResult(
            framework="pytest",
            total_tests=1,
            passed=0,
            failed=1,
            duration_seconds=1.0,
            failures=[
                TestFailure(
                    test_name="test_add",
                    test_file="tests/test_calc.py",
                    error_type="AssertionError",
                    error_message="assert -1 == 5",
                )
            ],
        )

        input_data = DiagnosticInput(
            task_id="REPAIR-001",
            workspace_path=str(tmp_path),
            test_result=test_result,
            error_type="AssertionError",
            error_message="assert -1 == 5",
            stack_trace="",
        )

        report = agent.execute(input_data)

        assert report.task_id == "REPAIR-001"
        assert report.issue_type == IssueType.LOGIC_ERROR
        assert report.severity == Severity.HIGH
        assert report.confidence == 0.95
        assert len(report.suggested_fixes) == 1
        assert report.best_fix.fix_id == "FIX-001"

    def test_execute_prompt_not_found(self, agent, mock_llm_client, tmp_path):
        """Test execution fails when prompt template is missing."""
        test_result = TestResult(
            framework="pytest",
            total_tests=1,
            passed=1,
            failed=0,
            duration_seconds=1.0,
        )

        input_data = DiagnosticInput(
            task_id="REPAIR-001",
            workspace_path=str(tmp_path),
            test_result=test_result,
            error_type="Error",
            error_message="msg",
        )

        # Mock load_prompt to raise FileNotFoundError
        with patch.object(
            agent, "load_prompt", side_effect=FileNotFoundError("not found")
        ):
            with pytest.raises(AgentExecutionError, match="Prompt template not found"):
                agent.execute(input_data)

    def test_execute_invalid_llm_response(self, agent, mock_llm_client, tmp_path):
        """Test execution fails with invalid LLM response."""
        mock_llm_client.call_with_retry.return_value = {
            "content": {"invalid": "response"}
        }

        test_result = TestResult(
            framework="pytest",
            total_tests=1,
            passed=1,
            failed=0,
            duration_seconds=1.0,
        )

        input_data = DiagnosticInput(
            task_id="REPAIR-001",
            workspace_path=str(tmp_path),
            test_result=test_result,
            error_type="Error",
            error_message="msg",
        )

        with pytest.raises(AgentExecutionError):
            agent.execute(input_data)
