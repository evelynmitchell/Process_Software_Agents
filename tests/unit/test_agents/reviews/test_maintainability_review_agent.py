"""
Unit tests for Maintainability Review Agent (FR-003).

Tests the specialist agent that reviews design specifications for maintainability:
- Coupling and cohesion
- Component boundaries and separation of concerns
- Error handling consistency
- Code organization and modularity
"""

import json
import logging
from unittest.mock import MagicMock, patch

import pytest

from asp.agents.base_agent import AgentExecutionError
from asp.agents.reviews.maintainability_review_agent import MaintainabilityReviewAgent
from asp.models.design import (
    ComponentLogic,
    DesignReviewChecklistItem,
    DesignSpecification,
)


class TestMaintainabilityReviewAgentInitialization:
    """Test Maintainability Review Agent initialization."""

    def test_initialization_with_defaults(self):
        """Test agent initializes with default values."""
        agent = MaintainabilityReviewAgent()

        assert agent.agent_version == "1.0.0"

    def test_initialization_with_custom_llm_client(self):
        """Test agent initializes with custom LLM client."""
        mock_client = MagicMock()
        agent = MaintainabilityReviewAgent(llm_client=mock_client)

        assert agent.agent_version == "1.0.0"

    def test_initialization_with_custom_db_path(self):
        """Test agent initializes with custom database path."""
        agent = MaintainabilityReviewAgent(db_path=":memory:")

        assert agent.agent_version == "1.0.0"


