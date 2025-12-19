"""
ASP LLM Provider Abstraction Layer.

This package provides a unified interface for multiple LLM providers,
enabling flexibility, cost optimization, and vendor independence.

Supported Providers:
- Cloud: Anthropic (default), OpenRouter, Gemini, Groq, Together, Fireworks, DeepInfra
- Local: Ollama, vLLM, Claude CLI

Usage:
    from asp.providers import ProviderRegistry, LLMResponse

    # Get default provider (Anthropic)
    provider = ProviderRegistry.get_default()

    # Get specific provider
    provider = ProviderRegistry.get("openrouter")

    # Make LLM call
    response = await provider.call_async("Hello, world!")

Author: ASP Development Team
Date: December 2025
"""

from asp.providers.base import (
    LLMProvider,
    LLMResponse,
    ProviderConfig,
)
from asp.providers.errors import (
    AuthenticationError,
    ModelNotFoundError,
    ProviderError,
    RateLimitError,
)
from asp.providers.registry import ProviderRegistry

__all__ = [
    # Base types
    "LLMProvider",
    "LLMResponse",
    "ProviderConfig",
    # Registry
    "ProviderRegistry",
    # Errors
    "ProviderError",
    "RateLimitError",
    "AuthenticationError",
    "ModelNotFoundError",
]
