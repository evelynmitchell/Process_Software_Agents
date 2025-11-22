# HITL Quality Gate Architecture
## Human-in-the-Loop Approval Workflow Design

**Document ID:** ARCH-HITL-001
**Version:** 1.0
**Date:** November 22, 2025
**Status:** DRAFT - Architecture Proposal
**Author:** ASP Development Team

---

## 1. Executive Summary

### 1.1 Purpose

This document defines the architecture for a production-ready Human-in-the-Loop (HITL) Quality Gate system for the ASP platform. The current implementation uses a synchronous callback (`hitl_approver=lambda gate, report: True`) suitable only for testing. This design specifies a real-world workflow that:

1. **Pauses pipeline execution** when quality gates fail
2. **Presents review reports** to humans in a consumable format
3. **Captures approval decisions** with justification
4. **Resumes execution** based on human input
5. **Maintains complete audit trail** of all HITL decisions

### 1.2 Current State Analysis

**Existing Implementation (TSP Orchestrator):**
- Location: `src/asp/orchestrators/tsp_orchestrator.py:444-451`
- Mechanism: Synchronous callback function
- Quality Gates: Design Review, Code Review
- Limitation: No mechanism for actual human interaction

**Quality Gate Triggers (per PRD):**
- **Design Review FAIL:** Critical issues OR high-priority issues detected
- **Code Review FAIL:** Critical issues OR ≥5 high-priority issues
- **Test FAIL:** Build failures or test failures (no HITL override allowed)

**PRD Requirements:**
- FR-15: HITL approval for PIP proposals and quality gate overrides
- NFR-17: HITL interfaces must support approval within 3 clicks
- NFR-8: Quality gates must be fail-safe (default to blocking)

### 1.3 Design Goals

1. **Minimal Disruption:** Integrate with existing TSP Orchestrator without refactoring core logic
2. **Multiple Interface Options:** Support CLI, GitHub Issues, API, and future Web UI
3. **Leverage Existing Infrastructure:** Use GitHub for approvals (zero new infrastructure)
4. **Async Execution:** Allow pipeline to pause and resume gracefully
5. **Audit Trail:** Log all HITL decisions for compliance and analysis
6. **Timeout Handling:** Define behavior when humans don't respond within SLA
7. **Extensibility:** Support future approval types (e.g., PIP reviews, deployment gates)

### 1.4 Recommended Implementation Path ⭐

**Phase 1A (CLI) + Phase 1B (GitHub Issues)** provides the best immediate value:

| Approach | Use Case | Effort | Infrastructure |
|----------|----------|--------|----------------|
| **CLI (Phase 1A)** | Local development, solo work | 16-20h | None |
| **GitHub Issues (Phase 1B)** ⭐ | Team workflows, CI/CD | 8-12h | GitHub only |
| **REST API (Phase 2)** | Enterprise integration | 12-16h | DB + API server |
| **Web Dashboard (Phase 3)** | Non-technical stakeholders | 40-60h | DB + API + React |

**Why GitHub Issues is Recommended:**
- ✅ Project already git-centric (all artifacts in repo)
- ✅ Zero infrastructure (no database, no API server)
- ✅ Better audit trail than custom database (immutable GitHub history)
- ✅ Native notifications (email, mobile, Slack)
- ✅ Team-friendly (engineers already monitor GitHub)
- ✅ Faster to implement than custom database (8-12h vs. 20h)

See Section 3.1B for full GitHub Issues design and Section 10.2 for detailed analysis.

---

## 2. Architecture Overview

### 2.1 High-Level Design

```
┌─────────────────────────────────────────────────────────────────┐
│                     TSP Orchestrator                             │
│  ┌────────────────┐    ┌──────────────┐    ┌────────────────┐   │
│  │ Design Phase   │───▶│ Quality Gate │───▶│ HITL Request   │   │
│  │ (Agent Exec)   │    │ Evaluation   │    │ (if FAIL)      │   │
│  └────────────────┘    └──────────────┘    └────────┬───────┘   │
└───────────────────────────────────────────────────────┼──────────┘
                                                        │
                    ┌───────────────────────────────────▼──────────┐
                    │      HITL Approval Service (New)              │
                    │  ┌────────────────────────────────────────┐   │
                    │  │  Approval Request Queue                │   │
                    │  │  - Pending requests                    │   │
                    │  │  - Timeout tracking                    │   │
                    │  │  - Status: pending/approved/rejected   │   │
                    │  └────────────────────────────────────────┘   │
                    │  ┌────────────────────────────────────────┐   │
                    │  │  Report Formatter                      │   │
                    │  │  - Markdown renderer                   │   │
                    │  │  - Issue summaries                     │   │
                    │  │  - Risk assessments                    │   │
                    │  └────────────────────────────────────────┘   │
                    │  ┌────────────────────────────────────────┐   │
                    │  │  Approval Decision Logger              │   │
                    │  │  - Audit trail (who/when/why)          │   │
                    │  │  - Integration with Langfuse           │   │
                    │  └────────────────────────────────────────┘   │
                    └──────────┬─────────────────────────────────────┘
                               │
          ┌────────────────────┼────────────────────┐
          │                    │                    │
          ▼                    ▼                    ▼
    ┌──────────┐         ┌──────────┐        ┌──────────┐
    │ CLI UI   │         │ REST API │        │ Web UI   │
    │ (Phase 1)│         │ (Phase 2)│        │ (Phase 3)│
    └──────────┘         └──────────┘        └──────────┘
          │                    │                    │
          └────────────────────┼────────────────────┘
                               ▼
                    ┌─────────────────────┐
                    │  Human Reviewer     │
                    │  - View report      │
                    │  - Approve/Reject   │
                    │  - Add justification│
                    └─────────────────────┘
```

### 2.2 Key Components

#### 2.2.1 HITL Approval Service (Core)
- **Purpose:** Central service for managing approval requests lifecycle
- **Responsibilities:**
  - Queue approval requests from orchestrator
  - Track request status (pending → approved/rejected/timeout)
  - Format review reports for human consumption
  - Record approval decisions with audit metadata
  - Notify orchestrator when decision is made

#### 2.2.2 Approval Request Queue
- **Storage:** SQLite database (local) or PostgreSQL (production)
- **Schema:**
  ```python
  ApprovalRequest:
    - request_id: UUID
    - task_id: str
    - gate_name: str (DesignReview, CodeReview, PIPApproval)
    - report: JSON (full review report)
    - status: enum (PENDING, APPROVED, REJECTED, TIMEOUT)
    - created_at: datetime
    - timeout_at: datetime
    - decision_at: datetime (nullable)
    - approver_id: str (nullable)
    - justification: str (nullable)
  ```

#### 2.2.3 Report Formatter
- **Purpose:** Transform review reports into human-readable format
- **Capabilities:**
  - Markdown rendering for CLI display
  - HTML rendering for Web UI
  - JSON API responses
  - Issue prioritization and grouping
  - Risk scoring summaries

#### 2.2.4 User Interfaces (Phased Rollout)

**Phase 1: CLI Interface (MVP)**
- Interactive terminal prompts
- Displays formatted reports
- Collects approval decision inline
- No external dependencies

**Phase 2: REST API + Webhook**
- API endpoints for pending requests
- Webhook notifications when requests created
- Integration with Slack/Teams/email
- Supports custom approval workflows

**Phase 3: Web Dashboard**
- Browser-based approval interface
- Batch approval capabilities
- Historical review analytics
- Mobile-responsive design

---

## 3. Detailed Design

### 3.1 Phase 1: CLI-Based HITL (MVP)

#### 3.1.1 Workflow

```
┌─────────────────────────────────────────────────────────────────┐
│ TSP Orchestrator Execution                                       │
└───────────────────┬─────────────────────────────────────────────┘
                    │
                    ▼
    ┌───────────────────────────────┐
    │ Design Review Agent Executes  │
    └───────────────┬───────────────┘
                    │
                    ▼
    ┌───────────────────────────────┐
    │ Quality Gate Evaluation       │
    │ Status: FAIL (4H, 7M issues)  │
    └───────────────┬───────────────┘
                    │
                    ▼
    ┌───────────────────────────────────────────────┐
    │ HITL Approval Service                         │
    │ 1. Create approval request in queue           │
    │ 2. Format review report (markdown)            │
    │ 3. Return formatted report to orchestrator    │
    └───────────────┬───────────────────────────────┘
                    │
                    ▼
    ┌───────────────────────────────────────────────┐
    │ CLI Prompt (Blocking)                         │
    │ ┌─────────────────────────────────────────┐   │
    │ │ ═══════════════════════════════════════ │   │
    │ │ QUALITY GATE FAILURE: Design Review    │   │
    │ │ ═══════════════════════════════════════ │   │
    │ │                                          │   │
    │ │ Task ID: TSP-FIB-001                     │   │
    │ │ Gate: Design Review                      │   │
    │ │ Status: FAIL                             │   │
    │ │                                          │   │
    │ │ Issue Summary:                           │   │
    │ │ • Critical: 0                            │   │
    │ │ • High: 4                                │   │
    │ │ • Medium: 7                              │   │
    │ │ • Low: 4                                 │   │
    │ │                                          │   │
    │ │ Top Issues:                              │   │
    │ │ [H] Missing error handling (3 locations)│   │
    │ │ [H] No input validation (2 locations)   │   │
    │ │ [M] Suboptimal data structure (1 loc)   │   │
    │ │                                          │   │
    │ │ Commands:                                │   │
    │ │   [v]iew  - View full report            │   │
    │ │   [a]pprove - Approve override          │   │
    │ │   [r]eject  - Reject (halt pipeline)    │   │
    │ │   [i]ssues  - List all issues           │   │
    │ │                                          │   │
    │ │ Decision [v/a/r/i]: _                   │   │
    │ └─────────────────────────────────────────┘   │
    └───────────────────────────────────────────────┘
                    │
                    ▼
    ┌───────────────────────────────────────────────┐
    │ User selects: [a]pprove                       │
    └───────────────┬───────────────────────────────┘
                    │
                    ▼
    ┌───────────────────────────────────────────────┐
    │ Justification Prompt                          │
    │ > Justification: Low-risk Fibonacci impl,     │
    │   error handling not critical for demo        │
    └───────────────┬───────────────────────────────┘
                    │
                    ▼
    ┌───────────────────────────────────────────────┐
    │ HITL Approval Service                         │
    │ 1. Update approval request status: APPROVED   │
    │ 2. Record: approver, timestamp, justification │
    │ 3. Log to Langfuse (audit trail)              │
    │ 4. Return decision to orchestrator            │
    └───────────────┬───────────────────────────────┘
                    │
                    ▼
    ┌───────────────────────────────────────────────┐
    │ TSP Orchestrator Resumes                      │
    │ ✓ HITL override approved - proceeding         │
    │ Next: Code Agent execution...                 │
    └───────────────────────────────────────────────┘
```

