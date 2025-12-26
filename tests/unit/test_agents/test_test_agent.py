"""
Unit tests for TestAgent.

Tests the TestAgent functionality including:
- Initialization with various configurations
- Test generation and execution (sync and async)
- Validation of test reports
- Error handling for LLM failures and invalid responses
- Edge cases for defect handling and status validation

Author: ASP Development Team
Date: December 23, 2025
"""

import json
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest

from asp.agents.base_agent import AgentExecutionError
from asp.agents.test_agent import TestAgent
from asp.models.code import GeneratedCode, GeneratedFile
from asp.models.design import (
    ComponentLogic,
    DesignReviewChecklistItem,
    DesignSpecification,
)
from asp.models.test import TestInput, TestReport

# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def mock_generated_code():
    """Create a mock GeneratedCode instance."""
    return GeneratedCode(
        task_id="TEST-001",
        files=[
            GeneratedFile(
                file_path="src/calculator.py",
                content="def add(a, b): return a + b",
                file_type="source",
                semantic_unit_id="SU-001",
                component_id="COMP-001",
                description="Calculator module with basic arithmetic operations",
            )
        ],
        file_structure={"src": ["calculator.py"]},
        dependencies=[],
        implementation_notes="Simple calculator implementation with add, subtract, multiply, and divide operations for basic arithmetic",
        agent_version="1.0.0",
    )


@pytest.fixture
def mock_design_spec():
    """Create a mock DesignSpecification instance."""
    return DesignSpecification(
        task_id="TEST-001",
        architecture_overview="Simple calculator API with basic arithmetic operations for testing",
        technology_stack={
            "language": "Python 3.12",
            "framework": "None",
        },
        component_logic=[
            ComponentLogic(
                component_name="Calculator",
                semantic_unit_id="SU-001",
                responsibility="Basic arithmetic operations including add, subtract, multiply, divide",
                interfaces=[
                    {
                        "method": "add",
                        "parameters": {"a": "int", "b": "int"},
                        "returns": "int",
                        "description": "Add two numbers",
                    }
                ],
                dependencies=[],
                implementation_notes="Simple implementation",
            )
        ],
        design_review_checklist=[
            DesignReviewChecklistItem(
                category="Functionality",
                description="All operations must handle edge cases",
                validation_criteria="Test with zero, negative, and large numbers",
                severity="High",
            ),
            DesignReviewChecklistItem(
                category="Functionality",
                description="Division must handle zero divisor",
                validation_criteria="Return error for division by zero",
                severity="Critical",
            ),
            DesignReviewChecklistItem(
                category="Code Quality",
                description="Functions must have type hints",
                validation_criteria="All function parameters and return types annotated",
                severity="Medium",
            ),
            DesignReviewChecklistItem(
                category="Documentation",
                description="All functions must have docstrings",
                validation_criteria="Docstrings with description and examples",
                severity="Low",
            ),
            DesignReviewChecklistItem(
                category="Testing",
                description="Unit tests for all functions",
                validation_criteria="At least 80% code coverage",
                severity="High",
            ),
        ],
        assumptions=["Python 3.12+ environment"],
    )


@pytest.fixture
def mock_test_input(mock_generated_code, mock_design_spec):
    """Create a mock TestInput instance."""
    return TestInput(
        task_id="TEST-001",
        generated_code=mock_generated_code,
        design_specification=mock_design_spec,
        test_framework="pytest",
        coverage_target=80.0,
    )


@pytest.fixture
def mock_pass_response():
    """Mock LLM response for a passing test report."""
    return {
        "content": {
            "task_id": "TEST-001",
            "test_status": "PASS",
            "build_successful": True,
            "build_errors": [],
            "test_summary": {
                "total_tests": 5,
                "passed": 5,
                "failed": 0,
                "skipped": 0,
            },
            "coverage_percentage": 95.0,
            "defects_found": [],
            "total_tests_generated": 5,
            "test_files_created": ["tests/test_calculator.py"],
            "test_timestamp": "2025-12-23T12:00:00Z",
            "test_duration_seconds": 2.5,
        }
    }


