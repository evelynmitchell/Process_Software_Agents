"""
Shared test fixtures for unit tests.

Provides factory functions for creating valid Pydantic model instances
that satisfy all validation requirements.
"""

from datetime import datetime

import pytest

from asp.models.code import GeneratedCode, GeneratedFile
from asp.models.code_review import (
    ChecklistItemReview as CodeChecklistItemReview,
    CodeImprovementSuggestion,
    CodeIssue,
    CodeReviewReport,
)
from asp.models.design import (
    APIContract,
    ComponentLogic,
    DataSchema,
    DesignReviewChecklistItem,
    DesignSpecification,
)
from asp.models.design_review import (
    ChecklistItemReview,
    DesignIssue,
    DesignReviewReport,
    ImprovementSuggestion,
)
from asp.models.planning import ProjectPlan, SemanticUnit


# ============================================================================
# SemanticUnit and ProjectPlan Fixtures
# ============================================================================


@pytest.fixture
def make_semantic_unit():
    """Factory fixture for creating valid SemanticUnit instances."""

    def _make(
        unit_id: str = "SU-001",
        description: str = "Implement test functionality for the component module",
        api_interactions: int = 2,
        data_transformations: int = 1,
        logical_branches: int = 3,
        code_entities_modified: int = 2,
        novelty_multiplier: float = 1.0,
        est_complexity: int = 10,
        dependencies: list[str] | None = None,
    ) -> SemanticUnit:
        return SemanticUnit(
            unit_id=unit_id,
            description=description,
            api_interactions=api_interactions,
            data_transformations=data_transformations,
            logical_branches=logical_branches,
            code_entities_modified=code_entities_modified,
            novelty_multiplier=novelty_multiplier,
            est_complexity=est_complexity,
            dependencies=dependencies or [],
        )

    return _make


@pytest.fixture
def sample_semantic_unit(make_semantic_unit):
    """A sample SemanticUnit for testing."""
    return make_semantic_unit()


@pytest.fixture
def make_project_plan(make_semantic_unit):
    """Factory fixture for creating valid ProjectPlan instances."""

    def _make(
        task_id: str = "TASK-001",
        project_id: str | None = None,
        semantic_units: list[SemanticUnit] | None = None,
        total_est_complexity: int | None = None,
    ) -> ProjectPlan:
        units = semantic_units or [make_semantic_unit()]
        complexity = total_est_complexity or sum(u.est_complexity for u in units)
        return ProjectPlan(
            task_id=task_id,
            project_id=project_id,
            semantic_units=units,
            total_est_complexity=complexity,
        )

    return _make


@pytest.fixture
def sample_project_plan(make_project_plan):
    """A sample ProjectPlan for testing."""
    return make_project_plan()


# ============================================================================
# Design Specification Fixtures
# ============================================================================


@pytest.fixture
def make_api_contract():
    """Factory fixture for creating valid APIContract instances."""

    def _make(
        endpoint: str = "/api/test",
        method: str = "GET",
        description: str = "Test endpoint for retrieving data from the system",
        request_schema: dict | None = None,
        response_schema: dict | None = None,
        semantic_unit_id: str = "SU-001",
        authentication_required: bool = False,
    ) -> APIContract:
        return APIContract(
            endpoint=endpoint,
            method=method,
            description=description,
            request_schema=request_schema or {},
            response_schema=response_schema or {"status": "string"},
            semantic_unit_id=semantic_unit_id,
            authentication_required=authentication_required,
        )

    return _make


@pytest.fixture
def make_data_schema():
    """Factory fixture for creating valid DataSchema instances."""

    def _make(
        table_name: str = "users",
        description: str = "User table for storing user account data",
        columns: list[dict] | None = None,
        semantic_unit_id: str = "SU-001",
    ) -> DataSchema:
        return DataSchema(
            table_name=table_name,
            description=description,
            columns=columns
            or [
                {"name": "id", "type": "integer", "primary_key": True},
                {"name": "name", "type": "string"},
            ],
            semantic_unit_id=semantic_unit_id,
        )

    return _make


@pytest.fixture
def make_component_logic():
    """Factory fixture for creating valid ComponentLogic instances."""

    def _make(
        component_name: str = "TestComponent",
        semantic_unit_id: str = "SU-001",
        responsibility: str = "Handle test requests and return appropriate responses",
        interfaces: list[dict] | None = None,
        implementation_notes: str = "Use standard REST patterns for implementation",
        dependencies: list[str] | None = None,
    ) -> ComponentLogic:
        return ComponentLogic(
            component_name=component_name,
            semantic_unit_id=semantic_unit_id,
            responsibility=responsibility,
            interfaces=interfaces or [{"method": "get_data"}],
            implementation_notes=implementation_notes,
            dependencies=dependencies or [],
        )

    return _make


