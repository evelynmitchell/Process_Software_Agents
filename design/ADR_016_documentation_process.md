# ADR 016: Documentation Process and DocumentationAgent

**Status:** Draft
**Date:** 2025-12-26
**Session:** 20251226.1
**Deciders:** User, Claude

## Context and Problem Statement

Documentation often lags behind code changes. Features are implemented and tested, but corresponding documentation updates are missed. This leads to:

1. **Stale docs** - Users find outdated instructions
2. **Incomplete docs** - New features undocumented
3. **Inconsistent docs** - Different docs describe the same feature differently
4. **Discovery friction** - Users don't know features exist

### Current State

| Aspect | Current Implementation |
|--------|------------------------|
| Doc updates | Ad-hoc, manual |
| Review process | No doc-specific checklist |
| Automation | None |
| Doc coverage | Unknown |
| Freshness checks | None |

### Pain Points

```
Current: Ad-hoc Documentation
┌─────────────────────────────────────────────────────────────┐
│ Feature Added → Tests Written → PR Merged → Docs Forgotten  │
│                                                             │
│ Example: ClaudeCLIProvider added, but docs not updated      │
│ until explicitly asked                                      │
└─────────────────────────────────────────────────────────────┘

Desired: Documentation-Aware Development
┌─────────────────────────────────────────────────────────────┐
│ Feature Added → Tests Written → Docs Updated → PR Merged    │
│                      ↓                                      │
│              DocumentationAgent suggests updates            │
│              CI checks doc coverage                         │
└─────────────────────────────────────────────────────────────┘
```

## Decision Drivers

1. **Completeness** - All features documented
2. **Freshness** - Docs updated with code changes
3. **Discoverability** - Users can find what they need
4. **Automation** - Reduce manual burden
5. **Integration** - Works with existing workflow
6. **Quality** - Docs are accurate and useful

## Documentation Inventory

### Primary Documentation Files

| File | Purpose | Update Trigger |
|------|---------|----------------|
| `README.md` | Project overview, quick start | Major features, architecture changes |
| `docs/Getting_Started.md` | Installation, first use | New providers, new CLI commands |
| `docs/API_Reference.md` | Programmatic API | New classes, methods, parameters |
| `docs/Agents_Reference.md` | Agent documentation | New agents, agent changes |
| `docs/Developer_Guide.md` | Contributing, extending | Architecture changes, new patterns |
| `design/ADR_*.md` | Architecture decisions | Design decisions |

### Documentation-to-Code Mapping

| Code Area | Documentation Files |
|-----------|---------------------|
| `src/asp/agents/*.py` | `docs/Agents_Reference.md` |
| `src/asp/providers/*.py` | `docs/Getting_Started.md` (providers section) |
| `src/asp/cli/*.py` | `docs/Getting_Started.md` (CLI section) |
| `src/asp/orchestrators/*.py` | `docs/API_Reference.md` |
| `design/ADR_*.md` | `docs/KNOWLEDGE_BASE.md` (ADR index) |

## Proposed Solution

### 1. DocumentationAgent

A new agent that analyzes code changes and suggests documentation updates.

```
┌─────────────────────────────────────────────────────────────┐
│                   DocumentationAgent                         │
├─────────────────────────────────────────────────────────────┤
│ Input:                                                       │
│   - Code diff (files changed)                               │
│   - Existing documentation                                  │
│   - Documentation mapping rules                             │
│                                                             │
│ Output:                                                      │
│   - List of docs that need updates                          │
│   - Suggested content for each doc                          │
│   - Priority (critical/recommended/optional)                │
│                                                             │
│ Modes:                                                       │
│   - Analyze: Identify gaps                                  │
│   - Suggest: Generate update content                        │
│   - Apply: Write documentation updates                      │
└─────────────────────────────────────────────────────────────┘
```

#### DocumentationAgent Workflow

```python
# Usage Example
from asp.agents import DocumentationAgent

agent = DocumentationAgent()

# Analyze what docs need updates based on code changes
analysis = await agent.analyze(
    changed_files=["src/asp/providers/claude_cli_provider.py"],
    commit_message="feat: add ClaudeCLIProvider"
)

# Output:
# DocumentationAnalysis(
#     required_updates=[
#         DocUpdate(
#             file="docs/Getting_Started.md",
#             section="Use Alternative LLM Providers",
#             priority="critical",
#             reason="New provider added but not documented",
#             suggested_content="..."
#         )
#     ],
#     coverage_score=0.85,
#     freshness_score=0.92
# )
```

#### Agent Integration Points

| Integration | Description |
|-------------|-------------|
| Post-commit hook | Analyze changes, warn if docs outdated |
| PR review | Add doc coverage check to review |
| CI pipeline | Fail if critical docs missing |
| MCP tool | Expose to Claude Code for suggestions |

### 2. Documentation Checklist for PRs

Add to PR template:

```markdown
## Documentation Checklist

- [ ] Updated relevant docs (check if changes affect):
  - [ ] `docs/Getting_Started.md` - New features, providers, CLI
  - [ ] `docs/API_Reference.md` - New classes, methods
  - [ ] `docs/Agents_Reference.md` - Agent changes
  - [ ] `README.md` - Major features
- [ ] Added/updated docstrings for public APIs
- [ ] Updated `KNOWLEDGE_BASE.md` if adding ADR
```

