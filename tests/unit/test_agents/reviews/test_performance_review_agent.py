"""
Unit tests for Performance Review Agent (FR-003).

Tests the specialist agent that reviews design specifications for performance issues:
- Database indexing and query optimization
- Caching strategies
- Scalability and horizontal scaling
- Resource utilization (memory, CPU)
- Batch vs real-time processing decisions
"""

import json
import logging
from unittest.mock import MagicMock, patch

import pytest

from asp.agents.base_agent import AgentExecutionError
from asp.agents.reviews.performance_review_agent import PerformanceReviewAgent
from asp.models.design import (
    APIContract,
    ComponentLogic,
    DataSchema,
    DesignReviewChecklistItem,
    DesignSpecification,
)


class TestPerformanceReviewAgentInitialization:
    """Test Performance Review Agent initialization."""

    def test_initialization_with_defaults(self):
        """Test agent initializes with default values."""
        agent = PerformanceReviewAgent()

        assert agent.agent_version == "1.0.0"

    def test_initialization_with_custom_llm_client(self):
        """Test agent initializes with custom LLM client."""
        mock_client = MagicMock()
        agent = PerformanceReviewAgent(llm_client=mock_client)

        assert agent.agent_version == "1.0.0"

    def test_initialization_with_custom_db_path(self):
        """Test agent initializes with custom database path."""
        agent = PerformanceReviewAgent(db_path=":memory:")

        assert agent.agent_version == "1.0.0"


