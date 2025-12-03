"""
Unit tests for web API layer.

Tests data access functions that connect to telemetry database.
"""

import pytest


@pytest.fixture
def isolated_api_layer(tmp_path, monkeypatch):
    """Isolate tests from production data."""
    import asp.web.api as api_module

    monkeypatch.setattr(api_module, "DEFAULT_DB_PATH", tmp_path / "telemetry.db")
    monkeypatch.setattr(api_module, "DEFAULT_ARTIFACTS_PATH", tmp_path / "artifacts")
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
        import sqlite3

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


class TestGetRecentAgentActivity:
    """Test the get_recent_agent_activity function."""

    def test_returns_empty_when_no_db(self, isolated_api_layer):
        """Test returns empty list when no database."""
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


class TestGetCostSummary:
    """Test the get_cost_summary function."""

    def test_returns_default_when_no_db(self, isolated_api_layer):
        """Test returns default summary when no database."""
        from asp.web.api import get_cost_summary

        summary = get_cost_summary()

        assert summary["total_usd"] == 0
        assert summary["by_role"] == {}
        assert summary["token_usage"] == {}


class TestGetUserPerformance:
    """Test the get_user_performance function."""

    def test_returns_empty_when_no_db(self, isolated_api_layer):
        """Test returns empty list when no database."""
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


class TestGetPipDetails:
    """Test PIP details function."""

    def test_get_pip_details_returns_none_for_nonexistent(self, isolated_api_layer):
        """Test returns None for non-existent PIP."""
        from asp.web.api import get_pip_details

        details = get_pip_details("NONEXISTENT")
        assert details is None

    def test_get_pip_details_from_file(self, isolated_api_layer):
        """Test retrieves PIP details from pip.json file."""
        import json

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


class TestGetProjectProgress:
    """Test project progress function."""

    def test_returns_progress_when_no_db(self, isolated_api_layer):
        """Test returns progress structure even without database."""
        from asp.web.api import get_project_progress

        progress = get_project_progress()

        assert "total" in progress
        assert "completed" in progress
        assert "in_progress" in progress
