"""
Unit tests for Design models (asp.models.design).

Tests all Pydantic models used by the Design Agent:
- DesignInput: Input to Design Agent
- APIContract: API endpoint specification
- DataSchema: Database table specification
- ComponentLogic: Component/module specification
- DesignReviewChecklistItem: Review checklist item
- DesignSpecification: Complete design output

Coverage:
- Field validation (pattern, min_length, ranges)
- Required vs optional fields
- JSON serialization/deserialization
- Edge cases and error conditions

Author: ASP Test Team
Date: 2025-11-18
"""

import json

import pytest
from pydantic import ValidationError

from asp.models.design import (
    APIContract,
    ComponentLogic,
    DataSchema,
    DesignInput,
    DesignReviewChecklistItem,
    DesignSpecification,
)
from asp.models.planning import ProjectPlan, SemanticUnit

# =============================================================================
# Helper Functions
# =============================================================================


def create_test_project_plan(task_id="TEST-001"):
    """Create a minimal valid ProjectPlan for testing."""
    unit = SemanticUnit(
        unit_id="SU-001",
        description="Test semantic unit for testing",
        api_interactions=1,
        data_transformations=1,
        logical_branches=1,
        code_entities_modified=1,
        novelty_multiplier=1.0,
        est_complexity=10,
    )
    return ProjectPlan(
        task_id=task_id,
        semantic_units=[unit],
        total_est_complexity=10,
    )


# =============================================================================
# DesignInput Tests
# =============================================================================


class TestDesignInput:
    """Test DesignInput model."""

    def test_valid_design_input_minimal(self):
        """Test creating DesignInput with minimal fields."""
        design_input = DesignInput(
            task_id="TEST-001",
            requirements="This is a test requirement with sufficient length to pass validation",
            project_plan=create_test_project_plan("TEST-001"),
        )

        assert design_input.task_id == "TEST-001"
        assert len(design_input.requirements) >= 20
        assert design_input.project_plan.task_id == "TEST-001"
        assert design_input.context_files == []
        assert design_input.design_constraints is None

    def test_valid_design_input_full(self):
        """Test creating DesignInput with all fields."""
        design_input = DesignInput(
            task_id="JWT-AUTH-001",
            requirements="Build a comprehensive JWT authentication system with user registration and login",
            project_plan=create_test_project_plan("JWT-AUTH-001"),
            context_files=["Claude.md", "ARCHITECTURE.md"],
            design_constraints="Use FastAPI framework and PostgreSQL database",
        )

        assert design_input.task_id == "JWT-AUTH-001"
        assert len(design_input.context_files) == 2
        assert design_input.design_constraints is not None

    def test_design_input_task_id_too_short(self):
        """Test that task_id must be at least 3 characters."""
        with pytest.raises(ValidationError):
            DesignInput(
                task_id="AB",  # Too short
                requirements="This is a test requirement with sufficient length",
                project_plan=create_test_project_plan("AB"),
            )

    def test_design_input_requirements_too_short(self):
        """Test that requirements must be at least 20 characters."""
        with pytest.raises(ValidationError):
            DesignInput(
                task_id="TEST-001",
                requirements="Short req",  # Too short (< 20 chars)
                project_plan=create_test_project_plan("TEST-001"),
            )

    def test_design_input_missing_required_fields(self):
        """Test that required fields cannot be omitted."""
        with pytest.raises(ValidationError):
            DesignInput(
                task_id="TEST-001",
                requirements="This is a test requirement with sufficient length",
                # Missing project_plan
            )

    def test_design_input_json_serialization(self):
        """Test JSON serialization and deserialization."""
        design_input = DesignInput(
            task_id="TEST-001",
            requirements="This is a test requirement with sufficient length to pass validation",
            project_plan=create_test_project_plan("TEST-001"),
            context_files=["test.md"],
        )

        # Serialize
        json_str = design_input.model_dump_json()
        json_data = json.loads(json_str)

        assert json_data["task_id"] == "TEST-001"
        assert json_data["context_files"] == ["test.md"]

        # Deserialize
        restored = DesignInput.model_validate_json(json_str)
        assert restored.task_id == design_input.task_id


