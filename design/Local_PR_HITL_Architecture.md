# Local Pull Request-Style HITL Architecture

**Document Version:** 1.0
**Date:** November 24, 2025
**Status:** Design Specification
**Related:** `design/HITL_QualityGate_Architecture.md` (Phase 1A: CLI-based HITL)

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Problem Statement](#problem-statement)
3. [Architecture Overview](#architecture-overview)
4. [Local Branch Workflow](#local-branch-workflow)
5. [Review Approval Mechanism](#review-approval-mechanism)
6. [Integration with TSP Orchestrator](#integration-with-tsp-orchestrator)
7. [Implementation Design](#implementation-design)
8. [Comparison with Other HITL Approaches](#comparison-with-other-hitl-approaches)
9. [Usage Examples](#usage-examples)
10. [Best Practices](#best-practices)
11. [Future Enhancements](#future-enhancements)

---

## Executive Summary

This document specifies a **Pull Request-style Human-in-the-Loop (HITL) workflow for local development** that enables code review and approval without requiring GitHub or external infrastructure.

### Key Features

- ✅ **Zero Infrastructure**: Pure git-based solution, no servers required
- ✅ **Local Development**: Works offline, no internet connection needed
- ✅ **PR-Like Experience**: Familiar workflow for developers
- ✅ **Audit Trail**: Full review history preserved in git
- ✅ **TSP Integration**: Compatible with existing TSP Orchestrator
- ✅ **Fast Iteration**: No network latency, instant feedback

### Use Cases

1. **Local Development**: Developer working on laptop without internet
2. **Testing Workflows**: Validating TSP Orchestrator without GitHub API calls
3. **CI/CD Pipelines**: Automated workflows that need review gates
4. **Air-Gapped Environments**: Secure environments without external access

---

## Problem Statement

### Current Gap

The HITL Quality Gate Architecture (Phase 1A: CLI-based, Phase 1B: GitHub Issues) requires either:
- Interactive terminal prompts (Phase 1A) - blocks automation
- GitHub API access (Phase 1B) - requires internet, GitHub account

### Local Development Challenges

When developing or testing TSP Orchestrator locally:

1. **No PR Infrastructure**: Can't create GitHub PRs for every test run
2. **Blocking Prompts**: CLI prompts interrupt automated workflows
3. **No Review History**: Approval decisions not preserved
4. **Manual Merging**: Risk of human error when merging branches
5. **Lost Context**: No structured way to document why approvals were granted/rejected

### Requirements

**Functional:**
- FR-1: Create feature branches automatically for agent output
- FR-2: Generate human-readable diffs for review
- FR-3: Accept/reject reviews with structured comments
- FR-4: Merge approved changes with audit trail
- FR-5: Preserve review history in git repository

**Non-Functional:**
- NFR-1: Zero external dependencies (pure git)
- NFR-2: Works offline (no network required)
- NFR-3: Fast review cycle (<30 seconds from review to merge)
- NFR-4: Compatible with existing HITL architecture
- NFR-5: Scriptable/automatable for testing

---

## Architecture Overview

### High-Level Design

```
┌─────────────────────────────────────────────────────────────┐
│                    TSP Orchestrator                          │
│                                                              │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐            │
│  │  Planning  │→│  Design    │→│  Code      │ (Agents)     │
│  └────────────┘  └────────────┘  └────────────┘            │
│         ↓              ↓              ↓                      │
│  ┌──────────────────────────────────────────┐              │
│  │      Quality Gate Check                   │              │
│  │  (Design Review, Code Review, etc.)       │              │
│  └──────────────────────────────────────────┘              │
│         ↓ (FAIL)                                             │
│  ┌──────────────────────────────────────────┐              │
│  │   LocalPRApprovalService                  │  ← THIS DOC │
│  └──────────────────────────────────────────┘              │
└─────────────────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────────────────┐
│                   Git Repository                             │
│                                                              │
│  main ──────────────────────────●───────────→               │
│                                 ↑  (merge)                   │
│  feature/task-123 ──●──●──●───┘                             │
│                     (commits)                                │
│                                                              │
│  refs/notes/reviews/task-123                                │
│    └─ Review comments, approval decision, timestamp         │
└─────────────────────────────────────────────────────────────┘
```

### Component Architecture

```
┌──────────────────────────────────────────────────────────┐
│           LocalPRApprovalService                          │
├──────────────────────────────────────────────────────────┤
│                                                           │
│  ┌─────────────────────────────────────────────────┐    │
│  │  1. BranchManager                                │    │
│  │     - Create feature branch                      │    │
│  │     - Commit agent output                        │    │
│  │     - Generate human-readable diff               │    │
│  └─────────────────────────────────────────────────┘    │
│                        ↓                                  │
│  ┌─────────────────────────────────────────────────┐    │
│  │  2. ReviewPresenter                              │    │
│  │     - Format diff for human review               │    │
│  │     - Show quality gate report                   │    │
│  │     - Display review options                     │    │
│  └─────────────────────────────────────────────────┘    │
│                        ↓                                  │
│  ┌─────────────────────────────────────────────────┐    │
│  │  3. ApprovalCollector                            │    │
│  │     - Prompt for approve/reject decision         │    │
│  │     - Collect justification/comments             │    │
│  │     - Store review in git notes                  │    │
│  └─────────────────────────────────────────────────┘    │
│                        ↓                                  │
│  ┌─────────────────────────────────────────────────┐    │
│  │  4. MergeController                              │    │
│  │     - Merge approved branches (--no-ff)          │    │
│  │     - Reject/tag rejected branches               │    │
│  │     - Clean up merged branches                   │    │
│  └─────────────────────────────────────────────────┘    │
│                                                           │
└──────────────────────────────────────────────────────────┘
```

---

## Local Branch Workflow

### Workflow Steps

#### 1. Agent Generates Output (TSP Orchestrator)

```python
# Agent produces code/design/tests
agent_output = code_agent.generate(task)

# Quality gate check fails
quality_gate_result = code_review_agent.review(agent_output)
if not quality_gate_result.passed:
    # Trigger HITL approval workflow
    approval_service.request_approval(
        task_id="TSP-123",
        gate_type="code_review",
        agent_output=agent_output,
        quality_report=quality_gate_result
    )
```

#### 2. Create Feature Branch

```bash
# LocalPRApprovalService creates branch automatically
git checkout -b review/TSP-123-code-review

# Commit agent output
git add generated_code/
git commit -m "Code Agent: Generate implementation for TSP-123

Generated by: Code Agent (FR-004)
Task: TSP-123
Quality Gate: FAILED (4 issues)
Requires HITL approval before merge"
```

#### 3. Generate Review Diff

```bash
# Show changes since main branch
git diff main...review/TSP-123-code-review > /tmp/review-diff.txt

# Generate human-readable summary
git log main..review/TSP-123-code-review --oneline
git diff --stat main...review/TSP-123-code-review
```

#### 4. Present for Human Review

Display in terminal:
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  REVIEW REQUEST: TSP-123 Code Review
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Task ID:        TSP-123
Agent:          Code Agent (FR-004)
Quality Gate:   Code Review
Status:         ❌ FAILED (4 issues: 0C/0H/2M/2L)

Branch:         review/TSP-123-code-review
Base Branch:    main
Files Changed:  12
Insertions:     +456
Deletions:      -23

Quality Gate Report:
┌─────────────────────────────────────────────────────────┐
│ Issue                                   Severity  Line   │
├─────────────────────────────────────────────────────────┤
│ Missing error handling in API call     MEDIUM    45     │
│ Hardcoded configuration value           MEDIUM    67     │
│ TODO comment in production code         LOW       89     │
│ Magic number without constant          LOW       112    │
└─────────────────────────────────────────────────────────┘

Diff Summary:
  src/api/endpoints.py              | 156 ++++++++++++++++++++++++
  src/models/request.py             |  89 +++++++++++++
  src/utils/validation.py           |  67 ++++++++++
  tests/test_api.py                 | 144 ++++++++++++++++++++++
  ...

View full diff? [y/n]: y

[Shows full diff with syntax highlighting]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  REVIEW DECISION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Options:
  1. APPROVE   - Merge changes to main branch
  2. REJECT    - Do not merge, mark for revision
  3. DEFER     - Save decision for later
  4. DIFF      - View diff again

Your decision [1/2/3/4]:
```

#### 5. Collect Approval Decision

```bash
# User chooses APPROVE
Decision: 1

# Prompt for justification
Justification (required): Issues are low-risk, API endpoint
functionality is critical for release. Error handling can be
improved in follow-up task.

# Store review in git notes
git notes --ref=reviews add review/TSP-123-code-review -m "
Review Decision: APPROVED
Reviewer: user@example.com
Timestamp: 2025-11-24T10:30:00Z
Task: TSP-123
Quality Gate: Code Review (FAILED: 4 issues)
Justification: Issues are low-risk, API endpoint functionality
is critical for release. Error handling can be improved in
follow-up task.

Quality Report Summary:
- Medium: 2 issues
- Low: 2 issues
- Critical/High: 0 issues
"
```

#### 6. Merge (APPROVED) or Tag (REJECTED)

**If APPROVED:**
```bash
# Merge with explicit merge commit (preserves branch history)
git checkout main
git merge --no-ff review/TSP-123-code-review \
  -m "Merge review/TSP-123-code-review: HITL Approved

Task: TSP-123
Agent: Code Agent (FR-004)
Quality Gate: Code Review (FAILED, 4 issues)
Review Decision: APPROVED by user@example.com
Justification: Issues are low-risk, API endpoint functionality
is critical for release.

Reviewed-by: user@example.com
Approved-with-issues: 2M/2L"

# Delete feature branch
git branch -d review/TSP-123-code-review

# Tag merge commit for easy reference
git tag -a review-approved-TSP-123 -m "HITL approved review for TSP-123"
```

**If REJECTED:**
```bash
# Tag branch for historical record
git tag -a review-rejected-TSP-123 review/TSP-123-code-review -m "
Review Decision: REJECTED
Reviewer: user@example.com
Timestamp: 2025-11-24T10:35:00Z
Reason: Critical security issues must be addressed before merge"

# Optionally delete branch (tag preserves history)
git branch -D review/TSP-123-code-review
```

---

## Review Approval Mechanism

### Git Notes for Review Storage

Git notes provide a lightweight way to attach review metadata without modifying commits:

```bash
# Create review note
git notes --ref=reviews add <commit-sha> -m "Review metadata..."

# View review notes
git notes --ref=reviews show <commit-sha>

# List all reviews
git log --show-notes=reviews

# Push notes to remote (if needed)
git push origin refs/notes/reviews
```

### Review Metadata Schema

```yaml
review_decision:
  decision: "APPROVED" | "REJECTED" | "DEFERRED"
  reviewer: "user@example.com"
  timestamp: "2025-11-24T10:30:00Z"

task_context:
  task_id: "TSP-123"
  agent: "Code Agent (FR-004)"
  quality_gate: "Code Review"
  gate_status: "FAILED"

quality_summary:
  critical: 0
  high: 0
  medium: 2
  low: 2
  total: 4

justification: |
    Issues are low-risk, API endpoint functionality is critical
    for release. Error handling can be improved in follow-up task.

artifacts:
  branch: "review/TSP-123-code-review"
  merge_commit: "a1b2c3d4..."  # (if approved)
  tag: "review-approved-TSP-123"
```

### Audit Trail

All review decisions preserved in git:

```bash
# View all review decisions
git log --all --show-notes=reviews --grep="Review Decision"

# Search for approved reviews
git log --all --show-notes=reviews --grep="APPROVED"

# Find reviews by task ID
git log --all --show-notes=reviews --grep="TSP-123"

# Generate review report
git log --all --show-notes=reviews --pretty=format:"%h %s" \
  --grep="Review Decision" | \
  awk '{print $1}' | \
  xargs -I {} git notes --ref=reviews show {}
```

---

## Integration with TSP Orchestrator

### Approval Service Interface

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional
from enum import Enum

class ReviewDecision(Enum):
    APPROVED = "approved"
    REJECTED = "rejected"
    DEFERRED = "deferred"

@dataclass
class ApprovalRequest:
    task_id: str
    gate_type: str  # "design_review", "code_review", etc.
    agent_output: dict
    quality_report: dict
    base_branch: str = "main"

@dataclass
class ApprovalResponse:
    decision: ReviewDecision
    reviewer: str
    timestamp: str
    justification: str
    review_branch: Optional[str] = None
    merge_commit: Optional[str] = None

class ApprovalService(ABC):
    """Abstract base class for HITL approval services."""

    @abstractmethod
    def request_approval(
        self,
        request: ApprovalRequest
    ) -> ApprovalResponse:
        """Request human approval for quality gate failure."""
        pass

class LocalPRApprovalService(ApprovalService):
    """Local PR-style approval using git branches and notes."""

    def __init__(
        self,
        repo_path: str,
        base_branch: str = "main",
        auto_cleanup: bool = True
    ):
        self.repo_path = repo_path
        self.base_branch = base_branch
        self.auto_cleanup = auto_cleanup
        self.branch_manager = BranchManager(repo_path)
        self.review_presenter = ReviewPresenter()
        self.approval_collector = ApprovalCollector()
        self.merge_controller = MergeController(repo_path)

    def request_approval(
        self,
        request: ApprovalRequest
    ) -> ApprovalResponse:
        """
        Request HITL approval using local PR-style workflow.

        Steps:
        1. Create feature branch with agent output
        2. Generate and present diff for review
        3. Collect approval decision
        4. Merge (if approved) or tag (if rejected)
        5. Store review metadata in git notes
        """

        # Step 1: Create feature branch
        branch_name = f"review/{request.task_id}-{request.gate_type}"
        self.branch_manager.create_branch(
            branch_name=branch_name,
            base_branch=request.base_branch
        )

        # Commit agent output
        commit_sha = self.branch_manager.commit_output(
            branch_name=branch_name,
            output=request.agent_output,
            task_id=request.task_id,
            gate_type=request.gate_type
        )

        # Step 2: Generate diff
        diff = self.branch_manager.generate_diff(
            base_branch=request.base_branch,
            feature_branch=branch_name
        )

        # Step 3: Present for review
        self.review_presenter.display_review(
            task_id=request.task_id,
            gate_type=request.gate_type,
            quality_report=request.quality_report,
            diff=diff,
            branch_name=branch_name
        )

        # Step 4: Collect decision
        approval = self.approval_collector.collect_decision()

        # Step 5: Execute decision
        if approval.decision == ReviewDecision.APPROVED:
            merge_commit = self.merge_controller.merge_branch(
                branch_name=branch_name,
                base_branch=request.base_branch,
                review_metadata=approval
            )
            approval.merge_commit = merge_commit

            if self.auto_cleanup:
                self.branch_manager.delete_branch(branch_name)

        elif approval.decision == ReviewDecision.REJECTED:
            self.merge_controller.tag_rejected(
                branch_name=branch_name,
                review_metadata=approval
            )

            if self.auto_cleanup:
                self.branch_manager.delete_branch(branch_name)

        # Store review in git notes
        self._store_review_notes(commit_sha, approval, request)

        approval.review_branch = branch_name
        return approval

    def _store_review_notes(
        self,
        commit_sha: str,
        approval: ApprovalResponse,
        request: ApprovalRequest
    ):
        """Store review metadata in git notes."""
        note_content = f"""
Review Decision: {approval.decision.value.upper()}
Reviewer: {approval.reviewer}
Timestamp: {approval.timestamp}
Task: {request.task_id}
Quality Gate: {request.gate_type}
Justification: {approval.justification}

Quality Report Summary:
{self._format_quality_summary(request.quality_report)}
"""
        self.branch_manager.add_note(
            commit_sha=commit_sha,
            note_content=note_content,
            notes_ref="reviews"
        )
```

### TSP Orchestrator Integration

```python
class TSPOrchestrator:
    def __init__(self, approval_service: ApprovalService):
        self.approval_service = approval_service
        # ... other initialization

    def run_pipeline(self, task: Task):
        # ... agents run ...

        # Code Review quality gate
        code_review_result = self.code_review_agent.review(code_output)

        if not code_review_result.passed:
            # Trigger HITL approval
            approval_request = ApprovalRequest(
                task_id=task.id,
                gate_type="code_review",
                agent_output=code_output,
                quality_report=code_review_result.to_dict(),
                base_branch="main"
            )

            approval_response = self.approval_service.request_approval(
                approval_request
            )

            if approval_response.decision == ReviewDecision.REJECTED:
                raise QualityGateRejected(
                    f"Code review rejected: {approval_response.justification}"
                )

            # Log approval override
            self.telemetry.log_quality_gate_override(
                task_id=task.id,
                gate="code_review",
                decision=approval_response.decision.value,
                justification=approval_response.justification
            )

        # Continue pipeline...
```

---

## Implementation Design

### Class Diagram

```python
┌─────────────────────────────────────────────────────────┐
│              LocalPRApprovalService                      │
├─────────────────────────────────────────────────────────┤
│ - repo_path: str                                         │
│ - base_branch: str                                       │
│ - auto_cleanup: bool                                     │
│ - branch_manager: BranchManager                          │
│ - review_presenter: ReviewPresenter                      │
│ - approval_collector: ApprovalCollector                  │
│ - merge_controller: MergeController                      │
├─────────────────────────────────────────────────────────┤
│ + request_approval(request: ApprovalRequest)             │
│   → ApprovalResponse                                     │
│ - _store_review_notes(commit_sha, approval, request)     │
└─────────────────────────────────────────────────────────┘
                          │
           ┌──────────────┼──────────────┐
           │              │              │
           ▼              ▼              ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│ BranchManager│  │ReviewPresenter│ │ApprovalCollector│
├──────────────┤  ├──────────────┤  ├──────────────┤
│+create_branch│  │+display_review│ │+collect_decision│
│+commit_output│  │+format_diff   │  │+prompt_user  │
│+generate_diff│  │+show_summary  │  │+validate_input│
│+add_note     │  └──────────────┘  └──────────────┘
│+delete_branch│
└──────────────┘
           ▼
┌──────────────────┐
│  MergeController │
├──────────────────┤
│ +merge_branch    │
│ +tag_rejected    │
│ +create_tag      │
└──────────────────┘
```

### File Structure

```
src/asp/approval/
├── __init__.py
├── base.py                      # ApprovalService ABC
├── local_pr.py                  # LocalPRApprovalService
├── branch_manager.py            # Git branch operations
├── review_presenter.py          # Terminal UI for reviews
├── approval_collector.py        # User input collection
├── merge_controller.py          # Merge/tag operations
└── utils.py                     # Helper functions

tests/approval/
├── test_local_pr_service.py
├── test_branch_manager.py
├── test_review_presenter.py
├── test_approval_collector.py
└── test_merge_controller.py

docs/
└── local_pr_approval_guide.md   # User guide
```

### Key Implementation Details

#### BranchManager

```python
import subprocess
from pathlib import Path

class BranchManager:
    def __init__(self, repo_path: str):
        self.repo_path = Path(repo_path)

    def create_branch(self, branch_name: str, base_branch: str):
        """Create new branch from base branch."""
        subprocess.run(
            ["git", "checkout", "-b", branch_name, base_branch],
            cwd=self.repo_path,
            check=True
        )

    def commit_output(
        self,
        branch_name: str,
        output: dict,
        task_id: str,
        gate_type: str
    ) -> str:
        """Commit agent output to branch, return commit SHA."""
        # Switch to branch
        subprocess.run(
            ["git", "checkout", branch_name],
            cwd=self.repo_path,
            check=True
        )

        # Write output files (implementation specific)
        self._write_output_files(output)

        # Stage changes
        subprocess.run(
            ["git", "add", "."],
            cwd=self.repo_path,
            check=True
        )

        # Commit
        commit_msg = f"""Agent output for {task_id}

Task: {task_id}
Quality Gate: {gate_type}
Generated by: {output.get('agent', 'Unknown')}
Requires HITL approval"""

        subprocess.run(
            ["git", "commit", "-m", commit_msg],
            cwd=self.repo_path,
            check=True
        )

        # Get commit SHA
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=self.repo_path,
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout.strip()

    def generate_diff(
        self,
        base_branch: str,
        feature_branch: str
    ) -> str:
        """Generate diff between branches."""
        result = subprocess.run(
            ["git", "diff", f"{base_branch}...{feature_branch}"],
            cwd=self.repo_path,
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout

    def add_note(
        self,
        commit_sha: str,
        note_content: str,
        notes_ref: str = "reviews"
    ):
        """Add git note to commit."""
        subprocess.run(
            ["git", "notes", "--ref", notes_ref, "add",
             commit_sha, "-m", note_content],
            cwd=self.repo_path,
            check=True
        )

    def delete_branch(self, branch_name: str):
        """Delete branch (must not be current branch)."""
        # Switch to main first
        subprocess.run(
            ["git", "checkout", "main"],
            cwd=self.repo_path,
            check=True
        )

        subprocess.run(
            ["git", "branch", "-d", branch_name],
            cwd=self.repo_path,
            check=True
        )
```

#### ReviewPresenter

```python
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.syntax import Syntax

class ReviewPresenter:
    def __init__(self):
        self.console = Console()

    def display_review(
        self,
        task_id: str,
        gate_type: str,
        quality_report: dict,
        diff: str,
        branch_name: str
    ):
        """Display review information in terminal."""

        # Header
        self.console.rule(f"[bold]REVIEW REQUEST: {task_id}", style="cyan")

        # Summary table
        summary = Table.grid(padding=(0, 2))
        summary.add_row("Task ID:", task_id)
        summary.add_row("Quality Gate:", gate_type)
        summary.add_row("Branch:", branch_name)
        summary.add_row(
            "Status:",
            f"❌ FAILED ({quality_report['total']} issues)"
        )

        self.console.print(Panel(summary, title="Summary"))

        # Quality report
        self._display_quality_report(quality_report)

        # Diff statistics
        self._display_diff_stats(diff)

        # Ask if user wants to see full diff
        show_diff = self.console.input("\nView full diff? [y/n]: ")
        if show_diff.lower() == 'y':
            self._display_full_diff(diff)

    def _display_quality_report(self, report: dict):
        """Display quality issues in table."""
        table = Table(title="Quality Gate Issues")
        table.add_column("Issue", style="white")
        table.add_column("Severity", justify="center")
        table.add_column("Line", justify="right")

        for issue in report.get('issues', []):
            severity_color = {
                'CRITICAL': 'red bold',
                'HIGH': 'red',
                'MEDIUM': 'yellow',
                'LOW': 'cyan'
            }.get(issue['severity'], 'white')

            table.add_row(
                issue['description'],
                f"[{severity_color}]{issue['severity']}[/{severity_color}]",
                str(issue.get('line', '-'))
            )

        self.console.print(table)

    def _display_diff_stats(self, diff: str):
        """Display diff statistics."""
        lines = diff.split('\n')
        additions = sum(1 for line in lines if line.startswith('+'))
        deletions = sum(1 for line in lines if line.startswith('-'))

        self.console.print(f"\n[green]+{additions}[/green] additions")
        self.console.print(f"[red]-{deletions}[/red] deletions")

    def _display_full_diff(self, diff: str):
        """Display full diff with syntax highlighting."""
        syntax = Syntax(diff, "diff", theme="monokai", line_numbers=True)
        self.console.print(syntax)
```

#### ApprovalCollector

```python
from datetime import datetime
import getpass

class ApprovalCollector:
    def __init__(self):
        self.console = Console()

    def collect_decision(self) -> ApprovalResponse:
        """Collect approval decision from user."""

        # Display options
        self.console.rule("[bold]REVIEW DECISION", style="cyan")
        self.console.print("\nOptions:")
        self.console.print("  1. APPROVE   - Merge changes to main branch")
        self.console.print("  2. REJECT    - Do not merge, mark for revision")
        self.console.print("  3. DEFER     - Save decision for later")

        # Get decision
        while True:
            choice = self.console.input("\nYour decision [1/2/3]: ")
            if choice in ['1', '2', '3']:
                break
            self.console.print("[red]Invalid choice. Please enter 1, 2, or 3.[/red]")

        decision_map = {
            '1': ReviewDecision.APPROVED,
            '2': ReviewDecision.REJECTED,
            '3': ReviewDecision.DEFERRED
        }
        decision = decision_map[choice]

        # Get justification
        self.console.print("\nJustification (required):")
        justification = self.console.input("> ")

        while not justification.strip():
            self.console.print("[red]Justification is required.[/red]")
            justification = self.console.input("> ")

        # Get reviewer info
        reviewer = getpass.getuser() + "@local"
        timestamp = datetime.utcnow().isoformat() + 'Z'

        return ApprovalResponse(
            decision=decision,
            reviewer=reviewer,
            timestamp=timestamp,
            justification=justification
        )
```

#### MergeController

```python
class MergeController:
    def __init__(self, repo_path: str):
        self.repo_path = Path(repo_path)

    def merge_branch(
        self,
        branch_name: str,
        base_branch: str,
        review_metadata: ApprovalResponse
    ) -> str:
        """Merge branch with --no-ff, return merge commit SHA."""

        # Switch to base branch
        subprocess.run(
            ["git", "checkout", base_branch],
            cwd=self.repo_path,
            check=True
        )

        # Create merge commit message
        merge_msg = f"""Merge {branch_name}: HITL Approved

Review Decision: APPROVED
Reviewer: {review_metadata.reviewer}
Timestamp: {review_metadata.timestamp}
Justification: {review_metadata.justification}
"""

        # Merge with --no-ff
        subprocess.run(
            ["git", "merge", "--no-ff", branch_name, "-m", merge_msg],
            cwd=self.repo_path,
            check=True
        )

        # Get merge commit SHA
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=self.repo_path,
            capture_output=True,
            text=True,
            check=True
        )
        merge_sha = result.stdout.strip()

        # Create tag for easy reference
        tag_name = f"review-approved-{branch_name.split('/')[-1]}"
        self.create_tag(tag_name, merge_sha, review_metadata)

        return merge_sha

    def tag_rejected(
        self,
        branch_name: str,
        review_metadata: ApprovalResponse
    ):
        """Tag rejected branch for historical record."""

        tag_name = f"review-rejected-{branch_name.split('/')[-1]}"
        tag_msg = f"""Review REJECTED

Reviewer: {review_metadata.reviewer}
Timestamp: {review_metadata.timestamp}
Reason: {review_metadata.justification}
"""

        subprocess.run(
            ["git", "tag", "-a", tag_name, branch_name, "-m", tag_msg],
            cwd=self.repo_path,
            check=True
        )

    def create_tag(
        self,
        tag_name: str,
        commit_sha: str,
        review_metadata: ApprovalResponse
    ):
        """Create annotated tag."""
        tag_msg = f"""HITL Review Approved

Reviewer: {review_metadata.reviewer}
Timestamp: {review_metadata.timestamp}
"""
        subprocess.run(
            ["git", "tag", "-a", tag_name, commit_sha, "-m", tag_msg],
            cwd=self.repo_path,
            check=True
        )
```

---

## Comparison with Other HITL Approaches

| Feature | Local PR | CLI Prompts (Phase 1A) | GitHub Issues (Phase 1B) |
|---------|----------|------------------------|--------------------------|
| **Infrastructure** | Git only | Terminal only | GitHub API |
| **Network Required** | ❌ No | ❌ No | ✅ Yes |
| **Approval History** | ✅ Git notes | ❌ Not stored | ✅ GitHub issues |
| **Branch Workflow** | ✅ Automatic | ❌ Manual | ✅ Automatic |
| **Review Context** | ✅ Full diff | ⚠️ Summary only | ✅ Full diff |
| **Audit Trail** | ✅ Git history | ❌ Limited | ✅ GitHub history |
| **Automation** | ✅ Scriptable | ⚠️ Blocks execution | ✅ Webhook-based |
| **Team Workflow** | ⚠️ Single user | ⚠️ Single user | ✅ Multi-user |
| **Notifications** | ❌ None | ❌ None | ✅ Email/Slack |
| **Setup Time** | 5 minutes | 0 minutes | 30 minutes |
| **Best For** | Local dev, testing | Quick demos | Production teams |

### When to Use Each Approach

**Use Local PR (this document):**
- ✅ Local development on laptop
- ✅ Testing TSP Orchestrator workflows
- ✅ Offline or air-gapped environments
- ✅ Single developer iteration
- ✅ CI/CD pipelines with review gates

**Use CLI Prompts (Phase 1A):**
- ✅ Quick demos or prototypes
- ✅ Immediate feedback needed
- ✅ No need for audit trail
- ✅ Interactive workshops

**Use GitHub Issues (Phase 1B):**
- ✅ Team workflows (multiple reviewers)
- ✅ Production deployments
- ✅ Need notifications (email, Slack)
- ✅ Long-running reviews (hours/days)
- ✅ Compliance requirements (immutable audit trail)

---

## Usage Examples

### Example 1: Testing TSP Orchestrator Locally

```python
# test_tsp_orchestrator_local.py
import pytest
from asp.orchestrators.tsp_orchestrator import TSPOrchestrator
from asp.approval.local_pr import LocalPRApprovalService

def test_tsp_pipeline_with_local_pr():
    """Test TSP Orchestrator with local PR approval."""

    # Initialize approval service
    approval_service = LocalPRApprovalService(
        repo_path="/path/to/test_repo",
        base_branch="main",
        auto_cleanup=True
    )

    # Initialize orchestrator
    orchestrator = TSPOrchestrator(
        approval_service=approval_service
    )

    # Run pipeline (will pause for review at quality gates)
    task = Task(id="TSP-TEST-001", description="Test task")
    result = orchestrator.run_pipeline(task)

    assert result.success
    assert result.quality_gates_passed >= 0  # Some may require override
```

### Example 2: Automated Testing with Auto-Approve

```python
class AutoApproveService(LocalPRApprovalService):
    """Auto-approve all reviews for testing."""

    def request_approval(self, request: ApprovalRequest) -> ApprovalResponse:
        """Auto-approve without human intervention."""

        # Still create branch and commit (for audit trail)
        branch_name = f"review/{request.task_id}-{request.gate_type}"
        self.branch_manager.create_branch(branch_name, request.base_branch)
        commit_sha = self.branch_manager.commit_output(
            branch_name, request.agent_output,
            request.task_id, request.gate_type
        )

        # Auto-approve
        approval = ApprovalResponse(
            decision=ReviewDecision.APPROVED,
            reviewer="autotest@local",
            timestamp=datetime.utcnow().isoformat() + 'Z',
            justification="Auto-approved for automated testing"
        )

        # Merge
        merge_commit = self.merge_controller.merge_branch(
            branch_name, request.base_branch, approval
        )
        approval.merge_commit = merge_commit

        # Store note
        self._store_review_notes(commit_sha, approval, request)

        # Cleanup
        if self.auto_cleanup:
            self.branch_manager.delete_branch(branch_name)

        return approval

# Use in tests
def test_full_pipeline_e2e():
    orchestrator = TSPOrchestrator(
        approval_service=AutoApproveService(
            repo_path="/tmp/test_repo",
            auto_cleanup=True
        )
    )

    # Runs full pipeline without blocking
    result = orchestrator.run_pipeline(task)
    assert result.success
```

### Example 3: Review History Analysis

```bash
#!/bin/bash
# scripts/analyze_reviews.sh

# Show all review decisions
echo "=== All Review Decisions ==="
git log --all --show-notes=reviews --grep="Review Decision" \
  --pretty=format:"%h %s"

# Count approved vs rejected
echo -e "\n=== Approval Statistics ==="
approved=$(git log --all --show-notes=reviews --grep="APPROVED" | grep -c "Review Decision")
rejected=$(git log --all --show-notes=reviews --grep="REJECTED" | grep -c "Review Decision")
echo "Approved: $approved"
echo "Rejected: $rejected"

# Find reviews with most issues
echo -e "\n=== Reviews with Quality Issues ==="
git log --all --show-notes=reviews --pretty=format:"%h" --grep="Review Decision" | \
  while read sha; do
    echo -e "\n--- $sha ---"
    git notes --ref=reviews show $sha | grep -E "(Task|Quality Gate|Justification)"
  done
```

### Example 4: Custom Review UI (Web-based)

```python
# Optional: Web interface for reviews
from flask import Flask, render_template, request
from asp.approval.local_pr import LocalPRApprovalService

app = Flask(__name__)
approval_service = LocalPRApprovalService(repo_path="/path/to/repo")

@app.route('/reviews/pending')
def list_pending_reviews():
    """List all pending review branches."""
    # Get branches matching review/* pattern
    branches = approval_service.branch_manager.list_branches("review/*")
    return render_template('pending_reviews.html', branches=branches)

@app.route('/reviews/<branch_name>')
def show_review(branch_name):
    """Show review details and diff."""
    diff = approval_service.branch_manager.generate_diff("main", branch_name)
    return render_template('review_detail.html', branch=branch_name, diff=diff)

@app.route('/reviews/<branch_name>/approve', methods=['POST'])
def approve_review(branch_name):
    """Approve and merge review."""
    justification = request.form['justification']

    approval = ApprovalResponse(
        decision=ReviewDecision.APPROVED,
        reviewer=request.form['reviewer'],
        timestamp=datetime.utcnow().isoformat() + 'Z',
        justification=justification
    )

    merge_commit = approval_service.merge_controller.merge_branch(
        branch_name, "main", approval
    )

    return {"success": True, "merge_commit": merge_commit}
```

---

## Best Practices

### 1. Branch Naming Convention

Use consistent naming for review branches:
```
review/<task-id>-<gate-type>

Examples:
  review/TSP-123-code-review
  review/TSP-123-design-review
  review/HW-001-test-results
```

### 2. Commit Messages

Follow structured format for review commits:
```
<Agent Name>: <Brief description>

Task: <task-id>
Agent: <agent-name> (<FR-number>)
Quality Gate: <gate-name>
Status: FAILED (<issue-count> issues)
Requires HITL approval

<Optional: Additional details>
```

### 3. Merge Commit Messages

Include review metadata in merge commits:
```
Merge <branch-name>: HITL Approved

Review Decision: APPROVED
Reviewer: <reviewer-email>
Timestamp: <ISO-8601-timestamp>
Justification: <approval-justification>

Quality Gate: <gate-name> (FAILED, <issue-count> issues)
Approved-with-issues: <severity-breakdown>
```

### 4. Git Notes Organization

Use dedicated refs for different note types:
```
refs/notes/reviews        # HITL approval decisions
refs/notes/quality-gates  # Quality gate results
refs/notes/metrics        # Cost/time metrics
```

### 5. Cleanup Strategy

**Merged Branches:**
- Delete after merge (history preserved in merge commit)
- Tag merge commit for easy reference

**Rejected Branches:**
- Tag before deletion (preserves rejected work)
- Optionally keep branch for later revision

**Deferred Reviews:**
- Keep branch until decision made
- Add reminder tag: `review-deferred-<task-id>`

### 6. Testing with Local PR

**Unit Tests:**
```python
# Use temporary git repos
import tempfile
import shutil

@pytest.fixture
def temp_repo():
    repo_dir = tempfile.mkdtemp()
    # Initialize git repo
    subprocess.run(["git", "init"], cwd=repo_dir, check=True)
    subprocess.run(["git", "config", "user.email", "test@test.com"],
                   cwd=repo_dir, check=True)
    subprocess.run(["git", "config", "user.name", "Test User"],
                   cwd=repo_dir, check=True)

    yield repo_dir

    shutil.rmtree(repo_dir)

def test_branch_creation(temp_repo):
    service = LocalPRApprovalService(repo_path=temp_repo)
    # ... test logic
```

**Integration Tests:**
- Use test artifacts repository (from Session 20251123.2)
- Verify full approval workflow end-to-end
- Test both approve and reject paths

### 7. Performance Optimization

**Large Diffs:**
- Limit diff display to configurable line count
- Offer to open diff in external tool (difftool)
- Generate diff summary first, full diff on request

**Repository Size:**
- Use shallow clones for testing (`git clone --depth 1`)
- Regularly prune old review branches/tags
- Consider archiving old review notes

---

## Future Enhancements

### Phase 2: Enhanced Features

**1. Batch Review Mode**
- Review multiple quality gates at once
- Approve/reject all with single decision
- Useful for end-of-day reviews

**2. Review Delegation**
- Tag specific reviewers in git notes
- Email/notify assigned reviewers
- Track review SLAs

**3. Review Templates**
- Pre-defined justification templates by gate type
- Quick approval reasons (e.g., "Low-risk issues")
- Custom templates per project

**4. Diff Analysis Tools**
- Automatic code quality metrics on diff
- Security scan integration (bandit, semgrep)
- Complexity analysis (cyclomatic complexity)

**5. Review Dashboard**
- CLI dashboard showing pending reviews
- Statistics: approval rate, avg review time
- Filter by task, agent, gate type

### Phase 3: Advanced Workflows

**1. Multi-Stage Approval**
- Require approval from multiple reviewers
- Sequential approval workflow (junior → senior)
- Parallel approval (any 2 of 3 approvers)

**2. Automated Review Policies**
- Auto-approve if severity below threshold
- Auto-reject if critical issues present
- Require justification for medium+ issues

**3. Review Analytics**
- Track quality gate override patterns
- Identify frequently approved issue types
- Generate PIP recommendations

**4. Integration with Phase 1B (GitHub)**
- Optionally push review branches to GitHub
- Sync local approvals to GitHub Issues
- Hybrid workflow: local dev → GitHub for team

**5. Web UI (Optional)**
- Browser-based review interface
- Real-time diff viewer
- Collaborative review comments

### Phase 4: Enterprise Features

**1. Audit Compliance**
- Export review history for audits
- Cryptographic signing of review decisions
- Tamper-proof review trail

**2. Access Control**
- Role-based approval authority
- Reviewer whitelists per gate type
- Approval escalation workflows

**3. Integration with External Tools**
- JIRA/Linear task tracking
- Slack/Teams notifications
- Code quality platforms (SonarQube)

---

## Appendix A: Command Reference

### Git Commands for Reviews

```bash
# List all review branches
git branch --list 'review/*'

# View review notes for commit
git notes --ref=reviews show <commit-sha>

# View all review history
git log --all --show-notes=reviews --grep="Review Decision"

# Find approved reviews
git log --all --show-notes=reviews --grep="APPROVED"

# Export review history
git log --all --show-notes=reviews --pretty=format:"%h %s" \
  --grep="Review Decision" > review_history.txt

# Count approvals vs rejections
git log --all --show-notes=reviews --grep="Review Decision" | \
  grep -c "APPROVED"

# Delete old review branches
git branch --list 'review/*' | xargs git branch -d

# Push review notes to remote (optional)
git push origin refs/notes/reviews

# Fetch review notes from remote
git fetch origin refs/notes/reviews:refs/notes/reviews
```

### Scripts

See `scripts/` directory for:
- `review_pending.sh` - List pending reviews
- `review_approve.sh` - Quick approve script
- `review_reject.sh` - Quick reject script
- `review_history.sh` - Generate review report
- `review_cleanup.sh` - Clean up old review branches

---

## Appendix B: Configuration

### Environment Variables

```bash
# Default base branch
export ASP_REVIEW_BASE_BRANCH="main"

# Auto-cleanup after merge/reject
export ASP_REVIEW_AUTO_CLEANUP="true"

# Review notes ref name
export ASP_REVIEW_NOTES_REF="reviews"

# Default reviewer (fallback)
export ASP_REVIEW_DEFAULT_REVIEWER="$(git config user.email)"

# Max diff lines to display
export ASP_REVIEW_MAX_DIFF_LINES="1000"
```

### Configuration File

`~/.asp/review_config.yaml`:
```yaml
approval:
  # Base branch for all reviews
  base_branch: "main"

  # Automatically clean up branches after merge/reject
  auto_cleanup: true

  # Git notes ref for storing review metadata
  notes_ref: "reviews"

  # Default reviewer (uses git config user.email if not set)
  default_reviewer: null

  # UI preferences
  ui:
    # Maximum diff lines to display before prompting
    max_diff_lines: 1000

    # Use color output (auto-detected if not set)
    color: true

    # Use rich formatting (requires rich library)
    rich_output: true

  # Merge preferences
  merge:
    # Always use --no-ff for merge commits
    no_fast_forward: true

    # Create tags for approved merges
    tag_approved: true

    # Tag name template
    tag_template: "review-approved-{task_id}"

  # Branch naming
  branch:
    # Branch name template
    template: "review/{task_id}-{gate_type}"

    # Automatically delete rejected branches after tagging
    delete_rejected: true
```

---

## Appendix C: Integration Examples

### Example: Custom Approval Logic

```python
class ConditionalApprovalService(LocalPRApprovalService):
    """
    Approval service with custom logic:
    - Auto-approve if only LOW severity issues
    - Auto-reject if any CRITICAL issues
    - Request human review for MEDIUM/HIGH
    """

    def request_approval(self, request: ApprovalRequest) -> ApprovalResponse:
        issues_by_severity = self._group_by_severity(
            request.quality_report['issues']
        )

        # Auto-reject for critical issues
        if issues_by_severity.get('CRITICAL', 0) > 0:
            return ApprovalResponse(
                decision=ReviewDecision.REJECTED,
                reviewer="auto-reject@local",
                timestamp=datetime.utcnow().isoformat() + 'Z',
                justification="Auto-rejected: Contains CRITICAL severity issues"
            )

        # Auto-approve for only LOW issues
        if issues_by_severity.get('HIGH', 0) == 0 and \
           issues_by_severity.get('MEDIUM', 0) == 0:
            return ApprovalResponse(
                decision=ReviewDecision.APPROVED,
                reviewer="auto-approve@local",
                timestamp=datetime.utcnow().isoformat() + 'Z',
                justification="Auto-approved: Only LOW severity issues"
            )

        # Otherwise, request human review
        return super().request_approval(request)
```

### Example: Notification Integration

```python
import smtplib
from email.message import EmailMessage

class NotifyingApprovalService(LocalPRApprovalService):
    """Send email notification when review is needed."""

    def __init__(self, *args, notification_email: str, **kwargs):
        super().__init__(*args, **kwargs)
        self.notification_email = notification_email

    def request_approval(self, request: ApprovalRequest) -> ApprovalResponse:
        # Send notification
        self._send_notification(request)

        # Continue with normal approval flow
        return super().request_approval(request)

    def _send_notification(self, request: ApprovalRequest):
        msg = EmailMessage()
        msg['Subject'] = f"Review Required: {request.task_id}"
        msg['From'] = "asp-orchestrator@local"
        msg['To'] = self.notification_email
        msg.set_content(f"""
A review is required for task {request.task_id}.

Quality Gate: {request.gate_type}
Status: FAILED ({request.quality_report['total']} issues)

Please review and approve/reject at your earliest convenience.
        """)

        # Send email (configure SMTP server)
        with smtplib.SMTP('localhost') as smtp:
            smtp.send_message(msg)
```

---

## Appendix D: Troubleshooting

### Common Issues

**Issue: Branch already exists**
```
Error: A branch named 'review/TSP-123-code-review' already exists
```
Solution: Delete or rename existing branch before creating new review

**Issue: Merge conflicts**
```
Error: Automatic merge failed; fix conflicts and then commit the result
```
Solution: Resolve conflicts manually, then complete merge

**Issue: Git notes not showing**
```
git log --show-notes=reviews  # Notes not displayed
```
Solution: Fetch notes from remote or verify notes ref name

**Issue: Permission denied on branch operations**
```
Error: permission denied while trying to connect to the Docker daemon socket
```
Solution: Ensure git repository is writable, check file permissions

---

**End of Document**

**Related Documents:**
- `design/HITL_QualityGate_Architecture.md` - Overall HITL architecture
- `design/Repository_Management_Strategy.md` - Artifact storage strategy
- `docs/test_artifacts_repository_guide.md` - Test repository setup

**Revision History:**
- v1.0 (2025-11-24): Initial design specification
