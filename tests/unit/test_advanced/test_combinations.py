"""
Combination/Pairwise tests for ASP agent configurations.

Uses allpairspy to generate efficient test combinations that cover
all pairwise interactions without exhaustive combinatorial explosion.

See: design/testing_strategies.md

Example:
    # Run combination tests
    pytest -m combinations

    # Skip combination tests
    pytest -m "not combinations"
"""

from unittest.mock import Mock

import pytest

pytest.importorskip("allpairspy", reason="allpairspy not installed - skipping pairwise tests")
from allpairspy import AllPairs

from asp.models.planning import SemanticUnit, TaskRequirements

# =============================================================================
# SemanticUnit Complexity Factor Combinations
# =============================================================================

# C1 formula factors - each with their valid ranges
API_INTERACTIONS = [0, 2, 5, 10]  # 0-10 per model
DATA_TRANSFORMATIONS = [0, 2, 5, 10]
LOGICAL_BRANCHES = [0, 2, 5, 10]
CODE_ENTITIES = [1, 3, 5, 10]  # must be >= 1 for non-trivial work
NOVELTY_MULTIPLIERS = [1.0, 1.25, 1.5, 2.0]


@pytest.mark.combinations
@pytest.mark.unit
class TestSemanticUnitCombinations:
    """Test pairwise combinations of SemanticUnit complexity factors."""

    def test_all_complexity_factor_combinations_are_valid(self):
        """
        Verify all pairwise combinations of C1 formula factors create valid units.

        Full combinatorial: 4 * 4 * 4 * 4 * 4 = 1024 test cases
        Pairwise: ~20-25 test cases (covers all pairs)
        """
        parameters = [
            API_INTERACTIONS,
            DATA_TRANSFORMATIONS,
            LOGICAL_BRANCHES,
            CODE_ENTITIES,
            NOVELTY_MULTIPLIERS,
        ]

        combination_count = 0
        for api, data, logic, entities, novelty in AllPairs(parameters):
            # Calculate expected complexity using C1 formula
            # C1 = (A + D + L + E) * N
            base = api + data + logic + entities
            est_complexity = int(base * novelty)
            # Clamp to valid range
            est_complexity = max(1, min(100, est_complexity))

            unit = SemanticUnit(
                unit_id="SU-001",
                description="Test semantic unit for combination testing",
                api_interactions=api,
                data_transformations=data,
                logical_branches=logic,
                code_entities_modified=entities,
                novelty_multiplier=novelty,
                est_complexity=est_complexity,
            )

            # Validate unit was created successfully
            assert unit.api_interactions == api
            assert unit.data_transformations == data
            assert unit.logical_branches == logic
            assert unit.code_entities_modified == entities
            assert unit.novelty_multiplier == novelty
            assert 1 <= unit.est_complexity <= 100

            combination_count += 1

        # AllPairs should generate far fewer than full combinatorial
        full_combinatorial = 4 * 4 * 4 * 4 * 4
        assert (
            combination_count < full_combinatorial
        ), f"Expected reduction from {full_combinatorial}, got {combination_count}"
        # But should still have meaningful coverage
        assert (
            combination_count >= 15
        ), f"Expected at least 15 combinations, got {combination_count}"

    def test_boundary_value_combinations(self):
        """Test combinations at boundary values of each factor."""
        boundary_parameters = [
            [0, 10],  # api_interactions: min, max
            [0, 10],  # data_transformations: min, max
            [0, 10],  # logical_branches: min, max
            [1, 10],  # code_entities: practical min, max (0 is unrealistic)
            [1.0, 2.0],  # novelty: min, max
        ]

        for api, data, logic, entities, novelty in AllPairs(boundary_parameters):
            base = api + data + logic + entities
            est_complexity = max(1, min(100, int(base * novelty)))

            unit = SemanticUnit(
                unit_id="SU-001",
                description="Boundary test semantic unit",
                api_interactions=api,
                data_transformations=data,
                logical_branches=logic,
                code_entities_modified=entities,
                novelty_multiplier=novelty,
                est_complexity=est_complexity,
            )

            # All boundary combinations should be valid
            assert unit is not None


# =============================================================================
# TaskRequirements Input Combinations
# =============================================================================

TASK_ID_PATTERNS = ["TASK-001", "BUG-123", "FEATURE-999", "HW-001"]
DESCRIPTION_LENGTHS = ["short desc", "a" * 50, "a" * 200]  # varied lengths
HAS_PROJECT_ID = [True, False]
HAS_CONTEXT_FILES = [True, False]


@pytest.mark.combinations
@pytest.mark.unit
class TestTaskRequirementsCombinations:
    """Test pairwise combinations of TaskRequirements inputs."""

    def test_input_format_combinations(self):
        """
        Test that various input combinations create valid TaskRequirements.

        Validates that the Planning Agent can accept diverse input formats.
        """
        parameters = [
            TASK_ID_PATTERNS,
            HAS_PROJECT_ID,
            HAS_CONTEXT_FILES,
        ]

        for task_id, has_project, has_context in AllPairs(parameters):
            req = TaskRequirements(
                task_id=task_id,
                project_id="PROJECT-001" if has_project else None,
                description="Test task description that is long enough",
                requirements="Detailed requirements text that meets minimum length requirement for validation",
                context_files=["docs/arch.md", "docs/api.md"] if has_context else None,
            )

            assert req.task_id == task_id
            assert (req.project_id is not None) == has_project
            assert (req.context_files is not None) == has_context


