"""
Unit tests for API Design Review Agent (FR-003).

Tests the specialist agent that reviews design specifications for API design:
- RESTful principles and best practices
- HTTP methods and status codes
- Error handling and responses
- API versioning strategies
- Request/response schema design
"""

import json
import logging
from unittest.mock import MagicMock, patch

import pytest

from asp.agents.base_agent import AgentExecutionError
from asp.agents.reviews.api_design_review_agent import APIDesignReviewAgent
from asp.models.design import (
    APIContract,
    ComponentLogic,
    DesignReviewChecklistItem,
    DesignSpecification,
)


class TestAPIDesignReviewAgentInitialization:
    """Test API Design Review Agent initialization."""

    def test_initialization_with_defaults(self):
        """Test agent initializes with default values."""
        agent = APIDesignReviewAgent()

        assert agent.agent_version == "1.0.0"

    def test_initialization_with_custom_llm_client(self):
        """Test agent initializes with custom LLM client."""
        mock_client = MagicMock()
        agent = APIDesignReviewAgent(llm_client=mock_client)

        assert agent.agent_version == "1.0.0"

    def test_initialization_with_custom_db_path(self):
        """Test agent initializes with custom database path."""
        agent = APIDesignReviewAgent(db_path=":memory:")

        assert agent.agent_version == "1.0.0"


