# Developer Guide: ASP Utilities

**Version:** 1.0.0
**Last Updated:** November 2025

This guide documents the shared utility modules in `src/asp/utils/`. Using these utilities ensures consistency across agents and reduces code duplication.

## Table of Contents

1. [Artifact I/O (`artifact_io.py`)](#artifact-io-artifact_iopy)
2. [Git Integration (`git_utils.py`)](#git-integration-git_utilspy)
3. [LLM Client (`llm_client.py`)](#llm-client-llm_clientpy)
4. [JSON Extraction (`json_extraction.py`)](#json-extraction-json_extractionpy)
5. [Markdown Rendering (`markdown_renderer.py`)](#markdown-rendering-markdown_rendererpy)
6. [Semantic Complexity (`semantic_complexity.py`)](#semantic-complexity-semantic_complexitypy)

---

## Artifact I/O (`artifact_io.py`)

Handles reading and writing agent artifacts (plans, designs, reports) to the filesystem in a structured way.

### Key Functions

#### `write_artifact_json(task_id, artifact_type, data)`
Writes a Pydantic model or dict to `artifacts/{task_id}/{artifact_type}.json`.

```python
from asp.utils.artifact_io import write_artifact_json
write_artifact_json("TASK-001", "plan", project_plan)
```

#### `write_artifact_markdown(task_id, artifact_type, markdown_content)`
Writes a markdown string to `artifacts/{task_id}/{artifact_type}.md`.

#### `write_generated_file(task_id, file)`
Writes a `GeneratedFile` object to its target path (e.g., `src/main.py`). Automatically handles directory creation.

#### `ensure_artifact_directory(task_id)`
Ensures `artifacts/{task_id}/` exists.

---

## Git Integration (`git_utils.py`)

Provides utilities for interacting with git, enabling the "Artifact Persistence" feature where every agent step is committed.

### Key Functions

#### `is_git_repository()`
Returns `True` if the current directory is a valid git repo.

#### `git_commit_artifact(task_id, agent_name, artifact_files)`
Stages the specified files and creates a commit with a standardized message:
`{agent_name}: Update artifacts for {task_id}`.

```python
from asp.utils.git_utils import git_commit_artifact
git_commit_artifact("TASK-001", "Planning Agent", ["artifacts/TASK-001/plan.json"])
```

---

## LLM Client (`llm_client.py`)

Standardized wrapper for LLM providers (currently Anthropic). Handles retry logic, token counting, and standardized error handling.

### Key Classes

#### `LLMClient`
The main client class.

```python
from asp.utils.llm_client import LLMClient
client = LLMClient(provider="anthropic")
response = client.chat(
    messages=[{"role": "user", "content": "Hello"}],
    model="claude-3-5-sonnet-20241022",
    temperature=0.0
)
```

---

## JSON Extraction (`json_extraction.py`)

Robust utilities for extracting JSON from LLM responses, which often contain markdown code fences or conversational text.

### Key Functions

#### `extract_json_from_text(text)`
Attempts to find and parse JSON within a string.
1. Looks for ````json ... ``` ` blocks.
2. Looks for `{ ... }` blocks.
3. Tries parsing the entire string.

```python
from asp.utils.json_extraction import extract_json_from_text
data = extract_json_from_text(llm_response_string)
```

---

## Markdown Rendering (`markdown_renderer.py`)

Converts Pydantic models (like `ProjectPlan` or `TestReport`) into human-readable Markdown for documentation.

### Key Functions

#### `render_plan_markdown(plan)`
#### `render_design_markdown(design_spec)`
#### `render_test_report_markdown(report)`

These functions use Jinja2 templates (implicitly or explicitly) to generate consistent, readable reports.

---

## Semantic Complexity (`semantic_complexity.py`)

Implements the **C1 Complexity Formula** defined in the PRD (Section 13.1).

### Key Classes

#### `ComplexityFactors`
Data class for holding the inputs:
- `api_interactions`
- `data_transformations`
- `logical_branches`
- `code_entities_modified`
- `novelty_multiplier`

### Key Functions

#### `calculate_semantic_complexity(factors)`
Returns a float representing the semantic complexity score.

```python
from asp.utils.semantic_complexity import ComplexityFactors, calculate_semantic_complexity

factors = ComplexityFactors(
    api_interactions=2,
    data_transformations=5,
    logical_branches=10,
    code_entities_modified=3,
    novelty_multiplier=1.0
)
score = calculate_semantic_complexity(factors)
```
