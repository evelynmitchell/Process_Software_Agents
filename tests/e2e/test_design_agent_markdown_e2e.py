"""
End-to-End tests for Design Agent Markdown Mode with real Anthropic API

These tests validate the markdown output format introduced in Phase 2 of the
Design Agent markdown migration. They test both Sonnet 4.5 and Haiku 4.5 models
to compare success rates and validate the hypothesis that markdown reduces
JSON escaping issues with Haiku.

Test Categories:
1. Basic markdown generation and parsing
2. Model comparison (Sonnet vs Haiku)
3. Format validation and quality
4. Performance metrics

Run with:
    pytest tests/e2e/test_design_agent_markdown_e2e.py -m e2e -v -s

Requirements:
- ANTHROPIC_API_KEY environment variable must be set
- Will consume API credits (approximately $0.02-0.05 per test)
"""

import os
import pytest
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any

from asp.agents.design_agent import DesignAgent
from asp.models.design import DesignInput, DesignSpecification
from asp.models.planning import (
    ProjectPlan,
    SemanticUnit,
    PROBEAIPrediction,
)
from asp.parsers.design_markdown_parser import DesignMarkdownParser


# Skip all tests if no API key is available
pytestmark = pytest.mark.skipif(
    not os.getenv("ANTHROPIC_API_KEY"),
    reason="ANTHROPIC_API_KEY not set - skipping E2E tests"
)


def create_hello_world_plan() -> ProjectPlan:
    """Create Hello World API project plan (matches markdown format spec example)."""
    return ProjectPlan(
        project_id="TEST-MARKDOWN-E2E",
        task_id="MD-E2E-001",
        semantic_units=[
            SemanticUnit(
                unit_id="SU-001",
                description="Hello World API endpoint handler",
                api_interactions=1,
                data_transformations=1,
                logical_branches=0,
                code_entities_modified=1,
                novelty_multiplier=1.0,
                est_complexity=10,
                dependencies=[],
            ),
        ],
        total_est_complexity=10,
        probe_ai_prediction=PROBEAIPrediction(
            total_est_latency_ms=2000.0,
            total_est_tokens=1500,
            total_est_api_cost=0.01,
            confidence=0.95,
        ),
        probe_ai_enabled=False,
        agent_version="1.0.0",
        timestamp=datetime.now(),
    )


