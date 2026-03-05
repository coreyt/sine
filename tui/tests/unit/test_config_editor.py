"""Tests for ConfigEditorScreen."""

from __future__ import annotations

from lookout_tui.config import TUIConfig
from lookout_tui.screens.config_editor import ConfigEditorScreen

MOCK_MODELS = {
    "gemini": ["gemini-3.1-flash", "gemini-3.1-pro-tools"],
    "anthropic": ["claude-sonnet-4-20250514"],
    "openai": ["gpt-4o"],
}


class TestConfigEditorScreen:
    def test_screen_has_save_binding(self) -> None:
        bindings = {b.key for b in ConfigEditorScreen.BINDINGS}
        assert "s" in bindings

    def test_screen_has_escape_binding(self) -> None:
        bindings = {b.key for b in ConfigEditorScreen.BINDINGS}
        assert "escape" in bindings

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
