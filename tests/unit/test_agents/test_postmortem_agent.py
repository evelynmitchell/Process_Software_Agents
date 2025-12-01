"""
Unit tests for Postmortem Agent.

Tests cover:
- Initialization
- Performance analysis with valid inputs
- Estimation accuracy calculation
- Quality metrics calculation
- Root cause analysis
- Summary generation
- PIP generation (mocked)
- Error handling

Author: ASP Development Team
Date: November 19, 2025
"""

import json
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from asp.agents.base_agent import AgentExecutionError
from asp.agents.postmortem_agent import PostmortemAgent
from asp.models.planning import PROBEAIPrediction, ProjectPlan, SemanticUnit
from asp.models.postmortem import (
    DefectLogEntry,
    EffortLogEntry,
    PostmortemInput,
    PostmortemReport,
    ProcessImprovementProposal,
)

# =============================================================================
# Test Fixtures
# =============================================================================


def create_test_project_plan(task_id="POSTMORTEM-001"):
    """Create a test project plan."""
    return ProjectPlan(
        task_id=task_id,
        project_id="TEST-PROJECT",
        total_est_complexity=18,
        probe_ai_prediction=PROBEAIPrediction(
            total_est_latency_ms=35000.0,
            total_est_tokens=88000,
            total_est_api_cost=0.14,
            confidence=0.85,
        ),
        probe_ai_enabled=True,
        semantic_units=[
            SemanticUnit(
                unit_id="SU-001",
                description="Implement user authentication",
                api_interactions=2,
                data_transformations=1,
                logical_branches=3,
                code_entities_modified=2,
                novelty_multiplier=1.0,
                dependencies=[],
                est_complexity=10,
            ),
            SemanticUnit(
                unit_id="SU-002",
                description="Add database migrations",
                api_interactions=1,
                data_transformations=2,
                logical_branches=1,
                code_entities_modified=1,
                novelty_multiplier=1.0,
                dependencies=["SU-001"],
                est_complexity=8,
            ),
        ],
    )


def create_test_effort_log(task_id="POSTMORTEM-001"):
    """Create test effort log entries."""
    return [
        EffortLogEntry(
            timestamp=datetime(2025, 11, 19, 10, 0, 0),
            task_id=task_id,
            agent_role="Planning",
            metric_type="Latency",
            metric_value=2500,
            unit="ms",
        ),
        EffortLogEntry(
            timestamp=datetime(2025, 11, 19, 10, 0, 0),
            task_id=task_id,
            agent_role="Planning",
            metric_type="Tokens_In",
            metric_value=5000,
            unit="tokens",
        ),
        EffortLogEntry(
            timestamp=datetime(2025, 11, 19, 10, 0, 0),
            task_id=task_id,
            agent_role="Planning",
            metric_type="Tokens_Out",
            metric_value=3000,
            unit="tokens",
        ),
        EffortLogEntry(
            timestamp=datetime(2025, 11, 19, 10, 0, 0),
            task_id=task_id,
            agent_role="Planning",
            metric_type="API_Cost",
            metric_value=0.03,
            unit="USD",
        ),
        EffortLogEntry(
            timestamp=datetime(2025, 11, 19, 10, 5, 0),
            task_id=task_id,
            agent_role="Design",
            metric_type="Latency",
            metric_value=8000,
            unit="ms",
        ),
        EffortLogEntry(
            timestamp=datetime(2025, 11, 19, 10, 5, 0),
            task_id=task_id,
            agent_role="Design",
            metric_type="Tokens_In",
            metric_value=20000,
            unit="tokens",
        ),
        EffortLogEntry(
            timestamp=datetime(2025, 11, 19, 10, 5, 0),
            task_id=task_id,
            agent_role="Design",
            metric_type="Tokens_Out",
            metric_value=25000,
            unit="tokens",
        ),
        EffortLogEntry(
            timestamp=datetime(2025, 11, 19, 10, 5, 0),
            task_id=task_id,
            agent_role="Design",
            metric_type="API_Cost",
            metric_value=0.08,
            unit="USD",
        ),
        EffortLogEntry(
            timestamp=datetime(2025, 11, 19, 10, 15, 0),
            task_id=task_id,
            agent_role="Code",
            metric_type="Latency",
            metric_value=28000,
            unit="ms",
        ),
        EffortLogEntry(
            timestamp=datetime(2025, 11, 19, 10, 15, 0),
            task_id=task_id,
            agent_role="Code",
            metric_type="Tokens_In",
            metric_value=35000,
            unit="tokens",
        ),
        EffortLogEntry(
            timestamp=datetime(2025, 11, 19, 10, 15, 0),
            task_id=task_id,
            agent_role="Code",
            metric_type="Tokens_Out",
            metric_value=44000,
            unit="tokens",
        ),
        EffortLogEntry(
            timestamp=datetime(2025, 11, 19, 10, 15, 0),
            task_id=task_id,
            agent_role="Code",
            metric_type="API_Cost",
            metric_value=0.06,
            unit="USD",
        ),
    ]