#### 3.1.2 Implementation Details

**File Structure:**
```
src/asp/hitl/
├── __init__.py
├── approval_service.py      # Core HITL service
├── request_queue.py          # SQLite-based approval queue
├── report_formatters.py      # Markdown/HTML/JSON formatters
├── cli_interface.py          # Interactive CLI prompts
└── audit_logger.py           # Langfuse integration

src/asp/models/
└── hitl.py                   # Pydantic models for HITL

tests/unit/test_hitl/
├── test_approval_service.py
├── test_request_queue.py
└── test_cli_interface.py
```

**Key Classes:**

```python
# src/asp/models/hitl.py
from enum import Enum
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, Any
from uuid import UUID, uuid4

class ApprovalStatus(str, Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    TIMEOUT = "TIMEOUT"

class GateType(str, Enum):
    DESIGN_REVIEW = "DesignReview"
    CODE_REVIEW = "CodeReview"
    PIP_APPROVAL = "PIPApproval"

class ApprovalRequest(BaseModel):
    """Approval request submitted to HITL queue."""
    request_id: UUID = Field(default_factory=uuid4)
    task_id: str
    gate_name: GateType
    report: dict[str, Any]  # Full review report (DesignReviewReport, etc.)
    status: ApprovalStatus = ApprovalStatus.PENDING
    created_at: datetime = Field(default_factory=datetime.utcnow)
    timeout_at: Optional[datetime] = None
    timeout_seconds: int = 86400  # 24 hours default

class ApprovalDecision(BaseModel):
    """Decision recorded by human reviewer."""
    request_id: UUID
    status: ApprovalStatus  # APPROVED or REJECTED
    approver_id: str  # Username or email
    justification: str
    decision_at: datetime = Field(default_factory=datetime.utcnow)

class HITLApprovalResult(BaseModel):
    """Result returned to orchestrator."""
    approved: bool
    decision: ApprovalDecision
    request: ApprovalRequest
```

```python
# src/asp/hitl/approval_service.py
from typing import Optional, Callable
import logging
from datetime import datetime, timedelta

from asp.hitl.request_queue import ApprovalRequestQueue
from asp.hitl.report_formatters import ReportFormatter
from asp.hitl.audit_logger import AuditLogger
from asp.models.hitl import (
    ApprovalRequest,
    ApprovalDecision,
    ApprovalStatus,
    GateType,
    HITLApprovalResult,
)

logger = logging.getLogger(__name__)

class HITLApprovalService:
    """
    Core HITL Approval Service.

    Manages approval request lifecycle:
    1. Queue approval requests from orchestrator
    2. Present requests to human via interface (CLI/API/Web)
    3. Record decisions with audit trail
    4. Return results to orchestrator

    Example:
        >>> service = HITLApprovalService(interface="cli")
        >>> request = ApprovalRequest(
        ...     task_id="TSP-FIB-001",
        ...     gate_name=GateType.DESIGN_REVIEW,
        ...     report=design_review.model_dump()
        ... )
        >>> result = service.request_approval(request)
        >>> if result.approved:
        ...     print(f"Approved by {result.decision.approver_id}")
    """

    def __init__(
        self,
        interface: str = "cli",  # "cli", "api", "web"
        queue: Optional[ApprovalRequestQueue] = None,
        formatter: Optional[ReportFormatter] = None,
        audit_logger: Optional[AuditLogger] = None,
        timeout_seconds: int = 86400,  # 24 hours
    ):
        """
        Initialize HITL Approval Service.

        Args:
            interface: User interface type ("cli", "api", "web")
            queue: Approval request queue (default: SQLite-based)
            formatter: Report formatter (default: Markdown)
            audit_logger: Audit trail logger (default: Langfuse)
            timeout_seconds: Default timeout for approval requests
        """
        self.interface = interface
        self.queue = queue or ApprovalRequestQueue()
        self.formatter = formatter or ReportFormatter()
        self.audit_logger = audit_logger or AuditLogger()
        self.timeout_seconds = timeout_seconds

        # Interface handlers
        self._interface_handlers = {
            "cli": self._request_approval_cli,
            "api": self._request_approval_api,
            "web": self._request_approval_web,
        }

    def request_approval(
        self,
        task_id: str,
        gate_name: GateType,
        report: dict,
    ) -> HITLApprovalResult:
        """
        Request approval from human reviewer.

        This is the main entry point called by TSP Orchestrator when
        quality gate fails.

        Workflow:
        1. Create approval request
        2. Add to queue
        3. Present to human via interface
        4. Wait for decision (blocking or async)
        5. Record decision in audit trail
        6. Return result

        Args:
            task_id: Task identifier (e.g., "TSP-FIB-001")
            gate_name: Quality gate type (DesignReview, CodeReview)
            report: Full review report dictionary

        Returns:
            HITLApprovalResult with approval decision

        Raises:
            TimeoutError: If approval not received within timeout
        """
        # Create approval request
        request = ApprovalRequest(
            task_id=task_id,
            gate_name=gate_name,
            report=report,
            timeout_at=datetime.utcnow() + timedelta(seconds=self.timeout_seconds),
            timeout_seconds=self.timeout_seconds,
        )

        # Add to queue
        self.queue.enqueue(request)
        logger.info(
            f"HITL approval request queued: {request.request_id} "
            f"(task={task_id}, gate={gate_name})"
        )

        # Dispatch to interface handler
        handler = self._interface_handlers.get(self.interface)
        if not handler:
            raise ValueError(f"Unknown interface: {self.interface}")

        try:
            result = handler(request)

            # Record in audit trail
            self.audit_logger.log_decision(result)

            return result

        except TimeoutError:
            # Update request status
            self.queue.update_status(request.request_id, ApprovalStatus.TIMEOUT)
            logger.warning(
                f"HITL approval timeout: {request.request_id} "
                f"(timeout={self.timeout_seconds}s)"
            )
            raise

    def _request_approval_cli(self, request: ApprovalRequest) -> HITLApprovalResult:
        """
        CLI-based approval workflow (blocking, interactive).

        Displays formatted report in terminal and prompts human for decision.
        """
        from asp.hitl.cli_interface import CLIApprovalInterface

        cli = CLIApprovalInterface(formatter=self.formatter)
        decision = cli.prompt_for_approval(request)

        # Update queue
        self.queue.record_decision(request.request_id, decision)

        return HITLApprovalResult(
            approved=(decision.status == ApprovalStatus.APPROVED),
            decision=decision,
            request=request,
        )

    def _request_approval_api(self, request: ApprovalRequest) -> HITLApprovalResult:
        """
        API-based approval workflow (non-blocking, webhook-driven).

        Creates approval request in queue and waits for external decision via API.
        """
        # Non-blocking: Request is already in queue
        # Wait for decision (polling or event-driven)
        logger.info(
            f"Approval request {request.request_id} pending API decision. "
            f"View at: http://localhost:8000/approvals/{request.request_id}"
        )

        # Poll for decision (simplistic implementation)
        decision = self.queue.wait_for_decision(
            request.request_id,
            timeout_seconds=self.timeout_seconds,
        )

        return HITLApprovalResult(
            approved=(decision.status == ApprovalStatus.APPROVED),
            decision=decision,
            request=request,
        )

    def _request_approval_web(self, request: ApprovalRequest) -> HITLApprovalResult:
        """
        Web UI approval workflow (non-blocking, browser-based).

        Similar to API mode but with browser notification.
        """
        # Trigger browser notification (future: WebSocket push)
        logger.info(
            f"Approval request {request.request_id} pending Web UI decision. "
            f"View at: http://localhost:8080/approvals/{request.request_id}"
        )

        # Wait for decision
        decision = self.queue.wait_for_decision(
            request.request_id,
            timeout_seconds=self.timeout_seconds,
        )

        return HITLApprovalResult(
            approved=(decision.status == ApprovalStatus.APPROVED),
            decision=decision,
            request=request,
        )

    def get_pending_requests(self) -> list[ApprovalRequest]:
        """Get all pending approval requests (for dashboard)."""
        return self.queue.get_pending()

    def get_request_history(
        self, task_id: Optional[str] = None
    ) -> list[ApprovalRequest]:
        """Get historical approval requests for analysis."""
        return self.queue.get_history(task_id=task_id)
```

