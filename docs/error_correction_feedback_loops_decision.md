# Architecture Decision Record: Error Correction and Feedback Loops in Multi-Agent Workflow

**Date:** 2025-11-17
**Status:** Proposed
**Deciders:** Development Team
**Related:**
- Planning Agent ADR (`planning_agent_architecture_decision.md`)
- Design Agent ADR (`design_agent_architecture_decision.md`)
- Design Review Agent ADR (`design_review_agent_architecture_decision.md`)
- PRD Section 6.2.4 (Quality Gates and Error Handling)

---

## Context and Problem Statement

As we implement the Code Agent (FR-4) and prepare for the main TSP Orchestrator, we must decide how errors discovered in downstream phases should be corrected. Specifically:

**The Core Question:**
> When the Design Review Agent finds errors that originate from the Planning phase (not the Design phase), how should those errors be corrected?

**Current State:**
- We have implemented 3 agents: Planning, Design, Design Review
- Design Review Agent produces `DesignReviewReport` with `overall_assessment`: PASS, FAIL, or NEEDS_IMPROVEMENT
- PRD specifies: "Design Review Agent → FAIL: Loop back to Design Agent with defects"
- **No mechanism exists to route errors back to earlier phases**

**Problem Scenarios:**

1. **Planning Error Discovered in Design Review:**
   - Planning Agent decomposes task incorrectly (missing critical semantic unit)
   - Design Agent creates design based on incomplete decomposition
   - Design Review Agent identifies missing functionality
   - **Current behavior:** Can only fail back to Design Agent
   - **Question:** Should we fail back to Planning Agent instead?

2. **Planning Error Discovered During Code Generation:**
   - Code Agent finds semantic unit complexity estimates are wildly inaccurate
   - Code Agent cannot generate implementable code due to missing requirements
   - **Question:** Should Code Agent be able to request replanning?

3. **Design Error Discovered in Code Review:**
   - Code Review finds security vulnerability in generated code
   - Root cause: Design specification missing security requirements
   - **Question:** Should we regenerate design, or just regenerate code?

4. **Multi-Phase Error:**
   - Error affects both planning AND design
   - Example: Missing authentication requirement (planning) leads to missing auth API design (design)
   - **Question:** Do we fix both phases, or just the most recent?

**Key Challenges:**
1. How to identify which phase introduced a defect?
2. How to route failures to the correct upstream agent?
3. How to prevent infinite loops (A → B → A → B...)?
4. How to maintain audit trail of corrections?
5. How to balance correction thoroughness vs. development velocity?

---

## Decision Drivers

1. **PSP/TSP Alignment:** Defects should be corrected in the phase where they were injected (PSP principle)
2. **Quality:** Preventing error propagation is more important than speed
3. **Traceability:** Must maintain full audit trail for PROBE-AI learning
4. **Simplicity:** Orchestration logic should be understandable and debuggable
5. **Cost Efficiency:** Minimize unnecessary rework and LLM API calls
6. **Developer Experience:** Clear error messages and correction paths
7. **Scalability:** Solution must work for 7-agent workflow (not just 3 agents)

---

## Considered Options

### Option 1: Single-Step Feedback (Current Implementation) ❌

**Architecture:**
- Each review agent can only fail back to the immediately preceding agent
- Design Review → Design Agent
- Code Review → Code Agent
- Test Agent → Code Agent
- No multi-phase feedback

**Flow Example:**
```
Planning → Design → Design Review (finds planning error)
                    ↓
                  FAIL → Design Agent (must work around planning error)
```

**Pros:**
- ✅ Simple orchestration logic
- ✅ No complex routing decisions
- ✅ Fast to implement
- ✅ Predictable behavior

**Cons:**
- ❌ Planning errors never get corrected
- ❌ Violates PSP principle (fix defects where injected)
- ❌ Leads to design workarounds instead of proper fixes
- ❌ Accumulates technical debt
- ❌ Poor training data for PROBE-AI (defect phase tracking inaccurate)
- ❌ Doesn't align with PRD's defect tracking requirements

**Cost:** No additional API calls beyond single retry

**Verdict:** ❌ **REJECTED** - Violates PSP principles and leads to poor quality

---

### Option 2: Phase-Aware Feedback with Orchestrator Routing ✅ RECOMMENDED

**Architecture:**
- Issues include `affected_phase` field: "Planning", "Design", "Code", "Test"
- Review reports include both phase-specific and aggregated issues
- Orchestrator analyzes issues and routes to appropriate upstream agent
- Each agent can be invoked multiple times until issues resolved

