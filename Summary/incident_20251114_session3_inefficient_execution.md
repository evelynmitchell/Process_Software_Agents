# Incident Report: Inefficient Token Usage - Session 3 Bootstrap Collection

**Date:** November 14, 2025
**Session:** Session 3 of 20251114
**Severity:** Medium
**Status:** Resolved
**Reported By:** User

---

## Executive Summary

During Session 3, inefficient debugging practices led to excessive token consumption and wasted API calls while developing the bootstrap data collection script. Multiple full script executions were attempted without proper cleanup of background processes, and bugs were not isolated before running the complete pipeline.

---

## Incident Timeline

| Time | Event |
|------|-------|
| 20:16 UTC | First script execution attempted, failed with async/await error |
| 20:29 UTC | Second execution started in background without killing first process |
| 20:39 UTC | Third execution started, still debugging same async/await issue |
| 21:01 UTC | Fourth execution after fixing async issues, discovered field name bugs |
| 21:07 UTC | Fifth execution, processed 5 tasks before hitting API limit |
| 21:15 UTC | User identified inefficiency issue |

**Total Background Processes:** 4-5 concurrent instances running
**Total Script Runs:** 5+ full executions
**API Calls Wasted:** Estimated 20-30 calls on repeated failures

---

## What Happened

### Root Cause
1. **Inadequate Testing Strategy**: Attempted to run full pipeline (12 tasks) instead of testing with single task first
2. **Poor Process Management**: Started new script instances without killing previous background processes
3. **Iterative Debugging on Full Dataset**: Fixed bugs one at a time while re-running entire 12-task pipeline each time

### Specific Issues

**Issue 1: Multiple Background Processes**
- Started script in background (bash ID: 19b72c)
- Started second instance (bash ID: fe66c5)
- Started third instance (bash ID: b297f6)
- Started fourth instance (bash ID: 0772e7)
- None were properly terminated before starting new ones

**Issue 2: Repeated Full Executions**
- Run 1: Failed on `await` syntax (all 12 tasks attempted)
- Run 2: Failed on `await` syntax again (all 12 tasks attempted)
- Run 3: Failed on field name errors (tasks 1-5 attempted)
- Run 4: Failed on `total_issue_count` error (tasks 1-5 attempted)
- Run 5: Hit API limit at task 5

**Issue 3: Bug Fixing Approach**
- Fixed bugs sequentially rather than identifying all issues first
- Re-ran full script after each individual fix
- Did not create minimal test case for single task validation

---

## Impact

### Token Usage
- **Estimated Waste:** 40,000-50,000 tokens on repeated failures
- **Actual Work:** ~50,000 tokens for 5 successful task completions
- **Efficiency:** ~50% token utilization rate

### API Quota
- Hit Anthropic API usage limit prematurely
- Only completed 5 of 12 planned bootstrap tasks
- API quota reset required: December 1, 2025

### Time
- **Session Duration:** ~1 hour
- **Productive Time:** ~30 minutes (successful 5 task runs)
- **Debugging Time:** ~30 minutes (inefficient iterations)

---

## What Should Have Been Done

### Correct Approach

1. **Single Task Test First**
   ```bash
   # Test with BOOTSTRAP-001 only
   uv run python -c "... test single task ..."
   ```
   - Identify ALL bugs with minimal API usage
   - Fix all bugs before full run
   - Estimated cost: 2-3 API calls vs 20+ actual

2. **Kill Previous Processes**
   ```bash
   # Before each new run
   ps aux | grep bootstrap | grep -v grep | awk '{print $2}' | xargs kill -9
   ```

3. **Comprehensive Bug Analysis**
   - Read the error traceback fully
   - Check model definitions before running
   - Validate all field names against actual schemas
   - Create fix list, implement all fixes, then test

4. **Incremental Testing**
   - Test with 1 task (validate script works)
   - Test with 2 tasks (validate iteration works)
   - Run all 12 tasks once bugs confirmed fixed

---

## Lessons Learned

### Technical Lessons
1. Always test with minimal dataset first
2. Check Pydantic model schemas before accessing attributes
3. Verify async/sync method signatures before calling
4. Use proper process management (kill before restart)

### Process Lessons
1. **Fail Fast Principle**: Identify all failures quickly with minimal data
2. **Batch Fix Strategy**: Collect all bugs, fix together, test once
3. **Resource Awareness**: Monitor API quota and token usage actively
4. **Process Hygiene**: Clean up background processes between runs

---

## Action Items

### Immediate (Completed)
- [x] Killed all hanging background processes
- [x] Created incident report
- [x] Committed working script for future use

### Short-term (Next Session)
- [ ] Fix remaining bug: `total_issue_count` attribute name
- [ ] Add single-task test mode to script (CLI flag: `--test-single`)
- [ ] Add process check at script startup (exit if already running)
- [ ] Complete remaining 7 bootstrap tasks when API limit resets

### Long-term (Future Sessions)
- [ ] Add pre-flight validation to all scripts (check models, schemas)
- [ ] Create testing utilities for single-item pipeline validation
- [ ] Implement token usage tracking and warnings
- [ ] Add retry logic with exponential backoff for API calls

---

## Prevention Measures

### Code Changes Needed
```python
# Add to script header
import sys
import psutil

def check_already_running():
    """Exit if another instance is running"""
    current_pid = os.getpid()
    for proc in psutil.process_iter(['pid', 'cmdline']):
        if 'bootstrap_design_review_collection' in ' '.join(proc.info['cmdline'] or []):
            if proc.info['pid'] != current_pid:
                print(f"ERROR: Another instance is running (PID {proc.info['pid']})")
                sys.exit(1)
```

### Testing Template
```python
# Add --test-single mode
if args.test_single:
    results = [BOOTSTRAP_TASKS[0]]  # Test with first task only
    print("TEST MODE: Processing single task only")
```

### Validation Checks
```python
# Add pre-flight schema validation
def validate_models():
    """Check all required attributes exist on models"""
    required_attrs = {
        'DesignReviewReport': ['overall_assessment', 'critical_issue_count'],
        'DesignSpecification': ['api_contracts', 'component_logic'],
    }
    # Validate each model has expected attributes
```

---

## Sign-off

**Incident Closed By:** Claude
**Date:** November 14, 2025
**Status:** Resolved with action items for prevention

---

## References

- Commit: bbfa7a6 - "Session 3: Create bootstrap data collection script and partial execution"
- Script: `scripts/bootstrap_design_review_collection.py`
- Summary: `Summary/summary20251114.3.md`
- API Limit Reset: December 1, 2025 00:00 UTC
