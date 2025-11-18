# Test Implementation Plan

**Date:** November 18, 2025
**Author:** Claude Code
**Status:** Ready for Implementation

---

## Overview

This document provides a detailed implementation plan for addressing the test coverage gaps identified in [Test Coverage Analysis](test_coverage_analysis.md).

**Goal:** Achieve 95%+ test coverage by implementing ~355-385 tests across 15 new test files.

**Estimated Effort:** 3-4 weeks (1 developer) or 2 weeks (2 developers in parallel)

---

## Implementation Strategy

### Approach

1. **Priority-driven:** Start with CRITICAL gaps that protect core infrastructure
2. **Incremental:** Each phase delivers working, tested code
3. **Test-first:** Write tests before refactoring (where applicable)
4. **Parallel-friendly:** Phases can be split across multiple developers

### Testing Standards

All new tests must follow these standards:

- **Framework:** pytest
- **Markers:** Use `@pytest.mark.unit` or `@pytest.mark.integration` appropriately
- **Fixtures:** Use fixtures for common setup (LLM mocking, database setup)
- **Coverage:** Each test file should achieve 85%+ coverage of its module
- **Assertions:** Use descriptive assertion messages
- **Documentation:** Each test has a docstring explaining what it validates
- **Mocking:** Mock external dependencies (LLM APIs, Langfuse, file I/O)

### File Organization

```
tests/
├── unit/
│   ├── agents/
│   │   ├── specialists/          # NEW: Specialist agent tests
│   │   │   ├── test_security_review_agent.py
│   │   │   ├── test_performance_review_agent.py
│   │   │   ├── test_data_integrity_review_agent.py
│   │   │   ├── test_maintainability_review_agent.py
│   │   │   ├── test_architecture_review_agent.py
│   │   │   └── test_api_design_review_agent.py
│   │   └── test_design_review_orchestrator.py  # NEW
│   ├── models/                   # NEW: Model tests
│   │   ├── test_planning_models.py
│   │   ├── test_design_models.py
│   │   ├── test_code_models.py
│   │   └── test_code_review_models.py
│   ├── telemetry/                # NEW: Telemetry tests
│   │   └── test_telemetry.py
│   └── test_error_handling.py    # NEW
├── integration/
│   └── test_full_pipeline_e2e.py # NEW
└── conftest.py                    # Shared fixtures
```

---

## Phase 1: Critical Foundation (Weeks 1-2)

**Goal:** Protect core infrastructure and highest-risk components

**Effort:** ~1,200 lines, 130 tests

### Week 1: Orchestrator + Security + Telemetry

#### Task 1.1: Design Review Orchestrator Tests (3 days)

**File:** `tests/unit/agents/test_design_review_orchestrator.py`

**Test Categories:**
1. **Initialization Tests** (5 tests)
   - Test orchestrator initialization
   - Test specialist agent loading
   - Test configuration validation
   - Test LLM client setup
   - Test error handling for missing dependencies

2. **Parallel Dispatch Tests** (8 tests)
   - Test concurrent agent execution
   - Test agent timeout handling
   - Test partial failure handling (some agents succeed, some fail)
   - Test all agents fail scenario
   - Test all agents succeed scenario
   - Test agent output format validation
   - Test agent execution order independence
   - Test concurrent execution performance

3. **Result Aggregation Tests** (10 tests)
   - Test finding deduplication
   - Test severity normalization
   - Test category mapping
   - Test line number normalization
   - Test finding merging logic
   - Test empty results handling
   - Test single agent results
   - Test conflicting findings resolution
   - Test priority ordering
   - Test result filtering

4. **Integration Tests** (8 tests)
   - Test full orchestration flow
   - Test with real specialist agents (mocked LLM)
   - Test error recovery
   - Test telemetry integration
   - Test logging output
   - Test performance under load
   - Test memory usage
   - Test cleanup after execution

5. **Edge Cases** (4 tests)
   - Test with malformed design specification
   - Test with very large design specs
   - Test with empty design specs
   - Test with invalid specialist agent responses

**Fixtures Needed:**
- `mock_specialist_agents`: Returns mocked specialist agent instances
- `sample_design_spec`: Returns valid design specification
- `mock_llm_client`: Returns mocked LLM client

**Estimated Tests:** 35-40 tests, ~450 lines

**Acceptance Criteria:**
- All orchestrator code paths covered
- Parallel execution validated
- Error handling verified
- 90%+ code coverage

---

