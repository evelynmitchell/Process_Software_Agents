# ADR 006: Repair Workflow Architecture

**Status:** Proposed
**Date:** 2025-12-10
**Session:** 20251210.5
**Deciders:** User, Claude

## Context and Problem Statement

The ASP (Agentic Software Process) platform is currently optimized for **greenfield code generation** - creating new code from scratch through a sequential pipeline:

```
Planning → Design → Code Generation → Code Review → Testing → Postmortem
```

However, the platform **cannot repair existing codebases**. This is a critical gap because most real-world software engineering involves:
- Fixing bugs in existing code
- Addressing security vulnerabilities
- Resolving failing tests
- Refactoring problematic code

**Core Question:** What architectural components are needed to enable ASP to diagnose issues in existing code and iteratively repair them until tests pass?

### Current Limitations

| Capability | Greenfield | Repair Needed | Current Status |
|------------|------------|---------------|----------------|
| Generate new code | ✅ | N/A | Works well |
| Read existing code | N/A | ✅ | Partial (LLM analysis only) |
| Execute code/tests | N/A | **Critical** | ❌ Missing |
| Surgical file edits | N/A | **Critical** | ❌ Missing |
| Parse real errors | N/A | **Critical** | ❌ Missing |
| Iterate until fixed | N/A | **Critical** | ❌ Missing |

### Gap Analysis

The gap between greenfield and repair is **NOT primarily sandboxing** (workspace isolation already exists). The real gaps are:

1. **No Test Execution** - Test Agent simulates results via LLM, doesn't run pytest/unittest
2. **No Surgical Editing** - Must regenerate entire files, can't patch specific lines
3. **No Runtime Diagnostics** - Cannot execute code to capture stack traces
4. **No Iteration Loop** - No feedback cycle based on actual test results

## Decision Drivers

1. **Safety:** Code execution must be sandboxed to prevent damage to host system
2. **Language Agnostic:** Support Python, JavaScript/TypeScript, Go, Rust, etc.
3. **Incremental:** Build on existing workspace isolation (ADR-001)
4. **Observable:** All execution traces captured in Langfuse
5. **Iterative:** Support repair loops until tests pass (with max iterations)
6. **Minimal Invasiveness:** Surgical edits preferred over full file regeneration

## Proposed Architecture

### High-Level Repair Workflow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         REPAIR WORKFLOW                                      │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐              │
│  │  Clone   │───▶│ Diagnose │───▶│  Repair  │───▶│ Validate │              │
│  │   Repo   │    │  Issue   │    │   Code   │    │   Fix    │              │
│  └──────────┘    └──────────┘    └──────────┘    └────┬─────┘              │
│                        ▲                              │                      │
│                        │         ┌────────────────────┘                      │
│                        │         ▼                                           │
│                        │    ┌─────────┐                                      │
│                        │    │  Tests  │                                      │
│                        │    │  Pass?  │                                      │
│                        │    └────┬────┘                                      │
│                        │         │                                           │
│                        │    No   │   Yes                                     │
│                        └─────────┘    │                                      │
│                                       ▼                                      │
│                                 ┌──────────┐                                 │
│                                 │  Commit  │                                 │
│                                 │   & PR   │                                 │
│                                 └──────────┘                                 │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### New Components Required

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         NEW COMPONENTS                                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌─────────────────────┐  ┌─────────────────────┐  ┌─────────────────────┐  │
│  │   SandboxExecutor   │  │   DiagnosticAgent   │  │    SurgicalEditor   │  │
│  │                     │  │                     │  │                     │  │
│  │  • Run tests        │  │  • Parse errors     │  │  • Generate patches │  │
│  │  • Capture output   │  │  • Locate bugs      │  │  • Apply diffs      │  │
│  │  • Resource limits  │  │  • Root cause       │  │  • Merge conflicts  │  │
│  │  • Timeout control  │  │  • Suggest fixes    │  │  • Rollback support │  │
│  └─────────────────────┘  └─────────────────────┘  └─────────────────────┘  │
│                                                                              │
│  ┌─────────────────────┐  ┌─────────────────────┐  ┌─────────────────────┐  │
│  │   RepairAgent       │  │  RepairOrchestrator │  │   TestExecutor      │  │
│  │                     │  │                     │  │   (Real)            │  │
│  │  • Generate fixes   │  │  • Coordinate loop  │  │                     │  │
│  │  • Multiple strats  │  │  • Quality gates    │  │  • pytest/unittest  │  │
│  │  • Context-aware    │  │  • Max iterations   │  │  • jest/mocha       │  │
│  │  • Learn from fails │  │  • HITL triggers    │  │  • go test          │  │
│  └─────────────────────┘  └─────────────────────┘  └─────────────────────┘  │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Component Specifications

### 1. SandboxExecutor

**Purpose:** Safely execute arbitrary code and tests within isolated environments.

**Location:** `src/services/sandbox_executor.py`

#### Architecture

```python
@dataclass
class ExecutionResult:
    """Result of code execution in sandbox."""
    exit_code: int
    stdout: str
    stderr: str
    duration_ms: int
    timed_out: bool
    resource_usage: ResourceUsage

@dataclass
class ResourceUsage:
    """Resource consumption metrics."""
    memory_peak_mb: float
    cpu_time_ms: int

@dataclass
class SandboxConfig:
    """Configuration for sandbox execution."""
    timeout_seconds: int = 300  # 5 minutes default
    memory_limit_mb: int = 512
    cpu_limit_cores: float = 1.0
    network_enabled: bool = False  # Disabled by default
    allowed_paths: list[Path] = field(default_factory=list)
    env_vars: dict[str, str] = field(default_factory=dict)
```

#### Implementation Options

**Option A: Docker-based Sandbox (Recommended)**

```python
class DockerSandboxExecutor:
    """Execute code in isolated Docker containers."""

    def __init__(self, config: SandboxConfig):
        self.config = config
        self.client = docker.from_env()

    def execute(
        self,
        workspace: Workspace,
        command: list[str],
        working_dir: str | None = None,
    ) -> ExecutionResult:
        """
        Execute command in sandboxed container.

        Args:
            workspace: Workspace containing code to execute
            command: Command and arguments (e.g., ["pytest", "-v"])
            working_dir: Working directory relative to workspace

        Returns:
            ExecutionResult with stdout, stderr, exit code
        """
        container = self.client.containers.run(
            image=self._get_image_for_workspace(workspace),
            command=command,
            volumes={
                str(workspace.target_repo_path): {
                    'bind': '/workspace',
                    'mode': 'rw'
                }
            },
            working_dir=working_dir or '/workspace',
            mem_limit=f"{self.config.memory_limit_mb}m",
            cpu_period=100000,
            cpu_quota=int(self.config.cpu_limit_cores * 100000),
            network_disabled=not self.config.network_enabled,
            detach=True,
            remove=False,  # Keep for log retrieval
        )

        try:
            result = container.wait(timeout=self.config.timeout_seconds)
            logs = container.logs(stdout=True, stderr=True)
            # ... parse and return ExecutionResult
        finally:
            container.remove(force=True)
```

