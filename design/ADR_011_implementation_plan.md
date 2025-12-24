# ADR 011 Implementation Plan: Container-First Approach

**Created:** 2025-12-24
**Session:** 20251224.2
**Status:** Draft - Awaiting Approval

## Overview

This plan implements ADR 011 (Claude CLI/Agent SDK Integration) with a **container-first approach** that keeps Node.js isolated from the host environment.

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         ASP Host Environment                             │
│                         (Python only, no Node.js)                        │
│                                                                          │
│  ┌─────────────────┐         HTTP (localhost:8080)    ┌────────────────┐│
│  │   ASP Agent     │ ◄───────────────────────────────►│  Claude SDK    ││
│  │                 │                                   │  Container     ││
│  │  LLMClient      │                                   │                ││
│  │       │         │                                   │  - Node.js 18+ ││
│  │       ▼         │                                   │  - Python 3.10+││
│  │  ClaudeSDK      │                                   │  - claude-agent││
│  │  Container      │                                   │    -sdk        ││
│  │  Provider       │                                   │  - FastAPI     ││
│  └─────────────────┘                                   └────────────────┘│
│                                                               │          │
└───────────────────────────────────────────────────────────────┼──────────┘
                                                                │
                                                                ▼
                                                       ┌────────────────┐
                                                       │  Anthropic API │
                                                       │  (or subscription)│
                                                       └────────────────┘
```

## Implementation Phases

### Phase 1: Container Service (2 sessions)

Create a containerized Claude SDK service that exposes a REST API.

#### 1.1 Create Directory Structure

```
docker/
└── claude-sdk-service/
    ├── Dockerfile
    ├── sdk_service.py      # FastAPI wrapper
    ├── requirements.txt    # Python deps for container
    └── healthcheck.py      # Simple health check script
```

#### 1.2 Create Dockerfile

**File:** `docker/claude-sdk-service/Dockerfile`

```dockerfile
FROM node:18-slim

# Install Python
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python3 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install Claude SDK and FastAPI
RUN pip install --no-cache-dir \
    claude-agent-sdk \
    fastapi \
    uvicorn[standard] \
    httpx

# Create app directory
WORKDIR /app
COPY sdk_service.py .
COPY healthcheck.py .

# Expose REST API port
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s \
  CMD python3 /app/healthcheck.py

# Run FastAPI service
CMD ["uvicorn", "sdk_service:app", "--host", "0.0.0.0", "--port", "8080"]
```

#### 1.3 Create SDK Service (FastAPI)

**File:** `docker/claude-sdk-service/sdk_service.py`

REST API wrapper for Claude Agent SDK:

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/health` | GET | Health check |
| `/v1/complete` | POST | Simple completion (no tools) |
| `/v1/info` | GET | SDK version and capabilities |

Key features:
- Async request handling
- Structured request/response models
- Error translation to HTTP status codes
- Token usage tracking
- Support for both API key and subscription auth

#### 1.4 Create Docker Compose

**File:** `docker-compose.claude-sdk.yaml`

```yaml
version: '3.8'

services:
  claude-sdk:
    build:
      context: ./docker/claude-sdk-service
    ports:
      - "8080:8080"
    environment:
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
    volumes:
      # For subscription auth
      - ~/.claude:/root/.claude:ro
    healthcheck:
      test: ["CMD", "python3", "/app/healthcheck.py"]
      interval: 30s
      timeout: 10s
      retries: 3
    deploy:
      resources:
        limits:
          memory: 1G
          cpus: '1.0'
```

#### 1.5 Deliverables

| Deliverable | Description |
|-------------|-------------|
| `docker/claude-sdk-service/Dockerfile` | Container definition |
| `docker/claude-sdk-service/sdk_service.py` | FastAPI REST wrapper |
| `docker/claude-sdk-service/requirements.txt` | Python dependencies |
| `docker/claude-sdk-service/healthcheck.py` | Health check script |
| `docker-compose.claude-sdk.yaml` | Compose configuration |

---

### Phase 2: Provider Implementation (1-2 sessions)

Create the ASP provider that calls the containerized service.

#### 2.1 Create Container Provider

**File:** `src/asp/providers/claude_sdk_container_provider.py`

```python
class ClaudeSDKContainerProvider(LLMProvider):
    """
    Claude SDK provider using containerized service.

    No Node.js on host - all SDK operations happen in container.
    """

    name = "claude_sdk"

    # Configuration
    DEFAULT_SERVICE_URL = "http://localhost:8080"
    DEFAULT_TIMEOUT = 120.0

    def __init__(self, config: ProviderConfig | None = None):
        ...

    async def call_async(self, prompt: str, **kwargs) -> LLMResponse:
        """Call containerized SDK service via HTTP."""
        ...

    def call(self, prompt: str, **kwargs) -> LLMResponse:
        """Sync wrapper."""
        ...

    async def health_check(self) -> bool:
        """Check if container service is running."""
        ...

    def estimate_cost(self, model: str, input_tokens: int, output_tokens: int) -> float:
        """Return 0 for subscription, calculate for API."""
        ...
```

