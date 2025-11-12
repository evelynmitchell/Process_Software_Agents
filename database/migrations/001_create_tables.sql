-- ASP Telemetry Database - Core Tables
-- Version: 1.0
-- Date: 2025-11-11
-- Description: Creates core tables for Agent Cost Vector, Defect Log, Task Metadata, and Bootstrap Metrics

-- ==============================================================================
-- Table 1: agent_cost_vector
-- Tracks multi-dimensional resource consumption per agent execution
-- ==============================================================================

CREATE TABLE IF NOT EXISTS agent_cost_vector (
    -- Primary Key
    id BIGSERIAL PRIMARY KEY,

    -- Temporal Data
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    execution_date DATE GENERATED ALWAYS AS (timestamp::DATE) STORED,

    -- Task Context
    task_id VARCHAR(100) NOT NULL,
    subtask_id VARCHAR(100),
    project_id VARCHAR(100),

    -- Agent Identification
    agent_role VARCHAR(50) NOT NULL,
    agent_version VARCHAR(20),
    agent_iteration INT DEFAULT 1,

    -- Metric Data
    metric_type VARCHAR(50) NOT NULL,
    metric_value NUMERIC(15, 4) NOT NULL,
    metric_unit VARCHAR(20) NOT NULL,

    -- Model Context
    llm_model VARCHAR(100),
    llm_provider VARCHAR(50),

    -- Additional Metadata
    metadata JSONB,

    -- Constraints
    CONSTRAINT chk_metric_value_positive CHECK (metric_value >= 0)
);

COMMENT ON TABLE agent_cost_vector IS 'Stores resource consumption metrics for every agent execution (FR-9)';
COMMENT ON COLUMN agent_cost_vector.agent_role IS 'Planning, Design, DesignReview, Code, CodeReview, Test, Postmortem';
COMMENT ON COLUMN agent_cost_vector.metric_type IS 'Latency, Tokens_In, Tokens_Out, API_Cost, Memory_Usage, Tool_Calls, Retries';
COMMENT ON COLUMN agent_cost_vector.agent_iteration IS 'Tracks retry/correction loops for self-correction analysis';

-- ==============================================================================
-- Table 2: defect_log
-- Captures AI-specific defects with injection/removal phase tracking
-- ==============================================================================

CREATE TABLE IF NOT EXISTS defect_log (
    -- Primary Key
    defect_id VARCHAR(50) PRIMARY KEY,

    -- Temporal Data
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    resolved_at TIMESTAMPTZ,

    -- Task Context
    task_id VARCHAR(100) NOT NULL,
    project_id VARCHAR(100),

    -- Defect Classification
    defect_type VARCHAR(50) NOT NULL,
    severity VARCHAR(20),

    -- PSP Phase Tracking
    phase_injected VARCHAR(50) NOT NULL,
    phase_removed VARCHAR(50) NOT NULL,

    -- Affected Code Context
    component_path TEXT,
    function_name VARCHAR(200),
    line_number INT,

    -- Effort to Fix
    effort_to_fix_json JSONB,

    -- Defect Details
    description TEXT NOT NULL,
    root_cause TEXT,
    resolution_notes TEXT,

    -- Review Agent Validation (Bootstrap Learning B4)
    flagged_by_agent BOOLEAN DEFAULT FALSE,
    validated_by_human BOOLEAN DEFAULT FALSE,
    false_positive BOOLEAN DEFAULT FALSE,

    -- Additional Metadata
    metadata JSONB,

    -- Constraints
    CONSTRAINT chk_phase_different CHECK (phase_injected != phase_removed),
    CONSTRAINT chk_resolved_after_created CHECK (resolved_at IS NULL OR resolved_at >= created_at)
);

COMMENT ON TABLE defect_log IS 'Stores AI-specific defects with PSP phase tracking (FR-10)';
COMMENT ON COLUMN defect_log.defect_type IS 'AI Defect Taxonomy: 1_Planning_Failure, 2_Prompt_Misinterpretation, 3_Tool_Use_Error, 4_Hallucination, 5_Security_Vulnerability, 6_Conventional_Code_Bug, 7_Task_Execution_Error, 8_Alignment_Deviation';
COMMENT ON COLUMN defect_log.phase_injected IS 'Agent role that created the defect';
COMMENT ON COLUMN defect_log.phase_removed IS 'Agent role that found the defect';
COMMENT ON COLUMN defect_log.flagged_by_agent IS 'TRUE if review agent found it (for Bootstrap Learning B4 - Review Agent Effectiveness)';

-- ==============================================================================
-- Table 3: task_metadata
-- Stores task-level context for PROBE-AI estimation and analytics
-- ==============================================================================

