# Database Schema Specification for ASP Telemetry

**Date:** November 11, 2025
**Purpose:** Define database schemas for Agent Cost Vector and Defect Recording Log
**Based On:** PRD Section VI (Tables 3 & 4), Section 14 (Bootstrap Learning)
**Platform:** Designed for PostgreSQL/TimescaleDB, adaptable to Langfuse metadata

---

## Overview

This document defines the telemetry schemas for the ASP system. These schemas capture:
1. **Agent Cost Vector:** Multi-dimensional resource consumption per agent execution
2. **Defect Recording Log:** AI-specific defects with injection/removal phase tracking
3. **Bootstrap Metrics:** Learning progress for graduated autonomy
4. **Task Metadata:** Context for PROBE-AI estimation and analytics

---

## Schema 1: Agent Cost Vector Log

### Purpose
Tracks resource consumption for every agent execution, enabling PROBE-AI estimation, cost tracking, and performance analysis.

### Table: `agent_cost_vector`

```sql
CREATE TABLE agent_cost_vector (
    -- Primary Key
    id BIGSERIAL PRIMARY KEY,

    -- Temporal Data
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    execution_date DATE GENERATED ALWAYS AS (timestamp::DATE) STORED,

    -- Task Context
    task_id VARCHAR(100) NOT NULL,
    subtask_id VARCHAR(100),  -- For decomposed tasks
    project_id VARCHAR(100),

    -- Agent Identification
    agent_role VARCHAR(50) NOT NULL,  -- Planning, Design, DesignReview, Code, CodeReview, Test, Postmortem
    agent_version VARCHAR(20),  -- For tracking prompt version changes
    agent_iteration INT DEFAULT 1,  -- For retry/correction loops

    -- Metric Data
    metric_type VARCHAR(50) NOT NULL,  -- Latency, Tokens_In, Tokens_Out, API_Cost, Memory_Usage, Tool_Calls, Retries
    metric_value NUMERIC(15, 4) NOT NULL,
    metric_unit VARCHAR(20) NOT NULL,  -- ms, tokens, USD, MB, count

    -- Model Context
    llm_model VARCHAR(100),  -- e.g., "gpt-4-0125-preview", "claude-sonnet-4"
    llm_provider VARCHAR(50),  -- e.g., "openai", "anthropic"

    -- Additional Metadata (JSON for flexibility)
    metadata JSONB,  -- Custom fields: prompt_hash, input_hash, tool_names, etc.

    -- Indexes
    CONSTRAINT chk_metric_value_positive CHECK (metric_value >= 0)
);

-- Indexes for performance (optimized for common queries)
CREATE INDEX idx_acv_task_id ON agent_cost_vector(task_id);
CREATE INDEX idx_acv_timestamp ON agent_cost_vector(timestamp DESC);
CREATE INDEX idx_acv_agent_role ON agent_cost_vector(agent_role);
CREATE INDEX idx_acv_metric_type ON agent_cost_vector(metric_type);
CREATE INDEX idx_acv_execution_date ON agent_cost_vector(execution_date DESC);

-- Composite index for PROBE-AI estimation queries
CREATE INDEX idx_acv_estimation ON agent_cost_vector(agent_role, metric_type, timestamp DESC);

-- JSONB index for metadata queries
CREATE INDEX idx_acv_metadata_gin ON agent_cost_vector USING GIN(metadata);
```

### TimescaleDB Optimization (Optional)

If using TimescaleDB, convert to hypertable for time-series optimization:

```sql
-- Convert to hypertable (partitioned by time)
SELECT create_hypertable('agent_cost_vector', 'timestamp',
    chunk_time_interval => INTERVAL '7 days',
    if_not_exists => TRUE
);

-- Add compression policy (compress data older than 30 days)
ALTER TABLE agent_cost_vector SET (
    timescaledb.compress,
    timescaledb.compress_segmentby = 'task_id, agent_role'
);

SELECT add_compression_policy('agent_cost_vector', INTERVAL '30 days');

-- Retention policy (optional: drop data older than 1 year)
SELECT add_retention_policy('agent_cost_vector', INTERVAL '1 year');
```

### Sample Data

