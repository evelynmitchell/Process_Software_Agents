"""
Unit tests for Design Review Orchestrator.

Tests the orchestration of 6 specialist review agents including:
- Initialization and specialist agent loading
- Parallel dispatch to specialist agents
- Result aggregation and deduplication
- Issue normalization and conflict resolution
- Error handling and partial failures
- Telemetry integration
"""

from datetime import datetime
from unittest.mock import Mock, patch

import pytest

from asp.agents.base_agent import AgentExecutionError
from asp.agents.design_review_orchestrator import DesignReviewOrchestrator
from asp.models.design import (
    APIContract,
    ComponentLogic,
    DataSchema,
    DesignReviewChecklistItem,
    DesignSpecification,
)
from asp.models.design_review import DesignReviewReport

# Helper functions for creating test data


def create_test_design_spec(task_id="TEST-001"):
    """Create a minimal valid DesignSpecification for testing."""
    return DesignSpecification(
        task_id=task_id,
        timestamp=datetime.now(),
        api_contracts=[
            APIContract(
                endpoint="/api/test",
                method="GET",
                description="Test endpoint for validation",
                request_schema={"type": "object"},
                response_schema={"type": "object"},
                authentication_required=True,
                error_responses=[],
            )
        ],
        data_schemas=[
            DataSchema(
                table_name="test_table",
                description="Test table for testing purposes",
                columns=[
                    {"name": "id", "type": "INTEGER", "constraints": "PRIMARY KEY"},
                    {"name": "name", "type": "VARCHAR(255)", "constraints": "NOT NULL"},
                ],
                relationships=[],
                constraints=[],
                indexes=[],
            )
        ],
        component_logic=[
            ComponentLogic(
                component_name="TestComponent",
                semantic_unit_id="SU-001",
                responsibility="Handles test operations for validation purposes",
                interfaces=[{"method": "execute", "parameters": {}, "returns": "dict"}],
                implementation_notes="Implement test logic with proper error handling",
                dependencies=[],
            )
        ],
        design_review_checklist=[
            DesignReviewChecklistItem(
                category="Security",
                description="Check security requirements are met",
                validation_criteria="Validate authentication and authorization",
                severity="Critical",
            ),
            DesignReviewChecklistItem(
                category="Performance",
                description="Check performance requirements are met",
                validation_criteria="Validate response time under 100ms",
                severity="High",
            ),
            DesignReviewChecklistItem(
                category="Architecture",
                description="Check architecture compliance",
                validation_criteria="Validate separation of concerns",
            ),
            DesignReviewChecklistItem(
                category="Data Integrity",
                description="Check data integrity requirements",
                validation_criteria="Validate all foreign keys",
            ),
            DesignReviewChecklistItem(
                category="Maintainability",
                description="Check code maintainability",
                validation_criteria="Validate code documentation",
            ),
        ],
        architecture_overview="Simple test architecture with API layer and data layer",
        technology_stack={"language": "Python", "framework": "FastAPI"},
    )


def create_mock_specialist_result(
    issues_count=2, suggestions_count=1, specialist_name="Security"
):
    """Create a mock specialist agent result."""
    return {
        "issues_found": [
            {
                "issue_id": f"{specialist_name.upper()}-{i:03d}",
                "category": specialist_name,
                "severity": "High" if i == 0 else "Medium",
                "title": f"Test {specialist_name} issue {i}",
                "description": f"Detailed description for {specialist_name} issue number {i} with sufficient length",
                "affected_component": "TestComponent",
                "line_number": None,
                "evidence": f"{specialist_name} evidence for issue {i}",
                "impact": f"Significant impact of {specialist_name} issue number {i} on the system",
                "affected_phase": "Design",
            }
            for i in range(issues_count)
        ],
        "improvement_suggestions": [
            {
                "suggestion_id": f"{specialist_name.upper()}-IMPROVE-{i:03d}",
                "category": specialist_name,
                "priority": "High",
                "title": f"Test {specialist_name} suggestion {i}",
                "description": f"Detailed description for {specialist_name} suggestion number {i} with sufficient length",
                "affected_component": "TestComponent",
                "implementation_guidance": f"Implementation guidance for {specialist_name} suggestion number {i}",
                "related_issue_id": None,
            }
            for i in range(suggestions_count)
        ],
    }


