# Advanced Testing Strategies

**Date:** 2025-12-11
**Status:** Proposed

## Overview

This document describes three advanced testing strategies and how to integrate them into the project with **opt-in enablement** to control compute costs.

| Strategy | Purpose | Compute Cost | Default |
|----------|---------|--------------|---------|
| Combination Testing | Test parameter interactions | Low | Enabled |
| Property-Based (Hypothesis) | Find edge cases via random generation | **High** | Disabled |
| Mutation Testing | Measure test effectiveness | **Very High** | Disabled |

---

## 1. Combination Testing (Pairwise)

### What It Does

Tests interactions between parameters without exhaustive combinations. For N parameters with M values each, full testing requires M^N tests. Pairwise testing covers most bugs with far fewer tests by ensuring every pair of parameter values appears together at least once.

### When to Use

- Functions with multiple configuration options
- API endpoints with several query parameters
- HITL configs, sandbox configs, CLI options

### Implementation

```python
# requirements-dev.txt
allpairspy>=2.5.0

# tests/unit/test_config_combinations.py
import pytest
from allpairspy import AllPairs

HITL_MODES = ["autonomous", "supervised", "threshold"]
MAX_ITERATIONS = [1, 3, 5, 10]
CONFIDENCE_THRESHOLDS = [0.5, 0.7, 0.9]
DRAFT_PR = [True, False]

@pytest.mark.combinations
def test_repair_config_combinations():
    """Test that all pairwise combinations of config options work."""
    parameters = [
        HITL_MODES,
        MAX_ITERATIONS,
        CONFIDENCE_THRESHOLDS,
        DRAFT_PR,
    ]

    # AllPairs generates ~20 combinations instead of 3*4*3*2=72
    for mode, max_iter, confidence, draft in AllPairs(parameters):
        config = RepairConfig(
            hitl_mode=mode,
            max_iterations=max_iter,
            confidence_threshold=confidence,
            draft_pr=draft,
        )
        # Validate config doesn't raise
        assert config.validate()
```

### Enablement

```ini
# pytest.ini
[pytest]
markers =
    combinations: Pairwise combination tests (enabled by default)
```

```bash
# Run combination tests (included in normal test run)
pytest

# Skip combination tests
pytest -m "not combinations"
```

**Cost:** Low - generates O(M^2) tests instead of O(M^N)

---

## 2. Property-Based Testing (Hypothesis)

### What It Does

Instead of writing specific test cases, you define **properties** that should always hold. Hypothesis generates hundreds of random inputs to find counterexamples, then shrinks failures to minimal examples.

### When to Use

- Parsers (pytest output, GitHub URLs)
- Validators (model validation, input sanitization)
- Serialization/deserialization (round-trip properties)
- Mathematical invariants

### Implementation

```python
# requirements-dev.txt
hypothesis>=6.100.0

# conftest.py - CRITICAL: Configure to control compute
from hypothesis import settings, Verbosity, Phase

# Define profiles with different compute budgets
settings.register_profile(
    "ci",
    max_examples=50,          # Reduced for CI
    deadline=1000,            # 1 second per example max
    suppress_health_check=[],
)

settings.register_profile(
    "dev",
    max_examples=10,          # Fast for local dev
    deadline=500,
)

settings.register_profile(
    "thorough",
    max_examples=500,         # Comprehensive but expensive
    deadline=5000,
    phases=[Phase.explicit, Phase.reuse, Phase.generate, Phase.shrink],
)

# Load profile from environment
import os
settings.load_profile(os.getenv("HYPOTHESIS_PROFILE", "dev"))
```

```python
# tests/unit/test_parsers_hypothesis.py
import pytest
from hypothesis import given, strategies as st, assume

@pytest.mark.hypothesis
@given(st.text())
def test_github_url_parser_never_crashes(url_text):
    """Parser should never raise unexpected exceptions."""
    try:
        result = parse_github_url(url_text)
        # If it parses, result should be valid
        if result:
            assert result.owner
            assert result.repo
    except InvalidGitHubURLError:
        pass  # Expected for invalid input


@pytest.mark.hypothesis
@given(
    owner=st.text(min_size=1, max_size=39, alphabet=st.characters(whitelist_categories=('Ll', 'Lu', 'Nd'), whitelist_characters='-')),
    repo=st.text(min_size=1, max_size=100, alphabet=st.characters(whitelist_categories=('Ll', 'Lu', 'Nd'), whitelist_characters='-_.')),
    number=st.integers(min_value=1, max_value=999999),
)
def test_github_url_roundtrip(owner, repo, number):
    """Parsing a constructed URL should return original values."""
    assume(not owner.startswith('-') and not owner.endswith('-'))
    assume(not repo.startswith('-'))

    url = f"https://github.com/{owner}/{repo}/issues/{number}"
    parsed = parse_github_url(url)

    assert parsed.owner == owner
    assert parsed.repo == repo
    assert parsed.number == number


@pytest.mark.hypothesis
@given(st.binary())
def test_pytest_parser_handles_garbage(garbage_output):
    """Parser should handle any input without crashing."""
    try:
        result = PytestResultParser().parse(
            stdout=garbage_output.decode('utf-8', errors='replace'),
            stderr="",
            exit_code=1,
        )
        # Should return a valid TestResult even for garbage
        assert isinstance(result, TestResult)
    except UnicodeDecodeError:
        pass  # Expected for some binary
```

