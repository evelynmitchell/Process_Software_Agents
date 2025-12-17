# ADR 008: Async Process Architecture

**Status:** Active
**Date:** 2025-12-11
**Implementation Started:** 2025-12-17
**Session:** 20251211.3
**Deciders:** User, Claude

## Context and Problem Statement

The current ASP implementation is primarily **single-threaded and synchronous**, limiting throughput and responsiveness. Key bottlenecks include:

1. **Sequential LLM calls** - Each agent waits for its LLM call to complete before the next can start
2. **Blocking I/O** - File reads, subprocess execution, and network calls block the main thread
3. **No parallelism** - Independent agents (e.g., multiple code reviewers) run sequentially

### Current State

| Component | Async? | Notes |
|-----------|--------|-------|
| `RepairOrchestrator.repair()` | ✅ Yes | Already async |
| `CodeReviewOrchestrator._dispatch_specialists()` | ✅ Yes | Parallel specialist dispatch |
| `DesignReviewOrchestrator._dispatch_specialists()` | ✅ Yes | Parallel specialist dispatch |
| All agents (`execute_async()`) | ✅ Yes | Native async LLM calls (Phase 2 complete) |
| `LLMClient.call_with_retry_async()` | ✅ Yes | Async Anthropic client (Phase 1 complete) |
| `parallel.py` utilities | ✅ Yes | gather_with_concurrency, RateLimiter |
| `TSPOrchestrator.execute()` | ❌ No | Sequential pipeline (Phase 4) |
| `PlanningDesignOrchestrator.execute()` | ❌ No | Sequential (Phase 4) |
| `SandboxExecutor.execute()` | ❌ No | Blocking subprocess (Phase 3) |
| `TestExecutor.run_tests()` | ❌ No | Blocking (Phase 3) |

### Pain Points

```
Current: Sequential Execution
┌─────────────────────────────────────────────────────────────┐
│ Agent1 ██████████ → Agent2 ██████████ → Agent3 ██████████  │
│                                                             │
│ Total time: T1 + T2 + T3                                   │
└─────────────────────────────────────────────────────────────┘

Desired: Concurrent Execution (where possible)
┌─────────────────────────────────────────────────────────────┐
│ Agent1 ██████████                                          │
│ Agent2 ██████████  (if independent)                        │
│ Agent3      ██████████  (if depends on Agent1)             │
│                                                             │
│ Total time: max(T1, T2) + T3                               │
└─────────────────────────────────────────────────────────────┘
```

## Decision Drivers

1. **Throughput** - Process multiple tasks concurrently
2. **Latency** - Reduce wall-clock time for pipelines with independent stages
3. **Resource Utilization** - Better use of I/O wait time
4. **Incremental Migration** - Don't require big-bang rewrite
5. **Compatibility** - Support both sync and async callers
6. **Debuggability** - Async code can be harder to debug; maintain clarity

## Proposed Architecture

### 1. Async LLM Calls (Foundation)

The most impactful change: make LLM calls async.

**File:** `src/asp/agents/base_agent.py`

```python
from anthropic import AsyncAnthropic

class BaseAgent:
    def __init__(self, ...):
        self._sync_client = Anthropic(...)
        self._async_client = AsyncAnthropic(...)

    # Keep sync for backward compatibility
    def call_llm(self, prompt: str, ...) -> dict:
        """Synchronous LLM call (existing)."""
        return self._sync_client.messages.create(...)

    # Add async version
    async def call_llm_async(self, prompt: str, ...) -> dict:
        """Asynchronous LLM call."""
        return await self._async_client.messages.create(...)

    # Sync execute (existing)
    def execute(self, input_data: BaseModel) -> BaseModel:
        ...

    # Async execute (new)
    async def execute_async(self, input_data: BaseModel) -> BaseModel:
        """Async version of execute. Override in subclasses."""
        # Default: run sync version in executor (compatibility)
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.execute, input_data)
```

### 2. Async Agent Pattern

**File:** `src/asp/agents/code_agent.py` (example)

```python
class CodeAgent(BaseAgent):
    # Existing sync method
    def execute(self, input_data: CodeInput) -> GeneratedCode:
        prompt = self._build_prompt(input_data)
        response = self.call_llm(prompt)
        return self._parse_response(response)

    # New async method
    async def execute_async(self, input_data: CodeInput) -> GeneratedCode:
        prompt = self._build_prompt(input_data)
        response = await self.call_llm_async(prompt)
        return self._parse_response(response)
```

### 3. Parallel Agent Execution

**File:** `src/asp/orchestrators/parallel.py` (new)

