# Test Plan Quick Start Guide

This guide provides quick instructions for executing the comprehensive test plan for all 21 agents in the ASP Platform.

## Prerequisites

### 1. Install Dependencies

```bash
pip install -e ".[dev]"
```

### 2. Set Environment Variables

```bash
export ANTHROPIC_API_KEY="your_anthropic_key_here"
export OPENAI_API_KEY="your_openai_key_here"
export LANGFUSE_PUBLIC_KEY="your_langfuse_public_key"
export LANGFUSE_SECRET_KEY="your_langfuse_secret_key"
export LANGFUSE_HOST="https://cloud.langfuse.com"
```

## Quick Test Execution

### Option 1: Using the Python Test Runner (Recommended)

```bash
# Run all tests
python scripts/run_agent_tests.py all

# Run tests incrementally (phase by phase)
python scripts/run_agent_tests.py incremental

# Run only core agents
python scripts/run_agent_tests.py core

# Run with coverage report
python scripts/run_agent_tests.py coverage
```

### Option 2: Using the Bash Test Runner

```bash
# Run all tests
./scripts/run_agent_tests.sh all

# Run tests incrementally (phase by phase)
./scripts/run_agent_tests.sh incremental

# Run only core agents
./scripts/run_agent_tests.sh core

# Run with coverage report
./scripts/run_agent_tests.sh coverage
```

### Option 3: Direct Pytest Commands

```bash
# Run all tests
pytest tests/ -v

# Run specific agent tests
pytest tests/unit/test_agents/test_planning_agent.py -v
pytest tests/unit/test_agents/test_design_agent.py -v

# Run with coverage
pytest tests/ --cov=src/asp --cov-report=html
```

## Available Commands

| Command | Description |
|---------|-------------|
| `all` | Run all tests (default) |
| `incremental` | Run tests phase by phase (recommended) |
| `core` | Test 7 core agents only |
| `orchestrators` | Test 2 orchestrator agents |
| `design-specialists` | Test 6 design review specialists |
| `code-specialists` | Test 6 code review specialists |
| `integration` | Run integration/E2E tests |
| `performance` | Run performance tests |
| `unit` | Run all unit tests |
| `e2e` | Run all E2E tests |
| `coverage` | Run with coverage report |
| `help` | Show help message |

## Test Phases (Incremental Mode)

When running in incremental mode, tests execute in 6 phases:

### Phase 1: Core Agents (7 agents)
- Planning Agent (FR-1)
- Design Agent (FR-2)
- Design Review Agent (FR-3)
- Code Agent (FR-4)
- Code Review Agent (FR-5)
- Test Agent (FR-6)
- Postmortem Agent (FR-7)

### Phase 2: Orchestrators (2 agents)
- Design Review Orchestrator
- Code Review Orchestrator

### Phase 3: Design Review Specialists (6 agents)
- Security Review Agent
- Performance Review Agent
- Data Integrity Review Agent
- Maintainability Review Agent
- Architecture Review Agent
- API Design Review Agent

### Phase 4: Code Review Specialists (6 agents)
- Code Quality Review Agent
- Code Security Review Agent
- Code Performance Review Agent
- Test Coverage Review Agent
- Documentation Review Agent
- Best Practices Review Agent

### Phase 5: Integration Tests
- End-to-end workflow tests
- Agent-to-agent interaction tests

### Phase 6: Performance Tests
- Latency benchmarks
- Cost benchmarks
- Parallel execution performance

## Expected Test Counts

- **Planning Agent**: 110 tests (102 unit + 8 E2E)
- **Design Agent**: 28 tests (23 unit + 5 E2E)
- **Design Review Agent**: 24 tests (21 unit + 3 E2E)
- **Other Core Agents**: Unit tests + E2E tests
- **Total**: 200+ tests across all agents

## Viewing Results

### Terminal Output
Test results are displayed in the terminal with color-coded output:
- ✓ Green: Tests passed
- ✗ Red: Tests failed
- ➜ Yellow: Info messages

### Coverage Report
After running with coverage, open the HTML report:

```bash
# Generate coverage report
python scripts/run_agent_tests.py coverage

# Open in browser (Linux)
xdg-open htmlcov/index.html

# Open in browser (macOS)
open htmlcov/index.html

# Open in browser (Windows)
start htmlcov/index.html
```

## Troubleshooting

### Missing Environment Variables
If you see an error about missing environment variables:

```bash
✗ Missing environment variables: ANTHROPIC_API_KEY, OPENAI_API_KEY
```

Solution: Set the required environment variables (see Prerequisites section)

### Tests Failing
If tests fail, check:

1. **Dependencies installed**: `pip install -e ".[dev]"`
2. **API keys valid**: Ensure your API keys are correct and active
3. **Langfuse accessible**: Check that Langfuse is reachable
4. **Test data available**: Ensure bootstrap data exists in `bootstrap_data/`

### Import Errors
If you see import errors:

```bash
ModuleNotFoundError: No module named 'asp'
```

Solution: Install the package in editable mode:

```bash
pip install -e .
```

## Common Use Cases

### 1. Quick Validation (Core Agents Only)
```bash
python scripts/run_agent_tests.py core
```

### 2. Full Test Suite Before PR
```bash
python scripts/run_agent_tests.py coverage
```

### 3. Testing After Code Changes
```bash
# Test affected agent only
pytest tests/unit/test_agents/test_planning_agent.py -v

# Then run full suite
python scripts/run_agent_tests.py incremental
```

### 4. Performance Validation
```bash
python scripts/run_agent_tests.py performance
```

### 5. Integration Testing
```bash
python scripts/run_agent_tests.py integration
```

## Success Criteria

All tests should pass with:
- ✅ **Unit tests**: > 95% pass rate
- ✅ **Integration tests**: 100% pass rate
- ✅ **Code coverage**: > 90%
- ✅ **Performance**: Within expected ranges

## Next Steps

After running tests:

1. **Review coverage report**: Check for untested code paths
2. **Check Langfuse**: Verify telemetry data is being collected
3. **Review test output**: Look for warnings or deprecations
4. **Update documentation**: If tests reveal gaps in documentation

## Additional Resources

- **Full Test Plan**: See `docs/comprehensive_agent_test_plan.md`
- **Test Implementation Plan**: See `docs/test_implementation_plan.md`
- **Test Coverage Analysis**: See `docs/test_coverage_analysis.md`
- **CI/CD Integration**: See `.github/workflows/test_all_agents.yml` (if exists)

## Getting Help

If you encounter issues:

1. Check the full test plan documentation
2. Review test output for specific error messages
3. Verify all prerequisites are met
4. Check that all 21 agents are properly implemented

---

**Last Updated**: 2025-11-19
**Test Plan Version**: 1.0.0
**Total Agents**: 21 (7 core + 2 orchestrators + 12 specialists)
