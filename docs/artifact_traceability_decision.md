# Architecture Decision Record: Artifact Traceability in Multi-Agent Pipeline

**Date:** 2025-11-19
**Status:** Proposed
**Deciders:** Development Team
**Related:**
- `error_correction_feedback_loops_decision.md` (Phase-aware feedback)
- `planning_agent_architecture_decision.md` (ProjectPlan artifact)
- `design_agent_architecture_decision.md` (DesignSpecification artifact)

---

## Context and Problem Statement

During implementation of the `PlanningDesignOrchestrator`, we discovered an artifact traceability gap:

**The Core Problem:**
> Downstream agents and pipeline stages need access to artifacts from earlier phases (e.g., Postmortem Agent needs ProjectPlan), but there's no consistent mechanism for passing or referencing these artifacts.

**Current State:**
- `DesignInput` contains full `ProjectPlan` object (passed to Design Agent)
- `DesignSpecification` output does **NOT** contain `ProjectPlan` or reference to it
- Orchestrator has internal access to `ProjectPlan` but doesn't return it
- E2E tests need to mock `ProjectPlan` for Postmortem Agent because it's not accessible
- No standard way to trace which plan/design/review produced which code

**Which Agents Need Which Artifacts:**

| Agent | Needs ProjectPlan? | Needs DesignSpecification? | Needs GeneratedCode? |
|-------|-------------------|---------------------------|---------------------|
| Planning Agent | ❌ No | ❌ No | ❌ No |
| Design Agent | ✅ **Yes** (required) | ❌ No | ❌ No |
| Design Review Agent | ❌ No | ✅ **Yes** (required) | ❌ No |
| Code Agent | ❌ **No** | ✅ **Yes** (required) | ❌ No |
| Code Review Agent | ❌ No | ✅ Yes (optional) | ✅ **Yes** (required) |
| Test Agent | ❌ No | ✅ Yes (optional) | ✅ **Yes** (required) |
| Postmortem Agent | ✅ **Yes** (required) | ✅ Yes (optional) | ✅ **Yes** (required) |

**Key Insight:** Code Agent does NOT need ProjectPlan directly. The DesignSpecification already contains all planning information translated into concrete design (API contracts, components, architecture). The ProjectPlan is primarily needed for:
- **Design Agent** - to create the design from decomposed semantic units
- **Postmortem Agent** - for effort estimation analysis (estimated vs actual complexity)

**Specific Issues:**

1. **Postmortem Agent Data Dependency:**
   - Needs `ProjectPlan.semantic_units` for effort log analysis
   - Needs `ProjectPlan.total_est_complexity` for comparison with actual
   - Currently: E2E test must create mock `ProjectPlan` because orchestrator doesn't return it

2. **Debugging and Audit Trail:**
   - When Code Agent fails, which specific plan and design was it using?
   - When reviewing artifacts, how do we trace back to the original plan?
   - No way to correlate artifacts across phases

3. **Artifact Persistence:**
   - Agents write artifacts to `artifacts/{task_id}/plan.json`, `design.json`, etc.
   - No explicit links between these files (only implicit via `task_id`)
   - If design is regenerated after feedback, how do we track version history?

4. **Orchestrator Return Values:**
   - `PlanningDesignOrchestrator.execute()` returns `(DesignSpecification, DesignReviewReport)`
   - `ProjectPlan` generated internally but discarded
   - Caller has no access to plan unless they stored it separately
   - Postmortem Agent later in pipeline needs ProjectPlan but has no way to get it

---

## Decision Drivers

1. **Traceability:** Every artifact should reference its upstream dependencies
2. **Telemetry:** PROBE-AI needs complete artifact chain for learning
3. **Debugging:** Developers need to trace failures back to source artifacts
4. **Simplicity:** Solution should be easy to use and maintain
5. **Backward Compatibility:** Minimize breaking changes to existing agents
6. **Storage Efficiency:** Avoid excessive data duplication
7. **Version History:** Support artifact regeneration from feedback loops

---

## Considered Options

### Option 1: Embed Full Upstream Artifacts (Current Partial Implementation)

**Architecture:**
- Each output artifact contains complete copies of all upstream artifacts
- `DesignSpecification` contains full `ProjectPlan` object
- `GeneratedCode` contains full `DesignSpecification` + `ProjectPlan`
- `TestReport` contains full `GeneratedCode` + `DesignSpecification` + `ProjectPlan`

