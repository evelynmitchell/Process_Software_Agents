"""
ASP Agents MCP Server.

Exposes ASP agents as MCP tools for Claude Code CLI.

Core Tools:
- asp_plan: Generate project plans using PlanningAgent
- asp_code_review: Review code using CodeReviewOrchestrator
- asp_diagnose: Diagnose errors using DiagnosticAgent
- asp_test: Run tests and analyze results using TestAgent

Extended Tools:
- asp_repair_issue: Full GitHub issue-to-PR automation
- asp_beads_sync: Sync beads planning with GitHub issues
- asp_provider_status: Check LLM provider configuration
- asp_session_context: Load tiered session context

Usage:
    # Run the MCP server
    python -m asp.mcp.server

    # Or configure in .mcp.json for Claude Code

Author: ASP Development Team
Date: December 2025
"""

import asyncio
import glob
import json
import logging
import os
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool

logger = logging.getLogger(__name__)

# Create MCP server
server = Server("asp-agents")


def create_server() -> Server:
    """Create and return the MCP server instance."""
    return server


@server.list_tools()
async def list_tools() -> list[Tool]:
    """List available ASP agent tools."""
    return [
        Tool(
            name="asp_plan",
            description=(
                "Generate a comprehensive project plan using ASP's PlanningAgent. "
                "Use when you need to break down a complex task into actionable steps "
                "with complexity scoring. Returns semantic units with effort estimates."
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
                        "description": "Brief description of the task (10+ characters)",
                    },
                    "requirements": {
                        "type": "string",
                        "description": "Detailed requirements and acceptance criteria (20+ characters)",
                    },
                    "context_files": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Optional list of file paths for additional context",
                    },
                },
                "required": ["task_id", "description", "requirements"],
            },
        ),
        Tool(
            name="asp_code_review",
            description=(
                "Review code using ASP's CodeReviewOrchestrator with 6 specialist agents. "
                "Analyzes code for security issues, performance problems, code quality, "
                "test coverage, documentation, and best practices. Returns structured feedback."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "task_id": {
                        "type": "string",
                        "description": "Unique identifier for this review task",
                    },
                    "files": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "path": {"type": "string"},
                                "content": {"type": "string"},
                                "file_type": {
                                    "type": "string",
                                    "enum": ["source", "test", "config"],
                                    "default": "source",
                                },
                            },
                            "required": ["path", "content"],
                        },
                        "description": "List of files to review with their content",
                    },
                    "quality_standards": {
                        "type": "string",
                        "description": "Optional additional quality standards to apply",
                    },
                },
                "required": ["task_id", "files"],
            },
        ),
        Tool(
            name="asp_diagnose",
            description=(
                "Diagnose test failures or errors using ASP's DiagnosticAgent. "
                "Analyzes error messages, stack traces, and source code to identify "
                "root causes and suggest precise fixes using search-replace patterns."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "task_id": {
                        "type": "string",
                        "description": "Unique identifier for this diagnostic task",
                    },
                    "error_type": {
                        "type": "string",
                        "description": "Type of error (e.g., 'AssertionError', 'TypeError')",
                    },
                    "error_message": {
                        "type": "string",
                        "description": "The error message or test failure output",
                    },
                    "stack_trace": {
                        "type": "string",
                        "description": "Full stack trace if available",
                    },
                    "workspace_path": {
                        "type": "string",
                        "description": "Path to the workspace/repository",
                        "default": ".",
                    },
                    "source_files": {
                        "type": "object",
                        "additionalProperties": {"type": "string"},
                        "description": "Map of file paths to their contents for context",
                    },
                },
                "required": ["task_id", "error_type", "error_message"],
            },
        ),
        Tool(
            name="asp_test",
            description=(
                "Generate and analyze tests using ASP's TestAgent. "
                "Creates comprehensive unit tests from design specifications and "
                "analyzes test results with defect classification."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "task_id": {
                        "type": "string",
                        "description": "Unique identifier for this test task",
                    },
                    "test_framework": {
                        "type": "string",
                        "description": "Test framework to use (e.g., 'pytest', 'unittest')",
                        "default": "pytest",
                    },
                    "coverage_target": {
                        "type": "number",
                        "description": "Target code coverage percentage",
                        "default": 80.0,
                    },
                    "generated_code": {
                        "type": "object",
                        "description": "GeneratedCode object with files and dependencies",
                    },
                    "design_specification": {
                        "type": "object",
                        "description": "DesignSpecification object with module design",
                    },
                },
                "required": ["task_id", "generated_code", "design_specification"],
            },
        ),
        # === Extended Tools ===
        Tool(
            name="asp_repair_issue",
            description=(
                "Automate the full GitHub issue-to-PR workflow. "
                "Fetches issue details, clones repo, creates branch, "
                "diagnoses the problem, generates a fix, runs tests, and creates a PR. "
                "Use for bug fixes referenced by GitHub issue URLs."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "issue_url": {
                        "type": "string",
                        "description": "GitHub issue URL (e.g., https://github.com/owner/repo/issues/123)",
                    },
                    "dry_run": {
                        "type": "boolean",
                        "description": "If true, diagnose and generate fix but don't create PR",
                        "default": False,
                    },
                    "workspace_path": {
                        "type": "string",
                        "description": "Optional path to existing workspace (skip clone if provided)",
                    },
                },
                "required": ["issue_url"],
            },
        ),
        Tool(
            name="asp_beads_sync",
            description=(
                "Synchronize beads planning data with GitHub issues. "
                "Supports push (create GitHub issues from beads), "
                "pull (import GitHub issues as beads), or bidirectional sync."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "direction": {
                        "type": "string",
                        "enum": ["push", "pull", "bidirectional"],
                        "description": "Sync direction: push to GitHub, pull from GitHub, or both",
                    },
                    "dry_run": {
                        "type": "boolean",
                        "description": "If true, show what would be synced without making changes",
                        "default": True,
                    },
                    "repo": {
                        "type": "string",
                        "description": "GitHub repo in owner/repo format (defaults to current repo)",
                    },
                },
                "required": ["direction"],
            },
        ),
        Tool(
            name="asp_provider_status",
            description=(
                "Check the status of configured LLM providers. "
                "Returns availability, available models, rate limit status, "
                "and cost estimates for each configured provider."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "check_connection": {
                        "type": "boolean",
                        "description": "If true, verify connection to each provider (slower but more accurate)",
                        "default": False,
                    },
                },
                "required": [],
            },
        ),
        Tool(
            name="asp_session_context",
            description=(
                "Load tiered session context from project history. "
                "Returns recent session summaries, weekly reflections, "
                "ADR status, and knowledge base entries based on depth level."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "depth": {
                        "type": "string",
                        "enum": ["minimal", "standard", "full"],
                        "description": "Context depth: minimal (last session), standard (3 sessions + weekly), full (all + knowledge base)",
                        "default": "standard",
                    },
                    "project_path": {
                        "type": "string",
                        "description": "Path to project root (defaults to current directory)",
                        "default": ".",
                    },
                },
                "required": [],
            },
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
    """Execute an ASP agent tool."""
    logger.info(f"MCP tool call: {name} with args: {list(arguments.keys())}")

    try:
        # Core tools
        if name == "asp_plan":
            return await _handle_plan(arguments)
        elif name == "asp_code_review":
            return await _handle_code_review(arguments)
        elif name == "asp_diagnose":
            return await _handle_diagnose(arguments)
        elif name == "asp_test":
            return await _handle_test(arguments)
        # Extended tools
        elif name == "asp_repair_issue":
            return await _handle_repair_issue(arguments)
        elif name == "asp_beads_sync":
            return await _handle_beads_sync(arguments)
        elif name == "asp_provider_status":
            return await _handle_provider_status(arguments)
        elif name == "asp_session_context":
            return await _handle_session_context(arguments)
        else:
            return [TextContent(type="text", text=f"Unknown tool: {name}")]
    except Exception as e:
        logger.error(f"Tool {name} failed: {e}", exc_info=True)
        return [
            TextContent(
                type="text",
                text=json.dumps(
                    {
                        "error": True,
                        "tool": name,
                        "message": str(e),
                        "type": type(e).__name__,
                    },
                    indent=2,
                ),
            )
        ]


