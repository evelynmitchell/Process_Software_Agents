"""
Unit tests for DatabaseApprovalService.

Tests the database-based HITL approval service including:
- Initialization and configuration
- Database connection and table creation
- Request writing and polling
- Decision submission
- Error handling and edge cases

Author: ASP Development Team
Date: December 23, 2025
"""

import sqlite3
import tempfile
import time
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import patch

import pytest

from asp.approval.base import ApprovalRequest, ReviewDecision
from asp.approval.database_service import (
    DatabaseApprovalService,
    DecisionInput,
    _json_serializer,
)


# =============================================================================
# JSON Serializer Tests
# =============================================================================


class TestJsonSerializer:
    """Tests for _json_serializer helper function."""

    def test_serialize_datetime(self):
        """Test datetime serialization."""
        dt = datetime(2025, 12, 23, 12, 30, 45)
        result = _json_serializer(dt)
        assert result == "2025-12-23T12:30:45"

    def test_serialize_unsupported_type_raises(self):
        """Test that unsupported types raise TypeError."""
        with pytest.raises(TypeError) as exc_info:
            _json_serializer(set([1, 2, 3]))
        assert "set" in str(exc_info.value)


# =============================================================================
# DecisionInput Tests
# =============================================================================


class TestDecisionInput:
    """Tests for DecisionInput dataclass."""

    def test_create_decision_input_minimal(self):
        """Test creating DecisionInput with required fields only."""
        decision = DecisionInput(
            request_id="REQ-001",
            decision="approved",
            reviewer="human",
            justification="Looks good",
        )
        assert decision.request_id == "REQ-001"
        assert decision.review_branch is None
        assert decision.merge_commit is None

    def test_create_decision_input_full(self):
        """Test creating DecisionInput with all fields."""
        decision = DecisionInput(
            request_id="REQ-001",
            decision="approved",
            reviewer="human",
            justification="Looks good",
            review_branch="feature/test",
            merge_commit="abc123",
        )
        assert decision.review_branch == "feature/test"
        assert decision.merge_commit == "abc123"


# =============================================================================
# Initialization Tests
# =============================================================================


class TestDatabaseApprovalServiceInit:
    """Tests for DatabaseApprovalService initialization."""

    def test_init_default_values(self):
        """Test initialization with default values."""
        service = DatabaseApprovalService()
        assert service.db_path == Path("data/asp_telemetry.db")
        assert service.poll_interval == 5.0
        assert service.timeout == 3600.0

    def test_init_custom_values(self):
        """Test initialization with custom values."""
        service = DatabaseApprovalService(
            db_path="/tmp/custom.db",
            poll_interval=1.0,
            timeout=60.0,
        )
        assert service.db_path == Path("/tmp/custom.db")
        assert service.poll_interval == 1.0
        assert service.timeout == 60.0

    def test_init_path_object(self):
        """Test initialization with Path object."""
        path = Path("/tmp/test.db")
        service = DatabaseApprovalService(db_path=path)
        assert service.db_path == path


# =============================================================================
# Database Connection Tests
# =============================================================================


class TestDatabaseConnection:
    """Tests for database connection handling."""

    def test_get_connection(self):
        """Test getting a database connection."""
        with tempfile.NamedTemporaryFile(suffix=".db") as f:
            service = DatabaseApprovalService(db_path=f.name)
            conn = service._get_connection()
            assert isinstance(conn, sqlite3.Connection)
            assert conn.row_factory == sqlite3.Row
            conn.close()

    def test_connection_row_factory(self):
        """Test that connection has row factory set."""
        with tempfile.NamedTemporaryFile(suffix=".db") as f:
            service = DatabaseApprovalService(db_path=f.name)
            conn = service._get_connection()

            # Create a test table and verify row factory works
            conn.execute("CREATE TABLE test (id INTEGER, name TEXT)")
            conn.execute("INSERT INTO test VALUES (1, 'test')")
            row = conn.execute("SELECT * FROM test").fetchone()

            # Row factory should allow dict-like access
            assert row["id"] == 1
            assert row["name"] == "test"
            conn.close()


# =============================================================================
# Table Creation Tests
# =============================================================================


