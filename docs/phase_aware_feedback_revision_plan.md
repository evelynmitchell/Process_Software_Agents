# Revision Plan: Phase-Aware Feedback Implementation

**Date:** 2025-11-17
**Status:** Proposed
**Related ADR:** `error_correction_feedback_loops_decision.md`
**Goal:** Update existing agents to support phase-aware feedback before implementing Code Agent

---

## Overview

Based on the Error Correction and Feedback Loops ADR, we need to revise existing agents (Planning, Design, Design Review) to support phase-aware feedback routing. This revision must be completed before implementing the Code Agent to ensure consistent architecture across all agents.

**Scope:**
- 3 existing agents need updates
- 2 data models need changes
- 6+ prompts need updates
- 24+ tests need updates/additions
- Documentation needs updates

**Estimated Effort:** 4-6 hours
**Estimated Cost:** ~$0.20-0.30 (E2E testing)

---

## Revision Tasks

### 1. Data Model Updates

#### 1.1 Update `DesignIssue` Model
**File:** `src/asp/models/design_review.py`

**Changes:**
```python
class DesignIssue(BaseModel):
    issue_id: str
    category: Literal[...]
    severity: Literal[...]
    description: str
    evidence: str
    impact: str
    affected_phase: Literal["Planning", "Design", "Both"] = Field(  # NEW
        default="Design",
        description=(
            "Phase where this issue was introduced:\n"
            "- Planning: Missing requirements, wrong decomposition, missing dependencies\n"
            "- Design: API design errors, data model issues, architectural problems\n"
            "- Both: Issues affecting both planning and design"
        )
    )
```

**Validation:**
- Add validator to ensure affected_phase is one of allowed values
- Update json_schema_extra examples to include affected_phase
- Add field to existing example issues

**Backward Compatibility:**
- Default value = "Design" ensures existing code works
- Optional field, so existing DesignIssue instances remain valid

#### 1.2 Update `DesignReviewReport` Model
**File:** `src/asp/models/design_review.py`

**Changes:**
```python
class DesignReviewReport(BaseModel):
    # ... existing fields ...

    # NEW: Phase-specific issue groupings
    planning_phase_issues: list[DesignIssue] = Field(
        default_factory=list,
        description="Issues that originated in the Planning phase"
    )
    design_phase_issues: list[DesignIssue] = Field(
        default_factory=list,
        description="Issues that originated in the Design phase"
    )
    multi_phase_issues: list[DesignIssue] = Field(
        default_factory=list,
        description="Issues affecting both Planning and Design phases"
    )

    # Keep existing issues_found for backward compatibility
    issues_found: list[DesignIssue] = Field(
        default_factory=list,
        description="All issues (for backward compatibility)"
    )
```

**Computed Properties:**
```python
@model_validator(mode='after')
def populate_phase_groups(self) -> 'DesignReviewReport':
    """Automatically group issues by affected_phase."""
    self.planning_phase_issues = [
        issue for issue in self.issues_found
        if issue.affected_phase in ["Planning", "Both"]
    ]
    self.design_phase_issues = [
        issue for issue in self.issues_found
        if issue.affected_phase in ["Design", "Both"]
    ]
    self.multi_phase_issues = [
        issue for issue in self.issues_found
        if issue.affected_phase == "Both"
    ]
    return self
```

**Testing:**
- Unit test: Phase grouping works correctly
- Unit test: Backward compatibility maintained
- Unit test: Model validation passes

---

### 2. Design Review Agent Updates

#### 2.1 Update Design Review Agent Prompts
**Files:** `prompts/design_review/security_review_v1.md` (and 5 other specialist prompts)

**Changes to Each Specialist Prompt:**