### Enablement

```ini
# pytest.ini
[pytest]
markers =
    hypothesis: Property-based tests (DISABLED by default - high compute cost)
```

```bash
# Normal test run - hypothesis tests SKIPPED
pytest

# Explicitly run hypothesis tests
pytest -m hypothesis

# Run with specific profile
HYPOTHESIS_PROFILE=ci pytest -m hypothesis

# Run thorough hypothesis tests (expensive!)
HYPOTHESIS_PROFILE=thorough pytest -m hypothesis
```

### Compute Budget Control

| Profile | max_examples | Estimated Time | When to Use |
|---------|--------------|----------------|-------------|
| `dev` | 10 | ~seconds | Local development |
| `ci` | 50 | ~minutes | CI pipeline |
| `thorough` | 500 | ~10+ minutes | Pre-release, nightly |

```yaml
# .github/workflows/test.yml
jobs:
  test:
    steps:
      - name: Run unit tests
        run: pytest -m "not hypothesis and not mutation"

      - name: Run hypothesis tests (limited)
        run: HYPOTHESIS_PROFILE=ci pytest -m hypothesis
        continue-on-error: true  # Don't block on flaky property tests
```

**Cost:** High - can run thousands of examples. MUST configure limits.

---

## 3. Mutation Testing

### What It Does

Creates "mutants" of your code (small changes like `+` → `-`, `>` → `>=`, `True` → `False`) and runs tests. If tests pass with a mutant, your tests didn't catch that potential bug.

**Mutation Score** = killed mutants / total mutants

This measures test **effectiveness**, not just coverage.

### When to Use

- Evaluating test suite quality
- Finding weak tests that pass but don't verify behavior
- Pre-release quality gates
- NOT in regular CI (too slow)

### Implementation

```python
# requirements-dev.txt
mutmut>=2.4.0
```

```ini
# setup.cfg or pyproject.toml
[mutmut]
paths_to_mutate=src/
tests_dir=tests/
runner=python -m pytest -x -q
```

```python
# tests/mutation/test_critical_paths.py
"""
Mutation testing targets.

Run with: mutmut run --paths-to-mutate src/asp/orchestrators/confidence.py

These tests should kill mutants in critical calculation code.
"""

def test_confidence_calculation_boundaries():
    """Verify confidence calculation handles boundaries correctly."""
    # 0.0 confidence
    result = calculate_confidence(
        diagnostic_confidence=0.0,
        fix_confidence=0.0,
        test_coverage_confidence=0.0,
    )
    assert result.overall == 0.0

    # 1.0 confidence
    result = calculate_confidence(
        diagnostic_confidence=1.0,
        fix_confidence=1.0,
        test_coverage_confidence=1.0,
    )
    assert result.overall == 1.0

    # Weighted correctly (0.3, 0.3, 0.4)
    result = calculate_confidence(
        diagnostic_confidence=1.0,
        fix_confidence=0.0,
        test_coverage_confidence=0.0,
    )
    assert result.overall == pytest.approx(0.3)
```

### Enablement

```bash
# Run mutation testing on specific module (SLOW)
mutmut run --paths-to-mutate src/asp/orchestrators/confidence.py

# View results
mutmut results

# Generate HTML report
mutmut html

# Run only on changed files (faster)
mutmut run --paths-to-mutate $(git diff --name-only main -- 'src/*.py')
```

### CI Integration (Nightly Only)

```yaml
# .github/workflows/nightly.yml
name: Nightly Quality Checks

on:
  schedule:
    - cron: '0 3 * * *'  # 3 AM daily
  workflow_dispatch:

jobs:
  mutation:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Run mutation testing on critical modules
        run: |
          pip install mutmut
          mutmut run --paths-to-mutate src/asp/orchestrators/confidence.py
          mutmut run --paths-to-mutate src/services/surgical_editor.py
        continue-on-error: true

      - name: Upload mutation report
        uses: actions/upload-artifact@v4
        with:
          name: mutation-report
          path: .mutmut-cache/
```

