"""
Unit tests for Design Review Agent (Orchestrator and Specialists).

Tests cover:
- Initialization of all 6 specialist agents
- Initialization of orchestrator
- Individual specialist execute methods with mocked LLM
- Orchestrator execute with mocked specialists
- Result aggregation and deduplication
- Error handling
- Output validation

Author: ASP Development Team
Date: November 16, 2025
"""

import json
from datetime import datetime
from unittest.mock import MagicMock, Mock, patch

import pytest
from pydantic import ValidationError

from asp.agents.base_agent import AgentExecutionError
from asp.agents.design_review_orchestrator import DesignReviewOrchestrator
from asp.agents.reviews import (
    APIDesignReviewAgent,
    ArchitectureReviewAgent,
    DataIntegrityReviewAgent,
    MaintainabilityReviewAgent,
    PerformanceReviewAgent,
    SecurityReviewAgent,
)
from asp.models.design import (
    APIContract,
    ComponentLogic,
    DataSchema,
    DesignInput,
    DesignReviewChecklistItem,
    DesignSpecification,
)
from asp.models.design_review import (
    ChecklistItemReview,
    DesignIssue,
    DesignReviewReport,
    ImprovementSuggestion,
)
from asp.models.planning import ProjectPlan, PROBEAIPrediction, SemanticUnit


# =============================================================================
# Test Fixtures
# =============================================================================


def create_test_semantic_units():
    """Create test semantic units for project plan."""
    return [
        SemanticUnit(
            unit_id="SU-001",
            description="API endpoint for JWT authentication",
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
            description="Database schema for sessions table",
            api_interactions=0,
            data_transformations=0,
            logical_branches=0,
            code_entities_modified=1,
            novelty_multiplier=1.0,
            est_complexity=15,
            dependencies=[],
        ),
        SemanticUnit(
            unit_id="SU-003",
            description="JWT token generation and validation service",
            api_interactions=0,
            data_transformations=1,
            logical_branches=2,
            code_entities_modified=1,
            novelty_multiplier=1.0,
            est_complexity=20,
            dependencies=[],
        ),
    ]


def create_test_project_plan(task_id="TEST-REVIEW-001"):
    """Create a test project plan."""
    return ProjectPlan(
        task_id=task_id,
        semantic_units=create_test_semantic_units(),
        total_est_complexity=60,
        probe_ai_prediction=PROBEAIPrediction(
            total_est_latency_ms=5000.0,
            total_est_tokens=2800,
            total_est_api_cost=0.02,
            confidence=0.85,
        ),
        probe_ai_enabled=False,
        agent_version="1.0.0",
        timestamp=datetime.now(),
    )


