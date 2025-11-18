# Code Review Agent (FR-005) Implementation Plan

**Date:** November 17, 2025
**Session:** 2025-11-17 Session 2
**Status:** Planning

---

## Executive Summary

This document outlines the implementation plan for the Code Review Agent (FR-005), which reviews generated code for quality, security, performance, and standards compliance. The agent follows the proven multi-specialist architecture from Design Review Agent and supports phase-aware feedback for error correction.

**Key Objectives:**
1. Review generated code from Code Agent (FR-004)
2. Identify defects in code quality, security, performance, and standards
3. Support phase-aware feedback (route issues to Planning, Design, or Code phases)
4. Generate actionable improvement suggestions
5. Provide Pass/Fail quality gate decision

**Estimated Effort:** 8-12 hours
**Estimated Cost:** $0.50-1.00 in API costs
**Complexity:** High (multi-specialist orchestration + phase-aware routing)

---

## 1. Architecture Overview

### 1.1 Agent Type: Multi-Specialist Orchestrator

The Code Review Agent follows the same architecture as Design Review Agent:

```
Code Review Agent (Orchestrator)
│
├── Security Code Review Agent
│   └── Reviews: SQL injection, XSS, auth bypasses, secrets in code, etc.
│
├── Code Quality Review Agent
│   └── Reviews: Code structure, complexity, duplication, naming, error handling
│
├── Performance Review Agent
│   └── Reviews: Algorithmic complexity, N+1 queries, memory leaks, caching
│
├── Standards Compliance Review Agent
│   └── Reviews: Type hints, docstrings, PEP 8, test coverage, linting
│
├── Testing Review Agent
│   └── Reviews: Test completeness, test quality, edge cases, mocking
│
└── Maintainability Review Agent
    └── Reviews: Documentation, logging, configuration, dependency management
```

**Rationale:**
- Each specialist focuses on one domain (separation of concerns)
- Parallel execution for performance (all specialists run simultaneously)
- Proven pattern from Design Review Agent (6 specialists, orchestrator aggregates)
- Easy to add new specialists (e.g., Accessibility Review, Localization Review)

### 1.2 Input/Output

**Input:**
- `GeneratedCode` - Complete code from Code Agent (all files, dependencies, notes)
- `DesignSpecification` - Original design for traceability
- `CodingStandards` (optional) - Project-specific standards (PEP 8, style guide, etc.)
- `ReviewChecklist` (optional) - Additional checklist items to verify

**Output:**
- `CodeReviewReport` - Comprehensive review with:
  - Overall Pass/Fail status
  - List of `CodeIssue` objects (with phase attribution)
  - List of `ImprovementSuggestion` objects
  - Checklist results
  - Phase-grouped issues (Planning issues, Design issues, Code issues)

### 1.3 Phase-Aware Feedback

Following the phase-aware architecture from Session 1:

**Affected Phases:**
- `Planning` - Missing requirements, wrong decomposition, missing dependencies
- `Design` - API design errors, data model issues, architectural problems
- `Code` - Implementation bugs, security vulnerabilities, performance issues
- `Both` - Issues spanning multiple phases

**Example Issues:**
- **Planning Phase Issue:** "Missing authentication requirement in original task decomposition (SU-003 has no auth component)"
- **Design Phase Issue:** "API endpoint /users/{id} missing rate limiting specification in design"
- **Code Phase Issue:** "SQL injection vulnerability in user_repository.py line 45 (raw string interpolation)"

---

## 2. Data Models

### 2.1 CodeIssue Model

