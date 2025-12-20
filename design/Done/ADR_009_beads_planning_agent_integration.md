# ADR 009: Beads and Planning Agent Integration

**Status:** Implemented
**Date:** 2025-12-15
**Implemented:** 2025-12-16
**Session:** 20251215.3
**Deciders:** User, Claude

## Context and Problem Statement

The ASP system has a planning agent that decomposes tasks into semantic units, but there's no lightweight, git-native way to track these tasks through execution. Meanwhile, Beads provides a simple issue tracking system stored in `.beads/issues.jsonl`.

**Current State:**
- Beads: Standalone issue tracker with Kanban UI
- PlanningAgent: Generates plans with semantic units
- No connection between them

**Pain Points:**
1. Plans are generated but not tracked through execution
2. No visibility into which semantic units are complete
3. Manual task tracking required
4. No bidirectional flow (can't start from an issue)

## Decision Drivers

1. **Simplicity** - Beads is intentionally lightweight; integration should maintain this
2. **Bidirectionality** - Support both "Issue → ASP" and "ASP → Issues" flows
3. **Traceability** - Link issues to plans to execution results
4. **Incremental Adoption** - Each integration point should be independently useful
5. **Git-Native** - Everything stays in the repository

## Proposed Architecture

### Integration Points

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        Beads ↔ ASP Integration                          │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌──────────────┐     1. Manual      ┌──────────────────┐              │
│  │              │ ─────────────────► │                  │              │
│  │  Beads Issue │    CLI Trigger     │  Planning Agent  │              │
│  │              │                    │                  │              │
│  └──────────────┘                    └────────┬─────────┘              │
│         ▲                                     │                         │
│         │                                     │ 3. Auto-Sync            │
│         │ 2. Kanban Action                    ▼                         │
│         │                            ┌──────────────────┐              │
│  ┌──────┴───────┐                    │   Beads Issues   │              │
│  │   Kanban UI  │ ◄───────────────── │   (from plan)    │              │
│  └──────────────┘                    └──────────────────┘              │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### Integration 1: Manual CLI Trigger (Priority 1)

Process a Beads issue through ASP via CLI command.

**New File:** `src/asp/cli/beads_commands.py`

```python
"""CLI commands for Beads integration."""

import click
from asp.utils.beads import read_issues, BeadsStatus
from asp.agents.planning_agent import PlanningAgent
from asp.models.planning import TaskRequirements


@click.group()
def beads():
    """Beads issue tracking integration."""
    pass


@beads.command()
@click.argument("issue_id")
@click.option("--dry-run", is_flag=True, help="Show plan without executing")
def process(issue_id: str, dry_run: bool):
    """
    Process a Beads issue through ASP planning.

    Example:
        asp beads process bd-abc12
        asp beads process bd-abc12 --dry-run
    """
    # Find the issue
    issues = read_issues()
    issue = next((i for i in issues if i.id == issue_id), None)

    if not issue:
        click.echo(f"Error: Issue '{issue_id}' not found", err=True)
        raise SystemExit(1)

    if issue.status == BeadsStatus.CLOSED:
        click.echo(f"Warning: Issue '{issue_id}' is already closed", err=True)

    click.echo(f"Processing issue: {issue.title}")
    click.echo(f"Description: {issue.description or '(none)'}")

    # Convert to TaskRequirements
    requirements = TaskRequirements(
        task_id=issue.id,
        description=issue.title,
        requirements=issue.description or issue.title,
        context_files=[],
    )

    # Create plan
    agent = PlanningAgent()

    if dry_run:
        click.echo("\n[Dry Run] Would create plan for:")
        click.echo(f"  Task ID: {requirements.task_id}")
        click.echo(f"  Description: {requirements.description}")
        return

    click.echo("\nGenerating plan...")
    plan = agent.create_plan(requirements)

    click.echo(f"\nPlan created with {len(plan.semantic_units)} semantic units:")
    for i, unit in enumerate(plan.semantic_units, 1):
        click.echo(f"  {i}. {unit.description}")

    return plan


@beads.command()
def list():
    """List all open Beads issues."""
    issues = read_issues()
    open_issues = [i for i in issues if i.status != BeadsStatus.CLOSED]

    if not open_issues:
        click.echo("No open issues found.")
        return

    click.echo(f"Open issues ({len(open_issues)}):\n")
    for issue in open_issues:
        priority_marker = "!" * (5 - issue.priority) if issue.priority < 3 else ""
        click.echo(f"  [{issue.id}] {priority_marker} {issue.title}")
        if issue.description:
            click.echo(f"           {issue.description[:60]}...")
        click.echo()
```

**Modified:** `src/asp/cli/__init__.py`

```python
from .beads_commands import beads

# Add to main CLI group
cli.add_command(beads)
```

**Usage:**

```bash
# List open issues
asp beads list

# Process an issue (dry run first)
asp beads process bd-abc12 --dry-run

# Process an issue for real
asp beads process bd-abc12
```

### Integration 2: Kanban UI Action (Priority 2)

Add "Send to ASP" button on Kanban cards.

**Modified:** `src/asp/web/kanban.py`

```python
def IssueCard(issue):
    """Renders a single issue card with ASP action."""
    # ... existing code ...

    return Div(
        # ... existing card content ...

        # Add ASP action button
        Div(
            Button(
                "Plan with ASP",
                hx_post=f"/kanban/process/{issue.id}",
                hx_swap="outerHTML",
                hx_target=f"#card-{issue.id}",
                cls="text-xs bg-blue-500 text-white px-2 py-1 rounded hover:bg-blue-600",
            ),
            cls="mt-2 pt-2 border-t border-gray-200"
        ),

        id=f"card-{issue.id}",
        cls="bg-white p-3 rounded shadow border-l-4 mb-3",
        style=f"border-left-color: {border_color};"
    )


def kanban_routes(app):
    @app.get("/kanban")
    def get_kanban():
        return Title("Beads Kanban"), KanbanBoard()

    @app.post("/kanban/process/{issue_id}")
    async def process_issue(issue_id: str):
        """Process issue through ASP and return updated card."""
        from asp.agents.planning_agent import PlanningAgent
        from asp.models.planning import TaskRequirements

        issues = read_issues()
        issue = next((i for i in issues if i.id == issue_id), None)

        if not issue:
            return Div("Issue not found", cls="text-red-500")

        # Create plan
        requirements = TaskRequirements(
            task_id=issue.id,
            description=issue.title,
            requirements=issue.description or issue.title,
        )

        agent = PlanningAgent()
        plan = agent.create_plan(requirements)

        # Update issue status
        issue.status = BeadsStatus.IN_PROGRESS
        write_issues(issues)

        # Return success message with plan summary
        return Div(
            Div(f"Plan created: {len(plan.semantic_units)} units", cls="text-green-600 font-semibold"),
            Ul(*[Li(u.description, cls="text-sm") for u in plan.semantic_units[:3]]),
            Small(f"... and {len(plan.semantic_units) - 3} more" if len(plan.semantic_units) > 3 else ""),
            cls="bg-green-50 p-3 rounded"
        )
```

### Integration 3: Auto-Sync Plans to Beads (Priority 3)

Automatically create Beads issues from generated plans.

**New File:** `src/asp/utils/beads_sync.py`

```python
"""Sync ASP plans to Beads issues."""

import logging
from asp.utils.beads import (
    create_issue,
    read_issues,
    write_issues,
    BeadsType,
    BeadsStatus,
    BeadsIssue,
)
from asp.models.planning import Plan, SemanticUnit

logger = logging.getLogger(__name__)


def sync_plan_to_beads(
    plan: Plan,
    create_epic: bool = True,
    update_existing: bool = False,
) -> list[BeadsIssue]:
    """
    Create Beads issues from an ASP plan.

    Args:
        plan: The plan to sync
        create_epic: If True, create an epic for the main task
        update_existing: If True, update existing issues with same task_id

    Returns:
        List of created/updated BeadsIssues
    """
    created_issues = []
    existing_issues = read_issues()

    # Check if epic already exists
    epic_id = f"epic-{plan.task_id}"
    existing_epic = next((i for i in existing_issues if i.id == epic_id), None)

    if existing_epic and not update_existing:
        logger.warning("Epic %s already exists, skipping sync", epic_id)
        return []

    # Create or update epic
    if create_epic:
        if existing_epic:
            existing_epic.description = plan.summary
            existing_epic.updated_at = _now()
        else:
            epic = BeadsIssue(
                id=epic_id,
                title=f"[Epic] {plan.task_id}",
                description=plan.summary,
                type=BeadsType.EPIC,
                status=BeadsStatus.OPEN,
                priority=1,
                created_at=_now(),
                updated_at=_now(),
            )
            existing_issues.append(epic)
            created_issues.append(epic)

    # Create tasks for each semantic unit
    for i, unit in enumerate(plan.semantic_units, 1):
        task_id = f"{plan.task_id}-{i:02d}"
        existing_task = next((t for t in existing_issues if t.id == task_id), None)

        if existing_task and not update_existing:
            continue

        if existing_task:
            existing_task.title = unit.description
            existing_task.description = unit.rationale
            existing_task.updated_at = _now()
        else:
            task = BeadsIssue(
                id=task_id,
                title=unit.description,
                description=unit.rationale,
                type=BeadsType.TASK,
                status=BeadsStatus.OPEN,
                priority=_complexity_to_priority(unit.estimated_complexity),
                parent_id=epic_id if create_epic else None,
                labels=[unit.category] if hasattr(unit, 'category') else [],
                created_at=_now(),
                updated_at=_now(),
            )
            existing_issues.append(task)
            created_issues.append(task)

    # Write all issues
    write_issues(existing_issues)

    logger.info(
        "Synced plan %s to Beads: %d issues created",
        plan.task_id,
        len(created_issues),
    )

    return created_issues


def _now() -> str:
    """Return current time in ISO format."""
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _complexity_to_priority(complexity: float) -> int:
    """Convert complexity score to priority (0=highest, 4=lowest)."""
    if complexity >= 8:
        return 0  # Highest - very complex
    elif complexity >= 5:
        return 1
    elif complexity >= 3:
        return 2  # Medium
    elif complexity >= 1:
        return 3
    else:
        return 4  # Lowest - trivial
```

**Modified:** `src/asp/agents/planning_agent.py`

```python
class PlanningAgent(BaseAgent):
    def __init__(self, ..., sync_to_beads: bool = False):
        super().__init__(...)
        self.sync_to_beads = sync_to_beads

    def create_plan(self, requirements: TaskRequirements) -> Plan:
        """Create a plan, optionally syncing to Beads."""
        plan = self._generate_plan(requirements)

        if self.sync_to_beads:
            from asp.utils.beads_sync import sync_plan_to_beads
            sync_plan_to_beads(plan)

        return plan
```

---

## Data Flow

### Flow 1: Issue → Plan (Manual Trigger)

```
User runs: asp beads process bd-abc12

┌─────────────────┐     ┌──────────────────┐     ┌──────────────────┐
│  .beads/        │────►│  TaskRequirements │────►│  PlanningAgent   │
│  issues.jsonl   │     │                  │     │                  │
└─────────────────┘     └──────────────────┘     └────────┬─────────┘
                                                          │
                                                          ▼
                                                 ┌──────────────────┐
                                                 │      Plan        │
                                                 │  (semantic units)│
                                                 └──────────────────┘
```

### Flow 2: Plan → Issues (Auto-Sync)

```
PlanningAgent generates plan with sync_to_beads=True

┌──────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│  PlanningAgent   │────►│  beads_sync.py   │────►│  .beads/        │
│  (plan output)   │     │                  │     │  issues.jsonl   │
└──────────────────┘     └──────────────────┘     └─────────────────┘
                                                          │
                                                          ▼
                                                 ┌──────────────────┐
                                                 │   Kanban UI      │
                                                 │   (shows tasks)  │
                                                 └──────────────────┘
```

### Flow 3: Full Cycle (Issue → Plan → Sub-Issues → Execution)

```
1. User creates issue in Beads
2. User runs: asp beads process bd-abc12 --sync
3. PlanningAgent generates plan
4. Plan synced back to Beads as sub-tasks
5. Sub-tasks visible in Kanban
6. User (or automation) marks tasks complete as work progresses
```

---

## ID Conventions

All IDs use hash-based generation for consistency with Beads and to avoid coordination/collision issues.

| Entity | ID Pattern | Example |
|--------|------------|---------|
| User-created issue | `bd-{hash}` | `bd-a1b2c` |
| Epic from plan | `bd-{hash}` | `bd-e7f3a` |
| Task from semantic unit | `bd-{hash}` | `bd-9c2d1` |

### Why Hash-Based (Not Sequential)

**Problems with sequential/task_id based IDs:**
- Requires external coordination to avoid collisions
- Couples IDs to user-provided naming
- Hybrid schemes (hash + sequence) are brittle
- Cross-repo/cross-system conflicts possible

**Benefits of pure hash-based:**
- Globally unique without coordination
- Consistent with Beads convention
- Decentralized - any system can create IDs
- No state needed to generate

### Relationships via `parent_id`

Without sequential IDs, relationships are tracked via the `parent_id` field:

```json
{"id": "bd-e7f3a", "title": "[Epic] Implement auth", "type": "epic"}
{"id": "bd-9c2d1", "title": "Add JWT validation", "parent_id": "bd-e7f3a", "type": "task"}
{"id": "bd-b4a8f", "title": "Create login endpoint", "parent_id": "bd-e7f3a", "type": "task"}
```

### Hash Generation

```python
import hashlib
import uuid

def generate_beads_id() -> str:
    """Generate a unique Beads-style ID."""
    uid = str(uuid.uuid4())
    hash_digest = hashlib.sha256(uid.encode()).hexdigest()
    return f"bd-{hash_digest[:5]}"
```

---

## Configuration

**New:** `src/asp/config.py`

```python
@dataclass
class BeadsConfig:
    """Configuration for Beads integration."""

    # Auto-sync behavior
    auto_sync_plans: bool = False          # Sync plans to Beads automatically
    create_epics: bool = True              # Create epic for each plan
    update_on_resync: bool = False         # Update existing issues on re-sync

    # Issue creation
    default_priority: int = 2              # Default priority for new issues
    add_complexity_labels: bool = True     # Add complexity as labels

    # Paths
    beads_root: Path = Path(".")           # Root path for .beads directory
```

---

## Migration Strategy

### Phase 1: Manual CLI Trigger (This PR)

1. Add `asp beads list` command
2. Add `asp beads process <issue_id>` command
3. No changes to existing agents or orchestrators

**Deliverables:**
- `src/asp/cli/beads_commands.py`
- Tests for CLI commands
- Documentation

### Phase 2: Kanban UI Action

1. Add "Plan with ASP" button to issue cards
2. Add `/kanban/process/{id}` endpoint
3. Show plan summary in UI

**Deliverables:**
- Modified `src/asp/web/kanban.py`
- HTMX interactions for async processing
- Loading states and error handling

### Phase 3: Auto-Sync

1. Add `beads_sync.py` module
2. Add `sync_to_beads` option to PlanningAgent
3. Add configuration options
4. Support bidirectional sync

**Deliverables:**
- `src/asp/utils/beads_sync.py`
- Modified `PlanningAgent`
- Configuration in `BeadsConfig`

### Phase 4: GitHub Bidirectional Sync

Bidirectional sync between Beads and GitHub Issues for team collaboration and external issue intake.

#### Architecture

```
                         ┌──────────────────────────────────────┐
                         │          github_sync.py              │
                         │                                      │
┌─────────────────┐      │  ┌────────────┐    ┌────────────┐   │      ┌──────────────────┐
│  .beads/        │◄────►│  │  Export    │    │  Import    │   │◄────►│  GitHub Issues   │
│  issues.jsonl   │      │  │  (push)    │    │  (pull)    │   │      │                  │
└─────────────────┘      │  └────────────┘    └────────────┘   │      └────────┬─────────┘
                         │         │                │          │               │
                         │         └───────┬────────┘          │               │
                         │                 ▼                   │               │
                         │        ┌────────────────┐           │               │
                         │        │ Conflict Res.  │           │               │
                         │        │ (last-write)   │           │               │
                         │        └────────────────┘           │               │
                         └──────────────────────────────────────┘               │
                                                                               │
                                          ┌──────────────────┐                 │
                                          │  GitHub Projects │◄────────────────┘
                                          │  (optional)      │
                                          └──────────────────┘
```

#### Sync Directions

| Direction | Use Case | Trigger |
|-----------|----------|---------|
| **Beads → GitHub** | Share local work with team, external visibility | `asp beads push` or auto on commit |
| **GitHub → Beads** | Import issues for local ASP processing | `asp beads pull` or manual import |
| **Bidirectional** | Full sync, team collaboration | `asp beads sync` |

#### Approach Options

| Approach | Description | Pros | Cons |
|----------|-------------|------|------|
| **A: Via GitHub Issues** | Sync Beads ↔ GH Issues → Projects | Simple, native integration | Creates "real" issues |
| **B: Direct Projects API** | Create project items via GraphQL | Cleaner repo, no issue clutter | Complex auth, GraphQL |
| **C: GitHub Actions** | Auto-sync on push to `.beads/` | Fully automated | Another moving part |

**Recommended:** Start with Approach A (via GitHub Issues) for simplicity, with option to add Approach C for automation.

#### Implementation: Via GitHub Issues

**New File:** `src/asp/utils/github_sync.py`

```python
"""Sync Beads issues to GitHub Issues and Projects."""

import logging
import subprocess
from pathlib import Path
from typing import Optional

from asp.utils.beads import read_issues, BeadsIssue, BeadsStatus

logger = logging.getLogger(__name__)


def sync_to_github_issues(
    repo: Optional[str] = None,
    project: Optional[str] = None,
    dry_run: bool = False,
) -> list[str]:
    """
    Sync Beads issues to GitHub Issues.

    Args:
        repo: GitHub repo (owner/name). Auto-detected if None.
        project: GitHub Project number to add issues to.
        dry_run: If True, show what would happen without creating.

    Returns:
        List of created GitHub issue URLs.
    """
    issues = read_issues()
    created_urls = []

    for issue in issues:
        # Skip closed issues
        if issue.status == BeadsStatus.CLOSED:
            continue

        # Check if already synced (via label)
        if _is_synced(issue):
            continue

        if dry_run:
            logger.info("Would create: %s", issue.title)
            continue

        # Create GitHub issue
        url = _create_github_issue(issue, repo)
        if url:
            created_urls.append(url)
            _mark_synced(issue)

            # Add to project if specified
            if project:
                _add_to_project(url, project)

    return created_urls


def _create_github_issue(issue: BeadsIssue, repo: Optional[str]) -> Optional[str]:
    """Create a GitHub issue using gh CLI."""
    cmd = ["gh", "issue", "create"]

    if repo:
        cmd.extend(["--repo", repo])

    cmd.extend([
        "--title", f"[{issue.id}] {issue.title}",
        "--body", _format_body(issue),
        "--label", f"beads,beads-{issue.type.value}",
    ])

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        logger.error("Failed to create issue: %s", e.stderr)
        return None


def _format_body(issue: BeadsIssue) -> str:
    """Format issue body with Beads metadata."""
    return f"""
{issue.description or "No description"}

---
**Beads Metadata**
- ID: `{issue.id}`
- Type: {issue.type.value}
- Priority: {issue.priority}
- Status: {issue.status.value}
"""


def _is_synced(issue: BeadsIssue) -> bool:
    """Check if issue has been synced to GitHub."""
    return "gh-synced" in issue.labels


def _mark_synced(issue: BeadsIssue) -> None:
    """Mark issue as synced by adding label."""
    from asp.utils.beads import read_issues, write_issues

    issues = read_issues()
    for i in issues:
        if i.id == issue.id:
            if "gh-synced" not in i.labels:
                i.labels.append("gh-synced")
            break
    write_issues(issues)


def _add_to_project(issue_url: str, project_number: str) -> None:
    """Add issue to GitHub Project."""
    # Extract issue number from URL
    issue_num = issue_url.split("/")[-1]

    cmd = [
        "gh", "project", "item-add", project_number,
        "--owner", "@me",
        "--url", issue_url,
    ]

    try:
        subprocess.run(cmd, capture_output=True, text=True, check=True)
        logger.info("Added issue %s to project %s", issue_num, project_number)
    except subprocess.CalledProcessError as e:
        logger.warning("Failed to add to project: %s", e.stderr)


# =============================================================================
# IMPORT: GitHub → Beads
# =============================================================================

def import_from_github(
    repo: Optional[str] = None,
    issue_number: Optional[int] = None,
    label_filter: Optional[str] = None,
    state: str = "open",
    dry_run: bool = False,
) -> list[BeadsIssue]:
    """
    Import GitHub issues into Beads.

    Args:
        repo: GitHub repo (owner/name). Auto-detected if None.
        issue_number: Specific issue to import. If None, imports all matching.
        label_filter: Only import issues with this label.
        state: Issue state filter: "open", "closed", or "all".
        dry_run: If True, show what would be imported without creating.

    Returns:
        List of created BeadsIssues.
    """
    if issue_number:
        gh_issues = [_fetch_github_issue(issue_number, repo)]
    else:
        gh_issues = _fetch_github_issues(repo, label_filter, state)

    created = []
    existing_issues = read_issues()
    existing_gh_ids = {_get_github_ref(i) for i in existing_issues if _get_github_ref(i)}

    for gh_issue in gh_issues:
        gh_ref = f"gh-{gh_issue['number']}"

        # Skip if already imported
        if gh_ref in existing_gh_ids:
            logger.info("Skipping %s (already imported)", gh_ref)
            continue

        if dry_run:
            logger.info("Would import: #%s %s", gh_issue["number"], gh_issue["title"])
            continue

        beads_issue = _convert_to_beads(gh_issue)
        existing_issues.append(beads_issue)
        created.append(beads_issue)

    if not dry_run and created:
        write_issues(existing_issues)
        logger.info("Imported %d issues from GitHub", len(created))

    return created


def import_single_issue(
    issue_number: int,
    repo: Optional[str] = None,
) -> Optional[BeadsIssue]:
    """
    Import a single GitHub issue into Beads.

    Args:
        issue_number: GitHub issue number to import.
        repo: GitHub repo (owner/name). Auto-detected if None.

    Returns:
        Created BeadsIssue, or None if already exists.
    """
    result = import_from_github(repo=repo, issue_number=issue_number)
    return result[0] if result else None


def _fetch_github_issue(issue_number: int, repo: Optional[str]) -> dict:
    """Fetch a single GitHub issue."""
    cmd = ["gh", "issue", "view", str(issue_number), "--json",
           "number,title,body,labels,state,assignees,createdAt,updatedAt"]

    if repo:
        cmd.extend(["--repo", repo])

    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    return json.loads(result.stdout)


def _fetch_github_issues(
    repo: Optional[str],
    label_filter: Optional[str],
    state: str,
) -> list[dict]:
    """Fetch multiple GitHub issues."""
    cmd = ["gh", "issue", "list", "--json",
           "number,title,body,labels,state,assignees,createdAt,updatedAt",
           "--state", state, "--limit", "100"]

    if repo:
        cmd.extend(["--repo", repo])

    if label_filter:
        cmd.extend(["--label", label_filter])

    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    return json.loads(result.stdout)


def _convert_to_beads(gh_issue: dict) -> BeadsIssue:
    """Convert a GitHub issue to a BeadsIssue."""
    from asp.utils.beads import generate_beads_id

    # Map GitHub labels to Beads type
    labels = [l["name"] for l in gh_issue.get("labels", [])]
    issue_type = _infer_type_from_labels(labels)

    # Map GitHub state to Beads status
    status = BeadsStatus.CLOSED if gh_issue["state"] == "CLOSED" else BeadsStatus.OPEN

    return BeadsIssue(
        id=generate_beads_id(),
        title=gh_issue["title"],
        description=gh_issue.get("body") or "",
        status=status,
        type=issue_type,
        priority=2,  # Default, could infer from labels
        labels=[f"gh-{gh_issue['number']}"] + labels,  # Track origin
        created_at=gh_issue.get("createdAt"),
        updated_at=gh_issue.get("updatedAt"),
        source_repo=gh_issue.get("repository", {}).get("nameWithOwner"),
    )


def _infer_type_from_labels(labels: list[str]) -> BeadsType:
    """Infer Beads type from GitHub labels."""
    labels_lower = [l.lower() for l in labels]

    if "bug" in labels_lower:
        return BeadsType.BUG
    elif "enhancement" in labels_lower or "feature" in labels_lower:
        return BeadsType.FEATURE
    elif "epic" in labels_lower:
        return BeadsType.EPIC
    elif "chore" in labels_lower or "maintenance" in labels_lower:
        return BeadsType.CHORE
    else:
        return BeadsType.TASK


def _get_github_ref(issue: BeadsIssue) -> Optional[str]:
    """Extract GitHub reference from Beads issue labels."""
    for label in issue.labels:
        if label.startswith("gh-") and label[3:].isdigit():
            return label
    return None


# =============================================================================
# BIDIRECTIONAL SYNC
# =============================================================================

def sync_bidirectional(
    repo: Optional[str] = None,
    project: Optional[str] = None,
    conflict_resolution: str = "local-wins",
    dry_run: bool = False,
) -> dict:
    """
    Perform bidirectional sync between Beads and GitHub.

    Args:
        repo: GitHub repo (owner/name). Auto-detected if None.
        project: GitHub Project number to add new issues to.
        conflict_resolution: How to handle conflicts:
            - "local-wins": Beads version takes precedence
            - "remote-wins": GitHub version takes precedence
            - "newest-wins": Most recently updated wins
        dry_run: If True, show what would happen without changes.

    Returns:
        Dict with sync statistics: {"imported": N, "exported": N, "conflicts": N}
    """
    stats = {"imported": 0, "exported": 0, "conflicts": 0, "skipped": 0}

    # Phase 1: Import new GitHub issues (those not in Beads)
    imported = import_from_github(repo=repo, dry_run=dry_run)
    stats["imported"] = len(imported)

    # Phase 2: Export new Beads issues (those not in GitHub)
    exported = sync_to_github_issues(repo=repo, project=project, dry_run=dry_run)
    stats["exported"] = len(exported)

    # Phase 3: Handle conflicts (issues that exist in both)
    if not dry_run:
        conflicts = _resolve_conflicts(repo, conflict_resolution)
        stats["conflicts"] = conflicts

    return stats


def _resolve_conflicts(repo: Optional[str], strategy: str) -> int:
    """
    Resolve conflicts between linked Beads and GitHub issues.

    Returns number of conflicts resolved.
    """
    conflicts_resolved = 0
    issues = read_issues()

    for issue in issues:
        gh_ref = _get_github_ref(issue)
        if not gh_ref:
            continue

        gh_number = int(gh_ref.split("-")[1])

        try:
            gh_issue = _fetch_github_issue(gh_number, repo)
        except subprocess.CalledProcessError:
            continue  # GitHub issue may have been deleted

        # Compare timestamps
        local_updated = issue.updated_at or issue.created_at
        remote_updated = gh_issue.get("updatedAt")

        if not local_updated or not remote_updated:
            continue

        # Check if there's a conflict (both modified since last sync)
        if _has_conflict(issue, gh_issue):
            if strategy == "local-wins":
                _push_to_github(issue, gh_number, repo)
            elif strategy == "remote-wins":
                _update_from_github(issue, gh_issue)
            elif strategy == "newest-wins":
                if remote_updated > local_updated:
                    _update_from_github(issue, gh_issue)
                else:
                    _push_to_github(issue, gh_number, repo)

            conflicts_resolved += 1

    if conflicts_resolved:
        write_issues(issues)

    return conflicts_resolved


def _has_conflict(local: BeadsIssue, remote: dict) -> bool:
    """Check if local and remote have diverged."""
    # Simple check: titles differ
    return local.title != remote["title"]


def _push_to_github(issue: BeadsIssue, gh_number: int, repo: Optional[str]) -> None:
    """Update GitHub issue from Beads."""
    cmd = ["gh", "issue", "edit", str(gh_number),
           "--title", issue.title,
           "--body", issue.description or ""]

    if repo:
        cmd.extend(["--repo", repo])

    subprocess.run(cmd, capture_output=True, text=True, check=True)


def _update_from_github(issue: BeadsIssue, gh_issue: dict) -> None:
    """Update Beads issue from GitHub."""
    issue.title = gh_issue["title"]
    issue.description = gh_issue.get("body") or ""
    issue.updated_at = gh_issue.get("updatedAt")

    if gh_issue["state"] == "CLOSED":
        issue.status = BeadsStatus.CLOSED
```

#### CLI Commands

**Modified:** `src/asp/cli/beads_commands.py`

```python
@beads.command()
@click.option("--repo", help="GitHub repo (owner/name)")
@click.option("--project", help="GitHub Project number")
@click.option("--dry-run", is_flag=True, help="Show what would be synced")
def push(repo: str, project: str, dry_run: bool):
    """
    Push Beads issues to GitHub Issues.

    Example:
        asp beads push
        asp beads push --project 1
        asp beads push --repo owner/repo --dry-run
    """
    from asp.utils.github_sync import sync_to_github_issues

    urls = sync_to_github_issues(repo=repo, project=project, dry_run=dry_run)

    if dry_run:
        click.echo("Dry run complete.")
    else:
        click.echo(f"Created {len(urls)} GitHub issues:")
        for url in urls:
            click.echo(f"  {url}")


@beads.command()
@click.argument("issue_number", required=False, type=int)
@click.option("--repo", help="GitHub repo (owner/name)")
@click.option("--label", help="Only import issues with this label")
@click.option("--state", default="open", type=click.Choice(["open", "closed", "all"]))
@click.option("--dry-run", is_flag=True, help="Show what would be imported")
def pull(issue_number: int, repo: str, label: str, state: str, dry_run: bool):
    """
    Pull GitHub issues into Beads.

    Import a single issue by number, or all matching issues.

    Example:
        asp beads pull 42                    # Import issue #42
        asp beads pull --label "asp"         # Import all issues with "asp" label
        asp beads pull --state all           # Import all open and closed issues
        asp beads pull --dry-run             # Preview what would be imported
    """
    from asp.utils.github_sync import import_from_github

    issues = import_from_github(
        repo=repo,
        issue_number=issue_number,
        label_filter=label,
        state=state,
        dry_run=dry_run,
    )

    if dry_run:
        click.echo("Dry run complete.")
    else:
        click.echo(f"Imported {len(issues)} issues:")
        for issue in issues:
            click.echo(f"  [{issue.id}] {issue.title}")


@beads.command()
@click.option("--repo", help="GitHub repo (owner/name)")
@click.option("--project", help="GitHub Project number")
@click.option("--strategy", default="local-wins",
              type=click.Choice(["local-wins", "remote-wins", "newest-wins"]),
              help="Conflict resolution strategy")
@click.option("--dry-run", is_flag=True, help="Show what would be synced")
def sync(repo: str, project: str, strategy: str, dry_run: bool):
    """
    Bidirectional sync between Beads and GitHub.

    Imports new GitHub issues, exports new Beads issues, and resolves conflicts.

    Example:
        asp beads sync                           # Sync with defaults (local-wins)
        asp beads sync --strategy newest-wins    # Most recent update wins
        asp beads sync --dry-run                 # Preview changes
    """
    from asp.utils.github_sync import sync_bidirectional

    stats = sync_bidirectional(
        repo=repo,
        project=project,
        conflict_resolution=strategy,
        dry_run=dry_run,
    )

    if dry_run:
        click.echo("Dry run complete.")

    click.echo(f"Sync results:")
    click.echo(f"  Imported: {stats['imported']}")
    click.echo(f"  Exported: {stats['exported']}")
    click.echo(f"  Conflicts resolved: {stats['conflicts']}")
```

#### GitHub Actions Automation (Optional)

**New File:** `.github/workflows/beads-sync.yml`

```yaml
name: Sync Beads to GitHub

on:
  push:
    paths:
      - '.beads/issues.jsonl'

jobs:
  sync:
    runs-on: ubuntu-latest
    permissions:
      issues: write
      repository-projects: write

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'

      - name: Install dependencies
        run: |
          pip install -e .

      - name: Sync to GitHub Issues
        env:
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: |
          asp beads sync-github --project ${{ vars.BEADS_PROJECT_NUMBER }}
```

#### Configuration

**Extended:** `src/asp/config.py`

```python
@dataclass
class BeadsConfig:
    # ... existing fields ...

    # GitHub sync - general
    github_sync_enabled: bool = False
    github_repo: Optional[str] = None      # Auto-detect if None
    github_project: Optional[str] = None   # Project number

    # GitHub sync - export (Beads → GitHub)
    github_auto_push: bool = False         # Push on issue creation
    github_push_labels: list[str] = field(default_factory=lambda: ["beads"])

    # GitHub sync - import (GitHub → Beads)
    github_import_label: Optional[str] = None  # Only import with this label
    github_import_state: str = "open"          # open, closed, all
    github_auto_pull: bool = False             # Pull on sync command

    # GitHub sync - conflict resolution
    github_conflict_strategy: str = "local-wins"  # local-wins, remote-wins, newest-wins
```

**Deliverables:**
- `src/asp/utils/github_sync.py` (with import, export, and bidirectional sync)
- Modified `src/asp/cli/beads_commands.py` (push, pull, sync commands)
- `.github/workflows/beads-sync.yml` (optional)
- Extended `BeadsConfig`
- `tests/unit/test_github_sync.py`

---

## File Summary

### New Files

| File | Description | Phase |
|------|-------------|-------|
| `src/asp/cli/beads_commands.py` | CLI commands for Beads integration | 1 |
| `src/asp/utils/beads_sync.py` | Plan-to-Beads sync utilities | 3 |
| `src/asp/utils/github_sync.py` | GitHub bidirectional sync (import, export, sync) | 4 |
| `.github/workflows/beads-sync.yml` | Auto-sync on push (optional) | 4 |
| `tests/unit/test_beads_cli.py` | CLI command tests | 1 |
| `tests/unit/test_beads_sync.py` | Sync utility tests | 3 |
| `tests/unit/test_github_sync.py` | GitHub sync tests (import, export, bidirectional) | 4 |

### Modified Files

| File | Change | Phase |
|------|--------|-------|
| `src/asp/cli/__init__.py` | Add beads command group | 1 |
| `src/asp/web/kanban.py` | Add ASP action button and endpoint | 2 |
| `src/asp/agents/planning_agent.py` | Add sync_to_beads option | 3 |
| `src/asp/config.py` | Add BeadsConfig, GitHub sync options | 3, 4 |
| `src/asp/cli/beads_commands.py` | Add push, pull, sync commands | 4 |
| `src/asp/utils/beads.py` | Add `generate_beads_id()` function | 4 |

---

## Migrating ASP Task Numbering to Hash-Based IDs

The existing ASP system uses sequential task IDs (e.g., `TASK-001`, `HW-CODE-001`). This section describes migrating to hash-based IDs for consistency with Beads.

### Current ASP ID System

```python
# Current: Sequential IDs in TaskRequirements
requirements = TaskRequirements(
    task_id="TASK-001",           # User-provided, sequential
    description="Build auth system",
    ...
)

# Current: Artifacts use task_id as directory name
artifacts/TASK-001/plan.json
artifacts/TASK-001/design.json
```

**Problems:**
- User must provide meaningful, unique task_id
- No standard format enforced
- Collision risk across projects
- Artifacts directory tied to user-provided name

### Proposed: Hash-Based ASP IDs

```python
# New: Auto-generated hash IDs
requirements = TaskRequirements(
    task_id="bd-7a3f2",           # Auto-generated if not provided
    description="Build auth system",
    human_label="auth-system",    # Optional human-friendly label
    ...
)

# New: Artifacts use hash ID
artifacts/bd-7a3f2/plan.json
artifacts/bd-7a3f2/design.json
```

### Migration Strategy

#### Phase 1: Support Both (Backward Compatible)

```python
# src/asp/models/planning.py

class TaskRequirements(BaseModel):
    task_id: str = Field(default_factory=generate_beads_id)
    human_label: Optional[str] = None  # For display/reference
    description: str
    requirements: str
    context_files: list[str] = []

    @property
    def display_name(self) -> str:
        """Human-friendly name for UI/logs."""
        return self.human_label or self.task_id
```

- `task_id` auto-generates hash if not provided
- Existing code using explicit task_ids continues to work
- New `human_label` field for human-readable reference

#### Phase 2: Artifact Directory Migration

```python
# src/asp/utils/artifact_io.py

def get_artifact_path(task_id: str, artifact_type: str) -> Path:
    """Get artifact path, supporting both old and new ID formats."""
    base = Path("artifacts")

    # Check if old-style directory exists (backward compat)
    old_path = base / task_id / f"{artifact_type}.json"
    if old_path.exists():
        return old_path

    # Use new hash-based path
    return base / task_id / f"{artifact_type}.json"
```

#### Phase 3: ID Registry (Optional)

For traceability between hash IDs and human labels:

```python
# .asp/id_registry.jsonl
{"id": "bd-7a3f2", "label": "auth-system", "created": "2025-12-15T..."}
{"id": "bd-9c2d1", "label": "jwt-validation", "parent": "bd-7a3f2", "created": "2025-12-15T..."}
```

```python
# src/asp/utils/id_registry.py

def register_id(task_id: str, label: str, parent_id: Optional[str] = None) -> None:
    """Register a task ID with human-readable label."""
    ...

def lookup_by_label(label: str) -> Optional[str]:
    """Find task_id by human label."""
    ...

def lookup_by_id(task_id: str) -> Optional[dict]:
    """Get metadata for a task ID."""
    ...
```

### Changes to Existing Code

| File | Change |
|------|--------|
| `src/asp/models/planning.py` | Add `human_label`, default `task_id` to hash |
| `src/asp/utils/artifact_io.py` | Support both ID formats |
| `src/asp/agents/planning_agent.py` | Generate hash IDs for semantic units |
| `src/asp/cli/*.py` | Accept hash or label as input |
| `src/asp/web/*.py` | Display `human_label` when available |

### Example: Before and After

**Before (Sequential):**
```bash
asp plan --task-id TASK-001 --description "Build auth"
# Creates: artifacts/TASK-001/plan.json
```

**After (Hash-Based):**
```bash
asp plan --label "auth-system" --description "Build auth"
# Creates: artifacts/bd-7a3f2/plan.json
# Registry: bd-7a3f2 -> "auth-system"

# Can still reference by label:
asp status auth-system
# Resolves to bd-7a3f2
```

### Backward Compatibility

1. **Existing artifacts** - Old directories (`TASK-001/`) remain valid
2. **Explicit task_ids** - Users can still provide their own IDs
3. **Gradual migration** - No big-bang conversion required
4. **Registry is optional** - System works without it (just less human-friendly)

---

## Consequences

### Positive

- **Traceability** - Clear link between issues, plans, and execution
- **Visibility** - Plans become trackable tasks in Kanban
- **Flexibility** - Three integration points for different workflows
- **Git-Native** - All data stays in repository
- **Incremental** - Each phase is independently useful

### Negative

- **ID Coupling** - Issue IDs become meaningful (epic-*, task-*)
- **Sync Complexity** - Bidirectional sync can have edge cases
- **UI Coupling** - Kanban changes depend on HTMX behavior

### Risks

| Risk | Mitigation |
|------|------------|
| ID collisions | Use task_id prefix for generated issues |
| Stale sync | Add `updated_at` timestamps, warn on conflicts |
| Large plans overwhelming Kanban | Pagination, collapsible epics |
| LLM latency in UI | Async processing with loading indicator |

---

## Open Questions

1. **Execution Tracking** - Should we update issue status as ASP executes (e.g., mark "in progress" during codegen)?

2. **Failure Handling** - What happens to Beads issues when ASP execution fails?

3. **Re-planning** - If a plan changes, should we update or replace existing issues?

4. **Metrics** - Should we track cycle time from issue creation to completion?

---

## Related Documents

- `design/ADR_008_async_process_architecture.md` - Async execution (relevant for UI actions)
- `docs/planning_agent_user_guide.md` - PlanningAgent documentation
- PR number 100 - Beads integration foundation

---

**Status:** Proposed
**Next Steps:**
1. Phase 1: Manual CLI Trigger (`asp beads list`, `asp beads process`)
2. Phase 2: Kanban UI Action
3. Phase 3: Auto-Sync Plans to Beads
4. Phase 4: GitHub Bidirectional Sync (`asp beads push`, `asp beads pull`, `asp beads sync`)