**Option B: Subprocess with Resource Limits (Lighter weight)**

```python
class SubprocessSandboxExecutor:
    """Execute code using subprocess with resource limits."""

    def execute(
        self,
        workspace: Workspace,
        command: list[str],
        working_dir: str | None = None,
    ) -> ExecutionResult:
        """Execute with subprocess and resource.setrlimit()."""

        def set_limits():
            import resource
            # Memory limit
            resource.setrlimit(
                resource.RLIMIT_AS,
                (self.config.memory_limit_mb * 1024 * 1024,) * 2
            )
            # CPU time limit
            resource.setrlimit(
                resource.RLIMIT_CPU,
                (self.config.timeout_seconds,) * 2
            )

        process = subprocess.Popen(
            command,
            cwd=working_dir or workspace.target_repo_path,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            preexec_fn=set_limits,
            env=self._build_env(workspace),
        )

        try:
            stdout, stderr = process.communicate(
                timeout=self.config.timeout_seconds
            )
            return ExecutionResult(
                exit_code=process.returncode,
                stdout=stdout.decode(),
                stderr=stderr.decode(),
                # ...
            )
        except subprocess.TimeoutExpired:
            process.kill()
            return ExecutionResult(exit_code=-1, timed_out=True, ...)
```

#### Language-Specific Images

```python
SANDBOX_IMAGES = {
    "python": "python:3.11-slim",
    "node": "node:20-slim",
    "typescript": "node:20-slim",
    "go": "golang:1.21-alpine",
    "rust": "rust:1.74-slim",
    "java": "eclipse-temurin:21-jdk",
}

def detect_language(workspace: Workspace) -> str:
    """Detect primary language from workspace files."""
    repo_path = workspace.target_repo_path

    if (repo_path / "pyproject.toml").exists():
        return "python"
    if (repo_path / "package.json").exists():
        if (repo_path / "tsconfig.json").exists():
            return "typescript"
        return "node"
    if (repo_path / "go.mod").exists():
        return "go"
    if (repo_path / "Cargo.toml").exists():
        return "rust"
    if (repo_path / "pom.xml").exists():
        return "java"

    return "python"  # Default fallback
```

---

### 2. TestExecutor (Real)

**Purpose:** Execute actual test frameworks and parse results.

**Location:** `src/services/test_executor.py`

```python
@dataclass
class TestResult:
    """Parsed test execution results."""
    framework: str
    total_tests: int
    passed: int
    failed: int
    skipped: int
    errors: int
    duration_seconds: float
    coverage_percent: float | None
    failures: list[TestFailure]

@dataclass
class TestFailure:
    """Details of a single test failure."""
    test_name: str
    test_file: str
    line_number: int | None
    error_type: str
    error_message: str
    stack_trace: str


class TestExecutor:
    """Execute real test frameworks and parse results."""

    def __init__(self, sandbox: SandboxExecutor):
        self.sandbox = sandbox
        self.parsers = {
            "pytest": PytestResultParser(),
            "unittest": UnittestResultParser(),
            "jest": JestResultParser(),
            "mocha": MochaResultParser(),
            "go": GoTestResultParser(),
            "cargo": CargoTestResultParser(),
        }

    def run_tests(
        self,
        workspace: Workspace,
        framework: str | None = None,
        test_path: str | None = None,
        coverage: bool = True,
    ) -> TestResult:
        """
        Run tests in workspace and return parsed results.

        Args:
            workspace: Workspace containing code and tests
            framework: Test framework (auto-detected if None)
            test_path: Specific test file/directory (all tests if None)
            coverage: Whether to collect coverage data

        Returns:
            TestResult with parsed pass/fail/error details
        """
        framework = framework or self._detect_framework(workspace)
        command = self._build_command(framework, test_path, coverage)

        result = self.sandbox.execute(workspace, command)

        parser = self.parsers.get(framework)

        # FALLBACK MODE: If parser unavailable or fails, return raw output
        # This ensures agents aren't blinded by parser bugs or unsupported frameworks
        if parser is None:
            return self._fallback_parse(result, framework)

        try:
            return parser.parse(result.stdout, result.stderr, result.exit_code)
        except ParserError as e:
            logger.warning(f"Parser failed for {framework}: {e}, using fallback")
            return self._fallback_parse(result, framework)

    def _fallback_parse(
        self,
        result: ExecutionResult,
        framework: str,
    ) -> TestResult:
        """
        Fallback parser when structured parsing fails.

        Returns raw output so agents can still analyze failures.
        Infers pass/fail from exit code only.
        """
        return TestResult(
            framework=framework,
            total_tests=-1,  # Unknown
            passed=-1,
            failed=-1 if result.exit_code != 0 else 0,
            skipped=0,
            errors=1 if result.exit_code != 0 else 0,
            duration_seconds=result.duration_ms / 1000,
            coverage_percent=None,
            failures=[TestFailure(
                test_name="unknown",
                test_file="unknown",
                line_number=None,
                error_type="raw_output",
                error_message=f"Exit code: {result.exit_code}",
                stack_trace=f"STDOUT:\n{result.stdout}\n\nSTDERR:\n{result.stderr}",
            )] if result.exit_code != 0 else [],
            raw_output=result.stdout + "\n" + result.stderr,  # Preserve for LLM analysis
            parsing_failed=True,
        )

    def _detect_framework(self, workspace: Workspace) -> str:
        """Auto-detect test framework from project files."""
        repo = workspace.target_repo_path

        # Python
        if (repo / "pytest.ini").exists() or (repo / "pyproject.toml").exists():
            return "pytest"
        if (repo / "setup.py").exists():
            return "unittest"

        # JavaScript/TypeScript
        pkg_json = repo / "package.json"
        if pkg_json.exists():
            pkg = json.loads(pkg_json.read_text())
            if "jest" in pkg.get("devDependencies", {}):
                return "jest"
            if "mocha" in pkg.get("devDependencies", {}):
                return "mocha"

        # Go
        if (repo / "go.mod").exists():
            return "go"

        # Rust
        if (repo / "Cargo.toml").exists():
            return "cargo"

        return "pytest"  # Default

    def _build_command(
        self,
        framework: str,
        test_path: str | None,
        coverage: bool,
    ) -> list[str]:
        """Build test command for framework."""

        commands = {
            "pytest": [
                "pytest", "-v", "--tb=short",
                *(["--cov=.", "--cov-report=json"] if coverage else []),
                test_path or ".",
            ],
            "jest": [
                "npx", "jest", "--verbose",
                *(["--coverage", "--coverageReporters=json"] if coverage else []),
                *(test_path.split() if test_path else []),
            ],
            "go": [
                "go", "test", "-v",
                *(["-cover"] if coverage else []),
                test_path or "./...",
            ],
            "cargo": [
                "cargo", "test", "--", "--nocapture",
                *(test_path.split() if test_path else []),
            ],
        }

        return commands.get(framework, commands["pytest"])
```

