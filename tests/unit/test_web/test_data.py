"""
Unit tests for web data access layer.

Tests the data access functions that fetch tasks, telemetry, and artifacts
for display in the web interface.
"""

import json

import pytest


@pytest.fixture
def isolated_data_layer(tmp_path, monkeypatch):
    """Isolate tests from production data."""
    import asp.web.data as data_module

    monkeypatch.setattr(data_module, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(data_module, "ARTIFACTS_DIR", tmp_path / "artifacts")
    monkeypatch.setattr(data_module, "TELEMETRY_DB", tmp_path / "telemetry.db")
    monkeypatch.setattr(data_module, "BOOTSTRAP_RESULTS", tmp_path / "bootstrap.json")
    monkeypatch.setattr(
        data_module, "BOOTSTRAP_DESIGN_RESULTS", tmp_path / "design_review.json"
    )
    monkeypatch.setattr(data_module, "DATA_DIR", tmp_path / "data")
    return tmp_path


class TestSanitizeText:
    """Test the _sanitize_text utility function."""

    def test_sanitizes_normal_text(self, isolated_data_layer):
        """Test normal text passes through unchanged."""
        from asp.web.data import _sanitize_text

        result = _sanitize_text("Hello, World!")
        assert result == "Hello, World!"

    def test_handles_non_string_input(self, isolated_data_layer):
        """Test non-string input returns unchanged."""
        from asp.web.data import _sanitize_text

        result = _sanitize_text(123)
        assert result == 123

    def test_handles_unicode_text(self, isolated_data_layer):
        """Test Unicode text is preserved."""
        from asp.web.data import _sanitize_text

        result = _sanitize_text("Hello \u4e16\u754c")  # Hello World in Chinese
        assert "\u4e16\u754c" in result


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


class TestGetArtifactHistory:
    """Test the get_artifact_history function."""

    def test_returns_empty_for_nonexistent_task(self, isolated_data_layer):
        """Test returns empty list for non-existent task."""
        from asp.web.data import get_artifact_history

        history = get_artifact_history("NONEXISTENT")
        assert history == []

    def test_returns_artifacts_sorted_by_phase(self, isolated_data_layer):
        """Test returns artifacts sorted by development phase."""
        tmp_path = isolated_data_layer
        artifacts_dir = tmp_path / "artifacts"
        artifacts_dir.mkdir()

        task_dir = artifacts_dir / "TASK-001"
        task_dir.mkdir()
        (task_dir / "design.md").write_text("# Design")
        (task_dir / "plan.md").write_text("# Plan")
        (task_dir / "code.py").write_text("print('hello')")

        from asp.web.data import get_artifact_history

        history = get_artifact_history("TASK-001")

        assert len(history) == 3
        # Should be sorted by phase order: plan, design, code
        assert history[0]["phase"] == "plan"
        assert history[1]["phase"] == "design"
        assert history[2]["phase"] == "code"


class TestGetAgentHealth:
    """Test the get_agent_health function."""

    def test_returns_unknown_status_when_no_db(self, isolated_data_layer):
        """Test returns unknown status when no telemetry database."""
        from asp.web.data import get_agent_health

        health = get_agent_health()

        assert len(health) == 7  # 7 agents
        for agent in health:
            assert agent["status"] == "Unknown"
            assert agent["last_active"] == "No data"


class TestGetCostBreakdown:
    """Test the get_cost_breakdown function."""

    def test_returns_default_when_no_db(self, isolated_data_layer):
        """Test returns default values when no telemetry database."""
        from asp.web.data import get_cost_breakdown

        breakdown = get_cost_breakdown()

        assert breakdown["total_usd"] == 0
        assert breakdown["by_role"] == {}
        assert breakdown["token_usage"]["input"] == 0
        assert breakdown["token_usage"]["output"] == 0


class TestGetDailyMetrics:
    """Test the get_daily_metrics function."""

    def test_returns_placeholder_when_no_db(self, isolated_data_layer):
        """Test returns placeholder metrics when no telemetry database."""
        from asp.web.data import get_daily_metrics

        metrics = get_daily_metrics(days=7)

        assert len(metrics["dates"]) == 7
        assert len(metrics["cost"]) == 7
        assert len(metrics["tokens"]) == 7
        assert len(metrics["tasks"]) == 7
        # All values should be 0 for placeholder
        assert all(c == 0 for c in metrics["cost"])


class TestGenerateSparklineSvg:
    """Test the generate_sparkline_svg function."""

    def test_returns_no_data_for_empty_values(self, isolated_data_layer):
        """Test returns 'No data' message for empty values."""
        from asp.web.data import generate_sparkline_svg

        svg = generate_sparkline_svg([])

        assert "No data" in svg

    def test_returns_no_data_for_all_zeros(self, isolated_data_layer):
        """Test returns 'No data' message when all values are zero."""
        from asp.web.data import generate_sparkline_svg

        svg = generate_sparkline_svg([0, 0, 0, 0])

        assert "No data" in svg

    def test_generates_svg_path_for_valid_data(self, isolated_data_layer):
        """Test generates SVG with path for valid data."""
        from asp.web.data import generate_sparkline_svg

        svg = generate_sparkline_svg([1, 2, 3, 4, 5])

        assert "<svg" in svg
        assert "<path" in svg
        assert "</svg>" in svg


class TestBudgetSettings:
    """Test budget settings functions."""

    def test_get_budget_settings_returns_defaults(self, isolated_data_layer):
        """Test returns default settings when no file exists."""
        from asp.web.data import get_budget_settings

        settings = get_budget_settings()

        assert settings["daily_limit"] == 10.00
        assert settings["monthly_limit"] == 100.00
        assert settings["alert_threshold"] == 0.80
        assert settings["enabled"] is True

    def test_save_and_load_budget_settings(self, isolated_data_layer):
        """Test saving and loading budget settings."""
        tmp_path = isolated_data_layer
        data_dir = tmp_path / "data"
        data_dir.mkdir()

        from asp.web.data import get_budget_settings, save_budget_settings

        new_settings = {
            "daily_limit": 25.00,
            "monthly_limit": 200.00,
            "alert_threshold": 0.90,
            "enabled": False,
        }
        result = save_budget_settings(new_settings)
        assert result is True

        loaded = get_budget_settings()
        assert loaded["daily_limit"] == 25.00
        assert loaded["monthly_limit"] == 200.00

    def test_get_budget_status(self, isolated_data_layer):
        """Test get_budget_status returns proper structure."""
        from asp.web.data import get_budget_status

        status = get_budget_status()

        assert "daily_spent" in status
        assert "daily_limit" in status
        assert "daily_pct" in status
        assert "monthly_spent" in status
        assert "status" in status
        assert status["status"] in ("ok", "warning", "exceeded")


class TestTimelineSimulator:
    """Test timeline simulation functions."""

    def test_get_timeline_features_empty_when_no_tasks(self, isolated_data_layer):
        """Test returns empty list when no tasks exist."""
        from asp.web.data import get_timeline_features

        features = get_timeline_features()
        assert features == []

    def test_get_timeline_features_from_bootstrap(self, isolated_data_layer):
        """Test extracts features from bootstrap results."""
        tmp_path = isolated_data_layer
        bootstrap_file = tmp_path / "bootstrap.json"
        bootstrap_file.write_text(
            json.dumps(
                {
                    "results": [
                        {
                            "task_id": "FEAT-001",
                            "description": "Feature one",
                            "actual_total_complexity": 200,
                            "execution_time_seconds": 3600,
                            "success": True,
                        },
                        {
                            "task_id": "FEAT-002",
                            "description": "Feature two",
                            "actual_total_complexity": 100,
                            "execution_time_seconds": 1800,
                            "success": False,
                        },
                    ]
                }
            )
        )

        from asp.web.data import get_timeline_features

        features = get_timeline_features()

        assert len(features) == 2
        assert features[0]["id"] == "FEAT-001"
        assert features[0]["status"] == "completed"
        assert features[0]["confidence"] == 100
        assert features[1]["id"] == "FEAT-002"
        # Failed tasks get status "failed" in get_tasks, which maps to "planned" in features
        assert features[1]["status"] in ("completed", "planned")

    def test_simulate_timeline_empty_features(self, isolated_data_layer):
        """Test simulation with empty features."""
        from asp.web.data import simulate_timeline

        result = simulate_timeline(features=[])

        assert result["features"] == []
        assert result["total_weeks"] == 0
        assert result["completion_probability"] == 0
        assert len(result["suggestions"]) > 0

    def test_simulate_timeline_default_params(self, isolated_data_layer):
        """Test simulation with default parameters."""
        features = [
            {
                "id": "TASK-001",
                "name": "Test feature",
                "status": "planned",
                "complexity": 150,
                "estimated_hours": 1.5,
                "confidence": 60,
                "risk": "medium",
                "start_week": 0,
                "duration_weeks": 1.0,
            }
        ]

        from asp.web.data import simulate_timeline

        result = simulate_timeline(
            team_capacity=1.0, budget_multiplier=1.0, features=features
        )

        assert result["total_weeks"] > 0
        assert 0 < result["completion_probability"] <= 100
        assert "risk_summary" in result
        assert "suggestions" in result

    def test_simulate_timeline_high_capacity(self, isolated_data_layer):
        """Test that higher capacity shortens timeline."""
        features = [
            {
                "id": "TASK-001",
                "name": "Test feature",
                "status": "planned",
                "complexity": 150,
                "estimated_hours": 1.5,
                "confidence": 60,
                "risk": "medium",
                "start_week": 0,
                "duration_weeks": 2.0,
            }
        ]

        from asp.web.data import simulate_timeline

        result_normal = simulate_timeline(team_capacity=1.0, features=features)
        result_high = simulate_timeline(team_capacity=2.0, features=features)

        # Higher capacity should result in shorter timeline
        assert result_high["total_weeks"] < result_normal["total_weeks"]

    def test_simulate_timeline_high_budget(self, isolated_data_layer):
        """Test that higher budget improves confidence."""
        features = [
            {
                "id": "TASK-001",
                "name": "Test feature",
                "status": "planned",
                "complexity": 150,
                "estimated_hours": 1.5,
                "confidence": 60,
                "risk": "high",
                "start_week": 0,
                "duration_weeks": 2.0,
            }
        ]

        from asp.web.data import simulate_timeline

        result_low = simulate_timeline(budget_multiplier=0.5, features=features)
        result_high = simulate_timeline(budget_multiplier=2.0, features=features)

        # Higher budget should improve completion probability
        assert (
            result_high["completion_probability"]
            >= result_low["completion_probability"]
        )


class TestTaskExecution:
    """Test task execution service functions."""

    def test_register_and_get_running_tasks(self, isolated_data_layer):
        """Test registering and retrieving running tasks."""
        from asp.web.data import (
            _running_tasks,
            get_running_tasks,
            register_task_execution,
        )

        # Clear any existing tasks
        _running_tasks.clear()

        # Register a task
        register_task_execution("TEST-001", "Test task", "Test requirements")

        running = get_running_tasks()

        assert len(running) == 1
        assert running[0]["task_id"] == "TEST-001"
        assert running[0]["status"] == "pending"

        # Clean up
        _running_tasks.clear()

    def test_update_task_progress(self, isolated_data_layer):
        """Test updating task progress."""
        from asp.web.data import (
            _running_tasks,
            get_task_execution_status,
            register_task_execution,
            update_task_progress,
        )

        _running_tasks.clear()
        register_task_execution("TEST-001", "Test task", "Test requirements")

        update_task_progress("TEST-001", "design", "running", 30)

        status = get_task_execution_status("TEST-001")
        assert status["current_phase"] == "design"
        assert status["progress_pct"] == 30

        _running_tasks.clear()

    def test_complete_task_execution(self, isolated_data_layer):
        """Test completing task execution."""
        from asp.web.data import (
            _running_tasks,
            _task_results,
            complete_task_execution,
            get_running_tasks,
            get_task_execution_status,
            register_task_execution,
        )

        _running_tasks.clear()
        _task_results.clear()

        register_task_execution("TEST-001", "Test task", "Test requirements")
        complete_task_execution("TEST-001", {"output": "success"}, success=True)

        # Should no longer be in running tasks
        running = get_running_tasks()
        assert len(running) == 0

        # Should be in completed results
        status = get_task_execution_status("TEST-001")
        assert status["status"] == "completed"
        assert status["progress_pct"] == 100

        _task_results.clear()

    def test_get_active_agents(self, isolated_data_layer):
        """Test getting active agents based on running tasks."""
        from asp.web.data import (
            _running_tasks,
            get_active_agents,
            register_task_execution,
            update_task_progress,
        )

        _running_tasks.clear()
        register_task_execution("TEST-001", "Test task", "Test requirements")
        update_task_progress("TEST-001", "design", "running")

        agents = get_active_agents()

        assert len(agents) == 1
        assert agents[0]["agent_name"] == "Design Agent"
        assert agents[0]["task_id"] == "TEST-001"

        _running_tasks.clear()


class TestPhaseYieldData:
    """Test phase yield analysis function."""

    def test_returns_default_when_no_data(self, isolated_data_layer):
        """Test returns default structure when no data."""
        from asp.web.data import get_phase_yield_data

        data = get_phase_yield_data()

        assert "phases" in data
        assert "phase_counts" in data
        assert "transitions" in data
        assert data["total_started"] == 0

    def test_counts_completed_tasks(self, isolated_data_layer):
        """Test counts completed tasks from bootstrap."""
        tmp_path = isolated_data_layer
        bootstrap_file = tmp_path / "bootstrap.json"
        bootstrap_file.write_text(
            json.dumps(
                {
                    "results": [
                        {"task_id": "T1", "success": True},
                        {"task_id": "T2", "success": True},
                        {"task_id": "T3", "success": False},
                    ]
                }
            )
        )

        from asp.web.data import get_phase_yield_data

        data = get_phase_yield_data()

        assert data["phase_counts"]["Complete"] == 2
        assert data["phase_counts"]["Code"] == 1  # Failed tasks


class TestCodeDiffUtilities:
    """Test code diff utility functions."""

    def test_generate_unified_diff(self, isolated_data_layer):
        """Test generating unified diff."""
        from asp.web.data import generate_unified_diff

        original = "line1\nline2\nline3"
        modified = "line1\nline2_modified\nline3"

        diff = generate_unified_diff(original, modified, "test.py")

        assert "---" in diff
        assert "+++" in diff
        assert "-line2" in diff
        assert "+line2_modified" in diff

    def test_get_code_proposals_empty(self, isolated_data_layer):
        """Test returns empty list for nonexistent task."""
        from asp.web.data import get_code_proposals

        proposals = get_code_proposals("NONEXISTENT")
        assert proposals == []

    def test_get_code_proposals_from_task(self, isolated_data_layer):
        """Test gets code proposals from task directory."""
        tmp_path = isolated_data_layer
        artifacts_dir = tmp_path / "artifacts"
        artifacts_dir.mkdir()

        task_dir = artifacts_dir / "TASK-001"
        task_dir.mkdir()
        code_dir = task_dir / "code"
        code_dir.mkdir()
        (code_dir / "main.py").write_text("print('hello')")
        (code_dir / "utils.py").write_text("def helper(): pass")

        from asp.web.data import get_code_proposals

        proposals = get_code_proposals("TASK-001")

        assert len(proposals) == 2
        assert any(p["filename"] == "main.py" for p in proposals)
        assert any(p["filename"] == "utils.py" for p in proposals)
