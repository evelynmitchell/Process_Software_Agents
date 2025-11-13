# Architecture Decision Record: Planning Agent Implementation

**Date:** November 13, 2025
**Status:** Proposed
**Deciders:** Development Team
**Related PRD Sections:** FR-001, FR-002, Section 13.1, Section 14 (Bootstrap Learning)

---

## Context and Problem Statement

We need to implement the Planning Agent, the first agent in the ASP Platform's 7-agent architecture. The Planning Agent is responsible for:

1. **Task Decomposition (FR-001):** Breaking high-level requirements into semantic units
2. **PROBE-AI Estimation (FR-002):** Estimating effort using historical data and regression
3. **Semantic Complexity Scoring:** Calculating complexity using the C1 formula (PRD Section 13.1)

This is our first agent implementation, so architectural decisions made here will establish patterns for the remaining 6 agents (Design, DesignReview, Code, CodeReview, Test, Postmortem).

**Key Constraints:**
- Must integrate with existing telemetry infrastructure (@track_agent_cost decorator)
- Must log to both Langfuse and SQLite
- Must support Bootstrap Learning Framework (Phase 1: 10 tasks without PROBE-AI)
- Must be testable, observable, and maintainable
- Budget: <$1.00 per planning session

---

## Decision Drivers

### Technical Requirements
1. **Reliability:** Agent must handle API failures gracefully with retry logic
2. **Observability:** Full telemetry integration from day one
3. **Testability:** Must support unit, integration, and E2E testing
4. **Maintainability:** Clear abstractions, reusable components
5. **Performance:** <30 seconds per planning session (typical case)

### Business Requirements
6. **Cost Control:** Predictable per-task costs
7. **Flexibility:** Easy to swap LLM providers or models
8. **Scalability:** Architecture must support 6 additional agents
9. **Bootstrap Strategy:** Must work without historical data initially

### PSP Alignment
10. **Disciplined Process:** Follow PSP principles for measurement and quality
11. **Incremental Development:** Build in phases, measure, adapt
12. **Defect Prevention:** Catch issues early with testing

---

## Options Considered

### Option 1: LangChain Framework

**Description:** Use LangChain for LLM orchestration, prompt management, and structured outputs.

**Pros:**
- Built-in retry logic and error handling
- Prompt template management
- Structured output parsing
- Large community and examples
- Chain abstractions for complex workflows

**Cons:**
- Heavy dependency (50+ transitive dependencies)
- Framework lock-in (hard to switch providers)
- Overhead for simple use cases
- Harder to debug and profile
- Breaking changes between versions
- Our telemetry decorators may not integrate cleanly

**Estimated Cost:** Similar to direct API ($0.03-0.15 per task)

**Estimated Complexity:** Medium-High (learning curve, framework overhead)

---

### Option 2: LlamaIndex Framework

**Description:** Use LlamaIndex for document indexing, retrieval, and LLM orchestration.

**Pros:**
- Excellent for RAG (retrieval-augmented generation)
- Built-in document loaders and indexers
- Query engine abstractions
- Good for context management

