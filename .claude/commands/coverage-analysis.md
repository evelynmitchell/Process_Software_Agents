# Coverage Analysis Command

Analyze test coverage and identify modules that need additional tests.

## Instructions

1. **Run coverage report:**
   ```bash
   uv run pytest --cov=src --cov-report=json --cov-report=term-missing -q 2>/dev/null
   ```

2. **Parse coverage.json:**
   - Extract per-file coverage percentages
   - Identify files below 80% threshold
   - Calculate overall coverage

3. **Prioritize coverage gaps:**
   Sort files by priority score: `(80 - coverage%) * lines_of_code`

   This prioritizes files that are both:
   - Far below threshold (large gap)
   - Large files (more impactful)

4. **For top 5 low-coverage files, identify:**
   - Specific functions/methods with 0% coverage
   - Complex branches that lack test cases
   - Suggested test cases to add

5. **Generate coverage report:**

```markdown
## Coverage Summary
- **Overall:** 75.2% (target: 80%)
- **Gap:** 4.8% (approximately 2,400 lines uncovered)

## Priority Files to Cover

| File | Coverage | Lines | Gap | Priority |
|------|----------|-------|-----|----------|
| src/asp/agents/code_agent.py | 62% | 450 | 18% | High |
| src/asp/orchestrators/tsp.py | 68% | 380 | 12% | Medium |

## Suggested Test Cases

### src/asp/agents/code_agent.py
1. Test `generate_code()` with empty requirements
2. Test `validate_output()` with malformed JSON
3. Test error handling when LLM returns truncated response
```

## Output Format

Provide:
1. Overall coverage summary with gap to 80%
2. Priority table of files needing tests
3. Specific test case suggestions for top 3 files
4. Estimated effort to reach 80% threshold
