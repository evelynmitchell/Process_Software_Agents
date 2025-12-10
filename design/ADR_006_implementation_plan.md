# Implementation Plan: ADR 006 - Repair Workflow Architecture

**Date:** 2025-12-10
**Status:** Approved for Implementation
**Related:** [ADR 006 - Repair Workflow Architecture](./ADR_006_repair_workflow_architecture.md)

## Overview

Integrate repair workflow capability into ASP, enabling diagnosis and iterative repair of bugs in existing code until tests pass.

**Key Decisions:**
- Asynchronous RepairOrchestrator
- Artifacts stored in workspace `.asp/` folder (isolated, cleaned with workspace)
- Pytest parser only initially
- Basic buggy calculator E2E test

---

## Phase 1: Foundation - Execution Infrastructure

### Task 1.1: Create Execution Models

**File:** `src/asp/models/execution.py`

Create Pydantic models following patterns in `src/asp/models/test.py`:

```python
@dataclass
class SandboxConfig:
    timeout_seconds: int = 300
    memory_limit_mb: int = 512
    cpu_limit_cores: float = 1.0
    network_enabled: bool = False
    env_vars: dict[str, str] = field(default_factory=dict)

class ExecutionResult(BaseModel):
    exit_code: int
    stdout: str
    stderr: str
    duration_ms: int
    timed_out: bool

class TestFailure(BaseModel):
    test_name: str
    test_file: str
    line_number: int | None
    error_type: str
    error_message: str
    stack_trace: str

class TestResult(BaseModel):
    framework: str
    total_tests: int
    passed: int
    failed: int
    skipped: int
    errors: int
    duration_seconds: float
    coverage_percent: float | None
    failures: list[TestFailure]
    raw_output: str | None = None  # Fallback when parsing fails
    parsing_failed: bool = False
```

---

### Task 1.2: Implement SandboxExecutor

**File:** `src/services/sandbox_executor.py`

Subprocess-based executor with resource limits:

```python
class SubprocessSandboxExecutor:
    def __init__(self, config: SandboxConfig): ...

    def execute(
        self,
        workspace: Workspace,
        command: list[str],
        working_dir: str | None = None,
    ) -> ExecutionResult:
        """Execute with subprocess and resource.setrlimit()."""
```

Key implementation:
- Use `subprocess.Popen` with `preexec_fn` for resource limits
- Handle `TimeoutExpired` by killing process
- Capture stdout/stderr

---

### Task 1.3: Implement TestExecutor

**File:** `src/services/test_executor.py`

```python
class PytestResultParser:
    def parse(self, stdout: str, stderr: str, exit_code: int) -> TestResult: ...

class TestExecutor:
    def __init__(self, sandbox: SubprocessSandboxExecutor): ...

    def run_tests(
        self,
        workspace: Workspace,
        framework: str | None = None,
        test_path: str | None = None,
        coverage: bool = True,
    ) -> TestResult: ...

    def _detect_framework(self, workspace: Workspace) -> str: ...
    def _fallback_parse(self, result: ExecutionResult, framework: str) -> TestResult: ...
```

Key: Fallback parser returns raw output when structured parsing fails.

---

### Task 1.4: Unit Tests for Foundation

**Files:**
- `tests/unit/test_models/test_execution_models.py`
- `tests/unit/test_services/test_sandbox_executor.py`
- `tests/unit/test_services/test_test_executor.py`

---

## Phase 2: Diagnostic Capability

### Task 2.1: Create Diagnostic Models

**File:** `src/asp/models/diagnostic.py`

