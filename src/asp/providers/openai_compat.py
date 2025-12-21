"""
OpenAI-Compatible Provider Base Class.

This module provides a base class for LLM providers that use OpenAI-compatible
APIs. Many providers (OpenRouter, Groq, Together, Fireworks, DeepInfra, Ollama,
vLLM) expose OpenAI-compatible endpoints, allowing code reuse.

Author: ASP Development Team
Date: December 2025
"""

import json
import logging
import os
from typing import Any

from tenacity import (
    AsyncRetrying,
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from asp.providers.base import LLMProvider, LLMResponse, ProviderConfig
from asp.providers.errors import (
    AuthenticationError,
    ConnectionError,
    ProviderError,
    RateLimitError,
)

logger = logging.getLogger(__name__)


class OpenAICompatibleProvider(LLMProvider):
    """
    Base class for OpenAI-compatible LLM providers.

    Subclasses need only define:
    - name: Provider identifier
    - BASE_URL: API endpoint
    - API_KEY_ENV_VAR: Environment variable for API key
    - MODELS: List of available models
    - PRICING: Cost per million tokens (optional)
    - DEFAULT_MODEL: Default model to use

    Example subclass:
        class GroqProvider(OpenAICompatibleProvider):
            name = "groq"
            BASE_URL = "https://api.groq.com/openai/v1"
            API_KEY_ENV_VAR = "GROQ_API_KEY"
            MODELS = ["llama-3.3-70b-versatile", ...]
            DEFAULT_MODEL = "llama-3.3-70b-versatile"
    """

    # Subclasses must define these
    name: str
    BASE_URL: str
    API_KEY_ENV_VAR: str
    MODELS: list[str]
    DEFAULT_MODEL: str

    # Optional: pricing per million tokens {"model": {"input": X, "output": Y}}
    PRICING: dict[str, dict[str, float]] = {}

    # Optional: additional headers for requests
    EXTRA_HEADERS: dict[str, str] = {}

    # Whether API key is required (False for local providers like Ollama)
    REQUIRES_API_KEY: bool = True

    def __init__(self, config: ProviderConfig | None = None):
        """
        Initialize OpenAI-compatible provider.

        Args:
            config: Provider configuration. API key is read from config.api_key
                   or the provider's environment variable.

        Raises:
            AuthenticationError: If API key is required but not available
        """
        super().__init__(config)
        self.config = config or ProviderConfig()

        # Get API key from config or environment
        api_key = self.config.api_key or os.getenv(self.API_KEY_ENV_VAR)
        if self.REQUIRES_API_KEY and not api_key:
            raise AuthenticationError(
                f"{self.name.title()} API key not found. "
                f"Set {self.API_KEY_ENV_VAR} environment variable or pass api_key in config.",
                provider=self.name,
            )

        self._api_key = api_key or "not-required"
        self._base_url = self.config.base_url or self.BASE_URL
        self._default_model = self.config.default_model or self.DEFAULT_MODEL

        # Lazy-load clients
        self._sync_client_impl = None
        self._async_client_impl = None

        logger.info(
            "%sProvider initialized (base_url=%s)", self.name.title(), self._base_url
        )

    @property
    def _sync_client(self):
        """Lazy-load synchronous OpenAI client."""
        if self._sync_client_impl is None:
            from openai import OpenAI

            self._sync_client_impl = OpenAI(
                api_key=self._api_key,
                base_url=self._base_url,
                default_headers=self._get_headers(),
            )
        return self._sync_client_impl

    @property
    def _async_client(self):
        """Lazy-load asynchronous OpenAI client."""
        if self._async_client_impl is None:
            from openai import AsyncOpenAI

            self._async_client_impl = AsyncOpenAI(
                api_key=self._api_key,
                base_url=self._base_url,
                default_headers=self._get_headers(),
            )
        return self._async_client_impl

    def _get_headers(self) -> dict[str, str]:
        """Get headers for API requests. Override for custom headers."""
        return self.EXTRA_HEADERS.copy()

    @property
    def available_models(self) -> list[str]:
        """List available models."""
        return self.MODELS.copy()

    @property
    def default_model(self) -> str:
        """Get default model."""
        return self._default_model

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
            Estimated cost in USD (0.0 if pricing not defined)
        """
        if not self.PRICING:
            return 0.0

        # Try exact match, then prefix match
        pricing = self.PRICING.get(model)
        if not pricing:
            # Try to find a matching prefix
            for model_key, model_pricing in self.PRICING.items():
                if model.startswith(model_key) or model_key in model:
                    pricing = model_pricing
                    break

        if not pricing:
            return 0.0

        input_cost = (input_tokens / 1_000_000) * pricing.get("input", 0)
        output_cost = (output_tokens / 1_000_000) * pricing.get("output", 0)

        return input_cost + output_cost

    @retry(
        retry=retry_if_exception_type((ConnectionError,)),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True,
    )
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
            **kwargs: Additional arguments for OpenAI API

        Returns:
            LLMResponse with normalized response data
        """
        from openai import APIConnectionError, APIStatusError
        from openai import RateLimitError as OpenAIRateLimitError

        model = model or self._default_model

        try:
            logger.debug(
                "Calling %s API: model=%s, max_tokens=%d, temp=%s",
                self.name,
                model,
                max_tokens,
                temperature,
            )

            # Build messages
            messages = []
            if system:
                messages.append({"role": "system", "content": system})
            messages.append({"role": "user", "content": prompt})

            # Make API call
            response = self._sync_client.chat.completions.create(
                model=model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
                **kwargs,
            )

            return self._process_response(response, model)

        except OpenAIRateLimitError as e:
            logger.warning("Rate limit hit: %s", e)
            raise RateLimitError(
                str(e),
                provider=self.name,
            ) from e

        except APIConnectionError as e:
            logger.warning("Connection error: %s", e)
            raise ConnectionError(str(e), provider=self.name) from e

        except APIStatusError as e:
            logger.error("API error (HTTP %d): %s", e.status_code, e.message)
            if e.status_code == 401:
                raise AuthenticationError(e.message, provider=self.name) from e
            raise ProviderError(
                f"HTTP {e.status_code}: {e.message}",
                provider=self.name,
                details={"status_code": e.status_code},
            ) from e

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
        """
        from openai import APIConnectionError, APIStatusError
        from openai import RateLimitError as OpenAIRateLimitError

        model = model or self._default_model

        async for attempt in AsyncRetrying(
            retry=retry_if_exception_type((ConnectionError,)),
            stop=stop_after_attempt(3),
            wait=wait_exponential(multiplier=1, min=2, max=10),
            reraise=True,
        ):
            with attempt:
                try:
                    logger.debug(
                        "Async calling %s API: model=%s, max_tokens=%d, temp=%s",
                        self.name,
                        model,
                        max_tokens,
                        temperature,
                    )

                    # Build messages
                    messages = []
                    if system:
                        messages.append({"role": "system", "content": system})
                    messages.append({"role": "user", "content": prompt})

                    # Make async API call
                    response = await self._async_client.chat.completions.create(
                        model=model,
                        messages=messages,
                        max_tokens=max_tokens,
                        temperature=temperature,
                        **kwargs,
                    )

                    return self._process_response(response, model)

                except OpenAIRateLimitError as e:
                    logger.warning("Rate limit hit: %s", e)
                    raise RateLimitError(
                        str(e),
                        provider=self.name,
                    ) from e

                except APIConnectionError as e:
                    logger.warning("Connection error: %s", e)
                    raise ConnectionError(str(e), provider=self.name) from e

                except APIStatusError as e:
                    logger.error("API error (HTTP %d): %s", e.status_code, e.message)
                    if e.status_code == 401:
                        raise AuthenticationError(e.message, provider=self.name) from e
                    raise ProviderError(
                        f"HTTP {e.status_code}: {e.message}",
                        provider=self.name,
                        details={"status_code": e.status_code},
                    ) from e

        # Should never reach here due to reraise=True
        raise RuntimeError("Async retry loop completed without return or exception")

    def _process_response(self, response: Any, model: str) -> LLMResponse:
        """
        Process OpenAI API response into LLMResponse.

        Args:
            response: Raw OpenAI API response
            model: Model used for the request

        Returns:
            Normalized LLMResponse
        """
        # Extract content from first choice
        choice = response.choices[0]
        content_text = choice.message.content or ""

        # Try to parse as JSON
        parsed_content = self._try_parse_json(content_text)

        # Get token usage
        usage = {}
        if response.usage:
            usage = {
                "input_tokens": response.usage.prompt_tokens,
                "output_tokens": response.usage.completion_tokens,
            }

        # Calculate cost
        cost = self.estimate_cost(
            model,
            usage.get("input_tokens", 0),
            usage.get("output_tokens", 0),
        )

        if usage:
            logger.info(
                "LLM call successful: input_tokens=%d, output_tokens=%d, cost=$%.4f",
                usage.get("input_tokens", 0),
                usage.get("output_tokens", 0),
                cost,
            )

        return LLMResponse(
            content=parsed_content,
            raw_content=content_text,
            usage=usage,
            cost=cost if cost > 0 else None,
            model=response.model or model,
            provider=self.name,
            stop_reason=choice.finish_reason,
        )

    def _try_parse_json(self, text: str) -> Any:
        """
        Attempt to parse text as JSON.

        If parsing fails, returns the original text.
        """
        # Try to extract JSON from markdown code blocks
        if "```json" in text:
            try:
                start = text.index("```json") + 7
                end = text.index("```", start)
                json_text = text[start:end].strip()
                return json.loads(json_text)
            except (ValueError, json.JSONDecodeError):
                pass

        # Try to parse entire text as JSON
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            return text
