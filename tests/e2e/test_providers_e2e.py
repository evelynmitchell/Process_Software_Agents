"""
End-to-End tests for LLM Provider implementations.

These tests verify actual API connectivity and response handling for each provider.
Tests are skipped when the corresponding API key is not available.

Environment Variables Required:
- ANTHROPIC_API_KEY: For Anthropic provider tests
- OPENROUTER_API_KEY: For OpenRouter provider tests
- GROQ_API_KEY: For Groq provider tests

Run with:
    # Run all provider e2e tests (skips those without API keys)
    pytest tests/e2e/test_providers_e2e.py -v -s

    # Run only tests for a specific provider
    pytest tests/e2e/test_providers_e2e.py -v -s -k "anthropic"

GitHub Actions Setup:
    Add secrets: ANTHROPIC_API_KEY, OPENROUTER_API_KEY, GROQ_API_KEY
    See: .github/workflows/provider-e2e.yml

Author: ASP Development Team
Date: December 2025
"""

import os

import pytest

from asp.providers import ProviderConfig, ProviderRegistry
from asp.providers.errors import AuthenticationError, ProviderError

# =============================================================================
# Skip Conditions
# =============================================================================

HAS_ANTHROPIC_KEY = bool(os.getenv("ANTHROPIC_API_KEY"))
HAS_OPENROUTER_KEY = bool(os.getenv("OPENROUTER_API_KEY"))
HAS_GROQ_KEY = bool(os.getenv("GROQ_API_KEY"))

skip_without_anthropic = pytest.mark.skipif(
    not HAS_ANTHROPIC_KEY,
    reason="ANTHROPIC_API_KEY not set - skipping Anthropic e2e tests",
)

skip_without_openrouter = pytest.mark.skipif(
    not HAS_OPENROUTER_KEY,
    reason="OPENROUTER_API_KEY not set - skipping OpenRouter e2e tests",
)

skip_without_groq = pytest.mark.skipif(
    not HAS_GROQ_KEY, reason="GROQ_API_KEY not set - skipping Groq e2e tests"
)


# =============================================================================
# Test Fixtures
# =============================================================================


@pytest.fixture
def minimal_prompt() -> str:
    """A minimal prompt to reduce token usage and cost."""
    return "Reply with exactly one word: Hello"


@pytest.fixture
def json_prompt() -> str:
    """A prompt requesting JSON response."""
    return 'Reply with valid JSON only: {"status": "ok"}'


# =============================================================================
# Anthropic Provider E2E Tests
# =============================================================================


@pytest.mark.e2e
@pytest.mark.provider
class TestAnthropicProviderE2E:
    """E2E tests for Anthropic provider with real API calls."""

    @skip_without_anthropic
    def test_basic_call_sync(self, minimal_prompt):
        """Test synchronous API call to Anthropic."""
        from asp.providers.anthropic_provider import AnthropicProvider

        provider = AnthropicProvider()

        response = provider.call(
            prompt=minimal_prompt,
            model="claude-haiku-4-5",
            max_tokens=10,
            temperature=0.0,
        )

        # Validate response structure
        assert response is not None
        assert response.provider == "anthropic"
        assert response.model == "claude-haiku-4-5"
        assert response.content is not None
        assert response.usage["input_tokens"] > 0
        assert response.usage["output_tokens"] > 0
        assert response.stop_reason is not None

        print(f"\n  Response: {response.content}")
        print(f"  Tokens: {response.usage}")

    @skip_without_anthropic
    @pytest.mark.asyncio
    async def test_basic_call_async(self, minimal_prompt):
        """Test asynchronous API call to Anthropic."""
        from asp.providers.anthropic_provider import AnthropicProvider

        provider = AnthropicProvider()

        response = await provider.call_async(
            prompt=minimal_prompt,
            model="claude-haiku-4-5",
            max_tokens=10,
            temperature=0.0,
        )

        assert response is not None
        assert response.provider == "anthropic"
        assert response.content is not None
        assert response.usage["input_tokens"] > 0

        print(f"\n  Async Response: {response.content}")

    @skip_without_anthropic
    def test_json_response_parsing(self, json_prompt):
        """Test that JSON responses are properly parsed."""
        from asp.providers.anthropic_provider import AnthropicProvider

        provider = AnthropicProvider()

        response = provider.call(
            prompt=json_prompt,
            model="claude-haiku-4-5",
            max_tokens=50,
            temperature=0.0,
        )

        # Content should be parsed as dict if valid JSON
        assert response.content is not None
        # raw_content should always be string
        assert isinstance(response.raw_content, str)

        print(f"\n  Parsed content type: {type(response.content)}")
        print(f"  Content: {response.content}")

    @skip_without_anthropic
    def test_available_models(self):
        """Test that available models list is populated."""
        from asp.providers.anthropic_provider import AnthropicProvider

        provider = AnthropicProvider()
        models = provider.available_models

        assert isinstance(models, list)
        assert len(models) > 0
        assert "claude-haiku-4-5" in models

        print(f"\n  Available models: {models}")

    @skip_without_anthropic
    def test_cost_estimation(self):
        """Test cost estimation returns reasonable values."""
        from asp.providers.anthropic_provider import AnthropicProvider

        provider = AnthropicProvider()

        cost = provider.estimate_cost(
            model="claude-haiku-4-5",
            input_tokens=1000,
            output_tokens=500,
        )

        assert cost > 0
        assert cost < 0.01  # Haiku should be cheap for this usage

        print(f"\n  Estimated cost for 1K in / 500 out: ${cost:.6f}")

    def test_invalid_api_key_raises_error(self):
        """Test that invalid API key raises AuthenticationError."""
        from asp.providers.anthropic_provider import AnthropicProvider

        config = ProviderConfig(api_key="invalid-key-12345")

        # Should still initialize (key validation happens on call)
        provider = AnthropicProvider(config)

        with pytest.raises((AuthenticationError, ProviderError)):
            provider.call(
                prompt="test",
                model="claude-haiku-4-5",
                max_tokens=10,
            )


