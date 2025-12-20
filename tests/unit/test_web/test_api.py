"""
Unit tests for web API layer.

Tests data access functions that connect to telemetry database.
"""

import json
import sqlite3
import subprocess
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

import pytest


@pytest.fixture
def isolated_api_layer(tmp_path, monkeypatch):
    """Isolate tests from production data."""
    import asp.web.api as api_module

    monkeypatch.setattr(api_module, "DEFAULT_DB_PATH", tmp_path / "telemetry.db")
    monkeypatch.setattr(api_module, "DEFAULT_ARTIFACTS_PATH", tmp_path / "artifacts")
    return tmp_path


@pytest.fixture
def db_with_schema(isolated_api_layer):
    """Create a database with the required schema."""
    tmp_path = isolated_api_layer
    db_path = tmp_path / "telemetry.db"

    conn = sqlite3.connect(str(db_path))
    conn.execute(
        """
        CREATE TABLE agent_cost_vector (
            timestamp TEXT,
            task_id TEXT,
            agent_role TEXT,
            metric_type TEXT,
            metric_value REAL,
            metric_unit TEXT,
            user_id TEXT,
            llm_model TEXT
        )
    """
    )
    conn.execute(
        """
        CREATE TABLE defect_log (
            id INTEGER PRIMARY KEY,
            task_id TEXT,
            severity TEXT,
            defect_type TEXT,
            description TEXT
        )
    """
    )
    conn.commit()
    conn.close()

    return tmp_path


@pytest.fixture
def populated_db(db_with_schema):
    """Create a database with sample data."""
    tmp_path = db_with_schema
    db_path = tmp_path / "telemetry.db"

    conn = sqlite3.connect(str(db_path))
    now = datetime.now(timezone.utc)

    # Insert agent cost vector data
    test_data = [
        (
            now.isoformat(),
            "TASK-001",
            "design",
            "Latency",
            1500.0,
            "ms",
            "user1",
            "claude-3",
        ),
        (
            now.isoformat(),
            "TASK-001",
            "design",
            "API_Cost",
            0.05,
            "USD",
            "user1",
            "claude-3",
        ),
        (
            now.isoformat(),
            "TASK-001",
            "design",
            "Tokens_In",
            5000.0,
            "tokens",
            "user1",
            "claude-3",
        ),
        (
            now.isoformat(),
            "TASK-001",
            "design",
            "Tokens_Out",
            2000.0,
            "tokens",
            "user1",
            "claude-3",
        ),
        (
            (now - timedelta(hours=1)).isoformat(),
            "TASK-002",
            "code",
            "Latency",
            2500.0,
            "ms",
            "user2",
            "claude-3",
        ),
        (
            (now - timedelta(hours=1)).isoformat(),
            "TASK-002",
            "code",
            "API_Cost",
            0.08,
            "USD",
            "user2",
            "claude-3",
        ),
        (
            (now - timedelta(hours=1)).isoformat(),
            "TASK-002",
            "code",
            "Tokens_In",
            8000.0,
            "tokens",
            "user2",
            "claude-3",
        ),
        (
            (now - timedelta(hours=1)).isoformat(),
            "TASK-002",
            "code",
            "Tokens_Out",
            3000.0,
            "tokens",
            "user2",
            "claude-3",
        ),
    ]

    conn.executemany(
        """
        INSERT INTO agent_cost_vector
        (timestamp, task_id, agent_role, metric_type, metric_value, metric_unit, user_id, llm_model)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """,
        test_data,
    )

    # Insert defect data
    defect_data = [
        ("TASK-001", "high", "security", "SQL injection vulnerability"),
        ("TASK-001", "medium", "performance", "Slow query execution"),
        ("TASK-002", "low", "style", "Missing docstring"),
        ("TASK-002", "high", "security", "Hardcoded credentials"),
        ("TASK-003", "medium", "logic", "Off-by-one error"),
    ]

    conn.executemany(
        """
        INSERT INTO defect_log (task_id, severity, defect_type, description)
        VALUES (?, ?, ?, ?)
    """,
        defect_data,
    )

    conn.commit()
    conn.close()

    return tmp_path