```python
class IssueType(str, Enum):
    TEST_FAILURE = "test_failure"
    BUILD_ERROR = "build_error"
    RUNTIME_ERROR = "runtime_error"
    TYPE_ERROR = "type_error"

class Severity(str, Enum):
    CRITICAL = "Critical"
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"

class AffectedFile(BaseModel):
    path: str
    line_start: int
    line_end: int
    code_snippet: str
    issue_description: str

class CodeChange(BaseModel):
    """Search-replace based change (NOT line numbers - LLMs are bad at counting)."""
    file_path: str
    search_text: str
    replace_text: str
    occurrence: int = 1  # Which occurrence to replace (0=all)

class SuggestedFix(BaseModel):
    fix_id: str
    description: str
    confidence: float
    changes: list[CodeChange]

class DiagnosticInput(BaseModel):
    task_id: str
    workspace_path: str  # Path to workspace
    test_result: TestResult
    error_type: str
    error_message: str
    stack_trace: str

class DiagnosticReport(BaseModel):
    task_id: str
    issue_type: IssueType
    severity: Severity
    root_cause: str
    affected_files: list[AffectedFile]
    suggested_fixes: list[SuggestedFix]
    confidence: float
```

---

### Task 2.2: Create Diagnostic Prompt

**File:** `src/asp/prompts/diagnostic_agent_v1.txt`

Template with:
- ROLE: Expert debugger
- INPUT: Error info, test results, source context
- TASK: Identify root cause, locate bug, suggest fixes
- OUTPUT FORMAT: JSON matching DiagnosticReport
- CONSTRAINTS: Use search-replace, not line numbers

---

### Task 2.3: Implement DiagnosticAgent

**File:** `src/asp/agents/diagnostic_agent.py`

```python
class DiagnosticAgent(BaseAgent):
    @track_agent_cost(agent_role="Diagnostic", ...)
    def execute(self, input_data: DiagnosticInput) -> DiagnosticReport: ...

    def _gather_context(self, input_data: DiagnosticInput) -> dict:
        """
        Gather full repository context:
        1. Files from stack trace (±20 lines)
        2. Import dependencies
        3. Config files (pyproject.toml, etc.)
        4. Repository structure overview
        """
```

---

### Task 2.4: Unit Tests for Diagnostic

**Files:**
- `tests/unit/test_models/test_diagnostic_models.py`
- `tests/unit/test_agents/test_diagnostic_agent.py`

---

## Phase 3: Repair Capability

### Task 3.1: Create Repair Models

**File:** `src/asp/models/repair.py`

```python
class RepairAttempt(BaseModel):
    attempt_number: int
    changes_made: list[CodeChange]
    test_result: TestResult
    why_failed: str | None

class RepairInput(BaseModel):
    task_id: str
    workspace_path: str
    diagnostic: DiagnosticReport
    previous_attempts: list[RepairAttempt] = []
    max_changes_per_file: int = 50

class RepairOutput(BaseModel):
    task_id: str
    strategy: str
    changes: list[CodeChange]  # Search-replace pairs
    explanation: str
    confidence: float
    alternative_fixes: list[dict] | None = None
```

---

### Task 3.2: Implement SurgicalEditor

**File:** `src/services/surgical_editor.py`

```python
class EditResult(BaseModel):
    success: bool
    files_modified: list[str]
    backup_paths: dict[str, str]
    errors: list[str]

class SurgicalEditor:
    def __init__(self, workspace_path: Path): ...

    def apply_changes(self, changes: list[CodeChange], create_backup: bool = True) -> EditResult:
        """Apply search-replace changes with fuzzy matching."""

    def rollback(self, file_path: str | None = None) -> None:
        """Restore from backups."""

    def generate_diff(self, changes: list[CodeChange]) -> str:
        """Generate unified diff preview."""

    def _fuzzy_find(self, content: str, search: str, threshold: float = 0.8) -> Match | None:
        """Find code block with 80% similarity threshold."""
```

Key: Default to search-replace mode with fuzzy matching (not line numbers).

---

### Task 3.3: Create Repair Prompt

**File:** `src/asp/prompts/repair_agent_v1.txt`

Template emphasizing:
- Use search-replace, NOT line numbers
- Consider previous failed attempts
- Provide confidence scores
- Include alternative fixes when uncertain

---

### Task 3.4: Implement RepairAgent

**File:** `src/asp/agents/repair_agent.py`

