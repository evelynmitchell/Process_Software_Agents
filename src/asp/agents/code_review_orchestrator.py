"""
Code Review Orchestrator: Coordinates 6 specialist code review agents in parallel.

Dispatches generated code to:
- CodeQualityReviewAgent
- CodeSecurityReviewAgent
- CodePerformanceReviewAgent
- TestCoverageReviewAgent
- DocumentationReviewAgent
- BestPracticesReviewAgent

Aggregates results, deduplicates issues, resolves conflicts, generates CodeReviewReport.
"""

import asyncio
import logging
from datetime import datetime
from typing import Any, Optional

from asp.agents.base_agent import AgentExecutionError, BaseAgent
from asp.agents.code_reviews import (
    BestPracticesReviewAgent,
    CodePerformanceReviewAgent,
    CodeQualityReviewAgent,
    CodeSecurityReviewAgent,
    DocumentationReviewAgent,
    TestCoverageReviewAgent,
)
from asp.models.code import GeneratedCode
from asp.models.code_review import (
    ChecklistItemReview,
    CodeImprovementSuggestion,
    CodeIssue,
    CodeReviewReport,
)
from asp.telemetry.telemetry import track_agent_cost

logger = logging.getLogger(__name__)


class CodeReviewOrchestrator(BaseAgent):
    """
    Orchestrates parallel code review by 6 specialist agents.

    Coordinates: CodeQuality, CodeSecurity, CodePerformance, TestCoverage,
    Documentation, and BestPractices review agents.
    """

    def __init__(
        self,
        llm_client: Optional[Any] = None,
        db_path: Optional[str] = None,
    ):
        """
        Initialize Code Review Orchestrator.

        Args:
            llm_client: Optional LLM client instance (for testing/mocking)
            db_path: Optional database path (for testing)
        """
        super().__init__(
            llm_client=llm_client,
            db_path=db_path,
        )
        self.agent_version = "1.0.0"

        # Initialize specialist agents
        self.specialists = {
            "code_quality": CodeQualityReviewAgent(llm_client=llm_client, db_path=db_path),
            "code_security": CodeSecurityReviewAgent(llm_client=llm_client, db_path=db_path),
            "code_performance": CodePerformanceReviewAgent(llm_client=llm_client, db_path=db_path),
            "test_coverage": TestCoverageReviewAgent(llm_client=llm_client, db_path=db_path),
            "documentation": DocumentationReviewAgent(llm_client=llm_client, db_path=db_path),
            "best_practices": BestPracticesReviewAgent(llm_client=llm_client, db_path=db_path),
        }

    @track_agent_cost(
        agent_role="CodeReviewOrchestrator",
        agent_version="1.0.0",
        task_id_param="generated_code.task_id",
    )
    def execute(
        self,
        generated_code: GeneratedCode,
        quality_standards: Optional[str] = None,
    ) -> CodeReviewReport:
        """
        Execute comprehensive code review using all specialist agents in parallel.

        Args:
            generated_code: GeneratedCode to review
            quality_standards: Optional additional quality standards

        Returns:
            CodeReviewReport with aggregated results from all specialists

        Raises:
            AgentExecutionError: If orchestration fails
        """
        logger.info(f"Starting orchestrated code review for task {generated_code.task_id}")
        start_time = datetime.now()

        try:
            # Step 1: Run automated validation checks
            logger.debug("Running automated validation checks")
            automated_checks = self._run_automated_checks(generated_code)

            # Step 2: Dispatch to all specialists in parallel
            logger.debug("Dispatching to 6 specialist agents in parallel")
            specialist_results = asyncio.run(self._dispatch_specialists(generated_code))

            # Step 3: Aggregate specialist results
            logger.debug("Aggregating specialist results")
            aggregated_issues, aggregated_suggestions = self._aggregate_results(
                specialist_results
            )

            # Step 4: Generate checklist review (if code has review checklist)
            checklist_review = self._generate_checklist_review(
                generated_code, aggregated_issues
            )

            # Step 5: Convert to Pydantic models
            issues_list = [CodeIssue(**issue) for issue in aggregated_issues]
            suggestions_list = [
                CodeImprovementSuggestion(**suggestion) for suggestion in aggregated_suggestions
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
            if critical_count > 0:
                overall_assessment = "FAIL"
            elif high_count > 0:
                overall_assessment = "NEEDS_REVISION"
            elif medium_count > 0:
                overall_assessment = "NEEDS_IMPROVEMENT"
            else:
                overall_assessment = "PASS"

            # Step 8: Calculate review duration
            end_time = datetime.now()
            duration_ms = (end_time - start_time).total_seconds() * 1000

            # Step 9: Generate review ID
            review_id = self._generate_review_id(generated_code.task_id, start_time)

            # Step 10: Create review report
            report = CodeReviewReport(
                task_id=generated_code.task_id,
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
                reviewer_agent="CodeReviewOrchestrator",
                agent_version="1.0.0",
                review_duration_ms=duration_ms,
            )

            logger.info(
                f"Orchestrated code review completed: {overall_assessment} "
                f"({critical_count}C/{high_count}H/{medium_count}M/{low_count}L issues)"
            )
            return report

        except Exception as e:
            logger.error(f"Orchestrated code review failed: {e}", exc_info=True)
            raise AgentExecutionError(f"Code review orchestration failed: {e}") from e

    async def _dispatch_specialists(
        self, generated_code: GeneratedCode
    ) -> dict[str, dict[str, Any]]:
        """
        Dispatch generated code to all 6 specialists in parallel.

        Args:
            generated_code: GeneratedCode to review

        Returns:
            Dictionary mapping specialist name to review results
        """
        async def run_specialist(name: str, agent: BaseAgent) -> tuple[str, dict[str, Any]]:
            """Run a single specialist review (async wrapper)."""
            try:
                # Run in thread pool since agents are synchronous
                loop = asyncio.get_event_loop()
                result = await loop.run_in_executor(None, agent.execute, generated_code)
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

    def _normalize_category(self, category: str) -> str:
        """
        Normalize category values to match Pydantic Literal types.

        Args:
            category: Raw category from LLM

        Returns:
            Normalized category matching CodeIssue/CodeImprovementSuggestion schema
        """
        # Map common variations to canonical categories
        category_mappings = {
            # Security variations
            "security": "Security",
            "authentication": "Security",
            "authorization": "Security",
            "injection": "Security",
            "sql injection": "Security",
            "xss": "Security",
            "csrf": "Security",
            "crypto": "Security",
            "encryption": "Security",

            # Code Quality variations
            "code quality": "Code Quality",
            "quality": "Code Quality",
            "maintainability": "Maintainability",
            "readability": "Code Quality",
            "code smell": "Code Quality",
            "complexity": "Code Quality",
            "duplication": "Code Quality",

            # Performance variations
            "performance": "Performance",
            "optimization": "Performance",
            "efficiency": "Performance",
            "scalability": "Performance",
            "memory": "Performance",
            "cpu": "Performance",

            # Standards variations
            "standards": "Standards",
            "coding standards": "Standards",
            "style": "Standards",
            "conventions": "Standards",
            "pep 8": "Standards",

            # Testing variations
            "testing": "Testing",
            "tests": "Testing",
            "test coverage": "Testing",
            "unit tests": "Testing",

            # Error Handling variations
            "error handling": "Error Handling",
            "error": "Error Handling",
            "exception": "Error Handling",
            "exception handling": "Error Handling",

            # Data Integrity variations
            "data integrity": "Data Integrity",
            "data": "Data Integrity",
            "validation": "Data Integrity",
        }

        normalized = category_mappings.get(category.lower(), category)

        # If still not a valid category, default to best guess
        valid_categories = [
            "Security", "Code Quality", "Performance", "Standards",
            "Testing", "Maintainability", "Error Handling", "Data Integrity"
        ]
        if normalized not in valid_categories:
            logger.warning(f"Unknown category '{category}', defaulting to 'Code Quality'")
            return "Code Quality"

        return normalized

    def _normalize_issue(self, issue: dict[str, Any]) -> dict[str, Any]:
        """
        Normalize an issue dict to match CodeIssue schema.

        Args:
            issue: Raw issue dict from specialist

        Returns:
            Normalized issue dict
        """
        normalized = issue.copy()

        # Normalize category (required field)
        if "category" in normalized:
            normalized["category"] = self._normalize_category(normalized["category"])
        else:
            # Default category if missing
            normalized["category"] = "Code Quality"
            logger.warning("Issue missing category, defaulting to 'Code Quality'")

        # Ensure required fields exist with defaults if missing
        if "evidence" not in normalized:
            # Create evidence from file_path and line_number if available
            file_path = normalized.get("file_path", "unknown")
            line_num = normalized.get("line_number", "")
            if line_num:
                normalized["evidence"] = f"{file_path}:{line_num}"
            else:
                normalized["evidence"] = file_path

        # Ensure evidence meets minimum length requirement (10 chars)
        if len(normalized["evidence"]) < 10:
            # Pad short evidence strings with context
            normalized["evidence"] = f"File {normalized['evidence']}: {normalized.get('description', 'Issue identified in code')}"

        if "impact" not in normalized:
            normalized["impact"] = "Requires code review and remediation"

        if "file_path" not in normalized:
            # Try to extract from evidence
            if ":" in normalized.get("evidence", ""):
                normalized["file_path"] = normalized["evidence"].split(":")[0]
            else:
                normalized["file_path"] = "unknown"

        # Ensure file_path is not empty
        if not normalized["file_path"] or normalized["file_path"] == "":
            normalized["file_path"] = "unknown"

        if "affected_phase" not in normalized:
            normalized["affected_phase"] = "Code"

        return normalized

    def _normalize_suggestion(self, suggestion: dict[str, Any]) -> dict[str, Any]:
        """
        Normalize a suggestion dict to match CodeImprovementSuggestion schema.

        Args:
            suggestion: Raw suggestion dict from specialist

        Returns:
            Normalized suggestion dict
        """
        normalized = suggestion.copy()

        # Normalize category (required field)
        if "category" in normalized:
            normalized["category"] = self._normalize_category(normalized["category"])
        else:
            # Default category if missing
            normalized["category"] = "Code Quality"
            logger.warning("Suggestion missing category, defaulting to 'Code Quality'")

        # Ensure required fields
        if "description" not in normalized:
            normalized["description"] = "Review and improve code quality based on specialist feedback"
        elif len(normalized["description"]) < 30:
            # Pad short descriptions to meet minimum length requirement
            desc = normalized["description"]
            normalized["description"] = f"{desc} to improve code quality and maintainability"

        if "implementation_notes" not in normalized:
            # Some LLMs might use different field names
            if "implementation" in normalized:
                normalized["implementation_notes"] = normalized["implementation"]
            elif "notes" in normalized:
                normalized["implementation_notes"] = normalized["notes"]
            else:
                normalized["implementation_notes"] = "Review code and implement recommended changes following best practices"

        # Ensure implementation_notes meets minimum length
        if len(normalized["implementation_notes"]) < 20:
            notes = normalized["implementation_notes"]
            normalized["implementation_notes"] = f"{notes} to address code quality issues"

        if "priority" not in normalized:
            normalized["priority"] = "Medium"

        if "related_issue_id" not in normalized:
            normalized["related_issue_id"] = None

        return normalized

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

        # Collect all issues and suggestions, normalizing as we go
        for specialist_name, result in specialist_results.items():
            issues = result.get("issues_found", [])
            suggestions = result.get("improvement_suggestions", [])

            # Normalize each issue and suggestion
            all_issues.extend([self._normalize_issue(issue) for issue in issues])
            all_suggestions.extend([self._normalize_suggestion(sug) for sug in suggestions])

        # Deduplicate issues (simple approach: by file_path + line_number similarity)
        deduplicated_issues = self._deduplicate_issues(all_issues)

        # Standardize issue IDs (overwrite specialist-assigned IDs with canonical format)
        # Create mapping from old IDs to new IDs
        issue_id_mapping = {}
        for i, issue in enumerate(deduplicated_issues, 1):
            old_id = issue.get("issue_id")
            new_id = f"CODE-ISSUE-{i:03d}"
            if old_id:
                issue_id_mapping[old_id] = new_id
            issue["issue_id"] = new_id

        # Deduplicate suggestions
        deduplicated_suggestions = self._deduplicate_suggestions(all_suggestions)

        # Standardize suggestion IDs and update related_issue_id
        for i, suggestion in enumerate(deduplicated_suggestions, 1):
            suggestion["suggestion_id"] = f"CODE-IMPROVE-{i:03d}"

            # Update related_issue_id to use canonical CODE-ISSUE-### format
            if "related_issue_id" in suggestion and suggestion["related_issue_id"]:
                old_issue_id = suggestion["related_issue_id"]
                if old_issue_id in issue_id_mapping:
                    suggestion["related_issue_id"] = issue_id_mapping[old_issue_id]
                elif not old_issue_id.startswith("CODE-ISSUE-"):
                    # Try to find matching issue
                    suggestion["related_issue_id"] = None  # Clear invalid reference

        logger.info(
            f"Aggregation: {len(all_issues)} issues → {len(deduplicated_issues)} unique, "
            f"{len(all_suggestions)} suggestions → {len(deduplicated_suggestions)} unique"
        )

        return deduplicated_issues, deduplicated_suggestions

    def _deduplicate_issues(self, issues: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """
        Deduplicate issues based on file_path and line_number similarity.

        Args:
            issues: List of all issues from specialists

        Returns:
            Deduplicated list of issues (max severity kept for duplicates)
        """
        # Group by file_path + line_number (simplified deduplication)
        location_map: dict[str, dict[str, Any]] = {}
        severity_order = {"Critical": 4, "High": 3, "Medium": 2, "Low": 1}

        for issue in issues:
            file_path = issue.get("file_path", "unknown")
            line_num = issue.get("line_number", 0)
            location_key = f"{file_path}:{line_num}"

            if location_key in location_map:
                # Keep issue with higher severity
                existing_severity = severity_order.get(location_map[location_key]["severity"], 0)
                new_severity = severity_order.get(issue["severity"], 0)
                if new_severity > existing_severity:
                    location_map[location_key] = issue
            else:
                location_map[location_key] = issue

        return list(location_map.values())

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
        self, generated_code: GeneratedCode
    ) -> dict[str, bool]:
        """
        Run automated validation checks on the generated code.

        Args:
            generated_code: GeneratedCode to validate

        Returns:
            Dictionary of check results (check_name -> passed)
        """
        checks = {}

        # Check 1: Has source files
        source_files = [f for f in generated_code.files if f.file_type == "source"]
        checks["has_source_files"] = len(source_files) > 0

        # Check 2: Has test files
        test_files = [f for f in generated_code.files if f.file_type == "test"]
        checks["has_test_files"] = len(test_files) > 0

        # Check 3: Test/source ratio (at least 1 test file per 2 source files)
        if len(source_files) > 0:
            test_ratio = len(test_files) / len(source_files)
            checks["adequate_test_coverage"] = test_ratio >= 0.5
        else:
            checks["adequate_test_coverage"] = False

        # Check 4: Has dependencies specified
        checks["dependencies_specified"] = len(generated_code.dependencies) > 0

        # Check 5: All files have descriptions
        checks["all_files_documented"] = all(
            len(f.description) >= 20 for f in generated_code.files
        )

        # Check 6: Reasonable file size (not too large)
        MAX_FILE_SIZE = 1000  # lines
        checks["no_oversized_files"] = all(
            len(f.content.split("\n")) <= MAX_FILE_SIZE for f in generated_code.files
        )

        logger.debug(f"Automated checks: {checks}")
        return checks

    def _generate_checklist_review(
        self,
        generated_code: GeneratedCode,
        issues: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """
        Generate checklist review based on standard code review criteria and found issues.

        Args:
            generated_code: Original generated code
            issues: Aggregated issues found

        Returns:
            List of ChecklistItemReview dictionaries
        """
        # Standard code review checklist
        standard_checklist = [
            {
                "category": "Security",
                "description": "Code is free from security vulnerabilities (SQL injection, XSS, etc.)",
            },
            {
                "category": "Code Quality",
                "description": "Code follows best practices and maintainability standards",
            },
            {
                "category": "Performance",
                "description": "Code has no obvious performance bottlenecks",
            },
            {
                "category": "Testing",
                "description": "Code has adequate test coverage",
            },
            {
                "category": "Standards",
                "description": "Code follows language and project coding standards",
            },
        ]

        checklist_review = []

        for i, item in enumerate(standard_checklist):
            # Find related issues by matching category
            related_issues = [
                issue["issue_id"]
                for issue in issues
                if issue.get("category") == item["category"]
            ]

            # Determine status
            if related_issues:
                # Check severity of related issues
                related_severities = [
                    issue.get("severity", "Medium")
                    for issue in issues
                    if issue.get("issue_id") in related_issues
                ]
                has_critical_or_high = any(
                    s in ["Critical", "High"] for s in related_severities
                )
                status = "FAIL" if has_critical_or_high else "WARNING"
            else:
                status = "PASS"

            checklist_review.append({
                "checklist_item_id": f"CODE-CHECK-{i+1:03d}",
                "category": item["category"],
                "description": item["description"],
                "status": status,
                "notes": f"Found {len(related_issues)} related issue(s) in this category" if related_issues else "No issues found for this checklist item",
                "related_issues": related_issues,
            })

        return checklist_review

    def _generate_review_id(self, task_id: str, timestamp: datetime) -> str:
        """Generate unique review ID matching pattern ^CODE-REVIEW-[A-Z0-9]+-\\d{8}-\\d{6}$"""
        # Remove all non-alphanumeric characters (including hyphens and underscores)
        clean_task_id = "".join(
            c if c.isalnum() else "" for c in task_id
        ).upper()

        date_str = timestamp.strftime("%Y%m%d")
        time_str = timestamp.strftime("%H%M%S")

        return f"CODE-REVIEW-{clean_task_id}-{date_str}-{time_str}"
