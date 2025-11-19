"""
Code Security Review Agent: Specialist agent for security code review.

This agent focuses exclusively on security aspects of generated code:
- SQL injection, XSS, CSRF vulnerabilities
- Authentication and authorization flaws
- Sensitive data exposure
- Cryptographic issues
- Dependency vulnerabilities
- Input validation and sanitization
"""

import json
import logging
from typing import Any, Optional

from asp.agents.base_agent import AgentExecutionError, BaseAgent
from asp.models.code import GeneratedCode
from asp.telemetry.telemetry import track_agent_cost

logger = logging.getLogger(__name__)


class CodeSecurityReviewAgent(BaseAgent):
    """
    Specialist agent for security code review.

    Focuses on identifying security vulnerabilities and providing
    actionable security improvements.
    """

    def __init__(
        self,
        llm_client: Optional[Any] = None,
        db_path: Optional[str] = None,
    ):
        """
        Initialize Code Security Review Agent.

        Args:
            llm_client: Optional LLM client instance (for testing/mocking)
            db_path: Optional database path (for testing)
        """
        super().__init__(
            llm_client=llm_client,
            db_path=db_path,
        )
        self.agent_version = "1.0.0"

    @track_agent_cost(
        agent_role="CodeSecurityReview",
        agent_version="1.0.0",
        task_id_param="generated_code.task_id",
    )
    def execute(
        self,
        generated_code: GeneratedCode,
    ) -> dict[str, Any]:
        """
        Execute security review on generated code.

        Args:
            generated_code: GeneratedCode to review

        Returns:
            Dictionary with issues_found and improvement_suggestions

        Raises:
            AgentExecutionError: If review fails
        """
        logger.info(
            f"Starting security review for task {generated_code.task_id}"
        )

        try:
            # Load and format prompt
            prompt_template = self.load_prompt("code_security_review_agent_v1")
            prompt = self.format_prompt(
                prompt_template,
                generated_code=generated_code.model_dump_json(indent=2),
            )

            # Call LLM
            logger.debug("Calling LLM for security review")
            response = self.call_llm(prompt)

            # Parse JSON response
            try:
                content = response.get("content", {})
                if isinstance(content, str):
                    content = json.loads(content)

                # Validate response structure
                if "issues_found" not in content:
                    raise ValueError("Response missing 'issues_found' field")
                if "improvement_suggestions" not in content:
                    raise ValueError(
                        "Response missing 'improvement_suggestions' field"
                    )

                logger.info(
                    f"Security review completed: {len(content['issues_found'])} issues, "
                    f"{len(content['improvement_suggestions'])} suggestions"
                )

                return content

            except json.JSONDecodeError as e:
                raise AgentExecutionError(
                    f"Failed to parse LLM response as JSON: {e}"
                ) from e
            except ValueError as e:
                raise AgentExecutionError(
                    f"Invalid response structure: {e}"
                ) from e

        except Exception as e:
            logger.error(f"Security review failed: {e}")
            raise AgentExecutionError(
                f"CodeSecurityReviewAgent failed: {e}"
            ) from e
