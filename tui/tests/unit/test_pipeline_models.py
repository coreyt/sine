"""Tests for pipeline data models."""

from __future__ import annotations

from lookout_tui.pipeline.models import (
    GenerationJob,
    GenerationStage,
    StageResult,
    StageStatus,
)


class TestStageResult:
    def test_pending_is_not_terminal(self) -> None:
        s = StageResult(stage=GenerationStage.TOP_LEVEL)
        assert not s.is_terminal

    def test_running_is_not_terminal(self) -> None:
        s = StageResult(stage=GenerationStage.TOP_LEVEL, status=StageStatus.RUNNING)
        assert not s.is_terminal

    def test_awaiting_review_is_not_terminal(self) -> None:
        s = StageResult(stage=GenerationStage.TOP_LEVEL, status=StageStatus.AWAITING_REVIEW)
        assert not s.is_terminal

    def test_approved_is_terminal(self) -> None:
        s = StageResult(stage=GenerationStage.TOP_LEVEL, status=StageStatus.APPROVED)
        assert s.is_terminal

    def test_rejected_is_terminal(self) -> None:
        s = StageResult(stage=GenerationStage.TOP_LEVEL, status=StageStatus.REJECTED)
        assert s.is_terminal

    def test_error_is_terminal(self) -> None:
        s = StageResult(stage=GenerationStage.TOP_LEVEL, status=StageStatus.ERROR)
        assert s.is_terminal


class TestGenerationJob:
    def test_initialize_stages_top_level_only(self) -> None:
        job = GenerationJob(
            pattern_id="TEST-001",
            title="Test",
            description_hint="Test hint",
            target_languages=[],
        )
        job.initialize_stages()
        assert len(job.stages) == 1
        assert job.stages[0].stage == GenerationStage.TOP_LEVEL

    def test_initialize_stages_with_languages(self) -> None:
        job = GenerationJob(
            pattern_id="TEST-001",
            title="Test",
            description_hint="hint",
            target_languages=["python", "typescript"],
        )
        job.initialize_stages()
        assert len(job.stages) == 3  # top + 2 languages
        assert job.stages[1].language == "python"
        assert job.stages[2].language == "typescript"

    def test_initialize_stages_with_frameworks(self) -> None:
        job = GenerationJob(
            pattern_id="TEST-001",
            title="Test",
            description_hint="hint",
            target_languages=["python"],
            target_frameworks={"python": ["django", "flask"]},
        )
        job.initialize_stages()
        assert len(job.stages) == 4  # top + 1 lang + 2 frameworks
        assert job.stages[2].framework == "django"
        assert job.stages[3].framework == "flask"

    def test_current_stage_returns_first_non_terminal(self) -> None:
        job = GenerationJob(
            pattern_id="TEST-001",
            title="Test",
            description_hint="hint",
            target_languages=["python"],
        )
        job.initialize_stages()
        job.stages[0].status = StageStatus.APPROVED

        current = job.current_stage
        assert current is not None
        assert current.stage == GenerationStage.LANGUAGE_GENERIC

    def test_current_stage_none_when_all_complete(self) -> None:
        job = GenerationJob(
            pattern_id="TEST-001",
            title="Test",
            description_hint="hint",
            target_languages=[],
        )
        job.initialize_stages()
        job.stages[0].status = StageStatus.APPROVED

        assert job.current_stage is None

    def test_is_complete(self) -> None:
        job = GenerationJob(
            pattern_id="TEST-001",
            title="Test",
            description_hint="hint",
            target_languages=["python"],
        )
        job.initialize_stages()
        assert not job.is_complete

        for s in job.stages:
            s.status = StageStatus.APPROVED
        assert job.is_complete

    def test_top_level_result(self) -> None:
        job = GenerationJob(
            pattern_id="TEST-001",
            title="Test",
            description_hint="hint",
        )
        job.initialize_stages()
        assert job.top_level_result is not None
        assert job.top_level_result.stage == GenerationStage.TOP_LEVEL

    def test_empty_job_not_complete(self) -> None:
        job = GenerationJob(
            pattern_id="TEST-001",
            title="Test",
            description_hint="hint",
        )
        assert not job.is_complete

    def test_frameworks_without_matching_language_ignored(self) -> None:
        job = GenerationJob(
            pattern_id="TEST-001",
            title="Test",
            description_hint="hint",
            target_languages=["python"],
            target_frameworks={"java": ["spring"]},
        )
        job.initialize_stages()
        # java/spring should not appear since java not in target_languages
        assert len(job.stages) == 2  # top + python generic only
        assert all(s.framework == "" for s in job.stages)

    def test_initialize_stages_resets(self) -> None:
        job = GenerationJob(
            pattern_id="TEST-001",
            title="Test",
            description_hint="hint",
            target_languages=["python"],
        )
        job.initialize_stages()
        job.stages[0].status = StageStatus.APPROVED

        job.initialize_stages()
        assert job.stages[0].status == StageStatus.PENDING  # reset
