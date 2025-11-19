"""
Pydantic models for Postmortem Agent (FR-7).

The Postmortem Agent is a meta-agent that analyzes performance data after task
completion to calculate metrics, identify improvement opportunities, and generate
Process Improvement Proposals (PIPs) for Human-in-the-Loop approval.

Models:
    - PostmortemInput: Input to Postmortem Agent (plan + logs)
    - EstimationAccuracy: Planned vs. actual cost comparison
    - QualityMetrics: Defect density and phase distribution
    - RootCauseItem: Individual root cause finding
    - PostmortemReport: Complete performance analysis (output 1)
    - ProposedChange: Individual process change recommendation
    - ProcessImprovementProposal: PIP for HITL approval (output 2)

Postmortem Agent Flow:
    1. Receives PostmortemInput (Project Plan + Effort Log + Defect Log)
    2. Calculates estimation accuracy (planned vs. actual cost vectors)
    3. Analyzes defect metrics (density, injection/removal by phase, yield)
    4. Performs root cause analysis (top defect types by effort to fix)
    5. Returns PostmortemReport with all metrics
    6. Generates ProcessImprovementProposal with specific changes
    7. Submits PIP for Human-in-the-Loop approval

Author: ASP Development Team
Date: November 19, 2025
"""

from datetime import datetime
from typing import Dict, List, Literal, Optional

from pydantic import BaseModel, Field, field_validator, model_validator

from asp.models.planning import ProjectPlan


# =============================================================================
# Input Models
# =============================================================================


class EffortLogEntry(BaseModel):
    """
    Single entry from the automated telemetry/effort log.

    Represents one measurement from the observability layer (Table 3 in PSPdoc).
    """

    timestamp: datetime = Field(
        ...,
        description="Timestamp of the agent execution",
    )

    task_id: str = Field(
        ...,
        description="Unique task identifier",
    )

    agent_role: str = Field(
        ...,
        description="Agent that executed (Planning, Design, Code, etc.)",
    )

    metric_type: str = Field(
        ...,
        description="Metric being recorded (Latency, Tokens_In, Tokens_Out, API_Cost)",
    )

    metric_value: float = Field(
        ...,
        description="Numeric value of the metric",
    )

    unit: str = Field(
        ...,
        description="Unit of measure (ms, tokens, USD)",
    )


class DefectLogEntry(BaseModel):
    """
    Single entry from the defect log.

    Represents one defect found during development (Table 4 in PSPdoc).
    Uses AI Defect Taxonomy for classification.
    """

    defect_id: str = Field(
        ...,
        description="Unique defect identifier",
    )

    task_id: str = Field(
        ...,
        description="Unique task identifier",
    )

    defect_type: Literal[
        "Planning_Failure",
        "Prompt_Misinterpretation",
        "Tool_Use_Error",
        "Hallucination",
        "Security_Vulnerability",
        "Conventional_Code_Bug",
        "Task_Execution_Error",
        "Alignment_Deviation",
    ] = Field(
        ...,
        description="Classification from AI Defect Taxonomy (FR-11)",
    )

    phase_injected: str = Field(
        ...,
        description="Agent role that created the defect (e.g., Design, Code)",
    )

    phase_removed: str = Field(
        ...,
        description="Agent role that found the defect (e.g., Design Review, Test)",
    )

    effort_to_fix_vector: Dict[str, float] = Field(
        ...,
        description="Cost of correction loop (latency_ms, tokens, api_cost)",
    )

    description: str = Field(
        ...,
        description="Detailed description of the defect",
    )

    severity: Optional[Literal["Critical", "High", "Medium", "Low"]] = Field(
        default="Medium",
        description="Severity level of the defect",
    )


