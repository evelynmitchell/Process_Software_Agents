# ADR 003: OpenTelemetry Instrumentation for Reinforcement Learning Triplets

**Status:** Proposed
**Date:** 2025-12-03
**Session:** 20251203.1
**Deciders:** User, Claude

## Context and Problem Statement

The ASP platform needs comprehensive instrumentation to support reinforcement learning (RL) systems like Agent Lightning. RL requires capturing **(state, action, reward)** triplets at each decision point to learn optimal policies for agent behavior.

**Current State:**
- Langfuse integration exists for LLM observability (spans, events, usage)
- SQLite telemetry captures agent costs, latency, tokens, and defects
- `@track_agent_cost` decorator provides basic instrumentation

**Problem:** The current instrumentation is designed for observability, not RL. We need to capture structured triplets that include:
1. **State:** Complete context available when making a decision
2. **Action:** The result/output of the function call (success, error, LLM reply, tool output)
3. **Reward:** Signals indicating quality of the action

**Core Question:** How do we instrument the system to capture RL-ready triplets while maintaining compatibility with existing Langfuse/SQLite telemetry?

## Decision Drivers

1. **RL Compatibility:** Triplets must work with Agent Lightning's expected format
2. **Minimal Overhead:** Instrumentation should not significantly impact performance
3. **Existing Integration:** Complement (not replace) Langfuse and SQLite telemetry
4. **Completeness:** Capture sufficient context for RL training
5. **Flexibility:** Support different reward signals and sampling strategies
6. **Standard Protocol:** Use OpenTelemetry for interoperability

## RL Triplet Schema

### Design Principles

1. **State is flexible** - We don't control state typing in detail; capture what's available
2. **Action is the result** - Whatever the function call produced (success, error, output)
3. **Reward is continuous** - Float between 0.0 and 1.0, assigned immediately or later
4. **Sequence linking** - Triplets are linked for reward backpropagation

### Core Triplet Structure

```python
@dataclass
class RLTriplet:
    """
    Minimal triplet structure for Agent Lightning.

    Designed for flexibility - state and action are untyped dicts
    that capture whatever context is available at instrumentation time.
    """

    # === Identification ===
    triplet_id: str               # Unique ID for this triplet (UUID)
    sequence_id: str              # Links triplets in same workflow/episode
    sequence_index: int           # Order within sequence (for backpropagation)
    timestamp_utc: str            # ISO timestamp when triplet was created

    # === The Triplet ===
    state: dict                   # Context when action taken (flexible schema)
    action: dict                  # Result of the action (flexible schema)
    reward: float | None          # Continuous 0.0-1.0, initially None

    # === Reward Metadata ===
    reward_assigned_at: str | None    # When reward was assigned
    reward_source: str | None         # How reward was determined (see below)
```

### Sequence Scope Options

The `sequence_id` links triplets for reward attribution. The appropriate scope depends on the use case:

| Scope | sequence_id | Use Case |
|-------|-------------|----------|
| **Agent Execution** | `{task_id}:{agent_role}` | Learn per-agent behavior |
| **Pipeline Run** | `{task_id}` | Learn end-to-end workflow |
| **User Session** | `{session_id}` | Learn user interaction patterns |
| **Custom** | Caller-defined | Domain-specific grouping |

**Decision:** We will support all scopes. The decorator accepts a `sequence_scope` parameter, defaulting to pipeline (`task_id`).

### State (Flexible Dict)

The **state** captures context available when an action is taken. We are **agnostic about typing** - capture what's available and let the RL system determine what's useful.

**Possible state fields** (not exhaustive, not required):