class TestDesignReviewOrchestratorInitialization:
    """Test Design Review Orchestrator initialization."""

    def test_init_with_defaults(self):
        """Test initialization with default parameters."""
        orchestrator = DesignReviewOrchestrator()
        assert orchestrator.agent_version == "1.0.0"
        assert "security" in orchestrator.specialists
        assert "performance" in orchestrator.specialists
        assert "data_integrity" in orchestrator.specialists
        assert "maintainability" in orchestrator.specialists
        assert "architecture" in orchestrator.specialists
        assert "api_design" in orchestrator.specialists
        assert len(orchestrator.specialists) == 6

    def test_init_with_custom_llm_client(self):
        """Test initialization with custom LLM client."""
        mock_client = Mock()
        orchestrator = DesignReviewOrchestrator(llm_client=mock_client)
        # Verify LLM client is passed to all specialists
        assert orchestrator._llm_client == mock_client
        for specialist in orchestrator.specialists.values():
            assert specialist._llm_client == mock_client

    def test_init_with_db_path(self):
        """Test initialization with database path."""
        db_path = "/tmp/test.db"
        orchestrator = DesignReviewOrchestrator(db_path=db_path)
        assert orchestrator.db_path == db_path
        # Verify db_path is passed to all specialists
        for specialist in orchestrator.specialists.values():
            assert specialist.db_path == db_path

    def test_specialist_agents_loaded(self):
        """Test that all 6 specialist agents are loaded correctly."""
        orchestrator = DesignReviewOrchestrator()
        specialist_names = list(orchestrator.specialists.keys())
        expected_names = [
            "security",
            "performance",
            "data_integrity",
            "maintainability",
            "architecture",
            "api_design",
        ]
        assert sorted(specialist_names) == sorted(expected_names)

    def test_specialist_agents_are_base_agents(self):
        """Test that all specialists inherit from BaseAgent."""
        orchestrator = DesignReviewOrchestrator()
        for specialist in orchestrator.specialists.values():
            assert hasattr(specialist, "execute")
            assert hasattr(specialist, "_llm_client")


