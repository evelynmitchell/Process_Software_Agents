"""
Unit tests for hash-based ID generation utilities.

Tests the id_generation module which provides functions for generating
unique, hash-based identifiers for ASP entities.
"""

import re

import pytest

from asp.utils.id_generation import (
    CODE_IMPROVEMENT_ID_PATTERN,
    CODE_ISSUE_ID_PATTERN,
    HASH_ID_PATTERN,
    IMPROVEMENT_ID_PATTERN,
    ISSUE_ID_PATTERN,
    LEGACY_CODE_IMPROVEMENT_PATTERN,
    LEGACY_CODE_ISSUE_PATTERN,
    LEGACY_IMPROVEMENT_PATTERN,
    LEGACY_ISSUE_PATTERN,
    LEGACY_SEMANTIC_UNIT_PATTERN,
    SEMANTIC_UNIT_ID_PATTERN,
    generate_checklist_id,
    generate_code_improvement_id,
    generate_code_issue_id,
    generate_hash_id,
    generate_improvement_id,
    generate_issue_id,
    generate_semantic_unit_id,
    generate_task_id,
    is_legacy_id,
    is_valid_hash_id,
)


class TestGenerateHashId:
    """Tests for the base generate_hash_id function."""

    def test_generates_id_with_prefix(self):
        """ID should start with the given prefix."""
        result = generate_hash_id("test")
        assert result.startswith("test-")

    def test_generates_id_with_correct_length(self):
        """Hash portion should have the default length (7)."""
        result = generate_hash_id("test")
        hash_part = result.split("-")[1]
        assert len(hash_part) == 7

    def test_generates_id_with_custom_length(self):
        """Should support custom hash lengths."""
        result = generate_hash_id("test", length=8)
        hash_part = result.split("-")[1]
        assert len(hash_part) == 8

    def test_generates_unique_ids(self):
        """Each call should generate a unique ID."""
        ids = [generate_hash_id("test") for _ in range(100)]
        assert len(set(ids)) == 100

    def test_generates_lowercase_hex(self):
        """Hash portion should be lowercase hex characters."""
        result = generate_hash_id("test")
        hash_part = result.split("-")[1]
        assert re.match(r"^[a-f0-9]+$", hash_part)

    def test_matches_hash_id_pattern(self):
        """Generated ID should match the HASH_ID_PATTERN."""
        result = generate_hash_id("test")
        assert re.match(HASH_ID_PATTERN, result)


class TestSpecificIdGenerators:
    """Tests for entity-specific ID generators."""

    def test_generate_semantic_unit_id(self):
        """Should generate valid semantic unit ID."""
        result = generate_semantic_unit_id()
        assert result.startswith("su-")
        assert re.match(SEMANTIC_UNIT_ID_PATTERN, result)

    def test_generate_issue_id(self):
        """Should generate valid issue ID."""
        result = generate_issue_id()
        assert result.startswith("issue-")
        assert re.match(ISSUE_ID_PATTERN, result)

    def test_generate_improvement_id(self):
        """Should generate valid improvement ID."""
        result = generate_improvement_id()
        assert result.startswith("improve-")
        assert re.match(IMPROVEMENT_ID_PATTERN, result)

    def test_generate_code_issue_id(self):
        """Should generate valid code issue ID."""
        result = generate_code_issue_id()
        assert result.startswith("code-issue-")
        assert re.match(CODE_ISSUE_ID_PATTERN, result)

    def test_generate_code_improvement_id(self):
        """Should generate valid code improvement ID."""
        result = generate_code_improvement_id()
        assert result.startswith("code-improve-")
        assert re.match(CODE_IMPROVEMENT_ID_PATTERN, result)

    def test_generate_checklist_id(self):
        """Should generate valid checklist ID."""
        result = generate_checklist_id()
        assert result.startswith("check-")
        assert re.match(r"^check-[a-f0-9]{7}$", result)

    def test_generate_task_id(self):
        """Should generate valid task ID."""
        result = generate_task_id()
        assert result.startswith("task-")
        assert re.match(r"^task-[a-f0-9]{7}$", result)


class TestIsValidHashId:
    """Tests for hash ID validation."""

    def test_valid_hash_id_no_prefix(self):
        """Should accept valid hash IDs without prefix check."""
        assert is_valid_hash_id("su-a3f42bc")
        assert is_valid_hash_id("issue-b7c91de")
        assert is_valid_hash_id("test-1234567")

    def test_valid_hash_id_with_prefix(self):
        """Should validate prefix when specified."""
        assert is_valid_hash_id("su-a3f42bc", prefix="su")
        assert is_valid_hash_id("issue-b7c91de", prefix="issue")

    def test_invalid_prefix(self):
        """Should reject ID with wrong prefix."""
        assert not is_valid_hash_id("su-a3f42bc", prefix="issue")
        assert not is_valid_hash_id("issue-b7c91de", prefix="su")

    def test_invalid_legacy_format(self):
        """Should reject legacy sequential IDs."""
        assert not is_valid_hash_id("SU-001")
        assert not is_valid_hash_id("ISSUE-001")
        assert not is_valid_hash_id("CODE-ISSUE-001")

    def test_invalid_uppercase(self):
        """Should reject uppercase hex characters."""
        assert not is_valid_hash_id("su-A3F42BC")

    def test_invalid_length(self):
        """Should reject wrong length hash portion."""
        assert not is_valid_hash_id("su-a3f")  # Too short (3 chars)
        assert not is_valid_hash_id("su-a3f42")  # Too short (5 chars)
        assert not is_valid_hash_id("su-a3f42bc9")  # Too long (8 chars)

    def test_invalid_characters(self):
        """Should reject non-hex characters."""
        assert not is_valid_hash_id("su-ghijklm")
        assert not is_valid_hash_id("su-12!@#ab")


