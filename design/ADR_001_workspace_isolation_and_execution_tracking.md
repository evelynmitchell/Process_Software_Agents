# ADR 001: Workspace Isolation and Execution Tracking

**Status:** Accepted
**Date:** 2025-11-28
**Session:** 20251128.8
**Deciders:** User, Claude

## Context and Problem Statement

The ASP (Agentic Software Process) platform needs to:

1. Work on external repositories (not just Process_Software_Agents itself)
2. Avoid littering the main repository with test artifacts and execution outputs
3. Track execution history and metrics for PROBE-based improvement
4. Support working on any codebase in isolation

**Problems with previous approach:**
- Test artifacts cluttered the main repository
- Difficult to work on external projects
- Execution artifacts mixed with source code
- Git noise from timestamp updates in test runs

**Core Question:** How do we enable ASP to work on any repository while maintaining clean separation and comprehensive execution tracking?

## Decision Drivers

1. **Isolation:** ASP should work on external codebases without polluting Process_Software_Agents
2. **Auditability:** Need to track what ASP did, when, and on which repositories
3. **PROBE Metrics:** Execution data needed for continuous improvement
4. **Simplicity:** Avoid maintaining multiple overlapping systems
5. **Single Source of Truth:** Don't duplicate data across systems

## Considered Options

### Option 1: Store Everything in Process_Software_Agents
```
Process_Software_Agents/
├── executions/               # Execution records
│   └── task-123/
│       ├── metadata.json
│       ├── metrics.json
│       ├── planning.json
│       ├── design.json
│       └── code_review.json
└── artifacts/                # Test artifacts
    └── (test outputs)
```

**Pros:**
- Everything in git (version controlled)
- Easy to browse execution history
- No external dependencies

**Cons:**
- Clutters main repository
- Large binary artifacts in git
- Doesn't solve isolation problem
- Still can't work on external repos cleanly

### Option 2: Hybrid - Minimal Pointers in Git, Full Data in Langfuse
```
Process_Software_Agents/
└── executions/               # Lightweight pointers
    └── task-123/
        └── metadata.json     # Just: langfuse_trace_id, target_repo, timestamp

Langfuse:                     # Full execution data
└── trace-abc123
    ├── All execution traces
    ├── PROBE metrics
    └── Outcomes
```

**Pros:**
- Git audit trail (what tasks ran)
- Full data in specialized observability platform
- Queryable/searchable execution history

**Cons:**
- Duplication between git and Langfuse
- Need to maintain executions/ directory
- Two systems to keep in sync

### Option 3: Langfuse as Single Source of Truth (CHOSEN) ✅
```
Langfuse (cloud/self-hosted)  # Single source of truth
└── trace-{task-id}
    ├── Task metadata (target repo, branch, PR)
    ├── Execution traces (all agents)
    ├── PROBE metrics
    ├── Outcomes
    └── HITL decisions

/tmp/asp-workspaces/          # Ephemeral workspaces
└── task-{id}/
    ├── target-repo/          # Cloned external repo
    └── .asp/                 # Working artifacts (auto-cleanup)

Process_Software_Agents/      # Clean repository
└── (only ASP platform code)
```

**Pros:**
- ✅ Single source of truth (no duplication)
- ✅ Specialized observability platform (built for this)
- ✅ Clean git repository (no execution clutter)
- ✅ Queryable/searchable via Langfuse API
- ✅ Supports distributed/cloud deployments
- ✅ Built-in analytics, dashboards, metrics
- ✅ Already integrated with ASP

**Cons:**
- ⚠️ Requires Langfuse to be available
- ⚠️ No git-based execution audit trail
- ⚠️ Need Langfuse access for historical queries

## Decision Outcome

**Chosen option:** **Option 3 - Langfuse as Single Source of Truth**

### Rationale

1. **Langfuse is already configured and integrated** - leverages existing infrastructure
2. **Purpose-built for observability** - better than git for execution tracking
3. **PROBE metrics naturally fit** in observability platform
4. **Cleaner architecture** - each system does what it's best at:
   - Git: Source code version control
   - Langfuse: Execution observability and metrics
   - Workspace: Ephemeral working environment