```sql
INSERT INTO agent_cost_vector (task_id, agent_role, metric_type, metric_value, metric_unit, llm_model, llm_provider) VALUES
('TASK-001', 'Planning', 'Latency', 2150.50, 'ms', 'claude-sonnet-4', 'anthropic'),
('TASK-001', 'Planning', 'Tokens_In', 5240, 'tokens', 'claude-sonnet-4', 'anthropic'),
('TASK-001', 'Planning', 'Tokens_Out', 1820, 'tokens', 'claude-sonnet-4', 'anthropic'),
('TASK-001', 'Planning', 'API_Cost', 0.0382, 'USD', 'claude-sonnet-4', 'anthropic'),
('TASK-001', 'Design', 'Latency', 3850.25, 'ms', 'claude-sonnet-4', 'anthropic'),
('TASK-001', 'Design', 'Tool_Calls', 3, 'count', 'claude-sonnet-4', 'anthropic');
```

### Langfuse Integration Mapping

For Langfuse, these metrics map to:
- **Trace:** One per task_id
- **Span:** One per agent_role execution
- **Observation metadata:** metric_type/value/unit stored as custom fields

```python
# Example Langfuse instrumentation
from langfuse import Langfuse

langfuse = Langfuse()

trace = langfuse.trace(
    id=task_id,
    name="ASP Task Execution",
    metadata={"project_id": project_id}
)

span = trace.span(
    name=agent_role,
    metadata={
        "latency_ms": 2150.50,
        "tokens_in": 5240,
        "tokens_out": 1820,
        "api_cost_usd": 0.0382,
        "llm_model": "claude-sonnet-4",
        "agent_version": "v1.2.3"
    }
)
```

---

## Schema 2: Defect Recording Log

### Purpose
Captures AI-specific defects with injection/removal phase tracking, enabling quality analysis and bootstrap learning for review agents.

### Table: `defect_log`

```sql
CREATE TABLE defect_log (
    -- Primary Key
    defect_id VARCHAR(50) PRIMARY KEY,  -- e.g., "D-001", "D-042"

    -- Temporal Data
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    resolved_at TIMESTAMPTZ,

    -- Task Context
    task_id VARCHAR(100) NOT NULL,
    project_id VARCHAR(100),

    -- Defect Classification
    defect_type VARCHAR(50) NOT NULL,  -- From AI Defect Taxonomy (8 types)
    severity VARCHAR(20),  -- Critical, High, Medium, Low

    -- PSP Phase Tracking (Core PSP Concept)
    phase_injected VARCHAR(50) NOT NULL,  -- Agent role that created the defect
    phase_removed VARCHAR(50) NOT NULL,   -- Agent role that found the defect

    -- Affected Code Context
    component_path TEXT,  -- e.g., "src/auth/login.py"
    function_name VARCHAR(200),
    line_number INT,

    -- Effort to Fix (Agent Cost Vector for correction loop)
    effort_to_fix_json JSONB,  -- {latency_ms, tokens, api_cost, retries}

    -- Defect Details
    description TEXT NOT NULL,
    root_cause TEXT,
    resolution_notes TEXT,

    -- Review Agent Validation (Bootstrap Learning)
    flagged_by_agent BOOLEAN DEFAULT FALSE,  -- TRUE if review agent found it
    validated_by_human BOOLEAN DEFAULT FALSE,  -- TRUE if human confirmed it's real
    false_positive BOOLEAN DEFAULT FALSE,  -- TRUE if agent was wrong

    -- Additional Metadata
    metadata JSONB,  -- Custom fields: related_defects, external_issue_id, etc.

    -- Constraints
    CONSTRAINT chk_phase_different CHECK (phase_injected != phase_removed),
    CONSTRAINT chk_resolved_after_created CHECK (resolved_at IS NULL OR resolved_at >= created_at)
);

-- Indexes for performance
CREATE INDEX idx_defect_task_id ON defect_log(task_id);
CREATE INDEX idx_defect_type ON defect_log(defect_type);
CREATE INDEX idx_defect_phase_injected ON defect_log(phase_injected);
CREATE INDEX idx_defect_phase_removed ON defect_log(phase_removed);
CREATE INDEX idx_defect_component ON defect_log(component_path);
CREATE INDEX idx_defect_created_at ON defect_log(created_at DESC);

-- Composite index for bootstrap learning queries
CREATE INDEX idx_defect_bootstrap ON defect_log(flagged_by_agent, validated_by_human, false_positive);

-- JSONB indexes
CREATE INDEX idx_defect_effort_gin ON defect_log USING GIN(effort_to_fix_json);
CREATE INDEX idx_defect_metadata_gin ON defect_log USING GIN(metadata);
```

