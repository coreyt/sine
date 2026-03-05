"""Lookout TUI application."""

from __future__ import annotations

from textual.app import App
from textual.binding import Binding

from lookout_tui.config import TUIConfig
from lookout_tui.screens.browser import PatternBrowserScreen
from lookout_tui.screens.config_editor import ConfigEditorScreen
from lookout_tui.screens.generation import GenerationPipelineScreen


class LookoutApp(App[None]):
    """Main Lookout TUI application."""

    TITLE = "Lookout"
    SUB_TITLE = "Pattern Governance"
    CSS_PATH = "styles/app.tcss"

    BINDINGS = [
        Binding("b", "switch_screen('browser')", "Browser", priority=True),
        Binding("g", "switch_screen('generation')", "Generate", priority=True),
        Binding("c", "switch_screen('config')", "Config", priority=True),
        Binding("q", "quit", "Quit", priority=True),
    ]

    SCREENS = {
        "browser": PatternBrowserScreen,
        "generation": GenerationPipelineScreen,
        "config": ConfigEditorScreen,
    }

    def __init__(self) -> None:
        super().__init__()
        self.tui_config = TUIConfig()

    def on_mount(self) -> None:
        self.push_screen("browser")
