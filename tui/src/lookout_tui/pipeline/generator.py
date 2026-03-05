"""Three-stage generation pipeline orchestrator."""

from __future__ import annotations

import logging

from lookout_tui.clients.protocol import LLMClient, LLMResponse
from lookout_tui.pipeline.models import (
    GenerationJob,
    GenerationStage,
    StageResult,
    StageStatus,
)
from lookout_tui.prompts.loader import PromptTemplate

logger = logging.getLogger("lookout_tui.pipeline.generator")


class GenerationPipeline:
    """Orchestrates the three-stage LLM generation pipeline.

    Stages:
        1. Top-level pattern specification
        2. Language-generic variant (per language)
        3. Language-framework variant (per framework)

    Each stage produces output that feeds into the next stage's prompt.
    """

    def __init__(self, client: LLMClient, templates: PromptTemplate) -> None:
        self.client = client
        self.templates = templates

    async def run_top_level(self, job: GenerationJob) -> StageResult:
        """Run Stage 1: Generate top-level pattern specification."""
        stage = self._find_stage(job, GenerationStage.TOP_LEVEL)
        stage.status = StageStatus.RUNNING

        try:
            system_prompt = self.templates.render_system_prompt()
            user_prompt = self.templates.render_top_level(
                pattern_id=job.pattern_id,
                pattern_title=job.title,
                description_hint=job.description_hint,
            )

            response = await self.client.chat(system_prompt, user_prompt)
            self._apply_response(stage, response)
            stage.status = StageStatus.AWAITING_REVIEW
        except Exception as e:
            logger.exception("Top-level generation failed")
            stage.status = StageStatus.ERROR
            stage.error = str(e)

        return stage

    async def run_language_generic(
        self,
        job: GenerationJob,
        approved_top_level: str,
        language: str,
    ) -> StageResult:
        """Run Stage 2: Generate language-generic variant."""
        stage = self._find_stage(job, GenerationStage.LANGUAGE_GENERIC, language=language)
        stage.status = StageStatus.RUNNING

        try:
            system_prompt = self.templates.render_system_prompt()
            user_prompt = self.templates.render_language_generic(
                top_level_spec=approved_top_level,
                language=language,
                pattern_id_lower=job.pattern_id.lower(),
            )

            response = await self.client.chat(system_prompt, user_prompt)
            self._apply_response(stage, response)
            stage.status = StageStatus.AWAITING_REVIEW
        except Exception as e:
            logger.exception("Language-generic generation failed for %s", language)
            stage.status = StageStatus.ERROR
            stage.error = str(e)

        return stage

    async def run_language_framework(
        self,
        job: GenerationJob,
        approved_top_level: str,
        approved_language: str,
        language: str,
        framework: str,
    ) -> StageResult:
        """Run Stage 3: Generate language-framework variant."""
        stage = self._find_stage(
            job,
            GenerationStage.LANGUAGE_FRAMEWORK,
            language=language,
            framework=framework,
        )
        stage.status = StageStatus.RUNNING

        try:
            system_prompt = self.templates.render_system_prompt()
            user_prompt = self.templates.render_language_framework(
                top_level_spec=approved_top_level,
                language_generic_spec=approved_language,
                language=language,
                framework=framework,
                pattern_id_lower=job.pattern_id.lower(),
            )

            response = await self.client.chat(system_prompt, user_prompt)
            self._apply_response(stage, response)
            stage.status = StageStatus.AWAITING_REVIEW
        except Exception as e:
            logger.exception("Framework generation failed for %s/%s", language, framework)
            stage.status = StageStatus.ERROR
            stage.error = str(e)

        return stage

    def compile_output(self, job: GenerationJob) -> str:
        """Assemble approved stage outputs into a human-readable summary."""
        parts: list[str] = []
        parts.append(f"# Generated Pattern: {job.pattern_id}")
        parts.append(f"# Title: {job.title}")
        parts.append("")

        for stage in job.stages:
            if stage.status == StageStatus.APPROVED and stage.output:
                if stage.stage == GenerationStage.TOP_LEVEL:
                    parts.append("## Top-Level Specification")
                elif stage.stage == GenerationStage.LANGUAGE_GENERIC:
                    parts.append(f"## Language: {stage.language}")
                elif stage.stage == GenerationStage.LANGUAGE_FRAMEWORK:
                    parts.append(f"## Framework: {stage.language}/{stage.framework}")
                parts.append("")
                parts.append(stage.output)
                parts.append("")

        return "\n".join(parts)

    @staticmethod
    def _find_stage(
        job: GenerationJob,
        stage_type: GenerationStage,
        language: str = "",
        framework: str = "",
    ) -> StageResult:
        """Find a specific stage in the job."""
        for stage in job.stages:
            if stage.stage == stage_type:
                if stage_type == GenerationStage.TOP_LEVEL:
                    return stage
                if stage.language == language:
                    if stage_type == GenerationStage.LANGUAGE_GENERIC:
                        return stage
                    if stage.framework == framework:
                        return stage
        raise ValueError(
            f"Stage not found: {stage_type.value} (language={language}, framework={framework})"
        )

    @staticmethod
    def _apply_response(stage: StageResult, response: LLMResponse) -> None:
        """Apply LLM response to a stage result."""
        stage.output = response.content
        stage.model = response.model
        stage.token_usage = response.usage
