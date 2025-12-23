# ADR 014: Web UI Deprecation

**Status:** Draft
**Date:** 2025-12-21
**Session:** 20251221.2
**Deciders:** User, Claude

## Context and Problem Statement

The ASP project includes a **FastHTML-based web UI** that provides dashboards for monitoring agent execution, task tracking, and telemetry visualization. However, maintaining this UI adds complexity and the functionality can be better served by:

1. **GitHub Issues + Beads** - Already integrated for task/issue tracking
2. **Prometheus + Grafana** - Industry-standard telemetry stack with superior visualization

### Current Web UI Inventory

| Component | Location | Lines | Purpose |
|-----------|----------|-------|---------|
| main.py | src/asp/web/ | 243 | Entry point, app init |
| api.py | src/asp/web/ | 705 | HITL approval API |
| data.py | src/asp/web/ | 1,529 | Telemetry data access |
| manager.py | src/asp/web/ | 1,439 | Manager dashboard (Sarah) |
| developer.py | src/asp/web/ | 873 | Developer dashboard (Alex) |
| product.py | src/asp/web/ | 918 | Product manager dashboard (Jordan) |
| kanban.py | src/asp/web/ | 298 | Kanban board |
| components.py | src/asp/web/ | 29 | Shared UI components |
| **Total Production** | | **~6,000** | |
| Unit tests | tests/unit/test_web/ | ~4,400 | |
| E2E tests | tests/e2e/web/ | 233 | |
| **Total Test** | | **~4,600** | |

### Features to Migrate

```
Current Web UI Features
┌─────────────────────────────────────────────────────────────┐
│  Task Tracking          │  Telemetry            │  HITL     │
│  ─────────────          │  ─────────            │  ────     │
│  • Kanban board         │  • Agent metrics      │  • Review │
│  • Task lists           │  • Cost tracking      │  • Approve│
│  • Status updates       │  • Phase yields       │  • Reject │
│  • Beads integration    │  • Success rates      │  • Defer  │
└─────────────────────────────────────────────────────────────┘
                              ↓ Migration ↓
┌─────────────────────────────────────────────────────────────┐
│  GitHub Issues + Beads  │  Prometheus/Grafana   │  CLI/API  │
│  ──────────────────────  │  ─────────────────    │  ───────  │
│  • Native kanban        │  • Time-series DB     │  • gh CLI │
│  • Issue tracking       │  • Custom dashboards  │  • MCP    │
│  • Labels/milestones    │  • Alerting           │  • Script │
│  • Project boards       │  • Long-term storage  │           │
└─────────────────────────────────────────────────────────────┘
```

## Decision Drivers

1. **Maintenance Burden** - Web UI requires separate Docker service, tests, CI/CD
2. **Duplicate Functionality** - GitHub Issues already provides task tracking
3. **Superior Tooling** - Prometheus/Grafana offer better telemetry than custom SQLite
4. **CLI-First Philosophy** - ASP is designed for CLI/agent workflows
5. **Code Cleanliness** - Removing ~10,600 lines reduces complexity
6. **Dependency Reduction** - Only `python-fasthtml` is unique to web UI

## Considered Options

### Option 1: Full Deprecation (Recommended)

Remove web UI entirely, migrate all functionality to external tools.

**Pros:**
- Cleanest codebase
- No maintenance overhead
- Better tooling for each function

**Cons:**
- One-time migration effort
- Loss of integrated view

### Option 2: Partial Deprecation

Keep HITL approval UI, deprecate dashboards.

**Pros:**
- Retains interactive approval workflow
- Smaller migration scope

**Cons:**
- Still requires Docker service
- Partial maintenance burden remains

### Option 3: Status Quo

Keep web UI as-is.

**Pros:**
- No migration work
- Existing features preserved

**Cons:**
- Ongoing maintenance burden
- Duplicates GitHub functionality
- Inferior telemetry compared to Prometheus/Grafana

## Decision

**Option 1: Full Deprecation** with phased migration.

## Migration Plan

### Phase 1: Telemetry Migration (Prometheus/Grafana)

**Current:** SQLite-based telemetry in `data.py`
**Target:** Prometheus metrics + Grafana dashboards

