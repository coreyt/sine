"""Tests for the BatchScreen."""

from __future__ import annotations

from lookout_tui.screens.batch import BatchScreen
from lookout_tui.widgets.batch_grid import BatchGrid
from lookout_tui.widgets.batch_progress import BatchProgress


class TestBatchScreenBindings:
    def test_has_space_toggle_binding(self) -> None:
        bindings = {b.key for b in BatchScreen.BINDINGS}
        assert "space" in bindings

    def test_has_select_missing_binding(self) -> None:
        bindings = {b.key for b in BatchScreen.BINDINGS}
        assert "a" in bindings

    def test_has_select_stale_binding(self) -> None:
        bindings = {b.key for b in BatchScreen.BINDINGS}
        assert "s" in bindings

    def test_has_submit_binding(self) -> None:
        bindings = {b.key for b in BatchScreen.BINDINGS}
        assert "enter" in bindings

    def test_has_refresh_binding(self) -> None:
        bindings = {b.key for b in BatchScreen.BINDINGS}
        assert "r" in bindings
        assert "f5" in bindings

    def test_case_insensitive_bindings(self) -> None:
        bindings = {b.key for b in BatchScreen.BINDINGS}
        for key in ("a", "s", "r"):
            assert key in bindings
            assert key.upper() in bindings


class TestBatchScreenDefaults:
    def test_default_languages(self) -> None:
        assert "python" in BatchScreen.DEFAULT_LANGUAGES
        assert "typescript" in BatchScreen.DEFAULT_LANGUAGES

    def test_default_frameworks(self) -> None:
        assert "django" in BatchScreen.DEFAULT_FRAMEWORKS["python"]
        assert "react" in BatchScreen.DEFAULT_FRAMEWORKS["typescript"]

    def test_init_creates_grid_and_progress(self) -> None:
        screen = BatchScreen()
        assert isinstance(screen._grid, BatchGrid)
        assert isinstance(screen._progress, BatchProgress)
        assert screen._orchestrator is None


class TestBatchGridWidget:
    def test_populate_and_display(self) -> None:
        from lookout.batch.models import CellStatus, RegistryCell

        grid = BatchGrid()
        cells = [
            RegistryCell(
                pattern_id="P-001",
                language="python",
                framework=None,
                status=CellStatus.MISSING,
            ),
            RegistryCell(
                pattern_id="P-001",
                language="typescript",
                framework="react",
                status=CellStatus.PRESENT,
            ),
        ]
        grid.populate(cells)
        data = grid.get_display_data()
        assert len(data) == 2
        assert data[0]["pattern_id"] == "P-001"
        assert data[0]["status"] == CellStatus.MISSING
        assert data[1]["framework"] == "react"

    def test_toggle_and_select(self) -> None:
        from lookout.batch.models import CellStatus, RegistryCell

        grid = BatchGrid()
        cells = [
            RegistryCell(
                pattern_id="P-001",
                language="python",
                framework=None,
                status=CellStatus.MISSING,
            ),
        ]
        grid.populate(cells)
        cell_id = cells[0].cell_id
        assert len(grid.get_selected()) == 0
        grid.toggle_cell(cell_id)
        assert len(grid.get_selected()) == 1
        grid.toggle_cell(cell_id)
        assert len(grid.get_selected()) == 0

    def test_select_by_status(self) -> None:
        from lookout.batch.models import CellStatus, RegistryCell

        grid = BatchGrid()
        cells = [
            RegistryCell(
                pattern_id="P-001", language="python",
                framework=None, status=CellStatus.MISSING,
            ),
            RegistryCell(
                pattern_id="P-001", language="go",
                framework=None, status=CellStatus.PRESENT,
            ),
        ]
        grid.populate(cells)
        grid.select_by_status(CellStatus.MISSING)
        selected = grid.get_selected()
        assert len(selected) == 1
        assert selected[0].language == "python"


class TestBatchProgress:
    def test_no_job_status(self) -> None:
        progress = BatchProgress()
        assert progress.format_status() == "No active batch job"
        assert progress.job is None
