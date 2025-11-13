"""
Unit tests for llm_client.py

Tests the LLMClient wrapper including:
- Retry logic and exponential backoff
- JSON parsing
- Token counting and cost estimation
- Error handling for various API errors
"""

import json
import pytest
import os
from unittest.mock import Mock, MagicMock, patch
from anthropic import APIConnectionError, RateLimitError, APIStatusError

from asp.utils.llm_client import LLMClient


class TestLLMClientInitialization:
    """Test LLMClient initialization."""

    def test_init_with_api_key_parameter(self):
        """Test initialization with API key parameter."""
        client = LLMClient(api_key="test-api-key")
        assert client.api_key == "test-api-key"
        assert client.client is not None

    def test_init_with_env_variable(self):
        """Test initialization with environment variable."""
        with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "env-api-key"}):
            client = LLMClient()
            assert client.api_key == "env-api-key"

    def test_init_missing_api_key(self):
        """Test initialization fails without API key."""
        with patch.dict(os.environ, {}, clear=True):
            # Remove ANTHROPIC_API_KEY from environment
            with pytest.raises(ValueError) as exc_info:
                LLMClient()

            assert "Anthropic API key not found" in str(exc_info.value)
            assert "ANTHROPIC_API_KEY" in str(exc_info.value)

    def test_default_model_constant(self):
        """Test that DEFAULT_MODEL is set correctly."""
        assert LLMClient.DEFAULT_MODEL == "claude-sonnet-4-20250514"

    def test_cost_constants(self):
        """Test that cost constants are set correctly."""
        assert LLMClient.COST_PER_MILLION_INPUT_TOKENS == 3.0
        assert LLMClient.COST_PER_MILLION_OUTPUT_TOKENS == 15.0


class TestCallWithRetry:
    """Test call_with_retry method."""

    def test_successful_call(self):
        """Test successful API call with standard response."""
        client = LLMClient(api_key="test-key")

        # Mock response
        mock_response = Mock()
        mock_response.content = [Mock(text="This is the response")]
        mock_response.usage = Mock(input_tokens=100, output_tokens=50)
        mock_response.model = "claude-sonnet-4-20250514"
        mock_response.stop_reason = "end_turn"

        with patch.object(client.client.messages, 'create', return_value=mock_response):
            result = client.call_with_retry(
                prompt="Test prompt",
                model="claude-sonnet-4-20250514",
                max_tokens=2048,
                temperature=0.5
            )

        assert result["content"] == "This is the response"
        assert result["raw_content"] == "This is the response"
        assert result["usage"]["input_tokens"] == 100
        assert result["usage"]["output_tokens"] == 50
        assert result["model"] == "claude-sonnet-4-20250514"
        assert result["stop_reason"] == "end_turn"

    def test_successful_call_with_defaults(self):
        """Test successful API call with default parameters."""
        client = LLMClient(api_key="test-key")

        mock_response = Mock()
        mock_response.content = [Mock(text="Response")]
        mock_response.usage = Mock(input_tokens=50, output_tokens=25)
        mock_response.model = "claude-sonnet-4-20250514"
        mock_response.stop_reason = "end_turn"

        with patch.object(client.client.messages, 'create', return_value=mock_response) as mock_create:
            result = client.call_with_retry(prompt="Test")

            # Verify defaults were used
            mock_create.assert_called_once()
            call_kwargs = mock_create.call_args[1]
            assert call_kwargs["model"] == "claude-sonnet-4-20250514"
            assert call_kwargs["max_tokens"] == 4096
            assert call_kwargs["temperature"] == 0.0

    def test_cost_calculation(self):
        """Test that cost is calculated correctly."""
        client = LLMClient(api_key="test-key")

        mock_response = Mock()
        mock_response.content = [Mock(text="Response")]
        mock_response.usage = Mock(input_tokens=1000, output_tokens=500)
        mock_response.model = "claude-sonnet-4-20250514"
        mock_response.stop_reason = "end_turn"

        with patch.object(client.client.messages, 'create', return_value=mock_response):
            result = client.call_with_retry(prompt="Test")

        # Expected cost: (1000/1M * 3.0) + (500/1M * 15.0) = 0.003 + 0.0075 = 0.0105
        expected_cost = 0.0105
        assert result["cost"] == pytest.approx(expected_cost, rel=1e-6)

    def test_with_system_prompt(self):
        """Test call with system prompt."""
        client = LLMClient(api_key="test-key")

        mock_response = Mock()
        mock_response.content = [Mock(text="Response")]
        mock_response.usage = Mock(input_tokens=50, output_tokens=25)
        mock_response.model = "claude-sonnet-4-20250514"
        mock_response.stop_reason = "end_turn"

        with patch.object(client.client.messages, 'create', return_value=mock_response) as mock_create:
            client.call_with_retry(
                prompt="Test",
                system="You are a helpful assistant"
            )

            call_kwargs = mock_create.call_args[1]
            assert call_kwargs["system"] == "You are a helpful assistant"

    def test_with_extra_kwargs(self):
        """Test that extra kwargs are passed through."""
        client = LLMClient(api_key="test-key")

        mock_response = Mock()
        mock_response.content = [Mock(text="Response")]
        mock_response.usage = Mock(input_tokens=50, output_tokens=25)
        mock_response.model = "claude-sonnet-4-20250514"
        mock_response.stop_reason = "end_turn"

        with patch.object(client.client.messages, 'create', return_value=mock_response) as mock_create:
            client.call_with_retry(
                prompt="Test",
                custom_param="custom_value"
            )

            call_kwargs = mock_create.call_args[1]
            assert call_kwargs["custom_param"] == "custom_value"


