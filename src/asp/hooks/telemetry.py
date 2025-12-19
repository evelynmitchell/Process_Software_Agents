#!/usr/bin/env python3
"""
Universal telemetry hook for Claude Code.

Captures ALL tool invocations and sends to Logfire or Langfuse based on
ASP_TELEMETRY_PROVIDER environment variable.

Usage in .claude/settings.json:
{
  "hooks": {
    "PreToolUse": [{
      "matcher": "*",
      "hooks": [{"type": "command", "command": "python -m asp.hooks.telemetry pre"}]
    }],
    "PostToolUse": [{
      "matcher": "*",
      "hooks": [{"type": "command", "command": "python -m asp.hooks.telemetry post"}]
    }]
  }
}

Environment Variables:
    ASP_TELEMETRY_PROVIDER: "logfire", "langfuse", or "none" (default: langfuse)
    ASP_TELEMETRY_LOG_DIR: Directory for local logs (default: ~/.claude/telemetry)
    ASP_TELEMETRY_ENABLED: "true" or "false" (default: true)

    # Langfuse
    LANGFUSE_PUBLIC_KEY: Required for Langfuse
    LANGFUSE_SECRET_KEY: Required for Langfuse
    LANGFUSE_HOST: Optional (default: https://cloud.langfuse.com)

    # Logfire
    LOGFIRE_TOKEN: Required for Logfire

Author: ASP Development Team
Date: December 2025
"""

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# Sensitive keys to redact
SENSITIVE_KEYS = frozenset({
    "password",
    "secret",
    "token",
    "api_key",
    "apikey",
    "credential",
    "auth",
    "bearer",
    "private_key",
    "secret_key",
    "access_token",
    "refresh_token",
})

# Maximum lengths for truncation
MAX_INPUT_LENGTH = 10000
MAX_OUTPUT_LENGTH = 5000
MAX_RESPONSE_PREVIEW = 500


def get_log_dir() -> Path:
    """Get the telemetry log directory."""
    log_dir = os.getenv("ASP_TELEMETRY_LOG_DIR")
    if log_dir:
        return Path(log_dir).expanduser()
    return Path.home() / ".claude" / "telemetry"


def is_telemetry_enabled() -> bool:
    """Check if telemetry is enabled."""
    return os.getenv("ASP_TELEMETRY_ENABLED", "true").lower() == "true"


def get_telemetry_provider() -> str:
    """Get the configured telemetry provider."""
    provider = os.getenv("ASP_TELEMETRY_PROVIDER", "langfuse").lower()
    if provider in ("logfire", "langfuse", "none"):
        return provider
    return "langfuse"


def sanitize_value(value: Any, key: str = "") -> Any:
    """
    Sanitize a value, redacting sensitive data.

    Args:
        value: Value to sanitize
        key: Key name (used to detect sensitive fields)

    Returns:
        Sanitized value
    """
    # Check if key indicates sensitive data
    if key and any(s in key.lower() for s in SENSITIVE_KEYS):
        return "[REDACTED]"

    if isinstance(value, str):
        # Truncate very long strings
        if len(value) > MAX_INPUT_LENGTH:
            return value[:MAX_INPUT_LENGTH] + f"... [truncated, {len(value)} chars total]"
        return value

    if isinstance(value, dict):
        return {k: sanitize_value(v, k) for k, v in value.items()}

    if isinstance(value, list):
        return [sanitize_value(item) for item in value[:100]]  # Limit list length

    return value


def categorize_tool(tool_name: str) -> dict[str, str]:
    """
    Categorize a tool by type and extract metadata.

    Args:
        tool_name: Name of the tool

    Returns:
        Dict with tool_type, server (if MCP), and base_tool
    """
    if tool_name.startswith("mcp__"):
        parts = tool_name.split("__")
        return {
            "tool_type": "mcp",
            "mcp_server": parts[1] if len(parts) > 1 else "unknown",
            "mcp_tool": parts[2] if len(parts) > 2 else tool_name,
        }
    elif tool_name == "Task":
        return {"tool_type": "subagent"}
    else:
        return {"tool_type": "builtin"}


def write_local_log(event: dict, session_id: str) -> None:
    """
    Write event to local log file.

    Args:
        event: Event dictionary to log
        session_id: Session ID for log file naming
    """
    try:
        log_dir = get_log_dir()
        log_dir.mkdir(parents=True, exist_ok=True)

        # Use session prefix for log file name
        session_prefix = session_id[:8] if session_id else "unknown"
        log_file = log_dir / f"{session_prefix}.jsonl"

        with open(log_file, "a") as f:
            f.write(json.dumps(event, default=str) + "\n")
    except Exception:
        # Silently ignore local logging errors
        pass


