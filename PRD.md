# Product Requirements Document: Agentic Software Process (ASP) Platform

**Version:** 1.0
**Date:** November 11, 2025
**Status:** Draft
**Owner:** TBD

---

## Executive Summary

The Agentic Software Process (ASP) Platform is a multi-agent orchestration system that applies formal software engineering discipline to autonomous AI agents. By adapting the Personal Software Process (PSP) and Team Software Process (TSP) methodologies for AI agents, ASP enables autonomous code generation with built-in quality gates, automated telemetry, and self-improvement capabilities.

**Key Value Proposition:** Transform autonomous AI agents from unpredictable "copilots" into disciplined, measurable, and continuously improving development team members through formal process structure and data-driven feedback loops.

---

## 1. Problem Statement

### 1.1 Current State

Autonomous AI coding agents are moving beyond simple code completion to executing entire development tasks. However, current approaches suffer from critical limitations:

- **High Ambiguity:** Agile methodologies rely on high-bandwidth human collaboration, which AI agents cannot replicate
- **Lack of Governance:** Autonomous agents introduce systemic risks including uncontrolled behavior, fragmented access, and lack of traceability
- **Quality Issues:** Agents produce "compounding errors" where design flaws propagate through implementation and testing
- **No Observability:** Teams lack metrics to measure agent performance, cost, or improvement over time
- **Chaotic Coordination:** Multi-agent systems lack formal orchestration frameworks, leading to unpredictable outcomes

### 1.2 Why Now?

- AI agents are transitioning from "copilots" to autonomous "agents" capable of complex reasoning and tool use
- Enterprises require auditable, reliable, and trustworthy autonomous systems
- Specification-first development is emerging as best practice for AI systems
- Formal methods (common in hardware design) are being recognized as necessary for AI agent safety

---

## 2. Goals & Objectives

### 2.1 Primary Goals

1. **Enable Disciplined Autonomous Development:** Create a formal framework for AI agents to execute software development tasks with PSP-level discipline
2. **Automate Quality Assurance:** Implement mandatory quality gates (Design Review, Code Review, Testing) as programmatic checks, not manual tasks
3. **Establish Full Observability:** Provide complete, automated telemetry for agent performance, cost, and quality metrics
4. **Enable Self-Improvement:** Create a feedback loop where agents analyze their own performance and propose process improvements

### 2.2 Success Metrics

| Metric | Target | Timeline |
|--------|--------|----------|
| Estimation Accuracy (Cost Vector Variance) | ±15% | Phase 2 (Month 3) |
| Defect Density (Defects per Semantic Complexity Unit) | <0.10 | Phase 3 (Month 6) |
| Phase Yield (% Defects Caught in Review vs. Test) | >80% | Phase 3 (Month 6) |
| Process Improvement Cycle Time | <72 hours from defect to PIP approval | Phase 5 (Month 12) |
| Human Review Time Reduction | 60% reduction vs. manual review | Phase 4 (Month 9) |

---

## 3. Target Users & Personas

### 3.1 Primary Users

**Persona 1: Engineering Manager**
- **Goals:** Improve team productivity, reduce defect rates, gain visibility into development metrics
- **Pain Points:** Cannot measure AI agent performance, lack of governance, unpredictable quality
- **Success Criteria:** Quantitative dashboards showing agent cost/performance, ability to approve process improvements

**Persona 2: Software Engineer**
- **Goals:** Offload routine development tasks to agents while maintaining code quality
- **Pain Points:** Agent outputs require extensive rework, lack of trust in agent-generated code
- **Success Criteria:** Agent-generated code passes review with minimal edits, clear audit trail of agent decisions

**Persona 3: DevOps/Platform Engineer**
- **Goals:** Deploy and operate reliable agent infrastructure, ensure observability and cost control
- **Pain Points:** No standardized agent deployment model, difficult to debug agent failures
- **Success Criteria:** Standardized agent deployment, comprehensive telemetry, cost tracking

---

## 4. Functional Requirements

### 4.1 Core Agent Roles

The system MUST implement the following specialized agents:

#### FR-1: Planning Agent
- **Input:** Human-provided requirements (natural language or structured)
- **Output:** Task decomposition JSON with Semantic Complexity scores + Project Plan with estimated Cost Vector (latency, tokens, API cost)
- **Algorithm:** PROBE-AI linear regression using historical performance data
- **Implementation:** Two-prompt chain (Task Decomposition → Effort Estimation)

#### FR-2: Design Agent
- **Input:** Requirements + Project Plan
- **Output:** Low-Level Design Specification JSON (API contracts, data schemas, component logic, design review checklist)
- **Standards:** MUST use provided design templates and architectural standards
- **Constraint:** Output must be detailed enough for separate Coding Agent to implement without ambiguity

#### FR-3: Design Review Agent
- **Input:** Design Specification JSON + Original Requirements
- **Output:** Design Review Report JSON (Pass/Fail status + defect list)
- **Process:** Verify every checklist item, identify logical inconsistencies, validate against non-functional requirements
- **Quality Gate:** Orchestrator MUST halt if status = "Failed"

#### FR-4: Coding Agent
- **Input:** Approved Design Specification + Coding Standards + Context Files (e.g., CLAUDE.md)
- **Output:** Complete, production-ready code as JSON (filename → full file content mapping)
- **Standards:** MUST adhere perfectly to project coding standards (type hints, docstrings, security best practices)
- **Constraint:** MUST provide FULL file contents, not diffs or partial updates

#### FR-5: Code Review Agent
- **Input:** Generated Code + Coding Standards + Code Review Checklist
- **Output:** Code Review Report JSON (Pass/Fail status + defect list)
- **Process:** Check every checklist item, log every defect using Defect Recording Log format
- **Quality Gate:** Orchestrator MUST halt if status = "Failed"

#### FR-6: Test Agent
- **Input:** Approved Code + Design Specification
- **Output:** Test Report JSON (build status + test results + defect list)
- **Process:**
  1. Compile/build and log errors
  2. Generate unit tests from design specification
  3. Create synthetic test data
  4. Execute tests and log failures

#### FR-7: Postmortem Agent (Meta-Agent)
- **Input:** Project Plan + Effort Log + Defect Log
- **Output:**
  1. Postmortem Report JSON (estimation accuracy, defect metrics, root cause analysis)
  2. Process Improvement Proposal (PIP) JSON with proposed prompt/checklist changes
