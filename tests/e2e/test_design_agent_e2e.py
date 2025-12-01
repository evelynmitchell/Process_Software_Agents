"""
End-to-End tests for Design Agent with real or mocked Anthropic API

These tests validate the complete workflow with either:
- Real Anthropic API if ANTHROPIC_API_KEY is set
- Mock LLM client if API key is not available

Tests are marked with @pytest.mark.e2e and can be run with:
    pytest tests/e2e/test_design_agent_e2e.py -m e2e
"""

import os
import pytest
from pathlib import Path
from datetime import datetime

from asp.agents.design_agent import DesignAgent
from asp.agents.planning_agent import PlanningAgent
from asp.models.design import DesignInput, DesignSpecification
from asp.models.planning import (
    ProjectPlan,
    SemanticUnit,
    PROBEAIPrediction,
    TaskRequirements,
)


def create_simple_project_plan(task_id: str) -> ProjectPlan:
    """Helper to create a simple project plan for testing."""
    return ProjectPlan(
        project_id="TEST-E2E",
        task_id=task_id,
        semantic_units=[
            SemanticUnit(
                unit_id="SU-001",
                description="User registration API endpoint with email/password validation",
                api_interactions=1,
                data_transformations=2,
                logical_branches=3,
                code_entities_modified=2,
                novelty_multiplier=1.0,
                est_complexity=25,
                dependencies=[],
            ),
            SemanticUnit(
                unit_id="SU-002",
                description="Password hashing service using bcrypt",
                api_interactions=0,
                data_transformations=1,
                logical_branches=2,
                code_entities_modified=1,
                novelty_multiplier=1.0,
                est_complexity=20,
                dependencies=[],
            ),
        ],
        total_est_complexity=45,
        probe_ai_prediction=PROBEAIPrediction(
            total_est_latency_ms=5000.0,
            total_est_tokens=3000,
            total_est_api_cost=0.02,
            confidence=0.85,
        ),
        probe_ai_enabled=False,
        agent_version="1.0.0",
        timestamp=datetime.now(),
    )


