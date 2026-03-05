"""Tests for PromptTemplate."""

from __future__ import annotations

from pathlib import Path

import pytest

from lookout_tui.prompts.loader import PromptTemplate


@pytest.fixture
def tmp_prompts(tmp_path: Path) -> Path:
    """Create temporary prompt template files."""
    (tmp_path / "system-prompt-pattern-research.md").write_text(
        "# System Prompt\n\n```\nYou are an expert.\n```\n"
    )
    (tmp_path / "user-prompt-top-level.md").write_text(
        "# Top Level\n\n```\nPattern: {{PATTERN_ID}}\nTitle: {{PATTERN_TITLE}}\n"
        "Hint: {{DESCRIPTION_HINT}}\n```\n"
    )
    (tmp_path / "user-prompt-language-generic.md").write_text(
        "# Language\n\n```\nSpec: {{TOP_LEVEL_SPEC}}\n"
        "Lang: {{LANGUAGE}}\nVer: {{VERSION_CONSTRAINT_OR_SKIP}}\n"
        "ID: {{PATTERN_ID_LOWER}}\n```\n"
    )
    (tmp_path / "user-prompt-language-framework.md").write_text(
        "# Framework\n\n```\nSpec: {{TOP_LEVEL_SPEC}}\n"
        "LangSpec: {{LANGUAGE_GENERIC_SPEC}}\n"
        "Lang: {{LANGUAGE}}\nFW: {{FRAMEWORK}}\n"
        "FWVer: {{FRAMEWORK_VERSION_CONSTRAINT_OR_SKIP}}\n"
        "ID: {{PATTERN_ID_LOWER}}\n```\n"
    )
    return tmp_path


class TestCodeFenceStripping:
    def test_strips_code_fences(self, tmp_prompts: Path) -> None:
        t = PromptTemplate(tmp_prompts)
        result = t.load("system-prompt-pattern-research.md")
        assert result == "You are an expert."
        assert "```" not in result

    def test_no_fences_returns_raw(self, tmp_path: Path) -> None:
        (tmp_path / "no-fences.md").write_text("Just plain text.\nMore text.")
        t = PromptTemplate(tmp_path)
        result = t.load("no-fences.md")
        assert result == "Just plain text.\nMore text."


class TestVariableSubstitution:
    def test_substitutes_variables(self, tmp_prompts: Path) -> None:
        t = PromptTemplate(tmp_prompts)
        result = t.render(
            "user-prompt-top-level.md",
            PATTERN_ID="DI-001",
            PATTERN_TITLE="Dependency Injection",
            DESCRIPTION_HINT="Classes should use DI",
        )
        assert "DI-001" in result
        assert "Dependency Injection" in result
        assert "Classes should use DI" in result
        assert "{{" not in result

    def test_raises_on_unresolved_variables(self, tmp_prompts: Path) -> None:
        t = PromptTemplate(tmp_prompts)
        with pytest.raises(ValueError, match="Unresolved template variables"):
            t.render("user-prompt-top-level.md", PATTERN_ID="X")

    def test_caches_loaded_templates(self, tmp_prompts: Path) -> None:
        t = PromptTemplate(tmp_prompts)
        first = t.load("system-prompt-pattern-research.md")
        second = t.load("system-prompt-pattern-research.md")
        assert first is second


class TestRenderHelpers:
    def test_render_system_prompt(self, tmp_prompts: Path) -> None:
        t = PromptTemplate(tmp_prompts)
        result = t.render_system_prompt()
        assert "expert" in result

    def test_render_top_level(self, tmp_prompts: Path) -> None:
        t = PromptTemplate(tmp_prompts)
        result = t.render_top_level("ARCH-001", "HTTP Resilience", "Wrap HTTP calls")
        assert "ARCH-001" in result
        assert "HTTP Resilience" in result
        assert "Wrap HTTP calls" in result

    def test_render_language_generic(self, tmp_prompts: Path) -> None:
        t = PromptTemplate(tmp_prompts)
        result = t.render_language_generic(
            top_level_spec="approved spec content",
            language="python",
            pattern_id_lower="arch-001",
        )
        assert "approved spec content" in result
        assert "python" in result
        assert "arch-001" in result

    def test_render_language_framework(self, tmp_prompts: Path) -> None:
        t = PromptTemplate(tmp_prompts)
        result = t.render_language_framework(
            top_level_spec="top spec",
            language_generic_spec="lang spec",
            language="python",
            framework="django",
            pattern_id_lower="di-001",
        )
        assert "top spec" in result
        assert "lang spec" in result
        assert "django" in result
        assert "di-001" in result


class TestCodeFenceEdgeCases:
    def test_single_fence_returns_raw(self, tmp_path: Path) -> None:
        (tmp_path / "single-fence.md").write_text("Some text\n```\nMore text")
        t = PromptTemplate(tmp_path)
        result = t.load("single-fence.md")
        # Single fence = raw content
        assert "Some text" in result
        assert "```" in result

    def test_three_fences_takes_outermost(self, tmp_path: Path) -> None:
        content = "# Title\n```\nOuter start\n```python\ninner\n```\nOuter end\n```\n"
        (tmp_path / "multi-fence.md").write_text(content)
        t = PromptTemplate(tmp_path)
        result = t.load("multi-fence.md")
        assert "Outer start" in result
        assert "Outer end" in result

    def test_empty_file(self, tmp_path: Path) -> None:
        (tmp_path / "empty.md").write_text("")
        t = PromptTemplate(tmp_path)
        result = t.load("empty.md")
        assert result == ""


class TestMissingFile:
    def test_raises_on_missing_file(self, tmp_path: Path) -> None:
        t = PromptTemplate(tmp_path)
        with pytest.raises(FileNotFoundError):
            t.load("nonexistent.md")