```python
# src/asp/hitl/cli_interface.py
import sys
from typing import Optional
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.markdown import Markdown

from asp.models.hitl import (
    ApprovalRequest,
    ApprovalDecision,
    ApprovalStatus,
    GateType,
)
from asp.hitl.report_formatters import ReportFormatter

console = Console()

class CLIApprovalInterface:
    """
    Interactive CLI interface for HITL approval.

    Displays formatted review reports and prompts human for decision.
    """

    def __init__(self, formatter: Optional[ReportFormatter] = None):
        self.formatter = formatter or ReportFormatter()

    def prompt_for_approval(self, request: ApprovalRequest) -> ApprovalDecision:
        """
        Display approval request and prompt for decision.

        Returns:
            ApprovalDecision with human's choice
        """
        # Clear screen and display header
        console.clear()
        self._display_header(request)

        # Display formatted report
        self._display_report(request)

        # Prompt for decision
        while True:
            console.print("\n[bold yellow]Commands:[/bold yellow]")
            console.print("  [v]iew   - View full report")
            console.print("  [a]pprove - Approve override and continue")
            console.print("  [r]eject  - Reject and halt pipeline")
            console.print("  [i]ssues  - List all issues in detail")

            choice = console.input("\n[bold cyan]Decision [v/a/r/i]:[/bold cyan] ").lower()

            if choice == "v":
                self._display_full_report(request)
            elif choice == "i":
                self._display_issues(request)
            elif choice == "a":
                return self._approve(request)
            elif choice == "r":
                return self._reject(request)
            else:
                console.print("[red]Invalid choice. Please enter v, a, r, or i.[/red]")

    def _display_header(self, request: ApprovalRequest):
        """Display approval request header."""
        header = f"""
[bold red]═══════════════════════════════════════════════════════[/bold red]
[bold red]QUALITY GATE FAILURE[/bold red]
[bold red]═══════════════════════════════════════════════════════[/bold red]

[bold]Task ID:[/bold] {request.task_id}
[bold]Gate:[/bold] {request.gate_name.value}
[bold]Status:[/bold] [red]FAIL[/red]
[bold]Timeout:[/bold] {request.timeout_at.strftime('%Y-%m-%d %H:%M:%S UTC')}
"""
        console.print(Panel(header, border_style="red"))

    def _display_report(self, request: ApprovalRequest):
        """Display formatted report summary."""
        summary = self.formatter.format_summary(request.gate_name, request.report)
        console.print(Markdown(summary))

    def _display_full_report(self, request: ApprovalRequest):
        """Display complete report in detail."""
        full_report = self.formatter.format_full(request.gate_name, request.report)
        console.print(Markdown(full_report))
        console.input("\n[dim]Press Enter to continue...[/dim]")

    def _display_issues(self, request: ApprovalRequest):
        """Display all issues in table format."""
        issues = self.formatter.extract_issues(request.gate_name, request.report)

        table = Table(title="All Issues")
        table.add_column("Severity", style="cyan")
        table.add_column("Type", style="magenta")
        table.add_column("Description")
        table.add_column("Location")

        for issue in issues:
            severity_color = {
                "CRITICAL": "red",
                "HIGH": "yellow",
                "MEDIUM": "blue",
                "LOW": "green",
            }.get(issue["severity"], "white")

            table.add_row(
                f"[{severity_color}]{issue['severity']}[/{severity_color}]",
                issue["type"],
                issue["description"],
                issue.get("location", "N/A"),
            )

        console.print(table)
        console.input("\n[dim]Press Enter to continue...[/dim]")

    def _approve(self, request: ApprovalRequest) -> ApprovalDecision:
        """Approve override with justification."""
        console.print("\n[bold yellow]Approval requires justification.[/bold yellow]")
        console.print("[dim]Explain why it's acceptable to proceed despite failures.[/dim]\n")

        justification = console.input("[cyan]Justification:[/cyan] ").strip()

        if not justification:
            console.print("[red]Justification is required for approval.[/red]")
            return self._approve(request)  # Retry

        approver_id = console.input("[cyan]Your name/email:[/cyan] ").strip() or "unknown"

        console.print("\n[bold green]✓ Approval recorded. Pipeline will continue.[/bold green]")

        return ApprovalDecision(
            request_id=request.request_id,
            status=ApprovalStatus.APPROVED,
            approver_id=approver_id,
            justification=justification,
        )

    def _reject(self, request: ApprovalRequest) -> ApprovalDecision:
        """Reject override and halt pipeline."""
        console.print("\n[bold red]Pipeline will be halted.[/bold red]")

        approver_id = console.input("[cyan]Your name/email:[/cyan] ").strip() or "unknown"
        justification = console.input(
            "[cyan]Reason for rejection (optional):[/cyan] "
        ).strip() or "Quality gate failure deemed unacceptable"

        console.print("\n[bold red]✗ Override rejected. Pipeline halted.[/bold red]")

        return ApprovalDecision(
            request_id=request.request_id,
            status=ApprovalStatus.REJECTED,
            approver_id=approver_id,
            justification=justification,
        )
```

#### 3.1.3 Integration with TSP Orchestrator

**Modification to `tsp_orchestrator.py`:**

```python
# src/asp/orchestrators/tsp_orchestrator.py

from asp.hitl.approval_service import HITLApprovalService
from asp.models.hitl import GateType

class TSPOrchestrator:
    def __init__(
        self,
        ...,
        hitl_service: Optional[HITLApprovalService] = None,
    ):
        ...
        self.hitl_service = hitl_service or HITLApprovalService(interface="cli")

    def _execute_design_with_review(
        self,
        requirements: TaskRequirements,
        hitl_approver: Optional[callable],  # DEPRECATED
    ) -> tuple[DesignSpecification, DesignReviewReport]:
        ...
        # Design FAILED - check for HITL override
        if design_review.overall_assessment == "FAIL":
            logger.warning(f"⚠ Design FAILED review...")

            # NEW: Use HITL service instead of callback
            if self.hitl_service:
                result = self.hitl_service.request_approval(
                    task_id=requirements.task_id,
                    gate_name=GateType.DESIGN_REVIEW,
                    report=design_review.model_dump(),
                )

                if result.approved:
                    logger.info(
                        f"✓ HITL override approved by {result.decision.approver_id}: "
                        f"{result.decision.justification}"
                    )
                    self._record_hitl_override(
                        "DesignReview",
                        design_review,
                        f"APPROVED by {result.decision.approver_id}",
                    )
                    return design_spec, design_review
                else:
                    logger.error(
                        f"✗ HITL override rejected by {result.decision.approver_id}: "
                        f"{result.decision.justification}"
                    )
                    raise QualityGateFailure(
                        f"Design Review FAILED and HITL override rejected. "
                        f"Reason: {result.decision.justification}"
                    )

            # LEGACY: Fall back to callback for backwards compatibility
            elif hitl_approver:
                approved = hitl_approver(
                    gate_name="DesignReview",
                    report=design_review.model_dump(),
                )
                if approved:
                    logger.info("✓ HITL override approved (legacy callback)")
                    self._record_hitl_override("DesignReview", design_review, "Approved")
                    return design_spec, design_review

            # No HITL or rejected - attempt correction
            ...
```

**Backwards Compatibility:**
- Legacy `hitl_approver` callback still works for testing
- New `hitl_service` parameter preferred for production
- If both provided, `hitl_service` takes precedence

---

### 3.1B Phase 1B: GitHub Issues-Based HITL (Team Workflow)

#### 3.1B.1 Overview

**Context:** This project is already git-centric, storing all artifacts (designs, code, tests, session summaries) in the GitHub repository. GitHub Issues provides a natural, zero-infrastructure extension of this workflow for HITL approvals.

**Key Advantages Over Custom Database:**
- ✅ **Zero Infrastructure:** No database, no API server, uses existing GitHub
- ✅ **Built-in Audit Trail:** Immutable issue history with timestamps and authors
- ✅ **Native Notifications:** Email, mobile app, Slack integration (GitHub native)
- ✅ **Searchable:** Query language (`is:issue label:approval-required`)
- ✅ **Team Collaboration:** Discussion threads, @mentions, assignees
- ✅ **Access Control:** Leverages existing GitHub org permissions
- ✅ **Integrates with CI/CD:** GitHub Actions can consume approval decisions

**When to Use:**
- Team/multi-developer workflows (vs. solo CLI)
- CI/CD pipeline executions (async approvals)
- Distributed teams (async, timezone-friendly)
- Audit compliance requirements (GitHub Enterprise logging)

**When NOT to Use:**
- High-frequency approvals (>100/day due to API rate limits)
- Offline environments (requires GitHub connectivity)
- Non-GitHub users (requires GitHub account)
- Sub-second latency requirements (webhook delays ~1-5s)

#### 3.1B.2 Workflow