```python
state = {
    # Request context
    "task_id": "TASK-001",
    "task_description": "Build authentication...",  # or hash
    "requirements": "...",  # or hash

    # Agent context
    "agent_role": "Planning",
    "agent_version": "1.0.0",
    "function_name": "execute",

    # LLM context (if applicable)
    "llm_model": "claude-sonnet-4-20250514",
    "prompt": "...",  # or hash
    "prompt_tokens": 1500,
    "temperature": 0.0,

    # Pipeline context
    "phase": "Planning",
    "iteration": 1,
    "prior_artifacts": ["plan.json", "design.json"],
    "feedback_items": 0,

    # System context
    "budget_remaining_pct": 0.85,
    "pending_approvals": 2,
    "active_agents": 1,

    # Trace context
    "trace_id": "abc123",
    "parent_span_id": "def456",
    "call_depth": 2,

    # ... any other available context
}
```

**Implementation:** The `@rl_triplet` decorator will capture whatever state is accessible at the instrumentation point. Different call sites may have different state available.

### Action (Flexible Dict)

The **action** captures the result of the function call - whatever it produced.

**Possible action fields** (not exhaustive):

```python
action = {
    # Outcome
    "success": True,
    "error_type": None,  # or "ValidationError", "TimeoutError", etc.
    "error_message": None,  # or hash of message

    # LLM response (if applicable)
    "llm_response": "...",  # or hash
    "llm_tokens_in": 1500,
    "llm_tokens_out": 500,
    "llm_stop_reason": "end_turn",

    # Artifact output (if applicable)
    "artifact_type": "plan",
    "artifact_id": "artifacts/TASK-001/plan.json",
    "artifact_size_bytes": 2048,
    "validation_passed": True,

    # API response (if applicable)
    "http_status": 200,
    "response_body": "...",  # or hash

    # Timing
    "duration_ms": 1250.5,

    # Output summary
    "output_size_bytes": 2048,
    "output_hash": "sha256:...",
}
```

### Reward (Continuous 0.0 - 1.0)

The **reward** is a single float value between 0.0 and 1.0, assigned either immediately or later via backpropagation.

```python
reward: float | None  # 0.0 = worst, 1.0 = best, None = not yet assigned
```

**Reward Attribution Strategies:**

| Strategy | When Assigned | Attribution | Example |
|----------|---------------|-------------|---------|
| **Terminal** | Pipeline end | Backprop to all triplets | Task succeeded → all get 0.8 |
| **Local** | Immediately | This triplet only | Tool call succeeded → 1.0 |
| **Informational** | Immediately | Context quality signal | LLM asked for clarification → 0.3 |
| **Manual/LLM-as-Judge** | Later | External evaluation | Human review → 0.9 |

**Possible Reward Signals** (we don't know which we'll use):

| Signal | Type | Interpretation |
|--------|------|----------------|
| Function success | Local | Did it execute without exception? |
| Validation pass | Local | Did Pydantic validation succeed? |
| Output non-empty | Local | Did it produce meaningful output? |
| Clarification requested | Informational | LLM asked for more info (negative signal) |
| Retry triggered | Informational | Needed multiple attempts (negative) |
| Feedback loop | Informational | Design review sent back to planning (negative) |
| Tests pass | Terminal | All tests passed at pipeline end |
| HITL approved | Terminal | Human approved without modification |
| Defects found | Terminal | Defects logged later (negative) |
| Code merged | Terminal | PR was merged successfully |

**Decision:** Reward assignment strategy is **not decided**. The system will:
1. Store triplets with `reward: None` initially
2. Provide APIs to assign rewards later (by triplet_id or sequence_id)
3. Support both immediate and delayed assignment

### Reference: Detailed Field Catalog

For implementers, here is a comprehensive catalog of fields we **could** capture. This is for reference - actual capture depends on what's available at each instrumentation point.

<details>
<summary>Expand: Full State Field Catalog</summary>

