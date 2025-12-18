# ADR 012: MCP Server for ASP Agents + Universal Telemetry Hooks

**Status:** Draft
**Date:** 2025-12-18
**Session:** 20251218.2
**Deciders:** User, Claude
**Related:** ADR 010 (Multi-LLM Provider), ADR 011 (Claude CLI/Agent SDK Integration)

## Context and Problem Statement

Users want to leverage ASP's specialized agents (PlanningAgent, CodeReviewAgent, RepairAgent) **directly from Claude Code CLI** while maintaining **full observability** of all tool executions. This requires:

1. **Exposing ASP agents as callable tools** - So Claude CLI can invoke them
2. **Capturing telemetry on ALL tool calls** - Built-in tools, MCP tools, subagents
3. **Integrating with existing observability stack** - Langfuse, OpenTelemetry

### Why Not Skills?

Claude Code **Skills** are model-invoked instruction documents, not executable code:
- No control flow (loops, branching)
- No guaranteed execution order
- Model decides when/if to use them

Skills are unsuitable for complex agent logic like ASP's multi-step workflows.

### Why MCP + Hooks?

| Approach | Executable? | Telemetry? | Control? |
|----------|-------------|------------|----------|
| Skills | No (instructions only) | No | Model-controlled |
| **MCP Servers** | **Yes** | Via hooks | **User-controlled** |
| Subprocesses | Yes | Manual | User-controlled |

**MCP (Model Context Protocol)** servers expose tools that Claude can call with full input/output capture via hooks.

## Decision Drivers

1. **Reusability** - Use existing ASP agents without rewriting
2. **Observability** - Capture every tool call for debugging/analysis
3. **Integration** - Work with Langfuse (current) and OpenTelemetry (future)
4. **Non-Blocking** - Telemetry must not slow down Claude operations
5. **Configurability** - Enable/disable telemetry per environment
6. **Security** - Don't leak sensitive data in telemetry

## Proposed Architecture

### Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          Claude Code Session                                 │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────────┐│
│  │                         Hook Layer (Telemetry)                          ││
│  │  PreToolUse ─────────────────────────────────────────► Langfuse         ││
│  │  PostToolUse ────────────────────────────────────────► Langfuse         ││
│  │                                                                          ││
│  │  Captures: ALL tools (matcher: "*")                                     ││
│  │  - Built-in: Bash, Edit, Read, Write, Glob, Grep, WebFetch              ││
│  │  - MCP: mcp__asp__*, mcp__memory__*, mcp__github__*                     ││
│  │  - Subagents: Task tool invocations                                     ││
│  └─────────────────────────────────────────────────────────────────────────┘│
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────────┐│
│  │                         MCP Server Layer                                 ││
│  │                                                                          ││
│  │  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐          ││
│  │  │ asp-agents      │  │ memory          │  │ github          │          ││
│  │  │ (ASP Platform)  │  │ (built-in)      │  │ (built-in)      │          ││
│  │  │                 │  │                 │  │                 │          ││
│  │  │ • asp_plan      │  │ • create_entity │  │ • search_repos  │          ││
│  │  │ • asp_review    │  │ • query         │  │ • create_pr     │          ││
│  │  │ • asp_repair    │  │ • delete        │  │ • list_issues   │          ││
│  │  │ • asp_test      │  │                 │  │                 │          ││
│  │  └─────────────────┘  └─────────────────┘  └─────────────────┘          ││
│  └─────────────────────────────────────────────────────────────────────────┘│
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
                            ┌───────────────────┐
                            │     Langfuse      │
                            │                   │
                            │ • Traces          │
                            │ • Spans           │
                            │ • Token costs     │
                            │ • Latency metrics │
                            └───────────────────┘
```

### Component 1: ASP MCP Server

**File:** `src/asp/mcp/server.py`

```python
"""
ASP Agents MCP Server.

Exposes ASP agents as MCP tools for Claude Code CLI.
"""

import asyncio
import json
from typing import Any
from mcp import Server, Tool, TextContent
from mcp.server.stdio import stdio_server

