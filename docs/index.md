# Agentic Software Process (ASP) Platform

A multi-agent orchestration system that applies Personal Software Process (PSP) and Team Software Process (TSP) methodology to autonomous AI agents, enabling disciplined development with built-in quality gates, automated telemetry, and self-improvement capabilities.

---

## Overview

The ASP Platform transforms autonomous AI agents from unpredictable "copilots" into disciplined, measurable, and continuously improving development team members through:

- **7 Specialized Agents:** Planning, Design, Design Review, Coding, Code Review, Test, Postmortem
- **Mandatory Quality Gates:** Formal review phases prevent "compounding errors"
- **PROBE-AI Estimation:** Linear regression-based effort estimation using historical data
- **Bootstrap Learning:** Agents earn autonomy through demonstrated reliability
- **Full Observability:** Complete telemetry of agent performance, cost, and quality metrics

---

## 🚀 Quick Example

```python
from asp.orchestrators import TSPOrchestrator
from asp.models.planning import TaskRequirements

# Create task
task = TaskRequirements(
    task_id="EXAMPLE-001",
    description="Create a Python function that validates email addresses",
    requirements=[
        "Function accepts email string",
        "Returns True for valid emails, False otherwise",
        "Use regex for validation",
        "Include comprehensive tests"
    ]
)

# Run through ASP pipeline (7 agents)
orchestrator = TSPOrchestrator()
result = orchestrator.execute(task)

print(f"✅ Task complete! Cost: ${result.total_cost_usd:.4f}")
print(f"📁 Artifacts: artifacts/{task.task_id}/")
```

**More examples:** See [examples/](examples/) directory

---

## Quick Start

### Option 1: GitHub Codespaces (Recommended)

**Perfect for zero-setup development in the cloud.**

#### 1. Create Codespace

Click the "Code" button on GitHub → "Codespaces" → "Create codespace on main"

#### 2. Configure Secrets (One-Time Setup)

