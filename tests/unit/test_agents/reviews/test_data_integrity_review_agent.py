"""
Unit tests for Data Integrity Review Agent (FR-003).

Tests the specialist agent that reviews design specifications for data integrity:
- Referential integrity and foreign key constraints
- Data validation and constraints
- Transaction design and ACID properties
- Data consistency and type safety
"""

import json
import logging
from unittest.mock import MagicMock, patch

import pytest

from asp.agents.base_agent import AgentExecutionError
from asp.agents.reviews.data_integrity_review_agent import DataIntegrityReviewAgent
from asp.models.design import (
    ComponentLogic,
    DataSchema,
    DesignReviewChecklistItem,
    DesignSpecification,
)


class TestDataIntegrityReviewAgentInitialization:
    """Test Data Integrity Review Agent initialization."""

    def test_initialization_with_defaults(self):
        """Test agent initializes with default values."""
        agent = DataIntegrityReviewAgent()

        assert agent.agent_version == "1.0.0"

    def test_initialization_with_custom_llm_client(self):
        """Test agent initializes with custom LLM client."""
        mock_client = MagicMock()
        agent = DataIntegrityReviewAgent(llm_client=mock_client)

        assert agent.agent_version == "1.0.0"

    def test_initialization_with_custom_db_path(self):
        """Test agent initializes with custom database path."""
        agent = DataIntegrityReviewAgent(db_path=":memory:")

        assert agent.agent_version == "1.0.0"