@pytest.fixture
def artifacts_with_pips(isolated_api_layer):
    """Create artifacts directory with test PIPs."""
    tmp_path = isolated_api_layer
    artifacts_dir = tmp_path / "artifacts"
    artifacts_dir.mkdir()

    # Create task with pending PIP
    task1_dir = artifacts_dir / "TASK-001"
    task1_dir.mkdir()
    pip1 = {
        "proposal_id": "PIP-001",
        "hitl_status": "pending",
        "analysis": "Improve error handling in authentication module",
        "created_at": "2025-12-05T10:00:00",
        "expected_impact": "Reduce authentication failures by 50%",
    }
    (task1_dir / "pip.json").write_text(json.dumps(pip1))

    # Create task with approved PIP
    task2_dir = artifacts_dir / "TASK-002"
    task2_dir.mkdir()
    pip2 = {
        "proposal_id": "PIP-002",
        "hitl_status": "approved",
        "analysis": "Add caching layer for API responses",
    }
    (task2_dir / "pip.json").write_text(json.dumps(pip2))

    # Create task without PIP
    task3_dir = artifacts_dir / "TASK-003"
    task3_dir.mkdir()

    return tmp_path


class TestGetDbConnection:
    """Test the get_db_connection function."""

    def test_returns_none_when_db_not_exists(self, isolated_api_layer):
        """Test returns None when database doesn't exist."""
        from asp.web.api import get_db_connection

        conn = get_db_connection()
        assert conn is None

    def test_returns_connection_when_db_exists(self, isolated_api_layer):
        """Test returns connection when database exists."""
        tmp_path = isolated_api_layer
        db_path = tmp_path / "telemetry.db"

        # Create a test database
        conn = sqlite3.connect(str(db_path))
        conn.execute("CREATE TABLE test (id INTEGER)")
        conn.close()

        from asp.web.api import get_db_connection

        conn = get_db_connection()
        assert conn is not None
        conn.close()

    def test_connection_has_row_factory(self, db_with_schema):
        """Test that connection uses Row factory."""
        from asp.web.api import get_db_connection

        conn = get_db_connection()
        assert conn is not None
        assert conn.row_factory == sqlite3.Row
        conn.close()


class TestGetRecentAgentActivity:
    """Test the get_recent_agent_activity function."""

    def test_returns_empty_when_no_db(self, isolated_api_layer):
        """Test returns empty list when no database."""
        from asp.web.api import get_recent_agent_activity

        results = get_recent_agent_activity()
        assert results == []

    def test_returns_activity_data(self, populated_db):
        """Test returns activity data from database."""
        from asp.web.api import get_recent_agent_activity

        results = get_recent_agent_activity(limit=10)

        assert len(results) == 2  # Two Latency records
        assert results[0]["task_id"] in ("TASK-001", "TASK-002")
        assert "latency_ms" in results[0]
        assert "agent_role" in results[0]
        assert "user_id" in results[0]

    def test_respects_limit(self, populated_db):
        """Test respects the limit parameter."""
        from asp.web.api import get_recent_agent_activity

        results = get_recent_agent_activity(limit=1)
        assert len(results) == 1

    def test_orders_by_timestamp_desc(self, populated_db):
        """Test results are ordered by timestamp descending."""
        from asp.web.api import get_recent_agent_activity

        results = get_recent_agent_activity(limit=10)

        # First result should be more recent (TASK-001)
        assert results[0]["task_id"] == "TASK-001"

    def test_handles_db_error(self, db_with_schema):
        """Test handles database errors gracefully."""
        tmp_path = db_with_schema
        db_path = tmp_path / "telemetry.db"

        # Drop the table to cause an error
        conn = sqlite3.connect(str(db_path))
        conn.execute("DROP TABLE agent_cost_vector")
        conn.commit()
        conn.close()

        from asp.web.api import get_recent_agent_activity

        results = get_recent_agent_activity()
        assert results == []


