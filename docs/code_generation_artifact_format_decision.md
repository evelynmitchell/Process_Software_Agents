# ADR: Code Generation Artifact Format and Structure

**Status:** Proposed
**Date:** 2025-11-20
**Deciders:** ASP Development Team
**Related Issues:** CODE-AGENT-JSON-001 (JSON parsing failures in E2E tests)
**Related Docs:**
- `docs/debugging/code_agent_json_parsing_issue.md`
- `docs/artifact_persistence_version_control_decision.md`

---

## Context and Problem Statement

The Code Agent currently fails E2E tests with `JSONDecodeError: Unterminated string` when generating code. The LLM must embed complete source code files (with docstrings, quotes, and special characters) inside JSON string values, but frequently fails to properly escape these characters, resulting in malformed JSON that cannot be parsed.

**Key observations:**
- Planning Agent (1-2KB JSON, simple data) - 0% failure rate
- Design Agent (5-10KB JSON, structured data) - 0% failure rate
- Code Agent (20-50KB JSON, complete source files) - ~50% failure rate

**Root cause:** JSON is fundamentally unsuited for containing large blocks of source code due to escaping complexity. LLMs struggle to maintain character-level precision (escaping `"""`, `"`, `\`, etc.) across 20-50KB responses.

**Decision needed:** How should the Code Agent generate and structure code artifacts to ensure reliability?

---

## Decision Drivers

### Critical Requirements
- **Reliability:** Must work consistently (>95% success rate)
- **Debuggability:** Failures must be diagnosable with clear error messages
- **Performance:** Must complete within acceptable time/cost budgets
- **Maintainability:** Solution should be simple to understand and modify

### Important Factors
- **LLM token costs:** Each LLM call costs money (~$0.01-0.10 per call)
- **Response quality:** Smaller outputs generally have higher quality
- **Parsing robustness:** Must handle edge cases gracefully
- **Schema validation:** Should validate structure before processing
- **Integration:** Must work with existing artifact persistence system

### Nice-to-Have
- **Single LLM call:** Faster and simpler if possible
- **Backward compatibility:** Minimize changes to existing agents
- **Human readability:** Artifacts should be inspectable

---

## Options Considered

### Option 1: JSON Repair Layer (Quick Fix)

**Approach:** Pre-process LLM JSON response to fix common escaping errors before parsing.

**Implementation:**
```python
def repair_code_json(json_str: str) -> str:
    """Fix common JSON escaping errors in code content fields."""
    import re

    # Find "content" fields and repair unescaped quotes
    def fix_content_field(match):
        content = match.group(1)
        # Fix unescaped triple quotes
        content = content.replace('"""', r'\"\"\"')
        # Fix unescaped single quotes in docstrings
        content = re.sub(r'(?<!\\)"', r'\"', content)
        return f'"content": "{content}"'

    content_pattern = r'"content":\s*"((?:[^"\\]|\\.)*)"'
    return re.sub(content_pattern, fix_content_field, json_str, flags=re.DOTALL)

# In _generate_code():
json_str = extract_from_markdown(llm_response)
json_str = repair_code_json(json_str)  # ← Add repair layer
content = json.loads(json_str)
```

**Pros:**
- ✅ Quick to implement (30-60 minutes)
- ✅ No prompt changes needed
- ✅ No architectural changes
- ✅ Single LLM call (current cost)
- ✅ May fix 80%+ of current failures

**Cons:**
- ❌ Brittle (regex on massive strings)
- ❌ Won't catch all edge cases (nested quotes, complex escaping)
- ❌ May introduce new bugs (false positives in repair logic)
- ❌ Doesn't address root cause (LLM still generates bad JSON)
- ❌ Maintenance burden (need to add fixes for each new error pattern)

**Cost/Performance:**
- Implementation: 1 hour
- API cost: No change (~$0.50/task)
- Latency: +50-200ms for regex processing

**Risk Assessment:** Medium
- Risk: Regex fails on edge cases → still get JSON errors
- Risk: Repair logic corrupts valid JSON → new failures
- Mitigation: Extensive testing with known failure cases

---

### Option 2: Multi-Stage Generation (Manifest + Individual Files)

**Approach:** Split code generation into two phases:
1. **Manifest generation** - Small JSON with file list and metadata
2. **File generation** - Separate LLM call per file, returns raw code (no JSON)

**Implementation:**

**Phase 1 - Generate Manifest:**
```python
# Prompt: "Generate a file manifest (list of files to create)"
# Response: Small, simple JSON (no escaping issues)
{
  "task_id": "HW-001",
  "files": [
    {
      "file_path": "main.py",
      "file_type": "source",
      "description": "FastAPI application with /hello endpoint",
      "semantic_unit_id": "SU-001",
      "component_id": "COMP-001"
    },
    {
      "file_path": "tests/test_main.py",
      "file_type": "test",
      "description": "Unit tests for /hello endpoint",
      "semantic_unit_id": "SU-001",
      "component_id": "COMP-001"
    }
  ],
  "dependencies": ["fastapi==0.104.1", "pytest==7.4.3"],
  "setup_instructions": "pip install -r requirements.txt && uvicorn main:app"
}
```

**Phase 2 - Generate Each File:**
```python
generated_files = []

for file_meta in manifest['files']:
    # Separate LLM call for JUST this file's content
    # Returns RAW Python code, NO JSON wrapping
    prompt = f"""
Generate complete {file_meta['file_path']} based on:

Design: {design_spec}
Description: {file_meta['description']}
Standards: {coding_standards}

Return ONLY the complete file content, with no JSON wrapping.
"""

    file_content = llm.generate(prompt, max_tokens=4000)

    # No parsing needed - it's already raw code!
    generated_files.append({
        'path': file_meta['file_path'],
        'content': file_content,  # ← Raw string, no escaping issues
        'metadata': file_meta
    })

return GeneratedCode(files=generated_files, ...)
```

**Pros:**
- ✅ Eliminates JSON escaping problem entirely
- ✅ Smaller LLM responses (2-4KB per file vs. 50KB total)
- ✅ Higher quality code (LLM focuses on one file at a time)
- ✅ Granular error handling (retry individual files)
- ✅ Can parallelize file generation (async)
- ✅ Clear debugging (know exactly which file failed)

**Cons:**
- ❌ More LLM calls (10-15 calls vs. 1)
- ❌ Higher API cost (2-4x)
- ❌ Longer latency if sequential (can be mitigated with parallel calls)
- ❌ More complex orchestration logic
- ❌ Need to ensure consistency across files

**Cost/Performance:**
- Implementation: 4-6 hours (new prompts, orchestration logic, tests)
- API cost: ~$1.50-2.00/task (vs. ~$0.50 current)
- Latency: 120-180s if sequential, 30-60s if parallel (vs. ~90s current)
- Success rate: Expected >98% (eliminates main failure mode)

**Risk Assessment:** Low
- Risk: File generation inconsistencies → mismatched imports/types
- Mitigation: Validate file compatibility after generation
- Risk: Higher cost → budget concerns
- Mitigation: Measure actual cost, optimize prompt sizes

---

### Option 3: Custom Delimiter Format (No JSON)

**Approach:** Replace JSON with custom text delimiters for file boundaries.

**Implementation:**
```python
# LLM generates response like this:
"""
===FILE_START===
PATH: main.py
TYPE: source
SEMANTIC_UNIT: SU-001
COMPONENT: COMP-001
DESCRIPTION: FastAPI application with /hello endpoint
===CONTENT_START===
#!/usr/bin/env python3
"""
FastAPI Hello World Application.
"""
from fastapi import FastAPI

app = FastAPI()

@app.get("/hello")
async def hello():
    """Return greeting message."""
    return {"message": "Hello World"}
===CONTENT_END===

===FILE_START===
PATH: tests/test_main.py
TYPE: test
===CONTENT_START===
import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_hello_endpoint():
    response = client.get("/hello")
    assert response.status_code == 200
    assert "message" in response.json()
===CONTENT_END===

===METADATA===
DEPENDENCIES: fastapi==0.104.1, pytest==7.4.3
SETUP: pip install -r requirements.txt
===END===
"""

# Parsing:
def parse_delimited_response(response: str) -> GeneratedCode:
    files = []

    # Split by file boundaries
    file_blocks = response.split('===FILE_START===')[1:]

    for block in file_blocks:
        # Extract metadata from headers
        path = extract_field(block, 'PATH:')
        file_type = extract_field(block, 'TYPE:')
        description = extract_field(block, 'DESCRIPTION:')

        # Extract content between delimiters (no escaping!)
        content = extract_between(block, '===CONTENT_START===', '===CONTENT_END===')

        files.append(GeneratedFile(
            file_path=path,
            content=content.strip(),
            file_type=file_type,
            description=description
        ))

    # Extract metadata
    metadata_block = response.split('===METADATA===')[1].split('===END===')[0]
    dependencies = extract_field(metadata_block, 'DEPENDENCIES:').split(', ')

    return GeneratedCode(files=files, dependencies=dependencies, ...)
```

**Pros:**
- ✅ No JSON escaping issues
- ✅ Single LLM call (current cost ~$0.50/task)
- ✅ Human-readable format
- ✅ Simple parsing (regex + string splits)
- ✅ Can include any characters in content (no escaping needed)

**Cons:**
- ❌ Delimiter collision risk (what if code contains `===FILE_START===`?)
- ❌ Less structured than JSON (harder to validate)
- ❌ No schema validation (lose Pydantic benefits)
- ❌ Custom format (not standard like JSON/YAML)
- ❌ LLMs less familiar with custom formats (may hallucinate structure)

**Cost/Performance:**
- Implementation: 2-3 hours (new prompt, parsing logic, tests)
- API cost: No change (~$0.50/task)
- Latency: No change (~90s)
- Success rate: Expected >90% (eliminates escaping, but delimiter collision possible)

**Risk Assessment:** Medium
- Risk: Delimiter collision in generated code
- Mitigation: Use very unique delimiters (e.g., `===ASP_FILE_BOUNDARY_2025===`)
- Risk: LLM doesn't follow delimiter format correctly
- Mitigation: Clear examples in prompt, validation after parsing

---

### Option 4: YAML Format

**Approach:** Replace JSON with YAML, which has better multi-line string support.

**Implementation:**
```python
# LLM generates YAML:
"""
task_id: HW-001
project_id: PROJECT-HW-001
files:
  - file_path: main.py
    file_type: source
    semantic_unit_id: SU-001
    component_id: COMP-001
    description: FastAPI application with /hello endpoint
    content: |
      #!/usr/bin/env python3
      """
      FastAPI Hello World Application.
      """
      from fastapi import FastAPI

      app = FastAPI()

      @app.get("/hello")
      async def hello():
          """Return greeting message."""
          return {"message": "Hello World"}

  - file_path: tests/test_main.py
    file_type: test
    content: |
      import pytest
      from fastapi.testclient import TestClient
      from main import app

      def test_hello():
          client = TestClient(app)
          response = client.get("/hello")
          assert response.status_code == 200

dependencies:
  - fastapi==0.104.1
  - pytest==7.4.3

setup_instructions: |
  pip install -r requirements.txt
  uvicorn main:app --reload
"""

# Parsing:
import yaml

response_yaml = extract_from_markdown(llm_response)
data = yaml.safe_load(response_yaml)
code = GeneratedCode.model_validate(data)
```

**Pros:**
- ✅ Native multi-line string support (`|` block scalar)
- ✅ No escaping needed for quotes in content
- ✅ More readable than JSON for large text blocks
- ✅ Single LLM call (current cost)
- ✅ Standard format with library support

**Cons:**
- ❌ Indentation-sensitive (whitespace errors break parsing)
- ❌ LLMs less reliable with YAML vs. JSON
- ❌ YAML parsing errors harder to debug
- ❌ Inconsistent LLM indentation (especially for nested code)
- ❌ `yaml.safe_load()` security considerations

**Cost/Performance:**
- Implementation: 2-3 hours (prompt changes, YAML parsing, tests)
- API cost: No change (~$0.50/task)
- Latency: No change (~90s)
- Success rate: Expected ~70-80% (indentation errors common)

**Risk Assessment:** High
- Risk: LLM generates incorrect indentation → YAML parse errors
- Risk: Indentation errors hard to debug and fix automatically
- Mitigation: Detailed YAML examples in prompt, but LLMs still struggle

---

### Option 5: Hybrid (Manifest JSON + Delimited Files)

**Approach:** Combine structured JSON for metadata with delimited format for file contents.

**Implementation:**
```json
{
  "task_id": "HW-001",
  "project_id": "PROJECT-HW-001",
  "dependencies": ["fastapi==0.104.1", "pytest==7.4.3"],
  "setup_instructions": "pip install -r requirements.txt",
  "total_files": 2,
  "files_delimiter": "===FILE_CONTENT_BLOCK==="
}

===FILE_CONTENT_BLOCK===
PATH: main.py
TYPE: source
---
#!/usr/bin/env python3
"""FastAPI Hello World."""
from fastapi import FastAPI

app = FastAPI()

@app.get("/hello")
async def hello():
    return {"message": "Hello"}

===FILE_CONTENT_BLOCK===
PATH: tests/test_main.py
TYPE: test
---
import pytest
from fastapi.testclient import TestClient
from main import app

def test_hello():
    client = TestClient(app)
    response = client.get("/hello")
    assert response.status_code == 200
```

**Parsing:**
```python
# Extract JSON header
json_match = re.search(r'^({.*?})\n\n===', response, re.DOTALL)
metadata = json.loads(json_match.group(1))

# Extract file blocks
file_blocks = response.split('===FILE_CONTENT_BLOCK===')[1:]
files = []

for block in file_blocks:
    path_match = re.search(r'PATH: (.+)', block)
    type_match = re.search(r'TYPE: (.+)', block)
    content = block.split('---')[1].strip()

    files.append(GeneratedFile(
        file_path=path_match.group(1),
        file_type=type_match.group(1),
        content=content
    ))

return GeneratedCode(**metadata, files=files)
```

**Pros:**
- ✅ JSON for structured metadata (validated with Pydantic)
- ✅ Delimiters for file content (no escaping)
- ✅ Best of both worlds
- ✅ Single LLM call

**Cons:**
- ❌ Two parsing strategies in one response
- ❌ More complex parsing logic
- ❌ Still has delimiter collision risk
- ❌ LLM must follow two different formats

**Cost/Performance:**
- Implementation: 3-4 hours
- API cost: No change (~$0.50/task)
- Latency: No change (~90s)
- Success rate: Expected ~85-90%

**Risk Assessment:** Medium
- Risk: LLM mixes formats or generates invalid structure
- Mitigation: Clear prompt with examples

---

## Decision Matrix

| Criteria | Option 1: JSON Repair | Option 2: Multi-Stage | Option 3: Delimiters | Option 4: YAML | Option 5: Hybrid |
|----------|----------------------|----------------------|---------------------|---------------|------------------|
| **Reliability** | 🟡 80-85% | 🟢 98%+ | 🟢 90-95% | 🔴 70-80% | 🟡 85-90% |
| **Implementation Time** | 🟢 1 hour | 🔴 4-6 hours | 🟢 2-3 hours | 🟢 2-3 hours | 🟡 3-4 hours |
| **API Cost** | 🟢 No change | 🔴 2-4x higher | 🟢 No change | 🟢 No change | 🟢 No change |
| **Latency** | 🟢 No change | 🟡 Parallel: OK | 🟢 No change | 🟢 No change | 🟢 No change |
| **Maintainability** | 🔴 Brittle regex | 🟢 Clear separation | 🟢 Simple parsing | 🔴 Indent issues | 🟡 Dual formats |
| **Debuggability** | 🔴 Opaque repairs | 🟢 Clear file errors | 🟢 Clear structure | 🔴 Hard to debug | 🟡 Moderate |
| **Schema Validation** | 🟢 Full Pydantic | 🟢 Full Pydantic | 🔴 Limited | 🟢 Full Pydantic | 🟢 Partial |
| **LLM Familiarity** | 🟢 JSON (familiar) | 🟢 JSON + plain text | 🟡 Custom format | 🟡 YAML (less used) | 🟡 Mixed |
| **Risk Level** | 🟡 Medium | 🟢 Low | 🟡 Medium | 🔴 High | 🟡 Medium |

**Legend:** 🟢 Excellent | 🟡 Acceptable | 🔴 Poor

---

## Recommended Decision

### Short-Term (Immediate): **Option 1 - JSON Repair Layer**

**Rationale:**
- Unblocks E2E tests quickly (1 hour implementation)
- Minimal risk to existing system
- Can implement today and validate tomorrow
- Buys time to implement long-term solution properly

**Implementation Plan:**
1. Add `repair_code_json()` function to `code_agent.py`
2. Apply repair before JSON parsing in `_generate_code()`
3. Add unit tests with known failure cases
4. Test on 5-10 different code generation tasks
5. Document limitations and failure modes

**Success Criteria:**
- E2E tests pass >80% of the time
- No new test failures introduced
- Can diagnose remaining failures clearly

---

### Long-Term (Next Sprint): **Option 2 - Multi-Stage Generation**

**Rationale:**
- **Highest reliability** (>98% expected)
- **Best code quality** (smaller, focused LLM calls)
- **Eliminates root cause** (no JSON escaping needed)
- **Better debugging** (granular error handling)
- Cost increase justified by reliability improvement

**Why not other options:**
- **Option 3 (Delimiters):** Delimiter collision risk, loses schema validation
- **Option 4 (YAML):** LLMs struggle with indentation, lower reliability
- **Option 5 (Hybrid):** Complexity without reliability gain of Option 2

**Implementation Plan:**

**Phase 1 - Manifest Generation (Week 1):**
1. Create new prompt: `code_agent_v2_manifest.txt`
2. Implement `_generate_file_manifest()` method
3. Test manifest generation on 10+ tasks
4. Validate JSON structure with Pydantic

**Phase 2 - File Generation (Week 1-2):**
1. Create new prompt: `code_agent_v2_file_generation.txt`
2. Implement `_generate_file_content()` method
3. Add retry logic for individual file failures
4. Test file generation on 10+ tasks

**Phase 3 - Orchestration (Week 2):**
1. Refactor `_generate_code()` to coordinate both phases
2. Implement parallel file generation (asyncio)
3. Add file consistency validation
4. Update telemetry to track per-file costs

**Phase 4 - Testing & Validation (Week 2-3):**
1. Run E2E tests 20+ times to measure reliability
2. Compare code quality vs. single-call approach
3. Measure actual cost increase
4. Document new architecture

**Rollout Strategy:**
1. Deploy behind feature flag: `USE_MULTI_STAGE_CODE_GEN`
2. Run both old and new approaches in parallel (A/B test)
3. Compare reliability and cost metrics
4. Gradual rollout: 10% → 50% → 100% of tasks
5. Deprecate Option 1 (JSON repair) after validation

**Success Criteria:**
- Reliability: >95% success rate on E2E tests
- Quality: Code passes linting and tests without changes
- Performance: <60s latency with parallel generation
- Cost: <$3.00 per task (acceptable given reliability)

---

## Consequences

### Immediate (Option 1 - JSON Repair):

**Positive:**
- ✅ E2E tests unblocked today
- ✅ No architectural changes needed
- ✅ Can continue development on other features

**Negative:**
- ❌ Technical debt (brittle regex solution)
- ❌ Will still have occasional failures (~15-20%)
- ❌ Need to maintain repair logic as new patterns emerge

**Neutral:**
- ℹ️ Temporary solution, will be replaced

### Long-Term (Option 2 - Multi-Stage):

**Positive:**
- ✅ Highest reliability (>95% success rate)
- ✅ Better code quality (focused generation)
- ✅ Easier debugging (granular errors)
- ✅ Scalable (add more file types easily)
- ✅ Foundation for future improvements (streaming, caching)

**Negative:**
- ❌ Higher API costs (2-4x, ~$1.50-2.00/task)
- ❌ More complex orchestration logic
- ❌ Need to maintain two prompts (manifest + file)
- ❌ Implementation effort (4-6 hours)

**Neutral:**
- ℹ️ Code Agent becomes more complex but more robust
- ℹ️ Sets precedent for other multi-stage agents

---

## Alternatives Rejected

### Base64 Encoding (Not Considered)
**Why rejected:**
- Increases token usage 33% (higher cost)
- LLMs poor at generating valid base64
- Debugging nightmare (can't read content)
- Complexity without reliability gain

### Single-Call JSON with Schema-Guided Generation (Future)
**Why deferred:**
- Requires Anthropic API tool use (not available for all models)
- Significant refactor of agent architecture
- Uncertain if it actually improves reliability
- Can revisit after Option 2 if still having issues

### Template-Based Generation (Out of Scope)
**Why rejected:**
- Only works for highly standardized patterns
- Limits flexibility and creativity
- Not suitable for diverse task types
- Would require large template library

---

## Validation and Monitoring

### Metrics to Track:

**Reliability Metrics:**
- Code Agent success rate (target: >95%)
- JSON parsing error rate (target: <5%)
- File generation failure rate per file type

**Quality Metrics:**
- Generated code passes linting (target: 100%)
- Generated tests pass without modification (target: >90%)
- Code review agent approval rate (target: >80%)

**Cost Metrics:**
- Average cost per task (baseline: $0.50, acceptable: <$3.00)
- Cost per file generated
- Cost per line of code

**Performance Metrics:**
- End-to-end latency (target: <120s)
- Time per file generation (target: <15s)
- Parallel vs. sequential speedup ratio

### Validation Plan:

**Week 1 - Baseline Measurement:**
- Run current system 50 times, measure all metrics
- Document failure modes and costs

**Week 2 - Option 1 Validation:**
- Run with JSON repair 50 times
- Compare metrics to baseline
- Decision: Continue to Option 2 or iterate on Option 1?

**Week 3-4 - Option 2 Implementation:**
- Implement multi-stage generation
- Test on 20+ diverse tasks

**Week 5 - Option 2 Validation:**
- Run multi-stage system 100 times
- Compare to both baseline and Option 1
- Decision: Deploy or iterate?

---

## References

- **Debugging Doc:** `docs/debugging/code_agent_json_parsing_issue.md`
- **Failing Test:** `tests/e2e/test_all_agents_hello_world_e2e.py::test_code_agent_hello_world`
- **Current Code Agent:** `src/asp/agents/code_agent.py`
- **Current Prompt:** `src/asp/prompts/code_agent_v1_generation.txt`
- **Artifact Persistence:** `docs/artifact_persistence_version_control_decision.md`
- **RFC 8259:** JSON Specification (https://datatracker.ietf.org/doc/html/rfc8259)
- **Related Issue:** Session summary `Summary/summary20251120.5.md`

---

## Questions and Discussion

### Q: Why not fix the prompt to get better JSON escaping?
**A:** The prompt already has 3 detailed examples with correct escaping. The issue is LLM attention span and precision over 20-50KB outputs, not understanding of escaping rules.

### Q: Can we reduce the code output size to make JSON more reliable?
**A:** Possibly, but "Hello World" is already minimal (2-3 files). Real tasks generate 10-15 files. We can't meaningfully reduce output size.

### Q: Is 2-4x cost increase acceptable?
**A:** If it increases reliability from 50% to 98%, yes. Failed generations waste time and require reruns anyway. Measuring actual cost will inform final decision.

### Q: What if multi-stage generation has consistency issues?
**A:** We'll add validation to check:
- All imports are valid across files
- Type annotations match between files
- No circular dependencies
- Tests import correct modules

### Q: Can we parallelize file generation to reduce latency?
**A:** Yes, files can be generated concurrently with asyncio. Expected 3-5x speedup over sequential (120s → 30-40s).

### Q: Should we use this pattern for other agents?
**A:** Not immediately. Planning and Design agents work fine with current JSON approach. Revisit if they have similar failures.

---

**Status:** Awaiting approval to implement Option 1 (short-term) and Option 2 (long-term)

**Decision Date:** 2025-11-20
**Review Date:** After Option 1 validation (Week 2)
**Next Update:** After Option 2 implementation (Week 5)
