"""
Unit tests for test.py models (TestInput, TestDefect, TestReport).

Tests cover:
- Model initialization and validation
- Required field validation
- Field constraints (ranges, patterns, enums)
- Model validators (auto-calculation, consistency checks)
- JSON serialization/deserialization
"""

import pytest
from pydantic import ValidationError

from asp.models.code import GeneratedCode, GeneratedFile
from asp.models.design import (
    ComponentLogic,
    DesignReviewChecklistItem,
    DesignSpecification,
)
from asp.models.test import TestDefect, TestInput, TestReport

# =============================================================================
# Helper Functions
# =============================================================================


def create_valid_generated_code(task_id="TEST-001"):
    """Creates a minimal valid GeneratedCode for testing."""
    return GeneratedCode(
        task_id=task_id,
        files=[
            GeneratedFile(
                file_path="src/main.py",
                content="print('hello world')",
                file_type="source",
                description="This is the main file for the application.",
            )
        ],
        file_structure={"src": ["main.py"]},
        dependencies=["python>=3.12"],
        setup_instructions="Run python src/main.py",
        implementation_notes="This is a simple hello world application that prints a message.",
    )


def create_valid_design_spec(task_id="TEST-001"):
    """Creates a minimal valid DesignSpecification for testing."""
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

    return DesignSpecification(
        task_id=task_id,
        component_logic=[component],
        design_review_checklist=checklist,
        architecture_overview="This is a test architecture with sufficient detail to pass validation requirements",
        technology_stack={"language": "Python", "framework": "FastAPI"},
    )


# =============================================================================
# Test Cases
# =============================================================================


class TestTestInputModel:
    """Test TestInput model validation."""

    def test_init_with_valid_data(self):
        """Test initialization with valid data."""
        code = create_valid_generated_code()
        design = create_valid_design_spec()

        test_input = TestInput(
            task_id="TEST-001",
            generated_code=code,
            design_specification=design,
            test_framework="pytest",
            coverage_target=80.0,
        )

        assert test_input.task_id == "TEST-001"
        assert test_input.test_framework == "pytest"
        assert test_input.coverage_target == 80.0

    def test_task_id_min_length_validation(self):
        """Test task_id minimum length validation."""
        code = create_valid_generated_code()
        design = create_valid_design_spec()

        with pytest.raises(ValidationError) as exc_info:
            TestInput(
                task_id="TE",  # Too short
                generated_code=code,
                design_specification=design,
            )
        assert "task_id" in str(exc_info.value)

    def test_coverage_target_range_validation(self):
        """Test coverage_target must be 0-100."""
        code = create_valid_generated_code()
        design = create_valid_design_spec()

        # Test > 100
        with pytest.raises(ValidationError) as exc_info:
            TestInput(
                task_id="TEST-001",
                generated_code=code,
                design_specification=design,
                coverage_target=150.0,  # Invalid
            )
        assert "coverage_target" in str(exc_info.value)

        # Test < 0
        with pytest.raises(ValidationError) as exc_info:
            TestInput(
                task_id="TEST-001",
                generated_code=code,
                design_specification=design,
                coverage_target=-10.0,  # Invalid
            )
        assert "coverage_target" in str(exc_info.value)

    def test_default_values(self):
        """Test default values are applied."""
        code = create_valid_generated_code()
        design = create_valid_design_spec()

        test_input = TestInput(
            task_id="TEST-001",
            generated_code=code,
            design_specification=design,
        )

        assert test_input.test_framework == "pytest"  # Default
        assert test_input.coverage_target == 80.0  # Default