### Defect Type Enum (Reference)

```sql
-- AI Defect Taxonomy (from PRD Section VI)
CREATE TYPE defect_type_enum AS ENUM (
    '1_Planning_Failure',           -- Flawed task decomposition or estimation
    '2_Prompt_Misinterpretation',   -- Failed to follow instructions
    '3_Tool_Use_Error',             -- Incorrect tool selection or parameters
    '4_Hallucination',              -- Fabricated non-factual content
    '5_Security_Vulnerability',     -- Injected security flaw
    '6_Conventional_Code_Bug',      -- Traditional logical/syntax error
    '7_Task_Execution_Error',       -- Environment failure (timeout, API down)
    '8_Alignment_Deviation'         -- Violates business goals or ethics
);

-- Modify defect_log to use enum (optional, for stricter validation)
ALTER TABLE defect_log
    ALTER COLUMN defect_type TYPE defect_type_enum
    USING defect_type::defect_type_enum;
```

### Sample Data

```sql
INSERT INTO defect_log (
    defect_id, task_id, defect_type, phase_injected, phase_removed,
    component_path, description, effort_to_fix_json,
    flagged_by_agent, validated_by_human, false_positive
) VALUES
(
    'D-001',
    'TASK-001',
    '5_Security_Vulnerability',
    'Code',
    'CodeReview',
    'src/auth/login.py',
    'SQL injection vulnerability - used string concatenation instead of parameterized query',
    '{"latency_ms": 1250, "tokens": 850, "api_cost_usd": 0.015, "retries": 1}',
    TRUE,   -- Code Review Agent found it
    TRUE,   -- Human confirmed it's real
    FALSE   -- Not a false positive
),
(
    'D-002',
    'TASK-001',
    '4_Hallucination',
    'Code',
    'Test',
    'src/utils/helpers.py',
    'Agent imported non-existent library "data_transformer_v2" that does not exist',
    '{"latency_ms": 3200, "tokens": 1500, "api_cost_usd": 0.028, "retries": 2}',
    FALSE,  -- Test Agent found it (not caught in Code Review)
    TRUE,   -- Human confirmed
    FALSE
);
```

### Langfuse Integration Mapping

For Langfuse, defects map to:
- **Observation metadata:** Store defect_id and reference in span metadata
- **Score:** Use Langfuse's scoring feature to mark defective outputs

```python
# Example Langfuse defect logging
span = trace.span(
    name="Code",
    metadata={
        "defect_found": True,
        "defect_id": "D-001",
        "defect_type": "5_Security_Vulnerability"
    }
)

# Use Langfuse scoring to mark quality
span.score(
    name="code_quality",
    value=0.6,  # Lower score indicates defect
    comment="SQL injection vulnerability found by Code Review Agent"
)
```

---

## Schema 3: Task Metadata

### Purpose
Stores task-level context for PROBE-AI estimation, semantic complexity, and bootstrap learning analysis.

### Table: `task_metadata`

