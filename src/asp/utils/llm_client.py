"""
LLM Client Wrapper with Retry Logic for ASP Platform

This module provides a wrapper around the Anthropic SDK with:
- Exponential backoff retry logic
- Rate limiting handling
- Structured output parsing
- Token counting
- Error handling and logging
- Automatic telemetry instrumentation (Logfire/Langfuse)

Author: ASP Development Team
Date: November 13, 2025 (updated December 2025)
"""

import json
import logging
import os
from typing import Any

# Initialize LLM instrumentation BEFORE importing Anthropic
# This allows Logfire to patch the Anthropic SDK for auto-tracing
import asp.telemetry.config

asp.telemetry.config.ensure_llm_instrumentation()

from anthropic import (
    Anthropic,
    APIConnectionError,
    APIStatusError,
    AsyncAnthropic,
    RateLimitError,
)
from tenacity import (
    AsyncRetrying,
    retry,
    retry_if_exception,
    stop_after_attempt,
    wait_exponential,
)

logger = logging.getLogger(__name__)


def should_retry_api_error(exception):
    """
    Custom retry condition for API errors.

    Retries on:
    - APIConnectionError (network issues)
    - RateLimitError (rate limits)
    - APIStatusError with 5xx status codes (server errors)

    Does NOT retry on:
    - APIStatusError with 4xx status codes (client errors)
    """
    if isinstance(exception, APIConnectionError | RateLimitError):
        return True
    if isinstance(exception, APIStatusError):
        # Only retry server errors (5xx), not client errors (4xx)
        return exception.status_code >= 500
    return False


