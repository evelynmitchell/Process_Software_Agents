"""
GitHub Sync Module - Bidirectional sync between Beads and GitHub Issues.

This module provides utilities for syncing Beads issues with GitHub Issues,
enabling team collaboration and external issue intake.

Commands:
- push: Export Beads issues to GitHub Issues
- pull: Import GitHub Issues into Beads
- gh-sync: Bidirectional sync

See ADR 009 Phase 4 for architecture details.
"""

import json
import logging
import subprocess
from datetime import UTC, datetime
from pathlib import Path

from asp.utils.beads import (
    BeadsIssue,
    BeadsStatus,
    BeadsType,
    generate_beads_id,
    read_issues,
    write_issues,
)

logger = logging.getLogger(__name__)


# =============================================================================
# EXPORT: Beads → GitHub
# =============================================================================


def push_to_github(
    repo: str | None = None,
    project: str | None = None,
    dry_run: bool = False,
    root_path: Path = Path("."),
) -> list[str]:
    """
    Push Beads issues to GitHub Issues.

    Creates GitHub Issues for Beads issues that haven't been synced yet.
    Optionally adds them to a GitHub Project.

    Args:
        repo: GitHub repo (owner/name). Auto-detected if None.
        project: GitHub Project number to add issues to.
        dry_run: If True, show what would happen without creating.
        root_path: Root path for .beads directory.

    Returns:
        List of created GitHub issue URLs.

    Example:
        >>> urls = push_to_github(repo="owner/repo", dry_run=True)
        >>> print(f"Would create {len(urls)} issues")
    """
    issues = read_issues(root_path)
    created_urls = []

    for issue in issues:
        # Skip closed issues
        if issue.status == BeadsStatus.CLOSED:
            continue

        # Skip if already synced (has gh-synced label)
        if _is_gh_synced(issue):
            logger.debug("Skipping %s (already synced)", issue.id)
            continue

        if dry_run:
            logger.info("Would push: [%s] %s", issue.id, issue.title)
            created_urls.append(f"(dry-run) {issue.id}")
            continue

        # Create GitHub issue
        url = _create_github_issue(issue, repo)
        if url:
            created_urls.append(url)
            _mark_gh_synced(issue, url, root_path)
            logger.info("Created GitHub issue: %s", url)

            # Add to project if specified
            if project:
                _add_to_project(url, project, repo)

    return created_urls


def _create_github_issue(issue: BeadsIssue, repo: str | None) -> str | None:
    """Create a GitHub issue using gh CLI."""
    cmd = ["gh", "issue", "create"]

    if repo:
        cmd.extend(["--repo", repo])

    # Build labels
    labels = ["beads", f"beads-{issue.type.value}"]
    if issue.priority <= 1:
        labels.append("priority-high")

    cmd.extend(
        [
            "--title",
            f"[{issue.id}] {issue.title}",
            "--body",
            _format_gh_body(issue),
            "--label",
            ",".join(labels),
        ]
    )

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        logger.error("Failed to create issue: %s", e.stderr)
        return None


def _format_gh_body(issue: BeadsIssue) -> str:
    """Format issue body with Beads metadata."""
    body = issue.description or "No description"
    return f"""{body}

---
**Beads Metadata**
- ID: `{issue.id}`
- Type: {issue.type.value}
- Priority: P{issue.priority}
- Status: {issue.status.value}
"""


def _is_gh_synced(issue: BeadsIssue) -> bool:
    """Check if issue has been synced to GitHub."""
    return any(label.startswith("gh-synced") for label in issue.labels)


def _mark_gh_synced(issue: BeadsIssue, gh_url: str, root_path: Path) -> None:
    """Mark issue as synced by adding label with GitHub URL."""
    issues = read_issues(root_path)
    for i in issues:
        if i.id == issue.id:
            # Extract issue number from URL
            gh_number = gh_url.split("/")[-1]
            sync_label = f"gh-synced-{gh_number}"
            if sync_label not in i.labels:
                i.labels.append(sync_label)
            i.updated_at = _now()
            break
    write_issues(issues, root_path)