| Category | Field | Type | Source |
|----------|-------|------|--------|
| **Request** | task_id | str | TaskRequirements |
| | task_description | str/hash | TaskRequirements |
| | requirements | str/hash | TaskRequirements |
| | context_files | list[str] | TaskRequirements |
| **Agent** | agent_role | str | BaseAgent.agent_name |
| | agent_version | str | BaseAgent.agent_version |
| | function_name | str | func.__name__ |
| **LLM** | llm_model | str | decorator param |
| | llm_provider | str | decorator param |
| | prompt | str/hash | formatted_prompt |
| | prompt_tokens | int | tiktoken estimate |
| | temperature | float | call param |
| | max_tokens | int | call param |
| **Pipeline** | current_phase | str | orchestrator context |
| | iteration | int | loop counter |
| | prior_artifacts | list[str] | artifact paths |
| | feedback_count | int | len(feedback) |
| **System** | budget_remaining | float | get_budget_status() |
| | pending_approvals | int | get_tasks_pending_approval() |
| | active_agents | int | get_active_agents() |
| | recent_success_rate | float | computed from history |
| **Trace** | trace_id | str | OTEL context |
| | span_id | str | OTEL context |
| | parent_span_id | str | OTEL context |
| | call_depth | int | computed |
| **Time** | timestamp_utc | str | datetime.utcnow() |
| | wall_clock_ms | int | time.time() * 1000 |

</details>

<details>
<summary>Expand: Full Action Field Catalog</summary>

| Category | Field | Type | Source |
|----------|-------|------|--------|
| **Outcome** | success | bool | try/except |
| | error_type | str | type(e).__name__ |
| | error_message | str/hash | str(e) |
| **LLM** | response | str/hash | response["content"] |
| | tokens_in | int | response["usage"] |
| | tokens_out | int | response["usage"] |
| | stop_reason | str | response["stop_reason"] |
| | model_actual | str | response["model"] |
| **Artifact** | artifact_type | str | write_artifact param |
| | artifact_id | str | file path |
| | artifact_size | int | len(content) |
| | validation_passed | bool | model_validate() |
| | validation_errors | int | len(errors) |
| **API** | http_status | int | response.status_code |
| | endpoint | str/hash | request URL |
| **Timing** | duration_ms | float | end - start |
| **Output** | output_size | int | len(serialized) |
| | output_hash | str | sha256(output) |

</details>

## Considered Options

### Option 1: Extend Existing Langfuse Integration

Add RL triplet data as metadata on existing Langfuse spans.

```python
span = langfuse.start_span(
    name="PlanningAgent.execute",
    metadata={
        "rl_state": state.to_dict(),
        "rl_action": action.to_dict(),
        "rl_reward": reward.to_dict(),
    }
)
```

**Pros:**
- Minimal new infrastructure
- Leverages existing integration
- Single observability platform

**Cons:**
- Langfuse not designed for RL data
- Limited querying for RL-specific analysis
- May bloat span metadata
- Couples RL to observability tool choice

### Option 2: Separate SQLite Table for RL Triplets

Add new table to `asp_telemetry.db` for RL data.

```sql
CREATE TABLE rl_triplets (
    id INTEGER PRIMARY KEY,
    trace_id TEXT NOT NULL,
    span_id TEXT NOT NULL,
    timestamp TEXT NOT NULL,
    state_json TEXT NOT NULL,
    action_json TEXT NOT NULL,
    reward_json TEXT,  -- NULL until reward calculated
    UNIQUE(trace_id, span_id)
);
```

**Pros:**
- Simple, no new dependencies
- Queryable with SQL
- Consistent with existing telemetry

**Cons:**
- Not a standard protocol
- No distributed tracing correlation
- Harder to export to RL training systems

### Option 3: OpenTelemetry with Custom Attributes (RECOMMENDED)

Use OpenTelemetry SDK with structured attributes for RL triplets.

