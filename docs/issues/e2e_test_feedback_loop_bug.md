# E2E Test Issue: Orchestrator Feedback Loop Broken

**Issue ID:** ISSUE-E2E-001
**Date Discovered:** November 21, 2025
**Severity:** Critical
**Status:** Open
**Affects:** Planning-Design-Review orchestrator feedback loop

## Executive Summary

E2E tests revealed a critical bug in the PlanningDesignOrchestrator's feedback loop mechanism. When the Design Review Agent identifies issues and attempts to route them back to the Design Agent for revision, the Design Agent fails due to a missing `task_id` variable in its feedback prompt template. This causes an infinite error loop and prevents the orchestrator from completing its phase-aware feedback iterations.

## Issue Details

### What Happened

During E2E test execution (`test_complete_agent_pipeline_hello_world`), the following sequence occurred:

1. ✅ Planning Agent executed successfully (4 units, complexity 64)
2. ✅ Design Agent executed successfully (2 APIs, 4 components)
3. ✅ Design Review Agent executed successfully, identified 5 issues (1 high, 3 medium, 1 low severity)
4. ⚠️ Orchestrator attempted to route feedback back to Design Agent
5. ❌ Design Agent failed with missing prompt variable error
6. 🔄 Orchestrator entered infinite error loop, retrying indefinitely

### Error Message

```
ERROR:asp.agents.design_agent:DesignAgent execution failed: Missing required prompt variable: '\n  "task_id"'
Template requires: # ROLE

You are a **Software Design Agent** revising a previous design specification based on Design Review feedback.
...
# YOUR TASK

**Original Requirements:**
{description}

**Project Plan:**
{project_plan}

**Previous Design Specification:**
(You created this previously - it has issues that need fixing)

**Feedback from Design Review:**
{feedback}

Provided: dict_keys(['description', 'project_plan', 'feedback'])
```

### Root Cause

The Design Agent has two prompt templates:

1. **Initial design prompt** (`design_agent.txt`): Used for first-pass design generation
   - Variables: `{task_id}`, `{description}`, `{project_plan}`, `{coding_standards}`

2. **Feedback revision prompt** (`design_agent_with_feedback.txt`): Used when revising based on Design Review feedback
   - **Expected variables:** `{task_id}`, `{description}`, `{project_plan}`, `{feedback}`, `{previous_design}`
   - **Actually provided:** `{description}`, `{project_plan}`, `{feedback}` only

**Missing variables:** `{task_id}` and `{previous_design}`

### Impact

**Critical Impact:**
- ❌ Orchestrator feedback loop completely broken
- ❌ Design phase cannot iterate on design review issues
- ❌ E2E tests cannot complete Planning→Design→Review phase
- ❌ Multi-stage Code Agent never tested (blocked by this issue)
- ❌ Full pipeline validation impossible

**Workflow Impact:**
- Orchestrator is stuck after first design review
- No iterative improvement of designs based on feedback
- Phase-aware feedback loops (core ADR feature) non-functional

## Evidence

### Test Execution Log

```
INFO:asp.orchestrators.planning_design_orchestrator:Design review complete: FAIL, issues: 5 total, 0 critical, 1 high
INFO:asp.orchestrators.planning_design_orchestrator:  → 5 design-phase issues
WARNING:asp.orchestrators.planning_design_orchestrator:Design review FAILED: 0 critical, 1 high severity issues
INFO:asp.orchestrators.planning_design_orchestrator:Routing 5 issues back to Design Agent
INFO:asp.orchestrators.planning_design_orchestrator:Design Agent: executing with 5 feedback items
INFO:asp.agents.design_agent:Executing DesignAgent for task_id=HW-001, feedback_items=5
ERROR:asp.agents.design_agent:DesignAgent execution failed: Missing required prompt variable: '\n  "task_id"'
Template requires: ... [full prompt shown above] ...
Provided: dict_keys(['description', 'project_plan', 'feedback'])
ERROR:asp.orchestrators.planning_design_orchestrator:Design Agent failed: Design generation failed: Missing required prompt variable: '\n  "task_id"'
[Error repeats indefinitely in loop]
```

### Test Environment

- **Test File:** `tests/e2e/test_all_agents_hello_world_e2e.py`
- **Test Name:** `test_complete_agent_pipeline_hello_world`
- **Python Version:** 3.12.1
- **Pytest Version:** 9.0.0
- **Duration Before Halt:** ~1 minute (then infinite loop)
- **Total Cost Before Halt:** $0.0132 + $0.0578 + $0.0435 = $0.1145

## Location in Code

### Orchestrator Code

**File:** `src/asp/orchestrators/planning_design_orchestrator.py`

