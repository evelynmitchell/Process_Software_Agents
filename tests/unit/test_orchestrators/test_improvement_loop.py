"""
Tests for asp.orchestrators.improvement_loop module.

Tests the self-improvement loop orchestrator.
"""

from pathlib import Path
from unittest import mock

import pytest


class TestImprovementLoopOrchestratorInit:
    """Tests for ImprovementLoopOrchestrator initialization."""

    def test_init_with_all_features_enabled(self):
        """Test initialization with all features enabled."""
        with mock.patch(
            "asp.orchestrators.improvement_loop.PIPReviewService"
        ) as mock_pip_service:
            with mock.patch(
                "asp.orchestrators.improvement_loop.PromptVersioner"
            ) as mock_versioner:
                with mock.patch(
                    "asp.orchestrators.improvement_loop.CycleTracker"
                ) as mock_tracker:
                    from asp.orchestrators.improvement_loop import (
                        ImprovementLoopOrchestrator,
                    )

                    orchestrator = ImprovementLoopOrchestrator(
                        enable_hitl=True,
                        enable_prompt_updates=True,
                        enable_cycle_tracking=True,
                    )

                    assert orchestrator.enable_hitl is True
                    assert orchestrator.enable_prompt_updates is True
                    assert orchestrator.enable_cycle_tracking is True
                    mock_pip_service.assert_called_once()
                    mock_versioner.assert_called_once()
                    mock_tracker.assert_called_once()

    def test_init_with_hitl_disabled(self):
        """Test initialization with HITL disabled."""
        with mock.patch(
            "asp.orchestrators.improvement_loop.PIPReviewService"
        ) as mock_pip_service:
            with mock.patch("asp.orchestrators.improvement_loop.PromptVersioner"):
                with mock.patch("asp.orchestrators.improvement_loop.CycleTracker"):
                    from asp.orchestrators.improvement_loop import (
                        ImprovementLoopOrchestrator,
                    )

                    orchestrator = ImprovementLoopOrchestrator(
                        enable_hitl=False,
                        enable_prompt_updates=True,
                        enable_cycle_tracking=True,
                    )

                    assert orchestrator.enable_hitl is False
                    assert orchestrator.pip_review_service is None
                    mock_pip_service.assert_not_called()

    def test_init_with_prompt_updates_disabled(self):
        """Test initialization with prompt updates disabled."""
        with mock.patch("asp.orchestrators.improvement_loop.PIPReviewService"):
            with mock.patch(
                "asp.orchestrators.improvement_loop.PromptVersioner"
            ) as mock_versioner:
                with mock.patch("asp.orchestrators.improvement_loop.CycleTracker"):
                    from asp.orchestrators.improvement_loop import (
                        ImprovementLoopOrchestrator,
                    )

                    orchestrator = ImprovementLoopOrchestrator(
                        enable_hitl=True,
                        enable_prompt_updates=False,
                        enable_cycle_tracking=True,
                    )

                    assert orchestrator.enable_prompt_updates is False
                    assert orchestrator.prompt_versioner is None
                    mock_versioner.assert_not_called()

    def test_init_with_cycle_tracking_disabled(self):
        """Test initialization with cycle tracking disabled."""
        with mock.patch("asp.orchestrators.improvement_loop.PIPReviewService"):
            with mock.patch("asp.orchestrators.improvement_loop.PromptVersioner"):
                with mock.patch(
                    "asp.orchestrators.improvement_loop.CycleTracker"
                ) as mock_tracker:
                    from asp.orchestrators.improvement_loop import (
                        ImprovementLoopOrchestrator,
                    )

                    orchestrator = ImprovementLoopOrchestrator(
                        enable_hitl=True,
                        enable_prompt_updates=True,
                        enable_cycle_tracking=False,
                    )

                    assert orchestrator.enable_cycle_tracking is False
                    assert orchestrator.cycle_tracker is None
                    mock_tracker.assert_not_called()