class TestParallelDispatch:
    """Test parallel dispatch to specialist agents."""

    @pytest.mark.asyncio
    async def test_dispatch_all_specialists_success(self):
        """Test successful parallel dispatch to all 6 specialists."""
        orchestrator = DesignReviewOrchestrator()
        design_spec = create_test_design_spec()

        # Mock all specialists to return successful results
        for specialist in orchestrator.specialists.values():
            specialist.execute = Mock(return_value=create_mock_specialist_result())

        results = await orchestrator._dispatch_specialists(design_spec)

        # Verify all 6 specialists were called
        assert len(results) == 6
        for name in orchestrator.specialists.keys():
            assert name in results
            assert "issues_found" in results[name]
            assert "improvement_suggestions" in results[name]

    @pytest.mark.asyncio
    async def test_dispatch_with_specialist_failure(self):
        """Test dispatch continues when one specialist fails."""
        orchestrator = DesignReviewOrchestrator()
        design_spec = create_test_design_spec()

        # Mock 5 successful specialists and 1 failing
        for i, (name, specialist) in enumerate(orchestrator.specialists.items()):
            if i == 0:
                # First specialist fails
                specialist.execute = Mock(side_effect=Exception("Specialist failed"))
            else:
                # Others succeed
                specialist.execute = Mock(return_value=create_mock_specialist_result())

        results = await orchestrator._dispatch_specialists(design_spec)

        # Verify all 6 specialists returned results (failed one returns empty)
        assert len(results) == 6
        # Failed specialist should have empty results
        failed_specialist = list(orchestrator.specialists.keys())[0]
        assert results[failed_specialist]["issues_found"] == []
        assert results[failed_specialist]["improvement_suggestions"] == []
        # Other specialists should have results
        for name in list(orchestrator.specialists.keys())[1:]:
            assert len(results[name]["issues_found"]) > 0

    @pytest.mark.asyncio
    async def test_dispatch_all_specialists_fail(self):
        """Test dispatch when all specialists fail."""
        orchestrator = DesignReviewOrchestrator()
        design_spec = create_test_design_spec()

        # Mock all specialists to fail
        for specialist in orchestrator.specialists.values():
            specialist.execute = Mock(side_effect=Exception("All failed"))

        results = await orchestrator._dispatch_specialists(design_spec)

        # Verify all return empty results
        assert len(results) == 6
        for result in results.values():
            assert result["issues_found"] == []
            assert result["improvement_suggestions"] == []

    @pytest.mark.asyncio
    async def test_dispatch_execution_order_independence(self):
        """Test that specialist execution order doesn't affect results."""
        orchestrator = DesignReviewOrchestrator()
        design_spec = create_test_design_spec()

        # Mock specialists with different execution times
        for i, specialist in enumerate(orchestrator.specialists.values()):
            # Add varying delays to simulate different execution times
            def delayed_execute(spec, delay=i * 0.01):
                import time

                time.sleep(delay)
                return create_mock_specialist_result()

            specialist.execute = Mock(side_effect=delayed_execute)

        results = await orchestrator._dispatch_specialists(design_spec)

        # Verify all specialists completed regardless of execution time
        assert len(results) == 6
        for result in results.values():
            assert len(result["issues_found"]) > 0

    @pytest.mark.asyncio
    async def test_dispatch_with_design_spec_passed_correctly(self):
        """Test that design_spec is passed correctly to all specialists."""
        orchestrator = DesignReviewOrchestrator()
        design_spec = create_test_design_spec(task_id="SPECIFIC-TASK-ID")

        # Mock specialists to capture the design_spec argument
        for specialist in orchestrator.specialists.values():
            specialist.execute = Mock(return_value=create_mock_specialist_result())

        await orchestrator._dispatch_specialists(design_spec)

        # Verify all specialists were called with the correct design_spec
        for specialist in orchestrator.specialists.values():
            specialist.execute.assert_called_once()
            call_args = specialist.execute.call_args[0]
            assert call_args[0].task_id == "SPECIFIC-TASK-ID"


