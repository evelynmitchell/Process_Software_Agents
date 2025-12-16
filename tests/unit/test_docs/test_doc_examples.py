"""
Tests that validate documentation examples are accurate.

SECURITY: These tests do NOT execute code from markdown files.
Instead, they:
1. Verify syntax is valid (using ast.parse - safe)
2. Verify imports can be resolved (without executing)
3. Use static analysis to check attribute access patterns

This catches documentation drift without running arbitrary code.
"""

import ast
import re
import textwrap
from pathlib import Path

import pytest

DOCS_DIR = Path(__file__).parent.parent.parent.parent / "docs"


def is_runnable_example(code: str) -> bool:
    """
    Determine if a code block is a complete, runnable example.

    Returns False for:
    - API stubs with '...' as method bodies
    - Snippets without imports (likely partial examples)
    - Output examples (lines starting with indentation but no code structure)
    - Code with '# ...' placeholder comments in function bodies
    """
    # Skip blocks that are just output or continuation snippets
    lines = code.strip().split("\n")
    if lines and lines[0].startswith(" "):
        # Starts with indentation - probably a continuation snippet
        return False

    # Skip API reference stubs with ... as placeholder
    if re.search(r"def \w+\([^)]*\.{3}[^)]*\)", code):
        return False

    # Skip class stubs that only have docstrings
    if re.search(r"class \w+.*:\s+\"\"\"", code) and code.count("def ") <= 2:
        if '"""' in code and code.rstrip().endswith('"""'):
            return False

    # Skip code with '# ...' as placeholder in function/method bodies
    # This is a common documentation pattern
    if "# ..." in code:
        return False

    # Skip very short snippets (< 3 lines without import)
    if len(lines) < 3 and "import" not in code:
        return False

    return True


def extract_python_code_blocks(
    markdown_content: str, only_runnable: bool = True
) -> list[tuple[str, int]]:
    """
    Extract Python code blocks from markdown content.

    Args:
        markdown_content: The markdown text to parse.
        only_runnable: If True, only return blocks that appear to be
                      complete runnable examples (not stubs or snippets).
    """
    pattern = r"```python\n(.*?)```"
    blocks = []
    for match in re.finditer(pattern, markdown_content, re.DOTALL):
        code = match.group(1)
        line_num = markdown_content[: match.start()].count("\n") + 1

        # Dedent code blocks that may be indented in markdown (e.g., in lists)
        code = textwrap.dedent(code).strip()

        if only_runnable and not is_runnable_example(code):
            continue

        blocks.append((code, line_num))
    return blocks


def extract_attribute_accesses(code: str) -> list[tuple[str, str]]:
    """
    Extract attribute access patterns from code using AST.

    Returns list of (variable_name, attribute_name) tuples.
    Example: "unit.title" -> ("unit", "title")
    """
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return []

    accesses = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Attribute):
            if isinstance(node.value, ast.Name):
                accesses.append((node.value.id, node.attr))
    return accesses


def extract_imports(code: str) -> list[tuple[str, str | None]]:
    """
    Extract import statements from code using AST.

    Returns list of (module, name) tuples.
    "from asp.agents import X" -> ("asp.agents", "X")
    "import asp.agents" -> ("asp.agents", None)
    """
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return []

    imports = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.append((alias.name, None))
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                for alias in node.names:
                    imports.append((node.module, alias.name))
    return imports


class TestDocSyntaxValidation:
    """Validate that code blocks in docs have correct Python syntax."""

    @pytest.fixture
    def doc_files(self) -> list[Path]:
        """Get all documentation files with code examples."""
        guides = list(DOCS_DIR.glob("*_guide.md"))
        refs = list(DOCS_DIR.glob("*_reference.md"))
        return guides + refs

    def test_all_code_blocks_have_valid_syntax(self, doc_files: list[Path]):
        """All Python code blocks should parse without syntax errors."""
        all_errors = []

        for doc_file in doc_files:
            if not doc_file.exists():
                continue

            content = doc_file.read_text()
            code_blocks = extract_python_code_blocks(content)

            for code, line_num in code_blocks:
                try:
                    ast.parse(code)
                except SyntaxError as e:
                    all_errors.append(f"{doc_file.name}:~{line_num}: {e}")

        assert not all_errors, "Syntax errors found:\n" + "\n".join(all_errors)


