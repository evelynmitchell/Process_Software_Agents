"""
Groq Provider implementation.

Groq provides ultra-fast LLM inference using their custom LPU (Language
Processing Unit) technology, achieving 18x faster speeds than GPU-based
inference.

Author: ASP Development Team
Date: December 2025
"""

from asp.providers.base import ProviderConfig
from asp.providers.openai_compat import OpenAICompatibleProvider


class GroqProvider(OpenAICompatibleProvider):
    """
    Groq LLM provider with LPU-accelerated inference.

    Provides access to Llama, Mixtral, Gemma, and other models with:
    - Ultra-fast inference (284 tokens/sec for Llama 3 70B)
    - OpenAI-compatible interface
    - Automatic retry with exponential backoff
    - Both sync and async support

    Example:
        provider = GroqProvider()
        response = await provider.call_async(
            prompt="Explain quantum computing",
            model="llama-3.3-70b-versatile",
            max_tokens=1000
        )
        print(response.content)

    Speed benchmarks (tokens/sec):
    - Llama 3 70B: ~284 tokens/sec
    - Llama 3 8B: ~876 tokens/sec
    - Mixtral 8x7B: ~400 tokens/sec
    """

    name = "groq"
    BASE_URL = "https://api.groq.com/openai/v1"
    API_KEY_ENV_VAR = "GROQ_API_KEY"

    # Current models (as of Dec 2025)
    MODELS = [
        # Meta Llama
        "llama-3.3-70b-versatile",  # Latest Llama 3.3
        "llama-3.3-70b-specdec",  # Speculative decoding
        "llama-3.1-70b-versatile",  # Llama 3.1 70B
        "llama-3.1-8b-instant",  # Fast inference
        "llama3-70b-8192",  # 8K context
        "llama3-8b-8192",  # 8K context, fast
        # Google Gemma
        "gemma2-9b-it",  # Google Gemma 2
        # Mistral
        "mixtral-8x7b-32768",  # 32K context
        # Safety/Moderation
        "llama-guard-3-8b",  # Content moderation
    ]

    # Default to versatile Llama 3.3 70B
    DEFAULT_MODEL = "llama-3.3-70b-versatile"

    # Groq pricing is very competitive (per million tokens)
    PRICING = {
        # Llama models
        "llama-3.3-70b-versatile": {"input": 0.59, "output": 0.79},
        "llama-3.3-70b-specdec": {"input": 0.59, "output": 0.99},
        "llama-3.1-70b-versatile": {"input": 0.59, "output": 0.79},
        "llama-3.1-8b-instant": {"input": 0.05, "output": 0.08},
        "llama3-70b-8192": {"input": 0.59, "output": 0.79},
        "llama3-8b-8192": {"input": 0.05, "output": 0.08},
        # Gemma
        "gemma2-9b-it": {"input": 0.20, "output": 0.20},
        # Mixtral
        "mixtral-8x7b-32768": {"input": 0.24, "output": 0.24},
        # Guard (free for moderation)
        "llama-guard-3-8b": {"input": 0.20, "output": 0.20},
    }

    def __init__(self, config: ProviderConfig | None = None):
        """
        Initialize Groq provider.

        Args:
            config: Provider configuration. API key is read from config.api_key
                   or GROQ_API_KEY environment variable.

        Raises:
            AuthenticationError: If no API key is available
        """
        super().__init__(config)
