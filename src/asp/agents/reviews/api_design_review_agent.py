"""
API Design Review Agent: Specialist agent for API design review.

Focuses on: RESTful principles, HTTP methods, status codes, error handling, versioning.
"""

import json
import logging
from typing import Any

from pydantic import BaseModel
from asp.agents.base_agent import AgentExecutionError, BaseAgent
from asp.models.design import DesignSpecification
from asp.telemetry.telemetry import track_agent_cost

logger = logging.getLogger(__name__)


class APIDesignReviewAgent(BaseAgent):
    """Specialist agent for API design review."""

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

    @track_agent_cost(  # type: ignore
        agent_role="APIDesignReview",
        agent_version="1.0.0",
        task_id_param="design_spec.task_id",
    )
    def execute(
        self,
        design_spec: DesignSpecification,
    ) -> BaseModel:
        logger.info(f"Starting API design review for task {design_spec.task_id}")

        try:
            prompt_template = self.load_prompt("api_design_review_agent_v1")
            prompt = self.format_prompt(
                prompt_template,
                design_specification=design_spec.model_dump_json(indent=2),
            )

            response = self.call_llm(prompt)

            content = response.get("content", {})
            if isinstance(content, str):
                content = json.loads(content)

            if (
                "issues_found" not in content
                or "improvement_suggestions" not in content
            ):
                raise ValueError("Response missing required fields")

            logger.info(
                f"API design review completed: {len(content['issues_found'])} issues, "
                f"{len(content['improvement_suggestions'])} suggestions"
            )

            return content

        except Exception as e:
            logger.error(f"API design review failed: {e}", exc_info=True)
            raise AgentExecutionError(f"API design review failed: {e}") from e
