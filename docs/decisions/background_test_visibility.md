# ADR: Background Test Visibility and Monitoring

**Status:** Proposed
**Date:** November 21, 2025
**Decision Makers:** Development Team
**Related Issues:** Session 8 E2E test execution experience

## Context and Problem Statement

During Session 8 E2E test execution, we ran long-running tests (5-10 minutes) in background mode using the `Bash` tool with `run_in_background=True`. This created several visibility and usability issues:

### Problems Identified

1. **Silent Execution:** Tests ran with no visible progress indicators
2. **Unclear Status:** No way to know which agent was currently executing
3. **Hidden Failures:** Tests failed or hung without immediate notification
4. **Resource Waste:** Background processes continued running after being forgotten
5. **Poor User Experience:** User had to explicitly ask "what background processes?" to discover tests were still running
6. **Difficult Debugging:** When issues occurred, no incremental output was available for diagnosis

### Specific Incident (Session 8)

- **Started:** Two E2E test processes at ~00:25 UTC and ~00:30 UTC
- **Discovered:** ~00:45 UTC (15-20 minutes later) when user asked about background processes
- **Status:** One failed early (import error), one hung in infinite loop for 10+ minutes
- **Impact:** Wasted 10+ minutes of wall-clock time, delayed bug discovery

### User Quote

> "how can we make these background tests more obvious?"

This indicates the current approach fails to meet user expectations for visibility and control.

## Decision Drivers

### Must Have
1. **Real-time visibility** - User must know tests are running
2. **Progress indication** - User must see which phase/agent is executing
3. **Failure notification** - User must be notified immediately when tests fail
4. **Resource awareness** - User must know about background processes consuming resources

### Should Have
5. **Cost visibility** - Show LLM API costs as tests run
6. **Time estimates** - Indicate expected remaining duration
7. **Cancellation ability** - Easy way to stop long-running tests
8. **Incremental output** - Show key milestones without overwhelming with logs

### Nice to Have
9. **Progress bars** - Visual indication of completion percentage
10. **Historical comparison** - "This test usually takes 7 minutes"
11. **Parallel test tracking** - When running multiple test suites simultaneously

## Constraints

1. **Tool Limitations:** Claude Code Bash tool doesn't support interactive progress bars
2. **Token Budget:** Excessive polling/updates consume conversation tokens
3. **LLM Response Time:** Can't update more frequently than LLM response latency
4. **pytest Output:** Standard pytest output is verbose and not user-friendly

## Options Considered

### Option 1: Don't Use Background Mode (Recommended for Critical Tests)

**Description:** Run E2E tests in foreground with normal output, use high timeout.

**Implementation:**
```python
# Instead of background=True with polling
Bash(
    command="uv run pytest tests/e2e/test_all_agents_hello_world_e2e.py -v -s",
    description="Run E2E test suite",
    timeout=600000  # 10 minutes
)
# Output shows in real-time, blocking until complete
```

**Pros:**
- ✅ Immediate visibility - user sees output as it happens
- ✅ No polling required - single tool call
- ✅ Clear completion - tool returns when done
- ✅ Full output available - complete logs in response
- ✅ Simplest implementation - no additional code

**Cons:**
- ❌ Blocks conversation - user can't do other things during test
- ❌ Large output - may consume significant tokens
- ❌ No parallel work - can't run multiple tasks simultaneously

**Best For:** Critical tests where results are needed before proceeding (E2E validation, release tests)

**Estimated Effort:** 0 hours (already supported)

---

### Option 2: Background with TodoList Tracking (Recommended for Visibility)

**Description:** Use TodoList to track background test progress with periodic updates.

**Implementation:**
```python
# 1. Start test in background
bash_id = Bash(
    command="uv run pytest tests/e2e/test_all_agents_hello_world_e2e.py -v -s",
    run_in_background=True,
    timeout=600000
)

# 2. Add to todo list
TodoWrite([
    {"content": f"E2E tests running (shell {bash_id})", "status": "in_progress",
     "activeForm": "Running E2E test suite"},
    {"content": "Planning Agent phase", "status": "pending", "activeForm": "Running Planning Agent"},
    {"content": "Design Agent phase", "status": "pending", "activeForm": "Running Design Agent"},
    {"content": "Code Agent phase", "status": "pending", "activeForm": "Running Code Agent"},
])

# 3. Poll periodically (every 30-60 seconds) and update todos
while True:
    output = BashOutput(bash_id=bash_id)

    if output.status != "running":
        TodoWrite([mark_completed_or_failed(...)])
        break

    # Parse output and update todo statuses
    if "Planning Agent" in output.stdout:
        update_todo("Planning Agent phase", "in_progress")
    elif "Design Agent" in output.stdout:
        update_todo("Planning Agent phase", "completed")
        update_todo("Design Agent phase", "in_progress")
    # ... etc

    time.sleep(30)  # Check every 30 seconds
```

