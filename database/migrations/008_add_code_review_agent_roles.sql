-- Migration 008: Add specialist Code Review agent roles to CHECK constraint
-- Date: 2025-12-10
-- Description: Extends agent_role CHECK constraint to include the 6 specialist Code Review agents

-- SQLite doesn't support ALTER TABLE to modify CHECK constraints directly,
-- so we need to:
-- 1. Create a new table with the updated constraint
-- 2. Copy data from old table
-- 3. Drop old table
-- 4. Rename new table

-- Step 1: Create new table with updated CHECK constraint
CREATE TABLE agent_cost_vector_new (
    -- Primary Key
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    -- Task Context
    task_id VARCHAR(100) NOT NULL,
    project_id VARCHAR(100),

    -- Agent Identification
    agent_role VARCHAR(50) NOT NULL,
    agent_version VARCHAR(20),
    agent_iteration INT DEFAULT 1,

    -- Metric Data
    metric_type VARCHAR(50) NOT NULL,
    metric_value REAL NOT NULL,

    -- Timestamp
    timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    -- Constraints
    CHECK (metric_value >= 0),
    CHECK (agent_role IN (
        'Planning',
        'Design',
        'DesignReview',
        'SecurityReview',
        'PerformanceReview',
        'DataIntegrityReview',
        'MaintainabilityReview',
        'ArchitectureReview',
        'APIDesignReview',
        'Code',
        'CodeReview',
        'CodeQualityReview',
        'CodeSecurityReview',
        'BestPracticesReview',
        'TestCoverageReview',
        'CodePerformanceReview',
        'DocumentationReview',
        'Test',
        'Postmortem'
    )),
    CHECK (metric_type IN ('Latency', 'Tokens_In', 'Tokens_Out', 'API_Cost', 'Memory_Usage', 'Tool_Calls', 'Retries'))
);

-- Step 2: Copy data from old table
INSERT INTO agent_cost_vector_new (
    id, task_id, project_id, agent_role, agent_version, agent_iteration,
    metric_type, metric_value, timestamp
)
SELECT
    id, task_id, project_id, agent_role, agent_version, agent_iteration,
    metric_type, metric_value, timestamp
FROM agent_cost_vector;

-- Step 3: Drop old table
DROP TABLE agent_cost_vector;

-- Step 4: Rename new table
ALTER TABLE agent_cost_vector_new RENAME TO agent_cost_vector;

-- Recreate indexes (they were dropped with the old table)
CREATE INDEX idx_agent_cost_task ON agent_cost_vector(task_id);
CREATE INDEX idx_agent_cost_role ON agent_cost_vector(agent_role);
CREATE INDEX idx_agent_cost_metric ON agent_cost_vector(metric_type);
CREATE INDEX idx_agent_cost_timestamp ON agent_cost_vector(timestamp);
CREATE INDEX idx_agent_cost_composite ON agent_cost_vector(task_id, agent_role, metric_type);

-- Migration complete
-- Added Code Review specialist agent roles:
--   - CodeQualityReview, CodeSecurityReview, BestPracticesReview
--   - TestCoverageReview, CodePerformanceReview, DocumentationReview