class TestIsLegacyId:
    """Tests for legacy ID detection."""

    def test_legacy_semantic_unit(self):
        """Should detect legacy SU-xxx format."""
        assert is_legacy_id("SU-001")
        assert is_legacy_id("SU-123")
        assert is_legacy_id("SU-999")

    def test_legacy_issue(self):
        """Should detect legacy ISSUE-xxx format."""
        assert is_legacy_id("ISSUE-001")
        assert is_legacy_id("ISSUE-456")

    def test_legacy_improvement(self):
        """Should detect legacy IMPROVE-xxx format."""
        assert is_legacy_id("IMPROVE-001")
        assert is_legacy_id("IMPROVE-789")

    def test_legacy_code_issue(self):
        """Should detect legacy CODE-ISSUE-xxx format."""
        assert is_legacy_id("CODE-ISSUE-001")
        assert is_legacy_id("CODE-ISSUE-123")

    def test_legacy_code_improvement(self):
        """Should detect legacy CODE-IMPROVE-xxx format."""
        assert is_legacy_id("CODE-IMPROVE-001")
        assert is_legacy_id("CODE-IMPROVE-456")

    def test_new_hash_format_not_legacy(self):
        """Should not detect new hash IDs as legacy."""
        assert not is_legacy_id("su-a3f42bc")
        assert not is_legacy_id("issue-b7c91de")
        assert not is_legacy_id("code-issue-f1a23bc")

    def test_invalid_legacy_format(self):
        """Should not match invalid legacy formats."""
        assert not is_legacy_id("SU-1")  # Too short
        assert not is_legacy_id("SU-1234")  # Too long
        assert not is_legacy_id("su-001")  # Wrong case


class TestPatternConstants:
    """Tests for regex pattern constants."""

    def test_semantic_unit_pattern_matches_valid(self):
        """SEMANTIC_UNIT_ID_PATTERN should match valid IDs."""
        assert re.match(SEMANTIC_UNIT_ID_PATTERN, "su-a3f42bc")
        assert re.match(SEMANTIC_UNIT_ID_PATTERN, "su-0000000")
        assert re.match(SEMANTIC_UNIT_ID_PATTERN, "su-fffffff")

    def test_semantic_unit_pattern_rejects_invalid(self):
        """SEMANTIC_UNIT_ID_PATTERN should reject invalid IDs."""
        assert not re.match(SEMANTIC_UNIT_ID_PATTERN, "SU-001")
        assert not re.match(SEMANTIC_UNIT_ID_PATTERN, "su-a3f")
        assert not re.match(SEMANTIC_UNIT_ID_PATTERN, "issue-a3f42bc")

    def test_code_issue_pattern_matches_valid(self):
        """CODE_ISSUE_ID_PATTERN should match valid IDs."""
        assert re.match(CODE_ISSUE_ID_PATTERN, "code-issue-a3f42bc")
        assert re.match(CODE_ISSUE_ID_PATTERN, "code-issue-1234567")

    def test_code_issue_pattern_rejects_invalid(self):
        """CODE_ISSUE_ID_PATTERN should reject invalid IDs."""
        assert not re.match(CODE_ISSUE_ID_PATTERN, "CODE-ISSUE-001")
        assert not re.match(CODE_ISSUE_ID_PATTERN, "issue-a3f42bc")

    def test_legacy_patterns_match_old_format(self):
        """Legacy patterns should match old sequential format."""
        assert re.match(LEGACY_SEMANTIC_UNIT_PATTERN, "SU-001")
        assert re.match(LEGACY_ISSUE_PATTERN, "ISSUE-001")
        assert re.match(LEGACY_IMPROVEMENT_PATTERN, "IMPROVE-001")
        assert re.match(LEGACY_CODE_ISSUE_PATTERN, "CODE-ISSUE-001")
        assert re.match(LEGACY_CODE_IMPROVEMENT_PATTERN, "CODE-IMPROVE-001")


class TestIdUniqueness:
    """Tests for ID uniqueness guarantees."""

    def test_batch_uniqueness(self):
        """Large batch of IDs should all be unique."""
        ids = set()
        for _ in range(1000):
            new_id = generate_hash_id("test")
            assert new_id not in ids, f"Duplicate ID generated: {new_id}"
            ids.add(new_id)

    def test_different_generators_produce_different_ids(self):
        """Different generators should produce different IDs."""
        su_id = generate_semantic_unit_id()
        issue_id = generate_issue_id()
        code_issue_id = generate_code_issue_id()

        # Even if hash portions were same, prefixes differ
        assert su_id != issue_id
        assert issue_id != code_issue_id
        assert su_id != code_issue_id
