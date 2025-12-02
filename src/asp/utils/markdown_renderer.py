"""
Markdown rendering utilities for ASP platform.

This module provides functions for converting agent artifacts
(Pydantic models) into human-readable Markdown format.

Implements the markdown rendering from:
docs/artifact_persistence_version_control_decision.md

Author: ASP Development Team
Date: November 17, 2025
"""

import logging

from asp.models.code import GeneratedCode
from asp.models.code_review import CodeReviewReport
from asp.models.design import DesignSpecification
from asp.models.design_review import DesignReviewReport
from asp.models.planning import ProjectPlan
from asp.models.postmortem import PostmortemReport
from asp.models.test import TestReport

logger = logging.getLogger(__name__)


def render_plan_markdown(plan: ProjectPlan) -> str:
    """
    Render ProjectPlan as human-readable Markdown.

    Args:
        plan: ProjectPlan Pydantic model

    Returns:
        Markdown formatted string

    Example:
        >>> markdown = render_plan_markdown(project_plan)
        >>> "# Project Plan:" in markdown
        True
    """
    # Build header with available fields
    md = f"""# Project Plan: {plan.task_id}

**Project ID:** {plan.project_id or "N/A"}
**Task ID:** {plan.task_id}
**Total Complexity:** {plan.total_est_complexity}
**PROBE-AI Enabled:** {plan.probe_ai_enabled}
**Agent Version:** {plan.agent_version}

"""

    # Add PROBE-AI predictions if available
    if plan.probe_ai_prediction:
        md += f"""## PROBE-AI Predictions

**Estimated Effort:** {plan.probe_ai_prediction.total_effort_hours:.1f} hours
**Estimated Cost:** ${plan.probe_ai_prediction.total_cost:.2f}
**Confidence:** {plan.probe_ai_prediction.confidence:.1%}

"""

    md += "## Task Decomposition\n\n"

    # Add semantic units
    for i, unit in enumerate(plan.semantic_units, 1):
        md += f"""### {unit.unit_id}: {unit.description}

- **Estimated Complexity:** {unit.est_complexity}
- **API Interactions:** {unit.api_interactions}
- **Data Transformations:** {unit.data_transformations}
- **Logical Branches:** {unit.logical_branches}
- **Code Entities Modified:** {unit.code_entities_modified}
- **Novelty Multiplier:** {unit.novelty_multiplier}
- **Dependencies:** {", ".join(unit.dependencies) if unit.dependencies else "None"}

"""

    return md


def render_design_markdown(design: DesignSpecification) -> str:
    """
    Render DesignSpecification as human-readable Markdown.

    Args:
        design: DesignSpecification Pydantic model

    Returns:
        Markdown formatted string
    """
    md = f"""# Design Specification: {design.task_id}

**Task ID:** {design.task_id}

## Architecture Overview

{design.architecture_overview}

## Technology Stack

{design.technology_stack}

## Assumptions

{design.assumptions}

"""

    # Add API contracts
    if design.api_contracts:
        md += "## API Contracts\n\n"
        for api in design.api_contracts:
            md += f"""### {api.method} {api.endpoint}

- **Description:** {api.description}
- **Authentication:** {api.authentication_required}
"""
            if api.request_schema:
                md += f"- **Request Schema:**\n```json\n{api.request_schema}\n```\n"
            if api.response_schema:
                md += f"- **Response Schema:**\n```json\n{api.response_schema}\n```\n"
            if api.error_responses:
                # error_responses is a list of dicts with status_code and description
                error_summary = ", ".join(
                    [f"{e.get('status_code', 'N/A')}" for e in api.error_responses]
                )
                md += f"- **Error Responses:** {error_summary}\n"

            md += "\n"

    # Add data schemas
    if design.data_schemas:
        md += "## Data Schemas\n\n"
        for schema in design.data_schemas:
            md += f"""### {schema.table_name}

- **Description:** {schema.description}
"""
            if schema.columns:
                md += "- **Columns:**\n"
                for col in schema.columns:
                    col_name = (
                        col.get("name", "unknown")
                        if isinstance(col, dict)
                        else str(col)
                    )
                    md += f"  - `{col_name}`\n"
            if schema.indexes:
                md += f"- **Indexes:** {', '.join(schema.indexes)}\n"
            if schema.relationships:
                md += f"- **Relationships:** {', '.join(schema.relationships)}\n"

            md += "\n"

    # Add component logic
    if design.component_logic:
        md += "## Component Logic\n\n"
        for component in design.component_logic:
            md += f"""### {component.component_name}

- **Responsibility:** {component.responsibility}
- **Semantic Unit:** {component.semantic_unit_id}
- **Dependencies:** {', '.join(component.dependencies) if component.dependencies else 'None'}
- **Implementation Notes:** {component.implementation_notes}
"""
            if component.interfaces:
                md += "- **Interfaces:**\n"
                for interface in component.interfaces:
                    md += f"  - `{interface.get('method', 'N/A')}`\n"

            md += "\n"

    # Add metadata
    md += f"""---

*Generated by Design Agent on {design.timestamp.strftime('%Y-%m-%d %H:%M:%S')}*
"""

    return md


