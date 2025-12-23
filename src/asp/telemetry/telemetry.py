"""
Telemetry Infrastructure for ASP Platform

This module provides decorators and utilities for tracking agent costs and defects.
Supports multiple telemetry backends:
- Logfire (Pydantic's observability platform) - recommended
- Langfuse (LLM observability) - legacy support
- SQLite (persistent local storage) - always enabled

Features:
- @track_agent_cost: Decorator to track agent execution metrics (sync & async)
- @log_defect: Decorator to log defects with phase tracking
- Database helpers for SQLite operations
- Dual-backend support via ASP_TELEMETRY_PROVIDER env var

Environment Variables:
- ASP_TELEMETRY_PROVIDER: "logfire" (recommended), "langfuse", or "none"
- ASP_USER_ID: Override user identification

Author: ASP Development Team
Date: November 13, 2025 (updated December 2025)
"""

import asyncio
import functools
import os
import sqlite3
import time
from collections.abc import Callable
from contextlib import contextmanager
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path
from typing import Any

from langfuse import Langfuse

import asp.telemetry.config as telemetry_config

# ============================================================================
# Configuration
# ============================================================================

# Database path (relative to project root)
DEFAULT_DB_PATH = (
    Path(__file__).parent.parent.parent.parent / "data" / "asp_telemetry.db"
)


class DefectType(StrEnum):
    """
    Standard Defect Taxonomy (PSP/TSP PROBE).
    """

    DOCUMENTATION = "10_Documentation"
    SYNTAX = "20_Syntax"
    BUILD_PACKAGE = "30_Build_Package"
    ASSIGNMENT = "40_Assignment"
    INTERFACE = "50_Interface"
    CHECKING = "60_Checking"
    DATA = "70_Data"
    FUNCTION = "80_Function"
    SYSTEM = "90_System"
    ENVIRONMENT = "100_Environment"


# Langfuse client (initialized lazily)
_langfuse_client: Langfuse | None = None

# Telemetry initialization flag
_telemetry_initialized = False


def _ensure_telemetry_initialized() -> None:
    """Ensure telemetry is initialized based on configured provider."""
    global _telemetry_initialized
    if _telemetry_initialized:
        return

    provider = telemetry_config.get_telemetry_provider()
    if provider == "logfire":
        telemetry_config.configure_logfire()
    # Langfuse initializes lazily via get_langfuse_client()

    _telemetry_initialized = True


def get_langfuse_client() -> Langfuse:
    """Get or initialize the Langfuse client."""
    global _langfuse_client
    if _langfuse_client is None:
        _langfuse_client = Langfuse()
    return _langfuse_client


def _get_logfire():
    """
    Get the logfire module (lazy import).

    Returns:
        The logfire module or None if not available
    """
    try:
        import logfire

        return logfire
    except ImportError:
        return None


def get_user_id() -> str:
    """
    Resolve the current user ID for telemetry.

    Resolution order:
    1. ASP_USER_ID environment variable
    2. Git user.email configuration
    3. System user (os.getlogin())
    4. "unknown-user" fallback
    """
    # 1. Environment variable
    env_user = os.getenv("ASP_USER_ID")
    if env_user:
        return env_user

    # 2. Git config
    try:
        import subprocess

        result = subprocess.run(
            ["git", "config", "user.email"],
            capture_output=True,
            text=True,
            timeout=1,
        )
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout.strip()
    except Exception:
        pass

    # 3. System user
    try:
        return os.getlogin()
    except Exception:
        pass

    # 4. Fallback
    return "unknown-user"


# ============================================================================
# Database Helpers
# ============================================================================