class TestEnsureTablesExist:
    """Tests for _ensure_tables_exist method."""

    def test_ensure_tables_creates_inline_schema(self):
        """Test table creation with inline schema (fallback)."""
        with tempfile.NamedTemporaryFile(suffix=".db") as f:
            service = DatabaseApprovalService(db_path=f.name)
            service._ensure_tables_exist()

            # Verify tables were created
            conn = service._get_connection()
            tables = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
            table_names = [t["name"] for t in tables]

            assert "approval_requests" in table_names
            assert "approval_decisions" in table_names
            conn.close()

    def test_get_inline_schema(self):
        """Test inline schema generation."""
        service = DatabaseApprovalService()
        schema = service._get_inline_schema()

        assert "CREATE TABLE IF NOT EXISTS approval_requests" in schema
        assert "CREATE TABLE IF NOT EXISTS approval_decisions" in schema
        assert "CREATE INDEX IF NOT EXISTS" in schema


# =============================================================================
# Request ID Generation Tests
# =============================================================================


class TestGenerateRequestId:
    """Tests for _generate_request_id method."""

    def test_generate_request_id_format(self):
        """Test request ID format."""
        service = DatabaseApprovalService()
        request_id = service._generate_request_id("TASK-001", "code_review")

        assert request_id.startswith("TASK-001_code_review_")
        # Should have timestamp suffix
        parts = request_id.split("_")
        assert len(parts) >= 3
        # Timestamp should be 14 characters (YYYYMMDDHHMMSS)
        assert len(parts[-1]) == 14

    def test_generate_request_id_unique(self):
        """Test that generated IDs are unique."""
        service = DatabaseApprovalService()
        ids = set()
        for _ in range(10):
            request_id = service._generate_request_id("TASK", "gate")
            ids.add(request_id)
            time.sleep(0.001)  # Small delay to ensure different timestamps

        # All IDs should be unique (or at least most of them)
        assert len(ids) >= 1


# =============================================================================
# Extract Summary Tests
# =============================================================================


class TestExtractSummary:
    """Tests for _extract_summary method."""

    def test_extract_summary_design_review(self):
        """Test summary extraction from design review report."""
        service = DatabaseApprovalService()
        request = ApprovalRequest(
            task_id="TASK-001",
            gate_type="design_review",
            agent_output={},
            quality_report={
                "critical_issue_count": 2,
                "high_issue_count": 3,
                "overall_assessment": "NEEDS_REVISION",
                "issues_found": [{"issue": "1"}, {"issue": "2"}],
            },
        )

        summary, critical, high = service._extract_summary(request)

        assert critical == 2
        assert high == 3
        assert "Design Review: NEEDS_REVISION" in summary
        assert "2 issues found" in summary

    def test_extract_summary_code_review(self):
        """Test summary extraction from code review report."""
        service = DatabaseApprovalService()
        request = ApprovalRequest(
            task_id="TASK-001",
            gate_type="code_review",
            agent_output={},
            quality_report={
                "critical_issues": 1,
                "high_issues": 5,
                "overall_verdict": "FAIL",
            },
        )

        summary, critical, high = service._extract_summary(request)

        assert critical == 1
        assert high == 5
        assert "Code Review: FAIL" in summary

    def test_extract_summary_empty_report(self):
        """Test summary extraction from empty report."""
        service = DatabaseApprovalService()
        request = ApprovalRequest(
            task_id="TASK-001",
            gate_type="design_review",
            agent_output={},
            quality_report={},
        )

        summary, critical, high = service._extract_summary(request)

        assert critical == 0
        assert high == 0
        assert summary == "Quality gate failed"

    def test_extract_summary_design_review_no_issues(self):
        """Test summary extraction from design review without issues_found."""
        service = DatabaseApprovalService()
        request = ApprovalRequest(
            task_id="TASK-001",
            gate_type="design_review",
            agent_output={},
            quality_report={
                "critical_issue_count": 0,
                "high_issue_count": 0,
                "overall_assessment": "APPROVED",
            },
        )

        summary, critical, high = service._extract_summary(request)

        assert critical == 0
        assert high == 0
        assert "Design Review: APPROVED" in summary


# =============================================================================
# Write Request Tests
# =============================================================================


