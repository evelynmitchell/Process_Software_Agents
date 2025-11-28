# Avoiding Brittle Tests: A Guide to Writing Maintainable Test Suites

**Author:** ASP Development Team
**Date:** November 28, 2025
**Status:** Best Practices Guide

## Overview

This document provides guidance on identifying and refactoring brittle tests - tests that break due to irrelevant changes rather than actual bugs. Brittle tests increase maintenance burden and reduce confidence in the test suite.

## What Are Brittle Tests?

**Brittle tests** are tests that fail when implementation details change, even though the core functionality remains correct. They couple tests too tightly to specific implementation choices rather than testing behavior.

## Real-World Example: Pricing Tests

### The Problem We Had

Our LLM client pricing tests were brittle because they hardcoded dollar amounts:

```python
# BRITTLE TEST ❌
def test_estimate_cost_simple(self):
    client = LLMClient(api_key="test-key")
    cost = client.estimate_cost(input_tokens=1000, output_tokens=500)

    # Hardcoded value - breaks when Anthropic changes pricing
    assert cost == 0.000875
```

**Why this is brittle:**
- Hardcoded `0.000875` based on specific pricing ($0.25/$1.25 per M tokens)
- When Anthropic updates pricing, test fails even though calculation is correct
- Requires updating multiple test files when pricing changes
- Test doesn't actually validate the calculation logic

### The Solution

Refactor to test the **formula** rather than specific **values**:

```python
# ROBUST TEST ✅
def test_estimate_cost_simple(self):
    client = LLMClient(api_key="test-key")
    input_tokens, output_tokens = 1000, 500
    cost = client.estimate_cost(input_tokens=input_tokens, output_tokens=output_tokens)

    # Calculate expected from class constants
    expected = (
        (input_tokens / 1_000_000) * client.COST_PER_MILLION_INPUT_TOKENS +
        (output_tokens / 1_000_000) * client.COST_PER_MILLION_OUTPUT_TOKENS
    )
    assert cost == pytest.approx(expected, rel=1e-9)
```

**Why this is better:**
- Tests the calculation formula, not specific values
- Pricing can be updated in one place (`COST_PER_MILLION_*` constants)
- Test validates the actual logic being tested
- More maintainable long-term

## Common Patterns of Brittle Tests

### 1. Hardcoded External Values

**Brittle:**
```python
def test_api_version():
    assert get_api_version() == "v2.5.3"  # ❌ Breaks on every version bump
```

**Better:**
```python
def test_api_version():
    version = get_api_version()
    assert re.match(r'v\d+\.\d+\.\d+', version)  # ✅ Tests format, not value
    assert version == API_VERSION_CONSTANT  # ✅ Tests against source of truth
```

### 2. Hardcoded Timestamps/Dates

**Brittle:**
```python
def test_date_formatting():
    result = format_date(datetime(2025, 11, 28))
    assert result == "2025-11-28"  # ❌ Coupled to specific date
```

**Better:**
```python
def test_date_formatting():
    test_date = datetime(2025, 11, 28)
    result = format_date(test_date)
    assert result == test_date.strftime("%Y-%m-%d")  # ✅ Tests format logic
```

### 3. Exact String Matching

**Brittle:**
```python
def test_error_message():
    with pytest.raises(ValueError) as exc:
        process_invalid_input()
    # ❌ Breaks if error message wording changes
    assert str(exc.value) == "Invalid input: expected positive number"
```

**Better:**
```python
def test_error_message():
    with pytest.raises(ValueError) as exc:
        process_invalid_input()
    # ✅ Tests key parts, allows flexibility
    assert "Invalid input" in str(exc.value)
    assert "positive number" in str(exc.value)
```

### 4. Testing Implementation Details

**Brittle:**
```python
def test_cache_implementation():
    cache = Cache()
    cache.set("key", "value")
    # ❌ Testing internal data structure
    assert cache._internal_dict == {"key": "value"}
```

**Better:**
```python
def test_cache_behavior():
    cache = Cache()
    cache.set("key", "value")
    # ✅ Testing public behavior
    assert cache.get("key") == "value"
    assert cache.has("key") is True
```

### 5. Order-Dependent Tests

**Brittle:**
```python
def test_get_users():
    users = get_all_users()
    # ❌ Assumes specific order
    assert users[0].name == "Alice"
    assert users[1].name == "Bob"
```

