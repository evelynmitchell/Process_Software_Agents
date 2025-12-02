# Web UI Integration Todo List

**Created:** 2025-12-02 (Session 5)
**Last Updated:** 2025-12-02 (Session 10)

## Status Summary

| Category | Total | Done | Remaining |
|----------|-------|------|-----------|
| Core Integration | 3 | 2 | 1 |
| Data & Metrics | 4 | 4 | 0 |
| Product Manager | 2 | 2 | 0 |
| Developer Features | 3 | 3 | 0 |
| Polish | 1 | 1 | 0 |
| **Total** | **13** | **12** | **1** |

---

## Core Integration (High Priority)

- [x] **Connect to HITL approval workflow** (Completed 2025-12-02)
  - Location: `src/asp/web/api.py`
  - `get_tasks_pending_approval()` now checks:
    - PIP artifacts with `hitl_status="pending"`
    - Git branches matching `review/*` pattern (quality gate reviews)
  - Added `get_pip_details()` for full PIP information
  - Added helper functions `_get_pending_pips()` and `_get_pending_review_branches()`

- [x] **Connect to TSP orchestrator for live task execution** (Completed 2025-12-02 Session 7)
  - Added task execution service in `data.py`:
    - `register_task_execution()` - Register new tasks
    - `update_task_progress()` - Update task progress by phase
    - `get_running_tasks()` - Get list of running tasks
    - `complete_task_execution()` - Mark task complete with result
  - Added Feature Wizard form at `/product/new-feature`
  - Added running tasks view at `/product/running`
  - Added execution monitoring in Manager dashboard
  - Live progress updates with HTMX (5-second refresh)

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

- [x] **Implement Feature Wizard (task submission)** (Completed 2025-12-02 Session 7)
  - New route: `/product/new-feature`
  - Task submission form with:
    - Task ID, Description, Requirements fields
    - Priority selection (Normal/High/Critical)
  - Submits task to in-memory execution queue
  - Shows confirmation with pipeline overview
  - Links to running tasks view

- [x] **Add What-If scenario simulator for timeline** (Completed 2025-12-02 Session 10)
  - New route: `/product/timeline`
  - Adjustable sliders for Team Capacity (0.25x-2.0x) and Budget (0.5x-2.0x)
  - Timeline visualization with progress bars for each feature
  - Delivery probability meters (on-time and early)
  - Risk summary cards (low/medium/high/completed)
  - Dynamic recommendations based on parameters
  - HTMX integration for real-time simulation updates
  - Data functions: `get_timeline_features()`, `simulate_timeline()`

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

- [x] **Implement diff view for code changes** (Completed 2025-12-02 Session 7)
  - New route: `/developer/task/{task_id}/diff`
  - Added `get_code_proposals()` function to `data.py`
  - Code display with syntax highlighting CSS
  - File header with line count and status
  - Action buttons (Approve/Reject/Edit) - visual placeholders
  - Link from task detail page to diff view

- [x] **Add agent presence indicators** (Completed 2025-12-02 Session 7)
  - Added `get_active_agents()` function to `data.py`
  - Manager dashboard: "Active Agents" section with:
    - Agent avatar/initial, name, current task
    - Pulsing green indicator (CSS animation)
    - HTMX auto-refresh every 5 seconds
  - Running tasks section with progress bars
  - Developer dashboard: `/developer/active-agents` endpoint

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
