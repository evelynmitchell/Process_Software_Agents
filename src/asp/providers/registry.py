"""
Provider Registry for managing LLM providers.

This module provides a central registry for discovering and instantiating
LLM providers. Providers are registered by name and can be retrieved
dynamically based on configuration.

Author: ASP Development Team
Date: December 2025
"""

import logging
import os
from typing import TYPE_CHECKING

from asp.providers.base import LLMProvider, ProviderConfig
from asp.providers.errors import ProviderError

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


class ProviderRegistry:
    """
    Registry for LLM providers.

    Manages provider registration, instantiation, and lifecycle.
    Supports lazy loading of providers to avoid importing unused SDKs.

    Usage:
        # Register a provider
        ProviderRegistry.register("myprovider", MyProvider)

        # Get a provider instance
        provider = ProviderRegistry.get("anthropic")

        # Get default provider (from ASP_LLM_PROVIDER env var)
        provider = ProviderRegistry.get_default()

        # List available providers
        providers = ProviderRegistry.list_providers()
    """

    # Registered provider classes (lazy-loaded)
    _providers: dict[str, type[LLMProvider]] = {}

    # Cached provider instances (singleton per config)
    _instances: dict[str, LLMProvider] = {}

    # Default provider name (from env var or "anthropic")
    DEFAULT_PROVIDER = "anthropic"

    @classmethod
    def register(cls, name: str, provider_class: type[LLMProvider]) -> None:
        """
        Register a provider class.

        Args:
            name: Unique provider identifier (e.g., "anthropic", "openrouter")
            provider_class: Provider class implementing LLMProvider

        Example:
            ProviderRegistry.register("anthropic", AnthropicProvider)
        """
        cls._providers[name] = provider_class
        logger.debug("Registered provider: %s", name)

    @classmethod
    def get(
        cls,
        name: str,
        config: ProviderConfig | None = None,
        force_new: bool = False,
    ) -> LLMProvider:
        """
        Get or create a provider instance.

        By default, returns a cached instance for the given provider name.
        Use force_new=True to create a fresh instance.

        Args:
            name: Provider identifier
            config: Optional provider configuration
            force_new: Create new instance even if cached

        Returns:
            LLMProvider instance

        Raises:
            ProviderError: If provider is not registered
        """
        # Ensure built-in providers are registered
        cls._ensure_builtin_providers()

        if name not in cls._providers:
            available = ", ".join(cls._providers.keys())
            raise ProviderError(
                f"Unknown provider: '{name}'. Available: {available}",
                provider=name,
            )

        # Return cached instance if available and not forcing new
        cache_key = f"{name}:{id(config) if config else 'default'}"
        if not force_new and cache_key in cls._instances:
            return cls._instances[cache_key]

        # Create new instance
        provider_class = cls._providers[name]
        instance = provider_class(config)
        cls._instances[cache_key] = instance

        logger.info("Created provider instance: %s", name)
        return instance

    @classmethod
    def get_default(cls, config: ProviderConfig | None = None) -> LLMProvider:
        """
        Get the default provider.

        Uses ASP_LLM_PROVIDER environment variable if set,
        otherwise falls back to "anthropic".

        Args:
            config: Optional provider configuration

        Returns:
            Default LLMProvider instance
        """
        provider_name = os.getenv("ASP_LLM_PROVIDER", cls.DEFAULT_PROVIDER)
        return cls.get(provider_name, config)

    @classmethod
    def list_providers(cls) -> list[str]:
        """
        List all registered provider names.

        Returns:
            List of provider identifiers
        """
        cls._ensure_builtin_providers()
        return list(cls._providers.keys())

    @classmethod
    def is_registered(cls, name: str) -> bool:
        """
        Check if a provider is registered.

        Args:
            name: Provider identifier

        Returns:
            True if provider is registered
        """
        cls._ensure_builtin_providers()
        return name in cls._providers

    @classmethod
    def clear_cache(cls) -> None:
        """
        Clear all cached provider instances.

        Useful for testing or reconfiguration.
        """
        cls._instances.clear()
        logger.debug("Cleared provider instance cache")

    @classmethod
    def _ensure_builtin_providers(cls) -> None:
        """
        Lazily register built-in providers.

        This is called automatically when accessing the registry.
        Providers are only imported when first accessed.
        """
        if cls._providers:
            return  # Already registered

        # Register Anthropic provider (default)
        try:
            from asp.providers.anthropic_provider import AnthropicProvider

            cls.register("anthropic", AnthropicProvider)
        except ImportError:
            logger.debug("AnthropicProvider not available (missing anthropic SDK)")

        # Register OpenRouter provider (100+ models)
        try:
            from asp.providers.openrouter_provider import OpenRouterProvider

            cls.register("openrouter", OpenRouterProvider)
        except ImportError:
            logger.debug("OpenRouterProvider not available (missing openai SDK)")

        # Register Groq provider (ultra-fast LPU inference)
        try:
            from asp.providers.groq_provider import GroqProvider

            cls.register("groq", GroqProvider)
        except ImportError:
            logger.debug("GroqProvider not available (missing openai SDK)")

        # Register Claude CLI provider (subprocess-based, subscription billing)
        try:
            from asp.providers.claude_cli_provider import ClaudeCLIProvider

            cls.register("claude_cli", ClaudeCLIProvider)
        except ImportError:
            logger.debug("ClaudeCLIProvider not available")

        # Future providers will be registered here as they are implemented:
        # - gemini (uses google-generativeai SDK)
        # - together (OpenAI-compatible)
        # - fireworks (OpenAI-compatible)
        # - deepinfra (OpenAI-compatible)
        # - cloudflare (REST API)
        # - ollama (OpenAI-compatible, local)
        # - vllm (OpenAI-compatible, local)


# Alias for convenience
def get_provider(name: str, config: ProviderConfig | None = None) -> LLMProvider:
    """
    Convenience function to get a provider.

    Equivalent to ProviderRegistry.get(name, config).
    """
    return ProviderRegistry.get(name, config)


def get_default_provider(config: ProviderConfig | None = None) -> LLMProvider:
    """
    Convenience function to get the default provider.

    Equivalent to ProviderRegistry.get_default(config).
    """
    return ProviderRegistry.get_default(config)
