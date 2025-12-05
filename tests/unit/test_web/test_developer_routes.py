"""
Integration tests for Developer persona (Alex) routes.

Uses starlette TestClient and lxml for HTML validation per FastHTML testing best practices.
See: https://krokotsch.eu/posts/testing-fasthtml/
"""

import pytest
from lxml import html
from starlette.testclient import TestClient

from asp.web.main import app


@pytest.fixture
def client():
    """Create test client for the FastHTML app."""
    return TestClient(app)


@pytest.fixture
def mock_data_layer(monkeypatch):
    """Mock data layer functions for deterministic testing.

    Note: We mock on the developer module where functions are imported,
    not on the data module where they are defined.
    """
    import asp.web.developer as developer_module

    # Mock get_tasks
    mock_tasks = [
        {
            "task_id": "TASK-001",
            "description": "Implement user authentication with OAuth2",
            "status": "completed",
            "complexity": 150,
            "num_units": 5,
            "execution_time": 45.2,
        },
        {
            "task_id": "TASK-002",
            "description": "Add dashboard widgets for metrics display",
            "status": "in_progress",
            "complexity": 80,
            "num_units": 3,
            "execution_time": 0,
        },
        {
            "task_id": "TASK-003",
            "description": "Design API endpoints for user management",
            "status": "planning",
            "complexity": 0,
            "num_units": 0,
            "execution_time": 0,
        },
    ]
    monkeypatch.setattr(developer_module, "get_tasks", lambda: mock_tasks)

    # Mock get_agent_stats
    mock_stats = {
        "total_tasks": 10,
        "successful": 8,
        "failed": 2,
        "avg_complexity": 120.5,
        "avg_execution_time": 35.0,
        "total_units": 42,
    }
    monkeypatch.setattr(developer_module, "get_agent_stats", lambda: mock_stats)

    # Mock get_recent_activity
    mock_activity = [
        {
            "task_id": "TASK-001",
            "date": "2025-12-05",
            "time": "10:30:00",
            "action": "Completed code generation for authentication module",
            "status": "Success",
        },
        {
            "task_id": "TASK-002",
            "date": "2025-12-05",
            "time": "09:15:00",
            "action": "Started design phase for dashboard widgets",
            "status": "Success",
        },
        {
            "task_id": "TASK-003",
            "date": "2025-12-04",
            "time": "16:45:00",
            "action": "Created planning document for API endpoints",
            "status": "Success",
        },
    ]
    monkeypatch.setattr(
        developer_module, "get_recent_activity", lambda limit=10: mock_activity[:limit]
    )

    # Mock get_task_details
    def mock_get_task_details(task_id):
        if task_id == "TASK-001":
            return {
                "task_id": "TASK-001",
                "description": "Implement user authentication",
                "status": "completed",
                "artifacts": [
                    {"name": "plan.json", "type": "file", "size": 1024},
                    {"name": "design.json", "type": "file", "size": 2048},
                    {"name": "src/auth.py", "type": "file", "size": 4096},
                ],
                "plan": "1. Setup OAuth2 provider\n2. Implement login flow\n3. Add token validation",
                "design": "Authentication module using FastAPI OAuth2 with JWT tokens",
                "telemetry": {
                    "total_latency_ms": 5200,
                    "total_tokens_in": 15000,
                    "total_tokens_out": 8000,
                    "total_cost_usd": 0.0456,
                },
            }
        if task_id == "TASK-002":
            return {
                "task_id": "TASK-002",
                "description": "Add dashboard widgets",
                "status": "in_progress",
                "artifacts": [
                    {"name": "plan.json", "type": "file", "size": 512},
                ],
                "plan": "1. Design widget components\n2. Implement metrics API",
                "design": None,
                "telemetry": None,
            }
        return None

    monkeypatch.setattr(developer_module, "get_task_details", mock_get_task_details)

    # Mock get_artifact_history
    def mock_get_artifact_history(task_id):
        if task_id == "TASK-001":
            return [
                {
                    "name": "plan.json",
                    "phase": "plan",
                    "version": 1,
                    "size": 1024,
                    "modified_display": "2025-12-05 09:00",
                    "preview": '{"steps": ["step1", "step2"]}',
                },
                {
                    "name": "design.json",
                    "phase": "design",
                    "version": 1,
                    "size": 2048,
                    "modified_display": "2025-12-05 09:30",
                    "preview": '{"components": ["auth"]}',
                },
                {
                    "name": "src/auth.py",
                    "phase": "code",
                    "version": 1,
                    "size": 4096,
                    "modified_display": "2025-12-05 10:00",
                    "preview": "def authenticate(user):\n    pass",
                },
            ]
        return []

    monkeypatch.setattr(
        developer_module, "get_artifact_history", mock_get_artifact_history
    )

    # Mock get_code_proposals
    def mock_get_code_proposals(task_id):
        if task_id == "TASK-001":
            return [
                {
                    "filename": "src/auth.py",
                    "lines": 45,
                    "status": "approved",
                    "content": "from fastapi import Depends\n\ndef authenticate(user):\n    return True",
                },
                {
                    "filename": "src/tokens.py",
                    "lines": 30,
                    "status": "pending",
                    "content": "import jwt\n\ndef create_token(user_id):\n    return jwt.encode({})",
                },
            ]
        return []

    monkeypatch.setattr(developer_module, "get_code_proposals", mock_get_code_proposals)

    # Mock get_cost_breakdown
    monkeypatch.setattr(
        developer_module,
        "get_cost_breakdown",
        lambda days=7: {
            "total_usd": 12.45,
            "by_role": {"design": 5.20, "code": 4.80, "test": 2.45},
            "token_usage": {"input": 125000, "output": 45000},
        },
    )

    # Mock get_active_agents
    monkeypatch.setattr(
        developer_module,
        "get_active_agents",
        lambda: [
            {
                "agent_name": "Code Agent",
                "task_id": "TASK-002",
                "phase": "code_generation",
            }
        ],
    )

    return mock_tasks


