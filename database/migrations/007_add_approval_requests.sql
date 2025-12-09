-- Migration 007: Add HITL approval request tables
-- Date: 2025-12-09
-- Description: Creates tables for inter-container HITL approval workflow
-- Used by: asp-agent-runner (writes requests), asp-webui (reads/writes decisions)

-- ==============================================================================
-- Table: approval_requests
-- Stores pending HITL approval requests from agent-runner
-- ==============================================================================

CREATE TABLE IF NOT EXISTS approval_requests (
    -- Primary Key
    id BIGSERIAL PRIMARY KEY,

    -- Request Identification
    request_id VARCHAR(100) UNIQUE NOT NULL,

    -- Task Context
    task_id VARCHAR(100) NOT NULL,

    -- Gate Information
    gate_type VARCHAR(50) NOT NULL,  -- 'design_review', 'code_review'
    gate_name VARCHAR(100) NOT NULL, -- Display name

    -- Request Timing
    requested_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    expires_at TIMESTAMPTZ,  -- Optional timeout

    -- Quality Report (JSON)
    quality_report JSONB NOT NULL,  -- Full quality gate report

    -- Summary for UI display
    summary TEXT,  -- Human-readable summary
    critical_issues INT DEFAULT 0,
    high_issues INT DEFAULT 0,

    -- Status
    status VARCHAR(20) NOT NULL DEFAULT 'pending',

    -- Constraints
    CONSTRAINT chk_status_valid CHECK (status IN ('pending', 'approved', 'rejected', 'deferred', 'expired'))
);

COMMENT ON TABLE approval_requests IS 'HITL approval requests from agent-runner to webui';
COMMENT ON COLUMN approval_requests.request_id IS 'Unique identifier: {task_id}_{gate_type}_{timestamp}';
COMMENT ON COLUMN approval_requests.gate_type IS 'design_review, code_review';
COMMENT ON COLUMN approval_requests.status IS 'pending=awaiting decision, approved/rejected/deferred=decided, expired=timed out';


-- ==============================================================================
-- Table: approval_decisions
-- Stores human decisions on approval requests
-- ==============================================================================

CREATE TABLE IF NOT EXISTS approval_decisions (
    -- Primary Key
    id BIGSERIAL PRIMARY KEY,

    -- Link to request
    request_id VARCHAR(100) NOT NULL REFERENCES approval_requests(request_id),

    -- Decision
    decision VARCHAR(20) NOT NULL,

    -- Reviewer Information
    reviewer VARCHAR(100) NOT NULL,  -- Email or username
    decided_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Justification
    justification TEXT NOT NULL,

    -- Optional: Git context if merge was involved
    review_branch VARCHAR(200),
    merge_commit VARCHAR(40),

    -- Constraints
    CONSTRAINT chk_decision_valid CHECK (decision IN ('approved', 'rejected', 'deferred'))
);

COMMENT ON TABLE approval_decisions IS 'Human decisions on HITL approval requests';
COMMENT ON COLUMN approval_decisions.reviewer IS 'User who made the decision';
COMMENT ON COLUMN approval_decisions.justification IS 'Reason for decision (required)';


-- ==============================================================================
-- Indexes for efficient polling
-- ==============================================================================

CREATE INDEX IF NOT EXISTS idx_approval_requests_status
    ON approval_requests(status)
    WHERE status = 'pending';

CREATE INDEX IF NOT EXISTS idx_approval_requests_task
    ON approval_requests(task_id);

CREATE INDEX IF NOT EXISTS idx_approval_decisions_request
    ON approval_decisions(request_id);


-- ==============================================================================
-- Trigger: Auto-update request status when decision is made
-- ==============================================================================

CREATE OR REPLACE FUNCTION update_request_status()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE approval_requests
    SET status = NEW.decision
    WHERE request_id = NEW.request_id;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_update_request_status
    AFTER INSERT ON approval_decisions
    FOR EACH ROW
    EXECUTE FUNCTION update_request_status();


-- ==============================================================================
-- Completion Message
-- ==============================================================================

DO $$
BEGIN
    RAISE NOTICE 'HITL approval tables created successfully!';
    RAISE NOTICE 'Use approval_requests for pending requests, approval_decisions for outcomes';
END $$;
