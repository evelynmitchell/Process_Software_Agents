"""
End-to-End tests for Code Agent with real Anthropic API

These tests make actual API calls to validate the complete workflow.
They are marked with @pytest.mark.e2e and can be run with:
    pytest tests/e2e/test_code_agent_e2e.py -m e2e

Requirements:
- ANTHROPIC_API_KEY environment variable must be set
- Will consume API credits (approximately $0.05-0.10 per test)
"""

import os
import pytest
from pathlib import Path
from datetime import datetime

from asp.agents.code_agent import CodeAgent
from asp.models.code import CodeInput, GeneratedCode
from asp.models.design import (
    APIContract,
    ComponentLogic,
    DataSchema,
    DesignReviewChecklistItem,
    DesignSpecification,
)


# Skip all tests if no API key is available
pytestmark = pytest.mark.skipif(
    not os.getenv("ANTHROPIC_API_KEY"),
    reason="ANTHROPIC_API_KEY not set - skipping E2E tests"
)


def create_simple_design_specification(task_id: str) -> DesignSpecification:
    """Helper to create a simple design specification for testing."""
    return DesignSpecification(
        task_id=task_id,
        architecture_overview=(
            "Simple REST API with JWT authentication and PostgreSQL database. "
            "Uses FastAPI for the web framework with bcrypt for password hashing. "
            "Single-tier architecture with API endpoints directly accessing the database."
        ),
        technology_stack={
            "language": "Python 3.12",
            "framework": "FastAPI 0.104",
            "database": "PostgreSQL 16",
            "authentication": "JWT tokens (python-jose library)",
            "password_hashing": "bcrypt with cost factor 12",
        },
        api_contracts=[
            APIContract(
                endpoint="/api/auth/register",
                method="POST",
                description="Register a new user with email and password credentials",
                request_schema={
                    "email": "string (email format, required)",
                    "password": "string (min 8 chars, required)",
                },
                response_schema={
                    "user_id": "string (UUID)",
                    "email": "string",
                    "created_at": "string (ISO 8601 timestamp)",
                },
                error_responses=[
                    {"status": 400, "code": "INVALID_INPUT", "message": "Invalid email or password format"},
                    {"status": 409, "code": "EMAIL_EXISTS", "message": "Email already registered"},
                ],
                authentication_required=False,
            ),
        ],
        data_schemas=[
            DataSchema(
                table_name="users",
                description="User account information including credentials and timestamps",
                columns=[
                    {"name": "user_id", "type": "UUID", "constraints": "PRIMARY KEY DEFAULT gen_random_uuid()"},
                    {"name": "email", "type": "VARCHAR(255)", "constraints": "UNIQUE NOT NULL"},
                    {"name": "password_hash", "type": "VARCHAR(255)", "constraints": "NOT NULL"},
                    {"name": "created_at", "type": "TIMESTAMP", "constraints": "DEFAULT NOW()"},
                ],
                indexes=[
                    "CREATE INDEX idx_users_email ON users(email)",
                ],
                relationships=[],
            ),
        ],
        component_logic=[
            ComponentLogic(
                component_name="UserRegistrationService",
                semantic_unit_id="SU-001",
                responsibility="Handles user registration including email validation and password hashing",
                interfaces=[
                    {
                        "method": "register_user",
                        "parameters": {"email": "str", "password": "str"},
                        "returns": "User",
                        "description": "Register new user with hashed password",
                    }
                ],
                dependencies=["UserRepository", "PasswordHasher"],
                implementation_notes="Use bcrypt for password hashing with cost factor 12. Validate email format before registration. Check for duplicate emails before inserting into database.",
            ),
        ],
        design_review_checklist=[
            DesignReviewChecklistItem(
                category="Security",
                description="All passwords must be hashed before storage",
                validation_criteria="Verify all user passwords are hashed with bcrypt or stronger algorithm",
                severity="Critical",
            ),
            DesignReviewChecklistItem(
                category="Security",
                description="All API endpoints must have proper error handling",
                validation_criteria="Every APIContract must have at least 2 error_responses defined",
                severity="High",
            ),
            DesignReviewChecklistItem(
                category="Security",
                description="Database queries must use parameterized statements",
                validation_criteria="All SQL queries must use parameterized statements to prevent injection",
                severity="Critical",
            ),
            DesignReviewChecklistItem(
                category="Architecture",
                description="Separation of concerns must be maintained",
                validation_criteria="Components should follow single responsibility principle",
                severity="Medium",
            ),
            DesignReviewChecklistItem(
                category="Performance",
                description="Database indexes must be defined for frequent queries",
                validation_criteria="All foreign keys and frequently queried columns must have indexes",
                severity="Medium",
            ),
        ],
        assumptions=["PostgreSQL 16 available", "Python 3.12+ environment", "FastAPI framework installed"],
        agent_version="1.0.0",
    )


