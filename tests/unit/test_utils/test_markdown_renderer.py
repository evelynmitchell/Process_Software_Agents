"""
Unit tests for markdown rendering utilities.

Tests markdown generation for all artifact types:
- Project plans
- Design specifications
- Design review reports
- Code manifests
- Code review reports
"""


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


class TestRenderPlanMarkdown:
    """Test rendering project plans to markdown."""

    def test_renders_basic_plan(self):
        """Test renders a basic project plan."""
        plan = ProjectPlan(
            task_id="TASK-001",
            description="Test task",
            semantic_units=[
                SemanticUnit(
                    unit_id="UNIT-001",
                    description="Test unit",
                    unit_type="Feature",
                    estimated_complexity=5,
                )
            ],
            total_est_complexity=5,
            total_semantic_units=1,
        )

        markdown = render_plan_markdown(plan)

        # Should contain key sections
        assert "# Project Plan" in markdown
        assert "TASK-001" in markdown
        assert "Test task" in markdown
        assert "UNIT-001" in markdown
        assert "Test unit" in markdown

    def test_includes_complexity_metrics(self):
        """Test includes complexity metrics."""
        plan = ProjectPlan(
            task_id="TASK-002",
            description="Test",
            semantic_units=[
                SemanticUnit(
                    unit_id="UNIT-001",
                    description="Unit 1",
                    unit_type="Feature",
                    estimated_complexity=3,
                ),
                SemanticUnit(
                    unit_id="UNIT-002",
                    description="Unit 2",
                    unit_type="Enhancement",
                    estimated_complexity=2,
                ),
            ],
            total_est_complexity=5,
            total_semantic_units=2,
        )

        markdown = render_plan_markdown(plan)

        # Should show total complexity
        assert "5" in markdown  # Total complexity
        assert "2" in markdown  # Number of units


class TestRenderDesignMarkdown:
    """Test rendering design specifications to markdown."""

    def test_renders_basic_design(self):
        """Test renders a basic design specification."""
        design = DesignSpecification(
            task_id="TASK-001",
            description="Test design",
            api_contracts=[
                APIContract(
                    endpoint="/api/test",
                    method="GET",
                    description="Test endpoint",
                    request_schema={},
                    response_schema={},
                    component_id="COMP-001",
                )
            ],
            data_schemas=[],
            component_logic=[
                ComponentLogic(
                    component_id="COMP-001",
                    component_name="TestComponent",
                    component_type="Controller",
                    semantic_unit_id="UNIT-001",
                    dependencies=[],
                    implementation_notes="Test notes",
                )
            ],
            design_checklist=[],
        )

        markdown = render_design_markdown(design)

        # Should contain key sections
        assert "# Design Specification" in markdown
        assert "TASK-001" in markdown
        assert "API Contracts" in markdown
        assert "/api/test" in markdown
        assert "TestComponent" in markdown

    def test_includes_all_sections(self):
        """Test includes all design sections."""
        design = DesignSpecification(
            task_id="TASK-002",
            description="Full design",
            api_contracts=[
                APIContract(
                    endpoint="/test",
                    method="POST",
                    description="Test",
                    request_schema={},
                    response_schema={},
                    component_id="COMP-001",
                )
            ],
            data_schemas=[
                DataSchema(
                    table_name="users",
                    description="User table",
                    columns={},
                    component_id="COMP-001",
                )
            ],
            component_logic=[
                ComponentLogic(
                    component_id="COMP-001",
                    component_name="Component",
                    component_type="Service",
                    semantic_unit_id="UNIT-001",
                    dependencies=[],
                    implementation_notes="Notes",
                )
            ],
            design_review_checklist=[
                DesignReviewChecklistItem(
                    item_id="CHECK-001",
                    description="Validate security",
                    category="Security",
                ),
                DesignReviewChecklistItem(
                    item_id="CHECK-002",
                    description="Check API design",
                    category="API",
                ),
                DesignReviewChecklistItem(
                    item_id="CHECK-003",
                    description="Verify data models",
                    category="Data",
                ),
                DesignReviewChecklistItem(
                    item_id="CHECK-004",
                    description="Review error handling",
                    category="Error Handling",
                ),
                DesignReviewChecklistItem(
                    item_id="CHECK-005",
                    description="Check performance",
                    category="Performance",
                ),
            ],
        )

        markdown = render_design_markdown(design)

        # Should have all major sections
        assert "API Contracts" in markdown
        assert "Data Schemas" in markdown
        assert "Component Logic" in markdown
        assert "Design Checklist" in markdown


