"""
Architecture Review Agent: Specialist agent for architecture design review.

Focuses on: Design patterns, separation of concerns, testability, extensibility.
"""

# pylint: disable=logging-fstring-interpolation,arguments-renamed

import logging
from typing import Any

from asp.agents.base_agent import AgentExecutionError, BaseAgent
from asp.models.design import DesignSpecification
from asp.telemetry.telemetry import track_agent_cost
from asp.utils.json_extraction import JSONExtractionError, extract_json_from_response

logger = logging.getLogger(__name__)


class ArchitectureReviewAgent(BaseAgent):
    """Specialist agent for architecture design review."""

    def __init__(
        self,
        llm_client: Any | None = None,
        db_path: str | None = None,
    ):
        super().__init__(
            llm_client=llm_client,
            db_path=db_path,
        )
        self.agent_version = "1.0.0"

    @track_agent_cost(
        agent_role="ArchitectureReview",
        agent_version="1.0.0",
        task_id_param="design_spec.task_id",
    )
    def execute(
        self,
        design_spec: DesignSpecification,
    ) -> dict[str, Any]:
        logger.info(f"Starting architecture review for task {design_spec.task_id}")

        try:
            prompt_template = self.load_prompt("architecture_review_agent_v1")
            prompt = self.format_prompt(
                prompt_template,
                design_specification=design_spec.model_dump_json(indent=2),
            )

            response = self.call_llm(prompt, max_tokens=8192)

            # Parse JSON response with robust extraction
            try:
                content = extract_json_from_response(
                    response,
                    required_fields=["issues_found", "improvement_suggestions"],
                )

                logger.info(
                    f"Architecture review completed: {len(content['issues_found'])} issues, "
                    f"{len(content['improvement_suggestions'])} suggestions"
                )

                return content

            except JSONExtractionError as e:
                raise AgentExecutionError(f"Failed to parse LLM response: {e}") from e

        except Exception as e:
            logger.error(f"Architecture review failed: {e}", exc_info=True)
            raise AgentExecutionError(f"Architecture review failed: {e}") from e
