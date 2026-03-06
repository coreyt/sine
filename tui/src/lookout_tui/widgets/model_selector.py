"""Model selector widget — cascading provider/model dropdowns."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.message import Message
from textual.widget import Widget
from textual.widgets import Select

from lookout_tui.clients.litellm_client import get_available_models


class ModelSelector(Widget):
    """Two cascading Select widgets: provider → model.

    Posts ModelChanged message when the user selects a model.
    """

    class ModelChanged(Message):
        """Emitted when the selected model changes."""

        def __init__(self, model: str) -> None:
            super().__init__()
            self.model = model

    def __init__(
        self,
        current_model: str = "gemini/gemini-3.1-pro-tools",
        id: str | None = None,
    ) -> None:
        super().__init__(id=id)
        self._available = get_available_models()
        self._provider_options = [(p, p) for p in sorted(self._available.keys())]

        # Parse provider/model from current_model
        if "/" in current_model:
            provider, model_name = current_model.split("/", 1)
            if provider in self._available:
                self._current_provider = provider
                self._current_model_name = model_name
            else:
                first = self._provider_options[0][0] if self._provider_options else ""
                self._current_provider = first
                self._current_model_name = ""
        else:
            self._current_provider = self._provider_options[0][0] if self._provider_options else ""
            self._current_model_name = current_model

    @property
    def full_model_string(self) -> str:
        """Return the full provider/model string."""
        return f"{self._current_provider}/{self._current_model_name}"

    def _get_models_for_provider(self, provider: str) -> list[str]:
        """Get sorted model list for a provider."""
        return self._available.get(provider, [])

    def compose(self) -> ComposeResult:
        with Horizontal():
            providers = sorted(self._available.keys())
            yield Select[str](
                options=[(p, p) for p in providers],
                value=self._current_provider if self._current_provider in providers else Select.BLANK,
                allow_blank=not providers,
                id="provider-select",
                prompt="Provider",
            )
            models = self._get_models_for_provider(self._current_provider)
            if self._current_model_name in models:
                model_value = self._current_model_name
            elif models:
                model_value = models[0]
                self._current_model_name = model_value
            else:
                model_value = Select.BLANK
            yield Select[str](
                options=[(m, m) for m in models],
                value=model_value,
                allow_blank=not models,
                id="model-select",
                prompt="Model",
            )

    def on_select_changed(self, event: Select.Changed) -> None:
        """Handle provider or model selection changes."""
        select_id = event.select.id
        if select_id == "provider-select" and event.value != Select.BLANK:
            self._current_provider = str(event.value)
            models = self._get_models_for_provider(self._current_provider)
            model_select = self.query_one("#model-select", Select)
            model_select.set_options([(m, m) for m in models])
            if models:
                self._current_model_name = models[0]
                model_select.value = models[0]
                self.post_message(self.ModelChanged(self.full_model_string))
        elif select_id == "model-select" and event.value != Select.BLANK:
            self._current_model_name = str(event.value)
            self.post_message(self.ModelChanged(self.full_model_string))
