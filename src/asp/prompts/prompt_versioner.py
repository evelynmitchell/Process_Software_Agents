"""
Prompt Versioning System

This module manages prompt versions and applies approved Process Improvement
Proposals (PIPs) to prompts.

The prompt versioning workflow:
1. Load approved PIP
2. Identify target prompt files
3. Apply changes (add/modify/remove content)
4. Increment version number
5. Save new prompt version
6. Commit to git with PIP reference

This enables the self-improvement loop:
- Defects found in postmortem → PIPs created → PIPs approved → Prompts updated
- Next iteration uses improved prompts → Fewer defects

Author: ASP Development Team
Date: November 25, 2025
"""

import logging
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from asp.models.postmortem import ProcessImprovementProposal, ProposedChange
from asp.utils.git_utils import git_commit_artifact, is_git_repository


logger = logging.getLogger(__name__)


class PromptVersioner:
    """
    Manages prompt versions and applies PIP changes.

    The versioner:
    - Identifies current prompt versions (e.g., code_agent_v1_generation.txt)
    - Applies approved changes from PIPs
    - Creates new versions (e.g., code_agent_v2_generation.txt)
    - Tracks version history
    - Commits changes to git

    Example:
        >>> from asp.approval.pip_review_service import PIPReviewService
        >>> from asp.prompts.prompt_versioner import PromptVersioner
        >>>
        >>> # Review and approve PIP
        >>> service = PIPReviewService()
        >>> pip = service.review_pip_by_id("POSTMORTEM-001")
        >>>
        >>> # Apply changes if approved
        >>> if pip.hitl_status == "approved":
        >>>     versioner = PromptVersioner()
        >>>     results = versioner.apply_pip(pip)
        >>>     print(f"Updated {len(results)} prompts")
    """

    def __init__(self, prompts_dir: Path = Path("src/asp/prompts")):
        """
        Initialize PromptVersioner.

        Args:
            prompts_dir: Directory containing prompt files
        """
        self.prompts_dir = prompts_dir
        if not self.prompts_dir.exists():
            raise ValueError(f"Prompts directory not found: {self.prompts_dir}")

        self.version_history_file = self.prompts_dir / "VERSION_HISTORY.md"
        logger.info(f"PromptVersioner initialized: {self.prompts_dir}")

    def apply_pip(
        self,
        pip: ProcessImprovementProposal,
        dry_run: bool = False,
    ) -> Dict[str, str]:
        """
        Apply approved PIP changes to prompts.

        Args:
            pip: Approved ProcessImprovementProposal
            dry_run: If True, validate but don't write changes

        Returns:
            Dict mapping artifact names to new file paths

        Raises:
            ValueError: If PIP is not approved or changes are invalid
        """
        if pip.hitl_status != "approved":
            raise ValueError(
                f"Cannot apply non-approved PIP: {pip.proposal_id} (status: {pip.hitl_status})"
            )

        logger.info(
            f"Applying PIP {pip.proposal_id} to prompts "
            f"({'DRY RUN' if dry_run else 'LIVE'})"
        )

        results = {}

        for change in pip.proposed_changes:
            try:
                new_file_path = self._apply_change(change, pip, dry_run=dry_run)
                results[change.target_artifact] = str(new_file_path)
                logger.info(
                    f"Applied change to {change.target_artifact}: {new_file_path}"
                )
            except Exception as e:
                logger.error(
                    f"Failed to apply change to {change.target_artifact}: {e}",
                    exc_info=True
                )
                # Continue with other changes rather than failing completely
                results[change.target_artifact] = f"ERROR: {e}"

        # Update version history
        if not dry_run and results:
            self._update_version_history(pip, results)

            # Git commit if in repository
            if is_git_repository():
                changed_files = [
                    path for path in results.values() if not path.startswith("ERROR:")
                ]
                changed_files.append(str(self.version_history_file))

                git_commit_artifact(
                    task_id=pip.task_id,
                    artifact_type="prompt_update",
                    file_paths=changed_files,
                    message=f"Apply PIP-{pip.proposal_id}: {pip.analysis[:50]}...",
                )

        logger.info(
            f"PIP {pip.proposal_id} applied: {len(results)} prompts updated"
        )
        return results

    def _apply_change(
        self,
        change: ProposedChange,
        pip: ProcessImprovementProposal,
        dry_run: bool = False,
    ) -> Path:
        """
        Apply a single ProposedChange to a prompt file.

        Args:
            change: ProposedChange to apply
            pip: Parent PIP (for metadata)
            dry_run: If True, validate but don't write

        Returns:
            Path to new prompt file

        Raises:
            FileNotFoundError: If prompt file not found
            ValueError: If change cannot be applied
        """
        # Find current prompt file
        current_file, current_version = self._find_prompt_file(change.target_artifact)

        # Read current content
        current_content = current_file.read_text()

        # Apply change based on type
        if change.change_type == "add":
            new_content = self._apply_add(current_content, change)
        elif change.change_type == "modify":
            new_content = self._apply_modify(current_content, change)
        elif change.change_type == "remove":
            new_content = self._apply_remove(current_content, change)
        else:
            raise ValueError(f"Unknown change type: {change.change_type}")

        # Generate new version file name
        new_version = current_version + 1
        new_file = self._generate_new_filename(current_file, new_version)

        # Add PIP metadata to new content
        metadata_header = self._generate_metadata_header(pip, change, new_version)
        new_content = metadata_header + "\n\n" + new_content

        # Write new file (unless dry run)
        if not dry_run:
            new_file.write_text(new_content)
            logger.info(f"Wrote new prompt version: {new_file}")

        return new_file

    def _find_prompt_file(self, artifact_name: str) -> Tuple[Path, int]:
        """
        Find the latest version of a prompt file.

        Args:
            artifact_name: Artifact name (e.g., "code_agent_prompt", "code_review_checklist")

        Returns:
            Tuple of (file_path, version_number)

        Raises:
            FileNotFoundError: If no matching prompt file found
        """
        # Normalize artifact name to match file patterns
        # Examples:
        # "code_agent_prompt" → "code_agent_*.txt"
        # "code_review_checklist" → "code_review_*.txt"

        # Remove common suffixes
        search_name = artifact_name.replace("_prompt", "").replace("_checklist", "")

        # Find all matching files
        pattern = f"{search_name}_v*.txt"
        matching_files = list(self.prompts_dir.glob(pattern))

        if not matching_files:
            # Try alternate pattern (e.g., "code_agent_v1_generation.txt")
            pattern = f"{search_name}_v*_*.txt"
            matching_files = list(self.prompts_dir.glob(pattern))

        if not matching_files:
            raise FileNotFoundError(
                f"No prompt file found for artifact: {artifact_name} "
                f"(searched for: {pattern} in {self.prompts_dir})"
            )

        # Extract version numbers and find latest
        latest_file = None
        latest_version = 0

        for file_path in matching_files:
            # Extract version number (e.g., "code_agent_v2_generation.txt" → 2)
            match = re.search(r'_v(\d+)', file_path.name)
            if match:
                version = int(match.group(1))
                if version > latest_version:
                    latest_version = version
                    latest_file = file_path

        if latest_file is None:
            raise FileNotFoundError(
                f"Could not determine latest version for: {artifact_name}"
            )

        logger.debug(f"Found prompt file: {latest_file} (version {latest_version})")
        return latest_file, latest_version

    def _apply_add(self, current_content: str, change: ProposedChange) -> str:
        """
        Apply ADD change: Append content to prompt.

        Args:
            current_content: Current prompt content
            change: ProposedChange with content to add

        Returns:
            Updated content
        """
        # Add new content at the end with a separator
        separator = "\n\n# --- PIP Addition ---\n\n"
        return current_content + separator + change.proposed_content

    def _apply_modify(self, current_content: str, change: ProposedChange) -> str:
        """
        Apply MODIFY change: Replace specific content in prompt.

        Args:
            current_content: Current prompt content
            change: ProposedChange with current and proposed content

        Returns:
            Updated content

        Raises:
            ValueError: If current_content not found in prompt
        """
        if not change.current_content:
            raise ValueError("MODIFY change requires current_content field")

        if change.current_content not in current_content:
            raise ValueError(
                f"Current content not found in prompt: '{change.current_content[:50]}...'"
            )

        # Replace current content with proposed content
        new_content = current_content.replace(
            change.current_content,
            change.proposed_content
        )

        return new_content

    def _apply_remove(self, current_content: str, change: ProposedChange) -> str:
        """
        Apply REMOVE change: Delete content from prompt.

        Args:
            current_content: Current prompt content
            change: ProposedChange with content to remove

        Returns:
            Updated content

        Raises:
            ValueError: If content not found in prompt
        """
        if not change.current_content:
            # If no current_content specified, try to remove proposed_content
            content_to_remove = change.proposed_content
        else:
            content_to_remove = change.current_content

        if content_to_remove not in current_content:
            raise ValueError(
                f"Content to remove not found in prompt: '{content_to_remove[:50]}...'"
            )

        # Remove content
        new_content = current_content.replace(content_to_remove, "")

        # Clean up extra whitespace
        new_content = re.sub(r'\n\n\n+', '\n\n', new_content)

        return new_content

    def _generate_new_filename(self, current_file: Path, new_version: int) -> Path:
        """
        Generate filename for new version.

        Args:
            current_file: Current file path
            new_version: New version number

        Returns:
            New file path
        """
        # Replace version number in filename
        # Example: "code_agent_v1_generation.txt" → "code_agent_v2_generation.txt"
        new_name = re.sub(
            r'_v\d+',
            f'_v{new_version}',
            current_file.name
        )

        return current_file.parent / new_name

    def _generate_metadata_header(
        self,
        pip: ProcessImprovementProposal,
        change: ProposedChange,
        version: int,
    ) -> str:
        """
        Generate metadata header for new prompt version.

        Args:
            pip: ProcessImprovementProposal that triggered this change
            change: Specific ProposedChange being applied
            version: New version number

        Returns:
            Metadata header text
        """
        header = f"""# Prompt Version: v{version}
# Last Updated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")}
# Updated By: PIP-{pip.proposal_id} (Task: {pip.task_id})
# Change Type: {change.change_type.upper()}
# Rationale: {change.rationale}
# Reviewer: {pip.hitl_reviewer}
# Reviewed At: {pip.hitl_reviewed_at}
"""
        return header

    def _update_version_history(
        self,
        pip: ProcessImprovementProposal,
        results: Dict[str, str],
    ) -> None:
        """
        Update VERSION_HISTORY.md with PIP application record.

        Args:
            pip: Applied ProcessImprovementProposal
            results: Dict of artifact names to new file paths
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")

        entry = f"""
## PIP-{pip.proposal_id} - {timestamp}

**Task:** {pip.task_id}
**Reviewer:** {pip.hitl_reviewer}
**Reviewed:** {pip.hitl_reviewed_at}

**Analysis:** {pip.analysis}

**Expected Impact:** {pip.expected_impact}

**Changes Applied:**
"""

        for artifact, file_path in results.items():
            if file_path.startswith("ERROR:"):
                entry += f"- ❌ {artifact}: {file_path}\n"
            else:
                entry += f"- ✅ {artifact}: `{file_path}`\n"

        entry += "\n---\n"

        # Prepend to version history (most recent first)
        if self.version_history_file.exists():
            existing_content = self.version_history_file.read_text()
            new_content = entry + "\n" + existing_content
        else:
            header = """# Prompt Version History

This file tracks all prompt updates applied via Process Improvement Proposals (PIPs).

---
"""
            new_content = header + entry

        self.version_history_file.write_text(new_content)
        logger.info(f"Updated version history: {self.version_history_file}")