class TestGetDefectSummary:
    """Test the get_defect_summary function."""

    def test_returns_default_when_no_db(self, isolated_api_layer):
        """Test returns default summary when no database."""
        from asp.web.api import get_defect_summary

        summary = get_defect_summary()

        assert summary["total"] == 0
        assert summary["by_severity"] == {}
        assert summary["by_type"] == {}

    def test_returns_defect_counts(self, populated_db):
        """Test returns correct defect counts."""
        from asp.web.api import get_defect_summary

        summary = get_defect_summary()

        assert summary["total"] == 5
        assert "high" in summary["by_severity"]
        assert summary["by_severity"]["high"] == 2
        assert "security" in summary["by_type"]
        assert summary["by_type"]["security"] == 2

    def test_severity_breakdown(self, populated_db):
        """Test severity breakdown is correct."""
        from asp.web.api import get_defect_summary

        summary = get_defect_summary()

        assert summary["by_severity"]["high"] == 2
        assert summary["by_severity"]["medium"] == 2
        assert summary["by_severity"]["low"] == 1

    def test_type_breakdown_limited_to_top_5(self, populated_db):
        """Test type breakdown is limited to top 5."""
        from asp.web.api import get_defect_summary

        summary = get_defect_summary()

        # Should have at most 5 types
        assert len(summary["by_type"]) <= 5

    def test_handles_db_error(self, db_with_schema):
        """Test handles database errors gracefully."""
        tmp_path = db_with_schema
        db_path = tmp_path / "telemetry.db"

        # Drop the table to cause an error
        conn = sqlite3.connect(str(db_path))
        conn.execute("DROP TABLE defect_log")
        conn.commit()
        conn.close()

        from asp.web.api import get_defect_summary

        summary = get_defect_summary()
        assert summary == {"total": 0, "by_severity": {}, "by_type": {}}


class TestGetCostSummary:
    """Test the get_cost_summary function."""

    def test_returns_default_when_no_db(self, isolated_api_layer):
        """Test returns default summary when no database."""
        from asp.web.api import get_cost_summary

        summary = get_cost_summary()

        assert summary["total_usd"] == 0
        assert summary["by_role"] == {}
        assert summary["token_usage"] == {}

    def test_returns_cost_data(self, populated_db):
        """Test returns correct cost data."""
        from asp.web.api import get_cost_summary

        summary = get_cost_summary(days=7)

        assert summary["total_usd"] == 0.13  # 0.05 + 0.08
        assert "design" in summary["by_role"]
        assert "code" in summary["by_role"]

    def test_token_usage_calculation(self, populated_db):
        """Test token usage is calculated correctly."""
        from asp.web.api import get_cost_summary

        summary = get_cost_summary(days=7)

        assert summary["token_usage"]["input"] == 13000  # 5000 + 8000
        assert summary["token_usage"]["output"] == 5000  # 2000 + 3000

    def test_cost_by_role_breakdown(self, populated_db):
        """Test cost breakdown by role."""
        from asp.web.api import get_cost_summary

        summary = get_cost_summary(days=7)

        assert summary["by_role"]["design"] == 0.05
        assert summary["by_role"]["code"] == 0.08

    def test_handles_db_error(self, db_with_schema):
        """Test handles database errors gracefully."""
        tmp_path = db_with_schema
        db_path = tmp_path / "telemetry.db"

        conn = sqlite3.connect(str(db_path))
        conn.execute("DROP TABLE agent_cost_vector")
        conn.commit()
        conn.close()

        from asp.web.api import get_cost_summary

        summary = get_cost_summary()
        assert summary == {"total_usd": 0, "by_role": {}, "token_usage": {}}