@pytest.fixture
def mock_fail_response():
    """Mock LLM response for a failing test report with defects."""
    return {
        "content": {
            "task_id": "TEST-001",
            "test_status": "FAIL",
            "build_successful": True,
            "build_errors": [],
            "test_summary": {
                "total_tests": 5,
                "passed": 3,
                "failed": 2,
                "skipped": 0,
            },
            "coverage_percentage": 75.0,
            "defects_found": [
                {
                    "defect_id": "TEST-DEFECT-001",
                    "defect_type": "6_Conventional_Code_Bug",
                    "severity": "High",
                    "description": "Add function returns wrong result for negative numbers",
                    "evidence": "AssertionError: Expected -5, got 5",
                    "phase_injected": "Code",
                    "phase_removed": "Test",
                    "file_path": "src/calculator.py",
                    "line_number": 1,
                },
                {
                    "defect_id": "TEST-DEFECT-002",
                    "defect_type": "6_Conventional_Code_Bug",
                    "severity": "Medium",
                    "description": "Missing type validation for inputs",
                    "evidence": "TypeError: unsupported operand type(s)",
                    "phase_injected": "Code",
                    "phase_removed": "Test",
                },
            ],
            "total_tests_generated": 5,
            "test_files_created": ["tests/test_calculator.py"],
            "test_timestamp": "2025-12-23T12:00:00Z",
            "test_duration_seconds": 3.1,
        }
    }


@pytest.fixture
def mock_build_failed_response():
    """Mock LLM response for a build failure."""
    return {
        "content": {
            "task_id": "TEST-001",
            "test_status": "BUILD_FAILED",
            "build_successful": False,
            "build_errors": ["SyntaxError: invalid syntax", "IndentationError"],
            "test_summary": {
                "total_tests": 0,
                "passed": 0,
                "failed": 0,
                "skipped": 0,
            },
            "coverage_percentage": None,
            "defects_found": [],
            "total_tests_generated": 0,
            "test_files_created": [],
            "test_timestamp": "2025-12-23T12:00:00Z",
            "test_duration_seconds": 0.5,
        }
    }


# =============================================================================
# Initialization Tests
# =============================================================================


class TestTestAgentInitialization:
    """Tests for TestAgent initialization."""

    def test_init_with_defaults(self):
        """Test initialization with default parameters."""
        agent = TestAgent()
        assert agent.db_path is None
        assert agent._llm_client is None
        assert agent.agent_name == "TestAgent"
        assert agent.agent_version == "1.0.0"

    def test_init_with_db_path(self):
        """Test initialization with database path."""
        db_path = Path("/tmp/test.db")
        agent = TestAgent(db_path=db_path)
        assert agent.db_path == db_path

    def test_init_with_llm_client(self):
        """Test initialization with custom LLM client."""
        mock_client = Mock()
        agent = TestAgent(llm_client=mock_client)
        assert agent._llm_client == mock_client

    def test_init_with_all_parameters(self):
        """Test initialization with all parameters."""
        db_path = Path("/tmp/test.db")
        mock_client = Mock()
        agent = TestAgent(db_path=db_path, llm_client=mock_client)
        assert agent.db_path == db_path
        assert agent._llm_client == mock_client


# =============================================================================
# Happy Path Tests - Sync Execution
# =============================================================================