#### Task 1.2: Security Review Agent Tests (3 days)

**File:** `tests/unit/agents/specialists/test_security_review_agent.py`

**Test Categories:**
1. **SQL Injection Detection** (6 tests)
   - Test parameterized query validation (should pass)
   - Test string concatenation detection (should fail)
   - Test f-string SQL detection (should fail)
   - Test ORM usage validation (should pass)
   - Test stored procedure validation
   - Test dynamic SQL detection

2. **XSS Detection** (5 tests)
   - Test input sanitization validation
   - Test output encoding validation
   - Test innerHTML usage detection
   - Test template escaping validation
   - Test user input in JavaScript detection

3. **Authentication/Authorization** (6 tests)
   - Test authentication check presence
   - Test authorization validation
   - Test role-based access control validation
   - Test missing authentication detection
   - Test hardcoded credential detection
   - Test session management validation

4. **Sensitive Data Exposure** (5 tests)
   - Test password storage validation
   - Test API key exposure detection
   - Test PII handling validation
   - Test logging sensitive data detection
   - Test encryption validation

5. **API Security** (5 tests)
   - Test CORS configuration validation
   - Test rate limiting validation
   - Test input validation presence
   - Test HTTPS enforcement
   - Test API versioning security

6. **General Security** (3 tests)
   - Test dependency vulnerability scanning
   - Test error message sanitization
   - Test secure defaults validation

**Fixtures Needed:**
- `secure_code_sample`: Returns code with proper security practices
- `vulnerable_code_sample`: Returns code with known vulnerabilities
- `mock_security_llm`: Returns mocked LLM responses for security checks

**Estimated Tests:** 30-35 tests, ~400 lines

**Acceptance Criteria:**
- All OWASP Top 10 categories covered
- True positive rate >80% on sample vulnerable code
- False positive rate <20% on sample secure code

---

#### Task 1.3: Telemetry System Tests (2 days)

**File:** `tests/unit/telemetry/test_telemetry.py`

**Test Categories:**
1. **Decorator Tests** (10 tests)
   - Test `@track_agent_cost` basic functionality
   - Test cost vector calculation accuracy
   - Test latency measurement
   - Test token counting
   - Test API cost calculation
   - Test `@log_defect` basic functionality
   - Test defect recording accuracy
   - Test decorator error handling (should not crash main flow)
   - Test decorator with async functions
   - Test decorator with class methods

2. **Database Operations** (8 tests)
   - Test cost vector insertion
   - Test defect insertion
   - Test batch inserts
   - Test database connection error handling
   - Test transaction rollback on error
   - Test concurrent writes
   - Test query performance
   - Test data retrieval accuracy

3. **Langfuse Integration** (7 tests)
   - Test Langfuse client initialization
   - Test trace creation
   - Test span creation
   - Test event logging
   - Test Langfuse error handling (fallback when unavailable)
   - Test API key validation
   - Test configuration loading

4. **Edge Cases** (5 tests)
   - Test telemetry with missing database
   - Test telemetry with missing Langfuse credentials
   - Test very large payloads
   - Test concurrent telemetry writes
   - Test telemetry cleanup on shutdown

**Fixtures Needed:**
- `mock_database`: Returns in-memory SQLite database
- `mock_langfuse`: Returns mocked Langfuse client
- `sample_agent_function`: Returns a sample function to decorate

**Estimated Tests:** 30-35 tests, ~450 lines

**Acceptance Criteria:**
- All decorators work correctly
- Database operations validated
- Error handling ensures telemetry never crashes main flow
- 90%+ code coverage

---

### Week 2: Planning + Design Models

#### Task 1.4: Planning Models Tests (2 days)

**File:** `tests/unit/models/test_planning_models.py`

**Test Categories:**
1. **TaskRequirements Tests** (5 tests)
   - Test valid requirements creation
   - Test requirements validation
   - Test missing required fields
   - Test JSON serialization
   - Test JSON deserialization

2. **SemanticUnit Tests** (6 tests)
   - Test semantic unit creation
   - Test complexity calculation
   - Test cost vector estimation
   - Test dependencies validation
   - Test JSON serialization
   - Test validation edge cases

3. **ProjectPlan Tests** (6 tests)
   - Test project plan aggregation
   - Test total complexity calculation
   - Test total cost vector calculation
   - Test semantic unit ordering
   - Test validation rules
   - Test JSON serialization/deserialization

