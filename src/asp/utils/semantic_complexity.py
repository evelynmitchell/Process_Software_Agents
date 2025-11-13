"""
Semantic Complexity Calculation (C1 Formula)

Implements the Semantic Complexity formula from PRD Section 13.1.
This formula estimates the complexity of a semantic unit based on:
- API interactions
- Data transformations
- Logical branches
- Code entities modified
- Novelty multiplier

Formula:
    Semantic_Complexity = (
        (2 × API_Interactions) +
        (5 × Data_Transformations) +
        (3 × Logical_Branches) +
        (4 × Code_Entities_Modified)
    ) × Novelty_Multiplier

Where Novelty_Multiplier:
    - 1.0 = Familiar (done before)
    - 1.5 = Moderate (some new concepts)
    - 2.0 = Novel (entirely new)

Author: ASP Development Team
Date: November 13, 2025
"""

from pydantic import BaseModel, Field


class ComplexityFactors(BaseModel):
    """
    Input factors for semantic complexity calculation.

    These factors are identified by the Planning Agent when analyzing
    a semantic unit.
    """

    api_interactions: int = Field(
        ...,
        ge=0,
        le=10,
        description="Number of external API calls or integrations (0-10)",
    )

    data_transformations: int = Field(
        ...,
        ge=0,
        le=10,
        description="Number of data format conversions or mappings (0-10)",
    )

    logical_branches: int = Field(
        ...,
        ge=0,
        le=10,
        description="Number of if/else, switch, or conditional logic points (0-10)",
    )

    code_entities_modified: int = Field(
        ...,
        ge=0,
        le=10,
        description="Number of classes, functions, or modules to create/modify (0-10)",
    )

    novelty_multiplier: float = Field(
        ...,
        ge=1.0,
        le=2.0,
        description="1.0 (familiar), 1.5 (moderate), 2.0 (novel)",
    )


def calculate_semantic_complexity(factors: ComplexityFactors) -> int:
    """
    Calculate Semantic Complexity using C1 formula (PRD Section 13.1).

    This formula combines multiple factors to estimate the complexity of
    implementing a semantic unit. Higher scores indicate more complex work.

    Complexity Bands:
        - 1-10: Trivial (config change, simple CRUD)
        - 11-30: Simple (single API endpoint, basic logic)
        - 31-60: Moderate (multiple components, some integration)
        - 61-80: Complex (cross-system integration, novel algorithms)
        - 81-100: Very Complex (architectural changes, high novelty)

    Args:
        factors: ComplexityFactors with all required inputs

    Returns:
        int: Complexity score (typically 1-100, though can exceed for very complex tasks)

    Example:
        >>> factors = ComplexityFactors(
        ...     api_interactions=2,
        ...     data_transformations=3,
        ...     logical_branches=1,
        ...     code_entities_modified=2,
        ...     novelty_multiplier=1.0
        ... )
        >>> calculate_semantic_complexity(factors)
        19
    """
    # Calculate base score (weighted sum of factors)
    base_score = (
        (2 * factors.api_interactions)
        + (5 * factors.data_transformations)
        + (3 * factors.logical_branches)
        + (4 * factors.code_entities_modified)
    )

    # Apply novelty multiplier
    total = base_score * factors.novelty_multiplier

    # Round to nearest integer
    return round(total)


def validate_complexity_factors(factors: dict) -> ComplexityFactors:
    """
    Validate complexity factors from LLM output.

    This is a convenience function that wraps Pydantic validation
    with better error messages.

    Args:
        factors: Dictionary of factors from LLM

    Returns:
        ComplexityFactors: Validated factors

    Raises:
        ValueError: If factors are invalid
    """
    try:
        return ComplexityFactors.model_validate(factors)
    except Exception as e:
        raise ValueError(
            f"Invalid complexity factors: {e}\n"
            f"Expected fields: api_interactions, data_transformations, "
            f"logical_branches, code_entities_modified, novelty_multiplier\n"
            f"Received: {factors}"
        ) from e


def get_complexity_band(complexity: int) -> str:
    """
    Get human-readable complexity band for a given score.

    Args:
        complexity: Complexity score

    Returns:
        str: Complexity band name

    Example:
        >>> get_complexity_band(15)
        'Simple'
        >>> get_complexity_band(75)
        'Complex'
    """
    if complexity <= 10:
        return "Trivial"
    elif complexity <= 30:
        return "Simple"
    elif complexity <= 60:
        return "Moderate"
    elif complexity <= 80:
        return "Complex"
    else:
        return "Very Complex"