from asp.agents.planning_agent import PlanningAgent
from asp.agents.code_agent import CodeAgent
from asp.agents.review_agent import ReviewAgent
from asp.agents.repair_agent import RepairAgent
from asp.agents.test_agent import TestAgent
from asp.models.planning import TaskRequirements

# Create MCP server
server = Server("asp-agents")


@server.list_tools()
async def list_tools() -> list[Tool]:
    """List available ASP agent tools."""
    return [
        Tool(
            name="asp_plan",
            description=(
                "Generate a comprehensive project plan using ASP's PlanningAgent. "
                "Use when you need to break down a complex task into actionable steps "
                "with file modifications, dependencies, and validation criteria."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "task_id": {
                        "type": "string",
                        "description": "Unique identifier for this task (e.g., TASK-001)",
                    },
                    "description": {
                        "type": "string",
                        "description": "Brief description of the task",
                    },
                    "requirements": {
                        "type": "string",
                        "description": "Detailed requirements and acceptance criteria",
                    },
                    "workspace_path": {
                        "type": "string",
                        "description": "Path to the workspace/repository",
                        "default": ".",
                    },
                },
                "required": ["task_id", "description", "requirements"],
            },
        ),
        Tool(
            name="asp_code_review",
            description=(
                "Review code changes using ASP's ReviewAgent. "
                "Analyzes code for bugs, security issues, performance problems, "
                "and style violations. Returns structured feedback."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "Path to the file to review",
                    },
                    "diff": {
                        "type": "string",
                        "description": "Git diff of changes (optional, reviews full file if not provided)",
                    },
                    "context": {
                        "type": "string",
                        "description": "Additional context about the changes",
                    },
                },
                "required": ["file_path"],
            },
        ),
        Tool(
            name="asp_repair",
            description=(
                "Automatically repair failing code using ASP's RepairAgent. "
                "Analyzes test failures or errors and generates fixes. "
                "Use when tests are failing or code has bugs."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "error_message": {
                        "type": "string",
                        "description": "The error message or test failure output",
                    },
                    "file_path": {
                        "type": "string",
                        "description": "Path to the file with the error",
                    },
                    "test_command": {
                        "type": "string",
                        "description": "Command to run tests (e.g., 'pytest tests/')",
                    },
                },
                "required": ["error_message"],
            },
        ),
        Tool(
            name="asp_test",
            description=(
                "Run tests and analyze results using ASP's TestAgent. "
                "Executes test suite and provides structured analysis of failures."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "test_command": {
                        "type": "string",
                        "description": "Command to run tests",
                        "default": "pytest",
                    },
                    "test_path": {
                        "type": "string",
                        "description": "Path to tests (file or directory)",
                        "default": "tests/",
                    },
                    "verbose": {
                        "type": "boolean",
                        "description": "Include verbose output",
                        "default": False,
                    },
                },
            },
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
    """Execute an ASP agent tool."""

    if name == "asp_plan":
        return await _handle_plan(arguments)
    elif name == "asp_code_review":
        return await _handle_review(arguments)
    elif name == "asp_repair":
        return await _handle_repair(arguments)
    elif name == "asp_test":
        return await _handle_test(arguments)
    else:
        return [TextContent(type="text", text=f"Unknown tool: {name}")]


async def _handle_plan(args: dict) -> list[TextContent]:
    """Handle asp_plan tool call."""
    agent = PlanningAgent()

    requirements = TaskRequirements(
        task_id=args["task_id"],
        description=args["description"],
        requirements=args.get("requirements", ""),
    )

    result = await agent.execute_async(requirements)

    return [TextContent(
        type="text",
        text=json.dumps(result.model_dump(), indent=2),
    )]


async def _handle_review(args: dict) -> list[TextContent]:
    """Handle asp_code_review tool call."""
    agent = ReviewAgent()

    # Read file content if no diff provided
    file_path = args["file_path"]
    diff = args.get("diff")

    if not diff:
        with open(file_path) as f:
            content = f.read()
        review_input = {"file_path": file_path, "content": content}
    else:
        review_input = {"file_path": file_path, "diff": diff}

    if args.get("context"):
        review_input["context"] = args["context"]

    result = await agent.execute_async(review_input)

    return [TextContent(
        type="text",
        text=json.dumps(result.model_dump(), indent=2),
    )]