- **Process:** Analyze performance data, identify top defect types, propose defensive changes to prompts
- **HITL Gate:** Human MUST approve PIP before changes are committed

#### FR-8: TSP Orchestrator Agent
- **Input:** High-level project requirements
- **Output:** Orchestrated execution of all agents through formal workflow
- **Process:**
  1. Execute Planning Agent to generate master plan
  2. Assign tasks to specialized agents in sequence
  3. Enforce quality gates (halt on review failures, require human approval for overrides)
  4. Trigger Postmortem Agent on task completion

### 4.2 Data & Telemetry Requirements

#### FR-9: Agent Cost Vector Logging
The system MUST automatically capture for every agent execution:
- **Computational Cost:** Processing latency (ms), memory usage
- **Financial Cost:** API call costs, token usage (input/output separately)
- **Task Cost:** Number of tool calls, number of self-correction loops

**Schema:** See Table 3 (Section VI) - Must include: Timestamp, Task_ID, Agent_Role, Metric_Type, Metric_Value, Unit

#### FR-10: Defect Recording Log
The system MUST automatically capture for every defect:
- Unique Defect_ID
- Task_ID linkage
- Defect_Type (from AI Defect Taxonomy)
- Phase_Injected (agent role that created defect)
- Phase_Removed (agent role that found defect)
- Effort_to_Fix_Vector (cost of correction loop)
- Description

**Schema:** See Table 4 (Section VI)

#### FR-11: AI Defect Taxonomy
The system MUST classify defects using this taxonomy:
1. Planning_Failure
2. Prompt_Misinterpretation
3. Tool_Use_Error
4. Hallucination
5. Security_Vulnerability
6. Conventional_Code_Bug
7. Task_Execution_Error
8. Alignment_Deviation

### 4.3 Process Standards & Artifacts

#### FR-12: Process Scripts (System Prompts)
- All agent prompts MUST be versioned and stored in a "Prompt Repository"
- Prompts MUST include: Role definition, Input specification, Task description, Response format (JSON schema)
- Prompts MUST be updateable via approved PIPs

#### FR-13: Checklists & Standards
The system MUST maintain:
- Design Review Checklist (architectural, security, performance validation)
- Code Review Checklist (coding standards, security patterns, test coverage)
- Coding Standards document (language version, style guide, security requirements)
- Defect Type Standard (taxonomy definitions)

#### FR-14: Historical Performance Database
- System MUST store all execution logs for PROBE-AI estimation
- Minimum 3 completed tasks required before estimation can activate
- Database MUST support time-series queries for regression analysis

### 4.4 User Interface & Interaction

#### FR-15: Human-in-the-Loop (HITL) Approval Points
The system MUST require human approval for:
1. **PIP Approval:** Human must review and approve all Process Improvement Proposals before prompt updates
2. **Quality Gate Overrides:** If Design Review or Code Review fails, human can approve override with justification
3. **High-Risk Operations:** Deployment, infrastructure changes, or security-critical code

#### FR-16: Observability Dashboard
The system MUST provide a dashboard showing:
- Real-time agent execution status
- Cost metrics (actual vs. planned)
- Quality metrics (defect density, phase yield)
- Estimation accuracy trends
- Root cause analysis summaries

#### FR-17: PIP Review Interface
The system MUST provide an interface for humans to:
- View the Postmortem Report with data visualizations
- Review proposed prompt changes as a diff
- Approve, reject, or request modifications to PIPs
- View PIP history and impact analysis

---

## 5. Non-Functional Requirements

### 5.1 Performance

| Requirement | Target |
|-------------|--------|
| NFR-1: Agent Response Time | <30s per agent execution (excluding LLM latency) |
| NFR-2: Orchestration Overhead | <5% additional latency vs. direct agent calls |
| NFR-3: Telemetry Write Latency | <100ms per log entry (async) |
| NFR-4: Dashboard Load Time | <2s for real-time metrics view |

### 5.2 Scalability

- **NFR-5:** System MUST support concurrent execution of 10+ tasks (agent teams)
- **NFR-6:** Historical database MUST support 100,000+ execution records with <1s query time
- **NFR-7:** System MUST be horizontally scalable (support multi-tenant deployment)

### 5.3 Reliability & Safety

- **NFR-8:** All quality gates MUST be fail-safe (default to blocking, not passing)
- **NFR-9:** Agent executions MUST be idempotent (re-runnable without side effects)
- **NFR-10:** System MUST support rollback of agent-generated code
- **NFR-11:** All agent actions MUST be auditable (full execution trace logged)

### 5.4 Security

- **NFR-12:** All agent prompts MUST sanitize user input to prevent prompt injection
- **NFR-13:** Agent tool access MUST follow principle of least privilege
- **NFR-14:** Generated code MUST pass automated security scanning (SAST)
- **NFR-15:** PIP approval process MUST support multi-level authorization

### 5.5 Usability

- **NFR-16:** System MUST provide clear error messages when agents fail
- **NFR-17:** HITL interfaces MUST support approval actions within 3 clicks
- **NFR-18:** Dashboard MUST be accessible to non-technical stakeholders

---

## 6. System Architecture

### 6.1 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                   Human Users (HITL)                         │
│  (Engineering Manager, Software Engineer, DevOps Engineer)   │
└─────────────────┬───────────────────────────────────────────┘
                  │
┌─────────────────▼───────────────────────────────────────────┐
│              Web UI / Dashboard Layer                        │
│  - Real-time Metrics Dashboard                               │
│  - PIP Review Interface                                      │
│  - Quality Gate Override Interface                           │
└─────────────────┬───────────────────────────────────────────┘
                  │
┌─────────────────▼───────────────────────────────────────────┐
│         TSP Orchestrator Agent (Control Plane)               │
│  - Task Planning & Assignment                                │
│  - Quality Gate Enforcement                                  │
│  - HITL Workflow Management                                  │
└────┬──────┬──────┬──────┬──────┬──────┬──────┬──────────────┘
     │      │      │      │      │      │      │
     ▼      ▼      ▼      ▼      ▼      ▼      ▼
┌─────────────────────────────────────────────────────────────┐
│              Specialized Agent Layer                         │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐       │
│  │ Planning │ │  Design  │ │ Design   │ │  Coding  │       │
│  │  Agent   │ │  Agent   │ │  Review  │ │  Agent   │       │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘       │
│  ┌──────────┐ ┌──────────┐ ┌──────────────────────┐        │
│  │   Code   │ │   Test   │ │    Postmortem        │        │
│  │  Review  │ │  Agent   │ │   (Meta-Agent)       │        │
│  └──────────┘ └──────────┘ └──────────────────────┘        │
└────┬──────┬──────┬──────┬──────┬──────┬──────┬──────────────┘
     │      │      │      │      │      │      │
     ▼      ▼      ▼      ▼      ▼      ▼      ▼
