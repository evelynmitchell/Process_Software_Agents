-- ASP Telemetry Database - Sample Data (SQLite)
-- Version: 1.0
-- Date: 2025-11-12
-- Description: Inserts sample data for testing and validation

-- ==============================================================================
-- Sample Task Metadata
-- ==============================================================================

INSERT OR IGNORE INTO task_metadata (
    task_id, project_id, task_type, task_description,
    estimated_complexity, actual_complexity,
    semantic_units_json, estimated_cost_vector_json,
    components_affected, bootstrap_phase, status
) VALUES
(
    'TASK-001',
    'ASP-Platform',
    'authentication',
    'Implement user login with JWT tokens and session management',
    18,
    20,
    '{"semantic_units": [
        {"unit_id": "SU-001", "description": "Create JWT token generation function", "est_complexity": 8},
        {"unit_id": "SU-002", "description": "Implement session storage with Redis", "est_complexity": 10}
    ]}',
    '{"latency_ms": 35000, "tokens": 88000, "api_cost_usd": 0.14}',
    '["src/auth/login.py", "src/auth/jwt.py", "src/session/redis_store.py"]',
    'Learning',
    'completed'
),
(
    'TASK-002',
    'ASP-Platform',
    'database',
    'Create user profile table with migration scripts',
    10,
    12,
    '{"semantic_units": [
        {"unit_id": "SU-003", "description": "Design database schema", "est_complexity": 4},
        {"unit_id": "SU-004", "description": "Write migration script", "est_complexity": 6}
    ]}',
    '{"latency_ms": 22000, "tokens": 55000, "api_cost_usd": 0.09}',
    '["database/migrations/001_create_user_profiles.sql"]',
    'Learning',
    'completed'
),
(
    'TASK-003',
    'ASP-Platform',
    'api',
    'Build REST API endpoint for user profile CRUD operations',
    15,
    NULL,  -- Not completed yet
    '{"semantic_units": [
        {"unit_id": "SU-005", "description": "Create API routes", "est_complexity": 7},
        {"unit_id": "SU-006", "description": "Add input validation", "est_complexity": 5},
        {"unit_id": "SU-007", "description": "Write unit tests", "est_complexity": 3}
    ]}',
    '{"latency_ms": 28000, "tokens": 72000, "api_cost_usd": 0.12}',
    '["src/api/user_routes.py", "tests/test_user_api.py"]',
    'Shadow',
    'in_progress'
);

-- ==============================================================================
-- Sample Agent Cost Vector Data
-- ==============================================================================

-- TASK-001: Planning Agent execution
INSERT INTO agent_cost_vector (task_id, agent_role, metric_type, metric_value, metric_unit, llm_model, llm_provider, timestamp) VALUES
('TASK-001', 'Planning', 'Latency', 2150.50, 'ms', 'claude-sonnet-4', 'anthropic', datetime('now', '-5 days')),
('TASK-001', 'Planning', 'Tokens_In', 5240, 'tokens', 'claude-sonnet-4', 'anthropic', datetime('now', '-5 days')),
('TASK-001', 'Planning', 'Tokens_Out', 1820, 'tokens', 'claude-sonnet-4', 'anthropic', datetime('now', '-5 days')),
('TASK-001', 'Planning', 'API_Cost', 0.0382, 'USD', 'claude-sonnet-4', 'anthropic', datetime('now', '-5 days')),
('TASK-001', 'Planning', 'Tool_Calls', 2, 'count', 'claude-sonnet-4', 'anthropic', datetime('now', '-5 days'));

