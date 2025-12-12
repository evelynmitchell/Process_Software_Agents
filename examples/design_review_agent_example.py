#!/usr/bin/env python3
"""
Design Review Agent Example Script

This script demonstrates how to use the Design Review Orchestrator to validate
design specifications against quality criteria using 6 specialist review agents.

Usage:
    # With environment variables set (ANTHROPIC_API_KEY):
    uv run python examples/design_review_agent_example.py

    # Run specific example:
    uv run python examples/design_review_agent_example.py --example jwt
    uv run python examples/design_review_agent_example.py --example pipeline
    uv run python examples/design_review_agent_example.py --example full-workflow

    # Save review report to file:
    uv run python examples/design_review_agent_example.py --output review_report.json

Requirements:
    - ANTHROPIC_API_KEY environment variable set
    - Langfuse secrets configured (optional, for telemetry)

Author: ASP Development Team
Date: November 14, 2025
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

from asp.agents.design_agent import DesignAgent
from asp.agents.design_review_orchestrator import DesignReviewOrchestrator
from asp.agents.planning_agent import PlanningAgent
from asp.models.design import (
    APIContract,
    ComponentLogic,
    DataSchema,
    DesignInput,
    DesignReviewChecklistItem,
    DesignSpecification,
)
from asp.models.planning import TaskRequirements


def print_header(title: str):
    """Print a formatted section header."""
    print()
    print("=" * 80)
    print(f"  {title}")
    print("=" * 80)
    print()


def print_review_report(report):
    """Print design review report in a readable format."""
    print_header(f"Design Review Report for {report.task_id}")

    print(f"Overall Assessment: {report.overall_assessment}")
    print(f"Agent Version: {report.agent_version}")
    print()

    # Issue counts
    print("Issue Summary:")
    print(f"  Critical: {report.critical_issue_count}")
    print(f"  High:     {report.high_issue_count}")
    print(f"  Medium:   {report.medium_issue_count}")
    print(f"  Low:      {report.low_issue_count}")
    print()

    # Issues found
    if report.issues_found:
        print(f"Issues Found ({len(report.issues_found)}):")
        for i, issue in enumerate(report.issues_found, 1):
            print(f"\n  {i}. [{issue.severity}] {issue.category}")
            print(f"     {issue.description}")
            print(f"     Evidence: {issue.evidence}")
            print(f"     Impact: {issue.impact}")
    else:
        print("No issues found!")
    print()

    # Improvement suggestions
    if report.improvement_suggestions:
        print(f"Improvement Suggestions ({len(report.improvement_suggestions)}):")
        for i, suggestion in enumerate(report.improvement_suggestions, 1):
            print(f"\n  {i}. [{suggestion.priority}] {suggestion.category}")
            print(f"     {suggestion.description}")
            print(f"     Implementation: {suggestion.implementation_notes[:100]}...")
            if suggestion.related_issue_id:
                print(f"     Related Issue: {suggestion.related_issue_id}")
    else:
        print("No improvement suggestions.")
    print()

    # Checklist review
    if report.checklist_review:
        print(f"Checklist Review ({len(report.checklist_review)} items):")
        passed = sum(1 for item in report.checklist_review if item.status == "Pass")
        print(f"  Passed: {passed}/{len(report.checklist_review)}")
        for i, item in enumerate(report.checklist_review, 1):
            status_icon = (
                "[PASS]"
                if item.status == "Pass"
                else ("[WARN]" if item.status == "Warning" else "[FAIL]")
            )
            print(f"  {status_icon} [{item.category}] {item.status}")
            print(f"    {item.description}")
            if item.status != "Pass":
                print(f"    Notes: {item.notes}")
    print()

    print(f"Review Duration: {report.review_duration_ms:.0f}ms")
    print(f"Reviewed at: {report.timestamp}")
    print()


def create_jwt_auth_design() -> DesignSpecification:
    """Create a sample JWT authentication design specification."""
    return DesignSpecification(
        task_id="JWT-AUTH-001",
        architecture_overview="""
        The JWT authentication system follows a three-tier architecture:
        1. API Layer: FastAPI REST endpoints for registration and login
        2. Service Layer: Authentication, password hashing, and JWT token services
        3. Data Layer: PostgreSQL database for user storage

        Authentication flow:
        - User registers → Password hashed with bcrypt → Stored in database
        - User logs in → Credentials validated → JWT token generated → Returned to client
        - Protected routes → JWT middleware validates token → User info extracted
        """,
        technology_stack={
            "framework": "FastAPI",
            "database": "PostgreSQL",
            "password_hashing": "bcrypt",
            "jwt_library": "PyJWT",
            "orm": "SQLAlchemy",
        },
        api_contracts=[
            APIContract(
                endpoint="/auth/register",
                method="POST",
                description="Register a new user with email and password",
                request_schema={
                    "email": "string",
                    "password": "string",
                    "name": "string",
                },
                response_schema={
                    "user_id": "integer",
                    "email": "string",
                    "created_at": "datetime",
                },
                error_responses=[
                    {
                        "status": 400,
                        "code": "INVALID_INPUT",
                        "message": "Invalid email or password format",
                    },
                    {
                        "status": 409,
                        "code": "USER_EXISTS",
                        "message": "User already exists",
                    },
                    {
                        "status": 500,
                        "code": "INTERNAL_ERROR",
                        "message": "Internal server error",
                    },
                ],
                authentication_required=False,
                rate_limit="5 requests per minute per IP",
            ),
            APIContract(
                endpoint="/auth/login",
                method="POST",
                description="Login with email and password to receive JWT token",
                request_schema={
                    "email": "string",
                    "password": "string",
                },
                response_schema={
                    "token": "string",
                    "expires_at": "datetime",
                    "user_id": "integer",
                },
                error_responses=[
                    {
                        "status": 400,
                        "code": "INVALID_INPUT",
                        "message": "Missing email or password",
                    },
                    {
                        "status": 401,
                        "code": "INVALID_CREDENTIALS",
                        "message": "Invalid email or password",
                    },
                    {
                        "status": 500,
                        "code": "INTERNAL_ERROR",
                        "message": "Internal server error",
                    },
                ],
                authentication_required=False,
                rate_limit="10 requests per minute per IP",
            ),
        ],
        data_schemas=[
            DataSchema(
                table_name="users",
                description="User account information",
                columns=[
                    {
                        "name": "id",
                        "type": "INTEGER",
                        "constraints": "PRIMARY KEY AUTOINCREMENT",
                    },
                    {
                        "name": "email",
                        "type": "VARCHAR(255)",
                        "constraints": "UNIQUE NOT NULL",
                    },
                    {
                        "name": "password_hash",
                        "type": "VARCHAR(255)",
                        "constraints": "NOT NULL",
                    },
                    {"name": "name", "type": "VARCHAR(255)", "constraints": "NOT NULL"},
                    {
                        "name": "created_at",
                        "type": "TIMESTAMP",
                        "constraints": "DEFAULT CURRENT_TIMESTAMP",
                    },
                    {
                        "name": "updated_at",
                        "type": "TIMESTAMP",
                        "constraints": "DEFAULT CURRENT_TIMESTAMP",
                    },
                ],
                indexes=[
                    "CREATE UNIQUE INDEX idx_users_email ON users(email)",
                    "CREATE INDEX idx_users_created_at ON users(created_at)",
                ],
                relationships=[],
            )
        ],
        component_logic=[
            ComponentLogic(
                semantic_unit_id="SU-001",
                component_name="UserRegistrationEndpoint",
                responsibility="Handle user registration requests, validate input, call authentication service",
                interfaces=[
                    {
                        "method": "register",
                        "parameters": {
                            "email": "str",
                            "password": "str",
                            "name": "str",
                        },
                        "returns": "dict",
                        "description": "Register new user with email and password",
                    }
                ],
                dependencies=["AuthenticationService", "UserRepository"],
                implementation_notes="Validate email format using regex. Check password strength (min 8 chars). Call PasswordHashingService to hash password before storing. Return user_id and email on success.",
                complexity=25,
            ),
            ComponentLogic(
                semantic_unit_id="SU-002",
                component_name="UserLoginEndpoint",
                responsibility="Handle login requests, validate credentials, generate JWT token",
                interfaces=[
                    {
                        "method": "login",
                        "parameters": {"email": "str", "password": "str"},
                        "returns": "dict",
                        "description": "Authenticate user and return JWT token",
                    }
                ],
                dependencies=["AuthenticationService", "JWTService", "UserRepository"],
                implementation_notes="Retrieve user by email from database. Use PasswordHashingService to verify password hash. Generate JWT token with user_id claim and 1-hour expiration. Return token and expiration time.",
                complexity=30,
            ),
            ComponentLogic(
                semantic_unit_id="SU-003",
                component_name="PasswordHashingService",
                responsibility="Hash passwords using bcrypt with salt",
                interfaces=[
                    {
                        "method": "hash_password",
                        "parameters": {"password": "str"},
                        "returns": "str",
                        "description": "Hash password with bcrypt",
                    },
                    {
                        "method": "verify_password",
                        "parameters": {"password": "str", "password_hash": "str"},
                        "returns": "bool",
                        "description": "Verify password against hash",
                    },
                ],
                dependencies=["bcrypt"],
                implementation_notes="Use bcrypt.hashpw() with work factor 12 for hashing. Use bcrypt.checkpw() for verification. Always use salted hashes (bcrypt generates salt automatically).",
                complexity=20,
            ),
            ComponentLogic(
                semantic_unit_id="SU-004",
                component_name="JWTService",
                responsibility="Generate and validate JWT tokens with user claims",
                interfaces=[
                    {
                        "method": "generate_token",
                        "parameters": {"user_id": "int"},
                        "returns": "str",
                        "description": "Generate JWT token with user claims",
                    },
                    {
                        "method": "validate_token",
                        "parameters": {"token": "str"},
                        "returns": "dict",
                        "description": "Validate token and extract claims",
                    },
                ],
                dependencies=["PyJWT"],
                implementation_notes="Use HS256 algorithm for signing. Include user_id in payload. Set exp claim to 1 hour from creation. Use secure secret key from environment variable. Handle expired token exceptions.",
                complexity=35,
            ),
        ],
        design_review_checklist=[
            DesignReviewChecklistItem(
                category="Security",
                severity="Critical",
                description="Password storage uses secure hashing (bcrypt/argon2)",
                validation_criteria="PasswordHashingService component must use bcrypt or argon2 with appropriate work factor (bcrypt: 12+, argon2: standard parameters)",
            ),
            DesignReviewChecklistItem(
                category="Security",
                severity="Critical",
                description="JWT tokens use secure signing algorithm (HS256/RS256)",
                validation_criteria="JWTService must use HS256 or RS256 algorithm for token signing. Must not use 'none' algorithm.",
            ),
            DesignReviewChecklistItem(
                category="Performance",
                severity="High",
                description="Database indexes on frequently queried columns (email)",
                validation_criteria="users table must have index on email column since it's used for login lookups",
            ),
            DesignReviewChecklistItem(
                category="API Design",
                severity="Medium",
                description="Rate limiting implemented to prevent brute force attacks",
                validation_criteria="Authentication endpoints must specify rate limits (e.g., '5 requests per minute per IP')",
            ),
            DesignReviewChecklistItem(
                category="DataIntegrity",
                severity="High",
                description="Email uniqueness constraint enforced at database level",
                validation_criteria="users table must have UNIQUE constraint on email column to prevent duplicate accounts",
            ),
        ],
        assumptions=[
            "Users register with email addresses (unique identifier)",
            "JWT tokens expire after 1 hour",
            "Password minimum length: 8 characters",
            "Single PostgreSQL instance (no sharding needed in Phase 1)",
        ],
        dependencies_between_units={
            "SU-002": ["SU-003", "SU-004"],  # Login depends on password hashing and JWT
        },
        timestamp=datetime.now(),
    )


def create_data_pipeline_design() -> DesignSpecification:
    """Create a sample ETL data pipeline design specification."""
    return DesignSpecification(
        task_id="ETL-PIPELINE-001",
        architecture_overview="""
        The ETL pipeline follows a streaming architecture for memory efficiency:
        1. Extraction Layer: CSV file reader with streaming (iterator pattern)
        2. Transformation Layer: User event aggregation with in-memory state
        3. Loading Layer: Batch database loader with transaction management

        Data flow:
        - CSV rows streamed one at a time (no full file load)
        - Events aggregated by user_id in memory (dict structure)
        - Aggregated results batched into database (100 rows per transaction)
        """,
        technology_stack={
            "language": "Python 3.12",
            "csv_parsing": "csv module (standard library)",
            "database": "PostgreSQL",
            "db_driver": "psycopg2",
            "memory_pattern": "Iterator/streaming",
        },
        api_contracts=[],  # No REST API for this pipeline
        data_schemas=[
            DataSchema(
                table_name="user_activity_aggregates",
                description="Aggregated user activity metrics",
                columns=[
                    {
                        "name": "user_id",
                        "type": "INTEGER",
                        "constraints": "PRIMARY KEY",
                    },
                    {
                        "name": "total_events",
                        "type": "INTEGER",
                        "constraints": "NOT NULL",
                    },
                    {
                        "name": "first_event_at",
                        "type": "TIMESTAMP",
                        "constraints": "NOT NULL",
                    },
                    {
                        "name": "last_event_at",
                        "type": "TIMESTAMP",
                        "constraints": "NOT NULL",
                    },
                    {"name": "event_types", "type": "TEXT[]", "constraints": ""},
                    {
                        "name": "processed_at",
                        "type": "TIMESTAMP",
                        "constraints": "DEFAULT CURRENT_TIMESTAMP",
                    },
                ],
                indexes=[
                    "CREATE INDEX idx_activity_last_event ON user_activity_aggregates(last_event_at)",
                    "CREATE INDEX idx_activity_processed ON user_activity_aggregates(processed_at)",
                ],
                relationships=[],
            )
        ],
        component_logic=[
            ComponentLogic(
                semantic_unit_id="SU-001",
                component_name="CSVExtractor",
                responsibility="Stream CSV rows with validation and error handling",
                interfaces=[
                    {
                        "method": "extract_rows",
                        "parameters": {"file_path": "str"},
                        "returns": "Iterator[dict]",
                        "description": "Stream CSV rows one at a time",
                    }
                ],
                dependencies=["csv module"],
                implementation_notes="Use csv.DictReader for streaming. Validate each row has required columns (user_id, event_type, timestamp). Skip malformed rows and log errors. Track total rows processed and errors encountered.",
                complexity=30,
            ),
            ComponentLogic(
                semantic_unit_id="SU-002",
                component_name="EventAggregator",
                responsibility="Aggregate events by user_id with time window tracking",
                interfaces=[
                    {
                        "method": "aggregate",
                        "parameters": {"rows": "Iterator[dict]"},
                        "returns": "dict",
                        "description": "Aggregate events by user_id",
                    }
                ],
                dependencies=["CSVExtractor"],
                implementation_notes="Use dictionary to accumulate events by user_id. Track min/max timestamps for first/last event. Collect unique event types. Count total events per user. Return aggregated dictionary.",
                complexity=45,
            ),
            ComponentLogic(
                semantic_unit_id="SU-003",
                component_name="DatabaseLoader",
                responsibility="Batch load aggregated data into PostgreSQL",
                interfaces=[
                    {
                        "method": "load_batch",
                        "parameters": {"aggregates": "dict"},
                        "returns": "int",
                        "description": "Load aggregated data in batches",
                    }
                ],
                dependencies=["psycopg2", "EventAggregator"],
                implementation_notes="Use psycopg2 executemany() for batch inserts. Batch size: 100 rows. Wrap in transaction for atomicity. Commit after each batch. Handle database errors gracefully. Return count of rows loaded.",
                complexity=35,
            ),
        ],
        design_review_checklist=[
            DesignReviewChecklistItem(
                category="Performance",
                severity="Critical",
                description="Streaming pattern avoids loading full CSV into memory",
                validation_criteria="CSVExtractor must return Iterator[dict] (not list), and process rows one at a time without loading entire file",
            ),
            DesignReviewChecklistItem(
                category="DataIntegrity",
                severity="High",
                description="Database transactions ensure atomic batch loading",
                validation_criteria="DatabaseLoader must wrap batch inserts in transactions to ensure atomicity. Rollback on errors.",
            ),
            DesignReviewChecklistItem(
                category="Maintainability",
                severity="Medium",
                description="Error handling for malformed CSV rows",
                validation_criteria="CSVExtractor must handle malformed rows gracefully, skip them, and log errors without crashing",
            ),
            DesignReviewChecklistItem(
                category="Performance",
                severity="High",
                description="Database indexes on query columns",
                validation_criteria="user_activity_aggregates table must have indexes on last_event_at and processed_at for efficient time-based queries",
            ),
            DesignReviewChecklistItem(
                category="Architecture",
                severity="Medium",
                description="Clear separation of concerns between extraction, transformation, and loading",
                validation_criteria="Each component (CSVExtractor, EventAggregator, DatabaseLoader) must have single responsibility with minimal coupling",
            ),
        ],
        assumptions=[
            "CSV files may be multiple GB in size",
            "User IDs are integers (not UUIDs)",
            "Maximum 10 million unique users per file",
            "Database has sufficient disk space for aggregated data",
        ],
        dependencies_between_units={
            "SU-002": ["SU-001"],  # Aggregator depends on extractor
            "SU-003": ["SU-002"],  # Loader depends on aggregator
        },
        timestamp=datetime.now(),
    )


def example_jwt_authentication():
    """Example 1: Review JWT authentication design."""
    print_header("Example 1: JWT Authentication System Review")

    design_spec = create_jwt_auth_design()

    print("Input:")
    print(f"  Task ID: {design_spec.task_id}")
    print(f"  API Contracts: {len(design_spec.api_contracts)}")
    print(f"  Data Schemas: {len(design_spec.data_schemas)}")
    print(f"  Components: {len(design_spec.component_logic)}")
    print(f"  Checklist Items: {len(design_spec.design_review_checklist)}")
    print()

    # Create orchestrator and execute
    orchestrator = DesignReviewOrchestrator()
    report = orchestrator.execute(design_spec)

    # Display results
    print_review_report(report)

    return report


def example_data_pipeline():
    """Example 2: Review data pipeline design."""
    print_header("Example 2: ETL Data Pipeline Review")

    design_spec = create_data_pipeline_design()

    print("Input:")
    print(f"  Task ID: {design_spec.task_id}")
    print(f"  Data Schemas: {len(design_spec.data_schemas)}")
    print(f"  Components: {len(design_spec.component_logic)}")
    print(f"  Checklist Items: {len(design_spec.design_review_checklist)}")
    print()

    # Create orchestrator and execute
    orchestrator = DesignReviewOrchestrator()
    report = orchestrator.execute(design_spec)

    # Display results
    print_review_report(report)

    return report


def example_full_workflow():
    """Example 3: Full Planning→Design→Design Review workflow."""
    print_header("Example 3: Full Planning->Design->Design Review Workflow")
    print("This example runs all three agents in sequence:\n")
    print("  1. Planning Agent: Decompose task into semantic units")
    print("  2. Design Agent: Generate technical design specification")
    print("  3. Design Review Agent: Validate design quality")
    print()

    requirements_text = """
    Build a RESTful API for a task management system with the following features:

    1. Task CRUD Operations:
       - Create task with title, description, due date, priority
       - Read task by ID or list all tasks with pagination
       - Update task fields (title, description, status, priority)
       - Delete task by ID
       - Soft delete support (mark as deleted, don't remove from DB)

    2. Task Status Management:
       - Status values: TODO, IN_PROGRESS, COMPLETED, DELETED
       - Track status change history with timestamps
       - Prevent invalid status transitions

    3. Search and Filtering:
       - Search tasks by title/description (full-text search)
       - Filter by status, priority, due date range
       - Sort by created_at, due_date, priority

    4. Authentication and Authorization:
       - JWT-based authentication
       - Users can only access their own tasks
       - Admin role can access all tasks

    Technical Requirements:
    - FastAPI framework
    - PostgreSQL database
    - JWT for authentication
    - Full-text search using PostgreSQL tsvector
    - Pagination support (page size: 20)
    - Rate limiting: 100 requests per minute per user
    """

    # Step 1: Run Planning Agent
    print("Step 1: Running Planning Agent...")
    planning_agent = PlanningAgent()

    task_requirements = TaskRequirements(
        task_id="TASK-MGMT-001",
        description="RESTful API for task management with CRUD, search, and authentication",
        requirements=requirements_text,
        context_files=[],
    )

    project_plan = planning_agent.execute(task_requirements)
    print(
        f"[OK] Planning complete: {len(project_plan.semantic_units)} semantic units, complexity={project_plan.total_complexity}"
    )
    print()

    # Step 2: Run Design Agent
    print("Step 2: Running Design Agent...")
    design_agent = DesignAgent()

    design_input = DesignInput(
        task_id="TASK-MGMT-001",
        requirements=requirements_text,
        project_plan=project_plan,
        design_constraints="Use FastAPI, PostgreSQL with full-text search, JWT authentication, soft delete pattern",
    )

    design_spec = design_agent.execute(design_input)
    print(
        f"[OK] Design complete: {len(design_spec.api_contracts)} APIs, {len(design_spec.data_schemas)} schemas, {len(design_spec.component_logic)} components"
    )
    print()

    # Step 3: Run Design Review Agent
    print("Step 3: Running Design Review Orchestrator...")
    orchestrator = DesignReviewOrchestrator()
    report = orchestrator.execute(design_spec)
    print(f"[OK] Design review complete: {report.overall_assessment}")
    print()

    # Display results
    print_review_report(report)

    return report, design_spec, project_plan


def save_report_to_file(report, filename: str):
    """Save design review report to JSON file."""
    output_path = Path(filename)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Convert to dict for JSON serialization
    report_dict = report.model_dump(mode="json")

    with open(output_path, "w") as f:
        json.dump(report_dict, f, indent=2)

    print(f"Report saved to: {output_path}")


def main():
    """Run Design Review Agent examples."""
    parser = argparse.ArgumentParser(
        description="Design Review Agent example script",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--example",
        choices=["jwt", "pipeline", "full-workflow", "all"],
        default="jwt",
        help="Which example to run (default: jwt)",
    )
    parser.add_argument(
        "--output",
        type=str,
        help="Save report to JSON file",
    )

    args = parser.parse_args()

    # Banner
    print("=" * 80)
    print("  ASP Platform - Design Review Agent Demonstration")
    print("=" * 80)
    print()
    print("This script demonstrates the Design Review Orchestrator's ability to")
    print("validate design specifications using 6 specialist review agents:")
    print("  - SecurityReviewAgent: Authentication, authorization, encryption")
    print("  - PerformanceReviewAgent: Indexing, caching, scalability")
    print("  - DataIntegrityReviewAgent: Constraints, referential integrity")
    print("  - MaintainabilityReviewAgent: Coupling, cohesion, modularity")
    print("  - ArchitectureReviewAgent: Design patterns, separation of concerns")
    print("  - APIDesignReviewAgent: RESTful principles, error handling")
    print()

    try:
        reports = []

        if args.example == "jwt":
            report = example_jwt_authentication()
            reports.append(report)

        elif args.example == "pipeline":
            report = example_data_pipeline()
            reports.append(report)

        elif args.example == "full-workflow":
            report, design_spec, project_plan = example_full_workflow()
            reports.append(report)

        elif args.example == "all":
            report1 = example_jwt_authentication()
            reports.append(report1)

            report2 = example_data_pipeline()
            reports.append(report2)

        # Summary
        print_header("Summary")
        print(f"Reviewed {len(reports)} design(s) successfully!")
        print()
        for i, report in enumerate(reports, 1):
            print(f"Design {i}: {report.task_id}")
            print(f"  - Assessment: {report.overall_assessment}")
            print(
                f"  - Issues: {len(report.issues_found)} (Critical: {report.critical_issue_count}, High: {report.high_issue_count})"
            )
            print(f"  - Suggestions: {len(report.improvement_suggestions)}")
            print(f"  - Duration: {report.review_duration_ms:.0f}ms")
        print()

        if args.output and reports:
            save_report_to_file(reports[0], args.output)

        print("=" * 80)
        print()
        print("Next steps:")
        print(
            "  1. Check Langfuse dashboard for telemetry: https://us.cloud.langfuse.com"
        )
        print(
            "  2. Query SQLite for cost data: uv run python scripts/query_telemetry.py"
        )
        print("  3. Address Critical/High issues before code generation")
        print("  4. Proceed to Code Agent (FR-004) if assessment is PASS")
        print()
        print("=" * 80)

        return 0

    except Exception as e:
        print()
        print("=" * 80)
        print("  ERROR")
        print("=" * 80)
        print()
        print(f"Design Review Agent failed: {e}")
        print()
        print("Common issues:")
        print("  - ANTHROPIC_API_KEY not set (check: echo $ANTHROPIC_API_KEY)")
        print("  - Network connectivity issues")
        print("  - Rate limit exceeded")
        print("  - Invalid design specification (missing required fields)")
        print()
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