**Data Model Changes:**

```python
class DesignIssue(BaseModel):
    issue_id: str
    category: str
    severity: str
    description: str
    evidence: str
    impact: str
    affected_phase: Literal["Planning", "Design", "Both"]  # NEW FIELD

class DesignReviewReport(BaseModel):
    overall_assessment: Literal["PASS", "FAIL", "NEEDS_IMPROVEMENT"]
    planning_phase_issues: list[DesignIssue]  # NEW: Issues from planning
    design_phase_issues: list[DesignIssue]    # NEW: Issues from design
    # ... existing fields
```

**Orchestrator Logic:**

```python
def run_design_phase_with_review(requirements, project_plan, max_iterations=3):
    """Execute design phase with feedback loop."""

    for iteration in range(max_iterations):
        # Generate design
        design_spec = design_agent.execute(requirements, project_plan)

        # Review design
        review_report = design_review_agent.execute(design_spec)

        if review_report.overall_assessment == "PASS":
            return design_spec, review_report

        # Analyze failures
        if review_report.planning_phase_issues:
            # Route back to Planning Agent
            project_plan = planning_agent.execute(
                requirements,
                feedback=review_report.planning_phase_issues
            )
            # Continue loop to regenerate design with new plan

        elif review_report.design_phase_issues:
            # Route back to Design Agent only
            # Continue loop to regenerate design

        else:
            # No phase identified - fail back to design by default
            pass

    raise MaxIterationsExceeded("Could not resolve design issues")
```

**Flow Example:**
```
Planning → Design → Design Review (finds planning error)
                    ↓
                  Analyze issues
                    ↓
          planning_phase_issues found
                    ↓
           FAIL → Planning Agent (regenerate plan)
                    ↓
                  Design Agent (regenerate design with new plan)
                    ↓
                  Design Review (verify fix)
                    ↓
                  PASS → Continue to Code Agent
```

**Pros:**
- ✅ Aligns with PSP principle (fix defects where injected)
- ✅ Prevents error propagation through pipeline
- ✅ Accurate defect phase tracking for PROBE-AI
- ✅ Clear audit trail of corrections
- ✅ Extensible to 7-agent workflow
- ✅ Maintains quality over speed
- ✅ Prevents technical debt accumulation

**Cons:**
- ⚠️ More complex orchestrator logic
- ⚠️ Additional API costs for replanning/redesign
- ⚠️ Longer overall task completion time
- ⚠️ Need max iteration limits to prevent infinite loops
- ⚠️ Agents need to accept feedback parameter

**Cost Impact:**
- Worst case: 2x cost (replan + redesign)
- Expected: 1.2-1.5x cost (most designs pass on first try)
- Long-term: Lower cost due to fewer defects in later phases

**Iteration Limits:**
- Planning → Design → Review: Max 3 iterations
- Code → Review: Max 3 iterations
- Test: Max 2 iterations
- Total pipeline: Max 10 iterations before human escalation

**Verdict:** ✅ **RECOMMENDED** - Best alignment with PSP/TSP principles

---

### Option 3: Progressive Validation (Agent-Level Error Detection)

**Architecture:**
- Each agent validates its inputs BEFORE execution
- Design Agent validates Project Plan before designing
- Code Agent validates Design Spec before coding
- Agents can reject invalid inputs and request upstream fixes

**Flow Example:**
```
Planning → Design Agent validates plan
            ↓
          Validation FAILED (missing semantic units)
            ↓
          Request replanning → Planning Agent
            ↓
          Updated plan → Design Agent
            ↓
          Validation PASSED → Generate design
```

**Pros:**
- ✅ Early error detection (fail fast)
- ✅ Prevents wasted work on invalid inputs
- ✅ Clear separation of validation vs. review
- ✅ Simpler than full phase-aware feedback

**Cons:**
- ❌ Agents can only validate structure, not semantic quality
- ❌ Misses errors that require domain expertise (security, performance)
- ❌ Validation logic duplicates some review logic
- ❌ Doesn't handle discovered errors (only input validation)

**Verdict:** 🔶 **PARTIAL SOLUTION** - Good complement to Option 2, not replacement

---

### Option 4: Human-in-the-Loop Escalation Only

**Architecture:**
- All failures stop at current phase
- Agent attempts fixes within its phase only
- After max retries, escalate to human for manual correction
- No automated multi-phase feedback

**Flow Example:**
```
Planning → Design → Design Review (finds planning error)
                    ↓
                  FAIL → Design Agent (attempt workaround)
                    ↓
                  Still FAIL after 3 tries
                    ↓
                  ESCALATE TO HUMAN
                    ↓
          Human manually fixes plan + design
```

