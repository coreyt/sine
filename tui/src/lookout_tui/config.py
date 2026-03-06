"""TUI configuration settings."""

from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel, Field

from lookout_tui.catalog import (
    DEFAULT_FRAMEWORKS,
    DEFAULT_LANGUAGES,
    FrameworkEntry,
    LanguageEntry,
)


class TUIConfig(BaseModel):
    """Configuration for the Lookout TUI."""

    llm_model: str = Field(
        default="gemini/gemini-3.1-pro",
        description="LLM model string (provider/model format for litellm)",
    )
    llm_temperature: float = Field(
        default=0.3,
        description="Temperature for LLM generation",
    )
    llm_max_tokens: int = Field(
        default=4096,
        description="Max tokens for LLM responses",
    )
    llm_timeout: float = Field(
        default=120.0,
        description="Timeout in seconds for LLM calls",
    )
    llm_max_retries: int = Field(
        default=3,
        description="Max retry attempts for transient LLM errors",
    )
    prompts_dir: Path = Field(
        default=Path("docs/prompts"),
        description="Directory containing prompt template files",
    )
    index_path: Path = Field(
        default=Path(".lookout-index.json"),
        description="Path to write the pattern index JSON",
    )
    patterns_dir: Path = Field(
        default=Path(".lookout-patterns"),
        description="User patterns directory",
    )

    # Language and framework catalog (session-editable)
    languages: list[LanguageEntry] = Field(default_factory=lambda: list(DEFAULT_LANGUAGES))
    frameworks: list[FrameworkEntry] = Field(default_factory=lambda: list(DEFAULT_FRAMEWORKS))

    model_config = {"arbitrary_types_allowed": True}

    # ── Language helpers ──────────────────────────────────────────

    def get_language_names(self) -> list[str]:
        """Get sorted unique language base names."""
        return sorted({lang.name for lang in self.languages})

    def get_language_versions(self, name: str) -> list[str]:
        """Get sorted versions for a language name."""
        versions = [lang.version for lang in self.languages if lang.name == name and lang.version]
        return sorted(versions)

    def get_language_entries(self, name: str) -> list[LanguageEntry]:
        """Get all entries for a language name."""
        return [lang for lang in self.languages if lang.name == name]

    def add_language(self, name: str, version: str | None = None) -> bool:
        """Add a language entry. Returns False if already exists."""
        entry = LanguageEntry(name=name.lower(), version=version)
        if entry in self.languages:
            return False
        self.languages.append(entry)
        return True

    def remove_language(self, name: str, version: str | None = None) -> bool:
        """Remove a language entry. Returns False if not found."""
        entry = LanguageEntry(name=name.lower(), version=version)
        try:
            self.languages.remove(entry)
            return True
        except ValueError:
            return False

    # ── Framework helpers ─────────────────────────────────────────

    def get_framework_names(self, language: str) -> list[str]:
        """Get sorted unique framework names for a language."""
        return sorted({fw.name for fw in self.frameworks if fw.language == language})

    def get_framework_versions(self, name: str, language: str) -> list[str]:
        """Get sorted versions for a framework under a language."""
        versions = [
            fw.version
            for fw in self.frameworks
            if fw.name == name and fw.language == language and fw.version
        ]
        return sorted(versions)

    def add_framework(
        self, name: str, language: str, version: str | None = None
    ) -> bool:
        """Add a framework entry. Returns False if already exists."""
        entry = FrameworkEntry(name=name.lower(), language=language.lower(), version=version)
        if entry in self.frameworks:
            return False
        self.frameworks.append(entry)
        return True

    def remove_framework(
        self, name: str, language: str, version: str | None = None
    ) -> bool:
        """Remove a framework entry. Returns False if not found."""
        entry = FrameworkEntry(name=name.lower(), language=language.lower(), version=version)
        try:
            self.frameworks.remove(entry)
            return True
        except ValueError:
            return False