class TestRenderDesignReviewMarkdown:
    """Test rendering design review reports to markdown."""

    def test_renders_basic_review(self):
        """Test renders a basic design review report."""
        report = DesignReviewReport(
            task_id="TASK-001",
            review_id="REV-001",
            overall_assessment="PASS",
            automated_checks={},
            issues_found=[],
            improvement_suggestions=[],
            checklist_review=[],
            critical_issue_count=0,
            high_issue_count=0,
            medium_issue_count=0,
            low_issue_count=0,
            reviewer_agent="DesignReviewAgent",
            agent_version="1.0.0",
        )

        markdown = render_design_review_markdown(report)

        # Should contain key sections
        assert "# Design Review Report" in markdown
        assert "TASK-001" in markdown
        assert "REV-001" in markdown
        assert "PASS" in markdown

    def test_includes_issues(self):
        """Test includes issues in output."""
        report = DesignReviewReport(
            task_id="TASK-002",
            review_id="REV-002",
            overall_assessment="FAIL",
            automated_checks={},
            issues_found=[
                DesignIssue(
                    issue_id="ISSUE-001",
                    category="Security",
                    severity="Critical",
                    description="Security flaw",
                    affected_phase="Design",
                )
            ],
            improvement_suggestions=[
                ImprovementSuggestion(
                    suggestion_id="SUG-001",
                    category="Performance",
                    priority="High",
                    description="Optimize query",
                )
            ],
            checklist_review=[],
            critical_issue_count=1,
            high_issue_count=0,
            medium_issue_count=0,
            low_issue_count=0,
            reviewer_agent="DesignReviewAgent",
            agent_version="1.0.0",
        )

        markdown = render_design_review_markdown(report)

        # Should include issues and suggestions
        assert "ISSUE-001" in markdown
        assert "Security flaw" in markdown
        assert "SUG-001" in markdown
        assert "Optimize query" in markdown


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
                    component_id="COMP-001",
                )
            ],
            dependencies=["flask==2.0.0"],
            total_files=1,
            total_lines_of_code=1,
            setup_instructions="Run: pip install -r requirements.txt",
        )

        markdown = render_code_manifest_markdown(code)

        # Should contain key sections
        assert "# Code Generation Manifest" in markdown
        assert "TASK-001" in markdown
        assert "src/main.py" in markdown
        assert "Dependencies" in markdown
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
                    component_id="COMP-001",
                ),
                GeneratedFile(
                    file_path="tests/test_app.py",
                    file_type="test",
                    content="# Tests\n" * 20,
                    lines_of_code=20,
                    component_id="COMP-001",
                ),
            ],
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
        report = CodeReviewReport(
            task_id="TASK-001",
            review_id="REV-001",
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
        assert "# Code Review Report" in markdown
        assert "TASK-001" in markdown
        assert "REV-001" in markdown
        assert "PASS" in markdown

    def test_handles_missing_report_gracefully(self):
        """Test handles None report gracefully."""
        markdown = render_code_review_markdown(None)

        # Should return placeholder message
        assert "Code Review Report" in markdown
        assert (
            "not available" in markdown.lower()
            or markdown == "# Code Review Report\n\n*Report not available*\n"
        )