4. **Integration Tests** (3 tests)
   - Test full planning workflow
   - Test plan validation end-to-end
   - Test error propagation

**Estimated Tests:** 15-20 tests, ~300 lines

---

#### Task 1.5: Design Models Tests (2 days)

**File:** `tests/unit/models/test_design_models.py`

**Test Categories:**
1. **DesignSpecification Tests** (7 tests)
   - Test specification creation
   - Test nested component validation
   - Test API contract validation
   - Test data schema validation
   - Test JSON serialization
   - Test large specification handling
   - Test validation errors

2. **APIContract Tests** (6 tests)
   - Test contract creation
   - Test endpoint validation
   - Test request/response schema validation
   - Test authentication requirements
   - Test error response definitions
   - Test JSON serialization

3. **DataSchema Tests** (6 tests)
   - Test schema creation
   - Test field validation
   - Test constraint validation
   - Test relationship validation
   - Test index definitions
   - Test JSON serialization

4. **ComponentDesign Tests** (5 tests)
   - Test component creation
   - Test interface definition
   - Test dependency validation
   - Test logic specification
   - Test JSON serialization

**Estimated Tests:** 20-25 tests, ~350 lines

---

## Phase 2: Review Agents (Weeks 2-3)

**Goal:** Complete test coverage for all specialist review agents

**Effort:** ~1,500 lines, 155 tests

### Week 3: Performance + Data Integrity + Maintainability

#### Task 2.1: Performance Review Agent Tests (2 days)

**File:** `tests/unit/agents/specialists/test_performance_review_agent.py`

**Test Categories:**
1. **Query Optimization** (8 tests)
   - Test N+1 query detection
   - Test missing index detection
   - Test SELECT * detection
   - Test inefficient JOIN detection
   - Test missing WHERE clause detection
   - Test full table scan detection
   - Test proper query validation (should pass)
   - Test query complexity analysis

2. **Caching** (6 tests)
   - Test missing cache detection
   - Test cache invalidation validation
   - Test cache key design validation
   - Test cache TTL validation
   - Test proper caching validation (should pass)
   - Test cache penetration detection

3. **Algorithm Efficiency** (6 tests)
   - Test O(n²) algorithm detection
   - Test inefficient loop detection
   - Test redundant computation detection
   - Test proper algorithm validation (should pass)
   - Test complexity analysis accuracy
   - Test optimization suggestions

4. **Scalability** (5 tests)
   - Test pagination validation
   - Test batch processing validation
   - Test large dataset handling
   - Test concurrent request handling
   - Test resource usage validation

5. **General Performance** (5 tests)
   - Test eager loading validation
   - Test lazy loading validation
   - Test connection pooling validation
   - Test timeout configuration
   - Test performance metrics collection

**Estimated Tests:** 30-35 tests, ~400 lines

---

#### Task 2.2: Data Integrity Review Agent Tests (2 days)

**File:** `tests/unit/agents/specialists/test_data_integrity_review_agent.py`

**Test Categories:**
1. **Foreign Key Constraints** (7 tests)
   - Test FK presence validation
   - Test FK cascade behavior validation
   - Test orphaned record detection
   - Test circular dependency detection
   - Test proper FK validation (should pass)
   - Test missing FK detection
   - Test FK naming convention validation

2. **Referential Integrity** (6 tests)
   - Test referential integrity checks
   - Test delete cascade validation
   - Test update cascade validation
   - Test null handling validation
   - Test proper referential integrity (should pass)
   - Test integrity violation detection

3. **Transactions** (6 tests)
   - Test transaction boundary validation
   - Test ACID property validation
   - Test rollback logic validation
   - Test isolation level validation
   - Test proper transaction usage (should pass)
   - Test missing transaction detection

4. **Constraints** (6 tests)
   - Test unique constraint validation
   - Test check constraint validation
   - Test NOT NULL validation
   - Test default value validation
   - Test proper constraint usage (should pass)
   - Test missing constraint detection

5. **Data Consistency** (5 tests)
   - Test data type consistency
   - Test validation rule consistency
   - Test business rule validation
   - Test proper consistency checks (should pass)
   - Test consistency violation detection

**Estimated Tests:** 30 tests, ~400 lines

---

#### Task 2.3: Maintainability Review Agent Tests (2 days)

**File:** `tests/unit/agents/specialists/test_maintainability_review_agent.py`