### Architecture

#### Workspace Management

**Location:** `/tmp/asp-workspaces/{task-id}/`

**Structure:**
```
/tmp/asp-workspaces/task-123-fix-auth-bug/
├── my-web-app/                    # Cloned target repository
│   ├── .git/
│   ├── src/
│   └── (target repo contents)
└── .asp/                          # ASP working directory
    ├── planning.json              # Planning agent output
    ├── design.json                # Design agent output
    ├── code_review.json           # Code review results
    └── test_results.json          # Test execution results
```

**Lifecycle:**
1. **Create:** When task starts
2. **Populate:** Clone target repo, initialize .asp/
3. **Work:** All agent operations happen here
4. **Trace:** Send telemetry to Langfuse throughout
5. **Cleanup:** Delete after task completion (or failure)
6. **Preserve (optional):** Archive .asp/ if needed for debugging

#### Execution Tracking in Langfuse

**Trace Structure:**
```json
{
  "trace_id": "trace-abc123",
  "name": "task-123-fix-auth-bug",
  "metadata": {
    "task_id": "task-123",
    "target_repo": "org/my-web-app",
    "target_branch": "claude/fix-auth-bug",
    "workspace_path": "/tmp/asp-workspaces/task-123-fix-auth-bug",
    "pr_url": "https://github.com/org/my-web-app/pull/456",
    "hitl_required": true,
    "hitl_status": "approved"
  },
  "spans": [
    {
      "name": "planning_agent",
      "input": "...",
      "output": "...",
      "metadata": {"tokens": 1500, "cost": 0.002}
    },
    {
      "name": "design_agent",
      "input": "...",
      "output": "...",
      "metadata": {"tokens": 3000, "cost": 0.004}
    }
  ],
  "metrics": {
    "probe_accuracy": 0.95,
    "probe_latency_ms": 45000,
    "probe_cost_usd": 0.025,
    "probe_quality_score": 0.88
  }
}
```

**PROBE Metrics Captured:**
- **Accuracy:** Did the solution work? (from tests, HITL feedback)
- **Latency:** How long did execution take?
- **Cost:** Token usage, API costs
- **Quality:** Code review scores, test coverage

### Workflow Example

**Scenario:** User asks ASP to fix authentication bug in `org/my-web-app`

**Steps:**

1. **Create Workspace**
   ```python
   workspace = create_workspace("task-123-fix-auth-bug")
   # Creates: /tmp/asp-workspaces/task-123-fix-auth-bug/
   ```

2. **Clone Repository**
   ```python
   clone_repository("org/my-web-app", workspace.target_repo_path)
   # Clones to: workspace/my-web-app/
   ```

3. **Initialize Langfuse Trace**
   ```python
   trace = langfuse.trace(
       name="task-123-fix-auth-bug",
       metadata={
           "target_repo": "org/my-web-app",
           "workspace": str(workspace.path)
       }
   )
   ```

4. **Execute Agents (with tracing)**
   ```python
   planning_result = planning_agent.run(task, trace=trace)
   design_result = design_agent.run(planning_result, trace=trace)
   code_result = code_agent.run(design_result, trace=trace)
   ```

5. **Create PR in Target Repo**
   ```python
   pr_url = create_pr("org/my-web-app", "claude/fix-auth-bug")
   trace.update(metadata={"pr_url": pr_url})
   ```

6. **HITL Approval (optional)**
   ```python
   if hitl_required:
       approval = await_hitl_approval(trace.id)
       trace.update(metadata={"hitl_status": approval.status})
   ```

7. **Finalize Trace with PROBE Metrics**
   ```python
   trace.score(
       name="probe_accuracy",
       value=test_results.pass_rate
   )
   trace.score(
       name="probe_cost_usd",
       value=calculate_total_cost(trace)
   )
   ```

8. **Cleanup Workspace**
   ```python
   cleanup_workspace(workspace)
   # Deletes: /tmp/asp-workspaces/task-123-fix-auth-bug/
   ```

