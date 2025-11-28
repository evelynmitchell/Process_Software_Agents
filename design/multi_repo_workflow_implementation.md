# Multi-Repository Workflow Implementation Plan

**Created:** 2025-11-28 (Session 20251128.6)
**Status:** Planning
**Related Documents:**
- `design/HITL_QualityGate_Architecture.md` - Section 2.3 (Repository Management Strategy)
- `Summary/summary20251123.1.md` - Repository strategy session
- `Summary/summary20251123.2.md` - Test artifacts repository session
- `Summary/summary20251128.6.md` - Session summary

## Overview

This document outlines the implementation plan for enabling the ASP (Agentic Software Process) platform to work across multiple repositories. This includes checking out external repositories, managing workspaces, storing execution artifacts, and coordinating HITL approvals for multi-repo tasks.

## Background

### Repository Management Strategy

From HITL_QualityGate_Architecture.md Section 2.3.2, the decision matrix:

| Task Type | Repo Strategy | HITL Issue Location | Artifacts Location |
|-----------|---------------|--------------------|--------------------|
| Add feature to this project | Current repo, feature branch | Current repo | Current repo (`executions/`) |
| Fix bug in external repo | Checkout external, feature branch | **Current repo** (central) | Current repo (with refs) |
| Create new microservice | Create new repo | Current repo (planning), New repo (PRs) | Both repos (cross-linked) |
| Generate documentation | Current repo | Current repo | Current repo (`docs/`) |
| Analysis/research tasks | Current repo | Current repo | Current repo (`analysis/`) |

### Multi-Repository Task Workflow

The 5-step process for multi-repo tasks:

1. **Checkout** target repo into temporary workspace
2. **Create feature branch** in target repo
3. **Store execution artifacts** in Process_Software_Agents repo with cross-references
4. **Create HITL issue** in Process_Software_Agents repo (central approval)
5. **Create PR** in target repo once approved

### Centralized Orchestration Principle

The `Process_Software_Agents` repository serves as the **single source of truth** for:
- Agent orchestration state
- HITL approval records
- Execution metadata
- Process improvement tracking

**Rationale:**
1. **GitHub Issues HITL Integration** - Artifacts in same repo as issues enables seamless references
2. **Traceability** - Git history connects agent code, execution artifacts, and HITL decisions
3. **Simplicity** - No cross-repo coordination overhead
4. **Searchability** - Everything in one place for analysis

## Workflow Example

**Scenario:** Agent needs to fix authentication bug in external-api-service repo

**Steps:**
1. **Checkout** external-api-service into temporary workspace
2. **Create feature branch** `claude/fix-auth-bug-xyz` in external-api-service
3. **Store execution artifacts** in Process_Software_Agents:
   ```
   Process_Software_Agents/executions/2025-11-28_task-123/
   ├── metadata.json
   ├── code_review.md
   ├── test_results.json
   └── approval.md
   ```
4. **Create HITL issue** in Process_Software_Agents repo:
   ```markdown
   Title: [HITL Approval] Fix authentication bug in external-api-service

   - Target Repo: external-api-service
   - Branch: claude/fix-auth-bug-xyz
   - PR: external-api-service#456
   - Execution Record: executions/2025-11-28_task-123/
   - Quality Gate Status: Security scan found SQL injection risk
   ```
5. **Create PR** in external-api-service once approved

## Recommended Directory Structure

```
Process_Software_Agents/
├── src/                  # Agent implementation code
├── design/               # Architecture docs (HITL spec, etc.)
├── Summary/              # Session summaries
├── executions/           # Agent execution artifacts ⭐ NEW
│   ├── 2025-11-28_task-123/
│   │   ├── metadata.json
│   │   ├── code_review.md
│   │   ├── test_results.json
│   │   └── approval.md   # HITL decision record
├── pips/                 # Process Improvement Proposals ⭐ NEW
└── analysis/             # Research and analysis outputs
```

**Note:** The `executions/` and `pips/` directories are proposed but not yet created.

## Implementation Gap Analysis

### Status: ⚠️ Strategy Documented, Implementation Missing

The repository management strategy is well-documented in `design/HITL_QualityGate_Architecture.md` but needs implementation code.

### Missing Components

**High Priority:**
- [ ] Repository Manager Service implementation
- [ ] Workspace management utilities
- [ ] Artifact storage service
- [ ] Multi-repo orchestration logic

**Medium Priority:**
- [ ] Fork vs. checkout decision logic
- [ ] Cross-repo PR creation automation
- [ ] HITL integration for multi-repo tasks
- [ ] Cleanup and workspace lifecycle management

**Low Priority:**
- [ ] Developer guide for multi-repo tasks
- [ ] Advanced workspace configurations
- [ ] Parallel multi-repo task execution
- [ ] Workspace disk space monitoring

## Proposed Service Architecture

### 1. Repository Manager Service

**Purpose:** Manages repository checkout, fork, and workspace operations.

