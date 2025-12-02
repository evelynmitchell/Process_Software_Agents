"""
Playwright E2E tests for the ASP Web UI.

Tests the FastHTML-based web interface including:
- Home page with persona selection
- Developer dashboard with dynamic content
- Manager dashboard
- Product dashboard
- Navigation between pages
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

        # Check for main heading
        expect(page.get_by_role("heading", name="ASP Overwatch")).to_be_visible()

    def test_persona_buttons_present(self, page: Page, web_server: str) -> None:
        """Test that all persona buttons are present."""
        page.goto(web_server)

        # Check for all three persona headings within links
        expect(page.locator("a[href='/manager'] h3")).to_be_visible()
        expect(page.locator("a[href='/developer'] h3")).to_be_visible()
        expect(page.locator("a[href='/product'] h3")).to_be_visible()

    def test_developer_link_navigates(self, page: Page, web_server: str) -> None:
        """Test that clicking Developer link navigates to developer dashboard."""
        page.goto(web_server)

        # Click on Developer persona link
        page.locator("a[href='/developer']").click()

        # Should navigate to developer page
        expect(page).to_have_url(re.compile("/developer"))

    def test_manager_link_navigates(self, page: Page, web_server: str) -> None:
        """Test that clicking Manager link navigates to manager dashboard."""
        page.goto(web_server)

        # Click on Manager persona link
        page.locator("a[href='/manager']").click()

        # Should navigate to manager page
        expect(page).to_have_url(re.compile("/manager"))

    def test_product_link_navigates(self, page: Page, web_server: str) -> None:
        """Test that clicking Product link navigates to product dashboard."""
        page.goto(web_server)

        # Click on Product persona link
        page.locator("a[href='/product']").click()

        # Should navigate to product page
        expect(page).to_have_url(re.compile("/product"))


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
        expect(page.get_by_role("heading", name="Recent Completed")).to_be_visible()
        expect(page.get_by_role("heading", name="Tools")).to_be_visible()

    def test_main_content_sections(self, page: Page, web_server: str) -> None:
        """Test that main content sections are present."""
        page.goto(f"{web_server}/developer")

        # Check for main sections
        expect(page.get_by_role("heading", name="Defect Overview")).to_be_visible()
        expect(page.get_by_role("heading", name="Recent Activity")).to_be_visible()

    def test_tools_links_present(self, page: Page, web_server: str) -> None:
        """Test that tools links are present in sidebar."""
        page.goto(f"{web_server}/developer")

        expect(page.get_by_role("link", name="View All Tasks")).to_be_visible()
        expect(page.get_by_role("link", name="Agent Stats")).to_be_visible()

    def test_back_to_home_link(self, page: Page, web_server: str) -> None:
        """Test navigation back to home."""
        page.goto(f"{web_server}/developer")

        page.locator("a[href='/']").click()
        expect(page).to_have_url(f"{web_server}/")


class TestDeveloperNavigation:
    """Tests for navigation within the Developer persona."""

    def test_all_tasks_page(self, page: Page, web_server: str) -> None:
        """Test navigating to all tasks page."""
        page.goto(f"{web_server}/developer")

        page.get_by_role("link", name="View All Tasks").click()

        expect(page).to_have_url(re.compile("/developer/tasks"))
        expect(
            page.get_by_role("heading", name="All Tasks", exact=True)
        ).to_be_visible()

    def test_stats_page(self, page: Page, web_server: str) -> None:
        """Test navigating to stats page."""
        page.goto(f"{web_server}/developer")

        page.get_by_role("link", name="Agent Stats").click()

        expect(page).to_have_url(re.compile("/developer/stats"))
        expect(
            page.get_by_role("heading", name="Agent Performance Statistics")
        ).to_be_visible()

    def test_back_to_dashboard_from_tasks(self, page: Page, web_server: str) -> None:
        """Test navigating back to dashboard from tasks page."""
        page.goto(f"{web_server}/developer/tasks")

        page.get_by_role("link", name=re.compile("Back to Dashboard")).click()

        expect(page).to_have_url(re.compile("/developer$"))

    def test_back_to_dashboard_from_stats(self, page: Page, web_server: str) -> None:
        """Test navigating back to dashboard from stats page."""
        page.goto(f"{web_server}/developer/stats")

        page.get_by_role("link", name=re.compile("Back to Dashboard")).click()

        expect(page).to_have_url(re.compile("/developer$"))


class TestManagerDashboard:
    """Tests for the Manager (Sarah) dashboard."""

    def test_manager_page_loads(self, page: Page, web_server: str) -> None:
        """Test that the manager dashboard loads successfully."""
        page.goto(f"{web_server}/manager")

        expect(page).to_have_title(re.compile("ASP Overwatch"))

    def test_system_overview_visible(self, page: Page, web_server: str) -> None:
        """Test that system overview section is visible."""
        page.goto(f"{web_server}/manager")

        expect(page.get_by_role("heading", name="System Overview")).to_be_visible()

    def test_agent_health_visible(self, page: Page, web_server: str) -> None:
        """Test that agent health section is visible."""
        page.goto(f"{web_server}/manager")

        expect(page.get_by_role("heading", name="Agent Health")).to_be_visible()

    def test_quality_gates_visible(self, page: Page, web_server: str) -> None:
        """Test that quality gates section is visible."""
        page.goto(f"{web_server}/manager")

        expect(page.get_by_role("heading", name="Quality Gates")).to_be_visible()


class TestProductDashboard:
    """Tests for the Product Manager (Jordan) dashboard."""

    def test_product_page_loads(self, page: Page, web_server: str) -> None:
        """Test that the product dashboard loads successfully."""
        page.goto(f"{web_server}/product")

        expect(page).to_have_title(re.compile("Project Overview"))

    def test_delivery_dashboard_visible(self, page: Page, web_server: str) -> None:
        """Test that delivery dashboard section is visible."""
        page.goto(f"{web_server}/product")

        expect(page.get_by_role("heading", name="Delivery Dashboard")).to_be_visible()

    def test_task_pipeline_visible(self, page: Page, web_server: str) -> None:
        """Test that task pipeline section is visible."""
        page.goto(f"{web_server}/product")

        expect(page.get_by_role("heading", name="Task Pipeline")).to_be_visible()


class TestHealthEndpoint:
    """Tests for the health check endpoint."""

    def test_health_endpoint(self, page: Page, web_server: str) -> None:
        """Test that health endpoint returns healthy status."""
        response = page.request.get(f"{web_server}/health")
        assert response.ok
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "asp-web-ui"


class TestResponsiveness:
    """Tests for basic responsiveness and layout."""

    def test_mobile_viewport(self, page: Page, web_server: str) -> None:
        """Test that page works on mobile viewport."""
        page.set_viewport_size({"width": 375, "height": 667})
        page.goto(f"{web_server}/developer")

        # Main elements should still be visible (may be stacked)
        expect(page.get_by_role("heading", name="Active Tasks")).to_be_visible()

    def test_tablet_viewport(self, page: Page, web_server: str) -> None:
        """Test that page works on tablet viewport."""
        page.set_viewport_size({"width": 768, "height": 1024})
        page.goto(f"{web_server}/developer")

        # Main elements should still be visible
        expect(page.get_by_role("heading", name="Active Tasks")).to_be_visible()