```
┌─────────────────────────────────────────────────────────────────┐
│ TSP Orchestrator Execution (in CI/CD or local)                   │
└───────────────────┬─────────────────────────────────────────────┘
                    │
                    ▼
    ┌───────────────────────────────┐
    │ Design Review Agent Executes  │
    └───────────────┬───────────────┘
                    │
                    ▼
    ┌───────────────────────────────┐
    │ Quality Gate Evaluation       │
    │ Status: FAIL (4H, 7M issues)  │
    └───────────────┬───────────────┘
                    │
                    ▼
    ┌────────────────────────────────────────────────────┐
    │ GitHub Issue Approval Service                       │
    │ 1. Format review report as Markdown                 │
    │ 2. Create GitHub issue via API                      │
    │ 3. Add labels: approval-required, design-review     │
    │ 4. Assign to team lead / approver                   │
    │ 5. Set due date (timeout) using milestones          │
    │ 6. Return issue URL to orchestrator                 │
    └───────────────┬────────────────────────────────────┘
                    │
                    ▼
    ┌────────────────────────────────────────────────────┐
    │ GitHub Issue Created                                │
    │ https://github.com/user/repo/issues/42              │
    │                                                      │
    │ Title: [APPROVAL REQUIRED] TSP-FIB-001 Design      │
    │        Review Failed                                │
    │                                                      │
    │ Labels: approval-required, design-review,           │
    │         TSP-FIB-001                                 │
    │ Assignee: @engineering-manager                      │
    │ Milestone: Timeout 2025-11-23 14:30 UTC             │
    └───────────────┬────────────────────────────────────┘
                    │
                    ▼
    ┌────────────────────────────────────────────────────┐
    │ Notifications Sent (GitHub Native)                  │
    │ • Email to @engineering-manager                     │
    │ • Mobile app notification                           │
    │ • Slack notification (if GitHub bot configured)     │
    └───────────────┬────────────────────────────────────┘
                    │
                    ▼
    ┌────────────────────────────────────────────────────┐
    │ TSP Orchestrator Pauses                             │
    │ • Polls issue for approval decision (every 30s)     │
    │ • Or waits for webhook trigger                      │
    │ • Timeout: 24 hours (configurable)                  │
    └───────────────┬────────────────────────────────────┘
                    │
              [Human Reviews]
                    │
                    ▼
    ┌────────────────────────────────────────────────────┐
    │ Human Reviewer (on GitHub.com or mobile)            │
    │ 1. Clicks issue notification                        │
    │ 2. Reads formatted report in issue body             │
    │ 3. Clicks "View Full Report" link to artifact       │
    │ 4. Optionally discusses in comment thread           │
    │ 5. Posts approval decision as comment:              │
    │                                                      │
    │    /approve Low-risk Fibonacci demo, error          │
    │    handling not critical for educational use        │
    │                                                      │
    │    OR                                                │
    │                                                      │
    │    /reject Design has critical security flaw in     │
    │    input validation, cannot proceed                 │
    └───────────────┬────────────────────────────────────┘
                    │
                    ▼
    ┌────────────────────────────────────────────────────┐
    │ GitHub Webhook Fired                                │
    │ Event: issue_comment                                │
    │ Payload: comment body, author, timestamp            │
    └───────────────┬────────────────────────────────────┘
                    │
                    ▼
    ┌────────────────────────────────────────────────────┐
    │ Approval Parser (webhook listener)                  │
    │ 1. Receive webhook event                            │
    │ 2. Parse comment body with regex:                   │
    │    ^/(approve|reject)\s+(.+)$                       │
    │ 3. Extract: decision, justification, author         │
    │ 4. Validate: author has approval permissions        │
    │ 5. Update issue:                                    │
    │    - Add label: approved OR rejected                │
    │    - Close issue with resolution comment            │
    │    - Record decision in git (approval manifest)     │
    └───────────────┬────────────────────────────────────┘
                    │
                    ▼
    ┌────────────────────────────────────────────────────┐
    │ TSP Orchestrator Notified                           │
    │ • Polling detects issue status change               │
    │ • Or webhook triggers orchestrator callback         │
    │ • Reads decision from issue labels/comments         │
    └───────────────┬────────────────────────────────────┘
                    │
            ┌───────┴────────┐
            │                │
            ▼                ▼
    ┌──────────────┐  ┌──────────────┐
    │ APPROVED     │  │ REJECTED     │
    │ Resume       │  │ Halt         │
    │ pipeline     │  │ pipeline     │
    └──────┬───────┘  └──────┬───────┘
           │                 │
           ▼                 ▼
    ┌──────────────┐  ┌──────────────┐
    │ Log to       │  │ Raise        │
    │ Langfuse     │  │ QualityGate  │
    │ + git commit │  │ Failure      │
    └──────────────┘  └──────────────┘
```

#### 3.1B.3 GitHub Issue Template

When a quality gate fails, the service creates an issue with this structure:

```markdown
## Quality Gate Failure: Design Review

**Task ID:** TSP-FIB-001
**Gate:** Design Review
**Status:** ❌ FAIL
**Created:** 2025-11-22 14:30:00 UTC
**Timeout:** 2025-11-23 14:30:00 UTC (24 hours)

---

### Issue Summary

| Severity | Count |
|----------|-------|
| Critical | 0     |
| High     | 4     |
| Medium   | 7     |
| Low      | 4     |

### Top Issues

#### [HIGH] Missing Error Handling (3 locations)
- `FibonacciCalculator`: No validation for negative inputs
- `APIEndpoint`: No rate limiting or auth checks
- `DatabaseClient`: No connection timeout handling

#### [HIGH] No Input Validation (2 APIs)
- `POST /calculate`: Missing type validation for 'n' parameter
- `GET /history`: No pagination limits (DoS risk)

#### [MEDIUM] Suboptimal Data Structure Choice
- Using list for result cache (O(n) lookup vs. O(1) dict)

[View Full Report](../artifacts/TSP-FIB-001/design_review.md) | [View Design Spec](../artifacts/TSP-FIB-001/design.md)

---

### Approval Decision Required

This quality gate failure requires human approval to proceed. Review the issues above and decide:

**To APPROVE override and continue pipeline:**
```
/approve [your justification here]
```

Example:
```
/approve Low-risk Fibonacci demo for educational purposes. Error handling not critical for learning use case. Will add in production version.
```

**To REJECT and halt pipeline:**
```
/reject [reason for rejection]
```

Example:
```
/reject Security issues in input validation are unacceptable. Must fix before proceeding.
```

---

### Audit Information

- **Orchestrator Run ID:** `run_abc123xyz`
- **Pipeline Phase:** Design Review (Phase 2a)
- **Agent Version:** `design-review-agent:v1.2.3`
- **Timeout Policy:** Auto-reject after 24 hours
- **Approver Role Required:** `engineering-manager` or `tech-lead`

---

**Automated Issue** | Created by TSP Orchestrator | [Documentation](../docs/hitl_approval_workflow.md)
```

**Issue Metadata:**
- **Labels:** `approval-required`, `design-review`, `TSP-FIB-001`, `quality-gate-failure`
- **Assignee:** `@engineering-manager` (configurable per project)
- **Milestone:** `Approval Timeout 2025-11-23` (for visibility)
- **Project:** `ASP Pipeline Approvals` (if using GitHub Projects)

#### 3.1B.4 Implementation Details

**File Structure:**
```
src/asp/hitl/
├── __init__.py
├── approval_service.py           # Core HITL service (existing)
├── github_issue_service.py       # NEW: GitHub Issues backend
├── github_webhook_listener.py    # NEW: Webhook handler
├── approval_parsers.py           # NEW: Comment parsing logic
└── github_templates.py           # NEW: Issue body templates

config/
└── github_approvers.yml          # NEW: Approver permissions

.github/
└── workflows/
    └── hitl_webhook_listener.yml # NEW: GitHub Actions webhook handler
```

**Key Classes:**

