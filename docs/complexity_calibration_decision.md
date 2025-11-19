# Complexity Calibration Decision

**Date:** November 13, 2025
**Status:** DEFERRED - Pending Empirical Validation
**Decision Makers:** Product Team
**Context:** Bootstrap Data Collection Phase (12 tasks, 100 semantic units)

---

## Executive Summary

After successfully running the Planning Agent on 12 diverse real-world software tasks, we discovered that semantic complexity scores are **5-10x higher** than the initially proposed complexity bands in the PRD. Rather than immediately recalibrating the bands or adjusting the decomposition granularity, **we have decided to defer this decision** until we can validate complexity scores against actual development execution metrics from a complete agent suite.

**Decision:** Accept current complexity scoring as baseline and collect empirical data from real builds before calibrating.

---

## Context

### Initial Complexity Bands (PRD Section 13.1)

From the original PRD, expected complexity ranges were:

| Band | Range | Description |
|------|-------|-------------|
| Trivial | < 10 | Simple one-file changes |
| Simple | 11-30 | Basic features (2-3 files) |
| Moderate | 31-60 | Multi-component features |
| Complex | 61-100 | Cross-cutting features |

### Bootstrap Data Collection Results

**Date:** November 13, 2025
**Tasks:** 12 real-world software tasks
**Success Rate:** 100% (12/12)
**Total Semantic Units:** 100
**Execution Time:** 2 minutes 10 seconds
**Total Cost:** $0.24 USD

### Actual Complexity Scores

| Band | Expected Range | Actual Range | Actual Average | Deviation |
|------|---------------|--------------|----------------|-----------|
| Trivial | < 10 | 8-100 | 54 | 5.4x higher |
| Simple | 11-30 | 183-191 | 187 | 6.2x higher |
| Moderate | 31-60 | 277-501 | 380 | 6.3x higher |
| Complex | 61-100 | 386-790 | 572 | 5.7x higher |

**Key Observations:**
- Only 1 of 12 tasks scored within expected range (BOOTSTRAP-002: 8)
- Scores are consistently 5-10x higher across all complexity bands
- Decomposition granularity is very consistent (7-8 semantic units per task)
- Individual unit complexity ranges from 4 to 154

---

## Analysis

### Why Are Scores Higher Than Expected?

Three possible explanations:

#### 1. C1 Formula Accurately Reflects Real-World Complexity

The C1 formula may be correctly capturing the true complexity of comprehensive, production-ready implementations:

```
C1 = (API + Data + Branches + 2×Entities) × Novelty
```

- Formula weights `Entities` at 2× (file modifications dominate)
- LLM is decomposing into proper production-quality semantic units
- "Add config field" (BOOTSTRAP-001) isn't just a UI toggle - it's:
  - Database migration
  - Backend API (save/load endpoints)
  - Frontend UI component
  - Integration layer
  - Total: 5 units, complexity 100

This suggests our *bands were too conservative*, not that the formula is wrong.

#### 2. Complexity Bands Need Recalibration

Original bands may have been based on incomplete understanding of what comprehensive task decomposition entails:

- **Underestimated scope:** "Simple" tasks assumed 2-3 files, but production features touch DB + API + UI + integration
- **Missing cross-cutting concerns:** Security, error handling, validation, logging add complexity
- **Production-ready vs. prototype:** Bootstrap tasks are production-quality, not POC-level

#### 3. LLM Decomposition Too Granular

The LLM may be breaking tasks into smaller units than intended:

- Average 7-8 units per task (very consistent)
- Individual units quite detailed (separate frontend/backend work)
- Could instruct LLM to create fewer, larger units (3-5 instead of 7-8)

However, dependency graphs show units *are* semantically coherent and properly sequenced.

---

## Options Considered

### Option 1: Recalibrate Complexity Bands (5-10x Higher)

**Approach:** Adjust bands to match observed data.

**Proposed New Bands:**
| Band | Old Range | New Range | Multiplier |
|------|-----------|-----------|------------|
| Trivial | < 10 | < 50 | 5x |
| Simple | 11-30 | 50-200 | ~6x |
| Moderate | 31-60 | 201-400 | ~6.5x |
| Complex | 401-700 | 401-700 | ~6.5x |
| Very Complex | N/A | 700+ | New band |

**Pros:**
- Aligns bands with empirical data
- Preserves current decomposition granularity
- No changes to prompts or formulas needed
- Bootstrap data becomes immediately usable

**Cons:**
- **No validation against actual development time** - we don't know if complexity 277 = 2 hours or 20 hours
- May need re-recalibration after real builds
- Psychological impact: "Complex" now means 401-700 instead of 61-100

### Option 2: Reduce Decomposition Granularity

**Approach:** Modify prompt to create fewer, larger semantic units (3-5 instead of 7-8).

