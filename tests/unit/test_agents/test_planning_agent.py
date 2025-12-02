"""
Unit tests for planning_agent.py

Tests the PlanningAgent implementation including:
- Task decomposition
- Semantic complexity scoring
- Integration with base agent functionality
- Telemetry integration
- Error handling
"""

from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from asp.agents.base_agent import AgentExecutionError
from asp.agents.planning_agent import PlanningAgent
from asp.models.planning import ProjectPlan, TaskRequirements


# Helper function to create valid TaskRequirements for testing
def create_test_requirements(
    task_id="TEST-001",
    project_id="TEST-PROJECT",
    description="Test task description for unit testing",
    requirements="Test requirements with sufficient length for validation to pass",
    context_files=None,
):
    """Create a valid TaskRequirements object for testing."""
    return TaskRequirements(
        task_id=task_id,
        project_id=project_id,
        description=description,
        requirements=requirements,
        context_files=context_files,
    )


class TestPlanningAgentInitialization:
    """Test PlanningAgent initialization."""

    def test_init_with_defaults(self):
        """Test initialization with default parameters."""
        agent = PlanningAgent()
        assert agent.db_path is None
        assert agent._llm_client is None
        assert agent.agent_name == "PlanningAgent"
        assert agent.agent_version == "1.0.0"

    def test_init_with_db_path(self):
        """Test initialization with database path."""
        db_path = Path("/tmp/test.db")
        agent = PlanningAgent(db_path=db_path)
        assert agent.db_path == db_path

    def test_init_with_llm_client(self):
        """Test initialization with custom LLM client."""
        mock_client = Mock()
        agent = PlanningAgent(llm_client=mock_client)
        assert agent._llm_client == mock_client


