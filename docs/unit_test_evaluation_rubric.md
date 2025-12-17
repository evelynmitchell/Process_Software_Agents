# Unit Test Evaluation Rubric

A formal rubric for evaluating the quality of unit tests, based on industry best practices.

## Scoring Guide

Each dimension is scored 1-5:
- **1 - Poor**: Significant issues that undermine test value
- **2 - Below Average**: Notable gaps requiring attention
- **3 - Acceptable**: Meets minimum standards with room for improvement
- **4 - Good**: Solid implementation following best practices
- **5 - Excellent**: Exemplary tests that serve as models

---

## Dimension 1: Test Isolation

Tests should be independent and not rely on shared state or execution order.

| Score | Criteria |
|-------|----------|
| 1 | Tests share mutable state; execution order affects results; tests fail when run individually |
| 2 | Some shared fixtures cause occasional interference; cleanup is inconsistent |
| 3 | Tests use shared fixtures but are mostly independent; proper setup/teardown exists |
| 4 | Tests are fully independent; each test creates its own fixtures; proper isolation patterns used |
| 5 | Perfect isolation; tests can run in any order, in parallel; no global state; fixtures are immutable or freshly created |

**Key Questions:**
- Can tests run in any order?
- Can tests run in parallel without interference?
- Does each test clean up after itself?

---

## Dimension 2: Assertion Focus

Each test should verify one specific behavior with clear, focused assertions.

| Score | Criteria |
|-------|----------|
| 1 | Multiple unrelated behaviors tested; dozens of assertions per test; unclear what's being verified |
| 2 | Several loosely related behaviors in one test; hard to identify failure cause |
| 3 | Tests cover related behaviors; reasonable number of assertions; failure messages exist |
| 4 | Single behavior per test; assertions directly relate to the behavior; clear failure messages |
| 5 | One assertion per test (or logically grouped); failure immediately identifies the problem; test name matches assertion |

**Key Questions:**
- When a test fails, is the cause immediately obvious?
- Does each test verify exactly one thing?
- Are assertion messages descriptive?

---

## Dimension 3: Behavior vs Implementation Testing

Tests should verify what code does, not how it does it internally.

| Score | Criteria |
|-------|----------|
| 1 | Tests private methods directly; verifies internal data structures; breaks on any refactor |
| 2 | Mix of public/private testing; some coupling to implementation details |
| 3 | Mostly tests public API; occasional implementation dependencies |
| 4 | Tests public interfaces only; survives most refactoring; focuses on inputs/outputs |
| 5 | Pure behavioral testing; tests describe requirements; implementation can change freely without test updates |

**Key Questions:**
- Would a refactor break these tests even if behavior is unchanged?
- Do tests verify outcomes or mechanisms?
- Are tests coupled to specific implementation choices?

---

## Dimension 4: Coverage Quality

Tests should cover happy paths, edge cases, and error conditions meaningfully.

| Score | Criteria |
|-------|----------|
| 1 | Only trivial happy path; no edge cases; no error handling tests |
| 2 | Basic happy path with one or two variations; minimal edge case coverage |
| 3 | Happy path covered; some edge cases; basic error conditions tested |
| 4 | Comprehensive happy path; good edge case coverage; error conditions handled; boundary values tested |
| 5 | Exhaustive coverage; all edge cases; all error paths; boundary conditions; property-based testing where appropriate |

**Key Questions:**
- What happens with null/empty/invalid inputs?
- Are boundary values tested (0, -1, max, min)?
- Are error conditions explicitly tested?

---

## Dimension 5: Naming and Readability

Test names and structure should clearly communicate intent and serve as documentation.

| Score | Criteria |
|-------|----------|
| 1 | Names like `test1`, `testFunction`; no structure; impossible to understand purpose |
| 2 | Generic names; some structure; requires reading code to understand |
| 3 | Descriptive names for most tests; consistent structure; reasonably readable |
| 4 | Names describe behavior and expectation; clear arrange/act/assert structure; readable without comments |
| 5 | Tests read like specifications; names follow consistent pattern (given/when/then or similar); self-documenting |

**Naming Pattern Examples:**
- Poor: `test_function`, `test1`
- Acceptable: `test_add_numbers`, `test_user_creation`
- Good: `test_add_returns_sum_of_two_positive_numbers`
- Excellent: `test_add_given_negative_numbers_returns_correct_sum`

---

## Dimension 6: Speed and Performance

Unit tests should be fast and avoid external dependencies.

| Score | Criteria |
|-------|----------|
| 1 | Tests hit real databases, APIs, or file systems; suite takes minutes |
| 2 | Some external dependencies; inconsistent mocking; slow tests mixed in |
| 3 | Most dependencies mocked; occasional I/O; suite runs in reasonable time |
| 4 | All external dependencies mocked; tests run in milliseconds; proper test doubles used |
| 5 | Lightning fast; pure unit tests; excellent use of mocks/stubs/fakes; parallel execution possible |

**Key Questions:**
- Do tests require network access?
- Are databases/filesystems mocked?
- How long does the full suite take?

---

## Evaluation Template

### Test File: `[filename]`

| Dimension | Score (1-5) | Notes |
|-----------|-------------|-------|
| Isolation | | |
| Assertion Focus | | |
| Behavior vs Implementation | | |
| Coverage Quality | | |
| Naming/Readability | | |
| Speed/Performance | | |
| **Average** | | |

**Strengths:**
-

**Areas for Improvement:**
-

**Recommendations:**
-

---

## Aggregate Project Score

| Dimension | Average Score | Assessment |
|-----------|---------------|------------|
| Isolation | | |
| Assertion Focus | | |
| Behavior vs Implementation | | |
| Coverage Quality | | |
| Naming/Readability | | |
| Speed/Performance | | |
| **Overall Average** | | |

### Scoring Interpretation

| Average Score | Overall Rating |
|---------------|----------------|
| 4.5 - 5.0 | Excellent - Industry-leading test quality |
| 4.0 - 4.4 | Good - Solid test suite with minor improvements needed |
| 3.0 - 3.9 | Acceptable - Functional but needs attention |
| 2.0 - 2.9 | Below Average - Significant improvements required |
| 1.0 - 1.9 | Poor - Major overhaul needed |

---

## References

- [TestRail: How to Write Unit Tests](https://www.testrail.com/blog/how-to-write-unit-tests/)
- [TestRail: Unit Testing Best Practices](https://www.testrail.com/blog/unit-testing/)