```python
class CodeIssue(BaseModel):
    """
    Represents a code quality issue identified during code review.
    """

    issue_id: str  # Format: CODE-ISSUE-001
    category: Literal[
        "Security",           # SQL injection, XSS, auth bypass, secrets
        "Code Quality",       # Complexity, duplication, naming, structure
        "Performance",        # N+1 queries, memory leaks, inefficient algorithms
        "Standards",          # Type hints, docstrings, PEP 8, linting
        "Testing",            # Missing tests, poor coverage, weak assertions
        "Maintainability",    # Documentation, logging, configuration
        "Error Handling",     # Missing try/catch, poor error messages
        "Data Integrity",     # Validation, transactions, race conditions
    ]
    severity: Literal["Critical", "High", "Medium", "Low"]

    description: str  # What is wrong
    evidence: str     # File path + line number + code snippet
    impact: str       # Why this matters

    # Phase-aware field (NEW)
    affected_phase: Literal["Planning", "Design", "Code", "Both"]

    # Code-specific fields
    file_path: str              # e.g., "src/api/auth.py"
    line_number: Optional[int]  # Line number where issue occurs
    code_snippet: Optional[str] # Actual code causing the issue

    # Traceability
    semantic_unit_id: Optional[str]  # Link to planning task
    component_id: Optional[str]      # Link to design component
```

**Key Additions:**
- `affected_phase` - Enables routing corrections to appropriate agent
- `file_path`, `line_number`, `code_snippet` - Code-specific evidence
- Traceability fields for PROBE-AI defect tracking

### 2.2 CodeImprovementSuggestion Model

```python
class CodeImprovementSuggestion(BaseModel):
    """
    Actionable recommendation to improve code quality.
    """

    suggestion_id: str  # Format: CODE-IMPROVE-001
    related_issue_id: Optional[str]  # CODE-ISSUE-001
    category: Literal[...]  # Same as CodeIssue
    priority: Literal["High", "Medium", "Low"]

    description: str              # What to do
    implementation_notes: str     # How to do it (code example, pattern, library)

    # Code-specific fields
    file_path: Optional[str]      # File to modify
    suggested_code: Optional[str] # Code example showing the fix
```

### 2.3 CodeReviewReport Model

```python
class CodeReviewReport(BaseModel):
    """
    Complete code review report from all specialists.
    """

    review_id: str  # Format: CODE-REVIEW-{task_id}-YYYYMMDD-HHMMSS
    task_id: str
    review_status: Literal["PASS", "FAIL", "CONDITIONAL_PASS"]

    # Review results
    issues_found: list[CodeIssue]
    improvement_suggestions: list[CodeImprovementSuggestion]
    checklist_review: list[ChecklistItemReview]

    # Phase-aware grouping (auto-generated via model_validator)
    planning_phase_issues: list[CodeIssue]
    design_phase_issues: list[CodeIssue]
    code_phase_issues: list[CodeIssue]

    # Summary statistics
    total_issues: int
    critical_issues: int
    high_issues: int
    files_reviewed: int
    total_lines_reviewed: int

    # Specialist results
    security_review_passed: bool
    quality_review_passed: bool
    performance_review_passed: bool
    standards_review_passed: bool
    testing_review_passed: bool
    maintainability_review_passed: bool

    # Agent metadata
    agent_version: str
    review_timestamp: str  # ISO 8601
    review_duration_seconds: Optional[float]
```

**Pass/Fail Logic:**
- `FAIL` - Any Critical issues OR ≥5 High issues OR any specialist returns FAIL
- `CONDITIONAL_PASS` - High issues present but <5, all Critical issues resolved
- `PASS` - No Critical/High issues, all specialists pass

---

## 3. Specialist Agents

### 3.1 Security Code Review Agent

**Focus:** Security vulnerabilities in implementation

**Key Checks:**
- SQL injection (raw queries, string interpolation)
- XSS vulnerabilities (unescaped output, innerHTML usage)
- Authentication bypasses (missing decorators, weak tokens)
- Authorization failures (missing permission checks, IDOR)
- Secrets in code (hardcoded passwords, API keys, tokens)
- Insecure dependencies (known CVEs, outdated packages)
- CSRF protection (missing tokens, unsafe methods)
- Crypto misuse (weak algorithms, hardcoded keys, bad RNG)