Add section on phase identification:
```markdown
## Phase Identification

For each issue you identify, determine which phase introduced the problem:

**Planning Phase Issues:**
- Missing semantic units or requirements
- Incorrect task decomposition
- Missing dependencies between units
- Fundamentally wrong understanding of requirements
- Missing non-functional requirements in decomposition

**Design Phase Issues:**
- Incorrect API design (wrong HTTP methods, missing error codes)
- Poor data model choices (wrong column types, missing indexes)
- Architectural problems (tight coupling, circular dependencies)
- Security vulnerabilities in design (missing encryption, weak auth)
- Performance issues (missing caching, inefficient queries)

**Both Phases:**
- Issues that require changes to both plan and design
- Example: Missing feature affects both decomposition AND architecture

**When Uncertain:** Default to "Design"

## Output Format

For each issue:
{
  "issue_id": "ISSUE-001",
  "category": "Security",
  "severity": "Critical",
  "description": "...",
  "evidence": "...",
  "impact": "...",
  "affected_phase": "Planning"  // NEW REQUIRED FIELD
}
```

**Update Example Outputs:**
- Add affected_phase to all example issues
- Show mix of Planning, Design, and Both classifications
- Include reasoning for phase attribution

**Files to Update:**
- `prompts/design_review/security_review_v1.md`
- `prompts/design_review/performance_review_v1.md`
- `prompts/design_review/data_integrity_review_v1.md`
- `prompts/design_review/maintainability_review_v1.md`
- `prompts/design_review/architecture_review_v1.md`
- `prompts/design_review/api_design_review_v1.md`

#### 2.2 Update Design Review Orchestrator
**File:** `src/asp/agents/design_review_orchestrator.py`

**Changes:**
- No major logic changes needed
- Orchestrator already aggregates issues from specialists
- Phase grouping happens automatically in DesignReviewReport model validator
- Add logging to show phase distribution

**New Logging:**
```python
logger.info(
    f"Review complete: {report.critical_issue_count} critical, "
    f"{report.high_issue_count} high issues. "
    f"Phase distribution: {len(report.planning_phase_issues)} planning, "
    f"{len(report.design_phase_issues)} design, "
    f"{len(report.multi_phase_issues)} both"
)
```

---

### 3. Planning Agent Updates

#### 3.1 Add Feedback Parameter
**File:** `src/asp/agents/planning_agent.py`

**Changes to `execute` method:**
```python
@track_agent_cost(...)
def execute(
    self,
    input_data: TaskRequirements,
    feedback: Optional[list[DesignIssue]] = None  # NEW
) -> ProjectPlan:
    """
    Execute Planning Agent logic with optional feedback.

    Args:
        input_data: TaskRequirements with task details
        feedback: Optional list of issues from Design Review requiring replanning

    Returns:
        ProjectPlan with decomposed semantic units and complexity scores
    """
    logger.info(
        f"Planning Agent executing for task_id={input_data.task_id}, "
        f"feedback_items={len(feedback) if feedback else 0}"
    )

    # If feedback provided, incorporate into decomposition
    if feedback:
        return self.decompose_task_with_feedback(input_data, feedback)
    else:
        return self.decompose_task(input_data)
```

**New Method:**
```python
def decompose_task_with_feedback(
    self,
    requirements: TaskRequirements,
    feedback: list[DesignIssue]
) -> ProjectPlan:
    """
    Decompose task incorporating feedback from Design Review.

    This method:
    1. Analyzes feedback issues to understand what was missed/wrong
    2. Loads the feedback-aware decomposition prompt
    3. Includes previous attempt context + feedback
    4. Generates improved semantic units
    5. Returns updated ProjectPlan

    Args:
        requirements: Original task requirements
        feedback: Issues from Design Review indicating planning problems

    Returns:
        Updated ProjectPlan addressing feedback
    """
    # Format feedback for prompt
    feedback_text = self._format_feedback(feedback)

    # Load feedback-aware prompt
    prompt_template = self.load_prompt("planning_agent_v1_with_feedback")

    # Include both requirements and feedback
    formatted_prompt = self.format_prompt(
        prompt_template,
        description=requirements.description,
        requirements=requirements.requirements,
        feedback=feedback_text
    )

    # Call LLM with feedback context
    # ... rest of implementation
```