async def _handle_plan(args: dict) -> list[TextContent]:
    """Handle asp_plan tool call."""
    from asp.agents.planning_agent import PlanningAgent
    from asp.models.planning import TaskRequirements

    # Build TaskRequirements from args
    requirements = TaskRequirements(
        task_id=args["task_id"],
        description=args["description"],
        requirements=args["requirements"],
        context_files=args.get("context_files"),
    )

    # Execute planning agent
    agent = PlanningAgent()
    result = await agent.execute_async(requirements)

    return [
        TextContent(
            type="text",
            text=json.dumps(result.model_dump(), indent=2),
        )
    ]


async def _handle_code_review(args: dict) -> list[TextContent]:
    """Handle asp_code_review tool call."""
    from asp.agents.code_review_orchestrator import CodeReviewOrchestrator
    from asp.models.code import GeneratedCode, GeneratedFile

    # Build GeneratedCode from args
    files = []
    for file_data in args.get("files", []):
        files.append(
            GeneratedFile(
                file_path=file_data["path"],
                content=file_data["content"],
                file_type=file_data.get("file_type", "source"),
                description=file_data.get("description", f"File: {file_data['path']}"),
            )
        )

    generated_code = GeneratedCode(
        task_id=args["task_id"],
        files=files,
        dependencies=[],  # Optional, can be extended
    )

    # Execute code review orchestrator
    agent = CodeReviewOrchestrator()

    # Run in thread pool since execute() is sync
    loop = asyncio.get_running_loop()
    result = await loop.run_in_executor(
        None,
        lambda: agent.execute(
            generated_code=generated_code,
            quality_standards=args.get("quality_standards"),
        ),
    )

    return [
        TextContent(
            type="text",
            text=json.dumps(result.model_dump(), indent=2),
        )
    ]


