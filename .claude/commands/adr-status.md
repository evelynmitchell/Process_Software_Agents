# ADR Status Command

Generate a current status report of all Architectural Decision Records (ADRs).

## Instructions

1. **Find all ADR files:**
   - Search in `design/` directory for files matching `ADR_*.md`
   - Also check `design/Archive/` for completed ADRs

2. **Parse each ADR for status:**
   - Look for "Status:" or "## Status" sections
   - Look for phase completion indicators (e.g., "Phase 1: Complete", "[x]", "Done")
   - Count total phases and completed phases

3. **Categorize ADRs:**
   - **Complete:** All phases done
   - **In Progress:** Some phases done
   - **Draft:** No phases implemented yet
   - **Archived:** Moved to Archive folder

4. **Generate status table:**

```markdown
| ADR | Title | Status | Progress | Next Action |
|-----|-------|--------|----------|-------------|
| 001 | Workspace Isolation | Complete | 1/1 | - |
| 006 | Repair Workflow | Complete | 5/5 | - |
| 010 | Multi-LLM Providers | In Progress | 2/14 | Phase 3: OpenRouter |
```

5. **Calculate summary metrics:**
   - Total ADRs
   - Completed count
   - In-progress count
   - Draft count

## Output Format

Provide:
1. The status table sorted by ADR number
2. Summary metrics
3. Recommended next ADR to work on (based on priority and dependencies)
