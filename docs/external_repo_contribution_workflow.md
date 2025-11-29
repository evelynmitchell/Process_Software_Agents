# External Repository Contribution Workflow

## Issue: Git Proxy Authorization Limitation

### Problem Description

When working on external repositories via WorkspaceManager, the Claude Code git proxy only authorizes access to the primary repository (Process_Software_Agents). Attempting to push to other repositories (even forks owned by the same user) fails with:

```
remote: Proxy error: repository not authorized
fatal: unable to access 'http://127.0.0.1:PORT/git/evelynmitchell/nanoGPT/':
The requested URL returned error: 502
```

### Root Cause

The git proxy is configured to only allow authenticated access to specific repositories. This is a security measure to prevent unauthorized access, but it creates a workflow limitation when contributing to external projects.

### Workflow Impact

| Step | Works? | Notes |
|------|--------|-------|
| Clone external repo | ✅ | Public repos can be cloned |
| Create workspace | ✅ | WorkspaceManager functions correctly |
| Make changes | ✅ | All local operations work |
| Commit locally | ✅ | Git operations in workspace work |
| Push to fork | ❌ | Blocked by proxy authorization |
| Push to Process_Software_Agents | ✅ | Primary repo is authorized |

### Current Workarounds

#### Option 1: Export to Primary Repo
Copy contribution files to Process_Software_Agents and commit there:
```bash
mkdir -p contrib/project-name/
cp -r /tmp/asp-workspaces/task-id/target-repo/new-files/* contrib/project-name/
git add contrib/ && git commit && git push
```
User then manually copies files to their fork locally.

#### Option 2: Create Patch File
Generate a git patch that user can apply locally:
```bash
cd /tmp/asp-workspaces/task-id/target-repo
git format-patch origin/master --stdout > contribution.patch
```
User applies with: `git apply contribution.patch`

#### Option 3: Create Tarball
Archive the contribution files:
```bash
tar -czvf contribution.tar.gz new-files/
```
User extracts to their local clone.

### Recommended Workflow for External Contributions

```
┌─────────────────────────────────────────────────────────────┐
│                    Claude Code Session                       │
├─────────────────────────────────────────────────────────────┤
│ 1. Clone external repo to workspace                         │
│ 2. Make changes (code, tests, docs)                         │
│ 3. Commit locally in workspace                              │
│ 4. Copy files to Process_Software_Agents/contrib/           │
│ 5. Push to Process_Software_Agents                          │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    User Local Machine                        │
├─────────────────────────────────────────────────────────────┤
│ 1. Pull Process_Software_Agents branch                      │
│ 2. Clone/update fork of external repo                       │
│ 3. Copy files from contrib/ to fork                         │
│ 4. Commit and push to fork                                  │
│ 5. Create PR on GitHub                                      │
└─────────────────────────────────────────────────────────────┘
```

### Future Improvements

1. **Multi-repo authorization**: Allow users to authorize additional repos for proxy access
2. **GitHub App integration**: Use GitHub App tokens for broader repo access
3. **PR creation API**: Use GitHub API directly (if gh CLI becomes available)
4. **Export command**: Add WorkspaceManager method to export contributions

### Example: nanoGPT Test Contribution

**Session 20251129.2** encountered this issue when contributing tests to nanoGPT:

1. ✅ Cloned `karpathy/nanoGPT` to workspace
2. ✅ Created 28 tests with 79% coverage
3. ✅ Committed to local `add-test-suite` branch
4. ❌ Could not push to `evelynmitchell/nanoGPT` fork
5. ✅ Copied files to `Process_Software_Agents/contrib/nanogpt-tests/`
6. ✅ User can now copy files to their fork locally

### Files Location

Contribution files stored at:
```
Process_Software_Agents/
└── contrib/
    └── nanogpt-tests/
        ├── __init__.py
        ├── conftest.py
        ├── pyproject.toml
        ├── test_model.py
        └── test_nanogpt.ipynb
```

---

**Document Created:** Session 20251129.2
**Status:** Workaround implemented, improvement opportunities identified
