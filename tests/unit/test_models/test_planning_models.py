"""
Unit tests for Planning Models.

Tests the Pydantic models for Planning Agent including:
- TaskRequirements validation
- SemanticUnit validation and complexity constraints
- PROBEAIPrediction validation
- ProjectPlan validation and aggregation
- JSON serialization/deserialization
- Edge cases and error handling
"""

import pytest
import json
from pydantic import ValidationError

from asp.models.planning import (
    TaskRequirements,
    SemanticUnit,
    PROBEAIPrediction,
    ProjectPlan,
)


# =============================================================================
# TaskRequirements Tests
# =============================================================================


class TestTaskRequirements:
    """Test TaskRequirements model."""

    def test_valid_task_requirements_minimal(self):
        """Test creating TaskRequirements with minimal required fields."""
        requirements = TaskRequirements(
            task_id="TASK-001",
            description="Build authentication system",
            requirements="User registration with email and password validation",
        )

        assert requirements.task_id == "TASK-001"
        assert requirements.description == "Build authentication system"
        assert (
            requirements.requirements
            == "User registration with email and password validation"
        )
        assert requirements.project_id is None
        assert requirements.context_files is None

    def test_valid_task_requirements_full(self):
        """Test creating TaskRequirements with all fields."""
        requirements = TaskRequirements(
            task_id="TASK-2025-001",
            project_id="ASP-PLATFORM",
            description="Build user authentication system with JWT tokens",
            requirements="""
                - User registration with email/password
                - Login endpoint with JWT generation
                - Token validation middleware
            """,
            context_files=["docs/architecture.md", "docs/api_spec.md"],
        )

        assert requirements.task_id == "TASK-2025-001"
        assert requirements.project_id == "ASP-PLATFORM"
        assert len(requirements.context_files) == 2

    def test_task_requirements_description_too_short(self):
        """Test that description must be at least 10 characters."""
        with pytest.raises(ValidationError) as exc_info:
            TaskRequirements(
                task_id="TASK-001",
                description="Short",  # Too short
                requirements="Valid requirements text here",
            )

        error = exc_info.value.errors()[0]
        assert error["loc"] == ("description",)
        assert "at least 10 characters" in str(error["msg"])

    def test_task_requirements_requirements_too_short(self):
        """Test that requirements must be at least 20 characters."""
        with pytest.raises(ValidationError) as exc_info:
            TaskRequirements(
                task_id="TASK-001",
                description="Build authentication system",
                requirements="Short",  # Too short
            )

        error = exc_info.value.errors()[0]
        assert error["loc"] == ("requirements",)
        assert "at least 20 characters" in str(error["msg"])

    def test_task_requirements_missing_required_fields(self):
        """Test that required fields cannot be omitted."""
        with pytest.raises(ValidationError) as exc_info:
            TaskRequirements(
                task_id="TASK-001"
                # Missing description and requirements
            )

        errors = exc_info.value.errors()
        assert len(errors) == 2  # Missing description and requirements

    def test_task_requirements_json_serialization(self):
        """Test JSON serialization and deserialization."""
        requirements = TaskRequirements(
            task_id="TASK-001",
            project_id="PROJ-001",
            description="Test task description",
            requirements="Test requirements with sufficient length",
            context_files=["file1.md", "file2.md"],
        )

        # Serialize to JSON
        json_str = requirements.model_dump_json()
        json_data = json.loads(json_str)

        # Verify structure
        assert json_data["task_id"] == "TASK-001"
        assert json_data["project_id"] == "PROJ-001"
        assert len(json_data["context_files"]) == 2

        # Deserialize back
        restored = TaskRequirements.model_validate_json(json_str)
        assert restored == requirements


# =============================================================================
# SemanticUnit Tests
# =============================================================================


