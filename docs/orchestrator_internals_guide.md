# Orchestrator Internals Guide

**Version:** 1.0.0
**Last Updated:** November 2025

This guide documents the internal workings of the **TSPOrchestrator** (`src/asp/orchestrators/tsp_orchestrator.py`), the central nervous system of the ASP platform.

## Overview

The `TSPOrchestrator` (Task/Support/Process Orchestrator) manages the lifecycle of a task as it flows through the agentic pipeline. It is responsible for:
1.  **State Management:** Tracking which phase the task is in (Planning, Design, Code, Test).
2.  **Data Flow:** Passing artifacts (Plans, Specs, Code) between agents.
3.  **Feedback Loops:** Routing defects back to previous agents for correction.
4.  **Human-in-the-Loop (HITL):** Pausing for approval when configured.

## Core Flow

The orchestrator implements a **Phase-Gate Process**:

1.  **Planning Phase:** `PlanningAgent` -> `ProjectPlan`.
2.  **Design Phase:** `DesignAgent` -> `DesignSpecification`.
3.  **Design Review Gate:** `DesignReviewOrchestrator` -> `DesignReviewReport`.
    -   *If Fail:* Send feedback back to `DesignAgent` (or `PlanningAgent`).
    -   *If Pass:* Proceed.
4.  **Coding Phase:** `CodeAgent` -> `GeneratedCode`.
5.  **Testing Phase:** `TestAgent` -> `TestReport`.
    -   *If Fail:* Send feedback back to `CodeAgent`.
    -   *If Pass:* Proceed.
6.  **Postmortem:** `PostmortemAgent` -> `PostmortemReport` + `PIP`.

## State Machine Logic

The orchestrator logic is primarily sequential but includes **loops** for error correction.

### The `execute_task()` Method

This is the main entry point.

```python
def execute_task(self, task_request: str) -> TaskResult:
    # 1. Planning
    plan = self.planning_agent.execute(task_request)

    # 2. Design Loop
    while attempts < max_retries:
        design = self.design_agent.execute(plan, feedback)
        review = self.review_agent.execute(design)
        if review.status == "PASS":
            break
        feedback = review.issues

    # 3. Code & Test Loop
    while attempts < max_retries:
        code = self.code_agent.execute(design)
        test_report = self.test_agent.execute(code)
        if test_report.status == "PASS":
            break
        # Refine code based on test failures
```

## Data Models

The orchestrator relies on shared models in `src/asp/models/`:
-   `TaskRequirements`
-   `ProjectPlan`
-   `DesignSpecification`
-   `GeneratedCode`
-   `TestReport`

## Configuration

The orchestrator is configured via:
-   `max_retries`: How many times to loop before giving up (default 3).
-   `hitl_config`: Which gates require human approval.

## Extension Points

### Adding a New Phase

To add a "Security Audit" phase after Testing:
1.  Instantiate `SecurityAuditAgent` in `__init__`.
2.  Add a call to `self.security_agent.execute()` after the Test loop in `execute_task`.
3.  Handle the result (pass/fail logic).

### Customizing Feedback

The logic for how feedback is formatted and passed back is currently embedded in the loops. Future refactoring aims to move this to a `FeedbackStrategy` class.

## Async Execution (ADR 008)

As of ADR 008 implementation, all orchestrators support async execution.

### Async Methods

```python
# TSPOrchestrator
result = await orchestrator.execute_async(requirements)

# PlanningDesignOrchestrator
result = await orchestrator.execute_async(requirements)
```

### CLI Integration

```bash
# Sync (default)
uv run python -m asp.cli run --task-id TASK-001 --description "Add feature"

# Async
uv run python -m asp.cli run --task-id TASK-001 --description "Add feature" --async
```

### Implementation Details

The async orchestrator methods:
1. Call agent `execute_async()` methods instead of `execute()`
2. Use `asyncio.run()` wrapper in CLI for event loop management
3. Maintain same quality gate logic and iteration limits
4. Support HITL approval (currently sync, future async WebSocket support)

### Async Architecture

```
┌─────────────────────────────────────────────────────────────┐
│ CLI: --async flag                                           │
│   → asyncio.run(orchestrator.execute_async(...))           │
├─────────────────────────────────────────────────────────────┤
│ TSPOrchestrator.execute_async()                            │
│   → _execute_planning_async()                              │
│   → _execute_design_with_review_async()                    │
│   → _execute_code_with_review_async()                      │
│   → _execute_testing_with_retry_async()                    │
│   → _execute_postmortem_async()                            │
├─────────────────────────────────────────────────────────────┤
│ Each agent.execute_async()                                  │
│   → AsyncAnthropic client                                  │
│   → Non-blocking I/O                                       │
└─────────────────────────────────────────────────────────────┘
```

See [ADR 008](../design/ADR_008_async_process_architecture.md) for full details.
