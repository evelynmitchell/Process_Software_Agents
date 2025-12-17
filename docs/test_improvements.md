# Test Improvements Backlog

**Created:** 2025-12-16
**Source:** Unit test evaluation (Session 9)
**Priority Levels:** P0 (Critical), P1 (High), P2 (Medium), P3 (Low)

---

## Overview

This document tracks actionable improvements identified during unit test quality evaluation. Items are organized by priority and include specific file locations and recommended fixes.

**Current Test Quality Score:** 4.5/5 (Excellent)
**Target Score:** 4.8/5

---

## P1: High Priority

### TI-001: Replace os.chdir() in test_git_utils.py

**Status:** Open
**Severity:** High (affects parallel execution)
**File:** `tests/unit/test_utils/test_git_utils.py`
**Lines Affected:** 26 occurrences throughout file

**Problem:**
Using `os.chdir()` modifies global process state, which:
- Breaks parallel test execution (`pytest -n auto`)
- Can cause cascading failures if cleanup fails
- Makes tests order-dependent

**Current Code (example):**
```python
def test_returns_true_for_git_repo(self, git_repo):
    original_cwd = os.getcwd()
    try:
        os.chdir(git_repo)
        assert is_git_repository() is True
    finally:
        os.chdir(original_cwd)
```

**Recommended Fix:**
Option A - Modify functions to accept path parameter:
```python
def is_git_repository(path: Path | None = None) -> bool:
    """Check if path (default: cwd) is a git repo."""
    cmd = ["git", "rev-parse", "--git-dir"]
    if path:
        cmd = ["git", "-C", str(path)] + cmd[1:]
    # ...
```

Option B - Use subprocess cwd parameter in tests:
```python
def test_returns_true_for_git_repo(self, git_repo):
    result = subprocess.run(
        ["git", "-C", str(git_repo), "rev-parse", "--git-dir"],
        capture_output=True
    )
    assert result.returncode == 0
```

**Estimated Effort:** 2-3 hours
**Impact:** Enables parallel test execution, improves reliability

---

### TI-002: Refactor private method tests in test_test_executor.py

**Status:** Open
**Severity:** Medium (technical debt)
**File:** `tests/unit/test_services/test_test_executor.py`
**Lines Affected:** 340-450 (framework detection and command building tests)

**Problem:**
Tests directly call `_detect_framework()` and `_build_command()` private methods, coupling tests to implementation details.

**Current Code:**
```python
def test_detect_framework_pytest_ini(self, executor, workspace):
    (workspace.target_repo_path / "pytest.ini").write_text("[pytest]")
    framework = executor._detect_framework(workspace)
    assert framework == "pytest"
```

**Recommended Fix:**
Test through public `run_tests()` interface:
```python
def test_run_tests_uses_pytest_when_pytest_ini_present(self, executor, mock_sandbox, workspace):
    (workspace.target_repo_path / "pytest.ini").write_text("[pytest]")
    mock_sandbox.execute.return_value = ExecutionResult(exit_code=0, stdout="1 passed")

    executor.run_tests(workspace)

    call_args = mock_sandbox.execute.call_args
    command = call_args[0][1]
    assert "pytest" in command
```

**Estimated Effort:** 1-2 hours
**Impact:** Tests survive refactoring, better behavioral focus

---

### TI-003: Refactor private method tests in test_llm_client.py

**Status:** Open
**Severity:** Medium (technical debt)
**File:** `tests/unit/test_utils/test_llm_client.py`
**Lines Affected:** 503-544 (`_try_parse_json` tests)

**Problem:**
Direct testing of `_try_parse_json()` private method.

**Current Code:**
```python
def test_try_parse_json_valid_object(self):
    client = LLMClient(api_key="test-key")
    result = client._try_parse_json('{"key": "value"}')
```

**Recommended Fix:**
Option A - Test through `call_with_retry()`:
```python
def test_call_with_retry_parses_json_response(self):
    # Mock returns JSON, verify it's parsed
    mock_response.content = [Mock(text='{"key": "value"}')]
    result = client.call_with_retry(prompt="Test")
    assert isinstance(result["content"], dict)
```

Option B - Extract JSON parsing to a utility function:
```python
# In asp/utils/json_parser.py
def try_parse_json(text: str) -> dict | list | str:
    """Public utility for JSON parsing."""

# Tests can now test the public utility
```

**Estimated Effort:** 1 hour
**Impact:** Better separation of concerns

---

## P2: Medium Priority

