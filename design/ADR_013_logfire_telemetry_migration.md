# ADR 013: Migrate from Langfuse to Pydantic Logfire

**Status:** In Progress (Phase 2 Complete)
**Date:** 2025-12-18
**Session:** 20251218.2
**Deciders:** User, Claude
**Related:** ADR 012 (MCP Server + Telemetry Hooks)

## Context and Problem Statement

ASP currently uses **Langfuse** for observability (spans, traces, events). While Langfuse works, there are compelling reasons to consider **Pydantic Logfire**:

1. **Native Pydantic Integration** - ASP uses Pydantic extensively for models; Logfire provides built-in validation analytics
2. **OpenTelemetry Foundation** - Logfire is built on OTel, enabling vendor-neutral data export
3. **LLM Observability** - First-class support for Anthropic, OpenAI, and other LLM providers
4. **Python-First Design** - Rich display of Python objects, event-loop telemetry, profiling
5. **Real-Time Streaming** - "Pending spans" show activity as it happens, not just when complete

### Current State

```
Current: Langfuse
┌─────────────────────────────────────────────────────────────┐
│ ASP Agent                                                    │
│     │                                                        │
│     ▼                                                        │
│ @track_agent_cost decorator                                  │
│     │                                                        │
│     ├──► Langfuse.start_span()                              │
│     │         │                                              │
│     │         ▼                                              │
│     │    Langfuse Cloud ──► Dashboard                       │
│     │                                                        │
│     └──► SQLite (agent_cost_vector, defect_log)             │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

### Pain Points with Langfuse

| Issue | Impact |
|-------|--------|
| Separate from Pydantic ecosystem | No validation insights |
| Spans sent on completion only | Can't see in-progress work |
| Limited Python introspection | No event-loop visibility |
| API changes (v2 → v3) | Breaking changes in `tags` parameter |
| Closed-source dashboard | Limited customization |

## Decision Drivers

1. **Pydantic Synergy** - Leverage existing Pydantic models for telemetry
2. **OpenTelemetry Compatibility** - Export to any OTel backend
3. **Developer Experience** - Time-to-first-log under 5 minutes
4. **LLM Support** - Native Anthropic/OpenAI instrumentation
5. **Migration Simplicity** - Minimal code changes required
6. **Cost** - Competitive pricing or self-hostable

## Comparison: Langfuse vs Logfire

| Feature | Langfuse | Pydantic Logfire |
|---------|----------|------------------|
| **Foundation** | Custom SDK | OpenTelemetry |
| **Pydantic Integration** | None | Native (validation analytics) |
| **LLM Tracing** | Yes (manual) | Yes (auto-instrumentation) |
| **Pending Spans** | No | Yes (real-time) |
| **Python Objects** | JSON only | Rich display |
| **Event Loop** | No | Yes (asyncio visibility) |
| **Profiling** | No | Yes (code profiling) |
| **Database Queries** | No | Yes (SQLAlchemy, etc.) |
| **Self-Hosted** | Yes (open source) | No (SaaS only) |
| **Export** | Limited | Any OTel backend |
| **Pricing** | Free tier + paid | Free tier + paid |
| **License** | MIT (SDK) | MIT (SDK), Closed (platform) |

## Proposed Architecture

### Overview

```
Proposed: Logfire
┌─────────────────────────────────────────────────────────────┐
│ ASP Agent                                                    │
│     │                                                        │
│     ▼                                                        │
│ @track_agent_cost decorator (updated)                        │
│     │                                                        │
│     ├──► logfire.span() ──► Logfire Platform                │
│     │         │                     │                        │
│     │         │                     ▼                        │
│     │         │              Live Dashboard                  │
│     │         │              SQL Explorer                    │
│     │         │              Saved Searches                  │
│     │         │                                              │
│     │         └──► OTel Export (optional)                   │
│     │                   │                                    │
│     │                   ▼                                    │
│     │              Jaeger / Grafana / DataDog               │
│     │                                                        │
│     └──► SQLite (unchanged - local persistence)             │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

