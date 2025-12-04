# ADR 004: Process Graph Learning from Program Execution

**Status:** Proposed
**Date:** 2025-12-04
**Session:** 20251204.1
**Deciders:** User, Claude
**Depends On:** ADR 003 (OpenTelemetry RL Triplet Instrumentation)

## Context and Problem Statement

With OpenTelemetry instrumentation (ADR 003), the ASP platform will generate rich trace data capturing function calls, agent executions, and their relationships. This trace data contains implicit **causal structure** - the parent-child span relationships form a directed graph of execution flow.

**Opportunity:** We can apply process mining and causal discovery techniques to this trace data to:
1. Discover actual execution patterns (vs. designed patterns)
2. Identify bottlenecks and performance issues
3. Check conformance between expected and actual behavior
4. Build causal models for optimization and debugging
5. Feed learned graphs into RL systems for improved decision-making

**Problem:** How do we extract, represent, and analyze process/causal graphs from OpenTelemetry trace data?

## Decision Drivers

1. **Leverage Existing Data:** Build on OpenTelemetry traces from ADR 003
2. **Process Mining Standards:** Use established algorithms and representations
3. **Causal Discovery:** Go beyond correlation to causal relationships
4. **Actionable Insights:** Produce graphs useful for debugging and optimization
5. **RL Integration:** Causal graphs can inform Agent Lightning's decision-making
6. **Minimal New Infrastructure:** Reuse existing trace collectors where possible

## Core Concepts

### From Traces to Graphs

OpenTelemetry traces naturally encode graph structure:

```
Trace (DAG)                          Process Graph (Aggregated)
─────────────────                    ─────────────────────────────

trace_id: abc123                     [Discovered from many traces]

root_span (request)                  ┌──────────────┐
├── span: PlanningAgent.execute      │   Request    │
│   ├── span: llm_call               └──────┬───────┘
│   └── span: validate_output                │
├── span: DesignAgent.execute        ┌───────▼───────┐
│   ├── span: llm_call               │ PlanningAgent │
│   └── span: validate_output        └───────┬───────┘
└── span: CodeAgent.execute                  │
    ├── span: llm_call               ┌───────▼───────┐
    └── span: write_file             │  DesignAgent  │
                                     └───────┬───────┘
                                             │
                                     ┌───────▼───────┐
                                     │   CodeAgent   │
                                     └───────────────┘
```

### Graph Types We Can Learn

| Graph Type | Source | Use Case |
|------------|--------|----------|
| **Call Graph** | Direct span parent-child | Debugging, profiling |
| **Directly-Follows Graph (DFG)** | Span sequence ordering | Process discovery |
| **Petri Net** | Process mining algorithms | Formal process model |
| **Causal DAG** | Statistical inference | Root cause analysis |
| **State Transition Graph** | RL triplet sequences | Policy learning |

## Proposed Solution

### Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     OpenTelemetry Traces                         │
│                       (from ADR 003)                             │
└─────────────────────────┬───────────────────────────────────────┘
                          │
          ┌───────────────┼───────────────┐
          │               │               │
          ▼               ▼               ▼
   ┌─────────────┐ ┌─────────────┐ ┌─────────────┐
   │   OTLP      │ │   Jaeger/   │ │   SQLite    │
   │  Collector  │ │   Tempo     │ │  (export)   │
   └──────┬──────┘ └──────┬──────┘ └──────┬──────┘
          │               │               │
          └───────────────┼───────────────┘
                          │
                          ▼
              ┌───────────────────────┐
              │   Trace ETL Pipeline  │
              │                       │
              │  - Extract spans      │
              │  - Build event log    │
              │  - Add case IDs       │
              └───────────┬───────────┘
                          │
                          ▼
              ┌───────────────────────┐
              │    XES Event Log      │
              │  (Process Mining      │
              │   Standard Format)    │
              └───────────┬───────────┘
                          │
          ┌───────────────┼───────────────┐
          │               │               │
          ▼               ▼               ▼
   ┌─────────────┐ ┌─────────────┐ ┌─────────────┐
   │  Process    │ │   Causal    │ │ Conformance │
   │  Discovery  │ │  Discovery  │ │  Checking   │
   │             │ │             │ │             │
   │  - Alpha    │ │  - PC Alg   │ │  - Token    │
   │  - Heuristic│ │  - FCI      │ │    replay   │
   │  - Inductive│ │  - Granger  │ │  - Alignment│
   └──────┬──────┘ └──────┬──────┘ └──────┬──────┘
          │               │               │
          └───────────────┼───────────────┘
                          │
                          ▼
              ┌───────────────────────┐
              │   Learned Graphs      │
              │                       │
              │  - Petri nets         │
              │  - DFGs               │
              │  - Causal DAGs        │
              │  - Conformance reports│
              └───────────┬───────────┘
                          │
          ┌───────────────┼───────────────┐
          │               │               │
          ▼               ▼               ▼
   ┌─────────────┐ ┌─────────────┐ ┌─────────────┐
   │ Visualize   │ │   Optimize  │ │ Feed to RL  │
   │ (Web UI)    │ │  (Alerts)   │ │ (Lightning) │
   └─────────────┘ └─────────────┘ └─────────────┘
```

### Component 1: Trace ETL Pipeline

Transform OpenTelemetry spans into process mining event logs.

```python
# src/asp/telemetry/trace_etl.py

from dataclasses import dataclass
from typing import Iterator
import json

@dataclass
class ProcessEvent:
    """Event in XES-compatible format for process mining."""
    case_id: str          # trace_id or task_id (groups events)
    activity: str         # span name (e.g., "PlanningAgent.execute")
    timestamp: str        # ISO timestamp
    resource: str         # agent role or service name

    # Optional attributes
    duration_ms: float | None = None
    success: bool | None = None
    parent_activity: str | None = None

    # RL triplet data (if available)
    rl_state: dict | None = None
    rl_action: dict | None = None
    rl_reward: float | None = None


def spans_to_events(spans: list[dict]) -> Iterator[ProcessEvent]:
    """
    Convert OpenTelemetry spans to process mining events.

    Args:
        spans: List of OTLP span dicts

    Yields:
        ProcessEvent for each span
    """
    for span in spans:
        yield ProcessEvent(
            case_id=span.get("trace_id"),
            activity=span.get("name"),
            timestamp=span.get("start_time"),
            resource=span.get("attributes", {}).get("agent_role", "unknown"),
            duration_ms=_calc_duration(span),
            success=span.get("status", {}).get("code") != "ERROR",
            parent_activity=_get_parent_name(span, spans),
            rl_state=_parse_json_attr(span, "rl.state"),
            rl_action=_parse_json_attr(span, "rl.action"),
            rl_reward=span.get("attributes", {}).get("rl.reward"),
        )


def export_to_xes(events: list[ProcessEvent], path: str):
    """Export events to XES format for PM4Py/ProM."""
    # XES is XML-based IEEE standard for event logs
    ...


def export_to_csv(events: list[ProcessEvent], path: str):
    """Export events to CSV for simpler tools."""
    ...
```

### Component 2: Process Discovery

Use PM4Py to discover process models from event logs.

```python
# src/asp/telemetry/process_discovery.py

import pm4py
from pm4py.objects.log.importer.xes import importer as xes_importer
from pm4py.algo.discovery.inductive import algorithm as inductive_miner
from pm4py.algo.discovery.heuristics import algorithm as heuristics_miner
from pm4py.algo.discovery.dfg import algorithm as dfg_discovery


def discover_dfg(event_log_path: str) -> dict:
    """
    Discover Directly-Follows Graph from event log.

    Returns frequency of activity transitions.
    """
    log = xes_importer.apply(event_log_path)
    dfg = dfg_discovery.apply(log)
    return dfg


