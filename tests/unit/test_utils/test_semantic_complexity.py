"""
Unit tests for semantic_complexity.py

Tests the C1 formula implementation and complexity band classification.
"""

import pytest
from pydantic import ValidationError

from asp.utils.semantic_complexity import (
    ComplexityFactors,
    calculate_semantic_complexity,
    get_complexity_band,
    validate_complexity_factors,
)


class TestComplexityFactors:
    """Test ComplexityFactors Pydantic model validation."""

    def test_valid_factors(self):
        """Test that valid factors are accepted."""
        factors = ComplexityFactors(
            api_interactions=2,
            data_transformations=3,
            logical_branches=1,
            code_entities_modified=2,
            novelty_multiplier=1.0,
        )
        assert factors.api_interactions == 2
        assert factors.data_transformations == 3
        assert factors.logical_branches == 1
        assert factors.code_entities_modified == 2
        assert factors.novelty_multiplier == 1.0

    def test_factors_out_of_range(self):
        """Test that out-of-range factors are rejected."""
        # api_interactions > 10
        with pytest.raises(ValidationError):
            ComplexityFactors(
                api_interactions=15,
                data_transformations=3,
                logical_branches=1,
                code_entities_modified=2,
                novelty_multiplier=1.0,
            )

        # novelty_multiplier > 2.0
        with pytest.raises(ValidationError):
            ComplexityFactors(
                api_interactions=2,
                data_transformations=3,
                logical_branches=1,
                code_entities_modified=2,
                novelty_multiplier=2.5,
            )

    def test_negative_factors(self):
        """Test that negative factors are rejected."""
        with pytest.raises(ValidationError):
            ComplexityFactors(
                api_interactions=-1,
                data_transformations=3,
                logical_branches=1,
                code_entities_modified=2,
                novelty_multiplier=1.0,
            )


class TestCalculateSemanticComplexity:
    """Test calculate_semantic_complexity function."""

    def test_simple_calculation(self):
        """Test C1 formula with simple inputs."""
        factors = ComplexityFactors(
            api_interactions=2,
            data_transformations=3,
            logical_branches=1,
            code_entities_modified=2,
            novelty_multiplier=1.0,
        )
        # Expected: (2*2) + (5*3) + (3*1) + (4*2) = 4 + 15 + 3 + 8 = 30
        # With 1.0 multiplier: 30 * 1.0 = 30
        result = calculate_semantic_complexity(factors)
        assert result == 30

    def test_with_moderate_novelty(self):
        """Test C1 formula with moderate novelty multiplier."""
        factors = ComplexityFactors(
            api_interactions=2,
            data_transformations=3,
            logical_branches=1,
            code_entities_modified=2,
            novelty_multiplier=1.5,
        )
        # Base: 30 (from previous test)
        # With 1.5 multiplier: 30 * 1.5 = 45
        result = calculate_semantic_complexity(factors)
        assert result == 45

    def test_with_high_novelty(self):
        """Test C1 formula with high novelty multiplier."""
        factors = ComplexityFactors(
            api_interactions=2,
            data_transformations=3,
            logical_branches=1,
            code_entities_modified=2,
            novelty_multiplier=2.0,
        )
        # Base: 30
        # With 2.0 multiplier: 30 * 2.0 = 60
        result = calculate_semantic_complexity(factors)
        assert result == 60

    def test_zero_factors(self):
        """Test C1 formula with all zero factors."""
        factors = ComplexityFactors(
            api_interactions=0,
            data_transformations=0,
            logical_branches=0,
            code_entities_modified=0,
            novelty_multiplier=1.0,
        )
        # Expected: 0 * 1.0 = 0
        result = calculate_semantic_complexity(factors)
        assert result == 0

    def test_max_factors(self):
        """Test C1 formula with maximum factors."""
        factors = ComplexityFactors(
            api_interactions=10,
            data_transformations=10,
            logical_branches=10,
            code_entities_modified=10,
            novelty_multiplier=2.0,
        )
        # Base: (2*10) + (5*10) + (3*10) + (4*10) = 20 + 50 + 30 + 40 = 140
        # With 2.0 multiplier: 140 * 2.0 = 280
        result = calculate_semantic_complexity(factors)
        assert result == 280

    def test_rounding(self):
        """Test that complexity is rounded to nearest integer."""
        factors = ComplexityFactors(
            api_interactions=1,
            data_transformations=1,
            logical_branches=1,
            code_entities_modified=1,
            novelty_multiplier=1.5,
        )
        # Base: (2*1) + (5*1) + (3*1) + (4*1) = 2 + 5 + 3 + 4 = 14
        # With 1.5 multiplier: 14 * 1.5 = 21.0
        result = calculate_semantic_complexity(factors)
        assert result == 21
        assert isinstance(result, int)

    def test_prd_example_1(self):
        """Test example from PRD: simple REST API endpoint."""
        # Example: GET /users/:id endpoint
        factors = ComplexityFactors(
            api_interactions=1,
            data_transformations=2,
            logical_branches=2,
            code_entities_modified=2,
            novelty_multiplier=1.0,
        )
        # Expected: (2*1) + (5*2) + (3*2) + (4*2) = 2 + 10 + 6 + 8 = 26
        result = calculate_semantic_complexity(factors)
        assert result == 26

    def test_prd_example_2(self):
        """Test example from prompt: JWT authentication."""
        # Example: User registration with password hashing
        factors = ComplexityFactors(
            api_interactions=2,
            data_transformations=3,
            logical_branches=4,
            code_entities_modified=3,
            novelty_multiplier=1.0,
        )
        # Expected: (2*2) + (5*3) + (3*4) + (4*3) = 4 + 15 + 12 + 12 = 43
        result = calculate_semantic_complexity(factors)
        assert result == 43


