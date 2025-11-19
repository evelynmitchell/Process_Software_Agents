"""
Unit tests for Architecture Review Agent (FR-003).

Tests the specialist agent that reviews design specifications for architecture:
- Design patterns and best practices
- Separation of concerns
- Testability and dependency injection
- Extensibility and flexibility
"""

import json
import logging
from unittest.mock import MagicMock, patch

import pytest

from asp.agents.base_agent import AgentExecutionError
from asp.agents.reviews.architecture_review_agent import ArchitectureReviewAgent
from asp.models.design import (
    ComponentLogic,
    DesignReviewChecklistItem,
    DesignSpecification,
)


class TestArchitectureReviewAgentInitialization:
    """Test Architecture Review Agent initialization."""

    def test_initialization_with_defaults(self):
        """Test agent initializes with default values."""
        agent = ArchitectureReviewAgent()

        assert agent.agent_version == "1.0.0"

    def test_initialization_with_custom_llm_client(self):
        """Test agent initializes with custom LLM client."""
        mock_client = MagicMock()
        agent = ArchitectureReviewAgent(llm_client=mock_client)

        assert agent.agent_version == "1.0.0"

    def test_initialization_with_custom_db_path(self):
        """Test agent initializes with custom database path."""
        agent = ArchitectureReviewAgent(db_path=":memory:")

        assert agent.agent_version == "1.0.0"


