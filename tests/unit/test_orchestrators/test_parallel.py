"""
Tests for parallel execution utilities.

Tests the async execution helpers from ADR 008: Async Process Architecture.
"""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from asp.orchestrators.parallel import (
    AsyncConfig,
    DEFAULT_ASYNC_CONFIG,
    ParallelExecutionResult,
    RateLimiter,
    gather_with_concurrency,
    gather_with_results,
    run_agents_parallel,
    run_with_retry,
    run_with_timeout,
)


# =============================================================================
# AsyncConfig Tests
# =============================================================================


class TestAsyncConfig:
    """Tests for AsyncConfig dataclass."""

    def test_default_values(self):
        """Test default configuration values."""
        config = AsyncConfig()
        assert config.max_concurrent_llm_calls == 5
        assert config.max_concurrent_codegen == 3
        assert config.max_concurrent_reviews == 4
        assert config.max_concurrent_tests == 1
        assert config.llm_call_timeout == 120.0
        assert config.subprocess_timeout == 300.0
        assert config.agent_timeout == 180.0
        assert config.prefer_async is True
        assert config.fallback_to_sync is True
        assert config.return_exceptions is False

    def test_custom_values(self):
        """Test custom configuration values."""
        config = AsyncConfig(
            max_concurrent_llm_calls=10,
            llm_call_timeout=60.0,
            prefer_async=False,
        )
        assert config.max_concurrent_llm_calls == 10
        assert config.llm_call_timeout == 60.0
        assert config.prefer_async is False

    def test_default_async_config_exists(self):
        """Test that default config constant exists."""
        assert DEFAULT_ASYNC_CONFIG is not None
        assert isinstance(DEFAULT_ASYNC_CONFIG, AsyncConfig)


# =============================================================================
# gather_with_concurrency Tests
# =============================================================================


class TestGatherWithConcurrency:
    """Tests for gather_with_concurrency function."""

    @pytest.mark.asyncio
    async def test_basic_gather(self):
        """Test basic parallel execution."""
        results = []

        async def task(n):
            results.append(n)
            return n * 2

        output = await gather_with_concurrency(
            3, task(1), task(2), task(3)
        )
        assert output == [2, 4, 6]
        assert set(results) == {1, 2, 3}

    @pytest.mark.asyncio
    async def test_unlimited_concurrency(self):
        """Test unlimited concurrency (limit=0)."""
        async def task(n):
            return n

        output = await gather_with_concurrency(0, task(1), task(2), task(3))
        assert output == [1, 2, 3]

    @pytest.mark.asyncio
    async def test_limited_concurrency(self):
        """Test that concurrency is actually limited."""
        active = []
        max_active = 0

        async def task(n):
            nonlocal max_active
            active.append(n)
            max_active = max(max_active, len(active))
            await asyncio.sleep(0.01)  # Simulate work
            active.remove(n)
            return n

        await gather_with_concurrency(2, task(1), task(2), task(3), task(4))
        assert max_active <= 2

    @pytest.mark.asyncio
    async def test_return_exceptions(self):
        """Test returning exceptions instead of raising."""
        async def failing_task():
            raise ValueError("test error")

        async def success_task():
            return "success"

        results = await gather_with_concurrency(
            2, success_task(), failing_task(), return_exceptions=True
        )
        assert results[0] == "success"
        assert isinstance(results[1], ValueError)

    @pytest.mark.asyncio
    async def test_empty_tasks(self):
        """Test with no tasks."""
        results = await gather_with_concurrency(5)
        assert results == []


# =============================================================================
# run_agents_parallel Tests
# =============================================================================


class TestRunAgentsParallel:
    """Tests for run_agents_parallel function."""

    @pytest.mark.asyncio
    async def test_parallel_execution(self):
        """Test running multiple agents in parallel."""
        # Create mock agents
        agent1 = MagicMock()
        agent1.execute_async = AsyncMock(return_value="result1")

        agent2 = MagicMock()
        agent2.execute_async = AsyncMock(return_value="result2")

        inputs = [MagicMock(), MagicMock()]

        results = await run_agents_parallel(
            [agent1, agent2], inputs, max_concurrent=2
        )

        assert results == ["result1", "result2"]
        agent1.execute_async.assert_called_once_with(inputs[0])
        agent2.execute_async.assert_called_once_with(inputs[1])

    @pytest.mark.asyncio
    async def test_mismatched_lengths_raises_error(self):
        """Test that mismatched agents/inputs raises ValueError."""
        agents = [MagicMock(), MagicMock()]
        inputs = [MagicMock()]  # One less than agents

        with pytest.raises(ValueError, match="must match"):
            await run_agents_parallel(agents, inputs)

    @pytest.mark.asyncio
    async def test_empty_agents(self):
        """Test with empty agent list."""
        results = await run_agents_parallel([], [])
        assert results == []

    @pytest.mark.asyncio
    async def test_with_timeout(self):
        """Test parallel execution with timeout."""
        agent = MagicMock()
        agent.execute_async = AsyncMock(return_value="result")

        results = await run_agents_parallel(
            [agent], [MagicMock()], timeout=5.0
        )

        assert results == ["result"]

    @pytest.mark.asyncio
    async def test_timeout_exceeded(self):
        """Test that timeout is enforced."""
        async def slow_execute(_):
            await asyncio.sleep(10)  # Very slow
            return "result"

        agent = MagicMock()
        agent.execute_async = slow_execute

        with pytest.raises(asyncio.TimeoutError):
            await run_agents_parallel(
                [agent], [MagicMock()], timeout=0.01
            )