class TestAPIDesignReviewAgentExecute:
    """Test API Design Review Agent execute method."""

    @pytest.fixture
    def agent(self):
        """Create API Design Review Agent instance."""
        return APIDesignReviewAgent(db_path=":memory:")

    @pytest.fixture
    def design_spec(self):
        """Create a sample design specification."""
        return DesignSpecification(
            task_id="API-TEST-001",
            component_logic=[
                ComponentLogic(
                    component_name="UserAPI",
                    semantic_unit_id="SU-001",
                    responsibility="Provide user management API endpoints",
                    interfaces=[{"method": "get_user", "parameters": ["user_id"]}],
                    implementation_notes="REST API for user operations",
                )
            ],
            api_contracts=[
                APIContract(
                    endpoint="/users/{id}",
                    method="GET",
                    description="Get user by ID, returns 200 on success, 500 on any error",
                    request_schema={"id": "string"},
                    response_schema={"user": "object"},
                    success_codes=[200],
                    error_codes=[500],
                    semantic_unit_ids=["SU-001"],
                )
            ],
            design_review_checklist=[
                DesignReviewChecklistItem(
                    checklist_item_id="CHECK-001",
                    category="API Design",
                    severity="Critical",
                    description="Use appropriate HTTP status codes for responses",
                    validation_criteria="200 for success, 404 for not found, 400 for validation errors",
                ),
                DesignReviewChecklistItem(
                    checklist_item_id="CHECK-002",
                    category="API Design",
                    severity="High",
                    description="Follow RESTful resource naming conventions",
                    validation_criteria="Use plural nouns, lowercase, hyphens for multi-word",
                ),
                DesignReviewChecklistItem(
                    checklist_item_id="CHECK-003",
                    category="API Design",
                    severity="High",
                    description="Provide consistent error response format",
                    validation_criteria="Standard error structure with code, message, details",
                ),
                DesignReviewChecklistItem(
                    checklist_item_id="CHECK-004",
                    category="API Design",
                    severity="Medium",
                    description="Include API versioning strategy",
                    validation_criteria="URL path or header-based versioning",
                ),
                DesignReviewChecklistItem(
                    checklist_item_id="CHECK-005",
                    category="API Design",
                    severity="Low",
                    description="Document request/response examples",
                    validation_criteria="OpenAPI or similar documentation",
                ),
            ],
            architecture_overview="RESTful API for user management with inconsistent status codes and error handling",
            technology_stack={"language": "Python", "framework": "FastAPI"},
        )

    @patch.object(APIDesignReviewAgent, "load_prompt")
    @patch.object(APIDesignReviewAgent, "format_prompt")
    @patch.object(APIDesignReviewAgent, "call_llm")
    def test_execute_returns_valid_response(
        self, mock_call_llm, mock_format_prompt, mock_load_prompt, agent, design_spec
    ):
        """Test execute returns valid response with issues and suggestions."""
        mock_load_prompt.return_value = "API design review prompt template"
        mock_format_prompt.return_value = "Formatted prompt with design spec"
        mock_call_llm.return_value = {
            "content": json.dumps(
                {
                    "issues_found": [
                        {
                            "issue_id": "ISSUE-001",
                            "category": "API Design",
                            "severity": "High",
                            "description": "API returns 500 for user not found instead of 404",
                            "evidence": "GET /users/{id} error_codes only includes 500",
                            "impact": "Clients cannot distinguish between server errors and missing resources",
                            "affected_phase": "Design",
                        }
                    ],
                    "improvement_suggestions": [
                        {
                            "suggestion_id": "IMPROVE-001",
                            "related_issue_id": "ISSUE-001",
                            "category": "API Design",
                            "priority": "High",
                            "description": "Return 404 status code when user is not found",
                            "implementation_notes": "Add 404 to error_codes, return 404 with error message when user does not exist",
                        }
                    ],
                }
            )
        }

        result = agent.execute(design_spec)

        assert "issues_found" in result
        assert "improvement_suggestions" in result
        assert len(result["issues_found"]) == 1
        assert len(result["improvement_suggestions"]) == 1
        assert result["issues_found"][0]["category"] == "API Design"

    @patch.object(APIDesignReviewAgent, "load_prompt")
    @patch.object(APIDesignReviewAgent, "format_prompt")
    @patch.object(APIDesignReviewAgent, "call_llm")
    def test_execute_with_no_issues_found(
        self, mock_call_llm, mock_format_prompt, mock_load_prompt, agent, design_spec
    ):
        """Test execute with clean design (no issues)."""
        mock_load_prompt.return_value = "API design review prompt template"
        mock_format_prompt.return_value = "Formatted prompt"
        mock_call_llm.return_value = {
            "content": json.dumps({"issues_found": [], "improvement_suggestions": []})
        }

        result = agent.execute(design_spec)

        assert result["issues_found"] == []
        assert result["improvement_suggestions"] == []

    @patch.object(APIDesignReviewAgent, "load_prompt")
    @patch.object(APIDesignReviewAgent, "format_prompt")
    @patch.object(APIDesignReviewAgent, "call_llm")
    def test_execute_logs_review_metrics(
        self,
        mock_call_llm,
        mock_format_prompt,
        mock_load_prompt,
        agent,
        design_spec,
        caplog,
    ):
        """Test execute logs API design review metrics."""
        mock_load_prompt.return_value = "API design review prompt template"
        mock_format_prompt.return_value = "Formatted prompt"
        mock_call_llm.return_value = {
            "content": json.dumps(
                {
                    "issues_found": [
                        {
                            "issue_id": "ISSUE-001",
                            "category": "API Design",
                            "severity": "High",
                            "description": "API endpoint does not follow RESTful naming conventions",
                            "evidence": "Endpoint uses verb instead of noun in path",
                            "impact": "API design is not intuitive for developers using the service",
                            "affected_phase": "Design",
                        }
                    ],
                    "improvement_suggestions": [],
                }
            )
        }

        with caplog.at_level(logging.INFO):
            agent.execute(design_spec)

        assert "Starting API design review for task API-TEST-001" in caplog.text
        assert "API design review completed: 1 issues, 0 suggestions" in caplog.text


