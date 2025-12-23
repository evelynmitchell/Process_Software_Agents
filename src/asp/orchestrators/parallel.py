"""
Parallel Execution Utilities for ASP Platform.

Provides utilities for running agents and tasks concurrently with
rate limiting and error handling.

Part of ADR 008: Async Process Architecture.

Author: ASP Development Team
Date: December 2025
"""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from pydantic import BaseModel

    from asp.agents.base_agent import BaseAgent

logger = logging.getLogger(__name__)


# =============================================================================
# Configuration
# =============================================================================


@dataclass
class AsyncConfig:
    """
    Configuration for async execution.

    Controls concurrency limits, timeouts, and behavior for parallel
    agent execution.
    """

    # Concurrency limits
    max_concurrent_llm_calls: int = 5  # Respect API rate limits
    max_concurrent_codegen: int = 3  # Parallel file generation
    max_concurrent_reviews: int = 4  # Parallel code reviews
    max_concurrent_tests: int = 1  # Usually sequential

    # Timeouts (in seconds)
    llm_call_timeout: float = 120.0  # 2 minutes per LLM call
    subprocess_timeout: float = 300.0  # 5 minutes for tests
    agent_timeout: float = 180.0  # 3 minutes per agent execution

    # Behavior
    prefer_async: bool = True  # Use async when available
    fallback_to_sync: bool = True  # Fall back if async fails
    return_exceptions: bool = False  # Return exceptions instead of raising


# Default configuration
DEFAULT_ASYNC_CONFIG = AsyncConfig()


# =============================================================================
# Parallel Execution Utilities
# =============================================================================


async def gather_with_concurrency[
    T
](limit: int, *tasks: Awaitable[T], return_exceptions: bool = False,) -> list[T]:
    """
    Run tasks with concurrency limit.

    Uses a semaphore to limit how many tasks run simultaneously,
    preventing API rate limit violations.

    Args:
        limit: Max concurrent tasks (0 = unlimited)
        *tasks: Awaitables to execute
        return_exceptions: If True, return exceptions instead of raising

    Returns:
        Results in same order as input tasks

    Example:
        >>> tasks = [agent.execute_async(input) for input in inputs]
        >>> results = await gather_with_concurrency(5, *tasks)
    """
    if limit <= 0:
        return await asyncio.gather(*tasks, return_exceptions=return_exceptions)

    semaphore = asyncio.Semaphore(limit)

    async def limited_task(task: Awaitable[T]) -> T:
        async with semaphore:
            return await task

    return await asyncio.gather(
        *[limited_task(t) for t in tasks],
        return_exceptions=return_exceptions,
    )


async def run_agents_parallel(
    agents: list[BaseAgent],
    inputs: list[BaseModel],
    max_concurrent: int = 5,
    timeout: float | None = None,
    return_exceptions: bool = False,
) -> list[BaseModel]:
    """
    Run multiple agents in parallel.

    Executes agents concurrently with configurable concurrency limit
    and optional timeout.

    Args:
        agents: List of agents to run
        inputs: Corresponding inputs for each agent
        max_concurrent: Max concurrent LLM calls
        timeout: Optional timeout for the entire batch (seconds)
        return_exceptions: If True, return exceptions instead of raising

    Returns:
        Results from each agent (in same order as inputs)

    Raises:
        ValueError: If agents and inputs have different lengths
        asyncio.TimeoutError: If timeout is exceeded

    Example:
        >>> agents = [CodeAgent() for _ in range(3)]
        >>> inputs = [CodeInput(file=f) for f in files]
        >>> results = await run_agents_parallel(agents, inputs, max_concurrent=3)
    """
    if len(agents) != len(inputs):
        raise ValueError(
            f"Number of agents ({len(agents)}) must match "
            f"number of inputs ({len(inputs)})"
        )

    if not agents:
        return []

    logger.info(
        f"Running {len(agents)} agents in parallel "
        f"(max_concurrent={max_concurrent})"
    )

    tasks = [
        agent.execute_async(input_data)
        for agent, input_data in zip(agents, inputs, strict=False)
    ]

    if timeout:
        results = await asyncio.wait_for(
            gather_with_concurrency(
                max_concurrent, *tasks, return_exceptions=return_exceptions
            ),
            timeout=timeout,
        )
    else:
        results = await gather_with_concurrency(
            max_concurrent, *tasks, return_exceptions=return_exceptions
        )

    # Log summary
    successful = sum(1 for r in results if not isinstance(r, Exception))
    logger.info(f"Parallel execution complete: {successful}/{len(results)} succeeded")

    return results


async def run_with_retry[
    T
](
    coro_factory: Callable[[], Awaitable[T]],
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 30.0,
) -> T:
    """
    Retry async operation with exponential backoff.

    Args:
        coro_factory: Callable that returns a new coroutine for each attempt
        max_retries: Maximum number of retry attempts
        base_delay: Base delay between retries (seconds)
        max_delay: Maximum delay between retries (seconds)

    Returns:
        Result of successful coroutine execution

    Raises:
        Exception: The last exception if all retries fail

    Example:
        >>> result = await run_with_retry(
        ...     lambda: agent.execute_async(input),
        ...     max_retries=3,
        ... )
    """
    last_exception: Exception | None = None

    for attempt in range(max_retries):
        try:
            return await coro_factory()
        except Exception as e:
            last_exception = e
            if attempt < max_retries - 1:
                delay = min(base_delay * (2**attempt), max_delay)
                logger.warning(
                    f"Attempt {attempt + 1}/{max_retries} failed: {e}. "
                    f"Retrying in {delay:.1f}s..."
                )
                await asyncio.sleep(delay)

    assert last_exception is not None
    raise last_exception