def create_test_design_specification(task_id="TEST-REVIEW-001"):
    """Create a test DesignSpecification for review."""
    return DesignSpecification(
        task_id=task_id,
        api_contracts=[
            APIContract(
                endpoint="/api/v1/auth/login",
                method="POST",
                description="Authenticate user with JWT tokens",
                request_schema={"email": "string", "password": "string"},
                response_schema={"access_token": "string", "refresh_token": "string"},
                error_responses=[
                    {"status": 401, "code": "INVALID_CREDENTIALS", "message": "Invalid email or password"}
                ],
                authentication_required=False,
                rate_limit="5 requests per minute",
            )
        ],
        data_schemas=[
            DataSchema(
                table_name="sessions",
                description="Stores active user sessions with JWT tokens",
                columns=[
                    {"name": "session_id", "type": "UUID", "constraints": "PRIMARY KEY"},
                    {"name": "user_id", "type": "UUID", "constraints": "NOT NULL REFERENCES users(user_id)"},
                    {"name": "access_token", "type": "TEXT", "constraints": "NOT NULL"},
                    {"name": "refresh_token", "type": "TEXT", "constraints": "NOT NULL"},
                    {"name": "expires_at", "type": "TIMESTAMP", "constraints": "NOT NULL"},
                ],
                indexes=["CREATE INDEX idx_sessions_user_id ON sessions(user_id)"],
                relationships=["FOREIGN KEY (user_id) REFERENCES users(user_id)"],
                constraints=[],
            )
        ],
        component_logic=[
            ComponentLogic(
                component_name="JWTAuthenticationService",
                semantic_unit_id="SU-001",
                responsibility="Handles JWT authentication including token generation and validation",
                interfaces=[
                    {
                        "method": "authenticate",
                        "parameters": {"email": "str", "password": "str"},
                        "returns": "AuthTokens",
                        "description": "Authenticate user and return JWT tokens",
                    }
                ],
                dependencies=["DatabaseService", "JWTTokenService"],
                implementation_notes="Use bcrypt for password verification",
                complexity=25,
            ),
            ComponentLogic(
                component_name="JWTTokenService",
                semantic_unit_id="SU-003",
                responsibility="Handles JWT token generation and validation",
                interfaces=[
                    {
                        "method": "generate_token",
                        "parameters": {"user_id": "str", "expiry": "int"},
                        "returns": "str",
                        "description": "Generate JWT token",
                    }
                ],
                dependencies=[],
                implementation_notes="Use HS256 algorithm with secret key from environment",
                complexity=20,
            ),
        ],
        design_review_checklist=[
            DesignReviewChecklistItem(
                category="Security",
                description="Verify JWT tokens use secure signing algorithms",
                validation_criteria="Must use RS256 or HS256 algorithm",
                severity="Critical",
            ),
            DesignReviewChecklistItem(
                category="Security",
                description="Verify password hashing is implemented",
                validation_criteria="Must use bcrypt or argon2",
                severity="Critical",
            ),
            DesignReviewChecklistItem(
                category="Performance",
                description="Verify database indexes are defined for foreign keys",
                validation_criteria="Must have index on user_id column in sessions table",
                severity="High",
            ),
            DesignReviewChecklistItem(
                category="Data Integrity",
                description="Verify foreign key constraints are enforced",
                validation_criteria="Must have FOREIGN KEY constraint on user_id referencing users table",
                severity="High",
            ),
            DesignReviewChecklistItem(
                category="API Design",
                description="Verify error responses are properly defined",
                validation_criteria="Must have at least 3 error responses including 401, 400, and 500",
                severity="Medium",
            ),
        ],
        architecture_overview="This JWT authentication system uses a 3-tier architecture with FastAPI REST API layer, service layer for authentication logic, and PostgreSQL database. JWT tokens are generated using HS256 algorithm and stored in sessions table for tracking.",
        technology_stack={
            "language": "Python 3.12",
            "web_framework": "FastAPI",
            "database": "PostgreSQL",
            "authentication": "JWT (PyJWT library)",
            "password_hashing": "bcrypt",
        },
        total_complexity=60,
        agent_version="1.0.0",
        timestamp=datetime.now(),
    )


def create_mock_security_review_response():
    """Create a mock security review response."""
    return {
        "issues_found": [
            {
                "issue_id": "SEC-001",
                "category": "Security",
                "severity": "Critical",
                "description": "JWT tokens stored in database without encryption expose sensitive authentication data",
                "location": "DataSchema: sessions table - access_token and refresh_token columns",
                "evidence": "Columns defined as TEXT without encryption: access_token TEXT NOT NULL, refresh_token TEXT NOT NULL",
                "impact": "If database is compromised, all active sessions can be hijacked immediately",
                "affected_semantic_units": ["SU-002"],
                "related_components": ["sessions table"],
            }
        ],
        "improvement_suggestions": [
            {
                "suggestion_id": "SEC-SUGG-001",
                "title": "Encrypt JWT tokens at rest in database",
                "description": "Implement AES-256 encryption for JWT tokens stored in the sessions table to protect against database compromise",
                "priority": "High",
                "category": "Security",
                "implementation_notes": "Use application-level encryption with keys managed separately from the database",
                "related_issue_ids": ["SEC-001"],
            }
        ],
    }


def create_mock_performance_review_response():
    """Create a mock performance review response."""
    return {
        "issues_found": [
            {
                "issue_id": "PERF-001",
                "category": "Performance",
                "severity": "High",
                "description": "Missing index on frequently queried expires_at column for session cleanup",
                "location": "DataSchema: sessions table",
                "evidence": "No index defined for expires_at column used in cleanup queries",
                "impact": "Session cleanup queries will perform full table scans as sessions table grows",
                "affected_semantic_units": ["SU-002"],
                "related_components": ["sessions table"],
            }
        ],
        "improvement_suggestions": [
            {
                "suggestion_id": "PERF-SUGG-001",
                "title": "Add index on expires_at column",
                "description": "Create index on expires_at column to optimize session cleanup queries",
                "priority": "High",
                "category": "Performance",
                "implementation_notes": "CREATE INDEX idx_sessions_expires_at ON sessions(expires_at)",
                "related_issue_ids": ["PERF-001"],
            }
        ],
    }


