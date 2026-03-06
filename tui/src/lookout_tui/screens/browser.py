"""Pattern Browser screen."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import DataTable, Footer, Header, Input, Static

from lookout_tui.index.builder import build_index
from lookout_tui.index.models import PatternIndex, PatternIndexEntry
from lookout_tui.keys import ci
from lookout_tui.widgets.pattern_detail import PatternDetailPanel
from lookout_tui.widgets.pattern_table import PatternTable


class PatternBrowserScreen(Screen[None]):
    """Browse and inspect patterns."""

    BINDINGS = [
        Binding("slash", "focus_filter", "Filter", key_display="/"),
        *ci("r", "rebuild_index", "Refresh"),
        Binding("f5", "rebuild_index", "Refresh", show=False),
        Binding("escape", "app.go_home", "Home"),
        Binding("f3", "app.go_home", "Home", show=False),
        Binding("0", "filter_tier('0')", "All tiers", show=False),
    ]

    def __init__(self) -> None:
        super().__init__()
        self._index: PatternIndex | None = None
        self._tier_filter: int = 0

    def compose(self) -> ComposeResult:
        yield Header()
        yield Static(" Pattern Browser", id="screen-title")
        yield Input(placeholder="Filter patterns...", id="filter-input")
        with Horizontal(id="browser-main"):
            with Vertical(id="table-panel"):
                yield PatternTable(id="pattern-table")
            with Vertical(id="detail-panel"):
                yield PatternDetailPanel(id="pattern-detail")
        yield Footer()

    def on_mount(self) -> None:
        self._rebuild_index()

    def _rebuild_index(self) -> None:
        from lookout_tui.app import LookoutApp

        patterns_dirs = None
        if isinstance(self.app, LookoutApp):
            patterns_dir = self.app.tui_config.patterns_dir
            if patterns_dir.exists():
                patterns_dirs = [patterns_dir]
        self._index = build_index(patterns_dirs=patterns_dirs, include_built_in=True)
        self._apply_filters()

    def _apply_filters(self) -> None:
        if not self._index:
            return

        table = self.query_one("#pattern-table", PatternTable)
        filter_input = self.query_one("#filter-input", Input)
        filter_text = filter_input.value.lower()

        entries = self._index.entries
        if self._tier_filter:
            entries = [e for e in entries if e.tier == self._tier_filter]
        if filter_text:
            entries = [
                e
                for e in entries
                if filter_text in e.id.lower()
                or filter_text in e.title.lower()
                or filter_text in e.category.lower()
                or any(filter_text in t.lower() for t in e.tags)
            ]

        filtered = PatternIndex(
            entries=entries,
            total=len(entries),
            built_in_count=self._index.built_in_count,
            user_count=self._index.user_count,
        )
        table.populate(filtered)
        title = self.query_one("#screen-title", Static)
        title.update(f" Pattern Browser — {filtered.total} patterns")

    def on_input_changed(self, event: Input.Changed) -> None:
        if event.input.id == "filter-input":
            self._apply_filters()

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        if not self._index:
            return

        row_key = str(event.row_key.value) if event.row_key else ""
        entry = self._find_entry(row_key)
        detail = self.query_one("#pattern-detail", PatternDetailPanel)
        if entry:
            detail.show_entry(entry)
        else:
            detail.clear_detail()

    def on_data_table_row_highlighted(self, event: DataTable.RowHighlighted) -> None:
        if not self._index:
            return

        row_key = str(event.row_key.value) if event.row_key else ""
        entry = self._find_entry(row_key)
        detail = self.query_one("#pattern-detail", PatternDetailPanel)
        if entry:
            detail.show_entry(entry)
        else:
            detail.clear_detail()

    def _find_entry(self, pattern_id: str) -> PatternIndexEntry | None:
        if not self._index:
            return None
        for entry in self._index.entries:
            if entry.id == pattern_id:
                return entry
        return None

    def action_focus_filter(self) -> None:
        self.query_one("#filter-input", Input).focus()

    def action_rebuild_index(self) -> None:
        self._rebuild_index()

    def action_filter_tier(self, tier: str) -> None:
        self._tier_filter = int(tier)
        self._apply_filters()