#### 3.2 Add Feedback Prompt Template
**New File:** `prompts/planning/planning_agent_v1_with_feedback.md`

**Content:**
```markdown
# Task Decomposition with Feedback

You are a Planning Agent revising a previous task decomposition based on Design Review feedback.

## Original Task
**Description:** {description}
**Requirements:** {requirements}

## Feedback from Design Review
The following issues were identified in the Design phase that indicate problems with the original planning:

{feedback}

## Your Task
Reanalyze the requirements and create an IMPROVED task decomposition that addresses all feedback issues.

Pay special attention to:
- Missing requirements or semantic units identified in feedback
- Incorrect complexity estimates
- Missing dependencies between units
- Ambiguous requirements that led to design problems

[... rest of standard decomposition instructions ...]
```

---

### 4. Design Agent Updates

#### 4.1 Add Feedback Parameter
**File:** `src/asp/agents/design_agent.py`

**Changes to `execute` method:**
```python
@track_agent_cost(...)
def execute(
    self,
    input_data: DesignInput,
    feedback: Optional[list[DesignIssue]] = None  # NEW
) -> DesignSpecification:
    """
    Execute Design Agent with optional feedback.

    Args:
        input_data: DesignInput containing requirements, project_plan, etc.
        feedback: Optional list of issues requiring redesign

    Returns:
        DesignSpecification with complete technical design
    """
    logger.info(
        f"Executing DesignAgent for task_id={input_data.task_id}, "
        f"feedback_items={len(feedback) if feedback else 0}"
    )

    try:
        if feedback:
            design_spec = self._generate_design_with_feedback(input_data, feedback)
        else:
            design_spec = self._generate_design(input_data)

        # ... existing validation logic ...

        return design_spec
```

**New Method:**
```python
def _generate_design_with_feedback(
    self,
    input_data: DesignInput,
    feedback: list[DesignIssue]
) -> DesignSpecification:
    """
    Generate design incorporating feedback from Design Review.

    Similar to Planning Agent, this method:
    1. Analyzes feedback to understand design problems
    2. Loads feedback-aware design prompt
    3. Includes previous context + specific issues to fix
    4. Generates improved design

    Args:
        input_data: Original design input
        feedback: Issues from Design Review

    Returns:
        Updated DesignSpecification addressing feedback
    """
    # Implementation similar to Planning Agent
```

#### 4.2 Add Feedback Prompt Template
**New File:** `prompts/design/design_agent_v1_with_feedback.md`

Similar structure to Planning feedback prompt.

---

### 5. Testing Updates

