"""
Unit tests for web data access layer.

Tests the data access functions that fetch tasks, telemetry, and artifacts
for display in the web interface.
"""

import json


class TestGetTasks:
    """Test the get_tasks function."""

    def test_returns_empty_list_when_no_data(self, tmp_path, monkeypatch):
        """Test returns empty list when no bootstrap results or artifacts."""
        import asp.web.data as data_module

        # Monkey-patch the module paths
        monkeypatch.setattr(data_module, "DATA_DIR", tmp_path / "data")
        monkeypatch.setattr(data_module, "ARTIFACTS_DIR", tmp_path / "artifacts")
        monkeypatch.setattr(
            data_module,
            "BOOTSTRAP_RESULTS",
            tmp_path / "data" / "bootstrap_results.json",
        )

        from asp.web.data import get_tasks

        tasks = get_tasks()
        assert tasks == []

    def test_loads_tasks_from_bootstrap_results(self, tmp_path, monkeypatch):
        """Test loading tasks from bootstrap results."""
        import asp.web.data as data_module

        # Create test data
        data_dir = tmp_path / "data"
        data_dir.mkdir()
        bootstrap_file = data_dir / "bootstrap_results.json"
        bootstrap_file.write_text(
            json.dumps(
                {
                    "results": [
                        {
                            "task_id": "TASK-001",
                            "description": "Test task one",
                            "actual_total_complexity": 15,
                            "num_units": 3,
                            "execution_time_seconds": 5.2,
                            "success": True,
                        },
                        {
                            "task_id": "TASK-002",
                            "description": "Test task two",
                            "actual_total_complexity": 8,
                            "num_units": 2,
                            "execution_time_seconds": 3.1,
                            "success": False,
                        },
                    ]
                }
            )
        )

        # Monkey-patch the module paths
        monkeypatch.setattr(data_module, "DATA_DIR", data_dir)
        monkeypatch.setattr(data_module, "ARTIFACTS_DIR", tmp_path / "artifacts")
        monkeypatch.setattr(data_module, "BOOTSTRAP_RESULTS", bootstrap_file)

        from asp.web.data import get_tasks

        tasks = get_tasks()

        assert len(tasks) == 2
        assert tasks[0]["task_id"] == "TASK-001"
        assert tasks[0]["status"] == "completed"
        assert tasks[0]["complexity"] == 15
        assert tasks[1]["task_id"] == "TASK-002"
        assert tasks[1]["status"] == "failed"

    def test_loads_tasks_from_artifacts_directory(self, tmp_path, monkeypatch):
        """Test loading tasks from artifacts directory."""
        import asp.web.data as data_module

        # Create artifacts directory with some task folders
        artifacts_dir = tmp_path / "artifacts"
        artifacts_dir.mkdir()

        # Task with plan only
        task1 = artifacts_dir / "TASK-001"
        task1.mkdir()
        (task1 / "plan.md").write_text("# Plan")

        # Task with design
        task2 = artifacts_dir / "TASK-002"
        task2.mkdir()
        (task2 / "plan.md").write_text("# Plan")
        (task2 / "design.md").write_text("# Design")

        # Task with code (completed)
        task3 = artifacts_dir / "TASK-003"
        task3.mkdir()
        (task3 / "main.py").write_text("print('hello')")

        # Monkey-patch the module paths
        monkeypatch.setattr(data_module, "DATA_DIR", tmp_path / "data")
        monkeypatch.setattr(data_module, "ARTIFACTS_DIR", artifacts_dir)
        monkeypatch.setattr(
            data_module,
            "BOOTSTRAP_RESULTS",
            tmp_path / "data" / "bootstrap_results.json",
        )

        from asp.web.data import get_tasks

        tasks = get_tasks()

        assert len(tasks) == 3
        # Should be sorted by task_id
        assert tasks[0]["task_id"] == "TASK-001"
        assert tasks[0]["status"] == "planning"
        assert tasks[1]["task_id"] == "TASK-002"
        assert tasks[1]["status"] == "in_progress"
        assert tasks[2]["task_id"] == "TASK-003"
        assert tasks[2]["status"] == "completed"


class TestGetTaskDetails:
    """Test the get_task_details function."""

    def test_returns_none_for_nonexistent_task(self, tmp_path, monkeypatch):
        """Test returns None when task doesn't exist."""
        import asp.web.data as data_module

        artifacts_dir = tmp_path / "artifacts"
        artifacts_dir.mkdir()
        monkeypatch.setattr(data_module, "ARTIFACTS_DIR", artifacts_dir)

        from asp.web.data import get_task_details

        details = get_task_details("NONEXISTENT")
        assert details is None

    def test_returns_task_details_with_artifacts(self, tmp_path, monkeypatch):
        """Test returns task details with artifact list."""
        import asp.web.data as data_module

        artifacts_dir = tmp_path / "artifacts"
        artifacts_dir.mkdir()

        # Create task with artifacts
        task_dir = artifacts_dir / "TASK-001"
        task_dir.mkdir()
        (task_dir / "plan.md").write_text("# Project Plan\n\nThis is the plan.")
        (task_dir / "design.md").write_text("# Design Spec\n\nThis is the design.")
        (task_dir / "plan.json").write_text('{"task_id": "TASK-001"}')

        monkeypatch.setattr(data_module, "ARTIFACTS_DIR", artifacts_dir)

        from asp.web.data import get_task_details

        details = get_task_details("TASK-001")

        assert details is not None
        assert details["task_id"] == "TASK-001"
        assert len(details["artifacts"]) == 3
        assert details["plan"] is not None
        assert "Project Plan" in details["plan"]
        assert details["design"] is not None
        assert "Design Spec" in details["design"]


