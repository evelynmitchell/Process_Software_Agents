# ASP Platform Project Structure

This document describes the directory structure and organization of the Agentic Software Process (ASP) platform.

---

## Directory Layout

```
Process_Software_Agents/
├── src/asp/                    # Main application package
│   ├── agents/                 # Agent implementations (7 core + 14 specialized)
│   │   ├── base_agent.py
│   │   ├── planning_agent.py
│   │   ├── design_agent.py
│   │   ├── design_review_agent.py
│   │   ├── design_review_orchestrator.py  # Multi-agent design review
│   │   ├── code_agent.py
│   │   ├── code_review_orchestrator.py    # Multi-agent code review
│   │   ├── test_agent.py
│   │   ├── postmortem_agent.py
│   │   ├── reviews/            # 6 Design review specialist agents
│   │   │   ├── security_review_agent.py
│   │   │   ├── performance_review_agent.py
│   │   │   ├── data_integrity_review_agent.py
│   │   │   ├── maintainability_review_agent.py
│   │   │   ├── architecture_review_agent.py
│   │   │   └── api_design_review_agent.py
│   │   └── code_reviews/       # 6 Code review specialist agents
│   │       ├── code_quality_review_agent.py
│   │       ├── code_security_review_agent.py
│   │       ├── code_performance_review_agent.py
│   │       ├── best_practices_review_agent.py
│   │       ├── test_coverage_review_agent.py
│   │       └── documentation_review_agent.py
│   ├── orchestrators/          # Pipeline orchestrators with phase-aware feedback
│   │   ├── planning_design_orchestrator.py  # Planning-Design-Review coordination
│   │   └── types.py            # PlanningDesignResult and shared types
│   ├── telemetry/              # Observability and logging
│   │   ├── instrumentation.py
│   │   ├── langfuse_client.py
│   │   ├── cost_tracker.py
│   │   └── defect_logger.py
│   ├── models/                 # Data models (Pydantic/SQLAlchemy)
│   │   ├── planning.py
│   │   ├── design.py
│   │   ├── design_review.py
│   │   ├── code.py
│   │   ├── code_review.py
│   │   ├── test.py
│   │   ├── postmortem.py
│   │   └── telemetry.py
│   ├── prompts/                # Agent prompt templates (versioned)
│   │   ├── planning_agent_v1.txt
│   │   ├── design_agent_v1.txt
│   │   └── ...
│   └── utils/                  # Utility functions
│       ├── semantic_complexity.py
│       ├── probe_ai.py
│       └── config.py
├── artifacts/                  # Agent output artifacts (task-specific)
│   ├── BOOTSTRAP-001/          # Bootstrap task artifacts
│   ├── HW-001/                 # Hello World task artifacts
│   └── .../                    # 12+ task directories with plans, designs, code
├── data/                       # Runtime data (gitignored except .gitkeep)
│   ├── asp_telemetry.db        # SQLite database
│   ├── bootstrap_results.json  # Bootstrap learning data
│   └── bootstrap_analysis.md   # Bootstrap analysis reports
├── tests/                      # Test suite
│   ├── unit/                   # Unit tests
│   │   ├── test_agents/
│   │   ├── test_orchestrator/
│   │   └── test_telemetry/
│   ├── integration/            # Integration tests
│   │   └── test_full_workflow/
│   └── e2e/                    # End-to-end tests
│       └── test_complete_task/
├── database/                   # Database schemas and migrations
│   ├── migrations/
│   │   ├── 001_create_tables.sql
│   │   ├── 002_create_indexes.sql
│   │   ├── 003_timescaledb_setup.sql
│   │   └── 004_sample_data.sql
│   └── README.md
├── docs/                       # Documentation
│   ├── observability_platform_evaluation.md
│   ├── database_schema_specification.md
│   └── ...
├── scripts/                    # Utility scripts
│   ├── init_database.py        # Initialize SQLite database
│   ├── query_telemetry.py      # Query telemetry data
│   ├── run_agent_tests.py      # Test runner with incremental execution
│   ├── run_agent_tests.sh      # Bash test runner
│   ├── bootstrap_data_collection.py  # Collect bootstrap learning data
│   ├── bootstrap_code_collection.py
│   ├── bootstrap_design_review_collection.py
│   └── test_single_task.py     # Single task testing utility
├── config/                     # Configuration files
│   ├── agents.yaml
│   ├── prompts.yaml
│   └── telemetry.yaml
├── .github/workflows/          # GitHub Actions CI/CD
│   ├── tests.yml
│   └── deploy.yml
├── Summary/                    # Daily work logs
│   └── summary20251111.md
├── pyproject.toml              # Python project configuration (uv)
├── uv.lock                     # Dependency lock file
├── .python-version             # Python version specification
├── .gitignore                  # Git ignore rules
├── Claude.md                   # Development guidelines for Claude Code
├── PRD.md                      # Product Requirements Document
├── PSPdoc.md                   # ASP framework source document
└── README.md                   # Project README

```