```python
# src/asp/hitl/github_issue_service.py

import re
import time
from datetime import datetime, timedelta
from typing import Optional
from github import Github, GithubException
import logging

from asp.models.hitl import (
    ApprovalRequest,
    ApprovalDecision,
    ApprovalStatus,
    GateType,
    HITLApprovalResult,
)
from asp.hitl.github_templates import IssueTemplate

logger = logging.getLogger(__name__)

class GitHubIssueApprovalService:
    """
    GitHub Issues-based HITL approval workflow.

    Creates GitHub issues for quality gate failures and polls for
    approval decisions via issue comments.

    Requires:
    - GITHUB_TOKEN environment variable (with repo scope)
    - Repository in format "owner/repo"

    Example:
        >>> service = GitHubIssueApprovalService(
        ...     repo="evelynmitchell/Process_Software_Agents",
        ...     approvers=["@engineering-manager", "@tech-lead"]
        ... )
        >>> result = service.request_approval(
        ...     task_id="TSP-FIB-001",
        ...     gate_name=GateType.DESIGN_REVIEW,
        ...     report=design_review.model_dump()
        ... )
        >>> print(f"Issue created: {result.issue_url}")
    """

    APPROVAL_PATTERN = re.compile(r'^/approve\s+(.+)', re.IGNORECASE | re.DOTALL)
    REJECT_PATTERN = re.compile(r'^/reject\s+(.+)', re.IGNORECASE | re.DOTALL)

    def __init__(
        self,
        repo: str,
        github_token: Optional[str] = None,
        approvers: Optional[list[str]] = None,
        timeout_seconds: int = 86400,  # 24 hours
        poll_interval_seconds: int = 30,
    ):
        """
        Initialize GitHub Issues approval service.

        Args:
            repo: Repository in format "owner/repo"
            github_token: GitHub API token (defaults to GITHUB_TOKEN env var)
            approvers: List of GitHub usernames/teams that can approve
            timeout_seconds: How long to wait for approval
            poll_interval_seconds: How often to check for decision
        """
        self.repo_name = repo
        self.approvers = approvers or []
        self.timeout_seconds = timeout_seconds
        self.poll_interval = poll_interval_seconds

        # Initialize GitHub API client
        self.github = Github(github_token or os.getenv("GITHUB_TOKEN"))
        self.repo = self.github.get_repo(repo)

        logger.info(f"Initialized GitHub HITL service for {repo}")

    def request_approval(
        self,
        task_id: str,
        gate_name: GateType,
        report: dict,
    ) -> HITLApprovalResult:
        """
        Request approval by creating GitHub issue and waiting for decision.

        Workflow:
        1. Create GitHub issue with formatted report
        2. Add labels and assign to approvers
        3. Poll issue comments for /approve or /reject commands
        4. Parse decision and return result

        Args:
            task_id: Task identifier (e.g., "TSP-FIB-001")
            gate_name: Quality gate type
            report: Full review report dictionary

        Returns:
            HITLApprovalResult with decision

        Raises:
            TimeoutError: If no decision received within timeout
            GithubException: If GitHub API fails
        """
        # Create approval request
        request = ApprovalRequest(
            task_id=task_id,
            gate_name=gate_name,
            report=report,
            timeout_at=datetime.utcnow() + timedelta(seconds=self.timeout_seconds),
            timeout_seconds=self.timeout_seconds,
        )

        # Create GitHub issue
        issue = self._create_approval_issue(request)
        logger.info(
            f"Created approval issue #{issue.number}: {issue.html_url}"
        )

        # Poll for approval decision
        try:
            decision = self._wait_for_decision(issue, request)

            # Close issue with resolution
            self._close_issue_with_resolution(issue, decision)

            return HITLApprovalResult(
                approved=(decision.status == ApprovalStatus.APPROVED),
                decision=decision,
                request=request,
            )

        except TimeoutError:
            # Mark issue as timed out
            issue.add_to_labels("timeout")
            issue.create_comment(
                f"⏱️ **Approval Timeout**\n\n"
                f"No decision received within {self.timeout_seconds}s. "
                f"Pipeline halted per fail-safe policy."
            )
            issue.edit(state="closed")
            raise

    def _create_approval_issue(self, request: ApprovalRequest):
        """Create GitHub issue for approval request."""
        # Format issue body using template
        template = IssueTemplate()
        body = template.format_approval_request(request)

        # Create issue
        title = f"[APPROVAL REQUIRED] {request.task_id} {request.gate_name.value} Failed"

        issue = self.repo.create_issue(
            title=title,
            body=body,
            labels=[
                "approval-required",
                request.gate_name.value.lower().replace("_", "-"),
                request.task_id,
                "quality-gate-failure",
            ],
            assignees=[a.lstrip("@") for a in self.approvers],
        )

        return issue

    def _wait_for_decision(
        self,
        issue,
        request: ApprovalRequest,
    ) -> ApprovalDecision:
        """
        Poll issue comments for approval decision.

        Looks for comments matching:
        - /approve <justification>
        - /reject <reason>

        Returns when first matching comment found or timeout reached.
        """
        start_time = datetime.utcnow()
        timeout_at = request.timeout_at

        while datetime.utcnow() < timeout_at:
            # Refresh issue to get latest comments
            issue = self.repo.get_issue(issue.number)

            # Check all comments for decision
            for comment in issue.get_comments():
                decision = self._parse_comment_for_decision(
                    comment,
                    request.request_id,
                )
                if decision:
                    return decision

            # Sleep before next poll
            time.sleep(self.poll_interval)

            # Log progress
            elapsed = (datetime.utcnow() - start_time).total_seconds()
            if elapsed % 300 == 0:  # Log every 5 minutes
                logger.info(
                    f"Still waiting for approval on issue #{issue.number} "
                    f"({elapsed}s elapsed, timeout at {timeout_at})"
                )

        # Timeout reached
        raise TimeoutError(
            f"No approval decision received within {self.timeout_seconds}s"
        )

    def _parse_comment_for_decision(
        self,
        comment,
        request_id,
    ) -> Optional[ApprovalDecision]:
        """
        Parse issue comment for /approve or /reject command.

        Returns ApprovalDecision if found, None otherwise.
        """
        body = comment.body.strip()
        author = comment.user.login

        # Check for /approve command
        approve_match = self.APPROVAL_PATTERN.match(body)
        if approve_match:
            justification = approve_match.group(1).strip()
            logger.info(
                f"Approval detected from @{author}: {justification}"
            )
            return ApprovalDecision(
                request_id=request_id,
                status=ApprovalStatus.APPROVED,
                approver_id=author,
                justification=justification,
                decision_at=comment.created_at,
            )

        # Check for /reject command
        reject_match = self.REJECT_PATTERN.match(body)
        if reject_match:
            reason = reject_match.group(1).strip()
            logger.info(
                f"Rejection detected from @{author}: {reason}"
            )
            return ApprovalDecision(
                request_id=request_id,
                status=ApprovalStatus.REJECTED,
                approver_id=author,
                justification=reason,
                decision_at=comment.created_at,
            )

        return None

    def _close_issue_with_resolution(self, issue, decision: ApprovalDecision):
        """Close issue and add resolution comment."""
        if decision.status == ApprovalStatus.APPROVED:
            issue.add_to_labels("approved")
            emoji = "✅"
            status_text = "APPROVED"
            color = "green"
        else:
            issue.add_to_labels("rejected")
            emoji = "❌"
            status_text = "REJECTED"
            color = "red"

        resolution_comment = f"""
{emoji} **Quality Gate Override {status_text}**

**Decision:** {status_text}
**Approver:** @{decision.approver_id}
**Timestamp:** {decision.decision_at.isoformat()}
**Justification:** {decision.justification}

---

Pipeline will {"**continue** with approved override" if decision.status == ApprovalStatus.APPROVED else "**halt** per quality gate policy"}.

Approval decision logged to audit trail (Langfuse + git).
"""

        issue.create_comment(resolution_comment)
        issue.edit(state="closed")

        logger.info(
            f"Closed issue #{issue.number} with status: {status_text}"
        )


# src/asp/hitl/github_templates.py

from asp.models.hitl import ApprovalRequest, GateType

class IssueTemplate:
    """Templates for GitHub issue bodies."""

    def format_approval_request(self, request: ApprovalRequest) -> str:
        """Format approval request as GitHub issue markdown."""
        report = request.report

        # Extract issue counts (adapt to report schema)
        critical = report.get("critical_issue_count", report.get("critical_issues", 0))
        high = report.get("high_issue_count", report.get("high_issues", 0))
        medium = report.get("medium_issue_count", report.get("medium_issues", 0))
        low = report.get("low_issue_count", report.get("low_issues", 0))

        # Format issue summary table
        summary_table = f"""
| Severity | Count |
|----------|-------|
| Critical | {critical} |
| High     | {high} |
| Medium   | {medium} |
| Low      | {low} |
"""

        # Extract top issues (first 3-5)
        top_issues = self._format_top_issues(request.gate_name, report)

        # Construct full body
        body = f"""## Quality Gate Failure: {request.gate_name.value}

**Task ID:** {request.task_id}
**Gate:** {request.gate_name.value}
**Status:** ❌ FAIL
**Created:** {request.created_at.isoformat()}
**Timeout:** {request.timeout_at.isoformat()} (24 hours)

---

### Issue Summary

{summary_table}

### Top Issues

{top_issues}

[View Full Report](../artifacts/{request.task_id}/design_review.md) | [View Design Spec](../artifacts/{request.task_id}/design.md)

---

### Approval Decision Required

This quality gate failure requires human approval to proceed. Review the issues above and decide:

**To APPROVE override and continue pipeline:**
```
/approve [your justification here]
```

Example:
```
/approve Low-risk Fibonacci demo for educational purposes. Error handling not critical for learning use case. Will add in production version.
```

**To REJECT and halt pipeline:**
```
/reject [reason for rejection]
```

Example:
```
/reject Security issues in input validation are unacceptable. Must fix before proceeding.
```

---

### Audit Information

- **Request ID:** `{request.request_id}`
- **Pipeline Phase:** {request.gate_name.value} (Phase 2a/3a)
- **Timeout Policy:** Auto-reject after {request.timeout_seconds}s
- **Approver Role Required:** `engineering-manager` or `tech-lead`

---

**Automated Issue** | Created by TSP Orchestrator | [Documentation](../docs/hitl_approval_workflow.md)
"""
        return body

    def _format_top_issues(self, gate_name: GateType, report: dict) -> str:
        """Extract and format top 3-5 issues from report."""
        # This is gate-specific; adapt based on report schema
        if gate_name == GateType.DESIGN_REVIEW:
            suggestions = report.get("improvement_suggestions", [])[:3]
            formatted = []
            for suggestion in suggestions:
                severity = suggestion.get("severity", "MEDIUM")
                issue_type = suggestion.get("issue_type", "Unknown")
                description = suggestion.get("suggestion", "")
                location = suggestion.get("location", "")

                formatted.append(
                    f"#### [{severity}] {issue_type}\n"
                    f"{description}\n"
                    f"Location: `{location}`\n"
                )
            return "\n".join(formatted) if formatted else "*No specific issues listed*"

        elif gate_name == GateType.CODE_REVIEW:
            issues = report.get("issues", [])[:3]
            formatted = []
            for issue in issues:
                severity = issue.get("severity", "MEDIUM")
                category = issue.get("category", "Unknown")
                description = issue.get("description", "")
                file_path = issue.get("file_path", "")

                formatted.append(
                    f"#### [{severity}] {category}\n"
                    f"{description}\n"
                    f"File: `{file_path}`\n"
                )
            return "\n".join(formatted) if formatted else "*No specific issues listed*"

        return "*Issue details not available*"
```

