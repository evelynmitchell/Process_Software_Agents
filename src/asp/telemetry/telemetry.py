"""
Telemetry Infrastructure for ASP Platform

This module provides decorators and utilities for tracking agent costs and defects.
Integrates with both Langfuse (observability) and SQLite (persistent storage).

Features:
- @track_agent_cost: Decorator to track agent execution metrics
- @log_defect: Decorator to log defects with phase tracking
- Database helpers for SQLite operations
- Langfuse integration for real-time observability

Author: ASP Development Team
Date: November 13, 2025
"""

import functools
import os
import sqlite3
import time
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, Optional

from langfuse import Langfuse


# ============================================================================
# Configuration
# ============================================================================

# Database path (relative to project root)
DEFAULT_DB_PATH = Path(__file__).parent.parent.parent.parent / "data" / "asp_telemetry.db"

# Langfuse client (initialized lazily)
_langfuse_client: Optional[Langfuse] = None


def get_langfuse_client() -> Langfuse:
    """Get or initialize the Langfuse client."""
    global _langfuse_client
    if _langfuse_client is None:
        _langfuse_client = Langfuse()
    return _langfuse_client


# ============================================================================
# Database Helpers
# ============================================================================

@contextmanager
def get_db_connection(db_path: Optional[Path] = None):
    """
    Context manager for database connections.

    Args:
        db_path: Path to SQLite database file. Defaults to DEFAULT_DB_PATH.

    Yields:
        sqlite3.Connection: Database connection
    """
    db_path = db_path or DEFAULT_DB_PATH
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row  # Enable column access by name
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def insert_agent_cost(
    task_id: str,
    agent_role: str,
    metric_type: str,
    metric_value: float,
    metric_unit: str,
    subtask_id: Optional[str] = None,
    project_id: Optional[str] = None,
    agent_version: Optional[str] = None,
    agent_iteration: int = 1,
    llm_model: Optional[str] = None,
    llm_provider: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
    db_path: Optional[Path] = None,
) -> int:
    """
    Insert agent cost record into database.

    Args:
        task_id: Unique identifier for the task
        agent_role: Agent role (Planning, Design, Code, etc.)
        metric_type: Type of metric (Latency, Tokens_In, Tokens_Out, API_Cost, etc.)
        metric_value: Numeric value of the metric
        metric_unit: Unit of measurement (ms, tokens, USD, MB, count)
        subtask_id: Optional subtask identifier for decomposed tasks
        project_id: Optional project identifier
        agent_version: Optional agent version string
        agent_iteration: Iteration number for retry loops
        llm_model: LLM model name (e.g., "claude-sonnet-4")
        llm_provider: LLM provider (e.g., "anthropic")
        metadata: Additional metadata as dictionary
        db_path: Optional database path override

    Returns:
        int: ID of inserted record
    """
    import json

    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO agent_cost_vector (
                timestamp, task_id, subtask_id, project_id,
                agent_role, agent_version, agent_iteration,
                metric_type, metric_value, metric_unit,
                llm_model, llm_provider, metadata
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                datetime.utcnow().isoformat(),
                task_id,
                subtask_id,
                project_id,
                agent_role,
                agent_version,
                agent_iteration,
                metric_type,
                metric_value,
                metric_unit,
                llm_model,
                llm_provider,
                json.dumps(metadata) if metadata else None,
            ),
        )
        return cursor.lastrowid


def insert_defect(
    task_id: str,
    defect_type: str,
    severity: str,
    phase_injected: str,
    phase_removed: str,
    description: str,
    project_id: Optional[str] = None,
    component_path: Optional[str] = None,
    function_name: Optional[str] = None,
    line_number: Optional[int] = None,
    root_cause: Optional[str] = None,
    resolution_notes: Optional[str] = None,
    flagged_by_agent: bool = False,
    metadata: Optional[Dict[str, Any]] = None,
    db_path: Optional[Path] = None,
) -> str:
    """
    Insert defect record into database.

    Args:
        task_id: Unique identifier for the task
        defect_type: Type of defect (must match CHECK constraint)
        severity: Severity level (Low, Medium, High, Critical)
        phase_injected: Phase where defect was introduced
        phase_removed: Phase where defect was detected/fixed
        description: Defect description (required)
        project_id: Optional project identifier
        component_path: Path to affected component
        function_name: Name of affected function
        line_number: Line number of defect
        root_cause: Root cause analysis
        resolution_notes: Notes on how it was resolved
        flagged_by_agent: Whether defect was flagged by an agent
        metadata: Additional metadata as dictionary
        db_path: Optional database path override

    Returns:
        str: defect_id of inserted record
    """
    import json
    import uuid

    defect_id = f"DEFECT-{uuid.uuid4().hex[:12].upper()}"

    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO defect_log (
                defect_id, created_at, task_id, project_id,
                defect_type, severity, description,
                phase_injected, phase_removed,
                component_path, function_name, line_number,
                root_cause, resolution_notes,
                flagged_by_agent, metadata
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                defect_id,
                datetime.utcnow().isoformat(),
                task_id,
                project_id,
                defect_type,
                severity,
                description,
                phase_injected,
                phase_removed,
                component_path,
                function_name,
                line_number,
                root_cause,
                resolution_notes,
                1 if flagged_by_agent else 0,
                json.dumps(metadata) if metadata else None,
            ),
        )
        return defect_id


