"""
Tests for json_extraction module.

Author: ASP Development Team
Date: December 23, 2025
"""

import pytest

from asp.utils.json_extraction import JSONExtractionError, extract_json_from_response


class TestExtractJsonFromResponse:
    """Tests for extract_json_from_response function."""

    def test_extract_from_dict_content(self):
        """Test extraction when content is already a dict."""
        response = {"content": {"key": "value", "number": 42}}
        result = extract_json_from_response(response)
        assert result == {"key": "value", "number": 42}

    def test_extract_from_markdown_fence(self):
        """Test extraction from markdown code fence."""
        response = {"content": '```json\n{"key": "value"}\n```'}
        result = extract_json_from_response(response)
        assert result == {"key": "value"}

    def test_extract_from_raw_json_string(self):
        """Test extraction from raw JSON string."""
        response = {"content": '{"key": "value"}'}
        result = extract_json_from_response(response)
        assert result == {"key": "value"}

    def test_invalid_json_in_markdown_fence(self):
        """Test error handling when JSON in markdown fence is invalid."""
        response = {"content": '```json\n{invalid json}\n```'}
        with pytest.raises(JSONExtractionError) as exc_info:
            extract_json_from_response(response)
        assert "Failed to parse JSON from markdown fence" in str(exc_info.value)
        assert "JSON content preview" in str(exc_info.value)

    def test_invalid_json_string(self):
        """Test error handling when raw string is invalid JSON."""
        response = {"content": "not json at all"}
        with pytest.raises(JSONExtractionError) as exc_info:
            extract_json_from_response(response)
        assert "LLM returned non-JSON response" in str(exc_info.value)

    def test_unexpected_content_type(self):
        """Test error handling when content is unexpected type."""
        response = {"content": 12345}  # Integer instead of dict/string
        with pytest.raises(JSONExtractionError) as exc_info:
            extract_json_from_response(response)
        assert "Unexpected content type" in str(exc_info.value)
        assert "int" in str(exc_info.value)

    def test_required_fields_present(self):
        """Test validation passes when required fields are present."""
        response = {"content": {"name": "test", "value": 42}}
        result = extract_json_from_response(response, required_fields=["name", "value"])
        assert result == {"name": "test", "value": 42}

    def test_required_fields_missing(self):
        """Test error when required fields are missing."""
        response = {"content": {"name": "test"}}
        with pytest.raises(JSONExtractionError) as exc_info:
            extract_json_from_response(response, required_fields=["name", "missing"])
        assert "missing required fields" in str(exc_info.value)
        assert "missing" in str(exc_info.value)

    def test_empty_content(self):
        """Test handling of empty content."""
        response = {"content": ""}
        with pytest.raises(JSONExtractionError):
            extract_json_from_response(response)

    def test_list_content_type(self):
        """Test error handling when content is a list."""
        response = {"content": [1, 2, 3]}
        with pytest.raises(JSONExtractionError) as exc_info:
            extract_json_from_response(response)
        assert "Unexpected content type" in str(exc_info.value)
        assert "list" in str(exc_info.value)