class TestDeveloperDashboard:
    """Tests for /developer route - main dashboard."""

    def test_developer_dashboard_returns_200(self, client, mock_data_layer):
        """Test that developer dashboard loads successfully."""
        response = client.get("/developer")
        assert response.status_code == 200

    def test_developer_dashboard_has_title(self, client, mock_data_layer):
        """Test dashboard has correct title."""
        response = client.get("/developer")
        tree = html.fromstring(response.text)

        titles = tree.xpath("//title/text()")
        assert any("Flow State Canvas" in t or "Alex" in t for t in titles)

    def test_developer_dashboard_shows_active_tasks(self, client, mock_data_layer):
        """Test dashboard shows active tasks sidebar."""
        response = client.get("/developer")

        assert "Active Tasks" in response.text
        # Should show in_progress and planning tasks
        assert "TASK-002" in response.text or "TASK-003" in response.text

    def test_developer_dashboard_shows_completed_tasks(self, client, mock_data_layer):
        """Test dashboard shows recently completed tasks."""
        response = client.get("/developer")

        assert "Recent Completed" in response.text
        assert "TASK-001" in response.text

    def test_developer_dashboard_shows_stats(self, client, mock_data_layer):
        """Test dashboard shows task statistics."""
        response = client.get("/developer")

        # Check for total tasks count
        assert "10" in response.text  # total_tasks from mock
        assert "Success Rate" in response.text

    def test_developer_dashboard_shows_recent_activity(self, client, mock_data_layer):
        """Test dashboard shows recent activity table."""
        response = client.get("/developer")

        assert "Recent Activity" in response.text
        assert "Time" in response.text
        assert "Action" in response.text
        assert "Status" in response.text

    def test_developer_dashboard_has_tools_links(self, client, mock_data_layer):
        """Test dashboard has tool navigation links."""
        response = client.get("/developer")
        tree = html.fromstring(response.text)

        assert "Tools" in response.text
        links = tree.xpath("//a/@href")
        assert "/developer/tasks" in links
        assert "/developer/stats" in links

    def test_developer_dashboard_has_back_link(self, client, mock_data_layer):
        """Test dashboard has back to home link."""
        response = client.get("/developer")
        tree = html.fromstring(response.text)

        home_links = tree.xpath("//a[contains(@href, '/')]")
        assert len(home_links) >= 1


