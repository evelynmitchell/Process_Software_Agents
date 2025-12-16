"""Tests for asp.web.kanban module (ADR 009 Phase 2)."""

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

from fasthtml.common import to_xml

from asp.utils.beads import BeadsIssue, BeadsStatus, BeadsType, write_issues


def render_html(component):
    """Render a FastHTML component to HTML string."""
    return to_xml(component)


class TestIssueCard:
    """Tests for IssueCard component."""

    def test_renders_basic_card(self):
        """IssueCard renders basic issue information."""
        from asp.web.kanban import IssueCard

        issue = BeadsIssue(
            id="bd-test123",
            title="Test Issue",
            description="Test description",
            type=BeadsType.TASK,
            priority=2,
            labels=["test"],
        )

        # IssueCard returns a Div component
        card = IssueCard(issue)

        # Check it's a Div with the right ID
        assert card.tag == "div"
        assert card.attrs.get("id") == "card-bd-test123"

    def test_card_has_plan_button_for_open_issues(self):
        """Open issues should have Plan with ASP button."""
        from asp.web.kanban import IssueCard

        issue = BeadsIssue(
            id="bd-open123",
            title="Open Issue",
            status=BeadsStatus.OPEN,
        )

        card = IssueCard(issue, show_plan_button=True)

        # Convert to string to check for button
        card_html = render_html(card)
        assert "Plan with ASP" in card_html
        assert 'hx-post="/kanban/process/bd-open123"' in card_html

    def test_card_no_button_for_in_progress(self):
        """IN_PROGRESS issues should not have Plan button."""
        from asp.web.kanban import IssueCard

        issue = BeadsIssue(
            id="bd-prog123",
            title="In Progress Issue",
            status=BeadsStatus.IN_PROGRESS,
        )

        card = IssueCard(issue, show_plan_button=True)
        card_html = render_html(card)

        assert "Plan with ASP" not in card_html

    def test_card_no_button_for_closed(self):
        """CLOSED issues should not have Plan button."""
        from asp.web.kanban import IssueCard

        issue = BeadsIssue(
            id="bd-closed",
            title="Closed Issue",
            status=BeadsStatus.CLOSED,
        )

        card = IssueCard(issue, show_plan_button=True)
        card_html = render_html(card)

        assert "Plan with ASP" not in card_html

    def test_card_respects_show_plan_button_false(self):
        """show_plan_button=False disables button."""
        from asp.web.kanban import IssueCard

        issue = BeadsIssue(
            id="bd-nobutton",
            title="No Button Issue",
            status=BeadsStatus.OPEN,
        )

        card = IssueCard(issue, show_plan_button=False)
        card_html = render_html(card)

        assert "Plan with ASP" not in card_html

    def test_card_shows_priority_border(self):
        """Card should have priority-based border color."""
        from asp.web.kanban import IssueCard

        issue = BeadsIssue(
            id="bd-high",
            title="High Priority",
            priority=0,
        )

        card = IssueCard(issue)
        card_html = render_html(card)

        # Priority 0 = red (#ef4444)
        assert "#ef4444" in card_html

    def test_card_shows_labels(self):
        """Card should display issue labels."""
        from asp.web.kanban import IssueCard

        issue = BeadsIssue(
            id="bd-labels",
            title="Issue with Labels",
            labels=["bug", "urgent", "frontend"],
        )

        card = IssueCard(issue)
        card_html = render_html(card)

        assert "bug" in card_html
        assert "urgent" in card_html
        assert "frontend" in card_html


class TestKanbanColumn:
    """Tests for KanbanColumn component."""

    def test_renders_column_with_issues(self):
        """KanbanColumn renders issues of correct status."""
        from asp.web.kanban import KanbanColumn

        issues = [
            BeadsIssue(id="bd-1", title="Open 1", status=BeadsStatus.OPEN),
            BeadsIssue(id="bd-2", title="Open 2", status=BeadsStatus.OPEN),
            BeadsIssue(id="bd-3", title="Done", status=BeadsStatus.CLOSED),
        ]

        column = KanbanColumn(BeadsStatus.OPEN, "Todo", issues)
        column_html = render_html(column)

        # Should show count
        assert "Todo (2)" in column_html
        # Should contain open issues
        assert "bd-1" in column_html
        assert "bd-2" in column_html
        # Should NOT contain closed issue
        assert "bd-3" not in column_html


