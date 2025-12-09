-- Migration 006: Add missing columns to agent_cost_vector
-- Date: 2025-12-09
-- Description: Adds columns that exist in create_tables.sql but missing from existing databases

-- Add subtask_id column (for decomposed tasks)
ALTER TABLE agent_cost_vector ADD COLUMN subtask_id TEXT;

-- Add user_id column (for user tracking)
ALTER TABLE agent_cost_vector ADD COLUMN user_id TEXT;

-- Add metric_unit column (for unit of measurement)
ALTER TABLE agent_cost_vector ADD COLUMN metric_unit TEXT;

-- Add llm_model column (for model tracking)
ALTER TABLE agent_cost_vector ADD COLUMN llm_model TEXT;

-- Add llm_provider column (for provider tracking)
ALTER TABLE agent_cost_vector ADD COLUMN llm_provider TEXT;

-- Add metadata column (for additional JSON metadata)
ALTER TABLE agent_cost_vector ADD COLUMN metadata TEXT;

-- Add execution_date column (for date-based queries)
ALTER TABLE agent_cost_vector ADD COLUMN execution_date TEXT;

-- Update existing rows to populate execution_date from timestamp
UPDATE agent_cost_vector
SET execution_date = date(timestamp)
WHERE execution_date IS NULL;

-- Note: SQLite doesn't support adding CHECK constraints via ALTER TABLE
-- The new columns will not have the same constraints as fresh tables