def _add_to_project(issue_url: str, project_number: str, repo: str | None) -> None:
    """Add issue to GitHub Project."""
    # Get owner from repo or use @me
    owner = repo.split("/")[0] if repo else "@me"

    cmd = [
        "gh",
        "project",
        "item-add",
        project_number,
        "--owner",
        owner,
        "--url",
        issue_url,
    ]

    try:
        subprocess.run(cmd, capture_output=True, text=True, check=True)
        logger.info("Added to project %s", project_number)
    except subprocess.CalledProcessError as e:
        logger.warning("Failed to add to project: %s", e.stderr)


# =============================================================================
# IMPORT: GitHub → Beads
# =============================================================================


def pull_from_github(
    repo: str | None = None,
    issue_number: int | None = None,
    label_filter: str | None = None,
    state: str = "open",
    dry_run: bool = False,
    root_path: Path = Path("."),
) -> list[BeadsIssue]:
    """
    Pull GitHub issues into Beads.

    Imports GitHub Issues that haven't been imported yet.

    Args:
        repo: GitHub repo (owner/name). Auto-detected if None.
        issue_number: Specific issue to import. If None, imports all matching.
        label_filter: Only import issues with this label.
        state: Issue state filter: "open", "closed", or "all".
        dry_run: If True, show what would be imported without creating.
        root_path: Root path for .beads directory.

    Returns:
        List of created BeadsIssues.

    Example:
        >>> issues = pull_from_github(issue_number=42)
        >>> print(f"Imported: {issues[0].title}")
    """
    if issue_number:
        gh_issues = [_fetch_github_issue(issue_number, repo)]
    else:
        gh_issues = _fetch_github_issues(repo, label_filter, state)

    if not gh_issues:
        logger.info("No GitHub issues found to import")
        return []

    created = []
    existing_issues = read_issues(root_path)
    existing_gh_refs = {
        _get_github_ref(i) for i in existing_issues if _get_github_ref(i)
    }

    for gh_issue in gh_issues:
        if gh_issue is None:
            continue

        gh_ref = f"gh-{gh_issue['number']}"

        # Skip if already imported
        if gh_ref in existing_gh_refs:
            logger.debug("Skipping #%s (already imported)", gh_issue["number"])
            continue

        if dry_run:
            logger.info("Would import: #%s %s", gh_issue["number"], gh_issue["title"])
            # Create a placeholder for dry-run
            placeholder = BeadsIssue(
                id=f"(dry-run-{gh_issue['number']})",
                title=gh_issue["title"],
            )
            created.append(placeholder)
            continue

        beads_issue = _convert_to_beads(gh_issue)
        existing_issues.append(beads_issue)
        created.append(beads_issue)
        logger.info("Imported #%s as %s", gh_issue["number"], beads_issue.id)

    if not dry_run and created:
        write_issues(existing_issues, root_path)

    return created


def _fetch_github_issue(issue_number: int, repo: str | None) -> dict | None:
    """Fetch a single GitHub issue."""
    cmd = [
        "gh",
        "issue",
        "view",
        str(issue_number),
        "--json",
        "number,title,body,labels,state,assignees,createdAt,updatedAt",
    ]

    if repo:
        cmd.extend(["--repo", repo])

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return json.loads(result.stdout)
    except subprocess.CalledProcessError as e:
        logger.error("Failed to fetch issue #%s: %s", issue_number, e.stderr)
        return None


def _fetch_github_issues(
    repo: str | None,
    label_filter: str | None,
    state: str,
) -> list[dict]:
    """Fetch multiple GitHub issues."""
    cmd = [
        "gh",
        "issue",
        "list",
        "--json",
        "number,title,body,labels,state,assignees,createdAt,updatedAt",
        "--state",
        state,
        "--limit",
        "100",
    ]

    if repo:
        cmd.extend(["--repo", repo])

    if label_filter:
        cmd.extend(["--label", label_filter])

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return json.loads(result.stdout)
    except subprocess.CalledProcessError as e:
        logger.error("Failed to fetch issues: %s", e.stderr)
        return []