class TestTestAgentExecuteHappyPath:
    """Tests for successful TestAgent execution."""

    @pytest.fixture
    def agent(self):
        """Create a TestAgent with mocked LLM client."""
        mock_client = Mock()
        return TestAgent(llm_client=mock_client)

    @patch.object(TestAgent, "load_prompt")
    @patch.object(TestAgent, "call_llm")
    @patch("asp.agents.test_agent.write_artifact_json")
    @patch("asp.agents.test_agent.write_artifact_markdown")
    @patch("asp.agents.test_agent.is_git_repository", return_value=False)
    def test_execute_pass_status(
        self,
        mock_is_git,
        mock_write_md,
        mock_write_json,
        mock_call_llm,
        mock_load_prompt,
        agent,
        mock_test_input,
        mock_pass_response,
    ):
        """Test execution with PASS status."""
        mock_load_prompt.return_value = "test prompt template"
        mock_call_llm.return_value = mock_pass_response
        mock_write_json.return_value = Path("/tmp/test_report.json")
        mock_write_md.return_value = Path("/tmp/test_report.md")

        result = agent.execute(mock_test_input)

        assert isinstance(result, TestReport)
        assert result.test_status == "PASS"
        assert result.build_successful is True
        assert result.test_summary["passed"] == 5
        assert result.coverage_percentage == 95.0
        assert len(result.defects_found) == 0

    @patch.object(TestAgent, "load_prompt")
    @patch.object(TestAgent, "call_llm")
    @patch("asp.agents.test_agent.write_artifact_json")
    @patch("asp.agents.test_agent.write_artifact_markdown")
    @patch("asp.agents.test_agent.is_git_repository", return_value=False)
    def test_execute_fail_status_with_defects(
        self,
        mock_is_git,
        mock_write_md,
        mock_write_json,
        mock_call_llm,
        mock_load_prompt,
        agent,
        mock_test_input,
        mock_fail_response,
    ):
        """Test execution with FAIL status and defects."""
        mock_load_prompt.return_value = "test prompt template"
        mock_call_llm.return_value = mock_fail_response
        mock_write_json.return_value = Path("/tmp/test_report.json")
        mock_write_md.return_value = Path("/tmp/test_report.md")

        result = agent.execute(mock_test_input)

        assert isinstance(result, TestReport)
        assert result.test_status == "FAIL"
        assert result.build_successful is True
        assert len(result.defects_found) == 2
        assert result.high_defects == 1
        assert result.medium_defects == 1

    @patch.object(TestAgent, "load_prompt")
    @patch.object(TestAgent, "call_llm")
    @patch("asp.agents.test_agent.write_artifact_json")
    @patch("asp.agents.test_agent.write_artifact_markdown")
    @patch("asp.agents.test_agent.is_git_repository", return_value=False)
    def test_execute_build_failed_status(
        self,
        mock_is_git,
        mock_write_md,
        mock_write_json,
        mock_call_llm,
        mock_load_prompt,
        agent,
        mock_test_input,
        mock_build_failed_response,
    ):
        """Test execution with BUILD_FAILED status."""
        mock_load_prompt.return_value = "test prompt template"
        mock_call_llm.return_value = mock_build_failed_response
        mock_write_json.return_value = Path("/tmp/test_report.json")
        mock_write_md.return_value = Path("/tmp/test_report.md")

        result = agent.execute(mock_test_input)

        assert isinstance(result, TestReport)
        assert result.test_status == "BUILD_FAILED"
        assert result.build_successful is False
        assert len(result.build_errors) == 2

    @patch.object(TestAgent, "load_prompt")
    @patch.object(TestAgent, "call_llm")
    @patch("asp.agents.test_agent.write_artifact_json")
    @patch("asp.agents.test_agent.write_artifact_markdown")
    @patch("asp.agents.test_agent.is_git_repository", return_value=True)
    @patch("asp.agents.test_agent.git_commit_artifact")
    def test_execute_with_git_commit(
        self,
        mock_git_commit,
        mock_is_git,
        mock_write_md,
        mock_write_json,
        mock_call_llm,
        mock_load_prompt,
        agent,
        mock_test_input,
        mock_pass_response,
    ):
        """Test execution commits artifacts when in git repository."""
        mock_load_prompt.return_value = "test prompt template"
        mock_call_llm.return_value = mock_pass_response
        mock_write_json.return_value = Path("/tmp/test_report.json")
        mock_write_md.return_value = Path("/tmp/test_report.md")
        mock_git_commit.return_value = "abc123"

        result = agent.execute(mock_test_input)

        assert isinstance(result, TestReport)
        mock_git_commit.assert_called_once()


# =============================================================================
# Error Path Tests
# =============================================================================


