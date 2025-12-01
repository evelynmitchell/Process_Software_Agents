"""
Unit tests for Telemetry System.

Tests the telemetry infrastructure including:
- Database connection management
- Agent cost tracking decorator
- Defect logging decorator
- Database insertion operations
- Langfuse integration (mocked)
- Error handling and resilience
"""

import pytest
import sqlite3
import tempfile
import time
import os
from datetime import datetime
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch, call
from contextlib import contextmanager

from asp.telemetry.telemetry import (
    get_db_connection,
    insert_agent_cost,
    insert_defect,
    track_agent_cost,
    get_langfuse_client,
    get_user_id,
    DefectType,
)


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def temp_db():
    """Create a temporary database for testing."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = Path(f.name)

    # Initialize schema
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()

    # Create agent_cost_vector table (actual table name used)
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS agent_cost_vector (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            task_id TEXT NOT NULL,
            subtask_id TEXT,
            project_id TEXT,
            user_id TEXT,
            agent_role TEXT NOT NULL,
            agent_version TEXT,
            agent_iteration INTEGER DEFAULT 1,
            metric_type TEXT NOT NULL,
            metric_value REAL NOT NULL,
            metric_unit TEXT NOT NULL,
            llm_model TEXT,
            llm_provider TEXT,
            metadata TEXT
        )
    """
    )

    # Create defect_log table
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS defect_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            defect_id TEXT UNIQUE NOT NULL,
            created_at TEXT NOT NULL,
            task_id TEXT NOT NULL,
            project_id TEXT,
            user_id TEXT,
            defect_type TEXT NOT NULL,
            severity TEXT NOT NULL,
            description TEXT NOT NULL,
            phase_injected TEXT NOT NULL,
            phase_removed TEXT NOT NULL,
            component_path TEXT,
            function_name TEXT,
            line_number INTEGER,
            root_cause TEXT,
            resolution_notes TEXT,
            flagged_by_agent INTEGER DEFAULT 0,
            metadata TEXT
        )
    """
    )

    conn.commit()
    conn.close()

    yield db_path

    # Cleanup
    db_path.unlink(missing_ok=True)


@pytest.fixture
def mock_langfuse():
    """Create a mocked Langfuse client."""
    with patch("asp.telemetry.telemetry.Langfuse") as mock:
        client = MagicMock()
        mock.return_value = client
        yield client


# =============================================================================
# Database Connection Tests
# =============================================================================


class TestDatabaseConnection:
    """Test database connection management."""

    def test_get_db_connection_success(self, temp_db):
        """Test successful database connection."""
        with get_db_connection(temp_db) as conn:
            assert conn is not None
            assert isinstance(conn, sqlite3.Connection)
            # Test that we can execute queries
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = cursor.fetchall()
            assert len(tables) > 0

    def test_get_db_connection_row_factory(self, temp_db):
        """Test that row_factory is set for column access by name."""
        with get_db_connection(temp_db) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 'test' as col1, 'value' as col2")
            row = cursor.fetchone()
            # Should be able to access by column name
            assert row["col1"] == "test"
            assert row["col2"] == "value"

    def test_get_db_connection_auto_commit(self, temp_db):
        """Test that changes are automatically committed."""
        with get_db_connection(temp_db) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO agent_cost_vector (timestamp, task_id, agent_role, metric_type, metric_value, metric_unit) VALUES (?, ?, ?, ?, ?, ?)",
                (
                    datetime.utcnow().isoformat(),
                    "TEST-001",
                    "TestAgent",
                    "Latency",
                    100.0,
                    "ms",
                ),
            )

        # Verify commit happened by opening new connection
        with get_db_connection(temp_db) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) as count FROM agent_cost_vector")
            count = cursor.fetchone()["count"]
            assert count == 1

    def test_get_db_connection_rollback_on_error(self, temp_db):
        """Test that changes are rolled back on exception."""
        try:
            with get_db_connection(temp_db) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO agent_cost_vector (timestamp, task_id, agent_role, metric_type, metric_value, metric_unit) VALUES (?, ?, ?, ?, ?, ?)",
                    (
                        datetime.utcnow().isoformat(),
                        "TEST-002",
                        "TestAgent",
                        "Latency",
                        200.0,
                        "ms",
                    ),
                )
                # Force an error
                raise ValueError("Test error")
        except ValueError:
            pass

        # Verify rollback happened
        with get_db_connection(temp_db) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) as count FROM agent_cost_vector")
            count = cursor.fetchone()["count"]
            assert count == 0

    def test_get_db_connection_closes_connection(self, temp_db):
        """Test that connection is closed after context manager exits."""
        conn = None
        with get_db_connection(temp_db) as c:
            conn = c
            assert conn is not None

        # Connection should be closed after exiting context
        with pytest.raises(sqlite3.ProgrammingError):
            conn.execute("SELECT 1")


# =============================================================================
# Agent Cost Insertion Tests
# =============================================================================


class TestInsertAgentCost:
    """Test insert_agent_cost function."""

    def test_insert_agent_cost_minimal(self, temp_db):
        """Test inserting agent cost with minimal parameters."""
        record_id = insert_agent_cost(
            task_id="TEST-001",
            agent_role="PlanningAgent",
            metric_type="Latency",
            metric_value=123.45,
            metric_unit="ms",
            db_path=temp_db,
        )

        assert isinstance(record_id, int)
        assert record_id > 0

        # Verify insertion
        with get_db_connection(temp_db) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM agent_cost_vector WHERE id = ?", (record_id,))
            row = cursor.fetchone()
            assert row["task_id"] == "TEST-001"
            assert row["agent_role"] == "PlanningAgent"
            assert row["metric_type"] == "Latency"
            assert row["metric_value"] == 123.45
            assert row["metric_unit"] == "ms"

    def test_insert_agent_cost_all_parameters(self, temp_db):
        """Test inserting agent cost with all parameters."""
        metadata = {"key1": "value1", "key2": 42}

        record_id = insert_agent_cost(
            task_id="TEST-002",
            agent_role="DesignAgent",
            metric_type="Tokens_In",
            metric_value=1500.0,
            metric_unit="tokens",
            subtask_id="SU-001",
            project_id="PROJ-001",
            user_id="user-123",
            agent_version="1.0.0",
            agent_iteration=2,
            llm_model="claude-3-sonnet",
            llm_provider="anthropic",
            metadata=metadata,
            db_path=temp_db,
        )

        # Verify all fields
        with get_db_connection(temp_db) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM agent_cost_vector WHERE id = ?", (record_id,))
            row = cursor.fetchone()
            assert row["task_id"] == "TEST-002"
            assert row["subtask_id"] == "SU-001"
            assert row["project_id"] == "PROJ-001"
            assert row["user_id"] == "user-123"
            assert row["agent_version"] == "1.0.0"
            assert row["agent_iteration"] == 2
            assert row["llm_model"] == "claude-3-sonnet"
            assert row["llm_provider"] == "anthropic"
            assert row["metadata"] is not None

    def test_insert_agent_cost_multiple_records(self, temp_db):
        """Test inserting multiple agent cost records."""
        record_ids = []
        for i in range(5):
            record_id = insert_agent_cost(
                task_id=f"TEST-{i:03d}",
                agent_role="TestAgent",
                metric_type="Latency",
                metric_value=float(i * 100),
                metric_unit="ms",
                db_path=temp_db,
            )
            record_ids.append(record_id)

        # Verify all records
        with get_db_connection(temp_db) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) as count FROM agent_cost_vector")
            count = cursor.fetchone()["count"]
            assert count == 5


# =============================================================================
# Defect Insertion Tests
# =============================================================================


class TestInsertDefect:
    """Test insert_defect function."""

    def test_insert_defect_minimal(self, temp_db):
        """Test inserting defect with minimal parameters."""
        defect_id = insert_defect(
            task_id="TEST-001",
            defect_type="Planning_Failure",
            severity="High",
            phase_injected="Planning",
            phase_removed="Design",
            description="Test defect description",
            db_path=temp_db,
        )

        assert defect_id.startswith("DEFECT-")
        assert len(defect_id) == 19  # "DEFECT-" + 12 hex chars

        # Verify insertion
        with get_db_connection(temp_db) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM defect_log WHERE defect_id = ?", (defect_id,))
            row = cursor.fetchone()
            assert row["task_id"] == "TEST-001"
            assert row["defect_type"] == "Planning_Failure"
            assert row["severity"] == "High"
            assert row["phase_injected"] == "Planning"
            assert row["phase_removed"] == "Design"
            assert row["description"] == "Test defect description"

    def test_insert_defect_all_parameters(self, temp_db):
        """Test inserting defect with all parameters."""
        metadata = {"reviewer": "agent-1", "confidence": 0.95}

        defect_id = insert_defect(
            task_id="TEST-002",
            defect_type="Security_Vulnerability",
            severity="Critical",
            phase_injected="Code",
            phase_removed="CodeReview",
            description="SQL injection vulnerability detected",
            project_id="PROJ-001",
            user_id="user-123",
            component_path="src/auth/login.py",
            function_name="validate_credentials",
            line_number=42,
            root_cause="User input not sanitized",
            resolution_notes="Added parameterized queries",
            flagged_by_agent=True,
            metadata=metadata,
            db_path=temp_db,
        )

        # Verify all fields
        with get_db_connection(temp_db) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM defect_log WHERE defect_id = ?", (defect_id,))
            row = cursor.fetchone()
            assert row["project_id"] == "PROJ-001"
            assert row["user_id"] == "user-123"
            assert row["component_path"] == "src/auth/login.py"
            assert row["function_name"] == "validate_credentials"
            assert row["line_number"] == 42
            assert row["root_cause"] == "User input not sanitized"
            assert row["resolution_notes"] == "Added parameterized queries"
            assert row["flagged_by_agent"] == 1
            assert row["metadata"] is not None

    def test_insert_defect_unique_ids(self, temp_db):
        """Test that defect IDs are unique."""
        defect_ids = set()
        for i in range(10):
            defect_id = insert_defect(
                task_id=f"TEST-{i:03d}",
                defect_type="Tool_Use_Error",
                severity="Low",
                phase_injected="Code",
                phase_removed="Test",
                description=f"Test defect {i}",
                db_path=temp_db,
            )
            defect_ids.add(defect_id)

        # All IDs should be unique
        assert len(defect_ids) == 10


# =============================================================================
# Decorator Tests
# =============================================================================


class TestTrackAgentCostDecorator:
    """Test track_agent_cost decorator."""

    def test_decorator_basic_function(self, temp_db, mock_langfuse):
        """Test decorator on basic function."""

        @track_agent_cost(agent_role="TestAgent", agent_version="1.0.0")
        def test_function(task_id: str, value: int):
            time.sleep(0.01)  # Simulate work
            return value * 2

        # Patch insert_agent_cost to capture calls
        with patch("asp.telemetry.telemetry.insert_agent_cost") as mock_insert:
            result = test_function("TEST-001", 5)

            assert result == 10
            # Verify telemetry was called
            assert mock_insert.called
            call_args = mock_insert.call_args[1]
            assert call_args["task_id"] == "TEST-001"
            assert call_args["agent_role"] == "TestAgent"
            assert call_args["metric_type"] == "Latency"
            assert call_args["metric_value"] > 0

    def test_decorator_with_custom_task_id_param(self, temp_db):
        """Test decorator with custom task_id parameter name."""

        @track_agent_cost(agent_role="TestAgent", task_id_param="custom_task_id")
        def test_function(custom_task_id: str, data: str):
            return data.upper()

        with patch("asp.telemetry.telemetry.insert_agent_cost") as mock_insert:
            result = test_function("CUSTOM-001", "hello")

            assert result == "HELLO"
            call_args = mock_insert.call_args[1]
            assert call_args["task_id"] == "CUSTOM-001"

    def test_decorator_tracks_latency(self, temp_db):
        """Test that decorator accurately tracks execution latency."""

        @track_agent_cost(agent_role="TestAgent")
        def slow_function(task_id: str):
            time.sleep(0.05)  # Sleep for 50ms
            return "done"

        with patch("asp.telemetry.telemetry.insert_agent_cost") as mock_insert:
            slow_function("TEST-001")

            call_args = mock_insert.call_args[1]
            # Latency should be at least 50ms
            assert call_args["metric_value"] >= 40  # Allow some margin
            assert call_args["metric_unit"] == "ms"

    def test_decorator_preserves_function_signature(self):
        """Test that decorator preserves original function metadata."""

        @track_agent_cost(agent_role="TestAgent")
        def documented_function(task_id: str, param1: int, param2: str = "default"):
            """This is a documented function."""
            return f"{param1}:{param2}"

        assert documented_function.__name__ == "documented_function"
        assert documented_function.__doc__ == "This is a documented function."

    def test_decorator_handles_exceptions(self, temp_db):
        """Test that decorator doesn't suppress exceptions."""

        @track_agent_cost(agent_role="TestAgent")
        def failing_function(task_id: str):
            raise ValueError("Test error")

        with patch("asp.telemetry.telemetry.insert_agent_cost"):
            with pytest.raises(ValueError, match="Test error"):
                failing_function("TEST-001")

    def test_decorator_on_class_method(self, temp_db):
        """Test decorator works on class methods."""

        class TestClass:
            @track_agent_cost(agent_role="ClassAgent")
            def method(self, task_id: str, value: int):
                return value + 10

        obj = TestClass()
        with patch("asp.telemetry.telemetry.insert_agent_cost") as mock_insert:
            result = obj.method("TEST-001", 5)

            assert result == 15
            assert mock_insert.called


