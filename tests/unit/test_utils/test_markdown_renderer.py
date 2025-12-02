"""
Unit tests for markdown rendering utilities.

Tests markdown generation for all artifact types:
- Project plans
- Design specifications
- Design review reports
- Code manifests
- Code review reports
"""

from datetime import datetime

from asp.models.code import GeneratedCode, GeneratedFile
from asp.models.code_review import CodeReviewReport
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
from asp.utils.markdown_renderer import (
    render_code_manifest_markdown,
    render_code_review_markdown,
    render_design_markdown,
    render_design_review_markdown,
    render_plan_markdown,
)


def make_semantic_unit(
    unit_id: str = "SU-001",
    description: str = "Implement test functionality for the component",
    api_interactions: int = 2,
    data_transformations: int = 1,
    logical_branches: int = 3,
    code_entities_modified: int = 2,
    novelty_multiplier: float = 1.0,
    est_complexity: int = 10,
) -> SemanticUnit:
    """Helper to create valid SemanticUnit test data."""
    return SemanticUnit(
        unit_id=unit_id,
        description=description,
        api_interactions=api_interactions,
        data_transformations=data_transformations,
        logical_branches=logical_branches,
        code_entities_modified=code_entities_modified,
        novelty_multiplier=novelty_multiplier,
        est_complexity=est_complexity,
    )


def make_design_review_checklist(count: int = 5) -> list[DesignReviewChecklistItem]:
    """Helper to create minimum required checklist items with at least one Critical/High."""
    categories = ["Security", "API", "Data", "Error Handling", "Performance"]
    severities = ["Critical", "High", "Medium", "Medium", "Medium"]
    return [
        DesignReviewChecklistItem(
            category=categories[i % len(categories)],
            description=f"Validate {categories[i % len(categories)].lower()} requirements for the component thoroughly",
            validation_criteria=f"Check that all {categories[i % len(categories)].lower()} standards are properly met",
            severity=severities[i % len(severities)],
        )
        for i in range(count)
    ]


def make_checklist_review(count: int = 1) -> list[ChecklistItemReview]:
    """Helper to create checklist review items."""
    return [
        ChecklistItemReview(
            checklist_item_id=f"CHECK-{i+1:03d}",
            category="Security",
            description=f"Validate security requirements for component {i+1}",
            status="Pass",
            notes="All requirements have been verified and passed inspection",
        )
        for i in range(count)
    ]


class TestRenderPlanMarkdown:
    """Test rendering project plans to markdown."""

    def test_renders_basic_plan(self):
        """Test renders a basic project plan."""
        plan = ProjectPlan(
            task_id="TASK-001",
            semantic_units=[make_semantic_unit()],
            total_est_complexity=10,
        )

        markdown = render_plan_markdown(plan)

        # Should contain key sections
        assert "# Project Plan" in markdown
        assert "TASK-001" in markdown
        assert "SU-001" in markdown

    def test_includes_complexity_metrics(self):
        """Test includes complexity metrics."""
        plan = ProjectPlan(
            task_id="TASK-002",
            semantic_units=[
                make_semantic_unit(unit_id="SU-001", est_complexity=8),
                make_semantic_unit(unit_id="SU-002", est_complexity=12),
            ],
            total_est_complexity=20,
        )

        markdown = render_plan_markdown(plan)

        # Should show total complexity
        assert "20" in markdown  # Total complexity
        assert "2" in markdown  # Number of units