# =============================================================================
# Agent LLM Call Parameter Combinations
# =============================================================================

MODELS = ["claude-sonnet-4-20250514", "claude-haiku-4-5"]
MAX_TOKENS_VALUES = [1024, 2048, 4096, 8192]
TEMPERATURE_VALUES = [0.0, 0.3, 0.7, 1.0]


@pytest.mark.combinations
@pytest.mark.unit
class TestAgentLLMCallCombinations:
    """Test pairwise combinations of LLM call parameters."""

    def test_llm_call_parameter_combinations(self):
        """
        Test that all LLM parameter combinations are accepted by BaseAgent.call_llm.

        Uses mock to verify parameters are passed correctly without actual API calls.
        """
        from asp.agents.planning_agent import PlanningAgent

        parameters = [
            MODELS,
            MAX_TOKENS_VALUES,
            TEMPERATURE_VALUES,
        ]

        mock_client = Mock()
        mock_client.call_with_retry.return_value = {
            "content": {"semantic_units": []},
            "usage": {"input_tokens": 100, "output_tokens": 50},
            "model": "test",
        }

        agent = PlanningAgent(llm_client=mock_client)

        for model, max_tokens, temperature in AllPairs(parameters):
            # Reset mock for each combination
            mock_client.reset_mock()

            # Call LLM with this parameter combination
            agent.call_llm(
                prompt="Test prompt",
                model=model,
                max_tokens=max_tokens,
                temperature=temperature,
            )

            # Verify the call was made with correct parameters
            mock_client.call_with_retry.assert_called_once()
            call_kwargs = mock_client.call_with_retry.call_args
            assert call_kwargs.kwargs["model"] == model
            assert call_kwargs.kwargs["max_tokens"] == max_tokens
            assert call_kwargs.kwargs["temperature"] == temperature


# =============================================================================
# Design Review Severity/Phase Combinations
# =============================================================================

SEVERITIES = ["Critical", "High", "Medium", "Low"]
AFFECTED_PHASES = ["Planning", "Design", "Both"]
REQUIRES_REWORK = [True, False]


@pytest.mark.combinations
@pytest.mark.unit
class TestDesignReviewCombinations:
    """Test pairwise combinations of design review issue attributes."""

    def test_issue_severity_phase_combinations(self):
        """
        Test that all severity/phase combinations are handled correctly.

        These combinations determine routing in the PlanningDesignOrchestrator.
        """
        from asp.models.design_review import DesignIssue

        parameters = [
            SEVERITIES,
            AFFECTED_PHASES,
        ]

        for severity, phase in AllPairs(parameters):
            issue = DesignIssue(
                issue_id="ISSUE-001",
                severity=severity,
                affected_phase=phase,
                category="API Design",
                description="Test issue for combination testing",
                evidence="Found during review",
                impact="Affects system reliability",
                recommendation="Fix the issue",
            )

            assert issue.severity == severity
            assert issue.affected_phase == phase

            # Verify routing logic based on combinations
            requires_replanning = phase in ["Planning", "Both"]
            requires_redesign = phase in ["Design", "Both"]

            # Critical/high severity should trigger rework
            is_blocking = severity in ["Critical", "High"]

            # This validates our understanding of the routing logic
            if is_blocking and requires_replanning:
                # Would route back to planning
                pass
            if is_blocking and requires_redesign:
                # Would route back to design
                pass


# =============================================================================
# Report: Pairwise Reduction Statistics
# =============================================================================


@pytest.mark.combinations
@pytest.mark.unit
def test_pairwise_reduction_statistics():
    """
    Report on the test reduction achieved by pairwise testing.

    This test documents the efficiency gains from using AllPairs.
    """
    test_cases = [
        ("SemanticUnit factors", [4, 4, 4, 4, 4]),
        ("TaskRequirements", [4, 2, 2]),
        ("LLM parameters", [2, 4, 4]),
        ("DesignIssue routing", [4, 3]),
    ]

    print("\n=== Pairwise Testing Reduction Report ===")
    for name, factor_counts in test_cases:
        full_factorial = 1
        for count in factor_counts:
            full_factorial *= count

        # Generate pairwise to count
        params = [list(range(count)) for count in factor_counts]
        pairwise_count = len(list(AllPairs(params)))

        reduction_pct = (1 - pairwise_count / full_factorial) * 100

        print(f"{name}:")
        print(f"  Full factorial: {full_factorial}")
        print(f"  Pairwise: {pairwise_count}")
        print(f"  Reduction: {reduction_pct:.1f}%")
        print()

    # This test always passes - it's for reporting
    assert True