```sql
CREATE TABLE task_metadata (
    -- Primary Key
    task_id VARCHAR(100) PRIMARY KEY,

    -- Temporal Data
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,

    -- Project Context
    project_id VARCHAR(100),
    task_type VARCHAR(50),  -- e.g., "authentication", "database", "api", "ui"
    task_description TEXT,

    -- Requirements & Decomposition
    requirements_text TEXT,
    semantic_units_json JSONB,  -- Output from Planning Agent decomposition

    -- Semantic Complexity (from Planning Agent)
    estimated_complexity INT,  -- From Planning Agent
    actual_complexity INT,      -- Calculated post-execution

    -- PROBE-AI Estimation
    estimated_cost_vector_json JSONB,  -- {latency_ms, tokens, api_cost_usd}
    actual_cost_vector_json JSONB,     -- Aggregated from agent_cost_vector

    -- Quality Metrics
    defect_count INT DEFAULT 0,
    defect_density NUMERIC(5, 3),  -- Defects per complexity unit

    -- Affected Components
    components_affected TEXT[],  -- Array of file paths

    -- Bootstrap Learning Context
    bootstrap_phase VARCHAR(20),  -- Learning, Shadow, Autonomous
    human_reviewed BOOLEAN DEFAULT FALSE,
    human_corrections_json JSONB,  -- Track what humans fixed

    -- Status
    status VARCHAR(20) DEFAULT 'pending',  -- pending, in_progress, completed, failed

    -- Additional Metadata
    metadata JSONB,

    -- Constraints
    CONSTRAINT chk_status_valid CHECK (status IN ('pending', 'in_progress', 'completed', 'failed'))
);

-- Indexes
CREATE INDEX idx_task_project_id ON task_metadata(project_id);
CREATE INDEX idx_task_type ON task_metadata(task_type);
CREATE INDEX idx_task_created_at ON task_metadata(created_at DESC);
CREATE INDEX idx_task_status ON task_metadata(status);
CREATE INDEX idx_task_bootstrap_phase ON task_metadata(bootstrap_phase);

-- JSONB indexes for complex queries
CREATE INDEX idx_task_semantic_units_gin ON task_metadata USING GIN(semantic_units_json);
CREATE INDEX idx_task_components_gin ON task_metadata USING GIN(components_affected);
```

### Sample Data

```sql
INSERT INTO task_metadata (
    task_id, project_id, task_type, task_description,
    estimated_complexity, semantic_units_json,
    estimated_cost_vector_json, components_affected,
    bootstrap_phase, status
) VALUES
(
    'TASK-001',
    'ASP-Platform',
    'authentication',
    'Implement user login with JWT tokens and session management',
    18,
    '{"semantic_units": [
        {"unit_id": "SU-001", "description": "Create JWT token generation function", "est_complexity": 8},
        {"unit_id": "SU-002", "description": "Implement session storage with Redis", "est_complexity": 10}
    ]}',
    '{"latency_ms": 35000, "tokens": 88000, "api_cost_usd": 0.14}',
    ARRAY['src/auth/login.py', 'src/auth/jwt.py', 'src/session/redis_store.py'],
    'Learning',
    'in_progress'
);
```

---

## Schema 4: Bootstrap Metrics (Section 14 Support)

### Purpose
Tracks learning progress for bootstrap capabilities, enabling graduation decisions and performance monitoring.

### Table: `bootstrap_metrics`

```sql
CREATE TABLE bootstrap_metrics (
    -- Primary Key
    id BIGSERIAL PRIMARY KEY,

    -- Temporal Data
    measured_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    measurement_period_start TIMESTAMPTZ NOT NULL,
    measurement_period_end TIMESTAMPTZ NOT NULL,

    -- Capability Identification
    capability_name VARCHAR(50) NOT NULL,  -- PROBE_AI, TaskDecomposition, ErrorProneDetection, ReviewAgent_Design, ReviewAgent_Code, DefectTypePrediction
    capability_mode VARCHAR(20) NOT NULL,  -- Learning, Shadow, Autonomous

    -- Progress Tracking
    tasks_completed INT NOT NULL,
    tasks_required_for_graduation INT NOT NULL,

    -- Metrics (vary by capability)
    primary_metric_name VARCHAR(50) NOT NULL,
    primary_metric_value NUMERIC(10, 4) NOT NULL,
    primary_metric_target NUMERIC(10, 4) NOT NULL,

    -- Additional Metrics (JSON for flexibility)
    secondary_metrics_json JSONB,  -- {correction_rate, false_positive_rate, escape_rate, etc.}

    -- Graduation Status
    graduation_criteria_met BOOLEAN DEFAULT FALSE,
    graduation_notes TEXT,

    -- Additional Context
    metadata JSONB,

    -- Constraints
    CONSTRAINT chk_tasks_positive CHECK (tasks_completed >= 0 AND tasks_required_for_graduation > 0),
    CONSTRAINT chk_mode_valid CHECK (capability_mode IN ('Learning', 'Shadow', 'Autonomous'))
);

-- Indexes
CREATE INDEX idx_bootstrap_capability ON bootstrap_metrics(capability_name);
CREATE INDEX idx_bootstrap_measured_at ON bootstrap_metrics(measured_at DESC);
CREATE INDEX idx_bootstrap_mode ON bootstrap_metrics(capability_mode);
CREATE INDEX idx_bootstrap_graduation ON bootstrap_metrics(graduation_criteria_met);

-- Composite index for dashboard queries
CREATE INDEX idx_bootstrap_dashboard ON bootstrap_metrics(capability_name, measured_at DESC);
```