class TestTestAgentExecuteErrorPaths:
    """Tests for error handling in TestAgent execution."""

    @pytest.fixture
    def agent(self):
        """Create a TestAgent with mocked LLM client."""
        mock_client = Mock()
        return TestAgent(llm_client=mock_client)

    @patch.object(TestAgent, "load_prompt")
    def test_execute_prompt_not_found(self, mock_load_prompt, agent, mock_test_input):
        """Test error when prompt template is not found."""
        mock_load_prompt.side_effect = FileNotFoundError("Prompt not found")

        with pytest.raises(AgentExecutionError) as exc_info:
            agent.execute(mock_test_input)

        assert "Prompt template not found" in str(exc_info.value)

    @patch.object(TestAgent, "load_prompt")
    @patch.object(TestAgent, "call_llm")
    def test_execute_llm_returns_non_json_string(
        self, mock_call_llm, mock_load_prompt, agent, mock_test_input
    ):
        """Test error when LLM returns non-JSON string."""
        mock_load_prompt.return_value = "test prompt"
        mock_call_llm.return_value = {"content": "This is not JSON at all"}

        with pytest.raises(AgentExecutionError) as exc_info:
            agent.execute(mock_test_input)

        assert "non-JSON response" in str(exc_info.value)

    @patch.object(TestAgent, "load_prompt")
    @patch.object(TestAgent, "call_llm")
    def test_execute_llm_returns_invalid_json_in_fence(
        self, mock_call_llm, mock_load_prompt, agent, mock_test_input
    ):
        """Test error when LLM returns invalid JSON in markdown fence."""
        mock_load_prompt.return_value = "test prompt"
        mock_call_llm.return_value = {"content": "```json\n{invalid json here}\n```"}

        with pytest.raises(AgentExecutionError) as exc_info:
            agent.execute(mock_test_input)

        assert "Failed to parse JSON from markdown fence" in str(exc_info.value)

    @patch.object(TestAgent, "load_prompt")
    @patch.object(TestAgent, "call_llm")
    def test_execute_llm_returns_non_dict(
        self, mock_call_llm, mock_load_prompt, agent, mock_test_input
    ):
        """Test error when LLM returns non-dict after parsing."""
        mock_load_prompt.return_value = "test prompt"
        mock_call_llm.return_value = {"content": ["list", "not", "dict"]}

        with pytest.raises(AgentExecutionError) as exc_info:
            agent.execute(mock_test_input)

        assert "non-dict response" in str(exc_info.value)

    @patch.object(TestAgent, "load_prompt")
    @patch.object(TestAgent, "call_llm")
    def test_execute_validation_error_missing_fields(
        self, mock_call_llm, mock_load_prompt, agent, mock_test_input
    ):
        """Test error when response is missing required fields."""
        mock_load_prompt.return_value = "test prompt"
        mock_call_llm.return_value = {
            "content": {
                "task_id": "TEST-001",
                # Missing required fields
            }
        }

        with pytest.raises(AgentExecutionError) as exc_info:
            agent.execute(mock_test_input)

        assert "Failed to validate TestReport" in str(exc_info.value)

    @patch.object(TestAgent, "load_prompt")
    @patch.object(TestAgent, "call_llm")
    def test_execute_llm_exception(
        self, mock_call_llm, mock_load_prompt, agent, mock_test_input
    ):
        """Test error when LLM call raises exception."""
        mock_load_prompt.return_value = "test prompt"
        mock_call_llm.side_effect = Exception("LLM service unavailable")

        with pytest.raises(AgentExecutionError) as exc_info:
            agent.execute(mock_test_input)

        assert "Test execution failed" in str(exc_info.value)


# =============================================================================
# JSON Parsing Tests
# =============================================================================


class TestTestAgentJsonParsing:
    """Tests for JSON parsing from LLM responses."""

    @pytest.fixture
    def agent(self):
        """Create a TestAgent with mocked LLM client."""
        mock_client = Mock()
        return TestAgent(llm_client=mock_client)

    @patch.object(TestAgent, "load_prompt")
    @patch.object(TestAgent, "call_llm")
    @patch("asp.agents.test_agent.write_artifact_json")
    @patch("asp.agents.test_agent.write_artifact_markdown")
    @patch("asp.agents.test_agent.is_git_repository", return_value=False)
    def test_parse_json_from_markdown_fence(
        self,
        mock_is_git,
        mock_write_md,
        mock_write_json,
        mock_call_llm,
        mock_load_prompt,
        agent,
        mock_test_input,
    ):
        """Test parsing JSON from markdown code fence."""
        mock_load_prompt.return_value = "test prompt"
        json_content = {
            "task_id": "TEST-001",
            "test_status": "PASS",
            "build_successful": True,
            "build_errors": [],
            "test_summary": {"total_tests": 1, "passed": 1, "failed": 0, "skipped": 0},
            "defects_found": [],
            "test_timestamp": "2025-12-23T12:00:00Z",
        }
        mock_call_llm.return_value = {
            "content": f"```json\n{json.dumps(json_content)}\n```"
        }
        mock_write_json.return_value = Path("/tmp/test_report.json")
        mock_write_md.return_value = Path("/tmp/test_report.md")

        result = agent.execute(mock_test_input)

        assert result.test_status == "PASS"

    @patch.object(TestAgent, "load_prompt")
    @patch.object(TestAgent, "call_llm")
    @patch("asp.agents.test_agent.write_artifact_json")
    @patch("asp.agents.test_agent.write_artifact_markdown")
    @patch("asp.agents.test_agent.is_git_repository", return_value=False)
    def test_parse_raw_json_string(
        self,
        mock_is_git,
        mock_write_md,
        mock_write_json,
        mock_call_llm,
        mock_load_prompt,
        agent,
        mock_test_input,
    ):
        """Test parsing raw JSON string without markdown fence."""
        mock_load_prompt.return_value = "test prompt"
        json_content = {
            "task_id": "TEST-001",
            "test_status": "PASS",
            "build_successful": True,
            "build_errors": [],
            "test_summary": {"total_tests": 1, "passed": 1, "failed": 0, "skipped": 0},
            "defects_found": [],
            "test_timestamp": "2025-12-23T12:00:00Z",
        }
        mock_call_llm.return_value = {"content": json.dumps(json_content)}
        mock_write_json.return_value = Path("/tmp/test_report.json")
        mock_write_md.return_value = Path("/tmp/test_report.md")

        result = agent.execute(mock_test_input)

        assert result.test_status == "PASS"


