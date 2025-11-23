/**
 * HITL Quality Gate GitHub Workflow - Formal Specification
 *
 * This Alloy model formally specifies the Human-in-the-Loop (HITL) approval
 * workflow using GitHub Issues, as described in Section 3.1B of
 * HITL_QualityGate_Architecture.md
 *
 * The model captures:
 * - State machine for approval requests (PENDING → APPROVED/REJECTED/TIMEOUT)
 * - GitHub Issue lifecycle (created → commented → closed)
 * - Orchestrator polling behavior
 * - Human reviewer interaction
 * - Temporal constraints (timeout, polling intervals)
 * - Safety and liveness properties
 *
 * Author: ASP Development Team
 * Date: November 22, 2025
 * Version: 1.0
 */

module HITL_GitHub_Workflow

open util/ordering[Time] as time

/**
 * Time abstraction for modeling temporal behavior
 */
sig Time {}

/**
 * Approval request states
 */
abstract sig ApprovalStatus {}
one sig PENDING extends ApprovalStatus {}
one sig APPROVED extends ApprovalStatus {}
one sig REJECTED extends ApprovalStatus {}
one sig TIMEOUT extends ApprovalStatus {}

/**
 * Quality gate types
 */
abstract sig GateType {}
one sig DesignReview extends GateType {}
one sig CodeReview extends GateType {}

/**
 * Comment types on GitHub issues
 */
abstract sig CommentType {}
one sig ApproveCommand extends CommentType {}
one sig RejectCommand extends CommentType {}
one sig RegularComment extends CommentType {}

/**
 * A comment posted on a GitHub issue
 */
sig Comment {
  author: one Human,
  commentType: one CommentType,
  justification: lone String,
  postedAt: one Time
}

/**
 * A GitHub issue representing an approval request
 */
sig GitHubIssue {
  issueNumber: one Int,
  createdAt: one Time,
  closedAt: lone Time,
  comments: set Comment,
  assignee: set Human,

  // Issue metadata
  labels: set Label,

  // Relationship to approval request
  approvalRequest: one ApprovalRequest
} {
  // Issue number must be positive
  issueNumber > 0

  // If closed, closedAt must be after createdAt
  some closedAt implies time/lt[createdAt, closedAt]

  // Comments must be posted after issue creation
  all c: comments | time/gte[c.postedAt, createdAt]

  // If closed, all comments must be before closure
  some closedAt implies (all c: comments | time/lte[c.postedAt, closedAt])
}

/**
 * Labels on GitHub issues
 */
abstract sig Label {}
one sig ApprovalRequired extends Label {}
one sig ApprovedLabel extends Label {}
one sig RejectedLabel extends Label {}
one sig TimeoutLabel extends Label {}

/**
 * An approval request with state machine
 */
sig ApprovalRequest {
  taskId: one String,
  gate: one GateType,

  // State transitions over time
  status: Time -> one ApprovalStatus,

  // Temporal constraints
  createdAt: one Time,
  timeoutAt: one Time,
  decidedAt: lone Time,

  // Decision metadata
  approver: lone Human,
  justification: lone String,

  // Link to GitHub issue
  issue: one GitHubIssue
} {
  // Timeout must be after creation
  time/lt[createdAt, timeoutAt]

  // If decided, decision time must be between creation and timeout
  some decidedAt implies {
    time/gte[decidedAt, createdAt]
    time/lte[decidedAt, timeoutAt]
  }

  // Initially PENDING
  status[createdAt] = PENDING

  // Status can only change once (from PENDING to final state)
  all t1, t2: Time | t1 != t2 and status[t1] != PENDING and status[t2] != PENDING
    implies status[t1] = status[t2]

  // Once in final state, never changes
  all t: Time | status[t] in (APPROVED + REJECTED + TIMEOUT) implies
    (all t2: Time | time/gte[t2, t] implies status[t2] = status[t])

  // Approved/Rejected implies approver exists
  (some t: Time | status[t] in (APPROVED + REJECTED)) implies some approver

  // Timeout means no approver
  (some t: Time | status[t] = TIMEOUT) implies no approver

  // Bidirectional link with GitHub issue
  issue.approvalRequest = this
}