**Pros:**
- ✅ Visible in todo list - user always knows tests are running
- ✅ Progress tracking - shows which phase is active
- ✅ Non-blocking - user can do other things
- ✅ Periodic updates - balance between visibility and token usage
- ✅ Completion notification - todo marked complete/failed

**Cons:**
- ❌ Requires polling loop - more complex code
- ❌ Token overhead - each poll consumes tokens
- ❌ Update lag - 30-60 second delay between status changes
- ❌ Manual parsing - need to extract progress from logs

**Best For:** Long-running tests where user wants to do other work in parallel

**Estimated Effort:** 2-3 hours (implement polling loop, log parsing, todo management)

---

### Option 3: Structured Progress Callbacks in Agent Code

**Description:** Modify agent base class to emit structured progress events that can be captured and displayed.

**Implementation:**
```python
# Agent code changes
class BaseAgent:
    def __init__(self):
        self.progress_callback = None

    def emit_progress(self, phase: str, percent: int, message: str):
        """Emit progress event."""
        if self.progress_callback:
            self.progress_callback({
                "agent": self.__class__.__name__,
                "phase": phase,
                "percent": percent,
                "message": message,
                "timestamp": datetime.utcnow()
            })

    def execute(self, ...):
        self.emit_progress("initialization", 0, "Starting execution")
        # ... do work ...
        self.emit_progress("llm_call", 30, "Calling LLM")
        # ... more work ...
        self.emit_progress("complete", 100, "Execution complete")

# Test runner code
def progress_handler(event):
    """Handle progress events from agents."""
    print(f"[{event['agent']}] {event['phase']}: {event['message']} ({event['percent']}%)")

    # Could also write to file, update todo list, etc.
    with open('test_progress.json', 'a') as f:
        json.dump(event, f)
        f.write('\n')

# Use in tests
agent.progress_callback = progress_handler
agent.execute(...)
```

**Pros:**
- ✅ Fine-grained progress - know exactly what agent is doing
- ✅ Structured data - easy to parse and display
- ✅ Reusable - works for all agents automatically
- ✅ No polling - event-driven, real-time updates
- ✅ Extensible - can add more detailed events over time

**Cons:**
- ❌ Code changes required - modify all agent classes
- ❌ Not available in Claude Code - requires custom integration
- ❌ Test infrastructure changes - need progress handler setup
- ❌ Backward compatibility - need to support agents without callbacks

**Best For:** Long-term solution for production monitoring and observability

**Estimated Effort:** 6-8 hours (implement callbacks, update all agents, add test harness)

---

### Option 4: Pytest Plugin with Live Updates

**Description:** Create pytest plugin that emits structured events during test execution.

**Implementation:**
```python
# conftest.py
import pytest

class ProgressPlugin:
    """Pytest plugin for emitting progress events."""

    def __init__(self):
        self.current_phase = None

    @pytest.hookimpl(hookwrapper=True)
    def pytest_runtest_protocol(self, item, nextitem):
        """Called for each test item."""
        print(f"🧪 Starting test: {item.name}")
        yield
        print(f"✅ Completed test: {item.name}")

    @pytest.hookimpl(hookwrapper=True)
    def pytest_runtest_call(self, item):
        """Called when running test body."""
        # Extract phase from test name/markers
        if "planning" in item.name.lower():
            print("📋 Planning Agent phase")
        elif "design" in item.name.lower():
            print("🎨 Design Agent phase")
        # ... etc

        yield

def pytest_configure(config):
    """Register plugin."""
    config.pluginmanager.register(ProgressPlugin(), "progress")

# Run with plugin
# pytest tests/e2e/... (plugin auto-loads from conftest.py)
```

**Pros:**
- ✅ Pytest integration - works with existing test infrastructure
- ✅ Automatic progress - no changes to agent code
- ✅ Reusable - works for all tests
- ✅ Standard approach - follows pytest best practices

**Cons:**
- ❌ Limited granularity - only test-level events, not agent-level
- ❌ Still requires parsing - need to extract meaningful info from test names
- ❌ No sub-test progress - can't show LLM call progress within test
- ❌ Plugin complexity - pytest plugin API has learning curve