### Component 1: Logfire Configuration

**File:** `src/asp/telemetry/config.py`

```python
"""
Logfire configuration for ASP Platform.

Provides centralized telemetry configuration with environment-based settings.
"""

import os
from typing import Literal

import logfire

# Provider type
TelemetryProvider = Literal["logfire", "langfuse", "none"]


def get_telemetry_provider() -> TelemetryProvider:
    """Get configured telemetry provider."""
    provider = os.getenv("ASP_TELEMETRY_PROVIDER", "logfire").lower()
    if provider in ("logfire", "langfuse", "none"):
        return provider
    return "logfire"


def configure_logfire(
    service_name: str = "asp-platform",
    environment: str | None = None,
    send_to_logfire: bool = True,
) -> None:
    """
    Configure Logfire for the ASP platform.

    Args:
        service_name: Name of the service for tracing
        environment: Environment name (dev, staging, prod)
        send_to_logfire: Whether to send data to Logfire cloud
    """
    environment = environment or os.getenv("ASP_ENVIRONMENT", "development")

    logfire.configure(
        service_name=service_name,
        service_version=os.getenv("ASP_VERSION", "0.1.0"),
        environment=environment,
        send_to_logfire=send_to_logfire,
        console=os.getenv("ASP_TELEMETRY_CONSOLE", "false").lower() == "true",
        pydantic_plugin=logfire.PydanticPlugin(
            record="all",  # Record all Pydantic validations
        ),
    )

    # Auto-instrument common libraries
    logfire.instrument_httpx()  # HTTP client calls
    logfire.instrument_asyncpg()  # Async PostgreSQL (if used)
    logfire.instrument_sqlite3()  # SQLite queries


def configure_anthropic_instrumentation() -> None:
    """
    Enable automatic instrumentation for Anthropic API calls.

    This captures:
    - Request/response content
    - Token usage
    - Latency
    - Model selection
    """
    logfire.instrument_anthropic()


def configure_openai_instrumentation() -> None:
    """Enable automatic instrumentation for OpenAI API calls."""
    logfire.instrument_openai()
```

### Component 2: Updated Telemetry Module

**File:** `src/asp/telemetry/telemetry.py` (modified sections)

