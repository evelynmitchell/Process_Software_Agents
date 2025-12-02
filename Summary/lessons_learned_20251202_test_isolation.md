# Lessons Learned: Test Isolation and Debugging Efficiency

**Date:** 2025-12-02
**Session:** 9
**Issue:** Web UI tests failing in CI/CD due to improper test isolation

---

## Summary

Three tests in the web UI test suite were failing because they weren't properly isolated from production data. The debugging process also revealed inefficiencies in how the investigation was conducted.

## Root Cause Analysis

### The Bug

The `get_recent_activity()` function in `src/asp/web/data.py` has a **dual data source pattern**:

```python
def get_recent_activity(limit: int = 10) -> list[dict[str, Any]]:
    activities = []

    # Primary source: telemetry database
    conn = _get_db_connection()
    if conn:
        # ... fetch from DB ...

    # Fallback source: artifact file modification times
    if not activities and ARTIFACTS_DIR.exists():
        # ... fetch from artifacts ...

    return activities
```

The tests only mocked `ARTIFACTS_DIR`, assuming that was the data source. But when a real telemetry database exists at `TELEMETRY_DB`, the function returns real data instead of using the test fixtures.

### The Investigation Inefficiency

The initial debugging approach wasted time:
1. Ran full test suite which timed out (~4+ minutes)
2. Repeatedly polled background process waiting for output
3. Eventually killed the process and ran targeted tests

## Lessons Learned

### 1. Run Targeted Tests First

**Before:**
```bash
uv run pytest tests/ -v --tb=short  # Full suite - times out
```

**After:**
```bash
uv run pytest tests/test_web_ui.py tests/unit/test_web/ -v --no-cov  # Targeted - 3 seconds
```

When CI fails, identify the failing tests from CI logs and run only those locally.

### 2. Read the Function Under Test Before the Test

Before debugging a failing test, read the source code being tested. The dual data source pattern in `get_recent_activity()` is obvious when reading the function:

```python
# Line 305-306: Primary source
conn = _get_db_connection()
if conn:
    # ...

# Line 348: Fallback only if primary returned nothing
if not activities and ARTIFACTS_DIR.exists():
```

### 3. Mock All Data Sources, Not Just One

When a function has multiple data sources, tests must mock all of them:

**Incomplete (fails):**
```python
monkeypatch.setattr(data_module, "ARTIFACTS_DIR", tmp_path / "nonexistent")
```

**Complete (passes):**
```python
monkeypatch.setattr(data_module, "ARTIFACTS_DIR", tmp_path / "nonexistent")
monkeypatch.setattr(data_module, "TELEMETRY_DB", tmp_path / "nonexistent.db")
```

### 4. Look for Consistency in Existing Tests

Other tests in the same file properly mocked their data sources:

```python
# TestGetAgentStats properly mocks BOOTSTRAP_RESULTS
monkeypatch.setattr(data_module, "BOOTSTRAP_RESULTS", tmp_path / "nonexistent.json")
```

When tests are inconsistent in their mocking patterns, it's a code smell indicating incomplete isolation.

### 5. Use `--no-cov` for Faster Feedback

Coverage collection adds overhead. When debugging, skip it:

```bash
uv run pytest tests/unit/test_web/ -v --tb=short --no-cov  # 1.5 seconds
uv run pytest tests/unit/test_web/ -v --tb=short           # 7+ seconds with coverage
```

### 6. Prefer `--tb=short` or `--tb=long` Over Default

The default traceback can be verbose. Use:
- `--tb=short` for quick iteration
- `--tb=long` when you need full context
- `--tb=line` for summary view of many failures

## Prevention Strategies

### For Test Authors

1. **Audit data sources** - Before writing a test, identify ALL external data sources the function uses
2. **Use fixtures for common mocks** - Create a pytest fixture that mocks all data layer paths:

```python
@pytest.fixture
def isolated_data_layer(tmp_path, monkeypatch):
    """Isolate tests from production data."""
    import asp.web.data as data_module
    monkeypatch.setattr(data_module, "ARTIFACTS_DIR", tmp_path / "artifacts")
    monkeypatch.setattr(data_module, "TELEMETRY_DB", tmp_path / "telemetry.db")
    monkeypatch.setattr(data_module, "BOOTSTRAP_RESULTS", tmp_path / "bootstrap.json")
    monkeypatch.setattr(data_module, "DATA_DIR", tmp_path / "data")
    return tmp_path
```

3. **Test in CI-like environment** - Run tests with `--forked` or in containers to catch isolation issues

### For Code Reviewers

1. Check that new tests mock all relevant data sources
2. Verify tests pass in a clean environment (no local data)
3. Look for functions with fallback patterns - they need extra mocking

## Checklist for Future Test Debugging

- [ ] Identify specific failing tests from CI logs
- [ ] Run only those tests locally with `--no-cov --tb=short`
- [ ] Read the source function being tested
- [ ] Identify all data sources (DB, files, APIs, module-level constants)
- [ ] Verify test mocks all data sources
- [ ] Check similar tests for consistent mocking patterns
- [ ] Run tests in isolation to confirm fix

## Related Files

- `src/asp/web/data.py` - Data access layer with multiple sources
- `tests/unit/test_web/test_data.py` - Unit tests for data layer
- `tests/test_web_ui.py` - Integration tests for web UI routes