**Pros:**
- ✅ Simple implementation
- ✅ Human expert judgment for complex issues
- ✅ No infinite loop risk

**Cons:**
- ❌ Not truly autonomous (requires human intervention)
- ❌ Defeats purpose of autonomous agent system
- ❌ Doesn't scale (human becomes bottleneck)
- ❌ Poor learning loop (no automated correction data)

**Verdict:** ❌ **REJECTED** - Contradicts autonomous development goal

---

## Decision Outcome

**Chosen Option:** **Option 2: Phase-Aware Feedback with Orchestrator Routing**

**Rationale:**
1. **PSP Alignment:** Follows PSP best practice of fixing defects in phase where injected
2. **Quality First:** Prevents error propagation, even at cost of speed
3. **PROBE-AI Ready:** Accurate phase tracking enables defect injection analysis
4. **Scalable:** Pattern works for all 7 agents in workflow
5. **Measurable:** Can track correction rates, phase yields, and improvement over time

**Implementation Plan:**

### Phase 1: Data Model Updates (Immediate)
- Add `affected_phase` field to `DesignIssue`, `CodeIssue`, `TestIssue` models
- Add phase-specific issue groupings to all review reports
- Update existing agents to populate phase information

### Phase 2: Agent Feedback Support (Before Code Agent)
- Add optional `feedback` parameter to Planning Agent
- Add optional `feedback` parameter to Design Agent
- Agents should incorporate feedback into regeneration

### Phase 3: Orchestrator Implementation (After Code/Code Review Agents)
- Build main TSP Orchestrator with phase-aware routing
- Implement iteration limits and loop detection
- Add telemetry for correction cycles

### Phase 4: Iteration Limits and Safeguards
- Max 3 iterations per phase pair (e.g., Design → Review → Design)
- Max 10 total iterations before human escalation
- Track correction attempts in telemetry

**Complement with Option 3:**
- Add input validation to all agents (fail fast for structural errors)
- Reserve phase-aware feedback for semantic/quality errors

---

## Consequences

### Positive

1. **Quality Improvements:**
   - Defects fixed at source phase (lower cost than downstream fixes)
   - Reduced error propagation through pipeline
   - Better alignment with PSP/TSP quality principles

2. **Better Telemetry:**
   - Accurate defect injection phase tracking
   - Correction cycle metrics (planning corrections, design corrections, etc.)
   - Phase yield calculations (% defects caught in review vs. test)

3. **PROBE-AI Benefits:**
   - Training data includes correction patterns
   - Can learn which types of errors require replanning vs. redesign
   - Defect density by phase enables better estimation

4. **Auditability:**
   - Complete correction history in telemetry
   - Clear attribution of which phase introduced error
   - Traceable decision path for quality gates

### Negative

1. **Increased Complexity:**
   - Orchestrator logic more complex than simple linear flow
   - Need careful iteration limit management
   - More test cases required for feedback scenarios

2. **Cost Impact:**
   - Additional LLM API calls for replanning/redesign
   - Estimated 20-50% cost increase for tasks requiring corrections
   - Mitigated by: fewer downstream defects, better quality

3. **Latency Impact:**
   - Tasks with corrections take longer to complete
   - Estimated 30-80% latency increase for corrected tasks
   - Acceptable tradeoff for quality improvement

4. **Implementation Effort:**
   - Need to update existing agents (Planning, Design)
   - Build orchestrator routing logic
   - Add comprehensive tests for feedback loops
   - Estimated 8-12 hours additional work

### Risks and Mitigation

**Risk 1: Infinite Correction Loops**
- *Mitigation:* Hard iteration limits (3 per phase, 10 total)
- *Mitigation:* Human escalation after max iterations
- *Mitigation:* Telemetry alerts for high correction rates

**Risk 2: Incorrect Phase Attribution**
- *Mitigation:* Specialist review agents trained on phase identification
- *Mitigation:* Default to most recent phase if uncertain
- *Mitigation:* Human review of phase attributions in HITL mode

**Risk 3: Increased Costs**
- *Mitigation:* Monitor correction rates and optimize prompts
- *Mitigation:* Cache common planning/design patterns
- *Mitigation:* Use cheaper models for validation-only tasks

**Risk 4: Cascading Corrections**
- *Scenario:* Fix in planning requires design + code + test regeneration
- *Mitigation:* Clear dependency tracking in orchestrator
- *Mitigation:* Batch corrections when possible
- *Mitigation:* Incremental validation at each step