```python
"""
Telemetry Infrastructure for ASP Platform

Updated to support both Langfuse and Logfire backends.
"""

import functools
import os
import time
from collections.abc import Callable
from datetime import datetime, timezone
from typing import Any

import logfire

from .config import configure_logfire, get_telemetry_provider

# Lazy initialization
_initialized = False


def _ensure_initialized():
    """Ensure telemetry is initialized."""
    global _initialized
    if not _initialized:
        provider = get_telemetry_provider()
        if provider == "logfire":
            configure_logfire()
        _initialized = True


def track_agent_cost(
    agent_role: str,
    task_id_param: str = "task_id",
    llm_model: str | None = None,
    llm_provider: str | None = None,
    agent_version: str | None = None,
):
    """
    Decorator to track agent execution costs.

    Supports both Langfuse and Logfire backends based on ASP_TELEMETRY_PROVIDER.

    Args:
        agent_role: Agent role (Planning, Design, Code, etc.)
        task_id_param: Name of the task_id parameter in the function signature
        llm_model: Optional LLM model name
        llm_provider: Optional LLM provider name
        agent_version: Optional agent version

    Example:
        @track_agent_cost(agent_role="Planning", llm_model="claude-sonnet-4")
        async def plan_task(task_id: str, description: str) -> dict:
            return {"decomposed_tasks": [...]}
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            _ensure_initialized()
            task_id = _extract_task_id(func, args, kwargs, task_id_param)
            user_id = get_user_id()

            provider = get_telemetry_provider()

            if provider == "logfire":
                return await _track_with_logfire(
                    func, args, kwargs,
                    agent_role=agent_role,
                    task_id=task_id,
                    user_id=user_id,
                    llm_model=llm_model,
                    llm_provider=llm_provider,
                    agent_version=agent_version,
                )
            elif provider == "langfuse":
                return await _track_with_langfuse(
                    func, args, kwargs,
                    agent_role=agent_role,
                    task_id=task_id,
                    user_id=user_id,
                    llm_model=llm_model,
                    llm_provider=llm_provider,
                    agent_version=agent_version,
                )
            else:
                # No telemetry
                return await func(*args, **kwargs)

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            _ensure_initialized()
            task_id = _extract_task_id(func, args, kwargs, task_id_param)
            user_id = get_user_id()

            provider = get_telemetry_provider()

            if provider == "logfire":
                return _track_with_logfire_sync(
                    func, args, kwargs,
                    agent_role=agent_role,
                    task_id=task_id,
                    user_id=user_id,
                    llm_model=llm_model,
                    llm_provider=llm_provider,
                    agent_version=agent_version,
                )
            elif provider == "langfuse":
                return _track_with_langfuse_sync(
                    func, args, kwargs,
                    agent_role=agent_role,
                    task_id=task_id,
                    user_id=user_id,
                    llm_model=llm_model,
                    llm_provider=llm_provider,
                    agent_version=agent_version,
                )
            else:
                return func(*args, **kwargs)

        # Return appropriate wrapper based on function type
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    return decorator


async def _track_with_logfire(
    func: Callable,
    args: tuple,
    kwargs: dict,
    agent_role: str,
    task_id: str,
    user_id: str,
    llm_model: str | None,
    llm_provider: str | None,
    agent_version: str | None,
):
    """Track execution using Logfire."""
    with logfire.span(
        f"{agent_role}.{func.__name__}",
        _tags=[f"agent:{agent_role}", f"user:{user_id}"],
        task_id=task_id,
        user_id=user_id,
        agent_role=agent_role,
        llm_model=llm_model,
        llm_provider=llm_provider,
        agent_version=agent_version,
    ) as span:
        start_time = time.time()
        error = None

        try:
            result = await func(*args, **kwargs)

            # Extract LLM usage if available
            llm_usage = {}
            if args and hasattr(args[0], "_last_llm_usage"):
                llm_usage = args[0]._last_llm_usage

            # Log metrics
            latency_ms = (time.time() - start_time) * 1000

            span.set_attribute("latency_ms", latency_ms)
            span.set_attribute("success", True)

            if llm_usage:
                span.set_attribute("tokens_in", llm_usage.get("input_tokens", 0))
                span.set_attribute("tokens_out", llm_usage.get("output_tokens", 0))
                span.set_attribute("api_cost_usd", llm_usage.get("cost", 0))

            # Also log to SQLite for local persistence
            _log_to_sqlite(
                task_id=task_id,
                agent_role=agent_role,
                latency_ms=latency_ms,
                llm_usage=llm_usage,
                llm_model=llm_model,
                llm_provider=llm_provider,
                user_id=user_id,
                agent_version=agent_version,
            )

            return result

        except Exception as e:
            error = e
            span.set_attribute("success", False)
            span.set_attribute("error_type", type(e).__name__)
            span.set_attribute("error_message", str(e))
            logfire.error(f"Agent {agent_role} failed", exc_info=e)
            raise


def _track_with_logfire_sync(
    func: Callable,
    args: tuple,
    kwargs: dict,
    agent_role: str,
    task_id: str,
    user_id: str,
    llm_model: str | None,
    llm_provider: str | None,
    agent_version: str | None,
):
    """Track synchronous execution using Logfire."""
    with logfire.span(
        f"{agent_role}.{func.__name__}",
        _tags=[f"agent:{agent_role}", f"user:{user_id}"],
        task_id=task_id,
        user_id=user_id,
        agent_role=agent_role,
        llm_model=llm_model,
        llm_provider=llm_provider,
        agent_version=agent_version,
    ) as span:
        start_time = time.time()

        try:
            result = func(*args, **kwargs)

            llm_usage = {}
            if args and hasattr(args[0], "_last_llm_usage"):
                llm_usage = args[0]._last_llm_usage

            latency_ms = (time.time() - start_time) * 1000

            span.set_attribute("latency_ms", latency_ms)
            span.set_attribute("success", True)

            if llm_usage:
                span.set_attribute("tokens_in", llm_usage.get("input_tokens", 0))
                span.set_attribute("tokens_out", llm_usage.get("output_tokens", 0))
                span.set_attribute("api_cost_usd", llm_usage.get("cost", 0))

            _log_to_sqlite(
                task_id=task_id,
                agent_role=agent_role,
                latency_ms=latency_ms,
                llm_usage=llm_usage,
                llm_model=llm_model,
                llm_provider=llm_provider,
                user_id=user_id,
                agent_version=agent_version,
            )

            return result

        except Exception as e:
            span.set_attribute("success", False)
            span.set_attribute("error_type", type(e).__name__)
            logfire.error(f"Agent {agent_role} failed", exc_info=e)
            raise


def _log_to_sqlite(
    task_id: str,
    agent_role: str,
    latency_ms: float,
    llm_usage: dict,
    llm_model: str | None,
    llm_provider: str | None,
    user_id: str,
    agent_version: str | None,
):
    """Log metrics to SQLite for local persistence."""
    try:
        insert_agent_cost(
            task_id=task_id,
            agent_role=agent_role,
            metric_type="Latency",
            metric_value=latency_ms,
            metric_unit="ms",
            llm_model=llm_model,
            llm_provider=llm_provider,
            user_id=user_id,
            agent_version=agent_version,
        )

        if llm_usage.get("input_tokens"):
            insert_agent_cost(
                task_id=task_id,
                agent_role=agent_role,
                metric_type="Tokens_In",
                metric_value=llm_usage["input_tokens"],
                metric_unit="tokens",
                llm_model=llm_usage.get("model", llm_model),
                llm_provider=llm_provider,
                user_id=user_id,
                agent_version=agent_version,
            )

        if llm_usage.get("output_tokens"):
            insert_agent_cost(
                task_id=task_id,
                agent_role=agent_role,
                metric_type="Tokens_Out",
                metric_value=llm_usage["output_tokens"],
                metric_unit="tokens",
                llm_model=llm_usage.get("model", llm_model),
                llm_provider=llm_provider,
                user_id=user_id,
                agent_version=agent_version,
            )

        if llm_usage.get("cost"):
            insert_agent_cost(
                task_id=task_id,
                agent_role=agent_role,
                metric_type="API_Cost",
                metric_value=llm_usage["cost"],
                metric_unit="USD",
                llm_model=llm_usage.get("model", llm_model),
                llm_provider=llm_provider,
                user_id=user_id,
                agent_version=agent_version,
            )

    except Exception as e:
        logfire.warn(f"Failed to log to SQLite: {e}")
```