# =============================================================================
# run_with_retry Tests
# =============================================================================


class TestRunWithRetry:
    """Tests for run_with_retry function."""

    @pytest.mark.asyncio
    async def test_success_on_first_try(self):
        """Test successful execution on first attempt."""
        async def success():
            return "success"

        result = await run_with_retry(success)
        assert result == "success"

    @pytest.mark.asyncio
    async def test_retry_on_failure(self):
        """Test retry after failure."""
        attempts = []

        async def flaky():
            attempts.append(1)
            if len(attempts) < 2:
                raise ValueError("temporary error")
            return "success"

        result = await run_with_retry(flaky, max_retries=3, base_delay=0.01)
        assert result == "success"
        assert len(attempts) == 2

    @pytest.mark.asyncio
    async def test_max_retries_exceeded(self):
        """Test that exception is raised after max retries."""
        async def always_fail():
            raise ValueError("persistent error")

        with pytest.raises(ValueError, match="persistent error"):
            await run_with_retry(always_fail, max_retries=3, base_delay=0.01)


# =============================================================================
# run_with_timeout Tests
# =============================================================================


class TestRunWithTimeout:
    """Tests for run_with_timeout function."""

    @pytest.mark.asyncio
    async def test_success_within_timeout(self):
        """Test successful execution within timeout."""
        async def fast():
            return "result"

        result = await run_with_timeout(fast(), timeout=1.0)
        assert result == "result"

    @pytest.mark.asyncio
    async def test_timeout_exceeded(self):
        """Test that timeout is enforced."""
        async def slow():
            await asyncio.sleep(10)
            return "result"

        with pytest.raises(asyncio.TimeoutError):
            await run_with_timeout(slow(), timeout=0.01)


# =============================================================================
# ParallelExecutionResult Tests
# =============================================================================


class TestParallelExecutionResult:
    """Tests for ParallelExecutionResult dataclass."""

    def test_all_successful(self):
        """Test with all successful results."""
        result = ParallelExecutionResult(
            results=["a", "b", "c"],
            exceptions=[None, None, None],
        )
        assert result.successful_count == 3
        assert result.failed_count == 0
        assert result.all_successful is True
        assert result.get_successful_results() == ["a", "b", "c"]
        assert result.get_failed_indices() == []

    def test_some_failures(self):
        """Test with some failures."""
        error = ValueError("test")
        result = ParallelExecutionResult(
            results=["a", None, "c"],
            exceptions=[None, error, None],
        )
        assert result.successful_count == 2
        assert result.failed_count == 1
        assert result.all_successful is False
        assert result.get_successful_results() == ["a", "c"]
        assert result.get_failed_indices() == [1]

    def test_all_failures(self):
        """Test with all failures."""
        errors = [ValueError("e1"), ValueError("e2")]
        result = ParallelExecutionResult(
            results=[None, None],
            exceptions=errors,
        )
        assert result.successful_count == 0
        assert result.failed_count == 2
        assert result.all_successful is False


# =============================================================================
# gather_with_results Tests
# =============================================================================


class TestGatherWithResults:
    """Tests for gather_with_results function."""

    @pytest.mark.asyncio
    async def test_successful_tasks(self):
        """Test with all successful tasks."""
        async def task(n):
            return n

        result = await gather_with_results(task(1), task(2), task(3))
        assert result.all_successful
        assert result.results == [1, 2, 3]
        assert result.exceptions == [None, None, None]

    @pytest.mark.asyncio
    async def test_mixed_success_failure(self):
        """Test with mixed success and failure."""
        async def success():
            return "ok"

        async def failure():
            raise ValueError("error")

        result = await gather_with_results(success(), failure(), success())
        assert not result.all_successful
        assert result.successful_count == 2
        assert result.failed_count == 1
        assert result.results[0] == "ok"
        assert result.results[1] is None
        assert result.results[2] == "ok"
        assert isinstance(result.exceptions[1], ValueError)


# =============================================================================
# RateLimiter Tests
# =============================================================================


class TestRateLimiter:
    """Tests for RateLimiter class."""

    def test_init_defaults(self):
        """Test default initialization."""
        limiter = RateLimiter()
        assert limiter.requests_per_minute == 60
        assert limiter.burst_size == 60

    def test_init_custom(self):
        """Test custom initialization."""
        limiter = RateLimiter(requests_per_minute=30, burst_size=5)
        assert limiter.requests_per_minute == 30
        assert limiter.burst_size == 5

    @pytest.mark.asyncio
    async def test_context_manager(self):
        """Test rate limiter as context manager."""
        limiter = RateLimiter(requests_per_minute=1000, burst_size=10)

        async with limiter:
            pass  # Should not raise

    @pytest.mark.asyncio
    async def test_rate_limiting(self):
        """Test that rate limiting is applied."""
        # High rate limit for fast test
        limiter = RateLimiter(requests_per_minute=1000, burst_size=2)

        # Acquire burst
        async with limiter:
            async with limiter:
                pass  # Both should succeed quickly