class TestAPIDesignReviewAgentDetection:
    """Test API Design Review Agent detection capabilities."""

    @pytest.fixture
    def agent(self):
        """Create API Design Review Agent instance."""
        return APIDesignReviewAgent(db_path=":memory:")

    @patch.object(APIDesignReviewAgent, "load_prompt")
    @patch.object(APIDesignReviewAgent, "format_prompt")
    @patch.object(APIDesignReviewAgent, "call_llm")
    def test_detect_incorrect_http_status_codes(
        self, mock_call_llm, mock_format_prompt, mock_load_prompt, agent
    ):
        """Test detection of incorrect HTTP status code usage."""
        design_spec = DesignSpecification(
            task_id="API-STATUS-001",
            component_logic=[
                ComponentLogic(
                    component_name="ProductAPI",
                    semantic_unit_id="SU-001",
                    responsibility="Product CRUD operations",
                    interfaces=[{"method": "create_product"}],
                    implementation_notes="REST API endpoint implementation",
                )
            ],
            api_contracts=[
                APIContract(
                    endpoint="/products",
                    method="POST",
                    description="Create new product, returns 200 on success",
                    request_schema={"name": "string", "price": "number"},
                    response_schema={"product": "object"},
                    success_codes=[200],
                    error_codes=[500],
                    semantic_unit_ids=["SU-001"],
                )
            ],
            design_review_checklist=[
                DesignReviewChecklistItem(
                    checklist_item_id="CHECK-001",
                    category="API Design",
                    severity="Critical",
                    description="POST creating resources must return 201 Created",
                    validation_criteria="201 status code with Location header",
                ),
                DesignReviewChecklistItem(
                    checklist_item_id="CHECK-002",
                    category="API Design",
                    severity="High",
                    description="Additional checklist item for comprehensive review coverage",
                    validation_criteria="Validation criteria for completeness",
                ),
                DesignReviewChecklistItem(
                    checklist_item_id="CHECK-003",
                    category="API Design",
                    severity="Medium",
                    description="Additional checklist item for thorough evaluation",
                    validation_criteria="Validation criteria for quality",
                ),
                DesignReviewChecklistItem(
                    checklist_item_id="CHECK-004",
                    category="API Design",
                    severity="Medium",
                    description="Additional checklist item for detailed assessment",
                    validation_criteria="Validation criteria for standards",
                ),
                DesignReviewChecklistItem(
                    checklist_item_id="CHECK-005",
                    category="API Design",
                    severity="Low",
                    description="Additional checklist item for complete verification",
                    validation_criteria="Validation criteria for best practices",
                ),
            ],
            architecture_overview="Product API incorrectly returning 200 instead of 201 for resource creation",
            technology_stack={"framework": "FastAPI"},
        )

        mock_load_prompt.return_value = "API design review template"
        mock_format_prompt.return_value = "Formatted prompt"
        mock_call_llm.return_value = {
            "content": json.dumps(
                {
                    "issues_found": [
                        {
                            "issue_id": "ISSUE-001",
                            "category": "API Design",
                            "severity": "High",
                            "description": "POST /products returns 200 instead of 201 Created for resource creation",
                            "evidence": "success_codes contains 200, should be 201 for POST creating resource",
                            "impact": "Non-RESTful API, confusing for clients expecting 201 for newly created resources",
                            "affected_phase": "Design",
                        }
                    ],
                    "improvement_suggestions": [
                        {
                            "suggestion_id": "IMPROVE-001",
                            "related_issue_id": "ISSUE-001",
                            "category": "API Design",
                            "priority": "High",
                            "description": "Return 201 Created status code with Location header for POST /products",
                            "implementation_notes": "Change success_codes to [201], include Location header with URL of created resource",
                        }
                    ],
                }
            )
        }

        result = agent.execute(design_spec)

        assert len(result["issues_found"]) >= 1
        issue = result["issues_found"][0]
        assert (
            "status" in issue["description"].lower()
            or "201" in issue["description"]
            or "200" in issue["description"]
        )

    @patch.object(APIDesignReviewAgent, "load_prompt")
    @patch.object(APIDesignReviewAgent, "format_prompt")
    @patch.object(APIDesignReviewAgent, "call_llm")
    def test_detect_non_restful_naming(
        self, mock_call_llm, mock_format_prompt, mock_load_prompt, agent
    ):
        """Test detection of non-RESTful endpoint naming."""
        design_spec = DesignSpecification(
            task_id="API-NAMING-001",
            component_logic=[
                ComponentLogic(
                    component_name="UserAPI",
                    semantic_unit_id="SU-001",
                    responsibility="User operations",
                    interfaces=[{"method": "get_user"}],
                    implementation_notes="API endpoint implementations",
                )
            ],
            api_contracts=[
                APIContract(
                    endpoint="/getUserById",
                    method="GET",
                    description="Get user by ID using verb in endpoint name",
                    request_schema={"id": "string"},
                    response_schema={"user": "object"},
                    success_codes=[200],
                    error_codes=[404],
                    semantic_unit_ids=["SU-001"],
                )
            ],
            design_review_checklist=[
                DesignReviewChecklistItem(
                    checklist_item_id="CHECK-001",
                    category="API Design",
                    severity="High",
                    description="Endpoint names must use nouns not verbs",
                    validation_criteria="RESTful resource naming conventions",
                ),
                DesignReviewChecklistItem(
                    checklist_item_id="CHECK-002",
                    category="API Design",
                    severity="High",
                    description="Additional checklist item for comprehensive review coverage",
                    validation_criteria="Validation criteria for completeness",
                ),
                DesignReviewChecklistItem(
                    checklist_item_id="CHECK-003",
                    category="API Design",
                    severity="Medium",
                    description="Additional checklist item for thorough evaluation",
                    validation_criteria="Validation criteria for quality",
                ),
                DesignReviewChecklistItem(
                    checklist_item_id="CHECK-004",
                    category="API Design",
                    severity="Medium",
                    description="Additional checklist item for detailed assessment",
                    validation_criteria="Validation criteria for standards",
                ),
                DesignReviewChecklistItem(
                    checklist_item_id="CHECK-005",
                    category="API Design",
                    severity="Low",
                    description="Additional checklist item for complete verification",
                    validation_criteria="Validation criteria for best practices",
                ),
            ],
            architecture_overview="API with non-RESTful endpoint naming using verbs instead of resource nouns",
            technology_stack={"framework": "FastAPI"},
        )

        mock_load_prompt.return_value = "API design review template"
        mock_format_prompt.return_value = "Formatted prompt"
        mock_call_llm.return_value = {
            "content": json.dumps(
                {
                    "issues_found": [
                        {
                            "issue_id": "ISSUE-001",
                            "category": "API Design",
                            "severity": "High",
                            "description": "Endpoint /getUserById uses verb instead of RESTful resource naming",
                            "evidence": "Endpoint contains 'get' verb and camelCase, not RESTful noun pattern",
                            "impact": "API is not intuitive, violates REST conventions, difficult to discover",
                            "affected_phase": "Design",
                        }
                    ],
                    "improvement_suggestions": [
                        {
                            "suggestion_id": "IMPROVE-001",
                            "related_issue_id": "ISSUE-001",
                            "category": "API Design",
                            "priority": "High",
                            "description": "Rename endpoint to /users/{id} following RESTful conventions",
                            "implementation_notes": "Use plural noun 'users', path parameter {id}, HTTP GET method implies retrieval",
                        }
                    ],
                }
            )
        }

        result = agent.execute(design_spec)

        assert len(result["issues_found"]) >= 1
        issue = result["issues_found"][0]
        assert (
            "restful" in issue["description"].lower()
            or "naming" in issue["description"].lower()
            or "verb" in issue["description"].lower()
        )

    @patch.object(APIDesignReviewAgent, "load_prompt")
    @patch.object(APIDesignReviewAgent, "format_prompt")
    @patch.object(APIDesignReviewAgent, "call_llm")
    def test_detect_missing_error_codes(
        self, mock_call_llm, mock_format_prompt, mock_load_prompt, agent
    ):
        """Test detection of missing appropriate error status codes."""
        design_spec = DesignSpecification(
            task_id="API-ERROR-001",
            component_logic=[
                ComponentLogic(
                    component_name="OrderAPI",
                    semantic_unit_id="SU-001",
                    responsibility="Order creation with validation",
                    interfaces=[{"method": "create_order"}],
                    implementation_notes="Validate order before creation",
                )
            ],
            api_contracts=[
                APIContract(
                    endpoint="/orders",
                    method="POST",
                    description="Create order with validation, only returns 201 and 500",
                    request_schema={"product_id": "string", "quantity": "number"},
                    response_schema={"order": "object"},
                    success_codes=[201],
                    error_codes=[500],
                    semantic_unit_ids=["SU-001"],
                )
            ],
            design_review_checklist=[
                DesignReviewChecklistItem(
                    checklist_item_id="CHECK-001",
                    category="API Design",
                    severity="High",
                    description="Include 400 Bad Request for validation errors",
                    validation_criteria="400 status code for client input errors",
                ),
                DesignReviewChecklistItem(
                    checklist_item_id="CHECK-002",
                    category="API Design",
                    severity="High",
                    description="Additional checklist item for comprehensive review coverage",
                    validation_criteria="Validation criteria for completeness",
                ),
                DesignReviewChecklistItem(
                    checklist_item_id="CHECK-003",
                    category="API Design",
                    severity="Medium",
                    description="Additional checklist item for thorough evaluation",
                    validation_criteria="Validation criteria for quality",
                ),
                DesignReviewChecklistItem(
                    checklist_item_id="CHECK-004",
                    category="API Design",
                    severity="Medium",
                    description="Additional checklist item for detailed assessment",
                    validation_criteria="Validation criteria for standards",
                ),
                DesignReviewChecklistItem(
                    checklist_item_id="CHECK-005",
                    category="API Design",
                    severity="Low",
                    description="Additional checklist item for complete verification",
                    validation_criteria="Validation criteria for best practices",
                ),
            ],
            architecture_overview="Order API missing 400 status code for validation errors",
            technology_stack={"framework": "FastAPI"},
        )

        mock_load_prompt.return_value = "API design review template"
        mock_format_prompt.return_value = "Formatted prompt"
        mock_call_llm.return_value = {
            "content": json.dumps(
                {
                    "issues_found": [
                        {
                            "issue_id": "ISSUE-001",
                            "category": "API Design",
                            "severity": "High",
                            "description": "POST /orders missing 400 Bad Request for validation errors",
                            "evidence": "error_codes only includes 500, no 400 for client validation failures",
                            "impact": "Cannot distinguish server errors from client input errors, poor error handling",
                            "affected_phase": "Design",
                        }
                    ],
                    "improvement_suggestions": [
                        {
                            "suggestion_id": "IMPROVE-001",
                            "related_issue_id": "ISSUE-001",
                            "category": "API Design",
                            "priority": "High",
                            "description": "Add 400 status code for validation errors on POST /orders",
                            "implementation_notes": "Add 400 to error_codes, return 400 with validation error details when input is invalid",
                        }
                    ],
                }
            )
        }

        result = agent.execute(design_spec)

        assert len(result["issues_found"]) >= 1
        issue = result["issues_found"][0]
        assert (
            "400" in issue["description"]
            or "validation" in issue["description"].lower()
        )

    @patch.object(APIDesignReviewAgent, "load_prompt")
    @patch.object(APIDesignReviewAgent, "format_prompt")
    @patch.object(APIDesignReviewAgent, "call_llm")
    def test_detect_missing_api_versioning(
        self, mock_call_llm, mock_format_prompt, mock_load_prompt, agent
    ):
        """Test detection of missing API versioning strategy."""
        design_spec = DesignSpecification(
            task_id="API-VERSION-001",
            component_logic=[
                ComponentLogic(
                    component_name="PublicAPI",
                    semantic_unit_id="SU-001",
                    responsibility="Public API endpoints without versioning",
                    interfaces=[{"method": "list_items"}],
                    implementation_notes="API endpoints for external clients",
                )
            ],
            api_contracts=[
                APIContract(
                    endpoint="/items",
                    method="GET",
                    description="List items endpoint without version in path or headers",
                    request_schema={},
                    response_schema={"items": "array"},
                    success_codes=[200],
                    error_codes=[],
                    semantic_unit_ids=["SU-001"],
                )
            ],
            design_review_checklist=[
                DesignReviewChecklistItem(
                    checklist_item_id="CHECK-001",
                    category="API Design",
                    severity="High",
                    description="Public APIs must include versioning",
                    validation_criteria="Version in URL path or Accept header",
                ),
                DesignReviewChecklistItem(
                    checklist_item_id="CHECK-002",
                    category="API Design",
                    severity="High",
                    description="Additional checklist item for comprehensive review coverage",
                    validation_criteria="Validation criteria for completeness",
                ),
                DesignReviewChecklistItem(
                    checklist_item_id="CHECK-003",
                    category="API Design",
                    severity="Medium",
                    description="Additional checklist item for thorough evaluation",
                    validation_criteria="Validation criteria for quality",
                ),
                DesignReviewChecklistItem(
                    checklist_item_id="CHECK-004",
                    category="API Design",
                    severity="Medium",
                    description="Additional checklist item for detailed assessment",
                    validation_criteria="Validation criteria for standards",
                ),
                DesignReviewChecklistItem(
                    checklist_item_id="CHECK-005",
                    category="API Design",
                    severity="Low",
                    description="Additional checklist item for complete verification",
                    validation_criteria="Validation criteria for best practices",
                ),
            ],
            architecture_overview="Public API without versioning strategy making breaking changes difficult",
            technology_stack={"framework": "FastAPI"},
        )

        mock_load_prompt.return_value = "API design review template"
        mock_format_prompt.return_value = "Formatted prompt"
        mock_call_llm.return_value = {
            "content": json.dumps(
                {
                    "issues_found": [
                        {
                            "issue_id": "ISSUE-001",
                            "category": "API Design",
                            "severity": "High",
                            "description": "Public API endpoint /items missing version identifier",
                            "evidence": "No /v1/ or version parameter in endpoint path",
                            "impact": "Cannot make breaking changes without disrupting existing clients",
                            "affected_phase": "Design",
                        }
                    ],
                    "improvement_suggestions": [
                        {
                            "suggestion_id": "IMPROVE-001",
                            "related_issue_id": "ISSUE-001",
                            "category": "API Design",
                            "priority": "High",
                            "description": "Add version prefix to API endpoints for versioning strategy",
                            "implementation_notes": "Change endpoint to /v1/items, document versioning strategy in API documentation",
                        }
                    ],
                }
            )
        }

        result = agent.execute(design_spec)

        assert len(result["issues_found"]) >= 1
        issue = result["issues_found"][0]
        assert "version" in issue["description"].lower()


