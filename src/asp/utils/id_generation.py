"""
Hash-based ID generation utilities.

This module provides functions for generating unique, hash-based identifiers
for various ASP entities (semantic units, issues, improvements, etc.).

The hash-based approach replaces sequential IDs (e.g., SU-001, ISSUE-001)
with globally unique identifiers that don't require coordination.

See: ADR 009 (Beads and Planning Agent Integration)
"""

import hashlib
import uuid


def generate_hash_id(prefix: str = "id", length: int = 7) -> str:
    """
    Generate a unique hash-based ID.

    Args:
        prefix: ID prefix (e.g., 'su', 'issue', 'improve')
        length: Number of hex characters (default 7, gives ~268M unique IDs)

    Returns:
        ID in format '{prefix}-{hash}' (e.g., 'su-a3f42bc')

    Example:
        >>> generate_hash_id("su")
        'su-a3f42bc'
        >>> generate_hash_id("issue", length=8)
        'issue-b7c91d4e'
    """
    uid = str(uuid.uuid4())
    hash_digest = hashlib.sha256(uid.encode()).hexdigest()
    return f"{prefix}-{hash_digest[:length]}"


def generate_semantic_unit_id() -> str:
    """
    Generate a semantic unit ID.

    Returns:
        ID in format 'su-{7-char-hex}' (e.g., 'su-a3f42bc')
    """
    return generate_hash_id("su")


def generate_issue_id() -> str:
    """
    Generate a design issue ID.

    Returns:
        ID in format 'issue-{7-char-hex}' (e.g., 'issue-b7c91de')
    """
    return generate_hash_id("issue")


def generate_improvement_id() -> str:
    """
    Generate an improvement suggestion ID.

    Returns:
        ID in format 'improve-{7-char-hex}' (e.g., 'improve-d4e82fa')
    """
    return generate_hash_id("improve")


def generate_code_issue_id() -> str:
    """
    Generate a code issue ID.

    Returns:
        ID in format 'code-issue-{7-char-hex}' (e.g., 'code-issue-f1a23bc')
    """
    return generate_hash_id("code-issue")


def generate_code_improvement_id() -> str:
    """
    Generate a code improvement suggestion ID.

    Returns:
        ID in format 'code-improve-{7-char-hex}' (e.g., 'code-improve-c9d45ef')
    """
    return generate_hash_id("code-improve")


def generate_checklist_id() -> str:
    """
    Generate a checklist item ID.

    Returns:
        ID in format 'check-{7-char-hex}' (e.g., 'check-e2f67ab')
    """
    return generate_hash_id("check")


def generate_task_id() -> str:
    """
    Generate a task ID.

    Returns:
        ID in format 'task-{7-char-hex}' (e.g., 'task-a8b12cd')
    """
    return generate_hash_id("task")


# Regex patterns for validating hash-based IDs
# These can be used in Pydantic model Field definitions
# Using 7 hex chars = 16^7 = 268,435,456 unique IDs (avoids birthday collisions)
HASH_ID_PATTERN = r"^[a-z]+-[a-f0-9]{7}$"
SEMANTIC_UNIT_ID_PATTERN = r"^su-[a-f0-9]{7}$"
ISSUE_ID_PATTERN = r"^issue-[a-f0-9]{7}$"
IMPROVEMENT_ID_PATTERN = r"^improve-[a-f0-9]{7}$"
CODE_ISSUE_ID_PATTERN = r"^code-issue-[a-f0-9]{7}$"
CODE_IMPROVEMENT_ID_PATTERN = r"^code-improve-[a-f0-9]{7}$"
CHECKLIST_ID_PATTERN = r"^check-[a-f0-9]{7}$"
TASK_ID_PATTERN = r"^task-[a-f0-9]{7}$"


def is_valid_hash_id(id_string: str, prefix: str | None = None) -> bool:
    """
    Validate if a string is a valid hash-based ID.

    Args:
        id_string: The ID string to validate
        prefix: Expected prefix (optional). If None, accepts any prefix.

    Returns:
        True if valid, False otherwise

    Example:
        >>> is_valid_hash_id("su-a3f42bc")
        True
        >>> is_valid_hash_id("su-a3f42bc", prefix="su")
        True
        >>> is_valid_hash_id("su-a3f42bc", prefix="issue")
        False
        >>> is_valid_hash_id("SU-001")
        False
    """
    import re

    if prefix:
        pattern = f"^{prefix}-[a-f0-9]{{7}}$"
    else:
        pattern = HASH_ID_PATTERN

    return bool(re.match(pattern, id_string))


# Legacy ID patterns (for backward compatibility during migration)
LEGACY_SEMANTIC_UNIT_PATTERN = r"^SU-\d{3}$"
LEGACY_ISSUE_PATTERN = r"^ISSUE-\d{3}$"
LEGACY_IMPROVEMENT_PATTERN = r"^IMPROVE-\d{3}$"
LEGACY_CODE_ISSUE_PATTERN = r"^CODE-ISSUE-\d{3}$"
LEGACY_CODE_IMPROVEMENT_PATTERN = r"^CODE-IMPROVE-\d{3}$"


def is_legacy_id(id_string: str) -> bool:
    """
    Check if an ID uses the legacy sequential format.

    Args:
        id_string: The ID string to check

    Returns:
        True if it's a legacy format ID, False otherwise

    Example:
        >>> is_legacy_id("SU-001")
        True
        >>> is_legacy_id("su-a3f42")
        False
    """
    import re

    legacy_patterns = [
        LEGACY_SEMANTIC_UNIT_PATTERN,
        LEGACY_ISSUE_PATTERN,
        LEGACY_IMPROVEMENT_PATTERN,
        LEGACY_CODE_ISSUE_PATTERN,
        LEGACY_CODE_IMPROVEMENT_PATTERN,
    ]

    return any(re.match(pattern, id_string) for pattern in legacy_patterns)