#### 3.1B.5 Integration with TSP Orchestrator

**Modification to `tsp_orchestrator.py`:**

```python
# src/asp/orchestrators/tsp_orchestrator.py

from asp.hitl.approval_service import HITLApprovalService
from asp.hitl.github_issue_service import GitHubIssueApprovalService
from asp.models.hitl import GateType

class TSPOrchestrator:
    def __init__(
        self,
        ...,
        hitl_backend: str = "cli",  # "cli", "github", "api", "web"
        github_repo: Optional[str] = None,
    ):
        """
        Initialize TSP Orchestrator with HITL backend.

        Args:
            hitl_backend: HITL interface ("cli", "github", "api", "web")
            github_repo: GitHub repo for "github" backend (e.g., "owner/repo")
        """
        ...

        # Initialize HITL service based on backend
        if hitl_backend == "cli":
            self.hitl_service = HITLApprovalService(interface="cli")
        elif hitl_backend == "github":
            if not github_repo:
                raise ValueError("github_repo required for 'github' backend")
            self.hitl_service = GitHubIssueApprovalService(repo=github_repo)
        elif hitl_backend == "api":
            self.hitl_service = HITLApprovalService(interface="api")
        else:
            raise ValueError(f"Unknown HITL backend: {hitl_backend}")

# Example usage:
orchestrator = TSPOrchestrator(
    hitl_backend="github",
    github_repo="evelynmitchell/Process_Software_Agents",
)
```

#### 3.1B.6 GitHub Permissions & Security

**Required GitHub Token Scopes:**
- `repo` (full repository access)
- `write:discussion` (for issue comments)

**Approver Authorization:**
Two options for validating approvers:

**Option 1: Configuration File (Simple)**
```yaml
# config/github_approvers.yml
approvers:
  - alice
  - bob
  - engineering-managers  # GitHub team

approval_rules:
  design-review:
    min_approvals: 1
    required_roles: [engineering-manager, tech-lead]

  code-review:
    min_approvals: 1
    required_roles: [senior-engineer, tech-lead]

  pip-approval:
    min_approvals: 2
    required_roles: [engineering-manager]
```

**Option 2: GitHub CODEOWNERS (Advanced)**
```
# .github/CODEOWNERS
# Approval authority for quality gates

/artifacts/*/design_review.md       @engineering-managers
/artifacts/*/code_review.md         @senior-engineers @tech-leads
/docs/process_improvements/*.md     @engineering-managers
```

Then validate approver using GitHub API:
```python
def _is_authorized_approver(self, username: str, gate_name: GateType) -> bool:
    """Check if user is authorized to approve this gate."""
    # Check if user is in approvers list
    if username not in self.approvers:
        return False

    # Check if user has write access to repo
    try:
        permission = self.repo.get_collaborator_permission(username)
        return permission in ["admin", "write"]
    except GithubException:
        return False
```

#### 3.1B.7 Advantages vs. CLI/Database Approaches

| Feature | CLI (Phase 1A) | GitHub Issues (Phase 1B) | Database/API (Phase 2) |
|---------|---------------|--------------------------|------------------------|
| **Infrastructure** | None | GitHub only | DB + API server |
| **Notifications** | None (manual monitoring) | Email, mobile, Slack | Custom webhooks |
| **Audit Trail** | Langfuse only | GitHub + Langfuse + git | Database + Langfuse |
| **Team Collaboration** | Serial (one person) | Parallel (comments, @mentions) | Via API clients |
| **Searchability** | Langfuse queries | GitHub search + filters | SQL queries |
| **Access Control** | None | GitHub org permissions | Custom RBAC |
| **Offline Support** | Yes | No | No |
| **Async Approvals** | No (blocking) | Yes (polling/webhooks) | Yes |
| **Latency** | Instant | ~1-5s (webhooks) | ~100ms (API) |
| **Setup Time** | 0 | ~8-12 hours | ~20 hours |
| **Maintenance** | None | GitHub token management | DB + API maintenance |

**Recommendation:** Use GitHub Issues for team workflows and CI/CD, CLI for local development.

---

### 3.2 Phase 2: API-Based HITL

#### 3.2.1 REST API Endpoints

```python
# src/asp/api/hitl_router.py (Future FastAPI router)

from fastapi import APIRouter, HTTPException
from uuid import UUID

from asp.hitl.approval_service import HITLApprovalService
from asp.models.hitl import ApprovalDecision, ApprovalStatus

router = APIRouter(prefix="/api/v1/approvals", tags=["HITL"])

hitl_service = HITLApprovalService(interface="api")

@router.get("/pending")
async def get_pending_approvals():
    """Get all pending approval requests."""
    requests = hitl_service.get_pending_requests()
    return {"pending": [r.model_dump() for r in requests]}

@router.get("/{request_id}")
async def get_approval_request(request_id: UUID):
    """Get specific approval request details."""
    request = hitl_service.queue.get_by_id(request_id)
    if not request:
        raise HTTPException(status_code=404, detail="Request not found")
    return request.model_dump()

@router.post("/{request_id}/approve")
async def approve_request(request_id: UUID, decision: ApprovalDecision):
    """Approve quality gate override."""
    hitl_service.queue.record_decision(request_id, decision)
    return {"status": "approved", "request_id": request_id}

@router.post("/{request_id}/reject")
async def reject_request(request_id: UUID, decision: ApprovalDecision):
    """Reject quality gate override."""
    hitl_service.queue.record_decision(request_id, decision)
    return {"status": "rejected", "request_id": request_id}

@router.get("/history/{task_id}")
async def get_task_history(task_id: str):
    """Get approval history for a specific task."""
    history = hitl_service.get_request_history(task_id=task_id)
    return {"history": [r.model_dump() for r in history]}
```

#### 3.2.2 Webhook Notifications

```python
# src/asp/hitl/notifiers.py

import requests
from typing import Optional
import logging

from asp.models.hitl import ApprovalRequest

logger = logging.getLogger(__name__)

class WebhookNotifier:
    """Send webhook notifications when approval requests are created."""

    def __init__(self, webhook_url: Optional[str] = None):
        self.webhook_url = webhook_url or os.getenv("HITL_WEBHOOK_URL")

    def notify(self, request: ApprovalRequest):
        """Send webhook notification."""
        if not self.webhook_url:
            return

        payload = {
            "event": "approval_request_created",
            "request_id": str(request.request_id),
            "task_id": request.task_id,
            "gate_name": request.gate_name.value,
            "created_at": request.created_at.isoformat(),
            "timeout_at": request.timeout_at.isoformat(),
            "view_url": f"http://localhost:8000/approvals/{request.request_id}",
        }

        try:
            response = requests.post(self.webhook_url, json=payload, timeout=5)
            response.raise_for_status()
            logger.info(f"Webhook notification sent for {request.request_id}")
        except Exception as e:
            logger.error(f"Failed to send webhook: {e}")

# Slack integration example
class SlackNotifier(WebhookNotifier):
    """Send Slack notifications for approval requests."""

    def notify(self, request: ApprovalRequest):
        """Send Slack message."""
        if not self.webhook_url:
            return

        report = request.report
        issues_summary = (
            f"C:{report.get('critical_issue_count', 0)} "
            f"H:{report.get('high_issue_count', 0)} "
            f"M:{report.get('medium_issue_count', 0)} "
            f"L:{report.get('low_issue_count', 0)}"
        )

        slack_message = {
            "text": f"🚨 Quality Gate Failure: {request.gate_name.value}",
            "blocks": [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": f"🚨 Quality Gate Failure: {request.gate_name.value}",
                    },
                },
                {
                    "type": "section",
                    "fields": [
                        {"type": "mrkdwn", "text": f"*Task:*\n{request.task_id}"},
                        {"type": "mrkdwn", "text": f"*Gate:*\n{request.gate_name.value}"},
                        {"type": "mrkdwn", "text": f"*Issues:*\n{issues_summary}"},
                        {
                            "type": "mrkdwn",
                            "text": f"*Timeout:*\n{request.timeout_at.strftime('%Y-%m-%d %H:%M')}",
                        },
                    ],
                },
                {
                    "type": "actions",
                    "elements": [
                        {
                            "type": "button",
                            "text": {"type": "plain_text", "text": "View Details"},
                            "url": f"http://localhost:8000/approvals/{request.request_id}",
                            "style": "primary",
                        },
                    ],
                },
            ],
        }

        try:
            response = requests.post(self.webhook_url, json=slack_message, timeout=5)
            response.raise_for_status()
            logger.info(f"Slack notification sent for {request.request_id}")
        except Exception as e:
            logger.error(f"Failed to send Slack notification: {e}")
```

---

### 3.3 Phase 3: Web Dashboard

#### 3.3.1 UI Components (Conceptual)

