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

# Check database
sqlite3 data/asp_telemetry.db ".tables"
```

---

## Project Structure

```
Process_Software_Agents/
├── src/asp/                    # Main application package
│   ├── agents/                 # 7 specialized agent implementations
│   ├── orchestrator/           # TSP Orchestrator (control plane)
│   ├── telemetry/              # Observability and logging
│   ├── models/                 # Data models (Pydantic/SQLAlchemy)
│   ├── prompts/                # Agent prompt templates (versioned)
│   └── utils/                  # Utility functions
├── tests/                      # Test suite (unit, integration, e2e)
├── database/                   # SQL migrations and schemas
├── docs/                       # Documentation
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

### 3. Quality Gates

Mandatory review phases prevent defects from propagating:

```
Planning → Design → Design Review (GATE) → Code → Code Review (GATE) → Test → Postmortem
```

If a review fails, the orchestrator halts and loops back to the originating agent with defect details.

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
- Bootstrap data collection (12 planning tasks)

### Implemented Agents (3/7 Complete)

| Agent | Status | Tests | Docs | Bootstrap Data |
|-------|--------|-------|------|----------------|
| **Planning Agent** | Complete | 102/102 unit, 8/8 E2E | ADR, Examples | 12 tasks |
| **Design Agent** | Complete | 23/23 unit, 5/5 E2E | ADR, Examples | Partial |
| **Design Review Agent** | Complete | 21/21 unit, 3/3 E2E | ADR, User Guide | Partial |
| Code Agent | Next | - | - | - |
| Code Review Agent | Pending | - | - | - |
| Test Agent | Pending | - | - | - |
| Integration Agent | Pending | - | - | - |

### Design Review Agent (NEW!)

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

### Product & Architecture
- [PRD.md](PRD.md) - Product Requirements Document
- [PSPdoc.md](PSPdoc.md) - ASP Framework Source Document
- [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md) - Directory Organization

### Architecture Decisions
- [docs/data_storage_decision.md](docs/data_storage_decision.md) - SQLite vs PostgreSQL (with database file location)
- [docs/secrets_management_decision.md](docs/secrets_management_decision.md) - GitHub Codespaces Secrets strategy
- [docs/planning_agent_architecture_decision.md](docs/planning_agent_architecture_decision.md) - Planning Agent design
- [docs/design_agent_architecture_decision.md](docs/design_agent_architecture_decision.md) - Design Agent design
- [docs/design_review_agent_architecture_decision.md](docs/design_review_agent_architecture_decision.md) - Design Review multi-agent architecture

### Agent User Guides
- [docs/design_review_agent_user_guide.md](docs/design_review_agent_user_guide.md) - **NEW!** Complete guide for Design Review Agent (usage, examples, API reference, troubleshooting)

### Technical Specifications
- [docs/database_schema_specification.md](docs/database_schema_specification.md) - Database Design
- [docs/observability_platform_evaluation.md](docs/observability_platform_evaluation.md) - Platform Selection
- [database/README.md](database/README.md) - Database Setup Guide (SQLite & PostgreSQL)

### Testing Documentation
- [docs/test_coverage_analysis.md](docs/test_coverage_analysis.md) - Comprehensive test coverage analysis and gap identification
- [docs/test_implementation_plan.md](docs/test_implementation_plan.md) - Detailed 3-4 week implementation roadmap for test coverage

### Development Guidelines
- [Claude.md](Claude.md) - Guidelines for Claude Code
- [.env.example](.env.example) - Environment Variables Reference
- [Summary/](Summary/) - Daily Work Logs

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
| **Orchestration** | Custom (TSP-based) | Multi-agent workflow control |
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
# All tests
uv run pytest

# With coverage
uv run pytest --cov --cov-report=html

# Specific markers
uv run pytest -m unit
uv run pytest -m integration
uv run pytest -m bootstrap
```

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

### Phase 1: ASP0 - Measurement (Months 1-2) [In Progress]
- [x] Database schema design (SQLite with PostgreSQL migration path)
- [x] Observability platform selection (Langfuse)
- [x] Project structure setup (uv, 119 dependencies)
- [x] Secrets management strategy (GitHub Codespaces Secrets)
- [x] SQLite database implementation (4 tables, 25+ indexes)
- [ ] Deploy telemetry infrastructure (decorators, instrumentation)
- [ ] Implement Planning Agent with telemetry
- [ ] Collect baseline data (30+ tasks)

### Phase 2: ASP1 - Estimation (Months 3-4)
- [ ] Implement Planning Agent
- [ ] Build PROBE-AI linear regression
- [ ] Validate estimation accuracy (±20%)

### Phase 3: ASP2 - Gated Review (Months 5-6)
- [ ] Implement Design Review Agent
- [ ] Implement Code Review Agent
- [ ] Achieve >70% phase yield

### Phase 4: ASP-TSP - Orchestration (Months 7-9)
- [ ] Deploy all 7 agents
- [ ] Build TSP Orchestrator
- [ ] 50% task completion rate (low-risk tasks)

### Phase 5: ASP-Loop - Self-Improvement (Months 10-12)
- [ ] Implement Postmortem Agent
- [ ] Enable PIP workflow
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
