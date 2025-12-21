"""
OpenRouter Provider implementation.

OpenRouter provides access to 100+ models from various providers
(Anthropic, OpenAI, Google, Meta, Mistral, etc.) through a unified
OpenAI-compatible API.

Author: ASP Development Team
Date: December 2025
"""

from asp.providers.base import ProviderConfig
from asp.providers.openai_compat import OpenAICompatibleProvider


class OpenRouterProvider(OpenAICompatibleProvider):
    """
    OpenRouter LLM provider.

    Provides access to 100+ models through OpenRouter's API with:
    - OpenAI-compatible interface
    - Automatic retry with exponential backoff
    - Cost estimation for popular models
    - Both sync and async support

    Example:
        provider = OpenRouterProvider()
        response = await provider.call_async(
            prompt="Explain quantum computing",
            model="anthropic/claude-3.5-sonnet",
            max_tokens=1000
        )
        print(response.content)

    Models use the format: provider/model-name
    - anthropic/claude-3.5-sonnet
    - openai/gpt-4o
    - google/gemini-pro
    - meta-llama/llama-3.1-70b-instruct
    """

    name = "openrouter"
    BASE_URL = "https://openrouter.ai/api/v1"
    API_KEY_ENV_VAR = "OPENROUTER_API_KEY"

    # Popular models (as of Dec 2025)
    MODELS = [
        # Anthropic
        "anthropic/claude-3.5-sonnet",
        "anthropic/claude-3.5-haiku",
        "anthropic/claude-3-opus",
        # OpenAI
        "openai/gpt-4o",
        "openai/gpt-4o-mini",
        "openai/o1-preview",
        "openai/o1-mini",
        # Google
        "google/gemini-2.0-flash-exp",
        "google/gemini-pro",
        "google/gemini-pro-1.5",
        # Meta Llama
        "meta-llama/llama-3.3-70b-instruct",
        "meta-llama/llama-3.1-405b-instruct",
        "meta-llama/llama-3.1-70b-instruct",
        "meta-llama/llama-3.1-8b-instruct",
        # Mistral
        "mistralai/mistral-large",
        "mistralai/mixtral-8x22b-instruct",
        # DeepSeek
        "deepseek/deepseek-r1",
        "deepseek/deepseek-chat",
        # Qwen
        "qwen/qwen-2.5-72b-instruct",
    ]

    # Default to Claude 3.5 Sonnet (good balance of capability and cost)
    DEFAULT_MODEL = "anthropic/claude-3.5-sonnet"

    # Pricing per million tokens (approximate, as of Dec 2025)
    # OpenRouter may have slight markup over direct provider pricing
    PRICING = {
        # Anthropic (via OpenRouter)
        "anthropic/claude-3.5-sonnet": {"input": 3.0, "output": 15.0},
        "anthropic/claude-3.5-haiku": {"input": 0.25, "output": 1.25},
        "anthropic/claude-3-opus": {"input": 15.0, "output": 75.0},
        # OpenAI (via OpenRouter)
        "openai/gpt-4o": {"input": 2.5, "output": 10.0},
        "openai/gpt-4o-mini": {"input": 0.15, "output": 0.6},
        "openai/o1-preview": {"input": 15.0, "output": 60.0},
        "openai/o1-mini": {"input": 3.0, "output": 12.0},
        # Google (via OpenRouter)
        "google/gemini-2.0-flash-exp": {
            "input": 0.0,
            "output": 0.0,
        },  # Free during preview
        "google/gemini-pro": {"input": 0.5, "output": 1.5},
        "google/gemini-pro-1.5": {"input": 1.25, "output": 5.0},
        # Meta Llama (via OpenRouter)
        "meta-llama/llama-3.3-70b-instruct": {"input": 0.35, "output": 0.4},
        "meta-llama/llama-3.1-405b-instruct": {"input": 2.0, "output": 2.0},
        "meta-llama/llama-3.1-70b-instruct": {"input": 0.35, "output": 0.4},
        "meta-llama/llama-3.1-8b-instruct": {"input": 0.055, "output": 0.055},
        # Mistral (via OpenRouter)
        "mistralai/mistral-large": {"input": 2.0, "output": 6.0},
        "mistralai/mixtral-8x22b-instruct": {"input": 0.65, "output": 0.65},
        # DeepSeek (via OpenRouter)
        "deepseek/deepseek-r1": {"input": 0.55, "output": 2.19},
        "deepseek/deepseek-chat": {"input": 0.14, "output": 0.28},
        # Qwen (via OpenRouter)
        "qwen/qwen-2.5-72b-instruct": {"input": 0.35, "output": 0.4},
    }

    def __init__(self, config: ProviderConfig | None = None):
        """
        Initialize OpenRouter provider.

        Args:
            config: Provider configuration. API key is read from config.api_key
                   or OPENROUTER_API_KEY environment variable.

        Raises:
            AuthenticationError: If no API key is available
        """
        super().__init__(config)

    def _get_headers(self) -> dict[str, str]:
        """Get headers for OpenRouter API requests."""
        headers = super()._get_headers()

        # OpenRouter recommends these headers for tracking
        site_url = self.config.extra.get(
            "site_url", "https://github.com/evelynmitchell/Process_Software_Agents"
        )
        site_name = self.config.extra.get("site_name", "ASP Platform")

        headers.update(
            {
                "HTTP-Referer": site_url,
                "X-Title": site_name,
            }
        )

        return headers
