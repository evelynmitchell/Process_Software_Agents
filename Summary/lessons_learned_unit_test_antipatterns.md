# Unit Test Anti-Patterns and Lessons Learned

**Date:** 2025-12-16
**Source:** Unit test evaluation (Session 9)
**Related Documents:**
- `docs/unit_test_evaluation_rubric.md` - Formal rubric
- `docs/unit_test_evaluation_results.md` - Detailed evaluation
- `tests/test_quality_scores.yaml` - Machine-readable scores

---

## Overview

This document captures anti-patterns discovered during unit test evaluation and provides guidance for avoiding them in future development.

---

## Anti-Pattern 1: Testing Private Methods Directly

### Symptom
Tests directly call methods with underscore prefixes: `object._method_name()`

### Why It's Problematic
- **Couples tests to implementation**: Refactoring internal logic breaks tests even when behavior is unchanged
- **Tests don't reflect user perspective**: Private methods are implementation details, not contracts
- **Maintenance burden**: Every internal change requires test updates

### Examples Found

**test_test_executor.py** (lines 340-450):
```python
# BAD: Testing private method directly
def test_detect_framework_pytest_ini(self, executor, workspace):
    (workspace.target_repo_path / "pytest.ini").write_text("[pytest]")
    framework = executor._detect_framework(workspace)  # Private!
    assert framework == "pytest"
```

**test_llm_client.py** (lines 503-544):
```python
# BAD: Testing private JSON parser directly
def test_try_parse_json_valid_object(self):
    client = LLMClient(api_key="test-key")
    result = client._try_parse_json('{"key": "value"}')  # Private!
```

### Better Approach

Test through public interfaces that use the private method:

```python
# GOOD: Test behavior through public interface
def test_run_tests_detects_pytest_framework(self, executor, workspace):
    (workspace.target_repo_path / "pytest.ini").write_text("[pytest]")
    result = executor.run_tests(workspace)  # Public interface
    # Framework detection happens internally, we verify the outcome
    assert "pytest" in result.raw_output or result.framework == "pytest"
```

### Files Affected
- `tests/unit/test_services/test_test_executor.py`
- `tests/unit/test_utils/test_llm_client.py`
- `tests/unit/test_orchestrators/test_orchestrator.py`
- `tests/unit/test_agents/test_base_agent.py`

---

## Anti-Pattern 2: Global State Mutation (os.chdir)

### Symptom
Tests call `os.chdir()` to change the working directory

### Why It's Problematic
- **Breaks parallel execution**: Multiple tests changing directory simultaneously cause race conditions
- **Affects other tests**: If cleanup fails, subsequent tests run from wrong directory
- **Hard to debug**: Failures may not reproduce in isolation

### Examples Found

**test_git_utils.py** (26 occurrences):
```python
# BAD: Changing global working directory
def test_returns_true_for_git_repo(self, git_repo):
    original_cwd = os.getcwd()
    try:
        os.chdir(git_repo)  # Affects global state!
        assert is_git_repository() is True
    finally:
        os.chdir(original_cwd)
```

### Better Approach

Use `subprocess` with `cwd` parameter or `git -C`:

```python
# GOOD: Use subprocess cwd parameter
def test_returns_true_for_git_repo(self, git_repo):
    result = subprocess.run(
        ["git", "rev-parse", "--git-dir"],
        cwd=git_repo,  # No global state change
        capture_output=True
    )
    assert result.returncode == 0

# GOOD: Use git -C flag
def test_returns_true_for_git_repo(self, git_repo):
    result = subprocess.run(
        ["git", "-C", str(git_repo), "rev-parse", "--git-dir"],
        capture_output=True
    )
    assert result.returncode == 0
```

### Alternative: Modify the Function Under Test

If the function doesn't support a `cwd` parameter, consider adding one:

```python
# Before
def is_git_repository() -> bool:
    """Check if current directory is a git repo."""

# After
def is_git_repository(path: Path | None = None) -> bool:
    """Check if path (default: cwd) is a git repo."""
```

### Files Affected
- `tests/unit/test_utils/test_git_utils.py`

---

## Anti-Pattern 3: Mocking Private Attributes for Dependency Injection

### Symptom
Tests directly assign to private attributes to inject mocks: `orchestrator._agent = Mock()`

### Why It's Problematic
- **Bypasses initialization logic**: May miss validation or setup in constructors
- **Fragile to refactoring**: Renaming internal attributes breaks tests
- **Indicates design issue**: If mocking is hard, the class may need refactoring

### Examples Found

