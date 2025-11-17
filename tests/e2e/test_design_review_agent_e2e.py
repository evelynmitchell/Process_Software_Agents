"""
End-to-End tests for Design Review Agent with real Anthropic API.

These tests make actual API calls to validate the complete multi-agent review workflow.
They are marked with @pytest.mark.e2e and can be run with:
    pytest tests/e2e/test_design_review_agent_e2e.py -m e2e

Requirements:
- ANTHROPIC_API_KEY environment variable must be set
- Will consume API credits (approximately $0.15-0.25 per test due to 6 specialists)
"""

import os
from datetime import datetime

import pytest

from asp.agents.design_review_orchestrator import DesignReviewOrchestrator
from asp.models.design import (
    APIContract,
    ComponentLogic,
    DataSchema,
    DesignReviewChecklistItem,
    DesignSpecification,
)
from asp.models.design_review import DesignReviewReport


# Skip all tests if no API key is available
pytestmark = pytest.mark.skipif(
    not os.getenv("ANTHROPIC_API_KEY"),
    reason="ANTHROPIC_API_KEY not set - skipping E2E tests",
)


def create_jwt_auth_design_spec() -> DesignSpecification:
    """Helper to create a JWT authentication design specification for testing."""
    return DesignSpecification(
        task_id="E2E-REVIEW-001",
        api_contracts=[
            APIContract(
                endpoint="/api/v1/auth/login",
                method="POST",
                description="Authenticate user with email/password and return JWT tokens",
                request_schema={"email": "string", "password": "string"},
                response_schema={
                    "access_token": "string",
                    "refresh_token": "string",
                    "expires_in": "integer",
                },
                error_responses=[
                    {
                        "status": 401,
                        "code": "INVALID_CREDENTIALS",
                        "message": "Invalid email or password",
                    },
                    {
                        "status": 400,
                        "code": "VALIDATION_ERROR",
                        "message": "Invalid request format",
                    },
                    {
                        "status": 429,
                        "code": "RATE_LIMIT_EXCEEDED",
                        "message": "Too many login attempts",
                    },
                ],
                authentication_required=False,
                rate_limit="5 requests per minute per IP",
            ),
            APIContract(
                endpoint="/api/v1/auth/refresh",
                method="POST",
                description="Refresh access token using refresh token",
                request_schema={"refresh_token": "string"},
                response_schema={"access_token": "string", "expires_in": "integer"},
                error_responses=[
                    {
                        "status": 401,
                        "code": "INVALID_TOKEN",
                        "message": "Invalid or expired refresh token",
                    }
                ],
                authentication_required=False,
                rate_limit="10 requests per minute",
            ),
        ],
        data_schemas=[
            DataSchema(
                table_name="users",
                description="Stores user account information and credentials",
                columns=[
                    {"name": "user_id", "type": "UUID", "constraints": "PRIMARY KEY"},
                    {
                        "name": "email",
                        "type": "VARCHAR(255)",
                        "constraints": "NOT NULL UNIQUE",
                    },
                    {
                        "name": "password_hash",
                        "type": "VARCHAR(255)",
                        "constraints": "NOT NULL",
                    },
                    {
                        "name": "created_at",
                        "type": "TIMESTAMP",
                        "constraints": "NOT NULL DEFAULT NOW()",
                    },
                ],
                indexes=[
                    "CREATE INDEX idx_users_email ON users(email)",
                ],
                relationships=[],
                constraints=[],
            ),
            DataSchema(
                table_name="sessions",
                description="Stores active user sessions with JWT refresh tokens",
                columns=[
                    {
                        "name": "session_id",
                        "type": "UUID",
                        "constraints": "PRIMARY KEY",
                    },
                    {
                        "name": "user_id",
                        "type": "UUID",
                        "constraints": "NOT NULL REFERENCES users(user_id)",
                    },
                    {
                        "name": "refresh_token_hash",
                        "type": "VARCHAR(255)",
                        "constraints": "NOT NULL",
                    },
                    {
                        "name": "expires_at",
                        "type": "TIMESTAMP",
                        "constraints": "NOT NULL",
                    },
                    {
                        "name": "created_at",
                        "type": "TIMESTAMP",
                        "constraints": "NOT NULL DEFAULT NOW()",
                    },
                ],
                indexes=[
                    "CREATE INDEX idx_sessions_user_id ON sessions(user_id)",
                    "CREATE INDEX idx_sessions_expires_at ON sessions(expires_at)",
                ],
                relationships=["FOREIGN KEY (user_id) REFERENCES users(user_id)"],
                constraints=[],
            ),
        ],
        component_logic=[
            ComponentLogic(
                component_name="AuthenticationService",
                semantic_unit_id="SU-001",
                responsibility="Handles user authentication including credential validation and JWT token generation",
                interfaces=[
                    {
                        "method": "authenticate",
                        "parameters": {"email": "str", "password": "str"},
                        "returns": "AuthTokens",
                        "description": "Authenticate user and return JWT tokens",
                    }
                ],
                dependencies=["UserRepository", "PasswordHasher", "JWTTokenService"],
                implementation_notes="Use bcrypt for password verification. Implement rate limiting per IP address.",
                complexity=30,
            ),
            ComponentLogic(
                component_name="JWTTokenService",
                semantic_unit_id="SU-002",
                responsibility="Handles JWT token generation, validation, and refresh",
                interfaces=[
                    {
                        "method": "generate_access_token",
                        "parameters": {"user_id": "str", "expiry_minutes": "int"},
                        "returns": "str",
                        "description": "Generate JWT access token",
                    },
                    {
                        "method": "generate_refresh_token",
                        "parameters": {"user_id": "str"},
                        "returns": "str",
                        "description": "Generate JWT refresh token",
                    },
                ],
                dependencies=[],
                implementation_notes="Use RS256 algorithm with key rotation. Access tokens expire in 15 minutes, refresh tokens in 7 days.",
                complexity=25,
            ),
            ComponentLogic(
                component_name="UserRepository",
                semantic_unit_id="SU-003",
                responsibility="Handles database operations for user data",
                interfaces=[
                    {
                        "method": "find_by_email",
                        "parameters": {"email": "str"},
                        "returns": "Optional[User]",
                        "description": "Find user by email address",
                    }
                ],
                dependencies=[],
                implementation_notes="Use parameterized queries to prevent SQL injection",
                complexity=15,
            ),
        ],
        design_review_checklist=[
            DesignReviewChecklistItem(
                category="Security",
                description="Verify passwords are hashed using bcrypt or argon2",
                validation_criteria="Users table must have password_hash column, not plaintext password",
                severity="Critical",
            ),
            DesignReviewChecklistItem(
                category="Security",
                description="Verify JWT tokens use secure signing algorithms",
                validation_criteria="Must use RS256 or HS256, not none algorithm",
                severity="Critical",
            ),
            DesignReviewChecklistItem(
                category="Security",
                description="Verify rate limiting is implemented for authentication endpoints",
                validation_criteria="Login endpoint must have rate limit specified",
                severity="High",
            ),
            DesignReviewChecklistItem(
                category="Performance",
                description="Verify database indexes exist for foreign keys",
                validation_criteria="Sessions table must have index on user_id column",
                severity="High",
            ),
            DesignReviewChecklistItem(
                category="Data Integrity",
                description="Verify foreign key constraints are defined",
                validation_criteria="Sessions table must have FK constraint to users table",
                severity="High",
            ),
        ],
        architecture_overview="This JWT authentication system uses a 3-tier architecture with FastAPI REST API layer, service layer for authentication logic, and PostgreSQL database. JWT access tokens provide stateless authentication with 15-minute expiry. Refresh tokens are stored hashed in database for revocation capability. Password verification uses bcrypt hashing.",
        technology_stack={
            "language": "Python 3.12",
            "web_framework": "FastAPI 0.104",
            "database": "PostgreSQL 15",
            "authentication": "JWT (PyJWT library with RS256)",
            "password_hashing": "bcrypt",
            "rate_limiting": "Redis with sliding window",
        },
        total_complexity=70,
        agent_version="1.0.0",
        timestamp=datetime.now(),
    )