class TestJSONParsing:
    """Test JSON parsing functionality."""

    def test_parse_plain_json(self):
        """Test parsing plain JSON response."""
        client = LLMClient(api_key="test-key")

        json_response = '{"key": "value", "number": 42}'
        mock_response = Mock()
        mock_response.content = [Mock(text=json_response)]
        mock_response.usage = Mock(input_tokens=50, output_tokens=25)
        mock_response.model = "claude-sonnet-4-20250514"
        mock_response.stop_reason = "end_turn"

        with patch.object(client.client.messages, 'create', return_value=mock_response):
            result = client.call_with_retry(prompt="Test")

        assert isinstance(result["content"], dict)
        assert result["content"]["key"] == "value"
        assert result["content"]["number"] == 42
        assert result["raw_content"] == json_response

    def test_parse_json_code_block(self):
        """Test parsing JSON from markdown code block."""
        client = LLMClient(api_key="test-key")

        markdown_response = '```json\n{"key": "value", "number": 42}\n```'
        mock_response = Mock()
        mock_response.content = [Mock(text=markdown_response)]
        mock_response.usage = Mock(input_tokens=50, output_tokens=25)
        mock_response.model = "claude-sonnet-4-20250514"
        mock_response.stop_reason = "end_turn"

        with patch.object(client.client.messages, 'create', return_value=mock_response):
            result = client.call_with_retry(prompt="Test")

        assert isinstance(result["content"], dict)
        assert result["content"]["key"] == "value"
        assert result["content"]["number"] == 42

    def test_parse_json_array(self):
        """Test parsing JSON array."""
        client = LLMClient(api_key="test-key")

        json_response = '[{"id": 1}, {"id": 2}]'
        mock_response = Mock()
        mock_response.content = [Mock(text=json_response)]
        mock_response.usage = Mock(input_tokens=50, output_tokens=25)
        mock_response.model = "claude-sonnet-4-20250514"
        mock_response.stop_reason = "end_turn"

        with patch.object(client.client.messages, 'create', return_value=mock_response):
            result = client.call_with_retry(prompt="Test")

        assert isinstance(result["content"], list)
        assert len(result["content"]) == 2
        assert result["content"][0]["id"] == 1

    def test_non_json_response(self):
        """Test that non-JSON response is returned as-is."""
        client = LLMClient(api_key="test-key")

        text_response = "This is plain text, not JSON"
        mock_response = Mock()
        mock_response.content = [Mock(text=text_response)]
        mock_response.usage = Mock(input_tokens=50, output_tokens=25)
        mock_response.model = "claude-sonnet-4-20250514"
        mock_response.stop_reason = "end_turn"

        with patch.object(client.client.messages, 'create', return_value=mock_response):
            result = client.call_with_retry(prompt="Test")

        assert result["content"] == text_response
        assert isinstance(result["content"], str)

    def test_malformed_json_code_block(self):
        """Test handling of malformed JSON in code block."""
        client = LLMClient(api_key="test-key")

        malformed_response = '```json\n{invalid json\n```'
        mock_response = Mock()
        mock_response.content = [Mock(text=malformed_response)]
        mock_response.usage = Mock(input_tokens=50, output_tokens=25)
        mock_response.model = "claude-sonnet-4-20250514"
        mock_response.stop_reason = "end_turn"

        with patch.object(client.client.messages, 'create', return_value=mock_response):
            result = client.call_with_retry(prompt="Test")

        # Should fall back to returning raw text
        assert isinstance(result["content"], str)