#### Test Result Parsers

```python
class PytestResultParser:
    """Parse pytest output into TestResult."""

    def parse(
        self,
        stdout: str,
        stderr: str,
        exit_code: int
    ) -> TestResult:
        """Parse pytest verbose output."""

        failures = []

        # Parse failure blocks
        failure_pattern = r"FAILED (.+?)::(.+?) - (.+)"
        for match in re.finditer(failure_pattern, stdout):
            file_path, test_name, error_msg = match.groups()
            failures.append(TestFailure(
                test_name=test_name,
                test_file=file_path,
                error_message=error_msg,
                stack_trace=self._extract_traceback(stdout, test_name),
                # ...
            ))

        # Parse summary line: "5 passed, 2 failed, 1 skipped"
        summary = re.search(
            r"(\d+) passed.*?(\d+) failed.*?(\d+) skipped",
            stdout
        )

        return TestResult(
            framework="pytest",
            passed=int(summary.group(1)) if summary else 0,
            failed=int(summary.group(2)) if summary else 0,
            skipped=int(summary.group(3)) if summary else 0,
            failures=failures,
            # ...
        )
```

---

### 3. DiagnosticAgent

**Purpose:** Analyze errors, locate bugs, and suggest fixes.

**Location:** `src/asp/agents/diagnostic_agent.py`

```python
@dataclass
class DiagnosticReport:
    """Analysis of code issues and suggested fixes."""
    task_id: str
    issue_type: IssueType
    severity: Severity
    root_cause: str
    affected_files: list[AffectedFile]
    suggested_fixes: list[SuggestedFix]
    confidence: float  # 0.0 - 1.0

class IssueType(str, Enum):
    TEST_FAILURE = "test_failure"
    BUILD_ERROR = "build_error"
    RUNTIME_ERROR = "runtime_error"
    SECURITY_VULNERABILITY = "security_vulnerability"
    PERFORMANCE_ISSUE = "performance_issue"
    TYPE_ERROR = "type_error"

@dataclass
class AffectedFile:
    """File identified as containing the issue."""
    path: str
    line_start: int
    line_end: int
    code_snippet: str
    issue_description: str

@dataclass
class SuggestedFix:
    """A suggested code fix."""
    fix_id: str
    description: str
    confidence: float
    changes: list[CodeChange]

@dataclass
class CodeChange:
    """A specific change to make."""
    file_path: str
    change_type: Literal["replace", "insert", "delete"]
    line_start: int
    line_end: int | None  # None for insert
    old_code: str | None  # None for insert
    new_code: str


class DiagnosticAgent(BaseAgent):
    """
    Diagnostic Agent for analyzing code issues.

    This agent:
    - Receives test failures, build errors, or stack traces
    - Reads relevant source code for context
    - Identifies root cause of issues
    - Suggests specific fixes with confidence scores
    """

    def __init__(self, sandbox: SandboxExecutor, **kwargs):
        super().__init__(**kwargs)
        self.sandbox = sandbox

    def execute(self, input_data: DiagnosticInput) -> DiagnosticReport:
        """
        Analyze an issue and generate diagnostic report.

        Args:
            input_data: Contains error info, test results, workspace

        Returns:
            DiagnosticReport with root cause and suggested fixes
        """
        # 1. Gather context
        context = self._gather_context(input_data)

        # 2. Load diagnostic prompt
        prompt = self.load_prompt("diagnostic_agent_v1")
        formatted = self.format_prompt(
            prompt,
            error_type=input_data.error_type,
            error_message=input_data.error_message,
            stack_trace=input_data.stack_trace,
            test_failures=input_data.test_failures,
            source_context=context,
        )

        # 3. Call LLM for analysis
        response = self.call_llm(prompt=formatted, max_tokens=8000)

        # 4. Parse and validate
        return self.validate_output(response["content"], DiagnosticReport)

    def _gather_context(self, input_data: DiagnosticInput) -> dict:
        """
        Gather relevant source code context for analysis.

        IMPORTANT: Has FULL REPOSITORY ACCESS, not just the failing file.
        Root causes are often in dependencies, configs, or imports.

        Context gathering strategy:
        1. Files directly in stack trace (with ±20 line context)
        2. Import dependencies of failing files
        3. Configuration files (pyproject.toml, package.json, etc.)
        4. Related test files
        5. Files with similar names (e.g., if error in user.py, check user_test.py)
        """
        context = {}
        repo_path = input_data.workspace.target_repo_path

        # 1. Files directly in stack trace
        files_in_trace = self._extract_files_from_trace(input_data.stack_trace)
        for file_path, line_num in files_in_trace:
            full_path = repo_path / file_path
            if full_path.exists():
                content = full_path.read_text()
                context[file_path] = self._extract_lines(content, line_num - 20, line_num + 20)

        # 2. Import dependencies of failing files
        for file_path in list(context.keys()):
            imports = self._extract_imports(repo_path / file_path)
            for imp in imports[:5]:  # Limit to avoid context explosion
                imp_path = self._resolve_import(repo_path, imp)
                if imp_path and imp_path.exists() and str(imp_path) not in context:
                    context[str(imp_path.relative_to(repo_path))] = imp_path.read_text()[:2000]

        # 3. Configuration files (often contain the real issue)
        config_files = ["pyproject.toml", "setup.py", "package.json", "tsconfig.json", ".env.example"]
        for cfg in config_files:
            cfg_path = repo_path / cfg
            if cfg_path.exists():
                context[f"[CONFIG] {cfg}"] = cfg_path.read_text()[:1000]

        # 4. Repository structure overview
        context["[REPO_STRUCTURE]"] = self._get_repo_structure(repo_path, max_depth=3)

        return context

    def _get_repo_structure(self, repo_path: Path, max_depth: int = 3) -> str:
        """Get directory tree for orientation."""
        # Similar to `tree -L 3` command
        lines = []
        for path in sorted(repo_path.rglob("*")):
            if ".git" in path.parts:
                continue
            depth = len(path.relative_to(repo_path).parts)
            if depth <= max_depth:
                indent = "  " * (depth - 1)
                lines.append(f"{indent}{path.name}")
        return "\n".join(lines[:100])  # Limit size
```

#### Diagnostic Prompt Template