```python
from opentelemetry import trace
from opentelemetry.trace import Status, StatusCode

tracer = trace.get_tracer("asp.agents")

with tracer.start_as_current_span("PlanningAgent.execute") as span:
    # Set state attributes
    span.set_attribute("rl.state.task_id", state.task_id)
    span.set_attribute("rl.state.agent_role", state.agent_role)
    span.set_attribute("rl.state.prompt_hash", state.prompt_hash)
    # ... other state attributes

    try:
        result = execute_agent(input_data)

        # Set action attributes
        span.set_attribute("rl.action.success", True)
        span.set_attribute("rl.action.llm_tokens_out", result.tokens)
        span.set_attribute("rl.action.output_hash", hash(result))

        # Set immediate reward
        span.set_attribute("rl.reward.success_reward", 1.0)
        span.set_attribute("rl.reward.latency_reward", calc_latency_reward())

    except Exception as e:
        span.set_attribute("rl.action.success", False)
        span.set_attribute("rl.action.error_type", type(e).__name__)
        span.set_attribute("rl.reward.success_reward", 0.0)
        span.set_status(Status(StatusCode.ERROR, str(e)))
        raise
```

**Pros:**
- Industry-standard protocol (OTLP)
- Interoperable with many backends (Jaeger, Tempo, Honeycomb, etc.)
- Distributed tracing built-in
- Can export to Agent Lightning via OTLP
- Complements Langfuse (separate concerns)
- Rich ecosystem of tools

**Cons:**
- New dependency (opentelemetry-sdk)
- Learning curve for OTEL concepts
- Need to configure exporter

### Option 4: Hybrid - OpenTelemetry + SQLite Sync

Use OpenTelemetry for real-time tracing, sync to SQLite for persistence/analysis.

```python
# Real-time: OpenTelemetry spans with RL attributes
with tracer.start_as_current_span("agent.execute") as span:
    span.set_attribute("rl.state.task_id", task_id)
    # ... execute and record

# Batch sync: Export to SQLite for offline analysis
@periodic(interval=60)
def sync_rl_triplets_to_sqlite():
    triplets = otel_exporter.get_recent_spans(prefix="rl.")
    for triplet in triplets:
        insert_rl_triplet(triplet)
```

**Pros:**
- Best of both worlds
- Real-time + offline analysis
- Standard protocol + SQL queryability

**Cons:**
- More complexity
- Potential data duplication
- Two systems to maintain

## Decision Outcome

**Chosen option:** **Option 3 - OpenTelemetry with Custom Attributes**

### Rationale

1. **Industry Standard:** OTLP is the de facto standard for distributed tracing
2. **Agent Lightning Compatibility:** Can export directly via OTLP collector
3. **Separation of Concerns:**
   - Langfuse: LLM-specific observability (prompt management, cost tracking)
   - OpenTelemetry: Distributed tracing + RL triplets
   - SQLite: Persistent metrics for PROBE analysis
4. **Flexibility:** Easy to add new exporters (Jaeger, Tempo, custom)
5. **Ecosystem:** Rich tooling for visualization and analysis

### Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        ASP Platform                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐       │
│  │   Agents     │    │ Orchestrators │    │   Web UI    │       │
│  │              │    │              │    │             │       │
│  │ @rl_triplet  │    │ @rl_triplet  │    │ @rl_triplet │       │
│  └──────┬───────┘    └──────┬───────┘    └──────┬──────┘       │
│         │                   │                   │               │
│         └───────────────────┼───────────────────┘               │
│                             │                                    │
│                             ▼                                    │
│                  ┌──────────────────┐                           │
│                  │  OpenTelemetry   │                           │
│                  │     Tracer       │                           │
│                  │                  │                           │
│                  │ rl.state.*       │                           │
│                  │ rl.action.*      │                           │
│                  │ rl.reward.*      │                           │
│                  └────────┬─────────┘                           │
│                           │                                      │
└───────────────────────────┼──────────────────────────────────────┘
                            │
            ┌───────────────┼───────────────┐
            │               │               │
            ▼               ▼               ▼
    ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
    │    OTLP      │ │   Langfuse   │ │   SQLite     │
    │   Exporter   │ │  (existing)  │ │  (existing)  │
    │              │ │              │ │              │
    │ → Agent      │ │ → LLM obs    │ │ → PROBE      │
    │   Lightning  │ │              │ │   metrics    │
    └──────────────┘ └──────────────┘ └──────────────┘