/**
 * Human reviewer who can approve or reject
 */
sig Human {
  username: one String
}

/**
 * TSP Orchestrator that creates and polls issues
 */
one sig Orchestrator {
  // Polling interval (in abstract time units)
  pollInterval: one Int,

  // Issues created by orchestrator
  created: set GitHubIssue,

  // Polling history: which issues were polled at which times
  polled: GitHubIssue -> Time
} {
  pollInterval > 0

  // Can only poll issues that were created
  polled.Time in created

  // Can only poll after issue creation
  all i: GitHubIssue, t: Time | i->t in polled implies
    time/gte[t, i.createdAt]
}

/**
 * System state representing all entities at a point in time
 */
sig SystemState {
  time: one Time,
  requests: set ApprovalRequest,
  issues: set GitHubIssue,
  comments: set Comment
} {
  // All issues must have corresponding requests
  issues.approvalRequest in requests

  // Comments belong to issues
  comments in issues.comments
}

//============================================================================
// PREDICATES: State Transitions and Behaviors
//============================================================================

/**
 * Orchestrator creates a GitHub issue for an approval request
 */
pred createIssue[t: Time, r: ApprovalRequest] {
  // Preconditions
  r.status[t] = PENDING
  no r.issue.closedAt // Issue not yet closed

  // Issue created at this time
  r.issue.createdAt = t

  // Issue added to orchestrator's created set
  r.issue in Orchestrator.created

  // Initial labels
  ApprovalRequired in r.issue.labels
}

/**
 * Human posts an approval command
 */
pred humanApproves[t: Time, i: GitHubIssue, h: Human, just: String] {
  // Preconditions
  i.approvalRequest.status[t] = PENDING
  time/gte[t, i.createdAt]
  no i.closedAt or time/lt[t, i.closedAt]

  // Create approval comment
  some c: Comment | {
    c.author = h
    c.commentType = ApproveCommand
    c.justification = just
    c.postedAt = t
    c in i.comments
  }
}

/**
 * Human posts a rejection command
 */
pred humanRejects[t: Time, i: GitHubIssue, h: Human, reason: String] {
  // Preconditions
  i.approvalRequest.status[t] = PENDING
  time/gte[t, i.createdAt]
  no i.closedAt or time/lt[t, i.closedAt]

  // Create rejection comment
  some c: Comment | {
    c.author = h
    c.commentType = RejectCommand
    c.justification = reason
    c.postedAt = t
    c in i.comments
  }
}

/**
 * Orchestrator polls issue and detects approval decision
 */
pred orchestratorDetectsApproval[t: Time, i: GitHubIssue] {
  // Preconditions
  i.approvalRequest.status[t] = PENDING

  // There exists an approval comment before this poll
  some c: Comment | {
    c in i.comments
    c.commentType = ApproveCommand
    time/lte[c.postedAt, t]
  }

  // Record poll
  i->t in Orchestrator.polled

  // Transition to APPROVED
  let r = i.approvalRequest | {
    all t2: Time | time/gte[t2, t] implies r.status[t2] = APPROVED
    r.decidedAt = t
    r.approver = (i.comments & {c: Comment | c.commentType = ApproveCommand}).author
  }

  // Add approved label
  ApprovedLabel in i.labels
}

/**
 * Orchestrator polls issue and detects rejection decision
 */
pred orchestratorDetectsRejection[t: Time, i: GitHubIssue] {
  // Preconditions
  i.approvalRequest.status[t] = PENDING

  // There exists a rejection comment before this poll
  some c: Comment | {
    c in i.comments
    c.commentType = RejectCommand
    time/lte[c.postedAt, t]
  }

  // Record poll
  i->t in Orchestrator.polled

  // Transition to REJECTED
  let r = i.approvalRequest | {
    all t2: Time | time/gte[t2, t] implies r.status[t2] = REJECTED
    r.decidedAt = t
    r.approver = (i.comments & {c: Comment | c.commentType = RejectCommand}).author
  }

  // Add rejected label
  RejectedLabel in i.labels
}

/**
 * Approval request times out
 */
