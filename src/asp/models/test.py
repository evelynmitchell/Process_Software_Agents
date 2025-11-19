"""
Pydantic models for Test Agent (FR-6).

The Test Agent validates generated code through build verification, test generation,
test execution, and defect logging. This module defines the input/output data structures
for the testing phase.

Models:
    - TestInput: Input to Test Agent (approved code + design spec)
    - TestDefect: Individual defect found during testing
    - TestReport: Complete test execution report (output)

Test Agent Flow:
    1. Receives TestInput (GeneratedCode from Code Agent + DesignSpecification)
    2. Validates build/compilation
    3. Generates and executes unit tests
    4. Logs defects using AI Defect Taxonomy
    5. Returns TestReport with pass/fail status and defect list

Author: ASP Development Team
Date: November 19, 2025
"""

from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field, field_validator, model_validator

from asp.models.code import GeneratedCode
from asp.models.design import DesignSpecification


# =============================================================================
# Input Models
# =============================================================================


class TestInput(BaseModel):
    """
    Input data for Test Agent.

    Contains the approved code (post-review) and design specification
    needed to generate comprehensive tests and validate functionality.

    Attributes:
        task_id: Unique task identifier
        generated_code: Approved code from Code Agent (post Code Review)
        design_specification: Design specification for test generation
        test_framework: Testing framework to use (pytest, unittest, etc.)
        coverage_target: Target test coverage percentage (0-100)
    """

    task_id: str = Field(
        ...,
        min_length=3,
        description="Unique task identifier",
    )

    generated_code: GeneratedCode = Field(
        ...,
        description="Approved code from Code Agent (post-review)",
    )

    design_specification: DesignSpecification = Field(
        ...,
        description="Design specification for test generation and validation",
    )

    test_framework: str = Field(
        default="pytest",
        description="Testing framework (pytest, unittest, nose2, etc.)",
    )

    coverage_target: float = Field(
        default=80.0,
        ge=0.0,
        le=100.0,
        description="Target test coverage percentage",
    )

    @field_validator("task_id")
    @classmethod
    def validate_task_id(cls, v: str) -> str:
        """Validate task_id format."""
        if not v or len(v.strip()) < 3:
            raise ValueError("task_id must be at least 3 characters")
        return v.strip()

    class Config:
        json_schema_extra = {
            "example": {
                "task_id": "TEST-001",
                "generated_code": {
                    "task_id": "TEST-001",
                    "files": [
                        {
                            "file_path": "src/api/auth.py",
                            "content": "# Authentication module...",
                            "file_type": "source",
                        }
                    ],
                },
                "design_specification": {
                    "task_id": "TEST-001",
                    "architecture_overview": "REST API with JWT authentication",
                },
                "test_framework": "pytest",
                "coverage_target": 85.0,
            }
        }


# =============================================================================
# Defect Models
# =============================================================================