class PostmortemInput(BaseModel):
    """
    Input data for Postmortem Agent.

    Contains the project plan and all performance/quality logs
    needed for analysis.

    Attributes:
        task_id: Unique task identifier
        project_plan: Original plan from Planning Agent
        effort_log: All effort/cost measurements from telemetry
        defect_log: All defects found during development
        actual_semantic_complexity: Final actual complexity (calculated post-execution)
    """

    task_id: str = Field(
        ...,
        min_length=3,
        description="Unique task identifier",
    )

    project_plan: ProjectPlan = Field(
        ...,
        description="Original project plan from Planning Agent",
    )

    effort_log: List[EffortLogEntry] = Field(
        ...,
        description="All effort/cost measurements from telemetry (Table 3)",
    )

    defect_log: List[DefectLogEntry] = Field(
        default_factory=list,
        description="All defects found during development (Table 4)",
    )

    actual_semantic_complexity: float = Field(
        ...,
        gt=0,
        description="Actual semantic complexity calculated post-execution",
    )

    @field_validator("task_id")
    @classmethod
    def validate_task_id(cls, v: str) -> str:
        """Validate task_id format."""
        if not v or len(v.strip()) < 3:
            raise ValueError("task_id must be at least 3 characters")
        return v.strip()

    class Config:
        json_schema_extra = {
            "example": {
                "task_id": "POSTMORTEM-001",
                "project_plan": {
                    "task_id": "POSTMORTEM-001",
                    "total_est_complexity": 18.5,
                    "total_est_latency_ms": 35000,
                    "total_est_tokens": 88000,
                    "total_est_api_cost": 0.14,
                },
                "effort_log": [
                    {
                        "timestamp": "2025-11-19T10:00:00Z",
                        "task_id": "POSTMORTEM-001",
                        "agent_role": "Planning",
                        "metric_type": "Latency",
                        "metric_value": 2500,
                        "unit": "ms",
                    }
                ],
                "defect_log": [
                    {
                        "defect_id": "D-001",
                        "task_id": "POSTMORTEM-001",
                        "defect_type": "Security_Vulnerability",
                        "phase_injected": "Code",
                        "phase_removed": "Code Review",
                        "effort_to_fix_vector": {
                            "latency_ms": 5000,
                            "tokens": 12000,
                            "api_cost": 0.02,
                        },
                        "description": "SQL injection vulnerability in user input",
                        "severity": "Critical",
                    }
                ],
                "actual_semantic_complexity": 20.3,
            }
        }


# =============================================================================
# Output Models - Part 1: Postmortem Report
# =============================================================================


class MetricComparison(BaseModel):
    """
    Comparison of planned vs. actual for a single metric.
    """

    planned: float = Field(
        ...,
        description="Planned value from project plan",
    )

    actual: float = Field(
        ...,
        description="Actual value from effort log",
    )

    variance_percent: float = Field(
        ...,
        description="Percentage variance ((actual - planned) / planned * 100)",
    )

    @model_validator(mode="after")
    def calculate_variance(self):
        """Calculate variance percentage if not provided."""
        if self.planned > 0:
            calculated_variance = ((self.actual - self.planned) / self.planned) * 100
            # Round to 2 decimal places
            self.variance_percent = round(calculated_variance, 2)
        return self


class EstimationAccuracy(BaseModel):
    """
    Estimation accuracy metrics (planned vs. actual cost vector).

    Measures how well the Planning Agent predicted resource consumption.
    """

    latency_ms: MetricComparison = Field(
        ...,
        description="Latency comparison (milliseconds)",
    )

    tokens: MetricComparison = Field(
        ...,
        description="Token usage comparison",
    )

    api_cost: MetricComparison = Field(
        ...,
        description="API cost comparison (USD)",
    )

    semantic_complexity: MetricComparison = Field(
        ...,
        description="Semantic complexity comparison",
    )


