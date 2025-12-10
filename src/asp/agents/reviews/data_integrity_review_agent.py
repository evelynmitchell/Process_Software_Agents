"""
Data Integrity Review Agent: Specialist agent for data integrity design review.

This agent focuses exclusively on data integrity aspects of design specifications:
- Referential integrity (foreign keys, cascade rules)
- Data validation (constraints, CHECK, NOT NULL, UNIQUE)
- Transaction design (ACID properties, transaction boundaries)
- Data consistency (enum values, data types)
"""

# pylint: disable=logging-fstring-interpolation,arguments-renamed

import logging
from typing import Any

from asp.agents.base_agent import AgentExecutionError, BaseAgent
from asp.models.design import DesignSpecification
from asp.telemetry.telemetry import track_agent_cost
from asp.utils.json_extraction import JSONExtractionError, extract_json_from_response

logger = logging.getLogger(__name__)


class DataIntegrityReviewAgent(BaseAgent):
    """
    Specialist agent for data integrity design review.

    Focuses on identifying data integrity risks and providing
    actionable data integrity improvements.
    """

    def __init__(
        self,
        llm_client: Any | None = None,
        db_path: str | None = None,
    ):
        """
        Initialize Data Integrity Review Agent.

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
        agent_role="DataIntegrityReview",
        agent_version="1.0.0",
        task_id_param="design_spec.task_id",
    )
    def execute(
        self,
        design_spec: DesignSpecification,
    ) -> dict[str, Any]:
        """
        Execute data integrity review on a design specification.

        Args:
            design_spec: DesignSpecification to review

        Returns:
            Dictionary with issues_found and improvement_suggestions

        Raises:
            AgentExecutionError: If review fails
        """
        logger.info(f"Starting data integrity review for task {design_spec.task_id}")

        try:
            # Load and format prompt
            prompt_template = self.load_prompt("data_integrity_review_agent_v1")
            prompt = self.format_prompt(
                prompt_template,
                design_specification=design_spec.model_dump_json(indent=2),
            )

            # Call LLM
            logger.debug("Calling LLM for data integrity review")
            response = self.call_llm(prompt, max_tokens=8192)

            # Parse JSON response with robust extraction
            try:
                content = extract_json_from_response(
                    response,
                    required_fields=["issues_found", "improvement_suggestions"],
                )

                logger.info(
                    f"Data integrity review completed: found {len(content['issues_found'])} issues, "
                    f"{len(content['improvement_suggestions'])} suggestions"
                )

                return content

            except JSONExtractionError as e:
                raise AgentExecutionError(f"Failed to parse LLM response: {e}") from e

        except Exception as e:
            logger.error(f"Data integrity review failed: {e}", exc_info=True)
            raise AgentExecutionError(f"Data integrity review failed: {e}") from e