class TestDefect(BaseModel):
    """
    Defect found during testing phase.

    Represents a single bug, build error, or test failure discovered by the
    Test Agent. Uses the AI Defect Taxonomy (FR-11) for classification.

    Attributes:
        defect_id: Unique defect identifier (e.g., "TEST-DEFECT-001")
        defect_type: Classification from AI Defect Taxonomy
        severity: Impact level (Critical, High, Medium, Low)
        description: Human-readable defect description
        evidence: Test failure output, stack trace, or build error message
        phase_injected: Phase where defect was introduced
        phase_removed: Phase where defect was detected (always "Test")
        file_path: Optional file path where defect occurs
        line_number: Optional line number where defect occurs
        semantic_unit_id: Optional semantic unit ID for traceability
        component_id: Optional component ID for traceability
    """

    defect_id: str = Field(
        ...,
        pattern=r"^TEST-DEFECT-\d{3}$",
        description="Unique defect identifier (e.g., TEST-DEFECT-001)",
    )

    defect_type: Literal[
        "1_Planning_Failure",
        "2_Prompt_Misinterpretation",
        "3_Tool_Use_Error",
        "4_Hallucination",
        "5_Security_Vulnerability",
        "6_Conventional_Code_Bug",
        "7_Task_Execution_Error",
        "8_Alignment_Deviation",
    ] = Field(
        ...,
        description="AI Defect Taxonomy classification (FR-11)",
    )

    severity: Literal["Critical", "High", "Medium", "Low"] = Field(
        ...,
        description=(
            "- Critical: System failure, data loss, security breach\n"
            "- High: Major functionality broken, incorrect results\n"
            "- Medium: Minor functionality issue, degraded performance\n"
            "- Low: Cosmetic issue, minor edge case"
        ),
    )

    description: str = Field(
        ...,
        min_length=20,
        description="Clear, actionable description of the defect",
    )

    evidence: str = Field(
        ...,
        min_length=10,
        description="Test failure output, stack trace, or build error message",
    )

    phase_injected: Literal["Planning", "Design", "Code"] = Field(
        ...,
        description="Phase where defect was introduced",
    )

    phase_removed: str = Field(
        default="Test",
        description="Phase where defect was detected (always 'Test' for TestAgent)",
    )

    file_path: Optional[str] = Field(
        default=None,
        description="File path where defect occurs (if applicable)",
    )

    line_number: Optional[int] = Field(
        default=None,
        ge=1,
        description="Line number where defect occurs (if applicable)",
    )

    semantic_unit_id: Optional[str] = Field(
        default=None,
        description="Semantic unit ID from Planning Agent (for traceability)",
    )

    component_id: Optional[str] = Field(
        default=None,
        description="Component ID from Design Agent (for traceability)",
    )

    class Config:
        json_schema_extra = {
            "example": {
                "defect_id": "TEST-DEFECT-001",
                "defect_type": "6_Conventional_Code_Bug",
                "severity": "High",
                "description": "Authentication fails when password contains special characters",
                "evidence": "AssertionError: Expected 200, got 401\nTest: test_login_special_chars",
                "phase_injected": "Code",
                "phase_removed": "Test",
                "file_path": "src/api/auth.py",
                "line_number": 45,
                "semantic_unit_id": "SU-001",
                "component_id": "AUTH-001",
            }
        }


# =============================================================================
# Output Models
# =============================================================================