async def run_with_timeout[
    T
](coro: Awaitable[T], timeout: float, error_message: str = "Operation timed out",) -> T:
    """
    Run coroutine with timeout.

    Args:
        coro: Coroutine to execute
        timeout: Timeout in seconds
        error_message: Custom error message for timeout

    Returns:
        Result of coroutine

    Raises:
        asyncio.TimeoutError: If timeout is exceeded
    """
    try:
        return await asyncio.wait_for(coro, timeout=timeout)
    except TimeoutError:
        logger.error(f"{error_message} (timeout={timeout}s)")
        raise


# =============================================================================
# Error Handling
# =============================================================================


@dataclass
class ParallelExecutionResult:
    """
    Result of parallel execution with detailed status.

    Attributes:
        results: Successful results (None for failed tasks)
        exceptions: Exceptions for failed tasks (None for successful)
        successful_count: Number of successful tasks
        failed_count: Number of failed tasks
    """

    results: list[Any | None] = field(default_factory=list)
    exceptions: list[Exception | None] = field(default_factory=list)

    @property
    def successful_count(self) -> int:
        """Number of successful results."""
        return sum(1 for e in self.exceptions if e is None)

    @property
    def failed_count(self) -> int:
        """Number of failed results."""
        return sum(1 for e in self.exceptions if e is not None)

    @property
    def all_successful(self) -> bool:
        """True if all tasks succeeded."""
        return self.failed_count == 0

    def get_successful_results(self) -> list[Any]:
        """Return only successful results."""
        return [
            r for r, e in zip(self.results, self.exceptions, strict=False) if e is None
        ]

    def get_failed_indices(self) -> list[int]:
        """Return indices of failed tasks."""
        return [i for i, e in enumerate(self.exceptions) if e is not None]


async def gather_with_results[
    T
](*tasks: Awaitable[T], max_concurrent: int = 0,) -> ParallelExecutionResult:
    """
    Run tasks and return detailed results including failures.

    Unlike gather_with_concurrency, this always captures exceptions
    and returns them in a structured format.

    Args:
        *tasks: Awaitables to execute
        max_concurrent: Max concurrent tasks (0 = unlimited)

    Returns:
        ParallelExecutionResult with results and exceptions

    Example:
        >>> result = await gather_with_results(task1, task2, task3)
        >>> if result.all_successful:
        ...     print("All tasks succeeded!")
        >>> else:
        ...     print(f"{result.failed_count} tasks failed")
    """
    raw_results = await gather_with_concurrency(
        max_concurrent, *tasks, return_exceptions=True
    )

    results = []
    exceptions = []

    for r in raw_results:
        if isinstance(r, Exception):
            results.append(None)
            exceptions.append(r)
        else:
            results.append(r)
            exceptions.append(None)

    return ParallelExecutionResult(results=results, exceptions=exceptions)


# =============================================================================
# Rate Limiting
# =============================================================================


class RateLimiter:
    """
    Token bucket rate limiter for API calls.

    Limits the rate of operations to prevent API rate limit violations.

    Example:
        >>> limiter = RateLimiter(requests_per_minute=60)
        >>> async with limiter:
        ...     await make_api_call()
    """

    def __init__(
        self,
        requests_per_minute: int = 60,
        burst_size: int | None = None,
    ):
        """
        Initialize rate limiter.

        Args:
            requests_per_minute: Maximum requests per minute
            burst_size: Max burst size (defaults to requests_per_minute)
        """
        self.requests_per_minute = requests_per_minute
        self.burst_size = burst_size or requests_per_minute
        self._semaphore = asyncio.Semaphore(self.burst_size)
        self._refill_rate = 60.0 / requests_per_minute  # seconds per token
        self._tasks: set[asyncio.Task[Any]] = set()  # Track background tasks

    async def acquire(self) -> None:
        """Acquire a rate limit token."""
        await self._semaphore.acquire()
        # Schedule token release and track the task
        task = asyncio.create_task(self._release_after_delay())
        self._tasks.add(task)
        task.add_done_callback(self._tasks.discard)

    async def _release_after_delay(self) -> None:
        """Release token after delay."""
        await asyncio.sleep(self._refill_rate)
        self._semaphore.release()

    async def __aenter__(self) -> RateLimiter:
        """Context manager entry."""
        await self.acquire()
        return self

    async def __aexit__(self, *args) -> None:
        """Context manager exit (token already scheduled for release)."""
        pass

    async def close(self) -> None:
        """
        Cancel pending tasks and clean up resources.

        Call this method during graceful shutdown to ensure all background
        tasks are properly cancelled and awaited.

        Example:
            >>> limiter = RateLimiter(requests_per_minute=60)
            >>> # ... use limiter ...
            >>> await limiter.close()  # Clean shutdown
        """
        if not self._tasks:
            return

        # Cancel all pending tasks
        for task in self._tasks:
            task.cancel()

        # Wait for all tasks to complete (with cancellation)
        await asyncio.gather(*self._tasks, return_exceptions=True)
        self._tasks.clear()
