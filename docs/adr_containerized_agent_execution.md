# ADR: Containerized Agent Execution Architecture

## Status

Proposed

## Context

The ASP Platform currently supports two deployment modes:

1. **Local development** - Developers run agents via Python API on their host machine
2. **Web UI only** - Docker container serves the monitoring dashboard, but agents must run on host

Users have requested the ability to run agent pipelines entirely within Docker containers, enabling:
- Consistent execution environment across machines
- Easier deployment to cloud/CI environments
- Isolation from host system
- Reproducible builds

The key challenge is that ASP agents need to:
- Access target git repositories (read code, write changes, commit)
- Call external APIs (Anthropic, Langfuse)
- Write artifacts and telemetry to persistent storage
- Support Human-in-the-Loop (HITL) approval workflows

## Decision

Implement a **dual-container architecture** with separation of concerns:

| Container | Purpose | Lifecycle |
|-----------|---------|-----------|
| `asp-webui` | Monitoring dashboard, HITL approvals | Long-running daemon |
| `asp-agent-runner` | Execute agent pipelines on tasks | Per-task or long-running |

### Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│  Docker Compose                                                  │
│                                                                  │
│  ┌─────────────────────┐       ┌─────────────────────────────┐   │
│  │  asp-webui          │       │  asp-agent-runner           │   │
│  │                     │ HTTP  │                             │   │
│  │  - FastHTML UI      │◄─────►│  - TSPOrchestrator          │   │
│  │  - HITL approvals   │       │  - All 7 agents             │   │
│  │  - Port 8000        │       │  - Git operations           │   │
│  │                     │       │  - API calls                │   │
│  └──────────┬──────────┘       └──────────────┬──────────────┘   │
│             │                                 │                  │
│             └────────────┬────────────────────┘                  │
│                          ▼                                       │
│  Shared Volumes:                                                 │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐   │
│  │ ./data/         │  │ ./artifacts/    │  │ ./workspace/    │   │
│  │ SQLite DB       │  │ Agent outputs   │  │ Target repo(s)  │   │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘   │
└──────────────────────────────────────────────────────────────────┘
```

### Container Responsibilities

#### asp-webui (existing, minimal changes)
- Serve monitoring dashboard on port 8000
- Display agent status, costs, telemetry
- Provide HITL approval/rejection UI
- Read-only database access
- No API keys required

#### asp-agent-runner (new)
- Execute TSPOrchestrator and all agent pipelines
- Full read-write access to target git repository
- Call Anthropic API for LLM operations
- Call Langfuse API for telemetry
- Write artifacts to shared volume
- Write telemetry to shared database
- Git operations (clone, branch, commit, push)

### Shared Volumes

| Volume | Mount Point | asp-webui | asp-agent-runner |
|--------|-------------|-----------|------------------|
| `./data/` | `/app/data` | Read-only | Read-write |
| `./artifacts/` | `/app/artifacts` | Read-only | Read-write |
| `./workspace/` | `/workspace` | Not mounted | Read-write |

### Environment Variables

```yaml
# asp-agent-runner only
environment:
  - ANTHROPIC_API_KEY          # Required
  - LANGFUSE_PUBLIC_KEY        # Required
  - LANGFUSE_SECRET_KEY        # Required
  - LANGFUSE_HOST=https://cloud.langfuse.com
  - ASP_WORKSPACE=/workspace   # Target repo path
```

### Task Submission Options

Three patterns for submitting tasks to the agent runner:

#### Option A: CLI one-shot (simplest)
```bash
docker compose run --rm asp-agent-runner \
  python -m asp.cli run \
    --task-id "FEATURE-001" \
    --description "Add user authentication" \
    --repo /workspace
```

#### Option B: HTTP API (recommended for integration)
```bash
# Agent runner exposes REST API
curl -X POST http://asp-agent-runner:8080/tasks \
  -d '{"task_id": "FEATURE-001", "description": "Add user auth"}'