**Test Categories:**
1. **Coupling Analysis** (7 tests)
   - Test tight coupling detection
   - Test dependency count validation
   - Test circular dependency detection
   - Test proper loose coupling (should pass)
   - Test coupling metrics calculation
   - Test abstraction layer validation
   - Test dependency injection validation

2. **Cohesion Analysis** (6 tests)
   - Test low cohesion detection
   - Test single responsibility validation
   - Test method grouping validation
   - Test proper high cohesion (should pass)
   - Test cohesion metrics calculation
   - Test class responsibility validation

3. **Code Complexity** (6 tests)
   - Test cyclomatic complexity calculation
   - Test function length validation
   - Test nesting depth validation
   - Test parameter count validation
   - Test proper complexity (should pass)
   - Test complexity threshold validation

4. **Code Duplication** (5 tests)
   - Test duplicate code detection
   - Test similar pattern detection
   - Test DRY violation detection
   - Test proper abstraction (should pass)
   - Test refactoring suggestions

5. **Separation of Concerns** (5 tests)
   - Test mixed concerns detection
   - Test layering violation detection
   - Test proper separation (should pass)
   - Test architectural boundary validation
   - Test responsibility assignment

**Estimated Tests:** 25-30 tests, ~350 lines

---

### Week 4: Architecture + API Design + Code/Review Models

#### Task 2.4: Architecture Review Agent Tests (2 days)

**File:** `tests/unit/agents/specialists/test_architecture_review_agent.py`

**Test Categories:**
1. **SOLID Principles** (10 tests)
   - Test Single Responsibility Principle validation
   - Test Open/Closed Principle validation
   - Test Liskov Substitution Principle validation
   - Test Interface Segregation Principle validation
   - Test Dependency Inversion Principle validation
   - Test proper SOLID adherence (should pass for each)

2. **Design Patterns** (8 tests)
   - Test design pattern recognition
   - Test anti-pattern detection
   - Test pattern misuse detection
   - Test proper pattern usage (should pass)
   - Test pattern recommendation generation
   - Test pattern consistency validation
   - Test God object detection
   - Test Singleton abuse detection

3. **Layering** (7 tests)
   - Test layer violation detection
   - Test layer dependency direction
   - Test circular layer dependency detection
   - Test proper layering (should pass)
   - Test layer responsibility validation
   - Test cross-layer communication validation
   - Test layer abstraction validation

**Estimated Tests:** 25-30 tests, ~350 lines

---

#### Task 2.5: API Design Review Agent Tests (2 days)

**File:** `tests/unit/agents/specialists/test_api_design_review_agent.py`

**Test Categories:**
1. **RESTful Design** (8 tests)
   - Test HTTP verb usage validation
   - Test resource naming validation
   - Test URL structure validation
   - Test proper REST design (should pass)
   - Test statelessness validation
   - Test idempotency validation
   - Test HATEOAS validation
   - Test resource hierarchy validation

2. **Error Handling** (7 tests)
   - Test HTTP status code usage
   - Test error response format validation
   - Test error message clarity
   - Test proper error handling (should pass)
   - Test error code consistency
   - Test validation error responses
   - Test exception handling validation

3. **API Versioning** (5 tests)
   - Test versioning strategy validation
   - Test backward compatibility
   - Test deprecation handling
   - Test proper versioning (should pass)
   - Test version migration validation

4. **Pagination & Filtering** (5 tests)
   - Test pagination implementation
   - Test filtering parameter validation
   - Test sorting parameter validation
   - Test proper pagination (should pass)
   - Test performance considerations

5. **Documentation** (5 tests)
   - Test API documentation presence
   - Test endpoint documentation completeness
   - Test parameter documentation
   - Test example request/response
   - Test proper documentation (should pass)

**Estimated Tests:** 25-30 tests, ~350 lines

---

#### Task 2.6: Code Models Tests (1 day)

**File:** `tests/unit/models/test_code_models.py`

**Test Categories:**
1. **GeneratedCode Tests** (8 tests)
   - Test code creation
   - Test file collection validation
   - Test validation rules
   - Test JSON serialization
   - Test large codebases
   - Test file path validation
   - Test content encoding
   - Test duplicate file detection

2. **GeneratedFile Tests** (8 tests)
   - Test file creation
   - Test path validation
   - Test content validation
   - Test encoding handling
   - Test binary file handling
   - Test large file handling
   - Test JSON serialization
   - Test security validation (path traversal)

**Estimated Tests:** 15-20 tests, ~300 lines

---

#### Task 2.7: Code Review Models Tests (1 day)