class TestReport(BaseModel):
    """
    Complete test execution report (Test Agent output).

    Contains build status, test execution results, defect list, and coverage metrics.
    This is the primary output of the Test Agent and serves as a quality gate.

    Attributes:
        task_id: Unique task identifier
        test_status: Overall test status (PASS, FAIL, BUILD_FAILED)
        build_successful: Whether code built/compiled successfully
        build_errors: List of build/compilation errors
        test_summary: Test execution counts (total, passed, failed, skipped)
        coverage_percentage: Test coverage percentage (if available)
        defects_found: List of defects discovered during testing
        total_tests_generated: Number of tests generated by Test Agent
        test_files_created: List of test file paths created
        critical_defects: Count of critical severity defects
        high_defects: Count of high severity defects
        medium_defects: Count of medium severity defects
        low_defects: Count of low severity defects
        agent_version: Test Agent version
        test_timestamp: ISO 8601 timestamp of test execution
        test_duration_seconds: Total test execution time in seconds
    """

    task_id: str = Field(
        ...,
        min_length=3,
        description="Unique task identifier",
    )

    test_status: Literal["PASS", "FAIL", "BUILD_FAILED"] = Field(
        ...,
        description=(
            "- PASS: All tests passed, build successful, no defects\n"
            "- FAIL: Tests failed or defects found\n"
            "- BUILD_FAILED: Compilation/build errors prevent testing"
        ),
    )

    # Build results
    build_successful: bool = Field(
        ...,
        description="Whether code built/compiled successfully",
    )

    build_errors: list[str] = Field(
        default_factory=list,
        description="List of build/compilation error messages",
    )

    # Test execution summary
    test_summary: dict[str, int] = Field(
        ...,
        description="Test counts: {total_tests, passed, failed, skipped}",
    )

    # Test coverage
    coverage_percentage: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=100.0,
        description="Test coverage percentage (if available)",
    )

    # Defects found
    defects_found: list[TestDefect] = Field(
        default_factory=list,
        description="All defects identified during testing",
    )

    # Generated tests metadata
    total_tests_generated: int = Field(
        default=0,
        ge=0,
        description="Number of tests generated by Test Agent",
    )

    test_files_created: list[str] = Field(
        default_factory=list,
        description="List of test file paths created",
    )

    # Severity counts (auto-calculated)
    critical_defects: int = Field(
        default=0,
        ge=0,
        description="Count of critical severity defects",
    )

    high_defects: int = Field(
        default=0,
        ge=0,
        description="Count of high severity defects",
    )

    medium_defects: int = Field(
        default=0,
        ge=0,
        description="Count of medium severity defects",
    )

    low_defects: int = Field(
        default=0,
        ge=0,
        description="Count of low severity defects",
    )

    # Agent metadata
    agent_version: str = Field(
        default="1.0.0",
        description="Test Agent version",
    )

    test_timestamp: str = Field(
        ...,
        description="ISO 8601 timestamp of test execution",
    )

    test_duration_seconds: Optional[float] = Field(
        default=None,
        ge=0,
        description="Total test execution time in seconds",
    )

    @model_validator(mode="after")
    def calculate_statistics(self) -> "TestReport":
        """Auto-calculate defect counts from defects_found."""
        self.critical_defects = sum(
            1 for d in self.defects_found if d.severity == "Critical"
        )
        self.high_defects = sum(1 for d in self.defects_found if d.severity == "High")
        self.medium_defects = sum(
            1 for d in self.defects_found if d.severity == "Medium"
        )
        self.low_defects = sum(1 for d in self.defects_found if d.severity == "Low")
        return self

    @model_validator(mode="after")
    def validate_test_status(self) -> "TestReport":
        """Validate test_status matches defect/build state."""
        if not self.build_successful:
            if self.test_status != "BUILD_FAILED":
                raise ValueError(
                    "test_status must be BUILD_FAILED when build_successful is False"
                )
        elif len(self.defects_found) > 0:
            if self.test_status == "PASS":
                raise ValueError("test_status cannot be PASS when defects are found")
        elif self.test_summary.get("failed", 0) > 0:
            if self.test_status == "PASS":
                raise ValueError(
                    "test_status cannot be PASS when tests have failed"
                )
        return self

    @model_validator(mode="after")
    def validate_test_summary(self) -> "TestReport":
        """Validate test_summary has required keys."""
        required_keys = {"total_tests", "passed", "failed", "skipped"}
        missing_keys = required_keys - set(self.test_summary.keys())
        if missing_keys:
            raise ValueError(
                f"test_summary missing required keys: {missing_keys}"
            )
        return self

    class Config:
        json_schema_extra = {
            "example": {
                "task_id": "TEST-001",
                "test_status": "PASS",
                "build_successful": True,
                "build_errors": [],
                "test_summary": {
                    "total_tests": 25,
                    "passed": 25,
                    "failed": 0,
                    "skipped": 0,
                },
                "coverage_percentage": 92.5,
                "defects_found": [],
                "total_tests_generated": 25,
                "test_files_created": [
                    "tests/test_auth.py",
                    "tests/test_users.py",
                ],
                "critical_defects": 0,
                "high_defects": 0,
                "medium_defects": 0,
                "low_defects": 0,
                "agent_version": "1.0.0",
                "test_timestamp": "2025-11-19T12:00:00Z",
                "test_duration_seconds": 12.5,
            }
        }