### Component 3: LLM Auto-Instrumentation

**File:** `src/asp/telemetry/llm.py`

```python
"""
LLM-specific instrumentation for Logfire.

Provides automatic tracing for Anthropic and OpenAI API calls.
"""

import logfire


def instrument_anthropic():
    """
    Instrument Anthropic API calls.

    Automatically captures:
    - Request content and parameters
    - Response content
    - Token usage (input, output, total)
    - Latency
    - Model selection
    - Stop reason
    """
    logfire.instrument_anthropic()


def instrument_openai():
    """
    Instrument OpenAI API calls.

    Automatically captures similar data to Anthropic instrumentation.
    """
    logfire.instrument_openai()


def instrument_all_llm_providers():
    """Instrument all supported LLM providers."""
    try:
        instrument_anthropic()
    except Exception:
        pass  # Anthropic SDK not installed

    try:
        instrument_openai()
    except Exception:
        pass  # OpenAI SDK not installed
```

### Component 4: Pydantic Validation Insights

**File:** `src/asp/telemetry/pydantic_plugin.py`

```python
"""
Pydantic plugin configuration for Logfire.

Captures validation events for ASP models.
"""

import logfire


def configure_pydantic_plugin(
    record: str = "all",
    include_schemas: list[str] | None = None,
):
    """
    Configure Pydantic validation recording.

    Args:
        record: What to record ("all", "failure", "metrics")
        include_schemas: List of schema names to include (None = all)

    This provides:
    - Validation success/failure events
    - Field-level validation errors
    - Validation timing
    - Schema usage analytics
    """
    logfire.configure(
        pydantic_plugin=logfire.PydanticPlugin(
            record=record,
            include={"*"} if include_schemas is None else set(include_schemas),
        )
    )


# ASP models that benefit from validation tracking
ASP_MODELS = [
    "TaskRequirements",
    "ProjectPlan",
    "CodeChange",
    "ReviewResult",
    "RepairResult",
    "TestResult",
]
```

