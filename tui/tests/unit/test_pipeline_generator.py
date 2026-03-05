"""Tests for GenerationPipeline."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import AsyncMock

import pytest

from lookout_tui.clients.protocol import LLMResponse
from lookout_tui.pipeline.generator import GenerationPipeline
from lookout_tui.pipeline.models import (
    GenerationJob,
    GenerationStage,
    StageStatus,
)
from lookout_tui.prompts.loader import PromptTemplate


@pytest.fixture
def tmp_prompts(tmp_path: Path) -> Path:
    """Create minimal prompt templates."""
    (tmp_path / "system-prompt-pattern-research.md").write_text(
        "# System\n\n```\nYou are an expert.\n```\n"
    )
    (tmp_path / "user-prompt-top-level.md").write_text(
        "# Top\n\n```\n{{PATTERN_ID}} {{PATTERN_TITLE}} {{DESCRIPTION_HINT}}\n```\n"
    )
    (tmp_path / "user-prompt-language-generic.md").write_text(
        "# Lang\n\n```\n{{TOP_LEVEL_SPEC}} {{LANGUAGE}} "
        "{{VERSION_CONSTRAINT_OR_SKIP}} {{PATTERN_ID_LOWER}}\n```\n"
    )
    (tmp_path / "user-prompt-language-framework.md").write_text(
        "# FW\n\n```\n{{TOP_LEVEL_SPEC}} {{LANGUAGE_GENERIC_SPEC}} "
        "{{LANGUAGE}} {{FRAMEWORK}} {{FRAMEWORK_VERSION_CONSTRAINT_OR_SKIP}} "
        "{{PATTERN_ID_LOWER}}\n```\n"
    )
    return tmp_path


@pytest.fixture
def mock_client() -> AsyncMock:
    client = AsyncMock()
    client.chat = AsyncMock(
        return_value=LLMResponse(
            content="Generated content",
            model="test-model",
            usage={"prompt_tokens": 10, "completion_tokens": 20},
        )
    )
    return client


@pytest.fixture
def pipeline(mock_client: AsyncMock, tmp_prompts: Path) -> GenerationPipeline:
    templates = PromptTemplate(tmp_prompts)
    return GenerationPipeline(client=mock_client, templates=templates)


class TestTopLevelStage:
    async def test_run_top_level(self, pipeline: GenerationPipeline) -> None:
        job = GenerationJob(
            pattern_id="TEST-001",
            title="Test Pattern",
            description_hint="A test",
            target_languages=["python"],
        )
        job.initialize_stages()

        result = await pipeline.run_top_level(job)

        assert result.status == StageStatus.AWAITING_REVIEW
        assert result.output == "Generated content"
        assert result.model == "test-model"

    async def test_top_level_error(self, tmp_prompts: Path) -> None:
        bad_client = AsyncMock()
        bad_client.chat = AsyncMock(side_effect=RuntimeError("Connection failed"))

        pipeline = GenerationPipeline(client=bad_client, templates=PromptTemplate(tmp_prompts))
        job = GenerationJob(
            pattern_id="TEST-001",
            title="Test",
            description_hint="hint",
        )
        job.initialize_stages()

        result = await pipeline.run_top_level(job)

        assert result.status == StageStatus.ERROR
        assert "Connection failed" in result.error


class TestLanguageGenericStage:
    async def test_run_language_generic(self, pipeline: GenerationPipeline) -> None:
        job = GenerationJob(
            pattern_id="TEST-001",
            title="Test",
            description_hint="hint",
            target_languages=["python"],
        )
        job.initialize_stages()

        result = await pipeline.run_language_generic(job, "approved top level", "python")

        assert result.status == StageStatus.AWAITING_REVIEW
        assert result.output == "Generated content"

    async def test_language_generic_error(self, tmp_prompts: Path) -> None:
        bad_client = AsyncMock()
        bad_client.chat = AsyncMock(side_effect=RuntimeError("Timeout"))

        pipeline = GenerationPipeline(client=bad_client, templates=PromptTemplate(tmp_prompts))
        job = GenerationJob(
            pattern_id="TEST-001",
            title="Test",
            description_hint="hint",
            target_languages=["python"],
        )
        job.initialize_stages()

        result = await pipeline.run_language_generic(job, "spec", "python")

        assert result.status == StageStatus.ERROR
        assert "Timeout" in result.error


class TestLanguageFrameworkStage:
    async def test_run_language_framework(self, pipeline: GenerationPipeline) -> None:
        job = GenerationJob(
            pattern_id="TEST-001",
            title="Test",
            description_hint="hint",
            target_languages=["python"],
            target_frameworks={"python": ["django"]},
        )
        job.initialize_stages()

        result = await pipeline.run_language_framework(
            job, "top spec", "lang spec", "python", "django"
        )

        assert result.status == StageStatus.AWAITING_REVIEW
        assert result.output == "Generated content"

    async def test_language_framework_error(self, tmp_prompts: Path) -> None:
        bad_client = AsyncMock()
        bad_client.chat = AsyncMock(side_effect=RuntimeError("API down"))

        pipeline = GenerationPipeline(client=bad_client, templates=PromptTemplate(tmp_prompts))
        job = GenerationJob(
            pattern_id="TEST-001",
            title="Test",
            description_hint="hint",
            target_languages=["python"],
            target_frameworks={"python": ["django"]},
        )
        job.initialize_stages()

        result = await pipeline.run_language_framework(
            job, "top spec", "lang spec", "python", "django"
        )

        assert result.status == StageStatus.ERROR
        assert "API down" in result.error


class TestCompileOutput:
    def test_compile_approved_stages(self, pipeline: GenerationPipeline) -> None:
        job = GenerationJob(
            pattern_id="TEST-001",
            title="Test Pattern",
            description_hint="hint",
            target_languages=["python"],
            target_frameworks={"python": ["django"]},
        )
        job.initialize_stages()

        job.stages[0].status = StageStatus.APPROVED
        job.stages[0].output = "Top level spec content"
        job.stages[1].status = StageStatus.APPROVED
        job.stages[1].output = "Python generic content"
        job.stages[2].status = StageStatus.APPROVED
        job.stages[2].output = "Django content"

        result = pipeline.compile_output(job)

        assert "TEST-001" in result
        assert "Top level spec content" in result
        assert "Python generic content" in result
        assert "Django content" in result

    def test_compile_skips_rejected(self, pipeline: GenerationPipeline) -> None:
        job = GenerationJob(
            pattern_id="TEST-001",
            title="Test",
            description_hint="hint",
            target_languages=["python"],
        )
        job.initialize_stages()
        job.stages[0].status = StageStatus.APPROVED
        job.stages[0].output = "Good content"
        job.stages[1].status = StageStatus.REJECTED
        job.stages[1].output = "Bad content"

        result = pipeline.compile_output(job)

        assert "Good content" in result
        assert "Bad content" not in result

    def test_compile_no_approved_stages(self, pipeline: GenerationPipeline) -> None:
        job = GenerationJob(
            pattern_id="TEST-001",
            title="Test",
            description_hint="hint",
        )
        job.initialize_stages()
        job.stages[0].status = StageStatus.ERROR

        result = pipeline.compile_output(job)

        assert "TEST-001" in result
        # Should only contain header, no stage content
        assert "## " not in result

    def test_compile_skips_empty_output(self, pipeline: GenerationPipeline) -> None:
        job = GenerationJob(
            pattern_id="TEST-001",
            title="Test",
            description_hint="hint",
        )
        job.initialize_stages()
        job.stages[0].status = StageStatus.APPROVED
        job.stages[0].output = ""

        result = pipeline.compile_output(job)

        # Empty output stage should be skipped
        assert "## " not in result


class TestFindStage:
    def test_find_top_level(self, pipeline: GenerationPipeline) -> None:
        job = GenerationJob(
            pattern_id="TEST-001",
            title="Test",
            description_hint="hint",
        )
        job.initialize_stages()

        stage = GenerationPipeline._find_stage(job, GenerationStage.TOP_LEVEL)
        assert stage.stage == GenerationStage.TOP_LEVEL

    def test_find_language_stage(self, pipeline: GenerationPipeline) -> None:
        job = GenerationJob(
            pattern_id="TEST-001",
            title="Test",
            description_hint="hint",
            target_languages=["python", "typescript"],
        )
        job.initialize_stages()

        stage = GenerationPipeline._find_stage(
            job, GenerationStage.LANGUAGE_GENERIC, language="typescript"
        )
        assert stage.language == "typescript"

    def test_find_missing_stage_raises(self, pipeline: GenerationPipeline) -> None:
        job = GenerationJob(
            pattern_id="TEST-001",
            title="Test",
            description_hint="hint",
        )
        job.initialize_stages()

        with pytest.raises(ValueError, match="Stage not found"):
            GenerationPipeline._find_stage(job, GenerationStage.LANGUAGE_GENERIC, language="go")


class TestThreeStageFlow:
    async def test_full_flow(self, pipeline: GenerationPipeline, mock_client: AsyncMock) -> None:
        """Test the complete three-stage flow with mocked client."""
        job = GenerationJob(
            pattern_id="DI-001",
            title="Dependency Injection",
            description_hint="Use constructor injection",
            target_languages=["python"],
            target_frameworks={"python": ["django"]},
        )
        job.initialize_stages()

        # Stage 1: top level
        mock_client.chat.return_value = LLMResponse(
            content="Top-level spec output",
            model="test",
            usage={},
        )
        await pipeline.run_top_level(job)
        assert job.stages[0].status == StageStatus.AWAITING_REVIEW
        job.stages[0].status = StageStatus.APPROVED

        # Stage 2: language generic
        mock_client.chat.return_value = LLMResponse(
            content="Python generic output",
            model="test",
            usage={},
        )
        await pipeline.run_language_generic(job, job.stages[0].output, "python")
        assert job.stages[1].status == StageStatus.AWAITING_REVIEW
        job.stages[1].status = StageStatus.APPROVED

        # Stage 3: framework
        mock_client.chat.return_value = LLMResponse(
            content="Django output",
            model="test",
            usage={},
        )
        await pipeline.run_language_framework(
            job,
            job.stages[0].output,
            job.stages[1].output,
            "python",
            "django",
        )
        assert job.stages[2].status == StageStatus.AWAITING_REVIEW
        job.stages[2].status = StageStatus.APPROVED

        assert job.is_complete

        # Compile
        yaml_output = pipeline.compile_output(job)
        assert "DI-001" in yaml_output
        assert "Top-level spec output" in yaml_output
        assert "Python generic output" in yaml_output
        assert "Django output" in yaml_output
