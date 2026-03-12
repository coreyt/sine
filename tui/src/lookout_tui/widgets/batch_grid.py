"""BatchGrid widget — displays the pattern x language x framework grid."""

from __future__ import annotations

from typing import Any

from lookout.batch.models import CellStatus, RegistryCell


class BatchGrid:
    """In-memory grid model for batch generation cells.

    Not a Textual widget itself — used by BatchGridScreen to manage
    cell state and selection. The screen renders this into a DataTable.
    """

    def __init__(self) -> None:
        self._cells: list[RegistryCell] = []
        self._selected: set[str] = set()

    def populate(self, cells: list[RegistryCell]) -> None:
        """Set the grid cells."""
        self._cells = list(cells)
        self._selected.clear()

    def select_by_status(self, *statuses: CellStatus) -> None:
        """Select all cells matching any of the given statuses."""
        status_set = set(statuses)
        for cell in self._cells:
            if cell.status in status_set:
                self._selected.add(cell.cell_id)

    def toggle_cell(self, cell_id: str) -> None:
        """Toggle selection of a single cell."""
        if cell_id in self._selected:
            self._selected.discard(cell_id)
        else:
            self._selected.add(cell_id)

    def clear_selection(self) -> None:
        """Clear all selections."""
        self._selected.clear()

    def get_selected(self) -> list[RegistryCell]:
        """Return all selected cells."""
        return [c for c in self._cells if c.cell_id in self._selected]

    def get_display_data(self) -> list[dict[str, Any]]:
        """Return cell data for rendering."""
        return [
            {
                "cell_id": c.cell_id,
                "pattern_id": c.pattern_id,
                "language": c.language,
                "framework": c.framework or "generic",
                "status": c.status,
                "selected": c.cell_id in self._selected,
            }
            for c in self._cells
        ]