**File:** `tests/unit/models/test_code_review_models.py`

**Test Categories:**
1. **CodeIssue Tests** (10 tests)
   - Test issue creation
   - Test severity validation
   - Test category validation
   - Test line number validation
   - Test file path validation
   - Test description validation
   - Test suggestion validation
   - Test JSON serialization
   - Test issue equality comparison
   - Test issue sorting

2. **CodeReviewReport Tests** (10 tests)
   - Test report creation
   - Test issue aggregation
   - Test pass/fail determination
   - Test severity distribution
   - Test category distribution
   - Test JSON serialization
   - Test report summary generation
   - Test filtering by severity
   - Test filtering by category
   - Test empty report handling

**Estimated Tests:** 20-25 tests, ~350 lines

---

## Phase 3: Integration & Polish (Week 4)

**Goal:** Add integration tests and edge case coverage

**Effort:** ~400-500 lines, 40 tests

#### Task 3.1: Error Handling Tests (2 days)

**File:** `tests/unit/test_error_handling.py`

**Test Categories:**
1. **Agent Failure Recovery** (5 tests)
   - Test agent crash recovery
   - Test agent timeout recovery
   - Test partial failure handling
   - Test retry logic
   - Test fallback mechanisms

2. **Telemetry Failure Handling** (4 tests)
   - Test database unavailable scenario
   - Test Langfuse unavailable scenario
   - Test partial telemetry write failures
   - Test telemetry queue overflow

3. **Database Errors** (4 tests)
   - Test connection errors
   - Test write errors
   - Test constraint violations
   - Test transaction failures

4. **LLM API Failures** (4 tests)
   - Test API timeout
   - Test API rate limiting
   - Test API authentication errors
   - Test malformed API responses

**Estimated Tests:** 15-20 tests, ~250 lines

---

#### Task 3.2: Full Pipeline E2E Tests (2 days)

**File:** `tests/integration/test_full_pipeline_e2e.py`

**Test Categories:**
1. **Happy Path** (3 tests)
   - Test Requirements → Planning → Design → Review → Code → Test (all pass)
   - Test with small project
   - Test with medium project

2. **Review Failure Loops** (3 tests)
   - Test design review failure → loop back to design
   - Test code review failure → loop back to code
   - Test multiple iteration convergence

3. **Cross-Agent Data Flow** (2 tests)
   - Test data propagation through pipeline
   - Test telemetry collection throughout pipeline

4. **End-to-End Telemetry** (2 tests)
   - Test complete telemetry collection
   - Test cost tracking accuracy

**Estimated Tests:** 8-10 tests, ~350 lines

---

#### Task 3.3: Markdown Renderer Edge Cases (1 day)

**File:** Extend `tests/unit/test_markdown_renderer.py`

**Test Categories:**
1. **Complex Nesting** (3 tests)
   - Test deeply nested structures
   - Test mixed content types
   - Test edge case combinations

2. **Malformed Input** (3 tests)
   - Test malformed markdown
   - Test incomplete structures
   - Test invalid characters

3. **Performance** (3 tests)
   - Test very large outputs
   - Test rendering performance
   - Test memory usage

**Estimated Tests:** 10-15 additional tests, ~150 lines

---

## Testing Fixtures (Shared)

Create shared fixtures in `tests/conftest.py`:

```python
@pytest.fixture
def mock_llm_client():
    """Returns a mocked LLM client for testing."""
    # Implementation

@pytest.fixture
def mock_database():
    """Returns an in-memory SQLite database for testing."""
    # Implementation

@pytest.fixture
def mock_langfuse():
    """Returns a mocked Langfuse client."""
    # Implementation

@pytest.fixture
def sample_task_requirements():
    """Returns valid task requirements for testing."""
    # Implementation

@pytest.fixture
def sample_design_spec():
    """Returns valid design specification for testing."""
    # Implementation

@pytest.fixture
def sample_code():
    """Returns sample generated code for testing."""
    # Implementation

@pytest.fixture
def vulnerable_code_samples():
    """Returns code samples with known vulnerabilities."""
    # Implementation

@pytest.fixture
def secure_code_samples():
    """Returns code samples following best practices."""
    # Implementation
```

---

## Parallel Development Strategy

### Option 1: Two Developers

**Developer A (Focus: Agents + Orchestrator)**
- Week 1: Design Review Orchestrator + Security Review Agent
- Week 2: Performance + Data Integrity Review Agents
- Week 3: Maintainability + Architecture + API Design Review Agents

