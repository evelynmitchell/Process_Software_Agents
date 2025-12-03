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

### State (Context at Decision Time)

The **state** captures all information available when an action is taken.

```python
@dataclass
class RLState:
    """State captured at the moment an action is taken."""

    # === Request Context ===
    task_id: str                    # Unique task identifier
    task_description_hash: str      # SHA256 of task description (for dedup)
    requirements_hash: str          # SHA256 of requirements text
    context_file_count: int         # Number of context files provided

    # === Agent Context ===
    agent_role: str                 # "Planning", "Design", "Code", "Test", etc.
    agent_version: str              # Agent version string
    function_name: str              # Function being called

    # === LLM Context ===
    llm_model: str                  # Model name (e.g., "claude-sonnet-4-20250514")
    llm_provider: str               # Provider (e.g., "anthropic")
    prompt_hash: str                # SHA256 of formatted prompt
    prompt_token_estimate: int      # Estimated input tokens
    temperature: float              # Sampling temperature
    max_tokens: int                 # Max output tokens requested

    # === Pipeline Context ===
    current_phase: str              # PSP phase (Planning, Design, Code, Test, Postmortem)
    pipeline_iteration: int         # Retry/loop iteration count
    prior_artifact_ids: list[str]   # IDs of artifacts available as context
    feedback_item_count: int        # Design review feedback items (if any)

    # === System Context ===
    budget_remaining_pct: float     # Budget headroom (0.0 - 1.0)
    pending_approvals: int          # HITL items awaiting approval
    active_agent_count: int         # Currently executing agents
    recent_success_rate: float      # Success rate of last N executions

    # === Trace Context ===
    trace_id: str                   # OpenTelemetry trace ID
    parent_span_id: str | None      # Parent span (if nested)
    span_id: str                    # Current span ID
    call_depth: int                 # Nesting depth in call tree

    # === Temporal Context ===
    timestamp_utc: str              # ISO timestamp
    wall_clock_ms: int              # Milliseconds since epoch
```

**Data Sources:**

| Field | Source |
|-------|--------|
| `task_id` | `TaskRequirements.task_id` |
| `task_description_hash` | `hashlib.sha256(TaskRequirements.description)` |
| `agent_role` | `BaseAgent.agent_name` |
| `llm_model` | `@track_agent_cost` decorator param |
| `prompt_hash` | `hashlib.sha256(formatted_prompt)` |
| `current_phase` | TSP orchestrator context |
| `budget_remaining_pct` | `get_budget_status()` |
| `trace_id` | `opentelemetry.trace.get_current_span().context.trace_id` |

### Action (Function Call Result)

The **action** captures the result/output of the function execution.

```python
@dataclass
class RLAction:
    """Result of a function call / action taken."""

    # === Identification ===
    action_type: str                # "llm_call", "tool_call", "api_call", "db_query", "error"
    function_name: str              # Function that produced this result

    # === Outcome ===
    success: bool                   # Did it complete without exception?
    error_type: str | None          # Exception class name (if failed)
    error_message_hash: str | None  # SHA256 of error message (if failed)

    # === LLM-Specific (action_type == "llm_call") ===
    llm_response_hash: str | None   # SHA256 of response content
    llm_tokens_in: int | None       # Actual input tokens used
    llm_tokens_out: int | None      # Actual output tokens generated
    llm_stop_reason: str | None     # "end_turn", "max_tokens", "stop_sequence"
    llm_model_actual: str | None    # Actual model used (may differ from requested)

    # === Artifact-Specific (action_type == "tool_call") ===
    artifact_type: str | None       # "plan", "design", "code", "test", etc.
    artifact_id: str | None         # File path or artifact ID
    artifact_size_bytes: int | None # Size of generated artifact
    validation_passed: bool | None  # Pydantic validation result
    validation_error_count: int | None  # Number of validation errors

    # === API-Specific (action_type == "api_call") ===
    http_status: int | None         # HTTP response status
    api_endpoint_hash: str | None   # SHA256 of endpoint URL

    # === Timing ===
    duration_ms: float              # Execution time in milliseconds

    # === Output Summary ===
    output_size_bytes: int          # Size of serialized output
    output_hash: str                # SHA256 for identity/dedup
    output_structure: str | None    # JSON schema or type info
```

**Data Sources:**

| Field | Source |
|-------|--------|
| `success` | `try/except` wrapper result |
| `error_type` | `type(exception).__name__` |
| `llm_tokens_in` | `response["usage"]["input_tokens"]` |
| `llm_stop_reason` | `response["stop_reason"]` |
| `artifact_type` | `write_artifact_json()` parameter |
| `validation_passed` | `model.model_validate()` success |
| `duration_ms` | `(end_time - start_time) * 1000` |

### Reward (Quality Signals)

The **reward** captures signals indicating the quality/value of the action.

