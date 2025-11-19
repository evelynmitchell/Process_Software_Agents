#!/usr/bin/env python3
"""
Planning Agent Example Script

This script demonstrates how to use the Planning Agent to decompose
a high-level task into semantic units with complexity scoring.

Usage:
    # With environment variables set (ANTHROPIC_API_KEY):
    uv run python examples/planning_agent_example.py

    # With custom task:
    uv run python examples/planning_agent_example.py --task-id "TASK-001" \
        --description "Build user authentication" \
        --requirements "JWT tokens, registration, login endpoints"

Requirements:
    - ANTHROPIC_API_KEY environment variable set
    - Langfuse secrets configured (optional, for telemetry)

Author: ASP Development Team
Date: November 13, 2025
"""

import argparse
import json
import sys
from pathlib import Path

from asp.agents.planning_agent import PlanningAgent
from asp.models.planning import TaskRequirements
from asp.utils.semantic_complexity import get_complexity_band


def print_header(title: str):
    """Print a formatted section header."""
    print()
    print("=" * 80)
    print(f"  {title}")
    print("=" * 80)
    print()


def print_project_plan(plan):
    """Print project plan in a readable format."""
    print_header(f"Project Plan for {plan.task_id}")

    print(f"Project ID: {plan.project_id or 'N/A'}")
    print(f"Agent Version: {plan.agent_version}")
    print(f"Total Semantic Units: {len(plan.semantic_units)}")
    print(f"Total Estimated Complexity: {plan.total_est_complexity}")
    print(f"PROBE-AI Enabled: {plan.probe_ai_enabled}")
    print()

    # Print each semantic unit
    for i, unit in enumerate(plan.semantic_units, 1):
        complexity_band = get_complexity_band(unit.est_complexity)
        print(f"Unit {i}: {unit.unit_id}")
        print(f"  Description: {unit.description}")
        print(f"  Complexity: {unit.est_complexity} ({complexity_band})")
        print(f"  Factors:")
        print(f"    - API Interactions: {unit.api_interactions}")
        print(f"    - Data Transformations: {unit.data_transformations}")
        print(f"    - Logical Branches: {unit.logical_branches}")
        print(f"    - Code Entities Modified: {unit.code_entities_modified}")
        print(f"    - Novelty Multiplier: {unit.novelty_multiplier}x")
        print()


def example_user_authentication():
    """Example 1: User Authentication System."""
    print_header("Example 1: User Authentication System")

    requirements = TaskRequirements(
        task_id="TASK-2025-001",
        project_id="ASP-PLATFORM",
        description="Build user authentication system with JWT tokens",
        requirements="""
        Build a complete user authentication system with the following features:

        1. User Registration:
           - POST /auth/register endpoint
           - Email and password validation
           - Password hashing with bcrypt
           - Store user in PostgreSQL database
           - Return success/error response

        2. User Login:
           - POST /auth/login endpoint
           - Validate credentials against database
           - Generate JWT token with user claims
           - Return token with expiration time

        3. Protected Routes:
           - Authentication middleware for protected endpoints
           - JWT token validation
           - Extract user info from token
           - Handle expired tokens

        4. Error Handling:
           - Validation errors (400)
           - Authentication errors (401)
           - Server errors (500)
           - Detailed error messages

        Tech Stack:
        - Node.js with Express
        - PostgreSQL database
        - JWT for tokens
        - bcrypt for password hashing
        """,
        context_files=None,
    )

    print("Input:")
    print(f"  Task ID: {requirements.task_id}")
    print(f"  Description: {requirements.description}")
    print(f"  Requirements: {len(requirements.requirements.split())} words")
    print()

    # Create agent and execute
    agent = PlanningAgent()
    plan = agent.execute(requirements)

    # Display results
    print_project_plan(plan)

    return plan