### Component 5: Claude Code Hooks Integration

Update ADR 012 hooks to use Logfire:

**File:** `src/asp/hooks/telemetry.py` (updated)

```python
#!/usr/bin/env python3
"""
Universal telemetry hook for Claude Code.

Updated to use Logfire instead of Langfuse.
"""

import json
import os
import sys
from datetime import datetime, timezone

import logfire

# Initialize Logfire for hooks
logfire.configure(
    service_name="asp-claude-hooks",
    send_to_logfire=os.getenv("LOGFIRE_SEND", "true").lower() == "true",
)


def handle_pre_tool_use(input_data: dict) -> None:
    """Handle PreToolUse event using Logfire."""
    tool_name = input_data.get("tool_name", "unknown")
    tool_use_id = input_data.get("tool_use_id", "")
    session_id = input_data.get("session_id", "")
    tool_input = input_data.get("tool_input", {})

    # Determine tool type
    if tool_name.startswith("mcp__"):
        parts = tool_name.split("__")
        tool_type = "mcp"
        mcp_server = parts[1] if len(parts) > 1 else "unknown"
    elif tool_name == "Task":
        tool_type = "subagent"
        mcp_server = None
    else:
        tool_type = "builtin"
        mcp_server = None

    # Log to Logfire
    logfire.info(
        "Claude tool invoked: {tool_name}",
        tool_name=tool_name,
        tool_use_id=tool_use_id,
        session_id=session_id,
        tool_type=tool_type,
        mcp_server=mcp_server,
        input_keys=list(tool_input.keys()),
        _tags=[f"tool:{tool_name}", f"type:{tool_type}"],
    )


def handle_post_tool_use(input_data: dict) -> None:
    """Handle PostToolUse event using Logfire."""
    tool_name = input_data.get("tool_name", "unknown")
    tool_use_id = input_data.get("tool_use_id", "")
    session_id = input_data.get("session_id", "")
    tool_response = input_data.get("tool_response", {})

    is_error = False
    if isinstance(tool_response, dict):
        is_error = tool_response.get("is_error", False)

    if is_error:
        logfire.error(
            "Claude tool failed: {tool_name}",
            tool_name=tool_name,
            tool_use_id=tool_use_id,
            session_id=session_id,
        )
    else:
        logfire.info(
            "Claude tool completed: {tool_name}",
            tool_name=tool_name,
            tool_use_id=tool_use_id,
            session_id=session_id,
            success=True,
        )


def main():
    """Main entry point for hook."""
    if len(sys.argv) < 2:
        sys.exit(1)

    phase = sys.argv[1]

    try:
        input_data = json.load(sys.stdin)
    except json.JSONDecodeError:
        sys.exit(0)

    try:
        if phase == "pre":
            handle_pre_tool_use(input_data)
        elif phase == "post":
            handle_post_tool_use(input_data)
        sys.exit(0)
    except Exception as e:
        logfire.error(f"Hook error: {e}")
        sys.exit(0)


if __name__ == "__main__":
    main()
```

