# Advanced Testing Strategies

**Date:** 2025-12-11
**Status:** Proposed

## Overview

This document describes three advanced testing strategies and how to integrate them into the project with **opt-in enablement** to control compute costs.

| Strategy | Purpose | Compute Cost | Default |
|----------|---------|--------------|---------|
| Combination Testing | Test parameter interactions | Low | Enabled |
| Design of Experiments | Statistical test design, factor analysis | Medium | Disabled |
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

## 2. Design of Experiments (DoE)

### What It Is

Design of Experiments is the **statistical foundation** underneath combination testing. While pairwise testing is a practical heuristic, DoE provides rigorous mathematical frameworks for selecting test cases that maximize information gained per test run.

### Key Concepts

| Concept | Description | Use Case |
|---------|-------------|----------|
| **Full Factorial** | Test all combinations | Small parameter spaces, critical code |
| **Fractional Factorial** | Statistically selected subset | Large spaces, need interaction info |
| **Orthogonal Arrays** | Balanced designs (Taguchi L9, L18, L27) | When you need statistical independence |
| **Screening Designs** | Identify which factors matter | Early exploration, many factors |
| **Response Surface** | Find optimal parameter values | Performance tuning, threshold finding |
| **Latin Hypercube** | Space-filling for continuous params | Numerical optimization, simulations |

### Why Use DoE Over Ad-Hoc Testing

1. **Quantify interactions** - Not just "does it work" but "which factors affect the outcome"
2. **Statistical confidence** - Know how much you can trust your results
3. **Efficient coverage** - Maximize information per test case
4. **Identify main effects** - Which parameters matter most

### Implementation

```python
# requirements-dev.txt
pyDOE2>=1.3.0
doepy>=0.0.1

# tests/doe/test_factorial_designs.py
import pytest
import pyDOE2 as doe
import numpy as np

# Define factors and levels
FACTORS = {
    'max_iterations': [1, 5, 10],
    'confidence_threshold': [0.5, 0.7, 0.9],
    'hitl_mode': [0, 1, 2],  # autonomous, supervised, threshold
    'timeout_seconds': [60, 300, 600],
}

@pytest.mark.doe
def test_full_factorial():
    """
    Full factorial design - tests ALL combinations.
    Use for critical code with few factors.

    3^4 = 81 test cases
    """
    design = doe.fullfact([3, 3, 3, 3])  # 3 levels each

    for row in design:
        config = {
            'max_iterations': FACTORS['max_iterations'][int(row[0])],
            'confidence_threshold': FACTORS['confidence_threshold'][int(row[1])],
            'hitl_mode': ['autonomous', 'supervised', 'threshold'][int(row[2])],
            'timeout_seconds': FACTORS['timeout_seconds'][int(row[3])],
        }
        result = run_repair_with_config(config)
        assert result.is_valid()


@pytest.mark.doe
def test_fractional_factorial():
    """
    Fractional factorial - statistically selected subset.
    Resolution IV: main effects not aliased with 2-factor interactions.

    Reduces 81 tests to ~27 while preserving main effect estimates.
    """
    # 2-level fractional factorial (need to discretize)
    design = doe.fracfact('a b c d')  # 2^(4-1) = 8 runs

    for row in design:
        # Map -1/+1 to actual values
        config = {
            'max_iterations': 1 if row[0] < 0 else 10,
            'confidence_threshold': 0.5 if row[1] < 0 else 0.9,
            'hitl_mode': 'autonomous' if row[2] < 0 else 'threshold',
            'timeout_seconds': 60 if row[3] < 0 else 600,
        }
        result = run_repair_with_config(config)
        assert result.is_valid()


@pytest.mark.doe
def test_latin_hypercube():
    """
    Latin Hypercube Sampling - for continuous parameters.
    Space-filling design that ensures good coverage.

    Useful for: timeout values, confidence thresholds, numerical params.
    """
    # 20 samples across 3 continuous dimensions
    design = doe.lhs(3, samples=20)

    for row in design:
        config = {
            # Scale [0,1] to actual ranges
            'confidence_threshold': 0.5 + row[0] * 0.5,  # [0.5, 1.0]
            'timeout_seconds': 60 + row[1] * 540,        # [60, 600]
            'memory_limit_mb': 256 + row[2] * 768,       # [256, 1024]
        }
        result = run_repair_with_config(config)
        assert result.is_valid()
```