# ============================================================================
# Decorators
# ============================================================================

def track_agent_cost(
    agent_role: str,
    task_id_param: str = "task_id",
    llm_model: Optional[str] = None,
    llm_provider: Optional[str] = None,
    agent_version: Optional[str] = None,
):
    """
    Decorator to track agent execution costs.

    Automatically tracks:
    - Execution latency
    - Token usage (if available)
    - API costs (if available)

    Logs to both Langfuse and SQLite database.

    Args:
        agent_role: Agent role (Planning, Design, Code, etc.)
        task_id_param: Name of the task_id parameter in the function signature
        llm_model: Optional LLM model name
        llm_provider: Optional LLM provider name
        agent_version: Optional agent version

    Example:
        @track_agent_cost(agent_role="Planning", llm_model="claude-sonnet-4")
        def plan_task(task_id: str, description: str) -> dict:
            # Your agent logic here
            return {"decomposed_tasks": [...]}
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Extract task_id from function arguments
            task_id = kwargs.get(task_id_param)
            if task_id is None:
                # Try to find it in positional args based on function signature
                import inspect
                sig = inspect.signature(func)
                param_names = list(sig.parameters.keys())
                if task_id_param in param_names:
                    idx = param_names.index(task_id_param)
                    if idx < len(args):
                        task_id = args[idx]

            if task_id is None:
                raise ValueError(f"task_id not found in function arguments (looking for '{task_id_param}')")

            # Start Langfuse span
            langfuse = get_langfuse_client()
            span = langfuse.start_span(
                name=f"{agent_role}.{func.__name__}",
                metadata={
                    "agent_role": agent_role,
                    "task_id": task_id,
                    "function": func.__name__,
                    "llm_model": llm_model,
                    "llm_provider": llm_provider,
                    "agent_version": agent_version,
                },
            )

            # Track execution time
            start_time = time.time()
            error = None
            result = None

            try:
                # Execute the function
                result = func(*args, **kwargs)
                return result
            except Exception as e:
                error = e
                raise
            finally:
                # Calculate latency
                end_time = time.time()
                latency_ms = (end_time - start_time) * 1000

                # Insert latency metric to database
                try:
                    insert_agent_cost(
                        task_id=task_id,
                        agent_role=agent_role,
                        metric_type="Latency",
                        metric_value=latency_ms,
                        metric_unit="ms",
                        llm_model=llm_model,
                        llm_provider=llm_provider,
                        agent_version=agent_version,
                        metadata={
                            "function": func.__name__,
                            "success": error is None,
                            "error_type": type(error).__name__ if error else None,
                        },
                    )
                except Exception as db_error:
                    # Don't fail the function if telemetry fails
                    print(f"Warning: Failed to log telemetry to database: {db_error}")

                # Update Langfuse span
                try:
                    span.end()
                    langfuse.flush()
                except Exception as lf_error:
                    print(f"Warning: Failed to log to Langfuse: {lf_error}")

        return wrapper
    return decorator


def log_defect(
    defect_type: str,
    severity: str,
    phase_injected: str,
    phase_removed: str,
    task_id_param: str = "task_id",
):
    """
    Decorator to log defects when they are detected and fixed.

    Logs to SQLite database and creates a Langfuse event.

    Args:
        defect_type: Type of defect (must match CHECK constraint in database)
        severity: Severity level (Low, Medium, High, Critical)
        phase_injected: Phase where defect was introduced
        phase_removed: Phase where defect was detected/fixed
        task_id_param: Name of the task_id parameter in the function signature

    Example:
        @log_defect(
            defect_type="6_Conventional_Code_Bug",
            severity="High",
            phase_injected="Implementation",
            phase_removed="Review"
        )
        def fix_logic_error(task_id: str, error_description: str) -> dict:
            # Your fix logic here
            return {"fixed": True}
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Extract task_id from function arguments
            task_id = kwargs.get(task_id_param)
            if task_id is None:
                import inspect
                sig = inspect.signature(func)
                param_names = list(sig.parameters.keys())
                if task_id_param in param_names:
                    idx = param_names.index(task_id_param)
                    if idx < len(args):
                        task_id = args[idx]

            if task_id is None:
                raise ValueError(f"task_id not found in function arguments (looking for '{task_id_param}')")

            # Track fix time
            start_time = time.time()
            error = None
            result = None

            try:
                # Execute the function
                result = func(*args, **kwargs)
                return result
            except Exception as e:
                error = e
                raise
            finally:
                # Calculate fix time
                end_time = time.time()
                fix_time = end_time - start_time

                # Insert defect record to database
                try:
                    insert_defect(
                        task_id=task_id,
                        defect_type=defect_type,
                        severity=severity,
                        phase_injected=phase_injected,
                        phase_removed=phase_removed,
                        description=f"Detected and fixed by {func.__name__}",
                        flagged_by_agent=True,
                        metadata={
                            "function": func.__name__,
                            "fix_time_seconds": fix_time,
                            "success": error is None,
                        },
                    )
                except Exception as db_error:
                    print(f"Warning: Failed to log defect to database: {db_error}")

                # Log to Langfuse
                try:
                    langfuse = get_langfuse_client()
                    langfuse.create_event(
                        name=f"defect.{defect_type}",
                        metadata={
                            "task_id": task_id,
                            "defect_type": defect_type,
                            "severity": severity,
                            "phase_injected": phase_injected,
                            "phase_removed": phase_removed,
                            "fix_time_seconds": fix_time,
                            "function": func.__name__,
                        },
                    )
                    langfuse.flush()
                except Exception as lf_error:
                    print(f"Warning: Failed to log defect to Langfuse: {lf_error}")

        return wrapper
    return decorator