async def _handle_repair(args: dict) -> list[TextContent]:
    """Handle asp_repair tool call."""
    agent = RepairAgent()

    repair_input = {
        "error_message": args["error_message"],
        "file_path": args.get("file_path"),
        "test_command": args.get("test_command", "pytest"),
    }

    result = await agent.execute_async(repair_input)

    return [TextContent(
        type="text",
        text=json.dumps(result.model_dump(), indent=2),
    )]


async def _handle_test(args: dict) -> list[TextContent]:
    """Handle asp_test tool call."""
    agent = TestAgent()

    test_input = {
        "command": args.get("test_command", "pytest"),
        "path": args.get("test_path", "tests/"),
        "verbose": args.get("verbose", False),
    }

    result = await agent.execute_async(test_input)

    return [TextContent(
        type="text",
        text=json.dumps(result.model_dump(), indent=2),
    )]


async def main():
    """Run the MCP server."""
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream)


if __name__ == "__main__":
    asyncio.run(main())
```

### Component 2: Universal Telemetry Hooks

**File:** `src/asp/hooks/telemetry.py`

```python
#!/usr/bin/env python3
"""
Universal telemetry hook for Claude Code.

Captures ALL tool invocations and sends to Langfuse.

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
"""

import json
import os
import sys
from datetime import datetime, timezone
from typing import Any

# Optional: Use Langfuse if available
try:
    from langfuse import Langfuse
    LANGFUSE_AVAILABLE = True
except ImportError:
    LANGFUSE_AVAILABLE = False


def get_langfuse_client() -> "Langfuse | None":
    """Get Langfuse client if configured."""
    if not LANGFUSE_AVAILABLE:
        return None

    # Check for required env vars
    if not os.getenv("LANGFUSE_PUBLIC_KEY"):
        return None

    return Langfuse()


def sanitize_input(tool_input: dict) -> dict:
    """Remove sensitive data from tool input before logging."""
    sensitive_keys = {"password", "secret", "token", "api_key", "credential"}
    sanitized = {}

    for key, value in tool_input.items():
        if any(s in key.lower() for s in sensitive_keys):
            sanitized[key] = "[REDACTED]"
        elif isinstance(value, str) and len(value) > 10000:
            # Truncate very long values
            sanitized[key] = value[:1000] + f"... [truncated, {len(value)} chars total]"
        else:
            sanitized[key] = value

    return sanitized


def handle_pre_tool_use(input_data: dict) -> None:
    """Handle PreToolUse event - tool is about to execute."""
    tool_name = input_data.get("tool_name", "unknown")
    tool_use_id = input_data.get("tool_use_id", "")
    session_id = input_data.get("session_id", "")
    tool_input = input_data.get("tool_input", {})

    event = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "event": "tool_start",
        "tool": tool_name,
        "tool_use_id": tool_use_id,
        "session_id": session_id,
        "input": sanitize_input(tool_input),
    }

    # Categorize tool type
    if tool_name.startswith("mcp__"):
        parts = tool_name.split("__")
        event["tool_type"] = "mcp"
        event["mcp_server"] = parts[1] if len(parts) > 1 else "unknown"
        event["mcp_tool"] = parts[2] if len(parts) > 2 else tool_name
    elif tool_name == "Task":
        event["tool_type"] = "subagent"
    else:
        event["tool_type"] = "builtin"

    # Send to Langfuse
    langfuse = get_langfuse_client()
    if langfuse:
        langfuse.trace(
            id=tool_use_id,
            session_id=session_id,
            name=f"tool_{tool_name}",
            input=event,
            metadata={
                "tool_type": event["tool_type"],
                "tool_name": tool_name,
            },
        )

    # Also log locally for debugging
    log_dir = os.path.expanduser("~/.claude/telemetry")
    os.makedirs(log_dir, exist_ok=True)

    log_file = os.path.join(log_dir, f"{session_id[:8]}.jsonl")
    with open(log_file, "a") as f:
        f.write(json.dumps(event) + "\n")


