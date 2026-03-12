"""Batch screen — bulk generation grid, cell selection, batch submission."""

from __future__ import annotations

from lookout.batch.models import CellStatus, RegistryCell
from lookout.batch.orchestrator import BatchOrchestrator
from lookout.config import LookoutConfig
from textual import work
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Vertical
from textual.screen import Screen
from textual.widgets import DataTable, Footer, Header, Static

from lookout_tui.keys import ci
from lookout_tui.widgets.batch_grid import BatchGrid
from lookout_tui.widgets.batch_progress import BatchProgress

_STATUS_SYMBOLS = {
    CellStatus.PRESENT: ("present", "green"),
    CellStatus.POSSIBLY_STALE: ("stale~", "dodger_blue"),
    CellStatus.LIKELY_STALE: ("STALE!", "yellow"),
    CellStatus.MISSING: ("MISSING", "red"),
}


class BatchScreen(Screen[None]):
    """Browse and submit batch check generation requests."""

    DEFAULT_LANGUAGES = ["python", "typescript", "java", "go", "kotlin"]
    DEFAULT_FRAMEWORKS: dict[str, list[str]] = {
        "python": ["django", "flask", "fastapi"],
        "typescript": ["angular", "react", "nestjs"],
        "java": ["spring", "jakarta-ee"],
        "go": [],
        "kotlin": ["spring-boot", "ktor"],
    }

    BINDINGS = [
        Binding("space", "toggle_cell", "Select", priority=True),
        *ci("a", "select_missing", "All Missing"),
        *ci("s", "select_stale", "All Stale"),
        Binding("enter", "submit_batch", "Submit", priority=True),
        *ci("r", "refresh_grid", "Refresh"),
        Binding("f5", "refresh_grid", "Refresh", show=False),
    ]

    def __init__(self) -> None:
        super().__init__()
        self._grid = BatchGrid()
        self._progress = BatchProgress()
        self._orchestrator: BatchOrchestrator | None = None

    def compose(self) -> ComposeResult:
        yield Header()
        yield Static(" Lookout — Batch Generation", id="screen-title")
        with Vertical(id="batch-main"):
            yield DataTable(id="batch-table")
            yield Static("", id="batch-status")
        yield Footer()

    def on_mount(self) -> None:
        self._setup_table()
        self._refresh_grid()

    def _setup_table(self) -> None:
        table = self.query_one("#batch-table", DataTable)
        table.add_columns("Pattern", "Language", "Variant", "Status", "Selected")
        table.cursor_type = "row"

    def _get_orchestrator(self) -> BatchOrchestrator:
        if self._orchestrator is None:
            from lookout_tui.app import LookoutApp

            if isinstance(self.app, LookoutApp):
                config = LookoutConfig(rules_dir=self.app.tui_config.patterns_dir)
            else:
                config = LookoutConfig()
            self._orchestrator = BatchOrchestrator(
                config=config, patterns_dir=config.rules_dir
            )
        return self._orchestrator

    def _refresh_grid(self) -> None:
        orch = self._get_orchestrator()
        cells = orch.build_grid(self.DEFAULT_LANGUAGES, self.DEFAULT_FRAMEWORKS)
        self._grid.populate(cells)
        self._render_table()

    def _render_table(self) -> None:
        table = self.query_one("#batch-table", DataTable)
        prev_row = table.cursor_row
        table.clear()
        for item in self._grid.get_display_data():
            status_label, _ = _STATUS_SYMBOLS.get(
                item["status"], ("?", "white")
            )
            selected = "x" if item["selected"] else " "
            table.add_row(
                item["pattern_id"],
                item["language"],
                item["framework"],
                status_label,
                f"[{selected}]",
                key=item["cell_id"],
            )
        if prev_row is not None and prev_row < table.row_count:
            table.move_cursor(row=prev_row)

    def action_toggle_cell(self) -> None:
        table = self.query_one("#batch-table", DataTable)
        if table.cursor_row is not None:
            keys = list(table.rows.keys())
            if table.cursor_row < len(keys):
                cell_id = str(keys[table.cursor_row])
                self._grid.toggle_cell(cell_id)
                self._render_table()
                self._update_status()

    def action_select_missing(self) -> None:
        self._grid.clear_selection()
        self._grid.select_by_status(CellStatus.MISSING)
        self._render_table()
        self._update_status()
        selected = self._grid.get_selected()
        self.notify(f"Selected {len(selected)} missing cells")

    def action_select_stale(self) -> None:
        self._grid.clear_selection()
        self._grid.select_by_status(
            CellStatus.MISSING, CellStatus.POSSIBLY_STALE, CellStatus.LIKELY_STALE
        )
        self._render_table()
        self._update_status()
        selected = self._grid.get_selected()
        self.notify(f"Selected {len(selected)} cells (missing + stale)")

    def action_refresh_grid(self) -> None:
        self._refresh_grid()
        self.notify("Grid refreshed")

    def action_submit_batch(self) -> None:
        selected = self._grid.get_selected()
        if not selected:
            self.notify("No cells selected", severity="warning")
            return
        self._do_submit(selected)

    @work(thread=False)
    async def _do_submit(self, cells: list[RegistryCell]) -> None:
        orch = self._get_orchestrator()
        try:
            job = await orch.submit_batch(cells)
            self._progress.show_job(job)
            self._update_status()
            self.notify(f"Submitted batch {job.job_id}")
        except Exception as e:
            self.notify(f"Submit failed: {e}", severity="error")

    def _update_status(self) -> None:
        status_widget = self.query_one("#batch-status", Static)
        selected = self._grid.get_selected()
        parts = [f"{len(selected)} cell(s) selected"]
        progress = self._progress.format_status()
        if progress != "No active batch job":
            parts.append(progress)
        status_widget.update(" | ".join(parts))