```

### Implementation

#### 1. Dependencies

Add to `pyproject.toml`:

```toml
dependencies = [
    # ... existing deps ...
    "opentelemetry-api>=1.21.0",
    "opentelemetry-sdk>=1.21.0",
    "opentelemetry-exporter-otlp>=1.21.0",
    "opentelemetry-instrumentation-fastapi>=0.42b0",
    "opentelemetry-instrumentation-httpx>=0.42b0",
]
```

#### 2. Tracer Configuration

New file: `src/asp/telemetry/otel.py`

```python
"""OpenTelemetry configuration for RL triplet instrumentation."""

from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource, SERVICE_NAME

def configure_otel(
    service_name: str = "asp-platform",
    otlp_endpoint: str | None = None,
) -> trace.Tracer:
    """Configure OpenTelemetry tracer with OTLP exporter."""

    resource = Resource(attributes={
        SERVICE_NAME: service_name,
        "service.version": "1.0.0",
        "deployment.environment": os.getenv("ASP_ENV", "development"),
    })

    provider = TracerProvider(resource=resource)

    if otlp_endpoint:
        exporter = OTLPSpanExporter(endpoint=otlp_endpoint)
        provider.add_span_processor(BatchSpanProcessor(exporter))

    trace.set_tracer_provider(provider)
    return trace.get_tracer("asp.agents")
```

#### 3. RL Triplet Decorator

New file: `src/asp/telemetry/rl_triplet.py`

```python
"""RL Triplet instrumentation decorator."""

import functools
import json
import time
import uuid
from datetime import datetime
from typing import Any, Callable

from opentelemetry import trace

from asp.telemetry.otel import get_tracer

# Thread-local sequence index counter
_sequence_counters: dict[str, int] = {}