class QualityMetrics(BaseModel):
    """
    Quality metrics from defect analysis.

    Includes defect density and phase distribution.
    """

    defect_density: float = Field(
        ...,
        description="Total defects / Actual semantic complexity",
    )

    total_defects: int = Field(
        ...,
        ge=0,
        description="Total number of defects found",
    )

    defect_injection_by_phase: Dict[str, int] = Field(
        ...,
        description="Count of defects grouped by phase_injected",
    )

    defect_removal_by_phase: Dict[str, int] = Field(
        ...,
        description="Count of defects grouped by phase_removed",
    )

    phase_yield: Dict[str, float] = Field(
        default_factory=dict,
        description="Percentage of defects caught in each phase (not escaped to later phases)",
    )


class RootCauseItem(BaseModel):
    """
    Individual root cause finding.

    Identifies a defect type and its impact.
    """

    defect_type: str = Field(
        ...,
        description="Defect type from AI Defect Taxonomy",
    )

    occurrence_count: int = Field(
        ...,
        ge=0,
        description="Number of times this defect type occurred",
    )

    total_effort_to_fix: float = Field(
        ...,
        description="Total API cost to fix all occurrences (USD)",
    )

    average_effort_to_fix: float = Field(
        ...,
        description="Average API cost per occurrence (USD)",
    )

    recommendation: str = Field(
        ...,
        description="Recommended action to prevent this defect type",
    )


class PostmortemReport(BaseModel):
    """
    Complete postmortem analysis report.

    Output from Postmortem Agent's first phase (performance analysis).
    Contains all metrics, comparisons, and root cause analysis.
    """

    task_id: str = Field(
        ...,
        description="Unique task identifier",
    )

    analysis_timestamp: datetime = Field(
        default_factory=datetime.now,
        description="When this analysis was performed",
    )

    estimation_accuracy: EstimationAccuracy = Field(
        ...,
        description="Planned vs. actual cost vector comparison",
    )

    quality_metrics: QualityMetrics = Field(
        ...,
        description="Defect density and phase distribution",
    )

    root_cause_analysis: List[RootCauseItem] = Field(
        ...,
        description="Top defect types by effort to fix (sorted by total_effort_to_fix, descending)",
    )

    summary: str = Field(
        ...,
        description="Executive summary of findings (2-3 sentences)",
    )

    recommendations: List[str] = Field(
        default_factory=list,
        description="High-level recommendations for improvement",
    )

    @field_validator("root_cause_analysis")
    @classmethod
    def sort_root_causes(cls, v: List[RootCauseItem]) -> List[RootCauseItem]:
        """Ensure root causes are sorted by total effort to fix (descending)."""
        return sorted(v, key=lambda x: x.total_effort_to_fix, reverse=True)

    class Config:
        json_schema_extra = {
            "example": {
                "task_id": "POSTMORTEM-001",
                "analysis_timestamp": "2025-11-19T14:30:00Z",
                "estimation_accuracy": {
                    "latency_ms": {
                        "planned": 35000,
                        "actual": 38500,
                        "variance_percent": 10.0,
                    },
                    "tokens": {"planned": 88000, "actual": 102000, "variance_percent": 15.9},
                    "api_cost": {"planned": 0.14, "actual": 0.17, "variance_percent": 21.4},
                    "semantic_complexity": {
                        "planned": 18.5,
                        "actual": 20.3,
                        "variance_percent": 9.7,
                    },
                },
                "quality_metrics": {
                    "defect_density": 0.15,
                    "total_defects": 3,
                    "defect_injection_by_phase": {"Design": 1, "Code": 2},
                    "defect_removal_by_phase": {
                        "Design Review": 1,
                        "Code Review": 1,
                        "Test": 1,
                    },
                    "phase_yield": {
                        "Design Review": 50.0,
                        "Code Review": 33.3,
                        "Test": 16.7,
                    },
                },
                "root_cause_analysis": [
                    {
                        "defect_type": "Security_Vulnerability",
                        "occurrence_count": 1,
                        "total_effort_to_fix": 0.02,
                        "average_effort_to_fix": 0.02,
                        "recommendation": "Add SQL injection checks to Code Review checklist",
                    }
                ],
                "summary": "Task completed with 10% latency overrun and 21% cost overrun. 3 defects found, all caught before production. Security vulnerability indicates need for enhanced code review checklist.",
                "recommendations": [
                    "Update Code Review checklist with SQL injection examples",
                    "Improve Planning Agent estimation for database operations",
                ],
            }
        }


