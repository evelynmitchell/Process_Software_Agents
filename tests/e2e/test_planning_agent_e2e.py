"""
End-to-End tests for Planning Agent with real or mocked Anthropic API

These tests validate the complete workflow with either:
- Real Anthropic API if ANTHROPIC_API_KEY is set (will consume API credits)
- Mock LLM client if API key is not available (for testing without API access)

Tests are marked with @pytest.mark.e2e and can be run with:
    pytest tests/e2e/ -m e2e

Note: When running with mock LLM, tests validate the structure and flow,
but not the actual LLM reasoning quality.
"""

import os
import pytest
from pathlib import Path

from asp.agents.planning_agent import PlanningAgent
from asp.models.planning import TaskRequirements, ProjectPlan


@pytest.mark.e2e
class TestPlanningAgentE2E:
    """End-to-end tests with real or mocked API calls."""

    def test_simple_task_decomposition(self, llm_client):
        """Test decomposition of a simple REST API task."""
        agent = PlanningAgent(llm_client=llm_client)

        requirements = TaskRequirements(
            project_id="TEST-E2E",
            task_id="E2E-001",
            description="Build a simple REST API endpoint for user retrieval",
            requirements="""
            Create a GET /users/:id endpoint that:
            - Accepts a user ID as a path parameter
            - Queries the database for the user
            - Returns user data as JSON
            - Returns 404 if user not found
            - Includes basic error handling
            """,
        )

        # Execute with real API call
        plan = agent.execute(requirements)

        # Validate response structure
        assert isinstance(plan, ProjectPlan)
        assert plan.project_id == "TEST-E2E"
        assert plan.task_id == "E2E-001"
        assert len(plan.semantic_units) > 0
        assert plan.total_est_complexity > 0
        assert plan.probe_ai_enabled is False
        assert plan.agent_version == "1.0.0"

        # Validate semantic units
        for unit in plan.semantic_units:
            assert unit.unit_id.startswith("SU-")
            assert len(unit.description) >= 10
            assert 0 <= unit.api_interactions <= 10
            assert 0 <= unit.data_transformations <= 10
            assert 0 <= unit.logical_branches <= 10
            assert 0 <= unit.code_entities_modified <= 10
            assert 1.0 <= unit.novelty_multiplier <= 2.0
            assert unit.est_complexity > 0

        # Log results for calibration
        print(f"\n{'='*60}")
        print(f"E2E Test: Simple REST API Endpoint")
        print(f"{'='*60}")
        print(f"Units created: {len(plan.semantic_units)}")
        print(f"Total complexity: {plan.total_est_complexity}")
        print(f"\nSemantic Units:")
        for i, unit in enumerate(plan.semantic_units, 1):
            print(f"\n{i}. {unit.unit_id}: {unit.description}")
            print(f"   Complexity: {unit.est_complexity}")
            print(
                f"   Factors: API={unit.api_interactions}, "
                f"Data={unit.data_transformations}, "
                f"Branches={unit.logical_branches}, "
                f"Entities={unit.code_entities_modified}, "
                f"Novelty={unit.novelty_multiplier}"
            )
            if unit.dependencies:
                print(f"   Dependencies: {', '.join(unit.dependencies)}")

    def test_moderate_complexity_task(self, llm_client):
        """Test decomposition of a moderate complexity authentication task."""
        agent = PlanningAgent(llm_client=llm_client)

        requirements = TaskRequirements(
            project_id="TEST-E2E",
            task_id="E2E-002",
            description="Implement JWT-based user authentication system",
            requirements="""
            Build authentication system with:
            - User registration endpoint with email/password
            - Password hashing using bcrypt
            - Login endpoint that generates JWT tokens
            - JWT token validation middleware
            - Refresh token mechanism
            - Input validation and sanitization
            - Rate limiting for login attempts
            - Error handling and logging
            """,
        )

        # Execute with real API call
        plan = agent.execute(requirements)

        # Validate response
        assert isinstance(plan, ProjectPlan)
        assert len(plan.semantic_units) >= 2  # Should be multiple units
        assert plan.total_est_complexity > 30  # Should be moderate complexity

        # Log results
        print(f"\n{'='*60}")
        print(f"E2E Test: JWT Authentication System")
        print(f"{'='*60}")
        print(f"Units created: {len(plan.semantic_units)}")
        print(f"Total complexity: {plan.total_est_complexity}")
        print(f"\nSemantic Units:")
        for i, unit in enumerate(plan.semantic_units, 1):
            print(f"\n{i}. {unit.unit_id}: {unit.description}")
            print(f"   Complexity: {unit.est_complexity}")
            print(
                f"   Factors: API={unit.api_interactions}, "
                f"Data={unit.data_transformations}, "
                f"Branches={unit.logical_branches}, "
                f"Entities={unit.code_entities_modified}, "
                f"Novelty={unit.novelty_multiplier}"
            )
            if unit.dependencies:
                print(f"   Dependencies: {', '.join(unit.dependencies)}")

    def test_with_context_files(self, llm_client):
        """Test decomposition with context files specified."""
        agent = PlanningAgent(llm_client=llm_client)

        requirements = TaskRequirements(
            project_id="TEST-E2E",
            task_id="E2E-003",
            description="Add pagination to existing user list endpoint",
            requirements="""
            Enhance the existing GET /users endpoint to support pagination:
            - Add page and per_page query parameters
            - Implement offset-based pagination
            - Return total count in response headers
            - Maintain backward compatibility
            - Update API documentation
            """,
            context_files=[
                "src/api/users.py",
                "src/models/user.py",
                "docs/api_spec.md",
            ],
        )

        # Execute with real API call
        plan = agent.execute(requirements)

        # Validate response
        assert isinstance(plan, ProjectPlan)
        assert len(plan.semantic_units) > 0

        # Log results
        print(f"\n{'='*60}")
        print(f"E2E Test: Add Pagination (with context)")
        print(f"{'='*60}")
        print(f"Context files: {', '.join(requirements.context_files)}")
        print(f"Units created: {len(plan.semantic_units)}")
        print(f"Total complexity: {plan.total_est_complexity}")
        print(f"\nSemantic Units:")
        for i, unit in enumerate(plan.semantic_units, 1):
            print(f"\n{i}. {unit.unit_id}: {unit.description}")
            print(f"   Complexity: {unit.est_complexity}")

    def test_complex_data_pipeline_task(self, llm_client):
        """Test decomposition of a complex data pipeline task."""
        agent = PlanningAgent(llm_client=llm_client)

        requirements = TaskRequirements(
            project_id="TEST-E2E",
            task_id="E2E-004",
            description="Build ETL pipeline for processing customer event data",
            requirements="""
            Create data pipeline that:
            - Ingests events from Kafka topic
            - Validates and cleanses event data
            - Enriches events with customer metadata from PostgreSQL
            - Transforms events into analytics schema
            - Aggregates events by time windows (hourly, daily)
            - Writes results to data warehouse (Snowflake)
            - Implements error handling and dead letter queue
            - Adds monitoring and alerting
            - Ensures idempotency for reprocessing
            - Optimizes for throughput (target: 10k events/sec)
            """,
        )

        # Execute with real API call
        plan = agent.execute(requirements)

        # Validate response
        assert isinstance(plan, ProjectPlan)
        assert len(plan.semantic_units) >= 3  # Complex task should have many units
        assert plan.total_est_complexity > 60  # Should be high complexity

        # Check for dependency graph
        unit_ids = {unit.unit_id for unit in plan.semantic_units}
        has_dependencies = any(unit.dependencies for unit in plan.semantic_units)
        assert has_dependencies, "Complex task should have dependencies between units"

        # Validate all dependencies reference existing units
        for unit in plan.semantic_units:
            for dep in unit.dependencies:
                assert dep in unit_ids, f"Dependency {dep} not found in unit IDs"

        # Log results
        print(f"\n{'='*60}")
        print(f"E2E Test: Complex ETL Data Pipeline")
        print(f"{'='*60}")
        print(f"Units created: {len(plan.semantic_units)}")
        print(f"Total complexity: {plan.total_est_complexity}")
        print(f"\nDependency Graph:")
        for i, unit in enumerate(plan.semantic_units, 1):
            print(f"\n{i}. {unit.unit_id}: {unit.description[:60]}...")
            print(f"   Complexity: {unit.est_complexity}")
            if unit.dependencies:
                print(f"   Depends on: {', '.join(unit.dependencies)}")
            else:
                print(f"   Dependencies: None (can start immediately)")

    def test_telemetry_integration(self, llm_client):
        """Test that telemetry is captured during execution."""
        # Use a real database path for telemetry
        db_path = Path("data/asp_telemetry.db")
        agent = PlanningAgent(db_path=db_path, llm_client=llm_client)

        requirements = TaskRequirements(
            project_id="TEST-E2E",
            task_id="E2E-TELEMETRY-001",
            description="Simple task to test telemetry",
            requirements="""
            Create a health check endpoint:
            - GET /health returns 200 OK
            - Returns JSON with status and timestamp
            """,
        )

        # Execute with telemetry enabled
        plan = agent.execute(requirements)

        # Validate basic execution
        assert isinstance(plan, ProjectPlan)
        assert len(plan.semantic_units) > 0

        print(f"\n{'='*60}")
        print(f"E2E Test: Telemetry Integration")
        print(f"{'='*60}")
        print(f"Telemetry captured for task: {requirements.task_id}")
        print(f"Database: {db_path}")
        print(f"Check Langfuse dashboard for trace data")
        print(
            f"Run: uv run python scripts/query_telemetry.py --task-id {requirements.task_id}"
        )