# =============================================================================
# Auto-correction Tests
# =============================================================================


class TestTestAgentAutoCorrection:
    """Tests for auto-correction of test_status when build fails."""

    @pytest.fixture
    def agent(self):
        """Create a TestAgent with mocked LLM client."""
        mock_client = Mock()
        return TestAgent(llm_client=mock_client)

    @patch.object(TestAgent, "load_prompt")
    @patch.object(TestAgent, "call_llm")
    @patch("asp.agents.test_agent.write_artifact_json")
    @patch("asp.agents.test_agent.write_artifact_markdown")
    @patch("asp.agents.test_agent.is_git_repository", return_value=False)
    def test_auto_correct_status_when_build_failed(
        self,
        mock_is_git,
        mock_write_md,
        mock_write_json,
        mock_call_llm,
        mock_load_prompt,
        agent,
        mock_test_input,
    ):
        """Test auto-correction when build fails but status says FAIL."""
        mock_load_prompt.return_value = "test prompt"
        # LLM incorrectly returns FAIL instead of BUILD_FAILED
        mock_call_llm.return_value = {
            "content": {
                "task_id": "TEST-001",
                "test_status": "FAIL",  # Wrong - should be BUILD_FAILED
                "build_successful": False,
                "build_errors": ["SyntaxError"],
                "test_summary": {
                    "total_tests": 0,
                    "passed": 0,
                    "failed": 0,
                    "skipped": 0,
                },
                "defects_found": [],
                "test_timestamp": "2025-12-23T12:00:00Z",
            }
        }
        mock_write_json.return_value = Path("/tmp/test_report.json")
        mock_write_md.return_value = Path("/tmp/test_report.md")

        result = agent.execute(mock_test_input)

        # Should be auto-corrected to BUILD_FAILED
        assert result.test_status == "BUILD_FAILED"
        assert result.build_successful is False


# =============================================================================
# Validation Tests
# =============================================================================


class TestTestAgentValidation:
    """Tests for _validate_test_report method."""

    @pytest.fixture
    def agent(self):
        """Create a TestAgent instance."""
        return TestAgent()

    def test_validate_build_failed_wrong_status(self, agent):
        """Test validation fails when build failed but wrong status."""
        report = TestReport(
            task_id="TEST-001",
            test_status="BUILD_FAILED",  # Must match build_successful=False
            build_successful=False,
            test_summary={"total_tests": 0, "passed": 0, "failed": 0, "skipped": 0},
            test_timestamp="2025-12-23T12:00:00Z",
        )
        # This should pass validation
        agent._validate_test_report(report)

    def test_validate_defects_found_pass_status_error(self, agent):
        """Test validation fails when defects found but status is PASS."""
        # Create a report that will fail validation
        # We need to bypass Pydantic validation to test the agent's validation
        report = MagicMock(spec=TestReport)
        report.build_successful = True
        report.test_status = "PASS"
        report.defects_found = [MagicMock()]  # Non-empty
        report.test_summary = {"total_tests": 1, "passed": 1, "failed": 0, "skipped": 0}

        with pytest.raises(AgentExecutionError) as exc_info:
            agent._validate_test_report(report)

        assert "defects found but test_status=PASS" in str(exc_info.value)

    def test_validate_test_summary_total_mismatch(self, agent):
        """Test validation fails when test summary totals don't match."""
        report = MagicMock(spec=TestReport)
        report.build_successful = True
        report.test_status = "PASS"
        report.defects_found = []
        report.test_summary = {
            "total_tests": 10,  # Doesn't match sum
            "passed": 5,
            "failed": 2,
            "skipped": 1,  # Sum = 8, not 10
        }

        with pytest.raises(AgentExecutionError) as exc_info:
            agent._validate_test_report(report)

        assert "Test summary inconsistent" in str(exc_info.value)

    def test_validate_duplicate_defect_ids(self, agent):
        """Test validation fails when duplicate defect IDs found."""
        defect1 = MagicMock()
        defect1.defect_id = "TEST-DEFECT-001"
        defect1.severity = "High"
        defect2 = MagicMock()
        defect2.defect_id = "TEST-DEFECT-001"  # Duplicate
        defect2.severity = "Medium"

        report = MagicMock(spec=TestReport)
        report.build_successful = True
        report.test_status = "FAIL"
        report.defects_found = [defect1, defect2]
        report.test_summary = {"total_tests": 2, "passed": 0, "failed": 2, "skipped": 0}

        with pytest.raises(AgentExecutionError) as exc_info:
            agent._validate_test_report(report)

        assert "Duplicate defect IDs" in str(exc_info.value)

    def test_validate_severity_counts_mismatch(self, agent):
        """Test validation fails when severity counts don't match defects."""
        defect = MagicMock()
        defect.defect_id = "TEST-DEFECT-001"
        defect.severity = "High"

        report = MagicMock(spec=TestReport)
        report.build_successful = True
        report.test_status = "FAIL"
        report.defects_found = [defect]
        report.test_summary = {"total_tests": 1, "passed": 0, "failed": 1, "skipped": 0}
        report.critical_defects = 1  # Wrong - should be 0
        report.high_defects = 0  # Wrong - should be 1
        report.medium_defects = 0
        report.low_defects = 0

        with pytest.raises(AgentExecutionError) as exc_info:
            agent._validate_test_report(report)

        assert "Severity counts mismatch" in str(exc_info.value)

    def test_validate_success(self, agent):
        """Test validation passes for valid report."""
        defect = MagicMock()
        defect.defect_id = "TEST-DEFECT-001"
        defect.severity = "High"

        report = MagicMock(spec=TestReport)
        report.build_successful = True
        report.test_status = "FAIL"
        report.defects_found = [defect]
        report.test_summary = {"total_tests": 2, "passed": 1, "failed": 1, "skipped": 0}
        report.critical_defects = 0
        report.high_defects = 1
        report.medium_defects = 0
        report.low_defects = 0

        # Should not raise
        agent._validate_test_report(report)


