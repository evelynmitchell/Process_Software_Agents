# Hash-Based ID Migration Analysis

**Date:** 2025-12-16
**Session:** 1
**Related:** ADR 009 (Beads and Planning Agent Integration)
**Branch:** `feature/hash-based-ids`

## Executive Summary

This document analyzes the current codebase to identify all changes required to migrate from sequential IDs (e.g., `SU-001`, `ISSUE-001`) to hash-based IDs (e.g., `bd-a3f42`).

**Key Finding:** Beads already uses hash-based IDs. The migration primarily affects ASP agent models and their associated tests.

---

## Current ID Patterns

### 1. Beads IDs (Already Hash-Based)

**Location:** `src/asp/utils/beads.py:141-147`

```python
uid = str(uuid.uuid4())
hash_object = hashlib.sha256(uid.encode())
hex_dig = hash_object.hexdigest()
short_hash = hex_dig[:5]  # 5 chars
issue_id = f"bd-{short_hash}"
```

**Format:** `bd-{5-char-hex}` (e.g., `bd-a3f42`)

**Status:** No changes needed for Beads itself.

---

### 2. Semantic Unit IDs (SU-xxx)

**Location:** `src/asp/models/planning.py:81-85`

```python
unit_id: str = Field(
    ...,
    description="Unique unit identifier (e.g., 'SU-001')",
    pattern=r"^SU-\d{3}$",
)
```

**Validation:** Field-level regex pattern `^SU-\d{3}$`

**Generation:** LLM-generated via prompt instructions

**Used by:**
- Planning Agent outputs
- Design Agent (references via `semantic_unit_id`)
- Code Agent (references via `semantic_unit_id`)
- All downstream agents

**Impact:** HIGH - Core ID used throughout the pipeline

---

### 3. Design Issue IDs (ISSUE-xxx)

**Location:** `src/asp/models/design_review.py:21-25, 74-86`

```python
issue_id: str = Field(
    ...,
    description="Unique identifier for the issue (e.g., 'ISSUE-001')",
    pattern=r"^ISSUE-\d{3}$",
)

@field_validator("issue_id")
@classmethod
def validate_issue_id(cls, v: str) -> str:
    if not v.startswith("ISSUE-"):
        raise ValueError("Issue ID must start with 'ISSUE-'")
    num = int(v.split("-")[1])
    if num < 1 or num > 999:
        raise ValueError("Issue number must be between 001 and 999")
    return v
```

**Validation:**
- Field-level regex pattern
- Custom field_validator with range check (001-999)

**Generation:**
- LLM generates initial IDs
- **Orchestrator OVERWRITES** with sequential IDs (`src/asp/agents/design_review_orchestrator.py:460`)

**Impact:** MEDIUM - Isolated to design review phase

---

### 4. Design Improvement IDs (IMPROVE-xxx)

**Location:** `src/asp/models/design_review.py:109-112, 150-162`

```python
suggestion_id: str = Field(
    ...,
    description="Unique identifier for the suggestion (e.g., 'IMPROVE-001')",
    pattern=r"^IMPROVE-\d{3}$",
)
```

**Validation:** Same pattern as ISSUE-xxx

**Generation:** Orchestrator regenerates (`design_review_orchestrator.py:470`)

**Impact:** MEDIUM - Linked to ISSUE-xxx via `related_issue_id`

---

### 5. Code Issue IDs (CODE-ISSUE-xxx)

**Location:** `src/asp/models/code_review.py:24-28, 103-115`

```python
issue_id: str = Field(
    ...,
    description="Unique identifier for the issue (e.g., 'CODE-ISSUE-001')",
    pattern=r"^CODE-ISSUE-\d{3}$",
)
```

**Validation:**
- Field-level regex pattern
- Custom field_validator with range check

**Generation:** Orchestrator regenerates (`code_review_orchestrator.py:473`)

**Impact:** MEDIUM - Isolated to code review phase

---

### 6. Code Improvement IDs (CODE-IMPROVE-xxx)

**Location:** `src/asp/models/code_review.py:143-146, 193-205`

```python
suggestion_id: str = Field(
    ...,
    description="Unique identifier for the suggestion (e.g., 'CODE-IMPROVE-001')",
    pattern=r"^CODE-IMPROVE-\d{3}$",
)
```

**Validation:** Same pattern as CODE-ISSUE-xxx

**Generation:** Orchestrator regenerates (`code_review_orchestrator.py:483`)

**Impact:** MEDIUM - Linked to CODE-ISSUE-xxx

---

### 7. Task IDs (No Format Enforced)

**Location:** `src/asp/models/planning.py:24-28`

```python
task_id: str = Field(
    ...,
    description="Unique task identifier (e.g., 'TASK-2025-001')",
    min_length=1,
)
```

**Validation:** Only `min_length=1` - accepts any string

**Generation:** User-provided at CLI

**Impact:** LOW - No pattern validation to change

---

## Required Code Changes

### Phase 1: Add Hash ID Generation Utility