**Implementation:**
- Update decomposition prompt to combine related work
- Example: Merge "Create DB migration" + "Create API endpoint" into single unit
- Target: ~5x reduction in total complexity (fewer units = lower sum)

**Pros:**
- Brings scores closer to original bands
- Larger units may better match development milestones
- More intuitive: "Simple task = 3 units" vs "Simple task = 7 units"

**Cons:**
- **No validation** - we don't know if 3 large units or 7 small units better predict effort
- Loses granularity in dependency tracking
- May reduce PROBE-AI's ability to learn fine-grained patterns
- Requires prompt rewrite and re-collection of bootstrap data

### Option 3: Accept Current Scoring

**Approach:** Use current complexity scores as-is without recalibration.

**Rationale:**
- Complexity scores may accurately reflect comprehensive task breakdown
- "High" numbers aren't inherently wrong - they're just numbers
- What matters is **correlation with actual effort**, not absolute values
- Bands are arbitrary labels; the scores themselves drive PROBE-AI

**Pros:**
- No changes needed - continue collecting data
- Preserves maximum information (fine-grained decomposition)
- Defers decision until we have empirical validation
- Recognizes we lack ground truth

**Cons:**
- Complexity bands in PRD become misleading
- May confuse stakeholders ("Why is a simple task 187?")
- Harder to communicate relative complexity without recalibration

### Option 4: Defer Decision Until Empirical Validation (SELECTED)

**Approach:** Accept current scoring as baseline, collect execution metrics from real builds, then calibrate based on data.

**Implementation:**
1. Continue using current C1 formula and decomposition
2. Build complete agent suite (7 agents)
3. Execute bootstrap tasks end-to-end with full telemetry
4. Collect metrics:
   - **Actual development time** per task
   - **Actual defect count** per complexity band
   - **Agent execution costs** (LLM API calls)
   - **Phase distribution** (planning vs. coding vs. testing time)
5. Analyze correlation:
   - Does complexity 277 = X hours?
   - Do higher scores predict more defects?
   - Is granularity (7-8 units) optimal for agent execution?
6. Make data-driven decision on bands and granularity

**Pros:**
-  **Evidence-based decision** - will have real ground truth
-  No premature optimization
-  Preserves maximum information for PROBE-AI training
-  Can test multiple hypotheses simultaneously
-  Bootstrap data remains valid (baseline metrics)

**Cons:**
-  Delays final calibration (requires full agent suite)
-  Complexity bands in documentation may be temporarily inaccurate
-  Stakeholders may be confused by "high" numbers

---

## Decision

**We choose Option 4: Defer Decision Until Empirical Validation**

### Rationale

1. **Lack of Ground Truth:** We have no empirical data on how complexity scores correlate with actual development time, defect rates, or agent execution costs. Making calibration decisions now would be based on *intuition*, not *data*.

2. **Bootstrap Data is Valuable Regardless:** The 12 tasks provide a baseline dataset. Whether complexity bands are 1-100 or 1-1000, the *relative* differences and telemetry captured remain useful for PROBE-AI training.

3. **Full Agent Suite Required:** We cannot validate complexity scoring without agents that can actually build these projects. Once we have:
   - Planning Agent  (complete)
   - Design Agent (pending)
   - Code Agent (pending)
   - Test Agent (pending)
   - Review Agent (pending)
   - Debug Agent (pending)
   - Documentation Agent (pending)

   ...we can execute BOOTSTRAP-001 through BOOTSTRAP-012 end-to-end and measure actual effort.

4. **Premature Optimization Risk:** Adjusting bands or granularity now might optimize for the wrong metric. What if "complexity 277" actually *does* predict 2.5 hours of development time accurately, and recalibrating to "complexity 50" loses that signal?

5. **Scientific Method:** We should:
   - Form hypothesis: "C1 formula predicts development effort"
   - Collect data: Execute bootstrap tasks with full agent suite
   - Analyze: Measure correlation between scores and actual metrics
   - Decide: Calibrate based on evidence

### What This Means

**Short Term (Phase 1-2):**
-  Continue using current C1 formula and decomposition
-  Collect more bootstrap tasks if needed (20-30 total recommended)
-  Document that complexity bands are **provisional** pending validation
-  Communicate to stakeholders: "Complexity 277" is a baseline metric, not a normalized score

**Medium Term (Phase 3-4):**
- Build remaining 6 agents
- Execute bootstrap tasks end-to-end
- Collect execution telemetry:
  - Development time per task
  - Defect count per task
  - Phase distribution (time in each PSP phase)
  - Agent API costs
  - Human intervention frequency