-- TASK-001: Design Agent execution
INSERT INTO agent_cost_vector (task_id, agent_role, metric_type, metric_value, metric_unit, llm_model, llm_provider, timestamp) VALUES
('TASK-001', 'Design', 'Latency', 3850.25, 'ms', 'claude-sonnet-4', 'anthropic', datetime('now', '-4 days', '-1 hours')),
('TASK-001', 'Design', 'Tokens_In', 8500, 'tokens', 'claude-sonnet-4', 'anthropic', datetime('now', '-4 days', '-1 hours')),
('TASK-001', 'Design', 'Tokens_Out', 3200, 'tokens', 'claude-sonnet-4', 'anthropic', datetime('now', '-4 days', '-1 hours')),
('TASK-001', 'Design', 'API_Cost', 0.0625, 'USD', 'claude-sonnet-4', 'anthropic', datetime('now', '-4 days', '-1 hours')),
('TASK-001', 'Design', 'Tool_Calls', 3, 'count', 'claude-sonnet-4', 'anthropic', datetime('now', '-4 days', '-1 hours'));

-- TASK-001: Design Review Agent execution
INSERT INTO agent_cost_vector (task_id, agent_role, metric_type, metric_value, metric_unit, llm_model, llm_provider, timestamp) VALUES
('TASK-001', 'DesignReview', 'Latency', 1950.75, 'ms', 'claude-sonnet-4', 'anthropic', datetime('now', '-4 days', '-2 hours')),
('TASK-001', 'DesignReview', 'Tokens_In', 4100, 'tokens', 'claude-sonnet-4', 'anthropic', datetime('now', '-4 days', '-2 hours')),
('TASK-001', 'DesignReview', 'Tokens_Out', 1200, 'tokens', 'claude-sonnet-4', 'anthropic', datetime('now', '-4 days', '-2 hours')),
('TASK-001', 'DesignReview', 'API_Cost', 0.0285, 'USD', 'claude-sonnet-4', 'anthropic', datetime('now', '-4 days', '-2 hours'));

-- TASK-001: Code Agent execution
INSERT INTO agent_cost_vector (task_id, agent_role, metric_type, metric_value, metric_unit, llm_model, llm_provider, timestamp) VALUES
('TASK-001', 'Code', 'Latency', 5200.50, 'ms', 'claude-sonnet-4', 'anthropic', datetime('now', '-4 days', '-4 hours')),
('TASK-001', 'Code', 'Tokens_In', 11000, 'tokens', 'claude-sonnet-4', 'anthropic', datetime('now', '-4 days', '-4 hours')),
('TASK-001', 'Code', 'Tokens_Out', 4500, 'tokens', 'claude-sonnet-4', 'anthropic', datetime('now', '-4 days', '-4 hours')),
('TASK-001', 'Code', 'API_Cost', 0.0825, 'USD', 'claude-sonnet-4', 'anthropic', datetime('now', '-4 days', '-4 hours')),
('TASK-001', 'Code', 'Tool_Calls', 5, 'count', 'claude-sonnet-4', 'anthropic', datetime('now', '-4 days', '-4 hours')),
('TASK-001', 'Code', 'Retries', 1, 'count', 'claude-sonnet-4', 'anthropic', datetime('now', '-4 days', '-4 hours'));

-- TASK-001: Code Review Agent execution (found 1 defect)
INSERT INTO agent_cost_vector (task_id, agent_role, metric_type, metric_value, metric_unit, llm_model, llm_provider, timestamp) VALUES
('TASK-001', 'CodeReview', 'Latency', 2850.25, 'ms', 'claude-sonnet-4', 'anthropic', datetime('now', '-4 days', '-5 hours')),
('TASK-001', 'CodeReview', 'Tokens_In', 6200, 'tokens', 'claude-sonnet-4', 'anthropic', datetime('now', '-4 days', '-5 hours')),
('TASK-001', 'CodeReview', 'Tokens_Out', 1800, 'tokens', 'claude-sonnet-4', 'anthropic', datetime('now', '-4 days', '-5 hours')),
('TASK-001', 'CodeReview', 'API_Cost', 0.0425, 'USD', 'claude-sonnet-4', 'anthropic', datetime('now', '-4 days', '-5 hours'));