class TestDecomposeTask:
    """Test decompose_task method."""

    def test_decompose_task_success(self):
        """Test successful task decomposition."""
        agent = PlanningAgent()

        # Mock LLM response with valid semantic units
        llm_response = {
            "content": {
                "semantic_units": [
                    {
                        "unit_id": "SU-001",
                        "description": "Implement user registration",
                        "api_interactions": 2,
                        "data_transformations": 3,
                        "logical_branches": 4,
                        "code_entities_modified": 3,
                        "novelty_multiplier": 1.0,
                        "est_complexity": 43,
                        "dependencies": [],
                    },
                    {
                        "unit_id": "SU-002",
                        "description": "Implement login endpoint",
                        "api_interactions": 1,
                        "data_transformations": 2,
                        "logical_branches": 2,
                        "code_entities_modified": 2,
                        "novelty_multiplier": 1.0,
                        "est_complexity": 26,
                        "dependencies": ["SU-001"],
                    },
                ]
            }
        }

        # Create test requirements
        requirements = TaskRequirements(
            project_id="PROJ-001",
            task_id="TASK-001",
            description="Build authentication system",
            requirements="JWT tokens, user registration, login",
        )

        # Mock both prompt loading and LLM call
        with patch.object(agent, "load_prompt", return_value="Mock prompt {task_id}"):
            with patch.object(agent, "call_llm", return_value=llm_response):
                units = agent.decompose_task(requirements)

        assert len(units) == 2
        assert units[0].unit_id == "SU-001"
        assert units[0].description == "Implement user registration"
        assert units[0].est_complexity == 43
        assert units[1].unit_id == "SU-002"
        assert units[1].dependencies == ["SU-001"]

    def test_decompose_task_verifies_complexity(self):
        """Test that decompose_task verifies complexity calculation."""
        agent = PlanningAgent()

        # Mock LLM response with incorrect complexity
        llm_response = {
            "content": {
                "semantic_units": [
                    {
                        "unit_id": "SU-001",
                        "description": "Test semantic unit with proper length",
                        "api_interactions": 2,
                        "data_transformations": 3,
                        "logical_branches": 1,
                        "code_entities_modified": 2,
                        "novelty_multiplier": 1.0,
                        "est_complexity": 50,  # Incorrect (should be 30)
                        "dependencies": [],
                    }
                ]
            }
        }

        requirements = create_test_requirements(
            project_id="PROJ-001",
            task_id="TASK-001",
        )

        with patch.object(agent, "load_prompt", return_value="Mock prompt"):
            with patch.object(agent, "call_llm", return_value=llm_response):
                units = agent.decompose_task(requirements)

        # Should override with calculated value (30)
        assert units[0].est_complexity == 30

    def test_decompose_task_allows_small_rounding_differences(self):
        """Test that small rounding differences in complexity are allowed."""
        agent = PlanningAgent()

        # Mock LLM response with complexity off by 1
        llm_response = {
            "content": {
                "semantic_units": [
                    {
                        "unit_id": "SU-001",
                        "description": "Test semantic unit",
                        "api_interactions": 2,
                        "data_transformations": 3,
                        "logical_branches": 1,
                        "code_entities_modified": 2,
                        "novelty_multiplier": 1.0,
                        "est_complexity": 31,  # Off by 1 (should be 30)
                        "dependencies": [],
                    }
                ]
            }
        }

        requirements = create_test_requirements(
            project_id="PROJ-001",
            task_id="TASK-001",
        )

        with patch.object(agent, "load_prompt", return_value="Mock prompt"):
            with patch.object(agent, "call_llm", return_value=llm_response):
                units = agent.decompose_task(requirements)

        # Should keep LLM value for small difference
        assert units[0].est_complexity == 31

    def test_decompose_task_handles_context_files(self):
        """Test that context_files are included in prompt."""
        agent = PlanningAgent()

        llm_response = {
            "content": {
                "semantic_units": [
                    {
                        "unit_id": "SU-001",
                        "description": "Test semantic unit",
                        "api_interactions": 1,
                        "data_transformations": 1,
                        "logical_branches": 1,
                        "code_entities_modified": 1,
                        "novelty_multiplier": 1.0,
                        "est_complexity": 14,
                        "dependencies": [],
                    }
                ]
            }
        }

        requirements = create_test_requirements(
            project_id="PROJ-001",
            task_id="TASK-001",
            context_files=["file1.py", "file2.py"],
        )

        mock_prompt_template = "Task: {task_id}\nFiles: {context_files}"

        with patch.object(agent, "load_prompt", return_value=mock_prompt_template):
            with patch.object(
                agent, "format_prompt", wraps=agent.format_prompt
            ) as mock_format:
                with patch.object(agent, "call_llm", return_value=llm_response):
                    units = agent.decompose_task(requirements)

                    # Verify context_files were passed to format_prompt
                    mock_format.assert_called_once()
                    call_kwargs = mock_format.call_args[1]
                    assert call_kwargs["context_files"] == "file1.py\nfile2.py"

    def test_decompose_task_prompt_not_found(self):
        """Test error handling when prompt file not found."""
        agent = PlanningAgent()

        requirements = create_test_requirements(
            project_id="PROJ-001",
            task_id="TASK-001",
        )

        with patch.object(
            agent, "load_prompt", side_effect=FileNotFoundError("Prompt not found")
        ):
            with pytest.raises(AgentExecutionError) as exc_info:
                agent.decompose_task(requirements)

            assert "Prompt template not found" in str(exc_info.value)

    def test_decompose_task_non_json_response(self):
        """Test error handling for non-JSON LLM response."""
        agent = PlanningAgent()

        # LLM returns plain text instead of JSON
        llm_response = {"content": "This is plain text, not JSON"}

        requirements = create_test_requirements(
            project_id="PROJ-001",
            task_id="TASK-001",
        )

        with patch.object(agent, "load_prompt", return_value="Mock prompt"):
            with patch.object(agent, "call_llm", return_value=llm_response):
                with pytest.raises(AgentExecutionError) as exc_info:
                    agent.decompose_task(requirements)

                assert "LLM returned non-JSON response" in str(exc_info.value)

    def test_decompose_task_missing_semantic_units_key(self):
        """Test error handling when response missing semantic_units key."""
        agent = PlanningAgent()

        # Response missing semantic_units key
        llm_response = {"content": {"wrong_key": []}}

        requirements = create_test_requirements(
            project_id="PROJ-001",
            task_id="TASK-001",
        )

        with patch.object(agent, "load_prompt", return_value="Mock prompt"):
            with patch.object(agent, "call_llm", return_value=llm_response):
                with pytest.raises(AgentExecutionError) as exc_info:
                    agent.decompose_task(requirements)

                assert "missing 'semantic_units' key" in str(exc_info.value)

    def test_decompose_task_semantic_units_not_array(self):
        """Test error handling when semantic_units is not an array."""
        agent = PlanningAgent()

        # semantic_units is not an array
        llm_response = {"content": {"semantic_units": "not an array"}}

        requirements = create_test_requirements(
            project_id="PROJ-001",
            task_id="TASK-001",
        )

        with patch.object(agent, "load_prompt", return_value="Mock prompt"):
            with patch.object(agent, "call_llm", return_value=llm_response):
                with pytest.raises(AgentExecutionError) as exc_info:
                    agent.decompose_task(requirements)

                assert "'semantic_units' must be an array" in str(exc_info.value)

    def test_decompose_task_invalid_unit_data(self):
        """Test error handling for invalid semantic unit data."""
        agent = PlanningAgent()

        # Unit missing required fields
        llm_response = {
            "content": {
                "semantic_units": [
                    {
                        "unit_id": "SU-001",
                        # Missing required fields
                    }
                ]
            }
        }

        requirements = create_test_requirements(
            project_id="PROJ-001",
            task_id="TASK-001",
        )

        with patch.object(agent, "load_prompt", return_value="Mock prompt"):
            with patch.object(agent, "call_llm", return_value=llm_response):
                with pytest.raises(AgentExecutionError) as exc_info:
                    agent.decompose_task(requirements)

                assert "Failed to validate semantic unit" in str(exc_info.value)


