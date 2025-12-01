"""
Unit tests for Cycle Tracker.

Tests improvement cycle tracking, metrics calculation, and impact measurement.

Author: ASP Development Team
Date: November 25, 2025
"""

from datetime import datetime, timedelta
from pathlib import Path

import pytest

from asp.models.postmortem import ProcessImprovementProposal, ProposedChange
from asp.telemetry.cycle_tracker import CycleEvent, CycleTracker, ImprovementCycle


@pytest.fixture
def cycles_dir(tmp_path):
    """Create temporary cycles directory."""
    cycles_dir = tmp_path / "artifacts" / "improvement_cycles"
    cycles_dir.mkdir(parents=True)
    return cycles_dir


@pytest.fixture
def sample_pip():
    """Create sample PIP for testing."""
    return ProcessImprovementProposal(
        proposal_id="PIP-001",
        task_id="TASK-001",
        created_at=datetime(2025, 11, 25, 10, 0, 0),
        analysis="Security vulnerabilities found",
        proposed_changes=[
            ProposedChange(
                target_artifact="code_agent_prompt",
                change_type="add",
                proposed_content="Use parameterized queries",
                rationale="Prevent SQL injection",
            )
        ],
        expected_impact="Reduce security defects by 70%",
        hitl_status="pending",
    )


@pytest.fixture
def approved_pip(sample_pip):
    """Create approved PIP for testing."""
    sample_pip.hitl_status = "approved"
    sample_pip.hitl_reviewer = "security@example.com"
    sample_pip.hitl_reviewed_at = datetime(2025, 11, 25, 11, 0, 0)
    sample_pip.hitl_feedback = "Approved - security critical"
    return sample_pip


class TestImprovementCycle:
    """Test ImprovementCycle model."""

    def test_review_cycle_time(self):
        """Test review cycle time calculation."""
        cycle = ImprovementCycle(
            pip_id="PIP-001",
            task_id="TASK-001",
            events=[
                CycleEvent(
                    event_type="pip_created",
                    timestamp=datetime(2025, 11, 25, 10, 0, 0),
                    metadata={},
                ),
                CycleEvent(
                    event_type="pip_reviewed",
                    timestamp=datetime(2025, 11, 25, 11, 30, 0),
                    metadata={"decision": "approved"},
                ),
            ],
        )

        assert cycle.review_cycle_time == timedelta(hours=1, minutes=30)

    def test_total_cycle_time(self):
        """Test total cycle time calculation."""
        cycle = ImprovementCycle(
            pip_id="PIP-001",
            task_id="TASK-001",
            events=[
                CycleEvent(
                    event_type="pip_created",
                    timestamp=datetime(2025, 11, 25, 10, 0, 0),
                    metadata={},
                ),
                CycleEvent(
                    event_type="impact_measured",
                    timestamp=datetime(2025, 11, 26, 14, 0, 0),
                    metadata={},
                ),
            ],
        )

        assert cycle.total_cycle_time == timedelta(days=1, hours=4)

    def test_defect_reduction_percent(self):
        """Test defect reduction calculation."""
        cycle = ImprovementCycle(
            pip_id="PIP-001",
            task_id="TASK-001",
            baseline_defect_count=10,
            post_improvement_defect_count=3,
        )

        assert cycle.defect_reduction_percent == 70.0

    def test_defect_reduction_increase(self):
        """Test defect reduction with increase (negative reduction)."""
        cycle = ImprovementCycle(
            pip_id="PIP-001",
            task_id="TASK-001",
            baseline_defect_count=5,
            post_improvement_defect_count=8,
        )

        assert cycle.defect_reduction_percent == -60.0