def handle_post_tool_use(input_data: dict) -> None:
    """Handle PostToolUse event - tool has completed."""
    tool_name = input_data.get("tool_name", "unknown")
    tool_use_id = input_data.get("tool_use_id", "")
    session_id = input_data.get("session_id", "")
    tool_response = input_data.get("tool_response", {})

    # Determine success/failure
    is_error = False
    if isinstance(tool_response, dict):
        is_error = tool_response.get("is_error", False)

    event = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "event": "tool_end",
        "tool": tool_name,
        "tool_use_id": tool_use_id,
        "session_id": session_id,
        "success": not is_error,
        "response_preview": _truncate_response(tool_response),
    }

    # Send to Langfuse
    langfuse = get_langfuse_client()
    if langfuse:
        # Update the existing trace
        langfuse.trace(
            id=tool_use_id,
            output=event,
            metadata={
                "success": not is_error,
            },
        )

    # Log locally
    log_dir = os.path.expanduser("~/.claude/telemetry")
    log_file = os.path.join(log_dir, f"{session_id[:8]}.jsonl")
    with open(log_file, "a") as f:
        f.write(json.dumps(event) + "\n")


def _truncate_response(response: Any, max_length: int = 500) -> str:
    """Truncate response for logging."""
    if isinstance(response, dict):
        text = json.dumps(response)
    else:
        text = str(response)

    if len(text) > max_length:
        return text[:max_length] + f"... [truncated]"
    return text


def main():
    """Main entry point for hook."""
    if len(sys.argv) < 2:
        print("Usage: python -m asp.hooks.telemetry <pre|post>", file=sys.stderr)
        sys.exit(1)

    phase = sys.argv[1]

    try:
        input_data = json.load(sys.stdin)
    except json.JSONDecodeError:
        # No input or invalid JSON - exit silently
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
```

### Component 3: Hook Configuration

**File:** `.claude/settings.json` (project-level)

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "*",
        "hooks": [
          {
            "type": "command",
            "command": "python -m asp.hooks.telemetry pre"
          }
        ]
      }
    ],
    "PostToolUse": [
      {
        "matcher": "*",
        "hooks": [
          {
            "type": "command",
            "command": "python -m asp.hooks.telemetry post"
          }
        ]
      }
    ]
  }
}
```

### Component 4: MCP Server Configuration

**File:** `.mcp.json` (project-level)

```json
{
  "mcpServers": {
    "asp-agents": {
      "command": "python",
      "args": ["-m", "asp.mcp.server"],
      "env": {
        "ANTHROPIC_API_KEY": "${ANTHROPIC_API_KEY}",
        "LANGFUSE_PUBLIC_KEY": "${LANGFUSE_PUBLIC_KEY}",
        "LANGFUSE_SECRET_KEY": "${LANGFUSE_SECRET_KEY}"
      }
    }
  }
}
```

## Telemetry Data Flow

### PreToolUse Event

```json
{
  "timestamp": "2025-12-18T16:30:00.000Z",
  "event": "tool_start",
  "tool": "mcp__asp-agents__asp_plan",
  "tool_type": "mcp",
  "mcp_server": "asp-agents",
  "mcp_tool": "asp_plan",
  "tool_use_id": "toolu_01ABC123",
  "session_id": "sess_XYZ789",
  "input": {
    "task_id": "TASK-042",
    "description": "Add user authentication",
    "requirements": "JWT tokens, refresh flow, logout"
  }
}
```

### PostToolUse Event

```json
{
  "timestamp": "2025-12-18T16:30:05.000Z",
  "event": "tool_end",
  "tool": "mcp__asp-agents__asp_plan",
  "tool_use_id": "toolu_01ABC123",
  "session_id": "sess_XYZ789",
  "success": true,
  "response_preview": "{\"plan\": {\"steps\": [...], \"files\": [...]}}..."
}
```

### Langfuse Trace Structure