CREATE TABLE IF NOT EXISTS task_metadata (
    -- Primary Key
    task_id VARCHAR(100) PRIMARY KEY,

    -- Temporal Data
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,

    -- Project Context
    project_id VARCHAR(100),
    task_type VARCHAR(50),
    task_description TEXT,

    -- Requirements & Decomposition
    requirements_text TEXT,
    semantic_units_json JSONB,

    -- Semantic Complexity
    estimated_complexity INT,
    actual_complexity INT,

    -- PROBE-AI Estimation
    estimated_cost_vector_json JSONB,
    actual_cost_vector_json JSONB,

    -- Quality Metrics
    defect_count INT DEFAULT 0,
    defect_density NUMERIC(5, 3),

    -- Affected Components
    components_affected TEXT[],

    -- Bootstrap Learning Context
    bootstrap_phase VARCHAR(20),
    human_reviewed BOOLEAN DEFAULT FALSE,
    human_corrections_json JSONB,

    -- Status
    status VARCHAR(20) DEFAULT 'pending',

    -- Additional Metadata
    metadata JSONB,

    -- Constraints
    CONSTRAINT chk_status_valid CHECK (status IN ('pending', 'in_progress', 'completed', 'failed'))
);

COMMENT ON TABLE task_metadata IS 'Stores task-level context for PROBE-AI estimation and bootstrap learning';
COMMENT ON COLUMN task_metadata.semantic_units_json IS 'Output from Planning Agent task decomposition';
COMMENT ON COLUMN task_metadata.estimated_complexity IS 'Semantic Complexity score from Planning Agent (Section 13.1 C1)';
COMMENT ON COLUMN task_metadata.bootstrap_phase IS 'Learning, Shadow, or Autonomous (Section 14)';

-- ==============================================================================
-- Table 4: bootstrap_metrics
-- Tracks learning progress for bootstrap capabilities (Section 14)
-- ==============================================================================

CREATE TABLE IF NOT EXISTS bootstrap_metrics (
    -- Primary Key
    id BIGSERIAL PRIMARY KEY,

    -- Temporal Data
    measured_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    measurement_period_start TIMESTAMPTZ NOT NULL,
    measurement_period_end TIMESTAMPTZ NOT NULL,

    -- Capability Identification
    capability_name VARCHAR(50) NOT NULL,
    capability_mode VARCHAR(20) NOT NULL,

    -- Progress Tracking
    tasks_completed INT NOT NULL,
    tasks_required_for_graduation INT NOT NULL,

    -- Metrics
    primary_metric_name VARCHAR(50) NOT NULL,
    primary_metric_value NUMERIC(10, 4) NOT NULL,
    primary_metric_target NUMERIC(10, 4) NOT NULL,

    -- Additional Metrics
    secondary_metrics_json JSONB,

    -- Graduation Status
    graduation_criteria_met BOOLEAN DEFAULT FALSE,
    graduation_notes TEXT,

    -- Additional Context
    metadata JSONB,

    -- Constraints
    CONSTRAINT chk_tasks_positive CHECK (tasks_completed >= 0 AND tasks_required_for_graduation > 0),
    CONSTRAINT chk_mode_valid CHECK (capability_mode IN ('Learning', 'Shadow', 'Autonomous'))
);

COMMENT ON TABLE bootstrap_metrics IS 'Tracks learning progress for bootstrap capabilities (FR-23, FR-24)';
COMMENT ON COLUMN bootstrap_metrics.capability_name IS 'PROBE_AI, TaskDecomposition, ErrorProneDetection, ReviewAgent_Design, ReviewAgent_Code, DefectTypePrediction';
COMMENT ON COLUMN bootstrap_metrics.capability_mode IS 'Learning (human validates all), Shadow (spot checks), Autonomous (periodic review)';

-- ==============================================================================
-- Optional: Foreign Key Constraints
-- Note: May impact insert performance. Enable only if strict referential integrity required.
-- ==============================================================================

-- Uncomment to enable foreign keys:
-- ALTER TABLE agent_cost_vector
--     ADD CONSTRAINT fk_acv_task
--     FOREIGN KEY (task_id) REFERENCES task_metadata(task_id) ON DELETE CASCADE;

-- ALTER TABLE defect_log
--     ADD CONSTRAINT fk_defect_task
--     FOREIGN KEY (task_id) REFERENCES task_metadata(task_id) ON DELETE CASCADE;

-- ==============================================================================
-- Completion Message
-- ==============================================================================

DO $$
BEGIN
    RAISE NOTICE 'ASP Telemetry core tables created successfully!';
    RAISE NOTICE 'Next: Run 002_create_indexes.sql for performance optimization';
END $$;