@pytest.fixture
def make_design_review_checklist():
    """Factory fixture for creating valid design review checklist."""

    def _make(count: int = 5) -> list[DesignReviewChecklistItem]:
        categories = ["Security", "API", "Data", "Error Handling", "Performance"]
        severities = ["Critical", "High", "Medium", "Medium", "Medium"]
        return [
            DesignReviewChecklistItem(
                category=categories[i % len(categories)],
                description=f"Validate {categories[i % len(categories)].lower()} requirements thoroughly",
                validation_criteria=f"Check that all {categories[i % len(categories)].lower()} standards are met",
                severity=severities[i % len(severities)],
            )
            for i in range(count)
        ]

    return _make


@pytest.fixture
def make_design_specification(
    make_api_contract, make_component_logic, make_design_review_checklist
):
    """Factory fixture for creating valid DesignSpecification instances."""

    def _make(
        task_id: str = "TASK-001",
        architecture_overview: str = "Test architecture overview for the design specification providing sufficient detail for implementation",
        technology_stack: dict | None = None,
        api_contracts: list[APIContract] | None = None,
        data_schemas: list[DataSchema] | None = None,
        component_logic: list[ComponentLogic] | None = None,
        design_review_checklist: list[DesignReviewChecklistItem] | None = None,
    ) -> DesignSpecification:
        return DesignSpecification(
            task_id=task_id,
            architecture_overview=architecture_overview,
            technology_stack=technology_stack or {"language": "Python"},
            api_contracts=api_contracts or [make_api_contract()],
            data_schemas=data_schemas or [],
            component_logic=component_logic or [make_component_logic()],
            design_review_checklist=design_review_checklist
            or make_design_review_checklist(),
        )

    return _make


@pytest.fixture
def sample_design_specification(make_design_specification):
    """A sample DesignSpecification for testing."""
    return make_design_specification()


# ============================================================================
# Design Review Fixtures
# ============================================================================


@pytest.fixture
def make_design_issue():
    """Factory fixture for creating valid DesignIssue instances."""

    def _make(
        issue_id: str = "ISSUE-001",
        category: str = "Security",
        severity: str = "Critical",
        description: str = "Security vulnerability found in authentication flow",
        affected_component: str = "AuthService",
        evidence: str = "Missing input validation on user credentials",
        impact: str = "Could allow unauthorized access to the system",
        recommendation: str = "Add input validation and sanitization",
    ) -> DesignIssue:
        return DesignIssue(
            issue_id=issue_id,
            category=category,
            severity=severity,
            description=description,
            affected_component=affected_component,
            evidence=evidence,
            impact=impact,
            recommendation=recommendation,
        )

    return _make


@pytest.fixture
def make_improvement_suggestion():
    """Factory fixture for creating valid ImprovementSuggestion instances."""

    def _make(
        suggestion_id: str = "IMPROVE-001",
        category: str = "Performance",
        priority: str = "High",
        description: str = "Optimize database query for better performance",
        affected_component: str = "DataService",
        current_approach: str = "Using sequential queries",
        suggested_approach: str = "Use batch queries or caching",
        expected_benefit: str = "50% reduction in response time",
        implementation_notes: str = "Consider using Redis for caching frequently accessed data",
    ) -> ImprovementSuggestion:
        return ImprovementSuggestion(
            suggestion_id=suggestion_id,
            category=category,
            priority=priority,
            description=description,
            affected_component=affected_component,
            current_approach=current_approach,
            suggested_approach=suggested_approach,
            expected_benefit=expected_benefit,
            implementation_notes=implementation_notes,
        )

    return _make


@pytest.fixture
def make_checklist_review():
    """Factory fixture for creating valid ChecklistItemReview instances."""

    def _make(
        checklist_item_id: str = "CHECK-001",
        category: str = "Security",
        description: str = "Validate security requirements for component",
        status: str = "Pass",
        notes: str = "All requirements have been verified and passed inspection",
    ) -> ChecklistItemReview:
        return ChecklistItemReview(
            checklist_item_id=checklist_item_id,
            category=category,
            description=description,
            status=status,
            notes=notes,
        )

    return _make


@pytest.fixture
def make_design_review_report(make_checklist_review):
    """Factory fixture for creating valid DesignReviewReport instances."""

    def _make(
        task_id: str = "TASK-001",
        review_id: str | None = None,
        design_id: str = "DESIGN-001",
        overall_assessment: str = "PASS",
        issues_found: list[DesignIssue] | None = None,
        improvement_suggestions: list[ImprovementSuggestion] | None = None,
        checklist_review: list[ChecklistItemReview] | None = None,
        critical_issue_count: int = 0,
        high_issue_count: int = 0,
        medium_issue_count: int = 0,
        low_issue_count: int = 0,
    ) -> DesignReviewReport:
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        return DesignReviewReport(
            task_id=task_id,
            review_id=review_id or f"REVIEW-{task_id}-{timestamp}",
            design_id=design_id,
            overall_assessment=overall_assessment,
            automated_checks={"syntax": True, "security": True},
            issues_found=issues_found or [],
            improvement_suggestions=improvement_suggestions or [],
            checklist_review=checklist_review or [make_checklist_review()],
            critical_issue_count=critical_issue_count,
            high_issue_count=high_issue_count,
            medium_issue_count=medium_issue_count,
            low_issue_count=low_issue_count,
            reviewer_agent="DesignReviewAgent",
            agent_version="1.0.0",
        )

    return _make