# ============================================================================
# Manual Logging Functions (for non-decorator usage)
# ============================================================================

def log_agent_metric(
    task_id: str,
    agent_role: str,
    metric_type: str,
    metric_value: float,
    metric_unit: str,
    **kwargs,
):
    """
    Manually log an agent metric.

    Use this when you can't use the decorator or need to log additional metrics
    beyond what the decorator captures.

    Args:
        task_id: Task identifier
        agent_role: Agent role
        metric_type: Metric type (Tokens_In, Tokens_Out, API_Cost, etc.)
        metric_value: Metric value
        metric_unit: Unit of measurement
        **kwargs: Additional fields (subtask_id, project_id, llm_model, etc.)
    """
    try:
        insert_agent_cost(
            task_id=task_id,
            agent_role=agent_role,
            metric_type=metric_type,
            metric_value=metric_value,
            metric_unit=metric_unit,
            **kwargs,
        )
    except Exception as e:
        print(f"Warning: Failed to log metric: {e}")


def log_defect_manual(
    task_id: str,
    defect_type: str,
    severity: str,
    phase_injected: str,
    phase_removed: str,
    description: str,
    **kwargs,
):
    """
    Manually log a defect.

    Use this when you can't use the decorator or need more control over defect logging.

    Args:
        task_id: Task identifier
        defect_type: Defect type (must match CHECK constraint)
        severity: Severity level (Low, Medium, High, Critical)
        phase_injected: Phase where defect was introduced
        phase_removed: Phase where defect was detected/fixed
        description: Defect description (required)
        **kwargs: Additional fields (component_path, root_cause, etc.)
    """
    try:
        insert_defect(
            task_id=task_id,
            defect_type=defect_type,
            severity=severity,
            phase_injected=phase_injected,
            phase_removed=phase_removed,
            description=description,
            **kwargs,
        )

        # Also log to Langfuse
        langfuse = get_langfuse_client()
        langfuse.create_event(
            name=f"defect.{defect_type}",
            metadata={
                "task_id": task_id,
                "defect_type": defect_type,
                "severity": severity,
                "phase_injected": phase_injected,
                "phase_removed": phase_removed,
                "description": description,
            },
        )
        langfuse.flush()
    except Exception as e:
        print(f"Warning: Failed to log defect: {e}")