class TestValidateComplexityFactors:
    """Test validate_complexity_factors helper function."""

    def test_valid_dict(self):
        """Test validation of valid factor dictionary."""
        factors_dict = {
            "api_interactions": 2,
            "data_transformations": 3,
            "logical_branches": 1,
            "code_entities_modified": 2,
            "novelty_multiplier": 1.0,
        }
        factors = validate_complexity_factors(factors_dict)
        assert isinstance(factors, ComplexityFactors)
        assert factors.api_interactions == 2

    def test_invalid_dict(self):
        """Test validation of invalid factor dictionary."""
        factors_dict = {
            "api_interactions": 2,
            "data_transformations": 3,
            # Missing required fields
        }
        with pytest.raises(ValueError, match="Invalid complexity factors"):
            validate_complexity_factors(factors_dict)

    def test_invalid_types(self):
        """Test validation with invalid types."""
        factors_dict = {
            "api_interactions": "two",  # Should be int
            "data_transformations": 3,
            "logical_branches": 1,
            "code_entities_modified": 2,
            "novelty_multiplier": 1.0,
        }
        with pytest.raises(ValueError):
            validate_complexity_factors(factors_dict)


class TestGetComplexityBand:
    """Test get_complexity_band function."""

    def test_trivial_band(self):
        """Test complexity band for trivial tasks."""
        assert get_complexity_band(1) == "Trivial"
        assert get_complexity_band(5) == "Trivial"
        assert get_complexity_band(10) == "Trivial"

    def test_simple_band(self):
        """Test complexity band for simple tasks."""
        assert get_complexity_band(11) == "Simple"
        assert get_complexity_band(20) == "Simple"
        assert get_complexity_band(30) == "Simple"

    def test_moderate_band(self):
        """Test complexity band for moderate tasks."""
        assert get_complexity_band(31) == "Moderate"
        assert get_complexity_band(45) == "Moderate"
        assert get_complexity_band(60) == "Moderate"

    def test_complex_band(self):
        """Test complexity band for complex tasks."""
        assert get_complexity_band(61) == "Complex"
        assert get_complexity_band(70) == "Complex"
        assert get_complexity_band(80) == "Complex"

    def test_very_complex_band(self):
        """Test complexity band for very complex tasks."""
        assert get_complexity_band(81) == "Very Complex"
        assert get_complexity_band(100) == "Very Complex"
        assert get_complexity_band(200) == "Very Complex"

    def test_boundary_values(self):
        """Test complexity band boundaries."""
        assert get_complexity_band(10) == "Trivial"
        assert get_complexity_band(11) == "Simple"
        assert get_complexity_band(30) == "Simple"
        assert get_complexity_band(31) == "Moderate"
        assert get_complexity_band(60) == "Moderate"
        assert get_complexity_band(61) == "Complex"
        assert get_complexity_band(80) == "Complex"
        assert get_complexity_band(81) == "Very Complex"