```markdown
# Diagnostic Analysis Prompt

You are an expert software debugger. Analyze the following error and identify the root cause.

## Error Information

**Error Type:** {error_type}
**Error Message:**
```
{error_message}
```

**Stack Trace:**
```
{stack_trace}
```

## Test Failures (if applicable)
{test_failures}

## Source Code Context
{source_context}

## Your Task

1. **Identify Root Cause:** What is causing this error?
2. **Locate the Bug:** Which file(s) and line(s) contain the bug?
3. **Suggest Fixes:** Provide specific code changes to fix the issue.

## Output Format

Return a JSON object matching this schema:
```json
{
  "task_id": "string",
  "issue_type": "test_failure|build_error|runtime_error|...",
  "severity": "Critical|High|Medium|Low",
  "root_cause": "Clear explanation of what's wrong",
  "affected_files": [
    {
      "path": "src/example.py",
      "line_start": 42,
      "line_end": 45,
      "code_snippet": "the problematic code",
      "issue_description": "why this code is wrong"
    }
  ],
  "suggested_fixes": [
    {
      "fix_id": "FIX-001",
      "description": "What this fix does",
      "confidence": 0.95,
      "changes": [
        {
          "file_path": "src/example.py",
          "change_type": "replace",
          "line_start": 42,
          "line_end": 45,
          "old_code": "broken code",
          "new_code": "fixed code"
        }
      ]
    }
  ],
  "confidence": 0.90
}
```
```

---

### 4. SurgicalEditor

**Purpose:** Apply targeted code changes without regenerating entire files.

**Location:** `src/services/surgical_editor.py`

```python
@dataclass
class EditOperation:
    """A single edit operation."""
    file_path: Path
    operation: Literal["replace", "insert", "delete"]
    line_start: int
    line_end: int | None
    old_content: str | None
    new_content: str | None

@dataclass
class EditResult:
    """Result of applying edits."""
    success: bool
    files_modified: list[str]
    backup_paths: dict[str, Path]  # original -> backup
    errors: list[str]


class SurgicalEditor:
    """
    Apply targeted code changes to existing files.

    Features:
    - Line-level precision edits
    - Automatic backup creation
    - Rollback support
    - Conflict detection
    - Unified diff generation
    - **Fuzzy matching** for resilience to line number drift
    - **Search-replace mode** as alternative to line-based edits

    IMPORTANT: LLMs are notoriously bad at counting line numbers. This editor
    supports multiple strategies to handle line number inaccuracy:

    1. SEARCH_REPLACE (preferred): Match on code content, not line numbers
    2. FUZZY_LINE: Line-based with ±N line tolerance
    3. EXACT_LINE: Strict line numbers (legacy, not recommended)
    """

    def __init__(
        self,
        workspace: Workspace,
        match_mode: Literal["search_replace", "fuzzy_line", "exact_line"] = "search_replace",
        fuzzy_tolerance: int = 5,  # Lines of drift allowed in fuzzy mode
    ):
        self.workspace = workspace
        self.backups: dict[str, Path] = {}
        self.match_mode = match_mode
        self.fuzzy_tolerance = fuzzy_tolerance

    def apply_changes(
        self,
        changes: list[CodeChange],
        create_backup: bool = True,
    ) -> EditResult:
        """
        Apply a list of code changes to files.

        Args:
            changes: List of CodeChange objects describing edits
            create_backup: Whether to backup files before editing

        Returns:
            EditResult with success status and modified files
        """
        errors = []
        modified = []

        # Group changes by file
        by_file = self._group_by_file(changes)

        for file_path, file_changes in by_file.items():
            try:
                full_path = self.workspace.target_repo_path / file_path

                if not full_path.exists():
                    errors.append(f"File not found: {file_path}")
                    continue

                # Create backup
                if create_backup:
                    self.backups[file_path] = self._create_backup(full_path)

                # Read current content
                lines = full_path.read_text().splitlines(keepends=True)

                # Sort changes by line number (descending to avoid offset issues)
                sorted_changes = sorted(
                    file_changes,
                    key=lambda c: c.line_start,
                    reverse=True
                )

                # Apply each change
                for change in sorted_changes:
                    lines = self._apply_single_change(lines, change)

                # Write modified content
                full_path.write_text("".join(lines))
                modified.append(file_path)

            except Exception as e:
                errors.append(f"Failed to edit {file_path}: {e}")

        return EditResult(
            success=len(errors) == 0,
            files_modified=modified,
            backup_paths=self.backups,
            errors=errors,
        )

    def _apply_single_change(
        self,
        lines: list[str],
        change: CodeChange
    ) -> list[str]:
        """Apply a single change to lines."""

        # Convert to 0-indexed
        start = change.line_start - 1
        end = (change.line_end or change.line_start) - 1

        if change.change_type == "replace":
            # Verify old content matches (fuzzy)
            old_lines = lines[start:end + 1]
            if not self._content_matches(old_lines, change.old_code):
                raise ValueError(
                    f"Content mismatch at lines {change.line_start}-{change.line_end}"
                )

            # Replace lines
            new_lines = change.new_code.splitlines(keepends=True)
            lines = lines[:start] + new_lines + lines[end + 1:]

        elif change.change_type == "insert":
            new_lines = change.new_code.splitlines(keepends=True)
            lines = lines[:start] + new_lines + lines[start:]

        elif change.change_type == "delete":
            lines = lines[:start] + lines[end + 1:]

        return lines

    def rollback(self, file_path: str | None = None) -> None:
        """
        Rollback changes using backups.

        Args:
            file_path: Specific file to rollback, or None for all
        """
        targets = [file_path] if file_path else list(self.backups.keys())

        for path in targets:
            if path in self.backups:
                backup = self.backups[path]
                target = self.workspace.target_repo_path / path
                shutil.copy(backup, target)

    def generate_diff(self, changes: list[CodeChange]) -> str:
        """Generate unified diff for changes."""
        diffs = []

        for change in changes:
            full_path = self.workspace.target_repo_path / change.file_path
            original = full_path.read_text().splitlines(keepends=True)

            # Apply change to copy
            modified = self._apply_single_change(original.copy(), change)

            # Generate diff
            diff = difflib.unified_diff(
                original,
                modified,
                fromfile=f"a/{change.file_path}",
                tofile=f"b/{change.file_path}",
            )
            diffs.append("".join(diff))

        return "\n".join(diffs)

    # =========================================================================
    # SEARCH-REPLACE MODE (Preferred - resilient to line number errors)
    # =========================================================================

    def apply_search_replace(
        self,
        file_path: str,
        search: str,
        replace: str,
        occurrence: int = 1,  # Which occurrence to replace (0 = all)
    ) -> EditResult:
        """
        Apply change by searching for exact code block, not line numbers.

        This is MORE RELIABLE than line-based edits because:
        - LLMs are bad at counting lines
        - Code may have shifted since analysis
        - Works even if file was modified by other changes

        Args:
            file_path: Path to file
            search: Exact code block to find
            replace: Code to replace it with
            occurrence: Which match to replace (1=first, 2=second, 0=all)

        Returns:
            EditResult with success status
        """
        full_path = self.workspace.target_repo_path / file_path
        content = full_path.read_text()

        # Normalize whitespace for matching
        normalized_search = self._normalize_whitespace(search)

        # Find all occurrences
        matches = list(re.finditer(
            re.escape(normalized_search),
            self._normalize_whitespace(content)
        ))

        if not matches:
            # Try fuzzy match
            match = self._fuzzy_find(content, search)
            if match:
                matches = [match]

        if not matches:
            return EditResult(
                success=False,
                files_modified=[],
                errors=[f"Could not find code block in {file_path}"],
            )

        # Apply replacement
        if occurrence == 0:
            new_content = content.replace(search, replace)
        else:
            # Replace specific occurrence
            new_content = self._replace_nth(content, search, replace, occurrence)

        # Backup and write
        self.backups[file_path] = self._create_backup(full_path)
        full_path.write_text(new_content)

        return EditResult(success=True, files_modified=[file_path], errors=[])

    def _fuzzy_find(
        self,
        content: str,
        search: str,
        threshold: float = 0.8,
    ) -> re.Match | None:
        """
        Find code block using fuzzy matching.

        Uses difflib.SequenceMatcher to find best match above threshold.
        Handles minor whitespace/formatting differences.
        """
        search_lines = search.strip().splitlines()
        content_lines = content.splitlines()

        best_ratio = 0
        best_start = -1

        # Sliding window search
        window_size = len(search_lines)
        for i in range(len(content_lines) - window_size + 1):
            window = "\n".join(content_lines[i:i + window_size])
            ratio = difflib.SequenceMatcher(
                None,
                search.strip(),
                window.strip()
            ).ratio()

            if ratio > best_ratio:
                best_ratio = ratio
                best_start = i

        if best_ratio >= threshold:
            # Return a match-like object
            matched_text = "\n".join(content_lines[best_start:best_start + window_size])
            return type('Match', (), {
                'start': lambda: content.find(matched_text),
                'end': lambda: content.find(matched_text) + len(matched_text),
                'group': lambda: matched_text,
            })()

        return None
```