def create_user_registration_plan() -> ProjectPlan:
    """Create user registration API project plan."""
    return ProjectPlan(
        project_id="TEST-MARKDOWN-E2E",
        task_id="MD-E2E-002",
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


def validate_design_specification(design: DesignSpecification, project_plan: ProjectPlan):
    """Comprehensive validation of DesignSpecification object."""
    # Basic structure
    assert isinstance(design, DesignSpecification)
    assert design.task_id == project_plan.task_id

    # Architecture overview
    assert len(design.architecture_overview) >= 50, "Architecture overview too short"

    # Technology stack
    assert len(design.technology_stack) > 0, "Technology stack is empty"
    assert isinstance(design.technology_stack, dict), "Technology stack must be dict"

    # API contracts
    assert len(design.api_contracts) > 0, "No API contracts defined"
    for api in design.api_contracts:
        assert len(api.endpoint) > 0, "API endpoint is empty"
        assert api.method in ["GET", "POST", "PUT", "DELETE", "PATCH"], f"Invalid method: {api.method}"
        assert len(api.description) >= 10, f"API description too short: {api.endpoint}"
        assert api.response_schema is not None, f"Missing response schema: {api.endpoint}"

    # Data schemas
    assert len(design.data_schemas) >= 0, "Data schemas must be list (can be empty)"
    for schema in design.data_schemas:
        assert len(schema.table_name) > 0, "Table name is empty"
        assert len(schema.description) >= 10, f"Schema description too short: {schema.table_name}"
        assert len(schema.columns) > 0, f"No columns defined: {schema.table_name}"
        for col in schema.columns:
            assert "name" in col and len(col["name"]) > 0, f"Column missing name: {schema.table_name}"
            assert "type" in col or "data_type" in col, f"Column missing type: {col.get('name')}"

    # Component logic
    assert len(design.component_logic) >= len(project_plan.semantic_units), \
        "Must have at least one component per semantic unit"

    semantic_unit_ids = {unit.unit_id for unit in project_plan.semantic_units}
    for component in design.component_logic:
        assert len(component.component_name) > 0, "Component name is empty"
        assert len(component.responsibility) >= 20, f"Component responsibility too short: {component.component_name}"
        assert component.semantic_unit_id in semantic_unit_ids, \
            f"Invalid semantic_unit_id: {component.semantic_unit_id}"
        assert len(component.interfaces) > 0, f"No interfaces defined: {component.component_name}"

    # Design review checklist
    assert len(design.design_review_checklist) >= 5, "Must have at least 5 review items"

    valid_categories = ["completeness", "correctness", "performance", "security",
                       "maintainability", "data integrity", "error handling", "architecture"]
    valid_severities = ["critical", "high", "medium", "low"]

    for item in design.design_review_checklist:
        assert item.category.lower() in valid_categories, f"Invalid category: {item.category}"
        assert item.severity.lower() in valid_severities, f"Invalid severity: {item.severity}"
        assert len(item.description) >= 10, f"Review item description too short: {item.description}"
        assert len(item.validation_criteria) >= 10, f"Validation criteria too short: {item.description}"


def print_test_summary(title: str, design: DesignSpecification, metrics: Dict[str, Any]):
    """Print formatted test summary."""
    print(f"\n{'='*80}")
    print(f"{title}")
    print(f"{'='*80}")
    print(f"Task ID: {design.task_id}")
    print(f"\nMetrics:")
    for key, value in metrics.items():
        print(f"  - {key}: {value}")
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
    print(f"{'='*80}\n")


@pytest.mark.e2e
class TestDesignAgentMarkdownBasic:
    """Basic markdown mode functionality tests."""

    def test_hello_world_markdown_sonnet(self):
        """Test Hello World API with markdown mode using Sonnet 4.5."""
        agent = DesignAgent(
            use_markdown=True,
            model="claude-sonnet-4-5-20250929"
        )

        requirements = """
        Build a simple Hello World REST API.

        Requirements:
        - GET /hello endpoint
        - Returns JSON response with message "Hello, World!"
        - Returns 200 status code
        - Use FastAPI framework
        """

        project_plan = create_hello_world_plan()

        design_input = DesignInput(
            task_id="MD-E2E-001",
            requirements=requirements,
            project_plan=project_plan,
            design_constraints="Use FastAPI framework",
        )

        # Execute with markdown mode
        start_time = datetime.now()
        design = agent.execute(design_input)
        execution_time = (datetime.now() - start_time).total_seconds()

        # Validate
        validate_design_specification(design, project_plan)

        # Metrics
        metrics = {
            "model": "claude-sonnet-4-5",
            "mode": "markdown",
            "execution_time_sec": round(execution_time, 2),
            "api_contracts": len(design.api_contracts),
            "data_schemas": len(design.data_schemas),
            "components": len(design.component_logic),
            "review_items": len(design.design_review_checklist),
        }

        print_test_summary("Hello World API - Sonnet 4.5 Markdown", design, metrics)

        assert design.task_id == "MD-E2E-001"
        assert len(design.api_contracts) >= 1
        assert any("hello" in api.endpoint.lower() for api in design.api_contracts)

    def test_user_registration_markdown_sonnet(self):
        """Test user registration API with markdown mode using Sonnet 4.5."""
        agent = DesignAgent(
            use_markdown=True,
            model="claude-sonnet-4-5-20250929"
        )

        requirements = """
        Build a user registration API endpoint.

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

        project_plan = create_user_registration_plan()

        design_input = DesignInput(
            task_id="MD-E2E-002",
            requirements=requirements,
            project_plan=project_plan,
            design_constraints="Use FastAPI framework, PostgreSQL database, bcrypt for password hashing",
        )

        # Execute with markdown mode
        start_time = datetime.now()
        design = agent.execute(design_input)
        execution_time = (datetime.now() - start_time).total_seconds()

        # Validate
        validate_design_specification(design, project_plan)

        # Metrics
        metrics = {
            "model": "claude-sonnet-4-5",
            "mode": "markdown",
            "execution_time_sec": round(execution_time, 2),
            "api_contracts": len(design.api_contracts),
            "data_schemas": len(design.data_schemas),
            "components": len(design.component_logic),
            "review_items": len(design.design_review_checklist),
        }

        print_test_summary("User Registration API - Sonnet 4.5 Markdown", design, metrics)

        # Validate semantic unit coverage
        semantic_unit_ids = {unit.unit_id for unit in project_plan.semantic_units}
        design_unit_ids = {comp.semantic_unit_id for comp in design.component_logic}
        assert semantic_unit_ids == design_unit_ids, "All semantic units must have components"

        # Check for security items
        has_security = any(item.category.lower() == "security" for item in design.design_review_checklist)
        assert has_security, "Should have security review items for auth endpoint"


@pytest.mark.e2e
class TestDesignAgentMarkdownHaiku:
    """Test markdown mode with Haiku 4.5 model."""

    def test_hello_world_markdown_haiku(self):
        """Test Hello World API with markdown mode using Haiku 4.5."""
        agent = DesignAgent(
            use_markdown=True,
            model="claude-haiku-4-5"
        )

        requirements = """
        Build a simple Hello World REST API.

        Requirements:
        - GET /hello endpoint
        - Returns JSON response with message "Hello, World!"
        - Returns 200 status code
        - Use FastAPI framework
        """

        project_plan = create_hello_world_plan()

        design_input = DesignInput(
            task_id="MD-E2E-HAIKU-001",
            requirements=requirements,
            project_plan=project_plan,
            design_constraints="Use FastAPI framework",
        )

        # Execute with markdown mode
        start_time = datetime.now()
        design = agent.execute(design_input)
        execution_time = (datetime.now() - start_time).total_seconds()

        # Validate
        validate_design_specification(design, project_plan)

        # Metrics
        metrics = {
            "model": "claude-haiku-4-5",
            "mode": "markdown",
            "execution_time_sec": round(execution_time, 2),
            "api_contracts": len(design.api_contracts),
            "data_schemas": len(design.data_schemas),
            "components": len(design.component_logic),
            "review_items": len(design.design_review_checklist),
        }

        print_test_summary("Hello World API - Haiku 4.5 Markdown", design, metrics)

    def test_user_registration_markdown_haiku(self):
        """Test user registration API with markdown mode using Haiku 4.5."""
        agent = DesignAgent(
            use_markdown=True,
            model="claude-haiku-4-5"
        )

        requirements = """
        Build a user registration API endpoint.

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

        project_plan = create_user_registration_plan()

        design_input = DesignInput(
            task_id="MD-E2E-HAIKU-002",
            requirements=requirements,
            project_plan=project_plan,
            design_constraints="Use FastAPI framework, PostgreSQL database, bcrypt for password hashing",
        )

        # Execute with markdown mode
        start_time = datetime.now()
        design = agent.execute(design_input)
        execution_time = (datetime.now() - start_time).total_seconds()

        # Validate
        validate_design_specification(design, project_plan)

        # Metrics
        metrics = {
            "model": "claude-haiku-4-5",
            "mode": "markdown",
            "execution_time_sec": round(execution_time, 2),
            "api_contracts": len(design.api_contracts),
            "data_schemas": len(design.data_schemas),
            "components": len(design.component_logic),
            "review_items": len(design.design_review_checklist),
        }

        print_test_summary("User Registration API - Haiku 4.5 Markdown", design, metrics)


@pytest.mark.e2e
class TestDesignAgentMarkdownComparison:
    """Compare markdown vs JSON modes."""

    def test_json_vs_markdown_sonnet(self):
        """Compare JSON and markdown modes with Sonnet 4.5."""
        requirements = """
        Build a simple Hello World REST API.

        Requirements:
        - GET /hello endpoint
        - Returns JSON response with message "Hello, World!"
        - Returns 200 status code
        - Use FastAPI framework
        """

        project_plan = create_hello_world_plan()

        # Test JSON mode
        print("\n" + "="*80)
        print("Testing JSON Mode (Sonnet 4.5)")
        print("="*80)

        agent_json = DesignAgent(
            use_markdown=False,
            model="claude-sonnet-4-5-20250929"
        )

        design_input_json = DesignInput(
            task_id="MD-E2E-JSON-001",
            requirements=requirements,
            project_plan=project_plan,
            design_constraints="Use FastAPI framework",
        )

        start_json = datetime.now()
        design_json = agent_json.execute(design_input_json)
        time_json = (datetime.now() - start_json).total_seconds()

        # Test Markdown mode
        print("\n" + "="*80)
        print("Testing Markdown Mode (Sonnet 4.5)")
        print("="*80)

        agent_md = DesignAgent(
            use_markdown=True,
            model="claude-sonnet-4-5-20250929"
        )

        design_input_md = DesignInput(
            task_id="MD-E2E-MD-001",
            requirements=requirements,
            project_plan=project_plan,
            design_constraints="Use FastAPI framework",
        )

        start_md = datetime.now()
        design_md = agent_md.execute(design_input_md)
        time_md = (datetime.now() - start_md).total_seconds()

        # Validate both
        validate_design_specification(design_json, project_plan)
        validate_design_specification(design_md, project_plan)

        # Compare
        print("\n" + "="*80)
        print("Comparison: JSON vs Markdown (Sonnet 4.5)")
        print("="*80)
        print(f"\nExecution Time:")
        print(f"  JSON:     {time_json:.2f}s")
        print(f"  Markdown: {time_md:.2f}s")
        print(f"  Delta:    {abs(time_json - time_md):.2f}s ({'+' if time_md > time_json else '-'}{abs(1 - time_md/time_json)*100:.1f}%)")

        print(f"\nAPI Contracts:")
        print(f"  JSON:     {len(design_json.api_contracts)}")
        print(f"  Markdown: {len(design_md.api_contracts)}")

        print(f"\nComponents:")
        print(f"  JSON:     {len(design_json.component_logic)}")
        print(f"  Markdown: {len(design_md.component_logic)}")

        print(f"\nReview Items:")
        print(f"  JSON:     {len(design_json.design_review_checklist)}")
        print(f"  Markdown: {len(design_md.design_review_checklist)}")
        print("="*80 + "\n")

    def test_json_vs_markdown_haiku(self):
        """Compare JSON and markdown modes with Haiku 4.5."""
        requirements = """
        Build a simple Hello World REST API.

        Requirements:
        - GET /hello endpoint
        - Returns JSON response with message "Hello, World!"
        - Returns 200 status code
        - Use FastAPI framework
        """

        project_plan = create_hello_world_plan()

        # Test JSON mode
        print("\n" + "="*80)
        print("Testing JSON Mode (Haiku 4.5)")
        print("="*80)

        agent_json = DesignAgent(
            use_markdown=False,
            model="claude-haiku-4-5"
        )

        design_input_json = DesignInput(
            task_id="MD-E2E-JSON-HAIKU-001",
            requirements=requirements,
            project_plan=project_plan,
            design_constraints="Use FastAPI framework",
        )

        start_json = datetime.now()
        design_json = agent_json.execute(design_input_json)
        time_json = (datetime.now() - start_json).total_seconds()

        # Test Markdown mode
        print("\n" + "="*80)
        print("Testing Markdown Mode (Haiku 4.5)")
        print("="*80)

        agent_md = DesignAgent(
            use_markdown=True,
            model="claude-haiku-4-5"
        )

        design_input_md = DesignInput(
            task_id="MD-E2E-MD-HAIKU-001",
            requirements=requirements,
            project_plan=project_plan,
            design_constraints="Use FastAPI framework",
        )

        start_md = datetime.now()
        design_md = agent_md.execute(design_input_md)
        time_md = (datetime.now() - start_md).total_seconds()

        # Validate both
        validate_design_specification(design_json, project_plan)
        validate_design_specification(design_md, project_plan)

        # Compare
        print("\n" + "="*80)
        print("Comparison: JSON vs Markdown (Haiku 4.5)")
        print("="*80)
        print(f"\nExecution Time:")
        print(f"  JSON:     {time_json:.2f}s")
        print(f"  Markdown: {time_md:.2f}s")
        print(f"  Delta:    {abs(time_json - time_md):.2f}s ({'+' if time_md > time_json else '-'}{abs(1 - time_md/time_json)*100:.1f}%)")

        print(f"\nAPI Contracts:")
        print(f"  JSON:     {len(design_json.api_contracts)}")
        print(f"  Markdown: {len(design_md.api_contracts)}")

        print(f"\nComponents:")
        print(f"  JSON:     {len(design_json.component_logic)}")
        print(f"  Markdown: {len(design_md.component_logic)}")

        print(f"\nReview Items:")
        print(f"  JSON:     {len(design_json.design_review_checklist)}")
        print(f"  Markdown: {len(design_md.design_review_checklist)}")
        print("="*80 + "\n")


@pytest.mark.e2e
class TestDesignAgentMarkdownParsing:
    """Test markdown parsing and format validation."""

    def test_raw_markdown_parsing(self):
        """Test that raw markdown output can be parsed correctly."""
        agent = DesignAgent(
            use_markdown=True,
            model="claude-sonnet-4-5-20250929"
        )

        requirements = "Build a simple Hello World REST API with GET /hello endpoint"
        project_plan = create_hello_world_plan()

        design_input = DesignInput(
            task_id="MD-E2E-PARSE-001",
            requirements=requirements,
            project_plan=project_plan,
            design_constraints="Use FastAPI framework",
        )

        # Execute
        design = agent.execute(design_input)

        # Test that we can serialize back to dict and validate structure
        design_dict = design.model_dump()

        assert "task_id" in design_dict
        assert "architecture_overview" in design_dict
        assert "technology_stack" in design_dict
        assert "api_contracts" in design_dict
        assert "data_schemas" in design_dict
        assert "component_logic" in design_dict
        assert "design_review_checklist" in design_dict

        print(f"\n{'='*80}")
        print(f"Markdown Parsing Validation")
        print(f"{'='*80}")
        print(f"Successfully parsed and validated markdown output")
        print(f"Design dict keys: {list(design_dict.keys())}")
        print(f"{'='*80}\n")


if __name__ == "__main__":
    """Run markdown E2E tests manually."""
    pytest.main([__file__, "-v", "-s", "-m", "e2e"])