class TestGetUserPerformance:
    """Test the get_user_performance function."""

    def test_returns_empty_when_no_db(self, isolated_api_layer):
        """Test returns empty list when no database."""
        from asp.web.api import get_user_performance

        perf = get_user_performance()
        assert perf == []

    def test_returns_user_metrics(self, populated_db):
        """Test returns user performance metrics."""
        from asp.web.api import get_user_performance

        perf = get_user_performance()

        assert len(perf) == 2  # Two users
        user_ids = [r["user_id"] for r in perf]
        assert "user1" in user_ids
        assert "user2" in user_ids

    def test_filters_by_user_id(self, populated_db):
        """Test filters by specific user ID."""
        from asp.web.api import get_user_performance

        perf = get_user_performance(user_id="user1")

        assert len(perf) == 1
        assert perf[0]["user_id"] == "user1"

    def test_calculates_avg_latency(self, populated_db):
        """Test calculates average latency correctly."""
        from asp.web.api import get_user_performance

        perf = get_user_performance()

        for p in perf:
            assert "avg_latency_ms" in p
            assert p["avg_latency_ms"] >= 0

    def test_includes_task_count(self, populated_db):
        """Test includes task count per user."""
        from asp.web.api import get_user_performance

        perf = get_user_performance()

        for p in perf:
            assert "task_count" in p
            assert p["task_count"] >= 1

    def test_includes_execution_count(self, populated_db):
        """Test includes execution count per user."""
        from asp.web.api import get_user_performance

        perf = get_user_performance()

        for p in perf:
            assert "execution_count" in p
            assert p["execution_count"] >= 1

    def test_handles_db_error(self, db_with_schema):
        """Test handles database errors gracefully."""
        tmp_path = db_with_schema
        db_path = tmp_path / "telemetry.db"

        conn = sqlite3.connect(str(db_path))
        conn.execute("DROP TABLE agent_cost_vector")
        conn.commit()
        conn.close()

        from asp.web.api import get_user_performance

        perf = get_user_performance()
        assert perf == []


class TestGetTasksPendingApproval:
    """Test the get_tasks_pending_approval function."""

    def test_returns_list_when_no_artifacts(self, isolated_api_layer):
        """Test returns list structure when no artifacts."""
        from asp.web.api import get_tasks_pending_approval

        tasks = get_tasks_pending_approval()

        # Function returns a list, not a dict
        assert isinstance(tasks, list)

    def test_returns_pending_pips(self, artifacts_with_pips):
        """Test returns pending PIPs from artifacts."""
        import asp.web.api as api_module

        with patch.object(api_module, "_get_pending_review_branches", return_value=[]):
            from asp.web.api import get_tasks_pending_approval

            tasks = get_tasks_pending_approval()

            assert len(tasks) == 1
            assert tasks[0]["task_id"] == "TASK-001"
            assert tasks[0]["type"] == "pip"

    def test_excludes_approved_pips(self, artifacts_with_pips):
        """Test excludes approved PIPs."""
        import asp.web.api as api_module

        with patch.object(api_module, "_get_pending_review_branches", return_value=[]):
            from asp.web.api import get_tasks_pending_approval

            tasks = get_tasks_pending_approval()

            task_ids = [t["task_id"] for t in tasks]
            assert "TASK-002" not in task_ids

    def test_includes_review_branches(self, artifacts_with_pips):
        """Test includes pending review branches."""
        import asp.web.api as api_module

        mock_branches = [
            {
                "task_id": "TASK-005",
                "title": "Quality Gate: Design Review",
                "status": "pending_approval",
                "type": "quality_gate",
            }
        ]

        with patch.object(
            api_module, "_get_pending_review_branches", return_value=mock_branches
        ):
            from asp.web.api import get_tasks_pending_approval

            tasks = get_tasks_pending_approval()

            assert len(tasks) == 2  # 1 PIP + 1 branch
            types = [t["type"] for t in tasks]
            assert "pip" in types
            assert "quality_gate" in types


