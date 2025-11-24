# ADR: Agent Output Format Strategy - JSON vs Markdown

**Status:** Proposed
**Date:** 2025-11-21
**Deciders:** ASP Development Team
**Related Issues:** AGENT-FORMAT-001 (System-wide output format standardization)
**Related Docs:**
- `docs/code_generation_artifact_format_decision.md` (Code Agent multi-stage implementation)
- `Summary/summary20251120.5.md` (Code Agent JSON parsing diagnosis)
- `Summary/summary20251120.6.md` (Multi-stage implementation success)

---

## Context and Problem Statement

The ASP platform has **21 agents** across 7 categories, all currently generating structured JSON outputs validated by Pydantic models, with separate Markdown rendering for human readability. This creates a dual-format system requiring maintenance of both JSON schemas and Markdown renderers.

**Recent Success Story:** The Code Agent recently solved critical JSON parsing issues (50% failure rate) by switching to multi-stage generation: small JSON manifest (4.8KB) + raw file contents (no JSON wrapping). This improved reliability to 100% and demonstrated that moving away from large JSON outputs can significantly improve system robustness.

**Central Question:** Should we adopt a system-wide standard for agent outputs? If so, should it be JSON, Markdown, or a hybrid approach tailored to each agent's characteristics?

---

## Agent Inventory and Current State

### Core Pipeline Agents (7 agents)

| Agent | Output Model | JSON Size | MD Size | Success Rate | Complexity |
|-------|--------------|-----------|---------|--------------|------------|
| Planning Agent | ProjectPlan | 1.7 KB | 1.4 KB | ~100% | Low (structured decomposition) |
| Design Agent | DesignSpecification | 12 KB | 5.8 KB | ~98% | Medium (APIs, components, examples) |
| Design Review Agent | DesignReviewReport | 10.6 KB | ? | ~100% | Medium (feedback, recommendations) |
| Code Agent | FileManifest + Files | 174 KB | 4.8 KB | 100%* | High (embedded source code) |
| Code Review Orchestrator | CodeReviewReport | ? | ? | ~100% | Medium (aggregated reviews) |
| Test Agent | TestReport | 14 KB | 12 KB | ~100% | Medium (test results, coverage) |
| Postmortem Agent | PostmortemReport + PIP | ? | ? | ~100% | Medium (metrics, analysis) |

*Code Agent now uses multi-stage (manifest JSON + raw files), not monolithic JSON

### Specialist Review Agents (12 agents)

**Design Review Specialists (6):**
- Architecture Review Agent
- API Design Review Agent
- Security Review Agent
- Performance Review Agent
- Maintainability Review Agent
- Data Integrity Review Agent

**Code Review Specialists (6):**
- Code Quality Review Agent
- Code Security Review Agent
- Best Practices Review Agent
- Code Performance Review Agent
- Test Coverage Review Agent
- Documentation Review Agent

All specialist agents output structured review reports with issues, severity levels, and recommendations.

### Orchestrators (2 agents)

- Design Review Orchestrator → Coordinates 6 design specialists
- Code Review Orchestrator → Coordinates 6 code specialists

---

## Key Observations

### 1. Size Matters - JSON vs Markdown Compression

From HW-001 artifacts:

| Agent | JSON | Markdown | Ratio | Notes |
|-------|------|----------|-------|-------|
| Planning | 1.7 KB | 1.4 KB | 1.2x | Similar size, simple data |
| Design | 12 KB | 5.8 KB | 2.1x | JSON has more structure overhead |
| Code Manifest | 174 KB | 4.8 KB | 36x! | JSON embeds all file contents |
| Test | 14 KB | 12 KB | 1.2x | Similar size, test results |

**Insight:** Agents with deeply nested content (Design) or embedded artifacts (Code) suffer from significant JSON bloat.

### 2. Success Rates - Current JSON Approach

| Agent Category | Success Rate | Notes |
|----------------|--------------|-------|
| Planning | ~100% | Small, simple JSON |
| Design | ~98% | Haiku 4.5 had `request_params` issues (2 prompt fixes) |
| Design Review | ~100% | Medium JSON, structured feedback |
| Code (legacy) | ~50% | Large JSON with embedded code → FAILED |
| Code (multi-stage) | ~100% | Small JSON manifest + raw files → SUCCESS |
| Test | ~100% | Medium JSON, test results |
| Postmortem | ~100% | After schema fixes |