class TestRunImprovementCycle:
    """Tests for run_improvement_cycle method."""

    def setup_method(self):
        """Set up test fixtures."""
        # Create mock PIP
        self.mock_pip = mock.MagicMock()
        self.mock_pip.proposal_id = "PIP-001"
        self.mock_pip.hitl_status = "pending"

        # Create mock postmortem report
        self.mock_postmortem_report = mock.MagicMock()
        self.mock_postmortem_report.task_id = "TASK-001"

        # Create mock postmortem input
        self.mock_postmortem_input = mock.MagicMock()
        self.mock_postmortem_input.defect_log = ["defect1", "defect2"]

        # Create mock postmortem agent
        self.mock_postmortem_agent = mock.MagicMock()
        self.mock_postmortem_agent.generate_pip.return_value = self.mock_pip

    def test_run_cycle_generates_pip(self):
        """Test that cycle generates PIP from postmortem."""
        with mock.patch("asp.orchestrators.improvement_loop.PIPReviewService"):
            with mock.patch("asp.orchestrators.improvement_loop.PromptVersioner"):
                with mock.patch("asp.orchestrators.improvement_loop.CycleTracker"):
                    from asp.orchestrators.improvement_loop import (
                        ImprovementLoopOrchestrator,
                    )

                    orchestrator = ImprovementLoopOrchestrator(
                        enable_hitl=False,
                        enable_prompt_updates=False,
                        enable_cycle_tracking=False,
                    )

                    result = orchestrator.run_improvement_cycle(
                        postmortem_report=self.mock_postmortem_report,
                        postmortem_input=self.mock_postmortem_input,
                        postmortem_agent=self.mock_postmortem_agent,
                    )

                    assert result["pip_generated"] is True
                    assert result["pip"] == self.mock_pip
                    self.mock_postmortem_agent.generate_pip.assert_called_once()

    def test_run_cycle_auto_approve(self):
        """Test that cycle can auto-approve PIP."""
        with mock.patch("asp.orchestrators.improvement_loop.PIPReviewService"):
            with mock.patch("asp.orchestrators.improvement_loop.PromptVersioner"):
                with mock.patch("asp.orchestrators.improvement_loop.CycleTracker"):
                    from asp.orchestrators.improvement_loop import (
                        ImprovementLoopOrchestrator,
                    )

                    orchestrator = ImprovementLoopOrchestrator(
                        enable_hitl=True,
                        enable_prompt_updates=False,
                        enable_cycle_tracking=False,
                    )

                    result = orchestrator.run_improvement_cycle(
                        postmortem_report=self.mock_postmortem_report,
                        postmortem_input=self.mock_postmortem_input,
                        postmortem_agent=self.mock_postmortem_agent,
                        auto_approve=True,
                    )

                    assert result["pip_approved"] is True
                    assert self.mock_pip.hitl_status == "approved"
                    assert self.mock_pip.hitl_reviewer == "auto-approve"

    def test_run_cycle_hitl_review(self):
        """Test that cycle uses HITL review when enabled."""
        mock_pip_review_service = mock.MagicMock()
        approved_pip = mock.MagicMock()
        approved_pip.hitl_status = "approved"
        mock_pip_review_service.review_pip.return_value = approved_pip

        with mock.patch(
            "asp.orchestrators.improvement_loop.PIPReviewService",
            return_value=mock_pip_review_service,
        ):
            with mock.patch("asp.orchestrators.improvement_loop.PromptVersioner"):
                with mock.patch("asp.orchestrators.improvement_loop.CycleTracker"):
                    from asp.orchestrators.improvement_loop import (
                        ImprovementLoopOrchestrator,
                    )

                    orchestrator = ImprovementLoopOrchestrator(
                        enable_hitl=True,
                        enable_prompt_updates=False,
                        enable_cycle_tracking=False,
                    )

                    result = orchestrator.run_improvement_cycle(
                        postmortem_report=self.mock_postmortem_report,
                        postmortem_input=self.mock_postmortem_input,
                        postmortem_agent=self.mock_postmortem_agent,
                        auto_approve=False,
                    )

                    assert result["pip_approved"] is True
                    mock_pip_review_service.review_pip.assert_called_once()

    def test_run_cycle_applies_prompt_updates(self):
        """Test that cycle applies prompt updates when approved."""
        mock_prompt_versioner = mock.MagicMock()
        mock_prompt_versioner.apply_pip.return_value = {
            "file1.txt": "file1_v2.txt",
            "file2.txt": "file2_v2.txt",
        }

        with mock.patch("asp.orchestrators.improvement_loop.PIPReviewService"):
            with mock.patch(
                "asp.orchestrators.improvement_loop.PromptVersioner",
                return_value=mock_prompt_versioner,
            ):
                with mock.patch("asp.orchestrators.improvement_loop.CycleTracker"):
                    from asp.orchestrators.improvement_loop import (
                        ImprovementLoopOrchestrator,
                    )

                    orchestrator = ImprovementLoopOrchestrator(
                        enable_hitl=False,
                        enable_prompt_updates=True,
                        enable_cycle_tracking=False,
                    )

                    result = orchestrator.run_improvement_cycle(
                        postmortem_report=self.mock_postmortem_report,
                        postmortem_input=self.mock_postmortem_input,
                        postmortem_agent=self.mock_postmortem_agent,
                        auto_approve=True,
                    )

                    assert len(result["updated_prompts"]) == 2
                    mock_prompt_versioner.apply_pip.assert_called_once()

    def test_run_cycle_tracks_cycle(self):
        """Test that cycle tracking is enabled."""
        mock_cycle_tracker = mock.MagicMock()
        mock_cycle = mock.MagicMock()
        mock_cycle.pip_id = "PIP-001"
        mock_cycle_tracker.record_pip_created.return_value = mock_cycle

        with mock.patch("asp.orchestrators.improvement_loop.PIPReviewService"):
            with mock.patch("asp.orchestrators.improvement_loop.PromptVersioner"):
                with mock.patch(
                    "asp.orchestrators.improvement_loop.CycleTracker",
                    return_value=mock_cycle_tracker,
                ):
                    from asp.orchestrators.improvement_loop import (
                        ImprovementLoopOrchestrator,
                    )

                    orchestrator = ImprovementLoopOrchestrator(
                        enable_hitl=False,
                        enable_prompt_updates=False,
                        enable_cycle_tracking=True,
                    )

                    result = orchestrator.run_improvement_cycle(
                        postmortem_report=self.mock_postmortem_report,
                        postmortem_input=self.mock_postmortem_input,
                        postmortem_agent=self.mock_postmortem_agent,
                    )

                    assert result["cycle_id"] == "PIP-001"
                    mock_cycle_tracker.record_pip_created.assert_called_once()

    def test_run_cycle_handles_pip_generation_error(self):
        """Test that cycle handles PIP generation errors."""
        self.mock_postmortem_agent.generate_pip.side_effect = Exception("API error")

        with mock.patch("asp.orchestrators.improvement_loop.PIPReviewService"):
            with mock.patch("asp.orchestrators.improvement_loop.PromptVersioner"):
                with mock.patch("asp.orchestrators.improvement_loop.CycleTracker"):
                    from asp.orchestrators.improvement_loop import (
                        ImprovementLoopOrchestrator,
                    )

                    orchestrator = ImprovementLoopOrchestrator(
                        enable_hitl=False,
                        enable_prompt_updates=False,
                        enable_cycle_tracking=False,
                    )

                    result = orchestrator.run_improvement_cycle(
                        postmortem_report=self.mock_postmortem_report,
                        postmortem_input=self.mock_postmortem_input,
                        postmortem_agent=self.mock_postmortem_agent,
                    )

                    assert result["pip_generated"] is False
                    assert result["pip"] is None

    def test_run_cycle_handles_review_error(self):
        """Test that cycle handles review errors."""
        mock_pip_review_service = mock.MagicMock()
        mock_pip_review_service.review_pip.side_effect = Exception("Review failed")

        with mock.patch(
            "asp.orchestrators.improvement_loop.PIPReviewService",
            return_value=mock_pip_review_service,
        ):
            with mock.patch("asp.orchestrators.improvement_loop.PromptVersioner"):
                with mock.patch("asp.orchestrators.improvement_loop.CycleTracker"):
                    from asp.orchestrators.improvement_loop import (
                        ImprovementLoopOrchestrator,
                    )

                    orchestrator = ImprovementLoopOrchestrator(
                        enable_hitl=True,
                        enable_prompt_updates=False,
                        enable_cycle_tracking=False,
                    )

                    result = orchestrator.run_improvement_cycle(
                        postmortem_report=self.mock_postmortem_report,
                        postmortem_input=self.mock_postmortem_input,
                        postmortem_agent=self.mock_postmortem_agent,
                        auto_approve=False,
                    )

                    assert result["pip_generated"] is True
                    assert result["pip_approved"] is False

    def test_run_cycle_handles_prompt_update_error(self):
        """Test that cycle handles prompt update errors gracefully."""
        mock_prompt_versioner = mock.MagicMock()
        mock_prompt_versioner.apply_pip.side_effect = Exception("Update failed")

        with mock.patch("asp.orchestrators.improvement_loop.PIPReviewService"):
            with mock.patch(
                "asp.orchestrators.improvement_loop.PromptVersioner",
                return_value=mock_prompt_versioner,
            ):
                with mock.patch("asp.orchestrators.improvement_loop.CycleTracker"):
                    from asp.orchestrators.improvement_loop import (
                        ImprovementLoopOrchestrator,
                    )

                    orchestrator = ImprovementLoopOrchestrator(
                        enable_hitl=False,
                        enable_prompt_updates=True,
                        enable_cycle_tracking=False,
                    )

                    result = orchestrator.run_improvement_cycle(
                        postmortem_report=self.mock_postmortem_report,
                        postmortem_input=self.mock_postmortem_input,
                        postmortem_agent=self.mock_postmortem_agent,
                        auto_approve=True,
                    )

                    # Should still complete, but with error in updated_prompts
                    assert "ERROR" in str(result["updated_prompts"])