**Example:**
```python
class DesignSpecification(BaseModel):
    task_id: str
    project_plan: ProjectPlan  # NEW: Full upstream artifact
    api_contracts: list[APIContract]
    # ... other fields

class GeneratedCode(BaseModel):
    task_id: str
    design_specification: DesignSpecification  # Includes nested ProjectPlan
    files: list[GeneratedFile]
    # ... other fields
```

**Orchestrator Changes:**
```python
# No change needed - Design Agent already receives ProjectPlan
design_spec = design_agent.execute(design_input)
# design_spec.project_plan is available
return design_spec, design_review
```

**Pros:**
- ✅ Complete traceability - all upstream data available
- ✅ No need to look up external artifacts
- ✅ Self-contained artifacts (all context included)
- ✅ Easy to serialize and share artifacts
- ✅ Design Agent already uses this pattern (receives `ProjectPlan` in input)

**Cons:**
- ❌ Data duplication grows exponentially (each artifact contains all previous)
- ❌ Large artifact files (GeneratedCode would contain entire ProjectPlan + DesignSpec)
- ❌ Breaking change - requires updating `DesignSpecification` schema
- ❌ LLM responses larger (includes nested artifacts in JSON)
- ❌ Increased API costs (larger responses)
- ❌ Version confusion (which version of plan if regenerated after feedback?)

**Cost:** High initial implementation cost, ongoing storage/API cost

**Verdict:** ❌ **REJECTED** - Excessive data duplication and complexity

---

### Option 2: Artifact References (File Paths)

**Architecture:**
- Each artifact stores **file paths** to upstream artifact files
- Agents/orchestrators load referenced artifacts when needed
- Artifacts stored in standardized locations: `artifacts/{task_id}/plan.json`, etc.

**Example:**
```python
class DesignSpecification(BaseModel):
    task_id: str
    project_plan_artifact_path: str  # NEW: e.g., "artifacts/HW-001/plan.json"
    project_plan_version: str  # NEW: git commit hash or timestamp
    api_contracts: list[APIContract]
    # ... other fields

class GeneratedCode(BaseModel):
    task_id: str
    design_artifact_path: str  # e.g., "artifacts/HW-001/design.json"
    design_version: str  # git commit hash or timestamp
    files: list[GeneratedFile]
    # ... other fields
```

**Orchestrator Changes:**
```python
def execute(self, requirements: TaskRequirements) -> PlanningDesignResult:
    # Execute planning
    project_plan = planning_agent.execute(requirements)
    plan_path = f"artifacts/{requirements.task_id}/plan.json"

    # Execute design
    design_spec = design_agent.execute(design_input)
    # Design agent populates: design_spec.project_plan_artifact_path = plan_path

    # Return result with paths
    return PlanningDesignResult(
        design_specification=design_spec,
        design_review=design_review,
        project_plan_path=plan_path,
    )
```

**Loading Referenced Artifacts:**
```python
# Postmortem Agent needs project plan
def get_project_plan(design_spec: DesignSpecification) -> ProjectPlan:
    with open(design_spec.project_plan_artifact_path) as f:
        return ProjectPlan(**json.load(f))
```

**Pros:**
- ✅ No data duplication - references instead of copies
- ✅ Small artifact files (only paths, not full objects)
- ✅ Clear version tracking via git commit hashes
- ✅ Easy to trace artifact lineage
- ✅ Load artifacts on-demand (performance benefit)

**Cons:**
- ⚠️ Requires file system access to load referenced artifacts
- ⚠️ Artifacts less self-contained (need to load dependencies)
- ⚠️ Broken references if artifacts moved/deleted
- ⚠️ Breaking change - requires schema updates

**Cost:** Medium implementation cost, low ongoing cost

**Verdict:** ✅ **VIABLE** - Good balance, but requires file I/O

---

### Option 3: Orchestrator Returns Complete Artifact Set (RECOMMENDED)

**Architecture:**
- Orchestrators return **all artifacts** generated during execution
- Each artifact remains independent (no embedded references)
- Caller (E2E test, main pipeline) is responsible for passing artifacts to downstream agents

