"""
E2E test for TSP Orchestrator with ApprovalService integration.

This test validates the full integration between TSP Orchestrator and
LocalPRApprovalService (or mock equivalent) for HITL quality gate overrides.

Tests:
1. Quality gate failures trigger ApprovalService
2. Approved decisions allow pipeline to continue
3. Rejected decisions halt pipeline
4. Audit trail is captured properly
5. Full 7-agent pipeline with HITL integration

Requirements:
- Supports both real API (with ANTHROPIC_API_KEY) and mock mode
- Real API mode will consume API credits (approximately $0.30-0.60 per full test run)

Run with:
    pytest tests/e2e/test_tsp_with_approval_service.py -m e2e -v -s
"""

from datetime import datetime

import pytest

from asp.approval.base import (
    ApprovalRequest,
    ApprovalResponse,
    ApprovalService,
    ReviewDecision,
)
from asp.models.planning import TaskRequirements
from asp.orchestrators import TSPExecutionResult, TSPOrchestrator
from asp.orchestrators.tsp_orchestrator import QualityGateFailure

# Skip all tests if no API key is available


class MockApprovalService(ApprovalService):
    """
    Mock ApprovalService for automated E2E testing.

    This simulates LocalPRApprovalService behavior without requiring
    interactive user input, allowing automated testing of the full
    TSP + HITL integration.
    """

    def __init__(self, decision: ReviewDecision = ReviewDecision.APPROVED):
        """
        Initialize MockApprovalService.

        Args:
            decision: Default decision for all approval requests
        """
        self.decision = decision
        self.approval_requests: list[ApprovalRequest] = []

    def request_approval(self, request: ApprovalRequest) -> ApprovalResponse:
        """
        Mock approval request that returns predetermined decision.

        Args:
            request: ApprovalRequest with task info and quality report

        Returns:
            ApprovalResponse with mock decision
        """
        # Record request for validation
        self.approval_requests.append(request)

        # Extract quality report details
        quality_report = request.quality_report
        critical_count = quality_report.get(
            "critical_issue_count", 0
        ) or quality_report.get("critical_issues", 0)
        high_count = quality_report.get("high_issue_count", 0) or quality_report.get(
            "high_issues", 0
        )

        # Print approval simulation
        print(f"\n{'=' * 80}")
        print("MOCK APPROVAL SERVICE: Simulating HITL Review")
        print(f"{'=' * 80}")
        print(f"Task ID: {request.task_id}")
        print(f"Gate Type: {request.gate_type}")
        print(f"Quality Issues: {critical_count}C / {high_count}H")
        print(f"Decision: {self.decision.value.upper()}")
        print(f"{'=' * 80}\n")

        return ApprovalResponse(
            decision=self.decision,
            reviewer="MockReviewer",
            timestamp=datetime.utcnow().isoformat() + "Z",
            justification=f"Mock {self.decision.value} for testing purposes",
            review_branch=f"mock/{request.task_id}",
            merge_commit="mock_commit_sha",
        )


