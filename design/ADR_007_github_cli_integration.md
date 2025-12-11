# ADR 007: GitHub CLI Integration

**Status:** Proposed
**Date:** 2025-12-11
**Session:** 20251211.1
**Deciders:** User, Claude

## Context and Problem Statement

ADR 006 implemented a repair workflow that can diagnose and fix bugs in existing code. However, the workflow currently operates only on local workspaces. To be useful for **dogfooding** and real-world automation, the system needs to:

1. Clone repositories from GitHub
2. Understand issue context when fixing bugs
3. Submit fixes as pull requests

**Core Question:** How should we integrate GitHub CLI (`gh`) to enable end-to-end automation from issue to PR?

### Current State

| Capability | Status | Gap |
|------------|--------|-----|
| Clone repos | Partial (git clone exists) | No `gh` auth, no issue linking |
| Read issues | Missing | Cannot fetch issue descriptions |
| Create branches | Missing | No branch naming conventions |
| Create PRs | Missing | Cannot submit fixes |
| Link PR to issue | Missing | No "Fixes #123" automation |

### Dogfooding Value

With GitHub CLI integration, we can:
- Point the repair workflow at a real GitHub issue
- Have it clone the repo, understand the issue, fix the bug
- Submit a PR that references the issue
- Iterate based on real-world feedback

This creates a tight feedback loop for improving the system itself.

## Decision Drivers

1. **Dogfooding:** Use the tool on our own projects to find and fix issues
2. **Automation:** Enable fully automated issue-to-PR workflows
3. **Simplicity:** Use `gh` CLI rather than raw GitHub API (already handles auth)
4. **Traceability:** Link PRs to issues for audit trail
5. **Safety:** Require explicit confirmation before creating PRs

## Proposed Architecture

### High-Level Workflow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    GITHUB-INTEGRATED REPAIR WORKFLOW                         │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Input: GitHub Issue URL (e.g., github.com/owner/repo/issues/123)           │
│                                                                              │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐              │
│  │  Fetch   │───▶│  Clone   │───▶│  Repair  │───▶│  Create  │              │
│  │  Issue   │    │   Repo   │    │   Loop   │    │    PR    │              │
│  └──────────┘    └──────────┘    └──────────┘    └────┬─────┘              │
│       │                │              │               │                      │
│       ▼                ▼              ▼               ▼                      │
│  Issue title,     Branch:        ADR 006         PR with:                   │
│  body, labels     fix/issue-123  workflow        - Issue link               │
│                                                  - Change summary           │
│                                                  - Test results             │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### New Component: GitHubService

**Location:** `src/services/github_service.py`

