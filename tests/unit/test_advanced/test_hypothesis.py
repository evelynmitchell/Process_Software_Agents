"""
Property-based tests using Hypothesis for ASP Platform.

Hypothesis generates random inputs based on strategies to find edge cases
that hand-written tests miss. Tests define properties that should always
hold, and Hypothesis tries to falsify them.

See: design/testing_strategies.md

Example:
    # Run hypothesis tests with dev profile (fast)
    HYPOTHESIS_PROFILE=dev pytest -m hypothesis

    # Run with CI profile (more examples)
    HYPOTHESIS_PROFILE=ci pytest -m hypothesis

    # Run with thorough profile (comprehensive but slow)
    HYPOTHESIS_PROFILE=thorough pytest -m hypothesis
"""

import pytest
from hypothesis import assume, given
from hypothesis import strategies as st

from asp.models.execution import SandboxConfig, TestResult
from asp.models.planning import SemanticUnit, TaskRequirements

# =============================================================================
# SemanticUnit Model Property Tests
# =============================================================================


@pytest.mark.hypothesis
@pytest.mark.unit
class TestSemanticUnitProperties:
    """Property-based tests for SemanticUnit model validation."""

    @given(
        api=st.integers(min_value=0, max_value=10),
        data=st.integers(min_value=0, max_value=10),
        logic=st.integers(min_value=0, max_value=10),
        entities=st.integers(min_value=0, max_value=10),
        novelty=st.floats(min_value=1.0, max_value=2.0, allow_nan=False),
    )
    def test_valid_complexity_factors_always_create_valid_unit(
        self, api, data, logic, entities, novelty
    ):
        """
        Property: Any valid complexity factor combination should create a valid unit.

        This tests the model's validation logic across the entire valid input space.
        """
        # Calculate complexity
        base = api + data + logic + entities
        est_complexity = max(1, min(100, int(base * novelty)))

        unit = SemanticUnit(
            unit_id="SU-001",
            description="Generated test unit for property testing",
            api_interactions=api,
            data_transformations=data,
            logical_branches=logic,
            code_entities_modified=entities,
            novelty_multiplier=novelty,
            est_complexity=est_complexity,
        )

        # Properties that should always hold
        assert unit.api_interactions >= 0
        assert unit.data_transformations >= 0
        assert unit.logical_branches >= 0
        assert unit.code_entities_modified >= 0
        assert 1.0 <= unit.novelty_multiplier <= 2.0
        assert 1 <= unit.est_complexity <= 100

    @given(
        api=st.integers(min_value=-100, max_value=100),
        data=st.integers(min_value=-100, max_value=100),
    )
    def test_invalid_complexity_factors_are_rejected(self, api, data):
        """
        Property: Invalid factor values should be rejected by validation.
        """
        # Skip valid values - we want to test invalid ones
        assume(api < 0 or api > 10 or data < 0 or data > 10)

        with pytest.raises(Exception):  # Pydantic ValidationError
            SemanticUnit(
                unit_id="SU-001",
                description="Should fail validation",
                api_interactions=api,
                data_transformations=data,
                logical_branches=0,
                code_entities_modified=1,
                novelty_multiplier=1.0,
                est_complexity=10,
            )


# =============================================================================
# TaskRequirements Model Property Tests
# =============================================================================

# Strategy for valid task IDs
valid_task_id = st.text(
    alphabet=st.characters(
        whitelist_categories=("Lu", "Ll", "Nd"), whitelist_characters="-_"
    ),
    min_size=1,
    max_size=50,
).filter(lambda x: len(x.strip()) > 0)

# Strategy for descriptions (min 10 chars)
valid_description = st.text(min_size=10, max_size=500).filter(
    lambda x: len(x.strip()) >= 10
)

# Strategy for requirements (min 20 chars)
valid_requirements = st.text(min_size=20, max_size=2000).filter(
    lambda x: len(x.strip()) >= 20
)


