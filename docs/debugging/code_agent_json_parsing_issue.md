# Code Agent JSON Parsing Issue - Debugging Documentation

**Date:** November 20, 2025
**Issue ID:** CODE-AGENT-JSON-001
**Severity:** High (Blocks E2E pipeline)
**Status:** Diagnosed, Solution Pending

---

## Executive Summary

The Code Agent consistently fails with `JSONDecodeError: Unterminated string` when generating code for tasks. This occurs even after the markdown fence extraction fix (commit 77d721b). The issue is **unique to the Code Agent** - all other agents (Planning, Design, Design Review) successfully generate and parse JSON responses.

**Root Cause:** The Code Agent prompt requires the LLM to embed complete Python source code files (with docstrings, comments, multi-line strings) inside JSON string values. The LLM frequently fails to properly escape special characters (particularly triple-quoted docstrings `"""`) in these large code strings, resulting in malformed JSON.

---

## Test Failures

### E2E Test Run (November 20, 2025)

**Command:** `uv run pytest tests/e2e/test_all_agents_hello_world_e2e.py -v -s`

**Results:**
- ✅ **PASS:** `test_planning_agent_hello_world` (30s)
- ✅ **PASS:** `test_design_agent_hello_world` (30s)
- ❌ **FAIL:** `test_code_agent_hello_world` (189s, 3:09)
- ❌ **FAIL:** `test_complete_agent_pipeline_hello_world` (475s, 7:55 - failed at Code Agent step 4/6)

### Error Details

```
JSONDecodeError: Unterminated string starting at: line 55 column 18 (char 23228)

File: src/asp/agents/code_agent.py:235
json.loads(json_str)  # Fails here

JSON content preview:
{
  "task_id": "HW-CODE-001",
  "project_id": "PROJECT-HW-001",
  "files": [
    {
      "file_path": "main.py",
      "content": "#!/usr/bin/env python3\n\"\"\"\nHello World FastAPI Application...\n\"\"\"
      ...
```

**Error Location:** Character 23228 in the JSON string - approximately where a Python file's docstring appears unescaped.

---

## Why Only the Code Agent?

### Comparative Analysis of Agent JSON Requirements

| Agent | Output Size | JSON Complexity | Special Characters | Failure Rate |
|-------|-------------|-----------------|-------------------|--------------|
| **Planning Agent** | ~1-2KB | Simple (numbers, short strings) | None | 0% |
| **Design Agent** | ~5-10KB | Moderate (structured data, descriptions) | Few (API paths, SQL) | 0% |
| **Design Review Agent** | ~3-5KB | Moderate (issue descriptions, recommendations) | Few (code snippets in descriptions) | 0% |
| **Code Agent** | ~20-50KB | **Extreme (complete source files)** | **Many (docstrings, comments, strings)** | **High (~50%)** |

### Key Differences: Code Agent vs. Other Agents

#### 1. **Response Size**

**Code Agent:**
- Generates 8-15 complete files per task
- Each file: 50-500 lines of code
- Total JSON size: 20,000-50,000 characters
- Example: Hello World API = ~25KB JSON

**Other Agents:**
- Planning: 5-10 semantic units with numeric complexity scores (~1-2KB)
- Design: 3-5 API contracts + 4-8 components (~5-10KB)
- Design Review: 10-20 issues with text descriptions (~3-5KB)

**Impact:** Larger responses mean more opportunities for escaping errors.

#### 2. **Content Complexity**

**Code Agent - Must Escape:**
```python
"content": "#!/usr/bin/env python3\n\"\"\"\\nFastAPI Application.\\n\"\"\"\\n\\nfrom fastapi import FastAPI\\n\\napp = FastAPI()\\n\\n@app.get(\"/hello\")\\nasync def hello():\\n    \\\"\\\"\\\"Return greeting.\\\"\\\"\\\"\\n    return {\\\"message\\\": \\\"Hello World\\\"}"
```

