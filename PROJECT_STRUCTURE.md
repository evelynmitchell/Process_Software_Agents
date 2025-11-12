# ASP Platform Project Structure

This document describes the directory structure and organization of the Agentic Software Process (ASP) platform.

---

## Directory Layout

```
Process_Software_Agents/
├── src/asp/                    # Main application package
│   ├── agents/                 # Agent implementations (7 specialized agents)
│   │   ├── planning_agent.py
│   │   ├── design_agent.py
│   │   ├── design_review_agent.py
│   │   ├── coding_agent.py
│   │   ├── code_review_agent.py
│   │   ├── test_agent.py
│   │   └── postmortem_agent.py
│   ├── orchestrator/           # TSP Orchestrator (control plane)
│   │   ├── orchestrator.py
│   │   ├── quality_gates.py
│   │   └── hitl_workflow.py
│   ├── telemetry/              # Observability and logging
│   │   ├── instrumentation.py
│   │   ├── langfuse_client.py
│   │   ├── cost_tracker.py
│   │   └── defect_logger.py
│   ├── models/                 # Data models (Pydantic/SQLAlchemy)
│   │   ├── task.py
│   │   ├── agent_cost.py
│   │   ├── defect.py
│   │   └── bootstrap.py
│   ├── prompts/                # Agent prompt templates (versioned)
│   │   ├── planning_agent_v1.txt
│   │   ├── design_agent_v1.txt
│   │   └── ...
│   └── utils/                  # Utility functions
│       ├── semantic_complexity.py
│       ├── probe_ai.py
│       └── config.py
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
│   ├── run_migrations.sh
│   ├── setup_dev_env.sh
│   └── ...
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

**`agents/`** - Specialized Agent Implementations
- Each file implements one of the 7 specialized agents (Section V of PRD)
- Agents are stateless and communicate via orchestrator
- Prompts loaded from `prompts/` directory

**`orchestrator/`** - TSP Orchestrator (Control Plane)
- `orchestrator.py` - Main orchestrator logic (TSP-based workflow)
- `quality_gates.py` - Implements mandatory review gates (FR-3, FR-5)
- `hitl_workflow.py` - Human-in-the-Loop approval workflows

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

### `tests/` - Test Suite

**`unit/`** - Unit Tests
- Test individual agents, functions, and classes in isolation
- Mock external dependencies (LLM API, database)
- Fast execution (<1 second per test)

**`integration/`** - Integration Tests
- Test interactions between components (e.g., orchestrator + agents)
- Use test database or in-memory database
- Moderate execution time (1-10 seconds per test)

**`e2e/`** - End-to-End Tests
- Test complete workflows (e.g., task submission → code generation → review)
- Use full system with real LLM calls (or recorded responses)
- Slow execution (30+ seconds per test)

### `database/` - Database Schemas

- SQL migration scripts for PostgreSQL/TimescaleDB
- See `database/README.md` for setup instructions

### `docs/` - Documentation

- Technical specifications
- Architecture diagrams
- Decision records (observability platform, etc.)

### `scripts/` - Utility Scripts

- `run_migrations.sh` - Apply database migrations
- `setup_dev_env.sh` - Set up local development environment
- Deployment scripts, data seeding, etc.

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

## Phase 1 Implementation Priorities

Based on the 5-phase roadmap (PRD Section 7), focus areas for Phase 1:

### Month 1-2: ASP0 - Measurement Foundation

**Priority Directories:**
1. `src/asp/telemetry/` - Implement core logging
2. `src/asp/models/` - Create data models for agent_cost_vector, defect_log
3. `database/` - Deploy and test migrations
4. `tests/unit/test_telemetry/` - Validate telemetry accuracy

**Deferred:**
- Full agent implementations (Phase 4)
- Orchestrator (Phase 4)
- Postmortem agent (Phase 5)

### Month 3-4: ASP1 - Estimation

**Priority Directories:**
1. `src/asp/agents/planning_agent.py` - Implement Planning Agent
2. `src/asp/utils/probe_ai.py` - Implement PROBE-AI
3. `src/asp/utils/semantic_complexity.py` - Implement complexity calculation
4. `tests/integration/` - Validate estimation accuracy

---

## Next Steps

- [ ] Create `pyproject.toml` with dependencies
- [ ] Initialize with `uv sync`
- [ ] Create stub implementations for agents
- [ ] Set up pre-commit hooks
- [ ] Write initial unit tests

---

**Version:** 1.0
**Last Updated:** 2025-11-11