class TestGetPendingPips:
    """Test _get_pending_pips helper function."""

    def test_finds_pending_pips(self, artifacts_with_pips):
        """Test finds PIPs with pending status."""
        from asp.web.api import _get_pending_pips

        tmp_path = artifacts_with_pips
        artifacts_dir = tmp_path / "artifacts"

        pips = _get_pending_pips(artifacts_dir)

        assert len(pips) == 1
        assert pips[0]["task_id"] == "TASK-001"
        assert pips[0]["proposal_id"] == "PIP-001"

    def test_truncates_long_analysis(self, isolated_api_layer):
        """Test truncates long analysis text."""
        tmp_path = isolated_api_layer
        artifacts_dir = tmp_path / "artifacts"
        artifacts_dir.mkdir()

        task_dir = artifacts_dir / "TASK-LONG"
        task_dir.mkdir()
        pip = {
            "proposal_id": "PIP-LONG",
            "hitl_status": "pending",
            "analysis": "A" * 200,
        }
        (task_dir / "pip.json").write_text(json.dumps(pip))

        from asp.web.api import _get_pending_pips

        pips = _get_pending_pips(artifacts_dir)

        long_pip = pips[0]
        assert len(long_pip["title"]) <= 105  # "PIP: " + truncated

    def test_handles_invalid_json(self, isolated_api_layer):
        """Test handles invalid JSON gracefully."""
        tmp_path = isolated_api_layer
        artifacts_dir = tmp_path / "artifacts"
        artifacts_dir.mkdir()

        task_dir = artifacts_dir / "TASK-BAD"
        task_dir.mkdir()
        (task_dir / "pip.json").write_text("not valid json")

        from asp.web.api import _get_pending_pips

        pips = _get_pending_pips(artifacts_dir)

        task_ids = [p["task_id"] for p in pips]
        assert "TASK-BAD" not in task_ids

    def test_skips_non_directories(self, isolated_api_layer):
        """Test skips files in artifacts directory."""
        tmp_path = isolated_api_layer
        artifacts_dir = tmp_path / "artifacts"
        artifacts_dir.mkdir()

        # Create a file instead of directory
        (artifacts_dir / "not_a_dir.txt").write_text("test")

        from asp.web.api import _get_pending_pips

        pips = _get_pending_pips(artifacts_dir)
        assert pips == []


class TestGetPendingReviewBranches:
    """Test _get_pending_review_branches helper function."""

    def test_returns_review_branches(self):
        """Test returns branches matching review/* pattern."""
        import asp.web.api as api_module

        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = (
            "  review/TASK-001-design_review\n* review/TASK-002-code_review\n"
        )

        with patch.object(subprocess, "run", return_value=mock_result):
            result = api_module._get_pending_review_branches()

            assert len(result) == 2
            assert result[0]["task_id"] == "TASK-001"
            assert result[0]["gate_type"] == "design_review"

    def test_handles_remote_branches(self):
        """Test handles remote branch prefixes."""
        import asp.web.api as api_module

        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "  remotes/origin/review/TASK-001-design_review\n"

        with patch.object(subprocess, "run", return_value=mock_result):
            result = api_module._get_pending_review_branches()

            assert len(result) == 1
            assert result[0]["branch"] == "review/TASK-001-design_review"

    def test_deduplicates_branches(self):
        """Test deduplicates local and remote branches."""
        import asp.web.api as api_module

        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = (
            "  review/TASK-001-design_review\n"
            "  remotes/origin/review/TASK-001-design_review\n"
        )

        with patch.object(subprocess, "run", return_value=mock_result):
            result = api_module._get_pending_review_branches()

            assert len(result) == 1

    def test_handles_git_error(self):
        """Test handles git command errors."""
        import asp.web.api as api_module

        mock_result = MagicMock()
        mock_result.returncode = 1

        with patch.object(subprocess, "run", return_value=mock_result):
            result = api_module._get_pending_review_branches()
            assert result == []

    def test_handles_timeout(self):
        """Test handles subprocess timeout."""
        import asp.web.api as api_module

        with patch.object(
            subprocess, "run", side_effect=subprocess.TimeoutExpired("git", 5)
        ):
            result = api_module._get_pending_review_branches()
            assert result == []

    def test_handles_branch_without_gate_type(self):
        """Test handles branch names that split differently.

        Note: The code uses rsplit("-", 1) which splits from right.
        For 'review/TASK-001', this gives ['TASK', '001'], so the
        "gate_type" becomes '001'. This is the actual behavior.
        """
        import asp.web.api as api_module

        mock_result = MagicMock()
        mock_result.returncode = 0
        # Use a branch with only one hyphen after review/
        mock_result.stdout = "  review/SIMPLE\n"

        with patch.object(subprocess, "run", return_value=mock_result):
            result = api_module._get_pending_review_branches()

            assert len(result) == 1
            # Single part gets task_id, gate_type becomes "unknown"
            assert result[0]["task_id"] == "SIMPLE"
            assert result[0]["gate_type"] == "unknown"

    def test_handles_empty_lines(self):
        """Test handles empty lines in output."""
        import asp.web.api as api_module

        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "\n  review/TASK-001-test\n\n"

        with patch.object(subprocess, "run", return_value=mock_result):
            result = api_module._get_pending_review_branches()

            assert len(result) == 1


