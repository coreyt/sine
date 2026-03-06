"""Config Editor screen — model selection and LLM settings."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Vertical
from textual.screen import Screen
from textual.widgets import Footer, Header, Input, Label, Static

from lookout_tui.widgets.model_selector import ModelSelector


class ConfigEditorScreen(Screen[None]):
    """Configuration editor for LLM settings."""

    BINDINGS = [
        Binding("ctrl+s", "save", "Save", key_display="^s"),
        Binding("escape", "app.go_home", "Home"),
        Binding("f3", "app.go_home", "Home", show=False),
    ]

    def __init__(self) -> None:
        super().__init__()
        self._pending_model: str | None = None

    def compose(self) -> ComposeResult:
        from lookout_tui.app import LookoutApp

        yield Header()
        yield Static(" Configuration Editor", id="screen-title")

        config = self.app.tui_config if isinstance(self.app, LookoutApp) else None

        with Vertical(id="config-form"):
            yield Label("Model")
            model = config.llm_model if config else "gemini/gemini-3.1-pro-tools"
            yield ModelSelector(current_model=model, id="config-model-selector")

            yield Label("Temperature")
            yield Input(
                value=str(config.llm_temperature if config else 0.3),
                id="input-temperature",
                type="number",
            )

            yield Label("Max Tokens")
            yield Input(
                value=str(config.llm_max_tokens if config else 4096),
                id="input-max-tokens",
                type="integer",
            )

            yield Label("Timeout (seconds)")
            yield Input(
                value=str(config.llm_timeout if config else 120.0),
                id="input-timeout",
                type="number",
            )

        yield Footer()

    def on_model_selector_model_changed(self, event: ModelSelector.ModelChanged) -> None:
        """Track model changes for save."""
        self._pending_model = event.model

    def action_save(self) -> None:
        """Write settings back to app config (session-only)."""
        from lookout_tui.app import LookoutApp

        if not isinstance(self.app, LookoutApp):
            return

        config = self.app.tui_config

        if self._pending_model is not None:
            config.llm_model = self._pending_model

        try:
            temp_input = self.query_one("#input-temperature", Input)
            config.llm_temperature = float(temp_input.value)
        except ValueError:
            pass

        try:
            tokens_input = self.query_one("#input-max-tokens", Input)
            config.llm_max_tokens = int(tokens_input.value)
        except ValueError:
            pass

        try:
            timeout_input = self.query_one("#input-timeout", Input)
            config.llm_timeout = float(timeout_input.value)
        except ValueError:
            pass

        self.notify("Settings saved (session only)")
