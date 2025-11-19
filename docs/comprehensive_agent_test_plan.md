# Comprehensive Agent Test Plan

**Document Version**: 1.0.0
**Date**: 2025-11-19
**Status**: Active
**Purpose**: Execute and validate all 21 agents in the ASP Platform

---

## Executive Summary

This test plan provides comprehensive coverage for all 21 agents in the Agentic Software Process (ASP) Platform:
- **7 Core Agents** (PSP/TSP workflow)
- **2 Orchestrator Agents** (coordination layer)
- **12 Specialist Review Agents** (design + code review)

**Test Strategy**: Multi-level testing approach
1. **Unit Tests** - Individual agent functionality
2. **Integration Tests** - Agent-to-agent interactions
3. **End-to-End Tests** - Complete workflow validation
4. **Performance Tests** - Latency and cost metrics

---

## Table of Contents

1. [Test Environment Setup](#test-environment-setup)
2. [Core Agents Test Plan](#core-agents-test-plan)
3. [Orchestrator Agents Test Plan](#orchestrator-agents-test-plan)
4. [Specialist Review Agents Test Plan](#specialist-review-agents-test-plan)
5. [Integration Test Plan](#integration-test-plan)
6. [Performance Test Plan](#performance-test-plan)
7. [Test Execution Instructions](#test-execution-instructions)
8. [Success Criteria](#success-criteria)

---

## Test Environment Setup

### Prerequisites

```bash
# 1. Install dependencies
pip install -e ".[dev]"

# 2. Set up environment variables
export ANTHROPIC_API_KEY="your_key_here"
export OPENAI_API_KEY="your_key_here"
export LANGFUSE_PUBLIC_KEY="your_key_here"
export LANGFUSE_SECRET_KEY="your_key_here"
export LANGFUSE_HOST="https://cloud.langfuse.com"

# 3. Verify pytest is available
pytest --version
```

### Test Data Requirements

- **Bootstrap Data**: 12 planning tasks (already collected in `bootstrap_data/`)
- **Sample Requirements**: Test requirements documents
- **Mock Data**: For unit tests (mocked LLM responses)

---

## Core Agents Test Plan

### 1. Planning Agent (FR-1)

**File**: `src/asp/agents/planning_agent.py`

#### Test Objectives
- ✅ Task decomposition into semantic units
- ✅ Semantic complexity calculation (C1 formula)
- ✅ PROBE-AI estimation (after 10 tasks)
- ✅ Bootstrap data collection
- ✅ Telemetry tracking

#### Test Cases

##### TC-PA-001: Basic Task Decomposition
```python
# Test: tests/unit/test_agents/test_planning_agent.py::test_plan_with_llm_basic
Input: Simple task requirements (e.g., "Create a user authentication system")
Expected Output:
  - ProjectPlan with 3-7 semantic units
  - Each unit has: name, description, inputs, outputs, complexity score
  - Total complexity > 0
```

##### TC-PA-002: Semantic Complexity Calculation
```python
# Test: tests/unit/test_agents/test_planning_agent.py::test_semantic_complexity_integration
Input: Task with known complexity characteristics
Expected Output:
  - Each semantic unit has C1 score (0.1 - 100+ range)
  - Scores reflect relative complexity
  - Metadata includes: code_loc, data_vars, control_flow_depth
```

##### TC-PA-003: PROBE-AI Estimation
```python
# Test: tests/e2e/test_planning_agent_e2e.py::test_probe_ai_estimation
Input: 11th task (after collecting 10 bootstrap tasks)
Expected Output:
  - Linear regression model parameters (β0, β1)
  - Effort estimates (design_hours, code_hours, test_hours)
  - Estimation uncertainty metrics
```

##### TC-PA-004: Artifact Persistence
```python
# Test: tests/unit/test_agents/test_planning_agent.py::test_artifact_generation
Input: Any task requirements
Expected Output:
  - artifacts/plans/plan_{task_id}.json created
  - artifacts/plans/plan_{task_id}.md created
  - JSON matches Pydantic schema
  - Markdown is human-readable
```

##### TC-PA-005: Telemetry Tracking
```python
# Test: tests/unit/test_agents/test_planning_agent.py::test_telemetry_tracking
Input: Any task requirements
Expected Telemetry:
  - @track_agent_cost decorator fires
  - Langfuse trace created with:
    * Agent name: "Planning Agent"
    * Input tokens, output tokens, cost
    * Latency measurements
```

#### Execution Command
```bash
# Unit tests (102 tests)
pytest tests/unit/test_agents/test_planning_agent.py -v

# E2E tests (8 tests)
pytest tests/e2e/test_planning_agent_e2e.py -v

# Coverage report
pytest tests/unit/test_agents/test_planning_agent.py --cov=src/asp/agents/planning_agent --cov-report=html
```

#### Success Criteria
- ✅ All 110 tests pass
- ✅ Code coverage > 90%
- ✅ PROBE-AI activates after 10 tasks
- ✅ Artifacts generated correctly
- ✅ Telemetry data visible in Langfuse

---

### 2. Design Agent (FR-2)

**File**: `src/asp/agents/design_agent.py`

#### Test Objectives
- ✅ Transform requirements + plan into design specification
- ✅ Generate API contracts, data schemas, component logic
- ✅ Create design review checklists
- ✅ Markdown rendering

#### Test Cases

##### TC-DA-001: Design Specification Generation
```python
# Test: tests/unit/test_agents/test_design_agent.py::test_design_agent_basic
Input: DesignInput (requirements + ProjectPlan from Planning Agent)
Expected Output:
  - DesignSpecification with:
    * api_contracts: List of endpoint specs (method, path, request/response)
    * data_schemas: Entity definitions with fields and relationships
    * component_logic: Implementation details for each component
    * design_review_checklist: Quality validation items
```

##### TC-DA-002: API Contract Validation
```python
# Test: tests/unit/test_agents/test_design_agent.py::test_api_contracts
Input: Requirements for REST API
Expected Output:
  - Each API contract includes:
    * HTTP method (GET, POST, PUT, DELETE)
    * Endpoint path (e.g., /api/users/{id})
    * Request schema (headers, body, query params)
    * Response schema (success + error cases)
    * Status codes (200, 400, 404, 500, etc.)
```

##### TC-DA-003: Data Schema Generation
```python
# Test: tests/unit/test_agents/test_design_agent.py::test_data_schemas
Input: Requirements with data entities
Expected Output:
  - Each schema includes:
    * Entity name
    * Fields (name, type, constraints)
    * Relationships (foreign keys, joins)
    * Indexes for performance
```

##### TC-DA-004: Design Review Checklist
```python
# Test: tests/unit/test_agents/test_design_agent.py::test_checklist_generation
Expected Checklist Items:
  - Security considerations (auth, encryption, validation)
  - Performance considerations (indexing, caching)
  - Data integrity (constraints, transactions)
  - Maintainability (coupling, cohesion)
  - API design (RESTful, error handling)
```

##### TC-DA-005: Markdown Rendering
```python
# Test: tests/unit/test_agents/test_design_agent.py::test_markdown_output
Expected Output:
  - artifacts/designs/design_{task_id}.md created
  - Sections: Overview, API Contracts, Data Schemas, Component Logic, Checklist
  - Valid markdown syntax
```

#### Execution Command
```bash
# Unit tests (23 tests)
pytest tests/unit/test_agents/test_design_agent.py -v

# E2E tests (5 tests)
pytest tests/e2e/test_design_agent_e2e.py -v

# Coverage report
pytest tests/unit/test_agents/test_design_agent.py --cov=src/asp/agents/design_agent --cov-report=html
```

#### Success Criteria
- ✅ All 28 tests pass
- ✅ Design specs are implementation-ready
- ✅ API contracts follow RESTful conventions
- ✅ Data schemas include proper constraints

---

### 3. Design Review Agent (FR-3)

**File**: `src/asp/agents/design_review_agent.py`

#### Test Objectives
- ✅ Automated validation checks (structural)
- ✅ LLM-based deep review (quality)
- ✅ Pass/Fail quality gate enforcement
- ✅ Coordination with 6 specialist agents

#### Test Cases

##### TC-DRA-001: Structural Validation
```python
# Test: tests/unit/test_agents/test_design_review_agent.py::test_structural_validation
Input: DesignSpecification (valid and invalid variants)
Expected Output:
  - Valid: No structural issues
  - Invalid: Issues like missing API contracts, empty schemas, etc.
```

##### TC-DRA-002: LLM-Based Deep Review
```python
# Test: tests/unit/test_agents/test_design_review_agent.py::test_llm_review
Input: DesignSpecification with subtle issues
Expected Output:
  - DesignReviewReport with:
    * review_status: PASS or FAIL
    * overall_summary: High-level assessment
    * issues: List of DesignIssue (severity, category, description)
    * suggestions: Improvement recommendations
```

##### TC-DRA-003: Quality Gate Enforcement
```python
# Test: tests/unit/test_agents/test_design_review_agent.py::test_quality_gate
Input: DesignSpecification with major security flaw
Expected Output:
  - review_status: FAIL
  - At least one MAJOR or CRITICAL severity issue
  - Clear description of what needs fixing
```

##### TC-DRA-004: Specialist Coordination
```python
# Test: tests/unit/test_agents/test_design_review_orchestrator.py::test_orchestrator
Expected Behavior:
  - 6 specialist agents invoked in parallel
  - Results aggregated from all specialists
  - Duplicate issues removed
  - Unified report generated
```

##### TC-DRA-005: Performance Metrics
```python
# Test: tests/e2e/test_design_review_agent_e2e.py::test_performance
Expected Metrics:
  - Latency: 25-40 seconds
  - Cost: $0.15-0.25 per review
  - Parallelization reduces time by ~5x vs. sequential
```

#### Execution Command
```bash
# Unit tests (21 tests)
pytest tests/unit/test_agents/test_design_review_agent.py -v
pytest tests/unit/test_agents/test_design_review_orchestrator.py -v

# E2E tests (3 tests)
pytest tests/e2e/test_design_review_agent_e2e.py -v

# Coverage report
pytest tests/unit/test_agents/test_design_review_*.py --cov=src/asp/agents/design_review_agent --cov-report=html
```

#### Success Criteria
- ✅ All 24 tests pass
- ✅ Quality gate blocks bad designs
- ✅ Specialist agents run in parallel
- ✅ Performance within expected range

---

### 4. Code Agent (FR-4)

**File**: `src/asp/agents/code_agent.py`

#### Test Objectives
- ✅ Generate production-ready code from design specs
- ✅ Create complete file contents (source, tests, config)
- ✅ Adhere to coding standards
- ✅ Calculate lines of code (LOC)

#### Test Cases

##### TC-CA-001: Code Generation
```python
# Test: tests/unit/test_agents/test_code_agent.py::test_code_generation
Input: CodeInput (design_specification + coding_standards)
Expected Output:
  - GeneratedCode with:
    * files: List of GeneratedFile (path, content, language)
    * total_lines_of_code: Accurate LOC count
    * implementation_notes: Key decisions, assumptions
```

##### TC-CA-002: File Structure
```python
# Test: tests/unit/test_agents/test_code_agent.py::test_file_structure
Expected Files:
  - Source code files (.py, .js, etc.)
  - Test files (test_*.py, *.test.js)
  - Configuration files (setup.py, package.json)
  - Documentation (README.md, docstrings)
```

##### TC-CA-003: Coding Standards Compliance
```python
# Test: tests/unit/test_agents/test_code_agent.py::test_coding_standards
Input: Coding standards (e.g., PEP 8, ESLint rules)
Expected Output:
  - Code follows specified standards
  - Consistent naming conventions
  - Proper indentation and formatting
```

##### TC-CA-004: Completeness
```python
# Test: tests/unit/test_agents/test_code_agent.py::test_completeness
Expected Output:
  - All components from design spec implemented
  - All API endpoints have handlers
  - All data schemas have models
  - No placeholder or TODO comments
```

##### TC-CA-005: Artifact Persistence
```python
# Test: tests/unit/test_agents/test_code_agent.py::test_artifact_generation
Expected Artifacts:
  - artifacts/code/code_{task_id}/*.py (actual code files)
  - artifacts/code/code_{task_id}.json (metadata)
```

#### Execution Command
```bash
# Unit tests
pytest tests/unit/test_agents/test_code_agent.py -v

# E2E tests
pytest tests/e2e/test_code_agent_e2e.py -v

# Coverage report
pytest tests/unit/test_agents/test_code_agent.py --cov=src/asp/agents/code_agent --cov-report=html
```

#### Success Criteria
- ✅ All tests pass
- ✅ Generated code is syntactically valid
- ✅ Code implements all design requirements
- ✅ Coding standards enforced

---

### 5. Code Review Agent (FR-5)

**File**: `src/asp/agents/code_review_orchestrator.py`

#### Test Objectives
- ✅ Coordinate 6 specialist code review agents
- ✅ Validate code against coding standards
- ✅ Pass/Fail quality gate enforcement
- ✅ Deduplication of issues

#### Test Cases

##### TC-CRA-001: Code Quality Validation
```python
# Test: tests/unit/test_agents/test_code_review_orchestrator.py::test_code_quality
Input: GeneratedCode with quality issues
Expected Output:
  - CodeReviewReport with:
    * review_status: PASS or FAIL
    * issues: Categorized by specialist
    * suggestions: Actionable improvements
```

##### TC-CRA-002: Specialist Coordination
```python
# Test: tests/unit/test_agents/test_code_review_orchestrator.py::test_orchestration
Expected Behavior:
  - 6 specialist agents invoked in parallel:
    1. Code Quality Review Agent
    2. Code Security Review Agent
    3. Code Performance Review Agent
    4. Test Coverage Review Agent
    5. Documentation Review Agent
    6. Best Practices Review Agent
  - Results aggregated
  - Duplicate issues removed
```

##### TC-CRA-003: Security Vulnerability Detection
```python
# Test: tests/unit/test_agents/code_reviews/test_all_code_review_specialists.py::test_security
Input: Code with SQL injection vulnerability
Expected Output:
  - Security specialist flags the issue
  - Severity: CRITICAL
  - Category: Security
  - Suggestion includes fix
```

##### TC-CRA-004: Performance Issue Detection
```python
# Test: tests/unit/test_agents/code_reviews/test_all_code_review_specialists.py::test_performance
Input: Code with N+1 query problem
Expected Output:
  - Performance specialist flags the issue
  - Severity: MAJOR
  - Suggestion: Use eager loading / joins
```

##### TC-CRA-005: Quality Gate Enforcement
```python
# Test: tests/unit/test_agents/test_code_review_orchestrator.py::test_quality_gate
Input: Code with critical issues
Expected Output:
  - review_status: FAIL
  - Process loops back to Code Agent
```

#### Execution Command
```bash
# Unit tests
pytest tests/unit/test_agents/test_code_review_orchestrator.py -v
pytest tests/unit/test_agents/code_reviews/test_all_code_review_specialists.py -v

# Coverage report
pytest tests/unit/test_agents/test_code_review_*.py --cov=src/asp/agents/code_review_orchestrator --cov-report=html
```

#### Success Criteria
- ✅ All tests pass
- ✅ All 6 specialists execute in parallel
- ✅ Security vulnerabilities detected
- ✅ Quality gate blocks bad code

---

### 6. Test Agent (FR-6)

**File**: `src/asp/agents/test_agent.py`

#### Test Objectives
- ✅ Build validation (compilation, imports)
- ✅ Test generation from design specs
- ✅ Test execution and coverage measurement
- ✅ Defect logging with AI Defect Taxonomy

#### Test Cases

##### TC-TA-001: Build Validation
```python
# Test: tests/unit/test_agents/test_test_agent.py::test_build_validation
Input: GeneratedCode (valid and invalid variants)
Expected Output:
  - Valid code: build_status = SUCCESS
  - Invalid code: build_status = FAILED, error messages
```

##### TC-TA-002: Test Generation
```python
# Test: tests/unit/test_agents/test_test_agent.py::test_test_generation
Input: TestInput (generated_code + design_specification)
Expected Output:
  - Comprehensive unit tests for all components
  - Edge case coverage
  - Happy path + error path tests
```

##### TC-TA-003: Test Execution
```python
# Test: tests/unit/test_agents/test_test_agent.py::test_test_execution
Input: Generated tests
Expected Output:
  - TestReport with:
    * test_status: PASSED or FAILED
    * test_summary: Total tests, passed, failed, skipped
    * coverage_metrics: Line coverage, branch coverage
```

##### TC-TA-004: Defect Logging (AI Defect Taxonomy)
```python
# Test: tests/unit/test_agents/test_test_agent.py::test_defect_taxonomy
Input: Failed test results
Expected Output:
  - TestDefect records with classification:
    1. Planning_Failure
    2. Prompt_Misinterpretation
    3. Tool_Use_Error
    4. Hallucination
    5. Security_Vulnerability
    6. Conventional_Code_Bug
    7. Task_Execution_Error
    8. Alignment_Deviation
  - Each defect has: type, severity, description, root_cause, fix_effort
```

##### TC-TA-005: Coverage Metrics
```python
# Test: tests/unit/test_agents/test_test_agent.py::test_coverage_metrics
Expected Metrics:
  - Line coverage percentage
  - Branch coverage percentage
  - Uncovered lines identified
  - Coverage report generated
```

#### Execution Command
```bash
# Unit tests
pytest tests/unit/test_agents/test_test_agent.py -v

# Coverage report
pytest tests/unit/test_agents/test_test_agent.py --cov=src/asp/agents/test_agent --cov-report=html
```

#### Success Criteria
- ✅ All tests pass
- ✅ Build validation detects compilation errors
- ✅ Generated tests are comprehensive
- ✅ AI Defect Taxonomy correctly classifies defects

---

### 7. Postmortem Agent (FR-7)

**File**: `src/asp/agents/postmortem_agent.py`

#### Test Objectives
- ✅ Performance analysis (planned vs. actual)
- ✅ Root cause analysis (defect types)
- ✅ Process Improvement Proposal (PIP) generation
- ✅ Self-improvement recommendations

#### Test Cases

##### TC-PMA-001: Performance Analysis
```python
# Test: tests/unit/test_agents/test_postmortem_agent.py::test_performance_analysis
Input: PostmortemInput (plan, effort_log, defect_log, actual_complexity)
Expected Output:
  - PostmortemReport with:
    * estimation_accuracy: Planned vs. actual metrics
    * variance_analysis: % deviation by phase
    * cost_breakdown: Design, code, test, review efforts
```

##### TC-PMA-002: Root Cause Analysis
```python
# Test: tests/unit/test_agents/test_postmortem_agent.py::test_root_cause_analysis
Input: Defect log with multiple defect types
Expected Output:
  - root_cause_items: Top defect types ranked by fix effort
  - Includes:
    * Defect type
    * Frequency
    * Total fix effort (minutes/hours)
    * Percentage of total effort
```

##### TC-PMA-003: Process Improvement Proposal (PIP)
```python
# Test: tests/unit/test_agents/test_postmortem_agent.py::test_pip_generation
Input: Analysis showing recurring Planning_Failure defects
Expected Output:
  - ProcessImprovementProposal with:
    * problem_statement: Root cause description
    * proposed_changes: Specific improvements
      - Prompt modifications
      - Checklist additions
      - Workflow adjustments
    * expected_impact: Reduction in defect type
    * hitl_approval_status: PENDING
```

##### TC-PMA-004: Quality Metrics
```python
# Test: tests/unit/test_agents/test_postmortem_agent.py::test_quality_metrics
Expected Metrics:
  - Defect density (defects per KLOC)
  - Defect phase distribution (design, code, test)
  - Review effectiveness (defects caught in review vs. test)
  - Fix rate (defects fixed per hour)
```

##### TC-PMA-005: Self-Improvement
```python
# Test: tests/unit/test_agents/test_postmortem_agent.py::test_self_improvement
Expected Behavior:
  - PIP includes actionable changes to agent prompts
  - PIP references specific defect patterns
  - Changes are HITL-approved before applying
```

#### Execution Command
```bash
# Unit tests
pytest tests/unit/test_agents/test_postmortem_agent.py -v

# Coverage report
pytest tests/unit/test_agents/test_postmortem_agent.py --cov=src/asp/agents/postmortem_agent --cov-report=html
```

#### Success Criteria
- ✅ All tests pass
- ✅ Performance analysis accurate
- ✅ Root cause analysis identifies top issues
- ✅ PIPs are actionable and specific

---

## Orchestrator Agents Test Plan

### 8. Design Review Orchestrator

**File**: `src/asp/agents/design_review_orchestrator.py`

#### Test Objectives
- ✅ Parallel invocation of 6 design review specialists
- ✅ Result aggregation
- ✅ Deduplication of overlapping issues
- ✅ Conflict resolution

#### Test Cases

##### TC-DRO-001: Parallel Execution
```python
# Test: tests/unit/test_agents/test_design_review_orchestrator.py::test_parallel_execution
Expected Behavior:
  - All 6 specialists invoked simultaneously
  - Latency ~5x better than sequential
  - No race conditions
```

##### TC-DRO-002: Result Aggregation
```python
# Test: tests/unit/test_agents/test_design_review_orchestrator.py::test_aggregation
Input: Design spec with issues detected by multiple specialists
Expected Output:
  - Single unified DesignReviewReport
  - All issues from all specialists included
  - Issues categorized by specialist
```

##### TC-DRO-003: Deduplication
```python
# Test: tests/unit/test_agents/test_design_review_orchestrator.py::test_deduplication
Input: Design spec with issue detected by multiple specialists (e.g., security + API design both flag auth issue)
Expected Output:
  - Duplicate issues merged
  - Most severe severity retained
  - Combined descriptions
```

##### TC-DRO-004: Conflict Resolution
```python
# Test: tests/unit/test_agents/test_design_review_orchestrator.py::test_conflict_resolution
Input: Conflicting recommendations from specialists
Expected Behavior:
  - Orchestrator prioritizes based on severity
  - CRITICAL issues take precedence
  - Both perspectives documented
```

#### Execution Command
```bash
pytest tests/unit/test_agents/test_design_review_orchestrator.py -v
```

#### Success Criteria
- ✅ All tests pass
- ✅ Parallel execution confirmed
- ✅ Deduplication works correctly
- ✅ No data loss during aggregation

---

### 9. Code Review Orchestrator

**File**: `src/asp/agents/code_review_orchestrator.py`

#### Test Objectives
- ✅ Parallel invocation of 6 code review specialists
- ✅ Result aggregation
- ✅ Deduplication of overlapping issues
- ✅ Quality gate enforcement

#### Test Cases

##### TC-CRO-001: Parallel Execution
```python
# Test: tests/unit/test_agents/test_code_review_orchestrator.py::test_parallel_execution
Expected Behavior:
  - All 6 specialists invoked simultaneously
  - Latency optimized
  - No race conditions
```

##### TC-CRO-002: Result Aggregation
```python
# Test: tests/unit/test_agents/test_code_review_orchestrator.py::test_aggregation
Expected Output:
  - Single unified CodeReviewReport
  - All issues from all specialists included
  - Issues categorized by specialist
```

##### TC-CRO-003: Deduplication
```python
# Test: tests/unit/test_agents/test_code_review_orchestrator.py::test_deduplication
Input: Code with issue detected by multiple specialists
Expected Output:
  - Duplicate issues merged
  - Most severe severity retained
```

##### TC-CRO-004: Quality Gate
```python
# Test: tests/unit/test_agents/test_code_review_orchestrator.py::test_quality_gate
Input: Code with critical issues
Expected Output:
  - review_status: FAIL
  - Process halted until fixes applied
```

#### Execution Command
```bash
pytest tests/unit/test_agents/test_code_review_orchestrator.py -v
```

#### Success Criteria
- ✅ All tests pass
- ✅ Parallel execution confirmed
- ✅ Quality gate enforced

---

## Specialist Review Agents Test Plan

### 10-15. Design Review Specialists (6 Agents)

**Files**:
- `src/asp/agents/reviews/security_review_agent.py`
- `src/asp/agents/reviews/performance_review_agent.py`
- `src/asp/agents/reviews/data_integrity_review_agent.py`
- `src/asp/agents/reviews/maintainability_review_agent.py`
- `src/asp/agents/reviews/architecture_review_agent.py`
- `src/asp/agents/reviews/api_design_review_agent.py`

#### Test Objectives
- ✅ Each specialist detects issues in their domain
- ✅ Specialists provide actionable suggestions
- ✅ Severity levels correctly assigned
- ✅ No false positives on valid designs

#### Test Cases

##### TC-DRS-001: Security Review Agent
```python
# Test: tests/unit/test_agents/reviews/test_security_review_agent.py::test_security_issues
Input: Design with security flaws (e.g., missing auth, weak encryption)
Expected Output:
  - Issues flagged:
    * Missing authentication on sensitive endpoints
    * Weak password hashing (MD5 instead of bcrypt)
    * SQL injection vulnerability (unsanitized inputs)
    * Missing HTTPS enforcement
  - Severity: CRITICAL or MAJOR
  - Suggestions include specific fixes
```

##### TC-DRS-002: Performance Review Agent
```python
# Test: tests/unit/test_agents/reviews/test_performance_review_agent.py::test_performance_issues
Input: Design with performance issues (e.g., missing indexes, N+1 queries)
Expected Output:
  - Issues flagged:
    * Missing database indexes on frequently queried fields
    * N+1 query problem in API design
    * No caching strategy for expensive operations
  - Severity: MAJOR or MODERATE
  - Suggestions include indexing strategies, caching approaches
```

##### TC-DRS-003: Data Integrity Review Agent
```python
# Test: tests/unit/test_agents/reviews/test_data_integrity_review_agent.py::test_data_integrity_issues
Input: Design with data integrity issues (e.g., missing foreign keys)
Expected Output:
  - Issues flagged:
    * Missing foreign key constraints
    * No referential integrity enforcement
    * Missing transactions for multi-table updates
  - Severity: MAJOR
  - Suggestions include constraint definitions
```

##### TC-DRS-004: Maintainability Review Agent
```python
# Test: tests/unit/test_agents/reviews/test_maintainability_review_agent.py::test_maintainability_issues
Input: Design with high coupling, low cohesion
Expected Output:
  - Issues flagged:
    * Tight coupling between modules
    * God object (class with too many responsibilities)
    * Missing separation of concerns
  - Severity: MODERATE
  - Suggestions include refactoring strategies
```

##### TC-DRS-005: Architecture Review Agent
```python
# Test: tests/unit/test_agents/reviews/test_architecture_review_agent.py::test_architecture_issues
Input: Design violating SOLID principles
Expected Output:
  - Issues flagged:
    * Single Responsibility Principle violation
    * Missing dependency injection
    * Circular dependencies
  - Severity: MAJOR or MODERATE
  - Suggestions include architectural patterns
```

##### TC-DRS-006: API Design Review Agent
```python
# Test: tests/unit/test_agents/reviews/test_api_design_review_agent.py::test_api_design_issues
Input: Non-RESTful API design
Expected Output:
  - Issues flagged:
    * Non-standard HTTP methods
    * Inconsistent endpoint naming
    * Missing error response schemas
    * No API versioning strategy
  - Severity: MODERATE or MINOR
  - Suggestions include RESTful best practices
```

#### Execution Command
```bash
# Run all design review specialist tests
pytest tests/unit/test_agents/reviews/ -v

# Run individual specialist tests
pytest tests/unit/test_agents/reviews/test_security_review_agent.py -v
pytest tests/unit/test_agents/reviews/test_performance_review_agent.py -v
pytest tests/unit/test_agents/reviews/test_data_integrity_review_agent.py -v
pytest tests/unit/test_agents/reviews/test_maintainability_review_agent.py -v
pytest tests/unit/test_agents/reviews/test_architecture_review_agent.py -v
pytest tests/unit/test_agents/reviews/test_api_design_review_agent.py -v
```

#### Success Criteria
- ✅ Each specialist detects issues in their domain
- ✅ No cross-domain false positives
- ✅ Suggestions are actionable

---

### 16-21. Code Review Specialists (6 Agents)

**Files**:
- `src/asp/agents/code_reviews/code_quality_review_agent.py`
- `src/asp/agents/code_reviews/code_security_review_agent.py`
- `src/asp/agents/code_reviews/code_performance_review_agent.py`
- `src/asp/agents/code_reviews/test_coverage_review_agent.py`
- `src/asp/agents/code_reviews/documentation_review_agent.py`
- `src/asp/agents/code_reviews/best_practices_review_agent.py`

#### Test Objectives
- ✅ Each specialist detects issues in their domain
- ✅ Code-level validation (not design-level)
- ✅ Language-specific checks
- ✅ Actionable fix suggestions

#### Test Cases

##### TC-CRS-001: Code Quality Review Agent
```python
# Test: tests/unit/test_agents/code_reviews/test_all_code_review_specialists.py::test_code_quality
Input: Code with quality issues (e.g., code smells, PEP 8 violations)
Expected Output:
  - Issues flagged:
    * Long methods (>50 lines)
    * High cyclomatic complexity
    * Code duplication (DRY violation)
    * PEP 8 formatting issues
  - Severity: MODERATE or MINOR
  - Suggestions include refactoring techniques
```

##### TC-CRS-002: Code Security Review Agent
```python
# Test: tests/unit/test_agents/code_reviews/test_all_code_review_specialists.py::test_code_security
Input: Code with security vulnerabilities
Expected Output:
  - Issues flagged:
    * Hardcoded API keys or passwords
    * SQL injection (unsanitized user input)
    * XSS vulnerability (unescaped output)
    * Insecure deserialization
  - Severity: CRITICAL
  - Suggestions include secure coding practices
```

##### TC-CRS-003: Code Performance Review Agent
```python
# Test: tests/unit/test_agents/code_reviews/test_all_code_review_specialists.py::test_code_performance
Input: Code with performance issues
Expected Output:
  - Issues flagged:
    * Inefficient algorithms (O(n²) when O(n log n) possible)
    * Unnecessary database queries in loops
    * Memory leaks (unclosed resources)
    * Premature optimization
  - Severity: MAJOR or MODERATE
  - Suggestions include optimized implementations
```

##### TC-CRS-004: Test Coverage Review Agent
```python
# Test: tests/unit/test_agents/code_reviews/test_all_code_review_specialists.py::test_test_coverage
Input: Code with insufficient test coverage
Expected Output:
  - Issues flagged:
    * Coverage < 80%
    * Missing edge case tests
    * Missing error path tests
    * No integration tests
  - Severity: MAJOR
  - Suggestions include specific test cases to add
```

##### TC-CRS-005: Documentation Review Agent
```python
# Test: tests/unit/test_agents/code_reviews/test_all_code_review_specialists.py::test_documentation
Input: Code with missing/poor documentation
Expected Output:
  - Issues flagged:
    * Missing docstrings
    * Incomplete API documentation
    * No usage examples
    * Outdated comments
  - Severity: MODERATE or MINOR
  - Suggestions include documentation templates
```

##### TC-CRS-006: Best Practices Review Agent
```python
# Test: tests/unit/test_agents/code_reviews/test_all_code_review_specialists.py::test_best_practices
Input: Code violating language-specific best practices
Expected Output:
  - Issues flagged (Python-specific):
    * Not using context managers (with statements)
    * Mutable default arguments
    * Bare except clauses
    * Not using list comprehensions where appropriate
  - Severity: MODERATE or MINOR
  - Suggestions include idiomatic rewrites
```

#### Execution Command
```bash
# Run all code review specialist tests
pytest tests/unit/test_agents/code_reviews/test_all_code_review_specialists.py -v

# Coverage report
pytest tests/unit/test_agents/code_reviews/ --cov=src/asp/agents/code_reviews --cov-report=html
```

#### Success Criteria
- ✅ Each specialist detects issues in their domain
- ✅ Security vulnerabilities are CRITICAL severity
- ✅ Suggestions are code-specific

---

## Integration Test Plan

### Full Workflow Integration Tests

#### Test Objectives
- ✅ End-to-end workflow from requirements to postmortem
- ✅ Agent-to-agent data flow
- ✅ Quality gates enforce process
- ✅ Artifacts persisted correctly

#### Test Cases

##### TC-INT-001: Happy Path Workflow
```python
# Test: tests/e2e/test_full_workflow.py::test_happy_path
Input: Simple task requirements
Process:
  1. Planning Agent → ProjectPlan
  2. Design Agent → DesignSpecification
  3. Design Review Agent → PASS
  4. Code Agent → GeneratedCode
  5. Code Review Agent → PASS
  6. Test Agent → PASS (all tests green)
  7. Postmortem Agent → PostmortemReport
Expected Output:
  - All agents succeed
  - All artifacts created
  - No quality gate failures
```

##### TC-INT-002: Design Review Failure Loop
```python
# Test: tests/e2e/test_full_workflow.py::test_design_review_failure
Input: Requirements leading to flawed design
Process:
  1. Planning Agent → ProjectPlan
  2. Design Agent → DesignSpecification (with security flaw)
  3. Design Review Agent → FAIL (security issue flagged)
  4. Design Agent (retry) → DesignSpecification (fixed)
  5. Design Review Agent → PASS
  6. Continue workflow...
Expected Output:
  - Design Review Agent blocks bad design
  - Loop-back to Design Agent occurs
  - Workflow continues after fix
```

##### TC-INT-003: Code Review Failure Loop
```python
# Test: tests/e2e/test_full_workflow.py::test_code_review_failure
Input: Design spec leading to code with issues
Process:
  1-3. Planning, Design, Design Review (all pass)
  4. Code Agent → GeneratedCode (with SQL injection)
  5. Code Review Agent → FAIL (security issue flagged)
  6. Code Agent (retry) → GeneratedCode (fixed)
  7. Code Review Agent → PASS
  8. Continue workflow...
Expected Output:
  - Code Review Agent blocks bad code
  - Loop-back to Code Agent occurs
  - Workflow continues after fix
```

##### TC-INT-004: Test Failure and Defect Logging
```python
# Test: tests/e2e/test_full_workflow.py::test_test_failure
Input: Code with runtime bug
Process:
  1-5. Planning, Design, Design Review, Code, Code Review (all pass)
  6. Test Agent → FAILED (tests fail, defects logged)
  7. Postmortem Agent → Analyzes defects
Expected Output:
  - Test failures logged with AI Defect Taxonomy
  - Postmortem identifies root cause
  - PIP generated for improvement
```

##### TC-INT-005: Artifact Chain Validation
```python
# Test: tests/e2e/test_full_workflow.py::test_artifact_chain
Expected Artifacts:
  - artifacts/plans/plan_{task_id}.json + .md
  - artifacts/designs/design_{task_id}.json + .md
  - artifacts/design_reviews/review_{task_id}.json + .md
  - artifacts/code/code_{task_id}/ (source files)
  - artifacts/code_reviews/review_{task_id}.json + .md
  - artifacts/tests/test_{task_id}.json + .md
  - artifacts/postmortems/postmortem_{task_id}.json + .md
Validation:
  - All artifacts reference correct task_id
  - Timestamps show proper sequencing
  - Data flows correctly between agents
```

#### Execution Command
```bash
# Run all integration tests
pytest tests/e2e/ -v

# Run with detailed logging
pytest tests/e2e/ -v -s --log-cli-level=INFO
```

#### Success Criteria
- ✅ Full workflow completes successfully
- ✅ Quality gates enforce process
- ✅ Artifacts created in correct order
- ✅ Defect logging and PIPs work

---

## Performance Test Plan

### Test Objectives
- ✅ Measure latency for each agent
- ✅ Measure cost for each agent
- ✅ Validate parallel execution performance gains
- ✅ Identify bottlenecks

### Test Cases

#### TC-PERF-001: Agent Latency Benchmarks
```python
# Test: tests/performance/test_agent_latency.py
Expected Latencies (approximate):
  - Planning Agent: 10-20 seconds
  - Design Agent: 15-30 seconds
  - Design Review Agent: 25-40 seconds (with parallelization)
  - Code Agent: 20-40 seconds
  - Code Review Agent: 30-50 seconds (with parallelization)
  - Test Agent: 30-60 seconds (includes test execution)
  - Postmortem Agent: 15-25 seconds
```

#### TC-PERF-002: Agent Cost Benchmarks
```python
# Test: tests/performance/test_agent_cost.py
Expected Costs (approximate):
  - Planning Agent: $0.05-$0.15
  - Design Agent: $0.10-$0.20
  - Design Review Agent: $0.15-$0.25
  - Code Agent: $0.15-$0.30
  - Code Review Agent: $0.20-$0.40
  - Test Agent: $0.20-$0.35
  - Postmortem Agent: $0.10-$0.20
Total Workflow Cost: $1.05-$2.05
```

#### TC-PERF-003: Parallel Execution Performance
```python
# Test: tests/performance/test_parallel_execution.py
Comparison:
  - Design Review (sequential): ~150 seconds
  - Design Review (parallel): ~25-40 seconds
  - Speedup: ~5x

  - Code Review (sequential): ~180 seconds
  - Code Review (parallel): ~30-50 seconds
  - Speedup: ~5x
```

#### TC-PERF-004: Telemetry Overhead
```python
# Test: tests/performance/test_telemetry_overhead.py
Expected Overhead:
  - Telemetry adds < 5% latency
  - Network calls to Langfuse async
  - No blocking on telemetry failures
```

#### Execution Command
```bash
# Run performance tests
pytest tests/performance/ -v

# Generate performance report
pytest tests/performance/ -v --benchmark-only --benchmark-autosave
```

#### Success Criteria
- ✅ Latencies within expected ranges
- ✅ Costs within expected ranges
- ✅ Parallel execution achieves ~5x speedup
- ✅ Telemetry overhead < 5%

---

## Test Execution Instructions

### Full Test Suite Execution

```bash
# 1. Install test dependencies
pip install -e ".[dev]"

# 2. Set up environment variables
export ANTHROPIC_API_KEY="your_key_here"
export OPENAI_API_KEY="your_key_here"
export LANGFUSE_PUBLIC_KEY="your_key_here"
export LANGFUSE_SECRET_KEY="your_key_here"

# 3. Run all tests
pytest tests/ -v

# 4. Run tests by category
pytest tests/unit/ -v                    # Unit tests only
pytest tests/e2e/ -v                     # E2E tests only
pytest tests/performance/ -v             # Performance tests only

# 5. Run tests for specific agent
pytest tests/unit/test_agents/test_planning_agent.py -v
pytest tests/unit/test_agents/test_design_agent.py -v
pytest tests/unit/test_agents/test_code_agent.py -v

# 6. Run tests with coverage
pytest tests/ --cov=src/asp --cov-report=html --cov-report=term

# 7. Generate test report
pytest tests/ -v --html=test_report.html --self-contained-html
```

### Incremental Testing (Recommended)

```bash
# Phase 1: Core agents (7 agents)
pytest tests/unit/test_agents/test_planning_agent.py -v
pytest tests/unit/test_agents/test_design_agent.py -v
pytest tests/unit/test_agents/test_design_review_agent.py -v
pytest tests/unit/test_agents/test_code_agent.py -v
pytest tests/unit/test_agents/test_code_review_orchestrator.py -v
pytest tests/unit/test_agents/test_test_agent.py -v
pytest tests/unit/test_agents/test_postmortem_agent.py -v

# Phase 2: Orchestrators (2 agents)
pytest tests/unit/test_agents/test_design_review_orchestrator.py -v
pytest tests/unit/test_agents/test_code_review_orchestrator.py -v

# Phase 3: Design review specialists (6 agents)
pytest tests/unit/test_agents/reviews/ -v

# Phase 4: Code review specialists (6 agents)
pytest tests/unit/test_agents/code_reviews/ -v

# Phase 5: Integration tests
pytest tests/e2e/ -v

# Phase 6: Performance tests
pytest tests/performance/ -v
```

### Continuous Integration

```yaml
# .github/workflows/test_all_agents.yml
name: Test All Agents

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: pip install -e ".[dev]"
      - name: Run all tests
        env:
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
          OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
          LANGFUSE_PUBLIC_KEY: ${{ secrets.LANGFUSE_PUBLIC_KEY }}
          LANGFUSE_SECRET_KEY: ${{ secrets.LANGFUSE_SECRET_KEY }}
        run: pytest tests/ -v --cov=src/asp --cov-report=xml
      - name: Upload coverage
        uses: codecov/codecov-action@v2
        with:
          file: ./coverage.xml
```

---

## Success Criteria

### Overall Test Plan Success Criteria

✅ **All 21 agents tested**
- 7 core agents: 100% test coverage
- 2 orchestrators: 100% test coverage
- 12 specialists: 100% test coverage

✅ **All test categories pass**
- Unit tests: > 95% pass rate
- Integration tests: 100% pass rate
- E2E tests: 100% pass rate
- Performance tests: Within expected ranges

✅ **Quality gates enforced**
- Design Review Agent blocks flawed designs
- Code Review Agent blocks flawed code
- Test Agent logs defects correctly

✅ **Telemetry validated**
- All agents tracked in Langfuse
- Cost and latency metrics collected
- No telemetry failures block execution

✅ **Artifacts validated**
- All agents generate required artifacts
- JSON artifacts match Pydantic schemas
- Markdown artifacts are human-readable

✅ **Performance acceptable**
- Latencies within expected ranges
- Costs within budget
- Parallel execution achieves speedup

✅ **Self-improvement demonstrated**
- Postmortem Agent generates PIPs
- PIPs are actionable
- HITL approval workflow functional

---

## Appendix A: Quick Reference

### Agent Testing Checklist

- [ ] Planning Agent (FR-1)
- [ ] Design Agent (FR-2)
- [ ] Design Review Agent (FR-3)
- [ ] Code Agent (FR-4)
- [ ] Code Review Agent (FR-5)
- [ ] Test Agent (FR-6)
- [ ] Postmortem Agent (FR-7)
- [ ] Design Review Orchestrator
- [ ] Code Review Orchestrator
- [ ] Security Review Agent (Design)
- [ ] Performance Review Agent (Design)
- [ ] Data Integrity Review Agent (Design)
- [ ] Maintainability Review Agent (Design)
- [ ] Architecture Review Agent (Design)
- [ ] API Design Review Agent (Design)
- [ ] Code Quality Review Agent
- [ ] Code Security Review Agent
- [ ] Code Performance Review Agent
- [ ] Test Coverage Review Agent
- [ ] Documentation Review Agent
- [ ] Best Practices Review Agent

### Test Execution Commands Cheat Sheet

```bash
# All tests
pytest tests/ -v

# Core agents only
pytest tests/unit/test_agents/test_*_agent.py -v

# Orchestrators only
pytest tests/unit/test_agents/test_*_orchestrator.py -v

# Design specialists only
pytest tests/unit/test_agents/reviews/ -v

# Code specialists only
pytest tests/unit/test_agents/code_reviews/ -v

# E2E tests only
pytest tests/e2e/ -v

# With coverage
pytest tests/ --cov=src/asp --cov-report=html
```

---

## Document Changelog

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2025-11-19 | Initial comprehensive test plan for all 21 agents |

---

**End of Test Plan**
