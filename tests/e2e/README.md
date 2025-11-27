# End-to-End (E2E) Tests

This directory contains end-to-end tests that validate the complete Planning Agent workflow.

**New in 2025-11-27:** E2E tests now support two modes:
- **Real API Mode:** Uses actual Anthropic Claude API when `ANTHROPIC_API_KEY` is set
- **Mock Mode:** Uses mock LLM client when API key is not available (no cost, validates structure/flow)

## Setup

### 1. Set API Key (Optional for Mock Mode)

For real API testing, set the Anthropic API key using one of these methods:

**Option A: GitHub Codespaces Secrets (Recommended)**
1. Go to: https://github.com/settings/codespaces
2. Add repository secret: `ANTHROPIC_API_KEY`
3. Value: Your Anthropic API key (starts with `sk-ant-`)
4. Restart your Codespace for the secret to be available

**Option B: Local Environment Variable**
```bash
export ANTHROPIC_API_KEY="sk-ant-your-key-here"
```

**Option C: .env File (Local Development)**
```bash
cp ../.env.example ../.env
# Edit .env and uncomment/set ANTHROPIC_API_KEY
```

### 2. Verify Setup

```bash
# Check if API key is available
echo $ANTHROPIC_API_KEY

# Should show: sk-ant-... (not empty)
```

## Running E2E Tests

### Run All E2E Tests
```bash
# From project root
uv run pytest tests/e2e/ -v -s -m e2e
```

### Run Individual Tests
```bash
# Simple task decomposition
uv run pytest tests/e2e/test_planning_agent_e2e.py::TestPlanningAgentE2E::test_simple_task_decomposition -v -s

# Moderate complexity task
uv run pytest tests/e2e/test_planning_agent_e2e.py::TestPlanningAgentE2E::test_moderate_complexity_task -v -s

# Complex data pipeline
uv run pytest tests/e2e/test_planning_agent_e2e.py::TestPlanningAgentE2E::test_complex_data_pipeline_task -v -s
```

### Run Calibration Tests
```bash
# These tests validate complexity scoring calibration
uv run pytest tests/e2e/ -v -s -m calibration
```

## Test Categories

### Basic E2E Tests
- `test_simple_task_decomposition` - Simple REST API endpoint
- `test_moderate_complexity_task` - JWT authentication system
- `test_with_context_files` - Task with context files specified
- `test_complex_data_pipeline_task` - Complex ETL pipeline
- `test_telemetry_integration` - Validates telemetry capture

### Calibration Tests
- `test_trivial_task_complexity` - Expected: < 10 complexity
- `test_simple_task_complexity` - Expected: 11-30 complexity
- `test_moderate_task_complexity` - Expected: 31-60 complexity

## Cost Considerations

**Mock Mode (No API Key):** FREE - No API calls are made

**Real API Mode (With API Key):**
- **Per test:** ~$0.01-0.02 USD
- **Full suite:** ~$0.10-0.15 USD
- **Model used:** claude-sonnet-4-20250514

**Recommendation:** Use mock mode for development and CI, use real API mode for calibration and validation.

## Test Output

E2E tests print detailed output including:
- Number of semantic units created
- Total complexity score
- Individual unit details with complexity factors
- Dependency graph (for complex tasks)

Example output:
```
============================================================
E2E Test: JWT Authentication System
============================================================
Units created: 5
Total complexity: 112

Semantic Units:

1. SU-001: Create user registration endpoint with validation
   Complexity: 43
   Factors: API=2, Data=3, Branches=4, Entities=3, Novelty=1.0
   Dependencies: None

2. SU-002: Implement password hashing with bcrypt
   Complexity: 26
   Factors: API=1, Data=2, Branches=2, Entities=2, Novelty=1.0
   Dependencies: SU-001
...
```

## Troubleshooting

### Tests Running in Mock Mode vs Real API Mode
- **How to check:** Tests will automatically use mock mode if no API key is set
- **Mock Mode:** Returns pre-defined responses, validates structure and flow
- **Real API Mode:** Makes actual API calls, validates LLM reasoning quality
- **To force Real API Mode:** Set the `ANTHROPIC_API_KEY` environment variable

### ValidationError: "String should match pattern '^SU-\d{3}$'" (Real API Mode)
- **Cause:** LLM returned non-standard unit IDs
- **Fix:** This is expected occasionally; retry the test
- **Note:** Prompt includes format examples to minimize this

### Cost Concerns
- Run individual tests instead of full suite
- Use mock tests in `tests/unit/` for development
- Reserve E2E tests for validation and calibration

## Next Steps

After running E2E tests:
1. Review complexity scores for calibration
2. Check telemetry in Langfuse dashboard
3. Query SQLite database: `uv run python scripts/query_telemetry.py`
4. Adjust C1 formula weights if needed (see PRD Section 13.1)
