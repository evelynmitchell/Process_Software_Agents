"""
LLM Client Wrapper with Retry Logic for ASP Platform

This module provides a wrapper around the Anthropic SDK with:
- Exponential backoff retry logic
- Rate limiting handling
- Structured output parsing
- Token counting
- Error handling and logging

Author: ASP Development Team
Date: November 13, 2025
"""

import json
import logging
import os
from typing import Any, Dict, Optional

from anthropic import Anthropic, APIConnectionError, RateLimitError, APIStatusError
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    retry_if_exception,
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
    if isinstance(exception, (APIConnectionError, RateLimitError)):
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

    def __init__(self, api_key: Optional[str] = None):
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

        self.client = Anthropic(api_key=self.api_key)
        logger.info("LLMClient initialized with Anthropic SDK")

    @retry(
        retry=retry_if_exception(should_retry_api_error),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True,
    )
    def call_with_retry(
        self,
        prompt: str,
        model: Optional[str] = None,
        max_tokens: int = 4096,
        temperature: float = 0.0,
        system: Optional[str] = None,
        **kwargs,
    ) -> Dict[str, Any]:
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
                f"Calling Anthropic API: model={model}, "
                f"max_tokens={max_tokens}, temp={temperature}"
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
                f"LLM call successful: "
                f"input_tokens={response.usage.input_tokens}, "
                f"output_tokens={response.usage.output_tokens}, "
                f"cost=${total_cost:.4f}"
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

        except APIStatusError as e:
            if 400 <= e.status_code < 500:
                # Client error - don't retry
                logger.error(
                    f"Client error (HTTP {e.status_code}): {e.message}\n"
                    f"This is likely a bug in our code or prompt."
                )
                raise
            else:
                # Server error - retry
                logger.warning(
                    f"Server error (HTTP {e.status_code}): {e.message}\n"
                    f"Will retry with exponential backoff..."
                )
                raise

        except (APIConnectionError, RateLimitError) as e:
            logger.warning(f"Transient error: {e}. Will retry...")
            raise

        except Exception as e:
            logger.error(f"Unexpected error during LLM call: {e}")
            raise

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
