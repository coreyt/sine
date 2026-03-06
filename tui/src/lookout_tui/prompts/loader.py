"""Prompt template loader and renderer — delegates to shared lookout.prompts."""

from __future__ import annotations

from pathlib import Path

from lookout.prompts import PromptTemplateLoader


class PromptTemplate(PromptTemplateLoader):
    """TUI-specific prompt template with convenience methods.

    Extends the shared PromptTemplateLoader with domain-specific
    rendering methods for the generation pipeline.
    """

    def __init__(self, prompts_dir: Path) -> None:
        super().__init__(prompts_dir)

    def render_system_prompt(self) -> str:
        """Render the system prompt (no variables needed)."""
        return self.load("system-prompt-pattern-research.md")

    def render_top_level(
        self,
        pattern_id: str,
        pattern_title: str,
        description_hint: str,
    ) -> str:
        """Render the top-level pattern spec user prompt."""
        return self.render(
            "user-prompt-top-level.md",
            PATTERN_ID=pattern_id,
            PATTERN_TITLE=pattern_title,
            DESCRIPTION_HINT=description_hint,
        )

    def render_language_generic(
        self,
        top_level_spec: str,
        language: str,
        version_constraint: str = "[SKIP]",
        pattern_id_lower: str = "",
    ) -> str:
        """Render the language-generic variant user prompt."""
        return self.render(
            "user-prompt-language-generic.md",
            TOP_LEVEL_SPEC=top_level_spec,
            LANGUAGE=language,
            VERSION_CONSTRAINT_OR_SKIP=version_constraint,
            PATTERN_ID_LOWER=pattern_id_lower,
        )

    def render_language_framework(
        self,
        top_level_spec: str,
        language_generic_spec: str,
        language: str,
        framework: str,
        framework_version_constraint: str = "[SKIP]",
        pattern_id_lower: str = "",
    ) -> str:
        """Render the language-framework variant user prompt."""
        return self.render(
            "user-prompt-language-framework.md",
            TOP_LEVEL_SPEC=top_level_spec,
            LANGUAGE_GENERIC_SPEC=language_generic_spec,
            LANGUAGE=language,
            FRAMEWORK=framework,
            FRAMEWORK_VERSION_CONSTRAINT_OR_SKIP=framework_version_constraint,
            PATTERN_ID_LOWER=pattern_id_lower,
        )