class TestMeasureImpact:
    """Tests for measure_impact method."""

    def test_measure_impact_success(self):
        """Test successful impact measurement."""
        mock_cycle_tracker = mock.MagicMock()
        mock_cycle = mock.MagicMock()
        mock_cycle.baseline_defect_count = 5
        mock_cycle.post_improvement_defect_count = 2
        mock_cycle.defect_reduction_percent = 60.0
        mock_cycle.review_cycle_time = "2:00:00"
        mock_cycle.total_cycle_time = "5:00:00"
        mock_cycle_tracker.record_impact.return_value = mock_cycle

        with mock.patch("asp.orchestrators.improvement_loop.PIPReviewService"):
            with mock.patch("asp.orchestrators.improvement_loop.PromptVersioner"):
                with mock.patch(
                    "asp.orchestrators.improvement_loop.CycleTracker",
                    return_value=mock_cycle_tracker,
                ):
                    from asp.orchestrators.improvement_loop import (
                        ImprovementLoopOrchestrator,
                    )

                    orchestrator = ImprovementLoopOrchestrator(
                        enable_hitl=False,
                        enable_prompt_updates=False,
                        enable_cycle_tracking=True,
                    )

                    result = orchestrator.measure_impact(
                        pip_id="PIP-001",
                        impact_task_id="TASK-002",
                        new_defect_count=2,
                        notes="Test notes",
                    )

                    assert result["baseline_defects"] == 5
                    assert result["new_defects"] == 2
                    assert result["defect_reduction_percent"] == 60.0

    def test_measure_impact_tracking_disabled(self):
        """Test impact returns empty when tracking disabled."""
        with mock.patch("asp.orchestrators.improvement_loop.PIPReviewService"):
            with mock.patch("asp.orchestrators.improvement_loop.PromptVersioner"):
                with mock.patch("asp.orchestrators.improvement_loop.CycleTracker"):
                    from asp.orchestrators.improvement_loop import (
                        ImprovementLoopOrchestrator,
                    )

                    orchestrator = ImprovementLoopOrchestrator(
                        enable_hitl=False,
                        enable_prompt_updates=False,
                        enable_cycle_tracking=False,
                    )

                    result = orchestrator.measure_impact(
                        pip_id="PIP-001",
                        impact_task_id="TASK-002",
                        new_defect_count=2,
                    )

                    assert result == {}

    def test_measure_impact_handles_error(self):
        """Test impact handles errors gracefully."""
        mock_cycle_tracker = mock.MagicMock()
        mock_cycle_tracker.record_impact.side_effect = Exception("Record failed")

        with mock.patch("asp.orchestrators.improvement_loop.PIPReviewService"):
            with mock.patch("asp.orchestrators.improvement_loop.PromptVersioner"):
                with mock.patch(
                    "asp.orchestrators.improvement_loop.CycleTracker",
                    return_value=mock_cycle_tracker,
                ):
                    from asp.orchestrators.improvement_loop import (
                        ImprovementLoopOrchestrator,
                    )

                    orchestrator = ImprovementLoopOrchestrator(
                        enable_hitl=False,
                        enable_prompt_updates=False,
                        enable_cycle_tracking=True,
                    )

                    result = orchestrator.measure_impact(
                        pip_id="PIP-001",
                        impact_task_id="TASK-002",
                        new_defect_count=2,
                    )

                    assert result == {}


