"""Coverage Matrix screen — scaffold."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.binding import Binding
from textual.screen import Screen
from textual.widgets import Footer, Header, Static


class CoverageMatrixScreen(Screen[None]):
    """Coverage matrix — coming soon."""

    BINDINGS = [
        Binding("escape", "app.pop_screen", "Back"),
    ]

    def compose(self) -> ComposeResult:
        yield Header()
        yield Static(" Coverage Matrix\n\n  Coming soon.", id="placeholder")
        yield Footer()
