# ASP Telemetry Database

This directory contains database schemas and migration scripts for the Agentic Software Process (ASP) telemetry system.

---

## Overview

The ASP telemetry database captures:
1. **Agent Cost Vector** - Resource consumption per agent execution (latency, tokens, API cost)
2. **Defect Log** - AI-specific defects with PSP phase tracking
3. **Task Metadata** - Context for PROBE-AI estimation and analytics
4. **Bootstrap Metrics** - Learning progress for graduated autonomy

**Database Choice:** See [Data Storage Decision](../docs/data_storage_decision.md) for rationale.
- **Phase 1-3 (Recommended):** SQLite - Zero setup, portable, perfect for <100K rows
- **Phase 4+ (Production):** PostgreSQL - When scaling to high concurrency or large datasets

---

## Quick Start (SQLite - Recommended)

### Option 1: Python Script (Easiest)

```bash
# Create database with schema only
uv run python scripts/init_database.py

# Create database with sample data for testing
uv run python scripts/init_database.py --with-sample-data

# Reset existing database
uv run python scripts/init_database.py --reset

# Custom database path
uv run python scripts/init_database.py --db-path /path/to/custom.db
```

The script will:
1. Create `asp_telemetry.db` (or custom path)
2. Create all 4 tables with proper constraints
3. Create performance indexes
4. Optionally populate with sample data
5. Display statistics and verification results

### Option 2: Manual SQL Execution

```bash
# Create data directory
mkdir -p data

# Create database and run migrations
sqlite3 data/asp_telemetry.db < database/sqlite/create_tables.sql
sqlite3 data/asp_telemetry.db < database/sqlite/create_indexes.sql

# Optional: Add sample data
sqlite3 data/asp_telemetry.db < database/sqlite/sample_data.sql
```

### Verifying SQLite Database

```bash
# Check tables
sqlite3 data/asp_telemetry.db ".tables"

# Query sample data
sqlite3 data/asp_telemetry.db "SELECT task_id, task_type, status FROM task_metadata;"

# Check database size
ls -lh data/asp_telemetry.db
```

**Note:** The database is stored in the `data/` directory to separate runtime data from source code.

---

## Advanced: PostgreSQL Setup

