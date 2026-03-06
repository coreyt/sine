"""Tests for the language/framework catalog."""

from __future__ import annotations

from lookout_tui.catalog import (
    DEFAULT_FRAMEWORKS,
    DEFAULT_LANGUAGES,
    FrameworkEntry,
    LanguageEntry,
    get_framework_names_for_language,
    get_frameworks_for_language,
    get_language_names,
)


class TestLanguageEntry:
    def test_display_with_version(self) -> None:
        entry = LanguageEntry("python", "3.12")
        assert entry.display == "python 3.12"

    def test_display_without_version(self) -> None:
        entry = LanguageEntry("rust")
        assert entry.display == "rust"

    def test_key_with_version(self) -> None:
        entry = LanguageEntry("python", "3.12")
        assert entry.key == "python:3.12"

    def test_key_without_version(self) -> None:
        entry = LanguageEntry("rust")
        assert entry.key == "rust"

    def test_equality(self) -> None:
        a = LanguageEntry("python", "3.12")
        b = LanguageEntry("python", "3.12")
        assert a == b

    def test_inequality_version(self) -> None:
        a = LanguageEntry("python", "3.12")
        b = LanguageEntry("python", "3.13")
        assert a != b


class TestFrameworkEntry:
    def test_display_with_version(self) -> None:
        entry = FrameworkEntry("django", "python", "5.0")
        assert entry.display == "django 5.0"

    def test_display_without_version(self) -> None:
        entry = FrameworkEntry("swiftui", "swift")
        assert entry.display == "swiftui"

    def test_key_with_version(self) -> None:
        entry = FrameworkEntry("django", "python", "5.0")
        assert entry.key == "django:5.0"

    def test_equality(self) -> None:
        a = FrameworkEntry("django", "python", "5.0")
        b = FrameworkEntry("django", "python", "5.0")
        assert a == b


class TestDefaultCatalog:
    def test_has_languages(self) -> None:
        assert len(DEFAULT_LANGUAGES) >= 30

    def test_has_frameworks(self) -> None:
        assert len(DEFAULT_FRAMEWORKS) >= 40

    def test_python_has_versions(self) -> None:
        python_entries = [l for l in DEFAULT_LANGUAGES if l.name == "python"]
        assert len(python_entries) >= 3
        versions = [l.version for l in python_entries]
        assert "3.12" in versions

    def test_csharp_has_multiple_versions(self) -> None:
        csharp = [l for l in DEFAULT_LANGUAGES if l.name == "csharp"]
        assert len(csharp) >= 3

    def test_typescript_has_multiple_versions(self) -> None:
        ts = [l for l in DEFAULT_LANGUAGES if l.name == "typescript"]
        assert len(ts) >= 4


class TestCatalogHelpers:
    def test_get_language_names(self) -> None:
        names = get_language_names(DEFAULT_LANGUAGES)
        assert "python" in names
        assert "typescript" in names
        assert "java" in names
        # Should be deduplicated
        assert len(names) == len(set(names))

    def test_get_frameworks_for_language(self) -> None:
        python_fws = get_frameworks_for_language("python", DEFAULT_FRAMEWORKS)
        assert len(python_fws) >= 5
        assert all(fw.language == "python" for fw in python_fws)

    def test_get_framework_names_for_language(self) -> None:
        names = get_framework_names_for_language("python", DEFAULT_FRAMEWORKS)
        assert "django" in names
        assert "fastapi" in names
        # Should be deduplicated
        assert len(names) == len(set(names))

    def test_no_frameworks_for_unknown_language(self) -> None:
        fws = get_frameworks_for_language("cobol", DEFAULT_FRAMEWORKS)
        assert fws == []