def discover_petri_net(event_log_path: str, algorithm: str = "inductive") -> tuple:
    """
    Discover Petri net process model.

    Args:
        event_log_path: Path to XES event log
        algorithm: "inductive" (sound) or "heuristics" (noise-tolerant)

    Returns:
        (net, initial_marking, final_marking)
    """
    log = xes_importer.apply(event_log_path)

    if algorithm == "inductive":
        net, im, fm = inductive_miner.apply(log)
    else:
        net, im, fm = heuristics_miner.apply(log)

    return net, im, fm


def visualize_dfg(dfg: dict, output_path: str):
    """Render DFG as image for web UI."""
    from pm4py.visualization.dfg import visualizer
    gviz = visualizer.apply(dfg)
    visualizer.save(gviz, output_path)


def get_process_statistics(event_log_path: str) -> dict:
    """
    Extract process statistics for dashboard.

    Returns:
        - Most common paths
        - Average case duration
        - Activity frequencies
        - Bottleneck activities (highest wait times)
    """
    log = xes_importer.apply(event_log_path)

    return {
        "total_cases": len(log),
        "total_events": sum(len(trace) for trace in log),
        "activity_counts": _count_activities(log),
        "avg_case_duration": _avg_duration(log),
        "bottlenecks": _find_bottlenecks(log),
    }
```

### Component 3: Causal Discovery

Go beyond process discovery to find causal relationships.

```python
# src/asp/telemetry/causal_discovery.py

from typing import Optional
import pandas as pd
import numpy as np

# Causal discovery libraries
# - causal-learn (CMU): PC, FCI, GES algorithms
# - DoWhy (Microsoft): Causal inference framework
# - TIGRAMITE: Time series causal discovery


def build_span_dataframe(events: list[ProcessEvent]) -> pd.DataFrame:
    """
    Convert events to DataFrame for causal analysis.

    Columns: activity, duration, success, parent, timestamp, ...
    """
    return pd.DataFrame([
        {
            "case_id": e.case_id,
            "activity": e.activity,
            "timestamp": e.timestamp,
            "duration_ms": e.duration_ms,
            "success": int(e.success) if e.success else 0,
            "parent": e.parent_activity,
        }
        for e in events
    ])


def discover_causal_graph_pc(df: pd.DataFrame) -> dict:
    """
    Use PC algorithm to discover causal DAG.

    PC algorithm finds conditional independencies to
    construct a causal graph skeleton, then orients edges.

    Returns:
        Adjacency dict representing causal DAG
    """
    from causallearn.search.ConstraintBased.PC import pc

    # Prepare numeric matrix
    # (encode activities, aggregate by case)
    matrix = _prepare_causal_matrix(df)

    # Run PC algorithm
    cg = pc(matrix)

    return _graph_to_dict(cg)


def discover_granger_causality(
    df: pd.DataFrame,
    activity_a: str,
    activity_b: str,
    max_lag: int = 5
) -> dict:
    """
    Test Granger causality between activity metrics.

    Does A's duration/success Granger-cause B's duration/success?

    Returns:
        p-values and test statistics
    """
    from statsmodels.tsa.stattools import grangercausalitytests

    # Prepare time series for each activity
    series_a = _activity_timeseries(df, activity_a)
    series_b = _activity_timeseries(df, activity_b)

    # Combine and test
    combined = pd.concat([series_b, series_a], axis=1)
    results = grangercausalitytests(combined, maxlag=max_lag)

    return _summarize_granger(results)


def build_causal_dag_from_traces(spans: list[dict]) -> dict:
    """
    Build causal DAG directly from span parent-child relationships.

    This is the simplest approach: parent span → child span
    represents direct causal influence.

    Returns:
        {
            "nodes": ["PlanningAgent.execute", "DesignAgent.execute", ...],
            "edges": [
                {"from": "PlanningAgent.execute", "to": "DesignAgent.execute", "weight": 150},
                ...
            ]
        }
    """
    nodes = set()
    edges = {}  # (from, to) -> count

    for span in spans:
        activity = span.get("name")
        parent_id = span.get("parent_span_id")

        nodes.add(activity)

        if parent_id:
            parent_activity = _find_span_name(spans, parent_id)
            if parent_activity:
                edge = (parent_activity, activity)
                edges[edge] = edges.get(edge, 0) + 1

    return {
        "nodes": list(nodes),
        "edges": [
            {"from": f, "to": t, "weight": w}
            for (f, t), w in edges.items()
        ]
    }