class TestExecute:
    """Test execute method."""

    def test_execute_success(self):
        """Test successful execution of planning agent."""
        agent = PlanningAgent()

        # Mock LLM response
        llm_response = {
            "content": {
                "semantic_units": [
                    {
                        "unit_id": "SU-001",
                        "description": "Implement feature",
                        "api_interactions": 2,
                        "data_transformations": 3,
                        "logical_branches": 1,
                        "code_entities_modified": 2,
                        "novelty_multiplier": 1.0,
                        "est_complexity": 30,
                        "dependencies": [],
                    }
                ]
            }
        }

        requirements = TaskRequirements(
            project_id="PROJ-001",
            task_id="TASK-001",
            description="Build feature",
            requirements="Test requirements with sufficient length",
        )

        with patch.object(agent, "load_prompt", return_value="Mock prompt {task_id}"):
            with patch.object(agent, "call_llm", return_value=llm_response):
                plan = agent.execute(requirements)

        assert isinstance(plan, ProjectPlan)
        assert plan.project_id == "PROJ-001"
        assert plan.task_id == "TASK-001"
        assert len(plan.semantic_units) == 1
        assert plan.total_est_complexity == 30
        assert plan.probe_ai_enabled is False
        assert plan.probe_ai_prediction is None
        assert plan.agent_version == "1.0.0"

    def test_execute_multiple_units(self):
        """Test execution with multiple semantic units."""
        agent = PlanningAgent()

        llm_response = {
            "content": {
                "semantic_units": [
                    {
                        "unit_id": "SU-001",
                        "description": "First semantic unit",
                        "api_interactions": 2,
                        "data_transformations": 3,
                        "logical_branches": 1,
                        "code_entities_modified": 2,
                        "novelty_multiplier": 1.0,
                        "est_complexity": 30,
                        "dependencies": [],
                    },
                    {
                        "unit_id": "SU-002",
                        "description": "Second semantic unit",
                        "api_interactions": 1,
                        "data_transformations": 2,
                        "logical_branches": 2,
                        "code_entities_modified": 2,
                        "novelty_multiplier": 1.0,
                        "est_complexity": 26,
                        "dependencies": ["SU-001"],
                    },
                    {
                        "unit_id": "SU-003",
                        "description": "Third semantic unit",
                        "api_interactions": 3,
                        "data_transformations": 4,
                        "logical_branches": 3,
                        "code_entities_modified": 4,
                        "novelty_multiplier": 1.5,
                        "est_complexity": 72,
                        "dependencies": ["SU-001", "SU-002"],
                    },
                ]
            }
        }

        requirements = TaskRequirements(
            project_id="PROJ-001",
            task_id="TASK-001",
            description="Build feature",
            requirements="Test requirements with sufficient length",
        )

        with patch.object(agent, "load_prompt", return_value="Mock prompt"):
            with patch.object(agent, "call_llm", return_value=llm_response):
                plan = agent.execute(requirements)

        assert len(plan.semantic_units) == 3
        # Total: 30 + 26 + 76 = 132 (SU-003 recalculated from 72 to 76)
        assert plan.total_est_complexity == 132

    def test_execute_handles_decomposition_error(self):
        """Test that execute handles decomposition errors."""
        agent = PlanningAgent()

        requirements = TaskRequirements(
            project_id="PROJ-001",
            task_id="TASK-001",
            description="Build feature",
            requirements="Test requirements with sufficient length",
        )

        # Mock decompose_task to raise error
        with patch.object(
            agent, "decompose_task", side_effect=Exception("LLM failure")
        ):
            with pytest.raises(AgentExecutionError) as exc_info:
                agent.execute(requirements)

            assert "Planning Agent failed for task TASK-001" in str(exc_info.value)
            assert "LLM failure" in str(exc_info.value)

    def test_execute_with_empty_context_files(self):
        """Test execution with empty context_files list."""
        agent = PlanningAgent()

        llm_response = {
            "content": {
                "semantic_units": [
                    {
                        "unit_id": "SU-001",
                        "description": "Test semantic unit",
                        "api_interactions": 1,
                        "data_transformations": 1,
                        "logical_branches": 1,
                        "code_entities_modified": 1,
                        "novelty_multiplier": 1.0,
                        "est_complexity": 14,
                        "dependencies": [],
                    }
                ]
            }
        }

        requirements = create_test_requirements(
            project_id="PROJ-001", task_id="TASK-001", context_files=[]
        )

        with patch.object(agent, "load_prompt", return_value="Mock {task_id}"):
            with patch.object(agent, "call_llm", return_value=llm_response):
                plan = agent.execute(requirements)

        assert plan is not None