# =============================================================================
# APIContract Tests
# =============================================================================


class TestAPIContract:
    """Test APIContract model."""

    def test_valid_api_contract(self):
        """Test creating valid APIContract."""
        contract = APIContract(
            endpoint="/api/v1/users",
            method="POST",
            description="Register a new user with email and password",
            request_schema={"email": "string", "password": "string"},
            response_schema={"user_id": "string", "email": "string"},
            authentication_required=False,
        )

        assert contract.endpoint == "/api/v1/users"
        assert contract.method == "POST"
        assert contract.authentication_required is False
        assert contract.request_params is None
        assert contract.rate_limit is None

    def test_api_contract_with_all_fields(self):
        """Test APIContract with all optional fields."""
        contract = APIContract(
            endpoint="/api/v1/auth/login",
            method="POST",
            description="Authenticate user and return JWT token",
            request_schema={"email": "string", "password": "string"},
            request_params={"session_id": "string"},
            response_schema={"token": "string", "expires_at": "timestamp"},
            error_responses=[
                {"status": 401, "code": "INVALID_CREDENTIALS"},
                {"status": 429, "code": "RATE_LIMITED"},
            ],
            authentication_required=False,
            rate_limit="5 requests per minute",
        )

        assert len(contract.error_responses) == 2
        assert contract.rate_limit == "5 requests per minute"
        assert contract.request_params is not None

    def test_api_contract_method_validation(self):
        """Test that method must be valid HTTP method."""
        # Valid methods
        for method in ["GET", "POST", "PUT", "DELETE", "PATCH"]:
            contract = APIContract(
                endpoint="/api/test",
                method=method,
                description="Test endpoint for validation purposes",
                response_schema={"result": "ok"},
            )
            assert contract.method == method

        # Invalid method
        with pytest.raises(ValidationError):
            APIContract(
                endpoint="/api/test",
                method="INVALID",  # Not a valid HTTP method
                description="Test endpoint for validation",
                response_schema={"result": "ok"},
            )

    def test_api_contract_description_too_short(self):
        """Test that description must be at least 10 characters."""
        with pytest.raises(ValidationError):
            APIContract(
                endpoint="/api/test",
                method="GET",
                description="Short",  # Too short (< 10 chars)
                response_schema={"result": "ok"},
            )

    def test_api_contract_json_serialization(self):
        """Test JSON serialization and deserialization."""
        contract = APIContract(
            endpoint="/api/v1/users",
            method="POST",
            description="Register a new user with email and password",
            response_schema={"user_id": "string"},
        )

        # Serialize
        json_str = contract.model_dump_json()
        json_data = json.loads(json_str)

        assert json_data["endpoint"] == "/api/v1/users"
        assert json_data["method"] == "POST"

        # Deserialize
        restored = APIContract.model_validate_json(json_str)
        assert restored == contract


# =============================================================================
# DataSchema Tests
# =============================================================================


