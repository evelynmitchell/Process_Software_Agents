"""
Tests for async execution patterns (ADR 008).

Tests async LLM calls and agent execution.
"""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from pydantic import BaseModel

from asp.agents.base_agent import AgentExecutionError, BaseAgent

# =============================================================================
# Test Models
# =============================================================================


class TestInput(BaseModel):
    """Test input model."""

    value: str


class TestOutput(BaseModel):
    """Test output model."""

    result: str


# =============================================================================
# Concrete Test Agent
# =============================================================================


class ConcreteTestAgent(BaseAgent):
    """Concrete agent for testing."""

    def execute(self, input_data: TestInput) -> TestOutput:
        """Sync execution."""
        response = self.call_llm(f"Process: {input_data.value}")
        return TestOutput(result=response.get("content", ""))

    async def execute_async_native(self, input_data: TestInput) -> TestOutput:
        """Native async execution (example implementation)."""
        response = await self.call_llm_async(f"Process: {input_data.value}")
        return TestOutput(result=response.get("content", ""))


# =============================================================================
# Async LLM Client Tests
# =============================================================================


class TestAsyncLLMClient:
    """Tests for async LLM client functionality."""

    @pytest.fixture
    def mock_async_client(self):
        """Create a mock async Anthropic client."""
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text='{"result": "async_response"}')]
        mock_response.usage.input_tokens = 100
        mock_response.usage.output_tokens = 50
        mock_response.model = "claude-haiku-4-5"
        mock_response.stop_reason = "end_turn"

        mock_client = MagicMock()
        mock_client.messages.create = AsyncMock(return_value=mock_response)
        return mock_client

    @pytest.mark.asyncio
    async def test_call_with_retry_async_success(self, mock_async_client):
        """Test successful async LLM call."""
        from asp.utils.llm_client import LLMClient

        with patch.object(LLMClient, "__init__", lambda x, y=None: None):
            client = LLMClient.__new__(LLMClient)
            client.api_key = "test-key"
            client._async_client = mock_async_client
            client.DEFAULT_MODEL = "claude-haiku-4-5"
            client.COST_PER_MILLION_INPUT_TOKENS = 0.25
            client.COST_PER_MILLION_OUTPUT_TOKENS = 1.25

            response = await client.call_with_retry_async(
                prompt="Test prompt",
                max_tokens=1000,
            )

            assert response["content"] == {"result": "async_response"}
            assert response["usage"]["input_tokens"] == 100
            assert response["usage"]["output_tokens"] == 50
            mock_async_client.messages.create.assert_called_once()

    @pytest.mark.asyncio
    async def test_call_with_retry_async_with_system_prompt(self, mock_async_client):
        """Test async LLM call with system prompt."""
        from asp.utils.llm_client import LLMClient

        with patch.object(LLMClient, "__init__", lambda x, y=None: None):
            client = LLMClient.__new__(LLMClient)
            client.api_key = "test-key"
            client._async_client = mock_async_client
            client.DEFAULT_MODEL = "claude-haiku-4-5"
            client.COST_PER_MILLION_INPUT_TOKENS = 0.25
            client.COST_PER_MILLION_OUTPUT_TOKENS = 1.25

            await client.call_with_retry_async(
                prompt="Test prompt",
                system="You are a helpful assistant",
            )

            call_kwargs = mock_async_client.messages.create.call_args[1]
            assert call_kwargs["system"] == "You are a helpful assistant"


# =============================================================================
# Async Agent Execution Tests
# =============================================================================


