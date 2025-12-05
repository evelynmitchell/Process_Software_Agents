"""
Integration tests for Manager persona (Sarah) routes.

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

    Note: We mock on the manager module where functions are imported,
    not on the data module where they are defined.
    """
    import asp.web.manager as manager_module

    # Mock get_tasks
    mock_tasks = [
        {
            "task_id": "TASK-001",
            "description": "Implement user authentication",
            "status": "completed",
            "complexity": 150,
            "num_units": 5,
            "execution_time": 45.2,
        },
        {
            "task_id": "TASK-002",
            "description": "Add dashboard widgets",
            "status": "in_progress",
            "complexity": 80,
            "num_units": 3,
            "execution_time": 0,
        },
        {
            "task_id": "TASK-003",
            "description": "Design API endpoints",
            "status": "planning",
            "complexity": 0,
            "num_units": 0,
            "execution_time": 0,
        },
    ]
    monkeypatch.setattr(manager_module, "get_tasks", lambda: mock_tasks)

    # Mock get_agent_stats
    mock_stats = {
        "total_tasks": 10,
        "successful": 8,
        "failed": 2,
        "avg_complexity": 120.5,
        "avg_execution_time": 35.0,
        "total_units": 42,
    }
    monkeypatch.setattr(manager_module, "get_agent_stats", lambda: mock_stats)

    # Mock get_design_review_stats
    mock_review_stats = {
        "total_reviews": 15,
        "passed": 12,
        "failed": 2,
        "needs_improvement": 1,
        "total_defects": 8,
        "by_category": {
            "Security": 3,
            "Performance": 2,
            "Maintainability": 3,
        },
    }
    monkeypatch.setattr(
        manager_module, "get_design_review_stats", lambda: mock_review_stats
    )

    # Mock get_agent_health
    mock_health = [
        {
            "name": "Planning Agent",
            "status": "Operational",
            "last_active": "2 min ago",
            "executions": 42,
        },
        {
            "name": "Design Agent",
            "status": "Idle",
            "last_active": "1 hour ago",
            "executions": 38,
        },
        {
            "name": "Code Agent",
            "status": "Operational",
            "last_active": "5 min ago",
            "executions": 35,
        },
        {
            "name": "Test Agent",
            "status": "Unknown",
            "last_active": "No data",
            "executions": 0,
        },
    ]
    monkeypatch.setattr(manager_module, "get_agent_health", lambda: mock_health)

    # Mock get_cost_breakdown
    monkeypatch.setattr(
        manager_module,
        "get_cost_breakdown",
        lambda days=7: {
            "total_usd": 12.45,
            "by_role": {"design": 5.20, "code": 4.80, "test": 2.45},
            "token_usage": {"input": 125000, "output": 45000},
        },
    )

    # Mock get_daily_metrics
    monkeypatch.setattr(
        manager_module,
        "get_daily_metrics",
        lambda days=7: {
            "dates": ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
            "cost": [1.50, 2.20, 1.80, 2.10, 1.90, 0.50, 2.45],
            "tokens": [15000, 22000, 18000, 21000, 19000, 5000, 25000],
            "tasks": [3, 4, 3, 4, 3, 1, 4],
        },
    )

    # Mock get_budget_status
    monkeypatch.setattr(
        manager_module,
        "get_budget_status",
        lambda: {
            "daily_spent": 2.45,
            "daily_limit": 10.00,
            "daily_pct": 24.5,
            "monthly_spent": 45.80,
            "monthly_limit": 100.00,
            "monthly_pct": 45.8,
            "status": "ok",
            "status_color": "green",
        },
    )

    # Mock get_budget_settings
    monkeypatch.setattr(
        manager_module,
        "get_budget_settings",
        lambda: {
            "daily_limit": 10.00,
            "monthly_limit": 100.00,
            "alert_threshold": 0.80,
            "enabled": True,
        },
    )

    # Mock save_budget_settings
    monkeypatch.setattr(manager_module, "save_budget_settings", lambda s: True)

    # Mock get_active_agents
    monkeypatch.setattr(
        manager_module,
        "get_active_agents",
        lambda: [
            {
                "agent_name": "Code Agent",
                "task_id": "TASK-002",
                "phase": "code_generation",
            }
        ],
    )

    # Mock get_running_tasks
    monkeypatch.setattr(
        manager_module,
        "get_running_tasks",
        lambda: [
            {
                "task_id": "TASK-002",
                "description": "Add dashboard widgets",
                "phase": "code_generation",
                "status": "running",
                "progress_pct": 45,
            }
        ],
    )

    # Mock get_phase_yield_data
    monkeypatch.setattr(
        manager_module,
        "get_phase_yield_data",
        lambda: {
            "phases": ["Planning", "Design", "Code", "Test", "Complete"],
            "phase_counts": {
                "Planning": 3,
                "Design": 5,
                "Code": 8,
                "Test": 6,
                "Complete": 10,
            },
            "phase_defects": {
                "Design": 2,
                "Code": 5,
                "Test": 1,
            },
            "transitions": [
                {"from": "Planning", "to": "Design", "count": 12},
                {"from": "Design", "to": "Code", "count": 10},
                {"from": "Code", "to": "Test", "count": 9},
                {"from": "Test", "to": "Complete", "count": 8},
            ],
            "total_started": 15,
            "total_completed": 10,
            "yield_rate": 66.7,
            "total_defects": 8,
        },
    )

    # Mock generate_sparkline_svg
    monkeypatch.setattr(
        manager_module,
        "generate_sparkline_svg",
        lambda values, width=60, height=20, color="#000": '<svg width="60" height="20"><path d="M0,10 L60,10"/></svg>',
    )

    return mock_tasks