```python
@dataclass
class RLReward:
    """Reward signals for the action taken."""

    # === Immediate Rewards (available at action completion) ===
    success_reward: float           # 1.0 if success, 0.0 if error
    latency_reward: float           # Normalized: 1.0 - (latency / max_expected)
    cost_efficiency: float          # Normalized: output_quality / cost
    validation_reward: float        # 1.0 if valid, 0.0 if invalid

    # === Delayed Rewards (available after downstream processing) ===
    hitl_approval: float | None     # 1.0 approved, 0.5 modified, 0.0 rejected
    downstream_success: float | None  # Did next agent succeed?
    test_pass_rate: float | None    # % of tests passing (0.0 - 1.0)
    defect_penalty: float | None    # Negative reward for defects found later

    # === Composite Reward ===
    total_reward: float             # Weighted combination of signals
    reward_version: str             # Schema version for reward calculation

    # === Metadata ===
    reward_timestamp_utc: str       # When reward was calculated
    reward_delay_ms: int            # Time between action and reward
```

**Reward Calculation:**

```python
def calculate_reward(action: RLAction, config: RewardConfig) -> RLReward:
    """Calculate composite reward from action outcome."""

    # Immediate rewards
    success_reward = 1.0 if action.success else 0.0
    latency_reward = max(0, 1.0 - (action.duration_ms / config.max_latency_ms))
    cost_efficiency = calculate_cost_efficiency(action)
    validation_reward = 1.0 if action.validation_passed else 0.0

    # Weighted combination
    total = (
        config.w_success * success_reward +
        config.w_latency * latency_reward +
        config.w_cost * cost_efficiency +
        config.w_validation * validation_reward
    )

    return RLReward(
        success_reward=success_reward,
        latency_reward=latency_reward,
        cost_efficiency=cost_efficiency,
        validation_reward=validation_reward,
        total_reward=total,
        reward_version="1.0.0",
        ...
    )
```

**Default Weights:**

| Signal | Weight | Rationale |
|--------|--------|-----------|
| `success` | 0.4 | Most important - did it work? |
| `latency` | 0.2 | Speed matters for UX |
| `cost` | 0.2 | Token efficiency |
| `validation` | 0.2 | Output quality |

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
import hashlib
import time
from dataclasses import asdict
from typing import Callable

from opentelemetry import trace

from asp.telemetry.otel import get_tracer
from asp.telemetry.rl_schemas import RLState, RLAction, RLReward


def rl_triplet(
    agent_role: str,
    task_id_param: str = "input_data.task_id",
    capture_prompt: bool = True,
):
    """
    Decorator to capture RL (state, action, reward) triplets.

    Wraps function execution with OpenTelemetry span containing
    structured RL attributes for Agent Lightning integration.

    Args:
        agent_role: Agent role name (Planning, Design, Code, etc.)
        task_id_param: Path to task_id in function arguments
        capture_prompt: Whether to hash and record prompt content

    Example:
        @rl_triplet(agent_role="Planning")
        @track_agent_cost(agent_role="Planning", ...)
        def execute(self, input_data: TaskRequirements) -> ProjectPlan:
            ...
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            tracer = get_tracer()
            span_name = f"{agent_role}.{func.__name__}"

            with tracer.start_as_current_span(span_name) as span:
                # === Capture State ===
                state = _capture_state(
                    func, args, kwargs,
                    agent_role=agent_role,
                    task_id_param=task_id_param,
                    span=span,
                )
                _set_state_attributes(span, state)

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

                    # === Capture Action ===
                    action = _capture_action(
                        result=result,
                        error=error,
                        duration_ms=duration_ms,
                        func_name=func.__name__,
                    )
                    _set_action_attributes(span, action)

                    # === Calculate Reward ===
                    reward = _calculate_reward(action)
                    _set_reward_attributes(span, reward)

        return wrapper
    return decorator


def _set_state_attributes(span: trace.Span, state: RLState):
    """Set RL state attributes on span."""
    for key, value in asdict(state).items():
        if value is not None:
            span.set_attribute(f"rl.state.{key}", value)


def _set_action_attributes(span: trace.Span, action: RLAction):
    """Set RL action attributes on span."""
    for key, value in asdict(action).items():
        if value is not None:
            span.set_attribute(f"rl.action.{key}", value)


def _set_reward_attributes(span: trace.Span, reward: RLReward):
    """Set RL reward attributes on span."""
    for key, value in asdict(reward).items():
        if value is not None:
            span.set_attribute(f"rl.reward.{key}", value)
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

## Open Questions

1. **Prompt Content:** Should we capture full prompt text, or just hash + token count?
   - Full text: Complete for RL, but large storage
   - Hash only: Compact, but loses semantic info
   - **Proposed:** Hash by default, full text opt-in via config

2. **Reward Timing:** When should delayed rewards be attached?
   - Same span (update attributes)
   - Linked span (new span with reference)
   - **Proposed:** New span with `follows_from` link to original

3. **Sampling:** Should we sample triplets?
   - 100% capture: Complete data, high volume
   - Sampled: Reduced storage, potential bias
   - **Proposed:** 100% for agents, sampled for web UI

4. **Agent Lightning Format:** What exact format does Agent Lightning expect?
   - **Action needed:** Get schema spec from Agent Lightning docs

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