@contextmanager
def get_db_connection(db_path: Path | None = None):
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
    subtask_id: str | None = None,
    project_id: str | None = None,
    user_id: str | None = None,
    agent_version: str | None = None,
    agent_iteration: int = 1,
    llm_model: str | None = None,
    llm_provider: str | None = None,
    metadata: dict[str, Any] | None = None,
    db_path: Path | None = None,
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
        user_id: Optional user identifier (person or agent instance)
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

    # Auto-resolve user_id if not provided
    if user_id is None:
        user_id = get_user_id()

    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO agent_cost_vector (
                timestamp, task_id, subtask_id, project_id, user_id,
                agent_role, agent_version, agent_iteration,
                metric_type, metric_value, metric_unit,
                llm_model, llm_provider, metadata
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                datetime.now(UTC).isoformat(),
                task_id,
                subtask_id,
                project_id,
                user_id,
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
    project_id: str | None = None,
    user_id: str | None = None,
    component_path: str | None = None,
    function_name: str | None = None,
    line_number: int | None = None,
    root_cause: str | None = None,
    resolution_notes: str | None = None,
    flagged_by_agent: bool = False,
    metadata: dict[str, Any] | None = None,
    db_path: Path | None = None,
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

    # Auto-resolve user_id if not provided
    if user_id is None:
        user_id = get_user_id()

    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO defect_log (
                defect_id, created_at, task_id, project_id, user_id,
                defect_type, severity, description,
                phase_injected, phase_removed,
                component_path, function_name, line_number,
                root_cause, resolution_notes,
                flagged_by_agent, metadata
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                defect_id,
                datetime.now(UTC).isoformat(),
                task_id,
                project_id,
                user_id,
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


def _extract_task_id(func: Callable, args: tuple, kwargs: dict, task_id_param: str):
    """
    Extract task_id from function arguments.

    Supports:
    - Simple parameter name: "task_id"
    - Dot notation: "input_data.task_id"
    - Object with task_id attribute

    Returns:
        str | None: The extracted task_id or None
    """
    import inspect

    task_id = None

    if "." in task_id_param:
        # Handle dot notation (e.g., "input_data.task_id")
        parts = task_id_param.split(".", 1)
        param_name = parts[0]
        attr_name = parts[1]

        # Try to get the parameter
        param_value = kwargs.get(param_name)
        if param_value is None:
            # Try positional args
            sig = inspect.signature(func)
            param_names = list(sig.parameters.keys())
            if param_name in param_names:
                idx = param_names.index(param_name)
                if idx < len(args):
                    param_value = args[idx]

        # Extract attribute from the parameter object
        if param_value is not None and hasattr(param_value, attr_name):
            task_id = getattr(param_value, attr_name)
    else:
        # Simple parameter name (backwards compatible)
        task_id = kwargs.get(task_id_param)
        if task_id is None:
            # Try to find it in positional args based on function signature
            sig = inspect.signature(func)
            param_names = list(sig.parameters.keys())
            if task_id_param in param_names:
                idx = param_names.index(task_id_param)
                if idx < len(args):
                    param_value = args[idx]
                    # If it's an object with task_id attribute, extract it
                    if hasattr(param_value, "task_id"):
                        task_id = param_value.task_id
                    else:
                        task_id = param_value

    return task_id


def _log_metrics_to_sqlite(
    task_id: str,
    agent_role: str,
    latency_ms: float,
    llm_usage: dict,
    llm_model: str | None,
    llm_provider: str | None,
    user_id: str,
    agent_version: str | None,
    metadata: dict,
) -> None:
    """Log agent metrics to SQLite database."""
    try:
        # Always log latency
        insert_agent_cost(
            task_id=task_id,
            agent_role=agent_role,
            metric_type="Latency",
            metric_value=latency_ms,
            metric_unit="ms",
            llm_model=llm_model,
            llm_provider=llm_provider,
            user_id=user_id,
            agent_version=agent_version,
            metadata=metadata,
        )

        # Log token usage if available
        if llm_usage.get("input_tokens"):
            insert_agent_cost(
                task_id=task_id,
                agent_role=agent_role,
                metric_type="Tokens_In",
                metric_value=llm_usage["input_tokens"],
                metric_unit="tokens",
                llm_model=llm_usage.get("model", llm_model),
                llm_provider=llm_provider,
                user_id=user_id,
                agent_version=agent_version,
                metadata=metadata,
            )

        if llm_usage.get("output_tokens"):
            insert_agent_cost(
                task_id=task_id,
                agent_role=agent_role,
                metric_type="Tokens_Out",
                metric_value=llm_usage["output_tokens"],
                metric_unit="tokens",
                llm_model=llm_usage.get("model", llm_model),
                llm_provider=llm_provider,
                user_id=user_id,
                agent_version=agent_version,
                metadata=metadata,
            )

        if llm_usage.get("cost"):
            insert_agent_cost(
                task_id=task_id,
                agent_role=agent_role,
                metric_type="API_Cost",
                metric_value=llm_usage["cost"],
                metric_unit="USD",
                llm_model=llm_usage.get("model", llm_model),
                llm_provider=llm_provider,
                user_id=user_id,
                agent_version=agent_version,
                metadata=metadata,
            )

    except Exception as db_error:
        # Don't fail the function if telemetry fails
        print(f"Warning: Failed to log telemetry to database: {db_error}")


def _track_with_langfuse(
    func_name: str,
    agent_role: str,
    task_id: str,
    user_id: str,
    llm_model: str | None,
    llm_provider: str | None,
    agent_version: str | None,
    latency_ms: float,
    llm_usage: dict,
    error: Exception | None,
) -> None:
    """Log telemetry to Langfuse."""
    try:
        langfuse = get_langfuse_client()
        span = langfuse.start_span(
            name=f"{agent_role}.{func_name}",
            metadata={
                "agent_role": agent_role,
                "task_id": task_id,
                "user_id": user_id,
                "function": func_name,
                "llm_model": llm_model,
                "llm_provider": llm_provider,
                "agent_version": agent_version,
                "latency_ms": latency_ms,
                "success": error is None,
                "error_type": type(error).__name__ if error else None,
                "tags": [
                    f"user:{user_id}",
                    f"model:{llm_model}" if llm_model else "model:unknown",
                    (
                        f"pair:{user_id}|{llm_model}"
                        if llm_model
                        else f"pair:{user_id}|unknown"
                    ),
                ],
            },
        )
        if llm_usage:
            span.update(
                usage={
                    "input": llm_usage.get("input_tokens", 0),
                    "output": llm_usage.get("output_tokens", 0),
                    "total": llm_usage.get("total_tokens", 0),
                }
            )
        span.end()
        langfuse.flush()
    except Exception as lf_error:
        print(f"Warning: Failed to log to Langfuse: {lf_error}")


def _track_with_logfire(
    func_name: str,
    agent_role: str,
    task_id: str,
    user_id: str,
    llm_model: str | None,
    llm_provider: str | None,
    agent_version: str | None,
    latency_ms: float,
    llm_usage: dict,
    error: Exception | None,
) -> None:
    """Log telemetry to Logfire."""
    logfire = _get_logfire()
    if logfire is None:
        return

    try:
        # Log as a span with all attributes
        with logfire.span(
            f"{agent_role}.{func_name}",
            _tags=[f"agent:{agent_role}", f"user:{user_id}"],
        ) as span:
            span.set_attribute("task_id", task_id)
            span.set_attribute("user_id", user_id)
            span.set_attribute("agent_role", agent_role)
            span.set_attribute("llm_model", llm_model or "unknown")
            span.set_attribute("llm_provider", llm_provider or "unknown")
            span.set_attribute("agent_version", agent_version or "unknown")
            span.set_attribute("latency_ms", latency_ms)
            span.set_attribute("success", error is None)

            if error:
                span.set_attribute("error_type", type(error).__name__)
                span.set_attribute("error_message", str(error))

            if llm_usage:
                span.set_attribute("tokens_in", llm_usage.get("input_tokens", 0))
                span.set_attribute("tokens_out", llm_usage.get("output_tokens", 0))
                span.set_attribute("api_cost_usd", llm_usage.get("cost", 0))

    except Exception as lf_error:
        print(f"Warning: Failed to log to Logfire: {lf_error}")


def track_agent_cost(
    agent_role: str,
    task_id_param: str = "task_id",
    llm_model: str | None = None,
    llm_provider: str | None = None,
    agent_version: str | None = None,
):
    """
    Decorator to track agent execution costs.

    Automatically tracks:
    - Execution latency
    - Token usage (if available)
    - API costs (if available)

    Logs to configured backend (Logfire or Langfuse) and SQLite database.
    Supports both synchronous and asynchronous functions.

    Args:
        agent_role: Agent role (Planning, Design, Code, etc.)
        task_id_param: Name of the task_id parameter in the function signature.
                       Supports dot notation like "input_data.task_id"
        llm_model: Optional LLM model name
        llm_provider: Optional LLM provider name
        agent_version: Optional agent version

    Example:
        @track_agent_cost(agent_role="Planning", llm_model="claude-sonnet-4")
        def plan_task(task_id: str, description: str) -> dict:
            # Your agent logic here
            return {"decomposed_tasks": [...]}

        @track_agent_cost(agent_role="Code", llm_model="claude-sonnet-4")
        async def generate_code(task_id: str, spec: str) -> str:
            # Your async agent logic here
            return "generated code"
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            _ensure_telemetry_initialized()

            task_id = _extract_task_id(func, args, kwargs, task_id_param)
            if task_id is None:
                raise ValueError(
                    f"task_id not found in function arguments (looking for '{task_id_param}')"
                )

            user_id = get_user_id()
            provider = telemetry_config.get_telemetry_provider()
            start_time = time.time()
            error = None

            try:
                result = await func(*args, **kwargs)
                return result
            except Exception as e:
                error = e
                raise
            finally:
                latency_ms = (time.time() - start_time) * 1000

                # Extract LLM usage data if available
                llm_usage = {}
                if args and hasattr(args[0], "_last_llm_usage"):
                    llm_usage = args[0]._last_llm_usage

                metadata = {
                    "function": func.__name__,
                    "success": error is None,
                    "error_type": type(error).__name__ if error else None,
                }

                # Always log to SQLite
                _log_metrics_to_sqlite(
                    task_id=task_id,
                    agent_role=agent_role,
                    latency_ms=latency_ms,
                    llm_usage=llm_usage,
                    llm_model=llm_model,
                    llm_provider=llm_provider,
                    user_id=user_id,
                    agent_version=agent_version,
                    metadata=metadata,
                )

                # Log to configured provider
                if provider == "logfire":
                    _track_with_logfire(
                        func_name=func.__name__,
                        agent_role=agent_role,
                        task_id=task_id,
                        user_id=user_id,
                        llm_model=llm_model,
                        llm_provider=llm_provider,
                        agent_version=agent_version,
                        latency_ms=latency_ms,
                        llm_usage=llm_usage,
                        error=error,
                    )
                elif provider == "langfuse":
                    _track_with_langfuse(
                        func_name=func.__name__,
                        agent_role=agent_role,
                        task_id=task_id,
                        user_id=user_id,
                        llm_model=llm_model,
                        llm_provider=llm_provider,
                        agent_version=agent_version,
                        latency_ms=latency_ms,
                        llm_usage=llm_usage,
                        error=error,
                    )

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            _ensure_telemetry_initialized()

            task_id = _extract_task_id(func, args, kwargs, task_id_param)
            if task_id is None:
                raise ValueError(
                    f"task_id not found in function arguments (looking for '{task_id_param}')"
                )

            user_id = get_user_id()
            provider = telemetry_config.get_telemetry_provider()
            start_time = time.time()
            error = None

            try:
                result = func(*args, **kwargs)
                return result
            except Exception as e:
                error = e
                raise
            finally:
                latency_ms = (time.time() - start_time) * 1000

                # Extract LLM usage data if available
                llm_usage = {}
                if args and hasattr(args[0], "_last_llm_usage"):
                    llm_usage = args[0]._last_llm_usage

                metadata = {
                    "function": func.__name__,
                    "success": error is None,
                    "error_type": type(error).__name__ if error else None,
                }

                # Always log to SQLite
                _log_metrics_to_sqlite(
                    task_id=task_id,
                    agent_role=agent_role,
                    latency_ms=latency_ms,
                    llm_usage=llm_usage,
                    llm_model=llm_model,
                    llm_provider=llm_provider,
                    user_id=user_id,
                    agent_version=agent_version,
                    metadata=metadata,
                )

                # Log to configured provider
                if provider == "logfire":
                    _track_with_logfire(
                        func_name=func.__name__,
                        agent_role=agent_role,
                        task_id=task_id,
                        user_id=user_id,
                        llm_model=llm_model,
                        llm_provider=llm_provider,
                        agent_version=agent_version,
                        latency_ms=latency_ms,
                        llm_usage=llm_usage,
                        error=error,
                    )
                elif provider == "langfuse":
                    _track_with_langfuse(
                        func_name=func.__name__,
                        agent_role=agent_role,
                        task_id=task_id,
                        user_id=user_id,
                        llm_model=llm_model,
                        llm_provider=llm_provider,
                        agent_version=agent_version,
                        latency_ms=latency_ms,
                        llm_usage=llm_usage,
                        error=error,
                    )

        # Return appropriate wrapper based on function type
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

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
                raise ValueError(
                    f"task_id not found in function arguments (looking for '{task_id_param}')"
                )

            # Resolve User
            user_id = get_user_id()

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
                        user_id=user_id,
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
                            "user_id": user_id,
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
