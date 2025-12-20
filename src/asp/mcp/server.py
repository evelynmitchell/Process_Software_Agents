"""
ASP Agents MCP Server.

Exposes ASP agents as MCP tools for Claude Code CLI.

Tools:
- asp_plan: Generate project plans using PlanningAgent
- asp_code_review: Review code using CodeReviewOrchestrator
- asp_diagnose: Diagnose errors using DiagnosticAgent
- asp_test: Run tests and analyze results using TestAgent

Usage:
    # Run the MCP server
    python -m asp.mcp.server

    # Or configure in .mcp.json for Claude Code

Author: ASP Development Team
Date: December 2025
"""

import asyncio
import json
import logging
import os
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
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
    """Execute an ASP agent tool."""
    logger.info(f"MCP tool call: {name} with args: {list(arguments.keys())}")

    try:
        if name == "asp_plan":
            return await _handle_plan(arguments)
        elif name == "asp_code_review":
            return await _handle_code_review(arguments)
        elif name == "asp_diagnose":
            return await _handle_diagnose(arguments)
        elif name == "asp_test":
            return await _handle_test(arguments)
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