def render_design_review_markdown(review: DesignReviewReport) -> str:
    """
    Render DesignReviewReport as human-readable Markdown.

    Args:
        review: DesignReviewReport Pydantic model

    Returns:
        Markdown formatted string
    """
    total_issues = (
        review.critical_issue_count
        + review.high_issue_count
        + review.medium_issue_count
        + review.low_issue_count
    )
    timestamp_str = (
        review.timestamp.strftime("%Y-%m-%d %H:%M:%S")
        if hasattr(review, "timestamp") and review.timestamp
        else "N/A"
    )
    md = f"""# Design Review Report: {review.task_id}

**Review ID:** {review.review_id}
**Review Status:** {review.overall_assessment}
**Reviewed by:** Design Review Agent v{review.agent_version}
**Date:** {timestamp_str}

## Summary

- **Total Issues:** {total_issues}
- **Critical:** {review.critical_issue_count}
- **High:** {review.high_issue_count}
- **Medium:** {review.medium_issue_count}
- **Low:** {review.low_issue_count}

"""

    # Add issues by severity
    if review.critical_issue_count > 0:
        md += "## Critical Issues\n\n"
        for issue in review.issues_found:
            if issue.severity == "Critical":
                md += f"""### {issue.issue_id}: {issue.description}

**Category:** {issue.category}
**Severity:** {issue.severity}
**Affected Phase:** {issue.affected_phase}
**Evidence:** {issue.evidence}

{issue.impact}

"""

    if review.high_issue_count > 0:
        md += "## High Issues\n\n"
        for issue in review.issues_found:
            if issue.severity == "High":
                md += f"""### {issue.issue_id}: {issue.description}

**Category:** {issue.category}
**Evidence:** {issue.evidence}

{issue.impact}

"""

    if review.medium_issue_count > 0:
        md += "## Medium Issues\n\n"
        for issue in review.issues_found:
            if issue.severity == "Medium":
                md += (
                    f"- **{issue.issue_id}**: {issue.description} ({issue.category})\n"
                )
        md += "\n"

    if review.low_issue_count > 0:
        md += "## Low Issues\n\n"
        for issue in review.issues_found:
            if issue.severity == "Low":
                md += (
                    f"- **{issue.issue_id}**: {issue.description} ({issue.category})\n"
                )
        md += "\n"

    # Add improvement suggestions
    if review.improvement_suggestions:
        md += "## Improvement Suggestions\n\n"
        for suggestion in review.improvement_suggestions:
            if suggestion.priority == "High":
                md += f"""### {suggestion.suggestion_id}: {suggestion.description}

**Priority:** {suggestion.priority}
**Category:** {suggestion.category}
"""
                if suggestion.related_issue_id:
                    md += f"**Addresses:** {suggestion.related_issue_id}\n"

                md += f"\n{suggestion.implementation_notes}\n\n"

    # Add phase-aware breakdown
    if review.planning_phase_issues or review.design_phase_issues:
        md += "## Phase-Aware Issue Breakdown\n\n"
        if review.planning_phase_issues:
            md += f"- **Planning Phase Issues:** {len(review.planning_phase_issues)}\n"
        if review.design_phase_issues:
            md += f"- **Design Phase Issues:** {len(review.design_phase_issues)}\n"
        md += "\n"

    # Add metadata
    duration_ms = getattr(review, "review_duration_ms", None)
    if duration_ms:
        md += f"""---

*Review completed in {duration_ms / 1000:.1f} seconds*
"""

    return md