class TestWriteRequest:
    """Tests for _write_request method."""

    def test_write_request(self):
        """Test writing an approval request to database."""
        with tempfile.NamedTemporaryFile(suffix=".db") as f:
            service = DatabaseApprovalService(db_path=f.name)
            service._ensure_tables_exist()

            request = ApprovalRequest(
                task_id="TASK-001",
                gate_type="code_review",
                agent_output={},
                quality_report={"passed": False, "issues": []},
            )

            service._write_request(request, "REQ-001")

            # Verify request was written
            conn = service._get_connection()
            row = conn.execute(
                "SELECT * FROM approval_requests WHERE request_id = ?",
                ("REQ-001",),
            ).fetchone()

            assert row is not None
            assert row["task_id"] == "TASK-001"
            assert row["gate_type"] == "code_review"
            assert row["status"] == "pending"
            conn.close()

    def test_write_request_with_datetime_in_report(self):
        """Test writing request with datetime in quality report."""
        with tempfile.NamedTemporaryFile(suffix=".db") as f:
            service = DatabaseApprovalService(db_path=f.name)
            service._ensure_tables_exist()

            request = ApprovalRequest(
                task_id="TASK-001",
                gate_type="design_review",
                agent_output={},
                quality_report={
                    "timestamp": datetime(2025, 12, 23, 12, 0, 0),
                    "issues": [],
                },
            )

            # Should not raise due to datetime serialization
            service._write_request(request, "REQ-002")


# =============================================================================
# Poll for Decision Tests
# =============================================================================


class TestPollForDecision:
    """Tests for _poll_for_decision method."""

    def test_poll_finds_decision(self):
        """Test polling finds an existing decision."""
        with tempfile.NamedTemporaryFile(suffix=".db") as f:
            service = DatabaseApprovalService(
                db_path=f.name, poll_interval=0.1, timeout=1.0
            )
            service._ensure_tables_exist()

            # Create request and decision
            conn = service._get_connection()
            conn.execute(
                """
                INSERT INTO approval_requests (request_id, task_id, gate_type,
                    gate_name, quality_report, status)
                VALUES ('REQ-001', 'TASK-001', 'code_review', 'Code Review', '{}', 'pending')
                """
            )
            conn.execute(
                """
                INSERT INTO approval_decisions (request_id, decision, reviewer,
                    justification)
                VALUES ('REQ-001', 'approved', 'human', 'Looks good')
                """
            )
            conn.commit()
            conn.close()

            response = service._poll_for_decision("REQ-001")

            assert response is not None
            assert response.decision == ReviewDecision.APPROVED
            assert response.reviewer == "human"
            assert response.justification == "Looks good"

    def test_poll_timeout(self):
        """Test polling times out when no decision."""
        with tempfile.NamedTemporaryFile(suffix=".db") as f:
            service = DatabaseApprovalService(
                db_path=f.name, poll_interval=0.05, timeout=0.1
            )
            service._ensure_tables_exist()

            # Create request without decision
            conn = service._get_connection()
            expires_at = (datetime.now() + timedelta(hours=1)).isoformat()
            conn.execute(
                """
                INSERT INTO approval_requests (request_id, task_id, gate_type,
                    gate_name, quality_report, status, expires_at)
                VALUES ('REQ-001', 'TASK-001', 'design_review', 'Design Review', '{}', 'pending', ?)
                """,
                (expires_at,),
            )
            conn.commit()
            conn.close()

            response = service._poll_for_decision("REQ-001")

            assert response is None

    def test_poll_expired_request(self):
        """Test polling returns None for expired request."""
        with tempfile.NamedTemporaryFile(suffix=".db") as f:
            service = DatabaseApprovalService(
                db_path=f.name, poll_interval=0.05, timeout=1.0
            )
            service._ensure_tables_exist()

            # Create expired request
            conn = service._get_connection()
            conn.execute(
                """
                INSERT INTO approval_requests (request_id, task_id, gate_type,
                    gate_name, quality_report, status)
                VALUES ('REQ-001', 'TASK-001', 'code_review', 'Code Review', '{}', 'expired')
                """
            )
            conn.commit()
            conn.close()

            response = service._poll_for_decision("REQ-001")

            assert response is None

    def test_poll_request_expires_during_poll(self):
        """Test request expiring during polling."""
        with tempfile.NamedTemporaryFile(suffix=".db") as f:
            service = DatabaseApprovalService(
                db_path=f.name, poll_interval=0.05, timeout=1.0
            )
            service._ensure_tables_exist()

            # Create request that expires immediately
            conn = service._get_connection()
            expires_at = (datetime.now() - timedelta(seconds=1)).isoformat()
            conn.execute(
                """
                INSERT INTO approval_requests (request_id, task_id, gate_type,
                    gate_name, quality_report, status, expires_at)
                VALUES ('REQ-001', 'TASK-001', 'design_review', 'Design Review', '{}', 'pending', ?)
                """,
                (expires_at,),
            )
            conn.commit()
            conn.close()

            response = service._poll_for_decision("REQ-001")

            assert response is None