---

### 5. RepairAgent

**Purpose:** Generate fixes for diagnosed issues.

**Location:** `src/asp/agents/repair_agent.py`

```python
@dataclass
class RepairInput:
    """Input for repair agent."""
    task_id: str
    workspace: Workspace
    diagnostic: DiagnosticReport
    previous_attempts: list[RepairAttempt] = field(default_factory=list)
    max_changes_per_file: int = 50

@dataclass
class RepairAttempt:
    """Record of a previous repair attempt."""
    attempt_number: int
    changes_made: list[CodeChange]
    test_result: TestResult
    why_failed: str | None

@dataclass
class RepairOutput:
    """Output from repair agent."""
    task_id: str
    strategy: str
    changes: list[CodeChange]
    explanation: str
    confidence: float
    alternative_fixes: list[dict] | None = None


class RepairAgent(BaseAgent):
    """
    Repair Agent for generating code fixes.

    This agent:
    - Takes diagnostic report with identified issues
    - Considers previous failed repair attempts
    - Generates targeted code changes
    - Provides multiple fix strategies when uncertain
    """

    def execute(self, input_data: RepairInput) -> RepairOutput:
        """
        Generate repair for diagnosed issue.

        Args:
            input_data: Contains diagnostic report and workspace

        Returns:
            RepairOutput with code changes to apply
        """
        # 1. Read relevant files for context
        file_contents = self._read_affected_files(input_data)

        # 2. Build repair prompt
        prompt = self.load_prompt("repair_agent_v1")
        formatted = self.format_prompt(
            prompt,
            task_id=input_data.task_id,
            diagnostic=input_data.diagnostic.model_dump_json(indent=2),
            file_contents=json.dumps(file_contents, indent=2),
            previous_attempts=self._format_attempts(input_data.previous_attempts),
            max_changes=input_data.max_changes_per_file,
        )

        # 3. Call LLM
        response = self.call_llm(prompt=formatted, max_tokens=8000)

        # 4. Parse and validate
        return self.validate_output(response["content"], RepairOutput)

    def _format_attempts(self, attempts: list[RepairAttempt]) -> str:
        """Format previous attempts for context."""
        if not attempts:
            return "No previous attempts."

        lines = ["## Previous Repair Attempts\n"]
        for attempt in attempts:
            lines.append(f"### Attempt {attempt.attempt_number}")
            lines.append(f"**Changes:** {len(attempt.changes_made)} modifications")
            lines.append(f"**Result:** {attempt.test_result.failed} tests still failing")
            if attempt.why_failed:
                lines.append(f"**Why it failed:** {attempt.why_failed}")
            lines.append("")

        return "\n".join(lines)
```

---

### 6. RepairOrchestrator

**Purpose:** Coordinate the diagnose-repair-validate loop.

**Location:** `src/asp/orchestrators/repair_orchestrator.py`

