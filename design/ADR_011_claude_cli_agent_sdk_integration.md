# ADR 011: Claude CLI and Agent SDK Integration

**Status:** Draft
**Date:** 2025-12-18
**Session:** 20251218.1
**Deciders:** User, Claude
**Supersedes:** Partially overlaps with ADR 010 (Multi-LLM Provider Support)

## Context and Problem Statement

The current ASP implementation uses the **Anthropic Python SDK** to make direct API calls to Claude. While this works well, there are several reasons to consider using the **Claude CLI** or **Claude Agent SDK** instead:

1. **Subscription-Based Pricing** - Users with Claude Pro/Max subscriptions could use ASP without additional API costs
2. **Agentic Capabilities** - Claude CLI has built-in tools (file editing, bash execution, git operations) that overlap with ASP's agent capabilities
3. **MCP Integration** - Model Context Protocol support enables extensible tool architectures
4. **Session Management** - Built-in conversation context and compaction
5. **Reduced Complexity** - Leverage Anthropic's production-ready agent harness

### Current State

```
Current: Direct API Integration
┌─────────────────────────────────────────────────────────────┐
│ ASP Agent → LLMClient → Anthropic SDK → Anthropic API      │
│                                                             │
│ - Direct HTTP calls to api.anthropic.com                   │
│ - Pay-per-token via API key                                │
│ - Custom retry/error handling                              │
│ - No built-in tool execution                               │
└─────────────────────────────────────────────────────────────┘

Proposed: Claude Agent SDK Integration
┌─────────────────────────────────────────────────────────────┐
│ ASP Agent → ClaudeCLIProvider → Claude Agent SDK → Claude  │
│                                                             │
│ - SDK handles API calls internally                         │
│ - Subscription OR API billing                              │
│ - Built-in retry/context management                        │
│ - Native tool execution (optional)                         │
└─────────────────────────────────────────────────────────────┘
```

### Pain Points with Current Approach

| Issue | Impact |
|-------|--------|
| API-only billing | Users with subscriptions pay twice |
| Manual tool orchestration | ASP must manage all tool execution |
| No context compaction | Long sessions hit token limits |
| No session persistence | Can't resume interrupted work |
| Duplicate functionality | ASP tools overlap with Claude CLI tools |

## Decision Drivers

1. **Cost Flexibility** - Support both subscription and API billing
2. **Backward Compatibility** - Existing API-based code must continue to work
3. **Leverage Agentic Features** - Use Claude's built-in tools where beneficial
4. **Maintain Control** - ASP should remain the orchestration layer
5. **Simplicity** - Avoid unnecessary complexity
6. **Async Support** - Must integrate with ADR 008 async architecture

## Claude CLI / Agent SDK Overview

### What is the Claude Agent SDK?