class LLMClient:
    """
    Wrapper around Anthropic SDK with retry logic and error handling.

    Features:
    - Exponential backoff for transient failures
    - Rate limit handling
    - JSON parsing and validation
    - Token counting and logging
    - Configurable model and parameters

    Example:
        client = LLMClient()
        response = client.call_with_retry(
            prompt="Decompose this task...",
            model="claude-sonnet-4-20250514",
            max_tokens=4096
        )
    """

    # Default model (pinned version for reproducibility)
    # Using Haiku 4.5 for cost-effective testing
    DEFAULT_MODEL = "claude-haiku-4-5"

    # Cost per million tokens (as of Nov 2025)
    # Haiku 4.5 costs: ~$0.25 input, ~$1.25 output per million tokens
    COST_PER_MILLION_INPUT_TOKENS = 0.25  # USD
    COST_PER_MILLION_OUTPUT_TOKENS = 1.25  # USD

    def __init__(self, api_key: str | None = None):
        """
        Initialize LLM client.

        Args:
            api_key: Optional Anthropic API key (defaults to ANTHROPIC_API_KEY env var)
        """
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError(
                "Anthropic API key not found. "
                "Set ANTHROPIC_API_KEY environment variable or pass api_key parameter."
            )

        # Sync client for backward compatibility
        self.client = Anthropic(api_key=self.api_key)

        # Async client for concurrent operations
        self._async_client: AsyncAnthropic | None = None

        logger.info("LLMClient initialized with Anthropic SDK")

    @property
    def async_client(self) -> AsyncAnthropic:
        """
        Lazy-load async client.

        Returns:
            AsyncAnthropic client instance
        """
        if self._async_client is None:
            self._async_client = AsyncAnthropic(api_key=self.api_key)
        return self._async_client

    @retry(
        retry=retry_if_exception(should_retry_api_error),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True,
    )
    def call_with_retry(
        self,
        prompt: str,
        model: str | None = None,
        max_tokens: int = 4096,
        temperature: float = 0.0,
        system: str | None = None,
        **kwargs,
    ) -> dict[str, Any]:
        """
        Call Anthropic API with retry logic.

        Retries on:
        - APIConnectionError (network issues)
        - RateLimitError (too many requests)
        - APIStatusError 5xx (server errors)

        Does NOT retry on:
        - APIStatusError 4xx (client errors - bad request)

        Args:
            prompt: User prompt text
            model: Model name (defaults to DEFAULT_MODEL)
            max_tokens: Maximum tokens in response
            temperature: Sampling temperature (0.0 = deterministic, 1.0 = creative)
            system: Optional system prompt
            **kwargs: Additional arguments for Anthropic API

        Returns:
            Dict with parsed response:
                {
                    "content": str or dict (parsed JSON if applicable),
                    "usage": {"input_tokens": int, "output_tokens": int},
                    "model": str,
                    "stop_reason": str
                }

        Raises:
            APIConnectionError: Network failure (after 3 retries)
            RateLimitError: Rate limit exceeded (after 3 retries)
            APIStatusError: API error (4xx or 5xx after retries)
            ValueError: Invalid parameters
        """
        model = model or self.DEFAULT_MODEL

        try:
            logger.debug(
                "Calling Anthropic API: model=%s, max_tokens=%d, temp=%s",
                model,
                max_tokens,
                temperature,
            )

            # Build messages
            messages = [{"role": "user", "content": prompt}]

            # Build API call parameters
            api_params = {
                "model": model,
                "max_tokens": max_tokens,
                "temperature": temperature,
                "messages": messages,
                **kwargs,
            }

            # Only include system parameter if it's provided
            if system:
                api_params["system"] = system

            # Make API call
            response = self.client.messages.create(**api_params)

            # Extract content
            content_text = response.content[0].text

            # Try to parse as JSON if it looks like JSON
            parsed_content = self._try_parse_json(content_text)

            # Calculate cost
            input_cost = (
                response.usage.input_tokens / 1_000_000
            ) * self.COST_PER_MILLION_INPUT_TOKENS
            output_cost = (
                response.usage.output_tokens / 1_000_000
            ) * self.COST_PER_MILLION_OUTPUT_TOKENS
            total_cost = input_cost + output_cost

            logger.info(
                "LLM call successful: input_tokens=%d, output_tokens=%d, cost=$%.4f",
                response.usage.input_tokens,
                response.usage.output_tokens,
                total_cost,
            )

            return {
                "content": parsed_content,
                "raw_content": content_text,
                "usage": {
                    "input_tokens": response.usage.input_tokens,
                    "output_tokens": response.usage.output_tokens,
                },
                "cost": total_cost,
                "model": response.model,
                "stop_reason": response.stop_reason,
            }

        except RateLimitError as e:
            logger.warning("Rate limit hit: %s. Will retry...", e)
            raise

        except APIConnectionError as e:
            logger.warning("Connection error: %s. Will retry...", e)
            raise

        except APIStatusError as e:
            if 400 <= e.status_code < 500:
                # Client error - don't retry
                logger.error(
                    "Client error (HTTP %d): %s. This is likely a bug in our code or prompt.",
                    e.status_code,
                    e.message,
                )
                raise
            # Server error - retry
            logger.warning(
                "Server error (HTTP %d): %s. Will retry with exponential backoff...",
                e.status_code,
                e.message,
            )
            raise

        except Exception as e:
            logger.error("Unexpected error during LLM call: %s", e)
            raise

    async def call_with_retry_async(
        self,
        prompt: str,
        model: str | None = None,
        max_tokens: int = 4096,
        temperature: float = 0.0,
        system: str | None = None,
        **kwargs,
    ) -> dict[str, Any]:
        """
        Asynchronous version of call_with_retry.

        Call Anthropic API asynchronously with retry logic. Enables concurrent
        LLM calls for parallel agent execution.

        Retries on:
        - APIConnectionError (network issues)
        - RateLimitError (too many requests)
        - APIStatusError 5xx (server errors)

        Does NOT retry on:
        - APIStatusError 4xx (client errors - bad request)

        Args:
            prompt: User prompt text
            model: Model name (defaults to DEFAULT_MODEL)
            max_tokens: Maximum tokens in response
            temperature: Sampling temperature (0.0 = deterministic, 1.0 = creative)
            system: Optional system prompt
            **kwargs: Additional arguments for Anthropic API

        Returns:
            Dict with parsed response:
                {
                    "content": str or dict (parsed JSON if applicable),
                    "usage": {"input_tokens": int, "output_tokens": int},
                    "model": str,
                    "stop_reason": str
                }

        Raises:
            APIConnectionError: Network failure (after 3 retries)
            RateLimitError: Rate limit exceeded (after 3 retries)
            APIStatusError: API error (4xx or 5xx after retries)
            ValueError: Invalid parameters
        """
        model = model or self.DEFAULT_MODEL

        async for attempt in AsyncRetrying(
            retry=retry_if_exception(should_retry_api_error),
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

                    # Build messages
                    messages = [{"role": "user", "content": prompt}]

                    # Build API call parameters
                    api_params = {
                        "model": model,
                        "max_tokens": max_tokens,
                        "temperature": temperature,
                        "messages": messages,
                        **kwargs,
                    }

                    # Only include system parameter if it's provided
                    if system:
                        api_params["system"] = system

                    # Make async API call
                    response = await self.async_client.messages.create(**api_params)

                    # Extract content
                    content_text = response.content[0].text

                    # Try to parse as JSON if it looks like JSON
                    parsed_content = self._try_parse_json(content_text)

                    # Calculate cost
                    input_cost = (
                        response.usage.input_tokens / 1_000_000
                    ) * self.COST_PER_MILLION_INPUT_TOKENS
                    output_cost = (
                        response.usage.output_tokens / 1_000_000
                    ) * self.COST_PER_MILLION_OUTPUT_TOKENS
                    total_cost = input_cost + output_cost

                    logger.info(
                        "Async LLM call successful: input_tokens=%d, output_tokens=%d, cost=$%.4f",
                        response.usage.input_tokens,
                        response.usage.output_tokens,
                        total_cost,
                    )

                    return {
                        "content": parsed_content,
                        "raw_content": content_text,
                        "usage": {
                            "input_tokens": response.usage.input_tokens,
                            "output_tokens": response.usage.output_tokens,
                        },
                        "cost": total_cost,
                        "model": response.model,
                        "stop_reason": response.stop_reason,
                    }

                except RateLimitError as e:
                    logger.warning("Rate limit hit: %s. Will retry...", e)
                    raise

                except APIConnectionError as e:
                    logger.warning("Connection error: %s. Will retry...", e)
                    raise

                except APIStatusError as e:
                    if 400 <= e.status_code < 500:
                        # Client error - don't retry
                        logger.error(
                            "Client error (HTTP %d): %s. This is likely a bug in our code or prompt.",
                            e.status_code,
                            e.message,
                        )
                        raise
                    # Server error - retry
                    logger.warning(
                        "Server error (HTTP %d): %s. Will retry with exponential backoff...",
                        e.status_code,
                        e.message,
                    )
                    raise

                except Exception as e:
                    logger.error("Unexpected error during async LLM call: %s", e)
                    raise

        # Should never reach here due to reraise=True, but for type safety
        raise RuntimeError("Async retry loop completed without return or exception")

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
                # Extract content between ```json and ```
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
            # Not JSON, return as-is
            return text

    def estimate_cost(
        self,
        input_tokens: int,
        output_tokens: int,
    ) -> float:
        """
        Estimate cost for a given number of tokens.

        Args:
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens

        Returns:
            Estimated cost in USD
        """
        input_cost = (input_tokens / 1_000_000) * self.COST_PER_MILLION_INPUT_TOKENS
        output_cost = (output_tokens / 1_000_000) * self.COST_PER_MILLION_OUTPUT_TOKENS
        return input_cost + output_cost

    def count_tokens_approximate(self, text: str) -> int:
        """
        Approximate token count for text.

        Uses a simple heuristic: 1 token ~= 4 characters for English text.
        This is an approximation; actual tokenization may differ.

        For precise token counts, use the Anthropic tokenizer API.

        Args:
            text: Text to count tokens for

        Returns:
            Approximate token count
        """
        return len(text) // 4