def create_test_defect_log(task_id="POSTMORTEM-001"):
    """Create test defect log entries."""
    return [
        DefectLogEntry(
            defect_id="D-001",
            task_id=task_id,
            defect_type="5_Security_Vulnerability",
            phase_injected="Code",
            phase_removed="Code Review",
            effort_to_fix_vector={
                "latency_ms": 5000,
                "tokens": 12000,
                "api_cost": 0.02,
            },
            description="SQL injection vulnerability in user input",
            severity="Critical",
        ),
        DefectLogEntry(
            defect_id="D-002",
            task_id=task_id,
            defect_type="6_Conventional_Code_Bug",
            phase_injected="Code",
            phase_removed="Test",
            effort_to_fix_vector={
                "latency_ms": 3000,
                "tokens": 8000,
                "api_cost": 0.01,
            },
            description="Off-by-one error in loop",
            severity="High",
        ),
        DefectLogEntry(
            defect_id="D-003",
            task_id=task_id,
            defect_type="2_Prompt_Misinterpretation",
            phase_injected="Design",
            phase_removed="Design Review",
            effort_to_fix_vector={
                "latency_ms": 2000,
                "tokens": 5000,
                "api_cost": 0.008,
            },
            description="Missing API endpoint from requirements",
            severity="Medium",
        ),
    ]


@pytest.fixture
def postmortem_agent():
    """Create PostmortemAgent instance for testing."""
    return PostmortemAgent()


@pytest.fixture
def test_postmortem_input():
    """Create test PostmortemInput."""
    return PostmortemInput(
        task_id="POSTMORTEM-001",
        project_plan=create_test_project_plan(),
        effort_log=create_test_effort_log(),
        defect_log=create_test_defect_log(),
        actual_semantic_complexity=20.3,
    )


# =============================================================================
# Tests: Initialization
# =============================================================================


def test_postmortem_agent_initialization():
    """Test PostmortemAgent initializes correctly."""
    agent = PostmortemAgent()
    assert agent.agent_name == "PostmortemAgent"
    assert agent.agent_version == "1.0.0"


def test_postmortem_agent_initialization_with_params():
    """Test PostmortemAgent initializes with custom parameters."""
    mock_client = MagicMock()
    db_path = Path("/tmp/test.db")

    agent = PostmortemAgent(db_path=db_path, llm_client=mock_client)
    assert agent.db_path == db_path
    assert agent._llm_client == mock_client


# =============================================================================
# Tests: Execute - Performance Analysis
# =============================================================================