**test_orchestrator.py** (lines 119-121, 215-217):
```python
# BAD: Injecting mocks via private attributes
orchestrator = PlanningDesignOrchestrator()
orchestrator._planning_agent = mock_planning_agent  # Private!
orchestrator._design_agent = mock_design_agent      # Private!
orchestrator._design_review_agent = mock_review_agent  # Private!
```

### Better Approach

Use constructor injection:

```python
# GOOD: Constructor injection
class PlanningDesignOrchestrator:
    def __init__(
        self,
        planning_agent: PlanningAgent | None = None,
        design_agent: DesignAgent | None = None,
        review_agent: DesignReviewAgent | None = None,
    ):
        self.planning_agent = planning_agent or PlanningAgent()
        # ...

# Test becomes cleaner
def test_simple_pass(self):
    orchestrator = PlanningDesignOrchestrator(
        planning_agent=mock_planning_agent,
        design_agent=mock_design_agent,
        review_agent=mock_review_agent,
    )
```

### Files Affected
- `tests/unit/test_orchestrators/test_orchestrator.py`

---

## Anti-Pattern 4: Real External Calls in Unit Tests

### Symptom
Unit tests make real network, database, or filesystem calls

### Why It's Problematic
- **Slow**: External calls are orders of magnitude slower than in-memory operations
- **Flaky**: Network issues, database state, or file permissions cause random failures
- **Not isolated**: Tests depend on external system state

### Examples Found

**test_git_utils.py**:
```python
# BORDERLINE: Real git subprocess calls
# This is acceptable for integration testing git behavior,
# but should be clearly marked and separated from unit tests
subprocess.run(["git", "init"], cwd=repo_dir, check=True)
```

### Better Approach

For unit tests, mock external dependencies:

```python
# GOOD: Mock external dependency
def test_git_add_files(self, mocker):
    mock_run = mocker.patch("subprocess.run")
    mock_run.return_value = Mock(returncode=0)

    git_add_files(["file.txt"])

    mock_run.assert_called_once()
    assert "git" in mock_run.call_args[0][0]
    assert "add" in mock_run.call_args[0][0]
```

For integration tests, mark them appropriately:

```python
@pytest.mark.integration
@pytest.mark.slow
def test_real_git_operations(self, tmp_path):
    """Integration test - requires real git."""
    # Real git calls OK here, but separated from unit tests
```

---

## Anti-Pattern 5: Overly Specific Assertions

### Symptom
Tests assert on exact error messages, timestamps, or generated IDs

### Why It's Problematic
- **Brittle**: Minor message changes break tests
- **False positives**: Tests fail even when behavior is correct
- **Maintenance burden**: Every text change requires test updates

### Examples (Hypothetical - not found in codebase)

```python
# BAD: Exact message assertion
def test_validation_error():
    with pytest.raises(ValidationError) as exc:
        validate(None)
    assert str(exc.value) == "Field 'name' is required and cannot be None"

# BAD: Exact timestamp assertion
def test_created_at():
    user = User.create("test")
    assert user.created_at == "2025-12-16T10:30:00Z"  # Will fail in 1 second
```

### Better Approach

```python
# GOOD: Assert on type and key properties
def test_validation_error():
    with pytest.raises(ValidationError) as exc:
        validate(None)
    assert "required" in str(exc.value).lower()
    assert "name" in str(exc.value)

# GOOD: Assert on relative time or type
def test_created_at():
    before = datetime.now()
    user = User.create("test")
    after = datetime.now()
    assert before <= user.created_at <= after
```

---

## Summary Table

| Anti-Pattern | Severity | Occurrences | Primary Fix |
|--------------|----------|-------------|-------------|
| Testing Private Methods | Medium | 4 files | Test through public interface |
| Global State (os.chdir) | High | 1 file (26 uses) | Use subprocess cwd parameter |
| Mocking Private Attributes | Medium | 1 file | Use constructor injection |
| Real External Calls | Low | 1 file | Mock or mark as integration |

---

## Prevention Checklist

Before merging new tests, verify:

- [ ] No direct calls to `_private_method()` - test through public interface
- [ ] No `os.chdir()` calls - use `cwd` parameter instead
- [ ] No private attribute assignment for mocking - use constructor injection
- [ ] External dependencies are mocked in unit tests
- [ ] Integration tests are marked with `@pytest.mark.integration`
- [ ] Assertions focus on behavior, not exact messages

---

## References

- [TestRail: How to Write Unit Tests](https://www.testrail.com/blog/how-to-write-unit-tests/)
- `docs/unit_test_evaluation_rubric.md` - Formal quality rubric
- `src/asp/prompts/test_agent_v2_generation.txt` - Updated test generation prompt