**Insight:** Small-to-medium JSON (<15KB) works well, but large JSON (>50KB) with embedded content fails consistently.

### 3. LLM Model Compatibility

**Sonnet 4 (high quality, expensive):**
- JSON: ~100% success across all agents
- Complex nested structures: No issues
- Cost: $3.00/M input, $15.00/M output

**Haiku 4.5 (fast, cheap):**
- JSON: ~98% success (Design Agent needed fixes)
- Complex nested structures: Requires very explicit prompts
- Cost: $0.25/M input, $1.25/M output (12x cheaper)
- **Trade-off:** 12x cost savings vs 2% reliability drop + prompt engineering effort

**Insight:** JSON format creates LLM compatibility challenges when optimizing for cost. Markdown is more "natural" for LLMs to generate.

### 4. Maintenance Burden

**Current System:**
- Pydantic models (7 modules: planning, design, design_review, code, code_review, test, postmortem)
- JSON generation prompts (must specify exact schema structure)
- Markdown renderer functions (separate implementation per agent)
- Dual artifact storage (`*.json` + `*.md`)

**Maintenance Tasks:**
- Update Pydantic model → Update prompt template → Update MD renderer → Test all 3
- ~3x the work for any schema change

**Insight:** Dual format increases maintenance overhead linearly with number of schema changes.

---

## Decision Drivers

### Critical Requirements

1. **Reliability:** >95% success rate across all agents and LLM models
2. **Maintainability:** Schema changes should be easy and safe
3. **Validation:** Ensure output correctness and completeness
4. **Debuggability:** Clear error messages when things fail
5. **Integration:** Support downstream consumers (orchestrators, telemetry, UI)

### Important Factors

6. **LLM Performance:** Format should be natural for LLMs to generate reliably
7. **Cost Efficiency:** Enable use of cheaper models (Haiku vs Sonnet)
8. **Human Readability:** Outputs should be immediately inspectable
9. **Token Efficiency:** Minimize syntax overhead
10. **Consistency:** Architectural alignment across agents

### Nice-to-Have

11. **Single Format:** Avoid dual JSON + Markdown maintenance
12. **Migration Path:** Incremental adoption without breaking changes
13. **Backward Compatibility:** Support existing integrations during transition

---

## Options Considered

### Option 1: Universal JSON (Status Quo)

**Approach:** All agents generate JSON as primary output, Markdown rendered separately.

**Architecture:**
```python
# Every agent follows this pattern
class SomeAgent(BaseAgent):
    def generate(self, input_data) -> SomeModel:
        prompt = self.load_prompt("some_agent_v1")
        response = self.call_llm(prompt)
        json_content = extract_json_from_markdown(response)
        model = SomeModel.model_validate(json_content)  # Pydantic

        # Save both formats
        self.save_artifact(model.model_dump_json(), "output.json")
        self.save_artifact(render_markdown(model), "output.md")
        return model
```

**Pros:**
- ✅ No changes required (0 hours implementation)
- ✅ Pydantic validation ensures structural correctness
- ✅ Type-safe for Python consumers
- ✅ Works well for small-medium outputs (<15KB)
- ✅ Industry-standard machine-readable format
- ✅ Current success rate 98-100% for most agents

**Cons:**
- ❌ Failed catastrophically for Code Agent (50% → required multi-stage fix)
- ❌ Design Agent compatibility issues with Haiku 4.5 (prompt engineering overhead)
- ❌ Dual format maintenance burden (3x work for schema changes)
- ❌ JSON bloat (Design: 2.1x, Code: 36x larger than markdown)
- ❌ Less natural for LLMs (strict formatting requirements)
- ❌ Escaping complexity for nested content
- ❌ Inconsistent with Code Agent's proven approach

**Risk Assessment:** Medium-High
- Risk: More agents will hit JSON parsing issues as outputs grow
- Risk: Haiku optimization blocked by JSON brittleness
- Risk: Continued maintenance burden scaling with agent count

---

### Option 2: Universal Markdown

**Approach:** All agents generate Markdown as primary output, parse to extract structured data.