**Example Issue:**
```json
{
  "issue_id": "CODE-ISSUE-001",
  "category": "Security",
  "severity": "Critical",
  "description": "SQL injection vulnerability via raw string interpolation",
  "evidence": "src/repositories/user_repository.py:45",
  "impact": "Attacker can execute arbitrary SQL, extract database, modify data",
  "affected_phase": "Code",
  "file_path": "src/repositories/user_repository.py",
  "line_number": 45,
  "code_snippet": "query = f\"SELECT * FROM users WHERE username = '{username}'\""
}
```

### 3.2 Code Quality Review Agent

**Focus:** Code structure, readability, complexity

**Key Checks:**
- Cyclomatic complexity (>10 per function)
- Code duplication (copy-paste violations)
- Long functions (>50 lines)
- Poor naming (single letters, abbreviations, unclear intent)
- Deep nesting (>4 levels)
- God classes (>500 lines, >20 methods)
- Magic numbers (hardcoded constants)
- Dead code (unused imports, unreachable code)

**Example Issue:**
```json
{
  "issue_id": "CODE-ISSUE-005",
  "category": "Code Quality",
  "severity": "Medium",
  "description": "Function `process_user_data` has cyclomatic complexity of 15 (threshold: 10)",
  "evidence": "src/services/user_service.py:120-185",
  "impact": "High complexity increases bug risk, reduces testability, makes maintenance difficult",
  "affected_phase": "Code",
  "file_path": "src/services/user_service.py",
  "line_number": 120
}
```

### 3.3 Performance Review Agent

**Focus:** Runtime performance, resource usage

**Key Checks:**
- N+1 query problems (loops with DB calls)
- Missing indexes on queries
- Inefficient algorithms (O(n²) when O(n log n) possible)
- Memory leaks (circular references, unclosed resources)
- Missing caching (repeated expensive operations)
- Synchronous blocking calls (should be async)
- Large file operations in memory (should stream)
- Missing pagination (unbounded queries)

**Example Issue:**
```json
{
  "issue_id": "CODE-ISSUE-010",
  "category": "Performance",
  "severity": "High",
  "description": "N+1 query problem in user listing endpoint",
  "evidence": "src/api/users.py:55-60",
  "impact": "100 users → 101 DB queries (1 + 100). With 1000 users, will timeout/crash",
  "affected_phase": "Code",
  "file_path": "src/api/users.py",
  "line_number": 55,
  "code_snippet": "for user in users:\n    user.posts = db.query(Post).filter_by(user_id=user.id).all()"
}
```

### 3.4 Standards Compliance Review Agent

**Focus:** Coding standards adherence (PEP 8, type hints, docstrings)

**Key Checks:**
- Missing type hints (function parameters, return types)
- Missing docstrings (modules, classes, functions)
- PEP 8 violations (line length, naming conventions, imports)
- Missing __init__.py files
- Incorrect import ordering (stdlib, third-party, local)
- Unused imports
- Missing requirements.txt or dependency file
- Version pinning (dependencies without versions)

**Example Issue:**
```json
{
  "issue_id": "CODE-ISSUE-015",
  "category": "Standards",
  "severity": "Medium",
  "description": "Function missing type hints for parameters and return value",
  "evidence": "src/utils/helpers.py:12-18",
  "impact": "Reduces IDE support, increases bug risk, violates project standards",
  "affected_phase": "Code",
  "file_path": "src/utils/helpers.py",
  "line_number": 12,
  "code_snippet": "def calculate_total(items, tax_rate):\n    return sum(items) * (1 + tax_rate)"
}
```

### 3.5 Testing Review Agent

**Focus:** Test quality and completeness

**Key Checks:**
- Missing test files for source files
- Low test coverage (<80%)
- Missing edge case tests (empty input, null, boundary values)
- Weak assertions (assertTrue only, no specific checks)
- Missing negative tests (error handling not tested)
- Test interdependencies (tests that must run in order)
- Missing test documentation
- No integration tests for API endpoints

**Example Issue:**
```json
{
  "issue_id": "CODE-ISSUE-020",
  "category": "Testing",
  "severity": "High",
  "description": "Missing test file for src/api/auth.py (authentication endpoint)",
  "evidence": "No corresponding tests/test_auth.py or tests/api/test_auth.py found",
  "impact": "Authentication logic untested; security vulnerabilities may go undetected",
  "affected_phase": "Code",
  "file_path": "src/api/auth.py"
}
```