### 3. Documentation Coverage Metrics

Track documentation coverage similar to code coverage:

```python
@dataclass
class DocumentationCoverage:
    """Track what's documented vs what exists."""

    # Code entities
    public_classes: int
    documented_classes: int

    public_functions: int
    documented_functions: int

    providers: int
    documented_providers: int

    agents: int
    documented_agents: int

    # Calculated
    @property
    def coverage_pct(self) -> float:
        total = (self.public_classes + self.public_functions +
                 self.providers + self.agents)
        documented = (self.documented_classes + self.documented_functions +
                     self.documented_providers + self.documented_agents)
        return (documented / total * 100) if total > 0 else 100.0
```

### 4. Freshness Tracking

Track when docs were last updated vs code:

```python
@dataclass
class DocumentationFreshness:
    """Track doc freshness relative to code."""

    doc_file: str
    doc_last_modified: datetime

    related_code_files: list[str]
    code_last_modified: datetime

    @property
    def is_stale(self) -> bool:
        """Doc is stale if code changed after doc."""
        return self.code_last_modified > self.doc_last_modified

    @property
    def staleness_days(self) -> int:
        """Days since code changed without doc update."""
        if not self.is_stale:
            return 0
        return (self.code_last_modified - self.doc_last_modified).days
```

## Implementation Phases

### Phase 1: Documentation Mapping (This Session)
- [x] Create ADR 016
- [ ] Define doc-to-code mapping rules
- [ ] Create `docs/DOCUMENTATION_MAP.md`

### Phase 2: DocumentationAgent Core
- [ ] Create `src/asp/agents/documentation_agent.py`
- [ ] Implement `analyze()` method
- [ ] Implement `suggest()` method
- [ ] Add unit tests

### Phase 3: Integration
- [ ] Add to MCP server tools
- [ ] Create pre-commit hook (optional warning)
- [ ] Add to PR template
- [ ] Create `/docs` skill for Claude Code

### Phase 4: Metrics & Reporting
- [ ] Implement coverage calculation
- [ ] Implement freshness tracking
- [ ] Add to session summary template
- [ ] Create dashboard/report

## DocumentationAgent Specification

### Input Models

```python
@dataclass
class DocumentationInput:
    """Input for DocumentationAgent."""

    # What changed
    changed_files: list[str]
    commit_message: str | None = None

    # Context
    doc_mapping: dict[str, list[str]] | None = None  # code pattern -> doc files

    # Mode
    mode: Literal["analyze", "suggest", "apply"] = "analyze"
```

### Output Models

```python
@dataclass
class DocUpdate:
    """A suggested documentation update."""

    file: str
    section: str | None
    priority: Literal["critical", "recommended", "optional"]
    reason: str
    suggested_content: str | None = None

@dataclass
class DocumentationAnalysis:
    """Analysis of documentation needs."""

    required_updates: list[DocUpdate]
    coverage_score: float  # 0-1
    freshness_score: float  # 0-1

    # Detailed breakdown
    undocumented_entities: list[str]
    stale_docs: list[str]
```

### Prompts

```python
ANALYZE_PROMPT = """
You are a documentation analyst. Given the following code changes,
identify which documentation files need to be updated.

## Changed Files
{changed_files}

## Commit Message
{commit_message}

## Documentation Mapping
{doc_mapping}

## Current Documentation
{current_docs}

Analyze and return:
1. Which docs need updates (critical/recommended/optional)
2. What sections need changes
3. Why the update is needed
"""

SUGGEST_PROMPT = """
You are a technical writer. Generate documentation updates for:

## File to Update
{doc_file}

## Section to Update
{section}

## Code Context
{code_context}

## Existing Content
{existing_content}

Write clear, concise documentation that:
1. Explains the feature/change
2. Includes usage examples
3. Matches existing doc style
"""
```

## Decision

**Chosen Approach:** Implement DocumentationAgent with phased rollout

### Rationale

1. **Agent-based** - Fits existing architecture, reuses LLM capabilities
2. **Non-blocking** - Start with warnings, not hard failures
3. **Incremental** - Can add stricter enforcement over time
4. **Integrated** - Works with existing PR/session workflow

### Trade-offs

| Approach | Pros | Cons |
|----------|------|------|
| Manual checklist only | Simple, no code | Easy to ignore |
| Hard CI failure | Forces compliance | Blocks legitimate PRs |
| **Agent + warnings** | Smart suggestions, non-blocking | Requires LLM calls |
| Full automation | Zero effort | May generate poor docs |

## Success Criteria

| Metric | Target | Measurement |
|--------|--------|-------------|
| Doc coverage | >90% | Public entities documented |
| Freshness | <7 days | Max staleness for critical docs |
| PR compliance | >80% | PRs update docs when needed |
| User feedback | Positive | Docs are findable/useful |

## Open Questions

1. **Enforcement level** - Warning only, or block PRs?
2. **LLM cost** - Run on every commit, or periodic?
3. **Scope** - All docs, or just user-facing?

---

**Status:** Draft
**Next Steps:**
1. Review and discuss approach
2. Create documentation mapping
3. Implement DocumentationAgent Phase 1