**Feedback routing logic (approximate location ~line 150-200):**
```python
# After design review fails
if design_review_status == "FAIL":
    logger.warning(f"Design review FAILED: {critical_count} critical, {high_count} high severity issues")
    logger.info(f"Routing {len(design_issues)} issues back to Design Agent")

    # Re-execute Design Agent with feedback
    design_result = self.design_agent.execute(
        task_id=task_id,
        description=description,
        project_plan=project_plan,
        feedback_items=design_issues  # ❌ Missing task_id and previous_design in template vars
    )
```

### Design Agent Code

**File:** `src/asp/agents/design_agent.py`

**Template selection logic (approximate location ~line 80-120):**
```python
def execute(self, task_id, description, project_plan, feedback_items=None, ...):
    if feedback_items:
        # Use feedback revision prompt
        prompt_file = "design_agent_with_feedback.txt"
        template_vars = {
            'description': description,
            'project_plan': project_plan.model_dump_json(),
            'feedback': format_feedback_for_prompt(feedback_items)
            # ❌ MISSING: 'task_id': task_id
            # ❌ MISSING: 'previous_design': self._get_previous_design(task_id)
        }
    else:
        # Use initial design prompt
        prompt_file = "design_agent.txt"
        template_vars = {
            'task_id': task_id,  # ✅ Present in initial prompt
            'description': description,
            'project_plan': project_plan.model_dump_json(),
            'coding_standards': ...
        }
```

### Prompt Template

**File:** `src/asp/prompts/design_agent_with_feedback.txt`

**Template references (excerpt):**
```
# YOUR TASK

**Task ID:** {task_id}  ❌ Referenced but not provided

**Original Requirements:**
{description}  ✅ Provided

**Project Plan:**
{project_plan}  ✅ Provided

**Previous Design Specification:**
{previous_design}  ❌ Referenced but not provided

**Feedback from Design Review:**
{feedback}  ✅ Provided
```

## Proposed Fix

### Option 1: Add Missing Variables (Recommended)

**File:** `src/asp/agents/design_agent.py`

```python
def execute(self, task_id, description, project_plan, feedback_items=None, ...):
    if feedback_items:
        # Load previous design from artifacts
        previous_design = self._load_previous_design(task_id)

        prompt_file = "design_agent_with_feedback.txt"
        template_vars = {
            'task_id': task_id,  # ✅ FIX: Add task_id
            'description': description,
            'project_plan': project_plan.model_dump_json(),
            'feedback': self._format_feedback(feedback_items),
            'previous_design': previous_design.model_dump_json()  # ✅ FIX: Add previous design
        }
    else:
        # Initial design prompt (unchanged)
        ...
```

**Helper method to add:**
```python
def _load_previous_design(self, task_id: str) -> DesignSpecification:
    """Load previous design specification from artifacts directory."""
    artifact_path = f"artifacts/{task_id}/design.json"
    if not os.path.exists(artifact_path):
        raise FileNotFoundError(f"Previous design not found: {artifact_path}")

    with open(artifact_path, 'r') as f:
        design_data = json.load(f)

    return DesignSpecification.model_validate(design_data)
```

**Estimated effort:** 1-2 hours (includes testing)

### Option 2: Simplify Prompt Template

If loading previous design is complex, remove `{previous_design}` from template and add instruction that previous design is in artifacts:

**File:** `src/asp/prompts/design_agent_with_feedback.txt`

```diff
- **Previous Design Specification:**
- {previous_design}
+ **Previous Design Specification:**
+ Your previous design specification is available in artifacts/{task_id}/design.json.
+ Review it to understand what needs fixing based on the feedback below.
```

Still need to add `{task_id}` variable.

**Estimated effort:** 30 minutes

### Option 3: Fix Orchestrator to Pass Variables

**File:** `src/asp/orchestrators/planning_design_orchestrator.py`

Ensure orchestrator provides all required variables when calling Design Agent with feedback:

```python
# Load previous design result from first pass
previous_design = design_result.design_specification

# Re-execute with complete context
design_result = self.design_agent.execute(
    task_id=task_id,
    description=description,
    project_plan=project_plan,
    previous_design=previous_design,  # ✅ FIX: Pass previous design
    feedback_items=design_issues
)
```

**Estimated effort:** 1-2 hours (requires orchestrator and agent changes)

## Testing Plan

After implementing fix:

### Unit Tests

```python
def test_design_agent_with_feedback_has_required_variables():
    """Test that feedback prompt has all required variables."""
    agent = DesignAgent()

    # Execute with feedback
    result = agent.execute(
        task_id="TEST-001",
        description="Test task",
        project_plan=mock_project_plan,
        feedback_items=[mock_feedback_issue]
    )

    assert result is not None
    assert isinstance(result, DesignResult)
```

### Integration Tests

```python
def test_orchestrator_feedback_loop_completes():
    """Test that orchestrator can complete feedback iteration."""
    orchestrator = PlanningDesignOrchestrator()

    result = orchestrator.execute(
        task_id="TEST-001",
        description="Build simple API",
        max_iterations=2  # Allow feedback loop
    )

    # Should complete without infinite loop
    assert result.design_review.status in ["PASS", "FAIL"]
    assert result.design_specification is not None
```