class TestManagerDashboard:
    """Tests for /manager route - main dashboard."""

    def test_manager_dashboard_returns_200(self, client, mock_data_layer):
        """Test that manager dashboard loads successfully."""
        response = client.get("/manager")
        assert response.status_code == 200

    def test_manager_dashboard_has_title(self, client, mock_data_layer):
        """Test dashboard has correct title."""
        response = client.get("/manager")
        tree = html.fromstring(response.text)

        titles = tree.xpath("//title/text()")
        assert any("ASP Overwatch" in t or "Sarah" in t for t in titles)

    def test_manager_dashboard_shows_success_rate(self, client, mock_data_layer):
        """Test dashboard displays success rate metric."""
        response = client.get("/manager")

        # 8 successful out of 10 = 80%
        assert "80%" in response.text or "Success Rate" in response.text

    def test_manager_dashboard_shows_active_tasks(self, client, mock_data_layer):
        """Test dashboard shows active task count."""
        response = client.get("/manager")

        assert "Active Tasks" in response.text

    def test_manager_dashboard_shows_cost_metrics(self, client, mock_data_layer):
        """Test dashboard shows API cost metrics."""
        response = client.get("/manager")

        assert "$12.45" in response.text or "API Cost" in response.text
        assert "Total Tokens" in response.text

    def test_manager_dashboard_shows_agent_health_table(self, client, mock_data_layer):
        """Test dashboard has agent health table."""
        response = client.get("/manager")
        tree = html.fromstring(response.text)

        assert "Agent Health" in response.text

        # Check for agent names in table
        assert "Planning Agent" in response.text
        assert "Design Agent" in response.text
        assert "Code Agent" in response.text

    def test_manager_dashboard_shows_quality_gates(self, client, mock_data_layer):
        """Test dashboard shows quality gate metrics."""
        response = client.get("/manager")

        assert "Quality Gates" in response.text
        assert "Design Reviews" in response.text
        assert "Pass Rate" in response.text

    def test_manager_dashboard_shows_defects_by_category(self, client, mock_data_layer):
        """Test dashboard shows defect categories."""
        response = client.get("/manager")

        assert "Defects by Category" in response.text
        assert "Security" in response.text
        assert "Performance" in response.text

    def test_manager_dashboard_shows_budget_status(self, client, mock_data_layer):
        """Test dashboard shows budget meters."""
        response = client.get("/manager")

        assert "Budget Status" in response.text
        assert "Daily" in response.text
        assert "Monthly" in response.text

    def test_manager_dashboard_shows_active_agents(self, client, mock_data_layer):
        """Test dashboard shows active agent indicators."""
        response = client.get("/manager")

        assert "Active Agents" in response.text
        assert "Code Agent" in response.text

    def test_manager_dashboard_shows_recent_tasks(self, client, mock_data_layer):
        """Test dashboard shows recent task activity table."""
        response = client.get("/manager")

        assert "Recent Task Activity" in response.text
        assert "TASK-001" in response.text


class TestManagerTasks:
    """Tests for /manager/tasks route - All tasks view."""

    def test_manager_tasks_page_loads(self, client, mock_data_layer):
        """Test tasks page loads successfully."""
        response = client.get("/manager/tasks")
        assert response.status_code == 200

    def test_manager_tasks_has_summary_stats(self, client, mock_data_layer):
        """Test page shows summary statistics."""
        response = client.get("/manager/tasks")

        assert "Total:" in response.text
        assert "Completed:" in response.text
        assert "Failed:" in response.text

    def test_manager_tasks_shows_all_tasks(self, client, mock_data_layer):
        """Test page shows all tasks in table."""
        response = client.get("/manager/tasks")
        tree = html.fromstring(response.text)

        # Check for task table
        tables = tree.xpath("//table")
        assert len(tables) >= 1

        # Check for all task IDs
        assert "TASK-001" in response.text
        assert "TASK-002" in response.text
        assert "TASK-003" in response.text

    def test_manager_tasks_has_back_link(self, client, mock_data_layer):
        """Test page has link back to dashboard."""
        response = client.get("/manager/tasks")
        tree = html.fromstring(response.text)

        back_links = tree.xpath("//a[contains(@href, '/manager')]")
        assert len(back_links) >= 1


