"""
Pydantic models for Design Agent input and output.

This module defines the data structures for the Design Agent (FR-2), which creates
low-level technical design specifications from requirements and project plans.

Models:
    - DesignInput: Input to Design Agent (requirements + project plan)
    - APIContract: API endpoint specification
    - DataSchema: Database table specification
    - ComponentLogic: Component/module specification
    - DesignReviewChecklistItem: Individual design review checklist item
    - DesignSpecification: Complete design output from Design Agent

Design Agent Flow:
    1. Receives DesignInput (requirements + ProjectPlan from Planning Agent)
    2. Generates comprehensive DesignSpecification
    3. Output includes API contracts, data schemas, component logic, and review checklist
    4. DesignSpecification is used by Design Review Agent (FR-3) and Coding Agent (FR-4)

Author: ASP Development Team
Date: 2025-11-13
"""

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field, field_validator

from asp.models.planning import ProjectPlan  # Import Planning Agent output


# =============================================================================
# Input Models
# =============================================================================


class DesignInput(BaseModel):
    """
    Input to Design Agent.

    Combines user requirements with the project plan from Planning Agent to
    produce a detailed technical design.

    Attributes:
        task_id: Unique task identifier (must match Planning Agent task_id)
        requirements: Original user requirements (natural language)
        project_plan: ProjectPlan output from Planning Agent
        context_files: Optional context (architecture docs, coding standards, etc.)
        design_constraints: Optional constraints (technology choices, patterns to follow)
    """

    task_id: str = Field(
        ...,
        description="Unique task identifier",
        min_length=3,
        max_length=100,
        examples=["DESIGN-001", "JWT-AUTH-2025-11-13"],
    )

    requirements: str = Field(
        ...,
        description="Original user requirements (natural language)",
        min_length=20,
        examples=[
            "Build a REST API for user authentication using JWT tokens. "
            "Users should be able to register, login, and logout. "
            "Include rate limiting and password hashing."
        ],
    )

    project_plan: ProjectPlan = Field(
        ...,
        description="ProjectPlan output from Planning Agent",
    )

    context_files: list[str] = Field(
        default_factory=list,
        description="Optional context files (architecture docs, standards)",
        examples=[["Claude.md", "ARCHITECTURE.md", "API_STANDARDS.md"]],
    )

    design_constraints: Optional[str] = Field(
        default=None,
        description="Optional design constraints (technology choices, patterns)",
        examples=[
            "Use FastAPI framework, PostgreSQL database, and Redis for caching. "
            "Follow RESTful API best practices."
        ],
    )

    @field_validator("task_id")
    @classmethod
    def validate_task_id(cls, v: str) -> str:
        """Validate task_id format."""
        if not v or len(v.strip()) < 3:
            raise ValueError("task_id must be at least 3 characters")
        return v.strip()

    @field_validator("requirements")
    @classmethod
    def validate_requirements(cls, v: str) -> str:
        """Validate requirements are substantial."""
        if not v or len(v.strip()) < 20:
            raise ValueError("requirements must be at least 20 characters")
        return v.strip()

    model_config = {
        "json_schema_extra": {
            "example": {
                "task_id": "JWT-AUTH-001",
                "requirements": "Build JWT authentication system with registration and login",
                "project_plan": {
                    "task_id": "JWT-AUTH-001",
                    "semantic_units": [],
                    "total_complexity": 250,
                },
                "context_files": ["ARCHITECTURE.md"],
                "design_constraints": "Use FastAPI and PostgreSQL",
            }
        }
    }


# =============================================================================
# Output Models - Design Components
# =============================================================================