class TestAPIDesignReviewAgentErrorHandling:
    """Test API Design Review Agent error handling."""

    @pytest.fixture
    def agent(self):
        """Create API Design Review Agent instance."""
        return APIDesignReviewAgent(db_path=":memory:")

    @pytest.fixture
    def design_spec(self):
        """Create minimal design specification."""
        return DesignSpecification(
            task_id="ERROR-TEST-001",
            component_logic=[
                ComponentLogic(
                    component_name="TestComponent",
                    semantic_unit_id="SU-001",
                    responsibility="Test component for error handling",
                    interfaces=[{"method": "test"}],
                    implementation_notes="Test implementation for unit tests",
                )
            ],
            design_review_checklist=[
                DesignReviewChecklistItem(
                    checklist_item_id="CHECK-001",
                    category="API Design",
                    severity="Critical",
                    description="Test checklist item for validation purposes",
                    validation_criteria="Test validation criteria applied",
                ),
                DesignReviewChecklistItem(
                    checklist_item_id="CHECK-002",
                    category="API Design",
                    severity="High",
                    description="Test checklist item for comprehensive testing",
                    validation_criteria="Test validation criteria checked",
                ),
                DesignReviewChecklistItem(
                    checklist_item_id="CHECK-003",
                    category="API Design",
                    severity="Medium",
                    description="Test checklist item for medium severity cases",
                    validation_criteria="Test validation criteria validated",
                ),
                DesignReviewChecklistItem(
                    checklist_item_id="CHECK-004",
                    category="API Design",
                    severity="Medium",
                    description="Test checklist item for additional test coverage",
                    validation_criteria="Test validation criteria confirmed",
                ),
                DesignReviewChecklistItem(
                    checklist_item_id="CHECK-005",
                    category="API Design",
                    severity="Low",
                    description="Test checklist item for low severity verification",
                    validation_criteria="Test validation criteria ensured",
                ),
            ],
            architecture_overview="Test architecture overview for error handling test scenarios",
            technology_stack={"language": "Python"},
        )

    @patch.object(APIDesignReviewAgent, "load_prompt")
    @patch.object(APIDesignReviewAgent, "format_prompt")
    @patch.object(APIDesignReviewAgent, "call_llm")
    def test_execute_raises_error_on_invalid_json_response(
        self, mock_call_llm, mock_format_prompt, mock_load_prompt, agent, design_spec
    ):
        """Test execute raises error when LLM returns invalid JSON."""
        mock_load_prompt.return_value = "API design review prompt template"
        mock_format_prompt.return_value = "Formatted prompt"
        mock_call_llm.return_value = {"content": "Invalid JSON {{{"}

        with pytest.raises(AgentExecutionError) as exc_info:
            agent.execute(design_spec)

        assert "API design review failed" in str(exc_info.value)

    @patch.object(APIDesignReviewAgent, "load_prompt")
    @patch.object(APIDesignReviewAgent, "format_prompt")
    @patch.object(APIDesignReviewAgent, "call_llm")
    def test_execute_raises_error_on_missing_required_fields(
        self, mock_call_llm, mock_format_prompt, mock_load_prompt, agent, design_spec
    ):
        """Test execute raises error when response missing required fields."""
        mock_load_prompt.return_value = "API design review prompt template"
        mock_format_prompt.return_value = "Formatted prompt"
        mock_call_llm.return_value = {"content": json.dumps({"issues_found": []})}

        with pytest.raises(AgentExecutionError) as exc_info:
            agent.execute(design_spec)

        assert "Response missing required fields" in str(exc_info.value)

    @patch.object(APIDesignReviewAgent, "load_prompt")
    @patch.object(APIDesignReviewAgent, "format_prompt")
    @patch.object(APIDesignReviewAgent, "call_llm")
    def test_execute_handles_llm_exceptions(
        self, mock_call_llm, mock_format_prompt, mock_load_prompt, agent, design_spec
    ):
        """Test execute handles exceptions from LLM calls."""
        mock_load_prompt.return_value = "API design review prompt template"
        mock_format_prompt.return_value = "Formatted prompt"
        mock_call_llm.side_effect = Exception("LLM connection failed")

        with pytest.raises(AgentExecutionError) as exc_info:
            agent.execute(design_spec)

        assert "API design review failed" in str(exc_info.value)


