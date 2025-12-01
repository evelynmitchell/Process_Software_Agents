"""
Design Agent Example Script

This script demonstrates how to use the Design Agent to generate technical designs
from requirements and project plans.

Usage:
    # Run with built-in example (JWT authentication)
    uv run python examples/design_agent_example.py

    # Run with built-in example (data pipeline)
    uv run python examples/design_agent_example.py --example pipeline

    # Run with full Planning→Design workflow
    uv run python examples/design_agent_example.py --example full-workflow

    # Output as JSON
    uv run python examples/design_agent_example.py --json

Author: ASP Development Team
Date: November 13, 2025
"""

import argparse
import json
import logging
import sys
from datetime import datetime
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from asp.agents.design_agent import DesignAgent
from asp.agents.planning_agent import PlanningAgent
from asp.models.design import DesignInput
from asp.models.planning import (
    ProjectPlan,
    PROBEAIPrediction,
    SemanticUnit,
    TaskRequirements,
)


def setup_logging(level=logging.INFO):
    """Configure logging."""
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def print_design_summary(design, output_json=False):
    """Print design specification summary."""
    if output_json:
        print(json.dumps(design.model_dump(), indent=2, default=str))
        return

    print("\n" + "=" * 80)
    print(f"DESIGN SPECIFICATION: {design.task_id}")
    print("=" * 80)

    print(f"\nArchitecture Overview:")
    print(f"  {design.architecture_overview}")

    print(f"\nTechnology Stack:")
    for key, value in design.technology_stack.items():
        print(f"  - {key}: {value}")

    print(f"\nAPI Contracts: {len(design.api_contracts)}")
    for i, api in enumerate(design.api_contracts, 1):
        print(f"  {i}. {api.method} {api.endpoint}")
        print(f"     {api.description}")
        if api.authentication_required:
            print(f"     [AUTH REQUIRED]")
        if api.rate_limit:
            print(f"     Rate limit: {api.rate_limit}")

    print(f"\nData Schemas: {len(design.data_schemas)}")
    for i, schema in enumerate(design.data_schemas, 1):
        print(f"  {i}. {schema.table_name} ({len(schema.columns)} columns)")
        print(f"     {schema.description}")
        print(
            f"     Indexes: {len(schema.indexes)}, Relationships: {len(schema.relationships)}"
        )

    print(f"\nComponents: {len(design.component_logic)}")
    for i, component in enumerate(design.component_logic, 1):
        print(f"  {i}. {component.component_name} [{component.semantic_unit_id}]")
        print(f"     {component.responsibility}")
        print(
            f"     Interfaces: {len(component.interfaces)}, Dependencies: {len(component.dependencies)}"
        )
        if component.complexity:
            print(f"     Complexity: {component.complexity}")

    print(f"\nDesign Review Checklist: {len(design.design_review_checklist)} items")
    for i, item in enumerate(design.design_review_checklist, 1):
        print(f"  {i}. [{item.category}] {item.severity}")
        print(f"     {item.description}")

    print(f"\nAssumptions: {len(design.assumptions)}")
    for i, assumption in enumerate(design.assumptions, 1):
        print(f"  {i}. {assumption}")

    print(f"\nGenerated at: {design.timestamp}")
    print("=" * 80 + "\n")


def example_jwt_authentication():
    """Example: JWT authentication system."""
    print("\nExample 1: JWT Authentication System")
    print("-" * 80)

    # Create a project plan (normally from Planning Agent)
    project_plan = ProjectPlan(
        task_id="JWT-AUTH-001",
        semantic_units=[
            SemanticUnit(
                semantic_unit_id="SU-001",
                description="User registration API endpoint with email/password",
                api_interactions=1,
                data_transformations=2,
                logical_branches=3,
                code_entities_modified=2,
                novelty_multiplier=1.0,
                complexity=25,
                dependencies=[],
            ),
            SemanticUnit(
                semantic_unit_id="SU-002",
                description="User login API endpoint with JWT token generation",
                api_interactions=1,
                data_transformations=2,
                logical_branches=4,
                code_entities_modified=2,
                novelty_multiplier=1.0,
                complexity=30,
                dependencies=["SU-001"],
            ),
            SemanticUnit(
                semantic_unit_id="SU-003",
                description="Password hashing service using bcrypt",
                api_interactions=0,
                data_transformations=1,
                logical_branches=2,
                code_entities_modified=1,
                novelty_multiplier=1.0,
                complexity=20,
                dependencies=[],
            ),
            SemanticUnit(
                semantic_unit_id="SU-004",
                description="JWT token generation and validation service",
                api_interactions=0,
                data_transformations=2,
                logical_branches=3,
                code_entities_modified=1,
                novelty_multiplier=1.5,
                complexity=35,
                dependencies=[],
            ),
        ],
        total_complexity=110,
        estimated_effort=PROBEAIPrediction(
            latency_ms=8500,
            tokens_in=2800,
            tokens_out=1200,
            api_cost_usd=0.025,
            confidence_interval=0.15,
        ),
        timestamp=datetime.now(),
    )

    requirements = """
    Build a JWT authentication system with user registration and login capabilities.

    Requirements:
    - Users can register with email and password
    - Users can login with email and password to receive JWT token
    - Passwords must be securely hashed using bcrypt
    - JWT tokens expire after 1 hour
    - Include rate limiting to prevent brute force attacks
    - Store user data in PostgreSQL database
    - Use FastAPI for the REST API
    """

    # Create Design Agent input
    design_input = DesignInput(
        task_id="JWT-AUTH-001",
        requirements=requirements,
        project_plan=project_plan,
        design_constraints="Use FastAPI framework, PostgreSQL database, bcrypt for password hashing, PyJWT for tokens",
    )

    return design_input