```python
import asyncio
from typing import TypeVar, Callable, Awaitable

T = TypeVar('T')

async def gather_with_concurrency(
    limit: int,
    *tasks: Awaitable[T],
) -> list[T]:
    """
    Run tasks with concurrency limit.

    Args:
        limit: Max concurrent tasks (0 = unlimited)
        tasks: Awaitables to execute

    Returns:
        Results in same order as input tasks
    """
    if limit <= 0:
        return await asyncio.gather(*tasks)

    semaphore = asyncio.Semaphore(limit)

    async def limited_task(task: Awaitable[T]) -> T:
        async with semaphore:
            return await task

    return await asyncio.gather(*[limited_task(t) for t in tasks])


async def run_agents_parallel(
    agents: list[BaseAgent],
    inputs: list[BaseModel],
    max_concurrent: int = 5,
) -> list[BaseModel]:
    """
    Run multiple agents in parallel.

    Args:
        agents: List of agents to run
        inputs: Corresponding inputs for each agent
        max_concurrent: Max concurrent LLM calls

    Returns:
        Results from each agent
    """
    tasks = [
        agent.execute_async(input_data)
        for agent, input_data in zip(agents, inputs)
    ]
    return await gather_with_concurrency(max_concurrent, *tasks)
```

### 4. Async Orchestrator Pattern

**File:** `src/asp/orchestrators/tsp_orchestrator.py` (modified)

```python
class TSPOrchestrator:
    # Keep sync for backward compatibility
    def execute(self, request: TSPRequest) -> TSPExecutionResult:
        """Synchronous execution (existing)."""
        return asyncio.run(self.execute_async(request))

    async def execute_async(self, request: TSPRequest) -> TSPExecutionResult:
        """
        Async execution with parallel stages where possible.

        Pipeline:
        1. Planning (sequential - need plan first)
        2. Design (sequential - need to follow plan)
        3. Code Generation (parallel - multiple files)
        4. Code Review (parallel - multiple reviewers)
        5. Testing (sequential - need all code first)
        6. Postmortem (sequential)
        """
        # Phase 1-2: Sequential planning and design
        plan = await self.planning_agent.execute_async(request.requirements)
        design = await self.design_agent.execute_async(plan)

        # Phase 3: Parallel code generation
        code_tasks = [
            self.code_agent.execute_async(CodeInput(file=f, design=design))
            for f in design.files_to_generate
        ]
        generated_files = await gather_with_concurrency(
            self.config.max_concurrent_codegen,
            *code_tasks,
        )

        # Phase 4: Parallel code review
        review_tasks = [
            self.review_agent.execute_async(ReviewInput(code=code))
            for code in generated_files
        ]
        reviews = await gather_with_concurrency(
            self.config.max_concurrent_reviews,
            *review_tasks,
        )

        # Phase 5-6: Sequential testing and postmortem
        test_result = await self.test_executor.run_tests_async(workspace)
        postmortem = await self.postmortem_agent.execute_async(...)

        return TSPExecutionResult(...)
```

### 5. Async Services

**File:** `src/services/sandbox_executor.py`

```python
class SubprocessSandboxExecutor:
    def execute(self, workspace: Workspace, command: list[str]) -> ExecutionResult:
        """Synchronous execution (existing)."""
        # ... existing implementation ...

    async def execute_async(
        self,
        workspace: Workspace,
        command: list[str],
    ) -> ExecutionResult:
        """Asynchronous subprocess execution."""
        process = await asyncio.create_subprocess_exec(
            *command,
            cwd=workspace.target_repo_path,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            preexec_fn=self._set_limits,
        )

        try:
            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=self.config.timeout_seconds,
            )
            return ExecutionResult(
                exit_code=process.returncode,
                stdout=stdout.decode(),
                stderr=stderr.decode(),
                timed_out=False,
            )
        except asyncio.TimeoutError:
            process.kill()
            return ExecutionResult(exit_code=-1, timed_out=True, ...)
```

### 6. Configuration

**File:** `src/asp/config.py`

```python
@dataclass
class AsyncConfig:
    """Configuration for async execution."""

    # Concurrency limits
    max_concurrent_llm_calls: int = 5      # Respect API rate limits
    max_concurrent_codegen: int = 3        # Parallel file generation
    max_concurrent_reviews: int = 4        # Parallel code reviews
    max_concurrent_tests: int = 1          # Usually sequential

    # Timeouts
    llm_call_timeout: float = 120.0        # 2 minutes per LLM call
    subprocess_timeout: float = 300.0      # 5 minutes for tests

    # Behavior
    prefer_async: bool = True              # Use async when available
    fallback_to_sync: bool = True          # Fall back if async fails
```