@pytest.mark.e2e
@pytest.mark.calibration
class TestComplexityCalibration:
    """Tests for calibrating complexity scoring."""

    def test_trivial_task_complexity(self, llm_client):
        """Test that trivial tasks score low complexity (< 10)."""
        agent = PlanningAgent(llm_client=llm_client)

        requirements = TaskRequirements(
            project_id="CALIBRATION",
            task_id="CAL-TRIVIAL-001",
            description="Add a single log statement to existing function",
            requirements="""
            Add a log statement at the beginning of the processUser() function
            that logs the user ID. No other changes needed.
            """,
        )

        plan = agent.execute(requirements)

        print(f"\n{'='*60}")
        print(f"Calibration: Trivial Task")
        print(f"{'='*60}")
        print(f"Expected: Complexity < 10")
        print(f"Actual: {plan.total_est_complexity}")
        print(f"Result: {' PASS' if plan.total_est_complexity <= 10 else ' FAIL'}")

    def test_simple_task_complexity(self, llm_client):
        """Test that simple tasks score 11-30 complexity."""
        agent = PlanningAgent(llm_client=llm_client)

        requirements = TaskRequirements(
            project_id="CALIBRATION",
            task_id="CAL-SIMPLE-001",
            description="Add input validation to existing endpoint",
            requirements="""
            Add input validation to POST /users endpoint:
            - Validate email format
            - Validate password length (min 8 chars)
            - Return 400 with error message for invalid input
            """,
        )

        plan = agent.execute(requirements)

        print(f"\n{'='*60}")
        print(f"Calibration: Simple Task")
        print(f"{'='*60}")
        print(f"Expected: Complexity 11-30")
        print(f"Actual: {plan.total_est_complexity}")
        print(
            f"Result: {' PASS' if 11 <= plan.total_est_complexity <= 30 else ' FAIL'}"
        )

    def test_moderate_task_complexity(self, llm_client):
        """Test that moderate tasks score 31-60 complexity."""
        agent = PlanningAgent(llm_client=llm_client)

        requirements = TaskRequirements(
            project_id="CALIBRATION",
            task_id="CAL-MODERATE-001",
            description="Implement rate limiting middleware",
            requirements="""
            Create Express middleware for rate limiting:
            - Track requests per IP address
            - Use Redis for distributed rate limiting
            - Configurable limits (requests per minute)
            - Return 429 when limit exceeded
            - Include Retry-After header
            - Add monitoring metrics
            """,
        )

        plan = agent.execute(requirements)

        print(f"\n{'='*60}")
        print(f"Calibration: Moderate Task")
        print(f"{'='*60}")
        print(f"Expected: Complexity 31-60")
        print(f"Actual: {plan.total_est_complexity}")
        print(
            f"Result: {' PASS' if 31 <= plan.total_est_complexity <= 60 else ' FAIL'}"
        )


