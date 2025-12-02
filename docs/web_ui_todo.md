# Web UI Integration Todo List

**Created:** 2025-12-02 (Session 5)
**Last Updated:** 2025-12-02 (Session 6)

## Status Summary

| Category | Total | Done | Remaining |
|----------|-------|------|-----------|
| Core Integration | 3 | 1 | 2 |
| Data & Metrics | 4 | 4 | 0 |
| Product Manager | 2 | 0 | 2 |
| Developer Features | 3 | 1 | 2 |
| Polish | 1 | 1 | 0 |
| **Total** | **13** | **7** | **6** |

---

## Core Integration (High Priority)

- [x] **Connect to HITL approval workflow** (Completed 2025-12-02)
  - Location: `src/asp/web/api.py`
  - `get_tasks_pending_approval()` now checks:
    - PIP artifacts with `hitl_status="pending"`
    - Git branches matching `review/*` pattern (quality gate reviews)
  - Added `get_pip_details()` for full PIP information
  - Added helper functions `_get_pending_pips()` and `_get_pending_review_branches()`

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

- [x] **Add cost tracking display** (Completed 2025-12-02)
  - Added cost metrics row to Manager dashboard:
    - API Cost (7 days), Total Tokens, Input Tokens, Output Tokens
  - Added "API Cost Tracking" section to Developer stats page:
    - Cost cards + Cost by Agent Role table
  - Uses `get_cost_breakdown()` from `data.py`
  - Gracefully handles empty telemetry database

- [x] **Add Sparklines/trend charts for metrics** (Completed 2025-12-02)
  - Added `generate_sparkline_svg()` function to `data.py`:
    - Creates inline SVG sparkline charts
    - Configurable width, height, color
    - Shows "No data" placeholder when empty
  - Added `get_daily_metrics()` for 7-day historical data
  - Integrated into Manager dashboard metric cards:
    - Cost sparkline (cyan)
    - Token sparkline (purple)
    - Task sparkline (green)

- [x] **Implement Phase Yield Analysis view for Manager** (Completed 2025-12-02)
  - Added `get_phase_yield_data()` function to `data.py`
  - Created `/manager/phase-yield` route with:
    - Summary metrics (Started, Completed, Yield Rate, Defects)
    - Phase flow visualization with progress bars
    - Phase transitions table with flow indicators
  - Color-coded phases (Planning=purple, Design=cyan, Code=amber, Test=green)
  - Real data from bootstrap results and design reviews

- [x] **Add Budget Cap controls for Manager dashboard** (Completed 2025-12-02 Session 6)
  - Added `/manager/budget` route with settings form
  - Added `/manager/budget-status` HTMX endpoint for auto-refresh
  - New data functions: `get_budget_settings()`, `save_budget_settings()`, `get_budget_status()`
  - Visual budget meters with progress bars (daily/monthly)
  - Color-coded status (green/yellow/red based on threshold)
  - Settings persist in `data/budget_settings.json`

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

- [x] **Implement Traceability view (artifact history)** (Completed 2025-12-02 Session 6)
  - New route: `/developer/task/{task_id}/trace`
  - Added `get_artifact_history()` function to `data.py`
  - Visual timeline showing development phases
  - Phase-colored indicators (Plan=purple, Design=cyan, Code=green, etc.)
  - Version tracking for artifacts
  - Content preview for text files
  - Telemetry data display (latency, tokens, cost)
  - Link from task detail page to trace view

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

- [x] **Add dark mode toggle** (Completed 2025-12-02 Session 6)
  - New component module: `src/asp/web/components.py`
  - `theme_toggle()` reusable button component
  - Uses PicoCSS native dark mode (`data-theme="dark"`)
  - Preference persisted in localStorage
  - Respects system preference on first visit
  - Added to all dashboards (Home, Manager, Developer, Product)

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
- `src/asp/web/components.py` - Shared UI components

### Database
- Telemetry: `/data/asp_telemetry.db`
- Tables: `agent_cost_vector`, `defect_log`, `task_metadata`, `bootstrap_metrics`
- Budget settings: `/data/budget_settings.json`
