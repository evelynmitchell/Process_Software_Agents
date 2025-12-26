# Documentation Map

This file defines the mapping between code areas and documentation files.
Used by the DocumentationAgent to identify which docs need updates when code changes.

## Code-to-Documentation Mapping

### Providers (`src/asp/providers/`)

| Code Pattern | Documentation Files | Sections |
|--------------|---------------------|----------|
| `*_provider.py` | `docs/Getting_Started.md` | "Use Alternative LLM Providers" |
| `registry.py` | `docs/Getting_Started.md` | "Available providers" table |
| `base.py` | `docs/API_Reference.md` | "LLMProvider Interface" |
| `errors.py` | `docs/API_Reference.md` | "Provider Errors" |

### Agents (`src/asp/agents/`)

| Code Pattern | Documentation Files | Sections |
|--------------|---------------------|----------|
| `*_agent.py` | `docs/Agents_Reference.md` | Agent-specific section |
| `base_agent.py` | `docs/API_Reference.md` | "BaseAgent" |
| `code_reviews/*.py` | `docs/Agents_Reference.md` | "Code Review Agents" |
| `reviews/*.py` | `docs/Agents_Reference.md` | "Design Review Agents" |

### CLI (`src/asp/cli/`)

| Code Pattern | Documentation Files | Sections |
|--------------|---------------------|----------|
| `main.py` | `docs/Getting_Started.md` | "CLI Usage" |
| `beads_commands.py` | `docs/Getting_Started.md` | "Beads Planning" |

### Orchestrators (`src/asp/orchestrators/`)

| Code Pattern | Documentation Files | Sections |
|--------------|---------------------|----------|
| `*.py` | `docs/API_Reference.md` | "Orchestrators" |
| `*.py` | `README.md` | "Quick Example" (if API changes) |

### Models (`src/asp/models/`)

| Code Pattern | Documentation Files | Sections |
|--------------|---------------------|----------|
| `*.py` | `docs/API_Reference.md` | "Data Models" |

### MCP Server (`src/asp/mcp/`)

| Code Pattern | Documentation Files | Sections |
|--------------|---------------------|----------|
| `server.py` | `docs/Developer_Guide.md` | "MCP Integration" |
| `tools.py` | `docs/Developer_Guide.md` | "Available MCP Tools" |

### Design Decisions (`design/`)

| Code Pattern | Documentation Files | Sections |
|--------------|---------------------|----------|
| `ADR_*.md` | `docs/KNOWLEDGE_BASE.md` | ADR index table |

## Priority Rules

When code changes, documentation updates have these priorities:

### Critical (Must Update)
- New public class or function added
- New provider added
- New agent added
- API signature changed
- New CLI command added

### Recommended (Should Update)
- Behavior change in existing feature
- New configuration option
- New error type added
- Performance characteristics changed

### Optional (Nice to Have)
- Internal refactoring
- Test changes only
- Comment/docstring improvements
- Dependency updates

## Freshness Thresholds

| Doc Type | Max Staleness |
|----------|---------------|
| Getting_Started.md | 7 days |
| API_Reference.md | 14 days |
| README.md | 30 days |
| ADR_*.md | N/A (immutable once accepted) |

## Validation Commands

```bash
# Check which docs might be stale
git log --name-only --since="7 days ago" -- src/asp/providers/*.py

# List undocumented providers
diff <(ls src/asp/providers/*_provider.py | xargs -I{} basename {} _provider.py) \
     <(grep -oP '`\w+`(?= \|)' docs/Getting_Started.md | tr -d '`')
```

## DocumentationAgent Integration

The DocumentationAgent uses this mapping to:

1. **Analyze** - Given changed files, identify affected docs
2. **Prioritize** - Determine update priority
3. **Suggest** - Generate content for missing sections
4. **Report** - Track coverage and freshness metrics

Example query:
```python
# What docs need updates for this change?
mapping.get_affected_docs(["src/asp/providers/claude_cli_provider.py"])
# Returns: [("docs/Getting_Started.md", "Use Alternative LLM Providers", "critical")]
```
