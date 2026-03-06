"""Config Editor screen — model selection, LLM settings, and catalog management."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import DataTable, Footer, Header, Input, Label, Static

from lookout_tui.config import TUIConfig
from lookout_tui.keys import ci
from lookout_tui.widgets.input_dialog import InputDialog
from lookout_tui.widgets.model_selector import ModelSelector


class ConfigEditorScreen(Screen[None]):
    """Configuration editor for LLM settings, languages, and frameworks."""

    BINDINGS = [
        Binding("ctrl+s", "save", "Save", key_display="^s"),
        *ci("a", "add_entry", "Add"),
        *ci("d", "delete_entry", "Delete"),
        Binding("escape", "app.go_home", "Home"),
        Binding("f3", "app.go_home", "Home", show=False),
    ]

    def __init__(self) -> None:
        super().__init__()
        self._pending_model: str | None = None
        self._active_table: str | None = None

    def compose(self) -> ComposeResult:
        from lookout_tui.app import LookoutApp

        yield Header()
        yield Static(" Configuration Editor", id="screen-title")

        config = self.app.tui_config if isinstance(self.app, LookoutApp) else None

        with Vertical(id="config-form"):
            # ── LLM settings ──
            yield Label("Model")
            model = config.llm_model if config else TUIConfig().llm_model
            yield ModelSelector(current_model=model, id="config-model-selector")

            with Horizontal(id="config-params"):
                with Vertical():
                    yield Label("Temperature")
                    yield Input(
                        value=str(config.llm_temperature if config else 0.3),
                        id="input-temperature",
                        type="number",
                    )
                with Vertical():
                    yield Label("Max Tokens")
                    yield Input(
                        value=str(config.llm_max_tokens if config else 4096),
                        id="input-max-tokens",
                        type="integer",
                    )
                with Vertical():
                    yield Label("Timeout (s)")
                    yield Input(
                        value=str(config.llm_timeout if config else 120.0),
                        id="input-timeout",
                        type="number",
                    )

            # ── Language catalog ──
            yield Static(" Languages (a: add, d: delete)", id="lang-header")
            lang_table: DataTable[str] = DataTable(id="lang-table")
            lang_table.cursor_type = "row"
            yield lang_table

            # ── Framework catalog ──
            yield Static(" Frameworks (a: add, d: delete)", id="fw-header")
            fw_table: DataTable[str] = DataTable(id="fw-table")
            fw_table.cursor_type = "row"
            yield fw_table

        yield Footer()

    def on_mount(self) -> None:
        self._populate_tables()

    def _populate_tables(self) -> None:
        config = self._get_config()

        # Language table
        lang_table = self.query_one("#lang-table", DataTable)
        lang_table.clear(columns=True)
        lang_table.add_columns("Language", "Version")
        for lang in sorted(config.languages, key=lambda l: (l.name, l.version or "")):
            lang_table.add_row(lang.name, lang.version or "(any)", key=lang.key)

        # Framework table
        fw_table = self.query_one("#fw-table", DataTable)
        fw_table.clear(columns=True)
        fw_table.add_columns("Framework", "Language", "Version")
        for fw in sorted(config.frameworks, key=lambda f: (f.language, f.name, f.version or "")):
            fw_table.add_row(fw.name, fw.language, fw.version or "(any)", key=fw.key)

    def on_data_table_row_highlighted(self, event: DataTable.RowHighlighted) -> None:
        """Track which table is active for add/delete context."""
        table_id = event.data_table.id
        if table_id in ("lang-table", "fw-table"):
            self._active_table = table_id

    def on_model_selector_model_changed(self, event: ModelSelector.ModelChanged) -> None:
        self._pending_model = event.model

    # ── Add / Delete actions ──

    def action_add_entry(self) -> None:
        if self._active_table == "fw-table":
            self._add_framework()
        else:
            self._add_language()

    def action_delete_entry(self) -> None:
        if self._active_table == "fw-table":
            self._delete_framework()
        else:
            self._delete_language()

    def _add_language(self) -> None:
        def _on_result(result: str | None) -> None:
            if not result:
                return
            parts = result.strip().lower().split(maxsplit=1)
            name = parts[0]
            version = parts[1] if len(parts) > 1 else None

            config = self._get_config()
            if config.add_language(name, version):
                self._populate_tables()
                label = f"{name} {version}" if version else name
                self.notify(f"Added language: {label}")
            else:
                self.notify("Language already exists", severity="warning")

        self.app.push_screen(
            InputDialog(
                "Add language (name [version]):",
                placeholder="e.g. python 3.14  or  haskell",
            ),
            _on_result,
        )

    def _delete_language(self) -> None:
        lang_table = self.query_one("#lang-table", DataTable)
        row_key = lang_table.cursor_row
        if row_key < 0:
            self.notify("No language selected", severity="warning")
            return
        row = lang_table.get_row_at(row_key)
        name = str(row[0])
        version = str(row[1]) if row[1] != "(any)" else None

        config = self._get_config()
        if config.remove_language(name, version):
            self._populate_tables()
            label = f"{name} {version}" if version else name
            self.notify(f"Removed language: {label}")
        else:
            self.notify("Language not found", severity="warning")

    def _add_framework(self) -> None:
        config = self._get_config()
        lang_names = config.get_language_names()

        if not lang_names:
            self.notify("Add a language first", severity="warning")
            return

        def _on_result(result: str | None) -> None:
            if not result:
                return
            # Expected format: "language framework [version]"
            parts = result.strip().lower().split()
            if len(parts) < 2:
                self.notify(
                    "Format: language framework [version]",
                    severity="warning",
                )
                return
            language = parts[0]
            fw_name = parts[1]
            version = parts[2] if len(parts) > 2 else None

            if config.add_framework(fw_name, language, version):
                self._populate_tables()
                label = f"{fw_name} {version}" if version else fw_name
                self.notify(f"Added framework: {label} ({language})")
            else:
                self.notify("Framework already exists", severity="warning")

        self.app.push_screen(
            InputDialog(
                "Add framework (language name [version]):",
                placeholder="e.g. python django 5.2  or  go fiber",
            ),
            _on_result,
        )

    def _delete_framework(self) -> None:
        fw_table = self.query_one("#fw-table", DataTable)
        row_key = fw_table.cursor_row
        if row_key < 0:
            self.notify("No framework selected", severity="warning")
            return
        row = fw_table.get_row_at(row_key)
        name = str(row[0])
        language = str(row[1])
        version = str(row[2]) if row[2] != "(any)" else None

        config = self._get_config()
        if config.remove_framework(name, language, version):
            self._populate_tables()
            label = f"{name} {version}" if version else name
            self.notify(f"Removed framework: {label} ({language})")
        else:
            self.notify("Framework not found", severity="warning")

    # ── Save ──

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

    # ── Helpers ──

    def _get_config(self) -> TUIConfig:
        from lookout_tui.app import LookoutApp

        if isinstance(self.app, LookoutApp):
            return self.app.tui_config
        return TUIConfig()