**Architecture:**
```python
class SomeAgent(BaseAgent):
    def generate(self, input_data) -> SomeModel:
        prompt = self.load_prompt("some_agent_v2_markdown")
        markdown = self.call_llm(prompt)  # Returns markdown directly

        # Parse markdown → structured data
        parsed_data = parse_markdown(markdown)
        model = SomeModel.model_validate(parsed_data)  # Still validate!

        # Save both formats
        self.save_artifact(markdown, "output.md")  # Primary
        self.save_artifact(model.model_dump_json(), "output.json")  # For tools
        return model
```

**Example Markdown:**
```markdown
# Project Plan: HW-001

**Task ID:** HW-001
**Total Complexity:** 83

## Semantic Units

### SU-001: Setup FastAPI project

- **Complexity:** 11
- **Dependencies:** None
```

**Pros:**
- ✅ LLM-native format (more reliable generation)
- ✅ Human-readable by default (no rendering needed)
- ✅ No JSON escaping issues (proven by Code Agent)
- ✅ Token efficient (less syntax overhead)
- ✅ Enables cost optimization (Haiku more reliable with markdown)
- ✅ Consistent architecture across all agents
- ✅ Single primary format (markdown) + optional JSON

**Cons:**
- ❌ Large implementation effort (80-120 hours for 7 core agents)
- ❌ Parsing complexity (regex/library for each model type)
- ❌ Validation after parsing (not during generation)
- ❌ Parser maintenance burden (handle format variations)
- ❌ Risk: Parsing failures if markdown format varies
- ❌ Loss of Pydantic's generation-time enforcement
- ❌ Need comprehensive testing for parsers

**Implementation Estimate:**
- Planning Agent: 10-15 hours (simplest, template for others)
- Design Agent: 15-20 hours (complex nested structures)
- Design Review Agent: 12-16 hours (similar to Design)
- Code Agent: 0 hours (already uses multi-stage)
- Test Agent: 12-16 hours (test results, coverage)
- Postmortem Agent: 15-20 hours (metrics, calculations)
- Code Review Orchestrator: 10-12 hours (aggregate reviews)
- **Total: 74-99 hours**

**Risk Assessment:** Medium
- Risk: Parsing failures reduce reliability gains
- Risk: Implementation bugs in parsers
- Mitigation: Comprehensive test suite, fallback mechanisms

---

### Option 3: Tiered Strategy (Size-Based)

**Approach:** Choose format based on output characteristics (size, complexity, nesting depth).

**Decision Criteria:**
- **JSON:** Simple structure + Small size (<5KB) + No nested content
- **Markdown:** Complex structure OR Large size (>10KB) OR Embedded content
- **Multi-Stage:** Very large (>50KB) OR File generation

**Agent Classification:**

| Agent | Format | Rationale |
|-------|--------|-----------|
| Planning Agent | JSON | Simple, 1.7KB, structured decomposition |
| Design Agent | **Markdown** | Complex, 12KB, nested APIs/components |
| Design Review Agent | **Markdown** | Medium complex, 10KB, feedback |
| Code Agent | **Multi-Stage** | Very large, 174KB, embedded files ✅ Done |
| Code Review | **Markdown** | Aggregated reviews, variable size |
| Test Agent | JSON | 14KB, but simple test results |
| Postmortem Agent | **Markdown** | Complex metrics, analysis, PIPs |
| Design Review Specialists | JSON | Small focused reviews |
| Code Review Specialists | JSON | Small focused reviews |

**Pros:**
- ✅ Pragmatic trade-off (optimize where needed)
- ✅ Planning Agent stays simple (no changes)
- ✅ Target agents with known/potential issues
- ✅ Reduced implementation effort (4 agents vs 7)
- ✅ Incremental migration path

**Cons:**
- ❌ Architectural inconsistency (confusing for developers)
- ❌ Still maintain both JSON and Markdown systems
- ❌ Arbitrary thresholds may need tuning
- ❌ Planning Agent may outgrow JSON later
- ❌ Mixed patterns increase cognitive load

**Implementation Estimate:**
- Design Agent: 15-20 hours
- Design Review Agent: 12-16 hours
- Code Review Orchestrator: 10-12 hours
- Postmortem Agent: 15-20 hours
- **Total: 52-68 hours**

