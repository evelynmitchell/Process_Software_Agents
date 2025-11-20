"""
Pydantic models for Code Agent (FR-004).

The Code Agent generates complete, production-ready code from design specifications.
This module defines the input/output data structures for code generation.

Author: ASP Development Team
Date: November 17, 2025
"""

from typing import Optional

from pydantic import BaseModel, Field

from asp.models.design import DesignSpecification
from asp.models.design_review import DesignReviewReport


class FileMetadata(BaseModel):
    """
    Metadata for a single file in the code generation manifest.

    Used in Phase 1 of multi-stage code generation to plan the file structure
    before generating actual file contents.
    """

    file_path: str = Field(
        ...,
        min_length=1,
        description="Relative file path (e.g., 'src/api/auth.py', 'tests/test_auth.py')",
    )
    file_type: str = Field(
        ...,
        description=(
            "File type category: 'source', 'test', 'config', 'documentation', "
            "'requirements', 'schema'"
        ),
    )
    semantic_unit_id: Optional[str] = Field(
        default=None,
        description="Semantic unit ID from planning (for traceability)",
    )
    component_id: Optional[str] = Field(
        default=None,
        description="Component ID from design (for traceability)",
    )
    description: str = Field(
        ...,
        min_length=20,
        description="Clear explanation of what this file will implement (1-2 sentences)",
    )
    estimated_lines: int = Field(
        ...,
        gt=0,
        description="Rough estimate of lines of code (50, 100, 200, 500, etc.)",
    )
    dependencies: list[str] = Field(
        default_factory=list,
        description="List of other files this file depends on (imports from)",
    )

    class Config:
        json_schema_extra = {
            "example": {
                "file_path": "src/api/auth.py",
                "file_type": "source",
                "semantic_unit_id": "SU-001",
                "component_id": "COMP-001",
                "description": "JWT authentication API endpoints with login, token generation, and validation",
                "estimated_lines": 250,
                "dependencies": ["src/models/user.py", "src/utils/jwt_utils.py"],
            }
        }


class FileManifest(BaseModel):
    """
    Complete file manifest for code generation.

    Phase 1 output of multi-stage code generation. Contains the list of all files
    that need to be created, along with their metadata. This manifest is then used
    in Phase 2 to generate individual file contents.
    """

    task_id: str = Field(
        ...,
        min_length=3,
        description="Task identifier matching input",
    )
    project_id: Optional[str] = Field(
        default=None,
        min_length=3,
        description="Project identifier (if part of larger project)",
    )
    files: list[FileMetadata] = Field(
        ...,
        min_items=1,
        description="List of all files to be generated with their metadata",
    )
    dependencies: list[str] = Field(
        default_factory=list,
        description=(
            "All external dependencies required (pip packages, npm packages, etc.). "
            "Format: 'package==version' (e.g., 'fastapi==0.104.1')"
        ),
    )
    setup_instructions: str = Field(
        ...,
        min_length=20,
        description=(
            "Step-by-step instructions for setting up and running the generated code "
            "(installation, database setup, environment variables, etc.)"
        ),
    )
    total_files: int = Field(
        ...,
        gt=0,
        description="Total number of files in the manifest",
    )
    total_estimated_lines: int = Field(
        default=0,
        ge=0,
        description="Sum of all estimated_lines values from files",
    )

    class Config:
        json_schema_extra = {
            "example": {
                "task_id": "JWT-AUTH-001",
                "project_id": "PROJECT-2025-001",
                "files": [
                    {
                        "file_path": "src/api/auth.py",
                        "file_type": "source",
                        "semantic_unit_id": "SU-001",
                        "component_id": "COMP-001",
                        "description": "JWT authentication API endpoints",
                        "estimated_lines": 250,
                        "dependencies": ["src/models/user.py"],
                    }
                ],
                "dependencies": ["fastapi==0.104.1", "python-jose==3.3.0"],
                "setup_instructions": "1. pip install -r requirements.txt\n2. Run: uvicorn main:app",
                "total_files": 10,
                "total_estimated_lines": 2500,
            }
        }


class CodeInput(BaseModel):
    """
    Input data for Code Agent.

    Contains the approved design specification and coding standards
    needed to generate production-ready code.
    """

    task_id: str = Field(
        ...,
        min_length=3,
        description="Unique task identifier",
    )
    design_specification: DesignSpecification = Field(
        ...,
        description="Approved design specification from Design Agent",
    )
    design_review_report: Optional[DesignReviewReport] = Field(
        default=None,
        description="Optional design review report with quality feedback",
    )
    coding_standards: Optional[str] = Field(
        default=None,
        description=(
            "Project-specific coding standards and conventions "
            "(e.g., from CLAUDE.md, style guides)"
        ),
    )
    context_files: Optional[list[str]] = Field(
        default=None,
        description=(
            "Additional context files (existing code, architectural docs, "
            "framework-specific patterns)"
        ),
    )

    class Config:
        json_schema_extra = {
            "example": {
                "task_id": "JWT-AUTH-001",
                "design_specification": {
                    "task_id": "JWT-AUTH-001",
                    "architecture_overview": "FastAPI REST API with JWT authentication",
                    # ... (rest of design spec)
                },
                "design_review_report": {
                    "review_status": "PASS",
                    # ... (rest of review report)
                },
                "coding_standards": "Follow PEP 8, use type hints, docstrings required",
                "context_files": ["CLAUDE.md", "docs/api_patterns.md"],
            }
        }