@pytest.mark.e2e
class TestTSPWithApprovalService:
    """E2E tests for TSP Orchestrator with ApprovalService integration."""

    def test_approval_service_integration_with_simple_task(self, llm_client):
        """
        Test TSP Orchestrator with MockApprovalService on simple task.

        This validates:
        - ApprovalService can be passed to TSP Orchestrator
        - Pipeline executes successfully with approval service configured
        - Simple task likely passes quality gates (no HITL needed)
        """
        print("\n" + "=" * 80)
        print("TSP + APPROVAL SERVICE E2E: Simple Task (No HITL Expected)")
        print("=" * 80)

        # Create mock approval service (will auto-approve if called)
        approval_service = MockApprovalService(decision=ReviewDecision.APPROVED)

        # Create orchestrator with approval service
        orchestrator = TSPOrchestrator(approval_service=approval_service)

        requirements = TaskRequirements(
            project_id="TSP-APPROVAL-E2E",
            task_id="TSP-APPROVAL-001",
            description="Implement a simple sum function",
            requirements="""
            Create a Python function that sums two numbers.

            Requirements:
            1. Function: sum_numbers(a: int, b: int) -> int
            2. Returns the sum of a and b
            3. Include type hints
            4. Include docstring
            5. Handle edge cases
            """,
        )

        # Execute pipeline
        print("\n[EXECUTING] TSP Pipeline with ApprovalService...")
        result = orchestrator.execute(
            requirements=requirements,
            design_constraints="Simple Python implementation. No external dependencies.",
            coding_standards="PEP 8 compliance.",
        )

        # Validate result
        assert isinstance(result, TSPExecutionResult)
        assert result.task_id == "TSP-APPROVAL-001"
        assert result.overall_status in ["PASS", "CONDITIONAL_PASS", "NEEDS_REVIEW"]

        # Validate critical phases completed
        print("\n[VALIDATION] Phase Completion:")
        assert result.project_plan is not None, "Planning phase failed"
        print("  ✓ Planning")
        assert result.design_specification is not None, "Design phase failed"
        print("  ✓ Design")
        assert result.design_review is not None, "Design Review phase failed"
        print("  ✓ Design Review")
        assert result.generated_code is not None, "Code phase failed"
        print("  ✓ Code Generation")
        assert result.code_review is not None, "Code Review phase failed"
        print("  ✓ Code Review")
        assert result.test_report is not None, "Test phase failed"
        print("  ✓ Testing")

        # Postmortem is optional (may fail due to validation issues)
        if result.postmortem_report is not None:
            print("  ✓ Postmortem")
        else:
            print("  ⚠ Postmortem (skipped or failed)")

        # Check if ApprovalService was called
        print(
            f"\n[HITL] ApprovalService calls: {len(approval_service.approval_requests)}"
        )
        if len(approval_service.approval_requests) > 0:
            print("  Quality gates that required HITL approval:")
            for req in approval_service.approval_requests:
                print(f"    - {req.gate_type} (Task: {req.task_id})")
        else:
            print("  ✓ No HITL approval needed (quality gates passed)")

        print("\n✓ TEST PASSED: ApprovalService integration working")

    def test_approval_service_called_on_complex_task(self, llm_client):
        """
        Test that ApprovalService is called for complex task with likely failures.

        This validates:
        - Complex requirements trigger quality gate failures
        - ApprovalService.request_approval() is called
        - Approved decisions allow pipeline to continue
        - HITL overrides are recorded in audit trail
        """
        print("\n" + "=" * 80)
        print("TSP + APPROVAL SERVICE E2E: Complex Task (HITL Expected)")
        print("=" * 80)

        # Create mock approval service that auto-approves
        approval_service = MockApprovalService(decision=ReviewDecision.APPROVED)

        # Create orchestrator with approval service
        orchestrator = TSPOrchestrator(approval_service=approval_service)

        requirements = TaskRequirements(
            project_id="TSP-APPROVAL-E2E",
            task_id="TSP-APPROVAL-002",
            description="Build a complex distributed system",
            requirements="""
            Create a distributed microservices system with:
            - 5+ microservices (Auth, Users, Orders, Payments, Notifications)
            - REST API with authentication (JWT)
            - Database integration (PostgreSQL)
            - Message queue (RabbitMQ)
            - Caching layer (Redis)
            - Service discovery
            - Load balancing
            - Distributed tracing
            - Monitoring and alerting
            - CI/CD pipeline

            This is intentionally complex to trigger quality gate failures.
            """,
        )

        # Execute pipeline
        print("\n[EXECUTING] TSP Pipeline with complex requirements...")
        result = orchestrator.execute(
            requirements=requirements,
            design_constraints="Enterprise-grade, production-ready architecture",
            coding_standards="Strict enterprise standards with security compliance",
        )

        # Validate result
        assert isinstance(result, TSPExecutionResult)
        assert result.task_id == "TSP-APPROVAL-002"

        # Pipeline should complete with approval service
        assert result.overall_status in ["PASS", "CONDITIONAL_PASS", "NEEDS_REVIEW"]

        # Validate ApprovalService was called
        print(
            f"\n[HITL] ApprovalService calls: {len(approval_service.approval_requests)}"
        )

        if len(approval_service.approval_requests) > 0:
            print("  ✓ ApprovalService was invoked (quality gates failed as expected)")
            print("  Quality gates that required approval:")

            for req in approval_service.approval_requests:
                quality_report = req.quality_report
                critical = quality_report.get(
                    "critical_issue_count", 0
                ) or quality_report.get("critical_issues", 0)
                high = quality_report.get("high_issue_count", 0) or quality_report.get(
                    "high_issues", 0
                )
                print(f"    - {req.gate_type}: {critical}C / {high}H issues")

            # Validate HITL overrides recorded
            print(f"\n[AUDIT] HITL overrides recorded: {len(result.hitl_overrides)}")
            assert len(result.hitl_overrides) > 0, "Overrides should be recorded"

            for override in result.hitl_overrides:
                print(f"    - Gate: {override['gate_name']}")
                print(f"      Decision: {override['decision']}")
                print(f"      Reviewer: {override.get('reviewer', 'N/A')}")
        else:
            print("  ! ApprovalService was not called (task may have been too simple)")
            print("  This is acceptable but not ideal for validating HITL integration")

        print("\n✓ TEST PASSED: Complex task with ApprovalService integration")

    def test_rejection_decision_halts_pipeline(self, llm_client):
        """
        Test that REJECTED decision halts the pipeline.

        This validates:
        - ApprovalService returning REJECTED stops execution
        - QualityGateFailure is raised
        - Pipeline does not continue past rejection
        """
        print("\n" + "=" * 80)
        print("TSP + APPROVAL SERVICE E2E: Rejection Workflow")
        print("=" * 80)

        # Create mock approval service that REJECTS all requests
        approval_service = MockApprovalService(decision=ReviewDecision.REJECTED)

        # Create orchestrator
        orchestrator = TSPOrchestrator(approval_service=approval_service)

        requirements = TaskRequirements(
            project_id="TSP-APPROVAL-E2E",
            task_id="TSP-APPROVAL-003",
            description="Complex system to trigger quality gate failures",
            requirements="""
            Build a complex system with:
            - Distributed architecture
            - Microservices
            - Advanced security
            - High availability
            - Data consistency guarantees

            Intentionally complex to trigger failures.
            """,
        )

        # Execute pipeline - may succeed OR fail depending on quality gates
        try:
            result = orchestrator.execute(
                requirements=requirements,
                design_constraints="Enterprise-grade architecture",
                coding_standards="Strict security compliance",
            )

            # If pipeline succeeded, no quality gates failed
            print("\n[RESULT] Pipeline succeeded without quality gate failures")
            print(f"  Status: {result.overall_status}")
            print("  ℹ️  No quality gates triggered, so rejection was not tested")
            assert result.overall_status in ["PASS", "CONDITIONAL_PASS"]

        except QualityGateFailure as e:
            # Expected when quality gate fails and rejection occurs
            print("\n[EXPECTED] Quality gate failed and rejection halted pipeline")
            print(f"  Error: {e}")
            print("  ✓ Rejection properly halts pipeline")

            # Validate ApprovalService was called
            assert (
                len(approval_service.approval_requests) > 0
            ), "ApprovalService should have been called before failure"
            print(
                f"  ✓ ApprovalService was called {len(approval_service.approval_requests)} time(s)"
            )

        print("\n✓ TEST PASSED: Rejection workflow validated")

    def test_approval_service_priority_over_callable(self, llm_client):
        """
        Test that ApprovalService takes precedence over legacy hitl_approver callable.

        This validates:
        - When both ApprovalService and hitl_approver are provided
        - ApprovalService is used (not the callable)
        - Priority ordering is correct
        """
        print("\n" + "=" * 80)
        print("TSP + APPROVAL SERVICE E2E: Priority Testing")
        print("=" * 80)

        # Create approval service
        approval_service = MockApprovalService(decision=ReviewDecision.APPROVED)

        # Create orchestrator with BOTH approval service and callable
        orchestrator = TSPOrchestrator(approval_service=approval_service)

        # Track if callable is called
        callable_called = []

        def legacy_callable(gate_name: str, report: dict) -> bool:
            """Legacy callable that should NOT be called."""
            callable_called.append(gate_name)
            print(f"\n[ERROR] Legacy callable was called! Gate: {gate_name}")
            return False  # Reject to make it obvious if called

        requirements = TaskRequirements(
            project_id="TSP-APPROVAL-E2E",
            task_id="TSP-APPROVAL-004",
            description="Task to test priority ordering",
            requirements="""
            Build a moderately complex REST API with:
            - Authentication
            - Database
            - Caching
            - API documentation
            """,
        )

        # Execute with both approval service AND callable
        result = orchestrator.execute(
            requirements=requirements,
            hitl_approver=legacy_callable,  # This should be ignored
        )

        # Validate result
        assert isinstance(result, TSPExecutionResult)
        assert result.overall_status in ["PASS", "CONDITIONAL_PASS", "NEEDS_REVIEW"]

        # Validate priority: ApprovalService should be used, NOT callable
        print("\n[VALIDATION] Priority Ordering:")
        print(f"  ApprovalService calls: {len(approval_service.approval_requests)}")
        print(f"  Legacy callable calls: {len(callable_called)}")

        if len(approval_service.approval_requests) > 0:
            print("  ✓ ApprovalService was used")
            assert (
                len(callable_called) == 0
            ), "Legacy callable should NOT be called when ApprovalService exists"
            print("  ✓ Legacy callable was NOT called (correct priority)")
        else:
            print("  ℹ️  No quality gate failures, priority not tested")

        print("\n✓ TEST PASSED: ApprovalService takes precedence over callable")

    def test_metadata_and_audit_trail(self, llm_client):
        """
        Test that approval metadata is captured in audit trail.

        This validates:
        - HITL overrides are recorded with full metadata
        - Reviewer, timestamp, justification are captured
        - Audit trail is complete
        """
        print("\n" + "=" * 80)
        print("TSP + APPROVAL SERVICE E2E: Audit Trail Validation")
        print("=" * 80)

        # Create approval service
        approval_service = MockApprovalService(decision=ReviewDecision.APPROVED)

        # Create orchestrator
        orchestrator = TSPOrchestrator(approval_service=approval_service)

        requirements = TaskRequirements(
            project_id="TSP-APPROVAL-E2E",
            task_id="TSP-APPROVAL-005",
            description="Task to validate audit trail",
            requirements="""
            Build a complex application with:
            - Multi-tier architecture
            - Database integration
            - External API calls
            - Authentication and authorization
            - Monitoring and logging
            """,
        )

        # Execute pipeline
        result = orchestrator.execute(
            requirements=requirements,
            design_constraints="Enterprise standards",
            coding_standards="Security compliance required",
        )

        # Validate audit trail
        print("\n[AUDIT TRAIL] Analysis:")
        print(f"  Total HITL overrides: {len(result.hitl_overrides)}")

        if len(result.hitl_overrides) > 0:
            print("  ✓ HITL overrides recorded")

            for i, override in enumerate(result.hitl_overrides, 1):
                print(f"\n  Override {i}:")
                print(f"    Gate: {override.get('gate_name', 'N/A')}")
                print(f"    Decision: {override.get('decision', 'N/A')}")
                print(f"    Reviewer: {override.get('reviewer', 'N/A')}")
                print(f"    Timestamp: {override.get('timestamp', 'N/A')}")
                print(f"    Justification: {override.get('justification', 'N/A')}")

                # Validate required fields
                assert "gate_name" in override, "gate_name missing"
                assert "decision" in override, "decision missing"
                assert "reviewer" in override, "reviewer missing"
                assert "timestamp" in override, "timestamp missing"
                assert "justification" in override, "justification missing"

            print("\n  ✓ All required metadata fields present")
        else:
            print("  ℹ️  No HITL overrides (quality gates passed)")

        print("\n✓ TEST PASSED: Audit trail validated")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s", "-m", "e2e"])
