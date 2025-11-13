#!/usr/bin/env python3
"""
Example script demonstrating telemetry infrastructure usage.

This script shows how to use the telemetry decorators and manual logging functions.

Usage:
    uv run python examples/telemetry_example.py
"""

import time
from asp.telemetry import track_agent_cost, log_defect, log_agent_metric


# ============================================================================
# Example 1: Using @track_agent_cost decorator
# ============================================================================

@track_agent_cost(
    agent_role="Planning",
    llm_model="claude-sonnet-4",
    llm_provider="anthropic",
    agent_version="1.0.0"
)
def plan_task(task_id: str, description: str) -> dict:
    """
    Example Planning Agent function with telemetry.

    The decorator will automatically track:
    - Execution latency
    - Success/failure status
    - Log to both Langfuse and SQLite
    """
    print(f"Planning task: {task_id}")
    print(f"Description: {description}")

    # Simulate some work
    time.sleep(0.5)

    # Return decomposed tasks
    return {
        "task_id": task_id,
        "subtasks": [
            {"id": f"{task_id}-1", "description": "Design the system"},
            {"id": f"{task_id}-2", "description": "Implement the code"},
            {"id": f"{task_id}-3", "description": "Write tests"},
        ],
        "estimated_complexity": 8.5,
    }


# ============================================================================
# Example 2: Using @log_defect decorator
# ============================================================================

@log_defect(
    defect_type="6_Conventional_Code_Bug",
    severity="High",
    phase_injected="Implementation",
    phase_removed="Review"
)
def fix_logic_error(task_id: str, error_description: str) -> dict:
    """
    Example function that logs a defect when called.

    The decorator will track:
    - Time to fix
    - Defect metadata
    - Log to both Langfuse and SQLite
    """
    print(f"Fixing logic error in task: {task_id}")
    print(f"Error: {error_description}")

    # Simulate fixing the error
    time.sleep(0.3)

    return {
        "task_id": task_id,
        "fixed": True,
        "fix_description": "Updated conditional logic in validation function",
    }


# ============================================================================
# Example 3: Manual logging of additional metrics
# ============================================================================

@track_agent_cost(
    agent_role="Code",
    llm_model="claude-sonnet-4",
    llm_provider="anthropic"
)
def implement_feature(task_id: str, feature_spec: str) -> dict:
    """
    Example Code Agent with manual metric logging.

    In addition to automatic latency tracking, we manually log:
    - Token usage
    - API costs
    """
    print(f"Implementing feature: {task_id}")

    # Simulate LLM call and track tokens
    time.sleep(0.7)

    # Manually log additional metrics
    tokens_in = 1500
    tokens_out = 800
    api_cost = (tokens_in * 0.003 + tokens_out * 0.015) / 1000  # Example pricing

    log_agent_metric(
        task_id=task_id,
        agent_role="Code",
        metric_type="Tokens_In",
        metric_value=tokens_in,
        metric_unit="tokens",
        llm_model="claude-sonnet-4",
        llm_provider="anthropic",
    )

    log_agent_metric(
        task_id=task_id,
        agent_role="Code",
        metric_type="Tokens_Out",
        metric_value=tokens_out,
        metric_unit="tokens",
        llm_model="claude-sonnet-4",
        llm_provider="anthropic",
    )

    log_agent_metric(
        task_id=task_id,
        agent_role="Code",
        metric_type="API_Cost",
        metric_value=api_cost,
        metric_unit="USD",
        llm_model="claude-sonnet-4",
        llm_provider="anthropic",
    )

    return {
        "task_id": task_id,
        "code_generated": True,
        "tokens_used": tokens_in + tokens_out,
        "cost": api_cost,
    }


# ============================================================================
# Main execution
# ============================================================================

def main():
    """Run telemetry examples."""
    print("=" * 70)
    print("ASP Platform - Telemetry Infrastructure Demo")
    print("=" * 70)
    print()

    # Example 1: Planning Agent with automatic telemetry
    print("Example 1: Planning Agent with @track_agent_cost")
    print("-" * 70)
    result1 = plan_task(
        task_id="TASK-2025-001",
        description="Build a user authentication system"
    )
    print(f"Result: {result1}")
    print()

    # Example 2: Code Agent with manual metric logging
    print("Example 2: Code Agent with manual metric logging")
    print("-" * 70)
    result2 = implement_feature(
        task_id="TASK-2025-001-2",
        feature_spec="Implement JWT token validation"
    )
    print(f"Result: {result2}")
    print()

    # Example 3: Defect logging
    print("Example 3: Defect logging with @log_defect")
    print("-" * 70)
    result3 = fix_logic_error(
        task_id="TASK-2025-001-2",
        error_description="JWT validation fails for expired tokens"
    )
    print(f"Result: {result3}")
    print()

    print("=" * 70)
    print("Demo complete!")
    print()
    print("Next steps:")
    print("  1. Check your Langfuse dashboard at https://us.cloud.langfuse.com")
    print("  2. Query SQLite database at data/asp_telemetry.db")
    print("     Example: uv run python scripts/init_database.py --reset")
    print("=" * 70)


if __name__ == "__main__":
    main()
