"""Tests for ModelSelector widget."""

from __future__ import annotations

from unittest.mock import patch

from lookout_tui.widgets.model_selector import ModelSelector

MOCK_MODELS = {
    "anthropic": ["claude-sonnet-4-20250514", "claude-haiku-4-5-20251001"],
    "gemini": ["gemini-3.1-flash", "gemini-3.1-pro"],
    "openai": ["gpt-4o", "gpt-4o-mini"],
}

_PATCH_TARGET = "lookout_tui.widgets.model_selector.get_available_models"


class TestModelSelector:
    def test_provider_options_from_models(self) -> None:
        with patch(_PATCH_TARGET, return_value=MOCK_MODELS):
            selector = ModelSelector(current_model="gemini/gemini-3.1-pro")
        providers = [p for p, _ in selector._provider_options]
        assert "gemini" in providers
        assert "anthropic" in providers
        assert "openai" in providers

    def test_models_for_provider(self) -> None:
        with patch(_PATCH_TARGET, return_value=MOCK_MODELS):
            selector = ModelSelector(current_model="gemini/gemini-3.1-pro")
        models = selector._get_models_for_provider("gemini")
        assert "gemini-3.1-pro" in models
        assert "gemini-3.1-flash" in models

    def test_initial_provider_from_model(self) -> None:
        with patch(_PATCH_TARGET, return_value=MOCK_MODELS):
            selector = ModelSelector(
                current_model="anthropic/claude-sonnet-4-20250514",
            )
        assert selector._current_provider == "anthropic"
        assert selector._current_model_name == "claude-sonnet-4-20250514"

    def test_full_model_string(self) -> None:
        with patch(_PATCH_TARGET, return_value=MOCK_MODELS):
            selector = ModelSelector(current_model="openai/gpt-4o")
        assert selector.full_model_string == "openai/gpt-4o"

    def test_default_provider_when_no_slash(self) -> None:
        with patch(_PATCH_TARGET, return_value=MOCK_MODELS):
            selector = ModelSelector(current_model="gemini-3.1-pro")
        # Falls back to first provider
        assert selector._current_provider == "anthropic"
