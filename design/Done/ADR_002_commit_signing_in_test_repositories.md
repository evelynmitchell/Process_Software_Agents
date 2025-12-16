# ADR 002: Commit Signing in Ephemeral Test Repositories

**Status:** Accepted
**Date:** 2025-12-02
**Session:** 20251202.1
**Deciders:** User, Claude

## Context and Problem Statement

The `WorkspaceManager` service creates ephemeral git repositories in `/tmp/asp-workspaces/` for isolated task execution (see ADR 001). These repositories need to support git commits for:

1. Initial commit of test files
2. Committing work-in-progress during agent operations
3. Integration testing of git workflows

**Problem:** The test environment has GPG commit signing enabled globally. When `WorkspaceManager.initialize_git_repo()` attempts to commit, the signing server returns an error:

```
error: signing failed: Signing failed: signing operation failed:
signing server returned status 400: {"type":"error","error":
{"type":"invalid_request_error","message":"source: Field required"}}
```

**Core Question:** Should we disable commit signing in ephemeral test repositories, and if so, what are the security implications?

## Decision Drivers

1. **Functionality:** Tests must be able to create commits in ephemeral repositories
2. **Security:** Commit signing provides author verification and integrity
3. **Scope:** Changes should be minimal and targeted
4. **CI/CD Compatibility:** Solution must work in various environments (local, CI, cloud)
5. **Supply Chain Security:** Consider implications for the broader software supply chain

## Security Analysis

### What Commit Signing Provides

| Protection | Description |
|------------|-------------|
| **Author Verification** | Cryptographically proves who made the commit |
| **Integrity** | Ensures commit content hasn't been tampered with |
| **Non-repudiation** | Author cannot deny making the commit |
| **Supply Chain** | Enables verification of code provenance |

### Risk Assessment for Ephemeral Repositories

| Factor | Risk Level | Rationale |
|--------|------------|-----------|
| **Persistence** | Very Low | Repos deleted after task completion |
| **External Access** | Very Low | Located in `/tmp/`, not pushed to remotes |
| **Author Trust** | N/A | Commits made by ASP agent, not humans |
| **Tampering** | Low | Local filesystem, short-lived |
| **Supply Chain** | None | Artifacts never enter production supply chain |

**Key Insight:** These ephemeral repositories are isolated working environments, not production code repositories. Commits made here are:
- Not pushed to GitHub/remotes
- Not part of the software supply chain
- Not used for author attribution
- Deleted after task completion

## Considered Options

### Option 1: Disable Signing in Ephemeral Repos (CHOSEN) ✅

```python
# In workspace_manager.py
subprocess.run(["git", "config", "commit.gpgsign", "false"], cwd=repo_path)
```

**Scope:** Only ephemeral repositories created by `WorkspaceManager`

**Pros:**
- ✅ Simple, minimal change
- ✅ Scoped to test repos only
- ✅ Works in all environments (local, CI, cloud)
- ✅ No external dependencies
- ✅ Security impact negligible (repos are ephemeral)

**Cons:**
- ⚠️ Commits in test repos are unsigned
- ⚠️ Slightly inconsistent with production practices

### Option 2: Configure Test-Specific Signing Key

```python
# Generate ephemeral GPG key for test repos
subprocess.run(["gpg", "--quick-generate-key", "asp-test@example.com"])
subprocess.run(["git", "config", "user.signingkey", key_id], cwd=repo_path)
```

**Pros:**
- ✅ Commits are signed
- ✅ Maintains signing consistency

**Cons:**
- ❌ Adds complexity (GPG key management)
- ❌ Ephemeral key provides no real security benefit
- ❌ Slower (key generation overhead)
- ❌ Potential key management issues in CI
- ❌ "Security theater" - signing without meaningful verification

### Option 3: Mock/Stub the Signing Service

```python
# In tests, mock the signing service to always succeed
@patch('signing_service.sign')
def test_with_mock_signing(mock_sign):
    mock_sign.return_value = "fake-signature"
```

**Pros:**
- ✅ Tests with signing enabled (sort of)

**Cons:**
- ❌ Only works in test context, not `WorkspaceManager` runtime
- ❌ Doesn't solve the actual problem
- ❌ More complex test setup
- ❌ Still "security theater"

### Option 4: Environment Variable Toggle

```python
# Check environment before deciding
if os.environ.get("ASP_DISABLE_COMMIT_SIGNING"):
    subprocess.run(["git", "config", "commit.gpgsign", "false"], cwd=repo_path)
```

**Pros:**
- ✅ Configurable per-environment
- ✅ Can enable signing in some contexts