@patch("asp.utils.artifact_io.write_artifact_json")
@patch("asp.utils.artifact_io.write_artifact_markdown")
@patch("asp.utils.git_utils.is_git_repository", return_value=False)
def test_execute_basic_analysis(
    mock_git,
    mock_write_md,
    mock_write_json,
    postmortem_agent,
    test_postmortem_input,
):
    """Test basic postmortem analysis execution."""
    report = postmortem_agent.execute(test_postmortem_input)

    # Verify report structure
    assert isinstance(report, PostmortemReport)
    assert report.task_id == "POSTMORTEM-001"

    # Verify estimation accuracy
    assert report.estimation_accuracy.latency_ms.planned == 35000
    assert report.estimation_accuracy.latency_ms.actual == 38500  # 2500 + 8000 + 28000
    assert abs(report.estimation_accuracy.latency_ms.variance_percent - 10.0) < 0.1

    assert report.estimation_accuracy.tokens.planned == 88000
    assert report.estimation_accuracy.tokens.actual > 0  # Tokens were aggregated
    assert isinstance(report.estimation_accuracy.tokens.variance_percent, float)

    assert report.estimation_accuracy.api_cost.planned == 0.14
    assert report.estimation_accuracy.api_cost.actual == pytest.approx(0.17, abs=0.01)
    assert abs(report.estimation_accuracy.api_cost.variance_percent - 21.43) < 0.5

    # Verify quality metrics
    assert report.quality_metrics.total_defects == 3
    assert report.quality_metrics.defect_density == pytest.approx(0.148, abs=0.01)
    assert report.quality_metrics.defect_injection_by_phase == {"Code": 2, "Design": 1}
    assert report.quality_metrics.defect_removal_by_phase == {
        "Code Review": 1,
        "Test": 1,
        "Design Review": 1,
    }

    # Verify root cause analysis
    assert len(report.root_cause_analysis) > 0
    top_issue = report.root_cause_analysis[0]
    assert top_issue.defect_type == "5_Security_Vulnerability"  # Highest fix cost
    assert top_issue.total_effort_to_fix == 0.02
    assert top_issue.occurrence_count == 1

    # Verify summary and recommendations
    assert len(report.summary) > 0
    assert len(report.recommendations) > 0


def test_estimation_accuracy_calculation(postmortem_agent, test_postmortem_input):
    """Test estimation accuracy calculation logic."""
    estimation_accuracy = postmortem_agent._calculate_estimation_accuracy(
        test_postmortem_input
    )

    # Check planned values
    assert estimation_accuracy.latency_ms.planned == 35000
    assert estimation_accuracy.tokens.planned == 88000
    assert estimation_accuracy.api_cost.planned == 0.14
    assert estimation_accuracy.semantic_complexity.planned == 18

    # Check actual values
    assert estimation_accuracy.latency_ms.actual == 38500
    assert estimation_accuracy.tokens.actual > 0  # Tokens were aggregated
    assert estimation_accuracy.api_cost.actual == pytest.approx(0.17, abs=0.01)
    assert estimation_accuracy.semantic_complexity.actual == 20.3


def test_quality_metrics_calculation(postmortem_agent, test_postmortem_input):
    """Test quality metrics calculation logic."""
    quality_metrics = postmortem_agent._calculate_quality_metrics(test_postmortem_input)

    assert quality_metrics.total_defects == 3
    assert quality_metrics.defect_density == pytest.approx(0.148, abs=0.01)
    assert quality_metrics.defect_injection_by_phase["Code"] == 2
    assert quality_metrics.defect_injection_by_phase["Design"] == 1
    assert quality_metrics.phase_yield["Code Review"] == pytest.approx(33.3, abs=0.1)


def test_root_cause_analysis(postmortem_agent, test_postmortem_input):
    """Test root cause analysis logic."""
    root_causes = postmortem_agent._perform_root_cause_analysis(test_postmortem_input)

    # Should be sorted by total_effort_to_fix (descending)
    assert len(root_causes) == 3
    assert root_causes[0].defect_type == "5_Security_Vulnerability"
    assert root_causes[0].total_effort_to_fix == 0.02
    assert root_causes[1].defect_type == "6_Conventional_Code_Bug"
    assert root_causes[1].total_effort_to_fix == 0.01
    assert root_causes[2].defect_type == "2_Prompt_Misinterpretation"
    assert root_causes[2].total_effort_to_fix == 0.008


def test_summary_generation(postmortem_agent, test_postmortem_input):
    """Test summary generation."""
    estimation_accuracy = postmortem_agent._calculate_estimation_accuracy(
        test_postmortem_input
    )
    quality_metrics = postmortem_agent._calculate_quality_metrics(test_postmortem_input)
    root_cause_analysis = postmortem_agent._perform_root_cause_analysis(
        test_postmortem_input
    )

    summary = postmortem_agent._generate_summary(
        test_postmortem_input,
        estimation_accuracy,
        quality_metrics,
        root_cause_analysis,
    )

    # Summary should mention task ID and key metrics
    assert "POSTMORTEM-001" in summary
    assert "defect" in summary.lower() or "quality" in summary.lower()


