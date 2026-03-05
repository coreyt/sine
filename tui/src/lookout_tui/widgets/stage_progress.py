"""Pipeline stage progress widget."""

from __future__ import annotations

from rich.text import Text
from textual.widgets import Static

from lookout_tui.pipeline.models import GenerationJob, StageStatus

_STATUS_STYLES = {
    StageStatus.PENDING: ("dim", "○"),
    StageStatus.RUNNING: ("yellow", "◐"),
    StageStatus.AWAITING_REVIEW: ("cyan", "●"),
    StageStatus.APPROVED: ("green", "✓"),
    StageStatus.REJECTED: ("red", "✗"),
    StageStatus.ERROR: ("red bold", "!"),
}


class StageProgress(Static):
    """Shows progress through pipeline stages for a job."""

    def show_job(self, job: GenerationJob) -> None:
        lines = Text()
        lines.append(f"  Pipeline: {job.pattern_id}\n\n", style="bold")

        for stage in job.stages:
            style, icon = _STATUS_STYLES.get(stage.status, ("dim", "?"))
            label = stage.stage.value
            if stage.language:
                label += f" ({stage.language}"
                if stage.framework:
                    label += f"/{stage.framework}"
                label += ")"

            lines.append(f"  {icon} ", style=style)
            lines.append(f"{label}: ", style="bold" if not stage.is_terminal else "")
            lines.append(f"{stage.status.value}\n", style=style)

            if stage.error:
                lines.append(f"    Error: {stage.error}\n", style="red")

        self.update(lines)