**Example:**
```python
@dataclass
class PlanningDesignResult:
    """Complete result from Planning-Design-Review orchestration."""
    project_plan: ProjectPlan
    design_specification: DesignSpecification
    design_review: DesignReviewReport

class PlanningDesignOrchestrator:
    def execute(
        self,
        requirements: TaskRequirements
    ) -> PlanningDesignResult:
        # Execute planning
        project_plan = self._execute_planning(requirements)

        # Execute design
        design_spec = self._execute_design(requirements, project_plan, ...)

        # Execute review
        design_review = self._execute_design_review(design_spec)

        # Return ALL artifacts
        return PlanningDesignResult(
            project_plan=project_plan,
            design_specification=design_spec,
            design_review=design_review,
        )
```

**E2E Test Usage:**
```python
# Execute orchestrator
result = orchestrator.execute(requirements)

# All artifacts available
project_plan = result.project_plan
design_spec = result.design_specification
design_review = result.design_review

# Pass to Code Agent
code_input = CodeInput(
    task_id=requirements.task_id,
    design_specification=design_spec,
    coding_standards="...",
)
generated_code = code_agent.execute(code_input)

# Pass to Postmortem Agent
postmortem_input = PostmortemInput(
    task_id=requirements.task_id,
    project_plan=project_plan,  # Available from orchestrator result!
    generated_code=generated_code,
    # ... other fields
)
postmortem_report = postmortem_agent.execute(postmortem_input)
```

**Artifact Files Still Written:**
- `artifacts/{task_id}/plan.json` - ProjectPlan
- `artifacts/{task_id}/design.json` - DesignSpecification
- `artifacts/{task_id}/design_review.json` - DesignReviewReport
- Each file is self-contained (no references)
- Git commits provide version history

**Pros:**
- ✅ No schema changes to existing models
- ✅ Orchestrator provides all artifacts to caller
- ✅ Caller has complete control over artifact flow
- ✅ No data duplication within artifacts
- ✅ Easy to extend (add more artifacts to result)
- ✅ Works with or without file system (in-memory tests possible)
- ✅ Backward compatible (existing individual agent calls unchanged)

**Cons:**
- ⚠️ Caller must explicitly pass artifacts to downstream stages
- ⚠️ More parameters to track in E2E tests and main pipeline
- ⚠️ No implicit traceability within artifacts themselves

**Cost:** Low implementation cost (just return value changes)

**Verdict:** ✅ **RECOMMENDED** - Clean, simple, no breaking changes

---

### Option 4: Artifact ID Chain (Metadata)

**Architecture:**
- Each artifact has a unique ID (e.g., UUID or `{task_id}-{phase}-{timestamp}`)
- Artifacts store IDs of upstream dependencies (not full objects or paths)
- Separate artifact registry/database tracks all artifacts

**Example:**
```python
class DesignSpecification(BaseModel):
    artifact_id: str = "HW-001-design-20251119-143022"
    task_id: str
    upstream_artifact_ids: list[str] = ["HW-001-plan-20251119-142500"]
    api_contracts: list[APIContract]
    # ... other fields

# Artifact Registry (database or in-memory)
artifact_registry = {
    "HW-001-plan-20251119-142500": project_plan_object,
    "HW-001-design-20251119-143022": design_spec_object,
}

# Retrieve upstream artifact
def get_upstream(artifact: DesignSpecification, phase: str) -> Any:
    plan_id = [id for id in artifact.upstream_artifact_ids
               if phase in id][0]
    return artifact_registry[plan_id]
```

**Pros:**
- ✅ Clear dependency graph
- ✅ No data duplication
- ✅ Supports complex artifact relationships
- ✅ Good for telemetry database integration

**Cons:**
- ❌ Requires artifact registry infrastructure
- ❌ More complex to implement and maintain
- ❌ Requires database or in-memory store
- ❌ Over-engineered for current needs

**Cost:** High implementation cost

**Verdict:** ❌ **REJECTED** - Too complex for current requirements

---

## Decision Outcome

**Chosen Option:** **Option 3: Orchestrator Returns Complete Artifact Set**

**Rationale:**
1. **Simplicity:** No schema changes, just return value updates
2. **Flexibility:** Caller controls artifact flow, easy to test
3. **No Duplication:** Artifacts remain independent and lightweight
4. **Backward Compatible:** Individual agents unchanged
5. **Future-Proof:** Easy to add more artifacts or metadata later

