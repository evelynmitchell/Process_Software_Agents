"""
Unit tests for RepairAgent.

Tests the RepairAgent functionality including:
- Reading affected files
- Generating repairs
- Handling previous attempts
- Output validation
"""

from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest

from asp.agents.base_agent import AgentExecutionError
from asp.agents.repair_agent import RepairAgent
from asp.models.diagnostic import (
    AffectedFile,
    CodeChange,
    DiagnosticReport,
    IssueType,
    Severity,
    SuggestedFix,
)
from asp.models.execution import TestResult
from asp.models.repair import RepairAttempt, RepairInput, RepairOutput


class TestRepairAgentInitialization:
    """Tests for RepairAgent initialization."""

    def test_init_with_defaults(self):
        """Test initialization with default parameters."""
        agent = RepairAgent()
        assert agent.db_path is None
        assert agent._llm_client is None
        assert agent.agent_name == "RepairAgent"
        assert agent.agent_version == "1.0.0"

    def test_init_with_db_path(self):
        """Test initialization with database path."""
        db_path = Path("/tmp/test.db")
        agent = RepairAgent(db_path=db_path)
        assert agent.db_path == db_path

    def test_init_with_llm_client(self):
        """Test initialization with custom LLM client."""
        mock_client = Mock()
        agent = RepairAgent(llm_client=mock_client)
        assert agent._llm_client == mock_client


class TestReadAffectedFiles:
    """Tests for reading affected files."""

    @pytest.fixture
    def agent(self):
        """Create a RepairAgent instance."""
        return RepairAgent()

    @pytest.fixture
    def diagnostic_report(self):
        """Create a diagnostic report with affected files."""
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
                    code_snippet="return a - b",
                    issue_description="Wrong operator",
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

    def test_read_affected_files(self, agent, diagnostic_report, tmp_path):
        """Test reading affected files from workspace."""
        # Create source file
        src_dir = tmp_path / "src"
        src_dir.mkdir()
        calc_file = src_dir / "calculator.py"
        calc_file.write_text("def add(a, b):\n    return a - b\n")

        input_data = RepairInput(
            task_id="REPAIR-001",
            workspace_path=str(tmp_path),
            diagnostic=diagnostic_report,
        )

        context = agent._read_affected_files(input_data)

        assert "src/calculator.py" in context
        assert "return a - b" in context["src/calculator.py"]

    def test_read_includes_provided_files(self, agent, diagnostic_report, tmp_path):
        """Test that provided source_files are included."""
        input_data = RepairInput(
            task_id="REPAIR-001",
            workspace_path=str(tmp_path),
            diagnostic=diagnostic_report,
            source_files={"custom/file.py": "custom content"},
        )

        context = agent._read_affected_files(input_data)

        assert "custom/file.py" in context
        assert context["custom/file.py"] == "custom content"

    def test_read_nonexistent_workspace(self, agent, diagnostic_report):
        """Test reading from nonexistent workspace."""
        input_data = RepairInput(
            task_id="REPAIR-001",
            workspace_path="/nonexistent/path",
            diagnostic=diagnostic_report,
        )

        context = agent._read_affected_files(input_data)
        assert context == {}


class TestFormatPreviousAttempts:
    """Tests for formatting previous attempts."""

    @pytest.fixture
    def agent(self):
        """Create a RepairAgent instance."""
        return RepairAgent()

    def test_format_no_attempts(self, agent):
        """Test formatting with no previous attempts."""
        result = agent._format_previous_attempts([])
        assert "No previous repair attempts" in result

    def test_format_with_attempts(self, agent):
        """Test formatting with previous attempts."""
        code_change = CodeChange(
            file_path="src/calculator.py",
            search_text="return a - b",
            replace_text="return a + b",
            description="Fix operator",
        )
        attempt = RepairAttempt(
            attempt_number=1,
            changes_made=[code_change],
            test_result=TestResult(
                framework="pytest",
                total_tests=5,
                passed=3,
                failed=2,
                duration_seconds=1.0,
            ),
            why_failed="Fix did not address all issues",
        )

        result = agent._format_previous_attempts([attempt])

        assert "Attempt 1" in result
        assert "FAILED" in result
        assert "src/calculator.py" in result
        assert "Passed: 3" in result
        assert "Failed: 2" in result
        assert "Fix did not address all issues" in result