**Best For:** Medium-term solution for test-level visibility

**Estimated Effort:** 4-6 hours (implement plugin, test, document)

---

### Option 5: Test Orchestration Script with Monitoring

**Description:** Create dedicated script that runs tests and provides structured progress output.

**Implementation:**
```python
#!/usr/bin/env python3
"""
E2E test runner with progress monitoring.

Usage:
    python scripts/run_e2e_tests.py --monitor
"""

import subprocess
import re
import time
from datetime import datetime

class TestMonitor:
    """Monitor E2E test execution and display progress."""

    PHASE_PATTERNS = {
        'planning': r'INFO:.*planning_agent.*executing',
        'design': r'INFO:.*design_agent.*executing',
        'code': r'INFO:.*code_agent.*executing',
        'review': r'INFO:.*review.*executing',
        'test': r'INFO:.*test_agent.*executing',
        'postmortem': r'INFO:.*postmortem_agent.*executing',
    }

    def __init__(self):
        self.current_phase = None
        self.phase_start = None
        self.costs = []

    def parse_line(self, line: str):
        """Parse log line and extract progress info."""
        # Detect phase changes
        for phase, pattern in self.PHASE_PATTERNS.items():
            if re.search(pattern, line):
                self._phase_changed(phase)

        # Extract costs
        if 'cost=$' in line:
            match = re.search(r'cost=\$([0-9.]+)', line)
            if match:
                self.costs.append(float(match.group(1)))
                self._display_cost_update()

    def _phase_changed(self, new_phase: str):
        """Handle phase transition."""
        if self.current_phase:
            duration = time.time() - self.phase_start
            print(f"✅ {self.current_phase.capitalize()} complete ({duration:.1f}s)")

        self.current_phase = new_phase
        self.phase_start = time.time()
        print(f"🔄 Starting {new_phase.capitalize()} phase...")

    def _display_cost_update(self):
        """Display cumulative cost."""
        total = sum(self.costs)
        print(f"💰 Cost so far: ${total:.4f}")

    def run_tests(self):
        """Run tests with monitoring."""
        print("🚀 Starting E2E tests...")
        print(f"⏰ Started at {datetime.now().strftime('%H:%M:%S')}")
        print()

        process = subprocess.Popen(
            ['uv', 'run', 'pytest', 'tests/e2e/test_all_agents_hello_world_e2e.py', '-v', '-s'],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )

        # Process output line by line
        for line in iter(process.stdout.readline, ''):
            if line:
                self.parse_line(line)

                # Also save to log file
                with open('e2e_test_output.log', 'a') as f:
                    f.write(line)

        process.wait()

        print()
        print(f"🏁 Tests {'PASSED' if process.returncode == 0 else 'FAILED'}")
        print(f"💰 Total cost: ${sum(self.costs):.4f}")
        print(f"⏰ Completed at {datetime.now().strftime('%H:%M:%S')}")

        return process.returncode

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--monitor', action='store_true', help='Enable progress monitoring')
    args = parser.parse_args()

    if args.monitor:
        monitor = TestMonitor()
        exit_code = monitor.run_tests()
    else:
        # Standard pytest run
        exit_code = subprocess.call(['pytest', 'tests/e2e/...', '-v'])

    exit(exit_code)
```

**Usage:**
```bash
# Run with monitoring
python scripts/run_e2e_tests.py --monitor

# Output:
# 🚀 Starting E2E tests...
# ⏰ Started at 14:23:15
#
# 🔄 Starting Planning phase...
# 💰 Cost so far: $0.0132
# ✅ Planning complete (12.3s)
# 🔄 Starting Design phase...
# 💰 Cost so far: $0.0710
# ✅ Design complete (28.7s)
# ...
# 🏁 Tests PASSED
# 💰 Total cost: $0.2145
# ⏰ Completed at 14:28:42
```

**Pros:**
- ✅ Excellent visibility - clear, real-time progress updates
- ✅ Cost tracking - shows cumulative LLM costs
- ✅ Timing info - shows duration of each phase
- ✅ Log preservation - saves full output to file
- ✅ No agent changes - works with existing code
- ✅ Standalone tool - can be used independently

**Cons:**
- ❌ Requires script execution - not integrated into Claude Code
- ❌ Pattern matching - brittle, depends on log format
- ❌ External dependency - user must run separate script

**Best For:** Development/CI environments where tests run frequently

**Estimated Effort:** 3-4 hours (implement script, test, document)