class TestDataSchema:
    """Test DataSchema model."""

    def test_valid_data_schema_minimal(self):
        """Test creating DataSchema with minimal fields."""
        schema = DataSchema(
            table_name="users",
            description="Stores user account information and credentials",
            columns=[
                {"name": "id", "type": "INTEGER", "constraints": "PRIMARY KEY"},
                {"name": "email", "type": "VARCHAR(255)", "constraints": "NOT NULL"},
            ],
        )

        assert schema.table_name == "users"
        assert len(schema.columns) == 2
        assert schema.indexes == []
        assert schema.relationships == []
        assert schema.constraints == []

    def test_valid_data_schema_with_relationships(self):
        """Test DataSchema with indexes, relationships, and constraints."""
        schema = DataSchema(
            table_name="posts",
            description="Stores blog posts created by users with metadata",
            columns=[
                {"name": "post_id", "type": "UUID", "constraints": "PRIMARY KEY"},
                {"name": "user_id", "type": "UUID", "constraints": "NOT NULL"},
                {"name": "title", "type": "VARCHAR(255)", "constraints": "NOT NULL"},
            ],
            indexes=["CREATE INDEX idx_posts_user_id ON posts(user_id)"],
            relationships=[
                "ALTER TABLE posts ADD FOREIGN KEY (user_id) REFERENCES users(user_id)"
            ],
            constraints=["CHECK (LENGTH(title) >= 5)"],
        )

        assert schema.table_name == "posts"
        assert len(schema.indexes) == 1
        assert len(schema.relationships) == 1
        assert len(schema.constraints) == 1

    def test_data_schema_description_too_short(self):
        """Test that description must be at least 10 characters."""
        with pytest.raises(ValidationError):
            DataSchema(
                table_name="users",
                description="Users",  # Too short (< 10 chars)
                columns=[{"name": "id", "type": "INTEGER"}],
            )

    def test_data_schema_columns_required(self):
        """Test that columns list cannot be empty."""
        with pytest.raises(ValidationError):
            DataSchema(
                table_name="users",
                description="Stores user information in the database",
                columns=[],  # Empty columns list
            )

    def test_data_schema_json_serialization(self):
        """Test JSON serialization and deserialization."""
        schema = DataSchema(
            table_name="users",
            description="Stores user account information and credentials",
            columns=[{"name": "id", "type": "INTEGER"}],
            indexes=["CREATE INDEX idx_users_id ON users(id)"],
        )

        # Serialize
        json_str = schema.model_dump_json()
        json_data = json.loads(json_str)

        assert json_data["table_name"] == "users"
        assert len(json_data["indexes"]) == 1

        # Deserialize
        restored = DataSchema.model_validate_json(json_str)
        assert restored == schema


# =============================================================================
# ComponentLogic Tests
# =============================================================================


