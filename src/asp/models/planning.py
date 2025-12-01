"""
Data Models for Planning Agent

This module defines Pydantic models for Planning Agent input and output:
- TaskRequirements: Input to Planning Agent
- SemanticUnit: A decomposed unit of work
- ProjectPlan: Output from Planning Agent

Author: ASP Development Team
Date: November 13, 2025
"""


from pydantic import BaseModel, Field


class TaskRequirements(BaseModel):
    """
    Input to Planning Agent.

    Represents a high-level task that needs to be decomposed into
    semantic units for implementation.
    """

    task_id: str = Field(
        ...,
        description="Unique task identifier (e.g., 'TASK-2025-001')",
        min_length=1,
    )

    project_id: str | None = Field(
        None,
        description="Project identifier for grouping related tasks",
    )

    description: str = Field(
        ...,
        description="High-level task description (1-2 sentences)",
        min_length=10,
    )

    requirements: str = Field(
        ...,
        description="Detailed requirements text (user stories, acceptance criteria, etc.)",
        min_length=20,
    )

    context_files: list[str] | None = Field(
        default=None,
        description="Paths to context files (architecture docs, design specs, etc.)",
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "task_id": "TASK-2025-001",
                    "project_id": "ASP-PLATFORM",
                    "description": "Build user authentication system with JWT",
                    "requirements": """
                        - User registration with email/password
                        - Login endpoint with JWT token generation
                        - Token validation middleware
                        - Password hashing with bcrypt
                        - Input validation and error handling
                    """,
                    "context_files": ["docs/architecture.md", "docs/api_spec.md"],
                }
            ]
        }
    }


class SemanticUnit(BaseModel):
    """
    A decomposed unit of work.

    Represents a single semantic unit that can be implemented by one agent
    in 1-4 hours. Contains complexity scoring factors per the C1 formula.
    """

    unit_id: str = Field(
        ...,
        description="Unique unit identifier (e.g., 'SU-001')",
        pattern=r"^SU-\d{3}$",
    )

    description: str = Field(
        ...,
        description="Clear description of work to be done",
        min_length=10,
    )

    # C1 Formula Factors (PRD Section 13.1)
    api_interactions: int = Field(
        ...,
        ge=0,
        le=10,
        description="Number of external API calls or integrations",
    )

    data_transformations: int = Field(
        ...,
        ge=0,
        le=10,
        description="Number of data format conversions or mappings",
    )

    logical_branches: int = Field(
        ...,
        ge=0,
        le=10,
        description="Number of if/else, switch, or conditional logic points",
    )

    code_entities_modified: int = Field(
        ...,
        ge=0,
        le=10,
        description="Number of classes, functions, or modules to create/modify",
    )

    novelty_multiplier: float = Field(
        ...,
        ge=1.0,
        le=2.0,
        description="1.0 (familiar), 1.5 (moderate), 2.0 (novel)",
    )

    # Calculated Complexity
    est_complexity: int = Field(
        ...,
        ge=1,
        le=100,
        description="Semantic Complexity Score (calculated using C1 formula)",
    )

    # Optional dependencies
    dependencies: list[str] = Field(
        default_factory=list,
        description="List of unit_ids that this unit depends on (e.g., ['SU-001', 'SU-002'])",
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "unit_id": "SU-001",
                    "description": "Implement JWT token generation endpoint",
                    "api_interactions": 2,
                    "data_transformations": 3,
                    "logical_branches": 2,
                    "code_entities_modified": 3,
                    "novelty_multiplier": 1.0,
                    "est_complexity": 19,
                }
            ]
        }
    }


class PROBEAIPrediction(BaseModel):
    """
    PROBE-AI estimation results.

    Contains predicted effort metrics based on historical data and
    linear regression. Only populated when PROBE-AI is enabled (Phase 2).
    """

    total_est_latency_ms: float = Field(
        ...,
        ge=0,
        description="Predicted total execution time in milliseconds",
    )

    total_est_tokens: int = Field(
        ...,
        ge=0,
        description="Predicted total token usage (input + output)",
    )

    total_est_api_cost: float = Field(
        ...,
        ge=0,
        description="Predicted total API cost in USD",
    )

    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="R² coefficient indicating prediction confidence",
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "total_est_latency_ms": 45000.0,
                    "total_est_tokens": 8500,
                    "total_est_api_cost": 0.15,
                    "confidence": 0.82,
                }
            ]
        }
    }


class ProjectPlan(BaseModel):
    """
    Output from Planning Agent.

    Contains the decomposed semantic units with complexity scores and
    optional PROBE-AI predictions (Phase 2).
    """

    project_id: str | None = Field(
        None,
        description="Project identifier",
    )

    task_id: str = Field(
        ...,
        description="Task identifier",
    )

    semantic_units: list[SemanticUnit] = Field(
        ...,
        min_length=1,
        max_length=15,
        description="List of decomposed semantic units (typically 3-8)",
    )

    total_est_complexity: int = Field(
        ...,
        ge=1,
        description="Sum of all unit complexities",
    )

    # PROBE-AI predictions (None until Phase 2)
    probe_ai_prediction: PROBEAIPrediction | None = Field(
        None,
        description="PROBE-AI predictions (None if insufficient historical data)",
    )

    # Metadata
    probe_ai_enabled: bool = Field(
        False,
        description="Whether PROBE-AI was used for estimation",
    )

    agent_version: str = Field(
        "1.0.0",
        description="Planning Agent version that created this plan",
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "project_id": "ASP-PLATFORM",
                    "task_id": "TASK-2025-001",
                    "semantic_units": [
                        {
                            "unit_id": "SU-001",
                            "description": "Design JWT authentication schema",
                            "api_interactions": 1,
                            "data_transformations": 2,
                            "logical_branches": 1,
                            "code_entities_modified": 2,
                            "novelty_multiplier": 1.0,
                            "est_complexity": 13,
                        },
                        {
                            "unit_id": "SU-002",
                            "description": "Implement user registration endpoint",
                            "api_interactions": 2,
                            "data_transformations": 3,
                            "logical_branches": 3,
                            "code_entities_modified": 3,
                            "novelty_multiplier": 1.0,
                            "est_complexity": 21,
                        },
                    ],
                    "total_est_complexity": 34,
                    "probe_ai_prediction": None,
                    "probe_ai_enabled": False,
                    "agent_version": "1.0.0",
                }
            ]
        }
    }
