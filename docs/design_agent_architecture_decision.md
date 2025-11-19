# Architecture Decision Record: Design Agent Implementation

**Date:** 2025-11-13
**Status:** Accepted
**Deciders:** Development Team
**Related:** Planning Agent ADR (`planning_agent_architecture_decision.md`)

---

## Context and Problem Statement

Following the successful implementation of the Planning Agent, we need to implement the **Design Agent** (FR-2 from PRD), which is the second agent in the 7-agent workflow. The Design Agent must transform high-level requirements and project plans into detailed, unambiguous technical designs that can be directly implemented by the Coding Agent.

**Core Requirements (from PRD FR-2):**
- **Input:** Requirements + Project Plan (semantic units with complexity scores from Planning Agent)
- **Output:** Low-Level Design Specification JSON containing:
  - API contracts (endpoints, methods, request/response schemas)
  - Data schemas (database tables, columns, relationships, indexes)
  - Component logic (classes, functions, responsibilities, interfaces)
  - Design review checklist (validation criteria for Design Review Agent)
- **Constraint:** Output must be detailed enough for a separate Coding Agent to implement without ambiguity
- **Standards:** Must use provided design templates and architectural standards

**Key Challenges:**
1. How to structure the design output to be both comprehensive and parseable?
2. How to ensure consistency with Planning Agent output (semantic units)?
3. How to guide the LLM to produce high-quality architectural designs?
4. How to integrate with existing telemetry infrastructure?
5. How to validate design completeness programmatically?

---

## Decision Drivers

1. **Consistency:** Reuse the successful BaseAgent pattern from Planning Agent
2. **Quality:** Designs must be implementation-ready with no ambiguity
3. **Observability:** Full telemetry integration (latency, tokens, costs)
4. **Testability:** Must be unit and E2E testable
5. **Maintainability:** Clear separation of concerns, well-documented code
6. **Cost-Effectiveness:** Optimize LLM usage while maintaining quality
7. **Interoperability:** Seamless integration with Planning Agent output

---

## Considered Options

### Option 1: Direct Anthropic SDK (BaseAgent Pattern)  RECOMMENDED

**Architecture:**
- Inherit from existing `BaseAgent` class
- Use `LLMClient` wrapper for Anthropic API calls
- Pydantic models for input/output validation
- Single-prompt design generation with structured JSON output
- Automatic telemetry via `@track_agent_cost` decorator

**Pros:**
-  Proven pattern from Planning Agent (102/102 tests passing)
-  Minimal additional infrastructure needed
-  Full control over prompt engineering
-  Built-in telemetry and error handling
-  Fast implementation (reuse 80% of Planning Agent patterns)
-  Predictable costs (~$0.02-0.04 per design)

**Cons:**
-  Design prompt will be more complex than planning prompt
-  Need to design comprehensive Pydantic models for design output
-  Manual prompt engineering for design templates

**Cost Estimate:**
- Input: ~2,000-3,000 tokens (requirements + project plan + design templates)
- Output: ~1,500-2,500 tokens (detailed design JSON)
- Cost per task: ~$0.025-0.040 with Claude Sonnet 4
- Monthly cost (100 tasks): ~$2.50-4.00

### Option 2: LangGraph Multi-Step Design Process

**Architecture:**
- Break design into multiple steps: API design → Data modeling → Component design
- Use LangGraph state machine to orchestrate
- Each step validates and refines previous steps

**Pros:**
-  More structured, stepwise approach
-  Potential for higher quality through iteration
-  Better debugging (see intermediate states)

**Cons:**
-  3-4x more LLM calls = 3-4x cost
-  Added complexity (LangGraph framework)
-  Longer latency (sequential steps)
-  Harder to test (stateful orchestration)
-  Over-engineered for current needs

**Cost Estimate:**
- 3-4 LLM calls per design
- Cost per task: ~$0.08-0.15
- Monthly cost (100 tasks): ~$8-15

### Option 3: Code Generation as Design

**Architecture:**
- Skip separate design phase
- Have Planning Agent output directly fed to Coding Agent
- Generate code as the "design"

**Pros:**
-  Simpler workflow (fewer agents)
-  Lower cost (one less LLM call)

**Cons:**
-  Violates PSP process (no formal design review)
-  Higher defect rates (compounding errors)
-  Cannot implement Design Review Agent (FR-3)
-  Incompatible with PRD requirements
-  Loses architectural thinking step

---

## Decision Outcome

**Chosen Option:** **Option 1 - Direct Anthropic SDK (BaseAgent Pattern)**

### Rationale

