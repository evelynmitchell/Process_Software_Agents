-- ASP Telemetry Database - Core Tables (SQLite)
-- Version: 1.0
-- Date: 2025-11-12
-- Description: Creates core tables for Agent Cost Vector, Defect Log, Task Metadata, and Bootstrap Metrics
-- Database: SQLite 3.x (requires JSON1 extension for JSON functions)

-- ==============================================================================
-- Table 1: agent_cost_vector
-- Tracks multi-dimensional resource consumption per agent execution
-- ==============================================================================

CREATE TABLE IF NOT EXISTS agent_cost_vector (
    -- Primary Key (SQLite AUTOINCREMENT)
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    -- Temporal Data (ISO 8601 format: YYYY-MM-DD HH:MM:SS)
    timestamp TEXT NOT NULL DEFAULT (datetime('now')),
    execution_date TEXT NOT NULL DEFAULT (date('now')),

    -- Task Context
    task_id TEXT NOT NULL,
    subtask_id TEXT,
    project_id TEXT,
    user_id TEXT,

    -- Agent Identification
    agent_role TEXT NOT NULL,
    agent_version TEXT,
    agent_iteration INTEGER DEFAULT 1,

    -- Metric Data
    metric_type TEXT NOT NULL,
    metric_value REAL NOT NULL,
    metric_unit TEXT NOT NULL,

    -- Model Context
    llm_model TEXT,
    llm_provider TEXT,

    -- Additional Metadata (JSON as TEXT)
    metadata TEXT,

    -- Constraints
    CHECK (metric_value >= 0),
    CHECK (agent_role IN ('Planning', 'Design', 'DesignReview', 'Code', 'CodeReview', 'Test', 'Postmortem')),
    CHECK (metric_type IN ('Latency', 'Tokens_In', 'Tokens_Out', 'API_Cost', 'Memory_Usage', 'Tool_Calls', 'Retries'))
);

-- ==============================================================================
-- Table 2: defect_log
-- Captures AI-specific defects with injection/removal phase tracking
-- ==============================================================================

CREATE TABLE IF NOT EXISTS defect_log (
    -- Primary Key
    defect_id TEXT PRIMARY KEY,

    -- Temporal Data
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    resolved_at TEXT,

    -- Task Context
    task_id TEXT NOT NULL,
    project_id TEXT,
    user_id TEXT,

    -- Defect Classification
    defect_type TEXT NOT NULL,
    severity TEXT,

    -- PSP Phase Tracking
    phase_injected TEXT NOT NULL,
    phase_removed TEXT NOT NULL,

    -- Affected Code Context
    component_path TEXT,
    function_name TEXT,
    line_number INTEGER,

    -- Effort to Fix (JSON as TEXT)
    effort_to_fix_json TEXT,

    -- Defect Details
    description TEXT NOT NULL,
    root_cause TEXT,
    resolution_notes TEXT,

    -- Review Agent Validation (Bootstrap Learning B4)
    flagged_by_agent INTEGER DEFAULT 0,  -- SQLite uses 0/1 for boolean
    validated_by_human INTEGER DEFAULT 0,
    false_positive INTEGER DEFAULT 0,

    -- Additional Metadata (JSON as TEXT)
    metadata TEXT,

    -- Constraints
    CHECK (phase_injected != phase_removed),
    CHECK (resolved_at IS NULL OR resolved_at >= created_at),
    -- PROBE/PSP Defect Taxonomy (10-100)
    -- CHECK (defect_type IN ('10_Documentation', '20_Syntax', '30_Build_Package', '40_Assignment',
    --                        '50_Interface', '60_Checking', '70_Data', '80_Function',
    --                        '90_System', '100_Environment')),
    -- Note: Strict check commented out to allow migration from old types
    CHECK (severity IN ('Low', 'Medium', 'High', 'Critical')),
    CHECK (flagged_by_agent IN (0, 1)),
    CHECK (validated_by_human IN (0, 1)),
    CHECK (false_positive IN (0, 1))
);