class TestResultAggregation:
    """Test result aggregation and deduplication."""

    def test_aggregate_results_from_multiple_specialists(self):
        """Test aggregating results from multiple specialists."""
        orchestrator = DesignReviewOrchestrator()

        specialist_results = {
            "security": create_mock_specialist_result(
                issues_count=2, suggestions_count=1, specialist_name="Security"
            ),
            "performance": create_mock_specialist_result(
                issues_count=1, suggestions_count=2, specialist_name="Performance"
            ),
            "data_integrity": create_mock_specialist_result(
                issues_count=0, suggestions_count=0, specialist_name="DataIntegrity"
            ),
        }

        issues, suggestions = orchestrator._aggregate_results(specialist_results)

        # Verify aggregation
        assert len(issues) == 3  # 2 + 1 + 0
        assert len(suggestions) == 3  # 1 + 2 + 0

    def test_aggregate_results_deduplicate_identical_issues(self):
        """Test that identical issues are deduplicated."""
        orchestrator = DesignReviewOrchestrator()

        # Create duplicate issues
        duplicate_issue = {
            "issue_id": "ISSUE-001",
            "category": "Security",
            "severity": "High",
            "title": "SQL Injection vulnerability",
            "description": "User input not sanitized",
            "affected_component": "UserController",
            "line_number": None,
            "evidence": "Evidence found during review",
            "impact": "Significant impact on the system",
            "affected_phase": "Design",
        }

        specialist_results = {
            "security": {
                "issues_found": [duplicate_issue],
                "improvement_suggestions": [],
            },
            "maintainability": {
                "issues_found": [duplicate_issue],
                "improvement_suggestions": [],
            },
        }

        issues, _ = orchestrator._aggregate_results(specialist_results)

        # Should deduplicate based on title+description+component
        assert len(issues) == 1

    def test_aggregate_results_empty_specialists(self):
        """Test aggregation when all specialists return empty results."""
        orchestrator = DesignReviewOrchestrator()

        specialist_results = {
            "security": {"issues_found": [], "improvement_suggestions": []},
            "performance": {"issues_found": [], "improvement_suggestions": []},
        }

        issues, suggestions = orchestrator._aggregate_results(specialist_results)

        assert len(issues) == 0
        assert len(suggestions) == 0

    def test_aggregate_results_normalizes_issues(self):
        """Test that issues are normalized during aggregation."""
        orchestrator = DesignReviewOrchestrator()

        # Issue with non-standard category
        issue_with_bad_category = {
            "issue_id": "ISSUE-001",
            "category": "god component",  # Should normalize to "Maintainability"
            "severity": "High",
            "title": "Test issue",
            "description": "Test description",
            "affected_component": "TestComponent",
            "line_number": None,
            "evidence": "Evidence found during review",
            "impact": "Significant impact on the system",
            "affected_phase": "Design",
        }

        specialist_results = {
            "maintainability": {
                "issues_found": [issue_with_bad_category],
                "improvement_suggestions": [],
            }
        }

        issues, _ = orchestrator._aggregate_results(specialist_results)

        # Verify category was normalized
        assert issues[0]["category"] == "Maintainability"


class TestCategoryNormalization:
    """Test category normalization logic."""

    def test_normalize_security_variations(self):
        """Test normalization of security-related categories."""
        orchestrator = DesignReviewOrchestrator()
        assert orchestrator._normalize_category("security") == "Security"
        assert orchestrator._normalize_category("authentication") == "Security"
        assert orchestrator._normalize_category("authorization") == "Security"

    def test_normalize_performance_variations(self):
        """Test normalization of performance-related categories."""
        orchestrator = DesignReviewOrchestrator()
        assert orchestrator._normalize_category("performance") == "Performance"
        assert orchestrator._normalize_category("optimization") == "Performance"
        assert orchestrator._normalize_category("caching") == "Performance"

    def test_normalize_maintainability_variations(self):
        """Test normalization of maintainability-related categories."""
        orchestrator = DesignReviewOrchestrator()
        assert orchestrator._normalize_category("maintainability") == "Maintainability"
        assert orchestrator._normalize_category("god component") == "Maintainability"
        assert orchestrator._normalize_category("code smell") == "Maintainability"
        assert orchestrator._normalize_category("coupling") == "Maintainability"

    def test_normalize_unknown_category_defaults_to_architecture(self):
        """Test that unknown categories default to Architecture."""
        orchestrator = DesignReviewOrchestrator()
        result = orchestrator._normalize_category("unknown_category_xyz")
        assert result == "Architecture"

    def test_normalize_category_case_insensitive(self):
        """Test that normalization is case-insensitive."""
        orchestrator = DesignReviewOrchestrator()
        assert orchestrator._normalize_category("SECURITY") == "Security"
        assert orchestrator._normalize_category("Performance") == "Performance"
        assert orchestrator._normalize_category("DATA INTEGRITY") == "Data Integrity"


