"""
Artifact I/O utilities for ASP platform.

This module provides functions for reading and writing agent artifacts
to the filesystem in both JSON and Markdown formats.

Implements the artifact persistence architecture from:
docs/artifact_persistence_version_control_decision.md

Author: ASP Development Team
Date: November 17, 2025
"""

import json
import logging
from pathlib import Path
from typing import TYPE_CHECKING, Any, Optional

if TYPE_CHECKING:
    from asp.models.code import GeneratedFile

logger = logging.getLogger(__name__)


class ArtifactIOError(Exception):
    """Exception raised for artifact I/O errors."""

    pass


def ensure_artifact_directory(task_id: str, base_path: Optional[str] = None) -> Path:
    """
    Ensure artifact directory exists for a task.

    Creates the directory structure: artifacts/{task_id}/

    Args:
        task_id: Task identifier (e.g., "JWT-AUTH-001")
        base_path: Optional base path (defaults to current directory)

    Returns:
        Path object for the artifact directory

    Raises:
        ArtifactIOError: If directory creation fails
    """
    try:
        if base_path:
            base = Path(base_path)
        else:
            base = Path.cwd()

        artifact_dir = base / "artifacts" / task_id
        artifact_dir.mkdir(parents=True, exist_ok=True)

        logger.debug(f"Ensured artifact directory exists: {artifact_dir}")
        return artifact_dir

    except Exception as e:
        raise ArtifactIOError(f"Failed to create artifact directory: {e}") from e


def write_artifact_json(
    task_id: str,
    artifact_type: str,
    data: Any,
    base_path: Optional[str] = None,
) -> Path:
    """
    Write artifact data as JSON file.

    Creates: artifacts/{task_id}/{artifact_type}.json

    Args:
        task_id: Task identifier (e.g., "JWT-AUTH-001")
        artifact_type: Type of artifact (e.g., "plan", "design", "design_review")
        data: Data to write (Pydantic model or dict)
        base_path: Optional base path (defaults to current directory)

    Returns:
        Path to the created JSON file

    Raises:
        ArtifactIOError: If writing fails

    Example:
        >>> write_artifact_json("JWT-AUTH-001", "plan", project_plan)
        Path("artifacts/JWT-AUTH-001/plan.json")
    """
    try:
        artifact_dir = ensure_artifact_directory(task_id, base_path)
        file_path = artifact_dir / f"{artifact_type}.json"

        # Convert Pydantic model to dict if necessary
        if hasattr(data, "model_dump"):
            # Use mode='json' to properly serialize datetime and other special types
            data_dict = data.model_dump(mode="json")
        elif hasattr(data, "dict"):
            data_dict = data.dict()
        else:
            data_dict = data

        # Write JSON with pretty formatting
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data_dict, f, indent=2, ensure_ascii=False)

        logger.info(f"Wrote artifact JSON: {file_path}")
        return file_path

    except Exception as e:
        raise ArtifactIOError(
            f"Failed to write artifact JSON for {task_id}/{artifact_type}: {e}"
        ) from e


def write_artifact_markdown(
    task_id: str,
    artifact_type: str,
    markdown_content: str,
    base_path: Optional[str] = None,
) -> Path:
    """
    Write artifact data as Markdown file.

    Creates: artifacts/{task_id}/{artifact_type}.md

    Args:
        task_id: Task identifier (e.g., "JWT-AUTH-001")
        artifact_type: Type of artifact (e.g., "plan", "design", "design_review")
        markdown_content: Markdown content to write
        base_path: Optional base path (defaults to current directory)

    Returns:
        Path to the created Markdown file

    Raises:
        ArtifactIOError: If writing fails

    Example:
        >>> write_artifact_markdown("JWT-AUTH-001", "plan", "# Project Plan\\n...")
        Path("artifacts/JWT-AUTH-001/plan.md")
    """
    try:
        artifact_dir = ensure_artifact_directory(task_id, base_path)
        file_path = artifact_dir / f"{artifact_type}.md"

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(markdown_content)

        logger.info(f"Wrote artifact Markdown: {file_path}")
        return file_path

    except Exception as e:
        raise ArtifactIOError(
            f"Failed to write artifact Markdown for {task_id}/{artifact_type}: {e}"
        ) from e