┌─────────────────────────────────────────────────────────────┐
│               Data & Infrastructure Layer                    │
│  ┌────────────────┐  ┌────────────────┐  ┌───────────────┐ │
│  │  Prompt Repo   │  │  Telemetry DB  │  │  Code Output  │ │
│  │  (Versioned)   │  │  (Time-Series) │  │  Repository   │ │
│  └────────────────┘  └────────────────┘  └───────────────┘ │
│  ┌────────────────┐  ┌────────────────┐                     │
│  │  Standards &   │  │  LLM Provider  │                     │
│  │  Checklists    │  │  (OpenAI, etc.)│                     │
│  └────────────────┘  └────────────────┘                     │
└─────────────────────────────────────────────────────────────┘
```

### 6.2 Data Flow: Development Cycle

```
1. Human submits requirements
   ↓
2. Orchestrator → Planning Agent → Generates Project Plan
   ↓
3. Orchestrator → Design Agent → Generates Design Spec
   ↓
4. Orchestrator → Design Review Agent → Review (GATE: Pass/Fail)
   ├─ FAIL: Loop back to Design Agent with defects
   └─ PASS: Continue to Coding Agent
   ↓
5. Orchestrator → Coding Agent → Generates Code
   ↓
6. Orchestrator → Code Review Agent → Review (GATE: Pass/Fail)
   ├─ FAIL: Loop back to Coding Agent with defects
   └─ PASS: Continue to Test Agent
   ↓
7. Orchestrator → Test Agent → Build & Test (GATE: Pass/Fail)
   ├─ FAIL: Loop back to Coding Agent with defects
   └─ PASS: Continue to Postmortem
   ↓
8. Orchestrator → Postmortem Agent → Analyze Performance
   ↓
9. Postmortem Agent → Generates PIP → Human Approval (HITL)
   ├─ APPROVED: Update Prompt Repository
   └─ REJECTED: Log feedback for future analysis
   ↓