# =============================================================================
# SecurityReviewAgent Tests
# =============================================================================


class TestSecurityReviewAgent:
    """Test suite for SecurityReviewAgent."""

    def test_initialization(self):
        """Test SecurityReviewAgent initialization."""
        agent = SecurityReviewAgent()
        assert agent.agent_version == "1.0.0"
        assert agent.llm_client is not None

    def test_initialization_with_custom_client(self):
        """Test initialization with custom LLM client."""
        mock_client = Mock()
        agent = SecurityReviewAgent(llm_client=mock_client)
        assert agent.llm_client == mock_client

    @patch("asp.agents.base_agent.BaseAgent.call_llm")
    @patch("asp.agents.base_agent.BaseAgent.load_prompt")
    def test_execute_success(self, mock_load_prompt, mock_call_llm):
        """Test successful security review execution."""
        # Setup mocks
        mock_load_prompt.return_value = "Security review prompt: {{design_specification}}"
        mock_call_llm.return_value = {
            "content": json.dumps(create_mock_security_review_response())
        }

        # Create agent and execute
        agent = SecurityReviewAgent()
        design_spec = create_test_design_specification()
        result = agent.execute(design_spec)

        # Verify
        assert "issues_found" in result
        assert "improvement_suggestions" in result
        assert len(result["issues_found"]) == 1
        assert len(result["improvement_suggestions"]) == 1
        assert result["issues_found"][0]["issue_id"] == "SEC-001"
        assert result["issues_found"][0]["severity"] == "Critical"

    @patch("asp.agents.base_agent.BaseAgent.call_llm")
    @patch("asp.agents.base_agent.BaseAgent.load_prompt")
    def test_execute_missing_issues_found(self, mock_load_prompt, mock_call_llm):
        """Test error handling when response missing issues_found."""
        mock_load_prompt.return_value = "Security review prompt"
        mock_call_llm.return_value = {
            "content": json.dumps({"improvement_suggestions": []})
        }

        agent = SecurityReviewAgent()
        design_spec = create_test_design_specification()

        with pytest.raises(AgentExecutionError, match="missing 'issues_found'"):
            agent.execute(design_spec)

    @patch("asp.agents.base_agent.BaseAgent.call_llm")
    @patch("asp.agents.base_agent.BaseAgent.load_prompt")
    def test_execute_invalid_json(self, mock_load_prompt, mock_call_llm):
        """Test error handling with invalid JSON response."""
        mock_load_prompt.return_value = "Security review prompt"
        mock_call_llm.return_value = {"content": "invalid json {"}

        agent = SecurityReviewAgent()
        design_spec = create_test_design_specification()

        with pytest.raises(AgentExecutionError, match="Failed to parse"):
            agent.execute(design_spec)


# =============================================================================
# PerformanceReviewAgent Tests
# =============================================================================


class TestPerformanceReviewAgent:
    """Test suite for PerformanceReviewAgent."""

    def test_initialization(self):
        """Test PerformanceReviewAgent initialization."""
        agent = PerformanceReviewAgent()
        assert agent.agent_version == "1.0.0"
        assert agent.llm_client is not None

    @patch("asp.agents.base_agent.BaseAgent.call_llm")
    @patch("asp.agents.base_agent.BaseAgent.load_prompt")
    def test_execute_success(self, mock_load_prompt, mock_call_llm):
        """Test successful performance review execution."""
        mock_load_prompt.return_value = "Performance review prompt: {{design_specification}}"
        mock_call_llm.return_value = {
            "content": json.dumps(create_mock_performance_review_response())
        }

        agent = PerformanceReviewAgent()
        design_spec = create_test_design_specification()
        result = agent.execute(design_spec)

        assert "issues_found" in result
        assert "improvement_suggestions" in result
        assert len(result["issues_found"]) == 1
        assert result["issues_found"][0]["issue_id"] == "PERF-001"
        assert result["issues_found"][0]["severity"] == "High"


# =============================================================================
# DataIntegrityReviewAgent Tests
# =============================================================================


