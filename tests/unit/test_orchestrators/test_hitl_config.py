"""
Unit tests for HITL configuration module.

Tests the Human-in-the-Loop configuration and approval logic.
"""

# pylint: disable=too-many-public-methods

import pytest

from asp.orchestrators.hitl_config import (
    AUTONOMOUS_CONFIG,
    CONSERVATIVE_CONFIG,
    DEFAULT_CONFIG,
    PRODUCTION_CONFIG,
    SUPERVISED_CONFIG,
    HITLConfig,
)


class TestHITLConfigValidation:
    """Tests for HITLConfig validation."""

    def test_valid_config(self):
        """Test creating a valid configuration."""
        config = HITLConfig(
            mode="threshold",
            require_approval_after_iterations=3,
            require_approval_for_confidence_below=0.6,
            max_auto_iterations=10,
        )
        assert config.mode == "threshold"
        assert config.require_approval_after_iterations == 3

    def test_invalid_iterations_negative(self):
        """Test negative iterations validation."""
        with pytest.raises(ValueError, match="non-negative"):
            HITLConfig(require_approval_after_iterations=-1)

    def test_invalid_confidence_below_zero(self):
        """Test confidence below 0 validation."""
        with pytest.raises(ValueError, match="between 0 and 1"):
            HITLConfig(require_approval_for_confidence_below=-0.1)

    def test_invalid_confidence_above_one(self):
        """Test confidence above 1 validation."""
        with pytest.raises(ValueError, match="between 0 and 1"):
            HITLConfig(require_approval_for_confidence_below=1.5)

    def test_invalid_auto_approve_confidence(self):
        """Test auto_approve_high_confidence validation."""
        with pytest.raises(ValueError, match="between 0 and 1"):
            HITLConfig(auto_approve_high_confidence=2.0)

    def test_invalid_max_auto_iterations(self):
        """Test max_auto_iterations negative validation."""
        with pytest.raises(ValueError, match="non-negative"):
            HITLConfig(max_auto_iterations=-1)


class TestAutonomousMode:
    """Tests for autonomous mode."""

    def test_never_requires_approval(self):
        """Test autonomous mode never requires approval."""
        config = HITLConfig(mode="autonomous")

        # Low confidence
        requires, reason = config.should_require_approval(iteration=1, confidence=0.1)
        assert requires is False
        assert reason == ""

        # Many iterations
        requires, reason = config.should_require_approval(iteration=100, confidence=0.1)
        assert requires is False

        # Critical files
        requires, reason = config.should_require_approval(
            iteration=1, confidence=0.1, files_to_modify=["config.py"]
        )
        assert requires is False


class TestSupervisedMode:
    """Tests for supervised mode."""

    def test_always_requires_approval(self):
        """Test supervised mode always requires approval."""
        config = HITLConfig(mode="supervised")

        # High confidence
        requires, reason = config.should_require_approval(iteration=1, confidence=0.99)
        assert requires is True
        assert "Supervised mode" in reason

        # First iteration
        requires, reason = config.should_require_approval(iteration=1, confidence=1.0)
        assert requires is True


