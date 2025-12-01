"""
Postmortem Agent for ASP Platform

The Postmortem Agent is a meta-agent responsible for:
1. Performance Analysis (FR-007): Analyzing planned vs. actual metrics
2. Root Cause Analysis: Identifying top defect types by effort to fix
3. PIP Generation: Creating Process Improvement Proposals for HITL approval
4. Self-Improvement: Proposing changes to prompts/checklists to prevent future defects

This is the seventh and final agent in the 7-agent ASP architecture, following the Test Agent.
It implements the PSP Postmortem phase, enabling continuous improvement.

Author: ASP Development Team
Date: November 19, 2025
"""

import json
import logging
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from asp.agents.base_agent import AgentExecutionError, BaseAgent
from asp.models.postmortem import (
    DefectLogEntry,
    EffortLogEntry,
    EstimationAccuracy,
    MetricComparison,
    PostmortemInput,
    PostmortemReport,
    ProcessImprovementProposal,
    ProposedChange,
    QualityMetrics,
    RootCauseItem,
)
from asp.telemetry import track_agent_cost
from asp.utils.artifact_io import write_artifact_json, write_artifact_markdown
from asp.utils.git_utils import git_commit_artifact, is_git_repository
from asp.utils.markdown_renderer import render_postmortem_report_markdown


logger = logging.getLogger(__name__)


