"""
Surgical Editor for precise code modifications.

Provides search-replace based code editing with fuzzy matching support
for the repair workflow. Handles backup/rollback for safe code changes.

Classes:
    - EditResult: Result of applying code changes
    - SurgicalEditor: Apply search-replace changes with fuzzy matching

Part of ADR 006: Repair Workflow Architecture.

Author: ASP Development Team
Date: December 10, 2025
"""

# pylint: disable=logging-fstring-interpolation

from __future__ import annotations

import difflib
import logging
import shutil
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from asp.models.diagnostic import CodeChange

logger = logging.getLogger(__name__)


# =============================================================================
# Result Types
# =============================================================================


@dataclass
class Match:
    """
    Represents a match found in file content.

    Attributes:
        start: Start index in the content
        end: End index in the content
        matched_text: The actual text that was matched
        similarity: Similarity score (1.0 = exact match)
    """

    start: int
    end: int
    matched_text: str
    similarity: float


@dataclass
class EditResult:
    """
    Result of applying code changes.

    Attributes:
        success: Whether all changes were applied successfully
        files_modified: List of files that were modified
        backup_paths: Mapping of original paths to backup paths
        errors: List of error messages for failed changes
        changes_applied: Number of changes successfully applied
        changes_failed: Number of changes that failed
    """

    success: bool
    files_modified: list[str] = field(default_factory=list)
    backup_paths: dict[str, str] = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)
    changes_applied: int = 0
    changes_failed: int = 0


class SurgicalEditorError(Exception):
    """Raised when surgical editing fails."""


# =============================================================================
# Surgical Editor
# =============================================================================


