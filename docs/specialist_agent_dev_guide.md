# Specialist Agent Developer Guide

**Version:** 1.0.0
**Last Updated:** November 2025

This guide explains the architecture of the **Specialist Review Agents** and how to implement new ones. These agents are orchestrated by the `DesignReviewOrchestrator` to provide parallel, domain-specific feedback.

## Architecture

Specialist agents are located in `src/asp/agents/reviews/`. They all inherit from a common base or implement a standard interface.

### The Specialist Interface

Each specialist is a self-contained agent that focuses on **one** quality dimension (e.g., Security, Performance).

**Input:** `DesignSpecification`
**Output:** List of `DesignIssue` objects and `ImprovementSuggestion` objects.

## Existing Specialists

1.  **SecurityReviewAgent:** Checks for OWASP vulnerabilities, auth flaws.
2.  **PerformanceReviewAgent:** Checks for N+1 queries, indexing, caching.
3.  **DataIntegrityReviewAgent:** Checks schema normalization, foreign keys.
4.  **MaintainabilityReviewAgent:** Checks coupling, cohesion, naming.
5.  **ArchitectureReviewAgent:** Checks patterns, layering, SOLID principles.
6.  **APIDesignReviewAgent:** Checks REST conventions, error handling.

*(Note: The "12 Specialist Agents" mentioned in older docs refers to the planned expansion. Currently, 6 are implemented.)*

## Creating a New Specialist

To add a new specialist (e.g., `AccessibilityReviewAgent`), follow these steps:

### 1. Create the Class

Create `src/asp/agents/reviews/accessibility_review_agent.py`.

```python
from asp.agents.base_agent import BaseAgent
from asp.models.design import DesignSpecification
from asp.models.design_review import DesignIssue, ImprovementSuggestion

class AccessibilityReviewAgent(BaseAgent):
    def review(self, design: DesignSpecification) -> tuple[list[DesignIssue], list[ImprovementSuggestion]]:
        # Implementation here
        pass
```

### 2. Create the Prompt

Create `src/asp/prompts/accessibility_review_agent_v1.txt`.

Focus the prompt *only* on accessibility rules (WCAG, contrast, screen readers).

### 3. Implement `review()` Method

1.  Load the prompt.
2.  Format it with the design spec.
3.  Call `self.call_llm()`.
4.  Parse the JSON response into `DesignIssue` objects.
5.  Return the lists.

### 4. Register with Orchestrator

Open `src/asp/agents/design_review_orchestrator.py` and add the new agent to the parallel execution list.

```python
# In execute() method
specialists = [
    SecurityReviewAgent(),
    PerformanceReviewAgent(),
    # ...
    AccessibilityReviewAgent() # Add this
]
```

## Testing

1.  **Unit Test:** Create `tests/unit/test_agents/reviews/test_accessibility_review_agent.py`. Mock the LLM response and verify it parses correctly.
2.  **Integration Test:** Run the full `DesignReviewOrchestrator` and ensure the new category appears in the report.

## Best Practices

-   **Narrow Scope:** Don't let the Accessibility agent comment on SQL performance.
-   **Structured Output:** Ensure the prompt enforces the `DesignIssue` JSON schema strictly.
-   **Severity Calibration:** Define what "Critical" means for your domain (e.g., "Site unusable for screen readers").