@pytest.mark.e2e
class TestPlanningAgentUnhappyPaths:
    """Tests for error handling and edge cases."""

    def test_minimal_requirements(self, llm_client):
        """Test handling of minimal requirements string."""
        agent = PlanningAgent(llm_client=llm_client)

        requirements = TaskRequirements(
            project_id="TEST-E2E",
            task_id="E2E-ERROR-001",
            description="Minimal requirements test",
            requirements="Create a simple endpoint",  # Minimal but valid
        )

        # Should still return a valid plan, even if minimal
        plan = agent.execute(requirements)
        assert isinstance(plan, ProjectPlan)
        assert plan.project_id == "TEST-E2E"
        assert plan.task_id == "E2E-ERROR-001"

    def test_very_vague_requirements(self, llm_client):
        """Test handling of vague/unclear requirements."""
        agent = PlanningAgent(llm_client=llm_client)

        requirements = TaskRequirements(
            project_id="TEST-E2E",
            task_id="E2E-ERROR-002",
            description="Do something",
            requirements="Make it work better somehow",  # Vague but valid length
        )

        # Should still produce a plan, even if it's generic
        plan = agent.execute(requirements)
        assert isinstance(plan, ProjectPlan)
        assert len(plan.semantic_units) > 0

    def test_extremely_long_requirements(self, llm_client):
        """Test handling of very long requirements."""
        agent = PlanningAgent(llm_client=llm_client)

        # Generate a very long requirements string
        long_requirements = "\n".join(
            [
                f"- Requirement {i}: Implement feature {i} with comprehensive functionality"
                for i in range(100)
            ]
        )

        requirements = TaskRequirements(
            project_id="TEST-E2E",
            task_id="E2E-ERROR-003",
            description="Very complex system with many requirements",
            requirements=long_requirements,
        )

        # Should handle long input gracefully
        plan = agent.execute(requirements)
        assert isinstance(plan, ProjectPlan)
        assert len(plan.semantic_units) > 0

    def test_special_characters_in_requirements(self, llm_client):
        """Test handling of special characters in requirements."""
        agent = PlanningAgent(llm_client=llm_client)

        requirements = TaskRequirements(
            project_id="TEST-E2E",
            task_id="E2E-ERROR-004",
            description="API with special chars: <>&\"'`",
            requirements="""
            Create an API that handles:
            - JSON with quotes: {"key": "value"}
            - HTML tags: <div>content</div>
            - SQL: SELECT * FROM users WHERE name = 'O\\'Reilly'
            - Regex: ^[a-zA-Z0-9_]*$
            - URLs: https://example.com?param=value&other=123
            """,
        )

        # Should handle special characters without errors
        plan = agent.execute(requirements)
        assert isinstance(plan, ProjectPlan)
        assert len(plan.semantic_units) > 0

    def test_unicode_and_emojis_in_requirements(self, llm_client):
        """Test handling of unicode and emojis."""
        agent = PlanningAgent(llm_client=llm_client)

        requirements = TaskRequirements(
            project_id="TEST-E2E",
            task_id="E2E-ERROR-005",
            description="Multi-language app with emojis 🚀",
            requirements="""
            Create an app that supports:
            - English: Hello World
            - Spanish: Hola Mundo
            - Japanese: こんにちは世界
            - Chinese: 你好世界
            - Arabic: مرحبا بالعالم
            - Emojis: 🎉 🚀 💻 ✅
            """,
        )

        # Should handle unicode gracefully
        plan = agent.execute(requirements)
        assert isinstance(plan, ProjectPlan)
        assert len(plan.semantic_units) > 0

    def test_conflicting_requirements(self, llm_client):
        """Test handling of contradictory requirements."""
        agent = PlanningAgent(llm_client=llm_client)

        requirements = TaskRequirements(
            project_id="TEST-E2E",
            task_id="E2E-ERROR-006",
            description="System with conflicting requirements",
            requirements="""
            Build a system that:
            1. Must be completely stateless
            2. Must track user sessions
            3. Must have no database
            4. Must persist user data permanently
            5. Must be real-time
            6. Must work offline without connectivity
            """,
        )

        # Should still produce a plan (agent will do its best)
        plan = agent.execute(requirements)
        assert isinstance(plan, ProjectPlan)
        assert len(plan.semantic_units) > 0

    def test_missing_context_files(self, llm_client):
        """Test handling of non-existent context files."""
        agent = PlanningAgent(llm_client=llm_client)

        requirements = TaskRequirements(
            project_id="TEST-E2E",
            task_id="E2E-ERROR-007",
            description="Update non-existent files",
            requirements="Update the user authentication logic",
            context_files=[
                "src/nonexistent/file1.py",
                "src/missing/file2.py",
                "docs/not_real.md",
            ],
        )

        # Should handle gracefully (context files are just hints)
        plan = agent.execute(requirements)
        assert isinstance(plan, ProjectPlan)
        assert len(plan.semantic_units) > 0

    def test_invalid_task_id_format(self, llm_client):
        """Test with non-standard task ID format."""
        agent = PlanningAgent(llm_client=llm_client)

        requirements = TaskRequirements(
            project_id="TEST-E2E!!!",
            task_id="this_is_a_weird_id_12345",
            description="Test with unusual IDs",
            requirements="Create a simple health check endpoint",
        )

        # Should work regardless of ID format
        plan = agent.execute(requirements)
        assert isinstance(plan, ProjectPlan)
        assert plan.project_id == "TEST-E2E!!!"
        assert plan.task_id == "this_is_a_weird_id_12345"


if __name__ == "__main__":
    """Run E2E tests manually."""
    pytest.main([__file__, "-v", "-s", "-m", "e2e"])
