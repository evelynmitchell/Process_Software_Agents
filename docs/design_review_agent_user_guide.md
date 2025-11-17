# Design Review Agent - User Guide

**Version:** 1.0.0
**Last Updated:** November 16, 2025
**Status:** Production Ready

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Quick Start](#quick-start)
4. [Specialist Agents](#specialist-agents)
5. [Usage Examples](#usage-examples)
6. [Understanding Results](#understanding-results)
7. [Performance & Cost](#performance--cost)
8. [Testing](#testing)
9. [Troubleshooting](#troubleshooting)
10. [API Reference](#api-reference)

---

## Overview

The Design Review Agent is a multi-agent system that performs comprehensive quality reviews of software design specifications. It evaluates designs across six specialized dimensions: Security, Performance, Data Integrity, Maintainability, Architecture, and API Design.

### Key Features

- **6 Specialist Agents:** Each focused on a specific quality dimension
- **Parallel Execution:** All specialists run concurrently via asyncio (~25-40s total)
- **Comprehensive Coverage:** Identifies Critical, High, Medium, and Low severity issues
- **Actionable Output:** Provides specific improvement suggestions with implementation notes
- **Checklist Validation:** Reviews against design-specific quality criteria
- **Full Telemetry:** Integrates with Langfuse and SQLite for observability

### When to Use

Use the Design Review Agent when you have a `DesignSpecification` output from the Design Agent and want to:
- Validate design quality before implementation
- Identify security vulnerabilities early
- Optimize performance bottlenecks
- Ensure data integrity and consistency
- Improve code maintainability
- Validate API design against best practices

---

## Architecture

### Multi-Agent System

```
┌─────────────────────────────────────────────────────────────┐
│                  DesignReviewOrchestrator                   │
│                                                             │
│  Coordinates 6 specialists in parallel, aggregates results │
└─────────────────────────────────────────────────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        │                   │                   │
        ▼                   ▼                   ▼
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│  Security    │    │ Performance  │    │ Data         │
│  Review      │    │ Review       │    │ Integrity    │
│  Agent       │    │ Agent        │    │ Review Agent │
└──────────────┘    └──────────────┘    └──────────────┘
        │                   │                   │
        ▼                   ▼                   ▼
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│Maintainability│   │ Architecture │    │ API Design   │
│ Review       │    │ Review       │    │ Review       │
│ Agent        │    │ Agent        │    │ Agent        │
└──────────────┘    └──────────────┘    └──────────────┘
        │                   │                   │
        └───────────────────┴───────────────────┘
                            │
                            ▼
                ┌─────────────────────┐
                │ DesignReviewReport  │
                │                     │
                │ • Issues Found      │
                │ • Suggestions       │
                │ • Checklist Review  │
                │ • Overall Assessment│
                └─────────────────────┘
```

### Design Decisions

- **Why Multi-Agent?** Specialized expertise > monolithic review
- **Why Parallel?** 6x faster than sequential (40s vs 240s)
- **Why Orchestrator?** Centralized aggregation, deduplication, conflict resolution
- **Why Telemetry?** PROBE-AI learning requires detailed metrics

For detailed architecture rationale, see: `docs/design_review_agent_architecture_decision.md`

---

## Quick Start

### Basic Usage

```python
from asp.agents.design_review_orchestrator import DesignReviewOrchestrator
from asp.models.design import DesignSpecification

# 1. Create orchestrator
orchestrator = DesignReviewOrchestrator()

# 2. Load or create a DesignSpecification
design_spec = DesignSpecification(...)  # From Design Agent output

# 3. Execute review
report = orchestrator.execute(design_spec)

# 4. Check results
print(f"Overall Assessment: {report.overall_assessment}")
print(f"Issues: {len(report.issues_found)} total")
print(f"  Critical: {report.critical_issue_count}")
print(f"  High: {report.high_issue_count}")
print(f"  Medium: {report.medium_issue_count}")
print(f"  Low: {report.low_issue_count}")
print(f"Suggestions: {len(report.improvement_suggestions)}")
```

### Minimal Example

```python
from asp.agents.design_review_orchestrator import DesignReviewOrchestrator

# Review from file
import json
with open("design_output.json") as f:
    design_data = json.load(f)

from asp.models.design import DesignSpecification
design_spec = DesignSpecification(**design_data)

orchestrator = DesignReviewOrchestrator()
report = orchestrator.execute(design_spec)

# Save results
with open("review_report.json", "w") as f:
    json.dump(report.model_dump(), f, indent=2, default=str)
```

---

## Specialist Agents

### SecurityReviewAgent

**Focus Areas:**
- Authentication & authorization mechanisms
- Input validation & sanitization
- Injection prevention (SQL, XSS, CSRF, Command)
- Sensitive data handling (encryption, hashing)
- API rate limiting & abuse prevention
- Session management security
- OWASP Top 10 vulnerabilities

**Example Issues Detected:**
- Passwords stored in plaintext
- Missing HTTPS/TLS requirements
- SQL injection vulnerabilities
- Weak JWT signing algorithms
- Missing rate limiting on authentication endpoints

**Severity Guidelines:**
- **Critical:** Plaintext passwords, SQL injection, missing encryption
- **High:** Weak hashing, missing rate limiting, session fixation
- **Medium:** Missing input validation, weak session timeouts
- **Low:** Missing security headers, insufficient logging

### PerformanceReviewAgent

**Focus Areas:**
- Database indexing strategy
- Caching mechanisms
- N+1 query problems
- Unbounded query risks
- Scalability bottlenecks
- Resource utilization

**Example Issues Detected:**
- Missing foreign key indexes
- No caching layer for frequently accessed data
- Full table scans on large tables
- N+1 queries in component logic
- Missing pagination on list endpoints

**Severity Guidelines:**
- **Critical:** Missing FK indexes on high-volume tables, N+1 queries
- **High:** No caching, full table loads, missing pagination
- **Medium:** Suboptimal index coverage, missing query hints
- **Low:** Minor optimization opportunities

### DataIntegrityReviewAgent

**Focus Areas:**
- Foreign key constraints
- Referential integrity
- Transaction boundaries
- Data validation rules
- Constraint enforcement
- Cascade behavior (ON DELETE, ON UPDATE)

**Example Issues Detected:**
- Missing foreign key constraints
- No referential integrity enforcement
- Missing NOT NULL constraints
- Incorrect cascade behavior
- Missing CHECK constraints
- Orphaned record risks

**Severity Guidelines:**
- **Critical:** Missing critical FK constraints, no transaction boundaries
- **High:** Missing data validation, incorrect cascade rules
- **Medium:** Missing CHECK constraints, weak validation
- **Low:** Optional constraint improvements

### MaintainabilityReviewAgent

**Focus Areas:**
- Component coupling & cohesion
- Separation of concerns
- Code organization
- Naming conventions
- Interface clarity
- Technical debt indicators

**Example Issues Detected:**
- High coupling between components
- Mixed responsibilities in single component
- Business logic in wrong layer
- Unclear component boundaries
- Missing abstraction layers

**Severity Guidelines:**
- **High:** Tight coupling, mixed concerns, business logic in wrong layer
- **Medium:** Moderate coupling, unclear responsibilities
- **Low:** Minor organizational improvements, naming issues

### ArchitectureReviewAgent

**Focus Areas:**
- Design patterns application
- Layering & separation
- Dependency direction
- Testability design
- Extension points
- SOLID principles

**Example Issues Detected:**
- Missing adapter patterns
- No dependency injection
- Business logic in API layer
- Untestable components
- Missing error boundaries
- Circular dependencies

**Severity Guidelines:**
- **High:** Missing critical patterns, circular dependencies, untestable design
- **Medium:** Suboptimal patterns, moderate architectural debt
- **Low:** Pattern improvement opportunities

### APIDesignReviewAgent

**Focus Areas:**
- RESTful principles
- HTTP method usage
- Status code correctness
- Error response design
- API versioning strategy
- Request/response consistency

**Example Issues Detected:**
- Non-RESTful endpoint design
- Incorrect HTTP methods
- Inconsistent error formats
- Missing API versioning
- Poor error response structure
- Missing pagination support

**Severity Guidelines:**
- **High:** Major REST violations, missing error handling
- **Medium:** Inconsistent patterns, missing versioning
- **Low:** Minor improvements, documentation gaps

---

## Usage Examples

### Example 1: Basic Review

```python
from asp.agents.design_review_orchestrator import DesignReviewOrchestrator
from asp.models.design import DesignSpecification

# Load design
design_spec = DesignSpecification.model_validate_json(
    open("my_design.json").read()
)

# Execute review
orchestrator = DesignReviewOrchestrator()
report = orchestrator.execute(design_spec)

# Print summary
print(f"\n{'='*60}")
print(f"Design Review Report: {report.task_id}")
print(f"{'='*60}")
print(f"Overall Assessment: {report.overall_assessment}")
print(f"\nIssues by Severity:")
print(f"  🔴 Critical: {report.critical_issue_count}")
print(f"  🟠 High:     {report.high_issue_count}")
print(f"  🟡 Medium:   {report.medium_issue_count}")
print(f"  🟢 Low:      {report.low_issue_count}")
print(f"\nSuggestions: {len(report.improvement_suggestions)}")
print(f"Review Duration: {report.review_duration_ms/1000:.1f}s")
```

### Example 2: Filter Critical Issues

```python
# Get all critical issues
critical_issues = [
    issue for issue in report.issues_found
    if issue.severity == "Critical"
]

print(f"\n🔴 Critical Issues ({len(critical_issues)}):")
for issue in critical_issues:
    print(f"\n{issue.issue_id}: {issue.description}")
    print(f"  Category: {issue.category}")
    print(f"  Evidence: {issue.evidence}")
    print(f"  Impact: {issue.impact}")
```

### Example 3: Review by Category

```python
from collections import defaultdict

# Group issues by category
issues_by_category = defaultdict(list)
for issue in report.issues_found:
    issues_by_category[issue.category].append(issue)

# Print by category
for category, issues in sorted(issues_by_category.items()):
    print(f"\n{category} ({len(issues)} issues):")
    for issue in issues:
        print(f"  [{issue.severity}] {issue.description[:80]}...")
```

### Example 4: Export to JSON

```python
import json
from datetime import datetime

# Create export
export_data = {
    "task_id": report.task_id,
    "review_id": report.review_id,
    "timestamp": report.timestamp.isoformat(),
    "overall_assessment": report.overall_assessment,
    "summary": {
        "total_issues": len(report.issues_found),
        "critical": report.critical_issue_count,
        "high": report.high_issue_count,
        "medium": report.medium_issue_count,
        "low": report.low_issue_count,
        "suggestions": len(report.improvement_suggestions),
    },
    "issues": [issue.model_dump() for issue in report.issues_found],
    "suggestions": [s.model_dump() for s in report.improvement_suggestions],
    "checklist": [c.model_dump() for c in report.checklist_review],
}

# Save to file
filename = f"review_{report.task_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
with open(filename, "w") as f:
    json.dump(export_data, f, indent=2, default=str)
```

### Example 5: Full Pipeline (Planning → Design → Review)

```python
from asp.agents.planning_agent import PlanningAgent
from asp.agents.design_agent import DesignAgent
from asp.agents.design_review_orchestrator import DesignReviewOrchestrator
from asp.models.planning import TaskRequirements
from asp.models.design import DesignInput

# Step 1: Planning
planning_agent = PlanningAgent()
requirements = TaskRequirements(
    task_id="FULL-PIPELINE-001",
    description="Build a JWT authentication system",
)
project_plan = planning_agent.execute(requirements)

# Step 2: Design
design_agent = DesignAgent()
design_input = DesignInput(
    task_id="FULL-PIPELINE-001",
    requirements="Implement JWT-based authentication with login/refresh endpoints",
    project_plan=project_plan,
    design_constraints="Use FastAPI, PostgreSQL, bcrypt, RS256 JWT",
)
design_spec = design_agent.execute(design_input)

# Step 3: Review
review_orchestrator = DesignReviewOrchestrator()
review_report = review_orchestrator.execute(design_spec)

# Results
print(f"Planning: {len(project_plan.semantic_units)} semantic units")
print(f"Design: {len(design_spec.component_logic)} components")
print(f"Review: {review_report.overall_assessment}")
print(f"  Issues: {len(review_report.issues_found)}")
print(f"  Suggestions: {len(review_report.improvement_suggestions)}")
```

---

## Understanding Results

### DesignReviewReport Structure

```python
{
    "task_id": "TASK-001",
    "review_id": "REVIEW-TASK001-20251116-143022",
    "timestamp": "2025-11-16T14:30:22",
    "overall_assessment": "FAIL",  # PASS | FAIL | NEEDS_IMPROVEMENT

    "automated_checks": {
        "semantic_coverage": True,
        "no_circular_deps": True,
        "schema_api_consistency": True,
        "checklist_completeness": True
    },

    "issues_found": [/* DesignIssue objects */],
    "improvement_suggestions": [/* ImprovementSuggestion objects */],
    "checklist_review": [/* ChecklistItemReview objects */],

    "critical_issue_count": 2,
    "high_issue_count": 5,
    "medium_issue_count": 8,
    "low_issue_count": 3,

    "reviewer_agent": "DesignReviewOrchestrator",
    "agent_version": "1.0.0",
    "review_duration_ms": 38500.0
}
```

### Overall Assessment Logic

- **PASS:** No Critical or High severity issues
- **FAIL:** At least one Critical or High severity issue
- **NEEDS_IMPROVEMENT:** Only Medium or Low severity issues

### Issue Severity Meanings

| Severity | Description | Examples |
|----------|-------------|----------|
| **Critical** | Security vulnerabilities, data loss risks, system crashes | Plaintext passwords, SQL injection, missing FK constraints |
| **High** | Performance bottlenecks, incorrect behavior, major tech debt | Missing indexes, N+1 queries, weak hashing |
| **Medium** | Suboptimal patterns, minor inconsistencies, code smell | Missing caching, moderate coupling, suboptimal APIs |
| **Low** | Style issues, documentation gaps, minor improvements | Missing security headers, naming conventions |

---

## Performance & Cost

### Execution Time

- **Typical Review:** 25-40 seconds
- **Simple Design:** ~25 seconds (minimal components)
- **Complex Design:** ~40 seconds (many components, APIs, schemas)
- **Parallel Speedup:** 6x faster than sequential (~40s vs ~240s)

### API Costs

Based on Claude Sonnet 4 pricing:

- **Input Tokens:** ~800-1,500 per specialist (design spec size)
- **Output Tokens:** ~500-1,000 per specialist (issues + suggestions)
- **Total per Review:** ~9,000-15,000 tokens across 6 specialists
- **Estimated Cost:** $0.15-0.25 per review

**Cost Optimization Tips:**
- Use simpler designs for testing
- Mock specialists for unit tests (zero cost)
- Batch multiple reviews together
- Monitor telemetry for token usage patterns

### Resource Usage

- **Memory:** ~200-300 MB per orchestrator instance
- **CPU:** Minimal (I/O bound, mostly waiting for LLM)
- **Network:** 6 concurrent API calls to Anthropic
- **Database:** ~5-10 KB per review (telemetry)

---

## Testing

### Unit Tests

Run unit tests (no API calls, fully mocked):

```bash
# All unit tests
uv run pytest tests/unit/test_agents/test_design_review_agent.py -v

# Specific specialist
uv run pytest tests/unit/test_agents/test_design_review_agent.py::TestSecurityReviewAgent -v

# With coverage
uv run pytest tests/unit/test_agents/test_design_review_agent.py --cov=asp.agents.reviews --cov-report=html
```

**Coverage:** 21/21 tests passing (100%)

### E2E Tests

Run E2E tests (real API calls, ~$0.30-0.40 total):

```bash
# All E2E tests
uv run pytest tests/e2e/test_design_review_agent_e2e.py -v -m e2e

# Single test
uv run pytest tests/e2e/test_design_review_agent_e2e.py::TestDesignReviewAgentE2E::test_minimal_design_review -v

# Skip E2E (when no API key)
uv run pytest tests/e2e/test_design_review_agent_e2e.py -v -m "not e2e"
```

**Coverage:** 3/3 tests passing (100%)

### Test Fixtures

Example test fixture from `test_design_review_agent.py`:

```python
def create_test_design_specification(task_id="TEST-REVIEW-001"):
    """Create a test DesignSpecification for review."""
    return DesignSpecification(
        task_id=task_id,
        api_contracts=[...],
        data_schemas=[...],
        component_logic=[...],
        design_review_checklist=[...],  # At least 5 items required
        architecture_overview="...",     # At least 50 characters
        technology_stack={...},          # Required dictionary
        total_complexity=60,
        agent_version="1.0.0",
        timestamp=datetime.now(),
    )
```

---

## Troubleshooting

### Common Issues

#### 1. ValidationError: design_review_checklist too short

**Error:**
```
List should have at least 5 items after validation, not 2
```

**Solution:**
```python
# Ensure at least 5 checklist items
design_review_checklist=[
    DesignReviewChecklistItem(...),  # Item 1
    DesignReviewChecklistItem(...),  # Item 2
    DesignReviewChecklistItem(...),  # Item 3
    DesignReviewChecklistItem(...),  # Item 4
    DesignReviewChecklistItem(...),  # Item 5
]
```

#### 2. ValidationError: architecture_overview required

**Error:**
```
Field required [type=missing]
```

**Solution:**
```python
architecture_overview="This system uses a 3-tier architecture..."  # Min 50 chars
```

#### 3. Telemetry Database Warning

**Warning:**
```
Warning: Failed to log telemetry to database: table agent_cost_vector has no column named subtask_id
```

**Impact:** Non-blocking. Telemetry logs to Langfuse Cloud but not local SQLite.

**Solution:** Database schema migration needed (future work).

#### 4. Specialist Execution Failure

**Symptom:** Review completes but one specialist has no results

**Cause:** Specialist exception caught and handled gracefully

**Check logs:**
```python
import logging
logging.basicConfig(level=logging.DEBUG)
# Will show: "WARNING: security specialist failed: <error>"
```

**Solution:** Check Langfuse dashboard for specialist execution errors.

#### 5. Slow Review Performance (>60s)

**Possible Causes:**
- Network latency to Anthropic API
- Very large design specification (>10 components, >10 API endpoints)
- API rate limiting

**Check:**
```python
print(f"Review duration: {report.review_duration_ms/1000:.1f}s")
# Expected: 25-40s for typical designs
```

---

## API Reference

### DesignReviewOrchestrator

```python
class DesignReviewOrchestrator(BaseAgent):
    """Orchestrates parallel design review by 6 specialist agents."""

    def __init__(
        self,
        llm_client: Optional[Any] = None,
        db_path: Optional[str] = None,
    ):
        """
        Initialize Design Review Orchestrator.

        Args:
            llm_client: Optional LLM client (for testing/mocking)
            db_path: Optional database path (for testing)
        """

    def execute(
        self,
        design_spec: DesignSpecification,
        quality_standards: Optional[str] = None,
    ) -> DesignReviewReport:
        """
        Execute comprehensive design review.

        Args:
            design_spec: DesignSpecification to review
            quality_standards: Optional additional quality standards

        Returns:
            DesignReviewReport with aggregated results

        Raises:
            AgentExecutionError: If orchestration fails
        """
```

### DesignReviewReport

```python
class DesignReviewReport(BaseModel):
    """Complete design review report."""

    task_id: str
    review_id: str  # Format: REVIEW-{TASK_ID}-{YYYYMMDD}-{HHMMSS}
    timestamp: datetime
    overall_assessment: Literal["PASS", "FAIL", "NEEDS_IMPROVEMENT"]

    automated_checks: dict[str, bool]
    issues_found: list[DesignIssue]
    improvement_suggestions: list[ImprovementSuggestion]
    checklist_review: list[ChecklistItemReview]

    critical_issue_count: int
    high_issue_count: int
    medium_issue_count: int
    low_issue_count: int

    reviewer_agent: str
    agent_version: str
    review_duration_ms: float
```

### DesignIssue

```python
class DesignIssue(BaseModel):
    """Represents a design quality issue."""

    issue_id: str  # Format: ISSUE-{001-999}
    category: Literal[
        "Security", "Performance", "Data Integrity",
        "Error Handling", "Architecture", "Maintainability",
        "API Design", "Scalability"
    ]
    severity: Literal["Critical", "High", "Medium", "Low"]
    description: str  # Min 20 chars
    evidence: str  # Min 10 chars - specific location in design
    impact: str  # Min 20 chars - why it matters
```

### ImprovementSuggestion

```python
class ImprovementSuggestion(BaseModel):
    """Actionable improvement recommendation."""

    suggestion_id: str  # Format: IMPROVE-{001-999}
    title: str  # Min 10 chars
    description: str  # Min 30 chars
    priority: Literal["Critical", "High", "Medium", "Low"]
    category: Literal[...]  # Same as DesignIssue
    implementation_notes: str  # Min 20 chars
    related_issue_ids: list[str]  # Optional links to issues
```

---

## Additional Resources

- **Architecture Decision:** `docs/design_review_agent_architecture_decision.md`
- **Data Models:** `src/asp/models/design_review.py`
- **Unit Tests:** `tests/unit/test_agents/test_design_review_agent.py`
- **E2E Tests:** `tests/e2e/test_design_review_agent_e2e.py`
- **Example Scripts:** `examples/design_review_agent_example.py`
- **Langfuse Dashboard:** https://us.cloud.langfuse.com

---

**Questions or Issues?**
File an issue in the repository or contact the ASP development team.
