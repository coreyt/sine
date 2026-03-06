"""Generation Pipeline screen."""

from __future__ import annotations

import asyncio

from textual import work
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import DataTable, Footer, Header, Static

from lookout_tui.clients.litellm_client import LiteLLMClient
from lookout_tui.clients.protocol import LLMClient
from lookout_tui.config import TUIConfig
from lookout_tui.keys import ci
from lookout_tui.pipeline.generator import GenerationPipeline
from lookout_tui.pipeline.models import (
    GenerationJob,
    GenerationStage,
    StageResult,
    StageStatus,
)
from lookout_tui.prompts.loader import PromptTemplate
from lookout_tui.widgets.diff_view import DiffView
from lookout_tui.widgets.job_queue import JobQueue
from lookout_tui.widgets.model_selector import ModelSelector
from lookout_tui.widgets.stage_progress import StageProgress


class GenerationPipelineScreen(Screen[None]):
    """Run and review the three-stage generation pipeline."""

    BINDINGS = [
        *ci("a", "new_job", "Add Job"),
        Binding("ctrl+a", "approve", "Approve", key_display="^a"),
        Binding("ctrl+x", "reject", "Reject", key_display="^x"),
        *ci("t", "retry", "Retry"),
        *ci("w", "write_yaml", "Write YAML"),
        *ci("r", "refresh_view", "Refresh"),
        Binding("f5", "refresh_view", "Refresh", show=False),
        Binding("escape", "app.go_home", "Home"),
        Binding("f3", "app.go_home", "Home", show=False),
    ]

    def __init__(self) -> None:
        super().__init__()
        self._jobs: list[GenerationJob] = []
        self._current_job: GenerationJob | None = None
        self._pipeline: GenerationPipeline | None = None
        self._client: LLMClient | None = None
        self._pipeline_lock = asyncio.Lock()

    def compose(self) -> ComposeResult:
        yield Header()
        yield Static(" Generation Pipeline", id="screen-title")
        from lookout_tui.app import LookoutApp

        model = self.app.tui_config.llm_model if isinstance(self.app, LookoutApp) else TUIConfig().llm_model
        yield ModelSelector(current_model=model, id="model-selector")
        with Horizontal(id="generation-main"):
            with Vertical(id="queue-panel"):
                yield JobQueue(id="job-queue")
            with Vertical(id="stage-panel"):
                yield StageProgress(id="stage-progress")
                yield DiffView(id="diff-view")
        yield Footer()

    async def on_unmount(self) -> None:
        """Clean up LLM client on screen teardown."""
        if self._client:
            await self._client.__aexit__(None, None, None)
            self._client = None
            self._pipeline = None

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        row_key = str(event.row_key.value) if event.row_key else ""
        for job in self._jobs:
            if job.pattern_id == row_key:
                self._current_job = job
                self._refresh_stage_view()
                break

    def _refresh_stage_view(self) -> None:
        if not self._current_job:
            return
        progress = self.query_one("#stage-progress", StageProgress)
        progress.show_job(self._current_job)

        diff = self.query_one("#diff-view", DiffView)
        current = self._current_job.current_stage
        if current:
            diff.show_stage(current)
        else:
            diff.clear_view()

    def _refresh_queue(self) -> None:
        queue = self.query_one("#job-queue", JobQueue)
        queue.populate(self._jobs)

    async def _ensure_pipeline(self) -> GenerationPipeline:
        async with self._pipeline_lock:
            if self._pipeline:
                return self._pipeline

            from lookout_tui.app import LookoutApp

            assert isinstance(self.app, LookoutApp)
            config = self.app.tui_config

            self._client = LiteLLMClient(
                model=config.llm_model,
                temperature=config.llm_temperature,
                max_tokens=config.llm_max_tokens,
                timeout=config.llm_timeout,
                max_retries=config.llm_max_retries,
            )
            await self._client.__aenter__()

            templates = PromptTemplate(config.prompts_dir)
            self._pipeline = GenerationPipeline(self._client, templates)
            return self._pipeline

    async def on_model_selector_model_changed(self, event: ModelSelector.ModelChanged) -> None:
        """Update config and invalidate pipeline when model changes."""
        from lookout_tui.app import LookoutApp

        if isinstance(self.app, LookoutApp):
            self.app.tui_config.llm_model = event.model
        async with self._pipeline_lock:
            self._client = None
            self._pipeline = None

    def action_refresh_view(self) -> None:
        self._refresh_queue()
        self._refresh_stage_view()

    def action_new_job(self) -> None:
        """Create a new generation job (simple dialog via notify)."""
        job = GenerationJob(
            pattern_id=f"NEW-{len(self._jobs) + 1:03d}",
            title="New Pattern",
            description_hint="Describe the pattern...",
            target_languages=["python"],
        )
        job.initialize_stages()
        self._jobs.append(job)
        self._current_job = job
        self._refresh_queue()
        self._refresh_stage_view()
        self.notify(f"Created job {job.pattern_id}. Press 't' to run first stage.")

    def action_approve(self) -> None:
        if not self._current_job:
            self.notify("No job selected", severity="warning")
            return
        current = self._current_job.current_stage
        if not current or current.status != StageStatus.AWAITING_REVIEW:
            self.notify("No stage awaiting review", severity="warning")
            return
        current.status = StageStatus.APPROVED
        self._refresh_stage_view()
        self._refresh_queue()
        self.notify(f"Approved {current.stage.value}")

        # Auto-advance: run next pending stage
        next_stage = self._current_job.current_stage
        if next_stage and next_stage.status == StageStatus.PENDING:
            self._run_stage(self._current_job, next_stage)

    def action_reject(self) -> None:
        if not self._current_job:
            self.notify("No job selected", severity="warning")
            return
        current = self._current_job.current_stage
        if not current or current.status != StageStatus.AWAITING_REVIEW:
            self.notify("No stage awaiting review", severity="warning")
            return
        current.status = StageStatus.REJECTED
        self._refresh_stage_view()
        self._refresh_queue()
        self.notify(f"Rejected {current.stage.value}. Press 't' to retry.")

    def action_retry(self) -> None:
        if not self._current_job:
            self.notify("No job selected", severity="warning")
            return
        stage = self._find_retryable_stage(self._current_job)
        if not stage:
            self.notify("No stage to retry", severity="warning")
            return
        if stage.status in (StageStatus.REJECTED, StageStatus.ERROR):
            stage.status = StageStatus.PENDING
        self._run_stage(self._current_job, stage)

    @staticmethod
    def _find_retryable_stage(job: GenerationJob) -> StageResult | None:
        """Find a stage that can be retried.

        Priority: first REJECTED/ERROR stage, then first PENDING stage.
        Skips RUNNING, AWAITING_REVIEW, and APPROVED stages.
        """
        for stage in job.stages:
            if stage.status in (StageStatus.REJECTED, StageStatus.ERROR):
                return stage
        for stage in job.stages:
            if stage.status == StageStatus.PENDING:
                return stage
        return None

    def action_write_yaml(self) -> None:
        if not self._current_job or not self._pipeline:
            self.notify("No job or pipeline", severity="warning")
            return
        output = self._pipeline.compile_output(self._current_job)
        self.query_one("#diff-view", DiffView).update(output)
        self.notify("Output rendered in diff view")

    @work(thread=False)
    async def _run_stage(self, job: GenerationJob, stage: StageResult) -> None:
        """Run a pipeline stage asynchronously."""
        pipeline = await self._ensure_pipeline()

        if stage.stage == GenerationStage.TOP_LEVEL:
            await pipeline.run_top_level(job)
        elif stage.stage == GenerationStage.LANGUAGE_GENERIC:
            top_level = job.top_level_result
            if not top_level or top_level.status != StageStatus.APPROVED:
                self.notify("Top-level must be approved first", severity="error")
                return
            await pipeline.run_language_generic(job, top_level.output, stage.language)
        elif stage.stage == GenerationStage.LANGUAGE_FRAMEWORK:
            top_level = job.top_level_result
            if not top_level or top_level.status != StageStatus.APPROVED:
                self.notify("Top-level must be approved first", severity="error")
                return
            lang_output = ""
            for s in job.stages:
                if (
                    s.stage == GenerationStage.LANGUAGE_GENERIC
                    and s.language == stage.language
                    and s.status == StageStatus.APPROVED
                ):
                    lang_output = s.output
                    break
            if not lang_output:
                self.notify(
                    f"Language stage for {stage.language} must be approved first",
                    severity="error",
                )
                return
            await pipeline.run_language_framework(
                job,
                top_level.output,
                lang_output,
                stage.language,
                stage.framework,
            )

        self._refresh_stage_view()
        self._refresh_queue()