class TestCycleTracker:
    """Test CycleTracker functionality."""

    def test_init(self, cycles_dir):
        """Test tracker initialization."""
        tracker = CycleTracker(cycles_dir)
        assert tracker.cycles_dir == cycles_dir
        assert cycles_dir.exists()

    def test_record_pip_created(self, cycles_dir, sample_pip):
        """Test recording PIP creation."""
        tracker = CycleTracker(cycles_dir)

        cycle = tracker.record_pip_created(sample_pip, defect_count=5)

        assert cycle.pip_id == "PIP-001"
        assert cycle.task_id == "TASK-001"
        assert cycle.baseline_defect_count == 5
        assert len(cycle.events) == 1
        assert cycle.events[0].event_type == "pip_created"
        assert "code_agent_prompt" in cycle.target_artifacts

    def test_record_pip_reviewed(self, cycles_dir, approved_pip):
        """Test recording PIP review."""
        tracker = CycleTracker(cycles_dir)

        # Create initial cycle
        tracker.record_pip_created(approved_pip, defect_count=5)

        # Record review
        cycle = tracker.record_pip_reviewed(approved_pip)

        assert len(cycle.events) == 2
        assert cycle.events[1].event_type == "pip_reviewed"
        assert cycle.events[1].metadata["decision"] == "approved"
        assert cycle.events[1].metadata["reviewer"] == "security@example.com"

    def test_record_prompts_updated(self, cycles_dir, sample_pip):
        """Test recording prompt updates."""
        tracker = CycleTracker(cycles_dir)

        # Create initial cycle
        tracker.record_pip_created(sample_pip)

        # Record prompt update
        updated_files = [
            "src/asp/prompts/code_agent_v2_generation.txt",
            "src/asp/prompts/code_security_review_v2.txt",
        ]
        cycle = tracker.record_prompts_updated("PIP-001", updated_files)

        assert len(cycle.events) == 2
        assert cycle.events[1].event_type == "prompts_updated"
        assert cycle.events[1].metadata["count"] == "2"
        assert (
            "code_agent_v2_generation.txt" in cycle.events[1].metadata["files_updated"]
        )

    def test_record_impact(self, cycles_dir, sample_pip):
        """Test recording improvement impact."""
        tracker = CycleTracker(cycles_dir)

        # Create initial cycle with baseline
        tracker.record_pip_created(sample_pip, defect_count=10)

        # Record impact
        cycle = tracker.record_impact(
            pip_id="PIP-001",
            impact_task_id="TASK-002",
            defect_count=3,
            notes="Significant improvement in security defects",
        )

        assert cycle.impact_task_id == "TASK-002"
        assert cycle.post_improvement_defect_count == 3
        assert cycle.defect_reduction_percent == 70.0

        # Verify event
        impact_event = cycle.events[-1]
        assert impact_event.event_type == "impact_measured"
        assert impact_event.metadata["defect_count"] == "3"
        assert impact_event.metadata["defect_reduction_percent"] == "70.0%"
        assert (
            impact_event.metadata["notes"]
            == "Significant improvement in security defects"
        )

    def test_get_cycle(self, cycles_dir, sample_pip):
        """Test retrieving cycle by PIP ID."""
        tracker = CycleTracker(cycles_dir)

        # Create cycle
        created_cycle = tracker.record_pip_created(sample_pip, defect_count=5)

        # Retrieve cycle
        retrieved_cycle = tracker.get_cycle("PIP-001")

        assert retrieved_cycle.pip_id == created_cycle.pip_id
        assert retrieved_cycle.task_id == created_cycle.task_id
        assert retrieved_cycle.baseline_defect_count == 5

    def test_get_cycle_not_found(self, cycles_dir):
        """Test error when cycle not found."""
        tracker = CycleTracker(cycles_dir)

        with pytest.raises(FileNotFoundError, match="Improvement cycle not found"):
            tracker.get_cycle("PIP-999")

    def test_get_all_cycles(self, cycles_dir):
        """Test retrieving all cycles."""
        tracker = CycleTracker(cycles_dir)

        # Create multiple cycles
        pip1 = ProcessImprovementProposal(
            proposal_id="PIP-001",
            task_id="TASK-001",
            created_at=datetime.now(),
            analysis="Test 1",
            proposed_changes=[
                ProposedChange(
                    target_artifact="test",
                    change_type="add",
                    proposed_content="Test",
                    rationale="Test",
                )
            ],
            expected_impact="Test",
        )
        tracker.record_pip_created(pip1, defect_count=5)

        pip2 = ProcessImprovementProposal(
            proposal_id="PIP-002",
            task_id="TASK-002",
            created_at=datetime.now(),
            analysis="Test 2",
            proposed_changes=[
                ProposedChange(
                    target_artifact="test",
                    change_type="add",
                    proposed_content="Test",
                    rationale="Test",
                )
            ],
            expected_impact="Test",
        )
        tracker.record_pip_created(pip2, defect_count=8)

        # Get all cycles
        cycles = tracker.get_all_cycles()

        assert len(cycles) == 2
        pip_ids = [c.pip_id for c in cycles]
        assert "PIP-001" in pip_ids
        assert "PIP-002" in pip_ids

    def test_generate_report_empty(self, cycles_dir):
        """Test report generation with no cycles."""
        tracker = CycleTracker(cycles_dir)

        report = tracker.generate_report()

        assert report["total_cycles"] == 0
        assert "message" in report

    def test_generate_report_with_data(self, cycles_dir, sample_pip):
        """Test report generation with cycle data."""
        tracker = CycleTracker(cycles_dir)

        # Create complete cycle
        pip = sample_pip
        pip.hitl_status = "approved"
        pip.hitl_reviewed_at = datetime(2025, 11, 25, 12, 0, 0)

        tracker.record_pip_created(pip, defect_count=10)
        tracker.record_pip_reviewed(pip)
        tracker.record_prompts_updated("PIP-001", ["test.txt"])
        tracker.record_impact("PIP-001", "TASK-002", defect_count=3)

        # Generate report
        report = tracker.generate_report()

        assert report["total_cycles"] == 1
        assert report["completed_cycles"] == 1
        assert report["avg_review_time_hours"] is not None
        assert report["avg_defect_reduction_percent"] == 70.0
        assert report["cycles_with_positive_impact"] == 1
        assert report["cycles_with_negative_impact"] == 0

    def test_generate_report_mixed_impact(self, cycles_dir):
        """Test report with positive and negative impact cycles."""
        tracker = CycleTracker(cycles_dir)

        # Cycle 1: Positive impact (10 → 2 defects)
        pip1 = ProcessImprovementProposal(
            proposal_id="PIP-001",
            task_id="TASK-001",
            created_at=datetime.now(),
            analysis="Test",
            proposed_changes=[
                ProposedChange(
                    target_artifact="test",
                    change_type="add",
                    proposed_content="Test",
                    rationale="Test",
                )
            ],
            expected_impact="Test",
        )
        tracker.record_pip_created(pip1, defect_count=10)
        tracker.record_impact("PIP-001", "TASK-002", defect_count=2)

        # Cycle 2: Negative impact (5 → 8 defects)
        pip2 = ProcessImprovementProposal(
            proposal_id="PIP-002",
            task_id="TASK-003",
            created_at=datetime.now(),
            analysis="Test",
            proposed_changes=[
                ProposedChange(
                    target_artifact="test",
                    change_type="add",
                    proposed_content="Test",
                    rationale="Test",
                )
            ],
            expected_impact="Test",
        )
        tracker.record_pip_created(pip2, defect_count=5)
        tracker.record_impact("PIP-002", "TASK-004", defect_count=8)

        # Generate report
        report = tracker.generate_report()

        assert report["total_cycles"] == 2
        assert report["cycles_with_positive_impact"] == 1
        assert report["cycles_with_negative_impact"] == 1
        assert report["cycles_with_no_change"] == 0


