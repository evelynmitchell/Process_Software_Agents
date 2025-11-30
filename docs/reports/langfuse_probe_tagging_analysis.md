# Report: Langfuse Tagging Strategy for PROBE Analysis

**Date:** November 30, 2025
**Branch:** claude/langfuse-probe-analysis
**Author:** Claude (ASP Development Assistant)

## Executive Summary

This report analyzes the current Langfuse integration within the ASP platform and proposes a comprehensive tagging strategy to enable PROBE (Proxy Based Estimation) analysis across multiple dimensions: Tasks, Projects, and People/GitHub Accounts.

Currently, the system logs execution traces and defects but lacks consistent metadata for **Project**, **User Identity**, and granular **Defect Taxonomy** required for robust PROBE analysis.

## 1. Current State Analysis

### 1.1 Existing Telemetry (`src/asp/telemetry/telemetry.py`)

The system currently tracks:
- **Traces:** Agent execution spans via `@track_agent_cost`.
- **Events:** Defect detection/fixing via `@log_defect`.
- **Metadata Captured:**
    - `task_id` (Primary correlation ID)
    - `agent_role` (e.g., Planning, Design)
    - `function` (Function name)
    - `llm_model`, `llm_provider`
    - `agent_version`
    - `defect_type`, `severity`, `phase_injected`, `phase_removed` (for defects)

### 1.2 Gaps for PROBE Analysis

PROBE (from PSP/TSP) requires tracking:
1.  **Size/Proxy Data:** (Estimated vs. Actual LOC, Tokens, etc.)
2.  **Time:** (Phase-based effort tracking)
3.  **Defects:** (Type, Injection Phase, Removal Phase, Fix Time)
4.  **Context:** (Project, Person/Role)

**Identified Gaps:**
*   **Project Context:** `project_id` is an optional argument in `insert_agent_cost` but is **not** captured in the `track_agent_cost` decorator or sent to Langfuse traces.
*   **User/Person Context:** There is no concept of "User" or "GitHub Account" in the current telemetry. It assumes a single-user or system-agent context.
*   **Defect Taxonomy:** The system allows any string for `defect_type`, `phase_injected`, etc. PROBE requires a standard taxonomy (e.g., 10 - Documentation, 20 - Syntax, 30 - Build, 40 - Assignment, etc.).
*   **Session/Batch Context:** No grouping of traces into a "Session" or "Work Period" (crucial for time-in-phase tracking).

## 2. Proposed Tagging Strategy

To enable multi-project, multi-person PROBE analysis, we must standardize tags and metadata in Langfuse.

### 2.1 Standardized Tags

Langfuse **Tags** should be used for high-level filtering (searchable, indexable).

| Tag Category | Format | Example | Purpose |
| :--- | :--- | :--- | :--- |
| **Project** | `project:<id>` | `project:nanogpt-fork` | Filter traces by repository/project. |
| **User** | `user:<github_handle>` | `user:jules-agent` | Identify the person or agent instance. |
| **Task** | `task:<id>` | `task:TSP-001` | Group all work for a specific task. |
| **Cycle** | `cycle:<id>` | `cycle:20251130.1` | Correlate with session summaries. |

### 2.2 Detailed Metadata

Langfuse **Metadata** should store granular PROBE data (analyzable via SQL/API exports).

**Trace Metadata (Execution):**
```json
{
  "probe": {
    "phase": "Code",
    "size_metric": "tokens",
    "size_estimated": 1000,
    "size_actual": 1250,
    "time_delta_ms": 4500
  },
  "context": {
    "repo_url": "https://github.com/karpathy/nanoGPT",
    "branch": "feature/add-tests",
    "commit_hash": "a1b2c3d..."
  }
}
```

**Event Metadata (Defect):**
```json
{
  "probe_defect": {
    "id": "DEF-001",
    "type_code": "20",  // Syntax
    "type_name": "Syntax",
    "phase_injected": "Code",
    "phase_removed": "Compile",
    "fix_time_min": 5,
    "fix_ref": "https://github.com/.../commit/..."
  }
}
```

### 2.3 User/Account Identification

Since ASP can run locally or in CI:
1.  **Local Mode:** Read `git config user.name` or an environment variable `ASP_USER_ID`.
2.  **CI Mode:** Read `GITHUB_ACTOR` or equivalent.

## 3. Recommended Code Changes

### 3.1 Update `track_agent_cost` Decorator

Modify `src/asp/telemetry/telemetry.py` to accept and log `project_id` and `user_id`.

```python
# Pseudo-code update
def track_agent_cost(..., project_id: str = None, user_id: str = None):
    # ... resolution logic ...

    # Resolve Context
    current_project = project_id or os.getenv("ASP_PROJECT_ID")
    current_user = user_id or os.getenv("ASP_USER_ID") or get_git_user()

    span = langfuse.start_span(
        tags=[
            f"project:{current_project}",
            f"user:{current_user}"
        ],
        metadata={...}
    )
```

### 3.2 Standardize Defect Types (PROBE/PSP Standard)

Enforce a standard enum for `defect_type` in `log_defect`:

| Code | Type | Description |
| :--- | :--- | :--- |
| 10 | Documentation | Comments, messages |
| 20 | Syntax | Spelling, punctuation, typos, instruction formats |
| 30 | Build, Package | Change management, library, version control |
| 40 | Assignment | Declaration, duplicate names, scope, limits |
| 50 | Interface | Procedure calls and references, I/O, user formats |
| 60 | Checking | Error messages, inadequate checks |
| 70 | Data | Structure, content |
| 80 | Function | Logic, pointers, loops, recursion, computation |
| 90 | System | Configuration, timing, memory |
| 100 | Environment | Design, compile, test, or other support system problems |

## 4. Conclusion

The current telemetry implementation is a strong foundation (capturing latency and basic defect events) but lacks the **contextual tagging** (Project/User) needed for the requested multi-dimension PROBE analysis.

By implementing the **Standardized Tags** and **Defect Type Enum** proposed above, we can enable queries like:
> *"Show me the defect density (Defects/KLOC) for User X on Project Y during the Coding phase."*

This aligns perfectly with the goals of PROBE-style estimation and process improvement.