def render_code_manifest_markdown(code: GeneratedCode) -> str:
    """
    Render GeneratedCode metadata as human-readable Markdown.

    Args:
        code: GeneratedCode Pydantic model

    Returns:
        Markdown formatted string
    """
    md = f"""# Code Generation Manifest: {code.task_id}

**Project ID:** {code.project_id or "N/A"}
**Generated by:** Code Agent v{code.agent_version}
**Timestamp:** {code.generation_timestamp or "N/A"}

## Summary

- **Total Files:** {code.total_files}
- **Total Lines of Code:** {code.total_lines_of_code:,}
- **Test Coverage Target:** {code.test_coverage_target or 0}%

## File Structure

"""

    # Add file structure
    for directory, files in sorted(code.file_structure.items()):
        md += f"**{directory}/**\n"
        for file in sorted(files):
            md += f"- {file}\n"
        md += "\n"

    # Add generated files summary
    md += "## Generated Files\n\n"

    # Group by file type
    source_files = [f for f in code.files if f.file_type == "source"]
    test_files = [f for f in code.files if f.file_type == "test"]
    config_files = [f for f in code.files if f.file_type == "config"]
    other_files = [
        f for f in code.files if f.file_type not in ["source", "test", "config"]
    ]

    if source_files:
        md += "### Source Files\n\n"
        for file in source_files:
            md += f"- `{file.file_path}` - {file.description}\n"
        md += "\n"

    if test_files:
        md += "### Test Files\n\n"
        for file in test_files:
            md += f"- `{file.file_path}` - {file.description}\n"
        md += "\n"

    if config_files:
        md += "### Configuration Files\n\n"
        for file in config_files:
            md += f"- `{file.file_path}` - {file.description}\n"
        md += "\n"

    # Add implementation notes
    md += f"""## Implementation Notes

{code.implementation_notes}

"""

    # Add dependencies
    if code.dependencies:
        md += "## Dependencies\n\n"
        md += "```\n"
        for dep in code.dependencies:
            md += f"{dep}\n"
        md += "```\n\n"

    # Add setup instructions
    if code.setup_instructions:
        md += f"""## Setup Instructions

{code.setup_instructions}

"""

    # Add traceability
    if code.semantic_units_implemented or code.components_implemented:
        md += "## Traceability\n\n"
        if code.semantic_units_implemented:
            md += (
                f"- **Semantic Units:** {', '.join(code.semantic_units_implemented)}\n"
            )
        if code.components_implemented:
            md += f"- **Components:** {', '.join(code.components_implemented)}\n"
        md += "\n"

    md += "---\n\n*See individual files in src/, tests/, etc. for actual code*\n"

    return md