## Migration Plan

### Phase 1: Add Logfire Support (1 session) ✅ COMPLETE

| Task | Description | Status |
|------|-------------|--------|
| 1.1 | Add `logfire` to dependencies | ✅ Done |
| 1.2 | Create `telemetry/config.py` | ✅ Done |
| 1.3 | Add `ASP_TELEMETRY_PROVIDER` env var support | ✅ Done |
| 1.4 | Update `track_agent_cost` decorator | ✅ Done |
| 1.5 | Update `log_defect` decorator | ⏳ Pending |
| 1.6 | Test with both backends | ✅ Done (41 tests pass) |

**Commit:** a193af3

### Phase 2: LLM Auto-Instrumentation (1 session) ✅ COMPLETE

| Task | Description | Status |
|------|-------------|--------|
| 2.1 | Add Anthropic auto-instrumentation | ✅ Done |
| 2.2 | Add OpenAI auto-instrumentation | ✅ Done |
| 2.3 | Configure Pydantic plugin | ✅ Done |
| 2.4 | Update LLMClient to leverage instrumentation | ✅ Done |
| 2.5 | Test token/cost tracking | ✅ Done (41 tests pass) |

**Key additions:**
- `initialize_telemetry()` - main entry point for app startup
- `ensure_llm_instrumentation()` - called by LLMClient before Anthropic import
- LLMClient now auto-instruments when using Logfire provider

### Phase 3: Dashboard & Queries (1 session)

| Task | Description | Effort |
|------|-------------|--------|
| 3.1 | Set up Logfire project | Low |
| 3.2 | Create saved searches for agents | Medium |
| 3.3 | Create cost/token dashboards | Medium |
| 3.4 | Document SQL queries | Low |

### Phase 4: Deprecate Langfuse (Future)

| Task | Description | Effort |
|------|-------------|--------|
| 4.1 | Update documentation | Low |
| 4.2 | Remove Langfuse dependency | Low |
| 4.3 | Clean up dual-backend code | Medium |

## Configuration

### Environment Variables

```bash
# Telemetry provider selection
ASP_TELEMETRY_PROVIDER=logfire  # or "langfuse" or "none"

# Logfire configuration
LOGFIRE_TOKEN=<your-logfire-token>
LOGFIRE_PROJECT_NAME=asp-platform
LOGFIRE_ENVIRONMENT=development  # or staging, production

# Optional: Console output for debugging
ASP_TELEMETRY_CONSOLE=false

# Optional: Disable cloud sending (local only)
LOGFIRE_SEND=true
```

### Logfire Project Setup

```bash
# Install Logfire CLI
pip install logfire

# Authenticate
logfire auth

# Create project (or use existing)
logfire projects create asp-platform

# Configure environment
logfire config set project asp-platform
```

## Logfire Features for ASP

### 1. Real-Time Live View

See agent activity as it happens:
- Pending spans show work in progress
- No waiting for span completion
- Instant visibility into long-running agents

### 2. SQL Explorer

Query telemetry data directly:

```sql
-- Agent performance by role
SELECT
    attributes->>'agent_role' as role,
    AVG(CAST(attributes->>'latency_ms' AS FLOAT)) as avg_latency,
    COUNT(*) as invocations
FROM spans
WHERE span_name LIKE '%.execute%'
GROUP BY role
ORDER BY avg_latency DESC;

-- Token usage by model
SELECT
    attributes->>'llm_model' as model,
    SUM(CAST(attributes->>'tokens_in' AS INT)) as total_input,
    SUM(CAST(attributes->>'tokens_out' AS INT)) as total_output,
    SUM(CAST(attributes->>'api_cost_usd' AS FLOAT)) as total_cost
FROM spans
WHERE attributes->>'tokens_in' IS NOT NULL
GROUP BY model;
```

