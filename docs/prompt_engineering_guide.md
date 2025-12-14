# Prompt Engineering Guide

**Version:** 1.0.0
**Last Updated:** November 2025

This guide documents the prompt engineering standards, versioning strategy, and modification process for the ASP platform.

## Directory Structure

All prompts are stored in `src/asp/prompts/`.

```
src/asp/prompts/
├── __init__.py
├── prompt_versioner.py          # Utility for loading prompts
├── planning_agent_v1_decomposition.txt
├── design_agent_v1_specification.txt
├── code_agent_v1_generation.txt
├── code_agent_v2_manifest.txt   # V2 indicates major structural change
├── ...
└── test_agent_v1_generation.txt
```

## Prompt Naming Convention

Prompts must follow the format:
`{agent_name}_v{version}_{action}.txt`

-   **agent_name:** `planning_agent`, `design_agent`, etc.
-   **version:** `v1`, `v2`, etc.
-   **action:** `decomposition`, `specification`, `review`, etc.

**Example:** `planning_agent_v1_decomposition.txt`

## Prompt Format

Prompts are text files that support Python `format()` style placeholders (e.g., `{task_id}`).

### Standard Sections

Every prompt should generally include:
1.  **Role Definition:** "You are the Planning Agent..."
2.  **Input Context:** "You are given a task description..."
3.  **Task Instructions:** Step-by-step logic.
4.  **Output Format:** Strict JSON schema definition.
5.  **Examples:** Few-shot examples (optional but recommended).

### Example Template

```text
You are the Planning Agent.
Your goal is to decompose a task into semantic units.

INPUT:
Task ID: {task_id}
Description: {description}

INSTRUCTIONS:
1. Analyze the description.
2. Break it down into testable units.
3. Assign complexity scores.

OUTPUT FORMAT:
Return a valid JSON object matching this schema:
{{
    "semantic_units": [
        {{
            "unit_id": "string",
            "title": "string",
            ...
        }}
    ]
}}
```

*Note: JSON braces `{}` must be escaped as `{{}}` when used in Python format strings.*

## Loading Prompts

Use the `BaseAgent.load_prompt` method or the `PromptVersioner` directly.

```python
# Inside an agent class
template = self.load_prompt("planning_agent_v1_decomposition")
prompt = self.format_prompt(template, task_id="123", description="Build login")
```

## Updating Prompts (Versioning)

We follow a **Immutable Prompt** policy for major releases.

1.  **Minor Tweaks:** If you are fixing a typo or clarifying an instruction without changing the input/output schema, you *may* edit the existing `v1` file.
2.  **Major Changes:** If you change the JSON schema, add new required inputs, or significantly alter the logic, you **must** create a new file (e.g., `_v2_`).
3.  **Update Code:** Update the agent code to reference the new prompt filename.

### Why Version?
-   **Reproducibility:** We need to know exactly which prompt generated a specific artifact.
-   **A/B Testing:** We can run different versions of agents against the same task to compare performance.

## Testing Prompts

Before committing a prompt change:
1.  **Run Unit Tests:** Ensure the agent can still parse the output.
2.  **Manual Verification:** Run the agent with `temperature=0.0` on a standard task (like "Build a JWT Auth System") and verify the quality.

## Best Practices

-   **Be Specific:** LLMs work best with unambiguous instructions.
-   **Enforce JSON:** Always explicitly describe the JSON structure and ask for "raw JSON without markdown formatting" (though `json_extraction` utility handles markdown fences).
-   **Limit Context:** Don't dump the entire codebase into the prompt if only one file is needed.
-   **Chain of Thought:** For complex logic, ask the model to "Think step-by-step" in a `scratchpad` field before outputting the final JSON.