class APIContract(BaseModel):
    """
    API endpoint specification.

    Defines a single API endpoint with complete request/response schemas,
    error handling, and implementation guidance.

    Attributes:
        endpoint: URL path (e.g., "/api/v1/users")
        method: HTTP method (GET, POST, PUT, DELETE, PATCH)
        description: What this endpoint does
        request_schema: JSON schema for request body (None for GET)
        request_params: Query parameters or path parameters
        response_schema: JSON schema for successful response
        error_responses: List of possible error responses
        authentication_required: Whether endpoint requires auth
        rate_limit: Optional rate limit specification
    """

    endpoint: str = Field(
        ...,
        description="URL path for this endpoint",
        min_length=1,
        examples=["/api/v1/users", "/api/v1/auth/login"],
    )

    method: str = Field(
        ...,
        description="HTTP method",
        pattern="^(GET|POST|PUT|DELETE|PATCH)$",
        examples=["POST", "GET"],
    )

    description: str = Field(
        ...,
        description="What this endpoint does",
        min_length=10,
        examples=["Register a new user with email and password"],
    )

    request_schema: Optional[dict[str, Any]] = Field(
        default=None,
        description="JSON schema for request body (None for GET)",
        examples=[
            {
                "email": "string (email format, required)",
                "password": "string (min 8 chars, required)",
                "username": "string (min 3 chars, optional)",
            }
        ],
    )

    request_params: Optional[dict[str, str]] = Field(
        default=None,
        description="Query parameters or path parameters",
        examples=[{"user_id": "string (UUID, path parameter)"}],
    )

    response_schema: dict[str, Any] = Field(
        ...,
        description="JSON schema for successful response",
        examples=[
            {
                "user_id": "string (UUID)",
                "email": "string",
                "created_at": "string (ISO 8601 timestamp)",
            }
        ],
    )

    error_responses: list[dict[str, Any]] = Field(
        default_factory=list,
        description="List of possible error responses",
        examples=[
            [
                {"status": 400, "code": "INVALID_EMAIL", "message": "Email format invalid"},
                {"status": 409, "code": "USER_EXISTS", "message": "User already exists"},
            ]
        ],
    )

    authentication_required: bool = Field(
        default=False,
        description="Whether endpoint requires authentication",
    )

    rate_limit: Optional[str] = Field(
        default=None,
        description="Rate limit specification",
        examples=["10 requests per minute per IP"],
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "endpoint": "/api/v1/auth/register",
                "method": "POST",
                "description": "Register a new user with email and password",
                "request_schema": {
                    "email": "string (email format, required)",
                    "password": "string (min 8 chars, required)",
                },
                "response_schema": {
                    "user_id": "string (UUID)",
                    "email": "string",
                },
                "error_responses": [
                    {"status": 400, "code": "INVALID_EMAIL"},
                ],
                "authentication_required": False,
                "rate_limit": "5 requests per minute per IP",
            }
        }
    }


class DataSchema(BaseModel):
    """
    Database table specification.

    Defines a single database table with columns, constraints, indexes,
    and relationships.

    Attributes:
        table_name: Name of the table
        description: Purpose of this table
        columns: List of column specifications
        indexes: List of index specifications
        relationships: Foreign key relationships to other tables
        constraints: Additional constraints (UNIQUE, CHECK, etc.)
    """

    table_name: str = Field(
        ...,
        description="Name of the table",
        min_length=1,
        examples=["users", "authentication_tokens"],
    )

    description: str = Field(
        ...,
        description="Purpose of this table",
        min_length=10,
        examples=["Stores user account information including credentials"],
    )

    columns: list[dict[str, Any]] = Field(
        ...,
        description="List of column specifications",
        min_length=1,
        examples=[
            [
                {"name": "user_id", "type": "UUID", "constraints": "PRIMARY KEY"},
                {"name": "email", "type": "VARCHAR(255)", "constraints": "NOT NULL UNIQUE"},
                {"name": "password_hash", "type": "VARCHAR(255)", "constraints": "NOT NULL"},
                {"name": "created_at", "type": "TIMESTAMP", "constraints": "DEFAULT NOW()"},
            ]
        ],
    )

    indexes: list[str] = Field(
        default_factory=list,
        description="List of index specifications",
        examples=[
            [
                "CREATE INDEX idx_users_email ON users(email)",
                "CREATE INDEX idx_users_created_at ON users(created_at)",
            ]
        ],
    )

    relationships: list[dict[str, str]] = Field(
        default_factory=list,
        description="Foreign key relationships",
        examples=[
            [
                {
                    "foreign_key": "user_id",
                    "references_table": "users",
                    "references_column": "user_id",
                    "on_delete": "CASCADE",
                }
            ]
        ],
    )

    constraints: list[str] = Field(
        default_factory=list,
        description="Additional constraints",
        examples=[
            [
                "CHECK (LENGTH(email) >= 5)",
                "CHECK (created_at <= NOW())",
            ]
        ],
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "table_name": "users",
                "description": "Stores user account information",
                "columns": [
                    {"name": "user_id", "type": "UUID", "constraints": "PRIMARY KEY"},
                    {"name": "email", "type": "VARCHAR(255)", "constraints": "NOT NULL UNIQUE"},
                ],
                "indexes": ["CREATE INDEX idx_users_email ON users(email)"],
                "relationships": [],
                "constraints": ["CHECK (LENGTH(email) >= 5)"],
            }
        }
    }