### 3. Pydantic Validation Insights

Automatic tracking of:
- Validation success/failure rates per model
- Common validation errors
- Schema usage patterns
- Validation latency

### 4. Exception Tracking

Rich exception display:
- Full stack traces
- Local variables
- Request context
- Error grouping

## Dependencies

### New Dependencies

```toml
# pyproject.toml
[project.dependencies]
logfire = ">=4.0.0"

[project.optional-dependencies]
telemetry = [
    "logfire[anthropic]",  # Anthropic auto-instrumentation
    "logfire[openai]",     # OpenAI auto-instrumentation
    "logfire[httpx]",      # HTTP client instrumentation
    "logfire[sqlite3]",    # SQLite query instrumentation
]
```

### Removed Dependencies (Phase 4)

```toml
# Remove in Phase 4
# langfuse  # No longer needed
```

## Risks and Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Logfire platform outage | No cloud telemetry | SQLite backup, OTel export option |
| API changes | Breaking changes | Pin version, monitor changelog |
| Pricing changes | Cost increase | Monitor usage, evaluate alternatives |
| No self-hosting | Vendor lock-in | OTel export to self-hosted backend |
| Learning curve | Adoption friction | Good documentation, gradual rollout |

## Alternatives Considered

### Alternative 1: Keep Langfuse Only

Continue with current Langfuse integration.

**Rejected because:**
- Missing Pydantic integration
- No pending spans (real-time visibility)
- Limited Python introspection
- API instability (v2→v3 breaking changes)

### Alternative 2: Pure OpenTelemetry

Use OTel SDK directly without Logfire wrapper.

**Rejected because:**
- More complex setup
- Requires separate backend (Jaeger, etc.)
- No Pydantic plugin
- More code to write

### Alternative 3: Dual Backend (Langfuse + Logfire)

Run both systems in parallel permanently.

**Rejected because:**
- Double the cost
- Maintenance overhead
- Confusing for users
- Data inconsistency

### Alternative 4: Self-Hosted OTel Backend

Use Jaeger, Grafana Tempo, or similar.

**Considered for future:**
- Good for cost control
- More complexity to operate
- Could use Logfire's OTel export

## Consequences

### Positive

- **Pydantic Integration** - Automatic validation insights
- **Real-Time Visibility** - Pending spans show work in progress
- **LLM Auto-Instrumentation** - Zero-config Anthropic/OpenAI tracing
- **Python-First** - Rich object display, event-loop visibility
- **OTel Foundation** - Export to any backend

### Negative

- **No Self-Hosting** - SaaS dependency for platform
- **New Dependency** - Another library to manage
- **Migration Effort** - Code changes required

### Neutral

- **Pricing** - Similar to Langfuse
- **Learning Curve** - Different but not harder

## References

- [Pydantic Logfire](https://pydantic.dev/logfire) - Official site
- [Logfire Documentation](https://logfire.pydantic.dev/docs/) - Full docs
- [Logfire GitHub](https://github.com/pydantic/logfire) - Open source SDK
- [Why Logfire?](https://pydantic.dev/articles/why-logfire) - Philosophy
- [Logfire LLM Integrations](https://logfire.pydantic.dev/docs/integrations/llms/) - LLM support
- [Langfuse Documentation](https://langfuse.com/docs) - Current system

---

**Status:** Draft
**Next Steps:**
1. Review and approve migration approach
2. Set up Logfire project and obtain token
3. Implement Phase 1 (dual-backend support)
4. Test and validate with existing workflows
5. Plan deprecation timeline for Langfuse