**Better:**
```python
def test_get_users():
    users = get_all_users()
    # ✅ Tests content, not order
    user_names = {user.name for user in users}
    assert "Alice" in user_names
    assert "Bob" in user_names
```

## How to Identify Brittle Tests

### Red Flags Checklist

Look for these warning signs when reviewing tests:

- [ ] **Magic numbers**: Hardcoded values without clear meaning
- [ ] **External dependencies**: Tests that assume specific API versions, pricing, etc.
- [ ] **Exact string matching**: Full error message or output comparisons
- [ ] **Implementation testing**: Tests accessing private attributes (`_*`)
- [ ] **Fragile assertions**: Tests that fail when adding new valid data
- [ ] **Time/date dependencies**: Tests that use `datetime.now()` or assume current date
- [ ] **Order assumptions**: Tests that assume specific ordering of results
- [ ] **Mock overuse**: Heavy mocking that recreates entire implementation

### Questions to Ask

When writing or reviewing a test, ask:

1. **Will this test break if we update external dependencies?** (pricing, API versions)
2. **Am I testing behavior or implementation details?**
3. **Could this fail for reasons unrelated to correctness?**
4. **Am I hardcoding values that might legitimately change?**
5. **Does this test make assumptions about internal data structures?**

## Refactoring Strategies

### Strategy 1: Test Against Constants

Instead of hardcoding values, reference the source of truth:

```python
# Before
assert config.max_retries == 3

# After
assert config.max_retries == DEFAULT_MAX_RETRIES
```

### Strategy 2: Test Properties, Not Values

Test invariants and relationships rather than exact values:

```python
# Before
assert calculate_discount(100) == 85

# After
original_price = 100
discounted = calculate_discount(original_price)
assert discounted < original_price  # Property: discounted < original
assert discounted >= 0  # Property: non-negative
```

### Strategy 3: Parameterize External Values

Make external dependencies explicit and configurable:

```python
# Before
def test_with_hardcoded_model():
    assert get_model_name() == "claude-sonnet-4-20250514"

# After
@pytest.fixture
def expected_model():
    return LLMClient.DEFAULT_MODEL

def test_with_fixture(expected_model):
    assert get_model_name() == expected_model
```

### Strategy 4: Use Matchers Over Equality

Prefer matchers that allow flexibility:

```python
# Before
assert error_msg == "Error: Invalid input received"

# After
assert "Invalid input" in error_msg
# Or use regex for more precision
assert re.match(r"Error:.*Invalid input.*", error_msg)
```

## Best Practices Summary

### DO ✅

- **Test behavior, not implementation**
- **Use constants and configuration values**
- **Test formulas and calculations**
- **Allow flexibility in non-essential details**
- **Test properties and invariants**
- **Make external dependencies explicit**

### DON'T ❌

- **Hardcode values that might change** (pricing, versions, dates)
- **Test private attributes or methods**
- **Assume specific ordering unless required**
- **Use exact string matching for error messages**
- **Couple tests to implementation details**
- **Mock everything (prefer real objects when safe)**

## Measuring Test Brittleness

### Indicators of a Healthy Test Suite

- Tests rarely break when refactoring code
- Failed tests indicate actual bugs, not false positives
- Updating external dependencies doesn't require massive test changes
- Tests are easy to understand and modify
- High signal-to-noise ratio in test failures

### Indicators of Brittleness

- Frequent test failures on dependency updates
- Tests break during harmless refactoring
- Many tests need updates for simple changes
- Difficulty distinguishing real bugs from test issues
- Team avoids running tests due to false positives

## Conclusion

Brittle tests undermine the value of a test suite. By following these guidelines, we can build tests that:

1. **Survive refactoring** - Tests focus on behavior, not implementation
2. **Adapt to change** - Tests reference constants rather than hardcoding values
3. **Provide value** - Test failures indicate real problems, not false alarms
4. **Are maintainable** - Easy to update when legitimate changes occur

Remember: **A test should fail only when the functionality it tests is broken, not when unrelated details change.**

## References

- [Session Summary 20251128.1](../Summary/summary20251128.1.md) - Pricing test refactoring example
- [Comprehensive Agent Test Plan](comprehensive_agent_test_plan.md)
- [Developer Guide](Developer_Guide.md)

## Related Issues

When refactoring brittle tests, consider:
- Updating related documentation
- Adding comments explaining why tests are structured a certain way
- Creating test utilities for common patterns
- Reviewing other tests for similar brittleness