class TestAsyncAgentExecution:
    """Tests for async agent execution."""

    @pytest.fixture
    def mock_llm_client(self):
        """Create a mock LLM client with async support."""
        mock_client = MagicMock()
        mock_client.call_with_retry.return_value = {
            "content": "sync_response",
            "usage": {"input_tokens": 100, "output_tokens": 50},
            "cost": 0.01,
            "model": "claude-haiku-4-5",
        }
        mock_client.call_with_retry_async = AsyncMock(
            return_value={
                "content": "async_response",
                "usage": {"input_tokens": 100, "output_tokens": 50},
                "cost": 0.01,
                "model": "claude-haiku-4-5",
            }
        )
        return mock_client

    def test_sync_execution(self, mock_llm_client):
        """Test sync execution still works."""
        agent = ConcreteTestAgent(llm_client=mock_llm_client)
        result = agent.execute(TestInput(value="test"))

        assert result.result == "sync_response"
        mock_llm_client.call_with_retry.assert_called_once()

    @pytest.mark.asyncio
    async def test_async_llm_call(self, mock_llm_client):
        """Test async LLM call from agent."""
        agent = ConcreteTestAgent(llm_client=mock_llm_client)
        response = await agent.call_llm_async("Test prompt")

        assert response["content"] == "async_response"
        mock_llm_client.call_with_retry_async.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_async_default_fallback(self, mock_llm_client):
        """Test execute_async falls back to sync in thread pool."""
        agent = ConcreteTestAgent(llm_client=mock_llm_client)
        result = await agent.execute_async(TestInput(value="test"))

        # Default execute_async should call sync execute
        assert result.result == "sync_response"

    @pytest.mark.asyncio
    async def test_native_async_execution(self, mock_llm_client):
        """Test native async execution pattern."""
        agent = ConcreteTestAgent(llm_client=mock_llm_client)
        result = await agent.execute_async_native(TestInput(value="test"))

        assert result.result == "async_response"
        mock_llm_client.call_with_retry_async.assert_called_once()

    @pytest.mark.asyncio
    async def test_async_llm_call_error_handling(self, mock_llm_client):
        """Test error handling in async LLM call."""
        mock_llm_client.call_with_retry_async = AsyncMock(
            side_effect=Exception("API Error")
        )

        agent = ConcreteTestAgent(llm_client=mock_llm_client)

        with pytest.raises(AgentExecutionError) as exc_info:
            await agent.call_llm_async("Test prompt")

        assert "failed during async LLM call" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_parallel_agent_execution(self, mock_llm_client):
        """Test running multiple agents in parallel."""
        from asp.orchestrators.parallel import run_agents_parallel

        agents = [ConcreteTestAgent(llm_client=mock_llm_client) for _ in range(3)]
        inputs = [TestInput(value=f"input_{i}") for i in range(3)]

        results = await run_agents_parallel(agents, inputs, max_concurrent=3)

        assert len(results) == 3
        # All should use sync fallback
        assert mock_llm_client.call_with_retry.call_count == 3


# =============================================================================
# Integration Tests
# =============================================================================


class TestAsyncIntegration:
    """Integration tests for async execution patterns."""

    @pytest.mark.asyncio
    async def test_concurrent_execution_timing(self):
        """Test that concurrent execution is actually parallel."""
        execution_times = []

        async def timed_task(n):
            start = asyncio.get_event_loop().time()
            await asyncio.sleep(0.1)  # 100ms
            end = asyncio.get_event_loop().time()
            execution_times.append((n, start, end))
            return n

        from asp.orchestrators.parallel import gather_with_concurrency

        start = asyncio.get_event_loop().time()
        await gather_with_concurrency(5, timed_task(1), timed_task(2), timed_task(3))
        total_time = asyncio.get_event_loop().time() - start

        # If sequential: 3 * 100ms = 300ms
        # If parallel: ~100ms
        # Allow some margin
        assert total_time < 0.25  # Should be much less than 300ms

    @pytest.mark.asyncio
    async def test_mixed_sync_async_workflow(self):
        """Test workflow mixing sync and async operations."""
        from asp.orchestrators.parallel import gather_with_results

        async def sync_like_task():
            # Simulate sync operation wrapped in async
            return "sync_result"

        async def async_task():
            await asyncio.sleep(0.01)
            return "async_result"

        result = await gather_with_results(
            sync_like_task(), async_task(), sync_like_task()
        )

        assert result.all_successful
        assert result.results == ["sync_result", "async_result", "sync_result"]
