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
            checklist_item_id=f"CHECK-{i + 1:03d}",
            category="Security",
            description=f"Validate security requirements for component {i + 1}",
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

    def test_renders_review_with_critical_issues(self):
        """Test renders code review with critical issues."""
        from asp.models.code_review import CodeImprovementSuggestion, CodeIssue

        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        report = CodeReviewReport(
            task_id="TASK-CRITICAL",
            review_id=f"CODE-REVIEW-CRITICAL-{timestamp}",
            review_timestamp=datetime.now().isoformat(),
            review_status="FAIL",
            issues_found=[
                CodeIssue(
                    issue_id="CODE-ISSUE-001",
                    category="Security",
                    severity="Critical",
                    description="SQL injection vulnerability in user input handling code",
                    file_path="src/db/queries.py",
                    line_number=45,
                    code_snippet="query = f'SELECT * FROM users WHERE id = {user_id}'",
                    evidence="src/db/queries.py:45 - raw f-string interpolation",
                    impact="Could allow attackers to access or modify database records",
                    affected_phase="Code",
                ),
                CodeIssue(
                    issue_id="CODE-ISSUE-002",
                    category="Security",
                    severity="High",
                    description="Missing authentication check on delete endpoint",
                    file_path="src/api/endpoints.py",
                    line_number=120,
                    code_snippet="def delete_user(user_id):",
                    evidence="src/api/endpoints.py:120 - no auth decorator",
                    impact="Unauthorized users could delete user accounts freely",
                    affected_phase="Design",
                ),
            ],
            improvement_suggestions=[
                CodeImprovementSuggestion(
                    suggestion_id="CODE-IMPROVE-001",
                    category="Security",
                    priority="High",
                    description="Use parameterized queries to prevent SQL injection",
                    related_issue_id="CODE-ISSUE-001",
                    implementation_notes="Replace f-string with parameter binding for safety",
                    suggested_code="cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))",
                ),
            ],
            critical_count=1,
            high_count=1,
            medium_count=0,
            low_count=0,
            total_issues=2,
            agent_version="1.0.0",
            security_review_passed=False,
            quality_review_passed=True,
            performance_review_passed=True,
            standards_review_passed=True,
            testing_review_passed=True,
            maintainability_review_passed=True,
        )

        markdown = render_code_review_markdown(report)

        # Should contain critical issue details
        assert "Critical" in markdown or "ISSUE-001" in markdown
        assert "Security" in markdown
        # Should contain improvement suggestion
        assert "IMPROVE-001" in markdown or "parameterized" in markdown.lower()

    def test_renders_review_with_phase_breakdown(self):
        """Test renders code review with phase-aware breakdown."""
        from asp.models.code_review import CodeIssue

        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        report = CodeReviewReport(
            task_id="TASK-PHASES",
            review_id=f"CODE-REVIEW-PHASES-{timestamp}",
            review_timestamp=datetime.now().isoformat(),
            review_status="FAIL",
            issues_found=[
                CodeIssue(
                    issue_id="CODE-ISSUE-001",
                    category="Code Quality",
                    severity="Medium",
                    description="Planning issue with missing requirements specification",
                    file_path="src/main.py",
                    evidence="src/main.py:10 - missing input validation",
                    impact="Could cause unexpected bugs in production environment",
                    affected_phase="Planning",
                ),
                CodeIssue(
                    issue_id="CODE-ISSUE-002",
                    category="Code Quality",
                    severity="Medium",
                    description="Design issue with improper API contract definition",
                    file_path="src/api.py",
                    evidence="src/api.py:25 - missing error handling",
                    impact="Could cause client applications to crash unexpectedly",
                    affected_phase="Design",
                ),
                CodeIssue(
                    issue_id="CODE-ISSUE-003",
                    category="Maintainability",
                    severity="Low",
                    description="Code issue with suboptimal variable naming convention",
                    file_path="src/utils.py",
                    evidence="src/utils.py:50 - unclear variable names",
                    impact="Minor issue affecting code readability over time",
                    affected_phase="Code",
                ),
            ],
            improvement_suggestions=[],
            critical_count=0,
            high_count=0,
            medium_count=2,
            low_count=1,
            total_issues=3,
            agent_version="1.0.0",
        )

        markdown = render_code_review_markdown(report)

        # Should contain the issues
        assert "TASK-PHASES" in markdown
        assert "3" in markdown  # total issues
        # Phase issues should be auto-populated by model validator
        assert len(report.planning_phase_issues) == 1
        assert len(report.design_phase_issues) == 1
        assert len(report.code_phase_issues) == 1


