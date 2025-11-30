# Proposal: ASP Web UI Stack (No-NPM/WASM Focus)

**Date:** November 30, 2025
**Status:** Draft
**Author:** Claude (ASP Development Assistant)

## 1. Executive Summary

This proposal recommends the **FastHTML** stack for the ASP Platform's web interface.

FastHTML enables building modern, interactive web applications using **100% Python**. It leverages **HTMX** under the hood to eliminate the need for writing JavaScript, and it requires **no npm, no webpack, and no build step**. This aligns perfectly with the project's constraints (minimize JS, no npm) and existing infrastructure (Python/FastAPI).

## 2. Requirements & Constraints

*   **Existing Stack:** Python 3.12+, FastAPI.
*   **Constraints:**
    *   Avoid `npm`/`node_modules`.
    *   Minimize direct JavaScript authoring.
    *   Consider WASM (WebAssembly).
*   **Goal:** A maintainable foundation for ongoing improvement by Python developers.

## 3. Evaluated Options

### Option A: FastHTML (Recommended)
FastHTML is a new framework from the creators of fast.ai. It wraps Starlette (the core of FastAPI) and provides a Pythonic API for generating HTML and handling HTMX interactions.

*   **Pros:**
    *   **Pure Python:** Define UI components as Python functions.
    *   **No Build Step:** Run `python app.py`, and it works. No npm install.
    *   **HTMX Native:** Interactivity (updates without page reloads) is built-in.
    *   **FastAPI Compatible:** Can mount inside existing FastAPI apps or run standalone.
    *   **Performance:** Very fast (Starlette-based).
*   **Cons:**
    *   Newer ecosystem compared to Django/Flask.
*   **Verdict:** Best fit for "Not a web developer but want a good basis."

### Option B: FastAPI + Jinja2 + HTMX (Traditional)
The standard way to do "No-JS" with FastAPI. You write HTML templates (Jinja2) and add `hx-get`, `hx-post` attributes for interactivity.

*   **Pros:**
    *   Standard, battle-tested approach.
    *   Full control over HTML.
*   **Cons:**
    *   **Context Switching:** Must write HTML/CSS in separate files, then switch to Python for logic.
    *   **Boilerplate:** More verbose than FastHTML for simple components.
*   **Verdict:** Solid backup, but less "fun" and productive than FastHTML for Python devs.

### Option C: PyScript (WASM)
PyScript allows running Python code directly in the browser via WebAssembly.

*   **Pros:**
    *   True "Python in the browser".
    *   Access to client-side hardware/logic.
*   **Cons:**
    *   **Heavy Load Time:** Browsers must download the Python runtime (megabytes) on first load.
    *   **Complexity:** Mixing client-side Python and server-side Python can be confusing (they don't share memory).
    *   **Overkill:** For a dashboard/management tool, server-side rendering is usually snappier.
*   **Verdict:** Interesting tech, but likely adds unnecessary friction for this specific use case compared to HTMX.

## 4. Detailed Recommendation: FastHTML

We propose adopting **FastHTML** as the UI layer.

### 4.1 Architecture
The ASP Platform is currently a FastAPI application. FastHTML is built on Starlette, same as FastAPI. We can:
1.  **Mount** the FastHTML app as a sub-app within FastAPI (e.g., `/ui`).
2.  **Or** use FastHTML to serve the main UI and call the internal ASP agents directly (Python-to-Python).

### 4.2 Example Code Structure

No HTML files. No JS files. Just Python.

```python
# src/asp/ui/main.py
from fasthtml.common import *

app, rt = fast_app()

@rt('/')
def get():
    return Titled("ASP Overwatch",
        Div(
            H3("Active Agents"),
            # Dynamic content updates via HTMX
            Div(hx_get="/api/agent-status", hx_trigger="load, every 2s"),
            Class="dashboard-grid"
        )
    )

@rt('/api/agent-status')
def get_status():
    # Call internal Python logic directly
    status = get_agent_health()
    return Ul(*[Li(f"{name}: {state}") for name, state in status.items()])
```

### 4.3 Why this fits
1.  **Zero npm:** We install `python-fasthtml` via `uv`. That's it.
2.  **Minimize JS:** Interactions are declarative attributes (`hx_get`).
3.  **Ongoing Improvement:** Refactoring UI is just refactoring Python code. We can use classes, inheritance, and functions to manage UI complexity.

## 5. Implementation Plan

1.  **Dependency:** Add `python-fasthtml` to `pyproject.toml`.
2.  **Structure:** Create `src/asp/web/` to house the UI logic.
3.  **Prototype:** Build the "ASP Overwatch" dashboard (Engineering Manager view) first.
    *   Show active tasks.
    *   Show agent status (using the telemetry we just built).
4.  **Integration:** Ensure the UI runs smoothly alongside the existing API routes.

## 6. Questions for Discussion

1.  **Styling:** FastHTML includes PicoCSS by default (minimal, semantic). Is this acceptable, or do we need a specific design system (Tailwind, Bootstrap)? *Recommendation: Stick to PicoCSS or simple CSS to avoid npm/build steps.*
2.  **Deployment:** This stack runs on the same container/process as the backend. Does this align with your deployment model? (Yes, aligns with the container design).

## 7. Conclusion

FastHTML provides the most "Pythonic" path to a modern web UI without the accidental complexity of the JavaScript ecosystem. It allows us to build a rich, reactive "ASP Overwatch" dashboard while staying entirely within the team's core competency.