### Working on Process_Software_Agents Itself

**Question:** How does ASP work on its own repository without cluttering it?

**Answer:** Same workflow! Fork/clone approach:

```python
# Option A: Clone to workspace (even if it's the same repo)
workspace = create_workspace("task-456-add-feature")
clone_repository("evelynmitchell/Process_Software_Agents", workspace.target_repo_path)
# Work happens in workspace, not in current directory

# Option B: Fork first, then clone
fork_url = fork_repository("evelynmitchell/Process_Software_Agents")
clone_repository(fork_url, workspace.target_repo_path)
# Work on fork in isolation
```

**Benefits:**
- No artifacts in current working directory
- Can test changes without affecting current environment
- Clean separation even when working on self

## Consequences

### Positive

✅ **Clean Repository:** No execution artifacts cluttering Process_Software_Agents
✅ **True Isolation:** Can work on any repository without mixing concerns
✅ **Purpose-Built Tracking:** Langfuse designed for LLM observability
✅ **PROBE Metrics:** Natural fit in observability platform
✅ **Queryable History:** Langfuse API for analytics and reporting
✅ **Scalable:** Works for distributed/multi-instance deployments
✅ **Rich Analytics:** Built-in dashboards, cost tracking, performance metrics

### Negative

⚠️ **Langfuse Dependency:** Requires Langfuse to be available for execution history
⚠️ **No Git Audit Trail:** Can't browse execution history via git log
⚠️ **Debugging:** Need Langfuse access to debug past executions

### Mitigation Strategies

**For Langfuse Availability:**
- Support self-hosted Langfuse (not just cloud)
- Graceful degradation if Langfuse unavailable
- Optional local trace export for critical executions

**For Git Audit Trail:**
- Generate markdown reports from Langfuse for important milestones
- Optional: PR descriptions include Langfuse trace links
- Session summaries capture major execution outcomes

**For Debugging:**
- Preserve .asp/ workspace artifacts for recent executions
- Export critical traces to local files when needed
- Implement trace replay functionality

## Implementation Plan

### Phase 1: Workspace Management (Session 8)
- [ ] Create `WorkspaceManager` service
- [ ] Implement workspace creation/cleanup
- [ ] Add repository cloning utilities
- [ ] Test with "hellogit" example

### Phase 2: Repository Operations (Future)
- [ ] Implement `RepositoryManager` service
- [ ] Add fork detection and creation
- [ ] Branch creation and management
- [ ] PR creation automation

### Phase 3: Langfuse Integration Enhancement (Future)
- [ ] Standardize trace metadata schema
- [ ] Add PROBE metrics helpers
- [ ] Create HITL trace annotations
- [ ] Build analytics queries for PROBE

### Phase 4: Multi-Repo Orchestration (Future)
- [ ] Multi-repo task detection
- [ ] Cross-repo artifact coordination
- [ ] Parallel workspace management

## Related Documents

- `design/multi_repo_workflow_implementation.md` - Original multi-repo design (needs update)
- `design/HITL_QualityGate_Architecture.md` - Section 2.3 (Repository Management Strategy)
- `Summary/summary20251128.6.md` - Multi-repo workflow planning session
- `Summary/summary20251128.8.md` - This session (architecture decisions)

## Notes

**Key Insight from User:**
> "We wasted a lot of time last week because test artifacts got littered through the repo. Creating git repos to hold test artifacts would have avoided that."

This ADR addresses that problem by:
1. Isolating all work in ephemeral workspaces
2. Never storing execution artifacts in Process_Software_Agents
3. Using Langfuse for execution tracking (purpose-built for this)

**Follow-up Questions for Future Sessions:**
- Should we support workspace persistence for long-running tasks?
- How do we handle workspace cleanup on system crash?
- Should .asp/ artifacts be optionally archived to cloud storage?
- What's the retention policy for Langfuse traces?

---

**Status:** Accepted and ready for implementation
**Next Steps:** Implement Phase 1 (WorkspaceManager) in session 9
