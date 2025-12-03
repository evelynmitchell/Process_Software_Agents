# ASP Platform - Agent Reference Documentation

**Version:** 1.0.0
**Last Updated:** December 3, 2025
**Status:** Production Ready

---

## Table of Contents

1. [Overview](#overview)
2. [Agent Architecture](#agent-architecture)
3. [Core Agents](#core-agents)
   - [1. Planning Agent](#1-planning-agent)
   - [2. Design Agent](#2-design-agent)
   - [3. Design Review Agent](#3-design-review-agent)
   - [4. Code Agent](#4-code-agent)
   - [5. Code Review Agent](#5-code-review-agent)
   - [6. Test Agent](#6-test-agent)
   - [7. Postmortem Agent](#7-postmortem-agent)
4. [Multi-Agent Review Systems](#multi-agent-review-systems)
5. [Pipeline Orchestration](#pipeline-orchestration)
6. [Prompt Versioning](#prompt-versioning)
7. [Telemetry and Observability](#telemetry-and-observability)
8. [Performance Characteristics](#performance-characteristics)
9. [Cost Analysis](#cost-analysis)
10. [Common Issues and Troubleshooting](#common-issues-and-troubleshooting)
11. [Best Practices](#best-practices)
12. [API Reference](#api-reference)

---

## Overview

The ASP (Agentic Software Process) Platform implements a disciplined, multi-agent system that applies Personal Software Process (PSP) and Team Software Process (TSP) methodology to autonomous AI agents. The platform consists of **7 core agents** that work together through a structured pipeline with mandatory quality gates.

### Key Principles

1. **Autonomy Through Reliability**: Agents earn autonomy through demonstrated accuracy
2. **Mandatory Quality Gates**: Formal review phases prevent error compounding
3. **Full Observability**: Complete telemetry of agent performance, cost, and quality metrics
4. **Bootstrap Learning**: Agents improve through data collection and PROBE-AI estimation
5. **Self-Improvement**: Postmortem analysis generates Process Improvement Proposals (PIPs)

### Agent Pipeline

```
Requirements
    ↓
┌─────────────────────────────────────────────────────────────┐
│ 1. Planning Agent                                           │
│    - Task decomposition into semantic units                 │
│    - Complexity scoring (C1 formula)                        │
│    - PROBE-AI estimation (Phase 2+)                         │
└─────────────────────────────────────────────────────────────┘
    ↓ ProjectPlan
┌─────────────────────────────────────────────────────────────┐
│ 2. Design Agent                                             │
│    - Low-level design specification                         │
│    - API contracts, data schemas, component logic           │
│    - Design review checklist generation                     │
└─────────────────────────────────────────────────────────────┘
    ↓ DesignSpecification
┌─────────────────────────────────────────────────────────────┐
│ 3. Design Review Agent (Multi-Agent Orchestrator)          │
│    - 6 specialist reviews in parallel                      │
│    - Security, Performance, Data Integrity                  │
│    - Maintainability, Architecture, API Design             │
│    - Quality gate: PASS / FAIL / NEEDS_IMPROVEMENT         │
└─────────────────────────────────────────────────────────────┘
    ↓ DesignReviewReport
    │ (if FAIL → feedback to Planning/Design for corrections)
    ↓
┌─────────────────────────────────────────────────────────────┐
│ 4. Code Agent                                               │
│    - Production-ready code generation                       │
│    - Complete file contents with tests                      │
│    - Multi-stage generation (manifest + files)              │
└─────────────────────────────────────────────────────────────┘
    ↓ GeneratedCode
┌─────────────────────────────────────────────────────────────┐
│ 5. Code Review Agent (Multi-Agent Orchestrator)            │
│    - 6 specialist reviews in parallel                      │
│    - Quality, Security, Performance                         │
│    - Test Coverage, Documentation, Best Practices          │
│    - Quality gate: PASS / CONDITIONAL_PASS / FAIL          │
└─────────────────────────────────────────────────────────────┘
    ↓ CodeReviewReport
    │ (if FAIL → feedback to Code Agent for fixes)
    ↓
┌─────────────────────────────────────────────────────────────┐
│ 6. Test Agent                                               │
│    - Build validation                                       │
│    - Test generation and execution                          │
│    - Defect logging with AI Defect Taxonomy                │
│    - Quality gate: PASS / FAIL / BUILD_FAILED              │
└─────────────────────────────────────────────────────────────┘
    ↓ TestReport
┌─────────────────────────────────────────────────────────────┐
│ 7. Postmortem Agent                                         │
│    - Performance analysis (planned vs. actual)              │
│    - Quality metrics (defect density, phase yield)          │
│    - Root cause analysis                                    │
│    - Process Improvement Proposal (PIP) generation          │
└─────────────────────────────────────────────────────────────┘
    ↓ PostmortemReport, PIP
```

---

## Agent Architecture

### Base Agent

All agents inherit from `BaseAgent` which provides:

- **LLM Integration**: Anthropic Claude Sonnet 4 via `LLMClient`
- **Prompt Management**: Load and format versioned prompts from `src/asp/prompts/`
- **Telemetry Decorators**: `@track_agent_cost` for automatic observability
- **Output Validation**: Pydantic model validation for all agent outputs
- **Error Handling**: Consistent `AgentExecutionError` exception handling

**Key Methods:**

```python
class BaseAgent:
    def load_prompt(self, prompt_name: str) -> str:
        """Load prompt template from src/asp/prompts/"""

    def format_prompt(self, template: str, **kwargs) -> str:
        """Format prompt with placeholders"""

    def call_llm(self, prompt: str, max_tokens: int, temperature: float) -> dict:
        """Call LLM and return response"""

    def validate_output(self, data: dict, model: Type[BaseModel]) -> BaseModel:
        """Validate response against Pydantic model"""

    def execute(self, input_data: BaseModel) -> BaseModel:
        """Main execution method (implemented by subclasses)"""
```

**File Location:** `/workspaces/Process_Software_Agents/src/asp/agents/base_agent.py`

---

## Core Agents

### 1. Planning Agent

**Purpose:** Decomposes high-level task requirements into measurable semantic units with complexity scoring.

**Role in Pipeline:** First agent in the pipeline; transforms requirements into structured project plan.

#### Inputs

```python
class TaskRequirements(BaseModel):
    task_id: str                      # Unique task identifier (e.g., "TASK-2025-001")
    project_id: str                   # Project identifier
    description: str                  # High-level task description
    requirements: str                 # Detailed requirements
    context_files: Optional[list[str]] = None  # Project context
```

#### Outputs

```python
class ProjectPlan(BaseModel):
    project_id: str
    task_id: str
    semantic_units: list[SemanticUnit]       # 3-8 semantic units
    total_est_complexity: int                # Sum of unit complexities
    probe_ai_prediction: Optional[ProbeAIPrediction] = None  # Phase 2+
    probe_ai_enabled: bool = False
    agent_version: str
    timestamp: datetime
```

**SemanticUnit Structure:**

```python
class SemanticUnit(BaseModel):
    unit_id: str                      # e.g., "SU-001"
    description: str                  # What needs to be implemented
    api_interactions: int             # 0-10
    data_transformations: int         # 0-10
    logical_branches: int             # 0-10
    code_entities_modified: int       # 0-10
    novelty_multiplier: float         # 1.0, 1.5, or 2.0
    est_complexity: int               # Calculated via C1 formula
    dependencies: list[str] = []      # Unit IDs this depends on
```

#### Configuration

**Environment Variables:**
- None specific to Planning Agent

**Initialization:**

```python
from asp.agents.planning_agent import PlanningAgent

agent = PlanningAgent(
    db_path=None,        # Optional: Override telemetry DB path
    llm_client=None,     # Optional: Mock LLM for testing
)
```

#### Usage Example

```python
from asp.agents.planning_agent import PlanningAgent
from asp.models.planning import TaskRequirements

# Initialize agent
agent = PlanningAgent()

# Create requirements
requirements = TaskRequirements(
    task_id="JWT-AUTH-001",
    project_id="AUTH-SYSTEM",
    description="Build JWT authentication system",
    requirements="Implement user registration, login, and token refresh endpoints with bcrypt password hashing and RS256 JWT tokens",
)

# Execute planning
plan = agent.execute(requirements)

# Inspect results
print(f"Task decomposed into {len(plan.semantic_units)} semantic units")
print(f"Total complexity: {plan.total_est_complexity}")

for unit in plan.semantic_units:
    print(f"{unit.unit_id}: {unit.description} (complexity: {unit.est_complexity})")
```

#### Prompt Versions

**Current Version:** `planning_agent_v1_decomposition.txt`

**Prompt Path:** `/workspaces/Process_Software_Agents/src/asp/prompts/planning_agent_v1_decomposition.txt`

**Key Features:**
- C1 complexity formula with weighted factors
- Complexity bands (1-10 Trivial, 11-30 Simple, 31-60 Moderate, 61-80 Complex, 81-100 Very Complex)
- Calibration examples for consistent scoring
- Few-shot learning with JWT auth example

**Feedback-Aware Version:** `planning_agent_v1_with_feedback.txt`

Used when Design Review identifies planning-phase issues requiring replanning.

#### Performance Characteristics

**Latency:**
- Typical: 3-8 seconds
- Simple tasks (3-4 units): ~3s
- Complex tasks (7-8 units): ~8s

**Token Usage:**
- Input: 2,000-3,000 tokens (prompt + requirements)
- Output: 800-1,500 tokens (3-8 semantic units)
- Total: ~2,800-4,500 tokens per execution

**Cost (Claude Sonnet 4):**
- $0.015-$0.025 per planning task
- Input: $0.003 per 1K tokens
- Output: $0.015 per 1K tokens

#### Common Issues

**Issue 1: Complexity Score Mismatch**

**Symptom:** Warning log: `"Unit SU-001: Complexity mismatch. LLM reported 25, calculated 27. Using calculated value."`

**Cause:** LLM miscalculates C1 formula or uses outdated scoring.

**Solution:** Agent auto-corrects by recalculating complexity. No action needed.

---

**Issue 2: Too Many Semantic Units**

**Symptom:** Plan contains 10+ semantic units for a simple task.

**Cause:** Over-decomposition or including non-implementation work.

**Solution:** Refine requirements to be more specific. Prompt enforces 3-8 unit limit.

---

**Issue 3: Missing Dependencies**

**Symptom:** `AgentExecutionError: "Circular dependency detected involving: SU-003"`

**Cause:** Invalid dependency graph (cycles or missing units).

**Solution:** Review semantic units. Ensure dependencies reference valid unit_ids and form a DAG.

#### Troubleshooting

**Enable Debug Logging:**

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Logs will show:
# - Prompt content (first 500 chars)
# - LLM response structure
# - Complexity calculations
# - Validation steps
```

**Inspect Artifacts:**

```bash
# Planning artifacts saved to artifacts/{task_id}/
cat artifacts/JWT-AUTH-001/plan.json       # JSON format
cat artifacts/JWT-AUTH-001/plan.md         # Markdown format
```

---

### 2. Design Agent

**Purpose:** Transforms requirements and project plans into detailed, implementation-ready technical designs.

**Role in Pipeline:** Second agent; creates low-level design specifications for the Code Agent.

#### Inputs

```python
class DesignInput(BaseModel):
    task_id: str
    requirements: str                        # Original requirements
    project_plan: ProjectPlan                # From Planning Agent
    context_files: Optional[list[str]] = None
    design_constraints: Optional[str] = None # Technology/architecture constraints
```

#### Outputs

```python
class DesignSpecification(BaseModel):
    task_id: str
    api_contracts: list[APIContract]          # Complete API specifications
    data_schemas: list[DataSchema]            # Database table definitions
    component_logic: list[ComponentLogic]     # Component/module specifications
    design_review_checklist: list[DesignReviewChecklistItem]  # Min 5 items
    architecture_overview: str                # Min 50 chars
    technology_stack: dict[str, str]          # Key-value pairs
    assumptions: list[str]
    total_complexity: int
    agent_version: str
    timestamp: datetime
```

**Key Submodels:**

```python
class APIContract(BaseModel):
    endpoint: str                    # "/api/users/register"
    http_method: str                 # "POST"
    request_schema: dict             # JSON schema
    response_schema: dict            # JSON schema
    error_responses: list[ErrorResponse]
    authentication_required: bool
    rate_limit: Optional[str]

class DataSchema(BaseModel):
    table_name: str
    description: str
    columns: list[ColumnDefinition]
    indexes: list[IndexDefinition]
    relationships: list[Relationship]

class ComponentLogic(BaseModel):
    component_name: str
    semantic_unit_id: str            # Links to ProjectPlan
    responsibilities: str
    public_interface: list[MethodSignature]
    dependencies: list[str]
    implementation_notes: str
```

#### Configuration

**Environment Variables:**
- `ASP_DESIGN_AGENT_USE_MARKDOWN`: "true" to use markdown output format (default: "false")

**Initialization:**

```python
from asp.agents.design_agent import DesignAgent

agent = DesignAgent(
    db_path=None,           # Optional: Override DB path
    llm_client=None,        # Optional: Mock LLM
    use_markdown=False,     # Optional: Use markdown format
    model=None,             # Optional: Override LLM model
)
```

#### Usage Example

```python
from asp.agents.design_agent import DesignAgent
from asp.models.design import DesignInput

# Initialize agent
agent = DesignAgent()

# Create design input (from planning output)
design_input = DesignInput(
    task_id="JWT-AUTH-001",
    requirements="Implement JWT authentication with registration and login",
    project_plan=project_plan,  # From Planning Agent
    design_constraints="Use FastAPI, PostgreSQL, bcrypt, RS256 JWT",
)

# Execute design
design_spec = agent.execute(design_input)

# Inspect results
print(f"Generated design with:")
print(f"  - {len(design_spec.api_contracts)} API endpoints")
print(f"  - {len(design_spec.data_schemas)} database tables")
print(f"  - {len(design_spec.component_logic)} components")
print(f"  - {len(design_spec.design_review_checklist)} review items")
```

#### Prompt Versions

**Current Versions:**

1. **JSON Format (v1):** `design_agent_v1_specification.txt`
   - Legacy format
   - Entire design in single JSON response
   - File: `/workspaces/Process_Software_Agents/src/asp/prompts/design_agent_v1_specification.txt`

2. **Markdown Format (v2):** `design_agent_v2_markdown.txt`
   - Human-readable output
   - Parsed to DesignSpecification
   - File: `/workspaces/Process_Software_Agents/src/asp/prompts/design_agent_v2_markdown.txt`

**Feedback-Aware Version:** `design_agent_v1_with_feedback.txt`

Used when Design Review identifies design-phase issues requiring redesign.

**Key Features:**
- Complete API contract templates
- Database schema templates with constraints
- Component logic templates with interfaces
- Security-first design (passwords hashed, parameterized queries)
- Traceability to semantic units

#### Performance Characteristics

**Latency:**
- Typical: 8-15 seconds
- Simple design (2-3 components): ~8s
- Complex design (8+ components): ~15s

**Token Usage:**
- Input: 3,000-5,000 tokens (prompt + requirements + plan)
- Output: 3,000-8,000 tokens (comprehensive design)
- Total: ~6,000-13,000 tokens per execution

**Cost (Claude Sonnet 4):**
- $0.045-$0.130 per design task
- Higher for complex designs with many components

#### Common Issues

**Issue 1: Missing Semantic Unit Coverage**

**Symptom:** `AgentExecutionError: "Design incomplete: semantic units ['SU-003'] have no corresponding components"`

**Cause:** Design Agent didn't create components for all semantic units.

**Solution:** Agent validates coverage automatically. If error persists, review requirements and re-execute.

---

**Issue 2: Circular Dependencies**

**Symptom:** `AgentExecutionError: "Design contains circular dependencies. Component 'AuthService' is part of a dependency cycle."`

**Cause:** Component A depends on B, B depends on C, C depends on A.

**Solution:** Redesign component boundaries. Use dependency injection or event-driven patterns to break cycles.

---

**Issue 3: Technology Stack Boolean Values**

**Symptom:** `ValidationError: Input should be a valid string [type=string_type]`

**Cause:** LLM returns `{"standard_library_only": true}` instead of `"yes"`/`"no"`.

**Solution:** Agent auto-corrects boolean values to strings. No action needed.

#### Troubleshooting

**View Artifacts:**

```bash
# Design artifacts saved to artifacts/{task_id}/
cat artifacts/JWT-AUTH-001/design.json     # JSON format
cat artifacts/JWT-AUTH-001/design.md       # Markdown format
```

**Test Markdown Format:**

```python
from asp.agents.design_agent import DesignAgent

agent = DesignAgent(use_markdown=True)
design_spec = agent.execute(design_input)
# Design generated using markdown parser
```

---

### 3. Design Review Agent

**Purpose:** Multi-agent system that performs comprehensive quality reviews of design specifications across 6 specialized dimensions.

**Role in Pipeline:** Quality gate after Design Agent; prevents design defects from propagating to code.

#### Inputs

```python
# Direct input
design_spec: DesignSpecification  # From Design Agent

# Optional
quality_standards: Optional[str] = None  # Additional standards
```

#### Outputs

```python
class DesignReviewReport(BaseModel):
    task_id: str
    review_id: str                   # "REVIEW-{TASK_ID}-{YYYYMMDD}-{HHMMSS}"
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

    reviewer_agent: str = "DesignReviewOrchestrator"
    agent_version: str
    review_duration_ms: float
```

**DesignIssue Structure:**

```python
class DesignIssue(BaseModel):
    issue_id: str                    # "ISSUE-001"
    category: Literal[
        "Security", "Performance", "Data Integrity",
        "Error Handling", "Architecture", "Maintainability",
        "API Design", "Scalability"
    ]
    severity: Literal["Critical", "High", "Medium", "Low"]
    description: str                 # Min 20 chars
    evidence: str                    # Min 10 chars - location in design
    impact: str                      # Min 20 chars - why it matters
    affected_phase: Literal["Planning", "Design", "Both"]  # For feedback routing
```

#### Configuration

**Initialization:**

```python
from asp.agents.design_review_orchestrator import DesignReviewOrchestrator

orchestrator = DesignReviewOrchestrator(
    llm_client=None,    # Optional: Mock LLM
    db_path=None,       # Optional: Override DB path
)
```

#### 6 Specialist Agents

The Design Review Orchestrator coordinates these specialists in parallel:

**1. SecurityReviewAgent**
- Focus: OWASP Top 10, authentication, encryption, injection prevention
- Prompt: `security_review_agent_v1.txt`
- Example Issues: Plaintext passwords, missing HTTPS, SQL injection

**2. PerformanceReviewAgent**
- Focus: Indexing, caching, N+1 queries, scalability
- Prompt: `performance_review_agent_v1.txt`
- Example Issues: Missing FK indexes, no caching layer, full table scans

**3. DataIntegrityReviewAgent**
- Focus: FK constraints, referential integrity, transactions
- Prompt: `data_integrity_review_agent_v1.txt`
- Example Issues: Missing NOT NULL constraints, incorrect cascade behavior

**4. MaintainabilityReviewAgent**
- Focus: Coupling, cohesion, separation of concerns
- Prompt: `maintainability_review_agent_v1.txt`
- Example Issues: Tight coupling, mixed responsibilities

**5. ArchitectureReviewAgent**
- Focus: Design patterns, layering, SOLID principles
- Prompt: `architecture_review_agent_v1.txt`
- Example Issues: Missing adapter patterns, circular dependencies

**6. APIDesignReviewAgent**
- Focus: RESTful principles, error handling, versioning
- Prompt: `api_design_review_agent_v1.txt`
- Example Issues: Non-RESTful endpoints, inconsistent error formats

#### Usage Example

```python
from asp.agents.design_review_orchestrator import DesignReviewOrchestrator

# Initialize orchestrator
orchestrator = DesignReviewOrchestrator()

# Execute review
report = orchestrator.execute(design_spec)

# Check results
print(f"Overall Assessment: {report.overall_assessment}")
print(f"Issues: {len(report.issues_found)} total")
print(f"  Critical: {report.critical_issue_count}")
print(f"  High: {report.high_issue_count}")
print(f"  Medium: {report.medium_issue_count}")
print(f"  Low: {report.low_issue_count}")
print(f"Suggestions: {len(report.improvement_suggestions)}")

# Filter critical issues
critical_issues = [i for i in report.issues_found if i.severity == "Critical"]
for issue in critical_issues:
    print(f"\n{issue.issue_id}: {issue.description}")
    print(f"  Evidence: {issue.evidence}")
    print(f"  Impact: {issue.impact}")
```

#### Prompt Versions

**Specialist Prompts (all v1):**
- `security_review_agent_v1.txt`
- `performance_review_agent_v1.txt`
- `data_integrity_review_agent_v1.txt`
- `maintainability_review_agent_v1.txt`
- `architecture_review_agent_v1.txt`
- `api_design_review_agent_v1.txt`

**Orchestrator Logic:**
- No separate prompt (orchestrator coordinates specialists)
- Aggregation, deduplication, conflict resolution in Python

#### Performance Characteristics

**Latency:**
- Typical: 25-40 seconds (parallel execution)
- Simple design: ~25 seconds
- Complex design: ~40 seconds
- Sequential equivalent: ~150-240 seconds (6x slower)

**Token Usage:**
- Input per specialist: 800-1,500 tokens
- Output per specialist: 500-1,000 tokens
- Total: ~9,000-15,000 tokens (6 specialists)

**Cost (Claude Sonnet 4):**
- $0.15-$0.25 per review
- Approximately 6x single-agent cost but catches 5-10x more issues

#### Overall Assessment Logic

```python
if critical_count > 0 or high_count > 0:
    overall_assessment = "FAIL"
elif medium_count > 0 or low_count > 0:
    overall_assessment = "NEEDS_IMPROVEMENT"
else:
    overall_assessment = "PASS"
```

#### Phase-Aware Feedback Routing

Issues include `affected_phase` field for intelligent routing:

- **Planning-phase issues** → Routes back to Planning Agent for replanning
- **Design-phase issues** → Routes back to Design Agent for redesign
- **Multi-phase issues** → Triggers both replanning and redesign

**Example:**

```python
# Issue from SecurityReviewAgent
{
    "issue_id": "ISSUE-001",
    "category": "Security",
    "severity": "Critical",
    "description": "Missing user role enumeration in design",
    "affected_phase": "Planning",  # Planning Agent needs to add role semantic unit
    "evidence": "No semantic unit addresses user role management",
    "impact": "Cannot implement role-based access control"
}
```

#### Common Issues

**Issue 1: Specialist Execution Failure**

**Symptom:** Review completes but one specialist has no results.

**Cause:** Specialist exception caught and handled gracefully.

**Solution:** Check Langfuse dashboard for specialist execution errors. Review continues with other specialists.

---

**Issue 2: Slow Review Performance (>60s)**

**Symptom:** Review takes longer than expected.

**Cause:** Network latency, very large design, or API rate limiting.

**Solution:**
- Check network connection to Anthropic API
- Simplify design for testing
- Monitor telemetry for bottlenecks

#### Troubleshooting

**View Detailed User Guide:**

See `/workspaces/Process_Software_Agents/docs/design_review_agent_user_guide.md` for:
- Complete API reference
- Specialist focus areas
- Severity guidelines
- Full examples

---

### 4. Code Agent

**Purpose:** Generates production-ready code from approved design specifications.

**Role in Pipeline:** Fourth agent; transforms design into complete, runnable code.

#### Inputs

```python
class CodeInput(BaseModel):
    task_id: str
    design_specification: DesignSpecification  # From Design Agent
    coding_standards: Optional[str] = None     # "Follow PEP 8, use type hints..."
    context_files: Optional[list[str]] = None
```

#### Outputs

```python
class GeneratedCode(BaseModel):
    task_id: str
    project_id: str
    files: list[GeneratedFile]                 # All generated files
    file_structure: dict[str, list[str]]       # Directory → filenames
    implementation_notes: str
    dependencies: list[str]                    # External packages
    setup_instructions: str
    total_lines_of_code: int
    total_files: int
    test_coverage_target: float
    semantic_units_implemented: list[str]
    components_implemented: list[str]
    agent_version: str
    generation_timestamp: str
```

**GeneratedFile Structure:**

```python
class GeneratedFile(BaseModel):
    file_path: str                   # "src/auth/user_service.py"
    content: str                     # Full file contents
    file_type: Literal["source", "test", "config", "documentation"]
    semantic_unit_id: Optional[str]  # Links to ProjectPlan
    component_id: Optional[str]      # Links to DesignSpecification
    description: str
```

#### Configuration

**Environment Variables:**
- `ASP_MULTI_STAGE_CODE_GEN`: "true" to use multi-stage generation (default: "false")

**Generation Modes:**

1. **Single-Call (Legacy):** Entire code in one JSON response
   - Pros: Simple, one LLM call
   - Cons: JSON escaping issues with large code blocks

2. **Multi-Stage (Recommended):** Two-phase generation
   - Phase 1: Generate file manifest (metadata only)
   - Phase 2: Generate each file content separately (raw code)
   - Pros: Avoids JSON escaping, handles large codebases
   - Cons: More LLM calls (N+1 for N files)

**Initialization:**

```python
from asp.agents.code_agent import CodeAgent

agent = CodeAgent(
    db_path=None,              # Optional: Override DB path
    llm_client=None,           # Optional: Mock LLM
    use_multi_stage=True,      # Optional: Use multi-stage generation
)
```

#### Usage Example

**Single-Call Generation:**

```python
from asp.agents.code_agent import CodeAgent
from asp.models.code import CodeInput

# Initialize agent (default single-call mode)
agent = CodeAgent()

# Create code input
code_input = CodeInput(
    task_id="JWT-AUTH-001",
    design_specification=design_spec,  # From Design Agent
    coding_standards="Follow PEP 8, use type hints, 80% test coverage",
)

# Execute code generation
generated_code = agent.execute(code_input)

# Inspect results
print(f"Generated {generated_code.total_files} files")
print(f"Total LOC: {generated_code.total_lines_of_code}")
print(f"Dependencies: {', '.join(generated_code.dependencies)}")

# Inspect file structure
for directory, files in generated_code.file_structure.items():
    print(f"\n{directory}/")
    for filename in files:
        print(f"  - {filename}")
```

**Multi-Stage Generation:**

```python
# Initialize with multi-stage mode
agent = CodeAgent(use_multi_stage=True)

# Execute (same interface)
generated_code = agent.execute(code_input)

# Multi-stage process:
# 1. Generate file manifest (fast, ~3-5s)
# 2. Generate each file content (N x 2-5s per file)
# Total: ~10-30s for 5-10 files
```

#### Prompt Versions

**Single-Call Prompts:**
- `code_agent_v1_generation.txt` - Generates complete code in one JSON response

**Multi-Stage Prompts:**
- `code_agent_v2_manifest.txt` - Generates file manifest (Phase 1)
- `code_agent_v2_file_generation.txt` - Generates individual file content (Phase 2)

**Key Features:**
- Complete file templates (source, tests, config)
- Security best practices (no hardcoded secrets)
- Error handling patterns
- Test generation guidance
- Documentation requirements

#### Performance Characteristics

**Latency:**

**Single-Call Mode:**
- Typical: 8-15 seconds
- Small codebase (3-5 files): ~8s
- Large codebase (10+ files): ~15s

**Multi-Stage Mode:**
- Manifest generation: 3-5 seconds
- Per-file generation: 2-5 seconds each
- Total: 10-30 seconds for 5-10 files
- Scales linearly with file count

**Token Usage:**

**Single-Call:**
- Input: 4,000-6,000 tokens
- Output: 5,000-12,000 tokens
- Total: ~9,000-18,000 tokens

**Multi-Stage:**
- Manifest input: 4,000-6,000 tokens
- Manifest output: 500-1,000 tokens
- Per-file input: 3,000-5,000 tokens
- Per-file output: 1,000-3,000 tokens
- Total: ~20,000-40,000 tokens for 5 files (more calls, similar total)

**Cost (Claude Sonnet 4):**
- Single-call: $0.090-$0.180 per code generation
- Multi-stage: $0.150-$0.300 per code generation (more reliable)

#### Generated File Structure

**Example for JWT Auth Task:**

```
artifacts/JWT-AUTH-001/generated_code/
├── src/
│   ├── auth/
│   │   ├── __init__.py
│   │   ├── user_service.py
│   │   ├── token_service.py
│   │   └── password_hasher.py
│   ├── api/
│   │   ├── __init__.py
│   │   └── auth_routes.py
│   └── models/
│       ├── __init__.py
│       └── user.py
├── tests/
│   ├── test_user_service.py
│   ├── test_token_service.py
│   └── test_auth_routes.py
├── requirements.txt
└── README.md
```

#### Common Issues

**Issue 1: JSON Escaping Errors (Single-Call Mode)**

**Symptom:** `JSONDecodeError: Expecting ',' delimiter`

**Cause:** LLM generates code with unescaped quotes or braces in JSON strings.

**Solution:** Switch to multi-stage mode:

```python
agent = CodeAgent(use_multi_stage=True)
```

---

**Issue 2: File Structure Inconsistency**

**Symptom:** `AgentExecutionError: "File structure inconsistency: ['config.yaml'] listed but not generated"`

**Cause:** Mismatch between file_structure and files list.

**Solution:** Agent validates automatically. If error persists, regenerate code.

---

**Issue 3: Missing Component Coverage**

**Symptom:** Warning: `"Design components: {...}, Generated file component IDs: {...}"`

**Cause:** Not all design components have corresponding code files.

**Solution:** Review design specification and regenerate with explicit component mappings.

#### Troubleshooting

**View Generated Code:**

```bash
# Code artifacts saved to artifacts/{task_id}/generated_code/
ls -la artifacts/JWT-AUTH-001/generated_code/

# View manifest
cat artifacts/JWT-AUTH-001/code_manifest.json
cat artifacts/JWT-AUTH-001/code_manifest.md

# View specific file
cat artifacts/JWT-AUTH-001/generated_code/src/auth/user_service.py
```

**Enable Multi-Stage Mode:**

```bash
export ASP_MULTI_STAGE_CODE_GEN=true
```

Or in code:

```python
agent = CodeAgent(use_multi_stage=True)
```

---

### 5. Code Review Agent

**Purpose:** Multi-agent system that performs comprehensive code quality reviews across 6 specialized dimensions.

**Role in Pipeline:** Quality gate after Code Agent; prevents code defects from reaching testing.

#### Inputs

```python
# Direct input
generated_code: GeneratedCode  # From Code Agent

# Optional
quality_standards: Optional[str] = None  # Additional standards
```

#### Outputs

```python
class CodeReviewReport(BaseModel):
    task_id: str
    review_id: str                   # "CODE-REVIEW-{TASK_ID}-{YYYYMMDD}-{HHMMSS}"
    review_status: Literal["PASS", "CONDITIONAL_PASS", "FAIL"]
    review_timestamp: str

    issues_found: list[CodeIssue]
    improvement_suggestions: list[CodeImprovementSuggestion]
    checklist_review: list[ChecklistItemReview]

    critical_issues: int
    high_issues: int
    medium_issues: int
    low_issues: int
    total_issues: int

    files_reviewed: int
    total_lines_reviewed: int
    agent_version: str
    review_duration_seconds: float
```

**CodeIssue Structure:**

```python
class CodeIssue(BaseModel):
    issue_id: str                    # "CODE-ISSUE-001"
    category: Literal[
        "Security", "Code Quality", "Performance",
        "Standards", "Testing", "Maintainability",
        "Error Handling", "Data Integrity"
    ]
    severity: Literal["Critical", "High", "Medium", "Low"]
    description: str
    file_path: str                   # File where issue found
    line_number: Optional[int]       # Specific line
    code_snippet: Optional[str]      # Problematic code
    recommendation: str
```

#### Configuration

**Initialization:**

```python
from asp.agents.code_review_orchestrator import CodeReviewOrchestrator

orchestrator = CodeReviewOrchestrator(
    llm_client=None,    # Optional: Mock LLM
    db_path=None,       # Optional: Override DB path
)
```

#### 6 Specialist Agents

The Code Review Orchestrator coordinates these specialists in parallel:

**1. CodeQualityReviewAgent**
- Focus: Complexity, duplication, readability, code smells
- Prompt: `code_quality_review_agent_v1.txt`
- Example Issues: High cyclomatic complexity, duplicate code

**2. CodeSecurityReviewAgent**
- Focus: Injection vulnerabilities, hardcoded secrets, crypto issues
- Prompt: `code_security_review_agent_v1.txt`
- Example Issues: SQL injection, hardcoded passwords, weak crypto

**3. CodePerformanceReviewAgent**
- Focus: Algorithmic complexity, resource leaks, inefficient patterns
- Prompt: `code_performance_review_agent_v1.txt`
- Example Issues: N+1 queries in loops, unbounded memory allocation

**4. TestCoverageReviewAgent**
- Focus: Test completeness, edge case coverage, assertions
- Prompt: `test_coverage_review_agent_v1.txt`
- Example Issues: Missing edge case tests, insufficient assertions

**5. DocumentationReviewAgent**
- Focus: Docstrings, comments, README, API documentation
- Prompt: `documentation_review_agent_v1.txt`
- Example Issues: Missing docstrings, outdated comments

**6. BestPracticesReviewAgent**
- Focus: Language idioms, design patterns, SOLID principles
- Prompt: `best_practices_review_agent_v1.txt`
- Example Issues: Not using context managers, missing type hints

#### Usage Example

```python
from asp.agents.code_review_orchestrator import CodeReviewOrchestrator

# Initialize orchestrator
orchestrator = CodeReviewOrchestrator()

# Execute review
report = orchestrator.execute(generated_code)

# Check results
print(f"Review Status: {report.review_status}")
print(f"Files Reviewed: {report.files_reviewed}")
print(f"Lines Reviewed: {report.total_lines_reviewed}")
print(f"Issues: {report.total_issues}")
print(f"  Critical: {report.critical_issues}")
print(f"  High: {report.high_issues}")

# Filter by file
for file_path in set(i.file_path for i in report.issues_found):
    file_issues = [i for i in report.issues_found if i.file_path == file_path]
    print(f"\n{file_path}: {len(file_issues)} issues")
    for issue in file_issues:
        print(f"  [{issue.severity}] {issue.description}")
```

#### Prompt Versions

**Specialist Prompts (all v1):**
- `code_quality_review_agent_v1.txt`
- `code_security_review_agent_v1.txt`
- `code_performance_review_agent_v1.txt`
- `test_coverage_review_agent_v1.txt`
- `documentation_review_agent_v1.txt`
- `best_practices_review_agent_v1.txt`

#### Performance Characteristics

**Latency:**
- Typical: 30-50 seconds (parallel execution)
- Small codebase (3-5 files): ~30 seconds
- Large codebase (10+ files): ~50 seconds

**Token Usage:**
- Input per specialist: 1,000-3,000 tokens (code content)
- Output per specialist: 500-1,500 tokens
- Total: ~12,000-27,000 tokens (6 specialists)

**Cost (Claude Sonnet 4):**
- $0.20-$0.40 per review
- Scales with codebase size

#### Review Status Logic

```python
if critical_issues > 0 or high_issues >= 5:
    review_status = "FAIL"
elif high_issues > 0:
    review_status = "CONDITIONAL_PASS"  # High issues but <5
else:
    review_status = "PASS"
```

**CONDITIONAL_PASS:** Code can proceed to testing with documented issues. High-severity issues must be addressed before production.

#### Common Issues

**Issue 1: High Issue Count for Generated Code**

**Symptom:** Review finds 10+ high-severity issues.

**Cause:** Code Agent generated code with quality issues.

**Solution:** Provide better coding standards in CodeInput. Review Design Agent output for clarity.

---

**Issue 2: False Positive Security Issues**

**Symptom:** Security agent flags safe code as vulnerable.

**Cause:** LLM misinterprets context or pattern.

**Solution:** Review issue evidence. If false positive, document and proceed.

#### Troubleshooting

**View Review Report:**

```bash
# Review artifacts saved to artifacts/{task_id}/
cat artifacts/JWT-AUTH-001/code_review_report.json
cat artifacts/JWT-AUTH-001/code_review_report.md
```

---

### 6. Test Agent

**Purpose:** Validates generated code through build verification, test generation, test execution, and defect logging.

**Role in Pipeline:** Sixth agent; ensures code quality through comprehensive testing.

#### Inputs

```python
class TestInput(BaseModel):
    task_id: str
    generated_code: GeneratedCode          # From Code Agent
    design_specification: DesignSpecification  # From Design Agent
    test_framework: str                    # "pytest", "unittest", etc.
    coverage_target: float                 # Target % (e.g., 80.0)
```

#### Outputs

```python
class TestReport(BaseModel):
    task_id: str
    test_status: Literal["PASS", "FAIL", "BUILD_FAILED"]
    build_successful: bool
    build_output: str

    test_summary: dict[str, int]           # {"total_tests": 10, "passed": 8, ...}
    coverage_percentage: float
    defects_found: list[TestDefect]

    critical_defects: int
    high_defects: int
    medium_defects: int
    low_defects: int

    agent_version: str
    test_timestamp: str
```

**TestDefect Structure:**

```python
class TestDefect(BaseModel):
    defect_id: str                   # "DEFECT-001"
    defect_type: Literal[
        "Planning_Failure", "Prompt_Misinterpretation",
        "Tool_Use_Error", "Hallucination",
        "Security_Vulnerability", "Conventional_Code_Bug",
        "Task_Execution_Error", "Alignment_Deviation"
    ]
    severity: Literal["Critical", "High", "Medium", "Low"]
    description: str
    evidence: str                    # Test failure output, stack trace
    phase_injected: Literal["Planning", "Design", "Code"]
    phase_removed: str               # "Test"
    effort_to_fix_vector: dict[str, float]  # Latency, tokens, cost
```

#### Configuration

**Initialization:**

```python
from asp.agents.test_agent import TestAgent

agent = TestAgent(
    db_path=None,      # Optional: Override DB path
    llm_client=None,   # Optional: Mock LLM
)
```

#### AI Defect Taxonomy

The Test Agent classifies defects using an 8-type AI-specific taxonomy:

1. **Planning_Failure**: Task decomposition errors, missing semantic units
2. **Prompt_Misinterpretation**: Agent misunderstood instructions
3. **Tool_Use_Error**: Incorrect API calls, malformed queries
4. **Hallucination**: Fabricated functions, non-existent libraries
5. **Security_Vulnerability**: Injection, weak crypto, missing auth
6. **Conventional_Code_Bug**: Logic errors, off-by-one, null references
7. **Task_Execution_Error**: Timeout, rate limit, resource exhaustion
8. **Alignment_Deviation**: Implemented wrong feature, misaligned with requirements

#### 4-Phase Testing Process

**Phase 1: Build Validation**
- Verify compilation/import success
- Check dependency installation
- Validate syntax

**Phase 2: Test Generation**
- Create comprehensive unit tests from design
- Cover edge cases, error paths
- Generate test fixtures

**Phase 3: Test Execution**
- Run generated tests
- Capture results and coverage
- Record failures with stack traces

**Phase 4: Defect Logging**
- Classify failures using AI Defect Taxonomy
- Assign severity based on impact
- Track phase injected/removed
- Calculate effort to fix

#### Usage Example

```python
from asp.agents.test_agent import TestAgent
from asp.models.test import TestInput

# Initialize agent
agent = TestAgent()

# Create test input
test_input = TestInput(
    task_id="JWT-AUTH-001",
    generated_code=generated_code,        # From Code Agent
    design_specification=design_spec,     # From Design Agent
    test_framework="pytest",
    coverage_target=80.0,
)

# Execute testing
test_report = agent.execute(test_input)

# Check results
print(f"Test Status: {test_report.test_status}")
print(f"Build Successful: {test_report.build_successful}")
print(f"Tests: {test_report.test_summary['passed']}/{test_report.test_summary['total_tests']}")
print(f"Coverage: {test_report.coverage_percentage}%")
print(f"Defects: {len(test_report.defects_found)}")

# Analyze defects
for defect in test_report.defects_found:
    print(f"\n{defect.defect_id}: {defect.defect_type} ({defect.severity})")
    print(f"  Phase: {defect.phase_injected} → {defect.phase_removed}")
    print(f"  Description: {defect.description}")
```

#### Prompt Versions

**Current Version:** `test_agent_v1_generation.txt`

**Key Features:**
- Build validation instructions
- Test generation templates (pytest, unittest)
- Coverage calculation guidance
- Defect classification examples
- Severity assignment rules

#### Performance Characteristics

**Latency:**
- Typical: 10-20 seconds
- Build validation: 2-3 seconds
- Test generation: 4-8 seconds
- Test execution: 4-9 seconds (depends on code complexity)

**Token Usage:**
- Input: 5,000-8,000 tokens (design + code)
- Output: 2,000-5,000 tokens (tests + results)
- Total: ~7,000-13,000 tokens

**Cost (Claude Sonnet 4):**
- $0.06-$0.13 per test execution

#### Test Status Logic

```python
if not build_successful:
    test_status = "BUILD_FAILED"
elif len(defects_found) > 0:
    test_status = "FAIL"
else:
    test_status = "PASS"
```

#### Common Issues

**Issue 1: Build Failed but test_status != BUILD_FAILED**

**Symptom:** `ValidationError: When build_successful is False, test_status must be BUILD_FAILED`

**Cause:** LLM inconsistency.

**Solution:** Agent auto-corrects test_status. No action needed.

---

**Issue 2: Test Summary Totals Don't Match**

**Symptom:** `AgentExecutionError: "Test summary inconsistent: total=10 but passed+failed+skipped=9"`

**Cause:** LLM miscalculated test counts.

**Solution:** Review test_summary in report. Regenerate if counts are critical.

---

**Issue 3: Defect Severity Mismatch**

**Symptom:** `AgentExecutionError: "Severity counts mismatch: critical=2 (actual=3)"`

**Cause:** Inconsistent severity assignment.

**Solution:** Agent validates and errors. Review defects_found and regenerate.

#### Troubleshooting

**View Test Report:**

```bash
# Test artifacts saved to artifacts/{task_id}/
cat artifacts/JWT-AUTH-001/test_report.json
cat artifacts/JWT-AUTH-001/test_report.md
```

**Analyze Defect Distribution:**

```python
from collections import defaultdict

defects_by_type = defaultdict(list)
for defect in test_report.defects_found:
    defects_by_type[defect.defect_type].append(defect)

for defect_type, defects in defects_by_type.items():
    print(f"{defect_type}: {len(defects)} defects")
```

---

### 7. Postmortem Agent

**Purpose:** Meta-agent for performance analysis, quality metrics, root cause analysis, and self-improvement through Process Improvement Proposals (PIPs).

**Role in Pipeline:** Final agent; analyzes completed task performance and generates improvement recommendations.

#### Inputs

```python
class PostmortemInput(BaseModel):
    task_id: str
    project_plan: ProjectPlan                  # From Planning Agent
    effort_log: list[EffortLogEntry]           # Performance data
    defect_log: list[DefectLogEntry]           # All defects found
    actual_semantic_complexity: float          # Final measured complexity
```

**EffortLogEntry Structure:**

```python
class EffortLogEntry(BaseModel):
    task_id: str
    phase: str                      # "Planning", "Design", "Code", etc.
    metric_type: str                # "Latency", "Tokens_In", "API_Cost"
    metric_value: float
    unit: str                       # "ms", "tokens", "USD"
    timestamp: datetime
```

**DefectLogEntry Structure:**

```python
class DefectLogEntry(BaseModel):
    defect_id: str
    defect_type: str                # AI Defect Taxonomy
    severity: str
    phase_injected: str
    phase_removed: str
    effort_to_fix_vector: dict[str, float]  # Latency, tokens, cost
    description: str
```

#### Outputs

```python
class PostmortemReport(BaseModel):
    task_id: str
    analysis_timestamp: datetime

    estimation_accuracy: EstimationAccuracy
    quality_metrics: QualityMetrics
    root_cause_analysis: list[RootCauseItem]

    summary: str                    # Executive summary (2-3 sentences)
    recommendations: list[str]
```

**EstimationAccuracy Structure:**

```python
class EstimationAccuracy(BaseModel):
    latency_ms: MetricComparison
    tokens: MetricComparison
    api_cost: MetricComparison
    semantic_complexity: MetricComparison

class MetricComparison(BaseModel):
    planned: float
    actual: float
    variance_percent: float         # Auto-calculated: ((actual-planned)/planned)*100
```

**QualityMetrics Structure:**

```python
class QualityMetrics(BaseModel):
    defect_density: float           # Defects per unit complexity
    total_defects: int
    defect_injection_by_phase: dict[str, int]
    defect_removal_by_phase: dict[str, int]
    phase_yield: dict[str, float]   # % of defects caught in each phase
```

**RootCauseItem Structure:**

```python
class RootCauseItem(BaseModel):
    defect_type: str                # From AI Defect Taxonomy
    occurrence_count: int
    total_effort_to_fix: float      # Sum of API costs
    average_effort_to_fix: float
    recommendation: str             # Specific improvement action
```

#### Configuration

**Initialization:**

```python
from asp.agents.postmortem_agent import PostmortemAgent

agent = PostmortemAgent(
    db_path=None,      # Optional: Override DB path
    llm_client=None,   # Optional: Mock LLM
)
```

#### Usage Example

**Performance Analysis:**

```python
from asp.agents.postmortem_agent import PostmortemAgent
from asp.models.postmortem import PostmortemInput

# Initialize agent
agent = PostmortemAgent()

# Create postmortem input (from completed task)
postmortem_input = PostmortemInput(
    task_id="JWT-AUTH-001",
    project_plan=project_plan,           # From Planning Agent
    effort_log=effort_entries,           # Collected during execution
    defect_log=defect_entries,           # From Test Agent + Reviews
    actual_semantic_complexity=68.5,     # Final measured
)

# Execute analysis
report = agent.execute(postmortem_input)

# View results
print(f"\nEstimation Accuracy:")
print(f"  Latency: {report.estimation_accuracy.latency_ms.variance_percent:.1f}% variance")
print(f"  Cost: {report.estimation_accuracy.api_cost.variance_percent:.1f}% variance")

print(f"\nQuality Metrics:")
print(f"  Defect Density: {report.quality_metrics.defect_density:.2f}")
print(f"  Total Defects: {report.quality_metrics.total_defects}")

print(f"\nRoot Causes:")
for cause in report.root_cause_analysis:
    print(f"  {cause.defect_type}: {cause.occurrence_count} occurrences")
    print(f"    Total fix effort: ${cause.total_effort_to_fix:.4f}")
    print(f"    Recommendation: {cause.recommendation}")

print(f"\nSummary: {report.summary}")
```

**Process Improvement Proposal (PIP) Generation:**

```python
# Generate PIP from postmortem report
pip = agent.generate_pip(report, postmortem_input)

print(f"\nPIP ID: {pip.proposal_id}")
print(f"Target: {pip.target_artifact_type}")
print(f"Status: {pip.hitl_status}")
print(f"\nProposed Changes:")

for change in pip.proposed_changes:
    print(f"\n  {change.change_type}: {change.target_file}")
    print(f"  Rationale: {change.rationale}")
    print(f"  Expected Impact: {change.expected_impact}")
```

#### PIP Workflow

**Process Improvement Proposal Structure:**

```python
class ProcessImprovementProposal(BaseModel):
    proposal_id: str                 # "PIP-20251125143022"
    task_id: str
    creation_timestamp: datetime
    target_artifact_type: Literal["prompt", "checklist", "orchestrator"]
    proposed_changes: list[ProposedChange]
    rationale: str
    expected_impact: str
    hitl_status: Literal["pending", "approved", "rejected"] = "pending"
    hitl_reviewer: Optional[str] = None
    hitl_review_timestamp: Optional[datetime] = None
    hitl_feedback: Optional[str] = None

class ProposedChange(BaseModel):
    change_type: Literal["add", "modify", "remove"]
    target_file: str                 # "src/asp/prompts/planning_agent_v1_decomposition.txt"
    section_identifier: Optional[str]  # "CALIBRATION EXAMPLES"
    before_content: Optional[str]
    after_content: str
    rationale: str
    expected_impact: str
```

**HITL Approval Process:**

1. **Generate PIP**: Postmortem Agent creates PIP with `hitl_status="pending"`
2. **Human Review**: Developer reviews PIP, approves/rejects
3. **Apply Changes**: If approved, update prompts/checklists
4. **Track Impact**: Monitor defect rates in subsequent tasks

#### Prompt Versions

**Current Version:** `postmortem_agent_v1_pip_generation.txt`

**Key Features:**
- Performance analysis templates
- Root cause analysis logic
- PIP generation instructions
- Change proposal formatting
- HITL workflow guidance

#### Performance Characteristics

**Latency:**
- Analysis: 3-6 seconds (calculation-heavy, minimal LLM)
- PIP generation: 5-10 seconds (requires LLM call)
- Total: 8-16 seconds

**Token Usage (PIP Generation):**
- Input: 2,000-4,000 tokens (postmortem report + defect log)
- Output: 1,000-2,000 tokens (PIP with changes)
- Total: ~3,000-6,000 tokens

**Cost (Claude Sonnet 4):**
- Analysis only: ~$0.00 (no LLM calls, pure calculation)
- PIP generation: $0.02-$0.04
- Total: $0.02-$0.04 per postmortem with PIP

#### Derived Measures

**Estimation Accuracy:**
- Variance % = ((Actual - Planned) / Planned) × 100
- Acceptable range: ±20%
- Used to calibrate PROBE-AI (Phase 2+)

**Defect Density:**
- Defects per unit complexity
- Formula: Total Defects / Actual Semantic Complexity
- Industry benchmark: 0.1-0.3 for mature processes

**Phase Yield:**
- % of defects caught in each phase
- Formula: (Defects Removed in Phase / Total Defects) × 100
- Target: >70% caught before Test phase

**Root Cause Ranking:**
- Ranked by total effort to fix (API cost)
- Top 3-5 causes drive PIP recommendations

#### Common Issues

**Issue 1: Zero Planned Metrics (Phase 1)**

**Symptom:** All variance_percent values are 0.0 or ∞

**Cause:** PROBE-AI not enabled yet (Phase 1 baseline collection).

**Solution:** Expected behavior. Collect 10-20 tasks before enabling PROBE-AI.

---

**Issue 2: PIP Generation Failure**

**Symptom:** `AgentExecutionError: "Failed to generate PIP: ..."`

**Cause:** LLM error, invalid response format.

**Solution:** Retry PIP generation. Check Langfuse for LLM errors.

---

**Issue 3: No Root Causes**

**Symptom:** `root_cause_analysis` is empty list.

**Cause:** No defects found (perfect execution or insufficient testing).

**Solution:** Expected for defect-free tasks. Recommendations default to "Continue current process."

#### Troubleshooting

**View Postmortem Report:**

```bash
# Postmortem artifacts saved to artifacts/{task_id}/
cat artifacts/JWT-AUTH-001/postmortem_report.json
cat artifacts/JWT-AUTH-001/postmortem_report.md
```

**View PIP:**

```bash
cat artifacts/JWT-AUTH-001/pip.json
```

**Analyze Defect Phases:**

```python
print("\nDefect Injection by Phase:")
for phase, count in report.quality_metrics.defect_injection_by_phase.items():
    print(f"  {phase}: {count} defects")

print("\nPhase Yield:")
for phase, yield_pct in report.quality_metrics.phase_yield.items():
    print(f"  {phase}: {yield_pct}% of defects caught")
```

---

## Multi-Agent Review Systems

Both Design Review and Code Review agents use a **multi-agent orchestrator pattern** for comprehensive quality analysis.

### Architecture Pattern

```
┌─────────────────────────────────────┐
│     Review Orchestrator             │
│  (DesignReview / CodeReview)        │
└─────────────────────────────────────┘
         │
         ├── async dispatch to specialists
         │
    ┌────┴────┬────────┬────────┬────────┬────────┐
    ▼         ▼        ▼        ▼        ▼        ▼
┌────────┐┌────────┐┌────────┐┌────────┐┌────────┐┌────────┐
│Spec 1  ││Spec 2  ││Spec 3  ││Spec 4  ││Spec 5  ││Spec 6  │
└────────┘└────────┘└────────┘└────────┘└────────┘└────────┘
    │         │        │        │        │        │
    └────┬────┴────────┴────────┴────────┴────────┘
         │
         ▼
┌─────────────────────────────────────┐
│  Aggregate, Deduplicate, Resolve    │
│  Generate Review Report             │
└─────────────────────────────────────┘
```

### Parallel Execution

**asyncio Integration:**

```python
async def _dispatch_specialists(self, input_spec):
    """Dispatch to all specialists in parallel."""

    async def run_specialist(name: str, agent: BaseAgent):
        # Run in thread pool (agents are synchronous)
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, agent.execute, input_spec)
        return (name, result)

    # Launch all specialists concurrently
    tasks = [run_specialist(name, agent) for name, agent in self.specialists.items()]
    results = await asyncio.gather(*tasks)

    return {name: result for name, result in results}
```

**Benefits:**
- 6x faster than sequential execution
- Independent specialist failures don't block others
- Graceful degradation (missing specialist = continue with others)

### Result Aggregation

**Deduplication Logic:**

```python
def _deduplicate_issues(self, issues: list[dict]) -> list[dict]:
    """Remove duplicate issues based on description similarity."""
    seen = set()
    unique_issues = []

    for issue in issues:
        # Create fingerprint from description + severity + category
        fingerprint = f"{issue['description'][:50]}_{issue['severity']}_{issue['category']}"

        if fingerprint not in seen:
            seen.add(fingerprint)
            unique_issues.append(issue)

    return unique_issues
```

**Conflict Resolution:**

- Multiple specialists flag same issue → Keep highest severity
- Category conflicts → Use most specific category
- Evidence conflicts → Concatenate all evidence

### Specialist Agent Pattern

All specialist agents follow this pattern:

```python
class SecurityReviewAgent(BaseAgent):
    """Specialist agent for security review."""

    def __init__(self, llm_client=None, db_path=None):
        super().__init__(llm_client=llm_client, db_path=db_path)
        self.agent_version = "1.0.0"
        self.focus_area = "Security"

    def execute(self, design_spec: DesignSpecification) -> dict:
        """Execute security-focused review."""
        # Load specialist prompt
        prompt = self.load_prompt("security_review_agent_v1")

        # Format with design spec
        formatted = self.format_prompt(
            prompt,
            design_json=design_spec.model_dump_json(indent=2)
        )

        # Call LLM
        response = self.call_llm(formatted, max_tokens=4000, temperature=0.0)

        # Return issues and suggestions
        return response["content"]
```

### Performance Optimization

**Parallel vs Sequential:**

```
Sequential (6 specialists × 7s each):  ~42 seconds
Parallel (max latency of 6 specialists): ~8 seconds
Speedup: 5-6x
```

**Resource Usage:**
- 6 concurrent API calls to Anthropic
- Memory: ~200-300 MB per orchestrator instance
- CPU: Minimal (I/O bound, waiting for LLM)

---

## Pipeline Orchestration

### PlanningDesignOrchestrator

Coordinates Planning → Design → Design Review with phase-aware feedback loops.

**Purpose:** Automate error correction by routing defects back to their originating phase.

#### Architecture

```
┌─────────────────────────────────────────────────┐
│  PlanningDesignOrchestrator                     │
│                                                 │
│  1. Planning Agent                              │
│  2. Design Agent                                │
│  3. Design Review Agent                         │
│  4. Feedback Routing (if FAIL)                  │
│  5. Iteration Limits (max 3 per phase, 10 total)│
└─────────────────────────────────────────────────┘
```

#### Phase-Aware Feedback Routing

**Routing Logic:**

```python
if review_report.overall_assessment == "FAIL":
    # Categorize issues by affected_phase
    planning_issues = [i for i in issues if i.affected_phase in ["Planning", "Both"]]
    design_issues = [i for i in issues if i.affected_phase in ["Design", "Both"]]

    if planning_issues:
        # Route back to Planning Agent for replanning
        revised_plan = planning_agent.execute(requirements, feedback=planning_issues)

    if design_issues:
        # Route back to Design Agent for redesign
        revised_design = design_agent.execute(design_input, feedback=design_issues)

    # Re-run Design Review on revised artifacts
    review_report = design_review.execute(revised_design)
```

**Error Correction Flow:**

```
Planning → Design → Design Review (finds planning error: missing role management)
    ↑                      ↓
    └───── REPLAN ─────────┘  (add role semantic unit)
             ↓
    Design (with updated plan) → Design Review (PASS) → Continue
```

#### Iteration Limits

**Safety Constraints:**

```python
MAX_PLANNING_ITERATIONS = 3
MAX_DESIGN_ITERATIONS = 3
MAX_TOTAL_ITERATIONS = 10

if planning_iterations >= MAX_PLANNING_ITERATIONS:
    raise OrchestratorError("Max planning iterations reached - manual intervention required")
```

**Why Limits?**
- Prevent infinite feedback loops
- Force human-in-the-loop for complex issues
- Control API costs

#### PlanningDesignResult

**Return Type:**

```python
class PlanningDesignResult(BaseModel):
    plan: ProjectPlan
    design: DesignSpecification
    review: DesignReviewReport

    planning_iterations: int
    design_iterations: int
    total_duration_ms: float
    total_cost_usd: float
```

**Usage:**

```python
from asp.orchestrators import PlanningDesignOrchestrator

orchestrator = PlanningDesignOrchestrator()
result = orchestrator.execute(requirements)

# Access artifacts
project_plan = result.plan
design_spec = result.design
review_report = result.review

# Check if corrections were needed
if result.planning_iterations > 1:
    print(f"Required {result.planning_iterations} planning iterations")
if result.design_iterations > 1:
    print(f"Required {result.design_iterations} design iterations")
```

#### Cost Impact

**Baseline (No Corrections):**
- Planning: $0.02
- Design: $0.10
- Design Review: $0.20
- Total: **$0.32**

**With Corrections (1 replan + 1 redesign):**
- Planning (×2): $0.04
- Design (×2): $0.20
- Design Review (×2): $0.40
- Total: **$0.64** (2x baseline)

**Cost vs Quality Tradeoff:**
- 20-50% cost increase for corrected tasks
- Prevents downstream defects (10x more expensive to fix in Test phase)
- Improves PROBE-AI accuracy through cleaner data

---

## Prompt Versioning

All prompts are versioned and stored in `/workspaces/Process_Software_Agents/src/asp/prompts/`.

### Naming Convention

```
{agent_name}_{version}_{variant}.txt
```

**Examples:**
- `planning_agent_v1_decomposition.txt` - Planning Agent v1, decomposition mode
- `planning_agent_v1_with_feedback.txt` - Planning Agent v1, feedback mode
- `design_agent_v1_specification.txt` - Design Agent v1, JSON format
- `design_agent_v2_markdown.txt` - Design Agent v2, Markdown format
- `security_review_agent_v1.txt` - Security Review specialist v1

### Version Lifecycle

**Version Transitions:**

1. **v1 (Current):** Initial production version
2. **v2 (Experimental):** New features, different format (e.g., Markdown)
3. **v1.1 (Patch):** Bug fixes, calibration updates (backward compatible)
4. **v3 (Breaking):** Major changes, incompatible with v2

### Loading Prompts

**BaseAgent Method:**

```python
def load_prompt(self, prompt_name: str) -> str:
    """
    Load prompt template from src/asp/prompts/.

    Args:
        prompt_name: Name without .txt extension (e.g., "planning_agent_v1_decomposition")

    Returns:
        Prompt template content

    Raises:
        FileNotFoundError: If prompt file doesn't exist
    """
    prompt_path = Path(__file__).parent.parent / "prompts" / f"{prompt_name}.txt"

    if not prompt_path.exists():
        raise FileNotFoundError(f"Prompt template not found: {prompt_path}")

    with open(prompt_path, "r", encoding="utf-8") as f:
        return f.read()
```

**Usage in Agents:**

```python
class PlanningAgent(BaseAgent):
    def execute(self, input_data: TaskRequirements) -> ProjectPlan:
        # Load v1 decomposition prompt
        prompt_template = self.load_prompt("planning_agent_v1_decomposition")

        # Format with input data
        formatted_prompt = self.format_prompt(
            prompt_template,
            task_id=input_data.task_id,
            description=input_data.description,
            requirements=input_data.requirements,
        )

        # Call LLM
        response = self.call_llm(formatted_prompt, max_tokens=4096, temperature=0.0)
```

### Prompt Structure

**Typical Sections:**

1. **ROLE**: Defines agent persona and expertise
2. **TASK**: Clear statement of what to generate
3. **INPUT**: Description of input data structure
4. **OUTPUT**: Complete JSON/Markdown schema with examples
5. **GUIDELINES**: Explicit rules and constraints
6. **EXAMPLES**: Few-shot learning examples for calibration
7. **EDGE CASES**: How to handle errors, ambiguity

**Example (Planning Agent):**

```
You are a PSP Planning Agent, a Senior Software Architect...

TASK: Decompose requirements into 3-8 semantic units...

COMPLEXITY FORMULA:
Semantic_Complexity = (2×API_Interactions) + (5×Data_Transformations) + ...

CALIBRATION EXAMPLES:
Example 1: Simple REST API Endpoint
Input: "Build GET /users/:id endpoint..."
Output: { "semantic_units": [...] }

IMPORTANT GUIDELINES:
1. Each semantic unit should be independently implementable
2. Units should be ordered in logical implementation sequence
3. Don't create units for documentation or meetings
...
```

### Prompt Updates (PIP Process)

**Process Improvement Proposal Workflow:**

1. **Identify Issue**: Postmortem Agent detects pattern (e.g., "Planning_Failure" defects recurring)
2. **Generate PIP**: Postmortem Agent creates PIP with specific prompt changes
3. **HITL Review**: Human reviews and approves/rejects PIP
4. **Apply Changes**: If approved, update prompt file with versioning
5. **Test**: Run test suite to verify new prompt performance
6. **Deploy**: Update agent to use new prompt version
7. **Monitor**: Track defect rates to measure impact

**Example PIP:**

```json
{
  "proposal_id": "PIP-20251125143022",
  "task_id": "JWT-AUTH-001",
  "target_artifact_type": "prompt",
  "proposed_changes": [
    {
      "change_type": "add",
      "target_file": "src/asp/prompts/planning_agent_v1_decomposition.txt",
      "section_identifier": "CALIBRATION EXAMPLES",
      "after_content": "Example 3: User Role Management\nInput: 'Add role-based access control'\nOutput: {...}",
      "rationale": "5 Planning_Failure defects related to missing role management semantic units",
      "expected_impact": "Reduce Planning_Failure defects by ~60% for RBAC tasks"
    }
  ]
}
```

---

## Telemetry and Observability

Full observability of agent performance, cost, and quality metrics.

### Telemetry Stack

**Components:**
- **Langfuse Cloud**: LLM trace visualization, prompt versioning
- **SQLite**: Local telemetry database (Phase 1-3)
- **PostgreSQL + TimescaleDB**: Production time-series database (Phase 4+)

### @track_agent_cost Decorator

**Automatic Instrumentation:**

```python
from asp.telemetry import track_agent_cost

@track_agent_cost(
    agent_role="Planning",
    task_id_param="input_data.task_id",
    llm_model="claude-sonnet-4-20250514",
    llm_provider="anthropic",
    agent_version="1.0.0",
)
def execute(self, input_data: TaskRequirements) -> ProjectPlan:
    # Execution logic
    ...
```

**Captured Metrics:**
- **Latency**: End-to-end execution time (ms)
- **Token Usage**: Input tokens, output tokens, total
- **API Cost**: USD cost based on Claude Sonnet 4 pricing
- **Task ID**: Traceability to task
- **Agent Version**: For A/B testing prompt versions

**Database Schema (agent_cost_vector table):**

```sql
CREATE TABLE agent_cost_vector (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id TEXT NOT NULL,
    agent_role TEXT NOT NULL,
    agent_version TEXT NOT NULL,
    llm_model TEXT NOT NULL,
    llm_provider TEXT NOT NULL,

    latency_ms REAL NOT NULL,
    tokens_in INTEGER NOT NULL,
    tokens_out INTEGER NOT NULL,
    total_tokens INTEGER NOT NULL,
    api_cost_usd REAL NOT NULL,

    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,

    INDEX idx_task_id (task_id),
    INDEX idx_agent_role (agent_role),
    INDEX idx_timestamp (timestamp)
);
```

### Langfuse Integration

**Trace Hierarchy:**

```
Trace: Task JWT-AUTH-001
├── Span: Planning Agent
│   ├── Generation: planning_agent_v1_decomposition
│   │   ├── Input: requirements
│   │   ├── Output: ProjectPlan (3 semantic units)
│   │   ├── Latency: 4.2s
│   │   ├── Tokens: 2,800 (in) + 1,200 (out)
│   │   └── Cost: $0.024
│   └── Metadata: {agent_version: "1.0.0", complexity: 45}
│
├── Span: Design Agent
│   ├── Generation: design_agent_v1_specification
│   │   └── ...
│
└── Span: Design Review Orchestrator
    ├── Span: Security Specialist
    ├── Span: Performance Specialist
    ├── ...
    └── Metadata: {overall_assessment: "FAIL", issues: 3}
```

**Configuration:**

```bash
# Environment variables
export LANGFUSE_PUBLIC_KEY="pk-lf-..."
export LANGFUSE_SECRET_KEY="sk-lf-..."
export LANGFUSE_HOST="https://cloud.langfuse.com"
```

**LLMClient Integration:**

```python
class LLMClient:
    def __init__(self):
        self.anthropic_client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        self.langfuse = Langfuse(
            public_key=os.getenv("LANGFUSE_PUBLIC_KEY"),
            secret_key=os.getenv("LANGFUSE_SECRET_KEY"),
            host=os.getenv("LANGFUSE_HOST"),
        )

    def generate(self, prompt: str, **kwargs):
        # Create Langfuse trace
        trace = self.langfuse.trace(name="agent_execution")
        generation = trace.generation(
            name="llm_call",
            model=kwargs.get("model", "claude-sonnet-4-20250514"),
            input=prompt,
        )

        # Call Anthropic API
        response = self.anthropic_client.messages.create(...)

        # Log to Langfuse
        generation.end(
            output=response.content,
            usage={
                "input_tokens": response.usage.input_tokens,
                "output_tokens": response.usage.output_tokens,
            },
        )

        return response
```

### Viewing Telemetry

**Langfuse Dashboard:**

1. Navigate to https://cloud.langfuse.com
2. Select project: "ASP Platform"
3. View traces by task_id
4. Analyze token usage, latency, costs
5. Compare prompt versions

**SQLite Queries:**

```bash
# Connect to telemetry database
sqlite3 data/asp_telemetry.db

# Query agent costs by role
SELECT
    agent_role,
    COUNT(*) as executions,
    ROUND(AVG(latency_ms), 2) as avg_latency_ms,
    ROUND(AVG(api_cost_usd), 4) as avg_cost_usd,
    ROUND(SUM(api_cost_usd), 4) as total_cost_usd
FROM agent_cost_vector
GROUP BY agent_role
ORDER BY total_cost_usd DESC;

# Query costs by task
SELECT
    task_id,
    COUNT(*) as agent_calls,
    ROUND(SUM(latency_ms)/1000, 2) as total_seconds,
    ROUND(SUM(api_cost_usd), 4) as total_cost_usd
FROM agent_cost_vector
GROUP BY task_id
ORDER BY total_cost_usd DESC;
```

### Bootstrap Learning Data

**Collected Metrics for PROBE-AI:**

- **Semantic Complexity** (planned vs actual)
- **Latency** (planned vs actual)
- **Token Usage** (planned vs actual)
- **API Cost** (planned vs actual)
- **Defect Density** (defects per unit complexity)
- **Phase Yield** (% defects caught per phase)

**Bootstrap Thresholds (PRD):**

| Capability | Data Needed | Accuracy Target | Status |
|------------|-------------|-----------------|--------|
| PROBE-AI Estimation | 10-20 tasks | MAPE < 20% | Phase 2 |
| Task Decomposition | 15-30 tasks | <10% correction rate | Phase 1 (collecting) |
| Error-Prone Detection | 30+ tasks | Risk map generation | Phase 3 |
| Review Effectiveness | 20-40 reviews | TP >80%, FP <20% | Phase 3 |
| Defect Type Prediction | 50+ tasks | 60% accuracy | Phase 5 |

**Current Status (as of Nov 2025):**
- **Tasks Collected**: 12+
- **Planning Agent**: 102 unit tests, 8 E2E tests passing
- **Bootstrap Data**: Partial collection in progress
- **PROBE-AI**: Not yet enabled (need 10-20 tasks)

---

## Performance Characteristics

### Agent Latency Summary

| Agent | Typical Latency | Token Usage | Cost per Execution |
|-------|----------------|-------------|-------------------|
| Planning | 3-8s | 2,800-4,500 | $0.015-$0.025 |
| Design | 8-15s | 6,000-13,000 | $0.045-$0.130 |
| Design Review | 25-40s | 9,000-15,000 | $0.15-$0.25 |
| Code (Single) | 8-15s | 9,000-18,000 | $0.09-$0.18 |
| Code (Multi) | 10-30s | 20,000-40,000 | $0.15-$0.30 |
| Code Review | 30-50s | 12,000-27,000 | $0.20-$0.40 |
| Test | 10-20s | 7,000-13,000 | $0.06-$0.13 |
| Postmortem | 3-6s | 0 (analysis only) | ~$0.00 |
| Postmortem + PIP | 8-16s | 3,000-6,000 | $0.02-$0.04 |

### End-to-End Pipeline

**Complete Task (No Corrections):**

```
Planning (5s) → Design (12s) → Design Review (35s) → Code (20s) →
Code Review (40s) → Test (15s) → Postmortem (5s)

Total Latency: ~132 seconds (~2.2 minutes)
Total Cost: $0.58-$1.02
```

**Complete Task (With Corrections):**

```
Planning (5s) → Design (12s) → Design Review (35s, FAIL) →
Replan (5s) → Redesign (12s) → Design Review (35s, PASS) →
Code (20s) → Code Review (40s, CONDITIONAL_PASS) →
Test (15s, FAIL: 2 defects) → Postmortem (5s) → PIP (10s)

Total Latency: ~194 seconds (~3.2 minutes)
Total Cost: $0.88-$1.54
```

### Scaling Characteristics

**Parallel Review Benefits:**

- Design Review: 6 specialists in ~35s (vs ~150s sequential) = **77% reduction**
- Code Review: 6 specialists in ~40s (vs ~180s sequential) = **78% reduction**

**Codebase Size Impact:**

| Codebase Size | Code Gen Latency | Code Review Latency | Total Cost |
|---------------|------------------|---------------------|------------|
| Small (3-5 files) | 10-15s | 30-35s | $0.30-$0.50 |
| Medium (6-10 files) | 15-25s | 35-45s | $0.50-$0.80 |
| Large (11-20 files) | 25-40s | 45-60s | $0.80-$1.20 |

### Optimization Strategies

**1. Prompt Caching (Future)**

Claude supports prompt caching - reuse long prompts across calls:
- Cache design specification in Code Agent (saves ~50% input tokens)
- Cache project plan in Design Agent (saves ~30% input tokens)

**2. Batching**

Process multiple tasks in parallel:
- Run 10 planning tasks concurrently (bounded by API rate limits)
- Aggregate telemetry for batch analysis

**3. Adaptive Token Limits**

Adjust max_tokens based on task complexity:
- Simple tasks: max_tokens=2000 (faster, cheaper)
- Complex tasks: max_tokens=8000 (more comprehensive)

**4. Specialist Pruning**

Disable low-value specialists for simple tasks:
- Skip APIDesignReviewAgent if no APIs in design
- Skip PerformanceReviewAgent for trivial CRUD operations

---

## Cost Analysis

### Claude Sonnet 4 Pricing (as of Nov 2025)

- **Input**: $0.003 per 1K tokens
- **Output**: $0.015 per 1K tokens (5x input cost)

### Cost Breakdown by Agent

**Planning Agent:**
- Input: 2,500 tokens × $0.003/1K = $0.0075
- Output: 1,200 tokens × $0.015/1K = $0.018
- **Total: $0.0255 per planning task**

**Design Agent:**
- Input: 4,500 tokens × $0.003/1K = $0.0135
- Output: 6,000 tokens × $0.015/1K = $0.090
- **Total: $0.1035 per design task**

**Design Review (6 specialists):**
- Per specialist: 1,000 input + 800 output = $0.015/specialist
- **Total: $0.090 per review (6 specialists)**

**Code Agent (Multi-Stage):**
- Manifest: 5,000 input + 800 output = $0.027
- Per file (5 files): 4,000 input + 2,000 output = $0.042/file
- **Total: $0.237 for 5 files**

**Code Review (6 specialists):**
- Per specialist: 2,000 input + 1,000 output = $0.021/specialist
- **Total: $0.126 per review (6 specialists)**

**Test Agent:**
- Input: 7,000 tokens × $0.003/1K = $0.021
- Output: 3,500 tokens × $0.015/1K = $0.0525
- **Total: $0.0735 per test execution**

**Postmortem Agent (with PIP):**
- Analysis: $0.00 (no LLM calls)
- PIP: 3,500 input + 1,500 output = $0.033
- **Total: $0.033 per postmortem + PIP**

### Budget Planning

**Monthly Budget Estimates:**

**Scenario 1: Small Team (10 tasks/month)**
- 10 tasks × $0.70/task (average with corrections) = **$7.00/month**

**Scenario 2: Medium Team (50 tasks/month)**
- 50 tasks × $0.70/task = **$35.00/month**

**Scenario 3: Large Team (200 tasks/month)**
- 200 tasks × $0.70/task = **$140.00/month**

**Cost Optimization:**
- Use single-call code generation for simple tasks (-30% cost)
- Skip review agents for trivial tasks (-40% cost)
- Cache prompts when available (-20% cost)

### Cost Monitoring

**Telemetry Queries:**

```sql
-- Daily cost by agent
SELECT
    DATE(timestamp) as date,
    agent_role,
    ROUND(SUM(api_cost_usd), 4) as daily_cost_usd
FROM agent_cost_vector
WHERE timestamp >= DATE('now', '-7 days')
GROUP BY DATE(timestamp), agent_role
ORDER BY date DESC, daily_cost_usd DESC;

-- Cost per task
SELECT
    task_id,
    ROUND(SUM(api_cost_usd), 4) as total_cost_usd,
    COUNT(*) as agent_executions,
    ROUND(SUM(api_cost_usd) / COUNT(*), 4) as avg_cost_per_agent
FROM agent_cost_vector
GROUP BY task_id
ORDER BY total_cost_usd DESC
LIMIT 10;

-- Monthly cost trend
SELECT
    strftime('%Y-%m', timestamp) as month,
    COUNT(DISTINCT task_id) as tasks,
    ROUND(SUM(api_cost_usd), 2) as total_cost_usd,
    ROUND(SUM(api_cost_usd) / COUNT(DISTINCT task_id), 4) as avg_cost_per_task
FROM agent_cost_vector
GROUP BY month
ORDER BY month DESC;
```

**Langfuse Cost Dashboard:**

1. Navigate to Langfuse → Analytics → Costs
2. Filter by date range, agent, task
3. View cost trends, outliers
4. Export CSV for reporting

---

## Common Issues and Troubleshooting

### Cross-Agent Issues

#### Issue: High API Costs

**Symptom:** Monthly costs exceed budget expectations.

**Diagnosis:**
```sql
-- Find most expensive tasks
SELECT task_id, SUM(api_cost_usd) as cost
FROM agent_cost_vector
GROUP BY task_id
ORDER BY cost DESC
LIMIT 10;

-- Find agents with high costs
SELECT agent_role, AVG(api_cost_usd) as avg_cost
FROM agent_cost_vector
GROUP BY agent_role
ORDER BY avg_cost DESC;
```

**Solutions:**
- Review expensive tasks for complexity issues
- Optimize prompts to reduce output tokens
- Use single-call code generation for simple tasks
- Skip optional review specialists

---

#### Issue: Telemetry Database Errors

**Symptom:** `Warning: Failed to log telemetry to database: table agent_cost_vector has no column named subtask_id`

**Cause:** Database schema mismatch.

**Solution:**
```bash
# Backup existing database
cp data/asp_telemetry.db data/asp_telemetry.db.backup

# Reinitialize database
uv run python scripts/init_database.py

# Restore critical data if needed
# (Langfuse Cloud has full trace history)
```

---

#### Issue: Langfuse Connection Failure

**Symptom:** Agent executes but no traces in Langfuse dashboard.

**Diagnosis:**
```bash
# Check environment variables
echo $LANGFUSE_PUBLIC_KEY  # Should show pk-lf-...
echo $LANGFUSE_SECRET_KEY  # Should show sk-lf-...
echo $LANGFUSE_HOST        # Should show https://cloud.langfuse.com
```

**Solutions:**
- Verify API keys in Langfuse dashboard
- Check network connectivity to Langfuse Cloud
- Review LLMClient logs for authentication errors
- Restart Codespace to reload environment variables

---

#### Issue: Agent Execution Timeout

**Symptom:** Agent hangs for >2 minutes, no response.

**Cause:** Network issue, API rate limit, or infinite loop.

**Diagnosis:**
```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Run agent with debug logging
agent.execute(input_data)
# Check logs for last operation before hang
```

**Solutions:**
- Check Anthropic API status (https://status.anthropic.com)
- Verify API rate limits not exceeded
- Reduce max_tokens to lower timeout risk
- Add timeout parameter to call_llm()

---

### Phase-Aware Feedback Issues

#### Issue: Infinite Feedback Loop

**Symptom:** Orchestrator exceeds iteration limits: `OrchestratorError: "Max planning iterations reached"`

**Cause:** Design Review repeatedly fails on same issue.

**Diagnosis:**
```python
# Review feedback history
for i, feedback_item in enumerate(planning_issues):
    print(f"Iteration {i}: {feedback_item.description}")
# Check if same issue recurring
```

**Solutions:**
- Manual intervention required
- Review Design Review criteria (may be too strict)
- Provide more explicit requirements
- Break task into smaller subtasks

---

#### Issue: Incorrect Phase Attribution

**Symptom:** Issue attributed to wrong phase (e.g., design issue marked as planning).

**Cause:** Design Review specialist misclassified issue.

**Diagnosis:**
```python
# Review issue details
for issue in review_report.issues_found:
    print(f"{issue.issue_id}: {issue.affected_phase} - {issue.description}")
```

**Solutions:**
- Update specialist prompt to clarify phase attribution
- Manually override affected_phase if needed
- Submit PIP to improve classifier

---

### Artifact Persistence Issues

#### Issue: Artifact Write Failure

**Symptom:** `Warning: Failed to write artifacts: [Errno 13] Permission denied`

**Cause:** Insufficient permissions on artifacts/ directory.

**Solution:**
```bash
# Fix permissions
chmod -R 755 artifacts/

# Verify directory exists
mkdir -p artifacts/

# Test write
echo "test" > artifacts/test.txt
```

---

#### Issue: Git Commit Failure

**Symptom:** `Warning: Not in git repository, skipping commit`

**Cause:** Not in git repository or git not initialized.

**Solution:**
```bash
# Verify git repository
git status

# If not in repo, initialize
git init
git add .
git commit -m "Initial commit"
```

---

## Best Practices

### 1. Task Requirements

**DO:**
- Provide specific, detailed requirements
- Include technology constraints (e.g., "Use PostgreSQL, FastAPI, bcrypt")
- Specify exact data types and constraints
- Reference existing architecture patterns

**DON'T:**
- Use vague requirements (e.g., "Make it secure")
- Mix multiple unrelated features in one task
- Omit critical constraints
- Assume agents know project context

**Example (Good):**

```python
requirements = TaskRequirements(
    task_id="USER-AUTH-001",
    description="Implement JWT-based user authentication system",
    requirements="""
    Build a JWT authentication system with the following:

    1. User Registration:
       - Endpoint: POST /api/auth/register
       - Input: email (valid email), password (min 12 chars)
       - Password hashing: bcrypt with cost factor 12
       - Email uniqueness validation
       - Return: user_id, email (no password in response)

    2. User Login:
       - Endpoint: POST /api/auth/login
       - Input: email, password
       - Validate credentials against hashed password
       - Generate JWT with RS256 algorithm
       - Token expiration: 1 hour
       - Return: access_token, expires_at, user_id

    3. Database:
       - Table: users (id UUID, email VARCHAR(255) UNIQUE, password_hash VARCHAR(255), created_at TIMESTAMP)
       - Use PostgreSQL
       - Add indexes on email for login performance

    4. Security:
       - Never log passwords
       - Rate limit: 5 login attempts per minute per IP
       - HTTPS required in production
    """,
    context_files=[
        "docs/api_standards.md",
        "src/database/schema.sql",
    ],
)
```

---

### 2. Iterative Development

**Start Simple, Then Expand:**

1. **Task 1**: Core authentication (registration + login)
2. **Task 2**: Token refresh endpoint
3. **Task 3**: Password reset flow
4. **Task 4**: Multi-factor authentication

**Benefits:**
- Smaller tasks = faster execution, lower cost
- Easier to debug issues
- Better bootstrap data (more tasks)
- Incremental complexity calibration

---

### 3. Review Quality Gates

**Don't Skip Reviews:**

- Design Review catches 60-80% of defects before code
- Code Review catches 20-30% of defects before test
- Review cost (20-30% of total) is much less than fixing defects later

**When to Skip:**
- Trivial config changes (no logic, no security impact)
- Documentation-only updates
- Already reviewed similar tasks

---

### 4. Telemetry Analysis

**Regular Reviews:**

```bash
# Weekly cost review
sqlite3 data/asp_telemetry.db "
SELECT
    strftime('%Y-%W', timestamp) as week,
    ROUND(SUM(api_cost_usd), 2) as weekly_cost
FROM agent_cost_vector
WHERE timestamp >= DATE('now', '-8 weeks')
GROUP BY week
ORDER BY week DESC;
"

# Monthly defect analysis
sqlite3 data/asp_telemetry.db "
SELECT
    defect_type,
    COUNT(*) as occurrences,
    AVG(severity) as avg_severity
FROM defect_log
WHERE timestamp >= DATE('now', '-1 month')
GROUP BY defect_type
ORDER BY occurrences DESC;
"
```

**Langfuse Dashboard:**
- Review traces weekly
- Identify prompt version performance
- Compare A/B test results
- Monitor token usage trends

---

### 5. Bootstrap Learning

**Data Collection Best Practices:**

- Aim for 10-20 tasks before enabling PROBE-AI
- Vary task complexity (mix simple and complex)
- Include diverse domains (CRUD, auth, integration, etc.)
- Ensure accurate defect logging (use AI Defect Taxonomy)
- Review estimation accuracy after each task

**PROBE-AI Readiness Checklist:**

- [ ] 10+ completed tasks with telemetry
- [ ] Complexity range: 20-80 (diverse)
- [ ] Defect density calculated for each task
- [ ] Phase yield measured (>70% caught before Test)
- [ ] Estimation variance analyzed (target ±20%)

---

### 6. Prompt Customization

**When to Update Prompts:**

- Recurring defect type (e.g., 5+ Planning_Failure in 10 tasks)
- Consistent estimation errors (MAPE > 30%)
- Review false positives (>20% of issues invalid)
- New technology stack (add calibration examples)

**Process:**

1. Generate PIP via Postmortem Agent
2. Review proposed changes
3. Create new prompt version (e.g., v1 → v1.1)
4. A/B test: run 5 tasks with v1, 5 with v1.1
5. Compare defect rates, estimation accuracy
6. Promote winner to default version

---

### 7. Error Handling

**Graceful Degradation:**

```python
try:
    report = orchestrator.execute(design_spec)
except AgentExecutionError as e:
    logger.error(f"Agent execution failed: {e}")
    # Fallback: return partial results
    # Or: retry with simplified input
    # Or: escalate to human
```

**Retry Strategy:**

```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10)
)
def execute_with_retry(agent, input_data):
    return agent.execute(input_data)
```

---

### 8. Version Control

**Artifact Versioning:**

```bash
# All artifacts in git
git log --oneline -- artifacts/JWT-AUTH-001/

# Compare design versions
git diff HEAD~1 artifacts/JWT-AUTH-001/design.md
```

**Prompt Versioning:**

```bash
# Track prompt changes
git log --oneline -- src/asp/prompts/planning_agent_v1_decomposition.txt

# Compare prompt versions
git diff v1.0.0 v1.1.0 -- src/asp/prompts/
```

---

## API Reference

### BaseAgent

**File:** `/workspaces/Process_Software_Agents/src/asp/agents/base_agent.py`

```python
class BaseAgent:
    """Base class for all ASP agents."""

    def __init__(
        self,
        db_path: Optional[Path] = None,
        llm_client: Optional[Any] = None,
    ):
        """
        Initialize base agent.

        Args:
            db_path: Optional path to SQLite database for telemetry
            llm_client: Optional LLM client (for dependency injection in tests)
        """

    def load_prompt(self, prompt_name: str) -> str:
        """
        Load prompt template from src/asp/prompts/.

        Args:
            prompt_name: Prompt name without .txt extension

        Returns:
            Prompt template content

        Raises:
            FileNotFoundError: If prompt file doesn't exist
        """

    def format_prompt(self, template: str, **kwargs) -> str:
        """
        Format prompt template with placeholders.

        Args:
            template: Prompt template with {placeholder} syntax
            **kwargs: Placeholder values

        Returns:
            Formatted prompt string
        """

    def call_llm(
        self,
        prompt: str,
        max_tokens: int = 4096,
        temperature: float = 0.0,
        model: Optional[str] = None,
    ) -> dict:
        """
        Call LLM and return response.

        Args:
            prompt: Formatted prompt
            max_tokens: Maximum tokens in response
            temperature: Sampling temperature (0.0-1.0)
            model: Optional model override

        Returns:
            Response dict with "content" (parsed JSON or raw text)

        Raises:
            AgentExecutionError: If LLM call fails
        """

    def validate_output(self, data: dict, model: Type[BaseModel]) -> BaseModel:
        """
        Validate response against Pydantic model.

        Args:
            data: Response data dictionary
            model: Pydantic model class

        Returns:
            Validated Pydantic model instance

        Raises:
            ValidationError: If validation fails
        """

    def execute(self, input_data: BaseModel) -> BaseModel:
        """
        Main execution method (implemented by subclasses).

        Args:
            input_data: Input Pydantic model

        Returns:
            Output Pydantic model

        Raises:
            AgentExecutionError: If execution fails
        """
```

### AgentExecutionError

```python
class AgentExecutionError(Exception):
    """Raised when agent execution fails."""
    pass
```

### Telemetry Decorator

```python
from asp.telemetry import track_agent_cost

@track_agent_cost(
    agent_role: str,           # "Planning", "Design", etc.
    task_id_param: str,        # Dotted path to task_id in args (e.g., "input_data.task_id")
    llm_model: str,            # "claude-sonnet-4-20250514"
    llm_provider: str,         # "anthropic"
    agent_version: str,        # "1.0.0"
)
def execute(self, input_data: BaseModel) -> BaseModel:
    """Agent execution method."""
```

### Artifact I/O Utilities

```python
from asp.utils.artifact_io import (
    write_artifact_json,
    write_artifact_markdown,
    write_generated_file,
)

# Write JSON artifact
json_path = write_artifact_json(
    task_id="JWT-AUTH-001",
    artifact_type="plan",  # "plan", "design", "code_manifest", etc.
    data=project_plan,     # Pydantic model
)

# Write Markdown artifact
md_path = write_artifact_markdown(
    task_id="JWT-AUTH-001",
    artifact_type="plan",
    markdown_content=markdown_str,
)

# Write generated code file
file_path = write_generated_file(
    task_id="JWT-AUTH-001",
    file=generated_file,   # GeneratedFile model
    base_path="artifacts/JWT-AUTH-001/generated_code",
)
```

### Git Utilities

```python
from asp.utils.git_utils import (
    git_commit_artifact,
    is_git_repository,
)

# Check if in git repo
if is_git_repository():
    # Commit artifacts
    commit_hash = git_commit_artifact(
        task_id="JWT-AUTH-001",
        agent_name="Planning Agent",
        artifact_files=["artifacts/JWT-AUTH-001/plan.json"],
    )
    print(f"Committed: {commit_hash}")
```

### Markdown Renderers

```python
from asp.utils.markdown_renderer import (
    render_plan_markdown,
    render_design_markdown,
    render_code_manifest_markdown,
    render_test_report_markdown,
    render_postmortem_report_markdown,
)

# Render ProjectPlan to Markdown
markdown = render_plan_markdown(project_plan)

# Render DesignSpecification to Markdown
markdown = render_design_markdown(design_spec)

# Render GeneratedCode manifest to Markdown
markdown = render_code_manifest_markdown(generated_code)

# Render TestReport to Markdown
markdown = render_test_report_markdown(test_report)

# Render PostmortemReport to Markdown
markdown = render_postmortem_report_markdown(postmortem_report)
```

---

## Additional Resources

### Documentation

- **PRD**: `/workspaces/Process_Software_Agents/PRD.md`
- **PSP Framework**: `/workspaces/Process_Software_Agents/PSPdoc.md`
- **Project Structure**: `/workspaces/Process_Software_Agents/PROJECT_STRUCTURE.md`
- **Design Review User Guide**: `/workspaces/Process_Software_Agents/docs/design_review_agent_user_guide.md`
- **Telemetry User Guide**: `/workspaces/Process_Software_Agents/docs/telemetry_user_guide.md`
- **Artifact Persistence**: `/workspaces/Process_Software_Agents/docs/artifact_persistence_user_guide.md`

### Architecture Decision Records (ADRs)

- **Planning Agent**: `/workspaces/Process_Software_Agents/docs/planning_agent_architecture_decision.md`
- **Design Agent**: `/workspaces/Process_Software_Agents/docs/design_agent_architecture_decision.md`
- **Design Review Agent**: `/workspaces/Process_Software_Agents/docs/design_review_agent_architecture_decision.md`
- **Error Correction Feedback**: `/workspaces/Process_Software_Agents/docs/error_correction_feedback_loops_decision.md`
- **Artifact Traceability**: `/workspaces/Process_Software_Agents/docs/artifact_traceability_decision.md`
- **Complexity Calibration**: `/workspaces/Process_Software_Agents/docs/complexity_calibration_decision.md`
- **Bootstrap Learning**: `/workspaces/Process_Software_Agents/docs/bootstrap_data_collection_decision.md`

### Test Documentation

- **Comprehensive Test Plan**: `/workspaces/Process_Software_Agents/docs/comprehensive_agent_test_plan.md`
- **Test Gap Analysis**: `/workspaces/Process_Software_Agents/docs/test_gap_analysis_and_recommendations.md`
- **Test Quick Start**: `/workspaces/Process_Software_Agents/docs/test_plan_quick_start.md`

### External Links

- **Langfuse Dashboard**: https://cloud.langfuse.com
- **Anthropic API Docs**: https://docs.anthropic.com
- **Claude Sonnet 4 Pricing**: https://www.anthropic.com/pricing
- **ASP Repository**: https://github.com/evelynmitchell/Process_Software_Agents

---

## Changelog

### Version 1.0.0 (November 25, 2025)

**Initial Release:**
- Complete documentation for all 7 core agents
- Multi-agent review system details
- Pipeline orchestration guide
- Telemetry and observability integration
- Performance and cost analysis
- Comprehensive troubleshooting guide
- API reference with code examples

**Agents Documented:**
1. Planning Agent (v1.0.0)
2. Design Agent (v1.0.0)
3. Design Review Agent (v1.0.0) + 6 specialists
4. Code Agent (v1.0.0)
5. Code Review Agent (v1.0.0) + 6 specialists
6. Test Agent (v1.0.0)
7. Postmortem Agent (v1.0.0)

**Total Agent Count:** 21 agents (7 core + 2 orchestrators + 12 specialists)

---

**Built with Claude Code**

*Autonomy is earned through demonstrated reliability, not assumed.*