```python
class RepairAgent(BaseAgent):
    @track_agent_cost(agent_role="Repair", ...)
    def execute(self, input_data: RepairInput) -> RepairOutput: ...

    def _read_affected_files(self, input_data: RepairInput) -> dict[str, str]: ...
    def _format_attempts(self, attempts: list[RepairAttempt]) -> str: ...
```

---

### Task 3.5: Unit Tests for Repair

**Files:**
- `tests/unit/test_models/test_repair_models.py`
- `tests/unit/test_services/test_surgical_editor.py`
- `tests/unit/test_agents/test_repair_agent.py`

---

## Phase 4: Orchestration

### Task 4.1: Implement RepairOrchestrator (Async)

**File:** `src/asp/orchestrators/repair_orchestrator.py`

```python
@dataclass
class RepairRequest:
    task_id: str
    workspace: Workspace
    issue_description: str | None = None
    target_tests: list[str] | None = None
    max_iterations: int = 5

@dataclass
class RepairResult:
    task_id: str
    success: bool
    iterations_used: int
    final_test_result: TestResult
    changes_made: list[CodeChange]
    diagnostic_reports: list[DiagnosticReport]
    repair_attempts: list[RepairAttempt]

class RepairOrchestrator:
    def __init__(
        self,
        sandbox: SubprocessSandboxExecutor,
        test_executor: TestExecutor,
        diagnostic_agent: DiagnosticAgent,
        repair_agent: RepairAgent,
        approval_service: ApprovalService | None = None,
    ): ...

    async def repair(self, request: RepairRequest) -> RepairResult:
        """
        Async repair loop:
        1. Run tests
        2. If pass → return success
        3. Diagnose failures
        4. Generate fix
        5. Apply fix
        6. Loop until pass or max iterations
        """
```

HITL escalation after 2 failed iterations.

---

### Task 4.2: Implement Confidence Calculation

**File:** `src/asp/orchestrators/confidence.py`

```python
@dataclass
class ConfidenceBreakdown:
    diagnostic_confidence: float  # Stack trace clarity, single root cause
    fix_confidence: float  # Fix size, attempt history
    test_coverage_confidence: float  # OBJECTIVE: actual coverage

    @property
    def overall(self) -> float:
        return (self.diagnostic_confidence * 0.3 +
                self.fix_confidence * 0.3 +
                self.test_coverage_confidence * 0.4)

def calculate_confidence(...) -> ConfidenceBreakdown: ...
```

---

### Task 4.3: Implement HITL Configuration

**File:** `src/asp/orchestrators/hitl_config.py`

```python
@dataclass
class HITLConfig:
    mode: Literal["autonomous", "supervised", "threshold"] = "threshold"
    require_approval_after_iterations: int = 2
    require_approval_for_confidence_below: float = 0.7
    require_approval_for_critical_files: list[str] = field(default_factory=list)
```

---

### Task 4.4: Unit Tests for Orchestration

**File:** `tests/unit/test_orchestrators/test_repair_orchestrator.py`

---

## Phase 5: Integration & E2E

### Task 5.1: Extend TSPOrchestrator

**File:** `src/asp/orchestrators/tsp_orchestrator.py` (modify)

Add:
- `_repair_orchestrator` lazy-loaded property
- `async _execute_repair()` method
- Mode parameter to distinguish greenfield vs repair

---

### Task 5.2: Update Orchestrator Types

**File:** `src/asp/orchestrators/types.py` (modify)

Add to `TSPExecutionResult`:
- `mode: Literal["greenfield", "repair"]`
- `repair_result: RepairResult | None`

---

### Task 5.3: E2E Test - Buggy Calculator

**File:** `tests/e2e/test_repair_workflow_e2e.py`