---

### Option 6: Hybrid Approach (Quick + Long-term)

**Description:** Combine multiple options for immediate improvement and long-term solution.

**Phase 1 (Immediate - 0 hours):**
- Use Option 1 (foreground) for critical E2E tests
- Document when background mode is appropriate

**Phase 2 (Short-term - 2-3 hours):**
- Implement Option 2 (TodoList tracking) for background tests
- Add polling logic with 30-second intervals
- Parse logs for phase detection

**Phase 3 (Medium-term - 4-6 hours):**
- Implement Option 5 (orchestration script) for local development
- Integrate with CI/CD pipelines

**Phase 4 (Long-term - 6-8 hours):**
- Implement Option 3 (agent callbacks) for fine-grained progress
- Add telemetry integration for production monitoring

**Pros:**
- ✅ Immediate improvement - fix current pain points now
- ✅ Incremental investment - spread effort over time
- ✅ Best of both worlds - simple + sophisticated
- ✅ Risk mitigation - can stop after any phase if good enough

**Cons:**
- ❌ Ongoing work - not a single fix
- ❌ Maintenance burden - multiple solutions to maintain
- ❌ Potential inconsistency - different approaches in different contexts

**Best For:** Organizations with ongoing development and improvement cycles

**Estimated Total Effort:** 12-17 hours (spread over multiple sprints)

---

## Decision Matrix

| Criteria | Opt 1: Foreground | Opt 2: TodoList | Opt 3: Callbacks | Opt 4: Plugin | Opt 5: Script | Opt 6: Hybrid |
|----------|-------------------|-----------------|------------------|---------------|---------------|---------------|
| **Immediate Visibility** | ⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ |
| **Progress Detail** | ⭐ | ⭐⭐ | ⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ |
| **Non-blocking** | ❌ | ⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ |
| **Implementation Cost** | ⭐⭐⭐ | ⭐⭐ | ❌ | ⭐ | ⭐⭐ | ⭐ |
| **Token Efficiency** | ⭐ | ⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐ |
| **Reusability** | ⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ |
| **Maintenance** | ⭐⭐⭐ | ⭐⭐ | ⭐ | ⭐⭐ | ⭐⭐ | ⭐ |
| **CI/CD Integration** | ⭐⭐⭐ | ⭐ | ⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ |
| **User Experience** | ⭐⭐ | ⭐⭐ | ⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ |

**Legend:** ⭐⭐⭐ Excellent, ⭐⭐ Good, ⭐ Fair, ❌ Poor

---

## Recommended Decision

### Primary Recommendation: **Option 6 (Hybrid Approach)**

**Rationale:**
- Provides immediate relief (Phase 1) with zero implementation cost
- Delivers short-term improvements (Phase 2) within one sprint
- Builds toward long-term excellence (Phases 3-4) incrementally
- Allows learning and adjustment at each phase
- Balances investment with value delivery

### Implementation Plan

**Phase 1: Immediate (This Week)**

**Action:** Update test execution guidelines
```markdown
# When to Use Background vs Foreground Tests

## Use Foreground (Blocking)
- ✅ E2E tests where results needed immediately
- ✅ Critical validation tests
- ✅ Pre-commit/pre-merge tests
- ✅ Tests with <2 minute duration
- ✅ Any test where user waits for results

## Use Background (Non-blocking)
- ✅ Long-running performance tests
- ✅ Exploratory testing during development
- ✅ Tests running in parallel with other work
- ✅ MUST use TodoList tracking (see below)

## Background Test Protocol
When using background mode:
1. Add to TodoList immediately after starting
2. Include shell ID in todo item
3. Check progress every 30-60 seconds
4. Update user with meaningful milestones
5. Mark complete/failed when done
```

**Phase 2: Short-term (Next Sprint)**

**Deliverables:**
1. `utils/test_monitor.py` - Background test monitoring utility
2. Updated documentation with examples
3. Integration tests for monitor

**Code:**
```python
# utils/test_monitor.py
class BackgroundTestMonitor:
    """Monitor background test execution with TodoList integration."""

    def start_test(self, command: str, description: str) -> str:
        """Start background test and add to todo list."""
        ...

    def poll_progress(self, shell_id: str) -> dict:
        """Check test progress and update todos."""
        ...

    def wait_for_completion(self, shell_id: str, check_interval: int = 30):
        """Block until test completes, updating todos periodically."""
        ...
```

**Phase 3: Medium-term (Month 2)**