class TestSemanticUnit:
    """Test SemanticUnit model."""

    def test_valid_semantic_unit(self):
        """Test creating valid SemanticUnit."""
        unit = SemanticUnit(
            unit_id="SU-001",
            description="Implement user registration endpoint",
            api_interactions=2,
            data_transformations=3,
            logical_branches=4,
            code_entities_modified=3,
            novelty_multiplier=1.0,
            est_complexity=43,
        )

        assert unit.unit_id == "SU-001"
        assert unit.api_interactions == 2
        assert unit.novelty_multiplier == 1.0
        assert unit.dependencies == []  # Default empty list

    def test_semantic_unit_with_dependencies(self):
        """Test SemanticUnit with dependencies."""
        unit = SemanticUnit(
            unit_id="SU-002",
            description="Build login endpoint",
            api_interactions=1,
            data_transformations=2,
            logical_branches=2,
            code_entities_modified=2,
            novelty_multiplier=1.0,
            est_complexity=26,
            dependencies=["SU-001"],
        )

        assert unit.dependencies == ["SU-001"]

    def test_semantic_unit_id_pattern_validation(self):
        """Test that unit_id must match pattern SU-XXX."""
        # Valid pattern
        unit = SemanticUnit(
            unit_id="SU-123",
            description="Valid unit",
            api_interactions=1,
            data_transformations=1,
            logical_branches=1,
            code_entities_modified=1,
            novelty_multiplier=1.0,
            est_complexity=10,
        )
        assert unit.unit_id == "SU-123"

        # Invalid patterns
        invalid_ids = ["SU-1", "SU-12", "SU-1234", "SU001", "su-001", "UNIT-001"]
        for invalid_id in invalid_ids:
            with pytest.raises(ValidationError):
                SemanticUnit(
                    unit_id=invalid_id,
                    description="Test unit here",
                    api_interactions=1,
                    data_transformations=1,
                    logical_branches=1,
                    code_entities_modified=1,
                    novelty_multiplier=1.0,
                    est_complexity=10,
                )

    def test_semantic_unit_factor_range_validation(self):
        """Test that complexity factors must be within valid ranges."""
        # Test api_interactions out of range
        with pytest.raises(ValidationError):
            SemanticUnit(
                unit_id="SU-001",
                description="Test unit here",
                api_interactions=15,  # Max is 10
                data_transformations=1,
                logical_branches=1,
                code_entities_modified=1,
                novelty_multiplier=1.0,
                est_complexity=10,
            )

        # Test novelty_multiplier out of range
        with pytest.raises(ValidationError):
            SemanticUnit(
                unit_id="SU-001",
                description="Test unit here",
                api_interactions=1,
                data_transformations=1,
                logical_branches=1,
                code_entities_modified=1,
                novelty_multiplier=2.5,  # Max is 2.0
                est_complexity=10,
            )

    def test_semantic_unit_complexity_range_validation(self):
        """Test that complexity must be between 1 and 100."""
        # Valid complexity
        unit = SemanticUnit(
            unit_id="SU-001",
            description="Test unit here",
            api_interactions=1,
            data_transformations=1,
            logical_branches=1,
            code_entities_modified=1,
            novelty_multiplier=1.0,
            est_complexity=50,
        )
        assert unit.est_complexity == 50

        # Invalid complexity (too high)
        with pytest.raises(ValidationError):
            SemanticUnit(
                unit_id="SU-001",
                description="Test unit here",
                api_interactions=1,
                data_transformations=1,
                logical_branches=1,
                code_entities_modified=1,
                novelty_multiplier=1.0,
                est_complexity=150,  # Max is 100
            )

    def test_semantic_unit_json_serialization(self):
        """Test JSON serialization and deserialization."""
        unit = SemanticUnit(
            unit_id="SU-001",
            description="Test semantic unit",
            api_interactions=2,
            data_transformations=3,
            logical_branches=4,
            code_entities_modified=3,
            novelty_multiplier=1.5,
            est_complexity=55,
            dependencies=["SU-000"],
        )

        # Serialize
        json_str = unit.model_dump_json()
        json_data = json.loads(json_str)

        assert json_data["unit_id"] == "SU-001"
        assert json_data["novelty_multiplier"] == 1.5
        assert json_data["dependencies"] == ["SU-000"]

        # Deserialize
        restored = SemanticUnit.model_validate_json(json_str)
        assert restored == unit


# =============================================================================
# PROBEAIPrediction Tests
# =============================================================================


class TestPROBEAIPrediction:
    """Test PROBEAIPrediction model."""

    def test_valid_probe_ai_prediction(self):
        """Test creating valid PROBE-AI prediction."""
        prediction = PROBEAIPrediction(
            total_est_latency_ms=45000.0,
            total_est_tokens=8500,
            total_est_api_cost=0.15,
            confidence=0.82,
        )

        assert prediction.total_est_latency_ms == 45000.0
        assert prediction.total_est_tokens == 8500
        assert prediction.total_est_api_cost == 0.15
        assert prediction.confidence == 0.82

    def test_probe_ai_prediction_non_negative_values(self):
        """Test that prediction values cannot be negative."""
        with pytest.raises(ValidationError):
            PROBEAIPrediction(
                total_est_latency_ms=-1000.0,  # Negative
                total_est_tokens=8500,
                total_est_api_cost=0.15,
                confidence=0.82,
            )

    def test_probe_ai_prediction_confidence_range(self):
        """Test that confidence must be between 0 and 1."""
        # Valid confidence
        prediction = PROBEAIPrediction(
            total_est_latency_ms=45000.0,
            total_est_tokens=8500,
            total_est_api_cost=0.15,
            confidence=0.95,
        )
        assert prediction.confidence == 0.95

        # Invalid confidence (too high)
        with pytest.raises(ValidationError):
            PROBEAIPrediction(
                total_est_latency_ms=45000.0,
                total_est_tokens=8500,
                total_est_api_cost=0.15,
                confidence=1.5,  # Max is 1.0
            )

    def test_probe_ai_prediction_json_serialization(self):
        """Test JSON serialization and deserialization."""
        prediction = PROBEAIPrediction(
            total_est_latency_ms=45000.0,
            total_est_tokens=8500,
            total_est_api_cost=0.15,
            confidence=0.82,
        )

        # Serialize
        json_str = prediction.model_dump_json()
        json_data = json.loads(json_str)

        assert json_data["total_est_latency_ms"] == 45000.0
        assert json_data["confidence"] == 0.82

        # Deserialize
        restored = PROBEAIPrediction.model_validate_json(json_str)
        assert restored == prediction