class TestComponentLogic:
    """Test ComponentLogic model."""

    def test_valid_component_logic(self):
        """Test creating valid ComponentLogic."""
        component = ComponentLogic(
            component_name="UserAuthService",
            semantic_unit_id="SU-001",
            responsibility="Handles user authentication and JWT token generation",
            interfaces=[
                {
                    "method": "authenticate",
                    "parameters": {"email": "str", "password": "str"},
                    "returns": "Optional[str]",
                }
            ],
            implementation_notes="Use bcrypt for password hashing with cost factor 12",
        )

        assert component.component_name == "UserAuthService"
        assert component.semantic_unit_id == "SU-001"
        assert len(component.interfaces) == 1
        assert component.dependencies == []
        assert component.complexity is None

    def test_component_logic_with_dependencies(self):
        """Test ComponentLogic with dependencies and complexity."""
        component = ComponentLogic(
            component_name="UserAuthService",
            semantic_unit_id="SU-042",
            responsibility="Handles user authentication and session management",
            interfaces=[{"method": "login", "parameters": {}, "returns": "str"}],
            dependencies=["DatabaseService", "PasswordHasher"],
            implementation_notes="Use JWT tokens with 1-hour expiration for stateless auth",
            complexity=75,
        )

        assert component.semantic_unit_id == "SU-042"
        assert len(component.dependencies) == 2
        assert component.complexity == 75

    def test_component_logic_semantic_unit_id_pattern(self):
        """Test that semantic_unit_id must match pattern ^SU-[0-9]{3}$."""
        # Valid patterns
        for unit_id in ["SU-001", "SU-042", "SU-999"]:
            component = ComponentLogic(
                component_name="TestComponent",
                semantic_unit_id=unit_id,
                responsibility="Test component for validation purposes here",
                interfaces=[{"method": "test", "parameters": {}, "returns": "None"}],
                implementation_notes="Test implementation notes for validation",
            )
            assert component.semantic_unit_id == unit_id

        # Invalid patterns
        for invalid_id in ["SU-1", "SU-1234", "SU001", "su-001"]:
            with pytest.raises(ValidationError):
                ComponentLogic(
                    component_name="TestComponent",
                    semantic_unit_id=invalid_id,
                    responsibility="Test component for validation",
                    interfaces=[{"method": "test"}],
                    implementation_notes="Test implementation notes",
                )

    def test_component_logic_responsibility_too_short(self):
        """Test that responsibility must be at least 10 characters."""
        with pytest.raises(ValidationError):
            ComponentLogic(
                component_name="TestComponent",
                semantic_unit_id="SU-001",
                responsibility="Test",  # Too short (< 10 chars)
                interfaces=[{"method": "test"}],
                implementation_notes="Test implementation notes for validation",
            )

    def test_component_logic_implementation_notes_too_short(self):
        """Test that implementation_notes must be at least 20 characters."""
        with pytest.raises(ValidationError):
            ComponentLogic(
                component_name="TestComponent",
                semantic_unit_id="SU-001",
                responsibility="Test component for validation purposes",
                interfaces=[{"method": "test"}],
                implementation_notes="Short",  # Too short (< 20 chars)
            )

    def test_component_logic_complexity_range(self):
        """Test that complexity must be between 1 and 1000."""
        # Valid complexity
        component = ComponentLogic(
            component_name="TestComponent",
            semantic_unit_id="SU-001",
            responsibility="Test component for validation purposes here",
            interfaces=[{"method": "test"}],
            implementation_notes="Test implementation notes for validation",
            complexity=500,
        )
        assert component.complexity == 500

        # Invalid complexity (too high)
        with pytest.raises(ValidationError):
            ComponentLogic(
                component_name="TestComponent",
                semantic_unit_id="SU-001",
                responsibility="Test component for validation",
                interfaces=[{"method": "test"}],
                implementation_notes="Test implementation notes",
                complexity=1500,  # > 1000
            )

    def test_component_logic_interfaces_optional(self):
        """Test that interfaces list can be empty (for simple modules)."""
        # Model was updated to allow empty interfaces with default_factory=list
        component = ComponentLogic(
            component_name="TestComponent",
            semantic_unit_id="SU-001",
            responsibility="Test component for validation purposes",
            interfaces=[],  # Empty list now allowed
            implementation_notes="Test implementation notes for validation",
        )
        assert component.interfaces == []

    def test_component_logic_json_serialization(self):
        """Test JSON serialization and deserialization."""
        component = ComponentLogic(
            component_name="UserAuthService",
            semantic_unit_id="SU-001",
            responsibility="Handles user authentication and JWT generation",
            interfaces=[{"method": "login"}],
            implementation_notes="Use bcrypt for password hashing with cost 12",
            complexity=50,
        )

        # Serialize
        json_str = component.model_dump_json()
        json_data = json.loads(json_str)

        assert json_data["component_name"] == "UserAuthService"
        assert json_data["complexity"] == 50

        # Deserialize
        restored = ComponentLogic.model_validate_json(json_str)
        assert restored.component_name == component.component_name


# =============================================================================
# DesignReviewChecklistItem Tests
# =============================================================================


class TestDesignReviewChecklistItem:
    """Test DesignReviewChecklistItem model."""

    def test_valid_checklist_item(self):
        """Test creating valid DesignReviewChecklistItem."""
        item = DesignReviewChecklistItem(
            category="Security",
            description="Verify password fields are hashed, never plaintext",
            validation_criteria="DataSchema must use 'password_hash' not 'password'",
            severity="Critical",
        )

        assert item.category == "Security"
        assert item.severity == "Critical"

    def test_checklist_item_default_severity(self):
        """Test that severity defaults to Medium."""
        item = DesignReviewChecklistItem(
            category="Architecture",
            description="Check separation of concerns across components",
            validation_criteria="Each component should have single responsibility",
        )

        assert item.severity == "Medium"

    def test_checklist_item_severity_validation(self):
        """Test that severity must be Critical, High, Medium, or Low."""
        # Valid severities
        for severity in ["Critical", "High", "Medium", "Low"]:
            item = DesignReviewChecklistItem(
                category="Test",
                description="Test checklist item for validation purposes",
                validation_criteria="Test validation criteria for checking",
                severity=severity,
            )
            assert item.severity == severity

        # Invalid severity
        with pytest.raises(ValidationError):
            DesignReviewChecklistItem(
                category="Test",
                description="Test checklist item for validation",
                validation_criteria="Test validation criteria",
                severity="Invalid",  # Not in allowed values
            )

    def test_checklist_item_description_too_short(self):
        """Test that description must be at least 10 characters."""
        with pytest.raises(ValidationError):
            DesignReviewChecklistItem(
                category="Test",
                description="Short",  # Too short (< 10 chars)
                validation_criteria="Test validation criteria for checking",
            )

    def test_checklist_item_validation_criteria_too_short(self):
        """Test that validation_criteria must be at least 10 characters."""
        with pytest.raises(ValidationError):
            DesignReviewChecklistItem(
                category="Test",
                description="Test checklist item for validation purposes",
                validation_criteria="Short",  # Too short (< 10 chars)
            )

    def test_checklist_item_json_serialization(self):
        """Test JSON serialization and deserialization."""
        item = DesignReviewChecklistItem(
            category="Performance",
            description="Verify database indexes for frequent queries",
            validation_criteria="All foreign keys must have corresponding indexes",
            severity="High",
        )

        # Serialize
        json_str = item.model_dump_json()
        json_data = json.loads(json_str)

        assert json_data["category"] == "Performance"
        assert json_data["severity"] == "High"

        # Deserialize
        restored = DesignReviewChecklistItem.model_validate_json(json_str)
        assert restored == item


