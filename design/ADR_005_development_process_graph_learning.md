# ADR 005: Development Process Graph Learning from Summary Files and Git History

**Status:** Proposed
**Date:** 2025-12-04
**Session:** 20251204.1
**Deciders:** User, Claude
**Related:** ADR 004 (Process Graph Learning from Execution)

## Context and Problem Statement

The ASP project maintains detailed session summary files (`Summary/summary*.md`) documenting objectives, completed work, files modified, and session progression. Combined with git history, this data represents a rich **event log of the development process itself**.

**Insight:** If we can apply process mining to runtime execution traces (ADR 004), we can apply the same techniques to the development process:
- How do features actually get built?
- What's the typical session → commit → merge flow?
- Which files are "hot spots" that correlate with issues?
- Does actual development follow intended workflows?

**Problem:** How do we extract trace-like events from unstructured/semi-structured development artifacts (summaries, git) and analyze them as a process?

## Decision Drivers

1. **Unified Approach:** Same process mining techniques for runtime and development
2. **Data Already Exists:** Summaries and git history are already captured
3. **Meta-Learning:** Understand how to improve the development process itself
4. **Correlation:** Link development patterns to outcomes (bugs, velocity, quality)
5. **Low Overhead:** No new instrumentation needed - just parsing existing data

## Data Sources

### Source 1: Session Summary Files

Location: `Summary/summary{YYYYMMDD}.{N}.md`

**Structure (semi-structured markdown):**

```markdown
# Session Summary - 2025-12-02 Session 10

## Objective
Fix CI/CD pytest failures...

## Completed Work
- Investigated recent changes...
- Found that...
- Ran the test suite...

## Files Modified
- `scripts/init_test_artifacts_repo.sh`
- `tests/integration/test_artifacts_repo_scripts.py`
...

## Commits Made
1. `540661c` - Fix CI test failures for artifacts repo
2. `79d4f83` - Add What-If scenario simulator

## Status
Complete
```

**Extractable Events:**
| Event Type | Source | Example |
|------------|--------|---------|
| `session.start` | File creation | 2025-12-02, session 10 |
| `session.objective` | ## Objective section | "Fix CI/CD pytest failures" |
| `task.completed` | ## Completed Work bullets | "Investigated recent changes" |
| `file.modified` | ## Files Modified list | "scripts/init_test.sh" |
| `commit.referenced` | ## Commits Made | "540661c" |
| `session.end` | ## Status | "Complete" |

### Source 2: Git History

**Git Log Data:**
```
commit 540661c (2025-12-02 14:23:15)
Author: User <user@example.com>
Message: Fix CI test failures for artifacts repo

 scripts/init_test_artifacts_repo.sh | 2 ++
 tests/integration/test_artifacts.py | 5 +++++
 2 files changed, 7 insertions(+)
```

**Extractable Events:**
| Event Type | Source | Example |
|------------|--------|---------|
| `commit.created` | git log | SHA, timestamp, author |
| `file.added` | git diff --stat | New file |
| `file.modified` | git diff --stat | Changed file |
| `file.deleted` | git diff --stat | Removed file |
| `branch.created` | git branch --contains | Feature branch |
| `branch.merged` | merge commits | PR merged |

### Source 3: GitHub/PR Data (Optional)

If available via `gh` CLI or API:
| Event Type | Source |
|------------|--------|
| `pr.opened` | PR creation |
| `pr.reviewed` | Review submitted |
| `pr.approved` | Approval given |
| `pr.merged` | PR merged |
| `issue.opened` | Issue created |
| `issue.closed` | Issue resolved |

## Proposed Solution

### Event Schema