10. Cycle Complete (All data logged to Telemetry DB)
```

### 6.3 Technology Stack Recommendations

| Component | Recommended Technologies |
|-----------|-------------------------|
| **Orchestrator** | LangGraph, CrewAI, AutoGen, or custom Python orchestration |
| **LLM Provider** | OpenAI GPT-4, Anthropic Claude, or Azure OpenAI |
| **Telemetry/Observability** | Langfuse, AgentOps, Arize Phoenix, or custom PostgreSQL + TimescaleDB |
| **Prompt Management** | Promptfoo, Langchain Hub, or Git-based version control |
| **Web Dashboard** | React/Next.js + FastAPI backend |
| **Database** | PostgreSQL (relational) + TimescaleDB (time-series) |
| **Code Repository** | Git (GitHub, GitLab, or Bitbucket) |

---

## 7. Implementation Roadmap

The ASP platform MUST be implemented incrementally, following the 5-phase approach:

### Phase 1: ASP0 - Measurement Foundation (Months 1-2)
**Goal:** Establish baseline process and begin data collection

**Deliverables:**
- [ ] Implement Agent Cost Vector logging schema (Table 3)
- [ ] Implement Defect Recording Log schema (Table 4)
- [ ] Deploy observability layer (Langfuse/AgentOps integration)
- [ ] Integrate with existing development process (human or semi-autonomous)
- [ ] Create initial dashboard for metrics visualization

**Success Criteria:**
- 100% of agent executions logged
- 30+ tasks completed with full telemetry
- Dashboard accessible to stakeholders

**Risk:** Low (no autonomous agents deployed)

---

### Phase 2: ASP1 - Estimation (Months 3-4)
**Goal:** Deploy Planning Agent and validate PROBE-AI estimation model

**Deliverables:**
- [ ] Implement Planning Agent (Task Decomposition + Estimation)
- [ ] Build PROBE-AI linear regression engine
- [ ] Run Planning Agent in shadow mode (parallel to human estimation)
- [ ] Create estimation accuracy comparison dashboard

**Success Criteria:**
- Planning Agent estimates within ±20% of actual costs on 70% of tasks
- Human team trusts agent estimates for planning purposes

**Risk:** Medium (agent provides recommendations but no autonomy)

---

### Phase 3: ASP2 - Gated Review (Months 5-6)
**Goal:** Deploy Review Agents and refine quality gates

**Deliverables:**
- [ ] Implement Design Review Agent
- [ ] Implement Code Review Agent
- [ ] Deploy agents as assistants to human reviewers
- [ ] Collect feedback and refine checklists
- [ ] Measure defect detection rates (agent vs. human)

**Success Criteria:**
- Review agents detect 60%+ of defects found by humans
- Defect density <0.15
- Phase yield >70% (defects caught in review vs. test)

**Risk:** Medium-High (agents find defects but humans validate)

---

### Phase 4: ASP-TSP - Autonomous Orchestration (Months 7-9)
**Goal:** Deploy full autonomous agent team with TSP Orchestrator

**Deliverables:**
- [ ] Implement Design Agent, Coding Agent, Test Agent
- [ ] Implement TSP Orchestrator Agent
- [ ] Define quality gate enforcement logic
- [ ] Implement HITL override workflow
- [ ] Deploy for low-risk tasks (bug fixes, unit tests)

**Success Criteria:**
- 50% of low-risk tasks completed end-to-end by agents
- Human review time reduced by 40%
- Zero critical defects shipped from agent-generated code

**Risk:** High (autonomous code generation with quality gates)

---

### Phase 5: ASP-Loop - Self-Improvement (Months 10-12)
**Goal:** Activate full feedback loop with Postmortem Agent

**Deliverables:**
- [ ] Implement Postmortem Agent (Performance Analysis + PIP Generation)
- [ ] Build PIP Review Interface for HITL approval
- [ ] Implement prompt versioning and update workflow
- [ ] Measure improvement cycle time and impact

**Success Criteria:**
- First PIP approved and deployed within 72 hours of defect detection
- Measurable reduction in defect density after PIP deployment
- Process improvement cycle operating continuously

**Risk:** High (agents propose changes to their own behavior)

---

## 8. Dependencies & Integrations

### 8.1 External Dependencies

| Dependency | Type | Criticality | Mitigation |
|------------|------|-------------|------------|
| LLM API (OpenAI/Anthropic) | Service | Critical | Multi-provider support, fallback models |
| Observability Platform | Service | High | Self-hosted option (PostgreSQL) |
| Code Repository | Service | High | Standard Git, supports GitHub/GitLab/Bitbucket |
| CI/CD Pipeline | Service | Medium | Integration with existing pipeline |

### 8.2 Internal Integrations

- **Version Control System:** Must integrate with existing Git workflow
- **Issue Tracking:** Optional integration with Jira/Linear for task management
- **Security Scanning:** Must integrate with SAST/DAST tools for code review
- **Deployment Pipeline:** Must integrate with existing CI/CD for code deployment

---

## 9. Risks & Mitigation

| Risk | Impact | Probability | Mitigation Strategy |
|------|--------|-------------|---------------------|
| **R1: Agent hallucination produces vulnerable code** | Critical | Medium | Mandatory Code Review Agent, automated SAST scanning, human HITL approval for high-risk changes |
| **R2: Estimation model inaccurate due to insufficient data** | High | High | Require minimum 30 tasks before enabling PROBE-AI, implement confidence intervals |
| **R3: Infinite feedback loops in agent self-correction** | High | Medium | Implement max retry limits (3x), fallback to human intervention, timeouts |
| **R4: PIP approval bottleneck slows improvement cycle** | Medium | High | Create PIP prioritization system, pre-approve low-risk changes, assign PIP reviewers |
| **R5: High LLM API costs** | High | Medium | Implement cost caps per task, use cheaper models for reviews, cache repeated queries |
| **R6: User resistance to agent-generated code** | Medium | High | Incremental rollout (Phase 1-5), extensive logging/auditability, human HITL controls |
| **R7: Quality gates too strict (false positives block progress)** | Medium | Medium | Continuously refine checklists based on false positive analysis, HITL override capability |
| **R8: Prompt injection attacks on agent system** | Critical | Low | Input sanitization, prompt engineering best practices, security review of all prompts |

---

## 10. Success Criteria & KPIs

### 10.1 Phase-Specific KPIs

| Phase | KPI | Target | Measurement Method |
|-------|-----|--------|-------------------|
| Phase 1 | Logging Coverage | 100% | % of agent executions with telemetry |
| Phase 2 | Estimation Accuracy | ±20% | Planned vs. Actual Cost Vector variance |
| Phase 3 | Defect Detection Rate | 60% | Agent-found defects / Total defects |
| Phase 4 | Task Completion Rate | 50% | % of tasks completed without human intervention |
| Phase 5 | Improvement Cycle Time | <72 hrs | Time from defect to PIP deployment |

### 10.2 Long-Term Business KPIs

| KPI | Baseline | 12-Month Target | 24-Month Target |
|-----|----------|-----------------|-----------------|
| Development Velocity | 100% | 150% | 200% |
| Defect Escape Rate | Baseline | -40% | -60% |
| Code Review Time | Baseline | -50% | -70% |
| Cost per Feature | $X | -30% | -50% |
| Time to Market | Y days | -35% | -50% |

---

## 11. Open Questions & Future Considerations

### 11.1 Open Questions (To Be Resolved)

1. **Q1:** Should the system support multi-language codebases initially, or start with Python-only?
2. **Q2:** What is the appropriate balance between agent autonomy and human oversight for different task risk levels?
3. **Q3:** Should PIPs require multi-level approval (engineer + manager) or single-level?
4. **Q4:** How should the system handle conflicting PIPs from different Postmortem analyses?
5. **Q5:** What is the minimum viable historical dataset size for PROBE-AI to be reliable?

### 11.2 Future Enhancements (Post-MVP)

- **Multi-Tenant Support:** Enable multiple teams/organizations on shared infrastructure
- **Custom Agent Plugins:** Allow users to define custom agent roles beyond the core 7
- **Real-Time Collaboration:** Enable human developers to work alongside agents in real-time
- **Cross-Project Learning:** Enable agents to learn from other projects' historical data
- **Agent Performance Benchmarking:** Compare agent performance across different LLM providers
- **Natural Language PIP Review:** Allow stakeholders to approve PIPs via conversational interface
- **Automated A/B Testing:** Test prompt variations automatically and select best performers

---

## 12. Appendices

### Appendix A: Key Terminology

| Term | Definition |
|------|------------|
| **ASP** | Agentic Software Process - adaptation of PSP for AI agents |
| **PSP** | Personal Software Process - formal methodology for individual engineers |
| **TSP** | Team Software Process - formal methodology for engineering teams |
| **PROBE-AI** | Proxy-Based Estimation method adapted for AI agents using linear regression |
| **Agent Cost Vector** | Multi-dimensional measure of agent resource consumption (latency, tokens, API cost, tool calls) |
| **Semantic Complexity** | Composite metric measuring work required (replaces Lines of Code) |
| **Alignment Deviation** | AI-specific defect category for behavior that violates business goals |
| **PIP** | Process Improvement Proposal - proposed change to agent prompts/process |
| **HITL** | Human-in-the-Loop - human approval required for critical decisions |
| **Phase Yield** | Percentage of defects caught in current phase vs. escaped to later phases |

### Appendix B: Reference Documents

- PSP/TSP Methodology: Software Engineering Institute, Carnegie Mellon University
- Agentic AI Frameworks: LangChain, AutoGen, CrewAI documentation
- Specification-First AI Development: Industry research papers (see PSPdoc.md citations)
- AI Agent Safety: NIST AI Risk Management Framework

### Appendix C: Prompt Templates

See Section IV (Planning), Section V (Development), and Section VII (Postmortem) in PSPdoc.md for complete prompt templates for each agent role.

---

## 13. Implementation Considerations & Risk Mitigation

This section addresses critical concerns that must be resolved before and during implementation to ensure the ASP platform's success.

### 13.1 Critical Implementation Concerns

#### C1: Semantic Complexity Calculation Algorithm

**Problem:** The PRD defines Semantic Complexity conceptually but lacks a concrete calculation formula. Without this, the Planning Agent cannot consistently estimate task complexity.

**Solution:** Define a weighted scoring formula for the Planning Agent:

```
Semantic_Complexity =
  (2 × API_Interactions) +
  (5 × Data_Transformations) +
  (3 × Logical_Branches) +
  (4 × Code_Entities_Modified) +
  (Novelty_Multiplier × Base_Score)