```
Session: sess_XYZ789
├── Trace: tool_mcp__asp-agents__asp_plan (toolu_01ABC123)
│   ├── Input: {task_id, description, requirements}
│   ├── Output: {plan object}
│   ├── Duration: 5.2s
│   └── Metadata: {tool_type: mcp, success: true}
│
├── Trace: tool_Bash (toolu_02DEF456)
│   ├── Input: {command: "pytest tests/"}
│   ├── Output: {stdout, exit_code}
│   ├── Duration: 12.1s
│   └── Metadata: {tool_type: builtin, success: true}
│
└── Trace: tool_Edit (toolu_03GHI789)
    ├── Input: {file_path, old_string, new_string}
    ├── Output: {success: true}
    ├── Duration: 0.1s
    └── Metadata: {tool_type: builtin, success: true}
```

## Captured Tool Categories

| Category | Matcher | Examples | Captured Data |
|----------|---------|----------|---------------|
| **Built-in** | `Bash`, `Edit`, etc. | Bash, Edit, Read, Write, Glob, Grep, WebFetch, WebSearch | Command, file paths, content |
| **MCP Tools** | `mcp__*` | mcp__asp-agents__asp_plan, mcp__memory__query | Server, tool, arguments |
| **Subagents** | `Task` | Task tool for spawning agents | Prompt, agent type, result |
| **All** | `*` | Everything above | Universal capture |

## Security Considerations

### Data Sanitization

The telemetry hook automatically redacts sensitive fields:

```python
SENSITIVE_KEYS = {"password", "secret", "token", "api_key", "credential"}

# These are replaced with "[REDACTED]" in logs
```

### What's NOT Logged

- File contents (only paths)
- API keys and secrets
- Full command outputs (truncated to 500 chars)
- Response bodies over 10KB

### Access Control

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "mcp__asp-agents__*",
        "hooks": [
          {
            "type": "command",
            "command": "python ~/.claude/hooks/asp-auth-check.py"
          }
        ]
      }
    ]
  }
}
```

## Implementation Plan

### Phase 1: MCP Server (1 session)

| Task | Description | Effort |
|------|-------------|--------|
| 1.1 | Create `src/asp/mcp/` package | Low |
| 1.2 | Implement MCP server with 4 tools | Medium |
| 1.3 | Add `.mcp.json` configuration | Low |
| 1.4 | Test with Claude Code CLI | Medium |
| 1.5 | Document usage | Low |

### Phase 2: Telemetry Hooks (1 session)

| Task | Description | Effort |
|------|-------------|--------|
| 2.1 | Create `src/asp/hooks/telemetry.py` | Medium |
| 2.2 | Add Langfuse integration | Medium |
| 2.3 | Create `.claude/settings.json` template | Low |
| 2.4 | Add local file logging | Low |
| 2.5 | Test with various tools | Medium |

### Phase 3: Advanced Features (1-2 sessions)

| Task | Description | Effort |
|------|-------------|--------|
| 3.1 | Add OpenTelemetry export option | Medium |
| 3.2 | Create telemetry dashboard queries | Medium |
| 3.3 | Add cost tracking per tool | Medium |
| 3.4 | Performance metrics (latency, throughput) | Medium |

## Configuration Options

### Environment Variables

```bash
# Langfuse (required for cloud telemetry)
LANGFUSE_PUBLIC_KEY=pk-lf-...
LANGFUSE_SECRET_KEY=sk-lf-...
LANGFUSE_HOST=https://cloud.langfuse.com  # or self-hosted

# OpenTelemetry (optional)
OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4317
OTEL_SERVICE_NAME=asp-claude-code

# Local logging
ASP_TELEMETRY_LOG_DIR=~/.claude/telemetry
ASP_TELEMETRY_ENABLED=true
```

### Telemetry Levels

```yaml
# .asp/config.yaml
telemetry:
  enabled: true
  level: full  # full | minimal | off

  # What to capture
  capture:
    builtin_tools: true
    mcp_tools: true
    subagents: true

  # Where to send
  destinations:
    langfuse: true
    local_file: true
    otel: false

  # Privacy
  sanitize_secrets: true
  truncate_responses: 500