def render_code_review_markdown(review: CodeReviewReport | None) -> str:
    """
    Render CodeReviewReport as human-readable Markdown.

    Args:
        review: CodeReviewReport Pydantic model

    Returns:
        Markdown formatted string
    """
    if review is None:
        return "# Code Review Report\n\n*Report not available*\n"

    # Get counts (handle both old and new field names)
    critical = getattr(review, "critical_count", 0)
    high = getattr(review, "high_count", 0)
    medium = getattr(review, "medium_count", 0)
    low = getattr(review, "low_count", 0)
    files_reviewed = getattr(review, "files_reviewed", 0)
    lines_reviewed = getattr(review, "total_lines_reviewed", 0)

    md = f"""# Code Review Report: {review.task_id}

**Review ID:** {review.review_id}
**Review Status:** {review.review_status}
**Reviewed by:** Code Review Agent v{review.agent_version}
**Date:** {review.review_timestamp}

## Summary

- **Files Reviewed:** {files_reviewed}
- **Lines Reviewed:** {lines_reviewed:,}
- **Total Issues:** {review.total_issues}
- **Critical:** {critical}
- **High:** {high}
- **Medium:** {medium}
- **Low:** {low}

"""

    # Add critical issues
    if critical > 0:
        md += "## Critical Issues\n\n"
        for issue in review.issues_found:
            if issue.severity == "Critical":
                md += f"""### {issue.issue_id}: {issue.description}

**Category:** {issue.category}
**Severity:** {issue.severity}
**Affected Phase:** {issue.affected_phase}
**File:** `{issue.file_path}`
"""
                if issue.line_number:
                    md += f"**Line:** {issue.line_number}\n"

                if issue.code_snippet:
                    md += f"\n```python\n{issue.code_snippet}\n```\n"

                md += f"\n**Impact:** {issue.impact}\n\n"

    # Add high issues
    if high > 0:
        md += "## High Issues\n\n"
        for issue in review.issues_found:
            if issue.severity == "High":
                md += f"""### {issue.issue_id}: {issue.description}

**Category:** {issue.category}
**File:** `{issue.file_path}:{issue.line_number or 'N/A'}`

{issue.impact}

"""

    # Add medium/low issues summary
    if medium > 0 or low > 0:
        md += "## Other Issues\n\n"
        for issue in review.issues_found:
            if issue.severity in ["Medium", "Low"]:
                md += f"- **[{issue.severity}]** {issue.issue_id}: {issue.description} (`{issue.file_path}`)\n"
        md += "\n"

    # Add improvement suggestions
    if review.improvement_suggestions:
        md += "## Improvement Suggestions\n\n"
        for suggestion in review.improvement_suggestions:
            if suggestion.priority == "High":
                md += f"""### {suggestion.suggestion_id}: {suggestion.description}

**Priority:** {suggestion.priority}
**Category:** {suggestion.category}
"""
                if suggestion.related_issue_id:
                    md += f"**Fixes:** {suggestion.related_issue_id}\n"

                md += f"\n{suggestion.implementation_notes}\n"

                if suggestion.suggested_code:
                    md += f"\n**Suggested Fix:**\n```python\n{suggestion.suggested_code}\n```\n"

                md += "\n"

    # Add specialist results
    md += """## Specialist Review Results

"""

    specialists = [
        ("Security Review", review.security_review_passed),
        ("Code Quality Review", review.quality_review_passed),
        ("Performance Review", review.performance_review_passed),
        ("Standards Compliance", review.standards_review_passed),
        ("Testing Review", review.testing_review_passed),
        ("Maintainability Review", review.maintainability_review_passed),
    ]

    for name, passed in specialists:
        status_text = "PASS" if passed else "FAIL"
        md += f"- {name}: {status_text}\n"

    md += "\n"

    # Add phase-aware breakdown
    if (
        review.planning_phase_issues
        or review.design_phase_issues
        or review.code_phase_issues
    ):
        md += "## Phase-Aware Issue Breakdown\n\n"
        if review.planning_phase_issues:
            md += f"- **Planning Phase Issues:** {len(review.planning_phase_issues)}\n"
        if review.design_phase_issues:
            md += f"- **Design Phase Issues:** {len(review.design_phase_issues)}\n"
        if review.code_phase_issues:
            md += f"- **Code Phase Issues:** {len(review.code_phase_issues)}\n"
        md += "\n"

    # Add metadata
    duration_secs = getattr(review, "review_duration_seconds", None)
    if duration_secs:
        md += f"""---

*Review completed in {duration_secs:.1f} seconds*
"""

    return md