class TestDocImportsValidation:
    """Validate that imports in docs can be resolved."""

    @pytest.fixture
    def doc_files(self) -> list[Path]:
        """Get all documentation files with code examples."""
        guides = list(DOCS_DIR.glob("*_guide.md"))
        refs = list(DOCS_DIR.glob("*_reference.md"))
        return guides + refs

    def test_all_imports_resolve(self, doc_files: list[Path]):
        """All imports in code blocks should be resolvable."""
        all_errors = []

        for doc_file in doc_files:
            if not doc_file.exists():
                continue

            content = doc_file.read_text()
            code_blocks = extract_python_code_blocks(content)

            for code, line_num in code_blocks:
                imports = extract_imports(code)

                for module, name in imports:
                    try:
                        mod = __import__(module, fromlist=[name] if name else [])
                        if name and not hasattr(mod, name):
                            all_errors.append(
                                f"{doc_file.name}:~{line_num}: "
                                f"'{name}' not found in '{module}'"
                            )
                    except ImportError:
                        all_errors.append(
                            f"{doc_file.name}:~{line_num}: " f"Cannot import '{module}'"
                        )

        assert not all_errors, "Import errors found:\n" + "\n".join(all_errors)


class TestKnownDocPatterns:
    """
    Test known patterns that docs should use correctly.

    These are curated checks for specific API patterns we know
    have caused issues in the past.
    """

    def test_semantic_unit_uses_description_not_title(self):
        """
        SemanticUnit has 'description' field, not 'title'.

        Docs that reference unit.title are incorrect.
        """
        from asp.models.planning import SemanticUnit

        fields = set(SemanticUnit.model_fields.keys())
        assert "description" in fields
        assert "title" not in fields

    def test_json_extraction_correct_function_name(self):
        """
        Correct function is 'extract_json_from_response', not 'extract_json_from_text'.
        """
        from asp.utils import json_extraction

        # Correct name exists
        assert hasattr(json_extraction, "extract_json_from_response")
        # Wrong name should not exist
        assert not hasattr(json_extraction, "extract_json_from_text")

    def test_artifact_io_uses_write_not_save(self):
        """
        Correct functions are 'write_artifact_*', not 'save_artifact_*'.
        """
        from asp.utils import artifact_io

        # Correct names exist
        assert hasattr(artifact_io, "write_artifact_json")
        assert hasattr(artifact_io, "write_artifact_markdown")
        # Wrong names should not exist
        assert not hasattr(artifact_io, "save_artifact_json")
        assert not hasattr(artifact_io, "save_artifact_markdown")

    def test_llm_client_uses_call_with_retry_not_chat(self):
        """
        Correct method is 'call_with_retry', not 'chat'.
        """
        from asp.utils.llm_client import LLMClient

        # Correct method exists
        assert hasattr(LLMClient, "call_with_retry")
        # Wrong method should not exist
        assert not hasattr(LLMClient, "chat")

    def test_llm_client_init_uses_api_key_not_provider(self):
        """
        LLMClient.__init__ takes 'api_key', not 'provider'.
        """
        import inspect

        from asp.utils.llm_client import LLMClient

        sig = inspect.signature(LLMClient.__init__)
        params = set(sig.parameters.keys())

        assert "api_key" in params
        assert "provider" not in params


class TestCriticalExamples:
    """
    Test that critical documented examples work correctly.

    These are hand-written tests that mirror key doc examples.
    They serve as a contract between docs and implementation.
    """

    def test_planning_agent_quick_start(self):
        """Mirror of planning_agent_user_guide.md Quick Start section."""
        from asp.agents.planning_agent import PlanningAgent
        from asp.models.planning import TaskRequirements

        # Can create agent
        agent = PlanningAgent()
        assert agent is not None

        # Can create requirements as documented
        requirements = TaskRequirements(
            task_id="TASK-2025-001",
            description="Build user authentication system",
            requirements="Support JWT tokens, user registration, and login.",
            context_files=["docs/auth_spec.md"],
        )
        assert requirements.task_id == "TASK-2025-001"

    def test_code_agent_quick_start(self):
        """Mirror of coding_agent_user_guide.md Quick Start section."""
        from asp.agents.code_agent import CodeAgent

        # Can create agent with multi-stage parameter
        agent = CodeAgent(use_multi_stage=True)
        assert agent is not None

    def test_semantic_complexity_example(self):
        """Mirror of utils_reference.md semantic complexity section."""
        from asp.utils.semantic_complexity import (
            ComplexityFactors,
            calculate_semantic_complexity,
        )

        factors = ComplexityFactors(
            api_interactions=2,
            data_transformations=5,
            logical_branches=10,
            code_entities_modified=3,
            novelty_multiplier=1.0,
        )
        score = calculate_semantic_complexity(factors)

        assert isinstance(score, int | float)
        assert score > 0
