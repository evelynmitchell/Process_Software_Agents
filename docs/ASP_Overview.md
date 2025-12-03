# ASP System Overview

**Autonomous Software Process (ASP) Platform**

A multi-agent orchestration system that applies Personal Software Process (PSP) and Team Software Process (TSP) methodology to autonomous AI agents.

---

## Table of Contents

- [What is ASP?](#what-is-asp)
- [Why ASP?](#why-asp)
- [Core Concepts](#core-concepts)
- [The Five Phases](#the-five-phases)
- [Architecture Overview](#architecture-overview)
- [When to Use ASP](#when-to-use-asp)
- [Key Benefits](#key-benefits)

---

## What is ASP?

The **Autonomous Software Process (ASP)** is a disciplined framework that transforms autonomous AI agents from unpredictable "copilots" into measurable, continuously improving development team members.

ASP adapts proven software engineering methodologies (PSP/TSP) for AI agents, providing:

- **Structured Workflow:** 7 specialized agents working in coordinated phases
- **Quality Gates:** Mandatory review phases that prevent defect propagation
- **Telemetry:** Complete observability of agent performance, cost, and quality
- **Self-Improvement:** Agents learn from past performance and propose process changes
- **Bootstrap Learning:** Agents earn autonomy through demonstrated reliability

---

## Why ASP?

### The Problem with Current AI Agents

Traditional AI "copilots" suffer from:

1. **Unpredictable Quality:** No systematic quality control or review process
2. **Compounding Errors:** Early mistakes propagate and amplify through the pipeline
3. **No Observability:** Difficult to measure performance, cost, or improvement
4. **Limited Learning:** No structured feedback loop for continuous improvement
5. **Trust Issues:** Humans hesitant to grant autonomy without reliability metrics

### The ASP Solution

ASP addresses these challenges through:

1. **Quality Gates:** Design Review and Code Review agents catch defects early
2. **Phase-Aware Feedback:** Defects are routed back to their originating phase for correction
3. **Complete Telemetry:** Every agent action is measured (latency, tokens, cost, defects)
4. **Bootstrap Learning:** Agents collect data to prove reliability before earning autonomy
5. **Self-Improvement:** Postmortem Agent analyzes performance and proposes process changes

---

## Core Concepts

### 1. PSP Adaptation for AI Agents

ASP adapts the Personal Software Process (PSP) framework for autonomous agents:

| PSP Concept | ASP Implementation | Purpose |
|-------------|-------------------|---------|
| **Size (LOC)** | Semantic Complexity | Predict effort based on task complexity |
| **Effort (minutes)** | Agent Cost Vector | Measure latency, tokens, API cost |
| **Quality (defects)** | Alignment Deviations | Track AI-specific errors (hallucinations, etc.) |
| **Schedule** | Planned vs. Actual | Improve estimation accuracy over time |

### 2. Agent Cost Vector

Instead of measuring "hours worked," ASP measures three dimensions of agent effort:

```python
@dataclass
class AgentCostVector:
    latency_ms: int        # Time taken
    total_tokens: int      # LLM tokens consumed
    api_cost_usd: float    # Actual cost in USD
```

This enables:
- **Accurate Cost Tracking:** Know exactly what each task costs
- **Optimization:** Identify expensive operations
- **Estimation:** Predict future costs based on complexity

### 3. AI Defect Taxonomy

ASP defines 8 AI-specific defect types (beyond conventional bugs):

1. **Planning Failure** - Incorrect task decomposition or missing steps
2. **Prompt Misinterpretation** - Misunderstood requirements or context
3. **Tool Use Error** - Incorrect API calls or parameter usage
4. **Hallucination** - Generated false information or invented APIs
5. **Security Vulnerability** - Introduced security risks (injection, XSS, etc.)
6. **Conventional Code Bug** - Standard programming errors
7. **Task Execution Error** - Failed to complete requested functionality
8. **Alignment Deviation** - Output doesn't match specification

### 4. Bootstrap Learning Framework

All agent capabilities start in **Learning Mode** and graduate to autonomy:

**Learning Mode → Shadow Mode → Autonomous Mode**

| Mode | Agent Behavior | Human Involvement | Purpose |
|------|---------------|-------------------|---------|
| **Learning** | All outputs validated by human | High (every output) | Collect baseline data |
| **Shadow** | Provides recommendations | Medium (spot checks) | Validate prediction accuracy |
| **Autonomous** | Operates independently | Low (periodic review) | Production operation |

**5 Bootstrap Capabilities:**

1. **PROBE-AI Estimation** (10-20 tasks, MAPE < 20%)
2. **Task Decomposition Quality** (15-30 tasks, <10% correction rate)
3. **Error-Prone Area Detection** (30+ tasks, risk map generation)
4. **Review Agent Effectiveness** (20-40 reviews, TP >80%, FP <20%)
5. **Defect Type Prediction** (50+ tasks, 60% prediction accuracy)

### 5. Quality Gates with Phase-Aware Feedback

ASP implements PSP's core principle: **Fix defects where they were injected**

**Standard Flow (No Issues):**
```
Planning → Design → Design Review (PASS) → Code → Code Review (PASS) → Test → Postmortem
```

**Feedback Flow (Issues Found):**
```
Planning → Design → Design Review (FAIL: planning error detected)
    ↑                      ↓
    └────── Replan ────────┘
             ↓
    Design (with corrected plan) → Design Review (PASS) → Continue...
```

This prevents **compounding errors** - mistakes caught early don't propagate downstream.

---

## The Five Phases

ASP is implemented in five progressive phases, each building on the previous:

### Phase 1: ASP0 - Measurement Foundation (Months 1-2)

**Status:** ✅ COMPLETE

**Goal:** Establish baseline telemetry and data collection infrastructure.

**Deliverables:**
- SQLite database schema (4 tables, 25+ indexes)
- Langfuse Cloud integration for observability
- Telemetry decorators (`@track_agent_cost`, `@log_defect`)
- All 7 core agents with full telemetry
- 740+ tests (unit, integration, E2E)
- Bootstrap data collection infrastructure

**Key Metrics:**
- All agent actions logged to database
- Complete cost tracking (latency, tokens, API cost)
- Artifact traceability (JSON + Markdown)

---

### Phase 2: ASP1 - Estimation (Months 3-4)

**Status:** ⏳ IN PROGRESS

**Goal:** Build PROBE-AI estimation engine using bootstrap data.

**Deliverables:**
- PROBE-AI Agent implementing linear regression
- Estimation model trained on 30+ tasks
- Prediction accuracy validation (±20% MAPE)

**Key Metrics:**
- Mean Absolute Percentage Error (MAPE) < 20%
- Complexity scores calibrated to actual effort
- Estimation improves over time

**Current:** Data collection infrastructure complete, awaiting 30+ tasks for model training.

---

### Phase 3: ASP2 - Gated Review (Months 5-6)

**Status:** ✅ COMPLETE

**Goal:** Implement quality gates to prevent defect propagation.

**Deliverables:**
- Design Review Agent (multi-agent system, 6 specialists)
- Code Review Agent (multi-agent system, 6 specialists)
- Phase yield metrics (% of work passing review)

**Key Metrics:**
- >70% phase yield (work passes review first time)
- Defects caught in originating phase
- Reduced rework in later phases

**6 Design Review Specialists:**
1. Security Review (OWASP Top 10)
2. Performance Review (indexing, caching)
3. Data Integrity Review (FK constraints)
4. Maintainability Review (coupling, cohesion)
5. Architecture Review (design patterns)
6. API Design Review (RESTful principles)

**6 Code Review Specialists:**
1. Code Quality Review (naming, complexity)
2. Security Review (injection, XSS)
3. Performance Review (N+1 queries)
4. Best Practices Review (patterns, idioms)
5. Test Coverage Review (assertions, edge cases)
6. Documentation Review (docstrings, comments)

---

### Phase 4: ASP-TSP - Autonomous Orchestration (Months 7-9)

**Status:** ✅ COMPLETE

**Goal:** Deploy full 7-agent pipeline with HITL approval workflow.

**Deliverables:**
- All 7 specialized agents implemented (Planning, Design, Code, Test, Review, Postmortem)
- TSP Orchestrator Agent coordinating full workflow
- Quality gate enforcement
- **HITL approval workflow** (Local PR-style) ⭐
- ApprovalService integrated with TSP Orchestrator
- E2E validation with HITL completed

**Key Metrics:**
- 50% task completion rate (low-risk tasks)
- Automatic defect routing to originating phase
- Complete artifact traceability
- Human approval required for critical decisions

**7 Specialized Agents:**
1. **Planning Agent** - Task decomposition and estimation
2. **Design Agent** - Architecture and design specifications
3. **Code Agent** - Implementation
4. **Test Agent** - Test generation and defect logging
5. **Design Review Agent** - Design quality gates
6. **Code Review Agent** - Code quality gates
7. **Postmortem Agent** - Performance analysis and PIPs

**HITL Architecture:**
- **Local PR-Style HITL:** Implemented and tested (solo/local work)
- **GitHub Issues HITL:** Planned (team collaboration)
- **CLI-Based HITL:** Planned (interactive sessions)

---

### Phase 5: ASP-Loop - Self-Improvement (Months 10-12)

**Status:** ⏳ PENDING (Postmortem Agent complete, workflow pending)

**Goal:** Enable continuous improvement through automated analysis and human-approved process changes.

**Deliverables:**
- Postmortem Agent (✅ COMPLETE)
- PIP (Process Improvement Proposal) Review Interface
- Prompt versioning and rollout workflow
- Improvement cycle time measurement

**Key Metrics:**
- PIPs generated per 10 tasks
- PIP approval rate (human acceptance)
- Defect rate reduction over time
- Estimation accuracy improvement

**Self-Improvement Loop:**
```
Task Completion
    ↓
Postmortem Analysis (automated)
    ↓
Generate PIPs (LLM-generated defensive changes)
    ↓
Human Review & Approval (HITL)
    ↓
Update Agent Prompts/Checklists
    ↓
Next Task (improved process)
```

---

## Architecture Overview

### High-Level System Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    TSP Orchestrator                          │
│  (Coordinates 7-agent pipeline with HITL approval)           │
└────────────┬────────────────────────────────────────────────┘
             │
             ├──→ Planning Agent ──→ ProjectPlan
             │        ↓ (if review fails)
             │        ↑
             ├──→ Design Agent ──→ DesignSpecification
             │        ↓ (if review fails)
             │        ↑
             ├──→ Design Review Agent ──→ DesignReviewReport
             │        │ (6 specialist agents)
             │        ↓ (PASS/FAIL/NEEDS_IMPROVEMENT)
             │
             ├──→ Code Agent ──→ GeneratedCode
             │        ↓ (if review fails)
             │        ↑
             ├──→ Code Review Agent ──→ CodeReviewReport
             │        │ (6 specialist agents)
             │        ↓ (PASS/FAIL/NEEDS_IMPROVEMENT)
             │
             ├──→ Test Agent ──→ TestResults + DefectLog
             │        │ (4-phase testing)
             │        ↓ (PASS/FAIL/BUILD_FAILED)
             │
             └──→ Postmortem Agent ──→ PerformanceAnalysis + PIPs
                      │ (analyzes all telemetry)
                      ↓
               ┌──────────────────┐
               │  Human Approval  │
               │  (PIP Review)    │
               └──────────────────┘
                      │
                      ↓
               Update Prompts/Checklists
```

### Data Flow

```
Task Request
    ↓
Planning Phase
    ├─→ ProjectPlan artifact (JSON + MD)
    └─→ Telemetry (cost, complexity)
    ↓
Design Phase
    ├─→ DesignSpecification artifact
    └─→ Telemetry (cost, quality)
    ↓
Design Review Phase
    ├─→ DesignReviewReport artifact
    ├─→ Defects logged (if any)
    └─→ Decision: PASS/FAIL/NEEDS_IMPROVEMENT
    ↓ (if FAIL → route back to Planning/Design)
    ↓
Code Phase
    ├─→ GeneratedCode artifact
    └─→ Telemetry (cost, quality)
    ↓
Code Review Phase
    ├─→ CodeReviewReport artifact
    ├─→ Defects logged (if any)
    └─→ Decision: PASS/FAIL/NEEDS_IMPROVEMENT
    ↓ (if FAIL → route back to Code)
    ↓
Test Phase
    ├─→ TestResults artifact
    ├─→ DefectLog (AI Defect Taxonomy)
    └─→ Decision: PASS/FAIL/BUILD_FAILED
    ↓
Postmortem Phase
    ├─→ PerformanceAnalysis artifact
    ├─→ PIPs (Process Improvement Proposals)
    └─→ Telemetry aggregation
    ↓
All artifacts stored in artifacts/<TASK-ID>/
All telemetry stored in database
```

### Storage Architecture

**Artifacts:** `artifacts/<TASK-ID>/`
- `plan.json` / `plan.md` - Planning output
- `design.json` / `design.md` - Design specification
- `design_review.json` / `design_review.md` - Review report
- `generated_code/` - Code artifacts
- `code_review.json` / `code_review.md` - Code review report
- `test_results.json` / `test_results.md` - Test results
- `postmortem.json` / `postmortem.md` - Performance analysis

**Database:** `data/asp_telemetry.db` (SQLite)
- `agent_cost_vector` - Cost tracking (latency, tokens, API cost)
- `defect_log_entry` - Defect tracking (type, severity, phase)
- `task_context` - Task metadata and status
- `bootstrap_learning_state` - Learning mode state tracking

**Observability:** Langfuse Cloud
- Real-time trace visualization
- Agent performance dashboards
- Cost analytics
- Error tracking

**Web UI Dashboard:** `http://localhost:5001`
- **Manager View** (`/manager`) - Agent health, cost tracking, HITL approvals
- **Developer View** (`/developer`) - Task details, code diffs, traceability
- **Product Manager View** (`/product`) - Feature wizard, What-If timeline simulator

---

## When to Use ASP

### ASP is Ideal For:

✅ **Autonomous Agent Development**
- You're building AI agents that need to operate independently
- You need measurable reliability before granting autonomy
- You want continuous improvement over time

✅ **Quality-Critical AI Systems**
- Defects are expensive (financial, security, compliance)
- You need audit trails for regulatory compliance
- You require systematic quality control

✅ **Cost-Conscious AI Development**
- LLM API costs are significant
- You need to optimize token usage
- You want predictable cost estimation

✅ **Team Collaboration with AI**
- Multiple developers working with AI agents
- Need approval workflows (HITL)
- Want shared learning across team

✅ **Research and Experimentation**
- Studying AI agent behavior and reliability
- Collecting training data for agent improvement
- Evaluating different prompt strategies

### ASP is NOT Ideal For:

❌ **Simple One-Off Tasks**
- Quick scripts or prototypes
- No need for quality gates or telemetry
- Traditional copilot is sufficient

❌ **Real-Time Interactive Systems**
- Need sub-second latency
- Multi-phase pipeline adds overhead
- Better suited for direct LLM calls

❌ **Non-Software Tasks**
- ASP is designed for software development
- Other domains may need different frameworks

---

## Key Benefits

### 1. Predictable Quality

- **Quality Gates:** Design Review and Code Review prevent defect propagation
- **Phase-Aware Feedback:** Defects fixed at their source
- **AI Defect Taxonomy:** Track AI-specific errors (hallucinations, tool misuse)

**Result:** Higher first-time quality, less rework

### 2. Complete Observability

- **Cost Tracking:** Know exactly what each task costs (latency, tokens, USD)
- **Artifact Traceability:** Complete audit trail from task to code
- **Defect Analytics:** Understand where and why defects occur

**Result:** Data-driven optimization and compliance

### 3. Continuous Improvement

- **Bootstrap Learning:** Agents learn from historical data
- **PROBE-AI Estimation:** Prediction accuracy improves over time
- **PIP Workflow:** Systematic process improvement

**Result:** Agents get better with use

### 4. Earned Autonomy

- **Learning Mode:** All outputs validated (collect baseline data)
- **Shadow Mode:** Predictions compared to actuals
- **Autonomous Mode:** Operate independently with proven reliability

**Result:** Trust through demonstrated performance

### 5. Cost Optimization

- **Effort Estimation:** Predict costs before starting
- **Complexity Analysis:** Identify expensive operations
- **Telemetry-Driven Optimization:** Focus on high-cost areas

**Result:** Predictable and optimized LLM spend

### 6. Human-In-The-Loop (HITL)

- **Approval Workflows:** Critical decisions require human approval
- **Flexible HITL Modes:** Local PR, GitHub Issues, CLI-based
- **Audit Trails:** Complete record of human decisions

**Result:** Safe autonomy with human oversight

---

## Next Steps

Ready to get started with ASP?

1. **[Getting Started Guide](Getting_Started.md)** - Installation and first task
2. **[HITL Integration Guide](HITL_Integration.md)** - Configure approval workflows
3. **[Agent Reference](Agents_Reference.md)** - Deep dive into each agent
4. **[Developer Guide](Developer_Guide.md)** - Extend and customize ASP
5. **[API Reference](API_Reference.md)** - Core models and utilities

---

## Summary

**ASP transforms autonomous AI agents from unpredictable copilots into disciplined, measurable, continuously improving development team members.**

Key differentiators:
- ✅ **7 specialized agents** working in coordinated phases
- ✅ **Quality gates** that prevent defect propagation
- ✅ **Complete telemetry** for cost, performance, and quality
- ✅ **Bootstrap learning** that earns autonomy through demonstrated reliability
- ✅ **Self-improvement** through Postmortem analysis and PIPs
- ✅ **HITL approval workflows** for safe autonomy

ASP is production-ready for autonomous software development with built-in quality control, cost optimization, and continuous improvement.

---

**Built with ASP Platform v1.0**

*Autonomy is earned through demonstrated reliability, not assumed.*