class TestGetRecentActivity:
    """Test the get_recent_activity function."""

    def test_returns_empty_when_no_artifacts(self, tmp_path, monkeypatch):
        """Test returns empty list when no artifacts exist."""
        import asp.web.data as data_module

        monkeypatch.setattr(data_module, "ARTIFACTS_DIR", tmp_path / "nonexistent")
        monkeypatch.setattr(data_module, "TELEMETRY_DB", tmp_path / "nonexistent.db")

        from asp.web.data import get_recent_activity

        activities = get_recent_activity()
        assert activities == []

    def test_returns_recent_activities(self, tmp_path, monkeypatch):
        """Test returns list of recent activities sorted by time."""
        import time

        import asp.web.data as data_module

        artifacts_dir = tmp_path / "artifacts"
        artifacts_dir.mkdir()

        # Create task with artifacts
        task_dir = artifacts_dir / "TASK-001"
        task_dir.mkdir()
        (task_dir / "plan.md").write_text("# Plan")
        time.sleep(0.01)  # Small delay to ensure different mtime
        (task_dir / "design.md").write_text("# Design")

        monkeypatch.setattr(data_module, "ARTIFACTS_DIR", artifacts_dir)
        monkeypatch.setattr(data_module, "TELEMETRY_DB", tmp_path / "nonexistent.db")

        from asp.web.data import get_recent_activity

        activities = get_recent_activity(limit=10)

        assert len(activities) >= 2
        # Most recent should be first
        assert "design.md" in activities[0]["action"]

    def test_respects_limit_parameter(self, tmp_path, monkeypatch):
        """Test that limit parameter limits results."""
        import asp.web.data as data_module

        artifacts_dir = tmp_path / "artifacts"
        artifacts_dir.mkdir()

        # Create task with many artifacts
        task_dir = artifacts_dir / "TASK-001"
        task_dir.mkdir()
        for i in range(10):
            (task_dir / f"file_{i}.txt").write_text(f"Content {i}")

        monkeypatch.setattr(data_module, "ARTIFACTS_DIR", artifacts_dir)
        monkeypatch.setattr(data_module, "TELEMETRY_DB", tmp_path / "nonexistent.db")

        from asp.web.data import get_recent_activity

        activities = get_recent_activity(limit=3)
        assert len(activities) == 3


class TestGetAgentStats:
    """Test the get_agent_stats function."""

    def test_returns_default_stats_when_no_data(self, tmp_path, monkeypatch):
        """Test returns default stats when no bootstrap results."""
        import asp.web.data as data_module

        monkeypatch.setattr(
            data_module, "BOOTSTRAP_RESULTS", tmp_path / "nonexistent.json"
        )

        from asp.web.data import get_agent_stats

        stats = get_agent_stats()

        assert stats["total_tasks"] == 0
        assert stats["successful"] == 0
        assert stats["failed"] == 0

    def test_returns_stats_from_bootstrap(self, tmp_path, monkeypatch):
        """Test returns computed stats from bootstrap results."""
        import asp.web.data as data_module

        bootstrap_file = tmp_path / "bootstrap_results.json"
        bootstrap_file.write_text(
            json.dumps(
                {
                    "total_tasks": 5,
                    "successful": 4,
                    "failed": 1,
                    "results": [
                        {
                            "actual_total_complexity": 10,
                            "execution_time_seconds": 2.0,
                            "num_units": 2,
                        },
                        {
                            "actual_total_complexity": 20,
                            "execution_time_seconds": 4.0,
                            "num_units": 4,
                        },
                    ],
                }
            )
        )

        monkeypatch.setattr(data_module, "BOOTSTRAP_RESULTS", bootstrap_file)

        from asp.web.data import get_agent_stats

        stats = get_agent_stats()

        assert stats["total_tasks"] == 5
        assert stats["successful"] == 4
        assert stats["failed"] == 1
        assert stats["avg_complexity"] == 15.0  # (10+20)/2
        assert stats["avg_execution_time"] == 3.0  # (2+4)/2
        assert stats["total_units"] == 6  # 2+4


class TestGetDesignReviewStats:
    """Test the get_design_review_stats function."""

    def test_returns_default_stats_when_no_data(self, tmp_path, monkeypatch):
        """Test returns default stats when no design review results."""
        import asp.web.data as data_module

        monkeypatch.setattr(
            data_module, "BOOTSTRAP_DESIGN_RESULTS", tmp_path / "nonexistent.json"
        )

        from asp.web.data import get_design_review_stats

        stats = get_design_review_stats()

        assert stats["total_reviews"] == 0
        assert stats["passed"] == 0
        assert stats["failed"] == 0

    def test_returns_stats_from_design_reviews(self, tmp_path, monkeypatch):
        """Test returns computed stats from design review results."""
        import asp.web.data as data_module

        design_file = tmp_path / "bootstrap_design_review_results.json"
        design_file.write_text(
            json.dumps(
                {
                    "results": [
                        {
                            "verdict": "PASS",
                            "findings": [
                                {"category": "Security"},
                            ],
                        },
                        {
                            "verdict": "FAIL",
                            "findings": [
                                {"category": "Performance"},
                                {"category": "Security"},
                            ],
                        },
                        {
                            "verdict": "NEEDS_IMPROVEMENT",
                            "findings": [],
                        },
                    ]
                }
            )
        )

        monkeypatch.setattr(data_module, "BOOTSTRAP_DESIGN_RESULTS", design_file)

        from asp.web.data import get_design_review_stats

        stats = get_design_review_stats()

        assert stats["total_reviews"] == 3
        assert stats["passed"] == 1
        assert stats["failed"] == 1
        assert stats["needs_improvement"] == 1
        assert stats["total_defects"] == 3
        assert stats["by_category"]["Security"] == 2
        assert stats["by_category"]["Performance"] == 1