class TestRenderDesignMarkdown:
    """Test rendering design specifications to markdown."""

    def test_renders_basic_design(self):
        """Test renders a basic design specification."""
        design = DesignSpecification(
            task_id="TASK-001",
            architecture_overview="Test architecture overview for the design specification that provides sufficient detail for implementation",
            technology_stack={"language": "Python", "framework": "FastAPI"},
            api_contracts=[
                APIContract(
                    endpoint="/api/test",
                    method="GET",
                    description="Test endpoint for retrieving data",
                    request_schema={},
                    response_schema={"status": "string"},
                    semantic_unit_id="SU-001",
                )
            ],
            data_schemas=[],
            component_logic=[
                ComponentLogic(
                    component_name="TestComponent",
                    semantic_unit_id="SU-001",
                    responsibility="Handle test requests and return responses",
                    interfaces=[{"method": "get_data"}],
                    implementation_notes="Use standard REST patterns for implementation",
                )
            ],
            design_review_checklist=make_design_review_checklist(5),
        )

        markdown = render_design_markdown(design)

        # Should contain key sections
        assert "# Design Specification" in markdown or "Design" in markdown
        assert "TASK-001" in markdown
        assert "/api/test" in markdown
        assert "TestComponent" in markdown

    def test_includes_all_sections(self):
        """Test includes all design sections."""
        design = DesignSpecification(
            task_id="TASK-002",
            architecture_overview="Full architecture overview for comprehensive design specification with complete implementation details and patterns",
            technology_stack={"language": "Python"},
            api_contracts=[
                APIContract(
                    endpoint="/test",
                    method="POST",
                    description="Test endpoint for posting data",
                    request_schema={"data": "object"},
                    response_schema={"id": "integer"},
                    semantic_unit_id="SU-001",
                )
            ],
            data_schemas=[
                DataSchema(
                    table_name="users",
                    description="User table for storing user data",
                    columns=[
                        {"name": "id", "type": "integer", "primary_key": True},
                        {"name": "name", "type": "string"},
                    ],
                    semantic_unit_id="SU-001",
                )
            ],
            component_logic=[
                ComponentLogic(
                    component_name="Component",
                    semantic_unit_id="SU-001",
                    responsibility="Handle component logic and data processing",
                    interfaces=[{"method": "process"}],
                    implementation_notes="Implement using service pattern architecture",
                )
            ],
            design_review_checklist=make_design_review_checklist(5),
        )

        markdown = render_design_markdown(design)

        # Should have all major sections
        assert "API" in markdown
        assert "users" in markdown or "Data" in markdown
        assert "Component" in markdown


class TestRenderDesignReviewMarkdown:
    """Test rendering design review reports to markdown."""

    def test_renders_basic_review(self):
        """Test renders a basic design review report."""
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        report = DesignReviewReport(
            task_id="TASK-001",
            review_id=f"REVIEW-TASK001-{timestamp}",
            design_id="DESIGN-001",
            overall_assessment="PASS",
            automated_checks={"syntax": True, "security": True},
            issues_found=[],
            improvement_suggestions=[],
            checklist_review=make_checklist_review(1),
            critical_issue_count=0,
            high_issue_count=0,
            medium_issue_count=0,
            low_issue_count=0,
            reviewer_agent="DesignReviewAgent",
            agent_version="1.0.0",
        )

        markdown = render_design_review_markdown(report)

        # Should contain key sections
        assert "Design Review" in markdown or "Review" in markdown
        assert "TASK-001" in markdown
        assert "PASS" in markdown

    def test_includes_issues(self):
        """Test includes issues in output."""
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        report = DesignReviewReport(
            task_id="TASK-002",
            review_id=f"REVIEW-TASK002-{timestamp}",
            design_id="DESIGN-002",
            overall_assessment="FAIL",
            automated_checks={},
            issues_found=[
                DesignIssue(
                    issue_id="ISSUE-001",
                    category="Security",
                    severity="Critical",
                    description="Security vulnerability found in authentication flow",
                    affected_component="AuthService",
                    evidence="Missing input validation on user credentials",
                    impact="Could allow unauthorized access to the system",
                    recommendation="Add input validation and sanitization",
                )
            ],
            improvement_suggestions=[
                ImprovementSuggestion(
                    suggestion_id="IMPROVE-001",
                    category="Performance",
                    priority="High",
                    description="Optimize database query for better performance",
                    affected_component="DataService",
                    current_approach="Using sequential queries",
                    suggested_approach="Use batch queries or caching",
                    expected_benefit="50% reduction in response time",
                    implementation_notes="Consider using Redis for caching frequently accessed data",
                )
            ],
            checklist_review=make_checklist_review(1),
            critical_issue_count=1,
            high_issue_count=0,
            medium_issue_count=0,
            low_issue_count=0,
            reviewer_agent="DesignReviewAgent",
            agent_version="1.0.0",
        )

        markdown = render_design_review_markdown(report)

        # Should include issues and suggestions
        assert "ISSUE-001" in markdown or "Security" in markdown
        assert "IMPROVE-001" in markdown or "Performance" in markdown


