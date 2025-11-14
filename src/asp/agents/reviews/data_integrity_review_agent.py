"""
Data Integrity Review Agent: Specialist agent for data integrity design review.

This agent focuses exclusively on data integrity aspects of design specifications:
- Referential integrity (foreign keys, cascade rules)
- Data validation (constraints, CHECK, NOT NULL, UNIQUE)
- Transaction design (ACID properties, transaction boundaries)
- Data consistency (enum values, data types)
"""

import json
import logging
from typing import Any, Optional

from asp.agents.base_agent import AgentExecutionError, BaseAgent
from asp.models.design import DesignSpecification
from asp.telemetry.telemetry import track_agent_cost

logger = logging.getLogger(__name__)


class DataIntegrityReviewAgent(BaseAgent):
    """
    Specialist agent for data integrity design review.

    Focuses on identifying data integrity risks and providing
    actionable data integrity improvements.
    """

    def __init__(
        self,
        llm_client: Optional[Any] = None,
        db_path: Optional[str] = None,
    ):
        """
        Initialize Data Integrity Review Agent.

        Args:
            llm_client: Optional LLM client instance (for testing/mocking)
            db_path: Optional database path (for testing)
        """
        super().__init__(
            agent_role="DataIntegrityReview",
            agent_version="1.0.0",
            llm_client=llm_client,
            db_path=db_path,
        )

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
        logger.info(
            f"Starting data integrity review for task {design_spec.task_id}"
        )

        try:
            # Load and format prompt
            prompt_variables = {
                "design_specification": design_spec.model_dump_json(indent=2),
            }

            prompt = self._load_and_format_prompt(
                "data_integrity_review_agent_v1.txt", prompt_variables
            )

            # Call LLM
            logger.debug("Calling LLM for data integrity review")
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
                    f"Data integrity review completed: found {len(content['issues_found'])} issues, "
                    f"{len(content['improvement_suggestions'])} suggestions"
                )

                return content

            except (json.JSONDecodeError, KeyError, ValueError) as e:
                logger.error(f"Failed to parse LLM response: {e}")
                raise AgentExecutionError(
                    f"Failed to parse data integrity review response: {e}"
                ) from e

        except Exception as e:
            logger.error(f"Data integrity review failed: {e}", exc_info=True)
            raise AgentExecutionError(f"Data integrity review failed: {e}") from e