```python
@dataclass
class RepairRequest:
    """Request to repair code in a workspace."""
    task_id: str
    workspace: Workspace
    issue_description: str | None = None  # Optional description of issue
    target_tests: list[str] | None = None  # Specific tests to fix
    max_iterations: int = 5

@dataclass
class RepairResult:
    """Result of repair workflow."""
    task_id: str
    success: bool
    iterations_used: int
    final_test_result: TestResult
    changes_made: list[CodeChange]
    diagnostic_reports: list[DiagnosticReport]
    repair_attempts: list[RepairAttempt]


class RepairOrchestrator:
    """
    Orchestrates the repair workflow loop.

    Workflow:
    1. Run tests to identify failures
    2. Diagnose issues using DiagnosticAgent
    3. Generate fixes using RepairAgent
    4. Apply fixes using SurgicalEditor
    5. Re-run tests to validate
    6. If still failing, loop back to step 2
    7. Stop on success or max iterations
    """

    def __init__(
        self,
        sandbox: SandboxExecutor,
        test_executor: TestExecutor,
        diagnostic_agent: DiagnosticAgent,
        repair_agent: RepairAgent,
        langfuse_client: Langfuse | None = None,
    ):
        self.sandbox = sandbox
        self.test_executor = test_executor
        self.diagnostic_agent = diagnostic_agent
        self.repair_agent = repair_agent
        self.langfuse = langfuse_client

    async def repair(self, request: RepairRequest) -> RepairResult:
        """
        Execute repair workflow.

        Args:
            request: RepairRequest with workspace and constraints

        Returns:
            RepairResult with success status and all changes
        """
        trace = self._start_trace(request)

        all_changes = []
        diagnostics = []
        attempts = []
        editor = SurgicalEditor(request.workspace)

        for iteration in range(1, request.max_iterations + 1):
            logger.info(f"Repair iteration {iteration}/{request.max_iterations}")

            # Step 1: Run tests
            with trace.span(name=f"test_execution_{iteration}"):
                test_result = self.test_executor.run_tests(
                    request.workspace,
                    test_path=request.target_tests[0] if request.target_tests else None,
                )

            # Check for success
            if test_result.failed == 0 and test_result.errors == 0:
                logger.info(f"All tests passing after {iteration} iterations")
                return RepairResult(
                    task_id=request.task_id,
                    success=True,
                    iterations_used=iteration,
                    final_test_result=test_result,
                    changes_made=all_changes,
                    diagnostic_reports=diagnostics,
                    repair_attempts=attempts,
                )

            # Step 2: Diagnose
            with trace.span(name=f"diagnosis_{iteration}"):
                diagnostic_input = DiagnosticInput(
                    task_id=request.task_id,
                    workspace=request.workspace,
                    test_result=test_result,
                    error_type="test_failure",
                    error_message=self._format_failures(test_result.failures),
                    stack_trace=self._combine_traces(test_result.failures),
                )
                diagnostic = self.diagnostic_agent.execute(diagnostic_input)
                diagnostics.append(diagnostic)

            # Step 3: Generate repair
            with trace.span(name=f"repair_generation_{iteration}"):
                repair_input = RepairInput(
                    task_id=request.task_id,
                    workspace=request.workspace,
                    diagnostic=diagnostic,
                    previous_attempts=attempts,
                )
                repair_output = self.repair_agent.execute(repair_input)

            # Step 4: Apply changes
            with trace.span(name=f"apply_changes_{iteration}"):
                edit_result = editor.apply_changes(repair_output.changes)

                if not edit_result.success:
                    logger.warning(f"Failed to apply some changes: {edit_result.errors}")

            # Record attempt
            all_changes.extend(repair_output.changes)
            attempts.append(RepairAttempt(
                attempt_number=iteration,
                changes_made=repair_output.changes,
                test_result=test_result,
                why_failed=f"{test_result.failed} tests failing",
            ))

            # Check for HITL trigger (too many iterations)
            if iteration >= 3 and test_result.failed > 0:
                if await self._should_escalate_to_human(request, attempts):
                    logger.info("Escalating to human review")
                    # ... trigger HITL workflow

        # Max iterations reached
        final_test = self.test_executor.run_tests(request.workspace)

        return RepairResult(
            task_id=request.task_id,
            success=False,
            iterations_used=request.max_iterations,
            final_test_result=final_test,
            changes_made=all_changes,
            diagnostic_reports=diagnostics,
            repair_attempts=attempts,
        )
```

---

## Integration with Existing Architecture

### Modified TSP Orchestrator

The existing TSP (Tiny Software Process) orchestrator can be extended to support repair mode:

```python
class TSPOrchestrator:
    """Extended to support both greenfield and repair modes."""

    async def execute(self, request: TSPRequest) -> TSPResult:
        """Execute TSP workflow."""

        if request.mode == "greenfield":
            return await self._execute_greenfield(request)
        elif request.mode == "repair":
            return await self._execute_repair(request)
        else:
            raise ValueError(f"Unknown mode: {request.mode}")

    async def _execute_repair(self, request: TSPRequest) -> TSPResult:
        """Execute repair workflow."""

        # 1. Clone/setup workspace (existing)
        workspace = self.workspace_manager.create_workspace(request.task_id)
        self.workspace_manager.clone_repository(workspace, request.repo_url)

        # 2. Run repair orchestrator (new)
        repair_result = await self.repair_orchestrator.repair(
            RepairRequest(
                task_id=request.task_id,
                workspace=workspace,
                issue_description=request.issue_description,
                max_iterations=request.max_iterations or 5,
            )
        )

        # 3. If successful, commit and create PR (existing)
        if repair_result.success:
            self._commit_changes(workspace, repair_result)
            pr_url = self._create_pr(workspace, repair_result)

        return TSPResult(
            success=repair_result.success,
            mode="repair",
            repair_result=repair_result,
            # ...
        )
```

### New Prompt Templates

```
prompts/
├── diagnostic_agent_v1.md      # Error analysis prompt
├── repair_agent_v1.md          # Fix generation prompt
└── repair_agent_v1_retry.md    # Retry with previous attempts
```

### New Models

```
src/asp/models/
├── diagnostic.py    # DiagnosticInput, DiagnosticReport, etc.
├── repair.py        # RepairInput, RepairOutput, CodeChange
└── execution.py     # ExecutionResult, TestResult, TestFailure
```

---

## E2E Test for Repair Workflow

**Location:** `tests/e2e/test_repair_workflow_e2e.py`

```python
"""
E2E test for repair workflow - fixing bugs in existing code.

This test:
1. Creates a workspace with intentionally buggy code
2. Runs the repair orchestrator
3. Verifies the bugs are fixed and tests pass
"""

import pytest
from pathlib import Path

from services.workspace_manager import WorkspaceManager
from services.sandbox_executor import DockerSandboxExecutor
from services.test_executor import TestExecutor
from asp.agents.diagnostic_agent import DiagnosticAgent
from asp.agents.repair_agent import RepairAgent
from asp.orchestrators.repair_orchestrator import RepairOrchestrator, RepairRequest


# Intentionally buggy code fixture
BUGGY_CALCULATOR = '''
def add(a, b):
    return a - b  # BUG: should be a + b

def divide(a, b):
    return a / b  # BUG: no zero division check

def multiply(a, b):
    return a * b  # Correct
'''

CALCULATOR_TESTS = '''
import pytest
from calculator import add, divide, multiply

def test_add():
    assert add(2, 3) == 5  # Will fail due to bug

def test_divide():
    assert divide(10, 2) == 5

def test_divide_by_zero():
    with pytest.raises(ZeroDivisionError):
        divide(10, 0)  # Will fail - no handling

def test_multiply():
    assert multiply(3, 4) == 12  # Will pass
'''


@pytest.fixture
def buggy_workspace(tmp_path):
    """Create workspace with buggy code."""
    manager = WorkspaceManager(base_path=tmp_path)
    workspace = manager.create_workspace("test-repair-001")

    # Initialize git repo with buggy code
    manager.initialize_git_repo(
        workspace,
        initial_files={
            "calculator.py": BUGGY_CALCULATOR,
            "test_calculator.py": CALCULATOR_TESTS,
            "pyproject.toml": '[project]\nname = "calculator"\n',
        }
    )

    return workspace


class TestRepairWorkflowE2E:
    """E2E tests for the repair workflow."""

    @pytest.mark.e2e
    @pytest.mark.slow
    def test_repair_buggy_calculator(self, buggy_workspace):
        """
        Test that repair workflow can fix bugs in calculator.

        Expected behavior:
        1. Initial test run shows 2 failures (add, divide_by_zero)
        2. Diagnostic agent identifies both bugs
        3. Repair agent generates fixes
        4. After repair, all tests pass
        """
        # Setup components
        sandbox = DockerSandboxExecutor()
        test_executor = TestExecutor(sandbox)
        diagnostic_agent = DiagnosticAgent(sandbox=sandbox)
        repair_agent = RepairAgent()

        orchestrator = RepairOrchestrator(
            sandbox=sandbox,
            test_executor=test_executor,
            diagnostic_agent=diagnostic_agent,
            repair_agent=repair_agent,
        )

        # Run repair workflow
        result = orchestrator.repair(RepairRequest(
            task_id="test-repair-001",
            workspace=buggy_workspace,
            max_iterations=3,
        ))

        # Assertions
        assert result.success, f"Repair failed after {result.iterations_used} iterations"
        assert result.final_test_result.failed == 0
        assert result.final_test_result.passed >= 3
        assert len(result.changes_made) >= 2  # At least 2 fixes

        # Verify the fixes
        calculator_path = buggy_workspace.target_repo_path / "calculator.py"
        fixed_code = calculator_path.read_text()

        # Check add is fixed
        assert "a + b" in fixed_code or "return a + b" in fixed_code

        # Check divide has zero check
        assert "if b == 0" in fixed_code or "ZeroDivisionError" in fixed_code

    @pytest.mark.e2e
    def test_repair_max_iterations_exceeded(self, buggy_workspace):
        """Test behavior when repair cannot fix issue within max iterations."""
        # ... similar setup but with harder-to-fix bug
        pass

    @pytest.mark.e2e
    def test_repair_with_hitl_escalation(self, buggy_workspace):
        """Test that complex repairs trigger HITL."""
        pass
```

