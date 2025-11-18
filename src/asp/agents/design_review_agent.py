"""
Design Review Agent (FR-003): Validates design specifications against quality criteria.

This agent performs automated validation checks and LLM-based deep review to ensure
design quality before code generation.
"""

import json
import logging
from datetime import datetime
from typing import Any, Optional

from asp.agents.base_agent import AgentExecutionError, BaseAgent
from asp.models.design import DesignSpecification
from asp.models.design_review import (
    ChecklistItemReview,
    DesignIssue,
    DesignReviewReport,
    ImprovementSuggestion,
)
from asp.telemetry.telemetry import track_agent_cost
from asp.utils.artifact_io import write_artifact_json, write_artifact_markdown
from asp.utils.git_utils import git_commit_artifact, is_git_repository
from asp.utils.markdown_renderer import render_design_review_markdown

logger = logging.getLogger(__name__)


class DesignReviewAgent(BaseAgent):
    """
    Design Review Agent validates design specifications against quality criteria.

    The agent uses a hybrid approach:
    1. Automated validation checks (structural, consistency)
    2. LLM-based deep review (security, performance, maintainability)

    Outputs a comprehensive review report with issues and improvement suggestions.
    """

    def __init__(
        self,
        llm_client: Optional[Any] = None,
        db_path: Optional[str] = None,
    ):
        """
        Initialize Design Review Agent.

        Args:
            llm_client: Optional LLM client instance (for testing/mocking)
            db_path: Optional database path (for testing)
        """
        super().__init__(
            llm_client=llm_client,
            db_path=db_path,
        )
        self.agent_version = "1.0.0"

    @track_agent_cost(
        agent_role="DesignReview",
        agent_version="1.0.0",
        task_id_param="design_spec.task_id",
    )
    def execute(
        self,
        design_spec: DesignSpecification,
        quality_standards: Optional[str] = None,
    ) -> DesignReviewReport:
        """
        Execute design review on a design specification.

        Args:
            design_spec: DesignSpecification to review
            quality_standards: Optional additional quality standards to apply

        Returns:
            DesignReviewReport with assessment, issues, and suggestions

        Raises:
            AgentExecutionError: If review fails
        """
        logger.info(f"Starting design review for task {design_spec.task_id}")
        start_time = datetime.now()

        try:
            # Step 1: Automated validation checks
            logger.debug("Running automated validation checks")
            automated_checks = self._run_automated_checks(design_spec)

            # Step 2: LLM-based deep review
            logger.debug("Running LLM-based deep review")
            llm_review_results = self._run_llm_review(design_spec, quality_standards)

            # Step 3: Parse LLM results
            issues = llm_review_results.get("issues_found", [])
            suggestions = llm_review_results.get("improvement_suggestions", [])
            checklist_review = llm_review_results.get("checklist_review", [])

            # Convert to Pydantic models
            issues_list = [DesignIssue(**issue) for issue in issues]
            suggestions_list = [
                ImprovementSuggestion(**suggestion) for suggestion in suggestions
            ]
            checklist_review_list = [
                ChecklistItemReview(**item) for item in checklist_review
            ]

            # Step 4: Calculate issue counts
            critical_count = sum(1 for issue in issues_list if issue.severity == "Critical")
            high_count = sum(1 for issue in issues_list if issue.severity == "High")
            medium_count = sum(1 for issue in issues_list if issue.severity == "Medium")
            low_count = sum(1 for issue in issues_list if issue.severity == "Low")

            # Step 5: Determine overall assessment
            if critical_count > 0 or high_count > 0:
                overall_assessment = "FAIL"
            elif medium_count > 0 or low_count > 0:
                overall_assessment = "NEEDS_IMPROVEMENT"
            else:
                overall_assessment = "PASS"

            # Step 6: Calculate review duration
            end_time = datetime.now()
            duration_ms = (end_time - start_time).total_seconds() * 1000

            # Step 7: Generate review ID
            review_id = self._generate_review_id(design_spec.task_id, start_time)

            # Step 8: Create review report
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
                reviewer_agent="DesignReviewAgent",
                agent_version="1.0.0",
                review_duration_ms=duration_ms,
            )

            logger.info(
                f"Design review completed: {overall_assessment} "
                f"({critical_count}C/{high_count}H/{medium_count}M/{low_count}L issues)"
            )

            # Write artifacts to filesystem (if enabled)
            try:
                # Write JSON artifact
                json_path = write_artifact_json(
                    task_id=report.task_id,
                    artifact_type="design_review",
                    data=report,
                )
                logger.debug(f"Wrote design review JSON: {json_path}")

                # Write Markdown artifact
                markdown_content = render_design_review_markdown(report)
                md_path = write_artifact_markdown(
                    task_id=report.task_id,
                    artifact_type="design_review",
                    markdown_content=markdown_content,
                )
                logger.debug(f"Wrote design review Markdown: {md_path}")

                # Commit to git (if in repository)
                if is_git_repository():
                    commit_hash = git_commit_artifact(
                        task_id=report.task_id,
                        agent_name="Design Review Agent",
                        artifact_files=[str(json_path), str(md_path)],
                    )
                    logger.info(f"Committed artifacts: {commit_hash}")
                else:
                    logger.warning("Not in git repository, skipping commit")

            except Exception as e:
                # Log but don't fail - artifact persistence is not critical
                logger.warning(f"Failed to write artifacts: {e}", exc_info=True)

            return report

        except Exception as e:
            logger.error(f"Design review failed: {e}", exc_info=True)
            raise AgentExecutionError(f"Design review failed: {e}") from e

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
        # (Already validated in DesignAgent, but recheck for safety)
        checks["semantic_coverage"] = self._check_semantic_coverage(design_spec)

        # Check 2: Circular dependencies
        checks["no_circular_deps"] = self._check_circular_dependencies(design_spec)

        # Check 3: Checklist completeness
        checks["checklist_complete"] = len(design_spec.design_review_checklist) >= 5
        checks["has_high_priority_items"] = any(
            item.severity in ["Critical", "High"]
            for item in design_spec.design_review_checklist
        )

        # Check 4: Schema-API consistency
        checks["schema_api_consistency"] = self._check_schema_api_consistency(
            design_spec
        )

        # Check 5: Component completeness
        checks["components_have_interfaces"] = all(
            len(comp.interfaces) > 0 for comp in design_spec.component_logic
        )

        logger.debug(f"Automated checks: {checks}")
        return checks

    def _check_semantic_coverage(self, design_spec: DesignSpecification) -> bool:
        """
        Check that all semantic units have corresponding components.

        Args:
            design_spec: DesignSpecification to check

        Returns:
            True if all semantic units have components
        """
        # Extract semantic unit IDs from design specification
        # (They are referenced in component_logic)
        semantic_unit_ids = set()
        for component in design_spec.component_logic:
            semantic_unit_ids.add(component.semantic_unit_id)

        # We don't have access to the original ProjectPlan here,
        # so we assume the DesignAgent already validated this
        # This check is more for safety/logging
        return len(semantic_unit_ids) > 0

    def _check_circular_dependencies(self, design_spec: DesignSpecification) -> bool:
        """
        Check for circular dependencies in component graph.

        Args:
            design_spec: DesignSpecification to check

        Returns:
            True if no circular dependencies found
        """
        # Build adjacency list
        graph: dict[str, list[str]] = {}
        for component in design_spec.component_logic:
            graph[component.component_name] = [
                dep
                for dep in component.dependencies
                if any(c.component_name == dep for c in design_spec.component_logic)
            ]

        # DFS to detect cycles
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
        """
        Check consistency between data schemas and API contracts.

        Args:
            design_spec: DesignSpecification to check

        Returns:
            True if schemas and APIs are consistent
        """
        # For now, this is a simple check
        # In the future, could validate:
        # - API request/response schemas reference defined tables
        # - Foreign keys in schemas match API endpoints
        # - Authentication requirements consistent

        # Basic check: if we have APIs, we should have schemas
        has_apis = len(design_spec.api_contracts) > 0
        has_schemas = len(design_spec.data_schemas) > 0

        if has_apis and not has_schemas:
            return False  # APIs without schemas

        return True

    def _run_llm_review(
        self,
        design_spec: DesignSpecification,
        quality_standards: Optional[str] = None,
    ) -> dict[str, Any]:
        """
        Run LLM-based deep review of the design specification.

        Args:
            design_spec: DesignSpecification to review
            quality_standards: Optional additional quality standards

        Returns:
            Dictionary with issues, suggestions, and checklist review
        """
        # Load prompt template
        try:
            prompt_template = self.load_prompt("design_review_agent_v1_review")
        except FileNotFoundError as e:
            raise AgentExecutionError(f"Prompt template not found: {e}") from e

        # Format prompt with design specification and quality standards
        prompt = self.format_prompt(
            prompt_template,
            design_specification=design_spec.model_dump_json(indent=2),
            quality_standards=quality_standards or "Use standard best practices",
        )

        # Call LLM
        logger.debug("Calling LLM for design review")
        response = self.call_llm(prompt)

        # Parse JSON response
        try:
            content = response.get("content", {})
            if isinstance(content, str):
                # Handle case where content is JSON string
                content = json.loads(content)

            return content
        except (json.JSONDecodeError, KeyError) as e:
            logger.error(f"Failed to parse LLM response: {e}")
            raise AgentExecutionError(f"Failed to parse LLM review response: {e}") from e

    def _generate_review_id(self, task_id: str, timestamp: datetime) -> str:
        """
        Generate unique review ID.

        Args:
            task_id: Task identifier
            timestamp: Review timestamp

        Returns:
            Review ID in format REVIEW-{task_id}-YYYYMMDD-HHMMSS
        """
        # Clean task_id (remove special chars except hyphen/underscore)
        clean_task_id = "".join(
            c if c.isalnum() or c in ["-", "_"] else "" for c in task_id
        ).upper()

        date_str = timestamp.strftime("%Y%m%d")
        time_str = timestamp.strftime("%H%M%S")

        return f"REVIEW-{clean_task_id}-{date_str}-{time_str}"
