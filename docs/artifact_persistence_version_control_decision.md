# Architecture Decision Record: Artifact Persistence and Version Control Integration

**Date:** November 17, 2025
**Status:** Proposed
**Decision Maker:** ASP Development Team
**Context:** Code Review Agent (FR-005) Implementation

---

## Context and Problem Statement

The ASP platform currently generates artifacts (ProjectPlan, DesignSpecification, GeneratedCode) as in-memory Pydantic models that are:
1. Stored only in the telemetry database (SQLite)
2. Not written to the filesystem
3. Not committed to version control (git)

This creates several critical problems:

**Problem 1: No Human Visibility**
- Developers cannot easily inspect plans, designs, or generated code
- No IDE integration (can't open files, search, navigate)
- Difficult to review agent outputs before acceptance

**Problem 2: No Version Control History**
- No git log showing evolution of artifacts
- Cannot rollback to previous versions
- No code review workflow (pull requests, comments)
- No traceability of changes over time

**Problem 3: No Collaboration**
- Team cannot review/comment on plans or designs
- No way to suggest changes before code generation
- Agent outputs are "black box" JSON in database

**Problem 4: Code Review Challenges**
- Code Review Agent (FR-005) would review in-memory strings
- Issues reference non-existent file paths
- Cannot open file:line in IDE to see the issue
- No way to manually verify agent findings

**Problem 5: CI/CD Integration Gaps**
- Cannot trigger builds on code generation
- Cannot run linters/formatters on generated code
- No automated quality gates in CI pipeline

---

## Decision Drivers

### Must Have
1. **Human readability** - Developers must be able to read artifacts in IDE
2. **Version control** - All artifacts must be in git for history/rollback
3. **Traceability** - Clear linkage from requirements → code via git log
4. **Code review workflow** - Support standard PR review process
5. **Backward compatibility** - Existing Pydantic models still work

### Should Have
1. **Automated commits** - Agents auto-commit artifacts after execution
2. **Markdown reports** - Human-readable summaries alongside JSON
3. **Standard directory structure** - Consistent artifact organization
4. **CI/CD integration** - Trigger workflows on artifact commits

### Nice to Have
1. **Artifact diffing** - Compare plan v1 vs. v2 easily
2. **Multi-project support** - Handle multiple projects in one repo
3. **Artifact templates** - Standardized markdown formats

---

## Considered Options

### Option A: Status Quo (Database Only)

**Description:** Continue storing artifacts only in telemetry database.

**Pros:**
- ✅ No implementation work required
- ✅ Centralized storage (single SQLite file)
- ✅ Easy to query (SQL)

**Cons:**
- ❌ No human visibility (must query DB)
- ❌ No version control
- ❌ No IDE integration
- ❌ Code Review Agent reviews in-memory strings
- ❌ Cannot leverage git workflows
- ❌ No CI/CD integration

**Verdict:** ❌ Rejected - Fails critical requirements

---

### Option B: Filesystem + Git (Hybrid Approach)

**Description:** Write artifacts to filesystem AND store in database. Auto-commit to git.

**Architecture:**
```
For each agent execution:
1. Generate artifact (Pydantic model)
2. Write to database (telemetry)
3. Write to filesystem (artifacts/ directory)
4. Convert to markdown (human-readable)
5. Git commit with descriptive message
```

**Directory Structure:**
```
project_root/
├── artifacts/
│   └── {task_id}/
│       ├── plan.json              # ProjectPlan (machine-readable)
│       ├── plan.md                # ProjectPlan (human-readable)
│       ├── design.json            # DesignSpecification
│       ├── design.md              # Design summary
│       ├── design_review.json     # DesignReviewReport
│       ├── design_review.md       # Review report
│       ├── code_manifest.json     # GeneratedCode metadata
│       ├── code_review.json       # CodeReviewReport
│       └── code_review.md         # Review report
├── src/                           # Generated source code
│   ├── api/
│   │   └── auth.py                # From Code Agent
│   ├── models/
│   │   └── user.py
│   └── ...
├── tests/                         # Generated tests
│   └── test_auth.py
└── ...
```

**Git Workflow:**
```bash
# After Planning Agent
git commit -m "Add project plan for JWT-AUTH-001"

# After Design Agent
git commit -m "Add design specification for JWT-AUTH-001"

# After Design Review Agent
git commit -m "Add design review for JWT-AUTH-001 - PASS"

# After Code Agent
git commit -m "Implement JWT-AUTH-001: JWT authentication endpoints"

# After Code Review Agent
git commit -m "Add code review for JWT-AUTH-001 - FAIL (2 Critical issues)"
```

**Pros:**
- ✅ Human visibility (files in IDE)
- ✅ Version control (full git history)
- ✅ Code review workflow (can create PRs)
- ✅ IDE integration (click file:line to jump)
- ✅ CI/CD integration (git hooks, GitHub Actions)
- ✅ Traceability (git log shows pipeline)
- ✅ Rollback capability (git revert)
- ✅ Dual storage (filesystem + database)
- ✅ Backward compatible (Pydantic models unchanged)

**Cons:**
- ❌ Implementation complexity (+2-3 hours work)
- ❌ Disk space usage (artifacts + code on disk)
- ❌ Git repo growth (many commits)
- ❌ Need file I/O utilities
- ❌ Need markdown rendering

**Verdict:** ✅ **RECOMMENDED**

---

### Option C: Filesystem Only (No Database)

**Description:** Write artifacts only to filesystem, remove database storage.

**Pros:**
- ✅ Human visibility
- ✅ Version control
- ✅ Simpler architecture (single storage)

**Cons:**
- ❌ Lose telemetry queryability (SQL analysis)
- ❌ Lose PROBE-AI historical data
- ❌ Lose cost tracking per task
- ❌ Breaks existing telemetry infrastructure

**Verdict:** ❌ Rejected - Breaks telemetry requirements

---

### Option D: External Artifact Store (S3/Cloud)

**Description:** Write artifacts to cloud storage (AWS S3, GCS, Azure Blob).

**Pros:**
- ✅ Scalable storage
- ✅ Multi-environment support
- ✅ Versioning built-in (S3 versioning)

**Cons:**
- ❌ No git integration
- ❌ No local IDE integration
- ❌ Requires cloud credentials
- ❌ Network latency
- ❌ Cost (storage fees)
- ❌ Complexity (cloud SDK integration)

**Verdict:** ❌ Rejected - Over-engineered for current needs

---

### Option E: Separate Git Repository Per Project

**Description:** Initialize a new git repository for each project that ASP creates, rather than working within a single monorepo.

**Architecture:**
```
~/asp_projects/
├── jwt-auth-system/              ← Separate git repo
│   ├── .git/
│   ├── artifacts/
│   │   ├── JWT-AUTH-001/
│   │   │   ├── plan.json
│   │   │   ├── plan.md
│   │   │   └── ...
│   │   └── JWT-AUTH-002/
│   ├── src/
│   │   └── api/
│   │       └── auth.py
│   ├── tests/
│   │   └── test_auth.py
│   ├── README.md
│   └── requirements.txt
│
├── user-management-api/          ← Separate git repo
│   ├── .git/
│   ├── artifacts/
│   ├── src/
│   └── ...
│
└── payment-service/              ← Separate git repo
    ├── .git/
    └── ...
```

**Use Cases:**

**Use Case 1: Project-Level Agent (Greenfield Development)**
```
User: "Build me a microservice for user authentication"
ASP:
  1. Planning Agent: Detects this is a complete project
  2. Creates ~/asp_projects/user-auth-service/
  3. Runs: git init
  4. Creates: README.md, .gitignore, src/, tests/, artifacts/
  5. All agents work within this new repo
```

**Use Case 2: Task-Level Agent (Feature Development)**
```
User: "Add JWT authentication to my existing FastAPI app"
ASP:
  1. Planning Agent: Detects this is a task in current repo
  2. Works in current working directory
  3. Creates: artifacts/JWT-AUTH-001/ in current repo
  4. Commits to current repo
```

**Implementation Approach: Hybrid Mode Support**

```python
# Project Mode - Creates new standalone repo
planning_agent.execute(
    requirements="Build user authentication microservice",
    mode="project",
    project_name="user-auth-service",
    base_directory="~/asp_projects"
)
# Creates: ~/asp_projects/user-auth-service/ (new git repo)
# Initializes: git init, directory structure, .gitignore
# Registers: Project in ASP registry database

# Task Mode - Works in current repo (default)
planning_agent.execute(
    requirements="Add JWT authentication",
    mode="task",  # Default
)
# Works in: Current working directory
# Creates: artifacts/{task_id}/ in current repo
```

**Project Registry Database:**
```sql
CREATE TABLE asp_projects (
    project_id TEXT PRIMARY KEY,
    project_name TEXT NOT NULL,
    project_path TEXT NOT NULL,       -- /home/user/asp_projects/user-auth-service
    git_remote TEXT,                  -- https://github.com/user/user-auth-service (optional)
    created_at TIMESTAMP,
    mode TEXT,                        -- 'project' or 'task'
    parent_task_id TEXT,              -- First planning task that created this project
    status TEXT                       -- 'active', 'archived', 'deployed'
);
```

**Pros:**
- ✅ **Clean separation** - Each project is completely independent
- ✅ **Standard project structure** - Matches how developers normally organize code
- ✅ **Independent deployment** - Each repo can have its own CI/CD pipeline
- ✅ **Clear ownership** - Each repo can have its own team/permissions on GitHub/GitLab
- ✅ **No namespace pollution** - No need for `project_id` in artifact paths
- ✅ **Easy to distribute** - Push to GitHub, share complete working projects
- ✅ **Realistic output** - Agent produces real, deployable applications
- ✅ **Scalable isolation** - Projects don't interfere with each other
- ✅ **Natural archiving** - Archive/delete entire project repo when done
- ✅ **Supports both workflows** - Greenfield projects AND feature development in existing repos

**Cons:**
- ❌ **Management complexity** - Need to track multiple repos, multiple working directories
- ❌ **Cross-project dependencies** - Hard to reference code across different repos
- ❌ **Testing complexity** - Each E2E test might create a new repo (need cleanup)
- ❌ **Discovery challenge** - How do you find all projects created by ASP? (solved by registry)
- ❌ **Telemetry fragmentation** - ASP telemetry database in one location, projects scattered
- ❌ **Initial setup overhead** - More work to initialize project (git init, directory structure)
- ❌ **Path management** - Need to track current working directory, switch between repos

**When This Makes Sense:**
- ASP is generating **complete, standalone applications** (microservices, CLIs, libraries)
- Each project will be **deployed independently**
- Projects are **long-lived** and maintained separately
- **Multi-team environment** where different projects have different owners
- User wants **distributable output** (can push to GitHub and share)

**When This Doesn't Make Sense:**
- ASP is generating **tasks/features within one existing codebase**
- All work is for the **same application** (monolith architecture)
- **Short-lived experiments** or bootstrap data collection
- **Single developer or small team** working in one codebase

**Decision Criteria for Mode Selection:**

The Planning Agent could auto-detect based on requirements:

```python
def detect_mode(requirements: str) -> str:
    """Auto-detect if this is a project or task."""
    project_indicators = [
        "build", "create", "develop", "implement a system",
        "microservice", "application", "service", "API from scratch"
    ]
    task_indicators = [
        "add", "update", "fix", "modify", "refactor",
        "to my app", "to the codebase", "in the existing"
    ]

    if any(indicator in requirements.lower() for indicator in project_indicators):
        return "project"
    elif any(indicator in requirements.lower() for indicator in task_indicators):
        return "task"
    else:
        # Default: task mode (safer, works in current repo)
        return "task"
```

**Implementation Changes:**

**Planning Agent:**
```python
def execute(self, requirements: str, mode: Optional[str] = None) -> ProjectPlan:
    # Auto-detect or use explicit mode
    execution_mode = mode or self._detect_mode(requirements)

    if execution_mode == "project":
        # Create new project repo
        project_name = self._extract_project_name(requirements)
        project_path = self._initialize_project_repo(project_name)

        # Register in ASP database
        self._register_project(project_name, project_path)

        # Change working directory to new repo
        os.chdir(project_path)

    # Continue with normal planning...
```

**Project Initialization:**
```python
def _initialize_project_repo(self, project_name: str) -> str:
    """Initialize new git repo for project."""
    base_dir = os.path.expanduser("~/asp_projects")
    project_path = os.path.join(base_dir, project_name)

    # Create directory structure
    os.makedirs(project_path, exist_ok=True)
    os.makedirs(f"{project_path}/src", exist_ok=True)
    os.makedirs(f"{project_path}/tests", exist_ok=True)
    os.makedirs(f"{project_path}/artifacts", exist_ok=True)
    os.makedirs(f"{project_path}/docs", exist_ok=True)

    # Initialize git
    subprocess.run(["git", "init"], cwd=project_path, check=True)

    # Create .gitignore
    gitignore_content = """
__pycache__/
*.py[cod]
*$py.class
*.so
.env
.venv
venv/
*.db
*.sqlite3
.pytest_cache/
.coverage
htmlcov/
dist/
build/
*.egg-info/
"""
    write_file(f"{project_path}/.gitignore", gitignore_content)

    # Create README
    readme_content = f"""# {project_name}

Generated by ASP (Agentic Software Process) Platform

## Project Structure

- `src/` - Source code
- `tests/` - Test files
- `artifacts/` - ASP planning/design artifacts
- `docs/` - Documentation

## Setup

TBD (will be populated by Code Agent)

## Generated By

- ASP Platform
- Date: {datetime.now().isoformat()}
"""
    write_file(f"{project_path}/README.md", readme_content)

    # Initial commit
    subprocess.run(["git", "add", "."], cwd=project_path, check=True)
    subprocess.run(
        ["git", "commit", "-m", f"Initialize project: {project_name}"],
        cwd=project_path,
        check=True
    )

    return project_path
```

**CLI Support:**
```bash
# Explicit project mode
asp plan "Build user authentication microservice" --mode=project --name=user-auth-service

# Explicit task mode (default)
asp plan "Add JWT authentication" --mode=task

# Auto-detect (default)
asp plan "Build a FastAPI microservice"  # Detects "build" → project mode
asp plan "Add logging to the API"        # Detects "add" → task mode
```

**Verdict:** ✅ **RECOMMENDED as Enhancement** - Support both modes

This option should be implemented as an **enhancement to Option B** (not a replacement). The hybrid approach provides:

1. **Flexibility** - Users choose based on their workflow (greenfield vs. feature development)
2. **Natural separation** - Projects are isolated when appropriate
3. **Backward compatibility** - Default to task mode (works in current directory)
4. **Professional output** - Can generate complete, distributable projects

**Recommendation:**
- **Phase 1 (MVP):** Implement Option B (task mode only) to unblock Code Review Agent
- **Phase 2 (Enhancement):** Add project mode support with auto-detection
- Default to task mode for safety (doesn't create repos unexpectedly)

---

## Decision Outcome

**Chosen Option:** **Option B - Filesystem + Git (Task Mode)** with **Option E (Project Mode) as Future Enhancement**

### Rationale

1. **Best of Both Worlds:** Maintains telemetry database for PROBE-AI while adding human visibility
2. **Standard Workflow:** Leverages industry-standard git workflow (commit, PR, review)
3. **Tool Integration:** Works with existing developer tools (IDE, git, CI/CD)
4. **Future-Proof:** Supports multi-agent collaboration, human-in-the-loop, code review
5. **Meets All Must-Haves:** Human readability, version control, traceability, code review
6. **Flexible Architecture:** Option B (task mode) can be enhanced with Option E (project mode) later without breaking changes

### Phased Implementation

**Phase 1 (Immediate - Code Review Agent Unblocking):**
- Implement Option B (task mode only)
- Work in current working directory
- Create `artifacts/{task_id}/` for each task
- Write generated code to `src/`, `tests/`, etc. in current repo
- Auto-commit to current repo after each agent
- **Estimated effort:** 10 hours
- **Goal:** Unblock Code Review Agent implementation

**Phase 2 (Future Enhancement - Project Mode):**
- Implement Option E (project mode)
- Add `mode` parameter to Planning Agent (`"task"` or `"project"`)
- Support auto-detection based on requirements keywords
- Initialize new git repos for greenfield projects
- Add project registry database table
- **Estimated effort:** 8-12 hours
- **Goal:** Support complete project generation workflow

**Default Behavior:**
- Task mode (works in current directory)
- Safe for existing workflows
- No unexpected repo creation

### Implementation Strategy

**Phase 1: Core File I/O (2 hours)**
- Create `src/asp/utils/artifact_io.py` with functions:
  - `write_artifact_json(task_id, artifact_type, data)` - Write JSON
  - `write_artifact_markdown(task_id, artifact_type, data)` - Write MD
  - `read_artifact_json(task_id, artifact_type)` - Read JSON
  - `ensure_artifact_directory(task_id)` - Create dirs
- Create markdown renderers for each artifact type:
  - `render_plan_markdown(project_plan)` → plan.md
  - `render_design_markdown(design_spec)` → design.md
  - `render_review_markdown(review_report)` → review.md

**Phase 2: Git Integration (1 hour)**
- Create `src/asp/utils/git_utils.py` with functions:
  - `git_commit_artifact(task_id, agent_name, message)` - Auto-commit
  - `git_status_check()` - Verify clean working directory
  - `git_add_files(file_paths)` - Stage specific files
- Add safety checks:
  - Don't commit if working directory is dirty (unrelated changes)
  - Include task_id in commit message for traceability
  - Support `--no-commit` flag for testing

**Phase 3: Agent Updates (3-4 hours)**
- Update Planning Agent:
  - After generating ProjectPlan, write plan.json + plan.md
  - Git commit: "Add project plan for {task_id}"
- Update Design Agent:
  - After generating DesignSpecification, write design.json + design.md
  - Optionally extract API contracts → OpenAPI YAML
  - Optionally extract schemas → DDL SQL
  - Git commit: "Add design specification for {task_id}"
- Update Design Review Agent:
  - After generating DesignReviewReport, write design_review.json + design_review.md
  - Git commit: "Add design review for {task_id} - {PASS/FAIL}"
- Update Code Agent:
  - After generating code, write all files to src/, tests/, etc.
  - Write code_manifest.json with metadata
  - Git commit: "Implement {task_id}: {description}"
- Update Code Review Agent (NEW):
  - Read actual files from filesystem (not just in-memory)
  - Write code_review.json + code_review.md
  - Git commit: "Add code review for {task_id} - {PASS/FAIL}"

**Phase 4: Testing (1 hour)**
- Unit tests for artifact_io utilities
- Unit tests for git_utils
- E2E test: Run full pipeline, verify git history
- Manual test: Inspect artifacts in IDE

---

## Consequences

### Positive Consequences

1. **Developer Experience**
   - Can open plans/designs/code in IDE
   - Can search across artifacts with IDE tools
   - Can use git blame to see who/when/why

2. **Code Review Workflow**
   - Code Review Agent issues reference real files
   - Can click file:line to jump to issue
   - Can manually verify agent findings
   - Can create PRs for agent-generated code

3. **Traceability**
   - Git log shows complete pipeline execution
   - Easy to see: plan → design → design review → code → code review
   - Can trace any code back to original requirement

4. **CI/CD Integration**
   - Can run linters on generated code (black, ruff, mypy)
   - Can run formatters automatically
   - Can trigger builds on code commits
   - Can enforce quality gates (tests must pass)

5. **Collaboration**
   - Team can review plans before design
   - Team can review designs before code
   - Team can suggest changes via comments
   - Supports human-in-the-loop workflow

6. **Debugging**
   - Can diff plan v1 vs. v2 to see what changed
   - Can inspect what agent actually generated
   - Can reproduce issues from git history

### Negative Consequences

1. **Implementation Effort**
   - +6-8 hours implementation time
   - Need to update all existing agents (Planning, Design, Design Review, Code)
   - Need comprehensive testing

2. **Disk Space**
   - Artifacts stored twice (filesystem + database)
   - Git repo grows with each task
   - Generated code increases repo size
   - **Mitigation:** Use .gitignore for build artifacts, add cleanup scripts

3. **Git Commit Noise**
   - Many automated commits (1 per agent execution)
   - Could clutter git history
   - **Mitigation:** Use conventional commit messages, support squashing

4. **Complexity**
   - Need to handle git conflicts (if manual edits made)
   - Need to handle dirty working directory
   - Need to support --no-commit flag for testing
   - **Mitigation:** Clear error messages, documentation

5. **Testing Complexity**
   - Tests need to mock filesystem and git
   - Need to clean up test artifacts
   - E2E tests create real commits
   - **Mitigation:** Use temp directories, git worktrees for isolation

---

## Implementation Details

### 1. Artifact Directory Structure

```
artifacts/
├── {task_id}/
│   ├── plan.json                    # ProjectPlan (machine-readable)
│   ├── plan.md                      # Human-readable summary
│   ├── design.json                  # DesignSpecification
│   ├── design.md                    # Human-readable summary
│   ├── design.api_contracts.yaml   # OpenAPI spec (optional)
│   ├── design.schema.sql           # Database DDL (optional)
│   ├── design_review.json          # DesignReviewReport
│   ├── design_review.md            # Human-readable report
│   ├── code_manifest.json          # GeneratedCode metadata
│   ├── code_review.json            # CodeReviewReport
│   └── code_review.md              # Human-readable report
```

**Naming Convention:**
- `{artifact_type}.json` - Machine-readable (full Pydantic JSON)
- `{artifact_type}.md` - Human-readable (summary + highlights)
- `{artifact_type}.{subtype}.{ext}` - Extracted artifacts (API specs, schemas)

### 2. Markdown Rendering Examples

**plan.md:**
```markdown
# Project Plan: JWT-AUTH-001

**Task:** Implement JWT authentication for FastAPI application
**Estimated Effort:** 8 hours
**Estimated Cost:** $0.50

## Task Decomposition

### SU-001: JWT Token Generation
- **Complexity:** 3.2
- **Description:** Create endpoint to generate JWT tokens on successful login
- **Dependencies:** None

### SU-002: JWT Token Validation
- **Complexity:** 2.8
- **Description:** Middleware to validate JWT tokens on protected routes
- **Dependencies:** SU-001

## Cost Vector
- **Latency:** 45 seconds
- **Input Tokens:** 1,200
- **Output Tokens:** 800
- **Total Cost:** $0.50

---
*Generated by Planning Agent v1.0.0 on 2025-11-17 14:30:00*
```

**design_review.md:**
```markdown
# Design Review Report: JWT-AUTH-001

**Review Status:** ❌ FAIL
**Reviewed by:** Design Review Agent v1.0.0
**Date:** 2025-11-17 14:45:00

## Summary
- **Total Issues:** 3
- **Critical:** 1
- **High:** 2
- **Medium:** 0

## Critical Issues

### ISSUE-001: Password stored in plaintext
**Category:** Security
**Severity:** Critical
**Affected Phase:** Design
**Evidence:** users table, password column (VARCHAR)

User credentials vulnerable to breach; violates security best practices.

**Recommendation:** Use bcrypt or Argon2 for password hashing. Store hash + salt in password_hash column.

## High Issues

### ISSUE-002: Missing rate limiting on login endpoint
...

---
*Generated by Design Review Agent v1.0.0 on 2025-11-17 14:45:00*
```

**code_review.md:**
```markdown
# Code Review Report: JWT-AUTH-001

**Review Status:** ❌ FAIL
**Reviewed by:** Code Review Agent v1.0.0
**Date:** 2025-11-17 15:00:00

## Summary
- **Files Reviewed:** 8
- **Lines Reviewed:** 450
- **Total Issues:** 5
- **Critical:** 2
- **High:** 3

## Critical Issues

### CODE-ISSUE-001: SQL Injection Vulnerability
**Category:** Security
**Severity:** Critical
**Affected Phase:** Code
**File:** src/repositories/user_repository.py:45

```python
query = f"SELECT * FROM users WHERE username = '{username}'"
```

Raw string interpolation allows SQL injection attacks. Attacker can execute arbitrary SQL.

**Fix:** Use parameterized queries:
```python
query = "SELECT * FROM users WHERE username = ?"
cursor.execute(query, (username,))
```

---

## Specialist Results
- ✅ Testing Review: PASS (90% coverage, comprehensive tests)
- ✅ Standards Compliance: PASS (type hints, docstrings present)
- ❌ Security Review: FAIL (2 Critical issues)
- ⚠️  Performance Review: CONDITIONAL PASS (1 High issue)
- ⚠️  Code Quality: CONDITIONAL PASS (2 High issues)
- ✅ Maintainability: PASS (good logging, config)

---
*Generated by Code Review Agent v1.0.0 on 2025-11-17 15:00:00*
```

### 3. Git Commit Message Format

**Convention:** `{agent_name}: {action} for {task_id} [{status}]`

**Examples:**
```bash
git commit -m "Planning Agent: Add project plan for JWT-AUTH-001"
git commit -m "Design Agent: Add design specification for JWT-AUTH-001"
git commit -m "Design Review Agent: Review complete for JWT-AUTH-001 [PASS]"
git commit -m "Code Agent: Implement JWT-AUTH-001 - JWT authentication endpoints"
git commit -m "Code Review Agent: Review complete for JWT-AUTH-001 [FAIL - 2 Critical]"
```

**Benefits:**
- Easy to filter by agent: `git log --grep="Code Agent"`
- Easy to filter by task: `git log --grep="JWT-AUTH-001"`
- Easy to see status: `git log --grep="FAIL"`
- Conventional Commits compatible

### 4. API Changes

**Before (Database Only):**
```python
# Code Agent
generated_code = code_agent.execute(code_input)
# Returns GeneratedCode, stored in DB only
```

**After (Filesystem + Database):**
```python
# Code Agent
generated_code = code_agent.execute(
    code_input,
    write_to_filesystem=True,  # Default: True
    git_commit=True,           # Default: True
)
# Returns GeneratedCode
# Side effects:
#   1. Writes files to src/, tests/, etc.
#   2. Writes code_manifest.json to artifacts/{task_id}/
#   3. Stores in DB (telemetry)
#   4. Git commits all changes
```

**Testing Mode:**
```python
# Disable filesystem writes for unit tests
generated_code = code_agent.execute(
    code_input,
    write_to_filesystem=False,
    git_commit=False,
)
```

### 5. Backward Compatibility

**Guaranteed:**
- All existing Pydantic models unchanged
- All existing function signatures unchanged (new params are optional with defaults)
- All existing tests pass (default params preserve old behavior)
- Telemetry database storage still works

**Migration Path:**
- Old code: Continues working (no filesystem writes)
- New code: Opt-in with `write_to_filesystem=True`
- Can enable globally via config: `ASP_WRITE_ARTIFACTS=true`

---

## Alternatives Considered (Detailed)

### Alternative 1: Write Only Generated Code (Not Artifacts)

**Idea:** Write source files to disk, but keep plans/designs in DB only.

**Rejected Because:**
- Still no visibility into planning/design phase
- Cannot review designs before code generation
- Breaks traceability (code in git, design in DB)

### Alternative 2: Separate "Review Repo" for Artifacts

**Idea:** Create separate git repo for artifacts, main repo for code only.

**Rejected Because:**
- Complexity (manage 2 repos)
- Breaks single source of truth
- Hard to link code → artifacts across repos

### Alternative 3: Use Git Notes for Metadata

**Idea:** Store JSON artifacts as git notes on commits.

**Rejected Because:**
- Git notes not well supported in tools
- Hard to read/search notes
- Not visible in GitHub/GitLab UI

---

## Open Questions

### Q1: Should artifacts be .gitignored in some cases?

**Consideration:** Large artifacts (e.g., code_manifest.json with 50 files) could bloat repo.

**Recommendation:** Start with committing everything. Add .gitignore rules later if needed:
```gitignore
# Optional: Ignore derived artifacts (can be regenerated)
artifacts/**/*.md
artifacts/**/code_manifest.json
```

### Q2: How to handle multi-project repositories?

**Consideration:** If ASP manages multiple projects in one repo, need namespacing.

**Answer:** ✅ **ADDRESSED by Option E**

Two approaches depending on use case:

**Approach 1: Task Mode (Single Project per Repo)**
- Default behavior for feature development
- All tasks in one repo: `artifacts/{task_id}/plan.json`
- No namespacing needed (one project = one repo)

**Approach 2: Project Mode (Separate Repo per Project)**
- For greenfield projects
- Each project gets its own git repo: `~/asp_projects/{project_name}/`
- Natural isolation, no namespacing needed

**If using monorepo for multiple projects (advanced):**
```
artifacts/{project_id}/{task_id}/plan.json
```
But this is not recommended. Use separate repos instead (Option E).

### Q3: Should we support non-git version control (SVN, Mercurial)?

**Recommendation:** No. Git is industry standard. Can add later if needed.

### Q4: How to handle concurrent task execution?

**Consideration:** If 2 agents run simultaneously, git commits could conflict.

**Recommendation:** Use task-specific directories (no conflicts). If conflicts occur, use git merge strategies.

---

## Risks and Mitigations

### Risk 1: Git Repo Growth

**Risk:** Artifacts + code could grow repo to GB scale over time.

**Mitigation:**
- Use git LFS for large binary artifacts (if any)
- Add cleanup scripts to remove old artifact directories
- Use git shallow clones for CI/CD (don't need full history)
- Archive old tasks to separate "archive" branch

### Risk 2: Dirty Working Directory

**Risk:** If developer has uncommitted changes, agent cannot commit.

**Mitigation:**
- Check `git status` before committing
- If dirty, prompt user: "Uncommitted changes detected. Commit, stash, or skip git integration?"
- Support `--no-commit` flag to disable auto-commit

### Risk 3: Merge Conflicts

**Risk:** If developer manually edits agent-generated files, next agent run could conflict.

**Mitigation:**
- Agent-generated files have header comments: `# AUTO-GENERATED by Code Agent - DO NOT EDIT`
- If conflict detected, prompt user to resolve
- Consider using separate branches for agent work

### Risk 4: CI/CD Noise

**Risk:** Every agent commit triggers CI builds, wasting resources.

**Mitigation:**
- Use `[skip ci]` in commit messages for artifact-only commits
- Only trigger builds on Code Agent commits (actual code changes)
- Use commit message patterns to filter: `Planning Agent:` → skip, `Code Agent:` → build

---

## Success Metrics

### Implementation Success Criteria

- ✅ All agents write artifacts to filesystem
- ✅ All artifacts committed to git automatically
- ✅ Markdown renderers produce readable reports
- ✅ Code Review Agent reads from filesystem
- ✅ Git history shows complete pipeline execution
- ✅ Existing tests pass (backward compatibility)
- ✅ New tests cover file I/O and git integration

### User Success Criteria

- ✅ Developers can open artifacts in IDE
- ✅ Developers can review designs before code gen
- ✅ Code review issues link to actual files
- ✅ Git log shows clear pipeline traceability
- ✅ Can rollback to previous versions with `git revert`

### Quality Metrics

- Artifact write time: <500ms per artifact
- Git commit time: <2 seconds per commit
- No data loss (filesystem AND database always synced)
- 100% test coverage for artifact I/O utilities

---

## Timeline

| Phase | Description | Effort | Dependencies |
|-------|-------------|--------|--------------|
| 1 | Core File I/O utilities | 2 hours | None |
| 2 | Git integration utilities | 1 hour | Phase 1 |
| 3 | Markdown renderers | 2 hours | Phase 1 |
| 4 | Update Planning Agent | 30 min | Phase 1-3 |
| 5 | Update Design Agent | 30 min | Phase 1-3 |
| 6 | Update Design Review Agent | 30 min | Phase 1-3 |
| 7 | Update Code Agent | 1 hour | Phase 1-3 |
| 8 | Update Code Review Agent | 1 hour | Phase 1-3 |
| 9 | Testing | 1 hour | Phase 1-8 |
| 10 | Documentation | 30 min | Phase 1-9 |
| **Total** | | **10 hours** | |

**Can parallelize:** Phases 4-8 (agent updates) can be done in any order after phases 1-3.

---

## Related Decisions

- **Phase-Aware Feedback Architecture** (docs/error_correction_feedback_loops_decision.md) - Enables routing corrections via git history
- **Design Review Agent Multi-Specialist Architecture** (docs/design_review_agent_architecture_decision.md) - Established specialist pattern
- **Code Review Agent Implementation Plan** (docs/code_review_agent_implementation_plan.md) - Will be updated to use filesystem

---

## References

- **PSP Methodology:** Recommends documenting all artifacts for quality tracking
- **Git Workflow Best Practices:** Atomic commits, meaningful messages, traceability
- **OpenAPI Specification:** Standard for API contract documentation
- **Conventional Commits:** https://www.conventionalcommits.org/

---

## Decision Status

**Status:** ✅ **APPROVED** (Pending User Confirmation)

**Next Steps:**
1. Get user approval for Option B (Filesystem + Git)
2. Update Code Review Agent implementation plan to include artifact persistence
3. Implement Phase 1 (File I/O utilities) as foundation
4. Roll out to agents incrementally (Planning → Design → Design Review → Code → Code Review)

---

**Date of Decision:** 2025-11-17
**Revisit Date:** 2025-12-01 (after Code Review Agent implementation complete)