class TestKanbanBoard:
    """Tests for KanbanBoard component."""

    def test_renders_all_columns(self):
        """KanbanBoard renders all three columns."""
        from asp.web.kanban import KanbanBoard

        with tempfile.TemporaryDirectory() as tmpdir:
            # Create empty issues file
            write_issues([], Path(tmpdir))

            with patch("asp.web.kanban.read_issues") as mock_read:
                mock_read.return_value = []
                board = KanbanBoard()

        board_html = render_html(board)

        assert "Todo" in board_html
        assert "In Progress" in board_html
        assert "Done" in board_html


class TestPlanSuccessCard:
    """Tests for PlanSuccessCard component."""

    def test_shows_plan_summary(self):
        """Success card shows plan summary."""
        from asp.models.planning import ProjectPlan, SemanticUnit
        from asp.web.kanban import PlanSuccessCard

        issue = BeadsIssue(
            id="bd-success",
            title="Success Issue",
            status=BeadsStatus.IN_PROGRESS,
        )

        plan = ProjectPlan(
            task_id="bd-success",
            semantic_units=[
                SemanticUnit(
                    unit_id="su-a000001",
                    description="First semantic unit for testing",
                    api_interactions=1,
                    data_transformations=1,
                    logical_branches=1,
                    code_entities_modified=1,
                    novelty_multiplier=1.0,
                    est_complexity=10,
                ),
                SemanticUnit(
                    unit_id="su-b000002",
                    description="Second semantic unit for testing",
                    api_interactions=1,
                    data_transformations=1,
                    logical_branches=1,
                    code_entities_modified=1,
                    novelty_multiplier=1.0,
                    est_complexity=15,
                ),
            ],
            total_est_complexity=25,
        )

        card = PlanSuccessCard(issue, plan)
        card_html = render_html(card)

        assert "Plan created" in card_html
        assert "2 units" in card_html
        assert "C=25" in card_html
        assert "su-a000001" in card_html
        assert "su-b000002" in card_html

    def test_shows_more_text_for_many_units(self):
        """Success card shows '... and N more' for many units."""
        from asp.models.planning import ProjectPlan, SemanticUnit
        from asp.web.kanban import PlanSuccessCard

        issue = BeadsIssue(id="bd-many", title="Many Units")

        # Generate valid unit IDs (su-{7 hex chars})
        units = [
            SemanticUnit(
                unit_id=f"su-{i:07x}",  # Generates su-0000000, su-0000001, etc.
                description=f"Semantic unit number {i} for testing purposes",
                api_interactions=1,
                data_transformations=1,
                logical_branches=1,
                code_entities_modified=1,
                novelty_multiplier=1.0,
                est_complexity=10,
            )
            for i in range(5)
        ]

        plan = ProjectPlan(
            task_id="bd-many",
            semantic_units=units,
            total_est_complexity=50,
        )

        card = PlanSuccessCard(issue, plan)
        card_html = render_html(card)

        assert "5 units" in card_html
        assert "and 2 more" in card_html


class TestPlanErrorCard:
    """Tests for PlanErrorCard component."""

    def test_shows_error_message(self):
        """Error card shows error message and retry button."""
        from asp.web.kanban import PlanErrorCard

        issue = BeadsIssue(
            id="bd-error",
            title="Failed Issue",
        )

        card = PlanErrorCard(issue, "API rate limit exceeded")
        card_html = render_html(card)

        assert "Planning failed" in card_html
        assert "API rate limit exceeded" in card_html
        assert "Retry" in card_html
        assert 'hx-post="/kanban/process/bd-error"' in card_html


