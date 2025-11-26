# Getting Started with ASP

This guide will help you install the ASP Platform, configure your environment, and run your first autonomous software development task.

---

## Table of Contents

- [Prerequisites](#prerequisites)
- [Installation Options](#installation-options)
- [Configuration](#configuration)
- [Your First Task](#your-first-task)
- [Understanding the Output](#understanding-the-output)
- [Troubleshooting](#troubleshooting)
- [Next Steps](#next-steps)

---

## Prerequisites

Before installing ASP, ensure you have:

### Required

- **Python 3.12 or higher** - [Download Python](https://www.python.org/downloads/)
- **uv package manager** - [Install uv](https://github.com/astral-sh/uv)
- **Anthropic API Key** - [Get API Key](https://console.anthropic.com)
- **Langfuse Account** - [Sign up for Langfuse Cloud](https://cloud.langfuse.com) (free tier available)

### Optional

- **Git** - For version control
- **GitHub Account** - For GitHub Codespaces or GitHub Issues HITL

### System Requirements

- **OS:** Linux, macOS, or Windows (WSL recommended for Windows)
- **RAM:** 4GB minimum, 8GB recommended
- **Disk Space:** 500MB for installation + space for artifacts

---

## Installation Options

Choose the installation method that best suits your workflow:

### Option 1: GitHub Codespaces (Recommended for Beginners)

**Perfect for zero-setup development in the cloud.**

#### Step 1: Create Codespace

1. Navigate to the [ASP repository](https://github.com/evelynmitchell/Process_Software_Agents)
2. Click the **"Code"** button
3. Select **"Codespaces"** tab
4. Click **"Create codespace on main"**

GitHub will create a cloud development environment with all dependencies pre-installed.

#### Step 2: Configure Secrets

Add your API keys to [Repository Settings → Codespaces Secrets](https://github.com/evelynmitchell/Process_Software_Agents/settings/secrets/codespaces):

| Secret Name | Value | Where to Get It |
|-------------|-------|----------------|
| `ANTHROPIC_API_KEY` | `sk-ant-...` | [Anthropic Console](https://console.anthropic.com) → API Keys |
| `LANGFUSE_PUBLIC_KEY` | `pk-lf-...` | [Langfuse Dashboard](https://cloud.langfuse.com) → Settings → API Keys |
| `LANGFUSE_SECRET_KEY` | `sk-lf-...` | [Langfuse Dashboard](https://cloud.langfuse.com) → Settings → API Keys |
| `LANGFUSE_HOST` | `https://cloud.langfuse.com` | Fixed value for Langfuse Cloud |

**After adding secrets, restart your Codespace** for them to take effect.

#### Step 3: Verify Setup

```bash
# Check secrets are loaded
echo $ANTHROPIC_API_KEY    # Should show sk-ant-...
echo $LANGFUSE_PUBLIC_KEY  # Should show pk-lf-...

# Initialize database
uv run python scripts/init_database.py --with-sample-data

# Run tests
uv run pytest -m unit
```

**You're ready!** Skip to [Your First Task](#your-first-task).

---

### Option 2: Local Development

**For development on your local machine.**

#### Step 1: Install Prerequisites

**Install Python 3.12:**
```bash
# macOS (using Homebrew)
brew install python@3.12

# Ubuntu/Debian
sudo apt install python3.12 python3.12-venv

# Verify installation
python3.12 --version
```

**Install uv package manager:**
```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Verify installation
uv --version
```

#### Step 2: Clone Repository

```bash
# Clone the repository
git clone https://github.com/evelynmitchell/Process_Software_Agents.git
cd Process_Software_Agents
```

#### Step 3: Install Dependencies

```bash
# Install all dependencies (development + optional extras)
uv sync --all-extras

# This creates a virtual environment at .venv/ and installs:
# - Core dependencies (anthropic, langfuse, pydantic, sqlalchemy)
# - Development tools (pytest, ruff, mypy)
# - All optional extras
```

#### Step 4: Configure Environment

ASP uses environment variables for API keys and configuration. You have two options:

**Option A: Environment Variables (Recommended)**

```bash
# Set environment variables (add to ~/.bashrc or ~/.zshrc for persistence)
export ANTHROPIC_API_KEY="sk-ant-your-key-here"
export LANGFUSE_PUBLIC_KEY="pk-lf-your-key-here"
export LANGFUSE_SECRET_KEY="sk-lf-your-key-here"
export LANGFUSE_HOST="https://cloud.langfuse.com"

# Verify
echo $ANTHROPIC_API_KEY
```

**Option B: .env File (Alternative)**

```bash
# Create .env file (copy from example)
cp .env.example .env

# Edit .env with your favorite editor
nano .env  # or vim, code, etc.

# Add your keys:
# ANTHROPIC_API_KEY=sk-ant-your-key-here
# LANGFUSE_PUBLIC_KEY=pk-lf-your-key-here
# LANGFUSE_SECRET_KEY=sk-lf-your-key-here
# LANGFUSE_HOST=https://cloud.langfuse.com
```

#### Step 5: Initialize Database

```bash
# Create database with schema and sample data
uv run python scripts/init_database.py --with-sample-data

# This creates:
# - data/asp_telemetry.db (SQLite database)
# - Schema with 4 tables and 25+ indexes
# - Sample bootstrap data (if --with-sample-data flag used)
```

#### Step 6: Verify Installation

```bash
# Run unit tests (fast, no API calls)
uv run pytest -m unit

# Run integration tests (uses real APIs, costs ~$0.10)
uv run pytest -m integration

# Run all tests
uv run pytest

# Check orchestrator is available
uv run python -c "from asp.orchestrators import TSPOrchestrator; print('✓ ASP ready')"
```

If all tests pass, you're ready to use ASP!

---

## Configuration

### API Keys

ASP requires two sets of API keys:

#### 1. Anthropic API Key (Required)

**Purpose:** Access Claude models for agent execution

**Get Key:**
1. Visit [Anthropic Console](https://console.anthropic.com)
2. Create account or log in
3. Navigate to **API Keys**
4. Click **"Create Key"**
5. Copy key (starts with `sk-ant-`)

**Cost:** Pay-as-you-go pricing
- Claude Sonnet 4: $3/$15 per million tokens (input/output)
- Typical task: $0.05 - $0.50 depending on complexity

#### 2. Langfuse Keys (Required for Telemetry)

**Purpose:** Observability, tracing, and cost analytics

**Get Keys:**
1. Visit [Langfuse Cloud](https://cloud.langfuse.com)
2. Create account (free tier available)
3. Create a new project
4. Navigate to **Settings → API Keys**
5. Copy **Public Key** (starts with `pk-lf-`)
6. Copy **Secret Key** (starts with `sk-lf-`)

**Cost:** Free tier includes:
- 50,000 observations/month
- 7 days retention
- Sufficient for ~100-200 ASP tasks

### Optional Configuration

ASP provides sensible defaults, but you can customize:

```python
# src/asp/config.py (if you need to override defaults)

# Database Configuration
DATABASE_PATH = "data/asp_telemetry.db"  # SQLite database location

# Artifact Configuration
ARTIFACTS_DIR = "artifacts/"  # Where task artifacts are stored

# Agent Configuration
DEFAULT_MODEL = "claude-sonnet-4"  # Default LLM model
MAX_RETRIES = 3  # Agent retry limit
TIMEOUT_SECONDS = 300  # Agent timeout

# Bootstrap Learning Configuration
PROBE_AI_MIN_TASKS = 30  # Minimum tasks before PROBE-AI activation
ESTIMATION_MAPE_THRESHOLD = 20.0  # Max acceptable estimation error %
```

Most users won't need to change these defaults.

---

## Your First Task

Let's run a simple task through the ASP pipeline to verify everything works.

### Example 1: Hello World (Simple Task)

This example demonstrates the full 7-agent pipeline with a trivial task.

```python
# examples/hello_world.py
"""
Simple Hello World task demonstrating ASP pipeline.

This runs a complete task through all 7 agents:
- Planning Agent: Breaks down task
- Design Agent: Creates design specification
- Design Review Agent: Reviews design quality
- Code Agent: Generates implementation
- Code Review Agent: Reviews code quality
- Test Agent: Generates and runs tests
- Postmortem Agent: Analyzes performance

Run with:
    uv run python examples/hello_world.py
"""

from asp.orchestrators import TSPOrchestrator
from asp.models import TaskRequest

# Create task request
task = TaskRequest(
    task_id="HW-001",
    description="Create a Python function that prints 'Hello, World!' to stdout",
    requirements=[
        "Function should be named 'hello_world'",
        "Function should take no parameters",
        "Function should print exactly 'Hello, World!' (case-sensitive)",
        "Include a docstring explaining the function"
    ]
)

# Create orchestrator
orchestrator = TSPOrchestrator()

# Execute full pipeline
print("🚀 Starting ASP pipeline for Hello World task...")
print(f"📋 Task ID: {task.task_id}")
print(f"📝 Description: {task.description}\n")

result = orchestrator.execute(task)

# Display results
print("\n✅ Pipeline completed successfully!\n")
print(f"📊 Performance Summary:")
print(f"   - Total Latency: {result.total_latency_ms:,} ms")
print(f"   - Total Tokens: {result.total_tokens:,}")
print(f"   - Total Cost: ${result.total_cost_usd:.4f}")
print(f"   - Defects Found: {len(result.defects)}")
print(f"   - Quality Gates: {'PASS' if result.quality_gate_status == 'PASS' else 'FAIL'}")

print(f"\n📁 Artifacts saved to: artifacts/{task.task_id}/")
print("   - plan.md - Planning output")
print("   - design.md - Design specification")
print("   - design_review.md - Design review report")
print("   - generated_code/ - Implementation")
print("   - code_review.md - Code review report")
print("   - test_results.md - Test results")
print("   - postmortem.md - Performance analysis")

print(f"\n🔍 View detailed traces at: https://cloud.langfuse.com")
```

**Run it:**

```bash
uv run python examples/hello_world.py
```

**Expected Output:**

```
🚀 Starting ASP pipeline for Hello World task...
📋 Task ID: HW-001
📝 Description: Create a Python function that prints 'Hello, World!' to stdout

[Planning Phase] Analyzing task... ✓
[Design Phase] Creating design... ✓
[Design Review Phase] Reviewing design (6 specialists)... ✓
[Code Phase] Generating implementation... ✓
[Code Review Phase] Reviewing code (6 specialists)... ✓
[Test Phase] Running tests... ✓
[Postmortem Phase] Analyzing performance... ✓

✅ Pipeline completed successfully!

📊 Performance Summary:
   - Total Latency: 45,231 ms
   - Total Tokens: 12,450
   - Total Cost: $0.0823
   - Defects Found: 0
   - Quality Gates: PASS

📁 Artifacts saved to: artifacts/HW-001/
   - plan.md - Planning output
   - design.md - Design specification
   - design_review.md - Design review report
   - generated_code/ - Implementation
   - code_review.md - Code review report
   - test_results.md - Test results
   - postmortem.md - Performance analysis

🔍 View detailed traces at: https://cloud.langfuse.com
```

**Cost:** ~$0.08 - $0.15 for full 7-agent pipeline

---

### Example 2: REST API Endpoint (Medium Complexity)

A more realistic task demonstrating ASP's capabilities:

```python
# examples/rest_api_endpoint.py
from asp.orchestrators import TSPOrchestrator
from asp.models import TaskRequest

task = TaskRequest(
    task_id="API-001",
    description="Create a FastAPI endpoint for user registration",
    requirements=[
        "POST /api/users endpoint",
        "Accept JSON body with username, email, password",
        "Validate email format and password strength",
        "Hash password with bcrypt before storage",
        "Return 201 Created with user ID on success",
        "Return 400 Bad Request for validation errors",
        "Include SQLAlchemy User model",
        "Include comprehensive tests (happy path + error cases)"
    ]
)

orchestrator = TSPOrchestrator()
result = orchestrator.execute(task)

print(f"\n📊 Task completed in {result.total_latency_ms/1000:.1f}s")
print(f"💰 Total cost: ${result.total_cost_usd:.4f}")
```

**Run it:**

```bash
uv run python examples/rest_api_endpoint.py
```

**Expected Output:** Full implementation with validation, error handling, tests, and comprehensive documentation. Cost: ~$0.25 - $0.50.

---

## Understanding the Output

After running a task, ASP generates comprehensive artifacts and telemetry.

### Artifacts Directory Structure

```
artifacts/HW-001/
├── plan.json                  # Machine-readable planning output
├── plan.md                    # Human-readable planning output
├── design.json                # Machine-readable design
├── design.md                  # Human-readable design
├── design_review.json         # Review results (JSON)
├── design_review.md           # Review results (Markdown)
├── generated_code/            # Code artifacts
│   ├── hello_world.py         # Implementation
│   └── test_hello_world.py    # Tests
├── code_review.json           # Code review results
├── code_review.md             # Code review report
├── test_results.json          # Test execution results
├── test_results.md            # Test report
├── postmortem.json            # Performance analysis
└── postmortem.md              # Postmortem report
```

### Key Artifacts Explained

#### 1. plan.md - Planning Output

Contains:
- **Task Breakdown:** Semantic units and subtasks
- **Complexity Analysis:** Weighted complexity score
- **Effort Estimation:** Predicted latency, tokens, cost (if PROBE-AI enabled)
- **Risk Assessment:** Potential challenges and mitigation strategies

Example:
```markdown
# Project Plan: HW-001

## Task Analysis
- Semantic Complexity: 1.5 (Very Low)
- Estimated Latency: 2,000 ms
- Estimated Tokens: 500

## Semantic Units
1. Function Definition (Complexity: 1.0)
   - Define hello_world() function
   - Add docstring

2. Implementation (Complexity: 0.5)
   - Print statement

## Risk Assessment
- Risks: None (trivial task)
```

#### 2. design.md - Design Specification

Contains:
- **Architecture:** High-level design decisions
- **Data Models:** Class/function signatures
- **API Design:** Input/output specifications
- **Security Considerations:** Identified security requirements

#### 3. design_review.md - Design Review Report

Contains:
- **Overall Assessment:** PASS / NEEDS_IMPROVEMENT / FAIL
- **6 Specialist Reviews:**
  - Security Review (OWASP Top 10, authentication)
  - Performance Review (caching, indexing)
  - Data Integrity Review (FK constraints, transactions)
  - Maintainability Review (coupling, cohesion)
  - Architecture Review (design patterns, SOLID)
  - API Design Review (RESTful principles, versioning)
- **Defects Found:** Severity, description, recommendation

#### 4. code_review.md - Code Review Report

Contains:
- **Overall Assessment:** PASS / NEEDS_IMPROVEMENT / FAIL
- **6 Specialist Reviews:**
  - Code Quality Review
  - Security Review
  - Performance Review
  - Best Practices Review
  - Test Coverage Review
  - Documentation Review
- **Defects Found:** With file, line number, and fix recommendations

#### 5. test_results.md - Test Report

Contains:
- **Build Status:** PASS / FAIL / BUILD_FAILED
- **Test Results:** Passed/failed tests with details
- **Coverage Metrics:** Code coverage percentage
- **Defect Log:** AI Defect Taxonomy classification
  - Defect type (8 categories)
  - Severity (Critical, High, Medium, Low)
  - Phase injected (Planning, Design, Code)
  - Root cause analysis

#### 6. postmortem.md - Performance Analysis

Contains:
- **Estimation Accuracy:** Planned vs. actual metrics
- **Quality Metrics:** Defect density, phase yield, phase distribution
- **Root Cause Analysis:** Top defect types by fix effort
- **Process Improvement Proposals (PIPs):** LLM-generated defensive changes

Example:
```markdown
# Postmortem Analysis: HW-001

## Performance Metrics
| Metric | Planned | Actual | Variance |
|--------|---------|--------|----------|
| Latency (ms) | 2,000 | 1,850 | -7.5% |
| Tokens | 500 | 485 | -3.0% |
| Cost (USD) | $0.010 | $0.009 | -10.0% |

## Quality Metrics
- Defects Found: 0
- Defect Density: 0.00 per semantic unit
- Phase Yield: 100% (no rework required)

## Process Improvement Proposals
None (task completed with high quality)
```

### Database Telemetry

All agent actions are logged to `data/asp_telemetry.db`:

```bash
# Explore telemetry data
sqlite3 data/asp_telemetry.db

# View cost data
SELECT agent_id, latency_ms, total_tokens, api_cost_usd
FROM agent_cost_vector
ORDER BY timestamp DESC
LIMIT 10;

# View defect data
SELECT defect_type, severity, phase_injected, fix_effort_ms
FROM defect_log_entry
ORDER BY severity DESC;

# View task summaries
SELECT task_id, status, total_latency_ms, total_cost_usd
FROM task_context
ORDER BY created_at DESC;
```

### Langfuse Dashboard

View real-time telemetry at [cloud.langfuse.com](https://cloud.langfuse.com):

- **Traces:** Complete execution flow for each task
- **Cost Analytics:** Token usage and API costs over time
- **Performance:** Latency distributions and bottlenecks
- **Error Tracking:** Failed agent executions with stack traces

---

## Troubleshooting

### Common Issues

#### 1. "ModuleNotFoundError: No module named 'asp'"

**Cause:** Virtual environment not activated or dependencies not installed

**Solution:**
```bash
# Reinstall dependencies
uv sync --all-extras

# Verify installation
uv run python -c "import asp; print('✓ ASP installed')"
```

#### 2. "AuthenticationError: Invalid API key"

**Cause:** Missing or incorrect Anthropic API key

**Solution:**
```bash
# Check environment variable
echo $ANTHROPIC_API_KEY

# If empty, set it
export ANTHROPIC_API_KEY="sk-ant-your-key-here"

# Or add to .env file
echo "ANTHROPIC_API_KEY=sk-ant-your-key-here" >> .env
```

#### 3. "Database not found: data/asp_telemetry.db"

**Cause:** Database not initialized

**Solution:**
```bash
# Initialize database
uv run python scripts/init_database.py --with-sample-data

# Verify database exists
ls -lh data/asp_telemetry.db
```

#### 4. "Langfuse connection failed"

**Cause:** Missing or incorrect Langfuse keys

**Solution:**
```bash
# Check environment variables
echo $LANGFUSE_PUBLIC_KEY
echo $LANGFUSE_SECRET_KEY
echo $LANGFUSE_HOST

# Set them if missing
export LANGFUSE_PUBLIC_KEY="pk-lf-your-key-here"
export LANGFUSE_SECRET_KEY="sk-lf-your-key-here"
export LANGFUSE_HOST="https://cloud.langfuse.com"
```

#### 5. "Tests failing with API errors"

**Cause:** Rate limiting or network issues

**Solution:**
```bash
# Run only unit tests (no API calls)
uv run pytest -m unit

# Run integration tests with retries
uv run pytest -m integration --retries 3
```

#### 6. "Out of disk space for artifacts"

**Cause:** Too many artifacts accumulated

**Solution:**
```bash
# Check artifact directory size
du -sh artifacts/

# Clean old artifacts (keep last 10 tasks)
ls -t artifacts/ | tail -n +11 | xargs -I {} rm -rf artifacts/{}
```

### Performance Issues

#### Slow Execution

**Cause:** Network latency, large tasks, or review overhead

**Solutions:**
- Use faster model for simple tasks: `DEFAULT_MODEL = "claude-haiku-4"`
- Skip review phases for prototyping (not recommended for production)
- Increase timeout: `TIMEOUT_SECONDS = 600`

#### High Costs

**Cause:** Complex tasks, inefficient prompts, or repeated failures

**Solutions:**
- Start with simpler tasks to build bootstrap data
- Review prompts for verbosity (agents may be over-generating)
- Check for retry loops in telemetry
- Use PROBE-AI estimation to predict costs before execution

### Getting Help

If you're still stuck:

1. **Check Documentation:**
   - [HITL Integration Guide](HITL_Integration.md) - Approval workflows
   - [Agent Reference](Agents_Reference.md) - Agent-specific troubleshooting
   - [Developer Guide](Developer_Guide.md) - Advanced configuration

2. **Search Issues:**
   - [GitHub Issues](https://github.com/evelynmitchell/Process_Software_Agents/issues)

3. **File a Bug Report:**
   - Include: OS, Python version, error message, minimal reproduction
   - Attach: Relevant artifacts, logs, telemetry data

---

## Next Steps

Now that you've completed your first task, explore more advanced features:

### 1. Configure HITL Approval Workflow

Learn how to add human approval for critical decisions:

→ **[HITL Integration Guide](HITL_Integration.md)**

### 2. Deep Dive into Agents

Understand how each of the 7 agents works and how to customize them:

→ **[Agent Reference Documentation](Agents_Reference.md)**

### 3. Extend and Customize ASP

Build custom agents, modify prompts, or integrate with your workflow:

→ **[Developer Guide](Developer_Guide.md)**

### 4. Explore API

Work with ASP programmatically using the Python API:

→ **[API Reference](API_Reference.md)**

### 5. Run Example Projects

Try more complex examples to see ASP's full capabilities:

```bash
# Run all examples
uv run python examples/hello_world.py
uv run python examples/rest_api_endpoint.py
uv run python examples/multi_file_refactor.py
uv run python examples/hitl_workflow.py
```

---

## Summary

You've successfully:

- ✅ Installed ASP Platform
- ✅ Configured API keys and database
- ✅ Ran your first task through the 7-agent pipeline
- ✅ Explored artifacts and telemetry
- ✅ Learned how to troubleshoot common issues

**You're ready to use ASP for autonomous software development!**

Key takeaways:
- ASP provides **complete observability** (artifacts + telemetry)
- **7 specialized agents** work together with quality gates
- **Costs are predictable** ($0.05 - $0.50 per typical task)
- **Bootstrap learning** improves performance over time
- **HITL workflows** enable safe autonomy

---

**Built with ASP Platform v1.0**

*Autonomy is earned through demonstrated reliability, not assumed.*