**Risk Assessment:** Medium
- Risk: Inconsistency creates confusion
- Risk: Agents may need reclassification over time
- Risk: Harder to establish clear patterns

---

### Option 4: Markdown with Structured Frontmatter (Hybrid)

**Approach:** YAML frontmatter for critical metadata + Markdown for content.

**Architecture:**
```python
class SomeAgent(BaseAgent):
    def generate(self, input_data) -> SomeModel:
        prompt = self.load_prompt("some_agent_v3_frontmatter")
        response = self.call_llm(prompt)

        # Parse YAML frontmatter + markdown body
        frontmatter, body = parse_frontmatter(response)
        metadata = MetadataModel.model_validate(frontmatter)  # Validate YAML

        # Parse markdown for detailed content
        content = parse_markdown_body(body)

        # Assemble full model
        model = SomeModel(**metadata.model_dump(), **content)
        return model
```

**Example Output:**
```markdown
---
task_id: HW-001
project_id: HELLO-WORLD
total_complexity: 83
probe_ai_enabled: false
agent_version: 1.0.0
---

# Project Plan: HW-001

## Semantic Units

### SU-001: Setup FastAPI project

**Complexity:** 11
**Dependencies:** None

[Detailed description...]
```

**Pros:**
- ✅ Best of both worlds (structured + flexible)
- ✅ YAML frontmatter is industry standard (Jekyll, Hugo, Obsidian)
- ✅ Critical fields strictly validated (Pydantic on frontmatter)
- ✅ Content flexible and human-readable
- ✅ Easier parsing (python-frontmatter library)
- ✅ Graceful degradation (can skip frontmatter if needed)
- ✅ Clear separation of metadata vs content

**Cons:**
- ❌ Implementation effort similar to Option 2 (70-100 hours)
- ❌ Two parsing steps (YAML + Markdown)
- ❌ LLMs need to learn frontmatter format
- ❌ YAML parsing issues (indentation, special chars)
- ❌ Less common in LLM agent patterns

**Implementation Estimate:**
- Similar to Option 2: 74-99 hours

**Risk Assessment:** Medium
- Risk: YAML formatting errors (indentation sensitive)
- Risk: LLM may forget frontmatter delimiters
- Mitigation: Clear examples, retry logic

---

### Option 5: Agent-Specific Optimization (Recommended)

**Approach:** Make format decisions per agent based on proven pain points and characteristics, not arbitrary size thresholds.

**Strategy:**
1. **Keep JSON where it works well**
2. **Switch to Markdown where JSON has failed or caused issues**
3. **Maintain architectural consistency within agent categories**

**Agent-by-Agent Decisions:**

| Agent | Decision | Rationale |
|-------|----------|-----------|
| **Planning Agent** | Keep JSON ✅ | 1.7KB, 100% success, simple structure, no issues |
| **Design Agent** | **Switch to Markdown** ⚠️ | Haiku compatibility issues, 12KB, nested structures, 2 prompt fixes needed |
| **Design Review Agent** | Keep JSON ✅ | 10KB, 100% success, structured feedback works well |
| **Code Agent** | Multi-Stage ✅ | Already done, 50% → 100% success |
| **Code Review Orchestrator** | Keep JSON ✅ | Aggregates structured reviews, no issues observed |
| **Test Agent** | Keep JSON ✅ | 14KB, 100% success, test results are naturally structured |
| **Postmortem Agent** | Keep JSON ✅ | 100% success after schema fixes, metrics are structured |
| **Design Review Specialists** | Keep JSON ✅ | Small, focused reviews, work well |
| **Code Review Specialists** | Keep JSON ✅ | Small, focused reviews, work well |

**Implementation Plan:**

**Phase 1: Design Agent Only (2-3 weeks)**
- Switch Design Agent to Markdown (highest pain point)
- Implement parser and comprehensive tests
- Measure success rate improvement with Haiku
- Validate approach before expanding

**Phase 2: Monitor and Evaluate (1 month)**
- Track metrics across all agents
- Identify any new issues with other agents
- Decide if further migrations needed based on data

**Phase 3: Expand if Needed (conditional)**
- Only migrate additional agents if they show issues
- Evidence-based decisions, not premature optimization