def example_data_pipeline():
    """Example: Data pipeline with ETL operations."""
    print("\nExample 2: ETL Data Pipeline")
    print("-" * 80)

    # Create a project plan
    project_plan = ProjectPlan(
        task_id="ETL-PIPELINE-001",
        semantic_units=[
            SemanticUnit(
                semantic_unit_id="SU-001",
                description="CSV file extraction with error handling and validation",
                api_interactions=0,
                data_transformations=1,
                logical_branches=5,
                code_entities_modified=2,
                novelty_multiplier=1.0,
                complexity=30,
                dependencies=[],
            ),
            SemanticUnit(
                semantic_unit_id="SU-002",
                description="Data transformation and aggregation logic",
                api_interactions=0,
                data_transformations=5,
                logical_branches=4,
                code_entities_modified=2,
                novelty_multiplier=1.0,
                complexity=45,
                dependencies=["SU-001"],
            ),
            SemanticUnit(
                semantic_unit_id="SU-003",
                description="Database loader with batch operations",
                api_interactions=1,
                data_transformations=2,
                logical_branches=3,
                code_entities_modified=1,
                novelty_multiplier=1.0,
                complexity=35,
                dependencies=["SU-002"],
            ),
            SemanticUnit(
                semantic_unit_id="SU-004",
                description="Database schema for aggregated metrics",
                api_interactions=0,
                data_transformations=0,
                logical_branches=0,
                code_entities_modified=1,
                novelty_multiplier=1.0,
                complexity=20,
                dependencies=[],
            ),
        ],
        total_complexity=130,
        estimated_effort=PROBEAIPrediction(
            latency_ms=10000,
            tokens_in=3500,
            tokens_out=1800,
            api_cost_usd=0.035,
            confidence_interval=0.20,
        ),
        timestamp=datetime.now(),
    )

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

    design_input = DesignInput(
        task_id="ETL-PIPELINE-001",
        requirements=requirements,
        project_plan=project_plan,
        design_constraints="Use Python standard library for CSV parsing, PostgreSQL for storage, iterator pattern for memory efficiency",
    )

    return design_input


def example_full_workflow():
    """Example: Full Planning→Design workflow."""
    print("\nExample 3: Full Planning->Design Workflow")
    print("-" * 80)
    print("This example runs Planning Agent first, then feeds output to Design Agent\n")

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
    print("Step 1: Running Planning Agent...")
    planning_agent = PlanningAgent()

    task_requirements = TaskRequirements(
        task_id="BLOG-API-001",
        description="RESTful API for blog system with CRUD operations",
        requirements=requirements_text,
        context_files=[],
    )

    project_plan = planning_agent.execute(task_requirements)
    print(
        f"[OK] Planning complete: {len(project_plan.semantic_units)} semantic units, complexity={project_plan.total_complexity}"
    )

    # Step 2: Run Design Agent
    print("\nStep 2: Running Design Agent...")
    design_input = DesignInput(
        task_id="BLOG-API-001",
        requirements=requirements_text,
        project_plan=project_plan,
        design_constraints="Use FastAPI, PostgreSQL, API key authentication",
    )

    return design_input


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Design Agent Example")
    parser.add_argument(
        "--example",
        choices=["jwt", "pipeline", "full-workflow"],
        default="jwt",
        help="Which example to run (default: jwt)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output design as JSON",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging",
    )

    args = parser.parse_args()

    # Setup logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    setup_logging(log_level)

    # Select example
    if args.example == "jwt":
        design_input = example_jwt_authentication()
    elif args.example == "pipeline":
        design_input = example_data_pipeline()
    elif args.example == "full-workflow":
        design_input = example_full_workflow()
    else:
        print(f"Unknown example: {args.example}")
        return 1

    # Run Design Agent
    print(f"\nRunning Design Agent for task: {design_input.task_id}")
    print(f"Requirements: {len(design_input.requirements)} characters")
    print(
        f"Project plan: {len(design_input.project_plan.semantic_units)} semantic units\n"
    )

    try:
        design_agent = DesignAgent()
        design_spec = design_agent.execute(design_input)

        print("[OK] Design Agent execution successful!")
        print_design_summary(design_spec, output_json=args.json)

        return 0

    except Exception as e:
        print(f"\n[ERROR] Design Agent execution failed: {e}")
        if args.verbose:
            import traceback

            traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