Where:
- API_Interactions: Number of external API/tool calls required
- Data_Transformations: Number of data structure conversions or calculations
- Logical_Branches: Number of conditional paths (if/else, switch, loops)
- Code_Entities_Modified: Number of functions/classes/modules to be created or changed
- Novelty_Multiplier: 1.0 (familiar), 1.5 (moderate), 2.0 (novel/experimental)
- Base_Score: Sum of weighted factors before novelty
```

**Action Items:**
- [ ] Validate formula with historical data (Phase 1)
- [ ] Calibrate weights based on actual vs. estimated complexity correlation
- [ ] Document formula in Planning Agent prompt template

---

#### C2: Bootstrapping Problem - Cold Start Estimation

**Problem:** PROBE-AI requires historical data from "at least 3 prior projects" to build regression models. The first 3-10 tasks have no baseline for estimation.

**Solution:** Implement a hybrid bootstrap process:

**Phase 0.5: Bootstrap Period (Pre-Phase 2)**
1. **Tasks 1-10:** Use human expert estimates as baseline
2. **All tasks:** Collect full telemetry (Agent Cost Vector, Semantic Complexity)
3. **After task 10:** Run PROBE-AI validation
   - Calculate estimation accuracy if human estimates had been used
   - If R² > 0.7, enable PROBE-AI in shadow mode (Phase 2)
   - If R² < 0.7, continue to task 20 before enabling

**Fallback Strategy:**
- If PROBE-AI confidence interval is >50%, revert to human estimation
- Display confidence score with every estimate

**Action Items:**
- [ ] Add Phase 0.5 to implementation roadmap
- [ ] Define minimum dataset criteria (task count, variance threshold)
- [ ] Implement confidence interval calculation in PROBE-AI

---

#### C3: Context Window Management for Large Codebases

**Problem:** Large codebases may exceed LLM token limits (e.g., 200K tokens for Claude). Design and Code agents need full context but cannot load entire repositories.

**Solution:** Implement a multi-tiered context strategy:

**Tier 1: Context Management Requirements (New FR-20)**
The system MUST implement intelligent context selection:
1. **Semantic Search:** Use embedding-based search to find relevant code sections
2. **Dependency Analysis:** Include imports and dependencies of modified files
3. **Context Files:** Load project-specific guidance files (e.g., Claude.md, architecture docs)
4. **Context Budget:** Allocate max 50% of token budget to context, 50% to generation

**Tier 2: Chunking Strategy**
For tasks affecting >100 files:
1. Planning Agent decomposes into smaller semantic units (max 20 files per unit)
2. Orchestrator processes units sequentially
3. Each unit includes interfaces/contracts from previous units as context

**Action Items:**
- [ ] Add FR-20: Context Management to Section 4
- [ ] Evaluate context tools (e.g., LangChain embeddings, Claude's contextual retrieval)
- [ ] Define context budget allocation policy

---

#### C4: Cost Projections and Budget Planning

**Problem:** No financial projections provided. Stakeholders cannot approve without understanding LLM API costs, which could range from $100s to $10,000s/month.

**Solution:** Add cost modeling appendix with three deployment scenarios:

**Appendix D: Cost Model Projections**

**Assumptions:**
- Average task requires 5 agent executions (Planning, Design, Design Review, Code, Test)
- Average agent execution: 10K input tokens, 5K output tokens
- LLM pricing: $3/1M input tokens, $15/1M output tokens (Claude Sonnet tier)

| Scenario | Tasks/Month | Avg Tokens/Task | Monthly API Cost | Annual Cost |
|----------|-------------|-----------------|------------------|-------------|
| **Small Team** (10 tasks) | 10 | 75K | $22.50 | $270 |
| **Medium Team** (50 tasks) | 50 | 75K | $112.50 | $1,350 |
| **Large Team** (200 tasks) | 200 | 75K | $450 | $5,400 |

**Additional Costs:**
- Observability platform: $50-500/month (depending on log volume)
- Database hosting: $25-200/month (TimescaleDB cloud or self-hosted)
- Compute for orchestration: $50-300/month

**Total Cost of Ownership (TCO) - Medium Team Example:**
- Year 1: $1,350 (API) + $600 (observability) + $300 (database) + $1,200 (compute) = **$3,450**
- ROI Projection: If 1 engineer saves 5 hours/week = 260 hours/year × $100/hour = $26,000 value

**Action Items:**
- [ ] Add Appendix D: Cost Model to PRD
- [ ] Define cost monitoring alerts (e.g., >$1000/month)
- [ ] Implement per-task cost caps (fail-safe at $10/task)

---

#### C5: Self-Improvement Degradation and Rollback Strategy

**Problem:** Process Improvement Proposals (PIPs) may degrade performance rather than improve it. No rollback mechanism specified.

**Solution:** Implement PIP versioning with automated regression detection:

**New FR-21: PIP Version Control and Rollback**
The system MUST maintain:
1. **Prompt Versioning:** Git-based version control for all agent prompts
2. **Task-Prompt Linkage:** Log which prompt version generated which output
3. **Performance Baseline:** Calculate 7-day rolling average for key metrics before PIP deployment
4. **Regression Detection:** After PIP deployment, monitor for:
   - Defect density increase >20%
   - Cost vector increase >30%
   - Phase yield decrease >15%
5. **Automatic Rollback:** If regression detected over 5 tasks, auto-flag for human review
6. **Manual Rollback:** HITL interface must provide 1-click rollback to previous prompt version

**PIP Deployment Process:**
1. Human approves PIP
2. Deploy PIP to "canary" mode (10% of tasks)
3. Monitor for 2 days
4. If metrics stable/improved, deploy to 100%
5. If metrics degrade, auto-rollback and request human analysis

**Action Items:**
- [ ] Add FR-21 to Section 4.1
- [ ] Design PIP canary deployment system
- [ ] Define regression detection thresholds

---

### 13.2 Medium Priority Concerns

#### C6: HITL Bottleneck and SLA Requirements

**Problem:** If PIP approvals require human review but reviewers are busy, improvement cycle stalls. Target is <72 hours but no enforcement mechanism.

**Solution:**

**PIP Approval SLA Policy:**
- **Priority 1 (Critical):** Security vulnerabilities, blocking errors → 4 hour SLA
- **Priority 2 (High):** Quality improvements, cost reduction → 24 hour SLA
- **Priority 3 (Medium):** Process optimization → 72 hour SLA
- **Priority 4 (Low):** Documentation, logging improvements → 7 day SLA

**Escalation Process:**
- If SLA exceeded, auto-escalate to manager
- If 2× SLA exceeded, auto-reject PIP and request re-prioritization

**Async Approval Options:**
- Pre-approve "safe" PIP categories (e.g., adding items to checklists)
- Implement multi-approver system (any 2 of 3 engineers can approve)
- After 30 days of zero rollbacks, increase pre-approval categories

**Action Items:**
- [ ] Define PIP priority classification rules
- [ ] Implement SLA tracking dashboard
- [ ] Create escalation workflow

---

#### C7: Agent and Prompt Version Traceability

**Problem:** If prompts constantly update, debugging becomes difficult. Need to know exactly which prompt version generated which code for audit trails and reproducibility.

**Solution:**

**New FR-22: Execution Traceability**
The telemetry system MUST log for every agent execution:
1. **Prompt Version Hash:** SHA-256 of the exact prompt used
2. **Agent Code Version:** Git commit hash of agent orchestration code
3. **LLM Model Version:** Exact model ID (e.g., "gpt-4-0125-preview")
4. **Timestamp:** ISO 8601 with timezone
5. **Input Hash:** SHA-256 of input data (for reproducibility testing)

**Reproduction Workflow:**
When debugging a defect:
1. Query telemetry DB by Task_ID
2. Retrieve exact prompt version, model version, input hash
3. Re-run agent with identical parameters
4. Compare outputs to identify if issue is deterministic or stochastic

**Action Items:**
- [ ] Add FR-22 to Section 4.2
- [ ] Implement prompt hashing in orchestrator
- [ ] Create "reproduce task" CLI command

---

### 13.3 Minor Concerns

#### C8: Staffing and Resource Plan

**Problem:** No guidance on team size required for implementation and operation.

**Recommended Staffing by Phase:**

| Phase | Engineers | Roles | Time Commitment |
|-------|-----------|-------|-----------------|
| **Phase 1** | 2-3 | 1 Backend, 1 Data Engineer, 1 DevOps | 50% (3 months) |
| **Phase 2** | 2 | 1 ML Engineer, 1 Backend | 50% (2 months) |
| **Phase 3** | 3 | 1 ML Engineer, 2 Backend (for agent dev) | 75% (2 months) |
| **Phase 4** | 4 | 2 Backend, 1 ML Engineer, 1 QA | 100% (3 months) |
| **Phase 5** | 3 | 1 ML Engineer, 1 Backend, 1 Product Manager | 50% (3 months) |

**Ongoing Operations (Post-Phase 5):**
- 1 Platform Engineer (50% FTE) - infrastructure and observability
- 1 ML Engineer (25% FTE) - PIP review and prompt optimization
- 1 Product Owner (10% FTE) - prioritization and roadmap

---

#### C9: Dashboard Mockups and UX Requirements

**Problem:** No visual guidance for dashboard design. Risk of building wrong interface.

**Action Items for Pre-Phase 1:**
- [ ] Create wireframes for 3 key screens:
  1. Real-time agent execution dashboard (for DevOps persona)
  2. PIP review interface (for ML Engineer persona)
  3. Executive metrics dashboard (for Engineering Manager persona)
- [ ] Conduct user interviews with 5 target users per persona
- [ ] Define top 5 "must-see" metrics for each persona

**Defer to Phase 1:** Build minimal dashboard first, iterate based on usage data.

---

#### C10: Integration Testing Strategy

**Problem:** No plan for validating full orchestration flow before production.

**Recommended Testing Strategy:**

**Phase 1-2 (Pre-Autonomous):**
- Manual end-to-end tests with synthetic tasks
- Validate telemetry collection accuracy (compare to manual logs)
- Test PROBE-AI with historical data (train/test split)

**Phase 3-4 (Autonomous Agents):**
- **Synthetic Task Suite:** Create 20 "golden path" tasks with known correct outputs
- **Adversarial Testing:** Inject ambiguous requirements, edge cases
- **Quality Gate Validation:** Manually inject defects, verify review agents catch them

**Phase 5 (Self-Improvement):**
- **PIP Simulation:** Manually create PIPs, test rollback workflow
- **Regression Testing:** Deploy intentionally degraded prompt, verify auto-rollback triggers

**Continuous Validation:**
- Run synthetic task suite weekly
- Alert if success rate drops below 90%

**Action Items:**
- [ ] Create synthetic task repository
- [ ] Define "golden path" test cases
- [ ] Implement continuous regression testing pipeline

---

### 13.4 Risk Register Updates

The following risks should be added to Section 9:

| Risk | Impact | Probability | Mitigation Strategy |
|------|--------|-------------|---------------------|
| **R9: Semantic Complexity formula inaccurate** | High | High | Calibrate with historical data (C1), iterate formula in Phase 1 |
| **R10: Insufficient data for PROBE-AI** | Medium | High | Implement bootstrap period (C2), use human estimates for first 10 tasks |
| **R11: Context exceeds token limits** | High | Medium | Implement context management (C3), use chunking strategy |
| **R12: Cost overruns exceed budget** | Critical | Medium | Implement per-task cost caps (C4), monitor monthly spend |
| **R13: PIP degrades performance** | High | Medium | Implement canary deployment and auto-rollback (C5) |
| **R14: HITL approval bottleneck** | Medium | High | Define SLAs and escalation process (C6), pre-approve safe categories |

---

## 14. Bootstrap Learning Framework

This section defines the ASP system's core learning strategy: **all agent capabilities start in supervised "learning mode" and graduate to autonomy based on demonstrated accuracy.**

### 14.1 Core Principle

**Principle:** _Autonomy is earned through demonstrated reliability, not assumed._

Every agent capability follows a three-phase lifecycle:
1. **Learning Mode:** Human validates all outputs, system collects accuracy data
2. **Shadow Mode:** Agent provides recommendations alongside humans, predictions compared to actuals
3. **Autonomous Mode:** Agent operates independently, with periodic recalibration

### 14.2 Bootstrap Capabilities

#### B1: PROBE-AI Estimation Accuracy

**What to Measure:**
- Estimation accuracy: Planned vs. Actual Cost Vector variance
- Model fit: R² coefficient from linear regression
- Confidence intervals: Standard error of estimates

**Bootstrap Process:**
```
Phase 0.5 (Bootstrap Period):
- Tasks 1-10:  Human estimates + full telemetry collection
- Task 11:     Run PROBE-AI validation (train on 1-10)
              Calculate R² and prediction accuracy
              If R² > 0.7 → Enable Shadow Mode
              If R² < 0.7 → Continue to task 20