1. **Proven Pattern:** Planning Agent implementation is working perfectly (102/102 tests, 100% E2E success)
2. **PRD Compliance:** Meets all FR-2 requirements
3. **Cost-Effective:** ~$0.03/design vs $0.12 for multi-step
4. **Fast Implementation:** Can reuse existing infrastructure
5. **Quality:** Single well-crafted prompt can produce complete designs (validated by Planning Agent success)

### Implementation Strategy

#### Phase 1: Core Implementation (Week 1)
1. **Data Models** (`src/asp/models/design.py`):
   ```python
   class DesignInput(BaseModel):
       """Input to Design Agent"""
       task_id: str
       requirements: str
       project_plan: ProjectPlan  # From Planning Agent
       context_files: Optional[list[str]] = []

   class APIContract(BaseModel):
       """API endpoint specification"""
       endpoint: str
       method: str  # GET, POST, PUT, DELETE
       description: str
       request_schema: dict
       response_schema: dict
       error_responses: list[dict]

   class DataSchema(BaseModel):
       """Database table specification"""
       table_name: str
       description: str
       columns: list[dict]  # {name, type, constraints}
       indexes: list[str]
       relationships: list[dict]  # Foreign keys, etc.

   class ComponentLogic(BaseModel):
       """Component/module specification"""
       component_name: str
       semantic_unit_id: str  # Links to Planning Agent output
       responsibility: str
       interfaces: list[dict]  # Public methods/functions
       dependencies: list[str]  # Other components it depends on
       implementation_notes: str

   class DesignReviewChecklistItem(BaseModel):
       """Individual checklist item"""
       category: str  # Architecture, Security, Performance, etc.
       description: str
       validation_criteria: str

   class DesignSpecification(BaseModel):
       """Complete design output"""
       task_id: str
       api_contracts: list[APIContract]
       data_schemas: list[DataSchema]
       component_logic: list[ComponentLogic]
       design_review_checklist: list[DesignReviewChecklistItem]
       architecture_overview: str
       technology_stack: dict
       assumptions: list[str]
   ```

2. **Design Agent Class** (`src/asp/agents/design_agent.py`):
   ```python
   class DesignAgent(BaseAgent):
       """Design Agent - Creates low-level technical designs"""

       @track_agent_cost(task_id_param="input_data.task_id")
       def execute(self, input_data: DesignInput) -> DesignSpecification:
           """Generate detailed technical design"""
           # Load design prompt template
           # Format with requirements + project plan
           # Call LLM
           # Validate output against DesignSpecification schema
           # Return structured design
   ```

3. **Design Prompt** (`src/asp/prompts/design_agent_v1_specification.txt`):
   - Role: "Software Design Agent" specializing in technical architecture
   - Input format: Requirements + ProjectPlan JSON
   - Design templates: API design patterns, data modeling best practices
   - Output format: Strict JSON matching DesignSpecification schema
   - Examples: 2-3 complete design examples (REST API, data pipeline, authentication system)

#### Phase 2: Testing & Validation (Week 1)
1. **Unit Tests** (`tests/unit/test_agents/test_design_agent.py`):
   - Input validation
   - Prompt formatting
   - Output parsing and validation
   - Error handling
   - Integration with Planning Agent output

2. **E2E Tests** (`tests/e2e/test_design_agent_e2e.py`):
   - Run Design Agent with real Planning Agent output
   - Validate design completeness
   - Verify API contracts are implementable
   - Check data schemas are valid SQL
   - Confirm telemetry capture

#### Phase 3: Integration (Week 2)
1. **Planning→Design Pipeline:**
   - Example script showing Planning Agent → Design Agent flow
   - Validate semantic unit IDs match between planning and design
   - Demonstrate complete requirements-to-design workflow

2. **Documentation:**
   - Update README with Design Agent usage
   - Document design output format
   - Provide design quality guidelines

---

## Design Decisions

### 1. Single-Prompt vs. Multi-Prompt

**Decision:** Single comprehensive prompt

**Reasoning:**
- Planning Agent showed that Claude Sonnet 4 can handle complex, multi-part outputs in a single call
- Lower cost and latency
- Simpler state management
- If quality issues arise, can refactor to multi-step in Phase 2

### 2. Design Template Strategy

**Decision:** Embed design patterns and templates directly in the prompt

**Reasoning:**
- No need for external template files initially
- Prompt can include architectural best practices inline
- Examples in prompt serve as "templates by example"
- Can refactor to external templates if prompt becomes too large

### 3. Semantic Unit Mapping

**Decision:** Each `ComponentLogic` must reference a `semantic_unit_id` from Planning Agent

**Reasoning:**
- Ensures traceability from planning → design → code
- Enables complexity validation (design aligns with estimated complexity)
- Supports telemetry aggregation by semantic unit

### 4. Validation Strategy

