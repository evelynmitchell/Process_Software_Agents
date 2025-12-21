# Claude

# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Important Notes

**For Claude**: If you notice you've forgotten key details about this project (like using `uv` instead of `pip`, or commit message specificity), re-read this entire file to refresh context.

**For User**: If you notice Claude has forgotten key workflow details after context compression, ask it to re-read this file.

## Starting a New Day / New Codespace

**IMPORTANT**: When starting work on a new day or in a new codespace, **ALWAYS** check if `setup_codespace.sh` exists and run it:

```bash
# Check if setup script exists
if [ -f "setup_codespace.sh" ]; then
    bash setup_codespace.sh
fi
```

The setup script will:
1. Install Claude Code (if needed)
2. Install uv package manager (if needed)
3. Verify Python 3.12+ is available
4. Install all project dependencies via `uv sync --all-extras`
5. Verify the installation by running unit tests
6. Display next steps and useful commands

**Why this matters**:
- Ensures consistent environment setup across different codespaces
- Installs all required tools (uv, dependencies)
- Verifies the setup works by running tests
- Saves time by automating the setup process

After running the setup script:

**THEN: Load context using tiered memory (CRITICAL):**
1. Read `docs/KNOWLEDGE_BASE.md` (Long-term Memory - evergreen patterns)
2. Read this `Claude.md` (Behavioral Instructions)
3. Read latest `Summary/weekly_reflection_*.md` (Recent Context - last week's progress)
4. Read last 3 `Summary/summaryYYYYMMDD.*.md` files (Immediate Context - recent sessions)

**AVOID:** Reading all 136+ session summaries - this exhausts the context window.

**FINALLY:** Create a new session summary file (`Summary/summaryYYYYMMDD.N.md`) to track the session's work.

## Repository Overview

The **Autonomous Software Process (ASP)** platform implements PSP/TSP (Personal/Team Software Process) principles for AI agents. It provides:

- **8 Specialized Agents:** Planning, Design, DesignReview, Code, CodeReview, Test, Postmortem, Repair
- **TSP Orchestrator:** 7-phase pipeline with quality gates and HITL (Human-in-the-Loop) integration
- **Web UI:** Three personas - Manager (Overwatch), Developer (Flow State Canvas), Product Manager (Feature Wizard)
- **MCP Server:** 4 tools for Claude CLI integration (`asp_plan`, `asp_code_review`, `asp_diagnose`, `asp_test`)
- **GitHub Integration:** Issue-to-PR automation via `asp repair-issue` command
- **Multi-LLM Support:** Provider abstraction layer (Anthropic, OpenRouter, Gemini, etc.)

**Key Metrics (as of Dec 2025):**
- 60,000+ LOC across source and tests
- 75-76% test coverage
- 13 ADRs (Architectural Decision Records)
- 136+ documented development sessions

## Repository Structure

```
src/asp/
├── agents/           # Agent implementations
│   ├── planning_agent.py
│   ├── design_agent.py
│   ├── code_agent.py
│   ├── test_agent.py
│   ├── diagnostic_agent.py
│   ├── repair_agent.py
│   └── *_review_*.py  # Review specialists
├── orchestrators/    # Pipeline orchestrators
│   ├── tsp_orchestrator.py
│   └── repair_orchestrator.py
├── providers/        # Multi-LLM provider abstraction
│   ├── base.py
│   ├── anthropic_provider.py
│   └── registry.py
├── mcp/              # MCP server for Claude CLI
│   └── server.py
├── web/              # FastHTML web UI
│   └── routes/
├── models/           # Pydantic data models
├── services/         # External service integrations
│   └── github_service.py
└── telemetry/        # Observability (Langfuse, Logfire)

design/               # ADRs and design documents
Summary/              # Session summaries and weekly reflections
docs/                 # User guides and API reference
tests/                # Unit, integration, and E2E tests
```



## Development Workflow

This repository follows a structured 6-stage programming workflow inspired by design recipe methodology (documented in `Process` file):

1. **Problem Analysis to Data Definitions**: Identify input/output data representation with examples
2. **Signature, Purpose Statement, Header**: Define function signature and stub
3. **Functional Examples**: Create manual examples that will become tests
4. **Function Template**: Translate data definitions into function outline
5. **Function Definition**: Fill in the template
6. **Testing**: Run tests to verify correctness

Time tracking: The workflow uses git commit timestamps to track time spent at each stage.

### ADR-Driven Development

For features requiring 3+ phases or architectural decisions, use ADR-driven development:

1. **Create ADR:** Write `design/ADR_XXX_<feature_name>.md` with context, decision, and phases
2. **Define Phases:** Break implementation into independent, testable phases with clear deliverables
3. **Implement Phase-by-Phase:** Complete and commit each phase before starting the next
4. **Update Status:** Mark phase completion in the ADR after each merge

**Current ADR Status:** See `Summary/weekly_reflection_*.md` for the latest ADR progress summary.

**Template:** Reference existing ADRs in `design/` directory (e.g., `ADR_006_repair_workflow.md`).

## MCP Server (Claude CLI Integration)

ASP exposes 4 tools via MCP for Claude CLI integration:

| Tool | Description |
|------|-------------|
| `asp_plan` | Task decomposition with PROBE estimation |
| `asp_code_review` | 6-specialist code review (security, performance, quality, tests, docs, best practices) |
| `asp_diagnose` | Bug diagnosis with root cause analysis and fix suggestions |
| `asp_test` | Test generation and execution with defect classification |

**Configuration Files:**
- `.mcp.json` - MCP server configuration for Claude CLI
- `.claude/settings.json` - Universal telemetry hooks

**Starting the MCP Server:**
```bash
uv run python -m asp.mcp.server
```

## Python Development

This project uses **uv** for Python version and dependency management.

### What is uv?

`uv` is a fast, Rust-based Python package manager that:
- Resolves dependencies 10-100x faster than pip
- Automatically manages virtual environments
- Handles Python version management
- Creates lock files for reproducible builds
- Fully compatible with standard `pyproject.toml` format

### Installation

Install uv (one-time setup):
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Or on macOS with Homebrew:
```bash
brew install uv
```

### Common Commands

**Install dependencies:**
```bash
uv sync
```
This creates a virtual environment and installs all dependencies from `pyproject.toml`.

**Install with dev dependencies:**
```bash
uv sync --all-extras
```

**Run a Python script:**
```bash
uv run scripts/test_yfinance_api.py
```
Automatically uses the project's virtual environment.

**Run a Python module:**
```bash
uv run python -m pytest
```

**Add a new dependency:**
```bash
uv add package-name
```

**Add a dev dependency:**
```bash
uv add --dev package-name
```

**Update dependencies:**
```bash
uv lock --upgrade
uv sync
```

**Run Python REPL with project environment:**
```bash
uv run python
```

### Project Dependencies

**Core dependencies** (defined in `pyproject.toml`):
- `yfinance>=0.2.0` - Yahoo Finance market data
- `yoptions>=0.1.0` - Options Greeks calculation

**Dev dependencies** (optional, installed with `--all-extras`):
- `pytest>=8.0.0` - Testing framework
- `black>=24.0.0` - Code formatter
- `ruff>=0.1.0` - Fast Python linter

### Python Version

This project requires **Python 3.12 or higher**.

The `.python-version` file specifies the exact version. `uv` will automatically use the correct Python version when running commands.

### Virtual Environment

`uv` automatically creates and manages a virtual environment in `.venv/`.

You don't need to manually activate it - `uv run` handles this automatically.

### IDE Setup

**VS Code**: Install the Python extension. It should automatically detect the `.venv/` environment created by uv.

**PyCharm**: Set the Python interpreter to `.venv/bin/python`.




## Common Patterns

### Workflow

Create a Summaryyyymmdd.md file for every new workday, and update it with progress regularly. Add it to the commit after updating and then do the commit.

Use the summary to track work done, issues discovered, and good practices learned.

### Memory & Learning Protocol

**1. Memory Management (Tiered Context):**
To manage context window limits, do not read all files in `Summary/`.
- **Read:** `docs/KNOWLEDGE_BASE.md` (Long-term Memory)
- **Read:** `Claude.md` (Behavioral Instructions)
- **Read:** The latest `Summary/weekly_reflection_*.md` (Recent Context)
- **Read:** The last 3 `Summary/summaryYYYYMMDD.md` files (Immediate Context)

**2. The Learning Loop (Weekly):**
- **Capture:** In daily summaries, mark potential permanent lessons under `## Candidate for Evergreen`.
- **Synthesize:** In weekly reflections, review these candidates.
- **Promote:** Move verified lessons to `docs/KNOWLEDGE_BASE.md` (for system facts) or `Claude.md` (for behavioral instructions).

### Running Tests

**ALWAYS use `uv run` for test execution:**
```bash
uv run pytest                           # Run all tests
uv run pytest -x                        # Stop on first failure
uv run pytest tests/unit/               # Unit tests only
uv run pytest tests/integration/        # Integration tests only
uv run pytest -m "not slow"             # Skip slow tests
uv run pytest --cov --cov-report=term   # With coverage report
```

**Never run `pytest` directly** - this bypasses uv's environment management and may use wrong dependencies.

**Coverage Requirements:**
- Target: 80% minimum (configured in `pyproject.toml`)
- Check coverage: `uv run pytest --cov --cov-report=term-missing`
- Identify gaps: Sort by lowest coverage modules and prioritize

### Testing Philosophy

- Write comprehensive tests covering edge cases (empty arrays, zeros, boundary conditions)
- Test naming: `test_<feature>_<case><expected_result>` (e.g., `test_array_oneT` for True result)
- Use combinatorial testing: test sign combinations (+/+, +/-, -/-, -/+) and value ranges (low/low, low/high, high/low, high/high)
- **Mocking:** E2E mock responses must align strictly with Pydantic models - schema mismatches are the #1 cause of E2E test failures
- **Isolation:** Tests that modify state (files, DB) must use fixtures to prevent leakage

### Code Quality Standards

Common errors to avoid:
- Use `False/True` not `FALSE/TRUE` (Python booleans)
- Watch for edge case "thinkos" - assumptions about cases that aren't needed
- Always use version control with meaningful commits

### Common LLM Integration Errors

Patterns learned from 136+ development sessions:

1. **JSON Parsing:** LLMs wrap JSON in markdown fences - use `extract_json_from_response()` utility
2. **Token Limits:** Use 8192+ for structured output (4096 causes truncation and parse failures)
3. **Schema Validation:** Pydantic `pattern` uses `re.search()` not `re.fullmatch()` - always add `^...$` anchors
4. **Hash IDs:** Use 7+ characters to avoid birthday collisions (5-char hits 50% collision at ~1,170 items)
5. **Retry Logic:** Essential for production reliability - use exponential backoff

### Session Summaries

Create `Summary/summaryYYYYMMDD.N.md` for each development session using the template in `design/SESSION_TEMPLATE.md`.

Key sections to complete:
- **Objective:** Single clear sentence
- **Previous Session Outcome:** Track if work "stuck" (fully used, partially used, not used)
- **Interventions:** Log any course corrections during the session
- **Completeness Checklist:** Verify before closing

**North Star Metric:** Effective Work Rate = (work that stuck) / (total work done)

### Weekly Reflections

Create `Summary/weekly_reflection_YYYYMMDD.md` every Friday:

1. Review all daily summaries from the week
2. Identify candidates for `KNOWLEDGE_BASE.md` promotion
3. Update ADR status summary table
4. List improvement actions for next week
5. Calculate weekly metrics (PRs merged, tests added, coverage delta)

### CI/CD with GitHub Actions

This repository uses GitHub Actions for continuous integration.


### Pre-commit Hooks

This repository uses pre-commit hooks to enforce code quality before commits:

**Initial setup** (one-time):
```bash
pip install pre-commit
pre-commit install
```

**What runs automatically on commit**:
- **Ruff**: Lints and auto-fixes Python issues
- **Ruff format**: Auto-formats Python code
- **Trim trailing whitespace**: Removes trailing spaces
- **Fix end of files**: Ensures files end with newline
- **Check YAML/TOML**: Validates configuration files
- **Check for merge conflicts**: Detects merge markers
- **Mixed line endings**: Ensures consistent line endings
- **Debug statements**: Catches leftover debug code
- **Check Python AST**: Validates Python syntax

If hooks fail, they will:
1. Auto-fix formatting issues where possible
2. Block the commit if there are unfixable issues
3. Allow you to review changes and re-attempt the commit

**Manual execution** (optional):
```bash
# Run on all files
pre-commit run --all-files

# Run on staged files only
pre-commit run
```

The pre-commit hooks serve as the first line of defense, with GitHub Actions as a backup for any changes that bypass local hooks.

### Git Commit Workflow for Claude Code

**IMPORTANT**: When creating commits, ALWAYS follow this workflow to ensure code quality:

1. **Stage your changes**:
   ```bash
   git add <files>
   ```

2. **Create the commit** (pre-commit hooks run automatically):
   ```bash
   git commit -m "Your commit message"
   ```

3. **If pre-commit hooks modify files**:
   - The hooks auto-fix formatting/linting issues
   - The commit will FAIL with "files were modified by this hook"
   - The fixes are already applied to your working directory
   - **You MUST add the fixes and amend the commit**:

   ```bash
   # Add the auto-fixed files
   git add <modified-files>

   # Amend the commit with the fixes
   git commit --amend --no-edit
   ```

4. **Verify the commit succeeded**:
   - Pre-commit hooks should now pass
   - Commit is created with both your changes and auto-fixes

**Example workflow**:
```bash
# Stage files
git add src/ranking_representation/comparison.py

# Attempt commit (hooks may fix formatting)
git commit -m "Add comparison functionality"
# Output: "files were modified by this hook" - FAILED

# Add the auto-fixed files
git add src/ranking_representation/comparison.py

# Amend to include fixes
git commit --amend --no-edit
# Output: All hooks passes - SUCCESS
```

**Why this matters**:
- Ensures consistent code formatting across the project
- Catches common errors before they reach GitHub
- Prevents CI/CD failures from formatting issues
- Maintains high code quality standards

**For Claude**: Always follow this workflow when creating commits. If a commit fails due to pre-commit hooks, immediately add the modified files and amend the commit.

## Telemetry & Observability

ASP supports dual-backend telemetry for comprehensive observability:

| Backend | Purpose |
|---------|---------|
| **Langfuse** | Agent traces, cost tracking, prompt versioning |
| **Logfire** | LLM auto-instrumentation, Pydantic validation insights |

**Configuration:**
```bash
# Choose telemetry backend
export ASP_TELEMETRY_PROVIDER=both    # or "langfuse" or "logfire"

# Required API keys
export LANGFUSE_PUBLIC_KEY=...
export LANGFUSE_SECRET_KEY=...
export LOGFIRE_TOKEN=...
```

**Key Features:**
- Automatic LLM call tracing (Anthropic, OpenAI)
- Cost tracking per agent invocation
- Sensitive data redaction in hooks
- Non-blocking telemetry (no performance impact)
