# ADR 015: Wide Events Logging Philosophy

**Status:** Draft
**Date:** 2025-12-22
**Session:** 20251222.1
**Deciders:** User, Claude
**Related:** ADR 013 (Logfire Migration)

## Context and Problem Statement

ASP currently uses a mix of:
1. **Scattered `logger.info()`/`logger.debug()` calls** throughout agent code
2. **Telemetry decorators** (`@track_agent_cost`) for span-based tracing
3. **Logfire/Langfuse** for centralized observability

This follows traditional logging patterns that have fundamental problems in distributed/agent systems:

### Current Logging Pattern (Anti-Pattern)

```python
class PlanningAgent(BaseAgent):
    async def execute(self, task: Task) -> PlanResult:
        logger.info(f"Starting planning for task {task.id}")
        logger.debug(f"Task description: {task.description}")

        # ... LLM call ...
        logger.info(f"LLM returned {len(response.content)} chars")

        # ... validation ...
        logger.debug(f"Validating plan structure")

        # ... decomposition ...
        logger.info(f"Decomposed into {len(subtasks)} subtasks")

        # ... save ...
        logger.info(f"Planning complete for {task.id}")
        return result
```

**Problems with this approach:**

| Issue | Impact |
|-------|--------|
| **6+ log lines per request** | Volume without value |
| **Lost context** | Can't correlate start/end/intermediate logs |
| **Text search only** | "What requests had >3 subtasks?" impossible |
| **Debugging pain** | Must grep across scattered logs |
| **No high-cardinality fields** | Can't filter by user_id, model, cost |

### Reference: loggingsucks.com Philosophy