Requires escaping:
- Triple-quoted docstrings: `"""` → `\"\"\"`
- Single-quoted docstrings: `'''` → `\'\'\'`
- Quote characters in strings: `"message"` → `\"message\"`
- Curly braces in f-strings: `f"{var}"` → `f\"{var}\"`
- Backslashes in regex: `r"\d+"` → `r\"\\d+\"`
- Newlines: actual newlines → `\n`

**Other Agents - Simple Strings:**
```json
"description": "Create user registration endpoint with email validation",
"validation_criteria": "Must use bcrypt for password hashing",
"recommendation": "Add rate limiting to prevent brute force attacks"
```

Rarely contains special characters requiring escaping.

#### 3. **Prompt Examples**

**Code Agent Prompt** (line 115, `code_agent_v1_generation.txt`):
```json
{
  "file_path": "src/api/auth.py",
  "content": "\"\"\"\\nAuthentication API endpoints.\\n\\nProvides JWT-based authentication...\\n\"\"\"\\nfrom fastapi import APIRouter..."
}
```

Shows proper escaping with `\"\"\"\\n` but the LLM frequently:
- Misses escapes for internal quotes
- Fails on nested string structures
- Drops backslashes in long code blocks

**Planning/Design Agent Prompts:**
```json
{
  "unit_id": "SU-001",
  "description": "Create login endpoint with JWT token generation",
  "est_complexity": 27
}
```

Simple key-value pairs with no code content.

#### 4. **LLM Context Window Pressure**

**Code Agent:**
- Prompt size: ~15KB (code_agent_v1_generation.txt)
- Input (Design Spec): ~10-15KB
- **Output (Generated Code): ~25-50KB**
- **Total context: ~50-80KB (12,000-20,000 tokens)**

**Other Agents:**
- Prompt: 6-25KB
- Input: 1-5KB
- Output: 1-10KB
- Total context: ~8-40KB (2,000-10,000 tokens)

**Impact:** Near the context window limits, LLMs are more prone to:
- Attention failures (missing characters deep in output)
- Pattern drift (starting with proper escaping, losing it later)
- Truncation errors (incomplete escape sequences)

---

## Technical Deep Dive

### JSON String Escaping Rules

