-- ASP Telemetry Database - Indexes (SQLite)
-- Version: 1.0
-- Date: 2025-11-12
-- Description: Creates performance indexes for common query patterns

-- ==============================================================================
-- Indexes for agent_cost_vector
-- ==============================================================================

-- Basic indexes for filtering
CREATE INDEX IF NOT EXISTS idx_acv_task_id ON agent_cost_vector(task_id);
CREATE INDEX IF NOT EXISTS idx_acv_timestamp ON agent_cost_vector(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_acv_agent_role ON agent_cost_vector(agent_role);
CREATE INDEX IF NOT EXISTS idx_acv_metric_type ON agent_cost_vector(metric_type);
CREATE INDEX IF NOT EXISTS idx_acv_execution_date ON agent_cost_vector(execution_date DESC);
CREATE INDEX IF NOT EXISTS idx_acv_project_id ON agent_cost_vector(project_id);

-- Composite index for PROBE-AI estimation queries (Section IV)
CREATE INDEX IF NOT EXISTS idx_acv_estimation
    ON agent_cost_vector(agent_role, metric_type, timestamp DESC);

-- Composite index for cost analysis by agent
CREATE INDEX IF NOT EXISTS idx_acv_cost_analysis
    ON agent_cost_vector(agent_role, timestamp DESC)
    WHERE metric_type = 'API_Cost';

-- Note: SQLite does not support GIN indexes for JSON
-- JSON queries will use standard B-tree indexes on the JSON column

-- ==============================================================================
-- Indexes for defect_log
-- ==============================================================================

-- Basic indexes for filtering
CREATE INDEX IF NOT EXISTS idx_defect_task_id ON defect_log(task_id);
CREATE INDEX IF NOT EXISTS idx_defect_type ON defect_log(defect_type);
CREATE INDEX IF NOT EXISTS idx_defect_phase_injected ON defect_log(phase_injected);
CREATE INDEX IF NOT EXISTS idx_defect_phase_removed ON defect_log(phase_removed);
CREATE INDEX IF NOT EXISTS idx_defect_component ON defect_log(component_path);
CREATE INDEX IF NOT EXISTS idx_defect_created_at ON defect_log(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_defect_project_id ON defect_log(project_id);

-- Composite index for bootstrap learning queries (B4: Review Agent Effectiveness)
CREATE INDEX IF NOT EXISTS idx_defect_bootstrap
    ON defect_log(flagged_by_agent, validated_by_human, false_positive, phase_removed);

-- Composite index for error-prone area detection (B3)
CREATE INDEX IF NOT EXISTS idx_defect_component_analysis
    ON defect_log(component_path, defect_type, created_at DESC)
    WHERE component_path IS NOT NULL;

-- Composite index for defect type prediction (B5)
CREATE INDEX IF NOT EXISTS idx_defect_type_prediction
    ON defect_log(defect_type, created_at DESC);

-- ==============================================================================
-- Indexes for task_metadata
-- ==============================================================================

-- Basic indexes for filtering
CREATE INDEX IF NOT EXISTS idx_task_project_id ON task_metadata(project_id);
CREATE INDEX IF NOT EXISTS idx_task_type ON task_metadata(task_type);
CREATE INDEX IF NOT EXISTS idx_task_created_at ON task_metadata(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_task_status ON task_metadata(status);
CREATE INDEX IF NOT EXISTS idx_task_bootstrap_phase ON task_metadata(bootstrap_phase);

-- Composite index for PROBE-AI training data selection
CREATE INDEX IF NOT EXISTS idx_task_probe_ai
    ON task_metadata(status, actual_complexity, created_at DESC)
    WHERE status = 'completed' AND actual_complexity IS NOT NULL;

-- Composite index for bootstrap learning validation
CREATE INDEX IF NOT EXISTS idx_task_bootstrap_validation
    ON task_metadata(bootstrap_phase, human_reviewed, created_at DESC);

-- ==============================================================================
-- Indexes for bootstrap_metrics
-- ==============================================================================

-- Basic indexes for filtering
CREATE INDEX IF NOT EXISTS idx_bootstrap_capability ON bootstrap_metrics(capability_name);
CREATE INDEX IF NOT EXISTS idx_bootstrap_measured_at ON bootstrap_metrics(measured_at DESC);
CREATE INDEX IF NOT EXISTS idx_bootstrap_mode ON bootstrap_metrics(capability_mode);
CREATE INDEX IF NOT EXISTS idx_bootstrap_graduation ON bootstrap_metrics(graduation_criteria_met);

-- Composite index for dashboard queries (FR-23, FR-24)
CREATE INDEX IF NOT EXISTS idx_bootstrap_dashboard
    ON bootstrap_metrics(capability_name, measured_at DESC);

-- Composite index for trend analysis
CREATE INDEX IF NOT EXISTS idx_bootstrap_trends
    ON bootstrap_metrics(capability_name, capability_mode, measured_at DESC);

-- ==============================================================================
-- Analyze Tables for Query Optimizer
-- ==============================================================================

-- SQLite's ANALYZE command updates statistics for the query planner
ANALYZE agent_cost_vector;
ANALYZE defect_log;
ANALYZE task_metadata;
ANALYZE bootstrap_metrics;
