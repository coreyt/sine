"""Generation pipeline data models."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class GenerationStage(Enum):
    """Stages of the generation pipeline."""

    TOP_LEVEL = "top_level"
    LANGUAGE_GENERIC = "language_generic"
    LANGUAGE_FRAMEWORK = "language_framework"


class StageStatus(Enum):
    """Status of a pipeline stage."""

    PENDING = "pending"
    RUNNING = "running"
    AWAITING_REVIEW = "awaiting_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    ERROR = "error"


@dataclass
class StageResult:
    """Result of a single pipeline stage execution."""

    stage: GenerationStage
    status: StageStatus = StageStatus.PENDING
    output: str = ""
    error: str = ""
    model: str = ""
    token_usage: dict[str, int] = field(default_factory=dict)
    language: str = ""
    framework: str = ""

    @property
    def is_terminal(self) -> bool:
        return self.status in (StageStatus.APPROVED, StageStatus.REJECTED, StageStatus.ERROR)


@dataclass
class GenerationJob:
    """A pattern generation job tracking all pipeline stages."""

    pattern_id: str
    title: str
    description_hint: str
    target_languages: list[str] = field(default_factory=list)
    target_frameworks: dict[str, list[str]] = field(default_factory=dict)
    stages: list[StageResult] = field(default_factory=list)

    @property
    def current_stage(self) -> StageResult | None:
        """Get the first non-terminal stage."""
        for stage in self.stages:
            if not stage.is_terminal:
                return stage
        return None

    @property
    def top_level_result(self) -> StageResult | None:
        for stage in self.stages:
            if stage.stage == GenerationStage.TOP_LEVEL:
                return stage
        return None

    @property
    def is_complete(self) -> bool:
        return all(s.is_terminal for s in self.stages) and len(self.stages) > 0

    def initialize_stages(self) -> None:
        """Create stage entries based on targets."""
        self.stages = [StageResult(stage=GenerationStage.TOP_LEVEL)]
        for lang in self.target_languages:
            self.stages.append(StageResult(stage=GenerationStage.LANGUAGE_GENERIC, language=lang))
            for fw in self.target_frameworks.get(lang, []):
                self.stages.append(
                    StageResult(
                        stage=GenerationStage.LANGUAGE_FRAMEWORK,
                        language=lang,
                        framework=fw,
                    )
                )
