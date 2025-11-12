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

### Prerequisites

- Python 3.12+
- [uv](https://github.com/astral-sh/uv) package manager
- PostgreSQL 14+ (optional: TimescaleDB for production)

### Installation

```bash
# 1. Clone the repository
git clone https://github.com/evelynmitchell/Process_Software_Agents.git
cd Process_Software_Agents

# 2. Install dependencies
uv sync --all-extras

# 3. Activate virtual environment
source .venv/bin/activate  # On macOS/Linux
# or
.venv\Scripts\activate  # On Windows

# 4. Set up database (optional)
psql -c "CREATE DATABASE asp_telemetry;"
psql asp_telemetry < database/migrations/001_create_tables.sql
psql asp_telemetry < database/migrations/002_create_indexes.sql

# 5. Configure environment
cp .env.example .env
# Edit .env with your API keys and database connection
```

### Run Tests

```bash
# Run all tests
uv run pytest

# Run specific test categories
uv run pytest -m unit          # Fast unit tests only
uv run pytest -m integration   # Integration tests
uv run pytest --cov            # With coverage report
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

## Phase 1: Measurement Foundation (Current)

**Goal:** Establish baseline telemetry and bootstrap learning data collection.

**Status:** ✅ Complete (infrastructure setup)

**Next Steps:**
- [ ] Deploy database (PostgreSQL/TimescaleDB)
- [ ] Set up Langfuse Cloud account
- [ ] Implement Planning Agent stub
- [ ] Build telemetry instrumentation decorators
- [ ] Run first 10 tasks to collect bootstrap data

---

## Documentation

### Product & Architecture
- [PRD.md](PRD.md) - Product Requirements Document
- [PSPdoc.md](PSPdoc.md) - ASP Framework Source Document
- [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md) - Directory Organization

### Technical Specifications
- [docs/database_schema_specification.md](docs/database_schema_specification.md) - Database Design
- [docs/observability_platform_evaluation.md](docs/observability_platform_evaluation.md) - Platform Selection
- [database/README.md](database/README.md) - Database Setup Guide

### Development Guidelines
- [Claude.md](Claude.md) - Guidelines for Claude Code
- [Summary/](Summary/) - Daily Work Logs

---

## Technology Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **Language** | Python 3.12+ | Core implementation |
| **Package Manager** | uv | Fast, Rust-based dependency management |
| **LLM Providers** | Anthropic (Claude), OpenAI | Multi-provider support |
| **Observability** | Langfuse (self-hosted) | Agent tracing and telemetry |
| **Database** | PostgreSQL + TimescaleDB | Time-series telemetry storage |
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

### Phase 1: ASP0 - Measurement (Months 1-2) ✅
- [x] Database schema design
- [x] Observability platform selection (Langfuse)
- [x] Project structure setup
- [ ] Deploy telemetry infrastructure
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

### ✅ Delivered
- Comprehensive database schema (4 tables, 25+ indexes)
- SQL migration scripts with TimescaleDB optimization
- Project structure with uv package management
- PRD with 24 functional requirements and 5-phase roadmap
- Bootstrap Learning Framework (Section 14)

### 🚧 In Progress (Phase 1)
- Telemetry infrastructure deployment
- Planning Agent implementation
- Langfuse integration

### 📋 Planned
- Full multi-agent orchestration
- PROBE-AI estimation engine
- Bootstrap dashboard (FR-23, FR-24)
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

**Built with Claude Code** 🤖

*Autonomy is earned through demonstrated reliability, not assumed.*
