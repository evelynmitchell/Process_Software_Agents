# Detailed User Stories: Day-to-Day Workflows with ASP

This document describes how each role uses the Agentic Software Process (ASP) platform to accomplish their daily tasks. For each workflow, we document the **trigger**, **inputs**, **actions**, **outputs**, and **decisions** that result.

---

## Table of Contents

1. [Developer Workflows (Alex)](#developer-workflows-alex)
2. [Engineering Manager Workflows (Sarah)](#engineering-manager-workflows-sarah)
3. [Product Manager Workflows (Jordan)](#product-manager-workflows-jordan)
4. [Cross-Role Interactions](#cross-role-interactions)
5. [Inputs and Outputs Reference](#inputs-and-outputs-reference)

---

## Developer Workflows (Alex)

### Workflow D1: Starting a New Feature

**Trigger:** PM assigns a feature ticket with requirements.

**Inputs:**
- Feature requirements document (from PM)
- Acceptance criteria
- Context: related files, APIs, database schemas
- Constraints (time budget, cost budget, security requirements)

**Actions in ASP:**
1. Open Flow State Canvas → "New Task"
2. Paste or link requirements document
3. Select context files from project tree (or let Planning Agent suggest)
4. Set parameters:
   - Complexity budget (estimated tokens/cost)
   - Quality gates (must pass security review: yes/no)
   - Human review checkpoints (after design? after code?)
5. Click "Start Planning Phase"

**System Process:**
1. **Planning Agent** analyzes requirements
2. Planning Agent asks clarifying questions (displayed as cards)
3. Developer answers questions inline
4. Planning Agent produces: Task Plan artifact
5. **Design Agent** creates: Design Specification artifact
6. Design Review runs automatically
7. Artifacts linked with traceability arrows

**Outputs:**
| Artifact | Format | Contains |
|----------|--------|----------|
| Task Plan | Markdown | Goals, approach, subtasks, risks |
| Design Spec | Markdown | API contracts, data models, sequence diagrams |
| Review Report | Markdown | Design issues found, severity, recommendations |

**Decisions:**
- Approve design and proceed to code generation?
- Request design revision based on review feedback?
- Escalate blockers to PM (scope unclear)?

---

### Workflow D2: Generating Code from Approved Design

**Trigger:** Design approved, ready for implementation.

**Inputs:**
- Approved Design Specification
- Code style guide (from repo config)
- Existing codebase context
- Test coverage requirements

**Actions in ASP:**
1. From approved Design card, click "Generate Implementation"
2. Code Agent status appears: "Generating..."
3. Live preview shows code being written (streaming)
4. Code blocks appear as canvas cards linked to design sections
5. Developer can annotate: "Prefer using dependency injection here"

**System Process:**
1. **Code Agent** generates implementation files
2. Files automatically staged for review
3. **Code Review Agent** runs:
   - Style checks
   - Security scan (OWASP patterns)
   - Performance analysis
4. Review comments appear on code cards

**Outputs:**
| Artifact | Format | Contains |
|----------|--------|----------|
| Implementation Code | Python/JS/etc. | Generated source files |
| Code Review Report | Markdown | Issues, line references, severity |
| Diff Preview | Unified diff | Changes vs. existing code |

**Decisions:**
- Accept code as-is?
- Request specific changes (via chat with Code Agent)?
- Reject and regenerate with different parameters?

---

### Workflow D3: Generating Tests

**Trigger:** Code implementation complete, needs test coverage.

**Inputs:**
- Implementation code (from D2)
- Test framework config (pytest, jest, etc.)
- Coverage targets (e.g., 80% line coverage)
- Edge case hints (optional, from developer)

**Actions in ASP:**
1. Select code cards on canvas
2. Right-click → "Generate Tests"
3. Test Agent dialog:
   - Test types: Unit / Integration / E2E
   - Coverage target: 80%
   - Include edge cases: Yes
   - Mocking strategy: Auto / Manual
4. Click "Generate"

**System Process:**
1. **Test Agent** analyzes code structure
2. Identifies public interfaces, edge cases, error paths
3. Generates test files with fixtures
4. Runs tests locally (if environment configured)
5. Reports coverage metrics

**Outputs:**
| Artifact | Format | Contains |
|----------|--------|----------|
| Test Files | Python/JS | Unit tests, integration tests |
| Coverage Report | HTML/JSON | Line coverage, branch coverage |
| Test Results | JSON | Pass/fail, duration, failures |

**Decisions:**
- Sufficient coverage achieved?
- Add manual tests for complex scenarios?
- Fix code based on test failures?

---

### Workflow D4: Debugging a Test Failure

**Trigger:** CI pipeline reports test failure, or local test fails.

**Inputs:**
- Test failure output (stack trace, assertion error)
- Test file and line number
- Code under test
- Recent commits (for regression debugging)

**Actions in ASP:**
1. Click alert notification → Opens failure card
2. Failure card shows:
   - Stack trace
   - Relevant code snippets
   - Git diff since last passing build
3. Click "Analyze Failure"
4. Postmortem Agent suggests:
   - Root cause hypothesis
   - Suggested fix locations
   - Similar past failures

**System Process:**
1. **Postmortem Agent** correlates:
   - Error message patterns
   - Recent code changes
   - Historical failure database
2. Produces root cause analysis
3. Optionally generates fix patch

**Outputs:**
| Artifact | Format | Contains |
|----------|--------|----------|
| Failure Analysis | Markdown | Root cause, evidence, confidence |
| Suggested Fix | Diff | Proposed code change |
| Related Issues | List | Links to similar past failures |

**Decisions:**
- Apply suggested fix?
- Investigate further manually?
- Mark as known issue / flaky test?

---

### Workflow D5: Code Review (Reviewing Others' Code)

**Trigger:** PR assigned for review.

**Inputs:**
- Pull request diff
- PR description and linked ticket
- Author's design rationale
- Existing review comments

**Actions in ASP:**
1. Open PR link → Flow State Canvas loads PR context
2. Canvas shows:
   - Original requirements (linked)
   - Design spec (linked)
   - Code diff as cards
   - AI pre-review comments
3. Click "Run Deep Review" for detailed analysis
4. Add human comments alongside AI comments
5. Request changes or approve

**System Process:**
1. **Design Review Agent** checks:
   - Does code match design?
   - Are there architectural concerns?
2. **Code Review Agent** checks:
   - Security vulnerabilities
   - Performance issues
   - Style violations
3. Results merged into single review view

**Outputs:**
| Artifact | Format | Contains |
|----------|--------|----------|
| Review Summary | Markdown | Issues by category and severity |
| Line Comments | JSON | Comment text, line ref, type |
| Approval Status | Enum | Approved / Changes Requested / Blocked |

**Decisions:**
- Approve PR?
- Request specific changes?
- Block for security review?

---

### Workflow D6: Refactoring Existing Code

**Trigger:** Tech debt ticket, or opportunity spotted during feature work.

**Inputs:**
- Code to refactor (file or module selection)
- Refactoring goal (e.g., "extract to service", "improve testability")
- Constraints (preserve API? preserve behavior?)
- Test coverage of existing code

**Actions in ASP:**
1. Select files on canvas
2. Right-click → "Refactor..."
3. Refactoring dialog:
   - Goal description (free text)
   - Pattern to apply (Strategy, Extract Method, etc.)
   - Preserve backward compatibility: Yes/No
4. Preview refactoring plan before execution

**System Process:**
1. **Planning Agent** creates refactoring plan
2. **Code Agent** generates refactored code
3. **Test Agent** runs existing tests
4. Diff shows all changes
5. Coverage comparison shows before/after

**Outputs:**
| Artifact | Format | Contains |
|----------|--------|----------|
| Refactoring Plan | Markdown | Steps, risks, rollback strategy |
| Refactored Code | Source files | New implementation |
| Test Results | JSON | Verify behavior preserved |
| Coverage Delta | Report | Coverage change |

**Decisions:**
- Accept refactoring?
- Apply partially (some files)?
- Abandon if tests fail?

---

### Workflow D7: Security Vulnerability Fix

**Trigger:** Security scan alert, or CVE notification.

**Inputs:**
- Vulnerability report (CVE ID, severity)
- Affected code locations
- Remediation guidance (from scanner or advisory)
- Current dependencies/versions

**Actions in ASP:**
1. Security alert card appears in dashboard
2. Click to expand: shows affected files, severity, CVSS score
3. Click "Generate Fix"
4. Review proposed changes:
   - Dependency updates
   - Code patches
   - Configuration changes
5. Click "Apply and Test"

**System Process:**
1. **Code Agent** generates security fix
2. **Security Review** validates fix effectiveness
3. **Test Agent** runs security-focused tests
4. Regression tests confirm no breakage

**Outputs:**
| Artifact | Format | Contains |
|----------|--------|----------|
| Security Fix | Diff | Patched code/dependencies |
| Verification Report | Markdown | Fix confirmed, no new vulns |
| Test Results | JSON | Pass/fail, security test results |

**Decisions:**
- Deploy fix immediately (critical)?
- Schedule for next release?
- Request manual security review?

---

## Engineering Manager Workflows (Sarah)

### Workflow M1: Morning Health Check

**Trigger:** Start of workday.

**Inputs:**
- Overnight telemetry data
- Active tasks status
- Alert notifications
- Team schedule/capacity

**Actions in ASP Overwatch:**
1. Open Overwatch dashboard
2. Review "Global Health" panel:
   - Success rate (target: >95%)
   - Active tasks count
   - Average execution time
3. Check "Critical Alerts" section:
   - Security review failures
   - Budget overspend warnings
   - Agent errors
4. Click each alert for details

**System Process:**
1. Dashboard aggregates overnight activity
2. Anomaly detection flags unusual patterns
3. Postmortem Agent pre-analyzes any failures

**Outputs:**
| View | Contains |
|------|----------|
| Health Summary | Uptime, success rate, active count |
| Alert List | Critical/Warning/Info categorized |
| Agent Status | Per-agent health (7 agents) |
| Cost Summary | Yesterday's spend, MTD total |

**Decisions:**
- Escalate critical issues to team?
- Adjust priorities based on overnight results?
- Schedule deep-dive for concerning trends?

---

### Workflow M2: Sprint Planning Review

**Trigger:** Sprint planning meeting preparation.

**Inputs:**
- Proposed sprint backlog
- Team capacity (available hours)
- Historical velocity data
- PROBE-AI estimates for each item

**Actions in ASP Overwatch:**
1. Navigate to "Planning" view
2. Import proposed tickets from backlog
3. Review AI estimates per ticket:
   - Agent time estimate
   - Human review time estimate
   - Cost estimate
   - Risk level
4. Compare total against capacity
5. Adjust sprint scope if overcommitted

**System Process:**
1. **PROBE-AI** analyzes each ticket:
   - Historical similar tasks
   - Complexity factors
   - Dependency analysis
2. Produces confidence intervals
3. Flags high-risk items

**Outputs:**
| Artifact | Format | Contains |
|----------|--------|----------|
| Sprint Estimate | Summary | Total hours, cost, risk breakdown |
| Per-Ticket Analysis | Table | Each item with estimate and confidence |
| Risk Report | Markdown | High-risk items, mitigation suggestions |
| Capacity Comparison | Chart | Proposed vs. available |

**Decisions:**
- Approve sprint scope?
- Move items to next sprint?
- Split large items?
- Add buffer for risk?

---

### Workflow M3: Quality Gate Review

**Trigger:** Weekly quality review, or before release.

**Inputs:**
- Phase yield data (per-phase pass rates)
- Defect data (by category, severity)
- Code review statistics
- Test coverage metrics

**Actions in ASP Overwatch:**
1. Navigate to "Quality Gates" panel
2. Review phase-by-phase metrics:
   - Planning → Design conversion rate
   - Design → Code approval rate
   - Code → Test pass rate
3. Drill into defect categories:
   - Security defects
   - Logic errors
   - Performance issues
4. Compare against SLOs

**System Process:**
1. Telemetry aggregates all artifact transitions
2. Calculates yield (what % passes each gate)
3. Pareto analysis shows top defect sources
4. **Postmortem Agent** suggests improvements

**Outputs:**
| View | Contains |
|------|----------|
| Phase Yield Chart | Sankey diagram of flow |
| Defect Pareto | Top defect categories |
| SLO Comparison | Target vs. actual per metric |
| Recommendations | AI-suggested improvements |

**Decisions:**
- Accept quality level for release?
- Block release until issues resolved?
- Adjust agent configurations (prompts, temperature)?
- Assign team to fix systematic issues?

---

### Workflow M4: Budget Management

**Trigger:** Monthly budget review, or cost alert.

**Inputs:**
- Cost telemetry (per task, per agent)
- Budget allocation
- ROI metrics (time saved vs. cost)

**Actions in ASP Overwatch:**
1. Navigate to "Cost Control" panel
2. Review current spend:
   - MTD total
   - Per-squad breakdown
   - Per-agent breakdown
3. Check cost efficiency:
   - Cost per successful task
   - Cost per line of code
   - Cost vs. manual baseline
4. Set or adjust budget caps

**System Process:**
1. Cost aggregation from Langfuse telemetry
2. Token usage analysis per agent
3. ROI calculation against baseline estimates

**Outputs:**
| View | Contains |
|------|----------|
| Cost Summary | MTD, projected, vs. budget |
| Cost Breakdown | By squad, agent, task type |
| Efficiency Metrics | $/task, $/line, $/feature |
| Alert Thresholds | Current caps, triggered alerts |

**Decisions:**
- Increase/decrease budget allocation?
- Optimize expensive workflows?
- Disable non-essential agents?
- Report ROI to leadership?

---

### Workflow M5: Incident Response

**Trigger:** Production incident, or agent failure cascade.

**Inputs:**
- Incident alert (severity, affected systems)
- Recent deployments
- Agent activity logs
- Related code changes

**Actions in ASP Overwatch:**
1. Click incident alert → Incident Card opens
2. Review incident timeline:
   - When did it start?
   - What changed before it?
   - Which agents were involved?
3. Click "Trace Root Cause"
4. Review linked artifacts:
   - Original task → Design → Code → Tests
5. Click "Generate Postmortem"

**System Process:**
1. **Postmortem Agent** analyzes:
   - Code changes timeline
   - Agent decision logs
   - Test results history
2. Correlates with known failure patterns
3. Generates root cause analysis
4. Suggests preventive measures

**Outputs:**
| Artifact | Format | Contains |
|----------|--------|----------|
| Incident Timeline | Visual | Events leading to incident |
| Root Cause Analysis | Markdown | What, why, contributing factors |
| Remediation Plan | Checklist | Steps to fix and prevent |
| Process Improvements | Recommendations | Changes to prevent recurrence |

**Decisions:**
- Immediate mitigation action?
- Rollback deployment?
- Disable specific agent functionality?
- Schedule retro with team?

---

### Workflow M6: Team Performance Review

**Trigger:** Monthly 1:1s, or performance review cycle.

**Inputs:**
- Individual developer activity
- Task completion rates
- Quality metrics per developer
- Learning/skill progression

**Actions in ASP Overwatch:**
1. Navigate to "Team" view
2. Select team member
3. Review individual metrics:
   - Tasks completed
   - Quality scores (defects introduced)
   - Agent collaboration patterns
   - Skills demonstrated
4. Compare against team average
5. Identify coaching opportunities

**System Process:**
1. Per-developer aggregation
2. Skill inference from task types
3. Quality attribution (who wrote the code)
4. Growth trajectory analysis

**Outputs:**
| View | Contains |
|------|----------|
| Individual Summary | Tasks, quality, efficiency |
| Skill Profile | Languages, domains, tools used |
| Trend Charts | Performance over time |
| Coaching Suggestions | Areas for growth |

**Decisions:**
- Recognition for strong performance?
- Coaching for quality issues?
- Training recommendations?
- Workload rebalancing?

---

## Product Manager Workflows (Jordan)

### Workflow P1: Feature Scoping

**Trigger:** New feature request from stakeholder or roadmap.

**Inputs:**
- High-level feature description
- Business justification
- User research insights
- Constraints (deadline, budget, dependencies)

**Actions in ASP Project Overview:**
1. Click "New Feature" wizard
2. Enter feature description (natural language)
3. Planning Agent asks clarifying questions:
   - Who is the user?
   - What is the success metric?
   - What are the edge cases?
4. Answer questions inline
5. Review generated requirements

**System Process:**
1. **Planning Agent** parses description
2. Identifies ambiguities
3. Generates structured requirements
4. **PROBE-AI** estimates effort
5. Risk analysis based on complexity

**Outputs:**
| Artifact | Format | Contains |
|----------|--------|----------|
| Requirements Doc | Markdown | User stories, acceptance criteria |
| Estimate | Summary | Time, cost, confidence interval |
| Risk Assessment | Markdown | Technical risks, dependencies |
| Scope Definition | Checklist | In-scope/out-of-scope items |

**Decisions:**
- Scope approved as-is?
- Reduce scope to fit deadline?
- Split into phases?
- Reject if cost too high?

---

### Workflow P2: Roadmap Planning

**Trigger:** Quarterly planning, or roadmap review.

**Inputs:**
- Feature backlog with priorities
- Team capacity forecast
- Dependencies between features
- Business deadlines

**Actions in ASP Project Overview:**
1. Navigate to "Timeline" view
2. Import features from backlog
3. PROBE-AI shows estimates for each
4. Drag features onto timeline
5. System shows:
   - Probability of hitting dates
   - Dependency conflicts
   - Resource constraints
6. Adjust and optimize

**System Process:**
1. Monte Carlo simulation of timelines
2. Dependency graph analysis
3. Confidence calculation per feature
4. "What-if" scenario modeling

**Outputs:**
| View | Contains |
|------|----------|
| Probability Timeline | Fuzzy-edged timeline bars |
| Dependency Graph | Feature relationships |
| Confidence Report | Per-feature probability |
| Scenario Comparison | Alternative roadmaps |

**Decisions:**
- Commit to timeline?
- Reorder priorities?
- Add resources to critical path?
- Communicate risks to stakeholders?

---

### Workflow P3: Sprint Grooming

**Trigger:** Sprint grooming meeting preparation.

**Inputs:**
- Backlog items to discuss
- Current PROBE-AI estimates
- Team feedback on items
- Acceptance criteria drafts

**Actions in ASP Project Overview:**
1. Navigate to "Backlog" view
2. For each item, review:
   - Requirements completeness score
   - Estimate confidence level
   - Open questions from Planning Agent
3. Address open questions
4. Re-estimate if requirements changed
5. Mark "Ready for Sprint" or "Needs Work"

**System Process:**
1. Requirements analysis per item
2. Completeness scoring
3. Question tracking
4. Re-estimation on change

**Outputs:**
| Artifact | Format | Contains |
|----------|--------|----------|
| Ready Items List | Table | Items meeting "Definition of Ready" |
| Blocked Items | Table | Items with open questions |
| Estimate Updates | Summary | Changed estimates with reasons |
| Questions Log | List | Unresolved clarifications needed |

**Decisions:**
- Which items ready for sprint?
- Which need more refinement?
- Who should answer questions?
- Should we split large items?

---

### Workflow P4: Stakeholder Update

**Trigger:** Weekly status meeting, or ad-hoc request.

**Inputs:**
- Sprint progress data
- Feature completion status
- Risk updates
- Blockers and issues

**Actions in ASP Project Overview:**
1. Click "Generate Status Report"
2. Select time period and scope
3. Review auto-generated report:
   - Progress summary
   - Completed items
   - In-progress items
   - Risks and blockers
4. Edit/customize messaging
5. Export or present

**System Process:**
1. Aggregates sprint data
2. Formats for stakeholder audience
3. Highlights key metrics
4. Auto-generates charts

**Outputs:**
| Artifact | Format | Contains |
|----------|--------|----------|
| Status Report | Markdown/PDF | Executive summary |
| Progress Charts | Images | Burndown, velocity, completion |
| Risk Summary | Table | Top risks with mitigation status |
| Blockers List | Table | Issues needing escalation |

**Decisions:**
- Report ready to send?
- Need to escalate issues?
- Adjust messaging for audience?
- Schedule follow-up meetings?

---

### Workflow P5: Release Planning

**Trigger:** Approaching release date.

**Inputs:**
- Features targeted for release
- Quality gate status
- Outstanding defects
- Release checklist

**Actions in ASP Project Overview:**
1. Navigate to "Release" view
2. Review release readiness:
   - Features: Complete/In-Progress/At-Risk
   - Quality: Gate pass rates
   - Defects: Open critical/high/medium
3. Run release simulation
4. Decision: Go/No-Go

**System Process:**
1. Feature completion analysis
2. Quality gate aggregation
3. Defect impact assessment
4. Release risk calculation

**Outputs:**
| View | Contains |
|------|----------|
| Release Dashboard | Feature status, quality status |
| Risk Assessment | Release risk score |
| Defect Summary | Open defects by severity |
| Go/No-Go Recommendation | AI-suggested decision |

**Decisions:**
- Release as planned?
- Delay release?
- Ship with known issues?
- Roll back problematic features?

---

### Workflow P6: Requirements Refinement

**Trigger:** Feedback that requirements are unclear.

**Inputs:**
- Original requirements
- Developer questions
- Design review feedback
- User feedback

**Actions in ASP Project Overview:**
1. Open requirement item
2. View linked feedback:
   - Developer questions (from chat)
   - Design review issues
   - Planning Agent suggestions
3. Revise requirements inline
4. Re-run Planning Agent analysis
5. Verify questions resolved

**System Process:**
1. Tracks requirement changes
2. Re-analyzes for completeness
3. Updates estimates based on scope change
4. Links changes to original

**Outputs:**
| Artifact | Format | Contains |
|----------|--------|----------|
| Updated Requirements | Markdown | Revised user stories |
| Change Log | List | What changed and why |
| Updated Estimate | Summary | New time/cost after changes |
| Resolution Status | Checklist | Which questions answered |

**Decisions:**
- Requirements sufficiently clear?
- Need stakeholder input?
- Scope creep concern?
- Ready for development?

---

## Cross-Role Interactions

### Interaction X1: Handoff from PM to Developer

**Scenario:** Jordan (PM) has scoped a feature; Alex (Developer) picks it up.

**Jordan's Output:**
- Requirements document with acceptance criteria
- PROBE-AI estimate
- Risk assessment
- Priority and deadline

**Alex's Input:**
- Reviews requirements in Flow State Canvas
- Asks clarifying questions (routed to Jordan)
- Accepts or requests refinement

**Handoff Artifacts:**
| From | To | Artifact |
|------|-----|----------|
| Jordan | Alex | Requirements Doc |
| Jordan | Alex | Estimate Summary |
| System | Both | Traceability Link |
| Alex | Jordan | Questions (if any) |

---

### Interaction X2: Escalation from Developer to Manager

**Scenario:** Alex encounters a blocker; Sarah (Manager) needs to intervene.

**Alex's Output:**
- Blocker description
- Attempted solutions
- Impact assessment
- Help needed

**Sarah's Input:**
- Sees escalation in Overwatch alerts
- Reviews context (linked artifacts)
- Makes decision (unblock, reassign, escalate further)

**Escalation Artifacts:**
| From | To | Artifact |
|------|-----|----------|
| Alex | Sarah | Blocker Report |
| System | Sarah | Related Telemetry |
| Sarah | Alex | Resolution/Decision |

---

### Interaction X3: Quality Gate Failure Notification

**Scenario:** Code fails security review; all three roles notified.

**System Outputs:**
- To Alex (Developer): Fix required, specific issues listed
- To Sarah (Manager): Quality gate failure logged, team notified
- To Jordan (PM): Feature at risk, timeline impact calculated

**Resolution Flow:**
1. Alex fixes the issue
2. Resubmits for review
3. Pass notification to all
4. Jordan updates stakeholders if delay occurred

---

## Inputs and Outputs Reference

### Developer Inputs
| Input Type | Source | Format |
|------------|--------|--------|
| Requirements | PM | Markdown |
| Design Spec | Design Agent | Markdown |
| Code Context | Repository | Source files |
| Test Results | CI/CD | JSON |
| Review Comments | Code Review Agent | JSON |
| Security Alerts | Security Scanner | JSON |

### Developer Outputs
| Output Type | Destination | Format |
|-------------|-------------|--------|
| Code | Repository | Source files |
| Tests | Repository | Test files |
| PR | GitHub | Pull Request |
| Questions | PM | Chat/Ticket |
| Review | Other Developers | Comments |

### Manager Inputs
| Input Type | Source | Format |
|------------|--------|--------|
| Telemetry | Langfuse | Time series |
| Alerts | Monitoring | JSON |
| Team Status | Developers | Updates |
| Budget Data | Finance | Numbers |
| Quality Metrics | ASP Agents | JSON |

### Manager Outputs
| Output Type | Destination | Format |
|-------------|-------------|--------|
| Decisions | Team | Announcements |
| Budget Adjustments | System | Config |
| Process Changes | Documentation | Markdown |
| Escalations | Leadership | Reports |
| Coaching | Individuals | 1:1s |

### PM Inputs
| Input Type | Source | Format |
|------------|--------|--------|
| Stakeholder Requests | Business | Natural language |
| User Research | Research Team | Reports |
| Estimates | PROBE-AI | JSON |
| Progress Data | ASP Telemetry | JSON |
| Developer Questions | Alex | Chat |

### PM Outputs
| Output Type | Destination | Format |
|-------------|-------------|--------|
| Requirements | Developers | Markdown |
| Roadmap | Stakeholders | Timeline |
| Status Reports | Leadership | PDF/Slides |
| Priorities | Team | Ranked list |
| Release Decisions | All | Go/No-Go |

---

## Summary: The Daily Rhythm

### Developer (Alex) Daily Rhythm
| Time | Activity |
|------|----------|
| 9:00 AM | Check notifications, review overnight CI results |
| 9:30 AM | Pick up next task from sprint backlog |
| 10:00 AM | Plan and design with agents, answer clarifying questions |
| 11:00 AM | Generate code, review and iterate |
| 12:00 PM | Run tests, fix failures |
| 2:00 PM | Code review (own code or others') |
| 3:00 PM | Continue implementation or start new task |
| 4:00 PM | Update task status, prepare for next day |

### Manager (Sarah) Daily Rhythm
| Time | Activity |
|------|----------|
| 8:30 AM | Morning health check in Overwatch |
| 9:00 AM | Standup - review team status |
| 10:00 AM | Clear blockers, make decisions |
| 11:00 AM | Deep-dive on quality metrics or incidents |
| 2:00 PM | 1:1s and coaching |
| 3:00 PM | Cross-team coordination |
| 4:00 PM | Budget and capacity review |
| 5:00 PM | Plan next day priorities |

### PM (Jordan) Daily Rhythm
| Time | Activity |
|------|----------|
| 9:00 AM | Check feature progress in Project Overview |
| 9:30 AM | Stakeholder sync |
| 10:00 AM | Requirements refinement |
| 11:00 AM | Grooming session or feature scoping |
| 2:00 PM | Roadmap updates |
| 3:00 PM | Risk review and mitigation planning |
| 4:00 PM | Status report preparation |
| 5:00 PM | Next-day planning |

---

*Document Version: 1.0*
*Last Updated: December 2025*
*Author: ASP Development Team*