---

## Migration Strategy

### Phase 1: Foundation (Non-Breaking)

Add async capabilities without breaking existing sync code:

1. Add `AsyncAnthropic` client to `BaseAgent`
2. Add `call_llm_async()` method
3. Add `execute_async()` with default sync fallback
4. All existing code continues to work unchanged

### Phase 2: Async Agents (Opt-In)

Convert agents to native async one by one:

1. `DiagnosticAgent.execute_async()` - independent, safe to start
2. `RepairAgent.execute_async()` - already used in async orchestrator
3. `CodeAgent.execute_async()` - enables parallel codegen
4. `TestAgent.execute_async()` - enables parallel test analysis
5. ...remaining agents...

### Phase 3: Async Services

Convert blocking services:

1. `SandboxExecutor.execute_async()` - uses `asyncio.create_subprocess_exec`
2. `TestExecutor.run_tests_async()` - wraps async sandbox
3. `SurgicalEditor.apply_changes_async()` - async file I/O with `aiofiles`

### Phase 4: Async Orchestrators

Update orchestrators to use async:

1. `TSPOrchestrator.execute_async()` - parallel codegen, reviews
2. `PlanningDesignOrchestrator.execute_async()` - parallel specialists
3. `ImprovementLoopOrchestrator.run_async()` - async iteration

### Phase 5: CLI Integration

Update CLI to support async:

```python
# src/asp/cli/main.py
import asyncio

@cli.command()
def repair(issue_url: str):
    """Run repair workflow."""
    result = asyncio.run(orchestrator.repair_from_issue_async(...))
    # ... handle result ...
```

---

## Compatibility Patterns

### Pattern 1: Dual Interface

Provide both sync and async versions:

```python
class MyAgent(BaseAgent):
    def execute(self, input_data: Input) -> Output:
        """Sync interface (backward compatible)."""
        return asyncio.run(self.execute_async(input_data))

    async def execute_async(self, input_data: Input) -> Output:
        """Async interface (new)."""
        # Native async implementation
        ...
```

### Pattern 2: Sync Wrapper

For callers that must remain sync:

```python
def sync_wrapper(async_func: Callable[..., Awaitable[T]]) -> Callable[..., T]:
    """Wrap async function for sync callers."""
    @functools.wraps(async_func)
    def wrapper(*args, **kwargs):
        return asyncio.run(async_func(*args, **kwargs))
    return wrapper
```

### Pattern 3: Run in Executor

For sync code that must be called from async context:

```python
async def call_sync_from_async(sync_func: Callable[..., T], *args) -> T:
    """Run sync function in thread pool from async context."""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, sync_func, *args)
```

---

## Rate Limiting and Backpressure

### LLM API Rate Limits

```python
class RateLimitedLLMClient:
    """LLM client with rate limiting."""

    def __init__(
        self,
        client: AsyncAnthropic,
        requests_per_minute: int = 60,
        tokens_per_minute: int = 100000,
    ):
        self.client = client
        self.request_semaphore = asyncio.Semaphore(requests_per_minute)
        self.token_bucket = TokenBucket(tokens_per_minute)

    async def create_message(self, **kwargs) -> Message:
        async with self.request_semaphore:
            await self.token_bucket.acquire(kwargs.get('max_tokens', 1000))
            return await self.client.messages.create(**kwargs)
```

### Backpressure for Task Queues

```python
class BoundedTaskQueue:
    """Task queue with backpressure."""

    def __init__(self, max_pending: int = 100):
        self.queue = asyncio.Queue(maxsize=max_pending)
        self.workers: list[asyncio.Task] = []

    async def submit(self, coro: Awaitable[T]) -> asyncio.Future[T]:
        """Submit task, blocks if queue is full."""
        future = asyncio.Future()
        await self.queue.put((coro, future))
        return future

    async def _worker(self):
        while True:
            coro, future = await self.queue.get()
            try:
                result = await coro
                future.set_result(result)
            except Exception as e:
                future.set_exception(e)
            finally:
                self.queue.task_done()
```

---

## Error Handling

### Async Exception Patterns