The Claude Agent SDK (formerly Claude Code's internal harness) is Anthropic's official framework for building AI agents. It provides:

- **Multi-turn conversations** with context management
- **Tool execution** via Model Context Protocol (MCP)
- **Session persistence** and resumption
- **Structured outputs** with JSON schema validation
- **Built-in tools**: File editing, bash execution, git operations
- **Permission controls** for tool access
- **Hooks** for pre/post execution logic

### Invocation Methods

| Method | Use Case | Complexity | Control |
|--------|----------|------------|---------|
| **Subprocess CLI** | Simple, one-shot prompts | Low | Low |
| **Claude Agent SDK (Python)** | Full agentic control | Medium | High |
| **Direct API** | Raw LLM calls only | Low | Full |

### Authentication Options

| Method | Billing | Setup | Best For |
|--------|---------|-------|----------|
| `ANTHROPIC_API_KEY` | Pay-per-token | Env var | Production, CI/CD |
| Subscription login | Included in plan | Interactive | Development, personal use |
| AWS Bedrock | AWS billing | AWS credentials | Enterprise AWS users |
| Google Vertex AI | GCP billing | GCP credentials | Enterprise GCP users |

### Pricing Comparison

| Approach | Cost Model | Estimated Monthly Cost* |
|----------|------------|------------------------|
| API (Haiku 4.5) | ~$0.25/$1.25 per 1M tokens | $5-50 for light use |
| API (Sonnet 4.5) | ~$3/$15 per 1M tokens | $50-500 for moderate use |
| Claude Pro | $20/month flat | $20 (40-80 hrs/week) |
| Claude Max 5x | $100/month flat | $100 (200-400 hrs/week) |

*Actual costs depend on usage patterns

## Proposed Architecture

### Option A: Claude Agent SDK as LLM Provider (Recommended)

Integrate Claude Agent SDK as a provider within the ADR 010 provider abstraction:

```python
# src/asp/providers/claude_sdk_provider.py

from claude_agent_sdk import ClaudeSDKClient, ClaudeAgentOptions, OutputFormat
from asp.providers.base import LLMProvider, LLMResponse, ProviderConfig

class ClaudeSDKProvider(LLMProvider):
    """
    Claude Agent SDK provider for ASP agents.

    Uses the official Claude Agent SDK for:
    - Subscription-based or API billing
    - Built-in context management
    - Session persistence (optional)
    - Structured output validation
    """

    name = "claude_sdk"

    def __init__(self, config: ProviderConfig | None = None):
        self.config = config or ProviderConfig()
        self._client: ClaudeSDKClient | None = None

        # SDK options
        self.options = ClaudeAgentOptions(
            # Disable built-in tools - ASP handles tool execution
            allowed_tools=[],
            # Enable structured outputs for consistent parsing
            output_format=OutputFormat(type="text"),
        )

    async def call_async(
        self,
        prompt: str,
        model: str | None = None,
        max_tokens: int = 4096,
        temperature: float = 0.0,
        system: str | None = None,
        **kwargs,
    ) -> LLMResponse:
        """
        Async LLM call via Claude Agent SDK.
        """
        async with ClaudeSDKClient(options=self.options) as client:
            # Build the full prompt with system context
            full_prompt = prompt
            if system:
                full_prompt = f"{system}\n\n{prompt}"

            await client.query(full_prompt)

            content_parts = []
            usage = {"input_tokens": 0, "output_tokens": 0}

            async for message in client.receive_response():
                if message.type == "text":
                    content_parts.append(message.content)
                elif message.type == "usage":
                    usage = message.usage

            content = "".join(content_parts)

            return LLMResponse(
                content=self._try_parse_json(content),
                raw_content=content,
                usage=usage,
                cost=self._estimate_cost(usage),
                model=model or "claude-sonnet-4-5",
                provider="claude_sdk",
                stop_reason="end_turn",
            )

    def call(self, prompt: str, **kwargs) -> LLMResponse:
        """Sync wrapper for async call."""
        import asyncio
        return asyncio.run(self.call_async(prompt, **kwargs))

    def estimate_cost(self, model: str, input_tokens: int, output_tokens: int) -> float:
        """
        Estimate cost. Returns 0 for subscription users.
        """
        # If using subscription, cost is included
        if self._is_subscription_auth():
            return 0.0

        # API pricing (Sonnet 4.5)
        return (input_tokens / 1_000_000) * 3.0 + (output_tokens / 1_000_000) * 15.0
```

### Option B: Hybrid Mode - SDK for Tools, API for LLM

Use Claude Agent SDK's tool execution while keeping direct API calls for LLM:

```python
class HybridClaudeProvider(LLMProvider):
    """
    Hybrid provider: Direct API for LLM + SDK for tool execution.

    Benefits:
    - Full control over LLM parameters
    - SDK handles complex tool orchestration
    - Best of both worlds
    """

    def __init__(self, config: ProviderConfig | None = None):
        self.config = config or ProviderConfig()

        # Direct API client for LLM calls
        self.api_client = AsyncAnthropic(api_key=config.api_key)

        # SDK client for tool execution (lazy-loaded)
        self._sdk_client: ClaudeSDKClient | None = None

    async def call_async(self, prompt: str, **kwargs) -> LLMResponse:
        """Direct API call for LLM."""
        response = await self.api_client.messages.create(
            model=kwargs.get("model", "claude-sonnet-4-5"),
            max_tokens=kwargs.get("max_tokens", 4096),
            messages=[{"role": "user", "content": prompt}],
        )
        return self._convert_response(response)

    async def execute_with_tools(
        self,
        prompt: str,
        tools: list[str],
        **kwargs,
    ) -> LLMResponse:
        """
        Execute prompt with Claude SDK tools.

        Useful for tasks that benefit from Claude's built-in tools:
        - File editing with Edit tool
        - Bash command execution
        - Git operations
        """
        options = ClaudeAgentOptions(
            allowed_tools=tools,  # e.g., ["Edit", "Bash", "Read"]
        )

        async with ClaudeSDKClient(options=options) as client:
            await client.query(prompt)
            # ... collect response ...
```

### Option C: Full SDK Delegation (Agentic Mode)

Let Claude Agent SDK handle both LLM calls AND tool execution:

```python
class AgenticClaudeProvider(LLMProvider):
    """
    Full agentic provider using Claude Agent SDK.

    In this mode, ASP provides high-level goals and the SDK
    handles multi-step execution autonomously.

    Use cases:
    - Complex multi-file refactoring
    - Autonomous debugging sessions
    - End-to-end feature implementation
    """

    async def execute_agentic_task(
        self,
        task_description: str,
        workspace_path: Path,
        allowed_tools: list[str] | None = None,
        max_iterations: int = 10,
    ) -> AgenticResult:
        """
        Execute a task using Claude's full agentic capabilities.

        The SDK will autonomously:
        1. Analyze the task
        2. Plan execution steps
        3. Execute tools (file edits, bash, etc.)
        4. Iterate until complete or max_iterations
        """
        options = ClaudeAgentOptions(
            allowed_tools=allowed_tools or ["Edit", "Read", "Bash", "Glob", "Grep"],
            working_directory=str(workspace_path),
            max_turns=max_iterations,
        )

        async with ClaudeSDKClient(options=options) as client:
            await client.query(task_description)

            results = []
            async for message in client.receive_response():
                results.append(message)

                # Track tool executions
                if message.type == "tool_use":
                    logger.info(f"SDK executing tool: {message.name}")
                elif message.type == "tool_result":
                    logger.info(f"Tool result: {message.output[:100]}...")

            return AgenticResult(
                messages=results,
                files_modified=self._extract_modified_files(results),
                commands_executed=self._extract_commands(results),
            )
```

### Option D: Custom MCP Server Integration

Expose ASP's existing agents as MCP tools for Claude SDK:

```python
# src/asp/mcp/asp_tools_server.py

from claude_agent_sdk import tool, create_sdk_mcp_server

@tool(
    name="asp_plan",
    description="Generate a project plan using ASP's PlanningAgent",
    schema={
        "task_id": {"type": "string", "description": "Unique task identifier"},
        "description": {"type": "string", "description": "Task description"},
        "requirements": {"type": "string", "description": "Detailed requirements"},
    }
)
async def asp_plan_tool(args: dict) -> dict:
    """MCP tool wrapper for PlanningAgent."""
    from asp.agents.planning_agent import PlanningAgent
    from asp.models.planning import TaskRequirements

    agent = PlanningAgent()
    requirements = TaskRequirements(
        task_id=args["task_id"],
        description=args["description"],
        requirements=args["requirements"],
    )

    plan = await agent.execute_async(requirements)

    return {
        "content": [{
            "type": "text",
            "text": plan.model_dump_json(indent=2)
        }]
    }


@tool(
    name="asp_code_review",
    description="Review code using ASP's CodeReviewAgent",
    schema={
        "file_path": {"type": "string"},
        "code": {"type": "string"},
    }
)
async def asp_code_review_tool(args: dict) -> dict:
    """MCP tool wrapper for CodeReviewAgent."""
    # ... implementation ...


# Create MCP server with ASP tools
asp_mcp_server = create_sdk_mcp_server(
    name="asp-agents",
    version="1.0.0",
    tools=[asp_plan_tool, asp_code_review_tool],
)
```

## Comparison of Options

| Aspect | Option A: SDK Provider | Option B: Hybrid | Option C: Full Agentic | Option D: MCP Tools |
|--------|------------------------|------------------|------------------------|---------------------|
| **Complexity** | Low | Medium | Medium | High |
| **Control** | High (ASP orchestrates) | High | Low (SDK orchestrates) | Medium |
| **Subscription Support** | Yes | Partial | Yes | Yes |
| **Tool Execution** | ASP handles | SDK handles | SDK handles | SDK calls ASP |
| **Backward Compatible** | Yes | Yes | Breaking change | Yes |
| **Best For** | LLM-only replacement | Tool-heavy tasks | Autonomous tasks | Extending Claude CLI |

## Recommended Approach

**Phase 1: Option A (SDK as LLM Provider)**

Start with the simplest integration:
1. Create `ClaudeSDKProvider` implementing the ADR 010 `LLMProvider` interface
2. Support both subscription and API authentication
3. ASP remains the orchestration layer
4. Claude SDK handles only LLM calls (no tools)

**Phase 2: Option B (Hybrid for Tool Tasks)**

Add hybrid mode for specific use cases:
1. Use SDK's built-in tools for file editing and bash execution
2. Keep ASP agents for specialized logic (planning, code review)
3. Configurable per-task

**Phase 3: Option D (MCP Integration - Optional)**

If there's demand:
1. Expose ASP agents as MCP tools
2. Allow Claude CLI users to invoke ASP capabilities
3. Enables "asp" as a Claude Code slash command

## Implementation Plan

### Phase 1: Foundation (1-2 sessions)

| Task | Description | Effort |
|------|-------------|--------|
| 1.1 | Install `claude-agent-sdk` dependency | Low |
| 1.2 | Create `ClaudeSDKProvider` class | Medium |
| 1.3 | Implement async `call_async()` method | Medium |
| 1.4 | Add authentication detection (API vs subscription) | Low |
| 1.5 | Register provider in `ProviderRegistry` | Low |
| 1.6 | Add `--provider claude_sdk` CLI flag | Low |
| 1.7 | Write unit tests with mocked SDK | Medium |

### Phase 2: Hybrid Mode (1-2 sessions)

| Task | Description | Effort |
|------|-------------|--------|
| 2.1 | Create `execute_with_tools()` method | Medium |
| 2.2 | Map ASP tool permissions to SDK allowed_tools | Medium |
| 2.3 | Add configuration for tool delegation | Low |
| 2.4 | Integration tests with real SDK | High |

### Phase 3: MCP Integration (2-3 sessions, optional)

| Task | Description | Effort |
|------|-------------|--------|
| 3.1 | Create `asp_tools_server.py` MCP server | High |
| 3.2 | Wrap ASP agents as MCP tools | High |
| 3.3 | Documentation for Claude CLI users | Medium |
| 3.4 | E2E tests | High |

## Configuration

### Environment Variables

```bash
# Provider selection
ASP_LLM_PROVIDER=claude_sdk  # Use Claude Agent SDK

# Authentication (in priority order)
ANTHROPIC_API_KEY=sk-ant-...  # API billing (takes precedence)
# OR: Use interactive login for subscription billing

# SDK-specific options
CLAUDE_SDK_ALLOWED_TOOLS=     # Empty = no tools (LLM only)
CLAUDE_SDK_MAX_TURNS=10       # Max iterations for agentic mode
CLAUDE_SDK_WORKING_DIR=.      # Working directory for tools
```

### Configuration File

```yaml
# .asp/config.yaml
llm:
  provider: claude_sdk

  claude_sdk:
    # Authentication mode: "api" | "subscription" | "auto"
    auth_mode: auto

    # Tool configuration (Phase 2+)
    tools:
      enabled: false  # Start with LLM-only
      allowed:
        - Read
        - Glob
        - Grep
      # Explicitly disable dangerous tools
      blocked:
        - Bash
        - Edit

    # Session management
    session:
      persist: false  # Save sessions for resumption
      max_context_tokens: 100000
```

## Dependencies

### New Dependencies

```toml
# pyproject.toml
[project.optional-dependencies]
claude-sdk = [
    "claude-agent-sdk>=0.1.0",  # Official SDK
]
```

### System Requirements

- Python 3.10+ (SDK requirement)
- Node.js 18+ (SDK uses Node.js internally)
- Claude CLI installed (for subscription auth)

## Containerized Deployment (Recommended)

To isolate the Node.js dependency and maintain a clean ASP environment, the Claude SDK can be deployed as a **containerized sidecar service**.

### Architecture: Containerized SDK Service

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         ASP Host Environment                            │
│                         (Python only, no Node.js)                       │
│                                                                         │
│  ┌─────────────────┐         HTTP/gRPC          ┌────────────────────┐ │
│  │   ASP Agent     │ ◄─────────────────────────► │  Claude SDK        │ │
│  │                 │         localhost:8080      │  Container         │ │
│  │  LLMClient      │                             │                    │ │
│  │       │         │                             │  - Node.js 18+     │ │
│  │       ▼         │                             │  - Claude SDK      │ │
│  │  ClaudeSDK      │                             │  - REST API        │ │
│  │  Provider       │                             │                    │ │
│  └─────────────────┘                             └────────────────────┘ │
│                                                          │              │
└──────────────────────────────────────────────────────────┼──────────────┘
                                                           │
                                                           ▼
                                                  ┌────────────────────┐
                                                  │   Anthropic API    │
                                                  │   (or subscription)│
                                                  └────────────────────┘
```

### Benefits of Containerization

| Benefit | Description |
|---------|-------------|
| **Dependency Isolation** | Node.js stays in container, ASP host remains Python-only |
| **Version Control** | Pin exact Node.js and SDK versions in Dockerfile |
| **Reproducibility** | Same container works across dev, CI, production |
| **Resource Limits** | Constrain memory/CPU for SDK operations |
| **Security** | SDK runs in isolated namespace |
| **Easy Updates** | Update SDK by pulling new container image |

### Container Implementation

#### Dockerfile for Claude SDK Service

```dockerfile
# docker/claude-sdk-service/Dockerfile
FROM node:18-slim

# Install Claude CLI and SDK
RUN npm install -g @anthropic-ai/claude-code

# Install Python for SDK Python bindings (optional)
RUN apt-get update && apt-get install -y python3 python3-pip
RUN pip3 install claude-agent-sdk fastapi uvicorn

# Copy service code
WORKDIR /app
COPY sdk_service.py .

# Expose REST API port
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s \
  CMD curl -f http://localhost:8080/health || exit 1

CMD ["uvicorn", "sdk_service:app", "--host", "0.0.0.0", "--port", "8080"]
```

#### SDK Service (FastAPI wrapper)

```python
# docker/claude-sdk-service/sdk_service.py
"""
REST API wrapper for Claude Agent SDK.

Runs inside container, exposes HTTP endpoints for ASP to call.
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from claude_agent_sdk import ClaudeSDKClient, ClaudeAgentOptions
import os

app = FastAPI(title="Claude SDK Service")


class LLMRequest(BaseModel):
    prompt: str
    model: str | None = None
    max_tokens: int = 4096
    temperature: float = 0.0
    system: str | None = None


class LLMResponse(BaseModel):
    content: str
    usage: dict
    model: str
    stop_reason: str | None


@app.get("/health")
async def health():
    return {"status": "healthy", "sdk_version": "0.1.0"}


@app.post("/v1/complete", response_model=LLMResponse)
async def complete(request: LLMRequest):
    """
    Simple completion endpoint (no tools).
    """
    try:
        options = ClaudeAgentOptions(allowed_tools=[])

        async with ClaudeSDKClient(options=options) as client:
            full_prompt = request.prompt
            if request.system:
                full_prompt = f"{request.system}\n\n{request.prompt}"

            await client.query(full_prompt)

            content_parts = []
            usage = {}

            async for message in client.receive_response():
                if message.type == "text":
                    content_parts.append(message.content)
                elif hasattr(message, "usage"):
                    usage = message.usage

            return LLMResponse(
                content="".join(content_parts),
                usage=usage,
                model=request.model or "claude-sonnet-4-5",
                stop_reason="end_turn",
            )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/v1/agentic")
async def agentic_task(request: dict):
    """
    Full agentic execution with tools (Phase 2+).
    """
    # Implementation for tool-enabled execution
    pass
```

#### Docker Compose Configuration

```yaml
# docker-compose.claude-sdk.yaml
version: '3.8'

services:
  claude-sdk:
    build:
      context: ./docker/claude-sdk-service
      dockerfile: Dockerfile
    ports:
      - "8080:8080"
    environment:
      # Pass through API key (or mount subscription credentials)
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
    volumes:
      # For subscription auth, mount Claude config
      - ~/.claude:/root/.claude:ro
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8080/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    # Resource limits
    deploy:
      resources:
        limits:
          memory: 1G
          cpus: '1.0'
```

#### ASP Provider (calls containerized service)

```python
# src/asp/providers/claude_sdk_container_provider.py
"""
Claude SDK provider that calls containerized service.

No Node.js dependency on the host - all SDK operations happen in container.
"""

import httpx
from asp.providers.base import LLMProvider, LLMResponse, ProviderConfig


class ClaudeSDKContainerProvider(LLMProvider):
    """
    Claude SDK provider using containerized service.

    Benefits:
    - No Node.js on host
    - Isolated SDK environment
    - Easy version management
    """

    name = "claude_sdk_container"

    def __init__(self, config: ProviderConfig | None = None):
        self.config = config or ProviderConfig()
        self.base_url = self.config.extra.get(
            "service_url", "http://localhost:8080"
        )
        self._client: httpx.AsyncClient | None = None

    @property
    def client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                timeout=120.0,  # LLM calls can be slow
            )
        return self._client

    async def call_async(
        self,
        prompt: str,
        model: str | None = None,
        max_tokens: int = 4096,
        temperature: float = 0.0,
        system: str | None = None,
        **kwargs,
    ) -> LLMResponse:
        """Call containerized SDK service."""
        response = await self.client.post(
            "/v1/complete",
            json={
                "prompt": prompt,
                "model": model,
                "max_tokens": max_tokens,
                "temperature": temperature,
                "system": system,
            },
        )
        response.raise_for_status()
        data = response.json()

        return LLMResponse(
            content=data["content"],
            raw_content=data["content"],
            usage=data["usage"],
            cost=None,  # Container service can calculate
            model=data["model"],
            provider="claude_sdk_container",
            stop_reason=data.get("stop_reason"),
        )

    def call(self, prompt: str, **kwargs) -> LLMResponse:
        """Sync wrapper."""
        import asyncio
        return asyncio.run(self.call_async(prompt, **kwargs))

    async def health_check(self) -> bool:
        """Check if container service is running."""
        try:
            response = await self.client.get("/health")
            return response.status_code == 200
        except httpx.RequestError:
            return False
```

### Deployment Options

| Option | Complexity | Best For |
|--------|------------|----------|
| **Docker Compose** | Low | Local development, single-machine |
| **Kubernetes Sidecar** | Medium | Production, cloud deployments |
| **AWS ECS/Fargate** | Medium | AWS-native deployments |
| **Podman** | Low | Rootless containers, security-focused |
| **Cloudflare Containers** | Low-Medium | Global edge deployment, low latency |

### Cloudflare Containers Deployment

[Cloudflare Containers](https://blog.cloudflare.com/cloudflare-containers-coming-2025/) (open beta June 2025) provides an excellent deployment option with global edge distribution.

#### Why Cloudflare Containers?

| Benefit | Description |
|---------|-------------|
| **Global Distribution** | Containers run on Cloudflare's edge network (300+ cities) |
| **Low Latency** | Requests routed to nearest edge location |
| **Simple Scaling** | Automatic scaling with high limits (400 GiB RAM, 100 vCPUs) |
| **Workers Integration** | Use Workers as API gateway/orchestrator |
| **No Cold Starts** | Durable Objects keep containers warm |
| **Cost Effective** | Pay only for actual compute time |

#### Architecture: Cloudflare Edge Deployment

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        Cloudflare Edge Network                               │
│                                                                              │
│   User Request                                                               │
│        │                                                                     │
│        ▼                                                                     │
│   ┌─────────────────┐         ┌────────────────────────────────────────┐   │
│   │ Cloudflare      │         │  Cloudflare Container                   │   │
│   │ Worker          │ ──────► │                                         │   │
│   │ (API Gateway)   │         │  - Node.js 18 + Claude SDK              │   │
│   │                 │         │  - FastAPI REST service                 │   │
│   │ - Auth          │         │  - Handles LLM calls                    │   │
│   │ - Rate limiting │         │                                         │   │
│   │ - Routing       │         └────────────────────────────────────────┘   │
│   └─────────────────┘                          │                            │
│                                                ▼                            │
└────────────────────────────────────────────────┼────────────────────────────┘
                                                 │
                                                 ▼
                                        ┌────────────────────┐
                                        │   Anthropic API    │
                                        └────────────────────┘
```

#### Cloudflare Worker (API Gateway)

```typescript
// cloudflare/worker/src/index.ts
import { Hono } from 'hono'
import { cors } from 'hono/cors'
import { bearerAuth } from 'hono/bearer-auth'

type Bindings = {
  CLAUDE_SDK_CONTAINER: Fetcher  // Binding to container
  ASP_API_KEY: string
}

const app = new Hono<{ Bindings: Bindings }>()

// CORS for ASP clients
app.use('/*', cors())

// API key authentication
app.use('/v1/*', async (c, next) => {
  const auth = bearerAuth({ token: c.env.ASP_API_KEY })
  return auth(c, next)
})

// Proxy to Claude SDK container
app.post('/v1/complete', async (c) => {
  const body = await c.req.json()

  // Forward to container
  const response = await c.env.CLAUDE_SDK_CONTAINER.fetch(
    new Request('http://container/v1/complete', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    })
  )

  return response
})

// Health check
app.get('/health', (c) => {
  return c.json({ status: 'healthy', edge: c.req.cf?.colo })
})

export default app
```

#### Cloudflare Container Configuration

```toml
# cloudflare/container/wrangler.toml
name = "claude-sdk-service"
compatibility_date = "2025-06-01"

[containers]
  name = "claude-sdk"
  image = "asp/claude-sdk-service:latest"

  # Resource allocation
  memory_mb = 1024
  vcpus = 1

  # Environment variables
  [containers.env]
    NODE_ENV = "production"

  # Secrets (set via wrangler secret)
  # ANTHROPIC_API_KEY = <from secrets>

[containers.ports]
  http = 8080

# Durable Object for session state (optional)
[[durable_objects.bindings]]
  name = "SESSIONS"
  class_name = "SessionState"
```

#### Deployment Commands

```bash
# Login to Cloudflare
wrangler login

# Deploy container
cd cloudflare/container
wrangler deploy

# Set secrets
wrangler secret put ANTHROPIC_API_KEY

# Deploy worker (API gateway)
cd ../worker
wrangler deploy

# Check status
wrangler containers list
```

#### ASP Configuration for Cloudflare

```yaml
# .asp/config.yaml
llm:
  provider: claude_sdk_container

  claude_sdk_container:
    # Cloudflare Worker URL (your custom domain or workers.dev)
    service_url: https://claude-sdk.your-domain.com
    # OR: https://claude-sdk-gateway.your-account.workers.dev

    # Authentication
    api_key: ${ASP_CLOUDFLARE_API_KEY}

    timeout: 120
    retries: 3
```

#### Cost Estimate (Cloudflare Containers)

| Usage Level | Containers | Estimated Cost* |
|-------------|------------|-----------------|
| Development | 1 basic instance | ~$5-10/month |
| Light Production | 2-5 instances | ~$20-50/month |
| Heavy Production | 10+ instances | ~$100+/month |

*Plus Anthropic API costs. Cloudflare pricing still evolving in beta.

#### Alternative: Workers-Only (No Container)

For simpler deployments, Cloudflare Workers now has [improved Node.js compatibility](https://blog.cloudflare.com/nodejs-workers-2025/). However, the Claude Agent SDK may require full Node.js runtime features not yet available in Workers. Test carefully:

```typescript
// Experimental: Direct SDK in Worker (may have limitations)
// cloudflare/worker-only/src/index.ts
import { ClaudeSDKClient } from 'claude-agent-sdk'  // If compatible

export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    // May work with nodejs_compat flag
    const client = new ClaudeSDKClient()
    // ...
  }
}
```

```toml
# wrangler.toml for Workers-only approach
compatibility_flags = ["nodejs_compat"]
```

**Recommendation:** Start with Cloudflare Containers for full SDK compatibility, then evaluate Workers-only if SDK adds Workers support.

### Updated Implementation Plan with Containerization

| Phase | Task | Description |
|-------|------|-------------|
| 1a | Create Dockerfile | SDK service container |
| 1b | Create FastAPI wrapper | REST API for SDK |
| 1c | Create `ClaudeSDKContainerProvider` | HTTP client provider |
| 1d | Docker Compose config | Local development setup |
| 1e | Health checks and retry logic | Robust container communication |

### Configuration for Containerized Mode

```yaml
# .asp/config.yaml
llm:
  provider: claude_sdk_container

  claude_sdk_container:
    service_url: http://localhost:8080
    # OR for Kubernetes:
    # service_url: http://claude-sdk-service:8080

    timeout: 120  # seconds
    retries: 3

    # Container management (if ASP should start/stop container)
    auto_start: true
    container_name: asp-claude-sdk
    image: asp/claude-sdk-service:latest
```

## Option E: ASP Agents as Claude Skills with Unified Telemetry

A powerful integration approach: package ASP agents as **Claude Skills** and wrap *all* tool execution (Claude's built-in + ASP agents) in unified telemetry.

### Skills vs MCP Tools

| Aspect | Skills | MCP Tools |
|--------|--------|-----------|
| **Architecture** | Prompt-based (instruction injection) | Protocol-based (network) |
| **Deployment** | Filesystem (`.claude/skills/`) | Servers (stdio, SSE, HTTP) |
| **Network Access** | No (local only) | Yes (APIs, databases) |
| **Use Case** | Methodology, workflows | External integrations |
| **Latency** | Immediate (context injection) | Network latency |

**Key Insight:** Skills package *methodology* (how to plan, code, review), MCP provides *connectivity* (APIs, telemetry backends). They're complementary.

### Architecture: ASP Skills + MCP Telemetry

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         Claude Agent SDK Runtime                             │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                    ASP Skills (Methodology Layer)                    │   │
│  │                                                                      │   │
│  │  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌────────────┐ │   │
│  │  │ asp-planning │ │ asp-design   │ │ asp-code     │ │ asp-review │ │   │
│  │  │ SKILL.md     │ │ SKILL.md     │ │ SKILL.md     │ │ SKILL.md   │ │   │
│  │  └──────┬───────┘ └──────┬───────┘ └──────┬───────┘ └─────┬──────┘ │   │
│  │         │                │                │               │         │   │
│  └─────────┼────────────────┼────────────────┼───────────────┼─────────┘   │
│            │                │                │               │              │
│            ▼                ▼                ▼               ▼              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │              Telemetry MCP Server (Wraps Everything)                │   │
│  │                                                                      │   │
│  │  • Intercepts all tool calls (Claude built-in + ASP)                │   │
│  │  • Logs: latency, tokens, cost, defects                             │   │
│  │  • Routes to Langfuse + SQLite                                      │   │
│  │  • Provides bootstrap data for PROBE-AI                             │   │
│  └──────────────────────────────┬──────────────────────────────────────┘   │
│                                 │                                           │
└─────────────────────────────────┼───────────────────────────────────────────┘
                                  │
          ┌───────────────────────┼───────────────────────┐
          ▼                       ▼                       ▼
┌──────────────────┐   ┌──────────────────┐   ┌──────────────────┐
│    Langfuse      │   │     SQLite       │   │   Anthropic API  │
│  (Real-time UI)  │   │  (Persistence)   │   │   (LLM Calls)    │
└──────────────────┘   └──────────────────┘   └──────────────────┘
```

### ASP Skills Directory Structure

```
.claude/skills/
├── asp-planning/
│   ├── SKILL.md                    # Planning methodology + telemetry hooks
│   ├── prompts/
│   │   └── decomposition-checklist.md
│   └── templates/
│       └── project-plan-template.json
│
├── asp-design/
│   ├── SKILL.md                    # Design patterns + architecture guidelines
│   ├── prompts/
│   │   └── design-principles.md
│   └── templates/
│       └── design-spec-template.json
│
├── asp-code-generation/
│   ├── SKILL.md                    # Code generation standards
│   ├── prompts/
│   │   ├── coding-standards.md
│   │   └── security-guidelines.md
│   └── scripts/
│       └── inject-telemetry.py
│
├── asp-code-review/
│   ├── SKILL.md                    # Review checklist + severity definitions
│   └── prompts/
│       ├── owasp-top-10.md
│       └── performance-checklist.md
│
├── asp-testing/
│   ├── SKILL.md                    # Test generation methodology
│   └── prompts/
│       └── coverage-requirements.md
│
└── asp-postmortem/
    ├── SKILL.md                    # Defect analysis methodology
    └── prompts/
        └── root-cause-template.md
```

### Example Skill: asp-planning

```yaml
# .claude/skills/asp-planning/SKILL.md
---
name: asp-planning
description: |
  Decomposes complex tasks into structured project plans using TSP methodology.
  Use when starting a new feature, fixing a complex bug, or planning refactoring.
  Outputs: ProjectPlan with phases, estimates, and risk assessment.
---

# ASP Planning Skill

## When to Use
- New feature requests requiring multiple files
- Bug fixes spanning multiple components
- Refactoring with architectural implications
- Any task with unclear scope

## Methodology

Follow the Team Software Process (TSP) decomposition:

1. **Requirements Analysis**
   - Extract functional requirements
   - Identify non-functional constraints
   - List acceptance criteria

2. **Task Decomposition**
   - Break into phases: Design → Code → Test → Review
   - Estimate complexity (1-10 scale)
   - Identify dependencies

3. **Risk Assessment**
   - Technical risks (new technology, complexity)
   - Schedule risks (dependencies, unknowns)
   - Quality risks (test coverage gaps)

## Telemetry Requirements

Every planning execution must track:
- `latency_ms`: Total planning time
- `input_tokens`: Tokens consumed reading context
- `output_tokens`: Tokens in generated plan
- `complexity_score`: Semantic complexity (1-10)
- `subtask_count`: Number of decomposed tasks

Call the telemetry MCP tool:
```
mcp__telemetry__log_agent_execution(
  agent_role="Planning",
  task_id=current_task_id,
  metrics={...}
)
```

## Output Format

```json
{
  "task_id": "TASK-001",
  "phases": [
    {
      "name": "Design",
      "subtasks": [...],
      "estimated_hours": 2,
      "complexity": 4
    }
  ],
  "risks": [...],
  "acceptance_criteria": [...]
}
```
```

### Telemetry MCP Server

The key to unified telemetry: an MCP server that wraps all tool calls.

```python
# src/asp/mcp/telemetry_server.py
"""
Telemetry MCP Server for unified observability.

Intercepts and logs all tool executions with cost/quality metrics.
Routes to Langfuse (real-time) and SQLite (persistence).
"""

from claude_agent_sdk import tool, create_sdk_mcp_server
from asp.telemetry.langfuse_client import langfuse
from asp.telemetry.sqlite_store import TelemetryStore
import time
from typing import Any
from contextlib import contextmanager


class TelemetryContext:
    """Thread-local telemetry context for nested tool calls."""
    _current_span = None
    _task_id = None


@contextmanager
def telemetry_span(tool_name: str, task_id: str, metadata: dict):
    """Create a telemetry span for tool execution."""
    start_time = time.time()
    span = langfuse.trace(
        name=f"Tool.{tool_name}",
        metadata={
            "task_id": task_id,
            "tool_name": tool_name,
            **metadata
        }
    )

    try:
        yield span
    finally:
        duration_ms = (time.time() - start_time) * 1000
        span.end(metadata={"duration_ms": duration_ms})


@tool(
    name="log_agent_execution",
    description="Log agent/skill execution metrics for telemetry",
    schema={
        "agent_role": {"type": "string", "description": "Planning|Design|Code|Review|Test|Postmortem"},
        "task_id": {"type": "string"},
        "metrics": {
            "type": "object",
            "properties": {
                "latency_ms": {"type": "number"},
                "input_tokens": {"type": "number"},
                "output_tokens": {"type": "number"},
                "cost_usd": {"type": "number"},
                "complexity_score": {"type": "number"},
            }
        }
    }
)
async def log_agent_execution(args: dict) -> dict:
    """Log agent execution to Langfuse + SQLite."""
    store = TelemetryStore()

    # Log to Langfuse (real-time visualization)
    langfuse.trace(
        name=f"Agent.{args['agent_role']}",
        metadata={
            "task_id": args["task_id"],
            **args["metrics"]
        }
    )

    # Log to SQLite (persistence for PROBE-AI)
    store.log_cost_vector(
        task_id=args["task_id"],
        agent_role=args["agent_role"],
        latency_ms=args["metrics"].get("latency_ms", 0),
        input_tokens=args["metrics"].get("input_tokens", 0),
        output_tokens=args["metrics"].get("output_tokens", 0),
        cost_usd=args["metrics"].get("cost_usd", 0),
    )

    return {
        "content": [{
            "type": "text",
            "text": f"Logged metrics for {args['agent_role']} on {args['task_id']}"
        }]
    }


@tool(
    name="log_defect",
    description="Log a defect discovered during execution",
    schema={
        "task_id": {"type": "string"},
        "defect_type": {"type": "string", "description": "bug|security|performance|design"},
        "severity": {"type": "string", "description": "low|medium|high|critical"},
        "phase_injected": {"type": "string", "description": "Which phase introduced the defect"},
        "phase_detected": {"type": "string", "description": "Which phase found the defect"},
        "description": {"type": "string"},
    }
)
async def log_defect(args: dict) -> dict:
    """Log defect to telemetry for quality tracking."""
    store = TelemetryStore()

    store.log_defect(
        task_id=args["task_id"],
        defect_type=args["defect_type"],
        severity=args["severity"],
        phase_injected=args["phase_injected"],
        phase_detected=args["phase_detected"],
        description=args["description"],
    )

    langfuse.trace(
        name="Defect",
        metadata=args,
        level="warning" if args["severity"] in ["low", "medium"] else "error"
    )

    return {
        "content": [{
            "type": "text",
            "text": f"Logged {args['severity']} defect: {args['defect_type']}"
        }]
    }


@tool(
    name="wrap_tool_call",
    description="Wrap any tool call with telemetry tracking",
    schema={
        "tool_name": {"type": "string"},
        "task_id": {"type": "string"},
        "input_summary": {"type": "string"},
    }
)
async def wrap_tool_call(args: dict) -> dict:
    """
    Start telemetry tracking for a tool call.
    Call this BEFORE executing any Claude built-in tool.
    """
    TelemetryContext._current_span = langfuse.trace(
        name=f"Tool.{args['tool_name']}",
        metadata={
            "task_id": args["task_id"],
            "input_summary": args["input_summary"][:200],
        }
    )
    TelemetryContext._task_id = args["task_id"]

    return {
        "content": [{
            "type": "text",
            "text": f"Started telemetry for {args['tool_name']}"
        }]
    }


@tool(
    name="end_tool_call",
    description="End telemetry tracking for a tool call",
    schema={
        "tool_name": {"type": "string"},
        "success": {"type": "boolean"},
        "output_summary": {"type": "string"},
    }
)
async def end_tool_call(args: dict) -> dict:
    """
    End telemetry tracking for a tool call.
    Call this AFTER executing any Claude built-in tool.
    """
    if TelemetryContext._current_span:
        TelemetryContext._current_span.end(
            metadata={
                "success": args["success"],
                "output_summary": args["output_summary"][:200],
            }
        )
        TelemetryContext._current_span = None

    return {
        "content": [{
            "type": "text",
            "text": f"Ended telemetry for {args['tool_name']}"
        }]
    }


# Create the MCP server
asp_telemetry_server = create_sdk_mcp_server(
    name="asp-telemetry",
    version="1.0.0",
    tools=[
        log_agent_execution,
        log_defect,
        wrap_tool_call,
        end_tool_call,
    ],
)
```

### Skills Configuration with Telemetry

```yaml
# .claude/settings.yaml
skills:
  enabled: true
  auto_discover: true  # Find skills in .claude/skills/

mcp_servers:
  # Telemetry server wraps all tool calls
  asp-telemetry:
    type: in_process
    module: asp.mcp.telemetry_server
    server: asp_telemetry_server

  # ASP agents exposed as MCP tools (for complex logic)
  asp-agents:
    type: in_process
    module: asp.mcp.agents_server
    server: asp_agents_server

# Hook telemetry into all tool calls
hooks:
  pre_tool_call:
    - mcp__asp-telemetry__wrap_tool_call
  post_tool_call:
    - mcp__asp-telemetry__end_tool_call
```

### Unified Telemetry Flow

```
User Request: "Implement user authentication"
    │
    ▼
┌─────────────────────────────────────────────────────────────────┐
│  [asp-planning Skill]                                           │
│   ├─ Skill instructions injected into context                  │
│   ├─ Claude generates plan                                      │
│   ├─ Calls: mcp__asp-telemetry__log_agent_execution            │
│   │         {agent_role: "Planning", latency_ms: 2340, ...}    │
│   └─ Output: ProjectPlan.json                                   │
└─────────────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────────────┐
│  [asp-design Skill]                                             │
│   ├─ Design methodology injected                               │
│   ├─ Claude generates design spec                              │
│   ├─ Calls: mcp__asp-telemetry__log_agent_execution            │
│   └─ Output: DesignSpec.json                                    │
└─────────────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────────────┐
│  [asp-code-generation Skill]                                    │
│   ├─ Code standards injected                                   │
│   ├─ Claude uses Edit tool (wrapped by telemetry hook)         │
│   │   └─ pre_tool_call: wrap_tool_call("Edit", ...)           │
│   │   └─ post_tool_call: end_tool_call("Edit", success=true)  │
│   ├─ Calls: mcp__asp-telemetry__log_agent_execution            │
│   └─ Output: Generated code files                               │
└─────────────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────────────┐
│  [asp-code-review Skill]                                        │
│   ├─ Review checklist injected                                 │
│   ├─ Claude reviews generated code                             │
│   ├─ Found issue → Calls: mcp__asp-telemetry__log_defect       │
│   │               {defect_type: "security", severity: "high"}  │
│   ├─ Calls: mcp__asp-telemetry__log_agent_execution            │
│   └─ Output: ReviewReport.json                                  │
└─────────────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────────────┐
│  Telemetry Backends                                             │
│   ├─ Langfuse: Real-time trace visualization                   │
│   ├─ SQLite: asp_telemetry.db for PROBE-AI training           │
│   └─ Metrics: Cost vectors, defect logs, bootstrap data        │
└─────────────────────────────────────────────────────────────────┘
```

### Benefits of Skills + Telemetry Approach

| Benefit | Description |
|---------|-------------|
| **Unified Observability** | All tools (Claude built-in + ASP) tracked in one place |
| **Progressive Disclosure** | Skills load only when needed (~100 tokens metadata) |
| **Methodology Preservation** | ASP's TSP methodology encoded in skill instructions |
| **Bootstrap Data** | Telemetry feeds PROBE-AI estimation model |
| **Defect Tracking** | Phase-aware defect logging (injected vs detected) |
| **Cost Transparency** | Every LLM call and tool execution has cost metrics |

### Implementation Plan: Skills + Telemetry

| Phase | Task | Effort |
|-------|------|--------|
| E1 | Create telemetry MCP server | Medium |
| E2 | Convert Planning agent to Skill | Medium |
| E3 | Convert remaining agents to Skills | High |
| E4 | Add pre/post tool hooks for telemetry | Medium |
| E5 | Integrate with existing Langfuse/SQLite | Low |
| E6 | Test unified telemetry flow | High |

## Risks and Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| SDK API changes | Breaking changes in provider | Pin SDK version, integration tests |
| Node.js dependency | Additional runtime requirement | Document clearly, make optional |
| Subscription rate limits | Usage caps hit during heavy use | Fall back to API, warn user |
| Tool permission conflicts | SDK tools conflict with ASP tools | Disable SDK tools by default |
| Context window limits | Long sessions fail | Use SDK's built-in compaction |
| Cost surprises | API users unexpectedly billed | Clear auth mode indication |

## Alternatives Considered

### Alternative 1: Direct CLI Subprocess

Invoke `claude` CLI as subprocess:

```python
import subprocess
import json

async def call_claude_cli(prompt: str) -> str:
    proc = await asyncio.create_subprocess_exec(
        "claude", "-p", prompt, "--output-format", "json",
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await proc.communicate()
    result = json.loads(stdout)
    return result["messages"][-1]["content"]
```

**Rejected because:**
- Limited control over execution
- Difficult to stream responses
- No access to intermediate steps
- Subprocess overhead per call

### Alternative 2: Keep API-Only

Continue using direct Anthropic API:

**Rejected because:**
- No subscription billing support
- Users pay API costs even with Pro subscription
- Missing context management features
- Duplicates SDK capabilities

### Alternative 3: Use LiteLLM/aisuite

Use third-party abstraction libraries:

**Considered but deferred:**
- Good for multi-provider support (ADR 010)
- Doesn't provide Claude SDK's agentic features
- Different goal than this ADR

## Consequences

### Positive

- **Cost Savings** - Subscription users avoid API charges
- **Feature Leverage** - Built-in context management, session persistence
- **Future-Proof** - Aligned with Anthropic's agent architecture
- **Simpler Tool Execution** - SDK handles file/bash operations (opt-in)

### Negative

- **New Dependency** - Node.js runtime required for SDK
- **Learning Curve** - Team needs SDK familiarity
- **Version Coupling** - Tied to SDK release cycle
- **Complexity** - Another integration path to maintain

### Neutral

- **Authentication Modes** - More options, but also more to document
- **Tool Overlap** - SDK tools overlap with ASP tools (can be managed)

## Open Questions

1. **Session Persistence** - Should ASP persist SDK sessions for long-running tasks?

2. **Tool Delegation** - Which tasks benefit from SDK tool execution vs ASP agents?

3. **Error Recovery** - How should ASP handle SDK-specific errors?

4. **Telemetry** - How do we integrate SDK usage with ASP's Langfuse telemetry?

5. **Model Selection** - SDK uses Sonnet by default; should ASP override to Haiku for cost?

## References

- [Claude Agent SDK GitHub](https://github.com/anthropics/claude-agent-sdk-python)
- [Claude Agent SDK Documentation](https://docs.claude.com/en/api/agent-sdk/overview)
- [Claude Code CLI Reference](https://docs.anthropic.com/en/docs/claude-code/cli-reference)
- [Building Agents with Claude Agent SDK](https://www.anthropic.com/engineering/building-agents-with-the-claude-agent-sdk)
- [Claude Pricing](https://claude.com/pricing)
- [ADR 008: Async Process Architecture](./ADR_008_async_process_architecture.md)
- [ADR 010: Multi-LLM Provider Support](./ADR_010_multi_llm_provider_support.md)

---

**Status:** Draft
**Next Steps:**
1. Review and discuss options
2. Decide on phased approach
3. Begin Phase 1 implementation if approved
