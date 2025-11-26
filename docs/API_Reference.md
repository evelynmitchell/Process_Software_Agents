# ASP Platform API Reference

**Version:** 1.0.0
**Last Updated:** November 26, 2025

Complete API reference for the Agentic Software Process (ASP) Platform Python API.

---

## Table of Contents

1. [Core Data Models](#core-data-models)
2. [Agent Classes](#agent-classes)
3. [Orchestrator Classes](#orchestrator-classes)
4. [Approval Services](#approval-services)
5. [Telemetry](#telemetry)
6. [Utilities](#utilities)
7. [Configuration](#configuration)

---

## Core Data Models

All data models are defined using Pydantic BaseModel for validation and serialization.

### Planning Models

Module: `asp.models.planning`

#### TaskRequirements

Input to Planning Agent representing a high-level task.

```python
class TaskRequirements(BaseModel):
    task_id: str  # Unique task identifier (e.g., 'TASK-2025-001')
    project_id: Optional[str]  # Project identifier for grouping
    description: str  # High-level task description (1-2 sentences)
    requirements: str  # Detailed requirements text
    context_files: Optional[list[str]]  # Paths to context files
```

**Validators:**
- `task_id`: Minimum 1 character
- `description`: Minimum 10 characters
- `requirements`: Minimum 20 characters

**Example:**
```python
requirements = TaskRequirements(
    task_id="TASK-2025-001",
    project_id="ASP-PLATFORM",
    description="Build user authentication system with JWT",
    requirements="""
        - User registration with email/password
        - Login endpoint with JWT token generation
        - Token validation middleware
    """,
    context_files=["docs/architecture.md"]
)
```

#### SemanticUnit

A decomposed unit of work with complexity scoring.

```python
class SemanticUnit(BaseModel):
    unit_id: str  # Unique identifier (pattern: ^SU-\d{3}$)
    description: str  # Clear description of work
    api_interactions: int  # Number of API calls (0-10)
    data_transformations: int  # Number of data conversions (0-10)
    logical_branches: int  # Number of conditionals (0-10)
    code_entities_modified: int  # Number of classes/functions (0-10)
    novelty_multiplier: float  # 1.0 (familiar), 1.5 (moderate), 2.0 (novel)
    est_complexity: int  # Calculated semantic complexity (1-100)
    dependencies: list[str]  # List of unit_ids this depends on
```

**Complexity Formula:**
```
Semantic_Complexity = (
    (2 × API_Interactions) +
    (5 × Data_Transformations) +
    (3 × Logical_Branches) +
    (4 × Code_Entities_Modified)
) × Novelty_Multiplier
```

**Example:**
```python
unit = SemanticUnit(
    unit_id="SU-001",
    description="Implement JWT token generation endpoint",
    api_interactions=2,
    data_transformations=3,
    logical_branches=2,
    code_entities_modified=3,
    novelty_multiplier=1.0,
    est_complexity=19,
    dependencies=[]
)
```

#### ProjectPlan

Output from Planning Agent containing decomposed semantic units.

```python
class ProjectPlan(BaseModel):
    project_id: Optional[str]  # Project identifier
    task_id: str  # Task identifier
    semantic_units: list[SemanticUnit]  # Decomposed units (1-15)
    total_est_complexity: int  # Sum of all unit complexities
    probe_ai_prediction: Optional[PROBEAIPrediction]  # PROBE-AI estimates
    probe_ai_enabled: bool  # Whether PROBE-AI was used
    agent_version: str  # Planning Agent version
```

**Validators:**
- `semantic_units`: Minimum 1, maximum 15 units
- `total_est_complexity`: Must be ≥ 1

**Example:**
```python
plan = ProjectPlan(
    task_id="TASK-2025-001",
    semantic_units=[unit1, unit2, unit3],
    total_est_complexity=85,
    probe_ai_enabled=False,
    agent_version="1.0.0"
)
```

#### PROBEAIPrediction

PROBE-AI estimation results (Phase 2 feature).

```python
class PROBEAIPrediction(BaseModel):
    total_est_latency_ms: float  # Predicted execution time
    total_est_tokens: int  # Predicted token usage
    total_est_api_cost: float  # Predicted API cost (USD)
    confidence: float  # R² coefficient (0.0-1.0)
```

---

### Design Models

Module: `asp.models.design`

#### DesignInput

Input to Design Agent combining requirements and project plan.

```python
class DesignInput(BaseModel):
    task_id: str  # Unique task identifier
    requirements: str  # Original requirements (min 20 chars)
    project_plan: ProjectPlan  # From Planning Agent
    context_files: list[str]  # Context files (default: [])
    design_constraints: Optional[str]  # Optional constraints
```

**Validators:**
- `task_id`: Minimum 3 characters
- `requirements`: Minimum 20 characters

**Example:**
```python
design_input = DesignInput(
    task_id="JWT-AUTH-001",
    requirements="Build JWT authentication with registration and login",
    project_plan=project_plan,
    context_files=["ARCHITECTURE.md"],
    design_constraints="Use FastAPI and PostgreSQL"
)
```

#### APIContract

API endpoint specification with complete request/response schemas.

```python
class APIContract(BaseModel):
    endpoint: str  # URL path (e.g., "/api/v1/users")
    method: str  # HTTP method (GET|POST|PUT|DELETE|PATCH)
    description: str  # What this endpoint does
    request_schema: Optional[dict[str, Any]]  # JSON schema for request
    request_params: Optional[dict[str, str]]  # Query/path parameters
    response_schema: dict[str, Any]  # JSON schema for response
    error_responses: list[dict[str, Any]]  # Possible error responses
    authentication_required: bool  # Requires auth (default: False)
    rate_limit: Optional[str]  # Rate limit specification
```

**Example:**
```python
api = APIContract(
    endpoint="/api/v1/auth/register",
    method="POST",
    description="Register a new user with email and password",
    request_schema={
        "email": "string (email format, required)",
        "password": "string (min 8 chars, required)"
    },
    response_schema={
        "user_id": "string (UUID)",
        "email": "string"
    },
    error_responses=[
        {"status": 400, "code": "INVALID_EMAIL"},
        {"status": 409, "code": "USER_EXISTS"}
    ],
    authentication_required=False,
    rate_limit="5 requests per minute per IP"
)
```

#### DataSchema

Database table specification with columns and constraints.

```python
class DataSchema(BaseModel):
    table_name: str  # Name of the table
    description: str  # Purpose of this table
    columns: list[dict[str, Any]]  # Column specifications
    indexes: list[str]  # Index definitions
    relationships: list[str]  # Foreign key relationships
    constraints: list[str]  # Additional constraints
```

**Example:**
```python
schema = DataSchema(
    table_name="users",
    description="Stores user account information",
    columns=[
        {"name": "user_id", "type": "UUID", "constraints": "PRIMARY KEY"},
        {"name": "email", "type": "VARCHAR(255)", "constraints": "NOT NULL UNIQUE"}
    ],
    indexes=["CREATE INDEX idx_users_email ON users(email)"],
    relationships=[],
    constraints=["CHECK (LENGTH(email) >= 5)"]
)
```

#### ComponentLogic

Component/module specification with interfaces and dependencies.

```python
class ComponentLogic(BaseModel):
    component_name: str  # Name of the component
    semantic_unit_id: str  # Links to Planning (pattern: ^SU-\d{3}$)
    responsibility: str  # What this component does
    interfaces: list[dict[str, Any]]  # Public methods/functions
    dependencies: list[str]  # Other components this depends on
    implementation_notes: str  # Detailed implementation guidance
    complexity: Optional[int]  # Estimated complexity (1-1000)
```

**Example:**
```python
component = ComponentLogic(
    component_name="UserAuthenticationService",
    semantic_unit_id="SU-001",
    responsibility="Handles user authentication and JWT token generation",
    interfaces=[{
        "method": "register_user",
        "parameters": {"email": "str", "password": "str"},
        "returns": "User",
        "description": "Register new user"
    }],
    dependencies=["DatabaseService", "PasswordHasher"],
    implementation_notes="Use bcrypt with cost factor 12",
    complexity=45
)
```

#### DesignReviewChecklistItem

Validation criterion for Design Review Agent.

```python
class DesignReviewChecklistItem(BaseModel):
    category: str  # Category of check
    description: str  # What to check
    validation_criteria: str  # How to validate
    severity: str  # Critical|High|Medium|Low (default: Medium)
```

**Example:**
```python
item = DesignReviewChecklistItem(
    category="Security",
    description="Verify password fields are hashed",
    validation_criteria="DataSchema must use 'password_hash' not 'password'",
    severity="Critical"
)
```

#### DesignSpecification

Complete design output from Design Agent.

```python
class DesignSpecification(BaseModel):
    task_id: str  # Unique task identifier
    api_contracts: list[APIContract]  # API endpoint specifications
    data_schemas: list[DataSchema]  # Database table specifications
    component_logic: list[ComponentLogic]  # Component specifications (min 1)
    design_review_checklist: list[DesignReviewChecklistItem]  # Validation criteria (min 5)
    architecture_overview: str  # High-level architecture description
    technology_stack: dict[str, str]  # Technology choices
    assumptions: list[str]  # Design assumptions and constraints
    timestamp: datetime  # When design was created
```

**Validators:**
- `component_logic`: Minimum 1 component required
- `design_review_checklist`: Minimum 5 items, at least one Critical/High severity

**Example:**
```python
design = DesignSpecification(
    task_id="JWT-AUTH-001",
    api_contracts=[api1, api2],
    data_schemas=[schema1],
    component_logic=[component1, component2],
    design_review_checklist=[item1, item2, item3, item4, item5],
    architecture_overview="3-tier architecture with FastAPI, PostgreSQL, Redis",
    technology_stack={
        "language": "Python 3.12",
        "framework": "FastAPI",
        "database": "PostgreSQL 15"
    },
    assumptions=["Email is unique identifier"],
    timestamp=datetime.now()
)
```

---

### Design Review Models

Module: `asp.models.design_review`

#### DesignIssue

Design quality issue identified during review.

```python
class DesignIssue(BaseModel):
    issue_id: str  # Pattern: ^ISSUE-\d{3}$
    category: Literal[
        "Security", "Performance", "Data Integrity",
        "Error Handling", "Architecture", "Maintainability",
        "API Design", "Scalability"
    ]
    severity: Literal["Critical", "High", "Medium", "Low"]
    description: str  # Clear description (min 20 chars)
    evidence: str  # Specific location in design (min 10 chars)
    impact: str  # Why this matters (min 20 chars)
    affected_phase: Literal["Planning", "Design", "Both"]  # Default: Design
```

**Example:**
```python
issue = DesignIssue(
    issue_id="ISSUE-001",
    category="Security",
    severity="Critical",
    description="Password stored in plaintext without hashing",
    evidence="users table, password column (VARCHAR)",
    impact="User credentials vulnerable to breach",
    affected_phase="Design"
)
```

#### ImprovementSuggestion

Actionable recommendation to improve the design.

```python
class ImprovementSuggestion(BaseModel):
    suggestion_id: str  # Pattern: ^IMPROVE-\d{3}$
    related_issue_id: Optional[str]  # Pattern: ^ISSUE-\d{3}$
    category: Literal[
        "Security", "Performance", "Data Integrity",
        "Error Handling", "Architecture", "Maintainability",
        "API Design", "Scalability"
    ]
    priority: Literal["High", "Medium", "Low"]
    description: str  # Specific recommendation (min 30 chars)
    implementation_notes: str  # How to implement (min 20 chars)
```

**Example:**
```python
suggestion = ImprovementSuggestion(
    suggestion_id="IMPROVE-001",
    related_issue_id="ISSUE-001",
    category="Security",
    priority="High",
    description="Implement bcrypt password hashing",
    implementation_notes="Use bcrypt.hashpw() with auto-generated salt"
)
```

#### DesignReviewReport

Complete design review report with assessment and issues.

```python
class DesignReviewReport(BaseModel):
    task_id: str  # Task identifier
    review_id: str  # Pattern: ^REVIEW-[A-Z0-9]+-\d{8}-\d{6}$
    timestamp: datetime  # Review completion timestamp
    overall_assessment: Literal["PASS", "FAIL", "NEEDS_IMPROVEMENT"]
    automated_checks: dict[str, bool]  # Validation results
    issues_found: list[DesignIssue]  # Issues identified
    improvement_suggestions: list[ImprovementSuggestion]  # Recommendations
    checklist_review: list[ChecklistItemReview]  # Checklist status

    # Phase-specific groupings (auto-populated)
    planning_phase_issues: list[DesignIssue]
    design_phase_issues: list[DesignIssue]
    multi_phase_issues: list[DesignIssue]

    # Summary counts
    critical_issue_count: int
    high_issue_count: int
    medium_issue_count: int
    low_issue_count: int

    # Metadata
    reviewer_agent: str  # Default: "DesignReviewAgent"
    agent_version: str  # Default: "1.0.0"
    review_duration_ms: float  # Review execution time
```

**Validators:**
- Issue counts must match actual issues found
- Overall assessment must be FAIL if Critical/High issues present
- All failed checklist items must have related issues

---

### Code Models

Module: `asp.models.code`

#### CodeInput

Input data for Code Agent.

```python
class CodeInput(BaseModel):
    task_id: str  # Unique task identifier (min 3 chars)
    design_specification: DesignSpecification  # Approved design
    design_review_report: Optional[DesignReviewReport]  # Optional review feedback
    coding_standards: Optional[str]  # Project coding standards
    context_files: Optional[list[str]]  # Additional context files
```

#### GeneratedFile

Single generated file with metadata.

```python
class GeneratedFile(BaseModel):
    file_path: str  # Relative file path
    content: str  # Complete file content (FULL file)
    file_type: str  # source|test|config|documentation|requirements|schema
    semantic_unit_id: Optional[str]  # Links to planning
    component_id: Optional[str]  # Links to design
    description: str  # Brief description (min 20 chars)
```

#### GeneratedCode

Complete code generation output from Code Agent.

```python
class GeneratedCode(BaseModel):
    task_id: str  # Task identifier
    project_id: Optional[str]  # Project identifier
    files: list[GeneratedFile]  # All generated files (min 1)
    file_structure: dict[str, list[str]]  # Directory structure
    implementation_notes: str  # Implementation approach (min 50 chars)
    dependencies: list[str]  # External dependencies
    setup_instructions: Optional[str]  # Setup instructions
    total_lines_of_code: int  # Total LOC (auto-calculated)
    total_files: int  # Total file count (auto-calculated)
    test_coverage_target: Optional[float]  # Expected coverage (0-100)
    semantic_units_implemented: list[str]  # Implemented unit IDs
    components_implemented: list[str]  # Implemented component IDs
    agent_version: str  # Default: "1.0.0"
    generation_timestamp: Optional[str]  # ISO 8601 timestamp
```

---

### Code Review Models

Module: `asp.models.code_review`

#### CodeIssue

Code quality issue identified during review.

```python
class CodeIssue(BaseModel):
    issue_id: str  # Pattern: ^CODE-ISSUE-\d{3}$
    category: Literal[
        "Security", "Code Quality", "Performance",
        "Standards", "Testing", "Maintainability",
        "Error Handling", "Data Integrity"
    ]
    severity: Literal["Critical", "High", "Medium", "Low"]
    description: str  # Clear description (min 20 chars)
    evidence: str  # Specific location (min 10 chars)
    impact: str  # Why this matters (min 20 chars)
    affected_phase: Literal["Planning", "Design", "Code", "Both"]  # Default: Code

    # Code-specific fields
    file_path: str  # File path where issue occurs
    line_number: Optional[int]  # Line number (≥1)
    code_snippet: Optional[str]  # Problematic code snippet

    # Traceability
    semantic_unit_id: Optional[str]  # From planning
    component_id: Optional[str]  # From design
```

#### CodeReviewReport

Complete code review report from all specialists.

```python
class CodeReviewReport(BaseModel):
    review_id: str  # Pattern: ^CODE-REVIEW-[A-Z0-9\-_]+-\d{8}-\d{6}$
    task_id: str  # Task identifier
    review_status: Literal["PASS", "FAIL", "CONDITIONAL_PASS"]

    # Review results
    issues_found: list[CodeIssue]
    improvement_suggestions: list[CodeImprovementSuggestion]
    checklist_review: list[ChecklistItemReview]

    # Phase-aware grouping (auto-populated)
    planning_phase_issues: list[CodeIssue]
    design_phase_issues: list[CodeIssue]
    code_phase_issues: list[CodeIssue]

    # Summary statistics (auto-calculated)
    total_issues: int
    critical_issues: int
    high_issues: int
    medium_issues: int
    low_issues: int
    files_reviewed: int
    total_lines_reviewed: int

    # Specialist results
    security_review_passed: bool
    quality_review_passed: bool
    performance_review_passed: bool
    standards_review_passed: bool
    testing_review_passed: bool
    maintainability_review_passed: bool

    # Metadata
    agent_version: str  # Default: "1.0.0"
    review_timestamp: str  # ISO 8601 timestamp
    review_duration_seconds: Optional[float]
```

**Review Status Logic:**
- PASS: No Critical/High issues, all quality gates passed
- FAIL: Critical issues OR ≥5 High issues OR any specialist FAIL
- CONDITIONAL_PASS: High issues present but <5, all Critical resolved

---

### Test Models

Module: `asp.models.test`

#### TestInput

Input data for Test Agent.

```python
class TestInput(BaseModel):
    task_id: str  # Unique task identifier (min 3 chars)
    generated_code: GeneratedCode  # Approved code from Code Agent
    design_specification: DesignSpecification  # For test generation
    test_framework: str  # Default: "pytest"
    coverage_target: float  # Default: 80.0 (0-100)
```

#### TestDefect

Defect found during testing phase using AI Defect Taxonomy.

```python
class TestDefect(BaseModel):
    defect_id: str  # Pattern: ^TEST-DEFECT-\d{3}$
    defect_type: Literal[
        "1_Planning_Failure", "2_Prompt_Misinterpretation",
        "3_Tool_Use_Error", "4_Hallucination",
        "5_Security_Vulnerability", "6_Conventional_Code_Bug",
        "7_Task_Execution_Error", "8_Alignment_Deviation"
    ]
    severity: Literal["Critical", "High", "Medium", "Low"]
    description: str  # Clear, actionable description (min 20 chars)
    evidence: str  # Test failure output, stack trace (min 10 chars)
    phase_injected: Literal["Planning", "Design", "Code"]
    phase_removed: str  # Default: "Test"
    file_path: Optional[str]  # File where defect occurs
    line_number: Optional[int]  # Line number (≥1)
    semantic_unit_id: Optional[str]  # For traceability
    component_id: Optional[str]  # For traceability
```

#### TestReport

Complete test execution report (Test Agent output).

```python
class TestReport(BaseModel):
    task_id: str  # Task identifier
    test_status: Literal["PASS", "FAIL", "BUILD_FAILED"]

    # Build results
    build_successful: bool
    build_errors: list[str]

    # Test execution summary
    test_summary: dict[str, int]  # {total_tests, passed, failed, skipped}
    coverage_percentage: Optional[float]  # Test coverage (0-100)

    # Defects found
    defects_found: list[TestDefect]

    # Generated tests metadata
    total_tests_generated: int
    test_files_created: list[str]

    # Severity counts (auto-calculated)
    critical_defects: int
    high_defects: int
    medium_defects: int
    low_defects: int

    # Metadata
    agent_version: str  # Default: "1.0.0"
    test_timestamp: str  # ISO 8601 timestamp
    test_duration_seconds: Optional[float]
```

**Validators:**
- test_status must be BUILD_FAILED if build_successful=False
- test_status cannot be PASS if defects found or tests failed
- test_summary must contain: total_tests, passed, failed, skipped

---

### Postmortem Models

Module: `asp.models.postmortem`

#### EffortLogEntry

Single entry from automated telemetry/effort log.

```python
class EffortLogEntry(BaseModel):
    timestamp: datetime  # Timestamp of agent execution
    task_id: str  # Unique task identifier
    agent_role: str  # Agent that executed
    metric_type: str  # Latency|Tokens_In|Tokens_Out|API_Cost
    metric_value: float  # Numeric value
    unit: str  # ms|tokens|USD
```

#### DefectLogEntry

Single entry from defect log.

```python
class DefectLogEntry(BaseModel):
    defect_id: str  # Unique defect identifier
    task_id: str  # Task identifier
    defect_type: Literal[
        "1_Planning_Failure", "2_Prompt_Misinterpretation",
        "3_Tool_Use_Error", "4_Hallucination",
        "5_Security_Vulnerability", "6_Conventional_Code_Bug",
        "7_Task_Execution_Error", "8_Alignment_Deviation"
    ]
    phase_injected: str  # Agent role that created defect
    phase_removed: str  # Agent role that found defect
    effort_to_fix_vector: Dict[str, float]  # {latency_ms, tokens, api_cost}
    description: str  # Detailed description
    severity: Optional[Literal["Critical", "High", "Medium", "Low"]]  # Default: Medium
```

#### PostmortemInput

Input data for Postmortem Agent.

```python
class PostmortemInput(BaseModel):
    task_id: str  # Task identifier (min 3 chars)
    project_plan: ProjectPlan  # Original plan from Planning Agent
    effort_log: List[EffortLogEntry]  # All effort measurements
    defect_log: List[DefectLogEntry]  # All defects found (default: [])
    actual_semantic_complexity: float  # Final actual complexity (>0)
```

#### PostmortemReport

Complete postmortem analysis report.

```python
class PostmortemReport(BaseModel):
    task_id: str  # Task identifier
    analysis_timestamp: datetime  # When analysis performed
    estimation_accuracy: EstimationAccuracy  # Planned vs actual comparison
    quality_metrics: QualityMetrics  # Defect density and distribution
    root_cause_analysis: List[RootCauseItem]  # Top defect types by effort
    summary: str  # Executive summary (2-3 sentences)
    recommendations: List[str]  # High-level recommendations
```

**Related Models:**

```python
class EstimationAccuracy(BaseModel):
    latency_ms: MetricComparison
    tokens: MetricComparison
    api_cost: MetricComparison
    semantic_complexity: MetricComparison

class MetricComparison(BaseModel):
    planned: float
    actual: float
    variance_percent: float  # ((actual - planned) / planned * 100)

class QualityMetrics(BaseModel):
    defect_density: float  # Total defects / Actual complexity
    total_defects: int
    defect_injection_by_phase: Dict[str, int]
    defect_removal_by_phase: Dict[str, int]
    phase_yield: Dict[str, float]

class RootCauseItem(BaseModel):
    defect_type: str  # AI Defect Taxonomy type
    occurrence_count: int
    total_effort_to_fix: float  # Total API cost (USD)
    average_effort_to_fix: float  # Average API cost per occurrence
    recommendation: str  # Recommended preventive action
```

#### ProcessImprovementProposal (PIP)

Process Improvement Proposal for HITL approval.

```python
class ProcessImprovementProposal(BaseModel):
    proposal_id: str  # Pattern: ^PIP-.+
    task_id: str  # Task that triggered PIP
    created_at: datetime  # When PIP was created
    analysis: str  # Analysis of the problem (2-4 sentences)
    proposed_changes: List[ProposedChange]  # Specific changes (min 1)
    expected_impact: str  # Expected impact of changes
    hitl_status: Literal["pending", "approved", "rejected", "needs_revision"]
    hitl_reviewer: Optional[str]  # Name/ID of human reviewer
    hitl_reviewed_at: Optional[datetime]  # Review timestamp
    hitl_feedback: Optional[str]  # Feedback from human reviewer
```

**Related Model:**

```python
class ProposedChange(BaseModel):
    target_artifact: str  # Artifact to change (e.g., 'code_review_checklist')
    change_type: Literal["add", "modify", "remove"]
    current_content: Optional[str]  # Current content (for modify/remove)
    proposed_content: str  # Proposed new/modified content
    rationale: str  # Why this change will prevent defects
```

---

## Agent Classes

All agents inherit from `BaseAgent` and implement the `execute()` method.

### BaseAgent

Module: `asp.agents.base_agent`

Abstract base class for all ASP agents.

```python
class BaseAgent(ABC):
    """
    Base class providing common functionality:
    - Prompt template loading
    - LLM client integration with retry logic
    - Telemetry decorator integration
    - Error handling and logging
    """

    def __init__(
        self,
        db_path: Optional[Path] = None,
        llm_client: Optional[Any] = None
    ):
        """
        Initialize base agent.

        Args:
            db_path: Optional path to SQLite database for telemetry
            llm_client: Optional LLM client (for dependency injection in tests)
        """
```

#### Methods

**load_prompt(prompt_name: str) -> str**

Load prompt template from file.

```python
prompt = agent.load_prompt("planning_agent_v1_decomposition")
# Loads: src/asp/prompts/planning_agent_v1_decomposition.txt
```

- **Args:**
  - `prompt_name`: Name of prompt file (without .txt extension)
- **Returns:** Prompt template content as string
- **Raises:** `FileNotFoundError` if prompt file doesn't exist

**format_prompt(template: str, **kwargs) -> str**

Format prompt template with variables.

```python
formatted = agent.format_prompt(
    template,
    task_description="Build API",
    requirements="REST endpoints"
)
```

- **Args:**
  - `template`: Prompt template string
  - `**kwargs`: Variables to substitute into template
- **Returns:** Formatted prompt string
- **Raises:** `ValueError` if required variables missing

**call_llm(prompt: str, model: Optional[str] = None, max_tokens: int = 4096, temperature: float = 0.0, **kwargs) -> Dict[str, Any]**

Call LLM with retry logic and telemetry.

```python
response = agent.call_llm(
    prompt=formatted_prompt,
    max_tokens=8000,
    temperature=0.1
)
```

- **Args:**
  - `prompt`: Formatted prompt string
  - `model`: Optional model name (overrides default)
  - `max_tokens`: Maximum tokens in response (default: 4096)
  - `temperature`: Sampling temperature (default: 0.0)
  - `**kwargs`: Additional arguments passed to LLM client
- **Returns:** Dictionary containing LLM response
- **Raises:** `AgentExecutionError` if LLM call fails after retries

**validate_output(data: Dict[str, Any], model_class: type[BaseModel]) -> BaseModel**

Validate LLM output against Pydantic model.

```python
validated = agent.validate_output(response, ProjectPlan)
```

- **Args:**
  - `data`: Dictionary data from LLM response
  - `model_class`: Pydantic model class to validate against
- **Returns:** Validated Pydantic model instance
- **Raises:** `ValidationError` if data doesn't match schema

**execute(input_data: BaseModel) -> BaseModel** *(abstract)*

Execute agent logic. Must be implemented by subclasses.

```python
@track_agent_cost(agent_role="Planning")
def execute(self, input_data: TaskRequirements) -> ProjectPlan:
    # Implementation here
    pass
```

- **Args:** `input_data`: Pydantic model with agent-specific input
- **Returns:** Pydantic model with agent-specific output
- **Raises:** `AgentExecutionError` if execution fails

---

### PlanningAgent

Module: `asp.agents.planning_agent`

Decomposes high-level requirements into semantic units with complexity scoring.

```python
class PlanningAgent(BaseAgent):
    """
    Planning Agent implementation.

    Phase 1: Task decomposition + complexity scoring
    Phase 2 (future): Add PROBE-AI estimation
    """

    def __init__(
        self,
        db_path: Optional[Path] = None,
        llm_client: Optional[Any] = None
    ):
        """Initialize Planning Agent."""
```

#### Methods

**execute(input_data: TaskRequirements, feedback: Optional[list] = None) -> ProjectPlan**

Execute Planning Agent logic with optional feedback.

```python
requirements = TaskRequirements(
    task_id="TASK-001",
    description="Build authentication",
    requirements="JWT tokens, registration..."
)
plan = planning_agent.execute(requirements)
```

- **Args:**
  - `input_data`: TaskRequirements with task details
  - `feedback`: Optional list of DesignIssue objects requiring replanning
- **Returns:** ProjectPlan with decomposed semantic units
- **Raises:** `AgentExecutionError` if decomposition fails
- **Decorator:** `@track_agent_cost(agent_role="Planning")`

**decompose_task(requirements: TaskRequirements) -> list[SemanticUnit]**

Decompose task into semantic units using LLM.

- **Args:** `requirements`: TaskRequirements to decompose
- **Returns:** List of validated SemanticUnit objects
- **Raises:** `AgentExecutionError` if decomposition fails

**decompose_task_with_feedback(requirements: TaskRequirements, feedback: list) -> list[SemanticUnit]**

Re-decompose task with Design Review feedback.

- **Args:**
  - `requirements`: Original TaskRequirements
  - `feedback`: List of DesignIssue objects with affected_phase="Planning"
- **Returns:** List of revised SemanticUnit objects
- **Raises:** `AgentExecutionError` if decomposition fails

---

### DesignAgent

Module: `asp.agents.design_agent`

Transforms requirements and project plans into detailed technical designs.

```python
class DesignAgent(BaseAgent):
    """
    Design Agent implementation.

    Generates:
    - API contracts (endpoints, schemas, error handling)
    - Data schemas (database tables, indexes, relationships)
    - Component logic (classes, interfaces, dependencies)
    - Design review checklist
    """

    def __init__(
        self,
        db_path: Optional[Path] = None,
        llm_client: Optional[Any] = None,
        use_markdown: Optional[bool] = None,
        model: Optional[str] = None
    ):
        """
        Initialize Design Agent.

        Args:
            db_path: Optional database path for telemetry
            llm_client: Optional LLM client for testing
            use_markdown: Use markdown output format (env: ASP_DESIGN_AGENT_USE_MARKDOWN)
            model: Optional model name (e.g., "claude-sonnet-4-5-20250929")
        """
```

#### Methods

**execute(input_data: DesignInput, feedback: Optional[list] = None) -> DesignSpecification**

Execute Design Agent to generate technical design.

```python
design_input = DesignInput(
    task_id="JWT-AUTH-001",
    requirements="Build JWT authentication...",
    project_plan=project_plan
)
design = design_agent.execute(design_input)
```

- **Args:**
  - `input_data`: DesignInput with requirements and project plan
  - `feedback`: Optional list of DesignIssue objects requiring redesign
- **Returns:** DesignSpecification with complete technical design
- **Raises:** `AgentExecutionError`, `ValidationError`
- **Decorator:** `@track_agent_cost(agent_role="Design")`

**Internal Methods:**

- `_generate_design(input_data)`: Generate design using JSON or Markdown format
- `_generate_design_json(input_data)`: Generate using JSON format (legacy)
- `_generate_design_markdown(input_data)`: Generate using Markdown format (v2)
- `_validate_semantic_unit_coverage(design_spec, project_plan)`: Ensure all semantic units have components
- `_validate_component_dependencies(design_spec)`: Check for circular dependencies

---

### CodeAgent

Module: `asp.agents.code_agent`

Generates production-ready code from design specifications.

```python
class CodeAgent(BaseAgent):
    """
    Code Agent implementation.

    Generates complete code with:
    - Full file contents (source, tests, config, docs)
    - File structure and dependencies
    - Implementation notes and setup instructions
    """

    def __init__(
        self,
        db_path: Optional[Path] = None,
        llm_client: Optional[Any] = None,
        use_multi_stage: Optional[bool] = None
    ):
        """
        Initialize Code Agent.

        Args:
            db_path: Optional database path for telemetry
            llm_client: Optional LLM client for testing
            use_multi_stage: Enable multi-stage generation (env: ASP_MULTI_STAGE_CODE_GEN)
                Phase 1: Generate file manifest
                Phase 2: Generate each file separately
        """
```

#### Methods

**execute(input_data: CodeInput) -> GeneratedCode**

Execute Code Agent to generate production-ready code.

```python
code_input = CodeInput(
    task_id="JWT-AUTH-001",
    design_specification=design_spec,
    coding_standards="Follow PEP 8..."
)
code = code_agent.execute(code_input)
```

- **Args:** `input_data`: CodeInput with design specification
- **Returns:** GeneratedCode with complete file contents
- **Raises:** `AgentExecutionError`, `ValidationError`
- **Decorator:** `@track_agent_cost(agent_role="Code")`

**Multi-Stage Generation:**

Two-phase approach to avoid JSON escaping issues:

1. **Phase 1:** `_generate_file_manifest(input_data)` → FileManifest
   - Small JSON output listing all files with metadata
   - No code content, just file planning

2. **Phase 2:** `_generate_file_content(file_meta, input_data)` → str
   - Generate raw code content for each file
   - No JSON wrapping, avoiding escaping issues

**Internal Methods:**

- `_generate_code(input_data)`: Route to single-call or multi-stage
- `_generate_code_single_call(input_data)`: Legacy single LLM call
- `_generate_code_multi_stage(input_data)`: New multi-stage approach
- `_validate_component_coverage(generated_code, design_spec)`: Verify component coverage
- `_validate_file_structure(generated_code)`: Check file structure consistency

---

### TestAgent

Module: `asp.agents.test_agent`

Validates code through build verification, test generation, and execution.

```python
class TestAgent(BaseAgent):
    """
    Test Agent implementation.

    Performs:
    - Build validation
    - Test generation from design specification
    - Test execution
    - Defect logging using AI Defect Taxonomy
    """

    def __init__(
        self,
        db_path: Optional[Path] = None,
        llm_client: Optional[Any] = None
    ):
        """Initialize Test Agent."""
```

#### Methods

**execute(input_data: TestInput) -> TestReport**

Execute Test Agent to validate code through testing.

```python
test_input = TestInput(
    task_id="TEST-001",
    generated_code=code,
    design_specification=design_spec,
    test_framework="pytest",
    coverage_target=85.0
)
report = test_agent.execute(test_input)
```

- **Args:** `input_data`: TestInput with code and design specification
- **Returns:** TestReport with build status, test results, and defects
- **Raises:** `AgentExecutionError`, `ValidationError`
- **Decorator:** `@track_agent_cost(agent_role="Test")`

**Internal Methods:**

- `_generate_and_execute_tests(input_data)`: Generate and run tests via LLM
- `_validate_test_report(report)`: Validate report consistency

---

### PostmortemAgent

Module: `asp.agents.postmortem_agent`

Analyzes performance data to calculate metrics and generate Process Improvement Proposals.

```python
class PostmortemAgent(BaseAgent):
    """
    Postmortem Agent (meta-agent) implementation.

    Analyzes:
    - Estimation accuracy (planned vs actual)
    - Quality metrics (defect density, phase distribution)
    - Root cause analysis
    - Process improvement opportunities
    """

    def __init__(
        self,
        db_path: Optional[Path] = None,
        llm_client: Optional[Any] = None
    ):
        """Initialize Postmortem Agent."""
```

#### Methods

**execute(input_data: PostmortemInput) -> PostmortemReport**

Execute Postmortem Agent for performance analysis.

```python
postmortem_input = PostmortemInput(
    task_id="POST-001",
    project_plan=project_plan,
    effort_log=effort_entries,
    defect_log=defect_entries,
    actual_semantic_complexity=45.2
)
report = postmortem_agent.execute(postmortem_input)
```

- **Args:** `input_data`: PostmortemInput with plan and logs
- **Returns:** PostmortemReport with metrics and PIPs
- **Raises:** `AgentExecutionError`, `ValidationError`
- **Decorator:** `@track_agent_cost(agent_role="Postmortem")`

---

## Orchestrator Classes

Orchestrators coordinate multiple agents through formal workflows.

### TSPOrchestrator

Module: `asp.orchestrators.tsp_orchestrator`

Complete autonomous development pipeline with quality gates and HITL approval.

```python
class TSPOrchestrator:
    """
    TSP Orchestrator: Complete autonomous development pipeline.

    Workflow:
    1. Planning Agent → Generate project plan
    2. Design Agent → Create design specification
    3. Design Review (Quality Gate) → Pass/Fail/HITL
    4. Code Agent → Generate implementation
    5. Code Review (Quality Gate) → Pass/Fail/HITL
    6. Test Agent → Build, test, validate
    7. Postmortem Agent → Analyze performance

    Quality Gates:
    - Design Review: Halts if critical/high issues (unless HITL override)
    - Code Review: Halts if critical or ≥5 high issues (unless HITL override)
    - Test: Halts if build fails or tests fail
    """

    # Maximum correction iterations
    MAX_DESIGN_ITERATIONS = 3
    MAX_CODE_ITERATIONS = 3
    MAX_TEST_ITERATIONS = 2
    MAX_TOTAL_ITERATIONS = 15

    def __init__(
        self,
        db_path: Optional[Path] = None,
        llm_client: Optional[Any] = None,
        approval_service: Optional[ApprovalService] = None
    ):
        """
        Initialize TSP Orchestrator.

        Args:
            db_path: Optional database path for telemetry
            llm_client: Optional LLM client for testing
            approval_service: Optional ApprovalService for HITL workflow
        """
```

#### Methods

**execute(requirements: TaskRequirements, design_constraints: Optional[str] = None, coding_standards: Optional[str] = None, hitl_approver: Optional[callable] = None) -> TSPExecutionResult**

Execute complete TSP autonomous development pipeline.

```python
orchestrator = TSPOrchestrator()
requirements = TaskRequirements(
    task_id="TASK-001",
    description="Build authentication",
    requirements="JWT tokens..."
)

result = orchestrator.execute(
    requirements=requirements,
    design_constraints="Use FastAPI and PostgreSQL",
    coding_standards="Follow PEP 8. Use type hints.",
    hitl_approver=lambda gate, report: True  # Auto-approve for demo
)

print(f"Status: {result.overall_status}")
print(f"Files: {result.generated_code.total_files}")
print(f"Tests: {result.test_report.test_summary['passed']}/
           {result.test_report.test_summary['total_tests']}")
```

- **Args:**
  - `requirements`: TaskRequirements with task description
  - `design_constraints`: Optional design constraints
  - `coding_standards`: Optional coding standards
  - `hitl_approver`: Optional callable for HITL approval
    - Signature: `(gate_name: str, report: dict) -> bool`
    - If None and no approval_service, quality gate failures raise exception
- **Returns:** `TSPExecutionResult` containing all artifacts and metadata
- **Raises:**
  - `QualityGateFailure`: If quality gate fails without HITL override
  - `MaxIterationsExceeded`: If correction loops exceed limits
  - `AgentExecutionError`: If agent execution fails

**TSPExecutionResult:**

```python
@dataclass
class TSPExecutionResult:
    task_id: str
    overall_status: str  # PASS|CONDITIONAL_PASS|FAIL|NEEDS_REVIEW
    project_plan: ProjectPlan
    design_specification: DesignSpecification
    design_review: DesignReviewReport
    generated_code: GeneratedCode
    code_review: CodeReviewReport
    test_report: TestReport
    postmortem_report: PostmortemReport
    execution_log: list[dict[str, Any]]
    hitl_overrides: list[dict[str, Any]]
    total_duration_seconds: float
    timestamp: datetime
```

**Quality Gate Logic:**

- **Design Review:**
  - PASS → Proceed to Code
  - NEEDS_IMPROVEMENT → Proceed with warnings
  - FAIL → Request HITL approval or retry (up to MAX_DESIGN_ITERATIONS)

- **Code Review:**
  - PASS → Proceed to Test
  - CONDITIONAL_PASS → Proceed with warnings (<5 high issues)
  - FAIL → Request HITL approval or retry (up to MAX_CODE_ITERATIONS)

- **Test:**
  - PASS → Proceed to Postmortem
  - FAIL → Regenerate code with feedback (up to MAX_TEST_ITERATIONS)

---

### PlanningDesignOrchestrator

Module: `asp.orchestrators.planning_design_orchestrator`

Orchestrates Planning and Design phases with feedback loop.

```python
class PlanningDesignOrchestrator:
    """
    Planning-Design Orchestrator.

    Workflow:
    1. Planning Agent → ProjectPlan
    2. Design Agent → DesignSpecification
    3. Design Review → Feedback
    4. If FAIL: Loop back to appropriate phase with feedback
    """

    def execute(
        self,
        requirements: TaskRequirements,
        design_constraints: Optional[str] = None,
        max_iterations: int = 3
    ) -> tuple[ProjectPlan, DesignSpecification, DesignReviewReport]:
        """
        Execute Planning-Design workflow with review feedback.

        Args:
            requirements: TaskRequirements
            design_constraints: Optional design constraints
            max_iterations: Maximum correction iterations (default: 3)

        Returns:
            Tuple of (ProjectPlan, DesignSpecification, DesignReviewReport)
        """
```

---

## Approval Services

Module: `asp.approval.base`

### ApprovalService (ABC)

Abstract base class for HITL approval services.

```python
class ApprovalService(ABC):
    """
    Abstract base class for Human-in-the-Loop approval services.

    Implementations can use:
    - GitHub PR workflow
    - Local file-based approval
    - Web-based approval UI
    - CLI-based approval
    """

    @abstractmethod
    def request_approval(
        self,
        request: ApprovalRequest
    ) -> ApprovalResponse:
        """
        Request human approval for quality gate failure.

        Args:
            request: ApprovalRequest with task info and quality report

        Returns:
            ApprovalResponse with decision and metadata
        """
        pass
```

### Data Classes

**ReviewDecision (Enum)**

```python
class ReviewDecision(Enum):
    APPROVED = "approved"
    REJECTED = "rejected"
    DEFERRED = "deferred"
```

**ApprovalRequest**

```python
@dataclass
class ApprovalRequest:
    task_id: str
    gate_type: str  # "design_review"|"code_review"
    agent_output: Dict[str, Any]  # Full agent output
    quality_report: Dict[str, Any]  # Quality report details
    base_branch: str = "main"
```

**ApprovalResponse**

```python
@dataclass
class ApprovalResponse:
    decision: ReviewDecision
    reviewer: str  # Name/ID of reviewer
    timestamp: str  # ISO 8601 timestamp
    justification: str  # Reason for decision
    review_branch: Optional[str] = None
    merge_commit: Optional[str] = None
```

### Example Usage

```python
from asp.approval.base import ApprovalService, ApprovalRequest, ApprovalResponse, ReviewDecision

class MyApprovalService(ApprovalService):
    def request_approval(self, request: ApprovalRequest) -> ApprovalResponse:
        # Implementation: GitHub PR, CLI prompt, web UI, etc.
        decision = ReviewDecision.APPROVED
        return ApprovalResponse(
            decision=decision,
            reviewer="alice@example.com",
            timestamp=datetime.now().isoformat(),
            justification="Design quality is acceptable for MVP"
        )

# Use in orchestrator
orchestrator = TSPOrchestrator(
    approval_service=MyApprovalService()
)
```

---

## Telemetry

Module: `asp.telemetry.telemetry`

### Decorators

#### @track_agent_cost

Decorator to track agent execution costs and metrics.

```python
@track_agent_cost(
    agent_role: str,
    task_id_param: str = "task_id",
    llm_model: Optional[str] = None,
    llm_provider: Optional[str] = None,
    agent_version: Optional[str] = None
)
```

Automatically tracks:
- Execution latency (milliseconds)
- Token usage (input/output tokens)
- API costs (USD)

Logs to both Langfuse and SQLite database.

**Example:**

```python
@track_agent_cost(
    agent_role="Planning",
    task_id_param="input_data.task_id",
    llm_model="claude-sonnet-4-20250514",
    llm_provider="anthropic",
    agent_version="1.0.0"
)
def execute(self, input_data: TaskRequirements) -> ProjectPlan:
    # Agent logic here
    return project_plan
```

**Parameters:**
- `agent_role`: Agent role (Planning, Design, Code, Test, etc.)
- `task_id_param`: Parameter name containing task_id (supports dot notation)
- `llm_model`: Optional LLM model name
- `llm_provider`: Optional LLM provider name
- `agent_version`: Optional agent version

**Dot Notation Support:**

```python
@track_agent_cost(
    agent_role="Planning",
    task_id_param="input_data.task_id"  # Extract from input_data.task_id
)
```

#### @log_defect

Decorator to log defects when detected and fixed.

```python
@log_defect(
    defect_type: str,
    severity: str,
    phase_injected: str,
    phase_removed: str,
    task_id_param: str = "task_id"
)
```

**Example:**

```python
@log_defect(
    defect_type="6_Conventional_Code_Bug",
    severity="High",
    phase_injected="Code",
    phase_removed="Review"
)
def fix_logic_error(task_id: str, error_description: str) -> dict:
    # Fix logic here
    return {"fixed": True}
```

---

### Functions

#### insert_agent_cost

Insert agent cost record into database.

```python
def insert_agent_cost(
    task_id: str,
    agent_role: str,
    metric_type: str,
    metric_value: float,
    metric_unit: str,
    subtask_id: Optional[str] = None,
    project_id: Optional[str] = None,
    agent_version: Optional[str] = None,
    agent_iteration: int = 1,
    llm_model: Optional[str] = None,
    llm_provider: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
    db_path: Optional[Path] = None
) -> int:
    """
    Insert agent cost record.

    Args:
        task_id: Unique task identifier
        agent_role: Agent role (Planning, Design, etc.)
        metric_type: Latency|Tokens_In|Tokens_Out|API_Cost
        metric_value: Numeric value
        metric_unit: ms|tokens|USD|MB|count
        ...

    Returns:
        ID of inserted record
    """
```

**Example:**

```python
from asp.telemetry import insert_agent_cost

record_id = insert_agent_cost(
    task_id="TASK-001",
    agent_role="Planning",
    metric_type="Latency",
    metric_value=2500.0,
    metric_unit="ms",
    llm_model="claude-sonnet-4",
    llm_provider="anthropic"
)
```

#### insert_defect

Insert defect record into database.

```python
def insert_defect(
    task_id: str,
    defect_type: str,
    severity: str,
    phase_injected: str,
    phase_removed: str,
    description: str,
    project_id: Optional[str] = None,
    component_path: Optional[str] = None,
    function_name: Optional[str] = None,
    line_number: Optional[int] = None,
    root_cause: Optional[str] = None,
    resolution_notes: Optional[str] = None,
    flagged_by_agent: bool = False,
    metadata: Optional[Dict[str, Any]] = None,
    db_path: Optional[Path] = None
) -> str:
    """
    Insert defect record.

    Args:
        task_id: Task identifier
        defect_type: AI Defect Taxonomy type
        severity: Low|Medium|High|Critical
        phase_injected: Phase where defect was introduced
        phase_removed: Phase where defect was detected
        description: Defect description
        ...

    Returns:
        defect_id of inserted record
    """
```

#### log_agent_metric

Manually log an agent metric (non-decorator usage).

```python
def log_agent_metric(
    task_id: str,
    agent_role: str,
    metric_type: str,
    metric_value: float,
    metric_unit: str,
    **kwargs
):
    """
    Manually log metric without decorator.

    Example:
        log_agent_metric(
            task_id="TASK-001",
            agent_role="Planning",
            metric_type="Tokens_In",
            metric_value=1500,
            metric_unit="tokens",
            llm_model="claude-sonnet-4"
        )
    """
```

#### log_defect_manual

Manually log a defect (non-decorator usage).

```python
def log_defect_manual(
    task_id: str,
    defect_type: str,
    severity: str,
    phase_injected: str,
    phase_removed: str,
    description: str,
    **kwargs
):
    """
    Manually log defect without decorator.

    Example:
        log_defect_manual(
            task_id="TASK-001",
            defect_type="6_Conventional_Code_Bug",
            severity="High",
            phase_injected="Code",
            phase_removed="Review",
            description="SQL injection vulnerability",
            component_path="src/api/users.py",
            line_number=45
        )
    """
```

---

### Database Schema

**agent_cost_vector Table:**

```sql
CREATE TABLE agent_cost_vector (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    task_id TEXT NOT NULL,
    subtask_id TEXT,
    project_id TEXT,
    agent_role TEXT NOT NULL,
    agent_version TEXT,
    agent_iteration INTEGER DEFAULT 1,
    metric_type TEXT NOT NULL,
    metric_value REAL NOT NULL,
    metric_unit TEXT NOT NULL,
    llm_model TEXT,
    llm_provider TEXT,
    metadata TEXT
);
```

**defect_log Table:**

```sql
CREATE TABLE defect_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    defect_id TEXT UNIQUE NOT NULL,
    created_at TEXT NOT NULL,
    task_id TEXT NOT NULL,
    project_id TEXT,
    defect_type TEXT NOT NULL,
    severity TEXT NOT NULL,
    description TEXT NOT NULL,
    phase_injected TEXT NOT NULL,
    phase_removed TEXT NOT NULL,
    component_path TEXT,
    function_name TEXT,
    line_number INTEGER,
    root_cause TEXT,
    resolution_notes TEXT,
    flagged_by_agent INTEGER DEFAULT 0,
    metadata TEXT
);
```

---

## Utilities

### Semantic Complexity

Module: `asp.utils.semantic_complexity`

#### calculate_semantic_complexity

Calculate Semantic Complexity using C1 formula.

```python
def calculate_semantic_complexity(factors: ComplexityFactors) -> int:
    """
    Calculate complexity score (1-100+).

    Formula:
        Semantic_Complexity = (
            (2 × API_Interactions) +
            (5 × Data_Transformations) +
            (3 × Logical_Branches) +
            (4 × Code_Entities_Modified)
        ) × Novelty_Multiplier

    Args:
        factors: ComplexityFactors with all inputs

    Returns:
        Complexity score (rounded integer)

    Example:
        factors = ComplexityFactors(
            api_interactions=2,
            data_transformations=3,
            logical_branches=1,
            code_entities_modified=2,
            novelty_multiplier=1.0
        )
        score = calculate_semantic_complexity(factors)  # Returns 19
    """
```

#### get_complexity_band

Get human-readable complexity band.

```python
def get_complexity_band(complexity: int) -> str:
    """
    Get complexity band for score.

    Bands:
        1-10: Trivial
        11-30: Simple
        31-60: Moderate
        61-80: Complex
        81+: Very Complex

    Example:
        band = get_complexity_band(45)  # Returns "Moderate"
    """
```

#### ComplexityFactors

Input model for complexity calculation.

```python
class ComplexityFactors(BaseModel):
    api_interactions: int  # 0-10
    data_transformations: int  # 0-10
    logical_branches: int  # 0-10
    code_entities_modified: int  # 0-10
    novelty_multiplier: float  # 1.0-2.0
```

---

### Artifact I/O

Module: `asp.utils.artifact_io`

#### write_artifact_json

Write artifact data as JSON file.

```python
def write_artifact_json(
    task_id: str,
    artifact_type: str,
    data: Any,
    base_path: Optional[str] = None
) -> Path:
    """
    Write artifact as JSON.

    Creates: artifacts/{task_id}/{artifact_type}.json

    Args:
        task_id: Task identifier (e.g., "JWT-AUTH-001")
        artifact_type: Artifact type (e.g., "plan", "design")
        data: Pydantic model or dict to write
        base_path: Optional base path (default: current directory)

    Returns:
        Path to created JSON file

    Raises:
        ArtifactIOError: If writing fails

    Example:
        path = write_artifact_json("TASK-001", "plan", project_plan)
        # Creates: artifacts/TASK-001/plan.json
    """
```

#### write_artifact_markdown

Write artifact data as Markdown file.

```python
def write_artifact_markdown(
    task_id: str,
    artifact_type: str,
    markdown_content: str,
    base_path: Optional[str] = None
) -> Path:
    """
    Write artifact as Markdown.

    Creates: artifacts/{task_id}/{artifact_type}.md

    Example:
        path = write_artifact_markdown(
            "TASK-001",
            "plan",
            "# Project Plan\n..."
        )
        # Creates: artifacts/TASK-001/plan.md
    """
```

#### read_artifact_json

Read artifact data from JSON file.

```python
def read_artifact_json(
    task_id: str,
    artifact_type: str,
    base_path: Optional[str] = None
) -> dict[str, Any]:
    """
    Read artifact from JSON file.

    Reads: artifacts/{task_id}/{artifact_type}.json

    Returns:
        Dictionary containing artifact data

    Raises:
        ArtifactIOError: If file doesn't exist or reading fails

    Example:
        data = read_artifact_json("TASK-001", "plan")
        plan = ProjectPlan(**data)
    """
```

#### write_generated_file

Write a generated code file to disk.

```python
def write_generated_file(
    task_id: str,
    file: GeneratedFile,
    base_path: Optional[str] = None
) -> Path:
    """
    Write generated code file.

    Creates: {base_path}/{file.file_path}
    Automatically creates parent directories.

    Args:
        task_id: Task identifier (for logging)
        file: GeneratedFile with file_path and content
        base_path: Optional base path (default: current directory)

    Returns:
        Path to created file

    Example:
        from asp.models.code import GeneratedFile

        file = GeneratedFile(
            file_path="src/api/auth.py",
            content="from fastapi import...",
            file_type="source",
            description="Authentication endpoints"
        )
        path = write_generated_file("TASK-001", file)
        # Creates: src/api/auth.py
    """
```

#### artifact_exists

Check if artifact file exists.

```python
def artifact_exists(
    task_id: str,
    artifact_type: str,
    format: str = "json",
    base_path: Optional[str] = None
) -> bool:
    """
    Check if artifact exists.

    Args:
        task_id: Task identifier
        artifact_type: Artifact type
        format: "json" or "md"
        base_path: Optional base path

    Returns:
        True if artifact exists, False otherwise

    Example:
        if artifact_exists("TASK-001", "plan", "json"):
            plan_data = read_artifact_json("TASK-001", "plan")
    """
```

---

### Git Utilities

Module: `asp.utils.git_utils`

#### is_git_repository

Check if current directory is a Git repository.

```python
def is_git_repository(path: Optional[Path] = None) -> bool:
    """
    Check if directory is a Git repository.

    Args:
        path: Optional directory path (default: current directory)

    Returns:
        True if Git repository, False otherwise
    """
```

#### git_commit_artifact

Commit artifact files to Git repository.

```python
def git_commit_artifact(
    task_id: str,
    agent_name: str,
    artifact_files: list[str],
    branch: Optional[str] = None
) -> str:
    """
    Commit artifact files to Git.

    Args:
        task_id: Task identifier
        agent_name: Name of agent creating artifacts
        artifact_files: List of file paths to commit
        branch: Optional branch name (default: current branch)

    Returns:
        Commit hash

    Raises:
        GitError: If commit fails

    Example:
        commit_hash = git_commit_artifact(
            task_id="TASK-001",
            agent_name="Planning Agent",
            artifact_files=[
                "artifacts/TASK-001/plan.json",
                "artifacts/TASK-001/plan.md"
            ]
        )
    """
```

---

## Configuration

### Environment Variables

The ASP Platform uses environment variables for configuration.

#### Telemetry

- `LANGFUSE_PUBLIC_KEY`: Langfuse public API key
- `LANGFUSE_SECRET_KEY`: Langfuse secret API key
- `LANGFUSE_HOST`: Langfuse host URL (default: https://cloud.langfuse.com)

#### Agent Configuration

- `ASP_DESIGN_AGENT_USE_MARKDOWN`: Enable Markdown output for Design Agent (true/false, default: false)
- `ASP_MULTI_STAGE_CODE_GEN`: Enable multi-stage code generation (true/false, default: false)

#### LLM Configuration

- `ANTHROPIC_API_KEY`: Anthropic API key for Claude models
- `OPENAI_API_KEY`: OpenAI API key (if using OpenAI models)

#### Database

- `ASP_DB_PATH`: Path to SQLite database (default: data/asp_telemetry.db)

#### Example .env File

```bash
# Telemetry
LANGFUSE_PUBLIC_KEY=pk-lf-xxx
LANGFUSE_SECRET_KEY=sk-lf-xxx
LANGFUSE_HOST=https://cloud.langfuse.com

# LLM
ANTHROPIC_API_KEY=sk-ant-xxx

# Agent Configuration
ASP_DESIGN_AGENT_USE_MARKDOWN=true
ASP_MULTI_STAGE_CODE_GEN=true

# Database
ASP_DB_PATH=data/asp_telemetry.db
```

---

### Database Path Configuration

Default database path: `data/asp_telemetry.db`

Override via:
1. Environment variable: `ASP_DB_PATH`
2. Constructor parameter: `db_path` in agent/orchestrator initialization

```python
# Option 1: Environment variable
os.environ["ASP_DB_PATH"] = "/path/to/custom.db"
agent = PlanningAgent()

# Option 2: Constructor parameter
from pathlib import Path
agent = PlanningAgent(db_path=Path("/path/to/custom.db"))
```

---

## Complete Example

End-to-end example using the TSP Orchestrator:

```python
from asp.models.planning import TaskRequirements
from asp.orchestrators.tsp_orchestrator import TSPOrchestrator

# Define requirements
requirements = TaskRequirements(
    task_id="DEMO-001",
    project_id="ASP-DEMO",
    description="Build user authentication system with JWT",
    requirements="""
        - User registration with email/password
        - Login endpoint with JWT token generation
        - Token validation middleware
        - Password hashing with bcrypt
        - Input validation and error handling
        - Rate limiting on auth endpoints
    """,
    context_files=[]
)

# Initialize orchestrator
orchestrator = TSPOrchestrator()

# Execute complete pipeline
result = orchestrator.execute(
    requirements=requirements,
    design_constraints="Use FastAPI framework and PostgreSQL database",
    coding_standards="Follow PEP 8. Use type hints. Include docstrings.",
    hitl_approver=lambda gate, report: True  # Auto-approve for demo
)

# Access results
print(f"Overall Status: {result.overall_status}")
print(f"Semantic Units: {len(result.project_plan.semantic_units)}")
print(f"Components: {len(result.design_specification.component_logic)}")
print(f"Files Generated: {result.generated_code.total_files}")
print(f"LOC: {result.generated_code.total_lines_of_code}")
print(f"Tests: {result.test_report.test_summary['passed']}/
         {result.test_report.test_summary['total_tests']}")
print(f"Defects: {len(result.test_report.defects_found)}")
print(f"Duration: {result.total_duration_seconds:.1f}s")

# Access artifacts
project_plan = result.project_plan
design_spec = result.design_specification
generated_code = result.generated_code

# Iterate through generated files
for file in generated_code.files:
    print(f"  {file.file_path} ({file.file_type}): {len(file.content)} chars")

# Check quality metrics
if result.test_report.test_status == "PASS":
    print("All tests passed!")
else:
    print(f"Test failures: {result.test_report.test_summary['failed']}")
    for defect in result.test_report.defects_found:
        print(f"  - {defect.defect_type}: {defect.description}")
```

---

## Error Handling

### Exception Hierarchy

```
Exception
├── AgentExecutionError  # Base exception for agent failures
├── QualityGateFailure  # Quality gate failed without HITL override
├── MaxIterationsExceeded  # Correction loops exceeded limits
└── ArtifactIOError  # Artifact I/O failures
```

### Example Error Handling

```python
from asp.agents.base_agent import AgentExecutionError
from asp.orchestrators.tsp_orchestrator import QualityGateFailure, MaxIterationsExceeded

try:
    result = orchestrator.execute(requirements)
except QualityGateFailure as e:
    print(f"Quality gate failed: {e}")
    # Handle quality gate failure (e.g., request manual approval)
except MaxIterationsExceeded as e:
    print(f"Too many correction iterations: {e}")
    # Handle iteration limit (e.g., mark task for manual review)
except AgentExecutionError as e:
    print(f"Agent execution failed: {e}")
    # Handle agent failure (e.g., retry, log, alert)
except Exception as e:
    print(f"Unexpected error: {e}")
    # Handle unexpected errors
```

---

## Related Documentation

- **Architecture:** `docs/Architecture.md`
- **PSP Documentation:** `docs/PSPdoc.md`
- **PRD:** `docs/PRD_v3.md`
- **Development Guide:** `docs/Development_Guide.md`
- **Testing Guide:** `docs/Testing_Guide.md`

---

**Document Version:** 1.0.0
**Generated:** November 26, 2025
**Total Lines:** ~2,800