class GeneratedFile(BaseModel):
    """
    Represents a single generated file with metadata.

    Contains the full file content plus metadata for code review and testing.
    """

    file_path: str = Field(
        ...,
        min_length=1,
        description="Relative file path (e.g., 'src/api/auth.py', 'tests/test_auth.py')",
    )
    content: str = Field(
        ...,
        min_length=1,
        description="Complete file content (FULL file, not diff or partial)",
    )
    file_type: str = Field(
        ...,
        description=(
            "File type category: 'source', 'test', 'config', 'documentation', "
            "'requirements', 'schema'"
        ),
    )
    semantic_unit_id: Optional[str] = Field(
        default=None,
        description="Semantic unit ID from planning (for traceability)",
    )
    component_id: Optional[str] = Field(
        default=None,
        description="Component ID from design (for traceability)",
    )
    description: str = Field(
        ...,
        min_length=20,
        description="Brief description of what this file implements",
    )

    class Config:
        json_schema_extra = {
            "example": {
                "file_path": "src/api/auth.py",
                "content": "from fastapi import APIRouter...",
                "file_type": "source",
                "semantic_unit_id": "SU-001",
                "component_id": "COMP-001",
                "description": "JWT authentication API endpoints with token generation and validation",
            }
        }


class GeneratedCode(BaseModel):
    """
    Complete code generation output from Code Agent.

    Contains all generated files, dependencies, and implementation notes
    for a task.
    """

    task_id: str = Field(
        ...,
        min_length=3,
        description="Task identifier matching input",
    )
    project_id: Optional[str] = Field(
        default=None,
        min_length=3,
        description="Project identifier (if part of larger project)",
    )

    # Generated files
    files: list[GeneratedFile] = Field(
        ...,
        min_items=1,
        description="All generated files (source, tests, config, docs)",
    )

    # File structure metadata
    file_structure: dict[str, list[str]] = Field(
        ...,
        description=(
            "Directory structure mapping (directory → list of file names). "
            "Example: {'src/api': ['auth.py', 'users.py'], 'tests': ['test_auth.py']}"
        ),
    )

    # Implementation metadata
    implementation_notes: str = Field(
        ...,
        min_length=50,
        description=(
            "Detailed explanation of implementation approach, key design decisions, "
            "architecture choices, and important patterns used"
        ),
    )
    dependencies: list[str] = Field(
        default_factory=list,
        description=(
            "All external dependencies required (pip packages, npm packages, etc.). "
            "Format: 'package==version' (e.g., 'fastapi==0.104.1')"
        ),
    )
    setup_instructions: Optional[str] = Field(
        default=None,
        description=(
            "Step-by-step instructions for setting up and running the generated code "
            "(installation, database setup, environment variables, etc.)"
        ),
    )

    # Code quality metadata
    total_lines_of_code: int = Field(
        default=0,
        ge=0,
        description="Total lines of code generated (excluding blank lines and comments)",
    )
    total_files: int = Field(
        default=0,
        ge=0,
        description="Total number of files generated",
    )
    test_coverage_target: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=100.0,
        description="Expected test coverage percentage for generated tests",
    )

    # Traceability
    semantic_units_implemented: list[str] = Field(
        default_factory=list,
        description=(
            "List of semantic unit IDs from planning that are implemented "
            "in this code generation"
        ),
    )
    components_implemented: list[str] = Field(
        default_factory=list,
        description=(
            "List of component IDs from design that are implemented "
            "in this code generation"
        ),
    )

    # Agent metadata
    agent_version: str = Field(
        default="1.0.0",
        description="Version of Code Agent that generated this code",
    )
    generation_timestamp: Optional[str] = Field(
        default=None,
        description="ISO 8601 timestamp of code generation",
    )

    class Config:
        json_schema_extra = {
            "example": {
                "task_id": "JWT-AUTH-001",
                "project_id": "PROJECT-2025-001",
                "files": [
                    {
                        "file_path": "src/api/auth.py",
                        "content": "from fastapi import APIRouter...",
                        "file_type": "source",
                        "semantic_unit_id": "SU-001",
                        "component_id": "COMP-001",
                        "description": "JWT authentication API endpoints",
                    }
                ],
                "file_structure": {
                    "src/api": ["auth.py", "users.py"],
                    "src/models": ["user.py"],
                    "tests": ["test_auth.py"],
                },
                "implementation_notes": (
                    "Implemented JWT authentication using python-jose library with "
                    "HS256 algorithm. Password hashing uses bcrypt with cost factor 12. "
                    "Token expiration set to 30 minutes with refresh token support."
                ),
                "dependencies": [
                    "fastapi==0.104.1",
                    "python-jose[cryptography]==3.3.0",
                    "bcrypt==4.1.1",
                    "pydantic==2.5.0",
                ],
                "setup_instructions": (
                    "1. pip install -r requirements.txt\n"
                    "2. Set JWT_SECRET_KEY environment variable\n"
                    "3. Run with: uvicorn main:app --reload"
                ),
                "total_lines_of_code": 450,
                "total_files": 8,
                "test_coverage_target": 90.0,
                "semantic_units_implemented": ["SU-001", "SU-002"],
                "components_implemented": ["COMP-001", "COMP-002", "COMP-003"],
                "agent_version": "1.0.0",
            }
        }
