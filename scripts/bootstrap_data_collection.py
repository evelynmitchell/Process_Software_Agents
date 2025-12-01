#!/usr/bin/env python3
"""
Bootstrap Data Collection Script

Runs the Planning Agent on 10+ diverse real-world software tasks to:
- Validate agent works on production scenarios
- Build bootstrap telemetry dataset
- Test complexity scoring calibration
- Identify edge cases or issues

Usage:
    python scripts/bootstrap_data_collection.py
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import json
import time
from datetime import datetime

from asp.agents.planning_agent import PlanningAgent
from asp.models.planning import TaskRequirements

# Define diverse real-world software tasks
BOOTSTRAP_TASKS = [
    # TRIVIAL COMPLEXITY (< 10)
    {
        "task_id": "BOOTSTRAP-001",
        "project_id": "ECOMMERCE",
        "description": "Add new configuration field to settings page",
        "requirements": """
        Add a single boolean toggle to the settings page for "Enable email notifications".
        - Add toggle to React settings component
        - Save value to user preferences in database
        - Load existing value on page load
        """,
        "expected_complexity": "trivial",
    },
    {
        "task_id": "BOOTSTRAP-002",
        "project_id": "ANALYTICS",
        "description": "Update copyright year in footer",
        "requirements": """
        Change the copyright year from 2024 to 2025 in the application footer.
        Update both web and mobile app footers.
        """,
        "expected_complexity": "trivial",
    },
    # SIMPLE COMPLEXITY (11-30)
    {
        "task_id": "BOOTSTRAP-003",
        "project_id": "BLOG",
        "description": "Implement basic comment system for blog posts",
        "requirements": """
        Add comment functionality to blog posts:
        - Create comments table with post_id, user_id, content, created_at
        - Add POST /posts/:id/comments endpoint
        - Add GET /posts/:id/comments endpoint with pagination
        - Display comments under blog posts
        - Basic validation (max 1000 chars, required fields)
        """,
        "expected_complexity": "simple",
    },
    {
        "task_id": "BOOTSTRAP-004",
        "project_id": "TASKMANAGER",
        "description": "Add task filtering by status and due date",
        "requirements": """
        Implement filtering for task list:
        - Add filter dropdown for status (pending, in_progress, completed)
        - Add date range picker for due dates
        - Update API to support filter query parameters
        - Preserve filters in URL query string
        - Update UI to show active filters with clear button
        """,
        "expected_complexity": "simple",
    },
    # MODERATE COMPLEXITY (31-60)
    {
        "task_id": "BOOTSTRAP-005",
        "project_id": "AUTH-SYSTEM",
        "description": "Implement OAuth2 social login with Google",
        "requirements": """
        Add Google OAuth2 authentication:
        - Integrate Google OAuth2 API with client ID/secret
        - Create OAuth callback endpoint
        - Handle authorization code exchange for tokens
        - Create or link user accounts based on Google email
        - Store OAuth tokens securely with encryption
        - Add "Sign in with Google" button to login page
        - Handle OAuth errors and token refresh
        - Add logout functionality
        """,
        "expected_complexity": "moderate",
    },
    {
        "task_id": "BOOTSTRAP-006",
        "project_id": "PAYMENT",
        "description": "Build Stripe payment integration for subscriptions",
        "requirements": """
        Implement Stripe subscription payments:
        - Set up Stripe API integration with webhooks
        - Create subscription plans (monthly, annual)
        - Implement checkout flow with Stripe Elements
        - Handle successful payment webhooks
        - Handle failed payment webhooks with retry logic
        - Update user subscription status in database
        - Send confirmation emails
        - Add subscription management page (upgrade, cancel)
        - Handle proration for plan changes
        - Implement invoice generation
        """,
        "expected_complexity": "moderate",
    },
    {
        "task_id": "BOOTSTRAP-007",
        "project_id": "FILEUPLOAD",
        "description": "Implement file upload with S3 and virus scanning",
        "requirements": """
        Build secure file upload system:
        - Accept file uploads via multipart form (max 50MB)
        - Validate file types (images, PDFs, docs)
        - Scan files with ClamAV before storage
        - Upload to AWS S3 with presigned URLs
        - Generate thumbnails for images
        - Store file metadata in database (name, size, type, s3_key)
        - Implement download endpoint with access control
        - Add progress indicator for uploads
        - Handle upload errors and retry logic
        """,
        "expected_complexity": "moderate",
    },
    # COMPLEX COMPLEXITY (61-100)
    {
        "task_id": "BOOTSTRAP-008",
        "project_id": "CHAT",
        "description": "Build real-time chat with WebSocket and message history",
        "requirements": """
        Implement real-time chat application:
        - Set up WebSocket server with Socket.io
        - Create chat rooms with join/leave functionality
        - Implement real-time message broadcasting
        - Store message history in database with pagination
        - Add user presence indicators (online/offline)
        - Implement typing indicators
        - Add message read receipts
        - Support file attachments in messages
        - Implement message search functionality
        - Add push notifications for offline users
        - Handle WebSocket reconnection logic
        - Implement message encryption for privacy
        - Add rate limiting to prevent spam
        """,
        "expected_complexity": "complex",
    },
    {
        "task_id": "BOOTSTRAP-009",
        "project_id": "ANALYTICS",
        "description": "Build real-time analytics dashboard with streaming data",
        "requirements": """
        Create analytics dashboard with real-time updates:
        - Set up data streaming pipeline with Kafka
        - Create multiple consumer groups for different metrics
        - Implement WebSocket endpoint for live data updates
        - Build time-series database queries (1h, 24h, 7d, 30d views)
        - Create aggregation workers for hourly/daily rollups
        - Implement caching layer with Redis for hot data
        - Build interactive charts with drill-down capability
        - Add custom date range filtering
        - Implement data export functionality (CSV, JSON)
        - Add alerting system for threshold violations
        - Create API rate limiting per user tier
        - Implement data retention policies
        - Add audit logging for data access
        - Handle high-throughput data ingestion (10k events/sec)
        """,
        "expected_complexity": "complex",
    },
    {
        "task_id": "BOOTSTRAP-010",
        "project_id": "RECOMMENDATION",
        "description": "Build ML-powered product recommendation engine",
        "requirements": """
        Implement product recommendation system:
        - Collect user interaction data (views, clicks, purchases)
        - Build collaborative filtering model with surprise library
        - Train model on user-item interaction matrix
        - Implement content-based filtering using product attributes
        - Create hybrid recommendation combining both approaches
        - Set up batch training pipeline (daily model updates)
        - Build real-time inference API with caching
        - Implement A/B testing framework for recommendation algorithms
        - Add fallback recommendations for cold start users
        - Create recommendation explanation feature
        - Implement diversity and novelty metrics
        - Build admin dashboard for model performance monitoring
        - Add feature for manual recommendation overrides
        - Implement privacy controls for data usage
        - Scale to handle 1M+ users and 100k+ products
        """,
        "expected_complexity": "complex",
    },
    # EDGE CASES & SPECIAL SCENARIOS
    {
        "task_id": "BOOTSTRAP-011",
        "project_id": "MICROSERVICES",
        "description": "Implement distributed tracing across microservices",
        "requirements": """
        Add distributed tracing to microservices architecture:
        - Integrate OpenTelemetry SDK in all services
        - Set up trace context propagation via HTTP headers
        - Configure trace sampling (1% for production, 100% for staging)
        - Send traces to Jaeger backend
        - Add custom spans for critical operations
        - Implement trace correlation with logs
        - Add service dependency mapping
        - Create performance dashboards in Grafana
        - Set up alerting for high latency traces
        - Implement trace-based debugging tools
        """,
        "expected_complexity": "moderate",
    },
    {
        "task_id": "BOOTSTRAP-012",
        "project_id": "DATABASE",
        "description": "Implement database sharding for horizontal scaling",
        "requirements": """
        Add sharding to PostgreSQL database:
        - Design shard key strategy (user_id based)
        - Create shard routing logic in application layer
        - Set up multiple database instances (8 shards)
        - Implement shard-aware connection pooling
        - Add data migration scripts for resharding
        - Create monitoring for shard balance
        - Implement cross-shard queries for analytics
        - Add shard health checks and failover
        - Update ORM queries to be shard-aware
        - Document sharding architecture
        - Create runbooks for operational procedures
        - Test failure scenarios and recovery
        """,
        "expected_complexity": "complex",
    },
]


def run_bootstrap_collection():
    """Run Planning Agent on all bootstrap tasks and collect results."""

    print("=" * 80)
    print("BOOTSTRAP DATA COLLECTION - Planning Agent")
    print("=" * 80)
    print(f"Starting at: {datetime.now().isoformat()}")
    print(f"Total tasks: {len(BOOTSTRAP_TASKS)}")
    print()

    agent = PlanningAgent()
    results = []

    for i, task_def in enumerate(BOOTSTRAP_TASKS, 1):
        print(f"\n{'='*80}")
        print(f"TASK {i}/{len(BOOTSTRAP_TASKS)}: {task_def['task_id']}")
        print(f"{'='*80}")
        print(f"Description: {task_def['description']}")
        print(f"Expected: {task_def['expected_complexity']}")
        print()

        # Create TaskRequirements
        requirements = TaskRequirements(
            project_id=task_def["project_id"],
            task_id=task_def["task_id"],
            description=task_def["description"],
            requirements=task_def["requirements"],
        )

        # Execute Planning Agent
        start_time = time.time()
        try:
            plan = agent.execute(requirements)
            elapsed_time = time.time() - start_time

            # Display results
            print(f" SUCCESS")
            print(f"Units: {len(plan.semantic_units)}")
            print(f"Total Complexity: {plan.total_est_complexity}")
            print(f"Execution Time: {elapsed_time:.2f}s")
            print()

            # Show units
            for j, unit in enumerate(plan.semantic_units, 1):
                deps = (
                    f" (depends on: {', '.join(unit.dependencies)})"
                    if unit.dependencies
                    else ""
                )
                print(f"  {j}. {unit.unit_id}: {unit.description[:60]}...")
                print(
                    f"     Complexity: {unit.est_complexity} | "
                    f"API={unit.api_interactions}, "
                    f"Data={unit.data_transformations}, "
                    f"Branches={unit.logical_branches}, "
                    f"Entities={unit.code_entities_modified}, "
                    f"Novelty={unit.novelty_multiplier}{deps}"
                )

            # Store results
            result = {
                "task_id": task_def["task_id"],
                "project_id": task_def["project_id"],
                "description": task_def["description"],
                "expected_complexity": task_def["expected_complexity"],
                "actual_total_complexity": plan.total_est_complexity,
                "num_units": len(plan.semantic_units),
                "execution_time_seconds": elapsed_time,
                "units": [
                    {
                        "unit_id": u.unit_id,
                        "description": u.description,
                        "complexity": u.est_complexity,
                        "factors": {
                            "api_interactions": u.api_interactions,
                            "data_transformations": u.data_transformations,
                            "logical_branches": u.logical_branches,
                            "code_entities_modified": u.code_entities_modified,
                            "novelty_multiplier": u.novelty_multiplier,
                        },
                        "dependencies": u.dependencies,
                    }
                    for u in plan.semantic_units
                ],
                "success": True,
            }
            results.append(result)

        except Exception as e:
            elapsed_time = time.time() - start_time
            print(f" FAILED: {e}")
            print(f"Execution Time: {elapsed_time:.2f}s")

            result = {
                "task_id": task_def["task_id"],
                "project_id": task_def["project_id"],
                "description": task_def["description"],
                "expected_complexity": task_def["expected_complexity"],
                "execution_time_seconds": elapsed_time,
                "error": str(e),
                "success": False,
            }
            results.append(result)

    # Save results
    output_file = Path("data/bootstrap_results.json")
    output_file.parent.mkdir(exist_ok=True)

    with open(output_file, "w") as f:
        json.dump(
            {
                "timestamp": datetime.now().isoformat(),
                "total_tasks": len(BOOTSTRAP_TASKS),
                "successful": sum(1 for r in results if r["success"]),
                "failed": sum(1 for r in results if not r["success"]),
                "results": results,
            },
            f,
            indent=2,
        )

    print(f"\n{'='*80}")
    print("BOOTSTRAP COLLECTION COMPLETE")
    print(f"{'='*80}")
    print(f"Results saved to: {output_file}")
    print(f"Successful: {sum(1 for r in results if r['success'])}/{len(results)}")
    print(f"Failed: {sum(1 for r in results if not r['success'])}/{len(results)}")
    print()

    return results


if __name__ == "__main__":
    try:
        results = run_bootstrap_collection()

        # Summary analysis
        print("\n" + "=" * 80)
        print("COMPLEXITY ANALYSIS")
        print("=" * 80)

        successful = [r for r in results if r["success"]]

        # Group by expected complexity
        by_expected = {}
        for r in successful:
            expected = r["expected_complexity"]
            if expected not in by_expected:
                by_expected[expected] = []
            by_expected[expected].append(r["actual_total_complexity"])

        for expected, complexities in sorted(by_expected.items()):
            avg = sum(complexities) / len(complexities)
            min_c = min(complexities)
            max_c = max(complexities)
            print(f"\n{expected.upper()}: {len(complexities)} tasks")
            print(f"  Range: {min_c} - {max_c}")
            print(f"  Average: {avg:.1f}")
            print(f"  Values: {complexities}")

    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nFATAL ERROR: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
