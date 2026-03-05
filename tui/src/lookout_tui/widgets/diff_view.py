"""Diff view widget for reviewing generated content."""

from __future__ import annotations

from textual.widgets import Static

from lookout_tui.pipeline.models import StageResult, StageStatus


class DiffView(Static):
    """Displays generated content for review."""

    def show_stage(self, result: StageResult) -> None:
        """Display stage output for review."""
        header = f"Stage: {result.stage.value}"
        if result.language:
            header += f" ({result.language}"
            if result.framework:
                header += f"/{result.framework}"
            header += ")"
        header += f"  |  Status: {result.status.value}"
        if result.model:
            header += f"  |  Model: {result.model}"

        if result.status == StageStatus.ERROR:
            content = f"{header}\n{'─' * 60}\n\nError: {result.error}"
        elif result.output:
            content = f"{header}\n{'─' * 60}\n\n{result.output}"
        else:
            content = f"{header}\n{'─' * 60}\n\nNo output yet."

        self.update(content)

    def clear_view(self) -> None:
        self.update("No content to review.")