class TestGetCycleReport:
    """Tests for get_cycle_report method."""

    def test_get_report_success(self):
        """Test successful report generation."""
        mock_cycle_tracker = mock.MagicMock()
        mock_cycle_tracker.generate_report.return_value = {
            "total_cycles": 10,
            "avg_review_time_hours": 2.5,
            "avg_defect_reduction_percent": 45.0,
        }

        with mock.patch("asp.orchestrators.improvement_loop.PIPReviewService"):
            with mock.patch("asp.orchestrators.improvement_loop.PromptVersioner"):
                with mock.patch(
                    "asp.orchestrators.improvement_loop.CycleTracker",
                    return_value=mock_cycle_tracker,
                ):
                    from asp.orchestrators.improvement_loop import (
                        ImprovementLoopOrchestrator,
                    )

                    orchestrator = ImprovementLoopOrchestrator(
                        enable_hitl=False,
                        enable_prompt_updates=False,
                        enable_cycle_tracking=True,
                    )

                    result = orchestrator.get_cycle_report()

                    assert result["total_cycles"] == 10
                    mock_cycle_tracker.generate_report.assert_called_once()

    def test_get_report_tracking_disabled(self):
        """Test report returns error when tracking disabled."""
        with mock.patch("asp.orchestrators.improvement_loop.PIPReviewService"):
            with mock.patch("asp.orchestrators.improvement_loop.PromptVersioner"):
                with mock.patch("asp.orchestrators.improvement_loop.CycleTracker"):
                    from asp.orchestrators.improvement_loop import (
                        ImprovementLoopOrchestrator,
                    )

                    orchestrator = ImprovementLoopOrchestrator(
                        enable_hitl=False,
                        enable_prompt_updates=False,
                        enable_cycle_tracking=False,
                    )

                    result = orchestrator.get_cycle_report()

                    assert "error" in result

    def test_get_report_handles_error(self):
        """Test report handles errors gracefully."""
        mock_cycle_tracker = mock.MagicMock()
        mock_cycle_tracker.generate_report.side_effect = Exception("Report failed")

        with mock.patch("asp.orchestrators.improvement_loop.PIPReviewService"):
            with mock.patch("asp.orchestrators.improvement_loop.PromptVersioner"):
                with mock.patch(
                    "asp.orchestrators.improvement_loop.CycleTracker",
                    return_value=mock_cycle_tracker,
                ):
                    from asp.orchestrators.improvement_loop import (
                        ImprovementLoopOrchestrator,
                    )

                    orchestrator = ImprovementLoopOrchestrator(
                        enable_hitl=False,
                        enable_prompt_updates=False,
                        enable_cycle_tracking=True,
                    )

                    result = orchestrator.get_cycle_report()

                    assert "error" in result


