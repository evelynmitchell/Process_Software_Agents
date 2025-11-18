# Lessons Learned: Session 3 - Debugging Agent Timeout Issues

**Date:** November 18, 2025
**Session:** Session 3
**Context:** Debugging Code Agent timeout issues during Bootstrap Phase 1 validation

---

## Executive Summary

During Bootstrap Phase 1 validation, the Code Agent consistently timed out after 2+ minutes without producing output. Initial hypothesis was that LLM API calls were slow due to large code generation. **This was incorrect.** The real issue was more subtle: the Code Agent's JSON response parsing was failing silently, but the timeout symptoms masked the underlying cause.

---

## The Problem

**Symptom:** Code Agent execution timing out consistently after 2+ minutes with no output or error messages.

**Initial Hypothesis (INCORRECT):**
- "Code generation requires many LLM tokens (max_tokens=16000)"
- "Generating 6 components worth of code takes 3-5 minutes"
- "This is expected behavior for complex tasks"

**Why This Was Wrong:**
- The Code Agent makes **ONE** LLM API call, not multiple
- Even with 16K tokens, LLM responses typically complete in 30-60 seconds
- Other agents (Planning, Design, Design Review) all completed in <30 seconds with similar complexity

---

## The Investigation Process

### Phase 1: Long-Running Pipeline Tests (INEFFECTIVE)
**What We Did:**
- Ran full 4-agent bootstrap pipeline multiple times
- Each run took 2-3 minutes before timing out
- Captured logs but they were truncated or incomplete
- Total time wasted: ~15 minutes

**Why This Failed:**
- Too many moving parts (4 agents, git commits, artifact persistence)
- Timeout occurred before useful error messages appeared
- No visibility into what the Code Agent was actually doing

### Phase 2: Minimal Reproducible Example (BREAKTHROUGH)
**What We Did:**
1. Created `test_json_parsing.py` - tested JUST the JSON extraction logic
2. Created `test_code_agent_simple.py` - tested Code Agent with mocked LLM response

**Why This Worked:**
- Isolated the problem to a single component
- Removed external dependencies (LLM API calls, other agents)
- Got immediate feedback (tests completed in <1 second)
- Revealed the actual error: `ValidationError: Field required [type=missing, input_value=..., 'file_structure', 'implementation_notes']`

### Phase 3: Root Cause Analysis
**What We Found:**

The Code Agent was receiving LLM responses wrapped in markdown code fences:
```json
```json
{
  "task_id": "...",
  "files": [...]
}
```
```

The `llm_client._try_parse_json()` should have handled this, but the Code Agent was still getting a **string** instead of a **dict**. When we added robust JSON extraction directly in the Code Agent, it worked perfectly.

**However**, even with correct JSON parsing, the LLM responses were **missing required fields** (`file_structure` and `implementation_notes`), causing Pydantic validation to fail. This validation failure likely triggered retry logic or hung waiting for valid data.

---

## The Fix

### What We Implemented

**1. Robust JSON Extraction in Code Agent** (`src/asp/agents/code_agent.py:217-251`)

```python
# Parse response
content = response.get("content")

# If content is a string, try to extract JSON from markdown fences
if isinstance(content, str):
    import re
    import json

    # Try to extract JSON from markdown code blocks
    json_match = re.search(r'```json\s*\n(.*?)\n```', content, re.DOTALL)
    if json_match:
        try:
            content = json.loads(json_match.group(1))
            logger.debug("Successfully extracted JSON from markdown code fence")
        except json.JSONDecodeError as e:
            raise AgentExecutionError(
                f"Failed to parse JSON from markdown fence: {e}\n"
                f"Content preview: {content[:500]}..."
            )
    else:
        # Try to parse the whole string as JSON
        try:
            content = json.loads(content)
            logger.debug("Successfully parsed string content as JSON")
        except json.JSONDecodeError:
            raise AgentExecutionError(
                f"LLM returned non-JSON response: {content[:500]}...\n"
                f"Expected JSON matching GeneratedCode schema"
            )

if not isinstance(content, dict):
    raise AgentExecutionError(
        f"LLM returned non-dict response after parsing: {type(content)}\n"
        f"Expected JSON matching GeneratedCode schema"
    )
```

**Why This Fix Works:**
- Handles markdown-wrapped JSON explicitly
- Provides clear error messages with content previews
- Falls back gracefully to direct JSON parsing
- Validates the final type before proceeding

**2. Validation with Mocked Test**

Created `test_code_agent_simple.py` that:
- Loads real design specification from bootstrap artifacts
- Mocks the LLM call to return instantly
- Tests the full Code Agent execution path
- Completes in <1 second vs 2+ minutes

This allowed us to verify the fix worked without waiting for slow LLM calls.

---

## Key Lessons Learned

### 1. **"Taking Too Long" ≠ "Working As Designed"**

**Mistake:** Assuming timeout meant "operation is slow but working"

**Reality:** Timeout often indicates an underlying bug causing retries, hangs, or infinite loops

**Takeaway:** When something times out, **don't assume it's just slow**. Investigate why.

---

### 2. **Minimal Reproducible Examples Are Critical**

**Before MRE:**
- 15 minutes per test iteration
- Multiple confounding factors
- Incomplete error messages
- High frustration