Add the following secrets to [Repository Settings → Codespaces Secrets](https://github.com/evelynmitchell/Process_Software_Agents/settings/secrets/codespaces):

| Secret Name | Where to Get It | Required |
|-------------|----------------|----------|
| `LANGFUSE_PUBLIC_KEY` | [Langfuse Dashboard](https://cloud.langfuse.com) → Settings → API Keys | Yes |
| `LANGFUSE_SECRET_KEY` | [Langfuse Dashboard](https://cloud.langfuse.com) → Settings → API Keys | Yes |
| `LANGFUSE_HOST` | Set to: `https://cloud.langfuse.com` | Yes |
| `ANTHROPIC_API_KEY` | [Anthropic Console](https://console.anthropic.com) → API Keys | Yes |

After adding secrets, **restart your Codespace** for them to take effect.

#### 3. Verify Setup

```bash
# Check secrets are loaded
echo $LANGFUSE_PUBLIC_KEY  # Should show pk-lf-...
echo $ANTHROPIC_API_KEY    # Should show sk-ant-...

# Install dependencies (if not already done)
uv sync --all-extras

# Initialize database
uv run python scripts/init_database.py --with-sample-data

# Run tests
uv run pytest
```

**You're ready to develop!** All dependencies, database, and secrets are configured.

---

### Option 2: Local Development

**For development on your local machine.**

#### Prerequisites

- Python 3.12+
- [uv](https://github.com/astral-sh/uv) package manager

#### Installation

```bash
# 1. Clone the repository
git clone https://github.com/evelynmitchell/Process_Software_Agents.git
cd Process_Software_Agents

# 2. Install dependencies
uv sync --all-extras

# 3. Configure environment (copy and uncomment variables)
cp .env.example .env
# Edit .env with your API keys:
#   LANGFUSE_PUBLIC_KEY=pk-lf-your-key
#   LANGFUSE_SECRET_KEY=sk-lf-your-key
#   LANGFUSE_HOST=https://cloud.langfuse.com
#   ANTHROPIC_API_KEY=sk-ant-your-key

# 4. Initialize database
uv run python scripts/init_database.py --with-sample-data

# 5. Run tests
uv run pytest
```

---

### Quick Verification

```bash
# Run all tests
uv run pytest

# Run specific test categories
uv run pytest -m unit          # Fast unit tests only
uv run pytest -m integration   # Integration tests
uv run pytest --cov            # With coverage report

# Verify orchestrator
uv run python -c "from asp.orchestrators import PlanningDesignOrchestrator; print('✓ Orchestrator ready')"

# Inspect artifacts
ls -la artifacts/              # List all task artifacts
cat artifacts/BOOTSTRAP-001/plan.md  # View a planning artifact

# Check database and telemetry
sqlite3 data/asp_telemetry.db ".tables"
sqlite3 data/asp_telemetry.db "SELECT COUNT(*) FROM agent_cost_vector;"
```

---

## Project Structure

```
Process_Software_Agents/
├── src/asp/                    # Main application package
│   ├── agents/                 # 7 specialized agent implementations
│   ├── orchestrators/          # Pipeline orchestrators with phase-aware feedback
│   │   ├── planning_design_orchestrator.py  # Planning-Design-Review coordination
│   │   └── types.py            # PlanningDesignResult and shared types
│   ├── telemetry/              # Observability and logging
│   ├── models/                 # Data models (Pydantic/SQLAlchemy)
│   ├── prompts/                # Agent prompt templates (versioned)
│   └── utils/                  # Utility functions
├── artifacts/                  # Agent output artifacts (task-specific)
│   ├── BOOTSTRAP-001/          # Bootstrap task artifacts
│   ├── HW-001/                 # Hello World task artifacts
│   └── .../                    # 12+ task directories with plans, designs, code
├── tests/                      # Test suite (unit, integration, e2e)
├── database/                   # SQL migrations and schemas
├── docs/                       # Documentation (ADRs, user guides, specs)
├── config/                     # Configuration files
└── scripts/                    # Utility scripts
```

See [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md) for detailed documentation.

---

## Core Concepts

### 1. PSP Adaptation for AI Agents

The ASP Platform adapts the Personal Software Process (PSP) for autonomous agents:

| PSP Concept | ASP Implementation |
|-------------|-------------------|
| **Size (LOC)** | Semantic Complexity (weighted score) |
| **Effort (minutes)** | Agent Cost Vector (latency, tokens, API cost) |
| **Quality (defects)** | Alignment Deviations (AI-specific taxonomy) |
| **Schedule** | Planned vs. Actual Cost Vector |

### 2. Bootstrap Learning Framework

All agent capabilities start in "Learning Mode" and graduate to autonomy based on demonstrated accuracy:

- **Learning Mode:** Human validates all outputs, system collects data
- **Shadow Mode:** Agent provides recommendations, predictions compared to actuals
- **Autonomous Mode:** Agent operates independently with periodic recalibration

**5 Bootstrap Capabilities:**
1. **PROBE-AI Estimation** (10-20 tasks, MAPE < 20%)
2. **Task Decomposition Quality** (15-30 tasks, <10% correction rate)
3. **Error-Prone Area Detection** (30+ tasks, risk map generation)
4. **Review Agent Effectiveness** (20-40 reviews, TP >80%, FP <20%)
5. **Defect Type Prediction** (50+ tasks, 60% prediction accuracy)

### 3. Orchestrator Infrastructure

The ASP Platform uses specialized orchestrators to coordinate multi-agent workflows with automatic error correction:

#### PlanningDesignOrchestrator

Coordinates Planning → Design → Design Review with phase-aware feedback loops that route defects back to their originating phase.

**Phase-Aware Routing:**
- **Planning-phase issues** → Routes back to Planning Agent for replanning
- **Design-phase issues** → Routes back to Design Agent for redesign
- **Multi-phase issues** → Triggers both replanning and redesign

**Error Correction Flow:**
```
Planning → Design → Design Review (finds planning error)
    ↑                      ↓
    └───── REPLAN ─────────┘  (fixes error at source)
```

**Key Features:**
- Automatic defect routing to originating phase (implements PSP principle: fix defects where injected)
- Iteration limits prevent infinite loops (max 3 per phase, 10 total)
- Complete telemetry for bootstrap learning and PROBE-AI
- Returns complete artifact set: `PlanningDesignResult(plan, design, review)`

**Cost Impact:** 20-50% increase for tasks requiring corrections, offset by preventing downstream defects and rework.

**Architecture:** See [docs/error_correction_feedback_loops_decision.md](docs/error_correction_feedback_loops_decision.md) for design rationale and [docs/artifact_traceability_decision.md](docs/artifact_traceability_decision.md) for artifact flow details.

#### Artifact Flow and Traceability

The orchestrator ensures complete artifact traceability through the pipeline for bootstrap learning and PROBE-AI:

**Artifact Flow:**
```
PlanningDesignOrchestrator.execute()
    ↓
Returns: PlanningDesignResult
    ├─ ProjectPlan         → Used by Postmortem Agent for effort analysis
    ├─ DesignSpecification → Used by Code Agent for implementation
    └─ DesignReviewReport  → Quality metrics for bootstrap learning
```

**Benefits:**
- **Traceability:** Every artifact links back to its source task and phase
- **PROBE-AI Learning:** Planned vs. actual metrics enable effort estimation
- **Quality Analysis:** Complete audit trail from requirements to code
- **No Data Duplication:** Single source of truth for each artifact

All artifacts are persisted to `artifacts/<TASK-ID>/` with both JSON (machine-readable) and Markdown (human-readable) formats.

### 4. Quality Gates with Phase-Aware Feedback

Review phases prevent defect propagation and route issues back to their originating phase:

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

**Review Agent Actions:**
- **PASS:** Proceed to next phase
- **NEEDS_IMPROVEMENT:** Log issues, proceed (no critical/high severity defects)
- **FAIL:** Route back to appropriate phase (Planning or Design) with detailed defect information

This implements the PSP principle: **fix defects in the phase where they were injected**, preventing error compounding through the pipeline.

---

## Implementation Status

### Phase 1: Measurement Foundation **COMPLETE**

**Goal:** Establish baseline telemetry and bootstrap learning data collection.

**Completed:**
- SQLite database schema (4 tables, 25+ indexes)
- Langfuse Cloud integration
- Telemetry decorators (`@track_agent_cost`, `@log_defect`)
- Pydantic data models for all agents
- Planning Agent with full telemetry
- Design Agent with full telemetry
- Design Review Agent (multi-agent system)
- Code Agent with full telemetry
- Code Review Agent (multi-agent system)
- Test Agent with AI Defect Taxonomy
- Bootstrap data collection (12 planning tasks)

### Implemented Agents (7/7 Complete) ✅

| Agent | Status | Tests | Docs | Bootstrap Data |
|-------|--------|-------|------|----------------|
| **Planning Agent** | ✅ Complete | 102/102 unit, 8/8 E2E | ADR, Examples | 12 tasks |
| **Design Agent** | ✅ Complete | 23/23 unit, 5/5 E2E | ADR, Examples | Partial |
| **Design Review Agent** | ✅ Complete | 21/21 unit, 3/3 E2E | ADR, User Guide | Partial |
| **Code Agent** | ✅ Complete | Unit tests | - | - |
| **Code Review Agent** | ✅ Complete | Unit tests | - | - |
| **Test Agent** | ✅ Complete | Unit tests | - | - |
| **Postmortem Agent** | ✅ Complete | Unit tests | Work Summary | - |

**All 21 agents are now implemented:**
- **7 Core Agents:** Planning, Design, Design Review, Code, Code Review, Test, Postmortem
- **2 Multi-Agent Review Orchestrators:** Design Review Orchestrator, Code Review Orchestrator
- **12 Specialist Review Agents:** 6 design specialists (Security, Performance, Data Integrity, Maintainability, Architecture, API Design) + 6 code review specialists (Code Quality, Security, Performance, Best Practices, Test Coverage, Documentation)

**Plus 1 Pipeline Orchestrator:** PlanningDesignOrchestrator (phase-aware feedback loops)

### Recently Completed

#### Comprehensive Test Plan for All 21 Agents (NEW!)

A **production-ready testing framework** covering all agents in the ASP Platform:

**Test Coverage:**
- **7 Core Agents** - Planning, Design, Design Review, Code, Code Review, Test, Postmortem
- **2 Orchestrator Agents** - Design Review and Code Review orchestrators
- **12 Specialist Review Agents** - 6 design + 6 code review specialists

**Test Execution:**
- **200+ tests** across all agents
- **Incremental execution** - Phase-by-phase testing for faster feedback
- **Performance benchmarks** - Latency and cost validation
- **Integration tests** - End-to-end workflow validation

**Easy Execution:**
```bash
python scripts/run_agent_tests.py incremental  # Run all tests
python scripts/run_agent_tests.py coverage     # With coverage report
```

**[Read the Quick Start Guide](docs/test_plan_quick_start.md)** for complete testing instructions.

#### Postmortem Agent (COMPLETE!)

The Postmortem Agent is a **meta-agent for performance analysis and self-improvement** that completes the 7-agent PSP/TSP workflow:

**Core Capabilities:**
- **Performance Analysis** - Planned vs. actual metrics (latency, tokens, cost, complexity)
- **Quality Metrics** - Defect density, phase distribution, phase yield
- **Root Cause Analysis** - Top defect types by fix effort
- **Process Improvement Proposals (PIPs)** - LLM-generated process changes for HITL approval

**Self-Improvement Loop:**
1. Analyze completed task performance
2. Identify top defect patterns
3. Generate defensive process changes
4. Submit PIPs for human approval
5. Update agent prompts/checklists after approval

This completes the foundation for **Phase 5: ASP-Loop Self-Improvement**.

#### Test Agent (COMPLETE!)

The Test Agent is a **production-ready testing system** that validates generated code through comprehensive testing and defect logging:

**4-Phase Testing Process:**
- **Build Validation** - Verify compilation, imports, dependencies
- **Test Generation** - Create comprehensive unit tests from design specs
- **Test Execution** - Run tests and calculate coverage metrics
- **Defect Logging** - Classify defects using AI Defect Taxonomy (8 types)

**AI Defect Taxonomy:**
- Planning Failure, Prompt Misinterpretation, Tool Use Error
- Hallucination, Security Vulnerability, Conventional Code Bug
- Task Execution Error, Alignment Deviation

**Quality Gates:** PASS / FAIL / BUILD_FAILED
**Severity Levels:** Critical, High, Medium, Low
**Phase-Aware Tracking:** Links defects to Planning/Design/Code phases

#### Design Review Agent

The Design Review Agent is a **production-ready multi-agent system** that performs comprehensive design quality reviews across 6 specialized dimensions:

**6 Specialist Agents:**
- **SecurityReviewAgent** - OWASP Top 10, authentication, encryption, injection prevention
- **PerformanceReviewAgent** - Indexing, caching, N+1 queries, scalability
- **DataIntegrityReviewAgent** - FK constraints, referential integrity, transactions
- **MaintainabilityReviewAgent** - Coupling, cohesion, separation of concerns
- **ArchitectureReviewAgent** - Design patterns, layering, SOLID principles
- **APIDesignReviewAgent** - RESTful design, error handling, versioning

**Performance:** 25-40 seconds per review (parallel execution)
**Cost:** ~$0.15-0.25 per review
**Test Coverage:** 24/24 tests passing (100%)

**[Read the Full User Guide](docs/design_review_agent_user_guide.md)** for usage examples, API reference, and troubleshooting.

---

## Documentation

### 🚀 Getting Started (Start Here!)
- **[ASP Overview](docs/ASP_Overview.md)** - What is ASP? Core concepts and benefits
- **[Getting Started Guide](docs/Getting_Started.md)** - Installation, configuration, and first task
- **[Examples](examples/)** - Runnable code examples demonstrating key features

### 📚 User Guides
- **[HITL Integration Guide](docs/HITL_Integration.md)** - Human-In-The-Loop approval workflows
- **[Agent Reference](docs/Agents_Reference.md)** - Complete reference for all 7 agents
- **[API Reference](docs/API_Reference.md)** - Python API documentation
- **[Planning Agent Guide](docs/planning_agent_user_guide.md)** - Task decomposition and complexity scoring
- **[Coding Agent Guide](docs/coding_agent_user_guide.md)** - Code generation and file management
- **[Test Agent Guide](docs/test_agent_user_guide.md)** - Test generation and defect logging
- **[Postmortem Agent Guide](docs/postmortem_agent_user_guide.md)** - Process improvement and RCA
- **[Web UI Guide](docs/web_ui_user_guide.md)** - Dashboard usage for Manager/Developer/Product
- [design_review_agent_user_guide.md](docs/design_review_agent_user_guide.md) - Design Review Agent deep dive
- [artifact_persistence_user_guide.md](docs/artifact_persistence_user_guide.md) - Artifact system usage
- [telemetry_user_guide.md](docs/telemetry_user_guide.md) - Telemetry and observability

### 👨‍💻 Developer Documentation
- **[Developer Guide](docs/Developer_Guide.md)** - Extending, customizing, and contributing
- **[Utils Reference](docs/utils_reference.md)** - Shared utilities reference
- **[Prompt Engineering Guide](docs/prompt_engineering_guide.md)** - Prompt versioning and standards
- **[Specialist Agent Guide](docs/specialist_agent_dev_guide.md)** - Creating new specialist agents
- **[Orchestrator Internals](docs/orchestrator_internals_guide.md)** - State machine and logic guide
- [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md) - Directory organization
- [Claude.md](Claude.md) - Development guidelines
- [.env.example](.env.example) - Environment variables reference

### 📋 Product & Architecture
- [PRD.md](PRD.md) - Product Requirements Document
- [PSPdoc.md](PSPdoc.md) - ASP Framework Source Document

### 🏗️ Architecture Decisions (ADRs)
- [data_storage_decision.md](docs/data_storage_decision.md) - SQLite vs PostgreSQL
- [secrets_management_decision.md](docs/secrets_management_decision.md) - GitHub Codespaces Secrets
- [planning_agent_architecture_decision.md](docs/planning_agent_architecture_decision.md) - Planning Agent design
- [design_agent_architecture_decision.md](docs/design_agent_architecture_decision.md) - Design Agent design
- [design_review_agent_architecture_decision.md](docs/design_review_agent_architecture_decision.md) - Multi-agent review architecture
- [error_correction_feedback_loops_decision.md](docs/error_correction_feedback_loops_decision.md) - Phase-aware feedback
- [artifact_traceability_decision.md](docs/artifact_traceability_decision.md) - Artifact flow
- [artifact_persistence_version_control_decision.md](docs/artifact_persistence_version_control_decision.md) - Artifact storage
- [phase_aware_feedback_revision_plan.md](docs/phase_aware_feedback_revision_plan.md) - Feedback implementation
- [complexity_calibration_decision.md](docs/complexity_calibration_decision.md) - Semantic complexity
- [bootstrap_data_collection_decision.md](docs/bootstrap_data_collection_decision.md) - Bootstrap learning

### 🧪 Testing Documentation
- [comprehensive_agent_test_plan.md](docs/comprehensive_agent_test_plan.md) - Complete test plan for all 21 agents
- [test_gap_analysis_and_recommendations.md](docs/test_gap_analysis_and_recommendations.md) - Test gap analysis
- [test_plan_quick_start.md](docs/test_plan_quick_start.md) - Testing quick reference
- [test_coverage_analysis.md](docs/test_coverage_analysis.md) - Coverage analysis
- [test_implementation_plan.md](docs/test_implementation_plan.md) - Test implementation roadmap
- [run_agent_tests.py](scripts/run_agent_tests.py) - Python test runner
- [run_agent_tests.sh](scripts/run_agent_tests.sh) - Bash test runner

### 🔧 Technical Specifications
- [database_schema_specification.md](docs/database_schema_specification.md) - Database design
- [observability_platform_evaluation.md](docs/observability_platform_evaluation.md) - Platform selection
- [database/README.md](database/README.md) - Database setup guide

### 📝 Development Logs
- [Summary/](Summary/) - Daily work logs and session summaries

---

## Technology Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **Language** | Python 3.12+ | Core implementation |
| **Package Manager** | uv | Fast, Rust-based dependency management |
| **Development Env** | GitHub Codespaces | Cloud-based development |
| **Secrets Management** | GitHub Codespaces Secrets | Secure API key storage |
| **LLM Providers** | Anthropic (Claude), OpenAI | Multi-provider support |
| **Observability** | Langfuse (Cloud/Self-hosted) | Agent tracing and telemetry |
| **Database (Phase 1-3)** | SQLite | Local file-based storage |
| **Database (Phase 4+)** | PostgreSQL + TimescaleDB | Production time-series storage |
| **Orchestration** | Custom (Phase-aware feedback) | Multi-agent workflow with error correction |
| **Testing** | pytest | Unit, integration, e2e tests |
| **Linting/Formatting** | ruff | Fast Python linter and formatter |
| **Type Checking** | mypy | Static type analysis |

---

## Development Workflow

### 1. Install Development Tools

```bash
uv sync --all-extras
```

### 2. Run Pre-Commit Hooks (Optional)

```bash
uv run pre-commit install
uv run pre-commit run --all-files
```

### 3. Format and Lint

```bash
# Format code
uv run ruff format .

# Run linter
uv run ruff check --fix .

# Type check
uv run mypy src/
```

### 4. Run Tests

```bash
# Option 1: Use the comprehensive test runner (recommended)
python scripts/run_agent_tests.py incremental  # Run all tests phase by phase
python scripts/run_agent_tests.py coverage     # Run with coverage report
python scripts/run_agent_tests.py core         # Test only core agents

# Option 2: Direct pytest commands
uv run pytest                                   # All tests
uv run pytest --cov --cov-report=html          # With coverage
uv run pytest -m unit                          # Unit tests only
uv run pytest -m integration                   # Integration tests only
uv run pytest -m bootstrap                     # Bootstrap tests only
```

See [docs/test_plan_quick_start.md](docs/test_plan_quick_start.md) for complete testing guide.

### 5. Create Feature Branch

```bash
git checkout -b feature/my-feature
# Make changes
git add .
git commit -m "Add feature: description"
git push origin feature/my-feature
```

---

## Contributing

We follow a structured development process (inspired by PSP!):

1. **Problem Analysis:** Understand requirements and examples
2. **Design:** Create function signatures and stubs
3. **Examples:** Write test cases before implementation
4. **Implementation:** Fill in the function body
5. **Testing:** Validate with tests
6. **Review:** Get code reviewed before merge

See [Claude.md](Claude.md) for detailed guidelines.

---

## Roadmap

### Phase 1: ASP0 - Measurement (Months 1-2) **87.5% Complete**
- [x] Database schema design (SQLite with PostgreSQL migration path)
- [x] Observability platform selection (Langfuse)
- [x] Project structure setup (uv, 119 dependencies)
- [x] Secrets management strategy (GitHub Codespaces Secrets)
- [x] SQLite database implementation (4 tables, 25+ indexes)
- [x] Deploy telemetry infrastructure (decorators, instrumentation)
- [x] Implement Planning Agent with telemetry (102 unit tests, 8 E2E tests)
- [ ] Collect baseline data (30+ tasks) - **In Progress: 12+ tasks collected**

### Phase 2: ASP1 - Estimation (Months 3-4)
- [ ] Build PROBE-AI linear regression (requires 30+ tasks)
- [ ] Validate estimation accuracy (±20%)

### Phase 3: ASP2 - Gated Review (Months 5-6) **66% Complete**
- [x] Implement Design Review Agent (multi-agent system, 24/24 tests passing)
- [x] Implement Code Review Agent (multi-agent system)
- [ ] Achieve >70% phase yield (measuring with bootstrap data)

### Phase 4: ASP-TSP - Orchestration (Months 7-9) **Started**
- [x] Deploy all 7 agents (Planning, Design, Design Review, Code, Code Review, Test, Postmortem)
- [ ] Build TSP Orchestrator - **Partial: PlanningDesignOrchestrator complete with phase-aware feedback**
- [ ] 50% task completion rate (low-risk tasks)

### Phase 5: ASP-Loop - Self-Improvement (Months 10-12) **33% Complete**
- [x] Implement Postmortem Agent (performance analysis, quality metrics, root cause analysis)
- [ ] Enable PIP workflow (Process Improvement Proposals with HITL approval)
- [ ] Continuous improvement cycle operational

---

## Key Features

### Delivered (Phase 1 Infrastructure)
- **Database:** SQLite schema (4 tables, 25+ indexes) with PostgreSQL migration path
- **Secrets Management:** GitHub Codespaces Secrets integration
- **Database Tooling:** Python CLI for one-command database initialization
- **Data Organization:** Structured `data/` directory for runtime files
- **Project Structure:** uv package management with 119 dependencies
- **Documentation:** PRD v1.2 with 24 FRs, Bootstrap Learning Framework, 2 architecture decisions
- **Development Environment:** GitHub Codespaces with zero-setup workflow

### In Progress (Phase 1)
- Telemetry decorators (`@track_agent_cost`, `@log_defect`)
- Python data models (SQLAlchemy/Pydantic)
- Planning Agent implementation with telemetry
- Langfuse API integration

### Planned (Phase 2-5)
- Full 7-agent orchestration (Planning, Design, Code, Review, Test, Postmortem)
- PROBE-AI estimation engine (linear regression)
- Bootstrap dashboard (FR-23, FR-24)
- Quality gates (Design Review, Code Review)
- Self-improvement PIP workflow

---

## License

MIT License - See [LICENSE](LICENSE) for details.

---

## Acknowledgments

- **PSP/TSP Framework:** Watts Humphrey, Software Engineering Institute (SEI), Carnegie Mellon University
- **Agentic AI Research:** Informed by recent research on specification-first AI development and agent observability

---

## Contact

- **Repository:** [github.com/evelynmitchell/Process_Software_Agents](https://github.com/evelynmitchell/Process_Software_Agents)
- **Issues:** [github.com/evelynmitchell/Process_Software_Agents/issues](https://github.com/evelynmitchell/Process_Software_Agents/issues)

---

**Built with Claude Code**

*Autonomy is earned through demonstrated reliability, not assumed.*