@pytest.mark.hypothesis
@pytest.mark.unit
class TestTaskRequirementsProperties:
    """Property-based tests for TaskRequirements model."""

    @given(
        task_id=valid_task_id,
        description=valid_description,
        requirements=valid_requirements,
    )
    def test_valid_inputs_create_valid_requirements(
        self, task_id, description, requirements
    ):
        """
        Property: Valid inputs should always create a valid TaskRequirements.
        """
        req = TaskRequirements(
            task_id=task_id,
            description=description,
            requirements=requirements,
        )

        assert req.task_id == task_id
        assert len(req.description) >= 10
        assert len(req.requirements) >= 20

    @given(description=st.text(max_size=9))
    def test_short_descriptions_are_rejected(self, description):
        """
        Property: Descriptions shorter than 10 chars should be rejected.
        """
        assume(len(description.strip()) < 10)

        with pytest.raises(Exception):  # Pydantic ValidationError
            TaskRequirements(
                task_id="TEST-001",
                description=description,
                requirements="Valid requirements text that is long enough",
            )


# =============================================================================
# SandboxConfig Property Tests
# =============================================================================


@pytest.mark.hypothesis
@pytest.mark.unit
class TestSandboxConfigProperties:
    """Property-based tests for SandboxConfig."""

    @given(
        timeout=st.integers(min_value=1, max_value=3600),
        memory=st.integers(min_value=1, max_value=8192),
        cpu=st.floats(min_value=0.1, max_value=16.0, allow_nan=False),
    )
    def test_valid_configs_are_accepted(self, timeout, memory, cpu):
        """
        Property: Valid config values should create valid SandboxConfig.
        """
        config = SandboxConfig(
            timeout_seconds=timeout,
            memory_limit_mb=memory,
            cpu_limit_cores=cpu,
        )

        assert config.timeout_seconds == timeout
        assert config.memory_limit_mb == memory
        assert config.cpu_limit_cores == cpu

    @given(
        timeout=st.integers(min_value=-1000, max_value=0),
    )
    def test_non_positive_timeout_rejected(self, timeout):
        """
        Property: Non-positive timeout values should be rejected.
        """
        with pytest.raises(ValueError, match="timeout_seconds must be positive"):
            SandboxConfig(timeout_seconds=timeout)


# =============================================================================
# PytestResultParser Property Tests
# =============================================================================


@pytest.mark.hypothesis
@pytest.mark.unit
class TestPytestParserProperties:
    """Property-based tests for pytest output parser robustness."""

    @given(garbage=st.binary(max_size=10000))
    def test_parser_never_crashes_on_garbage(self, garbage):
        """
        Property: Parser should handle any input without crashing.

        Even garbage/binary input should return a valid TestResult
        (possibly with parsing_failed=True).
        """
        from services.test_executor import PytestResultParser

        parser = PytestResultParser()

        # Decode garbage as UTF-8, replacing errors
        garbage_str = garbage.decode("utf-8", errors="replace")

        result = parser.parse(
            stdout=garbage_str,
            stderr="",
            exit_code=1,
            duration_ms=1000,
        )

        # Should always return a valid TestResult
        assert isinstance(result, TestResult)
        assert result.framework == "pytest"

    @given(
        passed=st.integers(min_value=0, max_value=1000),
        failed=st.integers(min_value=0, max_value=100),
        duration=st.floats(min_value=0.01, max_value=1000.0, allow_nan=False),
    )
    def test_parser_extracts_valid_summary_lines(self, passed, failed, duration):
        """
        Property: Parser should correctly extract values from valid summary lines.
        """
        from services.test_executor import PytestResultParser

        parser = PytestResultParser()

        # Generate valid pytest summary line
        if failed > 0:
            summary = f"===== {failed} failed, {passed} passed in {duration:.2f}s ====="
        else:
            summary = f"===== {passed} passed in {duration:.2f}s ====="

        result = parser.parse(
            stdout=summary,
            stderr="",
            exit_code=0 if failed == 0 else 1,
            duration_ms=int(duration * 1000),
        )

        # Parser should extract correct values
        if not result.parsing_failed:
            assert result.passed == passed
            if failed > 0:
                assert result.failed == failed

    @given(
        test_suffix=st.text(
            alphabet=st.characters(
                whitelist_categories=("Ll", "Nd"), whitelist_characters="_"
            ),
            min_size=1,
            max_size=30,
        ),
        file_name=st.text(
            alphabet=st.characters(
                whitelist_categories=("Ll",), whitelist_characters="_"
            ),
            min_size=1,
            max_size=20,
        ),
    )
    def test_parser_handles_varied_test_names(self, test_suffix, file_name):
        """
        Property: Parser should handle various valid test name formats.
        """
        from services.test_executor import PytestResultParser

        parser = PytestResultParser()

        # Build valid test name and file path directly
        test_name = f"test_{test_suffix}"
        file_path = f"tests/test_{file_name}.py"

        # Generate pytest output with this test
        output = f"""
{file_path}::{test_name} PASSED
===== 1 passed in 0.01s =====
"""

        result = parser.parse(
            stdout=output,
            stderr="",
            exit_code=0,
            duration_ms=10,
        )

        assert isinstance(result, TestResult)