class TestAllTasksView:
    """Tests for /developer/tasks route - All tasks view."""

    def test_all_tasks_page_loads(self, client, mock_data_layer):
        """Test all tasks page loads successfully."""
        response = client.get("/developer/tasks")
        assert response.status_code == 200

    def test_all_tasks_has_title(self, client, mock_data_layer):
        """Test page has appropriate title."""
        response = client.get("/developer/tasks")

        assert "All Tasks" in response.text

    def test_all_tasks_shows_table(self, client, mock_data_layer):
        """Test page shows tasks in a table."""
        response = client.get("/developer/tasks")
        tree = html.fromstring(response.text)

        # Check for table headers
        assert "Task ID" in response.text
        assert "Description" in response.text
        assert "Complexity" in response.text
        assert "Status" in response.text

    def test_all_tasks_shows_all_task_ids(self, client, mock_data_layer):
        """Test page shows all task IDs."""
        response = client.get("/developer/tasks")

        assert "TASK-001" in response.text
        assert "TASK-002" in response.text
        assert "TASK-003" in response.text

    def test_all_tasks_has_task_links(self, client, mock_data_layer):
        """Test task IDs link to detail pages."""
        response = client.get("/developer/tasks")
        tree = html.fromstring(response.text)

        task_links = tree.xpath("//a[contains(@href, '/developer/task/')]")
        assert len(task_links) >= 3

    def test_all_tasks_has_back_link(self, client, mock_data_layer):
        """Test page has back to dashboard link."""
        response = client.get("/developer/tasks")
        tree = html.fromstring(response.text)

        back_links = tree.xpath("//a[contains(@href, '/developer')]")
        assert len(back_links) >= 1


class TestTaskDetailView:
    """Tests for /developer/task/{task_id} route - Task detail view."""

    def test_task_detail_page_loads(self, client, mock_data_layer):
        """Test task detail page loads for valid task."""
        response = client.get("/developer/task/TASK-001")
        assert response.status_code == 200

    def test_task_detail_shows_task_id(self, client, mock_data_layer):
        """Test page shows task ID in title."""
        response = client.get("/developer/task/TASK-001")

        assert "TASK-001" in response.text

    def test_task_detail_shows_artifacts(self, client, mock_data_layer):
        """Test page shows artifacts list."""
        response = client.get("/developer/task/TASK-001")

        assert "Artifacts" in response.text
        assert "plan.json" in response.text
        assert "design.json" in response.text

    def test_task_detail_shows_plan_preview(self, client, mock_data_layer):
        """Test page shows plan preview."""
        response = client.get("/developer/task/TASK-001")

        assert "Plan Preview" in response.text
        assert "OAuth2" in response.text

    def test_task_detail_shows_action_links(self, client, mock_data_layer):
        """Test page shows action links."""
        response = client.get("/developer/task/TASK-001")
        tree = html.fromstring(response.text)

        # Check for trace and diff links
        trace_links = tree.xpath("//a[contains(@href, '/trace')]")
        diff_links = tree.xpath("//a[contains(@href, '/diff')]")
        assert len(trace_links) >= 1
        assert len(diff_links) >= 1

    def test_task_detail_not_found(self, client, mock_data_layer):
        """Test page shows not found for invalid task."""
        response = client.get("/developer/task/NONEXISTENT")
        assert response.status_code == 200

        assert "not found" in response.text.lower()

    def test_task_detail_has_navigation(self, client, mock_data_layer):
        """Test page has navigation links."""
        response = client.get("/developer/task/TASK-001")
        tree = html.fromstring(response.text)

        back_links = tree.xpath("//a[contains(@href, '/developer')]")
        assert len(back_links) >= 1


class TestArtifactTimeline:
    """Tests for /developer/task/{task_id}/trace route - Artifact timeline."""

    def test_trace_page_loads(self, client, mock_data_layer):
        """Test artifact timeline page loads."""
        response = client.get("/developer/task/TASK-001/trace")
        assert response.status_code == 200

    def test_trace_shows_title(self, client, mock_data_layer):
        """Test page shows timeline title."""
        response = client.get("/developer/task/TASK-001/trace")

        assert "Artifact Timeline" in response.text
        assert "TASK-001" in response.text

    def test_trace_shows_artifact_count(self, client, mock_data_layer):
        """Test page shows artifact count."""
        response = client.get("/developer/task/TASK-001/trace")

        assert "3 artifacts" in response.text

    def test_trace_shows_phases(self, client, mock_data_layer):
        """Test page shows phase labels."""
        response = client.get("/developer/task/TASK-001/trace")

        assert "Plan" in response.text
        assert "Design" in response.text
        assert "Code" in response.text

    def test_trace_shows_artifact_names(self, client, mock_data_layer):
        """Test page shows artifact names."""
        response = client.get("/developer/task/TASK-001/trace")

        assert "plan.json" in response.text
        assert "design.json" in response.text
        assert "src/auth.py" in response.text

    def test_trace_shows_telemetry(self, client, mock_data_layer):
        """Test page shows execution telemetry."""
        response = client.get("/developer/task/TASK-001/trace")

        assert "Execution Telemetry" in response.text
        assert "Latency" in response.text
        assert "Tokens" in response.text

    def test_trace_not_found(self, client, mock_data_layer):
        """Test page shows not found for invalid task."""
        response = client.get("/developer/task/NONEXISTENT/trace")
        assert response.status_code == 200

        assert "not found" in response.text.lower()

    def test_trace_has_navigation(self, client, mock_data_layer):
        """Test page has navigation links."""
        response = client.get("/developer/task/TASK-001/trace")
        tree = html.fromstring(response.text)

        back_links = tree.xpath("//a[contains(@href, '/developer/task/TASK-001')]")
        assert len(back_links) >= 1