class ComponentLogic(BaseModel):
    """
    Component/module specification.

    Defines a single software component (class, module, service) with its
    responsibilities, interfaces, and implementation guidance.

    Attributes:
        component_name: Name of the component
        semantic_unit_id: Links to Planning Agent semantic unit
        responsibility: What this component does
        interfaces: Public methods/functions
        dependencies: Other components this depends on
        implementation_notes: Detailed implementation guidance
        complexity: Estimated complexity (from Planning Agent)
    """

    component_name: str = Field(
        ...,
        description="Name of the component",
        min_length=1,
        examples=["UserAuthenticationService", "PasswordHasher"],
    )

    semantic_unit_id: str = Field(
        ...,
        description="Links to Planning Agent semantic unit (e.g., SU-001)",
        pattern="^SU-[0-9]{3}$",
        examples=["SU-001", "SU-042"],
    )

    responsibility: str = Field(
        ...,
        description="What this component does (single responsibility)",
        min_length=10,
        examples=[
            "Handles user authentication including password verification and JWT token generation"
        ],
    )

    interfaces: list[dict[str, Any]] = Field(
        ...,
        description="Public methods/functions",
        min_length=1,
        examples=[
            [
                {
                    "method": "register_user",
                    "parameters": {"email": "str", "password": "str"},
                    "returns": "User",
                    "description": "Register new user with hashed password",
                },
                {
                    "method": "authenticate",
                    "parameters": {"email": "str", "password": "str"},
                    "returns": "Optional[str]",
                    "description": "Authenticate user and return JWT token",
                },
            ]
        ],
    )

    dependencies: list[str] = Field(
        default_factory=list,
        description="Other components this depends on",
        examples=[["DatabaseService", "PasswordHasher", "TokenGenerator"]],
    )

    implementation_notes: str = Field(
        ...,
        description="Detailed implementation guidance",
        min_length=20,
        examples=[
            "Use bcrypt for password hashing with cost factor 12. "
            "Generate JWT tokens with 1-hour expiration. "
            "Validate email format before registration. "
            "Rate limit authentication attempts (5 per minute per IP)."
        ],
    )

    complexity: Optional[int] = Field(
        default=None,
        description="Estimated complexity from Planning Agent",
        ge=1,
        le=1000,
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "component_name": "UserAuthenticationService",
                "semantic_unit_id": "SU-001",
                "responsibility": "Handles user authentication and JWT token generation",
                "interfaces": [
                    {
                        "method": "register_user",
                        "parameters": {"email": "str", "password": "str"},
                        "returns": "User",
                    }
                ],
                "dependencies": ["DatabaseService", "PasswordHasher"],
                "implementation_notes": "Use bcrypt with cost factor 12",
                "complexity": 45,
            }
        }
    }


class DesignReviewChecklistItem(BaseModel):
    """
    Individual design review checklist item.

    Defines a validation criterion for the Design Review Agent (FR-3) to check.

    Attributes:
        category: Category of the check (Architecture, Security, Performance, etc.)
        description: What to check
        validation_criteria: How to validate (specific criteria)
        severity: How critical this check is (Critical, High, Medium, Low)
    """

    category: str = Field(
        ...,
        description="Category of the check",
        examples=["Architecture", "Security", "Performance", "Data Integrity"],
    )

    description: str = Field(
        ...,
        description="What to check",
        min_length=10,
        examples=["Verify all API endpoints have proper error handling"],
    )

    validation_criteria: str = Field(
        ...,
        description="How to validate (specific criteria)",
        min_length=10,
        examples=[
            "Every APIContract must have at least 3 error_responses defined: "
            "400 (invalid input), 401 (unauthorized), 500 (server error)"
        ],
    )

    severity: str = Field(
        default="Medium",
        description="How critical this check is",
        pattern="^(Critical|High|Medium|Low)$",
        examples=["Critical", "High"],
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "category": "Security",
                "description": "Verify password fields are hashed, never stored in plaintext",
                "validation_criteria": "DataSchema for users table must use 'password_hash' not 'password'",
                "severity": "Critical",
            }
        }
    }


# =============================================================================
# Output Model - Complete Design Specification
# =============================================================================