def render_test_report_markdown(report: TestReport) -> str:
    """
    Render TestReport as human-readable Markdown.

    Args:
        report: TestReport Pydantic model

    Returns:
        Markdown formatted string
    """
    # Status emoji
    status_emoji = {
        "PASS": "✅",
        "FAIL": "❌",
        "BUILD_FAILED": "🔴",
    }
    emoji = status_emoji.get(report.test_status, "❓")

    md = f"""# Test Report: {report.task_id}

**Test Status:** {emoji} {report.test_status}
**Tested by:** Test Agent v{report.agent_version}
**Date:** {report.test_timestamp}
**Duration:** {report.test_duration_seconds:.1f}s

## Build Status

**Build Successful:** {"✅ Yes" if report.build_successful else "❌ No"}

"""

    if report.build_errors:
        md += "### Build Errors\n\n"
        for error in report.build_errors:
            md += f"- {error}\n"
        md += "\n"

    # Test execution summary
    md += f"""## Test Execution Summary

- **Total Tests:** {report.test_summary.get('total_tests', 0)}
- **Passed:** {report.test_summary.get('passed', 0)} ✅
- **Failed:** {report.test_summary.get('failed', 0)} ❌
- **Skipped:** {report.test_summary.get('skipped', 0)} ⏭️
- **Coverage:** {report.coverage_percentage or 'N/A'}%

## Test Generation

- **Tests Generated:** {report.total_tests_generated}
- **Test Files Created:** {len(report.test_files_created)}

"""

    if report.test_files_created:
        for file in report.test_files_created:
            md += f"  - `{file}`\n"
        md += "\n"

    # Defects summary
    md += f"""## Defects Summary

- **Total Defects:** {len(report.defects_found)}
- **Critical:** {report.critical_defects} 🔴
- **High:** {report.high_defects} 🟠
- **Medium:** {report.medium_defects} 🟡
- **Low:** {report.low_defects} 🟢

"""

    # Critical defects
    if report.critical_defects > 0:
        md += "## Critical Defects\n\n"
        for defect in report.defects_found:
            if defect.severity == "Critical":
                md += f"""### {defect.defect_id}: {defect.description}

**Type:** {defect.defect_type}
**Severity:** {defect.severity}
**Phase Injected:** {defect.phase_injected}
**File:** `{defect.file_path or 'N/A'}:{defect.line_number or 'N/A'}`

**Evidence:**
```
{defect.evidence}
```

**Impact:** This is a critical defect that must be fixed before proceeding.

---

"""

    # High defects
    if report.high_defects > 0:
        md += "## High Priority Defects\n\n"
        for defect in report.defects_found:
            if defect.severity == "High":
                md += f"""### {defect.defect_id}: {defect.description}

**Type:** {defect.defect_type}
**Phase Injected:** {defect.phase_injected}
**File:** `{defect.file_path or 'N/A'}:{defect.line_number or 'N/A'}`

**Evidence:**
```
{defect.evidence}
```

---

"""

    # Medium and low defects (summary only)
    if report.medium_defects > 0 or report.low_defects > 0:
        md += "## Other Defects\n\n"
        for defect in report.defects_found:
            if defect.severity in ["Medium", "Low"]:
                md += f"- **[{defect.severity}]** {defect.defect_id}: {defect.description} "
                md += f"({defect.defect_type}) - `{defect.file_path or 'N/A'}`\n"
        md += "\n"

    # Defect analysis
    if len(report.defects_found) > 0:
        md += "## Defect Analysis\n\n"

        # Group by phase injected
        phases = {}
        for defect in report.defects_found:
            phase = defect.phase_injected
            if phase not in phases:
                phases[phase] = []
            phases[phase].append(defect)

        md += "### Defects by Phase Injected\n\n"
        for phase, defects in sorted(phases.items()):
            md += f"- **{phase}:** {len(defects)} defects\n"
        md += "\n"

        # Group by defect type
        types = {}
        for defect in report.defects_found:
            dtype = defect.defect_type
            if dtype not in types:
                types[dtype] = []
            types[dtype].append(defect)

        md += "### Defects by Type\n\n"
        for dtype, defects in sorted(types.items()):
            md += f"- **{dtype}:** {len(defects)} defects\n"
        md += "\n"

    # Recommendations
    if report.test_status != "PASS":
        md += "## Recommendations\n\n"

        if report.test_status == "BUILD_FAILED":
            md += """### Immediate Actions Required

1. Fix all build errors before proceeding
2. Verify all dependencies are installed
3. Check import statements and module paths
4. Return to Code Agent for corrections

"""
        elif report.critical_defects > 0 or report.high_defects > 0:
            md += """### Immediate Actions Required

1. Address all Critical and High severity defects
2. Re-run tests after fixes
3. Return to Code Agent if needed

"""
        else:
            md += """### Suggested Actions

1. Review and address Medium/Low severity defects
2. Consider proceeding with caution
3. Document known issues for future work

"""

    # Footer
    md += f"""---

*Test report generated by Test Agent v{report.agent_version}*
"""

    return md


