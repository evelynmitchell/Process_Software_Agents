# ASP Platform Examples

This directory contains runnable examples demonstrating various features of the ASP Platform.

---

## Quick Start

Run any example with:

```bash
uv run python examples/<example_name>.py
```

**Prerequisites:**
- API keys configured (see [Getting Started Guide](../docs/Getting_Started.md))
- Database initialized: `uv run python scripts/init_database.py`

---

## Examples

### 1. Hello World (`hello_world.py`)

**Purpose:** Demonstrate complete 7-agent pipeline with trivial task

**What it does:**
- Runs full ASP pipeline (Planning → Design → Code → Test → Postmortem)
- Creates a simple "Hello, World!" function
- Shows performance metrics and artifacts

**Run:**
```bash
uv run python examples/hello_world.py
```

**Cost:** ~$0.08 - $0.15
**Time:** ~45 seconds
**Complexity:** Beginner

**Learn:**
- Basic ASP workflow
- Artifact structure
- Performance metrics
- Quality gates

---

### 2. REST API Endpoint (`rest_api_endpoint.py`)

**Purpose:** Demonstrate ASP with medium-complexity task

**What it does:**
- Creates FastAPI endpoint with validation
- Includes error handling and security (bcrypt)
- Generates comprehensive tests
- Shows phase-by-phase breakdown

**Run:**
```bash
uv run python examples/rest_api_endpoint.py
```

**Cost:** ~$0.25 - $0.50
**Time:** ~2 minutes
**Complexity:** Intermediate

**Learn:**
- Multi-file code generation
- Security reviews
- Validation logic
- Error handling patterns

---

### 3. HITL Workflow (`hitl_workflow.py`)

**Purpose:** Demonstrate Human-In-The-Loop approval

**What it does:**
- Creates task with intentional security gap
- Triggers quality gate failure
- Prompts for human approval (APPROVE/REJECT/DEFER)
- Shows audit trail in git notes

**Run:**
```bash
# Requires git repository
git init  # If not already initialized
uv run python examples/hitl_workflow.py
```

**Cost:** ~$0.15 - $0.30
**Time:** ~1 minute + approval time
**Complexity:** Advanced

**Learn:**
- HITL approval workflow
- Local PR-style reviews
- Quality gate overrides
- Audit trails

---

### 4. Telemetry Analysis (`telemetry_analysis.py`)

**Purpose:** Demonstrate telemetry querying and analysis

**What it does:**
- Queries SQLite telemetry database
- Shows cost breakdown by agent
- Analyzes defect patterns
- Tracks bootstrap learning progress

**Run:**
```bash
uv run python examples/telemetry_analysis.py
```

**Cost:** $0 (no API calls)
**Time:** < 1 second
**Complexity:** Beginner

**Learn:**
- Telemetry database queries
- Cost analysis
- Defect tracking
- Bootstrap learning metrics

---

## Example Workflow

Recommended order for learning:

1. **Start with Hello World** - Understand basic workflow
   ```bash
   uv run python examples/hello_world.py
   ```

2. **Try REST API** - See more complex task
   ```bash
   uv run python examples/rest_api_endpoint.py
   ```

3. **Analyze Telemetry** - Review collected data
   ```bash
   uv run python examples/telemetry_analysis.py
   ```

4. **Enable HITL** - Add human oversight
   ```bash
   uv run python examples/hitl_workflow.py
   ```

---

## Common Issues

### "ModuleNotFoundError: No module named 'asp'"

**Solution:**
```bash
# Install dependencies
uv sync --all-extras

# Verify installation
uv run python -c "import asp; print('✓ ASP installed')"
```

### "AuthenticationError: Invalid API key"

**Solution:**
```bash
# Check environment variable
echo $ANTHROPIC_API_KEY

# Set if missing
export ANTHROPIC_API_KEY="sk-ant-your-key-here"
```

### "Database not found: data/asp_telemetry.db"

**Solution:**
```bash
# Initialize database
uv run python scripts/init_database.py --with-sample-data
```

### HITL example: "Not a git repository"

**Solution:**
```bash
# Initialize git
git init
git add .
git commit -m "Initial commit"

# Now run HITL example
uv run python examples/hitl_workflow.py
```

---

## Cost Budgeting

Estimated costs for running all examples:

| Example | Cost | Tokens | Time |
|---------|------|--------|------|
| Hello World | $0.08-$0.15 | ~8k | 45s |
| REST API | $0.25-$0.50 | ~20k | 2m |
| HITL Workflow | $0.15-$0.30 | ~12k | 1m + approval |
| Telemetry | $0 | 0 | <1s |
| **Total** | **~$0.50-$1.00** | **~40k** | **~5m** |

**Note:** Costs are approximate and vary based on:
- Task complexity
- Model used (Sonnet vs Haiku)
- Number of quality gate iterations
- Review defects found

---

## Next Steps

After running examples:

1. **Review Artifacts** - Check `artifacts/` directory for generated outputs
2. **Query Telemetry** - Explore `data/asp_telemetry.db` for metrics
3. **View Traces** - Visit [Langfuse Cloud](https://cloud.langfuse.com) for detailed traces
4. **Read Docs:**
   - [Getting Started Guide](../docs/Getting_Started.md)
   - [Agent Reference](../docs/Agents_Reference.md)
   - [HITL Integration](../docs/HITL_Integration.md)
   - [Developer Guide](../docs/Developer_Guide.md)
5. **Build Your Own** - Create custom agents or orchestrators

---

## Additional Examples

For more examples, see:

- **Test Suite:** `tests/e2e/` directory for end-to-end examples
- **Scripts:** `scripts/` directory for utility examples
- **Artifacts:** `artifacts/` directory for real task outputs

---

## Contributing Examples

Want to add an example? Follow these guidelines:

1. **Purpose:** Clear, focused demonstration of one feature
2. **Documentation:** Inline comments + docstring
3. **Error Handling:** Graceful failures with helpful messages
4. **Output:** Clear, formatted console output
5. **Cost:** Document estimated cost and time
6. **Runnable:** Self-contained with minimal dependencies

Submit via PR with:
- Example file: `examples/your_example.py`
- Entry in this README
- Test run verification

---

**Built with ASP Platform v1.0**

*Learn by doing.*