def rl_triplet(
    agent_role: str = None,
    sequence_scope: str = "pipeline",  # "agent", "pipeline", "session", or "custom"
    state_capturer: Callable[..., dict] | None = None,
    action_capturer: Callable[..., dict] | None = None,
):
    """
    Decorator to capture RL (state, action, reward) triplets.

    Wraps function execution with OpenTelemetry span containing
    flexible triplet data for Agent Lightning integration.

    Args:
        agent_role: Optional agent role (auto-detected from class if not provided)
        sequence_scope: How to group triplets for reward backpropagation
            - "agent": {task_id}:{agent_role}
            - "pipeline": {task_id}
            - "session": {session_id}
            - "custom": caller must set rl.sequence_id attribute
        state_capturer: Optional custom function to capture state dict
        action_capturer: Optional custom function to capture action dict

    Example:
        @rl_triplet(sequence_scope="pipeline")
        @track_agent_cost(agent_role="Planning", ...)
        def execute(self, input_data: TaskRequirements) -> ProjectPlan:
            ...
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            tracer = get_tracer()

            # Determine agent role
            role = agent_role
            if role is None and args and hasattr(args[0], 'agent_name'):
                role = args[0].agent_name
            role = role or "Unknown"

            span_name = f"{role}.{func.__name__}"

            with tracer.start_as_current_span(span_name) as span:
                # Generate triplet ID
                triplet_id = str(uuid.uuid4())
                span.set_attribute("rl.triplet_id", triplet_id)

                # Determine sequence ID based on scope
                sequence_id = _get_sequence_id(args, kwargs, sequence_scope, role)
                span.set_attribute("rl.sequence_id", sequence_id)

                # Get and increment sequence index
                sequence_index = _get_next_sequence_index(sequence_id)
                span.set_attribute("rl.sequence_index", sequence_index)

                # Timestamp
                span.set_attribute("rl.timestamp_utc", datetime.utcnow().isoformat())

                # === Capture State (flexible dict) ===
                if state_capturer:
                    state = state_capturer(func, args, kwargs, span)
                else:
                    state = _default_state_capturer(func, args, kwargs, role, span)

                # Store state as JSON (OTEL attributes are flat)
                span.set_attribute("rl.state", json.dumps(state))

                # === Execute Function ===
                start_time = time.perf_counter()
                error = None
                result = None

                try:
                    result = func(*args, **kwargs)
                    return result
                except Exception as e:
                    error = e
                    raise
                finally:
                    duration_ms = (time.perf_counter() - start_time) * 1000

                    # === Capture Action (flexible dict) ===
                    if action_capturer:
                        action = action_capturer(result, error, duration_ms)
                    else:
                        action = _default_action_capturer(result, error, duration_ms, func)

                    span.set_attribute("rl.action", json.dumps(action))

                    # === Reward: Initially None ===
                    # Reward is assigned later via assign_reward() API
                    span.set_attribute("rl.reward", "null")  # JSON null
                    span.set_attribute("rl.reward_assigned", False)

        return wrapper
    return decorator


def _get_sequence_id(args, kwargs, scope: str, role: str) -> str:
    """Determine sequence_id based on scope."""
    task_id = _extract_task_id(args, kwargs)

    if scope == "agent":
        return f"{task_id}:{role}"
    elif scope == "pipeline":
        return task_id
    elif scope == "session":
        # Would need session context - fall back to task_id for now
        return task_id
    else:  # custom
        return "custom"  # Caller should override via span.set_attribute


def _get_next_sequence_index(sequence_id: str) -> int:
    """Get and increment sequence index for a sequence."""
    global _sequence_counters
    if sequence_id not in _sequence_counters:
        _sequence_counters[sequence_id] = 0
    index = _sequence_counters[sequence_id]
    _sequence_counters[sequence_id] += 1
    return index


def _extract_task_id(args, kwargs) -> str:
    """Extract task_id from function arguments."""
    # Try common patterns
    if 'task_id' in kwargs:
        return kwargs['task_id']
    if 'input_data' in kwargs and hasattr(kwargs['input_data'], 'task_id'):
        return kwargs['input_data'].task_id
    if args and len(args) > 1 and hasattr(args[1], 'task_id'):
        return args[1].task_id  # args[0] is self, args[1] is input_data
    return "unknown"


def _default_state_capturer(func, args, kwargs, role: str, span) -> dict:
    """Default state capture - grab what's available."""
    state = {
        "agent_role": role,
        "function_name": func.__name__,
        "trace_id": format(span.get_span_context().trace_id, '032x'),
        "span_id": format(span.get_span_context().span_id, '016x'),
    }

    # Try to extract task info
    task_id = _extract_task_id(args, kwargs)
    if task_id != "unknown":
        state["task_id"] = task_id

    # Try to get input_data fields
    input_data = kwargs.get('input_data') or (args[1] if len(args) > 1 else None)
    if input_data:
        if hasattr(input_data, 'description'):
            state["task_description"] = str(input_data.description)[:500]  # Truncate
        if hasattr(input_data, 'requirements'):
            state["requirements"] = str(input_data.requirements)[:500]

    # Agent version if available
    if args and hasattr(args[0], 'agent_version'):
        state["agent_version"] = args[0].agent_version

    return state


def _default_action_capturer(result: Any, error: Exception | None, duration_ms: float, func) -> dict:
    """Default action capture - record outcome."""
    action = {
        "success": error is None,
        "duration_ms": duration_ms,
        "function_name": func.__name__,
    }

    if error:
        action["error_type"] = type(error).__name__
        action["error_message"] = str(error)[:500]  # Truncate

    if result is not None:
        action["has_result"] = True
        # Try to get size info
        try:
            action["result_type"] = type(result).__name__
            if hasattr(result, '__len__'):
                action["result_size"] = len(result)
        except Exception:
            pass

    return action