# =============================================================================
# Output Models - Part 2: Process Improvement Proposal (PIP)
# =============================================================================


class ProposedChange(BaseModel):
    """
    Individual proposed change to a process artifact.

    Represents a specific modification to a prompt, checklist, or standard.
    """

    target_artifact: str = Field(
        ...,
        description="Which artifact to change (e.g., 'code_review_checklist', 'coding_agent_prompt')",
    )

    change_type: Literal["add", "modify", "remove"] = Field(
        ...,
        description="Type of change to make",
    )

    current_content: Optional[str] = Field(
        None,
        description="Current content (for modify/remove)",
    )

    proposed_content: str = Field(
        ...,
        description="Proposed new/modified content",
    )

    rationale: str = Field(
        ...,
        description="Why this change will prevent the identified defect type",
    )


class ProcessImprovementProposal(BaseModel):
    """
    Process Improvement Proposal (PIP) for HITL approval.

    Output from Postmortem Agent's second phase (improvement proposal).
    Contains specific, actionable changes to process artifacts (prompts, checklists).
    """

    proposal_id: str = Field(
        ...,
        description="Unique PIP identifier (e.g., PIP-001)",
    )

    task_id: str = Field(
        ...,
        description="Task that triggered this PIP",
    )

    created_at: datetime = Field(
        default_factory=datetime.now,
        description="When this PIP was created",
    )

    analysis: str = Field(
        ...,
        description="Analysis of the problem that triggered this PIP (2-4 sentences)",
    )

    proposed_changes: List[ProposedChange] = Field(
        ...,
        min_length=1,
        description="List of specific changes to process artifacts",
    )

    expected_impact: str = Field(
        ...,
        description="Expected impact of implementing these changes",
    )

    hitl_status: Literal["pending", "approved", "rejected", "needs_revision"] = Field(
        default="pending",
        description="Human-in-the-Loop approval status",
    )

    hitl_reviewer: Optional[str] = Field(
        None,
        description="Name/ID of human reviewer",
    )

    hitl_reviewed_at: Optional[datetime] = Field(
        None,
        description="When HITL review was completed",
    )

    hitl_feedback: Optional[str] = Field(
        None,
        description="Feedback from human reviewer",
    )

    @field_validator("proposal_id")
    @classmethod
    def validate_proposal_id(cls, v: str) -> str:
        """Validate PIP ID format."""
        if not v.startswith("PIP-"):
            raise ValueError("proposal_id must start with 'PIP-'")
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "proposal_id": "PIP-001",
                "task_id": "POSTMORTEM-001",
                "created_at": "2025-11-19T15:00:00Z",
                "analysis": "The Code Agent injected a Security_Vulnerability defect (SQL Injection), which was caught by Code Review but consumed significant correction effort ($0.02). This suggests the Code Review checklist needs more specific SQL injection examples to catch this earlier in the review process.",
                "proposed_changes": [
                    {
                        "target_artifact": "code_review_checklist",
                        "change_type": "add",
                        "current_content": None,
                        "proposed_content": "- [ ] Verify all database queries use parameterized statements (e.g., cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,)))",
                        "rationale": "Specific parameterized query examples will help Code Review Agent identify SQL injection vulnerabilities more effectively",
                    }
                ],
                "expected_impact": "Reduce Security_Vulnerability defects in Code phase by 50% through earlier detection in Code Review",
                "hitl_status": "pending",
                "hitl_reviewer": None,
                "hitl_reviewed_at": None,
                "hitl_feedback": None,
            }
        }