**Cons:**
- ❌ Adds configuration complexity
- ❌ Easy to misconfigure
- ❌ Over-engineering for ephemeral repos

### Option 5: Use --no-gpg-sign Per-Commit

```python
subprocess.run(["git", "commit", "--no-gpg-sign", "-m", "Initial commit"], cwd=repo_path)
```

**Pros:**
- ✅ Per-commit control
- ✅ Doesn't change repo config

**Cons:**
- ❌ Must remember flag on every commit
- ❌ External callers (tests) must also use flag
- ❌ Easy to forget, causing intermittent failures

## Decision Outcome

**Chosen option:** **Option 1 - Disable Signing in Ephemeral Repos**

### Rationale

1. **Security impact is negligible** because:
   - Repositories are ephemeral (deleted after use)
   - Located in `/tmp/`, not accessible externally
   - Not pushed to remotes or part of supply chain
   - Commits are made by automated agent, not attributable to humans

2. **Simpler is better** for this use case:
   - Adding signing infrastructure to ephemeral repos is over-engineering
   - A test-specific GPG key provides no meaningful security benefit
   - The complexity cost outweighs any theoretical security gain

3. **Clear scope boundary**:
   - Only `WorkspaceManager`-created repos are affected
   - Production repositories retain full signing
   - Main codebase commits remain signed

### Implementation

```python
# workspace_manager.py, in initialize_git_repo()

# Configure git (required for commits)
subprocess.run(["git", "config", "user.email", "asp@example.com"], cwd=repo_path)
subprocess.run(["git", "config", "user.name", "ASP Agent"], cwd=repo_path)

# Disable GPG signing for this repo (avoids issues in CI/test environments)
subprocess.run(["git", "config", "commit.gpgsign", "false"], cwd=repo_path)
```

### Security Boundary Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                    PRODUCTION BOUNDARY                          │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  GitHub Repositories (signed commits required)           │  │
│  │  - Process_Software_Agents                               │  │
│  │  - External target repositories                          │  │
│  │  - All PRs, merges, releases                            │  │
│  └──────────────────────────────────────────────────────────┘  │
│                              ↑                                  │
│                         git push                                │
│                        (signed commits)                         │
│                              │                                  │
├──────────────────────────────┼──────────────────────────────────┤
│                    TEST/EPHEMERAL BOUNDARY                      │
│                              │                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  /tmp/asp-workspaces/{task-id}/                         │  │
│  │  - Ephemeral repositories (unsigned commits OK)          │  │
│  │  - Deleted after task completion                         │  │
│  │  - Never pushed to remotes                               │  │
│  │  - No supply chain impact                                │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

## Consequences

### Positive

✅ **Tests pass reliably** in all environments
✅ **Minimal code change** - single config line
✅ **CI/CD compatible** - no GPG infrastructure needed
✅ **Clear security boundary** - production repos unaffected
✅ **No false sense of security** - avoids "security theater"

### Negative

⚠️ **Unsigned commits** in ephemeral repos (acceptable given scope)
⚠️ **Different behavior** between test and production repos (intentional)

### Risks Mitigated

| Risk | Mitigation |
|------|------------|
| Unsigned commits escape to production | Ephemeral repos are never pushed |
| Supply chain compromise | Test repos isolated from supply chain |
| Commit attribution confusion | Agent commits clearly labeled "ASP Agent" |

## Alternatives Considered for Future

If requirements change (e.g., test repos need to be pushed somewhere), we could:

1. **Implement proper signing** with managed keys
2. **Use Sigstore/keyless signing** (cosign) for ephemeral attestation
3. **Add a "promote to signed" workflow** before any push

## Related Documents

- `ADR_001_workspace_isolation_and_execution_tracking.md` - Workspace architecture
- `src/services/workspace_manager.py` - Implementation
- `tests/unit/test_services/test_workspace_manager.py` - Tests

## Notes

**Root Cause of Original Failure:**
The development environment had GPG commit signing enabled globally via git config. The signing service (environment-manager code-sign) requires a `source` field that wasn't provided, causing HTTP 400 errors.

**Why This Matters:**
This decision explicitly acknowledges that security controls should match the threat model. Applying production-grade signing to ephemeral test artifacts is:
- Unnecessary (no supply chain impact)
- Costly (complexity, infrastructure)
- Potentially misleading (creates false sense of security)

The right security decision is sometimes to *not* add a control when it doesn't address a real risk.

---

**Status:** Accepted and implemented
**Implementation:** `src/services/workspace_manager.py` line 196-201
**Commit:** `fba7abb` - Fix git commit failures in workspace_manager tests