def _convert_to_beads(gh_issue: dict) -> BeadsIssue:
    """Convert a GitHub issue to a BeadsIssue."""
    # Map GitHub labels to Beads type
    labels = [label["name"] for label in gh_issue.get("labels", [])]
    issue_type = _infer_type_from_labels(labels)

    # Map GitHub state to Beads status
    status = BeadsStatus.CLOSED if gh_issue["state"] == "CLOSED" else BeadsStatus.OPEN

    return BeadsIssue(
        id=generate_beads_id(),
        title=gh_issue["title"],
        description=gh_issue.get("body") or "",
        status=status,
        type=issue_type,
        priority=_infer_priority_from_labels(labels),
        labels=[f"gh-{gh_issue['number']}"] + labels,  # Track origin
        created_at=gh_issue.get("createdAt"),
        updated_at=gh_issue.get("updatedAt"),
    )


def _infer_type_from_labels(labels: list[str]) -> BeadsType:
    """Infer Beads type from GitHub labels."""
    labels_lower = [label.lower() for label in labels]

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


def _infer_priority_from_labels(labels: list[str]) -> int:
    """Infer priority from GitHub labels."""
    labels_lower = [label.lower() for label in labels]

    if "priority-critical" in labels_lower or "p0" in labels_lower:
        return 0
    elif "priority-high" in labels_lower or "p1" in labels_lower:
        return 1
    elif "priority-low" in labels_lower or "p3" in labels_lower:
        return 3
    else:
        return 2  # Default medium


def _get_github_ref(issue: BeadsIssue) -> str | None:
    """Extract GitHub reference from Beads issue labels.

    Matches labels like:
    - gh-42 (imported from GitHub)
    - gh-synced-42 (pushed to GitHub)
    """
    for label in issue.labels:
        # Match gh-{number}
        if label.startswith("gh-") and label[3:].split("-")[0].isdigit():
            return label
        # Match gh-synced-{number}
        if label.startswith("gh-synced-") and label[10:].isdigit():
            return label
    return None


# =============================================================================
# BIDIRECTIONAL SYNC
# =============================================================================


def sync_github(
    repo: str | None = None,
    project: str | None = None,
    conflict_strategy: str = "local-wins",
    dry_run: bool = False,
    root_path: Path = Path("."),
) -> dict:
    """
    Perform bidirectional sync between Beads and GitHub.

    Imports new GitHub issues, exports new Beads issues, and optionally
    resolves conflicts between linked issues.

    Args:
        repo: GitHub repo (owner/name). Auto-detected if None.
        project: GitHub Project number to add new issues to.
        conflict_strategy: How to handle conflicts:
            - "local-wins": Beads version takes precedence
            - "remote-wins": GitHub version takes precedence
            - "skip": Don't resolve conflicts, just report
        dry_run: If True, show what would happen without changes.
        root_path: Root path for .beads directory.

    Returns:
        Dict with sync statistics: {"imported": N, "exported": N, "conflicts": N}

    Example:
        >>> stats = sync_github(dry_run=True)
        >>> print(f"Would import {stats['imported']}, export {stats['exported']}")
    """
    stats = {"imported": 0, "exported": 0, "conflicts": 0, "skipped": 0}

    # Phase 1: Import new GitHub issues (those not in Beads)
    logger.info("Phase 1: Pulling from GitHub...")
    imported = pull_from_github(repo=repo, dry_run=dry_run, root_path=root_path)
    stats["imported"] = len(imported)

    # Phase 2: Export new Beads issues (those not in GitHub)
    logger.info("Phase 2: Pushing to GitHub...")
    exported = push_to_github(
        repo=repo, project=project, dry_run=dry_run, root_path=root_path
    )
    stats["exported"] = len(exported)

    # Phase 3: Handle conflicts (issues that exist in both)
    if not dry_run and conflict_strategy != "skip":
        logger.info("Phase 3: Resolving conflicts (strategy: %s)...", conflict_strategy)
        conflicts = _resolve_conflicts(repo, conflict_strategy, root_path)
        stats["conflicts"] = conflicts

    return stats