# =============================================================================
# Async Execution Tests
# =============================================================================


class TestTestAgentAsyncExecution:
    """Tests for async TestAgent execution."""

    @pytest.fixture
    def agent(self):
        """Create a TestAgent with mocked LLM client."""
        mock_client = Mock()
        return TestAgent(llm_client=mock_client)

    @pytest.mark.asyncio
    @patch.object(TestAgent, "load_prompt")
    @patch.object(TestAgent, "call_llm_async")
    async def test_execute_async_pass(
        self,
        mock_call_llm_async,
        mock_load_prompt,
        agent,
        mock_test_input,
        mock_pass_response,
    ):
        """Test async execution with PASS status."""
        mock_load_prompt.return_value = "test prompt"
        mock_call_llm_async.return_value = mock_pass_response

        result = await agent.execute_async(mock_test_input)

        assert isinstance(result, TestReport)
        assert result.test_status == "PASS"
        assert result.build_successful is True

    @pytest.mark.asyncio
    @patch.object(TestAgent, "load_prompt")
    @patch.object(TestAgent, "call_llm_async")
    async def test_execute_async_fail_with_defects(
        self,
        mock_call_llm_async,
        mock_load_prompt,
        agent,
        mock_test_input,
        mock_fail_response,
    ):
        """Test async execution with FAIL status and defects."""
        mock_load_prompt.return_value = "test prompt"
        mock_call_llm_async.return_value = mock_fail_response

        result = await agent.execute_async(mock_test_input)

        assert isinstance(result, TestReport)
        assert result.test_status == "FAIL"
        assert len(result.defects_found) == 2

    @pytest.mark.asyncio
    @patch.object(TestAgent, "load_prompt")
    @patch.object(TestAgent, "call_llm_async")
    async def test_execute_async_build_failed(
        self,
        mock_call_llm_async,
        mock_load_prompt,
        agent,
        mock_test_input,
        mock_build_failed_response,
    ):
        """Test async execution with BUILD_FAILED status."""
        mock_load_prompt.return_value = "test prompt"
        mock_call_llm_async.return_value = mock_build_failed_response

        result = await agent.execute_async(mock_test_input)

        assert isinstance(result, TestReport)
        assert result.test_status == "BUILD_FAILED"
        assert result.build_successful is False

    @pytest.mark.asyncio
    @patch.object(TestAgent, "load_prompt")
    async def test_execute_async_prompt_not_found(
        self, mock_load_prompt, agent, mock_test_input
    ):
        """Test async error when prompt template not found."""
        mock_load_prompt.side_effect = FileNotFoundError("Prompt not found")

        with pytest.raises(AgentExecutionError) as exc_info:
            await agent.execute_async(mock_test_input)

        assert "Prompt template not found" in str(exc_info.value)

    @pytest.mark.asyncio
    @patch.object(TestAgent, "load_prompt")
    @patch.object(TestAgent, "call_llm_async")
    async def test_execute_async_llm_exception(
        self, mock_call_llm_async, mock_load_prompt, agent, mock_test_input
    ):
        """Test async error when LLM call fails."""
        mock_load_prompt.return_value = "test prompt"
        mock_call_llm_async.side_effect = Exception("Async LLM error")

        with pytest.raises(AgentExecutionError) as exc_info:
            await agent.execute_async(mock_test_input)

        assert "Test execution failed" in str(exc_info.value)

    @pytest.mark.asyncio
    @patch.object(TestAgent, "load_prompt")
    @patch.object(TestAgent, "call_llm_async")
    async def test_execute_async_auto_correct_status(
        self,
        mock_call_llm_async,
        mock_load_prompt,
        agent,
        mock_test_input,
    ):
        """Test async auto-correction when build fails."""
        mock_load_prompt.return_value = "test prompt"
        mock_call_llm_async.return_value = {
            "content": {
                "task_id": "TEST-001",
                "test_status": "FAIL",  # Wrong - should be BUILD_FAILED
                "build_successful": False,
                "build_errors": ["Error"],
                "test_summary": {
                    "total_tests": 0,
                    "passed": 0,
                    "failed": 0,
                    "skipped": 0,
                },
                "defects_found": [],
                "test_timestamp": "2025-12-23T12:00:00Z",
            }
        }

        result = await agent.execute_async(mock_test_input)

        assert result.test_status == "BUILD_FAILED"

    @pytest.mark.asyncio
    @patch.object(TestAgent, "load_prompt")
    @patch.object(TestAgent, "call_llm_async")
    async def test_execute_async_parse_json_from_fence(
        self,
        mock_call_llm_async,
        mock_load_prompt,
        agent,
        mock_test_input,
    ):
        """Test async JSON parsing from markdown fence."""
        mock_load_prompt.return_value = "test prompt"
        json_content = {
            "task_id": "TEST-001",
            "test_status": "PASS",
            "build_successful": True,
            "build_errors": [],
            "test_summary": {"total_tests": 1, "passed": 1, "failed": 0, "skipped": 0},
            "defects_found": [],
            "test_timestamp": "2025-12-23T12:00:00Z",
        }
        mock_call_llm_async.return_value = {
            "content": f"```json\n{json.dumps(json_content)}\n```"
        }

        result = await agent.execute_async(mock_test_input)

        assert result.test_status == "PASS"


