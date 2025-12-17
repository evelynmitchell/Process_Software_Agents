"""
Base Agent Abstract Class for ASP Platform

This module provides the abstract base class that all ASP agents inherit from.
It provides common functionality for prompt loading, LLM calls, telemetry integration,
and error handling.

Supports both synchronous and asynchronous execution patterns for parallel agent
orchestration (ADR 008).

Author: ASP Development Team
Date: November 13, 2025
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

from pydantic import BaseModel

logger = logging.getLogger(__name__)


class BaseAgent(ABC):
    """
    Abstract base class for all ASP agents.

    Provides common functionality:
    - Prompt template loading from files
    - LLM client integration with retry logic
    - Telemetry decorator integration
    - Error handling and logging

    All 7 agents (Planning, Design, DesignReview, Code, CodeReview, Test, Postmortem)
    inherit from this class.

    Example:
        class PlanningAgent(BaseAgent):
            def execute(self, input_data: TaskRequirements) -> ProjectPlan:
                # Implementation here
                pass
    """

    def __init__(
        self,
        db_path: Path | None = None,
        llm_client: Any | None = None,
    ):
        """
        Initialize base agent.

        Args:
            db_path: Optional path to SQLite database for telemetry
            llm_client: Optional LLM client (for dependency injection in tests)
        """
        self.db_path = db_path
        self._llm_client = llm_client
        self.agent_name = self.__class__.__name__
        self.agent_version = "1.0.0"  # Override in subclasses
        self._last_llm_usage = {}  # Track last LLM call usage for telemetry

    @property
    def llm_client(self):
        """
        Lazy-load LLM client.

        This allows for dependency injection in tests while maintaining
        convenience in production.
        """
        if self._llm_client is None:
            # Import here to avoid circular dependencies
            from asp.utils.llm_client import LLMClient

            self._llm_client = LLMClient()
        return self._llm_client

    def load_prompt(self, prompt_name: str) -> str:
        """
        Load prompt template from file.

        Prompts are stored in src/asp/prompts/ as text files.
        Naming convention: {agent_name}_{version}_{purpose}.txt

        Example:
            prompt = self.load_prompt("planning_agent_v1_decomposition")
            # Loads: src/asp/prompts/planning_agent_v1_decomposition.txt

        Args:
            prompt_name: Name of prompt file (without .txt extension)

        Returns:
            str: Prompt template content

        Raises:
            FileNotFoundError: If prompt file doesn't exist
        """
        prompts_dir = Path(__file__).parent.parent / "prompts"
        prompt_path = prompts_dir / f"{prompt_name}.txt"

        if not prompt_path.exists():
            raise FileNotFoundError(
                f"Prompt file not found: {prompt_path}\n"
                f"Expected location: {prompts_dir}/\n"
                f"Available prompts: {list(prompts_dir.glob('*.txt'))}"
            )

        logger.debug(f"Loading prompt from {prompt_path}")
        return prompt_path.read_text()

    def format_prompt(self, template: str, **kwargs) -> str:
        """
        Format prompt template with variables.

        Supports both str.format() style and simple replacement.

        Example:
            template = "Task: {task_description}\nRequirements: {requirements}"
            formatted = self.format_prompt(
                template,
                task_description="Build API",
                requirements="REST endpoints"
            )

        Args:
            template: Prompt template string
            **kwargs: Variables to substitute into template

        Returns:
            str: Formatted prompt
        """
        try:
            return template.format(**kwargs)
        except KeyError as e:
            raise ValueError(
                f"Missing required prompt variable: {e}\n"
                f"Template requires: {template}\n"
                f"Provided: {kwargs.keys()}"
            )

    def call_llm(
        self,
        prompt: str,
        model: str | None = None,
        max_tokens: int = 4096,
        temperature: float = 0.0,
        **kwargs,
    ) -> dict[str, Any]:
        """
        Call LLM with retry logic and telemetry.

        This method wraps the LLM client's call_with_retry method and provides
        consistent error handling and logging.

        Args:
            prompt: Formatted prompt string
            model: Optional model name (overrides default)
            max_tokens: Maximum tokens in response
            temperature: Sampling temperature (0.0 = deterministic)
            **kwargs: Additional arguments passed to LLM client

        Returns:
            Dict containing LLM response (format depends on client)

        Raises:
            AgentExecutionError: If LLM call fails after retries
        """
        try:
            logger.info(
                f"{self.agent_name}: Calling LLM "
                f"(model={model or 'default'}, max_tokens={max_tokens}, temp={temperature})"
            )

            response = self.llm_client.call_with_retry(
                prompt=prompt,
                model=model,
                max_tokens=max_tokens,
                temperature=temperature,
                **kwargs,
            )

            # Store usage data for telemetry
            self._last_llm_usage = {
                "input_tokens": response.get("usage", {}).get("input_tokens", 0),
                "output_tokens": response.get("usage", {}).get("output_tokens", 0),
                "total_tokens": response.get("usage", {}).get("input_tokens", 0)
                + response.get("usage", {}).get("output_tokens", 0),
                "cost": response.get("cost", 0.0),
                "model": response.get("model", model or "unknown"),
            }

            logger.info(f"{self.agent_name}: LLM call successful")
            return response

        except Exception as e:
            logger.error(f"{self.agent_name}: LLM call failed: {e}")
            raise AgentExecutionError(
                f"{self.agent_name} failed during LLM call: {e}"
            ) from e

    async def call_llm_async(
        self,
        prompt: str,
        model: str | None = None,
        max_tokens: int = 4096,
        temperature: float = 0.0,
        **kwargs,
    ) -> dict[str, Any]:
        """
        Asynchronous LLM call with retry logic and telemetry.

        This method wraps the LLM client's async call method and provides
        consistent error handling and logging. Use this for concurrent agent
        execution patterns.

        Args:
            prompt: Formatted prompt string
            model: Optional model name (overrides default)
            max_tokens: Maximum tokens in response
            temperature: Sampling temperature (0.0 = deterministic)
            **kwargs: Additional arguments passed to LLM client

        Returns:
            Dict containing LLM response (format depends on client)

        Raises:
            AgentExecutionError: If LLM call fails after retries
        """
        try:
            logger.info(
                f"{self.agent_name}: Async calling LLM "
                f"(model={model or 'default'}, max_tokens={max_tokens}, temp={temperature})"
            )

            response = await self.llm_client.call_with_retry_async(
                prompt=prompt,
                model=model,
                max_tokens=max_tokens,
                temperature=temperature,
                **kwargs,
            )

            # Store usage data for telemetry
            self._last_llm_usage = {
                "input_tokens": response.get("usage", {}).get("input_tokens", 0),
                "output_tokens": response.get("usage", {}).get("output_tokens", 0),
                "total_tokens": response.get("usage", {}).get("input_tokens", 0)
                + response.get("usage", {}).get("output_tokens", 0),
                "cost": response.get("cost", 0.0),
                "model": response.get("model", model or "unknown"),
            }

            logger.info(f"{self.agent_name}: Async LLM call successful")
            return response

        except Exception as e:
            logger.error(f"{self.agent_name}: Async LLM call failed: {e}")
            raise AgentExecutionError(
                f"{self.agent_name} failed during async LLM call: {e}"
            ) from e

    def validate_output(
        self,
        data: dict[str, Any],
        model_class: type[BaseModel],
    ) -> BaseModel:
        """
        Validate LLM output against Pydantic model.

        This ensures type safety and catches malformed LLM responses early.

        Example:
            response = self.call_llm(prompt)
            validated = self.validate_output(response, ProjectPlan)
            # validated is now a ProjectPlan instance with type checking

        Args:
            data: Dictionary data from LLM response
            model_class: Pydantic model class to validate against

        Returns:
            Validated Pydantic model instance

        Raises:
            ValidationError: If data doesn't match model schema
        """
        try:
            return model_class.model_validate(data)
        except Exception as e:
            logger.error(
                f"{self.agent_name}: Output validation failed\n"
                f"Expected: {model_class.__name__}\n"
                f"Received: {data}\n"
                f"Error: {e}"
            )
            raise

    @abstractmethod
    def execute(self, input_data: BaseModel) -> BaseModel:
        """
        Execute agent logic.

        This is the main entry point for agent execution. Each agent implements
        this method with their specific logic.

        The execute method should:
        1. Validate input data
        2. Load and format prompts
        3. Call LLM
        4. Parse and validate output
        5. Return structured result

        Telemetry is typically applied via decorators on this method.

        Args:
            input_data: Pydantic model with agent-specific input

        Returns:
            Pydantic model with agent-specific output

        Raises:
            AgentExecutionError: If execution fails
        """
        pass

    async def execute_async(self, input_data: BaseModel) -> BaseModel:
        """
        Asynchronous version of execute.

        Default implementation runs the sync execute() in a thread pool
        for backward compatibility. Subclasses can override this for
        native async execution using call_llm_async().

        For native async implementation in subclasses:

        Example:
            class CodeAgent(BaseAgent):
                async def execute_async(self, input_data: CodeInput) -> GeneratedCode:
                    prompt = self._build_prompt(input_data)
                    response = await self.call_llm_async(prompt)
                    return self._parse_response(response)

        Args:
            input_data: Pydantic model with agent-specific input

        Returns:
            Pydantic model with agent-specific output

        Raises:
            AgentExecutionError: If execution fails
        """
        # Default: run sync version in thread pool (backward compatible)
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, self.execute, input_data)


class AgentExecutionError(Exception):
    """
    Exception raised when an agent fails to execute.

    This is a custom exception that wraps underlying errors (LLM failures,
    validation errors, etc.) with context about which agent failed.
    """

    pass
