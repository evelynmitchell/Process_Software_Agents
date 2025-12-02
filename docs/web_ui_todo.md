# Web UI Integration Todo List

**Created:** 2025-12-02 (Session 5)
**Last Updated:** 2025-12-02

## Status Summary

| Category | Total | Done | Remaining |
|----------|-------|------|-----------|
| Core Integration | 3 | 0 | 3 |
| Data & Metrics | 4 | 0 | 4 |
| Product Manager | 2 | 0 | 2 |
| Developer Features | 3 | 0 | 3 |
| Polish | 1 | 0 | 1 |
| **Total** | **13** | **0** | **13** |

---

## Core Integration (High Priority)

- [ ] **Connect to HITL approval workflow**
  - Location: `src/asp/web/api.py:247` (stub exists)
  - Connect `get_tasks_pending_approval()` to actual approval system
  - Display pending approvals in Manager dashboard

- [ ] **Connect to TSP orchestrator for live task execution**
  - Enable real-time task submission from web UI
  - Show live progress updates during execution
  - Integrate with existing orchestrator in `src/asp/orchestrator/`

- [ ] **Reach 80% test coverage**
  - Current: 78%
  - Target: 80%
  - Focus areas: uncovered branches in web modules

---

## Data & Metrics Display

- [ ] **Add cost tracking display**
  - Show `total_cost_usd` from telemetry
  - Show token usage (input/output)
  - Add to Manager and Developer dashboards
  - Data available via `get_cost_summary()` in `api.py`

- [ ] **Add Sparklines/trend charts for metrics**
  - 30-day trends for cost, quality, velocity
  - Use lightweight charting (Chart.js or inline SVG)
  - Target: Manager dashboard metric cards

- [ ] **Implement Phase Yield Analysis view for Manager**
  - Sankey diagram showing task flow through phases
  - Show "leakage" (rework) at each phase
  - Top defect sources (Pareto chart)
  - Location: New route `/manager/phase-yield`

- [ ] **Add Budget Cap controls for Manager dashboard**
  - Set daily/monthly spending limits
  - Visual budget meter ($spent / $limit)
  - Alert when approaching limit

---

## Product Manager Features

- [ ] **Implement Feature Wizard (conversational input)**
  - Planning Agent integration for requirement clarification
  - Real-time estimate updates as questions answered
  - Confidence intervals on time/cost estimates
  - Location: New route `/product/new-feature`

- [ ] **Add What-If scenario simulator for timeline**
  - Adjustable sliders: Team Capacity, Budget
  - Timeline reshapes based on inputs
  - Show probability of hitting deadlines
  - Location: New route `/product/timeline`

---

## Developer Features

- [ ] **Implement Traceability view (artifact history)**
  - Timeline showing: Plan v1 -> Design v1 -> Review -> Code v1
  - Link to actual artifact files
  - Show why changes were made
  - Location: Enhance `/developer/task/{id}`

- [ ] **Implement diff view for code changes**
  - Show agent proposals as unified diffs
  - Accept/Reject/Edit buttons
  - Monaco editor integration (optional)

- [ ] **Add agent presence indicators**
  - Show which agents are currently working
  - Visual indicator (avatar/cursor) when agent is active
  - Real-time updates via WebSocket or SSE

---

## Polish

- [ ] **Add dark mode toggle**
  - Manager design specifies dark mode default
  - Color scheme: Deep Navy (#0f172a), Neon accents
  - Persist preference in localStorage

---

## Already Completed (Prior Sessions)

- [x] Developer Dashboard (Alex) - basic implementation
- [x] Manager Dashboard (Sarah) - basic implementation
- [x] Product Dashboard (Jordan) - basic implementation
- [x] Telemetry database integration (`asp_telemetry.db`)
- [x] Dynamic agent health from telemetry
- [x] HTMX auto-refresh for activity feeds
- [x] 24 E2E Playwright tests passing
- [x] CI/CD workflow for E2E tests
- [x] Pre-commit hooks (black, isort, ruff, pylint)
- [x] Task detail view with artifacts
- [x] Agent statistics page

---

## Notes

### Design Documents
- Manager: `docs/ui_designs/01_manager_overwatch.md`
- Developer: `docs/ui_designs/02_developer_flow_canvas.md`
- Product: `docs/ui_designs/03_pm_prediction_engine.md`

### Key Files
- `src/asp/web/main.py` - App setup and routes
- `src/asp/web/data.py` - Data layer (telemetry integration)
- `src/asp/web/api.py` - API functions
- `src/asp/web/manager.py` - Manager routes
- `src/asp/web/developer.py` - Developer routes
- `src/asp/web/product.py` - Product routes

### Database
- Telemetry: `/data/asp_telemetry.db`
- Tables: `agent_cost_vector`, `defect_log`, `task_metadata`, `bootstrap_metrics`