### Sample Data (Bootstrap Learning Progress)

```sql
INSERT INTO bootstrap_metrics (
    capability_name, capability_mode, tasks_completed, tasks_required_for_graduation,
    primary_metric_name, primary_metric_value, primary_metric_target,
    secondary_metrics_json, graduation_criteria_met, measurement_period_start, measurement_period_end
) VALUES
(
    'PROBE_AI',
    'Shadow',
    15,
    20,
    'MAPE',
    18.2,
    20.0,
    '{"r_squared": 0.73, "confidence_interval_avg": 0.35}',
    FALSE,
    NOW() - INTERVAL '15 days',
    NOW()
),
(
    'ReviewAgent_Code',
    'Learning',
    8,
    20,
    'True_Positive_Rate',
    85.0,
    80.0,
    '{"false_positive_rate": 15.0, "escape_rate": 8.0}',
    FALSE,  -- True Positive is good, but not enough tasks yet
    NOW() - INTERVAL '8 days',
    NOW()
);
```

---

## Relationships and Foreign Keys

### Entity Relationship Diagram (Conceptual)

```
task_metadata (1) ----< (N) agent_cost_vector
    |
    |
    +----< (N) defect_log
    |
    |
    +----< (N) bootstrap_metrics (via task_id in metadata)
```

### Optional Foreign Keys

```sql
-- Add foreign key constraints if strict referential integrity is needed
ALTER TABLE agent_cost_vector
    ADD CONSTRAINT fk_acv_task
    FOREIGN KEY (task_id) REFERENCES task_metadata(task_id) ON DELETE CASCADE;

ALTER TABLE defect_log
    ADD CONSTRAINT fk_defect_task
    FOREIGN KEY (task_id) REFERENCES task_metadata(task_id) ON DELETE CASCADE;
```

**Note:** Foreign keys may impact insert performance. Consider deferring or omitting them if telemetry logging must be async and high-throughput.

---

## Common Queries for ASP Analytics

### Query 1: PROBE-AI Estimation Data

```sql
-- Get historical data for PROBE-AI linear regression
SELECT
    tm.task_id,
    tm.estimated_complexity AS proxy,
    tm.actual_complexity,
    SUM(CASE WHEN acv.metric_type = 'Latency' THEN acv.metric_value ELSE 0 END) AS actual_latency_ms,
    SUM(CASE WHEN acv.metric_type = 'Tokens_In' THEN acv.metric_value ELSE 0 END) +
    SUM(CASE WHEN acv.metric_type = 'Tokens_Out' THEN acv.metric_value ELSE 0 END) AS actual_tokens,
    SUM(CASE WHEN acv.metric_type = 'API_Cost' THEN acv.metric_value ELSE 0 END) AS actual_api_cost_usd
FROM task_metadata tm
JOIN agent_cost_vector acv ON tm.task_id = acv.task_id
WHERE tm.status = 'completed'
  AND tm.actual_complexity IS NOT NULL
GROUP BY tm.task_id, tm.estimated_complexity, tm.actual_complexity
ORDER BY tm.created_at DESC
LIMIT 30;
```

### Query 2: Defect Density by Component

```sql
-- Identify error-prone components (Bootstrap Learning - B3)
SELECT
    dl.component_path,
    COUNT(*) AS defect_count,
    AVG(tm.actual_complexity) AS avg_complexity,
    COUNT(*) / NULLIF(AVG(tm.actual_complexity), 0) AS defect_density
FROM defect_log dl
JOIN task_metadata tm ON dl.task_id = tm.task_id
WHERE dl.component_path IS NOT NULL
GROUP BY dl.component_path
HAVING COUNT(*) > 2  -- At least 3 defects
ORDER BY defect_density DESC
LIMIT 10;
```

