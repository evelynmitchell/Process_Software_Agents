# HITL Integration Guide

**Human-In-The-Loop (HITL) approval workflows for safe AI autonomy**

This guide explains how to integrate Human-In-The-Loop approval workflows into your ASP pipeline, enabling safe autonomous operation with human oversight for critical decisions.

---

## Table of Contents

- [What is HITL?](#what-is-hitl)
- [Why Use HITL?](#why-use-hitl)
- [Three HITL Approaches](#three-hitl-approaches)
- [Local PR-Style HITL](#local-pr-style-hitl)
- [GitHub Issues HITL](#github-issues-hitl)
- [CLI-Based HITL](#cli-based-hitl)
- [Configuration](#configuration)
- [Custom Approval Services](#custom-approval-services)
- [API Reference](#api-reference)
- [Troubleshooting](#troubleshooting)

---

## What is HITL?

**Human-In-The-Loop (HITL)** is a design pattern where autonomous AI agents request human approval for critical decisions before proceeding.

In ASP, HITL enables:

- **Safe Autonomy:** Agents operate independently but defer critical decisions to humans
- **Quality Override:** Humans can approve work that failed quality gates
- **Audit Trail:** Complete record of all human decisions with justifications
- **Gradual Trust:** Start with high oversight, reduce as agents prove reliability

### HITL in the ASP Pipeline

HITL approval is requested when quality gates fail:

```
Design Review → FAIL (security issue detected)
    ↓
HITL Approval Requested
    ├─→ Human reviews diff
    ├─→ Human decides: APPROVE / REJECT / DEFER
    └─→ Audit trail captured
    ↓
If APPROVED → Continue to Code phase
If REJECTED → Route back to Design phase
If DEFERRED → Pause pipeline for later review
```

---

## Why Use HITL?

### When to Use HITL

✅ **Production Deployments**
- Code will be deployed to production
- Security or compliance requirements
- Financial or legal implications

✅ **Learning Phase**
- Agents are in bootstrap learning mode
- Building trust with new agent capabilities
- Collecting validation data

✅ **High-Risk Tasks**
- Database migrations or schema changes
- Security-critical code (authentication, authorization)
- Performance-critical paths
- Public API changes

✅ **Regulatory Compliance**
- Audit trails required for compliance (SOC 2, HIPAA, etc.)
- Human review mandated by policy
- Traceability requirements

### When NOT to Use HITL

❌ **Prototyping and Experimentation**
- Quick throwaway code
- Learning or exploration
- No production consequences

❌ **Fully Trusted Agents**
- Agent has proven reliability (bootstrap complete)
- Low-risk tasks (documentation, tests)
- Autonomous mode enabled

❌ **Automated Pipelines**
- CI/CD without human interaction
- Batch processing
- Background tasks

---

## Three HITL Approaches

ASP provides three HITL implementations for different workflows:

| Approach | Status | Use Case | Best For |
|----------|--------|----------|----------|
| **Local PR-Style** | ✅ Implemented | Solo developer, local work | Individual developers |
| **GitHub Issues** | ⏸️ Planned | Team collaboration | Distributed teams |
| **CLI-Based** | ⏸️ Planned | Interactive sessions | Real-time pair programming |

---

## Local PR-Style HITL

**Status:** ✅ Implemented and E2E validated

The Local PR-Style approach uses git branches and diffs to present agent output for review.

### How It Works

1. **Agent Completes Task** → Outputs fail quality gate
2. **Create Feature Branch** → `review/<TASK-ID>-<gate-type>`
3. **Commit Agent Output** → To feature branch
4. **Generate Diff** → Compare to base branch
5. **Present Review** → Rich terminal UI with diff, quality report
6. **Collect Decision** → APPROVE / REJECT / DEFER
7. **Execute Decision:**
   - APPROVED → Merge to base branch, store audit trail
   - REJECTED → Tag branch for revision, store feedback
   - DEFERRED → Leave branch for later review
8. **Cleanup** → Optional automatic branch deletion

### Installation

```bash
# Local PR-Style HITL is included in core ASP
# No additional dependencies required
uv sync --all-extras
```

### Basic Usage

```python
from asp.orchestrators import TSPOrchestrator
from asp.approval import LocalPRApprovalService
from asp.models import TaskRequest

# Create approval service
approval_service = LocalPRApprovalService(
    repo_path="/path/to/your/repo",
    base_branch="main",
    auto_cleanup=True  # Delete branches after merge/reject
)

# Create orchestrator with HITL enabled
orchestrator = TSPOrchestrator(
    approval_service=approval_service  # Enable HITL
)

# Run task - HITL approval requested if quality gates fail
task = TaskRequest(
    task_id="FEAT-001",
    description="Add user authentication endpoint",
    requirements=[...]
)

result = orchestrator.execute(task)
```

### Interactive Review Session

When quality gates fail, you'll see a rich terminal UI:

```
═══════════════════════════════════════════════════════════════
                    HUMAN-IN-THE-LOOP REVIEW
═══════════════════════════════════════════════════════════════

Task ID: FEAT-001
Gate Type: design_review
Decision Required: Design failed security review

───────────────────────────────────────────────────────────────
Quality Report Summary
───────────────────────────────────────────────────────────────

Overall Assessment: FAIL

Security Review:
  ❌ CRITICAL: Missing authentication on sensitive endpoint
  ❌ HIGH: Password stored in plaintext (should use bcrypt)
  ⚠️  MEDIUM: No rate limiting on login endpoint

Performance Review: ✅ PASS
Data Integrity Review: ✅ PASS

───────────────────────────────────────────────────────────────
Changes Preview
───────────────────────────────────────────────────────────────

 src/api/users.py              | 45 +++++++++++++++++++++
 src/models/user.py            | 23 +++++++++++
 tests/test_users.py           | 67 ++++++++++++++++++++++++++++++

View full diff? [y/n]: y

[Displays full git diff with syntax highlighting]

───────────────────────────────────────────────────────────────
                        REVIEW DECISION
───────────────────────────────────────────────────────────────

Options:
  1. APPROVE   - Merge changes to main branch
  2. REJECT    - Do not merge, mark for revision
  3. DEFER     - Save decision for later

Your decision [1/2/3]: 2

Justification for rejection (required):
> Security issues must be fixed: use bcrypt for passwords and add authentication middleware

───────────────────────────────────────────────────────────────
Review Complete
───────────────────────────────────────────────────────────────

✅ Decision: REJECTED
📝 Justification: Security issues must be fixed: use bcrypt for passwords and add authentication middleware
👤 Reviewer: developer@example.com
📅 Timestamp: 2025-11-25T23:30:00Z
🌿 Branch: review/FEAT-001-design_review (tagged for revision)
```

### Configuration Options

```python
LocalPRApprovalService(
    repo_path="/path/to/repo",           # Git repository path
    base_branch="main",                  # Base branch for merges
    auto_cleanup=True,                   # Delete branches after merge/reject
    notes_ref="reviews"                  # Git notes ref for audit trail
)
```

**Parameters:**

- **repo_path:** Path to your git repository (must be a valid git repo)
- **base_branch:** Branch to merge approved changes into (default: "main")
- **auto_cleanup:** Automatically delete feature branches after merge/reject (default: True)
- **notes_ref:** Git notes reference for storing review metadata (default: "reviews")

### Audit Trail

All review decisions are stored in git notes for complete traceability:

```bash
# View review metadata for a commit
git notes --ref=reviews show <commit-sha>

# Output:
# {
#   "decision": "rejected",
#   "reviewer": "developer@example.com",
#   "timestamp": "2025-11-25T23:30:00Z",
#   "justification": "Security issues must be fixed: use bcrypt for passwords and add authentication middleware",
#   "task_id": "FEAT-001",
#   "gate_type": "design_review"
# }

# List all review branches
git branch | grep "review/"

# View diff for a review branch
git diff main..review/FEAT-001-design_review
```

### Advanced Usage

#### Selective HITL (Only for Critical Gates)

```python
from asp.approval import LocalPRApprovalService

# Create approval service
approval_service = LocalPRApprovalService(repo_path=".")

# Custom orchestrator that only uses HITL for security failures
from asp.orchestrators import TSPOrchestrator

class SelectiveHITLOrchestrator(TSPOrchestrator):
    def should_request_approval(self, gate_type: str, report: dict) -> bool:
        """Only request approval for critical security issues."""
        if gate_type == "design_review":
            security_review = report.get("security_review", {})
            critical_issues = [
                issue for issue in security_review.get("defects", [])
                if issue["severity"] == "CRITICAL"
            ]
            return len(critical_issues) > 0
        return False

orchestrator = SelectiveHITLOrchestrator(approval_service=approval_service)
```

#### Pre-Commit Hook Integration

Integrate HITL with git pre-commit hooks:

```bash
# .git/hooks/pre-commit
#!/bin/bash

# Run ASP HITL approval before allowing commit
uv run python scripts/check_hitl_approval.py

if [ $? -ne 0 ]; then
    echo "❌ HITL approval required before commit"
    exit 1
fi

echo "✅ HITL approval verified"
exit 0
```

---

## GitHub Issues HITL

**Status:** ⏸️ Planned (Alloy model validated, implementation pending)

The GitHub Issues approach uses GitHub Issues and comments for team-based review workflows.

### How It Will Work

1. **Agent Completes Task** → Outputs fail quality gate
2. **Create GitHub Issue** → Title: `[REVIEW] <TASK-ID> - <gate-type>`
3. **Post Quality Report** → As issue description with diff
4. **Assign Reviewers** → Based on gate type (e.g., @security-team for security issues)
5. **Poll for Comments** → Check for approval keywords
6. **Extract Decision** → Parse `@asp-bot approve`, `@asp-bot reject`, etc.
7. **Execute Decision** → Merge or route back
8. **Close Issue** → Add final comment with decision metadata

### Planned Usage (API Preview)

```python
from asp.approval import GitHubIssuesApprovalService

# Create approval service
approval_service = GitHubIssuesApprovalService(
    github_token=os.getenv("GITHUB_TOKEN"),
    repo_owner="your-org",
    repo_name="your-repo",
    reviewer_teams={
        "design_review": ["@architecture-team"],
        "code_review": ["@code-reviewers"],
        "security_review": ["@security-team"]
    },
    poll_interval_seconds=30,  # Check for comments every 30s
    timeout_seconds=3600       # Timeout after 1 hour
)

orchestrator = TSPOrchestrator(approval_service=approval_service)
result = orchestrator.execute(task)
```

### Approval Commands (Planned)

Reviewers will approve/reject via issue comments:

```markdown
<!-- Approve -->
@asp-bot approve

Looks good! Security issues addressed with bcrypt and middleware.

<!-- Reject -->
@asp-bot reject

Still seeing issues:
- Missing rate limiting on /login
- No input validation on username field

Please fix and resubmit.

<!-- Defer -->
@asp-bot defer

Need more time to review. Will check back tomorrow.
```

**Implementation Timeline:** Estimated 8-12 hours development time

---

## CLI-Based HITL

**Status:** ⏸️ Planned

The CLI-based approach provides real-time interactive approval in the terminal.

### How It Will Work

1. **Agent Reaches Gate** → Quality gate check in progress
2. **Pause Execution** → Wait for human input
3. **Present Options** → Terminal UI with diff, report, options
4. **Collect Decision** → Inline in terminal
5. **Resume Execution** → Continue with decision applied

### Planned Usage (API Preview)

```python
from asp.approval import CLIApprovalService

# Create approval service (interactive terminal)
approval_service = CLIApprovalService(
    auto_show_diff=True,  # Always show diff
    timeout_seconds=300   # Timeout after 5 minutes
)

orchestrator = TSPOrchestrator(approval_service=approval_service)
result = orchestrator.execute(task)  # Will pause and prompt in terminal
```

**Implementation Timeline:** Estimated 2-3 hours development time

---

## Configuration

### TSP Orchestrator with HITL

The TSP Orchestrator accepts an optional `approval_service` parameter:

```python
from asp.orchestrators import TSPOrchestrator
from asp.approval import LocalPRApprovalService

# Option 1: HITL enabled (approval required for gate failures)
approval_service = LocalPRApprovalService(repo_path=".")
orchestrator = TSPOrchestrator(approval_service=approval_service)

# Option 2: No HITL (fully autonomous, no human approval)
orchestrator = TSPOrchestrator()  # approval_service=None (default)
```

### Approval Service Priority

If multiple approval mechanisms are available, TSP Orchestrator uses this priority:

1. **Explicit ApprovalService** (passed to constructor) - Highest priority
2. **Callable Function** (custom approval logic)
3. **No Approval** (autonomous mode) - Default

Example with callable:

```python
def custom_approval(request):
    """Custom approval logic."""
    # Your logic here
    return ApprovalResponse(
        decision=ReviewDecision.APPROVED,
        reviewer="auto-approver",
        timestamp=datetime.utcnow().isoformat() + 'Z',
        justification="Auto-approved for low-risk task"
    )

orchestrator = TSPOrchestrator(approval_service=custom_approval)
```

### Environment Variables

Optional environment variables for HITL configuration:

```bash
# GitHub Issues HITL (when implemented)
export GITHUB_TOKEN="ghp_your_token_here"
export GITHUB_REPO_OWNER="your-org"
export GITHUB_REPO_NAME="your-repo"

# Default reviewer assignments
export ASP_DESIGN_REVIEWERS="@architecture-team"
export ASP_CODE_REVIEWERS="@code-reviewers"
export ASP_SECURITY_REVIEWERS="@security-team"
```

---

## Custom Approval Services

You can create custom approval services by implementing the `ApprovalService` interface.

### ApprovalService Interface

```python
from abc import ABC, abstractmethod
from asp.approval.base import ApprovalRequest, ApprovalResponse

class ApprovalService(ABC):
    """Abstract base class for HITL approval services."""

    @abstractmethod
    def request_approval(
        self,
        request: ApprovalRequest
    ) -> ApprovalResponse:
        """
        Request human approval for quality gate failure.

        Args:
            request: ApprovalRequest containing task info and quality report

        Returns:
            ApprovalResponse with decision and metadata
        """
        pass
```

### Example: Slack-Based Approval

```python
from asp.approval.base import (
    ApprovalService,
    ApprovalRequest,
    ApprovalResponse,
    ReviewDecision
)
import requests
from datetime import datetime

class SlackApprovalService(ApprovalService):
    """HITL approval via Slack messages."""

    def __init__(self, webhook_url: str, channel: str):
        self.webhook_url = webhook_url
        self.channel = channel

    def request_approval(
        self,
        request: ApprovalRequest
    ) -> ApprovalResponse:
        """Request approval via Slack message."""

        # Format quality report
        report_summary = self._format_report(request.quality_report)

        # Send Slack message
        message = {
            "channel": self.channel,
            "text": f"🔔 HITL Approval Required",
            "blocks": [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": f"Review Required: {request.task_id}"
                    }
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*Gate Type:* {request.gate_type}\n\n{report_summary}"
                    }
                },
                {
                    "type": "actions",
                    "elements": [
                        {
                            "type": "button",
                            "text": {"type": "plain_text", "text": "✅ Approve"},
                            "style": "primary",
                            "value": "approve"
                        },
                        {
                            "type": "button",
                            "text": {"type": "plain_text", "text": "❌ Reject"},
                            "style": "danger",
                            "value": "reject"
                        }
                    ]
                }
            ]
        }

        requests.post(self.webhook_url, json=message)

        # Wait for response (implement polling or webhook listener)
        decision = self._wait_for_decision(request.task_id)

        return ApprovalResponse(
            decision=decision["decision"],
            reviewer=decision["reviewer"],
            timestamp=datetime.utcnow().isoformat() + 'Z',
            justification=decision["justification"]
        )

    def _format_report(self, quality_report: dict) -> str:
        """Format quality report for Slack."""
        # Implementation here
        pass

    def _wait_for_decision(self, task_id: str) -> dict:
        """Wait for Slack button click (webhook or polling)."""
        # Implementation here
        pass

# Usage
approval_service = SlackApprovalService(
    webhook_url="https://hooks.slack.com/services/YOUR/WEBHOOK/URL",
    channel="#asp-reviews"
)

orchestrator = TSPOrchestrator(approval_service=approval_service)
```

### Example: Auto-Approval for Low-Risk Tasks

```python
class RiskBasedApprovalService(ApprovalService):
    """Automatically approve low-risk tasks, request human approval for high-risk."""

    def __init__(self, fallback_service: ApprovalService):
        self.fallback_service = fallback_service

    def request_approval(
        self,
        request: ApprovalRequest
    ) -> ApprovalResponse:
        """Auto-approve low-risk, delegate high-risk to human."""

        risk_level = self._assess_risk(request)

        if risk_level == "LOW":
            # Auto-approve
            return ApprovalResponse(
                decision=ReviewDecision.APPROVED,
                reviewer="auto-approver",
                timestamp=datetime.utcnow().isoformat() + 'Z',
                justification=f"Auto-approved: {risk_level} risk task"
            )
        else:
            # Delegate to human
            return self.fallback_service.request_approval(request)

    def _assess_risk(self, request: ApprovalRequest) -> str:
        """Assess risk level based on quality report."""
        report = request.quality_report

        # Check for critical defects
        for review in report.get("specialist_reviews", []):
            for defect in review.get("defects", []):
                if defect.get("severity") == "CRITICAL":
                    return "HIGH"

        # Check for security issues
        if request.gate_type == "design_review":
            security_review = report.get("security_review", {})
            if len(security_review.get("defects", [])) > 0:
                return "MEDIUM"

        return "LOW"

# Usage
human_approval = LocalPRApprovalService(repo_path=".")
smart_approval = RiskBasedApprovalService(fallback_service=human_approval)

orchestrator = TSPOrchestrator(approval_service=smart_approval)
```

---

## API Reference

### ApprovalRequest

Request for human approval of quality gate failure.

```python
@dataclass
class ApprovalRequest:
    task_id: str                    # Task identifier (e.g., "FEAT-001")
    gate_type: str                  # "design_review", "code_review", etc.
    agent_output: Dict[str, Any]    # Agent's output artifacts
    quality_report: Dict[str, Any]  # Quality gate report with defects
    base_branch: str = "main"       # Base branch for merges
```

### ApprovalResponse

Response containing approval decision and metadata.

```python
@dataclass
class ApprovalResponse:
    decision: ReviewDecision         # APPROVED, REJECTED, DEFERRED
    reviewer: str                    # Reviewer email or username
    timestamp: str                   # ISO 8601 timestamp (UTC)
    justification: str               # Required reason for decision
    review_branch: Optional[str]     # Feature branch name (if applicable)
    merge_commit: Optional[str]      # Merge commit SHA (if approved)
```

### ReviewDecision

Enum for review decision options.

```python
class ReviewDecision(Enum):
    APPROVED = "approved"   # Merge changes, continue pipeline
    REJECTED = "rejected"   # Do not merge, route back to originating phase
    DEFERRED = "deferred"   # Save decision for later review
```

---

## Troubleshooting

### Common Issues

#### 1. "Not a git repository" Error

**Cause:** `LocalPRApprovalService` requires a valid git repository

**Solution:**
```bash
# Initialize git repo if needed
git init
git add .
git commit -m "Initial commit"

# Or specify correct repo path
approval_service = LocalPRApprovalService(repo_path="/path/to/git/repo")
```

#### 2. Branch Already Exists

**Cause:** Previous review branch wasn't cleaned up

**Solution:**
```bash
# Manually delete old review branches
git branch -D review/TASK-001-design_review

# Or enable auto-cleanup
approval_service = LocalPRApprovalService(auto_cleanup=True)
```

#### 3. Git Notes Not Showing

**Cause:** Git notes aren't automatically fetched/pushed

**Solution:**
```bash
# Fetch notes from remote
git fetch origin refs/notes/reviews:refs/notes/reviews

# Push notes to remote
git push origin refs/notes/reviews:refs/notes/reviews

# View notes
git notes --ref=reviews show <commit-sha>
```

#### 4. Approval Service Not Called

**Cause:** Quality gates passed (no approval needed)

**Solution:**

HITL approval is only requested when quality gates **FAIL**. If all quality gates pass, approval is not needed.

To test HITL, intentionally create a task that will fail quality gates (e.g., task with security requirements but no authentication).

#### 5. Terminal UI Not Rendering Correctly

**Cause:** Terminal doesn't support Rich library formatting

**Solution:**
```bash
# Check terminal compatibility
python -c "from rich.console import Console; Console().print('[green]✓ Rich supported[/green]')"

# If not supported, use plain text mode (implementation pending)
approval_service = LocalPRApprovalService(rich_ui=False)
```

### Debugging HITL Workflows

Enable debug logging:

```python
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("asp.approval")

# Now HITL operations will be logged
```

Check approval service activity:

```bash
# View recent review branches
git branch -a | grep review/

# View git notes for all commits
git log --show-notes=reviews

# Check for merge commits
git log --merges --oneline
```

---

## Next Steps

Ready to dive deeper?

1. **[Agent Reference](Agents_Reference.md)** - Understand quality gates and review agents
2. **[Developer Guide](Developer_Guide.md)** - Build custom approval services
3. **[API Reference](API_Reference.md)** - Complete API documentation
4. **Examples:** Check `examples/` directory for runnable HITL demos

---

## Summary

**HITL enables safe AI autonomy with human oversight for critical decisions.**

Key takeaways:
- ✅ **Three approaches:** Local PR, GitHub Issues (planned), CLI (planned)
- ✅ **Complete audit trail:** All decisions logged with justifications
- ✅ **Flexible configuration:** Use HITL selectively or for all gates
- ✅ **Custom services:** Build your own approval mechanisms
- ✅ **Production-ready:** E2E tested and validated

HITL is **optional** - use it when you need human oversight, skip it for fully autonomous operation.

---

**Built with ASP Platform v1.0**

*Safe autonomy through Human-In-The-Loop approval workflows.*