class TestIntegration:
    """Integration tests for PlanningAgent."""

    def test_full_workflow_with_mocked_llm(self):
        """Test complete workflow from requirements to plan."""
        agent = PlanningAgent()

        # Realistic LLM response
        llm_response = {
            "content": {
                "semantic_units": [
                    {
                        "unit_id": "SU-001",
                        "description": "Create user registration endpoint with email validation",
                        "api_interactions": 2,
                        "data_transformations": 3,
                        "logical_branches": 4,
                        "code_entities_modified": 3,
                        "novelty_multiplier": 1.0,
                        "est_complexity": 43,
                        "dependencies": [],
                    },
                    {
                        "unit_id": "SU-002",
                        "description": "Implement password hashing with bcrypt",
                        "api_interactions": 1,
                        "data_transformations": 2,
                        "logical_branches": 2,
                        "code_entities_modified": 2,
                        "novelty_multiplier": 1.0,
                        "est_complexity": 26,
                        "dependencies": ["SU-001"],
                    },
                    {
                        "unit_id": "SU-003",
                        "description": "Create JWT token generation and validation",
                        "api_interactions": 2,
                        "data_transformations": 3,
                        "logical_branches": 3,
                        "code_entities_modified": 2,
                        "novelty_multiplier": 1.2,
                        "est_complexity": 43,
                        "dependencies": ["SU-001", "SU-002"],
                    },
                ]
            }
        }

        requirements = TaskRequirements(
            project_id="AUTH-2025",
            task_id="TASK-AUTH-001",
            description="Build JWT authentication system",
            requirements="User registration, login, JWT tokens, password hashing",
            context_files=["src/api/auth.py", "src/models/user.py"],
        )

        with patch.object(agent, "load_prompt", return_value="Mock prompt"):
            with patch.object(agent, "call_llm", return_value=llm_response):
                plan = agent.execute(requirements)

        # Verify plan structure
        assert plan.project_id == "AUTH-2025"
        assert plan.task_id == "TASK-AUTH-001"
        assert len(plan.semantic_units) == 3

        # Verify first unit
        unit1 = plan.semantic_units[0]
        assert unit1.unit_id == "SU-001"
        assert unit1.est_complexity == 43
        assert len(unit1.dependencies) == 0

        # Verify second unit
        unit2 = plan.semantic_units[1]
        assert unit2.unit_id == "SU-002"
        assert unit2.dependencies == ["SU-001"]

        # Verify third unit
        unit3 = plan.semantic_units[2]
        assert unit3.unit_id == "SU-003"
        assert unit3.dependencies == ["SU-001", "SU-002"]

        # Verify total complexity: 43 + 26 + 43 = 112
        assert plan.total_est_complexity == 112

        # Verify Phase 1 settings
        assert plan.probe_ai_enabled is False
        assert plan.probe_ai_prediction is None