class TestFormatSourceFiles:
    """Tests for formatting source files."""

    @pytest.fixture
    def agent(self):
        """Create a RepairAgent instance."""
        return RepairAgent()

    def test_format_source_files(self, agent):
        """Test formatting source files."""
        context = {
            "src/calculator.py": "def add(a, b):\n    return a - b",
        }

        result = agent._format_source_files(context)

        assert "### src/calculator.py" in result
        assert "def add(a, b)" in result
        assert "```" in result

    def test_format_empty_context(self, agent):
        """Test formatting empty context."""
        result = agent._format_source_files({})
        assert "No source files available" in result

    def test_format_truncates_large_files(self, agent):
        """Test that large files are truncated."""
        context = {
            "large.py": "x" * 15000,
        }

        result = agent._format_source_files(context)

        assert "truncated" in result
        assert len(result) < 15000


class TestJSONExtraction:
    """Tests for JSON content extraction."""

    @pytest.fixture
    def agent(self):
        """Create a RepairAgent instance."""
        return RepairAgent()

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


class TestOutputValidation:
    """Tests for repair output validation."""

    @pytest.fixture
    def agent(self):
        """Create a RepairAgent instance."""
        return RepairAgent()

    @pytest.fixture
    def valid_output(self):
        """Create a valid repair output."""
        return RepairOutput(
            task_id="REPAIR-001",
            strategy="Apply direct operator fix from diagnostic",
            changes=[
                CodeChange(
                    file_path="src/calculator.py",
                    search_text="return a - b",
                    replace_text="return a + b",
                )
            ],
            explanation="Changing the operator from - to + will fix the add function",
            confidence=0.95,
        )

    def test_validate_valid_output(self, agent, valid_output):
        """Test validation passes for valid output."""
        # Should not raise
        agent._validate_repair_output(valid_output)

    def test_validate_no_changes_fails(self, agent):
        """Test validation fails with no changes."""
        output = MagicMock()
        output.changes = []

        with pytest.raises(AgentExecutionError, match="at least one code change"):
            agent._validate_repair_output(output)

    def test_validate_empty_search_text_fails(self, agent):
        """Test validation fails with empty search text."""
        change = MagicMock()
        change.search_text = ""
        change.replace_text = "new"

        output = MagicMock()
        output.changes = [change]

        with pytest.raises(AgentExecutionError, match="empty search_text"):
            agent._validate_repair_output(output)

    def test_validate_identical_search_replace_fails(self, agent):
        """Test validation fails when search equals replace."""
        change = MagicMock()
        change.search_text = "same"
        change.replace_text = "same"

        output = MagicMock()
        output.changes = [change]

        with pytest.raises(AgentExecutionError, match="identical search and replace"):
            agent._validate_repair_output(output)

    def test_validate_low_confidence_warns(self, agent, caplog):
        """Test that low confidence logs a warning."""
        output = RepairOutput(
            task_id="REPAIR-001",
            strategy="Low confidence repair attempt",
            changes=[
                CodeChange(
                    file_path="src/test.py",
                    search_text="old",
                    replace_text="new",
                )
            ],
            explanation="This is a low confidence repair attempt",
            confidence=0.3,
        )

        import logging

        with caplog.at_level(logging.WARNING):
            agent._validate_repair_output(output)

        assert "low confidence" in caplog.text.lower()