# =============================================================================
# OpenRouter Provider E2E Tests
# =============================================================================


@pytest.mark.e2e
@pytest.mark.provider
class TestOpenRouterProviderE2E:
    """E2E tests for OpenRouter provider with real API calls."""

    @skip_without_openrouter
    def test_basic_call_sync(self, minimal_prompt):
        """Test synchronous API call to OpenRouter."""
        from asp.providers.openrouter_provider import OpenRouterProvider

        provider = OpenRouterProvider()

        response = provider.call(
            prompt=minimal_prompt,
            model="anthropic/claude-3.5-haiku",  # Cheapest Claude on OpenRouter
            max_tokens=10,
            temperature=0.0,
        )

        assert response is not None
        assert response.provider == "openrouter"
        assert response.content is not None
        assert response.usage["input_tokens"] > 0
        assert response.usage["output_tokens"] > 0

        print(f"\n  Response: {response.content}")
        print(f"  Tokens: {response.usage}")

    @skip_without_openrouter
    @pytest.mark.asyncio
    async def test_basic_call_async(self, minimal_prompt):
        """Test asynchronous API call to OpenRouter."""
        from asp.providers.openrouter_provider import OpenRouterProvider

        provider = OpenRouterProvider()

        response = await provider.call_async(
            prompt=minimal_prompt,
            model="anthropic/claude-3.5-haiku",
            max_tokens=10,
            temperature=0.0,
        )

        assert response is not None
        assert response.provider == "openrouter"
        assert response.content is not None

        print(f"\n  Async Response: {response.content}")

    @skip_without_openrouter
    def test_available_models(self):
        """Test that available models list is populated."""
        from asp.providers.openrouter_provider import OpenRouterProvider

        provider = OpenRouterProvider()
        models = provider.available_models

        assert isinstance(models, list)
        assert len(models) > 0

        print(f"\n  Available models: {models[:5]}...")

    @skip_without_openrouter
    def test_headers_include_referer(self):
        """Test that OpenRouter-specific headers are set."""
        from asp.providers.openrouter_provider import OpenRouterProvider

        provider = OpenRouterProvider()
        headers = provider._get_headers()

        assert "HTTP-Referer" in headers
        assert "X-Title" in headers

        print(f"\n  Headers: {headers}")

    def test_invalid_api_key_raises_error(self):
        """Test that invalid API key raises appropriate error."""
        from asp.providers.openrouter_provider import OpenRouterProvider

        config = ProviderConfig(api_key="invalid-key-12345")
        provider = OpenRouterProvider(config)

        with pytest.raises((AuthenticationError, ProviderError)):
            provider.call(
                prompt="test",
                model="anthropic/claude-3.5-haiku",
                max_tokens=10,
            )


# =============================================================================
# Groq Provider E2E Tests
# =============================================================================