class TestCodeDiffView:
    """Tests for /developer/task/{task_id}/diff route - Code diff view."""

    def test_diff_page_loads(self, client, mock_data_layer):
        """Test code diff page loads."""
        response = client.get("/developer/task/TASK-001/diff")
        assert response.status_code == 200

    def test_diff_shows_title(self, client, mock_data_layer):
        """Test page shows code review title."""
        response = client.get("/developer/task/TASK-001/diff")

        assert "Code Review" in response.text or "Code Proposals" in response.text
        assert "TASK-001" in response.text

    def test_diff_shows_proposal_count(self, client, mock_data_layer):
        """Test page shows proposal count."""
        response = client.get("/developer/task/TASK-001/diff")

        assert "2 file" in response.text

    def test_diff_shows_filenames(self, client, mock_data_layer):
        """Test page shows proposed filenames."""
        response = client.get("/developer/task/TASK-001/diff")

        assert "src/auth.py" in response.text
        assert "src/tokens.py" in response.text

    def test_diff_shows_status(self, client, mock_data_layer):
        """Test page shows proposal status."""
        response = client.get("/developer/task/TASK-001/diff")

        assert "APPROVED" in response.text
        assert "PENDING" in response.text

    def test_diff_shows_code_content(self, client, mock_data_layer):
        """Test page shows code content."""
        response = client.get("/developer/task/TASK-001/diff")

        assert "fastapi" in response.text or "authenticate" in response.text
        assert "jwt" in response.text or "create_token" in response.text

    def test_diff_shows_action_buttons(self, client, mock_data_layer):
        """Test page shows action buttons (disabled)."""
        response = client.get("/developer/task/TASK-001/diff")

        assert "Approve" in response.text
        assert "Reject" in response.text

    def test_diff_not_found(self, client, mock_data_layer):
        """Test page shows not found for invalid task."""
        response = client.get("/developer/task/NONEXISTENT/diff")
        assert response.status_code == 200

        assert "not found" in response.text.lower()

    def test_diff_empty_proposals(self, client, mock_data_layer):
        """Test page handles task with no proposals."""
        response = client.get("/developer/task/TASK-002/diff")
        assert response.status_code == 200

        assert "No code proposals" in response.text


class TestAgentStats:
    """Tests for /developer/stats route - Agent statistics."""

    def test_stats_page_loads(self, client, mock_data_layer):
        """Test stats page loads successfully."""
        response = client.get("/developer/stats")
        assert response.status_code == 200

    def test_stats_shows_title(self, client, mock_data_layer):
        """Test page shows statistics title."""
        response = client.get("/developer/stats")

        assert "Agent" in response.text and "Statistics" in response.text

    def test_stats_shows_task_metrics(self, client, mock_data_layer):
        """Test page shows task metrics."""
        response = client.get("/developer/stats")

        assert "Task Metrics" in response.text
        assert "Total Tasks" in response.text
        assert "Successful" in response.text
        assert "Failed" in response.text
        assert "Success Rate" in response.text

    def test_stats_shows_performance_metrics(self, client, mock_data_layer):
        """Test page shows performance metrics."""
        response = client.get("/developer/stats")

        assert "Performance" in response.text
        assert "Avg Complexity" in response.text
        assert "Avg Execution Time" in response.text

    def test_stats_shows_cost_tracking(self, client, mock_data_layer):
        """Test page shows API cost tracking."""
        response = client.get("/developer/stats")

        assert "API Cost" in response.text or "Cost Tracking" in response.text
        assert "$12.45" in response.text  # total_usd from mock

    def test_stats_shows_token_usage(self, client, mock_data_layer):
        """Test page shows token usage."""
        response = client.get("/developer/stats")

        assert "Total Tokens" in response.text
        assert "Input Tokens" in response.text
        assert "Output Tokens" in response.text

    def test_stats_shows_cost_by_role(self, client, mock_data_layer):
        """Test page shows cost breakdown by role."""
        response = client.get("/developer/stats")

        assert "Cost by Agent Role" in response.text
        assert "design" in response.text.lower()
        assert "code" in response.text.lower()

    def test_stats_has_back_link(self, client, mock_data_layer):
        """Test page has back to dashboard link."""
        response = client.get("/developer/stats")
        tree = html.fromstring(response.text)

        back_links = tree.xpath("//a[contains(@href, '/developer')]")
        assert len(back_links) >= 1


