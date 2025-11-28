# ASP Repository Workflow Implementation Guide

**Status:** 🚧 Design Complete, Implementation Needed
**Last Updated:** November 28, 2025
**Session:** 20251128.6

---

## Executive Summary

This document provides a comprehensive implementation roadmap for enabling ASP agents to work with external repositories through checkout and fork workflows. The repository management strategy was designed in session 20251123.1 and documented in `design/HITL_QualityGate_Architecture.md` Section 2.3, but implementation code is missing.

**Current State:**
- ✅ Architecture documented (HITL_QualityGate_Architecture.md Section 2.3)
- ✅ Decision matrix defined (when to checkout/fork/use current repo)
- ✅ Multi-repository workflow specified (5-step process)
- ✅ Basic git utilities exist (git_utils.py for current repo only)
- ✅ Branch manager exists (branch_manager.py for local PR workflow)
- ❌ No external repository checkout capability
- ❌ No fork workflow implementation
- ❌ No workspace management for external repos
- ❌ No multi-repository orchestration

**This Document Provides:**
1. Gap analysis between architecture and implementation
2. Detailed implementation specifications
3. Code examples and API designs
4. Testing strategy
5. Phased rollout plan

---

## Table of Contents

- [Background](#background)
- [Architecture Overview](#architecture-overview)
- [Existing Implementation](#existing-implementation)
- [Implementation Gaps](#implementation-gaps)
- [Proposed Implementation](#proposed-implementation)
- [API Specifications](#api-specifications)
- [Testing Strategy](#testing-strategy)
- [Migration Path](#migration-path)
- [Security Considerations](#security-considerations)
- [References](#references)

---

## Background

### Problem Statement

ASP agents currently only operate within the Process_Software_Agents repository. To enable real-world workflows, agents need to:

1. **Fix bugs in external repositories** (e.g., fix auth bug in external-api-service)
2. **Add features to existing projects** (e.g., add logging to user-service)
3. **Create patches for dependencies** (e.g., fix upstream library issue)
4. **Coordinate multi-repo changes** (e.g., update API contract across 3 services)

### Design Foundation

Session 20251123.1 established the **Centralized Orchestration Principle**:

> The `Process_Software_Agents` repository serves as the **single source of truth** for:
> - Agent orchestration state
> - HITL approval records
> - Execution metadata
> - Process improvement tracking

This means:
- External repos are checked out to temporary workspaces
- Execution artifacts stored in Process_Software_Agents
- HITL approvals managed centrally
- Cross-repo PRs referenced in central approval issues

### Repository Strategy Decision Matrix

From HITL Architecture Section 2.3.2:

| Task Type | Repo Strategy | HITL Issue Location | Artifacts Location |
|-----------|---------------|--------------------|--------------------|
| Add feature to this project | Current repo, feature branch | Current repo | Current repo (`executions/`) |
| Fix bug in external repo | Checkout external, feature branch | **Current repo** (central) | Current repo (with refs) |
| Create new microservice | Create new repo | Current repo (planning), New repo (PRs) | Both repos (cross-linked) |
| Generate documentation | Current repo | Current repo | Current repo (`docs/`) |
| Analysis/research tasks | Current repo | Current repo | Current repo (`analysis/`) |

---

## Architecture Overview

### Multi-Repository Task Workflow

From HITL Architecture Section 2.3.8, the 5-step workflow for external repo modifications:

```
┌─────────────────────────────────────────────────────────────┐
│ Step 1: Checkout Target Repository                         │
│                                                             │
│  git clone https://github.com/org/external-api-service.git │
│           → /tmp/asp-workspaces/task-123/external-api-service/│
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ Step 2: Create Feature Branch                              │
│                                                             │
│  cd /tmp/asp-workspaces/task-123/external-api-service/     │
│  git checkout -b claude/fix-auth-bug-xyz                   │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ Step 3: Store Execution Artifacts (in Process_Software_Agents)│
│                                                             │
│  Process_Software_Agents/executions/2025-11-28_task-123/   │
│  ├── metadata.json                                         │
│  ├── code_review.md                                        │
│  ├── test_results.json                                     │
│  └── external_api_service/                                 │
│      ├── diff.patch                                        │
│      └── pr_link.txt                                       │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ Step 4: Create HITL Issue (in Process_Software_Agents)     │
│                                                             │
│  Title: [HITL Approval] Fix auth bug in external-api-service│
│  Body:                                                      │
│    - Target Repo: external-api-service                     │
│    - Branch: claude/fix-auth-bug-xyz                       │
│    - Execution Record: executions/2025-11-28_task-123/     │
│    - Quality Gate Status: PASS                             │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ Step 5: Create PR in External Repo (after approval)        │
│                                                             │
│  gh pr create --repo org/external-api-service \            │
│    --base main --head claude/fix-auth-bug-xyz \            │
│    --title "Fix authentication bug" \                      │
│    --body "See Process_Software_Agents#456 for approval"   │
└─────────────────────────────────────────────────────────────┘
```

### Directory Structure

**Process_Software_Agents Repository:**
```
Process_Software_Agents/
├── src/asp/
│   ├── agents/              # Existing agents
│   ├── orchestrators/       # Existing orchestrators
│   ├── approval/            # Existing approval services
│   ├── utils/
│   │   ├── git_utils.py     # ✅ Exists (current repo only)
│   │   └── repo_manager.py  # ❌ NEW - External repo management
│   └── repository/          # ❌ NEW - Repository services
│       ├── __init__.py
│       ├── workspace.py     # Workspace management
│       ├── checkout.py      # Clone/checkout operations
│       ├── fork.py          # Fork operations
│       └── artifacts.py     # Cross-repo artifact storage
├── executions/              # ❌ NEW - Execution artifacts
│   └── 2025-11-28_task-123/
│       ├── metadata.json
│       ├── code_review.md
│       └── external_api_service/
│           └── diff.patch
├── pips/                    # ❌ NEW - Process Improvement Proposals
└── analysis/                # ❌ NEW - Research outputs
```

**Temporary Workspace (on filesystem, not in git):**
```
/tmp/asp-workspaces/          # Or configurable workspace root
├── task-123/
│   ├── external-api-service/ # Cloned repository
│   │   ├── .git/
│   │   ├── src/
│   │   └── ...
│   └── user-service/        # Another repo for multi-repo tasks
│       └── ...
└── task-124/
    └── ...
```

---

## Existing Implementation

### What We Have

#### 1. git_utils.py (src/asp/utils/git_utils.py)

**Capabilities:**
- ✅ Check if directory is a git repository
- ✅ Check git status (clean/dirty)
- ✅ Stage files (`git add`)
- ✅ Create commits
- ✅ Get current branch
- ✅ Get git repository root

**Limitations:**
- ❌ Only works with current repository
- ❌ No clone/checkout of external repos
- ❌ No multi-repository support
- ❌ No workspace management

**Example Usage:**
```python
from asp.utils.git_utils import git_commit_artifact

# Commit artifacts in current repo
git_commit_artifact(
    task_id="JWT-AUTH-001",
    agent_name="Planning Agent",
    artifact_files=["artifacts/JWT-AUTH-001/plan.json"]
)
```

#### 2. branch_manager.py (src/asp/approval/branch_manager.py)

**Capabilities:**
- ✅ Create branches in a repository
- ✅ Commit agent output to branches
- ✅ Generate diffs between branches
- ✅ Manage git notes for reviews
- ✅ Delete branches

**Limitations:**
- ❌ Operates on single repository only (specified by repo_path)
- ❌ No external repository checkout
- ❌ No multi-repo coordination

**Example Usage:**
```python
from asp.approval.branch_manager import BranchManager

# Manage branches in current repo
manager = BranchManager(repo_path="/workspace/Process_Software_Agents")
manager.create_branch("review/task-123", "main")
manager.commit_output("review/task-123", output, "task-123", "CodeReview")
```

#### 3. TSPOrchestrator (src/asp/orchestrators/tsp_orchestrator.py)

**Capabilities:**
- ✅ Orchestrate 7 agents through TSP workflow
- ✅ Enforce quality gates
- ✅ HITL approval integration
- ✅ Artifact generation and storage

**Limitations:**
- ❌ No multi-repository task detection
- ❌ No workspace lifecycle management
- ❌ Assumes all work happens in current repo

---

## Implementation Gaps

### Critical Gaps

1. **External Repository Checkout** ❌
   - No ability to clone external repositories
   - No workspace directory management
   - No cleanup after task completion

2. **Fork Workflow** ❌
   - No GitHub fork creation
   - No upstream/origin remote configuration
   - No fork sync capabilities

3. **Multi-Repository Orchestration** ❌
   - TSPOrchestrator doesn't detect multi-repo tasks
   - No coordination across multiple workspaces
   - No cross-repo artifact linking

4. **Workspace Management** ❌
   - No temporary workspace creation
   - No isolation between concurrent tasks
   - No disk space monitoring
   - No automatic cleanup

5. **Artifact Cross-Referencing** ❌
   - No linking between execution artifacts and external PRs
   - No structured metadata for multi-repo tasks
   - No external repo diff storage

### Medium Priority Gaps

6. **Access Control** ⚠️
   - No permission checking (fork vs checkout decision)
   - No GitHub token management for external repos
   - No handling of private repositories

7. **Directory Structure** ⚠️
   - `executions/` directory not created
   - `pips/` directory not created
   - `analysis/` directory not created

### Low Priority Gaps

8. **Advanced Features** 📋
   - No parallel multi-repo task execution
   - No workspace caching/reuse
   - No incremental clone/shallow clone support

---

## Proposed Implementation

### Phase 1: Workspace Management (2-3 hours)

**Goal:** Create infrastructure for temporary workspace management

**Deliverables:**

1. **WorkspaceManager Class** (`src/asp/repository/workspace.py`)

```python
"""
Workspace management for multi-repository tasks.

Provides isolated workspaces for external repository operations.
"""

from pathlib import Path
from typing import Optional
import tempfile
import shutil
import logging

logger = logging.getLogger(__name__)


class WorkspaceManager:
    """Manages temporary workspaces for multi-repo tasks."""

    def __init__(self, workspace_root: Optional[Path] = None):
        """
        Initialize WorkspaceManager.

        Args:
            workspace_root: Root directory for workspaces (default: /tmp/asp-workspaces)
        """
        self.workspace_root = workspace_root or Path(tempfile.gettempdir()) / "asp-workspaces"
        self.workspace_root.mkdir(parents=True, exist_ok=True)

    def create_workspace(self, task_id: str) -> Path:
        """
        Create isolated workspace for task.

        Args:
            task_id: Unique task identifier

        Returns:
            Path to workspace directory

        Example:
            >>> manager = WorkspaceManager()
            >>> workspace = manager.create_workspace("task-123")
            >>> print(workspace)
            /tmp/asp-workspaces/task-123
        """
        workspace_path = self.workspace_root / task_id
        workspace_path.mkdir(parents=True, exist_ok=True)
        logger.info(f"Created workspace: {workspace_path}")
        return workspace_path

    def cleanup_workspace(self, task_id: str) -> None:
        """
        Remove workspace and all contents.

        Args:
            task_id: Task identifier

        Example:
            >>> manager = WorkspaceManager()
            >>> manager.cleanup_workspace("task-123")
        """
        workspace_path = self.workspace_root / task_id
        if workspace_path.exists():
            shutil.rmtree(workspace_path)
            logger.info(f"Cleaned up workspace: {workspace_path}")

    def get_workspace(self, task_id: str) -> Optional[Path]:
        """
        Get existing workspace path.

        Args:
            task_id: Task identifier

        Returns:
            Path to workspace if exists, None otherwise
        """
        workspace_path = self.workspace_root / task_id
        return workspace_path if workspace_path.exists() else None

    def list_workspaces(self) -> list[str]:
        """
        List all active workspaces.

        Returns:
            List of task IDs with active workspaces
        """
        if not self.workspace_root.exists():
            return []

        return [d.name for d in self.workspace_root.iterdir() if d.is_dir()]

    def get_workspace_size(self, task_id: str) -> int:
        """
        Calculate total size of workspace in bytes.

        Args:
            task_id: Task identifier

        Returns:
            Total size in bytes, or 0 if workspace doesn't exist
        """
        workspace_path = self.workspace_root / task_id
        if not workspace_path.exists():
            return 0

        total_size = 0
        for path in workspace_path.rglob('*'):
            if path.is_file():
                total_size += path.stat().st_size

        return total_size
```

2. **Directory Creation Script**

```bash
# scripts/init_execution_directories.sh

#!/bin/bash
# Initialize directory structure for execution artifacts

set -e

REPO_ROOT=$(git rev-parse --show-toplevel)

echo "Creating execution artifact directories..."

mkdir -p "$REPO_ROOT/executions"
mkdir -p "$REPO_ROOT/pips"
mkdir -p "$REPO_ROOT/analysis"

# Create README files
cat > "$REPO_ROOT/executions/README.md" <<EOF
# Execution Artifacts

This directory contains artifacts from agent task executions.

## Structure

Each subdirectory corresponds to a task execution:

\`\`\`
executions/
├── 2025-11-28_task-123/
│   ├── metadata.json          # Task metadata
│   ├── code_review.md         # Quality gate reports
│   ├── test_results.json      # Test results
│   └── external_repos/        # Cross-repo artifacts
│       └── external-api-service/
│           └── diff.patch
└── 2025-11-28_task-124/
    └── ...
\`\`\`

## Retention Policy

- Keep artifacts for 90 days
- Archive on task completion
- Clean up failed/cancelled tasks after 30 days
EOF

echo "✅ Directory structure created"
```

**Tests:**
- `tests/test_workspace_manager.py` - Comprehensive workspace management tests

---

### Phase 2: Repository Manager (4-6 hours)

**Goal:** Implement external repository checkout and fork capabilities

**Deliverables:**

1. **RepositoryManager Class** (`src/asp/repository/checkout.py`)

```python
"""
Repository checkout and clone management.

Handles cloning external repositories into workspaces.
"""

import subprocess
import logging
from pathlib import Path
from typing import Optional, Dict, Any
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class RepositoryInfo:
    """Information about a checked-out repository."""
    url: str
    local_path: Path
    default_branch: str
    remotes: Dict[str, str]


class RepositoryManager:
    """Manages repository checkout and clone operations."""

    def __init__(self, workspace_manager):
        """
        Initialize RepositoryManager.

        Args:
            workspace_manager: WorkspaceManager instance for workspace creation
        """
        self.workspace_manager = workspace_manager

    def checkout_repository(
        self,
        repo_url: str,
        task_id: str,
        branch: Optional[str] = None,
        depth: Optional[int] = None
    ) -> RepositoryInfo:
        """
        Clone repository into task workspace.

        Args:
            repo_url: Repository URL (https or ssh)
            task_id: Task identifier
            branch: Optional specific branch to checkout
            depth: Optional shallow clone depth (e.g., 1 for latest commit only)

        Returns:
            RepositoryInfo with clone details

        Example:
            >>> manager = RepositoryManager(workspace_manager)
            >>> repo_info = manager.checkout_repository(
            ...     "https://github.com/org/external-api-service.git",
            ...     "task-123"
            ... )
            >>> print(repo_info.local_path)
            /tmp/asp-workspaces/task-123/external-api-service
        """
        # Get or create workspace
        workspace_path = self.workspace_manager.get_workspace(task_id)
        if not workspace_path:
            workspace_path = self.workspace_manager.create_workspace(task_id)

        # Extract repo name from URL
        repo_name = self._extract_repo_name(repo_url)
        repo_path = workspace_path / repo_name

        # Check if already cloned
        if repo_path.exists():
            logger.info(f"Repository already cloned at {repo_path}")
            return self._get_repo_info(repo_url, repo_path)

        # Build clone command
        cmd = ["git", "clone"]
        if depth:
            cmd.extend(["--depth", str(depth)])
        if branch:
            cmd.extend(["--branch", branch])
        cmd.extend([repo_url, str(repo_path)])

        # Clone repository
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True
            )
            logger.info(f"Cloned {repo_url} to {repo_path}")

        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to clone {repo_url}: {e.stderr}")
            raise

        return self._get_repo_info(repo_url, repo_path)

    def create_feature_branch(
        self,
        repo_path: Path,
        branch_name: str,
        base_branch: Optional[str] = None
    ) -> str:
        """
        Create feature branch in repository.

        Args:
            repo_path: Path to repository
            branch_name: Name for new branch
            base_branch: Base branch (default: current branch)

        Returns:
            Created branch name

        Example:
            >>> manager.create_feature_branch(
            ...     Path("/tmp/asp-workspaces/task-123/external-api-service"),
            ...     "claude/fix-auth-bug-xyz"
            ... )
            'claude/fix-auth-bug-xyz'
        """
        # Checkout base branch if specified
        if base_branch:
            subprocess.run(
                ["git", "checkout", base_branch],
                cwd=repo_path,
                capture_output=True,
                check=True
            )

        # Create and checkout feature branch
        subprocess.run(
            ["git", "checkout", "-b", branch_name],
            cwd=repo_path,
            capture_output=True,
            check=True
        )

        logger.info(f"Created branch {branch_name} in {repo_path.name}")
        return branch_name

    def _extract_repo_name(self, repo_url: str) -> str:
        """
        Extract repository name from URL.

        Args:
            repo_url: Repository URL

        Returns:
            Repository name (without .git suffix)

        Example:
            >>> self._extract_repo_name("https://github.com/org/repo.git")
            'repo'
        """
        # Handle both https and ssh URLs
        name = repo_url.rstrip('/').split('/')[-1]
        if name.endswith('.git'):
            name = name[:-4]
        return name

    def _get_repo_info(self, repo_url: str, repo_path: Path) -> RepositoryInfo:
        """Get repository information."""
        # Get default branch
        result = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=repo_path,
            capture_output=True,
            text=True,
            check=True
        )
        default_branch = result.stdout.strip()

        # Get remotes
        result = subprocess.run(
            ["git", "remote", "-v"],
            cwd=repo_path,
            capture_output=True,
            text=True,
            check=True
        )
        remotes = self._parse_remotes(result.stdout)

        return RepositoryInfo(
            url=repo_url,
            local_path=repo_path,
            default_branch=default_branch,
            remotes=remotes
        )

    def _parse_remotes(self, remote_output: str) -> Dict[str, str]:
        """Parse git remote -v output."""
        remotes = {}
        for line in remote_output.strip().split('\n'):
            if line:
                parts = line.split()
                if len(parts) >= 2:
                    name = parts[0]
                    url = parts[1]
                    if '(fetch)' in line:
                        remotes[name] = url
        return remotes
```

2. **Fork Manager** (`src/asp/repository/fork.py`)

```python
"""
GitHub fork management for ASP platform.

Handles repository forking for external contributions.
"""

import logging
import subprocess
from pathlib import Path
from typing import Optional
import os

logger = logging.getLogger(__name__)


class ForkManager:
    """Manages GitHub repository forks."""

    def __init__(self, github_token: Optional[str] = None):
        """
        Initialize ForkManager.

        Args:
            github_token: GitHub personal access token (or use GITHUB_TOKEN env var)
        """
        self.github_token = github_token or os.getenv("GITHUB_TOKEN")

    def fork_repository(self, repo_url: str) -> str:
        """
        Fork repository using GitHub CLI.

        Args:
            repo_url: Repository URL to fork

        Returns:
            Fork URL

        Example:
            >>> fork_manager = ForkManager()
            >>> fork_url = fork_manager.fork_repository(
            ...     "https://github.com/upstream/repo"
            ... )
            >>> print(fork_url)
            https://github.com/your-username/repo
        """
        # Extract owner/repo from URL
        owner_repo = self._extract_owner_repo(repo_url)

        # Fork using gh CLI
        try:
            result = subprocess.run(
                ["gh", "repo", "fork", owner_repo, "--remote=false"],
                capture_output=True,
                text=True,
                check=True,
                env={**os.environ, "GH_TOKEN": self.github_token} if self.github_token else None
            )

            # Parse fork URL from output
            fork_url = result.stdout.strip().split('\n')[-1]
            logger.info(f"Forked {repo_url} to {fork_url}")
            return fork_url

        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to fork {repo_url}: {e.stderr}")
            raise

    def has_write_access(self, repo_url: str) -> bool:
        """
        Check if agent has write access to repository.

        Args:
            repo_url: Repository URL

        Returns:
            True if write access granted

        Example:
            >>> fork_manager = ForkManager()
            >>> if fork_manager.has_write_access("https://github.com/org/repo"):
            ...     print("Can push directly")
            ... else:
            ...     print("Need to fork")
        """
        owner_repo = self._extract_owner_repo(repo_url)

        try:
            result = subprocess.run(
                ["gh", "api", f"/repos/{owner_repo}"],
                capture_output=True,
                text=True,
                check=True,
                env={**os.environ, "GH_TOKEN": self.github_token} if self.github_token else None
            )

            # Check permissions in JSON response
            import json
            repo_data = json.loads(result.stdout)
            permissions = repo_data.get("permissions", {})
            return permissions.get("push", False)

        except (subprocess.CalledProcessError, json.JSONDecodeError, KeyError):
            # Conservative: assume no access if check fails
            return False

    def _extract_owner_repo(self, repo_url: str) -> str:
        """
        Extract owner/repo from GitHub URL.

        Args:
            repo_url: GitHub repository URL

        Returns:
            String in format "owner/repo"

        Example:
            >>> self._extract_owner_repo("https://github.com/org/repo.git")
            'org/repo'
        """
        # Remove .git suffix
        url = repo_url.rstrip('/').replace('.git', '')

        # Extract from https://github.com/owner/repo
        if 'github.com/' in url:
            parts = url.split('github.com/')[1].split('/')
            return f"{parts[0]}/{parts[1]}"

        raise ValueError(f"Invalid GitHub URL: {repo_url}")
```

**Tests:**
- `tests/test_repository_manager.py`
- `tests/test_fork_manager.py`

---

### Phase 3: Artifact Manager (2-3 hours)

**Goal:** Manage execution artifacts with cross-repo references

**Deliverables:**

1. **ArtifactManager Class** (`src/asp/repository/artifacts.py`)

```python
"""
Execution artifact management with multi-repository support.

Stores artifacts in Process_Software_Agents/executions/ with cross-repo linking.
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)


@dataclass
class ExternalRepoReference:
    """Reference to external repository in multi-repo task."""
    repo_url: str
    branch_name: str
    pr_number: Optional[int] = None
    pr_url: Optional[str] = None
    commit_sha: Optional[str] = None


@dataclass
class TaskMetadata:
    """Metadata for task execution."""
    task_id: str
    created_at: str
    task_type: str
    status: str
    primary_repo: str  # "current" or external repo URL
    external_repos: List[ExternalRepoReference]
    agent_sequence: List[str]
    quality_gates: Dict[str, str]  # gate_name -> status
    hitl_approval: Optional[Dict[str, Any]] = None


class ArtifactManager:
    """Manages execution artifacts for multi-repository tasks."""

    def __init__(self, process_repo_root: Path):
        """
        Initialize ArtifactManager.

        Args:
            process_repo_root: Root of Process_Software_Agents repository
        """
        self.process_repo_root = Path(process_repo_root)
        self.executions_dir = self.process_repo_root / "executions"
        self.executions_dir.mkdir(parents=True, exist_ok=True)

    def create_execution_directory(
        self,
        task_id: str,
        task_type: str,
        primary_repo: str = "current"
    ) -> Path:
        """
        Create directory for task execution artifacts.

        Args:
            task_id: Unique task identifier
            task_type: Type of task (e.g., "bug_fix", "feature", "analysis")
            primary_repo: Primary repository ("current" or URL)

        Returns:
            Path to execution directory

        Example:
            >>> manager = ArtifactManager(Path("/workspace/Process_Software_Agents"))
            >>> exec_dir = manager.create_execution_directory(
            ...     "2025-11-28_task-123",
            ...     "bug_fix",
            ...     "https://github.com/org/external-api-service"
            ... )
        """
        exec_dir = self.executions_dir / task_id
        exec_dir.mkdir(parents=True, exist_ok=True)

        # Initialize metadata
        metadata = TaskMetadata(
            task_id=task_id,
            created_at=datetime.now().isoformat(),
            task_type=task_type,
            status="in_progress",
            primary_repo=primary_repo,
            external_repos=[],
            agent_sequence=[],
            quality_gates={}
        )

        self._write_metadata(exec_dir, metadata)
        logger.info(f"Created execution directory: {exec_dir}")
        return exec_dir

    def store_artifact(
        self,
        task_id: str,
        artifact_name: str,
        content: str,
        artifact_type: str = "text"
    ) -> Path:
        """
        Store artifact file.

        Args:
            task_id: Task identifier
            artifact_name: Filename for artifact
            content: Artifact content
            artifact_type: Type of artifact ("text", "json", "markdown")

        Returns:
            Path to stored artifact

        Example:
            >>> manager.store_artifact(
            ...     "2025-11-28_task-123",
            ...     "code_review.md",
            ...     "# Code Review Report\\n..."
            ... )
        """
        exec_dir = self.executions_dir / task_id
        artifact_path = exec_dir / artifact_name

        artifact_path.parent.mkdir(parents=True, exist_ok=True)
        artifact_path.write_text(content)

        logger.info(f"Stored artifact: {artifact_path}")
        return artifact_path

    def add_external_repo_reference(
        self,
        task_id: str,
        repo_url: str,
        branch_name: str,
        pr_number: Optional[int] = None,
        pr_url: Optional[str] = None
    ) -> None:
        """
        Add reference to external repository.

        Args:
            task_id: Task identifier
            repo_url: External repository URL
            branch_name: Branch created in external repo
            pr_number: PR number if created
            pr_url: PR URL if created

        Example:
            >>> manager.add_external_repo_reference(
            ...     "2025-11-28_task-123",
            ...     "https://github.com/org/external-api-service",
            ...     "claude/fix-auth-bug-xyz",
            ...     pr_number=456,
            ...     pr_url="https://github.com/org/external-api-service/pull/456"
            ... )
        """
        metadata = self._read_metadata(task_id)

        ref = ExternalRepoReference(
            repo_url=repo_url,
            branch_name=branch_name,
            pr_number=pr_number,
            pr_url=pr_url
        )

        metadata.external_repos.append(ref)
        self._write_metadata(self.executions_dir / task_id, metadata)

        logger.info(f"Added external repo reference: {repo_url}")

    def update_task_status(
        self,
        task_id: str,
        status: str,
        quality_gate: Optional[str] = None,
        gate_status: Optional[str] = None
    ) -> None:
        """
        Update task execution status.

        Args:
            task_id: Task identifier
            status: Task status ("in_progress", "completed", "failed")
            quality_gate: Quality gate name (e.g., "CodeReview")
            gate_status: Gate status ("PASS", "FAIL", "OVERRIDE")
        """
        metadata = self._read_metadata(task_id)
        metadata.status = status

        if quality_gate and gate_status:
            metadata.quality_gates[quality_gate] = gate_status

        self._write_metadata(self.executions_dir / task_id, metadata)

    def _read_metadata(self, task_id: str) -> TaskMetadata:
        """Read metadata file."""
        metadata_path = self.executions_dir / task_id / "metadata.json"
        if not metadata_path.exists():
            raise FileNotFoundError(f"Metadata not found for task {task_id}")

        data = json.loads(metadata_path.read_text())

        # Convert external_repos dicts back to dataclass instances
        external_repos = [
            ExternalRepoReference(**ref) for ref in data.get("external_repos", [])
        ]
        data["external_repos"] = external_repos

        return TaskMetadata(**data)

    def _write_metadata(self, exec_dir: Path, metadata: TaskMetadata) -> None:
        """Write metadata file."""
        metadata_path = exec_dir / "metadata.json"

        # Convert dataclass to dict for JSON serialization
        data = asdict(metadata)

        metadata_path.write_text(json.dumps(data, indent=2))
```

**Tests:**
- `tests/test_artifact_manager.py`

---

### Phase 4: Multi-Repository Orchestrator Integration (6-8 hours)

**Goal:** Integrate multi-repo capabilities into TSPOrchestrator

**Deliverables:**

1. **Multi-Repository Support in TSPOrchestrator**

Extend `src/asp/orchestrators/tsp_orchestrator.py`:

```python
# Add to TSPOrchestrator class

def execute_multi_repo_task(
    self,
    requirements: TaskRequirements,
    target_repo_url: str,
    workspace_manager: WorkspaceManager,
    approval_service: Optional[ApprovalService] = None
) -> TSPExecutionResult:
    """
    Execute task in external repository.

    Args:
        requirements: Task requirements
        target_repo_url: External repository URL
        workspace_manager: Workspace manager instance
        approval_service: Optional HITL approval service

    Returns:
        Execution result with artifacts in Process_Software_Agents

    Example:
        >>> orchestrator = TSPOrchestrator()
        >>> workspace_manager = WorkspaceManager()
        >>> result = orchestrator.execute_multi_repo_task(
        ...     requirements=TaskRequirements(name="Fix auth bug", ...),
        ...     target_repo_url="https://github.com/org/external-api-service",
        ...     workspace_manager=workspace_manager
        ... )
    """
    # 1. Determine repo strategy (checkout or fork)
    fork_manager = ForkManager()
    if fork_manager.has_write_access(target_repo_url):
        strategy = "checkout"
    else:
        strategy = "fork"
        target_repo_url = fork_manager.fork_repository(target_repo_url)

    # 2. Checkout repository to workspace
    repo_manager = RepositoryManager(workspace_manager)
    repo_info = repo_manager.checkout_repository(
        target_repo_url,
        requirements.task_id
    )

    # 3. Create feature branch
    branch_name = f"claude/{requirements.task_id}"
    repo_manager.create_feature_branch(
        repo_info.local_path,
        branch_name
    )

    # 4. Execute TSP workflow in external repo
    # (Modify agent execution to work in repo_info.local_path)
    result = self._execute_workflow_in_repo(
        requirements,
        repo_info.local_path,
        approval_service
    )

    # 5. Store artifacts in Process_Software_Agents
    artifact_manager = ArtifactManager(Path.cwd())
    exec_dir = artifact_manager.create_execution_directory(
        requirements.task_id,
        "external_repo_task",
        target_repo_url
    )

    # Store all agent outputs
    artifact_manager.store_artifact(
        requirements.task_id,
        "plan.json",
        result.project_plan.model_dump_json()
    )

    # 6. Create PR if approved
    if result.overall_status == "COMPLETE":
        pr_url = self._create_pull_request(
            repo_info.local_path,
            target_repo_url,
            branch_name,
            requirements
        )

        artifact_manager.add_external_repo_reference(
            requirements.task_id,
            target_repo_url,
            branch_name,
            pr_url=pr_url
        )

    # 7. Cleanup workspace
    workspace_manager.cleanup_workspace(requirements.task_id)

    return result
```

2. **Repo Strategy Detection**

Add to TSPOrchestrator:

```python
def determine_repo_strategy(
    self,
    requirements: TaskRequirements
) -> tuple[str, Optional[str]]:
    """
    Determine repository strategy for task.

    Returns:
        Tuple of (strategy, target_repo_url)
        strategy: "current", "checkout", or "fork"
        target_repo_url: External repo URL or None for current
    """
    # Parse requirements for repo references
    # Look for keywords: "in <repo>", "external-api-service", GitHub URLs

    # Simple heuristic for now
    if "current" in requirements.description.lower():
        return ("current", None)

    # Check for GitHub URL in description
    import re
    github_pattern = r'https://github\.com/[\w-]+/[\w-]+'
    match = re.search(github_pattern, requirements.description)
    if match:
        repo_url = match.group(0)
        return ("checkout", repo_url)

    return ("current", None)
```

**Tests:**
- `tests/test_multi_repo_orchestrator.py`
- `tests/test_external_repo_workflow_e2e.py` (End-to-end test)

---

## API Specifications

### WorkspaceManager API

```python
class WorkspaceManager:
    def __init__(self, workspace_root: Optional[Path] = None)
    def create_workspace(self, task_id: str) -> Path
    def cleanup_workspace(self, task_id: str) -> None
    def get_workspace(self, task_id: str) -> Optional[Path]
    def list_workspaces(self) -> list[str]
    def get_workspace_size(self, task_id: str) -> int
```

### RepositoryManager API

```python
class RepositoryManager:
    def __init__(self, workspace_manager: WorkspaceManager)
    def checkout_repository(
        self,
        repo_url: str,
        task_id: str,
        branch: Optional[str] = None,
        depth: Optional[int] = None
    ) -> RepositoryInfo
    def create_feature_branch(
        self,
        repo_path: Path,
        branch_name: str,
        base_branch: Optional[str] = None
    ) -> str
```

### ForkManager API

```python
class ForkManager:
    def __init__(self, github_token: Optional[str] = None)
    def fork_repository(self, repo_url: str) -> str
    def has_write_access(self, repo_url: str) -> bool
```

### ArtifactManager API

```python
class ArtifactManager:
    def __init__(self, process_repo_root: Path)
    def create_execution_directory(
        self,
        task_id: str,
        task_type: str,
        primary_repo: str = "current"
    ) -> Path
    def store_artifact(
        self,
        task_id: str,
        artifact_name: str,
        content: str,
        artifact_type: str = "text"
    ) -> Path
    def add_external_repo_reference(
        self,
        task_id: str,
        repo_url: str,
        branch_name: str,
        pr_number: Optional[int] = None,
        pr_url: Optional[str] = None
    ) -> None
    def update_task_status(
        self,
        task_id: str,
        status: str,
        quality_gate: Optional[str] = None,
        gate_status: Optional[str] = None
    ) -> None
```

---

## Testing Strategy

### Unit Tests

**Phase 1: Workspace Management**
```python
# tests/test_workspace_manager.py

def test_create_workspace():
    """Test workspace creation."""

def test_cleanup_workspace():
    """Test workspace cleanup."""

def test_list_workspaces():
    """Test listing active workspaces."""

def test_get_workspace_size():
    """Test workspace size calculation."""
```

**Phase 2: Repository Management**
```python
# tests/test_repository_manager.py

def test_checkout_repository():
    """Test repository checkout."""

def test_create_feature_branch():
    """Test feature branch creation."""

def test_extract_repo_name():
    """Test repository name extraction."""

# tests/test_fork_manager.py

def test_has_write_access():
    """Test permission checking."""

def test_extract_owner_repo():
    """Test owner/repo extraction."""
```

**Phase 3: Artifact Management**
```python
# tests/test_artifact_manager.py

def test_create_execution_directory():
    """Test execution directory creation."""

def test_store_artifact():
    """Test artifact storage."""

def test_add_external_repo_reference():
    """Test external repo reference tracking."""

def test_update_task_status():
    """Test task status updates."""
```

### Integration Tests

```python
# tests/test_multi_repo_integration.py

def test_checkout_and_branch_workflow():
    """Test complete checkout + branch creation workflow."""

def test_artifact_storage_multi_repo():
    """Test artifact storage for multi-repo task."""

def test_workspace_lifecycle():
    """Test workspace creation, use, and cleanup."""
```

### End-to-End Tests

```python
# tests/test_external_repo_workflow_e2e.py

def test_complete_external_repo_task():
    """
    End-to-end test of external repository task:
    1. Create workspace
    2. Checkout external repo
    3. Create feature branch
    4. Execute TSP workflow
    5. Store artifacts in Process_Software_Agents
    6. Create PR
    7. Cleanup workspace
    """

def test_fork_workflow_e2e():
    """End-to-end test of fork workflow for repos without write access."""

def test_multi_repo_task_e2e():
    """End-to-end test spanning multiple repositories."""
```

### Test Data

Use `test_artifacts_repo/` (from session 20251123.2) as external repository for testing:

```python
# Leverage existing test repository infrastructure
TEST_REPO_PATH = Path("/workspace/test_artifacts_repo")

def setup_test_repository():
    """Initialize test_artifacts_repo for multi-repo testing."""
    subprocess.run(
        ["bash", "scripts/init_test_artifacts_repo.sh"],
        check=True
    )
```

---

## Migration Path

### Step 1: Create Directory Structure (15 minutes)

```bash
# Run directory initialization
bash scripts/init_execution_directories.sh

# Verify structure
ls -la executions/ pips/ analysis/
```

### Step 2: Deploy Workspace Manager (1 hour)

1. Implement `src/asp/repository/workspace.py`
2. Create tests in `tests/test_workspace_manager.py`
3. Run tests: `pytest tests/test_workspace_manager.py -v`
4. Commit: "Add WorkspaceManager for multi-repo task isolation"

### Step 3: Deploy Repository Manager (2 hours)

1. Implement `src/asp/repository/checkout.py`
2. Create tests
3. Run tests
4. Commit: "Add RepositoryManager for external repo checkout"

### Step 4: Deploy Fork Manager (2 hours)

1. Implement `src/asp/repository/fork.py`
2. Create tests
3. Run tests
4. Commit: "Add ForkManager for GitHub fork workflows"

### Step 5: Deploy Artifact Manager (2 hours)

1. Implement `src/asp/repository/artifacts.py`
2. Create tests
3. Run tests
4. Commit: "Add ArtifactManager for multi-repo execution tracking"

### Step 6: Integrate with TSPOrchestrator (4 hours)

1. Add multi-repo methods to TSPOrchestrator
2. Update agent execution to support external repos
3. Create integration tests
4. Commit: "Integrate multi-repo capabilities into TSPOrchestrator"

### Step 7: End-to-End Validation (2 hours)

1. Create E2E test using test_artifacts_repo
2. Run full multi-repo workflow
3. Validate artifacts stored correctly
4. Commit: "Add E2E tests for multi-repo workflow"

### Step 8: Documentation (1 hour)

1. Update Developer Guide with multi-repo examples
2. Create multi-repo workflow tutorial
3. Add API documentation
4. Commit: "Document multi-repo workflow capabilities"

**Total Estimated Time: 14-16 hours**

---

## Security Considerations

### 1. GitHub Token Management

**Risk:** Exposing GitHub tokens in logs or artifacts

**Mitigation:**
- Use environment variable `GITHUB_TOKEN`
- Never log token values
- Use subprocess env parameter instead of shell expansion
- Rotate tokens regularly

```python
# GOOD - Token not exposed
subprocess.run(
    ["gh", "api", "/user"],
    env={**os.environ, "GH_TOKEN": token}
)

# BAD - Token in command string
subprocess.run(f"gh auth login --with-token {token}", shell=True)
```

### 2. Repository Access Control

**Risk:** Agent modifying wrong repository

**Mitigation:**
- Check write access before clone
- Require explicit target_repo_url parameter
- Validate repository URLs (whitelist pattern)
- Log all repository operations

### 3. Workspace Isolation

**Risk:** Tasks interfering with each other

**Mitigation:**
- Unique workspace per task_id
- Automatic cleanup after task completion
- Disk quota monitoring
- Concurrent task limits

### 4. Secrets in External Repos

**Risk:** Agent committing secrets to external repos

**Mitigation:**
- Run secret scanning before PR creation
- Validate .gitignore patterns
- Require HITL approval for external repo changes
- Use gitleaks or trufflehog integration

### 5. Malicious Repository Content

**Risk:** Cloning compromised repositories

**Mitigation:**
- Shallow clone by default (--depth 1)
- Run security scans on cloned repos
- Sandbox agent execution environment
- Review external repo URLs before checkout

---

## References

### Design Documents
- `design/HITL_QualityGate_Architecture.md` - Section 2.3 (Repository Management Strategy)
- `docs/test_artifacts_repository_guide.md` - Test repository infrastructure

### Session Summaries
- `Summary/summary20251123.1.md` - Repository management strategy design
- `Summary/summary20251123.2.md` - Test artifacts repository creation
- `Summary/summary20251128.6.md` - This session (gap analysis)

### Existing Code
- `src/asp/utils/git_utils.py` - Current repository git operations
- `src/asp/approval/branch_manager.py` - Branch management for local PR workflow
- `src/asp/orchestrators/tsp_orchestrator.py` - TSP orchestration pipeline

### External References
- GitHub CLI Documentation: https://cli.github.com/manual/
- Git Submodules: https://git-scm.com/book/en/v2/Git-Tools-Submodules
- GitHub API (Forks): https://docs.github.com/en/rest/repos/forks

---

## Next Steps

### Immediate Actions (Session 20251128.6 or Next Session)

1. **Create directory structure**
   ```bash
   mkdir -p executions pips analysis
   ```

2. **Implement WorkspaceManager** (Phase 1)
   - Priority: HIGH
   - Time: 2-3 hours
   - Dependencies: None

3. **Implement RepositoryManager** (Phase 2)
   - Priority: HIGH
   - Time: 4-6 hours
   - Dependencies: WorkspaceManager

### Short-term Goals (1-2 sessions)

4. **Implement ArtifactManager** (Phase 3)
5. **Create comprehensive tests**
6. **End-to-end validation with test_artifacts_repo**

### Medium-term Goals (2-4 sessions)

7. **Integrate with TSPOrchestrator** (Phase 4)
8. **Add HITL integration for external repos**
9. **Create developer documentation**

### Long-term Goals (Future enhancement)

10. **Fork workflow optimization**
11. **Parallel multi-repo task execution**
12. **Workspace caching for performance**

---

## Conclusion

The ASP repository workflow architecture is well-designed and documented, but lacks implementation. This guide provides:

- ✅ Complete gap analysis
- ✅ Detailed implementation specifications
- ✅ Code examples for all major components
- ✅ Testing strategy
- ✅ Security considerations
- ✅ Phased migration path

**Estimated total implementation time: 14-16 hours** across 4 phases.

**Key principle:** Maintain centralized orchestration in Process_Software_Agents while enabling flexible multi-repository operations through isolated workspaces.

**Next session should start with Phase 1 (Workspace Management)** to establish the foundation for all multi-repo capabilities.

---

**Document Status:** ✅ COMPLETE
**Author:** Claude (ASP Development Assistant)
**Session:** 20251128.6
**Created:** November 28, 2025