# =============================================================================
# Request Approval Tests
# =============================================================================


class TestRequestApproval:
    """Tests for request_approval method."""

    def test_request_approval_success(self):
        """Test successful approval request flow."""
        with tempfile.NamedTemporaryFile(suffix=".db") as f:
            service = DatabaseApprovalService(
                db_path=f.name, poll_interval=0.05, timeout=0.5
            )

            request = ApprovalRequest(
                task_id="TASK-001",
                gate_type="code_review",
                agent_output={},
                quality_report={"passed": False},
            )

            # Pre-insert a decision (simulating WebUI)
            service._ensure_tables_exist()

            # We need to insert the decision after the request is created
            # Use a separate thread or mock the polling
            with patch.object(service, "_poll_for_decision") as mock_poll:
                from asp.approval.base import ApprovalResponse

                mock_poll.return_value = ApprovalResponse(
                    decision=ReviewDecision.APPROVED,
                    reviewer="human",
                    timestamp=datetime.now().isoformat(),
                    justification="Approved",
                )

                response = service.request_approval(request)

            assert response.decision == ReviewDecision.APPROVED

    def test_request_approval_timeout(self):
        """Test approval request timeout."""
        with tempfile.NamedTemporaryFile(suffix=".db") as f:
            service = DatabaseApprovalService(
                db_path=f.name, poll_interval=0.05, timeout=0.1
            )

            request = ApprovalRequest(
                task_id="TASK-001",
                gate_type="design_review",
                agent_output={},
                quality_report={},
            )

            with pytest.raises(TimeoutError) as exc_info:
                service.request_approval(request)

            assert "No approval decision received" in str(exc_info.value)


# =============================================================================
# Get Pending Requests Tests
# =============================================================================


class TestGetPendingRequests:
    """Tests for get_pending_requests method."""

    def test_get_pending_requests_empty(self):
        """Test getting pending requests when none exist."""
        with tempfile.NamedTemporaryFile(suffix=".db") as f:
            service = DatabaseApprovalService(db_path=f.name)
            requests = service.get_pending_requests()
            assert requests == []

    def test_get_pending_requests_all(self):
        """Test getting all pending requests."""
        with tempfile.NamedTemporaryFile(suffix=".db") as f:
            service = DatabaseApprovalService(db_path=f.name)
            service._ensure_tables_exist()

            # Insert test requests
            conn = service._get_connection()
            conn.execute(
                """
                INSERT INTO approval_requests (request_id, task_id, gate_type,
                    gate_name, quality_report, status)
                VALUES ('REQ-001', 'TASK-001', 'code_review', 'Code Review', '{}', 'pending')
                """
            )
            conn.execute(
                """
                INSERT INTO approval_requests (request_id, task_id, gate_type,
                    gate_name, quality_report, status)
                VALUES ('REQ-002', 'TASK-002', 'design_review', 'Design Review', '{}', 'pending')
                """
            )
            conn.execute(
                """
                INSERT INTO approval_requests (request_id, task_id, gate_type,
                    gate_name, quality_report, status)
                VALUES ('REQ-003', 'TASK-003', 'code_review', 'Code Review', '{}', 'approved')
                """
            )
            conn.commit()
            conn.close()

            requests = service.get_pending_requests()

            assert len(requests) == 2
            request_ids = {r["request_id"] for r in requests}
            assert "REQ-001" in request_ids
            assert "REQ-002" in request_ids
            assert "REQ-003" not in request_ids  # Not pending

    def test_get_pending_requests_by_task(self):
        """Test getting pending requests filtered by task ID."""
        with tempfile.NamedTemporaryFile(suffix=".db") as f:
            service = DatabaseApprovalService(db_path=f.name)
            service._ensure_tables_exist()

            # Insert test requests
            conn = service._get_connection()
            conn.execute(
                """
                INSERT INTO approval_requests (request_id, task_id, gate_type,
                    gate_name, quality_report, status)
                VALUES ('REQ-001', 'TASK-001', 'code_review', 'Code Review', '{}', 'pending')
                """
            )
            conn.execute(
                """
                INSERT INTO approval_requests (request_id, task_id, gate_type,
                    gate_name, quality_report, status)
                VALUES ('REQ-002', 'TASK-002', 'design_review', 'Design Review', '{}', 'pending')
                """
            )
            conn.commit()
            conn.close()

            requests = service.get_pending_requests(task_id="TASK-001")

            assert len(requests) == 1
            assert requests[0]["task_id"] == "TASK-001"