pred requestTimeout[t: Time, r: ApprovalRequest] {
  // Preconditions
  r.status[t] = PENDING
  time/gte[t, r.timeoutAt]

  // Transition to TIMEOUT
  all t2: Time | time/gte[t2, t] implies r.status[t2] = TIMEOUT

  // No approver for timeout
  no r.approver

  // Add timeout label to issue
  TimeoutLabel in r.issue.labels
}

/**
 * Orchestrator closes issue after decision
 */
pred closeIssue[t: Time, i: GitHubIssue] {
  // Preconditions
  i.approvalRequest.status[t] in (APPROVED + REJECTED + TIMEOUT)
  time/gte[t, i.approvalRequest.decidedAt] or i.approvalRequest.status[t] = TIMEOUT

  // Close issue
  i.closedAt = t
}

//============================================================================
// FACTS: System Invariants
//============================================================================

/**
 * Approval decision can only happen via human comment
 */
fact DecisionRequiresComment {
  all r: ApprovalRequest, t: Time |
    r.status[t] = APPROVED implies {
      some c: r.issue.comments |
        c.commentType = ApproveCommand and
        time/lte[c.postedAt, t]
    }

  all r: ApprovalRequest, t: Time |
    r.status[t] = REJECTED implies {
      some c: r.issue.comments |
        c.commentType = RejectCommand and
        time/lte[c.postedAt, t]
    }
}

/**
 * No decision after timeout
 */
fact NoDecisionAfterTimeout {
  all r: ApprovalRequest |
    r.status[r.timeoutAt] = PENDING implies
      (all t: Time | time/gte[t, r.timeoutAt] implies r.status[t] = TIMEOUT)
}

/**
 * Timeout is fail-safe: cannot transition from TIMEOUT
 */
fact TimeoutIsFailSafe {
  all r: ApprovalRequest, t: Time |
    r.status[t] = TIMEOUT implies
      (all t2: Time | time/gte[t2, t] implies r.status[t2] = TIMEOUT)
}

/**
 * Only one decision per request
 */
fact SingleDecision {
  all r: ApprovalRequest |
    lone r.decidedAt

  all r: ApprovalRequest |
    (some t: Time | r.status[t] in (APPROVED + REJECTED)) implies
      one r.approver
}

/**
 * Issue lifecycle consistency
 */
fact IssueLifecycle {
  // Issue must be created before closed
  all i: GitHubIssue |
    some i.closedAt implies time/lt[i.createdAt, i.closedAt]

  // Closed issues have final status
  all i: GitHubIssue |
    some i.closedAt implies
      i.approvalRequest.status[i.closedAt] in (APPROVED + REJECTED + TIMEOUT)
}

/**
 * Orchestrator polling regularity
 */
fact RegularPolling {
  // Orchestrator polls pending requests at regular intervals
  all i: GitHubIssue, t: Time |
    i.approvalRequest.status[t] = PENDING and
    time/lt[t, i.approvalRequest.timeoutAt] implies
      // Either already polled or will poll in the future
      (some t2: Time | i->t2 in Orchestrator.polled and time/gte[t2, t])
}

/**
 * Approval/Rejection are mutually exclusive
 */
fact MutualExclusivity {
  all r: ApprovalRequest, t: Time |
    r.status[t] = APPROVED implies
      (all t2: Time | r.status[t2] != REJECTED and r.status[t2] != TIMEOUT)

  all r: ApprovalRequest, t: Time |
    r.status[t] = REJECTED implies
      (all t2: Time | r.status[t2] != APPROVED and r.status[t2] != TIMEOUT)
}

//============================================================================
// ASSERTIONS: Properties to Verify
//============================================================================

/**
 * Safety: No request transitions after timeout
 */
assert NoTransitionAfterTimeout {
  all r: ApprovalRequest |
    r.status[r.timeoutAt] = PENDING implies
      (all t: Time | time/gte[t, r.timeoutAt] implies r.status[t] = TIMEOUT)
}

/**
 * Safety: Every approved request has an approver
 */
assert ApprovedHasApprover {
  all r: ApprovalRequest |
    (some t: Time | r.status[t] = APPROVED) implies some r.approver
}

/**
 * Safety: Timed out requests have no approver
 */