class TestRetryLogic:
    """Test retry logic and error handling."""

    def test_retry_on_connection_error(self):
        """Test retry on APIConnectionError."""
        client = LLMClient(api_key="test-key")

        # Mock successful response after retries
        mock_response = Mock()
        mock_response.content = [Mock(text="Success after retry")]
        mock_response.usage = Mock(input_tokens=50, output_tokens=25)
        mock_response.model = "claude-sonnet-4-20250514"
        mock_response.stop_reason = "end_turn"

        # First call fails, second succeeds
        call_count = [0]
        def side_effect(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] == 1:
                raise APIConnectionError("Network error")
            return mock_response

        with patch.object(client.client.messages, 'create', side_effect=side_effect):
            result = client.call_with_retry(prompt="Test")

        assert result["content"] == "Success after retry"

    def test_retry_on_rate_limit_error(self):
        """Test retry on RateLimitError."""
        client = LLMClient(api_key="test-key")

        mock_response = Mock()
        mock_response.content = [Mock(text="Success after rate limit")]
        mock_response.usage = Mock(input_tokens=50, output_tokens=25)
        mock_response.model = "claude-sonnet-4-20250514"
        mock_response.stop_reason = "end_turn"

        # First call rate limited, second succeeds
        call_count = [0]
        def side_effect(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] == 1:
                raise RateLimitError("Rate limit exceeded")
            return mock_response

        with patch.object(client.client.messages, 'create', side_effect=side_effect):
            result = client.call_with_retry(prompt="Test")

        assert result["content"] == "Success after rate limit"

    def test_max_retries_exhausted(self):
        """Test that retries are exhausted after 3 attempts."""
        client = LLMClient(api_key="test-key")

        # All attempts fail
        with patch.object(
            client.client.messages,
            'create',
            side_effect=APIConnectionError("Persistent network error")
        ):
            with pytest.raises(APIConnectionError):
                client.call_with_retry(prompt="Test")

    def test_no_retry_on_client_error(self):
        """Test that 4xx errors are not retried."""
        client = LLMClient(api_key="test-key")

        # Create mock APIStatusError for 400
        error = APIStatusError(
            message="Bad request",
            response=Mock(status_code=400),
            body={}
        )

        with patch.object(client.client.messages, 'create', side_effect=error):
            with pytest.raises(APIStatusError) as exc_info:
                client.call_with_retry(prompt="Test")

            # Should not retry, so only one attempt
            assert exc_info.value.response.status_code == 400

    def test_retry_on_server_error(self):
        """Test that 5xx errors are retried."""
        client = LLMClient(api_key="test-key")

        # Create successful response
        mock_response = Mock()
        mock_response.content = [Mock(text="Success after server error")]
        mock_response.usage = Mock(input_tokens=50, output_tokens=25)
        mock_response.model = "claude-sonnet-4-20250514"
        mock_response.stop_reason = "end_turn"

        # First call 500 error, second succeeds
        call_count = [0]
        def side_effect(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] == 1:
                server_error = APIStatusError(
                    message="Internal server error",
                    response=Mock(status_code=500),
                    body={}
                )
                raise server_error
            return mock_response

        with patch.object(client.client.messages, 'create', side_effect=side_effect):
            result = client.call_with_retry(prompt="Test")

        assert result["content"] == "Success after server error"