def test_recommendations_generation(postmortem_agent, test_postmortem_input):
    """Test recommendations generation."""
    root_cause_analysis = postmortem_agent._perform_root_cause_analysis(
        test_postmortem_input
    )
    recommendations = postmortem_agent._generate_recommendations(root_cause_analysis)

    # Should have recommendations for top issues
    assert len(recommendations) > 0
    assert isinstance(recommendations[0], str)


def test_execute_no_defects(postmortem_agent):
    """Test postmortem analysis with no defects."""
    input_data = PostmortemInput(
        task_id="POSTMORTEM-NO-DEFECTS",
        project_plan=create_test_project_plan("POSTMORTEM-NO-DEFECTS"),
        effort_log=create_test_effort_log("POSTMORTEM-NO-DEFECTS"),
        defect_log=[],  # No defects
        actual_semantic_complexity=18.0,
    )

    with (
        patch("asp.utils.artifact_io.write_artifact_json"),
        patch("asp.utils.artifact_io.write_artifact_markdown"),
        patch("asp.utils.git_utils.is_git_repository", return_value=False),
    ):
        report = postmortem_agent.execute(input_data)

    assert report.quality_metrics.total_defects == 0
    assert report.quality_metrics.defect_density == 0.0
    assert len(report.root_cause_analysis) == 0
    assert (
        "excellent quality" in report.summary.lower()
        or "no defects" in report.summary.lower()
    )


# =============================================================================
# Tests: PIP Generation
# =============================================================================


@patch("asp.agents.postmortem_agent.PostmortemAgent.call_llm")
def test_generate_pip(mock_call_llm, postmortem_agent, test_postmortem_input):
    """Test PIP generation with mocked LLM."""
    # Create a mock postmortem report
    report = postmortem_agent.execute(test_postmortem_input)

    # Mock LLM response
    mock_pip_response = {
        "analysis": "Security vulnerabilities indicate Code Agent needs better security guidance",
        "proposed_changes": [
            {
                "target_artifact": "code_agent_prompt",
                "change_type": "add",
                "current_content": None,
                "proposed_content": "SECURITY: Use parameterized queries for all SQL",
                "rationale": "Prevent SQL injection vulnerabilities",
            }
        ],
        "expected_impact": "Reduce security vulnerabilities by 70%",
    }

    mock_call_llm.return_value = {"content": json.dumps(mock_pip_response)}

    with patch("asp.utils.artifact_io.write_artifact_json"):
        pip = postmortem_agent.generate_pip(report, test_postmortem_input)

    # Verify PIP structure
    assert isinstance(pip, ProcessImprovementProposal)
    assert pip.task_id == "POSTMORTEM-001"
    assert pip.proposal_id.startswith("PIP-")
    assert len(pip.proposed_changes) > 0
    assert pip.hitl_status == "pending"


# =============================================================================
# Tests: Error Handling
# =============================================================================


def test_execute_with_invalid_input(postmortem_agent):
    """Test that invalid input raises appropriate errors."""
    with pytest.raises(Exception):  # Pydantic ValidationError
        postmortem_agent.execute(None)


# =============================================================================
# Tests: Artifact Writing
# =============================================================================


@patch("asp.agents.postmortem_agent.write_artifact_json")
@patch("asp.agents.postmortem_agent.write_artifact_markdown")
@patch("asp.agents.postmortem_agent.is_git_repository", return_value=False)
def test_artifact_writing(
    mock_git,
    mock_write_md,
    mock_write_json,
    postmortem_agent,
    test_postmortem_input,
):
    """Test that artifacts are written correctly."""
    mock_write_json.return_value = Path("/tmp/postmortem_report.json")
    mock_write_md.return_value = Path("/tmp/postmortem_report.md")

    report = postmortem_agent.execute(test_postmortem_input)

    # Verify write_artifact_json was called
    assert mock_write_json.called
    call_args = mock_write_json.call_args
    assert call_args[1]["task_id"] == "POSTMORTEM-001"
    assert call_args[1]["artifact_type"] == "postmortem_report"

    # Verify write_artifact_markdown was called
    assert mock_write_md.called


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