-- TASK-001: Test Agent execution
INSERT INTO agent_cost_vector (task_id, agent_role, metric_type, metric_value, metric_unit, llm_model, llm_provider, timestamp) VALUES
('TASK-001', 'Test', 'Latency', 4100.00, 'ms', 'claude-sonnet-4', 'anthropic', datetime('now', '-4 days', '-6 hours')),
('TASK-001', 'Test', 'Tokens_In', 9500, 'tokens', 'claude-sonnet-4', 'anthropic', datetime('now', '-4 days', '-6 hours')),
('TASK-001', 'Test', 'Tokens_Out', 3800, 'tokens', 'claude-sonnet-4', 'anthropic', datetime('now', '-4 days', '-6 hours')),
('TASK-001', 'Test', 'API_Cost', 0.0715, 'USD', 'claude-sonnet-4', 'anthropic', datetime('now', '-4 days', '-6 hours')),
('TASK-001', 'Test', 'Tool_Calls', 8, 'count', 'claude-sonnet-4', 'anthropic', datetime('now', '-4 days', '-6 hours'));

-- ==============================================================================
-- Sample Defect Log Data
-- ==============================================================================

INSERT OR IGNORE INTO defect_log (
    defect_id, task_id, defect_type, severity, phase_injected, phase_removed,
    component_path, function_name, line_number, description, root_cause,
    effort_to_fix_json, flagged_by_agent, validated_by_human, false_positive,
    created_at, resolved_at
) VALUES
(
    'D-001',
    'TASK-001',
    '5_Security_Vulnerability',
    'Critical',
    'Code',
    'CodeReview',
    'src/auth/login.py',
    'authenticate_user',
    42,
    'SQL injection vulnerability - used string concatenation instead of parameterized query',
    'Agent generated SQL query using f-string with user input: f"SELECT * FROM users WHERE username = ''{username}''"',
    '{"latency_ms": 1250, "tokens": 850, "api_cost_usd": 0.015, "retries": 1}',
    1,   -- Code Review Agent found it (1 = TRUE)
    1,   -- Human confirmed it's real
    0,   -- Not a false positive (0 = FALSE)
    datetime('now', '-4 days', '-5 hours'),
    datetime('now', '-4 days', '-5 hours', '-30 minutes')
),
(
    'D-002',
    'TASK-001',
    '4_Hallucination',
    'High',
    'Code',
    'Test',
    'src/utils/crypto.py',
    'hash_password',
    15,
    'Agent imported non-existent library "bcrypt_pro" that does not exist in requirements',
    'Agent hallucinated an enhanced bcrypt library that does not exist. Actual library should be standard "bcrypt"',
    '{"latency_ms": 2100, "tokens": 1200, "api_cost_usd": 0.022, "retries": 2}',
    0,  -- Test Agent found it (escaped Code Review!)
    1,  -- Human confirmed
    0,
    datetime('now', '-4 days', '-6 hours'),
    datetime('now', '-4 days', '-6 hours', '-15 minutes')
),
(
    'D-003',
    'TASK-002',
    '6_Conventional_Code_Bug',
    'Medium',
    'Code',
    'CodeReview',
    'database/migrations/001_create_user_profiles.sql',
    NULL,
    8,
    'Missing NOT NULL constraint on email column which is required field',
    'Agent did not add NOT NULL to email VARCHAR(255) column definition',
    '{"latency_ms": 800, "tokens": 450, "api_cost_usd": 0.008, "retries": 1}',
    1,   -- Code Review Agent found it
    1,   -- Human confirmed
    0,
    datetime('now', '-3 days', '-12 hours'),
    datetime('now', '-3 days', '-12 hours', '-10 minutes')
),
(
    'D-004',
    'TASK-002',
    '2_Prompt_Misinterpretation',
    'Low',
    'Design',
    'DesignReview',
    NULL,
    NULL,
    NULL,
    'Agent did not include user avatar field in schema despite requirement mentioning "profile with picture"',
    'Agent misinterpreted "profile" to only mean text fields (name, email, bio) and missed the avatar/picture requirement',
    '{"latency_ms": 1500, "tokens": 920, "api_cost_usd": 0.017, "retries": 1}',
    1,   -- Design Review Agent found it
    1,   -- Human confirmed
    0,
    datetime('now', '-3 days', '-13 hours'),
    datetime('now', '-3 days', '-13 hours', '-30 minutes')
);