---

## Implementation Plan

### Phase 1: Update Orchestrator Return Types (Immediate)

1. **Create Result Dataclasses:**
   ```python
   # src/asp/orchestrators/types.py
   from dataclasses import dataclass
   from asp.models.planning import ProjectPlan
   from asp.models.design import DesignSpecification
   from asp.models.design_review import DesignReviewReport

   @dataclass
   class PlanningDesignResult:
       """Result from Planning-Design-Review orchestration."""
       project_plan: ProjectPlan
       design_specification: DesignSpecification
       design_review: DesignReviewReport
   ```

2. **Update PlanningDesignOrchestrator:**
   ```python
   def execute(
       self,
       requirements: TaskRequirements,
       design_constraints: Optional[str] = None,
   ) -> PlanningDesignResult:  # Changed return type
       # ... existing implementation ...

       # Return all three artifacts
       return PlanningDesignResult(
           project_plan=project_plan,
           design_specification=design_spec,
           design_review=review_report,
       )
   ```

3. **Update E2E Test:**
   ```python
   # Execute orchestrator
   result = orchestrator.execute(requirements)

   # Unpack results
   project_plan = result.project_plan
   design_spec = result.design_specification
   design_review = result.design_review

   # Remove mock ProjectPlan - use real one from orchestrator
   # (Delete lines 140-159 in current test)
   ```

### Phase 2: Add Metadata for Traceability (Optional Enhancement)

Add optional metadata fields to track artifact lineage:

```python
class DesignSpecification(BaseModel):
    task_id: str
    # ... existing fields ...

    # Optional metadata for traceability (backward compatible)
    metadata: Optional[dict] = Field(
        default=None,
        description="Optional metadata for artifact traceability",
        examples=[{
            "generated_at": "2025-11-19T14:30:22Z",
            "agent_version": "1.0.0",
            "upstream_artifacts": {
                "plan": "artifacts/HW-001/plan.json",
                "plan_commit": "a1b2c3d",
            },
            "feedback_iteration": 1,
        }]
    )
```

### Phase 3: Future Orchestrators (Follow Same Pattern)

When implementing complete pipeline orchestrator:

```python
@dataclass
class CompletePipelineResult:
    """Result from complete 7-agent pipeline."""
    project_plan: ProjectPlan
    design_specification: DesignSpecification
    design_review: DesignReviewReport
    generated_code: GeneratedCode
    code_review: CodeReviewReport
    test_report: TestReport
    postmortem_report: PostmortemReport

class CompletePipelineOrchestrator:
    def execute(
        self,
        requirements: TaskRequirements
    ) -> CompletePipelineResult:
        # Execute all agents
        # Return all artifacts
        pass
```

---

## Consequences

### Positive

1. **Immediate Fix:**
   - E2E test no longer needs mock `ProjectPlan`
   - Postmortem Agent gets real plan data
   - All artifacts available to caller

2. **Clean Architecture:**
   - Artifacts remain independent
   - No circular dependencies
   - Easy to serialize/deserialize

3. **Testing Benefits:**
   - In-memory tests possible (no file system required)
   - Easy to mock individual artifacts
   - Clear artifact flow in tests

4. **Flexibility:**
   - Caller controls which artifacts to pass to which agents
   - Easy to add new artifacts to result objects
   - No breaking changes to existing code

### Negative

1. **Caller Responsibility:**
   - E2E tests and pipeline must explicitly pass artifacts
   - More parameters to track
   - Potential for passing wrong artifact to wrong agent

2. **No Implicit Traceability:**
   - Artifacts don't store references to upstream artifacts
   - Must rely on caller to maintain relationship
   - Could add optional metadata later if needed

### Mitigations

1. **Type Safety:**
   - Use dataclasses with type hints
   - Pydantic validation ensures correct artifact types
   - IDE autocomplete helps developers

2. **Documentation:**
   - Document artifact flow in orchestrator docstrings
   - Provide E2E test examples showing correct usage
   - Add architecture diagrams showing artifact relationships

3. **Future Enhancement:**
   - Can add optional metadata later without breaking changes
   - Can build artifact registry if needed
   - Can implement Option 2 (file references) incrementally

