"""
Anthropic Provider implementation.

This module provides the Anthropic (Claude) provider for the ASP platform,
wrapping the Anthropic SDK with retry logic, cost tracking, and the
standard LLMProvider interface.

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
    retry_if_exception,
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


def _should_retry_anthropic_error(exception: Exception) -> bool:
    """
    Determine if an Anthropic API error should be retried.

    Retries on:
    - APIConnectionError (network issues)
    - RateLimitError (rate limits)
    - APIStatusError with 5xx status codes (server errors)

    Does NOT retry on:
    - APIStatusError with 4xx status codes (client errors)
    """
    # Import here to avoid requiring anthropic SDK at module level
    from anthropic import APIConnectionError, APIStatusError
    from anthropic import RateLimitError as AnthropicRateLimitError

    if isinstance(exception, APIConnectionError | AnthropicRateLimitError):
        return True
    if isinstance(exception, APIStatusError):
        return exception.status_code >= 500
    return False


class AnthropicProvider(LLMProvider):
    """
    Anthropic (Claude) LLM provider.

    Provides access to Claude models via the Anthropic API with:
    - Automatic retry with exponential backoff
    - Rate limit handling
    - Cost estimation
    - Both sync and async support

    Example:
        provider = AnthropicProvider()
        response = await provider.call_async(
            prompt="Explain quantum computing",
            model="claude-sonnet-4-5",
            max_tokens=1000
        )
        print(response.content)
    """

    name = "anthropic"

    # Available Claude models
    MODELS = [
        "claude-opus-4-5",
        "claude-sonnet-4-5",
        "claude-haiku-4-5",
        "claude-sonnet-4-20250514",
    ]

    # Default model (cost-effective for testing)
    DEFAULT_MODEL = "claude-haiku-4-5"

    # Pricing per million tokens (as of Dec 2025)
    PRICING = {
        "claude-opus-4-5": {"input": 15.0, "output": 75.0},
        "claude-sonnet-4-5": {"input": 3.0, "output": 15.0},
        "claude-sonnet-4-20250514": {"input": 3.0, "output": 15.0},
        "claude-haiku-4-5": {"input": 0.25, "output": 1.25},
    }

    def __init__(self, config: ProviderConfig | None = None):
        """
        Initialize Anthropic provider.

        Args:
            config: Provider configuration. API key is read from config.api_key
                   or ANTHROPIC_API_KEY environment variable.

        Raises:
            AuthenticationError: If no API key is available
        """
        self.config = config or ProviderConfig()

        # Get API key from config or environment
        api_key = self.config.api_key or os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise AuthenticationError(
                "Anthropic API key not found. "
                "Set ANTHROPIC_API_KEY environment variable or pass api_key in config.",
                provider=self.name,
            )

        self._api_key = api_key
        self._default_model = self.config.default_model or self.DEFAULT_MODEL

        # Lazy-load clients
        self._client = None
        self._async_client = None

        logger.info("AnthropicProvider initialized")

    @property
    def _sync_client(self):
        """Lazy-load synchronous Anthropic client."""
        if self._client is None:
            from anthropic import Anthropic

            self._client = Anthropic(api_key=self._api_key)
        return self._client

    @property
    def _async_client_instance(self):
        """Lazy-load asynchronous Anthropic client."""
        if self._async_client is None:
            from anthropic import AsyncAnthropic

            self._async_client = AsyncAnthropic(api_key=self._api_key)
        return self._async_client

    @property
    def available_models(self) -> list[str]:
        """List available Claude models."""
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
            Estimated cost in USD
        """
        # Get pricing for model, fall back to Haiku pricing if unknown
        pricing = self.PRICING.get(model, self.PRICING["claude-haiku-4-5"])

        input_cost = (input_tokens / 1_000_000) * pricing["input"]
        output_cost = (output_tokens / 1_000_000) * pricing["output"]

        return input_cost + output_cost

    @retry(
        retry=retry_if_exception(_should_retry_anthropic_error),
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
        Make a synchronous LLM call to Anthropic.

        Args:
            prompt: User prompt text
            model: Model identifier (defaults to claude-haiku-4-5)
            max_tokens: Maximum tokens in response
            temperature: Sampling temperature (0.0 = deterministic)
            system: Optional system prompt
            **kwargs: Additional arguments for Anthropic API

        Returns:
            LLMResponse with normalized response data

        Raises:
            RateLimitError: Rate limit exceeded
            AuthenticationError: Invalid credentials
            ConnectionError: Network failure
            ProviderError: Other API errors
        """
        from anthropic import APIConnectionError, APIStatusError
        from anthropic import RateLimitError as AnthropicRateLimitError

        model = model or self._default_model

        try:
            logger.debug(
                "Calling Anthropic API: model=%s, max_tokens=%d, temp=%s",
                model,
                max_tokens,
                temperature,
            )

            # Build API parameters
            api_params = {
                "model": model,
                "max_tokens": max_tokens,
                "temperature": temperature,
                "messages": [{"role": "user", "content": prompt}],
                **kwargs,
            }
            if system:
                api_params["system"] = system

            # Make API call
            response = self._sync_client.messages.create(**api_params)

            return self._process_response(response, model)

        except AnthropicRateLimitError as e:
            logger.warning("Rate limit hit: %s", e)
            raise RateLimitError(
                str(e),
                provider=self.name,
                retry_after=getattr(e, "retry_after", None),
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
        Make an asynchronous LLM call to Anthropic.

        This is the preferred method for concurrent operations.
        See call() for parameter documentation.

        Returns:
            LLMResponse with normalized response data
        """
        from anthropic import APIConnectionError, APIStatusError
        from anthropic import RateLimitError as AnthropicRateLimitError

        model = model or self._default_model

        async for attempt in AsyncRetrying(
            retry=retry_if_exception(_should_retry_anthropic_error),
            stop=stop_after_attempt(3),
            wait=wait_exponential(multiplier=1, min=2, max=10),
            reraise=True,
        ):
            with attempt:
                try:
                    logger.debug(
                        "Async calling Anthropic API: model=%s, max_tokens=%d, temp=%s",
                        model,
                        max_tokens,
                        temperature,
                    )

                    # Build API parameters
                    api_params = {
                        "model": model,
                        "max_tokens": max_tokens,
                        "temperature": temperature,
                        "messages": [{"role": "user", "content": prompt}],
                        **kwargs,
                    }
                    if system:
                        api_params["system"] = system

                    # Make async API call
                    response = await self._async_client_instance.messages.create(
                        **api_params
                    )

                    return self._process_response(response, model)

                except AnthropicRateLimitError as e:
                    logger.warning("Rate limit hit: %s", e)
                    raise RateLimitError(
                        str(e),
                        provider=self.name,
                        retry_after=getattr(e, "retry_after", None),
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
        Process Anthropic API response into LLMResponse.

        Args:
            response: Raw Anthropic API response
            model: Model used for the request

        Returns:
            Normalized LLMResponse
        """
        # Extract content
        content_text = response.content[0].text

        # Try to parse as JSON
        parsed_content = self._try_parse_json(content_text)

        # Calculate cost
        cost = self.estimate_cost(
            model,
            response.usage.input_tokens,
            response.usage.output_tokens,
        )

        logger.info(
            "LLM call successful: input_tokens=%d, output_tokens=%d, cost=$%.4f",
            response.usage.input_tokens,
            response.usage.output_tokens,
            cost,
        )

        return LLMResponse(
            content=parsed_content,
            raw_content=content_text,
            usage={
                "input_tokens": response.usage.input_tokens,
                "output_tokens": response.usage.output_tokens,
            },
            cost=cost,
            model=response.model,
            provider=self.name,
            stop_reason=response.stop_reason,
        )

    def _try_parse_json(self, text: str) -> Any:
        """
        Attempt to parse text as JSON.

        If parsing fails, returns the original text.

        Args:
            text: Text to parse

        Returns:
            Parsed JSON (dict/list) or original text
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
