"""
Claude CLI Provider implementation.

This module provides an LLM provider that uses the Claude CLI (claude command)
via subprocess. This enables subscription billing (Pro/Max) without requiring
npm/Node.js in the Python environment.

Key features:
- Full token visibility via JSON output
- Cost tracking built into CLI output
- Session resumption support
- No additional dependencies (uses installed claude binary)

See ADR 011 for design rationale.

Author: ASP Development Team
Date: December 2025
"""

import asyncio
import builtins
import json
import logging
import shutil
from typing import Any

from asp.providers.base import LLMProvider, LLMResponse, ProviderConfig
from asp.providers.errors import (
    ConnectionError,
    ProviderError,
    TimeoutError,
)

logger = logging.getLogger(__name__)


class ClaudeCLIProvider(LLMProvider):
    """
    Claude CLI LLM provider using subprocess.

    Invokes the `claude` CLI binary with `--output-format json` to get
    structured responses including full token usage and cost tracking.

    Benefits:
    - Subscription billing support (Pro/Max plans)
    - No npm/Node.js dependency (binary is self-contained)
    - Full token visibility
    - Session resumption via session_id

    Limitations:
    - Subprocess overhead per call (~100ms)
    - No streaming (single result)
    - Requires claude CLI to be installed

    Example:
        provider = ClaudeCLIProvider()
        response = await provider.call_async(
            prompt="Explain quantum computing",
            max_tokens=1000
        )
        print(response.content)
        print(f"Cost: ${response.cost}")
    """

    name = "claude_cli"

    # Available models (same as Anthropic API)
    MODELS = [
        "claude-opus-4-5",
        "claude-sonnet-4-5",
        "claude-haiku-4-5",
    ]

    # Default model (CLI typically uses Sonnet by default)
    DEFAULT_MODEL = "claude-sonnet-4-5"

    def __init__(self, config: ProviderConfig | None = None):
        """
        Initialize Claude CLI provider.

        Args:
            config: Provider configuration.
                   - timeout: Subprocess timeout in seconds (default: 120)
                   - extra["max_turns"]: Max conversation turns (default: 1)
                   - extra["session_id"]: Resume a previous session
                   - extra["allowed_tools"]: Tools to allow (default: none)

        Raises:
            ConnectionError: If claude CLI is not installed
        """
        self.config = config or ProviderConfig()
        self._default_model = self.config.default_model or self.DEFAULT_MODEL
        self._timeout = self.config.timeout or 120.0

        # Check that claude CLI is available
        self._claude_path = shutil.which("claude")
        if not self._claude_path:
            raise ConnectionError(
                "Claude CLI not found. Install it from https://claude.ai/download",
                provider=self.name,
            )

        logger.info(
            "ClaudeCLIProvider initialized (claude binary: %s)", self._claude_path
        )

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

        Note: For subscription users, this returns 0 since costs are included
        in the plan. The actual cost from CLI output is more accurate.

        Args:
            model: Model identifier
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens

        Returns:
            Estimated cost in USD (0 for subscription users)
        """
        # Pricing per million tokens (as of Dec 2025)
        pricing = {
            "claude-opus-4-5": {"input": 15.0, "output": 75.0},
            "claude-sonnet-4-5": {"input": 3.0, "output": 15.0},
            "claude-haiku-4-5": {"input": 0.25, "output": 1.25},
        }

        # Get pricing for model, fall back to Sonnet pricing if unknown
        model_pricing = pricing.get(model, pricing["claude-sonnet-4-5"])

        input_cost = (input_tokens / 1_000_000) * model_pricing["input"]
        output_cost = (output_tokens / 1_000_000) * model_pricing["output"]

        return input_cost + output_cost

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
        Make a synchronous LLM call via Claude CLI.

        Args:
            prompt: User prompt text
            model: Model identifier (uses default if not specified)
            max_tokens: Maximum tokens in response (passed to CLI)
            temperature: Sampling temperature (not directly supported by CLI)
            system: Optional system prompt
            **kwargs: Additional arguments:
                - session_id: Resume a previous session
                - max_turns: Maximum conversation turns (default: 1)
                - allowed_tools: List of tools to allow

        Returns:
            LLMResponse with normalized response data

        Raises:
            TimeoutError: If CLI takes too long
            ProviderError: If CLI returns an error
        """
        return asyncio.run(
            self.call_async(prompt, model, max_tokens, temperature, system, **kwargs)
        )

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
        Make an asynchronous LLM call via Claude CLI subprocess.

        This is the preferred method for concurrent operations.
        See call() for parameter documentation.

        Returns:
            LLMResponse with normalized response data
        """
        model = model or self._default_model

        # Build command arguments
        cmd = [
            self._claude_path,
            "-p",
            prompt,
            "--output-format",
            "json",
        ]

        # Add max turns (default: 1 for single-shot LLM calls)
        max_turns = kwargs.get("max_turns", self.config.extra.get("max_turns", 1))
        cmd.extend(["--max-turns", str(max_turns)])

        # Add system prompt if provided
        if system:
            cmd.extend(["--system-prompt", system])

        # Add session resumption if provided
        session_id = kwargs.get("session_id", self.config.extra.get("session_id"))
        if session_id:
            cmd.extend(["--resume", session_id])

        # Add allowed tools (default: none for LLM-only mode)
        allowed_tools = kwargs.get(
            "allowed_tools", self.config.extra.get("allowed_tools")
        )
        if allowed_tools:
            cmd.extend(["--allowed-tools", ",".join(allowed_tools)])
        else:
            # Disable all tools for pure LLM calls
            cmd.extend(["--tools", ""])

        logger.debug("Executing Claude CLI: %s", " ".join(cmd[:4]) + " ...")

        try:
            # Run subprocess
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            try:
                stdout, stderr = await asyncio.wait_for(
                    proc.communicate(), timeout=self._timeout
                )
            except builtins.TimeoutError:
                proc.kill()
                await proc.wait()
                raise TimeoutError(
                    f"Claude CLI timed out after {self._timeout}s",
                    provider=self.name,
                    timeout=self._timeout,
                )

            # Check for errors
            if proc.returncode != 0:
                error_msg = stderr.decode("utf-8", errors="replace").strip()
                raise ProviderError(
                    f"Claude CLI failed (exit code {proc.returncode}): {error_msg}",
                    provider=self.name,
                    details={"exit_code": proc.returncode, "stderr": error_msg},
                )

            # Parse JSON output
            try:
                result = json.loads(stdout.decode("utf-8"))
            except json.JSONDecodeError as e:
                raise ProviderError(
                    f"Failed to parse Claude CLI output: {e}",
                    provider=self.name,
                    details={"stdout": stdout.decode("utf-8", errors="replace")[:500]},
                ) from e

            return self._process_response(result, model)

        except FileNotFoundError as e:
            raise ConnectionError(
                f"Claude CLI not found at {self._claude_path}",
                provider=self.name,
            ) from e

    def _process_response(self, result: dict[str, Any], model: str) -> LLMResponse:
        """
        Process Claude CLI JSON output into LLMResponse.

        Args:
            result: Parsed JSON from CLI stdout
            model: Model used for the request

        Returns:
            Normalized LLMResponse
        """
        # Check for errors in response
        if result.get("is_error", False):
            raise ProviderError(
                f"Claude CLI error: {result.get('result', 'Unknown error')}",
                provider=self.name,
                details=result,
            )

        # Extract content
        content_text = result.get("result", "")

        # Try to parse as JSON
        parsed_content = self._try_parse_json(content_text)

        # Extract usage information
        usage = result.get("usage", {})
        usage_dict = {
            "input_tokens": usage.get("input_tokens", 0),
            "output_tokens": usage.get("output_tokens", 0),
            "cache_creation_input_tokens": usage.get("cache_creation_input_tokens", 0),
            "cache_read_input_tokens": usage.get("cache_read_input_tokens", 0),
        }

        # Get cost from CLI (more accurate than estimation)
        cost = result.get("total_cost_usd")

        # Extract model from modelUsage if available
        model_usage = result.get("modelUsage", {})
        actual_model = model
        if model_usage:
            # Get the first (usually primary) model used
            actual_model = next(iter(model_usage.keys()), model)

        logger.info(
            "Claude CLI call successful: input_tokens=%d, output_tokens=%d, cost=$%.4f",
            usage_dict["input_tokens"],
            usage_dict["output_tokens"],
            cost or 0.0,
        )

        return LLMResponse(
            content=parsed_content,
            raw_content=content_text,
            usage=usage_dict,
            cost=cost,
            model=actual_model,
            provider=self.name,
            stop_reason="end_turn",
            metadata={
                "session_id": result.get("session_id"),
                "duration_ms": result.get("duration_ms"),
                "duration_api_ms": result.get("duration_api_ms"),
                "num_turns": result.get("num_turns"),
                "model_usage": model_usage,
            },
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

    async def resume_session(
        self,
        session_id: str,
        prompt: str,
        **kwargs: Any,
    ) -> LLMResponse:
        """
        Resume a previous session with a new prompt.

        Args:
            session_id: Session ID from a previous response
            prompt: New prompt to continue the conversation
            **kwargs: Additional arguments passed to call_async

        Returns:
            LLMResponse with the continuation
        """
        return await self.call_async(prompt, session_id=session_id, **kwargs)