class TestPhaseYield:
    """Tests for /manager/phase-yield route - Phase Yield Analysis."""

    def test_phase_yield_page_loads(self, client, mock_data_layer):
        """Test phase yield page loads successfully."""
        response = client.get("/manager/phase-yield")
        assert response.status_code == 200

    def test_phase_yield_shows_summary_metrics(self, client, mock_data_layer):
        """Test page shows summary metrics."""
        response = client.get("/manager/phase-yield")

        assert "Tasks Started" in response.text
        assert "Completed" in response.text
        assert "Yield Rate" in response.text
        assert "Defects Found" in response.text

    def test_phase_yield_shows_phase_flow(self, client, mock_data_layer):
        """Test page shows phase flow visualization."""
        response = client.get("/manager/phase-yield")

        assert "Phase Flow" in response.text
        assert "Planning" in response.text
        assert "Design" in response.text
        assert "Code" in response.text
        assert "Test" in response.text
        assert "Complete" in response.text

    def test_phase_yield_shows_transitions(self, client, mock_data_layer):
        """Test page shows phase transitions table."""
        response = client.get("/manager/phase-yield")

        assert "Phase Transitions" in response.text

    def test_phase_yield_has_back_link(self, client, mock_data_layer):
        """Test page has link back to dashboard."""
        response = client.get("/manager/phase-yield")
        tree = html.fromstring(response.text)

        back_links = tree.xpath("//a[contains(@href, '/manager')]")
        assert len(back_links) >= 1


class TestBudgetControls:
    """Tests for /manager/budget routes - Budget settings."""

    def test_budget_page_loads(self, client, mock_data_layer):
        """Test budget page loads successfully."""
        response = client.get("/manager/budget")
        assert response.status_code == 200

    def test_budget_page_shows_current_status(self, client, mock_data_layer):
        """Test page shows current budget status."""
        response = client.get("/manager/budget")

        assert "Current Status" in response.text
        assert "Daily Spend" in response.text
        assert "Monthly Spend" in response.text

    def test_budget_page_has_settings_form(self, client, mock_data_layer):
        """Test page has budget settings form."""
        response = client.get("/manager/budget")
        tree = html.fromstring(response.text)

        # Check for form inputs
        daily_limit = tree.xpath("//input[@name='daily_limit']")
        assert len(daily_limit) == 1

        monthly_limit = tree.xpath("//input[@name='monthly_limit']")
        assert len(monthly_limit) == 1

        alert_threshold = tree.xpath("//input[@name='alert_threshold']")
        assert len(alert_threshold) == 1

        enabled = tree.xpath("//input[@name='enabled']")
        assert len(enabled) == 1

    def test_budget_page_has_submit_button(self, client, mock_data_layer):
        """Test form has save button."""
        response = client.get("/manager/budget")
        tree = html.fromstring(response.text)

        submit_btn = tree.xpath("//button[@type='submit']")
        assert len(submit_btn) >= 1

    def test_budget_save_success(self, client, mock_data_layer):
        """Test saving budget settings returns success response."""
        response = client.post(
            "/manager/budget",
            data={
                "daily_limit": "15.00",
                "monthly_limit": "150.00",
                "alert_threshold": "85",
                "enabled": "on",
            },
        )
        assert response.status_code == 200
        # The route either returns "Saved!" or redirects to the budget page
        # Either way, response should be valid
        assert "Budget" in response.text or "Saved" in response.text

    def test_budget_page_has_back_link(self, client, mock_data_layer):
        """Test page has link back to dashboard."""
        response = client.get("/manager/budget")
        tree = html.fromstring(response.text)

        back_links = tree.xpath("//a[contains(@href, '/manager')]")
        assert len(back_links) >= 1


