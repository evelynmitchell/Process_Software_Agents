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