class TestPerformanceReviewAgentExecute:
    """Test Performance Review Agent execute method."""

    @pytest.fixture
    def agent(self):
        """Create Performance Review Agent instance."""
        return PerformanceReviewAgent(db_path=":memory:")

    @pytest.fixture
    def design_spec(self):
        """Create a sample design specification."""
        return DesignSpecification(
            task_id="PERF-TEST-001",
            component_logic=[
                ComponentLogic(
                    component_name="UserService",
                    semantic_unit_id="SU-001",
                    responsibility="Manages user data operations",
                    interfaces=[{"method": "get_user", "parameters": ["user_id"]}],
                    implementation_notes="Fetch user from database",
                )
            ],
            api_contracts=[
                APIContract(
                    endpoint="/api/users/{id}",
                    method="GET",
                    description="Retrieve user by ID from database",
                    request_schema={"user_id": "string"},
                    response_schema={"user": "object"},
                    success_codes=[200],
                    error_codes=[404],
                    semantic_unit_ids=["SU-001"],
                )
            ],
            data_schemas=[
                DataSchema(
                    schema_name="users",
                    schema_type="table",
                    fields=[
                        {"name": "id", "type": "uuid", "constraints": ["PRIMARY KEY"]},
                        {"name": "email", "type": "varchar(255)", "constraints": []},
                        {"name": "name", "type": "varchar(100)", "constraints": []},
                    ],
                    relationships=[],
                    semantic_unit_ids=["SU-001"],
                )
            ],
            design_review_checklist=[
                DesignReviewChecklistItem(
                    checklist_item_id="CHECK-001",
                    category="Performance",
                    severity="Critical",
                    description="Database queries must have appropriate indexes",
                    validation_criteria="All WHERE, JOIN, and ORDER BY columns are indexed",
                ),
                DesignReviewChecklistItem(
                    checklist_item_id="CHECK-002",
                    category="Performance",
                    severity="High",
                    description="Frequently accessed data should be cached",
                    validation_criteria="Caching strategy defined for read-heavy endpoints",
                ),
                DesignReviewChecklistItem(
                    checklist_item_id="CHECK-003",
                    category="Performance",
                    severity="Medium",
                    description="Avoid N+1 query patterns",
                    validation_criteria="Related data fetched with joins or batch queries",
                ),
                DesignReviewChecklistItem(
                    checklist_item_id="CHECK-004",
                    category="Performance",
                    severity="Medium",
                    description="Use pagination for large result sets",
                    validation_criteria="List endpoints have limit/offset or cursor pagination",
                ),
                DesignReviewChecklistItem(
                    checklist_item_id="CHECK-005",
                    category="Performance",
                    severity="Low",
                    description="Consider async processing for long operations",
                    validation_criteria="Operations >1s should be async with status polling",
                ),
            ],
            architecture_overview="Simple CRUD API for user management with direct database access",
            technology_stack={
                "language": "Python",
                "framework": "FastAPI",
                "database": "PostgreSQL",
            },
        )

    @patch.object(PerformanceReviewAgent, "load_prompt")
    @patch.object(PerformanceReviewAgent, "format_prompt")
    @patch.object(PerformanceReviewAgent, "call_llm")
    def test_execute_returns_valid_response(
        self, mock_call_llm, mock_format_prompt, mock_load_prompt, agent, design_spec
    ):
        """Test execute returns valid response with issues and suggestions."""
        mock_load_prompt.return_value = "Performance review prompt template"
        mock_format_prompt.return_value = "Formatted prompt with design spec"
        mock_call_llm.return_value = {
            "content": json.dumps(
                {
                    "issues_found": [
                        {
                            "issue_id": "ISSUE-001",
                            "category": "Performance",
                            "severity": "High",
                            "description": "Missing database index on frequently queried email column",
                            "evidence": "users table email column has no index",
                            "impact": "Full table scans on every email lookup causing slow queries",
                            "affected_phase": "Design",
                        }
                    ],
                    "improvement_suggestions": [
                        {
                            "suggestion_id": "IMPROVE-001",
                            "related_issue_id": "ISSUE-001",
                            "category": "Performance",
                            "priority": "High",
                            "description": "Add index on users.email column for faster lookups",
                            "implementation_notes": "CREATE INDEX idx_users_email ON users(email) in migration script",
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
        assert result["issues_found"][0]["category"] == "Performance"

    @patch.object(PerformanceReviewAgent, "load_prompt")
    @patch.object(PerformanceReviewAgent, "format_prompt")
    @patch.object(PerformanceReviewAgent, "call_llm")
    def test_execute_with_no_issues_found(
        self, mock_call_llm, mock_format_prompt, mock_load_prompt, agent, design_spec
    ):
        """Test execute with clean design (no issues)."""
        mock_load_prompt.return_value = "Performance review prompt template"
        mock_format_prompt.return_value = "Formatted prompt"
        mock_call_llm.return_value = {
            "content": json.dumps(
                {"issues_found": [], "improvement_suggestions": []}
            )
        }

        result = agent.execute(design_spec)

        assert result["issues_found"] == []
        assert result["improvement_suggestions"] == []

    @patch.object(PerformanceReviewAgent, "load_prompt")
    @patch.object(PerformanceReviewAgent, "format_prompt")
    @patch.object(PerformanceReviewAgent, "call_llm")
    def test_execute_logs_review_metrics(
        self, mock_call_llm, mock_format_prompt, mock_load_prompt, agent, design_spec, caplog
    ):
        """Test execute logs performance review metrics."""
        mock_load_prompt.return_value = "Performance review prompt template"
        mock_format_prompt.return_value = "Formatted prompt"
        mock_call_llm.return_value = {
            "content": json.dumps(
                {
                    "issues_found": [
                        {
                            "issue_id": "ISSUE-001",
                            "category": "Performance",
                            "severity": "High",
                            "description": "Missing index on frequently queried column in database",
                            "evidence": "users.email has no index",
                            "impact": "Slow queries due to full table scans on every lookup",
                            "affected_phase": "Design",
                        }
                    ],
                    "improvement_suggestions": [],
                }
            )
        }

        with caplog.at_level(logging.INFO):
            agent.execute(design_spec)

        assert "Starting performance review for task PERF-TEST-001" in caplog.text
        assert "Performance review completed: found 1 issues, 0 suggestions" in caplog.text


class TestPerformanceReviewAgentDetection:
    """Test Performance Review Agent detection capabilities."""

    @pytest.fixture
    def agent(self):
        """Create Performance Review Agent instance."""
        return PerformanceReviewAgent(db_path=":memory:")

    @patch.object(PerformanceReviewAgent, "load_prompt")
    @patch.object(PerformanceReviewAgent, "format_prompt")
    @patch.object(PerformanceReviewAgent, "call_llm")
    def test_detect_missing_database_indexes(
        self, mock_call_llm, mock_format_prompt, mock_load_prompt, agent
    ):
        """Test detection of missing database indexes on frequently queried columns."""
        design_spec = DesignSpecification(
            task_id="PERF-INDEX-001",
            component_logic=[
                ComponentLogic(
                    component_name="UserLookupService",
                    semantic_unit_id="SU-001",
                    responsibility="Lookup users by email for authentication",
                    interfaces=[{"method": "find_by_email"}],
                    implementation_notes="SELECT * FROM users WHERE email = ? for login",
                )
            ],
            data_schemas=[
                DataSchema(
                    schema_name="users",
                    schema_type="table",
                    fields=[
                        {"name": "id", "type": "uuid", "constraints": ["PRIMARY KEY"]},
                        {"name": "email", "type": "varchar(255)", "constraints": []},
                    ],
                    relationships=[],
                    semantic_unit_ids=["SU-001"],
                )
            ],
            design_review_checklist=[
                DesignReviewChecklistItem(
                    checklist_item_id="CHECK-001",
                    category="Performance",
                    severity="Critical",
                    description="All WHERE clause columns must be indexed",
                    validation_criteria="Email column should have index",
                )
            ],
            architecture_overview="User authentication system with email lookup requiring fast query performance",
            technology_stack={"database": "PostgreSQL"},
        )

        mock_load_prompt.return_value = "Performance review template"
        mock_format_prompt.return_value = "Formatted prompt"
        mock_call_llm.return_value = {
            "content": json.dumps(
                {
                    "issues_found": [
                        {
                            "issue_id": "ISSUE-001",
                            "category": "Performance",
                            "severity": "Critical",
                            "description": "Missing index on users.email column used in WHERE clause",
                            "evidence": "UserLookupService queries users by email without index",
                            "impact": "Every login causes full table scan, degrading performance with user growth",
                            "affected_phase": "Design",
                        }
                    ],
                    "improvement_suggestions": [
                        {
                            "suggestion_id": "IMPROVE-001",
                            "related_issue_id": "ISSUE-001",
                            "category": "Performance",
                            "priority": "High",
                            "description": "Add unique index on users.email for fast authentication lookups",
                            "implementation_notes": "CREATE UNIQUE INDEX idx_users_email ON users(email); Also add application-level uniqueness validation",
                        }
                    ],
                }
            )
        }

        result = agent.execute(design_spec)

        assert len(result["issues_found"]) >= 1
        issue = result["issues_found"][0]
        assert issue["severity"] in ["Critical", "High"]
        assert "index" in issue["description"].lower()

    @patch.object(PerformanceReviewAgent, "load_prompt")
    @patch.object(PerformanceReviewAgent, "format_prompt")
    @patch.object(PerformanceReviewAgent, "call_llm")
    def test_detect_missing_caching_strategy(
        self, mock_call_llm, mock_format_prompt, mock_load_prompt, agent
    ):
        """Test detection of missing caching for frequently accessed data."""
        design_spec = DesignSpecification(
            task_id="PERF-CACHE-001",
            component_logic=[
                ComponentLogic(
                    component_name="ProductCatalogService",
                    semantic_unit_id="SU-001",
                    responsibility="Serve product catalog to all users",
                    interfaces=[{"method": "get_products"}],
                    implementation_notes="Query database for product list on every request",
                )
            ],
            api_contracts=[
                APIContract(
                    endpoint="/api/products",
                    method="GET",
                    description="Get all products (called thousands of times per day)",
                    request_schema={},
                    response_schema={"products": "array"},
                    success_codes=[200],
                    error_codes=[],
                    semantic_unit_ids=["SU-001"],
                )
            ],
            design_review_checklist=[
                DesignReviewChecklistItem(
                    checklist_item_id="CHECK-001",
                    category="Performance",
                    severity="High",
                    description="High-traffic read endpoints should use caching",
                    validation_criteria="Redis or in-memory cache for product catalog",
                )
            ],
            architecture_overview="E-commerce product catalog API with high read traffic and infrequent updates",
            technology_stack={"database": "PostgreSQL"},
        )

        mock_load_prompt.return_value = "Performance review template"
        mock_format_prompt.return_value = "Formatted prompt"
        mock_call_llm.return_value = {
            "content": json.dumps(
                {
                    "issues_found": [
                        {
                            "issue_id": "ISSUE-001",
                            "category": "Performance",
                            "severity": "High",
                            "description": "No caching strategy for high-traffic product catalog endpoint",
                            "evidence": "ProductCatalogService queries database on every request",
                            "impact": "Unnecessary database load, slow response times under high traffic",
                            "affected_phase": "Design",
                        }
                    ],
                    "improvement_suggestions": [
                        {
                            "suggestion_id": "IMPROVE-001",
                            "related_issue_id": "ISSUE-001",
                            "category": "Performance",
                            "priority": "High",
                            "description": "Implement Redis caching for product catalog with TTL",
                            "implementation_notes": "Cache product list in Redis with 5-minute TTL, invalidate on product updates",
                        }
                    ],
                }
            )
        }

        result = agent.execute(design_spec)

        assert len(result["issues_found"]) >= 1
        issue = result["issues_found"][0]
        assert "cach" in issue["description"].lower()

    @patch.object(PerformanceReviewAgent, "load_prompt")
    @patch.object(PerformanceReviewAgent, "format_prompt")
    @patch.object(PerformanceReviewAgent, "call_llm")
    def test_detect_n_plus_one_query_pattern(
        self, mock_call_llm, mock_format_prompt, mock_load_prompt, agent
    ):
        """Test detection of N+1 query antipattern."""
        design_spec = DesignSpecification(
            task_id="PERF-N1-001",
            component_logic=[
                ComponentLogic(
                    component_name="OrderDisplayService",
                    semantic_unit_id="SU-001",
                    responsibility="Display orders with customer details",
                    interfaces=[{"method": "get_orders_with_customers"}],
                    implementation_notes="Loop through orders, fetch customer for each order separately",
                )
            ],
            design_review_checklist=[
                DesignReviewChecklistItem(
                    checklist_item_id="CHECK-001",
                    category="Performance",
                    severity="High",
                    description="Avoid N+1 query patterns in data retrieval",
                    validation_criteria="Use JOIN or batch loading for related data",
                )
            ],
            architecture_overview="Order management system that displays customer information with each order",
            technology_stack={"database": "PostgreSQL"},
        )

        mock_load_prompt.return_value = "Performance review template"
        mock_format_prompt.return_value = "Formatted prompt"
        mock_call_llm.return_value = {
            "content": json.dumps(
                {
                    "issues_found": [
                        {
                            "issue_id": "ISSUE-001",
                            "category": "Performance",
                            "severity": "High",
                            "description": "N+1 query pattern when fetching orders with customer data",
                            "evidence": "OrderDisplayService loops through orders and queries customer table separately",
                            "impact": "100 orders = 101 queries (1 + 100), severe performance degradation",
                            "affected_phase": "Design",
                        }
                    ],
                    "improvement_suggestions": [
                        {
                            "suggestion_id": "IMPROVE-001",
                            "related_issue_id": "ISSUE-001",
                            "category": "Performance",
                            "priority": "High",
                            "description": "Use JOIN query to fetch orders with customer data in single query",
                            "implementation_notes": "SELECT orders.*, customers.* FROM orders JOIN customers ON orders.customer_id = customers.id",
                        }
                    ],
                }
            )
        }

        result = agent.execute(design_spec)

        assert len(result["issues_found"]) >= 1
        issue = result["issues_found"][0]
        assert issue["severity"] in ["Critical", "High"]

    @patch.object(PerformanceReviewAgent, "load_prompt")
    @patch.object(PerformanceReviewAgent, "format_prompt")
    @patch.object(PerformanceReviewAgent, "call_llm")
    def test_detect_inefficient_algorithm(
        self, mock_call_llm, mock_format_prompt, mock_load_prompt, agent
    ):
        """Test detection of inefficient algorithms or data structures."""
        design_spec = DesignSpecification(
            task_id="PERF-ALGO-001",
            component_logic=[
                ComponentLogic(
                    component_name="SearchService",
                    semantic_unit_id="SU-001",
                    responsibility="Search products by name prefix",
                    interfaces=[{"method": "search_by_prefix"}],
                    implementation_notes="Load all products into memory, iterate through with startswith() check",
                )
            ],
            design_review_checklist=[
                DesignReviewChecklistItem(
                    checklist_item_id="CHECK-001",
                    category="Performance",
                    severity="High",
                    description="Use efficient algorithms and data structures",
                    validation_criteria="O(log n) or better for search operations",
                )
            ],
            architecture_overview="Product search system handling millions of products with prefix matching",
            technology_stack={"language": "Python", "database": "PostgreSQL"},
        )

        mock_load_prompt.return_value = "Performance review template"
        mock_format_prompt.return_value = "Formatted prompt"
        mock_call_llm.return_value = {
            "content": json.dumps(
                {
                    "issues_found": [
                        {
                            "issue_id": "ISSUE-001",
                            "category": "Performance",
                            "severity": "High",
                            "description": "Inefficient O(n) linear search for prefix matching on large dataset",
                            "evidence": "SearchService loads all products and iterates with startswith()",
                            "impact": "Search becomes unusable with millions of products, high memory usage",
                            "affected_phase": "Design",
                        }
                    ],
                    "improvement_suggestions": [
                        {
                            "suggestion_id": "IMPROVE-001",
                            "related_issue_id": "ISSUE-001",
                            "category": "Performance",
                            "priority": "High",
                            "description": "Use database LIKE query with index or full-text search engine",
                            "implementation_notes": "Create trigram index: CREATE INDEX idx_products_name_trgm ON products USING gin(name gin_trgm_ops); Use query: SELECT * FROM products WHERE name LIKE 'prefix%' LIMIT 20",
                        }
                    ],
                }
            )
        }

        result = agent.execute(design_spec)

        assert len(result["issues_found"]) >= 1
        issue = result["issues_found"][0]
        assert issue["severity"] in ["Critical", "High"]


class TestPerformanceReviewAgentErrorHandling:
    """Test Performance Review Agent error handling."""

    @pytest.fixture
    def agent(self):
        """Create Performance Review Agent instance."""
        return PerformanceReviewAgent(db_path=":memory:")

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
                    implementation_notes="Test implementation",
                )
            ],
            design_review_checklist=[
                DesignReviewChecklistItem(
                    checklist_item_id="CHECK-001",
                    category="Performance",
                    severity="Critical",
                    description="Test checklist item",
                    validation_criteria="Test validation",
                )
            ],
            architecture_overview="Test architecture for error handling scenarios",
            technology_stack={"language": "Python"},
        )

    @patch.object(PerformanceReviewAgent, "load_prompt")
    @patch.object(PerformanceReviewAgent, "format_prompt")
    @patch.object(PerformanceReviewAgent, "call_llm")
    def test_execute_raises_error_on_invalid_json_response(
        self, mock_call_llm, mock_format_prompt, mock_load_prompt, agent, design_spec
    ):
        """Test execute raises error when LLM returns invalid JSON."""
        mock_load_prompt.return_value = "Performance review prompt template"
        mock_format_prompt.return_value = "Formatted prompt"
        mock_call_llm.return_value = {"content": "Invalid JSON {{{"}

        with pytest.raises(AgentExecutionError) as exc_info:
            agent.execute(design_spec)

        assert "Failed to parse performance review response" in str(exc_info.value)

    @patch.object(PerformanceReviewAgent, "load_prompt")
    @patch.object(PerformanceReviewAgent, "format_prompt")
    @patch.object(PerformanceReviewAgent, "call_llm")
    def test_execute_raises_error_on_missing_issues_found(
        self, mock_call_llm, mock_format_prompt, mock_load_prompt, agent, design_spec
    ):
        """Test execute raises error when response missing issues_found."""
        mock_load_prompt.return_value = "Performance review prompt template"
        mock_format_prompt.return_value = "Formatted prompt"
        mock_call_llm.return_value = {
            "content": json.dumps({"improvement_suggestions": []})
        }

        with pytest.raises(AgentExecutionError) as exc_info:
            agent.execute(design_spec)

        assert "Response missing 'issues_found' field" in str(exc_info.value)

    @patch.object(PerformanceReviewAgent, "load_prompt")
    @patch.object(PerformanceReviewAgent, "format_prompt")
    @patch.object(PerformanceReviewAgent, "call_llm")
    def test_execute_raises_error_on_missing_suggestions(
        self, mock_call_llm, mock_format_prompt, mock_load_prompt, agent, design_spec
    ):
        """Test execute raises error when response missing improvement_suggestions."""
        mock_load_prompt.return_value = "Performance review prompt template"
        mock_format_prompt.return_value = "Formatted prompt"
        mock_call_llm.return_value = {"content": json.dumps({"issues_found": []})}

        with pytest.raises(AgentExecutionError) as exc_info:
            agent.execute(design_spec)

        assert "Response missing 'improvement_suggestions' field" in str(exc_info.value)


class TestPerformanceReviewAgentEdgeCases:
    """Test Performance Review Agent edge cases."""

    @pytest.fixture
    def agent(self):
        """Create Performance Review Agent instance."""
        return PerformanceReviewAgent(db_path=":memory:")

    @patch.object(PerformanceReviewAgent, "load_prompt")
    @patch.object(PerformanceReviewAgent, "format_prompt")
    @patch.object(PerformanceReviewAgent, "call_llm")
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
                    implementation_notes="Test implementation",
                )
            ],
            design_review_checklist=[
                DesignReviewChecklistItem(
                    checklist_item_id="CHECK-001",
                    category="Performance",
                    severity="Critical",
                    description="Edge case checklist item",
                    validation_criteria="Edge case validation",
                )
            ],
            architecture_overview="Edge case architecture for testing string response handling",
            technology_stack={"language": "Python"},
        )

        mock_load_prompt.return_value = "Performance review prompt template"
        mock_format_prompt.return_value = "Formatted prompt"
        mock_call_llm.return_value = {
            "content": '{"issues_found": [], "improvement_suggestions": []}'
        }

        result = agent.execute(design_spec)

        assert result["issues_found"] == []
        assert result["improvement_suggestions"] == []

    @patch.object(PerformanceReviewAgent, "load_prompt")
    @patch.object(PerformanceReviewAgent, "format_prompt")
    @patch.object(PerformanceReviewAgent, "call_llm")
    def test_execute_with_large_number_of_issues(
        self, mock_call_llm, mock_format_prompt, mock_load_prompt, agent
    ):
        """Test execute handles large number of issues correctly."""
        design_spec = DesignSpecification(
            task_id="LARGE-001",
            component_logic=[
                ComponentLogic(
                    component_name="LargeComponent",
                    semantic_unit_id="SU-001",
                    responsibility="Component with many performance issues",
                    interfaces=[{"method": "test"}],
                    implementation_notes="Test implementation with many performance problems",
                )
            ],
            design_review_checklist=[
                DesignReviewChecklistItem(
                    checklist_item_id="CHECK-001",
                    category="Performance",
                    severity="Critical",
                    description="Large test checklist item",
                    validation_criteria="Large test validation",
                )
            ],
            architecture_overview="Architecture with many performance issues for testing large result handling",
            technology_stack={"language": "Python"},
        )

        mock_load_prompt.return_value = "Performance review prompt template"
        mock_format_prompt.return_value = "Formatted prompt"

        # Create 50 issues
        issues = [
            {
                "issue_id": f"ISSUE-{i:03d}",
                "category": "Performance",
                "severity": "Medium",
                "description": f"Performance issue number {i} found in the component design",
                "evidence": f"Evidence for performance issue number {i}",
                "impact": f"Impact of performance issue number {i} on system",
                "affected_phase": "Design",
            }
            for i in range(1, 51)
        ]

        mock_call_llm.return_value = {
            "content": json.dumps(
                {"issues_found": issues, "improvement_suggestions": []}
            )
        }

        result = agent.execute(design_spec)

        assert len(result["issues_found"]) == 50
        assert result["issues_found"][0]["issue_id"] == "ISSUE-001"
        assert result["issues_found"][49]["issue_id"] == "ISSUE-050"