class PostmortemAgent(BaseAgent):
    """
    Postmortem Agent implementation.

    A meta-agent that analyzes performance data after task completion to:
    - Calculate estimation accuracy (planned vs. actual cost vectors)
    - Analyze quality metrics (defect density, phase distribution)
    - Perform root cause analysis (top defect types)
    - Generate Process Improvement Proposals (PIPs) for HITL approval

    The Postmortem Agent:
    - Takes PostmortemInput with project plan and performance logs
    - Calculates derived measures (estimation accuracy, defect metrics)
    - Identifies improvement opportunities through root cause analysis
    - Returns PostmortemReport with complete analysis
    - Generates ProcessImprovementProposal with specific changes
    - Submits PIP for Human-in-the-Loop approval

    Example:
        >>> from asp.agents.postmortem_agent import PostmortemAgent
        >>> from asp.models.postmortem import PostmortemInput
        >>>
        >>> agent = PostmortemAgent()
        >>> input_data = PostmortemInput(
        ...     task_id="POSTMORTEM-001",
        ...     project_plan=plan,
        ...     effort_log=effort_entries,
        ...     defect_log=defect_entries,
        ...     actual_semantic_complexity=20.3,
        ... )
        >>> report = agent.execute(input_data)
        >>> print(f"Estimation variance: {report.estimation_accuracy.api_cost.variance_percent}%")
        >>> print(f"Defect density: {report.quality_metrics.defect_density}")
        >>>
        >>> # Generate PIP
        >>> pip = agent.generate_pip(report, input_data)
        >>> print(f"PIP ID: {pip.proposal_id}, Changes: {len(pip.proposed_changes)}")
    """

    def __init__(
        self,
        db_path: Optional[Path] = None,
        llm_client: Optional[Any] = None,
    ):
        """
        Initialize Postmortem Agent.

        Args:
            db_path: Optional path to SQLite database for telemetry
            llm_client: Optional LLM client (for dependency injection in tests)
        """
        super().__init__(db_path=db_path, llm_client=llm_client)
        self.agent_version = "1.0.0"
        logger.info("PostmortemAgent initialized")

    @track_agent_cost(
        agent_role="Postmortem",
        task_id_param="input_data.task_id",
        llm_model="claude-sonnet-4-20250514",
        llm_provider="anthropic",
        agent_version="1.0.0",
    )
    def execute(self, input_data: PostmortemInput) -> PostmortemReport:
        """
        Execute the Postmortem Agent to analyze performance data.

        This method:
        1. Calculates estimation accuracy (planned vs. actual)
        2. Analyzes quality metrics (defect density, phase distribution)
        3. Performs root cause analysis (top defect types)
        4. Generates executive summary
        5. Returns complete PostmortemReport

        Args:
            input_data: PostmortemInput with project plan and performance logs

        Returns:
            PostmortemReport with complete analysis

        Raises:
            AgentExecutionError: If analysis fails
        """
        logger.info(
            f"Executing PostmortemAgent for task_id={input_data.task_id}, "
            f"effort_entries={len(input_data.effort_log)}, "
            f"defects={len(input_data.defect_log)}"
        )

        try:
            # Calculate estimation accuracy
            estimation_accuracy = self._calculate_estimation_accuracy(input_data)

            # Calculate quality metrics
            quality_metrics = self._calculate_quality_metrics(input_data)

            # Perform root cause analysis
            root_cause_analysis = self._perform_root_cause_analysis(input_data)

            # Generate summary and recommendations
            summary = self._generate_summary(
                input_data, estimation_accuracy, quality_metrics, root_cause_analysis
            )
            recommendations = self._generate_recommendations(root_cause_analysis)

            # Create report
            report = PostmortemReport(
                task_id=input_data.task_id,
                analysis_timestamp=datetime.now(),
                estimation_accuracy=estimation_accuracy,
                quality_metrics=quality_metrics,
                root_cause_analysis=root_cause_analysis,
                summary=summary,
                recommendations=recommendations,
            )

            logger.info(
                f"Postmortem analysis complete: "
                f"latency_variance={estimation_accuracy.latency_ms.variance_percent:.1f}%, "
                f"cost_variance={estimation_accuracy.api_cost.variance_percent:.1f}%, "
                f"defect_density={quality_metrics.defect_density:.2f}, "
                f"root_causes={len(root_cause_analysis)}"
            )

            # Write artifacts to filesystem (if enabled)
            try:
                artifact_files = []

                # Write postmortem report as JSON
                report_path = write_artifact_json(
                    task_id=report.task_id,
                    artifact_type="postmortem_report",
                    data=report,
                )
                logger.debug(f"Wrote postmortem report JSON: {report_path}")
                artifact_files.append(str(report_path))

                # Write postmortem report as Markdown (human-readable)
                markdown_content = render_postmortem_report_markdown(report)
                md_path = write_artifact_markdown(
                    task_id=report.task_id,
                    artifact_type="postmortem_report",
                    markdown_content=markdown_content,
                )
                logger.debug(f"Wrote postmortem report Markdown: {md_path}")
                artifact_files.append(str(md_path))

                # Git commit artifacts (if in git repository)
                if is_git_repository():
                    git_commit_artifact(
                        task_id=report.task_id,
                        artifact_type="postmortem_report",
                        file_paths=artifact_files,
                    )

            except Exception as e:
                logger.warning(f"Failed to write artifacts: {e}")

            return report

        except Exception as e:
            logger.error(f"Postmortem analysis failed: {e}", exc_info=True)
            raise AgentExecutionError(f"PostmortemAgent failed: {e}") from e

    def _calculate_estimation_accuracy(
        self, input_data: PostmortemInput
    ) -> EstimationAccuracy:
        """
        Calculate estimation accuracy (planned vs. actual).

        Args:
            input_data: PostmortemInput with plan and effort log

        Returns:
            EstimationAccuracy with variance calculations
        """
        # Aggregate actual metrics from effort log
        actual_latency_ms = 0.0
        actual_tokens = 0.0
        actual_api_cost = 0.0

        for entry in input_data.effort_log:
            if entry.metric_type == "Latency" and entry.unit == "ms":
                actual_latency_ms += entry.metric_value
            elif (
                entry.metric_type in ["Tokens_In", "Tokens_Out"]
                and entry.unit == "tokens"
            ):
                actual_tokens += entry.metric_value
            elif entry.metric_type == "API_Cost" and entry.unit == "USD":
                actual_api_cost += entry.metric_value

        # Get planned values from project plan
        plan = input_data.project_plan

        # Check if PROBE-AI predictions are available
        if plan.probe_ai_prediction:
            planned_latency_ms = plan.probe_ai_prediction.total_est_latency_ms
            planned_tokens = plan.probe_ai_prediction.total_est_tokens
            planned_api_cost = plan.probe_ai_prediction.total_est_api_cost
        else:
            # If no PROBE-AI predictions, use 0 as baseline (can't compare)
            # This happens in Phase 1 before PROBE-AI is enabled
            planned_latency_ms = 0.0
            planned_tokens = 0.0
            planned_api_cost = 0.0

        planned_complexity = plan.total_est_complexity

        # Create metric comparisons
        return EstimationAccuracy(
            latency_ms=MetricComparison(
                planned=planned_latency_ms,
                actual=actual_latency_ms,
                variance_percent=0.0,  # Will be calculated by model
            ),
            tokens=MetricComparison(
                planned=planned_tokens,
                actual=actual_tokens,
                variance_percent=0.0,
            ),
            api_cost=MetricComparison(
                planned=planned_api_cost,
                actual=actual_api_cost,
                variance_percent=0.0,
            ),
            semantic_complexity=MetricComparison(
                planned=planned_complexity,
                actual=input_data.actual_semantic_complexity,
                variance_percent=0.0,
            ),
        )

    def _calculate_quality_metrics(self, input_data: PostmortemInput) -> QualityMetrics:
        """
        Calculate quality metrics from defect log.

        Args:
            input_data: PostmortemInput with defect log

        Returns:
            QualityMetrics with defect analysis
        """
        defects = input_data.defect_log
        total_defects = len(defects)

        # Calculate defect density
        defect_density = (
            total_defects / input_data.actual_semantic_complexity
            if input_data.actual_semantic_complexity > 0
            else 0.0
        )

        # Group defects by injection phase
        injection_counts: Dict[str, int] = defaultdict(int)
        for defect in defects:
            injection_counts[defect.phase_injected] += 1

        # Group defects by removal phase
        removal_counts: Dict[str, int] = defaultdict(int)
        for defect in defects:
            removal_counts[defect.phase_removed] += 1

        # Calculate phase yield (% of defects caught in each phase)
        phase_yield: Dict[str, float] = {}
        if total_defects > 0:
            for phase, count in removal_counts.items():
                phase_yield[phase] = round((count / total_defects) * 100, 1)

        return QualityMetrics(
            defect_density=round(defect_density, 3),
            total_defects=total_defects,
            defect_injection_by_phase=dict(injection_counts),
            defect_removal_by_phase=dict(removal_counts),
            phase_yield=phase_yield,
        )

    def _perform_root_cause_analysis(
        self, input_data: PostmortemInput
    ) -> List[RootCauseItem]:
        """
        Perform root cause analysis on defects.

        Identifies top defect types by total effort to fix.

        Args:
            input_data: PostmortemInput with defect log

        Returns:
            List of RootCauseItem sorted by total_effort_to_fix (descending)
        """
        # Group defects by type
        defect_groups: Dict[str, List[DefectLogEntry]] = defaultdict(list)
        for defect in input_data.defect_log:
            defect_groups[defect.defect_type].append(defect)

        # Calculate metrics for each defect type
        root_causes = []
        for defect_type, defects in defect_groups.items():
            occurrence_count = len(defects)

            # Sum effort to fix (use api_cost as primary metric)
            total_effort = sum(
                d.effort_to_fix_vector.get("api_cost", 0.0) for d in defects
            )
            average_effort = (
                total_effort / occurrence_count if occurrence_count > 0 else 0.0
            )

            # Generate recommendation based on defect type
            recommendation = self._generate_recommendation_for_defect_type(
                defect_type, defects
            )

            root_causes.append(
                RootCauseItem(
                    defect_type=defect_type,
                    occurrence_count=occurrence_count,
                    total_effort_to_fix=round(total_effort, 4),
                    average_effort_to_fix=round(average_effort, 4),
                    recommendation=recommendation,
                )
            )

        # Sort by total effort (descending) and return top 5
        root_causes.sort(key=lambda x: x.total_effort_to_fix, reverse=True)
        return root_causes[:5]

    def _generate_recommendation_for_defect_type(
        self, defect_type: str, defects: List[DefectLogEntry]
    ) -> str:
        """
        Generate specific recommendation based on defect type.

        Args:
            defect_type: Type of defect from AI Defect Taxonomy
            defects: List of defects of this type

        Returns:
            Recommendation string
        """
        # Analyze common patterns in defects
        common_phase_injected = max(
            set(d.phase_injected for d in defects),
            key=lambda p: sum(1 for d in defects if d.phase_injected == p),
        )
        common_phase_removed = max(
            set(d.phase_removed for d in defects),
            key=lambda p: sum(1 for d in defects if d.phase_removed == p),
        )

        # Generate targeted recommendation
        recommendations_map = {
            "Planning_Failure": f"Enhance Planning Agent prompt with examples of proper task decomposition. Add validation checks for complexity estimation.",
            "Prompt_Misinterpretation": f"Add explicit constraints and examples to {common_phase_injected} Agent prompt. Consider few-shot examples for common scenarios.",
            "Tool_Use_Error": f"Add detailed tool usage examples to {common_phase_injected} Agent prompt. Include error handling patterns.",
            "Hallucination": f"Add fact-checking validation to {common_phase_injected} Agent. Require citations for technical claims.",
            "Security_Vulnerability": f"Enhance {common_phase_removed} checklist with specific security patterns. Add OWASP Top 10 examples.",
            "Conventional_Code_Bug": f"Add code quality checks to {common_phase_removed} checklist. Include edge case testing examples.",
            "Task_Execution_Error": f"Add retry logic and timeout handling to orchestrator. Improve error messages for debugging.",
            "Alignment_Deviation": f"Clarify business requirements in {common_phase_injected} Agent prompt. Add acceptance criteria validation.",
        }

        return recommendations_map.get(
            defect_type,
            f"Review and enhance {common_phase_injected} Agent prompt and {common_phase_removed} checklist.",
        )

    def _generate_summary(
        self,
        input_data: PostmortemInput,
        estimation_accuracy: EstimationAccuracy,
        quality_metrics: QualityMetrics,
        root_cause_analysis: List[RootCauseItem],
    ) -> str:
        """
        Generate executive summary of findings.

        Args:
            input_data: PostmortemInput
            estimation_accuracy: Calculated estimation accuracy
            quality_metrics: Calculated quality metrics
            root_cause_analysis: Root cause analysis results

        Returns:
            Summary string (2-3 sentences)
        """
        latency_var = estimation_accuracy.latency_ms.variance_percent
        cost_var = estimation_accuracy.api_cost.variance_percent
        defect_count = quality_metrics.total_defects
        defect_density = quality_metrics.defect_density

        # Determine if variances are acceptable (±20% threshold)
        latency_status = (
            "on target"
            if abs(latency_var) <= 20
            else f"{'over' if latency_var > 0 else 'under'}ran by {abs(latency_var):.0f}%"
        )
        cost_status = (
            "on target"
            if abs(cost_var) <= 20
            else f"{'over' if cost_var > 0 else 'under'}ran by {abs(cost_var):.0f}%"
        )

        # Build summary
        summary_parts = [
            f"Task {input_data.task_id} completed with latency {latency_status} and cost {cost_status}."
        ]

        if defect_count > 0:
            top_defect = (
                root_cause_analysis[0].defect_type if root_cause_analysis else "N/A"
            )
            summary_parts.append(
                f"{defect_count} defect{'s' if defect_count > 1 else ''} found "
                f"(density: {defect_density:.2f}), with {top_defect} being the primary issue."
            )
        else:
            summary_parts.append("No defects found - excellent quality.")

        # Add recommendation hint
        if root_cause_analysis:
            summary_parts.append(
                "Process improvements recommended to prevent future defects."
            )

        return " ".join(summary_parts)

    def _generate_recommendations(
        self, root_cause_analysis: List[RootCauseItem]
    ) -> List[str]:
        """
        Generate high-level recommendations.

        Args:
            root_cause_analysis: Root cause analysis results

        Returns:
            List of recommendation strings
        """
        if not root_cause_analysis:
            return [
                "Continue current development process - no significant defects detected."
            ]

        recommendations = []
        for item in root_cause_analysis[:3]:  # Top 3 issues
            recommendations.append(item.recommendation)

        return recommendations

    def generate_pip(
        self,
        postmortem_report: PostmortemReport,
        input_data: PostmortemInput,
        pip_id: Optional[str] = None,
    ) -> ProcessImprovementProposal:
        """
        Generate Process Improvement Proposal (PIP) based on postmortem analysis.

        This method uses LLM to analyze the postmortem report and generate
        specific, actionable changes to process artifacts (prompts, checklists).

        Args:
            postmortem_report: PostmortemReport from execute()
            input_data: Original PostmortemInput
            pip_id: Optional custom PIP ID (auto-generated if not provided)

        Returns:
            ProcessImprovementProposal with specific changes for HITL approval

        Raises:
            AgentExecutionError: If PIP generation fails
        """
        logger.info(f"Generating PIP for task_id={postmortem_report.task_id}")

        try:
            # Auto-generate PIP ID if not provided
            if pip_id is None:
                timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
                pip_id = f"PIP-{timestamp}"

            # Load and format PIP generation prompt
            prompt_template = self.load_prompt("postmortem_agent_v1_pip_generation")

            # Prepare context for LLM
            prompt = self.format_prompt(
                prompt_template,
                postmortem_report_json=postmortem_report.model_dump_json(indent=2),
                defect_log_json=json.dumps(
                    [d.model_dump() for d in input_data.defect_log], indent=2
                ),
                root_cause_analysis="\n".join(
                    f"- {item.defect_type}: {item.occurrence_count} occurrences, "
                    f"${item.total_effort_to_fix:.4f} total fix cost"
                    for item in postmortem_report.root_cause_analysis
                ),
            )

            # Call LLM to generate PIP
            response = self.call_llm(
                prompt=prompt,
                max_tokens=4096,
                temperature=0.1,  # Low temperature for consistent, focused recommendations
            )

            # Parse and validate response
            pip_data = json.loads(response["content"])
            pip_data["proposal_id"] = pip_id  # Override with our generated ID
            pip_data["task_id"] = postmortem_report.task_id

            pip = self.validate_output(pip_data, ProcessImprovementProposal)

            logger.info(
                f"PIP generated: {pip.proposal_id}, "
                f"changes={len(pip.proposed_changes)}, "
                f"status={pip.hitl_status}"
            )

            # Write PIP artifact
            try:
                pip_path = write_artifact_json(
                    task_id=postmortem_report.task_id,
                    artifact_type="pip",
                    data=pip,
                )
                logger.debug(f"Wrote PIP: {pip_path}")

            except Exception as e:
                logger.warning(f"Failed to write PIP artifact: {e}")

            return pip

        except Exception as e:
            logger.error(f"PIP generation failed: {e}", exc_info=True)
            raise AgentExecutionError(f"Failed to generate PIP: {e}") from e