**Cons:**
- Overkill for our use case (we don't need RAG yet)
- Similar lock-in concerns as LangChain
- Heavyweight dependency
- Not designed for multi-agent workflows
- Less flexibility for custom telemetry

**Estimated Cost:** Similar to direct API ($0.03-0.15 per task)

**Estimated Complexity:** High (unnecessary features for Phase 1)

---

### Option 3: Direct Anthropic SDK ✅ SELECTED

**Description:** Use Anthropic Python SDK directly with custom abstractions for retry logic, prompt management, and structured outputs.

**Pros:**
- **Full control:** Direct access to API, no framework overhead
- **Simplicity:** Minimal dependencies, easy to understand
- **Performance:** No middleware, faster debugging
- **Flexibility:** Easy to add other providers (OpenAI, etc.)
- **Telemetry integration:** Our decorators work seamlessly
- **Transparency:** Clear token counting, cost tracking

**Cons:**
- Must implement retry logic ourselves (mitigated: use `tenacity` library)
- Must manage prompts manually (mitigated: use file-based templates)
- No built-in structured output parsing (mitigated: use Pydantic)

**Estimated Cost:** $0.03-0.15 per task (Claude Sonnet 4 pricing)

**Estimated Complexity:** Medium (custom implementation, but well-scoped)

**Implementation Approach:**
- Use `anthropic` SDK (already in dependencies)
- Use `tenacity` for retry logic (already in dependencies)
- Use `pydantic` for structured output validation (already in dependencies)
- Store prompts as text files in `src/asp/prompts/`
- Create `BaseAgent` abstraction for shared patterns

---

### Option 4: OpenAI Function Calling

**Description:** Use OpenAI SDK with function calling for structured outputs.

**Pros:**
- Function calling provides structured JSON outputs
- Well-documented API
- Similar pricing to Anthropic

**Cons:**
- PRD explicitly recommends Anthropic Claude for reasoning tasks
- Function calling is more limited than tool use
- Switching costs if we need Claude-specific features later

**Decision:** Deferred - we'll implement provider abstraction to support OpenAI in Phase 2

---

## Decision Outcome

**Chosen Option:** Option 3 - Direct Anthropic SDK with custom abstractions

### Rationale

1. **Simplicity over Framework:** The Planning Agent's workflow is straightforward:
   - Call LLM with prompt → Parse JSON → Validate with Pydantic → Save to database
   - No need for complex orchestration (chains, agents, tools) in Phase 1

2. **Control and Observability:**
   - Direct API access gives us precise control over token counting, cost tracking
   - Easier to integrate with our existing telemetry decorators
   - No "magic" happening in framework layers

3. **Performance:**
   - No framework overhead means faster execution and debugging
   - Direct API calls are easier to profile and optimize

4. **Flexibility:**
   - Easy to add OpenAI, Cohere, or other providers later
   - No framework lock-in if we need to switch strategies

5. **Dependencies:**
   - All required libraries already in `pyproject.toml`:
     - `anthropic>=0.39.0` (LLM client)
     - `tenacity>=9.0.0` (retry logic)
     - `pydantic>=2.9.0` (validation)
   - Zero new dependencies needed

6. **Team Knowledge:**
   - Direct SDK is easier to onboard new developers
   - No framework-specific knowledge required
   - Standard Python patterns throughout

### Trade-offs Accepted

| Trade-off | Mitigation |
|-----------|-----------|
| Must implement retry logic | Use `tenacity` library (12 lines of code) |
| Must manage prompts manually | Use file-based templates in `src/asp/prompts/` |
| No built-in output parsing | Use Pydantic models with strict validation |
| No built-in prompt versioning | Version prompts by filename (`v1`, `v2`, etc.) |

---

## Implementation Architecture

### Component Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                        Planning Agent                            │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │              PlanningAgent(BaseAgent)                     │  │
│  │  - decompose_task()                                       │  │
│  │  - estimate_with_probe_ai() [Phase 2]                     │  │
│  └──────────────────────────────────────────────────────────┘  │
│                             │                                    │
│                             ├──────────────────┐                 │
│                             ▼                  ▼                 │
│  ┌─────────────────────────────┐  ┌───────────────────────┐   │
│  │      LLMClient              │  │ SemanticComplexity    │   │
│  │  - call_with_retry()        │  │  - calculate_c1()     │   │
│  │  - parse_json_response()    │  │  - validate_factors() │   │
│  └─────────────────────────────┘  └───────────────────────┘   │
│                             │                                    │
│                             ▼                                    │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │              Telemetry (@track_agent_cost)               │  │
│  │  - Log to Langfuse (real-time observability)            │  │
│  │  - Log to SQLite (persistent storage)                   │  │
│  └─────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

### File Structure

```
src/asp/
├── agents/
│   ├── base_agent.py           # Abstract base class
│   └── planning_agent.py       # Planning Agent implementation
├── models/
│   └── planning.py             # TaskRequirements, ProjectPlan, SemanticUnit
├── prompts/
│   ├── planning_agent_v1_decomposition.txt
│   └── planning_agent_v1_estimation.txt     # Phase 2
├── utils/
│   ├── llm_client.py           # Anthropic SDK wrapper with retry
│   ├── semantic_complexity.py  # C1 formula implementation
│   └── probe_ai.py             # PROBE-AI estimator (stub for Phase 1)
└── telemetry/
    └── telemetry.py            # Existing: @track_agent_cost decorator

tests/
├── unit/
│   ├── test_agents/
│   │   ├── test_base_agent.py
│   │   └── test_planning_agent.py
│   └── test_utils/
│       └── test_semantic_complexity.py
└── integration/
    └── test_planning_agent_integration.py
```

---

## Detailed Design Decisions

### 1. Base Agent Abstraction

**Decision:** Create an abstract `BaseAgent` class that all 7 agents inherit from.

**Rationale:**
- **Code reuse:** All agents need: prompt loading, LLM calls, telemetry, error handling
- **Consistency:** Uniform interface across all agents
- **Testing:** Mock the base class once, test all agents

**Interface:**

```python
from abc import ABC, abstractmethod

class BaseAgent(ABC):
    """Abstract base class for all ASP agents."""

    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path
        self.llm_client = LLMClient()

    def load_prompt(self, prompt_name: str) -> str:
        """Load prompt template from file."""
        prompt_path = Path(__file__).parent.parent / "prompts" / f"{prompt_name}.txt"
        return prompt_path.read_text()

    @abstractmethod
    def execute(self, input_data: BaseModel) -> BaseModel:
        """Execute agent logic. Must be implemented by subclasses."""
        pass

    def _call_llm(self, prompt: str, **kwargs) -> dict:
        """Call LLM with retry logic and telemetry."""
        return self.llm_client.call_with_retry(prompt, **kwargs)
```

**Alternatives Considered:**
- **Composition over inheritance:** Use a helper class instead of base class
  - Rejected: More boilerplate, less clear agent interface
- **No abstraction:** Each agent implements everything independently
  - Rejected: High code duplication, inconsistent patterns

---

### 2. Semantic Complexity Calculation

**Decision:** Implement C1 formula as a pure function in a separate utility module.

**Formula (from PRD Section 13.1):**

```
Semantic_Complexity = (
    (2 × API_Interactions) +
    (5 × Data_Transformations) +
    (3 × Logical_Branches) +
    (4 × Code_Entities_Modified) +
    (Novelty_Multiplier × Base_Score)
)

Novelty_Multiplier:
  - 1.0 = Familiar (done before)
  - 1.5 = Moderate (some new concepts)
  - 2.0 = Novel (entirely new)
```

**Implementation:**

```python
# src/asp/utils/semantic_complexity.py

from pydantic import BaseModel, Field

class ComplexityFactors(BaseModel):
    """Input to semantic complexity calculation."""
    api_interactions: int = Field(ge=0)
    data_transformations: int = Field(ge=0)
    logical_branches: int = Field(ge=0)
    code_entities_modified: int = Field(ge=0)
    novelty_multiplier: float = Field(ge=1.0, le=2.0)

def calculate_semantic_complexity(factors: ComplexityFactors) -> int:
    """
    Calculate Semantic Complexity using C1 formula (PRD Section 13.1).

    Returns:
        int: Complexity score (typically 1-100)
    """
    base_score = (
        (2 * factors.api_interactions) +
        (5 * factors.data_transformations) +
        (3 * factors.logical_branches) +
        (4 * factors.code_entities_modified)
    )

    total = base_score * factors.novelty_multiplier

    return round(total)
```

**Rationale:**
- **Testability:** Pure function is trivial to unit test
- **Reusability:** Other agents may use complexity scoring
- **Clarity:** Formula is explicit and matches PRD exactly

**Calibration Strategy:**
- After 10 tasks, analyze actual effort vs. estimated complexity
- If correlation is weak (R² < 0.5), adjust formula weights
- Document calibration in a separate analysis report

---

### 3. PROBE-AI Implementation Strategy

**Decision:** Implement PROBE-AI as a stub in Phase 1, activate in Phase 2 after 10 completed tasks.

**Phase 1 (Current):**
```python
# src/asp/utils/probe_ai.py

class PROBEAIEstimator:
    def __init__(self, db_path: Path):
        self.db_path = db_path

    def estimate(self, semantic_units: list[SemanticUnit]) -> Optional[PROBEAIPrediction]:
        """
        Estimate effort using historical data and regression.

        Returns None if insufficient data (< 10 completed tasks).
        """
        # Check if we have enough data
        with get_db_connection(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM task_metadata WHERE status = 'completed'")
            completed_count = cursor.fetchone()[0]

        if completed_count < 10:
            logger.warning(f"PROBE-AI disabled: only {completed_count}/10 tasks completed")
            return None

        # Phase 2: Implement regression here
        # For now, return None
        return None
```

**Phase 2 (After 10 tasks):**
- Query historical data: complexity → (latency, tokens, cost)
- Use `scipy.stats.linregress` to fit linear model
- Calculate R² coefficient
- If R² > 0.7, return predictions with confidence intervals
- If R² < 0.7, log warning and return None

**Rationale:**
- **Bootstrap problem:** Can't train regression model without data
- **PRD alignment:** Section 14 (B1) specifies 10-20 tasks for bootstrap
- **Risk mitigation:** Don't deploy untested predictions
- **Incremental approach:** Validate complexity scoring first, then add estimation

**Alternatives Considered:**
- **Start with PROBE-AI immediately:** Rejected - no historical data
- **Use synthetic data for cold start:** Rejected - unrealistic, could bias model
- **Skip PROBE-AI entirely:** Rejected - it's a key PRD requirement (FR-002)

---

### 4. Prompt Engineering Strategy

**Decision:** Use file-based prompt templates with XML structure and few-shot examples.

**Prompt Template Structure:**

```xml
<!-- src/asp/prompts/planning_agent_v1_decomposition.txt -->

<role>
You are a PSP Planning Agent, a Senior Software Architect responsible for breaking down
software tasks into measurable semantic units.
</role>

<objective>
Decompose the given task requirements into 3-8 semantic units, each representing
1-4 hours of work. For each unit, calculate a Semantic Complexity score using the C1 formula.
</objective>

<complexity_scoring_guide>
Use the following formula to calculate complexity for each semantic unit:

Semantic_Complexity = (2×API_Interactions) + (5×Data_Transformations) +
                      (3×Logical_Branches) + (4×Code_Entities_Modified) +
                      (Novelty_Multiplier × Base_Score)

Where:
- API_Interactions: Number of external API calls or integrations (0-10)
- Data_Transformations: Number of data format conversions or mappings (0-10)
- Logical_Branches: Number of if/else, switch, or conditional logic points (0-10)
- Code_Entities_Modified: Number of classes, functions, or modules to modify (0-10)
- Novelty_Multiplier: 1.0 (familiar), 1.5 (moderate), 2.0 (novel)

Complexity Bands:
- 1-10: Trivial (config change, simple CRUD)
- 11-30: Simple (single API endpoint, basic logic)
- 31-60: Moderate (multiple components, some integration)
- 61-80: Complex (cross-system integration, novel algorithms)
- 81-100: Very Complex (architectural changes, high novelty)
</complexity_scoring_guide>

<examples>
<!-- Example 1: Simple CRUD API -->
<example>
<input>
Task: Build a REST API endpoint to retrieve user profile by ID
Requirements: GET /users/:id endpoint, return JSON, query PostgreSQL database
</input>

<output>
{
  "semantic_units": [
    {
      "unit_id": "SU-001",
      "description": "Create GET /users/:id route handler",
      "api_interactions": 1,
      "data_transformations": 2,
      "logical_branches": 1,
      "code_entities_modified": 2,
      "novelty_multiplier": 1.0,
      "est_complexity": 15
    },
    {
      "unit_id": "SU-002",
      "description": "Implement database query and error handling",
      "api_interactions": 1,
      "data_transformations": 1,
      "logical_branches": 3,
      "code_entities_modified": 1,
      "novelty_multiplier": 1.0,
      "est_complexity": 13
    }
  ]
}
</output>
</example>

<!-- Example 2: More examples here... -->
</examples>

<task_requirements>
{requirements}
</task_requirements>

<output_format>
Return a JSON object with a "semantic_units" array. Each unit must have:
- unit_id (string): Unique identifier (e.g., "SU-001")
- description (string): Clear description of work
- api_interactions (int): 0-10
- data_transformations (int): 0-10
- logical_branches (int): 0-10
- code_entities_modified (int): 0-10
- novelty_multiplier (float): 1.0, 1.5, or 2.0
- est_complexity (int): Calculated using formula above

Do not include any text outside the JSON object.
</output_format>
```

**Prompt Engineering Techniques:**
1. **XML tags:** Clear section boundaries (Claude is trained on XML)
2. **Few-shot examples:** 2-3 calibration examples
3. **Explicit formula:** Show the math, don't expect LLM to derive it
4. **Complexity bands:** Help LLM calibrate scores
5. **Constraints:** Specify output format strictly

**Versioning:**
- Prompts are versioned by filename: `v1`, `v2`, etc.
- Changes to prompts trigger new version
- Agent logs prompt version in telemetry for tracking

---

### 5. Error Handling and Retry Logic

**Decision:** Use `tenacity` library for exponential backoff with specific retry strategies per error type.

**Implementation:**

```python
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)
from anthropic import APIConnectionError, RateLimitError, APIStatusError

class LLMClient:
    @retry(
        retry=retry_if_exception_type((APIConnectionError, RateLimitError)),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True
    )
    def call_with_retry(self, prompt: str, **kwargs) -> dict:
        """Call Anthropic API with retry logic."""
        try:
            response = self.client.messages.create(
                model="claude-sonnet-4-20250514",  # Pin version
                max_tokens=4096,
                messages=[{"role": "user", "content": prompt}],
                **kwargs
            )
            return self._parse_response(response)
        except APIStatusError as e:
            if 400 <= e.status_code < 500:
                # Client error - don't retry
                logger.error(f"Client error (HTTP {e.status_code}): {e.message}")
                raise
            else:
                # Server error - retry
                logger.warning(f"Server error (HTTP {e.status_code}), retrying...")
                raise
```

**Retry Strategy:**

| Error Type | Retry? | Max Attempts | Backoff |
|------------|--------|--------------|---------|
| `APIConnectionError` | Yes | 3 | Exponential (2s, 4s, 8s) |
| `RateLimitError` | Yes | 3 | Exponential (2s, 4s, 8s) |
| `APIStatusError` (5xx) | Yes | 3 | Exponential (2s, 4s, 8s) |
| `APIStatusError` (4xx) | No | - | Immediate failure |
| `ValidationError` (bad JSON) | No | - | Log defect, fail |

**Rationale:**
- **Network failures:** Transient, should retry
- **Rate limits:** Temporary, backoff and retry
- **Server errors:** May resolve, retry with backoff
- **Client errors:** Code bug, don't waste retries
- **Validation errors:** LLM output issue, log as defect

---

### 6. Testing Strategy

**Three-tier testing approach:**

#### Unit Tests (Fast, Isolated)
- **Coverage target:** 90%+
- **Mocking:** All LLM calls mocked with pre-defined responses
- **Focus:** Logic, validation, error handling

```python
# tests/unit/test_agents/test_planning_agent.py

def test_planning_agent_decompose_task(mock_llm_client):
    mock_llm_client.call_with_retry.return_value = {
        "semantic_units": [
            {
                "unit_id": "SU-001",
                "description": "Design API schema",
                "est_complexity": 15,
                "api_interactions": 2,
                "data_transformations": 3,
                "logical_branches": 1,
                "code_entities_modified": 2,
                "novelty_multiplier": 1.0
            }
        ]
    }

    agent = PlanningAgent()
    result = agent.decompose_task(TaskRequirements(...))

    assert len(result.semantic_units) == 1
    assert result.semantic_units[0].est_complexity == 15
```

#### Integration Tests (Medium Speed)
- **Test database:** In-memory SQLite
- **LLM calls:** Mocked (still fast)
- **Focus:** Database persistence, telemetry logging, full workflow

#### E2E Tests (Slow, Manual)
- **Mark:** `@pytest.mark.e2e` (run manually, not in CI)
- **LLM calls:** Real Anthropic API
- **Focus:** Output quality, prompt effectiveness

**Test Execution:**
```bash
# Fast: Run unit + integration tests (CI)
uv run pytest tests/unit tests/integration

# Slow: Run E2E tests (manual, requires API key)
uv run pytest -m e2e
```

---

## Consequences

### Positive Consequences

1. **Simplicity and Control:**
   - No framework overhead means faster debugging and profiling
   - Full visibility into LLM calls, token usage, and costs
   - Easy to understand for new team members

2. **Flexibility:**
   - Can add OpenAI, Cohere, or other providers with minimal changes
   - No framework lock-in if requirements change
   - Easy to customize behavior per agent

3. **Cost Efficiency:**
   - Direct API calls with precise token counting
   - No middleware overhead
   - Estimated $0.03-0.15 per planning session

4. **Testability:**
   - Pure functions and clear abstractions
   - Easy to mock LLM calls for fast unit tests
   - High test coverage achievable

5. **Observability:**
   - Seamless integration with existing telemetry infrastructure
   - Full tracking in Langfuse and SQLite
   - Can measure performance at every layer

6. **Scalability:**
   - `BaseAgent` pattern supports all 7 agents
   - Consistent interface across the platform
   - Reusable components (LLMClient, prompt loading, telemetry)

### Negative Consequences

1. **Custom Implementation Effort:**
   - Must implement retry logic (mitigated: `tenacity` library)
   - Must manage prompts manually (mitigated: file-based templates)
   - Must parse outputs manually (mitigated: Pydantic validation)
   - **Estimated overhead:** ~2 hours for base infrastructure

2. **No Built-in Prompt Versioning:**
   - Must track prompt versions manually in filenames
   - No automatic A/B testing support
   - **Mitigation:** Log prompt version in telemetry; build versioning system if needed

3. **Missing Framework Features:**
   - No built-in caching (not needed for Phase 1)
   - No prompt optimization tools (can add later)
   - No agent chains/tools (not needed yet)

4. **Maintenance Burden:**
   - Must keep up with Anthropic API changes
   - Must update SDK versions manually
   - **Mitigation:** Pin model versions, use semantic versioning

---

## Validation Strategy

### Success Criteria (Phase 1)

#### Week 1: Base Infrastructure
- [x] BaseAgent class implemented and tested
- [x] LLMClient with retry logic working
- [x] Pydantic models defined and validated
- [x] Unit tests passing (90%+ coverage)

#### Week 2: Planning Agent Core
- [ ] Task decomposition working with real LLM calls
- [ ] Semantic complexity calculation accurate (within 20% of actual)
- [ ] 5 test tasks successfully planned
- [ ] Telemetry data appearing in Langfuse and SQLite

#### End of Phase 1 (10 tasks completed)
- [ ] Planning Agent used in production for 10 real tasks
- [ ] Mean complexity score variance <25% (consistent)
- [ ] Zero agent crashes or unhandled errors
- [ ] Average cost per task: $0.03-0.15 (within budget)
- [ ] Team satisfied with decomposition quality

### Calibration Metrics

After 10 completed tasks, analyze:

1. **Complexity Accuracy:**
   ```
   Correlation(est_complexity, actual_effort) > 0.5
   Mean Absolute Percentage Error (MAPE) < 30%
   ```

2. **Consistency:**
   ```
   Coefficient_of_Variation(complexity_scores) < 0.3
   (Similar tasks should have similar scores)
   ```

3. **Cost:**
   ```
   Mean(api_cost_per_task) < $0.20
   P95(api_cost_per_task) < $0.50
   ```

4. **Performance:**
   ```
   Mean(latency_per_task) < 30 seconds
   P95(latency_per_task) < 60 seconds
   ```

If any metric fails, adjust:
- Prompts (if accuracy/consistency is low)
- C1 formula weights (if correlation is weak)
- Model choice (if costs are too high)

---

## Phase 2 Considerations

### When to Activate PROBE-AI

**Criteria (from PRD Section 14, B1):**
1. Minimum 10 completed tasks with both estimated and actual effort
2. Linear regression R² > 0.7 (strong correlation)
3. MAPE < 20% on validation set

**Activation Plan:**
1. **Task 1-10:** Planning Agent logs complexity only; human provides effort estimates
2. **Task 11:** Run PROBE-AI in shadow mode (predictions not shown to user)
3. **Task 11-20:** Compare PROBE-AI predictions vs. actuals
4. **Task 21+:** If R² > 0.7 and MAPE < 20%, enable autonomous mode

**Shadow Mode Implementation:**
```python
# Phase 2: After 10 tasks

def estimate_with_probe_ai(semantic_units: list[SemanticUnit]) -> PROBEAIPrediction:
    estimator = PROBEAIEstimator(db_path=self.db_path)
    prediction = estimator.estimate(semantic_units)

    if prediction is None:
        logger.warning("PROBE-AI not ready, returning None")
        return None

    if prediction.confidence < 0.7:
        logger.warning(f"PROBE-AI confidence low ({prediction.confidence:.2f}), consider manual review")

    return prediction
```

---

## Cost Analysis

### Per-Task Cost Breakdown (Estimated)

**Assumptions:**
- Model: Claude Sonnet 4
- Pricing: $3 per million input tokens, $15 per million output tokens
- Average task: 2,000 input tokens, 500 output tokens

**Cost Calculation:**
```
Input cost:  2,000 tokens × ($3 / 1,000,000) = $0.006
Output cost: 500 tokens × ($15 / 1,000,000) = $0.0075
Total: ~$0.014 per task
```

**With retries (10% of tasks):**
```
Average cost = $0.014 × 1.1 (10% retry rate) = $0.015 per task
```

**Monthly Budget (100 tasks/month):**
```
100 tasks × $0.015 = $1.50/month
```

**Cost Controls:**
1. Per-task cap: $1.00 (reject if exceeded)
2. Monthly cap: $100 (alert if 50% threshold reached)
3. Token limits: 10,000 input, 4,096 output per call

### Cost Optimization Strategies

If costs exceed budget:
1. Switch to Claude Haiku (10x cheaper, slightly lower quality)
2. Reduce max_tokens parameter
3. Optimize prompts to be more concise
4. Cache common decompositions (Phase 2)

---

## Monitoring and Observability

### Metrics to Track (via Telemetry)

**Performance Metrics:**
- Latency per task (mean, P50, P95, P99)
- Token usage per task (input, output, total)
- API cost per task
- Retry rate (% of calls that needed retries)

**Quality Metrics:**
- Complexity score variance (consistency check)
- Decomposition count per task (should be 3-8 units)
- JSON parsing failure rate (LLM output quality)

**Business Metrics:**
- Tasks planned per day
- Total monthly cost
- Agent uptime (% of requests that succeeded)

### Alerts

| Metric | Threshold | Action |
|--------|-----------|--------|
| Latency P95 | >60 seconds | Investigate performance bottleneck |
| Cost per task | >$0.50 | Review prompt, consider cheaper model |
| JSON parse failure rate | >5% | Review prompt, improve examples |
| Retry rate | >20% | Check API health, increase backoff |
| Monthly cost | >$50 | Review usage, optimize prompts |

### Dashboards

**Langfuse Dashboard:**
- Real-time traces for each Planning Agent call
- Token usage and cost visualization
- Error rate over time

**SQLite + Grafana (Optional):**
- Historical trends (complexity scores, costs)
- Task decomposition patterns
- Agent performance metrics

---

## Risks and Mitigations

### Risk 1: Semantic Complexity Inconsistency

**Probability:** Medium
**Impact:** High (affects PROBE-AI training)

**Description:** Claude may score similar tasks differently due to non-determinism.

**Mitigation:**
1. Use temperature=0 for deterministic outputs
2. Include 3-4 calibration examples in prompt
3. Define explicit complexity bands (1-10, 11-30, etc.)
4. After 10 tasks, analyze coefficient of variation
5. If CV > 0.3, refine prompt with more constraints

**Validation:** Track CV < 0.3 for similar task types

---

### Risk 2: Prompt Drift (Model Updates)

**Probability:** Low (but inevitable long-term)
**Impact:** Medium (behavior changes without code changes)

**Description:** Anthropic updates Claude models, changing prompt interpretation.

**Mitigation:**
1. Pin model version: `claude-sonnet-4-20250514` (not just `claude-sonnet-4`)
2. Version prompts in filenames: `v1`, `v2`, etc.
3. Log model version in telemetry
4. Run regression tests before upgrading models
5. A/B test new models before full rollout

**Validation:** Monitor complexity score mean/variance after model upgrades

---

### Risk 3: Context Window Exceeds Limits

**Probability:** Low for Phase 1 (200K token limit)
**Impact:** High (task rejection)

**Description:** Very large requirements exceed model context window.

**Mitigation:**
1. Set input limit: 50,000 tokens (~37,500 words)
2. If exceeded, return error: "Requirements too large, split into multiple tasks"
3. Phase 2: Implement chunking strategy with map-reduce pattern

**Validation:** Track input token distribution, alert if P95 > 40K tokens

---

### Risk 4: Cost Overruns

**Probability:** Medium
**Impact:** Medium (budget constraints)

**Description:** Costs exceed expected $0.015/task due to long outputs or retries.

**Mitigation:**
1. Set `max_tokens=4096` (hard cap on output length)
2. Implement per-task cost cap: $1.00
3. Monthly budget alert at $50 (50% of $100 budget)
4. If costs high, switch to Claude Haiku

**Validation:** Monitor monthly spend via Langfuse

---

### Risk 5: Telemetry Failures

**Probability:** Low
**Impact:** Medium (data loss for analytics)

**Description:** Langfuse or SQLite write failures corrupt telemetry data.

**Mitigation:**
1. Wrap all telemetry calls in try/except (already implemented)
2. Log warnings but don't fail agent execution
3. Daily health check: insert test record, verify retrieval
4. Implement telemetry replay if data loss detected

**Validation:** Monitor telemetry write failure rate < 1%

---

## Timeline and Milestones

### Week 1: Base Infrastructure
- **Days 1-2:** Implement `BaseAgent`, `LLMClient`, retry logic
- **Day 3:** Create Pydantic models, write unit tests
- **Days 4-5:** Review, iterate, achieve 90% test coverage

**Deliverable:** Base infrastructure working and tested

---

### Week 2: Planning Agent Implementation
- **Days 1-2:** Write decomposition prompt, test with Claude Playground
- **Day 3:** Implement `PlanningAgent.decompose_task()`
- **Day 4:** Implement `semantic_complexity.py` with C1 formula
- **Day 5:** Create example script, integration tests

**Deliverable:** Planning Agent working end-to-end

---

### Week 3: Calibration and Refinement
- **Days 1-3:** Test with 5 real tasks, analyze results
- **Days 4-5:** Calibrate prompt, adjust complexity bands if needed

**Deliverable:** Planning Agent production-ready

---

### Phase 2 (After 10 Tasks): PROBE-AI Activation
- **Week 4:** Implement PROBE-AI regression
- **Week 5:** Shadow mode testing (10 tasks)
- **Week 6:** Autonomous mode if R² > 0.7

**Deliverable:** PROBE-AI estimation enabled

---

## Appendices

### Appendix A: Related Documents

- **PRD.md** - Product Requirements (FR-001, FR-002, Section 13.1, Section 14)
- **PSPdoc.md** - PSP implementation standards
- **docs/database_schema_specification.md** - Task metadata schema
- **docs/data_storage_decision.md** - SQLite architecture decision
- **docs/secrets_management_decision.md** - API key management

### Appendix B: Dependencies

**Already in pyproject.toml:**
- `anthropic>=0.39.0` - LLM client
- `tenacity>=9.0.0` - Retry logic
- `pydantic>=2.9.0` - Data validation
- `langfuse>=2.52.0` - Observability
- `pytest>=8.3.2` - Testing
- `pytest-mock>=3.14.0` - Mocking

**No new dependencies required.**

### Appendix C: Prompt Template Example (Full)

See: `src/asp/prompts/planning_agent_v1_decomposition.txt` (to be created)

### Appendix D: Testing Checklist

- [ ] Unit tests for `BaseAgent` (10+ tests)
- [ ] Unit tests for `PlanningAgent` (15+ tests)
- [ ] Unit tests for `semantic_complexity.py` (8+ tests)
- [ ] Integration tests for database persistence (5+ tests)
- [ ] Integration tests for telemetry logging (3+ tests)
- [ ] E2E test with real LLM call (1+ test)
- [ ] Manual testing with 5 diverse tasks
- [ ] Calibration report after 10 tasks

---

## Decision Log

| Date | Version | Change | Reason |
|------|---------|--------|--------|
| 2025-11-13 | 1.0 | Initial decision | First agent implementation |

---

## Approval

**Status:** Proposed (awaiting review)

**Reviewers:**
- [ ] Technical Lead
- [ ] Product Owner
- [ ] Development Team

**Notes:**
- This decision will be reviewed after Phase 1 (10 tasks completed)
- If any success criteria fail, we will revise the approach
- Prompt versions will be managed separately from this document

---

**Next Steps:**
1. Review and approve this ADR
2. Create implementation tickets
3. Begin Week 1: Base infrastructure
4. Update this document based on learnings
