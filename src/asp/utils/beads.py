"""
Beads Integration Module

This module provides utilities for interacting with the Beads issue tracking system.
It reads and writes to the .beads/issues.jsonl file, which is the source of truth
for Beads issues.

See: https://github.com/steveyegge/beads
"""

import hashlib
import json
import logging
import uuid
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import List, Optional

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class BeadsStatus(str, Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    CLOSED = "closed"


class BeadsType(str, Enum):
    TASK = "task"
    BUG = "bug"
    FEATURE = "feature"
    EPIC = "epic"
    CHORE = "chore"


class BeadsIssue(BaseModel):
    """
    Represents a single issue in the Beads system.
    Matches the schema found in .beads/issues.jsonl
    """
    id: str
    title: str
    description: Optional[str] = ""
    status: BeadsStatus = BeadsStatus.OPEN
    priority: int = 2  # 0=Highest, 4=Lowest
    type: BeadsType = BeadsType.TASK
    assignee: Optional[str] = None
    labels: List[str] = Field(default_factory=list)

    # Timestamps are usually strings in ISO format in JSONL
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    closed_at: Optional[str] = None

    source_repo: Optional[str] = None

    # Dependencies are stored as a list of strings (IDs) or objects in some versions.
    # The README says "four dependency types".
    # Usually in the JSONL it might be a list of relation objects or just IDs?
    # Let's assume for now we might see a list of IDs in a simple field or we need to parse relations.
    # Looking at the README, `bd dep add` adds a dependency.
    # Let's keep it flexible for now.
    parent_id: Optional[str] = None


    class Config:
        extra = "allow"  # Allow extra fields since the schema might evolve


def get_beads_directory(root_path: Path = Path(".")) -> Path:
    return root_path / ".beads"


def get_issues_file(root_path: Path = Path(".")) -> Path:
    return get_beads_directory(root_path) / "issues.jsonl"


def read_issues(root_path: Path = Path(".")) -> List[BeadsIssue]:
    """
    Reads all issues from .beads/issues.jsonl
    """
    issues_file = get_issues_file(root_path)
    if not issues_file.exists():
        return []

    issues = []
    try:
        with open(issues_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    data = json.loads(line)
                    # Handle potential field discrepancies
                    issues.append(BeadsIssue(**data))
                except json.JSONDecodeError:
                    continue
                except Exception as e:
                    # Skip malformed lines
                    logger.warning("Error parsing beads issue line: %s", e)
                    continue
    except Exception as e:
        logger.warning("Error reading beads file: %s", e)
        return []

    return issues


def write_issues(issues: List[BeadsIssue], root_path: Path = Path(".")) -> None:
    """
    Writes a list of issues to .beads/issues.jsonl
    """
    issues_file = get_issues_file(root_path)
    issues_file.parent.mkdir(parents=True, exist_ok=True)

    with open(issues_file, "w", encoding="utf-8") as f:
        for issue in issues:
            f.write(issue.model_dump_json(exclude_none=True) + "\n")


def create_issue(
    title: str,
    description: str = "",
    priority: int = 2,
    issue_type: BeadsType = BeadsType.TASK,
    root_path: Path = Path(".")
) -> BeadsIssue:
    """
    Creates a new issue and appends it to the file.
    Note: This is a simple implementation. Real `bd` handles ID generation (sequential or hash).
    Here we will generate a simple hash-based ID for compatibility if needed,
    or just use a timestamp based one for now if we lack the DB state.

    Actually, to be safe and avoid collisions if `bd` is used, we should try to use `bd` CLI if available.
    But for this Python implementation, we'll try to emulate hash-based IDs.
    """
    # Generate a short hash ID similar to beads v0.20.1+
    # "bd-" + 4-6 chars of hash
    uid = str(uuid.uuid4())
    hash_object = hashlib.sha256(uid.encode())
    hex_dig = hash_object.hexdigest()
    short_hash = hex_dig[:5]  # 5 chars seems safe enough for small lists
    issue_id = f"bd-{short_hash}"

    now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

    issue = BeadsIssue(
        id=issue_id,
        title=title,
        description=description,
        priority=priority,
        type=issue_type,
        created_at=now,
        updated_at=now,
        status=BeadsStatus.OPEN
    )

    # Append to file (read-modify-write is safer to ensure we don't overwrite concurrent writes roughly)
    # But for a simple append, we can just append.
    # However, JSONL usually requires full file validity.
    # Let's read, append, write for now to be safe with our own logic.
    existing = read_issues(root_path)
    existing.append(issue)
    write_issues(existing, root_path)

    return issue
