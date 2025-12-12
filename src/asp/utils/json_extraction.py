"""JSON extraction utilities for LLM responses.

Provides robust JSON extraction from LLM responses that may contain
markdown code fences or other surrounding text.
"""

import json
import logging
import re
from typing import Any

logger = logging.getLogger(__name__)


class JSONExtractionError(Exception):
    """Raised when JSON extraction fails."""


def extract_json_from_response(
    response: dict[str, Any],
    required_fields: list[str] | None = None,
) -> dict[str, Any]:
    """
    Extract JSON from an LLM response, handling markdown fences.

    This function handles common LLM response patterns:
    1. Response already parsed as dict by LLMClient
    2. Response is a string containing ```json...``` fences
    3. Response is a raw JSON string

    Args:
        response: LLM response dict with 'content' key
        required_fields: Optional list of fields that must be present in result

    Returns:
        Parsed JSON as a dictionary

    Raises:
        JSONExtractionError: If JSON extraction or validation fails
    """
    content = response.get("content", {})

    # Case 1: Already parsed as dict
    if isinstance(content, dict):
        result = content
    elif isinstance(content, str):
        # Case 2: Try to extract from markdown code fences
        json_match = re.search(r"```(?:json)?\s*(.*?)\s*```", content, re.DOTALL)
        if json_match:
            try:
                json_str = json_match.group(1).strip()
                result = json.loads(json_str)
                logger.debug("Successfully extracted JSON from markdown code fence")
            except json.JSONDecodeError as e:
                json_preview = json_match.group(1).strip()[:500]
                raise JSONExtractionError(
                    f"Failed to parse JSON from markdown fence: {e}\n"
                    f"JSON content preview: {json_preview}..."
                ) from e
        else:
            # Case 3: Try to parse the whole string as JSON
            try:
                result = json.loads(content)
                logger.debug("Successfully parsed string content as JSON")
            except json.JSONDecodeError as e:
                content_preview = content[:500] if content else "(empty)"
                raise JSONExtractionError(
                    f"LLM returned non-JSON response: {content_preview}...\nError: {e}"
                ) from e
    else:
        raise JSONExtractionError(f"Unexpected content type: {type(content).__name__}")

    # Validate required fields if specified
    if required_fields:
        missing_fields = [f for f in required_fields if f not in result]
        if missing_fields:
            raise JSONExtractionError(
                f"Response missing required fields: {missing_fields}"
            )

    return result
