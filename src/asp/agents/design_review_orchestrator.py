"""
Design Review Orchestrator: Coordinates 6 specialist review agents in parallel.

Dispatches design specifications to:
- SecurityReviewAgent
- PerformanceReviewAgent
- DataIntegrityReviewAgent
- MaintainabilityReviewAgent
- ArchitectureReviewAgent
- APIDesignReviewAgent

Aggregates results, deduplicates issues, resolves conflicts, generates DesignReviewReport.
"""

import asyncio
import logging
from datetime import datetime
from typing import Any, Optional

from asp.agents.base_agent import AgentExecutionError, BaseAgent
from asp.agents.reviews import (
    APIDesignReviewAgent,
    ArchitectureReviewAgent,
    DataIntegrityReviewAgent,
    MaintainabilityReviewAgent,
    PerformanceReviewAgent,
    SecurityReviewAgent,
)
from asp.models.design import DesignSpecification
from asp.models.design_review import (
    ChecklistItemReview,
    DesignIssue,
    DesignReviewReport,
    ImprovementSuggestion,
)
from asp.telemetry.telemetry import track_agent_cost

logger = logging.getLogger(__name__)


class DesignReviewOrchestrator(BaseAgent):
    """
    Orchestrates parallel design review by 6 specialist agents.

    Coordinates: Security, Performance, DataIntegrity, Maintainability,
    Architecture, and APIDesign review agents.
    """

    def __init__(
        self,
        llm_client: Optional[Any] = None,
        db_path: Optional[str] = None,
    ):
        """
        Initialize Design Review Orchestrator.

        Args:
            llm_client: Optional LLM client instance (for testing/mocking)
            db_path: Optional database path (for testing)
        """
        super().__init__(
            agent_role="DesignReviewOrchestrator",
            agent_version="1.0.0",
            llm_client=llm_client,
            db_path=db_path,
        )

        # Initialize specialist agents
        self.specialists = {
            "security": SecurityReviewAgent(llm_client=llm_client, db_path=db_path),
            "performance": PerformanceReviewAgent(llm_client=llm_client, db_path=db_path),
            "data_integrity": DataIntegrityReviewAgent(llm_client=llm_client, db_path=db_path),
            "maintainability": MaintainabilityReviewAgent(llm_client=llm_client, db_path=db_path),
            "architecture": ArchitectureReviewAgent(llm_client=llm_client, db_path=db_path),
            "api_design": APIDesignReviewAgent(llm_client=llm_client, db_path=db_path),
        }

    @track_agent_cost(
        agent_role="DesignReviewOrchestrator",
        agent_version="1.0.0",
        task_id_param="design_spec.task_id",
    )
    def execute(
        self,
        design_spec: DesignSpecification,
        quality_standards: Optional[str] = None,
    ) -> DesignReviewReport:
        """
        Execute comprehensive design review using all specialist agents in parallel.

        Args:
            design_spec: DesignSpecification to review
            quality_standards: Optional additional quality standards

        Returns:
            DesignReviewReport with aggregated results from all specialists

        Raises:
            AgentExecutionError: If orchestration fails
        """
        logger.info(f"Starting orchestrated design review for task {design_spec.task_id}")
        start_time = datetime.now()

        try:
            # Step 1: Run automated validation checks
            logger.debug("Running automated validation checks")
            automated_checks = self._run_automated_checks(design_spec)

            # Step 2: Dispatch to all specialists in parallel
            logger.debug("Dispatching to 6 specialist agents in parallel")
            specialist_results = asyncio.run(self._dispatch_specialists(design_spec))

            # Step 3: Aggregate specialist results
            logger.debug("Aggregating specialist results")
            aggregated_issues, aggregated_suggestions = self._aggregate_results(
                specialist_results
            )

            # Step 4: Generate checklist review (from design spec's own checklist)
            checklist_review = self._generate_checklist_review(
                design_spec, aggregated_issues
            )

            # Step 5: Convert to Pydantic models
            issues_list = [DesignIssue(**issue) for issue in aggregated_issues]
            suggestions_list = [
                ImprovementSuggestion(**suggestion) for suggestion in aggregated_suggestions
            ]
            checklist_review_list = [
                ChecklistItemReview(**item) for item in checklist_review
            ]

            # Step 6: Calculate issue counts
            critical_count = sum(1 for issue in issues_list if issue.severity == "Critical")
            high_count = sum(1 for issue in issues_list if issue.severity == "High")
            medium_count = sum(1 for issue in issues_list if issue.severity == "Medium")
            low_count = sum(1 for issue in issues_list if issue.severity == "Low")

            # Step 7: Determine overall assessment
            if critical_count > 0 or high_count > 0:
                overall_assessment = "FAIL"
            elif medium_count > 0 or low_count > 0:
                overall_assessment = "NEEDS_IMPROVEMENT"
            else:
                overall_assessment = "PASS"

            # Step 8: Calculate review duration
            end_time = datetime.now()
            duration_ms = (end_time - start_time).total_seconds() * 1000

            # Step 9: Generate review ID
            review_id = self._generate_review_id(design_spec.task_id, start_time)

            # Step 10: Create review report
            report = DesignReviewReport(
                task_id=design_spec.task_id,
                review_id=review_id,
                timestamp=start_time,
                overall_assessment=overall_assessment,
                automated_checks=automated_checks,
                issues_found=issues_list,
                improvement_suggestions=suggestions_list,
                checklist_review=checklist_review_list,
                critical_issue_count=critical_count,
                high_issue_count=high_count,
                medium_issue_count=medium_count,
                low_issue_count=low_count,
                reviewer_agent="DesignReviewOrchestrator",
                agent_version="1.0.0",
                review_duration_ms=duration_ms,
            )

            logger.info(
                f"Orchestrated design review completed: {overall_assessment} "
                f"({critical_count}C/{high_count}H/{medium_count}M/{low_count}L issues)"
            )
            return report

        except Exception as e:
            logger.error(f"Orchestrated design review failed: {e}", exc_info=True)
            raise AgentExecutionError(f"Design review orchestration failed: {e}") from e

    async def _dispatch_specialists(
        self, design_spec: DesignSpecification
    ) -> dict[str, dict[str, Any]]:
        """
        Dispatch design spec to all 6 specialists in parallel.

        Args:
            design_spec: DesignSpecification to review

        Returns:
            Dictionary mapping specialist name to review results
        """
        async def run_specialist(name: str, agent: BaseAgent) -> tuple[str, dict[str, Any]]:
            """Run a single specialist review (async wrapper)."""
            try:
                # Run in thread pool since agents are synchronous
                loop = asyncio.get_event_loop()
                result = await loop.run_in_executor(None, agent.execute, design_spec)
                return (name, result)
            except Exception as e:
                logger.warning(f"{name} specialist failed: {e}")
                # Return empty results on failure (don't block other specialists)
                return (name, {"issues_found": [], "improvement_suggestions": []})

        # Launch all specialists in parallel
        tasks = [
            run_specialist(name, agent)
            for name, agent in self.specialists.items()
        ]

        results = await asyncio.gather(*tasks)

        return {name: result for name, result in results}

    def _aggregate_results(
        self, specialist_results: dict[str, dict[str, Any]]
    ) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        """
        Aggregate results from all specialists, deduplicating and resolving conflicts.

        Args:
            specialist_results: Results from all specialist agents

        Returns:
            Tuple of (aggregated_issues, aggregated_suggestions)
        """
        all_issues = []
        all_suggestions = []

        # Collect all issues and suggestions
        for specialist_name, result in specialist_results.items():
            all_issues.extend(result.get("issues_found", []))
            all_suggestions.extend(result.get("improvement_suggestions", []))

        # Deduplicate issues (simple approach: by evidence similarity)
        deduplicated_issues = self._deduplicate_issues(all_issues)

        # Deduplicate suggestions
        deduplicated_suggestions = self._deduplicate_suggestions(all_suggestions)

        logger.info(
            f"Aggregation: {len(all_issues)} issues → {len(deduplicated_issues)} unique, "
            f"{len(all_suggestions)} suggestions → {len(deduplicated_suggestions)} unique"
        )

        return deduplicated_issues, deduplicated_suggestions

    def _deduplicate_issues(self, issues: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """
        Deduplicate issues based on evidence similarity.

        Args:
            issues: List of all issues from specialists

        Returns:
            Deduplicated list of issues (max severity kept for duplicates)
        """
        # Group by evidence (simplified deduplication)
        evidence_map: dict[str, dict[str, Any]] = {}
        severity_order = {"Critical": 4, "High": 3, "Medium": 2, "Low": 1}

        for issue in issues:
            evidence = issue.get("evidence", "")
            if evidence in evidence_map:
                # Keep issue with higher severity
                existing_severity = severity_order.get(evidence_map[evidence]["severity"], 0)
                new_severity = severity_order.get(issue["severity"], 0)
                if new_severity > existing_severity:
                    evidence_map[evidence] = issue
            else:
                evidence_map[evidence] = issue

        return list(evidence_map.values())

    def _deduplicate_suggestions(
        self, suggestions: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """
        Deduplicate suggestions based on description similarity.

        Args:
            suggestions: List of all suggestions from specialists

        Returns:
            Deduplicated list of suggestions
        """
        # Group by description (simplified deduplication)
        desc_map: dict[str, dict[str, Any]] = {}

        for suggestion in suggestions:
            description = suggestion.get("description", "")
            if description not in desc_map:
                desc_map[description] = suggestion

        return list(desc_map.values())

    def _run_automated_checks(
        self, design_spec: DesignSpecification
    ) -> dict[str, bool]:
        """
        Run automated validation checks on the design specification.

        Args:
            design_spec: DesignSpecification to validate

        Returns:
            Dictionary of check results (check_name -> passed)
        """
        checks = {}

        # Check 1: Semantic unit coverage
        checks["semantic_coverage"] = len(design_spec.component_logic) > 0

        # Check 2: Circular dependencies
        checks["no_circular_deps"] = self._check_circular_dependencies(design_spec)

        # Check 3: Checklist completeness
        checks["checklist_complete"] = len(design_spec.design_review_checklist) >= 5
        checks["has_high_priority_items"] = any(
            item.severity in ["Critical", "High"]
            for item in design_spec.design_review_checklist
        )

        # Check 4: Schema-API consistency
        checks["schema_api_consistency"] = self._check_schema_api_consistency(design_spec)

        # Check 5: Component completeness
        checks["components_have_interfaces"] = all(
            len(comp.interfaces) > 0 for comp in design_spec.component_logic
        )

        logger.debug(f"Automated checks: {checks}")
        return checks

    def _check_circular_dependencies(self, design_spec: DesignSpecification) -> bool:
        """Check for circular dependencies in component graph."""
        graph: dict[str, list[str]] = {}
        for component in design_spec.component_logic:
            graph[component.component_name] = [
                dep
                for dep in component.dependencies
                if any(c.component_name == dep for c in design_spec.component_logic)
            ]

        def has_cycle(node: str, visited: set[str], rec_stack: set[str]) -> bool:
            visited.add(node)
            rec_stack.add(node)
            for neighbor in graph.get(node, []):
                if neighbor not in visited:
                    if has_cycle(neighbor, visited, rec_stack):
                        return True
                elif neighbor in rec_stack:
                    return True
            rec_stack.remove(node)
            return False

        visited: set[str] = set()
        for component in design_spec.component_logic:
            if component.component_name not in visited:
                if has_cycle(component.component_name, visited, set()):
                    return False
        return True

    def _check_schema_api_consistency(self, design_spec: DesignSpecification) -> bool:
        """Check basic consistency between schemas and APIs."""
        has_apis = len(design_spec.api_contracts) > 0
        has_schemas = len(design_spec.data_schemas) > 0

        if has_apis and not has_schemas:
            return False  # APIs without schemas
        return True

    def _generate_checklist_review(
        self,
        design_spec: DesignSpecification,
        issues: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """
        Generate checklist review based on original design checklist and found issues.

        Args:
            design_spec: Original design specification
            issues: Aggregated issues found

        Returns:
            List of ChecklistItemReview dictionaries
        """
        checklist_review = []

        for i, item in enumerate(design_spec.design_review_checklist):
            # Find related issues by matching category
            related_issues = [
                issue["issue_id"]
                for issue in issues
                if issue["category"] == item.category
            ]

            # Determine status
            if related_issues:
                # Check severity of related issues
                related_severities = [
                    issue["severity"]
                    for issue in issues
                    if issue["issue_id"] in related_issues
                ]
                has_critical_or_high = any(
                    s in ["Critical", "High"] for s in related_severities
                )
                status = "Fail" if has_critical_or_high else "Warning"
            else:
                status = "Pass"

            checklist_review.append({
                "checklist_item_id": f"CHECK-{i+1:03d}",
                "category": item.category,
                "description": item.description,
                "status": status,
                "notes": f"Found {len(related_issues)} related issues" if related_issues else "No issues found",
                "related_issues": related_issues,
            })

        return checklist_review

    def _generate_review_id(self, task_id: str, timestamp: datetime) -> str:
        """Generate unique review ID."""
        clean_task_id = "".join(
            c if c.isalnum() or c in ["-", "_"] else "" for c in task_id
        ).upper()

        date_str = timestamp.strftime("%Y%m%d")
        time_str = timestamp.strftime("%H%M%S")

        return f"REVIEW-{clean_task_id}-{date_str}-{time_str}"