For production deployment or when you need PostgreSQL features (see [migration criteria](../docs/data_storage_decision.md#when-to-migrate-to-postgresql)):

### PostgreSQL Only

```bash
# 1. Create database
createdb asp_telemetry

# 2. Run migrations in order
psql asp_telemetry < migrations/001_create_tables.sql
psql asp_telemetry < migrations/002_create_indexes.sql
psql asp_telemetry < migrations/004_sample_data.sql  # Optional: test data
```

### PostgreSQL + TimescaleDB (Production Optimization)

```bash
# 1. Install TimescaleDB extension (Ubuntu/Debian)
sudo apt-get install timescaledb-postgresql-14

# 2. Create database and enable extension
createdb asp_telemetry
psql asp_telemetry -c "CREATE EXTENSION timescaledb;"

# 3. Run all migrations in order
psql asp_telemetry < migrations/001_create_tables.sql
psql asp_telemetry < migrations/002_create_indexes.sql
psql asp_telemetry < migrations/003_timescaledb_setup.sql  # TimescaleDB optimization
psql asp_telemetry < migrations/004_sample_data.sql        # Optional: test data
```

### Migrating from SQLite to PostgreSQL

```bash
# Use the migration script (coming soon)
uv run python scripts/migrate_sqlite_to_postgres.py \
    --sqlite-db asp_telemetry.db \
    --postgres-url postgresql://user:pass@localhost/asp_telemetry
```

---

## Migration Files

### SQLite Files (Phase 1-3)

| File | Description | Required |
|------|-------------|----------|
| `sqlite/create_tables.sql` | Creates 4 core tables | Yes |
| `sqlite/create_indexes.sql` | Adds performance indexes | Yes |
| `sqlite/sample_data.sql` | Inserts test data | Optional |

### PostgreSQL Files (Phase 4+)

| File | Description | Required | Dependencies |
|------|-------------|----------|--------------|
| `migrations/001_create_tables.sql` | Creates 4 core tables | Yes | PostgreSQL 12+ |
| `migrations/002_create_indexes.sql` | Adds performance indexes | Yes | 001 |
| `migrations/003_timescaledb_setup.sql` | TimescaleDB optimization | Optional | 001, 002, TimescaleDB |
| `migrations/004_sample_data.sql` | Inserts test data | Optional | 001, 002 |

---

## Table Reference

### 1. agent_cost_vector
**Purpose:** Tracks multi-dimensional resource consumption per agent execution

**Key Columns:**
- `task_id` - Links to task_metadata
- `agent_role` - Planning, Design, Code, etc.
- `metric_type` - Latency, Tokens_In, Tokens_Out, API_Cost, etc.
- `metric_value` - Numeric value of the metric
- `llm_model` - e.g., "claude-sonnet-4", "gpt-4-turbo"

**Use Cases:**
- PROBE-AI estimation (Section 14.2 B1)
- Cost tracking and budget monitoring
- Performance analysis by agent role

### 2. defect_log
**Purpose:** Captures AI-specific defects with injection/removal phase tracking

**Key Columns:**
- `defect_id` - Unique identifier (e.g., "D-001")
- `defect_type` - From AI Defect Taxonomy (8 types)
- `phase_injected` - Agent that created the defect
- `phase_removed` - Agent that found the defect
- `flagged_by_agent` - TRUE if review agent found it
- `validated_by_human` - TRUE if human confirmed it's real

**Use Cases:**
- Bootstrap Learning - Review Agent Effectiveness (B4)
- Error-prone area detection (B3)
- Defect type prediction (B5)

### 3. task_metadata
**Purpose:** Stores task-level context for PROBE-AI and analytics

**Key Columns:**
- `task_id` - Unique identifier
- `estimated_complexity` - From Planning Agent
- `actual_complexity` - Post-execution calculation
- `semantic_units_json` - Task decomposition
- `bootstrap_phase` - Learning, Shadow, or Autonomous

**Use Cases:**
- PROBE-AI training data
- Task decomposition quality tracking (B2)
- Project planning and estimation accuracy

### 4. bootstrap_metrics
**Purpose:** Tracks learning progress for bootstrap capabilities

**Key Columns:**
- `capability_name` - PROBE_AI, TaskDecomposition, etc.
- `capability_mode` - Learning, Shadow, Autonomous
- `primary_metric_value` - Current accuracy metric
- `graduation_criteria_met` - Ready to graduate?

**Use Cases:**
- Bootstrap Status Dashboard (FR-24)
- Graduation decision support
- Performance regression detection

---

## Common Queries

These queries work on both SQLite and PostgreSQL (with minor syntax variations noted).

### Get PROBE-AI Training Data

```sql
-- Works on both SQLite and PostgreSQL
SELECT
    tm.task_id,
    tm.estimated_complexity AS proxy,
    SUM(CASE WHEN acv.metric_type = 'Latency' THEN acv.metric_value ELSE 0 END) AS actual_latency_ms,
    SUM(CASE WHEN acv.metric_type = 'API_Cost' THEN acv.metric_value ELSE 0 END) AS actual_api_cost
FROM task_metadata tm
JOIN agent_cost_vector acv ON tm.task_id = acv.task_id
WHERE tm.status = 'completed'
GROUP BY tm.task_id, tm.estimated_complexity
ORDER BY tm.created_at DESC
LIMIT 20;
```

### Review Agent True Positive Rate

```sql
-- SQLite version (use SUM with CASE)
SELECT
    phase_removed AS review_agent,
    SUM(CASE WHEN flagged_by_agent = 1 AND validated_by_human = 1 THEN 1 ELSE 0 END) AS true_positives,
    SUM(CASE WHEN flagged_by_agent = 1 AND false_positive = 1 THEN 1 ELSE 0 END) AS false_positives,
    ROUND(100.0 * SUM(CASE WHEN flagged_by_agent = 1 AND validated_by_human = 1 THEN 1 ELSE 0 END) /
          NULLIF(SUM(CASE WHEN flagged_by_agent = 1 THEN 1 ELSE 0 END), 0), 2) AS true_positive_rate_pct
FROM defect_log
WHERE phase_removed IN ('DesignReview', 'CodeReview')
GROUP BY phase_removed;

-- PostgreSQL version (use FILTER clause for cleaner syntax)
-- SELECT
--     phase_removed AS review_agent,
--     COUNT(*) FILTER (WHERE flagged_by_agent = TRUE AND validated_by_human = TRUE) AS true_positives,
--     COUNT(*) FILTER (WHERE flagged_by_agent = TRUE AND false_positive = TRUE) AS false_positives,
--     ROUND(100.0 * COUNT(*) FILTER (WHERE flagged_by_agent = TRUE AND validated_by_human = TRUE) /
--           NULLIF(COUNT(*) FILTER (WHERE flagged_by_agent = TRUE), 0), 2) AS true_positive_rate_pct
-- FROM defect_log
-- WHERE phase_removed IN ('DesignReview', 'CodeReview')
-- GROUP BY phase_removed;
```

### Cost Analysis by Agent (Last 30 Days)

```sql
-- SQLite version
SELECT
    agent_role,
    COUNT(DISTINCT task_id) AS tasks,
    SUM(CASE WHEN metric_type = 'API_Cost' THEN metric_value ELSE 0 END) AS total_cost_usd,
    AVG(CASE WHEN metric_type = 'Latency' THEN metric_value ELSE NULL END) AS avg_latency_ms
FROM agent_cost_vector
WHERE timestamp >= datetime('now', '-30 days')
GROUP BY agent_role
ORDER BY total_cost_usd DESC;

-- PostgreSQL version
-- WHERE timestamp >= NOW() - INTERVAL '30 days'
```

### Bootstrap Dashboard Data

```sql
-- SQLite version (using subquery for latest record per capability)
SELECT
    capability_name,
    capability_mode,
    tasks_completed || '/' || tasks_required_for_graduation AS progress,
    primary_metric_value,
    primary_metric_target,
    graduation_criteria_met
FROM bootstrap_metrics bm1
WHERE measured_at = (
    SELECT MAX(measured_at)
    FROM bootstrap_metrics bm2
    WHERE bm2.capability_name = bm1.capability_name
)
ORDER BY capability_name;

-- PostgreSQL version (using DISTINCT ON)
-- SELECT DISTINCT ON (capability_name)
--     capability_name,
--     capability_mode,
--     tasks_completed || '/' || tasks_required_for_graduation AS progress,
--     primary_metric_value,
--     primary_metric_target,
--     graduation_criteria_met
-- FROM bootstrap_metrics
-- ORDER BY capability_name, measured_at DESC;
```

---

## Schema Evolution

To modify the schema:

1. Create a new migration file: `005_your_change.sql`
2. Use `ALTER TABLE` statements (not `DROP TABLE`)
3. Add comments explaining the change
4. Test on sample data first

Example:
```sql
-- 005_add_agent_timeout.sql
ALTER TABLE agent_cost_vector
    ADD COLUMN IF NOT EXISTS timeout_occurred BOOLEAN DEFAULT FALSE;

COMMENT ON COLUMN agent_cost_vector.timeout_occurred IS 'TRUE if agent hit LLM timeout';
```

---

## TimescaleDB Features

If using TimescaleDB (003), you get:

**Hypertables:**
- `agent_cost_vector` - 7-day chunks, 30-day compression
- `bootstrap_metrics` - 30-day chunks, 60-day compression

**Continuous Aggregates (Pre-computed Views):**
- `daily_cost_summary` - Cost rollups by day/agent/project
- `hourly_agent_performance` - Hourly latency/retry metrics

**Query Optimization:**
```sql
-- Before: Slow full table scan
SELECT AVG(metric_value) FROM agent_cost_vector WHERE metric_type = 'Latency';

-- After: Fast with continuous aggregate
SELECT AVG(avg_latency_ms) FROM hourly_agent_performance WHERE hour >= NOW() - INTERVAL '7 days';
```

---

## Maintenance

### Vacuum and Analyze
```sql
-- Run weekly to maintain performance
VACUUM ANALYZE agent_cost_vector;
VACUUM ANALYZE defect_log;
VACUUM ANALYZE task_metadata;
VACUUM ANALYZE bootstrap_metrics;
```

### Check Table Sizes
```sql
SELECT
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
```

### TimescaleDB Compression Status
```sql
SELECT * FROM timescaledb_information.hypertable_compression_stats
WHERE hypertable_name IN ('agent_cost_vector', 'bootstrap_metrics');
```

---

## Integration with Langfuse

The schemas are designed to complement Langfuse:

**Hybrid Approach (Recommended):**
- **Langfuse:** Trace visualization, prompt management, real-time debugging
- **PostgreSQL:** Complex analytics, PROBE-AI, bootstrap learning queries

**Data Flow:**
1. Agent executes → Log to both Langfuse (via SDK) and PostgreSQL (via instrumentation)
2. Use Langfuse for debugging agent behavior
3. Use PostgreSQL for estimation, quality analysis, bootstrap metrics

**Migration Path:**
- Start with Langfuse Cloud (fast setup)
- Add PostgreSQL hybrid layer when analytics needs grow (Phase 2+)
- Export Langfuse data to backfill PostgreSQL if switching platforms

---

## Troubleshooting

### "relation does not exist" Error
Run migrations in order (001 → 002 → 003 → 004). Each depends on the previous.

### Slow Queries
1. Check indexes exist: `\di` in psql
2. Run `ANALYZE` on tables
3. Consider TimescaleDB continuous aggregates for repeated queries

### TimescaleDB "could not create hypertable"
Ensure TimescaleDB extension is installed:
```sql
SELECT * FROM pg_extension WHERE extname = 'timescaledb';
```

---

## Next Steps

- [ ] Deploy database (see deployment options above)
- [ ] Run migrations
- [ ] Build Python data models (SQLAlchemy/Pydantic)
- [ ] Implement instrumentation decorators
- [ ] Set up Grafana dashboards
- [ ] Configure automated backups

---

**Related Documentation:**
- [Data Storage Decision](../docs/data_storage_decision.md) - SQLite vs PostgreSQL
- [Database Schema Specification](../docs/database_schema_specification.md)
- [Observability Platform Evaluation](../docs/observability_platform_evaluation.md)
- PRD Section VI: Automating Process Data

**Version:** 1.1
**Last Updated:** 2025-11-12
**Changes:**
- Added SQLite as default/recommended database (Phase 1-3)
- Created SQLite-compatible schema scripts
- Added Python initialization script (`scripts/init_database.py`)
- Updated queries to work with both SQLite and PostgreSQL