class TestIntegrateWithTSPOrchestrator:
    """Tests for integrate_with_tsp_orchestrator function."""

    def test_integrate_enabled(self):
        """Test integration with TSP orchestrator."""
        mock_tsp = mock.MagicMock()

        with mock.patch("asp.orchestrators.improvement_loop.PIPReviewService"):
            with mock.patch("asp.orchestrators.improvement_loop.PromptVersioner"):
                with mock.patch("asp.orchestrators.improvement_loop.CycleTracker"):
                    from asp.orchestrators.improvement_loop import (
                        integrate_with_tsp_orchestrator,
                    )

                    result = integrate_with_tsp_orchestrator(
                        tsp_orchestrator=mock_tsp,
                        enable_improvement_loop=True,
                        enable_hitl=True,
                        auto_approve_pips=False,
                    )

                    assert result is not None
                    assert mock_tsp.improvement_loop == result
                    assert mock_tsp.auto_approve_pips is False

    def test_integrate_disabled(self):
        """Test integration when disabled."""
        mock_tsp = mock.MagicMock()

        from asp.orchestrators.improvement_loop import integrate_with_tsp_orchestrator

        result = integrate_with_tsp_orchestrator(
            tsp_orchestrator=mock_tsp,
            enable_improvement_loop=False,
        )

        assert result is None