**File:** `src/asp/utils/id_generation.py` (NEW)

```python
"""Hash-based ID generation utilities."""

import hashlib
import uuid

def generate_hash_id(prefix: str = "id", length: int = 5) -> str:
    """Generate a unique hash-based ID.

    Args:
        prefix: ID prefix (e.g., 'su', 'issue', 'improve')
        length: Number of hex characters (default 5)

    Returns:
        ID in format '{prefix}-{hash}' (e.g., 'su-a3f42')
    """
    uid = str(uuid.uuid4())
    hash_digest = hashlib.sha256(uid.encode()).hexdigest()
    return f"{prefix}-{hash_digest[:length]}"

def generate_semantic_unit_id() -> str:
    """Generate a semantic unit ID."""
    return generate_hash_id("su")

def generate_issue_id() -> str:
    """Generate a design issue ID."""
    return generate_hash_id("issue")

def generate_code_issue_id() -> str:
    """Generate a code issue ID."""
    return generate_hash_id("code-issue")

def generate_improvement_id() -> str:
    """Generate an improvement suggestion ID."""
    return generate_hash_id("improve")

def generate_code_improvement_id() -> str:
    """Generate a code improvement suggestion ID."""
    return generate_hash_id("code-improve")
```

---

### Phase 2: Update Model Validations

#### 2.1 SemanticUnit (planning.py:81-85)

**Current:**
```python
unit_id: str = Field(
    ...,
    pattern=r"^SU-\d{3}$",
)
```

**New:**
```python
unit_id: str = Field(
    ...,
    pattern=r"^su-[a-f0-9]{5}$",
    description="Unique unit identifier (e.g., 'su-a3f42')",
)
```

#### 2.2 DesignIssue (design_review.py:21-25, 74-86)

**Current Pattern:** `^ISSUE-\d{3}$`

**New Pattern:** `^issue-[a-f0-9]{5}$`

**Also update:** `field_validator` to remove range check

#### 2.3 ImprovementSuggestion (design_review.py:109-162)

**Current Pattern:** `^IMPROVE-\d{3}$`

**New Pattern:** `^improve-[a-f0-9]{5}$`

**Also update:** `related_issue_id` pattern

#### 2.4 CodeIssue (code_review.py:24-28, 103-115)

**Current Pattern:** `^CODE-ISSUE-\d{3}$`

**New Pattern:** `^code-issue-[a-f0-9]{5}$`

#### 2.5 CodeImprovementSuggestion (code_review.py:143-205)

**Current Pattern:** `^CODE-IMPROVE-\d{3}$`

**New Pattern:** `^code-improve-[a-f0-9]{5}$`

---

### Phase 3: Update Orchestrators

#### 3.1 Design Review Orchestrator

**File:** `src/asp/agents/design_review_orchestrator.py:457-470`

**Current:**
```python
for i, issue in enumerate(deduplicated_issues, 1):
    old_id = issue.get("issue_id")
    new_id = f"ISSUE-{i:03d}"
    ...
```

**New:**
```python
from asp.utils.id_generation import generate_issue_id, generate_improvement_id

for issue in deduplicated_issues:
    old_id = issue.get("issue_id")
    new_id = generate_issue_id()
    ...
```

#### 3.2 Code Review Orchestrator

**File:** `src/asp/agents/code_review_orchestrator.py:470-483`

**Current:**
```python
new_id = f"CODE-ISSUE-{i:03d}"
```

**New:**
```python
from asp.utils.id_generation import generate_code_issue_id, generate_code_improvement_id

new_id = generate_code_issue_id()
```

---

### Phase 4: Update Prompts

**Files affected:** 25+ prompt templates in `src/asp/prompts/`

Key prompts to update:
1. `planning_agent_v1_decomposition.txt:177` - SU-XXX instructions
2. `design_review_agent_v1_review.txt:204-206` - ISSUE-XXX instructions
3. All specialist agent prompts

**Change:** Update instructions from "use SU-001, SU-002" to "use su-{hash} format"

**Note:** Since orchestrators regenerate IDs anyway, prompt changes are optional but recommended for consistency.

---

## Test Changes Required

### Summary Table

| Pattern | Test Files | Test Methods | Validation Tests | Sample Data Tests |
|---------|-----------|--------------|------------------|-------------------|
| `SU-\d{3}` | 31 | ~80 | ~20 (explicit) | ~60 |
| `ISSUE-\d{3}` | 15 | ~35 | ~11 | ~24 |
| `IMPROVE-\d{3}` | 13 | ~20 | ~8 | ~12 |
| `CODE-ISSUE-\d{3}` | 5 | ~8 | ~4 | ~4 |
| `CODE-IMPROVE-\d{3}` | 5 | ~8 | ~4 | ~4 |
| **Total** | **69** | **~151** | **~47** | **~104** |

### Key Test Files

1. **`tests/unit/conftest.py`** - All factory fixtures
   - `make_semantic_unit(unit_id="SU-001")` -> `make_semantic_unit(unit_id="su-a1b2c")`
   - `make_design_issue(issue_id="ISSUE-001")` -> `make_design_issue(issue_id="issue-a1b2c")`
   - etc.