**Cost:** Very High - runs full test suite per mutant. Only run on critical code paths, nightly.

---

## 4. Unit Test Evaluation Rubric

Use this rubric to assess test quality:

| Dimension | 1 (Poor) | 3 (Adequate) | 5 (Excellent) |
|-----------|----------|--------------|---------------|
| **Coverage** | <50% | 70-80% | >90% |
| **Mutation Score** | <40% | 60-70% | >80% |
| **Isolation** | External deps, slow | Some mocking | Fully isolated, <100ms |
| **Clarity** | Unclear names | Descriptive names | BDD-style, self-documenting |
| **Edge Cases** | Happy path only | Some boundaries | Comprehensive edge cases |
| **Properties** | None | Some invariants | Key properties verified |
| **Maintainability** | Copy-paste, brittle | Some fixtures | DRY, parameterized |

### Automated Checks

```python
# tests/conftest.py

def pytest_collection_modifyitems(session, config, items):
    """Enforce test quality standards."""
    for item in items:
        # Check test name is descriptive
        if not item.name.startswith("test_"):
            continue

        # Warn about tests without assertions (empty tests)
        # This is a simple heuristic
        source = inspect.getsource(item.function)
        if "assert" not in source and "pytest.raises" not in source:
            warnings.warn(f"{item.name} has no assertions")
```

---

## 5. Recommended Test Pyramid

```
                    ┌─────────────┐
                    │   E2E       │  Few, slow, expensive
                    │  (manual)   │  Run: Pre-release
                    ├─────────────┤
                    │ Integration │  Some, medium speed
                    │   Tests     │  Run: CI (on PR)
                    ├─────────────┤
                    │  Hypothesis │  Many examples, medium
                    │  (opt-in)   │  Run: CI limited, nightly full
                    ├─────────────┤
                    │ Combination │  Pairwise, fast
                    │   Tests     │  Run: Always
                    ├─────────────┤
                    │    Unit     │  Many, fast
                    │   Tests     │  Run: Always
                    └─────────────┘

Mutation Testing: Run nightly on critical paths only
```

---

## 6. Configuration Summary

### pytest.ini

```ini
[pytest]
markers =
    unit: Unit tests (default, always run)
    integration: Integration tests (run on CI)
    combinations: Pairwise combination tests (always run)
    hypothesis: Property-based tests (opt-in, high compute)
    mutation: Mutation test targets (nightly only)
    e2e: End-to-end tests (manual/pre-release)
    slow: Slow tests (>10s)

# Default: run unit and combination tests only
addopts = -m "unit or combinations" --strict-markers
```

### Makefile / pyproject.toml scripts

```makefile
.PHONY: test test-all test-hypothesis test-mutation

test:  ## Run fast tests (unit + combinations)
	pytest -m "not hypothesis and not mutation and not e2e"

test-ci:  ## Run CI tests (unit + combinations + limited hypothesis)
	pytest -m "not mutation and not e2e"
	HYPOTHESIS_PROFILE=ci pytest -m hypothesis

test-hypothesis:  ## Run property-based tests (expensive)
	HYPOTHESIS_PROFILE=thorough pytest -m hypothesis

test-mutation:  ## Run mutation tests (very expensive)
	mutmut run --paths-to-mutate src/asp/orchestrators/
```

---

## 7. Adding New Tests - Guidelines

### Unit Tests (Always)
- Fast (<100ms per test)
- No external dependencies
- Use mocks for I/O
- Name: `test_<function>_<scenario>`

### Combination Tests (When applicable)
- Mark with `@pytest.mark.combinations`
- Use when function has 3+ interacting parameters
- Keep parameter sets small

### Hypothesis Tests (For parsers/validators)
- Mark with `@pytest.mark.hypothesis`
- Define clear properties, not just "doesn't crash"
- Use `assume()` to filter invalid generated inputs
- Always set `deadline` to prevent hangs

### Mutation Targets (For critical code)
- Mark with `@pytest.mark.mutation`
- Focus on: calculations, conditionals, business logic
- Ensure tests would fail if logic changed

---

## Summary

| Strategy | Default | CI | Nightly | Manual |
|----------|---------|-----|---------|--------|
| Unit | ✅ | ✅ | ✅ | ✅ |
| Combination | ✅ | ✅ | ✅ | ✅ |
| Hypothesis | ❌ | ✅ (limited) | ✅ (full) | ✅ |
| Mutation | ❌ | ❌ | ✅ | ✅ |
| E2E | ❌ | ❌ | ❌ | ✅ |

This approach balances thoroughness with compute cost, allowing you to opt-in to expensive testing strategies when appropriate.