### 3.6 Maintainability Review Agent

**Focus:** Long-term maintenance, operations, documentation

**Key Checks:**
- Missing logging (errors, important events)
- Hardcoded configuration (should use env vars/config files)
- Missing error context (stack traces, request IDs)
- Unclear commit messages (if git history included)
- Missing README or setup instructions
- Complex dependencies (many transitive deps)
- No health check endpoints
- Missing observability (metrics, tracing)

**Example Issue:**
```json
{
  "issue_id": "CODE-ISSUE-025",
  "category": "Maintainability",
  "severity": "Medium",
  "description": "Missing structured logging for database connection failures",
  "evidence": "src/database/connection.py:30-35",
  "impact": "Database issues difficult to debug in production; no error tracking",
  "affected_phase": "Code",
  "file_path": "src/database/connection.py",
  "line_number": 30
}
```

---

## 4. Implementation Phases

### Phase 1: Data Models (60 minutes)

**Tasks:**
1. Create `src/asp/models/code_review.py`
2. Implement `CodeIssue` model with phase-aware fields
3. Implement `CodeImprovementSuggestion` model
4. Implement `CodeReviewReport` model with phase grouping
5. Add phase-aware model validator (auto-group issues)
6. Export models from `src/asp/models/__init__.py`
7. Create unit tests for models (validation, phase grouping)

**Success Criteria:**
- All models have complete type hints and docstrings
- Validators prevent invalid data (issue IDs, severity levels)
- Phase grouping works automatically
- 15+ unit tests passing

### Phase 2: Specialist Prompts (90 minutes)

**Tasks:**
1. Create `src/asp/prompts/security_code_review_agent_v1.txt`
2. Create `src/asp/prompts/code_quality_review_agent_v1.txt`
3. Create `src/asp/prompts/performance_code_review_agent_v1.txt`
4. Create `src/asp/prompts/standards_compliance_review_agent_v1.txt`
5. Create `src/asp/prompts/testing_review_agent_v1.txt`
6. Create `src/asp/prompts/maintainability_code_review_agent_v1.txt`

**Prompt Structure (per specialist):**
```
# Security Code Review Agent v1.0

You are a specialist security code reviewer for the ASP platform. Your role is to identify security vulnerabilities in generated code.

## Input
You will receive:
1. GeneratedCode JSON (all files, dependencies, implementation notes)
2. DesignSpecification JSON (original design for context)
3. Optional coding standards

## Your Task
Review ALL generated files for security vulnerabilities. For each issue:
- Identify the specific file, line number, and code snippet
- Classify severity (Critical/High/Medium/Low)
- Determine affected phase (Planning/Design/Code/Both)
- Provide actionable fix suggestions

## Security Categories to Check
1. SQL Injection
2. XSS (Cross-Site Scripting)
3. Authentication/Authorization
4. Secrets Management
... (full checklist)

## Output Format
Return JSON with this structure:
{
  "issues_found": [
    {
      "issue_id": "CODE-ISSUE-001",
      "category": "Security",
      "severity": "Critical",
      "description": "...",
      "evidence": "...",
      "impact": "...",
      "affected_phase": "Code",
      "file_path": "...",
      "line_number": 45,
      "code_snippet": "..."
    }
  ],
  "improvement_suggestions": [...]
}

## Example
... (full example showing real vulnerability detection)
```

**Success Criteria:**
- Each prompt has clear role definition
- Complete checklist of items to review
- Examples of real issues + fixes
- Phase attribution guidelines
- JSON output schema

### Phase 3: Specialist Agents (90 minutes)

**Tasks:**
1. Create `src/asp/agents/code_reviews/` directory
2. Implement `SecurityCodeReviewAgent`
3. Implement `CodeQualityReviewAgent`
4. Implement `PerformanceCodeReviewAgent`
5. Implement `StandardsComplianceReviewAgent`
6. Implement `TestingReviewAgent`
7. Implement `MaintainabilityCodeReviewAgent`
8. Each agent follows BaseAgent pattern + telemetry decorator