def _resolve_conflicts(
    repo: str | None,
    strategy: str,
    root_path: Path,
) -> int:
    """
    Resolve conflicts between linked Beads and GitHub issues.

    Returns number of conflicts resolved.
    """
    conflicts_resolved = 0
    issues = read_issues(root_path)
    modified = False

    for issue in issues:
        gh_ref = _get_github_ref(issue)
        if not gh_ref:
            continue

        # Extract issue number from gh-123 or gh-synced-123
        gh_number_str = gh_ref.replace("gh-synced-", "").replace("gh-", "")
        if not gh_number_str.isdigit():
            continue
        gh_number = int(gh_number_str)

        try:
            gh_issue = _fetch_github_issue(gh_number, repo)
            if not gh_issue:
                continue
        except Exception:
            continue  # GitHub issue may have been deleted

        # Check if there's a conflict (titles differ)
        if not _has_conflict(issue, gh_issue):
            continue

        logger.info("Conflict detected: %s vs #%s", issue.id, gh_number)

        if strategy == "local-wins":
            _push_update_to_github(issue, gh_number, repo)
            conflicts_resolved += 1
        elif strategy == "remote-wins":
            _update_from_github(issue, gh_issue)
            modified = True
            conflicts_resolved += 1

    if modified:
        write_issues(issues, root_path)

    return conflicts_resolved


def _has_conflict(local: BeadsIssue, remote: dict) -> bool:
    """Check if local and remote have diverged."""
    # Simple check: titles differ (excluding the [bd-xxx] prefix)
    remote_title = remote["title"]
    # Remove [bd-xxx] prefix if present
    if remote_title.startswith("["):
        remote_title = remote_title.split("] ", 1)[-1]

    return local.title != remote_title


def _push_update_to_github(issue: BeadsIssue, gh_number: int, repo: str | None) -> None:
    """Update GitHub issue from Beads."""
    cmd = [
        "gh",
        "issue",
        "edit",
        str(gh_number),
        "--title",
        f"[{issue.id}] {issue.title}",
        "--body",
        _format_gh_body(issue),
    ]

    if repo:
        cmd.extend(["--repo", repo])

    try:
        subprocess.run(cmd, capture_output=True, text=True, check=True)
        logger.info("Updated GitHub #%s from Beads", gh_number)
    except subprocess.CalledProcessError as e:
        logger.error("Failed to update GitHub #%s: %s", gh_number, e.stderr)


def _update_from_github(issue: BeadsIssue, gh_issue: dict) -> None:
    """Update Beads issue from GitHub."""
    title = gh_issue["title"]
    # Remove [bd-xxx] prefix if present
    if title.startswith("["):
        title = title.split("] ", 1)[-1]

    issue.title = title
    issue.description = gh_issue.get("body") or ""
    issue.updated_at = gh_issue.get("updatedAt") or _now()

    if gh_issue["state"] == "CLOSED":
        issue.status = BeadsStatus.CLOSED
        issue.closed_at = _now()

    logger.info("Updated Beads %s from GitHub", issue.id)


# =============================================================================
# Helpers
# =============================================================================


def _now() -> str:
    """Return current time in ISO format."""
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def verify_gh_cli() -> bool:
    """Verify that gh CLI is installed and authenticated."""
    try:
        result = subprocess.run(
            ["gh", "auth", "status"],
            capture_output=True,
            text=True,
        )
        return result.returncode == 0
    except FileNotFoundError:
        return False