---

## Security Considerations

### Sandbox Isolation

1. **No Host Access:** Containers cannot access host filesystem except mounted workspace
2. **No Network by Default:** Network disabled unless explicitly required
3. **Resource Limits:** Memory, CPU, and time limits prevent DoS
4. **Read-Only Mounts:** Consider read-only mounts for dependency directories

### Code Execution Risks

1. **Arbitrary Code:** Executing untrusted code requires full containerization
2. **Secret Exposure:** Ensure API keys/secrets not passed to sandbox
3. **Malicious Tests:** Test code could attempt exploits - sandbox mitigates
4. **Supply Chain:** Dependencies pulled during test could be malicious

### Mitigations

```python
class SecurityConfig:
    """Security configuration for sandbox."""

    # Disallow these commands
    BLOCKED_COMMANDS = [
        "rm -rf /",
        "curl",
        "wget",
        "nc",
        "ssh",
    ]

    # Required for all executions
    REQUIRED_CONTAINER_OPTIONS = {
        "read_only": False,  # Need to write test results
        "network_disabled": True,
        "cap_drop": ["ALL"],
        "security_opt": ["no-new-privileges"],
    }
```

---

## Implementation Plan

### Phase 1: Foundation (Week 1-2)
- [ ] Implement `SandboxExecutor` with subprocess backend
- [ ] Implement `TestExecutor` with pytest parser
- [ ] Write unit tests for both components
- [ ] Add sandbox config to settings

### Phase 2: Diagnostic Capability (Week 2-3)
- [ ] Create `DiagnosticAgent` with prompt template
- [ ] Implement stack trace parsing
- [ ] Implement source context gathering
- [ ] Add `DiagnosticInput`/`DiagnosticReport` models

### Phase 3: Repair Capability (Week 3-4)
- [ ] Implement `SurgicalEditor` with backup/rollback
- [ ] Create `RepairAgent` with prompt template
- [ ] Add `CodeChange` model and apply logic
- [ ] Write integration tests

### Phase 4: Orchestration (Week 4-5)
- [ ] Implement `RepairOrchestrator`
- [ ] Add iteration loop with max limits
- [ ] Integrate with Langfuse tracing
- [ ] Add HITL escalation triggers

### Phase 5: Integration & E2E (Week 5-6)
- [ ] Extend `TSPOrchestrator` for repair mode
- [ ] Write E2E test with buggy calculator
- [ ] Docker sandbox implementation
- [ ] Documentation and examples

### Phase 6: Multi-Language Support (Future)
- [ ] Add Jest/Mocha parsers for JavaScript
- [ ] Add Go test parser
- [ ] Add Cargo test parser for Rust
- [ ] Language-specific sandbox images

---

## Consequences

### Positive

✅ **Full Repair Capability:** Can diagnose and fix bugs in existing code
✅ **Validated Fixes:** Real test execution confirms fixes work
✅ **Iterative Refinement:** Can retry until tests pass
✅ **Safe Execution:** Sandboxed code execution prevents damage
✅ **Surgical Precision:** Targeted edits reduce risk of side effects
✅ **Observable:** Full Langfuse tracing for debugging and improvement

### Negative

⚠️ **Complexity:** Significant new components to build and maintain
⚠️ **Docker Dependency:** Full sandbox requires Docker
⚠️ **Execution Time:** Real test execution slower than LLM simulation
⚠️ **Resource Usage:** Running containers requires more resources
⚠️ **Security Surface:** Code execution introduces security considerations

### Risks

| Risk | Mitigation |
|------|------------|
| Sandbox escape | Use rootless containers, drop capabilities |
| Infinite loops | Max iterations, per-test timeouts |
| Resource exhaustion | Memory/CPU limits per container |
| Fix introduces new bugs | Comprehensive test re-run after each fix |
| LLM generates bad fixes | Multiple fix strategies, confidence scores |

---

## Open Questions

1. **Should we support parallel test execution?** Running tests in parallel could speed up validation but complicates result parsing.

2. **How do we handle flaky tests?** Tests that sometimes pass/fail could cause infinite repair loops.

3. **Should repairs be atomic?** Roll back all changes if any test still fails, or keep partial progress?

4. **What's the HITL threshold?** After how many iterations should we escalate to human review?

5. **Should we cache diagnostic results?** If the same error appears, can we reuse previous diagnosis?

---

## HITL (Human-In-The-Loop) Approval Gates

Per Gemini's review feedback, explicit HITL gates are needed. The repair workflow supports both **autonomous** and **supervised** modes:

### Approval Gate Configuration

```python
@dataclass
class HITLConfig:
    """Configuration for human approval gates."""

    # Mode: "autonomous" (no approval), "supervised" (always approve), "threshold" (conditional)
    mode: Literal["autonomous", "supervised", "threshold"] = "threshold"

    # Threshold triggers (only in "threshold" mode)
    require_approval_after_iterations: int = 2  # Escalate after N failed attempts
    require_approval_for_confidence_below: float = 0.7  # Low confidence fixes need approval
    require_approval_for_critical_files: list[str] = field(default_factory=lambda: [
        "*.env*", "*.key", "*.pem",  # Secrets
        "**/auth/**", "**/security/**",  # Security-critical
        "Dockerfile", "docker-compose*",  # Infrastructure
    ])

    # What to show human
    show_diff_preview: bool = True
    show_test_results: bool = True
    show_diagnostic_reasoning: bool = True
```