```

### Component 4: Conformance Checking

Compare actual execution against expected process model.

```python
# src/asp/telemetry/conformance.py

from dataclasses import dataclass
from typing import list

@dataclass
class ConformanceResult:
    """Result of conformance check."""
    fitness: float          # 0.0-1.0, how well log fits model
    precision: float        # 0.0-1.0, how precise model is
    generalization: float   # 0.0-1.0, how well model generalizes

    deviations: list[dict]  # List of specific deviations
    conformant_cases: int
    non_conformant_cases: int


def check_conformance(
    event_log_path: str,
    reference_model: str,  # Path to PNML Petri net
) -> ConformanceResult:
    """
    Check if actual execution conforms to expected process.

    Uses token-based replay to identify deviations.
    """
    import pm4py
    from pm4py.algo.conformance.tokenreplay import algorithm as token_replay

    log = pm4py.read_xes(event_log_path)
    net, im, fm = pm4py.read_pnml(reference_model)

    # Token replay
    replayed = token_replay.apply(log, net, im, fm)

    # Calculate fitness
    fitness = pm4py.fitness_token_based_replay(log, net, im, fm)

    # Find deviations
    deviations = _extract_deviations(replayed)

    return ConformanceResult(
        fitness=fitness["log_fitness"],
        precision=_calc_precision(log, net, im, fm),
        generalization=_calc_generalization(log, net, im, fm),
        deviations=deviations,
        conformant_cases=sum(1 for r in replayed if r["trace_is_fit"]),
        non_conformant_cases=sum(1 for r in replayed if not r["trace_is_fit"]),
    )


def define_expected_model() -> str:
    """
    Define the expected TSP pipeline process model.

    Returns path to PNML file.
    """
    # Expected flow:
    # Request → Planning → Design → Code → Test → Review → Complete
    #                  ↑___________↓ (feedback loops)

    # Could be defined programmatically or loaded from file
    return "models/expected_tsp_pipeline.pnml"
```

### Component 5: Web UI Integration

Display graphs and analysis in the dashboard.

```python
# src/asp/web/process_graphs.py

from starlette.routing import Route
from starlette.responses import HTMLResponse, JSONResponse

from asp.telemetry.process_discovery import (
    discover_dfg,
    get_process_statistics,
)
from asp.telemetry.causal_discovery import build_causal_dag_from_traces
from asp.telemetry.conformance import check_conformance


async def process_graph_page(request):
    """Render process graph visualization page."""
    return HTMLResponse(templates.render("process_graph.html"))


async def get_dfg_data(request):
    """Return DFG data for D3.js visualization."""
    dfg = discover_dfg("data/event_log.xes")
    return JSONResponse({
        "nodes": list(dfg["activities"]),
        "edges": [
            {"source": s, "target": t, "weight": w}
            for (s, t), w in dfg["dfg"].items()
        ]
    })


async def get_causal_graph_data(request):
    """Return causal DAG for visualization."""
    spans = _load_recent_spans(hours=24)
    graph = build_causal_dag_from_traces(spans)
    return JSONResponse(graph)


async def get_conformance_report(request):
    """Return conformance checking results."""
    result = check_conformance(
        "data/event_log.xes",
        "models/expected_tsp_pipeline.pnml"
    )
    return JSONResponse({
        "fitness": result.fitness,
        "precision": result.precision,
        "conformant_pct": result.conformant_cases /
            (result.conformant_cases + result.non_conformant_cases),
        "top_deviations": result.deviations[:10],
    })