```

#### Option C: Message queue (for scale)
```yaml
services:
  redis:
    image: redis:alpine
  asp-agent-runner:
    # Polls Redis for tasks
```

### Git Repository Access

Two patterns for providing git access:

#### Pattern 1: Pre-cloned repository (simpler)
```yaml
volumes:
  - /path/to/my-project:/workspace
```
User clones repo on host, mounts into container.

#### Pattern 2: Clone inside container (more isolated)
```yaml
volumes:
  - ~/.ssh:/home/asp/.ssh:ro           # SSH keys
  - ~/.gitconfig:/home/asp/.gitconfig:ro
environment:
  - GIT_REPO_URL=git@github.com:user/repo.git
```
Agent runner clones repo at startup or per-task.

### HITL Integration

When an agent requires human approval:

1. Agent runner writes approval request to database
2. Agent runner polls database for approval status (or blocks)
3. Web UI displays pending approvals
4. User clicks Approve/Reject in Web UI
5. Web UI writes decision to database
6. Agent runner detects approval, continues execution

Alternative: WebSocket connection between containers for real-time notifications.

## Consequences

### Positive

1. **Consistent environment** - Same container runs in dev, CI, and production
2. **No host dependencies** - Users only need Docker, not Python/uv
3. **Isolation** - Agent operations don't affect host system
4. **Reproducibility** - Locked dependencies via uv.lock
5. **Scalability path** - Can run multiple agent-runner instances
6. **Security** - API keys isolated to agent container, not exposed to web UI

### Negative

1. **Complexity** - Two containers instead of one, inter-container communication
2. **Git credential management** - SSH keys or tokens must be mounted/configured
3. **File permissions** - Container user vs host user for mounted volumes
4. **HITL latency** - Polling-based approval adds delay vs direct integration
5. **Debugging harder** - Can't just run Python directly, need to exec into container

### Neutral

1. **Database choice** - SQLite works for single agent-runner; PostgreSQL needed for multiple concurrent runners
2. **Build time** - Agent container is larger (~500MB) due to full dependencies

## Implementation Plan

### Phase 1: Agent Runner Container
- [ ] Create `Dockerfile.agents` with full dependencies
- [ ] Add git and SSH client to container
- [ ] Create `asp.cli` module for command-line task execution
- [ ] Update `docker-compose.webui.yml` to include agent-runner service
- [ ] Document volume mounts and environment variables

### Phase 2: Inter-Container Communication
- [ ] Define HITL approval protocol (database polling or WebSocket)
- [ ] Add task status API to Web UI
- [ ] Implement approval polling in agent runner

### Phase 3: Task Submission API (optional)
- [ ] Add HTTP API to agent runner for task submission
- [ ] Add task queue support (Redis or database-backed)
- [ ] Support multiple concurrent agent runners

## Alternatives Considered

### Alternative 1: Single container with everything
Run both Web UI and agent execution in one container.

**Rejected because:**
- Conflates monitoring with execution
- Can't scale Web UI separately from agents
- Harder to secure (Web UI doesn't need API keys)

### Alternative 2: Host-only execution (current state)
Keep agents on host, only Web UI in Docker.

**Acceptable for:**
- Development workflows
- Users comfortable with Python/uv

**Insufficient for:**
- CI/CD pipelines
- Cloud deployment
- Users who want pure Docker workflow

### Alternative 3: Kubernetes-native
Design for Kubernetes from the start with Jobs, Services, etc.

**Deferred because:**
- Adds significant complexity
- Docker Compose covers 80% of use cases
- Can migrate to K8s later with minimal changes

## References

- [Docker Compose documentation](https://docs.docker.com/compose/)
- [Existing Dockerfile.webui](../Dockerfile.webui)
- [TSPOrchestrator implementation](../src/asp/orchestrators/)
- [HITL Integration Guide](./HITL_Integration.md)