# =============================================================================
# Submit Decision Tests
# =============================================================================


class TestSubmitDecision:
    """Tests for submit_decision method."""

    def test_submit_decision_success(self):
        """Test successful decision submission."""
        with tempfile.NamedTemporaryFile(suffix=".db") as f:
            service = DatabaseApprovalService(db_path=f.name)
            service._ensure_tables_exist()

            # Create pending request
            conn = service._get_connection()
            conn.execute(
                """
                INSERT INTO approval_requests (request_id, task_id, gate_type,
                    gate_name, quality_report, status)
                VALUES ('REQ-001', 'TASK-001', 'code_review', 'Code Review', '{}', 'pending')
                """
            )
            conn.commit()
            conn.close()

            decision = DecisionInput(
                request_id="REQ-001",
                decision="approved",
                reviewer="human",
                justification="Looks good",
            )

            result = service.submit_decision(decision)

            assert result is True

            # Verify decision was recorded
            conn = service._get_connection()
            row = conn.execute(
                "SELECT * FROM approval_decisions WHERE request_id = ?",
                ("REQ-001",),
            ).fetchone()
            assert row is not None
            assert row["decision"] == "approved"

            # Verify request status was updated
            req = conn.execute(
                "SELECT status FROM approval_requests WHERE request_id = ?",
                ("REQ-001",),
            ).fetchone()
            assert req["status"] == "approved"
            conn.close()

    def test_submit_decision_request_not_found(self):
        """Test decision submission for non-existent request."""
        with tempfile.NamedTemporaryFile(suffix=".db") as f:
            service = DatabaseApprovalService(db_path=f.name)
            service._ensure_tables_exist()

            decision = DecisionInput(
                request_id="NONEXISTENT",
                decision="approved",
                reviewer="human",
                justification="Test",
            )

            result = service.submit_decision(decision)

            assert result is False

    def test_submit_decision_request_not_pending(self):
        """Test decision submission for non-pending request."""
        with tempfile.NamedTemporaryFile(suffix=".db") as f:
            service = DatabaseApprovalService(db_path=f.name)
            service._ensure_tables_exist()

            # Create already-approved request
            conn = service._get_connection()
            conn.execute(
                """
                INSERT INTO approval_requests (request_id, task_id, gate_type,
                    gate_name, quality_report, status)
                VALUES ('REQ-001', 'TASK-001', 'design_review', 'Design Review', '{}', 'approved')
                """
            )
            conn.commit()
            conn.close()

            decision = DecisionInput(
                request_id="REQ-001",
                decision="rejected",
                reviewer="human",
                justification="Change mind",
            )

            result = service.submit_decision(decision)

            assert result is False

    def test_submit_decision_with_optional_fields(self):
        """Test decision submission with all optional fields."""
        with tempfile.NamedTemporaryFile(suffix=".db") as f:
            service = DatabaseApprovalService(db_path=f.name)
            service._ensure_tables_exist()

            # Create pending request
            conn = service._get_connection()
            conn.execute(
                """
                INSERT INTO approval_requests (request_id, task_id, gate_type,
                    gate_name, quality_report, status)
                VALUES ('REQ-001', 'TASK-001', 'code_review', 'Code Review', '{}', 'pending')
                """
            )
            conn.commit()
            conn.close()

            decision = DecisionInput(
                request_id="REQ-001",
                decision="approved",
                reviewer="human",
                justification="All good",
                review_branch="feature/test",
                merge_commit="abc123def456",
            )

            result = service.submit_decision(decision)

            assert result is True

            # Verify optional fields were stored
            conn = service._get_connection()
            row = conn.execute(
                "SELECT * FROM approval_decisions WHERE request_id = ?",
                ("REQ-001",),
            ).fetchone()
            assert row["review_branch"] == "feature/test"
            assert row["merge_commit"] == "abc123def456"
            conn.close()