# =============================================================================
# Langfuse Integration Tests
# =============================================================================


class TestLangfuseIntegration:
    """Test Langfuse integration."""

    def test_get_langfuse_client_singleton(self):
        """Test Langfuse client is a singleton and properly initialized."""
        with patch("asp.telemetry.telemetry.Langfuse") as mock_langfuse:
            mock_client = MagicMock()
            mock_langfuse.return_value = mock_client

            # Reset module-level variable to ensure clean state
            import asp.telemetry.telemetry as telemetry_module

            telemetry_module._langfuse_client = None

            # Get client twice
            client1 = get_langfuse_client()
            client2 = get_langfuse_client()

            # Should return same instance (singleton pattern)
            assert client1 == client2
            assert client1 == mock_client
            # Langfuse constructor should only be called once
            mock_langfuse.assert_called_once()


# =============================================================================
# User ID Resolution Tests
# =============================================================================


class TestUserIdResolution:
    """Test get_user_id resolution logic."""

    def test_get_user_id_env_var(self):
        """Test resolution from environment variable."""
        with patch.dict(os.environ, {"ASP_USER_ID": "env-user"}):
            assert get_user_id() == "env-user"

    def test_get_user_id_git_config(self):
        """Test resolution from git config."""
        with patch.dict(os.environ, {}, clear=True):  # Ensure no env var
            with patch("subprocess.run") as mock_run:
                mock_run.return_value.returncode = 0
                mock_run.return_value.stdout = "git-user@example.com"

                assert get_user_id() == "git-user@example.com"

    def test_get_user_id_system(self):
        """Test resolution from system login."""
        with patch.dict(os.environ, {}, clear=True):
            with patch("subprocess.run") as mock_run:
                mock_run.side_effect = Exception("No git")
                with patch("os.getlogin", return_value="system-user"):
                    assert get_user_id() == "system-user"

    def test_get_user_id_fallback(self):
        """Test fallback to unknown-user."""
        with patch.dict(os.environ, {}, clear=True):
            with patch("subprocess.run", side_effect=Exception("No git")):
                with patch("os.getlogin", side_effect=Exception("No system user")):
                    assert get_user_id() == "unknown-user"