```python
async def robust_parallel_execution(
    tasks: list[Awaitable[T]],
    return_exceptions: bool = False,
) -> list[T | Exception]:
    """
    Run tasks with robust error handling.

    Args:
        tasks: Awaitables to execute
        return_exceptions: If True, return exceptions instead of raising

    Returns:
        Results (or exceptions if return_exceptions=True)
    """
    results = await asyncio.gather(*tasks, return_exceptions=True)

    if not return_exceptions:
        # Check for exceptions and raise the first one
        for result in results:
            if isinstance(result, Exception):
                raise result

    return results


async def retry_with_backoff(
    coro_factory: Callable[[], Awaitable[T]],
    max_retries: int = 3,
    base_delay: float = 1.0,
) -> T:
    """Retry async operation with exponential backoff."""
    last_exception = None

    for attempt in range(max_retries):
        try:
            return await coro_factory()
        except Exception as e:
            last_exception = e
            if attempt < max_retries - 1:
                delay = base_delay * (2 ** attempt)
                await asyncio.sleep(delay)

    raise last_exception
```

---

## Testing Async Code

### pytest-asyncio Configuration

```ini
# pytest.ini
[pytest]
asyncio_mode = auto
```

### Async Test Patterns

```python
import pytest

@pytest.mark.asyncio
async def test_agent_execute_async():
    """Test async agent execution."""
    agent = CodeAgent(...)
    result = await agent.execute_async(input_data)
    assert result.code is not None


@pytest.mark.asyncio
async def test_parallel_execution():
    """Test parallel agent execution."""
    agents = [CodeAgent(...) for _ in range(3)]
    inputs = [CodeInput(...) for _ in range(3)]

    results = await run_agents_parallel(agents, inputs)

    assert len(results) == 3
    assert all(r.code for r in results)


@pytest.mark.asyncio
async def test_rate_limiting():
    """Test that rate limiting is respected."""
    client = RateLimitedLLMClient(max_requests_per_minute=10)

    start = time.time()
    tasks = [client.create_message(...) for _ in range(20)]
    await asyncio.gather(*tasks)
    elapsed = time.time() - start

    # Should take at least 1 minute for 20 requests at 10/min
    assert elapsed >= 60
```

---

## File Summary

### New Files

| File | Description |
|------|-------------|
| `src/asp/orchestrators/parallel.py` | Parallel execution utilities |
| `src/asp/services/rate_limiter.py` | Rate limiting for API calls |
| `tests/unit/test_async_execution.py` | Async execution tests |

### Modified Files

| File | Change |
|------|--------|
| `src/asp/agents/base_agent.py` | Add async client and methods |
| `src/asp/agents/*.py` | Add `execute_async()` methods |
| `src/services/sandbox_executor.py` | Add `execute_async()` |
| `src/services/test_executor.py` | Add `run_tests_async()` |
| `src/asp/orchestrators/*.py` | Add async orchestration |
| `src/asp/config.py` | Add `AsyncConfig` |

---

## Consequences

### Positive

✅ **Improved Throughput** - Parallel LLM calls reduce wall-clock time
✅ **Better Resource Utilization** - Use I/O wait time productively
✅ **Incremental Migration** - Dual interface allows gradual adoption
✅ **Rate Limit Compliance** - Built-in rate limiting for API calls
✅ **Scalability** - Foundation for distributed execution later

### Negative

⚠️ **Complexity** - Async code is harder to debug
⚠️ **Learning Curve** - Team needs async/await familiarity
⚠️ **Testing Complexity** - Need pytest-asyncio, async fixtures
⚠️ **Potential Race Conditions** - Shared state requires careful handling

### Risks

| Risk | Mitigation |
|------|------------|
| Race conditions | Avoid shared mutable state; use locks where needed |
| Deadlocks | Use timeouts on all waits; avoid nested locks |
| Resource exhaustion | Semaphores and bounded queues for backpressure |
| API rate limit violations | Built-in rate limiting client |
| Debug difficulty | Structured logging with correlation IDs |

---

## Open Questions

1. **Event Loop Management** - Should we use a single global event loop or create per-request loops?

2. **Cancellation** - How should we handle task cancellation when a parent operation times out?

3. **Monitoring** - How do we trace async operations in Langfuse?

4. **Worker Pools** - Should we use process pools for CPU-bound work (e.g., parsing)?

5. **Streaming** - Should LLM responses stream for better UX?

---

## Implementation Priority

| Priority | Component | Benefit | Effort |
|----------|-----------|---------|--------|
| 1 | Async LLM calls | High | Low |
| 2 | Parallel code review | High | Medium |
| 3 | Parallel codegen | Medium | Medium |
| 4 | Async subprocess | Medium | Low |
| 5 | Rate limiting | Medium | Medium |
| 6 | Full orchestrator async | High | High |

---

## Related Documents

- `design/ADR_006_repair_workflow_architecture.md` - RepairOrchestrator already uses async
- `design/ADR_007_github_cli_integration.md` - Will benefit from async subprocess calls

---

**Status:** Proposed
**Next Steps:** Review, then begin Phase 1 (async LLM calls)
