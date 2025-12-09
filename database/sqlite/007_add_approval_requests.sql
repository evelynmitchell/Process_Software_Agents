-- Migration 007: Add HITL approval request tables (SQLite)
-- Date: 2025-12-09
-- Description: Creates tables for inter-container HITL approval workflow
-- Used by: asp-agent-runner (writes requests), asp-webui (reads/writes decisions)

-- ==============================================================================
-- Table: approval_requests
-- Stores pending HITL approval requests from agent-runner
-- ==============================================================================

CREATE TABLE IF NOT EXISTS approval_requests (
    -- Primary Key
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    -- Request Identification
    request_id TEXT UNIQUE NOT NULL,

    -- Task Context
    task_id TEXT NOT NULL,

    -- Gate Information
    gate_type TEXT NOT NULL,  -- 'design_review', 'code_review'
    gate_name TEXT NOT NULL,  -- Display name

    -- Request Timing
    requested_at TEXT NOT NULL DEFAULT (datetime('now')),
    expires_at TEXT,  -- Optional timeout

    -- Quality Report (JSON as TEXT)
    quality_report TEXT NOT NULL,  -- Full quality gate report as JSON

    -- Summary for UI display
    summary TEXT,  -- Human-readable summary
    critical_issues INTEGER DEFAULT 0,
    high_issues INTEGER DEFAULT 0,

    -- Status
    status TEXT NOT NULL DEFAULT 'pending',

    -- Constraints
    CHECK (status IN ('pending', 'approved', 'rejected', 'deferred', 'expired')),
    CHECK (gate_type IN ('design_review', 'code_review'))
);


-- ==============================================================================
-- Table: approval_decisions
-- Stores human decisions on approval requests
-- ==============================================================================

CREATE TABLE IF NOT EXISTS approval_decisions (
    -- Primary Key
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    -- Link to request
    request_id TEXT NOT NULL,

    -- Decision
    decision TEXT NOT NULL,

    -- Reviewer Information
    reviewer TEXT NOT NULL,  -- Email or username
    decided_at TEXT NOT NULL DEFAULT (datetime('now')),

    -- Justification
    justification TEXT NOT NULL,

    -- Optional: Git context if merge was involved
    review_branch TEXT,
    merge_commit TEXT,

    -- Constraints
    CHECK (decision IN ('approved', 'rejected', 'deferred')),

    -- Foreign key (SQLite requires PRAGMA foreign_keys = ON)
    FOREIGN KEY (request_id) REFERENCES approval_requests(request_id)
);


-- ==============================================================================
-- Indexes for efficient polling
-- ==============================================================================

CREATE INDEX IF NOT EXISTS idx_approval_requests_status
    ON approval_requests(status);

CREATE INDEX IF NOT EXISTS idx_approval_requests_task
    ON approval_requests(task_id);

CREATE INDEX IF NOT EXISTS idx_approval_requests_pending
    ON approval_requests(status)
    WHERE status = 'pending';

CREATE INDEX IF NOT EXISTS idx_approval_decisions_request
    ON approval_decisions(request_id);


-- ==============================================================================
-- Trigger: Auto-update request status when decision is made
-- SQLite trigger syntax
-- ==============================================================================

CREATE TRIGGER IF NOT EXISTS trg_update_request_status
    AFTER INSERT ON approval_decisions
    FOR EACH ROW
BEGIN
    UPDATE approval_requests
    SET status = NEW.decision
    WHERE request_id = NEW.request_id;
END;