class TestGetPipDetails:
    """Test PIP details function."""

    def test_get_pip_details_returns_none_for_nonexistent(self, isolated_api_layer):
        """Test returns None for non-existent PIP."""
        from asp.web.api import get_pip_details

        details = get_pip_details("NONEXISTENT")
        assert details is None

    def test_get_pip_details_from_file(self, isolated_api_layer):
        """Test retrieves PIP details from pip.json file."""
        tmp_path = isolated_api_layer
        artifacts_dir = tmp_path / "artifacts"
        artifacts_dir.mkdir()

        pip_dir = artifacts_dir / "TEST-001"
        pip_dir.mkdir()
        pip_json = pip_dir / "pip.json"
        pip_json.write_text(
            json.dumps(
                {
                    "status": "pending",
                    "title": "Test PIP",
                    "description": "A test PIP",
                    "changes": [{"file": "main.py", "type": "add"}],
                }
            )
        )

        from asp.web.api import get_pip_details

        details = get_pip_details("TEST-001")

        assert details is not None
        assert details["title"] == "Test PIP"
        assert details["status"] == "pending"

    def test_returns_none_for_task_without_pip(self, artifacts_with_pips):
        """Test returns None for task without pip.json."""
        from asp.web.api import get_pip_details

        details = get_pip_details("TASK-003")
        assert details is None

    def test_handles_invalid_json(self, isolated_api_layer):
        """Test handles invalid JSON gracefully."""
        tmp_path = isolated_api_layer
        artifacts_dir = tmp_path / "artifacts"
        artifacts_dir.mkdir()

        pip_dir = artifacts_dir / "TASK-BAD"
        pip_dir.mkdir()
        (pip_dir / "pip.json").write_text("not valid json")

        from asp.web.api import get_pip_details

        details = get_pip_details("TASK-BAD")
        assert details is None


class TestGetProjectProgress:
    """Test project progress function."""

    def test_returns_progress_when_no_db(self, isolated_api_layer):
        """Test returns progress structure even without database."""
        from asp.web.api import get_project_progress

        progress = get_project_progress()

        assert "total" in progress
        assert "completed" in progress
        assert "in_progress" in progress

    def test_returns_task_counts(self, populated_db):
        """Test returns correct task counts."""
        from asp.web.api import get_project_progress

        progress = get_project_progress()

        assert progress["completed"] == 2  # Two distinct tasks
        assert progress["total"] >= progress["completed"]

    def test_handles_db_error(self, db_with_schema):
        """Test handles database errors gracefully."""
        tmp_path = db_with_schema
        db_path = tmp_path / "telemetry.db"

        conn = sqlite3.connect(str(db_path))
        conn.execute("DROP TABLE agent_cost_vector")
        conn.commit()
        conn.close()

        from asp.web.api import get_project_progress

        progress = get_project_progress()
        assert progress == {"completed": 0, "in_progress": 0, "total": 0}