def assign_reward(triplet_id: str, reward: float, source: str = "unknown"):
    """
    Assign a reward to a triplet after the fact.

    This would typically update the stored triplet in the collector/backend.

    Args:
        triplet_id: The triplet to update
        reward: Reward value (0.0 - 1.0)
        source: How the reward was determined

    Note: Implementation depends on backend storage.
    """
    if not 0.0 <= reward <= 1.0:
        raise ValueError(f"Reward must be between 0.0 and 1.0, got {reward}")

    # TODO: Implement based on backend (OTLP collector, SQLite, etc.)
    pass


def assign_sequence_reward(sequence_id: str, reward: float, source: str = "terminal"):
    """
    Assign the same reward to all triplets in a sequence.

    Used for terminal reward backpropagation.

    Args:
        sequence_id: The sequence to update
        reward: Reward value (0.0 - 1.0)
        source: How the reward was determined

    Note: Implementation depends on backend storage.
    """
    if not 0.0 <= reward <= 1.0:
        raise ValueError(f"Reward must be between 0.0 and 1.0, got {reward}")

    # TODO: Implement based on backend
    pass
```

#### 4. Integration with Existing Decorators

Update agent execute methods to use both decorators:

```python
# src/asp/agents/planning_agent.py

@rl_triplet(
    agent_role="Planning",
    task_id_param="input_data.task_id",
)
@track_agent_cost(
    agent_role="Planning",
    task_id_param="input_data.task_id",
    llm_model="claude-sonnet-4-20250514",
    llm_provider="anthropic",
    agent_version="1.0.0",
)
def execute(self, input_data: TaskRequirements, feedback: list | None = None) -> ProjectPlan:
    """Execute Planning Agent logic."""
    ...
```

#### 5. Web UI Instrumentation

```python
# src/asp/web/main.py

from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from asp.telemetry.otel import configure_otel

# Configure OTEL on startup
tracer = configure_otel(
    service_name="asp-web-ui",
    otlp_endpoint=os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT"),
)

# Auto-instrument FastAPI/Starlette routes
FastAPIInstrumentor.instrument_app(app)
```

#### 6. Environment Configuration

```bash
# .env
OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4317
OTEL_SERVICE_NAME=asp-platform
ASP_RL_CAPTURE_PROMPTS=true
ASP_RL_REWARD_WEIGHTS='{"success": 0.4, "latency": 0.2, "cost": 0.2, "validation": 0.2}'
```

### Data Flow

```
1. User Request
       │
       ▼
2. @rl_triplet decorator activates
       │
       ▼
3. Capture STATE (pre-execution)
   - Task context
   - Agent context
   - System context
   - Trace context
       │
       ▼
4. Execute function
       │
       ▼
5. Capture ACTION (post-execution)
   - Success/error
   - Output metadata
   - Timing
       │
       ▼
6. Calculate REWARD (immediate)
   - Success reward
   - Latency reward
   - Cost efficiency
       │
       ▼
7. Export via OTLP
   → Agent Lightning
   → Jaeger/Tempo (visualization)
       │
       ▼
8. (Later) Delayed rewards
   - HITL approval
   - Test results
   - Defects found