class TestAPIDesignReviewAgentEdgeCases:
    """Test API Design Review Agent edge cases."""

    @pytest.fixture
    def agent(self):
        """Create API Design Review Agent instance."""
        return APIDesignReviewAgent(db_path=":memory:")

    @patch.object(APIDesignReviewAgent, "load_prompt")
    @patch.object(APIDesignReviewAgent, "format_prompt")
    @patch.object(APIDesignReviewAgent, "call_llm")
    def test_execute_with_string_response_content(
        self, mock_call_llm, mock_format_prompt, mock_load_prompt, agent
    ):
        """Test execute handles string JSON response correctly."""
        design_spec = DesignSpecification(
            task_id="EDGE-001",
            component_logic=[
                ComponentLogic(
                    component_name="EdgeComponent",
                    semantic_unit_id="SU-001",
                    responsibility="Edge case testing component",
                    interfaces=[{"method": "test"}],
                    implementation_notes="Test implementation for unit tests",
                )
            ],
            design_review_checklist=[
                DesignReviewChecklistItem(
                    checklist_item_id="CHECK-001",
                    category="API Design",
                    severity="Critical",
                    description="Edge case checklist item for validation purposes",
                    validation_criteria="Edge case validation criteria applied",
                ),
                DesignReviewChecklistItem(
                    checklist_item_id="CHECK-002",
                    category="API Design",
                    severity="High",
                    description="Edge case checklist item for comprehensive testing",
                    validation_criteria="Edge case validation criteria checked",
                ),
                DesignReviewChecklistItem(
                    checklist_item_id="CHECK-003",
                    category="API Design",
                    severity="Medium",
                    description="Edge case checklist item for medium severity cases",
                    validation_criteria="Edge case validation criteria validated",
                ),
                DesignReviewChecklistItem(
                    checklist_item_id="CHECK-004",
                    category="API Design",
                    severity="Medium",
                    description="Edge case checklist item for additional test coverage",
                    validation_criteria="Edge case validation criteria confirmed",
                ),
                DesignReviewChecklistItem(
                    checklist_item_id="CHECK-005",
                    category="API Design",
                    severity="Low",
                    description="Edge case checklist item for low severity verification",
                    validation_criteria="Edge case validation criteria ensured",
                ),
            ],
            architecture_overview="Edge case architecture overview for testing string response handling",
            technology_stack={"language": "Python"},
        )

        mock_load_prompt.return_value = "API design review prompt template"
        mock_format_prompt.return_value = "Formatted prompt"
        mock_call_llm.return_value = {
            "content": '{"issues_found": [], "improvement_suggestions": []}'
        }

        result = agent.execute(design_spec)

        assert result["issues_found"] == []
        assert result["improvement_suggestions"] == []

    @patch.object(APIDesignReviewAgent, "load_prompt")
    @patch.object(APIDesignReviewAgent, "format_prompt")
    @patch.object(APIDesignReviewAgent, "call_llm")
    def test_execute_with_multiple_api_endpoints(
        self, mock_call_llm, mock_format_prompt, mock_load_prompt, agent
    ):
        """Test execute handles design with many API endpoints."""
        api_contracts = [
            APIContract(
                endpoint=f"/resources/{i}",
                method="GET",
                description=f"Get resource {i} from the API system",
                request_schema={"id": "string"},
                response_schema={"resource": "object"},
                success_codes=[200],
                error_codes=[404],
                semantic_unit_ids=["SU-001"],
            )
            for i in range(1, 6)
        ]

        design_spec = DesignSpecification(
            task_id="MULTI-API-001",
            component_logic=[
                ComponentLogic(
                    component_name="MultiResourceAPI",
                    semantic_unit_id="SU-001",
                    responsibility="Provide multiple resource API endpoints",
                    interfaces=[{"method": "get_resource"}],
                    implementation_notes="Multiple API endpoint implementation",
                )
            ],
            api_contracts=api_contracts,
            design_review_checklist=[
                DesignReviewChecklistItem(
                    checklist_item_id="CHECK-001",
                    category="API Design",
                    severity="Critical",
                    description="Large API checklist item",
                    validation_criteria="Large API validation",
                ),
                DesignReviewChecklistItem(
                    checklist_item_id="CHECK-002",
                    category="API Design",
                    severity="High",
                    description="Additional checklist item for comprehensive review coverage",
                    validation_criteria="Validation criteria for completeness",
                ),
                DesignReviewChecklistItem(
                    checklist_item_id="CHECK-003",
                    category="API Design",
                    severity="Medium",
                    description="Additional checklist item for thorough evaluation",
                    validation_criteria="Validation criteria for quality",
                ),
                DesignReviewChecklistItem(
                    checklist_item_id="CHECK-004",
                    category="API Design",
                    severity="Medium",
                    description="Additional checklist item for detailed assessment",
                    validation_criteria="Validation criteria for standards",
                ),
                DesignReviewChecklistItem(
                    checklist_item_id="CHECK-005",
                    category="API Design",
                    severity="Low",
                    description="Additional checklist item for complete verification",
                    validation_criteria="Validation criteria for best practices",
                ),
            ],
            architecture_overview="API with multiple endpoints for testing multi-endpoint handling",
            technology_stack={"framework": "FastAPI"},
        )

        mock_load_prompt.return_value = "API design review prompt template"
        mock_format_prompt.return_value = "Formatted prompt"
        mock_call_llm.return_value = {
            "content": json.dumps({"issues_found": [], "improvement_suggestions": []})
        }

        result = agent.execute(design_spec)

        assert "issues_found" in result
        assert "improvement_suggestions" in result