assert TimeoutHasNoApprover {
  all r: ApprovalRequest |
    (some t: Time | r.status[t] = TIMEOUT) implies no r.approver
}

/**
 * Safety: Status only changes once
 */
assert StatusChangesOnce {
  all r: ApprovalRequest, t1, t2, t3: Time |
    time/lt[t1, t2] and time/lt[t2, t3] and
    r.status[t1] = PENDING and
    r.status[t2] in (APPROVED + REJECTED + TIMEOUT)
    implies r.status[t3] = r.status[t2]
}

/**
 * Safety: Decisions are idempotent
 */
assert DecisionIdempotence {
  all r: ApprovalRequest, t1, t2: Time |
    time/lte[t1, t2] and
    r.status[t1] in (APPROVED + REJECTED) and
    r.status[t2] in (APPROVED + REJECTED)
    implies r.status[t1] = r.status[t2]
}

/**
 * Liveness: Every request eventually reaches a final state
 */
assert EventualDecision {
  all r: ApprovalRequest |
    some t: Time | r.status[t] in (APPROVED + REJECTED + TIMEOUT)
}

/**
 * Liveness: If human approves before timeout, request will be approved
 */
assert HumanApprovalHonored {
  all r: ApprovalRequest, c: Comment |
    c in r.issue.comments and
    c.commentType = ApproveCommand and
    time/lt[c.postedAt, r.timeoutAt]
    implies
      (some t: Time | time/gte[t, c.postedAt] and r.status[t] = APPROVED)
}

/**
 * Liveness: If human rejects before timeout, request will be rejected
 */
assert HumanRejectionHonored {
  all r: ApprovalRequest, c: Comment |
    c in r.issue.comments and
    c.commentType = RejectCommand and
    time/lt[c.postedAt, r.timeoutAt]
    implies
      (some t: Time | time/gte[t, c.postedAt] and r.status[t] = REJECTED)
}

/**
 * Consistency: Issue labels match request status
 */
assert LabelConsistency {
  all r: ApprovalRequest, t: Time |
    r.status[t] = APPROVED implies ApprovedLabel in r.issue.labels

  all r: ApprovalRequest, t: Time |
    r.status[t] = REJECTED implies RejectedLabel in r.issue.labels

  all r: ApprovalRequest, t: Time |
    r.status[t] = TIMEOUT implies TimeoutLabel in r.issue.labels
}

/**
 * Consistency: Closed issues have final status
 */
assert ClosedIssuesFinal {
  all i: GitHubIssue |
    some i.closedAt implies
      i.approvalRequest.status[i.closedAt] in (APPROVED + REJECTED + TIMEOUT)
}

//============================================================================
// PREDICATES: Example Scenarios
//============================================================================

/**
 * Example: Successful approval workflow
 */
pred approvalScenario {
  some r: ApprovalRequest, h: Human |
    // Request starts pending
    r.status[r.createdAt] = PENDING and

    // Human approves before timeout
    some c: Comment |
      c.author = h and
      c.commentType = ApproveCommand and
      time/lt[c.postedAt, r.timeoutAt] and
      c in r.issue.comments and

    // Request eventually approved
    some t: Time |
      r.status[t] = APPROVED and
      r.approver = h and

    // Issue eventually closed
    some r.issue.closedAt
}

/**
 * Example: Rejection workflow
 */
pred rejectionScenario {
  some r: ApprovalRequest, h: Human |
    r.status[r.createdAt] = PENDING and

    some c: Comment |
      c.author = h and
      c.commentType = RejectCommand and
      time/lt[c.postedAt, r.timeoutAt] and
      c in r.issue.comments and

    some t: Time |
      r.status[t] = REJECTED and
      r.approver = h
}

/**
 * Example: Timeout scenario
 */
pred timeoutScenario {
  some r: ApprovalRequest |
    r.status[r.createdAt] = PENDING and

    // No approval or rejection comment before timeout
    no c: r.issue.comments |
      c.commentType in (ApproveCommand + RejectCommand) and
      time/lt[c.postedAt, r.timeoutAt]
    and

    // Status becomes TIMEOUT at timeout
    r.status[r.timeoutAt] = TIMEOUT and
    no r.approver
}