```python
# src/asp/telemetry/dev_events.py

from dataclasses import dataclass
from datetime import datetime
from typing import Literal

EventType = Literal[
    "session.start",
    "session.end",
    "objective.set",
    "task.started",
    "task.completed",
    "file.created",
    "file.modified",
    "file.deleted",
    "commit.created",
    "branch.created",
    "branch.merged",
    "pr.opened",
    "pr.merged",
    "test.passed",
    "test.failed",
]


@dataclass
class DevelopmentEvent:
    """
    Event in the development process.

    Analogous to OpenTelemetry span but for dev activities.
    """
    # Identification
    event_id: str               # Unique ID
    case_id: str                # Groups events (session_id, feature_id, etc.)
    timestamp: datetime         # When event occurred

    # Event details
    event_type: EventType       # Type of development event
    activity: str               # Human-readable activity name
    resource: str               # Who/what performed it (user, CI, Claude)

    # Context
    session_id: str | None      # Which session (e.g., "20251202.10")
    commit_sha: str | None      # Related commit
    files: list[str] | None     # Related files
    description: str | None     # Additional context

    # Linkage
    parent_event_id: str | None # Causal predecessor
    trace_id: str | None        # Links to runtime traces (if any)


@dataclass
class DevelopmentTrace:
    """
    A sequence of development events forming a trace.

    Analogous to an OTEL trace but for development.
    """
    trace_id: str               # e.g., feature branch name
    events: list[DevelopmentEvent]
    start_time: datetime
    end_time: datetime | None
    outcome: str | None         # "merged", "abandoned", "in_progress"
```

### Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      Data Sources                                │
├─────────────────┬─────────────────┬─────────────────────────────┤
│  Summary Files  │   Git History   │   GitHub API (optional)     │
│  Summary/*.md   │   .git/         │   PRs, Issues, Reviews      │
└────────┬────────┴────────┬────────┴────────────┬────────────────┘
         │                 │                      │
         ▼                 ▼                      ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Parsers / Extractors                          │
├─────────────────┬─────────────────┬─────────────────────────────┤
│ SummaryParser   │  GitLogParser   │   GitHubEventParser         │
│                 │                 │                              │
│ - Regex/MD AST  │  - git log      │   - gh pr list              │
│ - Section split │  - git diff     │   - gh issue list           │
│ - Date extract  │  - git branch   │   - gh pr view              │
└────────┬────────┴────────┬────────┴────────────┬────────────────┘
         │                 │                      │
         └─────────────────┼──────────────────────┘
                           │
                           ▼
              ┌───────────────────────┐
              │    Event Correlator   │
              │                       │
              │  - Match commits to   │
              │    sessions           │
              │  - Link files across  │
              │    events             │
              │  - Build case IDs     │
              └───────────┬───────────┘
                          │
                          ▼
              ┌───────────────────────┐
              │   Development Event   │
              │        Log            │
              │                       │
              │   (XES / CSV / JSON)  │
              └───────────┬───────────┘
                          │
          ┌───────────────┼───────────────┐
          │               │               │
          ▼               ▼               ▼
   ┌─────────────┐ ┌─────────────┐ ┌─────────────┐
   │  Process    │ │   Pattern   │ │ Correlation │
   │  Discovery  │ │   Mining    │ │  Analysis   │
   │             │ │             │ │             │
   │  How do we  │ │  Common     │ │  Dev speed  │
   │  actually   │ │  sequences  │ │  vs bugs    │
   │  develop?   │ │  that lead  │ │  vs quality │
   │             │ │  to bugs    │ │             │
   └─────────────┘ └─────────────┘ └─────────────┘
```

### Component 1: Summary File Parser

```python
# src/asp/telemetry/parsers/summary_parser.py

import re
from pathlib import Path
from datetime import datetime
from typing import Iterator

from asp.telemetry.dev_events import DevelopmentEvent


class SummaryParser:
    """Parse session summary markdown files into events."""

    # Patterns for extracting data
    HEADER_PATTERN = re.compile(
        r"# Session Summary - (\d{4}-\d{2}-\d{2}) Session (\d+)"
    )
    SECTION_PATTERN = re.compile(r"^## (.+)$", re.MULTILINE)
    BULLET_PATTERN = re.compile(r"^[-*] (.+)$", re.MULTILINE)
    FILE_PATTERN = re.compile(r"`([^`]+\.[a-z]+)`")
    COMMIT_PATTERN = re.compile(r"`([a-f0-9]{7,40})`")

    def parse_file(self, path: Path) -> Iterator[DevelopmentEvent]:
        """
        Parse a summary file into development events.

        Yields events in chronological order.
        """
        content = path.read_text()

        # Extract header info
        header_match = self.HEADER_PATTERN.search(content)
        if not header_match:
            return

        date_str = header_match.group(1)
        session_num = header_match.group(2)
        session_id = f"{date_str.replace('-', '')}.{session_num}"
        session_date = datetime.strptime(date_str, "%Y-%m-%d")

        # Emit session start
        yield DevelopmentEvent(
            event_id=f"{session_id}:start",
            case_id=session_id,
            timestamp=session_date,
            event_type="session.start",
            activity="Session Started",
            resource="developer",
            session_id=session_id,
            commit_sha=None,
            files=None,
            description=None,
            parent_event_id=None,
            trace_id=None,
        )

        # Parse sections
        sections = self._split_sections(content)

        # Objective section
        if "Objective" in sections:
            objective = sections["Objective"].strip()
            yield DevelopmentEvent(
                event_id=f"{session_id}:objective",
                case_id=session_id,
                timestamp=session_date,
                event_type="objective.set",
                activity="Set Objective",
                resource="developer",
                session_id=session_id,
                commit_sha=None,
                files=None,
                description=objective[:500],
                parent_event_id=f"{session_id}:start",
                trace_id=None,
            )

        # Completed Work section
        if "Completed Work" in sections:
            for i, task in enumerate(self._extract_bullets(sections["Completed Work"])):
                yield DevelopmentEvent(
                    event_id=f"{session_id}:task:{i}",
                    case_id=session_id,
                    timestamp=session_date,
                    event_type="task.completed",
                    activity=task[:100],
                    resource="developer",
                    session_id=session_id,
                    commit_sha=None,
                    files=self.FILE_PATTERN.findall(task),
                    description=task,
                    parent_event_id=f"{session_id}:objective",
                    trace_id=None,
                )

        # Files Modified section
        if "Files Modified" in sections:
            files = self.FILE_PATTERN.findall(sections["Files Modified"])
            for i, file_path in enumerate(files):
                yield DevelopmentEvent(
                    event_id=f"{session_id}:file:{i}",
                    case_id=session_id,
                    timestamp=session_date,
                    event_type="file.modified",
                    activity=f"Modified {Path(file_path).name}",
                    resource="developer",
                    session_id=session_id,
                    commit_sha=None,
                    files=[file_path],
                    description=None,
                    parent_event_id=None,
                    trace_id=None,
                )

        # Commits Made section
        if "Commits Made" in sections:
            commits = self.COMMIT_PATTERN.findall(sections["Commits Made"])
            for i, sha in enumerate(commits):
                yield DevelopmentEvent(
                    event_id=f"{session_id}:commit:{i}",
                    case_id=session_id,
                    timestamp=session_date,
                    event_type="commit.created",
                    activity=f"Commit {sha[:7]}",
                    resource="developer",
                    session_id=session_id,
                    commit_sha=sha,
                    files=None,
                    description=None,
                    parent_event_id=None,
                    trace_id=None,
                )

        # Session end
        status = sections.get("Status", "").strip()
        yield DevelopmentEvent(
            event_id=f"{session_id}:end",
            case_id=session_id,
            timestamp=session_date,
            event_type="session.end",
            activity="Session Ended",
            resource="developer",
            session_id=session_id,
            commit_sha=None,
            files=None,
            description=status,
            parent_event_id=f"{session_id}:start",
            trace_id=None,
        )

    def _split_sections(self, content: str) -> dict[str, str]:
        """Split markdown into sections by ## headers."""
        sections = {}
        current_section = None
        current_content = []

        for line in content.split("\n"):
            if line.startswith("## "):
                if current_section:
                    sections[current_section] = "\n".join(current_content)
                current_section = line[3:].strip()
                current_content = []
            elif current_section:
                current_content.append(line)

        if current_section:
            sections[current_section] = "\n".join(current_content)

        return sections

    def _extract_bullets(self, text: str) -> list[str]:
        """Extract bullet point items from text."""
        return self.BULLET_PATTERN.findall(text)


def parse_all_summaries(summary_dir: Path) -> list[DevelopmentEvent]:
    """Parse all summary files in chronological order."""
    parser = SummaryParser()
    events = []

    for path in sorted(summary_dir.glob("summary*.md")):
        events.extend(parser.parse_file(path))

    return sorted(events, key=lambda e: (e.timestamp, e.event_id))
```

### Component 2: Git History Parser

```python
# src/asp/telemetry/parsers/git_parser.py

import subprocess
from datetime import datetime
from pathlib import Path
from typing import Iterator

from asp.telemetry.dev_events import DevelopmentEvent


class GitLogParser:
    """Parse git history into development events."""

    def __init__(self, repo_path: Path = Path(".")):
        self.repo_path = repo_path

    def parse_commits(
        self,
        since: datetime | None = None,
        until: datetime | None = None,
    ) -> Iterator[DevelopmentEvent]:
        """
        Parse git log into commit events.

        Each commit becomes a commit.created event,
        plus file.* events for each changed file.
        """
        cmd = [
            "git", "log",
            "--format=%H|%aI|%an|%ae|%s",
            "--name-status",
        ]

        if since:
            cmd.append(f"--since={since.isoformat()}")
        if until:
            cmd.append(f"--until={until.isoformat()}")

        result = subprocess.run(
            cmd,
            cwd=self.repo_path,
            capture_output=True,
            text=True,
        )

        current_commit = None
        file_events = []

        for line in result.stdout.split("\n"):
            if "|" in line and line.count("|") == 4:
                # Yield previous commit's events
                if current_commit:
                    yield current_commit
                    yield from file_events
                    file_events = []

                # Parse commit line
                sha, date_str, author, email, message = line.split("|", 4)
                timestamp = datetime.fromisoformat(date_str)

                current_commit = DevelopmentEvent(
                    event_id=f"commit:{sha[:7]}",
                    case_id=self._get_case_id(sha),
                    timestamp=timestamp,
                    event_type="commit.created",
                    activity=f"Commit: {message[:50]}",
                    resource=author,
                    session_id=None,  # Link later via correlation
                    commit_sha=sha,
                    files=None,
                    description=message,
                    parent_event_id=None,
                    trace_id=None,
                )

            elif line and line[0] in "AMD" and "\t" in line:
                # File change line: "M\tpath/to/file.py"
                status, file_path = line.split("\t", 1)

                event_type = {
                    "A": "file.created",
                    "M": "file.modified",
                    "D": "file.deleted",
                }.get(status, "file.modified")

                if current_commit:
                    file_events.append(DevelopmentEvent(
                        event_id=f"commit:{current_commit.commit_sha[:7]}:file:{file_path}",
                        case_id=current_commit.case_id,
                        timestamp=current_commit.timestamp,
                        event_type=event_type,
                        activity=f"{status} {Path(file_path).name}",
                        resource=current_commit.resource,
                        session_id=None,
                        commit_sha=current_commit.commit_sha,
                        files=[file_path],
                        description=None,
                        parent_event_id=current_commit.event_id,
                        trace_id=None,
                    ))

        # Yield last commit
        if current_commit:
            yield current_commit
            yield from file_events

    def parse_branches(self) -> Iterator[DevelopmentEvent]:
        """Parse branch creation and merge events."""
        # Get all branches with their first commit
        cmd = ["git", "branch", "-a", "-v", "--format=%(refname:short)|%(objectname:short)|%(creatordate:iso)"]
        result = subprocess.run(cmd, cwd=self.repo_path, capture_output=True, text=True)

        for line in result.stdout.strip().split("\n"):
            if not line or "|" not in line:
                continue

            branch, sha, date_str = line.split("|")

            if date_str:
                timestamp = datetime.fromisoformat(date_str.strip())
            else:
                timestamp = datetime.now()

            yield DevelopmentEvent(
                event_id=f"branch:{branch}",
                case_id=branch,  # Branch as case ID for feature flows
                timestamp=timestamp,
                event_type="branch.created",
                activity=f"Branch: {branch}",
                resource="developer",
                session_id=None,
                commit_sha=sha,
                files=None,
                description=None,
                parent_event_id=None,
                trace_id=None,
            )

    def _get_case_id(self, commit_sha: str) -> str:
        """
        Determine case_id for a commit.

        Options:
        - Use branch name if on feature branch
        - Use date-based session ID
        - Use commit SHA prefix
        """
        # Try to find branch containing this commit
        cmd = ["git", "branch", "--contains", commit_sha, "--format=%(refname:short)"]
        result = subprocess.run(cmd, cwd=self.repo_path, capture_output=True, text=True)

        branches = [b.strip() for b in result.stdout.strip().split("\n") if b.strip()]

        # Prefer feature branches over main
        for branch in branches:
            if branch not in ("main", "master"):
                return branch

        return commit_sha[:7]
```

### Component 3: Event Correlator

```python
# src/asp/telemetry/correlate.py

from datetime import datetime, timedelta
from asp.telemetry.dev_events import DevelopmentEvent


class EventCorrelator:
    """
    Correlate events from different sources.

    Links:
    - Commits to sessions (by date and referenced SHA)
    - Files across events (same file path)
    - Sessions to features (by objective keywords)
    """

    def correlate(
        self,
        summary_events: list[DevelopmentEvent],
        git_events: list[DevelopmentEvent],
    ) -> list[DevelopmentEvent]:
        """
        Merge and correlate events from summaries and git.

        Returns unified, correlated event list.
        """
        all_events = []

        # Index summary events by date and commit SHA
        sessions_by_date = self._index_by_date(summary_events)
        commits_in_summaries = self._extract_commit_refs(summary_events)

        # Add summary events
        all_events.extend(summary_events)

        # Add git events with correlation
        for event in git_events:
            # Try to link to session
            if event.event_type == "commit.created":
                session_id = self._find_session(
                    event.timestamp,
                    event.commit_sha,
                    sessions_by_date,
                    commits_in_summaries,
                )
                if session_id:
                    event.session_id = session_id
                    event.case_id = session_id  # Group with session

            all_events.append(event)

        # Sort by timestamp
        return sorted(all_events, key=lambda e: e.timestamp)

    def _index_by_date(
        self,
        events: list[DevelopmentEvent]
    ) -> dict[str, list[str]]:
        """Index session IDs by date."""
        index = {}
        for event in events:
            if event.event_type == "session.start":
                date_key = event.timestamp.strftime("%Y-%m-%d")
                if date_key not in index:
                    index[date_key] = []
                index[date_key].append(event.session_id)
        return index

    def _extract_commit_refs(
        self,
        events: list[DevelopmentEvent]
    ) -> dict[str, str]:
        """Map commit SHAs to session IDs."""
        refs = {}
        for event in events:
            if event.commit_sha and event.session_id:
                refs[event.commit_sha[:7]] = event.session_id
        return refs

    def _find_session(
        self,
        commit_time: datetime,
        commit_sha: str,
        sessions_by_date: dict,
        commits_in_summaries: dict,
    ) -> str | None:
        """Find session that likely contains this commit."""
        # Check if commit is explicitly referenced
        sha_short = commit_sha[:7]
        if sha_short in commits_in_summaries:
            return commits_in_summaries[sha_short]

        # Match by date
        date_key = commit_time.strftime("%Y-%m-%d")
        sessions = sessions_by_date.get(date_key, [])

        if len(sessions) == 1:
            return sessions[0]

        # Multiple sessions on same day - could use time proximity
        # For now, return the last session of the day
        return sessions[-1] if sessions else None


def build_development_traces(
    events: list[DevelopmentEvent],
    case_field: str = "session_id",
) -> dict[str, list[DevelopmentEvent]]:
    """
    Group events into traces by case ID.

    Args:
        events: All development events
        case_field: Field to group by (session_id, case_id, etc.)

    Returns:
        Dict mapping case_id to list of events
    """
    traces = {}
    for event in events:
        case_id = getattr(event, case_field) or event.case_id
        if case_id not in traces:
            traces[case_id] = []
        traces[case_id].append(event)

    return traces
```

### Component 4: Analysis and Mining

```python
# src/asp/telemetry/dev_process_mining.py

import pm4py
from collections import Counter
from asp.telemetry.dev_events import DevelopmentEvent


def discover_development_process(events: list[DevelopmentEvent]) -> dict:
    """
    Discover the actual development process from events.

    Returns DFG and statistics.
    """
    # Convert to PM4Py event log format
    log = _to_pm4py_log(events)

    # Discover DFG
    dfg = pm4py.discover_dfg(log)

    # Get process statistics
    stats = {
        "total_sessions": len(set(e.session_id for e in events if e.session_id)),
        "total_commits": len([e for e in events if e.event_type == "commit.created"]),
        "total_files_touched": len(set(
            f for e in events if e.files for f in e.files
        )),
        "activity_frequency": Counter(e.activity for e in events),
        "avg_session_events": _avg_events_per_session(events),
    }

    return {
        "dfg": dfg,
        "statistics": stats,
    }


def find_common_patterns(events: list[DevelopmentEvent]) -> list[dict]:
    """
    Find common sequential patterns in development.

    E.g., "objective → task → commit" sequences.
    """
    patterns = Counter()

    # Build traces
    traces = {}
    for event in events:
        case_id = event.session_id or event.case_id
        if case_id not in traces:
            traces[case_id] = []
        traces[case_id].append(event.event_type)

    # Count 2-grams and 3-grams
    for trace in traces.values():
        for i in range(len(trace) - 1):
            patterns[(trace[i], trace[i+1])] += 1
        for i in range(len(trace) - 2):
            patterns[(trace[i], trace[i+1], trace[i+2])] += 1

    return [
        {"pattern": p, "count": c}
        for p, c in patterns.most_common(20)
    ]


def analyze_file_hotspots(events: list[DevelopmentEvent]) -> list[dict]:
    """
    Find files that are frequently modified.

    Hotspots may indicate:
    - Core files that need careful attention
    - Problematic files that need refactoring
    - Configuration files that change often
    """
    file_counts = Counter()
    file_sessions = {}  # file -> set of sessions

    for event in events:
        if event.files:
            for f in event.files:
                file_counts[f] += 1
                if event.session_id:
                    if f not in file_sessions:
                        file_sessions[f] = set()
                    file_sessions[f].add(event.session_id)

    return [
        {
            "file": f,
            "modifications": c,
            "sessions_touched": len(file_sessions.get(f, set())),
        }
        for f, c in file_counts.most_common(20)
    ]


def correlate_with_outcomes(
    events: list[DevelopmentEvent],
    outcomes: dict[str, str],  # session_id -> outcome
) -> dict:
    """
    Correlate development patterns with outcomes.

    E.g., do sessions with many small commits have fewer bugs?

    Args:
        events: Development events
        outcomes: Map of session_id to outcome label
            (e.g., "success", "bug_introduced", "reverted")

    Returns:
        Correlation analysis
    """
    session_features = {}

    for event in events:
        sid = event.session_id
        if not sid:
            continue

        if sid not in session_features:
            session_features[sid] = {
                "commit_count": 0,
                "file_count": 0,
                "task_count": 0,
            }

        if event.event_type == "commit.created":
            session_features[sid]["commit_count"] += 1
        if event.event_type == "task.completed":
            session_features[sid]["task_count"] += 1
        if event.files:
            session_features[sid]["file_count"] += len(event.files)

    # Compare features by outcome
    by_outcome = {}
    for sid, features in session_features.items():
        outcome = outcomes.get(sid, "unknown")
        if outcome not in by_outcome:
            by_outcome[outcome] = []
        by_outcome[outcome].append(features)

    # Calculate averages by outcome
    summary = {}
    for outcome, feature_list in by_outcome.items():
        if feature_list:
            summary[outcome] = {
                "count": len(feature_list),
                "avg_commits": sum(f["commit_count"] for f in feature_list) / len(feature_list),
                "avg_files": sum(f["file_count"] for f in feature_list) / len(feature_list),
                "avg_tasks": sum(f["task_count"] for f in feature_list) / len(feature_list),
            }

    return summary


def _to_pm4py_log(events: list[DevelopmentEvent]):
    """Convert events to PM4Py EventLog format."""
    from pm4py.objects.log.obj import EventLog, Trace, Event

    traces = {}
    for e in events:
        case_id = e.session_id or e.case_id
        if case_id not in traces:
            traces[case_id] = []
        traces[case_id].append({
            "concept:name": e.activity,
            "time:timestamp": e.timestamp,
            "org:resource": e.resource,
            "event_type": e.event_type,
        })

    log = EventLog()
    for case_id, event_list in traces.items():
        trace = Trace()
        trace.attributes["concept:name"] = case_id
        for event_dict in event_list:
            event = Event(event_dict)
            trace.append(event)
        log.append(trace)

    return log


def _avg_events_per_session(events: list[DevelopmentEvent]) -> float:
    """Calculate average events per session."""
    sessions = {}
    for e in events:
        if e.session_id:
            sessions[e.session_id] = sessions.get(e.session_id, 0) + 1

    if not sessions:
        return 0.0
    return sum(sessions.values()) / len(sessions)
```

## Use Cases

### 1. Development Process Discovery

**Question:** What does our actual development process look like?

```python
# Run discovery
events = parse_all_summaries(Path("Summary"))
events += list(GitLogParser().parse_commits(since=datetime(2025, 11, 1)))
events = EventCorrelator().correlate(events, events)

result = discover_development_process(events)
visualize_dfg(result["dfg"], "dev_process.png")
```

**Output:** DFG showing typical flow:
```
session.start → objective.set → task.completed → commit.created → session.end
                                      ↓
                               file.modified
```

### 2. Hotspot Analysis

**Question:** Which files are touched most frequently?

```python
hotspots = analyze_file_hotspots(events)
# Result:
# [
#   {"file": "src/asp/web/data.py", "modifications": 45, "sessions_touched": 12},
#   {"file": "tests/unit/test_web/test_data.py", "modifications": 38, "sessions_touched": 10},
#   ...
# ]
```

### 3. Pattern Mining

**Question:** What sequences lead to successful outcomes?

```python
patterns = find_common_patterns(events)
# Result:
# [
#   {"pattern": ("objective.set", "task.completed"), "count": 89},
#   {"pattern": ("task.completed", "commit.created"), "count": 76},
#   {"pattern": ("commit.created", "file.modified"), "count": 156},
#   ...
# ]
```

### 4. Session Comparison

**Question:** Do sessions with explicit objectives have better outcomes?

```python
outcomes = {
    "20251202.10": "success",  # CI fixed, feature shipped
    "20251202.11": "success",  # Docs updated
    "20251201.5": "bug_introduced",  # Had to fix later
    # ...
}

correlation = correlate_with_outcomes(events, outcomes)
# Result:
# {
#   "success": {"count": 45, "avg_commits": 2.3, "avg_files": 5.1, "avg_tasks": 4.2},
#   "bug_introduced": {"count": 3, "avg_commits": 4.7, "avg_files": 12.3, "avg_tasks": 6.1},
# }
# Insight: Sessions with more files touched correlate with bugs
```

## Implementation Plan

### Phase 1: Parsers
- [ ] Create `src/asp/telemetry/parsers/summary_parser.py`
- [ ] Create `src/asp/telemetry/parsers/git_parser.py`
- [ ] Create `src/asp/telemetry/dev_events.py` schema
- [ ] Unit tests for parsers

### Phase 2: Correlation
- [ ] Create `src/asp/telemetry/correlate.py`
- [ ] Link commits to sessions
- [ ] Build unified event log
- [ ] Export to XES format

### Phase 3: Analysis
- [ ] Create `src/asp/telemetry/dev_process_mining.py`
- [ ] Implement DFG discovery
- [ ] Implement pattern mining
- [ ] Implement hotspot analysis

### Phase 4: Visualization
- [ ] Add development process page to Web UI
- [ ] Visualize DFG with D3.js
- [ ] Show session timeline
- [ ] Display hotspot files

### Phase 5: Integration
- [ ] Link to runtime traces (ADR 004) via trace_id
- [ ] Feed patterns into documentation
- [ ] Use for retrospective analysis

## Dependencies

```toml
# pyproject.toml - same as ADR 004
dependencies = [
    "pm4py>=2.7.0",
]
```

## Consequences

### Positive
- **Self-Awareness:** Understand how development actually happens
- **No New Instrumentation:** Uses existing summaries and git
- **Pattern Learning:** Discover what works and what doesn't
- **Unified View:** Same tools for runtime and dev process

### Negative
- **Parsing Fragility:** Summary format changes break parser
- **Manual Correlation:** Some linking requires heuristics
- **Outcome Labeling:** Need manual or automated outcome tagging

### Mitigation
- Standardize summary format (template)
- Fallback gracefully on parse failures
- Add outcome tagging to session workflow

## Related Documents

- ADR 004: Process Graph Learning from Execution
- ADR 003: OpenTelemetry RL Triplet Instrumentation
- Summary file examples: `Summary/summary*.md`

---

**Status:** Proposed - Awaiting review