---

## Directory Descriptions

### `src/asp/` - Main Application Package

The core ASP platform implementation.

**`agents/`** - Agent Implementations (21 Total)
- **7 Core Agents:** Planning, Design, Design Review, Code, Code Review, Test, Postmortem
- **2 Multi-Agent Review Orchestrators:** Design Review Orchestrator, Code Review Orchestrator
- **12 Specialist Review Agents:** 6 design specialists + 6 code review specialists
- `reviews/` subdirectory: Design review specialists (security, performance, data integrity, maintainability, architecture, API design)
- `code_reviews/` subdirectory: Code review specialists (quality, security, performance, best practices, test coverage, documentation)
- All agents extend `base_agent.py` for common functionality
- Agents are stateless and load prompts from `prompts/` directory

**`orchestrators/`** - Pipeline Orchestrators (Phase-Aware Feedback)
- `planning_design_orchestrator.py` - Coordinates Planning → Design → Design Review with automatic error correction
- `types.py` - `PlanningDesignResult` dataclass for artifact traceability
- Implements phase-aware feedback loops: routes defects back to originating phase
- Iteration limits prevent infinite loops (max 3 per phase, 10 total)
- Returns complete artifact set for downstream agents and PROBE-AI learning

**`telemetry/`** - Observability and Telemetry
- `instrumentation.py` - Decorators for automatic agent logging
- `langfuse_client.py` - Langfuse SDK integration
- `cost_tracker.py` - Agent Cost Vector tracking (FR-9)
- `defect_logger.py` - Defect Recording Log (FR-10)

**`models/`** - Data Models
- Pydantic models for validation and serialization
- SQLAlchemy models for database ORM (if using PostgreSQL hybrid)
- Matches database schema from `database/migrations/`

**`prompts/`** - Agent Prompt Templates
- Versioned prompt templates (v1, v2, etc.)
- Loaded dynamically by agents
- Supports PIP-driven prompt updates (Section VII)

**`utils/`** - Utility Functions
- `semantic_complexity.py` - Semantic Complexity calculation (Section 13.1 C1)
- `probe_ai.py` - PROBE-AI linear regression (Section 14.2 B1)
- `config.py` - Configuration management

### `artifacts/` - Agent Output Artifacts

Task-specific directories containing agent outputs:
- Each task gets a directory named by task ID (e.g., `BOOTSTRAP-001/`, `HW-001/`)
- Contains both JSON (machine-readable) and Markdown (human-readable) formats
- **Files per task:**
  - `plan.json`, `plan.md` - Planning Agent output (ProjectPlan)
  - `design.json`, `design.md` - Design Agent output (DesignSpecification)
  - `design_review.json` - Design Review Agent output (DesignReviewReport)
  - `code/` - Code Agent output (generated source files)
  - `test_results.json` - Test Agent output
  - `postmortem.json`, `postmortem.md` - Postmortem Agent analysis
- Used for bootstrap learning, PROBE-AI training, and artifact traceability
- 12+ task directories currently collected

### `data/` - Runtime Data

Runtime files (gitignored except `.gitkeep`):
- `asp_telemetry.db` - SQLite database with telemetry data (4 tables, 25+ indexes)
- `bootstrap_results.json` - Bootstrap learning metrics and analysis
- `bootstrap_analysis.md` - Human-readable bootstrap reports
- Generated during development and testing
- Database file location per ADR: `data/asp_telemetry.db`

### `tests/` - Test Suite

**`unit/`** - Unit Tests
- Test individual agents, functions, and classes in isolation
- Mock external dependencies (LLM API, database)
- Fast execution (<1 second per test)
- 200+ tests across all agents

**`integration/`** - Integration Tests
- Test interactions between components (e.g., orchestrator + agents)
- Use test database or in-memory database
- Moderate execution time (1-10 seconds per test)

**`e2e/`** - End-to-End Tests
- Test complete workflows (e.g., task submission → code generation → review)
- Use full system with real LLM calls (or recorded responses)
- Slow execution (30+ seconds per test)
- Validates orchestrator feedback loops and artifact flow

### `database/` - Database Schemas

- SQL migration scripts for SQLite/PostgreSQL
- See `database/README.md` for setup instructions
- Schema specification in `docs/database_schema_specification.md`

### `docs/` - Documentation

- **Architecture Decision Records (ADRs):** 11+ decision documents
- **User Guides:** Agent usage, artifact persistence, telemetry
- **Technical Specifications:** Database schema, observability platform, test plans
- **Planning Documents:** PRD, PSPdoc, test implementation plans

### `scripts/` - Utility Scripts