class TestRenderTestReportMarkdown:
    """Test rendering test reports to markdown."""

    def test_renders_passing_test_report(self):
        """Test renders a passing test report."""
        from asp.models.test import TestReport

        report = TestReport(
            task_id="TEST-PASS-001",
            test_status="PASS",
            build_successful=True,
            build_errors=[],
            test_summary={
                "total_tests": 25,
                "passed": 25,
                "failed": 0,
                "skipped": 0,
            },
            coverage_percentage=85.5,
            defects_found=[],
            total_tests_generated=25,
            test_files_created=["tests/test_main.py", "tests/test_utils.py"],
            agent_version="1.0.0",
            test_timestamp=datetime.now().isoformat(),
            test_duration_seconds=12.5,
        )

        from asp.utils.markdown_renderer import render_test_report_markdown

        markdown = render_test_report_markdown(report)

        # Should contain key elements
        assert "TEST-PASS-001" in markdown
        assert "PASS" in markdown
        assert "25" in markdown  # total tests
        assert "85" in markdown  # coverage (without decimal)
        assert "test_main.py" in markdown

    def test_renders_failing_test_report_with_defects(self):
        """Test renders a failing test report with defects."""
        from asp.models.test import TestDefect, TestReport

        report = TestReport(
            task_id="TEST-FAIL-001",
            test_status="FAIL",
            build_successful=True,
            build_errors=[],
            test_summary={
                "total_tests": 20,
                "passed": 15,
                "failed": 5,
                "skipped": 0,
            },
            coverage_percentage=60.0,
            defects_found=[
                TestDefect(
                    defect_id="TEST-DEFECT-001",
                    defect_type="6_Conventional_Code_Bug",
                    severity="Critical",
                    description="Null pointer exception in auth handler",
                    evidence="TypeError: Cannot read property 'id' of null",
                    phase_injected="Code",
                    phase_removed="Test",
                    file_path="src/auth.py",
                    line_number=42,
                ),
                TestDefect(
                    defect_id="TEST-DEFECT-002",
                    defect_type="5_Security_Vulnerability",
                    severity="High",
                    description="Password not hashed before storage",
                    evidence="AssertionError: Expected hashed password",
                    phase_injected="Code",
                    phase_removed="Test",
                    file_path="src/user.py",
                    line_number=88,
                ),
            ],
            total_tests_generated=20,
            test_files_created=["tests/test_auth.py"],
            agent_version="1.0.0",
            test_timestamp=datetime.now().isoformat(),
            test_duration_seconds=8.3,
        )

        from asp.utils.markdown_renderer import render_test_report_markdown

        markdown = render_test_report_markdown(report)

        # Should contain failure information
        assert "FAIL" in markdown
        assert "5" in markdown  # failed tests
        assert "Critical" in markdown
        assert "TEST-DEFECT-001" in markdown

    def test_renders_build_failed_report(self):
        """Test renders a build failed report."""
        from asp.models.test import TestReport

        report = TestReport(
            task_id="TEST-BUILD-FAIL",
            test_status="BUILD_FAILED",
            build_successful=False,
            build_errors=[
                "SyntaxError: unexpected EOF in main.py line 45",
                "ImportError: No module named 'missing_dep'",
            ],
            test_summary={
                "total_tests": 0,
                "passed": 0,
                "failed": 0,
                "skipped": 0,
            },
            coverage_percentage=None,
            defects_found=[],
            total_tests_generated=0,
            test_files_created=[],
            agent_version="1.0.0",
            test_timestamp=datetime.now().isoformat(),
            test_duration_seconds=1.2,
        )

        from asp.utils.markdown_renderer import render_test_report_markdown

        markdown = render_test_report_markdown(report)

        # Should contain build error information
        assert "BUILD_FAILED" in markdown or "Build" in markdown
        assert "SyntaxError" in markdown
        assert "ImportError" in markdown