**Deliverables:**
1. `scripts/run_e2e_tests.py` - Test orchestration script
2. CI/CD integration (GitHub Actions)
3. Documentation and examples

**Phase 4: Long-term (Month 3-4)**

**Deliverables:**
1. Agent progress callback system
2. Telemetry integration (Langfuse)
3. Real-time dashboard (optional)

---

## Alternative Recommendation: **Option 1 (Foreground) + Option 5 (Script)**

**If we want a simpler approach:**

1. **Use foreground mode in Claude Code** - Always visible, always clear
2. **Use orchestration script for CLI/CI** - Better experience when not using Claude Code

**Rationale:**
- Simpler to implement (3-4 hours total)
- Covers both use cases well
- Less maintenance burden
- Easier to understand and use

---

## Consequences

### If We Choose Option 6 (Hybrid - Recommended)

**Positive:**
- ✅ Immediate improvement to user experience
- ✅ Incremental investment spreads cost over time
- ✅ Flexibility to adjust based on feedback
- ✅ Best long-term outcome

**Negative:**
- ❌ Ongoing maintenance of multiple approaches
- ❌ Need to document when to use which approach
- ❌ Some code duplication between approaches

**Mitigation:**
- Create clear decision tree for when to use each approach
- Consolidate common code into shared utilities
- Sunset older approaches as newer ones prove better

### If We Choose Option 1 (Foreground Only)

**Positive:**
- ✅ Zero implementation cost
- ✅ Maximum simplicity
- ✅ Always visible

**Negative:**
- ❌ No parallel work possible
- ❌ User must wait for long tests
- ❌ Large output consumes tokens

**Mitigation:**
- Run long tests outside Claude Code sessions
- Use test orchestration script for local development

---

## Open Questions

1. **Token Budget:** How many tokens per session are we comfortable spending on progress updates?
   - Proposed: 1-2% of token budget for monitoring (2,000-4,000 tokens per session)

2. **Update Frequency:** How often should we poll background tests?
   - Proposed: 30 seconds (balance between responsiveness and overhead)

3. **Notification Preference:** Should we interrupt with updates or wait for user to ask?
   - Proposed: Proactive updates at major milestones (phase changes, failures)

4. **Failure Handling:** What should happen when background test fails?
   - Proposed: Immediate notification, mark todo as failed, preserve logs

5. **Multiple Tests:** How to handle multiple background tests simultaneously?
   - Proposed: Separate todo items, shared poll loop, consolidated updates

---

## Success Metrics

### Phase 1 Success
- [ ] Zero incidents of "forgotten" background tests
- [ ] User never asks "what background processes?"
- [ ] All tests use appropriate mode (foreground vs background)

### Phase 2 Success
- [ ] Background tests visible in todo list
- [ ] Progress updates every 30-60 seconds
- [ ] Immediate notification of failures
- [ ] 90%+ user satisfaction with visibility

### Phase 3 Success
- [ ] Orchestration script used in CI/CD
- [ ] Clear progress output in all environments
- [ ] <5% overhead from monitoring
- [ ] Detailed logs available for debugging

### Phase 4 Success
- [ ] Real-time progress at agent level
- [ ] <1% overhead from callbacks
- [ ] Integrated telemetry dashboard
- [ ] Reusable across all agent types

---

## References

### Related Documents
- Session 8 summary: `Summary/summary20251120.8.md`
- E2E test issue: `docs/issues/e2e_test_feedback_loop_bug.md`
- Test architecture: `tests/e2e/README.md` (if exists)

### External Resources
- Pytest plugin development: https://docs.pytest.org/en/stable/how-to/writing_plugins.html
- Subprocess progress monitoring: https://docs.python.org/3/library/subprocess.html#subprocess.Popen
- Claude Code Bash tool: Claude Code documentation

### Prior Art
- GitHub Actions progress display
- pytest-xdist parallel execution output
- Jenkins build progress indicators
- Langfuse real-time telemetry

---

## Decision

**Status:** 🟡 Proposed (Awaiting approval)

**Recommended:** Option 6 (Hybrid Approach)

**Next Steps:**
1. Review this ADR with team
2. Get approval for recommended approach
3. Create implementation tickets for Phase 1-2
4. Schedule implementation in next sprint
5. Update test execution guidelines immediately (Phase 1)

**Decision Date:** TBD
**Approved By:** TBD
**Implementation Start:** TBD

---

**Author:** Claude (ASP Development Assistant)
**Date Created:** November 21, 2025
**Last Updated:** November 21, 2025
**Version:** 1.0