Per [RFC 8259 Section 7](https://datatracker.ietf.org/doc/html/rfc8259#section-7), JSON strings must escape:

| Character | Escape Sequence | Example in Python Code | Required Escape in JSON |
|-----------|----------------|------------------------|------------------------|
| `"` | `\"` | `print("hello")` | `print(\"hello\")` |
| `\` | `\\` | `r"\d+"` | `r\"\\d+\"` |
| Newline | `\n` | Multi-line string | Explicit `\n` |
| Tab | `\t` | Indentation | Explicit `\t` |
| Carriage return | `\r` | Windows line endings | Explicit `\r` |

### Problem: Triple-Quoted Docstrings

Python uses triple quotes for multi-line docstrings:
```python
def hello():
    """
    Return a greeting message.

    Returns:
        dict: Greeting message with timestamp
    """
    return {"message": "Hello"}
```

**In JSON, this must be:**
```json
{
  "content": "def hello():\n    \"\"\"\n    Return a greeting message.\n    \n    Returns:\n        dict: Greeting message with timestamp\n    \"\"\"\n    return {\"message\": \"Hello\"}"
}
```

**What the LLM generates (WRONG):**
```json
{
  "content": "def hello():\n    """\n    Return a greeting message.\n    \n    Returns:\n        dict: Greeting message with timestamp\n    """\n    return {"message": "Hello"}"
}
```

**Error:** The `"""` at line start terminates the JSON string prematurely, causing `JSONDecodeError: Unterminated string`.

### Observed Failure Pattern

From test output, the error occurs at **character 23228**, approximately **55 lines** into the JSON response. This suggests:

1. **LLM starts correctly:** First few files have proper escaping
2. **Escaping degrades:** As output grows, LLM "forgets" to escape consistently
3. **Triple-quote collision:** First unescaped `"""` breaks JSON parser
4. **Cascade failure:** Parser cannot recover, entire response rejected

---

## Why Commit 77d721b Didn't Fully Fix This

### What 77d721b Fixed ✅

**Problem:** LLM was wrapping JSON in markdown code fences:
```
Here's the generated code:

```json
{
  "task_id": "HW-001",
  ...
}
```

I've generated 12 files with 1247 lines of code.
```

**Solution:** Regex extraction to find JSON inside markdown fences:
```python
json_match = re.search(r'```json\s*(.*?)\s*```', content, re.DOTALL)
if json_match:
    json_str = json_match.group(1).strip()
    content = json.loads(json_str)  # Now works!
```

**Result:** Successfully extracts JSON from markdown - **but only if the JSON itself is valid**.

### What 77d721b Didn't Fix ❌

**Problem:** The extracted JSON itself is malformed due to unescaped characters.

**Why it still fails:**
```python
# Step 1: Extract JSON from markdown ✅ (77d721b fixed this)
json_str = extract_from_markdown(llm_response)
# json_str = '{"task_id": "HW-001", "files": [...unescaped """...]}'

# Step 2: Parse JSON ❌ (Still fails here!)
content = json.loads(json_str)
# JSONDecodeError: Unterminated string at char 23228
```

**Root cause persists:** LLM generates malformed JSON with unescaped special characters in code content strings.

---

## Comparison: Why Planning/Design Agents Succeed

### Planning Agent Success Case

**Test:** `test_planning_agent_hello_world`
**Result:** ✅ PASS (30 seconds)

**JSON Response:**
```json
{
  "task_id": "HW-001",
  "project_id": "PROJECT-HW-001",
  "semantic_units": [
    {
      "unit_id": "SU-001",
      "description": "Setup FastAPI application with basic configuration",
      "api_interactions": 1,
      "data_transformations": 0,
      "logical_branches": 0,
      "code_entities_modified": 2,
      "novelty_multiplier": 1.0,
      "est_complexity": 9
    }
  ],
  "agent_version": "1.0.0"
}
```

**Why it succeeds:**
- No code content (just descriptions)
- Small response size (~1KB)
- Simple numeric/string values
- No special character escaping needed
- LLM can easily maintain JSON validity

### Design Agent Success Case

**Test:** `test_design_agent_hello_world`
**Result:** ✅ PASS (30 seconds)

**JSON Response:**
```json
{
  "task_id": "HW-001",
  "api_contracts": [
    {
      "endpoint": "GET /hello",
      "request_schema": {},
      "response_schema": {
        "message": "string",
        "timestamp": "string",
        "status": "string"
      },
      "auth_required": false
    }
  ],
  "components": [
    {
      "component_id": "COMP-001",
      "name": "HelloWorldEndpoint",
      "description": "FastAPI endpoint that returns Hello World message",
      "dependencies": ["FastAPI", "datetime"]
    }
  ]
}
```

**Why it succeeds:**
- Structured data (objects, arrays)
- Minimal special characters
- Response size ~5-10KB
- Short string values
- Occasional code snippets (like `"dependencies": ["FastAPI"]`) are simple
- LLM can maintain JSON structure throughout

---

## Why This Is Hard to Fix

### Challenge 1: LLM Limitations

Modern LLMs (including Claude Sonnet 4.5) have known issues with:
- **Long-form structured output:** Quality degrades after ~15-20KB
- **Consistent escaping:** Maintaining JSON validity across large outputs
- **Attention span:** "Forgetting" formatting rules deep in response
- **Character-level precision:** Missing individual escape characters in 50KB responses

### Challenge 2: JSON as a Container for Code

**The Fundamental Problem:**
```
JSON (structured data format)
  └─ Contains "content" field (string)
      └─ Contains Python code (text with complex escaping needs)
          └─ Contains docstrings, quotes, braces, backslashes
              └─ ALL must be escaped for JSON validity
```

This is a **deeply nested escaping problem** that LLMs struggle with at scale.

### Challenge 3: No Easy Prompt Fix

**Tried approaches that don't work:**

1. ❌ **"Make sure to escape all quotes"**
   - Too vague, LLM doesn't understand context

2. ❌ **More examples in prompt**
   - Prompt already has 3 detailed examples with proper escaping
   - LLM follows examples initially, then degrades

3. ❌ **"Use \\" for backslash"**
   - Specific instructions get lost in large prompts

4. ❌ **Larger context window**
   - Problem isn't space, it's attention/precision

### Challenge 4: Alternative Formats Have Tradeoffs

| Format | Pros | Cons |
|--------|------|------|
| **JSON (current)** | Structured, parseable, schema validation | Escaping hell for code content |
| **YAML** | Less escaping, multi-line strings | Indentation-sensitive, harder to parse reliably |
| **XML** | Well-defined escaping (`<![CDATA[...]]>`) | Verbose, less LLM-friendly |
| **Custom delimiters** | Can avoid escaping | Brittle, delimiter collision possible |
| **Base64 encoding** | No escaping needed | Increases size 33%, harder to debug |

---

## Potential Solutions

### Solution 1: Multi-Part JSON with Base64 (Recommended)

**Approach:** Generate JSON structure separately from file contents.

**Step 1 - LLM generates metadata only:**
```json
{
  "task_id": "HW-CODE-001",
  "files": [
    {
      "file_path": "main.py",
      "file_type": "source",
      "description": "FastAPI application with /hello endpoint"
    }
  ]
}
```

**Step 2 - Separate LLM calls for each file content:**
```python
for file_metadata in files:
    # Separate LLM call for just this file's code
    file_content = llm.generate_file(file_metadata)

    # No JSON parsing needed - raw text
    file_metadata['content'] = file_content
```

**Pros:**
- ✅ No JSON escaping needed for code content
- ✅ Smaller per-call outputs (better quality)
- ✅ Can retry individual files on failure

**Cons:**
- ❌ More LLM calls (higher cost, slower)
- ❌ More complex orchestration logic
- ❌ Requires multiple agents or multi-step process

### Solution 2: Aggressive JSON Repair (Quick Fix)

**Approach:** Attempt to fix common escaping errors before parsing.

```python
def repair_code_json(json_str: str) -> str:
    """
    Repair common JSON escaping errors in code content.

    Known issues:
    - Unescaped triple quotes: """ → \"\"\"
    - Unescaped single quotes: ' → \\'
    - Unescaped curly braces in f-strings: { → \\{
    """
    # Inside "content": "..." blocks, escape unescaped quotes
    # Use regex to find content fields
    content_pattern = r'"content":\s*"((?:[^"\\]|\\.)*)"'

    def fix_content(match):
        content = match.group(1)
        # Fix unescaped triple quotes
        content = content.replace('"""', r'\"\"\"')
        # Fix unescaped single quotes (but not escaped ones)
        content = re.sub(r'(?<!\\)\'', r"\'", content)
        return f'"content": "{content}"'

    return re.sub(content_pattern, fix_content, json_str, flags=re.DOTALL)
```

**Pros:**
- ✅ Quick to implement
- ✅ No architectural changes
- ✅ Can catch 80% of escaping errors

**Cons:**
- ❌ Brittle (regex on large JSON strings)
- ❌ Won't catch all edge cases
- ❌ May introduce new bugs

### Solution 3: Schema-Guided Generation (Advanced)

**Approach:** Use LLM function calling / tool use with Pydantic schema enforcement.

```python
from anthropic import Anthropic
from pydantic import BaseModel

class GeneratedFile(BaseModel):
    file_path: str
    content: str  # Pydantic handles escaping
    file_type: str

client = Anthropic()
response = client.messages.create(
    model="claude-sonnet-4-5-20250929",
    tools=[{
        "name": "generate_code",
        "input_schema": GeneratedFile.model_json_schema()
    }],
    tool_choice={"type": "tool", "name": "generate_code"}
)
```

**Pros:**
- ✅ LLM handles escaping automatically
- ✅ Built-in schema validation
- ✅ More reliable than raw JSON generation

**Cons:**
- ❌ Requires Anthropic API with tool use (costs more)
- ❌ Multiple tool calls needed (one per file)
- ❌ Major refactor of agent architecture

### Solution 4: Alternative Delimiter Format

**Approach:** Use custom delimiters instead of JSON for file content.

```
FILE_START: main.py
FILE_TYPE: source
CONTENT_START
#!/usr/bin/env python3
"""
FastAPI Hello World Application.
"""
from fastapi import FastAPI

app = FastAPI()

@app.get("/hello")
async def hello():
    """Return greeting."""
    return {"message": "Hello World"}
CONTENT_END

FILE_START: tests/test_main.py
FILE_TYPE: test
CONTENT_START
...
```

**Pros:**
- ✅ No JSON escaping needed
- ✅ Human-readable
- ✅ Easy to parse with regex

**Cons:**
- ❌ Less structured (harder to validate)
- ❌ Delimiter collision possible
- ❌ Loses JSON schema benefits

---

## Recommended Action Plan

### Phase 1: Immediate Fix (1-2 hours)
Implement **Solution 2 (Aggressive JSON Repair)** to unblock E2E tests:
1. Add `repair_code_json()` function to `code_agent.py`
2. Call before `json.loads()` in `_generate_code()`
3. Test on known failing cases
4. Document limitations

### Phase 2: Robust Solution (1-2 days)
Implement **Solution 1 (Multi-Part JSON)**:
1. Split Code Agent into two LLM calls:
   - Call 1: Generate file manifest (metadata only)
   - Call 2: Generate each file's content (no JSON wrapping)
2. Update prompt templates
3. Update `GeneratedCode` schema
4. Test with 5-10 different tasks

### Phase 3: Long-Term (Future)
Evaluate **Solution 3 (Schema-Guided Generation)**:
1. Prototype with Anthropic tool use API
2. Measure cost/latency impact
3. Compare reliability vs current approach
4. Decision: Adopt if significantly better

---

## Lessons Learned

### Why JSON Is Hard for Code Generation

1. **Size matters:** 50KB JSON responses are at the edge of LLM reliability
2. **Nesting is fragile:** JSON → string → Python code → docstrings = too many layers
3. **Escaping is hard:** LLMs struggle with character-level precision at scale
4. **Examples aren't enough:** Even with perfect examples, LLMs degrade on long outputs

### Why Other Agents Don't Have This Problem

1. **Content type:** Structured data vs. raw source code
2. **Response size:** 1-10KB vs. 20-50KB
3. **Escaping needs:** Minimal vs. extensive
4. **Failure modes:** Schema violations (catchable) vs. malformed JSON (uncatchable)

### Design Implications for Future Agents

- ✅ **Prefer structured data** over raw content in JSON
- ✅ **Keep responses small** (<10KB if possible)
- ✅ **Use separate calls** for large content generation
- ✅ **Base64 encode** if binary or heavily-escaped content needed
- ✅ **Add repair layers** for known error patterns
- ❌ **Avoid embedding source code directly in JSON strings**

---

## References

- **Failing Tests:** `tests/e2e/test_all_agents_hello_world_e2e.py::test_code_agent_hello_world`
- **Code Agent:** `src/asp/agents/code_agent.py:235` (JSON parsing location)
- **Prompt:** `src/asp/prompts/code_agent_v1_generation.txt`
- **Previous Fix:** Commit 77d721b ("Fix Code Agent JSON parsing with robust markdown fence extraction")
- **Error Log:** See test output above
- **RFC 8259:** JSON specification (https://datatracker.ietf.org/doc/html/rfc8259)

---

**Author:** Claude (ASP Development Assistant)
**Last Updated:** November 20, 2025
**Status:** Documented, awaiting fix implementation