The [loggingsucks.com](https://loggingsucks.com) manifesto identifies the core problem:

> "Instead of logging _what your code is doing_, log _what happened to this request_."

**Key principles:**
1. **Wide Events**: One comprehensive event per operation (not 13 scattered logs)
2. **High Cardinality**: Include user_id, request_id, model, cost—fields with many unique values
3. **Structured Data**: JSON/key-value pairs, not free-form strings
4. **Tail Sampling**: 100% of errors/slow/important, 1-5% of routine successes
5. **Business Context**: User tier, feature flags, deployment info

## Decision Drivers

1. **Agent Debugging** - Single event should capture entire agent execution context
2. **Cost Attribution** - Need to query "how much did user X spend?" instantly
3. **Performance Analysis** - Filter by p99 latency, model, agent type
4. **Logfire Integration** - ADR 013 provides the backend; this provides the philosophy
5. **Reduced Noise** - Fewer log lines = easier debugging
6. **High-Cardinality Queries** - "Show all Claude Opus 4 calls >$0.10" should be fast

## Proposed Architecture

### Wide Event Model for ASP Agents

```
Current: Scattered Logs (6+ per request)
┌─────────────────────────────────────────────────────────────┐
│ logger.info("Starting planning for task-123")               │
│ logger.debug("Task description: ...")                       │
│ logger.info("LLM returned 2500 chars")                      │
│ logger.debug("Validating plan structure")                   │
│ logger.info("Decomposed into 5 subtasks")                   │
│ logger.info("Planning complete for task-123")               │
└─────────────────────────────────────────────────────────────┘
                              ↓
Proposed: Wide Event (1 per request)
┌─────────────────────────────────────────────────────────────┐
│ {                                                           │
│   "event": "agent.execution",                               │
│   "agent_type": "PlanningAgent",                            │
│   "task_id": "task-123",                                    │
│   "user_id": "user-456",                                    │
│   "session_id": "session-789",                              │
│                                                             │
│   // Timing                                                 │
│   "duration_ms": 3420,                                      │
│   "llm_latency_ms": 2800,                                   │
│                                                             │
│   // LLM Details                                            │
│   "model": "claude-sonnet-4-20250514",                      │
│   "provider": "anthropic",                                  │
│   "tokens_in": 1250,                                        │
│   "tokens_out": 890,                                        │
│   "cost_usd": 0.0234,                                       │
│                                                             │
│   // Business Context                                       │
│   "subtasks_created": 5,                                    │
│   "complexity_score": 3,                                    │
│   "retry_count": 0,                                         │
│                                                             │
│   // Outcome                                                │
│   "success": true,                                          │
│   "error_type": null,                                       │
│   "error_message": null                                     │
│ }                                                           │
└─────────────────────────────────────────────────────────────┘
```

### Implementation Pattern: Event Builder

Replace scattered logs with event enrichment:

```python
from asp.telemetry.wide_events import WideEvent

class PlanningAgent(BaseAgent):
    async def execute(self, task: Task) -> PlanResult:
        # Create event at start, enrich throughout, emit at end
        event = WideEvent("agent.execution")
        event.set(
            agent_type="PlanningAgent",
            task_id=task.id,
            user_id=self.user_id,
            session_id=self.session_id,
        )

        try:
            # LLM call - timing captured automatically
            with event.timed("llm_latency_ms"):
                response = await self.llm.generate(prompt)

            # Enrich with LLM details
            event.set(
                model=response.model,
                provider="anthropic",
                tokens_in=response.usage.input_tokens,
                tokens_out=response.usage.output_tokens,
                cost_usd=self.calculate_cost(response.usage),
            )

            # Business logic
            subtasks = self.decompose(response)
            event.set(
                subtasks_created=len(subtasks),
                complexity_score=task.complexity,
            )

            event.set(success=True)
            return PlanResult(subtasks=subtasks)

        except Exception as e:
            event.set(
                success=False,
                error_type=type(e).__name__,
                error_message=str(e),
            )
            raise
        finally:
            # Single emission point
            event.emit()
```

### Component 1: WideEvent Class

**File:** `src/asp/telemetry/wide_events.py`

```python
"""
Wide Events implementation for ASP.

Replaces scattered logging with single comprehensive events per operation.
Based on https://loggingsucks.com philosophy.
"""

import time
from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Any

import logfire

from .config import get_telemetry_provider


class WideEvent:
    """
    A wide event that accumulates context throughout an operation.

    Usage:
        event = WideEvent("agent.execution")
        event.set(agent_type="PlanningAgent", task_id="123")

        with event.timed("llm_latency_ms"):
            response = await llm.generate(...)

        event.set(tokens_in=response.usage.input_tokens)
        event.emit()  # Single emission point
    """

    def __init__(self, name: str):
        self.name = name
        self.start_time = time.time()
        self.attributes: dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        self._timers: dict[str, float] = {}
        self._emitted = False

    def set(self, **kwargs) -> "WideEvent":
        """Add attributes to the event."""
        self.attributes.update(kwargs)
        return self

    @contextmanager
    def timed(self, field_name: str):
        """Time a block and add duration to event."""
        start = time.time()
        try:
            yield
        finally:
            duration_ms = (time.time() - start) * 1000
            self.attributes[field_name] = round(duration_ms, 2)

    def emit(self) -> None:
        """Emit the wide event."""
        if self._emitted:
            return

        # Add total duration
        self.attributes["duration_ms"] = round(
            (time.time() - self.start_time) * 1000, 2
        )

        provider = get_telemetry_provider()

        if provider == "logfire":
            # Use Logfire's structured logging
            logfire.info(
                self.name,
                **self.attributes,
                _tags=self._generate_tags(),
            )
        elif provider == "langfuse":
            # Fallback to Langfuse event
            from langfuse import Langfuse
            langfuse = Langfuse()
            langfuse.event(name=self.name, metadata=self.attributes)

        self._emitted = True

    def _generate_tags(self) -> list[str]:
        """Generate tags from high-cardinality fields."""
        tags = []
        if "agent_type" in self.attributes:
            tags.append(f"agent:{self.attributes['agent_type']}")
        if "user_id" in self.attributes:
            tags.append(f"user:{self.attributes['user_id']}")
        if "model" in self.attributes:
            tags.append(f"model:{self.attributes['model']}")
        if "success" in self.attributes:
            status = "ok" if self.attributes["success"] else "error"
            tags.append(f"status:{status}")
        return tags


class AgentEvent(WideEvent):
    """Pre-configured wide event for agent execution."""

    def __init__(
        self,
        agent_type: str,
        task_id: str,
        user_id: str | None = None,
        session_id: str | None = None,
    ):
        super().__init__("agent.execution")
        self.set(
            agent_type=agent_type,
            task_id=task_id,
            user_id=user_id or "anonymous",
            session_id=session_id,
        )


class LLMCallEvent(WideEvent):
    """Pre-configured wide event for LLM API calls."""

    def __init__(
        self,
        provider: str,
        model: str,
        operation: str = "generate",
    ):
        super().__init__("llm.call")
        self.set(
            provider=provider,
            model=model,
            operation=operation,
        )

    def record_usage(
        self,
        tokens_in: int,
        tokens_out: int,
        cost_usd: float,
    ) -> "LLMCallEvent":
        """Record token usage and cost."""
        return self.set(
            tokens_in=tokens_in,
            tokens_out=tokens_out,
            cost_usd=cost_usd,
        )
```

### Component 2: Agent Decorator Update

Update `@track_agent_cost` to use wide events:

```python
def track_agent_execution(
    agent_type: str,
    task_id_param: str = "task_id",
):
    """
    Decorator that wraps agent execution with a wide event.

    Automatically captures:
    - Duration (total and LLM-specific)
    - Token usage and cost
    - Success/failure
    - Error details on failure
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def async_wrapper(self, *args, **kwargs):
            # Extract task_id from args/kwargs
            task_id = _extract_task_id(func, (self,) + args, kwargs, task_id_param)

            event = AgentEvent(
                agent_type=agent_type,
                task_id=task_id,
                user_id=getattr(self, "user_id", None),
                session_id=getattr(self, "session_id", None),
            )

            try:
                result = await func(self, *args, **kwargs)

                # Extract LLM usage if available
                if hasattr(self, "_last_llm_usage"):
                    usage = self._last_llm_usage
                    event.set(
                        model=usage.get("model"),
                        provider=usage.get("provider"),
                        tokens_in=usage.get("input_tokens", 0),
                        tokens_out=usage.get("output_tokens", 0),
                        cost_usd=usage.get("cost", 0),
                    )

                event.set(success=True)
                return result

            except Exception as e:
                event.set(
                    success=False,
                    error_type=type(e).__name__,
                    error_message=str(e),
                )
                raise
            finally:
                event.emit()

        return async_wrapper
    return decorator
```

### Component 3: Tail Sampling Configuration

Control costs while preserving debuggability:

```python
# src/asp/telemetry/sampling.py

from dataclasses import dataclass
from typing import Callable
import random


@dataclass
class SamplingConfig:
    """
    Tail sampling configuration for wide events.

    Preserves 100% of important events while sampling routine successes.
    """

    # Always keep these (100% sampling)
    keep_errors: bool = True
    keep_slow_requests_p99: bool = True
    keep_high_cost: bool = True
    high_cost_threshold_usd: float = 0.50

    # Sample rate for routine successes
    success_sample_rate: float = 0.05  # 5%

    def should_emit(self, event: "WideEvent") -> bool:
        """Determine if event should be emitted based on sampling rules."""
        attrs = event.attributes

        # Always keep errors
        if self.keep_errors and not attrs.get("success", True):
            return True

        # Always keep high-cost operations
        if self.keep_high_cost:
            cost = attrs.get("cost_usd", 0)
            if cost >= self.high_cost_threshold_usd:
                return True

        # Sample routine successes
        return random.random() < self.success_sample_rate


# Default configuration
DEFAULT_SAMPLING = SamplingConfig()
```

## Standard Event Types

### Agent Execution Events

| Field | Type | Description |
|-------|------|-------------|
| `event` | string | `"agent.execution"` |
| `agent_type` | string | Agent class name |
| `task_id` | string | Task identifier |
| `user_id` | string | User identifier |
| `session_id` | string | Session identifier |
| `duration_ms` | float | Total execution time |
| `llm_latency_ms` | float | LLM API call time |
| `model` | string | LLM model used |
| `provider` | string | LLM provider |
| `tokens_in` | int | Input tokens |
| `tokens_out` | int | Output tokens |
| `cost_usd` | float | API cost |
| `retry_count` | int | Number of retries |
| `success` | bool | Execution success |
| `error_type` | string? | Exception class name |
| `error_message` | string? | Error message |

### LLM Call Events

| Field | Type | Description |
|-------|------|-------------|
| `event` | string | `"llm.call"` |
| `provider` | string | anthropic, openai, etc. |
| `model` | string | Full model ID |
| `operation` | string | generate, embed, etc. |
| `tokens_in` | int | Input tokens |
| `tokens_out` | int | Output tokens |
| `cost_usd` | float | API cost |
| `latency_ms` | float | API latency |
| `stop_reason` | string | end_turn, max_tokens, etc. |
| `success` | bool | Call success |

### MCP Tool Events

| Field | Type | Description |
|-------|------|-------------|
| `event` | string | `"mcp.tool_call"` |
| `tool_name` | string | Tool identifier |
| `mcp_server` | string | Server name |
| `session_id` | string | Claude Code session |
| `duration_ms` | float | Tool execution time |
| `success` | bool | Tool success |
| `error_type` | string? | Error class |

## Migration Plan

### Phase 1: Add Wide Events Infrastructure

| Task | Description |
|------|-------------|
| 1.1 | Create `telemetry/wide_events.py` |
| 1.2 | Create `telemetry/sampling.py` |
| 1.3 | Add `AgentEvent`, `LLMCallEvent` classes |
| 1.4 | Unit tests for wide event emission |

### Phase 2: Update Agent Base Class

| Task | Description |
|------|-------------|
| 2.1 | Add `WideEvent` to `BaseAgent.execute()` |
| 2.2 | Update `@track_agent_execution` decorator |
| 2.3 | Remove scattered `logger.info()` calls |
| 2.4 | Preserve `logger.debug()` for development |

### Phase 3: Update LLM Client

| Task | Description |
|------|-------------|
| 3.1 | Add `LLMCallEvent` to `LLMClient.generate()` |
| 3.2 | Capture token usage, cost, latency |
| 3.3 | Record stop reason, retry attempts |

### Phase 4: Update MCP Server

| Task | Description |
|------|-------------|
| 4.1 | Add wide events to MCP tool handlers |
| 4.2 | Update Claude Code hooks |
| 4.3 | Remove scattered logs from hooks |

### Phase 5: Documentation & Queries

| Task | Description |
|------|-------------|
| 5.1 | Document standard event types |
| 5.2 | Create Logfire saved queries |
| 5.3 | Update KNOWLEDGE_BASE.md |

## Logfire Queries for Wide Events

```sql
-- Agent performance by type (last 24h)
SELECT
    agent_type,
    COUNT(*) as executions,
    AVG(duration_ms) as avg_duration,
    PERCENTILE_CONT(0.99) WITHIN GROUP (ORDER BY duration_ms) as p99,
    SUM(cost_usd) as total_cost
FROM events
WHERE event = 'agent.execution'
  AND timestamp > NOW() - INTERVAL '24 hours'
GROUP BY agent_type
ORDER BY total_cost DESC;

-- Failed agent executions with context
SELECT
    timestamp,
    agent_type,
    task_id,
    user_id,
    error_type,
    error_message,
    duration_ms,
    model
FROM events
WHERE event = 'agent.execution'
  AND success = false
ORDER BY timestamp DESC
LIMIT 50;

-- High-cost operations
SELECT
    timestamp,
    agent_type,
    model,
    tokens_in,
    tokens_out,
    cost_usd,
    task_id
FROM events
WHERE event = 'agent.execution'
  AND cost_usd > 0.50
ORDER BY cost_usd DESC;

-- User spending by model
SELECT
    user_id,
    model,
    COUNT(*) as calls,
    SUM(cost_usd) as total_spent
FROM events
WHERE event IN ('agent.execution', 'llm.call')
GROUP BY user_id, model
ORDER BY total_spent DESC;
```

## Consequences

### Positive

- **Debuggability**: Single event contains full context
- **Query Power**: High-cardinality fields enable analytical queries
- **Reduced Noise**: 1 event vs 6+ log lines per operation
- **Cost Attribution**: Instant "how much did X spend?" answers
- **Logfire Synergy**: Wide events leverage Logfire's SQL explorer

### Negative

- **Migration Effort**: Must update all agents
- **Learning Curve**: New mental model for developers
- **Lost Granularity**: Intermediate steps not visible (use debug logs if needed)

### Neutral

- **Log Volume**: Similar bytes, fewer events
- **Storage Cost**: Wider events, fewer rows

## Compatibility with ADR 013

This ADR is **complementary** to ADR 013 (Logfire Migration):

| ADR 013 | ADR 015 |
|---------|---------|
| **Backend**: Logfire vs Langfuse | **Philosophy**: Wide events vs scattered logs |
| Where data goes | What data looks like |
| Infrastructure | Application pattern |

Both can be implemented together. Wide events are emitted via Logfire spans.

## References

- [loggingsucks.com](https://loggingsucks.com) - Core philosophy
- [Charity Majors: Canonical Log Lines](https://charity.wtf/2019/02/05/logs-vs-structured-events/) - Wide events concept
- [Honeycomb: High-Cardinality](https://www.honeycomb.io/blog/so-you-want-to-build-an-observability-tool) - Why cardinality matters
- [ADR 013](./ADR_013_logfire_telemetry_migration.md) - Logfire backend
- [OpenTelemetry Events](https://opentelemetry.io/docs/specs/otel/logs/) - OTel log events spec

---

**Status:** Draft
**Next Steps:**
1. Review and approve wide events philosophy
2. Implement WideEvent class and tests
3. Update BaseAgent with wide event pattern
4. Migrate agents incrementally
5. Create Logfire saved queries