```

## Usage Examples

### Invoking ASP Agents from Claude Code

Once configured, Claude can use ASP agents naturally:

```
User: Use ASP to plan implementing a new authentication system

Claude: I'll use the ASP planning agent to create a comprehensive plan.
[Calls mcp__asp-agents__asp_plan]

The plan includes:
1. Create auth middleware (src/auth/middleware.py)
2. Add JWT token handling (src/auth/jwt.py)
3. Create login endpoint (src/api/auth.py)
...
```

### Viewing Telemetry

```bash
# Local logs
cat ~/.claude/telemetry/sess_abc.jsonl | jq .

# Langfuse UI
# Navigate to https://cloud.langfuse.com/traces
# Filter by session_id or tool_name
```

### Querying Telemetry

```python
from langfuse import Langfuse

langfuse = Langfuse()

# Get all ASP agent invocations
traces = langfuse.get_traces(
    name="tool_mcp__asp-agents__*",
    limit=100,
)

# Analyze success rates
success_count = sum(1 for t in traces if t.metadata.get("success"))
print(f"Success rate: {success_count}/{len(traces)}")
```

## Alternatives Considered

### Alternative 1: Subprocess-Based Agent Calls

Invoke ASP agents via subprocess instead of MCP:

```bash
claude --tool-command "python -m asp.cli plan --task-id $TASK_ID"
```

**Rejected because:**
- No structured input/output
- Harder to integrate with Claude's tool flow
- Less discoverable

### Alternative 2: Custom Claude Code Extension

Build a full Claude Code extension/plugin:

**Deferred because:**
- Higher complexity
- Plugin ecosystem still maturing
- MCP is the recommended approach

### Alternative 3: No Telemetry (Trust Claude's Logs)

Rely on Claude Code's built-in logging:

**Rejected because:**
- No Langfuse integration
- Limited query capabilities
- No cross-session analysis

## Consequences

### Positive

- **Full Observability** - Every tool call captured with timing, input, output
- **Seamless Integration** - ASP agents available as natural Claude tools
- **Debugging** - Easy to trace issues through Langfuse
- **Analytics** - Understand tool usage patterns, success rates
- **Non-Blocking** - Telemetry runs async, doesn't slow Claude

### Negative

- **Dependency** - Requires Langfuse or similar for cloud telemetry
- **Storage** - Local logs can grow large in active sessions
- **Complexity** - Additional configuration files to manage

### Neutral

- **Performance** - Minimal overhead (~10ms per tool call)
- **Security** - Requires careful handling of sensitive data

## Dependencies

### New Dependencies

```toml
# pyproject.toml
[project.optional-dependencies]
mcp = [
    "mcp>=0.1.0",  # Model Context Protocol SDK
]
telemetry = [
    "langfuse>=2.0.0",
    "opentelemetry-api>=1.20.0",
    "opentelemetry-sdk>=1.20.0",
]
```

### System Requirements

- Python 3.10+
- Claude Code CLI installed
- Langfuse account (for cloud telemetry) or self-hosted instance

## References

- [Claude Code Hooks Guide](https://docs.anthropic.com/en/docs/claude-code/hooks)
- [Claude Code MCP Documentation](https://docs.anthropic.com/en/docs/claude-code/mcp)
- [MCP Protocol Specification](https://modelcontextprotocol.io/)
- [Langfuse Documentation](https://langfuse.com/docs)
- [OpenTelemetry Python](https://opentelemetry.io/docs/languages/python/)
- [ADR 010: Multi-LLM Provider Support](./ADR_010_multi_llm_provider_support.md)
- [ADR 011: Claude CLI/Agent SDK Integration](./ADR_011_claude_cli_agent_sdk_integration.md)

---

**Status:** Draft
**Next Steps:**
1. Review and approve architecture
2. Implement Phase 1 (MCP Server)
3. Implement Phase 2 (Telemetry Hooks)
4. Test end-to-end with Claude Code CLI