---

## Implementation Checklist

### Data Models (Immediate - Before Code Agent)
- [ ] Add `affected_phase` to `DesignIssue` model
- [ ] Add `planning_phase_issues` and `design_phase_issues` to `DesignReviewReport`
- [ ] Update Design Review Agent prompts to identify affected phase
- [ ] Add validation for phase field values

### Agent Updates (Before Orchestrator)
- [ ] Add `feedback` parameter to Planning Agent execute method
- [ ] Add `feedback` parameter to Design Agent execute method
- [ ] Update agent prompts to incorporate feedback into regeneration
- [ ] Add tests for feedback-driven regeneration

### Code Agent Design (Current Work)
- [ ] Design `CodeIssue` model with `affected_phase` field
- [ ] Design `CodeReviewReport` with phase-specific issue lists
- [ ] Plan for feedback parameter in Code Agent

### Orchestrator (After Code Review Agent)
- [ ] Implement phase-aware routing logic
- [ ] Add iteration counters and limits
- [ ] Implement human escalation on max iterations
- [ ] Add telemetry for correction cycles
- [ ] Create comprehensive test suite for feedback loops

### Testing Strategy
- [ ] Unit tests: Each agent handles feedback correctly
- [ ] Integration tests: Planning → Design → Review with corrections
- [ ] E2E tests: Full workflow with multi-phase corrections
- [ ] Load tests: Ensure correction loops don't cause performance issues
- [ ] Cost tests: Measure actual cost impact of corrections

---

## References

1. **PRD Section 6.2.4:** Quality Gates and Error Handling
2. **PRD Section 13:** Defect Recording Log (phase injection tracking)
3. **PSP Methodology:** Defect prevention and phase yield principles
4. **Planning Agent ADR:** BaseAgent pattern and telemetry integration
5. **Design Review Agent ADR:** Multi-agent orchestration patterns

---

## Appendix A: Example Correction Flow

### Scenario: Missing Authentication Requirement

**Initial Attempt:**
```
1. Planning Agent: Decomposes "Build user management system"
   → Semantic units: CreateUser, UpdateUser, DeleteUser, ListUsers
   → Missing: Authentication semantic unit

2. Design Agent: Creates design for CRUD operations
   → APIs: POST /users, PUT /users/{id}, DELETE /users/{id}, GET /users
   → Missing: Authentication endpoints, JWT handling

3. Design Review Agent: Reviews design
   → SecurityReviewAgent flags: "No authentication mechanism"
   → Issue severity: Critical
   → Affected phase: Planning (missing semantic unit)
   → Overall assessment: FAIL
```

**Correction Flow:**
```
4. Orchestrator analyzes DesignReviewReport
   → Finds 1 Critical issue in planning_phase_issues
   → Routes back to Planning Agent with feedback

5. Planning Agent (with feedback): Regenerates plan
   → Adds Authentication semantic unit
   → Updates complexity estimates
   → New plan includes auth as dependency

6. Design Agent: Regenerates design with new plan
   → Adds authentication endpoints
   → Adds JWT token handling
   → Updates all APIs to require auth

7. Design Review Agent: Reviews updated design
   → All security checks pass
   → Overall assessment: PASS
   → Continues to Code Agent
```

**Telemetry Captured:**
- Defect: Missing Authentication Requirement
- Phase Injected: Planning
- Phase Detected: Design Review
- Correction Attempts: 1 (planning) + 1 (design) = 2 total
- Cost Impact: +$0.05 (replanning + redesign)
- Latency Impact: +25 seconds

---

## Appendix B: Phase Attribution Guidelines for Review Agents

Review agents should use the following guidelines when setting `affected_phase`:

### Planning Phase Issues:
- Missing semantic units or requirements
- Incorrect task decomposition
- Missing dependencies between units
- Fundamentally wrong understanding of requirements

### Design Phase Issues:
- Incorrect API design (wrong HTTP methods, missing error codes)
- Poor data model choices (wrong column types, missing indexes)
- Architectural problems (tight coupling, circular dependencies)
- Security vulnerabilities in design (missing encryption, weak auth)

### Both Phases:
- Issues that require changes to both plan and design
- Example: Missing feature affects both decomposition and architecture

### When Uncertain:
- Default to most recent phase (Design for Design Review, Code for Code Review)
- Include explanation in issue description
- Human review can reclassify in HITL mode

---

**Decision Status:** Proposed (Pending Implementation)
**Next Review:** After Code Agent implementation
**Document Owner:** Development Team