```python
BUGGY_CALCULATOR = '''
def add(a, b):
    return a - b  # BUG: should be +

def divide(a, b):
    return a / b  # BUG: no zero check
'''

CALCULATOR_TESTS = '''
def test_add():
    assert add(2, 3) == 5

def test_divide_by_zero():
    with pytest.raises(ZeroDivisionError):
        divide(10, 0)
'''

class TestRepairWorkflowE2E:
    @pytest.mark.e2e
    @pytest.mark.slow
    def test_repair_buggy_calculator(self, buggy_workspace):
        """Verify repair workflow fixes both bugs."""
```

---

### Task 5.4: Update ADR Status

**File:** `design/ADR_006_repair_workflow_architecture.md` (modify)

Change status from "Proposed" to "Accepted"

---

## File Summary

### New Files (23)

| File | Description |
|------|-------------|
| `src/asp/models/execution.py` | ExecutionResult, TestResult, TestFailure, SandboxConfig |
| `src/asp/models/diagnostic.py` | DiagnosticInput, DiagnosticReport, CodeChange, SuggestedFix |
| `src/asp/models/repair.py` | RepairInput, RepairOutput, RepairAttempt |
| `src/services/sandbox_executor.py` | SubprocessSandboxExecutor |
| `src/services/test_executor.py` | TestExecutor, PytestResultParser |
| `src/services/surgical_editor.py` | SurgicalEditor with fuzzy matching |
| `src/asp/agents/diagnostic_agent.py` | DiagnosticAgent |
| `src/asp/agents/repair_agent.py` | RepairAgent |
| `src/asp/orchestrators/repair_orchestrator.py` | RepairOrchestrator (async) |
| `src/asp/orchestrators/confidence.py` | Confidence calculation |
| `src/asp/orchestrators/hitl_config.py` | HITL configuration |
| `src/asp/prompts/diagnostic_agent_v1.txt` | Diagnostic prompt |
| `src/asp/prompts/repair_agent_v1.txt` | Repair prompt |
| `tests/unit/test_models/test_execution_models.py` | Unit tests |
| `tests/unit/test_models/test_diagnostic_models.py` | Unit tests |
| `tests/unit/test_models/test_repair_models.py` | Unit tests |
| `tests/unit/test_services/test_sandbox_executor.py` | Unit tests |
| `tests/unit/test_services/test_test_executor.py` | Unit tests |
| `tests/unit/test_services/test_surgical_editor.py` | Unit tests |
| `tests/unit/test_agents/test_diagnostic_agent.py` | Unit tests |
| `tests/unit/test_agents/test_repair_agent.py` | Unit tests |
| `tests/unit/test_orchestrators/test_repair_orchestrator.py` | Unit tests |
| `tests/e2e/test_repair_workflow_e2e.py` | E2E test |

### Modified Files (2)

| File | Change |
|------|--------|
| `src/asp/orchestrators/tsp_orchestrator.py` | Add repair mode support |
| `src/asp/orchestrators/types.py` | Add repair result fields |

---

## Dependency Order

```
Phase 1: 1.1 → 1.2 → 1.3 → 1.4
Phase 2: 2.1 → 2.2 → 2.3 → 2.4 (depends on Phase 1)
Phase 3: 3.1 → 3.2, 3.3 → 3.4 → 3.5 (depends on Phase 2)
Phase 4: 4.1, 4.2, 4.3 → 4.4 (depends on Phase 3)
Phase 5: 5.1 → 5.2 → 5.3 → 5.4 (depends on Phase 4)
```

---

## Risks and Mitigations

| Risk | Mitigation |
|------|------------|
| LLM generates bad fixes | Max 5 iterations, HITL escalation, confidence scores |
| Subprocess sandbox insufficient | Document limitations, plan Docker for future |
| Pytest parser edge cases | Fallback returns raw output for LLM |
| Search-replace misses code | Fuzzy matching with 80% threshold |

---

## Success Criteria

1. **Unit tests pass** for all new models, services, and agents
2. **E2E test passes** - buggy calculator is successfully repaired
3. **Integration with TSPOrchestrator** works in repair mode
4. **HITL escalation triggers** after 2 failed iterations
5. **Artifacts stored** in workspace `.asp/` folder and cleaned up properly