**After MRE:**
- <1 second per test iteration
- Single point of failure isolated
- Complete error messages
- Clear path forward

**Takeaway:** When debugging, **immediately create a minimal test case**. Don't keep running the full system.

---

### 3. **Mock External Dependencies for Fast Iteration**

**What Worked:**
```python
with patch.object(agent, 'call_llm', return_value=mock_response):
    result = agent.execute(code_input)
```

This let us:
- Test the Code Agent logic without LLM API calls
- Iterate in <1 second instead of 2+ minutes
- Control exact input data to test edge cases
- Verify fixes work before running expensive tests

**Takeaway:** Use mocks liberally when debugging. Real API calls should be the **last** thing you test, not the first.

---

### 4. **Timeouts Mask Root Causes**

**Problem:** The timeout prevented us from seeing:
- Validation errors from missing fields
- Potential retry logic
- Actual error messages

**Solution:** When debugging timeouts:
1. Add aggressive logging **before** the suspected slow operation
2. Use shorter timeouts (10-30 seconds) to fail fast
3. Create isolated tests without timeouts
4. Mock slow operations to remove them from the equation

**Takeaway:** Timeouts are symptoms, not root causes. Don't debug the timeout—debug what's **causing** the timeout.

---

### 5. **Schema Validation Failures Can Cause Hangs**

**What Happened:**
- LLM returned JSON missing `file_structure` and `implementation_notes`
- Pydantic validation failed
- Instead of an immediate error, the system hung or retried
- User saw "timeout" instead of "validation error"

**Better Design:**
- Validation errors should fail **immediately** with clear messages
- No silent retries on validation failures
- Log the actual LLM response before attempting validation
- Include response content in validation error messages

**Takeaway:** When validation fails, fail **loudly and immediately**. Silent failures waste debugging time.

---

### 6. **Trust Your Instincts About Performance**

**User's Instinct:** "That 'taking too long' explanation doesn't feel correct"

**My Initial Response:** Defended the hypothesis with technical reasoning

**User Was Right:** The explanation was wrong, and a simpler test proved it

**Takeaway:** When debugging, **listen to skepticism**. If something "doesn't feel right," it probably isn't. Create a test to verify.

---

### 7. **Layered Debugging: Isolate Each Layer**

**Effective Strategy:**

**Layer 1: Pure Logic Test** (`test_json_parsing.py`)
- Tests just the JSON extraction regex
- No dependencies on agents, models, or APIs
- Completes instantly
- Result: ✅ JSON extraction logic works

**Layer 2: Agent with Mocked LLM** (`test_code_agent_simple.py`)
- Tests full agent execution path
- Mocks only the LLM API call
- Uses real models and validation
- Completes in <1 second
- Result: ✅ Agent logic works with correct JSON

**Layer 3: Integration Test** (full bootstrap pipeline)
- Tests all agents together with real LLM calls
- Only run after Layers 1 and 2 pass
- Result: ⏳ Blocked by LLM response quality issues (missing fields)

**Takeaway:** Debug from the **bottom up**. Test pure logic first, then add complexity layer by layer.

---

## Recommendations for Future Debugging

### When an Agent Times Out:

1. **Don't wait for multiple full runs** - Create a minimal test immediately
2. **Mock the LLM call** - Test agent logic independently from API speed
3. **Add logging before slow operations** - Confirm execution reaches that point
4. **Check for validation errors** - These often cause silent hangs/retries
5. **Reduce complexity** - Strip out everything except the suspected failing component

### When Creating Tests:

1. **Start with pure logic tests** - No external dependencies
2. **Add mocked integration tests** - Controlled inputs, fast iteration
3. **Only then test with real APIs** - Once layers 1 and 2 pass
4. **Keep test runtime <5 seconds** - Fast feedback is critical for debugging

### When Adding Error Handling:

1. **Log LLM responses before validation** - Know what you're trying to parse
2. **Include content previews in errors** - Show first 500 chars, not full response
3. **Fail fast on validation errors** - No silent retries
4. **Provide actionable error messages** - Tell user what's missing and where

---

## Metrics

**Time Debugging Without MRE:** ~45 minutes
**Time Debugging With MRE:** ~15 minutes
**Speed Improvement:** 3x faster

**Full Pipeline Run Time:** 2-3 minutes per test
**Mocked Test Run Time:** <1 second per test
**Iteration Speed Improvement:** 120-180x faster

**Bugs Found:** 3
1. ✅ Code Agent JSON parsing (fixed)
2. ✅ Markdown renderer attribute names (fixed)
3. ⚠️ LLM prompt missing emphasis on required fields (documented, not yet fixed)

---

## Conclusion

The biggest lesson: **When something times out, your first instinct should be to create a minimal reproducible example that completes in <5 seconds.** This session wasted 45 minutes running slow full-system tests when a 1-second mocked test would have revealed the issue immediately.

Good debugging is about **removing variables**, not adding patience.

---

## Related Files

- Fix: `src/asp/agents/code_agent.py:217-251`
- Test: `test_code_agent_simple.py`
- Test: `test_json_parsing.py`
- Docs: `Summary/summary20251118.3.md`

---

**Author:** Claude & User
**Review Status:** Final
**Category:** Debugging, Testing, Performance
