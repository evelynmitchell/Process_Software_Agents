# Documentation Improvement Tracker

This document tracks suggestions for improving the project's documentation.

## Open Items

### 1. Create a `CONTRIBUTING.md` File

A dedicated guide for contributors is a standard and very helpful convention. This would be the perfect place to centralize information for anyone looking to make a change. It could include:

- **A "First Time Setup" Checklist:** A clear, step-by-step list:
  1. Clone the repository.
  2. Run `uv sync --all-extras` to ensure all dependencies, including dev and test tools, are installed.
  3. Run `uv run python scripts/init_database.py` to set up the database.
  4. Run `uv run pytest -m "not e2e"` to get a baseline confirmation that the core tests are passing.
- **Guidance on Testing:** Explicitly mention that many `e2e` tests are expected to fail if API keys are not configured. This would prevent new contributors from thinking they've broken the build when they first run the full test suite.
- **Code Style and Conventions:** Briefly outline the project's conventions for code style, commit messages, and the PR process.

### 2. Clarify the Role of the `artifacts/` Directory

My biggest point of confusion was seeing the `artifacts/` directory in the `.gitignore` file but also seeing its contents being tracked by Git and modified by the test suite. This is an unconventional setup. A brief explanation in the `README.md` or the new `CONTRIBUTING.md` would be very helpful. It could clarify:

- **What** these files are (outputs from agent runs).
- **Why** they are tracked in Git (e.g., for historical analysis, reproducibility).
- **That running tests is expected to modify them**, and these modifications should be committed along with other changes.

### 3. Automate API Documentation

The project has many excellent Pydantic data models (e.g., `ProjectPlan`, `DesignSpecification`) that define the core data structures of the system. While the high-level documentation is great, developers would benefit from a detailed API reference.

Since the project already uses `mkdocs` and `mkdocstrings`, it would be relatively straightforward to create a new "API Reference" page in the documentation that automatically generates documentation from the Python docstrings and type hints in the `src/asp/models/` directory. This would create a "single source of truth" that is always up-to-date with the code.