def send_to_langfuse(event: dict, phase: str) -> None:
    """
    Send event to Langfuse.

    Args:
        event: Event dictionary
        phase: "pre" or "post"
    """
    try:
        from langfuse import Langfuse
    except ImportError:
        return

    # Check for required env vars
    if not os.getenv("LANGFUSE_PUBLIC_KEY"):
        return

    try:
        langfuse = Langfuse()

        if phase == "pre":
            langfuse.trace(
                id=event.get("tool_use_id"),
                session_id=event.get("session_id"),
                name=f"tool_{event.get('tool')}",
                input=event,
                metadata={
                    "tool_type": event.get("tool_type"),
                    "tool_name": event.get("tool"),
                },
            )
        else:  # post
            langfuse.trace(
                id=event.get("tool_use_id"),
                output=event,
                metadata={
                    "success": event.get("success", True),
                },
            )

        langfuse.flush()
    except Exception:
        # Don't block on Langfuse errors
        pass


def send_to_logfire(event: dict, phase: str) -> None:
    """
    Send event to Logfire.

    Args:
        event: Event dictionary
        phase: "pre" or "post"
    """
    try:
        import logfire
    except ImportError:
        return

    try:
        tool_name = event.get("tool", "unknown")

        if phase == "pre":
            logfire.info(
                f"Tool started: {tool_name}",
                tool_name=tool_name,
                tool_use_id=event.get("tool_use_id"),
                session_id=event.get("session_id"),
                tool_type=event.get("tool_type"),
                input_preview=str(event.get("input", ""))[:200],
            )
        else:  # post
            success = event.get("success", True)
            log_fn = logfire.info if success else logfire.warn
            log_fn(
                f"Tool completed: {tool_name}",
                tool_name=tool_name,
                tool_use_id=event.get("tool_use_id"),
                session_id=event.get("session_id"),
                success=success,
                response_preview=event.get("response_preview", "")[:200],
            )
    except Exception:
        # Don't block on Logfire errors
        pass


def handle_pre_tool_use(input_data: dict) -> None:
    """
    Handle PreToolUse event - tool is about to execute.

    Args:
        input_data: Event data from Claude Code
    """
    tool_name = input_data.get("tool_name", "unknown")
    tool_use_id = input_data.get("tool_use_id", "")
    session_id = input_data.get("session_id", "")
    tool_input = input_data.get("tool_input", {})

    # Build event
    event = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "event": "tool_start",
        "tool": tool_name,
        "tool_use_id": tool_use_id,
        "session_id": session_id,
        "input": sanitize_value(tool_input),
        **categorize_tool(tool_name),
    }

    # Write to local log
    write_local_log(event, session_id)

    # Send to configured provider
    provider = get_telemetry_provider()
    if provider == "langfuse":
        send_to_langfuse(event, "pre")
    elif provider == "logfire":
        send_to_logfire(event, "pre")


def handle_post_tool_use(input_data: dict) -> None:
    """
    Handle PostToolUse event - tool has completed.

    Args:
        input_data: Event data from Claude Code
    """
    tool_name = input_data.get("tool_name", "unknown")
    tool_use_id = input_data.get("tool_use_id", "")
    session_id = input_data.get("session_id", "")
    tool_response = input_data.get("tool_response", {})

    # Determine success/failure
    is_error = False
    if isinstance(tool_response, dict):
        is_error = tool_response.get("is_error", False)

    # Truncate response for logging
    if isinstance(tool_response, dict):
        response_preview = json.dumps(tool_response, default=str)
    else:
        response_preview = str(tool_response)

    if len(response_preview) > MAX_RESPONSE_PREVIEW:
        response_preview = response_preview[:MAX_RESPONSE_PREVIEW] + "... [truncated]"

    # Build event
    event = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "event": "tool_end",
        "tool": tool_name,
        "tool_use_id": tool_use_id,
        "session_id": session_id,
        "success": not is_error,
        "response_preview": response_preview,
        **categorize_tool(tool_name),
    }

    # Write to local log
    write_local_log(event, session_id)

    # Send to configured provider
    provider = get_telemetry_provider()
    if provider == "langfuse":
        send_to_langfuse(event, "post")
    elif provider == "logfire":
        send_to_logfire(event, "post")


def main():
    """Main entry point for hook."""
    # Check if telemetry is enabled
    if not is_telemetry_enabled():
        sys.exit(0)

    # Get phase from command line
    if len(sys.argv) < 2:
        print("Usage: python -m asp.hooks.telemetry <pre|post>", file=sys.stderr)
        sys.exit(0)  # Exit 0 to not block

    phase = sys.argv[1]

    # Read input from stdin
    try:
        input_data = json.load(sys.stdin)
    except json.JSONDecodeError:
        # No input or invalid JSON - exit silently
        sys.exit(0)
    except Exception:
        # Any other error - exit silently
        sys.exit(0)

    try:
        if phase == "pre":
            handle_pre_tool_use(input_data)
        elif phase == "post":
            handle_post_tool_use(input_data)

        # Exit 0 = success, don't block
        sys.exit(0)

    except Exception as e:
        # Log error but don't block Claude
        print(f"Telemetry error: {e}", file=sys.stderr)
        sys.exit(0)  # Still exit 0 to not block


if __name__ == "__main__":
    main()