Tasks:
- [ ] Add Prometheus client to core agents
- [ ] Export metrics: task counts, durations, costs, success rates
- [ ] Create Grafana dashboard templates for each persona view
- [ ] Add docker-compose service for Prometheus/Grafana (optional local dev)

Metrics to export:
```
asp_task_total{status, agent_type}
asp_task_duration_seconds{agent_type}
asp_cost_dollars{agent_type, model}
asp_phase_yield{phase}
asp_agent_health{agent_id}
```

### Phase 2: Task Tracking Migration (GitHub Issues + Beads)

**Current:** Kanban in `kanban.py` with Beads integration
**Target:** GitHub Projects + existing Beads sync

Tasks:
- [ ] Verify `asp_beads_sync` MCP tool covers all kanban functionality
- [ ] Document GitHub Projects setup for ASP workflows
- [ ] Add labels for task metadata (complexity, priority, agent-assigned)

Note: Much of this already exists via ADR 009 Beads integration.

### Phase 3: HITL Approval Migration

**Current:** Web-based approve/reject/defer in `api.py`
**Target:** CLI + GitHub PR-based approvals

Options:
1. **CLI command:** `asp approve <task-id>` / `asp reject <task-id>`
2. **GitHub PR comments:** Agent creates PR, human reviews
3. **MCP tool:** `asp_approve` for Claude Code integration

Tasks:
- [ ] Implement CLI approval commands
- [ ] Add MCP tool for HITL approvals
- [ ] Document approval workflow

### Phase 4: Code Removal

Files to remove:
```
src/asp/web/                    # All 9 modules
tests/unit/test_web/            # All unit tests
tests/e2e/web/                  # E2E tests
tests/test_web_ui.py            # Integration test
Dockerfile.webui                # Container
docker-compose.webui.yml        # Compose config
.github/workflows/webui-e2e.yml # CI/CD
docs/web_ui_docker.md           # Docker docs
docs/web_ui_user_guide.md       # User guide
docs/proposals/web_ui_stack.md  # Original proposal
```

Dependencies to remove from pyproject.toml:
```
python-fasthtml
```

### Phase 5: Documentation Update

- [ ] Update README to reflect CLI-first approach
- [ ] Update KNOWLEDGE_BASE.md
- [ ] Archive web UI documentation

## Rollback Strategy

Git branch preservation:
```bash
git tag web-ui-archive-v1 HEAD  # Before removal
git branch archive/web-ui HEAD   # Preserve branch
```

If needed, web UI can be restored from archive branch.

## Success Criteria

- [ ] All telemetry metrics available in Prometheus
- [ ] Grafana dashboards replicate persona views
- [ ] HITL approvals work via CLI/MCP
- [ ] Beads sync handles all task tracking needs
- [ ] ~10,600 lines removed from codebase
- [ ] CI pipeline simplified (no E2E web tests)
- [ ] Docker footprint reduced (no webui service)

## Consequences

### Positive
- Cleaner codebase (~10,600 lines removed)
- Better telemetry (Prometheus > SQLite)
- Native GitHub integration for task tracking
- Reduced Docker complexity
- Fewer dependencies to maintain
- Faster CI (no E2E browser tests)

### Negative
- Migration effort required
- Loss of single integrated view
- Prometheus/Grafana setup required for telemetry
- Non-technical stakeholders may prefer web UI

### Neutral
- HITL workflow changes (web form → CLI/PR)
- Learning curve for Grafana dashboard creation

## Related ADRs

- **ADR 009:** Beads Planning Agent Integration (task tracking)
- **ADR 012:** MCP Server (CLI/tool integration)
- **ADR 013:** Logfire Migration (telemetry context)

## Open Questions

1. **Prometheus hosting:** Local docker-compose vs cloud service?
2. **Grafana dashboards:** Pre-built templates or user-created?
3. **HITL urgency:** Blocking CLI prompt vs async notification?
4. **Timeline:** Deprecation warning period before removal?

## References

- [Prometheus Python Client](https://github.com/prometheus/client_python)
- [Grafana Dashboard Provisioning](https://grafana.com/docs/grafana/latest/administration/provisioning/)
- [GitHub Projects](https://docs.github.com/en/issues/planning-and-tracking-with-projects)
