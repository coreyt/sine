"""Shared prompt template loader and renderer."""

from __future__ import annotations

import re
from pathlib import Path


class PromptTemplateLoader:
    """Load and render prompt templates from markdown files.

    Templates use {{VARIABLE}} placeholders. Content between
    first and last ``` markers is extracted.
    """

    def __init__(self, prompts_dir: Path | None = None) -> None:
        if prompts_dir is None:
            prompts_dir = Path(__file__).resolve().parents[2] / "docs" / "prompts"
        self.prompts_dir = prompts_dir
        self._cache: dict[str, str] = {}

    def load(self, filename: str) -> str:
        """Load a prompt template, stripping code fences."""
        if filename in self._cache:
            return self._cache[filename]

        filepath = self.prompts_dir / filename
        if not filepath.exists():
            raise FileNotFoundError(f"Template not found: {filepath}")

        raw = filepath.read_text()
        content = self._strip_code_fences(raw)
        self._cache[filename] = content
        return content

    def render(self, filename: str, **variables: str) -> str:
        """Load template and substitute {{VARIABLE}} placeholders."""
        template = self.load(filename)
        result = template
        for key, value in variables.items():
            result = result.replace(f"{{{{{key}}}}}", value)

        unresolved = re.findall(r"\{\{([A-Z0-9_]+)\}\}", result)
        if unresolved:
            raise ValueError(f"Unresolved template variables: {', '.join(unresolved)}")
        return result

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