class TestTestDefectModel:
    """Test TestDefect model validation."""

    def test_init_with_valid_data(self):
        """Test initialization with valid data."""
        defect = TestDefect(
            defect_id="TEST-DEFECT-001",
            defect_type="6_Conventional_Code_Bug",
            severity="High",
            description="Password validation fails with special characters",
            evidence="AssertionError: Expected True, got False",
            phase_injected="Code",
            phase_removed="Test",
            file_path="src/auth.py",
            line_number=45,
        )

        assert defect.defect_id == "TEST-DEFECT-001"
        assert defect.severity == "High"
        assert defect.phase_removed == "Test"

    def test_defect_id_pattern_validation(self):
        """Test defect_id must match pattern TEST-DEFECT-NNN."""
        with pytest.raises(ValidationError) as exc_info:
            TestDefect(
                defect_id="INVALID-ID",  # Wrong pattern
                defect_type="6_Conventional_Code_Bug",
                severity="High",
                description="Test defect",
                evidence="Test evidence",
                phase_injected="Code",
            )
        assert "defect_id" in str(exc_info.value)

        # Valid pattern should work
        defect = TestDefect(
            defect_id="TEST-DEFECT-123",
            defect_type="6_Conventional_Code_Bug",
            severity="High",
            description="Test defect with valid ID pattern",
            evidence="Test evidence",
            phase_injected="Code",
        )
        assert defect.defect_id == "TEST-DEFECT-123"

    def test_defect_type_enum_validation(self):
        """Test defect_type must be from AI Defect Taxonomy."""
        valid_types = [
            "1_Planning_Failure",
            "2_Prompt_Misinterpretation",
            "3_Tool_Use_Error",
            "4_Hallucination",
            "5_Security_Vulnerability",
            "6_Conventional_Code_Bug",
            "7_Task_Execution_Error",
            "8_Alignment_Deviation",
        ]

        # Test all valid types
        for dtype in valid_types:
            defect = TestDefect(
                defect_id="TEST-DEFECT-001",
                defect_type=dtype,
                severity="High",
                description="This is a valid test description.",
                evidence="This is valid evidence.",
                phase_injected="Code",
            )
            assert defect.defect_type == dtype

        # Test invalid type
        with pytest.raises(ValidationError):
            TestDefect(
                defect_id="TEST-DEFECT-001",
                defect_type="Invalid_Type",
                severity="High",
                description="This is a valid test description.",
                evidence="This is valid evidence.",
                phase_injected="Code",
            )

    def test_severity_enum_validation(self):
        """Test severity must be Critical/High/Medium/Low."""
        valid_severities = ["Critical", "High", "Medium", "Low"]

        for sev in valid_severities:
            defect = TestDefect(
                defect_id="TEST-DEFECT-001",
                defect_type="6_Conventional_Code_Bug",
                severity=sev,
                description="This is a valid test description.",
                evidence="This is valid evidence.",
                phase_injected="Code",
            )
            assert defect.severity == sev

        # Test invalid severity
        with pytest.raises(ValidationError):
            TestDefect(
                defect_id="TEST-DEFECT-001",
                defect_type="6_Conventional_Code_Bug",
                severity="Invalid",
                description="This is a valid test description.",
                evidence="This is valid evidence.",
                phase_injected="Code",
            )

    def test_description_min_length(self):
        """Test description must be at least 20 characters."""
        with pytest.raises(ValidationError) as exc_info:
            TestDefect(
                defect_id="TEST-DEFECT-001",
                defect_type="6_Conventional_Code_Bug",
                severity="High",
                description="Too short",  # < 20 chars
                evidence="Evidence",
                phase_injected="Code",
            )
        assert "description" in str(exc_info.value)