#### 2.2 Register Provider

Update `src/asp/providers/registry.py`:

```python
# Register Claude SDK container provider
try:
    from asp.providers.claude_sdk_container_provider import ClaudeSDKContainerProvider
    cls.register("claude_sdk", ClaudeSDKContainerProvider)
except ImportError:
    logger.debug("ClaudeSDKContainerProvider not available")
```

#### 2.3 Add CLI Support

Update CLI to support `--provider claude_sdk`:

```bash
asp run --provider claude_sdk --model claude-sonnet-4-5 "task description"
```

#### 2.4 Deliverables

| Deliverable | Description |
|-------------|-------------|
| `src/asp/providers/claude_sdk_container_provider.py` | HTTP client provider |
| Registry update | Register new provider |
| CLI integration | `--provider claude_sdk` flag |
| Unit tests | Mock HTTP responses |

---

### Phase 3: Integration & Testing (1 session)

#### 3.1 Integration Tests

- Container startup/shutdown
- Health check verification
- Simple completion requests
- Error handling (container down, timeout)
- Authentication modes (API key, subscription)

#### 3.2 Documentation

- README for container deployment
- Configuration options
- Troubleshooting guide

#### 3.3 Deliverables

| Deliverable | Description |
|-------------|-------------|
| `tests/integration/test_claude_sdk_container.py` | Integration tests |
| `docs/claude_sdk_container.md` | Usage documentation |
| Updated ADR 011 | Mark Phase 1 complete |

---

### Phase 4: Tool Execution (Future, Optional)

If needed later, add SDK tool execution capability:

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/v1/agentic` | POST | Execute with tools enabled |
| `/v1/session` | POST | Create persistent session |
| `/v1/session/{id}` | GET | Get session state |

This phase would enable:
- SDK's Edit, Bash, Read tools
- Session persistence across requests
- Context compaction for long conversations

---

## Configuration

### Environment Variables

```bash
# Provider selection
ASP_LLM_PROVIDER=claude_sdk

# Container service URL
ASP_CLAUDE_SDK_URL=http://localhost:8080

# Authentication (passed to container)
ANTHROPIC_API_KEY=sk-ant-...  # For API billing
# OR mount ~/.claude for subscription auth
```

### Config File

```yaml
# .asp/config.yaml
llm:
  provider: claude_sdk

  claude_sdk:
    service_url: http://localhost:8080
    timeout: 120
    retries: 3

    # Container management
    auto_start: false  # Require manual docker-compose up
```

---

## Task Checklist

### Phase 1: Container Service
- [ ] Create `docker/claude-sdk-service/` directory
- [ ] Write Dockerfile with Node.js + Python
- [ ] Implement `sdk_service.py` FastAPI wrapper
- [ ] Create health check script
- [ ] Write `docker-compose.claude-sdk.yaml`
- [ ] Test container builds and runs
- [ ] Verify SDK calls work from container

### Phase 2: Provider Implementation
- [ ] Create `ClaudeSDKContainerProvider` class
- [ ] Implement `call_async()` with httpx
- [ ] Implement `call()` sync wrapper
- [ ] Add `health_check()` method
- [ ] Implement `estimate_cost()` (0 for subscription)
- [ ] Register in `ProviderRegistry`
- [ ] Add `--provider claude_sdk` CLI support
- [ ] Write unit tests with mocked HTTP

### Phase 3: Integration & Testing
- [ ] Write integration tests
- [ ] Test with real container
- [ ] Create documentation
- [ ] Update ADR 011 status

---

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Container startup latency | Slow first request | Pre-warm container, health check before use |
| SDK API changes | Breaking changes | Pin SDK version in Dockerfile |
| Network issues | Request failures | Retry logic with exponential backoff |
| Container resource usage | Memory/CPU limits | Set resource limits in compose |
| Subscription auth in container | May not work headless | Document API key fallback |

---

## Success Criteria

1. **Container builds and runs** - `docker-compose up` works
2. **Health check passes** - `/health` returns 200
3. **Completion works** - `/v1/complete` returns LLM response
4. **Provider integrates** - `--provider claude_sdk` works in CLI
5. **No Node.js on host** - All Node.js is inside container
6. **Tests pass** - Unit and integration tests green

---

## Estimated Effort

| Phase | Sessions | Effort |
|-------|----------|--------|
| Phase 1: Container Service | 2 | Medium |
| Phase 2: Provider Implementation | 1-2 | Medium |
| Phase 3: Integration & Testing | 1 | Low-Medium |
| **Total** | **4-5 sessions** | |

---

## Next Steps

1. **Approve this plan** - Review and confirm approach
2. **Start Phase 1** - Create container service
3. **Validate SDK** - Confirm `claude-agent-sdk` works in container