# =============================================================================
# Edge Cases
# =============================================================================


class TestTestAgentEdgeCases:
    """Tests for edge cases in TestAgent."""

    @pytest.fixture
    def agent(self):
        """Create a TestAgent with mocked LLM client."""
        mock_client = Mock()
        return TestAgent(llm_client=mock_client)

    @patch.object(TestAgent, "load_prompt")
    @patch.object(TestAgent, "call_llm")
    @patch("asp.agents.test_agent.write_artifact_json")
    @patch("asp.agents.test_agent.write_artifact_markdown")
    @patch("asp.agents.test_agent.is_git_repository", return_value=False)
    def test_execute_with_all_severity_levels(
        self,
        mock_is_git,
        mock_write_md,
        mock_write_json,
        mock_call_llm,
        mock_load_prompt,
        agent,
        mock_test_input,
    ):
        """Test execution with defects of all severity levels."""
        mock_load_prompt.return_value = "test prompt"
        mock_call_llm.return_value = {
            "content": {
                "task_id": "TEST-001",
                "test_status": "FAIL",
                "build_successful": True,
                "build_errors": [],
                "test_summary": {
                    "total_tests": 4,
                    "passed": 0,
                    "failed": 4,
                    "skipped": 0,
                },
                "defects_found": [
                    {
                        "defect_id": "TEST-DEFECT-001",
                        "defect_type": "5_Security_Vulnerability",
                        "severity": "Critical",
                        "description": "SQL injection vulnerability in login",
                        "evidence": "SQLi detected",
                        "phase_injected": "Code",
                    },
                    {
                        "defect_id": "TEST-DEFECT-002",
                        "defect_type": "6_Conventional_Code_Bug",
                        "severity": "High",
                        "description": "Null pointer exception in handler",
                        "evidence": "NullPointerException",
                        "phase_injected": "Code",
                    },
                    {
                        "defect_id": "TEST-DEFECT-003",
                        "defect_type": "6_Conventional_Code_Bug",
                        "severity": "Medium",
                        "description": "Incorrect error message",
                        "evidence": "Wrong message displayed",
                        "phase_injected": "Code",
                    },
                    {
                        "defect_id": "TEST-DEFECT-004",
                        "defect_type": "6_Conventional_Code_Bug",
                        "severity": "Low",
                        "description": "Typo in variable name",
                        "evidence": "Variable 'usre' should be 'user'",
                        "phase_injected": "Code",
                    },
                ],
                "test_timestamp": "2025-12-23T12:00:00Z",
            }
        }
        mock_write_json.return_value = Path("/tmp/test_report.json")
        mock_write_md.return_value = Path("/tmp/test_report.md")

        result = agent.execute(mock_test_input)

        assert result.critical_defects == 1
        assert result.high_defects == 1
        assert result.medium_defects == 1
        assert result.low_defects == 1

    @patch.object(TestAgent, "load_prompt")
    @patch.object(TestAgent, "call_llm")
    @patch("asp.agents.test_agent.write_artifact_json")
    @patch("asp.agents.test_agent.write_artifact_markdown")
    @patch("asp.agents.test_agent.is_git_repository", return_value=False)
    def test_execute_artifact_write_failure_continues(
        self,
        mock_is_git,
        mock_write_md,
        mock_write_json,
        mock_call_llm,
        mock_load_prompt,
        agent,
        mock_test_input,
        mock_pass_response,
    ):
        """Test that artifact write failure doesn't fail execution."""
        mock_load_prompt.return_value = "test prompt"
        mock_call_llm.return_value = mock_pass_response
        mock_write_json.side_effect = Exception("Disk full")

        # Should succeed despite artifact write failure
        result = agent.execute(mock_test_input)

        assert isinstance(result, TestReport)
        assert result.test_status == "PASS"

    @patch.object(TestAgent, "load_prompt")
    @patch.object(TestAgent, "call_llm")
    @patch("asp.agents.test_agent.write_artifact_json")
    @patch("asp.agents.test_agent.write_artifact_markdown")
    @patch("asp.agents.test_agent.is_git_repository", return_value=False)
    def test_execute_with_null_coverage(
        self,
        mock_is_git,
        mock_write_md,
        mock_write_json,
        mock_call_llm,
        mock_load_prompt,
        agent,
        mock_test_input,
    ):
        """Test execution with null coverage percentage."""
        mock_load_prompt.return_value = "test prompt"
        mock_call_llm.return_value = {
            "content": {
                "task_id": "TEST-001",
                "test_status": "PASS",
                "build_successful": True,
                "build_errors": [],
                "test_summary": {
                    "total_tests": 1,
                    "passed": 1,
                    "failed": 0,
                    "skipped": 0,
                },
                "coverage_percentage": None,
                "defects_found": [],
                "test_timestamp": "2025-12-23T12:00:00Z",
            }
        }
        mock_write_json.return_value = Path("/tmp/test_report.json")
        mock_write_md.return_value = Path("/tmp/test_report.md")

        result = agent.execute(mock_test_input)

        assert result.coverage_percentage is None

    @patch.object(TestAgent, "load_prompt")
    @patch.object(TestAgent, "call_llm")
    @patch("asp.agents.test_agent.write_artifact_json")
    @patch("asp.agents.test_agent.write_artifact_markdown")
    @patch("asp.agents.test_agent.is_git_repository", return_value=False)
    def test_execute_with_skipped_tests(
        self,
        mock_is_git,
        mock_write_md,
        mock_write_json,
        mock_call_llm,
        mock_load_prompt,
        agent,
        mock_test_input,
    ):
        """Test execution with skipped tests."""
        mock_load_prompt.return_value = "test prompt"
        mock_call_llm.return_value = {
            "content": {
                "task_id": "TEST-001",
                "test_status": "PASS",
                "build_successful": True,
                "build_errors": [],
                "test_summary": {
                    "total_tests": 10,
                    "passed": 8,
                    "failed": 0,
                    "skipped": 2,
                },
                "defects_found": [],
                "test_timestamp": "2025-12-23T12:00:00Z",
            }
        }
        mock_write_json.return_value = Path("/tmp/test_report.json")
        mock_write_md.return_value = Path("/tmp/test_report.md")

        result = agent.execute(mock_test_input)

        assert result.test_summary["skipped"] == 2
        assert result.test_status == "PASS"  # Skipped tests don't cause failure
