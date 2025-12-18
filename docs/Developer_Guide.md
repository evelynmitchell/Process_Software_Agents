# Developer Guide

**Extending, customizing, and contributing to the ASP Platform**

This guide is for developers who want to extend the ASP Platform, create custom agents, modify existing behavior, or contribute to the project.

---

## Table of Contents

- [Project Structure](#project-structure)
- [Development Environment](#development-environment)
- [Creating Custom Agents](#creating-custom-agents)
- [Extending Existing Agents](#extending-existing-agents)
- [Custom Prompts](#custom-prompts)
- [Custom Orchestrators](#custom-orchestrators)
- [Custom Approval Services](#custom-approval-services)
- [Testing Strategy](#testing-strategy)
- [Telemetry & Instrumentation](#telemetry--instrumentation)
- [Contributing Guidelines](#contributing-guidelines)
- [Architecture Patterns](#architecture-patterns)
- [Performance Optimization](#performance-optimization)
- [Async Execution](#async-execution)

---

## Project Structure

### Directory Layout

```
Process_Software_Agents/
├── src/asp/                    # Main application package
│   ├── agents/                 # 7 core + 14 specialist agents
│   ├── orchestrators/          # Pipeline orchestrators
│   ├── telemetry/              # Observability system
│   ├── models/                 # Pydantic/SQLAlchemy models
│   ├── prompts/                # Versioned agent prompts
│   ├── approval/               # HITL approval services
│   ├── web/                    # Web UI dashboard
│   └── utils/                  # Utility functions
├── artifacts/                  # Agent output artifacts (task-specific)
├── data/                       # Runtime data (database, bootstrap data)
├── tests/                      # Test suite (unit, integration, e2e)
├── database/                   # SQL schemas and migrations
├── docs/                       # Documentation
├── scripts/                    # Utility scripts
└── config/                     # Configuration files
```

For complete structure details, see [PROJECT_STRUCTURE.md](../PROJECT_STRUCTURE.md).

### Key Components

**src/asp/agents/**
- `base_agent.py` - Abstract base class for all agents
- `*_agent.py` - 7 core agent implementations
- `*_orchestrator.py` - Multi-agent orchestrators
- `reviews/` - 6 design review specialists
- `code_reviews/` - 6 code review specialists

**src/asp/models/**
- Pydantic models for inputs/outputs
- SQLAlchemy models for database persistence
- Validation and serialization logic

**src/asp/telemetry/**
- `instrumentation.py` - Decorators for cost tracking
- `langfuse_client.py` - Langfuse integration
- `cost_tracker.py` - Token/cost calculation
- `defect_logger.py` - Defect taxonomy logging

**src/asp/prompts/**
- Versioned prompt templates (`.txt` files)
- Naming convention: `{agent}_v{version}_{variant}.txt`
- Loaded dynamically at runtime

**src/asp/web/**
- `main.py` - FastHTML application entry point
- `data.py` - Data layer for telemetry and artifacts
- `api.py` - API endpoints for HITL approvals
- `manager.py` - Manager persona routes
- `developer.py` - Developer persona routes
- `product.py` - Product Manager persona routes
- `components.py` - Shared UI components

---

## Development Environment

### Setup

```bash
# Clone repository
git clone https://github.com/evelynmitchell/Process_Software_Agents.git
cd Process_Software_Agents

# Install dependencies
uv sync --all-extras

# Initialize database
uv run python scripts/init_database.py --with-sample-data

# Run tests
uv run pytest -m unit
```

### Recommended Tools

**IDE:** VS Code or PyCharm
- Install Python extension
- Configure linter (ruff)
- Enable type checking (mypy)
- Use Python 3.12+

**Development Tools:**
```bash
# Linting and formatting
uv run ruff check .
uv run ruff format .

# Type checking
uv run mypy src/

# Test with coverage
uv run pytest --cov --cov-report=html

# Watch mode for tests
uv run pytest-watch
```

### Debugging

**Debug with pdb:**
```python
# Add breakpoint
import pdb; pdb.set_trace()

# Or use built-in
breakpoint()
```

**Debug with VS Code:**
```json
// .vscode/launch.json
{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "Python: Current File",
            "type": "python",
            "request": "launch",
            "program": "${file}",
            "console": "integratedTerminal"
        },
        {
            "name": "Python: Pytest",
            "type": "python",
            "request": "launch",
            "module": "pytest",
            "args": ["-sv", "${file}"]
        }
    ]
}
```

---

## Creating Custom Agents

### Step 1: Define Agent Purpose

Create a new agent by extending `BaseAgent`:

```python
# src/asp/agents/my_custom_agent.py
from asp.agents.base_agent import BaseAgent
from asp.models import MyCustomInput, MyCustomOutput
from asp.telemetry import track_agent_cost
from anthropic import Anthropic

class MyCustomAgent(BaseAgent):
    """
    Custom agent for [specific purpose].

    This agent performs [detailed description of functionality].
    """

    def __init__(
        self,
        model: str = "claude-sonnet-4",
        temperature: float = 0.7,
        max_tokens: int = 4000
    ):
        """Initialize MyCustomAgent."""
        super().__init__(
            agent_id="my_custom_agent",
            model=model,
            temperature=temperature,
            max_tokens=max_tokens
        )
        self.client = Anthropic()

    @track_agent_cost(agent_id="my_custom_agent")
    def execute(
        self,
        input_data: MyCustomInput
    ) -> MyCustomOutput:
        """
        Execute custom agent logic.

        Args:
            input_data: MyCustomInput with task context

        Returns:
            MyCustomOutput with results
        """
        # Load prompt template
        prompt = self._load_prompt("my_custom_agent_v1.txt")

        # Format prompt with input data
        formatted_prompt = prompt.format(
            task_description=input_data.description,
            requirements="\n".join(f"- {r}" for r in input_data.requirements)
        )

        # Call LLM
        response = self.client.messages.create(
            model=self.model,
            max_tokens=self.max_tokens,
            temperature=self.temperature,
            messages=[{
                "role": "user",
                "content": formatted_prompt
            }]
        )

        # Parse response
        output_text = response.content[0].text

        # Create output model
        output = MyCustomOutput(
            result=output_text,
            metadata={
                "model": self.model,
                "temperature": self.temperature
            }
        )

        return output
```

### Step 2: Define Data Models

```python
# src/asp/models/my_custom.py
from pydantic import BaseModel, Field
from typing import List, Optional

class MyCustomInput(BaseModel):
    """Input for MyCustomAgent."""

    task_id: str = Field(..., description="Task identifier")
    description: str = Field(..., description="Task description")
    requirements: List[str] = Field(
        default_factory=list,
        description="List of requirements"
    )
    context: Optional[str] = Field(
        None,
        description="Additional context"
    )

class MyCustomOutput(BaseModel):
    """Output from MyCustomAgent."""

    result: str = Field(..., description="Agent result")
    metadata: dict = Field(
        default_factory=dict,
        description="Additional metadata"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "result": "Example output",
                "metadata": {"model": "claude-sonnet-4"}
            }
        }
```

### Step 3: Create Prompt Template

```text
# src/asp/prompts/my_custom_agent_v1.txt
You are a specialized agent for [specific purpose].

Task Description:
{task_description}

Requirements:
{requirements}

Your goal is to [detailed instructions].

Output Format:
[Specify exact output format expected]
```

### Step 4: Add Tests

```python
# tests/unit/test_agents/test_my_custom_agent.py
import pytest
from asp.agents import MyCustomAgent
from asp.models import MyCustomInput

def test_my_custom_agent_initialization():
    """Test agent initializes correctly."""
    agent = MyCustomAgent()
    assert agent.agent_id == "my_custom_agent"
    assert agent.model == "claude-sonnet-4"

def test_my_custom_agent_execute():
    """Test agent execution."""
    agent = MyCustomAgent()

    input_data = MyCustomInput(
        task_id="TEST-001",
        description="Test task",
        requirements=["Requirement 1", "Requirement 2"]
    )

    output = agent.execute(input_data)

    assert output.result is not None
    assert len(output.result) > 0
    assert output.metadata["model"] == "claude-sonnet-4"

@pytest.mark.integration
def test_my_custom_agent_with_real_api():
    """Integration test with real API."""
    agent = MyCustomAgent()
    # Test with real API call
    pass
```

---

## Extending Existing Agents

### Modify Agent Behavior

Create a subclass to extend existing agents:

```python
from asp.agents import PlanningAgent
from asp.models import ProjectPlan

class EnhancedPlanningAgent(PlanningAgent):
    """Planning agent with additional risk analysis."""

    def execute(self, task_request) -> ProjectPlan:
        """Execute planning with enhanced risk analysis."""
        # Call parent implementation
        plan = super().execute(task_request)

        # Add custom risk analysis
        plan.risk_analysis = self._analyze_risks(plan)

        return plan

    def _analyze_risks(self, plan: ProjectPlan) -> dict:
        """Custom risk analysis logic."""
        risks = []

        # Example: Flag high complexity tasks
        if plan.total_est_complexity > 10.0:
            risks.append({
                "type": "complexity",
                "severity": "HIGH",
                "message": "Task complexity exceeds threshold"
            })

        return {"risks": risks}
```

### Override Prompt Loading

```python
class CustomPlanningAgent(PlanningAgent):
    """Planning agent with custom prompt."""

    def _load_prompt(self, prompt_name: str) -> str:
        """Load custom prompt from alternative location."""
        # Check custom prompts directory first
        custom_path = f"custom_prompts/{prompt_name}"
        if Path(custom_path).exists():
            with open(custom_path) as f:
                return f.read()

        # Fallback to default
        return super()._load_prompt(prompt_name)
```

---

## Custom Prompts

### Prompt Engineering

**Prompt Structure:**
```text
# Header - Agent role and purpose
You are a [role] specialized in [domain].

# Context - Task information
Task: {task_description}
Requirements: {requirements}

# Instructions - Detailed steps
1. [Step 1]
2. [Step 2]
...

# Output Format - Structured output
Output the result in the following JSON format:
{
  "field1": "value",
  "field2": ["array", "values"]
}

# Examples - Few-shot learning (optional)
Example Input:
...
Example Output:
...

# Constraints - Limitations and boundaries
- Constraint 1
- Constraint 2
```

### Prompt Versioning

**Naming Convention:**
- `{agent}_v{version}_{variant}.txt`
- Examples:
  - `planning_agent_v1_decomposition.txt`
  - `planning_agent_v1_with_feedback.txt`
  - `code_agent_v2_file_generation.txt`

**Loading Prompts:**
```python
def _load_prompt(self, prompt_name: str) -> str:
    """Load prompt template from file."""
    prompt_path = Path(__file__).parent.parent / "prompts" / prompt_name

    if not prompt_path.exists():
        raise FileNotFoundError(f"Prompt not found: {prompt_name}")

    with open(prompt_path) as f:
        return f.read()
```

### Testing Prompts

```python
def test_prompt_loading():
    """Test prompt loads correctly."""
    agent = PlanningAgent()
    prompt = agent._load_prompt("planning_agent_v1_decomposition.txt")

    assert "{task_description}" in prompt
    assert "{requirements}" in prompt
    assert len(prompt) > 100  # Sanity check

def test_prompt_formatting():
    """Test prompt formats with variables."""
    prompt = "Task: {task_description}\nReqs: {requirements}"

    formatted = prompt.format(
        task_description="Build API",
        requirements="- REQ1\n- REQ2"
    )

    assert "Build API" in formatted
    assert "REQ1" in formatted
```

---

## Custom Orchestrators

### Creating a Custom Orchestrator

```python
# src/asp/orchestrators/my_custom_orchestrator.py
from asp.orchestrators.base import BaseOrchestrator
from asp.agents import PlanningAgent, CodeAgent, TestAgent
from asp.telemetry import track_agent_cost

class MyCustomOrchestrator(BaseOrchestrator):
    """
    Custom orchestrator for [specific workflow].

    This orchestrator coordinates [agents involved] in a
    [description of workflow] pattern.
    """

    def __init__(
        self,
        planning_agent: Optional[PlanningAgent] = None,
        code_agent: Optional[CodeAgent] = None,
        test_agent: Optional[TestAgent] = None
    ):
        """Initialize orchestrator with agents."""
        self.planning_agent = planning_agent or PlanningAgent()
        self.code_agent = code_agent or CodeAgent()
        self.test_agent = test_agent or TestAgent()

    @track_agent_cost(agent_id="my_custom_orchestrator")
    def execute(self, task_request):
        """
        Execute custom orchestration workflow.

        Workflow:
        1. Planning
        2. Code generation
        3. Testing
        4. [Custom steps]

        Args:
            task_request: TaskRequest with description and requirements

        Returns:
            Custom result object
        """
        # Phase 1: Planning
        plan = self.planning_agent.execute(task_request)

        # Phase 2: Code generation
        code = self.code_agent.execute(plan)

        # Phase 3: Testing
        test_results = self.test_agent.execute(code)

        # Phase 4: Custom logic
        final_result = self._custom_processing(plan, code, test_results)

        return final_result

    def _custom_processing(self, plan, code, test_results):
        """Custom processing logic."""
        # Implement custom workflow logic
        pass
```

### Phase-Aware Feedback

```python
class FeedbackOrchestrator(BaseOrchestrator):
    """Orchestrator with feedback loops."""

    def execute(self, task_request):
        """Execute with automatic feedback routing."""
        max_iterations = 3
        iteration = 0

        # Phase 1: Planning
        plan = self.planning_agent.execute(task_request)

        while iteration < max_iterations:
            # Phase 2: Design
            design = self.design_agent.execute(plan)

            # Phase 3: Review
            review = self.review_agent.execute(design)

            if review.status == "PASS":
                # Success - continue
                break

            # Route feedback back to appropriate phase
            if self._has_planning_defects(review):
                # Re-plan
                plan = self.planning_agent.execute(
                    task_request,
                    feedback=review.planning_defects
                )
            else:
                # Re-design
                design = self.design_agent.execute(
                    plan,
                    feedback=review.design_defects
                )

            iteration += 1

        return {"plan": plan, "design": design, "review": review}
```

---

## Custom Approval Services

See [HITL Integration Guide](HITL_Integration.md) for complete details on creating custom approval services.

### Example: Email-Based Approval

```python
from asp.approval.base import ApprovalService, ApprovalRequest, ApprovalResponse, ReviewDecision
import smtplib
from email.mime.text import MIMEText
from datetime import datetime

class EmailApprovalService(ApprovalService):
    """HITL approval via email."""

    def __init__(
        self,
        smtp_server: str,
        smtp_port: int,
        from_email: str,
        to_email: str,
        poll_interval: int = 60
    ):
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.from_email = from_email
        self.to_email = to_email
        self.poll_interval = poll_interval

    def request_approval(
        self,
        request: ApprovalRequest
    ) -> ApprovalResponse:
        """Request approval via email."""
        # Send email with review request
        self._send_review_email(request)

        # Poll for response (check inbox for reply)
        decision = self._poll_for_response(request.task_id)

        return ApprovalResponse(
            decision=decision["decision"],
            reviewer=decision["reviewer"],
            timestamp=datetime.utcnow().isoformat() + 'Z',
            justification=decision["justification"]
        )

    def _send_review_email(self, request: ApprovalRequest):
        """Send review request email."""
        subject = f"[ASP Review] {request.task_id} - {request.gate_type}"

        body = f"""
        Review Required for Task: {request.task_id}
        Gate Type: {request.gate_type}

        Quality Report:
        {self._format_report(request.quality_report)}

        To approve: Reply with "APPROVE" and justification
        To reject: Reply with "REJECT" and justification
        """

        msg = MIMEText(body)
        msg["Subject"] = subject
        msg["From"] = self.from_email
        msg["To"] = self.to_email

        with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
            server.send_message(msg)

    def _poll_for_response(self, task_id: str) -> dict:
        """Poll inbox for approval response."""
        # Implementation depends on email provider (IMAP, etc.)
        pass
```

---

## Testing Strategy

### Test Pyramid

```
         /\
        /E2E\        <- Few (1-5 per agent)
       /------\
      /  INT   \     <- Some (5-10 per agent)
     /----------\
    /   UNIT     \   <- Many (20-50 per agent)
   /--------------\
```

### Unit Tests

**Fast, isolated, no external dependencies:**

```python
# tests/unit/test_agents/test_planning_agent.py
from asp.agents import PlanningAgent
from asp.models import TaskRequest
from unittest.mock import Mock, patch

def test_planning_agent_initialization():
    """Test agent initializes with defaults."""
    agent = PlanningAgent()
    assert agent.agent_id == "planning_agent"
    assert agent.model == "claude-sonnet-4"

@patch("asp.agents.planning_agent.Anthropic")
def test_planning_agent_execute_mocked(mock_anthropic):
    """Test planning with mocked LLM."""
    # Setup mock
    mock_client = Mock()
    mock_response = Mock()
    mock_response.content = [Mock(text='{"semantic_units": []}')]
    mock_client.messages.create.return_value = mock_response
    mock_anthropic.return_value = mock_client

    # Execute
    agent = PlanningAgent()
    task = TaskRequest(
        task_id="TEST-001",
        description="Test task",
        requirements=["REQ1"]
    )

    result = agent.execute(task)

    # Verify
    assert mock_client.messages.create.called
    assert result is not None
```

### Integration Tests

**Use real APIs, test agent interactions:**

```python
# tests/integration/test_planning_design_flow.py
import pytest
from asp.agents import PlanningAgent, DesignAgent
from asp.models import TaskRequest

@pytest.mark.integration
def test_planning_to_design_flow():
    """Test planning output feeds into design."""
    # Planning phase
    planning_agent = PlanningAgent()
    task = TaskRequest(
        task_id="INT-001",
        description="Build REST API",
        requirements=["CRUD operations"]
    )

    plan = planning_agent.execute(task)

    # Design phase (uses planning output)
    design_agent = DesignAgent()
    design = design_agent.execute(plan)

    # Verify integration
    assert design.task_id == plan.task_id
    assert len(design.components) > 0
```

### E2E Tests

**Full pipeline tests:**

```python
# tests/e2e/test_complete_task.py
import pytest
from asp.orchestrators import TSPOrchestrator
from asp.models import TaskRequest

@pytest.mark.e2e
@pytest.mark.slow
def test_complete_task_e2e():
    """Test complete task through full pipeline."""
    orchestrator = TSPOrchestrator()

    task = TaskRequest(
        task_id="E2E-001",
        description="Create hello world function",
        requirements=[
            "Function prints 'Hello, World!'",
            "Include tests"
        ]
    )

    result = orchestrator.execute(task)

    # Verify all phases completed
    assert result.plan is not None
    assert result.design is not None
    assert result.code is not None
    assert result.test_results is not None
    assert result.postmortem is not None

    # Verify artifacts created
    artifacts_dir = Path(f"artifacts/{task.task_id}")
    assert artifacts_dir.exists()
    assert (artifacts_dir / "plan.md").exists()
    assert (artifacts_dir / "design.md").exists()
```

### Running Tests

```bash
# Unit tests only (fast)
uv run pytest -m unit

# Integration tests (uses real APIs)
uv run pytest -m integration

# E2E tests (slow, expensive)
uv run pytest -m e2e

# All tests
uv run pytest

# With coverage
uv run pytest --cov --cov-report=html

# Specific test file
uv run pytest tests/unit/test_agents/test_planning_agent.py

# Specific test function
uv run pytest tests/unit/test_agents/test_planning_agent.py::test_planning_agent_initialization
```

---

## Telemetry & Instrumentation

### Adding Telemetry to Custom Agents

```python
from asp.telemetry import track_agent_cost
from datetime import datetime

class MyCustomAgent(BaseAgent):

    @track_agent_cost(agent_id="my_custom_agent")
    def execute(self, input_data):
        """Execute agent with automatic cost tracking."""
        start_time = datetime.utcnow()

        # Agent logic here
        result = self._process(input_data)

        # track_agent_cost decorator automatically:
        # - Records latency_ms
        # - Records total_tokens
        # - Records api_cost_usd
        # - Saves to database
        # - Sends to Langfuse

        return result
```

### Custom Metrics

```python
from asp.telemetry import log_custom_metric

def execute_with_custom_metrics(self, input_data):
    """Execute with custom metrics."""
    # Log custom metric
    log_custom_metric(
        agent_id="my_custom_agent",
        metric_name="custom_complexity",
        metric_value=self._calculate_complexity(input_data),
        metadata={"task_id": input_data.task_id}
    )

    # Continue execution
    return self._process(input_data)
```

### Querying Telemetry

```python
from asp.telemetry import TelemetryDB

# Initialize database connection
db = TelemetryDB("data/asp_telemetry.db")

# Query cost data
costs = db.query("""
    SELECT agent_id, SUM(api_cost_usd) as total_cost
    FROM agent_cost_vector
    WHERE timestamp > datetime('now', '-7 days')
    GROUP BY agent_id
    ORDER BY total_cost DESC
""")

# Query defects
defects = db.query("""
    SELECT defect_type, severity, COUNT(*) as count
    FROM defect_log_entry
    GROUP BY defect_type, severity
    ORDER BY count DESC
""")
```

---

## Contributing Guidelines

### Before You Start

1. **Check existing issues** - Avoid duplicate work
2. **Discuss large changes** - Open an issue first for architectural changes
3. **Read Claude.md** - Development guidelines and patterns

### Development Workflow

```bash
# 1. Create feature branch
git checkout -b feature/my-feature

# 2. Make changes
# - Write code
# - Add tests
# - Update docs

# 3. Run quality checks
uv run ruff check .
uv run ruff format .
uv run mypy src/
uv run pytest

# 4. Commit changes
git add .
git commit -m "feat: Add my feature

- Detailed description
- Breaking changes (if any)
"

# 5. Push and create PR
git push origin feature/my-feature
# Open PR on GitHub
```

### Code Style

**Follow PEP 8 with ruff:**
- Line length: 88 characters (Black default)
- Use type hints
- Docstrings required for public methods
- Google-style docstrings

**Example:**
```python
def calculate_complexity(
    semantic_units: List[SemanticUnit],
    weights: Optional[Dict[str, float]] = None
) -> float:
    """
    Calculate weighted semantic complexity.

    Args:
        semantic_units: List of semantic units to analyze
        weights: Optional custom weights for unit types

    Returns:
        Weighted complexity score

    Raises:
        ValueError: If semantic_units is empty
    """
    if not semantic_units:
        raise ValueError("semantic_units cannot be empty")

    # Implementation
    pass
```

### PR Requirements

**All PRs must:**
- ✅ Pass all existing tests
- ✅ Include new tests for new code
- ✅ Update documentation
- ✅ Pass linting (ruff)
- ✅ Pass type checking (mypy)
- ✅ Have clear commit messages

**PR Template:**
```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
- [ ] Unit tests added/updated
- [ ] Integration tests added/updated
- [ ] All tests passing

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Documentation updated
- [ ] No breaking changes (or documented)
```

---

## Architecture Patterns

### Agent Pattern

All agents follow a consistent pattern:

```python
class Agent(BaseAgent):
    """Agent description."""

    def __init__(self, **config):
        """Initialize with configuration."""
        super().__init__(agent_id="...", **config)

    @track_agent_cost(agent_id="...")
    def execute(self, input_data) -> output_type:
        """Execute agent logic."""
        # 1. Load prompt
        # 2. Format prompt with input
        # 3. Call LLM
        # 4. Parse response
        # 5. Return structured output
        pass
```

### Multi-Agent Orchestration

```python
class Orchestrator:
    """Multi-agent orchestrator."""

    def __init__(self, agents: List[BaseAgent]):
        """Initialize with agent list."""
        self.agents = agents

    async def execute_parallel(self, input_data):
        """Execute agents in parallel."""
        tasks = [agent.execute(input_data) for agent in self.agents]
        results = await asyncio.gather(*tasks)
        return self._aggregate(results)

    def _aggregate(self, results):
        """Aggregate results from multiple agents."""
        pass
```

### Phase-Aware Feedback

```python
def execute_with_feedback(self, task_request):
    """Execute with phase-aware feedback routing."""
    plan = self.planning_agent.execute(task_request)

    while True:
        design = self.design_agent.execute(plan)
        review = self.review_agent.execute(design)

        if review.status == "PASS":
            break

        # Route feedback to originating phase
        if review.has_planning_defects:
            plan = self.planning_agent.execute(
                task_request,
                feedback=review.planning_defects
            )
        else:
            design = self.design_agent.execute(
                plan,
                feedback=review.design_defects
            )

    return design
```

---

## Performance Optimization

### Profiling

```python
import cProfile
import pstats

# Profile agent execution
profiler = cProfile.Profile()
profiler.enable()

agent.execute(task)

profiler.disable()
stats = pstats.Stats(profiler)
stats.sort_stats('cumulative')
stats.print_stats(20)  # Top 20 functions
```

### Caching

```python
from functools import lru_cache

class CachedAgent(BaseAgent):
    """Agent with prompt caching."""

    @lru_cache(maxsize=128)
    def _load_prompt(self, prompt_name: str) -> str:
        """Load prompt with caching."""
        return super()._load_prompt(prompt_name)
```

### Batch Processing

```python
async def process_batch(self, tasks: List[TaskRequest]):
    """Process multiple tasks in parallel."""
    # Use asyncio for concurrent execution
    results = await asyncio.gather(
        *[self.execute(task) for task in tasks]
    )
    return results
```

### Token Optimization

```python
# Use smaller models for simple tasks
if task.complexity < 5.0:
    agent = PlanningAgent(model="claude-haiku-4")  # Faster, cheaper
else:
    agent = PlanningAgent(model="claude-sonnet-4")  # More capable
```

---

## Async Execution

ASP supports full async execution for non-blocking I/O and better resource utilization (ADR 008).

### CLI Async Mode

```bash
# Sync execution (default, backward compatible)
uv run python -m asp.cli run --task-id TASK-001 --description "Add feature"

# Async execution
uv run python -m asp.cli run --task-id TASK-001 --description "Add feature" --async
```

### Programmatic Async Usage

All orchestrators and agents support async execution:

```python
import asyncio
from asp.orchestrators import TSPOrchestrator
from asp.models.planning import TaskRequirements

async def run_task_async():
    orchestrator = TSPOrchestrator()

    requirements = TaskRequirements(
        task_id="ASYNC-001",
        description="Build async feature",
        requirements="Implement async processing"
    )

    # Use execute_async() instead of execute()
    result = await orchestrator.execute_async(requirements)
    return result

# Run from sync context
result = asyncio.run(run_task_async())
```

### Async Agent Methods

All agents provide both sync and async interfaces:

```python
from asp.agents import PlanningAgent

agent = PlanningAgent()

# Sync execution
result = agent.execute(requirements)

# Async execution
result = await agent.execute_async(requirements)
```

### Async Services

Services also support async execution:

```python
from services.sandbox_executor import SubprocessSandboxExecutor
from services.test_executor import TestExecutor

# Async subprocess execution
sandbox = SubprocessSandboxExecutor()
result = await sandbox.execute_async(workspace, ["pytest", "-v"])

# Async test execution
test_executor = TestExecutor(sandbox)
test_result = await test_executor.run_tests_async(workspace)
```

### When to Use Async

| Scenario | Recommendation |
|----------|----------------|
| Production workloads | ✅ Use `--async` or `execute_async()` |
| Multiple concurrent tasks | ✅ Use async with `asyncio.gather()` |
| Integration with FastAPI/async frameworks | ✅ Use `execute_async()` |
| Simple scripts / prototyping | Sync is fine |
| Debugging complex issues | Sync (easier stack traces) |

### Async Architecture (ADR 008)

The async implementation follows a layered approach:

```
┌─────────────────────────────────────────────────────────────┐
│ CLI Layer: --async flag → asyncio.run()                     │
├─────────────────────────────────────────────────────────────┤
│ Orchestrator Layer: execute_async()                         │
│   - TSPOrchestrator.execute_async()                        │
│   - PlanningDesignOrchestrator.execute_async()             │
├─────────────────────────────────────────────────────────────┤
│ Agent Layer: execute_async()                                │
│   - All 7 core agents + specialists                        │
│   - Uses AsyncAnthropic client                             │
├─────────────────────────────────────────────────────────────┤
│ Service Layer: *_async() methods                            │
│   - SandboxExecutor.execute_async()                        │
│   - TestExecutor.run_tests_async()                         │
├─────────────────────────────────────────────────────────────┤
│ LLM Layer: call_with_retry_async()                          │
│   - Non-blocking I/O during API calls                      │
└─────────────────────────────────────────────────────────────┘
```

For full details, see [ADR 008: Async Process Architecture](../design/ADR_008_async_process_architecture.md).

---

## Summary

**Key Takeaways:**

- ✅ **Project Structure:** Well-organized with clear separation of concerns
- ✅ **Custom Agents:** Easy to create by extending BaseAgent
- ✅ **Prompts:** Versioned, testable, and customizable
- ✅ **Orchestrators:** Coordinate multi-agent workflows with feedback
- ✅ **Testing:** Comprehensive pyramid (unit, integration, e2e)
- ✅ **Telemetry:** Built-in observability for all agents
- ✅ **Contributing:** Clear guidelines and quality standards
- ✅ **Async Execution:** Full async support via `execute_async()` (ADR 008)

**Next Steps:**

1. **Explore Examples:** Check `examples/` for runnable demos
2. **Read Agent Reference:** Deep dive into each agent (docs/Agents_Reference.md)
3. **Build Something:** Create a custom agent or orchestrator
4. **Contribute:** Submit a PR with improvements

---

**Built with ASP Platform v1.0**

*Extend ASP to fit your workflow.*