### Approval Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│                     APPROVAL GATE FLOW                               │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│   RepairAgent generates fix                                          │
│            │                                                         │
│            ▼                                                         │
│   ┌────────────────────┐                                            │
│   │  Check HITL Config │                                            │
│   └─────────┬──────────┘                                            │
│             │                                                        │
│    ┌────────┴────────┐                                              │
│    │                 │                                               │
│    ▼                 ▼                                               │
│ autonomous?      threshold?                                          │
│    │                 │                                               │
│    │         ┌──────┴──────┐                                        │
│    │         │             │                                         │
│    │         ▼             ▼                                         │
│    │    iterations > N?  confidence < 0.7?                          │
│    │         │             │                                         │
│    │         └──────┬──────┘                                        │
│    │                │                                                │
│    │           Yes  │  No                                            │
│    │                │                                                │
│    │    ┌───────────┴───────────┐                                   │
│    │    ▼                       ▼                                    │
│    │  Request                 Apply                                  │
│    │  Human                   Changes                                │
│    │  Approval                Directly                               │
│    │    │                                                            │
│    │    ▼                                                            │
│    │  ┌─────────┐                                                   │
│    │  │ Approve │────▶ Apply Changes                                │
│    │  │ Reject  │────▶ Try Alternative / Escalate                   │
│    │  │ Modify  │────▶ Apply Human Edits                            │
│    │  └─────────┘                                                   │
│    │                                                                 │
│    └─────────────────────────────────────────────────────────────────│
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### Approval Request Content

When HITL is triggered, the human sees:

```python
@dataclass
class ApprovalRequest:
    """Request sent to human for approval."""
    task_id: str
    iteration: int
    diagnostic_summary: str  # What's wrong
    proposed_fix: str  # What we want to do
    confidence: float  # How sure we are
    diff_preview: str  # Unified diff of changes
    files_affected: list[str]
    test_results_before: TestResult
    alternative_fixes: list[str] | None  # Other options if this is rejected
    langfuse_trace_url: str  # Link to full execution trace
```

---

## Confidence Score Calculation

Per Gemini's review feedback, confidence scores need clear definition. They are **NOT just LLM self-reporting**.

### Confidence Components

```python
@dataclass
class ConfidenceBreakdown:
    """Detailed confidence calculation."""

    # Component scores (0.0 - 1.0)
    diagnostic_confidence: float  # How sure we are about root cause
    fix_confidence: float  # How sure we are the fix is correct
    test_coverage_confidence: float  # How well tests cover the fix

    # Calculated overall confidence
    @property
    def overall(self) -> float:
        # Weighted average - test coverage weighs heavily
        return (
            self.diagnostic_confidence * 0.3 +
            self.fix_confidence * 0.3 +
            self.test_coverage_confidence * 0.4
        )


def calculate_confidence(
    diagnostic: DiagnosticReport,
    repair: RepairOutput,
    test_result: TestResult,
    workspace: Workspace,
) -> ConfidenceBreakdown:
    """
    Calculate confidence score from multiple signals.

    NOT just LLM self-reporting - uses objective metrics.
    """

    # 1. Diagnostic Confidence
    # - Based on: stack trace clarity, single vs multiple root causes,
    #   LLM's stated confidence, number of affected files
    diagnostic_confidence = _calc_diagnostic_confidence(diagnostic)

    # 2. Fix Confidence
    # - Based on: fix size (smaller = more confident), previous attempt history,
    #   LLM's stated confidence, fix strategy specificity
    fix_confidence = _calc_fix_confidence(repair)

    # 3. Test Coverage Confidence (OBJECTIVE - not LLM opinion)
    # - Based on: actual test coverage of modified lines,
    #   number of tests touching modified code, test pass rate
    test_coverage_confidence = _calc_test_coverage_confidence(
        repair.changes,
        test_result,
        workspace,
    )

    return ConfidenceBreakdown(
        diagnostic_confidence=diagnostic_confidence,
        fix_confidence=fix_confidence,
        test_coverage_confidence=test_coverage_confidence,
    )


def _calc_test_coverage_confidence(
    changes: list[CodeChange],
    test_result: TestResult,
    workspace: Workspace,
) -> float:
    """
    Calculate confidence based on ACTUAL test coverage.

    This is objective, not LLM opinion:
    - Did tests actually run against the modified code?
    - What % of modified lines are covered by tests?
    - Did all tests pass?
    """
    if test_result.coverage_percent is None:
        return 0.5  # Unknown coverage = medium confidence

    # Base: coverage percentage
    base = test_result.coverage_percent / 100.0

    # Penalty for failing tests
    if test_result.failed > 0:
        base *= 0.5

    # Bonus for high test count touching modified files
    modified_files = {c.file_path for c in changes}
    tests_touching_modified = _count_tests_for_files(modified_files, workspace)
    if tests_touching_modified >= 5:
        base = min(1.0, base * 1.2)

    return base
```

### Confidence Thresholds

| Confidence | Interpretation | Action |
|------------|----------------|--------|
| 0.9 - 1.0 | Very High | Apply automatically |
| 0.7 - 0.9 | High | Apply, monitor |
| 0.5 - 0.7 | Medium | Consider HITL approval |
| 0.3 - 0.5 | Low | Require HITL approval |
| 0.0 - 0.3 | Very Low | Reject, try alternative |

---

## Amendments from Review

This section documents changes made based on external review feedback (Gemini, 2025-12-10):

| Concern | Resolution |
|---------|------------|
| **TestExecutor parser maintenance burden** | Added `_fallback_parse()` method that returns raw stdout/stderr when parser fails or is unavailable. Agents can still analyze raw output. |
| **SurgicalEditor line number accuracy** | Added `search_replace` mode as default (preferred over line-based). Implemented `_fuzzy_find()` with 80% similarity threshold. |
| **Infinite repair loops** | Max 5 iterations with rollback. Each iteration tracked. HITL escalation after 2 failed attempts. |
| **DiagnosticAgent context scope** | Clarified full repo access. Now gathers: stack trace files, import dependencies, config files, and repo structure. |
| **HITL approval gates** | Added `HITLConfig` with three modes: autonomous, supervised, threshold. Configurable triggers. |
| **Confidence score calculation** | Defined multi-signal calculation: diagnostic confidence, fix confidence, and **objective** test coverage confidence. Not just LLM self-reporting. |

---

## Related Documents

- `design/ADR_001_workspace_isolation_and_execution_tracking.md` - Workspace architecture
- `design/HITL_QualityGate_Architecture.md` - Human-in-the-loop integration
- `docs/issues/e2e_test_feedback_loop_bug.md` - Related feedback loop issue
- `src/services/workspace_manager.py` - Existing workspace implementation

---

**Status:** Proposed - revised after Gemini review (2025-12-10)
**Next Steps:** Final review, then begin Phase 1 implementation