-- ==============================================================================
-- Table 3: task_metadata
-- Stores task-level context for PROBE-AI estimation and analytics
-- ==============================================================================

CREATE TABLE IF NOT EXISTS task_metadata (
    -- Primary Key
    task_id TEXT PRIMARY KEY,

    -- Temporal Data
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    started_at TEXT,
    completed_at TEXT,

    -- Project Context
    project_id TEXT,
    task_type TEXT,
    task_description TEXT,

    -- Requirements & Decomposition
    requirements_text TEXT,
    semantic_units_json TEXT,  -- JSON as TEXT

    -- Semantic Complexity
    estimated_complexity INTEGER,
    actual_complexity INTEGER,

    -- PROBE-AI Estimation
    estimated_cost_vector_json TEXT,  -- JSON as TEXT
    actual_cost_vector_json TEXT,     -- JSON as TEXT

    -- Quality Metrics
    defect_count INTEGER DEFAULT 0,
    defect_density REAL,

    -- Affected Components (JSON array as TEXT)
    components_affected TEXT,  -- Store as JSON array: ["file1.py", "file2.py"]

    -- Bootstrap Learning Context
    bootstrap_phase TEXT,
    human_reviewed INTEGER DEFAULT 0,  -- 0/1 for boolean
    human_corrections_json TEXT,       -- JSON as TEXT

    -- Status
    status TEXT DEFAULT 'pending',

    -- Additional Metadata (JSON as TEXT)
    metadata TEXT,

    -- Constraints
    CHECK (status IN ('pending', 'in_progress', 'completed', 'failed')),
    CHECK (bootstrap_phase IS NULL OR bootstrap_phase IN ('Learning', 'Shadow', 'Autonomous')),
    CHECK (human_reviewed IN (0, 1))
);

-- ==============================================================================
-- Table 4: bootstrap_metrics
-- Tracks learning progress for bootstrap capabilities (Section 14)
-- ==============================================================================

CREATE TABLE IF NOT EXISTS bootstrap_metrics (
    -- Primary Key
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    -- Temporal Data
    measured_at TEXT NOT NULL DEFAULT (datetime('now')),
    measurement_period_start TEXT NOT NULL,
    measurement_period_end TEXT NOT NULL,

    -- Capability Identification
    capability_name TEXT NOT NULL,
    capability_mode TEXT NOT NULL,

    -- Progress Tracking
    tasks_completed INTEGER NOT NULL,
    tasks_required_for_graduation INTEGER NOT NULL,

    -- Metrics
    primary_metric_name TEXT NOT NULL,
    primary_metric_value REAL,
    primary_metric_target REAL NOT NULL,

    -- Additional Metrics (JSON as TEXT)
    secondary_metrics_json TEXT,

    -- Graduation Status
    graduation_criteria_met INTEGER DEFAULT 0,  -- 0/1 for boolean
    graduation_notes TEXT,

    -- Additional Context (JSON as TEXT)
    metadata TEXT,

    -- Constraints
    CHECK (tasks_completed >= 0 AND tasks_required_for_graduation > 0),
    CHECK (capability_mode IN ('Learning', 'Shadow', 'Autonomous')),
    CHECK (capability_name IN ('PROBE_AI', 'TaskDecomposition', 'ErrorProneDetection',
                               'ReviewAgent_Design', 'ReviewAgent_Code', 'DefectTypePrediction')),
    CHECK (graduation_criteria_met IN (0, 1))
);

-- ==============================================================================
-- Enable Foreign Key Constraints (Optional)
-- SQLite requires explicit enabling of foreign keys
-- ==============================================================================

-- Uncomment to enable foreign key constraints:
-- PRAGMA foreign_keys = ON;
--
-- ALTER TABLE agent_cost_vector ADD CONSTRAINT fk_acv_task
--     FOREIGN KEY (task_id) REFERENCES task_metadata(task_id) ON DELETE CASCADE;
--
-- ALTER TABLE defect_log ADD CONSTRAINT fk_defect_task
--     FOREIGN KEY (task_id) REFERENCES task_metadata(task_id) ON DELETE CASCADE;