class TestRepairExecution:
    """Tests for full repair execution."""

    @pytest.fixture
    def mock_llm_client(self):
        """Create a mock LLM client."""
        return MagicMock()

    @pytest.fixture
    def agent(self, mock_llm_client):
        """Create a RepairAgent with mock LLM client."""
        return RepairAgent(llm_client=mock_llm_client)

    @pytest.fixture
    def diagnostic_report(self):
        """Create a diagnostic report."""
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
                    code_snippet="return a - b",
                    issue_description="Wrong operator",
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

    @pytest.fixture
    def valid_llm_response(self):
        """Create a valid LLM response."""
        return {
            "content": {
                "task_id": "REPAIR-001",
                "strategy": "Apply direct operator fix based on diagnostic recommendation",
                "changes": [
                    {
                        "file_path": "src/calculator.py",
                        "search_text": "return a - b",
                        "replace_text": "return a + b",
                    }
                ],
                "explanation": "Changing the operator from - to + will fix the add function as identified in the diagnostic",
                "confidence": 0.95,
                "based_on_fix_id": "FIX-001",
            },
            "usage": {"input_tokens": 100, "output_tokens": 200},
        }

    def test_execute_success(
        self, agent, mock_llm_client, diagnostic_report, valid_llm_response, tmp_path
    ):
        """Test successful repair execution."""
        mock_llm_client.call_with_retry.return_value = valid_llm_response

        # Create workspace files
        src_dir = tmp_path / "src"
        src_dir.mkdir()
        (src_dir / "calculator.py").write_text("def add(a, b):\n    return a - b\n")

        input_data = RepairInput(
            task_id="REPAIR-001",
            workspace_path=str(tmp_path),
            diagnostic=diagnostic_report,
        )

        output = agent.execute(input_data)

        assert output.task_id == "REPAIR-001"
        assert output.confidence == 0.95
        assert len(output.changes) == 1
        assert output.based_on_fix_id == "FIX-001"

    def test_execute_with_previous_attempts(
        self, agent, mock_llm_client, diagnostic_report, valid_llm_response, tmp_path
    ):
        """Test execution with previous failed attempts."""
        mock_llm_client.call_with_retry.return_value = valid_llm_response

        # Create previous failed attempt
        previous_attempt = RepairAttempt(
            attempt_number=1,
            changes_made=[
                CodeChange(
                    file_path="src/calculator.py",
                    search_text="a - b",
                    replace_text="a + b",
                )
            ],
            test_result=TestResult(
                framework="pytest",
                total_tests=5,
                passed=3,
                failed=2,
                duration_seconds=1.0,
            ),
            why_failed="Match was not unique enough",
        )

        input_data = RepairInput(
            task_id="REPAIR-001",
            workspace_path=str(tmp_path),
            diagnostic=diagnostic_report,
            previous_attempts=[previous_attempt],
        )

        output = agent.execute(input_data)

        assert output is not None
        # Verify prompt included previous attempts
        call_args = mock_llm_client.call_with_retry.call_args
        prompt = call_args.kwargs["prompt"]
        assert "Attempt 1" in prompt

    def test_execute_prompt_not_found(
        self, agent, mock_llm_client, diagnostic_report, tmp_path
    ):
        """Test execution fails when prompt template is missing."""
        input_data = RepairInput(
            task_id="REPAIR-001",
            workspace_path=str(tmp_path),
            diagnostic=diagnostic_report,
        )

        # Mock load_prompt to raise FileNotFoundError
        with patch.object(
            agent, "load_prompt", side_effect=FileNotFoundError("not found")
        ):
            with pytest.raises(AgentExecutionError, match="Prompt template not found"):
                agent.execute(input_data)

    def test_execute_invalid_llm_response(
        self, agent, mock_llm_client, diagnostic_report, tmp_path
    ):
        """Test execution fails with invalid LLM response."""
        mock_llm_client.call_with_retry.return_value = {
            "content": {"invalid": "response"}
        }

        input_data = RepairInput(
            task_id="REPAIR-001",
            workspace_path=str(tmp_path),
            diagnostic=diagnostic_report,
        )

        with pytest.raises(AgentExecutionError):
            agent.execute(input_data)