# =============================================================================
# ProjectPlan Tests
# =============================================================================


class TestProjectPlan:
    """Test ProjectPlan model."""

    def test_valid_project_plan_minimal(self):
        """Test creating ProjectPlan with minimal fields."""
        unit = SemanticUnit(
            unit_id="SU-001",
            description="Test unit here",
            api_interactions=2,
            data_transformations=3,
            logical_branches=2,
            code_entities_modified=2,
            novelty_multiplier=1.0,
            est_complexity=26,
        )

        plan = ProjectPlan(
            task_id="TASK-001", semantic_units=[unit], total_est_complexity=26
        )

        assert plan.task_id == "TASK-001"
        assert len(plan.semantic_units) == 1
        assert plan.total_est_complexity == 26
        assert plan.probe_ai_prediction is None
        assert plan.probe_ai_enabled is False

    def test_valid_project_plan_with_probe_ai(self):
        """Test ProjectPlan with PROBE-AI prediction."""
        units = [
            SemanticUnit(
                unit_id="SU-001",
                description="First unit here",
                api_interactions=2,
                data_transformations=2,
                logical_branches=2,
                code_entities_modified=2,
                novelty_multiplier=1.0,
                est_complexity=20,
            ),
            SemanticUnit(
                unit_id="SU-002",
                description="Second unit here",
                api_interactions=3,
                data_transformations=3,
                logical_branches=3,
                code_entities_modified=3,
                novelty_multiplier=1.0,
                est_complexity=30,
            ),
        ]

        prediction = PROBEAIPrediction(
            total_est_latency_ms=60000.0,
            total_est_tokens=10000,
            total_est_api_cost=0.20,
            confidence=0.85,
        )

        plan = ProjectPlan(
            project_id="PROJ-001",
            task_id="TASK-001",
            semantic_units=units,
            total_est_complexity=50,
            probe_ai_prediction=prediction,
            probe_ai_enabled=True,
        )

        assert plan.project_id == "PROJ-001"
        assert len(plan.semantic_units) == 2
        assert plan.total_est_complexity == 50
        assert plan.probe_ai_prediction is not None
        assert plan.probe_ai_enabled is True

    def test_project_plan_semantic_units_count_validation(self):
        """Test that semantic_units must have between 1 and 15 units."""
        # Valid: 1 unit (minimum)
        unit = SemanticUnit(
            unit_id="SU-001",
            description="Test unit here",
            api_interactions=1,
            data_transformations=1,
            logical_branches=1,
            code_entities_modified=1,
            novelty_multiplier=1.0,
            est_complexity=10,
        )

        plan = ProjectPlan(
            task_id="TASK-001", semantic_units=[unit], total_est_complexity=10
        )
        assert len(plan.semantic_units) == 1

        # Invalid: empty list
        with pytest.raises(ValidationError):
            ProjectPlan(
                task_id="TASK-001", semantic_units=[], total_est_complexity=0  # Empty
            )

        # Invalid: too many units (more than 15)
        too_many_units = [
            SemanticUnit(
                unit_id=f"SU-{i:03d}",
                description=f"Unit number {i}",
                api_interactions=1,
                data_transformations=1,
                logical_branches=1,
                code_entities_modified=1,
                novelty_multiplier=1.0,
                est_complexity=10,
            )
            for i in range(20)  # 20 units > max of 15
        ]

        with pytest.raises(ValidationError):
            ProjectPlan(
                task_id="TASK-001",
                semantic_units=too_many_units,
                total_est_complexity=200,
            )

    def test_project_plan_json_serialization(self):
        """Test JSON serialization and deserialization of complex ProjectPlan."""
        units = [
            SemanticUnit(
                unit_id="SU-001",
                description="First unit here",
                api_interactions=2,
                data_transformations=2,
                logical_branches=2,
                code_entities_modified=2,
                novelty_multiplier=1.0,
                est_complexity=20,
            ),
            SemanticUnit(
                unit_id="SU-002",
                description="Second unit here",
                api_interactions=3,
                data_transformations=3,
                logical_branches=3,
                code_entities_modified=3,
                novelty_multiplier=1.5,
                est_complexity=45,
                dependencies=["SU-001"],
            ),
        ]

        plan = ProjectPlan(
            project_id="PROJ-001",
            task_id="TASK-001",
            semantic_units=units,
            total_est_complexity=65,
            agent_version="1.0.0",
        )

        # Serialize
        json_str = plan.model_dump_json()
        json_data = json.loads(json_str)

        assert json_data["task_id"] == "TASK-001"
        assert len(json_data["semantic_units"]) == 2
        assert json_data["total_est_complexity"] == 65
        assert json_data["semantic_units"][1]["dependencies"] == ["SU-001"]

        # Deserialize
        restored = ProjectPlan.model_validate_json(json_str)
        assert restored == plan
        assert len(restored.semantic_units) == 2

    def test_project_plan_default_values(self):
        """Test that ProjectPlan has correct default values."""
        unit = SemanticUnit(
            unit_id="SU-001",
            description="Test unit here",
            api_interactions=1,
            data_transformations=1,
            logical_branches=1,
            code_entities_modified=1,
            novelty_multiplier=1.0,
            est_complexity=10,
        )

        plan = ProjectPlan(
            task_id="TASK-001", semantic_units=[unit], total_est_complexity=10
        )

        # Check defaults
        assert plan.project_id is None
        assert plan.probe_ai_prediction is None
        assert plan.probe_ai_enabled is False
        assert plan.agent_version == "1.0.0"