### Query 3: Review Agent Effectiveness (Bootstrap Learning - B4)

```sql
-- Calculate True Positive, False Positive, Escape rates
WITH review_metrics AS (
    SELECT
        phase_removed,
        COUNT(*) FILTER (WHERE flagged_by_agent = TRUE AND validated_by_human = TRUE) AS true_positives,
        COUNT(*) FILTER (WHERE flagged_by_agent = TRUE AND false_positive = TRUE) AS false_positives,
        COUNT(*) FILTER (WHERE flagged_by_agent = FALSE) AS false_negatives
    FROM defect_log
    WHERE phase_removed IN ('DesignReview', 'CodeReview')
    GROUP BY phase_removed
)
SELECT
    phase_removed AS review_agent,
    true_positives,
    false_positives,
    false_negatives,
    ROUND(100.0 * true_positives / NULLIF(true_positives + false_positives, 0), 2) AS true_positive_rate_pct,
    ROUND(100.0 * false_positives / NULLIF(true_positives + false_positives, 0), 2) AS false_positive_rate_pct,
    ROUND(100.0 * false_negatives / NULLIF(true_positives + false_negatives, 0), 2) AS escape_rate_pct
FROM review_metrics;
```

### Query 4: Bootstrap Dashboard Data

```sql
-- Get current status of all bootstrap capabilities
SELECT
    capability_name,
    capability_mode,
    tasks_completed,
    tasks_required_for_graduation,
    primary_metric_name,
    primary_metric_value,
    primary_metric_target,
    CASE
        WHEN graduation_criteria_met THEN 'Ready to Graduate'
        WHEN primary_metric_value <= primary_metric_target THEN 'On Track'
        ELSE 'Needs Improvement'
    END AS status_indicator
FROM (
    SELECT DISTINCT ON (capability_name) *
    FROM bootstrap_metrics
    ORDER BY capability_name, measured_at DESC
) latest_metrics
ORDER BY capability_name;
```

### Query 5: Cost Analysis by Agent Role

```sql
-- Track spending by agent role for budget monitoring
SELECT
    agent_role,
    COUNT(DISTINCT task_id) AS tasks_executed,
    SUM(CASE WHEN metric_type = 'API_Cost' THEN metric_value ELSE 0 END) AS total_cost_usd,
    AVG(CASE WHEN metric_type = 'Latency' THEN metric_value ELSE NULL END) AS avg_latency_ms,
    SUM(CASE WHEN metric_type = 'Tokens_In' THEN metric_value ELSE 0 END) +
    SUM(CASE WHEN metric_type = 'Tokens_Out' THEN metric_value ELSE 0 END) AS total_tokens
FROM agent_cost_vector
WHERE timestamp >= NOW() - INTERVAL '30 days'
GROUP BY agent_role
ORDER BY total_cost_usd DESC;
```

---

## Migration Strategy: Langfuse to PostgreSQL

If we start with Langfuse and later need to migrate to custom PostgreSQL:

1. **Export Langfuse Data:** Use Langfuse API to export traces/spans
2. **Transform to ASP Schema:** ETL pipeline to map Langfuse data to our schemas
3. **Backfill Historical Data:** Populate PostgreSQL with past 30-90 days of data
4. **Dual-Write Period:** Write to both Langfuse and PostgreSQL for validation
5. **Cutover:** Switch queries to PostgreSQL once validated
6. **Hybrid Mode (Optional):** Keep Langfuse for trace visualization, use PostgreSQL for analytics

---

## Implementation Checklist

- [ ] Review and approve schema design
- [ ] Create DDL scripts (next step)
- [ ] Set up PostgreSQL/TimescaleDB instance (if hybrid approach)
- [ ] Implement Python data models (SQLAlchemy or Pydantic)
- [ ] Build instrumentation decorators for automatic logging
- [ ] Create migration scripts for schema evolution
- [ ] Set up Grafana dashboards or custom analytics UI
- [ ] Write unit tests for schema constraints and queries

---

**Document Prepared By:** Claude Code
**Review Status:** Draft - Awaiting Approval
**Version:** 1.0