**Developer B (Focus: Models + Infrastructure)**
- Week 1: Telemetry + Planning Models + Design Models
- Week 2: Code Models + Code Review Models
- Week 3: Error Handling + Full Pipeline E2E + Edge Cases

**Total Time:** ~2 weeks (with overlap and parallel work)

---

### Option 2: Sprint-Based (Single Developer)

**Sprint 1 (Week 1-2): Critical Foundation**
- Design Review Orchestrator
- Security Review Agent
- Telemetry
- Planning + Design Models

**Sprint 2 (Week 3): Review Agents (Part 1)**
- Performance Review Agent
- Data Integrity Review Agent
- Maintainability Review Agent

**Sprint 3 (Week 4): Review Agents (Part 2) + Models**
- Architecture Review Agent
- API Design Review Agent
- Code Models + Code Review Models

**Sprint 4 (Optional Week 5): Integration & Polish**
- Error Handling
- Full Pipeline E2E
- Edge Cases

**Total Time:** ~3-4 weeks

---

## Success Metrics

### Coverage Targets

| Component | Current | Target | Priority |
|-----------|---------|--------|----------|
| Overall | ~85% | 95% | HIGH |
| Models | <5% | 90% | CRITICAL |
| Telemetry | 0% | 85% | CRITICAL |
| Review Agents (specialists) | 0% | 90% | CRITICAL |
| Design Review Orchestrator | 0% | 95% | CRITICAL |
| Utilities | 100% | 100% | MAINTAIN |
| Core Agents (Planning, Design, Code) | 80% | 90% | HIGH |

### Quality Gates

Before considering implementation complete:

1. **Coverage:** All new test files achieve 85%+ coverage
2. **Test Quality:** All tests have descriptive docstrings
3. **CI/CD:** All tests pass in CI pipeline
4. **Performance:** Test suite completes in <5 minutes
5. **Documentation:** All new test patterns documented
6. **Review:** All test code reviewed by senior developer

---

## Risks & Mitigation

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| **LLM mocking complexity** | High | Medium | Create comprehensive mock library early |
| **Test suite runtime too slow** | Medium | High | Use markers to split fast/slow tests, optimize fixtures |
| **Telemetry tests flaky** | Medium | Medium | Use deterministic time mocking, isolate database |
| **Coverage tool inaccuracies** | Low | Medium | Manual code review to supplement coverage reports |
| **Scope creep** | High | Medium | Stick to documented plan, defer nice-to-haves |

---

## Tools & Commands

### Running Tests

```bash
# Run all tests
uv run pytest

# Run only new tests
uv run pytest tests/unit/agents/specialists/
uv run pytest tests/unit/models/
uv run pytest tests/unit/telemetry/

# Run with coverage
uv run pytest --cov=src/asp --cov-report=html

# Run specific test categories
uv run pytest -m unit
uv run pytest -m integration

# Run fast tests only (during development)
uv run pytest -m "not slow"
```

### Coverage Reports

```bash
# Generate HTML coverage report
uv run pytest --cov=src/asp --cov-report=html
open htmlcov/index.html

# Generate terminal coverage report
uv run pytest --cov=src/asp --cov-report=term-missing

# Coverage for specific module
uv run pytest --cov=src/asp/telemetry tests/unit/telemetry/
```

---

## Next Steps

1. **Review this plan** with engineering team
2. **Assign developers** to Phase 1 tasks
3. **Set up tracking** (Jira, Linear, or GitHub Projects)
4. **Create kick-off issue** with Phase 1 checklist
5. **Begin implementation** following priority order

For questions or clarifications, see [Test Coverage Analysis](test_coverage_analysis.md).

---

## Appendix: Test Template

```python
"""
Tests for [Component Name].

This module tests [brief description of what is being tested].
"""

import pytest
from unittest.mock import Mock, patch

from src.asp.[module] import [Component]


class Test[Component]:
    """Test suite for [Component]."""

    @pytest.fixture
    def component(self):
        """Create a [Component] instance for testing."""
        return [Component]()

    def test_[specific_behavior](self, component):
        """
        Test that [Component] [does something specific].

        Given: [preconditions]
        When: [action]
        Then: [expected outcome]
        """
        # Arrange
        # ...

        # Act
        result = component.method()

        # Assert
        assert result == expected_value
        assert component.state == expected_state

    # More tests...
```

---

**Status:** Ready for Implementation
**Next Review:** After Phase 1 completion