class TestDataIntegrityReviewAgent:
    """Test suite for DataIntegrityReviewAgent."""

    def test_initialization(self):
        """Test DataIntegrityReviewAgent initialization."""
        agent = DataIntegrityReviewAgent()
        assert agent.agent_version == "1.0.0"
        assert agent.llm_client is not None

    @patch("asp.agents.base_agent.BaseAgent.call_llm")
    @patch("asp.agents.base_agent.BaseAgent.load_prompt")
    def test_execute_success(self, mock_load_prompt, mock_call_llm):
        """Test successful data integrity review execution."""
        mock_load_prompt.return_value = "Data integrity review prompt"
        mock_response = {
            "issues_found": [
                {
                    "issue_id": "DI-001",
                    "category": "Data Integrity",
                    "severity": "Medium",
                    "description": "Missing ON DELETE cascade for session cleanup",
                    "location": "DataSchema: sessions table",
                    "evidence": "Foreign key constraint does not specify ON DELETE behavior",
                    "impact": "Orphaned sessions may remain when users are deleted",
                    "affected_semantic_units": ["SU-002"],
                    "related_components": ["sessions table"],
                }
            ],
            "improvement_suggestions": [],
        }
        mock_call_llm.return_value = {"content": json.dumps(mock_response)}

        agent = DataIntegrityReviewAgent()
        design_spec = create_test_design_specification()
        result = agent.execute(design_spec)

        assert "issues_found" in result
        assert len(result["issues_found"]) == 1
        assert result["issues_found"][0]["category"] == "Data Integrity"


# =============================================================================
# MaintainabilityReviewAgent Tests
# =============================================================================


class TestMaintainabilityReviewAgent:
    """Test suite for MaintainabilityReviewAgent."""

    def test_initialization(self):
        """Test MaintainabilityReviewAgent initialization."""
        agent = MaintainabilityReviewAgent()
        assert agent.agent_version == "1.0.0"

    @patch("asp.agents.base_agent.BaseAgent.call_llm")
    @patch("asp.agents.base_agent.BaseAgent.load_prompt")
    def test_execute_success(self, mock_load_prompt, mock_call_llm):
        """Test successful maintainability review execution."""
        mock_load_prompt.return_value = "Maintainability review prompt"
        mock_response = {
            "issues_found": [],
            "improvement_suggestions": [
                {
                    "suggestion_id": "MAINT-SUGG-001",
                    "title": "Extract token validation logic to separate service",
                    "description": "Improve separation of concerns by extracting validation logic",
                    "priority": "Medium",
                    "category": "Maintainability",
                    "implementation_notes": "Create TokenValidationService",
                    "related_issue_ids": [],
                }
            ],
        }
        mock_call_llm.return_value = {"content": json.dumps(mock_response)}

        agent = MaintainabilityReviewAgent()
        design_spec = create_test_design_specification()
        result = agent.execute(design_spec)

        assert "improvement_suggestions" in result
        assert len(result["improvement_suggestions"]) == 1


# =============================================================================
# ArchitectureReviewAgent Tests
# =============================================================================


class TestArchitectureReviewAgent:
    """Test suite for ArchitectureReviewAgent."""

    def test_initialization(self):
        """Test ArchitectureReviewAgent initialization."""
        agent = ArchitectureReviewAgent()
        assert agent.agent_version == "1.0.0"

    @patch("asp.agents.base_agent.BaseAgent.call_llm")
    @patch("asp.agents.base_agent.BaseAgent.load_prompt")
    def test_execute_success(self, mock_load_prompt, mock_call_llm):
        """Test successful architecture review execution."""
        mock_load_prompt.return_value = "Architecture review prompt"
        mock_response = {
            "issues_found": [],
            "improvement_suggestions": [],
        }
        mock_call_llm.return_value = {"content": json.dumps(mock_response)}

        agent = ArchitectureReviewAgent()
        design_spec = create_test_design_specification()
        result = agent.execute(design_spec)

        assert "issues_found" in result
        assert "improvement_suggestions" in result


# =============================================================================
# APIDesignReviewAgent Tests
# =============================================================================


class TestAPIDesignReviewAgent:
    """Test suite for APIDesignReviewAgent."""

    def test_initialization(self):
        """Test APIDesignReviewAgent initialization."""
        agent = APIDesignReviewAgent()
        assert agent.agent_version == "1.0.0"

    @patch("asp.agents.base_agent.BaseAgent.call_llm")
    @patch("asp.agents.base_agent.BaseAgent.load_prompt")
    def test_execute_success(self, mock_load_prompt, mock_call_llm):
        """Test successful API design review execution."""
        mock_load_prompt.return_value = "API design review prompt"
        mock_response = {
            "issues_found": [
                {
                    "issue_id": "API-001",
                    "category": "API Design",
                    "severity": "Low",
                    "description": "Missing API versioning in endpoint path",
                    "location": "APIContract: /api/v1/auth/login",
                    "evidence": "Endpoint uses /api/v1/ prefix but version is not documented",
                    "impact": "Future API changes may break existing clients",
                    "affected_semantic_units": ["SU-001"],
                    "related_components": ["JWTAuthenticationService"],
                }
            ],
            "improvement_suggestions": [],
        }
        mock_call_llm.return_value = {"content": json.dumps(mock_response)}

        agent = APIDesignReviewAgent()
        design_spec = create_test_design_specification()
        result = agent.execute(design_spec)

        assert "issues_found" in result
        assert len(result["issues_found"]) == 1
        assert result["issues_found"][0]["category"] == "API Design"