class SurgicalEditor:
    """
    Apply search-replace code changes with fuzzy matching support.

    Uses text-based search and replace (not line numbers) for reliable
    code modifications. Supports fuzzy matching to handle minor whitespace
    or formatting differences.

    Features:
    - Exact and fuzzy text matching
    - Automatic backup before changes
    - Rollback support
    - Diff preview generation
    - Multiple occurrence handling

    Example:
        >>> editor = SurgicalEditor(Path("/workspace"))
        >>> changes = [CodeChange(
        ...     file_path="src/calculator.py",
        ...     search_text="return a - b",
        ...     replace_text="return a + b",
        ... )]
        >>> result = editor.apply_changes(changes)
        >>> if not result.success:
        ...     editor.rollback()
    """

    def __init__(
        self,
        workspace_path: Path,
        backup_dir: str = ".asp/backups",
        fuzzy_threshold: float = 0.8,
    ):
        """
        Initialize the surgical editor.

        Args:
            workspace_path: Root path of the workspace
            backup_dir: Directory for backup files (relative to workspace)
            fuzzy_threshold: Minimum similarity for fuzzy matching (0.0-1.0)
        """
        self.workspace_path = Path(workspace_path)
        self.backup_dir = self.workspace_path / backup_dir
        self.fuzzy_threshold = fuzzy_threshold
        self._backups: dict[str, Path] = {}  # Track active backups

        logger.debug(
            f"SurgicalEditor initialized: workspace={workspace_path}, "
            f"fuzzy_threshold={fuzzy_threshold}"
        )

    def apply_changes(
        self,
        changes: list[CodeChange],
        create_backup: bool = True,
        use_fuzzy: bool = True,
    ) -> EditResult:
        """
        Apply a list of code changes to the workspace.

        Args:
            changes: List of CodeChange objects to apply
            create_backup: Whether to create backups before modifying
            use_fuzzy: Whether to use fuzzy matching if exact match fails

        Returns:
            EditResult with success status and details
        """
        result = EditResult(success=True)

        # Group changes by file for efficiency
        changes_by_file: dict[str, list[CodeChange]] = {}
        for change in changes:
            if change.file_path not in changes_by_file:
                changes_by_file[change.file_path] = []
            changes_by_file[change.file_path].append(change)

        # Apply changes file by file
        for file_path, file_changes in changes_by_file.items():
            try:
                file_result = self._apply_changes_to_file(
                    file_path, file_changes, create_backup, use_fuzzy
                )

                if file_result.success:
                    result.files_modified.append(file_path)
                    result.backup_paths.update(file_result.backup_paths)
                    result.changes_applied += file_result.changes_applied
                else:
                    result.success = False
                    result.errors.extend(file_result.errors)
                    result.changes_failed += file_result.changes_failed

            except Exception as e:
                result.success = False
                result.errors.append(f"Error processing {file_path}: {e}")
                result.changes_failed += len(file_changes)
                logger.error(f"Failed to apply changes to {file_path}: {e}")

        logger.info(
            f"Applied {result.changes_applied} changes to {len(result.files_modified)} files, "
            f"{result.changes_failed} failed"
        )

        return result

    def _apply_changes_to_file(
        self,
        file_path: str,
        changes: list[CodeChange],
        create_backup: bool,
        use_fuzzy: bool,
    ) -> EditResult:
        """
        Apply changes to a single file.

        Args:
            file_path: Path to the file (relative to workspace)
            changes: List of changes for this file
            create_backup: Whether to create a backup
            use_fuzzy: Whether to use fuzzy matching

        Returns:
            EditResult for this file
        """
        result = EditResult(success=True)
        full_path = self.workspace_path / file_path

        if not full_path.exists():
            result.success = False
            result.errors.append(f"File not found: {file_path}")
            result.changes_failed = len(changes)
            return result

        # Read current content
        try:
            content = full_path.read_text()
        except OSError as e:
            result.success = False
            result.errors.append(f"Cannot read {file_path}: {e}")
            result.changes_failed = len(changes)
            return result

        # Create backup if requested
        if create_backup:
            backup_path = self._create_backup(full_path)
            if backup_path:
                result.backup_paths[file_path] = str(backup_path)

        # Apply each change
        modified_content = content
        for change in changes:
            try:
                new_content = self._apply_single_change(
                    modified_content, change, use_fuzzy
                )
                if new_content is None:
                    result.success = False
                    result.errors.append(
                        f"Could not find match for search_text in {file_path}: "
                        f"{change.search_text[:50]}..."
                    )
                    result.changes_failed += 1
                else:
                    modified_content = new_content
                    result.changes_applied += 1

            except Exception as e:
                result.success = False
                result.errors.append(f"Failed to apply change to {file_path}: {e}")
                result.changes_failed += 1

        # Write modified content if any changes succeeded
        if result.changes_applied > 0:
            try:
                full_path.write_text(modified_content)
                logger.debug(f"Wrote {result.changes_applied} changes to {file_path}")
            except OSError as e:
                result.success = False
                result.errors.append(f"Cannot write {file_path}: {e}")

        return result

    def _apply_single_change(
        self,
        content: str,
        change: CodeChange,
        use_fuzzy: bool,
    ) -> str | None:
        """
        Apply a single change to content.

        Args:
            content: Current file content
            change: Change to apply
            use_fuzzy: Whether to use fuzzy matching

        Returns:
            Modified content, or None if match not found
        """
        search_text = change.search_text
        replace_text = change.replace_text
        occurrence = change.occurrence

        # Try exact match first
        if search_text in content:
            return self._replace_occurrence(
                content, search_text, replace_text, occurrence
            )

        # Try fuzzy match if enabled
        if use_fuzzy:
            match = self._fuzzy_find(content, search_text)
            if match:
                logger.debug(
                    f"Using fuzzy match (similarity={match.similarity:.2f}): "
                    f"{match.matched_text[:50]}..."
                )
                return self._replace_occurrence(
                    content, match.matched_text, replace_text, occurrence
                )

        return None

    def _replace_occurrence(
        self,
        content: str,
        search_text: str,
        replace_text: str,
        occurrence: int,
    ) -> str:
        """
        Replace specific occurrence of search_text.

        Args:
            content: File content
            search_text: Text to find
            replace_text: Replacement text
            occurrence: Which occurrence (0=all, 1=first, 2=second, etc.)

        Returns:
            Modified content
        """
        if occurrence == 0:
            # Replace all occurrences
            return content.replace(search_text, replace_text)

        # Replace specific occurrence
        parts = content.split(search_text)
        if len(parts) <= occurrence:
            # Not enough occurrences, replace last one
            occurrence = len(parts) - 1

        if occurrence < 1:
            return content

        # Reconstruct with replacement at specific position
        result_parts = []
        for i, part in enumerate(parts):
            result_parts.append(part)
            if i < len(parts) - 1:
                if i + 1 == occurrence:
                    result_parts.append(replace_text)
                else:
                    result_parts.append(search_text)

        return "".join(result_parts)

    def _fuzzy_find(
        self,
        content: str,
        search_text: str,
    ) -> Match | None:
        """
        Find a fuzzy match for search_text in content.

        Uses difflib's SequenceMatcher with sliding window approach.

        Args:
            content: Content to search in
            search_text: Text to find (approximately)

        Returns:
            Match object if found, None otherwise
        """
        search_len = len(search_text)
        if search_len == 0:
            return None

        # Normalize whitespace for comparison
        normalized_search = self._normalize_whitespace(search_text)

        best_match: Match | None = None
        best_similarity = self.fuzzy_threshold

        # Sliding window with some flexibility in size
        window_sizes = [
            search_len,
            int(search_len * 0.9),
            int(search_len * 1.1),
            int(search_len * 0.8),
            int(search_len * 1.2),
        ]

        for window_size in window_sizes:
            if window_size < 10:
                continue

            for i in range(len(content) - window_size + 1):
                window = content[i : i + window_size]
                normalized_window = self._normalize_whitespace(window)

                similarity = difflib.SequenceMatcher(
                    None, normalized_search, normalized_window
                ).ratio()

                if similarity > best_similarity:
                    best_similarity = similarity
                    best_match = Match(
                        start=i,
                        end=i + window_size,
                        matched_text=window,
                        similarity=similarity,
                    )

                    # Early exit if we find a very good match
                    if similarity > 0.95:
                        return best_match

        return best_match

    def _normalize_whitespace(self, text: str) -> str:
        """
        Normalize whitespace for fuzzy comparison.

        Args:
            text: Text to normalize

        Returns:
            Text with normalized whitespace
        """
        # Replace multiple whitespace with single space
        import re

        return re.sub(r"\s+", " ", text.strip())

    def _create_backup(self, file_path: Path) -> Path | None:
        """
        Create a backup of a file.

        Args:
            file_path: Path to file to backup

        Returns:
            Path to backup file, or None if backup failed
        """
        try:
            # Ensure backup directory exists
            self.backup_dir.mkdir(parents=True, exist_ok=True)

            # Create backup with timestamp
            import time

            timestamp = int(time.time() * 1000)
            relative_path = file_path.relative_to(self.workspace_path)
            backup_name = f"{relative_path.stem}_{timestamp}{relative_path.suffix}"
            backup_path = self.backup_dir / backup_name

            shutil.copy2(file_path, backup_path)
            self._backups[str(file_path)] = backup_path

            logger.debug(f"Created backup: {backup_path}")
            return backup_path

        except Exception as e:
            logger.warning(f"Failed to create backup for {file_path}: {e}")
            return None

    def rollback(self, file_path: str | None = None) -> bool:
        """
        Rollback changes by restoring from backups.

        Args:
            file_path: Specific file to rollback, or None for all files

        Returns:
            True if rollback succeeded
        """
        if file_path:
            # Rollback specific file
            full_path = self.workspace_path / file_path
            backup_path = self._backups.get(str(full_path))

            if backup_path and backup_path.exists():
                try:
                    shutil.copy2(backup_path, full_path)
                    logger.info(f"Rolled back {file_path}")
                    return True
                except Exception as e:
                    logger.error(f"Failed to rollback {file_path}: {e}")
                    return False
            else:
                logger.warning(f"No backup found for {file_path}")
                return False

        # Rollback all files
        success = True
        for original_path, backup_path in self._backups.items():
            if backup_path.exists():
                try:
                    shutil.copy2(backup_path, original_path)
                    logger.info(f"Rolled back {original_path}")
                except Exception as e:
                    logger.error(f"Failed to rollback {original_path}: {e}")
                    success = False

        return success

    def cleanup_backups(self) -> None:
        """Remove all backup files created by this editor."""
        for backup_path in self._backups.values():
            try:
                if backup_path.exists():
                    backup_path.unlink()
            except Exception as e:
                logger.warning(f"Failed to delete backup {backup_path}: {e}")

        self._backups.clear()
        logger.debug("Cleaned up backup files")

    def generate_diff(self, changes: list[CodeChange]) -> str:
        """
        Generate a unified diff preview for changes.

        Does not modify any files - just shows what would change.

        Args:
            changes: List of changes to preview

        Returns:
            Unified diff string
        """
        diff_parts = []

        # Group changes by file
        changes_by_file: dict[str, list[CodeChange]] = {}
        for change in changes:
            if change.file_path not in changes_by_file:
                changes_by_file[change.file_path] = []
            changes_by_file[change.file_path].append(change)

        for file_path, file_changes in changes_by_file.items():
            full_path = self.workspace_path / file_path

            if not full_path.exists():
                diff_parts.append(f"--- {file_path} (file not found)\n")
                continue

            try:
                original = full_path.read_text()
                modified = original

                for change in file_changes:
                    if change.search_text in modified:
                        modified = self._replace_occurrence(
                            modified,
                            change.search_text,
                            change.replace_text,
                            change.occurrence,
                        )

                # Generate unified diff
                original_lines = original.splitlines(keepends=True)
                modified_lines = modified.splitlines(keepends=True)

                diff = difflib.unified_diff(
                    original_lines,
                    modified_lines,
                    fromfile=f"a/{file_path}",
                    tofile=f"b/{file_path}",
                )
                diff_parts.append("".join(diff))

            except Exception as e:
                diff_parts.append(f"--- {file_path} (error: {e})\n")

        return "\n".join(diff_parts)

    def verify_changes_applicable(
        self,
        changes: list[CodeChange],
        use_fuzzy: bool = True,
    ) -> tuple[bool, list[str]]:
        """
        Verify that all changes can be applied without actually applying them.

        Args:
            changes: List of changes to verify
            use_fuzzy: Whether to use fuzzy matching

        Returns:
            Tuple of (all_applicable, list of error messages)
        """
        errors = []

        for change in changes:
            full_path = self.workspace_path / change.file_path

            if not full_path.exists():
                errors.append(f"File not found: {change.file_path}")
                continue

            try:
                content = full_path.read_text()

                # Check if search_text can be found
                if change.search_text in content:
                    continue

                if use_fuzzy:
                    match = self._fuzzy_find(content, change.search_text)
                    if match:
                        continue

                errors.append(
                    f"Cannot find search_text in {change.file_path}: "
                    f"{change.search_text[:50]}..."
                )

            except Exception as e:
                errors.append(f"Error reading {change.file_path}: {e}")

        return len(errors) == 0, errors