### Orthogonal Arrays (Taguchi Method)

```python
# Taguchi L9 orthogonal array for 4 factors at 3 levels
# Only 9 tests instead of 81, but statistically balanced

L9 = [
    [0, 0, 0, 0],
    [0, 1, 1, 1],
    [0, 2, 2, 2],
    [1, 0, 1, 2],
    [1, 1, 2, 0],
    [1, 2, 0, 1],
    [2, 0, 2, 1],
    [2, 1, 0, 2],
    [2, 2, 1, 0],
]

@pytest.mark.doe
@pytest.mark.parametrize("levels", L9)
def test_taguchi_l9_design(levels):
    """
    Taguchi L9 orthogonal array.

    Properties:
    - Each level appears exactly 3 times per factor
    - All pairs of levels appear exactly once
    - Main effects can be estimated independently
    """
    config = {
        'max_iterations': [1, 5, 10][levels[0]],
        'confidence_threshold': [0.5, 0.7, 0.9][levels[1]],
        'hitl_mode': ['autonomous', 'supervised', 'threshold'][levels[2]],
        'timeout_seconds': [60, 300, 600][levels[3]],
    }
    result = run_repair_with_config(config)
    assert result.is_valid()
```

### Analyzing Results

```python
# After running DoE tests, analyze which factors matter

import pandas as pd
from scipy import stats

def analyze_doe_results(results_df):
    """
    Analyze DoE results to identify significant factors.

    Args:
        results_df: DataFrame with factor columns and 'success' outcome

    Returns:
        Dict of factor -> effect size
    """
    effects = {}

    for factor in ['max_iterations', 'confidence_threshold', 'hitl_mode']:
        # Group by factor level and compute success rate
        grouped = results_df.groupby(factor)['success'].mean()

        # Effect size: difference between best and worst level
        effects[factor] = grouped.max() - grouped.min()

    # Sort by effect size
    return dict(sorted(effects.items(), key=lambda x: -x[1]))

# Example output:
# {'confidence_threshold': 0.35, 'max_iterations': 0.22, 'hitl_mode': 0.08}
# -> confidence_threshold has the biggest impact on success
```

### When to Use Each Design

| Design | Factors | Levels | Tests | Use When |
|--------|---------|--------|-------|----------|
| Full Factorial | 2-3 | 2-3 | <30 | Critical code, need all interactions |
| Fractional Factorial | 4-8 | 2 | 8-32 | Many factors, main effects sufficient |
| Taguchi L9/L18 | 4-8 | 3 | 9-18 | Balanced design, moderate factors |
| Latin Hypercube | Any | Continuous | 10-50 | Numerical optimization |
| Pairwise | Many | Many | Varies | Practical coverage, less rigor |

### Enablement

```ini
# pytest.ini
[pytest]
markers =
    doe: Design of Experiments tests (opt-in, medium compute)
```

```bash
# Run DoE tests
pytest -m doe

# Run specific design
pytest -m doe -k "taguchi"
```

**Cost:** Medium - more rigorous than pairwise, less than full factorial. Worth it for understanding factor effects.

---

## 3. Property-Based Testing (Hypothesis)

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

## 4. Mutation Testing

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

## 5. Unit Test Evaluation Rubric

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

## 6. Recommended Test Pyramid

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

## 7. Configuration Summary

### pytest.ini

```ini
[pytest]
markers =
    unit: Unit tests (default, always run)
    integration: Integration tests (run on CI)
    combinations: Pairwise combination tests (always run)
    doe: Design of Experiments tests (opt-in, medium compute)
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

## 8. Adding New Tests - Guidelines

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
| DoE | ❌ | ❌ | ✅ | ✅ |
| Hypothesis | ❌ | ✅ (limited) | ✅ (full) | ✅ |
| Mutation | ❌ | ❌ | ✅ | ✅ |
| E2E | ❌ | ❌ | ❌ | ✅ |

This approach balances thoroughness with compute cost, allowing you to opt-in to expensive testing strategies when appropriate.