**Long Term (Phase 5+):**
- Analyze correlation between complexity scores and execution metrics
- Make data-driven decision on:
  - Complexity band recalibration
  - Semantic unit granularity
  - C1 formula adjustments (if needed)
  - PROBE-AI training approach

---

## Success Criteria for Future Calibration

When we revisit this decision (estimated: Phase 4), we will have collected:

### Required Data Points (per task)

1. **Execution Metrics:**
   - Total development time (end-to-end)
   - Time per PSP phase (planning, design, coding, testing, review)
   - Agent API costs (total USD)
   - Human intervention count

2. **Quality Metrics:**
   - Defect count (total)
   - Defect density (defects per complexity point)
   - Phase injection/removal rates
   - Code coverage achieved
   - Test pass rate

3. **Complexity Correlation:**
   - R² correlation: complexity score vs. development time
   - R² correlation: complexity score vs. defect count
   - R² correlation: complexity score vs. API cost
   - Variance analysis by complexity band

### Decision Criteria

We will recalibrate if:
- **Low correlation (R² < 0.5):** Complexity scores don't predict effort → adjust formula or granularity
- **High correlation (R² > 0.7):** Complexity scores predict effort → keep formula, possibly relabel bands
- **Non-linear relationship:** May need logarithmic or exponential bands

We will reduce granularity if:
- Units are too fine-grained for agent execution (agents combine units anyway)
- Dependency graphs are overly complex (>50% of units have 3+ dependencies)
- PROBE-AI training shows no benefit from fine-grained units

We will increase granularity if:
- Units are too coarse (agents frequently fail on single units)
- Defects cluster within units (units lack cohesion)
- PROBE-AI predictions are inaccurate due to high variance within units

---

## Mitigation Strategies

### Risk: Stakeholder Confusion

**Problem:** "Why does a simple task have complexity 187?"

**Mitigation:**
- Update PRD with "provisional bands" note
- Communicate that scores are *baseline metrics* pending validation
- Focus on *relative* complexity: "Task B is 2.5x more complex than Task A"
- Emphasize correlation with effort, not absolute values

### Risk: PROBE-AI Training Delay

**Problem:** Can't train PROBE-AI until we have execution data.

**Mitigation:**
- Phase 2 PROBE-AI can still use bootstrap data for *initial* model training
- Use synthetic data or proxy metrics (LLM confidence scores, token counts)
- Accept lower accuracy in Phase 2, refine in Phase 3-4

### Risk: Wasted Effort if Recalibration Needed

**Problem:** May need to rewrite prompts, recalculate scores, re-collect data.

**Mitigation:**
- Bootstrap data remains valid (raw telemetry preserved)
- Complexity recalculation is automated (C1 formula in code)
- Prompt adjustments are version-controlled (easy rollback)
- Accept some rework as cost of evidence-based decision

---

## Related Decisions

- **Planning Agent Architecture Decision** (`planning_agent_architecture_decision.md`)
  - Chose direct Anthropic SDK, C1 formula implementation
  - This decision validates that choice by collecting empirical data

- **Data Storage Decision** (`data_storage_decision.md`)
  - SQLite chosen for Phase 1-3
  - Supports storing bootstrap data and execution metrics

- **Bootstrap Data Collection** (`bootstrap_analysis.md`)
  - Comprehensive analysis of 12 tasks
  - Recommends collecting 20-30 more tasks to validate patterns

---

## Next Steps

### Immediate (Phase 1, Week 3)

1.  Document this decision (this file)
2.  Update PRD Section 13.1 to note complexity bands are **provisional**
3.  Consider collecting 10-20 more bootstrap tasks to increase dataset size
4.  Begin implementing next agent (Design or Code Agent)

### Short Term (Phase 2-3)

1. Build remaining 6 agents
2. Create end-to-end execution pipeline
3. Run bootstrap tasks through full agent suite
4. Collect execution telemetry (time, defects, costs)

### Long Term (Phase 4+)

1. Analyze correlation between complexity scores and execution metrics
2. Revisit this decision with empirical data
3. Make data-driven calibration decision
4. Update documentation and PROBE-AI training accordingly

---

## Conclusion

The bootstrap data collection revealed complexity scores 5-10x higher than expected bands. Rather than immediately recalibrating based on intuition, we are **deferring the decision** until we can validate complexity scores against actual development execution metrics from a complete agent suite.

This approach:
-  Preserves maximum information for PROBE-AI training
-  Enables evidence-based decision making
-  Avoids premature optimization
-  Maintains scientific rigor

**Status:** Decision deferred pending empirical validation in Phase 3-4.

**Review Date:** After executing 10+ bootstrap tasks with full agent suite.

**Owners:** Product team, PROBE-AI research team.

---

**Document Version:** 1.0
**Last Updated:** November 13, 2025
**Next Review:** Phase 4 (post-agent suite completion)
