"""Prompt template loader and renderer."""

from __future__ import annotations

import re
from pathlib import Path


class PromptTemplate:
    """Loads and renders prompt templates from markdown files.

    Templates use {{VARIABLE}} placeholders and wrap content in code fences.
    The loader extracts content between the first ``` and last ``` markers.
    """

    def __init__(self, prompts_dir: Path) -> None:
        self.prompts_dir = prompts_dir
        self._cache: dict[str, str] = {}

    def load(self, filename: str) -> str:
        """Load a prompt template file and extract content from code fences.

        Args:
            filename: Template filename (e.g., "system-prompt-pattern-research.md")

        Returns:
            Raw template content with code fences stripped.

        Raises:
            FileNotFoundError: If template file doesn't exist.
        """
        if filename in self._cache:
            return self._cache[filename]

        filepath = self.prompts_dir / filename
        raw = filepath.read_text()
        content = self._strip_code_fences(raw)
        self._cache[filename] = content
        return content

    def render(self, filename: str, **variables: str) -> str:
        """Load a template and substitute {{VARIABLE}} placeholders.

        Args:
            filename: Template filename.
            **variables: Key-value pairs for substitution. Keys should match
                placeholder names (e.g., PATTERN_ID="ARCH-001").

        Returns:
            Rendered template string.

        Raises:
            ValueError: If template contains unresolved placeholders.
        """
        template = self.load(filename)
        result = template
        for key, value in variables.items():
            result = result.replace(f"{{{{{key}}}}}", value)

        # Check for unresolved placeholders
        unresolved = re.findall(r"\{\{([A-Z0-9_]+)\}\}", result)
        if unresolved:
            raise ValueError(f"Unresolved template variables: {', '.join(unresolved)}")

        return result

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

    @staticmethod
    def _strip_code_fences(raw: str) -> str:
        """Extract content between first and last ``` markers."""
        lines = raw.split("\n")
        fence_indices: list[int] = []
        for i, line in enumerate(lines):
            if line.strip().startswith("```"):
                fence_indices.append(i)

        if len(fence_indices) >= 2:
            start = fence_indices[0] + 1
            end = fence_indices[-1]
            return "\n".join(lines[start:end])

        return raw