---

## Example: Complete E2E Flow with Traceability

```python
def test_complete_pipeline_with_traceability():
    """E2E test showing complete artifact traceability."""

    # Step 1-3: Planning-Design-Review
    orchestrator = PlanningDesignOrchestrator()
    result = orchestrator.execute(
        requirements=TaskRequirements(
            task_id="HW-001",
            description="Hello World API",
            requirements="Build REST API...",
        )
    )

    # All artifacts available
    project_plan = result.project_plan
    design_spec = result.design_specification
    design_review = result.design_review

    # Step 4: Code Generation
    # NOTE: Code Agent does NOT need ProjectPlan - design has all the info
    code_input = CodeInput(
        task_id="HW-001",
        design_specification=design_spec,  # Only design needed
        coding_standards="PEP 8",
    )
    generated_code = code_agent.execute(code_input)

    # Step 5: Testing
    # NOTE: Test Agent works from generated code + optional design reference
    test_input = TestInput(
        task_id="HW-001",
        generated_code=generated_code,
        design_specification=design_spec,  # Optional - for validation
        test_framework="pytest",
    )
    test_report = test_agent.execute(test_input)

    # Step 6: Postmortem Analysis
    # NOTE: Postmortem Agent DOES need ProjectPlan for effort analysis
    postmortem_input = PostmortemInput(
        task_id="HW-001",
        project_plan=project_plan,  # REQUIRED - from orchestrator result!
        generated_code=generated_code,
        test_report=test_report,
        effort_log=[...],
        defect_log=[...],
    )
    postmortem_report = postmortem_agent.execute(postmortem_input)

    # Complete artifact chain available for telemetry
    telemetry.log_pipeline_execution({
        "task_id": "HW-001",
        "plan_complexity": project_plan.total_est_complexity,
        "design_status": design_review.overall_assessment,
        "code_loc": generated_code.total_lines_of_code,
        "test_coverage": test_report.coverage_percent,
        "actual_defects": len(postmortem_report.defects),
    })
```

### Artifact Flow Diagram

```
TaskRequirements
     ↓
┌────────────────────────────────────────────┐
│  PlanningDesignOrchestrator                │
│                                            │
│  Planning → Design → Design Review         │
│                                            │
│  Returns: PlanningDesignResult             │
│    - project_plan                          │
│    - design_specification                  │
│    - design_review                         │
└────────────────────────────────────────────┘
     ↓
     ├─→ project_plan ──────────────────────────┐
     │                                           │
     └─→ design_specification                    │
              ↓                                  │
         Code Agent ──→ generated_code           │
              ↓              ↓                   │
         Test Agent ──→ test_report              │
              ↓              ↓                   ↓
         Postmortem Agent ←─────────────────────┘
         (needs ALL three: plan, code, test)
```

**Key Points:**
1. **ProjectPlan flows directly to Postmortem** - skips Code and Test agents
2. **DesignSpecification flows through all downstream agents** - contains translated plan info
3. **Code Agent never sees ProjectPlan** - design has everything it needs
4. **Orchestrator returns all three artifacts** - caller decides what goes where

---

## Alternatives Considered for Future

If we need more sophisticated traceability in the future:

1. **Hybrid Approach:** Orchestrators return artifacts + optional metadata
2. **Artifact Database:** Build SQLite database of all artifacts with relationships
3. **Git-Based Traceability:** Use git commit messages and tags to link artifacts
4. **Blockchain/Merkle Tree:** Cryptographic proof of artifact lineage (overkill)

---

## Related Decisions

- **Phase-Aware Feedback:** Orchestrator must track which artifacts were regenerated after feedback
- **Telemetry:** All artifacts should be available for PROBE-AI learning
- **Artifact Persistence:** Git commits provide version history of artifacts

---

**Decision Status:** Proposed
**Next Review:** After implementing Phase 1
**Document Owner:** Development Team

**References:**
- `error_correction_feedback_loops_decision.md` - Feedback loop architecture
- `planning_agent_architecture_decision.md` - ProjectPlan artifact definition
- `design_agent_architecture_decision.md` - DesignSpecification artifact definition
- `tests/e2e/test_all_agents_hello_world_e2e.py` - Current E2E test showing the problem