**Agent Template:**
```python
class SecurityCodeReviewAgent(BaseAgent):
    """Specialist agent for security code review."""

    def __init__(self, llm_client=None, db_path=None):
        super().__init__(llm_client=llm_client, db_path=db_path)
        self.agent_version = "1.0.0"

    @track_agent_cost(
        agent_role="SecurityCodeReview",
        agent_version="1.0.0",
        task_id_param="generated_code.task_id",
    )
    def execute(
        self,
        generated_code: GeneratedCode,
        design_spec: DesignSpecification,
        coding_standards: Optional[str] = None,
    ) -> dict[str, Any]:
        """Execute security code review."""
        # Load prompt
        # Call LLM
        # Parse response
        # Return {issues_found: [], improvement_suggestions: []}
```

**Success Criteria:**
- All 6 specialists implemented
- Each has telemetry tracking
- Each returns consistent JSON structure
- Error handling for invalid LLM responses

### Phase 4: Orchestrator Agent (120 minutes)

**Tasks:**
1. Create `src/asp/agents/code_review_agent.py`
2. Implement orchestrator that:
   - Runs all 6 specialists in parallel (or sequentially for debugging)
   - Aggregates results into CodeReviewReport
   - Computes Pass/Fail status
   - Groups issues by phase
   - Calculates statistics
3. Add automated validation checks (optional):
   - File count validation
   - Dependency version check
   - Basic syntax validation
4. Add telemetry tracking

**Orchestrator Logic:**
```python
class CodeReviewAgent(BaseAgent):
    """Orchestrator for code review specialists."""

    @track_agent_cost(...)
    def execute(
        self,
        generated_code: GeneratedCode,
        design_spec: DesignSpecification,
        coding_standards: Optional[str] = None,
    ) -> CodeReviewReport:
        """Execute multi-specialist code review."""

        # Step 1: Run all specialists
        security_results = SecurityCodeReviewAgent().execute(...)
        quality_results = CodeQualityReviewAgent().execute(...)
        performance_results = PerformanceCodeReviewAgent().execute(...)
        standards_results = StandardsComplianceReviewAgent().execute(...)
        testing_results = TestingReviewAgent().execute(...)
        maintainability_results = MaintainabilityCodeReviewAgent().execute(...)

        # Step 2: Aggregate all issues
        all_issues = (
            security_results["issues_found"] +
            quality_results["issues_found"] +
            ...
        )

        # Step 3: Convert to CodeIssue models
        issues_list = [CodeIssue(**issue) for issue in all_issues]

        # Step 4: Determine Pass/Fail status
        critical_count = sum(1 for i in issues_list if i.severity == "Critical")
        high_count = sum(1 for i in issues_list if i.severity == "High")

        if critical_count > 0 or high_count >= 5:
            status = "FAIL"
        elif high_count > 0:
            status = "CONDITIONAL_PASS"
        else:
            status = "PASS"

        # Step 5: Build CodeReviewReport
        return CodeReviewReport(
            review_id=self._generate_review_id(...),
            task_id=generated_code.task_id,
            review_status=status,
            issues_found=issues_list,
            ...
        )
```

**Success Criteria:**
- All specialists invoked correctly
- Results aggregated without data loss
- Pass/Fail logic works
- Phase grouping automatic (via model_validator)
- Report includes all required fields

### Phase 5: Unit Tests (90 minutes)

**Tasks:**
1. Create `tests/unit/test_models/test_code_review_models.py`
   - Test CodeIssue validation
   - Test phase grouping
   - Test severity calculations
2. Create `tests/unit/test_agents/test_code_review_specialists.py`
   - Test each specialist agent (mocked LLM)
   - Test prompt loading
   - Test error handling
3. Create `tests/unit/test_agents/test_code_review_agent.py`
   - Test orchestrator aggregation
   - Test Pass/Fail logic
   - Test statistics calculation

**Target:** 30+ unit tests, >95% coverage

### Phase 6: E2E Tests (60 minutes)