```python
@dataclass
class GitHubIssue:
    """Parsed GitHub issue."""
    owner: str
    repo: str
    number: int
    title: str
    body: str
    labels: list[str]
    state: str  # open, closed
    url: str

@dataclass
class GitHubPR:
    """Created pull request."""
    owner: str
    repo: str
    number: int
    url: str
    title: str
    branch: str

class GitHubService:
    """
    Service for GitHub operations using `gh` CLI.

    Requires: `gh` CLI installed and authenticated (`gh auth login`)
    """

    def __init__(self, workspace_base: Path):
        self.workspace_base = workspace_base
        self._verify_gh_installed()

    def _verify_gh_installed(self) -> None:
        """Verify gh CLI is available and authenticated."""
        result = subprocess.run(
            ["gh", "auth", "status"],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            raise RuntimeError(
                "GitHub CLI not authenticated. Run: gh auth login"
            )

    def fetch_issue(self, issue_url: str) -> GitHubIssue:
        """
        Fetch issue details from GitHub.

        Args:
            issue_url: Full URL like github.com/owner/repo/issues/123

        Returns:
            GitHubIssue with title, body, labels
        """
        owner, repo, number = self._parse_issue_url(issue_url)

        result = subprocess.run(
            [
                "gh", "issue", "view", str(number),
                "--repo", f"{owner}/{repo}",
                "--json", "title,body,labels,state,url",
            ],
            capture_output=True,
            text=True,
            check=True,
        )

        data = json.loads(result.stdout)
        return GitHubIssue(
            owner=owner,
            repo=repo,
            number=number,
            title=data["title"],
            body=data["body"],
            labels=[l["name"] for l in data.get("labels", [])],
            state=data["state"],
            url=data["url"],
        )

    def clone_repo(
        self,
        owner: str,
        repo: str,
        workspace: Workspace,
        branch: str | None = None,
    ) -> Path:
        """
        Clone repository into workspace.

        Args:
            owner: Repository owner
            repo: Repository name
            workspace: Target workspace
            branch: Optional branch to checkout

        Returns:
            Path to cloned repository
        """
        clone_path = workspace.target_repo_path

        subprocess.run(
            [
                "gh", "repo", "clone",
                f"{owner}/{repo}",
                str(clone_path),
                "--",
                *(["--branch", branch] if branch else []),
            ],
            check=True,
        )

        return clone_path

    def create_branch(
        self,
        workspace: Workspace,
        branch_name: str,
    ) -> None:
        """Create and checkout a new branch."""
        subprocess.run(
            ["git", "checkout", "-b", branch_name],
            cwd=workspace.target_repo_path,
            check=True,
        )

    def commit_changes(
        self,
        workspace: Workspace,
        message: str,
    ) -> str:
        """
        Stage and commit all changes.

        Returns:
            Commit SHA
        """
        repo_path = workspace.target_repo_path

        # Stage all changes
        subprocess.run(
            ["git", "add", "-A"],
            cwd=repo_path,
            check=True,
        )

        # Commit
        subprocess.run(
            ["git", "commit", "-m", message],
            cwd=repo_path,
            check=True,
        )

        # Get commit SHA
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=repo_path,
            capture_output=True,
            text=True,
            check=True,
        )

        return result.stdout.strip()

    def push_branch(
        self,
        workspace: Workspace,
        branch: str,
    ) -> None:
        """Push branch to origin."""
        subprocess.run(
            ["git", "push", "-u", "origin", branch],
            cwd=workspace.target_repo_path,
            check=True,
        )

    def create_pr(
        self,
        workspace: Workspace,
        title: str,
        body: str,
        base_branch: str = "main",
        draft: bool = False,
    ) -> GitHubPR:
        """
        Create a pull request.

        Args:
            workspace: Workspace with committed changes
            title: PR title
            body: PR description (markdown)
            base_branch: Target branch (default: main)
            draft: Create as draft PR

        Returns:
            GitHubPR with URL and number
        """
        result = subprocess.run(
            [
                "gh", "pr", "create",
                "--title", title,
                "--body", body,
                "--base", base_branch,
                *(["--draft"] if draft else []),
                "--json", "url,number",
            ],
            cwd=workspace.target_repo_path,
            capture_output=True,
            text=True,
            check=True,
        )

        data = json.loads(result.stdout)

        # Parse owner/repo from remote
        owner, repo = self._get_remote_info(workspace)

        return GitHubPR(
            owner=owner,
            repo=repo,
            number=data["number"],
            url=data["url"],
            title=title,
            branch=self._get_current_branch(workspace),
        )

    def _parse_issue_url(self, url: str) -> tuple[str, str, int]:
        """Parse github.com/owner/repo/issues/123 -> (owner, repo, 123)"""
        # Handle various URL formats
        patterns = [
            r"github\.com/([^/]+)/([^/]+)/issues/(\d+)",
            r"github\.com/([^/]+)/([^/]+)/pull/(\d+)",
        ]

        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1), match.group(2), int(match.group(3))

        raise ValueError(f"Could not parse GitHub URL: {url}")
```

---

### Branch Naming Convention

```python
def generate_branch_name(issue: GitHubIssue) -> str:
    """
    Generate branch name from issue.

    Format: fix/issue-{number}-{slug}
    Example: fix/issue-123-null-pointer-exception
    """
    # Create slug from title
    slug = issue.title.lower()
    slug = re.sub(r"[^a-z0-9]+", "-", slug)
    slug = slug.strip("-")[:30]  # Limit length

    return f"fix/issue-{issue.number}-{slug}"
```

---

### PR Body Template

