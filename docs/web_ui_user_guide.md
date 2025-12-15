# Web UI - User Guide

**Version:** 1.0.0
**Last Updated:** December 14, 2025
**Status:** Production Ready

## Table of Contents

1. [Overview](#overview)
2. [Accessing the Dashboard](#accessing-the-dashboard)
3. [Persona-Based Views](#persona-based-views)
    - [Engineering Manager (Sarah)](#engineering-manager-sarah)
    - [Senior Developer (Alex)](#senior-developer-alex)
    - [Product Manager (Jordan)](#product-manager-jordan)
4. [Key Features](#key-features)
    - [Budget & Cost Tracking](#budget--cost-tracking)
    - [Live Task Execution](#live-task-execution)
    - [Artifact Traceability](#artifact-traceability)
    - [Dark Mode](#dark-mode)
5. [Troubleshooting](#troubleshooting)

---

## Overview

The ASP Web UI provides a centralized interface for monitoring and interacting with the Agentic Software Process. It is built using **FastHTML** and **HTMX**, offering a responsive, server-side rendered experience without the bloat of heavy JavaScript frameworks.

The UI is designed around three specific personas, each with a tailored dashboard to meet their specific needs.

---

## Accessing the Dashboard

1.  **Start the Server:**
    Run the following command from the repository root:
    ```bash
    python -m asp.web.main
    ```

2.  **Open Browser:**
    Navigate to `http://localhost:8000`

3.  **Authentication:**
    The system uses a simplified role-based access model. Select your persona from the landing page to enter the appropriate workspace.

---

## Persona-Based Views

### Engineering Manager (Sarah)
**Focus:** Operational Oversight, Budget, Quality.

-   **Overwatch Dashboard:** A high-level view of system health, active agents, and recent alerts.
-   **Phase Yield Analysis:** Visualizes the efficiency of the pipeline (Planning → Design → Code → Test).
-   **Budget Controls:** Set daily/monthly spending caps for LLM API usage.
-   **Agent Activity:** Real-time monitoring of active agents and their current tasks.

### Senior Developer (Alex)
**Focus:** Code Review, Debugging, Artifacts.

-   **Flow State Canvas:** A distraction-free environment for reviewing generated code.
-   **Task Traceability:** View the complete history of a task, from requirements to tested code.
-   **Diff Viewer:** Review code proposals with syntax highlighting.
-   **Agent Telemetry:** Inspect detailed logs of agent performance (latency, tokens).

### Product Manager (Jordan)
**Focus:** Roadmap, Features, Prediction.

-   **Prediction Engine:** Visualize project timelines and delivery probabilities.
-   **Feature Wizard:** Submit new feature requests directly to the agent pipeline.
-   **What-If Scenarios:** Simulate how changes in team capacity or budget affect the delivery schedule.
-   **Risk Analysis:** Monitor high-level risks and bottlenecks.

---

## Key Features

### Budget & Cost Tracking
Located in the **Manager Dashboard**, this feature allows you to:
-   View real-time API costs (last 7 days).
-   Set hard limits to prevent runaway costs.
-   Monitor token usage (Input vs. Output).

### Live Task Execution
See the agents work in real-time.
-   **Active Agents:** Pulsing indicators show which agents are currently executing.
-   **Progress Bars:** Track the status of long-running tasks across phases.
-   **Live Updates:** The UI refreshes automatically (every 5 seconds) using HTMX.

### Artifact Traceability
Located in the **Developer Dashboard**, this view links all outputs together.
-   Click on a Task ID to see its full lineage.
-   View the original Requirement -> Plan -> Design Spec -> Code -> Test Report.
-   Compare versions of artifacts across different runs.

### Dark Mode
Toggle between Light and Dark themes using the sun/moon icon in the top navigation bar. Your preference is saved automatically.

---

## Troubleshooting

### Server Won't Start
**Error:** `Address already in use`
**Solution:** Ensure no other process is running on port 8000.
```bash
lsof -i :8000
kill -9 <PID>
```

### No Data in Dashboards
**Cause:** The telemetry database might be empty.
**Solution:** Run the database initialization script or execute some tasks using the CLI to generate data.
```bash
python scripts/init_database.py
python -m asp.cli run --task "Example Task"
```

### Agents Not Updating
**Cause:** The browser stopped receiving HTMX updates.
**Solution:** Refresh the page. Ensure the backend server is still running.

---

**Note:** This UI is designed for local development and internal team use. It is not intended for public-facing deployment without additional security layers.
