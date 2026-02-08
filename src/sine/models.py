from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class RuleCheck(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: Literal["must_wrap", "forbidden", "required_with", "raw", "pattern_discovery"]
    target: list[str] | None = None
    wrapper: list[str] | None = None
    pattern: str | None = None
    if_present: str | None = None
    must_have: str | None = None
    scope: str | None = None
    engine: str | None = None
    config: str | None = None
    # Pattern discovery fields
    patterns: list[str] | None = None


class RuleReporting(BaseModel):
    model_config = ConfigDict(extra="forbid")

    default_message: str
    confidence: Literal["low", "medium", "high"]
    documentation_url: str | None = None


class RuleExample(BaseModel):
    model_config = ConfigDict(extra="forbid")

    language: str
    code: str


class RuleExamples(BaseModel):
    model_config = ConfigDict(extra="forbid")

    good: list[RuleExample]
    bad: list[RuleExample]


class RuleSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    title: str
    description: str
    rationale: str
    tier: int = Field(ge=1, le=3)
    category: str
    severity: Literal["error", "warning", "info"]
    languages: list[str]
    check: RuleCheck
    reporting: RuleReporting
    examples: RuleExamples
    references: list[str]


class RuleSpecFile(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: int = 1
    rule: RuleSpec


@dataclass(frozen=True)
class Finding:
    """Represents a guideline violation (enforcement mode)."""

    guideline_id: str
    title: str
    severity: str
    file: str
    line: int
    message: str
    snippet: str
    engine: str
    tier: int


@dataclass(frozen=True)
class PatternInstance:
    """Represents a discovered pattern instance (discovery mode)."""

    pattern_id: str
    title: str
    category: str
    file: str
    line: int
    snippet: str
    confidence: str