2. **`tests/unit/test_models/test_planning_models.py`**
   - Update valid ID examples
   - Update invalid ID test cases

3. **`tests/unit/test_models/test_design_review_models.py`**
   - Update pattern validation tests

4. **`tests/unit/test_models/test_code_review_models.py`**
   - Update pattern validation tests

5. **`tests/unit/test_agents/test_*_orchestrator.py`**
   - Update ID normalization assertions

---

## Migration Strategy

### Option A: Big Bang (All at Once)

**Pros:**
- Clean cut, no backward compatibility code
- Simpler codebase post-migration

**Cons:**
- High risk, many files changed
- Difficult to rollback

### Option B: Gradual (Recommended)

**Phase 1:** Add new ID generation utility (no breaking changes)
**Phase 2:** Update models to accept BOTH old and new patterns
**Phase 3:** Update orchestrators to generate new format
**Phase 4:** Update tests
**Phase 5:** Remove old pattern support

**Pros:**
- Lower risk
- Easy rollback at each phase
- Can run e2e tests at each phase

**Cons:**
- Temporary complexity with dual support

---

## Backward Compatibility

### Existing Artifacts

Old artifacts using `SU-001` format will exist in:
- `artifacts/{task_id}/plan.json`
- `artifacts/{task_id}/design.json`
- etc.

**Solution:** Keep artifact I/O agnostic to ID format (already is)

### Existing Beads Issues

Beads issues already use `bd-{hash}` format - no migration needed.

---

## Recommended Next Steps

1. **Create `id_generation.py` utility module**
2. **Update model patterns to accept new format**
3. **Update orchestrator ID generation**
4. **Run full test suite to identify failures**
5. **Update test fixtures and assertions**
6. **Run e2e tests to validate pipeline**
7. **Update prompt templates (optional)**

---

## Files to Change (Complete List)

### Source Files (13 files)

| File | Change Type | Priority |
|------|-------------|----------|
| `src/asp/utils/id_generation.py` | NEW | P0 |
| `src/asp/models/planning.py` | MODIFY | P0 |
| `src/asp/models/design_review.py` | MODIFY | P0 |
| `src/asp/models/code_review.py` | MODIFY | P0 |
| `src/asp/agents/design_review_orchestrator.py` | MODIFY | P1 |
| `src/asp/agents/code_review_orchestrator.py` | MODIFY | P1 |
| `src/asp/agents/planning_agent.py` | MODIFY | P1 |
| `src/asp/utils/beads.py` | NO CHANGE | - |
| `src/asp/utils/artifact_io.py` | NO CHANGE | - |

### Test Files (Primary - 6 files)

| File | Change Type |
|------|-------------|
| `tests/unit/conftest.py` | MODIFY |
| `tests/unit/test_models/test_planning_models.py` | MODIFY |
| `tests/unit/test_models/test_design_review_models.py` | MODIFY |
| `tests/unit/test_models/test_code_review_models.py` | MODIFY |
| `tests/unit/test_agents/test_design_review_orchestrator.py` | MODIFY |
| `tests/unit/test_agents/test_code_review_orchestrator.py` | MODIFY |

### Test Files (Secondary - 63+ files)

All files using fixtures from conftest.py will automatically get new ID format once fixtures are updated.

### Prompt Files (Optional - 25+ files)

Located in `src/asp/prompts/` - update for consistency but not strictly required since orchestrators regenerate IDs.

---

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Breaking existing tests | HIGH | MEDIUM | Gradual rollout, run tests at each phase |
| ID collision (hash) | LOW | LOW | 5-char hex = 1M+ unique IDs |
| LLM generates wrong format | MEDIUM | LOW | Orchestrators regenerate anyway |
| Backward compat issues | MEDIUM | MEDIUM | Keep artifact I/O format-agnostic |

---

## Estimated Effort

| Task | Files | Estimated LOC |
|------|-------|---------------|
| New utility module | 1 | ~50 |
| Model updates | 3 | ~100 |
| Orchestrator updates | 2 | ~50 |
| Test fixture updates | 1 | ~50 |
| Test assertion updates | 5 | ~200 |
| **Total** | **12** | **~450** |

---

## Appendix: ID Format Comparison

| Entity | Old Format | New Format | Example |
|--------|-----------|------------|---------|
| Semantic Unit | `SU-001` | `su-a3f42` | Planning output |
| Design Issue | `ISSUE-001` | `issue-b7c91` | Design review |
| Design Improvement | `IMPROVE-001` | `improve-d4e82` | Design review |
| Code Issue | `CODE-ISSUE-001` | `code-issue-f1a23` | Code review |
| Code Improvement | `CODE-IMPROVE-001` | `code-improve-c9d45` | Code review |
| Beads Issue | `bd-a3f42` | `bd-a3f42` | No change |
| Task ID | `TASK-001` | (unchanged) | User-provided |