Shadow Mode:
- Tasks 11-20: PROBE-AI predicts alongside human estimates
              Compare predictions to actuals
              Track: Mean Absolute Percentage Error (MAPE)

Autonomous Mode:
- Task 21+:    If MAPE < 20% over last 10 tasks → Enable autonomous estimation
              Display confidence interval with each estimate
              If confidence interval > ±50% → Flag for human review
```

**Graduation Criteria:**
- Minimum 10 tasks completed
- R² > 0.7 (model explains 70%+ of variance)
- MAPE < 20% over last 10 tasks
- Dataset includes tasks across complexity range (low/medium/high)

**Ongoing Monitoring:**
- Monthly recalibration as dataset grows
- Alert if MAPE increases >10% from baseline
- Automatic regression to Shadow Mode if accuracy degrades

**New FR-23: Bootstrap Metrics Dashboard**
The system MUST provide a dashboard showing:
- Current mode for each capability (Learning/Shadow/Autonomous)
- Accuracy metrics and trends
- Graduation criteria progress (e.g., "8/10 tasks completed for PROBE-AI")
- Alerts for degradation requiring human intervention

---

#### B2: Task Decomposition Quality

**What to Measure:**
- **Completeness:** Do decomposed tasks cover all requirements? (% coverage)
- **Accuracy:** Are Semantic Complexity estimates accurate per subtask? (±% variance)
- **Sequencing:** Does task order make logical sense? (human rating 1-5)
- **Correction Rate:** % of decompositions requiring human edits before execution

**Bootstrap Process:**
```
Learning Mode (Tasks 1-15):
- Planning Agent generates task decomposition
- Human reviews EVERY decomposition before execution
- Human logs corrections in structured format:
  {
    "missing_tasks": ["Add error handling", "Update docs"],
    "incorrect_complexity": {"SU-003": "estimated 5, should be 12"},
    "sequencing_issues": "SU-004 must come before SU-002"
  }