# =============================================================================
# DesignSpecification Tests
# =============================================================================


class TestDesignSpecification:
    """Test DesignSpecification model."""

    def test_valid_design_specification_minimal(self):
        """Test creating DesignSpecification with minimal required fields."""
        component = ComponentLogic(
            component_name="TestComponent",
            semantic_unit_id="SU-001",
            responsibility="Handles test operations for validation purposes",
            interfaces=[{"method": "test"}],
            implementation_notes="Test implementation notes for validation purposes",
        )

        checklist = [
            DesignReviewChecklistItem(
                category="Security",
                description="Critical security check for validation purposes",
                validation_criteria="Validate that security requirements are met",
                severity="Critical",
            )
        ] + [
            DesignReviewChecklistItem(
                category=f"Category {i}",
                description=f"Check item {i} for validation purposes",
                validation_criteria=f"Validate that item {i} meets criteria",
            )
            for i in range(1, 5)
        ]

        spec = DesignSpecification(
            task_id="TEST-001",
            component_logic=[component],
            design_review_checklist=checklist,
            architecture_overview="This is a test architecture with sufficient detail to pass validation requirements",
            technology_stack={"language": "Python", "framework": "FastAPI"},
        )

        assert spec.task_id == "TEST-001"
        assert len(spec.component_logic) == 1
        assert len(spec.design_review_checklist) == 5
        assert spec.api_contracts == []
        assert spec.data_schemas == []
        assert spec.assumptions == []

    def test_valid_design_specification_complete(self):
        """Test DesignSpecification with all fields populated."""
        api_contract = APIContract(
            endpoint="/api/v1/users",
            method="POST",
            description="Register a new user account with email and password",
            response_schema={"user_id": "string"},
        )

        data_schema = DataSchema(
            table_name="users",
            description="Stores user account information and credentials",
            columns=[{"name": "id", "type": "INTEGER"}],
        )

        component = ComponentLogic(
            component_name="UserService",
            semantic_unit_id="SU-001",
            responsibility="Handles user registration and authentication",
            interfaces=[{"method": "register"}],
            implementation_notes="Use bcrypt for password hashing with cost factor 12",
        )

        checklist = [
            DesignReviewChecklistItem(
                category="Security",
                description="Critical security validation check for production",
                validation_criteria="Validate that all security requirements are met",
                severity="Critical",
            )
        ] + [
            DesignReviewChecklistItem(
                category=f"Category {i}",
                description=f"Check item number {i} for validation",
                validation_criteria=f"Validate that item number {i} meets all criteria",
            )
            for i in range(1, 6)
        ]

        spec = DesignSpecification(
            task_id="JWT-AUTH-001",
            api_contracts=[api_contract],
            data_schemas=[data_schema],
            component_logic=[component],
            design_review_checklist=checklist,
            architecture_overview="3-tier architecture with FastAPI REST layer, service layer, and PostgreSQL data layer for secure user management",
            technology_stack={
                "language": "Python 3.12",
                "framework": "FastAPI",
                "database": "PostgreSQL",
            },
            assumptions=["Email addresses are unique", "Passwords hashed with bcrypt"],
        )

        assert len(spec.api_contracts) == 1
        assert len(spec.data_schemas) == 1
        assert len(spec.component_logic) == 1
        assert len(spec.assumptions) == 2

    def test_design_specification_component_logic_required(self):
        """Test that component_logic cannot be empty."""
        checklist = [
            DesignReviewChecklistItem(
                category="Security",
                description="Critical security check for validation purposes",
                validation_criteria="Validate that security requirements are met",
                severity="Critical",
            )
        ] + [
            DesignReviewChecklistItem(
                category="Test",
                description=f"Test item {i} for validation purposes",
                validation_criteria=f"Validate item {i} meets criteria",
            )
            for i in range(1, 5)
        ]

        with pytest.raises(ValidationError):
            DesignSpecification(
                task_id="TEST-001",
                component_logic=[],  # Empty list
                design_review_checklist=checklist,
                architecture_overview="Test architecture overview with sufficient detail",
                technology_stack={"language": "Python"},
            )

    def test_design_specification_checklist_min_items(self):
        """Test that design_review_checklist requires at least 5 items."""
        component = ComponentLogic(
            component_name="TestComponent",
            semantic_unit_id="SU-001",
            responsibility="Test component for validation purposes here",
            interfaces=[{"method": "test"}],
            implementation_notes="Test implementation notes for validation",
        )

        # Valid: 5 items with at least one Critical
        checklist_valid = [
            DesignReviewChecklistItem(
                category="Security",
                description="Critical security check for validation purposes",
                validation_criteria="Validate that security requirements are met",
                severity="Critical",
            )
        ] + [
            DesignReviewChecklistItem(
                category="Test",
                description=f"Test item {i} for validation purposes",
                validation_criteria=f"Validate item {i} meets criteria",
            )
            for i in range(1, 5)
        ]

        spec = DesignSpecification(
            task_id="TEST-001",
            component_logic=[component],
            design_review_checklist=checklist_valid,
            architecture_overview="Test architecture overview with sufficient detail to pass validation",
            technology_stack={"language": "Python"},
        )
        assert len(spec.design_review_checklist) == 5

        # Invalid: 4 items (< 5)
        checklist_invalid = [
            DesignReviewChecklistItem(
                category="Test",
                description=f"Test item {i} for validation",
                validation_criteria=f"Validate item {i} criteria",
            )
            for i in range(4)
        ]

        with pytest.raises(ValidationError):
            DesignSpecification(
                task_id="TEST-001",
                component_logic=[component],
                design_review_checklist=checklist_invalid,  # Only 4 items
                architecture_overview="Test architecture overview with detail",
                technology_stack={"language": "Python"},
            )

    def test_design_specification_architecture_overview_too_short(self):
        """Test that architecture_overview must be at least 50 characters."""
        component = ComponentLogic(
            component_name="TestComponent",
            semantic_unit_id="SU-001",
            responsibility="Test component for validation purposes here",
            interfaces=[{"method": "test"}],
            implementation_notes="Test implementation notes for validation",
        )

        checklist = [
            DesignReviewChecklistItem(
                category="Security",
                description="Critical security check for validation purposes",
                validation_criteria="Validate that security requirements are met",
                severity="Critical",
            )
        ] + [
            DesignReviewChecklistItem(
                category="Test",
                description=f"Test item {i} for validation purposes",
                validation_criteria=f"Validate item {i} meets criteria",
            )
            for i in range(1, 5)
        ]

        with pytest.raises(ValidationError):
            DesignSpecification(
                task_id="TEST-001",
                component_logic=[component],
                design_review_checklist=checklist,
                architecture_overview="Short overview",  # < 50 chars
                technology_stack={"language": "Python"},
            )

    def test_design_specification_json_serialization(self):
        """Test JSON serialization and deserialization."""
        component = ComponentLogic(
            component_name="TestComponent",
            semantic_unit_id="SU-001",
            responsibility="Test component for validation purposes here",
            interfaces=[{"method": "test"}],
            implementation_notes="Test implementation notes for validation",
        )

        checklist = [
            DesignReviewChecklistItem(
                category="Security",
                description="Critical security check for validation purposes",
                validation_criteria="Validate that security requirements are met",
                severity="Critical",
            )
        ] + [
            DesignReviewChecklistItem(
                category="Test",
                description=f"Test item {i} for validation purposes",
                validation_criteria=f"Validate item {i} meets criteria",
            )
            for i in range(1, 5)
        ]

        spec = DesignSpecification(
            task_id="TEST-001",
            component_logic=[component],
            design_review_checklist=checklist,
            architecture_overview="Test architecture overview with sufficient detail to pass validation requirements",
            technology_stack={"language": "Python"},
        )

        # Serialize
        json_str = spec.model_dump_json()
        json_data = json.loads(json_str)

        assert json_data["task_id"] == "TEST-001"
        assert len(json_data["component_logic"]) == 1

        # Deserialize
        restored = DesignSpecification.model_validate_json(json_str)
        assert restored.task_id == spec.task_id


