"""Validation Dashboard screen — scaffold."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.binding import Binding
from textual.screen import Screen
from textual.widgets import Footer, Header, Static


class ValidationDashboardScreen(Screen[None]):
    """Validation dashboard — coming soon."""

    BINDINGS = [
        Binding("escape", "app.go_home", "Home"),
    ]

    def compose(self) -> ComposeResult:
        yield Header()
        yield Static(" Validation Dashboard\n\n  Coming soon.", id="placeholder")
        yield Footer()