- Track correction rate per task

Shadow Mode (Tasks 16-30):
- Planning Agent decomposition used if correction rate < 20% for last 5 tasks
- Human spot-checks 20% of decompositions
- Track defect escape rate (issues found during execution that should have been in decomposition)

Autonomous Mode (Task 31+):
- Enable if: Correction rate < 10% AND Defect escape rate < 5%
- Monthly human audits of 10% of decompositions
```

**Graduation Criteria:**
- 15+ tasks completed in Learning Mode
- Correction rate < 10% over last 5 tasks
- Defect escape rate < 5% over last 10 tasks
- Completeness score > 90% (human rating)

**Feedback Loop:**
- Add missed task patterns to Planning Agent prompt
- Example: "If requirements mention 'user authentication', always include 'Add security tests' as a subtask"

---

#### B3: Error-Prone Area Detection

**What to Measure:**
- **Defect Density by Component:** Defects per Semantic Complexity unit for each code module
- **Defect Density by Task Type:** Defects per task for categories (auth, database, API, UI)
- **Defect Density by Agent:** Which agents inject most defects?
- **Temporal Patterns:** Do defects increase over time (agent drift)?

**Bootstrap Process:**
```
Learning Mode (Phase 1-2, First 30 tasks):
- Collect comprehensive defect data with rich metadata:
  {
    "defect_id": "D-042",
    "component": "src/auth/login.py",
    "task_type": "authentication",
    "injecting_agent": "Coding_Agent",
    "defect_type": "5_Security_Vulnerability",
    "complexity": 18
  }
- NO automated actions yet, just data collection

Analysis Mode (After 30 tasks):
- Run statistical analysis:
  - Calculate defect density per component (sort descending)
  - Calculate defect rate per task type
  - Identify top 10 "high-risk" components (defect density > 2x median)
  - Identify top 3 "high-risk" task types

Autonomous Mode (Phase 3+):
- Use risk map to trigger enhanced reviews:
  - Tasks touching high-risk components → Add extra checklist items
  - High-risk task types → Require human review even if agent passes
- Example: If "authentication" has 3x higher defect rate, all auth tasks get mandatory human review

Recalibration:
- Recalculate risk map monthly
- Components/task types improve over time → graduate to lower risk tier
- New high-risk areas emerge → add to enhanced review list
```

**Graduation Criteria:**
- Minimum 30 tasks with defect data
- Risk map updated and validated by engineering lead
- Enhanced review rules defined and documented

**Impact Metrics:**
- Target: 30% reduction in defect density for high-risk areas after enhanced reviews deployed
- Track: Defect escape rate before/after risk-based review implementation

---

#### B4: Review Agent Effectiveness

**What to Measure:**
- **True Positive Rate:** % of agent-flagged issues that are real defects
- **False Positive Rate:** % of agent-flagged issues that are incorrect
- **False Negative Rate (Escape Rate):** % of defects found in Test that should have been caught in Review
- **By Defect Type:** Effectiveness varies by defect category (security vs. logic errors)

**Bootstrap Process:**
```
Learning Mode (Phase 3, First 20 reviews):
- Review Agents (Design + Code) flag potential defects
- Human validates EVERY finding:
  - "True Positive": Real defect, good catch
  - "False Positive": Not a defect, agent was wrong
  - "False Negative": (discovered retroactively when Test finds defect)
- Track per-defect-type accuracy

Analysis Mode (After 20 reviews):
- Calculate metrics:
  - Overall: TP rate, FP rate, Escape rate
  - Per defect type: Agent good at finding "6_Conventional_Code_Bug" but misses "5_Security_Vulnerability"
- Identify improvement opportunities:
  - High FP rate for defect type X → Refine checklist to be more specific
  - High escape rate for defect type Y → Add examples of Y to agent prompt

Shadow Mode (Reviews 21-40):
- Deploy improved prompts/checklists based on analysis
- Continue human validation but reduce to 50% sampling
- Track improvement in metrics