```
┌──────────────────────────────────────────────────────────────┐
│  ASP HITL Approval Dashboard                        [User ▼] │
├──────────────────────────────────────────────────────────────┤
│                                                               │
│  Pending Approvals (3)                                        │
│  ┌────────────────────────────────────────────────────────┐  │
│  │ TSP-FIB-001 | Design Review | 15 min ago             │  │
│  │ Issues: 0C / 4H / 7M / 4L                             │  │
│  │ [View Report] [Approve] [Reject]                      │  │
│  ├────────────────────────────────────────────────────────┤  │
│  │ TSP-WEB-042 | Code Review | 2 hours ago              │  │
│  │ Issues: 1C / 2H / 0M / 1L                             │  │
│  │ [View Report] [Approve] [Reject]                      │  │
│  ├────────────────────────────────────────────────────────┤  │
│  │ TSP-API-103 | PIP Approval | 1 day ago                │  │
│  │ Timeout in: 22 hours                                   │  │
│  │ [View Report] [Approve] [Reject]                      │  │
│  └────────────────────────────────────────────────────────┘  │
│                                                               │
│  Recent History (10)                              [View All]  │
│  ┌────────────────────────────────────────────────────────┐  │
│  │ ✓ TSP-AUTH-087 | Approved by alice@co | 3 hours ago   │  │
│  │ ✗ TSP-DB-054 | Rejected by bob@co | 5 hours ago       │  │
│  │ ⏱ TSP-ML-012 | Timeout | 1 day ago                     │  │
│  └────────────────────────────────────────────────────────┘  │
│                                                               │
│  Analytics                                                    │
│  Approval Rate: 78% | Avg Response Time: 4.2 hours           │
└──────────────────────────────────────────────────────────────┘
```

**Technology Stack (Future):**
- Frontend: React + TypeScript + TailwindCSS
- Backend: FastAPI (existing)
- Real-time: WebSocket for live updates
- Charts: Recharts or Chart.js for analytics

---

## 4. Data Model

### 4.1 Database Schema

```sql
-- SQLite schema for approval request queue

CREATE TABLE approval_requests (
    request_id TEXT PRIMARY KEY,
    task_id TEXT NOT NULL,
    gate_name TEXT NOT NULL,  -- DesignReview, CodeReview, PIPApproval
    report JSON NOT NULL,     -- Full review report
    status TEXT NOT NULL,     -- PENDING, APPROVED, REJECTED, TIMEOUT
    created_at TIMESTAMP NOT NULL,
    timeout_at TIMESTAMP,
    decision_at TIMESTAMP,
    approver_id TEXT,
    justification TEXT,

    INDEX idx_task_id (task_id),
    INDEX idx_status (status),
    INDEX idx_created_at (created_at)
);

-- Audit trail for all decisions
CREATE TABLE approval_audit_log (
    log_id INTEGER PRIMARY KEY AUTOINCREMENT,
    request_id TEXT NOT NULL,
    event_type TEXT NOT NULL,  -- CREATED, APPROVED, REJECTED, TIMEOUT
    timestamp TIMESTAMP NOT NULL,
    actor_id TEXT,
    metadata JSON,

    FOREIGN KEY (request_id) REFERENCES approval_requests(request_id),
    INDEX idx_request_id (request_id),
    INDEX idx_timestamp (timestamp)
);
```

### 4.2 Langfuse Integration (Audit Trail)

```python
# src/asp/hitl/audit_logger.py

from langfuse import Langfuse
from asp.models.hitl import HITLApprovalResult, ApprovalDecision
import logging

logger = logging.getLogger(__name__)

class AuditLogger:
    """Log HITL decisions to Langfuse for audit trail."""

    def __init__(self):
        self.langfuse = Langfuse()

    def log_decision(self, result: HITLApprovalResult):
        """Log approval decision to Langfuse."""
        try:
            self.langfuse.score(
                name="hitl_approval_decision",
                value=1.0 if result.approved else 0.0,
                data_type="NUMERIC",
                comment=result.decision.justification,
                trace_id=result.request.task_id,
                observation_id=str(result.request.request_id),
                metadata={
                    "gate_name": result.request.gate_name.value,
                    "approver_id": result.decision.approver_id,
                    "decision_at": result.decision.decision_at.isoformat(),
                    "report_summary": self._extract_summary(result.request.report),
                },
            )
            logger.info(f"Logged HITL decision to Langfuse: {result.request.request_id}")
        except Exception as e:
            logger.error(f"Failed to log to Langfuse: {e}")

    def _extract_summary(self, report: dict) -> dict:
        """Extract key metrics from report for metadata."""
        return {
            "critical": report.get("critical_issue_count", report.get("critical_issues", 0)),
            "high": report.get("high_issue_count", report.get("high_issues", 0)),
            "medium": report.get("medium_issue_count", report.get("medium_issues", 0)),
            "low": report.get("low_issue_count", report.get("low_issues", 0)),
        }
```

---

## 5. Non-Functional Requirements

### 5.1 Performance
- **Response Time:** CLI prompt displays in <500ms
- **Approval Latency:** Human decision recorded in <100ms after submission
- **Queue Throughput:** Support 100+ concurrent approval requests
- **Database:** SQLite for MVP, PostgreSQL for production (>1K requests/day)

### 5.2 Reliability
- **Fail-Safe:** Quality gates default to BLOCKING if HITL service unavailable
- **Idempotency:** Duplicate approval submissions have no effect
- **Crash Recovery:** Pending requests survive process restarts
- **Timeout Behavior:** Configurable (default: TIMEOUT status, pipeline halted)

### 5.3 Security
- **Authentication:** Approver identity required (username/email)
- **Authorization:** Future: Role-based access control (RBAC)
- **Audit Trail:** All decisions logged to Langfuse with immutable timestamps
- **Data Privacy:** Review reports may contain sensitive code; restrict access

### 5.4 Usability
- **3-Click Approval:** Per NFR-17, approval workflow completes in ≤3 clicks/commands
- **Clear Reporting:** Issue summaries highlight critical information first
- **Progressive Disclosure:** Summary → Full Report → Individual Issues
- **Responsive Design:** Web UI works on desktop and mobile

### 5.5 Observability
- **Metrics:**
  - Approval request volume (per gate type)
  - Approval rate (approved / total)
  - Average response time (created → decided)
  - Timeout rate
- **Dashboards:** Grafana integration for real-time monitoring
- **Alerts:** Slack/PagerDuty for timeouts or high rejection rates

---

## 6. Implementation Plan

### 6.1 Phase 1A: CLI-Based HITL (Week 1-2)

**Purpose:** Local development workflow with interactive terminal prompts

**Deliverables:**
- [ ] `src/asp/models/hitl.py` - Pydantic models
- [ ] `src/asp/hitl/request_queue.py` - SQLite-based queue
- [ ] `src/asp/hitl/report_formatters.py` - Markdown formatter
- [ ] `src/asp/hitl/cli_interface.py` - Interactive CLI
- [ ] `src/asp/hitl/approval_service.py` - Core service
- [ ] `src/asp/hitl/audit_logger.py` - Langfuse integration
- [ ] Integration with `TSPOrchestrator` (backwards-compatible)
- [ ] Unit tests (85% coverage)
- [ ] E2E test with real CLI interaction (mocked input)
- [ ] Documentation updates (README, PRD)

**Success Criteria:**
- ✅ TSP Orchestrator pauses on quality gate failure
- ✅ CLI displays formatted review report
- ✅ Human can approve/reject with justification
- ✅ Decision logged to Langfuse
- ✅ Pipeline resumes or halts based on decision
- ✅ Backwards compatible with legacy `hitl_approver` callback

**Estimated Effort:** 16-20 hours

### 6.1B Phase 1B: GitHub Issues-Based HITL (Week 2-3) ⭐ RECOMMENDED

**Purpose:** Team/CI workflow with GitHub-native approvals (zero infrastructure)

**Deliverables:**
- [ ] `src/asp/hitl/github_issue_service.py` - GitHub Issues backend
- [ ] `src/asp/hitl/github_templates.py` - Issue body templates
- [ ] `src/asp/hitl/approval_parsers.py` - Comment parsing logic (regex)
- [ ] `config/github_approvers.yml` - Approver configuration
- [ ] Integration with `TSPOrchestrator` (multi-backend support)
- [ ] Unit tests for GitHub API interaction (85% coverage)
- [ ] E2E test with GitHub API mocking
- [ ] Documentation: GitHub approval workflow guide
- [ ] Example: GitHub Actions workflow for webhook listener (optional)

**Success Criteria:**
- ✅ TSP Orchestrator creates GitHub issue on quality gate failure
- ✅ Issue contains formatted report with top issues
- ✅ Human can approve via `/approve <justification>` comment
- ✅ Human can reject via `/reject <reason>` comment
- ✅ Orchestrator polls issue and detects decision
- ✅ Issue closed with resolution comment
- ✅ Decision logged to Langfuse + recorded in issue history
- ✅ Works with existing GitHub org permissions

**Estimated Effort:** 8-12 hours

**Why Faster Than Phase 1A:**
- No database schema design (uses GitHub API)
- No UI framework (uses GitHub web interface)
- Simpler integration (just GitHub API client)
- Leverages existing project infrastructure (GitHub repo)

**Dependencies:**
- GitHub token with `repo` scope
- PyGithub library (`pip install PyGithub`)
- GitHub repository configured

### 6.2 Phase 2: API + Webhooks (Week 4-5)

**Deliverables:**
- [ ] FastAPI router (`src/asp/api/hitl_router.py`)
- [ ] Webhook notifier (Slack, generic HTTP)
- [ ] API polling mechanism in `ApprovalRequestQueue`
- [ ] API documentation (OpenAPI/Swagger)
- [ ] Integration tests for API endpoints
- [ ] Example: Slack bot for approvals