def render_postmortem_report_markdown(report: PostmortemReport) -> str:
    """
    Render PostmortemReport as human-readable Markdown.

    Args:
        report: PostmortemReport Pydantic model

    Returns:
        Markdown formatted string
    """
    md = f"""# Postmortem Analysis Report: {report.task_id}

**Analysis Date:** {report.analysis_timestamp.strftime('%Y-%m-%d %H:%M:%S')}

## Executive Summary

{report.summary}

---

## Estimation Accuracy

Comparison of planned vs. actual metrics:

| Metric | Planned | Actual | Variance |
|--------|---------|--------|----------|
| **Latency (ms)** | {report.estimation_accuracy.latency_ms.planned:,.0f} | {report.estimation_accuracy.latency_ms.actual:,.0f} | {report.estimation_accuracy.latency_ms.variance_percent:+.1f}% |
| **Tokens** | {report.estimation_accuracy.tokens.planned:,.0f} | {report.estimation_accuracy.tokens.actual:,.0f} | {report.estimation_accuracy.tokens.variance_percent:+.1f}% |
| **API Cost (USD)** | ${report.estimation_accuracy.api_cost.planned:.4f} | ${report.estimation_accuracy.api_cost.actual:.4f} | {report.estimation_accuracy.api_cost.variance_percent:+.1f}% |
| **Semantic Complexity** | {report.estimation_accuracy.semantic_complexity.planned:.1f} | {report.estimation_accuracy.semantic_complexity.actual:.1f} | {report.estimation_accuracy.semantic_complexity.variance_percent:+.1f}% |

**Estimation Quality:**
"""

    # Assess estimation quality
    avg_variance = (
        abs(report.estimation_accuracy.latency_ms.variance_percent)
        + abs(report.estimation_accuracy.tokens.variance_percent)
        + abs(report.estimation_accuracy.api_cost.variance_percent)
    ) / 3

    if avg_variance <= 10:
        md += "✅ **Excellent** - Average variance within ±10%\n"
    elif avg_variance <= 20:
        md += "✓ **Good** - Average variance within ±20% (acceptable)\n"
    elif avg_variance <= 30:
        md += "⚠️ **Fair** - Average variance >20% (needs improvement)\n"
    else:
        md += "❌ **Poor** - Average variance >30% (significant estimation issues)\n"

    md += "\n"

    # Quality Metrics section
    md += f"""---

## Quality Metrics

**Defect Summary:**
- **Total Defects:** {report.quality_metrics.total_defects}
- **Defect Density:** {report.quality_metrics.defect_density:.3f} defects per complexity unit

"""

    # Defect injection by phase
    if report.quality_metrics.defect_injection_by_phase:
        md += "### Defects Injected by Phase\n\n"
        for phase, count in sorted(
            report.quality_metrics.defect_injection_by_phase.items(),
            key=lambda x: x[1],
            reverse=True,
        ):
            md += f"- **{phase}:** {count} defects\n"
        md += "\n"

    # Defect removal by phase
    if report.quality_metrics.defect_removal_by_phase:
        md += "### Defects Removed by Phase\n\n"
        for phase, count in sorted(
            report.quality_metrics.defect_removal_by_phase.items(),
            key=lambda x: x[1],
            reverse=True,
        ):
            md += f"- **{phase}:** {count} defects\n"
        md += "\n"

    # Phase yield
    if report.quality_metrics.phase_yield:
        md += "### Phase Yield (% of defects caught in each phase)\n\n"
        for phase, yield_pct in sorted(
            report.quality_metrics.phase_yield.items(),
            key=lambda x: x[1],
            reverse=True,
        ):
            md += f"- **{phase}:** {yield_pct:.1f}%\n"
        md += "\n"

    # Root Cause Analysis section
    md += """---

## Root Cause Analysis

Top defect types by total effort to fix:

"""

    if report.root_cause_analysis:
        for i, item in enumerate(report.root_cause_analysis, 1):
            md += f"""### {i}. {item.defect_type}

- **Occurrences:** {item.occurrence_count}
- **Total Fix Effort:** ${item.total_effort_to_fix:.4f} USD
- **Average Fix Effort:** ${item.average_effort_to_fix:.4f} USD per occurrence

**Recommendation:**
{item.recommendation}

"""
    else:
        md += "*No defects found - excellent quality!*\n\n"

    # Recommendations section
    md += """---

## Recommendations

"""

    if report.recommendations:
        for i, rec in enumerate(report.recommendations, 1):
            md += f"{i}. {rec}\n"
        md += "\n"
    else:
        md += "*Continue current development process - no significant issues detected.*\n\n"

    # Next Steps
    md += """---

## Next Steps

"""

    if report.quality_metrics.total_defects > 0:
        md += """1. **Review Root Causes:** Examine top defect types and their recommendations
2. **Generate PIP:** Use `PostmortemAgent.generate_pip()` to create Process Improvement Proposal
3. **HITL Review:** Submit PIP for human approval
4. **Update Process:** Apply approved changes to prompts/checklists
5. **Monitor Impact:** Track defect reduction in subsequent tasks

"""
    else:
        md += """1. **Maintain Standards:** Continue current process with no changes
2. **Monitor Future Tasks:** Watch for any emerging patterns
3. **Document Success:** Record estimation accuracy for PROBE-AI refinement

"""

    # Footer
    md += f"""---

*Postmortem analysis performed by Postmortem Agent on {report.analysis_timestamp.strftime('%Y-%m-%d %H:%M:%S')}*
"""

    return md
