"""
ASP Hooks Package.

Provides Claude Code CLI hooks for telemetry and other integrations.

Hooks:
- telemetry: Universal telemetry hook for capturing all tool invocations

Usage:
    Configure in .claude/settings.json:
    {
      "hooks": {
        "PreToolUse": [{"matcher": "*", "hooks": [{"type": "command", "command": "python -m asp.hooks.telemetry pre"}]}],
        "PostToolUse": [{"matcher": "*", "hooks": [{"type": "command", "command": "python -m asp.hooks.telemetry post"}]}]
      }
    }
"""

from asp.hooks.telemetry import handle_post_tool_use, handle_pre_tool_use

__all__ = ["handle_pre_tool_use", "handle_post_tool_use"]