### TI-004: Add dependency injection to PlanningDesignOrchestrator

**Status:** Open
**Severity:** Medium (testability)
**File:** `src/asp/orchestrators/planning_design_orchestrator.py`
**Related Test:** `tests/unit/test_orchestrators/test_orchestrator.py`

**Problem:**
Tests inject mocks via private attributes:
```python
orchestrator._planning_agent = mock_planning_agent
```

**Recommended Fix:**
Add constructor injection:
```python
class PlanningDesignOrchestrator:
    def __init__(
        self,
        planning_agent: PlanningAgent | None = None,
        design_agent: DesignAgent | None = None,
        review_agent: DesignReviewAgent | None = None,
    ):
        self._planning_agent = planning_agent
        self._design_agent = design_agent
        self._design_review_agent = review_agent
```

**Estimated Effort:** 1 hour
**Impact:** Cleaner tests, better design

---

### TI-005: Evaluate remaining test files

**Status:** Open
**Severity:** Low (completeness)
**Files:** See list below

**Problem:**
Only 6 of ~50 unit test files have been evaluated against the rubric.

**Files Not Yet Evaluated:**
- `tests/unit/test_agents/reviews/*.py` (~6 files)
- `tests/unit/test_web/*.py` (~6 files)
- `tests/unit/test_approval/*.py` (~4 files)
- `tests/unit/test_telemetry/*.py` (~2 files)
- `tests/unit/test_parsers/*.py` (~1 file)
- `tests/unit/test_advanced/*.py` (~2 files)
- `tests/unit/test_cli/*.py` (~1 file)

**Recommended Fix:**
Evaluate remaining files in batches, update `tests/test_quality_scores.yaml`.

**Estimated Effort:** 2-3 hours
**Impact:** Complete quality visibility

---

### TI-006: Add property-based testing for model validation

**Status:** Open
**Severity:** Low (enhancement)
**File:** `tests/unit/test_models/*.py`

**Problem:**
Model tests use explicit examples; property-based testing could find edge cases automatically.

**Recommended Fix:**
Add hypothesis tests for Pydantic models:
```python
from hypothesis import given, strategies as st

@given(st.text(min_size=3))
def test_task_id_accepts_any_string_min_3_chars(task_id):
    # Will find edge cases like unicode, newlines, etc.
    model = DesignInput(task_id=task_id, ...)
    assert model.task_id == task_id
```

**Estimated Effort:** 2 hours
**Impact:** Better edge case coverage

---

## P3: Low Priority

### TI-007: Add type hints to test helper functions

**Status:** Open
**Severity:** Low (code quality)
**Files:** Various test files

**Problem:**
Helper functions like `make_semantic_unit()`, `make_component_logic()` lack type hints.

**Recommended Fix:**
```python
def make_semantic_unit(
    unit_id: str = "SU-001",
    description: str = "Create API endpoint...",
) -> SemanticUnit:
```

**Estimated Effort:** 30 minutes
**Impact:** Better IDE support, documentation

---

### TI-008: Add pytest markers for test categorization

**Status:** Open
**Severity:** Low (organization)
**Files:** All test files

**Problem:**
No consistent markers for slow tests, integration tests, etc.

**Recommended Fix:**
Add to `pytest.ini`:
```ini
[pytest]
markers =
    slow: marks tests as slow (deselect with '-m "not slow"')
    integration: marks tests as integration tests
    unit: marks tests as unit tests
```

Apply markers:
```python
@pytest.mark.slow
@pytest.mark.integration
def test_real_git_operations():
    ...
```

**Estimated Effort:** 1 hour
**Impact:** Better test selection, faster CI feedback

---

## Completed Items

*(Move items here when done)*

| ID | Description | Completed | Notes |
|----|-------------|-----------|-------|
| - | - | - | - |

---

## Progress Tracking

| Priority | Total | Open | In Progress | Done |
|----------|-------|------|-------------|------|
| P1 | 3 | 3 | 0 | 0 |
| P2 | 3 | 3 | 0 | 0 |
| P3 | 2 | 2 | 0 | 0 |
| **Total** | **8** | **8** | **0** | **0** |

---

## Related Documents

- `docs/unit_test_evaluation_rubric.md` - Quality rubric
- `docs/unit_test_evaluation_results.md` - Evaluation details
- `tests/test_quality_scores.yaml` - Machine-readable scores
- `Summary/lessons_learned_unit_test_antipatterns.md` - Anti-patterns guide
