"""Lookout TUI application."""

from __future__ import annotations

from textual.app import App
from textual.binding import Binding
from textual.events import Resize

from lookout_tui.config import TUIConfig
from lookout_tui.keys import ci
from lookout_tui.screens.batch import BatchGridScreen
from lookout_tui.screens.browser import PatternBrowserScreen
from lookout_tui.screens.config_editor import ConfigEditorScreen
from lookout_tui.screens.dashboard import DashboardScreen
from lookout_tui.screens.generation import GenerationPipelineScreen
from lookout_tui.screens.registry import RegistryScreen


class LookoutApp(App[None]):
    """Main Lookout TUI application."""

    TITLE = "Lookout"
    SUB_TITLE = "Pattern Governance"
    CSS_PATH = "styles/app.tcss"

    BINDINGS = [
        # Tier 1 — Global keys (§2.2)
        Binding("f1", "help", "Help", priority=True),
        Binding("question_mark", "help", "Help", priority=True, show=False),
        Binding("f3", "go_home", "Home", priority=True, show=False),
        *ci("q", "quit", "Quit", priority=True),
        # Tier 3 — Screen mnemonics (§2.2)
        *ci("b", "switch_screen('browser')", "Browser", priority=True),
        *ci("e", "switch_screen('registry')", "Registry", priority=True),
        *ci("g", "switch_screen('generation')", "Generate", priority=True),
        *ci("c", "switch_screen('config')", "Config", priority=True),
        *ci("t", "switch_screen('batch')", "Batch", priority=True),
    ]

    SCREENS = {
        "dashboard": DashboardScreen,
        "browser": PatternBrowserScreen,
        "registry": RegistryScreen,
        "generation": GenerationPipelineScreen,
        "config": ConfigEditorScreen,
        "batch": BatchGridScreen,
    }

    def __init__(self) -> None:
        super().__init__()
        self.tui_config = TUIConfig()

    def on_mount(self) -> None:
        self.push_screen("dashboard")

    def action_go_home(self) -> None:
        """Switch to the dashboard home screen."""
        self.switch_screen("dashboard")

    def action_help(self) -> None:
        self.notify(
            "Lookout TUI — b:Browser e:Registry g:Generate c:Config t:Batch Esc:Home q:Quit"
        )

    def on_resize(self, event: Resize) -> None:
        """Apply responsive breakpoint CSS classes per §1.6."""
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