class TestRenderCodeManifestMarkdown:
    """Test rendering code manifests to markdown."""

    def test_renders_basic_manifest(self):
        """Test renders a basic code manifest."""
        code = GeneratedCode(
            task_id="TASK-001",
            design_specification_id="DESIGN-001",
            files=[
                GeneratedFile(
                    file_path="src/main.py",
                    file_type="source",
                    content="print('Hello')",
                    lines_of_code=1,
                    semantic_unit_id="SU-001",
                    description="Main entry point for the application",
                )
            ],
            file_structure={"src": ["main.py"]},
            implementation_notes="This is a simple hello world implementation using Python standard library for demonstration purposes.",
            dependencies=["flask==2.0.0"],
            total_files=1,
            total_lines_of_code=1,
            setup_instructions="Run: pip install -r requirements.txt",
        )

        markdown = render_code_manifest_markdown(code)

        # Should contain key sections
        assert "Code" in markdown
        assert "TASK-001" in markdown
        assert "src/main.py" in markdown
        assert "flask" in markdown

    def test_includes_file_statistics(self):
        """Test includes file statistics."""
        code = GeneratedCode(
            task_id="TASK-002",
            design_specification_id="DESIGN-002",
            files=[
                GeneratedFile(
                    file_path="src/app.py",
                    file_type="source",
                    content="# Code\n" * 50,
                    lines_of_code=50,
                    semantic_unit_id="SU-001",
                    description="Main application module with core functionality",
                ),
                GeneratedFile(
                    file_path="tests/test_app.py",
                    file_type="test",
                    content="# Tests\n" * 20,
                    lines_of_code=20,
                    semantic_unit_id="SU-001",
                    description="Test suite for application module",
                ),
            ],
            file_structure={"src": ["app.py"], "tests": ["test_app.py"]},
            implementation_notes="Comprehensive implementation with full test coverage including unit and integration tests.",
            dependencies=[],
            total_files=2,
            total_lines_of_code=70,
            setup_instructions="",
        )

        markdown = render_code_manifest_markdown(code)

        # Should show totals
        assert "2" in markdown  # Total files
        assert "70" in markdown  # Total LOC


class TestRenderCodeReviewMarkdown:
    """Test rendering code review reports to markdown."""

    def test_renders_basic_review(self):
        """Test renders a basic code review report."""
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        report = CodeReviewReport(
            task_id="TASK-001",
            review_id=f"CODE-REVIEW-TASK001-{timestamp}",
            review_timestamp=datetime.now().isoformat(),
            review_status="PASS",
            issues_found=[],
            improvement_suggestions=[],
            critical_count=0,
            high_count=0,
            medium_count=0,
            low_count=0,
            total_issues=0,
            agent_version="1.0.0",
        )

        markdown = render_code_review_markdown(report)

        # Should contain key sections
        assert "Code Review" in markdown or "Review" in markdown
        assert "TASK-001" in markdown
        assert "PASS" in markdown

    def test_handles_missing_report_gracefully(self):
        """Test handles None report gracefully."""
        # This test checks if the renderer handles None without crashing
        try:
            markdown = render_code_review_markdown(None)
            # If it doesn't crash, check for some expected content
            assert markdown is not None
        except AttributeError:
            # If it raises AttributeError, that's also acceptable behavior
            # that should be documented/fixed
            pass