**Success Criteria:**
- ✅ Approval requests accessible via REST API
- ✅ Slack notification sent when request created
- ✅ External systems can approve/reject via API
- ✅ TSP Orchestrator waits for API decision

**Estimated Effort:** 12-16 hours

### 6.3 Phase 3: Web Dashboard (Week 5-8)

**Deliverables:**
- [ ] React frontend with approval UI
- [ ] WebSocket for real-time updates
- [ ] Historical analytics page
- [ ] Batch approval capability
- [ ] Mobile-responsive design
- [ ] E2E tests (Playwright/Cypress)

**Success Criteria:**
- ✅ Web UI displays pending approvals
- ✅ One-click approve/reject
- ✅ Real-time updates when new requests arrive
- ✅ Analytics dashboard (approval rate, response time)

**Estimated Effort:** 40-60 hours (larger effort due to frontend)

---

## 7. Risks & Mitigation

### 7.1 Risk: Blocking UX in CLI Mode
**Description:** Interactive CLI prompts block pipeline execution; poor UX for long-running tasks

**Mitigation:**
- Phase 1: Acceptable for MVP (human actively monitoring)
- Phase 2: API mode enables async workflows
- Future: Background service mode (TSP runs headless, notifications via Slack/email)

### 7.2 Risk: Timeout Handling Ambiguity
**Description:** Unclear what happens if human doesn't respond within 24 hours

**Mitigation:**
- Default behavior: Status set to TIMEOUT, pipeline halted with clear error
- Configurable policy:
  - `timeout_action="halt"` (default, fail-safe)
  - `timeout_action="auto_approve"` (risky, requires explicit opt-in)
  - `timeout_action="escalate"` (notify manager, extend timeout)

### 7.3 Risk: Database Bottleneck
**Description:** SQLite may not scale to 1000s of approval requests

**Mitigation:**
- Phase 1: SQLite sufficient (<100 requests/day)
- Phase 2: Add PostgreSQL support (connection pooling)
- Future: Redis for in-memory queue, PostgreSQL for audit log

### 7.4 Risk: Security (Unauthorized Approvals)
**Description:** No authentication in Phase 1; anyone can approve

**Mitigation:**
- Phase 1: Trust-based (approver_id collected but not verified)
- Phase 2: API key authentication
- Phase 3: OAuth2 + RBAC (GitHub SSO)

### 7.5 Risk: Poor Report Formatting
**Description:** Review reports may be too verbose or unclear for humans

**Mitigation:**
- Progressive disclosure: Summary → Full Report → Details
- User testing with real review reports
- Iteration on formatting based on feedback

---

## 8. Open Questions

1. **Timeout Policy:** Should timeout auto-reject or allow configurable behavior?
   - **Recommendation:** Default to halt (fail-safe), allow override via config

2. **Multi-Approver Workflow:** Should some gates require 2+ approvals?
   - **Recommendation:** Not for MVP; add in Phase 3 if needed

3. **Approval Delegation:** Can approver delegate to someone else?
   - **Recommendation:** Not for MVP; add comment/reassignment in Phase 2

4. **Audit Retention:** How long to keep approval history?
   - **Recommendation:** 90 days in database, archive to S3 for compliance

5. **Rollback:** If approval was mistake, can it be revoked?
   - **Recommendation:** No revocation (immutable audit trail), but can halt downstream phases manually

---

## 9. Success Metrics (Post-Launch)

### 9.1 Operational Metrics (Week 1-4)
- **Adoption Rate:** % of TSP executions using HITL (target: 100% for quality gate failures)
- **Approval Rate:** % approved vs. rejected (baseline: unknown, track trend)
- **Response Time:** P50, P95, P99 time from request → decision (target: <4 hours P95)
- **Timeout Rate:** % of requests timing out (target: <5%)

### 9.2 Quality Metrics (Month 1-3)
- **Defect Escape Rate:** % of approved overrides that later fail in Test phase (target: <10%)
- **False Positive Rate:** % of quality gate failures that are approved (indicates overly strict gates)
- **Audit Compliance:** 100% of approvals logged to Langfuse with justification

### 9.3 User Satisfaction (Month 3+)
- **UX Survey:** "How easy was it to review and approve?" (target: >4/5 average)
- **Friction Points:** User interviews to identify pain points
- **Feature Requests:** Track requests for batch approval, mobile app, etc.

---

## 10. Alternatives Considered

### 10.1 Alternative 1: Email-Based Approval
**Description:** Send email with approval link when quality gate fails

**Pros:**
- Familiar workflow for many teams
- No custom UI needed
- Works on mobile

**Cons:**
- Latency: Email delivery delays
- Security: Email links can be spoofed
- Poor UX for report review (HTML email limitations)

**Decision:** Rejected for MVP; consider as notification channel in Phase 2

### 10.2 Alternative 2: GitHub Issues-Based Approval ✅ ACCEPTED

**Description:** Create GitHub issue when approval needed; human responds via `/approve` or `/reject` comment commands

**Pros:**
- ✅ **Zero Infrastructure:** Uses existing GitHub (no DB, no API server)
- ✅ **Perfect Fit:** Project already git-centric with all artifacts in repo
- ✅ **Built-in Audit Trail:** Immutable GitHub issue history
- ✅ **Native Notifications:** Email, mobile, Slack (GitHub native)
- ✅ **Team Collaboration:** Discussion threads, @mentions, assignees
- ✅ **Access Control:** Leverages GitHub org permissions
- ✅ **Better Than Database:** Searchable, distributed, no maintenance

**Cons:**
- ❌ Tightly coupled to GitHub (acceptable: project already on GitHub)
- ❌ Parsing comment format (mitigated: simple regex, well-tested)
- ❌ API rate limits (5000 req/hour, sufficient for <100 approvals/day)
- ❌ Latency: Webhook delays ~1-5s (acceptable for human workflow)
- ❌ Requires GitHub connectivity (not suitable for offline use)

**Decision:** ✅ **ACCEPTED as Phase 1B** - Implemented alongside CLI (Phase 1A)

**Rationale:**
Upon deeper analysis, GitHub Issues is actually **superior to a custom database** for this project because:

1. **Consistency:** All artifacts already stored in git; approvals belong there too
2. **Audit Compliance:** GitHub issue history is immutable and traceable
3. **Zero Maintenance:** No database to deploy, backup, or scale
4. **Team-Friendly:** Engineers already monitor GitHub notifications
5. **CI/CD Ready:** GitHub Actions can trigger on issue comments
6. **Cost:** Free (vs. database hosting, API server)

The initial rejection was based on "too complex for MVP," but GitHub Issues is actually **simpler** than building a custom database + API. The perceived fragility of comment parsing is easily mitigated with robust regex and validation.

**Implementation:** See Section 3.1B for full design and code examples.

### 10.3 Alternative 3: LLM-Based Auto-Approval
**Description:** Use LLM to analyze review report and decide if override is safe

**Pros:**
- Fully autonomous (no human needed)
- Low latency

**Cons:**
- Risky: LLM may misjudge severity
- Defeats purpose of HITL (human oversight)
- PRD explicitly requires human approval (NFR-8: fail-safe)

**Decision:** Rejected; contradicts HITL principle

---

## 11. Appendix

### 11.1 Example: Design Review Failure Report (CLI)

```
═══════════════════════════════════════════════════════
QUALITY GATE FAILURE: Design Review
═══════════════════════════════════════════════════════

Task ID: TSP-FIB-001
Gate: Design Review
Status: FAIL
Timeout: 2025-11-23 14:30:00 UTC

Issue Summary:
• Critical: 0
• High: 4
• Medium: 7
• Low: 4

Top Issues:
[H] Missing error handling in 3 components
    - FibonacciCalculator: No validation for negative inputs
    - APIEndpoint: No rate limiting or auth checks
    - DatabaseClient: No connection timeout handling

[H] No input validation in 2 APIs
    - POST /calculate: Missing type validation for 'n' parameter
    - GET /history: No pagination limits (DoS risk)

[M] Suboptimal data structure choice
    - Using list for result cache (O(n) lookup vs. O(1) dict)

[M] Missing comprehensive documentation
    - 4 components lack docstrings for public methods

Commands:
  [v]iew   - View full report
  [a]pprove - Approve override and continue
  [r]eject  - Reject and halt pipeline
  [i]ssues  - List all issues in detail

Decision [v/a/r/i]: a

Justification: This is a demo/educational Fibonacci implementation.
Error handling not critical for learning purposes. Will add in production version.

Your name/email: alice@example.com

✓ Approval recorded. Pipeline will continue.
```

### 11.2 Glossary

- **HITL:** Human-in-the-Loop - requiring human approval for automated decisions
- **Quality Gate:** Checkpoint in pipeline where quality criteria must be met
- **Override:** Human approval to proceed despite quality gate failure
- **PIP:** Process Improvement Proposal - agent-generated suggestion to improve process
- **Fail-Safe:** System defaults to safe state (blocking) on error
- **Audit Trail:** Immutable log of all decisions for compliance

---

**End of Document**

**Next Steps:**
1. Review and approve this architecture document
2. Create engineering ticket for Phase 1 implementation
3. Set up project tracking (GitHub project board)
4. Begin implementation with `src/asp/models/hitl.py`

**Document Status:** DRAFT - Awaiting Review
**Reviewers:** Engineering Manager, Lead Developer, Product Owner
**Approval Date:** TBD