class TestEstimateCost:
    """Test estimate_cost method."""

    def test_estimate_cost_simple(self):
        """Test cost estimation with simple values."""
        client = LLMClient(api_key="test-key")

        # 1,000 input tokens, 500 output tokens
        cost = client.estimate_cost(input_tokens=1000, output_tokens=500)

        # Expected: (1000/1M * 3.0) + (500/1M * 15.0) = 0.003 + 0.0075 = 0.0105
        expected = 0.0105
        assert cost == pytest.approx(expected, rel=1e-6)

    def test_estimate_cost_large_values(self):
        """Test cost estimation with large token counts."""
        client = LLMClient(api_key="test-key")

        # 1 million input tokens, 500k output tokens
        cost = client.estimate_cost(input_tokens=1_000_000, output_tokens=500_000)

        # Expected: (1M/1M * 3.0) + (500k/1M * 15.0) = 3.0 + 7.5 = 10.5
        expected = 10.5
        assert cost == pytest.approx(expected, rel=1e-6)

    def test_estimate_cost_zero_tokens(self):
        """Test cost estimation with zero tokens."""
        client = LLMClient(api_key="test-key")

        cost = client.estimate_cost(input_tokens=0, output_tokens=0)
        assert cost == 0.0

    def test_estimate_cost_input_only(self):
        """Test cost estimation with only input tokens."""
        client = LLMClient(api_key="test-key")

        cost = client.estimate_cost(input_tokens=1000, output_tokens=0)

        # Expected: (1000/1M * 3.0) = 0.003
        expected = 0.003
        assert cost == pytest.approx(expected, rel=1e-6)

    def test_estimate_cost_output_only(self):
        """Test cost estimation with only output tokens."""
        client = LLMClient(api_key="test-key")

        cost = client.estimate_cost(input_tokens=0, output_tokens=500)

        # Expected: (500/1M * 15.0) = 0.0075
        expected = 0.0075
        assert cost == pytest.approx(expected, rel=1e-6)


class TestCountTokensApproximate:
    """Test count_tokens_approximate method."""

    def test_count_tokens_simple(self):
        """Test approximate token counting."""
        client = LLMClient(api_key="test-key")

        # "hello" = 5 chars, ~1-2 tokens (5 // 4 = 1)
        count = client.count_tokens_approximate("hello")
        assert count == 1

    def test_count_tokens_longer_text(self):
        """Test token counting with longer text."""
        client = LLMClient(api_key="test-key")

        # 100 chars = ~25 tokens (100 // 4 = 25)
        text = "a" * 100
        count = client.count_tokens_approximate(text)
        assert count == 25

    def test_count_tokens_empty_string(self):
        """Test token counting with empty string."""
        client = LLMClient(api_key="test-key")

        count = client.count_tokens_approximate("")
        assert count == 0

    def test_count_tokens_with_spaces(self):
        """Test token counting with spaces."""
        client = LLMClient(api_key="test-key")

        # "hello world" = 11 chars including space
        count = client.count_tokens_approximate("hello world")
        assert count == 11 // 4  # 2 tokens

    def test_count_tokens_realistic_text(self):
        """Test token counting with realistic text."""
        client = LLMClient(api_key="test-key")

        text = "This is a test sentence with approximately twenty tokens or so."
        count = client.count_tokens_approximate(text)

        # Should be roughly text length / 4
        expected_approx = len(text) // 4
        assert count == expected_approx


class TestTryParseJSON:
    """Test _try_parse_json internal method."""

    def test_try_parse_json_valid_object(self):
        """Test parsing valid JSON object."""
        client = LLMClient(api_key="test-key")

        result = client._try_parse_json('{"key": "value"}')
        assert isinstance(result, dict)
        assert result["key"] == "value"

    def test_try_parse_json_valid_array(self):
        """Test parsing valid JSON array."""
        client = LLMClient(api_key="test-key")

        result = client._try_parse_json('[1, 2, 3]')
        assert isinstance(result, list)
        assert result == [1, 2, 3]

    def test_try_parse_json_code_block(self):
        """Test parsing JSON from code block."""
        client = LLMClient(api_key="test-key")

        text = 'Here is the result:\n```json\n{"status": "success"}\n```\nDone.'
        result = client._try_parse_json(text)
        assert isinstance(result, dict)
        assert result["status"] == "success"

    def test_try_parse_json_plain_text(self):
        """Test that plain text is returned as-is."""
        client = LLMClient(api_key="test-key")

        result = client._try_parse_json("This is not JSON")
        assert result == "This is not JSON"

    def test_try_parse_json_invalid_json(self):
        """Test that invalid JSON is returned as-is."""
        client = LLMClient(api_key="test-key")

        result = client._try_parse_json("{invalid json}")
        assert result == "{invalid json}"