### E2E Tests

```bash
# Run full E2E test suite
uv run pytest tests/e2e/test_all_agents_hello_world_e2e.py -v -s

# Expected: Test completes without hanging
# Expected: All 4 tests pass (Planning, Design, Code, Full Pipeline)
```

### Manual Validation

1. Run orchestrator with task that will fail design review
2. Verify Design Agent receives feedback and revises design
3. Verify second design review shows improvements
4. Verify feedback loop terminates (not infinite)

## Success Criteria

- [ ] Design Agent accepts feedback without missing variable error
- [ ] Orchestrator feedback loop completes within reasonable iterations (max 3-5)
- [ ] E2E tests pass Planning→Design→Review phase
- [ ] E2E tests complete full pipeline (reach Code Agent)
- [ ] No infinite loops observed
- [ ] Design revisions address feedback issues

## Related Issues

### Issue #2: DesignReviewReport Missing total_issues Attribute

**Severity:** Low (Non-blocking warning)

**Error:**
```
WARNING:asp.agents.design_review_agent:Failed to write artifacts: 'DesignReviewReport' object has no attribute 'total_issues'
AttributeError: 'DesignReviewReport' object has no attribute 'total_issues'
```

**Location:** `src/asp/utils/markdown_renderer.py:197`

**Fix:** Add `total_issues` property to `DesignReviewReport` model:

```python
class DesignReviewReport(BaseModel):
    ...
    critical_issues: list[ReviewIssue]
    high_issues: list[ReviewIssue]
    medium_issues: list[ReviewIssue]
    low_issues: list[ReviewIssue]

    @property
    def total_issues(self) -> int:
        """Calculate total number of issues."""
        return (
            len(self.critical_issues) +
            len(self.high_issues) +
            len(self.medium_issues) +
            len(self.low_issues)
        )
```

### Issue #3: Planning Agent Git Commit Failures

**Severity:** Low (Non-blocking warning)

**Error:**
```
WARNING:asp.agents.planning_agent:Failed to write artifacts: Failed to commit artifact: Git commit failed:
Command '['git', 'commit', '-m', 'Planning Agent: Add project plan for HW-001...']' returned non-zero exit status 1.
```

**Impact:** Artifacts are written to disk but not committed to git. Non-blocking for tests.

**Likely Cause:** No staged files for commit, or git configuration issue in test environment.

## Timeline

**Discovered:** November 21, 2025 00:35 UTC
**Documented:** November 21, 2025 00:45 UTC
**Assigned:** TBD
**Target Fix Date:** TBD
**Priority:** P0 (Blocks all E2E testing)

## Dependencies

**Blocks:**
- E2E test completion
- Multi-stage Code Agent validation
- Full pipeline testing (Planning → Postmortem)
- Orchestrator feedback loop validation
- Phase-aware iteration testing

**Depends On:**
- None (can be fixed independently)

## Notes

### Why This Wasn't Caught Earlier

1. **Unit tests don't test feedback path:** Design Agent unit tests only test initial design generation, not feedback-based revision
2. **Integration tests don't test Design Review failures:** Tests assume designs pass review on first attempt
3. **No orchestrator feedback loop tests:** Orchestrator tests mock the Design Review Agent to always return PASS

### Lessons Learned

1. **Template variable validation:** Need automated checks that prompt templates and template_vars dicts match
2. **Test feedback paths:** Unit tests should cover both success path and feedback/revision paths
3. **Orchestrator iteration testing:** Need tests that intentionally trigger feedback loops
4. **E2E tests are essential:** This bug only surfaced during full E2E test with real LLM responses

### Prevention Measures

**Add to CI/CD:**
```python
def test_all_prompts_have_matching_variables():
    """Validate all prompt templates have matching variable dictionaries."""
    for agent_class in [PlanningAgent, DesignAgent, CodeAgent, ...]:
        agent = agent_class()
        for prompt_file in agent.get_prompt_files():
            template_vars = agent.get_template_vars_for_prompt(prompt_file)
            prompt_content = agent.load_prompt(prompt_file)

            # Extract {variables} from prompt
            required_vars = extract_template_variables(prompt_content)

            # Ensure all required vars are provided
            assert set(required_vars) <= set(template_vars.keys()), \
                f"{prompt_file} requires {required_vars} but only {template_vars.keys()} provided"
```

## Attachments

- Full E2E test output log: `logs/e2e_test_20251121_003500.log`
- Error traceback: See "Error Message" section above
- Test environment details: Python 3.12.1, pytest 9.0.0, anthropic SDK

---

**Reporter:** Claude (ASP Development Assistant)
**Document Version:** 1.0
**Last Updated:** November 21, 2025 00:45 UTC