class DesignSpecification(BaseModel):
    """
    Complete design output from Design Agent.

    This is the primary output of the Design Agent (FR-2), containing all
    information needed for the Coding Agent to implement the system.

    Attributes:
        task_id: Unique task identifier (matches input)
        api_contracts: List of API endpoint specifications
        data_schemas: List of database table specifications
        component_logic: List of component/module specifications
        design_review_checklist: List of validation criteria for Design Review Agent
        architecture_overview: High-level architecture description
        technology_stack: Technology choices (language, frameworks, databases)
        assumptions: Design assumptions and constraints
        timestamp: When this design was created
    """

    task_id: str = Field(
        ...,
        description="Unique task identifier",
        min_length=3,
        max_length=100,
    )

    api_contracts: list[APIContract] = Field(
        default_factory=list,
        description="List of API endpoint specifications",
    )

    data_schemas: list[DataSchema] = Field(
        default_factory=list,
        description="List of database table specifications",
    )

    component_logic: list[ComponentLogic] = Field(
        ...,
        description="List of component/module specifications",
        min_length=1,
    )

    design_review_checklist: list[DesignReviewChecklistItem] = Field(
        ...,
        description="Validation criteria for Design Review Agent",
        min_length=5,  # At least 5 checklist items required
    )

    architecture_overview: str = Field(
        ...,
        description="High-level architecture description",
        min_length=50,
        examples=[
            "This system uses a 3-tier architecture with FastAPI REST API layer, "
            "business logic service layer, and PostgreSQL data layer. "
            "Redis is used for caching and rate limiting. "
            "JWT tokens are used for stateless authentication."
        ],
    )

    technology_stack: dict[str, str] = Field(
        ...,
        description="Technology choices",
        examples=[
            {
                "language": "Python 3.12",
                "web_framework": "FastAPI 0.104",
                "database": "PostgreSQL 15",
                "cache": "Redis 7",
                "authentication": "JWT (PyJWT library)",
            }
        ],
    )

    assumptions: list[str] = Field(
        default_factory=list,
        description="Design assumptions and constraints",
        examples=[
            [
                "Email addresses are unique user identifiers",
                "Password complexity is enforced client-side",
                "System scales to 10,000 concurrent users",
            ]
        ],
    )

    timestamp: datetime = Field(
        default_factory=datetime.now,
        description="When this design was created",
    )

    @field_validator("component_logic")
    @classmethod
    def validate_component_logic(cls, v: list[ComponentLogic]) -> list[ComponentLogic]:
        """Validate component logic list."""
        if not v or len(v) < 1:
            raise ValueError("At least one component is required")

        # Validate semantic_unit_id uniqueness
        semantic_unit_ids = [component.semantic_unit_id for component in v]
        if len(semantic_unit_ids) != len(set(semantic_unit_ids)):
            raise ValueError("Duplicate semantic_unit_id found in component_logic")

        return v

    @field_validator("design_review_checklist")
    @classmethod
    def validate_checklist(cls, v: list[DesignReviewChecklistItem]) -> list[DesignReviewChecklistItem]:
        """Validate design review checklist has minimum required items."""
        if not v or len(v) < 5:
            raise ValueError("Design review checklist must have at least 5 items")

        # Validate at least one Critical or High severity item
        high_priority_items = [item for item in v if item.severity in ("Critical", "High")]
        if len(high_priority_items) < 1:
            raise ValueError("Design review checklist must have at least one Critical or High severity item")

        return v

    model_config = {
        "json_schema_extra": {
            "example": {
                "task_id": "JWT-AUTH-001",
                "api_contracts": [
                    {
                        "endpoint": "/api/v1/auth/register",
                        "method": "POST",
                        "description": "Register new user",
                        "response_schema": {"user_id": "string"},
                    }
                ],
                "data_schemas": [
                    {
                        "table_name": "users",
                        "description": "User accounts",
                        "columns": [{"name": "user_id", "type": "UUID"}],
                    }
                ],
                "component_logic": [
                    {
                        "component_name": "UserAuthService",
                        "semantic_unit_id": "SU-001",
                        "responsibility": "User authentication",
                        "interfaces": [{"method": "register_user"}],
                        "implementation_notes": "Use bcrypt",
                    }
                ],
                "design_review_checklist": [
                    {
                        "category": "Security",
                        "description": "Password hashing",
                        "validation_criteria": "Use bcrypt",
                        "severity": "Critical",
                    },
                    {
                        "category": "Architecture",
                        "description": "Dependency injection",
                        "validation_criteria": "Use constructor injection",
                        "severity": "High",
                    },
                    {
                        "category": "Performance",
                        "description": "Rate limiting",
                        "validation_criteria": "Implement rate limits",
                        "severity": "Medium",
                    },
                    {
                        "category": "Data Integrity",
                        "description": "Email uniqueness",
                        "validation_criteria": "Unique constraint on email",
                        "severity": "High",
                    },
                    {
                        "category": "Error Handling",
                        "description": "API error responses",
                        "validation_criteria": "All endpoints have error schemas",
                        "severity": "Medium",
                    },
                ],
                "architecture_overview": "3-tier architecture with FastAPI, PostgreSQL, and Redis",
                "technology_stack": {
                    "language": "Python 3.12",
                    "framework": "FastAPI",
                },
                "assumptions": ["Email is unique identifier"],
            }
        }
    }
