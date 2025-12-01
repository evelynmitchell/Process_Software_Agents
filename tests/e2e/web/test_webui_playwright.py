"""
Playwright E2E tests for the ASP Web UI.

Tests the FastHTML-based web interface including:
- Home page with persona selection
- Developer dashboard with dynamic content
- Navigation between pages
- HTMX dynamic updates
"""

import re

from playwright.sync_api import Page, expect


class TestHomePage:
    """Tests for the home page (persona selection)."""

    def test_home_page_loads(self, page: Page, web_server: str) -> None:
        """Test that the home page loads successfully."""
        page.goto(web_server)

        # Check page title
        expect(page).to_have_title(re.compile("ASP Platform"))

        # Check for persona selection heading
        expect(page.get_by_role("heading", name="Select Persona")).to_be_visible()

    def test_persona_buttons_present(self, page: Page, web_server: str) -> None:
        """Test that all persona buttons are present."""
        page.goto(web_server)

        # Check for all three persona buttons
        expect(
            page.get_by_role("link", name=re.compile("Sarah.*Manager"))
        ).to_be_visible()
        expect(
            page.get_by_role("link", name=re.compile("Alex.*Developer"))
        ).to_be_visible()
        expect(
            page.get_by_role("link", name=re.compile("Jordan.*Product"))
        ).to_be_visible()

    def test_developer_link_navigates(self, page: Page, web_server: str) -> None:
        """Test that clicking Developer link navigates to developer dashboard."""
        page.goto(web_server)

        # Click on Developer persona
        page.get_by_role("link", name=re.compile("Alex.*Developer")).click()

        # Should navigate to developer page
        expect(page).to_have_url(re.compile("/developer"))


class TestDeveloperDashboard:
    """Tests for the Developer (Alex) dashboard."""

    def test_developer_page_loads(self, page: Page, web_server: str) -> None:
        """Test that the developer dashboard loads successfully."""
        page.goto(f"{web_server}/developer")

        # Check page title
        expect(page).to_have_title(re.compile("Flow State Canvas"))

    def test_sidebar_sections_visible(self, page: Page, web_server: str) -> None:
        """Test that sidebar sections are visible."""
        page.goto(f"{web_server}/developer")

        # Check sidebar headings
        expect(page.get_by_role("heading", name="Active Tasks")).to_be_visible()
        expect(page.get_by_role("heading", name="Agent Stats")).to_be_visible()
        expect(page.get_by_role("heading", name="Tools")).to_be_visible()

    def test_main_content_sections(self, page: Page, web_server: str) -> None:
        """Test that main content sections are present."""
        page.goto(f"{web_server}/developer")

        # Check for main sections
        expect(page.get_by_role("heading", name="Dashboard")).to_be_visible()
        expect(page.get_by_role("heading", name="Recent Activity")).to_be_visible()
        expect(page.get_by_role("heading", name="Defect Overview")).to_be_visible()

    def test_htmx_tasks_load(self, page: Page, web_server: str) -> None:
        """Test that tasks load dynamically via HTMX."""
        page.goto(f"{web_server}/developer")

        # Wait for HTMX to load tasks (demo data)
        # Look for task IDs that match the demo pattern
        expect(page.locator("text=TSP-DEMO")).to_be_visible(timeout=5000)

    def test_htmx_activity_table_loads(self, page: Page, web_server: str) -> None:
        """Test that activity table loads dynamically."""
        page.goto(f"{web_server}/developer")

        # Wait for activity table to load
        # Should have table headers
        expect(page.locator("th:text('Time')")).to_be_visible(timeout=5000)
        expect(page.locator("th:text('Agent')")).to_be_visible()
        expect(page.locator("th:text('Metric')")).to_be_visible()

    def test_htmx_agent_stats_load(self, page: Page, web_server: str) -> None:
        """Test that agent stats load dynamically."""
        page.goto(f"{web_server}/developer")

        # Wait for agent stats to load (demo data has these agents)
        # At least one agent should be visible
        expect(
            page.locator("text=Planning").or_(page.locator("text=Design"))
        ).to_be_visible(timeout=5000)

    def test_htmx_defect_summary_loads(self, page: Page, web_server: str) -> None:
        """Test that defect summary loads dynamically."""
        page.goto(f"{web_server}/developer")

        # Wait for defect summary to load
        expect(page.locator("text=Total defects")).to_be_visible(timeout=5000)

    def test_tools_links_present(self, page: Page, web_server: str) -> None:
        """Test that tools links are present in sidebar."""
        page.goto(f"{web_server}/developer")

        expect(page.get_by_role("link", name="New Task")).to_be_visible()
        expect(page.get_by_role("link", name="View Defects")).to_be_visible()