class TestTestReportModel:
    """Test TestReport model validation."""

    def test_init_with_pass_status(self):
        """Test initialization with PASS status."""
        report = TestReport(
            task_id="TEST-001",
            test_status="PASS",
            build_successful=True,
            build_errors=[],
            test_summary={
                "total_tests": 20,
                "passed": 20,
                "failed": 0,
                "skipped": 0,
            },
            coverage_percentage=95.0,
            defects_found=[],
            total_tests_generated=20,
            test_files_created=["tests/test_auth.py"],
            test_timestamp="2025-11-19T12:00:00Z",
        )

        assert report.test_status == "PASS"
        assert report.build_successful is True
        assert len(report.defects_found) == 0
        assert report.critical_defects == 0

    def test_severity_counts_auto_calculated(self):
        """Test severity counts are auto-calculated from defects_found."""
        defects = [
            TestDefect(
                defect_id="TEST-DEFECT-001",
                defect_type="5_Security_Vulnerability",
                severity="Critical",
                description="Password stored in plaintext - critical security issue",
                evidence="Found plaintext password",
                phase_injected="Code",
            ),
            TestDefect(
                defect_id="TEST-DEFECT-002",
                defect_type="6_Conventional_Code_Bug",
                severity="High",
                description="Null pointer exception on edge case input",
                evidence="NullPointerException",
                phase_injected="Code",
            ),
            TestDefect(
                defect_id="TEST-DEFECT-003",
                defect_type="6_Conventional_Code_Bug",
                severity="Medium",
                description="Minor validation issue with empty strings",
                evidence="Empty string not handled",
                phase_injected="Code",
            ),
        ]

        report = TestReport(
            task_id="TEST-001",
            test_status="FAIL",
            build_successful=True,
            build_errors=[],
            test_summary={
                "total_tests": 20,
                "passed": 17,
                "failed": 3,
                "skipped": 0,
            },
            defects_found=defects,
            test_timestamp="2025-11-19T12:00:00Z",
        )

        # Counts should be auto-calculated
        assert report.critical_defects == 1
        assert report.high_defects == 1
        assert report.medium_defects == 1
        assert report.low_defects == 0

    def test_test_status_validation_build_failed(self):
        """Test validation: test_status must be BUILD_FAILED if build_successful is False."""
        with pytest.raises(ValidationError) as exc_info:
            TestReport(
                task_id="TEST-001",
                test_status="FAIL",  # Should be BUILD_FAILED
                build_successful=False,
                build_errors=["Some error"],
                test_summary={
                    "total_tests": 0,
                    "passed": 0,
                    "failed": 0,
                    "skipped": 0,
                },
                test_timestamp="2025-11-19T12:00:00Z",
            )
        assert "test_status must be BUILD_FAILED" in str(exc_info.value)

    def test_test_status_validation_pass_with_defects(self):
        """Test validation: PASS cannot have defects."""
        defect = TestDefect(
            defect_id="TEST-DEFECT-001",
            defect_type="6_Conventional_Code_Bug",
            severity="High",
            description="There is a defect but status is PASS - invalid",
            evidence="Test failure",
            phase_injected="Code",
        )

        with pytest.raises(ValidationError) as exc_info:
            TestReport(
                task_id="TEST-001",
                test_status="PASS",  # Inconsistent with defects
                build_successful=True,
                build_errors=[],
                test_summary={
                    "total_tests": 20,
                    "passed": 20,
                    "failed": 0,
                    "skipped": 0,
                },
                defects_found=[defect],  # Has defects!
                test_timestamp="2025-11-19T12:00:00Z",
            )
        assert "test_status cannot be PASS when defects are found" in str(
            exc_info.value
        )

    def test_test_summary_required_keys(self):
        """Test test_summary must have required keys."""
        with pytest.raises(ValidationError) as exc_info:
            TestReport(
                task_id="TEST-001",
                test_status="PASS",
                build_successful=True,
                build_errors=[],
                test_summary={
                    "total_tests": 20,
                    # Missing: passed, failed, skipped
                },
                test_timestamp="2025-11-19T12:00:00Z",
            )
        assert "missing required keys" in str(exc_info.value)

    def test_json_serialization(self):
        """Test model can serialize to/from JSON."""
        report = TestReport(
            task_id="TEST-001",
            test_status="PASS",
            build_successful=True,
            build_errors=[],
            test_summary={
                "total_tests": 10,
                "passed": 10,
                "failed": 0,
                "skipped": 0,
            },
            coverage_percentage=90.0,
            defects_found=[],
            test_timestamp="2025-11-19T12:00:00Z",
        )

        # Serialize to JSON
        json_data = report.model_dump_json()
        assert "TEST-001" in json_data

        # Deserialize from JSON
        report_copy = TestReport.model_validate_json(json_data)
        assert report_copy.task_id == "TEST-001"
        assert report_copy.test_status == "PASS"