@pytest.mark.e2e
@pytest.mark.provider
class TestGroqProviderE2E:
    """E2E tests for Groq provider with real API calls."""

    @skip_without_groq
    def test_basic_call_sync(self, minimal_prompt):
        """Test synchronous API call to Groq."""
        from asp.providers.groq_provider import GroqProvider

        provider = GroqProvider()

        response = provider.call(
            prompt=minimal_prompt,
            model="llama-3.1-8b-instant",  # Fast and cheap
            max_tokens=10,
            temperature=0.0,
        )

        assert response is not None
        assert response.provider == "groq"
        assert response.content is not None
        assert response.usage["input_tokens"] > 0
        assert response.usage["output_tokens"] > 0

        print(f"\n  Response: {response.content}")
        print(f"  Tokens: {response.usage}")

    @skip_without_groq
    @pytest.mark.asyncio
    async def test_basic_call_async(self, minimal_prompt):
        """Test asynchronous API call to Groq."""
        from asp.providers.groq_provider import GroqProvider

        provider = GroqProvider()

        response = await provider.call_async(
            prompt=minimal_prompt,
            model="llama-3.1-8b-instant",
            max_tokens=10,
            temperature=0.0,
        )

        assert response is not None
        assert response.provider == "groq"
        assert response.content is not None

        print(f"\n  Async Response: {response.content}")

    @skip_without_groq
    def test_ultra_fast_inference(self, minimal_prompt):
        """Test Groq's ultra-fast LPU inference."""
        import time

        from asp.providers.groq_provider import GroqProvider

        provider = GroqProvider()

        start = time.time()
        response = provider.call(
            prompt=minimal_prompt,
            model="llama-3.1-8b-instant",
            max_tokens=10,
            temperature=0.0,
        )
        elapsed = time.time() - start

        assert response is not None
        # Groq should be very fast (typically < 1 second for small prompts)
        print(f"\n  Response time: {elapsed:.3f}s")
        print(f"  Response: {response.content}")

    @skip_without_groq
    def test_available_models(self):
        """Test that available models list is populated."""
        from asp.providers.groq_provider import GroqProvider

        provider = GroqProvider()
        models = provider.available_models

        assert isinstance(models, list)
        assert len(models) > 0
        assert "llama-3.1-8b-instant" in models or "llama-3.3-70b-versatile" in models

        print(f"\n  Available models: {models}")

    def test_invalid_api_key_raises_error(self):
        """Test that invalid API key raises appropriate error."""
        from asp.providers.groq_provider import GroqProvider

        config = ProviderConfig(api_key="invalid-key-12345")
        provider = GroqProvider(config)

        with pytest.raises((AuthenticationError, ProviderError)):
            provider.call(
                prompt="test",
                model="llama-3.1-8b-instant",
                max_tokens=10,
            )


# =============================================================================
# Provider Registry E2E Tests
# =============================================================================


@pytest.mark.e2e
@pytest.mark.provider
class TestProviderRegistryE2E:
    """E2E tests for ProviderRegistry with available providers."""

    def test_registry_lists_all_providers(self):
        """Test that registry includes all implemented providers."""
        providers = ProviderRegistry.list_providers()

        assert "anthropic" in providers
        assert "openrouter" in providers
        assert "groq" in providers

        print(f"\n  Registered providers: {providers}")

    @skip_without_anthropic
    def test_get_anthropic_provider(self):
        """Test getting Anthropic provider from registry."""
        provider = ProviderRegistry.get("anthropic")

        assert provider is not None
        assert provider.name == "anthropic"

    @skip_without_openrouter
    def test_get_openrouter_provider(self):
        """Test getting OpenRouter provider from registry."""
        provider = ProviderRegistry.get("openrouter")

        assert provider is not None
        assert provider.name == "openrouter"

    @skip_without_groq
    def test_get_groq_provider(self):
        """Test getting Groq provider from registry."""
        provider = ProviderRegistry.get("groq")

        assert provider is not None
        assert provider.name == "groq"


# =============================================================================
# Cross-Provider Comparison Tests (requires multiple keys)
# =============================================================================


@pytest.mark.e2e
@pytest.mark.provider
class TestCrossProviderE2E:
    """Tests comparing behavior across providers."""

    @pytest.mark.skipif(
        not (HAS_ANTHROPIC_KEY and HAS_GROQ_KEY),
        reason="Requires both ANTHROPIC_API_KEY and GROQ_API_KEY",
    )
    def test_same_prompt_different_providers(self, minimal_prompt):
        """Test that different providers return similar responses."""
        from asp.providers.anthropic_provider import AnthropicProvider
        from asp.providers.groq_provider import GroqProvider

        anthropic = AnthropicProvider()
        groq = GroqProvider()

        anthropic_response = anthropic.call(
            prompt=minimal_prompt,
            model="claude-haiku-4-5",
            max_tokens=10,
        )

        groq_response = groq.call(
            prompt=minimal_prompt,
            model="llama-3.1-8b-instant",
            max_tokens=10,
        )

        # Both should return something
        assert anthropic_response.content is not None
        assert groq_response.content is not None

        print(f"\n  Anthropic: {anthropic_response.content}")
        print(f"  Groq: {groq_response.content}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s", "-m", "e2e and provider"])