class TestArchitectureReviewAgentExecute:
    """Test Architecture Review Agent execute method."""

    @pytest.fixture
    def agent(self):
        """Create Architecture Review Agent instance."""
        return ArchitectureReviewAgent(db_path=":memory:")

    @pytest.fixture
    def design_spec(self):
        """Create a sample design specification."""
        return DesignSpecification(
            task_id="ARCH-TEST-001",
            component_logic=[
                ComponentLogic(
                    component_name="DataProcessor",
                    semantic_unit_id="SU-001",
                    responsibility="Process data with hardcoded configuration and direct file system access",
                    interfaces=[{"method": "process"}],
                    implementation_notes="Hardcode file paths and configuration values inside component",
                )
            ],
            design_review_checklist=[
                DesignReviewChecklistItem(
                    checklist_item_id="CHECK-001",
                    category="Architecture",
                    severity="Critical",
                    description="Components must be testable with dependency injection",
                    validation_criteria="External dependencies injected via constructor",
                ),
                DesignReviewChecklistItem(
                    checklist_item_id="CHECK-002",
                    category="Architecture",
                    severity="High",
                    description="Use appropriate design patterns for common problems",
                    validation_criteria="Factory, Strategy, Observer patterns where applicable",
                ),
                DesignReviewChecklistItem(
                    checklist_item_id="CHECK-003",
                    category="Architecture",
                    severity="High",
                    description="Separate business logic from infrastructure concerns",
                    validation_criteria="Clean separation between domain and infrastructure layers",
                ),
                DesignReviewChecklistItem(
                    checklist_item_id="CHECK-004",
                    category="Architecture",
                    severity="Medium",
                    description="Design for extensibility without modification",
                    validation_criteria="Open/Closed Principle - extend via interfaces",
                ),
                DesignReviewChecklistItem(
                    checklist_item_id="CHECK-005",
                    category="Architecture",
                    severity="Low",
                    description="Document architectural decisions and trade-offs",
                    validation_criteria="ADRs or design documentation explaining key decisions",
                ),
            ],
            architecture_overview="Monolithic data processing system with hardcoded dependencies and minimal abstraction",
            technology_stack={"language": "Python", "framework": "Flask"},
        )

    @patch.object(ArchitectureReviewAgent, "load_prompt")
    @patch.object(ArchitectureReviewAgent, "format_prompt")
    @patch.object(ArchitectureReviewAgent, "call_llm")
    def test_execute_returns_valid_response(
        self, mock_call_llm, mock_format_prompt, mock_load_prompt, agent, design_spec
    ):
        """Test execute returns valid response with issues and suggestions."""
        mock_load_prompt.return_value = "Architecture review prompt template"
        mock_format_prompt.return_value = "Formatted prompt with design spec"
        mock_call_llm.return_value = {
            "content": json.dumps(
                {
                    "issues_found": [
                        {
                            "issue_id": "ISSUE-001",
                            "category": "Architecture",
                            "severity": "High",
                            "description": "DataProcessor has hardcoded dependencies preventing testability",
                            "evidence": "Component hardcodes file paths and configuration values",
                            "impact": "Impossible to unit test without file system, difficult to change configuration",
                            "affected_phase": "Design",
                        }
                    ],
                    "improvement_suggestions": [
                        {
                            "suggestion_id": "IMPROVE-001",
                            "related_issue_id": "ISSUE-001",
                            "category": "Architecture",
                            "priority": "High",
                            "description": "Use dependency injection for file system and configuration access",
                            "implementation_notes": "Inject FileSystemService and ConfigService via constructor, allowing mock injection in tests",
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
        assert result["issues_found"][0]["category"] == "Architecture"

    @patch.object(ArchitectureReviewAgent, "load_prompt")
    @patch.object(ArchitectureReviewAgent, "format_prompt")
    @patch.object(ArchitectureReviewAgent, "call_llm")
    def test_execute_with_no_issues_found(
        self, mock_call_llm, mock_format_prompt, mock_load_prompt, agent, design_spec
    ):
        """Test execute with clean design (no issues)."""
        mock_load_prompt.return_value = "Architecture review prompt template"
        mock_format_prompt.return_value = "Formatted prompt"
        mock_call_llm.return_value = {
            "content": json.dumps(
                {"issues_found": [], "improvement_suggestions": []}
            )
        }

        result = agent.execute(design_spec)

        assert result["issues_found"] == []
        assert result["improvement_suggestions"] == []

    @patch.object(ArchitectureReviewAgent, "load_prompt")
    @patch.object(ArchitectureReviewAgent, "format_prompt")
    @patch.object(ArchitectureReviewAgent, "call_llm")
    def test_execute_logs_review_metrics(
        self, mock_call_llm, mock_format_prompt, mock_load_prompt, agent, design_spec, caplog
    ):
        """Test execute logs architecture review metrics."""
        mock_load_prompt.return_value = "Architecture review prompt template"
        mock_format_prompt.return_value = "Formatted prompt"
        mock_call_llm.return_value = {
            "content": json.dumps(
                {
                    "issues_found": [
                        {
                            "issue_id": "ISSUE-001",
                            "category": "Architecture",
                            "severity": "High",
                            "description": "Component architecture does not follow dependency injection pattern",
                            "evidence": "DataProcessor hardcodes all dependencies internally",
                            "impact": "Difficult to test and modify component behavior independently",
                            "affected_phase": "Design",
                        }
                    ],
                    "improvement_suggestions": [],
                }
            )
        }

        with caplog.at_level(logging.INFO):
            agent.execute(design_spec)

        assert "Starting architecture review for task ARCH-TEST-001" in caplog.text
        assert "Architecture review completed: 1 issues, 0 suggestions" in caplog.text


class TestArchitectureReviewAgentDetection:
    """Test Architecture Review Agent detection capabilities."""

    @pytest.fixture
    def agent(self):
        """Create Architecture Review Agent instance."""
        return ArchitectureReviewAgent(db_path=":memory:")

    @patch.object(ArchitectureReviewAgent, "load_prompt")
    @patch.object(ArchitectureReviewAgent, "format_prompt")
    @patch.object(ArchitectureReviewAgent, "call_llm")
    def test_detect_poor_testability(
        self, mock_call_llm, mock_format_prompt, mock_load_prompt, agent
    ):
        """Test detection of poor testability due to hardcoded dependencies."""
        design_spec = DesignSpecification(
            task_id="ARCH-TEST-001",
            component_logic=[
                ComponentLogic(
                    component_name="EmailSender",
                    semantic_unit_id="SU-001",
                    responsibility="Send emails using SMTP",
                    interfaces=[{"method": "send_email"}],
                    implementation_notes="Hardcode SMTP server settings smtp.example.com:587 inside component",
                )
            ],
            design_review_checklist=[
                DesignReviewChecklistItem(
                    checklist_item_id="CHECK-001",
                    category="Architecture",
                    severity="Critical",
                    description="Components must be unit testable",
                    validation_criteria="Can test without external dependencies",
                ),
                DesignReviewChecklistItem(
                    checklist_item_id="CHECK-002",
                    category="Architecture",
                    severity="High",
                    description="Additional checklist item for comprehensive review coverage",
                    validation_criteria="Validation criteria for completeness",
                ),
                DesignReviewChecklistItem(
                    checklist_item_id="CHECK-003",
                    category="Architecture",
                    severity="Medium",
                    description="Additional checklist item for thorough evaluation",
                    validation_criteria="Validation criteria for quality",
                ),
                DesignReviewChecklistItem(
                    checklist_item_id="CHECK-004",
                    category="Architecture",
                    severity="Medium",
                    description="Additional checklist item for detailed assessment",
                    validation_criteria="Validation criteria for standards",
                ),
                DesignReviewChecklistItem(
                    checklist_item_id="CHECK-005",
                    category="Architecture",
                    severity="Low",
                    description="Additional checklist item for complete verification",
                    validation_criteria="Validation criteria for best practices",
                ),
            ],
            architecture_overview="Email system with hardcoded SMTP configuration making testing difficult",
            technology_stack={"language": "Python"},
        )

        mock_load_prompt.return_value = "Architecture review template"
        mock_format_prompt.return_value = "Formatted prompt"
        mock_call_llm.return_value = {
            "content": json.dumps(
                {
                    "issues_found": [
                        {
                            "issue_id": "ISSUE-001",
                            "category": "Architecture",
                            "severity": "Critical",
                            "description": "EmailSender hardcodes SMTP server making it impossible to unit test",
                            "evidence": "SMTP server settings hardcoded as smtp.example.com:587",
                            "impact": "Cannot test email logic without connecting to real SMTP server",
                            "affected_phase": "Design",
                        }
                    ],
                    "improvement_suggestions": [
                        {
                            "suggestion_id": "IMPROVE-001",
                            "related_issue_id": "ISSUE-001",
                            "category": "Architecture",
                            "priority": "High",
                            "description": "Inject SMTP configuration and connection via dependency injection",
                            "implementation_notes": "Create SMTPConfig class and inject via constructor: __init__(self, smtp_config: SMTPConfig), allowing test doubles",
                        }
                    ],
                }
            )
        }

        result = agent.execute(design_spec)

        assert len(result["issues_found"]) >= 1
        issue = result["issues_found"][0]
        assert issue["severity"] in ["Critical", "High"]
        assert "test" in issue["description"].lower() or "hardcod" in issue["description"].lower()

    @patch.object(ArchitectureReviewAgent, "load_prompt")
    @patch.object(ArchitectureReviewAgent, "format_prompt")
    @patch.object(ArchitectureReviewAgent, "call_llm")
    def test_detect_missing_design_patterns(
        self, mock_call_llm, mock_format_prompt, mock_load_prompt, agent
    ):
        """Test detection of missing appropriate design patterns."""
        design_spec = DesignSpecification(
            task_id="ARCH-PATTERN-001",
            component_logic=[
                ComponentLogic(
                    component_name="ReportGenerator",
                    semantic_unit_id="SU-001",
                    responsibility="Generate reports in PDF, CSV, JSON formats with if/else branching",
                    interfaces=[{"method": "generate"}],
                    implementation_notes="Use large if/else chain to select format: if format==PDF then..., elif format==CSV then...",
                )
            ],
            design_review_checklist=[
                DesignReviewChecklistItem(
                    checklist_item_id="CHECK-001",
                    category="Architecture",
                    severity="High",
                    description="Use Strategy pattern for varying algorithms",
                    validation_criteria="Avoid if/else for algorithm selection",
                ),
                DesignReviewChecklistItem(
                    checklist_item_id="CHECK-002",
                    category="Architecture",
                    severity="High",
                    description="Additional checklist item for comprehensive review coverage",
                    validation_criteria="Validation criteria for completeness",
                ),
                DesignReviewChecklistItem(
                    checklist_item_id="CHECK-003",
                    category="Architecture",
                    severity="Medium",
                    description="Additional checklist item for thorough evaluation",
                    validation_criteria="Validation criteria for quality",
                ),
                DesignReviewChecklistItem(
                    checklist_item_id="CHECK-004",
                    category="Architecture",
                    severity="Medium",
                    description="Additional checklist item for detailed assessment",
                    validation_criteria="Validation criteria for standards",
                ),
                DesignReviewChecklistItem(
                    checklist_item_id="CHECK-005",
                    category="Architecture",
                    severity="Low",
                    description="Additional checklist item for complete verification",
                    validation_criteria="Validation criteria for best practices",
                ),
            ],
            architecture_overview="Report generation system using if/else branching instead of Strategy pattern",
            technology_stack={"language": "Python"},
        )

        mock_load_prompt.return_value = "Architecture review template"
        mock_format_prompt.return_value = "Formatted prompt"
        mock_call_llm.return_value = {
            "content": json.dumps(
                {
                    "issues_found": [
                        {
                            "issue_id": "ISSUE-001",
                            "category": "Architecture",
                            "severity": "High",
                            "description": "ReportGenerator uses if/else chain instead of Strategy pattern",
                            "evidence": "Large if/else chain for format selection in generate() method",
                            "impact": "Adding new formats requires modifying existing code, violates Open/Closed Principle",
                            "affected_phase": "Design",
                        }
                    ],
                    "improvement_suggestions": [
                        {
                            "suggestion_id": "IMPROVE-001",
                            "related_issue_id": "ISSUE-001",
                            "category": "Architecture",
                            "priority": "High",
                            "description": "Implement Strategy pattern for report formatting",
                            "implementation_notes": "Create ReportFormatter interface with PDFFormatter, CSVFormatter, JSONFormatter implementations, inject via constructor",
                        }
                    ],
                }
            )
        }

        result = agent.execute(design_spec)

        assert len(result["issues_found"]) >= 1
        issue = result["issues_found"][0]
        assert "pattern" in issue["description"].lower() or "strategy" in issue["description"].lower()

    @patch.object(ArchitectureReviewAgent, "load_prompt")
    @patch.object(ArchitectureReviewAgent, "format_prompt")
    @patch.object(ArchitectureReviewAgent, "call_llm")
    def test_detect_poor_separation_of_concerns(
        self, mock_call_llm, mock_format_prompt, mock_load_prompt, agent
    ):
        """Test detection of poor separation between business logic and infrastructure."""
        design_spec = DesignSpecification(
            task_id="ARCH-SOC-001",
            component_logic=[
                ComponentLogic(
                    component_name="OrderService",
                    semantic_unit_id="SU-001",
                    responsibility="Process orders with SQL queries embedded in business logic",
                    interfaces=[{"method": "create_order"}],
                    implementation_notes="Execute SQL INSERT statements directly in order validation logic",
                )
            ],
            design_review_checklist=[
                DesignReviewChecklistItem(
                    checklist_item_id="CHECK-001",
                    category="Architecture",
                    severity="Critical",
                    description="Separate business logic from infrastructure",
                    validation_criteria="No SQL or file I/O in business logic layer",
                ),
                DesignReviewChecklistItem(
                    checklist_item_id="CHECK-002",
                    category="Architecture",
                    severity="High",
                    description="Additional checklist item for comprehensive review coverage",
                    validation_criteria="Validation criteria for completeness",
                ),
                DesignReviewChecklistItem(
                    checklist_item_id="CHECK-003",
                    category="Architecture",
                    severity="Medium",
                    description="Additional checklist item for thorough evaluation",
                    validation_criteria="Validation criteria for quality",
                ),
                DesignReviewChecklistItem(
                    checklist_item_id="CHECK-004",
                    category="Architecture",
                    severity="Medium",
                    description="Additional checklist item for detailed assessment",
                    validation_criteria="Validation criteria for standards",
                ),
                DesignReviewChecklistItem(
                    checklist_item_id="CHECK-005",
                    category="Architecture",
                    severity="Low",
                    description="Additional checklist item for complete verification",
                    validation_criteria="Validation criteria for best practices",
                ),
            ],
            architecture_overview="Order processing with SQL queries mixed into business logic layer",
            technology_stack={"language": "Python", "database": "PostgreSQL"},
        )

        mock_load_prompt.return_value = "Architecture review template"
        mock_format_prompt.return_value = "Formatted prompt"
        mock_call_llm.return_value = {
            "content": json.dumps(
                {
                    "issues_found": [
                        {
                            "issue_id": "ISSUE-001",
                            "category": "Architecture",
                            "severity": "Critical",
                            "description": "Business logic tightly coupled to SQL infrastructure code",
                            "evidence": "OrderService executes SQL INSERT statements within order validation logic",
                            "impact": "Cannot test business logic without database, cannot switch database implementation",
                            "affected_phase": "Design",
                        }
                    ],
                    "improvement_suggestions": [
                        {
                            "suggestion_id": "IMPROVE-001",
                            "related_issue_id": "ISSUE-001",
                            "category": "Architecture",
                            "priority": "High",
                            "description": "Separate business logic into domain layer with repository pattern",
                            "implementation_notes": "Create OrderRepository interface for data access, implement SQLOrderRepository, inject into OrderService",
                        }
                    ],
                }
            )
        }

        result = agent.execute(design_spec)

        assert len(result["issues_found"]) >= 1
        issue = result["issues_found"][0]
        assert issue["severity"] in ["Critical", "High"]

    @patch.object(ArchitectureReviewAgent, "load_prompt")
    @patch.object(ArchitectureReviewAgent, "format_prompt")
    @patch.object(ArchitectureReviewAgent, "call_llm")
    def test_detect_poor_extensibility(
        self, mock_call_llm, mock_format_prompt, mock_load_prompt, agent
    ):
        """Test detection of designs that violate Open/Closed Principle."""
        design_spec = DesignSpecification(
            task_id="ARCH-OCP-001",
            component_logic=[
                ComponentLogic(
                    component_name="PaymentProcessor",
                    semantic_unit_id="SU-001",
                    responsibility="Process payments for CreditCard and PayPal with if/else",
                    interfaces=[{"method": "process_payment"}],
                    implementation_notes="if payment_type == CreditCard: process_credit_card() elif payment_type == PayPal: process_paypal()",
                )
            ],
            design_review_checklist=[
                DesignReviewChecklistItem(
                    checklist_item_id="CHECK-001",
                    category="Architecture",
                    severity="High",
                    description="Design must be open for extension, closed for modification",
                    validation_criteria="Adding new features does not require modifying existing code",
                ),
                DesignReviewChecklistItem(
                    checklist_item_id="CHECK-002",
                    category="Architecture",
                    severity="High",
                    description="Additional checklist item for comprehensive review coverage",
                    validation_criteria="Validation criteria for completeness",
                ),
                DesignReviewChecklistItem(
                    checklist_item_id="CHECK-003",
                    category="Architecture",
                    severity="Medium",
                    description="Additional checklist item for thorough evaluation",
                    validation_criteria="Validation criteria for quality",
                ),
                DesignReviewChecklistItem(
                    checklist_item_id="CHECK-004",
                    category="Architecture",
                    severity="Medium",
                    description="Additional checklist item for detailed assessment",
                    validation_criteria="Validation criteria for standards",
                ),
                DesignReviewChecklistItem(
                    checklist_item_id="CHECK-005",
                    category="Architecture",
                    severity="Low",
                    description="Additional checklist item for complete verification",
                    validation_criteria="Validation criteria for best practices",
                ),
            ],
            architecture_overview="Payment processing system requiring code changes to add new payment methods",
            technology_stack={"language": "Python"},
        )

        mock_load_prompt.return_value = "Architecture review template"
        mock_format_prompt.return_value = "Formatted prompt"
        mock_call_llm.return_value = {
            "content": json.dumps(
                {
                    "issues_found": [
                        {
                            "issue_id": "ISSUE-001",
                            "category": "Architecture",
                            "severity": "High",
                            "description": "PaymentProcessor violates Open/Closed Principle, requires modification to add payment methods",
                            "evidence": "Uses if/else chain for payment type selection",
                            "impact": "Every new payment method requires modifying PaymentProcessor code, risk of breaking existing functionality",
                            "affected_phase": "Design",
                        }
                    ],
                    "improvement_suggestions": [
                        {
                            "suggestion_id": "IMPROVE-001",
                            "related_issue_id": "ISSUE-001",
                            "category": "Architecture",
                            "priority": "High",
                            "description": "Use PaymentMethod interface to support extension without modification",
                            "implementation_notes": "Define PaymentMethod interface with process() method, create CreditCardPayment, PayPalPayment implementations, use factory to select",
                        }
                    ],
                }
            )
        }

        result = agent.execute(design_spec)

        assert len(result["issues_found"]) >= 1
        issue = result["issues_found"][0]
        assert issue["severity"] in ["Critical", "High"]


class TestArchitectureReviewAgentErrorHandling:
    """Test Architecture Review Agent error handling."""

    @pytest.fixture
    def agent(self):
        """Create Architecture Review Agent instance."""
        return ArchitectureReviewAgent(db_path=":memory:")

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
                    category="Architecture",
                    severity="Critical",
                    description="Test checklist item for validation purposes",
                    validation_criteria="Test validation criteria applied",
                ),
                DesignReviewChecklistItem(
                    checklist_item_id="CHECK-002",
                    category="Architecture",
                    severity="High",
                    description="Test checklist item for comprehensive testing",
                    validation_criteria="Test validation criteria checked",
                ),
                DesignReviewChecklistItem(
                    checklist_item_id="CHECK-003",
                    category="Architecture",
                    severity="Medium",
                    description="Test checklist item for medium severity cases",
                    validation_criteria="Test validation criteria validated",
                ),
                DesignReviewChecklistItem(
                    checklist_item_id="CHECK-004",
                    category="Architecture",
                    severity="Medium",
                    description="Test checklist item for additional test coverage",
                    validation_criteria="Test validation criteria confirmed",
                ),
                DesignReviewChecklistItem(
                    checklist_item_id="CHECK-005",
                    category="Architecture",
                    severity="Low",
                    description="Test checklist item for low severity verification",
                    validation_criteria="Test validation criteria ensured",
                ),
            ],
            architecture_overview="Test architecture overview for error handling test scenarios",
            technology_stack={"language": "Python"},
        )

    @patch.object(ArchitectureReviewAgent, "load_prompt")
    @patch.object(ArchitectureReviewAgent, "format_prompt")
    @patch.object(ArchitectureReviewAgent, "call_llm")
    def test_execute_raises_error_on_invalid_json_response(
        self, mock_call_llm, mock_format_prompt, mock_load_prompt, agent, design_spec
    ):
        """Test execute raises error when LLM returns invalid JSON."""
        mock_load_prompt.return_value = "Architecture review prompt template"
        mock_format_prompt.return_value = "Formatted prompt"
        mock_call_llm.return_value = {"content": "Invalid JSON {{{"}

        with pytest.raises(AgentExecutionError) as exc_info:
            agent.execute(design_spec)

        assert "Architecture review failed" in str(exc_info.value)

    @patch.object(ArchitectureReviewAgent, "load_prompt")
    @patch.object(ArchitectureReviewAgent, "format_prompt")
    @patch.object(ArchitectureReviewAgent, "call_llm")
    def test_execute_raises_error_on_missing_required_fields(
        self, mock_call_llm, mock_format_prompt, mock_load_prompt, agent, design_spec
    ):
        """Test execute raises error when response missing required fields."""
        mock_load_prompt.return_value = "Architecture review prompt template"
        mock_format_prompt.return_value = "Formatted prompt"
        mock_call_llm.return_value = {"content": json.dumps({"issues_found": []})}

        with pytest.raises(AgentExecutionError) as exc_info:
            agent.execute(design_spec)

        assert "Response missing required fields" in str(exc_info.value)

    @patch.object(ArchitectureReviewAgent, "load_prompt")
    @patch.object(ArchitectureReviewAgent, "format_prompt")
    @patch.object(ArchitectureReviewAgent, "call_llm")
    def test_execute_handles_llm_exceptions(
        self, mock_call_llm, mock_format_prompt, mock_load_prompt, agent, design_spec
    ):
        """Test execute handles exceptions from LLM calls."""
        mock_load_prompt.return_value = "Architecture review prompt template"
        mock_format_prompt.return_value = "Formatted prompt"
        mock_call_llm.side_effect = Exception("LLM connection failed")

        with pytest.raises(AgentExecutionError) as exc_info:
            agent.execute(design_spec)

        assert "Architecture review failed" in str(exc_info.value)


class TestArchitectureReviewAgentEdgeCases:
    """Test Architecture Review Agent edge cases."""

    @pytest.fixture
    def agent(self):
        """Create Architecture Review Agent instance."""
        return ArchitectureReviewAgent(db_path=":memory:")

    @patch.object(ArchitectureReviewAgent, "load_prompt")
    @patch.object(ArchitectureReviewAgent, "format_prompt")
    @patch.object(ArchitectureReviewAgent, "call_llm")
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
                    category="Architecture",
                    severity="Critical",
                    description="Edge case checklist item for validation purposes",
                    validation_criteria="Edge case validation criteria applied",
                ),
                DesignReviewChecklistItem(
                    checklist_item_id="CHECK-002",
                    category="Architecture",
                    severity="High",
                    description="Edge case checklist item for comprehensive testing",
                    validation_criteria="Edge case validation criteria checked",
                ),
                DesignReviewChecklistItem(
                    checklist_item_id="CHECK-003",
                    category="Architecture",
                    severity="Medium",
                    description="Edge case checklist item for medium severity cases",
                    validation_criteria="Edge case validation criteria validated",
                ),
                DesignReviewChecklistItem(
                    checklist_item_id="CHECK-004",
                    category="Architecture",
                    severity="Medium",
                    description="Edge case checklist item for additional test coverage",
                    validation_criteria="Edge case validation criteria confirmed",
                ),
                DesignReviewChecklistItem(
                    checklist_item_id="CHECK-005",
                    category="Architecture",
                    severity="Low",
                    description="Edge case checklist item for low severity verification",
                    validation_criteria="Edge case validation criteria ensured",
                ),
            ],
            architecture_overview="Edge case architecture overview for testing string response handling",
            technology_stack={"language": "Python"},
        )

        mock_load_prompt.return_value = "Architecture review prompt template"
        mock_format_prompt.return_value = "Formatted prompt"
        mock_call_llm.return_value = {
            "content": '{"issues_found": [], "improvement_suggestions": []}'
        }

        result = agent.execute(design_spec)

        assert result["issues_found"] == []
        assert result["improvement_suggestions"] == []

    @patch.object(ArchitectureReviewAgent, "load_prompt")
    @patch.object(ArchitectureReviewAgent, "format_prompt")
    @patch.object(ArchitectureReviewAgent, "call_llm")
    def test_execute_with_complex_architecture(
        self, mock_call_llm, mock_format_prompt, mock_load_prompt, agent
    ):
        """Test execute handles complex multi-layer architecture."""
        design_spec = DesignSpecification(
            task_id="COMPLEX-001",
            component_logic=[
                ComponentLogic(
                    component_name="PresentationLayer",
                    semantic_unit_id="SU-001",
                    responsibility="Handle HTTP requests and responses in presentation layer",
                    interfaces=[{"method": "handle_request"}],
                    implementation_notes="REST API endpoints for presentation layer",
                ),
                ComponentLogic(
                    component_name="BusinessLogicLayer",
                    semantic_unit_id="SU-002",
                    responsibility="Implement core business rules and validation in domain layer",
                    interfaces=[{"method": "execute_business_logic"}],
                    implementation_notes="Domain logic implementation in business layer",
                ),
                ComponentLogic(
                    component_name="DataAccessLayer",
                    semantic_unit_id="SU-003",
                    responsibility="Handle database operations and persistence in data layer",
                    interfaces=[{"method": "save", "method": "find"}],
                    implementation_notes="Repository pattern for data persistence layer",
                ),
            ],
            design_review_checklist=[
                DesignReviewChecklistItem(
                    checklist_item_id="CHECK-001",
                    category="Architecture",
                    severity="Critical",
                    description="Complex architecture checklist item",
                    validation_criteria="Complex architecture validation",
                ),
                DesignReviewChecklistItem(
                    checklist_item_id="CHECK-002",
                    category="Architecture",
                    severity="High",
                    description="Additional checklist item for comprehensive review coverage",
                    validation_criteria="Validation criteria for completeness",
                ),
                DesignReviewChecklistItem(
                    checklist_item_id="CHECK-003",
                    category="Architecture",
                    severity="Medium",
                    description="Additional checklist item for thorough evaluation",
                    validation_criteria="Validation criteria for quality",
                ),
                DesignReviewChecklistItem(
                    checklist_item_id="CHECK-004",
                    category="Architecture",
                    severity="Medium",
                    description="Additional checklist item for detailed assessment",
                    validation_criteria="Validation criteria for standards",
                ),
                DesignReviewChecklistItem(
                    checklist_item_id="CHECK-005",
                    category="Architecture",
                    severity="Low",
                    description="Additional checklist item for complete verification",
                    validation_criteria="Validation criteria for best practices",
                ),
            ],
            architecture_overview="Three-tier architecture with proper separation of concerns across presentation, business, and data layers",
            technology_stack={"language": "Python", "framework": "FastAPI"},
        )

        mock_load_prompt.return_value = "Architecture review prompt template"
        mock_format_prompt.return_value = "Formatted prompt"
        mock_call_llm.return_value = {
            "content": json.dumps(
                {"issues_found": [], "improvement_suggestions": []}
            )
        }

        result = agent.execute(design_spec)

        assert "issues_found" in result
        assert "improvement_suggestions" in result