-- ==============================================================================
-- Sample Bootstrap Metrics Data
-- ==============================================================================

INSERT INTO bootstrap_metrics (
    capability_name, capability_mode, tasks_completed, tasks_required_for_graduation,
    primary_metric_name, primary_metric_value, primary_metric_target,
    secondary_metrics_json, graduation_criteria_met, graduation_notes,
    measured_at, measurement_period_start, measurement_period_end
) VALUES
(
    'PROBE_AI',
    'Learning',
    3,
    10,
    'MAPE',
    NULL,  -- Not enough data yet
    20.0,
    '{"r_squared": null, "tasks_with_estimates": 3}',
    0,  -- FALSE
    'Need 7 more tasks before PROBE-AI can be evaluated',
    datetime('now'),
    datetime('now', '-5 days'),
    datetime('now')
),
(
    'TaskDecomposition',
    'Learning',
    3,
    15,
    'Correction_Rate',
    33.33,  -- 1 out of 3 tasks required corrections
    10.0,
    '{"completeness_score": 85.0, "sequencing_score": 90.0, "human_corrections": 1}',
    0,  -- FALSE
    'Correction rate too high (33% > 10%). Need to improve Planning Agent prompts.',
    datetime('now'),
    datetime('now', '-5 days'),
    datetime('now')
),
(
    'ReviewAgent_Code',
    'Learning',
    2,
    20,
    'True_Positive_Rate',
    100.0,  -- 2 out of 2 flags were real defects
    80.0,
    '{"false_positive_rate": 0.0, "escape_rate": 50.0, "defects_found": 2, "defects_escaped": 1}',
    0,  -- FALSE
    'True Positive rate excellent (100%), but escape rate too high (50%). One defect slipped through to Test phase.',
    datetime('now'),
    datetime('now', '-5 days'),
    datetime('now')
),
(
    'ErrorProneDetection',
    'Learning',
    2,
    30,
    'Defects_Logged',
    4,
    30,
    '{"high_risk_components": ["src/auth/login.py"], "high_risk_task_types": ["authentication"]}',
    0,  -- FALSE
    'Only 2 tasks completed. Need 28 more before risk map is statistically significant.',
    datetime('now'),
    datetime('now', '-5 days'),
    datetime('now')
);

-- ==============================================================================
-- Update Aggregated Fields in task_metadata
-- ==============================================================================

-- Calculate actual cost vector for completed tasks
UPDATE task_metadata
SET actual_cost_vector_json = (
    SELECT json_object(
        'latency_ms', SUM(CASE WHEN metric_type = 'Latency' THEN metric_value ELSE 0 END),
        'tokens', SUM(CASE WHEN metric_type = 'Tokens_In' THEN metric_value ELSE 0 END) +
                  SUM(CASE WHEN metric_type = 'Tokens_Out' THEN metric_value ELSE 0 END),
        'api_cost_usd', SUM(CASE WHEN metric_type = 'API_Cost' THEN metric_value ELSE 0 END)
    )
    FROM agent_cost_vector
    WHERE agent_cost_vector.task_id = task_metadata.task_id
)
WHERE status = 'completed';

-- Calculate defect counts
UPDATE task_metadata
SET defect_count = (
    SELECT COUNT(*)
    FROM defect_log
    WHERE defect_log.task_id = task_metadata.task_id
),
defect_density = (
    SELECT CAST(COUNT(*) AS REAL) / NULLIF(actual_complexity, 0)
    FROM defect_log
    WHERE defect_log.task_id = task_metadata.task_id
)
WHERE status = 'completed';

-- ==============================================================================
-- Verification Queries
-- ==============================================================================

-- Show sample task summary
SELECT
    task_id,
    task_type,
    status,
    estimated_complexity,
    actual_complexity,
    defect_count,
    defect_density
FROM task_metadata
ORDER BY created_at;