```

## Consequences

### Positive

- **RL-Ready Data:** Structured triplets for Agent Lightning training
- **Standard Protocol:** OTLP enables integration with many systems
- **Separation of Concerns:** RL tracing separate from LLM observability
- **Minimal Intrusion:** Decorator-based, no major refactoring
- **Flexible Rewards:** Configurable weights, delayed reward support
- **Distributed Tracing:** Full call tree visibility

### Negative

- **New Dependency:** OpenTelemetry SDK adds complexity
- **Learning Curve:** Team needs to understand OTEL concepts
- **Exporter Setup:** Need to configure OTLP endpoint
- **Data Volume:** Triplets add to telemetry storage needs

### Mitigation Strategies

**For Complexity:**
- Provide sensible defaults (no config required for basic use)
- Document common configurations
- Add health checks for OTEL exporter

**For Data Volume:**
- Implement sampling for high-volume endpoints
- Hash large content (prompts, outputs) instead of storing full text
- Configure retention policies on collector

## Implementation Plan

### Phase 1: Foundation (This Session)
- [x] Write ADR document
- [ ] Add OpenTelemetry dependencies
- [ ] Create `src/asp/telemetry/otel.py` configuration
- [ ] Create `src/asp/telemetry/rl_schemas.py` dataclasses
- [ ] Create `src/asp/telemetry/rl_triplet.py` decorator

### Phase 2: Agent Instrumentation (Next Session)
- [ ] Add `@rl_triplet` to PlanningAgent
- [ ] Add `@rl_triplet` to DesignAgent
- [ ] Add `@rl_triplet` to CodeAgent
- [ ] Add `@rl_triplet` to TestAgent
- [ ] Add `@rl_triplet` to remaining agents

### Phase 3: Web UI Instrumentation
- [ ] Auto-instrument FastAPI routes
- [ ] Add custom spans for key user interactions
- [ ] Instrument HTMX endpoints

### Phase 4: Delayed Rewards
- [ ] Implement HITL approval reward callback
- [ ] Implement test result reward callback
- [ ] Implement defect detection penalty

### Phase 5: Agent Lightning Integration
- [ ] Configure OTLP exporter for Agent Lightning
- [ ] Validate triplet format compatibility
- [ ] Test RL training pipeline

## Design Decisions Made

1. **State typing:** Flexible dict, not strictly typed
   - We don't control state in detail
   - Capture what's available, let RL determine usefulness

2. **Reward range:** Continuous float, 0.0 to 1.0
   - 0.0 = worst outcome
   - 1.0 = best outcome
   - Initially `None` until assigned

3. **Sequence scope:** Configurable, supports multiple options
   - Agent-level: `{task_id}:{agent_role}`
   - Pipeline-level: `{task_id}` (default)
   - Session-level: `{session_id}`
   - Custom: caller-defined

4. **Reward assignment:** Deferred decision
   - System stores triplets with `reward: None`
   - Provides APIs for later assignment
   - Supports both immediate (local) and delayed (terminal) strategies

## Open Questions

1. **Reward strategy:** Which signals will we actually use?
   - Local (immediate success/failure)?
   - Terminal (pipeline outcome backpropagated)?
   - LLM-as-judge evaluation?
   - **Status:** Not decided - will experiment

2. **Agent Lightning integration:** Exact format/protocol?
   - How does Agent Lightning consume OTLP data?
   - Any required attributes beyond triplet_id, sequence_id, state, action, reward?
   - **Status:** Need to verify with Agent Lightning docs

3. **State content:** How much context to capture?
   - Full prompt text vs truncated vs hash?
   - Include file contents or just paths?
   - **Status:** Start with truncated (500 chars), iterate based on RL performance

4. **Sampling:** Capture everything or sample?
   - **Status:** Start with 100%, add sampling if volume is problematic

## Related Documents

- `design/ADR_001_workspace_isolation_and_execution_tracking.md` - Langfuse integration
- `src/asp/telemetry/telemetry.py` - Existing telemetry infrastructure
- `docs/database_schema_specification.md` - SQLite schema

## References

- [OpenTelemetry Python SDK](https://opentelemetry.io/docs/instrumentation/python/)
- [OTLP Specification](https://opentelemetry.io/docs/specs/otlp/)
- [Agent Lightning Documentation](TBD)

---

**Status:** Proposed - Awaiting review and approval
**Next Steps:** Review with user, then begin Phase 1 implementation