**Tasks:**
1. Create `tests/e2e/test_code_review_agent_e2e.py`
2. Test scenarios:
   - **Scenario 1:** Review secure, high-quality code (expect PASS)
   - **Scenario 2:** Review code with SQL injection (expect FAIL + Critical issue)
   - **Scenario 3:** Review code with multiple issues (expect phase-aware routing)
3. Validate real API costs (~$0.10-0.30 per E2E test)

**Success Criteria:**
- All E2E tests pass with real API
- Phase-aware issues correctly identified
- Pass/Fail status accurate
- Cost tracking in telemetry

### Phase 7: Documentation (45 minutes)

**Tasks:**
1. Create `docs/code_review_agent_user_guide.md`
   - Agent overview
   - Specialist descriptions
   - Usage examples
   - API reference
   - Interpreting results
2. Update `README.md` with Code Review Agent status
3. Optional: Create ADR for multi-specialist code review architecture

---

## 5. Testing Strategy

### 5.1 Unit Tests

**Coverage Targets:**
- Models: 100% coverage
- Each specialist agent: >90% coverage
- Orchestrator: >95% coverage

**Key Test Cases:**
- CodeIssue validation (valid/invalid issue IDs, severities)
- Phase grouping (Planning/Design/Code/Both)
- Pass/Fail logic (edge cases: 0 issues, 5 high issues, critical issues)
- Specialist response parsing (valid JSON, invalid JSON, missing fields)
- Error handling (LLM timeout, invalid input, missing files)

### 5.2 E2E Tests

**Test Scenarios:**

**Scenario 1: High-Quality Code (PASS)**
- Input: Well-written FastAPI app with tests, type hints, security
- Expected: PASS status, 0-2 Low severity suggestions
- Cost: ~$0.10

**Scenario 2: Security Vulnerability (FAIL)**
- Input: Code with SQL injection + XSS
- Expected: FAIL status, 2 Critical issues, phase=Code
- Cost: ~$0.15

**Scenario 3: Multi-Phase Issues (phase routing)**
- Input: Code with missing auth (Planning issue) + N+1 query (Code issue)
- Expected: CONDITIONAL_PASS or FAIL, issues grouped by phase
- Cost: ~$0.20

### 5.3 Manual Testing

**Checklist:**
1. Run Code Agent → Code Review Agent pipeline
2. Verify telemetry in Langfuse dashboard
3. Check SQLite database for cost tracking
4. Validate JSON output schema
5. Test with different code quality levels

---

## 6. Phase-Aware Feedback Integration

### 6.1 Affected Phase Attribution

**Guidelines for specialists:**

**Planning Phase Issues:**
- Missing requirements that caused code gaps
- Wrong task decomposition leading to architectural issues
- Missing dependencies causing integration problems

**Design Phase Issues:**
- API endpoint design errors (wrong HTTP methods, missing validation)
- Data model issues (missing fields, wrong types, no indexes)
- Architectural problems (missing layers, wrong patterns)

**Code Phase Issues:**
- Implementation bugs (logic errors, off-by-one)
- Security vulnerabilities (SQL injection, XSS)
- Performance problems (N+1 queries, missing caching)
- Standards violations (missing type hints, docstrings)

**Both:**
- Issues spanning multiple phases (e.g., missing auth requirement in Planning + missing auth in Code)

### 6.2 Orchestrator Routing (Future Work)

When Code Review Agent returns FAIL:

1. Orchestrator examines `affected_phase` field on each issue
2. Routes issues to appropriate agent for correction:
   - `Planning` issues → Planning Agent (with feedback)
   - `Design` issues → Design Agent (with feedback)
   - `Code` issues → Code Agent (with feedback)
3. Tracks iteration count (max 3 per phase, max 10 total)
4. Escalates to human if max iterations exceeded

---

## 7. Success Criteria

### 7.1 Functional Requirements

-  Code Review Agent accepts GeneratedCode + DesignSpecification
-  All 6 specialist agents implemented and functional
-  Orchestrator aggregates results correctly
-  Pass/Fail logic works (Critical issues → FAIL, High issues ≥5 → FAIL)
-  Phase-aware issues correctly attributed
-  JSON output matches CodeReviewReport schema