class TestDeveloperAPIEndpoints:
    """Tests for developer API/HTMX endpoints."""

    def test_current_task_endpoint(self, client, mock_data_layer):
        """Test current task API endpoint."""
        response = client.get("/developer/api/current-task")
        assert response.status_code == 200

        # Should return task info
        assert "TSP-IMPL-001" in response.text or "Progress" in response.text

    def test_stats_api_endpoint(self, client, mock_data_layer):
        """Test stats API endpoint."""
        response = client.get("/developer/api/stats")
        assert response.status_code == 200

        # Should return stats info
        assert "Executions" in response.text or "Activity" in response.text

    def test_activity_api_endpoint(self, client, mock_data_layer):
        """Test activity API endpoint."""
        response = client.get("/developer/api/activity")
        assert response.status_code == 200

        # Should return activity table
        assert "Time" in response.text or "Action" in response.text

    def test_activity_htmx_endpoint(self, client, mock_data_layer):
        """Test activity HTMX endpoint."""
        response = client.get("/developer/activity", headers={"HX-Request": "true"})
        assert response.status_code == 200

        assert "Recent Activity" in response.text

    def test_active_agents_endpoint(self, client, mock_data_layer):
        """Test active agents HTMX endpoint."""
        response = client.get(
            "/developer/active-agents", headers={"HX-Request": "true"}
        )
        assert response.status_code == 200

        # Should show active agent
        assert "Code Agent" in response.text or "TASK-002" in response.text

    def test_active_agents_empty_state(self, client, monkeypatch):
        """Test active agents returns message when none active."""
        import asp.web.developer as developer_module

        monkeypatch.setattr(developer_module, "get_active_agents", lambda: [])

        response = client.get(
            "/developer/active-agents", headers={"HX-Request": "true"}
        )
        assert response.status_code == 200

        assert "No agents" in response.text or len(response.text.strip()) > 0


class TestDeveloperNavigation:
    """Tests for navigation between developer routes."""

    def test_dashboard_links_to_tasks(self, client, mock_data_layer):
        """Test dashboard has link to all tasks."""
        response = client.get("/developer")
        tree = html.fromstring(response.text)

        links = tree.xpath("//a[@href='/developer/tasks']")
        assert len(links) >= 1

    def test_dashboard_links_to_stats(self, client, mock_data_layer):
        """Test dashboard has link to stats."""
        response = client.get("/developer")
        tree = html.fromstring(response.text)

        links = tree.xpath("//a[@href='/developer/stats']")
        assert len(links) >= 1

    def test_task_detail_links_to_trace(self, client, mock_data_layer):
        """Test task detail has link to trace."""
        response = client.get("/developer/task/TASK-001")
        tree = html.fromstring(response.text)

        links = tree.xpath("//a[contains(@href, '/trace')]")
        assert len(links) >= 1

    def test_task_detail_links_to_diff(self, client, mock_data_layer):
        """Test task detail has link to diff view."""
        response = client.get("/developer/task/TASK-001")
        tree = html.fromstring(response.text)

        links = tree.xpath("//a[contains(@href, '/diff')]")
        assert len(links) >= 1


class TestDeveloperAccessibility:
    """Basic accessibility tests for developer routes."""

    def test_dashboard_has_headings(self, client, mock_data_layer):
        """Test dashboard has proper heading structure."""
        response = client.get("/developer")
        tree = html.fromstring(response.text)

        h3_tags = tree.xpath("//h3")
        h4_tags = tree.xpath("//h4")

        assert len(h3_tags) >= 1
        assert len(h4_tags) >= 1

    def test_tables_have_headers(self, client, mock_data_layer):
        """Test tables have proper header rows."""
        response = client.get("/developer/tasks")
        tree = html.fromstring(response.text)

        thead = tree.xpath("//thead")
        assert len(thead) >= 1

    def test_links_have_text(self, client, mock_data_layer):
        """Test links have visible text content."""
        response = client.get("/developer")
        tree = html.fromstring(response.text)

        links = tree.xpath("//a")
        for link in links:
            # Links should have text or children with text
            text = link.text_content().strip()
            assert len(text) > 0 or len(link.xpath(".//*")) > 0