class TestDeveloperNavigation:
    """Tests for navigation within the Developer persona."""

    def test_task_detail_navigation(self, page: Page, web_server: str) -> None:
        """Test navigating to a task detail page."""
        page.goto(f"{web_server}/developer")

        # Wait for tasks to load and click on one
        page.locator("a[href*='/developer/task/']").first.click()

        # Should be on task detail page
        expect(page).to_have_url(re.compile("/developer/task/"))
        expect(
            page.get_by_role("heading", name=re.compile("Task Details"))
        ).to_be_visible()

    def test_back_to_dashboard_from_task(self, page: Page, web_server: str) -> None:
        """Test navigating back to dashboard from task detail."""
        page.goto(f"{web_server}/developer/task/TSP-DEMO-001")

        # Click back link
        page.get_by_role("link", name=re.compile("Back to Dashboard")).click()

        # Should be back on developer dashboard
        expect(page).to_have_url(re.compile("/developer$"))

    def test_defects_page_navigation(self, page: Page, web_server: str) -> None:
        """Test navigating to defects page."""
        page.goto(f"{web_server}/developer")

        # Click View Defects
        page.get_by_role("link", name="View Defects").click()

        # Should be on defects page
        expect(page).to_have_url(re.compile("/developer/defects"))
        expect(page.get_by_role("heading", name="Recent Defects")).to_be_visible()

    def test_new_task_form_navigation(self, page: Page, web_server: str) -> None:
        """Test navigating to new task form."""
        page.goto(f"{web_server}/developer")

        # Click New Task
        page.get_by_role("link", name="New Task").click()

        # Should be on new task page
        expect(page).to_have_url(re.compile("/developer/new-task"))
        expect(page.get_by_role("heading", name="Create New Task")).to_be_visible()


class TestNewTaskForm:
    """Tests for the new task creation form."""

    def test_form_fields_present(self, page: Page, web_server: str) -> None:
        """Test that form fields are present."""
        page.goto(f"{web_server}/developer/new-task")

        # Check for form fields
        expect(page.locator("input[name='task_id']")).to_be_visible()
        expect(page.locator("textarea[name='description']")).to_be_visible()
        expect(page.get_by_role("button", name="Create Task")).to_be_visible()

    def test_form_submission(self, page: Page, web_server: str) -> None:
        """Test form submission creates task."""
        page.goto(f"{web_server}/developer/new-task")

        # Fill form
        page.locator("input[name='task_id']").fill("TSP-TEST-001")
        page.locator("textarea[name='description']").fill("Test task description")

        # Submit
        page.get_by_role("button", name="Create Task").click()

        # Should see success message
        expect(
            page.get_by_role("heading", name="Task Created Successfully")
        ).to_be_visible()
        expect(page.locator("text=TSP-TEST-001")).to_be_visible()


class TestDefectsPage:
    """Tests for the defects list page."""

    def test_defects_table_present(self, page: Page, web_server: str) -> None:
        """Test that defects table is present with correct headers."""
        page.goto(f"{web_server}/developer/defects")

        # Check table headers
        expect(page.locator("th:text('ID')")).to_be_visible()
        expect(page.locator("th:text('Severity')")).to_be_visible()
        expect(page.locator("th:text('Type')")).to_be_visible()
        expect(page.locator("th:text('Description')")).to_be_visible()

    def test_defects_data_displayed(self, page: Page, web_server: str) -> None:
        """Test that defect data is displayed."""
        page.goto(f"{web_server}/developer/defects")

        # Demo data should be visible (at least one defect)
        expect(page.locator("text=DEFECT-")).to_be_visible()


class TestResponsiveness:
    """Tests for basic responsiveness and layout."""

    def test_mobile_viewport(self, page: Page, web_server: str) -> None:
        """Test that page works on mobile viewport."""
        page.set_viewport_size({"width": 375, "height": 667})
        page.goto(f"{web_server}/developer")

        # Main elements should still be visible
        expect(page.get_by_role("heading", name="Dashboard")).to_be_visible()

    def test_tablet_viewport(self, page: Page, web_server: str) -> None:
        """Test that page works on tablet viewport."""
        page.set_viewport_size({"width": 768, "height": 1024})
        page.goto(f"{web_server}/developer")

        # Main elements should still be visible
        expect(page.get_by_role("heading", name="Active Tasks")).to_be_visible()
        expect(page.get_by_role("heading", name="Dashboard")).to_be_visible()