routes = [
    Route("/process/graph", process_graph_page),
    Route("/api/process/dfg", get_dfg_data),
    Route("/api/process/causal", get_causal_graph_data),
    Route("/api/process/conformance", get_conformance_report),
]
```

## Implementation Plan

### Phase 1: Trace ETL (Foundation)
- [ ] Create `src/asp/telemetry/trace_etl.py`
- [ ] Implement span → ProcessEvent conversion
- [ ] Export to XES format
- [ ] Export to CSV format
- [ ] Add scheduled job to export traces

### Phase 2: Process Discovery
- [ ] Add PM4Py dependency
- [ ] Implement DFG discovery
- [ ] Implement Petri net discovery
- [ ] Add process statistics extraction
- [ ] Create visualization exports (PNG/SVG)

### Phase 3: Causal Discovery
- [ ] Add causal-learn dependency
- [ ] Implement call graph extraction (simple DAG from spans)
- [ ] Implement PC algorithm wrapper
- [ ] Implement Granger causality tests
- [ ] Store causal graphs for analysis

### Phase 4: Conformance Checking
- [ ] Define expected TSP pipeline model (PNML)
- [ ] Implement token-based replay
- [ ] Calculate fitness/precision metrics
- [ ] Extract and categorize deviations
- [ ] Add deviation alerting

### Phase 5: Web UI Integration
- [ ] Create process graph page
- [ ] Add D3.js force-directed graph visualization
- [ ] Display process statistics dashboard
- [ ] Show conformance report
- [ ] Add bottleneck highlighting

### Phase 6: RL Integration
- [ ] Export causal graphs in Agent Lightning format
- [ ] Use learned graphs as policy constraints
- [ ] Feedback conformance signals as rewards

## Dependencies

```toml
# pyproject.toml additions
dependencies = [
    # Process Mining
    "pm4py>=2.7.0",

    # Causal Discovery
    "causal-learn>=0.1.3",
    "dowhy>=0.11",

    # Visualization
    "graphviz>=0.20",
]
```

## Considered Alternatives

### Alternative 1: Custom Graph Building Only
Build simple call graphs from spans without process mining.

**Pros:** Simple, no new dependencies
**Cons:** Misses process mining algorithms, conformance checking

### Alternative 2: External Process Mining Tool
Export traces to ProM or Celonis for analysis.

**Pros:** Powerful commercial/academic tools
**Cons:** Not integrated, requires manual export/import

### Alternative 3: Graph Database (Neo4j)
Store traces in graph database for querying.

**Pros:** Powerful graph queries, visualization
**Cons:** Heavy infrastructure, overkill for current scale

**Decision:** Use PM4Py (Python library) for integrated analysis with option to export for external tools.

## Consequences

### Positive
- **Discovery:** Find actual patterns vs. assumptions
- **Debugging:** Visual call graphs for troubleshooting
- **Optimization:** Identify bottlenecks quantitatively
- **Conformance:** Detect process drift automatically
- **RL Feedback:** Causal graphs inform policy learning

### Negative
- **Dependencies:** PM4Py and causal-learn add to requirements
- **Computation:** Process mining can be expensive on large logs
- **Complexity:** New concepts (Petri nets, XES) to understand

### Mitigation
- Sample large logs for discovery (full logs for conformance)
- Cache discovered models (rebuild on schedule)
- Provide documentation on process mining concepts

## Related Documents

- ADR 003: OpenTelemetry RL Triplet Instrumentation
- ADR 005: Development Process Graph Learning (companion ADR)

## References

- [PM4Py Documentation](https://pm4py.fit.fraunhofer.de/)
- [Process Mining: Data Science in Action](https://www.springer.com/gp/book/9783662498507) - van der Aalst
- [Causal Discovery Toolbox](https://github.com/cmu-phil/causal-learn)
- [DoWhy: Causal Inference](https://microsoft.github.io/dowhy/)

---

**Status:** Proposed - Awaiting review
