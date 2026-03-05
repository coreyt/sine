"""Generation job queue widget."""

from __future__ import annotations

from textual.widgets import DataTable

from lookout_tui.pipeline.models import GenerationJob


class JobQueue(DataTable[str]):
    """DataTable showing generation jobs and their status."""

    def populate(self, jobs: list[GenerationJob]) -> None:
        """Fill the table with generation jobs."""
        self.clear(columns=True)
        self.add_columns("Pattern", "Stage", "Status")
        self.cursor_type = "row"

        for job in jobs:
            current = job.current_stage
            stage_label = current.stage.value if current else "done"
            status_label = current.status.value if current else "complete"
            self.add_row(
                job.pattern_id,
                stage_label,
                status_label,
                key=job.pattern_id,
            )