class TestThresholdMode:
    """Tests for threshold mode (default)."""

    @pytest.fixture
    def config(self):
        """Create a threshold config."""
        return HITLConfig(
            mode="threshold",
            require_approval_after_iterations=2,
            require_approval_for_confidence_below=0.7,
            auto_approve_high_confidence=0.9,
            max_auto_iterations=5,
            require_approval_for_large_changes=10,
        )

    def test_first_iteration_high_confidence_no_approval(self, config):
        """Test first iteration with high confidence doesn't need approval."""
        requires, reason = config.should_require_approval(iteration=1, confidence=0.85)
        assert requires is False

    def test_iteration_threshold_triggers_approval(self, config):
        """Test exceeding iteration threshold triggers approval."""
        requires, reason = config.should_require_approval(iteration=3, confidence=0.8)
        assert requires is True
        assert "Iteration 3 exceeds threshold of 2" in reason

    def test_confidence_threshold_triggers_approval(self, config):
        """Test low confidence triggers approval."""
        requires, reason = config.should_require_approval(iteration=1, confidence=0.5)
        assert requires is True
        assert "Confidence 0.50 below threshold of 0.7" in reason

    def test_high_confidence_auto_approves(self, config):
        """Test very high confidence auto-approves."""
        requires, reason = config.should_require_approval(
            iteration=1,
            confidence=0.95,  # > 0.9 auto_approve threshold
        )
        assert requires is False

    def test_high_confidence_still_checks_critical_files(self, config):
        """Test high confidence still requires approval for critical files."""
        config.require_approval_for_critical_files = ["config", "auth"]

        requires, reason = config.should_require_approval(
            iteration=1,
            confidence=0.95,
            files_to_modify=["src/auth/login.py"],
        )
        assert requires is True
        assert "critical files" in reason

    def test_critical_files_pattern_matching(self, config):
        """Test critical file pattern matching."""
        config.require_approval_for_critical_files = ["secret", "credential"]

        # Matches "secret"
        requires, reason = config.should_require_approval(
            iteration=1,
            confidence=0.8,
            files_to_modify=["secrets/api_keys.py"],
        )
        assert requires is True
        assert "secrets/api_keys.py" in reason

    def test_large_changes_trigger_approval(self, config):
        """Test large change count triggers approval."""
        requires, reason = config.should_require_approval(
            iteration=1,
            confidence=0.8,
            change_count=15,
        )
        assert requires is True
        assert "Large change count" in reason

    def test_max_auto_iterations_hard_limit(self, config):
        """Test max_auto_iterations is a hard limit."""
        requires, reason = config.should_require_approval(
            iteration=5,  # = max_auto_iterations
            confidence=0.95,  # High confidence
        )
        assert requires is True
        assert "maximum auto-iteration limit" in reason

    def test_multiple_reasons_combined(self, config):
        """Test multiple reasons are combined."""
        config.require_approval_for_critical_files = ["config"]

        requires, reason = config.should_require_approval(
            iteration=3,  # > 2
            confidence=0.5,  # < 0.7
            files_to_modify=["config.py"],
            change_count=15,  # > 10
        )
        assert requires is True
        assert "Iteration 3" in reason
        assert "Confidence 0.50" in reason
        assert "critical files" in reason
        assert "Large change count" in reason


class TestCanContinueWithoutApproval:
    """Tests for can_continue_without_approval helper."""

    def test_returns_true_when_no_approval_needed(self):
        """Test returns True when approval not needed."""
        config = HITLConfig(mode="autonomous")
        assert config.can_continue_without_approval(iteration=1, confidence=0.5)

    def test_returns_false_when_approval_needed(self):
        """Test returns False when approval needed."""
        config = HITLConfig(mode="supervised")
        assert not config.can_continue_without_approval(iteration=1, confidence=0.9)


class TestPreDefinedConfigs:
    """Tests for pre-defined configurations."""

    def test_autonomous_config(self):
        """Test AUTONOMOUS_CONFIG."""
        assert AUTONOMOUS_CONFIG.mode == "autonomous"
        requires, _ = AUTONOMOUS_CONFIG.should_require_approval(
            iteration=100, confidence=0.0
        )
        assert requires is False

    def test_supervised_config(self):
        """Test SUPERVISED_CONFIG."""
        assert SUPERVISED_CONFIG.mode == "supervised"
        requires, _ = SUPERVISED_CONFIG.should_require_approval(
            iteration=1, confidence=1.0
        )
        assert requires is True

    def test_default_config(self):
        """Test DEFAULT_CONFIG."""
        assert DEFAULT_CONFIG.mode == "threshold"
        assert DEFAULT_CONFIG.require_approval_after_iterations == 2
        assert DEFAULT_CONFIG.require_approval_for_confidence_below == 0.7
        assert DEFAULT_CONFIG.max_auto_iterations == 5

    def test_conservative_config(self):
        """Test CONSERVATIVE_CONFIG is more strict."""
        assert CONSERVATIVE_CONFIG.mode == "threshold"
        assert CONSERVATIVE_CONFIG.require_approval_after_iterations == 1
        assert CONSERVATIVE_CONFIG.require_approval_for_confidence_below == 0.8
        assert CONSERVATIVE_CONFIG.max_auto_iterations == 3

    def test_production_config_has_critical_files(self):
        """Test PRODUCTION_CONFIG protects sensitive files."""
        assert PRODUCTION_CONFIG.mode == "threshold"
        assert "config" in PRODUCTION_CONFIG.require_approval_for_critical_files
        assert "auth" in PRODUCTION_CONFIG.require_approval_for_critical_files
        assert "secret" in PRODUCTION_CONFIG.require_approval_for_critical_files

        # Should require approval for auth files
        requires, _ = PRODUCTION_CONFIG.should_require_approval(
            iteration=1,
            confidence=0.8,
            files_to_modify=["src/auth/oauth.py"],
        )
        assert requires is True
