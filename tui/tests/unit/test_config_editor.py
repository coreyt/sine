"""Tests for ConfigEditorScreen and TUIConfig catalog management."""

from __future__ import annotations

from lookout_tui.catalog import DEFAULT_FRAMEWORKS, DEFAULT_LANGUAGES
from lookout_tui.config import TUIConfig
from lookout_tui.screens.config_editor import ConfigEditorScreen


class TestConfigEditorScreen:
    def test_screen_has_save_binding(self) -> None:
        bindings = {b.key for b in ConfigEditorScreen.BINDINGS}
        assert "ctrl+s" in bindings

    def test_screen_has_escape_binding(self) -> None:
        bindings = {b.key for b in ConfigEditorScreen.BINDINGS}
        assert "escape" in bindings

    def test_screen_has_add_delete_bindings(self) -> None:
        bindings = {b.key for b in ConfigEditorScreen.BINDINGS}
        assert "a" in bindings
        assert "d" in bindings

    def test_parse_config_values(self) -> None:
        config = TUIConfig(
            llm_model="anthropic/claude-sonnet-4-20250514",
            llm_temperature=0.7,
            llm_max_tokens=8192,
            llm_timeout=60.0,
        )
        assert config.llm_model == "anthropic/claude-sonnet-4-20250514"
        assert config.llm_temperature == 0.7
        assert config.llm_max_tokens == 8192
        assert config.llm_timeout == 60.0

    def test_update_config_values(self) -> None:
        config = TUIConfig()
        config.llm_model = "openai/gpt-4o"
        config.llm_temperature = 0.9
        config.llm_max_tokens = 2048
        config.llm_timeout = 30.0
        assert config.llm_model == "openai/gpt-4o"
        assert config.llm_temperature == 0.9
        assert config.llm_max_tokens == 2048
        assert config.llm_timeout == 30.0

    def test_default_config_values(self) -> None:
        config = TUIConfig()
        assert config.llm_model == "gemini/gemini-3.1-pro-tools"
        assert config.llm_temperature == 0.3
        assert config.llm_max_tokens == 4096
        assert config.llm_timeout == 120.0
        assert config.llm_max_retries == 3


class TestTUIConfigLanguages:
    def test_default_languages_loaded(self) -> None:
        config = TUIConfig()
        assert len(config.languages) == len(DEFAULT_LANGUAGES)

    def test_get_language_names(self) -> None:
        config = TUIConfig()
        names = config.get_language_names()
        assert "python" in names
        assert "typescript" in names

    def test_get_language_versions(self) -> None:
        config = TUIConfig()
        versions = config.get_language_versions("python")
        assert "3.12" in versions
        assert len(versions) >= 3

    def test_add_language(self) -> None:
        config = TUIConfig()
        initial = len(config.languages)
        assert config.add_language("haskell", "9.8")
        assert len(config.languages) == initial + 1
        assert "haskell" in config.get_language_names()
        assert "9.8" in config.get_language_versions("haskell")

    def test_add_language_duplicate(self) -> None:
        config = TUIConfig()
        assert not config.add_language("python", "3.12")

    def test_add_language_no_version(self) -> None:
        config = TUIConfig()
        assert config.add_language("zig")
        assert "zig" in config.get_language_names()

    def test_remove_language(self) -> None:
        config = TUIConfig()
        initial = len(config.languages)
        assert config.remove_language("python", "3.10")
        assert len(config.languages) == initial - 1

    def test_remove_language_not_found(self) -> None:
        config = TUIConfig()
        assert not config.remove_language("cobol")


class TestTUIConfigFrameworks:
    def test_default_frameworks_loaded(self) -> None:
        config = TUIConfig()
        assert len(config.frameworks) == len(DEFAULT_FRAMEWORKS)

    def test_get_framework_names(self) -> None:
        config = TUIConfig()
        names = config.get_framework_names("python")
        assert "django" in names
        assert "fastapi" in names

    def test_get_framework_versions(self) -> None:
        config = TUIConfig()
        versions = config.get_framework_versions("django", "python")
        assert len(versions) >= 2

    def test_add_framework(self) -> None:
        config = TUIConfig()
        initial = len(config.frameworks)
        assert config.add_framework("starlette", "python", "0.37")
        assert len(config.frameworks) == initial + 1
        assert "starlette" in config.get_framework_names("python")

    def test_add_framework_duplicate(self) -> None:
        config = TUIConfig()
        assert not config.add_framework("django", "python", "5.0")

    def test_add_framework_no_version(self) -> None:
        config = TUIConfig()
        assert config.add_framework("httpx", "python")
        assert "httpx" in config.get_framework_names("python")

    def test_remove_framework(self) -> None:
        config = TUIConfig()
        initial = len(config.frameworks)
        assert config.remove_framework("django", "python", "4.2")
        assert len(config.frameworks) == initial - 1

    def test_remove_framework_not_found(self) -> None:
        config = TUIConfig()
        assert not config.remove_framework("nonexistent", "python")