@pytest.mark.e2e
class TestDesignAgentE2E:
    """End-to-end tests with real API calls."""

    def test_simple_api_design(self, llm_client):
        """Test design generation for a simple REST API."""
        agent = DesignAgent(llm_client=llm_client)

        requirements = """
        Build a simple user registration API endpoint.

        Requirements:
        - POST /users/register endpoint
        - Accept email and password in request body
        - Validate email format and password strength
        - Hash password using bcrypt
        - Store user in PostgreSQL database
        - Return 201 with user ID on success
        - Return 400 for validation errors
        - Return 409 if email already exists
        """

        project_plan = create_simple_project_plan("E2E-DESIGN-001")

        design_input = DesignInput(
            task_id="E2E-DESIGN-001",
            requirements=requirements,
            project_plan=project_plan,
            design_constraints="Use FastAPI framework, PostgreSQL database, bcrypt for password hashing",
        )

        # Execute with real API call
        design = agent.execute(design_input)

        # Validate response structure
        assert isinstance(design, DesignSpecification)
        assert design.task_id == "E2E-DESIGN-001"
        assert len(design.architecture_overview) >= 50
        assert len(design.technology_stack) > 0
        assert len(design.api_contracts) > 0
        assert len(design.data_schemas) > 0
        assert len(design.component_logic) >= 2  # At least 2 semantic units
        assert len(design.design_review_checklist) >= 5

        # Validate API contracts
        for api in design.api_contracts:
            assert len(api.endpoint) > 0
            assert api.method in ["GET", "POST", "PUT", "DELETE", "PATCH"]
            assert len(api.description) >= 10
            assert api.request_schema is not None or api.method == "GET"
            assert api.response_schema is not None

        # Validate data schemas
        for schema in design.data_schemas:
            assert len(schema.table_name) > 0
            assert len(schema.description) >= 10
            assert len(schema.columns) > 0
            for col in schema.columns:
                assert "name" in col and len(col["name"]) > 0
                assert "type" in col or "data_type" in col

        # Validate component logic
        semantic_unit_ids = {unit.unit_id for unit in project_plan.semantic_units}
        for component in design.component_logic:
            assert len(component.component_name) > 0
            assert len(component.responsibility) >= 20
            assert component.semantic_unit_id in semantic_unit_ids
            assert len(component.interfaces) > 0

        # Validate design review checklist
        valid_categories = [
            "completeness",
            "correctness",
            "performance",
            "security",
            "maintainability",
            "data integrity",
            "error handling",
            "architecture",
        ]
        valid_severities = ["critical", "high", "medium", "low"]
        for item in design.design_review_checklist:
            assert (
                item.category.lower() in valid_categories
            ), f"Invalid category: {item.category}"
            assert (
                item.severity.lower() in valid_severities
            ), f"Invalid severity: {item.severity}"
            assert len(item.description) >= 10
            assert len(item.validation_criteria) >= 10

        # Log results
        print(f"\n{'='*80}")
        print(f"E2E Test: Simple API Design")
        print(f"{'='*80}")
        print(f"Task ID: {design.task_id}")
        print(f"\nArchitecture: {design.architecture_overview[:100]}...")
        print(f"\nTechnology Stack:")
        for key, value in design.technology_stack.items():
            print(f"  - {key}: {value}")
        print(f"\nAPI Contracts: {len(design.api_contracts)}")
        for i, api in enumerate(design.api_contracts, 1):
            print(f"  {i}. {api.method} {api.endpoint}")
        print(f"\nData Schemas: {len(design.data_schemas)}")
        for i, schema in enumerate(design.data_schemas, 1):
            print(f"  {i}. {schema.table_name} ({len(schema.columns)} columns)")
        print(f"\nComponents: {len(design.component_logic)}")
        for i, component in enumerate(design.component_logic, 1):
            print(f"  {i}. {component.component_name} [{component.semantic_unit_id}]")
        print(f"\nDesign Review Checklist: {len(design.design_review_checklist)} items")

    def test_authentication_system_design(self, llm_client):
        """Test design generation for JWT authentication system."""
        agent = DesignAgent(llm_client=llm_client)

        requirements = """
        Build a JWT authentication system with user registration and login capabilities.

        Requirements:
        - Users can register with email and password
        - Users can login with email and password to receive JWT token
        - Passwords must be securely hashed using bcrypt
        - JWT tokens expire after 1 hour
        - Include refresh token mechanism (7 day expiry)
        - Rate limiting to prevent brute force attacks
        - Store user data in PostgreSQL database
        - Use FastAPI for the REST API
        - Include password reset functionality
        """

        project_plan = ProjectPlan(
            project_id="TEST-E2E",
            task_id="E2E-DESIGN-002",
            semantic_units=[
                SemanticUnit(
                    unit_id="SU-001",
                    description="User registration API endpoint with email/password",
                    api_interactions=1,
                    data_transformations=2,
                    logical_branches=3,
                    code_entities_modified=2,
                    novelty_multiplier=1.0,
                    est_complexity=25,
                    dependencies=[],
                ),
                SemanticUnit(
                    unit_id="SU-002",
                    description="User login API endpoint with JWT token generation",
                    api_interactions=1,
                    data_transformations=2,
                    logical_branches=4,
                    code_entities_modified=2,
                    novelty_multiplier=1.0,
                    est_complexity=30,
                    dependencies=["SU-001"],
                ),
                SemanticUnit(
                    unit_id="SU-003",
                    description="Password hashing service using bcrypt",
                    api_interactions=0,
                    data_transformations=1,
                    logical_branches=2,
                    code_entities_modified=1,
                    novelty_multiplier=1.0,
                    est_complexity=20,
                    dependencies=[],
                ),
                SemanticUnit(
                    unit_id="SU-004",
                    description="JWT token generation and validation service",
                    api_interactions=0,
                    data_transformations=2,
                    logical_branches=3,
                    code_entities_modified=1,
                    novelty_multiplier=1.5,
                    est_complexity=35,
                    dependencies=[],
                ),
                SemanticUnit(
                    unit_id="SU-005",
                    description="Refresh token mechanism with storage and validation",
                    api_interactions=1,
                    data_transformations=2,
                    logical_branches=3,
                    code_entities_modified=2,
                    novelty_multiplier=1.2,
                    est_complexity=30,
                    dependencies=["SU-004"],
                ),
            ],
            total_est_complexity=140,
            probe_ai_prediction=PROBEAIPrediction(
                total_est_latency_ms=10000.0,
                total_est_tokens=5000,
                total_est_api_cost=0.04,
                confidence=0.80,
            ),
            probe_ai_enabled=False,
            agent_version="1.0.0",
            timestamp=datetime.now(),
        )

        design_input = DesignInput(
            task_id="E2E-DESIGN-002",
            requirements=requirements,
            project_plan=project_plan,
            design_constraints="Use FastAPI, PostgreSQL, bcrypt, PyJWT",
        )

        # Execute with real API call
        design = agent.execute(design_input)

        # Validate response
        assert isinstance(design, DesignSpecification)
        assert len(design.api_contracts) >= 3  # Register, login, refresh
        assert len(design.data_schemas) >= 2  # Users, refresh_tokens
        assert len(design.component_logic) >= 5  # All semantic units covered

        # Validate semantic unit coverage
        semantic_unit_ids = {unit.unit_id for unit in project_plan.semantic_units}
        design_unit_ids = {comp.semantic_unit_id for comp in design.component_logic}
        assert (
            semantic_unit_ids == design_unit_ids
        ), "All semantic units must have components"

        # Check for security-related design review items
        has_security_checks = any(
            item.category.lower() == "security"
            for item in design.design_review_checklist
        )
        assert (
            has_security_checks
        ), "Authentication system should have security review items"

        # Log results
        print(f"\n{'='*80}")
        print(f"E2E Test: JWT Authentication System")
        print(f"{'='*80}")
        print(f"API Contracts: {len(design.api_contracts)}")
        for api in design.api_contracts:
            print(f"  - {api.method} {api.endpoint}: {api.description[:50]}...")
        print(f"\nData Schemas: {len(design.data_schemas)}")
        for schema in design.data_schemas:
            print(f"  - {schema.table_name}: {schema.description[:50]}...")
        print(f"\nComponents: {len(design.component_logic)}")
        for component in design.component_logic:
            print(f"  - {component.component_name} [{component.semantic_unit_id}]")
            if component.dependencies:
                print(f"    Depends on: {', '.join(component.dependencies)}")

    def test_planning_to_design_workflow(self, llm_client):
        """Test full Planning->Design workflow with real API calls."""
        requirements_text = """
        Build a RESTful API for a simple blog system with the following features:
        - Users can create, read, update, and delete blog posts
        - Each post has a title, content, author, and publication date
        - Support pagination for listing posts (10 per page)
        - Include basic authentication (API key based)
        - Store data in PostgreSQL
        - Use FastAPI framework
        """

        # Step 1: Run Planning Agent
        print(f"\n{'='*80}")
        print(f"E2E Test: Planning->Design Workflow")
        print(f"{'='*80}")
        print(f"Step 1: Running Planning Agent...")

        planning_agent = PlanningAgent(llm_client=llm_client)
        task_requirements = TaskRequirements(
            project_id="TEST-E2E",
            task_id="E2E-WORKFLOW-001",
            description="RESTful API for blog system with CRUD operations",
            requirements=requirements_text,
        )

        project_plan = planning_agent.execute(task_requirements)
        print(
            f"[OK] Planning complete: {len(project_plan.semantic_units)} units, complexity={project_plan.total_est_complexity}"
        )

        # Step 2: Run Design Agent
        print(f"\nStep 2: Running Design Agent...")

        design_agent = DesignAgent(llm_client=llm_client)
        design_input = DesignInput(
            task_id="E2E-WORKFLOW-001",
            requirements=requirements_text,
            project_plan=project_plan,
            design_constraints="Use FastAPI, PostgreSQL, API key authentication",
        )

        design = design_agent.execute(design_input)
        print(
            f"[OK] Design complete: {len(design.api_contracts)} APIs, {len(design.component_logic)} components"
        )

        # Validate workflow
        assert isinstance(project_plan, ProjectPlan)
        assert isinstance(design, DesignSpecification)
        assert design.task_id == project_plan.task_id

        # Validate semantic unit coverage
        planning_units = {unit.unit_id for unit in project_plan.semantic_units}
        design_units = {comp.semantic_unit_id for comp in design.component_logic}
        assert (
            planning_units == design_units
        ), "Design must cover all planning semantic units"

        # Log results
        print(f"\n{'='*80}")
        print(f"Workflow Summary")
        print(f"{'='*80}")
        print(f"Planning Output:")
        print(f"  - Semantic Units: {len(project_plan.semantic_units)}")
        print(f"  - Total Complexity: {project_plan.total_est_complexity}")
        print(f"\nDesign Output:")
        print(f"  - API Contracts: {len(design.api_contracts)}")
        print(f"  - Data Schemas: {len(design.data_schemas)}")
        print(f"  - Components: {len(design.component_logic)}")
        print(f"  - Review Items: {len(design.design_review_checklist)}")
        print(f"\nSemantic Unit Mapping:")
        for unit in project_plan.semantic_units:
            components = [
                c.component_name
                for c in design.component_logic
                if c.semantic_unit_id == unit.unit_id
            ]
            print(f"  {unit.unit_id}: {len(components)} component(s)")
            for comp in components:
                print(f"    - {comp}")

    def test_data_pipeline_design(self, llm_client):
        """Test design generation for ETL data pipeline."""
        agent = DesignAgent(llm_client=llm_client)

        requirements = """
        Create a data pipeline that extracts user activity logs from CSV files,
        transforms them by aggregating events per user, and loads the aggregated
        data into a PostgreSQL database.

        Requirements:
        - Extract data from CSV files (may be multiple GB)
        - Validate CSV data and handle malformed rows gracefully
        - Aggregate events by user_id (count, first/last event timestamps, event types)
        - Load aggregated data into database using batch operations
        - Use memory-efficient streaming (don't load full file into memory)
        - Implement proper error handling and logging
        - Track pipeline statistics (rows extracted, transformed, loaded, errors)
        """

        project_plan = ProjectPlan(
            project_id="TEST-E2E",
            task_id="E2E-DESIGN-003",
            semantic_units=[
                SemanticUnit(
                    unit_id="SU-001",
                    description="CSV file extraction with error handling and validation",
                    api_interactions=0,
                    data_transformations=1,
                    logical_branches=5,
                    code_entities_modified=2,
                    novelty_multiplier=1.0,
                    est_complexity=30,
                    dependencies=[],
                ),
                SemanticUnit(
                    unit_id="SU-002",
                    description="Data transformation and aggregation logic",
                    api_interactions=0,
                    data_transformations=5,
                    logical_branches=4,
                    code_entities_modified=2,
                    novelty_multiplier=1.0,
                    est_complexity=45,
                    dependencies=["SU-001"],
                ),
                SemanticUnit(
                    unit_id="SU-003",
                    description="Database loader with batch operations",
                    api_interactions=1,
                    data_transformations=2,
                    logical_branches=3,
                    code_entities_modified=1,
                    novelty_multiplier=1.0,
                    est_complexity=35,
                    dependencies=["SU-002"],
                ),
            ],
            total_est_complexity=110,
            probe_ai_prediction=PROBEAIPrediction(
                total_est_latency_ms=9000.0,
                total_est_tokens=4500,
                total_est_api_cost=0.03,
                confidence=0.82,
            ),
            probe_ai_enabled=False,
            agent_version="1.0.0",
            timestamp=datetime.now(),
        )

        design_input = DesignInput(
            task_id="E2E-DESIGN-003",
            requirements=requirements,
            project_plan=project_plan,
            design_constraints="Use Python standard library for CSV, PostgreSQL, iterator pattern for memory efficiency",
        )

        # Execute with real API call
        design = agent.execute(design_input)

        # Validate response
        assert isinstance(design, DesignSpecification)
        assert len(design.component_logic) >= 3  # At least 3 semantic units

        # Check for data schemas
        assert len(design.data_schemas) > 0, "ETL pipeline should have data schemas"

        # Check for performance-related design review items
        has_performance_checks = any(
            item.category.lower() == "performance"
            for item in design.design_review_checklist
        )
        assert (
            has_performance_checks
        ), "Data pipeline should have performance review items"

        # Log results
        print(f"\n{'='*80}")
        print(f"E2E Test: ETL Data Pipeline Design")
        print(f"{'='*80}")
        print(f"Components: {len(design.component_logic)}")
        for component in design.component_logic:
            print(f"  - {component.component_name}")
            print(f"    Responsibility: {component.responsibility[:60]}...")
            if component.dependencies:
                print(f"    Dependencies: {', '.join(component.dependencies)}")

    def test_telemetry_integration(self, llm_client):
        """Test that telemetry is captured during execution."""
        db_path = Path("data/asp_telemetry.db")
        agent = DesignAgent(db_path=db_path)

        requirements = """
        Create a simple health check endpoint that returns the service status.

        Requirements:
        - GET /health endpoint
        - Returns 200 OK with JSON response
        - Response includes status and timestamp
        """

        project_plan = create_simple_project_plan("E2E-TELEMETRY-001")

        design_input = DesignInput(
            task_id="E2E-TELEMETRY-001",
            requirements=requirements,
            project_plan=project_plan,
            design_constraints="Use FastAPI",
        )

        # Execute with telemetry enabled
        design = agent.execute(design_input)

        # Validate basic execution
        assert isinstance(design, DesignSpecification)

        print(f"\n{'='*80}")
        print(f"E2E Test: Telemetry Integration")
        print(f"{'='*80}")
        print(f"Telemetry captured for task: {design_input.task_id}")
        print(f"Database: {db_path}")
        print(f"Check Langfuse dashboard for trace data")
        print(
            f"Run: uv run python scripts/query_telemetry.py --task-id {design_input.task_id}"
        )


if __name__ == "__main__":
    """Run E2E tests manually."""
    pytest.main([__file__, "-v", "-s", "-m", "e2e"])
