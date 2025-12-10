"""
Security Review Agent: Specialist agent for security design review.

This agent focuses exclusively on security aspects of design specifications:
- Authentication and authorization mechanisms
- Input validation and sanitization
- Injection prevention (SQL, XSS, CSRF)
- Sensitive data handling (encryption, hashing)
- API rate limiting and abuse prevention
"""

# pylint: disable=logging-fstring-interpolation,arguments-renamed

import logging
from typing import Any

from asp.agents.base_agent import AgentExecutionError, BaseAgent
from asp.models.design import DesignSpecification
from asp.telemetry.telemetry import track_agent_cost
from asp.utils.json_extraction import JSONExtractionError, extract_json_from_response

logger = logging.getLogger(__name__)


class SecurityReviewAgent(BaseAgent):
    """
    Specialist agent for security design review.

    Focuses on identifying security vulnerabilities and providing
    actionable security improvements.
    """

    def __init__(
        self,
        llm_client: Any | None = None,
        db_path: str | None = None,
    ):
        """
        Initialize Security Review Agent.

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
        agent_role="SecurityReview",
        agent_version="1.0.0",
        task_id_param="design_spec.task_id",
    )
    def execute(
        self,
        design_spec: DesignSpecification,
    ) -> dict[str, Any]:
        """
        Execute security review on a design specification.

        Args:
            design_spec: DesignSpecification to review

        Returns:
            Dictionary with issues_found and improvement_suggestions

        Raises:
            AgentExecutionError: If review fails
        """
        logger.info(f"Starting security review for task {design_spec.task_id}")

        try:
            # Load and format prompt
            prompt_template = self.load_prompt("security_review_agent_v1")
            prompt = self.format_prompt(
                prompt_template,
                design_specification=design_spec.model_dump_json(indent=2),
            )

            # Call LLM with higher token limit to avoid truncation
            logger.debug("Calling LLM for security review")
            response = self.call_llm(prompt, max_tokens=8192)

            # Parse JSON response with robust extraction
            try:
                content = extract_json_from_response(
                    response,
                    required_fields=["issues_found", "improvement_suggestions"],
                )

                logger.info(
                    f"Security review completed: found {len(content['issues_found'])} issues, "
                    f"{len(content['improvement_suggestions'])} suggestions"
                )

                return content

            except JSONExtractionError as e:
                raise AgentExecutionError(f"Failed to parse LLM response: {e}") from e

        except Exception as e:
            logger.error(f"Security review failed: {e}", exc_info=True)
            raise AgentExecutionError(f"Security review failed: {e}") from e