### 7.2 Quality Requirements

-  30+ unit tests, >95% coverage
-  3+ E2E tests with real API
-  All tests passing
-  Telemetry tracking functional
-  Cost per review <$0.30

### 7.3 Documentation Requirements

-  User guide with examples
-  README updated
-  Code has comprehensive docstrings
-  Models have examples in Config

---

## 8. Timeline & Estimates

| Phase | Description | Estimated Time | Dependencies |
|-------|-------------|----------------|--------------|
| 1 | Data Models | 60 min | None |
| 2 | Specialist Prompts | 90 min | Phase 1 |
| 3 | Specialist Agents | 90 min | Phase 1, 2 |
| 4 | Orchestrator Agent | 120 min | Phase 1, 2, 3 |
| 5 | Unit Tests | 90 min | Phase 1, 3, 4 |
| 6 | E2E Tests | 60 min | Phase 1-5 |
| 7 | Documentation | 45 min | Phase 1-6 |
| **Total** | | **9.25 hours** | |

**Estimated API Costs:**
- Unit tests: $0.00 (mocked)
- E2E tests (3 scenarios): ~$0.45
- Manual testing: ~$0.10
- **Total:** ~$0.55

---

## 9. Risks & Mitigations

### Risk 1: LLM Hallucinations (False Positives)

**Risk:** Specialists may report non-existent vulnerabilities

**Mitigation:**
- Require evidence (file path + line number + code snippet)
- Add automated validation checks (does file exist? does line number exist?)
- Use high-quality prompts with examples
- Human review of FAIL reports before blocking

### Risk 2: Performance (6 LLM Calls per Review)

**Risk:** Running 6 specialists sequentially could take 60+ seconds

**Mitigation:**
- Implement parallel execution (asyncio or threading)
- Use caching for repeated code patterns
- Consider using Haiku for some specialists (quality vs. performance)

### Risk 3: Phase Attribution Errors

**Risk:** Specialists may incorrectly attribute issues to wrong phase

**Mitigation:**
- Provide clear guidelines in prompts with examples
- Add validation logic (e.g., "missing type hint" is always Code phase)
- Review and iterate on prompts based on test results

### Risk 4: Cost Overruns

**Risk:** 6 specialists × large code files = high token costs

**Mitigation:**
- Set max token limits per specialist
- Implement file batching (review 5 files at a time)
- Track costs in telemetry, alert if >$1.00 per review

---

## 10. Future Enhancements

### 10.1 Additional Specialists

- **Accessibility Review Agent** - WCAG compliance, screen reader support
- **Localization Review Agent** - i18n support, hardcoded strings
- **Dependency Security Agent** - CVE scanning, license compliance
- **Container Review Agent** - Dockerfile best practices, image size

### 10.2 Automated Fixes

- Generate pull requests with suggested fixes
- Auto-fix simple issues (add type hints, format with black, fix imports)
- Provide code diffs instead of just suggestions

### 10.3 Custom Checklists

- Allow users to define project-specific review criteria
- Support industry-specific standards (HIPAA, PCI-DSS, SOC2)
- Integrate with existing linters (pylint, mypy, bandit)

### 10.4 Learning from Feedback

- Track which issues are accepted vs. rejected by humans
- Use feedback to improve specialist prompts
- Build historical knowledge base of common issues

---

## 11. Next Steps

**Immediate Actions:**
1. Review and approve this implementation plan
2. Begin Phase 1: Data Models implementation
3. Create git branch for Code Review Agent work (optional)
4. Set up telemetry tracking for new agents

**After Implementation:**
1. Collect bootstrap data (run Code Review on 5-10 tasks)
2. Analyze telemetry data (cost, performance, accuracy)
3. Iterate on prompts based on results
4. Begin Test Agent (FR-006) implementation

---

**Status:**  Planning Complete - Ready for Implementation

**Next:** Phase 1 - Data Models Implementation