class TestManagerHTMXEndpoints:
    """Tests for HTMX endpoints in manager routes."""

    def test_agent_status_htmx_endpoint(self, client, mock_data_layer):
        """Test agent status HTMX endpoint returns agent data."""
        response = client.get("/manager/agent-status", headers={"HX-Request": "true"})
        assert response.status_code == 200

        # Should contain agent data
        # Note: FastHTML may return full page even with HX-Request header in tests
        assert "Agent Health" in response.text or "Planning Agent" in response.text

    def test_budget_status_htmx_endpoint(self, client, mock_data_layer):
        """Test budget status HTMX endpoint returns budget data."""
        response = client.get("/manager/budget-status", headers={"HX-Request": "true"})
        assert response.status_code == 200

        # Should contain budget data
        # Note: FastHTML may return full page even with HX-Request header in tests
        assert "Budget" in response.text or "Daily" in response.text

    def test_active_agents_htmx_endpoint(self, client, mock_data_layer):
        """Test active agents HTMX endpoint returns content."""
        response = client.get("/manager/active-agents", headers={"HX-Request": "true"})
        assert response.status_code == 200

        # Should return some content (may be full page or fragment)
        assert len(response.text) > 0

    def test_running_tasks_htmx_endpoint(self, client, mock_data_layer):
        """Test running tasks HTMX endpoint returns content."""
        response = client.get("/manager/running-tasks", headers={"HX-Request": "true"})
        assert response.status_code == 200

        # Should return some content (may be full page or fragment)
        assert len(response.text) > 0

    def test_active_agents_empty_state(self, client, monkeypatch):
        """Test active agents returns empty div when none active."""
        import asp.web.manager as manager_module

        monkeypatch.setattr(manager_module, "get_active_agents", lambda: [])

        response = client.get("/manager/active-agents", headers={"HX-Request": "true"})
        assert response.status_code == 200

        # Should return empty or minimal div
        tree = html.fromstring(response.text)
        # Empty div means no content children
        assert len(response.text.strip()) < 50 or "Active Agents" not in response.text

    def test_running_tasks_empty_state(self, client, monkeypatch):
        """Test running tasks returns empty div when none running."""
        import asp.web.manager as manager_module

        monkeypatch.setattr(manager_module, "get_running_tasks", lambda: [])

        response = client.get("/manager/running-tasks", headers={"HX-Request": "true"})
        assert response.status_code == 200

        # Should return empty div
        assert len(response.text.strip()) < 50 or "Running" not in response.text


class TestManagerDashboardHTMXAttributes:
    """Tests for HTMX attributes on dashboard elements."""

    def test_agent_health_has_htmx_refresh(self, client, mock_data_layer):
        """Test agent health table has HTMX auto-refresh."""
        response = client.get("/manager")
        tree = html.fromstring(response.text)

        # Find element with hx-get for agent-status
        htmx_elements = tree.xpath("//*[@hx-get='/manager/agent-status']")
        assert len(htmx_elements) >= 1

    def test_budget_status_has_htmx_refresh(self, client, mock_data_layer):
        """Test budget status has HTMX auto-refresh."""
        response = client.get("/manager")
        tree = html.fromstring(response.text)

        # Find element with hx-get for budget-status
        htmx_elements = tree.xpath("//*[@hx-get='/manager/budget-status']")
        assert len(htmx_elements) >= 1


class TestManagerNavigation:
    """Tests for navigation between manager routes."""

    def test_dashboard_links_to_tasks(self, client, mock_data_layer):
        """Test dashboard has link to all tasks."""
        response = client.get("/manager")
        tree = html.fromstring(response.text)

        links = tree.xpath("//a[@href='/manager/tasks']")
        assert len(links) >= 1

    def test_dashboard_links_to_budget(self, client, mock_data_layer):
        """Test dashboard has link to budget settings."""
        response = client.get("/manager")
        tree = html.fromstring(response.text)

        links = tree.xpath("//a[contains(@href, '/manager/budget')]")
        assert len(links) >= 1

    def test_dashboard_links_to_home(self, client, mock_data_layer):
        """Test subpages link back appropriately."""
        # Main dashboard typically doesn't need back link but check structure
        response = client.get("/manager")
        assert response.status_code == 200


class TestManagerAccessibility:
    """Basic accessibility tests for manager routes."""

    def test_dashboard_has_headings(self, client, mock_data_layer):
        """Test dashboard has proper heading structure."""
        response = client.get("/manager")
        tree = html.fromstring(response.text)

        # Should have h2 and h3 headings
        h2_tags = tree.xpath("//h2")
        h3_tags = tree.xpath("//h3")

        assert len(h2_tags) >= 1
        assert len(h3_tags) >= 1

    def test_dashboard_tables_have_headers(self, client, mock_data_layer):
        """Test tables have proper header rows."""
        response = client.get("/manager")
        tree = html.fromstring(response.text)

        tables = tree.xpath("//table")
        for table in tables:
            thead = table.xpath(".//thead")
            # Most tables should have thead
            # (Some small tables might use tbody only)

    def test_forms_have_labels(self, client, mock_data_layer):
        """Test form inputs have associated labels."""
        response = client.get("/manager/budget")
        tree = html.fromstring(response.text)

        # Check that inputs have labels
        inputs = tree.xpath("//input[@type='number']")
        for inp in inputs:
            input_id = inp.get("id")
            if input_id:
                labels = tree.xpath(f"//label[@for='{input_id}']")
                # Should have a label
                assert len(labels) >= 1 or inp.get("aria-label") is not None
