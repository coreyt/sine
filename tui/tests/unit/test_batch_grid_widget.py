"""Tests for BatchGrid widget."""

from __future__ import annotations

from lookout.batch.models import CellStatus, RegistryCell
from lookout_tui.widgets.batch_grid import BatchGrid


class TestBatchGrid:
    def test_select_by_status_missing(self) -> None:
        cells = [
            RegistryCell("DI-001", "python", None, CellStatus.MISSING),
            RegistryCell("DI-001", "python", "django", CellStatus.PRESENT),
            RegistryCell("DI-001", "typescript", None, CellStatus.MISSING),
        ]
        grid = BatchGrid()
        grid.populate(cells)
        grid.select_by_status(CellStatus.MISSING)
        selected = grid.get_selected()
        assert len(selected) == 2
        assert all(c.status == CellStatus.MISSING for c in selected)

    def test_select_by_status_stale(self) -> None:
        cells = [
            RegistryCell("DI-001", "python", None, CellStatus.POSSIBLY_STALE),
            RegistryCell("DI-001", "python", "django", CellStatus.LIKELY_STALE),
            RegistryCell("DI-001", "typescript", None, CellStatus.PRESENT),
        ]
        grid = BatchGrid()
        grid.populate(cells)
        grid.select_by_status(CellStatus.POSSIBLY_STALE, CellStatus.LIKELY_STALE)
        selected = grid.get_selected()
        assert len(selected) == 2

    def test_toggle_cell(self) -> None:
        cells = [
            RegistryCell("DI-001", "python", None, CellStatus.MISSING),
        ]
        grid = BatchGrid()
        grid.populate(cells)
        # Initially nothing selected
        assert len(grid.get_selected()) == 0
        # Toggle on
        grid.toggle_cell("DI-001__python__generic")
        assert len(grid.get_selected()) == 1
        # Toggle off
        grid.toggle_cell("DI-001__python__generic")
        assert len(grid.get_selected()) == 0

    def test_clear_selection(self) -> None:
        cells = [
            RegistryCell("DI-001", "python", None, CellStatus.MISSING),
            RegistryCell("DI-001", "typescript", None, CellStatus.MISSING),
        ]
        grid = BatchGrid()
        grid.populate(cells)
        grid.select_by_status(CellStatus.MISSING)
        assert len(grid.get_selected()) == 2
        grid.clear_selection()
        assert len(grid.get_selected()) == 0

    def test_cell_display_data(self) -> None:
        cells = [
            RegistryCell("DI-001", "python", None, CellStatus.PRESENT),
            RegistryCell("DI-001", "python", "django", CellStatus.MISSING),
        ]
        grid = BatchGrid()
        grid.populate(cells)
        display = grid.get_display_data()
        assert len(display) == 2
        assert display[0]["pattern_id"] == "DI-001"
        assert display[0]["language"] == "python"
        assert display[0]["framework"] == "generic"
        assert display[0]["status"] == "present"
        assert display[1]["framework"] == "django"
