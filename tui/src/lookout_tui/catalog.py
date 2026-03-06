"""Default language and framework catalog with version awareness.

Provides curated lists of popular languages (with major.minor versions)
and frameworks per language. Users can customize these via the Config screen.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class LanguageEntry:
    """A language with optional version constraint."""

    name: str
    version: str | None = None  # major.minor, e.g. "3.12"

    @property
    def display(self) -> str:
        return f"{self.name} {self.version}" if self.version else self.name

    @property
    def key(self) -> str:
        """Unique key for config storage."""
        return f"{self.name}:{self.version}" if self.version else self.name


@dataclass(frozen=True)
class FrameworkEntry:
    """A framework with language affinity and optional version."""

    name: str
    language: str  # which language this framework belongs to
    version: str | None = None

    @property
    def display(self) -> str:
        return f"{self.name} {self.version}" if self.version else self.name

    @property
    def key(self) -> str:
        return f"{self.name}:{self.version}" if self.version else self.name


# ── Default languages (top ~30, with notable version splits) ──────────

DEFAULT_LANGUAGES: list[LanguageEntry] = [
    # Python
    LanguageEntry("python", "3.10"),
    LanguageEntry("python", "3.11"),
    LanguageEntry("python", "3.12"),
    LanguageEntry("python", "3.13"),
    # TypeScript
    LanguageEntry("typescript", "5.0"),
    LanguageEntry("typescript", "5.2"),
    LanguageEntry("typescript", "5.4"),
    LanguageEntry("typescript", "5.6"),
    LanguageEntry("typescript", "5.8"),
    # JavaScript
    LanguageEntry("javascript", "ES2022"),
    LanguageEntry("javascript", "ES2023"),
    LanguageEntry("javascript", "ES2024"),
    # Java
    LanguageEntry("java", "11"),
    LanguageEntry("java", "17"),
    LanguageEntry("java", "21"),
    # C#
    LanguageEntry("csharp", "10"),
    LanguageEntry("csharp", "11"),
    LanguageEntry("csharp", "12"),
    LanguageEntry("csharp", "13"),
    # Go
    LanguageEntry("go", "1.21"),
    LanguageEntry("go", "1.22"),
    LanguageEntry("go", "1.23"),
    # Kotlin
    LanguageEntry("kotlin", "1.9"),
    LanguageEntry("kotlin", "2.0"),
    LanguageEntry("kotlin", "2.1"),
    # Rust
    LanguageEntry("rust"),
    # Swift
    LanguageEntry("swift", "5.9"),
    LanguageEntry("swift", "5.10"),
    LanguageEntry("swift", "6.0"),
    # Ruby
    LanguageEntry("ruby", "3.2"),
    LanguageEntry("ruby", "3.3"),
    # PHP
    LanguageEntry("php", "8.2"),
    LanguageEntry("php", "8.3"),
    LanguageEntry("php", "8.4"),
    # Scala
    LanguageEntry("scala", "2.13"),
    LanguageEntry("scala", "3.3"),
    # Dart
    LanguageEntry("dart", "3.2"),
    LanguageEntry("dart", "3.3"),
    # Elixir
    LanguageEntry("elixir", "1.16"),
    LanguageEntry("elixir", "1.17"),
    # C++
    LanguageEntry("cpp", "17"),
    LanguageEntry("cpp", "20"),
    LanguageEntry("cpp", "23"),
    # R
    LanguageEntry("r", "4.3"),
    LanguageEntry("r", "4.4"),
]


# ── Default frameworks (top ~20 per language) ─────────────────────────

DEFAULT_FRAMEWORKS: list[FrameworkEntry] = [
    # Python frameworks
    FrameworkEntry("django", "python", "4.2"),
    FrameworkEntry("django", "python", "5.0"),
    FrameworkEntry("django", "python", "5.1"),
    FrameworkEntry("fastapi", "python", "0.110"),
    FrameworkEntry("fastapi", "python", "0.115"),
    FrameworkEntry("flask", "python", "3.0"),
    FrameworkEntry("flask", "python", "3.1"),
    FrameworkEntry("sqlalchemy", "python", "2.0"),
    FrameworkEntry("pydantic", "python", "2.0"),
    FrameworkEntry("celery", "python", "5.3"),
    FrameworkEntry("pytest", "python", "8.0"),
    # TypeScript / JavaScript frameworks
    FrameworkEntry("react", "typescript", "18"),
    FrameworkEntry("react", "typescript", "19"),
    FrameworkEntry("next.js", "typescript", "14"),
    FrameworkEntry("next.js", "typescript", "15"),
    FrameworkEntry("angular", "typescript", "17"),
    FrameworkEntry("angular", "typescript", "18"),
    FrameworkEntry("angular", "typescript", "19"),
    FrameworkEntry("vue", "typescript", "3.4"),
    FrameworkEntry("vue", "typescript", "3.5"),
    FrameworkEntry("nest.js", "typescript", "10"),
    FrameworkEntry("express", "javascript", "4.18"),
    FrameworkEntry("express", "javascript", "5.0"),
    FrameworkEntry("react", "javascript", "18"),
    FrameworkEntry("react", "javascript", "19"),
    # Java frameworks
    FrameworkEntry("spring-boot", "java", "3.2"),
    FrameworkEntry("spring-boot", "java", "3.3"),
    FrameworkEntry("spring-boot", "java", "3.4"),
    FrameworkEntry("quarkus", "java", "3.8"),
    FrameworkEntry("micronaut", "java", "4.3"),
    FrameworkEntry("jakarta-ee", "java", "10"),
    # C# frameworks
    FrameworkEntry("asp.net-core", "csharp", "8.0"),
    FrameworkEntry("asp.net-core", "csharp", "9.0"),
    FrameworkEntry("entity-framework", "csharp", "8.0"),
    FrameworkEntry("entity-framework", "csharp", "9.0"),
    FrameworkEntry("blazor", "csharp", "8.0"),
    # Go frameworks
    FrameworkEntry("gin", "go", "1.9"),
    FrameworkEntry("gin", "go", "1.10"),
    FrameworkEntry("echo", "go", "4.11"),
    FrameworkEntry("echo", "go", "4.12"),
    FrameworkEntry("fiber", "go", "2.52"),
    # Kotlin frameworks
    FrameworkEntry("ktor", "kotlin", "2.3"),
    FrameworkEntry("spring-boot", "kotlin", "3.3"),
    FrameworkEntry("exposed", "kotlin", "0.50"),
    # Rust frameworks
    FrameworkEntry("actix-web", "rust", "4.5"),
    FrameworkEntry("axum", "rust", "0.7"),
    FrameworkEntry("tokio", "rust", "1.36"),
    # Swift frameworks
    FrameworkEntry("swiftui", "swift"),
    FrameworkEntry("vapor", "swift", "4.92"),
    # Ruby frameworks
    FrameworkEntry("rails", "ruby", "7.1"),
    FrameworkEntry("rails", "ruby", "7.2"),
    FrameworkEntry("rails", "ruby", "8.0"),
    FrameworkEntry("sinatra", "ruby", "4.0"),
    # PHP frameworks
    FrameworkEntry("laravel", "php", "10"),
    FrameworkEntry("laravel", "php", "11"),
    FrameworkEntry("symfony", "php", "6.4"),
    FrameworkEntry("symfony", "php", "7.1"),
    # Scala frameworks
    FrameworkEntry("play", "scala", "3.0"),
    FrameworkEntry("akka", "scala", "2.9"),
    FrameworkEntry("zio", "scala", "2.0"),
    # Dart frameworks
    FrameworkEntry("flutter", "dart", "3.19"),
    FrameworkEntry("flutter", "dart", "3.22"),
    # Elixir frameworks
    FrameworkEntry("phoenix", "elixir", "1.7"),
]


def get_language_names(languages: list[LanguageEntry]) -> list[str]:
    """Get sorted unique language base names."""
    return sorted({lang.name for lang in languages})


def get_frameworks_for_language(
    language: str, frameworks: list[FrameworkEntry]
) -> list[FrameworkEntry]:
    """Get frameworks that belong to a specific language."""
    return [fw for fw in frameworks if fw.language == language]


def get_framework_names_for_language(
    language: str, frameworks: list[FrameworkEntry]
) -> list[str]:
    """Get sorted unique framework base names for a language."""
    return sorted({fw.name for fw in frameworks if fw.language == language})