class TestMaintainabilityReviewAgentExecute:
    """Test Maintainability Review Agent execute method."""

    @pytest.fixture
    def agent(self):
        """Create Maintainability Review Agent instance."""
        return MaintainabilityReviewAgent(db_path=":memory:")

    @pytest.fixture
    def design_spec(self):
        """Create a sample design specification."""
        return DesignSpecification(
            task_id="MAINT-TEST-001",
            component_logic=[
                ComponentLogic(
                    component_name="UserService",
                    semantic_unit_id="SU-001",
                    responsibility="Handle user CRUD operations and authentication and authorization and logging",
                    interfaces=[
                        {"method": "create_user"},
                        {"method": "authenticate"},
                        {"method": "log_activity"},
                    ],
                    implementation_notes="Single component handles all user-related logic",
                )
            ],
            design_review_checklist=[
                DesignReviewChecklistItem(
                    checklist_item_id="CHECK-001",
                    category="Maintainability",
                    severity="Critical",
                    description="Components should have single, well-defined responsibility",
                    validation_criteria="Each component follows Single Responsibility Principle",
                ),
                DesignReviewChecklistItem(
                    checklist_item_id="CHECK-002",
                    category="Maintainability",
                    severity="High",
                    description="Minimize coupling between components",
                    validation_criteria="Components communicate through well-defined interfaces",
                ),
                DesignReviewChecklistItem(
                    checklist_item_id="CHECK-003",
                    category="Maintainability",
                    severity="Medium",
                    description="Error handling should be consistent across components",
                    validation_criteria="All components use same error handling patterns",
                ),
                DesignReviewChecklistItem(
                    checklist_item_id="CHECK-004",
                    category="Maintainability",
                    severity="Medium",
                    description="Avoid circular dependencies between components",
                    validation_criteria="Component dependency graph is acyclic",
                ),
                DesignReviewChecklistItem(
                    checklist_item_id="CHECK-005",
                    category="Maintainability",
                    severity="Low",
                    description="Use dependency injection for better testability",
                    validation_criteria="External dependencies injected via constructor",
                ),
            ],
            architecture_overview="Monolithic user management system with tightly coupled components",
            technology_stack={"language": "Python", "framework": "FastAPI"},
        )

    @patch.object(MaintainabilityReviewAgent, "load_prompt")
    @patch.object(MaintainabilityReviewAgent, "format_prompt")
    @patch.object(MaintainabilityReviewAgent, "call_llm")
    def test_execute_returns_valid_response(
        self, mock_call_llm, mock_format_prompt, mock_load_prompt, agent, design_spec
    ):
        """Test execute returns valid response with issues and suggestions."""
        mock_load_prompt.return_value = "Maintainability review prompt template"
        mock_format_prompt.return_value = "Formatted prompt with design spec"
        mock_call_llm.return_value = {
            "content": json.dumps(
                {
                    "issues_found": [
                        {
                            "issue_id": "ISSUE-001",
                            "category": "Maintainability",
                            "severity": "High",
                            "description": "UserService violates Single Responsibility Principle with mixed concerns",
                            "evidence": "UserService handles CRUD, authentication, authorization, and logging",
                            "impact": "Changes to any concern affect entire component, difficult to test",
                            "affected_phase": "Design",
                        }
                    ],
                    "improvement_suggestions": [
                        {
                            "suggestion_id": "IMPROVE-001",
                            "related_issue_id": "ISSUE-001",
                            "category": "Maintainability",
                            "priority": "High",
                            "description": "Split UserService into separate components by responsibility",
                            "implementation_notes": "Create UserRepository (CRUD), AuthService (authentication), AuthorizationService (permissions), AuditLogger (logging)",
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
        assert result["issues_found"][0]["category"] == "Maintainability"

    @patch.object(MaintainabilityReviewAgent, "load_prompt")
    @patch.object(MaintainabilityReviewAgent, "format_prompt")
    @patch.object(MaintainabilityReviewAgent, "call_llm")
    def test_execute_with_no_issues_found(
        self, mock_call_llm, mock_format_prompt, mock_load_prompt, agent, design_spec
    ):
        """Test execute with clean design (no issues)."""
        mock_load_prompt.return_value = "Maintainability review prompt template"
        mock_format_prompt.return_value = "Formatted prompt"
        mock_call_llm.return_value = {
            "content": json.dumps(
                {"issues_found": [], "improvement_suggestions": []}
            )
        }

        result = agent.execute(design_spec)

        assert result["issues_found"] == []
        assert result["improvement_suggestions"] == []

    @patch.object(MaintainabilityReviewAgent, "load_prompt")
    @patch.object(MaintainabilityReviewAgent, "format_prompt")
    @patch.object(MaintainabilityReviewAgent, "call_llm")
    def test_execute_logs_review_metrics(
        self, mock_call_llm, mock_format_prompt, mock_load_prompt, agent, design_spec, caplog
    ):
        """Test execute logs maintainability review metrics."""
        mock_load_prompt.return_value = "Maintainability review prompt template"
        mock_format_prompt.return_value = "Formatted prompt"
        mock_call_llm.return_value = {
            "content": json.dumps(
                {
                    "issues_found": [
                        {
                            "issue_id": "ISSUE-001",
                            "category": "Maintainability",
                            "severity": "High",
                            "description": "Component has too many responsibilities violating SRP",
                            "evidence": "UserService handles multiple unrelated concerns",
                            "impact": "Difficult to maintain, test, and modify component independently",
                            "affected_phase": "Design",
                        }
                    ],
                    "improvement_suggestions": [],
                }
            )
        }

        with caplog.at_level(logging.INFO):
            agent.execute(design_spec)

        assert "Starting maintainability review for task MAINT-TEST-001" in caplog.text
        assert "Maintainability review completed: 1 issues, 0 suggestions" in caplog.text


class TestMaintainabilityReviewAgentDetection:
    """Test Maintainability Review Agent detection capabilities."""

    @pytest.fixture
    def agent(self):
        """Create Maintainability Review Agent instance."""
        return MaintainabilityReviewAgent(db_path=":memory:")

    @patch.object(MaintainabilityReviewAgent, "load_prompt")
    @patch.object(MaintainabilityReviewAgent, "format_prompt")
    @patch.object(MaintainabilityReviewAgent, "call_llm")
    def test_detect_srp_violation(
        self, mock_call_llm, mock_format_prompt, mock_load_prompt, agent
    ):
        """Test detection of Single Responsibility Principle violation."""
        design_spec = DesignSpecification(
            task_id="MAINT-SRP-001",
            component_logic=[
                ComponentLogic(
                    component_name="OrderProcessor",
                    semantic_unit_id="SU-001",
                    responsibility="Process orders, send emails, update inventory, calculate taxes, generate reports",
                    interfaces=[
                        {"method": "process_order"},
                        {"method": "send_email"},
                        {"method": "update_inventory"},
                        {"method": "calculate_tax"},
                        {"method": "generate_report"},
                    ],
                    implementation_notes="Single component handles all order-related operations",
                )
            ],
            design_review_checklist=[
                DesignReviewChecklistItem(
                    checklist_item_id="CHECK-001",
                    category="Maintainability",
                    severity="Critical",
                    description="Components must follow Single Responsibility Principle",
                    validation_criteria="Each component has one reason to change",
                ),
                DesignReviewChecklistItem(
                    checklist_item_id="CHECK-002",
                    category="Maintainability",
                    severity="High",
                    description="Additional checklist item for comprehensive review coverage",
                    validation_criteria="Validation criteria for completeness",
                ),
                DesignReviewChecklistItem(
                    checklist_item_id="CHECK-003",
                    category="Maintainability",
                    severity="Medium",
                    description="Additional checklist item for thorough evaluation",
                    validation_criteria="Validation criteria for quality",
                ),
                DesignReviewChecklistItem(
                    checklist_item_id="CHECK-004",
                    category="Maintainability",
                    severity="Medium",
                    description="Additional checklist item for detailed assessment",
                    validation_criteria="Validation criteria for standards",
                ),
                DesignReviewChecklistItem(
                    checklist_item_id="CHECK-005",
                    category="Maintainability",
                    severity="Low",
                    description="Additional checklist item for complete verification",
                    validation_criteria="Validation criteria for best practices",
                ),
            ],
            architecture_overview="Order processing system with monolithic component handling multiple concerns",
            technology_stack={"language": "Python"},
        )

        mock_load_prompt.return_value = "Maintainability review template"
        mock_format_prompt.return_value = "Formatted prompt"
        mock_call_llm.return_value = {
            "content": json.dumps(
                {
                    "issues_found": [
                        {
                            "issue_id": "ISSUE-001",
                            "category": "Maintainability",
                            "severity": "Critical",
                            "description": "OrderProcessor violates SRP by handling 5 different responsibilities",
                            "evidence": "Component handles order processing, email sending, inventory management, tax calculation, and reporting",
                            "impact": "Any change to email format, tax rules, inventory logic, or reporting affects entire component",
                            "affected_phase": "Design",
                        }
                    ],
                    "improvement_suggestions": [
                        {
                            "suggestion_id": "IMPROVE-001",
                            "related_issue_id": "ISSUE-001",
                            "category": "Maintainability",
                            "priority": "High",
                            "description": "Split OrderProcessor into separate single-responsibility components",
                            "implementation_notes": "Create: OrderService (core logic), EmailService (notifications), InventoryService (stock), TaxCalculator (tax), ReportGenerator (reports)",
                        }
                    ],
                }
            )
        }

        result = agent.execute(design_spec)

        assert len(result["issues_found"]) >= 1
        issue = result["issues_found"][0]
        assert issue["severity"] in ["Critical", "High"]
        assert "responsibility" in issue["description"].lower() or "srp" in issue["description"].lower()

    @patch.object(MaintainabilityReviewAgent, "load_prompt")
    @patch.object(MaintainabilityReviewAgent, "format_prompt")
    @patch.object(MaintainabilityReviewAgent, "call_llm")
    def test_detect_tight_coupling(
        self, mock_call_llm, mock_format_prompt, mock_load_prompt, agent
    ):
        """Test detection of tight coupling between components."""
        design_spec = DesignSpecification(
            task_id="MAINT-COUPLING-001",
            component_logic=[
                ComponentLogic(
                    component_name="PaymentService",
                    semantic_unit_id="SU-001",
                    responsibility="Process payments by directly instantiating EmailService and InventoryService",
                    interfaces=[{"method": "process_payment"}],
                    implementation_notes="Directly creates EmailService() and InventoryService() instances internally",
                )
            ],
            design_review_checklist=[
                DesignReviewChecklistItem(
                    checklist_item_id="CHECK-001",
                    category="Maintainability",
                    severity="High",
                    description="Minimize coupling between components",
                    validation_criteria="Use dependency injection, avoid direct instantiation",
                ),
                DesignReviewChecklistItem(
                    checklist_item_id="CHECK-002",
                    category="Maintainability",
                    severity="High",
                    description="Additional checklist item for comprehensive review coverage",
                    validation_criteria="Validation criteria for completeness",
                ),
                DesignReviewChecklistItem(
                    checklist_item_id="CHECK-003",
                    category="Maintainability",
                    severity="Medium",
                    description="Additional checklist item for thorough evaluation",
                    validation_criteria="Validation criteria for quality",
                ),
                DesignReviewChecklistItem(
                    checklist_item_id="CHECK-004",
                    category="Maintainability",
                    severity="Medium",
                    description="Additional checklist item for detailed assessment",
                    validation_criteria="Validation criteria for standards",
                ),
                DesignReviewChecklistItem(
                    checklist_item_id="CHECK-005",
                    category="Maintainability",
                    severity="Low",
                    description="Additional checklist item for complete verification",
                    validation_criteria="Validation criteria for best practices",
                ),
            ],
            architecture_overview="Payment system with tightly coupled components and no dependency injection",
            technology_stack={"language": "Python"},
        )

        mock_load_prompt.return_value = "Maintainability review template"
        mock_format_prompt.return_value = "Formatted prompt"
        mock_call_llm.return_value = {
            "content": json.dumps(
                {
                    "issues_found": [
                        {
                            "issue_id": "ISSUE-001",
                            "category": "Maintainability",
                            "severity": "High",
                            "description": "PaymentService is tightly coupled to EmailService and InventoryService",
                            "evidence": "PaymentService directly instantiates dependencies internally",
                            "impact": "Difficult to test in isolation, changes to dependencies break PaymentService",
                            "affected_phase": "Design",
                        }
                    ],
                    "improvement_suggestions": [
                        {
                            "suggestion_id": "IMPROVE-001",
                            "related_issue_id": "ISSUE-001",
                            "category": "Maintainability",
                            "priority": "High",
                            "description": "Use dependency injection to decouple PaymentService from concrete implementations",
                            "implementation_notes": "Inject EmailService and InventoryService via constructor: __init__(self, email_service: EmailService, inventory_service: InventoryService)",
                        }
                    ],
                }
            )
        }

        result = agent.execute(design_spec)

        assert len(result["issues_found"]) >= 1
        issue = result["issues_found"][0]
        assert "coupl" in issue["description"].lower()

    @patch.object(MaintainabilityReviewAgent, "load_prompt")
    @patch.object(MaintainabilityReviewAgent, "format_prompt")
    @patch.object(MaintainabilityReviewAgent, "call_llm")
    def test_detect_inconsistent_error_handling(
        self, mock_call_llm, mock_format_prompt, mock_load_prompt, agent
    ):
        """Test detection of inconsistent error handling across components."""
        design_spec = DesignSpecification(
            task_id="MAINT-ERROR-001",
            component_logic=[
                ComponentLogic(
                    component_name="UserService",
                    semantic_unit_id="SU-001",
                    responsibility="Manage users, returns None on error",
                    interfaces=[{"method": "create_user"}],
                    implementation_notes="Returns None when user creation fails",
                ),
                ComponentLogic(
                    component_name="OrderService",
                    semantic_unit_id="SU-002",
                    responsibility="Manage orders, raises exceptions on error",
                    interfaces=[{"method": "create_order"}],
                    implementation_notes="Raises ValueError when order creation fails",
                ),
            ],
            design_review_checklist=[
                DesignReviewChecklistItem(
                    checklist_item_id="CHECK-001",
                    category="Maintainability",
                    severity="High",
                    description="Error handling must be consistent across components",
                    validation_criteria="All components use same error handling strategy",
                ),
                DesignReviewChecklistItem(
                    checklist_item_id="CHECK-002",
                    category="Maintainability",
                    severity="High",
                    description="Additional checklist item for comprehensive review coverage",
                    validation_criteria="Validation criteria for completeness",
                ),
                DesignReviewChecklistItem(
                    checklist_item_id="CHECK-003",
                    category="Maintainability",
                    severity="Medium",
                    description="Additional checklist item for thorough evaluation",
                    validation_criteria="Validation criteria for quality",
                ),
                DesignReviewChecklistItem(
                    checklist_item_id="CHECK-004",
                    category="Maintainability",
                    severity="Medium",
                    description="Additional checklist item for detailed assessment",
                    validation_criteria="Validation criteria for standards",
                ),
                DesignReviewChecklistItem(
                    checklist_item_id="CHECK-005",
                    category="Maintainability",
                    severity="Low",
                    description="Additional checklist item for complete verification",
                    validation_criteria="Validation criteria for best practices",
                ),
            ],
            architecture_overview="Application with inconsistent error handling patterns across different components",
            technology_stack={"language": "Python"},
        )

        mock_load_prompt.return_value = "Maintainability review template"
        mock_format_prompt.return_value = "Formatted prompt"
        mock_call_llm.return_value = {
            "content": json.dumps(
                {
                    "issues_found": [
                        {
                            "issue_id": "ISSUE-001",
                            "category": "Maintainability",
                            "severity": "High",
                            "description": "Inconsistent error handling: UserService returns None, OrderService raises exceptions",
                            "evidence": "UserService uses None returns, OrderService uses exception raising",
                            "impact": "Difficult to write consistent error handling code, error-prone for developers",
                            "affected_phase": "Design",
                        }
                    ],
                    "improvement_suggestions": [
                        {
                            "suggestion_id": "IMPROVE-001",
                            "related_issue_id": "ISSUE-001",
                            "category": "Maintainability",
                            "priority": "High",
                            "description": "Standardize error handling to use exceptions across all services",
                            "implementation_notes": "Define custom exception hierarchy (UserNotFoundError, OrderCreationError), raise exceptions consistently",
                        }
                    ],
                }
            )
        }

        result = agent.execute(design_spec)

        assert len(result["issues_found"]) >= 1
        issue = result["issues_found"][0]
        assert "error" in issue["description"].lower() or "exception" in issue["description"].lower()

    @patch.object(MaintainabilityReviewAgent, "load_prompt")
    @patch.object(MaintainabilityReviewAgent, "format_prompt")
    @patch.object(MaintainabilityReviewAgent, "call_llm")
    def test_detect_circular_dependencies(
        self, mock_call_llm, mock_format_prompt, mock_load_prompt, agent
    ):
        """Test detection of circular dependencies between components."""
        design_spec = DesignSpecification(
            task_id="MAINT-CIRC-001",
            component_logic=[
                ComponentLogic(
                    component_name="ServiceA",
                    semantic_unit_id="SU-001",
                    responsibility="Handles A operations and depends on ServiceB",
                    interfaces=[{"method": "do_a"}],
                    implementation_notes="Calls ServiceB.do_b() internally",
                ),
                ComponentLogic(
                    component_name="ServiceB",
                    semantic_unit_id="SU-002",
                    responsibility="Handles B operations and depends on ServiceA",
                    interfaces=[{"method": "do_b"}],
                    implementation_notes="Calls ServiceA.do_a() internally, creating circular dependency",
                ),
            ],
            design_review_checklist=[
                DesignReviewChecklistItem(
                    checklist_item_id="CHECK-001",
                    category="Maintainability",
                    severity="Critical",
                    description="Must not have circular dependencies between components",
                    validation_criteria="Component dependency graph must be acyclic (DAG)",
                ),
                DesignReviewChecklistItem(
                    checklist_item_id="CHECK-002",
                    category="Maintainability",
                    severity="High",
                    description="Additional checklist item for comprehensive review coverage",
                    validation_criteria="Validation criteria for completeness",
                ),
                DesignReviewChecklistItem(
                    checklist_item_id="CHECK-003",
                    category="Maintainability",
                    severity="Medium",
                    description="Additional checklist item for thorough evaluation",
                    validation_criteria="Validation criteria for quality",
                ),
                DesignReviewChecklistItem(
                    checklist_item_id="CHECK-004",
                    category="Maintainability",
                    severity="Medium",
                    description="Additional checklist item for detailed assessment",
                    validation_criteria="Validation criteria for standards",
                ),
                DesignReviewChecklistItem(
                    checklist_item_id="CHECK-005",
                    category="Maintainability",
                    severity="Low",
                    description="Additional checklist item for complete verification",
                    validation_criteria="Validation criteria for best practices",
                ),
            ],
            architecture_overview="System with circular dependencies between ServiceA and ServiceB creating tight coupling",
            technology_stack={"language": "Python"},
        )

        mock_load_prompt.return_value = "Maintainability review template"
        mock_format_prompt.return_value = "Formatted prompt"
        mock_call_llm.return_value = {
            "content": json.dumps(
                {
                    "issues_found": [
                        {
                            "issue_id": "ISSUE-001",
                            "category": "Maintainability",
                            "severity": "Critical",
                            "description": "Circular dependency detected between ServiceA and ServiceB",
                            "evidence": "ServiceA depends on ServiceB which depends on ServiceA",
                            "impact": "Impossible to test components in isolation, difficult to understand and modify",
                            "affected_phase": "Design",
                        }
                    ],
                    "improvement_suggestions": [
                        {
                            "suggestion_id": "IMPROVE-001",
                            "related_issue_id": "ISSUE-001",
                            "category": "Maintainability",
                            "priority": "High",
                            "description": "Break circular dependency by extracting shared logic to new component",
                            "implementation_notes": "Create SharedService with common functionality, have ServiceA and ServiceB both depend on SharedService",
                        }
                    ],
                }
            )
        }

        result = agent.execute(design_spec)

        assert len(result["issues_found"]) >= 1
        issue = result["issues_found"][0]
        assert issue["severity"] in ["Critical", "High"]


class TestMaintainabilityReviewAgentErrorHandling:
    """Test Maintainability Review Agent error handling."""

    @pytest.fixture
    def agent(self):
        """Create Maintainability Review Agent instance."""
        return MaintainabilityReviewAgent(db_path=":memory:")

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
                    category="Maintainability",
                    severity="Critical",
                    description="Test checklist item for validation purposes",
                    validation_criteria="Test validation criteria applied",
                ),
                DesignReviewChecklistItem(
                    checklist_item_id="CHECK-002",
                    category="Maintainability",
                    severity="High",
                    description="Test checklist item for comprehensive testing",
                    validation_criteria="Test validation criteria checked",
                ),
                DesignReviewChecklistItem(
                    checklist_item_id="CHECK-003",
                    category="Maintainability",
                    severity="Medium",
                    description="Test checklist item for medium severity cases",
                    validation_criteria="Test validation criteria validated",
                ),
                DesignReviewChecklistItem(
                    checklist_item_id="CHECK-004",
                    category="Maintainability",
                    severity="Medium",
                    description="Test checklist item for additional test coverage",
                    validation_criteria="Test validation criteria confirmed",
                ),
                DesignReviewChecklistItem(
                    checklist_item_id="CHECK-005",
                    category="Maintainability",
                    severity="Low",
                    description="Test checklist item for low severity verification",
                    validation_criteria="Test validation criteria ensured",
                ),
            ],
            architecture_overview="Test architecture overview for error handling test scenarios",
            technology_stack={"language": "Python"},
        )

    @patch.object(MaintainabilityReviewAgent, "load_prompt")
    @patch.object(MaintainabilityReviewAgent, "format_prompt")
    @patch.object(MaintainabilityReviewAgent, "call_llm")
    def test_execute_raises_error_on_invalid_json_response(
        self, mock_call_llm, mock_format_prompt, mock_load_prompt, agent, design_spec
    ):
        """Test execute raises error when LLM returns invalid JSON."""
        mock_load_prompt.return_value = "Maintainability review prompt template"
        mock_format_prompt.return_value = "Formatted prompt"
        mock_call_llm.return_value = {"content": "Invalid JSON {{{"}

        with pytest.raises(AgentExecutionError) as exc_info:
            agent.execute(design_spec)

        assert "Maintainability review failed" in str(exc_info.value)

    @patch.object(MaintainabilityReviewAgent, "load_prompt")
    @patch.object(MaintainabilityReviewAgent, "format_prompt")
    @patch.object(MaintainabilityReviewAgent, "call_llm")
    def test_execute_raises_error_on_missing_required_fields(
        self, mock_call_llm, mock_format_prompt, mock_load_prompt, agent, design_spec
    ):
        """Test execute raises error when response missing required fields."""
        mock_load_prompt.return_value = "Maintainability review prompt template"
        mock_format_prompt.return_value = "Formatted prompt"
        mock_call_llm.return_value = {"content": json.dumps({"issues_found": []})}

        with pytest.raises(AgentExecutionError) as exc_info:
            agent.execute(design_spec)

        assert "Response missing required fields" in str(exc_info.value)

    @patch.object(MaintainabilityReviewAgent, "load_prompt")
    @patch.object(MaintainabilityReviewAgent, "format_prompt")
    @patch.object(MaintainabilityReviewAgent, "call_llm")
    def test_execute_handles_llm_exceptions(
        self, mock_call_llm, mock_format_prompt, mock_load_prompt, agent, design_spec
    ):
        """Test execute handles exceptions from LLM calls."""
        mock_load_prompt.return_value = "Maintainability review prompt template"
        mock_format_prompt.return_value = "Formatted prompt"
        mock_call_llm.side_effect = Exception("LLM connection failed")

        with pytest.raises(AgentExecutionError) as exc_info:
            agent.execute(design_spec)

        assert "Maintainability review failed" in str(exc_info.value)


class TestMaintainabilityReviewAgentEdgeCases:
    """Test Maintainability Review Agent edge cases."""

    @pytest.fixture
    def agent(self):
        """Create Maintainability Review Agent instance."""
        return MaintainabilityReviewAgent(db_path=":memory:")

    @patch.object(MaintainabilityReviewAgent, "load_prompt")
    @patch.object(MaintainabilityReviewAgent, "format_prompt")
    @patch.object(MaintainabilityReviewAgent, "call_llm")
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
                    category="Maintainability",
                    severity="Critical",
                    description="Edge case checklist item for validation purposes",
                    validation_criteria="Edge case validation criteria applied",
                ),
                DesignReviewChecklistItem(
                    checklist_item_id="CHECK-002",
                    category="Maintainability",
                    severity="High",
                    description="Edge case checklist item for comprehensive testing",
                    validation_criteria="Edge case validation criteria checked",
                ),
                DesignReviewChecklistItem(
                    checklist_item_id="CHECK-003",
                    category="Maintainability",
                    severity="Medium",
                    description="Edge case checklist item for medium severity cases",
                    validation_criteria="Edge case validation criteria validated",
                ),
                DesignReviewChecklistItem(
                    checklist_item_id="CHECK-004",
                    category="Maintainability",
                    severity="Medium",
                    description="Edge case checklist item for additional test coverage",
                    validation_criteria="Edge case validation criteria confirmed",
                ),
                DesignReviewChecklistItem(
                    checklist_item_id="CHECK-005",
                    category="Maintainability",
                    severity="Low",
                    description="Edge case checklist item for low severity verification",
                    validation_criteria="Edge case validation criteria ensured",
                ),
            ],
            architecture_overview="Edge case architecture overview for testing string response handling",
            technology_stack={"language": "Python"},
        )

        mock_load_prompt.return_value = "Maintainability review prompt template"
        mock_format_prompt.return_value = "Formatted prompt"
        mock_call_llm.return_value = {
            "content": '{"issues_found": [], "improvement_suggestions": []}'
        }

        result = agent.execute(design_spec)

        assert result["issues_found"] == []
        assert result["improvement_suggestions"] == []

    @patch.object(MaintainabilityReviewAgent, "load_prompt")
    @patch.object(MaintainabilityReviewAgent, "format_prompt")
    @patch.object(MaintainabilityReviewAgent, "call_llm")
    def test_execute_with_multiple_component_design(
        self, mock_call_llm, mock_format_prompt, mock_load_prompt, agent
    ):
        """Test execute handles design with many components."""
        components = [
            ComponentLogic(
                component_name=f"Component{i}",
                semantic_unit_id=f"SU-{i:03d}",
                responsibility=f"Handles specific responsibility for component number {i}",
                interfaces=[{"method": f"do_operation_{i}"}],
                implementation_notes=f"Implementation notes for component number {i}",
            )
            for i in range(1, 11)
        ]

        design_spec = DesignSpecification(
            task_id="MULTI-001",
            component_logic=components,
            design_review_checklist=[
                DesignReviewChecklistItem(
                    checklist_item_id="CHECK-001",
                    category="Maintainability",
                    severity="Critical",
                    description="Large system checklist item",
                    validation_criteria="Large system validation",
                ),
                DesignReviewChecklistItem(
                    checklist_item_id="CHECK-002",
                    category="Maintainability",
                    severity="High",
                    description="Additional checklist item for comprehensive review coverage",
                    validation_criteria="Validation criteria for completeness",
                ),
                DesignReviewChecklistItem(
                    checklist_item_id="CHECK-003",
                    category="Maintainability",
                    severity="Medium",
                    description="Additional checklist item for thorough evaluation",
                    validation_criteria="Validation criteria for quality",
                ),
                DesignReviewChecklistItem(
                    checklist_item_id="CHECK-004",
                    category="Maintainability",
                    severity="Medium",
                    description="Additional checklist item for detailed assessment",
                    validation_criteria="Validation criteria for standards",
                ),
                DesignReviewChecklistItem(
                    checklist_item_id="CHECK-005",
                    category="Maintainability",
                    severity="Low",
                    description="Additional checklist item for complete verification",
                    validation_criteria="Validation criteria for best practices",
                ),
            ],
            architecture_overview="Large system with many components for testing multi-component handling",
            technology_stack={"language": "Python"},
        )

        mock_load_prompt.return_value = "Maintainability review prompt template"
        mock_format_prompt.return_value = "Formatted prompt"
        mock_call_llm.return_value = {
            "content": json.dumps(
                {"issues_found": [], "improvement_suggestions": []}
            )
        }

        result = agent.execute(design_spec)

        assert "issues_found" in result
        assert "improvement_suggestions" in result