class TestCycleTrackerIntegration:
    """Integration tests for complete cycle tracking."""

    def test_complete_improvement_cycle(self, cycles_dir):
        """Test tracking complete improvement cycle from start to finish."""
        tracker = CycleTracker(cycles_dir)

        # Step 1: PIP created
        pip = ProcessImprovementProposal(
            proposal_id="PIP-TEST-001",
            task_id="TASK-ORIG",
            created_at=datetime(2025, 11, 25, 10, 0, 0),
            analysis="High defect density in security checks",
            proposed_changes=[
                ProposedChange(
                    target_artifact="code_review_security",
                    change_type="add",
                    proposed_content="Check for SQL injection in all database queries",
                    rationale="Prevent security vulnerabilities",
                )
            ],
            expected_impact="Reduce security defects by 80%",
        )

        cycle = tracker.record_pip_created(pip, defect_count=15)
        assert cycle.baseline_defect_count == 15

        # Step 2: PIP reviewed
        pip.hitl_status = "approved"
        pip.hitl_reviewer = "security@team.com"
        pip.hitl_reviewed_at = datetime(2025, 11, 25, 11, 30, 0)
        pip.hitl_feedback = "Critical security improvement"

        cycle = tracker.record_pip_reviewed(pip)
        assert cycle.review_cycle_time == timedelta(hours=1, minutes=30)

        # Step 3: Prompts updated
        updated_files = ["src/asp/prompts/code_security_review_v2.txt"]
        cycle = tracker.record_prompts_updated("PIP-TEST-001", updated_files)
        assert len(cycle.events) == 3

        # Step 4: Impact measured
        cycle = tracker.record_impact(
            pip_id="PIP-TEST-001",
            impact_task_id="TASK-NEW",
            defect_count=3,
            notes="Dramatic reduction in SQL injection defects",
        )

        # Verify complete cycle
        assert cycle.impact_task_id == "TASK-NEW"
        assert cycle.baseline_defect_count == 15
        assert cycle.post_improvement_defect_count == 3
        assert cycle.defect_reduction_percent == 80.0
        assert cycle.total_cycle_time is not None

        # Verify all events recorded
        event_types = [e.event_type for e in cycle.events]
        assert "pip_created" in event_types
        assert "pip_reviewed" in event_types
        assert "prompts_updated" in event_types
        assert "impact_measured" in event_types