# =============================================================================
# Edge Cases and Integration Tests
# =============================================================================


class TestEdgeCases:
    """Test edge cases and integration scenarios."""

    def test_large_project_plan(self):
        """Test ProjectPlan with maximum allowed units."""
        units = [
            SemanticUnit(
                unit_id=f"SU-{i:03d}",
                description=f"Semantic unit {i}",
                api_interactions=2,
                data_transformations=2,
                logical_branches=2,
                code_entities_modified=2,
                novelty_multiplier=1.0,
                est_complexity=20,
            )
            for i in range(1, 16)  # 15 units (maximum)
        ]

        plan = ProjectPlan(
            task_id="LARGE-TASK", semantic_units=units, total_est_complexity=300
        )

        assert len(plan.semantic_units) == 15
        assert plan.total_est_complexity == 300

    def test_complex_dependency_chain(self):
        """Test SemanticUnits with complex dependency chain."""
        units = [
            SemanticUnit(
                unit_id="SU-001",
                description="Base unit here",
                api_interactions=1,
                data_transformations=1,
                logical_branches=1,
                code_entities_modified=1,
                novelty_multiplier=1.0,
                est_complexity=10,
                dependencies=[],
            ),
            SemanticUnit(
                unit_id="SU-002",
                description="Depends on SU-001",
                api_interactions=1,
                data_transformations=1,
                logical_branches=1,
                code_entities_modified=1,
                novelty_multiplier=1.0,
                est_complexity=10,
                dependencies=["SU-001"],
            ),
            SemanticUnit(
                unit_id="SU-003",
                description="Depends on SU-001 and SU-002",
                api_interactions=1,
                data_transformations=1,
                logical_branches=1,
                code_entities_modified=1,
                novelty_multiplier=1.0,
                est_complexity=10,
                dependencies=["SU-001", "SU-002"],
            ),
        ]

        plan = ProjectPlan(
            task_id="TASK-001", semantic_units=units, total_est_complexity=30
        )

        assert plan.semantic_units[0].dependencies == []
        assert plan.semantic_units[1].dependencies == ["SU-001"]
        assert plan.semantic_units[2].dependencies == ["SU-001", "SU-002"]

    def test_maximum_complexity_values(self):
        """Test SemanticUnit with maximum complexity values."""
        unit = SemanticUnit(
            unit_id="SU-999",
            description="Maximum complexity unit",
            api_interactions=10,  # Max
            data_transformations=10,  # Max
            logical_branches=10,  # Max
            code_entities_modified=10,  # Max
            novelty_multiplier=2.0,  # Max
            est_complexity=100,  # Max
        )

        assert unit.api_interactions == 10
        assert unit.data_transformations == 10
        assert unit.logical_branches == 10
        assert unit.code_entities_modified == 10
        assert unit.novelty_multiplier == 2.0
        assert unit.est_complexity == 100
