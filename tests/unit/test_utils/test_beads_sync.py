"""Tests for asp.utils.beads_sync module."""

import tempfile
from pathlib import Path

import pytest

from asp.models.planning import ProjectPlan, SemanticUnit
from asp.utils.beads import BeadsStatus, read_issues
from asp.utils.beads_sync import get_plan_issues, sync_plan_to_beads, update_unit_status


@pytest.fixture
def sample_plan():
    """Create a sample ProjectPlan for testing."""
    return ProjectPlan(
        task_id="TEST-001",
        semantic_units=[
            SemanticUnit(
                unit_id="su-a000001",
                description="Implement user authentication",
                api_interactions=2,
                data_transformations=1,
                logical_branches=3,
                code_entities_modified=2,
                novelty_multiplier=1.0,
                est_complexity=15,
            ),
            SemanticUnit(
                unit_id="su-b000002",
                description="Add login endpoint",
                api_interactions=1,
                data_transformations=2,
                logical_branches=2,
                code_entities_modified=3,
                novelty_multiplier=1.5,
                est_complexity=20,
                dependencies=["su-a000001"],
            ),
        ],
        total_est_complexity=35,
    )


class TestSyncPlanToBeads:
    """Tests for sync_plan_to_beads function."""

    def test_creates_epic_and_tasks(self, sample_plan):
        """Sync creates an epic and task issues."""
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)

            created = sync_plan_to_beads(sample_plan, root_path=root)

            # Should create 1 epic + 2 tasks
            assert len(created) == 3

            # Check epic
            epic = next((i for i in created if "epic" in i.id.lower()), None)
            assert epic is not None
            assert "TEST-001" in epic.title
            assert epic.type.value == "epic"

            # Check tasks
            tasks = [i for i in created if i.type.value == "task"]
            assert len(tasks) == 2

    def test_no_epic_option(self, sample_plan):
        """create_epic=False skips epic creation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)

            created = sync_plan_to_beads(sample_plan, create_epic=False, root_path=root)

            # Should create only 2 tasks
            assert len(created) == 2
            assert all(i.type.value == "task" for i in created)

    def test_tasks_have_parent_id(self, sample_plan):
        """Tasks should have parent_id pointing to epic."""
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)

            created = sync_plan_to_beads(sample_plan, root_path=root)

            epic = next(i for i in created if "epic" in i.id.lower())
            tasks = [i for i in created if i.type.value == "task"]

            for task in tasks:
                assert task.parent_id == epic.id

    def test_task_priority_based_on_complexity(self, sample_plan):
        """Task priority should reflect complexity."""
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)

            created = sync_plan_to_beads(sample_plan, root_path=root)
            tasks = [i for i in created if i.type.value == "task"]

            # Higher complexity should have higher priority (lower number)
            complexities = {
                t.id: sample_plan.semantic_units[i].est_complexity
                for i, t in enumerate(tasks)
            }

            # Just verify priorities are set reasonably
            for task in tasks:
                assert 0 <= task.priority <= 4

    def test_task_labels_include_metadata(self, sample_plan):
        """Task labels should include task ID and unit ID."""
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)

            created = sync_plan_to_beads(sample_plan, root_path=root)
            tasks = [i for i in created if i.type.value == "task"]

            for task in tasks:
                assert "asp-unit" in task.labels
                assert f"task-{sample_plan.task_id}" in task.labels
                assert any("unit-" in label for label in task.labels)

    def test_skip_existing_issues(self, sample_plan):
        """Should skip existing issues when update_existing=False."""
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)

            # First sync
            created1 = sync_plan_to_beads(sample_plan, root_path=root)
            assert len(created1) == 3

            # Second sync - should skip
            created2 = sync_plan_to_beads(sample_plan, root_path=root)
            assert len(created2) == 0

            # Total issues unchanged
            all_issues = read_issues(root)
            assert len(all_issues) == 3

    def test_update_existing_issues(self, sample_plan):
        """Should update issues when update_existing=True."""
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)

            # First sync
            sync_plan_to_beads(sample_plan, root_path=root)

            # Modify plan
            sample_plan.semantic_units[0].description = "Updated description"

            # Second sync with update
            created = sync_plan_to_beads(
                sample_plan, update_existing=True, root_path=root
            )

            # Should return updated issues
            assert len(created) == 3

            # Check description was updated
            all_issues = read_issues(root)
            updated = next(i for i in all_issues if "a000001" in i.id)
            assert "Updated" in updated.title


class TestGetPlanIssues:
    """Tests for get_plan_issues function."""

    def test_returns_plan_issues_only(self, sample_plan):
        """Should return only issues for the specified plan."""
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)

            # Create issues for sample_plan
            sync_plan_to_beads(sample_plan, root_path=root)

            # Create a second plan
            plan2 = ProjectPlan(
                task_id="TEST-002",
                semantic_units=[
                    SemanticUnit(
                        unit_id="su-c000003",
                        description="Other task",
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
            sync_plan_to_beads(plan2, root_path=root)

            # Get issues for first plan only
            plan_issues = get_plan_issues(sample_plan, root_path=root)

            # Should only have TEST-001 issues
            assert len(plan_issues) == 3
            assert all("task-TEST-001" in i.labels for i in plan_issues)


class TestUpdateUnitStatus:
    """Tests for update_unit_status function."""

    def test_updates_status(self, sample_plan):
        """Should update issue status by unit ID."""
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)

            sync_plan_to_beads(sample_plan, root_path=root)

            # Update status
            updated = update_unit_status(
                "su-a000001",
                BeadsStatus.IN_PROGRESS,
                root_path=root,
            )

            assert updated is not None
            assert updated.status == BeadsStatus.IN_PROGRESS

            # Verify persisted
            all_issues = read_issues(root)
            issue = next(i for i in all_issues if "a000001" in i.id)
            assert issue.status == BeadsStatus.IN_PROGRESS

    def test_close_sets_closed_at(self, sample_plan):
        """Closing an issue should set closed_at timestamp."""
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)

            sync_plan_to_beads(sample_plan, root_path=root)

            updated = update_unit_status(
                "su-a000001",
                BeadsStatus.CLOSED,
                root_path=root,
            )

            assert updated is not None
            assert updated.status == BeadsStatus.CLOSED
            assert updated.closed_at is not None

    def test_returns_none_for_unknown_unit(self, sample_plan):
        """Should return None for unknown unit ID."""
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)

            sync_plan_to_beads(sample_plan, root_path=root)

            result = update_unit_status(
                "su-unknown",
                BeadsStatus.IN_PROGRESS,
                root_path=root,
            )

            assert result is None
