"""Lookout TUI application."""

from __future__ import annotations

from textual.app import App
from textual.binding import Binding
from textual.events import Resize

from lookout_tui.config import TUIConfig
from lookout_tui.keys import ci
from lookout_tui.screens.batch import BatchScreen
from lookout_tui.screens.patterns import PatternsScreen
from lookout_tui.screens.settings import SettingsScreen


class LookoutApp(App[None]):
    """Main Lookout TUI application."""

    TITLE = "Lookout"
    SUB_TITLE = "Pattern Governance"
    CSS_PATH = "styles/app.tcss"

    BINDINGS = [
        Binding("f1", "help", "Help", priority=True),
        Binding("question_mark", "help", "Help", priority=True, show=False),
        *ci("q", "quit", "Quit", priority=True),
        Binding("1", "switch_screen('patterns')", "Patterns", priority=True),
        Binding("2", "switch_screen('batch')", "Batch", priority=True),
        Binding("3", "switch_screen('settings')", "Settings", priority=True),
    ]

    SCREENS = {
        "patterns": PatternsScreen,
        "batch": BatchScreen,
        "settings": SettingsScreen,
    }

    def __init__(self) -> None:
        super().__init__()
        self.tui_config = TUIConfig()

    def on_mount(self) -> None:
        self.push_screen("patterns")

    def action_help(self) -> None:
        self.notify(
            "Lookout TUI — 1:Patterns 2:Batch 3:Settings ?:Help q:Quit"
        )

    def on_resize(self, event: Resize) -> None:
        """Apply responsive breakpoint CSS classes."""
        cols = event.size.width
        if cols < 80:
            new_bp = "compact"
        elif cols < 120:
            new_bp = "standard"
        elif cols < 160:
            new_bp = "expanded"
        else:
            new_bp = "wide"
        if getattr(self, "_breakpoint", None) != new_bp:
            for cls in ("compact", "standard", "expanded", "wide"):
                self.remove_class(cls)
            self.add_class(new_bp)
            self._breakpoint = new_bp