# =============================================================================
# Edge Cases
# =============================================================================


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_design_specification_with_many_components(self):
        """Test DesignSpecification with many API contracts, schemas, and components."""
        api_contracts = [
            APIContract(
                endpoint=f"/api/v1/resource{i}",
                method="GET",
                description=f"Get resource number {i} from the system",
                response_schema={"data": "object"},
            )
            for i in range(10)
        ]

        data_schemas = [
            DataSchema(
                table_name=f"table_{i}",
                description=f"Database table number {i} for storing data",
                columns=[{"name": "id", "type": "INTEGER"}],
            )
            for i in range(8)
        ]

        components = [
            ComponentLogic(
                component_name=f"Component{i}",
                semantic_unit_id=f"SU-{i:03d}",
                responsibility=f"Handles operations for component number {i}",
                interfaces=[{"method": f"method_{i}"}],
                implementation_notes=f"Implementation notes for component number {i}",
            )
            for i in range(15)
        ]

        checklist = [
            DesignReviewChecklistItem(
                category="Security",
                description="Critical security validation for production",
                validation_criteria="Validate all security requirements are met",
                severity="Critical",
            )
        ] + [
            DesignReviewChecklistItem(
                category=f"Category {i}",
                description=f"Review checklist item number {i} for validation",
                validation_criteria=f"Validate that checklist item number {i} passes",
            )
            for i in range(1, 10)
        ]

        spec = DesignSpecification(
            task_id="LARGE-001",
            api_contracts=api_contracts,
            data_schemas=data_schemas,
            component_logic=components,
            design_review_checklist=checklist,
            architecture_overview="Large-scale microservices architecture with multiple API endpoints, database schemas, and service components",
            technology_stack={"language": "Python", "framework": "FastAPI"},
        )

        assert len(spec.api_contracts) == 10
        assert len(spec.data_schemas) == 8
        assert len(spec.component_logic) == 15
        assert len(spec.design_review_checklist) == 10

    def test_api_contract_get_method_no_request_body(self):
        """Test APIContract with GET method (no request body)."""
        contract = APIContract(
            endpoint="/api/v1/users/{user_id}",
            method="GET",
            description="Retrieve user information by user ID from database",
            request_params={"user_id": "UUID path parameter"},
            response_schema={"user_id": "string", "email": "string"},
            authentication_required=True,
        )

        assert contract.method == "GET"
        assert contract.request_schema is None
        assert contract.request_params is not None
        assert contract.authentication_required is True

    def test_component_logic_maximum_complexity(self):
        """Test ComponentLogic at maximum complexity boundary."""
        component = ComponentLogic(
            component_name="ComplexComponent",
            semantic_unit_id="SU-999",
            responsibility="Handles extremely complex operations for the system",
            interfaces=[{"method": "complex_operation"}],
            implementation_notes="Highly complex implementation requiring careful design and testing",
            complexity=1000,  # Maximum allowed
        )

        assert component.complexity == 1000