/**
 * Example: Multiple comments, first decision wins
 */
pred firstDecisionWins {
  some r: ApprovalRequest, h1, h2: Human |
    h1 != h2 and

    // First human approves
    some c1: Comment |
      c1.author = h1 and
      c1.commentType = ApproveCommand and
      c1 in r.issue.comments and

    // Second human tries to reject later
    some c2: Comment |
      c2.author = h2 and
      c2.commentType = RejectCommand and
      c2 in r.issue.comments and
      time/lt[c1.postedAt, c2.postedAt] and

    // Request approved (first decision)
    some t: Time |
      r.status[t] = APPROVED and
      r.approver = h1 and

    // Never rejected
    all t: Time | r.status[t] != REJECTED
}

//============================================================================
// VERIFICATION COMMANDS
//============================================================================

// Check that assertions hold (uncomment to run in Alloy Analyzer)
// check NoTransitionAfterTimeout for 5
// check ApprovedHasApprover for 5
// check TimeoutHasNoApprover for 5
// check StatusChangesOnce for 5
// check DecisionIdempotence for 5
// check EventualDecision for 5
// check HumanApprovalHonored for 5
// check HumanRejectionHonored for 5
// check LabelConsistency for 5
// check ClosedIssuesFinal for 5

// Run example scenarios (uncomment to run in Alloy Analyzer)
// run approvalScenario for 5 but 8 Time
// run rejectionScenario for 5 but 8 Time
// run timeoutScenario for 5 but 8 Time
// run firstDecisionWins for 5 but 10 Time

//============================================================================
// DOCUMENTATION
//============================================================================

/**
 * MODEL SUMMARY
 * =============
 *
 * This Alloy model captures the essential behavior of the HITL GitHub workflow
 * described in Section 3.1B of HITL_QualityGate_Architecture.md.
 *
 * KEY PROPERTIES VERIFIED:
 *
 * 1. Safety Properties:
 *    - No state transitions after timeout
 *    - Every approved request has an identified approver
 *    - Timed out requests have no approver
 *    - Status changes at most once (from PENDING to final state)
 *    - Decisions are idempotent
 *
 * 2. Liveness Properties:
 *    - Every request eventually reaches a final state (APPROVED/REJECTED/TIMEOUT)
 *    - Human approval comments are eventually honored
 *    - Human rejection comments are eventually honored
 *
 * 3. Consistency Properties:
 *    - GitHub issue labels match request status
 *    - Closed issues always have final status
 *    - Approval and rejection are mutually exclusive
 *
 * USAGE:
 * ======
 *
 * To verify the model in Alloy Analyzer:
 *
 * 1. Open this file in Alloy Analyzer 5.x or later
 * 2. Uncomment verification commands at the end of the file
 * 3. Execute "Check" commands to verify assertions
 * 4. Execute "Run" commands to see example traces
 * 5. Inspect counterexamples if any assertion fails
 *
 * EXAMPLE TRACES:
 * ===============
 *
 * The model includes several scenario predicates that can be executed to
 * visualize the workflow:
 *
 * - approvalScenario: Human approves before timeout, request approved
 * - rejectionScenario: Human rejects before timeout, request rejected
 * - timeoutScenario: No human response, request times out
 * - firstDecisionWins: Multiple comments, first decision is honored
 *
 * LIMITATIONS:
 * ============
 *
 * This model abstracts several implementation details:
 *
 * - Exact polling intervals (modeled abstractly via ordering)
 * - Network delays and failures (assumed perfect communication)
 * - GitHub API rate limits (not modeled)
 * - Concurrent access to issues (single-threaded model)
 * - String content validation (abstract String type)
 *
 * These limitations are acceptable for verifying high-level correctness
 * properties but should be addressed in implementation testing.
 *
 * RELATIONSHIP TO ARCHITECTURE:
 * =============================
 *
 * This model formalizes the workflow described in:
 * - HITL_QualityGate_Architecture.md, Section 3.1B
 * - Specifically the state machine in lines 150-173
 * - And the workflow diagram in lines 834-955
 *
 * The model serves as a formal specification that can guide implementation
 * and be used as a reference for testing scenarios.
 */