```python
class RepositoryManager:
    """Manages repository checkout, fork, and workspace operations."""

    def checkout_repository(self, repo_url: str, workspace_path: Path) -> Repository:
        """Clone repository into temporary workspace.

        Args:
            repo_url: URL of repository to clone
            workspace_path: Path to workspace directory

        Returns:
            Repository object representing the cloned repo
        """
        pass

    def create_feature_branch(self, repo: Repository, task_id: str) -> str:
        """Create feature branch for task.

        Args:
            repo: Repository object
            task_id: Unique task identifier

        Returns:
            Name of created branch
        """
        pass

    def fork_repository(self, repo_url: str) -> str:
        """Fork repository (for external contributions).

        Args:
            repo_url: URL of repository to fork

        Returns:
            URL of forked repository
        """
        pass

    def cleanup_workspace(self, workspace_path: Path):
        """Clean up temporary workspace after task completion.

        Args:
            workspace_path: Path to workspace directory to clean
        """
        pass
```

### 2. Artifact Manager Service

**Purpose:** Manages execution artifacts and cross-references.

```python
class ArtifactManager:
    """Manages execution artifacts and cross-references."""

    def create_execution_directory(self, task_id: str) -> Path:
        """Create directory for task execution artifacts.

        Args:
            task_id: Unique task identifier

        Returns:
            Path to created execution directory
        """
        pass

    def store_artifact(self, task_id: str, artifact_type: str, content: Any):
        """Store execution artifact with metadata.

        Args:
            task_id: Unique task identifier
            artifact_type: Type of artifact (e.g., 'code_review', 'test_results')
            content: Artifact content to store
        """
        pass

    def create_cross_reference(self, task_id: str, external_repo: str, pr_number: int):
        """Create cross-reference to external PR.

        Args:
            task_id: Unique task identifier
            external_repo: Repository name (e.g., 'org/repo')
            pr_number: Pull request number in external repo
        """
        pass
```

### 3. Multi-Repository Orchestrator

**Purpose:** Orchestrates tasks across multiple repositories.

```python
class MultiRepositoryOrchestrator:
    """Orchestrates tasks across multiple repositories."""

    def execute_multi_repo_task(self, task: Task) -> ExecutionResult:
        """Execute task that spans multiple repositories.

        Args:
            task: Task definition object

        Returns:
            Execution result with status and artifacts
        """
        pass

    def determine_repo_strategy(self, task: Task) -> RepoStrategy:
        """Determine whether to checkout, fork, or use current repo.

        Args:
            task: Task definition object

        Returns:
            Repository strategy (checkout, fork, or current)
        """
        pass
```

## Integration Points

### HITL Integration
- GitHub Issues creation in Process_Software_Agents repo
- Artifact references in issue body
- Cross-repo PR linking

### TSP Orchestrator Integration
- Multi-repo task detection
- Workspace lifecycle management
- Artifact storage coordination

### Quality Gates Integration
- External repo code review
- Security scanning across repos
- Test execution in target repo

## Key Design Decisions

### 1. Workspace Management

**Question:** Where should external repositories be checked out?

**Decision:** Use temporary directory (`/tmp/asp-workspaces/`)

**Rationale:**
- Isolation from main repository
- Automatic cleanup after task completion
- Easy disk space management
- Supports parallel task execution

**Implementation:**
```python
def get_workspace_path(task_id: str) -> Path:
    return Path(f"/tmp/asp-workspaces/{task_id}")
```

### 2. Fork vs. Checkout

**Question:** When should agents fork vs. checkout repositories?

**Decision:** Auto-detect via GitHub API permissions

**Decision Criteria:**
- **Checkout:** When agent has write access to target repo
- **Fork:** When contributing to external/third-party repos
- **Auto-detect:** Check permissions via GitHub API

**Implementation:**
```python
def determine_access_strategy(repo_url: str, github_token: str) -> str:
    """Determine access strategy based on permissions."""
    if has_write_access(repo_url, github_token):
        return "checkout"
    else:
        return "fork"
```

### 3. Artifact Organization

**Question:** How should artifacts be organized for multi-repo tasks?

**Decision:** Separate subdirectories per repository within execution directory

**Proposed Structure:**
```
executions/2025-11-28_task-123/
├── metadata.json              # Task metadata
├── target_repos.json          # List of repositories involved
├── process_software_agents/   # Artifacts for main repo
│   ├── code_review.md
│   └── test_results.json
├── external_api_service/      # Artifacts for external repo
│   ├── code_review.md
│   ├── test_results.json
│   └── pr_link.txt
└── approval.md                # HITL decision (consolidated)
```

### 4. HITL Approval Scope

**Question:** Should HITL approval be per-repo or per-task?

**Decision:** One approval per task (covers all repos)

**Rationale:**
- Simplicity - single approval workflow
- Atomic changes - all repos approved together
- Detailed breakdown in approval report shows per-repo changes

## Implementation Roadmap

### Phase 1: Directory Structure (2-3 hours)

**Scope:**
- Create `executions/`, `pips/`, `analysis/` directories
- Define metadata.json schema
- Create artifact storage utilities
- Document artifact organization

**Deliverables:**
- Directory structure created
- Schema documentation
- Basic artifact storage functions