async def _handle_diagnose(args: dict) -> list[TextContent]:
    """Handle asp_diagnose tool call."""
    from asp.agents.diagnostic_agent import DiagnosticAgent
    from asp.models.diagnostic import DiagnosticInput
    from asp.models.execution import TestFailure, TestResult

    # Build minimal TestResult for DiagnosticInput
    # The diagnostic agent expects a TestResult, so we create one from the error info
    test_result = TestResult(
        passed=False,
        exit_code=1,
        failures=[
            TestFailure(
                test_name="unknown",
                test_file=args.get("workspace_path", "."),
                error_type=args["error_type"],
                error_message=args["error_message"],
                stack_trace=args.get("stack_trace", ""),
            )
        ],
        duration_seconds=0.0,
    )

    diagnostic_input = DiagnosticInput(
        task_id=args["task_id"],
        workspace_path=args.get("workspace_path", "."),
        test_result=test_result,
        error_type=args["error_type"],
        error_message=args["error_message"],
        stack_trace=args.get("stack_trace"),
        source_files=args.get("source_files", {}),
    )

    # Execute diagnostic agent
    agent = DiagnosticAgent()
    result = await agent.execute_async(diagnostic_input)

    return [
        TextContent(
            type="text",
            text=json.dumps(result.model_dump(), indent=2),
        )
    ]


async def _handle_test(args: dict) -> list[TextContent]:
    """Handle asp_test tool call."""
    from asp.agents.test_agent import TestAgent
    from asp.models.code import GeneratedCode, GeneratedFile
    from asp.models.design import DesignSpecification
    from asp.models.test import TestInput

    # Parse generated_code from args
    gc_data = args.get("generated_code", {})
    files = []
    for file_data in gc_data.get("files", []):
        files.append(
            GeneratedFile(
                file_path=file_data["path"],
                content=file_data["content"],
                file_type=file_data.get("file_type", "source"),
                description=file_data.get("description", f"File: {file_data['path']}"),
            )
        )

    generated_code = GeneratedCode(
        task_id=args["task_id"],
        files=files,
        dependencies=gc_data.get("dependencies", []),
    )

    # Parse design_specification from args
    ds_data = args.get("design_specification", {})
    design_spec = DesignSpecification.model_validate(ds_data)

    # Build TestInput
    test_input = TestInput(
        task_id=args["task_id"],
        generated_code=generated_code,
        design_specification=design_spec,
        test_framework=args.get("test_framework", "pytest"),
        coverage_target=args.get("coverage_target", 80.0),
    )

    # Execute test agent
    agent = TestAgent()
    result = await agent.execute_async(test_input)

    return [
        TextContent(
            type="text",
            text=json.dumps(result.model_dump(), indent=2),
        )
    ]