```python
PR_BODY_TEMPLATE = '''
## Summary

Automated fix for #{issue_number}: {issue_title}

## Changes Made

{changes_summary}

## Test Results

- **Tests Run:** {tests_run}
- **Tests Passed:** {tests_passed}
- **Coverage:** {coverage}%

## Repair Process

- **Iterations:** {iterations}
- **Confidence:** {confidence:.0%}
- **Diagnostic:** {diagnostic_summary}

---

*This PR was generated by [ASP Repair Workflow](link-to-docs)*

Fixes #{issue_number}
'''
```

---

### Integration with Repair Orchestrator

**Modified:** `src/asp/orchestrators/repair_orchestrator.py`

```python
@dataclass
class GitHubRepairRequest:
    """Request to repair from GitHub issue."""
    issue_url: str
    max_iterations: int = 5
    create_pr: bool = True
    draft_pr: bool = True  # Safe default

@dataclass
class GitHubRepairResult:
    """Result of GitHub-integrated repair."""
    issue: GitHubIssue
    repair_result: RepairResult
    pr: GitHubPR | None
    branch: str


class RepairOrchestrator:
    """Extended with GitHub integration."""

    def __init__(
        self,
        # ... existing params ...
        github_service: GitHubService | None = None,
    ):
        # ... existing init ...
        self.github = github_service

    async def repair_from_issue(
        self,
        request: GitHubRepairRequest,
    ) -> GitHubRepairResult:
        """
        Full workflow: Issue -> Clone -> Repair -> PR

        Args:
            request: GitHubRepairRequest with issue URL

        Returns:
            GitHubRepairResult with PR URL if successful
        """
        # 1. Fetch issue details
        issue = self.github.fetch_issue(request.issue_url)
        logger.info(f"Fetched issue #{issue.number}: {issue.title}")

        # 2. Create workspace and clone repo
        workspace = self.workspace_manager.create_workspace(
            f"repair-{issue.owner}-{issue.repo}-{issue.number}"
        )
        self.github.clone_repo(issue.owner, issue.repo, workspace)

        # 3. Create fix branch
        branch = generate_branch_name(issue)
        self.github.create_branch(workspace, branch)

        # 4. Run repair workflow (ADR 006)
        repair_result = await self.repair(RepairRequest(
            task_id=f"{issue.owner}/{issue.repo}#{issue.number}",
            workspace=workspace,
            issue_description=f"{issue.title}\n\n{issue.body}",
            max_iterations=request.max_iterations,
        ))

        # 5. Create PR if successful
        pr = None
        if repair_result.success and request.create_pr:
            # Commit changes
            commit_msg = f"Fix #{issue.number}: {issue.title}"
            self.github.commit_changes(workspace, commit_msg)

            # Push branch
            self.github.push_branch(workspace, branch)

            # Create PR
            pr_body = self._format_pr_body(issue, repair_result)
            pr = self.github.create_pr(
                workspace,
                title=f"Fix #{issue.number}: {issue.title}",
                body=pr_body,
                draft=request.draft_pr,
            )
            logger.info(f"Created PR: {pr.url}")

        return GitHubRepairResult(
            issue=issue,
            repair_result=repair_result,
            pr=pr,
            branch=branch,
        )
```

---

### CLI Integration

**Modified:** `src/asp/cli/main.py`

```python
@cli.command()
@click.argument("issue_url")
@click.option("--max-iterations", default=5, help="Max repair iterations")
@click.option("--no-pr", is_flag=True, help="Don't create PR")
@click.option("--draft/--no-draft", default=True, help="Create as draft PR")
def repair_issue(
    issue_url: str,
    max_iterations: int,
    no_pr: bool,
    draft: bool,
):
    """
    Repair a bug from a GitHub issue.

    Example:
        asp repair-issue https://github.com/owner/repo/issues/123
    """
    orchestrator = create_repair_orchestrator()

    result = asyncio.run(orchestrator.repair_from_issue(
        GitHubRepairRequest(
            issue_url=issue_url,
            max_iterations=max_iterations,
            create_pr=not no_pr,
            draft_pr=draft,
        )
    ))

    if result.repair_result.success:
        click.echo(f"Successfully fixed issue #{result.issue.number}")
        if result.pr:
            click.echo(f"PR created: {result.pr.url}")
    else:
        click.echo(f"Failed to fix issue after {result.repair_result.iterations_used} iterations")
        sys.exit(1)
```