Autonomous Mode (Review 41+):
- Graduate if: TP rate > 80%, FP rate < 20%, Escape rate < 5%
- Human spot-checks 10% of reviews
- Monthly recalibration
```

**Graduation Criteria:**
- 20+ reviews completed with full validation
- True Positive rate > 80% (agent finds real issues)
- False Positive rate < 20% (agent doesn't waste human time)
- Escape rate < 5% (few defects slip through to Test)

**Feedback Loop (PIP Integration):**
- When review agent misses a defect (found in Test), Postmortem Agent automatically:
  1. Analyzes why it was missed (e.g., "Not on checklist")
  2. Generates PIP to add that pattern to review checklist
  3. Tags PIP as "Bootstrap Improvement - High Priority"

---

#### B5: Defect Type Prediction

**What to Measure:**
- **Defect Type Correlation:** Do certain task characteristics predict defect types?
  - Example: Database tasks → higher risk of "6_Conventional_Code_Bug" (SQL syntax errors)
  - Example: Authentication tasks → higher risk of "5_Security_Vulnerability"
- **Predictive Accuracy:** Can we predict top 3 likely defect types before task starts?

**Bootstrap Process:**
```
Learning Mode (Phase 1-3, First 50 tasks):
- Collect rich task metadata + defect data:
  {
    "task_id": "Task-042",
    "task_type": "authentication",
    "touches_components": ["auth/", "database/"],
    "keywords": ["login", "password", "session"],
    "complexity": 18,
    "defects_found": ["5_Security_Vulnerability", "6_Conventional_Code_Bug"]
  }
- NO predictions yet, just correlation analysis

Analysis Mode (After 50 tasks):
- Build predictive model:
  - Use classification algorithm (e.g., decision tree, logistic regression)
  - Features: task_type, components, keywords, complexity
  - Target: Top 3 defect types for this task
- Validate model: Train on first 40 tasks, test on last 10
- Calculate prediction accuracy (% of actual defects that were predicted)

Shadow Mode (Task 51+):
- For each new task, model predicts top 3 likely defect types
- Pre-populate review checklists with predicted defect types
- Human validates: Were predictions useful?
- Track: Did enhanced checklists improve detection rate for predicted defects?

Autonomous Mode (After validation):
- If prediction accuracy > 60% AND it improves detection rate by 15%+:
  - Automatically customize review checklists per task
  - Example: Auth task → Add extra items: "Check for hardcoded credentials", "Validate session timeout"
- Monthly retraining of prediction model as dataset grows
```

**Graduation Criteria:**
- 50+ tasks with defect type data
- Prediction accuracy > 60% (predicts defects that actually occur)
- Measurable improvement: Defect detection rate increases 15%+ when using predicted checklists
- Model validated by data scientist or ML engineer

**Advanced Future State:**
- Integrate with static analysis tools (SAST) to improve predictions
- Predict defect severity, not just type
- Predict which agents are most likely to inject which defect types

---

### 14.3 Unified Bootstrap Dashboard

**New FR-24: Bootstrap Status Dashboard**

The system MUST provide a unified dashboard showing the learning status of all capabilities:

| Capability | Current Mode | Tasks Completed | Key Metric | Graduation Criteria | Status |
|------------|--------------|-----------------|------------|---------------------|--------|
| PROBE-AI Estimation | Shadow | 15/20 | MAPE: 18% | MAPE < 20% | On Track |
| Task Decomposition | Learning | 8/15 | Correction Rate: 25% | Correction < 10% | In Progress |
| Error-Prone Detection | Learning | 22/30 | Defects Logged: 22 | 30 tasks | Near Complete |
| Review Agent (Design) | Learning | 5/20 | TP: 75%, FP: 30% | TP > 80%, FP < 20% | Needs Improvement |
| Review Agent (Code) | Learning | 5/20 | TP: 85%, FP: 15% | TP > 80%, FP < 20% | Performing Well |
| Defect Type Prediction | Not Started | 0/50 | N/A | 50 tasks | Pending |

**Dashboard Features:**
- **Visual Progress Bars:** Show progress toward graduation criteria
- **Trend Charts:** Show metric improvement over time
- **Alert System:** Flag capabilities regressing or stalling
- **Recommendations:** "Design Review Agent FP rate increasing - suggest prompt refinement"

---

### 14.4 Bootstrap Learning as a Continuous Process

**Key Insight:** Bootstrap learning is not a one-time phase. It's a continuous cycle:

```
1. Deploy capability in Learning Mode
2. Collect accuracy data
3. Analyze patterns and failure modes
4. Generate PIP to improve prompts/checklists
5. Human approves PIP
6. Deploy improved version
7. Measure improvement
8. Graduate to Shadow/Autonomous Mode
9. Continue monitoring (monthly recalibration)
10. If performance degrades → Regress to Learning Mode
11. Repeat cycle
```

**Integration with Postmortem Agent:**
The Postmortem Agent (Section VII) should be enhanced to:
- Track bootstrap metrics alongside standard PSP metrics
- Generate PIPs specifically tagged as "Bootstrap Improvements"
- Prioritize bootstrap PIPs (Phase 1-3) to accelerate learning

**Documentation Requirement:**
- Every PIP generated from bootstrap learning MUST document:
  - What data revealed the issue
  - What hypothesis was tested
  - What the expected improvement is
  - How success will be measured

This creates an audit trail of the system's learning process, essential for trust and regulatory compliance.

---

### 14.5 Risk Register Updates for Bootstrap Learning

Add to Section 9:

| Risk | Impact | Probability | Mitigation Strategy |
|------|--------|-------------|---------------------|
| **R15: Premature graduation to autonomous mode** | High | Medium | Enforce strict graduation criteria, require engineering lead approval for mode transitions |
| **R16: Insufficient data variety for learning** | Medium | High | Ensure bootstrap tasks span complexity/type range, reject graduation if dataset too homogeneous |
| **R17: Agent performance drift after graduation** | High | Medium | Monthly recalibration, automatic regression to Shadow Mode if metrics degrade >10% |
| **R18: False confidence from overfitting** | Critical | Low | Use train/test split for validation, require out-of-sample prediction accuracy |

---

## Approval & Sign-Off

| Role | Name | Signature | Date |
|------|------|-----------|------|
| Product Owner | | | |
| Engineering Lead | | | |
| Security Lead | | | |
| DevOps Lead | | | |

---

**Document Version History:**

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2025-11-11 | Claude Code | Initial PRD based on PSPdoc.md |
| 1.1 | 2025-11-11 | Claude Code | Added Section 13: Implementation Considerations (10 concerns, 3 new FRs, 6 new risks) |
| 1.2 | 2025-11-11 | Claude Code | Added Section 14: Bootstrap Learning Framework (5 capabilities, 2 new FRs, 4 new risks). Resolved 5 open questions. |
