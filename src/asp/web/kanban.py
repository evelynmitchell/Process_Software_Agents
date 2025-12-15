"""
Kanban Board UI Route

This module provides a Kanban board view for Beads issues.
"""

from fasthtml.common import *
from asp.utils.beads import read_issues, BeadsStatus, BeadsType

# Define column mapping
COLUMNS = {
    BeadsStatus.OPEN: "Todo",
    BeadsStatus.IN_PROGRESS: "In Progress",
    BeadsStatus.CLOSED: "Done",
}

def IssueCard(issue):
    """
    Renders a single issue card.
    """
    # Use actual color values for inline styles (Tailwind dynamic classes don't work)
    priority_colors = {
        0: "#ef4444",  # red-500 - Highest
        1: "#f97316",  # orange-500
        2: "#eab308",  # yellow-500
        3: "#3b82f6",  # blue-500
        4: "#6b7280",  # gray-500 - Lowest
    }
    border_color = priority_colors.get(issue.priority, "#6b7280")

    return Div(
        Div(
            Span(f"#{issue.id}", cls="text-xs font-mono text-gray-500"),
            Span(issue.type.value, cls="text-xs px-1 rounded bg-gray-200 text-gray-700 ml-2"),
            cls="flex justify-between items-center mb-1"
        ),
        H4(issue.title, cls="text-sm font-semibold mb-1"),
        P(issue.description or "", cls="text-xs text-gray-600 line-clamp-3"),
        Div(
            *[Span(label, cls="text-[10px] bg-blue-100 text-blue-800 px-1 rounded mr-1") for label in issue.labels],
            cls="mt-2 flex flex-wrap"
        ),
        cls="bg-white p-3 rounded shadow border-l-4 mb-3 hover:shadow-md transition-shadow",
        style=f"border-left-color: {border_color};"
    )

def KanbanColumn(status, title, issues):
    """
    Renders a single Kanban column.
    """
    column_issues = [i for i in issues if i.status == status]
    return Div(
        H3(f"{title} ({len(column_issues)})", cls="font-bold text-gray-700 mb-3"),
        Div(
            *[IssueCard(i) for i in column_issues],
            cls="space-y-2 min-h-[200px]"
        ),
        cls="bg-gray-100 p-4 rounded-lg w-1/3 min-w-[300px] flex-shrink-0"
    )

def KanbanBoard():
    """
    Renders the full Kanban board.
    """
    issues = read_issues()
    return Div(
        Div(
            H1("Beads Kanban", cls="text-2xl font-bold text-gray-800"),
            A("Refresh", href="/kanban", cls="text-sm text-blue-600 hover:underline"),
            cls="flex justify-between items-center mb-6"
        ),
        Div(
            KanbanColumn(BeadsStatus.OPEN, "Todo", issues),
            KanbanColumn(BeadsStatus.IN_PROGRESS, "In Progress", issues),
            KanbanColumn(BeadsStatus.CLOSED, "Done", issues),
            cls="flex gap-4 overflow-x-auto pb-4"
        ),
        cls="p-6 h-full"
    )

def kanban_routes(app):
    @app.get("/kanban")
    def get_kanban():
        return Title("Beads Kanban"), KanbanBoard()