def read_artifact_json(
    task_id: str,
    artifact_type: str,
    base_path: Optional[str] = None,
) -> dict[str, Any]:
    """
    Read artifact data from JSON file.

    Reads: artifacts/{task_id}/{artifact_type}.json

    Args:
        task_id: Task identifier (e.g., "JWT-AUTH-001")
        artifact_type: Type of artifact (e.g., "plan", "design", "design_review")
        base_path: Optional base path (defaults to current directory)

    Returns:
        Dictionary containing artifact data

    Raises:
        ArtifactIOError: If reading fails or file doesn't exist

    Example:
        >>> data = read_artifact_json("JWT-AUTH-001", "plan")
        >>> data["task_id"]
        "JWT-AUTH-001"
    """
    try:
        if base_path:
            base = Path(base_path)
        else:
            base = Path.cwd()

        file_path = base / "artifacts" / task_id / f"{artifact_type}.json"

        if not file_path.exists():
            raise ArtifactIOError(f"Artifact file not found: {file_path}")

        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        logger.debug(f"Read artifact JSON: {file_path}")
        return data

    except json.JSONDecodeError as e:
        raise ArtifactIOError(
            f"Invalid JSON in artifact {task_id}/{artifact_type}: {e}"
        ) from e
    except Exception as e:
        raise ArtifactIOError(
            f"Failed to read artifact JSON for {task_id}/{artifact_type}: {e}"
        ) from e


def read_artifact_markdown(
    task_id: str,
    artifact_type: str,
    base_path: Optional[str] = None,
) -> str:
    """
    Read artifact data from Markdown file.

    Reads: artifacts/{task_id}/{artifact_type}.md

    Args:
        task_id: Task identifier (e.g., "JWT-AUTH-001")
        artifact_type: Type of artifact (e.g., "plan", "design", "design_review")
        base_path: Optional base path (defaults to current directory)

    Returns:
        Markdown content as string

    Raises:
        ArtifactIOError: If reading fails or file doesn't exist

    Example:
        >>> content = read_artifact_markdown("JWT-AUTH-001", "plan")
        >>> "# Project Plan" in content
        True
    """
    try:
        if base_path:
            base = Path(base_path)
        else:
            base = Path.cwd()

        file_path = base / "artifacts" / task_id / f"{artifact_type}.md"

        if not file_path.exists():
            raise ArtifactIOError(f"Artifact file not found: {file_path}")

        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        logger.debug(f"Read artifact Markdown: {file_path}")
        return content

    except Exception as e:
        raise ArtifactIOError(
            f"Failed to read artifact Markdown for {task_id}/{artifact_type}: {e}"
        ) from e


def write_generated_file(
    task_id: str,
    file: "GeneratedFile",
    base_path: Optional[str] = None,
) -> Path:
    """
    Write a generated code file to disk.

    Creates the file at: {base_path}/{file.file_path}
    Automatically creates parent directories if needed.

    Args:
        task_id: Task identifier (for logging purposes, not used in path)
        file: GeneratedFile object with file_path and content attributes
        base_path: Optional base path (defaults to current directory)

    Returns:
        Path to the created file

    Raises:
        ArtifactIOError: If writing fails

    Example:
        >>> from asp.models.code import GeneratedFile
        >>> file = GeneratedFile(file_path="src/api/auth.py", content="...", ...)
        >>> write_generated_file("TASK-001", file)
        Path("src/api/auth.py")
    """
    try:
        if base_path:
            base = Path(base_path)
        else:
            base = Path.cwd()

        full_path = base / file.file_path

        # Create parent directories
        full_path.parent.mkdir(parents=True, exist_ok=True)

        # Write file content
        with open(full_path, "w", encoding="utf-8") as f:
            f.write(file.content)

        logger.debug(f"Wrote generated file for {task_id}: {full_path}")
        return full_path

    except Exception as e:
        raise ArtifactIOError(
            f"Failed to write generated file {file.file_path}: {e}"
        ) from e


def artifact_exists(
    task_id: str,
    artifact_type: str,
    format: str = "json",
    base_path: Optional[str] = None,
) -> bool:
    """
    Check if an artifact file exists.

    Args:
        task_id: Task identifier (e.g., "JWT-AUTH-001")
        artifact_type: Type of artifact (e.g., "plan", "design")
        format: File format ("json" or "md")
        base_path: Optional base path (defaults to current directory)

    Returns:
        True if artifact file exists, False otherwise

    Example:
        >>> artifact_exists("JWT-AUTH-001", "plan", "json")
        True
        >>> artifact_exists("NONEXISTENT", "plan", "json")
        False
    """
    if base_path:
        base = Path(base_path)
    else:
        base = Path.cwd()

    extension = "json" if format == "json" else "md"
    file_path = base / "artifacts" / task_id / f"{artifact_type}.{extension}"

    return file_path.exists()


def list_task_artifacts(
    task_id: str,
    base_path: Optional[str] = None,
) -> list[str]:
    """
    List all artifact files for a task.

    Args:
        task_id: Task identifier (e.g., "JWT-AUTH-001")
        base_path: Optional base path (defaults to current directory)

    Returns:
        List of artifact file names

    Example:
        >>> list_task_artifacts("JWT-AUTH-001")
        ["plan.json", "plan.md", "design.json", "design.md"]
    """
    if base_path:
        base = Path(base_path)
    else:
        base = Path.cwd()

    artifact_dir = base / "artifacts" / task_id

    if not artifact_dir.exists():
        return []

    return sorted([f.name for f in artifact_dir.iterdir() if f.is_file()])