**Decision:** Pydantic schema validation + programmatic checks

**Validation Checks:**
1. **Schema Validation:** Pydantic ensures all required fields present
2. **Semantic Unit Coverage:** Every semantic unit from Planning Agent has corresponding component(s)
3. **Dependency Consistency:** Component dependencies form valid DAG (no circular deps)
4. **Completeness:** API contracts have matching data schemas, components reference valid APIs

### 5. Technology Stack Specification

**Decision:** Design Agent should specify technology stack choices

**Reasoning:**
- Coding Agent needs to know language, frameworks, libraries
- Makes implicit decisions explicit
- Enables validation (no conflicting tech choices)
- Documents architectural decisions

---

## Risk Assessment

### Risk 1: Design Quality Variance
**Impact:** High
**Probability:** Medium
**Mitigation:**
- Include 3+ high-quality example designs in prompt
- Use strict JSON schema validation
- Implement Design Review Agent (FR-3) to catch quality issues
- Collect telemetry on Design Review defect rates

### Risk 2: Design Ambiguity
**Impact:** High (blocks Coding Agent)
**Probability:** Medium
**Mitigation:**
- Prompt emphasizes "detailed enough for separate agent to implement"
- Validation checks for specific implementation notes
- E2E tests attempt to "implement" design (human validation)
- Feedback loop: track ambiguity-related code review defects

### Risk 3: Planning-Design Mismatch
**Impact:** Medium
**Probability:** Low
**Mitigation:**
- Programmatic validation: semantic_unit_id coverage
- Unit tests verify all planning units have designs
- E2E tests use real Planning Agent output as input

### Risk 4: Context Window Limits
**Impact:** Medium
**Probability:** Low (for Phase 1 tasks)
**Mitigation:**
- Start with small-to-medium tasks (< 10 semantic units)
- Monitor token usage in telemetry
- If needed, implement chunking strategy (design 5 units at a time)

### Risk 5: Cost Overruns
**Impact:** Low
**Probability:** Low
**Mitigation:**
- Estimated $0.03/design is very manageable
- Telemetry tracks actual costs
- Alert if design cost > 2x planning cost (indicates inefficiency)

---

## Success Criteria

### Functional Requirements
- [ ] Design Agent generates valid DesignSpecification JSON
- [ ] All semantic units from Planning Agent mapped to components
- [ ] API contracts include complete request/response schemas
- [ ] Data schemas are valid and implementable
- [ ] Design review checklist includes 10+ validation criteria
- [ ] Technology stack explicitly specified

### Quality Requirements
- [ ] 100% unit test pass rate (target: 80%+ coverage)
- [ ] 100% E2E test pass rate with real Planning Agent integration
- [ ] Pydantic validation catches invalid outputs
- [ ] No missing required fields in generated designs

### Performance Requirements
- [ ] Design generation latency < 15 seconds
- [ ] Cost per design < $0.05
- [ ] Telemetry captures all 4 metrics (latency, tokens in/out, cost)

### Integration Requirements
- [ ] Accepts ProjectPlan from Planning Agent without modification
- [ ] Output format compatible with Design Review Agent (FR-3)
- [ ] Semantic unit IDs traceable across agents

---

## Open Questions

1. **Design Review Checklist Generation:** Should checklist be generic or task-specific?
   - **Recommendation:** Task-specific (based on requirements and technology stack)
   - **Reasoning:** More effective review, catches domain-specific issues

2. **Context Files:** How should Design Agent use context files (e.g., existing architecture docs)?
   - **Phase 1:** Include as optional string field in input
   - **Phase 2:** Implement semantic search to find relevant context automatically

3. **Architectural Patterns:** Should we maintain a library of reusable patterns?
   - **Phase 1:** Embed common patterns in prompt examples
   - **Phase 2:** Build pattern library if we see repeated patterns

4. **Versioning:** How to handle design iterations?
   - **Phase 1:** Each design is immutable (new task_id for revisions)
   - **Phase 2:** Add version field if needed

---

## References

- PRD Section 4.1 (FR-2: Design Agent)
- PSPdoc.md Section V (Design Agent Prompt)
- Planning Agent ADR (`planning_agent_architecture_decision.md`)
- BaseAgent implementation (`src/asp/agents/base_agent.py`)
- Pydantic documentation: https://docs.pydantic.dev/

---

## Approval

**Decision:** Approved for implementation
**Next Steps:**
1. Implement Pydantic models for Design Agent
2. Create design prompt template with examples
3. Implement DesignAgent class
4. Write comprehensive tests
5. Run Planning→Design E2E integration tests

**Estimated Implementation Time:** 1-2 days
**Estimated Cost:** $0.20-0.40 for testing (8-10 test runs)
