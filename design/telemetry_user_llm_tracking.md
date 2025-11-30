# Design Doc: User + LLM Telemetry Tracking

**Date:** November 30, 2025
**Status:** Draft
**Author:** Claude (ASP Development Assistant)

## 1. Objective

Enable the ASP Platform to track and analyze the performance, cost, and defect rates of specific **User + LLM Model** combinations.

This allows answering questions such as:
- *"Does the Coding Agent produce fewer bugs when using Claude 3.5 Sonnet vs. GPT-4o?"*
- *"How does Developer X's velocity compare when using different copilot models?"*
- *"What is the cost efficiency of Model A vs. Model B for the Design phase?"*

## 2. Problem Statement

Current telemetry (`src/asp/telemetry/telemetry.py`) captures:
- `task_id`
- `agent_role`
- `llm_model` (optional, not always populated)
- `llm_provider`

It **missing**:
- `user_id`: Identity of the actor (Human Developer or specific Agent Instance).
- **Strong Binding:** Guarantee that `user_id` and `llm_model` are captured together for every span.
- **Database Support:** The local SQLite database (`agent_cost_vector`) does not store `user_id`.

## 3. Solution Design

### 3.1 Context Resolution Strategy

We need a robust way to identify the "User".

1.  **Hierarchy of Resolution for `user_id`:**
    *   **Explicit Argument:** Passed to `@track_agent_cost(user_id="...")`.
    *   **Environment Variable:** `ASP_USER_ID` (e.g., set in CI/CD pipeline).
    *   **Git Config:** `git config user.email` (for local developer sessions).
    *   **System Fallback:** `os.getlogin()` or "system-agent".

2.  **Hierarchy of Resolution for `llm_model`:**
    *   **Explicit Argument:** Passed to decorator.
    *   **Runtime Context:** Extracted from agent instance attributes (e.g., `self.model_name`).
    *   **Usage Report:** Extracted from `_last_llm_usage` returned by the function.
    *   **Environment Default:** `ASP_DEFAULT_MODEL` env var.

### 3.2 Data Model Changes

#### A. SQLite Schema Update
We must alter the `agent_cost_vector` and `defect_log` tables to include `user_id`.

```sql
ALTER TABLE agent_cost_vector ADD COLUMN user_id TEXT;
ALTER TABLE defect_log ADD COLUMN user_id TEXT;
-- Add index for frequent querying
CREATE INDEX idx_cost_user_model ON agent_cost_vector(user_id, llm_model);
```

#### B. Langfuse Metadata/Tags
To enable the "Pair" analysis in Langfuse, we will use **Tags** for filtering and **Metadata** for aggregation.

*   **Tags:**
    *   `user:<user_id>`
    *   `model:<llm_model>`
    *   `pair:<user_id>|<llm_model>` (Composite tag for easy filtering of specific pairs)

*   **Metadata:**
    *   `user_id`: "jules@example.com"
    *   `llm_model`: "claude-3-5-sonnet-20241022"
    *   `llm_provider`: "anthropic"

### 3.3 Implementation Plan

#### Step 1: Update Telemetry Module (`src/asp/telemetry/telemetry.py`)

1.  **Add `get_user_id()` helper:**
    ```python
    def get_user_id() -> str:
        # Check env, then git config, then fallback
        pass
    ```

2.  **Update `insert_agent_cost` and `insert_defect`:**
    *   Add `user_id` parameter (default to `None`).
    *   Update SQL `INSERT` statements.
    *   *Note: Requires schema migration script or manual db update.*

3.  **Update `@track_agent_cost` and `@log_defect` decorators:**
    *   Resolve `user_id` using helper if not provided.
    *   Resolve `llm_model` from args or instance.
    *   Pass both to `insert_*` functions.
    *   Add tags to Langfuse span/event: `["user:{uid}", "model:{model}", "pair:{uid}|{model}"]`.

#### Step 2: Database Migration
Create a utility script `scripts/migrate_telemetry_db.py` to add the missing columns to existing SQLite databases without data loss.

### 3.4 Analysis & Visualization

With this data, we can build PROBE reports:

**Query:** Average Latency by User+Model Pair
```sql
SELECT
    user_id,
    llm_model,
    AVG(metric_value) as avg_latency_ms
FROM agent_cost_vector
WHERE metric_type = 'Latency'
GROUP BY user_id, llm_model;
```

**Langfuse:**
- Filter by tag `pair:alex-dev|gpt-4o` to see all traces for Alex using GPT-4o.
- Compare Score/Cost/Latency metrics across different `model:*` tags for the same `user:*` tag.

## 4. Alternatives Considered

*   **Metadata only:** Harder to filter quickly in Langfuse UI (requires clicking into filters). Tags are first-class citizens.
*   **Composite User ID:** e.g., "alex-dev/gpt-4o". Bad idea; conflates identity with tool usage. Better to keep them separate fields but allow composite querying.

## 5. Security Implications

*   **Privacy:** `user_id` might be an email address. Ensure this is acceptable for the logging destination (Langfuse Public vs Private host).
*   **Mitigation:** Hash email addresses if PII is a concern (`sha256(email)`), or use internal usernames.

## 6. Conclusion

By adding explicit `user_id` tracking and enforcing `llm_model` capture, we can create a powerful dataset for evaluating the "Productivity Impact" of different LLMs on specific Agents or Humans.