- `init_database.py` - One-command database initialization with sample data
- `query_telemetry.py` - Query and analyze telemetry data
- `run_agent_tests.py` - Test runner with incremental execution modes
- `bootstrap_*.py` - Scripts for collecting bootstrap learning data
- `test_single_task.py` - Single task testing and validation

### `config/` - Configuration Files

- YAML configuration for agents, prompts, telemetry
- Environment-specific configs (dev, staging, prod)

### `.github/workflows/` - CI/CD Pipelines

- `tests.yml` - Run tests on every PR
- `deploy.yml` - Deployment automation

---

## Key Files

### `pyproject.toml`
Python project metadata and dependencies (managed by `uv`)

### `uv.lock`
Lock file for reproducible builds (auto-generated by `uv`)

### `.python-version`
Specifies Python 3.12+ requirement

### `Claude.md`
Development guidelines for Claude Code (workflow, conventions, testing)

### `PRD.md`
Product Requirements Document (single source of truth for requirements)

### `README.md`
Project overview, quick start guide, contribution guidelines

---

## Naming Conventions

### Files
- Python modules: `snake_case.py`
- Test files: `test_<module_name>.py`
- SQL migrations: `NNN_<descriptive_name>.sql`
- Config files: `<component>.yaml`

### Code
- Classes: `PascalCase`
- Functions/Methods: `snake_case`
- Constants: `UPPER_SNAKE_CASE`
- Private members: `_leading_underscore`

### Git Branches
- Feature branches: `feature/<description>`
- Bug fixes: `fix/<description>`
- Documentation: `docs/<description>`

---

## Development Workflow

1. **Start New Feature:**
   ```bash
   git checkout -b feature/my-feature
   ```

2. **Install Dependencies:**
   ```bash
   uv sync --all-extras
   ```

3. **Run Tests:**
   ```bash
   uv run pytest
   ```

4. **Format Code:**
   ```bash
   uv run ruff format .
   uv run ruff check --fix .
   ```

5. **Commit Changes:**
   ```bash
   git add .
   git commit -m "Add feature: description"
   ```

6. **Push and Create PR:**
   ```bash
   git push origin feature/my-feature
   # Create PR on GitHub
   ```

---

## Current Implementation Status

Based on the 5-phase roadmap (PRD Section 7):

### Phase 1: ASP0 - Measurement Foundation **87.5% Complete**
- ✅ `src/asp/telemetry/` - Core logging and instrumentation implemented
- ✅ `src/asp/models/` - All data models created (planning, design, code, telemetry)
- ✅ `database/` - SQLite database deployed with 4 tables, 25+ indexes
- ✅ `tests/` - 200+ tests across all agents
- ✅ `data/` - Telemetry database operational
- 🟡 `artifacts/` - 12+ tasks collected, need 30+ for PROBE-AI

### Phase 2: ASP1 - Estimation **Not Started**
- ⏳ `src/asp/utils/probe_ai.py` - Requires 30+ tasks for linear regression
- ⏳ Validation of estimation accuracy (±20%)

### Phase 3: ASP2 - Gated Review **66% Complete**
- ✅ `src/asp/agents/design_review_agent.py` - Multi-agent system (6 specialists)
- ✅ `src/asp/agents/code_review_agent.py` - Multi-agent system (6 specialists)
- ✅ `src/asp/agents/design_review_orchestrator.py` - Design review orchestrator
- ✅ `src/asp/agents/code_review_orchestrator.py` - Code review orchestrator
- 🟡 Phase yield measurement (requires more bootstrap data)

### Phase 4: ASP-TSP - Orchestration **Started**
- ✅ All 7 core agents implemented
- ✅ `src/asp/orchestrators/planning_design_orchestrator.py` - Phase-aware feedback
- ✅ `src/asp/orchestrators/types.py` - PlanningDesignResult for artifact traceability
- 🟡 Full TSP orchestrator (partial - planning-design complete)
- ⏳ 50% task completion rate measurement

### Phase 5: ASP-Loop - Self-Improvement **33% Complete**
- ✅ `src/asp/agents/postmortem_agent.py` - Performance analysis and root cause analysis
- ⏳ PIP workflow (Process Improvement Proposals)
- ⏳ Continuous improvement cycle

---

## Recent Additions

**Orchestrator Infrastructure (Nov 19-20, 2025):**
- `src/asp/orchestrators/planning_design_orchestrator.py` - Coordinates Planning → Design → Design Review with phase-aware feedback loops
- Routes defects back to originating phase (implements PSP principle)
- Iteration limits prevent infinite loops
- Returns complete artifact set for downstream agents

**Artifact Traceability:**
- `artifacts/` directory with 12+ task directories
- Each task has plan, design, design review, code artifacts
- Used for bootstrap learning and PROBE-AI training

**Documentation:**
- 11+ Architecture Decision Records in `docs/`
- User guides for artifact persistence and telemetry
- Comprehensive test plans and gap analysis

---

**Version:** 2.0
**Last Updated:** 2025-11-20