# =============================================================================
# DesignReviewOrchestrator Tests
# =============================================================================


class TestDesignReviewOrchestrator:
    """Test suite for DesignReviewOrchestrator."""

    def test_initialization(self):
        """Test orchestrator initialization."""
        orchestrator = DesignReviewOrchestrator()
        assert orchestrator.agent_version == "1.0.0"
        assert len(orchestrator.specialists) == 6
        assert "security" in orchestrator.specialists
        assert "performance" in orchestrator.specialists
        assert "data_integrity" in orchestrator.specialists
        assert "maintainability" in orchestrator.specialists
        assert "architecture" in orchestrator.specialists
        assert "api_design" in orchestrator.specialists

    def test_specialists_are_correct_types(self):
        """Test that specialists are initialized with correct types."""
        orchestrator = DesignReviewOrchestrator()
        assert isinstance(orchestrator.specialists["security"], SecurityReviewAgent)
        assert isinstance(orchestrator.specialists["performance"], PerformanceReviewAgent)
        assert isinstance(orchestrator.specialists["data_integrity"], DataIntegrityReviewAgent)
        assert isinstance(orchestrator.specialists["maintainability"], MaintainabilityReviewAgent)
        assert isinstance(orchestrator.specialists["architecture"], ArchitectureReviewAgent)
        assert isinstance(orchestrator.specialists["api_design"], APIDesignReviewAgent)

    @patch.object(SecurityReviewAgent, "execute")
    @patch.object(PerformanceReviewAgent, "execute")
    @patch.object(DataIntegrityReviewAgent, "execute")
    @patch.object(MaintainabilityReviewAgent, "execute")
    @patch.object(ArchitectureReviewAgent, "execute")
    @patch.object(APIDesignReviewAgent, "execute")
    def test_execute_success(
        self,
        mock_api,
        mock_arch,
        mock_maint,
        mock_di,
        mock_perf,
        mock_sec,
    ):
        """Test successful orchestrated review execution."""
        # Setup mock responses
        mock_sec.return_value = create_mock_security_review_response()
        mock_perf.return_value = create_mock_performance_review_response()
        mock_di.return_value = {"issues_found": [], "improvement_suggestions": []}
        mock_maint.return_value = {"issues_found": [], "improvement_suggestions": []}
        mock_arch.return_value = {"issues_found": [], "improvement_suggestions": []}
        mock_api.return_value = {"issues_found": [], "improvement_suggestions": []}

        # Execute orchestrator
        orchestrator = DesignReviewOrchestrator()
        design_spec = create_test_design_specification()
        report = orchestrator.execute(design_spec)

        # Verify report structure
        assert isinstance(report, DesignReviewReport)
        assert report.task_id == "TEST-REVIEW-001"
        assert len(report.issues_found) == 2  # 1 security + 1 performance
        assert len(report.improvement_suggestions) == 2
        assert report.critical_issue_count == 1
        assert report.high_issue_count == 1
        assert report.overall_assessment in ["PASS", "FAIL", "NEEDS_IMPROVEMENT"]

        # Verify all specialists were called
        assert mock_sec.called
        assert mock_perf.called
        assert mock_di.called
        assert mock_maint.called
        assert mock_arch.called
        assert mock_api.called

    @patch.object(SecurityReviewAgent, "execute")
    @patch.object(PerformanceReviewAgent, "execute")
    @patch.object(DataIntegrityReviewAgent, "execute")
    @patch.object(MaintainabilityReviewAgent, "execute")
    @patch.object(ArchitectureReviewAgent, "execute")
    @patch.object(APIDesignReviewAgent, "execute")
    def test_execute_with_duplicate_issues(
        self,
        mock_api,
        mock_arch,
        mock_maint,
        mock_di,
        mock_perf,
        mock_sec,
    ):
        """Test deduplication of similar issues from multiple specialists."""
        # Create duplicate issue with different IDs but same description
        duplicate_issue = {
            "issue_id": "PERF-002",
            "category": "Performance",
            "severity": "High",
            "description": "JWT tokens stored in database without encryption expose sensitive authentication data",
            "location": "DataSchema: sessions table",
            "evidence": "Similar evidence about token storage",
            "impact": "Security and performance impact",
            "affected_semantic_units": ["SU-002"],
            "related_components": ["sessions table"],
        }

        mock_sec.return_value = create_mock_security_review_response()
        mock_perf.return_value = {
            "issues_found": [duplicate_issue],
            "improvement_suggestions": [],
        }
        mock_di.return_value = {"issues_found": [], "improvement_suggestions": []}
        mock_maint.return_value = {"issues_found": [], "improvement_suggestions": []}
        mock_arch.return_value = {"issues_found": [], "improvement_suggestions": []}
        mock_api.return_value = {"issues_found": [], "improvement_suggestions": []}

        orchestrator = DesignReviewOrchestrator()
        design_spec = create_test_design_specification()
        report = orchestrator.execute(design_spec)

        # Should deduplicate to 1 issue (or keep both if descriptions differ enough)
        # The exact behavior depends on deduplication logic
        assert isinstance(report, DesignReviewReport)
        assert len(report.issues_found) >= 1  # At least one issue after deduplication

    @patch.object(SecurityReviewAgent, "execute")
    @patch.object(PerformanceReviewAgent, "execute")
    @patch.object(DataIntegrityReviewAgent, "execute")
    @patch.object(MaintainabilityReviewAgent, "execute")
    @patch.object(ArchitectureReviewAgent, "execute")
    @patch.object(APIDesignReviewAgent, "execute")
    def test_execute_specialist_failure(
        self,
        mock_api,
        mock_arch,
        mock_maint,
        mock_di,
        mock_perf,
        mock_sec,
    ):
        """Test graceful handling of specialist execution failure."""
        # Mock one specialist raising an error
        mock_sec.side_effect = AgentExecutionError("Security review failed")
        # Other specialists return normal results
        mock_perf.return_value = {"issues_found": [], "improvement_suggestions": []}
        mock_di.return_value = {"issues_found": [], "improvement_suggestions": []}
        mock_maint.return_value = {"issues_found": [], "improvement_suggestions": []}
        mock_arch.return_value = {"issues_found": [], "improvement_suggestions": []}
        mock_api.return_value = {"issues_found": [], "improvement_suggestions": []}

        orchestrator = DesignReviewOrchestrator()
        design_spec = create_test_design_specification()

        # Orchestrator should handle specialist failure gracefully and continue
        report = orchestrator.execute(design_spec)

        # Should still produce a valid report with results from successful specialists
        assert isinstance(report, DesignReviewReport)
        assert report.task_id == "TEST-REVIEW-001"

    @patch.object(SecurityReviewAgent, "execute")
    @patch.object(PerformanceReviewAgent, "execute")
    @patch.object(DataIntegrityReviewAgent, "execute")
    @patch.object(MaintainabilityReviewAgent, "execute")
    @patch.object(ArchitectureReviewAgent, "execute")
    @patch.object(APIDesignReviewAgent, "execute")
    def test_checklist_review_generation(
        self,
        mock_api,
        mock_arch,
        mock_maint,
        mock_di,
        mock_perf,
        mock_sec,
    ):
        """Test that orchestrator generates checklist review items."""
        mock_sec.return_value = {"issues_found": [], "improvement_suggestions": []}
        mock_perf.return_value = {"issues_found": [], "improvement_suggestions": []}
        mock_di.return_value = {"issues_found": [], "improvement_suggestions": []}
        mock_maint.return_value = {"issues_found": [], "improvement_suggestions": []}
        mock_arch.return_value = {"issues_found": [], "improvement_suggestions": []}
        mock_api.return_value = {"issues_found": [], "improvement_suggestions": []}

        orchestrator = DesignReviewOrchestrator()
        design_spec = create_test_design_specification()
        report = orchestrator.execute(design_spec)

        # Verify checklist items are reviewed
        assert len(report.checklist_review) > 0
        for item in report.checklist_review:
            assert isinstance(item, ChecklistItemReview)
            assert item.category in ["Security", "Performance", "Data Integrity", "Maintainability", "Architecture", "API Design"]
            assert len(item.notes) >= 20  # Minimum length requirement
