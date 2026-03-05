"""Pattern browser data table widget."""

from __future__ import annotations

from textual.widgets import DataTable

from lookout_tui.index.models import PatternIndex


class PatternTable(DataTable[str]):
    """DataTable for browsing patterns."""

    def populate(self, index: PatternIndex) -> None:
        """Fill the table with pattern index entries."""
        self.clear(columns=True)
        self.add_columns("ID", "Title", "Tier", "Category", "Languages", "Fwks")
        self.cursor_type = "row"

        for entry in sorted(index.entries, key=lambda e: e.id):
            langs = ", ".join(entry.languages[:3])
            if len(entry.languages) > 3:
                langs += "..."
            self.add_row(
                entry.id,
                entry.title[:30],
                str(entry.tier),
                entry.category[:15],
                langs,
                str(entry.framework_count),
                key=entry.id,
            )
