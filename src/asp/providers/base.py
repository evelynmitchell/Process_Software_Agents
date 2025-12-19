"""
Base types for LLM Provider abstraction.

This module defines the core interfaces and data classes for the
multi-provider LLM system.

Author: ASP Development Team
Date: December 2025
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class LLMResponse:
    """
    Normalized response from any LLM provider.

    All providers return this common format, enabling consistent handling
    regardless of the underlying LLM service.

    Attributes:
        content: Parsed content (dict if JSON, str otherwise)
        raw_content: Original text response from the LLM
        usage: Token usage dict with 'input_tokens' and 'output_tokens'
        cost: Estimated cost in USD (None if unknown)
        model: Model identifier used for the request
        provider: Provider name (e.g., "anthropic", "openrouter")
        stop_reason: Why generation stopped (e.g., "end_turn", "max_tokens")
        metadata: Additional provider-specific metadata
    """

    content: str | dict[str, Any]
    raw_content: str
    usage: dict[str, int]
    cost: float | None
    model: str
    provider: str
    stop_reason: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert response to dictionary format for backward compatibility."""
        return {
            "content": self.content,
            "raw_content": self.raw_content,
            "usage": self.usage,
            "cost": self.cost,
            "model": self.model,
            "provider": self.provider,
            "stop_reason": self.stop_reason,
            "metadata": self.metadata,
        }


@dataclass
class ProviderConfig:
    """
    Configuration for an LLM provider.

    Attributes:
        api_key: API key for authentication (falls back to env var)
        base_url: Custom API endpoint URL (for self-hosted or proxies)
        default_model: Default model to use if not specified
        timeout: Request timeout in seconds
        max_retries: Maximum retry attempts for transient failures
        extra: Provider-specific additional configuration
    """

    api_key: str | None = None
    base_url: str | None = None
    default_model: str | None = None
    timeout: float = 120.0
    max_retries: int = 3
    extra: dict[str, Any] = field(default_factory=dict)


class LLMProvider(ABC):
    """
    Abstract base class for LLM providers.

    All LLM providers must implement this interface to be compatible
    with the ASP platform. This enables consistent behavior across
    Anthropic, OpenRouter, Gemini, and other providers.

    Example Implementation:
        class MyProvider(LLMProvider):
            name = "myprovider"

            def __init__(self, config: ProviderConfig | None = None):
                self.config = config or ProviderConfig()
                # Initialize provider-specific client

            async def call_async(self, prompt: str, **kwargs) -> LLMResponse:
                # Make async API call
                ...
    """

    # Provider identifier (e.g., "anthropic", "openrouter", "gemini")
    name: str

    @abstractmethod
    def __init__(self, config: ProviderConfig | None = None):
        """
        Initialize the provider with optional configuration.

        Args:
            config: Provider configuration (API key, base URL, etc.)
        """
        ...

    @abstractmethod
    def call(
        self,
        prompt: str,
        model: str | None = None,
        max_tokens: int = 4096,
        temperature: float = 0.0,
        system: str | None = None,
        **kwargs: Any,
    ) -> LLMResponse:
        """
        Make a synchronous LLM call.

        Args:
            prompt: User prompt text
            model: Model identifier (uses default if not specified)
            max_tokens: Maximum tokens in response
            temperature: Sampling temperature (0.0 = deterministic)
            system: Optional system prompt
            **kwargs: Provider-specific additional arguments

        Returns:
            LLMResponse with normalized response data

        Raises:
            ProviderError: Base class for provider errors
            RateLimitError: Rate limit exceeded
            AuthenticationError: Invalid credentials
            ModelNotFoundError: Requested model unavailable
        """
        ...

    @abstractmethod
    async def call_async(
        self,
        prompt: str,
        model: str | None = None,
        max_tokens: int = 4096,
        temperature: float = 0.0,
        system: str | None = None,
        **kwargs: Any,
    ) -> LLMResponse:
        """
        Make an asynchronous LLM call.

        This is the preferred method for concurrent operations.
        See call() for parameter documentation.

        Returns:
            LLMResponse with normalized response data
        """
        ...

    @abstractmethod
    def estimate_cost(
        self,
        model: str,
        input_tokens: int,
        output_tokens: int,
    ) -> float:
        """
        Estimate cost for token usage.

        Args:
            model: Model identifier
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens

        Returns:
            Estimated cost in USD
        """
        ...

    @property
    @abstractmethod
    def available_models(self) -> list[str]:
        """
        List available models for this provider.

        Returns:
            List of model identifiers
        """
        ...

    @property
    def default_model(self) -> str | None:
        """Get the default model for this provider."""
        return getattr(self, "_default_model", None)
