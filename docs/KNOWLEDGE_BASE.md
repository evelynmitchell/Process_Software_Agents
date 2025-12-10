# ASP Knowledge Base

This file contains "Evergreen" notes—verified facts, patterns, and solutions that are permanently relevant to the project.
**Source:** Distilled from Weekly Reflections and Session Summaries.
**Maintenance:** Review and update weekly.

## 1. Technical Patterns

### FastHTML & HTMX
- **Testing Gotcha (Monkeypatching):** When mocking functions in FastHTML routes, you must patch where the function is **imported** (e.g., `src.web.routes.product.get_tasks`), not where it is **defined** (e.g., `src.data.get_tasks`). Python imports copy references at import time.
- **HTML Testing:** Prefer `lxml` with XPath over regex for validating HTML responses. It is more robust to whitespace and attribute ordering changes.

### Agent Architecture
- **Input Validation:** Agents must explicitly validate the existence of input files/paths before starting their core logic to avoid failures deep in execution.
- **Tool Wrappers:** The pattern of "LLM Logic -> Tool Execution -> Result Parsing" is robust. Focus on refining the Tool Execution wrapper to handle CLI tool quirks (like `pytest` output parsing).

### Testing Strategy
- **Isolation:** Tests that modify state (files, DB) must use fixtures (like `isolated_data_layer`) to prevent leakage.
- **Mocking:** E2E mock responses must align strictly with Pydantic models. Schema mismatches are the #1 cause of E2E test failures.

## 2. Process & Workflow

### Development
- **Bulk Formatting:** Apply linting/formatting (black, isort) in a single dedicated commit, not incrementally.
- **Ephemeral Environments:** Test repositories created in `/tmp` do not need git commit signing.

### Telemetry (PROBE)
- **Defect Taxonomy:**
    - **Context/State Management:** Agents missing inputs.
    - **Path/File Handling:** Relative path issues.
    - **Tool Invocation:** Incorrect arguments to subprocesses.