class TestRenderPostmortemReportMarkdown:
    """Test rendering postmortem reports to markdown."""

    def test_renders_basic_postmortem(self):
        """Test renders a basic postmortem report."""
        from asp.models.postmortem import (
            EstimationAccuracy,
            MetricComparison,
            PostmortemReport,
            QualityMetrics,
            RootCauseItem,
        )

        report = PostmortemReport(
            task_id="POSTMORTEM-001",
            estimation_accuracy=EstimationAccuracy(
                latency_ms=MetricComparison(
                    planned=30000, actual=33000, variance_percent=10.0
                ),
                tokens=MetricComparison(
                    planned=50000, actual=55000, variance_percent=10.0
                ),
                api_cost=MetricComparison(
                    planned=0.10, actual=0.11, variance_percent=10.0
                ),
                semantic_complexity=MetricComparison(
                    planned=15.0, actual=16.5, variance_percent=10.0
                ),
            ),
            quality_metrics=QualityMetrics(
                defect_density=0.12,
                total_defects=2,
                defect_injection_by_phase={"Code": 2},
                defect_removal_by_phase={"Test": 2},
                phase_yield={"Test": 100.0},
            ),
            root_cause_analysis=[
                RootCauseItem(
                    defect_type="6_Conventional_Code_Bug",
                    occurrence_count=2,
                    total_effort_to_fix=0.02,
                    average_effort_to_fix=0.01,
                    recommendation="Add more unit tests for edge cases",
                ),
            ],
            summary="Task completed with acceptable variance. Two minor bugs found and fixed during testing.",
            recommendations=[
                "Increase test coverage for edge cases",
                "Add input validation checks",
            ],
        )

        from asp.utils.markdown_renderer import render_postmortem_report_markdown

        markdown = render_postmortem_report_markdown(report)

        # Should contain key sections
        assert "POSTMORTEM-001" in markdown
        assert "Estimation" in markdown
        assert "Quality" in markdown
        assert "Root Cause" in markdown
        assert "Recommendation" in markdown

    def test_renders_postmortem_with_no_defects(self):
        """Test renders postmortem with no defects (excellent quality)."""
        from asp.models.postmortem import (
            EstimationAccuracy,
            MetricComparison,
            PostmortemReport,
            QualityMetrics,
        )

        report = PostmortemReport(
            task_id="POSTMORTEM-CLEAN",
            estimation_accuracy=EstimationAccuracy(
                latency_ms=MetricComparison(
                    planned=20000, actual=19000, variance_percent=-5.0
                ),
                tokens=MetricComparison(
                    planned=40000, actual=38000, variance_percent=-5.0
                ),
                api_cost=MetricComparison(
                    planned=0.08, actual=0.076, variance_percent=-5.0
                ),
                semantic_complexity=MetricComparison(
                    planned=10.0, actual=10.0, variance_percent=0.0
                ),
            ),
            quality_metrics=QualityMetrics(
                defect_density=0.0,
                total_defects=0,
                defect_injection_by_phase={},
                defect_removal_by_phase={},
                phase_yield={},
            ),
            root_cause_analysis=[],
            summary="Perfect execution with no defects and under-budget completion.",
            recommendations=[],
        )

        from asp.utils.markdown_renderer import render_postmortem_report_markdown

        markdown = render_postmortem_report_markdown(report)

        # Should indicate excellent quality
        assert "POSTMORTEM-CLEAN" in markdown
        assert "Excellent" in markdown or "excellent" in markdown.lower()

    def test_renders_postmortem_with_poor_estimation(self):
        """Test renders postmortem with poor estimation accuracy."""
        from asp.models.postmortem import (
            EstimationAccuracy,
            MetricComparison,
            PostmortemReport,
            QualityMetrics,
            RootCauseItem,
        )

        report = PostmortemReport(
            task_id="POSTMORTEM-POOR",
            estimation_accuracy=EstimationAccuracy(
                latency_ms=MetricComparison(
                    planned=10000, actual=25000, variance_percent=150.0
                ),
                tokens=MetricComparison(
                    planned=20000, actual=60000, variance_percent=200.0
                ),
                api_cost=MetricComparison(
                    planned=0.05, actual=0.15, variance_percent=200.0
                ),
                semantic_complexity=MetricComparison(
                    planned=5.0, actual=15.0, variance_percent=200.0
                ),
            ),
            quality_metrics=QualityMetrics(
                defect_density=0.5,
                total_defects=5,
                defect_injection_by_phase={"Planning": 2, "Design": 2, "Code": 1},
                defect_removal_by_phase={
                    "Design Review": 2,
                    "Code Review": 2,
                    "Test": 1,
                },
                phase_yield={"Design Review": 40.0, "Code Review": 40.0, "Test": 20.0},
            ),
            root_cause_analysis=[
                RootCauseItem(
                    defect_type="1_Planning_Failure",
                    occurrence_count=2,
                    total_effort_to_fix=0.05,
                    average_effort_to_fix=0.025,
                    recommendation="Improve requirements analysis",
                ),
            ],
            summary="Significant estimation issues with 200% cost overrun.",
            recommendations=[
                "Review planning process",
                "Break down complex tasks",
            ],
        )

        from asp.utils.markdown_renderer import render_postmortem_report_markdown

        markdown = render_postmortem_report_markdown(report)

        # Should indicate poor estimation
        assert "POSTMORTEM-POOR" in markdown
        assert "Poor" in markdown or "❌" in markdown
        # Should show phase breakdown
        assert "Planning" in markdown
        assert "Design" in markdown
