"""
Unit tests for the LLM Provider abstraction layer.

Tests cover:
- LLMResponse dataclass
- ProviderConfig dataclass
- ProviderRegistry
- AnthropicProvider (mocked)
- Error types

Author: ASP Development Team
Date: December 2025
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from asp.providers import (
    LLMResponse,
    ProviderConfig,
    ProviderRegistry,
)
from asp.providers.errors import (
    AuthenticationError,
    ConnectionError,
    ModelNotFoundError,
    ProviderError,
    RateLimitError,
)


class TestLLMResponse:
    """Tests for LLMResponse dataclass."""

    def test_create_response(self):
        """Test creating an LLMResponse."""
        response = LLMResponse(
            content={"key": "value"},
            raw_content='{"key": "value"}',
            usage={"input_tokens": 100, "output_tokens": 50},
            cost=0.001,
            model="claude-haiku-4-5",
            provider="anthropic",
            stop_reason="end_turn",
        )

        assert response.content == {"key": "value"}
        assert response.raw_content == '{"key": "value"}'
        assert response.usage["input_tokens"] == 100
        assert response.usage["output_tokens"] == 50
        assert response.cost == 0.001
        assert response.model == "claude-haiku-4-5"
        assert response.provider == "anthropic"
        assert response.stop_reason == "end_turn"

    def test_response_with_string_content(self):
        """Test response with plain text content."""
        response = LLMResponse(
            content="Hello, world!",
            raw_content="Hello, world!",
            usage={"input_tokens": 10, "output_tokens": 5},
            cost=0.0001,
            model="claude-haiku-4-5",
            provider="anthropic",
        )

        assert response.content == "Hello, world!"
        assert response.stop_reason is None

    def test_to_dict(self):
        """Test converting response to dictionary."""
        response = LLMResponse(
            content="test",
            raw_content="test",
            usage={"input_tokens": 10, "output_tokens": 5},
            cost=0.0001,
            model="test-model",
            provider="test-provider",
        )

        result = response.to_dict()

        assert isinstance(result, dict)
        assert result["content"] == "test"
        assert result["model"] == "test-model"
        assert result["provider"] == "test-provider"
        assert "usage" in result
        assert "cost" in result

    def test_default_metadata(self):
        """Test that metadata defaults to empty dict."""
        response = LLMResponse(
            content="test",
            raw_content="test",
            usage={},
            cost=None,
            model="test",
            provider="test",
        )

        assert response.metadata == {}


class TestProviderConfig:
    """Tests for ProviderConfig dataclass."""

    def test_default_config(self):
        """Test default configuration values."""
        config = ProviderConfig()

        assert config.api_key is None
        assert config.base_url is None
        assert config.default_model is None
        assert config.timeout == 120.0
        assert config.max_retries == 3
        assert config.extra == {}

    def test_custom_config(self):
        """Test custom configuration."""
        config = ProviderConfig(
            api_key="test-key",
            base_url="https://api.example.com",
            default_model="test-model",
            timeout=60.0,
            max_retries=5,
            extra={"custom": "value"},
        )

        assert config.api_key == "test-key"
        assert config.base_url == "https://api.example.com"
        assert config.default_model == "test-model"
        assert config.timeout == 60.0
        assert config.max_retries == 5
        assert config.extra == {"custom": "value"}


class TestProviderErrors:
    """Tests for provider error types."""

    def test_provider_error(self):
        """Test base ProviderError."""
        error = ProviderError("Something went wrong", provider="test")

        assert str(error) == "[test] Something went wrong"
        assert error.message == "Something went wrong"
        assert error.provider == "test"
        assert error.details == {}

    def test_provider_error_without_provider(self):
        """Test ProviderError without provider name."""
        error = ProviderError("Error message")

        assert str(error) == "Error message"
        assert error.provider is None

    def test_rate_limit_error(self):
        """Test RateLimitError with retry_after."""
        error = RateLimitError(
            "Rate limit exceeded",
            provider="anthropic",
            retry_after=30.0,
        )

        assert error.retry_after == 30.0
        assert "Rate limit" in str(error)

    def test_authentication_error(self):
        """Test AuthenticationError."""
        error = AuthenticationError(
            "Invalid API key",
            provider="anthropic",
        )

        assert "Invalid API key" in str(error)
        assert error.provider == "anthropic"

    def test_model_not_found_error(self):
        """Test ModelNotFoundError."""
        error = ModelNotFoundError(
            "Model not available",
            provider="anthropic",
            model="claude-unknown",
            available_models=["claude-haiku-4-5", "claude-sonnet-4-5"],
        )

        assert error.model == "claude-unknown"
        assert "claude-haiku-4-5" in error.available_models

    def test_connection_error(self):
        """Test ConnectionError."""
        error = ConnectionError(
            "Network unreachable",
            provider="anthropic",
        )

        assert "Network unreachable" in str(error)


class TestProviderRegistry:
    """Tests for ProviderRegistry."""

    def setup_method(self):
        """Clear registry before each test."""
        ProviderRegistry._providers.clear()
        ProviderRegistry._instances.clear()

    def test_list_providers(self):
        """Test listing registered providers."""
        # Should auto-register built-in providers
        providers = ProviderRegistry.list_providers()

        assert isinstance(providers, list)
        assert "anthropic" in providers

    def test_is_registered(self):
        """Test checking if provider is registered."""
        assert ProviderRegistry.is_registered("anthropic")
        assert not ProviderRegistry.is_registered("unknown")

    def test_get_unknown_provider(self):
        """Test getting an unknown provider raises error."""
        with pytest.raises(ProviderError) as exc_info:
            ProviderRegistry.get("unknown")

        assert "Unknown provider" in str(exc_info.value)
        assert "unknown" in str(exc_info.value)

    def test_clear_cache(self):
        """Test clearing the provider instance cache."""
        # First ensure some state
        ProviderRegistry._instances["test"] = MagicMock()

        ProviderRegistry.clear_cache()

        assert len(ProviderRegistry._instances) == 0


class TestAnthropicProvider:
    """Tests for AnthropicProvider."""

    def test_init_without_api_key(self):
        """Test initialization fails without API key."""
        with patch.dict("os.environ", {}, clear=True):
            # Remove ANTHROPIC_API_KEY if present
            import os

            os.environ.pop("ANTHROPIC_API_KEY", None)

            with pytest.raises(AuthenticationError) as exc_info:
                from asp.providers.anthropic_provider import AnthropicProvider

                AnthropicProvider()

            assert "API key not found" in str(exc_info.value)

    def test_init_with_config_api_key(self):
        """Test initialization with API key in config."""
        from asp.providers.anthropic_provider import AnthropicProvider

        config = ProviderConfig(api_key="test-api-key")
        provider = AnthropicProvider(config)

        assert provider._api_key == "test-api-key"
        assert provider.name == "anthropic"

    def test_available_models(self):
        """Test listing available models."""
        from asp.providers.anthropic_provider import AnthropicProvider

        config = ProviderConfig(api_key="test-key")
        provider = AnthropicProvider(config)

        models = provider.available_models

        assert isinstance(models, list)
        assert "claude-haiku-4-5" in models
        assert "claude-sonnet-4-5" in models

    def test_estimate_cost(self):
        """Test cost estimation."""
        from asp.providers.anthropic_provider import AnthropicProvider

        config = ProviderConfig(api_key="test-key")
        provider = AnthropicProvider(config)

        # Haiku pricing: $0.25 input, $1.25 output per million tokens
        cost = provider.estimate_cost(
            model="claude-haiku-4-5",
            input_tokens=1_000_000,
            output_tokens=1_000_000,
        )

        assert cost == 0.25 + 1.25  # $1.50 total

    def test_estimate_cost_unknown_model_fallback(self):
        """Test cost estimation falls back to Haiku for unknown models."""
        from asp.providers.anthropic_provider import AnthropicProvider

        config = ProviderConfig(api_key="test-key")
        provider = AnthropicProvider(config)

        cost = provider.estimate_cost(
            model="unknown-model",
            input_tokens=1_000_000,
            output_tokens=1_000_000,
        )

        # Should use Haiku pricing as fallback
        assert cost == 0.25 + 1.25

    def test_default_model(self):
        """Test default model configuration."""
        from asp.providers.anthropic_provider import AnthropicProvider

        # Default
        config = ProviderConfig(api_key="test-key")
        provider = AnthropicProvider(config)
        assert provider.default_model == "claude-haiku-4-5"

        # Custom default
        config = ProviderConfig(api_key="test-key", default_model="claude-sonnet-4-5")
        provider = AnthropicProvider(config)
        assert provider.default_model == "claude-sonnet-4-5"

    def test_try_parse_json_valid(self):
        """Test JSON parsing with valid JSON."""
        from asp.providers.anthropic_provider import AnthropicProvider

        config = ProviderConfig(api_key="test-key")
        provider = AnthropicProvider(config)

        result = provider._try_parse_json('{"key": "value"}')

        assert result == {"key": "value"}

    def test_try_parse_json_markdown_block(self):
        """Test JSON parsing with markdown code block."""
        from asp.providers.anthropic_provider import AnthropicProvider

        config = ProviderConfig(api_key="test-key")
        provider = AnthropicProvider(config)

        result = provider._try_parse_json('```json\n{"key": "value"}\n```')

        assert result == {"key": "value"}

    def test_try_parse_json_invalid(self):
        """Test JSON parsing with non-JSON text."""
        from asp.providers.anthropic_provider import AnthropicProvider

        config = ProviderConfig(api_key="test-key")
        provider = AnthropicProvider(config)

        result = provider._try_parse_json("Just plain text")

        assert result == "Just plain text"

    @pytest.mark.asyncio
    async def test_call_async_mocked(self):
        """Test async call with mocked Anthropic client."""
        from asp.providers.anthropic_provider import AnthropicProvider

        config = ProviderConfig(api_key="test-key")
        provider = AnthropicProvider(config)

        # Mock the async client
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text='{"result": "success"}')]
        mock_response.usage.input_tokens = 100
        mock_response.usage.output_tokens = 50
        mock_response.model = "claude-haiku-4-5"
        mock_response.stop_reason = "end_turn"

        mock_client = AsyncMock()
        mock_client.messages.create = AsyncMock(return_value=mock_response)
        provider._async_client_impl = mock_client

        response = await provider.call_async(
            prompt="Test prompt",
            model="claude-haiku-4-5",
        )

        assert response.content == {"result": "success"}
        assert response.provider == "anthropic"
        assert response.usage["input_tokens"] == 100
        assert response.usage["output_tokens"] == 50