#### 5.1 Unit Tests - Design Review Models
**File:** `tests/unit/test_models/test_design_review.py` (create if doesn't exist)

**New Tests:**
```python
def test_design_issue_with_affected_phase():
    """Test DesignIssue includes affected_phase field."""
    issue = DesignIssue(
        issue_id="ISSUE-001",
        category="Security",
        severity="High",
        description="Missing authentication",
        evidence="No auth endpoints in API design",
        impact="Security vulnerability",
        affected_phase="Planning"  # NEW
    )
    assert issue.affected_phase == "Planning"

def test_design_issue_defaults_to_design_phase():
    """Test affected_phase defaults to Design."""
    issue = DesignIssue(
        issue_id="ISSUE-002",
        category="Performance",
        severity="Medium",
        description="Missing index",
        evidence="users table",
        impact="Slow queries"
        # No affected_phase specified
    )
    assert issue.affected_phase == "Design"

def test_design_review_report_phase_grouping():
    """Test DesignReviewReport automatically groups issues by phase."""
    issues = [
        DesignIssue(..., affected_phase="Planning"),
        DesignIssue(..., affected_phase="Design"),
        DesignIssue(..., affected_phase="Both"),
    ]

    report = DesignReviewReport(
        task_id="TEST-001",
        review_id="REVIEW-TEST-001-20251117-120000",
        overall_assessment="FAIL",
        automated_checks={},
        issues_found=issues,
        # ... other required fields ...
    )

    assert len(report.planning_phase_issues) == 2  # Planning + Both
    assert len(report.design_phase_issues) == 2    # Design + Both
    assert len(report.multi_phase_issues) == 1     # Both only
```

#### 5.2 Unit Tests - Planning Agent with Feedback
**File:** `tests/unit/test_agents/test_planning_agent.py`

**New Tests:**
```python
def test_planning_agent_execute_with_feedback(mock_llm_client):
    """Test Planning Agent accepts and processes feedback."""
    agent = PlanningAgent(llm_client=mock_llm_client)

    requirements = TaskRequirements(...)
    feedback = [
        DesignIssue(
            issue_id="ISSUE-001",
            category="Architecture",
            severity="High",
            description="Missing authentication semantic unit",
            evidence="No auth in decomposition",
            impact="Cannot design auth system",
            affected_phase="Planning"
        )
    ]

    # Mock should receive feedback in prompt
    mock_llm_client.messages.create.return_value = Mock(...)

    plan = agent.execute(requirements, feedback=feedback)

    # Verify feedback was included in LLM call
    call_args = mock_llm_client.messages.create.call_args
    assert "authentication" in call_args[1]["messages"][0]["content"].lower()
    assert "feedback" in call_args[1]["messages"][0]["content"].lower()
```

#### 5.3 Unit Tests - Design Agent with Feedback
**File:** `tests/unit/test_agents/test_design_agent.py`

Similar to Planning Agent feedback tests.

#### 5.4 E2E Tests - Full Correction Flow
**File:** `tests/e2e/test_correction_flow_e2e.py` (new file)

**New Tests:**
```python
async def test_planning_error_correction_flow():
    """
    Test full flow: Planning → Design → Review → Replan → Redesign.

    Scenario: Planning misses authentication requirement
    """
    # 1. Planning Agent: Initial decomposition (missing auth)
    planning_agent = PlanningAgent()
    requirements = TaskRequirements(
        task_id="CORRECTION-001",
        description="Build user management API",
        requirements="Users should be able to register, login, update profile"
    )
    initial_plan = planning_agent.execute(requirements)

    # 2. Design Agent: Create design based on incomplete plan
    design_agent = DesignAgent()
    design_input = DesignInput(
        task_id="CORRECTION-001",
        requirements=requirements.requirements,
        project_plan=initial_plan
    )
    initial_design = design_agent.execute(design_input)

    # 3. Design Review: Should catch missing auth
    review_agent = DesignReviewOrchestrator()
    review_report = await review_agent.execute(initial_design)

    # Verify review failed due to planning issue
    assert review_report.overall_assessment in ["FAIL", "NEEDS_IMPROVEMENT"]
    assert len(review_report.planning_phase_issues) > 0

    # 4. Replan with feedback
    corrected_plan = planning_agent.execute(
        requirements,
        feedback=review_report.planning_phase_issues
    )

    # Verify plan now includes auth
    auth_units = [u for u in corrected_plan.semantic_units if "auth" in u.description.lower()]
    assert len(auth_units) > 0

    # 5. Redesign with corrected plan
    corrected_design_input = DesignInput(
        task_id="CORRECTION-001",
        requirements=requirements.requirements,
        project_plan=corrected_plan
    )
    corrected_design = design_agent.execute(corrected_design_input)

    # 6. Review corrected design
    final_review = await review_agent.execute(corrected_design)

    # Verify review now passes
    assert final_review.overall_assessment == "PASS"
    assert len(final_review.planning_phase_issues) == 0
```

---

### 6. Documentation Updates

#### 6.1 Update Agent Documentation
**Files:**
- `docs/planning_agent_architecture_decision.md`
- `docs/design_agent_architecture_decision.md`
- `docs/design_review_agent_architecture_decision.md`

**Add Section:** "Phase-Aware Feedback Support (Added 2025-11-17)"
- Explain feedback parameter
- Show example usage with feedback
- Link to Error Correction ADR

#### 6.2 Update README
**File:** `README.md`

**Add to Agent Status:**
```markdown
### Phase-Aware Feedback (New Feature)

All agents now support phase-aware error correction:
- Design Review can identify if issues originated in Planning vs Design
- Orchestrator can route corrections to appropriate upstream agent
- Prevents error propagation through pipeline

See: `docs/error_correction_feedback_loops_decision.md`
```

---

## Implementation Order

### Phase 1: Data Models (30 min)
1. Update `DesignIssue` with `affected_phase` field
2. Update `DesignReviewReport` with phase groupings
3. Add model validators
4. Write unit tests for models

### Phase 2: Prompts (45 min)
5. Update 6 specialist review prompts with phase identification guidance
6. Create `planning_agent_v1_with_feedback.md` prompt
7. Create `design_agent_v1_with_feedback.md` prompt

### Phase 3: Agent Code (90 min)
8. Update Planning Agent with feedback parameter
9. Update Design Agent with feedback parameter
10. Update Design Review Orchestrator logging
11. Write unit tests for feedback functionality

### Phase 4: Integration Testing (90 min)
12. Create E2E correction flow tests
13. Run full test suite
14. Fix any failing tests
15. Validate with real API calls

### Phase 5: Documentation (30 min)
16. Update ADR documents
17. Update README
18. Update agent user guides

**Total Estimated Time:** 4-6 hours
**Total Estimated Cost:** $0.20-0.30 (E2E tests only)

---

## Validation Checklist

Before continuing to Code Agent:
- [ ] All existing unit tests still pass
- [ ] New model fields have unit test coverage
- [ ] Planning Agent accepts and uses feedback
- [ ] Design Agent accepts and uses feedback
- [ ] Design Review prompts include phase identification
- [ ] E2E test demonstrates full correction flow
- [ ] Documentation updated
- [ ] No regression in existing functionality
- [ ] Backward compatibility maintained (optional feedback parameter)

---

## Risk Mitigation

**Risk:** Breaking existing tests
- *Mitigation:* Make feedback parameter optional with default=None
- *Mitigation:* Default affected_phase="Design" for backward compatibility
- *Mitigation:* Run full test suite after each change

**Risk:** Prompt changes reduce quality
- *Mitigation:* Test with real API calls before committing
- *Mitigation:* Compare review quality before/after changes
- *Mitigation:* Keep old prompts as backup (_v1_original.md)

**Risk:** Increased prompt complexity confuses LLM
- *Mitigation:* Keep phase identification section concise
- *Mitigation:* Provide clear examples in prompts
- *Mitigation:* Test with multiple scenarios

**Risk:** Time estimate too optimistic
- *Mitigation:* Break work into small commits
- *Mitigation:* Can pause after any phase
- *Mitigation:* Prioritize critical changes first

---

## Success Criteria

1. **Functionality:**
   - Planning Agent can accept feedback and regenerate improved plans
   - Design Agent can accept feedback and regenerate improved designs
   - Design Review correctly identifies affected_phase for issues

2. **Quality:**
   - All tests pass (existing + new)
   - No regression in agent performance
   - Phase identification is accurate (>80% correct in E2E tests)

3. **Maintainability:**
   - Code is well-documented
   - Changes are backward compatible
   - Architecture supports future orchestrator implementation

4. **Observability:**
   - Telemetry captures feedback iterations
   - Logs show phase distribution of issues
   - Can track correction success rates

---

## Next Steps After Revision

Once existing agents are updated:
1. Design Code Agent with phase-aware models from the start
2. Implement Code Review Agent with same patterns
3. Build main TSP Orchestrator with routing logic
4. Add iteration limits and human escalation
5. Measure impact on quality and cost

---

**Document Status:** Proposed
**Approval Required:** Yes (before starting implementation)
**Estimated Start:** After approval
**Target Completion:** Same day (4-6 hour block)
