"""
ASP LLM Provider Abstraction Layer.

This package provides a unified interface for multiple LLM providers,
enabling flexibility, cost optimization, and vendor independence.

Supported Providers:
- Cloud: Anthropic (default), OpenRouter, Groq, Gemini, Together, Fireworks, DeepInfra
- Local: Ollama, vLLM, Claude CLI

Usage:
    from asp.providers import ProviderRegistry, LLMResponse

    # Get default provider (Anthropic)
    provider = ProviderRegistry.get_default()

    # Get specific provider
    provider = ProviderRegistry.get("openrouter")
    provider = ProviderRegistry.get("groq")

    # Make LLM call
    response = await provider.call_async("Hello, world!")

Author: ASP Development Team
Date: December 2025
"""

from asp.providers.base import LLMProvider, LLMResponse, ProviderConfig
from asp.providers.errors import (
    AuthenticationError,
    ConnectionError,
    ContentFilterError,
    InvalidRequestError,
    ModelNotFoundError,
    ProviderError,
    RateLimitError,
    TimeoutError,
)

# Import OpenAI-compatible base for subclassing
from asp.providers.openai_compat import OpenAICompatibleProvider
from asp.providers.registry import ProviderRegistry, get_default_provider, get_provider

__all__ = [
    # Base types
    "LLMProvider",
    "LLMResponse",
    "ProviderConfig",
    "OpenAICompatibleProvider",
    # Registry
    "ProviderRegistry",
    "get_provider",
    "get_default_provider",
    # Errors
    "ProviderError",
    "RateLimitError",
    "AuthenticationError",
    "ModelNotFoundError",
    "ConnectionError",
    "TimeoutError",
    "InvalidRequestError",
    "ContentFilterError",
]