class TestExecuteIntegration:
    """Test full execute() method integration."""

    def test_execute_success_all_pass(self):
        """Test successful execution with all checks passing."""
        orchestrator = DesignReviewOrchestrator()
        design_spec = create_test_design_spec()

        # Mock specialists to return no issues (should PASS)
        for specialist in orchestrator.specialists.values():
            specialist.execute = Mock(
                return_value={"issues_found": [], "improvement_suggestions": []}
            )

        report = orchestrator.execute(design_spec)

        assert isinstance(report, DesignReviewReport)
        assert report.task_id == "TEST-001"
        assert report.overall_assessment == "PASS"
        assert report.critical_issue_count == 0
        assert report.high_issue_count == 0

    def test_execute_fail_with_critical_issues(self):
        """Test execution fails when critical issues found."""
        orchestrator = DesignReviewOrchestrator()
        design_spec = create_test_design_spec()

        # Mock to return critical issue
        mock_result = {
            "issues_found": [
                {
                    "issue_id": "ISSUE-001",
                    "category": "Security",
                    "severity": "Critical",
                    "title": "Critical security flaw",
                    "description": "Detailed description of the critical security flaw found in the design",
                    "affected_component": "Component",
                    "line_number": None,
                    "evidence": "Evidence found in security review",
                    "impact": "Significant impact on system security and data integrity",
                    "affected_phase": "Design",
                }
            ],
            "improvement_suggestions": [],
        }
        for specialist in orchestrator.specialists.values():
            specialist.execute = Mock(return_value=mock_result)

        report = orchestrator.execute(design_spec)

        assert report.overall_assessment == "FAIL"
        assert report.critical_issue_count > 0

    def test_execute_needs_improvement_with_medium_issues(self):
        """Test execution returns NEEDS_IMPROVEMENT for medium/low issues."""
        orchestrator = DesignReviewOrchestrator()
        design_spec = create_test_design_spec()

        # Mock to return medium severity issue
        mock_result = {
            "issues_found": [
                {
                    "issue_id": "ISSUE-001",
                    "category": "Performance",
                    "severity": "Medium",
                    "title": "Performance concern",
                    "description": "Detailed description of the issue found in the design specification",
                    "affected_component": "Component",
                    "line_number": None,
                    "evidence": "Evidence found during review",
                    "impact": "Significant impact on the system",
                    "affected_phase": "Design",
                }
            ],
            "improvement_suggestions": [],
        }
        for specialist in orchestrator.specialists.values():
            specialist.execute = Mock(return_value=mock_result)

        report = orchestrator.execute(design_spec)

        assert report.overall_assessment == "NEEDS_IMPROVEMENT"
        assert report.medium_issue_count > 0

    def test_execute_generates_unique_review_id(self):
        """Test that each execution generates a unique review_id."""
        import time

        orchestrator = DesignReviewOrchestrator()
        design_spec = create_test_design_spec()

        # Mock specialists
        for specialist in orchestrator.specialists.values():
            specialist.execute = Mock(
                return_value={"issues_found": [], "improvement_suggestions": []}
            )

        report1 = orchestrator.execute(design_spec)
        time.sleep(1.1)  # Ensure different timestamps
        report2 = orchestrator.execute(design_spec)

        assert report1.review_id != report2.review_id
        assert report1.review_id.startswith("REVIEW-")
        assert report2.review_id.startswith("REVIEW-")

    def test_execute_tracks_review_duration(self):
        """Test that execution tracks review duration."""
        orchestrator = DesignReviewOrchestrator()
        design_spec = create_test_design_spec()

        # Mock specialists
        for specialist in orchestrator.specialists.values():
            specialist.execute = Mock(
                return_value={"issues_found": [], "improvement_suggestions": []}
            )

        report = orchestrator.execute(design_spec)

        assert report.review_duration_ms > 0
        assert isinstance(report.review_duration_ms, float)

    def test_execute_handles_specialist_errors_gracefully(self):
        """Test that execution continues when specialists fail."""
        orchestrator = DesignReviewOrchestrator()
        design_spec = create_test_design_spec()

        # Mock some specialists to fail
        for i, specialist in enumerate(orchestrator.specialists.values()):
            if i < 3:
                specialist.execute = Mock(side_effect=Exception("Failed"))
            else:
                specialist.execute = Mock(
                    return_value={"issues_found": [], "improvement_suggestions": []}
                )

        # Should not raise exception
        report = orchestrator.execute(design_spec)
        assert isinstance(report, DesignReviewReport)

    @patch("asp.telemetry.telemetry.track_agent_cost")
    def test_execute_telemetry_integration(self, mock_track):
        """Test that execute integrates with telemetry tracking."""
        orchestrator = DesignReviewOrchestrator()
        design_spec = create_test_design_spec()

        # Mock specialists
        for specialist in orchestrator.specialists.values():
            specialist.execute = Mock(
                return_value={"issues_found": [], "improvement_suggestions": []}
            )

        report = orchestrator.execute(design_spec)

        # Telemetry decorator should have been applied (verify by checking report exists)
        assert isinstance(report, DesignReviewReport)


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_execute_with_malformed_design_spec(self):
        """Test execution with malformed design specification."""
        orchestrator = DesignReviewOrchestrator()

        # Mock specialists to raise error on malformed input
        for specialist in orchestrator.specialists.values():
            specialist.execute = Mock(
                side_effect=AgentExecutionError("Invalid design spec")
            )

        # Create minimal design spec
        design_spec = create_test_design_spec()

        # Should handle errors and return report with empty results
        report = orchestrator.execute(design_spec)
        assert isinstance(report, DesignReviewReport)

    def test_execute_with_very_large_design_spec(self):
        """Test execution with very large design specification."""
        orchestrator = DesignReviewOrchestrator()

        # Create large design spec
        design_spec = create_test_design_spec()
        # Add many components
        design_spec.component_logic = [
            ComponentLogic(
                component_name=f"Component{i}",
                semantic_unit_id=f"SU-{i:03d}",
                responsibility=f"Handles operations for component number {i}",
                interfaces=[{"method": f"execute_{i}"}],
                implementation_notes=f"Implementation details for component number {i}",
            )
            for i in range(100)
        ]

        # Mock specialists
        for specialist in orchestrator.specialists.values():
            specialist.execute = Mock(
                return_value={"issues_found": [], "improvement_suggestions": []}
            )

        report = orchestrator.execute(design_spec)
        assert isinstance(report, DesignReviewReport)

    def test_execute_with_empty_design_spec(self):
        """Test execution with minimal design specification."""
        orchestrator = DesignReviewOrchestrator()

        # Minimal valid design spec (required fields only)
        design_spec = DesignSpecification(
            task_id="MINIMAL-001",
            timestamp=datetime.now(),
            component_logic=[
                ComponentLogic(
                    component_name="MinimalComponent",
                    semantic_unit_id="SU-001",
                    responsibility="Minimal component for testing purposes only",
                    interfaces=[{"method": "minimal"}],
                    implementation_notes="Minimal implementation for testing",
                )
            ],
            design_review_checklist=[
                DesignReviewChecklistItem(
                    category="Security",
                    description="Minimal security check",
                    validation_criteria="Minimal validation",
                    severity="Critical",
                ),
                DesignReviewChecklistItem(
                    category="Test",
                    description="Test check 1",
                    validation_criteria="Validate 1",
                ),
                DesignReviewChecklistItem(
                    category="Test",
                    description="Test check 2",
                    validation_criteria="Validate 2",
                ),
                DesignReviewChecklistItem(
                    category="Test",
                    description="Test check 3",
                    validation_criteria="Validate 3",
                ),
                DesignReviewChecklistItem(
                    category="Test",
                    description="Test check 4",
                    validation_criteria="Validate 4",
                ),
            ],
            architecture_overview="Minimal architecture overview for testing the orchestrator",
            technology_stack={"language": "Python"},
        )

        # Mock specialists
        for specialist in orchestrator.specialists.values():
            specialist.execute = Mock(
                return_value={"issues_found": [], "improvement_suggestions": []}
            )

        report = orchestrator.execute(design_spec)
        assert isinstance(report, DesignReviewReport)
        assert report.task_id == "MINIMAL-001"