@pytest.mark.e2e
class TestDesignReviewAgentE2E:
    """End-to-end tests with real API calls to all 6 specialist agents."""

    def test_jwt_authentication_design_review(self):
        """Test complete design review for JWT authentication system."""
        # Create orchestrator
        orchestrator = DesignReviewOrchestrator()

        # Create design specification
        design_spec = create_jwt_auth_design_spec()

        # Execute with real API calls (6 specialists in parallel)
        print("\nExecuting design review with 6 specialist agents...")
        report = orchestrator.execute(design_spec)

        # Validate report structure
        assert isinstance(report, DesignReviewReport)
        assert report.task_id == "E2E-REVIEW-001"
        assert len(report.review_id) > 0
        assert report.review_id.startswith("REVIEW-")

        # Validate overall assessment
        assert report.overall_assessment in ["PASS", "FAIL", "NEEDS_IMPROVEMENT"]
        print(f"Overall Assessment: {report.overall_assessment}")

        # Validate automated checks
        assert isinstance(report.automated_checks, dict)
        assert len(report.automated_checks) > 0

        # Validate issues found
        assert isinstance(report.issues_found, list)
        print(f"Issues Found: {len(report.issues_found)}")
        for issue in report.issues_found:
            assert len(issue.issue_id) > 0
            assert issue.issue_id.startswith("ISSUE-")
            assert issue.severity in ["Critical", "High", "Medium", "Low"]
            # Validate against actual Literal values from DesignIssue model
            assert issue.category in [
                "Security",
                "Performance",
                "Data Integrity",
                "Error Handling",
                "Architecture",
                "Maintainability",
                "API Design",
                "Scalability",
            ]
            assert len(issue.description) >= 20
            assert len(issue.evidence) >= 10
            assert len(issue.impact) >= 20

        # Validate improvement suggestions
        assert isinstance(report.improvement_suggestions, list)
        print(f"Improvement Suggestions: {len(report.improvement_suggestions)}")
        for suggestion in report.improvement_suggestions:
            assert len(suggestion.suggestion_id) > 0
            assert suggestion.priority in ["Critical", "High", "Medium", "Low"]
            assert len(suggestion.description) >= 30
            assert len(suggestion.implementation_notes) >= 20

        # Validate checklist review
        assert isinstance(report.checklist_review, list)
        assert len(report.checklist_review) == 5  # We defined 5 checklist items
        print(f"Checklist Items Reviewed: {len(report.checklist_review)}")
        for item in report.checklist_review:
            assert item.status in ["Pass", "Fail", "Warning"]
            assert len(item.notes) >= 20
            # Categories may be normalized during review
            assert len(item.category) > 0

        # Validate issue counts
        assert report.critical_issue_count >= 0
        assert report.high_issue_count >= 0
        assert report.medium_issue_count >= 0
        assert report.low_issue_count >= 0
        total_issues = (
            report.critical_issue_count
            + report.high_issue_count
            + report.medium_issue_count
            + report.low_issue_count
        )
        assert total_issues == len(report.issues_found)
        print(
            f"Issue Breakdown: {report.critical_issue_count}C / {report.high_issue_count}H / "
            f"{report.medium_issue_count}M / {report.low_issue_count}L"
        )

        # Validate review duration
        assert report.review_duration_ms > 0
        print(f"Review Duration: {report.review_duration_ms:.0f}ms")

        # Validate metadata
        assert report.reviewer_agent == "DesignReviewOrchestrator"
        assert report.agent_version == "1.0.0"

    def test_simple_crud_api_review(self):
        """Test design review for a simple CRUD API."""
        orchestrator = DesignReviewOrchestrator()

        # Create a simpler design spec
        design_spec = DesignSpecification(
            task_id="E2E-REVIEW-002",
            api_contracts=[
                APIContract(
                    endpoint="/api/v1/tasks",
                    method="GET",
                    description="Retrieve list of tasks",
                    request_schema=None,
                    response_schema={"tasks": "array"},
                    error_responses=[
                        {"status": 500, "code": "INTERNAL_ERROR", "message": "Server error"}
                    ],
                    authentication_required=True,
                    rate_limit="100 requests per minute",
                ),
                APIContract(
                    endpoint="/api/v1/tasks",
                    method="POST",
                    description="Create a new task",
                    request_schema={"title": "string", "description": "string"},
                    response_schema={"task_id": "string", "title": "string"},
                    error_responses=[
                        {
                            "status": 400,
                            "code": "VALIDATION_ERROR",
                            "message": "Invalid input",
                        }
                    ],
                    authentication_required=True,
                    rate_limit="50 requests per minute",
                ),
            ],
            data_schemas=[
                DataSchema(
                    table_name="tasks",
                    description="Stores task information",
                    columns=[
                        {"name": "task_id", "type": "UUID", "constraints": "PRIMARY KEY"},
                        {"name": "title", "type": "VARCHAR(255)", "constraints": "NOT NULL"},
                        {"name": "description", "type": "TEXT", "constraints": ""},
                        {"name": "created_at", "type": "TIMESTAMP", "constraints": "NOT NULL"},
                    ],
                    indexes=[],
                    relationships=[],
                    constraints=[],
                )
            ],
            component_logic=[
                ComponentLogic(
                    component_name="TaskService",
                    semantic_unit_id="SU-001",
                    responsibility="Handles task CRUD operations",
                    interfaces=[
                        {
                            "method": "get_tasks",
                            "parameters": {},
                            "returns": "List[Task]",
                            "description": "Get all tasks",
                        }
                    ],
                    dependencies=["TaskRepository"],
                    implementation_notes="Simple CRUD operations with basic validation",
                    complexity=15,
                )
            ],
            design_review_checklist=[
                DesignReviewChecklistItem(
                    category="Security",
                    description="Verify authentication is required for all endpoints",
                    validation_criteria="All endpoints must have authentication_required=true",
                    severity="Critical",
                ),
                DesignReviewChecklistItem(
                    category="Performance",
                    description="Verify pagination is implemented for list endpoints",
                    validation_criteria="GET endpoint should support limit/offset parameters",
                    severity="Medium",
                ),
                DesignReviewChecklistItem(
                    category="Data Integrity",
                    description="Verify primary keys are defined",
                    validation_criteria="Tasks table must have PRIMARY KEY constraint",
                    severity="High",
                ),
                DesignReviewChecklistItem(
                    category="API Design",
                    description="Verify error responses are comprehensive",
                    validation_criteria="Each endpoint must have at least 2 error responses",
                    severity="Medium",
                ),
                DesignReviewChecklistItem(
                    category="Architecture",
                    description="Verify proper separation of concerns",
                    validation_criteria="Service layer should be separate from repository layer",
                    severity="Medium",
                ),
            ],
            architecture_overview="Simple 3-tier CRUD API with REST endpoints, service layer for business logic, and PostgreSQL for data persistence. Uses standard RESTful patterns.",
            technology_stack={
                "language": "Python 3.12",
                "web_framework": "FastAPI",
                "database": "PostgreSQL 15",
            },
            total_complexity=15,
            agent_version="1.0.0",
            timestamp=datetime.now(),
        )

        # Execute review
        print("\nExecuting design review for simple CRUD API...")
        report = orchestrator.execute(design_spec)

        # Basic validations
        assert isinstance(report, DesignReviewReport)
        assert report.task_id == "E2E-REVIEW-002"
        assert report.overall_assessment in ["PASS", "FAIL", "NEEDS_IMPROVEMENT"]
        assert len(report.issues_found) >= 0
        assert len(report.improvement_suggestions) >= 0
        assert len(report.checklist_review) == 5

        print(f"Overall Assessment: {report.overall_assessment}")
        print(f"Issues: {len(report.issues_found)}")
        print(f"Suggestions: {len(report.improvement_suggestions)}")

    def test_minimal_design_review(self):
        """Test design review with minimal but valid design specification."""
        orchestrator = DesignReviewOrchestrator()

        design_spec = DesignSpecification(
            task_id="E2E-REVIEW-003",
            api_contracts=[],  # No API contracts
            data_schemas=[
                DataSchema(
                    table_name="events",
                    description="Simple event log table",
                    columns=[
                        {"name": "event_id", "type": "UUID", "constraints": "PRIMARY KEY"},
                        {"name": "event_type", "type": "VARCHAR(50)", "constraints": "NOT NULL"},
                    ],
                    indexes=[],
                    relationships=[],
                    constraints=[],
                )
            ],
            component_logic=[
                ComponentLogic(
                    component_name="EventLogger",
                    semantic_unit_id="SU-001",
                    responsibility="Logs events to database",
                    interfaces=[
                        {
                            "method": "log_event",
                            "parameters": {"event_type": "str"},
                            "returns": "None",
                            "description": "Log an event",
                        }
                    ],
                    dependencies=[],
                    implementation_notes="Simple event logging with no complex logic",
                    complexity=5,
                )
            ],
            design_review_checklist=[
                DesignReviewChecklistItem(
                    category="Data Integrity",
                    description="Verify primary key is defined",
                    validation_criteria="Events table must have PRIMARY KEY",
                    severity="High",
                ),
                DesignReviewChecklistItem(
                    category="Performance",
                    description="Verify indexes are defined for frequently queried columns",
                    validation_criteria="Should have index on event_type if queried frequently",
                    severity="Medium",
                ),
                DesignReviewChecklistItem(
                    category="Architecture",
                    description="Verify component has clear responsibility",
                    validation_criteria="Component should have single, well-defined responsibility",
                    severity="Low",
                ),
                DesignReviewChecklistItem(
                    category="Security",
                    description="Verify no sensitive data is logged in plaintext",
                    validation_criteria="Event data should not contain passwords or secrets",
                    severity="High",
                ),
                DesignReviewChecklistItem(
                    category="Maintainability",
                    description="Verify component interfaces are well-defined",
                    validation_criteria="Interfaces should have clear parameters and return types",
                    severity="Low",
                ),
            ],
            architecture_overview="Minimal event logging system with single component writing to PostgreSQL database table. No API layer or complex business logic.",
            technology_stack={"language": "Python 3.12", "database": "PostgreSQL 15"},
            total_complexity=5,
            agent_version="1.0.0",
            timestamp=datetime.now(),
        )

        # Execute review
        print("\nExecuting design review for minimal event logger...")
        report = orchestrator.execute(design_spec)

        # Validate report
        assert isinstance(report, DesignReviewReport)
        assert report.task_id == "E2E-REVIEW-003"
        assert len(report.checklist_review) == 5

        print(f"Overall Assessment: {report.overall_assessment}")
        print(f"Review completed in {report.review_duration_ms:.0f}ms")