class TestDataIntegrityReviewAgentExecute:
    """Test Data Integrity Review Agent execute method."""

    @pytest.fixture
    def agent(self):
        """Create Data Integrity Review Agent instance."""
        return DataIntegrityReviewAgent(db_path=":memory:")

    @pytest.fixture
    def design_spec(self):
        """Create a sample design specification."""
        return DesignSpecification(
            task_id="DATA-TEST-001",
            component_logic=[
                ComponentLogic(
                    component_name="OrderService",
                    semantic_unit_id="SU-001",
                    responsibility="Manage orders with references to users",
                    interfaces=[{"method": "create_order"}],
                    implementation_notes="Create orders linked to user IDs",
                )
            ],
            data_schemas=[
                DataSchema(
                    table_name="orders",
                    description="Database table storing information",
                    columns=[
                        {"name": "id", "type": "uuid", "constraints": ["PRIMARY KEY"]},
                        {"name": "user_id", "type": "uuid", "constraints": []},
                        {"name": "total", "type": "decimal", "constraints": []},
                    ],
                    relationships=[],
                    
                )
            ],
            design_review_checklist=[
                DesignReviewChecklistItem(
                    checklist_item_id="CHECK-001",
                    category="Data Integrity",
                    severity="Critical",
                    description="Foreign keys must have referential integrity constraints",
                    validation_criteria="All foreign key columns have FOREIGN KEY constraint",
                ),
                DesignReviewChecklistItem(
                    checklist_item_id="CHECK-002",
                    category="Data Integrity",
                    severity="High",
                    description="Required fields must have NOT NULL constraint",
                    validation_criteria="Critical fields marked as NOT NULL",
                ),
                DesignReviewChecklistItem(
                    checklist_item_id="CHECK-003",
                    category="Data Integrity",
                    severity="Medium",
                    description="Use CHECK constraints for data validation",
                    validation_criteria="Business rules enforced at database level",
                ),
                DesignReviewChecklistItem(
                    checklist_item_id="CHECK-004",
                    category="Data Integrity",
                    severity="Medium",
                    description="Define cascade rules for foreign keys",
                    validation_criteria="ON DELETE and ON UPDATE behavior specified",
                ),
                DesignReviewChecklistItem(
                    checklist_item_id="CHECK-005",
                    category="Data Integrity",
                    severity="Low",
                    description="Use appropriate data types for fields",
                    validation_criteria="Match data types to actual usage patterns",
                ),
            ],
            architecture_overview="Order management system with missing foreign key constraints",
            technology_stack={"language": "Python", "database": "PostgreSQL"},
        )

    @patch.object(DataIntegrityReviewAgent, "load_prompt")
    @patch.object(DataIntegrityReviewAgent, "format_prompt")
    @patch.object(DataIntegrityReviewAgent, "call_llm")
    def test_execute_returns_valid_response(
        self, mock_call_llm, mock_format_prompt, mock_load_prompt, agent, design_spec
    ):
        """Test execute returns valid response with issues and suggestions."""
        mock_load_prompt.return_value = "Data integrity review prompt template"
        mock_format_prompt.return_value = "Formatted prompt with design spec"
        mock_call_llm.return_value = {
            "content": json.dumps(
                {
                    "issues_found": [
                        {
                            "issue_id": "ISSUE-001",
                            "category": "Data Integrity",
                            "severity": "Critical",
                            "description": "Missing foreign key constraint on orders.user_id column",
                            "evidence": "orders.user_id has no FOREIGN KEY constraint to users table",
                            "impact": "Orphaned orders possible, data integrity violations",
                            "affected_phase": "Design",
                        }
                    ],
                    "improvement_suggestions": [
                        {
                            "suggestion_id": "IMPROVE-001",
                            "related_issue_id": "ISSUE-001",
                            "category": "Data Integrity",
                            "priority": "High",
                            "description": "Add foreign key constraint on orders.user_id referencing users.id",
                            "implementation_notes": "ALTER TABLE orders ADD CONSTRAINT fk_orders_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE",
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
        assert result["issues_found"][0]["category"] == "Data Integrity"

    @patch.object(DataIntegrityReviewAgent, "load_prompt")
    @patch.object(DataIntegrityReviewAgent, "format_prompt")
    @patch.object(DataIntegrityReviewAgent, "call_llm")
    def test_execute_with_no_issues_found(
        self, mock_call_llm, mock_format_prompt, mock_load_prompt, agent, design_spec
    ):
        """Test execute with clean design (no issues)."""
        mock_load_prompt.return_value = "Data integrity review prompt template"
        mock_format_prompt.return_value = "Formatted prompt"
        mock_call_llm.return_value = {
            "content": json.dumps(
                {"issues_found": [], "improvement_suggestions": []}
            )
        }

        result = agent.execute(design_spec)

        assert result["issues_found"] == []
        assert result["improvement_suggestions"] == []

    @patch.object(DataIntegrityReviewAgent, "load_prompt")
    @patch.object(DataIntegrityReviewAgent, "format_prompt")
    @patch.object(DataIntegrityReviewAgent, "call_llm")
    def test_execute_logs_review_metrics(
        self, mock_call_llm, mock_format_prompt, mock_load_prompt, agent, design_spec, caplog
    ):
        """Test execute logs data integrity review metrics."""
        mock_load_prompt.return_value = "Data integrity review prompt template"
        mock_format_prompt.return_value = "Formatted prompt"
        mock_call_llm.return_value = {
            "content": json.dumps(
                {
                    "issues_found": [
                        {
                            "issue_id": "ISSUE-001",
                            "category": "Data Integrity",
                            "severity": "Critical",
                            "description": "Missing foreign key constraint on critical relationship column",
                            "evidence": "user_id column has no foreign key constraint",
                            "impact": "Data integrity violations and orphaned records possible",
                            "affected_phase": "Design",
                        }
                    ],
                    "improvement_suggestions": [],
                }
            )
        }

        with caplog.at_level(logging.INFO):
            agent.execute(design_spec)

        assert "Starting data integrity review for task DATA-TEST-001" in caplog.text
        assert "Data integrity review completed: found 1 issues, 0 suggestions" in caplog.text


class TestDataIntegrityReviewAgentDetection:
    """Test Data Integrity Review Agent detection capabilities."""

    @pytest.fixture
    def agent(self):
        """Create Data Integrity Review Agent instance."""
        return DataIntegrityReviewAgent(db_path=":memory:")

    @patch.object(DataIntegrityReviewAgent, "load_prompt")
    @patch.object(DataIntegrityReviewAgent, "format_prompt")
    @patch.object(DataIntegrityReviewAgent, "call_llm")
    def test_detect_missing_foreign_key_constraints(
        self, mock_call_llm, mock_format_prompt, mock_load_prompt, agent
    ):
        """Test detection of missing foreign key constraints."""
        design_spec = DesignSpecification(
            task_id="DATA-FK-001",
            component_logic=[
                ComponentLogic(
                    component_name="CommentService",
                    semantic_unit_id="SU-001",
                    responsibility="Manage comments on posts",
                    interfaces=[{"method": "create_comment"}],
                    implementation_notes="Create comments with post_id and user_id",
                )
            ],
            data_schemas=[
                DataSchema(
                    table_name="comments",
                    description="Database table storing information",
                    columns=[
                        {"name": "id", "type": "uuid", "constraints": ["PRIMARY KEY"]},
                        {"name": "post_id", "type": "uuid", "constraints": []},
                        {"name": "user_id", "type": "uuid", "constraints": []},
                        {"name": "content", "type": "text", "constraints": []},
                    ],
                    relationships=[],
                    
                )
            ],
            design_review_checklist=[
                DesignReviewChecklistItem(
                    checklist_item_id="CHECK-001",
                    category="Data Integrity",
                    severity="Critical",
                    description="Foreign keys must reference parent tables",
                    validation_criteria="post_id and user_id have FOREIGN KEY constraints",
                ),
                DesignReviewChecklistItem(
                    checklist_item_id="CHECK-002",
                    category="Data Integrity",
                    severity="High",
                    description="Additional checklist item for comprehensive review coverage",
                    validation_criteria="Validation criteria for completeness",
                ),
                DesignReviewChecklistItem(
                    checklist_item_id="CHECK-003",
                    category="Data Integrity",
                    severity="Medium",
                    description="Additional checklist item for thorough evaluation",
                    validation_criteria="Validation criteria for quality",
                ),
                DesignReviewChecklistItem(
                    checklist_item_id="CHECK-004",
                    category="Data Integrity",
                    severity="Medium",
                    description="Additional checklist item for detailed assessment",
                    validation_criteria="Validation criteria for standards",
                ),
                DesignReviewChecklistItem(
                    checklist_item_id="CHECK-005",
                    category="Data Integrity",
                    severity="Low",
                    description="Additional checklist item for complete verification",
                    validation_criteria="Validation criteria for best practices",
                ),
            ],
            architecture_overview="Comment system without foreign key constraints on post_id and user_id",
            technology_stack={"database": "PostgreSQL"},
        )

        mock_load_prompt.return_value = "Data integrity review template"
        mock_format_prompt.return_value = "Formatted prompt"
        mock_call_llm.return_value = {
            "content": json.dumps(
                {
                    "issues_found": [
                        {
                            "issue_id": "ISSUE-001",
                            "category": "Data Integrity",
                            "severity": "Critical",
                            "description": "Missing foreign key constraints on comments.post_id and comments.user_id",
                            "evidence": "post_id and user_id columns have no FOREIGN KEY constraints",
                            "impact": "Orphaned comments possible, can reference non-existent posts and users",
                            "affected_phase": "Design",
                        }
                    ],
                    "improvement_suggestions": [
                        {
                            "suggestion_id": "IMPROVE-001",
                            "related_issue_id": "ISSUE-001",
                            "category": "Data Integrity",
                            "priority": "High",
                            "description": "Add foreign key constraints for post_id and user_id",
                            "implementation_notes": "ADD CONSTRAINT fk_comments_post FOREIGN KEY (post_id) REFERENCES posts(id) ON DELETE CASCADE, ADD CONSTRAINT fk_comments_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE",
                        }
                    ],
                }
            )
        }

        result = agent.execute(design_spec)

        assert len(result["issues_found"]) >= 1
        issue = result["issues_found"][0]
        assert issue["severity"] in ["Critical", "High"]
        assert "foreign key" in issue["description"].lower()

    @patch.object(DataIntegrityReviewAgent, "load_prompt")
    @patch.object(DataIntegrityReviewAgent, "format_prompt")
    @patch.object(DataIntegrityReviewAgent, "call_llm")
    def test_detect_missing_not_null_constraints(
        self, mock_call_llm, mock_format_prompt, mock_load_prompt, agent
    ):
        """Test detection of missing NOT NULL constraints on required fields."""
        design_spec = DesignSpecification(
            task_id="DATA-NULL-001",
            component_logic=[
                ComponentLogic(
                    component_name="ProductService",
                    semantic_unit_id="SU-001",
                    responsibility="Manage product catalog",
                    interfaces=[{"method": "create_product"}],
                    implementation_notes="All products must have name and price",
                )
            ],
            data_schemas=[
                DataSchema(
                    table_name="products",
                    description="Database table storing information",
                    columns=[
                        {"name": "id", "type": "uuid", "constraints": ["PRIMARY KEY"]},
                        {"name": "name", "type": "varchar(255)", "constraints": []},
                        {"name": "price", "type": "decimal(10,2)", "constraints": []},
                    ],
                    relationships=[],
                    
                )
            ],
            design_review_checklist=[
                DesignReviewChecklistItem(
                    checklist_item_id="CHECK-001",
                    category="Data Integrity",
                    severity="High",
                    description="Required fields must have NOT NULL constraints",
                    validation_criteria="name and price marked as NOT NULL",
                ),
                DesignReviewChecklistItem(
                    checklist_item_id="CHECK-002",
                    category="Data Integrity",
                    severity="High",
                    description="Additional checklist item for comprehensive review coverage",
                    validation_criteria="Validation criteria for completeness",
                ),
                DesignReviewChecklistItem(
                    checklist_item_id="CHECK-003",
                    category="Data Integrity",
                    severity="Medium",
                    description="Additional checklist item for thorough evaluation",
                    validation_criteria="Validation criteria for quality",
                ),
                DesignReviewChecklistItem(
                    checklist_item_id="CHECK-004",
                    category="Data Integrity",
                    severity="Medium",
                    description="Additional checklist item for detailed assessment",
                    validation_criteria="Validation criteria for standards",
                ),
                DesignReviewChecklistItem(
                    checklist_item_id="CHECK-005",
                    category="Data Integrity",
                    severity="Low",
                    description="Additional checklist item for complete verification",
                    validation_criteria="Validation criteria for best practices",
                ),
            ],
            architecture_overview="Product catalog where name and price are required but missing NOT NULL constraints",
            technology_stack={"database": "PostgreSQL"},
        )

        mock_load_prompt.return_value = "Data integrity review template"
        mock_format_prompt.return_value = "Formatted prompt"
        mock_call_llm.return_value = {
            "content": json.dumps(
                {
                    "issues_found": [
                        {
                            "issue_id": "ISSUE-001",
                            "category": "Data Integrity",
                            "severity": "High",
                            "description": "Missing NOT NULL constraints on required fields name and price",
                            "evidence": "products.name and products.price allow NULL values",
                            "impact": "Products can be created without name or price, violating business rules",
                            "affected_phase": "Design",
                        }
                    ],
                    "improvement_suggestions": [
                        {
                            "suggestion_id": "IMPROVE-001",
                            "related_issue_id": "ISSUE-001",
                            "category": "Data Integrity",
                            "priority": "High",
                            "description": "Add NOT NULL constraints to name and price columns",
                            "implementation_notes": "ALTER TABLE products ALTER COLUMN name SET NOT NULL, ALTER COLUMN price SET NOT NULL",
                        }
                    ],
                }
            )
        }

        result = agent.execute(design_spec)

        assert len(result["issues_found"]) >= 1
        issue = result["issues_found"][0]
        assert "not null" in issue["description"].lower() or "null" in issue["description"].lower()

    @patch.object(DataIntegrityReviewAgent, "load_prompt")
    @patch.object(DataIntegrityReviewAgent, "format_prompt")
    @patch.object(DataIntegrityReviewAgent, "call_llm")
    def test_detect_missing_check_constraints(
        self, mock_call_llm, mock_format_prompt, mock_load_prompt, agent
    ):
        """Test detection of missing CHECK constraints for business rules."""
        design_spec = DesignSpecification(
            task_id="DATA-CHECK-001",
            component_logic=[
                ComponentLogic(
                    component_name="InventoryService",
                    semantic_unit_id="SU-001",
                    responsibility="Track product inventory with non-negative quantities",
                    interfaces=[{"method": "update_quantity"}],
                    implementation_notes="Quantity must be >= 0",
                )
            ],
            data_schemas=[
                DataSchema(
                    table_name="inventory",
                    description="Database table storing information",
                    columns=[
                        {"name": "product_id", "type": "uuid", "constraints": ["PRIMARY KEY"]},
                        {"name": "quantity", "type": "integer", "constraints": []},
                    ],
                    relationships=[],
                    
                )
            ],
            design_review_checklist=[
                DesignReviewChecklistItem(
                    checklist_item_id="CHECK-001",
                    category="Data Integrity",
                    severity="High",
                    description="Use CHECK constraints to enforce business rules",
                    validation_criteria="quantity >= 0 enforced by CHECK constraint",
                ),
                DesignReviewChecklistItem(
                    checklist_item_id="CHECK-002",
                    category="Data Integrity",
                    severity="High",
                    description="Additional checklist item for comprehensive review coverage",
                    validation_criteria="Validation criteria for completeness",
                ),
                DesignReviewChecklistItem(
                    checklist_item_id="CHECK-003",
                    category="Data Integrity",
                    severity="Medium",
                    description="Additional checklist item for thorough evaluation",
                    validation_criteria="Validation criteria for quality",
                ),
                DesignReviewChecklistItem(
                    checklist_item_id="CHECK-004",
                    category="Data Integrity",
                    severity="Medium",
                    description="Additional checklist item for detailed assessment",
                    validation_criteria="Validation criteria for standards",
                ),
                DesignReviewChecklistItem(
                    checklist_item_id="CHECK-005",
                    category="Data Integrity",
                    severity="Low",
                    description="Additional checklist item for complete verification",
                    validation_criteria="Validation criteria for best practices",
                ),
            ],
            architecture_overview="Inventory system without CHECK constraint on quantity field allowing negative values",
            technology_stack={"database": "PostgreSQL"},
        )

        mock_load_prompt.return_value = "Data integrity review template"
        mock_format_prompt.return_value = "Formatted prompt"
        mock_call_llm.return_value = {
            "content": json.dumps(
                {
                    "issues_found": [
                        {
                            "issue_id": "ISSUE-001",
                            "category": "Data Integrity",
                            "severity": "High",
                            "description": "Missing CHECK constraint on inventory.quantity to prevent negative values",
                            "evidence": "quantity column has no CHECK constraint, allows negative values",
                            "impact": "Inventory can have negative quantities, violating business logic",
                            "affected_phase": "Design",
                        }
                    ],
                    "improvement_suggestions": [
                        {
                            "suggestion_id": "IMPROVE-001",
                            "related_issue_id": "ISSUE-001",
                            "category": "Data Integrity",
                            "priority": "High",
                            "description": "Add CHECK constraint to ensure quantity is non-negative",
                            "implementation_notes": "ALTER TABLE inventory ADD CONSTRAINT chk_quantity_positive CHECK (quantity >= 0)",
                        }
                    ],
                }
            )
        }

        result = agent.execute(design_spec)

        assert len(result["issues_found"]) >= 1
        issue = result["issues_found"][0]
        assert "check" in issue["description"].lower() or "constraint" in issue["description"].lower()

    @patch.object(DataIntegrityReviewAgent, "load_prompt")
    @patch.object(DataIntegrityReviewAgent, "format_prompt")
    @patch.object(DataIntegrityReviewAgent, "call_llm")
    def test_detect_missing_cascade_rules(
        self, mock_call_llm, mock_format_prompt, mock_load_prompt, agent
    ):
        """Test detection of missing cascade rules on foreign keys."""
        design_spec = DesignSpecification(
            task_id="DATA-CASCADE-001",
            component_logic=[
                ComponentLogic(
                    component_name="OrderItemService",
                    semantic_unit_id="SU-001",
                    responsibility="Manage order items linked to orders",
                    interfaces=[{"method": "add_item"}],
                    implementation_notes="Order items reference parent orders",
                )
            ],
            data_schemas=[
                DataSchema(
                    table_name="order_items",
                    description="Database table storing information",
                    columns=[
                        {"name": "id", "type": "uuid", "constraints": ["PRIMARY KEY"]},
                        {"name": "order_id", "type": "uuid", "constraints": ["FOREIGN KEY"]},
                        {"name": "product_id", "type": "uuid", "constraints": []},
                    ],
                    relationships=[
                        "ALTER TABLE order_items ADD FOREIGN KEY (order_id) REFERENCES orders(id)"
                    ],
                    
                )
            ],
            design_review_checklist=[
                DesignReviewChecklistItem(
                    checklist_item_id="CHECK-001",
                    category="Data Integrity",
                    severity="Medium",
                    description="Foreign keys must define cascade behavior",
                    validation_criteria="ON DELETE and ON UPDATE rules specified",
                ),
                DesignReviewChecklistItem(
                    checklist_item_id="CHECK-002",
                    category="Data Integrity",
                    severity="High",
                    description="Additional checklist item for comprehensive review coverage",
                    validation_criteria="Validation criteria for completeness",
                ),
                DesignReviewChecklistItem(
                    checklist_item_id="CHECK-003",
                    category="Data Integrity",
                    severity="Medium",
                    description="Additional checklist item for thorough evaluation",
                    validation_criteria="Validation criteria for quality",
                ),
                DesignReviewChecklistItem(
                    checklist_item_id="CHECK-004",
                    category="Data Integrity",
                    severity="Medium",
                    description="Additional checklist item for detailed assessment",
                    validation_criteria="Validation criteria for standards",
                ),
                DesignReviewChecklistItem(
                    checklist_item_id="CHECK-005",
                    category="Data Integrity",
                    severity="Low",
                    description="Additional checklist item for complete verification",
                    validation_criteria="Validation criteria for best practices",
                ),
            ],
            architecture_overview="Order items with foreign key but no cascade rules defined for deletion behavior",
            technology_stack={"database": "PostgreSQL"},
        )

        mock_load_prompt.return_value = "Data integrity review template"
        mock_format_prompt.return_value = "Formatted prompt"
        mock_call_llm.return_value = {
            "content": json.dumps(
                {
                    "issues_found": [
                        {
                            "issue_id": "ISSUE-001",
                            "category": "Data Integrity",
                            "severity": "Medium",
                            "description": "Foreign key on order_items.order_id missing cascade rules",
                            "evidence": "Relationship defined but no ON DELETE or ON UPDATE behavior specified",
                            "impact": "Unclear behavior when parent order deleted, potential orphaned records",
                            "affected_phase": "Design",
                        }
                    ],
                    "improvement_suggestions": [
                        {
                            "suggestion_id": "IMPROVE-001",
                            "related_issue_id": "ISSUE-001",
                            "category": "Data Integrity",
                            "priority": "Medium",
                            "description": "Define ON DELETE CASCADE for order_items.order_id foreign key",
                            "implementation_notes": "Specify ON DELETE CASCADE to automatically delete items when order deleted",
                        }
                    ],
                }
            )
        }

        result = agent.execute(design_spec)

        assert len(result["issues_found"]) >= 1
        issue = result["issues_found"][0]
        assert "cascade" in issue["description"].lower() or "delete" in issue["description"].lower()


class TestDataIntegrityReviewAgentErrorHandling:
    """Test Data Integrity Review Agent error handling."""

    @pytest.fixture
    def agent(self):
        """Create Data Integrity Review Agent instance."""
        return DataIntegrityReviewAgent(db_path=":memory:")

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
                    category="Data Integrity",
                    severity="Critical",
                    description="Test checklist item for validation purposes",
                    validation_criteria="Test validation criteria applied",
                ),
                DesignReviewChecklistItem(
                    checklist_item_id="CHECK-002",
                    category="Data Integrity",
                    severity="High",
                    description="Test checklist item for comprehensive testing",
                    validation_criteria="Test validation criteria checked",
                ),
                DesignReviewChecklistItem(
                    checklist_item_id="CHECK-003",
                    category="Data Integrity",
                    severity="Medium",
                    description="Test checklist item for medium severity cases",
                    validation_criteria="Test validation criteria validated",
                ),
                DesignReviewChecklistItem(
                    checklist_item_id="CHECK-004",
                    category="Data Integrity",
                    severity="Medium",
                    description="Test checklist item for additional test coverage",
                    validation_criteria="Test validation criteria confirmed",
                ),
                DesignReviewChecklistItem(
                    checklist_item_id="CHECK-005",
                    category="Data Integrity",
                    severity="Low",
                    description="Test checklist item for low severity verification",
                    validation_criteria="Test validation criteria ensured",
                ),
            ],
            architecture_overview="Test architecture overview for error handling test scenarios",
            technology_stack={"language": "Python"},
        )

    @patch.object(DataIntegrityReviewAgent, "load_prompt")
    @patch.object(DataIntegrityReviewAgent, "format_prompt")
    @patch.object(DataIntegrityReviewAgent, "call_llm")
    def test_execute_raises_error_on_invalid_json_response(
        self, mock_call_llm, mock_format_prompt, mock_load_prompt, agent, design_spec
    ):
        """Test execute raises error when LLM returns invalid JSON."""
        mock_load_prompt.return_value = "Data integrity review prompt template"
        mock_format_prompt.return_value = "Formatted prompt"
        mock_call_llm.return_value = {"content": "Invalid JSON {{{"}

        with pytest.raises(AgentExecutionError) as exc_info:
            agent.execute(design_spec)

        assert "Failed to parse data integrity review response" in str(exc_info.value)

    @patch.object(DataIntegrityReviewAgent, "load_prompt")
    @patch.object(DataIntegrityReviewAgent, "format_prompt")
    @patch.object(DataIntegrityReviewAgent, "call_llm")
    def test_execute_raises_error_on_missing_issues_found(
        self, mock_call_llm, mock_format_prompt, mock_load_prompt, agent, design_spec
    ):
        """Test execute raises error when response missing issues_found."""
        mock_load_prompt.return_value = "Data integrity review prompt template"
        mock_format_prompt.return_value = "Formatted prompt"
        mock_call_llm.return_value = {
            "content": json.dumps({"improvement_suggestions": []})
        }

        with pytest.raises(AgentExecutionError) as exc_info:
            agent.execute(design_spec)

        assert "Response missing 'issues_found' field" in str(exc_info.value)

    @patch.object(DataIntegrityReviewAgent, "load_prompt")
    @patch.object(DataIntegrityReviewAgent, "format_prompt")
    @patch.object(DataIntegrityReviewAgent, "call_llm")
    def test_execute_raises_error_on_missing_suggestions(
        self, mock_call_llm, mock_format_prompt, mock_load_prompt, agent, design_spec
    ):
        """Test execute raises error when response missing improvement_suggestions."""
        mock_load_prompt.return_value = "Data integrity review prompt template"
        mock_format_prompt.return_value = "Formatted prompt"
        mock_call_llm.return_value = {"content": json.dumps({"issues_found": []})}

        with pytest.raises(AgentExecutionError) as exc_info:
            agent.execute(design_spec)

        assert "Response missing 'improvement_suggestions' field" in str(exc_info.value)


class TestDataIntegrityReviewAgentEdgeCases:
    """Test Data Integrity Review Agent edge cases."""

    @pytest.fixture
    def agent(self):
        """Create Data Integrity Review Agent instance."""
        return DataIntegrityReviewAgent(db_path=":memory:")

    @patch.object(DataIntegrityReviewAgent, "load_prompt")
    @patch.object(DataIntegrityReviewAgent, "format_prompt")
    @patch.object(DataIntegrityReviewAgent, "call_llm")
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
                    category="Data Integrity",
                    severity="Critical",
                    description="Edge case checklist item for validation purposes",
                    validation_criteria="Edge case validation criteria applied",
                ),
                DesignReviewChecklistItem(
                    checklist_item_id="CHECK-002",
                    category="Data Integrity",
                    severity="High",
                    description="Edge case checklist item for comprehensive testing",
                    validation_criteria="Edge case validation criteria checked",
                ),
                DesignReviewChecklistItem(
                    checklist_item_id="CHECK-003",
                    category="Data Integrity",
                    severity="Medium",
                    description="Edge case checklist item for medium severity cases",
                    validation_criteria="Edge case validation criteria validated",
                ),
                DesignReviewChecklistItem(
                    checklist_item_id="CHECK-004",
                    category="Data Integrity",
                    severity="Medium",
                    description="Edge case checklist item for additional test coverage",
                    validation_criteria="Edge case validation criteria confirmed",
                ),
                DesignReviewChecklistItem(
                    checklist_item_id="CHECK-005",
                    category="Data Integrity",
                    severity="Low",
                    description="Edge case checklist item for low severity verification",
                    validation_criteria="Edge case validation criteria ensured",
                ),
            ],
            architecture_overview="Edge case architecture overview for testing string response handling",
            technology_stack={"language": "Python"},
        )

        mock_load_prompt.return_value = "Data integrity review prompt template"
        mock_format_prompt.return_value = "Formatted prompt"
        mock_call_llm.return_value = {
            "content": '{"issues_found": [], "improvement_suggestions": []}'
        }

        result = agent.execute(design_spec)

        assert result["issues_found"] == []
        assert result["improvement_suggestions"] == []

    @patch.object(DataIntegrityReviewAgent, "load_prompt")
    @patch.object(DataIntegrityReviewAgent, "format_prompt")
    @patch.object(DataIntegrityReviewAgent, "call_llm")
    def test_execute_with_complex_schema(
        self, mock_call_llm, mock_format_prompt, mock_load_prompt, agent
    ):
        """Test execute handles complex schema with multiple tables and relationships."""
        design_spec = DesignSpecification(
            task_id="COMPLEX-SCHEMA-001",
            component_logic=[
                ComponentLogic(
                    component_name="ComplexDataService",
                    semantic_unit_id="SU-001",
                    responsibility="Manage complex multi-table data relationships",
                    interfaces=[{"method": "process_data"}],
                    implementation_notes="Handle multiple related tables",
                )
            ],
            data_schemas=[
                DataSchema(
                    table_name="users",
                    description="Database table storing information",
                    columns=[
                        {"name": "id", "type": "uuid", "constraints": ["PRIMARY KEY"]},
                        {"name": "email", "type": "varchar(255)", "constraints": ["UNIQUE", "NOT NULL"]},
                    ],
                    relationships=[],
                    
                ),
                DataSchema(
                    table_name="posts",
                    description="Database table storing information",
                    columns=[
                        {"name": "id", "type": "uuid", "constraints": ["PRIMARY KEY"]},
                        {"name": "user_id", "type": "uuid", "constraints": ["FOREIGN KEY", "NOT NULL"]},
                    ],
                    relationships=[
                        "ALTER TABLE posts ADD FOREIGN KEY (user_id) REFERENCES users(id)"
                    ],
                    
                ),
                DataSchema(
                    table_name="comments",
                    description="Database table storing information",
                    columns=[
                        {"name": "id", "type": "uuid", "constraints": ["PRIMARY KEY"]},
                        {"name": "post_id", "type": "uuid", "constraints": ["FOREIGN KEY", "NOT NULL"]},
                        {"name": "user_id", "type": "uuid", "constraints": ["FOREIGN KEY", "NOT NULL"]},
                    ],
                    relationships=[
                        "ALTER TABLE comments ADD FOREIGN KEY (post_id) REFERENCES posts(id)",
                        "ALTER TABLE comments ADD FOREIGN KEY (user_id) REFERENCES users(id)",
                    ],
                    
                ),
            ],
            design_review_checklist=[
                DesignReviewChecklistItem(
                    checklist_item_id="CHECK-001",
                    category="Data Integrity",
                    severity="Critical",
                    description="Complex schema checklist item",
                    validation_criteria="Complex schema validation",
                ),
                DesignReviewChecklistItem(
                    checklist_item_id="CHECK-002",
                    category="Data Integrity",
                    severity="High",
                    description="Additional checklist item for comprehensive review coverage",
                    validation_criteria="Validation criteria for completeness",
                ),
                DesignReviewChecklistItem(
                    checklist_item_id="CHECK-003",
                    category="Data Integrity",
                    severity="Medium",
                    description="Additional checklist item for thorough evaluation",
                    validation_criteria="Validation criteria for quality",
                ),
                DesignReviewChecklistItem(
                    checklist_item_id="CHECK-004",
                    category="Data Integrity",
                    severity="Medium",
                    description="Additional checklist item for detailed assessment",
                    validation_criteria="Validation criteria for standards",
                ),
                DesignReviewChecklistItem(
                    checklist_item_id="CHECK-005",
                    category="Data Integrity",
                    severity="Low",
                    description="Additional checklist item for complete verification",
                    validation_criteria="Validation criteria for best practices",
                ),
            ],
            architecture_overview="Complex multi-table schema with users, posts, and comments relationships",
            technology_stack={"database": "PostgreSQL"},
        )

        mock_load_prompt.return_value = "Data integrity review prompt template"
        mock_format_prompt.return_value = "Formatted prompt"
        mock_call_llm.return_value = {
            "content": json.dumps(
                {"issues_found": [], "improvement_suggestions": []}
            )
        }

        result = agent.execute(design_spec)

        assert "issues_found" in result
        assert "improvement_suggestions" in result