---

## Security Considerations

### Authentication

- Uses `gh auth login` - credentials managed by GitHub CLI
- No API tokens stored in code or config
- Respects user's existing GitHub authentication

### Permissions

- **Read:** Needs read access to clone repos and view issues
- **Write:** Needs write access to push branches and create PRs
- For public repos: Fork workflow may be needed if no push access

### Fork Workflow (Future)

For repos where user doesn't have push access:

```python
def clone_or_fork(self, owner: str, repo: str, workspace: Workspace) -> Path:
    """Clone if we have access, otherwise fork first."""
    try:
        return self.clone_repo(owner, repo, workspace)
    except subprocess.CalledProcessError:
        # Fork the repo first
        subprocess.run(
            ["gh", "repo", "fork", f"{owner}/{repo}", "--clone=false"],
            check=True,
        )
        # Clone from fork
        user = self._get_authenticated_user()
        return self.clone_repo(user, repo, workspace)
```

### Rate Limiting

- GitHub API has rate limits (5000 requests/hour authenticated)
- `gh` CLI handles rate limiting automatically
- Consider caching issue data during repair loops

---

## Implementation Plan

### Phase 1: Core GitHub Operations
- [x] Implement `GitHubService` class
- [x] Add `fetch_issue()` with URL parsing
- [x] Add `clone_repo()` using `gh repo clone`
- [x] Add `create_branch()` and `commit_changes()`
- [x] Unit tests with mocked `gh` calls (29 tests)

### Phase 2: PR Creation
- [x] Implement `push_branch()`
- [x] Implement `create_pr()` with body template
- [x] Add branch naming convention
- [x] Add "Fixes #N" linking
- [x] Add `format_pr_body()` helper method
- [x] Unit tests for Phase 2 methods (12 tests)

### Phase 3: Integration
- [ ] Add `repair_from_issue()` to RepairOrchestrator
- [ ] Add `repair-issue` CLI command
- [ ] Integration tests with test repo

### Phase 4: Dogfooding
- [ ] Test on real issues in this repo
- [ ] Document workflow and limitations
- [ ] Iterate based on feedback

---

## File Summary

### New Files

| File | Description |
|------|-------------|
| `src/services/github_service.py` | GitHubService wrapping `gh` CLI |
| `tests/unit/test_services/test_github_service.py` | Unit tests |
| `tests/integration/test_github_repair_workflow.py` | Integration tests |

### Modified Files

| File | Change |
|------|--------|
| `src/asp/orchestrators/repair_orchestrator.py` | Add `repair_from_issue()` |
| `src/asp/cli/main.py` | Add `repair-issue` command |

---

## Consequences

### Positive

- **Dogfooding:** Can test repair workflow on real issues
- **Automation:** Full issue-to-PR workflow
- **Traceability:** PRs linked to issues
- **Simplicity:** Leverages `gh` CLI instead of raw API

### Negative

- **Dependency:** Requires `gh` CLI installed and authenticated
- **Permissions:** May need fork workflow for repos without push access
- **Rate Limits:** Heavy usage could hit GitHub API limits

### Risks

| Risk | Mitigation |
|------|------------|
| `gh` not installed | Clear error message with install instructions |
| Auth expired | Check auth status before operations |
| No push access | Future: implement fork workflow |
| PR spam | Default to draft PRs, require explicit opt-in |

---

## Open Questions

1. **Fork workflow:** Should we auto-fork when push access is denied?
2. **Multiple issues:** Support batch repair of related issues?
3. **Issue templates:** Parse issue templates for structured bug info?
4. **Status updates:** Comment on issue with repair progress?

---

## Related Documents

- `design/ADR_006_repair_workflow_architecture.md` - Repair workflow this integrates with
- `design/ADR_001_workspace_isolation_and_execution_tracking.md` - Workspace management

---

**Status:** Proposed
**Next Steps:** Review, then begin Phase 1 implementation
