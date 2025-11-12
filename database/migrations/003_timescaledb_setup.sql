-- ASP Telemetry Database - TimescaleDB Extension (Optional)
-- Version: 1.0
-- Date: 2025-11-11
-- Description: Converts tables to TimescaleDB hypertables for time-series optimization
-- Prerequisites: TimescaleDB extension must be installed (CREATE EXTENSION timescaledb;)

-- ==============================================================================
-- Enable TimescaleDB Extension
-- ==============================================================================

CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE;

-- ==============================================================================
-- Convert agent_cost_vector to Hypertable
-- ==============================================================================

-- Convert to hypertable (partitioned by time)
SELECT create_hypertable(
    'agent_cost_vector',
    'timestamp',
    chunk_time_interval => INTERVAL '7 days',
    if_not_exists => TRUE,
    migrate_data => TRUE  -- Migrate existing data if any
);

-- Enable compression for older data (saves storage, improves query performance)
ALTER TABLE agent_cost_vector SET (
    timescaledb.compress,
    timescaledb.compress_segmentby = 'task_id, agent_role, metric_type',  -- Segment by high-cardinality columns
    timescaledb.compress_orderby = 'timestamp DESC'
);

-- Add compression policy: compress data older than 30 days
SELECT add_compression_policy('agent_cost_vector', INTERVAL '30 days');

-- Add retention policy: automatically drop data older than 1 year (optional)
-- Uncomment if you want automatic data deletion:
-- SELECT add_retention_policy('agent_cost_vector', INTERVAL '1 year');

COMMENT ON TABLE agent_cost_vector IS 'TimescaleDB hypertable for time-series agent metrics (7-day chunks, 30-day compression)';

-- ==============================================================================
-- Convert bootstrap_metrics to Hypertable
-- ==============================================================================

-- Convert to hypertable
SELECT create_hypertable(
    'bootstrap_metrics',
    'measured_at',
    chunk_time_interval => INTERVAL '30 days',
    if_not_exists => TRUE,
    migrate_data => TRUE
);

-- Enable compression
ALTER TABLE bootstrap_metrics SET (
    timescaledb.compress,
    timescaledb.compress_segmentby = 'capability_name',
    timescaledb.compress_orderby = 'measured_at DESC'
);

-- Add compression policy: compress data older than 60 days
SELECT add_compression_policy('bootstrap_metrics', INTERVAL '60 days');

COMMENT ON TABLE bootstrap_metrics IS 'TimescaleDB hypertable for bootstrap learning metrics (30-day chunks, 60-day compression)';

-- ==============================================================================
-- Continuous Aggregates for Common Queries (Pre-computed Views)
-- ==============================================================================

-- Continuous Aggregate 1: Daily Cost Summary by Agent Role
CREATE MATERIALIZED VIEW IF NOT EXISTS daily_cost_summary
WITH (timescaledb.continuous) AS
SELECT
    time_bucket('1 day', timestamp) AS day,
    agent_role,
    project_id,
    COUNT(*) AS execution_count,
    SUM(CASE WHEN metric_type = 'API_Cost' THEN metric_value ELSE 0 END) AS total_cost_usd,
    AVG(CASE WHEN metric_type = 'Latency' THEN metric_value ELSE NULL END) AS avg_latency_ms,
    SUM(CASE WHEN metric_type = 'Tokens_In' THEN metric_value ELSE 0 END) AS total_tokens_in,
    SUM(CASE WHEN metric_type = 'Tokens_Out' THEN metric_value ELSE 0 END) AS total_tokens_out
FROM agent_cost_vector
GROUP BY day, agent_role, project_id;

-- Add refresh policy: update every hour for last 7 days
SELECT add_continuous_aggregate_policy('daily_cost_summary',
    start_offset => INTERVAL '7 days',
    end_offset => INTERVAL '1 hour',
    schedule_interval => INTERVAL '1 hour'
);

COMMENT ON MATERIALIZED VIEW daily_cost_summary IS 'Pre-computed daily cost rollups for dashboard performance';

-- Continuous Aggregate 2: Hourly Agent Performance Metrics
CREATE MATERIALIZED VIEW IF NOT EXISTS hourly_agent_performance
WITH (timescaledb.continuous) AS
SELECT
    time_bucket('1 hour', timestamp) AS hour,
    agent_role,
    COUNT(DISTINCT task_id) AS tasks_executed,
    AVG(CASE WHEN metric_type = 'Latency' THEN metric_value ELSE NULL END) AS avg_latency_ms,
    PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY CASE WHEN metric_type = 'Latency' THEN metric_value ELSE NULL END) AS p95_latency_ms,
    SUM(CASE WHEN metric_type = 'Retries' THEN metric_value ELSE 0 END) AS total_retries
FROM agent_cost_vector
GROUP BY hour, agent_role;

-- Add refresh policy
SELECT add_continuous_aggregate_policy('hourly_agent_performance',
    start_offset => INTERVAL '3 days',
    end_offset => INTERVAL '1 hour',
    schedule_interval => INTERVAL '1 hour'
);

COMMENT ON MATERIALIZED VIEW hourly_agent_performance IS 'Pre-computed hourly performance metrics for real-time monitoring';

-- ==============================================================================
-- Background Jobs for Data Management
-- ==============================================================================

-- Show all TimescaleDB background jobs
SELECT * FROM timescaledb_information.jobs;

-- Show compression status
SELECT
    hypertable_name,
    total_chunks,
    number_compressed_chunks,
    pg_size_pretty(before_compression_total_bytes) AS before_compression,
    pg_size_pretty(after_compression_total_bytes) AS after_compression,
    ROUND((1 - after_compression_total_bytes::numeric / NULLIF(before_compression_total_bytes, 0)) * 100, 2) AS compression_ratio_pct
FROM timescaledb_information.hypertable_compression_stats
WHERE hypertable_name IN ('agent_cost_vector', 'bootstrap_metrics');

-- ==============================================================================
-- Performance Tuning Recommendations
-- ==============================================================================

-- Analyze tables for optimal query planning
ANALYZE agent_cost_vector;
ANALYZE bootstrap_metrics;
ANALYZE daily_cost_summary;
ANALYZE hourly_agent_performance;

-- ==============================================================================
-- Completion Message
-- ==============================================================================

DO $$
BEGIN
    RAISE NOTICE 'TimescaleDB setup completed successfully!';
    RAISE NOTICE 'Hypertables created: agent_cost_vector (7-day chunks), bootstrap_metrics (30-day chunks)';
    RAISE NOTICE 'Continuous aggregates created: daily_cost_summary, hourly_agent_performance';
    RAISE NOTICE 'Compression enabled: agent_cost_vector (30 days), bootstrap_metrics (60 days)';
    RAISE NOTICE 'Query timescaledb_information.jobs to see background jobs';
END $$;