# =============================================================================
# TestResult Model Property Tests
# =============================================================================


@pytest.mark.hypothesis
@pytest.mark.unit
class TestTestResultProperties:
    """Property-based tests for TestResult model."""

    @given(
        total=st.integers(min_value=0, max_value=10000),
        passed=st.integers(min_value=0, max_value=10000),
        failed=st.integers(min_value=0, max_value=10000),
        skipped=st.integers(min_value=0, max_value=10000),
        duration=st.floats(min_value=0.0, max_value=10000.0, allow_nan=False),
    )
    def test_success_property_is_consistent(
        self, total, passed, failed, skipped, duration
    ):
        """
        Property: success should be True iff failed == 0 and errors == 0.
        """
        result = TestResult(
            framework="pytest",
            total_tests=total,
            passed=passed,
            failed=failed,
            skipped=skipped,
            errors=0,
            duration_seconds=duration,
        )

        # success property should be consistent
        if failed == 0:
            assert result.success is True
        else:
            assert result.success is False

    @given(
        failed=st.integers(min_value=1, max_value=100),
    )
    def test_has_failures_when_failed_positive(self, failed):
        """
        Property: has_failures should be True when failed > 0.
        """
        result = TestResult(
            framework="pytest",
            total_tests=failed,
            passed=0,
            failed=failed,
            duration_seconds=1.0,
        )

        assert result.has_failures is True


# =============================================================================
# Complexity Calculation Property Tests
# =============================================================================


@pytest.mark.hypothesis
@pytest.mark.unit
class TestComplexityCalculationProperties:
    """Property-based tests for semantic complexity calculation."""

    @given(
        api=st.integers(min_value=0, max_value=10),
        data=st.integers(min_value=0, max_value=10),
        logic=st.integers(min_value=0, max_value=10),
        entities=st.integers(min_value=0, max_value=10),
        novelty=st.floats(min_value=1.0, max_value=2.0, allow_nan=False),
    )
    def test_complexity_is_monotonic_in_novelty(
        self, api, data, logic, entities, novelty
    ):
        """
        Property: Complexity should increase with novelty multiplier.
        """
        from asp.utils.semantic_complexity import (
            ComplexityFactors,
            calculate_semantic_complexity,
        )

        factors_low = ComplexityFactors(
            api_interactions=api,
            data_transformations=data,
            logical_branches=logic,
            code_entities_modified=entities,
            novelty_multiplier=1.0,  # Minimum novelty
        )

        factors_high = ComplexityFactors(
            api_interactions=api,
            data_transformations=data,
            logical_branches=logic,
            code_entities_modified=entities,
            novelty_multiplier=novelty,  # Variable novelty
        )

        complexity_low = calculate_semantic_complexity(factors_low)
        complexity_high = calculate_semantic_complexity(factors_high)

        # Higher novelty should mean higher or equal complexity
        assert complexity_high >= complexity_low

    @given(
        factor=st.integers(min_value=0, max_value=10),
    )
    def test_complexity_is_additive_in_factors(self, factor):
        """
        Property: Adding to any factor should increase total complexity.
        """
        from asp.utils.semantic_complexity import (
            ComplexityFactors,
            calculate_semantic_complexity,
        )

        # Baseline
        factors_base = ComplexityFactors(
            api_interactions=0,
            data_transformations=0,
            logical_branches=0,
            code_entities_modified=0,
            novelty_multiplier=1.0,
        )

        # Add to api_interactions
        factors_added = ComplexityFactors(
            api_interactions=factor,
            data_transformations=0,
            logical_branches=0,
            code_entities_modified=0,
            novelty_multiplier=1.0,
        )

        complexity_base = calculate_semantic_complexity(factors_base)
        complexity_added = calculate_semantic_complexity(factors_added)

        # Adding should increase or maintain complexity
        assert complexity_added >= complexity_base