@pytest.fixture
def sample_design_review_report(make_design_review_report):
    """A sample DesignReviewReport for testing."""
    return make_design_review_report()


# ============================================================================
# Code Generation Fixtures
# ============================================================================


@pytest.fixture
def make_generated_file():
    """Factory fixture for creating valid GeneratedFile instances."""

    def _make(
        file_path: str = "src/main.py",
        file_type: str = "source",
        content: str = "print('Hello, World!')",
        lines_of_code: int = 1,
        semantic_unit_id: str = "SU-001",
        description: str = "Main entry point for the application",
    ) -> GeneratedFile:
        return GeneratedFile(
            file_path=file_path,
            file_type=file_type,
            content=content,
            lines_of_code=lines_of_code,
            semantic_unit_id=semantic_unit_id,
            description=description,
        )

    return _make


@pytest.fixture
def make_generated_code(make_generated_file):
    """Factory fixture for creating valid GeneratedCode instances."""

    def _make(
        task_id: str = "TASK-001",
        design_specification_id: str = "DESIGN-001",
        files: list[GeneratedFile] | None = None,
        file_structure: dict | None = None,
        implementation_notes: str = "This implementation follows best practices and design patterns for maintainability",
        dependencies: list[str] | None = None,
        total_files: int | None = None,
        total_lines_of_code: int | None = None,
    ) -> GeneratedCode:
        files_list = files or [make_generated_file()]
        return GeneratedCode(
            task_id=task_id,
            design_specification_id=design_specification_id,
            files=files_list,
            file_structure=file_structure or {"src": ["main.py"]},
            implementation_notes=implementation_notes,
            dependencies=dependencies or [],
            total_files=total_files or len(files_list),
            total_lines_of_code=total_lines_of_code
            or sum(f.lines_of_code for f in files_list),
        )

    return _make


@pytest.fixture
def sample_generated_code(make_generated_code):
    """A sample GeneratedCode for testing."""
    return make_generated_code()


# ============================================================================
# Code Review Fixtures
# ============================================================================


@pytest.fixture
def make_code_issue():
    """Factory fixture for creating valid CodeIssue instances."""

    def _make(
        issue_id: str = "CODE-ISSUE-001",
        category: str = "Security",
        severity: str = "Critical",
        description: str = "SQL injection vulnerability in query construction",
        file_path: str = "src/database.py",
        line_number: int = 42,
        code_snippet: str = "query = f'SELECT * FROM users WHERE id = {user_id}'",
        impact: str = "Allows malicious users to execute arbitrary SQL",
        recommendation: str = "Use parameterized queries instead",
        affected_phase: str = "Code",
    ) -> CodeIssue:
        return CodeIssue(
            issue_id=issue_id,
            category=category,
            severity=severity,
            description=description,
            file_path=file_path,
            line_number=line_number,
            code_snippet=code_snippet,
            impact=impact,
            recommendation=recommendation,
            affected_phase=affected_phase,
        )

    return _make


@pytest.fixture
def make_code_improvement_suggestion():
    """Factory fixture for creating valid CodeImprovementSuggestion instances."""

    def _make(
        suggestion_id: str = "CODE-IMPROVE-001",
        category: str = "Performance",
        priority: str = "High",
        description: str = "Use connection pooling for database connections",
        file_path: str = "src/database.py",
        current_code: str = "conn = create_connection()",
        suggested_code: str = "conn = pool.get_connection()",
        rationale: str = "Reduces connection overhead and improves throughput",
        implementation_notes: str = "Add SQLAlchemy connection pool configuration",
    ) -> CodeImprovementSuggestion:
        return CodeImprovementSuggestion(
            suggestion_id=suggestion_id,
            category=category,
            priority=priority,
            description=description,
            file_path=file_path,
            current_code=current_code,
            suggested_code=suggested_code,
            rationale=rationale,
            implementation_notes=implementation_notes,
        )

    return _make


@pytest.fixture
def make_code_review_report():
    """Factory fixture for creating valid CodeReviewReport instances."""

    def _make(
        task_id: str = "TASK-001",
        review_id: str | None = None,
        review_status: str = "PASS",
        issues_found: list[CodeIssue] | None = None,
        improvement_suggestions: list[CodeImprovementSuggestion] | None = None,
        critical_count: int = 0,
        high_count: int = 0,
        medium_count: int = 0,
        low_count: int = 0,
        total_issues: int = 0,
    ) -> CodeReviewReport:
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        return CodeReviewReport(
            task_id=task_id,
            review_id=review_id or f"CODE-REVIEW-{task_id}-{timestamp}",
            review_timestamp=datetime.now().isoformat(),
            review_status=review_status,
            issues_found=issues_found or [],
            improvement_suggestions=improvement_suggestions or [],
            critical_count=critical_count,
            high_count=high_count,
            medium_count=medium_count,
            low_count=low_count,
            total_issues=total_issues,
            agent_version="1.0.0",
        )

    return _make


@pytest.fixture
def sample_code_review_report(make_code_review_report):
    """A sample CodeReviewReport for testing."""
    return make_code_review_report()