class TestProcessIssueEndpoint:
    """Tests for /kanban/process/{issue_id} endpoint."""

    @patch("asp.web.kanban.read_issues")
    def test_returns_error_for_missing_issue(self, mock_read):
        """Endpoint returns error for non-existent issue."""
        import asyncio

        from asp.web.kanban import kanban_routes

        mock_read.return_value = []

        # Create mock app
        mock_app = MagicMock()
        routes = {}

        def mock_post(path):
            def decorator(func):
                routes[path] = func
                return func

            return decorator

        mock_app.post = mock_post
        mock_app.get = lambda path: lambda func: func

        kanban_routes(mock_app)

        # Call the endpoint
        process_func = routes["/kanban/process/{issue_id}"]
        result = asyncio.run(process_func("bd-notfound"))

        result_html = render_html(result)
        assert "not found" in result_html

    @patch("asp.web.kanban.write_issues")
    @patch("asp.web.kanban.read_issues")
    @patch("asp.agents.planning_agent.PlanningAgent")
    def test_processes_issue_successfully(
        self, mock_agent_class, mock_read, mock_write
    ):
        """Endpoint processes issue and returns success card."""
        import asyncio

        from asp.models.planning import ProjectPlan, SemanticUnit
        from asp.web.kanban import kanban_routes

        issue = BeadsIssue(
            id="bd-process",
            title="Process This",
            description="Test processing description",
            status=BeadsStatus.OPEN,
        )
        mock_read.return_value = [issue]

        # Mock planning agent
        mock_agent = MagicMock()
        mock_agent.create_plan.return_value = ProjectPlan(
            task_id="bd-process",
            semantic_units=[
                SemanticUnit(
                    unit_id="su-a123456",
                    description="Test semantic unit for testing purposes",
                    api_interactions=1,
                    data_transformations=1,
                    logical_branches=1,
                    code_entities_modified=1,
                    novelty_multiplier=1.0,
                    est_complexity=10,
                ),
            ],
            total_est_complexity=10,
        )
        mock_agent_class.return_value = mock_agent

        # Create mock app
        mock_app = MagicMock()
        routes = {}

        def mock_post(path):
            def decorator(func):
                routes[path] = func
                return func

            return decorator

        mock_app.post = mock_post
        mock_app.get = lambda path: lambda func: func

        kanban_routes(mock_app)

        # Call the endpoint
        process_func = routes["/kanban/process/{issue_id}"]
        result = asyncio.run(process_func("bd-process"))

        result_html = render_html(result)
        assert "Plan created" in result_html
        assert "1 units" in result_html

        # Verify issue status was updated
        assert issue.status == BeadsStatus.IN_PROGRESS
        mock_write.assert_called_once()

    @patch("asp.web.kanban.read_issues")
    @patch("asp.agents.planning_agent.PlanningAgent")
    def test_handles_planning_error(self, mock_agent_class, mock_read):
        """Endpoint returns error card on planning failure."""
        import asyncio

        from asp.web.kanban import kanban_routes

        issue = BeadsIssue(
            id="bd-fail",
            title="This issue will fail during planning",
            description="This is a test failure case that should trigger an error message",
            status=BeadsStatus.OPEN,
        )
        mock_read.return_value = [issue]

        # Mock agent to raise exception
        mock_agent = MagicMock()
        mock_agent.create_plan.side_effect = Exception("LLM connection failed")
        mock_agent_class.return_value = mock_agent

        # Create mock app
        mock_app = MagicMock()
        routes = {}

        def mock_post(path):
            def decorator(func):
                routes[path] = func
                return func

            return decorator

        mock_app.post = mock_post
        mock_app.get = lambda path: lambda func: func

        kanban_routes(mock_app)

        # Call the endpoint
        process_func = routes["/kanban/process/{issue_id}"]
        result = asyncio.run(process_func("bd-fail"))

        result_html = render_html(result)
        assert "Planning failed" in result_html
        assert "LLM connection failed" in result_html
