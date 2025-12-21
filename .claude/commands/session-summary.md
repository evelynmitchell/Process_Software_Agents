# Session Summary Command

Start a new development session by loading context and creating a session summary file.

## Instructions

1. **Determine the session number:**
   - List existing summaries for today: `ls Summary/summary$(date +%Y%m%d).*.md 2>/dev/null | wc -l`
   - The new session number is (count + 1)

2. **Load tiered context (read these files):**
   - `docs/KNOWLEDGE_BASE.md` (Long-term Memory)
   - The latest `Summary/weekly_reflection_*.md` file (Recent Context)
   - The last 3 session summary files (Immediate Context)

3. **Review recent work:**
   - Summarize what was accomplished in the last 3 sessions
   - Note any pending items or blockers
   - Check the ADR status from the weekly reflection

4. **Create the new session summary:**
   - File: `Summary/summary{YYYYMMDD}.{N}.md` where N is the session number
   - Use the template from `design/SESSION_TEMPLATE.md` if it exists
   - Pre-populate:
     - Date and session number
     - Start commit hash (from `git rev-parse --short HEAD`)
     - Reference to previous session
     - Status: "In Progress"

5. **Display session context to user:**
   - Show the current ADR status table
   - List any pending items from previous sessions
   - Suggest potential focus areas based on recent work

## Output Format

After completing the above steps, provide:
- A brief summary of recent work
- The path to the new session summary file
- Current ADR status
- Suggested focus areas for this session
