# Proposal: ASP Memory and Learning Strategy

## 1. The Problem
- **Memory Overload:** The `Summary/` directory is growing linearly. Reading all files consumes context window and confuses attention.
- **Open Loop Learning:** We collect metrics (Session Summaries) and insights (Weekly Reflections), but there is no explicit mechanism to *enforce* these learnings in future sessions.
- **Signal vs. Noise:** Difficulty distinguishing between "what happened today" (episodic memory) and "how we should work" (semantic memory).

## 2. Memory Management Strategy ("Context Tiering")

We will implement a 3-tier memory architecture to manage context load:

### Tier 1: Working Memory (Episodic - Short Term)
- **Source:** The current Session Summary being written.
- **Retention:** Active only during the session.
- **Action:** Discard details after session, keep only high-level outcome in the summary file.

### Tier 2: Recent Context (Episodic - Medium Term)
- **Source:** The last 3-5 `Summary/summaryYYYYMMDD.md` files.
- **Purpose:** Continuity of immediate tasks.
- **Action:** Agent reads these to know "what did we just do?".

### Tier 3: Long-Term Memory (Semantic - Evergreen)
- **Source:** `docs/KNOWLEDGE_BASE.md` (New File) and `Claude.md`.
- **Purpose:** Rules, Patterns, Architecture, "How to do things".
- **Action:**
    - `Claude.md`: Stores **Behavioral Instructions** (e.g., "Always run setup script").
    - `KNOWLEDGE_BASE.md`: Stores **System Facts & Patterns** (e.g., "The specific way we test FastHTML routes").

**Protocol Change:**
The Agent should *not* list/read all files in `Summary/`. Instead, read `Summary/weekly_reflection_LATEST.md` and the last 3 daily summaries.

## 3. The Learning Loop (Bootstrap Learning)

To turn metrics into improved process, we introduce a **Process Promotion Cycle**:

### Step 1: Capture (Daily)
- Continue writing Session Summaries.
- **New Section:** Add a `## Candidate for Evergreen` section to the template.
- *Criteria:* "Did I struggle with something today that I figured out?" or "Did I find a better way to do X?"

### Step 2: Synthesize (Weekly)
- During the Weekly Reflection, review the `## Candidate for Evergreen` sections from the week's summaries.
- **Filter:**
    - *Discard:* One-off bugs, temporary workarounds.
    - *Keep:* Architectural patterns, testing realizations, repeated pitfalls.

### Step 3: Promote (Weekly)
- Move the "Keep" items to one of two places:
    1. **`Claude.md`**: If it is an instruction for the Agent (e.g., "Always use `git diff` instead of `git status`").
    2. **`docs/KNOWLEDGE_BASE.md`**: If it is information about the System (e.g., "FastHTML testing requires patching imports, not definitions").

### Step 4: Prune (Monthly)
- Review `KNOWLEDGE_BASE.md` and `Claude.md`.
- Remove instructions that have become muscle memory or are no longer relevant due to refactoring.

## 4. Implementation Plan

1. **Create `docs/KNOWLEDGE_BASE.md`**: Initialize with high-value insights from the latest Weekly Reflection (e.g., the FastHTML testing gotcha).
2. **Update `Claude.md`**: Add the "Memory & Learning" protocol instructions.
3. **Update Session Template**: Add the `Candidate for Evergreen` section.