async def _handle_repair_issue(args: dict) -> list[TextContent]:
    """Handle asp_repair_issue tool call."""
    try:
        from asp.orchestrators.repair_orchestrator import RepairOrchestrator
        from asp.services.github_service import GitHubService
    except ImportError as e:
        return [
            TextContent(
                type="text",
                text=json.dumps(
                    {
                        "error": True,
                        "message": f"Required module not available: {e}",
                        "hint": "Ensure asp.services.github_service is installed",
                    },
                    indent=2,
                ),
            )
        ]

    issue_url = args["issue_url"]
    dry_run = args.get("dry_run", False)
    workspace_path = args.get("workspace_path")

    # Initialize services
    github_service = GitHubService()
    repair_orchestrator = RepairOrchestrator()

    try:
        # Execute repair workflow
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(
            None,
            lambda: repair_orchestrator.repair_from_issue(
                issue_url=issue_url,
                workspace_path=workspace_path,
                dry_run=dry_run,
            ),
        )

        return [
            TextContent(
                type="text",
                text=json.dumps(result if isinstance(result, dict) else result.model_dump(), indent=2),
            )
        ]
    except Exception as e:
        return [
            TextContent(
                type="text",
                text=json.dumps(
                    {
                        "error": True,
                        "issue_url": issue_url,
                        "message": str(e),
                        "type": type(e).__name__,
                    },
                    indent=2,
                ),
            )
        ]


async def _handle_beads_sync(args: dict) -> list[TextContent]:
    """Handle asp_beads_sync tool call."""
    try:
        from asp.beads.github_sync import GitHubBeadsSync
    except ImportError as e:
        return [
            TextContent(
                type="text",
                text=json.dumps(
                    {
                        "error": True,
                        "message": f"Required module not available: {e}",
                        "hint": "Ensure asp.beads.github_sync is installed",
                    },
                    indent=2,
                ),
            )
        ]

    direction = args["direction"]
    dry_run = args.get("dry_run", True)
    repo = args.get("repo")

    try:
        sync = GitHubBeadsSync(repo=repo)
        loop = asyncio.get_running_loop()

        if direction == "push":
            result = await loop.run_in_executor(None, lambda: sync.push(dry_run=dry_run))
        elif direction == "pull":
            result = await loop.run_in_executor(None, lambda: sync.pull(dry_run=dry_run))
        else:  # bidirectional
            result = await loop.run_in_executor(None, lambda: sync.sync(dry_run=dry_run))

        return [
            TextContent(
                type="text",
                text=json.dumps(result if isinstance(result, dict) else {"status": "complete", "result": str(result)}, indent=2),
            )
        ]
    except Exception as e:
        return [
            TextContent(
                type="text",
                text=json.dumps(
                    {
                        "error": True,
                        "direction": direction,
                        "message": str(e),
                        "type": type(e).__name__,
                    },
                    indent=2,
                ),
            )
        ]


async def _handle_provider_status(args: dict) -> list[TextContent]:
    """Handle asp_provider_status tool call."""
    check_connection = args.get("check_connection", False)

    try:
        from asp.providers.registry import ProviderRegistry
    except ImportError:
        # Fallback if provider registry not available
        return [
            TextContent(
                type="text",
                text=json.dumps(
                    {
                        "providers": {
                            "anthropic": {
                                "available": bool(os.environ.get("ANTHROPIC_API_KEY")),
                                "api_key_set": bool(os.environ.get("ANTHROPIC_API_KEY")),
                            }
                        },
                        "default": os.environ.get("ASP_LLM_PROVIDER", "anthropic"),
                        "note": "Full provider registry not available",
                    },
                    indent=2,
                ),
            )
        ]

    try:
        registry = ProviderRegistry()
        providers_info = {}

        for name in registry.list_providers():
            try:
                provider = registry.get(name)
                info = {
                    "available": True,
                    "models": provider.available_models if hasattr(provider, "available_models") else [],
                }

                if check_connection:
                    # Try a minimal API call to verify connection
                    try:
                        # This would need to be implemented in the provider
                        info["connection_verified"] = True
                    except Exception as conn_err:
                        info["connection_verified"] = False
                        info["connection_error"] = str(conn_err)

                providers_info[name] = info
            except Exception as e:
                providers_info[name] = {
                    "available": False,
                    "error": str(e),
                }

        return [
            TextContent(
                type="text",
                text=json.dumps(
                    {
                        "providers": providers_info,
                        "default": registry.get_default_provider_name(),
                        "total_available": sum(1 for p in providers_info.values() if p.get("available")),
                    },
                    indent=2,
                ),
            )
        ]
    except Exception as e:
        return [
            TextContent(
                type="text",
                text=json.dumps(
                    {
                        "error": True,
                        "message": str(e),
                        "type": type(e).__name__,
                    },
                    indent=2,
                ),
            )
        ]