**Pros:**
- ✅ Evidence-based (target proven pain points)
- ✅ Minimal scope (1 agent initially)
- ✅ Low risk (can rollback easily)
- ✅ Data-driven expansion (monitor first, migrate later)
- ✅ Preserves what works (7 agents unchanged)
- ✅ Learn from Design Agent before scaling

**Cons:**
- ❌ Architectural inconsistency (Design uses MD, others use JSON)
- ❌ Still maintains both systems
- ❌ Incremental, not comprehensive solution

**Implementation Estimate:**
- Phase 1 (Design Agent): 15-20 hours
- Phase 2 (Monitoring): 0 hours (automated)
- Phase 3 (Conditional): 0-60 hours (only if needed)
- **Total: 15-80 hours** (likely just 15-20)

**Risk Assessment:** Low
- Risk: Minimal, only 1 agent affected initially
- Risk: Can rollback if unsuccessful
- Mitigation: Comprehensive testing, feature flag rollout

---

## Decision Matrix

| Criteria | Option 1 (JSON) | Option 2 (Markdown) | Option 3 (Tiered) | Option 4 (Frontmatter) | Option 5 (Targeted) |
|----------|-----------------|---------------------|-------------------|------------------------|---------------------|
| **Reliability** | ⭐⭐⭐⭐ (98-100%) | ⭐⭐⭐⭐⭐ (99-100%) | ⭐⭐⭐⭐ (mixed) | ⭐⭐⭐⭐⭐ (99-100%) | ⭐⭐⭐⭐⭐ (target issues) |
| **Maintainability** | ⭐⭐⭐ (dual) | ⭐⭐⭐⭐ (single) | ⭐⭐ (inconsistent) | ⭐⭐⭐⭐ (clear) | ⭐⭐⭐ (mixed) |
| **Implementation Cost** | ⭐⭐⭐⭐⭐ (0h) | ⭐⭐ (74-99h) | ⭐⭐⭐ (52-68h) | ⭐⭐ (74-99h) | ⭐⭐⭐⭐ (15-20h) |
| **Risk Level** | ⭐⭐⭐ (known issues) | ⭐⭐⭐ (parser risk) | ⭐⭐⭐ (confusion) | ⭐⭐⭐ (YAML risk) | ⭐⭐⭐⭐⭐ (minimal) |
| **LLM Performance** | ⭐⭐⭐ (strict) | ⭐⭐⭐⭐⭐ (natural) | ⭐⭐⭐⭐ (mixed) | ⭐⭐⭐⭐ (good) | ⭐⭐⭐⭐ (improve pain points) |
| **Consistency** | ⭐⭐⭐⭐ (all JSON) | ⭐⭐⭐⭐⭐ (all MD) | ⭐⭐ (mixed) | ⭐⭐⭐⭐⭐ (all FM) | ⭐⭐⭐ (mostly JSON) |
| **Human Readable** | ⭐⭐⭐ (render) | ⭐⭐⭐⭐⭐ (native) | ⭐⭐⭐⭐ (mixed) | ⭐⭐⭐⭐⭐ (native) | ⭐⭐⭐⭐ (improved) |
| **Evidence-Based** | ⭐⭐⭐⭐ (proven) | ⭐⭐⭐ (hypothesis) | ⭐⭐ (arbitrary) | ⭐⭐⭐ (hypothesis) | ⭐⭐⭐⭐⭐ (data-driven) |

**Scoring:** ⭐ = Poor, ⭐⭐ = Fair, ⭐⭐⭐ = Good, ⭐⭐⭐⭐ = Very Good, ⭐⭐⭐⭐⭐ = Excellent

---

## Recommendation

### **Option 5: Agent-Specific Optimization (Targeted Migration)**

**Recommended Action:** Switch **Design Agent only** to Markdown format, keep all other agents on JSON.

### Rationale

1. **Evidence-Based Decision:**
   - Design Agent is the **only** agent with demonstrated JSON issues (Haiku compatibility, 2 prompt fixes)
   - All other agents have 100% success rates with JSON
   - Don't fix what isn't broken

2. **Minimal Risk:**
   - Scope: 1 agent out of 21
   - Rollback: Easy with feature flag
   - Learning: Validate approach before scaling

3. **Cost-Effective:**
   - Implementation: 15-20 hours
   - vs 74-99 hours for universal migration
   - ROI: Focus effort where pain exists