def example_data_pipeline():
    """Example 2: Real-time Data Processing Pipeline."""
    print_header("Example 2: Real-time Data Processing Pipeline")

    requirements = TaskRequirements(
        task_id="TASK-2025-002",
        project_id="DATA-PIPELINE",
        description="Build real-time data processing pipeline with anomaly detection",
        requirements="""
        Create a real-time data processing pipeline that:

        1. Data Ingestion:
           - Stream data from Kafka topics
           - Handle multiple data sources (IoT sensors, APIs, logs)
           - Parse different data formats (JSON, Avro, CSV)
           - Rate limiting and backpressure handling

        2. Data Transformation:
           - Clean and normalize incoming data
           - Enrich data with external lookups
           - Aggregate time-series data (1-min, 5-min windows)
           - Convert data formats for downstream systems

        3. Anomaly Detection:
           - Implement custom statistical anomaly detection algorithm
           - Z-score calculation for outlier detection
           - Moving average baseline comparison
           - Alert generation for detected anomalies

        4. Data Storage:
           - Write processed data to TimescaleDB
           - Archive raw data to S3
           - Maintain retention policies
           - Index optimization for queries

        5. Monitoring:
           - Pipeline health metrics
           - Latency tracking
           - Error rate monitoring
           - Grafana dashboards

        Tech Stack:
        - Python with Apache Kafka
        - TimescaleDB for time-series storage
        - AWS S3 for archival
        - Custom ML algorithms (scikit-learn)
        """,
        context_files=None,
    )

    print("Input:")
    print(f"  Task ID: {requirements.task_id}")
    print(f"  Description: {requirements.description}")
    print(f"  Requirements: {len(requirements.requirements.split())} words")
    print()

    # Create agent and execute
    agent = PlanningAgent()
    plan = agent.execute(requirements)

    # Display results
    print_project_plan(plan)

    return plan


def example_custom_task(task_id: str, description: str, requirements: str):
    """Run Planning Agent on custom task."""
    print_header("Custom Task Decomposition")

    task_requirements = TaskRequirements(
        task_id=task_id,
        project_id="CUSTOM",
        description=description,
        requirements=requirements,
        context_files=None,
    )

    print("Input:")
    print(f"  Task ID: {task_requirements.task_id}")
    print(f"  Description: {task_requirements.description}")
    print(f"  Requirements: {len(task_requirements.requirements.split())} words")
    print()

    # Create agent and execute
    agent = PlanningAgent()
    plan = agent.execute(task_requirements)

    # Display results
    print_project_plan(plan)

    return plan


def save_plan_to_file(plan, filename: str):
    """Save project plan to JSON file."""
    output_path = Path(filename)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Convert to dict for JSON serialization
    plan_dict = plan.model_dump(mode="json")

    with open(output_path, "w") as f:
        json.dump(plan_dict, f, indent=2)

    print(f"[OK] Plan saved to: {output_path}")


def main():
    """Run Planning Agent examples."""
    parser = argparse.ArgumentParser(
        description="Planning Agent example script",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--example",
        choices=["auth", "pipeline", "both"],
        default="both",
        help="Which example to run (default: both)",
    )
    parser.add_argument(
        "--task-id",
        type=str,
        help="Custom task ID (for custom task mode)",
    )
    parser.add_argument(
        "--description",
        type=str,
        help="Custom task description (for custom task mode)",
    )
    parser.add_argument(
        "--requirements",
        type=str,
        help="Custom task requirements (for custom task mode)",
    )
    parser.add_argument(
        "--output",
        type=str,
        help="Save plan to JSON file",
    )

    args = parser.parse_args()

    # Banner
    print("=" * 80)
    print("  ASP Platform - Planning Agent Demonstration")
    print("=" * 80)
    print()
    print("This script demonstrates the Planning Agent's ability to decompose")
    print("high-level tasks into semantic units with complexity scoring.")
    print()

    try:
        # Custom task mode
        if args.task_id and args.description and args.requirements:
            plan = example_custom_task(args.task_id, args.description, args.requirements)
            if args.output:
                save_plan_to_file(plan, args.output)
            return 0

        # Example mode
        plans = []

        if args.example in ("auth", "both"):
            plan1 = example_user_authentication()
            plans.append(plan1)

        if args.example in ("pipeline", "both"):
            plan2 = example_data_pipeline()
            plans.append(plan2)

        # Summary
        print_header("Summary")
        print(f"Decomposed {len(plans)} task(s) successfully!")
        print()
        for i, plan in enumerate(plans, 1):
            print(f"Task {i}: {plan.task_id}")
            print(f"  - {len(plan.semantic_units)} semantic units")
            print(f"  - Total complexity: {plan.total_est_complexity}")
        print()

        if args.output and plans:
            save_plan_to_file(plans[0], args.output)

        print("=" * 80)
        print()
        print("Next steps:")
        print("  1. Check Langfuse dashboard for telemetry: https://us.cloud.langfuse.com")
        print("  2. Query SQLite for cost data: uv run python scripts/query_telemetry.py")
        print("  3. Calibrate complexity scores after completing actual tasks")
        print()
        print("=" * 80)

        return 0

    except Exception as e:
        print()
        print("=" * 80)
        print("  ERROR")
        print("=" * 80)
        print()
        print(f"Planning Agent failed: {e}")
        print()
        print("Common issues:")
        print("  - ANTHROPIC_API_KEY not set (check: echo $ANTHROPIC_API_KEY)")
        print("  - Network connectivity issues")
        print("  - Rate limit exceeded")
        print()
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