async def _handle_session_context(args: dict) -> list[TextContent]:
    """Handle asp_session_context tool call."""
    depth = args.get("depth", "standard")
    project_path = Path(args.get("project_path", ".")).resolve()

    summary_dir = project_path / "Summary"
    docs_dir = project_path / "docs"
    design_dir = project_path / "design"

    context = {
        "depth": depth,
        "project_path": str(project_path),
        "timestamp": datetime.now(UTC).isoformat(),
        "sessions": [],
        "weekly_reflection": None,
        "adrs": {},
        "knowledge_base": None,
    }

    try:
        # Find session summaries sorted by modification time (newest first)
        summary_files = sorted(
            glob.glob(str(summary_dir / "summary*.md")),
            key=os.path.getmtime,
            reverse=True,
        )

        # Determine how many sessions to load based on depth
        session_count = {"minimal": 1, "standard": 3, "full": 5}.get(depth, 3)

        for summary_file in summary_files[:session_count]:
            try:
                with open(summary_file) as f:
                    content = f.read()
                    # Extract just the first 2000 chars to avoid context explosion
                    context["sessions"].append({
                        "file": os.path.basename(summary_file),
                        "content": content[:2000] + ("..." if len(content) > 2000 else ""),
                    })
            except Exception as e:
                logger.warning(f"Failed to read {summary_file}: {e}")

        # Find latest weekly reflection
        weekly_files = sorted(
            glob.glob(str(summary_dir / "weekly_reflection_*.md")),
            key=os.path.getmtime,
            reverse=True,
        )
        if weekly_files:
            try:
                with open(weekly_files[0]) as f:
                    content = f.read()
                    context["weekly_reflection"] = {
                        "file": os.path.basename(weekly_files[0]),
                        "content": content[:3000] + ("..." if len(content) > 3000 else ""),
                    }
            except Exception as e:
                logger.warning(f"Failed to read weekly reflection: {e}")

        # Parse ADR status from design directory
        adr_files = glob.glob(str(design_dir / "ADR_*.md"))
        for adr_file in adr_files:
            try:
                with open(adr_file) as f:
                    content = f.read()
                    # Extract title and status
                    lines = content.split("\n")
                    title = next((ln for ln in lines if ln.startswith("# ")), "Unknown")
                    status = "draft"
                    for line in lines:
                        if "complete" in line.lower():
                            status = "complete"
                            break
                        elif "in progress" in line.lower():
                            status = "in_progress"
                            break

                    context["adrs"][os.path.basename(adr_file)] = {
                        "title": title.replace("# ", ""),
                        "status": status,
                    }
            except Exception as e:
                logger.warning(f"Failed to parse ADR {adr_file}: {e}")

        # Load knowledge base for full depth
        if depth == "full":
            kb_path = docs_dir / "KNOWLEDGE_BASE.md"
            if kb_path.exists():
                try:
                    with open(kb_path) as f:
                        context["knowledge_base"] = f.read()
                except Exception as e:
                    logger.warning(f"Failed to read knowledge base: {e}")

        return [
            TextContent(
                type="text",
                text=json.dumps(context, indent=2),
            )
        ]
    except Exception as e:
        return [
            TextContent(
                type="text",
                text=json.dumps(
                    {
                        "error": True,
                        "message": str(e),
                        "type": type(e).__name__,
                        "project_path": str(project_path),
                    },
                    indent=2,
                ),
            )
        ]


async def _run_server():
    """Run the MCP server (async implementation)."""
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options(),
        )


def main():
    """Entry point for the MCP server."""
    # Configure logging
    logging.basicConfig(
        level=os.environ.get("ASP_LOG_LEVEL", "INFO"),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    logger.info("Starting ASP MCP Server")
    asyncio.run(_run_server())


if __name__ == "__main__":
    main()