4. **Preserves Strengths:**
   - Planning Agent (100% success) stays simple
   - Test/Postmortem (100% success) unchanged
   - 18 specialist agents (working well) untouched

5. **Future-Proof:**
   - Monitor all agents for 1+ month
   - Expand to other agents **only if data shows issues**
   - Avoid premature optimization

### When NOT to Migrate Other Agents

**Keep JSON if:**
- Success rate ≥ 99%
- Output size < 15KB
- No LLM compatibility issues observed
- Simple, structured data (not nested content)

**Current agents meeting these criteria:**
- ✅ Planning Agent (1.7KB, 100% success)
- ✅ Design Review Agent (10KB, 100% success)
- ✅ Test Agent (14KB, 100% success)
- ✅ Postmortem Agent (100% success after fixes)
- ✅ All 12 specialist review agents (small, focused)

### When TO Migrate Other Agents

**Switch to Markdown if:**
- Success rate drops below 95% for 3+ consecutive weeks
- LLM compatibility issues emerge (like Design Agent's Haiku issues)
- Output size grows beyond 20KB
- Deeply nested content causes escaping issues

**Monitoring Triggers:**
- Alert if any agent's success rate < 95%
- Review metrics monthly
- Re-evaluate after 100+ production runs

---

## Implementation Plan - Design Agent Migration

### Phase 1: Markdown Format Design (Week 1)

**Tasks:**
1. Design markdown schema for DesignSpecification
2. Create example outputs (Hello World, JWT Auth)
3. Define parser strategy (regex vs library)
4. Get team review and approval

**Deliverables:**
- `docs/design_agent_markdown_format.md` - Format specification
- Example markdown outputs (3+ tasks)

### Phase 2: Implementation (Week 2)

**Tasks:**
1. Create `design_agent_v2_markdown.txt` prompt
2. Implement markdown parser for DesignSpecification
3. Add feature flag (`ASP_DESIGN_AGENT_USE_MARKDOWN=true`)
4. Update Design Agent to support both formats
5. Write comprehensive unit tests (20+ cases)

**Files to Modify:**
- `src/asp/agents/design_agent.py`
- `src/asp/prompts/design_agent_v2_markdown.txt` (new)
- `tests/unit/test_agents/test_design_agent_markdown.py` (new)

**Deliverables:**
- Working markdown generation + parsing
- 100% backward compatible (JSON still works)
- Feature flag for gradual rollout

### Phase 3: Testing and Validation (Week 3)

**Tasks:**
1. Run E2E tests 50+ times with markdown enabled
2. Compare success rates: Sonnet vs Haiku
3. Measure token usage and cost savings
4. Validate output quality (manual review)
5. Test orchestrator integration

**Success Criteria:**
- Markdown success rate ≥ 99% (Haiku)
- No regressions vs JSON baseline
- Token savings ≥ 5%
- Zero orchestrator integration issues

**Deliverables:**
- Test report with metrics
- Go/No-Go decision for production rollout

### Phase 4: Rollout and Monitoring (Week 4+)

**Week 4: Canary (10%)**
- Enable markdown for 10% of tasks
- Monitor error rates, latency, quality
- Quick rollback if issues

**Week 5-6: Gradual Increase (50%, 100%)**
- Increase to 50% if canary succeeds
- Full rollout if 50% succeeds
- Remove feature flag after 2 weeks at 100%

**Week 7: Cleanup**
- Remove JSON generation code path (optional)
- Update documentation
- Archive decision document

---

## Testing Strategy

### Test Cases for Design Agent Markdown

**Happy Path (20 tests):**
- Simple task (1-2 APIs)
- Medium task (5-8 APIs)
- Complex task (10+ APIs)
- All optional fields present
- Minimal optional fields
- Various component types
- Different security schemes

**Edge Cases (15 tests):**
- Missing optional fields
- Very long descriptions
- Special characters (quotes, newlines)
- Unicode and emoji
- Code examples in descriptions
- Nested JSON in examples

**Error Handling (10 tests):**
- Malformed markdown
- Missing required sections
- Invalid frontmatter (if used)
- Parsing failures
- Validation errors

**Integration (5 tests):**
- Design Review Orchestrator consumption
- Artifact persistence
- Telemetry logging
- Error recovery

---

## Monitoring and Success Metrics

### Key Metrics (Track for 1 month)

**Design Agent (Markdown):**
- Parsing success rate (target: ≥99%)
- Generation quality (manual review)
- Token usage vs JSON baseline (target: -5 to -15%)
- Latency vs JSON baseline (target: ≤+50ms)

**All Other Agents (JSON):**
- Success rates (current: 98-100%, maintain)
- Watch for degradation (alert if <95%)
- Track output size growth

**System-Wide:**
- E2E pipeline success rate (maintain ≥95%)
- Total API costs (monitor impact)
- Developer feedback on maintainability

### Decision Points

**After 1 Month:**
- **If Design Agent markdown success ≥99%:** Declare success, keep markdown
- **If 95-99%:** Evaluate trade-offs, may keep or improve
- **If <95%:** Rollback to JSON, analyze root cause

**After 3 Months:**
- Review all agent metrics
- Identify any new candidates for markdown migration
- Make evidence-based decision on expanding scope

---

## Rollback Strategy

### Rollback Triggers

- Design Agent markdown success rate <90% for 1 week
- Critical bugs in parser (data loss, crashes)
- Orchestrator integration failures
- Team consensus to rollback

### Rollback Process

**Immediate (< 1 hour):**
1. Set `ASP_DESIGN_AGENT_USE_MARKDOWN=false`
2. Verify E2E tests pass with JSON
3. Alert team of rollback

**Short-term (1 week):**
1. Analyze root cause
2. Document lessons learned
3. Decide: fix forward or abandon

**Long-term (1 month):**
1. If abandoned: Remove markdown code
2. Update ADR with learnings
3. Close initiative

---

## Alternatives Considered and Rejected

### Why Not Universal Markdown (Option 2)?

**Reason:** Premature optimization
- Current JSON agents have 98-100% success
- No evidence they need fixing
- 74-99 hours implementation cost for hypothetical benefits
- **Principle:** Don't fix what isn't broken

### Why Not Tiered Strategy (Option 3)?

**Reason:** Arbitrary thresholds
- Size-based rules (5KB, 10KB) lack empirical basis
- Planning Agent (1.7KB) works perfectly, no need to "save" it
- Test Agent (14KB) works perfectly despite size
- **Principle:** Use evidence, not arbitrary rules

### Why Not Frontmatter (Option 4)?

**Reason:** Added complexity without proven benefit
- YAML frontmatter adds parsing layer
- LLMs less familiar with frontmatter format
- Similar implementation cost to Option 2
- No evidence current agents need this structure
- **Principle:** Simplicity over elegance

### Why Not Status Quo (Option 1)?

**Reason:** Design Agent has demonstrated issues
- Haiku compatibility required 2 prompt iterations
- 12KB output with nested structures
- JSON bloat (2.1x vs markdown)
- Clear evidence this agent would benefit from markdown
- **Principle:** Fix proven pain points

---

## Conclusion

**Recommended Decision: Option 5 (Agent-Specific Optimization)**

**Implementation:**
1. **Switch Design Agent to Markdown** (15-20 hours, 2-3 weeks)
2. **Keep all other agents on JSON** (0 hours, working well)
3. **Monitor for 3 months** (identify future candidates)
4. **Expand only if evidence emerges** (data-driven)

**Key Principles:**
- ✅ Evidence-based decisions (not premature optimization)
- ✅ Minimal scope (1 agent, low risk)
- ✅ Preserve what works (7 agents unchanged)
- ✅ Monitor and adapt (continuous improvement)

**Success Criteria:**
- Design Agent markdown success rate ≥99%
- No regressions in other agents
- Clear path for future migrations if needed

**Next Steps:**
1. Team review this ADR
2. Approve Phase 1 (format design)
3. Begin Design Agent implementation
4. Establish monitoring dashboard

---

**Status:** Awaiting team review and approval
**Decision Owner:** ASP Development Team
**Review Date:** 2025-11-21
**Next Review:** 2025-12-21 (after 1 month of monitoring)

**Related Decisions:**
- Code Agent multi-stage implementation (completed)
- Design Agent Haiku compatibility fixes (completed)
- Next: Design Agent markdown migration (proposed)