@pytest.mark.e2e
class TestCodeAgentE2E:
    """End-to-end tests with real API calls."""

    def test_simple_api_code_generation(self):
        """Test code generation for a simple user registration API."""
        agent = CodeAgent()

        design_spec = create_simple_design_specification("E2E-CODE-001")

        code_input = CodeInput(
            task_id="E2E-CODE-001",
            design_specification=design_spec,
            coding_standards=(
                "Follow PEP 8 style guide. Use type hints for all functions. "
                "Include docstrings for all modules, classes, and functions. "
                "Write unit tests with pytest. Use async/await for database operations."
            ),
        )

        # Execute with real API call
        print(f"\n\nExecuting Code Agent E2E test for task {code_input.task_id}...")
        print("This will make a real API call and may take 30-60 seconds...\n")

        generated_code = agent.execute(code_input)

        # Validate response structure
        assert isinstance(generated_code, GeneratedCode)
        assert generated_code.task_id == "E2E-CODE-001"
        assert len(generated_code.files) > 0, "Should generate at least one file"
        assert generated_code.total_files == len(generated_code.files)
        assert generated_code.total_lines_of_code > 0
        assert len(generated_code.dependencies) > 0
        assert len(generated_code.implementation_notes) >= 50

        print(f"✅ Code generation successful!")
        print(f"   Generated {generated_code.total_files} files with {generated_code.total_lines_of_code} LOC")
        print(f"   Dependencies: {len(generated_code.dependencies)}")

        # Validate file structure
        assert len(generated_code.file_structure) > 0
        total_files_in_structure = sum(len(files) for files in generated_code.file_structure.values())
        assert total_files_in_structure == generated_code.total_files

        # Validate files
        file_types_found = set()
        for file in generated_code.files:
            # Basic file validations
            assert len(file.file_path) > 0
            assert len(file.content) > 0, f"File {file.file_path} should have non-empty content"
            assert file.file_type in ["source", "test", "config", "documentation", "requirements", "schema"]
            assert len(file.description) >= 20

            file_types_found.add(file.file_type)

        # Should generate at least source files
        assert "source" in file_types_found, "Should generate at least one source file"

        print(f"   File types: {', '.join(sorted(file_types_found))}")

        # Validate dependencies format
        for dep in generated_code.dependencies:
            assert isinstance(dep, str)
            # Most Python deps should have version (e.g., "package==1.2.3")
            # But some might not, so we just check it's a non-empty string
            assert len(dep) > 0

        # Validate semantic units and components
        assert len(generated_code.semantic_units_implemented) > 0
        for su_id in generated_code.semantic_units_implemented:
            assert su_id.startswith("SU-"), f"Semantic unit ID should start with 'SU-': {su_id}"

        assert len(generated_code.components_implemented) > 0

        print(f"   Semantic units: {generated_code.semantic_units_implemented}")
        print(f"   Components: {generated_code.components_implemented}")

        # Validate implementation notes
        assert "bcrypt" in generated_code.implementation_notes.lower() or "password" in generated_code.implementation_notes.lower(), \
            "Implementation notes should mention password hashing approach"

        print(f"\n✅ All validations passed!")

    def test_code_generation_includes_tests(self):
        """Test that code generation includes test files."""
        agent = CodeAgent()

        design_spec = create_simple_design_specification("E2E-CODE-002")

        code_input = CodeInput(
            task_id="E2E-CODE-002",
            design_specification=design_spec,
            coding_standards="Follow PEP 8. Write comprehensive unit tests with pytest. Aim for 80%+ coverage.",
        )

        # Execute
        print(f"\n\nExecuting Code Agent E2E test for task {code_input.task_id}...")
        print("Testing that code generation includes test files...\n")

        generated_code = agent.execute(code_input)

        # Validate that test files are included
        test_files = [f for f in generated_code.files if f.file_type == "test"]
        assert len(test_files) > 0, "Should generate at least one test file"

        print(f"✅ Test files generated: {len(test_files)}")

        for test_file in test_files:
            assert "test" in test_file.file_path.lower(), f"Test file path should contain 'test': {test_file.file_path}"
            assert len(test_file.content) > 50, "Test files should have substantial content"

            # Check for common test frameworks
            content_lower = test_file.content.lower()
            has_test_framework = any([
                "import pytest" in content_lower,
                "import unittest" in content_lower,
                "def test_" in content_lower,
                "class test" in content_lower,
            ])
            assert has_test_framework, f"Test file should use a test framework: {test_file.file_path}"

        print(f"✅ All test files valid!")

    def test_code_generation_with_context(self):
        """Test code generation with additional context files."""
        agent = CodeAgent()

        design_spec = create_simple_design_specification("E2E-CODE-003")

        code_input = CodeInput(
            task_id="E2E-CODE-003",
            design_specification=design_spec,
            coding_standards="Follow project style guide",
            context_files=[
                "Example existing code pattern: Use FastAPI dependency injection for database sessions",
                "Project structure: src/api for endpoints, src/services for business logic, src/models for data models",
            ],
        )

        # Execute
        print(f"\n\nExecuting Code Agent E2E test for task {code_input.task_id}...")
        print("Testing code generation with context files...\n")

        generated_code = agent.execute(code_input)

        # Basic validations
        assert isinstance(generated_code, GeneratedCode)
        assert generated_code.task_id == "E2E-CODE-003"
        assert len(generated_code.files) > 0

        # Check that file structure respects context hints
        file_paths = [f.file_path for f in generated_code.files]
        has_structured_paths = any([
            "src/" in path or "api/" in path or "service" in path.lower() or "model" in path.lower()
            for path in file_paths
        ])
        assert has_structured_paths, "Should organize files in a structured directory layout"

        print(f"✅ Code generation with context successful!")
        print(f"   File paths: {', '.join(file_paths[:5])}...")