### Phase 2: Repository Manager Service (4-6 hours) ⭐ RECOMMENDED FIRST

**Scope:**
- Create `RepositoryManager` service
- Implement checkout/fork logic
- Add workspace management
- Create tests using test_artifacts_repo

**Deliverables:**
- `src/services/repository_manager.py`
- Unit tests for repository operations
- Workspace cleanup utilities

**Value:** Enables all multi-repo workflows

### Phase 3: Artifact Manager Service (3-4 hours)

**Scope:**
- Create `ArtifactManager` service
- Implement artifact storage
- Add cross-reference utilities
- Create metadata schemas

**Deliverables:**
- `src/services/artifact_manager.py`
- Artifact storage tests
- Metadata schema documentation

### Phase 4: Multi-Repository Orchestrator (6-8 hours)

**Scope:**
- Extend TSP Orchestrator for multi-repo support
- Implement repo strategy decision logic
- Add workspace lifecycle management
- Integrate with HITL workflow

**Deliverables:**
- Multi-repo orchestration service
- Integration with existing TSP
- End-to-end multi-repo tests

**Prerequisites:** Repository Manager (Phase 2)

### Phase 5: Developer Guide (2-3 hours)

**Scope:**
- Step-by-step workflow guide
- Code examples
- Best practices
- Troubleshooting tips

**Deliverables:**
- `docs/multi_repo_workflow_guide.md`
- Usage examples
- Best practices documentation

## Testing Requirements

### Test Scenarios

**Repository Operations:**
- [ ] Checkout external repository and create feature branch
- [ ] Fork repository for external contributions
- [ ] Cleanup workspace after task completion
- [ ] Handle checkout errors (permissions, network)

**Artifact Management:**
- [ ] Store artifacts in Process_Software_Agents during external repo work
- [ ] Create cross-references to external PRs
- [ ] Retrieve artifacts for HITL review
- [ ] Handle multi-repo artifact organization

**HITL Integration:**
- [ ] Create HITL issue with cross-references
- [ ] Link to external repo PR
- [ ] Store approval decision
- [ ] Track approval status

**End-to-End Workflows:**
- [ ] Complete multi-repo task (checkout → develop → approve → PR)
- [ ] Multi-repo task spanning 3+ repositories
- [ ] Fork workflow for repositories without write access
- [ ] Parallel multi-repo task execution

### Test Infrastructure

- Use existing `test_artifacts_repo/` for isolated testing
- Create mock GitHub API responses
- Test workspace cleanup and isolation
- Verify artifact storage integrity

## Documentation Needs

**Missing Documentation:**
1. **Developer guide** for implementing multi-repo tasks
2. **Workspace management** best practices
3. **Fork vs. checkout decision tree** (detailed)
4. **Artifact storage schema** specification
5. **Cross-repo PR workflow** step-by-step guide

## Outstanding Risks and Considerations

### Technical Risks

**1. Workspace Disk Space**
- Risk: Multiple concurrent checkouts consuming disk space
- Mitigation: Implement cleanup policies, monitor disk usage

**2. Network/Permissions Failures**
- Risk: Repository checkout failures due to network or permissions
- Mitigation: Retry logic, clear error messages, fallback strategies

**3. Concurrent Task Isolation**
- Risk: Multiple tasks interfering with each other's workspaces
- Mitigation: Unique workspace paths per task, proper locking

### Process Risks

**1. Cross-Repo Coordination**
- Risk: Changes in one repo breaking dependent repos
- Mitigation: Comprehensive testing, clear dependency tracking

**2. HITL Approval Complexity**
- Risk: Approving multi-repo changes without full context
- Mitigation: Detailed approval reports, per-repo breakdowns

## Success Metrics

**Implementation Success:**
- [ ] All 3 service classes implemented and tested
- [ ] 100% test coverage for repository operations
- [ ] End-to-end multi-repo workflow functional
- [ ] Documentation complete

**Operational Success:**
- [ ] Successfully execute multi-repo task in production
- [ ] Zero workspace cleanup failures
- [ ] Sub-5-minute checkout times for typical repos
- [ ] Clear HITL approval workflows

## Next Steps

**Immediate Actions:**
1. Create directory structure (`executions/`, `pips/`, `analysis/`)
2. Implement Repository Manager Service (Phase 2)
3. Create initial test suite using test_artifacts_repo
4. Document workspace management patterns

**Follow-up Actions:**
1. Implement Artifact Manager Service (Phase 3)
2. Extend TSP Orchestrator for multi-repo (Phase 4)
3. Create developer guide (Phase 5)
4. Conduct end-to-end testing

## References

- `design/HITL_QualityGate_Architecture.md` - Section 2.3: Repository Management Strategy
- `Summary/summary20251123.1.md` - Repository strategy architecture session
- `Summary/summary20251123.2.md` - Test artifacts repository implementation
- `Summary/summary20251128.6.md` - Multi-repo workflow analysis session

---

**Document Status:** Planning
**Last Updated:** 2025-11-28
**Next Review:** After Phase 2 completion