# =============================================================================
# Error Handling and Edge Cases
# =============================================================================


class TestErrorHandling:
    """Test error handling and edge cases."""

    def test_insert_agent_cost_with_missing_database(self):
        """Test insert_agent_cost fails gracefully with missing database."""
        nonexistent_db = Path("/nonexistent/path/db.sqlite")

        with pytest.raises(Exception):  # sqlite3.OperationalError or similar
            insert_agent_cost(
                task_id="TEST-001",
                agent_role="TestAgent",
                metric_type="Latency",
                metric_value=100.0,
                metric_unit="ms",
                db_path=nonexistent_db,
            )

    def test_insert_defect_with_very_long_description(self, temp_db):
        """Test inserting defect with very long description."""
        long_description = "X" * 10000  # Very long description

        defect_id = insert_defect(
            task_id="TEST-001",
            defect_type="Hallucination",
            severity="Medium",
            phase_injected="Code",
            phase_removed="Review",
            description=long_description,
            db_path=temp_db,
        )

        # Should succeed
        assert defect_id.startswith("DEFECT-")

    def test_decorator_with_none_values(self, temp_db):
        """Test decorator handles None values gracefully."""

        @track_agent_cost(agent_role="TestAgent", llm_model=None, llm_provider=None)
        def test_function(task_id: str):
            return "result"

        with patch("asp.telemetry.telemetry.insert_agent_cost") as mock_insert:
            result = test_function("TEST-001")
            assert result == "result"
            assert mock_insert.called
